#!/usr/bin/env python3
"""Build and score exact Planck MES morphology from the PR-324 feature pool.

The script is map-free and consumes only the corrected feature package.  It
does not import the quarantined legacy Planck MES implementation.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from typing import Mapping, Sequence

import numpy as np

from obsstat.mes_row_anchor import (
    MesRowAnchorError,
    MesRowAnchorState,
    ResidualDipoleAttribution,
    build_mes_row_anchor_pool,
    mes_row_anchor_pool_payload,
    numeric_array_content_identity,
)
from obsstat.planck_post275_lane import observation_inclusive_max_scan
try:
    from scripts.observed_runs.run_planck_pr3 import (
        PlanckWorkerError,
        replay_pr315_feature_package,
    )
except ModuleNotFoundError as exc:  # direct ``python scripts/...`` execution
    if exc.name not in {"scripts", "scripts.observed_runs"}:
        raise
    from run_planck_pr3 import PlanckWorkerError, replay_pr315_feature_package


OBSERVED_ROW_ID = "PLANCK-PR3-SMICA-OBSERVED"
ROOT = Path(__file__).resolve().parents[2]


class PlanckMesMorphologyError(MesRowAnchorError):
    """Raised when the exact 301-row MES morphology contract drifts."""


SOURCE_FEATURE_IDS = (
    "cl_l2",
    "cl_l3",
    "cl_l4",
    "cl_l5",
    "parity_even_over_odd_l2_l5",
    "power_tensor_gap_l2",
    "power_tensor_gap_l3",
    "multipole_l2_absdot",
    "multipole_l3_absdot_0",
    "multipole_l3_absdot_1",
    "multipole_l3_absdot_2",
    "multipole_plane_alignment_max_l2_l3",
)
SOURCE_FEATURE_UNITS = (
    "microK_CMB^2",
    "microK_CMB^2",
    "microK_CMB^2",
    "microK_CMB^2",
    *("dimensionless",) * 8,
)
MES_FEATURE_IDS = (
    "mes_sigma_anchor",
    "mes_omega_anchor",
    *SOURCE_FEATURE_IDS[4:],
)
MES_FEATURE_UNITS = ("dimensionless",) * len(MES_FEATURE_IDS)
MES_FEATURE_ROLES = (
    "ROWWISE_REALIZATION_CONDITIONAL_MES_AMPLITUDE_ANCHOR",
    "ROWWISE_REALIZATION_CONDITIONAL_MES_AMPLITUDE_ANCHOR",
    *("DIMENSIONLESS_IRREDUCIBLE_MORPHOLOGY",) * 8,
)
MES_TAILS = ("two-sided",) * len(MES_FEATURE_IDS)
MES_PACKAGE_FILENAME = "planck_mes_morphology.npz"
MES_METADATA_FILENAME = "planck_mes_morphology_metadata.json"
MES_RESULT_FILENAME = "planck_mes_morphology_result.json"
MES_REPLAY_FILENAME = "planck_mes_morphology_replay.json"
PR314_RESULT_SHA256 = (
    "sha256:898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97"
)
GENERIC_BENCHMARK_CONTROL = {
    "role": "FROZEN_PR314_BENCHMARK_CONTROL_NOT_MES",
    "result_sha256": PR314_RESULT_SHA256,
    "rank_fraction": "133/301",
    "reduced_fraction": "19/43",
}
MES_OPERATOR_SPEC = {
    "format": "PLANCK_MES_MORPHOLOGY_OPERATOR_V1",
    "source_feature_order": list(SOURCE_FEATURE_IDS),
    "output_feature_order": list(MES_FEATURE_IDS),
    "output_feature_roles": list(MES_FEATURE_ROLES),
    "tails": list(MES_TAILS),
    "row_anchor_branch": "SAG_OBSERVER_MOTION_EPS1_ZERO",
    "row_anchor_channels": ["sigma", "omega"],
    "raw_cl_amplitudes_replaced_by_anchors": ["cl_l2", "cl_l3"],
    "raw_cl_channels_excluded": ["cl_l2", "cl_l3", "cl_l4", "cl_l5"],
    "scan": "observation_inclusive_leave_one_out_max_exact_finite_rank_v1",
    "covariance": "canonical_row_id_ordered_pooled_301_row_ddof1_diagnostic",
    "selection_rule": "NO_OPERATOR_OR_TAIL_SELECTED_FROM_OBSERVED_OUTCOME",
}


def _canonical_hash(payload: object, *, role: str) -> str:
    encoded = json.dumps(
        {"role": role, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


MES_OPERATOR_IDENTITY = _canonical_hash(
    MES_OPERATOR_SPEC, role="planck_mes_morphology_operator"
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _strict_json(path: Path, *, label: str) -> dict[str, object]:
    try:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PlanckMesMorphologyError(f"{label} is invalid") from exc
    if not isinstance(payload, dict):
        raise PlanckMesMorphologyError(f"{label} must be a JSON object")
    return payload


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    Path(path).write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _git_generation_state() -> dict[str, str]:
    try:
        head, tree = subprocess.check_output(
            ["git", "rev-parse", "HEAD", "HEAD^{tree}"],
            cwd=ROOT,
            text=True,
        ).splitlines()
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=ROOT,
                text=True,
            ).strip()
        )
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        raise PlanckMesMorphologyError("generating git identity is unavailable") from exc
    return {
        "generating_git_head": head,
        "generating_git_tree": tree,
        "generating_worktree_state": (
            "DIRTY_BOUND_BY_GENERATOR_SOURCE_SHA256" if dirty else "CLEAN"
        ),
        "generator_source_sha256": _sha256_file(Path(__file__).resolve()),
    }


def _load_feature_pool(
    package_path: Path,
) -> tuple[
    np.ndarray,
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    tuple[str, ...],
    np.ndarray,
]:
    try:
        with np.load(package_path, allow_pickle=False) as bundle:
            observed = np.asarray(bundle["observed_features"], dtype=float)
            nulls = np.asarray(bundle["null_features"], dtype=float)
            covariance = np.asarray(bundle["covariance"], dtype=float)
            null_row_ids = tuple(
                str(value) for value in bundle["row_ids"].tolist()
            )
            feature_ids = tuple(
                str(value) for value in bundle["feature_ids"].tolist()
            )
            feature_units = tuple(
                str(value) for value in bundle["feature_units"].tolist()
            )
            tails = tuple(str(value) for value in bundle["tails"].tolist())
    except (KeyError, OSError, ValueError) as exc:
        raise MesRowAnchorError("PR-324 feature pool is unavailable") from exc
    if observed.ndim != 1 or nulls.ndim != 2 or nulls.shape[1:] != observed.shape:
        raise MesRowAnchorError("PR-324 feature pool row dimensions drifted")
    return (
        np.vstack((observed, nulls)),
        (OBSERVED_ROW_ID, *null_row_ids),
        feature_ids,
        feature_units,
        tails,
        covariance,
    )


def _state_map(
    states: Sequence[MesRowAnchorState],
) -> dict[str, MesRowAnchorState]:
    return {state.row_id: state for state in states}


def _anchor_equivariance_receipt(
    *,
    row_ids: tuple[str, ...],
    feature_matrix: np.ndarray,
    common: Mapping[str, object],
    baseline: tuple[MesRowAnchorState, ...],
) -> dict[str, str]:
    baseline_by_id = _state_map(baseline)
    reversed_states = build_mes_row_anchor_pool(
        row_ids=tuple(reversed(row_ids)),
        feature_matrix=feature_matrix[::-1],
        **common,
    )
    if _state_map(reversed_states) != baseline_by_id:
        raise MesRowAnchorError("row permutation equivariance failed")
    swap = np.arange(len(row_ids))
    swap[0], swap[1] = swap[1], swap[0]
    swapped_states = build_mes_row_anchor_pool(
        row_ids=tuple(row_ids[index] for index in swap),
        feature_matrix=feature_matrix[swap],
        **common,
    )
    if _state_map(swapped_states) != baseline_by_id:
        raise MesRowAnchorError("observation swap equivariance failed")
    return {"observation_swap": "PASS", "row_permutation": "PASS"}


def run_planck_mes_row_anchors(
    *,
    feature_package_path: Path,
    feature_metadata_path: Path,
    output_path: Path,
    residual_dipole_attribution: ResidualDipoleAttribution | None,
) -> dict[str, object]:
    """Execute the exact 1+300 row-anchor transform and write its receipt."""

    if not isinstance(residual_dipole_attribution, ResidualDipoleAttribution):
        raise MesRowAnchorError("BLOCKED_MES_ATTRIBUTION")
    package_path = Path(feature_package_path)
    metadata_path = Path(feature_metadata_path)
    output = Path(output_path)
    if output.exists():
        raise MesRowAnchorError("row-anchor output path must not already exist")

    replay = replay_pr315_feature_package(
        package_path=package_path,
        metadata_path=metadata_path,
    )
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise MesRowAnchorError("PR-324 feature metadata is invalid") from exc
    (
        matrix,
        row_ids,
        feature_ids,
        feature_units,
        _,
        covariance,
    ) = _load_feature_pool(package_path)
    if len(row_ids) != 301:
        raise MesRowAnchorError("exact Planck row-anchor pool requires 301 rows")
    common: dict[str, object] = {
        "feature_ids": feature_ids,
        "feature_units": feature_units,
        "residual_dipole_attribution": residual_dipole_attribution,
        "source_identity": replay["feature_package_sha256"],
        "covariance_identity": numeric_array_content_identity(
            covariance, role="PR315_EXACT_300_NULL_COVARIANCE"
        ),
        "operator_identity": replay["operator_identity_sha256"],
    }
    states = build_mes_row_anchor_pool(
        row_ids=row_ids,
        feature_matrix=matrix,
        **common,
    )
    payload = mes_row_anchor_pool_payload(states)
    payload.update(
        {
            "artifact_mode": "observed_diagnostic_row_anchor_state",
            "owner": "OBSSTAT",
            "scope": (
                "Planck PR3 SMICA corrected ell=2..3 rowwise geodesic MES "
                "anchor coordinates"
            ),
            "source_feature_package_identity": replay[
                "feature_package_sha256"
            ],
            "source_feature_projection_identity": replay[
                "scientific_projection_sha256"
            ],
            "source_feature_metadata_identity": replay[
                "feature_metadata_sha256"
            ],
            "raw_input_manifest_sha256": metadata.get(
                "raw_input_manifest_sha256"
            ),
            "null_ordered_row_ids_sha256": metadata.get(
                "null_ordered_row_ids_sha256"
            ),
            "equivariance_receipt": _anchor_equivariance_receipt(
                row_ids=row_ids,
                feature_matrix=matrix,
                common=common,
                baseline=states,
            ),
            "residual_dipole_premise": (
                "SAG observer-motion eps1=0 branch selected explicitly for "
                "the observed analysis and applied identically to observation "
                "and null scoring rows; this does not attribute a physical "
                "observer dipole to each simulated null"
            ),
            "generic_control_preserved": True,
            "MES_anchor_state": True,
            "MES_observed_result": False,
            "global_claim_boundary": "ABSTAIN_GLOBAL_RESPONSE_UNAVAILABLE",
            "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
            "transfer_source": metadata.get("transfer_source"),
            "sky_support_status": metadata.get("sky_support_status"),
            "covariance_status": metadata.get("covariance_status"),
            "null_mock_status": metadata.get("null_mock_status"),
            "caveats": metadata.get("caveats"),
            "allowed_use": [
                "rowwise prerequisite for symmetric finite-null MES scoring",
                "preregistered observational-coordinate construction input",
            ],
            "forbidden_use": [
                "independent evidence",
                "defined physical MES stress without a response",
                "local boost versus global tilt identification from Planck",
                "native solver result",
                "Bianchi family identification",
            ],
            "generating_procedure": (
                "scripts.observed_runs.run_planck_mes_morphology."
                "run_planck_mes_row_anchors"
            ),
            "raw_maps_reopened": False,
        }
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return payload


def build_planck_mes_morphology_rows(
    *,
    row_ids: Sequence[str],
    feature_matrix: Sequence[Sequence[float]],
    feature_ids: Sequence[str],
    feature_units: Sequence[str],
    residual_dipole_attribution: ResidualDipoleAttribution,
    source_identity: str,
    covariance_identity: str,
    operator_identity: str,
) -> tuple[np.ndarray, tuple[MesRowAnchorState, ...]]:
    """Apply the frozen two-anchor plus eight-invariant operator to 301 rows."""

    ids = tuple(row_ids)
    if len(ids) != 301:
        raise PlanckMesMorphologyError(
            "exact Planck MES morphology pool requires exactly 301 rows"
        )
    if len(set(ids)) != 301 or ids.count(OBSERVED_ROW_ID) != 1:
        raise PlanckMesMorphologyError(
            "exact Planck MES morphology row identities drifted"
        )
    source_ids = tuple(feature_ids)
    source_units = tuple(feature_units)
    if source_ids != SOURCE_FEATURE_IDS or source_units != SOURCE_FEATURE_UNITS:
        raise PlanckMesMorphologyError("source feature schema drifted")
    try:
        matrix = np.asarray(feature_matrix, dtype=float)
    except (TypeError, ValueError) as exc:
        raise PlanckMesMorphologyError("source feature rows must be numeric") from exc
    if matrix.shape != (301, len(SOURCE_FEATURE_IDS)) or not np.all(
        np.isfinite(matrix)
    ):
        raise PlanckMesMorphologyError(
            "exact Planck MES morphology feature matrix drifted"
        )
    try:
        states = build_mes_row_anchor_pool(
            row_ids=ids,
            feature_matrix=matrix,
            feature_ids=source_ids,
            feature_units=source_units,
            residual_dipole_attribution=residual_dipole_attribution,
            source_identity=source_identity,
            covariance_identity=covariance_identity,
            operator_identity=operator_identity,
        )
    except MesRowAnchorError as exc:
        raise PlanckMesMorphologyError(str(exc)) from exc
    anchor_rows = np.asarray(
        [
            (state.anchor("sigma").value, state.anchor("omega").value)
            for state in states
        ],
        dtype=float,
    )
    if anchor_rows.shape != (301, 2) or not np.all(np.isfinite(anchor_rows)):
        raise PlanckMesMorphologyError("active MES anchors are incomplete")
    if np.any(anchor_rows <= 0.0):
        raise PlanckMesMorphologyError("active MES anchors must be positive")
    morphology_rows = matrix[:, 4:]
    rows = np.column_stack((anchor_rows, morphology_rows))
    if rows.shape != (301, len(MES_FEATURE_IDS)) or not np.all(np.isfinite(rows)):
        raise PlanckMesMorphologyError("MES morphology row operator drifted")
    return rows, states


def _pooled_covariance(
    rows: np.ndarray,
    row_ids: Sequence[str],
) -> tuple[np.ndarray, dict[str, object]]:
    identifiers = tuple(row_ids)
    canonical_order = np.asarray(
        sorted(range(len(identifiers)), key=identifiers.__getitem__), dtype=int
    )
    covariance = np.cov(rows[canonical_order], rowvar=False, ddof=1)
    if (
        covariance.shape != (len(MES_FEATURE_IDS), len(MES_FEATURE_IDS))
        or not np.all(np.isfinite(covariance))
        or not np.allclose(covariance, covariance.T, rtol=0.0, atol=1e-30)
    ):
        raise PlanckMesMorphologyError("pooled MES covariance is invalid")
    try:
        np.linalg.cholesky(covariance)
    except np.linalg.LinAlgError as exc:
        raise PlanckMesMorphologyError(
            "pooled MES covariance is not positive definite"
        ) from exc
    standard_deviations = np.sqrt(np.diag(covariance))
    if np.any(standard_deviations <= 0.0):
        raise PlanckMesMorphologyError("pooled MES covariance has zero variance")
    correlation = covariance / np.outer(standard_deviations, standard_deviations)
    rank = int(np.linalg.matrix_rank(correlation))
    condition = float(np.linalg.cond(correlation))
    if rank != len(MES_FEATURE_IDS) or not np.isfinite(condition):
        raise PlanckMesMorphologyError(
            "pooled MES covariance loses standardized full rank"
        )
    identity = numeric_array_content_identity(
        covariance, role="PR327_POOLED_301_ROW_MES_DIAGNOSTIC_COVARIANCE"
    )
    return covariance, {
        "identity": identity,
        "scope": "POOLED_OBSERVATION_PLUS_300_NULL_DIAGNOSTIC_COVARIANCE",
        "row_order": "CANONICAL_LEXICOGRAPHIC_ROW_ID_ORDER",
        "ddof": 1,
        "dimension": len(MES_FEATURE_IDS),
        "standardized_rank": rank,
        "standardized_condition_number": condition,
        "raw_cholesky": "PASS",
        "used_by_rank_scan": False,
        "likelihood_role": "NOT_A_LIKELIHOOD_COVARIANCE",
    }


def _finite_rank_numerator(value: Fraction, row_count: int) -> int:
    scaled = value * row_count
    if scaled.denominator != 1:
        raise PlanckMesMorphologyError("finite rank does not resolve on the row pool")
    return scaled.numerator


def _mes_equivariance_receipt(
    *, rows: np.ndarray, row_ids: tuple[str, ...], covariance: np.ndarray
) -> dict[str, str]:
    observation_index = row_ids.index(OBSERVED_ROW_ID)
    baseline = observation_inclusive_max_scan(
        rows, MES_TAILS, observation_index=observation_index
    )
    reversed_ids = tuple(reversed(row_ids))
    reversed_rows = rows[::-1]
    reversed_scan = observation_inclusive_max_scan(
        reversed_rows,
        MES_TAILS,
        observation_index=reversed_ids.index(OBSERVED_ROW_ID),
    )
    if (
        reversed_scan.global_p != baseline.global_p
        or reversed_scan.local_p != baseline.local_p
    ):
        raise PlanckMesMorphologyError("row permutation equivariance failed")

    swap = np.arange(len(row_ids))
    other = 1 if observation_index == 0 else 0
    swap[observation_index], swap[other] = swap[other], swap[observation_index]
    swapped_ids = tuple(row_ids[index] for index in swap)
    swapped_scan = observation_inclusive_max_scan(
        rows[swap], MES_TAILS, observation_index=swapped_ids.index(OBSERVED_ROW_ID)
    )
    if swapped_scan.global_p != baseline.global_p or swapped_scan.local_p != baseline.local_p:
        raise PlanckMesMorphologyError("observation index swap equivariance failed")

    reversed_covariance, _ = _pooled_covariance(reversed_rows, reversed_ids)
    if not np.array_equal(reversed_covariance, covariance):
        raise PlanckMesMorphologyError("pooled covariance row permutation failed")
    return {
        "observation_index_swap": "PASS",
        "row_permutation": "PASS",
        "pooled_covariance_row_permutation": "PASS",
    }


def _validate_generic_control() -> dict[str, str]:
    path = ROOT / "docs/generated/pr314_planck_pr3_smica_existing_result.json"
    if _sha256_file(path) != PR314_RESULT_SHA256:
        raise PlanckMesMorphologyError("frozen PR-314 benchmark control drifted")
    payload = _strict_json(path, label="PR-314 benchmark control")
    if payload.get("finite_feature_family_p") != "19/43":
        raise PlanckMesMorphologyError("frozen PR-314 133/301 rank drifted")
    return dict(GENERIC_BENCHMARK_CONTROL)


def _anchor_binding_identity(
    *,
    row_ids: Sequence[str],
    row_content_identities: Sequence[str],
    source_identity: str,
    source_covariance_identity: str,
    source_operator_identity: str,
) -> str:
    return _canonical_hash(
        {
            "row_ids": list(row_ids),
            "row_content_identities": list(row_content_identities),
            "source_identity": source_identity,
            "source_covariance_identity": source_covariance_identity,
            "source_operator_identity": source_operator_identity,
        },
        role="pr327_mes_anchor_row_binding",
    )


def _result_scientific_projection(result: Mapping[str, object]) -> dict[str, object]:
    keys = (
        "primary_result_role",
        "source_feature_package_identity",
        "source_feature_projection_identity",
        "source_feature_metadata_identity",
        "source_anchor_binding_identity",
        "mes_operator_identity",
        "mes_feature_matrix_identity",
        "pooled_covariance",
        "observed_mes_feature_vector",
        "global_finite_rank",
        "local_finite_rank_fractions",
        "local_finite_rank_numerators",
        "equivariance_receipt",
        "generic_benchmark_control",
        "directional_moment_state",
        "local_global_response",
        "family_identification_gate",
    )
    if any(key not in result for key in keys):
        raise PlanckMesMorphologyError("MES result scientific projection is incomplete")
    return {key: result[key] for key in keys}


def _result_payload(
    *,
    source_replay: Mapping[str, object],
    source_metadata: Mapping[str, object],
    rows: np.ndarray,
    row_ids: tuple[str, ...],
    scan: object,
    covariance_diagnostic: Mapping[str, object],
    feature_matrix_identity: str,
    anchor_binding_identity: str,
    package_identity: str,
    equivariance_receipt: Mapping[str, str],
    generic_control: Mapping[str, str],
    generation_state: Mapping[str, str],
) -> dict[str, object]:
    row_count = len(row_ids)
    local_numerators = [
        _finite_rank_numerator(value, row_count) for value in scan.local_p
    ]
    global_numerator = _finite_rank_numerator(scan.global_p, row_count)
    observation_index = row_ids.index(OBSERVED_ROW_ID)
    return {
        "format": "PLANCK_PR327_MES_MORPHOLOGY_RESULT_V1",
        "owner": "OBSSTAT",
        "scope": (
            "Planck PR3 SMICA exact observation plus 300 ordered paired-null "
            "MES-anchored scalar irreducible morphology"
        ),
        "artifact_mode": "observed_diagnostic",
        "claim_id": "C-PR135-FINITE-NULL-RANK",
        "claim_status": "DIAGNOSTIC_ONLY",
        "evidence_type": "artifact",
        "claim_tier": "diagnostic_only",
        "claim_level": "C2",
        "primary_result_role": (
            "MES_ANCHORED_SCALAR_IRREDUCIBLE_MORPHOLOGY_FINITE_RANK"
        ),
        "pipeline_scope": "SMICA_ONLY_EXACT_300_PAIRED_NULLS",
        "observed_data_executed": True,
        "public_use": False,
        "row_count": row_count,
        "null_count": row_count - 1,
        "observation_row_id": OBSERVED_ROW_ID,
        "observation_index": observation_index,
        "feature_order": list(MES_FEATURE_IDS),
        "feature_units": list(MES_FEATURE_UNITS),
        "feature_roles": list(MES_FEATURE_ROLES),
        "tails": list(MES_TAILS),
        "observed_mes_feature_vector": [
            float(value) for value in rows[observation_index]
        ],
        "global_finite_rank": {
            "exceedances_including_observation": global_numerator,
            "denominator": row_count,
            "fraction": f"{global_numerator}/{row_count}",
            "reduced_fraction": str(scan.global_p),
        },
        "local_finite_rank_fractions": [str(value) for value in scan.local_p],
        "local_finite_rank_numerators": local_numerators,
        "resolution_floor": f"1/{row_count}",
        "rank_tail_policy": "CONSERVATIVE_GREATER_OR_EQUAL",
        "rank_scan": "OBSERVATION_INCLUSIVE_LEAVE_ONE_OUT_ROW_MAX",
        "equivariance_receipt": dict(equivariance_receipt),
        "pooled_covariance": dict(covariance_diagnostic),
        "mes_feature_package_identity": package_identity,
        "mes_feature_matrix_identity": feature_matrix_identity,
        "mes_operator_identity": MES_OPERATOR_IDENTITY,
        "source_anchor_binding_identity": anchor_binding_identity,
        "source_feature_package_identity": source_replay[
            "feature_package_sha256"
        ],
        "source_feature_projection_identity": source_replay[
            "scientific_projection_sha256"
        ],
        "source_feature_metadata_identity": source_replay[
            "feature_metadata_sha256"
        ],
        "raw_input_manifest_sha256": source_metadata.get(
            "raw_input_manifest_sha256"
        ),
        "null_ordered_row_ids_sha256": source_metadata.get(
            "null_ordered_row_ids_sha256"
        ),
        "transfer_source": source_metadata.get("transfer_source"),
        "sky_support_status": source_metadata.get("sky_support_status"),
        "null_mock_status": source_metadata.get("null_mock_status"),
        "self_anchor_shared_data_dependence": True,
        "self_anchor_independent_information_gain": False,
        "MES_anchor_state": True,
        "MES_observed_result": True,
        "directional_moment_state": "BLOCKED_DIRECTIONAL_SUPPORT",
        "local_global_response": "SINGLE_SHELL_LOCAL_GLOBAL_NONIDENTIFIED",
        "global_claim_boundary": "ABSTAIN_GLOBAL_RESPONSE_UNAVAILABLE",
        "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
        "generic_benchmark_control": dict(generic_control),
        "generic_control_preserved": True,
        "allowed_use": [
            "exact finite-null MES morphology diagnostic",
            "row-equivariant comparison under the frozen 301-row operator",
            "map-free portable replay",
        ],
        "forbidden_use": [
            "unconditional p-value",
            "independent evidence from rowwise self-anchors",
            "direction or STF tensor from scalar morphology",
            "local boost versus global tilt identification from Planck",
            "posterior evidence",
            "native solver result",
            "Bianchi family identification",
        ],
        "caveats": [
            "single SMICA shell only; Commander robustness is not required here",
            "finite rank is conditional on the exact 300 paired null rows",
            "pooled covariance is diagnostic and is not used by the rank scan",
            "the source package contains no direction-indexed support",
            "Planck alone cannot identify local boost versus global tilt",
        ],
        "generating_procedure": (
            "scripts.observed_runs.run_planck_mes_morphology."
            "run_planck_mes_morphology_analysis"
        ),
        "generating_command": (
            "python scripts/observed_runs/run_planck_mes_morphology.py "
            "--feature-package docs/generated/pr315_planck_smica_feature_replay.npz "
            "--feature-metadata docs/generated/pr315_planck_smica_feature_replay.json "
            "--output-dir docs/generated/planck_mes_morphology "
            "--residual-dipole-attribution SAG_OBSERVER_MOTION_EPS1_ZERO"
        ),
        "raw_maps_reopened": False,
        **generation_state,
    }


def _load_mes_package(
    package_path: Path,
) -> tuple[np.ndarray, np.ndarray, tuple[str, ...], tuple[str, ...]]:
    try:
        with np.load(package_path, allow_pickle=False) as bundle:
            if set(bundle.files) != {
                "feature_rows",
                "pooled_covariance",
                "row_ids",
                "feature_ids",
                "feature_units",
                "feature_roles",
                "tails",
                "anchor_row_content_identities",
            }:
                raise PlanckMesMorphologyError("MES package keys drifted")
            rows = np.asarray(bundle["feature_rows"], dtype=float)
            covariance = np.asarray(bundle["pooled_covariance"], dtype=float)
            row_ids = tuple(str(value) for value in bundle["row_ids"].tolist())
            feature_ids = tuple(
                str(value) for value in bundle["feature_ids"].tolist()
            )
            feature_units = tuple(
                str(value) for value in bundle["feature_units"].tolist()
            )
            feature_roles = tuple(
                str(value) for value in bundle["feature_roles"].tolist()
            )
            tails = tuple(str(value) for value in bundle["tails"].tolist())
            anchor_identities = tuple(
                str(value)
                for value in bundle["anchor_row_content_identities"].tolist()
            )
    except (KeyError, OSError, ValueError) as exc:
        raise PlanckMesMorphologyError("MES package is not safe numeric NPZ") from exc
    if (
        rows.shape != (301, len(MES_FEATURE_IDS))
        or covariance.shape != (len(MES_FEATURE_IDS), len(MES_FEATURE_IDS))
        or len(row_ids) != 301
        or len(set(row_ids)) != 301
        or row_ids[0] != OBSERVED_ROW_ID
        or feature_ids != MES_FEATURE_IDS
        or feature_units != MES_FEATURE_UNITS
        or feature_roles != MES_FEATURE_ROLES
        or tails != MES_TAILS
        or len(anchor_identities) != 301
        or not np.all(np.isfinite(rows))
        or not np.all(np.isfinite(covariance))
    ):
        raise PlanckMesMorphologyError("MES package schema or row pool drifted")
    return rows, covariance, row_ids, anchor_identities


def replay_planck_mes_morphology_package(
    *, output_dir: Path
) -> dict[str, object]:
    """Recompute the portable PR-327 rank without source maps or likelihoods."""

    directory = Path(output_dir)
    package_path = directory / MES_PACKAGE_FILENAME
    metadata_path = directory / MES_METADATA_FILENAME
    result_path = directory / MES_RESULT_FILENAME
    metadata = _strict_json(metadata_path, label="PR-327 MES metadata")
    result = _strict_json(result_path, label="PR-327 MES result")
    if (
        metadata.get("format") != "PLANCK_PR327_MES_MORPHOLOGY_PACKAGE_V1"
        or result.get("format") != "PLANCK_PR327_MES_MORPHOLOGY_RESULT_V1"
        or metadata.get("package_filename") != MES_PACKAGE_FILENAME
        or metadata.get("result_filename") != MES_RESULT_FILENAME
    ):
        raise PlanckMesMorphologyError("MES artifact format drifted")
    if metadata.get("result_sha256") != _sha256_file(result_path):
        raise PlanckMesMorphologyError("MES result identity drifted")
    source_fields = (
        "source_feature_package_identity",
        "source_feature_projection_identity",
        "source_feature_metadata_identity",
        "source_anchor_binding_identity",
    )
    if any(metadata.get(field) != result.get(field) for field in source_fields):
        raise PlanckMesMorphologyError("MES source identity drifted")
    if (
        metadata.get("package_byte_size") != package_path.stat().st_size
        or metadata.get("package_sha256") != _sha256_file(package_path)
        or result.get("mes_feature_package_identity")
        != metadata.get("package_sha256")
    ):
        raise PlanckMesMorphologyError("MES package identity drifted")
    rows, stored_covariance, row_ids, anchor_identities = _load_mes_package(
        package_path
    )
    feature_matrix_identity = numeric_array_content_identity(
        rows, role="PR327_ORDERED_301_ROW_MES_MORPHOLOGY_FEATURE_MATRIX"
    )
    if (
        metadata.get("mes_feature_matrix_identity") != feature_matrix_identity
        or result.get("mes_feature_matrix_identity") != feature_matrix_identity
    ):
        raise PlanckMesMorphologyError("MES feature matrix identity drifted")
    anchor_binding_identity = _anchor_binding_identity(
        row_ids=row_ids,
        row_content_identities=anchor_identities,
        source_identity=str(metadata["source_feature_package_identity"]),
        source_covariance_identity=str(metadata["source_covariance_identity"]),
        source_operator_identity=str(metadata["source_operator_identity"]),
    )
    if metadata.get("source_anchor_binding_identity") != anchor_binding_identity:
        raise PlanckMesMorphologyError("MES source anchor identity drifted")
    covariance, covariance_diagnostic = _pooled_covariance(rows, row_ids)
    if not np.array_equal(covariance, stored_covariance):
        raise PlanckMesMorphologyError("MES pooled covariance replay drifted")
    if result.get("pooled_covariance") != covariance_diagnostic:
        raise PlanckMesMorphologyError("MES covariance diagnostic drifted")
    scan = observation_inclusive_max_scan(rows, MES_TAILS, observation_index=0)
    local_numerators = [
        _finite_rank_numerator(value, len(row_ids)) for value in scan.local_p
    ]
    global_numerator = _finite_rank_numerator(scan.global_p, len(row_ids))
    expected_global = {
        "exceedances_including_observation": global_numerator,
        "denominator": len(row_ids),
        "fraction": f"{global_numerator}/{len(row_ids)}",
        "reduced_fraction": str(scan.global_p),
    }
    if (
        result.get("global_finite_rank") != expected_global
        or result.get("local_finite_rank_fractions")
        != [str(value) for value in scan.local_p]
        or result.get("local_finite_rank_numerators") != local_numerators
        or result.get("observed_mes_feature_vector")
        != [float(value) for value in rows[0]]
    ):
        raise PlanckMesMorphologyError("MES finite-rank replay drifted")
    if (
        result.get("generic_benchmark_control") != GENERIC_BENCHMARK_CONTROL
        or result.get("owner") != "OBSSTAT"
        or result.get("artifact_mode") != "observed_diagnostic"
        or result.get("claim_tier") != "diagnostic_only"
        or result.get("claim_level") != "C2"
        or result.get("public_use") is not False
        or result.get("self_anchor_shared_data_dependence") is not True
        or result.get("self_anchor_independent_information_gain") is not False
        or result.get("mes_operator_identity") != MES_OPERATOR_IDENTITY
        or metadata.get("mes_operator_identity") != MES_OPERATOR_IDENTITY
        or result.get("directional_moment_state")
        != "BLOCKED_DIRECTIONAL_SUPPORT"
        or result.get("local_global_response")
        != "SINGLE_SHELL_LOCAL_GLOBAL_NONIDENTIFIED"
        or result.get("family_identification_gate") != "BLOCKED_PRE_NATIVE_ATLAS"
    ):
        raise PlanckMesMorphologyError("MES claim boundary drifted")
    projection_identity = _canonical_hash(
        _result_scientific_projection(result),
        role="pr327_planck_mes_morphology_scientific_projection",
    )
    if metadata.get("scientific_projection_sha256") != projection_identity:
        raise PlanckMesMorphologyError("MES scientific projection identity drifted")
    return {
        "format": "PLANCK_PR327_MES_MORPHOLOGY_REPLAY_V1",
        "replay_status": "PASS_EXACT_301_ROW_MES_MORPHOLOGY",
        "package_sha256": metadata["package_sha256"],
        "metadata_sha256": _sha256_file(metadata_path),
        "result_sha256": metadata["result_sha256"],
        "scientific_projection_sha256": projection_identity,
        "source_feature_package_identity": metadata[
            "source_feature_package_identity"
        ],
        "mes_operator_identity": MES_OPERATOR_IDENTITY,
        "mes_feature_matrix_identity": feature_matrix_identity,
        "pooled_covariance_identity": covariance_diagnostic["identity"],
        "global_rank_fraction": expected_global["fraction"],
        "global_rank_reduced_fraction": expected_global["reduced_fraction"],
        "directional_moment_state": "BLOCKED_DIRECTIONAL_SUPPORT",
        "local_global_response": "SINGLE_SHELL_LOCAL_GLOBAL_NONIDENTIFIED",
        "generic_control_rank_fraction": "133/301",
        "raw_maps_reopened": False,
    }


def run_planck_mes_morphology_analysis(
    *,
    feature_package_path: Path,
    feature_metadata_path: Path,
    output_dir: Path,
    residual_dipole_attribution: ResidualDipoleAttribution | None,
) -> dict[str, object]:
    """Execute and export the frozen exact-301-row Planck MES morphology lane."""

    if not isinstance(residual_dipole_attribution, ResidualDipoleAttribution):
        raise PlanckMesMorphologyError("BLOCKED_MES_ATTRIBUTION")
    output = Path(output_dir)
    if output.exists():
        raise PlanckMesMorphologyError("MES output directory must not already exist")
    package_path = Path(feature_package_path)
    metadata_path = Path(feature_metadata_path)
    try:
        source_replay = replay_pr315_feature_package(
            package_path=package_path, metadata_path=metadata_path
        )
    except (OSError, PlanckWorkerError) as exc:
        raise PlanckMesMorphologyError("PR-315 source replay failed") from exc
    source_metadata = _strict_json(metadata_path, label="PR-315 feature metadata")
    (
        source_matrix,
        row_ids,
        feature_ids,
        feature_units,
        tails,
        source_covariance,
    ) = _load_feature_pool(package_path)
    if (
        feature_ids != SOURCE_FEATURE_IDS
        or feature_units != SOURCE_FEATURE_UNITS
        or tails != ("two-sided",) * len(SOURCE_FEATURE_IDS)
        or row_ids[0] != OBSERVED_ROW_ID
    ):
        raise PlanckMesMorphologyError("PR-315 source schema drifted")
    source_covariance_identity = numeric_array_content_identity(
        source_covariance, role="PR315_EXACT_300_NULL_COVARIANCE"
    )
    rows, states = build_planck_mes_morphology_rows(
        row_ids=row_ids,
        feature_matrix=source_matrix,
        feature_ids=feature_ids,
        feature_units=feature_units,
        residual_dipole_attribution=residual_dipole_attribution,
        source_identity=str(source_replay["feature_package_sha256"]),
        covariance_identity=source_covariance_identity,
        operator_identity=str(source_replay["operator_identity_sha256"]),
    )
    anchor_payload = mes_row_anchor_pool_payload(states)
    anchor_identities = tuple(state.row_content_identity for state in states)
    anchor_binding_identity = _anchor_binding_identity(
        row_ids=row_ids,
        row_content_identities=anchor_identities,
        source_identity=str(source_replay["feature_package_sha256"]),
        source_covariance_identity=source_covariance_identity,
        source_operator_identity=str(source_replay["operator_identity_sha256"]),
    )
    feature_matrix_identity = numeric_array_content_identity(
        rows, role="PR327_ORDERED_301_ROW_MES_MORPHOLOGY_FEATURE_MATRIX"
    )
    covariance, covariance_diagnostic = _pooled_covariance(rows, row_ids)
    scan = observation_inclusive_max_scan(rows, MES_TAILS, observation_index=0)
    equivariance = _mes_equivariance_receipt(
        rows=rows, row_ids=row_ids, covariance=covariance
    )
    generic_control = _validate_generic_control()
    generation_state = _git_generation_state()

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=f".{output.name}.", dir=output.parent
    ) as temporary:
        temporary_path = Path(temporary)
        mes_package_path = temporary_path / MES_PACKAGE_FILENAME
        np.savez_compressed(
            mes_package_path,
            feature_rows=rows,
            pooled_covariance=covariance,
            row_ids=np.asarray(row_ids),
            feature_ids=np.asarray(MES_FEATURE_IDS),
            feature_units=np.asarray(MES_FEATURE_UNITS),
            feature_roles=np.asarray(MES_FEATURE_ROLES),
            tails=np.asarray(MES_TAILS),
            anchor_row_content_identities=np.asarray(anchor_identities),
        )
        package_identity = _sha256_file(mes_package_path)
        result = _result_payload(
            source_replay=source_replay,
            source_metadata=source_metadata,
            rows=rows,
            row_ids=row_ids,
            scan=scan,
            covariance_diagnostic=covariance_diagnostic,
            feature_matrix_identity=feature_matrix_identity,
            anchor_binding_identity=anchor_binding_identity,
            package_identity=package_identity,
            equivariance_receipt=equivariance,
            generic_control=generic_control,
            generation_state=generation_state,
        )
        result_path = temporary_path / MES_RESULT_FILENAME
        _write_json(result_path, result)
        result_identity = _sha256_file(result_path)
        projection_identity = _canonical_hash(
            _result_scientific_projection(result),
            role="pr327_planck_mes_morphology_scientific_projection",
        )
        metadata = {
            "format": "PLANCK_PR327_MES_MORPHOLOGY_PACKAGE_V1",
            "owner": "OBSSTAT",
            "scope": result["scope"],
            "artifact_mode": "claim_bearing_frozen_observed_diagnostic",
            "claim_tier": "diagnostic_only",
            "package_filename": MES_PACKAGE_FILENAME,
            "package_byte_size": mes_package_path.stat().st_size,
            "package_sha256": package_identity,
            "result_filename": MES_RESULT_FILENAME,
            "result_sha256": result_identity,
            "row_count": 301,
            "null_count": 300,
            "feature_ids": list(MES_FEATURE_IDS),
            "feature_units": list(MES_FEATURE_UNITS),
            "feature_roles": list(MES_FEATURE_ROLES),
            "tails": list(MES_TAILS),
            "operator_spec": json.loads(json.dumps(MES_OPERATOR_SPEC)),
            "mes_operator_identity": MES_OPERATOR_IDENTITY,
            "mes_feature_matrix_identity": feature_matrix_identity,
            "pooled_covariance_identity": covariance_diagnostic["identity"],
            "source_feature_package_identity": source_replay[
                "feature_package_sha256"
            ],
            "source_feature_projection_identity": source_replay[
                "scientific_projection_sha256"
            ],
            "source_feature_metadata_identity": source_replay[
                "feature_metadata_sha256"
            ],
            "source_covariance_identity": source_covariance_identity,
            "source_operator_identity": source_replay["operator_identity_sha256"],
            "source_anchor_pool_identity": anchor_payload["pool_content_identity"],
            "source_anchor_binding_identity": anchor_binding_identity,
            "scientific_projection_sha256": projection_identity,
            "null_ordered_row_ids_sha256": source_metadata.get(
                "null_ordered_row_ids_sha256"
            ),
            "raw_input_manifest_sha256": source_metadata.get(
                "raw_input_manifest_sha256"
            ),
            "transfer_source": source_metadata.get("transfer_source"),
            "sky_support_status": source_metadata.get("sky_support_status"),
            "null_mock_status": source_metadata.get("null_mock_status"),
            "directional_moment_state": "BLOCKED_DIRECTIONAL_SUPPORT",
            "local_global_response": "SINGLE_SHELL_LOCAL_GLOBAL_NONIDENTIFIED",
            "family_identification_gate": "BLOCKED_PRE_NATIVE_ATLAS",
            "generic_control_preserved": True,
            "generating_procedure": result["generating_procedure"],
            "generating_command": result["generating_command"],
            **generation_state,
        }
        _write_json(temporary_path / MES_METADATA_FILENAME, metadata)
        replay = replay_planck_mes_morphology_package(output_dir=temporary_path)
        _write_json(temporary_path / MES_REPLAY_FILENAME, replay)
        temporary_path.rename(output)
    return {"metadata": metadata, "result": result, "replay": replay}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-package", type=Path, required=True)
    parser.add_argument("--feature-metadata", type=Path, required=True)
    outputs = parser.add_mutually_exclusive_group(required=True)
    outputs.add_argument(
        "--output",
        type=Path,
        help="write only the prerequisite PR-325 row-anchor JSON",
    )
    outputs.add_argument(
        "--output-dir",
        type=Path,
        help="write the complete PR-327 exact-301-row portable package",
    )
    parser.add_argument(
        "--residual-dipole-attribution",
        choices=[value.value for value in ResidualDipoleAttribution],
        required=True,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    attribution = ResidualDipoleAttribution(
        arguments.residual_dipole_attribution
    )
    if arguments.output_dir is not None:
        run_planck_mes_morphology_analysis(
            feature_package_path=arguments.feature_package,
            feature_metadata_path=arguments.feature_metadata,
            output_dir=arguments.output_dir,
            residual_dipole_attribution=attribution,
        )
    else:
        run_planck_mes_row_anchors(
            feature_package_path=arguments.feature_package,
            feature_metadata_path=arguments.feature_metadata,
            output_path=arguments.output,
            residual_dipole_attribution=attribution,
        )
    return 0


__all__ = [
    "MES_FEATURE_IDS",
    "MES_FEATURE_ROLES",
    "MES_FEATURE_UNITS",
    "MES_METADATA_FILENAME",
    "MES_OPERATOR_IDENTITY",
    "MES_OPERATOR_SPEC",
    "MES_PACKAGE_FILENAME",
    "MES_REPLAY_FILENAME",
    "MES_RESULT_FILENAME",
    "MES_TAILS",
    "MesRowAnchorError",
    "OBSERVED_ROW_ID",
    "PlanckMesMorphologyError",
    "ResidualDipoleAttribution",
    "build_planck_mes_morphology_rows",
    "build_mes_row_anchor_pool",
    "main",
    "mes_row_anchor_pool_payload",
    "numeric_array_content_identity",
    "observation_inclusive_max_scan",
    "replay_planck_mes_morphology_package",
    "run_planck_mes_morphology_analysis",
    "run_planck_mes_row_anchors",
]


if __name__ == "__main__":
    raise SystemExit(main())
