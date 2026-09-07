#!/usr/bin/env python3
"""Check Appendix B using only its finite polynomial/rational formulae.

This is a document-specific exact-arithmetic check, not the old CAS harness,
not a finite-HEALPix calculation, and not a proof of a numerical error model.
No network, floating-point arithmetic or external mathematics package is used.
"""
from __future__ import annotations

import argparse
import json
import math
from fractions import Fraction as Q
from functools import lru_cache
from pathlib import Path

NORMAL = (
    '2371221567616482963655661538277/124939643158494289811515067921858560',
    '1784012728720795037550100553/1743019575313815427057966907392',
    '10945595347193184954026503331/871509787656907713528983453696',
    '104531461379720327/1585267068834414592',
    '665044625583572687/3170534137668829184',
    '1/2',
)
MINOR_SQUARED = (
    '13854851227718467321621702138503980744130367185396095166590753194419819749485140749388736644495507/2946385964528764001602729286917704836323445407941374503789674365768429551770231683936450693300224',
    '45897747416692690585791274614572327208356017181052125887012037607944001265218344300648587575/11439368869955288869320571209776405550745656790554396265529415077685155349137762741139313524736',
    '39493718757090374514153222808257755001282326150716790292260982205042519060828776367475925/215305412825852519355010761635586687254061841359588806014692042617344168936576686059039460687872',
    '3965156020663594870880515310630136258902710414400775484668459177/613649291260366690751581334535331511253026015611909498783126158409990144',
    '33648590107505417977636161099564743354425815/321031865290431140061490488646804497908163936256',
    '1654580299939355708034129/1995199839012425102786560',
)


def multiply(a: tuple[Q, ...], b: tuple[Q, ...]) -> tuple[Q, ...]:
    out = [Q(0)] * (len(a) + len(b) - 1)
    for i, ai in enumerate(a):
        for j, bj in enumerate(b):
            out[i + j] += ai * bj
    return tuple(out)


@lru_cache(None)
def derivative_legendre(ell: int, m: int) -> tuple[Q, ...]:
    if not 0 <= m <= ell:
        raise ValueError('Need 0 <= m <= ell')
    out = [Q(0)] * (ell + 1)
    for k in range(ell // 2 + 1):
        p = ell - 2 * k
        coefficient = Q((-1) ** k * math.factorial(2 * ell - 2 * k),
                        2 ** ell * math.factorial(k) * math.factorial(ell - k)
                        * math.factorial(p))
        out[p] = coefficient
    for _ in range(m):
        out = [(i + 1) * out[i + 1] for i in range(len(out) - 1)]
    return tuple(out)


@lru_cache(None)
def weight_moment(k: int) -> Q:
    if k < 0:
        raise ValueError('Moment degree must be nonnegative')
    a = Q(3, 4)
    return (Q(1, 2) * (a ** (k + 1) - (-a) ** (k + 1)) / (k + 1)
            + Q(2, 3) * (a ** (k + 2) - (-a) ** (k + 2)) / (k + 2)
            + (1 - a ** (k + 1)) / (k + 1))


@lru_cache(None)
def overlap(m: int, ell: int, p: int) -> Q:
    factor = (Q(1),)
    for _ in range(m):
        factor = multiply(factor, (Q(1), Q(0), Q(-1)))
    polynomial = multiply(factor, multiply(derivative_legendre(ell, m),
                                           derivative_legendre(p, m)))
    return sum((a * weight_moment(k) for k, a in enumerate(polynomial)), Q(0))


def scale(ell: int, m: int) -> Q:
    return Q((2 * ell + 1) * math.factorial(ell - m),
             2 * math.factorial(ell + m))


def determinant(matrix: list[list[Q]]) -> Q:
    n = len(matrix)
    if any(len(row) != n for row in matrix):
        raise ValueError('Determinant needs a square matrix')
    a = [row[:] for row in matrix]
    value = Q(1)
    for k in range(n):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        if pivot is None:
            return Q(0)
        if pivot != k:
            a[k], a[pivot] = a[pivot], a[k]
            value = -value
        diagonal = a[k][k]
        value *= diagonal
        for i in range(k + 1, n):
            multiplier = a[i][k] / diagonal
            for j in range(k + 1, n):
                a[i][j] -= multiplier * a[k][j]
            a[i][k] = Q(0)
    return value


def solve(matrix: list[list[Q]], right: list[list[Q]]) -> list[list[Q]]:
    n = len(matrix)
    if len(right) != n or any(len(row) != n for row in matrix):
        raise ValueError('Incompatible exact solve')
    columns = len(right[0])
    if any(len(row) != columns for row in right):
        raise ValueError('Ragged right-hand side')
    a = [matrix[i][:] + right[i][:] for i in range(n)]
    for k in range(n):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        if pivot is None:
            raise ValueError('Singular exact normal matrix')
        a[k], a[pivot] = a[pivot], a[k]
        diagonal = a[k][k]
        a[k] = [x / diagonal for x in a[k]]
        for i in range(n):
            if i != k:
                multiplier = a[i][k]
                a[i] = [x - multiplier * y for x, y in zip(a[i], a[k])]
    return [row[n:] for row in a]


def product(xs: list[Q]) -> Q:
    result = Q(1)
    for x in xs:
        result *= x
    return result


def check() -> dict[str, object]:
    # Small arithmetic controls are not counted as tensor theorems.
    assert derivative_legendre(2, 0) == (Q(-1, 2), Q(0), Q(3, 2))
    assert derivative_legendre(3, 1) == (Q(-3, 2), Q(0), Q(15, 2))
    assert weight_moment(0) == 1 and weight_moment(1) == Q(13, 32)
    assert determinant([[Q(2), Q(1)], [Q(1), Q(2)]]) == 3
    rows: list[dict[str, object]] = []
    for m in range(6):
        fit = list(range(m, 6))
        retained = list(range(max(2, m), 6))
        sources = list(range(7, 7 + len(retained)))
        gram = [[overlap(m, ell, p) for p in fit] for ell in fit]
        # B_z P_p^m = a_plus P_(p+1)^m + a_minus P_(p-1)^m.
        response = [[Q((p + 1) * (p - m + 1), 2 * p + 1) * overlap(m, ell, p + 1)
                     - Q(p * (p + m), 2 * p + 1) * overlap(m, ell, p - 1)
                     for p in sources] for ell in fit]
        raw_response = solve(gram, response)
        raw_minor = [raw_response[fit.index(ell)] for ell in retained]
        normal_det = determinant(gram) * product([scale(ell, m) for ell in fit])
        minor_sq = (determinant(raw_minor) ** 2
                    * product([scale(p, m) for p in sources])
                    / product([scale(ell, m) for ell in retained]))
        rows.append({
            'm': m, 'fit_ell': fit, 'retained_ell': retained, 'source_ell': sources,
            'normal_determinant': str(normal_det),
            'normal_matches_printed': normal_det == Q(NORMAL[m]),
            'minor_squared': str(minor_sq),
            'minor_matches_printed': minor_sq == Q(MINOR_SQUARED[m]),
            'nonzero': normal_det != 0 and minor_sq != 0,
            'certified_complex_block_rank': len(retained) if minor_sq else None,
        })
    passed = all(r['normal_matches_printed'] and r['minor_matches_printed'] and r['nonzero'] for r in rows)
    real_rank = 4 + 2 * (4 + 4 + 3 + 2 + 1) if all(r['nonzero'] for r in rows) else None
    return {
        'operation': 'exact Fraction check of the newly printed finite certificate',
        'basis': 'unnormalised associated Legendre derivatives with explicit normalisation ratios',
        'arithmetic': 'rational only',
        'blocks': rows,
        'retained_real_dimension': 32,
        'certified_real_rank': real_rank,
        'printed_certificate_matches': passed,
        'finite_HEALPix_verified': False,
        'physical_or_observational_inference': False,
        'overall': 'PASS_PRINTED_AXIAL_CERTIFICATE' if passed else 'NONPASS_PRINTED_CERTIFICATE_COMPARISON',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(f'Refusing to overwrite {args.out}')
    result = check()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0 if result['printed_certificate_matches'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
