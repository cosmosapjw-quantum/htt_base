"""Independent Sage 10.9 algebra for the frozen CAS-15-C04 component."""
import json
import subprocess
from pathlib import Path

from sage.all import QQ, PolynomialRing, identity_matrix, matrix, vector

HERE = Path(__file__).resolve().parent
SINGULAR = Path('/home/cosmosapjw/opt/sage/local/bin/Singular')


def comm(A, B):
    return A * B - B * A


def frob(A, B):
    return sum(A[i, j] * B[i, j] for i in range(3) for j in range(3))


def skew_basis(R):
    # E_i are generators of v x x.  The orthonormal basis is E_i/sqrt(2),
    # so every Gram entry below is half the integer-basis Frobenius pairing.
    return (
        matrix(R, [[0, 0, 0], [0, 0, -1], [0, 1, 0]]),
        matrix(R, [[0, 0, 1], [0, 0, 0], [-1, 0, 0]]),
        matrix(R, [[0, -1, 0], [1, 0, 0], [0, 0, 0]]),
    )


def response_gram(channels, E):
    R = E[0].base_ring()
    return matrix(R, 3, 3, lambda i, j: sum(
        frob(comm(M, E[i]), comm(M, E[j])) / 2 for M in channels
    ))


def assert_zero_mod(A, I, label):
    for i in range(A.nrows()):
        for j in range(A.ncols()):
            r = I.reduce(A[i, j])
            if r != 0:
                raise AssertionError(f'{label}[{i},{j}] residual {r}')


checks = {}

# An arbitrary real symmetric channel: the displayed response Gram is the
# actual Frobenius Gram, entry by entry.  Its kernel equality follows from
# v^T G v = sum_a ||[M_a,W(v)]||_F^2 / 2 over real matrices.
R0 = PolynomialRing(QQ, names=('m00', 'm11', 'm22', 'm01', 'm02', 'm12'))
m00, m11, m22, m01, m02, m12 = R0.gens()
M0 = matrix(R0, [[m00, m01, m02], [m01, m11, m12], [m02, m12, m22]])
E0 = skew_basis(R0)
G0 = response_gram((M0,), E0)
for i in range(3):
    for j in range(3):
        expected = frob(comm(M0, E0[i]), comm(M0, E0[j])) / 2
        assert G0[i, j] == expected
assert G0 == G0.transpose()
checks['generic_gram_identity'] = True

# Universal axisymmetric channel, with only the admitted unit relation.
R = PolynomialRing(QQ, names=('alpha', 'beta', 'nx', 'ny', 'nz'))
alpha, beta, nx, ny, nz = R.gens()
n = vector(R, [nx, ny, nz])
M = alpha * identity_matrix(R, 3) + beta * (n.column() * n.row())
E = skew_basis(R)
I = R.ideal(nx * nx + ny * ny + nz * nz - 1)
G = response_gram((M,), E)
expected = matrix(R, 3, 3, lambda i, j: beta * beta * (int(i == j) - n[i] * n[j]))
assert_zero_mod(G - expected, I, 'axis_gram')
for Ei in E:
    w = Ei * n
    # [M,W]=-beta(n(Wn)^T+(Wn)n^T); Wn=0 iff the commutator is 0
    # because the latter matrix applied to n equals -beta Wn.
    predicted = -beta * (n.column() * w.row() + w.column() * n.row())
    assert_zero_mod(comm(M, Ei) - predicted, I, 'axis_commutator')
checks['axis_commutator_and_gram'] = True

# Rank controls and exact two-axis determinant after rotating the pair to
# n1=e3, n2=(s,0,t), s^2+t^2=1.  An orthogonal coordinate change preserves
# Frobenius products and the dimension of the common skew commutant.
R2 = PolynomialRing(QQ, names=('a1', 'a2', 'b1', 'b2', 's', 't'))
a1, a2, b1, b2, s, t = R2.gens()
e3 = vector(R2, [0, 0, 1])
n2 = vector(R2, [s, 0, t])
M1 = a1 * identity_matrix(R2, 3) + b1 * (e3.column() * e3.row())
M2 = a2 * identity_matrix(R2, 3) + b2 * (n2.column() * n2.row())
E2 = skew_basis(R2)
G1 = response_gram((M1,), E2)
assert G1 == matrix(R2, [[b1*b1,0,0],[0,b1*b1,0],[0,0,0]])
assert G1.change_ring(R2.fraction_field()).rank() == 2
assert G1.subs({b1: 0}) == matrix(R2, 3, 3)
checks['single_axis_rank_and_isotropic_zero'] = True

G12 = response_gram((M1, M2), E2)
I2 = R2.ideal(s*s + t*t - 1)
expected12 = matrix(R2, [
    [b1*b1 + b2*b2*t*t, 0, -b2*b2*s*t],
    [0, b1*b1 + b2*b2, 0],
    [-b2*b2*s*t, 0, b2*b2*s*s],
])
assert_zero_mod(G12 - expected12, I2, 'stacked_gram')
assert I2.reduce(G12.det() - b1*b1*b2*b2*s*s*(b1*b1+b2*b2)) == 0
assert G12.subs({s:0,t:1}).change_ring(R2.fraction_field()).rank() == 2
assert G12.subs({s:0,t:-1}).change_ring(R2.fraction_field()).rank() == 2
checks['two_axis_determinant_and_parallel_control'] = True

# The pinned Singular executable performs a separate exact polynomial check.
singular_argv = [str(SINGULAR), '-q', str(HERE / 'check.sing')]
p = subprocess.run(singular_argv, cwd=HERE, text=True, capture_output=True, timeout=300)
(HERE / 'singular_stdout.log').write_text(p.stdout)
(HERE / 'singular_stderr.log').write_text(p.stderr)
if p.returncode != 0 or p.stderr.strip() or '// **' in p.stdout or '? ' in p.stdout:
    raise RuntimeError(f'Singular diagnostic failure: exit={p.returncode}, stdout={p.stdout!r}, stderr={p.stderr!r}')
required = {
    'SINGULAR_VERSION=44100',
    'DET_REMAINDER=0',
    'PARALLEL_DET=0',
    'LEADING_TWO_REMAINDER=0',
}
if not required.issubset(set(p.stdout.splitlines())):
    raise RuntimeError(f'Singular exact certificate missing: {p.stdout!r}')
checks['singular_polynomial_certificate'] = True

print(json.dumps({'checks': checks, 'singular_argv': singular_argv, 'singular_exit_code': p.returncode}, sort_keys=True))
