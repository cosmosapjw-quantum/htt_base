# CAS-15-C03 Sage + Singular finite component

The admitted domain is real symmetric `M,Mhat`, real skew `W,What`, Frobenius
norms unless `op` is written, `delta>0` for the exact inverse, `deltahat>0` for
the fitted inverse, and nonnegative `epsilon_R,epsilon_M,Wstar`. All frames and
units are inherited from `COMMON_SPEC.md`; this is a rest-frame Euclidean
matrix statement and uses no indefinite Lorentz norm. No sign choice of an
eigenvector matters. Eigenvalues are ordered increasingly for the perturbation
claim.

In an orthonormal eigenbasis of `M=diag(m1,m2,m3)`, write a skew matrix with
independent coordinates `x12,x13,x23`, so `Xji=-Xij`. Direct multiplication
gives `[M,X]ij=(mi-mj)Xij`, `[M,X]ii=0`, and a symmetric output. Relative to
orthonormal bases `Fij=(Eij-Eji)/sqrt(2)` in `so(3)` and
`Sij=(Eij+Eji)/sqrt(2)` in the symmetric off-diagonal space, the map is the
diagonal matrix with entries `m1-m2,m1-m3,m2-m3`. Thus its rank is three and
its kernel zero when `delta=min(i<j)|mi-mj|>0`. Its exact singular values are
the three absolute gaps, so `||[M,X]||F >= delta ||X||F`. For an exact
`R=[M,W]`, all diagonal entries of `R` vanish, and
`Wij=Rij/(mi-mj)`, `Wii=0`. Also `R` must be symmetric; the diagonal condition
alone is not sufficient if an arbitrary matrix is offered as an exact residual.

For `Mhat` with distinct eigenvalues, the image of `Lhat:X->[Mhat,X]` is
exactly the symmetric zero-diagonal subspace in its eigenbasis. Let `P` be
Frobenius orthogonal projection onto that subspace:
`P(Rhat)ij=(Rhatij+Rhatji)/2` for `i!=j`, with zero diagonal. Completing
squares in all nine entries gives

`||Lhat(X)-Rhat||F^2 = 2 sum(i<j)((lambdai-lambdaj) Xij - P(Rhat)ij)^2 + sum(i) Rhat_ii^2 + (1/2) sum(i<j)(Rhat_ij-Rhat_ji)^2`.

Because every gap is nonzero, the unique least-squares minimizer is
`What_ij=P(Rhat)ij/(lambdai-lambdaj)`. The diagonal and antisymmetric
residuals are retained in the minimum; they are not fitted away. Projection
nonexpansiveness and `R=[M,W]` yield

`Lhat(What-W)=P(Rhat-Lhat(W))=P((Rhat-R)-[Mhat-M,W])`.

The exact gap inequality for `Lhat` and the triangle inequality imply
`deltahat ||What-W||F <= ||Rhat-R||F + ||[Mhat-M,W]||F`. For any real
matrix `D`, the Frobenius/operator submultiplicativity inequalities give
`||DW-WD||F <= ||DW||F+||WD||F <= 2||D||op||W||F`. Under the admitted
bounds, division by `deltahat>0` proves
`||What-W||F <= (epsilon_R+2 epsilon_M Wstar)/deltahat`.
No division is made at zero gap.

For ordered eigenvalues of real symmetric `M` and `Mhat`, the min-max
characterization of each eigenvalue and
`-epsilon_M I <= Mhat-M <= epsilon_M I` imply
`|lambdahat_i-lambda_i| <= epsilon_M` for each `i`. For every `i<j`, the
reverse triangle inequality gives
`|lambdahat_i-lambdahat_j| >= |lambda_i-lambda_j|-2epsilon_M`.
Taking the minimum proves `deltahat >= delta-2epsilon_M`. This lower bound
may be nonpositive; the fitted inverse separately requires `deltahat>0`.

When two eigenvalues coincide, the associated `Fij` is a nonzero kernel
element, so a `1/delta` inverse is unavailable. If all three coincide, the
commutator map is zero. These controls and the diagonal residual are exact
finite statements. They do not establish CAS15 C01/C02, sphere integration
by parts, photon transport/measurement, or any scientific admission.
