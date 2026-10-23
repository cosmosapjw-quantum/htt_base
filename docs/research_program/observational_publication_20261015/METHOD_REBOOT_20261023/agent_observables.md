# Solver-free observable methods and their admissible HTT interpretation

Prepared 2026-10-23. Scope: literature verification, mathematical derivations, and reusable statistical procedures. No ODE, Einstein–Boltzmann, ray-tracing, or substitute history was run. This note does not promote any L03/V03/B02/K03 gate.

> **Full-tuple scope clarification added by the coordinating author:** the notation below concerns the legacy scalar projection supplied to this subtask. The full tensor-functional/set/path definitions in `THEOREMS.md` T7, the July tensor plan and R9 revision 2 are primary. In particular Q may be an anchor gauge, F separates support/pushforward/occupancy, and the full G_F is a FunctionalDepthPath. This appendix does not redefine that richer framework.

## 1. Registered targets and the type boundary

The parent supplied the current definitions:

\[
x_C=\Sigma_G^2-W_G^2+\Omega_{\rm tilt}+\Delta\Omega_k,
\qquad Q=x_C/U_\sigma,\quad U_\sigma=\tfrac32B_\sigma^2>0.
\]

The shear, vorticity and Hubble normalization must refer to the same congruence. The registered shear contraction is \(\sigma_{ab}\sigma^{ab}/(6H^2)\), with \(H=\Theta/3\). The normalizer \(U_\sigma\) is a registered shear-sector MES normalizer, not a bound on the complete signed sum. \(F\) is the samplewise normalized sign-clean sector fraction only on its positive-ceiling and amplitude-admissible domain. It is not a volume fraction. \(\Pi_Q\) is a source-weighted tail functional with explicit unknown completion, not a null-hypothesis p-value. \(G_F=\max(F_c,\delta)/\max(F_r,\delta)\), with predeclared \(\delta>0\).

Use separate types \(\widehat h_{2,\mathrm{opt}}\), \(\widehat{\boldsymbol\mu}_{\mathrm{phot}}\), \(\widehat{\boldsymbol\beta}_{\mathrm{CMB,local}}\), and harmonic residual coefficients. They become physical HTT quantities only through a validated same-congruence response map, including selection, frame, calibration, finite-redshift remainder, and source provenance. A new algebraic name is not that map.

## 2. Primary literature and the methods it actually supports

### Planck, cross-spectra and foreground control

**P1. Planck 2018 IV, Diffuse component separation.** [Paper](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html), [arXiv:1807.06208](https://arxiv.org/abs/1807.06208), DOI [10.1051/0004-6361/201833881](https://doi.org/10.1051/0004-6361/201833881). OE differences chiefly trace instrumental noise; HM differences are more sensitive to long-time systematics. LFI's product called OE still uses half-ring splitting. Split maps require their additional unobserved-pixel masks. The 300 noise-plus-systematic realizations and 999 CMB-only realizations are distinct products. Fixed component-separation weights make propagation linear, permitting separate component propagation under those weights. The paper acknowledges simulation–data discrepancies at the few-percent level. This supports existing-data split diagnostics and conditional calibration, not a claim that every joint component/split product exists.

**P2. Planck 2018 VIII, Gravitational lensing.** [Paper](https://www.aanda.org/articles/aa/full_html/2020/09/aa33886-18/aa33886-18.html), DOI [10.1051/0004-6361/201833886](https://doi.org/10.1051/0004-6361/201833886). Its consistency-test discussion explicitly says there are no HM FFP10 CMB simulations in the 2018 release, only HM noise simulations. FFP9 and FFP10 use the same CMB seeds, but differ in weights and effective beams; beam differences affect low-lensing-multipole mean fields. Therefore sharing a seed is weaker than sharing the required observation operator. This directly corroborates L03's component-specific missingness.

**P3. Sheehy & Slosar (2018), No evidence for dust B-mode decorrelation in Planck data.** [arXiv:1709.09729](https://arxiv.org/abs/1709.09729), DOI [10.1103/PhysRevD.97.043522](https://doi.org/10.1103/PhysRevD.97.043522). The reanalysis identifies noise bias in cross-spectra between nominal splits, split-dependent systematic uncertainty, and correlation across sky patches. It is a concrete counterexample to treating all split cross-spectra as automatically unbiased.

**P4. Umiltà, Cardoso & Benabed (2019), The CMB angular power spectrum via component separation.** [arXiv:1807.00830](https://arxiv.org/abs/1807.00830), DOI [10.1051/0004-6361/201833758](https://doi.org/10.1051/0004-6361/201833758). Cross-only SMICA is a standard way to avoid the auto-noise bias under the cross-noise assumptions, but their Planck/simulation study still requires foreground-residual likelihood modelling and finds parameter shifts sensitive to it.

**P5. Elsner, Leistedt & Peiris (2017), Unbiased pseudo-Cℓ power spectrum estimation with mode projection.** [arXiv:1609.03577](https://arxiv.org/abs/1609.03577), DOI [10.1093/mnras/stw2752](https://doi.org/10.1093/mnras/stw2752). Removing templates and then taking a pseudo-spectrum produces a calculable projection bias. Their analytical correction is standard and does not require new cosmological-history integration. Deprojecting extra templates also removes signal components aligned with them.

**P6. Planck 2013 XXVII, Doppler boosting of the CMB.** [arXiv:1303.5087](https://arxiv.org/abs/1303.5087), DOI [10.1051/0004-6361/201321556](https://doi.org/10.1051/0004-6361/201321556). Aberration and modulation of small-scale anisotropies provide an independent test of a kinematic dipole; the reported dipole-direction component was 384±78(stat.)±115(syst.) km/s. Linearized intensity-derived temperature maps require the frequency-dependent modulation response \(b_\nu=x\coth(x/2)-1\), \(x=h\nu/(k_BT_0)\). This is an observer-at-one-event radiation-frame test, not a matter-tilt history measurement.

### Astrometry, frames and sources

**A1. Mignard & Klioner (2012), Analysis of astrometric catalogues with vector spherical harmonics.** [arXiv:1207.0025](https://arxiv.org/abs/1207.0025), DOI [10.1051/0004-6361/201219927](https://doi.org/10.1051/0004-6361/201219927). Complete E/B vector spherical harmonics separate rigid rotation (B1) and glide (E1). Masked/nonuniform samples require the actual design Gram matrix; continuum orthogonality is not sample orthogonality.

**A2. Gaia EDR3, The celestial reference frame (Gaia-CRF3).** [arXiv:2204.12574](https://arxiv.org/abs/2204.12574), DOI [10.1051/0004-6361/202243483](https://doi.org/10.1051/0004-6361/202243483). About 1.6 million QSO-like sources define the frame. The proper-motion systematics are about 12 μas/yr on scales above 15 degrees; radio–optical offsets for ICRF3 counterparts also remain. Sourcewise 2×2 errors alone therefore do not provide the complete covariance of a sky field.

**A3. Gaia EDR3, Acceleration of the Solar System from Gaia astrometry.** DOI [10.1051/0004-6361/202039734](https://doi.org/10.1051/0004-6361/202039734). Its measured E1 pattern has amplitude 5.05±0.35 μas/yr. This validates an observable acceleration/glide analysis under a specified frame and source treatment, not a universal separation of local and cosmological E1 fields.

**A4. Petrov & Kovalev (2017), Observational consequences of optical-band milliarcsecond-scale structure in AGN.** [arXiv:1704.07365](https://arxiv.org/abs/1704.07365). **Petrov, Kovalev & Plavin (2019), Quantitative analysis of Gaia DR2 versus VLBI.** [Author paper at NASA](https://ntrs.nasa.gov/citations/20190028777). Optical structure and flux variability can move the photocentre; the latter analysis finds a strong jet-alignment signature in offsets and significant proper motions. Improving positional precision does not make optical and radio centroids identical matter markers.

**A5. Quercellini et al. (2009), Cosmic parallax as a probe of late-time anisotropic expansion.** [arXiv:0905.4853](https://arxiv.org/abs/0905.4853), DOI [10.1103/PhysRevD.80.063527](https://doi.org/10.1103/PhysRevD.80.063527). **Fontanini, West & Trodden (2009), Can cosmic parallax distinguish between anisotropic cosmologies?** DOI [10.1103/PhysRevD.80.123515](https://doi.org/10.1103/PhysRevD.80.123515). These are actual model-dependent forecasts/comparisons. They motivate angular-drift observables but do not supply the missing HTT family atlas.

### Covariant cosmography and current empirical comparators

**C1. Heinesen (2021), Multipole decomposition of the general luminosity-distance Hubble law.** [arXiv:2010.06534](https://arxiv.org/abs/2010.06534), DOI [10.1088/1475-7516/2021/05/008](https://doi.org/10.1088/1475-7516/2021/05/008). A smooth emitter/observer congruence, regular optical vertex, and locally invertible redshift–affine-parameter relation allow a general low-redshift expansion without assuming field equations or a metric family. The timelike-congruence shear and null optical shear are different tensors. Finite-order distance coefficients alone do not reconstruct the full spacetime.

**C2. Maartens et al. (2024), Covariant cosmography: observer-dependence of the Hubble parameter.** [arXiv:2312.09875](https://arxiv.org/abs/2312.09875), DOI [10.1088/1475-7516/2024/09/070](https://doi.org/10.1088/1475-7516/2024/09/070). In their geodesic-dust setting the intrinsic local Hubble field has monopole plus quadrupole; a local observer boost generates a dipole involving both Hubble expansion and shear. Luminosity distance must receive the correct boost treatment; using \(d_L/(1+z)^2\) gives the area-distance transformation. A moving observer at one event does not define a global boosted congruence.

**C3. Heinesen & Korzyński (2024), Exploring geometrical information in cosmic drift signals.** [arXiv:2406.06167](https://arxiv.org/abs/2406.06167), DOI [10.1103/PhysRevD.110.043525](https://doi.org/10.1103/PhysRevD.110.043525). Joint position drift, redshift drift and distance cosmography is a constructive way to add independent geometric information. Regional kinematic and tidal terms matter; finite-distance source drift is not simply a local velocity-gradient tensor.

**C4. Kalbouneh et al. (2026), The anisotropic expansion rate of the local Universe and its covariant cosmographic interpretation.** [arXiv:2510.02510v2](https://arxiv.org/abs/2510.02510v2), DOI [10.1088/1475-7516/2026/03/084](https://doi.org/10.1088/1475-7516/2026/03/084). Using CF4 and Pantheon+ over 0.01<z<0.1, they measure expansion-field multipoles and interpret them with covariant cosmography. Low-redshift fluctuation dipole amplitude is about 0.022±0.0015; quadrupole and low-redshift octupole are also present. Their interpretation assigns a strong Hubble quadrupole plus deceleration multipoles, rather than identifying every measured finite-bin multipole with a point-local Hubble coefficient. The paper explicitly studies angular sampling, flux selection and grouped tracers.

**C5. Stiskalek, Desmond & Lavaux (2026), No evidence for local H0 anisotropy from Tully–Fisher or supernova distances.** [arXiv:2509.14997v2](https://arxiv.org/abs/2509.14997v2), DOI [10.1093/mnras/staf2048](https://doi.org/10.1093/mnras/staf2048). Their z<0.05 forward model jointly calibrates distance relations, marginalizes distances and includes reconstructed peculiar velocities. CF4 and Pantheon+ still show zero-point dipoles equivalent to 4.1±0.9% and 2.3±0.6% in H. A flexible radially varying velocity dipole accounts for those features without requiring anisotropic expansion; the inferred bulk-flow curve agrees with standard-model expectations. Thus their null conclusion concerns interpretation after a larger nuisance model, not absence of a raw dipole.

**C6. Bendtsen, Heinesen & Koksbang (2026 preprint), Cosmography for a general spacetime centred at arbitrary redshift.** [arXiv:2608.07008v1](https://arxiv.org/abs/2608.07008v1), submitted August 7, 2026. General-redshift expansions and two LTB test cases show that fitted finite-range coefficients can become effective quantities rather than point-local geometric quantities. This supports explicit finite-redshift remainder control; it supplies no HTT-specific bound for that remainder.

**C7. Clarkson & Maartens (2026 preprint), Beyond dust in local cosmography: covariant kinetic theory.** [arXiv:2610.04284v1](https://arxiv.org/abs/2610.04284v1), submitted October 3, 2026. Velocity dispersion and pressure gradients in collisionless matter can generate matter-frame acceleration and an intrinsic Hubble dipole, with acceleration curl sourcing vorticity. Therefore C2's dipole-to-boost interpretation must retain its dust/geodesic assumptions. This new preprint is a theoretical generalization, not an empirical calibration of quasar photocentres.

**C8. Saadeh et al. (2016), A framework for testing isotropy with the CMB.** [arXiv:1604.01024](https://arxiv.org/abs/1604.01024), DOI [10.1093/mnras/stw1731](https://doi.org/10.1093/mnras/stw1731). Their scalar/vector/tensor Bianchi VIIh analysis uses physical shear-mode evolution and photon Boltzmann transfer, including T/E/B. The related [PRL](https://doi.org/10.1103/PhysRevLett.117.131302) bounds are family-, evolution-, and prior-dependent. These methods are the appropriate comparator for B02, but their published bounds are not a replacement for the absent all-m T/E/B HTT history-response atlas.

## 3. The split-null kernel theorem and its constructive use

This section is a direct algebraic derivation, not a claimed new literature result. At a fixed common beam/mask/weight operator, let maps be

\[
d_s=c+f_0+\Delta f_s+n_s,\qquad s=1,\ldots,k.
\]

Here c is the desired common sky and f0 a common foreground/residual component. Stack the splits and let D be any contrast matrix satisfying D1=0. Then

\[
(D\otimes I)d=(D\otimes I)(\Delta f+n).
\]

**Proof and impossibility statement.** For every sky vector g, adding \(1\otimes g\) to all maps leaves the contrast unchanged. Thus the complete contrast data have the common-mode subspace in their kernel. No bound on \(\|f_0\|\) follows from contrast amplitudes alone without an additional restriction linking common and differential contamination. The obstruction is exact, not a lack of Monte Carlo power.

For two splits, \(d_+=(d_1+d_2)/2\) contains \(c+f_0\), whereas \(d_-=(d_1-d_2)/2\) does not. A cross-spectrum satisfies, for zero-mean noises uncorrelated with the sky,

\[
E[d_1d_2^\dagger]
=E[(c+f_0+\Delta f_1)(c+f_0+\Delta f_2)^\dagger]
+N_{12}.
\]

It removes the auto-noise term only if the appropriate cross-noise covariance is zero or subtracted; it retains common-foreground power and any CMB–foreground cross terms. Frequency leverage, external templates, beam knowledge and joint processing can constrain these terms; differencing alone cannot.

If a statistic combines FULL/HM/OE maps, its covariance is computed from their joint block covariance. Concatenating separately valid marginal simulations does not identify cross-block covariance. An independent re-pairing changes the simulated experiment. Shared CMB seeds but unequal beams change the response as well. Preserve the eight actual paired source rows and the known missing fields; do not fill missing HM CMB with a copied FULL map or an FFP9 product labelled FFP10.

**Obtainable now:** common-mask split maps and cross-spectra; mask/beam matched pipeline differences; spectral residual coefficients with analytical deprojection-bias correction; diagnostic sensitivity to a declared common-mode foreground basis. These improve observable constraints while leaving L03's full-joint calibration unfulfilled.

## 4. Simulation-independent nuisance envelopes: honest conditional alternatives

Take a linear observable coefficient \(\hat a=w^Ty\), a declared physical/phenomenological mean \(E[y]=Ra+Tb+r\), and a target contrast with \(w^TR=1\). If \(\|b\|\le B\) and \(\|r\|\le\varepsilon\), Hölder's inequality gives

\[
|E\hat a-a|\le B\|T^Tw\|_*+\varepsilon\|w\|_*=:b_{\max}.
\]

With known Gaussian scalar variance \(s^2=w^TCw\),

\[
[\hat a-b_{\max}-z_{1-\alpha/2}s,\ \hat a+b_{\max}+z_{1-\alpha/2}s]
\]

has at least \(1-\alpha\) coverage uniformly over the declared bias set. Proof: on \(|w^T\epsilon|\le z s\), the triangle inequality contains the target. Gaussianity is unnecessary if a valid noise-tail bound replaces z s. For ellipsoidal b, its support function supplies a closed-form bias radius. Projecting T out can set the represented bias to zero but may destroy signal rank; it does not bound r outside span(T).

For a residual vector and a known norm ball \(\|r\|\le\rho\),

\[
(\|v\|-\rho)_+\le\|v-r\|\le\|v\|+\rho.
\]

These deterministic bounds require no simulations. An unbounded common foreground along the signal direction makes \(b_{\max}=\infty\): the honest interval is then uninformative. A chosen B or rho is a sensitivity parameter, not an empirically established envelope. A covariance family with no coverage guarantee cannot certify coverage merely by scanning many choices.

Standard primary comparators are [Armstrong & Kolesár 2021, DOI 10.3982/QE1609](https://doi.org/10.3982/QE1609), which treats bias-aware inference under bounded moment misspecification, and [Berger & Boos 1994, DOI 10.1080/01621459.1994.10476836](https://doi.org/10.1080/01621459.1994.10476836), which provides \(p_{BB}=\min(1,\sup_{\eta\in C_{1-\gamma}}p_\eta+\gamma)\). The latter requires valid fixed-nuisance p-values and a nuisance confidence set with actual coverage; it does not manufacture them from unavailable simulations.

## 5. Full proof: local Hubble quadrupole to normalized timelike shear

Use metric signature (−+++), sourceward unit vector n in the local rest space, physical proper time, and SI-compatible kinematic rates. Let H=Theta/3 in s−1, S_ab=sigma_ab in s−1, and A_a the physical four-acceleration's spatial components in m/s². The local directional coefficient is

\[
h(n)=H-\frac{A_an^a}{c}+S_{ab}n^an^b,
\qquad d_L(z,n)=\frac{cz}{h(n)}+O(z^2).
\]

This follows by contracting the covariant velocity-gradient decomposition with the null direction. The antisymmetric vorticity contraction vanishes because \(n^an^b\omega_{ab}=0\). Acceleration contributes an odd dipole; the symmetric trace-free shear contributes the quadrupole. The statement concerns the same smooth congruence followed by source and observer, before or after an explicitly correct observer-boost treatment. It does not equate an arbitrary finite-z fitted expansion field with h.

Define \(h_2(n)=S_{ab}n^an^b\) and normalized full-sky average \(\langle f\rangle=(4\pi)^{-1}\int f\,d\Omega\). Rotational invariance and index contraction give

\[
\langle n_an_b\rangle=\delta_{ab}/3,\qquad
\langle n_an_bn_cn_d\rangle=
\frac{\delta_{ab}\delta_{cd}+\delta_{ac}\delta_{bd}+\delta_{ad}\delta_{bc}}{15}.
\]

The fourth-moment coefficient is 1/15 because summing a=b and c=d makes the left side one and the three contractions total 15. Consequently

\[
\langle h_2^2\rangle
=\frac{(\operatorname{tr}S)^2+2\operatorname{tr}(S^2)}{15}
=\frac{2}{15}S_{ab}S^{ab},
\]

and therefore

\[
\boxed{\frac{\sigma_{ab}\sigma^{ab}}{6H^2}
=\frac54\left\langle\left(\frac{h_2}{H}\right)^2\right\rangle.}
\]

The tensor can also be recovered directly:

\[
S_{ab}=\frac{15}{2}\left\langle h_2(n)
\left(n_an_b-\frac{\delta_{ab}}3\right)\right\rangle.
\]

With orthonormal spherical harmonics \(\int|Y_{2m}|^2d\Omega=1\), this becomes \(\sigma_{ab}\sigma^{ab}=15\sum_m|h_{2m}|^2/(8\pi)\). Real and complex conventions must be declared; double-counting conjugate modes is not allowed. On a cut sky use an explicit full-sky coefficient estimator/response, not an uncorrected mean over observed directions.

### Finite-z and uncertainty transport

Suppose a simultaneous confidence event provides \(\|\hat h_2-h_2\|_{L^2(d\Omega/4\pi)}\le\epsilon\) and \(0<H_-\le H\le H_+\). Epsilon includes statistical coefficient error, finite-redshift truncation, source/observer boost, calibration and selection leakage, or those terms are separately declared as deterministic sensitivities. Let \(r=\|\hat h_2\|_{L^2}\). Reverse and ordinary triangle inequalities imply

\[
\boxed{
\frac{\sqrt5}{2H_+}(r-\epsilon)_+
\le\sqrt{\frac{\sigma_{ab}\sigma^{ab}}{6H^2}}
\le\frac{\sqrt5}{2H_-}(r+\epsilon).}
\]

Squaring preserves these nonnegative bounds. If the joint input event has probability at least 1−alpha, this nonlinear image has at least the same coverage. Independence between H and coefficients is not required. If marginal events are used, the union bound gives at least 1−alpha_H−alpha_h; a falsely independent product must not be used. Unknown finite-z remainder cannot be silently set to zero. A statistical interval conditional on epsilon is distinguishable from an empirically calibrated interval for the local tensor.

For coefficients q in a declared orthonormal real l=2 basis, an ellipsoid \((q-\hat q)^TV^{-1}(q-\hat q)\le c_\alpha\) gives \(\epsilon_{\rm stat}\le\sqrt{c_\alpha\lambda_{\max}(V)/(4\pi)}\). Add justified deterministic L2 radii by the triangle inequality. This yields an implementable closed-form conservative interval without solving a physical history.

**Interpretation:** this can identify the registered shear contraction only after same-congruence validation. The leading Hubble coefficient remains blind to W_G², and measures neither Omega_tilt nor DeltaOmega_k. It cannot yield full x_C from shear alone. Its optical-only product should remain separately typed.

## 6. Astrometric invariants, conditional rank and validity

For source directions n_i and tangential measured proper motions mu_i, \(d(n_i\cdot n_j)/dt=\mu_i\cdot n_j+n_i\cdot\mu_j\). Adding a common frame spin \(\Omega\times n_i\) changes the right side by zero because the scalar triple products cancel. Thus pairwise angular-separation drift is exactly invariant under a common rigid rotation. It does not cancel an E1 glide \((I-nn^T)g\), source-dependent photocentre motion, angular correlated calibration errors, or finite-distance optical effects. O(N²) pairwise quantities are not O(N²) independent measurements; their covariance is the pushforward of the source covariance and is singular/redundant.

In the instantaneous local kinematic limit, a symmetric trace-free local velocity gradient S produces

\[
\mu_S(n)=(I-nn^T)Sn=\tfrac12\nabla_{S^2}h_2(n),
\qquad \langle|\mu_S|^2\rangle=\tfrac15\operatorname{tr}(S^2)
=\tfrac32\langle h_2^2\rangle.
\]

The norm identity follows from \(\langle n^TS^2n\rangle=\operatorname{tr}(S^2)/3\) minus the fourth moment above. This is a constructive **conditional consistency test**, not a formula for all finite-distance Gaia sources. Photon-path, source motion and observer terms require C3's optical response. A B1 spin or optical jet drift is not W_G².

For the local boosted geodesic-dust Hubble observable in C2, with beta=v/c, the leading dipole d obeys

\[
d=-2(HI+S)\beta+O(\|\beta\|^2).
\]

If \(M=HI+S\) is invertible, the first-order algebraic estimate is \(\hat\beta=-M^{-1}d/2\). This expression keeps all orders in the *shear matrix* while remaining first order in velocity. A local-rank statement does not certify small beta. A necessary admissibility inequality on a predeclared \(\|\beta\|\le\epsilon_\beta\) domain is

\[
\|d\|\le 2\epsilon_\beta\|M\|_{op}+r_d,
\]

where r_d must bound noise, nuisance and the neglected nonlinear remainder. Failure excludes the declared small-velocity working domain, not all physical cosmologies. Passing is only necessary. If the formal K03 estimate lies outside that domain, report the rank and invalid formal estimate separately; clipping the estimate or assigning its Gaussian error bar does not restore validity. For nongeodesic matter, the intrinsic acceleration dipole must also be included, and its degeneracy with the boost may destroy identification.

The existing A22-05 archive illustrates why this matters: duplicated local/cosmic E1 columns have rank three, and B1 retains frame-spin degeneracy. Its declared correlated-nuisance simulations had severely poor coverage when omitted l4 fields or template-correlated means were injected. Enlarging an observable quotient can be legitimate; transferring its conditional rank to physical K03 acceptance is not.

## 7. From valid intervals to the tensorized targets

Let a physically validated same-source joint set imply \(x_{C,i}\in[x_i^-,x_i^+]\). For fixed registered positive \(U_{\sigma,i}\), set \(q_i^\pm=x_i^\pm/U_{\sigma,i}\). If only shear is bounded and the remaining signed terms are unbounded, these x intervals are unbounded: no finite Q claim follows. If U_sigma is uncertain, bound the ratio over its **joint** positive-domain set; do not divide by a fitted central value.

With fixed nonnegative weights p_i, known sources K, unknown normalized mass u, and strict exceedance Q>t,

\[
\sum_{i\in K}p_i\mathbf1(q_i^->t)
\le\Pi_Q(t)\le
\sum_{i\in K}p_i\mathbf1(q_i^+>t)+u.
\]

These are safe outer bounds; joint coupling can tighten them. A boundary at q_i^-=t is not guaranteed exceedance. Weights must preserve normalized joint source IDs, and unknown mass is not renormalized away. Conditional simultaneous input confidence pushes through to simultaneous tail bounds, without turning Pi into a null p-value.

On the positive-ceiling, amplitude-admissible domain, suppose joint analysis yields \(F_r\in[L_r,U_r]\) and \(F_c\in[L_c,U_c]\). Monotonicity gives the safe box bound

\[
\frac{\max(L_c,\delta)}{\max(U_r,\delta)}
\le G_F\le
\frac{\max(U_c,\delta)}{\max(L_r,\delta)}.
\]

The floor must be frozen before seeing the comparison. Source, sky, selection and normalization covariance remain in the joint set; overlapping catalogues are not independent repetitions. This transport changes no F definition and does not authorize F outside its admissible sector.

## 8. What the recent empirical disagreement teaches

The following is an inference from C4–C6, not a claim that either analysis has resolved the other's model. Kalbouneh et al. and Stiskalek et al. both find directional structure. They differ in redshift range, tracer subsets, observable parametrization, calibration/velocity model, and what is interpreted as anisotropic expansion. A finite-bin fluctuation multipole, a magnitude zero-point dipole, a point-local Hubble tensor and a global anisotropic history are distinct estimands. Comparing their quoted percentages as if they were the same tensor would be invalid.

An available-data comparison should freeze a shared source-ID subset, covariance and frame convention, then compare (i) radial-bin multipole estimates, (ii) joint calibration with a flexible radial dipole, and (iii) cosmographic order/range sensitivity. The stable outputs are joint observable coefficients and their stated response assumptions. Cosmography can avoid a prespecified metric family, but its finite-range fit does not evade approximation, tracer, or calibration assumptions. No published external point estimate should be inserted into x_C as if it were a joint HTT source sample.

## 9. Concrete work that advances the four gates without mislabelling completion

| Gate | Existing-input analysis available without a new physical solver | Product type | Remaining qualification |
|---|---|---|---|
| L03 | Reuse paired maps; common masks/beams; split nulls, cross-spectra, deprojected coefficients and common-mode sensitivity radii | Observable residual constraints with a declared covariance/bias set | Same-realization all-component FULL/HM/OE/source coverage remains absent; HM FFP10 CMB and FFP9 beam gap retained |
| V03 | Joint dipole/aberration/modulation consistency; frame-correct distance multipoles; possible local beta comparison | Local observer/radiation and local observer/tracer quantities | Original external global tilt history and calibrated global response remain required |
| B02 | Fit generic all-m T/E/B harmonic coefficients, corrected template projections, rotation-invariant summaries | Phenomenological anisotropy invariants | Full physical family/history atlas and joint transfer response remain required |
| K03 | VSH nuisance quotient, pairwise spin-invariant drift, joint source covariance sensitivity, explicit small-velocity-domain inequality | Conditional astrometric experiment and validity test | Source congruence, optical/radio centroid response, cross-source errors and finite-validity calibration remain required |

The new mathematical deliverables are the exact split common-mode kernel result, norm-bounded nuisance intervals, a full shear-from-Hubble-quadrupole proof with nonlinear confidence transport, pairwise frame-spin cancellation, and a small-velocity admissibility inequality. None requires claiming unavailable histories have been supplied.

## Retrieval notes for parent citation reuse

All references above were checked using SciSpace, Exa and web retrieval on 2026-10-23. Exact web references useful to reopen: Planck missing HM CMB turn111search12; Planck boost turn114search7; Gaia-CRF3 turn108search20/turn117search3; Gaia acceleration turn117search4; Heinesen full equations turn113view0; Maartens boost equations turn113view1; Kalbouneh current abstract turn119view1 and full text turn121view1; Stiskalek abstract turn119view0 and full text turn121view0; arbitrary-z preprint turn119view2; beyond-dust preprint turn119view3. Source-specific summaries were kept brief; derivations are supplied explicitly as this note's mathematical reasoning.
