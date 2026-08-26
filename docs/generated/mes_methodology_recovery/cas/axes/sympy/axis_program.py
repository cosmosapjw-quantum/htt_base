#!/usr/bin/env python3
"""Independent exact SymPy axis for CAS-PR323-MES-METHODOLOGY-CORE-001.

The program writes exactly one JSON document to stdout.  Its ``checks`` object
has exactly the obligations registered by the content-bound CAS contract, so it
can be executed directly by ``cas_gate.py run-adjudicate``.  No sibling-axis
artifact is read or imported.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sympy as sp


RUN_ID = "pr323-mes-theory-20260826"
ASSIGNMENT_ID = "PR323-CAS-SYMPY"
CONTEXT_VERSION = "e9b385d7fbc4f8e47c97c3b0c7edae4e522d9be4e025d9342e26ab24829e3019"
CONTRACT_ID = "CAS-PR323-MES-METHODOLOGY-CORE-001"
CONTRACT_RELATIVE_PATH = (
    "docs/generated/mes_methodology_recovery/cas/CAS_CONTRACT.json"
)
EXPECTED_CONTRACT_SHA256 = (
    "910fd4e002e4c5af1be441253e236b4ffa16f6a71815cf6618417b6b5d5b850c"
)
EXPECTED_SYMPY_VERSION = "1.14.0"

OBLIGATIONS = (
    "scalar_to_vector_no_go",
    "scalar_to_stf2_no_go",
    "directional_dipole_recovery",
    "directional_stf2_recovery",
    "eigenframe_slice_transverse_simple_spectrum",
    "local_global_fisher_factorization",
    "invertible_anchor_fisher_congruence",
    "finite_rank_formula_n1_100",
    "finite_rank_ties_conservative_n1_100",
    "zero_mean_antipodal_construction",
    "second_moment_antipodal_construction",
)

EXPECTED_SOURCE_HASHES = {
    "docs/codex_handoff/mes_methodology_recovery/RESEARCH_DECISION_LEDGER.yaml": (
        "e4d98b5907eb09a13c04658aeee3db23a3d0995a8378e5d4c3e627141ccc0b62"
    ),
    "docs/codex_handoff/mes_methodology_recovery/ADVERSARIAL_SCIENCE_AUDIT.md": (
        "6ac385bca9dfebbcbf32a746ef6b7c38022313053b4f0df2ab0f7c0c8f17324a"
    ),
    "docs/codex_handoff/mes_methodology_recovery/LOCAL_FORMALIZATION_TASKS.yaml": (
        "3868acaf3e065b484b3943ae69886916f322ae8184f83214c8454a1c7e15fe52"
    ),
    "wolfram/mes_methodology_recovery_proofs.wls": (
        "738666f3993471dd461b0f07e35783ac3b0604ee10dbe00ba0e2e4477d4b4930"
    ),
}

ASSUMPTIONS = [
    "All symbolic equalities are exact over the declared real or rational domains.",
    "The sphere measure is rotation invariant, antipodally symmetric, and has total area 4*pi.",
    "The directional reconstruction tensor is real, symmetric, and trace free.",
    "The fixed MES anchor U is positive; row-dependent self-anchors are excluded.",
    "The parameter normalizer D is invertible when rank invariance is inferred from congruence.",
    "Finite ranks include the observation and all m null rows.",
    "The antipodal construction assigns lambda_i/2 to each of +e_i and -e_i, with lambda_i >= 0 and sum(lambda_i)=1 for a probability measure.",
]

CONVENTIONS = {
    "rotation_action": "active right-handed Cartesian SO(3); O(3) no-go follows because SO(3) is a subgroup",
    "sphere_measure": "area(S2)=4*pi",
    "stf_projection": "n_<i n_j> = n_i*n_j - delta_ij/3",
    "mes_anchor": "fixed positive scale only",
    "local_global_ordering": "two depth profiles tensor three directional components",
    "metric_signature": "not used in this algebraic bundle; repository convention (-,+,+,+) is unchanged",
    "units": "dimensionless exact representation, moment, rank, and congruence identities",
}


def sha256_path(path: Path) -> str:
    """Return the hexadecimal SHA-256 digest of one regular file."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def exact_zero(value: sp.Expr) -> bool:
    return bool(sp.simplify(value) == 0)


def exact_zero_matrix(matrix: sp.MatrixBase) -> bool:
    return all(exact_zero(value) for value in matrix)


def sphere_moment(*indices: int) -> sp.Expr:
    """Exact full-sky Cartesian moments through degree four.

    Odd moments vanish by antipodal symmetry.  The degree-two and degree-four
    tensors are the normalized identities stated in the shared CAS contract;
    no numerical quadrature or conclusion-as-hypothesis is used.
    """

    degree = len(indices)
    delta = sp.KroneckerDelta
    if degree == 0:
        return 4 * sp.pi
    if degree % 2 == 1:
        return sp.Integer(0)
    if degree == 2:
        i, j = indices
        return sp.Rational(4, 3) * sp.pi * delta(i, j)
    if degree == 4:
        i, j, k, ell = indices
        return sp.Rational(4, 15) * sp.pi * (
            delta(i, j) * delta(k, ell)
            + delta(i, k) * delta(j, ell)
            + delta(i, ell) * delta(j, k)
        )
    raise ValueError(f"unsupported sphere-moment degree {degree}")


def derive_checks() -> tuple[dict[str, bool], dict[str, Any]]:
    """Execute the eleven independent exact obligations."""

    checks = {name: False for name in OBLIGATIONS}
    details: dict[str, Any] = {}

    # 1. The common fixed subspace of the standard SO(3) vector generators.
    jx = sp.Matrix([[0, 0, 0], [0, 0, -1], [0, 1, 0]])
    jy = sp.Matrix([[0, 0, 1], [0, 0, 0], [-1, 0, 0]])
    jz = sp.Matrix([[0, -1, 0], [1, 0, 0], [0, 0, 0]])
    generators = (jx, jy, jz)
    vector_system = sp.Matrix.vstack(*generators)
    vector_rank = vector_system.rank()
    vector_nullspace = vector_system.nullspace()
    checks["scalar_to_vector_no_go"] = (
        vector_rank == 3 and vector_nullspace == []
    )
    details["scalar_to_vector_no_go"] = {
        "method": "rank and nullspace of the vertically stacked infinitesimal SO(3) generators",
        "coefficient_matrix_shape": list(vector_system.shape),
        "rank": int(vector_rank),
        "nullity": len(vector_nullspace),
        "pass": checks["scalar_to_vector_no_go"],
    }

    # 2. The fixed subspace in the real symmetric trace-free rank-two sector.
    a, b, d, e, f = sp.symbols("a b d e f", real=True)
    tensor = sp.Matrix([[a, d, e], [d, b, f], [e, f, -a - b]])
    commutator_residuals = [
        value for generator in generators for value in generator * tensor - tensor * generator
    ]
    stf_system, stf_rhs = sp.linear_eq_to_matrix(
        commutator_residuals, (a, b, d, e, f)
    )
    stf_rank = stf_system.rank()
    stf_nullspace = stf_system.nullspace()
    checks["scalar_to_stf2_no_go"] = (
        exact_zero_matrix(stf_rhs)
        and stf_rank == 5
        and stf_nullspace == []
    )
    details["scalar_to_stf2_no_go"] = {
        "method": "commutator equations [J_i,T]=0 in five independent STF2 coordinates",
        "coefficient_matrix_shape": list(stf_system.shape),
        "rank": int(stf_rank),
        "nullity": len(stf_nullspace),
        "trace": sp.sstr(sp.trace(tensor)),
        "pass": checks["scalar_to_stf2_no_go"],
    }

    # 3-4. Full-sky directional reconstruction using explicit moment tensors.
    v1, v2, v3 = sp.symbols("v1 v2 v3", real=True)
    s11, s22, s12, s13, s23 = sp.symbols(
        "s11 s22 s12 s13 s23", real=True
    )
    vector = sp.Matrix([v1, v2, v3])
    stf = sp.Matrix(
        [[s11, s12, s13], [s12, s22, s23], [s13, s23, -s11 - s22]]
    )

    recovered_vector = sp.Matrix(
        [
            sp.simplify(
                sp.Rational(3, 1)
                / (4 * sp.pi)
                * (
                    sum(vector[alpha] * sphere_moment(alpha, i) for alpha in range(3))
                    + sum(
                        stf[alpha, beta] * sphere_moment(alpha, beta, i)
                        for alpha in range(3)
                        for beta in range(3)
                    )
                )
            )
            for i in range(3)
        ]
    )
    dipole_residual = sp.simplify(recovered_vector - vector)
    checks["directional_dipole_recovery"] = exact_zero_matrix(dipole_residual)
    details["directional_dipole_recovery"] = {
        "method": "explicit second moment plus antipodal vanishing of the cubic moment",
        "recovered_vector": [sp.sstr(value) for value in recovered_vector],
        "residual": [sp.sstr(value) for value in dipole_residual],
        "pass": checks["directional_dipole_recovery"],
    }

    recovered_stf = sp.zeros(3, 3)
    for i in range(3):
        for j in range(3):
            dipole_term = sum(
                vector[alpha]
                * (
                    sphere_moment(alpha, i, j)
                    - sp.Rational(1, 3)
                    * sp.KroneckerDelta(i, j)
                    * sphere_moment(alpha)
                )
                for alpha in range(3)
            )
            tensor_term = sum(
                stf[alpha, beta]
                * (
                    sphere_moment(alpha, beta, i, j)
                    - sp.Rational(1, 3)
                    * sp.KroneckerDelta(i, j)
                    * sphere_moment(alpha, beta)
                )
                for alpha in range(3)
                for beta in range(3)
            )
            recovered_stf[i, j] = sp.simplify(
                sp.Rational(15, 1) / (8 * sp.pi) * (dipole_term + tensor_term)
            )
    stf_residual = sp.simplify(recovered_stf - stf)
    checks["directional_stf2_recovery"] = exact_zero_matrix(stf_residual)
    details["directional_stf2_recovery"] = {
        "method": "explicit fourth and second moment contraction with the STF projector",
        "recovered_tensor": [
            [sp.sstr(recovered_stf[i, j]) for j in range(3)] for i in range(3)
        ],
        "residual": [
            [sp.sstr(stf_residual[i, j]) for j in range(3)] for i in range(3)
        ],
        "pass": checks["directional_stf2_recovery"],
    }

    # 5. Transversality of the ordered simple-spectrum eigenframe slice.
    lam_a, lam_b, lam_c = sp.symbols("lambda_a lambda_b lambda_c", real=True)
    omega12, omega13, omega23 = sp.symbols(
        "omega12 omega13 omega23", real=True
    )
    diagonal_tensor = sp.diag(lam_a, lam_b, lam_c)
    skew_generator = sp.Matrix(
        [
            [0, omega12, omega13],
            [-omega12, 0, omega23],
            [-omega13, -omega23, 0],
        ]
    )
    orbit_tangent = skew_generator * diagonal_tensor - diagonal_tensor * skew_generator
    off_diagonal = sp.Matrix(
        [orbit_tangent[0, 1], orbit_tangent[0, 2], orbit_tangent[1, 2]]
    )
    slice_jacobian = off_diagonal.jacobian((omega12, omega13, omega23))
    slice_determinant = sp.factor(slice_jacobian.det())
    expected_slice_determinant = -(
        (lam_a - lam_b) * (lam_a - lam_c) * (lam_b - lam_c)
    )
    slice_example = slice_determinant.subs(
        {lam_a: sp.Integer(1), lam_b: sp.Integer(-1), lam_c: sp.Integer(0)}
    )
    checks["eigenframe_slice_transverse_simple_spectrum"] = (
        exact_zero(slice_determinant - expected_slice_determinant)
        and slice_example != 0
    )
    details["eigenframe_slice_transverse_simple_spectrum"] = {
        "method": "Jacobian from rotation parameters to the three off-diagonal orbit-tangent components",
        "determinant": sp.sstr(slice_determinant),
        "expected": sp.sstr(expected_slice_determinant),
        "simple_spectrum_condition": "all three pairwise eigenvalue differences are nonzero",
        "registered_example_determinant": sp.sstr(slice_example),
        "pass": checks["eigenframe_slice_transverse_simple_spectrum"],
    }

    # 6. Kronecker Fisher determinant and the one-shell rank obstruction.
    k11, k12, k22, p, q, r = sp.symbols("k11 k12 k22 p q r", real=True)
    depth_gram = sp.Matrix([[k11, k12], [k12, k22]])
    directional_metric = sp.diag(p, q, r)
    fisher = sp.kronecker_product(depth_gram, directional_metric)
    fisher_determinant = sp.factor(fisher.det())
    expected_fisher_determinant = sp.factor(
        depth_gram.det() ** 3 * directional_metric.det() ** 2
    )

    independent_f_l = sp.Matrix([1, 0])
    independent_f_g = sp.Matrix([0, 1])
    independent_profiles = sp.Matrix.hstack(independent_f_l, independent_f_g)
    independent_gram = independent_profiles.T * independent_profiles
    registered_directional_metric = sp.diag(2, 3, 5)
    independent_fisher = sp.kronecker_product(
        independent_gram, registered_directional_metric
    )

    one_shell_profiles = sp.Matrix([[2, 3]])
    one_shell_gram = one_shell_profiles.T * one_shell_profiles
    one_shell_fisher = sp.kronecker_product(
        one_shell_gram, registered_directional_metric
    )
    checks["local_global_fisher_factorization"] = all(
        (
            exact_zero(fisher_determinant - expected_fisher_determinant),
            independent_gram.det() == 1,
            independent_fisher.rank() == 6,
            independent_fisher.det() == 900,
            one_shell_gram.det() == 0,
            one_shell_gram.rank() == 1,
            one_shell_fisher.det() == 0,
            one_shell_fisher.rank() == 3,
        )
    )
    details["local_global_fisher_factorization"] = {
        "method": "exact determinant of K tensor diag(p,q,r), plus both registered depth vectors",
        "symbolic_determinant": sp.sstr(fisher_determinant),
        "expected_determinant": sp.sstr(expected_fisher_determinant),
        "depth_independent": {
            "gram": [
                [int(independent_gram[i, j]) for j in range(2)] for i in range(2)
            ],
            "fisher_rank": int(independent_fisher.rank()),
            "fisher_determinant": int(independent_fisher.det()),
        },
        "depth_single_shell": {
            "gram": [
                [int(one_shell_gram[i, j]) for j in range(2)] for i in range(2)
            ],
            "gram_rank": int(one_shell_gram.rank()),
            "fisher_rank": int(one_shell_fisher.rank()),
            "fisher_determinant": int(one_shell_fisher.det()),
        },
        "pass": checks["local_global_fisher_factorization"],
    }

    # 7. General Fisher congruence; invertibility is used only for rank parity.
    r11, r12, r21, r22 = sp.symbols("r11 r12 r21 r22", real=True)
    c11, c12, c22 = sp.symbols("c11 c12 c22", real=True)
    d11, d12, d21, d22 = sp.symbols("d11 d12 d21 d22", real=True)
    response = sp.Matrix([[r11, r12], [r21, r22]])
    covariance_inverse = sp.Matrix([[c11, c12], [c12, c22]])
    normalizer = sp.Matrix([[d11, d12], [d21, d22]])
    fisher_zero = response.T * covariance_inverse * response
    fisher_scaled = (response * normalizer).T * covariance_inverse * (
        response * normalizer
    )
    congruence_target = normalizer.T * fisher_zero * normalizer
    congruence_residual = sp.simplify(fisher_scaled - congruence_target)
    congruence_determinant_residual = sp.factor(
        fisher_scaled.det() - normalizer.det() ** 2 * fisher_zero.det()
    )

    fixed_anchor = sp.Integer(5)
    registered_vector = sp.Matrix([1, 2, 3])
    registered_tensor = sp.diag(1, -1, 0)
    normalized_vector = registered_vector / fixed_anchor
    normalized_tensor = registered_tensor / fixed_anchor
    numeric_response = sp.Matrix([[1, 2], [3, 4]])
    numeric_covariance_inverse = sp.Matrix([[2, 1], [1, 3]])
    scalar_normalizer = sp.eye(2) / fixed_anchor
    numeric_fisher = numeric_response.T * numeric_covariance_inverse * numeric_response
    numeric_scaled_fisher = (
        (numeric_response * scalar_normalizer).T
        * numeric_covariance_inverse
        * (numeric_response * scalar_normalizer)
    )
    checks["invertible_anchor_fisher_congruence"] = all(
        (
            exact_zero_matrix(congruence_residual),
            exact_zero(congruence_determinant_residual),
            fixed_anchor * normalized_vector == registered_vector,
            fixed_anchor * normalized_tensor == registered_tensor,
            scalar_normalizer.det() != 0,
            numeric_fisher.rank() == numeric_scaled_fisher.rank() == 2,
            numeric_scaled_fisher
            == scalar_normalizer.T * numeric_fisher * scalar_normalizer,
        )
    )
    details["invertible_anchor_fisher_congruence"] = {
        "method": "direct symbolic expansion for a general 2x2 D, followed by the registered U=5 exact example",
        "matrix_residual": [
            [sp.sstr(congruence_residual[i, j]) for j in range(2)]
            for i in range(2)
        ],
        "determinant_residual": sp.sstr(congruence_determinant_residual),
        "rank_condition": "det(D) != 0",
        "fixed_anchor_example": {
            "U": 5,
            "normalized_vector": [sp.sstr(value) for value in normalized_vector],
            "normalized_tensor": [
                [sp.sstr(normalized_tensor[i, j]) for j in range(3)]
                for i in range(3)
            ],
            "unscaled_fisher_rank": int(numeric_fisher.rank()),
            "scaled_fisher_rank": int(numeric_scaled_fisher.rank()),
        },
        "pass": checks["invertible_anchor_fisher_congruence"],
    }

    # 8-9. Observation-inclusive exact finite-rank size and conservative ties.
    alpha = sp.Rational(1, 20)
    rank_formula_failures: list[dict[str, int | str]] = []
    tie_failures: list[dict[str, int]] = []
    first_nonempty_m: int | None = None
    for m in range(1, 101):
        rejection_count = sum(
            1 for position in range(m + 1) if sp.Rational(1 + position, m + 1) <= alpha
        )
        exact_size = sp.Rational(rejection_count, m + 1)
        expected_size = sp.Rational((m + 1) // 20, m + 1)
        if exact_size != expected_size:
            rank_formula_failures.append(
                {"m": m, "observed": sp.sstr(exact_size), "expected": sp.sstr(expected_size)}
            )
        if first_nonempty_m is None and rejection_count > 0:
            first_nonempty_m = m

        untied_count = rejection_count
        for tied_nulls in range(m + 1):
            tied_count = sum(
                1
                for position in range(m + 1)
                if sp.Rational(1 + position + tied_nulls, m + 1) <= alpha
            )
            if tied_count > untied_count:
                tie_failures.append(
                    {
                        "m": m,
                        "tied_nulls": tied_nulls,
                        "tied_rejections": tied_count,
                        "untied_rejections": untied_count,
                    }
                )

    checks["finite_rank_formula_n1_100"] = (
        rank_formula_failures == [] and first_nonempty_m == 19
    )
    checks["finite_rank_ties_conservative_n1_100"] = tie_failures == []
    details["finite_rank_formula_n1_100"] = {
        "method": "enumerate every observation rank among m+1 rows and compare exact Rational size with floor(alpha*(m+1))/(m+1)",
        "alpha": "1/20",
        "m_range": [1, 100],
        "first_nonempty_rejection_m": first_nonempty_m,
        "failure_count": len(rank_formula_failures),
        "failures": rank_formula_failures,
        "pass": checks["finite_rank_formula_n1_100"],
    }
    details["finite_rank_ties_conservative_n1_100"] = {
        "method": "enumerate m=1..100 and every additive tied-null count t=0..m",
        "case_count": sum(m + 1 for m in range(1, 101)),
        "failure_count": len(tie_failures),
        "failures": tie_failures,
        "pass": checks["finite_rank_ties_conservative_n1_100"],
    }

    # 10-11. Antipodal spectral-axis construction.
    lambda1, lambda2, lambda3 = sp.symbols(
        "lambda1 lambda2 lambda3", real=True, nonnegative=True
    )
    weights = (lambda1, lambda2, lambda3)
    axes = (
        sp.Matrix([1, 0, 0]),
        sp.Matrix([0, 1, 0]),
        sp.Matrix([0, 0, 1]),
    )
    antipodal_mean = sp.zeros(3, 1)
    antipodal_second_moment = sp.zeros(3, 3)
    for weight, axis in zip(weights, axes, strict=True):
        antipodal_mean += sp.Rational(1, 2) * weight * (axis + (-axis))
        antipodal_second_moment += sp.Rational(1, 2) * weight * (
            axis * axis.T + (-axis) * (-axis).T
        )
    expected_second_moment = sp.diag(*weights)
    checks["zero_mean_antipodal_construction"] = exact_zero_matrix(
        antipodal_mean
    )
    checks["second_moment_antipodal_construction"] = exact_zero_matrix(
        antipodal_second_moment - expected_second_moment
    )
    details["zero_mean_antipodal_construction"] = {
        "method": "paired support at plus and minus each Cartesian spectral axis",
        "mean": [sp.sstr(value) for value in antipodal_mean],
        "probability_conditions": "lambda_i >= 0 and lambda1+lambda2+lambda3=1",
        "pass": checks["zero_mean_antipodal_construction"],
    }
    details["second_moment_antipodal_construction"] = {
        "method": "exact dyadic sum of the six antipodal support points",
        "second_moment": [
            [sp.sstr(antipodal_second_moment[i, j]) for j in range(3)]
            for i in range(3)
        ],
        "expected": [
            [sp.sstr(expected_second_moment[i, j]) for j in range(3)]
            for i in range(3)
        ],
        "trace": sp.sstr(sp.trace(antipodal_second_moment)),
        "pass": checks["second_moment_antipodal_construction"],
    }

    return checks, details


def main() -> int:
    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[6]
    script_relative_path = script_path.relative_to(repo_root).as_posix()
    contract_path = repo_root / CONTRACT_RELATIVE_PATH

    checks = {name: False for name in OBLIGATIONS}
    details: dict[str, Any] = {}
    counterexample: dict[str, Any] | None = None

    actual_contract_sha256 = sha256_path(contract_path)
    actual_source_hashes = {
        path: sha256_path(repo_root / path) for path in EXPECTED_SOURCE_HASHES
    }
    binding_errors = []
    if actual_contract_sha256 != EXPECTED_CONTRACT_SHA256:
        binding_errors.append(
            {
                "path": CONTRACT_RELATIVE_PATH,
                "expected": EXPECTED_CONTRACT_SHA256,
                "actual": actual_contract_sha256,
            }
        )
    for path, expected in EXPECTED_SOURCE_HASHES.items():
        actual = actual_source_hashes[path]
        if actual != expected:
            binding_errors.append(
                {"path": path, "expected": expected, "actual": actual}
            )
    if sp.__version__ != EXPECTED_SYMPY_VERSION:
        binding_errors.append(
            {
                "tool": "sympy",
                "expected": EXPECTED_SYMPY_VERSION,
                "actual": sp.__version__,
            }
        )

    if binding_errors:
        counterexample = {
            "type": "CONTENT_OR_TOOLCHAIN_BINDING_MISMATCH",
            "mismatches": binding_errors,
        }
    else:
        try:
            checks, details = derive_checks()
        except Exception as exc:  # keep stdout as one runner-parseable JSON document
            counterexample = {
                "type": "SYMPY_AXIS_EXECUTION_ERROR",
                "exception_type": type(exc).__name__,
                "message": str(exc),
            }

    all_pass = all(checks.values()) and counterexample is None
    if not all_pass and counterexample is None:
        counterexample = {
            "type": "FAILED_EXACT_OBLIGATION",
            "failed_obligations": [name for name, passed in checks.items() if not passed],
        }

    completed_at = utc_now()
    script_sha256 = sha256_path(script_path)
    command = f"python {script_relative_path}"
    result_envelope = {
        "schema": "htt.agent_harness.cas_axis_embedded_result.v1",
        "run_id": RUN_ID,
        "assignment_id": ASSIGNMENT_ID,
        "context_version": CONTEXT_VERSION,
        "axis": "sympy",
        "status": "PASS" if all_pass else "FAIL",
        "evidence_class": "exact",
        "contract_id": CONTRACT_ID,
        "contract_sha256": actual_contract_sha256,
        "claim_ceiling": "diagnostic_only_methodology_receipt",
        "completed_at": completed_at,
        "commands": [{"cmd": command, "exit": 0 if all_pass else 1}],
        "artifact_hashes": [
            {
                "kind": "standalone_axis_program",
                "path": script_relative_path,
                "sha256": script_sha256,
            }
        ],
        "source_input_hashes": [
            {"path": path, "sha256": actual_source_hashes[path]}
            for path in EXPECTED_SOURCE_HASHES
        ],
        "toolchain": {
            "python": platform.python_version(),
            "sympy": sp.__version__,
            "pinned_sympy": EXPECTED_SYMPY_VERSION,
        },
        "assumptions": ASSUMPTIONS,
        "conventions": CONVENTIONS,
        "domain_assumption_diff": [],
        "checks": checks,
        "counterexample": counterexample,
        "reproducible_command": command,
        "claim_tier_recommendation": "EXPLORATORY diagnostic-only methodology receipt; no physical, posterior, native-solver, geometry, family, or release promotion",
        "caveats": [
            "The full-sky moment identities do not certify masked or discrete quadrature.",
            "The Fisher result is structural algebra and does not provide physical local/global response functions.",
            "The antipodal construction proves only the registered zero-mean second-moment realization.",
            "This independent engine receipt is one CAS axis, not aggregate four-axis adjudication or scientific authority.",
        ],
    }
    payload = {
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": counterexample,
        "transcript": {
            "schema": "htt.agent_harness.sympy_engine_transcript.v1",
            "engine": "SymPy",
            "engine_version": sp.__version__,
            "python_version": platform.python_version(),
            "arithmetic": "exact",
            "numeric_quadrature_used": False,
            "input_bindings": {
                "contract": {
                    "path": CONTRACT_RELATIVE_PATH,
                    "sha256": actual_contract_sha256,
                    "matches_expected": actual_contract_sha256
                    == EXPECTED_CONTRACT_SHA256,
                },
                "sources": [
                    {
                        "path": path,
                        "sha256": actual_source_hashes[path],
                        "matches_expected": actual_source_hashes[path]
                        == EXPECTED_SOURCE_HASHES[path],
                    }
                    for path in EXPECTED_SOURCE_HASHES
                ],
            },
            "details": details,
            "all_pass": all_pass,
        },
        "result_envelope": result_envelope,
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
