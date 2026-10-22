# CAS-15-C03 Wolfram-axis proof

The claim is finite dimensional over real matrices. The source
`commutator_inverse.wls` loads Wolfram Engine 15 and xTensor, and checks the
displayed identities exactly. The only inputs are the frozen C03 contract,
admitted inputs, and `COMMON_SPEC.md`. No C01/C02, transport, or scientific
claim follows.

Let (T_M(X)=MX-XM), where (M=M^T) and (X=-X^T). Orthogonal conjugation
preserves both spaces, (T), and the Frobenius norm. In an orthonormal
eigenbasis (M=\operatorname{diag}(m_1,m_2,m_3)), the independent skew
coordinates are (x_{12},x_{13},x_{23}), and

\[
 (T_MX)_{ij}=(m_i-m_j)x_{ij},\quad (T_MX)_{ii}=0,
 \qquad
 \|T_MX\|_F^2=2\sum_{i<j}(m_i-m_j)^2x_{ij}^2.
\]

The output is symmetric with zero diagonal. Thus the coordinate matrix of
(T_M:\mathfrak{so}(3)\to\operatorname{Sym}_0^{\rm off}(3)) is diagonal with
entries (m_1-m_2,m_1-m_3,m_2-m_3). If
(\delta=\min_{i<j}|m_i-m_j|>0), its determinant is nonzero, rank is three,
and kernel is zero. Also
(\|T_MX\|_F^2\ge\delta^2\|X\|_F^2). For a compatible
(R=T_MW), (R) is symmetric with zero diagonal and the unique inverse is
(W_{ij}=R_{ij}/(m_i-m_j)), (W_{ii}=0), (W_{ji}=-W_{ij}). An arbitrary
diagonal or antisymmetric part of (R) is outside the image and cannot be
inverted by that formula.

For symmetric (\widehat M), diagonalize it orthogonally and denote the
eigenvalues (h_i). When (\widehat\delta>0), its commutator image is again
the symmetric zero-diagonal subspace. The Frobenius orthogonal projection
onto that image in this eigenbasis is
(P(A)=(A+A^T)/2-\operatorname{diag}(A)). For every skew (X),

\[
 \|T_{\widehat M}X-\widehat R\|_F^2
 =\|T_{\widehat M}X-P\widehat R\|_F^2
  +\|(I-P)\widehat R\|_F^2.
\]

The first term has the unique zero at
(\widehat W=T_{\widehat M}^{-1}P\widehat R). This proves the stated
least-squares minimizer and shows that diagonal residual mismatch, as well
as any antisymmetric residual, remains diagnostic. The engine checks the
projection orthogonality and the exact inverse identity.

Write (\Delta M=\widehat M-M), (\Delta R=\widehat R-R). Since
(R=T_MW), the projection identity gives

\[
 T_{\widehat M}(\widehat W-W)
 =P(\widehat R-T_{\widehat M}W)
 =P(\Delta R-[\Delta M,W]).
\]

The gap bound for (\widehat M) and orthogonal projection contraction imply
(\widehat\delta\|\widehat W-W\|_F\le
\|\Delta R-[\Delta M,W]\|_F). Matrix norm submultiplicativity yields
(\|[\Delta M,W]\|_F\le
\|\Delta M W\|_F+\|W\Delta M\|_F\le
2\|\Delta M\|_{\rm op}\|W\|_F). Applying the admitted bounds gives

\[
 \|\widehat W-W\|_F\le
 \frac{\epsilon_R+2\epsilon_M W_\star}{\widehat\delta}.
\]

The engine checks the exact error projection identity and the final real
inequality implication. The intervening norm steps are standard Hilbert
projection and matrix operator/Frobenius inequalities stated explicitly
above; they are valid for every real 3-by-3 input in the admitted domain.

For ordered eigenvalues of two real symmetric matrices, the Rayleigh
quotient obeys
(|v^T(\widehat M-M)v|\le\|\Delta M\|_{\rm op}\|v\|^2).
The Courant-Fischer min-max formula therefore gives
(|\widehat m_i-m_i|\le\epsilon_M) for each ordered index. Consequently
(|\widehat m_i-\widehat m_j|\ge|m_i-m_j|-2\epsilon_M), and taking the
minimum over pairs proves
(\widehat\delta\ge\delta-2\epsilon_M). This comparison does not
establish positivity of (\widehat\delta); that positivity is a separate
admitted condition for the perturbed inverse.

If (m_1=m_2), the skew 12-direction lies in the kernel. If all three
eigenvalues coincide, the map is zero. Likewise (\widehat\delta=0)
excludes the perturbed inverse. The engine checks these singular controls
without division at zero.
