#!/usr/bin/env python3
"""Execute a bounded exploratory PR-315 joint cut-sky observation/null path."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Mapping, Sequence

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "htt", ROOT / "htt/src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from obsstat.planck_joint_cutsky import (  # noqa: E402
    JointCutSkyLowEllFit,
    fit_joint_cutsky_lowell,
)
from obsstat.planck_post275_lane import (  # noqa: E402
    PlanckLaneContractError,
    observation_inclusive_max_scan,
)
from obsstat.planck_pr3_operator import (  # noqa: E402
    JOINT_FEATURE_IDS,
    extract_component_features,
)
from scripts.observed_runs.run_planck_pr3 import (  # noqa: E402
    _synthetic_context,
    _synthetic_pair,
)


FORMAT = "PLANCK_PR315_JOINT_CUTSKY_SYNTHETIC_V1"


class JointSyntheticRunError(RuntimeError):
    """Raised when the bounded exploratory observation/null path drifts."""


def _array_digest(value: np.ndarray, *, role: str) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(array.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(array.shape).encode("ascii") + b"\0")
    digest.update(memoryview(array).cast("B"))
    return "sha256:" + digest.hexdigest()


def _process_component(
    pixel_map: np.ndarray,
    *,
    component: str,
    context: Mapping[str, object],
) -> tuple[np.ndarray, JointCutSkyLowEllFit]:
    fit = fit_joint_cutsky_lowell(
        pixel_map,
        common_mask=context["common_mask"],
        source_beam=context["source_beams"][component],
        source_pixel_window=context["source_pixels"][component],
        target_beam=context["target_beam"],
        target_pixel_window=context["target_pixel"],
    )
    return extract_component_features(fit.retained_alm), fit


def _joint_row(
    seed: int,
    *,
    context: Mapping[str, object],
) -> tuple[np.ndarray, tuple[JointCutSkyLowEllFit, JointCutSkyLowEllFit]]:
    smica_map, commander_map = _synthetic_pair(seed, nside=int(context["nside"]))
    smica, smica_fit = _process_component(
        smica_map, component="SMICA", context=context
    )
    commander, commander_fit = _process_component(
        commander_map, component="Commander", context=context
    )
    return np.concatenate((smica, commander)), (smica_fit, commander_fit)


def build_exploratory_result(*, rows: int) -> dict[str, object]:
    if type(rows) is not int or not 2 <= rows <= 32:
        raise JointSyntheticRunError("rows must be an integer in [2,32]")
    context = _synthetic_context(nside=8)
    observed, observed_fits = _joint_row(30_700_000, context=context)
    null_rows: list[np.ndarray] = []
    all_fits = list(observed_fits)
    for ordinal in range(rows):
        row, fits = _joint_row(30_600_000 + ordinal, context=context)
        null_rows.append(row)
        all_fits.extend(fits)
    nulls = np.asarray(null_rows, dtype=float)
    if nulls.shape != (rows, len(JOINT_FEATURE_IDS)):
        raise JointSyntheticRunError("joint null feature shape drifted")

    mask_ids = {fit.mask_sha256 for fit in all_fits}
    normal_ids = {fit.normal_matrix_sha256 for fit in all_fits}
    basis_orders = {fit.basis_order for fit in all_fits}
    if len(mask_ids) != 1 or len(normal_ids) != 1 or len(basis_orders) != 1:
        raise JointSyntheticRunError(
            "observation and null rows did not share one joint operator"
        )

    pool = np.vstack((observed, nulls))
    scan = observation_inclusive_max_scan(
        pool,
        ("two-sided",) * pool.shape[1],
        observation_index=0,
    )
    return {
        "format": FORMAT,
        "status": "EXPLORATORY_NONAUTHORITATIVE",
        "operator_branch": "PR315_JOINT_CUTSKY",
        "row_count": rows,
        "feature_order": list(JOINT_FEATURE_IDS),
        "observation_feature_sha256": _array_digest(
            observed, role="pr315_joint_observation_features"
        ),
        "null_feature_matrix_sha256": _array_digest(
            nulls, role="pr315_joint_null_features"
        ),
        "finite_family_rank": str(scan.global_p),
        "resolution_floor": str(scan.resolution_floor),
        "mask_sha256": next(iter(mask_ids)),
        "normal_matrix_sha256": next(iter(normal_ids)),
        "maximum_condition_number": max(
            fit.condition_number for fit in all_fits
        ),
        "minimum_relative_singular_floor": min(
            fit.relative_singular_floor for fit in all_fits
        ),
        "observation_null_operator_identity": "PASS",
        "observed_data_executed": False,
        "scientific_result": None,
        "claim_boundary": (
            "synthetic implementation evidence only; no Planck observation, "
            "MES result, local/global identification, or family claim"
        ),
    }


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
        + "\n",
        encoding="ascii",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=8)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = build_exploratory_result(rows=args.rows)
        if args.output is None:
            print(json.dumps(payload, sort_keys=True, allow_nan=False))
        else:
            _write_json(args.output, payload)
        return 0
    except (JointSyntheticRunError, PlanckLaneContractError) as exc:
        print(f"BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
