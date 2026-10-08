# CAS-07-C02, independent SageMath and Singular axis

Let `A=D-sI`, `r=s eta`, `m=s-r`, `M=s+r`.  The only supplied matrix
inequality is the **Euclidean induced** operator bound `||A||op <= r`.
By its supplied definition, for every `x` in Euclidean `R^2`,
`||Ax|| <= r||x||`.  The unit-sphere supremum and this all-vector form
are equivalent by homogeneity (`x=0` separately).  In particular
`q=||Ax||^2 <= r^2 n`, where `n=||x||^2`.

The exact Sage and Singular Lagrange certificates give
`n q-p^2=(u(Av)_2-v(Av)_1)^2 >= 0`, with `p=x dot Ax`.
For `x != 0`, set `t=sqrt(n q)`.  Then `0<=t<=r n` and `-t<=p<=t`.
The Gram expansion certificate gives
`||Dx||^2=s^2 n+2s p+q`.  Its upper gap is exactly
`M^2 n-||Dx||^2=2s(rn-p)+(r^2 n-q)>=0`.
For the lower gap, Sage certifies modulo `t^2=nq` that
`n(||Dx||^2-m^2 n)=2sn(p+t)+(rn-t)((2s-r)n-t)>=0`.
Both factors in the last product are nonnegative: `t<=rn` and
`(2s-r)n-t >= 2(s-r)n>0` because `s>r`.
For `x=0`, both bounds are equality.  Thus `m^2||x||^2 <=
||Dx||^2 <= M^2||x||^2` universally.  `D^T D` is real symmetric,
so the real spectral theorem supplies an orthonormal eigenbasis.
For each nonzero eigenvector the displayed Rayleigh inequality gives
`m^2<=lambda_i<=M^2`.  Since singular values are the nonnegative
square roots of these eigenvalues and `m>0`, **both** lie in `[m,M]`.

Determinant sign follows independently.  `B=(D+D^T)/2` satisfies
`x^T B x=s n+p >=(s-r)n=m n`, so it is positive definite for arbitrary
real (including nonsymmetric) `D`.  Its `B11>=m>0`.  For the nonzero
vector `w=(-B12,B11)`, Sage certifies `w^T B w=B11 det(B)`, hence
`det(B)>0`.  Sage and Singular certify
`det(D)=det(B)+((D12-D21)/2)^2>0`.  The positive root `sqrt(det D)`
therefore exists.  The Gram determinant certificate gives
`det(D^T D)=det(D)^2`; hence the product of the two singular values
equals `|detD|=detD`.  Their individual interval bounds imply
`m^2<=detD<=M^2`, so `m<=sqrt(detD)<=M` on the positive branch.

No diagonal, symmetry, SPD, eigenvalue, determinant-sign, singular-value,
or target bound is an input premise.  `eta=0` forces `A=0` by the norm
definition.  `eta<1` is essential for `m>0`; no assertion is made at
`eta=1`.  These are exact algebraic certificates plus explicitly stated
standard Euclidean order/spectral consequences, not finite samples.
