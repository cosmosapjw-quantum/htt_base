"""Independent exact Sage proof for frozen CAS-03-C02.

This source uses only the frozen execution contract, admitted inputs, and
COMMON_SPEC.  Hyperbolic functions are represented by exact indeterminates
h=sinh(chi), q=cosh(chi) modulo q^2-h^2-1.
"""

import json

from sage.all import QQ, PolynomialRing, diagonal_matrix, matrix, vector


P = PolynomialRing(QQ, names=("epsilon", "b2", "b3", "h", "q", "n1", "n2", "n3"))
epsilon, b2, b3, h, q, n1, n2, n3 = P.gens()

K = vector(P, (-1, n1, n2, n3))
rchi_flat = vector(P, (-h, q, 0, 0))
rzero_flat = vector(P, (0, 1, 0, 0))
e2_flat = vector(P, (0, 0, 1, 0))
e3_flat = vector(P, (0, 0, 0, 1))


def outer(v):
    return v.column() * v.row()


B_chi = epsilon * outer(rchi_flat) + b2 * outer(e2_flat) + b3 * outer(e3_flat)
B_zero = epsilon * outer(rzero_flat) + b2 * outer(e2_flat) + b3 * outer(e3_flat)
value_chi = (K.row() * B_chi * K.column())[0, 0]
value_zero = (K.row() * B_zero * K.column())[0, 0]
family_difference = P(value_chi - value_zero)
target = epsilon * (h**2 + 2 * h * q * n1 + h**2 * n1**2)

hyperbolic = q**2 - h**2 - 1
sphere = n1**2 + n2**2 + n3**2 - 1
hyperbolic_basis = P.ideal((hyperbolic,)).groebner_basis()
combined_basis = P.ideal((hyperbolic, sphere)).groebner_basis()
remainder_hyperbolic = (family_difference - target).reduce(hyperbolic_basis)
remainder_combined = (family_difference - target).reduce(combined_basis)

# The chi=0 control is exact h=0, q=1.  Its spatial block must be diagonal.
chi_zero_block = B_zero.matrix_from_rows_and_columns((1, 2, 3), (1, 2, 3))
expected_block = diagonal_matrix(P, (epsilon, b2, b3))
chi_zero_exact = chi_zero_block == expected_block
chi_zero_difference = family_difference.subs({h: 0, q: 1})

# A rational function field makes each retained symbol generically nonzero.
# Setting a selected diagonal entry to literal zero therefore represents each
# exact zero/nonzero stratum without choosing numerical coefficient values.
CP = PolynomialRing(QQ, names=("epsilon", "b2", "b3"))
CF = CP.fraction_field()
ce, cb2, cb3 = map(CF, CP.gens())
coefficients = (ce, cb2, cb3)
labels = ("epsilon", "b2", "b3")


def stratum_record(mask):
    entries = tuple(coefficients[i] if mask[i] else CF.zero() for i in range(3))
    block = diagonal_matrix(CF, entries)
    expected_rank = sum(mask)
    expected_kernel = [
        vector(CF, tuple(1 if i == j else 0 for i in range(3)))
        for j in range(3)
        if not mask[j]
    ]
    actual_rank = block.rank()
    actual_nullity = 3 - actual_rank
    basis_annihilated = all(block * v == vector(CF, (0, 0, 0)) for v in expected_kernel)
    basis_independent = (
        not expected_kernel
        or matrix(CF, [list(v) for v in expected_kernel]).rank() == len(expected_kernel)
    )
    kernel_complete = (
        basis_annihilated
        and basis_independent
        and len(expected_kernel) == actual_nullity
    )
    name = "".join("N" if bit else "Z" for bit in mask)
    return {
        "name": name,
        "conditions": {labels[i]: ("nonzero" if mask[i] else "zero") for i in range(3)},
        "rank": int(actual_rank),
        "expected_rank": int(expected_rank),
        "kernel_dimension": int(actual_nullity),
        "expected_kernel_dimension": int(3 - expected_rank),
        "kernel_basis_coordinates": [list(map(str, v)) for v in expected_kernel],
        "basis_annihilated": bool(basis_annihilated),
        "basis_independent": bool(basis_independent),
        "kernel_complete": bool(kernel_complete),
        "pass": bool(actual_rank == expected_rank and kernel_complete),
    }


strata = []
for bits in range(8):
    mask = tuple(bool(bits & (1 << i)) for i in range(3))
    strata.append(stratum_record(mask))

repeated_nonzero = diagonal_matrix(CF, (ce, ce, CF.zero()))
repeated_control = {
    "rank": int(repeated_nonzero.rank()),
    "kernel_dimension": int(3 - repeated_nonzero.rank()),
    "pass": bool(repeated_nonzero.rank() == 2),
}
all_zero = diagonal_matrix(CF, (CF.zero(), CF.zero(), CF.zero()))
all_zero_control = {
    "rank": int(all_zero.rank()),
    "kernel_dimension": int(3 - all_zero.rank()),
    "pass": bool(all_zero.rank() == 0),
}

report = {
    "engine": "SageMath",
    "evidence_class": "exact",
    "family": {
        "value_chi": str(value_chi),
        "value_zero": str(value_zero),
        "difference_expanded": str(family_difference),
        "target": str(target),
        "hyperbolic_remainder": str(remainder_hyperbolic),
        "hyperbolic_and_sphere_remainder": str(remainder_combined),
        "pass": bool(remainder_hyperbolic == 0 and remainder_combined == 0),
    },
    "chi_zero": {
        "spatial_block": [[str(x) for x in row] for row in chi_zero_block.rows()],
        "difference": str(chi_zero_difference),
        "pass": bool(chi_zero_exact and chi_zero_difference == 0),
    },
    "rank_strata": strata,
    "repeated_nonzero_control": repeated_control,
    "all_zero_control": all_zero_control,
}
report["CAS-03-C02"] = bool(
    report["family"]["pass"]
    and report["chi_zero"]["pass"]
    and len(strata) == 8
    and all(item["pass"] for item in strata)
    and repeated_control["pass"]
    and all_zero_control["pass"]
)
print(json.dumps(report, sort_keys=True))
