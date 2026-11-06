# Theory and Observable Contracts for HTT R38

## 1. Conventions and congruences

Use metric signature (-,+,+,+). Let U^a be a specified future-directed unit timelike congruence, U^a U_a = -1, and h_ab = g_ab + U_a U_b. Define
\[
\mathcal A^a = U^b\nabla_b U^a,\qquad
\Theta=\nabla_a U^a,\qquad
\sigma_{ab}=D_{(a}U_{b)}-\tfrac13\Theta h_{ab},\qquad
\omega_{ab}=D_{[a}U_{b]} .
\]
Here D is the fully projected derivative. In a length-parameter convention, \(\Theta,\sigma_{ab},\omega_{ab},\mathcal A_a\) have dimensions length^{-1}. The decomposition is
\[
\nabla_b U_a=\tfrac13\Theta h_{ab}+\sigma_{ab}+\omega_{ab}-\mathcal A_a U_b.
\]
Physical quantities are H=c\Theta/3, \(\Sigma_{ab}=c\sigma_{ab}\), \(\Omega_{ab}=c\omega_{ab}\), and A_a=c^2\mathcal A_a. Thus H, Sigma and Omega have dimensions time^{-1}, A has acceleration dimensions, and A/(cH) is dimensionless.

The congruence is part of the physical model, not a coordinate choice. At minimum distinguish radiation frame R, matter frame M, and observer frame O. A velocity defined relative to one of these frames must never be relabelled as a geometric shear/tilt without an explicit response map.

## 2. Local optical Hubble law

For a smooth congruence and idealized emitters following the same congruence, with regular optical vertex, no caustic at the expansion point, and a well-defined observed direction n^a in the observer rest space, the leading local directional expansion is
\[
H_U(\mathbf n)=H_U-\frac{A_a n^a}{c}+\sigma_{ab}n^a n^b,\qquad
d_L(z,\mathbf n)=\frac{cz}{H_U(\mathbf n)}+O(z^2).
\]
All terms in H_U(n) have units s^{-1}; A·n/c has units s^{-1}. The sign of the acceleration term follows the chosen sourceward/observerward convention for n and must be locked by implementation tests. This is a local z→0 relation, not a finite-z Bianchi distance law.

For a finite-redshift survey, use shell-indexed coefficients rather than extrapolating the local law:
\[
H(z,\mathbf n)=H_0(z)+D_a(z)n^a+Q_{ab}(z)n^a n^b+\sum_{\ell\ge3}H_{A_\ell}(z)n^{\langle A_\ell\rangle}.
\]
Here Q_ab is STF and the expansion is a response/cosmographic parameterization until a dynamical model supplies its redshift evolution. Distance observables are fitted through a forward relation for D_L(z,n), D_A(z,n), redshift and source selection; they are not all equivalent to H(z,n).

At leading order in magnitude perturbations, a directional distance-modulus contrast maps to an apparent Hubble ratio as
\[
\Delta\ln H_F=-\frac{\ln 10}{5}\Delta m.
\]
This is a ratio/contrast. An additive magnitude intercept does not determine absolute H0. A physical local-Hubble sensitivity also needs finite-distance and response remainder control, plus the declared source-frame/time convention.

## 3. Full-sky STF2 normalization

Let h_2(n)=sigma_ab n^a n^b with sigma_ab symmetric trace-free. Isotropic angular averaging gives
\[
\langle n_i n_j n_k n_l\rangle
=\frac{\delta_{ij}\delta_{kl}+\delta_{ik}\delta_{jl}+\delta_{il}\delta_{jk}}{15},
\quad
\left\langle (h_2/H)^2\right\rangle
=\frac{2}{15}\frac{\sigma_{ab}\sigma^{ab}}{H^2}.
\]
Therefore
\[
\frac{\sigma:\sigma}{6H^2}=
\frac54\left\langle(h_2/H)^2\right\rangle.
\]
The associated full-sky reconstruction is
\[
\sigma_{ab}=\frac{15}{2}\left\langle h_2(n)
\left(n_an_b-\frac13\delta_{ab}\right)\right\rangle .
\]
The identity assumes full-sky uniform angular measure and exact STF projection. A mask, anisotropic noise, beam, pixel window or nonuniform selection changes the response and requires the explicit observation operator and covariance. Wolfram symbolic verification evaluated the difference between the two scalar normalizations to exactly zero. This is a symbolic normalization check, not an observed-data result.

## 4. Local boost, intrinsic dipole and global tilt

Use the project’s registered frame labels:
- beta_RO: radiation-observer relative velocity;
- beta_RM: radiation-matter relative velocity, treated as the global-tilt candidate only when a global matter/radiation frame model is specified;
- beta_MO: matter-observer relative velocity, the local observer boost.

At first order in small velocities,
\[
\boldsymbol\beta_{RO}=\boldsymbol\beta_{RM}+\boldsymbol\beta_{MO}+O(\beta^2).
\]
The second-order terms, including kinetic quadrupole and composition corrections, must be included whenever a beta^2 effect is compared with the low-ell quadrupole. Add a separate intrinsic radiation dipole d_int and, where relevant, the long-wavelength dipolar-potential/second-order initial-condition response. These are not aliases for beta_RM.

The local boost has characteristic signatures in CMB aberration, Doppler modulation and harmonic mode coupling, including T/E response and kinetic quadrupole. It also induces number-count modulation. With cumulative counts N(>S) proportional to S^{-x} and a power-law spectrum S_nu proportional to nu^{-alpha}, the idealized kinematic number-count dipole coefficient is [2+x(1+alpha)] beta; this formula is only valid under its declared flux-count and spectral-index assumptions and must be replaced by the actual catalogue selection operator.

A global tilt/shear model predicts a congruence-dependent and potentially redshift-dependent response across optical distances, VSH proper motions, radiation multipoles and source-count observables. A free intrinsic CMB dipole changes the CMB dipole carrier but does not generically reproduce all boost-induced aberration and cross-multipole responses. Some Doppler-like terms can be exactly degenerate under restricted second-order initial conditions; the likelihood must include that possibility rather than asserting that a single mode-coupling estimator solves the problem.

## 5. Joint response and identifiability

Write the retained observable vector schematically as
\[
y=\mathcal R_{\rm loc}\beta_{MO}
+\mathcal R_{\rm int}d_{\rm int}
+\mathcal R_{\rm global}\theta_{\rm kin}
+\mathcal N\eta+\epsilon,\qquad \epsilon\sim\mathcal N(0,C),
\]
where y may include CMB low-ell T/E/B harmonic coefficients or map-level summaries, radio/quasar flux- and redshift-binned count multipoles, SN/CF4 distance windows, BAO radial/transverse quantities, and Gaia VSH coefficients. The response blocks are different measurement operators, not interchangeable copies of one common dipole vector.

For a positive-definite covariance C and a full-column-rank nuisance design N, the nuisance-profiled precision is
\[
\Pi_N=C^{-1}-C^{-1}N(N^TC^{-1}N)^{-1}N^TC^{-1},
\qquad F=R^T\Pi_N R.
\]
For rank-deficient nuisance columns use a declared QR/SVD or Moore-Penrose construction, not a silent inverse. Equivalently, with C=LL^T, whiten y, N and R by L^{-1}, project onto the orthogonal complement of the whitened nuisance span, and inspect the singular values of
\[
R_{\rm id}=P_{\perp \tilde N}L^{-1}R.
\]
Only response directions with singular values stable to source, covariance, mask and truncation uncertainty are data-identifiable. A prior can regularize an identified posterior but cannot increase the data rank. Retain null vectors and condition numbers in the report.

The model comparison should use a common covariance and common nuisance support:
- M0: perturbed-FLRW + local observer boost + ordinary peculiar velocities/selection/foreground/calibration.
- M1: M0 + intrinsic CMB dipole and the allowed long-wavelength potential/second-order response.
- M2: M1 + global beta_RM and redshift-dependent STF kinematic tensors.
- M3: Bianchi-I or another family-specific dynamical restriction on M2, only when the family response/transfer is qualified.

A joint analysis must not multiply duplicate estimates from the same CMB sky. Planck SMICA/Commander/NILC processing products and WMAP observe the same primordial realization; their noise/foreground differences are useful but their cosmic-variance contributions are not independent. Likewise, multiple estimators made from the same catalogue are not independent data sets.

## 6. Five-variable tensorized framework: correct role

The established HTT state uses (x,Q,F,Pi,G_F) as a structured inference object:
- x: sample-by-functional carrier with typed ranks/parities and signed components;
- Q: anchor/gauge/margin information;
- F: support, pushforward and occupancy structure;
- Pi: source-measure exceedance law, not automatically a frequentist p-value;
- G_F: functional-depth/path representation.

These are not five independent experiments and must not be added as five likelihood factors. Scalar ratios are allowed only for eligible positive projections and only when the source measure and denominator are declared. Preserve original signed tensors, full covariance, fibre/null-space information and path outputs. Do not replace a joint tensor state by a single positive scalar score merely because it is easier to sample.

For the joint posterior, use the physical target vector
\[
\theta_{\rm kin}=(\Sigma/H,\ \Omega/H,\ A/(cH),\ \beta_{RM}),
\]
whose generic components are STF5 + axial-vector3 + polar-vector3 + relative-velocity3 = 14. Keep beta_MO as a separate local observer nuisance (3 components), and d_int as a separate radiation-dipole component (3 components). This count assumes one common declared triad/epoch and excludes additional redshift-history coefficients.

## 7. Low-ell morphology to radiation physics

Low-ell morphology must be computed from signed a_lm and explicit map/beam/mask response, not C_l alone. Alignments, parity ratios, hemispherical power and power tensors compress phase information differently; their covariance is not diagonal and they are not independent anomalies. Use BipoSH or equivalent off-diagonal harmonic response for anisotropy/boost tests; use null realizations preserving the actual mask, noise, beam, transfer and foreground-processing family.

A thermodynamic CMB temperature anisotropy map is not automatically a bolometric radiation-energy map. To infer radiation stress, reconstruct calibrated frequency-dependent specific intensity and integrate with the correct spectral response. The intensity moments J_<A_l> determine energy density, flux and anisotropic stress only after the frequency integral and frame are fixed. E/B harmonic coefficients are not bolometric intensity. Q/U frequency response and spin-2 convention must be carried separately. The existing 23D full polarized joint carrier and 20D circular-polarization-excluded carrier are theoretical/statistical response constructions; they are not a claim that all required physical polarization channels exist in the Planck archive.

The quadrupole radiation stress is directly related to the rank-2 intensity moment, while the shear response can depend on higher angular moments and Thomson gain/loss terms. An unpolarized or temperature-only reduction must be assigned an explicit omission-bias bound rather than treated as the same physics.

## 8. Bianchi classification contract

A Bianchi family label is a property of a spatially homogeneous geometry and its dynamical solution, not a local classification of one observed quadrupole. The family comparison must retain:
- Lie-algebra structure constants / invariant spatial frame and its automorphism freedom;
- spatial Ricci scalar and STF Ricci eigenstructure;
- electric/magnetic Weyl tensors;
- shear/vorticity evolution and Hamiltonian/momentum constraints;
- matter content, tilt, initial conditions and family-specific transfer/beam/polarization maps.

The existing design pack contains contracts for 11 families, not 11 fully implemented or validated Einstein-Boltzmann pipelines. Begin with Bianchi I response (where the Gaia VSH quadrupole comparator exists), then only add II/VII0 or V/VII_h when source-backed response templates and exact code are available. Scalar curvature or a shared principal axis alone is not a family identifier.

## 9. Falsifiable signatures and no-go outcome

- Local-boost support: independently inferred beta from CMB aberration/Doppler and selected, flux-binned radio/quasar dipoles agree after selection and calibration, and a common boost reproduces the expected harmonic coupling.
- Intrinsic-dipole support: a residual CMB dipole remains after the beta inferred from non-dipole boost response is fitted; it is stable across frequency/component separation and second-order nuisance alternatives.
- Global-tilt/shear support: one congruence and shared tensor history explain redshift-dependent SN/CF4 directional H, Gaia VSH, and CMB/number-count residuals with common axes and common covariance.
- Bianchi support: the restricted family predicts additional mutually linked spatial-curvature, Weyl and transfer signatures; matching only a quadrupole is insufficient.
- No-go: projected response rank is deficient, or nuisance/source/mask uncertainty spans the same columns. Return the identified quotient, null vectors, sensitivity envelope and upper limits; do not attribute a preferred axis to global geometry.

## 10. Implementation/validation boundary

Derived in this R38 design: local optical formula contract, STF2 normalization and full-sky projection, first-order frame-velocity decomposition, common linear response, nuisance-projected rank test. Literature-supported: observer boost mode coupling, Bianchi I VSH quadrupole, directional distance-dipole tests, covariant cosmography. Symbolically checked: STF2 normalization identity. Not run: actual data, nonlinear posterior, Boltzmann/Bianchi transfer, numerical coverage, end-to-end covariance and code implementation.