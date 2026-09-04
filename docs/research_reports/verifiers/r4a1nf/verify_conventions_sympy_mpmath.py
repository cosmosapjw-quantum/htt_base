#!/usr/bin/env python3
"""Independent SymPy/mpmath checks for Report A R4A1NF conventions.

This verifier checks algebraic closures only. It does not validate observational
inputs, finite-HEALPix rank, or the full Q/O orbit implementation.
"""

from __future__ import annotations

import json

import mpmath as mp
import sympy as sp


E, c, beta2, lam = sp.symbols("E c beta2 lambda_reg", positive=True)
q = sp.symbols("q", nonnegative=True)

# Observer decomposition: u.u=-1, u.e=0, e.e=1.
photon_norm = sp.simplify((E / c) ** 2 * (-1 + 2 * 0 + 1))
measured_energy = sp.simplify(-c * (E / c) * (-1 + 0) - E)

# Boost normalization after gamma^2=(1-beta^2)^(-1).
boost_residual = sp.simplify((1 / (1 - beta2)) * (-1 + beta2) + 1)

# q>=0 and lambda_reg>0 imply q+lambda_reg^2>0.
positive_regularisation = sp.ask(sp.Q.positive(q + lam**2))

mp.mp.dps = 80
b = mp.mpf("0.37")
gamma = 1 / mp.sqrt(1 - b * b)
boost_numeric_residual = gamma * gamma * (-1 + b * b) + 1

receipt = {
    "photon_norm_residual": str(photon_norm),
    "measured_energy_residual": str(measured_energy),
    "boost_residual": str(boost_residual),
    "positive_regularisation_proved_by_assumptions": bool(positive_regularisation),
    "mpmath_digits": mp.mp.dps,
    "boost_numeric_residual": mp.nstr(boost_numeric_residual, 20),
}

assert photon_norm == 0
assert measured_energy == 0
assert boost_residual == 0
assert positive_regularisation is True
assert abs(boost_numeric_residual) < mp.mpf("1e-70")

print(json.dumps(receipt, indent=2))
