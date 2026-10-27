# Angular calculus v15: an observable-specific extension

**Internal research update, 26 October 2026.** This version integrates the supplied *An Entropic Angular Calculus for Relativistic Kinetic States*, Papers I and II, v15, into the previous five-loop HTT report. It retains the previous physical derivations and adds explicit kinetic calibration, response-preserving reconstruction, and detector-specific error bounds.

## The adopted theoretical reference

The two October 24 drafts replace the older Teff theoretical description for this report. Paper I uses energy-calibrated ray equilibria and a spectral–angular entropy split. Paper II adds particle-number information, a chemical-potential coordinate, massive velocity-dressed responses, and quantitative angular-rank sensitivity. Their exact uploaded source identities are recorded in the accompanying package.

Both papers condition their construction on an observer \(U\), with \(U^2=-c^2\). The previous report uses a unit field \(u=U/c\). Their momentum direction is the propagation direction \(e\); the outward observed sky direction of the optical chapters is \(n=-e\). These conversions are applied before combining responses.

The phrase “effective frame” in the Paper II source names a calibrated thermochemical description at fixed \(U\). It does not select a Lorentz observer by optimization. The adopted variables are
\[
\mathcal N(e)=\mathcal D\int E^2f(E,e)\,dE,\qquad
\mathcal E(e)=\mathcal D\int E^3f(E,e)\,dE,
\quad \mathcal D=\frac{g_s}{(2\pi\hbar)^3c^3}.
\tag{V1}
\]
Energy-only calibration produces a zero-chemical-potential reference, with \(\eta=0\) and unit fugacity. Joint calibration solves for \(T(e)\) and \(\eta(e)=\mu(e)/(k_BT(e))\) on the statistics-dependent domain.

For massless rays,
\[
\mathcal N=\mathcal D(k_BT)^3 I_2^\xi(\eta),\qquad
\mathcal E=\mathcal D(k_BT)^4 I_3^\xi(\eta).
\tag{V2}
\]
The independent population coordinate is \(\mathcal Q=\mathcal N^4/(\mathcal D\mathcal E^3)\). We use the calligraphic symbol here to distinguish this calibration ratio from the HTT anchor gauge \(Q\).

## What the new calculations add

### 1. Resolve the observable, rather than reconstructing everything

The previous radiative shear operator is
\[
\mathcal L_I(S)=\frac{8\rho}{15}S+
\frac{10}{7}\operatorname{STF}(S\pi)-I_4:S.
\tag{V3}
\]
It depends on energy-weighted brightness harmonics of degrees \(0,2,4\). The v15 maximum-entropy fit matches declared energy moments exactly. Therefore a fit through \(L=4\) preserves (V3), even when its unresolved spectral or higher-angular entropy is positive.

This gives a concrete stopping criterion for a reconstruction: once the required response is preserved to the target uncertainty, unresolved information that the response does not use need not trigger additional fitting. The transport residual on the other side of the shear equation still has its own derivative, flux and source inputs.

The static toy uses
\[
w(\mu)=1+0.3P_2(\mu)+0.2P_4(\mu)+0.15P_6(\mu).
\tag{V4}
\]
Its two reconstructions give:

| Retained angular rank | Angular entropy gap / isotropic entropy | Operator error / total energy density |
|---|---:|---:|
| \(L=2\) | \(3.73710\times10^{-4}\) | \(6.54244\times10^{-3}\) |
| \(L=4\) | \(9.37161\times10^{-5}\) | \(1.22\times10^{-15}\) numerically; zero algebraically |

The finite-domain entropy bound for the \(L=2\) operator error is \(1.37594\times10^{-2}\), above the observed toy error. The tested shear error is \(0.00737521\) in the declared shear unit, below its \(0.02803358\) certificate.

### 2. Turn an angular entropy deficit into a conditioning certificate

For total radiation energy \(\rho\), write \(w=4\pi I/\rho\) and normalize the energy-calibrated angular entropy by its isotropic value:
\[
\delta=1-\langle w^{3/4}\rangle.
\tag{V5}
\]
The derived bridge is
\[
\left\|\mathcal L_I-\frac{8\rho}{15}\mathrm{Id}\right\|_{\rm op}
\le\rho\sqrt{\frac{8\delta}{3}}.
\tag{V6}
\]
The proof combines a scalar divergence inequality with a centered, energy-matched radiation response. It gives an explicit sufficient inverse condition \(\delta<8/75\). Direct operator eigenvalues can certify a wider domain; the condition is designed for situations where the entropy deficit is the available scalar input.

This connects the entropy geometry to a physical inverse scale. It does not require equating temperature morphology with shear: the operator and the transport residual provide the intervening map.

### 3. Separate population information from Doppler temperature

For a pointwise massless Lorentz transformation, number and energy per solid angle carry Doppler weights three and four:
\[
\mathcal N'=D^3\mathcal N,\qquad
\mathcal E'=D^4\mathcal E,\qquad
\mathcal Q'=\mathcal Q
\tag{V7}
\]
at corresponding aberrated directions. Thus the calibrated \(\eta\) is a Doppler-weight-zero sky scalar. At first order, the contrast \(4\,\delta\ln\mathcal N-3\,\delta\ln\mathcal E\) cancels a purely thermal/Doppler perturbation.

Finite beams change this inference because they mix spectra before calibration. For rays with common \(\eta_0\), a common positive energy-independent beam gives
\[
\frac{\mathcal Q_{\rm beam}}{Q_\xi(\eta_0)}
=\frac{\langle T^3\rangle_B^4}{\langle T^4\rangle_B^3}.
\tag{V8}
\]
The sharp temperature-range envelope is an application of the established generalized Kantorovich inequality. Its use here is to turn unresolved thermal mixing into a calibrated \(\eta\)-bias interval. For a temperature ratio \(T_{\max}/T_{\min}=2\), the minimum ratio is \(0.51391970736\); for mixed Planck rays this corresponds to \(\eta_{\rm eff}=-0.42440662570\). These values are illustrative finite-range examples.

Even averaging the full sky of a boosted isotropic blackbody produces an apparent calibrated offset. At the illustrative \(\beta=0.00123\), the value is approximately \(-1.4127\times10^{-6}\). The resolved rays remain thermal. The observable lesson is to apply the beam and bandpass before interpreting a population coordinate.

### 4. Bound the actual detector response

The new response-frontier calculation keeps number and energy fixed and constrains the residual kinetic entropy. A signed detector tilt of the calibrated occupation produces an extremizing state. The Bregman three-point identity proves exact upper or lower attainment at its corresponding entropy budget.

At small budget \(\epsilon\), the response scale is \(\sqrt{2\epsilon\chi_K}\), with
\[
\chi_K=\int W\left[K-\operatorname{Proj}^{W}_{\{1,E\}}K\right]^2d\nu_U,
\qquad W=g(1+\xi g).
\tag{V9}
\]
The projection removes changes already determined by population and energy measurements. For the bounded Gaussian detector kernel in the toy, the calibrated-to-unprojected local width ratios are \(0.7032\) (MB), \(0.7102\) (BE), and \(0.6737\) (FD). Finite-amplitude curves and independent quadrature checks accompany the derivation.

## How all five previous loops are updated

| Previous loop | Added v15 interface | Preserved physical target |
|---|---|---|
| Low-\(\ell\) radiation/shear | Exact \(L=4\) response preservation and entropy-derived stability | Infer shear from a calibrated radiation transport residual |
| Dipole | Population contrast, beam-bias envelope and spectral response bounds | Separate physical responses using independent channels and common covariance |
| Beyond-FLRW kinematics | A calibrated radiation tensor can be compared with the radial/transverse optical shear image | Common congruence, clock and observer-frame closure |
| Bianchi geometry | Positive kinetic states provide explicit radiation stress inputs to geometric constraints | Full curvature compatibility and family-equivalence tests |
| \(H(z,n)\) | Spectral and angular calibration errors can enter the distance-response nuisance model | Joint optical coefficients and finite-distance remainders |

The static angular calculus supplies the kinetic side of these interfaces. The optical and geometric maps in the preceding report retain their own equations. For example, the same-frame shear inferred from radiation can be compared with the optical E2/radial STF2 closure, while Bianchi compatibility additionally consumes the spatial curvature tensor.

## Tensorized interpretation and execution consequence

The underlying carrier \(X\) retains the shared physical or observable tensor state; \(x\) remains its declared sample-by-functional array. Neither is replaced by an entropy scalar. A detector support direction determines a kernel combination. A response-specific entropy bound then defines a compatible region in that direction, which can be propagated to the existing support functional \(F_{\rm sup}\) or anchor gauge \(Q\).

The certified ceiling diagnostic \(F_{\rm cert}\) and measure-dependent occupancy \(F_\nu\) retain their separate definitions. An exceedance \(\Pi\) requires its statistical law, and depth transport \(G_F\) requires its actual joint coupling. The number–energy ratio \(\mathcal Q\) is a further explicitly named observable, not a new meaning of the anchor gauge.

The corresponding research workflow is to declare the desired response first, identify its retained moment span, and then solve only the unresolved response directions. An entropy residual outside that span can remain while the target response is already exact. This is a concrete way to avoid allowing an unnecessarily complete reconstruction requirement to block useful physical results.

The old report and its successful checks are reused. The new work consists of the v15 source replacement, the four interfaces above, literature comparison and small static tests. No Git push, production controller change or native solver execution is part of this update. A separate internal novelty memorandum records established ingredients, specific candidate extensions, and the comparisons needed for a publication claim.


\clearpage

# Part I — Physical responses retained from the preceding report

The following five chapters retain the reviewed radiation, optical and geometric calculations. The v15 interfaces in Part II use the same observer, direction and unit conventions. The earlier review and computational receipts are included in the source package.

\clearpage

# Loop A — brightness moments, a positive shear response, and finite-error transport inversion

Owner: common/obsstat for the deterministic construction; MIO for conditional diagnostic images. Internal theory result, C0, transfer source none. Date: 2026-10-26. Repository comparison identity: \texttt{a55036ad09c5\allowbreak 3a9215dee328\allowbreak 2e425d37cfb9\allowbreak 5443}. No repository mutation, solver, ODE, or raw-data campaign is part of this result.

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
\(\int I[2(Se)\cdot(Te)-(e^TSe)(e^TTe)]\,d\Omega\) is symmetric in \(S,T\), proving self-adjointness. Cauchy–Schwarz gives (eᵀSe)²≤|Se|², so the integral is at least tr(S²M₂)≥m||S||². For the upper bound rotate e to the third axis:

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





\clearpage

\begin{center}\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{/workspace/scratch/ef61c9590364/HTT_TEFF_V15_EXTENSION_20261026/prior_baseline/figures/figure_a_radiation.pdf}\end{center}

**Analytical radiation response.** For \(I(n)=\rho[1+aP_2(n_z)]/(4\pi)\), the five shear-response eigenvalues are \(\rho(56-10a)/105\) (twice), \(\rho(56+5a)/105\) (twice), and \(\rho(56+10a)/105\). The lower curve is the certified moment bound. No measured CMB data are plotted.

\clearpage

# Loop B — an intrinsic CMB dipole as a calibrated observer-response problem

Owner: `dipole_loop_20261026`. Date: 2026-10-26. Scope: internal, solver-free theoretical research; non-claim-bearing observational design. Repository reference: \texttt{a55036ad09c5\allowbreak 3a9215dee328\allowbreak 2e425d37cfb9\allowbreak 5443}. No push, native solver, ODE, catalogue fit, or observed-sky likelihood was performed. Equations below distinguish exact local transformations, a controlled expansion, and conditional statistical inference. This is an actual R1–R10 unit under research-loop 1.0.0; a separate fresh review is assigned by the parent.

## R1. Question and completed research contract

The legacy dipole goal becomes the following concrete question: given a measured temperature dipole and additional spectral/angular channels, which registered observable can estimate or bound the intrinsic dipole relative to a specified reference frame? The target vector is a dimensionless temperature coefficient \(d\), not a global matter-tilt history. Its temperature amplitude is \(T_0|d|\), in kelvin. The observer velocity is \(v=c\beta\).

We construct the exact phase-space transformation, derive its second-order dipole–quadrupole relation, examine what spectral channels add, and give a nuisance-projected multichannel estimator with a finite bound. The needed extra input is identified explicitly: either a calibrated angular-coupling response to observer motion or a constrained intrinsic-multipole response. This advances the old local/global discussion to a usable observation contract without introducing a dynamical Bianchi transfer.

## R2. Sources and retained expressions

The source-matched starting point is *FROM A CMB SKY MAP TO PHYSICAL CONSTRAINTS*, PDF pp. 28–30, equations (9.1)–(9.10): incoming propagation direction is opposite outward sky direction, temperature has Doppler weight one, and the first-order generator includes both modulation and angular remapping. The same expressions appear in *20-report-1-*, PDF pp. 14–16, §12–13, together with processed-response quotient and depth-path qualifications. Exact repository packs \texttt{T5\_WU010\_LOC\allowbreak AL\_OBSERVER\_\allowbreak RESPONSE\_THE\allowbreak OREM\_PACK.md}, §§1–3, and \texttt{T6\_WU011\_PRO\allowbreak CESSED\_RESPO\allowbreak NSE\_QUOTIENT\allowbreak \_THEOREM\_PAC\allowbreak K.md}, §§1–3, were also read. These are retained, rather than re-labelled as new results.

Ellis, Maartens and MacCallum, *Relativistic Cosmology*, supplied PDF pp. 106–108 (printed pp. 90–92), equations (5.2), (5.7)–(5.9), define barycentric, particle and energy frames. PDF pp. 120–121 (printed pp. 104–105), equations (5.76)–(5.82), give momentum decomposition, scalar distribution and PSTF multipoles. Cercignani and Kremer, *The Relativistic Boltzmann Equation*, supplied PDF pp. 42–43 (printed pp. 31–32), §2.1 and equations (2.1)–(2.5), supply the scalar distribution and invariant phase-space construction. We use these local kinematic statements; their collision terms are not solved.

Primary literature located through Exa on 2026-10-26 is: Dai–Chluba [1403.6117v2](https://arxiv.org/abs/1403.6117v2), Planck [1303.5087v3](https://arxiv.org/abs/1303.5087v3), Yasini–Pierpaoli [1610.00015v4](https://arxiv.org/abs/1610.00015v4), and Roldan–Notari–Quartin [1603.02664v2](https://arxiv.org/abs/1603.02664v2). The first separates Doppler weights; the second constructs angular-coupling velocity estimators; the third models low-multipole spectral leakage, including nonlinear blackbody terms in Appendices B–C; the fourth exposes gravitational dipole contributions to Doppler/aberration estimators. Literature supports the observational strategy and its assumptions; it does not establish this project's calibration.

The latest retained \texttt{evidence/bas\allowbreak eline/resear\allowbreak ch/theory\_ex\allowbreak pansion.md}, T1–T15, concerns a different optical observable: \(-5\log[1+d_{\rm opt}\cdot n+S:nn]/\ln10\), with \(d_{\rm opt}=-A/(cH)\). Its acceleration–shear octupole and finite logarithm remainder are already derived. Here \(d\) denotes a radiation temperature dipole. Equal vector dimension or STF tensor rank does not identify these physical quantities.

## R3. Conventions and approximation hierarchy

Use signature \((-+++ )\), unit timelike \(u\cdot u=-1\), and physical photon energy \(\epsilon=-c p\cdot u>0\). A photon arriving from sky direction \(n\) has
\[
 p^a={\epsilon\over c}(u^a-n^a),\qquad u\cdot n=0,\quad n\cdot n=1.
\]
Thus the propagation direction in Ellis's convention is \(e=-n\). The changed observer is \(u'=\gamma(u+\beta)\), \(\gamma=(1-\beta^2)^{-1/2}\). Here \(\beta\) is dimensionless and spatial; \(c\), \(k_B\) and \(h=2\pi\hbar\) remain explicit in physical formulas.

For the second-order calculation introduce a bookkeeping parameter \(\lambda\): \(\beta,d=O(\lambda)\), \(Q=O(\lambda^2)\), and
\[
 T(n)=T_0[1+d\cdot n+Q:nn]+O(\lambda^3),\qquad Q=Q^{\mathsf T},\quad\operatorname{tr}Q=0.
\tag{B1}
\]
The displayed hierarchy is a mathematical expansion, not an empirical statement that the actual intrinsic quadrupole has this scaling. If an intrinsic quadrupole or higher mode is retained at first order, its boost leakage is included using the generator below and becomes part of the registered response/nuisance model. Positivity of the exact input temperature is assumed.

The reference frame in (B1) is specified by the adopted physical/statistical model; it is not automatically the radiation energy frame. For a blackbody sky with a small temperature dipole, bolometric intensity is proportional to \(T^4=T_0^4(1+4d\cdot n+\cdots)\). Since photon propagation is \(-n\), direct angular integration gives physical energy flux \(\mathcal F^i=-(4/3)cU_\gamma d^i+O(\lambda^2)\), where \(U_\gamma\) is radiation energy density. Thus its radiation energy frame removes this dipole to first order. A nonzero intrinsic dipole relative to a statistical reference frame and a zero-flux radiation frame can coexist as different frame definitions. A matter energy or particle frame introduces an independently specified current or stress tensor. This is the physical content of the frame distinction, not an arbitrary name change.

## R4. Candidate channels and exact observer change

Direct contraction, with the incoming-direction sign retained, gives
\[
 \epsilon'=\gamma\epsilon(1+\beta\cdot n),\qquad
 n'={n+[(\gamma-1)(\hat\beta\cdot n)+\gamma|\beta|]\hat\beta
       \over\gamma(1+\beta\cdot n)}.
\tag{B2}
\]
Replace \(\beta\) by \(-\beta\) to invert the angular map. Define
\[
 D={\epsilon'\over\epsilon}
 ={1\over\gamma(1-\beta\cdot n')}.
\]
The scalar occupation number therefore obeys exactly
\[
 f'(\epsilon',n')=f(\epsilon'/D,n(n')),
\quad I'_{\nu'}(n')=D^3I_{\nu'/D}(n(n')) .
\tag{B3}
\]
For \(I_\nu=B_\nu(T)=(2h\nu^3/c^2)[e^{h\nu/(k_BT)}-1]^{-1}\), equation (B3) gives the exact directional temperature
\[
 T'(n')=D\,T(n(n')) .\tag{B4}
\]
This follows by preserving \(\epsilon/(k_BT)\) for the same ray. At \(\beta\cdot n'>0\), the moving observer measures a hotter monopole, which checks the sign. Frequency-dependent occupation or intensity, rather than a fitted temperature alone, is the general input. Candidate discriminators are spectral low-multipole leakage and small-scale angular couplings, both linked by (B3).

## R5. Constructive second-order dipole–quadrupole calculation

At fixed observed direction, write \(b=\beta\cdot n'\), \(s=d\cdot n'\). The inverse aberration is \(n=n'-\beta+b n'+O(\lambda^2)\). Hence
\[
 d\cdot n=s-\beta\cdot d+bs+O(\lambda^3),\qquad
 D=1+b+b^2-\beta^2/2+O(\lambda^3).
\]
Multiplying, rather than adding separate Doppler and intrinsic templates, yields
\[
 {T'\over T_0}=1+(\beta+d)\cdot n'
 +b^2-\beta^2/2-\beta\cdot d+2bs+Q:n'n'
 +O(\lambda^3).
\tag{B5}
\]
Spherical averaging uses \(\langle n_i n_j\rangle=\delta_{ij}/3\). The relative mean shift, dipole vector \(a\), and temperature quadrupole \(K\) are consequently
\[
 m=-\beta^2/6-(\beta\cdot d)/3,\qquad
 a=\beta+d+O(\lambda^3),
\]
\[
 K=Q+\beta_{\langle i}\beta_{j\rangle}
       +2\beta_{\langle i}d_{j\rangle}+O(\lambda^3).
\tag{B6}
\]
In particular,
\[
 K-a_{\langle i}a_{j\rangle}
 =Q-d_{\langle i}d_{j\rangle}+O(\lambda^3).
\tag{B7}
\]
This is an explicit closure test. A free intrinsic quadrupole enters precisely where one might otherwise assign a dipole anomaly. Under the restricted assumption \(Q=0\), the residual is \(-dd_{\rm STF}\): its eigenvalues are \((-2|d|^2/3,|d|^2/3,|d|^2/3)\). It determines an unoriented dipole axis and amplitude, not its sign. With a bounded \(Q\), it becomes a bounded-contamination constraint. With unconstrained \(Q\), its interpretation is the stated response equation.

More explicitly, let \(M=K-aa_{\rm STF}\), suppose \(\|Q\|_F\leq q_{\max}\), and suppose the combined measurement and expansion error in \(\hat M\) is at most \(\delta_M\). Because \(\|dd_{\rm STF}\|_F=\sqrt{2/3}|d|^2\), the triangle and reverse-triangle inequalities yield
\[
 \sqrt{3/2}\max(0,\|\hat M\|_F-q_{\max}-\delta_M)
 \leq |d|^2
 \leq\sqrt{3/2}(\|\hat M\|_F+q_{\max}+\delta_M).
\tag{B7a}
\]
The upper amplitude bound is the square root of the right side. This is a second route to a finite intrinsic-dipole bound, conditional on a quantitative intrinsic-quadrupole envelope instead of an independent velocity channel. A simultaneous coverage event for \(\delta_M\) propagates to the same coverage for this interval. Its square-root sensitivity and unresolved dipole sign are visible in the formula. Deboosting by the fitted total dipole \(a\) leaves quadrupole \(Q-dd_{\rm STF}\) at this order, which is another direct interpretation of the same residual.

For a known nonzero \(\beta\) and a constrained/subtracted intrinsic quadrupole, define
\[
 R=K-Q-\beta\beta_{\rm STF}=L_\beta d,
\quad L_\beta d=\beta d^{\mathsf T}+d\beta^{\mathsf T}
                 -{2\over3}(\beta\cdot d)I.
\]
Direct multiplication and contraction give
\[
 \|L_\beta d\|_F^2=2\beta^2|d|^2+{2\over3}(\beta\cdot d)^2,
\quad
 d={1\over\beta^2}\left(I-{\hat\beta\hat\beta^{\mathsf T}\over4}\right)R\beta.
\tag{B8}
\]
Thus all three components survive this ideal map. Its smallest singular value is \(\sqrt2|\beta|\), and tensor error \(\delta_R\) produces \(|\delta d|\leq\delta_R/(\sqrt2|\beta|)\). The conditioning is finite while the absolute inverse gain diverges as the known boost tends to zero. An arbitrary intrinsic quadrupole is a five-dimensional nuisance and must be calibrated or constrained before using this inverse.

## R6. Independent spectral derivation and closure

Set \(G_\nu=T_0\partial_TB_\nu\), \(H_\nu=T_0^2\partial_T^2B_\nu\), evaluated at \(T_0\). Expansion of the exact Planck function, independently of the boost derivation, gives
\[
 I'_\nu=B_\nu(T_0)+G_\nu\Theta'+\tfrac12H_\nu(\Theta')^2+O(\lambda^3).
\]
For \(x=h\nu/(k_BT_0)\), \(H_\nu/G_\nu=x\coth(x/2)-2\). Its intensity quadrupole is
\[
 I'_{\nu,2}=\left[G_\nu K_{ij}
       +\tfrac12H_\nu a_{\langle i}a_{j\rangle}\right]n'_in'_j
       +O(\lambda^3).
\tag{B9}
\]
The observed monopole similarly is
\[
 \bar I'_\nu=B_\nu(T_0)+G_\nu m+H_\nu|a|^2/6+O(\lambda^3).
\tag{B10}
\]
These equations retain the \(d^2\) term; dropping it requires a different, explicitly recorded small-intrinsic-dipole hierarchy. If the mean temperature itself is fitted, the \(G_\nu m\) term is absorbed into that parameter at this order. Directional blackbodies and spectrally distorted angular averages are consistent: averaging is nonlinear in temperature.

Differentiate (B3) directly to verify the intensity generator:
\[
 \delta_\beta I_\nu=(\beta\cdot n)(3-\nu\partial_\nu)I_\nu
 -[\beta-(\beta\cdot n)n]\cdot\nabla_{S^2}I_\nu.
\tag{B11}
\]
The identity \((3-\nu\partial_\nu)G_\nu=G_\nu+H_\nu\) then makes intrinsic-dipole leakage into the quadrupole proportional to \((2G_\nu+H_\nu)\beta_{\langle i}d_{j\rangle}\). Kinematic monopole leakage has the same spectral shape, with coefficient \(\beta_{\langle i}\beta_{j\rangle}/2\). The \(H_\nu\) contribution from intrinsic blackbody nonlinearity completes the total \(a a_{\rm STF}/2\) in (B9).

This calculation specifies what a spectral closure measurement tests and why a frequency count alone is insufficient for assigning an arbitrary blackbody sky to a frame. Yasini–Pierpaoli's proposed separation uses a rest-frame multipole model, small-anisotropy treatment, and control of neighbouring-mode leakage; Appendix A explicitly assumes Gaussian uncorrelated rest-frame multipoles. Their Appendix C retains intrinsic-dipole nonlinear corrections. Our contract keeps these assumptions visible instead of treating their forecast as a model-free measurement. This is a scope clarification and a reusable calculation, with no novelty or new no-go assertion.

## R7. Executed CAS and an independent angular channel

Connected Wolfram Language evaluation completed the lightweight algebra in `cas/loop_b.wl`. The clean output was
\[
 \{0,\operatorname{diag}(2\beta^2,2\beta^2,8\beta^2/3),\{0,0,0\},0,0\}.
\]
The entries check (B5), the Gram matrix of (B8), its inverse, the spectral Euler identity, and the Planck spectral ratio. The receipt is `cas/loop_b_receipt.json`. Rotating \(\beta\) to the positive \(z\)-axis is justified by spatial covariance; no pixel fit, xAct calculation, ODE, or native transfer is inferred from these checks.

For the angular channel, the retained weight-one temperature generator is \(\beta[\mu-(1-\mu^2)\partial_\mu]\). The normalized spherical-harmonic recurrences give
\[
 \delta_\beta Y_{\ell m}=\beta[(\ell+1)c_{\ell+1,m}Y_{\ell+1,m}
                       -\ell c_{\ell m}Y_{\ell-1,m}],
\quad c_{\ell m}=\sqrt{{\ell^2-m^2\over4\ell^2-1}}.
\]
For zero-mean statistically isotropic rest-frame fluctuation modes with power \(C_\ell\), taking \(\ell\geq2\), this implies
\[
 \mathbb E[a'_{\ell m}a'^*_{\ell+1,m}]
 =\beta(\ell+1)c_{\ell+1,m}(C_\ell-C_{\ell+1})+O(\beta^2).
\tag{B12}
\]
Products across many modes therefore supply a response to \(\beta\) beyond the measured low-order dipole. Intensity-derived temperature maps require their actual bandpass modulation coefficient, so (B12) is not transplanted unchanged. Mask, beam, lensing, foregrounds, intrinsic dipolar covariance and the fitted power spectrum enter calibration. Roldan–Notari–Quartin identify physical dipolar-potential contributions that can mimic parts of these couplings; those contributions must be included or bounded when assigning this response to observer velocity.

## R8. Nuisance-projected estimate and finite intrinsic-dipole bound

Stack a measured three-component dipole and calibrated angular-coupling features into one vector \(y\), with known joint covariance \(C\succ0\). Optional spectral features obeying (B9) may be appended after their registered linearization. A simple six-parameter design is
\[
 y=H\theta+N\eta+r+\epsilon,\quad
 \theta=(\beta,d),\qquad H=\begin{pmatrix}I&I\\R_{\rm ang}&0\end{pmatrix}.
\tag{B13}
\]
Nuisance columns include allowed calibration patterns and physical competing responses. Define \(\bar N=C^{-1/2}N\), \(P=I-\bar N\bar N^+\), \(A=PC^{-1/2}H\), \(z=PC^{-1/2}y\). If \(\operatorname{rank}A=6\), then
\[
 \hat\theta=A^+z,\quad F=A^{\mathsf T}A,\quad
 \hat d=S\hat\theta,\quad V_d=SF^{-1}S^{\mathsf T},\qquad S=(0,I).
\tag{B14}
\]
Projection removes \(N\eta\) exactly because \(P\bar N=0\); substitution proves unbiasedness for \(r=0\), and multiplication of the Gaussian noise covariance proves the stated \(V_d\). For a declared projected remainder bound \(\|PC^{-1/2}r\|\leq\rho\), Gaussian noise with the registered fixed covariance gives the conservative finite coverage bound
\[
 |d|\leq|\hat d|+
 \sqrt{\chi^2_{3,1-\alpha}\lambda_{\max}(V_d)}
 +\rho\|SA^+\|_2
 \quad\text{with probability at least }1-\alpha.
\tag{B15}
\]
The proof adds the Gaussian marginal ellipsoid radius and the operator-norm bias bound. Correlations between dipole, frequency maps and quadratic products remain in \(C\); their separate likelihoods are not multiplied. Products of Gaussian sky modes are not exactly Gaussian, so a Gaussian feature law is a stated approximation; finite calibration can instead supply a valid event \(\|PC^{-1/2}\epsilon\|\leq q_{1-\alpha}\), replacing the two radius terms by \((q_{1-\alpha}+\rho)\|SA^+\|\). No numerical value of this bound is claimed here.

If the quotient rank drops, compute the estimable target combinations through \(S\ker A\). A dipole component is identified only when its target row annihilates \(\ker A\). Before nuisance projection, block elimination in (B13) gives \(\operatorname{rank}H=3+\operatorname{rank}R_{\rm ang}\). Thus a velocity measurement along only one direction adds one scalar constraint: it bounds the parallel intrinsic dipole, while perpendicular components require additional response or compact external bounds. A three-component amplitude bound such as (B15) requires three surviving velocity directions. For the transparent special case \(R_{\rm ang}=I\), \(\hat d=\hat a-\hat\beta\) and \(V_d=C_a+C_\beta-C_{a\beta}-C_{\beta a}\). This also exposes the practical role of shared-sky covariance. Compact external parameter bounds can still give a finite identified-set envelope when rank is deficient. This is the existing nuisance-quotient logic applied to a named dipole observable.

## R9. Observable contract and truncation control

The deliverable inputs are absolute or jointly calibrated frequency maps, bandpasses, common direction conventions, beams/pixel windows, masks, the actual low-mode fit operator, coupling-mode range, full shared covariance or calibrated noise law, nuisance columns, and the rest-frame statistical/physical model used for \(R_{\rm ang}\). Output is \(\hat d,V_d\), the bound (B15), projected rank/singular values, and spectral closure residuals from (B9)–(B10). Units are dimensionless until multiplying by \(T_0\). Any local matter velocity comparison needs its own frame and selection definition.

Truncation is a measurable obligation. For an exact positive polynomial input sky, scale \((\beta,d,Q)\mapsto(t\beta,td,t^2Q)\) in (B4), obtaining the dimensionless \(F(t,n')=T'(t,n')/T_0\). On a compact domain \(|\beta|\leq b_{\max}<1\), its third derivative is bounded. Taylor's theorem gives \(|R_T|\leq M_3/6\), with \(M_3=\sup_{t\in[0,1],n'}|\partial_t^3F|\). A certified derivative bound or exact-map difference supplies this value for registered inputs; an additional intrinsic sky remainder is propagated separately. Full-sphere dipole and quadrupole errors then obey \(|R_a|\leq\sqrt3 M_3/6\) and \(\|R_K\|_F\leq\sqrt{15/2}M_3/6\); processed operators propagate these into \(\rho\). These bounds follow from projector contraction and normalized spherical moments. Foreground and calibration uncertainty are additional terms, not absorbed into a formal Taylor symbol.

## R10. Verdict and resume point

Established inputs are the scalar phase-space law and local Lorentz response. Derived results are (B5)–(B11), the calibrated inverse (B8), the angular response (B12), and the conditional finite bound (B15); selected algebra was executed and passed. The actual observing design's rank, covariance, calibration remainder and observed intrinsic-dipole constraint remain unresolved input-dependent quantities.

The next concrete action is to instantiate (B13) from a specified released dipole plus angular-coupling product, propagate bandpasses and sky support through the same estimator, and compute \(\sigma_{\min}(A)\), \(V_d\) and \(\rho\). A radiation dipole or a calibrated endpoint velocity constrains one event's radiation–observer relation. A global matter-tilt history additionally requires matter-frame observables, depth windows and dynamical response. This separate obligation follows the supplied reports' source distinction and is preserved in the resume contract.

### Physics/math and claim audit

The four project skills read were `htt-physics-math-audit`, `htt-local-global-discrimination`, `htt-claim-firewall` and `htt-claim-provenance-ledger`; their existing equation, frame, rank and claim controls are applied here. No project policy was changed.

| Item | Scoped verdict | Evidence or required application |
|---|---|---|
| Dimensions and signs | Checked | \(\epsilon\) is energy, \(d,\beta,Q\) dimensionless; forward hot-spot and zero-boost limits agree. |
| Exact transform and expansion | DERIVED | (B2)–(B6); second-order residual zero in CAS. |
| Spectral closure and inverse | DERIVED | (B8)–(B11); Gram, inverse and spectral identities checked. |
| Statistical bound | CONDITIONAL | Known joint law/design, registered nuisance image and remainder bound. |
| Observed intrinsic dipole | SPECIFIED | Requires actual calibrated input products and quotient-rank evaluation. |
| Global-tilt inference | Separate target | Requires matter/depth/dynamical response in addition to this local law. |

The proposed change is a research construction only. The tests performed are symbolic identities; the tests to run at application are injected-boost recovery, bandpass consistency, mask mean-field and nuisance-rank calibration under the same operator order. Rank loss, unbounded competing intrinsic covariance, or a missing calibration remainder suspends the associated physical assignment while retaining valid response diagnostics. Claims are owned by `common` for the transformations, `obsstat` for features, and `htt` for a future model-dependent interval. Transfer source is `none`, tier is exploratory `C0`, and no claim is promoted to observed or native-solver validation. No strong no-go or novelty result is proposed, so NG1–NG7 admission is not invoked. The only packaging artifacts are the requested research note, claim record and executed algebra receipt; no permanent project registry was edited.





\clearpage

\begin{center}\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{/workspace/scratch/ef61c9590364/HTT_TEFF_V15_EXTENSION_20261026/prior_baseline/figures/figure_b_dipole.pdf}\end{center}

**Conditional dipole envelope.** The scalar necessary bounds on \(|d|^2\) use the full Cartesian Frobenius norm, \(q_{\max}=0.10\), and \(\delta_M=0.02\). These declared illustrative amplitudes are not observations or a fitted confidence region.

\clearpage

# LOOP C — A local covariant optical inverse for expansion, shear, vorticity and acceleration

**Owner:** HTT internal theory loop C. **Date:** 2026-10-26. **Scope:** solver-free, local theory and exact finite algebra; no observational estimate. Source baseline is \texttt{a55036ad09c5\allowbreak 3a9215dee328\allowbreak 2e425d37cfb9\allowbreak 5443}, supplied by the parent inventory. This report does not change the production repository or claim acceptance. The preceding scoped review is retained in the source package.



## R1 — Question and completed construction

Can an optical catalogue add the antisymmetric velocity-gradient sector missing from a radial local Hubble diagram, while retaining which congruence and reference frame the measurement concerns? The result is an explicit twelve-component inverse, its exact full-sphere response norm, and finite-catalogue Jacobian. It also supplies a radial–transverse shear closure test and separates two physically different acceleration measurements.

The retained affine radial recipe already gives bulk motion, expansion and shear: `20-report-1-.txt`, §13, PDF p15; the source inventory also locates it in `legacy_reconstruction_chapter.md`. This loop adds the optical justification, transverse inversion, reference-frame kernel and joint carrier contract. The shear/vorticity E/B interpretation is established literature, not a claim of first discovery.

## R2 — Sources and convention matching

The local geometric starting point is Ellis, Maartens and MacCallum, *Relativistic Cosmology*, printed pp80–82, PDF pp96–98, equations (4.26)–(4.34). Its projected connecting-vector equation gives nearby relative velocity; (4.32) gives directional expansion and (4.33) gives direction change in a Fermi frame. The text explicitly restricts the linear description to a smooth continuum in a sufficiently small neighbourhood. Printed p192, PDF p208, equations (8.39)–(8.40), supplies the optical Hubble coefficient, including acceleration.

Heinesen and Korzyński, [PRD 110, 043525 (2024)](https://doi.org/10.1103/PhysRevD.110.043525), [arXiv:2406.06167v2](https://arxiv.org/html/2406.06167v2), equations (9)–(12), Appendix C and Appendix E, supplies the null-boundary derivation and vector-harmonic interpretation. Its Appendix C retains acceleration even though the main-text drift expansion specializes to geodesic observers. The final Appendix-C equation is (C10) in the paper numbering and (46) in the retrieved HTML. These different labels refer to the same displayed expansion. Marcori et al., [PRD 98, 023517 (2018)](https://doi.org/10.1103/PhysRevD.98.023517), [arXiv:1805.12121](https://arxiv.org/abs/1805.12121), treats general-observer direction drift and distinguishes parallax from aberration drift. Exa search and primary HTML retrieval were performed on 2026-10-26.

The project convention is fixed by \texttt{FROM\_A\_CMB\_S\allowbreak KY\_MAP\_TO\_PH\allowbreak YSICAL\_CONST\allowbreak RAINTS.txt}, §5, PDF pp17–18. The metric is \((-+++ )\), \(u^a u_a=-1\), and geometric rates differentiate proper length \(s=c\tau\). Thus
\[
\nabla_bu_a=H_g h_{ab}+\sigma_{ab}+\omega_{ab}-A_a u_b,
\quad \omega_{ab}=\epsilon_{abc}\omega_c,\quad\epsilon_{123}=+1.
\tag{C1}
\]
The vector \(\omega\) is therefore the project's axial convention, with its stated sign. We do not silently replace it by half the ordinary Euclidean curl. Define auxiliary physical-rate coordinates
\[
h=cH_g,\quad S=c\sigma,\quad v=c\omega,\quad\alpha=cA.
\tag{C2}
\]
All four have inverse-time units; physical four-acceleration is \(c^2A=c\alpha\). The state carrier retains the original geometric \(\sigma,\omega,A\).

## R3 — Assumptions and observable definitions

Let a \(C^3\) timelike field describe observer and emitters in a convex normal neighbourhood. Work before caustics, with geometric optics, differentiable source tracking and a specified Fermi–Walker transported observer triad. The expansion is local in source distance, not a perturbation about FLRW. No Einstein matter equation, dust equation of state or Bianchi model is needed for the leading kinematic map.

Let \(n\) point outward toward a source and let \(r\) be an independently calibrated local optical distance whose first-order normalization equals observer-normalized affine distance. Angular-diameter and luminosity distances have this normalization under the usual optical conditions. Define
\[
d(n)=\lim_{r\to0}\frac{cz(n,r)}r,
\qquad \mu(n)=\lim_{r\to0}\frac{dn_{\rm obs}}{d\tau},
\qquad P(n)=I-nn^T.
\tag{C3}
\]
No division by directional Hubble rate is required; contracting directions with zero or negative leading redshift remain mathematically admissible. Estimating these limits from a finite survey requires a distance-window and remainder model. A sparse set of bound sources is not automatically a sample of this continuum.

## R4 — Candidate response and its optical, rather than Newtonian, origin

The candidate is
\[
\boxed{d=h+S:nn-\alpha\cdot n,
\qquad\mu=PSn+n\times v.}
\tag{C4}
\]
The radial sign follows by contracting (C1) with the past-directed, observer-normalized ray \(\ell=-u+n\): \(c\ell^a\ell^b\nabla_a u_b=h+S:nn-\alpha\cdot n\). Antisymmetry removes \(\omega\). This is the first optical redshift–distance coefficient, as in Ellis (8.39)–(8.40), after converting Ellis's incoming photon direction to outward \(n\).

For a simultaneous connecting vector \(\xi=rn\), Ellis (4.29) gives projected relative velocity \(cD_\xi u\). Splitting its radial and transverse parts yields \(\dot r/r=h+S:nn\) and \(\dot n=PSn+n\times v\). This establishes the spacetime kinematics, but simultaneous separation alone is insufficient to establish apparent sky drift. The following null-boundary step closes that gap.

## R5 — Optical lemma and exact inverse

Consider two infinitesimally separated light rays connecting the same observer and emitter worldlines. Set \(k=E(u-n)\). Their deviation vector \(X\) obeys the endpoint conditions \(X_O=u_O\), \(X_E=u_E/(1+z)\). Smooth endpoint expansion and the null Jacobi equation imply
\[
P\nabla_kX\big|_O=P\nabla_ku\big|_O+O(r).
\]
The derivative of the observed direction is
\[
\frac\mu c=PA-\frac1E P\nabla_kX
=PA-P(A-\nabla_nu)+O(r)
=P\nabla_nu+O(r).
\tag{C5}
\]
The endpoint factor contributes only a multiple of \(u_O\) at leading order and disappears under \(P\). Curvature and second derivatives enter the next distance order through the Jacobi and endpoint expansions. This derivation follows the structure of Appendix C while displaying the acceleration cancellation explicitly. It proves (C4) for an accelerated common congruence as well as its geodesic specialization.

Consequently a term \(cPA\) must not be appended independently to (C4): it would count the observer aberration while omitting the compensating retarded emitter motion. On bounded normal neighbourhoods the omitted rate terms have size \(O(crK_2)\), where \(K_2\) contains curvature, second derivatives of \(u\), and quadratic first derivatives. This is an asymptotic order statement; no finite survey error constant is certified here.

Write \(\langle f\rangle=(4\pi)^{-1}\int f\,d\Omega\). The isotropic moments \(\langle n_in_j\rangle=\delta_{ij}/3\) and \(\langle n_in_jn_kn_l\rangle=(\delta_{ij}\delta_{kl}+\delta_{ik}\delta_{jl}+\delta_{il}\delta_{jk})/15\) give the inverse
\[
h=\langle d\rangle,\qquad
\alpha=-3\langle dn\rangle,\qquad
S_{ij}=\frac{15}{2}\left\langle d(n_in_j-\delta_{ij}/3)\right\rangle,
\tag{C6}
\]
\[
S_{ij}=5\langle\mu_{(i}n_{j)}\rangle,
\qquad v=-\frac32\langle n\times\mu\rangle.
\tag{C7}
\]
The second shear formula has zero trace because \(\mu\cdot n=0\). To verify its normalization directly, average \(\mu_i n_j\): the shear contribution is \(S_{ij}/3-2S_{ij}/15=S_{ij}/5\); symmetrization removes rotation. For rotation, \(n\times(n\times v)=n(n\cdot v)-v\) averages to \(-2v/3\). These computations fix both the factor and the sign.

Use orthonormal scalar harmonics and define \(E_{\ell m}=\nabla_{S^2}Y_{\ell m}/\sqrt{\ell(\ell+1)}\), \(B_{\ell m}=n\times E_{\ell m}\). For \(f=S:nn\) and \(g=v\cdot n\),
\[
\mu=\tfrac12\nabla_{S^2}f+n\times\nabla_{S^2}g,
\quad \mu^E_{2m}=\frac{\sqrt6}{2}f_{2m},
\quad\mu^B_{1m}=\sqrt2g_{1m}.
\tag{C8}
\]
Thus \(\nabla_{S^2}\cdot\mu=-3f\); the oriented surface curl of the B part is \(-2g\). Isotropic expansion produces no transverse signal. An additional \(PD\) term would give \(\mu^E_{1m}=\sqrt2(D\cdot n)_{1m}\) and \(D=\tfrac32\langle\mu\rangle\). This is a separate population/reference response, not the common-congruence \(A\).

## R6 — Frames, clocks, sources and discriminating limits

Let the catalogue triad rotate relative to Fermi–Walker axes with angular velocity \(\Omega\), defined by \(\dot e_i=\Omega\times e_i\). Components then drift by \(-\Omega\times n=n\times\Omega\). Its measured B1 coefficient is
\[
v_{\rm cat}=c\omega+\Omega.
\tag{C9}
\]
A calibrated nonrotating triad makes (C7) a physical vorticity measurement. Merely setting the mean quasar spin to zero selects an astrometric frame; it does not independently establish \(\Omega=0\) for a rotating matter congruence. Physical vorticity and tetrad rotation are different objects even though this observation channel sums them.

At first order in small peculiar velocities, observer translation \(V\) relative to the chosen source frame contributes \(-PV/r\), while source slip contributes \(Pv_{\rm slip}/r\). This local expression is not a finite-distance cosmological parallax transfer law. A relative velocity drift contributes secular aberration \(P\dot V/c\) under the accompanying stationary-source/reference closure. The coefficient measures \(\dot V/c\) in that specified reference, and need not equal the congruence four-acceleration \(cA\). Distant quasars have jets, structural centroid drift, source velocities and propagation corrections; declaring them dust would remove real nuisance terms without evidence.

The two E1 responses \(PD\) and \(-PV/r\) are identical angular patterns in one shell. Two distinct known distances give the coefficient matrix with rows \((1,-1/r_j)\), invertible when \(r_1\ne r_2\). This separates those two idealized coefficients only if their shared depth laws and source populations are valid. A smooth unknown source-slip gradient can mimic physical shear or vorticity across every shell.

Let \(k=d\tau/dt_{\rm cat}>0\). The transverse response becomes \(k[PSn+n\times(v+\Omega)]\). Radial distances/redshifts provide an independent rate scale. If \(S\ne0\), the E2 closure measures \(k\), in principle: \(k=\langle\mu_E,PSn\rangle/\langle PSn,PSn\rangle\). When \(S=0\), a transverse-only amplitude cannot calibrate the clock. Distance-scale uncertainty must likewise be carried as a radial calibration nuisance.

Useful limiting cases are FLRW comoving motion, where \(S=v=\alpha=0\) and \(\mu=0\); pure shear, which gives E2 only; rigid local rotation, which gives B1 only; and a common accelerated congruence with vanishing instantaneous spatial gradient, where the radial acceleration dipole survives while the leading transverse field vanishes.

## R7 — Actual algebra and response-rank checks

`cas/loop_c.wl` was executed with the connected Wolfram Language evaluator. Exact monomial integration verifies (C6)–(C7), the E1 inverse, and
\[
\left\langle d^2+|\mu|^2\right\rangle
=h^2+\frac13 S:S+\frac13|\alpha|^2+\frac23|v|^2.
\tag{C10}
\]
With an extra E1 coefficient \(D\), its right-hand side gains \(2|D|^2/3\). Every returned residual was exactly zero; the response is preserved in `cas/loop_c_wolfram_receipt.json`. WolframContext returned an internal error; the evaluator itself succeeded. Optional SymPy import failed in the available Python environment. A dependency-free exact rational check replaced that finite-design calculation.

In orthonormal STF coordinates, (C10) gives the ideal full-sphere Gram diagonal \((1,I_5/3,I_3/3,2I_3/3)\). Radial rank is nine, transverse rank eight, and joint rank twelve. `python cas/loop_c_check.py` also verified these ranks on twelve explicit rational unit directions: coordinate axes, the three positive 3–4–5 pair directions, and their antipodes. Adding three unknown triad-spin columns leaves rank twelve and creates exactly three kernel directions \((\delta v,\delta\Omega)=(-q,q)\). The output is `cas/loop_c_python_receipt.json`. These checks validate polynomial identities and a finite design; they do not constitute four-axis spacetime CAS validation.

## R8 — Verdict and closure conditions

The local inverse is constructed under R3. Its geometric origin and exact angular normalization are established; optical input and algebra agree. Its literature-known ingredients are explicitly credited. The project addition is the joined observation map with calibrated physical interpretation, the acceleration distinction, and a usable response/closure contract.

The shear consistency residual is
\[
C_{2m}=\mu^E_{2m}-\frac{\sqrt6}{2}d_{2m}.
\tag{C11}
\]
It vanishes in the leading common-clock/common-congruence model. E1 and higher multipoles are additional residual channels. Their nonzero values diagnose failure of a collection of assumptions or finite-distance effects; assigning a particular cause requires the corresponding nuisance/transfer model. No universal strong no-go or new impossibility claim is adopted. The explicit finite linear kernel is retained as a response property with its stated design and nuisance assumptions. Independent review is the remaining acceptance step.

## R9 — Joint observable image and the existing x·Q·F·Pi·G_F objects

For source \(a\), choose measured tangent basis \(t_{aA}\). A Jacobian row for \(\theta=(h,S_I,\alpha_j,v_j)\), with orthonormal STF basis \(E_I\), is
\[
J^{r}_a=(1,n^TE_In,-n_j,0),\quad
J^\mu_{aA}=(0,t_{aA}^TE_In,0,t_{aA}\cdot(n\times e_j)).
\tag{C12}
\]
These are derivatives of the actual source-level response. Fit raw redshift and distances jointly when division by uncertain \(r\) would distort the law. Apply angular masks, tangent-frame conversion, distance windows and nuisance operators before computing rank. With a covariance-support whitener \(W\), nuisance matrix \(N\), and anchor-coordinate map \(L\), use \(P^\perp_{WN}WJL\), retaining residuals in covariance null directions. No full-sphere orthogonality is presumed after selection.

For a declared observation law or tolerance set, form the joint inverse image
\[
\mathcal I_Y=\{X:\exists\eta,\nu,\epsilon;\ Y=R_\eta(X)+N\nu+\epsilon,\ (\eta,\nu,\epsilon)\in\mathcal A\}.
\tag{C13}
\]
Here \(X=(\sigma,\omega,A,\beta_{RM},\beta_{MO},\ldots)\) preserves the report's carrier; unreconstructed channels remain unavailable. A compatible CMB response can be intersected with this image using shared frame and covariance, rather than equating a CMB temperature tensor to \(\sigma\).

`20-report-1-.txt`, §23, PDF pp24–26, defines sample-by-functional \(x\), anchor gauge/margin \(Q\), directional support profiles \(F\), law-bound exceedance surfaces \(\Pi\), and structured depth paths \(G_F\). Apply the original \(\phi_j\) and normalization to each joint state from (C13). Preserve paired reference states. In the inspected current `typefree_functionals.py`, `support_utilization` is specifically \(u^T[\phi(X)-\phi(X_{ref})]/h_B(u)\), with positive denominator required. Taking its supremum over an explicitly supplied finite image yields the corresponding finite support profile; it does not certify a continuous supremum. A `FINITE_SET` carries no probability weights. \(\Pi_\phi\) therefore requires a named empirical, sampling, null or posterior law before exceedance is evaluated.

There are distinct F namespaces in the materials: the legacy `mio/formalism/filling_fraction.py` implements a certified diagnostic under a sign-clean ceiling and rejects material/volume-occupancy interpretations; the structured report retains directional support; the newer skill prose mentions explicit-measure occupancy. This construction uses the report/typefree support namespace and does not identify these quantities. `typefree_depth.py` transports signed paired features through `DepthRepresentation`, requiring one shared latent realization, frame endpoints and full cross-bin covariance for uncertainties. That is the applicable structured depth connection. A scalar legacy depth-gap is used only under its own definition. Deterministic images remain computable when a probability law is unavailable.

## R10 — Next executable checkpoint

The next integration is a source-level synthetic catalogue with known frame spin, clock scale, distance errors and shared source-slip nuisance. Generate it directly from (C12), recover its injected coefficients, and compare the shear closure across shrinking distance windows. Then add a declared finite-distance coefficient from the primary optical expansion and measure the induced bias. Real catalogue attribution requires population selection, an independent triad-spin calibration and the joint observation law. None of these steps requires an ODE or a Bianchi solver. The present unit ends with the explicit inverse, optical cancellation, exact projection checks and reusable joint-response contract delivered for independent review.



\clearpage

\begin{center}\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{/workspace/scratch/ef61c9590364/HTT_TEFF_V15_EXTENSION_20261026/prior_baseline/figures/figure_c_kinematics.pdf}\end{center}

**Analytical local-kinematics example.** In rate unit \(\Gamma\), \(h=2\Gamma\), \(S=\Gamma\,\mathrm{diag}(1,-1,0)\), \(\alpha=0\), \(v=(0,0,0.65\Gamma)\), and frame spin vanishes. The angular patterns and full-sphere ranks concern the stated local response, not an observed catalogue.

\clearpage

# Loop D — Bianchi geometry and the joint anisotropy image

**Internal theory note, 2026-10-26.** Owner: HTT internal theory campaign. Scope: homogeneous spatial initial data and conditional observability; no sky likelihood, evolution solver, native Bianchi transfer, or family identification. Source checkout snapshot supplied as \texttt{a55036ad09c5\allowbreak 3a9215dee328\allowbreak 2e425d37cfb9\allowbreak 5443} (the extracted `sources/repo` has no `.git`, so that identity is supplied, not independently verified here). Signature is \((-,+,+,+)\); \(c\) is explicit. Main finite calculation: `cas/loop_d.wl`, with standard-library exact-rational cross-check `cas/loop_d_check.py` and receipt `cas/loop_d_receipt.json`.

## R1–R3. Question, sources, conventions, and claim domain

The question is what a local anisotropy evaluation can restrict about Bianchi spaces when kinematics, spatial curvature, and initial-value constraints are retained together. The object is a three-dimensional, simply transitive spatial isometry algebra acting on a homogeneous slice, with a positive definite invariant metric and normal \(N^\mu\). The normal is geodesic and hypersurface orthogonal in the synchronous description. Normal-frame shear \(\sigma_{ij}\), expansion \(H>0\), spatial Ricci \({}^{3}R_{ij}\), energy density \(\varepsilon_N\), energy flux \(q_i\), and cosmological constant enter the compatibility calculation. In this note \(\varepsilon_N\) is energy per volume; \(q_i\) is also the energy-flux variable in an orthonormal frame divided by \(c\), so both have energy-density units. Set \(\kappa=8\pi G/c^4\), \(h=H/c\), and \(S_{ij}=\sigma_{ij}/c\); these last two and spatial commutator coefficients have inverse-length units. We take \(K_{ij}=-(h\delta_{ij}+S_{ij})\) for the slice's extrinsic curvature. The sign of \(q_i\) is chosen by \(T_{0i}=-q_i\) in the orthonormal \(e_0=N\) convention.

The primary textbook input is Ellis, Maartens and MacCallum, *Relativistic Cosmology*, §§2.7, 4.7, 6.3–6.5, 18.3, especially equations (18.13)–(18.21) and Tables 18.1–18.2, locally extracted at \texttt{text/ellis-r\allowbreak elativistic-\allowbreak cosmology.tx\allowbreak t}, PDF pp. 479–482 (printed pp. 463–466). Its Table 18.1 gives the canonical nonzero \((n_i,a_i)\); its Table 18.2 explicitly places flat FLRW in I and VII\(_0\), and open FLRW in V and VII\(_h\). The original classification context is Ellis and MacCallum (1969), [*A class of homogeneous cosmological models*](https://link.springer.com/article/10.1007/BF01645908), *Commun. Math. Phys.* **12**, 108–141, DOI 10.1007/BF01645908; the publisher's bibliographic record was checked on 2026-10-26. The observational distinction between a measured sky tensor and a physical response is made in Park, *From a CMB Sky Map to Physical Constraints* (2026-09-07), local text §§1.2, 5–7, and the later `text/20-report-1-.txt`, PDF pp. 3, 13–17 and 24. The retained R32-07-P5 algebra product, \texttt{sources/repo\allowbreak /docs/resear\allowbreak ch\_program/o\allowbreak bservational\allowbreak \_publication\allowbreak \_20261015/PU\allowbreak BLICATION\_AC\allowbreak CELERATION\_2\allowbreak 0261025/prod\allowbreak ucts/R32-07-\allowbreak P5-ALGEBRA/s\allowbreak cience/manus\allowbreak cript.md}, §§1–5, provides the narrower LRS V constraint and Bianchi I radiation-history example. This note extends the *spatial-geometry question* beyond that LRS chart; it does not reuse its LRS identity as a general Bianchi theorem.

The claims below concern a **finite algebraic instantaneous image**, not a posterior or a measured sky image. The Einstein constraints are imposed where stated. An arbitrary fluid can have normal-frame flux and anisotropic stress; the explicit same-matter matched example below uses orthogonal dust on one slice. Dynamical persistence, a photon history, and an observational response have additional inputs. The normal's vorticity is zero, which does not determine a tilted fluid's vorticity.

## R4–R5. Structure constants to spatial curvature

Choose an oriented orthonormal spatial triad \(e_i\), with \(\epsilon_{123}=+1\). Write

\[
 [e_i,e_j]=C^k{}_{ij}e_k,\qquad
 C^k{}_{ij}=\epsilon_{ij\ell}n^{\ell k}
                  +a_i\delta^k_j-a_j\delta^k_i,
 \quad n^{ij}=n^{ji},\qquad n^{ij}a_j=0.                 \tag{D1}
\]

The final equation is Jacobi. A rotation diagonalizes \(n\), and for class B its nonzero \(a\) may be chosen along axis 1; then \(n=\operatorname{diag}(0,n_2,n_3)\), \(a=(a,0,0)\). Class A has \(a=0\). The coefficients are physical inverse lengths in an orthonormal frame, not dimensionless Bianchi names. An orientation reversal changes some signed coefficients while preserving curvature invariants; the formulas here use the fixed orientation.

Here is a direct Levi-Civita construction, independent of a pretabulated Bianchi Ricci formula. Koszul's formula for the invariant spatial metric gives

\[
2\Gamma_{ijk}=C_{ijk}-C_{jki}+C_{kij},\qquad
\Gamma_{ijk}=\langle D_{e_i}e_j,e_k\rangle.              \tag{D2}
\]

With \(R(X,Y)Z=D_XD_YZ-D_YD_XZ-D_{[X,Y]}Z\), the coefficients, constant along each spatial invariant frame, give

\[
R^l{}_{mij}=\sum_p(\Gamma_{jmp}\Gamma_{ipl}
 -\Gamma_{imp}\Gamma_{jpl}-C^p{}_{ij}\Gamma_{pml}),
\qquad {}^3R_{jk}=\sum_iR^i{}_{jik}.                    \tag{D3}
\]

Substitution of (D1), *restricted by* \(n_1a=0\), yields

\[
{}^3R_{ii}=\tfrac12[n_i^2-(n_j-n_k)^2]-2a^2
 \quad(\{i,j,k\}=\{1,2,3\}),\quad
 {}^3R_{23}=a(n_2-n_3),\quad {}^3R_{12}={}^3R_{13}=0,             \tag{D4}
\]
\[
{}^3R=-\tfrac12\sum_i n_i^2+\sum_{i<j}n_i n_j-6a^2.          \tag{D5}
\]

The other off-diagonal entry is its symmetric partner. The unrestricted symbolic intermediate has an antisymmetric term proportional to \(an_1\); retaining it would be an algebraic false-positive geometry. In three dimensions the complete spatial Riemann tensor is algebraically determined by the Ricci tensor, so (D4) gives the entire intrinsic curvature at this slice, though not its derivatives or the embedding. Equations (D2)–(D3) exhibit the nontrivial transition from a group label to a tensor, and (D4) is the reusable finite evaluator.

Let \(u,v>0\), both inverse lengths. Actual substitutions give:

| Type / parameters \((n_1,n_2,n_3;a)\) | \({}^{3}R_{ij}\) in the chosen triad | \({}^{3}R\) |
|---|---|---|
| I: \((0,0,0;0)\) | \(0\) | \(0\) |
| II: \((u,0,0;0)\) | \(u^2\operatorname{diag}(1,-1,-1)/2\) | \(-u^2/2\) |
| IX, round: \((u,u,u;0)\) | \((u^2/2)I\) | \(3u^2/2\) |
| V: \((0,0,0;v)\) | \(-2v^2I\) | \(-6v^2\) |
| VII\(_0\), equal: \((0,u,u;0)\) | \(0\) | \(0\) |
| VII\(_0\), unequal: \((0,2u,u;0)\) | \((u^2/2)\operatorname{diag}(-1,3,-3)\) | \(-u^2/2\) |

The type II computation includes a sectional cross-check: since \({}^{3}R_{11}=u^2/2\) and \({}^{3}R=-u^2/2\), the three-dimensional identity \(R_{ijij}=R_{ii}+R_{jj}-R/2\) yields section curvatures \((+u^2/4,+u^2/4,-3u^2/4)\) for planes \((12,13,23)\). For IX, \(R_{ijij}=u^2/4>0\); for V, \(R_{ijij}=-v^2\). These signs independently check the scalar convention and the Bianchi V warped-slice curvature in the R32-P5 product, where \(v=A_0/X\). In physical units the corresponding curvature terms in time-rate equations are \(c^2{}^3R\) or \(c^2{}^3R_{ij}\).

The equal-\((n_2,n_3)\) VII\(_0\) row has the intrinsic Euclidean metric: the flat spatial Riemann tensor vanishes although its chosen simply transitive generators have a non-Abelian algebra. A local Euclidean geometry also admits the translational Bianchi I action. Thus I and flat VII\(_0\) are distinct *presentations of the same local spatial geometry*, not a counterexample showing two different intrinsic curvatures at that point. The symmetry subgroup, global identifications, and its relation to extrinsic data must be specified if a presentation is to have physical significance. An isotropically expanding flat FLRW realization has both presentations, as Ellis et al. Table 18.2 notes. The statement does not equate every anisotropically embedded I and VII\(_0\) spacetime.

## R5–R6. Joint Gauss–Codazzi image and a sharper matched pair

For homogeneous normal data the Hamiltonian constraint is

\[
3h^2=\kappa\varepsilon_N+\Lambda
       +\tfrac12 S_{ij}S_{ij}-\tfrac12{}^3R.             \tag{D6}
\]

The sign follows directly from \({}^3R+K^2-K_{ij}K^{ij}=2\kappa\varepsilon_N+2\Lambda\). The momentum constraint in the Ellis et al. equation (18.21) normalization reads

\[
\kappa q_i=3a S_{1i}+\sum_{jk}\epsilon_{ijk}n_j S_{jk}.
                                                               \tag{D7}
\]

To avoid a convention ambiguity, \(q_i\) here is chosen so that the right side agrees with the orthonormal signed LRS V branch: for \(a=v\) on axis 1, \(S=\operatorname{diag}(2s/c,-s/c,-s/c)\), equation (D7) gives \(\kappa q_1=6vs/c\), exactly the positive normal-frame momentum relation used in R32-P5 after its axes are permuted. Equation (D7) otherwise inherits the orientation and shear convention in (D1). This is a three-component constraint, not a shear-free rule. In class A with diagonal \(n,S\), \(q=0\) even when \(S\ne0\). In the LRS V tilted branch, \(q_1=0\) forces \(s=0\) for \(v>0\); transferring that conclusion to I, II or IX would discard the different structure constants.

The actual evaluator's algebraic compatibility set can therefore be written

\[
\begin{aligned}
\mathcal J_{\mathcal B}(h,S,\varepsilon_N,q,\Lambda)
=\{(n,a):\;& n=n^T,\ na=0,\\
&(n,a)\text{ lies in canonical sign class }\mathcal B,\\
&(D4),(D6),(D7)\text{ hold}\}.
\end{aligned}\tag{D8}
\]

One may intersect (D8) with measured or bounded *same-frame* curvature tensors, not with an uncalibrated sky quadrupole. The sign classes in Ellis et al. Table 18.1 supply finite canonical cells; the variables inside each cell are continuous. A quotient by rotations and actual local isometries prevents duplicate presentation counts. A scalar \({}^{3}R\) alone leaves greater degeneracy than the full \({}^{3}R_{ij}\).

An exact matched example makes this point beyond I versus II. Put the same normal-frame \(h>0\), diagonal \(S=\operatorname{diag}(s_1,s_2,s_3)\) with \(\sum s_i=0\), orthogonal dust \(q_i=0\), \(\Lambda\ge0\), and \(\varepsilon_N>0\) in two data sets. Take II data \(n=(u,0,0)\) and VII\(_0\) data \(n=(0,2u,u)\), both \(a=0\). Equation (D7) vanishes in each, and their scalar curvatures are identically \(-u^2/2\). Equation (D6) thus fixes **exactly the same** density

\[
\kappa\varepsilon_N=3h^2-\Lambda-\tfrac12\sum_i s_i^2-u^2/4,
                                                              \tag{D9}
\]

positive whenever the right side is positive (for example \(\Lambda=0\), \(h=2u\), \((s_1,s_2,s_3)=(u/10,-u/20,-u/20)\)). Yet the two spatial Ricci tensors are the distinct matrices in the table; their spectra cannot be made equal by a triad rotation. Consequently a common local normal-frame expansion/shear tensor, normal dust density, flux, \(\Lambda\), and scalar curvature do **not** uniquely recover even the local intrinsic curvature tensor. The STF Ricci difference is an immediate discriminator if a spatial tidal-curvature datum can be inferred independently. Einstein initial data with these smooth invariant spatial metric and extrinsic data satisfy both constraints; normal dust data are regular for the positive density chosen. Invoking their possible time developments requires the dust Cauchy equations, whereas the displayed statement needs only the initial slice.

The inverse direction is also useful. An independent full \({}^{3}R_{ij}\) measurement would exclude one member of this pair, but in flat constant-curvature sectors it still does not select a unique simply transitive presentation (I/VII\(_0\), likewise open V/VII\(_h\) in the FLRW limit). A Weyl electric/magnetic tensor or its time derivatives, a spatial-curvature-sensitive distance/parallel-transport response at more than one location, and a declared matter model could provide additional independent information. These are *candidate observables*, not results of evaluating the CMB sky. Weyl propagation and shear evolution also require anisotropic stress and initial conditions: Ellis et al. §6.4, equations (6.28), (6.33)–(6.36), make their coupling explicit. The spatial Ricci is an intrinsic slice tensor, whereas the Weyl tensor encodes four-dimensional free curvature; substituting one for the other without Gauss relations and extrinsic data would change the claim.

## R6–R8. Checks and verdict

The symbolic program computes (D2)–(D4), then substitutes six rows. Its first attempt used the protected Wolfram symbol `C`, generating an unresolved giant expression; changing it to `strC` is an implementation correction, not a physical counterexample. The successful evaluator output contains the six matrices and the class-B constrained matrix. A separate standard-library `Fraction` implementation uses integer permutations and performs exact-rational checks for \(u=2/7,v=3/11\). It prints six expected Ricci matrices and passes. Its independent finite enumeration is a cross-check of the finite identities at that substitution; the analytic derivation (D2)–(D4) supplies their symbolic scope. Positive sectional IX and negative constant sectional V provide a sign and unit check. The vanishing of the antisymmetric piece only on \(an_1=0\) checks the Jacobi dependence. No four-axis CAS admission or xAct validation is claimed by this targeted verification.

The proved result is an instantaneous, geometry-compatible image and a concrete degeneracy of kinematic-plus-scalar-curvature data. It is not framed as a new universal no-go theorem: the matched pair fixes the quantifiers it actually addresses and the curvature-tensor measurement that resolves it. In particular, an ordinary CMB quadrupole \(Q^{T}_{ij}\), a local optical shear tensor, and a spatial \({}^{3}R_{ij}\) are three distinct objects. The first depends on a photon history, source terms, observer, foreground/mask and transfer model; R32-P5 even supplies different Bianchi I shear histories with an identical full final collisionless temperature pattern. The second can arise as a local coefficient in a calibrated distance law; the third additionally probes spatial geometry. None follows numerically from the other in (D8) without a declared response. The P5 result and the present pair answer separate inverse questions, and neither licenses a Bianchi family identification from sky morphology alone.

For the project's \((x,Q,\Pi,F,G_F)\) vocabulary, (D8) supplies a *deterministic geometry carrier* and potential constraints on a same-frame \(x\). A normalized anchor score \(Q\) requires a named premise anchor and denominator; do not conflate it with \(Q^{T}_{ij}\) or a raw tensor norm. The current R32-05-P6 optical manuscript defines an occupancy \(F_\nu(B)=\nu(B\cap D)/\nu(D)\) under a declared finite support measure, whereas other project text uses directional-support language. Both need their own domain, measure, ceiling and mapping; this note chooses neither policy and computes no \(F\). A statistical \(\Pi\) requires a joint law; a depth functional \(G_F\) requires specified windows and dependence. Thus there is no posterior, occupancy, ceiling exceedance or empirical constraint in this calculation.

## R9–R10. Finite implementation contract and resume point

The reusable pre-solver evaluator accepts a real symmetric \(3\times3\) \(n\) with inverse-length units, real \(a\in\mathbb R^3\) with inverse-length units, oriented orthonormal frame, \((h,S,\varepsilon_N,q,\Lambda)\) in the units above, and an explicit tolerance only for noisy numeric data. It first checks \(\|n a\|=0\) algebraically or against a declared input uncertainty, constructs \(C\), \(\Gamma\), \({}^{3}R_{ij}\), and then checks (D6),(D7) jointly. It returns the curvature scalar, STF Ricci, Hamiltonian and three momentum residuals with units \(L^{-2}\), plus algebraic class and geometric equivalence flags. Exact input uses exact arithmetic; a zero curvature tensor in a non-Abelian presentation carries the flat equivalence flag. It does not convert residuals into a likelihood or infer a family. The six table rows and the II/VII\(_0\) matched pair are reference values; \(a\to0\) and \(n\to0\) are boundary limits, not automatic class relabelings of a nonzero datum.

The next independent scientific step is to specify one curvature-sensitive observational response and its uncertainty, then intersect its tensor image with (D8) while retaining source/observer history and equivalence classes. A practical candidate is a separately calibrated low-redshift distance/transport tensor or Weyl-sensitive response linked through explicit Gauss and propagation equations. Check the response on the matched II/VII\(_0\) pair first: it should distinguish their STF spatial Ricci when its assumptions actually expose that tensor. For flat I/VII\(_0\), record presentation equivalence rather than scoring a fictitious distinction. This is an executable mathematical target and does not invoke the absent native low-ell solver.






\clearpage

# LOOP E — What a direction-dependent Hubble measurement measures

**Owner:** HTT internal theory loop E. **Date:** 2026-10-26. **Scope:** local covariant distance jets, a vacuum Bianchi I example, and statistical transport. Baseline commit: \texttt{a55036ad09c5\allowbreak 3a9215dee328\allowbreak 2e425d37cfb9\allowbreak 5443}. No native evolution solver is used.



## R1 — Research question and useful output

The legacy programme asks for a redshift- and direction-dependent Hubble factor and its relation to the local geometric state. A map of fitted Hubble ratios answers this question after its distance definition, source congruence and redshift interval are fixed. This loop constructs the map from geometric derivatives to observable distance coefficients and identifies a curvature–history combination that an additional observable can resolve.

The output is a finite algebraic interface. The first distance coefficient measures directional expansion, the next its derivative along the ray, and the cubic term combines another derivative with Ricci focusing. Distance coefficients and their joint region enter a geometric image without constructing a new Einstein–Boltzmann history.

## R2 — Literature and source reuse

Ellis, Maartens and MacCallum, *Relativistic Cosmology*, supplied PDF pp179–184 (printed pp163–168), develops null congruences, focusing and reciprocity. PDF pp207–208 (printed pp191–192) relates the leading optical expansion to observer kinematics. Heinesen, “Multipole decomposition of the general luminosity distance ‘Hubble law’ — a new framework for observational cosmology,” JCAP 05 (2021) 008, [arXiv:2010.06534v2](https://arxiv.org/abs/2010.06534), supplies the general cosmographic setting; equations (11), (14), (16), (19), (28) and (29) were checked in the primary text. General anisotropic cosmography is established prior work. The construction here connects it to the HTT state and the retained residual-compatible image.

The legacy affine radial recipe and current R32 moment-image results are reused. Loop C supplies the same-congruence optical interpretation; Loop D supplies a geometric compatibility body. Loop C uses inverse-time rates, whereas this loop uses inverse-length rates until multiplication by \(c\).

## R3 — Geometric convention and observables

Use signature \((-+++)\), a unit timelike field \(u\), and outward sky direction \(n\), with \(u^2=-1\), \(n^2=1\), \(u\cdot n=0\). The past-directed null tangent and redshift are
\[
K=E(-u+n),\qquad E=u\cdot K,\qquad E_O=1,\qquad z=E-1.
\tag{E1}
\]
Affine parameter \(\lambda\), increasing into the past, has length units. Put \(A=u\cdot\nabla u\) and
\[
h(\lambda)=\frac{\Theta}{3}+\sigma_{ab}n^an^b-A_an^a.
\tag{E2}
\]
Contracting the velocity gradient with \(K^aK^b\) gives
\[
\frac{dE}{d\lambda}=E^2h.
\tag{E3}
\]
Antisymmetric vorticity drops out. This tensor contraction was evaluated with xAct/xTensor. It identifies \(H_{\rm dir}(0,n)=ch_0(n)\), where \(h_0=h(0)\).

Assume geometric optics, a regular observer vertex, no caustic in the expansion neighbourhood, and photon-conserving reciprocity. Then
\[
D_A''=-\left(\frac12R_{ab}K^aK^b+|\widehat\sigma|^2\right)D_A,
\quad D_A(0)=0,\quad D_A'(0)=1,\qquad D_L=(1+z)^2D_A.
\tag{E4}
\]
At a regular vertex the optical shear is \(O(\lambda)\), so its square enters beyond the cubic distance term. Matter-congruence shear \(\sigma\) and null optical shear \(\widehat\sigma\) are different tensors.

## R4 — Distance-jet calculation

Write \(h_1=h'(0)\), \(h_2=h''(0)\), and \(R_0=(R_{ab}K^aK^b)_O\). The derivatives include ray-direction and energy evolution. Differentiating (E3) gives
\[
E=1+h_0\lambda+\left(h_0^2+\frac{h_1}{2}\right)\lambda^2
+\left(h_0^3+h_0h_1+\frac{h_2}{6}\right)\lambda^3+O(\lambda^4).
\tag{E5}
\]
Focusing gives \(D_A=\lambda-R_0\lambda^3/12+O(\lambda^4)\). For \(h_0\ne0\), series inversion yields
\[
D_L=d_1z+d_2z^2+d_3z^3+O(z^4),
\tag{E6}
\]
\[
d_1=\frac1{h_0},\qquad d_2=\frac1{h_0}-\frac{h_1}{2h_0^3},\qquad
d_3=\frac{h_1^2}{2h_0^5}-\frac{h_2}{6h_0^4}-\frac{R_0}{12h_0^3}.
\tag{E7}
\]
Wolfram series inversion returns zero residual against (E7). In FLRW, \(h_1=(1+q)h_0^2\), \(h_2=(j+4q+3)h_0^3\), \(R_0=2h_0^2(1+q-\Omega_k)\). Therefore
\[
d_3=\frac{-1+q+3q^2-j+\Omega_k}{6h_0}.
\tag{E8}
\]
This limit was also checked symbolically.

## R5 — Two Hubble estimands and a curvature–history combination

Define
\[
H_{\rm ratio}=\frac{cz}{D_L},\qquad
H_{\rm diff}=\frac{c}{\partial_z[D_L/(1+z)]}.
\tag{E9}
\]
With \(q_{\rm eff}=h_1/h_0^2-1\),
\[
H_{\rm ratio}=ch_0\left[1-\frac{1-q_{\rm eff}}2z+O(z^2)\right],
\qquad H_{\rm diff}=ch_0[1+(1+q_{\rm eff})z+O(z^2)].
\tag{E10}
\]
These are different finite-redshift observables. Even in FLRW, the transverse comoving-distance definition of \(H_{\rm diff}\) equals \(H(z)\) only in the spatially flat case. A directional derivative fit measures a specified optical coefficient.

**Finite-jet equivalence lemma.** The three coefficients (E7), at \(h_0\ne0\), determine \(h_0,h_1\), and
\[
\mathcal J=h_2+\frac{h_0R_0}{2}
=\frac{3h_1^2}{h_0}-6h_0^4d_3.
\tag{E11}
\]
They are invariant under
\[
R_0\mapsto R_0+\delta,\qquad h_2\mapsto h_2-\frac{h_0\delta}{2}.
\tag{E12}
\]
**Proof.** Recover \(h_0,h_1\) from the first two coefficients. Multiply the third by \(6h_0^4\) to obtain (E11); substitution proves (E12). A curvature or derivative measurement thus adds precisely the missing direction in this local jet space. A fixed matter model can restrict the space further.

A physical example is a smooth FLRW family with fixed \(H_0,q_0,j-\Omega_k\), while \(j\) and \(\Omega_k\) vary together. Smooth scale-factor jets with these values can be chosen locally; Einstein's equations define the corresponding homogeneous density and pressure when no fixed equation of state is imposed. This gives local realizability under that freedom.

## R6 — A relativistic anisotropic example without an evolution solver

For diagonal Bianchi I,
\[
ds^2=-c^2dt^2+\sum_i a_i(t)^2(dx^i)^2,\qquad H_i=\dot a_i/a_i.
\tag{E13}
\]
In an orthonormal spatial frame let \(H_n=\sum_iH_in_i^2\). Conserved spatial photon momenta give
\[
\frac{dt}{d\lambda}=-\frac{E}{c},\qquad
\frac{dn_i}{d\lambda}=\frac{E}{c}n_i(H_i-H_n).
\tag{E14}
\]
Hence
\[
h_0=\frac{H_n}{c},\qquad
h_1=\frac1{c^2}\left[-\sum_i\dot H_i n_i^2
+2\left(\sum_iH_i^2n_i^2-H_n^2\right)\right]_O.
\tag{E15}
\]
Twice the directional variance of expansion eigenvalues enters because the photon direction drifts. Holding \(n\) fixed during differentiation would omit this contribution.

Choose the vacuum Kasner solution \(a_i=(t/t_*)^{p_i}\), \(p=(-1/3,2/3,2/3)\). Direct Christoffel-to-Ricci calculation gives, with \(t_*=1\),
\[
R_{tt}=\frac{\sum_i p_i-\sum_i p_i^2}{t^2},\qquad
R_{ii}=\frac{p_i(\sum_jp_j-1)t^{2p_i-2}}{c^2}.
\tag{E16}
\]
Both vanish for this triple. For \(x=n_1^2\),
\[
tH_{\rm dir}=\frac23-x,\qquad
q_{\rm eff}(x)=-1+\frac{2/3+x-2x^2}{(2/3-x)^2}
=\frac{2+3(7-9x)x}{(2-3x)^2}.
\tag{E17}
\]
At \(x=0\), \(q_{\rm eff}=1/2\); at \(x=1/2\), it is \(23\). Volume expansion is \(c\Theta=1/t\), while directional expansion can vanish or change sign. Large \(q_{\rm eff}\) near \(x=2/3\) comes from a small directional denominator; the spacetime remains Ricci-flat.

At \(h_0=0\), the affine expansion survives but redshift ceases to be a valid first-order local coordinate. The figure restricts the redshift-series example to \(x\le0.55\). A survey crossing the zero should fit the distance/affine response directly.

## R7 — Finite-redshift remainder and statistical application

Suppose a declared local domain supplies
\[
|D_L-d_1z-d_2z^2|\le Mz^3,\qquad z>0.
\tag{E18}
\]
If \(L=d_1+d_2z-Mz^2>0\), exact reciprocal monotonicity gives
\[
\frac{c}{d_1+d_2z+Mz^2}\le H_{\rm ratio}
\le\frac{c}{d_1+d_2z-Mz^2}.
\tag{E19}
\]
This is conditional on a justified \(M\). Window variation and an independently bounded derivative class can assess finite-distance sensitivity; a polynomial fit alone does not certify \(M\).

Fit distance coefficients with scalar/STF angular functions and redshift powers, then push their joint region through (E7) and (E11). Shared calibration, peculiar velocities, masks and repeated objects enter one covariance/nuisance model. Public total covariance is used once. For SN data, fit magnitude or flux through its distance response rather than assuming transformed distances have homoscedastic Gaussian errors.

For a declared linear response \(z_{\rm obs}=A\theta+e\), reuse the repaired repository image
\[
E_z=\{e\in E:(I-AA^+)(z_{\rm obs}-e)=0\},\qquad
\Theta_z=\{A^+(z_{\rm obs}-e)+k:e\in E_z,\ k\in\ker A\}.
\tag{E20}
\]
Nonlinear inversion requires its nonlinear image or a bounded linearization remainder. A linear target \(J\theta\) is point identified only if \(\ker A\subseteq\ker J\). Useful combinations can therefore proceed while others await additional input.

## R8 — Physical meaning of statistical robustness and information

The supplied Wager text, *Causal Inference: A Statistical Learning Approach*, Chapter 3, PDF pp30–35, explains augmented weighting and product-error control. The same mechanism applies to a missing-data estimating equation under explicit missing-at-random assumptions; no intervention is inferred from a sky direction.

Let \(S\) indicate selection, \(X\) parent covariates and \(g_\theta(X,Y)\) a population physical moment. Assume \(E[g_\theta\mid X,S=1]=E[g_\theta\mid X]\) and \(\pi(X)=P(S=1\mid X)>0\). For working functions \(\widetilde m,\widetilde\pi\), assume \(\widetilde\pi>0\) on the parent support and integrability of the terms below, and set
\[
\psi_\theta=\widetilde m_\theta(X)
+\frac{S}{\widetilde\pi(X)}[g_\theta-\widetilde m_\theta(X)].
\tag{E21}
\]
With \(m_\theta=E[g_\theta\mid X]\), conditional expectation gives
\[
E[\psi_\theta]-E[g_\theta]
=E\!\left[\left(1-\frac{\pi}{\widetilde\pi}\right)
(\widetilde m_\theta-m_\theta)\right].
\tag{E22}
\]
This proves the double-robust mean identity and exposes its product error. For Hubble measurements it couples a directional-residual regression to selection modelling. Use group/calibration-blocked cross-fitting for shared errors. Without parent support or a justified selection law, a population moment remains conditional; an explicitly selected-cohort estimand can still be studied under its own law.

Polyanskiy and Wu, *Information Theory*, §2.6 and §3.2, supplied PDF pp61–62 and pp78–79, supplies the sufficiency framework. For a regular dominated family with score \(s(Y)\), a parameter-independent compression \(T(Y)\) has score \(E[s(Y)\mid T]\). Thus
\[
I_Y-I_T=E[\operatorname{Cov}(s(Y)\mid T)]\succeq0.
\tag{E23}
\]
Differentiation under the marginal integral and total covariance prove the identity. Invertible tensor coordinates preserve information, while a scalar amplitude can discard orientation or signed combinations that separate shear, boost and calibration. The identity does not establish sufficiency for an arbitrary chosen summary.

## R9 — Tensorized carrier and flexible acceptance

The carrier \(x\) holds jointly framed geometric variables or identifiable combinations, with a shared epoch and explicit units. Push the joint confidence/feasibility region through the declared maps.

Keep three \(F\) namespaces distinct: current typefree directional support utilization \(F_{\rm sup}\); legacy certified diagnostic \(F_{\rm cert}=x_C/U\); measure-defined occupancy \(F_\nu\). The legacy code explicitly rejects a material-volume interpretation. \(Q\) is the gauge of a specified anchor body, \(\Pi\) an exceedance object after supplying a source law, and \(G_F\) a depth/transport/coherence construction with its actual joint couplings. A geometric image can be completed before a calibrated exceedance probability exists.

Attach acceptance to each delivered observable or theorem. Equations (E11), (E19) and (E20) have useful, distinct acceptance conditions. They do not overwrite the original external-history requirement. This makes theorem and optical-coefficient progress possible while preserving the external history task.

## R10 — Verification and next experiment

Stored Wolfram checks cover series inversion, the full Bianchi I Ricci tensor, vacuum Kasner specialization, cubic-jet invariance and the FLRW limit. All residuals vanish. An initial syntax failure is retained separately from the repaired successful receipt. The xAct check establishes the null-gradient contraction, not a full cosmographic likelihood.

Next fit the first two optical coefficients jointly in fixed redshift windows, using one common nuisance/covariance model and explicit remainder sensitivity. Report \(ch_0(n)\), \(h_1(n)\), and the positive-denominator domain of ratios. Extend the fit to a supported cubic coefficient \(d_3\) before reporting \(\mathcal J(n)\). Compare radial shear with Loop C's transverse E2 response. The Kasner example and Loop D bodies then supply concrete geometric interpretations.



\clearpage

\begin{center}\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{/workspace/scratch/ef61c9590364/HTT_TEFF_V15_EXTENSION_20261026/prior_baseline/figures/figure_de_geometry.pdf}\end{center}

**Analytical geometry and optical coefficients.** The II/VII\(_0\) pair shares scalar curvature but has different spatial Ricci spectra. Vacuum Kasner gives \(tH_{\rm dir}=2/3-x\), with \(x=n_1^2\). The final panel compares first-order Hubble estimands at \(q_{\rm eff}=1/2\); those lines are \(O(z)\) truncations, not exact finite-redshift solutions or observations.

\clearpage

# Part II — Angular calculus, calibrated responses and uncertainty

The four constructions below adopt Papers I and II v15. Detailed source inventories and the separate novelty assessment accompany this report.

\clearpage

# Paper I v15 reuse, replacement map, and entropy-controlled shear response

Owner: `/root/kinematics_loop_20261026`. Date: 2026-10-26. Source: \texttt{ANGULAR\_CALC\allowbreak ULUS\_PAPER\_I\allowbreak \_v15\_ACK\_CLE\allowbreak AN\_OVERLEAF.\allowbreak zip}, SHA-256 \texttt{c856939999ea\allowbreak 202a5d676059\allowbreak 907bfcef7274\allowbreak 027299a2664f\allowbreak d55b86eecd69\allowbreak faad}, as recorded in \texttt{sources/pape\allowbreak r\_I/ARCHIVE\_\allowbreak IDENTITY.jso\allowbreak n}. All 944 lines of the main TeX, ten section files and four appendices were read; bibliography entries relevant to entropy geometry, radiation moments, observer response and massive moments were inspected. This replaces the legacy Teff theoretical reference for this extension. No source, publication branch or dynamical solver was changed.

## R1. Question and achieved result

Which v15 statements can replace the earlier effective-temperature machinery, and can their entropy budget provide a useful conditioning certificate for the independently derived radiation-to-shear response?

The answer has three parts: a source-exact inventory; a replacement map preserving the prior A/B/C physical observables; and a proved **global entropy-controlled shear-response lemma**. In physical brightness notation, its main result is
\[
\boxed{\|\mathcal L_I-(8\rho/15)\mathrm{Id}\|_{\rm op}
\le\rho\sqrt{8\delta/3},\qquad
\delta:=\frac{k_B I_{{\rm ang},0}}{S_{\rm iso}}
=1-\langle w^{3/4}\rangle,\quad w=\frac{4\pi I}{\rho}.}
\tag{P1}
\]
It yields an explicit inverse certificate when \(\delta<8/75\). The scalar divergence inequality is established mathematics; the new project bridge is its normalization to v15 angular entropy, the mass-matched operator centering, and the resulting radiation/optical shear consistency contract. It does not assert a new universal positivity criterion or an observational result.

The source inventory covers all 15 TeX files, including the four appendices. Exact theorem labels and source hashes are retained in the accompanying inventory.

## R3. Legacy replacement map and conventions

| Earlier use | v15 replacement | Preserved physical distinction |
|---|---|---|
| A single Teff treated as a general spectrum | Energy-only ray section `eq:teff-family`, with \(I_{spec}\) retained separately | Nonthermal spectra have a bolometric calibration while energy-dependent rates still need extra spectral information. |
| Finite temperature multipoles treated as the entropy fit | Positive natural field \(\beta_b\in V_L\), theorem `thm:representative` | \(T=1/\beta\), \(I\propto\beta^{-4}\) and their harmonic truncations differ. |
| One scalar information-loss measure | Exact \((I_{spec},I_{ang,L})\) budget with stated domains | Neither refinement universally substitutes for the other. |
| Mechanical inference from a temperature Q alone | Kernel-calibrated brightness moments; v15 pressure example; prior Loop A operator | Radiation stress \(\pi\), optical shear \(\sigma\), temperature STF2 and diagnostic Q remain different quantities. |
| A frame-independent finite cutoff | State–observer–kernel tuple plus boost leakage and positive-patch comparison | Prior Loop B exact phase-space transform remains valid; inward propagation \(e=-n\) changes odd-mode signs. |
| Massive direction-only energy used for flux/stress | Physical \(v^\ell\) weights and positive shell factorization | Massive response needs radial/speed information. Poisson resolution parameter is not physical time. |
| Teff invoked as a dynamical closure/solver | Static reconstruction and declared response calculations | Prior Loop A transport residual and Loop C optical congruence are still independent physical inputs. |

Paper I uses \(U^2=-c^2\); prior A/B/C use unit \(u\), so set \(U=cu\). Both use \((-+++)\). Its angular \(e\) is photon propagation; the observed outward direction in B/C is \(n=-e\). Even radiation moments and the norm bounds below are unchanged. The present user direction selects v15 as the reference, replacing an earlier blanket “Teff legacy” research exclusion only within this scoped theoretical extension. It grants no source/publication/solver changes.

## R4. Candidate bridge and physical units

Let \(I(e)\ge0\) be physical bolometric energy density per solid angle, in J m\(^{-3}\) sr\(^{-1}\), with \(0<\rho=\int I\,d\Omega<\infty\). In Paper I notation \(I=E_*\rho_f\); for two equally populated photon helicities it agrees with Loop A's brightness normalization. Write \(I_0=\rho/(4\pi)\), \(w=I/I_0\), and \(\langle\cdot\rangle=(4\pi)^{-1}\int\cdot,d\Omega\).

The massless contracted entropy has the physical-coordinate form
\[
F^{phys}_\xi(I)=-C_\xi I^{3/4},\qquad
C_\xi=4a_\xi\mathcal C_*(3a_\xi\mathcal C_*E_*)^{-3/4}.
\tag{P2}
\]
This is merely `eq:rho-beta-chain` with \(I=E_*\rho_f\). Its units ensure \(k_B\int F^{phys}\) is entropy density. The isotropic entropy density is \(S_{iso}=k_BC_\xi4\pi I_0^{3/4}\). Because \(\int(I-I_0)=0\), the Bregman tangent term cancels and gives the exact \(\delta\) in (P1). For photons \(S_{iso}=4\rho/(3T_{iso})\).

This is the **angular** information of the energy-matched lift. The underlying \(f\) need not be ray thermal. Any spectral entropy gap is separate. A number-constrained thermochemical section changes the entropy function and must use Paper II's corresponding construction instead of importing (P2).

## R5. Proof of the new bridge

### Scalar divergence step, independently specialized

Define \(\varphi(t)=1-t^{3/4}+3(t-1)/4\), \(D(t)=(7+5t)/12\), and
\(G(t)=D(t)\varphi(t)-3(t-1)^2/32\). Direct differentiation gives
\[
G(1)=G'(1)=G''(1)=0,\qquad
G'''(t)=\frac{35}{256}(t-1)t^{-9/4}.
\tag{P3}
\]
For \(t<1\), integrating this negative third derivative backward from one makes \(G''\ge0\), then \(G'\le0\), then \(G\ge0\). For \(t>1\), all successive forward integrations are nonnegative. Thus
\[
\varphi(t)\ge\frac{3}{32}\frac{(t-1)^2}{D(t)}.
\]
Since \(\langle D(w)\rangle=1\), weighted Cauchy–Schwarz yields
\[
\delta=\langle\varphi(w)\rangle
\ge\frac3{32}\langle|w-1|\rangle^2.
\tag{P4}
\]
The continuous endpoint at \(t=0\) allows zero brightness; positive approximations handle that endpoint. This is the \(\alpha=3/4\) specialization of Gilardoni, [arXiv:cs/0603097](https://ar5iv.labs.arxiv.org/html/cs/0603097), Theorem 3 and Corollaries 4/6. The primary proof was retrieved on 2026-10-26 and the derivative criterion checked directly here. Its constant is sharp as a scalar probability inequality: equal-area two-level contrasts \(w=1\pm\varepsilon\) give \(\delta/\langle|w-1|\rangle^2\to3/32\).

### Centered shear-response step

Prior Loop A established the self-adjoint STF2 operator
\[
\langle S,\mathcal L_I T\rangle
=\int I\,[2(Se)\cdot(Te)-(e^TSe)(e^TTe)],d\Omega
=\int I\langle S,B_eT\rangle,d\Omega,
\tag{P5}
\]
with \(0\le B_e\le\mathrm{Id}\). This is a pointwise finite-tensor result, independent of thermality. Its isotropic average is \(\mathcal L_{I_0}=8\rho\mathrm{Id}/15\). Total-energy matching now supplies a stronger error estimate than an uncentered L1 bound:
\[
\mathcal L_I-\mathcal L_{I_0}
=\int(I-I_0)(B_e-\mathrm{Id}/2)\,d\Omega,
\]
\[
\|\mathcal L_I-\mathcal L_{I_0}\|_{op}
\le\tfrac12\int|I-I_0|\,d\Omega
=\tfrac\rho2\langle|w-1|\rangle.
\tag{P6}
\]
Combining (P4) and (P6) proves (P1). No compact amplitude ceiling on \(I\) is used. Set \(\eta=\sqrt{8\delta/3}\). The resulting finite-dimensional spectral bounds are
\[
\rho(8/15-\eta)\le\lambda_{min}(\mathcal L_I),\qquad
\lambda_{max}(\mathcal L_I)\le\rho\min(1,8/15+\eta).
\tag{P7}
\]
For \(\delta<8/75\), \(\eta<8/15\), so (P7) certifies invertibility and gives the corresponding condition-number bound by dividing its two sides. This threshold is sufficient, not necessary.

If \(\mathcal L_I\sigma=-R\), let \(\sigma_0=-15\widehat R/(8\rho)\) and \(\|R-\widehat R\|\le\varepsilon_R\). Subtraction gives the finite inverse estimate
\[
\boxed{\|\sigma-\sigma_0\|
\le\frac{\varepsilon_R/\rho+\eta\|\sigma_0\|}{8/15-\eta}.}
\tag{P8}
\]
Here \(\sigma\) has inverse-length units and \(R\) has energy density per length, as in Loop A. The operator proof is kinematic; using its transport equation retains Loop A's geodesic, irrotational, collisionless branch and its differentiability/integration conditions.

## R6. Sharpness, proof inspection and limiting cases

The scalar constant in (P4) is sharp. Centering by \(\mathrm{Id}/2\) is optimal given only the common scalar mass and pointwise operator range \([0,1]\): for a normalized off-diagonal STF test matrix, \(\langle S,B_eS\rangle\) attains both zero and one at suitable directions. This does **not** prove that their combined entropy-to-operator constant is sharp for brightness compared with the uniform sky. The half-area scalar extremizers need not optimize the tensor operator.

The uniaxial family already present in v15 makes the conservatism quantitative. For \(w=1+aP_2\),
\[
\langle|w-1|\rangle=\frac{2|a|}{3\sqrt3},\quad
\delta=\frac{3a^2}{160}+O(a^3),\quad
\|\mathcal L_I-\mathcal L_{I_0}\|/\rho=\frac{2|a|}{21}.
\]
The entropy bound behaves as \(|a|/\sqrt{20}\); its leading ratio to the true operator error is \(21/(2\sqrt{20})\simeq2.348\). At \(a=1.5\), the true normalized minimum eigenvalue is 0.390476 while (P7) gives 0.197485. This is useful but conservative.

A general small STF pressure perturbation gives another bridge. Put \(p=\pi/\rho\), and decompose \(w-1=(15/2)p:ee+r\), with \(r\) orthogonal to scalar and quadrupole harmonics. For uniformly small contrasts,
\[
\delta=\frac{45}{64}p:p+\frac3{32}\langle r^2\rangle
+O(\|w-1\|_\infty^3).
\tag{P9}
\]
The fixed-pressure minimal cost therefore starts at \(45\|\pi/\rho\|^2/64\); the rank-two energy-matched representative attains it to quadratic order. This generalizes v15's specific axisymmetric coefficient but uses its existing projection theorem and Fisher metric. It is a useful tensor form rather than a separate priority claim.

The source proof inspection checked Appendix A's integrable massless BE edge and \(b^{-3}\) angular barrier, Appendix B's FD interior perturbations, Appendix C's exact two-moment compensation and tail scaling, and Appendix D's second-argument Hessian and score cancellation. No concrete mathematical failure was found in these inspected steps. This is a bounded verification statement, not a certification of every possible extension. In particular, the observer proposition requires its raw projection to remain positive, and the tail example concerns \(p>4\), not the energy-fixed bolometric response (P5).

## R7. Executed finite checks

`cas/paper_i_check.wl` was run with the connected Wolfram Language evaluator. It returned `{0,{0,0,0},0,0}` for the derivative identity (P3), its three matching values, the coefficient \(45/64\), and the threshold arithmetic. The receipt is \texttt{cas/paper\_i\_\allowbreak check\_wolfra\allowbreak m\_receipt.js\allowbreak on}.

`python cas/paper_i_check.py` performed SciPy quadrature of ten exact quadrupolar states, checked (P4)–(P7), and approached the coefficient \(45/64\) with small amplitudes. It also integrated the positive even family \(w\propto e^{k\mu^2}\) in an orthonormal five-component STF basis. At \(k=8\), \(\delta=0.294552\) and the actual minimum response eigenvalue is \(0.128233\rho>0\), while the entropy lower bound is negative. This explicitly shows how a failed certificate leaves the actual operator test available. At \(k=20\) the actual value remains \(0.0501193\rho>0\). The states are smooth and positive; the stronger general positivity premise is directly available from Loop A rather than inferred from entropy.

The script records quadrature tolerances and finite results in `cas/paper_i_check_receipt.json`. All computations are toy quadratures or finite algebra; no transport ODE was solved. The analytic proof above establishes the general inequality; the toy values illustrate its scope and conservatism.

## R9. Physical integration and observable contract

Use the same observer, epoch, bolometric normalization and sky support for (i) the radiation moments, (ii) v15 angular entropy, and (iii) any optical shear estimate. Let \(S_{opt}=c\sigma_{opt}\) be the inverse-time shear recovered by Loop C's E2 response, with \(\|S_{opt}-c\sigma\|\le\varepsilon_S\). Form
\[
\mathcal C=\widehat R+\frac{8\rho}{15c}S_{opt}.
\]
Under the common-congruence and Loop A transport assumptions,
\[
\boxed{\|\mathcal C\|
\le\varepsilon_R+\frac\rho c\varepsilon_S
+\frac{\rho\eta}{c}\|S_{opt}\|.}
\tag{P10}
\]
Indeed, subtract \(R+\mathcal L_I\sigma=0\), use \(\|\mathcal L_I\|\le\rho\), and apply (P1) to \(S_{opt}/c\). This provides a finite cross-channel consistency envelope without identifying a temperature quadrupole with matter shear. A frame/clock/source-motion uncertainty enters \(\varepsilon_S\) or the joint nuisance model, not the entropy gap by fiat.

The required inputs are physical \(I\) or its joint feasible image, its total \(\rho\), an upper bound on the normalized angular information, and \(\widehat R,\varepsilon_R\) for inversion. Frequency bands require a bolometric completion error; v15's high-energy witness remains relevant to that acquisition step. Neither a covariance law nor confidence coverage is created by (P1). For a joint set of allowed brightness/residual/calibration states, evaluate this deterministic map state by state before applying existing x/Q/support-F/exceedance-Pi/depth-G_F functionals. Missing spectral-law or derivative inputs remain explicit unavailable channels.

## R10. Checkpoint and high-value next lemma

The delivered candidate is **the mass-matched entropy-to-shear-response certificate** (P1)–(P8), with the optical application (P10). Its scalar proof and physical units are closed; the finite computations passed. The closing independent review checks the centering identity, entropy normalization and the factor of \(c\) in (P10).

A high-value further lemma is a moment-aware optimum: minimize the v15 angular information at fixed quadratic form \(\langle S,\mathcal L_I S\rangle\), total energy and declared lower moments. Its target kernel is the explicit quartic polynomial in (P5), so v15's finite representative theorem supplies a positive rank-four natural field and a finite dual problem. This could replace the conservative L1 transfer by a response-specific entropy envelope. The other author's exact rank-four projection result is complementary: preserving all energy moments through four preserves \(\mathcal L_I\) exactly even when angular information remains above that cutoff. No new dynamical closure is required for either calculation.




\clearpage

# Entropy projection preserves the massless shear response at angular rank four

Internal conditional theory and executed static toy, 2026-10-26. Owner: common/obsstat for reconstruction and response algebra; MIO for a declared diagnostic image; HTT for any later posterior pushforward. Claim tier C0, transfer source none. No physical ODE, native solver, source-paper edit, repository push, or empirical CMB analysis is included.

## R1 — Question and achieved result

For massless radiation, exact energy-moment matching through angular cutoff L=4 preserves the complete five-dimensional radiative shear operator. This remains true when the unresolved angular entropy and radial spectral entropy are positive. Consequently an entropy projection may lose descriptive information while preserving this specified mechanical response exactly.

For L=2 or 3, only the unmatched energy hexadecapole affects the operator. On a declared bounded brightness domain, the reduced entropy curvature gives an explicit bound on that response error and, when transport derivatives are separately available, on the conditional shear inverse. A static maximum-entropy calculation below compares L=2 and L=4 and verifies the distinction numerically.

This research unit builds on the earlier Loop A positivity theorem. The general kernel-span principle and moment-matching existence are already in v15 Paper I; the present work specializes them to the exact shear operator, derives the response-specific error constant, and performs the finite projection experiment.

## R2 — Sources and comparison with v15

The source archive is ANGULAR_CALCULUS_PAPER_I_v15_ACK_CLEAN_OVERLEAF.zip, SHA-256 \texttt{c856939999ea\allowbreak 202a5d676059\allowbreak 907bfcef7274\allowbreak 027299a2664f\allowbreak d55b86eecd69\allowbreak faad}, as recorded in sources/paper_I/ARCHIVE_IDENTITY.json. The following original source locations were read directly:

| v15 source | Reused mathematical content |
|---|---|
| §2, eq:directional-energy-density, eq:retained-moments | Physical brightness I=E_*ρ_f; retained moments are energy moments, not temperature coefficients |
| §3, eq:main-contracted-entropy, eq:rho-beta-chain, eq:main-lift-identity | Convex reduced entropy, massless three-quarter power, exact lift divergence |
| §3b, eq:quadrupolar-pressure and eq:kinetic-fisher-metric | Concrete mechanical angular response and local curvature interpretation |
| §4, thm:representative, eq:exact-two-axis-budget, eq:adjacent-angular-budget | Positive finite entropy representative; spectral/angular decomposition; refinement |
| §5, subsec:score-span-identification | A response kernel in the span of retained kernels is already determined |

The earlier research/LOOP_A_LOWELL.md in HTT_INTERNAL_THEORY_20261026 supplies the exact positive shear operator and its transport inverse. It reuses the attached Ellis textbook, PDF p. 299, Eqs. (11.1)–(11.2), and explicitly resolves the 2/7 versus 10/7 source discrepancy using angular Liouville transport.

Thus v15 already contains the abstract mechanism needed for exact preservation. It does not display the shear operator, the cutoff-four mechanical corollary, the rank-four Bregman-to-response constant below, or the executed L=2 versus 4 comparison. This is a bounded source comparison, not a literature-wide novelty claim. A new SciSpace query on entropy closures and response errors was also executed; its summaries were used for discovery only. The cited v15 source and inherited primary transport derivation support the equations here. The separate Paper I reuse study by the parent team owns the global isotropic entropy inequality; this report uses a finite-amplitude local curvature bound for an arbitrary finite projection.

## R3 — Physical and entropy conventions

Keep c, ħ and k_B explicit and use signature (−,+,+,+). V15 uses a physical four-velocity U·U=−c² and photon energy E=−p·U. Set u=U/c, so u·u=−1 as in Loop A. Its dot derivative is u·∇ per proper length cτ. Consequently shear σ and expansion Θ have units m⁻¹; their proper-time rates are multiplied by c. Angular directions are photon propagation directions e, opposite to outward sky directions.

For the two photon helicities,

\[
 I(e)=\mathcal D\int_0^\infty E^3 f(E,e)\,dE,\qquad
 \mathcal D=\frac{2}{(2\pi\hbar)^3c^3},\qquad
 \rho=\int I\,d\Omega .
 \tag{ES1}
\]

I has energy-density per solid-angle units; solid angle is dimensionless in SI. It differs from the energy-resolved radiance c\(\mathcal D\)E³f used in v15 §3b by the explicit factor c. The present I is the directional energy density used in the local moment equation.

Define q=∫Ie, π=∫I e_⟨a e_b⟩, H₃=∫I e_⟨a e_b e_c⟩ and H₄=∫I e_⟨a e_b e_c e_d⟩. Physical energy flux is cq. The entropy lift may be applied to an arbitrary nonthermal occupation with the specified regular finite-entropy assumptions: f itself need not be Planckian.

The photon energy-matched ray lift has

\[
 I=C_\gamma T_E^4,\quad C_\gamma=\frac{\pi k_B^4}{60\hbar^3c^3},
 \qquad h(I)=-C I^{3/4},\quad C=\frac{4C_\gamma^{1/4}}{3k_B}.
 \tag{ES2}
\]

Here \(\mathcal H\)[I]=∫h(I)dΩ is negative entropy divided by k_B, with number-density units; S_ray=−k_B\(\mathcal H\). The coefficient follows from s_ray=4I/(3T_E). Substitution of the v15 massless formula, with I=E_*ρ_f, gives the same C and cancels the arbitrary reference energy E_*.

For the quantitative estimate impose 0<I_min≤I,J≤M<∞ almost everywhere. Equivalently their energy-calibrated temperatures lie in a common compact positive interval, with T_E≤(M/Cγ)^(1/4). This supplies finite scores and a common curvature bound. It is an amplitude-domain assumption, not an assumption that all frequency-resolved spectra are thermal.

## R4 — The retained response kernels

On spatial STF2, let

\[
 \mathcal L_I S=\frac{8\rho}{15}S+\frac{10}{7}\operatorname{STF}(S\pi)-H_4:S
 =\int I(e) B_eS\,d\Omega,
 \tag{ES3}
\]
\[
 B_eS=2\operatorname{STF}(See^T)-\operatorname{STF}(ee^T)(e^TSe).
 \tag{ES4}
\]

Loop A proved self-adjointness and 0≤B_e≤Id. Each matrix entry of B_e is an even polynomial of angular degree at most four. Hence its only spherical harmonic sectors are \(\ell\)=0,2,4. This is a statement about bolometric energy multipoles, not the low multipoles of T_E, log T_E, or β=T_ref/T_E.

Let f_L be the v15 entropy maximizer matching the complete energy moments through L and put J=I_L. Its inverse-temperature field belongs to V_L and is strictly positive on the stated interior moment domain. The resulting brightness generally contains harmonics beyond L. Matching measured moments and truncating the nonlinear brightness field are distinct operations.

## R5 — Exact preservation and an entropy error theorem

**Preservation theorem.** If ∫(I−J)Z_\(\ell\)m=0 for every retained harmonic through L≥4, then \(\mathcal L\)_I=\(\mathcal L\)_J. More minimally, equality of the \(\ell\)=0,2,4 energy moments suffices.

**Proof.** Each entry of B_e belongs to V₄, so the difference of the two angular integrals in Eq. (ES3) vanishes. Equivalently, Eq. (ES3) uses only equal ρ, π and H₄. This argument applies to any moment-matching representative, not only the entropy maximizer. Any radial redistribution that leaves I unchanged also leaves \(\mathcal L\) unchanged. Thus unresolved radial shape and higher energy multipoles may carry positive entropy costs while this operator is preserved. \(\square\)

The reduced Bregman divergence is

\[
 D_{\mathcal H}(I\Vert J)=\int[h(I)-h(J)-h'(J)(I-J)]\,d\Omega .
 \tag{ES5}
\]

For the entropy representative, h'(J) is a fixed multiple of its fitted β∈V_L, so moment matching removes the tangent term. The physical angular entropy increment is ΔS_ang=k_B D_\(\mathcal H\)(I∥I_L). V15's exact two-axis budget supplies this identity and keeps the spectral cost separate.

**Finite-amplitude bound.** Direct differentiation gives

\[
 h''(I)=\frac{3C}{16}I^{-5/4}\ge\kappa_M:=\frac{3C}{16M^{5/4}} .
 \tag{ES6}
\]

Taylor's integral remainder along the segment between I and J therefore yields

\[
 \|I-J\|_{L^2(d\Omega)}^2
 \le\frac{32M^{5/4}}{3C}D_{\mathcal H}(I\Vert J).
 \tag{ES7}
\]

This uses the stated finite domain rather than a small-anisotropy expansion.

For every L≥2, ρ and π match, so δ\(\mathcal L\)=−δH₄:S. Let P₄ denote the orthogonal harmonic projector. The standard STF angular identity has coefficient

\[
 \Delta_4=\frac{4\pi\,4!}{9!!}=\frac{32\pi}{315},\qquad
 \|\delta H_4\|_F^2=\Delta_4\|P_4(I-J)\|_2^2 .
 \tag{ES8}
\]

To verify the second equality, write P₄(I−J)=A_⟨abcd⟩eᵃeᵇeᶜeᵈ. Orthogonality gives δH₄=Δ₄A and ∥P₄(I−J)∥²=Δ₄∥A∥². Contraction of a rank-four tensor with a unit STF2 has output norm at most its Frobenius norm. Combining this fact, Eq. (ES8), and Eq. (ES7) proves

\[
 \boxed{\|\mathcal L_I-\mathcal L_{I_L}\|_{\rm op}
 \le\epsilon_{\rm ent}:=
 \left[\frac{1024\pi}{945C}M^{5/4}D_{\mathcal H}(I\Vert I_L)\right]^{1/2}}
 \quad (L\ge2).
 \tag{ES9}
\]

Replacing D_\(\mathcal H\) by ΔS_ang/k_B gives physical entropy units. Replacing it by the larger full spectral-plus-angular divergence is valid but loses the separation relevant to this response. At L≥4 the structural error bound is exactly zero and is sharper than a positive entropy-only estimate. The constant in Eq. (ES9) is sufficient; no optimality claim is made.

## R6 — Transport, shear error, and what matching does not supply

In a smooth geodesic irrotational congruence with collisionless radiation, the exact quadrupole equation is

\[
 \mathcal L_I\sigma=-R,\qquad
 R=\dot\pi_{\langle ab\rangle}+\frac43\Theta\pi_{ab}
 \;+\frac25D_{\langle a}q_{b\rangle}+D^cH_{abc}.
 \tag{ES10}
\]

Suppose an approximate residual R_L is supplied with ∥R−R_L∥≤ε_R. Set σ_L=−\(\mathcal L\)_J⁻¹R_L and λ_L=λ_min(\(\mathcal L\)_J). If λ_L>ε_ent, subtract the two equations and use the lower Rayleigh estimate for \(\mathcal L\)_I:

\[
 \boxed{\|\sigma-\sigma_L\|\le
 \frac{\epsilon_R+\epsilon_{\rm ent}\|\sigma_L\|}
 {\lambda_L-\epsilon_{\rm ent}}.}
 \tag{ES11}
\]

Operator and denominator units are energy density, while R has energy-density per length units, so the output has shear units m⁻¹. For L≥4 use ε_ent=0. The remaining term is ε_R/λ_L.

Matching moment values at one event does not determine their spatial or time derivatives. If an exact L≥4 projection is instead defined on an open neighborhood in the same fixed smooth congruence, equality of q, π and H₃ as fields implies equality of their derivatives there, and hence of R. That stronger supplied-field construction preserves both sides of the transport relation. The local algebra alone does not produce the required observational jets.

The zero-density and narrow-support degeneracies remain those in Loop A. For positive full-sky I, λ_min(\(\mathcal L\)_I)>0; the usable lower certificate λ_min(ρh/3+π) is also preserved already at L=2. A common lower certificate can therefore survive while the actual operator changes through H₄.

## R7 — Executed finite entropy projection

The toy is the positive axisymmetric field

\[
 w(\mu)=I/I_0=1+0.3P_2(\mu)+0.2P_4(\mu)+0.15P_6(\mu),\quad
 \rho_0=4\pi I_0.
 \tag{ES12}
\]

Its exact polynomial minimum is 0.878125 and maximum 1.65. The fitted fields are w_L=β_L⁻⁴, with β_L=∑_even≤L b_\(\ell\)P_\(\ell\). The full harmonic solution reduces to this even axisymmetric subspace because the data have these symmetries and the v15 representative is unique.

The code minimizes the convex dual ⟨β⁻³⟩/3+∑b_\(\ell\)⟨wP_\(\ell\)⟩ using its analytic gradient and Hessian 4⟨β⁻⁵P_iP_j⟩. Newton steps enforce positivity over the entire polynomial interval using all real derivative roots, plus line-search descent. No kinetic evolution is integrated.

Fitting uses 96 Gauss–Legendre nodes and an independent refinement with 192. Evaluation uses 256 and 320 nodes; twelve azimuthal nodes integrate the degree-four operator exactly in azimuth. The largest retained-moment residual is 1.51×10⁻¹⁵. Coefficients and reported entropy/operator quantities change by less than 4.6×10⁻¹⁵ under refinement. These are numerical consistency checks, not interval quadrature certificates.

| Result | L=2 fit | L=4 fit |
|---|---:|---:|
| ΔS_ang/S_iso | 3.73709609×10⁻⁴ | 9.37160903×10⁻⁵ |
| Actual ∥δ\(\mathcal L\)∥/ρ₀ | 0.00654243536 | 1.23×10⁻¹⁵ |
| Curvature bound, Eq. (ES9), /ρ₀ | 0.0137593740 | 0.00689030783 |
| Structural preservation bound /ρ₀ | — | 0 exactly |
| Same-residual shear error /σ_ref | 0.00737521276 | 1.78×10⁻¹⁵ |
| Eq. (ES11) shear bound /σ_ref | 0.0280335840 | 0 exactly |

For the shear control, the true STF-basis coordinates are σ_ref(1,1,1,1,1)/√5 and R is manufactured from the target operator, with ε_R=0. The L=4 nonzero floating errors are roundoff; the structural theorem is exact. This control is explicitly algebraic and does not supply physical derivative data.

An independent exact axisymmetric identity is also checked: if c₄ is the unmatched P₄ brightness coefficient, then ∥δ\(\mathcal L\)∥/ρ₀=4|c₄|/105. Wolfram returned the corresponding eigenvalue slopes (−4/105,8/315,−2/315) for m=0,|m|=1,|m|=2. It also checked h'', Δ₄, and the coefficient 1024π/(945C).

The runnable script is cas/entropic_shear_projection.py; numerical and exact outputs are cas/entropic_shear_results.json and cas/entropic_shear_constants_results.json. The three-panel figure figures/entropic_shear_projection.pdf/.png displays the angular fits, positive entropy residual, and the disappearing operator error. It is an analytical toy, not measured CMB.

## R8 — Evidence verdict and failure correction

The preservation theorem and error bounds are DERIVED under their displayed assumptions. The projection is IMPLEMENTED and the scoped static toy passed its moment, positivity, entropy cancellation, independent operator identity, isotropic limit, inverse-error and resolution checks. The general theorem is supported by the proof, not by the finite sample.

The first numerical call failed because an einsum retained an azimuthal index after that index had been averaged away. Changing the contraction from n,npab,n to n,nab,n corrected the implementation; the full scientific checks then passed. One authoring-tool call had a JavaScript syntax error before creating its requested CAS file; a subsequent call created and executed the same bounded coefficient check. Neither failure changes the theoretical argument.

No strong no-go is asserted. The result identifies a sufficient retained set for one response. The v15 linear-span criterion is acknowledged as existing work; the explicit mechanical application and quantitative response bound are the extension documented here. Fresh independent review remains a separate parent-owned step.

## R9 — Reusable implementation contract

Inputs are a fixed observer/congruence, bolometric energy-moment convention, a positive interior moment vector, cutoff L, and—when invoking Eq. (ES9)—a common finite M and a reduced Bregman or angular-entropy defect. Outputs are the fitted β_L and energy moments, the symmetric 5×5 response matrix, its minimum eigenvalue, and the appropriate structural or entropy error certificate. Shear inference additionally consumes R_L and ε_R.

Record moment-fit errors separately from projection error. An approximate L=4 fit can have a small residual operator error bounded directly from its ρ, π and H₄ mismatches; exact preservation must not be assigned from cutoff metadata alone. Frequency-band data additionally require the bolometric completion and energy-boundary controls inherited from Loop A.

All tensorized diagnostics remain typed as before: legacy F_cert=x_C/U is a certified diagnostic rejecting material/volume occupancy; current F_sup is directional support utilization; F_ν is occupancy under a separately specified measure and support. The reduced entropy \(\mathcal H\) is none of these quantities. No new empirical law, occupancy measure, depth covariance, posterior or native transfer is inferred.

## R10 — Checkpoint and next use

The requested bridge, constants, proof, projection experiment, figure and reusable code are complete within the author unit. The next empirical use is to form the energy moments through \(\ell\)=4 with their covariance and bolometric-error budget, then supply transport jets before evaluating the shear inverse. The original R32 morphology results and Loop A theorem remain unchanged.





\clearpage

\begin{center}\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{/workspace/scratch/ef61c9590364/HTT_TEFF_V15_EXTENSION_20261026/figures/entropic_shear_projection.pdf}\end{center}

**Static positive moment reconstruction.** The declared brightness contains degrees 2, 4 and 6. The rank-four fit preserves the shear operator exactly despite positive remaining entropy. The rank-two fit has a nonzero operator error bounded by the derived finite-brightness certificate. These are analytical toy states.

\clearpage

# Number–energy calibration, observer response and finite beam mixing

Internal theory extension, 26 October 2026. This note adopts the supplied Angular Calculus Paper II v15 as the active manuscript source and derives three connections to the preceding HTT theory report. The source manuscript is preserved unchanged. The new results are a resolved-ray observer law, a sharp finite-temperature-range beam envelope, and a calibrated population response with its explicit nuisance direction.

## R1 — Question and completed construction

The physical question is which part of a dipolar kinetic measurement tracks population structure independently of an observer boost or a change in temperature. Paper II measures both number and energy on each momentum ray. Their different Doppler weights provide a direct answer before angular averaging. A finite beam then mixes different temperatures and changes that answer by a calculable amount. We derive the exact transformation, an attained finite-amplitude mixing envelope, and its statistical propagation.

The term “effective frame” in the v15 file name denotes the number–energy calibration at a fixed observer. It is not a selected Lorentz observer or an entropy-minimizing velocity. The manuscript explicitly fixes \(U^a\), \(U_aU^a=-c^2\), and calls its construction a matched pair of fields.

All 13 Paper II TeX sources were read, including the global-calibration, rank-asymptotic and cutoff appendices. Their exact domains and labels are preserved in the source inventory.

## R3 — Conventions and replacement of legacy semantics

Keep \(c,\hbar,k_{\rm B}\), signature \((-+++)\), and \(U=cu\) when importing the preceding report's unit-timelike convention. Incoming sky direction \(n\) is opposite particle propagation direction \(e\). Let \(\boldsymbol\beta_{\rm obs}=v_{\rm obs}/c\) denote observer velocity; the thermodynamic inverse temperature is \(1/(k_{\rm B}T)\). They are distinct quantities.

The replacement map is explicit:

| Legacy shorthand | Active v15 meaning |
|---|---|
| One \(T_{\rm eff}\) represents a complete kinetic state | Energy-calibrated \(T_{\rm L,U}\) is one ray-wise entropy-selected representative; independently measured number introduces \(\eta\) |
| “Effective frame” interpreted as observer rest frame | Fixed-observer number–energy calibration; Landau/Eckart frames require \(T^{ab}\) or \(N^a\) |
| Energy-only angular refinement supplies particle flow | Number and energy have separate currents and separate retained scores |
| High angular rank means the same particle population at higher resolution | Massive rank \(\ell\) has the radial Fisher weight \(v^{2\ell+1}\) and its own sampled energy |
| A small high-rank weight alone certifies a cutoff | A coefficient-tail bound and positive patch constants complete the cutoff certificate |
| Kinetic entropy curvature is an observational likelihood | It is a susceptibility/convex geometry; measurement covariance and selection supply a separate statistical law |

The symbol \(\mathcal Q_{NE}\) below is the calibration ratio. It is not the HTT anchor gauge \(Q\), nor a temperature quadrupole. Paper II uses \(Z_{\ell m}=\sqrt{4\pi}Y_{\ell m}\) normalized in \(d\omega=d\Omega/(4\pi)\); imported orthonormal \(d\Omega\) coefficients require the corresponding factor.

## R4–R5 — A resolved-ray observer law

At the same event and for the same photon ray, let \(E'=D E\), with Doppler factor \(D>0\), and let \(n'\) and \(n\) be related by aberration. Scalar occupation means
\[
f'(E',n')=f(E'/D,n).
\tag{II1}
\]
The factor \(D\) is independent of energy for massless particles on this ray. Substitution in the two radial integrals gives the exact laws
\[
\mathcal N'(n')=D^3\mathcal N(n),\qquad
\mathcal E'(n')=D^4\mathcal E(n).
\tag{II2}
\]
Therefore
\[
\boxed{\mathcal Q'_{NE}(n')=\mathcal Q_{NE}(n).}
\tag{II3}
\]
This statement holds for arbitrary positive occupations with finite number and energy, not only equilibrium spectra. The angular pattern is remapped by aberration: weight zero does not mean that its multipole coefficients are unchanged.

Whenever the regular v15 inverse exists, its uniqueness gives
\[
\eta'(n')=\eta(n),\qquad T'(n')=D\,T(n).
\tag{II4}
\]
The ratio of total number and total energy is different because angular integration carries its own Jacobian. Equation (II3) concerns resolved ray densities.

At an isotropic regular reference, write \(A_\xi=\partial_\eta\log I_2^\xi\), \(B_\xi=\partial_\eta\log I_3^\xi\), \(J_\xi=4A_\xi-3B_\xi>0\). The first-order contrast
\[
\mathcal C=4\,\delta\log\mathcal N-3\,\delta\log\mathcal E
=J_\xi\,\delta\eta
\tag{II5}
\]
annihilates both a thermal perturbation and the boost of an isotropic monopole. It adds a population-sensitive coordinate to Loop B's temperature-dipole and aberration channels. Intrinsic blackbody temperature anisotropy also cancels in this contrast, so the question it answers is specifically population/shape calibration.

## R5 continued — A sharp finite beam envelope

Let a beam average with a common nonnegative, energy-independent normalized measure \(dB\). Assume its resolved rays have a common \(\eta_0\) and positive temperatures \(a\le T\le b\). This includes Planck rays with \(\eta_0=0\). The v15 radial laws give
\[
\overline{\mathcal N}=C_N(\eta_0)\langle T^3\rangle_B,\qquad
\overline{\mathcal E}=C_E(\eta_0)\langle T^4\rangle_B,
\]
and consequently
\[
R_B:=\frac{\overline{\mathcal Q}_{NE}}{Q_\xi(\eta_0)}
=\frac{\langle T^3\rangle_B^4}{\langle T^4\rangle_B^3}.
\tag{II6}
\]
The constants cancel; the result is independent of the temperature unit.

**Sharp beam-range lemma (generalized Kantorovich specialization).** Put \(r=b/a\ge1\). Then
\[
\boxed{\frac{256r^3(r^2+r+1)^3}
{27(r^3+r^2+r+1)^4}\le R_B\le1.}
\tag{II7}
\]
For \(r>1\), the lower bound is attained by temperatures \(a,b\) with hot weight
\[
p_*=\frac{3r^2+2r+1}{(r^3+r^2+r+1)(r^2+r+1)}.
\tag{II8}
\]
The upper equality holds precisely when \(T\) is constant almost everywhere under the beam.

The scalar bound is an exact specialization of the generalized Kantorovich reverse-Hölder inequality: set \(X=T^3/a^3\), \(1\le X\le r^3\), and \(p=4/3\); then \(R_{\min}=K(r^3,4/3)^{-3}\). The primary reference is T. Furuta, “Basic properties of the generalized Kantorovich constant and its applications,” *Acta Sci. Math. (Szeged)* **70** (2004), 319–337, Definition 1, Theorem A and Theorem 3(i), [primary article](https://acta.hu/download.phtml?id=2785), read directly. The following elementary proof displays its attaining temperature mixture for the present calibration.

**Proof.** Normalize \(a=1\). Hölder gives the upper bound. Put \(X=T^3\), \(m=\langle X\rangle_B\). Convexity of \(X^{4/3}\) puts it below the endpoint secant on \(1\le X\le r^3\), so
\[
\langle T^4\rangle_B\le A m+B,\quad
A=\frac{r^4-1}{r^3-1},\quad B=1-A<0.
\]
It follows that \(R_B\ge m^4/(Am+B)^3\). Differentiating its logarithm gives \(4/m-3A/(Am+B)\), which vanishes at \(m_*=-4B/A\). This point lies in \((1,r^3)\). The derivative is negative before it and positive after it. Substituting \(m_*\) yields (II7); choosing only endpoint temperatures saturates the secant inequality, and \(p_*=(m_*-1)/(r^3-1)\) gives (II8). The limit \(r\to1\) yields \(R_B=1\).

Monotonicity of the v15 calibration now gives the exact interval
\[
Q_\xi^{-1}\!\left(Q_\xi(\eta_0)R_{\min}(r)\right)
\le\eta_{\rm eff}\le\eta_0.
\tag{II9}
\]
For BE at a Planck reference, mixing moves the two-moment representative into the regular \(\eta<0\) branch. This fitted parameter describes the entropy-selected representative; the beam-averaged spectrum retains the distinct mixing residual calculated in Paper I.

For \(T=T_0(1+\Theta)\), \(\langle\Theta\rangle_B=0\), uniformly small contrast gives
\[
\log R_B=-6\langle\Theta^2\rangle_B+O(\langle|\Theta|^3\rangle_B),
\quad
\eta_{\rm eff}-\eta_0=-\frac{6\langle\Theta^2\rangle_B}{J_\xi(\eta_0)}
+o(\langle\Theta^2\rangle_B).
\tag{II10}
\]
The sharp bound instead remains finite amplitude. If \(r=1+s\), its expansion is
\(\log R_{\min}=-3s^2/2+3s^3/2+O(s^4)\).

An energy-dependent beam does not use one common measure for both moments. Equations (II6)–(II10) then require the measured spectral/angular response to be propagated before forming the ratio. The same issue applies to incomplete frequency coverage and bandpass-derived moments.

## R6 — Two relativistic limits and a material-current connection

For an exactly isotropic thermal sky viewed by a boosted observer, in the observed angular coordinate \(\mu=n'\cdot\widehat\beta_{\rm obs}\),
\[
D=[\gamma(1-\beta_{\rm obs}\mu)]^{-1}.
\]
A full-sky angular mean obeys
\[
\langle D^3\rangle=\gamma,\qquad
\langle D^4\rangle=\gamma^2(1+\beta_{\rm obs}^2/3).
\]
Thus the resolved-ray ratio is constant, while the ratio formed after averaging is
\[
\frac{\overline{\mathcal Q}_{NE}}{Q_\xi(\eta_0)}
=\frac{1-\beta_{\rm obs}^2}{(1+\beta_{\rm obs}^2/3)^3},
\quad
\log R_B=-2\beta_{\rm obs}^2-\frac13\beta_{\rm obs}^4+O(\beta_{\rm obs}^6).
\tag{II11}
\]
This is an explicit noncommutation of angular averaging and thermochemical calibration, with both operations completely specified.

The v15 counterflow also supplies a direct addition to Loop D's geometric state. Choose its reciprocal thermal energies as
\[
\Theta_+^{-1}=a_0+d_0,\qquad \Theta_-^{-1}=a_0-d_0,
\quad a_0>|d_0|,\qquad \Theta_\pm=k_{\rm B}T_\pm,
\]
Hold \(K_0,a_0\) and the angular preference \(0<b_0\le1\) fixed, and vary \(d_0\) within \((-a_0,a_0)\). For this counterflow use propagation angle \(\mu=e\cdot\widehat z\), rather than the incoming-sky angle in the preceding boost calculation. Its moments are
\[
\mathcal E(\mu)=6\mathcal D K_0,\qquad
\mathcal N(\mu)=2\mathcal D K_0(a_0+b_0d_0\mu).
\tag{II12}
\]
All members have the same total number, total energy and perfect-radiation stress tensor, but
\[
\frac{j^z}{cn}=\frac{b_0d_0}{3a_0}.
\tag{II13}
\]
The gravitational initial constraints in Loop D consume \(T^{ab}\), so this local population coordinate can vary within their fixed source data. If the particle current defines a timelike material congruence, its speed relative to the energy frame is \(j^a/n\) and
\[
\gamma_{NE}=\left(1-\frac{j_aj^a}{c^2n^2}\right)^{-1/2}.
\tag{II14}
\]
This is a local energy–particle-frame relation. The stress tensor fixes the energy frame, and number measurements determine the additional current. A specified transport/interaction model connects it to a material history.

## R7 — Executed symbolic and toy checks

The Wolfram program paper_ii_check.wl returns four exact zero residuals: the full-sky Doppler ratio, the endpoint mean, the sharp endpoint ratio, and stationarity of the bound. It also returns the two series in (II10)–(II11). At the Planck boundary,
\[
Q_c=0.1219819003452971,\qquad
J_{\rm BE}(0)=\frac{4\zeta(2)}{\zeta(3)}
-\frac{3\zeta(3)}{\zeta(4)}=2.141851504502379.
\]
The stored Python script passed 1,200 positive-beam examples against the proven range, independent exact-rational evaluation at \(r=2\), direct boost moment quadratures, temperature-scale invariance, and the exact quotient law at 501 angular points. Maximum pointwise relative quotient error was \(9.99\times10^{-16}\).

At \(r=2\), the attained lower ratio is \(702464/1366875=0.5139197073616826\), with hot weight \(17/105\). Its Planck-reference calibrated lower endpoint is \(\eta_{\min}=-0.4244066257029\). At illustrative \(\beta_{\rm obs}=0.00123\), whole-sky spectral averaging gives \(\eta_{\rm eff}=-1.41271484\times10^{-6}\) from the exact two-moment inverse. This number is an analytical toy readout of averaging, not a measured chemical distortion.

## R9 — Observational response, covariance and the tensorized state

For calibrated measured ray moments, linear error propagation gives
\[
\delta\log\mathcal Q_{NE}
=4\frac{\delta\mathcal N}{\mathcal N}
-3\frac{\delta\mathcal E}{\mathcal E},\qquad
\delta\eta=\frac{\delta\log\mathcal Q_{NE}}{J_\xi}.
\tag{II15}
\]
The covariance of the contrast is
\[
V_{\log Q}=\frac{16V_{NN}}{\mathcal N^2}
+\frac{9V_{EE}}{\mathcal E^2}
-\frac{24V_{NE}}{\mathcal N\mathcal E}.
\tag{II16}
\]
This is a local approximation to the joint measurement law. On a specified regular calibration interval with \(J_\xi\ge J_{\min}>0\), the mean-value theorem also gives the finite deterministic bound
\[
|\eta_1-\eta_2|\le
\frac{|\log\mathcal Q_1-\log\mathcal Q_2|}{J_{\min}}.
\tag{II17}
\]
A joint positive-moment uncertainty set can be pushed through the exact ratio and inverse instead of using the linear approximation.

At an isotropic MB reference, the one-component design for observer boost, intrinsic thermal dipole and chemical dipole is
\[
\begin{pmatrix}\delta_N\\\delta_E\end{pmatrix}
=\begin{pmatrix}3&3&1\\4&4&1\end{pmatrix}
\begin{pmatrix}b\\t\\\chi\end{pmatrix}.
\tag{II18}
\]
It has rank two, kernel \((1,-1,0)\), and identifiable target \(\chi=(4,-3)(\delta_N,\delta_E)^T\). An unknown common fractional gain adds the column \((1,1)^T\), which is identical to the MB chemical response. This specific calibration nuisance must be supplied or constrained. For fractional uncertainties \(10^{-3}\) with correlation \(0.9\), the contrast variance is \(3.4\times10^{-6}\); discarding the covariance gives \(25\times10^{-6}\). The toy check verifies these numbers.

The HTT carrier can now include \(\eta_{\ell m}\), the energy–particle current contrast, and their common beam/covariance region. Its support utilization, gauge, exceedance law and depth transport are evaluated only after that joint image is defined. A kinetic entropy divergence alone does not specify the observational covariance or its probability calibration.

## R10 — Next executable result

Apply (II7) to a declared beam and a resolved temperature-range estimate, then project the joint number–energy dipole against calibrated spectral and gain nuisances. The decisive small experiment compares an injected chemical dipole with (i) pure boost, (ii) unresolved temperature mixing, and (iii) an allowed common-gain pattern. Report the surviving target rank and an exact or controlled approximate interval for the chemical coordinate.

The current completed unit supplies all three analytic response cases, sharp beam bounds, a reproducible finite check and a plot. The independent review is included at the end of this report. Source manuscripts, production namespaces, original DAG completion and remote repository state are unchanged.



\clearpage

\begin{center}\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{/workspace/scratch/ef61c9590364/HTT_TEFF_V15_EXTENSION_20261026/figures/paper_ii_population_beam.pdf}\end{center}

**Finite thermal mixing and population calibration.** The curves show the sharp temperature-range envelope and its propagation through the Planck-reference number–energy inverse. The sharp scalar bound specializes the generalized Kantorovich inequality; the fitted population coordinate describes the mixed moments.

\clearpage

# Detector-specific response bounds after number–energy calibration

**Evidence status:** derived finite-amplitude extremizer identity; literature-supported convex-duality method; implementation-verified MB/BE/FD static toy. This chapter extends the v15 calibrated-kernel discussion into a computable response interval. It uses no transport solver.

## R1 — The physical question

Two measured moments can calibrate a ray's population and energy while leaving its detector response uncertain. Paper II already identifies the residual kernel after projecting out number and energy. The useful next step is to compute how far that response can move within a declared spectral entropy budget, while preserving the measured moments exactly.

For a finite detector band this yields an actual upper/lower response frontier. It can replace an arbitrary coordinate-space nuisance radius with a radius tied to the kinetic entropy of compatible states. The entropy budget remains an input to be measured or physically justified.

## R2 — Source and retained result

The input is Paper II v15, sections 02, 03 and 05: the fixed-observer number–energy calibration, the spectral–population information split, and the Fisher projection of a response kernel on the retained moment span. Paper I v15 section 05 and Appendix C explain why an unfiltered superlinear high-energy kernel needs an additional tail condition. We use a bounded detector kernel.

The optimization mechanism is standard convex information geometry. Related expectation bounds and local square-root divergence expansions are developed by Henry Lam, *Robust Sensitivity Analysis for Stochastic Systems*, Mathematics of Operations Research 41 (2016), DOI [10.1287/moor.2015.0776](https://doi.org/10.1287/moor.2015.0776), [arXiv:1303.0326](https://arxiv.org/abs/1303.0326), and by Dupuis, Katsoulakis, Pantazis and Plecháč, *Path-space information bounds for uncertainty quantification and sensitivity analysis of stochastic dynamics*, [arXiv:1503.05136](https://arxiv.org/abs/1503.05136), DOI [10.1137/15M1025645](https://doi.org/10.1137/15M1025645). The particular application below preserves kinetic number–energy constraints and all three occupation statistics. General entropy duality is not a novelty claim.

## R3 — Occupation, units and admissible response

Fix one observer and one ray. For a massless species,
\[
d\nu_U=\mathcal D E^2\,dE,\qquad
\mathcal D=\frac{g_s}{(2\pi\hbar)^3c^3}.
\tag{F1}
\]
Angular integration can be added for a declared angular channel. Let \(h_\xi\) be the v15 convex negative-entropy density and \(g\) a regular reference, with \(0<g<1\) for FD and \(g>0\) for MB/BE. Its score and fluctuation weight are
\[
s_0=h_\xi'(g),\qquad W=[h_\xi''(g)]^{-1}=g(1+\xi g).
\tag{F2}
\]
Use \(\xi=0,+1,-1\) for MB, BE and FD respectively. Let \(\phi=(1,E)^T\), and impose \(\int\phi f\,d\nu_U=\int\phi g\,d\nu_U=m\). The divergence
\[
D(f\Vert g)=\int[h_\xi(f)-h_\xi(g)-s_0(f-g)]\,d\nu_U
\tag{F3}
\]
has number-density units; \(k_BD\) has entropy-density units. A dimensionless bounded kernel \(K(E)\) defines \(\mathcal O_K(f)=\int Kf\,d\nu_U\), also with number-density units.

Assume the required integrals and score pairings are finite. The response family below must remain in the regular entropy domain, and its number–energy moment Jacobian must be nonsingular locally. For BE this includes the sign/domain of the score; for FD it includes the occupation cap.

## R4 — Finite-amplitude construction

Choose a signed response multiplier \(t\) and solve the two moment equations for \(\lambda(t)\):
\[
h_\xi'(g_t)=s_0+tK-\lambda(t)^T\phi,\qquad
\int\phi g_t\,d\nu_U=m.
\tag{F4}
\]
At \(t=0\), \(g_0=g\) and \(\lambda(0)=0\). In explicit form,
\[
g_t=(h_\xi')^{-1}(s_0+tK-\lambda^T\phi).
\tag{F5}
\]
For MB this is an exponential tilt; BE and FD use the corresponding quantum occupation inverse. Only two static calibration variables are solved at each \(t\). No time evolution is involved.

## R5 — Exact response-frontier identity

**Proposition F1.** Suppose \(g_t\) exists in the stated regular domain and has the same retained moments as \(g\). For every compatible \(f\),
\[
D(f\Vert g)
=D(f\Vert g_t)+D(g_t\Vert g)
+t[\mathcal O_K(f)-\mathcal O_K(g_t)].
\tag{F6}
\]
Consequently, at budget \(\epsilon_t=D(g_t\Vert g)\), \(g_t\) attains the largest compatible response when \(t>0\), and the smallest when \(t<0\).

**Proof.** Expand the three Bregman terms and cancel their common entropy contributions. The remaining cross term is
\[
\int[h_\xi'(g_t)-h_\xi'(g)](f-g_t)\,d\nu_U.
\]
Insert (F4). Its \(\lambda^T\phi\) part vanishes by exact moment matching; its remaining part is the last term in (F6). If \(D(f\Vert g)\le\epsilon_t\), nonnegativity of \(D(f\Vert g_t)\) gives
\[
t[\mathcal O_K(f)-\mathcal O_K(g_t)]\le0.
\]
The reference \(g_t\) itself is feasible and reaches equality. Strict convexity identifies the equality state up to null sets. This proves attainment for every constructed regular \(t\), without assuming that all conceivable entropy budgets are covered.

The construction applies to a signed linear combination of several detector channels. Thus repeating (F4) for support directions builds the boundary of a joint response set rather than independent marginal intervals.

## R6 — The calibrated Fisher coefficient

Define
\[
G=\int W\phi\phi^T\,d\nu_U,\qquad
b_K=\int W\phi K\,d\nu_U,\qquad
K_\perp=K-\phi^TG^{-1}b_K.
\tag{F7}
\]
Differentiating the moment equations at zero gives \(\lambda'(0)=G^{-1}b_K\), and therefore
\[
\dot g_0=WK_\perp,\qquad
\chi_K=\left.\frac{d\mathcal O_K(g_t)}{dt}\right|_0
=\int WK_\perp^2\,d\nu_U.
\tag{F8}
\]
The cross term vanishes because \(K_\perp\) is orthogonal to both retained scores. If the family is sufficiently smooth,
\[
D(g_t\Vert g)=\frac{t^2\chi_K}{2}+O(t^3),\qquad
\mathcal O_K(g_t)-\mathcal O_K(g)=t\chi_K+O(t^2).
\tag{F9}
\]
For \(\chi_K>0\), the two local frontiers are
\[
\mathcal O_K^\pm(\epsilon)
=\mathcal O_K(g)\pm\sqrt{2\epsilon\chi_K}+O(\epsilon).
\tag{F10}
\]
The square-root term is an asymptotic approximation, not a finite-budget upper bound. Equation (F6) gives the finite-amplitude result.

For several kernels, the residual susceptibility is the Schur complement
\[
C^\perp_{ij}
=\int WK_iK_j\,d\nu_U-b_i^TG^{-1}b_j.
\tag{F11}
\]
It is positive semidefinite. A null direction means the corresponding response combination belongs to the retained score span almost everywhere in the positive weight; that combination is already fixed by calibration. This is the computational connection to the v15 response criterion.

## R7 — Static toy experiment

The executable experiment uses \(x=E/(k_BT_*)\), measure \(x^2dx\), and
\[
K(x)=\exp[-(x-4)^2/(2\times0.8^2)].
\tag{F12}
\]
It compares MB with \(\eta_0=0\), BE with \(\eta_0=-0.5\), and FD with \(\eta_0=1\), all at inverse-temperature coefficient one. Every trial preserves its own reference number and energy. The detector is illustrative; it is not a fit to an instrument.

The code solves two nonlinear algebraic equations at each signed \(t\), evaluates both frontiers, checks the exact three-point identity on positive moment-preserving competitors, and repeats quadrature at 32 and 128 nodes per subinterval. It records the remaining inverse-temperature margin and compares the calibrated Fisher width with the unprojected kernel width.

Response changes, divergence budgets and susceptibility coefficients in the plotted results are normalized by the reference ray number. Write \(n_0=\int x^2g\,dx\), returned as the unnormalized dimensionless `number`; physical ray number is \(N_{\rm ref}=\mathcal D(k_BT_*)^3n_0\). Multiply the normalized response, divergence and susceptibility by \(N_{\rm ref}\) to restore physical units. The returned `energy` is the unnormalized integral \(\int x^3g\,dx\), whose physical conversion is \(\mathcal D(k_BT_*)^4\). An energy-valued detector kernel carries its additional declared energy unit. The numerical integration covers \(0\le x\le64\) with exponentially small reference tails. The record separates this floating-point quadrature from the continuum proof.

The actual toy output is:

| Statistics | \(\chi_K/N_{\rm ref}\) | Projected/unprojected local width | Maximum relative moment residual |
|---|---:|---:|---:|
| MB | 0.10447052 | 0.70324332 | \(7.41\times10^{-16}\) |
| BE | 0.10034471 | 0.71016168 | \(1.06\times10^{-15}\) |
| FD | 0.10611575 | 0.67370767 | \(1.03\times10^{-15}\) |

The 32-versus-128 quadrature comparison changed the selected frontier values by at most \(1.77\times10^{-13}\). The three-point identity residual was below \(6.25\times10^{-16}\) after number normalization. These are numerical checks of the specified toy and do not set an observational error budget.

## R8 — Meaning of the result

The projected kernel is the spectral redistribution the detector can see after number and energy have been held fixed. Its Fisher norm measures the leading information cost of that redistribution. The finite-amplitude extremizer answers a sharper question: which positive compatible spectrum produces the greatest detector change at the assigned entropy budget?

An unprojected variance counts changes in already measured population and energy as if they were unknown. The Schur complement removes those directions. Conversely, declaring a zero budget would assume that the calibrated spectrum is exact. A real application must supply the residual budget or infer it jointly from additional spectral channels.

## R9 — Connection to the previous HTT report

The earlier bandpass geometry permits finite moment/error regions but leaves their physical radius to an external model. Equations (F6) and (F11) provide one such physical family: positive occupations with calibrated moments and a stated kinetic entropy allowance. A support direction in the tensorized \(x\) coordinates defines a corresponding linear combination of kernels \(K_i\), so the same static solve produces support values for \(F_{\rm sup}\) or a gauge relative to a declared body.

The statistical law and kinetic entropy are distinct inputs. A deterministic entropy-budget region is not automatically a confidence region. To obtain coverage, propagate an actual likelihood or a separately calibrated confidence event for the moments, detector response and entropy allowance.

This extension is especially useful for bounded CMB bandpasses and other finite spectral channels. Paper I's high-energy-tail construction remains the correct boundary for unfiltered superlinear rates. A measured tail constraint can be included as another component of \(\phi\).




\clearpage

\begin{center}\includegraphics[width=\textwidth,height=0.72\textheight,keepaspectratio]{/workspace/scratch/ef61c9590364/HTT_TEFF_V15_EXTENSION_20261026/figures/response_frontier.pdf}\end{center}

**Detector-specific entropy frontiers.** Static MB, BE and FD occupations are varied at fixed number and energy. Finite extremal curves are compared with the projected local Fisher prediction for a bounded Gaussian kernel. These curves are deterministic entropy-budget regions, not statistical confidence intervals.

\clearpage

# Independent review of the v15 extension

Reviewer: \texttt{/root/intern\allowbreak al\_five\_loop\allowbreak \_review\_2026\allowbreak 1026}. Date: 2026-10-26. Scope: `PAPER_I_REUSE`, `PAPER_II_REUSE`, `ENTROPIC_SHEAR_BRIDGE`, and `RESPONSE_FRONTIER`, including their supplied computations, plus a final formula/numerical consistency skim of `V15_INTEGRATION`. This was one fresh review of the changed interface, followed by targeted repair checks. The reviewer did not author or edit the candidates, change either v15 manuscript, launch nested agents, solve a transport ODE, or push a repository.

**Verdict: PASS_SCOPED_AFTER_TARGETED_REPAIRS.** Five concrete findings were repaired and checked. No mathematical blocker remains for these internal conditional constructions. This verdict does not establish observational calibration, publication novelty, a dynamical closure, or the validity of every theorem in the two source manuscripts.

## Findings and closeout

**EXT-01**

**Severity:** Medium: physical normalization

**Finding:** Frontier R7 said its number-normalized response, divergence and susceptibility could be dimensionalized by the common density-of-states scale alone. This omitted the dimensionless reference number n0.

**Verified repair:** R7 now states N_ref = Dcal (k_B T_*)³ n0 and multiplies the normalized outputs by N_ref. It separately identifies the raw number/energy integrals and their conversions. CLOSED.

**EXT-02**

**Severity:** Medium: family premise

**Finding:** II's counterflow claimed fixed total number while explicitly fixing only K0 and b0. Its total number also depends on a0.

**Verified repair:** The note and JSON now fix K0, a0 and b0 and vary d0 inside (−a0,a0). The propagation-angle convention is also explicit. CLOSED.

**EXT-03**

**Severity:** Low: equation transcription

**Finding:** II10 omitted the literal plus before its little-o remainder.

**Verified repair:** The addition is restored in the final display. CLOSED.

**EXT-04**

**Severity:** Medium: thermodynamic terminology

**Finding:** The integration text called the energy-only reference “zero-fugacity”. Eta=0 instead means unit fugacity.

**Verified repair:** It now explicitly says zero chemical potential, eta=0 and unit fugacity. CLOSED.

**EXT-05**

**Severity:** Low: retained variable binding

**Finding:** The integration paragraph used x for the underlying tensor state, blurring the original sample-by-functional definition.

**Verified repair:** X now denotes the underlying state carrier; x remains its declared sample-by-functional array. CLOSED.


The repairs change a dimensional conversion, an explicit parameter-family premise, a displayed equation and two integration definitions. They do not require different numerical toy solutions. Integration equations V1–V9 and all quoted numerical examples agree with the reviewed candidates after these wording repairs.

## Definition and unit binding

The relevant v15 state-space, radial-calibration, entropy and response sections were read directly from the extracted sources. Paper I's energy-only representative and Paper II's number–energy representative are different constrained entropy problems. An energy-calibrated temperature is not a claim that the input spectrum is thermal. The extra spectral defect remains a separate input.

The source convention U²=−c² is mapped to the preceding report by U=cu. A geometric shear has inverse-length units; its proper-time rate is c times that shear. Propagation e and outward sky n have opposite signs. The massless shear operator and its entropy bounds use even moments, while the counterflow current requires the explicitly restored propagation-angle convention.

I=E_* rho_f is directional energy density, whereas the source's spectral radiance contains an extra factor c. The reduced negative entropy has number-density units, and k_B times its Bregman divergence has entropy-density units. A kinetic divergence is not an observational covariance or confidence radius. Paper I's dimensionless inverse-temperature field, Paper II's physical inverse temperature, and the dimensionless observer velocity must not be interchanged. The angular toy defines its natural field by w_L=beta_L^−4, fixing the corresponding brightness-reference normalization.

The three F namespaces remain distinct: certified ceiling utilization, directional support utilization, and occupancy under an independently declared measure. None is supplied by a kinetic entropy defect alone.

## Paper I: global angular entropy to shear response

P2 has the correct reference-energy conversion. From rho_f=3a_xi C_* beta^−4 and the contracted entropy −4a_xi C_* beta^−3, substituting I=E_* rho_f yields the displayed coefficient. Equal total brightness cancels the Bregman tangent term and gives delta=1−\(\langle\)w^(3/4)\(\rangle\). This angular defect concerns the energy-matched lift even for a nonthermal original occupation.

The scalar inequality is valid globally, including its continuous zero-brightness endpoint. The stated third derivative of G has the correct coefficient and sign. Integrating backward or forward from one establishes nonnegativity; weighted Cauchy–Schwarz with \(\langle\)D(w)\(\rangle\)=1 gives delta≥3\(\langle\)|w−1|\(\rangle\)²/32. The small equal-area contrast verifies sharpness of this scalar constant.

For the operator step, equal total mass permits subtracting Id/2 inside the integral. Because 0≤B_e≤Id, the centered operator norm is at most 1/2. Combining this estimate with the scalar inequality gives P1 and the sufficient threshold delta<8/75. The report correctly does not claim that the combined entropy-to-operator constant is sharp, or that failure of this certificate means singular response.

P8 follows by subtracting the exact and isotropic approximate transport equations, with denominator 8/15−eta. P9's coefficient is also correct: the quadrupole part has mean square (15/2)(pi/rho):(pi/rho), giving 45/64 after multiplication by the entropy curvature 3/32. The pressure-only quadratic optimum is a local consequence of the existing entropy representative, not a separate general novelty claim.

For P10, set v=S_opt/c. Then the consistency residual is (Rhat−R)+L_I(v−sigma)+(L_0−L_I)v. The bound ||L_I||≤rho supplies the stated epsilon_S term, and the entropy bound supplies the last term. All three terms have energy-density per length units. This application still requires the common congruence and the collisionless, geodesic, irrotational transport branch; static entropy does not supply its derivative jets.

The scalar divergence result is established prior art. The scoped project addition is the normalization and centered transfer to the physical shear operator, its inverse estimate, and its optical consistency application.

## Paper II: resolved rays, finite beams and particle current

Substitution E'=DE into the fixed-ray radial integrals gives number and energy weights three and four. Their quotient therefore has Doppler weight zero at corresponding aberrated rays. This does not preserve multipole coefficients or make the ratio of angularly averaged moments invariant. The inverse gives remapped eta and weight-one temperature only on the stated regular calibration branch.

The beam proof was checked independently by setting X=T³/a³. At fixed mean m, convexity maximizes the fourth-temperature moment on the endpoint secant. Minimizing m⁴/(Am+B)³ gives m*=−4B/A, the stated hot weight, and the displayed lower ratio. The upper equality requires constant temperature. The lower equality is attained by an endpoint two-temperature distribution with the specified hot weight; a particular fixed discrete instrument need not allow every such allocation. The universal interval is sharp over the stated class of admissible beam distributions.

The scalar lower constant is exactly the established generalized Kantorovich specialization K(r³,4/3)^−3. Furuta's primary Definition 1 and Theorem A were inspected, and the supplied comparison identifies the same constant. It must not be sold as a new scalar inequality. The physical extension is its propagation through the number–energy inverse and its use as a finite beam-mixing envelope. The common fugacity, common nonnegative energy-independent beam and positive temperature interval are essential.

The full-sky Doppler integrals, their small-velocity expansion, the r=2 endpoint fraction, and the Planck-boundary inverse are consistent. A mixed Planck spectrum's fitted negative eta is an entropy-selected two-moment parameter, not evidence for a measured chemical distortion. The source's one-sided Bose boundary qualification is retained.

For the repaired counterflow, total number is 8 pi Dcal K0 a0 and total energy is 24 pi Dcal K0. Fixing K0 and a0 while varying d0 preserves both; isotropic directional energy preserves the full stress-energy tensor. Integrating the propagation dipole gives j_z/(cn)=b0 d0/(3a0). The resulting timelike-current frame relation is local and does not construct a matter history.

The contrast covariance contains the correct −24 cross term. The finite inverse-conditioning bound follows from a positive lower bound on J_xi. The MB design has rank two, its thermal/boost kernel is explicit, and common gain is degenerate with its chemical column. These are correctly framed as conditional response properties rather than a new universal impossibility theorem.

## Rank-four entropy projection bridge

Every entry of B_e is an even angular polynomial with sectors only 0, 2 and 4. Matching these bolometric moments therefore preserves the complete STF2 operator exactly, irrespective of unresolved radial entropy or higher angular information. Entropy maximization supplies one representative; it is not necessary for this linear preservation theorem. Temperature or inverse-temperature truncation alone would not establish it.

On the common finite brightness domain, h''=3C I^−5/4/16 has the stated positive lower bound. Taylor's integral remainder gives ES7. For a pure harmonic-four coefficient A, delta H4=Delta4 A and ||P4 delta I||²=Delta4 ||A||², with Delta4=32 pi/315. Contraction by a unit STF2 tensor is bounded by the rank-four Frobenius norm. Combining these facts yields the ES9 coefficient 1024 pi/(945 C). The constant is sufficient and is not claimed optimal.

ES11 is the correct perturbation-of-inverse bound when lambda_L exceeds the operator error. At exact L≥4 matching, only the separately supplied residual error remains. Equality of moment values at one event does not determine derivatives; the note correctly requires equality as smooth fields on a neighborhood for the stronger derivative-preservation statement.

The static toy genuinely fits a positive natural-field polynomial, rather than merely truncating brightness. The dual gradient and Hessian have the correct signs, and positivity is checked on the polynomial interval. The bound's normalized coefficient 256/945 follows from dividing by rho0² and converting the normalized entropy integral. The constructed same-residual shear test is an algebraic control, not observed transport data.

## Detector response frontier

The three-point Bregman identity F6 has the correct sign. At budget D(g_t||g), nonnegativity of D(f||g_t) gives the extremal response with the appropriate sign of t. The constructed g_t itself attains the bound, and strict convexity fixes the equality state up to null sets. The theorem wisely covers every constructed regular branch point, rather than asserting that every entropy budget or Bose boundary has such a representative.

Differentiating the two moment constraints gives the Gram-projected kernel and lambda'(0)=G^−1 b_K. Consequently chi_K=∫W K_perp² and the local entropy cost is t² chi_K/2. The square-root response expression is asymptotic, not a finite-budget error bar. The multichannel susceptibility is the positive-semidefinite Schur complement; its null directions are retained-score combinations under the positive weight.

The common physical-density conversion is correct after EXT-01. The MB/BE/FD toy respects its respective occupation domains at the numerical points, matches number and energy, and checks the exact identity with positive convex competitors. Its finite quadrature to x=64 is not an interval proof on the infinite energy domain. The regular-domain theorem and the numerical illustration remain separate.

The variational method and local entropy-response expansion have direct precedents, including Lam's Theorem 3.1 and Proposition 3.1, inspected in the retrieved primary text. The quantum-statistical detector application and its achieved response region are the useful project construction; a new general information-projection theorem is not established.

## Executed review checks and evidence limits

The reviewer executed the supplied numerical kernels in memory with output-writing sections disabled. No candidate receipt or figure was overwritten.

* Paper I's ten quadrupolar states, strong-anisotropy states and broad scalar-inequality probes passed. At k=20, the actual normalized minimum eigenvalue remains 0.0501193 although the entropy lower certificate is negative.
* Paper II's 1,200 beam cases, exact r=2 fraction, direct Doppler quadratures, pointwise quotient and covariance/rank checks passed. The maximum quotient error was 9.99×10^−16.
* The angular projection was independently rerun at 128 fit and 288 evaluation nodes. L2 gives operator error 0.0065424353558177; L4 gives 1.33×10^−15 with positive entropy defect 9.3716090272×10^−5. Moment residuals remain below 5.3×10^−15.
* The three frontier statistics were rerun at 96 quadrature nodes and six signed tilts. Moment residuals were below 6×10^−16 and three-point residuals below 1.6×10^−16. The projected susceptibilities reproduce the recorded values.

One reviewer wrapper initially used a filename substring that classified `paper_ii` as `paper_i` and raised a KeyError while summarizing already executed checks. The corrected Paper II-only wrapper completed successfully. This was not a candidate mathematical or numerical failure. The author-recorded implementation failures remain preserved in their existing receipts.

The reported numerical tolerances are floating-point consistency evidence. The proofs establish the general claims. The full source-paper theorem inventories were checked against the definitions and theorem domains needed here; this review does not independently certify every proof or all potential extensions in v15. The preceding five-loop report is reused only through the changed shear, observer and optical interfaces.

## Final disposition

All five findings are closed. The four candidates and the bounded integration summary support internal DERIVED/CONDITIONAL status, with executed static toy evidence where specified. Their application still needs real response kernels, joint calibration/measurement laws, bolometric completion, entropy or tail budgets, and transport derivatives when shear inversion is requested. Neither kinetic entropy nor a deterministic feasible set supplies those observations automatically.

Final reviewed candidate identities are recorded in `INDEPENDENT_EXTENSION_REVIEW.json`. No source manuscript, production ownership, original DAG acceptance, native-solver state, or remote publication state is changed by this review.
