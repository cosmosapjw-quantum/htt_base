#!/usr/bin/env python3
"""Planck PR3 low-ell worker and synthetic/null profile harness.

``--synthetic-profile`` never opens admitted or observed products.  The
``--run-admitted`` mode is a production entrypoint for the attended PR-305
executor; this PR defines and tests it but does not invoke it on observed data.
"""

from __future__ import annotations

import os

for _name in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
):
    os.environ[_name] = "1"

import argparse
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import hashlib
import json
import math
import multiprocessing
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time
from typing import Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT / "htt", ROOT / "htt/src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from common.data_identity import (  # noqa: E402
    AdmissionStatus,
    DataIdentityError,
    _regular_beneath,
    _stream_sha256,
    load_lane_registry,
    replay_lane_admission_decision,
)
from obsstat.boost_biposh_residual import ExactBoostOperator  # noqa: E402
from obsstat.planck_post275_lane import validate_full_joint_covariance  # noqa: E402
from obsstat.planck_pr3_operator import (  # noqa: E402
    COMPONENT_FEATURE_IDS,
    EXPECTED_FFP10_NULL_ROWS,
    FFP10Inventory,
    GLOBAL_CLAIM_BOUNDARY,
    JOINT_FEATURE_IDS,
    LMAX,
    LMIN,
    MaskCouplingInverse,
    PlanckLaneContractError,
    alm_to_real_vector,
    build_mask_coupling_inverse,
    calibrate_complete_synthetic_pool,
    capability_snapshot,
    commonize_beam_pixel_alm,
    component_features_from_vectors,
    covariance_whitened_response_rank,
    estimate_matched_joint_covariance,
    extract_multipole_vectors,
    ordered_row_id_hash,
    real_vector_to_alm,
    remove_weighted_monopole_dipole,
)


SCHEMA = "htt.planck_pr3_profile.v1"
STAGES = (
    "input",
    "beam_pixel",
    "mask_inverse",
    "map2alm",
    "multipole_vectors",
    "features",
    "covariance",
    "null_calibration",
    "global_rank",
    "serialization",
)
THREAD_CONTROLS = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
}
REGISTRY = (
    ROOT / "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"
)
PROFILE_MODES = ("serial", "thread", "process")
ROW_LABELS = ("1", "8", "32", "128", "full")
PROFILE_MATRIX = (
    *((rows, "serial", 1) for rows in ROW_LABELS),
    *(
        (rows, mode, 2)
        for mode in ("thread", "process")
        for rows in ("8", "32", "128", "full")
    ),
)
RUST_GATE = "KEEP_PYTHON_NO_ELIGIBLE_POST_OPTIMIZATION_LEAF"
FFP10_RELEASE_ID = "planck:ffp10:pr3:cmb:same-sky:v1"
SMICA_EXISTING_NULL_ROWS = 300
SMICA_EXISTING_ROW_IDS = tuple(
    f"FFP10-SMICA-CMBNOISE-{index:05d}" for index in range(SMICA_EXISTING_NULL_ROWS)
)
SMICA_EXISTING_INVENTORY_ID = ordered_row_id_hash(SMICA_EXISTING_ROW_IDS)
SYNTHETIC_NULL_ROW_IDS = tuple(
    f"FFP10-{index:04d}" for index in range(EXPECTED_FFP10_NULL_ROWS)
)
SYNTHETIC_NULL_INVENTORY_ID = ordered_row_id_hash(SYNTHETIC_NULL_ROW_IDS)
REQUIRED_ADMITTED_COMPONENTS = frozenset(
    {
        "smica_map",
        "commander_map",
        "smica_mask",
        "commander_mask",
        "smica_beam",
        "commander_beam",
        "smica_window_operator",
        "commander_window_operator",
        "smica_covariance",
        "commander_covariance",
        "pixelization",
        "native_selection",
        "ffp10_null_inventory",
    }
)
PROFILE_CONSTANT_FIELDS = (
    "schema",
    "capability",
    "profile_kind",
    "thread_controls",
    "feature_order",
    "global_response_status",
    "global_claim_boundary",
    "rust_gate",
    "observed_statistic_seen",
    "observed_science_executed",
    "capability_snapshot",
)


class PlanckWorkerError(RuntimeError):
    """Raised when worker input, operator, or profile contracts drift."""


def _artifact_metadata(*, observed: bool) -> dict[str, object]:
    metadata: dict[str, object] = {
        "owner": "OBSSTAT",
        "scope": "Planck PR3 low-ell operator diagnostic",
        "claim_tier": "transfer_conditional_diagnostic_only",
        "allowed_use": [
            "operator validation",
            "matched-null calibration diagnostic",
        ],
        "forbidden_use": [
            "global tilt claim",
            "native transfer claim",
            "Bianchi family identification",
        ],
        "source_identity": (
            "content-bound admitted Planck PR3 products"
            if observed
            else "deterministic synthetic same-sky Gaussian pairs"
        ),
        "transfer_source": (
            "Planck PR3 products; no native Bianchi transfer"
            if observed
            else "NOT_APPLICABLE_SYNTHETIC_PROFILE"
        ),
        "sky_support_status": (
            "ADMITTED_PLANCK_PR3_COMMON_MASK" if observed else "SYNTHETIC_SKY_ONLY"
        ),
        "null_mock_status": (
            "CONTENT_BOUND_COMPLETE_FFP10_REQUIRED"
            if observed
            else "SYNTHETIC_PROFILE_ROWS"
        ),
        "covariance_status": "MATCHED_SAME_SKY_FULL_CROSS_BLOCK",
        "generating_procedure": "scripts/observed_runs/run_planck_pr3.py",
        "caveats": [
            "global response unavailable",
            "synthetic local response is not an observed response model",
            "family identification blocked before a native morphology atlas",
        ],
        "non_claim_bearing": not observed,
    }
    if observed:
        commit = os.environ.get("HTT_ATTENDED_CANDIDATE_COMMIT", "")
        tree = os.environ.get("HTT_ATTENDED_CANDIDATE_TREE", "")
        if any(
            len(value) != 40
            or any(character not in "0123456789abcdef" for character in value)
            for value in (commit, tree)
        ):
            raise PlanckWorkerError(
                "attended candidate identity is missing or malformed"
            )
        metadata.update(candidate_commit=commit, candidate_tree=tree)
    return metadata


def _now() -> int:
    return time.perf_counter_ns()


def _seconds(start: int) -> float:
    return (time.perf_counter_ns() - start) / 1_000_000_000.0


def _stage_template() -> dict[str, dict[str, object]]:
    return {name: {"status": "NOT_RUN", "seconds": 0.0} for name in STAGES}


def _add_stage(stages: dict[str, dict[str, object]], name: str, seconds: float) -> None:
    if name not in stages or not math.isfinite(seconds) or seconds < 0.0:
        raise PlanckWorkerError("stage timing contract drifted")
    stages[name]["status"] = "EXECUTED"
    stages[name]["seconds"] = float(stages[name]["seconds"]) + seconds


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _array_digest(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(array.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(array.shape).encode("ascii") + b"\0")
    digest.update(memoryview(array).cast("B"))
    return "sha256:" + digest.hexdigest()


def _atomic_npy(path: Path, value: np.ndarray) -> None:
    """Write one deterministic numeric replay input without pickle."""

    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as handle:
            np.save(handle, np.asarray(value, dtype=np.float64), allow_pickle=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def write_compact_smica_observed_replay_input(
    *, output_dir: Path, smica_map: np.ndarray, nside: int
) -> dict[str, object]:
    """Retain the one band-limited SMICA map used by the diagnostic."""

    import healpy as hp

    value = np.asarray(smica_map, dtype=np.float64)
    if (
        not hp.isnsideok(nside)
        or value.shape != (hp.nside2npix(nside),)
        or not np.all(np.isfinite(value))
        or output_dir.is_symlink()
        or not output_dir.is_dir()
    ):
        raise PlanckWorkerError("compact SMICA replay input is malformed")
    filename = "planck_pr3_observed_smica_bandlimited.npy"
    path = output_dir / filename
    if path.exists() or path.is_symlink():
        raise PlanckWorkerError("compact SMICA replay output already exists")
    _atomic_npy(path, value)
    return {
        "filename": filename,
        "sha256": _sha256_file(path),
        "shape": [value.size],
        "representation": "NUMPY_NPY_FLOAT64_NO_PICKLE",
        "map_unit": "microK_CMB",
        "coordinate_frame": "GALACTIC",
        "ordering": "RING",
        "lmax": LMAX,
        "null_ensemble_scope": "FFP10_SMICA_CMB_PLUS_NOISE_300",
    }


def _max_rss_bytes() -> int:
    own = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    children = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    # Linux reports KiB.  This worker is Linux-only by the attended contract.
    return int(max(own, children) * 1024)


def _synthetic_context(*, nside: int = 8) -> dict[str, object]:
    import healpy as hp

    npix = hp.nside2npix(nside)
    _, _, z = hp.pix2vec(nside, np.arange(npix))
    common_mask = (np.abs(z) >= 0.22).astype(float)
    # A small apodized boundary makes the inverse nontrivial without hiding a
    # pseudoinverse or data-dependent regularization.
    common_mask[(np.abs(z) >= 0.22) & (np.abs(z) < 0.30)] = 0.5
    ell = np.arange(LMAX + 1, dtype=float)
    smica_beam = np.exp(-ell * (ell + 1.0) * 0.0010)
    commander_beam = np.exp(-ell * (ell + 1.0) * 0.0014)
    source_pixel = np.asarray(hp.pixwin(nside, lmax=LMAX), dtype=float)
    target_beam = np.minimum(smica_beam, commander_beam)
    target_pixel = source_pixel.copy()
    inverse = build_mask_coupling_inverse(common_mask, lmin=LMIN, lmax=LMAX)
    return {
        "nside": nside,
        "common_mask": common_mask,
        "source_beams": {"SMICA": smica_beam, "Commander": commander_beam},
        "source_pixels": {"SMICA": source_pixel, "Commander": source_pixel},
        "target_beam": target_beam,
        "target_pixel": target_pixel,
        "mask_inverse": inverse,
    }


def _synthetic_pair(seed: int, *, nside: int) -> tuple[np.ndarray, np.ndarray]:
    import healpy as hp

    rng = np.random.default_rng(seed)
    dimension = len(alm_to_real_vector(np.zeros(hp.Alm.getsize(LMAX)), lmax=LMAX))
    shared = rng.normal(size=dimension)
    smica = shared + 0.18 * rng.normal(size=dimension)
    commander = 0.92 * shared + 0.22 * rng.normal(size=dimension)
    smica_map = hp.alm2map(real_vector_to_alm(smica, lmax=LMAX), nside=nside, lmax=LMAX)
    commander_map = hp.alm2map(
        real_vector_to_alm(commander, lmax=LMAX), nside=nside, lmax=LMAX
    )
    return np.asarray(smica_map), np.asarray(commander_map)


def _process_map(
    pixel_map: np.ndarray,
    *,
    component: str,
    context: Mapping[str, object],
) -> tuple[np.ndarray, dict[str, float], np.ndarray]:
    import healpy as hp

    timings = {name: 0.0 for name in STAGES}
    mask = np.asarray(context["common_mask"], dtype=float)
    inverse = context["mask_inverse"]
    if not isinstance(inverse, MaskCouplingInverse):
        raise PlanckWorkerError("mask-inverse context drifted")

    started = _now()
    cleaned = remove_weighted_monopole_dipole(pixel_map, mask)
    timings["input"] += _seconds(started)

    started = _now()
    raw_alm = hp.map2alm(cleaned, lmax=LMAX, iter=0, pol=False)
    timings["map2alm"] += _seconds(started)

    started = _now()
    common_alm = commonize_beam_pixel_alm(
        raw_alm,
        source_beam=context["source_beams"][component],
        source_pixel_window=context["source_pixels"][component],
        target_beam=context["target_beam"],
        target_pixel_window=context["target_pixel"],
        lmax=LMAX,
    )
    common_map = hp.alm2map(common_alm, nside=inverse.nside, lmax=LMAX, pol=False)
    timings["beam_pixel"] += _seconds(started)

    started = _now()
    pseudo = hp.map2alm(mask * common_map, lmax=LMAX, iter=0, pol=False)
    timings["map2alm"] += _seconds(started)

    started = _now()
    solved = inverse.inverse @ alm_to_real_vector(pseudo, lmin=LMIN, lmax=LMAX)
    alm = real_vector_to_alm(solved, lmin=LMIN, lmax=LMAX)
    timings["mask_inverse"] += _seconds(started)

    started = _now()
    vectors2 = extract_multipole_vectors(alm, ell=2, lmax=LMAX)
    vectors3 = extract_multipole_vectors(alm, ell=3, lmax=LMAX)
    timings["multipole_vectors"] += _seconds(started)

    started = _now()
    features = component_features_from_vectors(
        alm, vectors2=vectors2, vectors3=vectors3, lmax=LMAX
    )
    timings["features"] += _seconds(started)
    return features, timings, alm


def _evaluate_synthetic_row(
    ordinal: int, context: Mapping[str, object]
) -> tuple[int, np.ndarray, np.ndarray, dict[str, float]]:
    started = _now()
    smica_map, commander_map = _synthetic_pair(
        30_600_000 + ordinal, nside=int(context["nside"])
    )
    input_seconds = _seconds(started)
    smica, smica_timing, _ = _process_map(smica_map, component="SMICA", context=context)
    commander, commander_timing, _ = _process_map(
        commander_map, component="Commander", context=context
    )
    timing = {name: smica_timing[name] + commander_timing[name] for name in STAGES}
    timing["input"] += input_seconds
    return ordinal, smica, commander, timing


def _evaluate_synthetic_observation(
    context: Mapping[str, object],
) -> tuple[np.ndarray, dict[str, float]]:
    """Build one frozen profile observation independent of every null seed."""

    started = _now()
    smica_map, commander_map = _synthetic_pair(30_700_000, nside=int(context["nside"]))
    input_seconds = _seconds(started)
    smica, smica_timing, _ = _process_map(smica_map, component="SMICA", context=context)
    commander, commander_timing, _ = _process_map(
        commander_map, component="Commander", context=context
    )
    timing = {name: smica_timing[name] + commander_timing[name] for name in STAGES}
    timing["input"] += input_seconds
    return np.concatenate((smica, commander)), timing


def _run_rows(
    count: int,
    *,
    mode: str,
    workers: int,
    context: Mapping[str, object],
) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    if mode not in PROFILE_MODES or type(workers) is not int or workers < 1:
        raise PlanckWorkerError("profile executor selection is invalid")
    ordinals = list(range(count))
    if mode == "serial":
        if workers != 1:
            raise PlanckWorkerError("serial profile requires one worker")
        rows = [_evaluate_synthetic_row(index, context) for index in ordinals]
    else:
        executor_type = ThreadPoolExecutor if mode == "thread" else ProcessPoolExecutor
        executor_options = {"max_workers": workers}
        if mode == "process":
            executor_options["mp_context"] = multiprocessing.get_context("spawn")
        with executor_type(**executor_options) as executor:
            futures = [
                executor.submit(_evaluate_synthetic_row, index, context)
                for index in ordinals
            ]
            rows = [future.result() for future in futures]
    rows.sort(key=lambda row: row[0])
    if [row[0] for row in rows] != ordinals:
        raise PlanckWorkerError("parallel gather changed FFP10 row order")
    smica = np.asarray([row[1] for row in rows], dtype=float)
    commander = np.asarray([row[2] for row in rows], dtype=float)
    timing = {name: sum(row[3][name] for row in rows) for name in STAGES}
    return smica, commander, timing


def _synthetic_local_response(*, context: Mapping[str, object]) -> np.ndarray:
    """Return a fixed symmetric local-modulation response in feature order."""

    smica_map, commander_map = _synthetic_pair(30_699_999, nside=int(context["nside"]))
    beta = 1.0e-3
    plus_operator = ExactBoostOperator(
        nside=int(context["nside"]), lmax=LMAX, beta=beta
    )
    minus_operator = ExactBoostOperator(
        nside=int(context["nside"]), lmax=LMAX, beta=-beta
    )
    columns: list[np.ndarray] = []
    for component, base in (("SMICA", smica_map), ("Commander", commander_map)):
        plus, _, _ = _process_map(
            plus_operator(base), component=component, context=context
        )
        minus, _, _ = _process_map(
            minus_operator(base), component=component, context=context
        )
        columns.append((plus - minus) / (2.0 * beta))
    return np.concatenate(columns)[:, None]


def build_profile(*, rows: str, mode: str, workers: int) -> dict[str, object]:
    if rows not in ROW_LABELS:
        raise PlanckWorkerError("row selection is outside 1/8/32/128/full")
    count = EXPECTED_FFP10_NULL_ROWS if rows == "full" else int(rows)
    if mode == "serial" and workers != 1:
        raise PlanckWorkerError("serial profile requires workers=1")
    if mode != "serial" and workers not in (2, 4, 8):
        raise PlanckWorkerError("parallel profile workers must be 2, 4, or 8")
    if any(os.environ.get(name) != value for name, value in THREAD_CONTROLS.items()):
        raise PlanckWorkerError("one-thread BLAS/OpenMP policy is not active")
    stages = _stage_template()
    wall_started = _now()
    context_started = _now()
    context = _synthetic_context()
    _add_stage(stages, "mask_inverse", _seconds(context_started))
    smica, commander, row_timing = _run_rows(
        count, mode=mode, workers=workers, context=context
    )
    for name in (
        "input",
        "beam_pixel",
        "mask_inverse",
        "map2alm",
        "multipole_vectors",
        "features",
    ):
        _add_stage(stages, name, row_timing[name])

    row_ids = SYNTHETIC_NULL_ROW_IDS[:count]
    covariance = None
    response_rank = None
    synthetic_scan = None
    synthetic_observation_digest = None
    synthetic_observation_disjoint = None
    local_response_rank_seconds = 0.0
    if rows == "full":
        inventory = FFP10Inventory(
            row_ids, expected_identity=SYNTHETIC_NULL_INVENTORY_ID
        )
        started = _now()
        nulls = np.concatenate((smica, commander), axis=1)
        null_row_digests = {_array_digest(row) for row in nulls}
        inventory.require_complete()
        _add_stage(stages, "null_calibration", _seconds(started))

        started = _now()
        covariance = estimate_matched_joint_covariance(
            smica_row_ids=row_ids,
            commander_row_ids=row_ids,
            smica_features=smica,
            commander_features=commander,
        )
        _add_stage(stages, "covariance", _seconds(started))

        started = _now()
        local_response = _synthetic_local_response(context=context)
        response_rank = covariance_whitened_response_rank(
            covariance.matrix, local_response
        )
        local_response_rank_seconds = _seconds(started)

        synthetic_observation, observation_timing = _evaluate_synthetic_observation(
            context
        )
        for name in (
            "input",
            "beam_pixel",
            "mask_inverse",
            "map2alm",
            "multipole_vectors",
            "features",
        ):
            _add_stage(stages, name, observation_timing[name])
        synthetic_observation_digest = _array_digest(synthetic_observation)
        synthetic_observation_disjoint = (
            synthetic_observation_digest not in null_row_digests
        )
        if not synthetic_observation_disjoint:
            raise PlanckWorkerError(
                "synthetic profile observation is duplicated in the null pool"
            )
        started = _now()
        synthetic_scan = calibrate_complete_synthetic_pool(
            observation_features=synthetic_observation,
            null_features=nulls,
            inventory=inventory,
        )
        _add_stage(stages, "global_rank", _seconds(started))
    else:
        for name in ("covariance", "null_calibration", "global_rank"):
            stages[name] = {
                "status": "NOT_RUN_PARTIAL_INVENTORY",
                "seconds": 0.0,
            }

    payload: dict[str, object] = {
        "schema": SCHEMA,
        "capability": "PLANCK_PR3_LOWELL_OPERATOR_CLOSURE_AND_PROFILED_SYNTHETIC_REPLAY",
        "profile_kind": "SYNTHETIC_NULL_ONLY",
        "row_label": rows,
        "row_count": count,
        "complete_inventory": rows == "full",
        "mode": mode,
        "workers": workers,
        "thread_controls": dict(THREAD_CONTROLS),
        "feature_order": list(JOINT_FEATURE_IDS),
        "joint_features_sha256": _array_digest(
            np.concatenate((smica, commander), axis=1)
        ),
        "wall_seconds": 0.0,
        "max_rss_bytes": _max_rss_bytes(),
        "stages": stages,
        "covariance": (
            None
            if covariance is None
            else {
                "rank": covariance.rank,
                "condition_number": covariance.condition_number,
                "cross_block_norm": covariance.cross_block_norm,
            }
        ),
        "synthetic_local_response_rank": (
            None if response_rank is None else response_rank.rank
        ),
        "synthetic_local_response_rank_seconds": local_response_rank_seconds,
        "synthetic_local_response_source": (
            "fixed-seed symmetric local-modulation probe"
            if response_rank is not None
            else None
        ),
        "synthetic_observation_sha256": synthetic_observation_digest,
        "synthetic_observation_disjoint_from_nulls": synthetic_observation_disjoint,
        "global_response_status": "MISSING",
        "global_claim_boundary": GLOBAL_CLAIM_BOUNDARY,
        "synthetic_calibration": (
            None
            if synthetic_scan is None
            else {
                "global_p": str(synthetic_scan.global_p),
                "resolution_floor": str(synthetic_scan.resolution_floor),
                "observation_kind": "SYNTHETIC_PROFILE_ROW",
            }
        ),
        "capability_snapshot": capability_snapshot(response_rank=response_rank),
        "rust_gate": RUST_GATE,
        "observed_statistic_seen": False,
        "observed_science_executed": False,
        "artifact_metadata": _artifact_metadata(observed=False),
    }
    serialization_started = _now()
    json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    _add_stage(stages, "serialization", _seconds(serialization_started))
    payload["wall_seconds"] = _seconds(wall_started)
    payload["max_rss_bytes"] = _max_rss_bytes()
    return payload


def build_profile_matrix() -> dict[str, object]:
    """Run every benchmark cell in a fresh Python process."""

    cells: list[dict[str, object]] = []
    import_roots = sorted(
        {
            str(Path(__import__(name).__file__).resolve().parent.parent)
            for name in ("numpy", "scipy", "healpy")
        }
    )
    environment = {
        "HOME": "/nonexistent",
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "PYTHONPATH": os.pathsep.join(
            [str(ROOT / "htt"), str(ROOT / "htt/src"), *import_roots]
        ),
        **THREAD_CONTROLS,
    }
    with tempfile.TemporaryDirectory(prefix="htt-pr306-profile-") as temporary:
        root = Path(temporary)
        for ordinal, (rows, mode, workers) in enumerate(PROFILE_MATRIX):
            output = root / f"cell-{ordinal:02d}.json"
            completed = subprocess.run(
                [
                    str(Path(sys.executable).absolute()),
                    "-B",
                    str(Path(__file__).resolve()),
                    "--synthetic-profile",
                    "--rows",
                    rows,
                    "--mode",
                    mode,
                    "--workers",
                    str(workers),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=False,
                timeout=120,
            )
            if completed.returncode != 0:
                raise PlanckWorkerError(
                    "profile cell failed: "
                    + completed.stderr.decode("utf-8", "replace")[-1000:]
                )
            cells.append(dict(_strict_json(output, label="profile cell")))
    serial = {
        str(cell["row_label"]): cell for cell in cells if cell["mode"] == "serial"
    }
    for cell in cells:
        baseline = serial[str(cell["row_label"])]
        cell["serial_equivalent"] = (
            cell["joint_features_sha256"] == baseline["joint_features_sha256"]
        )
        if not cell["serial_equivalent"]:
            raise PlanckWorkerError(
                "parallel profile differs from serial feature bytes"
            )
    artifact_metadata = cells[0]["artifact_metadata"]
    if any(cell["artifact_metadata"] != artifact_metadata for cell in cells):
        raise PlanckWorkerError("profile cell artifact metadata drifted")
    for cell in cells:
        cell.pop("artifact_metadata")
    cell_contract = {name: cells[0][name] for name in PROFILE_CONSTANT_FIELDS}
    for cell in cells:
        for name, expected in cell_contract.items():
            if cell[name] != expected and name != "capability_snapshot":
                raise PlanckWorkerError(f"profile cell constant {name} drifted")
        cell.pop("capability_snapshot")
        for name in PROFILE_CONSTANT_FIELDS:
            if name != "capability_snapshot":
                cell.pop(name)
    full_serial = serial["full"]
    full_inventory_capability = capability_snapshot(response_rank=None)
    full_inventory_capability.update(
        {
            "synthetic_local_response_rank": "LOCAL_RESPONSE_RANK_COMPUTED",
            "synthetic_local_response_rank_value": full_serial[
                "synthetic_local_response_rank"
            ],
        }
    )
    cell_contract.pop("capability_snapshot")
    cell_contract["full_inventory_capability_snapshot"] = (
        full_inventory_capability
    )
    stage_totals = {
        name: sum(
            float(cell["stages"][name]["seconds"])
            for cell in cells
            if cell["stages"][name]["status"] == "EXECUTED"
        )
        for name in STAGES
    }
    total = sum(stage_totals.values())
    stage_fractions = {
        name: (seconds / total if total else 0.0)
        for name, seconds in stage_totals.items()
    }
    return {
        "schema": "htt.planck_pr3_profile_matrix.v1",
        "capability": "PLANCK_PR3_LOWELL_OPERATOR_CLOSURE_AND_PROFILED_SYNTHETIC_REPLAY",
        "matrix": [list(value) for value in PROFILE_MATRIX],
        "cell_contract": cell_contract,
        "cells": cells,
        "stage_seconds_total": stage_totals,
        "stage_fraction": stage_fractions,
        "operator_sha256": _sha256_file(ROOT / "htt/obsstat/planck_pr3_operator.py"),
        "worker_sha256": _sha256_file(Path(__file__).resolve()),
        "runtime": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "healpy": __import__("healpy").__version__,
        },
        "rust_gate": RUST_GATE,
        "rust_gate_reason": (
            "the measured transforms and polynomial extraction are already "
            "native-library calls; no project-owned pure numeric leaf remains "
            "eligible for a semantics-preserving Rust port"
        ),
        "observed_statistic_seen": False,
        "observed_science_executed": False,
        "artifact_metadata": artifact_metadata,
    }


def _strict_json(path: Path, *, label: str) -> Mapping[str, object]:
    try:
        raw = path.read_bytes()
        value = json.loads(
            raw,
            object_pairs_hook=lambda pairs: _unique_pairs(pairs, label=label),
            parse_constant=lambda token: (_ for _ in ()).throw(
                PlanckWorkerError(f"{label} contains {token}")
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PlanckWorkerError(f"{label} is not strict JSON") from exc
    if not isinstance(value, Mapping):
        raise PlanckWorkerError(f"{label} must contain an object")
    return value


def _unique_pairs(pairs: list[tuple[str, object]], *, label: str) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PlanckWorkerError(f"{label} contains duplicate key {key!r}")
        result[key] = value
    return result


def _load_admission(path: Path):
    try:
        decision = replay_lane_admission_decision(
            _strict_json(path, label="Planck admission"),
            registry=load_lane_registry(REGISTRY),
        )
    except (DataIdentityError, PlanckWorkerError) as exc:
        raise PlanckWorkerError(f"Planck admission replay failed: {exc}") from exc
    if (
        decision.status is not AdmissionStatus.ADMITTED_IDENTITY_ONLY
        or decision.lane_id != "PLANCK"
        or len(decision.records) != 13
        or decision.lane_admission_bundle_id is None
    ):
        raise PlanckWorkerError("Planck admission is not complete identity admission")
    return decision


def _admitted_paths(decision, *, data_root: Path) -> dict[str, Path]:
    if (
        not data_root.is_absolute()
        or data_root.is_symlink()
        or not data_root.is_dir()
        or data_root.resolve() != data_root
    ):
        raise PlanckWorkerError("data root must be an absolute regular directory")
    profile = decision.records[0].native_identity_profile
    bindings = profile.get("component_bindings")
    if not isinstance(bindings, Sequence) or len(bindings) != len(decision.records):
        raise PlanckWorkerError("Planck native component bindings drifted")
    records = {record.component_id: record for record in decision.records}
    if set(records) != REQUIRED_ADMITTED_COMPONENTS:
        raise PlanckWorkerError("Planck admitted component inventory is incomplete")
    result: dict[str, Path] = {}
    root = data_root
    for row in bindings:
        if not isinstance(row, Mapping):
            raise PlanckWorkerError("Planck component binding is not a mapping")
        component = row.get("component_id")
        relative = row.get("relative_path")
        if (
            not isinstance(component, str)
            or not isinstance(relative, str)
            or component not in records
        ):
            raise PlanckWorkerError("Planck component binding identity drifted")
        try:
            candidate, info = _regular_beneath(
                root,
                Path(relative),
                f"Planck component {component}",
            )
            digest = "sha256:" + _stream_sha256(
                candidate,
                field_name=f"Planck component {component}",
                expected_info=info,
            )
        except DataIdentityError as exc:
            raise PlanckWorkerError(
                f"{component} is not an exact admitted file: {exc}"
            ) from exc
        record = records[component]
        if info.st_size != record.byte_size or digest != record.content_sha256:
            raise PlanckWorkerError(f"{component} no longer matches the admission")
        result[component] = candidate
    if set(result) != set(records):
        raise PlanckWorkerError("Planck admitted component inventory drifted")
    return result


def _load_npy(path: Path, *, label: str, dimension: int | None = None) -> np.ndarray:
    try:
        value = np.asarray(np.load(path, allow_pickle=False), dtype=float)
    except (OSError, ValueError) as exc:
        raise PlanckWorkerError(f"{label} is not a numeric NPY product") from exc
    if not np.all(np.isfinite(value)) or (
        dimension is not None and value.ndim != dimension
    ):
        raise PlanckWorkerError(f"{label} shape or finiteness drifted")
    return value


def _require_declared_nside(
    inverse: MaskCouplingInverse, declared_nside: int
) -> int:
    if inverse.nside != declared_nside:
        raise PlanckWorkerError(
            "admitted map pixelization differs from the declared nside"
        )
    return declared_nside


def build_smica_operator_context(
    *,
    smica_map: np.ndarray,
    mask: np.ndarray,
    beam: np.ndarray,
    window: Mapping[str, np.ndarray],
    declared_nside: int,
) -> dict[str, object]:
    """Build the PR-306 operator for one explicitly SMICA-only diagnostic."""

    values = np.asarray(smica_map, dtype=float)
    selected_mask = np.asarray(mask, dtype=float)
    selected_beam = np.asarray(beam, dtype=float)
    required_window = {
        "source_pixel_window",
        "target_beam",
        "target_pixel_window",
    }
    if (
        values.ndim != 1
        or selected_mask.shape != values.shape
        or set(window) != required_window
        or not np.all(np.isfinite(values))
        or not np.all(np.isfinite(selected_mask))
        or not np.all(np.isfinite(selected_beam))
    ):
        raise PlanckWorkerError("SMICA-only operator inputs are malformed")
    source_pixel = np.asarray(window["source_pixel_window"], dtype=float)
    target_beam = np.asarray(window["target_beam"], dtype=float)
    target_pixel = np.asarray(window["target_pixel_window"], dtype=float)
    if (
        selected_beam.shape != target_beam.shape
        or source_pixel.shape != target_pixel.shape
        or not np.array_equal(selected_beam, target_beam)
        or not np.all(np.isfinite(source_pixel))
        or not np.all(np.isfinite(target_pixel))
    ):
        raise PlanckWorkerError("SMICA-only beam/pixel commonization drifted")
    inverse = build_mask_coupling_inverse(
        selected_mask, lmin=LMIN, lmax=LMAX
    )
    return {
        "pipeline_scope": "SMICA_ONLY",
        "nside": _require_declared_nside(inverse, declared_nside),
        "common_mask": selected_mask,
        "source_beams": {"SMICA": selected_beam},
        "source_pixels": {"SMICA": source_pixel},
        "target_beam": target_beam,
        "target_pixel": target_pixel,
        "mask_inverse": inverse,
    }


def analyze_smica_feature_rows(
    *,
    observed_features: object,
    null_features: object,
    row_ids: Sequence[str],
) -> dict[str, object]:
    """Calibrate the complete 300-row SMICA-only feature family."""

    identifiers = tuple(row_ids)
    if len(identifiers) != SMICA_EXISTING_NULL_ROWS:
        raise PlanckWorkerError("SMICA calibration requires the exact 300 null rows")
    if identifiers != SMICA_EXISTING_ROW_IDS:
        raise PlanckWorkerError("SMICA null row identity or order drifted")
    observed = np.asarray(observed_features, dtype=float)
    nulls = np.asarray(null_features, dtype=float)
    dimension = len(COMPONENT_FEATURE_IDS)
    if (
        observed.shape != (dimension,)
        or nulls.shape != (SMICA_EXISTING_NULL_ROWS, dimension)
        or not np.all(np.isfinite(observed))
        or not np.all(np.isfinite(nulls))
    ):
        raise PlanckWorkerError("SMICA feature matrix is incomplete or malformed")
    covariance = np.cov(nulls, rowvar=False, ddof=1)
    validation = validate_full_joint_covariance(
        covariance, COMPONENT_FEATURE_IDS
    )
    if float(validation["condition_number"]) > 1.0e10:
        raise PlanckWorkerError("SMICA covariance exceeds the condition ceiling")
    inventory = FFP10Inventory(
        identifiers,
        expected_identity=SMICA_EXISTING_INVENTORY_ID,
        expected_null_rows=SMICA_EXISTING_NULL_ROWS,
    )
    scan = calibrate_complete_synthetic_pool(
        observation_features=observed,
        null_features=nulls,
        inventory=inventory,
    )
    return {
        "pipeline_scope": "SMICA_ONLY",
        "feature_order": list(COMPONENT_FEATURE_IDS),
        "observed_feature_vector": observed.tolist(),
        "covariance_rank": int(validation["rank"]),
        "covariance_condition": float(validation["condition_number"]),
        "covariance_whitening": "CHOLESKY_LEFT",
        "null_rows": SMICA_EXISTING_NULL_ROWS,
        "null_semantics": "FFP10_CMB_PLUS_NOISE_PAIRED_BY_ID",
        "null_ordered_row_ids_sha256": SMICA_EXISTING_INVENTORY_ID,
        "finite_feature_family_p": str(scan.global_p),
        "resolution_floor": str(scan.resolution_floor),
        "local_feature_p": [str(value) for value in scan.local_p],
        "commander_robustness": "NOT_EVALUATED",
        "joint_covariance": "NOT_APPLICABLE_SMICA_ONLY",
        "local_response_rank": "NOT_COMPUTED_SMICA_ONLY",
        "global_response_status": "MISSING",
        "global_claim_boundary": GLOBAL_CLAIM_BOUNDARY,
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
    }


def _canonical_hash(payload: Mapping[str, object]) -> str:
    raw = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _require_git_identity(value: str, *, label: str) -> str:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise PlanckWorkerError(f"{label} must be one lowercase git object ID")
    return value


def _smica_plan_components(plan: Mapping[str, object]) -> dict[str, Path]:
    if (
        plan.get("format") != "PLANCK_PR3_SMICA_EXISTING_PLAN_V1"
        or plan.get("pipeline_scope") != "SMICA_ONLY"
        or plan.get("ordered_row_ids_sha256") != SMICA_EXISTING_INVENTORY_ID
        or plan.get("observed_temperature_payload_opened") is not False
    ):
        raise PlanckWorkerError("SMICA existing-data plan identity drifted")
    raw_components = plan.get("components")
    if not isinstance(raw_components, Mapping):
        raise PlanckWorkerError("SMICA plan components are missing")
    required = {"mask", "beam", "window", "null", "covariance", "selection"}
    if set(raw_components) != required:
        raise PlanckWorkerError("SMICA plan component inventory drifted")
    result: dict[str, Path] = {}
    for name in sorted(required):
        row = raw_components[name]
        if not isinstance(row, Mapping):
            raise PlanckWorkerError(f"SMICA plan component {name} is malformed")
        path_text = row.get("path")
        expected_size = row.get("byte_size")
        expected_hash = row.get("sha256")
        if not isinstance(path_text, str) or not isinstance(expected_size, int):
            raise PlanckWorkerError(f"SMICA plan component {name} identity is malformed")
        path = Path(path_text)
        if (
            not path.is_absolute()
            or path.is_symlink()
            or not path.is_file()
            or path.resolve() != path
            or path.stat().st_size != expected_size
            or _sha256_file(path) != expected_hash
        ):
            raise PlanckWorkerError(f"SMICA plan component {name} no longer matches")
        result[name] = path
    return result


def smica_existing_acceptance(
    *,
    plan_path: Path,
    output_dir: Path,
    candidate_commit: str,
    candidate_tree: str,
) -> dict[str, object]:
    """Compute the exact attended confirmation surface without observed open."""

    plan = _strict_json(plan_path, label="SMICA existing-data plan")
    _smica_plan_components(plan)
    observed = plan.get("observed_smica")
    if not isinstance(observed, Mapping):
        raise PlanckWorkerError("SMICA observed source identity is missing")
    path_text = observed.get("path")
    expected_size = observed.get("byte_size")
    if not isinstance(path_text, str) or not isinstance(expected_size, int):
        raise PlanckWorkerError("SMICA observed source identity is malformed")
    observed_path = Path(path_text)
    if (
        not observed_path.is_absolute()
        or observed_path.is_symlink()
        or not observed_path.is_file()
        or observed_path.resolve() != observed_path
        or observed_path.stat().st_size != expected_size
        or observed_path.name != observed.get("filename")
    ):
        raise PlanckWorkerError("SMICA observed source is not the identified product")
    if not output_dir.is_absolute() or output_dir.is_symlink():
        raise PlanckWorkerError("SMICA output directory must be absolute and regular")
    payload = {
        "capability": "PLANCK_PR3_SMICA_EXISTING_DATA_DIAGNOSTIC",
        "candidate_commit": _require_git_identity(
            candidate_commit, label="candidate commit"
        ),
        "candidate_tree": _require_git_identity(candidate_tree, label="candidate tree"),
        "plan_sha256": _sha256_file(plan_path),
        "observed_source": {
            "filename": observed_path.name,
            "byte_size": expected_size,
            "release_identity": plan.get("release_identity"),
        },
        "null_ordered_row_ids_sha256": SMICA_EXISTING_INVENTORY_ID,
        "worker_sha256": _sha256_file(Path(__file__).resolve()),
        "output_dir": str(output_dir),
    }
    return {**payload, "acceptance_hash": _canonical_hash(payload)}


def _load_smica_existing_rows(
    *, plan: Mapping[str, object], components: Mapping[str, Path]
) -> tuple[dict[str, object], tuple[str, ...], np.ndarray, Mapping[str, object]]:
    selection = _strict_json(components["selection"], label="SMICA selection")
    if (
        selection.get("pipeline_scope") != "SMICA_ONLY"
        or selection.get("expected_null_rows") != SMICA_EXISTING_NULL_ROWS
        or selection.get("null_semantics")
        != "FFP10_CMB_PLUS_NOISE_PAIRED_BY_ID"
        or selection.get("ordered_row_ids_sha256") != SMICA_EXISTING_INVENTORY_ID
        or selection.get("feature_ids") != list(COMPONENT_FEATURE_IDS)
    ):
        raise PlanckWorkerError("SMICA selection contract drifted")
    try:
        with np.load(components["null"], allow_pickle=False, mmap_mode="r") as bundle:
            if set(bundle.files) != {"row_ids", "smica_maps"}:
                raise PlanckWorkerError("SMICA null bundle keys drifted")
            raw_ids = np.asarray(bundle["row_ids"])
            maps = np.asarray(bundle["smica_maps"])
    except (OSError, ValueError) as exc:
        raise PlanckWorkerError("SMICA null bundle is not safe numeric NPZ") from exc
    row_ids = tuple(str(value) for value in raw_ids.tolist())
    if row_ids != SMICA_EXISTING_ROW_IDS:
        raise PlanckWorkerError("SMICA null row identity or order drifted")
    nside = selection.get("nside")
    if type(nside) is not int:
        raise PlanckWorkerError("SMICA output nside is malformed")
    return dict(selection), row_ids, maps, plan


def _smica_result_projection(payload: Mapping[str, object]) -> dict[str, object]:
    if payload.get("format") != "PLANCK_PR3_SMICA_EXISTING_RESULT_V1":
        raise PlanckWorkerError("SMICA result format drifted")
    projection = json.loads(
        json.dumps(payload, sort_keys=True, ensure_ascii=True, allow_nan=False)
    )
    projection.pop("wall_seconds", None)
    return projection


def _append_fsynced(path: Path, text_value: str) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(text_value)
        handle.flush()
        os.fsync(handle.fileno())


def run_smica_existing_attended(
    *,
    plan_path: Path,
    output_dir: Path,
    candidate_commit: str,
    candidate_tree: str,
    confirmation: str,
) -> dict[str, object]:
    """Run the complete local SMICA diagnostic after exact attended confirm."""

    acceptance = smica_existing_acceptance(
        plan_path=plan_path,
        output_dir=output_dir,
        candidate_commit=candidate_commit,
        candidate_tree=candidate_tree,
    )
    if confirmation != acceptance["acceptance_hash"]:
        raise PlanckWorkerError("SMICA attended confirmation does not match")
    if output_dir.exists():
        if not output_dir.is_dir() or any(output_dir.iterdir()):
            raise PlanckWorkerError("SMICA output directory must be new or empty")
    else:
        output_dir.mkdir(parents=True)
    _write_json(output_dir / "acceptance.json", acceptance)
    _write_json(
        output_dir / "start.json",
        {
            "state": "STARTED_BEFORE_OBSERVED_OPEN",
            "acceptance_hash": acceptance["acceptance_hash"],
            "candidate_commit": candidate_commit,
            "candidate_tree": candidate_tree,
        },
    )
    started = _now()
    try:
        plan = _strict_json(plan_path, label="SMICA existing-data plan")
        components = _smica_plan_components(plan)
        selection, row_ids, _, _ = _load_smica_existing_rows(
            plan=plan, components=components
        )
        nside = int(selection["nside"])
        observed_row = plan["observed_smica"]
        observed_path = Path(str(observed_row["path"]))
        from scripts.observed_runs.prepare_planck_pr3_admission import (
            read_temperature_fits,
            reduce_temperature_map,
        )

        loaded = read_temperature_fits(
            observed_path,
            allowed_column_names=("I_STOKES",),
            declared_coordinate_frame="GALACTIC",
        )
        observed_map = reduce_temperature_map(
            loaded.values,
            source_unit=loaded.unit,
            source_ordering=loaded.ordering,
            output_nside=nside,
        )
        mask = _load_npy(components["mask"], label="SMICA mask", dimension=1)
        beam = _load_npy(components["beam"], label="SMICA beam", dimension=1)
        window = _load_window(components["window"], label="SMICA window")
        context = build_smica_operator_context(
            smica_map=observed_map,
            mask=mask,
            beam=beam,
            window=window,
            declared_nside=nside,
        )
        null_features = _process_ffp10_component(
            components["null"],
            array_name="smica_maps",
            row_ids=row_ids,
            component="SMICA",
            context=context,
        )
        observed_features, _, _ = _process_map(
            observed_map, component="SMICA", context=context
        )
        diagnostic = analyze_smica_feature_rows(
            observed_features=observed_features,
            null_features=null_features,
            row_ids=row_ids,
        )
        replay = write_compact_smica_observed_replay_input(
            output_dir=output_dir, smica_map=observed_map, nside=nside
        )
        stored_covariance = _load_npy(
            components["covariance"], label="SMICA covariance", dimension=2
        )
        replay_covariance = np.cov(null_features, rowvar=False, ddof=1)
        if not np.array_equal(stored_covariance, replay_covariance):
            raise PlanckWorkerError("SMICA stored covariance differs from replay")
        result = {
            "format": "PLANCK_PR3_SMICA_EXISTING_RESULT_V1",
            **diagnostic,
            "acceptance_hash": acceptance["acceptance_hash"],
            "candidate_commit": candidate_commit,
            "candidate_tree": candidate_tree,
            "source_release": plan["release_identity"],
            "observed_smica_filename": observed_path.name,
            "observed_smica_sha256": _sha256_file(observed_path),
            "compact_observed_replay_input": replay,
            "wall_seconds": _seconds(started),
            "observed_statistic_seen": True,
            "observed_science_executed": True,
            "claim_tier": "diagnostic_only",
            "forbidden_claims": [
                "Commander robustness",
                "joint Planck component-separation closure",
                "global response",
                "source attribution",
                "native solver result",
                "Bianchi family identification",
            ],
        }
        _write_json(output_dir / "result.json", result)
        result_hash = _sha256_file(output_dir / "result.json")
        _write_json(
            output_dir / "terminal.json",
            {
                "state": "SUCCEEDED",
                "result_sha256": result_hash,
                "observed_science_executed": True,
            },
        )
        _append_fsynced(output_dir / "stdout.log", "SMICA diagnostic completed\n")
        (output_dir / "stderr.log").touch()
        return result
    except BaseException as exc:
        _write_json(
            output_dir / "terminal.json",
            {
                "state": "FAILED",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "scientific_result_emitted": False,
            },
        )
        _append_fsynced(output_dir / "stderr.log", f"{type(exc).__name__}: {exc}\n")
        raise


def replay_smica_existing_result(
    *, plan_path: Path, source_output_dir: Path, replay_output: Path
) -> dict[str, object]:
    """Replay the diagnostic from retained compact inputs without raw FITS."""

    plan = _strict_json(plan_path, label="SMICA existing-data plan")
    components = _smica_plan_components(plan)
    selection, row_ids, _, _ = _load_smica_existing_rows(
        plan=plan, components=components
    )
    expected = _strict_json(
        source_output_dir / "result.json", label="SMICA source result"
    )
    compact = expected.get("compact_observed_replay_input")
    if not isinstance(compact, Mapping):
        raise PlanckWorkerError("SMICA compact replay identity is missing")
    observed_path = source_output_dir / str(compact.get("filename"))
    if _sha256_file(observed_path) != compact.get("sha256"):
        raise PlanckWorkerError("SMICA compact observed replay hash drifted")
    observed_map = _load_npy(
        observed_path, label="compact observed SMICA", dimension=1
    )
    mask = _load_npy(components["mask"], label="SMICA mask", dimension=1)
    beam = _load_npy(components["beam"], label="SMICA beam", dimension=1)
    window = _load_window(components["window"], label="SMICA window")
    context = build_smica_operator_context(
        smica_map=observed_map,
        mask=mask,
        beam=beam,
        window=window,
        declared_nside=int(selection["nside"]),
    )
    null_features = _process_ffp10_component(
        components["null"],
        array_name="smica_maps",
        row_ids=row_ids,
        component="SMICA",
        context=context,
    )
    observed_features, _, _ = _process_map(
        observed_map, component="SMICA", context=context
    )
    diagnostic = analyze_smica_feature_rows(
        observed_features=observed_features,
        null_features=null_features,
        row_ids=row_ids,
    )
    replayed = dict(expected)
    for key, value in diagnostic.items():
        replayed[key] = value
    if _smica_result_projection(replayed) != _smica_result_projection(expected):
        raise PlanckWorkerError("SMICA compact replay differs from source result")
    _write_json(
        replay_output,
        {
            "state": "REPLAY_MATCH",
            "source_result_sha256": _sha256_file(source_output_dir / "result.json"),
            "scientific_projection_sha256": _canonical_hash(
                _smica_result_projection(expected)
            ),
            "observed_raw_reopened": False,
        },
    )
    return dict(_strict_json(replay_output, label="SMICA replay result"))


def _load_window(path: Path, *, label: str) -> dict[str, np.ndarray]:
    try:
        with np.load(path, allow_pickle=False) as bundle:
            if set(bundle.files) != {
                "source_pixel_window",
                "target_beam",
                "target_pixel_window",
            }:
                raise PlanckWorkerError(f"{label} keys drifted")
            result = {
                key: np.asarray(bundle[key], dtype=float).copy() for key in bundle.files
            }
    except (OSError, ValueError) as exc:
        raise PlanckWorkerError(f"{label} is not the registered NPZ window") from exc
    if any(
        value.ndim != 1 or not np.all(np.isfinite(value)) for value in result.values()
    ):
        raise PlanckWorkerError(f"{label} contains malformed transfer vectors")
    return result


def _load_ffp10_row_ids(
    path: Path, *, expected_inventory_identity: str
) -> tuple[str, ...]:
    try:
        with np.load(path, allow_pickle=False, mmap_mode="r") as bundle:
            if set(bundle.files) != {"row_ids", "smica_maps", "commander_maps"}:
                raise PlanckWorkerError("FFP10 bundle keys drifted")
            raw_ids = np.asarray(bundle["row_ids"])
    except (OSError, ValueError) as exc:
        raise PlanckWorkerError("FFP10 bundle is not a safe numeric NPZ") from exc
    if raw_ids.ndim != 1 or raw_ids.dtype.kind not in "US":
        raise PlanckWorkerError("FFP10 row IDs must be a string vector")
    row_ids = tuple(str(value) for value in raw_ids.tolist())
    FFP10Inventory(
        row_ids, expected_identity=expected_inventory_identity
    ).require_complete()
    return row_ids


def _process_ffp10_component(
    path: Path,
    *,
    array_name: str,
    row_ids: tuple[str, ...],
    component: str,
    context: Mapping[str, object],
    chunk_rows: int = 32,
) -> np.ndarray:
    """Process one component stack at a time with bounded validation chunks."""

    try:
        with np.load(path, allow_pickle=False, mmap_mode="r") as bundle:
            maps = np.asarray(bundle[array_name])
            if maps.ndim != 2 or maps.shape[0] != len(row_ids):
                raise PlanckWorkerError("FFP10 same-sky map pairing is incomplete")
            features: list[np.ndarray] = []
            for start in range(0, len(row_ids), chunk_rows):
                chunk = maps[start : start + chunk_rows]
                if not np.all(np.isfinite(chunk)):
                    raise PlanckWorkerError("FFP10 map stack contains nonfinite values")
                for pixel_map in chunk:
                    value, _, _ = _process_map(
                        np.asarray(pixel_map, dtype=float),
                        component=component,
                        context=context,
                    )
                    features.append(value)
    except (KeyError, OSError, ValueError) as exc:
        raise PlanckWorkerError("FFP10 bundle is not a safe numeric NPZ") from exc
    return np.asarray(features, dtype=float)


def _mark_observed_data_open_attempt() -> None:
    output_text = os.environ.get("HTT_ATTENDED_OUTPUT_DIR", "")
    output = Path(output_text)
    if (
        not output_text
        or not output.is_absolute()
        or output.is_symlink()
        or not output.is_dir()
        or not (output / "start.json").is_file()
    ):
        raise PlanckWorkerError("attended output/start binding is missing")
    marker = output / "observed_data_opened.json"
    if os.environ.get("HTT_ATTENDED_DATA_OPEN_MARKER") != str(marker):
        raise PlanckWorkerError("observed-data-open marker binding drifted")
    if marker.exists() or marker.is_symlink():
        raise PlanckWorkerError("observed-data-open marker already exists")
    _write_json(marker, {"state": "OBSERVED_DATA_OPEN_ATTEMPTED"})


def _observed_result_payload(
    *,
    admission_bundle_id: str,
    observed: np.ndarray,
    covariance,
    synthetic_response_rank,
    scan,
    null_rows: int,
    wall_seconds: float,
) -> dict[str, object]:
    """Serialize one claim-bounded result without response-provenance leakage."""

    return {
        "schema": "htt.planck_pr3_lowell_result.v1",
        "lane_admission_bundle_id": admission_bundle_id,
        "feature_order": list(JOINT_FEATURE_IDS),
        "observed_feature_vector": observed.tolist(),
        "joint_covariance_rank": covariance.rank,
        "joint_covariance_condition": covariance.condition_number,
        "synthetic_local_response_rank": synthetic_response_rank.rank,
        "synthetic_local_response_source": (
            "fixed-seed symmetric local-modulation probe; operator validation only"
        ),
        "global_response_status": "MISSING",
        "global_claim_boundary": GLOBAL_CLAIM_BOUNDARY,
        "finite_global_p": str(scan.global_p),
        "resolution_floor": str(scan.resolution_floor),
        "ffp10_null_rows": null_rows,
        "wall_seconds": wall_seconds,
        "artifact_metadata": _artifact_metadata(observed=True),
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "observed_data_opened": True,
        "observed_science_executed": True,
    }


def run_admitted(*, admission_path: Path, data_root: Path) -> dict[str, object]:
    """Execute the reviewed operator after the attended start receipt exists."""

    if os.environ.get("HTT_ATTENDED_START_WRITTEN") != "1":
        raise PlanckWorkerError("attended start receipt must precede data open")
    started = _now()
    decision = _load_admission(admission_path)
    _mark_observed_data_open_attempt()
    paths = _admitted_paths(decision, data_root=data_root)
    pixelization = _strict_json(paths["pixelization"], label="pixelization")
    selection = _strict_json(paths["native_selection"], label="native selection")
    expected_pixelization = {
        "schema": "htt.planck.pixelization.v1",
        "nside": pixelization.get("nside"),
        "ordering": "RING",
        "map_unit": "microK_CMB",
        "coordinate_frame": "GALACTIC",
        "harmonic_convention": "ORTHONORMAL_CONDON_SHORTLEY_REAL_MAP",
    }
    if (
        dict(pixelization) != expected_pixelization
        or type(pixelization["nside"]) is not int
    ):
        raise PlanckWorkerError("pixelization contract drifted")
    expected_selection = {
        "schema": "htt.planck.pr3.lowell_selection.v1",
        "lmin": LMIN,
        "lmax": LMAX,
        "expected_ffp10_null_rows": EXPECTED_FFP10_NULL_ROWS,
        "feature_ids": list(JOINT_FEATURE_IDS),
        "ffp10_release_id": FFP10_RELEASE_ID,
        "ffp10_ordered_row_ids_sha256": selection.get("ffp10_ordered_row_ids_sha256"),
    }
    inventory_identity = selection.get("ffp10_ordered_row_ids_sha256")
    if (
        dict(selection) != expected_selection
        or not isinstance(inventory_identity, str)
        or not inventory_identity.startswith("sha256:")
        or len(inventory_identity) != 71
    ):
        raise PlanckWorkerError("native low-ell selection drifted")
    try:
        int(inventory_identity.removeprefix("sha256:"), 16)
    except ValueError as exc:
        raise PlanckWorkerError("native FFP10 inventory identity is malformed") from exc
    maps = {
        component: _load_npy(
            paths[f"{component.lower()}_map"], label=f"{component} map", dimension=1
        )
        for component in ("SMICA", "COMMANDER")
    }
    masks = {
        component: _load_npy(
            paths[f"{component.lower()}_mask"], label=f"{component} mask", dimension=1
        )
        for component in ("SMICA", "COMMANDER")
    }
    beams = {
        component: _load_npy(
            paths[f"{component.lower()}_beam"], label=f"{component} beam", dimension=1
        )
        for component in ("SMICA", "COMMANDER")
    }
    windows = {
        component: _load_window(
            paths[f"{component.lower()}_window_operator"], label=f"{component} window"
        )
        for component in ("SMICA", "COMMANDER")
    }
    if maps["SMICA"].shape != maps["COMMANDER"].shape or any(
        mask.shape != maps["SMICA"].shape for mask in masks.values()
    ):
        raise PlanckWorkerError("Planck map/mask pixelization pairing drifted")
    common_mask = np.minimum(masks["SMICA"], masks["COMMANDER"])
    if not np.array_equal(
        windows["SMICA"]["target_beam"], windows["COMMANDER"]["target_beam"]
    ) or not np.array_equal(
        windows["SMICA"]["target_pixel_window"],
        windows["COMMANDER"]["target_pixel_window"],
    ):
        raise PlanckWorkerError("SMICA/Commander common target transfer differs")
    inverse = build_mask_coupling_inverse(common_mask, lmin=LMIN, lmax=LMAX)
    context = {
        "nside": _require_declared_nside(inverse, pixelization["nside"]),
        "common_mask": common_mask,
        "source_beams": {"SMICA": beams["SMICA"], "Commander": beams["COMMANDER"]},
        "source_pixels": {
            "SMICA": windows["SMICA"]["source_pixel_window"],
            "Commander": windows["COMMANDER"]["source_pixel_window"],
        },
        "target_beam": windows["SMICA"]["target_beam"],
        "target_pixel": windows["SMICA"]["target_pixel_window"],
        "mask_inverse": inverse,
    }
    row_ids = _load_ffp10_row_ids(
        paths["ffp10_null_inventory"],
        expected_inventory_identity=inventory_identity,
    )
    smica_matrix = _process_ffp10_component(
        paths["ffp10_null_inventory"],
        array_name="smica_maps",
        row_ids=row_ids,
        component="SMICA",
        context=context,
    )
    commander_matrix = _process_ffp10_component(
        paths["ffp10_null_inventory"],
        array_name="commander_maps",
        row_ids=row_ids,
        component="Commander",
        context=context,
    )
    covariance = estimate_matched_joint_covariance(
        smica_row_ids=row_ids,
        commander_row_ids=row_ids,
        smica_features=smica_matrix,
        commander_features=commander_matrix,
    )
    for component, offset in (("SMICA", 0), ("Commander", len(COMPONENT_FEATURE_IDS))):
        reference = _load_npy(
            paths[f"{component.lower()}_covariance"],
            label=f"{component} covariance",
            dimension=2,
        )
        block = covariance.matrix[
            offset : offset + len(COMPONENT_FEATURE_IDS),
            offset : offset + len(COMPONENT_FEATURE_IDS),
        ]
        if reference.shape != block.shape or not np.allclose(
            reference, block, rtol=1e-8, atol=1e-12
        ):
            raise PlanckWorkerError(
                f"{component} covariance reference differs from replay"
            )
    observed_features = []
    for component in ("SMICA", "Commander"):
        key = component.upper() if component == "SMICA" else "COMMANDER"
        value, _, _ = _process_map(maps[key], component=component, context=context)
        observed_features.append(value)
    observed = np.concatenate(observed_features)
    inventory = FFP10Inventory(row_ids, expected_identity=inventory_identity)
    nulls = np.concatenate((smica_matrix, commander_matrix), axis=1)
    scan = calibrate_complete_synthetic_pool(
        observation_features=observed,
        null_features=nulls,
        inventory=inventory,
    )
    local_response = _synthetic_local_response(context=context)
    response_rank = covariance_whitened_response_rank(covariance.matrix, local_response)
    return _observed_result_payload(
        admission_bundle_id=decision.lane_admission_bundle_id,
        observed=observed,
        covariance=covariance,
        synthetic_response_rank=response_rank,
        scan=scan,
        null_rows=len(row_ids),
        wall_seconds=_seconds(started),
    )


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n",
        encoding="ascii",
    )
    os.replace(temporary, path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--synthetic-profile", action="store_true")
    mode.add_argument("--synthetic-profile-matrix", action="store_true")
    mode.add_argument("--run-admitted", action="store_true")
    mode.add_argument("--print-smica-existing-acceptance", action="store_true")
    mode.add_argument("--run-smica-existing", action="store_true")
    mode.add_argument("--replay-smica-existing", action="store_true")
    parser.add_argument("--rows", choices=ROW_LABELS)
    parser.add_argument("--mode", choices=PROFILE_MODES, default="serial")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--admission", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--candidate-commit")
    parser.add_argument("--candidate-tree")
    parser.add_argument("--confirm")
    parser.add_argument("--source-output-dir", type=Path)
    parser.add_argument("--replay-output", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.synthetic_profile:
            if (
                args.rows is None
                or args.admission is not None
                or args.data_root is not None
            ):
                raise PlanckWorkerError(
                    "synthetic profile requires rows and forbids admitted inputs"
                )
            payload = build_profile(
                rows=args.rows, mode=args.mode, workers=args.workers
            )
        elif args.synthetic_profile_matrix:
            if (
                args.rows is not None
                or args.admission is not None
                or args.data_root is not None
            ):
                raise PlanckWorkerError(
                    "profile matrix forbids row and admitted inputs"
                )
            payload = build_profile_matrix()
        elif args.run_admitted:
            if (
                args.rows is not None
                or args.admission is None
                or args.data_root is None
            ):
                raise PlanckWorkerError(
                    "admitted run requires exact admission and data root"
                )
            payload = run_admitted(
                admission_path=args.admission, data_root=args.data_root
            )
        elif args.print_smica_existing_acceptance:
            if any(
                value is None
                for value in (
                    args.plan,
                    args.output_dir,
                    args.candidate_commit,
                    args.candidate_tree,
                )
            ):
                raise PlanckWorkerError(
                    "SMICA acceptance requires plan, output-dir, commit, and tree"
                )
            payload = smica_existing_acceptance(
                plan_path=args.plan,
                output_dir=args.output_dir,
                candidate_commit=args.candidate_commit,
                candidate_tree=args.candidate_tree,
            )
        elif args.run_smica_existing:
            if any(
                value is None
                for value in (
                    args.plan,
                    args.output_dir,
                    args.candidate_commit,
                    args.candidate_tree,
                    args.confirm,
                )
            ):
                raise PlanckWorkerError(
                    "SMICA run requires plan, output-dir, commit, tree, and confirm"
                )
            payload = run_smica_existing_attended(
                plan_path=args.plan,
                output_dir=args.output_dir,
                candidate_commit=args.candidate_commit,
                candidate_tree=args.candidate_tree,
                confirmation=args.confirm,
            )
        else:
            if any(
                value is None
                for value in (args.plan, args.source_output_dir, args.replay_output)
            ):
                raise PlanckWorkerError(
                    "SMICA replay requires plan, source-output-dir, and replay-output"
                )
            payload = replay_smica_existing_result(
                plan_path=args.plan,
                source_output_dir=args.source_output_dir,
                replay_output=args.replay_output,
            )
        if args.output is None:
            print(json.dumps(payload, sort_keys=True, allow_nan=False))
        else:
            _write_json(args.output, payload)
        return 0
    except (PlanckWorkerError, PlanckLaneContractError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
