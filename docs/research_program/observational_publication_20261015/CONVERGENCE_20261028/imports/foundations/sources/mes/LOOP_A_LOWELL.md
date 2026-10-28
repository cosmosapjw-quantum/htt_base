# Loop A — brightness moments, a positive shear response, and finite-error transport inversion

Owner: common/obsstat for the deterministic construction; MIO for conditional diagnostic images. Internal theory result, C0, transfer source none. Date: 2026-10-26. Repository comparison identity: a55036ad09c53a9215dee3282e425d37cfb95443. No repository mutation, solver, ODE, or raw-data campaign is part of this result.

## R1. Question and achieved advance

The useful physical question is: **which local radiation tensors enter a controlled reconstruction of matter-congruence shear, once their transport derivatives are supplied?** The answer is an exact five-dimensional positive operator built from bolometric brightness moments through order four. Its inverse has a finite-error certificate. Positivity removes a small-anisotropy requirement that a naive perturbative inversion would impose.

This extends the available research capability beyond the retained Q/O contraction ellipsoid and chirality optimization. It preserves those results, whose mathematical objects are a temperature STF2⊕STF3 pair and their attained invariant images. Here the objects are the photon occupation number, stress-energy moments, and a local transport residual. The two constructions have distinct inputs and applications. The published R32-01 results, including its Eq. (35) chirality margin, Eq. (36) temperature-quadrupole remainder and Eq. (37) asymptotic optical construction, are reused as the baseline rather than reproved.

Three completed results follow: an exact temperature-to-stress example exhibiting nonlinear harmonic mixing; a coercivity proof for the shear response; and an observation-error bound for the resulting conditional inverse. A small non-coaxial example connects the operator to relative tensor orientation.

## R2. Evidence and exact source correspondence

The attached 55-page *From a CMB sky map to physical constraints* supplies the first-order bridge: PDF pp. 49–50, Eqs. (E.1)–(E.8), particularly π=8ρϑ₂/15 and the quadrupole transport equation. Its pp. 51–53 specify derivative envelopes and their first-order scope. The attached 36-page report, PDF p. 10 §8.1, fixes the temperature convention T₂(n)=Q_ab nᵃnᵇ; pp. 24–26 §23 fix the current tensorized carriers and conditional forward map.

Ellis, Maartens and MacCallum, *Relativistic Cosmology*, attached PDF pp. 121–124, Eqs. (5.81)–(5.101), provide distribution multipoles and their mass-shell moments. PDF p. 299, printed p. 283, Eqs. (11.1)–(11.2), provides nonlinear bolometric transport. Cercignani and Kremer, *The Relativistic Boltzmann Equation*, attached PDF pp. 56–57, Eqs. (2.68)–(2.78), independently fixes the microscopic-to-macroscopic moment route. Its classical massive-gas normalization is not copied into the photon occupation convention below.

SciSpace was actually queried with full research questions; discovery records are in sources/A_SCISPACE_SEARCH.json. The relevant author paper was then downloaded and inspected: Maartens–Gebbie–Ellis (1999), DOI [10.1103/PhysRevD.59.083506](https://doi.org/10.1103/PhysRevD.59.083506), [arXiv:astro-ph/9808163v2](https://arxiv.org/abs/astro-ph/9808163), especially PDF p. 14 Eq. (71). Its PDF p. 15 Eq. (89) displays 2/7 for the σπ coefficient; Eq. (71), specialized consistently, gives 10/7, agreeing with the attached textbook. Both pages were inspected. The direct angular derivation below resolves the coefficient for our convention and preserves the source discrepancy.

No literature-wide priority claim is made. The hierarchy is established prior work. The contribution of this research unit is the explicit positive-operator reformulation, its bounded-error observation contract, and their integration with the existing tensorized diagnostics.

## R3. Frame, units and assumptions

Use signature (−,+,+,+), a future unit congruence U·U=−1, and h=g+U⊗U. Physical proper time is τ; the derivative dot=U·∇ differentiates per proper length s=cτ. Thus Θ=∇·U, σ_ab=D_⟨a U_b⟩ have units m⁻¹, and the shear rate per second is cσ. Work at an event in an orthonormal spatial triad, with propagation direction e·e=1; outward sky direction is n=−e. All norms are full spatial Frobenius norms unless an operator norm is explicit.

For the transport application assume a smooth **geodesic, irrotational** congruence, collisionless photons, finite energy density and differentiable required moments. Expansion need not be positive. The algebraic positivity lemma itself requires only a finite nonnegative angular brightness measure. More general acceleration, vorticity and collision terms can be included in the residual when independently supplied; this report proves the application in the stated branch.

Let f(x,E,e) be dimensionless occupation per photon helicity, E=−cp·U>0, with both helicities equally populated. Define

\[
 I_E={2E^3\over(2\pi\hbar)^3c^3}f,\qquad
 I(e)=\int_0^\infty I_E(e)\,dE.
 \tag{A1}
\]

I has units J m⁻³ sr⁻¹. Require the energy integration-by-parts boundary E⁴f→0 at both endpoints and sufficient domination for differentiation under integration. A finite bolometric moment alone does not guarantee these derivative conditions.

Write angular moments as

\[
 \rho=\int I\,d\Omega,\quad q_a=\int Ie_a\,d\Omega,\quad
 \pi_{ab}=\int Ie_{\langle a}e_{b\rangle}\,d\Omega,\quad
 H_{A_\ell}=\int Ie_{\langle A_\ell\rangle}\,d\Omega\quad(\ell=3,4).
 \tag{A2}
\]

The physical energy flux is cq; ρ, q, π and H have energy-density units. In the U frame,
T=ρU⊗U+(ρ/3)h+2U⊙q+π. This radiation π is distinct from exceedance Π; temperature Q is distinct from the premise-anchor Q diagnostic, and neither is identified with σ.

## R4. Candidate equations and an exact nonlinear bridge

For a Planck spectrum in each direction,

\[
 f=(e^{E/(k_BT(e))}-1)^{-1},\quad
 I=C_\gamma T(e)^4,\qquad
 C_\gamma={\pi k_B^4\over60\hbar^3c^3}.
 \tag{A3}
\]

This follows by E=k_BT y and ∫y³/(eʸ−1)dy=π⁴/15. It is exact for a direction-dependent absolute temperature. If T=T₀(1+ϑ), the first-order moments recover the attached appendix. For the outward temperature quadrupole, π=(8/15)ρ₀Q/T₀+O(ϑ²); odd moments change sign between n and e.

Nonlinearly, harmonic projection and fourth power do not commute. A concrete positive field is T(n)=T₀(1+d·n), |d|<1. It has Q=O=0. Nevertheless, with ρ₀=4πCγT₀⁴, direct angular integration gives

\[
 \rho=\rho_0(1+2|d|^2+|d|^4/5),\qquad
 \pi_{ab}=\rho_0\left({4\over5}+{4|d|^2\over35}\right)
 d_{\langle a}d_{b\rangle}.
 \tag{A4}
\]

Thus a temperature low-ell truncation cannot generally be substituted for stress-energy moments. Equation (A4) is a constructive conversion example; it does not assign an origin to the dipole. Frequency-resolved f remains the primary object for distorted spectra, for which a single thermodynamic T may not exist.

The exact quadrupole equation in our branch becomes

\[
 {\cal L}_I\sigma=-R,\qquad
 R=\dot\pi_{\langle ab\rangle}+{4\over3}\Theta\pi_{ab}
 +{2\over5}D_{\langle a}q_{b\rangle}+D^cH_{abc},
 \tag{A5}
\]
\[
 {\cal L}_I S={8\rho\over15}S+
 {10\over7}\operatorname{STF}(S\pi)-H_4:S,\qquad S\in\operatorname{STF}_2.
 \tag{A6}
\]

Here STF(Sπ) includes matrix symmetrization. This is a local algebraic inference once R is supplied. No closure or integration of the hierarchy has been performed.

## R5. Proof of the physical lemma

**Lemma.** For every nonnegative finite I, let M₂=∫Ieeᵀ=ρh/3+π and m=λ_min(M₂). Then L_I is self-adjoint on STF2 and

\[
 m\|S\|^2\le \langle S,{\cal L}_I S\rangle
 =\int I\{2|Se|^2-(e^TSe)^2\}\,d\Omega
 \le\rho\|S\|^2.
 \tag{A7}
\]

If m>0, it is invertible and ||σ||≤||R||/m. A sharper actual certificate uses λ_min(L_I), directly computed as a symmetric 5×5 matrix.

First recover the rank-four raw moment. The STF decomposition is

\[
 M_{abcd}=H_{abcd}+{1\over7}
 (h_{ab}\pi_{cd}+h_{ac}\pi_{bd}+h_{ad}\pi_{bc}
 +h_{bc}\pi_{ad}+h_{bd}\pi_{ac}+h_{cd}\pi_{ab})
 +{\rho\over15}(h_{ab}h_{cd}+h_{ac}h_{bd}+h_{ad}h_{bc}).
 \tag{A8}
\]

Taking a trace verifies each coefficient. Contracting against S and projecting the output yields

\[
 \operatorname{STF}(M_4:S)
 =H_4:S+{4\over7}\operatorname{STF}(S\pi)
 +{2\rho\over15}S.
\]

Consequently Eq. (A6) equals

\[
 {\cal L}_I S=
 2\operatorname{STF}(SM_2)-\operatorname{STF}(M_4:S).
 \tag{A9}
\]

Its quadratic form is exactly the integral in Eq. (A7). The polarized expression
∫I[2(Se)·(Te)−(eᵀSe)(eᵀTe)] is symmetric in S,T, proving self-adjointness. Cauchy–Schwarz gives (eᵀSe)²≤|Se|², so the integral is at least tr(S²M₂)≥m||S||². For the upper bound rotate e to the third axis:

\[
 \|S\|^2-\{2|Se|^2-(e^TSe)^2\}
 =S_{11}^2+S_{22}^2+2S_{12}^2\ge0.
\]

Integration proves the upper estimate. Finite-dimensional spectral theory gives inversion. This argument covers arbitrary amplitudes and nonthermal bolometric spectra.

The matrix can be assembled from even brightness moments of degrees zero, two and four. The local transport side additionally uses the dipole and octupole and the specified derivatives. Higher angular moments do not enter this particular algebraic response directly. Their nonlinear contribution to brightness remains relevant when the input is supplied as a temperature field rather than as I. A simple conservative conditioning certificate is
\[
 \kappa_2({\cal L}_I)\le {\rho\over m},\qquad
 m\ge {\rho\over3}-\|\pi\|_{\rm op},
\]
whenever the relevant lower bound is positive. The actual five-dimensional spectrum can certify conditioning even where this conservative scalar bound is uninformative.

The 10/7 coefficient can also be checked directly before moment decomposition. In the shear-only part of the exact brightness equation, put a=eᵀσe and v=σe−ae. Liouville gives a redshift term +4aI and angular drift −v·∇_S I. Since div_S v=−3a and v·∇_S(e_⟨a e_b⟩)=2e_⟨a(σe)_b⟩−2ae_⟨a e_b⟩, sphere integration by parts gives precisely 2 STF(σM₂)−STF(M₄:σ). Combined with Eq. (A8), this fixes 10/7. The coefficient 2/7 fails this identity.

## R6. Limits, conditioning and relative orientation

For isotropic brightness, π=H₄=0 and L_I=(8ρ/15)Id, recovering the first-order source coefficient. At ρ=0, nonnegative brightness vanishes and L=0. A single pencil beam has a nontrivial nullspace; positive brightness on the full sphere gives m>0. The sufficient m criterion is deliberately not asserted necessary: a rank-two M₂ may still yield a positive L on trace-free matrices.

Non-coaxiality has a transport meaning. Take
I(e)=ρ[1+b(e_z²−1/3)]/(4π), −3/2<b<3. Then
π=ρb diag(−2,−2,4)/45 and H₄=0. For S=k(E₁₃+E₃₁),

\[
 {\cal L}_I S={2\rho(84+5b)\over315}S,\qquad
 [\pi,S]={2\rho bk\over15}(E_{31}-E_{13}).
 \tag{A10}
\]

Taking R=−L_I S constructs a non-coaxial solution of the local quadrupole relation whenever bk≠0. This is an algebraic transport witness, not a claimed global Einstein–Liouville solution. Generally [π,σ]=−[π,L_I⁻¹R]: the relative orientation depends on transport. A morphology axis alone supplies neither R nor this commutator.

All terms in Eq. (A5) have units J m⁻⁴. Multiplying the equation by c converts it to per-second rates. No G enters the local kinetic identity; curvature or matter-source inference requires additional field equations.

## R7. Actual CAS execution

cas/loop_a.wl was executed through the Wolfram Language evaluator. Polynomial reduction modulo x²+y²+z²−1 returned a zero 3×3 remainder for Eq. (A9), and zero for the quadratic-form identity. Replacing 10/7 by 2/7 returned a nonzero remainder. Exact angular integrations verified Eq. (A4), while matrix algebra verified Eq. (A10). A separate upper-bound check returned a²+2b²+f², nonnegative for real entries.

The exact returned expressions are preserved in cas/loop_a_results.json. This is a finite algebra check supporting the written proof; it is neither xAct execution nor a historical four-axis CAS pass. Requested/observed author model and effort are UNKNOWN in this bounded task. Fresh independent review is assigned to the parent after delivery.

The optional analytical illustration, figures/figure_a_radiation.pdf and .png, uses I=ρ[1+aP₂(e_z)]/(4π), a∈[−0.8,1.5]. Its five response eigenvalues divided by ρ are (56−10a)/105, (56+5a)/105, and (56+10a)/105 with multiplicities 2, 2, and 1. The plotted certified bound is min[(5−a)/15,(5+2a)/15]. cas/make_a_figure.py independently assembled the 5×5 matrix at four amplitudes and matched these branches within 2.23×10⁻¹⁶; the complete interval remains positive by the displayed affine formulas. This is an analytical family rather than measured CMB.

## R8. Evidence verdict and coefficient correction

Equations (A4), (A7), (A9), and the error estimate below are DERIVED conditional results. The Boltzmann hierarchy is literature-supported; its local use additionally needs the stated transport branch. The current data-facing application is SPECIFIED because no radiation derivative-jet product has been supplied.

The source-coefficient watchdog finding is closed locally by the direct Liouville calculation, trace decomposition, source hierarchy Eq. (71), textbook Eq. (11.2), and CAS identity. The earlier displayed 2/7 is retained as a source discrepancy, not silently normalized away. No claim is made about a journal erratum or the entire original paper.

No strong no-go is proposed. In particular, absent derivative data is an input obligation, not an impossibility theorem. Publication novelty remains unassessed beyond the explicitly inspected comparators.

## R9. Observation operator and bounded-error contract

A frequency channel and spatial pixel supply, schematically,

\[
 d_{rp}=\int dE\,d\Omega\,
 {\cal R}_r(E){\cal B}_{rp}(e)I_E(e)+n_{rp}.
 \tag{A11}
\]

Response, beam, mask, calibration, frame and directional convention belong to the operator. Any nuisance fit and covariance must be retained jointly. For genuinely bolometric reconstructed brightness Ihat, assume
∫|I−Ihat|dΩ≤εI and ||R−Rhat||≤εR, where εR includes the derivative estimation error and all declared approximation terms.

For each direction, the integrand operator B_e in Eq. (A9) satisfies 0≤B_e≤Id by Eq. (A7)'s pointwise proof. Therefore

\[
 \|{\cal L}_I-{\cal L}_{\hat I}\|_{\rm op}\le\epsilon_I.
 \tag{A12}
\]

Let λhat=λ_min(L_Ihat)>εI and σhat=−L_Ihat⁻¹Rhat. Subtract the two transport equations and use the Rayleigh bound λ_min(L_I)≥λhat−εI. This proves

\[
 \boxed{\|\sigma-\hat\sigma\|\le
 {\epsilon_R+\epsilon_I\|\hat\sigma\|\over\hat\lambda-\epsilon_I}.}
 \tag{A13}
\]

The estimate retains units, permits nonlinear angular anisotropy, and gives an executable sensitivity criterion. Its denominator is an observed-response certificate, not a MES anchor. A signed component-separated Ihat can be used algebraically if the error bound certifies its distance from the physical positive I; positivity of the true field remains the premise.

Finite spectral coverage requires an explicit tail/model error in εI. Moreover ∫E₁^E₂ E⁴∂_E f dE=[E⁴f]₁²−4∫E₁^E₂ E³f dE: a finite band has boundary transport terms. Applying the uncorrected bolometric Eq. (A5) separately to channels is invalid. Frequency data instead constrains f and the bolometric completion, or carries its own boundary terms into R. This is a concrete calibration requirement rather than a spectral closure assumption.

The tensorized state may append (ρ,q,π,H₃,H₄,R,σ) with frame and units. x remains the sample-by-functional array; anchor-Q remains the declared body gauge/margin. The report's support-utilization F profile, exceedance surface Π_ϕ(c|η,L), and structured G_F depth path retain their respective support, law and cross-depth dependence. Three F namespaces remain explicit: the legacy filling_fraction.py quantity F_cert=x_C/U is a certified normalized diagnostic and rejects a material/volume-occupancy interpretation; the current typefree/report F_sup is directional support utilization; the skill/manuscript F_nu is occupancy under a separately declared measure ν and support. Neither a measure for F_nu nor a material volume is inferred from Eq. (A13). Deterministic feasible images can be computed before any probability law; posterior pushforward belongs to HTT.

## R10. Checkpoint and next executable use

The research unit is complete as a conditional theorem, constructive examples and observation contract. A downstream feature extractor can construct L as a 5×5 symmetric matrix from measured brightness moments, compute λhat, and report Eq. (A13) when the two error certificates are supplied. If R is unavailable, it should return the measured radiative tensors and L, retaining the derivative-input obligation.

For the requested independent review, check the angular integration-by-parts sign, the six-term STF4 trace decomposition, the source 2/7 versus 10/7 discrepancy, and the perturbation denominator in Eq. (A13). No data product, native transfer, posterior, or Bianchi-family acceptance is promoted by this report.

한국어 요약: 주파수별 광자 분포를 적분한 복사 응력과 온도 Q/O를 정확히 구별했다. 양의 밝기는 전단에 대한 양의 5차원 반응 연산자를 만들며, 수송 미분값이 주어지면 비선형 조건에서도 전단과 유한 오차 구간을 대수적으로 구할 수 있다. 순수 온도 쌍극자에서도 복사 비등방 응력이 생기는 정확한 예와 비공축 수송 예를 계산했다. 원전의 2/7 계수와 10/7 계수 불일치를 직접 Liouville 유도 및 Wolfram 계산으로 분해했다. 경험적 적용에는 볼로미터 보완오차와 복사 미분 관측량이 필요하다.

