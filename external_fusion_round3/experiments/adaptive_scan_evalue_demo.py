#!/usr/bin/env python3
from __future__ import annotations

import json
import numpy as np


def main() -> int:
    rng = np.random.default_rng(20260722)
    nrep, steps, lam = 30000, 80, 0.18
    increments = np.exp(lam * rng.normal(size=(nrep, steps)) - 0.5 * lam**2)
    process = np.cumprod(increments, axis=1)
    beta = 0.05
    crossing = float(np.mean(np.max(process, axis=1) >= 1.0 / beta))
    status = "PASS" if crossing <= beta + 0.005 else "FAIL"
    print(json.dumps({"status": status, "nrep": nrep, "steps": steps, "beta": beta, "crossing_rate": crossing, "ville_bound": beta}, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
