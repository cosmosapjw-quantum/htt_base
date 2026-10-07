# CAS-15-C04 Sage+Singular proof scope

The admitted space is real Euclidean three-space.  Let `E_i` be the
orthonormal skew basis obtained by dividing the standard cross-product
generators by `sqrt(2)`.  For a finite stack of real symmetric matrices
`M_a`, let `L(W)=([M_a,W])_a`.  Direct Frobenius expansion gives

`G_ij = sum_a <[M_a,E_i],[M_a,E_j]>_F`.

For any real coefficient vector `v`, with `W=sum_i v_i E_i`,
`v^T G v=sum_a ||[M_a,W]||_F^2`.  Every summand is nonnegative, so
`v in ker G` if and only if every commutator vanishes.  This argument
uses a finite sum and the positive Euclidean Frobenius norm.

For a unit axis `n`, `M=alpha I+beta n n^T`, `beta!=0`, and skew `W`,

`[M,W]=-beta(n(Wn)^T+(Wn)n^T)`.

Applying the right side to `n` gives `-beta Wn`, because `n^T Wn=0`.
Consequently `[M,W]=0` if and only if `Wn=0`.  A nonzero skew matrix
in three dimensions is a cross-product generator and has one-dimensional
kernel along its rotation axis.  Thus the skew commutant is precisely
the one-dimensional span of the generator about `n`.  The exact Gram
is `beta^2(I-n n^T)`, with eigenvalues `beta^2,beta^2,0`.

For nonparallel unit axes, a common skew commutant would have to be a
rotation about both axes, so it is zero.  Orthogonal covariance permits
`n1=e3`, `n2=(s,0,t)`, `s^2+t^2=1`, `s!=0`.  The stacked Gram in this
frame is

```
[[b1^2+b2^2*t^2, 0, -b2^2*s*t],
 [0, b1^2+b2^2, 0],
 [-b2^2*s*t, 0, b2^2*s^2]].
```

Its determinant is `b1^2*b2^2*s^2*(b1^2+b2^2)>0` for real nonzero
`b1,b2,s`.  As a Gram matrix it is positive semidefinite, and zero
kernel makes it positive definite with rank three.  The script also
checks `beta=0` (zero response), a single nonisotropic channel (rank
two), and parallel axes (rank two).  Singular checks the determinant
and parallel determinant as exact polynomial identities; its raw
diagnostics are inspected separately from its exit status.

This is only the contracted finite C04 algebra.  It does not establish
sphere integration by parts, photon transport, a measurement contract,
or scientific admission.
