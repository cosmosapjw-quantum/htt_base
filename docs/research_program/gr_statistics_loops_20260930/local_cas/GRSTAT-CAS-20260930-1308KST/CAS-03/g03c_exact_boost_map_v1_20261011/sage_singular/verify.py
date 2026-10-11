"""Exact finite boost-map checks for G03-C; execute with sage -python."""

from sage.all import PolynomialRing, QQ, matrix, vector

names = ["g", "a", "b0", "b1", "b2", "n0", "n1", "n2",
         "d00", "d01", "d02", "d11", "d12", "d22"]
R = PolynomialRing(QQ, names=names, order="degrevlex")
g, a, b0, b1, b2, n0, n1, n2, d00, d01, d02, d11, d12, d22 = R.gens()
b = vector(R, [b0, b1, b2])
n = vector(R, [n0, n1, n2])
q = b.dot_product(b)
D = matrix(R, [[d00, d01, d02], [d01, d11, d12], [d02, d12, d22]])
eta = matrix(R, 4, 4, lambda i, j: -1 if i == j == 0 else (1 if i == j else 0))
L = matrix(R, 4, 4, lambda i, j:
           g if i == j == 0 else
           g * b[j - 1] if i == 0 else
           g * b[i - 1] if j == 0 else
           (1 if i == j else 0) + a * b[i - 1] * b[j - 1])
restB = matrix(R, 4, 4, lambda i, j: D[i - 1, j - 1] if i and j else 0)
J = R.ideal(g**2 * (1 - q) - 1, a * (g + 1) - g**2)
gb = J.groebner_basis()

checks = {}
checks["boostA_q"] = a * q - (g - 1)
checks["redshift"] = -(L * vector(R, [-1, n0, n1, n2]))[0] - g * (1 - b.dot_product(n))
for i in range(4):
    for j in range(4):
        checks[f"lorentz_{i}{j}"] = (L.transpose() * eta * L - eta)[i, j]
boostedB = L.transpose() * restB * L
S = b.dot_product(D * b)
for i in range(3):
    checks[f"dipole_{i}"] = -2 * boostedB[0, i + 1] + 2 * g * ((D * b)[i] + a * b[i] * S)

failures = []
for label, poly in checks.items():
    remainder = R(poly).reduce(gb)
    print(f"{label}: remainder={remainder}")
    if remainder != 0:
        failures.append(label)
print(f"ideal_generators={[str(x) for x in J.gens()]}")
print(f"groebner_basis_size={len(gb)} checks={len(checks)} failures={failures}")
if failures:
    raise SystemExit(1)
