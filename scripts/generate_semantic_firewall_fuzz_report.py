#!/usr/bin/env python3
"""Generate deterministic semantic-firewall fuzz coverage for HTT/MIO formalism.

The hostile inputs are intentionally not printed into the generated report.
The report records only sanitized case ids, production surfaces, and whether
the corresponding production guard refused the input.
"""
from __future__ import annotations

import argparse
from collections.abc import Callable, Mapping, Sequence
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
HTT_ROOT = REPO_ROOT / "htt"
SCRIPTS_ROOT = REPO_ROOT / "scripts"
for root in (COMMON_ROOT, HTT_ROOT, SCRIPTS_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from common.semantic_guards.no_overclaim import scan_text  # noqa: E402
from common.transfer_registry import (  # noqa: E402
    TransferFunctionSpec,
    TransferValidRange,
)
from htt.departure.response_overlap import (  # noqa: E402
    build_response_overlap_audit,
    require_rank_audit_for_model_run,
)
from htt.departure.posterior_pushforward import (  # noqa: E402
    reject_mio_pushforward_inputs,
)
from mio.formalism.budget_spec import (  # noqa: E402
    BudgetPolicy,
    BudgetSpec,
    BudgetUse,
)
from mio.formalism.departure_bundle import build_departure_bundle  # noqa: E402
from mio.formalism.exceedance import (  # noqa: E402
    MeasureKind,
    ThresholdPolicy,
    build_exceedance_curve,
)
from mio.formalism.filling_fraction import (  # noqa: E402
    build_certified_filling_fraction,
)
from mio.formalism.isotropy_gap import (  # noqa: E402
    DepthBinMetadata,
    build_depth_bin_f_record,
    build_isotropy_gap,
)
from mio.formalism.normalized_score import build_normalized_score  # noqa: E402
from verify_formalism_figure_labels import validate_rows  # noqa: E402
from workspace.contracts.htt_posterior import reject_mio_likelihood_inputs  # noqa: E402


DEFAULT_JSON_OUTPUT = Path("docs/generated/semantic_firewall_fuzz_report.json")
DEFAULT_MD_OUTPUT = Path("docs/generated/semantic_firewall_fuzz_report.md")
SCHEMA_VERSION = "common.semantic_firewall_fuzz_report.v1"
ARTIFACT_ID = "semantic_firewall_fuzz_report"
_COMMAND = "python scripts/generate_semantic_firewall_fuzz_report.py"
_WORKTREE = "semantic-firewall-fuzz"
_INPUT_HASH = "sha256:" + "1" * 64
_FLOOR = 1.0e-3

INPUT_FILES: tuple[str, ...] = (
    "scripts/generate_semantic_firewall_fuzz_report.py",
    "tests/contracts/test_semantic_firewall_fuzz.py",
    "scripts/verify_formalism_figure_labels.py",
    "htt/src/common/semantic_guards/no_overclaim.py",
    "htt/src/common/transfer_registry.py",
    "htt/workspace/contracts/htt_posterior.py",
    "htt/htt/htt/departure/posterior_pushforward.py",
    "htt/htt/htt/departure/response_overlap.py",
    "htt/mio/formalism/budget_spec.py",
    "htt/mio/formalism/departure_bundle.py",
    "htt/mio/formalism/exceedance.py",
    "htt/mio/formalism/filling_fraction.py",
    "htt/mio/formalism/isotropy_gap.py",
    "htt/mio/formalism/normalized_score.py",
    "htt/bass/atlas/atlas_entry.py",
    "htt/bass/transfer/registry.py",
)


@dataclass(frozen=True)
class FirewallCaseResult:
    case_id: str
    attack_family: str
    surface: str
    modules_exercised: tuple[str, ...]
    blocked: bool
    blocker: str

    def as_payload(self) -> dict[str, object]:
        return asdict(self)


def _sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return _sha256_bytes(encoded)


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _current_git_state(repo_root: Path) -> str:
    commit = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    status = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if commit.returncode != 0 or status.returncode != 0:
        return "unknown"
    head = commit.stdout.strip()
    return f"{head}+dirty" if status.stdout.strip() else head


def _existing_git_state(json_output: Path, repo_root: Path) -> str | None:
    path = json_output if json_output.is_absolute() else repo_root / json_output
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    state = payload.get("git_commit_or_worktree_state")
    return str(state) if state else None


def _required_input_hashes(repo_root: Path) -> list[str]:
    missing = [rel for rel in INPUT_FILES if not (repo_root / rel).is_file()]
    if missing:
        raise FileNotFoundError(
            "required semantic-firewall fuzz input missing: " + ", ".join(missing)
        )
    return [f"{rel}:{_sha256_file(repo_root / rel)}" for rel in INPUT_FILES]


def _case(
    *,
    case_id: str,
    attack_family: str,
    surface: str,
    modules_exercised: Sequence[str],
    blocked: bool,
    blocker: str,
) -> FirewallCaseResult:
    return FirewallCaseResult(
        case_id=case_id,
        attack_family=attack_family,
        surface=surface,
        modules_exercised=tuple(modules_exercised),
        blocked=blocked,
        blocker=blocker if blocked else "",
    )


def _blocked_by_exception(
    *,
    case_id: str,
    attack_family: str,
    surface: str,
    modules_exercised: Sequence[str],
    action: Callable[[], object],
    expected: tuple[type[BaseException], ...] = (ValueError, TypeError, RuntimeError),
) -> FirewallCaseResult:
    try:
        action()
    except expected as exc:
        return _case(
            case_id=case_id,
            attack_family=attack_family,
            surface=surface,
            modules_exercised=modules_exercised,
            blocked=True,
            blocker=type(exc).__name__,
        )
    return _case(
        case_id=case_id,
        attack_family=attack_family,
        surface=surface,
        modules_exercised=modules_exercised,
        blocked=False,
        blocker="",
    )


def _transfer_metadata(transfer_id: str, **overrides: object) -> dict[str, object]:
    spec = TransferFunctionSpec(
        transfer_id=transfer_id,
        source="AniCLASS_external",
        family="BianchiI",
        valid_range=TransferValidRange(
            k_min=1.0e-5,
            k_max=0.2,
            ell_min=2,
            ell_max=30,
        ),
        observable_kind="scalar_summary",
        normalization="unit_primordial_curvature",
        calibration_status="external_calibrated",
        caveats=("external-transfer path", "transfer-conditional result"),
        source_ref=f"aniclass:{transfer_id}",
    )
    metadata = spec.to_metadata()
    metadata.update(overrides)
    return metadata


def _bundle(x_c: float, **overrides: object):
    values: dict[str, object] = {
        "components": {
            "Sigma2_std": x_c,
            "W2_std": 0.0,
            "Omega_tilt": 0.0,
            "Omega_k_aniso": 0.0,
        },
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "config_hash": f"cfg-x-{x_c}",
        "input_hashes": (f"x-input-{x_c}",),
    }
    values.update(overrides)
    return build_departure_bundle(**values)


def _budget(
    denominator_value: float,
    *,
    certified: bool = False,
    depth_reference: bool = False,
    **overrides: object,
) -> BudgetSpec:
    uses: list[BudgetUse] = [
        BudgetUse.DENOMINATOR_SENSITIVITY,
        BudgetUse.SIGNED_PROJECTION_NORMALIZATION,
    ]
    if certified:
        uses.append(BudgetUse.CERTIFIED_FILLING_CEILING)
    if depth_reference:
        uses.append(BudgetUse.DEPTH_GAP_REFERENCE)
    values: dict[str, object] = {
        "policy": BudgetPolicy.MES_LINEAR,
        "denominator_value": denominator_value,
        "denominator_label": "linear MES positive diagnostic ceiling",
        "comparator": "CMB_FLRW_reference",
        "frame": "normal_frame",
        "units": "dimensionless_hubble_normalized",
        "config_hash": f"cfg-budget-{denominator_value}",
        "input_hashes": (f"budget-input-{denominator_value}",),
        "assumptions": ("linear MES denominator for diagnostic firewall tests",),
        "admissible_uses": tuple(uses),
        "is_admissible_ceiling": certified,
    }
    values.update(overrides)
    return BudgetSpec(**values)


def _f_score(x_c: float, denominator: float):
    return build_certified_filling_fraction(
        (_bundle(x_c),),
        (_budget(denominator, certified=True, depth_reference=True),),
        generating_command=_COMMAND,
        worktree_state=_WORKTREE,
    )


def _depth_bin(bin_id: str, start: float, stop: float, **overrides: object):
    values: dict[str, object] = {
        "bin_id": bin_id,
        "depth_min": start,
        "depth_max": stop,
        "depth_unit": "redshift",
        "depth_convention": "z_cmb_bin_edges_left_closed_right_open",
        "selection_rule": "pre-registered redshift bin assignment",
        "selection_hash": f"sha256:selection-{bin_id}",
        "bin_assignment_hash": f"sha256:assignment-{bin_id}",
        "sky_support_status": "mask_weighted_directional_support",
        "mask_status": "masked_with_hash",
        "covariance_status": "mock_covariance",
        "covariance_metadata": {
            "covariance_hash": f"sha256:cov-{bin_id}",
            "shape": [2, 2],
            "estimator": "mock_bank",
            "calibration_status": "matched_calibrated",
        },
        "null_mock_status": "mock_calibrated",
        "null_metadata": {
            "mock_bank_hash": f"sha256:null-{bin_id}",
            "calibration_status": "matched_calibrated",
        },
        "denominator_evolution_status": "per_bin_denominator_recorded",
        "sample_count": 4,
    }
    values.update(overrides)
    return DepthBinMetadata(**values)


def _depth_record(
    bin_id: str,
    start: float,
    stop: float,
    x_c: float,
    denominator: float,
):
    return build_depth_bin_f_record(
        _f_score(x_c, denominator),
        depth_bin=_depth_bin(bin_id, start, stop),
    )


def _rank_audit_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "local_boost_response": (1.0, 0.0),
        "global_tilt_response": (2.0, 0.0),
        "covariance": np.eye(2),
        "observable_labels": ("dipole", "depth"),
        "artifact_id": "htt-response-overlap-firewall-fixture",
        "artifact_path": "memory://htt-response-overlap-firewall-fixture.json",
        "input_hashes": (_INPUT_HASH,),
        "generating_command": _COMMAND,
        "worktree_state": _WORKTREE,
        "sky_support_status": "pr040_sky_support_attached",
        "mask_status": "mask_hash_recorded",
        "covariance_status": "diagnostic_covariance_supplied",
        "null_mock_status": "rank_audit_without_null_fpr",
    }
    values.update(overrides)
    return values


def _atlas_entry_external_as_native() -> object:
    from bass.atlas import AtlasEntryLite
    from bass.transfer.registry import default_external_transfer_registry

    spec = default_external_transfer_registry().get("aniclass.lowell.shear_to_D2.v1")
    metadata = spec.to_metadata()
    metadata["native_solver_result"] = True
    return AtlasEntryLite(
        entry_id="bad.external.native",
        comparison_group="semantic-firewall",
        transfer_metadata=metadata,
        config_hash="sha256:atlas-config",
        input_hashes=("sha256:atlas-input",),
        generating_command=_COMMAND,
        git_commit_or_worktree_state=_WORKTREE,
    )


def _reserved_public_claim_prose() -> FirewallCaseResult:
    text = "\n".join(
        (
            "Result summary: " + "Bianchi " + "geometry " + "detected.",
            "Result summary: " + "Bianchi " + "family " + "identified.",
            "Result summary: AniCLASS transfer is " + "validated as " + "native.",
            "Result summary: MIO " + "reports " + "posterior " + "odds.",
        )
    )
    issues = scan_text(text, path=Path("hostile_claim_surface.md"))
    return _case(
        case_id="reserved_public_claim_prose",
        attack_family="reserved_language",
        surface="common.semantic_guards.no_overclaim.scan_text",
        modules_exercised=("common.semantic_guards.no_overclaim",),
        blocked=bool(issues),
        blocker="scan_text" if issues else "",
    )


def _figure_label_owner_definition_mismatch() -> FirewallCaseResult:
    issues = validate_rows(
        (
            {
                "symbol": "F",
                "owner": "HTT",
                "definition": "one minus look-elsewhere adjusted local-null FPR",
            },
            {
                "symbol": "G_F",
                "owner": "HTT",
                "definition": "normalized log depth-response envelope",
            },
        )
    )
    issue_keys = {(issue.symbol, issue.issue_type) for issue in issues}
    required = {
        ("F", "owner_mismatch"),
        ("F", "definition_mismatch"),
        ("G_F", "owner_mismatch"),
        ("G_F", "definition_mismatch"),
    }
    return _case(
        case_id="figure_label_owner_definition_mismatch",
        attack_family="figure_label",
        surface="scripts.verify_formalism_figure_labels.validate_rows",
        modules_exercised=("scripts.verify_formalism_figure_labels",),
        blocked=required.issubset(issue_keys),
        blocker="label_registry" if required.issubset(issue_keys) else "",
    )


def evaluate_firewall_cases() -> list[FirewallCaseResult]:
    """Run every deterministic hostile case against production guard surfaces."""

    results = [
        _reserved_public_claim_prose(),
        _figure_label_owner_definition_mismatch(),
        _blocked_by_exception(
            case_id="q_family_metadata",
            attack_family="q_metadata",
            surface="mio.formalism.normalized_score.build_normalized_score",
            modules_exercised=("mio.formalism.normalized_score",),
            action=lambda: build_normalized_score(
                _bundle(0.2),
                _budget(1.0),
                numerator_policy="absolute",
                artifact_metadata={
                    "caption": "Q supports " + "family " + "identification"
                },
            ),
        ),
        _blocked_by_exception(
            case_id="f_sign_dirty_sample",
            attack_family="f_semantics",
            surface="mio.formalism.filling_fraction.build_certified_filling_fraction",
            modules_exercised=("mio.formalism.filling_fraction",),
            action=lambda: build_certified_filling_fraction(
                (_bundle(-0.1),),
                (_budget(1.0, certified=True),),
                generating_command=_COMMAND,
                worktree_state=_WORKTREE,
            ),
        ),
        _blocked_by_exception(
            case_id="f_super_ceiling_no_clipping",
            attack_family="f_semantics",
            surface="mio.formalism.filling_fraction.build_certified_filling_fraction",
            modules_exercised=("mio.formalism.filling_fraction",),
            action=lambda: build_certified_filling_fraction(
                (_bundle(1.2),),
                (_budget(1.0, certified=True),),
                generating_command=_COMMAND,
                worktree_state=_WORKTREE,
            ),
        ),
        _blocked_by_exception(
            case_id="f_external_ceiling_not_certified",
            attack_family="f_semantics",
            surface="mio.formalism.budget_spec.BudgetSpec",
            modules_exercised=("mio.formalism.budget_spec",),
            action=lambda: BudgetSpec(
                policy=BudgetPolicy.EXTERNAL_TRANSFER,
                denominator_value=1.0,
                denominator_label="external transfer diagnostic denominator",
                comparator="CMB_FLRW_reference",
                frame="normal_frame",
                units="dimensionless_hubble_normalized",
                config_hash="cfg-external-budget",
                input_hashes=("external-budget-input",),
                assumptions=("transfer-conditional denominator",),
                transfer_source="AniCLASS_external",
                transfer_spec_id="aniclass.firewall.f.v1",
                transfer_metadata=_transfer_metadata("aniclass.firewall.f.v1"),
                admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,),
                is_admissible_ceiling=True,
            ),
        ),
        _blocked_by_exception(
            case_id="f_observational_ceiling_not_certified",
            attack_family="f_semantics",
            surface="mio.formalism.budget_spec.BudgetSpec",
            modules_exercised=("mio.formalism.budget_spec",),
            action=lambda: BudgetSpec(
                policy=BudgetPolicy.OBSERVATIONAL,
                denominator_value=1.0,
                denominator_label="observational diagnostic denominator",
                comparator="CMB_FLRW_reference",
                frame="normal_frame",
                units="dimensionless_hubble_normalized",
                config_hash="cfg-observational-budget",
                input_hashes=("observational-budget-input",),
                assumptions=("masked observational denominator",),
                source_description="masked observational diagnostic bound",
                sky_support_status="partial_sky_masked",
                covariance_status="empirical_covariance",
                null_mock_status="mock_calibrated",
                admissible_uses=(BudgetUse.CERTIFIED_FILLING_CEILING,),
                is_admissible_ceiling=True,
            ),
        ),
        _blocked_by_exception(
            case_id="pi_curve_only_selected_threshold_smuggle",
            attack_family="pi_semantics",
            surface="mio.formalism.exceedance.build_exceedance_curve",
            modules_exercised=("mio.formalism.exceedance",),
            action=lambda: build_exceedance_curve(
                (0.1, 0.3, 0.8),
                source_score_label="Q",
                input_hashes=("pi-input",),
                generating_command=_COMMAND,
                thresholds=(0.2, 0.5),
                threshold_policy=ThresholdPolicy.CURVE_ONLY,
                measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
                worktree_state=_WORKTREE,
                artifact_metadata={"selected_threshold": 0.2},
            ),
        ),
        _blocked_by_exception(
            case_id="pi_post_hoc_threshold_selection",
            attack_family="pi_semantics",
            surface="mio.formalism.exceedance.build_exceedance_curve",
            modules_exercised=("mio.formalism.exceedance",),
            action=lambda: build_exceedance_curve(
                (0.1, 0.3, 0.8),
                source_score_label="Q",
                input_hashes=("pi-input",),
                generating_command=_COMMAND,
                thresholds=(0.2, 0.5),
                threshold_policy=ThresholdPolicy.PRE_REGISTERED,
                threshold_metadata={
                    "registration_status": "pre_registered",
                    "selection_rule": "choose after diagnostic scan",
                    "registration_hash": "sha256:bad-threshold-plan",
                },
                selected_threshold=0.2,
                measure_kind=MeasureKind.SAMPLE_DISTRIBUTION,
                worktree_state=_WORKTREE,
            ),
        ),
        _blocked_by_exception(
            case_id="g_f_reserved_claim_metadata",
            attack_family="g_f_semantics",
            surface="mio.formalism.isotropy_gap.build_isotropy_gap",
            modules_exercised=("mio.formalism.isotropy_gap",),
            action=lambda: build_isotropy_gap(
                (
                    _depth_record("near", 0.0, 0.5, 0.2, 1.0),
                    _depth_record("far", 0.5, 1.0, 0.6, 1.0),
                ),
                reference_bin_id="near",
                comparison_bin_id="far",
                floor_value=_FLOOR,
                floor_label="pre_registered_positive_F_floor",
                floor_reason="floor chosen before depth diagnostic",
                generating_command=_COMMAND,
                worktree_state=_WORKTREE,
                artifact_metadata={
                    "caption": "G_F supports " + "global " + "tilt"
                },
            ),
        ),
        _blocked_by_exception(
            case_id="g_f_missing_covariance_status",
            attack_family="rank_null_covariance",
            surface="mio.formalism.isotropy_gap.DepthBinMetadata",
            modules_exercised=("mio.formalism.isotropy_gap",),
            action=lambda: _depth_bin(
                "near",
                0.0,
                0.5,
                covariance_status="not_statistical",
            ),
        ),
        _blocked_by_exception(
            case_id="htt_likelihood_rejects_mio_payload",
            attack_family="mio_htt_leakage",
            surface="workspace.contracts.htt_posterior.reject_mio_likelihood_inputs",
            modules_exercised=("workspace.contracts.htt_posterior",),
            action=lambda: reject_mio_likelihood_inputs(
                {
                    "owner": "MIO",
                    "report_type": "directional_coherence",
                    "departure_variables": {"resultant_R": 0.9},
                    "consistency_metrics": {"isotropy_pvalue": 0.01},
                }
            ),
        ),
        _blocked_by_exception(
            case_id="htt_pushforward_rejects_mio_payload",
            attack_family="mio_htt_leakage",
            surface="htt.departure.posterior_pushforward.reject_mio_pushforward_inputs",
            modules_exercised=("htt.departure.posterior_pushforward",),
            action=lambda: reject_mio_pushforward_inputs(
                {
                    "owner": "MIO",
                    "implementation_scope": "mio",
                    "sections": {"Q": {"status": "available"}},
                }
            ),
        ),
        _blocked_by_exception(
            case_id="response_rank_deficiency_blocks_model_run",
            attack_family="rank_null_covariance",
            surface="htt.departure.response_overlap.require_rank_audit_for_model_run",
            modules_exercised=("htt.departure.response_overlap",),
            action=lambda: require_rank_audit_for_model_run(
                build_response_overlap_audit(**_rank_audit_kwargs())
            ),
        ),
        _blocked_by_exception(
            case_id="atlas_entry_rejects_external_as_native",
            attack_family="transfer_provenance",
            surface="bass.atlas.AtlasEntryLite",
            modules_exercised=("bass.atlas", "bass.transfer.registry"),
            action=_atlas_entry_external_as_native,
        ),
    ]
    return results


def build_report_payload(
    *,
    repo_root: Path | str = REPO_ROOT,
    json_output: Path = DEFAULT_JSON_OUTPUT,
    md_output: Path = DEFAULT_MD_OUTPUT,
    generating_command: str,
    git_commit_or_worktree_state: str | None = None,
) -> dict[str, object]:
    root = Path(repo_root).resolve()
    cases = evaluate_firewall_cases()
    case_payloads = [case.as_payload() for case in cases]
    smuggles = [case for case in cases if not case.blocked]
    leakage = [
        case
        for case in smuggles
        if case.attack_family in {"mio_htt_leakage", "transfer_provenance"}
    ]
    modules = sorted(
        {
            module
            for case in cases
            for module in case.modules_exercised
        }
    )
    input_hashes = _required_input_hashes(root)
    config_hash = _stable_hash(
        {
            "schema_version": SCHEMA_VERSION,
            "case_ids": [case.case_id for case in cases],
            "attack_families": sorted({case.attack_family for case in cases}),
            "modules_exercised": modules,
        }
    )
    state = git_commit_or_worktree_state or _current_git_state(root)
    return {
        "artifact_id": ARTIFACT_ID,
        "artifact_path": _repo_relative(md_output, root),
        "json_artifact_path": _repo_relative(json_output, root),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "schema_version": SCHEMA_VERSION,
        "created_by": "scripts/generate_semantic_firewall_fuzz_report.py",
        "transfer_source": "mixed_none_and_external_transfer_controls",
        "sky_support_status": "mixed_not_directional_and_masked_controls",
        "null_mock_status": "mixed_diagnostic_null_and_constructor_controls",
        "covariance_status": "mixed_diagnostic_covariance_and_constructor_controls",
        "config_hash": config_hash,
        "input_hashes": input_hashes,
        "generating_command": generating_command,
        "git_commit_or_worktree_state": state,
        "attack_count": len(cases),
        "blocked_count": len([case for case in cases if case.blocked]),
        "smuggle_count": len(smuggles),
        "leakage_path_count": len(leakage),
        "all_cases_blocked": not smuggles,
        "modules_exercised": modules,
        "cases": case_payloads,
        "publication_ready": False,
        "science_claim_ceiling": (
            "diagnostic-only firewall coverage; not scientific validation"
        ),
        "caveats": [
            "This artifact tests hostile semantic paths against production guard surfaces.",
            "The report is diagnostic-only firewall coverage; not scientific validation.",
            "It does not validate a native low-ell solver, transfer calibration, or morphology atlas.",
            "It records sanitized case ids only; hostile prose payloads and exception text are intentionally omitted.",
        ],
    }


def render_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"


def render_markdown(payload: Mapping[str, object]) -> str:
    lines = [
        "# Semantic Firewall Fuzz Report",
        "",
        f"artifact_id: {payload['artifact_id']}",
        f"owner: {payload['owner']}",
        f"implementation_scope: {payload['implementation_scope']}",
        f"claim_tier: {payload['claim_tier']}",
        f"production_status: {payload['production_status']}",
        f"schema_version: {payload['schema_version']}",
        f"transfer_source: {payload['transfer_source']}",
        f"sky_support_status: {payload['sky_support_status']}",
        f"null_mock_status: {payload['null_mock_status']}",
        f"covariance_status: {payload['covariance_status']}",
        f"config_hash: {payload['config_hash']}",
        f"generating_command: `{payload['generating_command']}`",
        f"git_commit_or_worktree_state: {payload['git_commit_or_worktree_state']}",
        "",
        "## Summary",
        "",
        f"- attack_count: {payload['attack_count']}",
        f"- blocked_count: {payload['blocked_count']}",
        f"- smuggle_count: {payload['smuggle_count']}",
        f"- leakage_path_count: {payload['leakage_path_count']}",
        f"- publication_ready: {str(payload['publication_ready']).lower()}",
        f"- science_claim_ceiling: {payload['science_claim_ceiling']}",
        "",
        "## Case Matrix",
        "",
        "| Case | Family | Surface | Blocked | Blocker |",
        "| --- | --- | --- | --- | --- |",
    ]
    for case in payload["cases"]:  # type: ignore[index]
        if not isinstance(case, Mapping):
            continue
        lines.append(
            "| {case_id} | {attack_family} | `{surface}` | {blocked} | {blocker} |".format(
                case_id=case["case_id"],
                attack_family=case["attack_family"],
                surface=case["surface"],
                blocked=str(case["blocked"]).lower(),
                blocker=case["blocker"],
            )
        )
    lines.extend(
        [
            "",
            "## Modules Exercised",
            "",
        ]
    )
    lines.extend(f"- `{module}`" for module in payload["modules_exercised"])  # type: ignore[index]
    lines.extend(
        [
            "",
            "## Caveats",
            "",
        ]
    )
    lines.extend(f"- {caveat}" for caveat in payload["caveats"])  # type: ignore[index]
    lines.append("")
    return "\n".join(lines)


def _write_outputs(payload: Mapping[str, object], json_output: Path, md_output: Path) -> None:
    json_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(render_json(payload), encoding="utf-8")
    md_output.write_text(render_markdown(payload), encoding="utf-8")


def _outputs_current(payload: Mapping[str, object], json_output: Path, md_output: Path) -> bool:
    if not json_output.is_file() or not md_output.is_file():
        return False
    return (
        json_output.read_text(encoding="utf-8") == render_json(payload)
        and md_output.read_text(encoding="utf-8") == render_markdown(payload)
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-output", type=Path, default=DEFAULT_JSON_OUTPUT)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_OUTPUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    json_output = (
        args.json_output
        if args.json_output.is_absolute()
        else REPO_ROOT / args.json_output
    )
    md_output = (
        args.md_output
        if args.md_output.is_absolute()
        else REPO_ROOT / args.md_output
    )
    command_args = [
        arg
        for arg in (sys.argv[1:] if argv is None else list(argv))
        if arg != "--check"
    ]
    command = " ".join(["python", "scripts/generate_semantic_firewall_fuzz_report.py", *command_args]).strip()
    existing_state = _existing_git_state(json_output, REPO_ROOT) if args.check else None
    payload = build_report_payload(
        repo_root=REPO_ROOT,
        json_output=json_output,
        md_output=md_output,
        generating_command=command,
        git_commit_or_worktree_state=existing_state,
    )
    if not payload["all_cases_blocked"]:
        failed = [case["case_id"] for case in payload["cases"] if not case["blocked"]]  # type: ignore[index]
        print("semantic firewall smuggle(s) detected: " + ", ".join(failed), file=sys.stderr)
        return 1
    if args.check:
        if not _outputs_current(payload, json_output, md_output):
            print(
                "semantic firewall fuzz report is stale; rerun "
                "python scripts/generate_semantic_firewall_fuzz_report.py",
                file=sys.stderr,
            )
            return 1
        print("semantic firewall fuzz report is current")
        return 0
    _write_outputs(payload, json_output, md_output)
    print(f"wrote {_repo_relative(json_output, REPO_ROOT)}")
    print(f"wrote {_repo_relative(md_output, REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
