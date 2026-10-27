# Number–energy calibration, observer response and finite beam mixing

Internal theory extension, 26 October 2026. This note adopts the supplied Angular Calculus Paper II v15 as the active manuscript source and derives three connections to the preceding HTT theory report. The source manuscript is preserved unchanged. The new results are a resolved-ray observer law, a sharp finite-temperature-range beam envelope, and a calibrated population response with its explicit nuisance direction.

## R1 — Question and completed construction

The physical question is which part of a dipolar kinetic measurement tracks population structure independently of an observer boost or a change in temperature. Paper II measures both number and energy on each momentum ray. Their different Doppler weights provide a direct answer before angular averaging. A finite beam then mixes different temperatures and changes that answer by a calculable amount. We derive the exact transformation, an attained finite-amplitude mixing envelope, and its statistical propagation.

The term “effective frame” in the v15 file name denotes the number–energy calibration at a fixed observer. It is not a selected Lorentz observer or an entropy-minimizing velocity. The manuscript explicitly fixes \(U^a\), \(U_aU^a=-c^2\), and calls its construction a matched pair of fields.

## R2 — Source inventory and retained theorems

All thirteen Paper II TeX files were read, including all three appendices. Relevant Paper I state-space and radial-quotient sections, the preceding dipole loop B, geometric loop D and optical/statistical loop E were also read. Paper II archive SHA-256 is acfb9b65833c47d422f3413695a217c93e0985806dca4cef7a6d0f0006d7d1b0. The individual source identities are recorded in the accompanying JSON.

| v15 source label | Retained result | Current-use conditions |
|---|---|---|
| eq:number-ray, eq:energy-ray | \(\mathcal N=\mathcal D\int E^2f\,dE\), \(\mathcal E=\mathcal D\int E^3f\,dE\) | Same observer, ray and complete radial response; \(\mathcal D=g_s/[(2\pi\hbar)^3c^3]\) |
| eq:main-inverse-variance; eq:main-ray-inverse | \(\mathcal Q_{NE}=\mathcal N^4/(\mathcal D\mathcal E^3)=Q_\xi(\eta)\), monotone scalar inverse, then temperature | MB: positive ratio; FD: strict \(0<\mathcal Q_{NE}<64/81\); BE cloud: \(0<\mathcal Q_{NE}\le Q_c\) |
| eq:nested-radial-bregman | Spectral information splits into population and residual shape | Existing representatives, finite absolute entropies and integrable matched score pairings |
| eq:counterflow-readout | Isotropic directional energy and stress can coexist with a particle current | Explicit positive MB mixture; local distributional statement |
| eq:main-angular-inverse; eq:main-massless-fisher | Two measured fractional moments invert to thermal and chemical responses; determinant is an energy variance | Regular branch, finite Fisher moments; Planck-boundary variations are one-sided |
| eq:rate-width-identity; eq:pinching-rate | An \(E^2\) response depends on spectral variance after number and energy are fixed | Declared cross-section kernel; pinched family is an example, not universal spectrum |
| eq:realizability-factorization; eq:dressed-flux-bound-main | Massive \(v^\ell\) scores are Poisson-smoothed angular scores; the moment inclusion is strict; flux obeys a rest-energy bound | Fixed mass, physical density-of-states factor \(v\), occupation cap for FD |
| thm:main-global-inverse | Smooth global regular MB/FD inverse onto the dressed realizability interior | Finite rank; \(\min B_1>0\); the proof uses the finite-boundary barrier and finite-entropy witnesses |
| prop:main-BE-certificate | Regular BE inverse plus conditional anisotropic critical certificate; complete isotropic classification | Positive gap for regular image; critical cloud and supported singular measure for the certificate |
| eq:NR-rank-mean; eq:main-large-rank-asymptotic | Low-rank cold kinetic energy grows linearly in rank; fixed-mass high rank selects a cube-root relativistic tail | The two regimes have different scale conditions; no uniform simultaneous-limit estimate |
| eq:finite-cutoff-certificate | Entropy error bounded by omitted natural coefficients and radial Fisher majorants | MB/FD; common positive thermal floor and chemical ceiling; summable specified tail |

These are v15 manuscript results reused here, not newly discovered by this loop. The direct proofs were checked at the level needed for the bridges. In particular, the global MB/FD argument relies on linearly growing dressed scores and a potential that diverges when the thermal boundary touches zero; it is stronger than a local Hessian-invertibility argument alone. The general anisotropic BE critical existence problem remains the stated open problem.

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

## R8 — Scientific status and significance

The observer scaling and Hölder structure use established kinetic and moment mathematics. Their precise application here is the resolved-versus-averaged number–energy diagnostic with an attained finite-range calibration envelope. The retained v15 susceptibility supplies the inverse and its conditioning. The comparison with previous Loop B identifies a population-sensitive channel rather than an alternative estimate of the same blackbody dipole.

The scalar sharp bound is established prior art through the exact Furuta specialization. The candidate for independent methods significance is its thermochemical propagation, resolved-versus-averaged observer response, and use with a specified instrument and noise model. Novelty must be assessed at that combined physical-inference level, alongside log-temperature distortion moments, blackbody mixing and relativistic gray-moment calibration. The companion literature review performs that comparison. No literature-wide absence claim is made here.

The source manuscript's global MB/FD theorem and massive rank-selection law are substantial retained results. Their publication strength depends on separating the particular velocity-dressed domain and sharp radial asymptotics from the established maximum-entropy/convex-duality mechanism.

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

The current completed unit supplies all three analytic response cases, sharp beam bounds, a reproducible finite check and a plot. Independent review is assigned by the parent. Source manuscripts, production namespaces, original DAG completion and remote repository state are unchanged.
