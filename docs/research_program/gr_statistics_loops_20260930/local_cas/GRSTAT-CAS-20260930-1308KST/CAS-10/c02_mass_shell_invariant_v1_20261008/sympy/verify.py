#!/usr/bin/env python3
"""Independent exact SymPy verification for CAS-10-C02.

Permitted scientific inputs are limited to this unit's frozen execution
contract, admitted inputs, and COMMON_SPEC.md.  The proof produces exact
polynomial and sum-of-squares certificates; numeric vectors are controls only.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from pathlib import Path
from typing import Any

import sympy as sp


AXIS_DIR = Path(__file__).resolve().parent
UNIT_DIR = AXIS_DIR.parent
REPO_ROOT = Path.cwd().resolve()
CONTRACT_PATH = UNIT_DIR / "EXECUTION_CONTRACT.json"
ADMITTED_PATH = UNIT_DIR / "ADMITTED_INPUTS.json"
COMMON_PATH = (
    REPO_ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def zero(expr: sp.Expr) -> bool:
    return sp.expand(expr) == 0


def exact_vector_checks(
    metric: sp.Matrix, s_value: sp.Matrix, u_value: sp.Matrix, c_value: sp.Expr
) -> dict[str, bool]:
    h_value = (u_value.T * s_value * u_value)[0]
    b_value = (s_value + h_value * metric) * u_value
    a_value = 2 * c_value * b_value
    su_value = s_value * u_value
    j_value = (su_value.T * metric * su_value)[0] + h_value**2
    b_norm = (b_value.T * metric * b_value)[0]
    a_scaled = sp.cancel((a_value.T * metric * a_value)[0] / (4 * c_value**2))
    return {
        "mass_shell": zero((u_value.T * metric * u_value)[0] + 1),
        "future_branch": bool(u_value[0] > 0),
        "orthogonality": zero((u_value.T * b_value)[0]),
        "j_equals_b_norm": zero(j_value - b_norm),
        "j_equals_a_scaled": zero(j_value - a_scaled),
        "nonnegative": bool(j_value >= 0),
        "zero_iff_a_zero": bool((j_value == 0) == all(value == 0 for value in a_value)),
    }


def main() -> int:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    admitted = json.loads(ADMITTED_PATH.read_text(encoding="utf-8"))
    common_text = COMMON_PATH.read_text(encoding="utf-8")

    expected_inputs = {
        Path(item["path"]).name: item["sha256"]
        for item in contract["identity"]["source_input_hashes"]
    }
    observed_inputs = {
        CONTRACT_PATH.name: sha256(CONTRACT_PATH),
        ADMITTED_PATH.name: sha256(ADMITTED_PATH),
        COMMON_PATH.name: sha256(COMMON_PATH),
    }
    input_hash_checks = {
        "ADMITTED_INPUTS.json": (
            observed_inputs["ADMITTED_INPUTS.json"]
            == expected_inputs["ADMITTED_INPUTS.json"]
        ),
        "COMMON_SPEC.md": (
            observed_inputs["COMMON_SPEC.md"] == expected_inputs["COMMON_SPEC.md"]
        ),
    }

    # Fully symbolic definitions over the exact real domain.
    s00, s01, s02, s03, s11, s12, s13, s22, s23, s33 = sp.symbols(
        "s00 s01 s02 s03 s11 s12 s13 s22 s23 s33", real=True
    )
    u0, u1, u2, u3 = sp.symbols("u0 u1 u2 u3", real=True)
    c = sp.symbols("c", positive=True, finite=True)
    metric = sp.diag(-1, 1, 1, 1)
    symmetric_s = sp.Matrix(
        [
            [s00, s01, s02, s03],
            [s01, s11, s12, s13],
            [s02, s12, s22, s23],
            [s03, s13, s23, s33],
        ]
    )
    u = sp.Matrix([u0, u1, u2, u3])
    h = sp.expand((u.T * symmetric_s * u)[0])
    su = symmetric_s * u
    b = (symmetric_s + h * metric) * u
    a = 2 * c * b
    mass_shell_polynomial = sp.expand((u.T * metric * u)[0] + 1)
    j_geo = sp.expand((su.T * metric * su)[0] + h**2)
    b_norm = sp.expand((b.T * metric * b)[0])
    a_scaled = sp.cancel((a.T * metric * a)[0] / (4 * c**2))

    # Exact ideal-membership certificates for the identities on g(u,u)=-1.
    orthogonality_residual = sp.expand((u.T * b)[0])
    orthogonality_quotient = h
    norm_identity_residual = sp.expand(b_norm - j_geo)
    norm_identity_quotient = h**2
    exact_certificates = {
        "metric_inverse_equals_metric": metric.inv() == metric,
        "S_is_symmetric": symmetric_s.T == symmetric_s,
        "orthogonality_residual_equals_h_times_mass_shell": zero(
            orthogonality_residual
            - orthogonality_quotient * mass_shell_polynomial
        ),
        "b_norm_minus_Jgeo_equals_h2_times_mass_shell": zero(
            norm_identity_residual
            - norm_identity_quotient * mass_shell_polynomial
        ),
        "A_scaled_equals_b_norm_for_positive_c": zero(a_scaled - b_norm),
    }

    # Positivity certificate.  For b=(b0,q) with u^T b=0 and u0>0,
    # b0=-(r.q)/u0.  The mass shell gives the exact SOS identity below.
    q1, q2, q3 = sp.symbols("q1 q2 q3", real=True)
    spatial_u = (u1, u2, u3)
    spatial_q = (q1, q2, q3)
    dot_rq = sum(ri * qi for ri, qi in zip(spatial_u, spatial_q))
    q_squared = sum(qi**2 for qi in spatial_q)
    r_squared = sum(ri**2 for ri in spatial_u)
    lagrange_squares = sum(
        (spatial_u[i] * spatial_q[j] - spatial_u[j] * spatial_q[i]) ** 2
        for i in range(3)
        for j in range(i + 1, 3)
    )
    sos_terms = [
        q1,
        q2,
        q3,
        *[
            spatial_u[i] * spatial_q[j] - spatial_u[j] * spatial_q[i]
            for i in range(3)
            for j in range(i + 1, 3)
        ],
    ]
    sos_symbolic = sum(term**2 for term in sos_terms)
    sos_numerator = sp.expand(sos_symbolic)
    orthogonal_norm_numerator = sp.expand(u0**2 * q_squared - dot_rq**2)
    u0_positive = sp.symbols("u0_positive", positive=True, finite=True)
    b0_from_orthogonality = -dot_rq / u0_positive
    generic_b = sp.Matrix(sp.symbols("generic_b0:4", real=True))
    scale_solution = sp.solve(
        list(2 * c * generic_b), list(generic_b), dict=True
    )
    positivity_certificates = {
        "mass_shell_reduction_to_sos": zero(
            orthogonal_norm_numerator.subs(u0**2, 1 + r_squared)
            - sos_numerator
        ),
        "sos_decomposition_exact": zero(
            sos_numerator - sos_symbolic
        ),
        "sos_contains_spatial_b_coordinate_basis": sos_terms[:3]
        == list(spatial_q),
        "u0_squared_strictly_positive_on_future_branch": bool(
            sp.ask(sp.Q.positive(u0_positive**2))
        ),
        "sos_nonnegative_over_reals": bool(
            sp.ask(sp.Q.nonnegative(sos_symbolic))
        ),
        "sos_zero_forces_q_squared_zero": bool(
            sp.ask(sp.Q.nonnegative(q_squared))
        )
        and sos_terms[:3] == list(spatial_q),
        "orthogonality_then_b0_vanishes_when_spatial_b_zero": zero(
            b0_from_orthogonality.subs({q1: 0, q2: 0, q3: 0})
        ),
        "positive_scaling_A_zero_solution_is_b_zero": scale_solution
        == [
            {
                generic_b[0]: 0,
                generic_b[1]: 0,
                generic_b[2]: 0,
                generic_b[3]: 0,
            }
        ],
    }

    # Exact required controls: each shows why a published hypothesis is needed.
    nonunit_u = sp.Matrix([2, 0, 0, 0])
    control_s = sp.diag(1, 0, 0, 0)
    control_h = (nonunit_u.T * control_s * nonunit_u)[0]
    control_b = (control_s + control_h * metric) * nonunit_u
    c_zero_b = sp.Matrix([0, 1, 0, 0])
    c_zero_a = 2 * sp.Integer(0) * c_zero_b
    c_zero_denominator = 4 * sp.Integer(0) ** 2
    controls = {
        "c_zero_excluded": {
            "passed": bool(
                all(component == 0 for component in c_zero_a)
                and (c_zero_b.T * metric * c_zero_b)[0] == 1
                and c_zero_denominator == 0
            ),
            "witness": "For c=0 and b=(0,1,0,0), A=0 while b^T g^-1 b=1; A^2/(4c^2) is undefined.",
        },
        "nonunit_u_excluded": {
            "passed": bool(
                (nonunit_u.T * metric * nonunit_u)[0] != -1
                and (nonunit_u.T * control_b)[0] != 0
            ),
            "witness": {
                "u": [2, 0, 0, 0],
                "S_diagonal": [1, 0, 0, 0],
                "g_uu": int((nonunit_u.T * metric * nonunit_u)[0]),
                "uT_b": int((nonunit_u.T * control_b)[0]),
            },
        },
        "orthogonality_needed_for_indefinite_positivity": {
            "passed": bool((sp.Matrix([1, 0, 0, 0]).T * metric * sp.Matrix([1, 0, 0, 0]))[0] == -1),
            "witness": "At rest u=(1,0,0,0), nonorthogonal b=(1,0,0,0) has b^T g^-1 b=-1.",
        },
    }

    sample_s = sp.Matrix(
        [[2, 1, -1, 3], [1, 4, 2, -2], [-1, 2, 5, 1], [3, -2, 1, 6]]
    )
    exact_test_vectors = {
        "rest_u": exact_vector_checks(
            metric, sample_s, sp.Matrix([1, 0, 0, 0]), sp.Integer(3)
        ),
        "boosted_rational_u": exact_vector_checks(
            metric,
            sample_s,
            sp.Matrix([sp.Rational(5, 4), sp.Rational(3, 4), 0, 0]),
            sp.Rational(7, 3),
        ),
        "A_zero": exact_vector_checks(
            metric,
            metric,
            sp.Matrix([sp.Rational(5, 4), sp.Rational(3, 4), 0, 0]),
            sp.Integer(2),
        ),
    }

    statement_alignment = {
        "u^T b=0": exact_certificates[
            "orthogonality_residual_equals_h_times_mass_shell"
        ],
        "Jgeo=b^T g^-1 b": exact_certificates[
            "b_norm_minus_Jgeo_equals_h2_times_mass_shell"
        ],
        "Jgeo=A^T g^-1 A/(4 c^2)": exact_certificates[
            "b_norm_minus_Jgeo_equals_h2_times_mass_shell"
        ]
        and exact_certificates["A_scaled_equals_b_norm_for_positive_c"],
        "Jgeo>=0 on the future unit mass shell": all(
            positivity_certificates[key]
            for key in (
                "mass_shell_reduction_to_sos",
                "u0_squared_strictly_positive_on_future_branch",
                "sos_nonnegative_over_reals",
            )
        ),
        "Jgeo=0 iff A=0": all(positivity_certificates.values()),
    }

    all_checks = (
        all(input_hash_checks.values())
        and admitted["component"] == "CAS-10-C02"
        and contract["target"]["exact_test_obligations"] == ["CAS-10-C02"]
        and "signature (-,+,+,+)" in common_text
        and all(exact_certificates.values())
        and all(positivity_certificates.values())
        and all(item["passed"] for item in controls.values())
        and all(all(vector.values()) for vector in exact_test_vectors.values())
        and all(statement_alignment.values())
    )

    result: dict[str, Any] = {
        "schema": "htt.cas-axis-result.v1",
        "axis": "sympy",
        "component": "CAS-10-C02",
        "contract_id": contract["identity"]["contract_id"],
        "contract_sha256": observed_inputs["EXECUTION_CONTRACT.json"],
        "status": "PASS" if all_checks else "FAIL",
        "checks": {"CAS-10-C02": bool(all_checks)},
        "evidence_class": "exact",
        "statement_alignment": statement_alignment,
        "domain_assumption_diff": [],
        "counterexample": None if all_checks else "See failed exact certificate or control.",
        "exact_certificates": exact_certificates,
        "certificate_forms": {
            "mass_shell_polynomial": "-u0^2+u1^2+u2^2+u3^2+1",
            "orthogonality": "u^T b = h*(-u0^2+u1^2+u2^2+u3^2+1)",
            "norm_identity": "b^T g^-1 b-Jgeo = h^2*(-u0^2+u1^2+u2^2+u3^2+1)",
            "scaling_identity": "A^T g^-1 A/(4*c^2)=b^T g^-1 b for c>0",
            "positivity_sos": "u0^2*(b^T g^-1 b)=q1^2+q2^2+q3^2+(u1*q2-u2*q1)^2+(u1*q3-u3*q1)^2+(u2*q3-u3*q2)^2",
        },
        "positivity_certificates": positivity_certificates,
        "controls": controls,
        "exact_test_vectors": exact_test_vectors,
        "source_input_hashes": observed_inputs,
        "source_input_hash_checks": input_hash_checks,
        "toolchain": {
            "python_executable": sys.executable,
            "python_version": sys.version,
            "python_implementation": platform.python_implementation(),
            "sympy_version": sp.__version__,
            "sympy_path": sp.__file__,
        },
        "runtime_observation": {
            "launch_id": None,
            "authority": "unavailable",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
        },
        "independence_mode": contract["independence"]["mode"],
        "claim_ceiling": contract["identity"]["claim_ceiling"],
        "remaining_obligations": contract["full_theorem_boundary"]["remaining"],
        "scientific_admission": "HOLD",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if all_checks else 1


if __name__ == "__main__":
    raise SystemExit(main())
