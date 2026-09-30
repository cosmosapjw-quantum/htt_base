# Absolute redshift intercept and area-distance slope: a complete local inverse

Date: 2026-09-30. Role: proposer. Status: **analytically derived candidate; not independently promoted**. This is a bounded, purely geometric research loop. It contains no catalogue analysis, numerical scientific suite, or statistical calibration.

The result concerns one observation event and the first jet of a smooth source four-velocity field. Ideal absolute directional intercepts determine its value; ideal area-distance slopes then determine its symmetric derivative, even for accelerated sources. The remaining first-jet freedom is precisely spatial vorticity. A deterministic finite-error bound requires no expansion eigenvalue gap. None of these statements identifies a homogeneous-orbit normal or establishes a material Einstein solution.

## 1. Definitions, units, and the data contract

Let \(p\) lie in a smooth, time-oriented Lorentzian spacetime with signature \((-+++)\). Write the physical source and observer velocities as \(U=c u\), \(O=c o\), with \(u^2=o^2=-1\), both future pointing. Only the value of \(o\) at \(p\) is needed. The source field \(u\) is smooth in a neighbourhood of \(p\). Use length-valued coordinates, including \(x^0=ct\), and an observer orthonormal tetrad with \(e_0=o\).

For a sourceward unit sky direction \(n\), \(n\cdot o=0\), set

\[
K(p,n)=-o+n,\qquad K^2=0,\qquad o\cdot K=1. \tag{1}
\]

Extend \(K\) as the affine tangent to the past null geodesic, with length parameter \(\ell\ge0\) and \(\nabla_KK=0\). The angular-diameter/area distance \(d_A\) is defined by source-screen area divided by observer solid angle for the vertex bundle. Work before any conjugate point, close enough to the vertex that \(d_A\) is increasing.

The ideal data are the full-sky functions

\[
Z(n)=\lim_{d_A\downarrow0}(1+z(d_A,n)),\qquad
H(n)=c\left.\frac{\partial z}{\partial d_A}\right|_{0,n}. \tag{2}
\]

Here \(z\) is an absolute dimensionless endpoint redshift with the selected source field at emission and \(O\) at reception. No intercept is imposed externally. \(Z\) is dimensionless; \(H\) has units \(\mathrm{s}^{-1}\). This is a distance derivative at one fixed observation event, not redshift drift in observer time.

Define the derivative-first tensors and physical acceleration

\[
Q_{ab}=\nabla_a U_b,\quad B_{ab}=Q_{(ab)},\quad
A_b=U^a\nabla_aU_b,\quad h_{ab}=g_{ab}+u_au_b. \tag{3}
\]

\(Q,B,\theta,\sigma,W\) below have units \(\mathrm{s}^{-1}\); \(A\) has units \(\mathrm{m}\,\mathrm{s}^{-2}\). Parentheses and brackets include factors \(1/2\). Tensor components and all error norms below refer to the same observer tetrad.

**Optical first-order identity.** With these conventions,

\[
Z(n)=u(p)\cdot K(p,n),\qquad H(n)=B_{ab}K^aK^b. \tag{4}
\]

**Proof.** The endpoint frequency ratio is exactly
\(1+z(\ell,n)=u(x(\ell))\cdot K(x(\ell))\), since the reception denominator \(o\cdot K(p)\) is one. Affine parallel transport gives
\[
\frac{d(1+z)}{d\ell}=K^aK^b\nabla_a u_b=c^{-1}B_{ab}K^aK^b.
\]
For a vertex Jacobi matrix in a parallel screen basis, \(J(0)=0\), \(J'(0)=I\), and \(J''=\mathcal R J\), with smooth optical tidal matrix \(\mathcal R\). Thus \(J(\ell)=\ell I+O(\ell^3)\), and \(d_A=\sqrt{\det J}=\ell+O(\ell^3)\) on the positive branch. Changing the source screen changes transverse connecting vectors only by multiples of the null tangent, preserving their inner products. Source motion therefore does not alter this vertex normalization. The chain rule proves (4), without any geodesic assumption on \(U\). In particular,
\[
1+z(d_A,n)=Z(n)+c^{-1}H(n)d_A+O(d_A^2). \tag{5}
\]
The remainder is a local smoothness statement, not a supplied finite-distance bound. Curvature affects higher distance orders. \(\square\)

If \(Z\ne1\), the ratio \(cz/d_A\) has the term \(c(Z-1)/d_A\) and is not the slope in (2). With photon conservation and distance duality, \(d_A=d_L/(1+z)^2\). Direct area distance needs no luminosity or transparency assumption; replacing it by that luminosity expression does.

## 2. Exact image theorem

For sphere average \(\langle f\rangle=(4\pi)^{-1}\int f\,d\Omega\), use the unique coefficients

\[
Z(n)=\zeta_0+\zeta_i n^i,\qquad
H(n)=h_0+h_{1i}n^i+h_{2ij}n^in^j,\qquad
h_{2ij}=h_{2ji},\quad h_{2i}{}^i=0. \tag{6}
\]

**Theorem 1 — complete image.** A pair of real full-sky functions \((Z,H)\) occurs as (2) for a smooth future unit source field near \(p\) if and only if:

1. \(Z\) has no harmonics above degree one, and its coefficients obey
   \[
   \zeta_0^2-|\boldsymbol\zeta|^2=1,\qquad \zeta_0\ge1. \tag{7}
   \]
2. \(H\) has no harmonics above degree two, equivalently the form in (6).

There is **no additional joint algebraic constraint** and no positivity condition on \(H\). The source value and symmetric derivative are unique and are given by

\[
u^\alpha=(\zeta_0,\zeta_i),\qquad
S_{00}=h_0,\quad S_{0i}=-\tfrac12h_{1i},\quad S_{ij}=h_{2ij}, \tag{8}
\]
\[
\boxed{B=S+S(u,u)g.} \tag{9}
\]

The data space has dimension \(3+9=12\): the four intercept coefficients satisfy one constraint. At fixed observer, the full source first-jet space has dimension \(3+12=15\); Theorem 2 below gives its three-dimensional fibre.

**Proof of necessity and uniqueness.** In the observer tetrad \(K=(-1,n^i)\). Consequently \(u\cdot K=u^0+u^in_i\), so future unit normalization gives (7), and fixes \(u\) uniquely. Also
\[
B(K,K)=B_{00}-2B_{0i}n^i+B_{ij}n^in^j,
\]
which has degree at most two and is reproduced by \(S\) in (8).

To identify every possible lift, let \(T\) be symmetric and \(T(K,K)=0\) for all unit \(n\). Subtract its values at \(n\) and (-n); then \(T_{0i}=0\). Its even part says \(T_{ij}n^in^j=-T_{00}\) for every unit \(n\). Evaluating on coordinate directions and their normalized pairwise sums gives \(T_{ij}=a\delta_{ij}\), \(T_{00}=-a\). Thus \(T=ag\). Conversely \(g(K,K)=0\). The entire lift ambiguity is therefore \(B=S+\lambda g\).

Differentiating \(U^2=-c^2\) gives \(Q_{ab}u^b=0\), hence \(B(u,u)=0\). Since \(u^2=-1\), this fixes \(\lambda=S(u,u)\), proving (9). Sufficiency follows from the explicit normalized local field construction in Section 4. \(\square\)

The formulas are independent of the representative: replacing \(S\) by (S+ag) changes (S(u,u)) to (S(u,u)-a), leaving (9) unchanged. Harmonic coefficients can equivalently be extracted by

\[
\zeta_0=\langle Z\rangle,\quad \zeta_i=3\langle n_iZ\rangle,
\quad h_0=\langle H\rangle,\quad h_{1i}=3\langle n_iH\rangle,
\quad h_{2ij}=\tfrac{15}{2}\langle(n_in_j-\delta_{ij}/3)H\rangle. \tag{10}
\]

For rapidity \(\chi\ge0\), \(\zeta_0=\cosh\chi\), \(|\boldsymbol\zeta|=\sinh\chi\), and \(Z_{\min}=e^{-\chi}>0\), \(Z_{\max}=e^\chi\). A negative branch of (7) is not allowed. At zero dipole, \(Z=1\) and \(u=o\); no velocity direction must be selected.

## 3. Complete first-jet fibre and the physical rates

**Theorem 2 — fibre.** For an admissible pair, let \((u,B)\) be (8)–(9) and put \(b_a=B_{ab}u^b\). Every normalization-compatible derivative with these data, and only such a derivative, is

\[
\boxed{Q_{ab}=B_{ab}+b_a u_b-u_a b_b+W_{ab},}
\quad W_{ab}=-W_{ba},\quad W_{ab}u^b=0. \tag{11}
\]

Thus the unobserved part is an arbitrary antisymmetric bilinear form on the three-dimensional source rest space. In particular,

\[
\boxed{A_a=2c\,B_{ab}u^b=2c b_a,}\qquad
D_{ab}=h_a{}^c h_b{}^d B_{cd}, \tag{12}
\]
\[
\boxed{\theta=h^{ab}B_{ab}=g^{ab}B_{ab},\qquad
\sigma_{ab}=D_{ab}-\tfrac13\theta h_{ab}.} \tag{13}
\]

**Proof.** \(B(u,u)=0\) implies \(b\cdot u=0\). Equation (11) has symmetric part \(B\), and its contraction on the second index is \(b_a-b_a=0\); hence it differentiates the velocity normalization correctly. Contraction on the first index gives \(u^aQ_{ab}=2b_b\), proving (12). Conversely, subtract (11) with \(W=0\) from any eligible \(Q\). The difference is antisymmetric and annihilates \(u\), hence is exactly an allowed \(W\). Its spatial projection is itself, so
\[
W_{ab}=h_a{}^c h_b{}^d Q_{[cd]}. \tag{14}
\]
Also \(D=B+u\otimes b+b\otimes u\). Substitution yields the normalization-compatible decomposition
\[
\boxed{\nabla_aU_b=\tfrac13\theta h_{ab}+\sigma_{ab}+W_{ab}-\frac{u_aA_b}{c}
=\tfrac13\theta h_{ab}+\sigma_{ab}+W_{ab}-\frac{U_aA_b}{c^2}.} \tag{15}
\]
Tracing establishes (13). \(\square\)

The convention in (14) is derivative-first: \(W_{ab}=D_{[a}U_{b]}\). Its rate norm is \(\omega^2=\tfrac12W_{ab}W^{ab}\). In an oriented source rest tetrad, define \(\omega_i=\tfrac12\epsilon_{ijk}W_{jk}\), so \(W_{ij}=\epsilon_{ijk}\omega_k\) and the matrix \(W_{ij}\) acts on vectors as minus \(\boldsymbol\omega\times\). A rigid-rotation instantaneous velocity field \(v=\boldsymbol\Omega\times x\) gives \(W_{12}=\Omega_3\\). This fixes the sign without using an astrometric formula. The book's index order is different; the adapter is recorded in Section 8.

In the source rest frame, \(K=-u+n\), and (15) directly gives
\[
H(n)=\tfrac13\theta+\sigma_{ab}n^an^b-\frac{A_an^a}{c}. \tag{16}
\]
Thus an intrinsic dipole exists for accelerated sources. \(W\) does not occur in this scalar first-order sky. Recovering it requires different data or a restriction on the source field.

## 4. Local realizability, and what it does not establish

**Theorem 3 — local realization of every admissible pair and fibre element.** Fix any smooth Lorentzian metric near \(p\), any observer \(o\), any pair satisfying Theorem 1, and any \(W\) in (11). There is a smooth future unit field \(u(x)\) on a neighbourhood of \(p\) with exactly the prescribed value and \(\nabla_aU_b(p)=Q_{ab}\). Its ideal optical pair is exactly the prescribed \((Z,H)\).

**Proof.** Choose normal coordinates at \(p\), so \(g_{ab}(p)=\eta_{ab}\) and \(\partial_cg_{ab}(p)=0\), with coordinate components matched to the observer tetrad. Let
\[
v^b(x)=u^b+c^{-1}\eta^{bd}Q_{ad}x^a,\qquad
u^b(x)=\frac{v^b(x)}{\sqrt{-g_{cd}(x)v^c(x)v^d(x)}}. \tag{17}
\]
The seed \(v\) is future timelike on a sufficiently small neighbourhood by continuity. The denominator is one at \(p\). Its first derivatives vanish there because \(Q_{ab}u^b=0\) and \(\partial g(p)=0\). Therefore the normalized field has the prescribed first derivative, and its integral curves supply a local congruence. Equation (4) then gives the desired data. \(\square\)

This is a local first-jet theorem; higher jets remain free subject to smooth normalization and geometric identities. It supplies no fixed-sized neighbourhood, finite-distance remainder bound, global extension, homogeneity, or preferred slicing. It works in Minkowski spacetime with a freely chosen test-source congruence. It does **not** show that this field is the matter source of that metric.

If an Einstein/material model is imposed, its stress tensor, conservation laws, equation of state, forces, energy conditions, and symmetry restrictions can cut down the image. For conserved positive-density pressureless dust, acceleration must vanish. A freely prescribed accelerated congruence cannot therefore be relabelled as that dust. Realization in a specified non-vacuum Einstein/matter family remains a separate problem, unresolved here. The kinematic image theorem neither assumes nor proves those additional constraints.

## 5. Deterministic finite-error theorem, without an eigengap

All norms in this section are positive Euclidean component norms in one fixed observer tetrad; they are not Lorentz norms. Use \(|\cdot|_E\) for vectors, \(\|\cdot\|_F\) for matrices, and \(\|\cdot\|_{\mathrm{op}}\) for the Euclidean operator norm. The use of an observer norm is explicit because no positive definite Lorentz-invariant norm is available.

Consider two **admissible** pairs \((Z,H)\), \((\widetilde Z,\widetilde H)\), with reconstructed \((u,S,B)\), \((\widetilde u,\widetilde S,\widetilde B)\). Define the exact coefficient differences
\[
\epsilon_Z=\sqrt{(\Delta\zeta_0)^2+|\Delta\boldsymbol\zeta|^2},\qquad
\epsilon_H=\sqrt{(\Delta h_0)^2+\tfrac12|\Delta h_1|^2+\|\Delta h_2\|_F^2}. \tag{18}
\]
These are precisely \(|\widetilde u-u|_E\) and \(\|\widetilde S-S\|_F\); an asserted upper bound may replace either exact quantity. Suppose both source rapidities relative to \(o\) are at most \(R<\infty\). Set
\[
M=\sqrt{\cosh(2R)},\qquad
L=\min\{\|S\|_{\mathrm{op}},\|\widetilde S\|_{\mathrm{op}}\}. \tag{19}
\]

**Theorem 4 — finite perturbation bound.** Under these hypotheses,
\[
\boxed{|\widetilde u-u|_E=\epsilon_Z,\qquad
\|\widetilde B-B\|_F\le(1+2M^2)\epsilon_H+4ML\epsilon_Z.} \tag{20}
\]
One may replace \(L\) by either displayed norm individually, for example a known \(\|\widetilde S\|_{\mathrm{op}}\). The estimate is finite, nonlinear-valid, and makes no small-error, geodesicity, eigenvalue separation, or distinct-shear assumption.

**Proof.** A future unit vector of rapidity \(\chi\) obeys \(|u|_E^2=\cosh^2\chi+\sinh^2\chi=\cosh(2\chi)\), so both vector norms are at most \(M\). Write \(\lambda=S(u,u)\), \(\widetilde\lambda=\widetilde S(\widetilde u,\widetilde u)\). Then
\[
\begin{aligned}
|\widetilde\lambda-\lambda|
&\le |(\widetilde S-S)(u,u)|
 +|\widetilde S(\widetilde u,\widetilde u)-\widetilde S(u,u)|\\
&\le M^2\epsilon_H
 +\|\widetilde S\|_{\mathrm{op}}(|\widetilde u|_E+|u|_E)|\widetilde u-u|_E\\
&\le M^2\epsilon_H+2M\|\widetilde S\|_{\mathrm{op}}\epsilon_Z.
\end{aligned}
\]
Interchanging the roles gives the same bound with \(\|S\|_{\mathrm{op}}\), hence with \(L\). Since \(\|g\|_F=2\) in this tetrad, (9) and the triangle inequality give (20). \(\square\)

The rate-amplitude factor is necessary in some form: changing \(u\) changes the correction \(S(u,u)g\), and scaling a fixed nontrivial \(S\) amplifies that change without changing the intercept error. Thus rapidity and coefficient errors alone do not imply a rate-scale-independent Lipschitz constant for \(B\). Equation (20) uses a directly computable representative norm instead of hiding this dependence. The bound is conservative; sharpness is not claimed.

For optional angular \(L^2\) error descriptions, exact spherical orthogonality gives
\[
\|\Delta Z\|_{L^2}^2=(\Delta\zeta_0)^2+\tfrac13|\Delta\boldsymbol\zeta|^2,\quad
\|\Delta H\|_{L^2}^2=(\Delta h_0)^2+\tfrac13|\Delta h_1|^2+\tfrac{2}{15}\|\Delta h_2\|_F^2,
\]
so \(\epsilon_Z\le\sqrt3\|\Delta Z\|_{L^2}\) and \(\epsilon_H\le\sqrt{15/2}\|\Delta H\|_{L^2}\). These identities are for exact full-sky functions in the declared harmonic spaces, not a masked finite sample.

The derived acceleration is also continuous. For example, writing \(E_B\) for the right side of (20),
\[
|\widetilde A-A|_E\le2c\big(ME_B+\|\widetilde B\|_{\mathrm{op}}\epsilon_Z\big). \tag{21}
\]
This follows by adding and subtracting \(\widetilde B u\). Spatial rates follow from the explicit projection formulas (12)–(13), rather than from potentially discontinuous choices of individual eigenvectors.

### Optional deterministic extension for coefficients off the mass shell

The main theorem compares admissible pairs. A raw coefficient tuple need not obey (7). The following is only a defined reconstruction map with a conditional error guarantee; applying it does not establish that the supplied sky is in the exact image.

If the true rapidity obeys \(\chi\le R\), project a supplied dipole \(\widehat\zeta\) onto the closed Euclidean ball of radius \(\sinh R\), obtaining \(d_*\). Define \(u_*=(\sqrt{1+|d_*|^2},d_*)\), form \(S_*\) from the supplied slope coefficients by (8), and set \(B_*=S_*+S_*(u_*,u_*)g\). If \(|\widehat\zeta-\zeta|\le\eta_d\), convex projection gives \(|d_*-\zeta|\le\eta_d\). The gradient of \(d\mapsto\sqrt{1+|d|^2}\) has norm at most \(\tanh R\) on that ball; therefore
\[
|u_*-u|_E\le\sqrt{1+\tanh^2R}\,\eta_d. \tag{22}
\]
Equation (20) applies with this bound, slope representative error \(\|S_*-S\|_F\), and \(L\\) replaced by \(\|S_*\|_{\mathrm{op}}\). The supplied intercept monopole is an independent compatibility check, not silently overwritten evidence: if its error is at most \(\eta_0\), then
\[
|\widehat\zeta_0-\sqrt{1+|d_*|^2}|\le\eta_0+\tanh R\,\eta_d. \tag{23}
\]
Violations of higher-harmonic restrictions remain violations; this map merely discards them unless they are separately retained. No error sizes, extrapolation bounds, or data validity are supplied by the normalization operation.

## 6. What slope-only geodesicity does, including degeneracy

The condition \(A(p)=0\), weaker than geodesicity throughout a neighbourhood, is equivalent to \(Bu=0\). For a genuinely geodesic source field it certainly holds. With the slope representative \(S\), this is
\[
S^a{}_b u^b=s u^a,\qquad s=-S(u,u),\qquad B=S-sg. \tag{24}
\]

**Theorem 5 — complete pointwise geodesic slope fibre.** A real degree-two slope \(H\) admits a normalized source jet with \(A(p)=0\) if and only if the Lorentz-self-adjoint endomorphism \(S^a{}_b\) has a timelike eigenvector. If it does, its timelike eigenvalue \(s_t\) is unique, and \(B=S-s_tg\) is unique. Its compatible source values are exactly the future unit timelike vectors in
\[
E_t=\ker(S^a{}_b-s_t\delta^a{}_b). \tag{25}
\]
Relative to any one such \(u\), write the spatial eigenvalues of \(B\) as \(b_1,b_2,b_3\). If \(r\) of these vanish, \(E_t\) has signature \((-+\cdots+)\), dimension \(1+r\), and its future unit fibre is the hyperbolic space \(\mathbb H^r\). Thus the velocity is unique precisely when all three \(b_i\ne0\). Repeated **nonzero** spatial eigenvalues do not destroy uniqueness.

**Proof.** Necessity and sufficiency of the eigenvector condition follow from (24) and Theorem 2 with \(b=0\). A self-adjoint operator's eigenvectors for distinct real eigenvalues are metric orthogonal. Two timelike vectors cannot be orthogonal, so all timelike eigenvectors share one eigenvalue. Choosing one such \(u\) splits the tangent space into its timelike line and its positive-definite orthogonal complement. The latter is invariant under \(S\) and has an ordinary real orthogonal eigenbasis. Subtracting \(s_t I\) gives the claimed eigenvalues of \(B\), eigenspace signature, and complete unit hyperboloid fibre. \(\square\)

The allowed first jets can also be realized by a geodesic congruence in a neighbourhood: specify a normalized initial velocity field on a spacelike surface through \(p\) tangent to \(u^\perp\), with spatial derivative (B+W), and evolve its values by the local geodesic flow. Smoothness and nonintersecting flow hold after shrinking the neighbourhood. This realizes the prescribed first jet with zero acceleration throughout that neighbourhood; it remains a kinematic construction, not a dust Einstein solution.

Two distinctions matter. First, velocity degeneracy does not imply degeneracy of the geodesic symmetric tensor \(B\); the timelike eigenvalue remains unique. Second, the theorem requires a timelike eigenvector to exist. An arbitrary measured symmetric representative is not guaranteed to have one; timelike existence is part of the geodesic image condition, not a numerical eigenvalue-selection convention.

**Exact degeneracy.** In an observer tetrad, let
\[
B=\operatorname{diag}(0,0,b_2,b_3),\qquad
H(n)=b_2n_2^2+b_3n_3^2.
\]
Every \(u_\chi=(\cosh\chi,\sinh\chi,0,0)\) is a future unit kernel vector, giving the same slope. Its intercept \(Z_\chi=\cosh\chi+\sinh\chi\,n_1\) varies with \(\chi\). The degeneracy is therefore a slope-only statement.

**No uniform velocity stability near a lost gap.** Fix \(0<\chi\le R\), \(b_2,b_3>0\), and \(\varepsilon>0\). Let \(r_\chi=(\sinh\chi,\cosh\chi,0,0)\), a spacelike unit vector orthogonal to \(u_\chi\). Define
\[
B_{\varepsilon,\chi}=\varepsilon(r_\chi)_a(r_\chi)_b+b_2(e_2)_a(e_2)_b+b_3(e_3)_a(e_3)_b.
\]
For each \(\varepsilon>0\), its unique timelike kernel is \(u_\chi\), whereas \(B_{\varepsilon,0}\) has unique timelike kernel \(o\). Yet
\[
H_{\varepsilon,\chi}(n)-H_{\varepsilon,0}(n)
=\varepsilon\big[\sinh^2\chi+2\sinh\chi\cosh\chi\,n_1+\sinh^2\chi\,n_1^2\big]\longrightarrow0. \tag{26}
\]
The velocity difference stays fixed and nonzero. Both rapidities and rate amplitudes stay bounded. Thus no uniform slope-only velocity modulus of continuity tending to zero with coefficient error can hold over this class without excluding approach to degeneracy. Individual nondegenerate points permit local spectral perturbation control, but bounded rapidity alone is insufficient. Joint intercept data avoid this failure by directly fixing \(u\).

Without geodesicity, every future unit \(u\) is allowed for a given degree-two \(H\): use \(B=S+S(u,u)g\) and (11). Consequently unrestricted acceleration destroys slope-only velocity identification. This is not an impossibility result for joint intercept-plus-slope data.

**First-order velocity formula with arbitrary shear.** In the geodesic small-relative-velocity limit, denote the observer velocity relative to the source frame by the dimensionless vector \(\beta_{O/U}\), and write the source spatial expansion matrix as \(D=(\theta/3)I+\sigma\). The leading boosted dipole is \(h_1=-2D\beta_{O/U}+O(|\beta_{O/U}|^2)\). If \(D\) is invertible and held fixed in this expansion, the valid inverse at first order in velocity, without expanding in shear, is
\[
\beta_{O/U}=-\tfrac12D^{-1}h_1+O(|\beta_{O/U}|^2)
=-\tfrac12(h_0I+h_2)^{-1}h_1+O(|\beta_{O/U}|^2). \tag{27}
\]
The error constants depend on the inverse expansion matrix. Expanding \(D^{-1}\) as \((\theta/3)^{-1}I-(\theta/3)^{-2}\sigma+\cdots\) is a separate weak-shear expansion: its omitted \(\sigma^2\beta_{O/U}\) terms remain first order in velocity for unrestricted shear. Accordingly, Maartens et al. v3 Eq. (37) is not used here as an arbitrary-shear inverse. The exact eigenline method (24), or the joint inverse (9), avoids that truncation.

## 7. Edge cases and boundaries of interpretation

| Case | Exact conclusion |
|---|---|
| \(H=0\) with any admissible \(Z\) | \(B=0\), \(A=\theta=\sigma=0\); arbitrary spatial \(W\) is still invisible. |
| \(u=o\) | \(Z=1\); the dipole of \(H\) is \(-A/c\), not necessarily a boost. |
| Contracting, sign-changing, or vanishing \(H\) | Allowed; the inverse never divides by \(H\). |
| Repeated nonzero expansion eigenvalues | Joint inverse remains regular; geodesic slope velocity remains unique. |
| A zero spatial expansion eigenvalue | Joint inverse remains regular; geodesic slope-only velocity has a continuous fibre. |
| Very large rapidity | Exact uniqueness survives; the stated observer-norm stability constants grow. |
| Non-unit intercept coefficients or forbidden harmonics | Outside the exact image; no geometric promotion follows from projecting them into it. |
| Distances known only up to a constant scale | The corresponding rates rescale inversely; the intercept value does not supply the missing length calibration. |
| Finite sources bounded away from \(d_A=0\) | They do not by themselves supply the ideal limits or a bounded extrapolation error. |
| A source field defined only above a coarse-graining scale | Its continuation to \(p\) is an extra hypothesis. |

The \(U/O\) velocity relation is not \(U/N\) relative to a homogeneous-orbit normal \(N\). No homogeneous orbit, normal, Bianchi type, or non-tilt conclusion follows from this local inverse alone. Smoothness and ideal full-sky limits are the theorem's information contract; the theorem does not establish them for an actual population of emitters.

## 8. Primary-source bridge and convention audit

The supplied review `theory_blind_review_20260930/reviews/C.md`, especially its Section 4, was used as a list of issues to rederive, not as scientific authority. The prior `tilt_boost_loop_20260930/observations_findings.md`, Section 4, supplies the antecedent problem statement. All proofs above are written out here; earlier code and numerical claims are not used.

**Primary references and exact locators.**

| Source | Inspected locator | What it anchors |
|---|---|---|
| Maartens, Santiago, Clarkson, Kalbouneh & Marinoni, *Covariant cosmography: the observer-dependence of the Hubble parameter*, JCAP 09 (2024) 070, [arXiv:2312.09875v3](https://arxiv.org/html/2312.09875v3) | Sections 2.1–2.3, Eqs. (3)–(5), (15), (17), (24), (27) | Dust/geodesic scope, null direction and endpoint normalization. |
| Same | Section 3.1, Eqs. (28)–(34) and discussion following (34) | Null contraction and boosted monopole/dipole/quadrupole; antecedent inversion problem. |
| Same | Sections 4.1–4.3, Eqs. (59), (62)–(68), (72)–(73) | Distance transformation/duality, corrected luminosity distance, affine vertex expansion. |
| Ellis, Maartens & MacCallum, *Relativistic Cosmology*, CUP (2012), supplied `references/R01.pdf` and `R01.txt` | Printed p. 76 / PDF p. 92, Eqs. (4.8)–(4.9); printed pp. 80–85 / PDF pp. 96–101, Eqs. (4.30)–(4.40) | Acceleration, projected deformation, shear/expansion/vorticity decomposition and normalization. |
| Same | Printed pp. 157–159 / PDF pp. 173–175, Eqs. (7.17)–(7.19), Section 7.3 | Endpoint redshift, acceleration in directional redshift, and screen independence under a change of timelike observer at the screen. |
| Same | Printed pp. 164–165 / PDF pp. 180–181, Eqs. (7.40)–(7.48) | Area distance, luminosity distance, and reciprocity. |
| Same | Printed pp. 92–93 / PDF pp. 108–109, Eqs. (5.10)–(5.12) | Matter conservation imposes restrictions beyond an arbitrary source velocity jet. |

Maartens et al. use \(c=1\) and dust with zero acceleration, with negligible vorticity in their setup. Their boosted Hubble multipoles and distance correction are antecedents, not a claim for this arbitrary accelerated image theorem. Equations (4)–(26) above restore physical units and supply independent local proofs. The retrieved HTML source was inspected on 2026-09-30. Its relevant web retrieval identifiers were `turn138view0` and `turn139view0`–`turn139view3`; stable URLs and equation numbers, rather than those session identifiers, are the reproducible locators.

**Book sign adapter.** In R01, Eq. (4.38) is written with the velocity index first, \(\nabla_bu_a\), and its vorticity is \(\omega^{\mathrm{book}}_{ab}=D_{[b}u_{a]}\). This note fixes the derivative-first physical tensor \(W_{ab}=D_{[a}U_{b]}\\). For the same oriented frame and restored physical units,
\[
W_{ab}=-c\,\omega^{\mathrm{book}}_{ab}.
\]
The symmetric parts agree after the usual factor \(c\). A formula with a vorticity matrix acting on a sky vector cannot be imported across these conventions without this sign change. No position-drift reconstruction theorem is asserted here.

## 9. Bounded-loop closeout and novelty classification

| Result | Category | Proposer disposition |
|---|---|---|
| Endpoint formula, vertex normalization, kinematic decomposition, scalar multipole truncation | Established GR identities, rederived with explicit conventions | Retain with primary locators. |
| Null-cone kernel \(\operatorname{span}(g)\) and source mass-shell intercept | Elementary algebraic reformulations of established ingredients | Retain; no priority claim. |
| Complete accelerated joint image, unique \((u,B,A,\theta,\sigma)\), exact spatial-antisymmetric fibre, local realization | Self-contained deduction synthesized here; prior-art status not exhaustively searched | Candidate theorem for independent review. |
| Finite deterministic bound (20), optional map bounds (22)–(23) | Explicit derived estimate; optimality and novelty not established | Candidate theorem for independent review. |
| Complete geodesic eigenspace fibre, uniqueness of \(B\) despite velocity degeneracy, near-degenerate sequence (26) | Algebraic clarification and counterexample | Candidate theorem for independent review. |
| Operational recovery from finite catalogues or realization in a chosen Einstein/material family | Not established | Remains outside this completed local loop. |

Analytic checks completed within the proposer role: sourceward and acceleration signs; all powers of \(c\); uniqueness modulo \(g\); sufficiency by an explicit smooth field; complete first-jet fibre; zero-slope, zero-velocity, repeated-eigenvalue and zero-eigenvalue limits; finite rather than infinitesimal perturbation inequality. These checks are not independent review. The bounded analytical target is complete at candidate status. The next scientific gate is an independent audit of Theorems 1–5 and their stated scope, not automatic promotion based on this author's conclusion.
