"""Independent exact SageMath certificate for CAS-10-C02.

Permitted inputs are EXECUTION_CONTRACT.json, ADMITTED_INPUTS.json, and the
neutral COMMON_SPEC.md.  No sibling proof or result is used.
"""

from sage.all import QQ, PolynomialRing, diagonal_matrix, matrix, vector
from sage.version import version as sage_version


names = (
    "c", "u0", "u1", "u2", "u3",
    "s00", "s01", "s02", "s03", "s11", "s12", "s13", "s22", "s23", "s33",
)
R = PolynomialRing(QQ, names=names, order="degrevlex")
z = R.gens_dict()
c = z["c"]
u0, u1, u2, u3 = (z[f"u{i}"] for i in range(4))
s00, s01, s02, s03 = (z[f"s0{i}"] for i in range(4))
s11, s12, s13 = z["s11"], z["s12"], z["s13"]
s22, s23, s33 = z["s22"], z["s23"], z["s33"]

g = diagonal_matrix(R, [-1, 1, 1, 1])
u = vector(R, [u0, u1, u2, u3])
S = matrix(R, [
    [s00, s01, s02, s03],
    [s01, s11, s12, s13],
    [s02, s12, s22, s23],
    [s03, s13, s23, s33],
])

mass_shell = (u * g * u.column())[0] + 1
Su = S * u
h = (u * Su.column())[0]
b = Su + h * (g * u)
A = 2 * c * b
orth = (u * b.column())[0]
Jgeo = (Su * g * Su.column())[0] + h**2
b_norm = (b * g * b.column())[0]
A_norm = (A * g * A.column())[0]

I_mass = R.ideal([mass_shell])
gb_mass = I_mass.groebner_basis()

rem_orth = I_mass.reduce(orth)
rem_j_b = I_mass.reduce(Jgeo - b_norm)
rem_scale = A_norm - 4 * c**2 * b_norm

# For b orthogonal to unit timelike u, this gives an explicit positive
# rest-space certificate: u0^2 (b^T g^-1 b) is a sum of six real squares.
spatial_square = b[1]**2 + b[2]**2 + b[3]**2
wedge_squares = (
    (u1 * b[2] - u2 * b[1])**2
    + (u1 * b[3] - u3 * b[1])**2
    + (u2 * b[3] - u3 * b[2])**2
)
sos_numerator = spatial_square + wedge_squares
rem_sos = I_mass.reduce(u0**2 * b_norm - sos_numerator)

# Direct factor identities expose the quotient mechanism rather than merely
# reporting zero remainders.
factor_orth = orth - h * mass_shell
factor_j_b = b_norm - Jgeo - h**2 * mass_shell

checks = {
    "mass_shell_groebner_nonempty": len(gb_mass) == 1,
    "orthogonality_quotient": rem_orth == 0 and factor_orth == 0,
    "Jgeo_equals_b_norm": rem_j_b == 0 and factor_j_b == 0,
    "A_scaling": rem_scale == 0,
    "positive_rest_space_sos": rem_sos == 0,
}


def point(values):
    """Return a complete exact rational point substitution."""
    return {z[name]: QQ(values.get(name, 0)) for name in names}


S_sample = {
    "s00": 2, "s01": 1, "s02": -1, "s03": 3,
    "s11": 4, "s12": 2, "s13": -2,
    "s22": 5, "s23": 1, "s33": 6,
}
rest = point({"c": 2, "u0": 1, **S_sample})
boosted = point({"c": 3, "u0": QQ(5)/4, "u1": QQ(3)/4, **S_sample})
a_zero = point({
    "c": 2, "u0": QQ(5)/4, "u1": QQ(3)/4,
    "s00": -1, "s11": 1, "s22": 1, "s33": 1,
})


def target_residuals(p):
    return {
        "mass_shell": mass_shell.subs(p),
        "orthogonality": orth.subs(p),
        "Jgeo_minus_b_norm": (Jgeo - b_norm).subs(p),
        "A_norm_minus_4c2J": (A_norm - 4 * c**2 * Jgeo).subs(p),
    }


rest_residuals = target_residuals(rest)
boosted_residuals = target_residuals(boosted)
a_zero_residuals = target_residuals(a_zero)
a_zero_b = tuple(x.subs(a_zero) for x in b)
a_zero_A = tuple(x.subs(a_zero) for x in A)
a_zero_J = Jgeo.subs(a_zero)

# Exclusion controls.  Each is a genuine countermodel to the statement after
# deleting the named assumption.
c_zero = point({"c": 0, "u0": 1, "s01": 1})
c_zero_b = tuple(x.subs(c_zero) for x in b)
c_zero_A = tuple(x.subs(c_zero) for x in A)
c_zero_J = Jgeo.subs(c_zero)

nonunit = point({"c": 1, "u0": 2, "s00": 1})
nonunit_mass = mass_shell.subs(nonunit)
nonunit_orth = orth.subs(nonunit)

unconstrained_b = vector(QQ, [1, 0, 0, 0])
unconstrained_b_norm = (unconstrained_b * diagonal_matrix(QQ, [-1, 1, 1, 1]) * unconstrained_b.column())[0]

controls = {
    "c_zero_breaks_A_zero_iff_b_zero": c_zero_A == (0, 0, 0, 0) and c_zero_b != (0, 0, 0, 0) and c_zero_J == 1,
    "nonunit_breaks_orthogonality": nonunit_mass != 0 and nonunit_orth != 0,
    "lorentz_norm_not_positive_without_orthogonality": unconstrained_b_norm == -1,
    "nontrivial_S_A_zero_case": a_zero_b == (0, 0, 0, 0) and a_zero_A == (0, 0, 0, 0) and a_zero_J == 0,
    "rest_exact_vector": all(v == 0 for v in rest_residuals.values()),
    "boosted_rational_exact_vector": all(v == 0 for v in boosted_residuals.values()),
}

assert all(checks.values()), checks
assert all(controls.values()), controls

print("SAGE_DIAGNOSTICS_BEGIN")
print(f"sage_version=SageMath version {sage_version}")
print(f"coefficient_field={R.base_ring()}")
print(f"ring_generators={R.variable_names()}")
print(f"mass_shell_polynomial={mass_shell}")
print(f"mass_shell_groebner_basis={gb_mass}")
print(f"orth_minus_h_mass_shell={factor_orth}")
print(f"orth_remainder={rem_orth}")
print(f"b_norm_minus_Jgeo_minus_h2_mass_shell={factor_j_b}")
print(f"Jgeo_minus_b_norm_remainder={rem_j_b}")
print(f"A_norm_minus_4c2_b_norm={rem_scale}")
print(f"u0sq_b_norm_minus_sos_remainder={rem_sos}")
print("sos_certificate=u0^2*b_norm=b1^2+b2^2+b3^2+(u1*b2-u2*b1)^2+(u1*b3-u3*b1)^2+(u2*b3-u3*b2)^2")
print(f"rest_exact_residuals={rest_residuals}")
print(f"boosted_rational_exact_residuals={boosted_residuals}")
print(f"A_zero_control_b={a_zero_b};A={a_zero_A};Jgeo={a_zero_J}")
print(f"c_zero_control_b={c_zero_b};A={c_zero_A};Jgeo={c_zero_J}")
print(f"nonunit_control_mass_shell={nonunit_mass};orthogonality={nonunit_orth}")
print(f"unconstrained_timelike_covector_norm={unconstrained_b_norm}")
print(f"checks={checks}")
print(f"controls={controls}")
print("zero_locus_argument=u0^2=1+u1^2+u2^2+u3^2>0; SOS=0 forces b1=b2=b3=0; u^T b=0 and u0>0 force b0=0; c>0 makes A=0 iff b=0")
print("CAS-10-C02=PASS")
print("SAGE_DIAGNOSTICS_END")
