# R39 theory synthesis: six loops converging on tensor-valued x

## Common conventions

Metric signature (-,+,+,+). Keep c explicit in optical equations. A congruence must be identified by its 4-velocity, tetrad, epoch/window, spatial basis and averaging prescription. Dimensionless beta is used only for frame velocities.

The common latent state is Z=(Z_phys,Z_obs,eta,A,R). The primary HTT estimand is the typed x[s,alpha]=phi_alpha(Z_s) bundle. Its functional output spaces can be polar V1, axial V1, STF2 even/odd, spin-weighted harmonic spaces, or scalar invariants. It is not the legacy scalar x_C. Full application and functional registry are in VECTOR_TENSOR_X_FRAMEWORK.md.

For velocities beta_a and beta_b measured in a common inertial frame S, the velocity of A in the standard-boost axes of B is

\[
\beta_{A|B}=
\frac{\beta_a-\gamma_b\beta_b+
(\gamma_b-1)(\beta_a\cdot\beta_b)\beta_b/\beta_b^2}
{\gamma_b(1-\beta_a\cdot\beta_b)},\quad
\gamma_b=(1-\beta_b^2)^{-1/2}.
\]

This is the two-frame pure-boost convention. Non-collinear compositions may induce Wigner rotation. The R39 code correction implements this two-velocity transform; the three physical variables beta_RO, beta_RM, beta_MO still require an ordered tetrad/boost contract. The existing beta_MO=beta_RO-beta_RM assignment is only first-order and must not be advertised as exact.

For a smooth congruence, use the declared 1+3 decomposition, with all normalization choices stated at each API boundary. A local optical coefficient for sourceward direction n has the form

\[
{\cal H}_u(n)=H_u-\frac{A_u\cdot n}{c}+\sigma_{u,ab}n^an^b,\qquad
d_L(z,n)=\frac{cz}{{\cal H}_u(n)}+O(z^2),
\]

under a regular optical vertex, locally invertible redshift and a consistent emitter/observer congruence. The sign assumes n points from observer to source. The antisymmetric vorticity term vanishes in n^a n^b at this order. This local expansion is not a finite-z model.

## T1. Low-ell morphology to physical radiation observables

The low-ell output is a typed set of signed carriers, not merely C_l:
- a_lm^T, a_lm^E, a_lm^B with spin/parity conventions;
- STF quadrupole T2 and octupole T3;
- phase, multipole-vector, planarity and parity functionals;
- off-diagonal covariance/BipoSH A^{LM,XY}_{ell ell'}.

The general covariance can be represented as

\[
\langle a_{\ell m}^X a_{\ell' m'}^{Y*}\rangle
=\sum_{LM}(-1)^{m'}A_{\ell\ell'}^{LM,XY}
C_{\ell m,\ell' -m'}^{LM}.
\]

A boost induces characteristic L=1 off-diagonal couplings, especially ell to ell±1. Doppler modulation and aberration are similar but not identical. Polarization requires spin-weighted transfer and T/E/B parity. Map processing is a real operator:
\[
d_\nu={\cal P}_\nu{\cal B}_\nu{\cal M}_\nu{\cal S}_\nu a+n_\nu.
\]
Bandpass, intensity-to-temperature conversion, beam/pixel windows, mask, component separation, calibration and split noise are part of this operator. Planck PR3/PR4 processing products share the same sky and are not independent realizations.

Existing prior art includes Planck boost estimators, BipoSH inference, intrinsic-dipole constraints and masked-sky anisotropy reconstruction. Low-ell morphology studies show appreciable mask dependence. A new morphology tensor alone is therefore not a novelty claim. The candidate is calibrated transport of these typed carriers through the same frame/shear variables used in other probes, with same-sky covariance and held-out validation.

## T2. Dipole anomaly

Separate:
1. observer velocity relative to radiation beta_RO;
2. intrinsic/residual radiation dipole d_int with a gauge-invariant transfer definition;
3. radiation-matter relative drift beta_RM;
4. matter-observer velocity beta_MO;
5. tracer number-count dipole, which contains boost, structure, flux selection, spectral response and calibration.

For an ideal flux-limited sample the Ellis-Baldwin expectation is D=[2+x(1+alpha)] beta. In real catalogues x and alpha are distributions; the response must integrate each release's flux/redshift selection and spectrum. Overdispersion from multi-component radio sources must be tested; negative-binomial/hierarchical counts may be required. Include random catalogues, completeness, Galactic extinction, declination mask, local clustering, flux calibration, redshift selection and cross-match overlap.

A single dipole divided by one fiducial coefficient does not identify beta_MO. CMB dipole data alone measure a combination of boost and residual radiation dipole; separation needs independent aberration/Doppler/BipoSH, frequency/polarization response or a qualified matter-frame tracer. A prior must not create a likelihood eigenmode.

## T3. Beyond-FLRW kinematics

The local optical law identifies H as monopole, acceleration as polar dipole and shear as STF quadrupole. Vorticity is not present in the symmetric n^a n^b contraction at this order. It requires another channel. Gaia position-drift VSH separates E1 glide (secular acceleration), B1 spin (frame rotation) and E2 shear-like modes; those are distinct measured carriers, not direct metric components without a transfer.

The shear invariant relation in the full-sky uniform limit is
\[
\frac{\sigma_{ab}\sigma^{ab}}{6H^2}
=\frac54\left\langle(\sigma_{ab}n^an^b/H)^2\right\rangle_{S^2}.
\]
A cut sky must use the actual design/response and joint covariance. Finite-redshift directional distance coefficients remain phenomenological until a light-cone transfer and remainder are validated.

The vector/tensor x registry retains H, A/(cH), sigma_ij/H, omega_i/H, electric and magnetic Weyl STF2 components, plus their measured carriers. No one scalar invariant is asked to represent all of them.

## T4. Anisotropy classification and Bianchi spaces

A fitted STF2 axis is an observable representation, not a Bianchi label. Family classification requires:
- invariant spatial structure constants C^a_bc;
- spatial Ricci and its STF part;
- electric/magnetic Weyl tensors;
- shear, vorticity, acceleration and relative congruence motion;
- Einstein-matter evolution/constraints and history;
- family-specific transfer into CMB T/E/B, distances and astrometric position drift.

Bianchi polarized radiative-transfer hierarchies and ABSolve/ANICOSMO-style likelihoods already exist. Gaia DR3 Bianchi-I work finds significant quadrupole structure but does not confidently establish the predicted redshift growth. Therefore a Bianchi family claim is blocked until the family solver predicts at least two independent observable sectors and injection tests recover the family without systematics false positives.

The historical PR-190 refutation is scoped to its sealed hypersurface-orthogonal comparator premises; it is not a universal no-go theorem for Bianchi dynamics.

## T5. Direction- and redshift-dependent Hubble factor

Keep two estimands separate:
1. local H_u(n), the z→0 optical coefficient;
2. finite-z H_obs(z,n)=H_0(z)+D_i(z)n^i+Q_ij(z)n^in^j+..., where Q is STF after the angular window/basis is fixed.

Pantheon+ uses exact selected row identities and two-axis covariance subsetting. CF4 requires official Table 2/3/4 reconciliation, group/galaxy hierarchy, method pooling, calibrators and the actual source selection. Low-z optical coefficients are not finite-z transfer functions. Redshift-dependent calibration, peculiar-velocity correction, lensing, angular window and survey selection must be included.

Isotropically compressed DESI BAO constrain background H(z), D_M(z) but have no sky-axis multipole information. Directional BAO needs the full angular clustering catalogue, window and covariance.

## T6. Local boost versus global tilt

For probe p define d_p=O_p(Z,eta_p;W_p)+n_p. Compute the Jacobian of the actual estimator/forward operator. Whiten using the supported eigenspace of the full joint covariance, project shared/product nuisance in that same space, and calculate the identifiable quotient. Report full singular spectrum and all weak/null combinations.

Local boost acts through universal observer-frame Lorentz remapping/modulation. Global tilt is a relative-congruence/dynamical variable with tracer/redshift-dependent transfer. Shear is STF2. A common axis or alignment is insufficient. Include CMB independent boost estimator, multiple tracer selection responses, Gaia E1/B1/E2 modes and SN/CF4 redshift validation.

For functional phi_alpha, local identifiability requires ker(J_eff) subset ker(D phi_alpha). Global identification requires phi_alpha constant on each observation fibre. Otherwise retain K_alpha(D)=phi_alpha(C(D)) as a set. This is the actual convergence target for vector/tensor x.

## Cross-loop closure: kinematical theta and one joint likelihood

The six theory loops share one physical parameter domain rather than six independently fitted anomaly vectors. The state includes raw \(\sigma_{AB}\), axial \(\omega_A\), polar \(A_A\), and role-labelled \(\beta_{\rm RM,A},\beta_{\rm MO,A}\); \(\beta_{\rm RO}\) is a derived closure view. A functional registry then includes identity maps of these components, normalized copies, mixed contractions such as \(\sigma_{AB}\beta_{\rm RM}^A\beta_{\rm RM}^B/H\) and \(\beta_{\rm RM}^A\omega_A/H\), and predicted observer-space carriers.

The likelihood target is
\[
\mathcal L(\theta,\psi,\eta;D)
=p(D_{\rm CMB},D_{\rm count},D_{\rm SN/CF4},D_{\rm Gaia},\ldots
\mid\theta,\psi,\eta),
\]
with shared primordial/LSS/foreground/source fields integrated once and with full cross-probe covariance or an explicit conditional-independence model. The CMB harmonic covariance, count point process, directional distance likelihood and Gaia spin-1 proper-motion likelihood are observation operators on this same state. BipoSH, VSH and distance multipoles are typed predicted carriers or derived summaries, not extra independent data when computed from the same raw observation.

Local distance data constrain the leading expansion/acceleration/shear angular pattern, while vorticity remains blind in the leading symmetric radial contraction. Local observer boost and intrinsic congruence acceleration are distinct response directions. Functional-specific identifiability is assessed on the full likelihood tangent and observation fibres. The tensorized x,Q,Pi,F,G_F outputs are then computed from one common posterior/compatibility region; they are not separate likelihood factors. This is a source-conditioned likelihood-to-functional inference programme, not a new claim about the already established kinematic decomposition, CMB boost kernel or tensor MES geometry.

## Tensorized x and novelty

Pinned T7 defines one common state/confidence region and all functional images. Q is the matching anchor/gauge/margin; F separates directional support, pushforward and occupancy; Pi is a strict exceedance surface under a named law; G_F is a full-covariance depth path. These are established geometric/statistical constructs applied to this cosmological operator problem, not new mathematical priority claims.

The legacy x_C=Sigma2-W2+Omega_tilt+DeltaOmega_k is a many-to-one signed projection. It discards orientation, tensor eigendirections, parity, redshift evolution and functional dependence. It remains an optional ablation only.

The smallest candidate paper is a validated frame-covariant source-conditioned response and identifiable functional quotient across CMB, source-count and Gaia multipoles, with Pantheon+/CF4 as held-out distance validation. The contribution must outperform scalar x_C on a preregistered, calibrated comparison. If it does not, the result is a null methods comparison or functional upper/set bounds, not a global anisotropy detection.
