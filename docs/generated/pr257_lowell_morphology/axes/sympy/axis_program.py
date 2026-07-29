#!/usr/bin/env python3
"""Independent exact SymPy axis for CAS-PR257-ORBIT-CATALOGUE-V2-001.

The O(3) parity proof uses exact rational one-parameter generators for SO(3)
and one exact reflection.  The determinant-valued Krylov pseudoscalar is
verified in factorized form through K' = R K and the universal 3x3
determinant-product identity, avoiding unnecessary expression expansion.
"""

from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import sympy as sp


CONTRACT_PATH = Path(
    "docs/generated/pr257_lowell_morphology/"
    "CAS_CONTRACT_PR257_ORBIT_V2.json"
)
SPEC_PATH = Path("docs/research_program/premise_anchor/pr257_spec.yaml")
CONTRACT_SHA256 = (
    "1d3e0c76a3833dd72cb5e74dcd3ddedfe91a538902950df603587e77ad6c0e56"
)
SPEC_SHA256 = (
    "f2c3fdba9d9b7852e885e2166be5f2237c725a3da8be40cef5760158412915e2"
)
CONTRACT_ID = "CAS-PR257-ORBIT-CATALOGUE-V2-001"

OBLIGATIONS = (
    "scalar_pseudoscalar_o3",
    "cayley_hamilton_tracefree_3x3",
    "cayley_hamilton_vector_contractions",
    "beta_krylov_gram_syzygy",
    "fixed_rational_values",
    "nongeneric_nonseparation_witness",
    "generic_separation_not_promoted",
    "completeness_not_promoted",
)

CATALOGUE_NAMES = (
    "tr_sigma2",
    "tr_sigma3",
    "beta2",
    "beta_sigma_beta",
    "beta_sigma2_beta",
    "det_beta_sigma_beta_sigma2_beta",
    "omega2",
    "omega_sigma_omega",
    "omega_sigma2_omega",
    "beta_dot_omega",
    "beta_sigma_omega",
    "beta_sigma2_omega",
)
CANONICAL_INVARIANT_EXPRESSIONS = (
    "tr(sigma^2)",
    "tr(sigma^3)",
    "beta^T beta",
    "beta^T sigma beta",
    "beta^T sigma^2 beta",
    "det[beta,sigma beta,sigma^2 beta]",
    "omega^T omega",
    "omega^T sigma omega",
    "omega^T sigma^2 omega",
    "beta^T omega",
    "beta^T sigma omega",
    "beta^T sigma^2 omega",
)
EVEN_NAMES = frozenset(
    {
        "tr_sigma2",
        "tr_sigma3",
        "beta2",
        "beta_sigma_beta",
        "beta_sigma2_beta",
        "omega2",
        "omega_sigma_omega",
        "omega_sigma2_omega",
    }
)
ODD_NAMES = frozenset(
    {
        "det_beta_sigma_beta_sigma2_beta",
        "beta_dot_omega",
        "beta_sigma_omega",
        "beta_sigma2_omega",
    }
)


def sha256_path(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_zero(expression: sp.Expr) -> bool:
    return sp.cancel(expression) == 0


def exact_zero_matrix(matrix: sp.MatrixBase) -> bool:
    return all(exact_zero(entry) for entry in matrix)


def catalogue_without_krylov_det(
    sigma: sp.MatrixBase,
    beta: sp.MatrixBase,
    omega: sp.MatrixBase,
) -> dict[str, sp.Expr]:
    sigma2 = sigma * sigma
    return {
        "tr_sigma2": sp.trace(sigma2),
        "tr_sigma3": sp.trace(sigma2 * sigma),
        "beta2": (beta.T * beta)[0],
        "beta_sigma_beta": (beta.T * sigma * beta)[0],
        "beta_sigma2_beta": (beta.T * sigma2 * beta)[0],
        "omega2": (omega.T * omega)[0],
        "omega_sigma_omega": (omega.T * sigma * omega)[0],
        "omega_sigma2_omega": (omega.T * sigma2 * omega)[0],
        "beta_dot_omega": (beta.T * omega)[0],
        "beta_sigma_omega": (beta.T * sigma * omega)[0],
        "beta_sigma2_omega": (beta.T * sigma2 * omega)[0],
    }


def full_catalogue(
    sigma: sp.MatrixBase,
    beta: sp.MatrixBase,
    omega: sp.MatrixBase,
) -> dict[str, sp.Expr]:
    values = catalogue_without_krylov_det(sigma, beta, omega)
    krylov = sp.Matrix.hstack(beta, sigma * beta, sigma**2 * beta)
    values["det_beta_sigma_beta_sigma2_beta"] = krylov.det()
    return {name: values[name] for name in CATALOGUE_NAMES}


def exact_o3_parity_check(
    sigma: sp.MatrixBase,
    beta: sp.MatrixBase,
    omega: sp.MatrixBase,
) -> bool:
    t = sp.symbols("t", real=True)
    cosine = (1 - t**2) / (1 + t**2)
    sine = 2 * t / (1 + t**2)
    generators = (
        (
            sp.Matrix(
                [
                    [1, 0, 0],
                    [0, cosine, -sine],
                    [0, sine, cosine],
                ]
            ),
            1,
        ),
        (
            sp.Matrix(
                [
                    [cosine, 0, sine],
                    [0, 1, 0],
                    [-sine, 0, cosine],
                ]
            ),
            1,
        ),
        (
            sp.Matrix(
                [
                    [cosine, -sine, 0],
                    [sine, cosine, 0],
                    [0, 0, 1],
                ]
            ),
            1,
        ),
        (sp.diag(-1, 1, 1), -1),
    )

    original = catalogue_without_krylov_det(sigma, beta, omega)
    original_krylov = sp.Matrix.hstack(
        beta, sigma * beta, sigma**2 * beta
    )

    # This universal identity supplies the exact determinant step after K'=RK.
    r_entries = sp.symbols("r0:9", real=True)
    k_entries = sp.symbols("k0:9", real=True)
    generic_r = sp.Matrix(3, 3, r_entries)
    generic_k = sp.Matrix(3, 3, k_entries)
    determinant_product = sp.expand(
        (generic_r * generic_k).det()
        - generic_r.det() * generic_k.det()
    ) == 0

    all_generator_checks: list[bool] = []
    for rotation, determinant_sign in generators:
        orthogonal = exact_zero_matrix(rotation.T * rotation - sp.eye(3))
        determinant_correct = exact_zero(
            rotation.det() - determinant_sign
        )
        transformed_sigma = rotation * sigma * rotation.T
        transformed_beta = rotation * beta
        # omega is axial: omega' = det(R) R omega.
        transformed_omega = determinant_sign * rotation * omega
        transformed = catalogue_without_krylov_det(
            transformed_sigma,
            transformed_beta,
            transformed_omega,
        )

        parity_checks = []
        for name, original_value in original.items():
            parity = determinant_sign if name in ODD_NAMES else 1
            parity_checks.append(
                exact_zero(transformed[name] - parity * original_value)
            )

        transformed_krylov = sp.Matrix.hstack(
            transformed_beta,
            transformed_sigma * transformed_beta,
            transformed_sigma**2 * transformed_beta,
        )
        krylov_covariant = exact_zero_matrix(
            transformed_krylov - rotation * original_krylov
        )
        determinant_parity = (
            krylov_covariant
            and determinant_product
            and determinant_correct
        )
        all_generator_checks.append(
            orthogonal
            and determinant_correct
            and all(parity_checks)
            and determinant_parity
        )

    # The three rational planar families generate a dense subset of SO(3);
    # exact rational identities therefore extend polynomially to the omitted
    # t=infinity points.  Adding one reflection generates the other component.
    return (
        EVEN_NAMES | ODD_NAMES == frozenset(CATALOGUE_NAMES)
        and EVEN_NAMES.isdisjoint(ODD_NAMES)
        and all(all_generator_checks)
    )


def fixed_values() -> dict[str, str]:
    sigma = sp.diag(1, 2, -3)
    beta = sp.Matrix([1, 1, 1])
    omega = sp.Matrix([1, 2, 3])
    sigma2 = sigma**2
    sigma3 = sigma**3
    krylov = sp.Matrix.hstack(beta, sigma * beta, sigma2 * beta)
    values: dict[str, sp.Expr] = {
        **full_catalogue(sigma, beta, omega),
        "beta_sigma3_beta": (beta.T * sigma3 * beta)[0],
        "omega_sigma3_omega": (omega.T * sigma3 * omega)[0],
        "beta_sigma3_omega": (beta.T * sigma3 * omega)[0],
        "beta_krylov_gram_determinant": (krylov.T * krylov).det(),
    }
    return {name: str(sp.cancel(value)) for name, value in values.items()}


def nonseparation_witness() -> bool:
    sigma = sp.diag(1, 2, -3)
    beta = sp.zeros(3, 1)
    omega_left = sp.Matrix([1, 2, 3])
    omega_right = -omega_left
    left = full_catalogue(sigma, beta, omega_left)
    right = full_catalogue(sigma, beta, omega_right)

    # sigma has three distinct eigenvalues.  Its O(3) stabilizer is therefore
    # the eight diagonal sign matrices in this eigenbasis.  Enumerate all of
    # them and verify that the axial action maps none of them to -omega.
    no_stabilizer_map = True
    for signs in itertools.product((-1, 1), repeat=3):
        rotation = sp.diag(*signs)
        determinant_sign = signs[0] * signs[1] * signs[2]
        stabilizes_sigma = rotation * sigma * rotation.T == sigma
        maps_pair = (
            determinant_sign * rotation * omega_left == omega_right
        )
        no_stabilizer_map = (
            no_stabilizer_map and stabilizes_sigma and not maps_pair
        )

    return (
        omega_left != omega_right
        and left == right
        and all(left[name] == 0 for name in ODD_NAMES)
        and no_stabilizer_map
    )


def main() -> None:
    contract_bytes = CONTRACT_PATH.read_bytes()
    contract = json.loads(contract_bytes)
    target = contract["target"]
    semantics = contract["semantics"]
    source_hashes = {
        row["path"]: row["sha256"]
        for row in contract["identity"]["source_input_hashes"]
    }
    contract_bound = (
        hashlib.sha256(contract_bytes).hexdigest() == CONTRACT_SHA256
        and sha256_path(SPEC_PATH) == SPEC_SHA256
        and contract["identity"]["contract_id"] == CONTRACT_ID
        and tuple(target["exact_test_obligations"]) == OBLIGATIONS
        and tuple(target["invariants"]) == CANONICAL_INVARIANT_EXPRESSIONS
        and source_hashes.get(SPEC_PATH.as_posix()) == SPEC_SHA256
        and contract["semantics"]["symbol_type_domain_map"]["omega"]
        == "real axial 3-vector"
    )

    s11, s22, s12, s13, s23 = sp.symbols(
        "s11 s22 s12 s13 s23", real=True
    )
    b1, b2, b3 = sp.symbols("b1 b2 b3", real=True)
    w1, w2, w3 = sp.symbols("w1 w2 w3", real=True)
    sigma = sp.Matrix(
        [
            [s11, s12, s13],
            [s12, s22, s23],
            [s13, s23, -s11 - s22],
        ]
    )
    beta = sp.Matrix([b1, b2, b3])
    omega = sp.Matrix([w1, w2, w3])
    tr_sigma2 = sp.trace(sigma**2)
    tr_sigma3 = sp.trace(sigma**3)
    cayley_hamilton = (
        sigma**3
        - tr_sigma2 * sigma / 2
        - tr_sigma3 * sp.eye(3) / 3
    )
    cayley_hamilton_exact = exact_zero_matrix(cayley_hamilton)
    contraction_residuals = (
        (beta.T * sigma**3 * beta)[0]
        - tr_sigma2 * (beta.T * sigma * beta)[0] / 2
        - tr_sigma3 * (beta.T * beta)[0] / 3,
        (omega.T * sigma**3 * omega)[0]
        - tr_sigma2 * (omega.T * sigma * omega)[0] / 2
        - tr_sigma3 * (omega.T * omega)[0] / 3,
        (beta.T * sigma**3 * omega)[0]
        - tr_sigma2 * (beta.T * sigma * omega)[0] / 2
        - tr_sigma3 * (beta.T * omega)[0] / 3,
    )
    contractions_exact = all(
        exact_zero(residual) for residual in contraction_residuals
    )

    generic_krylov_entries = sp.symbols("g0:9", real=True)
    generic_krylov = sp.Matrix(3, 3, generic_krylov_entries)
    gram_syzygy_exact = (
        sp.expand(
            (generic_krylov.T * generic_krylov).det()
            - generic_krylov.det() ** 2
        )
        == 0
    )

    computed = fixed_values()
    expected = target["expected_exact_values"]
    fixed_values_exact = computed == expected
    witness_exact = nonseparation_witness()
    exclusions = set(semantics["exclusions"])
    forbidden_shortcuts = set(target["forbidden_shortcuts"])
    generic_separation_unpromoted = (
        "No generic orbit separation theorem is asserted." in exclusions
        and "Do not infer generic separation from finite test vectors."
        in forbidden_shortcuts
    )
    completeness_unpromoted = (
        "No invariant-ring or degree completeness theorem is asserted."
        in exclusions
        and (
            "Do not infer invariant-ring completeness from "
            "Cayley-Hamilton reductions."
        )
        in forbidden_shortcuts
    )

    checks = {
        "scalar_pseudoscalar_o3": (
            contract_bound and exact_o3_parity_check(sigma, beta, omega)
        ),
        "cayley_hamilton_tracefree_3x3": (
            contract_bound and cayley_hamilton_exact
        ),
        "cayley_hamilton_vector_contractions": (
            contract_bound and contractions_exact
        ),
        "beta_krylov_gram_syzygy": (
            contract_bound and gram_syzygy_exact
        ),
        "fixed_rational_values": (
            contract_bound and fixed_values_exact
        ),
        "nongeneric_nonseparation_witness": (
            contract_bound and witness_exact
        ),
        "generic_separation_not_promoted": (
            contract_bound and generic_separation_unpromoted
        ),
        "completeness_not_promoted": (
            contract_bound and completeness_unpromoted
        ),
    }
    payload = {
        "checks": checks,
        "computed": computed,
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
