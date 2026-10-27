# From sky morphology to measurable geometry

## Five internal theory loops

**Internal research report · 26 October 2026**

This report develops five questions inherited from the HTT legacy programme: how low-order sky morphology constrains physical fields; how a dipole separates observer motion from intrinsic radiation structure; which beyond-FLRW kinematic quantities optical observations can measure; what distinguishes homogeneous anisotropic geometries; and what a direction-dependent Hubble factor means at finite redshift.

The organizing idea is to preserve the tensor response between these layers. Temperature multipoles, bolometric stress, congruence shear and spatial curvature can share angular patterns while representing different physical quantities. An explicit response, its derivative terms and its uncertainty map determine which inference is available. The five chapters construct these interfaces using finite algebra, relativistic transport identities and local optical expansions.

## What the legacy intuition becomes

The legacy intuition that a low-order sky pattern carries geometric information remains productive. Its precise form is a sequence of maps:
\[
\text{calibrated intensity/distance/drift}
\longrightarrow \text{joint angular coefficients}
\longrightarrow \text{physical response image}
\longrightarrow \text{compatible geometric states}.
\tag{S1}
\]
Each arrow has its own source and frame. A temperature quadrupole becomes a stress tensor only after the spectral weighting is specified. A stress tensor constrains shear through its transport equation, including its time/spatial derivatives. A measured velocity-gradient tensor constrains a Bianchi state through curvature and matter constraints. Retaining those arrows turns morphology into an explicit physical question.

The five results below are internal conditional derivations. They supply quantities to estimate and consistency relations to test. They are not new fits to the CMB, CF4 or quasar catalogues.

| Loop | Main construction | Physical interpretation | Additional application input |
|---|---|---|---|
| A | Positive five-dimensional radiative shear operator and perturbation bound | Anisotropic radiation responds to differential expansion through more than its quadrupole axis | Bolometric moments, derivative/flux terms and their joint errors |
| B | \(K-(aa)_{\rm STF}=Q_{\rm intr}-(dd)_{\rm STF}\) | The dipole and quadrupole share boost terms that can be removed algebraically | Intrinsic-quadrupole bound or independently calibrated velocity response |
| C | Joint radial/proper-motion response of rank 12 | Expansion, shear, acceleration and vorticity occupy distinct angular sectors | Common congruence, distances, clock and reference-frame spin |
| D | Matched II/VII\(_0\) initial data with different Ricci spectra | Scalar curvature and local expansion do not exhaust homogeneous geometry | STF spatial curvature or suitable Weyl/derivative information |
| E | Distance-jet image and curvature–history combination | Directional Hubble ratios, derivatives and local expansion separate at finite redshift | Joint distance coefficients, calibration and finite-distance remainder |

## A common tensor state, with units retained

Use a unit timelike field \(u\), signature \((-+++)\), and proper-length differentiation. The geometric rates \(\Theta,\sigma,\omega,A\) have inverse-length units. Their physical rates are \(c\Theta,c\sigma,c\omega,cA\); physical acceleration is \(c^2A\). Loop C writes \(h=c\Theta/3\), \(S=c\sigma\), \(v=c\omega\), \(\alpha=cA\). Loops A, D and E use geometric rates unless explicitly converted.

At one event, a convenient carrier can include
\[
x=(\Theta,\sigma_{ab},\omega_a,A_a,\rho_\gamma,q_a,\pi_{ab},
{}^{(3)}R_{ab},\text{specified derivative jets}).
\tag{S2}
\]
This is a list of possible coordinates, not a claim that one data set measures every component. The tensorized construction acts on the jointly compatible subset. If a response leaves a kernel, retain that kernel or restrict to an identifiable functional.

The notation \(F\) has three actual uses in the source history. We distinguish directional support utilization \(F_{\rm sup}\), certified ceiling utilization \(F_{\rm cert}=x_C/U\), and an explicitly measured occupancy \(F_\nu\). The legacy certified diagnostic is not a material-volume fraction. \(Q\) is a gauge relative to a stated body; \(\Pi\) needs an actual statistical law; \(G_F\) needs the declared depth/transport coupling. These distinctions make the framework usable across different observables without changing their meaning.

## A physical reading of the five calculations

**Radiation and shear.** In Loop A, the relevant object is an operator on all five shear components. Its energy form is positive for a positive radiation intensity with adequate angular support. The smallest eigenvalue measures how much a shear perturbation changes the radiation transport residual. This gives a stability scale, not merely an alignment statistic. The fourth radiation moment enters the response, and temperature nonlinearities can create stress even when a temperature quadrupole is absent.

**Dipole structure.** In Loop B, \(a\) is the measured first-order temperature dipole, \(d\) an intrinsic radiation dipole and \(b\) observer velocity in units of \(c\). The relation \(a=b+d\) alone cannot separate them. The second-order quadrupole supplies a closure tensor. A frequency-curvature term built only from the same blackbody dipole does not create an independent velocity channel. A calibrated aberration/modulation response can add that channel, subject to its actual covariance and competing physical responses.

**Local motion.** In Loop C, radial redshift slopes see the trace, STF symmetric part and acceleration dipole. Proper motions add the transverse shear and antisymmetric rotation. The two shear estimates can be compared as a closure test. A rotation of the observing triad occupies the same B1 sector as physical vorticity, so its calibration has direct physical meaning. The common-congruence acceleration cancellation explains why nearby material tracers and distant quasar reference objects require different response models.

**Homogeneous geometry.** In Loop D, the spatial commutators determine curvature through the connection. Their Jacobi constraint is part of the physical family. Matching scalar curvature and local expansion leaves room for different anisotropic curvature tensors. The constructed II/VII\(_0\) pair makes that freedom explicit. Conversely, flat I and flat VII\(_0\) can be different homogeneous presentations of the same local Euclidean geometry. Classification should therefore specify both its geometric equivalence relation and the measurements that distinguish the surviving classes.

**Directional expansion.** In Loop E, the first optical coefficient measures \(c(\Theta/3+\sigma:nn-A\cdot n)\). At higher redshift, angular drift, ray derivatives and focusing enter. The Kasner calculation exposes these effects in a genuine Ricci-flat spacetime. It provides a concrete example of why a direction-dependent apparent deceleration cannot automatically be interpreted using an isotropic matter-density formula.

## Short research paths enabled by these results

The most useful next calculations are small, response-specific and reuse existing assets.

1. **Radiative moment conversion.** Extend the retained bandpass response to a joint bolometric moment region. Evaluate the five-dimensional operator eigenvalues over that region and report the derivative residual required for a chosen shear bound. This can produce a quantitative sensitivity result before a complete history inversion is available.
2. **Dipole closure.** Form the tensor \(K-(aa)_{\rm STF}\) with a shared calibration and noise model. Scan an explicit intrinsic-quadrupole envelope and compare the resulting necessary dipole bounds with an independent aberration velocity channel.
3. **Radial–transverse shear closure.** In a source population with a defensible common response, compare normalized radial STF2 and transverse E2 coefficients. Include shared distance errors and frame spin in the same joint model.
4. **Geometric compatibility.** Push the resulting kinematic region through Gauss–Codazzi constraints. Report compatible curvature tensors and family intersections; seek a derivative or Weyl observable that separates the II/VII\(_0\) witness.
5. **Finite-redshift Hubble coefficients.** Fit the first two optical coefficients over declared windows. Add a cubic coefficient only where supported, then constrain \(h_2+h_0R_{KK}/2\). Carry a finite-distance remainder into any reciprocal Hubble map.

These paths can advance independently. A missing full-population selection law blocks that particular population claim; it need not block a selected-cohort result, an algebraic theorem, or a design calculation with explicitly stated inputs. The original external-history acceptance remains a separate target.

## Calculation and literature record

Wolfram Language checked finite spherical integrals, Lorentz expansions, response ranks, homogeneous curvature, distance-series inversion and a metric-to-Ricci Kasner calculation. xAct/xTensor 1.3.0 checked the null velocity-gradient contraction and the quadratic contraction
\[
B_{ab}B^{ba}=\Theta^2/3+\sigma_{ab}\sigma^{ab}
-\omega_{ab}\omega^{ab}.
\tag{S3}
\]
The latter is the quadratic kinematic term that enters the Raychaudhuri derivation; the check itself is algebraic. The external permutation executable failed on the first attempted canonicalization, so the successful xAct runs used its Wolfram permutation implementation. Failed and repaired receipts remain separate.

The official xAct archive matched the supplied archive's SHA-256, 7a6c5f600868a3922668b020a15c0692f76574ff2a559808c62d460cef1b07be. The Wolfram kernel reported version 15.0.1 during the setup check. No new Boltzmann solver or numerical ODE integration was run.

The attached Ellis–Maartens–MacCallum and Cercignani–Kremer texts supplied geometric and kinetic conventions. Wager's supplied 2026 draft informed the selected-data moment construction; the supplied Polyanskiy–Wu text supplied the information/sufficiency interpretation. SciSpace and Exa were used for discovery, followed by primary papers for formula checks. Chapter references identify the relevant equations and attachment page numbers.

The current repository pin is a55036ad09c53a9215dee3282e425d37cfb95443. The source audit enumerated 559 accessible PR metadata records and 297 branches, acquired 114 selected files, and directly read 21 bounded scientific/code units in addition to the loop-specific sources. It reused a 26-family historical synthesis. This is a complete accessible metadata inventory with targeted scientific rereading, not a claim that every proof in every historical branch was reread. The detailed inventory and source pins accompany the report.

One independent reviewer checked the five derivations and targeted repairs. The report's claims remain at their stated conditional-theory level. Repository, controller and original 42-node completion states were not changed. No push was performed.
