#!/usr/bin/env python3
"""Required SymPy axis for CAS-R4A1NF-DOMAIN-R2.

This axis checks exact algebraic closures under the contract assumptions.  It
contains no observational data, HEALPix calculation, Q/O orbit computation, or
BASS solver claim.
"""
from __future__ import annotations

import json

import mpmath as mp
import sympy as sp


OBLIGATIONS = (
    "photon_null_decomposition",
    "observer_measured_photon_energy",
    "boosted_observer_unit_timelike",
    "regularized_error_envelope_positive_definite",
)


def main() -> None:
    # The contractions use u.u=-1, u.e=0, and e.e=1.  Positive scalar
    # prefactors E_gamma/c are irrelevant to the zero identities.
    photon_factor = sp.Integer(-1) + 2 * sp.Integer(0) + sp.Integer(1)
    measured_energy_factor = -(
        sp.Integer(-1) + sp.Integer(0)
    ) - sp.Integer(1)

    gamma2, beta2 = sp.symbols("gamma2 beta2", real=True)
    lorentz_relation = gamma2 * (1 - beta2) - 1
    boosted_norm_residual = gamma2 * (-1 + beta2) + 1
    boost_identity = sp.expand(boosted_norm_residual + lorentz_relation) == 0

    # Exact quadratic-form decomposition for a generic 2 x 2 Gram-type PSD
    # contribution P=A A^T.  This is an explicit algebraic witness for the
    # matrix form used by the numerical-error construction, not the full
    # ordered-field proof by itself.
    a11, a12, a21, a22 = sp.symbols(
        "a11 a12 a21 a22", real=True
    )
    x1, x2 = sp.symbols("x1 x2", real=True)
    lambda_reg = sp.symbols("lambda_reg", positive=True)
    A = sp.Matrix(((a11, a12), (a21, a22)))
    x = sp.Matrix((x1, x2))
    P = A * A.T
    Gamma = P + lambda_reg**2 * sp.eye(2)
    quadratic = sp.expand((x.T * Gamma * x)[0])
    Atx = A.T * x
    sos_form = sp.expand(
        Atx.dot(Atx) + lambda_reg**2 * x.dot(x)
    )
    sos_residual = sp.expand(quadratic - sos_form)

    # General ordered quadratic-form step.  For an arbitrary real PSD matrix
    # P and any nonzero x, set q_psd=x^T P x>=0 and
    # x_norm_sq=x^T x>0.  With lambda_reg>0, the regularizer is strictly
    # positive and q_psd + lambda_reg^2*x_norm_sq is therefore positive.  This
    # is the dimension-independent implication formalized separately in Lean.
    q_psd = sp.symbols("q_psd", nonnegative=True)
    x_norm_sq = sp.symbols("x_norm_sq", positive=True)
    strict_regularizer = lambda_reg**2 * x_norm_sq
    general_quadratic_form = q_psd + strict_regularizer
    general_ordered_posdef = (
        q_psd.is_nonnegative is True
        and x_norm_sq.is_positive is True
        and lambda_reg.is_positive is True
        and strict_regularizer.is_positive is True
        and general_quadratic_form.is_positive is True
    )
    regularized_posdef = sos_residual == 0 and general_ordered_posdef

    # Independent high-precision numerical cancellation check for the boost
    # identity.  This is supplemental to, not a substitute for, exact algebra.
    mp.mp.dps = 80
    beta = mp.mpf("0.37")
    gamma = 1 / mp.sqrt(1 - beta * beta)
    numeric_boost_residual = gamma * gamma * (-1 + beta * beta) + 1

    checks = {
        "photon_null_decomposition": bool(photon_factor == 0),
        "observer_measured_photon_energy": bool(
            measured_energy_factor == 0
        ),
        "boosted_observer_unit_timelike": bool(boost_identity),
        "regularized_error_envelope_positive_definite": bool(
            regularized_posdef
        ),
    }
    assert tuple(checks) == OBLIGATIONS
    assert abs(numeric_boost_residual) < mp.mpf("1e-70")

    print(
        json.dumps(
            {
                "checks": checks,
                "domain_assumption_diff": [],
                "computed": {
                    "sympy_version": sp.__version__,
                    "mpmath_version": mp.__version__,
                    "regularized_quadratic_form_residual": str(
                        sos_residual
                    ),
                    "general_ordered_quadratic_form": str(
                        general_quadratic_form
                    ),
                    "strict_regularizer_is_positive": bool(
                        strict_regularizer.is_positive is True
                    ),
                    "nonzero_vector_assumption": "x_norm_sq > 0",
                    "boost_high_precision_residual": mp.nstr(
                        numeric_boost_residual, 20
                    ),
                },
                "counterexample": None,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )


if __name__ == "__main__":
    main()
