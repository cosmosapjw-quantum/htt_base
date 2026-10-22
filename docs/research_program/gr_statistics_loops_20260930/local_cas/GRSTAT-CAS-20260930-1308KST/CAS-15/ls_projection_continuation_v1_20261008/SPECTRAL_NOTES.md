# CAS15-C03 rotated spectral and ordered-eigenvalue bridges

Status: **DERIVED** for the two full real symmetric \(3\times3\) matrix statements below; **FORMALLY_CHECKED** only for the exact theorems in `Spectral.lean`. This is a component argument under the owner-adopted C03 input, not a new four-axis execution, scientific admission, or a claim about construction of \(M,\widehat M,R,\widehat R\).

## Assumptions and norms

Let \(M,\widehat M\in\mathbb R^{3\times3}\) be symmetric, \(X^T=-X\), and let \(\|\cdot\|_F\) be the square root of the sum of all nine squared entries. The operator norm \(\|A\|_{\mathrm{op}}=\sup_{\|v\|_2=1}\|Av\|_2\) is induced by the Euclidean vector norm. Put \(\varepsilon_M\ge0\) and assume \(\|\widehat M-M\|_{\mathrm{op}}\le\varepsilon_M\). Write the eigenvalues in **decreasing** order as \(\lambda_1\ge\lambda_2\ge\lambda_3\) and \(\widehat\lambda_1\ge\widehat\lambda_2\ge\widehat\lambda_3\). Define \(\delta=\min_{i<j}|\lambda_i-\lambda_j|=\min(\lambda_1-\lambda_2,\lambda_2-\lambda_3)\), and likewise \(\widehat\delta\). These are basis-independent spectral gaps. No simplicity is needed for the estimates; \(\widehat\delta>0\) is needed only when dividing by it.

## Rotated commutator coercivity

The real spectral theorem supplies an orthogonal \(U\) and \(D=\operatorname{diag}(\widehat\lambda_1,\widehat\lambda_2,\widehat\lambda_3)\) with \(\widehat M=UDU^T\). Put \(Y=U^TXU\). Then \(Y^T=-Y\). Orthogonal multiplication on both sides preserves the Frobenius norm because, for any \(Z\),
\[
\|UZU^T\|_F^2=\operatorname{tr}((UZU^T)^T(UZU^T))
=\operatorname{tr}(UZ^TZU^T)=\operatorname{tr}(Z^TZ)=\|Z\|_F^2.
\]
Also \([\widehat M,X]=U[D,Y]U^T\), where \([A,B]=AB-BA\). In the diagonal basis \([D,Y]_{ij}=(\widehat\lambda_i-\widehat\lambda_j)Y_{ij}\) and its diagonal is zero. Skewness pairs the off-diagonal entries, so
\[
\|[D,Y]\|_F^2
=2\sum_{i<j}(\widehat\lambda_i-\widehat\lambda_j)^2Y_{ij}^2
\ge \widehat\delta^2\,2\sum_{i<j}Y_{ij}^2
=\widehat\delta^2\|Y\|_F^2.
\]
Both sides of the desired unsquared inequality are nonnegative; taking square roots and using orthogonal invariance gives
\(\boxed{\|[\widehat M,X]\|_F\ge\widehat\delta\|X\|_F}\) for **every** skew \(X\), including arbitrary rotations of the eigenbasis. If \(\widehat\delta=0\), this remains true but gives no inverse bound; if \(\widehat\delta>0\), the commutator restricted to skew matrices is injective. This proof does not assume coercivity or exact fitting of \(\widehat R\).

## Ordered eigenvalue matching from dimension intersections

For every unit vector \(v\), Cauchy–Schwarz and the operator norm give
\[
|v^T(\widehat M-M)v|\le\|(\widehat M-M)v\|_2\|v\|_2
\le\|\widehat M-M\|_{\mathrm{op}}\le\varepsilon_M.
\]
Fix **each** index \(k\in\{1,2,3\}\). Let \(E_k^+(\widehat M)\) be the span of eigenvectors numbered \(1,\ldots,k\) for \(\widehat M\), and let \(E_k^-(M)\) be the span of eigenvectors numbered \(k,\ldots,3\) for \(M\). Their dimensions are \(k\) and \(4-k\), whose sum is \(4>3\). Thus the intersection contains a nonzero vector; normalize it to a unit vector \(v\). Expansion in the respective orthonormal eigenbases gives
\[
v^T\widehat Mv\ge\widehat\lambda_k,
\qquad v^TMv\le\lambda_k.
\]
The Rayleigh estimate therefore yields \(\widehat\lambda_k\le\lambda_k+\varepsilon_M\). This argument is valid for \(k=1\) (a one-dimensional top eigenspace against the full other space), \(k=2\) (two planes intersect), and \(k=3\) (the full top span against a one-dimensional bottom eigenspace). It also handles repeated eigenvalues because the selected orthonormal bases still have the stated dimensions.

Exchange \(M\) and \(\widehat M\): the span of their first \(k\) and last \(4-k\) eigenvectors intersects in a unit vector and yields \(\lambda_k\le\widehat\lambda_k+\varepsilon_M\). Consequently, for all three **same ordered indices**, \(\boxed{|\widehat\lambda_k-\lambda_k|\le\varepsilon_M}\). This is the complete matching proof; no unproved invocation of a generic Weyl theorem or arbitrary eigenvalue permutation is used.

For \(k=1,2\), the two pointwise inequalities give
\(\widehat\lambda_k-\widehat\lambda_{k+1}\ge(\lambda_k-\lambda_{k+1})-2\varepsilon_M\).
Taking the minimum of the two adjacent differences proves
\(\boxed{\widehat\delta\ge\delta-2\varepsilon_M}\). The nonadjacent difference is the sum of the two nonnegative adjacent differences, so it cannot be smaller than their minimum. This remains correct when the right side is negative; no positivity follows unless \(\delta>2\varepsilon_M\) or \(\widehat\delta>0\) is assumed separately.

## Formal coverage and remaining integration

`Spectral.lean` kernel-checks the unit-vector Rayleigh perturbation estimate for continuous linear maps on Euclidean \(\mathbb R^3\), the adjacent-gap subtraction, and the three-index ordered-gap deduction **conditional on pointwise matches**. Its `#print axioms` output contains only `propext`, `Classical.choice`, and `Quot.sound`. The real spectral theorem, the subspace-dimension intersection construction, orthogonal Frobenius invariance, and rotated commutator coercivity are given as explicit mathematical derivations above but are **not yet Lean theorems** in this file. In particular, the pointwise-match hypothesis in the Lean gap theorem must not be reported as a formal proof of Weyl matching.

The diagonal coefficient inequality in the frozen C03 `CAS15C03.lean` covers the diagonal-basis algebra. `Frobenius.lean` identifies the nine-coordinate Euclidean norm with \(\|\cdot\|_F\) and proves least-squares projection contraction for arbitrary data. `Mixed.lean` is the separately owned operator/Frobenius estimate. Full Lean C03 closure requires compiling the actual orthogonal-conjugation and ordered-eigenvalue interfaces into a single theorem over arbitrary symmetric matrices, then independent review and the prescribed execution path under the unchanged frozen contract. Until then the existing CAS_CONFLICT and scientific HOLD remain unchanged.
