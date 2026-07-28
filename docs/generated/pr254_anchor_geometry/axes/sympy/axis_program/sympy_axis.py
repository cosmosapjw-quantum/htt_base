#!/usr/bin/env python3
"""Exact SymPy axis for CAS-PR254-ANCHOR-GEOMETRY-001.

This program reads only the assignment's immutable inputs.  In particular, it
parses the ordered H-polytope normals and bounds from the CAS contract rather
than supplying an implicit box.  It emits one JSON document on stdout for the
parent-owned ``cas_gate.py run-adjudicate`` process.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import sympy as sp


EXPECTED_INPUT_HASHES = {
    "docs/generated/pr254_anchor_geometry/CAS_CONTRACT_PR254_ANCHOR_GEOMETRY.json":
        "4f7092860fde327e0029154e3c4ca4c7e60f7095c4026c7fb00d1899ca8c3322",
    "docs/research_program/premise_anchor/pr254_spec.yaml":
        "4e2e497e0a3f13b9b9bbed02088072230315848a8669beb4b1901894d7fafe40",
    "htt/src/common/anchor_geometry.py":
        "dc7f2496ff0c96e34847c7b13e2e8d989722cdf1457525f311d0d21b0d5dfbb9",
    "docs/generated/pr254_anchor_geometry/counterexample_oracle.json":
        "03e4d591a3be1c97f4954e2afcb2c3a98b85a8a4b244e4396aeb6292ba19e45f",
}


def _repo_root() -> Path:
    # .../.agent-harness/runs/<run>/artifacts/<assignment>/axis_program/script
    return Path(__file__).resolve().parents[6]


def _rational(value: object) -> sp.Rational:
    return sp.Rational(str(value))


def _matrix(rows: object) -> sp.Matrix:
    if not isinstance(rows, list):
        raise TypeError("matrix fixture must be a list of rows")
    return sp.Matrix([[_rational(value) for value in row] for row in rows])


def _vector(values: object) -> sp.Matrix:
    if not isinstance(values, list):
        raise TypeError("vector fixture must be a list")
    return sp.Matrix([_rational(value) for value in values])


def _exact_text(value: object) -> str:
    return str(sp.cancel(sp.sympify(value)))


def _marginal(
    atoms: tuple[tuple[sp.Rational, sp.Rational, sp.Rational], ...],
    coordinate: int,
) -> dict[sp.Rational, sp.Rational]:
    result: dict[sp.Rational, sp.Rational] = {}
    for atom in atoms:
        value = atom[coordinate]
        result[value] = result.get(value, sp.S.Zero) + atom[2]
    return result


def _exceedance(
    atoms: tuple[tuple[sp.Rational, sp.Rational, sp.Rational], ...],
) -> sp.Rational:
    return sp.Add(
        *(
            probability
            for numerator, anchor, probability in atoms
            if bool(numerator / anchor > 1)
        )
    )


def main() -> None:
    root = _repo_root()
    domain_assumption_diff: list[str] = []
    input_bytes: dict[str, bytes] = {}
    for relative, expected_hash in EXPECTED_INPUT_HASHES.items():
        data = (root / relative).read_bytes()
        input_bytes[relative] = data
        actual_hash = hashlib.sha256(data).hexdigest()
        if actual_hash != expected_hash:
            domain_assumption_diff.append(
                f"required input hash mismatch for {relative}: "
                f"expected {expected_hash}, got {actual_hash}"
            )

    contract_path = (
        "docs/generated/pr254_anchor_geometry/"
        "CAS_CONTRACT_PR254_ANCHOR_GEOMETRY.json"
    )
    oracle_path = (
        "docs/generated/pr254_anchor_geometry/counterexample_oracle.json"
    )
    contract = json.loads(input_bytes[contract_path])
    oracle = json.loads(input_bytes[oracle_path])
    required_sympy = contract["axes"]["sympy"]["pinned_toolchain"]["sympy"]
    if sp.__version__ != required_sympy:
        domain_assumption_diff.append(
            f"SymPy version mismatch: expected {required_sympy}, "
            f"got {sp.__version__}"
        )

    target = contract["target"]
    obligation_keys = tuple(target["exact_test_obligations"])
    fixture_rows = target["numeric_test_vectors"]
    fixtures = {row["id"]: row for row in fixture_rows}
    if len(fixtures) != len(fixture_rows):
        raise ValueError("numeric fixture IDs must be unique")

    # Product of Euclidean block balls.
    product_fixture = fixtures["PRODUCT-FIXTURE"]
    product_vectors = tuple(
        _vector(block["u"]) for block in product_fixture["blocks"]
    )
    product_radii = tuple(
        _rational(block["radius"]) for block in product_fixture["blocks"]
    )
    product_norm_sq = tuple(vector.dot(vector) for vector in product_vectors)
    product_ratios = tuple(
        sp.sqrt(norm_sq) / radius
        for norm_sq, radius in zip(
            product_norm_sq, product_radii, strict=True
        )
    )
    product_gauge = sp.Max(*product_ratios)
    product_inside_by_gauge = bool(product_gauge <= 1)
    product_inside_by_blocks = all(
        bool(norm_sq <= radius**2)
        for norm_sq, radius in zip(
            product_norm_sq, product_radii, strict=True
        )
    )
    product_check = bool(
        product_radii
        and all(radius > 0 for radius in product_radii)
        and all(norm_sq >= 0 for norm_sq in product_norm_sq)
        and product_inside_by_gauge == product_inside_by_blocks
    )

    # Positive-definite ellipsoid.
    ellipsoid_fixture = fixtures["ELLIPSOID-FIXTURE"]
    ellipsoid_u = _vector(ellipsoid_fixture["u"])
    ellipsoid_q = _matrix(ellipsoid_fixture["Q"])
    ellipsoid_gauge_sq = sp.cancel(
        (ellipsoid_u.T * ellipsoid_q * ellipsoid_u)[0]
    )
    ellipsoid_gauge = sp.sqrt(ellipsoid_gauge_sq)
    ellipsoid_check = bool(
        ellipsoid_q.rows == ellipsoid_q.cols == ellipsoid_u.rows
        and ellipsoid_q == ellipsoid_q.T
        and ellipsoid_q.is_positive_definite is True
        and ellipsoid_gauge_sq >= 0
        and bool(ellipsoid_gauge <= 1)
        == bool(ellipsoid_gauge_sq <= 1)
    )

    # Centrally symmetric spanning H-polytope.  The ordered normals and bounds
    # are both parsed from the sealed fixture and paired without reordering.
    polytope_fixture = fixtures["POLYTOPE-FIXTURE"]
    polytope_u = _vector(polytope_fixture["u"])
    ordered_normals = tuple(
        _vector(row) for row in polytope_fixture["halfspace_normals"]
    )
    ordered_bounds = tuple(
        _rational(value)
        for value in polytope_fixture["halfspace_bounds"]
    )
    if len(ordered_normals) != len(ordered_bounds):
        raise ValueError("polytope normals and bounds must have equal length")
    ordered_halfspaces = tuple(
        zip(ordered_normals, ordered_bounds, strict=True)
    )
    normal_matrix = sp.Matrix.vstack(
        *(normal.T for normal in ordered_normals)
    )
    antipodal = all(
        any(
            other_normal == -normal and other_bound == bound
            for other_normal, other_bound in ordered_halfspaces
        )
        for normal, bound in ordered_halfspaces
    )
    polytope_ratios = tuple(
        sp.cancel(normal.dot(polytope_u) / bound)
        for normal, bound in ordered_halfspaces
    )
    polytope_gauge = sp.Max(*polytope_ratios)
    polytope_inside_by_gauge = bool(polytope_gauge <= 1)
    polytope_inside_by_halfspaces = all(
        bool(normal.dot(polytope_u) <= bound)
        for normal, bound in ordered_halfspaces
    )
    polytope_check = bool(
        ordered_halfspaces
        and all(normal.rows == polytope_u.rows for normal in ordered_normals)
        and all(normal.dot(normal) > 0 for normal in ordered_normals)
        and all(bound > 0 for bound in ordered_bounds)
        and normal_matrix.rank() == polytope_u.rows
        and antipodal
        and polytope_inside_by_gauge
        == polytope_inside_by_halfspaces
    )

    # One-way outer-envelope implication and its explicitly forbidden converse.
    j1 = oracle["j1_exact"]
    physical_radius = _rational(j1["physical_radius"])
    anchor_radii = (
        _rational(j1["anchor_a_radius"]),
        _rational(j1["anchor_b_radius"]),
    )
    one_way_violation_count = sum(
        int(bool(physical_radius > anchor_radius))
        for anchor_radius in anchor_radii
    )
    converse_witnesses = tuple(
        (physical_radius + anchor_radius) / 2
        for anchor_radius in anchor_radii
    )
    one_way_check = bool(
        physical_radius > 0
        and all(anchor_radius > 0 for anchor_radius in anchor_radii)
        and all(
            physical_radius <= anchor_radius
            for anchor_radius in anchor_radii
        )
        and one_way_violation_count == 0
        and all(
            physical_radius < abs(witness) <= anchor_radius
            for witness, anchor_radius in zip(
                converse_witnesses, anchor_radii, strict=True
            )
        )
    )

    # Exact rank preservation and response reparameterization.
    rank_fixture = fixtures["RANK-FIXTURE"]
    response = _matrix(rank_fixture["R"])
    scaling = _matrix(rank_fixture["D"])
    determinant = sp.cancel(scaling.det())
    transformed_response = response * scaling
    rank_response = response.rank()
    rank_transformed = transformed_response.rank()
    scaling_inverse = scaling.inv()
    rank_check = bool(
        scaling.rows == scaling.cols == response.cols
        and determinant != 0
        and scaling * scaling_inverse == sp.eye(scaling.rows)
        and rank_transformed == rank_response
    )
    state_symbols = sp.symbols(
        f"u0:{response.cols}", real=True
    )
    state = sp.Matrix(state_symbols)
    transformed_identity_residual = sp.simplify(
        response * state
        - transformed_response * (scaling_inverse * state)
    )
    transformed_response_check = bool(
        transformed_identity_residual
        == sp.zeros(response.rows, 1)
    )

    # J1 exact counterexample.
    probe = _rational(j1["probe"])
    j1_rho_a = sp.cancel(abs(probe) / anchor_radii[0])
    j1_rho_b = sp.cancel(abs(probe) / anchor_radii[1])
    j1_check = bool(
        physical_radius < anchor_radii[0]
        and physical_radius < anchor_radii[1]
        and j1_rho_a == _rational(j1["rho_a"])
        and j1_rho_b == _rational(j1["rho_b"])
        and j1_rho_a != j1_rho_b
        and oracle["checks"]["j1_both_outer_containments_hold"] is True
        and oracle["checks"]["j1_gauges_differ_on_same_state"] is True
        and oracle["checks"]["j1_neither_anchor_equals_physical_set"] is True
    )

    # J2 exact dependence counterexample.  Construct both joint laws explicitly
    # from the registered equal two-point marginals, then recompute marginals
    # and exceedance probabilities from the joint atoms.
    j2 = oracle["j2_exact"]
    numerator_marginal = {
        _rational(value): _rational(probability)
        for value, probability in j2["numerator_marginal"].items()
    }
    anchor_marginal = {
        _rational(value): _rational(probability)
        for value, probability in j2["anchor_marginal"].items()
    }
    numerator_support = tuple(sorted(numerator_marginal))
    anchor_support = tuple(sorted(anchor_marginal))
    comonotone_atoms = tuple(
        (
            numerator_value,
            anchor_value,
            numerator_marginal[numerator_value],
        )
        for numerator_value, anchor_value in zip(
            numerator_support, anchor_support, strict=True
        )
    )
    countermonotone_atoms = tuple(
        (
            numerator_value,
            anchor_value,
            numerator_marginal[numerator_value],
        )
        for numerator_value, anchor_value in zip(
            numerator_support, reversed(anchor_support), strict=True
        )
    )
    j2_comonotone_exceedance = _exceedance(comonotone_atoms)
    j2_countermonotone_exceedance = _exceedance(
        countermonotone_atoms
    )
    j2_check = bool(
        numerator_marginal == anchor_marginal
        and len(numerator_support) == len(anchor_support) == 2
        and sum(numerator_marginal.values(), sp.S.Zero) == 1
        and all(value > 0 for value in numerator_support)
        and all(value > 0 for value in anchor_support)
        and _marginal(comonotone_atoms, 0) == numerator_marginal
        and _marginal(comonotone_atoms, 1) == anchor_marginal
        and _marginal(countermonotone_atoms, 0) == numerator_marginal
        and _marginal(countermonotone_atoms, 1) == anchor_marginal
        and j2_comonotone_exceedance
        == _rational(j2["comonotone_exceedance_probability"])
        and j2_countermonotone_exceedance
        == _rational(j2["countermonotone_exceedance_probability"])
        and j2_comonotone_exceedance
        != j2_countermonotone_exceedance
        and oracle["checks"]["j2_joint_laws_have_same_marginals"] is True
        and oracle["checks"]["j2_exceedance_laws_differ"] is True
    )

    checks = {
        "product_ball_max_ratio": product_check,
        "ellipsoid_unit_sublevel": ellipsoid_check,
        "polytope_unit_sublevel": polytope_check,
        "one_way_outer_envelope": one_way_check,
        "invertible_scaling_rank": rank_check,
        "transformed_response_identity": transformed_response_check,
        "j1_counterexample": j1_check,
        "j2_dependence_counterexample": j2_check,
    }
    if set(checks) != set(obligation_keys):
        raise ValueError("axis check keys do not exactly match the contract")

    computed = {
        "product_gauge": _exact_text(product_gauge),
        "ellipsoid_gauge_sq": _exact_text(ellipsoid_gauge_sq),
        "polytope_gauge": _exact_text(polytope_gauge),
        "rank_R": _exact_text(rank_response),
        "rank_RD": _exact_text(rank_transformed),
        "det_D": _exact_text(determinant),
        "j1_rho_a": _exact_text(j1_rho_a),
        "j1_rho_b": _exact_text(j1_rho_b),
        "j2_comonotone_exceedance": _exact_text(
            j2_comonotone_exceedance
        ),
        "j2_countermonotone_exceedance": _exact_text(
            j2_countermonotone_exceedance
        ),
        "one_way_violation_count": _exact_text(
            one_way_violation_count
        ),
    }
    if set(computed) != set(target["expected_exact_values"]):
        raise ValueError(
            "computed keyset does not exactly match expected_exact_values"
        )

    payload = {
        "checks": checks,
        "domain_assumption_diff": domain_assumption_diff,
        "computed": computed,
        # The registered J1/J2 constructions are expected counterexamples to
        # broader conjectures.  This field is for a counterexample to the CAS
        # contract itself.
        "counterexample": None,
    }
    print(json.dumps(payload, sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
