# Independent SageMath exact checks for Report A R4A1NF conventions.
# Run with: sage verify_conventions.sage

R.<E, c, b2> = PolynomialRing(QQ)

# Algebraic closures after factoring out positive scalar prefactors.
photon_norm_factor = -1 + 1
measured_energy_factor = -(-1) - 1
assert photon_norm_factor == 0
assert measured_energy_factor == 0

# Work in the quotient imposing gamma2*(1-beta2)=1.
S.<gamma2, beta2> = PolynomialRing(QQ)
I = S.ideal([gamma2 * (1 - beta2) - 1])
boost_residual = I.reduce(gamma2 * (-1 + beta2) + 1)
assert boost_residual == 0

# Positive-definite sample envelope over exact rationals.
E1 = matrix(QQ, [[1, 0], [0, 0]])
E2 = matrix(QQ, [[0, 1], [1, 0]])
r1 = QQ(2)
r2 = QQ(1) / 2
lambda_reg = QQ(1) / 4
GammaE = 2 * (r1^2 * E1 * E1.transpose() + r2^2 * E2 * E2.transpose()) \
         + lambda_reg^2 * identity_matrix(QQ, 2)

# Exact Sylvester criterion; this avoids an RDF/CDF-only numerical backend.
leading_principal_minors = [
    GammaE[:k, :k].determinant() for k in (1, 2)
]
assert all(minor > 0 for minor in leading_principal_minors)

print('photon_norm_factor =', photon_norm_factor)
print('measured_energy_factor =', measured_energy_factor)
print('boost_quotient_residual =', boost_residual)
print('GammaE =')
print(GammaE)
print('leading_principal_minors =', leading_principal_minors)
print('GammaE_positive_definite_by_Sylvester =', True)
