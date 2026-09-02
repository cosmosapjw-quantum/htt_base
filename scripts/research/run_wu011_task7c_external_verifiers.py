#!/usr/bin/env python3
"""Independent downloaded-package verifiers for PMG-WU-011 Task-7C.

This script is intentionally outside the production ``obsstat`` package.  It
constructs the axisymmetric wide-mask continuum response by an exact SymPy
route and an independent DUCC/SciPy quadrature route, cross-checks Wigner 3j
symbols with WIGXJPF, DUCC and SymPy, and asks Arb ball arithmetic to prove that
one selected square minor in every z-direction ``|m|`` block excludes zero.

A PASS is proof support for the z-direction continuum ``L=12`` rank only.  It
does not validate the HEALPix bridge, the other boost directions, an empirical
velocity, a global matter tilt, a Bianchi family, or a scientific Task-7C
terminal.
"""

from __future__ import annotations

import argparse
from functools import lru_cache
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import sympy as sp


PYWIGXJPF_SDIST_SHA256 = (
    "30122c9ab2775aa8a0531d01956892627f1c6e82ba65c3abf6b8fc4fb75c3aef"
)
WOLFRAM_Z_L12_SMALLEST_SINGULAR = 0.0069056649796965369794076720012257161
_EXPECTED_L12_COMPLEX_BLOCK_RANKS = (4, 4, 4, 3, 2, 1)
_X = sp.symbols("x", real=True)


def package_contract() -> dict[str, str]:
    return {
        "pywigxjpf": "1.13.3",
        "python-flint": "0.9.0",
        "ducc0": "0.41.0",
        "mpmath": "1.4.1",
        "sympy": "1.14.0",
        "scipy": "1.18.1",
        "numpy": "2.5.2",
    }


def package_versions() -> dict[str, Any]:
    versions: dict[str, str] = {}
    for distribution, expected in package_contract().items():
        observed = importlib.metadata.version(distribution)
        versions[distribution] = observed
        if observed != expected:
            raise RuntimeError(
                f"package version mismatch for {distribution}: {observed} != {expected}"
            )
    return {
        "status": "PASS",
        "versions": versions,
        "pywigxjpf_sdist_sha256": PYWIGXJPF_SDIST_SHA256,
    }


def _registered_wigner_cases() -> list[tuple[int, int, int, int, int, int]]:
    cases: list[tuple[int, int, int, int, int, int]] = []
    for j2 in range(0, 13):
        for j3 in range(0, 13):
            for m2 in range(-min(j2, 2), min(j2, 2) + 1):
                m3 = 0
                m1 = -m2
                lower = max(abs(j2 - j3), abs(m1))
                upper = min(j2 + j3, 20)
                for j1 in range(lower, upper + 1):
                    cases.append((j1, j2, j3, m1, m2, m3))
                    if len(cases) >= 320:
                        return cases
    return cases


def validate_wigner_symbols() -> dict[str, Any]:
    """Compare WIGXJPF and DUCC values with exact SymPy Wigner 3j values."""

    import ducc0.misc as dmisc
    import pywigxjpf as wig
    from sympy.physics.wigner import wigner_3j

    cases = _registered_wigner_cases()
    maximum = 0.0
    maximum_case: tuple[int, int, int, int, int, int] | None = None
    wig.wig_table_init(48, 9)
    wig.wig_temp_init(48)
    try:
        for case in cases:
            j1, j2, j3, m1, m2, m3 = case
            exact = float(sp.N(wigner_3j(j1, j2, j3, m1, m2, m3), 60))
            wig_value = float(
                wig.wig3jj(
                    2 * j1,
                    2 * j2,
                    2 * j3,
                    2 * m1,
                    2 * m2,
                    2 * m3,
                )
            )
            first_j1, sequence = dmisc.wigner3j_int(j2, j3, m2, m3)
            offset = j1 - int(first_j1)
            if not 0 <= offset < len(sequence):
                raise RuntimeError(f"DUCC Wigner sequence omitted registered case {case}")
            ducc_value = float(sequence[offset])
            residual = max(abs(wig_value - exact), abs(ducc_value - exact))
            if residual > maximum:
                maximum = residual
                maximum_case = case
    finally:
        wig.wig_temp_free()
        wig.wig_table_free()

    status = "PASS" if len(cases) >= 100 and maximum <= 5.0e-14 else "FAIL"
    return {
        "status": status,
        "case_count": len(cases),
        "maximum_absolute_residual": maximum,
        "maximum_residual_case": maximum_case,
        "engines": [
            "pywigxjpf_prime_factorisation",
            "ducc0_schulten_gordon",
            "sympy_exact_wigner_3j",
        ],
    }


def _poly_integral(expr: sp.Expr, lower: sp.Rational, upper: sp.Rational) -> sp.Expr:
    poly = sp.Poly(sp.expand(expr), _X, domain=sp.QQ)
    antiderivative = poly.integrate().as_expr()
    return sp.cancel(
        antiderivative.subs(_X, upper) - antiderivative.subs(_X, lower)
    )


def _wide_mask_integral(poly: sp.Expr) -> sp.Expr:
    central = _poly_integral(
        (sp.Rational(1, 2) + sp.Rational(2, 3) * _X) * poly,
        sp.Rational(-3, 4),
        sp.Rational(3, 4),
    )
    upper = _poly_integral(poly, sp.Rational(3, 4), sp.Rational(1, 1))
    return sp.cancel(central + upper)


@lru_cache(maxsize=None)
def _associated_product(left_ell: int, right_ell: int, m: int) -> sp.Expr:
    left = sp.diff(sp.legendre(left_ell, _X), _X, m)
    right = sp.diff(sp.legendre(right_ell, _X), _X, m)
    return sp.expand((1 - _X**2) ** m * left * right)


@lru_cache(maxsize=None)
def _coupling_exact(left_ell: int, right_ell: int, m: int) -> sp.Expr:
    if left_ell < m or right_ell < m:
        return sp.Integer(0)
    normalization = sp.sqrt(
        sp.Rational(
            (2 * left_ell + 1)
            * (2 * right_ell + 1)
            * math.factorial(left_ell - m)
            * math.factorial(right_ell - m),
            math.factorial(left_ell + m) * math.factorial(right_ell + m),
        )
    )
    return sp.factor(
        sp.Rational(1, 2)
        * normalization
        * _wide_mask_integral(_associated_product(left_ell, right_ell, m))
    )


def _boost_a(ell: int, m: int) -> sp.Expr:
    return sp.sqrt(
        sp.Rational(ell * ell - m * m, (2 * ell - 1) * (2 * ell + 1))
    )


@lru_cache(maxsize=None)
def _exact_z_block(m: int, source_cutoff: int) -> tuple[sp.Matrix, sp.Matrix, sp.Matrix]:
    if not 0 <= m <= 5:
        raise ValueError("m is outside the retained block registry")
    if source_cutoff < 7:
        raise ValueError("source cutoff is outside its domain")
    fit_ells = tuple(range(m, 6))
    source_ells = tuple(range(7, source_cutoff + 1))
    normal = sp.Matrix(
        [[_coupling_exact(a, b, m) for b in fit_ells] for a in fit_ells]
    )
    rhs = sp.Matrix(
        [
            [
                -source_ell
                * _boost_a(source_ell, m)
                * _coupling_exact(fit_ell, source_ell - 1, m)
                + (source_ell + 1)
                * _boost_a(source_ell + 1, m)
                * _coupling_exact(fit_ell, source_ell + 1, m)
                for source_ell in source_ells
            ]
            for fit_ell in fit_ells
        ]
    )
    solved = normal.inv() * rhs
    retained_rows = [index for index, ell in enumerate(fit_ells) if ell >= 2]
    retained = solved.extract(retained_rows, range(len(source_ells)))
    return normal, rhs, retained


def _pivot_minor_record(m: int, source_cutoff: int) -> dict[str, Any]:
    normal, _rhs, retained = _exact_z_block(m, source_cutoff)
    rows = retained.rows
    if retained.cols < rows:
        return {
            "m": m,
            "row_count": rows,
            "pivot_source_ells": [],
            "determinant_nonzero": False,
            "determinant_squared": "0",
            "normal_determinant": str(sp.factor(normal.det())),
        }
    pivot_columns = tuple(range(rows))
    minor = retained.extract(range(rows), pivot_columns)
    determinant = sp.factor(minor.det())
    determinant_squared = sp.factor(sp.cancel(determinant * determinant))
    nonzero = determinant != 0 and determinant_squared != 0
    return {
        "m": m,
        "row_count": rows,
        "pivot_columns": list(pivot_columns),
        "pivot_source_ells": [7 + item for item in pivot_columns],
        "determinant_nonzero": bool(nonzero),
        "determinant_squared": str(determinant_squared),
        "determinant_squared_numeric_50d": str(sp.N(determinant_squared, 50)),
        "normal_determinant": str(sp.factor(normal.det())),
    }


def sympy_exact_z_block_certificate(source_cutoff: int = 12) -> dict[str, Any]:
    records = [_pivot_minor_record(m, source_cutoff) for m in range(6)]
    ranks = [record["row_count"] if record["determinant_nonzero"] else 0 for record in records]
    real_rank = ranks[0] + 2 * sum(ranks[1:])
    expected = list(_EXPECTED_L12_COMPLEX_BLOCK_RANKS)
    status = (
        "PASS"
        if source_cutoff == 12
        and ranks == expected
        and real_rank == 32
        and all(record["determinant_nonzero"] for record in records)
        else "FAIL"
    )
    return {
        "status": status,
        "source_cutoff": source_cutoff,
        "complex_block_ranks": ranks,
        "real_stored_rank": real_rank,
        "pivot_minors": records,
        "method": "exact_rational_polynomial_integrals_and_algebraic_minors",
    }


def _sympy_to_arb(expr: sp.Expr):
    from flint import arb

    value = sp.factor(expr)
    if value.is_Integer:
        return arb(int(value))
    if value.is_Rational:
        return arb(int(value.p)) / arb(int(value.q))
    if value.is_Add:
        result = arb(0)
        for term in value.args:
            result += _sympy_to_arb(term)
        return result
    if value.is_Mul:
        result = arb(1)
        for factor in value.args:
            result *= _sympy_to_arb(factor)
        return result
    if value.is_Pow:
        base, exponent = value.as_base_exp()
        if exponent.is_Integer:
            return _sympy_to_arb(base) ** int(exponent)
        if exponent == sp.Rational(1, 2):
            return _sympy_to_arb(base).sqrt()
        if exponent == sp.Rational(-1, 2):
            return arb(1) / _sympy_to_arb(base).sqrt()
    raise TypeError(f"unsupported exact expression for Arb conversion: {value!r}")


def arb_pivot_minor_certificate(exact: dict[str, Any] | None = None) -> dict[str, Any]:
    from flint import arb, arb_mat, ctx

    if exact is None:
        exact = sympy_exact_z_block_certificate(12)
    source_cutoff = int(exact["source_cutoff"])
    previous_dps = ctx.dps
    ctx.dps = 150
    records: list[dict[str, Any]] = []
    try:
        for m in range(6):
            _normal, _rhs, retained = _exact_z_block(m, source_cutoff)
            rows = retained.rows
            minor = retained.extract(range(rows), range(rows))
            ball_matrix = arb_mat(
                [[_sympy_to_arb(minor[i, j]) for j in range(rows)] for i in range(rows)]
            )
            determinant_ball = ball_matrix.det()
            determinant_squared_ball = determinant_ball * determinant_ball
            determinant_squared_exact = sp.factor(sp.cancel(minor.det() ** 2))
            if not determinant_squared_exact.is_Rational:
                raise RuntimeError("pivot-minor determinant square is not rational")
            target = arb(int(determinant_squared_exact.p)) / arb(
                int(determinant_squared_exact.q)
            )
            contains_zero = bool(determinant_ball.contains(0))
            square_contains_exact = bool(determinant_squared_ball.contains(target))
            records.append(
                {
                    "m": m,
                    "dimension": rows,
                    "contains_zero": contains_zero,
                    "square_contains_exact_rational": square_contains_exact,
                    "determinant_ball": determinant_ball.str(40),
                    "determinant_squared_ball": determinant_squared_ball.str(40),
                }
            )
    finally:
        ctx.dps = previous_dps

    status = (
        "PASS"
        if len(records) == 6
        and all(not item["contains_zero"] for item in records)
        and all(item["square_contains_exact_rational"] for item in records)
        else "FAIL"
    )
    return {
        "status": status,
        "minor_count": len(records),
        "precision_decimal_digits": 150,
        "minors": records,
        "method": "python_flint_arb_mat_determinant_of_exact_algebraic_entries",
    }


def _ducc_standard_gl(n: int) -> tuple[np.ndarray, np.ndarray]:
    import ducc0.misc as dmisc

    theta = np.asarray(dmisc.GL_thetas(n), dtype=np.float64)
    nodes = np.cos(theta)
    raw_weights = np.asarray(dmisc.GL_weights(n, 1), dtype=np.float64)
    if raw_weights.shape != nodes.shape:
        raise RuntimeError("DUCC Gauss-Legendre node/weight shapes differ")
    weights = raw_weights * (2.0 / float(np.sum(raw_weights)))
    return nodes, weights


def _segmented_ducc_nodes(n: int = 48) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    base_nodes, base_weights = _ducc_standard_gl(n)
    segments = ((-0.75, 0.75), (0.75, 1.0))
    nodes: list[np.ndarray] = []
    weights: list[np.ndarray] = []
    mask_values: list[np.ndarray] = []
    for lower, upper in segments:
        mapped = 0.5 * (upper - lower) * base_nodes + 0.5 * (upper + lower)
        mapped_weights = 0.5 * (upper - lower) * base_weights
        if lower < 0.0:
            mask = 0.5 + (2.0 / 3.0) * mapped
        else:
            mask = np.ones_like(mapped)
        nodes.append(mapped)
        weights.append(mapped_weights)
        mask_values.append(mask)
    return np.concatenate(nodes), np.concatenate(weights), np.concatenate(mask_values)


def _coupling_numeric(
    left_ell: int,
    right_ell: int,
    m: int,
    nodes: np.ndarray,
    weights: np.ndarray,
    mask: np.ndarray,
) -> float:
    from scipy.special import lpmv

    if left_ell < m or right_ell < m:
        return 0.0
    prefactor = 0.5 * math.sqrt(
        (2 * left_ell + 1)
        * (2 * right_ell + 1)
        * math.factorial(left_ell - m)
        * math.factorial(right_ell - m)
        / (math.factorial(left_ell + m) * math.factorial(right_ell + m))
    )
    product = lpmv(m, left_ell, nodes) * lpmv(m, right_ell, nodes)
    return float(prefactor * np.sum(weights * mask * product))


def ducc_z_quadrature_certificate(source_cutoff: int = 12) -> dict[str, Any]:
    nodes, weights, mask = _segmented_ducc_nodes(48)
    all_singular: list[float] = []
    maximum_normal_residual = 0.0
    block_records: list[dict[str, Any]] = []
    for m in range(6):
        fit_ells = tuple(range(m, 6))
        source_ells = tuple(range(7, source_cutoff + 1))
        normal = np.asarray(
            [
                [_coupling_numeric(a, b, m, nodes, weights, mask) for b in fit_ells]
                for a in fit_ells
            ],
            dtype=np.float64,
        )
        rhs = np.asarray(
            [
                [
                    -source_ell
                    * math.sqrt(
                        (source_ell * source_ell - m * m)
                        / ((2 * source_ell - 1) * (2 * source_ell + 1))
                    )
                    * _coupling_numeric(
                        fit_ell, source_ell - 1, m, nodes, weights, mask
                    )
                    + (source_ell + 1)
                    * math.sqrt(
                        (((source_ell + 1) ** 2 - m * m))
                        / ((2 * source_ell + 1) * (2 * source_ell + 3))
                    )
                    * _coupling_numeric(
                        fit_ell, source_ell + 1, m, nodes, weights, mask
                    )
                    for source_ell in source_ells
                ]
                for fit_ell in fit_ells
            ],
            dtype=np.float64,
        )
        exact_normal, _exact_rhs, _exact_retained = _exact_z_block(m, source_cutoff)
        exact_normal_float = np.asarray(exact_normal.evalf(50), dtype=np.float64)
        denominator = max(float(np.linalg.norm(exact_normal_float)), np.finfo(float).tiny)
        normal_residual = float(np.linalg.norm(normal - exact_normal_float) / denominator)
        maximum_normal_residual = max(maximum_normal_residual, normal_residual)
        solved = np.linalg.solve(normal, rhs)
        retained_rows = [index for index, ell in enumerate(fit_ells) if ell >= 2]
        retained = solved[retained_rows, :]
        singular = np.linalg.svd(retained, compute_uv=False)
        if m == 0:
            all_singular.extend(float(item) for item in singular)
        else:
            for item in singular:
                all_singular.extend((float(item), float(item)))
        block_records.append(
            {
                "m": m,
                "rank": int(np.count_nonzero(singular > 1.0e-12)),
                "smallest_singular_value": float(singular[-1]),
                "largest_singular_value": float(singular[0]),
                "normal_matrix_relative_residual": normal_residual,
            }
        )
    spectrum = np.sort(np.asarray(all_singular, dtype=np.float64))[::-1]
    smallest = float(spectrum[-1])
    relative_smallest = abs(smallest - WOLFRAM_Z_L12_SMALLEST_SINGULAR) / abs(
        WOLFRAM_Z_L12_SMALLEST_SINGULAR
    )
    rank = int(np.count_nonzero(spectrum > 1.0e-12))
    status = (
        "PASS"
        if rank == 32
        and relative_smallest <= 2.0e-7
        and maximum_normal_residual <= 2.0e-11
        else "FAIL"
    )
    return {
        "status": status,
        "source_cutoff": source_cutoff,
        "real_stored_rank": rank,
        "smallest_singular_value": smallest,
        "wolfram_reference_smallest_singular_value": WOLFRAM_Z_L12_SMALLEST_SINGULAR,
        "relative_smallest_singular_residual": relative_smallest,
        "normal_matrix_relative_residual": maximum_normal_residual,
        "quadrature": "ducc0_GL_thetas_GL_weights_segmented_at_mask_breakpoints",
        "segment_node_count": 48,
        "block_records": block_records,
    }


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
    )


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_external_verifier_artifacts(output: Path | str) -> dict[str, Any]:
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=True)
    versions = package_versions()
    wigner = validate_wigner_symbols()
    exact = sympy_exact_z_block_certificate(12)
    arb = arb_pivot_minor_certificate(exact)
    quadrature = ducc_z_quadrature_certificate(12)
    axes = {
        "package_versions": versions["status"],
        "wigner_three_way": wigner["status"],
        "sympy_exact_rank": exact["status"],
        "arb_pivot_minors": arb["status"],
        "ducc_quadrature": quadrature["status"],
    }
    status = (
        "PASS_EXTERNAL_VERIFIER_AXES"
        if all(value == "PASS" for value in axes.values())
        else "FAIL_EXTERNAL_VERIFIER_AXIS"
    )
    summary = {
        "schema": "HTT_WU011_TASK7C_EXTERNAL_VERIFIER_SUMMARY_V1",
        "status": status,
        "axes": axes,
        "z_direction_continuum_full_row_rank": exact["real_stored_rank"] == 32,
        "other_directions_certified": False,
        "healpix_bridge_certified": False,
        "scientific_terminal_authorized": False,
        "claim_promotion": False,
        "merge_authorized": False,
    }
    _write_json(destination / "package_versions.json", versions)
    _write_json(destination / "wigner_crosscheck.json", wigner)
    _write_json(destination / "sympy_exact_block_ranks.json", exact)
    _write_json(destination / "arb_pivot_minor_certificate.json", arb)
    _write_json(destination / "ducc_quadrature_crosscheck.json", quadrature)
    _write_json(destination / "external_verifier_summary.json", summary)
    files = sorted(path for path in destination.iterdir() if path.is_file())
    (destination / "SHA256SUMS").write_text(
        "\n".join(f"{_sha256(path)}  {path.name}" for path in files) + "\n",
        encoding="ascii",
    )
    if status != "PASS_EXTERNAL_VERIFIER_AXES":
        raise RuntimeError(f"external verifier failure: {axes}")
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = write_external_verifier_artifacts(args.output)
    print("EXTERNAL_VERIFIER_STATUS", summary["status"])
    print("Z_DIRECTION_CONTINUUM_FULL_ROW_RANK", summary["z_direction_continuum_full_row_rank"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
