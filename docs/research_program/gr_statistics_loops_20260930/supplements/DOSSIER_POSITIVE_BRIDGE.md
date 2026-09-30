# Two constructive ways to complete the local optical velocity jet

Date: 2026-09-30. Proposer supplement; independent review pending. This addresses the request to go beyond no-identification statements by specifying additional information and deriving an inverse. No PDE/Boltzmann solver, numerical scientific suite, Bianchi classification, or real-data analysis is used.

The starting point is gr/OPTICAL_THEOREMS.md: the ideal absolute intercept and area-distance slope determine \(u,B,A,\theta,\sigma\). Their remaining first-jet freedom is
\[
\nabla_aU_b=D_{ab}+W_{ab}-u_aA_b/c,\qquad
D=(\theta/3)h+\sigma,\quad W_{ab}=-W_{ba},\quad W_{ab}u^b=0. \tag{P0}
\]
Use its signature \((-+++)\), \(U=cu\), and derivative-first convention. In an oriented source rest tetrad,
\[
W_{ij}=\epsilon_{ijk}\omega_k,\qquad W x=-\omega\times x.
\]
The three components of \(\omega\), with units \(\mathrm{s}^{-1}\), are the remaining unknowns. These are source vorticity, not the arbitrary spin of a chosen tetrad. Every comparison below uses a known geometrical transport/rotation reference.

## Proposition A: two independent spatial derivative directions complete the jet

**Additional information contract.** Independently determine \(J(x)=h\nabla_x U\) at the same event for selected known source-spatial unit vectors \(x_m\). One possible realization is synchronized nearby measurements of the selected source four-velocity with known spacetime parallel transport:
\[
J(x)=\lim_{s\to0}\frac{h_p[P_{q_s\to p}U(q_s)-U(p)]}{s},\qquad
q_0=p,\quad \dot q_0=x. \tag{A1}
\]
The paths, length calibration, source identification, and transport must be specified independently. Equation (A1) is not available from a static remote sky alone. Finite baselines require a derivative/remainder bound. This is an explicit covariant derivative observation contract, not source proper motion or observer-time direction drift relabelled as a ray derivative.

Define \(y_m=J(x_m)-D x_m\). From (P0), since \(x_m\cdot u=0\),
\[
y_m=-W x_m=\omega\times x_m. \tag{A2}
\]
For positive weights \(w_m\), set
\[
G=\sum_m w_m(I-x_mx_m^T),\qquad b=\sum_m w_m x_m\times y_m.
\]
**Conclusion.** If the selected directions are not all parallel, then
\[
\boxed{\omega=G^{-1}b.} \tag{A3}
\]
Together with (P0), this determines the complete source first jet.

**Proof.** The triple-product identity gives
\(x_m\times(\omega\times x_m)=(I-x_mx_m^T)\omega\), hence \(b=G\omega\).
For any \(v\), \(v^TGv=\sum_mw_m|v\times x_m|^2\). It vanishes for nonzero \(v\) exactly when every \(x_m\) is parallel to \(v\). Thus two nonparallel directions suffice. No radiation anisotropy or expansion eigenvalue gap is needed. \(\square\)

There is an explicit three-scalar version. For \(x_1=e_1,x_2=e_2\),
\[
\omega_1=(y_2)_3,\qquad \omega_2=-(y_1)_3,\qquad \omega_3=(y_1)_2. \tag{A4}
\]
Other components are consistency checks, not discarded contradictions.

**Finite error.** For fixed calibrated directions, let
\(\epsilon_y^2=\sum_mw_m|\widehat y_m-y_m|^2\).
The weighted operator \(\mathcal A\omega=(\sqrt{w_m}\,\omega\times x_m)_m\) has
\(\mathcal A^T\mathcal A=G\). Its least-squares inverse obeys
\[
\boxed{|\widehat\omega-\omega|\le\epsilon_y/\sqrt{\lambda_{\min}(G)}.} \tag{A5}
\]
This follows from its singular-value decomposition. With two orthogonal directions and unit weights, \(\lambda_{\min}(G)=1\); with three orthogonal directions it is \(2\).
The tensor error is \(\|\widehat W-W\|_F=\sqrt2|\widehat\omega-\omega|\).
Errors in optical \(D\), directions, transport, and finite-baseline differentiation must enter the residual or operator error. For example, an error \(\Delta D\) contributes at most
\(\sqrt{\sum_mw_m}\|\Delta D\|_{\mathrm{op}}\) to \(\epsilon_y\).
If \(\|\widehat{\mathcal A}-\mathcal A\|\le\epsilon_{\mathcal A}\), the weighted data-vector error before this operator perturbation is at most \(\epsilon_y\), and \(|\omega|\le\Omega_*\), then
\[
|\widehat\omega-\omega|\le
\frac{\epsilon_y+\epsilon_{\mathcal A}\Omega_*}
{\sigma_{\min}(\widehat{\mathcal A})}. \tag{A6}
\]
This assumes the displayed denominator is positive. It is a deterministic bound, not a way to manufacture derivative observations.

## Proposition B: three radiation-quadrupole residual channels recover vorticity

This alternative uses independently differentiated local radiation data and a specified collision source. It applies locally to arbitrary smooth source congruences and spacetime geometry. No homogeneous normal or Bianchi structure constants enter the proof.

### B1. Define the derivative channel before using it

Use propagation direction \(e\) in the source rest space, not sourceward direction \(n\) of the optical intercept. Put \(L=U+ce\) and
\[
a=A/c,\quad H_u=\theta/3,\quad
\mathcal R(e)=H_u+a\cdot e+\sigma:ee,\quad
F(e)=P_e(a+\sigma e),\quad P_e=I-ee^T.
\]
The projected covariant change of direction along the same null ray is
\[
h\nabla_L e=-F(e)+W e,\qquad \nabla_L\ln E=-\mathcal R(e). \tag{B1}
\]
**Sign and normalization proof.** Write a future photon momentum as \(p=(E/c^2)L\). Its geodesic equation implies \(\nabla_LL=\mathcal R L\). Contracting with \(u\), using (P0), gives the displayed \(\mathcal R\). The spatial part of \(\nabla_LU\) is \(A+c(D e-W e)\); inserting this in \(\nabla_L(U+ce)=\mathcal R L\) gives (B1). The angular sign agrees with (A2).

To compare directional distributions at neighbouring events, use the rest-bundle connection obtained by projecting the spacetime connection: a horizontal comparison of a unit spatial direction obeys \(h\nabla_Xe=0\), with its temporal component fixed by differentiating \(e\cdot u=0\). Let \(\nabla^H\) denote this horizontal derivative, at fixed \(u\)-measured energy, and \(\mathscr D=L^a\nabla^H_a\).
It includes time and spatial radiation derivatives with this declared comparison. It is not the total photon-trajectory derivative, which also contains the angular and energy changes in (B1).

Let \(f(x,E,e)\) be intensity occupation summed over polarization states and
\[
\mathcal I(x,e)=\alpha\int_0^\infty E^3 f(x,E,e)\,dE,
\]
for a fixed normalization \(\alpha\). This is an energy-density angular carrier; specific intensity is \(c\mathcal I\). Assume finite required integrals and vanishing endpoint \(E^4f\). With collision rate \(C_t\) per physical second, Liouville transport and energy integration give
\[
\mathscr D\mathcal I+[-F+W e]\cdot\nabla_{S^2}\mathcal I
+4\mathcal R\mathcal I=\mathcal C,\quad
\mathcal C=\alpha\int_0^\infty E^3C_t[f]\,dE. \tag{B2}
\]
The coefficient four follows from \(\int E^4\partial_E f=-4\int E^3f\); finite spectral windows retain boundary fluxes. This derives the required identity directly, without certifying every high-rank hierarchy coefficient.

**Extra information required.** Independently supply \(\mathcal I(e)\), \(\mathscr D\mathcal I(e)\), and \(\mathcal C(e)\), or their sufficient moments, in this common frame. Derivatives must come from independent nearby-event information or another independently justified constraint. They cannot be obtained by solving (B2) with trial \(W\) and then reused as evidence for that \(W\). A static sky, an opacity history, or a collision conservation law alone does not supply this channel.

### B2. The three-channel inverse

Form \(r=\mathcal C-\mathscr D\mathcal I+F\cdot\nabla_{S^2}\mathcal I-4\mathcal R\mathcal I\).
Then \(r=(W e)\cdot\nabla_{S^2}\mathcal I\).
Define
\[
M=\int_{S^2}\mathcal I\,ee^T\,d\Omega,\qquad
R=\int_{S^2}r\,ee^T\,d\Omega. \tag{B3}
\]
**Conclusion.** If \(M\) has distinct eigenvalues \(m_1,m_2,m_3\), its three off-diagonal residual channels uniquely determine \(W\). In an orthonormal eigenbasis,
\[
\boxed{R=[M,W],\qquad W_{ij}=R_{ij}/(m_i-m_j)\ (i\ne j),\quad W_{ii}=0.} \tag{B4}
\]
Diagonal residuals must vanish; their nonzero values diagnose incompatibility with the exact contract.

**Proof.** The tangent field \(W e\) generates rotations and has zero sphere divergence. Integration by parts gives
\[
R=-\int\mathcal I[(W e)e^T+e(W e)^T]\,d\Omega
=-WM-MW^T=MW-WM.
\]
In the eigenbasis, each independent antisymmetric component has the indicated nonzero multiplier. No infinite-hierarchy closure is required. \(\square\)

The sufficient class is nonempty. For
\[
\mathcal I(e)=I_0[1+\varepsilon(e_1^2-e_3^2)],\quad I_0>0,\quad0<\varepsilon<1,
\]
brightness is strictly positive, and sphere moments give
\[
M=\frac{4\pi I_0}{3}I+
\frac{8\pi I_0\varepsilon}{15}\operatorname{diag}(1,0,-1).
\]
The minimum pairwise gap is \(8\pi I_0\varepsilon/15>0\). This example supplies an anisotropic carrier, not the required independent derivative/collision measurements. If \(M\) is axisymmetric, rotation about its symmetry axis is unidentifiable through this operator. If \(M\) is isotropic, the operator is zero. Proposition A remains available under its different information contract.

### B3. Angular differentiation is avoidable; spacetime differentiation is not

Put \(C_2=\int\mathcal C ee^T d\Omega\), \(T_2=\int(\mathscr D\mathcal I)ee^T d\Omega\).
Using \(\operatorname{div}_{S^2}F=-2a\cdot e-3\sigma:ee\), integration by parts gives
\[
\boxed{\begin{split}
R=C_2-T_2-\int\mathcal I\{&
[4H_u-\sigma:ee]ee^T+a e^T+e a^T\\
&+(\sigma e)e^T+e(\sigma e)^T\}\,d\Omega.
\end{split}} \tag{B5}
\]
Indeed the angular term is
\(-\int\mathcal I[(\operatorname{div}F)ee^T+F e^T+eF^T]\).
Combining with \(-4\mathcal R M\) cancels the \(a\cdot e\) coefficient multiplying \(ee^T\), leaving (B5). Only brightness moments through rank four and independently supplied derivative/collision rank-two moments are needed. Finite required moments do not imply a physical closure relation.

Let \(\delta=\min_{i<j}|m_i-m_j|\). With Frobenius norms,
\[
\|[M,W]\|_F^2=2\sum_{i<j}(m_i-m_j)^2W_{ij}^2\ge\delta^2\|W\|_F^2.
\]
For exact \(M\), least-squares inversion therefore gives
\[
\boxed{\|\widehat W-W\|_F\le\epsilon_R/\delta,} \tag{B6}
\]
where \(\epsilon_R\ge\|\widehat R-R\|_F\); diagonal mismatch remains a separate diagnostic.
If also \(\|\widehat M-M\|_{\mathrm{op}}\le\epsilon_M\), \(\|W\|_F\le W_*\), and the observed gap \(\widehat\delta>0\), then
\[
\boxed{\|\widehat W-W\|_F\le
(\epsilon_R+2\epsilon_M W_*)/\widehat\delta.} \tag{B7}
\]
Proof: \(\|[\Delta M,W]\|_F\le2\|\Delta M\|_{\mathrm{op}}\|W\|_F\); apply the pseudoinverse of \([\widehat M,\cdot]\). Ordered-eigenvalue perturbation also gives \(\widehat\delta\ge\delta-2\epsilon_M\).
Optical-rate errors, brightness errors, derivative calibration, energy boundaries, collisions, and transport must enter \(\epsilon_R\). The theorem supplies conditioning, not those input bounds.

**Several degenerate channels can jointly be sufficient.** Suppose independently known residuals satisfy \(R_j=[M_j,W]\) in one common frame. The stacked map is injective exactly when
\[
\bigcap_j\{W\in\mathfrak{so}(3):[M_j,W]=0\}=\{0\}.
\]
For a Frobenius-orthonormal basis \(E_\alpha\) of antisymmetric matrices, form
\[
\mathcal G_{\alpha\beta}=\sum_j
\langle[M_j,E_\alpha],[M_j,E_\beta]\rangle_F.
\]
This condition is equivalent to \(\mathcal G>0\); least-squares inversion then has error at most
\(\big(\sum_j\|\Delta R_j\|_F^2\big)^{1/2}/\sqrt{\lambda_{\min}(\mathcal G)}\) for exact calibrated \(M_j\). The proof is the identity between \(\mathcal G\) and the normal matrix of the stacked linear map.
For example, two nonisotropic axisymmetric tensors \(M_j=\alpha_j I+\beta_j n_jn_j^T\), with \(\beta_j\ne0\) and nonparallel axes, suffice: their commuting antisymmetric subspaces require respectively \(\omega\parallel n_j\), whose intersection is zero. More explicitly \(R_j n_j/\beta_j=\omega\times n_j\), so Proposition A's inverse applies with weights \(\beta_j^2\). Thus no individual quadrupole needs three distinct eigenvalues if independently differentiated additional channels are available. Spectral bands are possible channels only when their energy-boundary fluxes are included in their respective residuals.

## What the dossiers supply and what remains additional information

The five PDFs contain forward equations and compatibility restrictions. They contain no new measured \(\mathscr D\mathcal I\), local source derivative samples, or numerical residual-error guarantee.

| Dossier; inspected analytical pages | Supplied content and use | Additional requirement |
|---|---|---|
| I, pp. 3, 8–12 | Units; common kinetic moments (50)–(52); coherency positivity and angular moments (72)–(87); derivative constraints | Compatible states do not supply the derivative channels of A or B. |
| II, pp. 6–12 | Transfers (34)–(52); displayed hierarchy (58)–(69); ray/bolometric transport (74)–(98) | The vorticity-free normal component formula is not a formula for arbitrary source \(u\). Only the low-order identities needed here are independently derived. |
| III, pp. 9–12 | Energy weighting and matching event sources (47)–(51); proper-time/frame conditions (65)–(78) | Chemical/visibility histories do not determine arbitrary angular collisions or radiation derivatives. |
| IV, pp. 13–16 | Coherency and rest-electron Thomson integral (74)–(96); same-frame transfer (97)–(101) | Electron density/velocity, coherency, collision regime, clock and screen transformations must be supplied. |
| V, pp. 3–9, 17–19 | Common-screen transport; collision-map restrictions; product quadrature (38)–(46); propagator (47)–(53); common event ledger | Upper forward bounds, positivity and conserved moments do not suffice for inverse identification. |

Page numbers are printed counters, also one-based PDF pages. Coverage is targeted: these analytical pages were read; other sections were surveyed by headings only. No complete independent verification of all five documents is claimed. Extraction truncations affecting IV pp. 14–15 and V p. 7 were resolved by separate full-page reads. The source files are the user-supplied Dossier I–V Restored Revised PDFs and their matching extracted texts in references/.

**A bounded collision map makes \(C_2\) concrete in a restricted regime.** Under IV's cold rest-electron elastic Thomson assumptions, let \(\mathcal J(e)\) be bolometric coherency and \(\Gamma=c n_{e,\mathrm{rest}}\sigma_T\). Its integral map is
\[
\mathcal C_J(e)=\Gamma\left[-\mathcal J(e)+
\frac{3}{8\pi}P_e\left(\int\mathcal J(e')d\Omega'\right)P_e\right]. \tag{C1}
\]
The trace supplies \(\mathcal C\). In matrix-Frobenius \(L^2(S^2)\),
\[
\|\mathcal C_J\|_{L^2}\le\tfrac52\Gamma\|\mathcal J\|_{L^2}. \tag{C2}
\]
Proof: \(\|\int\mathcal J\|\le\sqrt{4\pi}\|\mathcal J\|_{L^2}\); left/right multiplication by \(P_e\) is contractive. The gain norm is at most \(3/2\), and the loss adds one. This conservative bound propagates coherency error into collision error; uncertainty in \(\Gamma\) adds another term. One cannot replace coherency by intensity when polarized gain matters. Electron tilt needs a transformed collision map, including Doppler-dependent rate, rather than (C1) with a guessed scalar \(\Gamma\).

Screen tensors must be embedded in one source tetrad before IV's angular tensor integral is taken. If interpolated, V p. 5 supplies a declared isometric screen-transport construction with positive weights. Rotation about the ray changes screen orientation without changing the ray direction; the latter does not determine the former. An unknown tetrad spin can likewise contaminate the rotational residual.

**Exact quadrature is conditional.** Suppose \(\mathcal I\), \(\mathcal C\), and \(\mathscr D\mathcal I\) have scalar bandlimits \(L,L_C,L_T\). Integrands in (B3),(B5) have maximum degree
\[
D_*=\max(L+4,L_C+2,L_T+2).
\]
A sufficient Gauss–Legendre/uniform-azimuth product rule is
\[
N_\mu\ge\lceil(D_*+1)/2\rceil,\qquad N_\phi\ge D_*+1. \tag{C3}
\]
Proof: azimuthal sums eliminate nonzero Fourier orders through \(D_*\); surviving associated-Legendre products have integer powers of \(1-\mu^2\) and polynomial degree at most \(D_*\), to which Gauss–Legendre exactness applies. This is V pp. 7–8's scalar argument with the actual weak-kernel degree four, not merely the state bandlimit. Angular tails, masks, nonpolynomial coefficients and energy quadrature require separate bounds. Exact state round trips do not imply exact product moments.

**Remote channels need a lower response bound.** If a known propagator/readout produces \(G R\), a sufficient condition is
\(\|G X\|\ge\beta\|X\|_F\) on the three-dimensional range of \([M,\cdot]\), with \(\beta>0\).
The composite response has smallest singular value at least \(\beta\delta\), so error \(\epsilon\) gives \(W\)-error at most \(\epsilon/(\beta\delta)\). This follows by multiplying the two lower bounds. An upper bound on \(\|G\|\) alone is insufficient. V pp. 8–9 provide a forward propagator framework, not such an independently identified channel or a verified lower bound. Initial/source subtraction and frame transport must also be supplied.

## Optional final step: tilt when the orbit tangent space is independently known

Suppose three independent vector fields \(X_I\), known to span the spacelike homogeneous-orbit tangent space on the relevant domain, are independently supplied. Positivity of \(G_{IJ}=g(X_I,X_J)\) makes
\[
v^a=\epsilon^{abcd}(X_1)_b(X_2)_c(X_3)_d,\qquad
N^a=\pm v^a/\sqrt{-v^2}
\]
well defined; select the future sign. The determinant identity gives \(v^2=-\det G\), and antisymmetry makes \(N\cdot X_I=0\). Thus the recovered source \(u\) gives
\[
\gamma_{uN}=-u\cdot N,\qquad
\beta_{uN}^2=1-\gamma_{uN}^{-2}.
\]
This is a standard type-free conditional construction, not an inference of the generators from optical data or a Bianchi classification. A single event gives relative tilt there; a domain statement requires the supplied orbit distribution and recovered field over that domain.

## Corrections and bounded conclusions

1. Here \(W\) is derivative-first source vorticity. Dossier II also uses \(W\) for rotating-tetrad components; those are different objects.
2. Dossiers I–II generally use inverse-length rates. Here expansion/shear and collision rates are per second; physical acceleration enters as \(A/c\).
3. Conservation fixes selected low collision moments, not an entire angular collision map. Rank-two closure requires its actual source or a bounded specified map.
4. Ray direction change is not observer-time image drift. Any astrometric implementation needs its own proven observation equation.
5. Invertibility does not establish that the right-hand side was observed. These two propositions explicitly provide sufficient extra-information conditions, making the earlier no-go conditional rather than terminal.

Proposition A requires two nonparallel calibrated local derivative directions. Proposition B requires independent differentiated radiation/collision information and a nondegenerate quadrupole. Each then recovers all three missing components and completes (P0), with a deterministic bound. Their finite-dimensional inverse principles and geometric ingredients are standard; this synthesis makes no priority claim. Both remain proposer candidates for independent review.
