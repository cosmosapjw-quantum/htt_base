#!/usr/bin/env python3
"""Execute and replay the registered PMG-WU-008 map-free power experiment.

This runner consumes only the accepted committed harmonic carriers.  It never
opens a sky map and never uses the observed Planck row.  Its estimates describe
the registered 200-reference functional, not the original 301/1000-row tests.
"""
from __future__ import annotations

import argparse
import csv
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import multiprocessing
import os
from pathlib import Path
import re
import sys
from typing import Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for import_root in (ROOT, ROOT / "htt", ROOT / "htt/src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from obsstat.planck_irrep_injections import (  # noqa: E402
    AMPLITUDES,
    COMBINERS,
    ECDF,
    LEGACY,
    evaluate_cell,
    reference_scale,
    summarize_decisions,
    template_bank,
    threshold_crossings,
)
from scripts.observed_runs.planck_irrep_power_adapter import (  # noqa: E402
    FAMILIES,
    TAILS,
    make_extractor,
)


REGISTRY_PATH = ROOT / "docs/research_program/post_pr327/planck_mes_wu008_experiment.json"
PAIRED_DIR = ROOT / "docs/generated/planck_pr3_paired300_irrep_carrier"
CMBONLY_DIR = ROOT / "docs/generated/planck_mes_smica_cmbonly_999_irrep"
OUTPUT_DIR = ROOT / "docs/generated/planck_mes_irrep_injection_power"
EXPECTED_REGISTRY_SHA256 = "f4374966e1710be6490e57f35ae8d725806f5488fc3595db0d3afb1ce67b5e4d"
EXPECTED_INPUT_SHA256 = {
    "paired_carrier": "0a296c21902b691eb2e2b68a9b39f626020aa8c2b14fb93a1b12116215886b93",
    "paired_metadata": "08be4f0ab0025969cb13b0cf4fed135ebfbc5fb2f0597ce0bfd0f1caf3f0721e",
    "paired_terminal": "bf82c1e2be03c9fe1c3ca8a4ef148a84be4d7b999cb31af5c617882fe1e0decb",
    "cmbonly_carrier": "99530ed25fe0bb09471c15152c6515a437bf6c684ea70cc17dfc96f115552b97",
    "cmbonly_metadata": "921ff0b9f054825152c853ef47664284b0883262e514cdb8bbfd5f2046633d5a",
    "cmbonly_terminal": "a0adb549fd43be4f79386605d1cb40c9cda62627e260efcffa50540a536279fe",
}
GIT_RE = re.compile(r"^[0-9a-f]{40}$")
SHA_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
FORMAT = "PLANCK_MES_IRREP_INJECTION_POWER_V1"
TERMINAL_FORMAT = "PLANCK_MES_IRREP_INJECTION_POWER_REVIEWED_TERMINAL_V1"
REVIEW_FORMAT = "PLANCK_MES_IRREP_INJECTION_POWER_FRESH_REVIEW_V1"
FIGURES = (
    "figure_power_curves.pdf",
    "figure_template_power_heatmap.pdf",
    "figure_scalar_irrep_power_difference.pdf",
    "figure_orientation_prefix_sensitivity.pdf",
)
OBJECTIVE_ARTIFACTS = (
    "paired300_trials.npz",
    "paired300_execution.json",
    "cmbonly999_trials.npz",
    "cmbonly999_execution.json",
    "power_table.csv",
    "threshold_crossings.csv",
    "scalar_irrep_comparison.csv",
    "orientation_sensitivity.csv",
    *FIGURES,
    "result.json",
)
POSITIVE_AMPLITUDES = AMPLITUDES[1:]
REDUCERS = (LEGACY, ECDF)
LARGEST_REJECTING_NUMERATOR = 10


class Wu008Error(RuntimeError):
    """Typed fail-closed WU-008 error."""


@dataclass(frozen=True)
class ArmInputs:
    ids: tuple[str, ...]
    carriers: np.ndarray
    content_id: str


@dataclass(frozen=True)
class PowerInputs:
    calibration_ids: tuple[str, ...]
    calibration_carriers: np.ndarray
    arms: Mapping[str, ArmInputs]
    metadata: Mapping[str, object]
    scale_rms: float
    source_identity: str
    raw_maps_reopened: bool = False


@dataclass(frozen=True)
class Cell:
    template_id: str
    amplitude: float
    orientation_count: int


@dataclass(frozen=True)
class CheckpointIdentity:
    candidate_git_head: str
    candidate_git_tree: str
    registry_sha256: str
    input_content_id: str
    arm: str
    template_id: str
    amplitude: float


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_id(value: object, *, role: str) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(role.encode("ascii") + b"\0" + encoded).hexdigest()


def _array_id(arrays: Mapping[str, np.ndarray], *, role: str) -> str:
    digest = hashlib.sha256(role.encode("ascii") + b"\0")
    for name in sorted(arrays):
        array = np.ascontiguousarray(arrays[name])
        digest.update(name.encode("ascii") + b"\0")
        digest.update(array.dtype.str.encode("ascii") + b"\0")
        digest.update(repr(array.shape).encode("ascii") + b"\0")
        digest.update(memoryview(array).cast("B"))
    return "sha256:" + digest.hexdigest()


def _atomic_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _atomic_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("wb") as handle:
        np.savez_compressed(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise Wu008Error(f"empty output table: {path.name}")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def _require_identity(value: str, *, git: bool, label: str) -> None:
    pattern = GIT_RE if git else SHA_RE
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise Wu008Error(f"malformed {label} identity")


def build_claim_metadata(
    *,
    registry: Mapping[str, object],
    input_source_identity: str,
    candidate_git_head: str,
    candidate_git_tree: str,
    evidence_repair_git_head: str,
    evidence_repair_git_tree: str,
) -> dict[str, object]:
    """Build the consumed claim boundary for the complete WU-008 result pack."""

    _require_identity(input_source_identity, git=False, label="input source")
    _require_identity(candidate_git_head, git=True, label="candidate head")
    _require_identity(candidate_git_tree, git=True, label="candidate tree")
    _require_identity(evidence_repair_git_head, git=True, label="evidence repair head")
    _require_identity(evidence_repair_git_tree, git=True, label="evidence repair tree")
    scope = registry.get("scope_limitation")
    if not isinstance(scope, str) or not scope:
        raise Wu008Error("claim metadata registry scope differs")
    command = "python scripts/observed_runs/run_planck_mes_irrep_injection_power.py"
    return {
        "owner": "OBSSTAT",
        "scope": scope,
        "claim_tier": "C2_CONDITIONAL_DIAGNOSTIC_ONLY",
        "artifact_mode": "CLAIM_BEARING_FROZEN_CONDITIONAL_METHOD_POWER",
        "allowed_use": [
            "conditional method-power reporting for the registered 200-reference functional",
            "template, family, reducer, and combiner sensitivity comparison",
            "map-free committed-artifact integrity replay",
        ],
        "forbidden_use": [
            "power calibration of the original full301 or full1000 observation procedures",
            "unconditional p-value, detection, or independent-replication claim",
            "physical shear, vorticity, local/global, geometry, or Bianchi-family inference",
            "replacement of the paired-300 primary result",
        ],
        "transfer_source": "NONE_POST_ESTIMATOR_CARRIER_DOMAIN",
        "sky_support_status": "INHERITED_FROM_ACCEPTED_WU005_AND_WU007_CARRIERS_NO_NEW_MAP_ACCESS",
        "mask_status": "INHERITED_FROZEN_JOINT_CUTSKY_OPERATOR_NO_NEW_MASK_OPERATION",
        "covariance_status": "DIAGNOSTIC_REFERENCE_COVARIANCE_NOT_USED_IN_FINITE_RANK_SCORING",
        "null_status_by_arm": {
            "cmbonly999": "MATCHED_CMB_ONLY_QUERY_AND_CMB_ONLY_REFERENCE_CONDITIONAL_FINITE_POOL",
            "paired300": "CMB_PLUS_NOISE_QUERY_AGAINST_CMB_ONLY_REFERENCE_NOT_EXCHANGEABLE_DESCRIPTIVE_DECISION_RULE",
        },
        "caveats": [
            "the two evaluation arms share 100 CMB identities and are not independent replications",
            "the 32 orientations are a fixed descriptive bank, not certified Haar convergence",
            "physical response templates are deferred and no observation enters the power study",
            "finite ranks are conditional on the fixed 200-row reference pool",
        ],
        "generating_procedure": (
            "execute each registered map-free arm from accepted carriers, summarize exact "
            "integer ranks, then assemble plots and content-bound evidence"
        ),
        "generating_commands": [
            f"{command} --execute --arm paired300 --checkpoint-root <private-checkpoint-root>",
            f"{command} --execute --arm cmbonly999 --checkpoint-root <private-checkpoint-root>",
            (
                f"{command} --assemble --output docs/generated/planck_mes_irrep_injection_power "
                "--candidate-git-head <execution-head> --candidate-git-tree <execution-tree> "
                "--evidence-repair-git-head <repair-head> --evidence-repair-git-tree <repair-tree>"
            ),
        ],
        "registry_sha256": "sha256:" + EXPECTED_REGISTRY_SHA256,
        "input_source_identity": input_source_identity,
        "candidate_git_head": candidate_git_head,
        "candidate_git_tree": candidate_git_tree,
        "candidate_git_state": "CODE_AND_REGISTRY_COMMITTED_BEFORE_EXECUTION",
        "evidence_repair_git_head": evidence_repair_git_head,
        "evidence_repair_git_tree": evidence_repair_git_tree,
        "evidence_repair_git_state": "BOUNDED_REFEREE_REPAIR_COMMITTED_BEFORE_EVIDENCE_REASSEMBLY",
        "applies_to_artifacts": list(OBJECTIVE_ARTIFACTS),
        "registered_claim_provenance": {
            "finite_rank_claim_id": "C-PR135-FINITE-NULL-RANK",
            "source_response_claim_id": "C-PR133-SOURCE-RESPONSE-TYPES",
            "claim_promotion": False,
        },
    }


def validate_claim_metadata(
    metadata: Mapping[str, object], *, registry: Mapping[str, object]
) -> None:
    """Reject incomplete or semantically altered WU-008 claim metadata."""

    if not isinstance(metadata, Mapping):
        raise Wu008Error("claim metadata is absent")
    try:
        expected = build_claim_metadata(
            registry=registry,
            input_source_identity=str(metadata["input_source_identity"]),
            candidate_git_head=str(metadata["candidate_git_head"]),
            candidate_git_tree=str(metadata["candidate_git_tree"]),
            evidence_repair_git_head=str(metadata["evidence_repair_git_head"]),
            evidence_repair_git_tree=str(metadata["evidence_repair_git_tree"]),
        )
    except (KeyError, TypeError, Wu008Error) as exc:
        raise Wu008Error("claim metadata is incomplete") from exc
    if dict(metadata) != expected:
        raise Wu008Error("claim metadata semantic content differs")


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, object]:
    path = Path(path)
    if path.is_symlink() or not path.is_file() or _sha256(path) != EXPECTED_REGISTRY_SHA256:
        raise Wu008Error("exact WU-008 numerical registry identity differs")
    payload = json.loads(path.read_text(encoding="utf-8"))
    expected_calibration = [f"{index:05d}" for index in range(200)]
    expected_paired = [f"{index:05d}" for index in range(200, 300)]
    expected_cmb = [f"{index:05d}" for index in range(200, 1000) if index != 970]
    exact = {
        "schema": "PMG_WU008_NUMERICAL_SPEC_V1",
        "accepted_head": "ccba350d7b725b227c64436e32af96abfe786449",
        "accepted_tree": "e91b8a4f57777c71c2bf1fc0f8c21395753481ba",
        "amplitudes": list(AMPLITUDES),
        "orientation_count": 32,
        "orientation_seed": "PMG-WU-008:20260829",
        "families": list(FAMILIES),
        "reducers": list(REDUCERS),
        "combiners": list(COMBINERS),
        "calibration_ids": expected_calibration,
        "observation_used_for_power": False,
        "raw_map_access": False,
        "finite_rank_denominator": 201,
        "largest_rejecting_rank_numerator": LARGEST_REJECTING_NUMERATOR,
    }
    if any(payload.get(key) != value for key, value in exact.items()):
        raise Wu008Error("WU-008 numerical registry semantic drift")
    evaluations = payload.get("evaluation_ids")
    if not isinstance(evaluations, dict) or evaluations.get("paired300") != expected_paired or evaluations.get("cmbonly999") != expected_cmb:
        raise Wu008Error("WU-008 evaluation row registry drift")
    if set(expected_calibration) & set(expected_cmb):
        raise Wu008Error("calibration and evaluation IDs overlap")
    return payload


def _require_file(path: Path, expected: str, label: str) -> None:
    if path.is_symlink() or not path.is_file() or _sha256(path) != expected:
        raise Wu008Error(f"accepted {label} byte identity differs")


def load_accepted_inputs(registry_path: Path = REGISTRY_PATH) -> PowerInputs:
    registry = load_registry(registry_path)
    paired_package = PAIRED_DIR / "carrier.npz"
    paired_metadata_path = PAIRED_DIR / "metadata.json"
    paired_terminal_path = PAIRED_DIR / "terminal.json"
    cmb_package = CMBONLY_DIR / "observable_irreps.npz"
    cmb_metadata_path = CMBONLY_DIR / "observable_irreps.json"
    cmb_terminal_path = CMBONLY_DIR / "terminal.json"
    paths = {
        "paired_carrier": paired_package,
        "paired_metadata": paired_metadata_path,
        "paired_terminal": paired_terminal_path,
        "cmbonly_carrier": cmb_package,
        "cmbonly_metadata": cmb_metadata_path,
        "cmbonly_terminal": cmb_terminal_path,
    }
    for label, path in paths.items():
        _require_file(path, EXPECTED_INPUT_SHA256[label], label)
    paired_terminal = json.loads(paired_terminal_path.read_text(encoding="utf-8"))
    cmb_terminal = json.loads(cmb_terminal_path.read_text(encoding="utf-8"))
    if paired_terminal.get("state") != "SUCCEEDED" or cmb_terminal.get("state") != "SUCCEEDED":
        raise Wu008Error("accepted carrier predecessor terminal is not successful")
    metadata = json.loads(paired_metadata_path.read_text(encoding="utf-8"))
    if metadata.get("coordinate_frame") != "GALACTIC" or metadata.get("map_unit") != "microK_CMB":
        raise Wu008Error("accepted carrier frame or units differ")
    with np.load(paired_package, allow_pickle=False) as bundle:
        if set(bundle.files) != {"observed_real_alm", "null_real_alm", "row_ids", "real_alm_layout"}:
            raise Wu008Error("paired carrier schema differs")
        paired = np.asarray(bundle["null_real_alm"], dtype=np.float64)
        paired_rows = tuple(str(value) for value in bundle["row_ids"].tolist())
    with np.load(cmb_package, allow_pickle=False) as bundle:
        if "carrier_rows" not in bundle.files or "row_ids" not in bundle.files:
            raise Wu008Error("CMB-only carrier schema differs")
        cmb = np.asarray(bundle["carrier_rows"], dtype=np.float64)
        cmb_rows = tuple(str(value) for value in bundle["row_ids"].tolist())
    expected_paired_rows = (
        "PLANCK-PR3-SMICA-OBSERVED",
        *(f"FFP10-SMICA-CMBNOISE-{index:05d}" for index in range(300)),
    )
    expected_cmb_ids = tuple(f"{index:05d}" for index in range(1000) if index != 970)
    expected_cmb_rows = (
        "PLANCK-PR3-SMICA-OBSERVED",
        *(f"FFP10-SMICA-CMB-{value}" for value in expected_cmb_ids),
    )
    if paired.shape != (300, 32) or paired_rows != expected_paired_rows:
        raise Wu008Error("paired carrier identity/order differs")
    if cmb.shape != (1000, 32) or cmb_rows != expected_cmb_rows:
        raise Wu008Error("CMB-only carrier identity/order differs")
    calibration_ids = tuple(registry["calibration_ids"])
    paired_ids = tuple(registry["evaluation_ids"]["paired300"])
    cmb_ids = tuple(registry["evaluation_ids"]["cmbonly999"])
    calibration = np.ascontiguousarray(cmb[1:201], dtype=np.float64)
    paired_eval = np.ascontiguousarray(paired[200:300], dtype=np.float64)
    cmb_eval = np.ascontiguousarray(cmb[201:], dtype=np.float64)
    if cmb_ids != expected_cmb_ids[200:] or paired_ids != tuple(f"{index:05d}" for index in range(200, 300)):
        raise Wu008Error("evaluation row slicing differs from registry")
    calibration_id = _array_id(
        {"calibration_carriers": calibration}, role="wu008_calibration_carriers"
    )
    arms = {
        "paired300": ArmInputs(
            ids=paired_ids, carriers=paired_eval,
            content_id=_array_id({"carriers": paired_eval}, role="wu008_paired300_evaluation"),
        ),
        "cmbonly999": ArmInputs(
            ids=cmb_ids, carriers=cmb_eval,
            content_id=_array_id({"carriers": cmb_eval}, role="wu008_cmbonly999_evaluation"),
        ),
    }
    source_identity = _canonical_id(
        {
            "registry_sha256": "sha256:" + EXPECTED_REGISTRY_SHA256,
            "calibration_content_id": calibration_id,
            "arm_content_ids": {name: arm.content_id for name, arm in arms.items()},
            "input_file_sha256": {name: "sha256:" + value for name, value in EXPECTED_INPUT_SHA256.items()},
        },
        role="wu008_map_free_inputs",
    )
    return PowerInputs(
        calibration_ids=calibration_ids,
        calibration_carriers=calibration,
        arms=arms,
        metadata=metadata,
        scale_rms=reference_scale(calibration),
        source_identity=source_identity,
    )


def cell_plan() -> tuple[Cell, ...]:
    result = [Cell("ZERO_BASELINE", 0.0, 1)]
    for template in template_bank():
        for amplitude in POSITIVE_AMPLITUDES:
            result.append(Cell(template.template_id, float(amplitude), 32))
    return tuple(result)


def positive_trial_count(arm: str) -> int:
    sizes = {"paired300": 100, "cmbonly999": 799}
    if arm not in sizes:
        raise Wu008Error("unknown WU-008 arm")
    return sizes[arm] * len(template_bank()) * len(POSITIVE_AMPLITUDES) * 32


def _checkpoint_paths(path: Path) -> tuple[Path, Path]:
    path = Path(path)
    return path.with_suffix(".npz"), path.with_suffix(".json")


def _validate_checkpoint_identity(identity: CheckpointIdentity) -> None:
    _require_identity(identity.candidate_git_head, git=True, label="candidate head")
    _require_identity(identity.candidate_git_tree, git=True, label="candidate tree")
    _require_identity(identity.registry_sha256, git=False, label="registry")
    _require_identity(identity.input_content_id, git=False, label="input")
    if identity.arm not in ("paired300", "cmbonly999") or not identity.template_id:
        raise Wu008Error("checkpoint cell identity is malformed")
    if not math.isfinite(identity.amplitude) or identity.amplitude < 0:
        raise Wu008Error("checkpoint amplitude is malformed")


def write_checkpoint(
    path: Path, *, identity: CheckpointIdentity, ranks: np.ndarray,
    absences: Sequence[Mapping[str, object]],
) -> None:
    _validate_checkpoint_identity(identity)
    array = np.asarray(ranks)
    if array.dtype != np.dtype("int32") or array.ndim != 5 or array.shape[-3:] != (2, 2, 2):
        raise Wu008Error("checkpoint rank array is malformed")
    if np.any((array < -1) | (array > 201)):
        raise Wu008Error("checkpoint rank numerator is outside the finite pool")
    package, metadata = _checkpoint_paths(path)
    if package.exists() or package.is_symlink() or metadata.exists() or metadata.is_symlink():
        raise Wu008Error("checkpoint output collision")
    absence_payload = [dict(value) for value in absences]
    _atomic_npz(package, {"ranks": array})
    _atomic_json(metadata, {
        "format": "PLANCK_MES_IRREP_POWER_PRIVATE_CELL_V1",
        "identity": asdict(identity),
        "ranks_content_id": _array_id({"ranks": array}, role="wu008_cell_ranks"),
        "absence_content_id": _canonical_id(absence_payload, role="wu008_cell_absences"),
        "absences": absence_payload,
    })


def load_checkpoint(
    path: Path, *, identity: CheckpointIdentity,
) -> tuple[np.ndarray, list[dict[str, object]]]:
    _validate_checkpoint_identity(identity)
    package, metadata = _checkpoint_paths(path)
    if package.is_symlink() or metadata.is_symlink() or not package.is_file() or not metadata.is_file():
        raise Wu008Error("checkpoint pair is missing or unsafe")
    payload = json.loads(metadata.read_text(encoding="utf-8"))
    if payload.get("format") != "PLANCK_MES_IRREP_POWER_PRIVATE_CELL_V1" or payload.get("identity") != asdict(identity):
        raise Wu008Error("checkpoint identity differs")
    with np.load(package, allow_pickle=False) as bundle:
        if set(bundle.files) != {"ranks"}:
            raise Wu008Error("checkpoint numerical schema differs")
        ranks = np.asarray(bundle["ranks"])
    absences = payload.get("absences")
    if (
        ranks.dtype != np.dtype("int32") or ranks.ndim != 5 or ranks.shape[-3:] != (2, 2, 2)
        or payload.get("ranks_content_id") != _array_id({"ranks": ranks}, role="wu008_cell_ranks")
        or not isinstance(absences, list)
        or payload.get("absence_content_id") != _canonical_id(absences, role="wu008_cell_absences")
    ):
        raise Wu008Error("checkpoint content identity differs")
    return ranks.copy(), [dict(value) for value in absences]


_WORKER_CONTEXT: dict[str, object] = {}


def _run_cell(cell: Cell) -> tuple[Cell, np.ndarray, list[dict[str, object]]]:
    context = _WORKER_CONTEXT
    templates = {template.template_id: template for template in template_bank()}
    template = templates["Q_AXIAL"] if cell.amplitude == 0 else templates[cell.template_id]
    ranks, absences = evaluate_cell(
        context["reference_features"], context["carriers"], template,
        cell.amplitude, context["scale_rms"], context["extractor"], TAILS,
        batch_size=32,
    )
    if ranks.shape[1] != cell.orientation_count:
        raise Wu008Error("cell orientation count differs")
    return cell, ranks, absences


def _checkpoint_stem(root: Path, arm: str, cell: Cell) -> Path:
    amplitude = str(cell.amplitude).replace(".", "p")
    return Path(root) / arm / f"{cell.template_id}__A{amplitude}"


def execute_arm(
    *, arm: str, output: Path, checkpoint_root: Path,
    candidate_git_head: str, candidate_git_tree: str, workers: int,
) -> dict[str, object]:
    _require_identity(candidate_git_head, git=True, label="candidate head")
    _require_identity(candidate_git_tree, git=True, label="candidate tree")
    if type(workers) is not int or workers < 1:
        raise Wu008Error("positive worker count required")
    inputs = load_accepted_inputs()
    if arm not in inputs.arms:
        raise Wu008Error("unknown WU-008 arm")
    checkpoint_root = Path(checkpoint_root)
    if checkpoint_root.is_symlink():
        raise Wu008Error("checkpoint root cannot be a symlink")
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    target = inputs.arms[arm]
    extractor, reference_features = make_extractor(
        dict(inputs.metadata), inputs.calibration_carriers, inputs.source_identity
    )
    global _WORKER_CONTEXT
    _WORKER_CONTEXT = {
        "reference_features": reference_features,
        "carriers": target.carriers,
        "scale_rms": inputs.scale_rms,
        "extractor": extractor,
    }
    registry_sha = "sha256:" + EXPECTED_REGISTRY_SHA256
    cells = cell_plan()
    completed: dict[tuple[str, float], tuple[np.ndarray, list[dict[str, object]]]] = {}
    missing: list[Cell] = []
    reused = 0
    for cell in cells:
        identity = CheckpointIdentity(
            candidate_git_head=candidate_git_head,
            candidate_git_tree=candidate_git_tree,
            registry_sha256=registry_sha,
            input_content_id=target.content_id,
            arm=arm, template_id=cell.template_id, amplitude=cell.amplitude,
        )
        stem = _checkpoint_stem(checkpoint_root, arm, cell)
        if stem.with_suffix(".npz").exists() or stem.with_suffix(".json").exists():
            completed[(cell.template_id, cell.amplitude)] = load_checkpoint(stem, identity=identity)
            reused += 1
        else:
            missing.append(cell)
    if missing and workers == 1:
        for ordinal, cell in enumerate(missing, 1):
            _, ranks, absences = _run_cell(cell)
            identity = CheckpointIdentity(
                candidate_git_head, candidate_git_tree, registry_sha,
                target.content_id, arm, cell.template_id, cell.amplitude,
            )
            stem = _checkpoint_stem(checkpoint_root, arm, cell)
            write_checkpoint(stem, identity=identity, ranks=ranks, absences=absences)
            completed[(cell.template_id, cell.amplitude)] = (ranks, absences)
            print(json.dumps({"arm": arm, "completed_new": ordinal, "remaining_new": len(missing)-ordinal, "template": cell.template_id, "amplitude": cell.amplitude}, sort_keys=True), flush=True)
    elif missing:
        context = multiprocessing.get_context("fork")
        with ProcessPoolExecutor(max_workers=workers, mp_context=context) as pool:
            futures = {pool.submit(_run_cell, cell): cell for cell in missing}
            for ordinal, future in enumerate(as_completed(futures), 1):
                cell, ranks, absences = future.result()
                identity = CheckpointIdentity(
                    candidate_git_head, candidate_git_tree, registry_sha,
                    target.content_id, arm, cell.template_id, cell.amplitude,
                )
                stem = _checkpoint_stem(checkpoint_root, arm, cell)
                write_checkpoint(stem, identity=identity, ranks=ranks, absences=absences)
                completed[(cell.template_id, cell.amplitude)] = (ranks, absences)
                print(json.dumps({"arm": arm, "completed_new": ordinal, "remaining_new": len(missing)-ordinal, "template": cell.template_id, "amplitude": cell.amplitude}, sort_keys=True), flush=True)
    zero, zero_absence = completed[("ZERO_BASELINE", 0.0)]
    templates = tuple(template.template_id for template in template_bank())
    positive = np.empty(
        (len(templates), len(POSITIVE_AMPLITUDES), len(target.carriers), 32, 2, 2, 2),
        dtype=np.int32,
    )
    all_absences = list(zero_absence)
    for template_index, template_id in enumerate(templates):
        for amplitude_index, amplitude in enumerate(POSITIVE_AMPLITUDES):
            ranks, absences = completed[(template_id, amplitude)]
            positive[template_index, amplitude_index] = ranks
            for value in absences:
                all_absences.append({"template_id": template_id, "amplitude": amplitude, **value})
    arrays = {
        "zero_ranks": zero,
        "positive_ranks": positive,
        "evaluation_ids": np.asarray(target.ids),
        "template_ids": np.asarray(templates),
        "positive_amplitudes": np.asarray(POSITIVE_AMPLITUDES, dtype=np.float64),
        "family_ids": np.asarray(FAMILIES),
        "reducer_ids": np.asarray(REDUCERS),
        "combiner_ids": np.asarray(COMBINERS),
    }
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    package = output / f"{arm}_trials.npz"
    _atomic_npz(package, arrays)
    result = {
        "format": "PLANCK_MES_IRREP_POWER_ARM_EXECUTION_V1",
        "arm": arm,
        "state": "SUCCEEDED",
        "candidate_git_head": candidate_git_head,
        "candidate_git_tree": candidate_git_tree,
        "registry_sha256": registry_sha,
        "input_content_id": target.content_id,
        "shared_calibration_source_identity": inputs.source_identity,
        "calibration_count": 200,
        "evaluation_sky_count": len(target.carriers),
        "positive_injected_carriers": positive_trial_count(arm),
        "zero_amplitude_sky_count": len(target.carriers),
        "zero_amplitude_computed_once": True,
        "typed_absence_count": len(all_absences),
        "typed_absences": all_absences,
        "scale_rms_microK_CMB": inputs.scale_rms,
        "checkpoint_reused_cells": reused,
        "checkpoint_new_cells": len(missing),
        "trial_package": package.name,
        "trial_package_sha256": "sha256:" + _sha256(package),
        "trial_content_id": _array_id(arrays, role=f"wu008_{arm}_trials"),
        "raw_maps_reopened": False,
        "observation_used_for_power": False,
    }
    _atomic_json(output / f"{arm}_execution.json", result)
    return result


def _load_arm(output: Path, arm: str) -> tuple[dict[str, object], dict[str, np.ndarray]]:
    metadata_path = Path(output) / f"{arm}_execution.json"
    package = Path(output) / f"{arm}_trials.npz"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("state") != "SUCCEEDED" or metadata.get("trial_package_sha256") != "sha256:" + _sha256(package):
        raise Wu008Error(f"{arm} execution identity differs")
    with np.load(package, allow_pickle=False) as bundle:
        arrays = {name: np.asarray(bundle[name]) for name in bundle.files}
    if metadata.get("trial_content_id") != _array_id(arrays, role=f"wu008_{arm}_trials"):
        raise Wu008Error(f"{arm} decoded trial content differs")
    return metadata, arrays


def _decision_summary(ranks: np.ndarray) -> dict[str, object]:
    decisions = np.where(ranks < 0, np.nan, ranks <= LARGEST_REJECTING_NUMERATOR)
    return summarize_decisions(decisions)


def build_summaries(output: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    summaries: list[dict[str, object]] = []
    thresholds: list[dict[str, object]] = []
    for arm in ("paired300", "cmbonly999"):
        _, arrays = _load_arm(output, arm)
        zero = arrays["zero_ranks"]
        positive = arrays["positive_ranks"]
        templates = tuple(map(str, arrays["template_ids"].tolist()))
        for family_index, family in enumerate(FAMILIES):
            for reducer_index, reducer in enumerate(REDUCERS):
                for combiner_index, combiner in enumerate(COMBINERS):
                    baseline = _decision_summary(
                        zero[:, :, family_index, reducer_index, combiner_index]
                    )
                    summaries.append({
                        "arm": arm, "template_id": "ZERO_BASELINE", "amplitude": 0.0,
                        "family": family, "reducer": reducer, "combiner": combiner,
                        **baseline,
                    })
                    for template_index, template_id in enumerate(templates):
                        powers: list[float | None] = [baseline["power"]]
                        for amplitude_index, amplitude in enumerate(POSITIVE_AMPLITUDES):
                            summary = _decision_summary(
                                positive[template_index, amplitude_index, :, :, family_index, reducer_index, combiner_index]
                            )
                            powers.append(summary["power"])
                            summaries.append({
                                "arm": arm, "template_id": template_id,
                                "amplitude": float(amplitude), "family": family,
                                "reducer": reducer, "combiner": combiner, **summary,
                            })
                        for target in (0.5, 0.9):
                            crossing = threshold_crossings(AMPLITUDES, powers, target)
                            thresholds.append({
                                "arm": arm, "template_id": template_id, "family": family,
                                "reducer": reducer, "combiner": combiner,
                                "target_power": target, "status": crossing["status"],
                                "crossings_json": json.dumps(crossing["crossings"], sort_keys=True),
                                "monotonic_non_decreasing": crossing["monotonic_non_decreasing"],
                                "interpolation_or_extrapolation_performed": False,
                            })
    return summaries, thresholds


def _comparison_rows(summaries: Sequence[Mapping[str, object]]) -> list[dict[str, object]]:
    keyed = {
        (row["arm"], row["template_id"], row["amplitude"], row["reducer"], row["combiner"], row["family"]): row
        for row in summaries
    }
    result = []
    for key, scalar in keyed.items():
        arm, template, amplitude, reducer, combiner, family = key
        if family != FAMILIES[0] or template == "ZERO_BASELINE":
            continue
        irrep = keyed[(arm, template, amplitude, reducer, combiner, FAMILIES[1])]
        result.append({
            "arm": arm, "template_id": template, "amplitude": amplitude,
            "reducer": reducer, "combiner": combiner,
            "scalar_power": scalar["power"], "irrep_power": irrep["power"],
            "irrep_minus_scalar": None if scalar["power"] is None or irrep["power"] is None else float(irrep["power"])-float(scalar["power"]),
            "arms_are_independent_replications": False,
        })
    return result


def build_template_power_heatmap(summaries: Sequence[Mapping[str, object]]):
    """Return the readable 2x2 template-resolved ECDF/min-power figure."""

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    lookup = {
        (
            row["arm"], row["template_id"], float(row["amplitude"]),
            row["family"], row["reducer"], row["combiner"],
        ): row
        for row in summaries
    }
    templates = tuple(template.template_id for template in template_bank())
    fig, axes = plt.subplots(
        2, 2, figsize=(9.0, 7.0), sharex=True, sharey=True,
        layout="constrained",
    )
    image = None
    for axis, (arm, family) in zip(
        axes.ravel(),
        ((arm, family) for arm in ("paired300", "cmbonly999") for family in FAMILIES),
        strict=True,
    ):
        matrix = np.asarray(
            [
                [
                    lookup[(arm, template, float(amplitude), family, ECDF, COMBINERS[0])]["power"]
                    for amplitude in POSITIVE_AMPLITUDES
                ]
                for template in templates
            ],
            dtype=float,
        )
        image = axis.imshow(matrix, aspect="auto", vmin=0, vmax=1, cmap="viridis")
        axis.set_xticks(
            range(len(POSITIVE_AMPLITUDES)),
            [str(amplitude) for amplitude in POSITIVE_AMPLITUDES],
            rotation=45,
        )
        axis.set_yticks(range(len(templates)), templates, fontsize=7)
        axis.set_title(f"{arm}: {family.replace('FROZEN_', '')}", fontsize=9)
        axis.set_xlabel("Registered amplitude A")
    if image is None:
        raise Wu008Error("template heatmap has no registered cells")
    fig.colorbar(image, ax=axes.ravel().tolist(), label="Power", shrink=0.82)
    fig.suptitle("Template-resolved ECDF/min-local-p power", fontsize=12)
    return fig


def _build_figures(output: Path, summaries: Sequence[Mapping[str, object]], comparisons: Sequence[Mapping[str, object]]) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output = Path(output)
    lookup = {
        (row["arm"], row["template_id"], float(row["amplitude"]), row["family"], row["reducer"], row["combiner"]): row
        for row in summaries
    }
    templates = tuple(template.template_id for template in template_bank())
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 7.0), sharex=True, sharey=True)
    for row_index, arm in enumerate(("paired300", "cmbonly999")):
        for column_index, family in enumerate(FAMILIES):
            axis = axes[row_index, column_index]
            for reducer, linestyle in zip(REDUCERS, ("-", "--"), strict=True):
                for combiner, marker in zip(COMBINERS, ("o", "s"), strict=True):
                    values=[]
                    baseline=lookup[(arm,"ZERO_BASELINE",0.0,family,reducer,combiner)]["power"]
                    values.append(baseline)
                    for amplitude in POSITIVE_AMPLITUDES:
                        sample=[lookup[(arm,t,float(amplitude),family,reducer,combiner)]["power"] for t in templates]
                        values.append(float(np.mean(sample)) if all(v is not None for v in sample) else np.nan)
                    axis.plot(AMPLITUDES,values,linestyle=linestyle,marker=marker,ms=3,label=f"{reducer.split('_')[0]} / {combiner.split('_')[0]}")
            axis.axhline(0.5,color="0.75",lw=.7);axis.axhline(0.9,color="0.75",lw=.7)
            axis.set_title(f"{arm}: {family.replace('FROZEN_','')}")
            axis.set_ylim(-.02,1.02);axis.grid(alpha=.2)
    axes[1,0].set_xlabel("Registered amplitude A");axes[1,1].set_xlabel("Registered amplitude A")
    axes[0,0].set_ylabel("Power");axes[1,0].set_ylabel("Power")
    axes[0,0].legend(fontsize=6,ncol=2)
    fig.suptitle("Method power at 200-reference calibration (template average)")
    fig.tight_layout();fig.savefig(output/FIGURES[0],bbox_inches="tight");plt.close(fig)

    fig = build_template_power_heatmap(summaries)
    fig.savefig(output/FIGURES[1],bbox_inches="tight");plt.close(fig)

    fig, axes = plt.subplots(1,2,figsize=(9.5,3.8),sharey=True)
    for axis,arm in zip(axes,("paired300","cmbonly999"),strict=True):
        for reducer,linestyle in zip(REDUCERS,("-","--"),strict=True):
            for combiner,marker in zip(COMBINERS,("o","s"),strict=True):
                values=[]
                for amplitude in POSITIVE_AMPLITUDES:
                    sample=[row["irrep_minus_scalar"] for row in comparisons if row["arm"]==arm and row["reducer"]==reducer and row["combiner"]==combiner and float(row["amplitude"])==float(amplitude)]
                    values.append(float(np.mean(sample)))
                axis.plot(POSITIVE_AMPLITUDES,values,linestyle=linestyle,marker=marker,ms=3,label=f"{reducer.split('_')[0]} / {combiner.split('_')[0]}")
        axis.axhline(0,color="black",lw=.7);axis.grid(alpha=.2);axis.set_title(arm);axis.set_xlabel("A")
    axes[0].set_ylabel("Irrep power minus MES-10 power");axes[0].legend(fontsize=6,ncol=2)
    fig.suptitle("Frozen-family method-power contrast (template average)")
    fig.tight_layout();fig.savefig(output/FIGURES[2],bbox_inches="tight");plt.close(fig)

    fig,axis=plt.subplots(figsize=(7.2,4.3))
    colors={"paired300":"tab:blue","cmbonly999":"tab:orange"}
    for arm in colors:
        points=[row for row in summaries if row["arm"]==arm and row["template_id"]!="ZERO_BASELINE" and row["orientation_prefix_difference"] is not None]
        axis.scatter([row["power"] for row in points],[row["orientation_prefix_difference"] for row in points],s=10,alpha=.5,label=arm,color=colors[arm])
    axis.axhline(0,color="black",lw=.7);axis.set_xlabel("Full-32 orientation-averaged power");axis.set_ylabel("First-16 minus full-32 power");axis.grid(alpha=.2);axis.legend()
    axis.set_title("Descriptive orientation-prefix sensitivity")
    fig.tight_layout();fig.savefig(output/FIGURES[3],bbox_inches="tight");plt.close(fig)


def assemble_outputs(
    *, output: Path, candidate_git_head: str, candidate_git_tree: str,
    evidence_repair_git_head: str, evidence_repair_git_tree: str,
) -> dict[str, object]:
    _require_identity(candidate_git_head, git=True, label="candidate head")
    _require_identity(candidate_git_tree, git=True, label="candidate tree")
    _require_identity(evidence_repair_git_head, git=True, label="evidence repair head")
    _require_identity(evidence_repair_git_tree, git=True, label="evidence repair tree")
    output = Path(output);output.mkdir(parents=True, exist_ok=True)
    registry=load_registry();inputs=load_accepted_inputs()
    arms={arm:_load_arm(output,arm)[0] for arm in ("paired300","cmbonly999")}
    for metadata in arms.values():
        if metadata["candidate_git_head"]!=candidate_git_head or metadata["candidate_git_tree"]!=candidate_git_tree:
            raise Wu008Error("arm execution candidate identity differs")
    summaries,thresholds=build_summaries(output)
    comparisons=_comparison_rows(summaries)
    _write_csv(output/"power_table.csv",summaries)
    _write_csv(output/"threshold_crossings.csv",thresholds)
    _write_csv(output/"scalar_irrep_comparison.csv",comparisons)
    orientation=[{
        "arm":row["arm"],"template_id":row["template_id"],"amplitude":row["amplitude"],
        "family":row["family"],"reducer":row["reducer"],"combiner":row["combiner"],
        "full32_power":row["power"],"first16_minus_full32":row["orientation_prefix_difference"],
        "interpretation":"DESCRIPTIVE_QUADRATURE_SENSITIVITY_NOT_CONTINUUM_CONVERGENCE",
    } for row in summaries if row["template_id"]!="ZERO_BASELINE"]
    _write_csv(output/"orientation_sensitivity.csv",orientation)
    _build_figures(output,summaries,comparisons)
    claim_metadata = build_claim_metadata(
        registry=registry,
        input_source_identity=inputs.source_identity,
        candidate_git_head=candidate_git_head,
        candidate_git_tree=candidate_git_tree,
        evidence_repair_git_head=evidence_repair_git_head,
        evidence_repair_git_tree=evidence_repair_git_tree,
    )
    validate_claim_metadata(claim_metadata, registry=registry)
    result={
        "format":FORMAT,"work_unit":"PMG-WU-008","state":"EXECUTED_PENDING_REVIEW",
        "candidate_git_head":candidate_git_head,"candidate_git_tree":candidate_git_tree,
        "evidence_repair_git_head":evidence_repair_git_head,
        "evidence_repair_git_tree":evidence_repair_git_tree,
        "registry_sha256":"sha256:"+EXPECTED_REGISTRY_SHA256,
        "input_source_identity":inputs.source_identity,
        "arms":arms,"families":list(FAMILIES),"reducers":list(REDUCERS),"combiners":list(COMBINERS),
        "amplitudes":list(AMPLITUDES),"template_ids":[t.template_id for t in template_bank()],
        "finite_rank_denominator":201,"largest_rejecting_rank_numerator":10,
        "summary_row_count":len(summaries),"threshold_row_count":len(thresholds),
        "typed_absence_count":sum(int(value["typed_absence_count"]) for value in arms.values()),
        "raw_maps_reopened":False,"observation_used_for_power":False,"raw_data_mutation":False,
        "claim_promotion":False,"physical_template_status":"DEFERRED_NOT_ATTEMPTED_WITHOUT_AUTHORIZED_RESPONSE",
        "claim_metadata":claim_metadata,
        "replay_semantics":"COMMITTED_ARTIFACT_INTEGRITY_AND_SUMMARY_CONTENT_NOT_FULL_NUMERICAL_REGENERATION",
        "scope_limitation":registry["scope_limitation"],
        "arm_dependence":"OVERLAPPING_CMB_SIMULATION_IDENTITIES_NOT_INDEPENDENT_REPLICATIONS",
        "A50_A90":"GRID_BRACKETS_ONLY_NO_INTERPOLATION_OR_EXTRAPOLATION",
        "allowed_claim":"CONDITIONAL_METHOD_POWER_FOR_REGISTERED_200_REFERENCE_FUNCTIONAL",
        "forbidden_claims":["power calibration of the original full301 or full1000 observation procedures","physical shear or vorticity sensitivity","Bianchi-family sensitivity","independent replication across the two arms"],
    }
    result["content_id"]=_canonical_id({k:v for k,v in result.items() if k!="content_id"},role="wu008_result")
    _atomic_json(output/"result.json",result)
    artifact_hashes={name:"sha256:"+_sha256(output/name) for name in OBJECTIVE_ARTIFACTS}
    manifest={
        "format":"PLANCK_MES_IRREP_POWER_ARTIFACT_MANIFEST_V1",
        "candidate_git_head":candidate_git_head,"candidate_git_tree":candidate_git_tree,
        "evidence_repair_git_head":evidence_repair_git_head,
        "evidence_repair_git_tree":evidence_repair_git_tree,
        "registry_sha256":"sha256:"+EXPECTED_REGISTRY_SHA256,
        "input_source_identity":inputs.source_identity,"artifacts":artifact_hashes,
        "claim_metadata":claim_metadata,
    }
    manifest["content_id"]=_canonical_id({k:v for k,v in manifest.items() if k!="content_id"},role="wu008_artifact_manifest")
    _atomic_json(output/"artifact_manifest.json",manifest)
    pending={
        "format":TERMINAL_FORMAT,"work_unit":"PMG-WU-008","state":"EXECUTED_PENDING_REVIEW",
        "candidate_git_head":candidate_git_head,"candidate_git_tree":candidate_git_tree,
        "evidence_repair_git_head":evidence_repair_git_head,
        "evidence_repair_git_tree":evidence_repair_git_tree,
        "artifact_manifest_content_id":manifest["content_id"],"real_host_execution":True,
        "replay_status":"MATCH","raw_maps_reopened":False,"raw_data_mutation":False,
        "observation_used_for_power":False,"claim_promotion":False,
        "P0_remaining":None,"P1_remaining":None,"unresolved_blockers":["FRESH_REVIEW_PENDING"],
        "next_executable_action":"FRESH_READ_ONLY_REVIEW",
    }
    _atomic_json(output/"terminal.pending.json",pending)
    replay=replay_directory(output,require_terminal=False)
    _atomic_json(output/"replay.json",replay)
    return result


def replay_directory(output: Path=OUTPUT_DIR, *, require_terminal: bool=True) -> dict[str, object]:
    output=Path(output)
    registry=load_registry()
    manifest=json.loads((output/"artifact_manifest.json").read_text(encoding="utf-8"))
    content=_canonical_id({k:v for k,v in manifest.items() if k!="content_id"},role="wu008_artifact_manifest")
    if content!=manifest.get("content_id"):
        raise Wu008Error("artifact manifest content identity differs")
    for name,expected in manifest.get("artifacts",{}).items():
        path=output/name
        if path.is_symlink() or not path.is_file() or "sha256:"+_sha256(path)!=expected:
            raise Wu008Error(f"portable artifact identity differs: {name}")
    for arm in ("paired300","cmbonly999"):_load_arm(output,arm)
    result=json.loads((output/"result.json").read_text(encoding="utf-8"))
    expected_result=_canonical_id({k:v for k,v in result.items() if k!="content_id"},role="wu008_result")
    if result.get("content_id")!=expected_result or result.get("raw_maps_reopened") is not False:
        raise Wu008Error("result semantic content differs")
    validate_claim_metadata(manifest.get("claim_metadata", {}), registry=registry)
    if result.get("claim_metadata") != manifest.get("claim_metadata"):
        raise Wu008Error("result and manifest claim metadata differ")
    if require_terminal:
        terminal=json.loads((output/"terminal.json").read_text(encoding="utf-8"))
        if terminal.get("state")!="SUCCEEDED" or terminal.get("artifact_manifest_content_id")!=manifest["content_id"]:
            raise Wu008Error("reviewed terminal is absent or differs")
    return {
        "format":"PLANCK_MES_IRREP_POWER_MAP_FREE_REPLAY_V1","status":"MATCH",
        "replay_semantics":"COMMITTED_ARTIFACT_INTEGRITY_AND_SUMMARY_CONTENT_NOT_FULL_NUMERICAL_REGENERATION",
        "artifact_manifest_content_id":manifest["content_id"],"result_content_id":result["content_id"],
        "raw_maps_reopened":False,"observation_used_for_power":False,
    }


def finalize_terminal(pending: Mapping[str, object], review: Mapping[str, object]) -> dict[str, object]:
    if pending.get("format")!=TERMINAL_FORMAT or pending.get("state")!="EXECUTED_PENDING_REVIEW":
        raise Wu008Error("pending terminal state differs")
    required_review={
        "format":REVIEW_FORMAT,"state":"PASS","candidate_git_head":pending.get("candidate_git_head"),
        "candidate_git_tree":pending.get("candidate_git_tree"),
        "artifact_manifest_content_id":pending.get("artifact_manifest_content_id"),
        "P0_remaining":0,"P1_remaining":0,"plot_inspection":"PASS",
    }
    if any(review.get(key)!=value for key,value in required_review.items()):
        raise Wu008Error("fresh review candidate or artifact identity differs")
    if review.get("repair_rounds_used") not in (0,1):
        raise Wu008Error("fresh review repair budget differs")
    return {
        **dict(pending),"state":"SUCCEEDED","fresh_review":"PASS",
        "fresh_review_content_id":_canonical_id(dict(review),role="wu008_fresh_review"),
        "review_repair_count":int(review["repair_rounds_used"]),"P0_remaining":0,"P1_remaining":0,
        "unresolved_blockers":[],"next_executable_action":"PMG-WU-009",
    }


def _parser() -> argparse.ArgumentParser:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute",action="store_true",help="execute one registered map-free arm")
    parser.add_argument("--arm",choices=("paired300","cmbonly999"))
    parser.add_argument("--assemble",action="store_true",help="assemble both executed arms and pending evidence")
    parser.add_argument("--finalize-review",type=Path,help="install an exact independent review receipt")
    parser.add_argument("--replay-committed",action="store_true",help="map-free replay of reviewed committed artifacts")
    parser.add_argument("--output",type=Path,default=OUTPUT_DIR)
    parser.add_argument("--checkpoint-root",type=Path)
    parser.add_argument("--candidate-git-head")
    parser.add_argument("--candidate-git-tree")
    parser.add_argument("--evidence-repair-git-head")
    parser.add_argument("--evidence-repair-git-tree")
    parser.add_argument("--workers",type=int,default=1)
    return parser


def main(argv: Sequence[str]|None=None) -> int:
    args=_parser().parse_args(argv)
    modes=sum((bool(args.execute),bool(args.assemble),args.finalize_review is not None,bool(args.replay_committed)))
    if modes!=1:raise Wu008Error("select exactly one execution, assembly, finalization, or replay mode")
    if args.execute:
        if args.arm is None or args.checkpoint_root is None:raise Wu008Error("--execute requires --arm and --checkpoint-root")
        result=execute_arm(arm=args.arm,output=args.output,checkpoint_root=args.checkpoint_root,candidate_git_head=args.candidate_git_head,candidate_git_tree=args.candidate_git_tree,workers=args.workers)
    elif args.assemble:
        result=assemble_outputs(
            output=args.output,
            candidate_git_head=args.candidate_git_head,
            candidate_git_tree=args.candidate_git_tree,
            evidence_repair_git_head=args.evidence_repair_git_head,
            evidence_repair_git_tree=args.evidence_repair_git_tree,
        )
    elif args.finalize_review is not None:
        pending=json.loads((args.output/"terminal.pending.json").read_text(encoding="utf-8"))
        review=json.loads(args.finalize_review.read_text(encoding="utf-8"))
        result=finalize_terminal(pending,review)
        _atomic_json(args.output/"terminal.json",result)
        _atomic_json(args.output/"replay.json",replay_directory(args.output))
    else:
        result=replay_directory(args.output)
    print(json.dumps(result,indent=2,sort_keys=True,allow_nan=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
