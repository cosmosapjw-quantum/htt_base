#!/usr/bin/env python3
"""Print the WU-011 full-sky HEALPix resolution characterization."""

from __future__ import annotations

import json
import numpy as np

from obsstat.processed_boost_evidence import _build_case


def main() -> None:
    cases = []
    built = {}
    for nside, processing_lmax in ((8, 7), (16, 7), (32, 7), (32, 12)):
        case_id = f"FULL_N{nside}_L{processing_lmax}_IDENTITY"
        case, _ = _build_case(
            case_id,
            nside=nside,
            processing_lmax=processing_lmax,
            mask_kind="FULL",
            transfer_kind="IDENTITY",
        )
        built[(nside, processing_lmax)] = case
        cases.append(case.scalar_record())
    drifts = {}
    for left, right in (((8, 7), (16, 7)), ((16, 7), (32, 7)), ((32, 7), (32, 12))):
        a = built[left].jacobian.metric_whitened_stacked_matrix
        b = built[right].jacobian.metric_whitened_stacked_matrix
        drifts[f"N{left[0]}L{left[1]}__N{right[0]}L{right[1]}"] = float(
            np.linalg.norm(a - b) / np.linalg.norm(b)
        )
    print(
        "TASK7A_FULLSKY_RESOLUTION_CHARACTERIZATION="
        + json.dumps({"cases": cases, "relative_matrix_drifts": drifts}, sort_keys=True)
    )


if __name__ == "__main__":
    main()
