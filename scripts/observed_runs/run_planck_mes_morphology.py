#!/usr/bin/env python3
"""Build rowwise active MES anchors from the portable PR-324 feature pool.

The script is map-free and consumes only the corrected feature package.  It
does not import the quarantined legacy Planck MES implementation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
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
try:
    from scripts.observed_runs.run_planck_pr3 import replay_pr315_feature_package
except ModuleNotFoundError as exc:  # direct ``python scripts/...`` execution
    if exc.name not in {"scripts", "scripts.observed_runs"}:
        raise
    from run_planck_pr3 import replay_pr315_feature_package


OBSERVED_ROW_ID = "PLANCK-PR3-SMICA-OBSERVED"


def _load_feature_pool(
    package_path: Path,
) -> tuple[
    np.ndarray,
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
    except (KeyError, OSError, ValueError) as exc:
        raise MesRowAnchorError("PR-324 feature pool is unavailable") from exc
    if observed.ndim != 1 or nulls.ndim != 2 or nulls.shape[1:] != observed.shape:
        raise MesRowAnchorError("PR-324 feature pool row dimensions drifted")
    return (
        np.vstack((observed, nulls)),
        (OBSERVED_ROW_ID, *null_row_ids),
        feature_ids,
        feature_units,
        covariance,
    )


def _state_map(
    states: Sequence[MesRowAnchorState],
) -> dict[str, MesRowAnchorState]:
    return {state.row_id: state for state in states}


def _equivariance_receipt(
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
    matrix, row_ids, feature_ids, feature_units, covariance = _load_feature_pool(
        package_path
    )
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
            "equivariance_receipt": _equivariance_receipt(
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feature-package", type=Path, required=True)
    parser.add_argument("--feature-metadata", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--residual-dipole-attribution",
        choices=[value.value for value in ResidualDipoleAttribution],
        required=True,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    run_planck_mes_row_anchors(
        feature_package_path=arguments.feature_package,
        feature_metadata_path=arguments.feature_metadata,
        output_path=arguments.output,
        residual_dipole_attribution=ResidualDipoleAttribution(
            arguments.residual_dipole_attribution
        ),
    )
    return 0


__all__ = [
    "MesRowAnchorError",
    "ResidualDipoleAttribution",
    "build_mes_row_anchor_pool",
    "main",
    "mes_row_anchor_pool_payload",
    "numeric_array_content_identity",
    "run_planck_mes_row_anchors",
]


if __name__ == "__main__":
    raise SystemExit(main())
