#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.alm import random_real_alm, rotate_alm_zyz  # noqa: E402
from htt_ext.lowell.poles import pole_from_alm  # noqa: E402


def main() -> int:
    rng = np.random.default_rng(20260722)
    cases = []
    worst = 0.0
    for ell in (1, 2, 3, 4, 5):
        for i in range(20):
            a = random_real_alm(ell, rng)
            alpha, beta, gamma = rng.uniform(-np.pi, np.pi, size=3)
            p, _ = pole_from_alm(a, ell)
            ap = rotate_alm_zyz(a, ell, alpha, beta, gamma)
            pp, _ = pole_from_alm(ap, ell)
            r = Rotation.from_euler("ZYZ", [alpha, beta, gamma]).as_matrix()
            agreement = abs(float(np.dot(pp, r @ p)))
            err = 1.0 - agreement
            worst = max(worst, err)
            cases.append({"ell": ell, "case": i, "axis_agreement_absdot": agreement})
    ok = worst < 1e-9
    print(json.dumps({"status": "PASS" if ok else "FAIL", "worst_1_minus_absdot": worst, "n_cases": len(cases)}, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
