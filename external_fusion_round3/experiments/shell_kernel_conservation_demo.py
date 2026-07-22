#!/usr/bin/env python3
"""Reference shell-kernel conservation and refinement experiment.

This deliberately uses a transparent analytic FLRW-like kernel rather than a
Boltzmann output.  PR-253 replaces the sampled kernel with CAMB/CLASS/readable
line-of-sight terms while retaining the conservation gate.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.integrate import quad

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.transfer import (  # noqa: E402
    integrate_kernel_on_edges,
    refinement_difference,
    shell_sum_relative_error,
)


def kernel(z: np.ndarray) -> np.ndarray:
    z = np.asarray(z, dtype=float)
    # Smooth complex source with a shallow late component and a recombination-like bump.
    return (
        np.exp(-z / 1.8) * (1.0 + 0.15j * z)
        + 0.035 * np.exp(-0.5 * ((z - 8.0) / 0.8) ** 2) * np.exp(0.2j * z)
    )


def main() -> int:
    z = np.linspace(0.0, 12.0, 12001)
    k = kernel(z)
    coarse_edges = np.array([0, 0.1, 0.3, 0.7, 1.5, 3, 6, 9, 12], dtype=float)
    fine_edges = np.unique(np.concatenate([coarse_edges, (coarse_edges[:-1] + coarse_edges[1:]) / 2]))
    coarse = integrate_kernel_on_edges(z, k, coarse_edges, ell=2, source_name="analytic_reference", convention="demo_v1")
    fine = integrate_kernel_on_edges(z, k, fine_edges, ell=2, source_name="analytic_reference", convention="demo_v1")
    real = quad(lambda x: float(kernel(np.array([x]))[0].real), 0, 12, epsabs=1e-12)[0]
    imag = quad(lambda x: float(kernel(np.array([x]))[0].imag), 0, 12, epsabs=1e-12)[0]
    total = real + 1j * imag
    err = shell_sum_relative_error(fine, total)
    refine = refinement_difference(coarse, fine)
    ok = err < 2e-7 and refine < 2e-7
    print(json.dumps({
        "status": "PASS" if ok else "FAIL",
        "purpose": "reference conservation gate, not physical CMB transfer",
        "fine_shell_sum_relative_error": err,
        "coarse_fine_total_relative_difference": refine,
        "coarse_shells": len(coarse.complex_response),
        "fine_shells": len(fine.complex_response),
        "total_real": total.real,
        "total_imag": total.imag,
    }, indent=2))
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
