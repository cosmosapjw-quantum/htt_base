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
