# R49 scientific continuation: general tilted Bianchi cosmology

Date: 2026-11-12 (Asia/Seoul)  
Track: convergence, theory-to-observable bridge, and local implementation handoff  
Claim ceiling: C0 until source-bound production inference and independent validation  
Convention: metric signature (-,+,+,+); retain c explicitly; spatial triads are orthonormal unless a coordinate basis is explicitly named.

## 1. Executive verdict

The Bianchi-I restriction is not forced by the existing project theory. The repository already contains an all-eleven-type Bianchi algebra registry, all-type shear-background scaffolding, a scalar rapidity plus fixed tilt direction in BianchiCosmology, partial exact tilted-fluid evolution for selected families, and geometry-only tilt-orbit identifiability. The restriction arises in the production bridge: the non-perturbative tilt RHS only registers FLRW, I, V, VII_0 and VII_h reduced families; the full hierarchy file is explicitly Bianchi-I; and no common all-type source-conditioned CMB/astrometry/count/distance likelihood is admitted.

The next programme must therefore generalize the physical state and its constraint equations, not merely replace the string BI_tilt with arbitrary type labels. A single beta scalar is insufficient for a general tilted homogeneous fluid: the tilt is a spatial three-vector in the invariant triad, and each matter/radiation species may have its own congruence. The fluid congruence can have vorticity even though the homogeneous hypersurface normal is hypersurface-orthogonal.

The strongest immediate scientific correction is that a genuinely tilted single perfect fluid in Bianchi I is not admissible under the standard homogeneous momentum constraint and positive enthalpy assumptions. This is not a blanket prohibition on Bianchi-I tilt: two or more fluids can carry nonzero individual tilts whose total normal-frame momentum obeys the constraint, and a 2026 nonlinear future-stability theorem establishes a two-fluid tilted Bianchi-I branch for 1/3 < K_(1) <= K_(2) < 5/7 with positive cosmological constant. The Bianchi-I tilt used in legacy code must therefore be classified as a single-fluid tilt, multi-fluid relative flow, radiation-to-matter frame relation, or observer boost before it is interpreted. These are not interchangeable.

## 2. What already exists, and why it stopped at Bianchi I

### 2.1 Repository assets

1. htt/bass/background/bianchi_types.py contains the Bianchi classification and a canonical (a,n,C) algebra representation, including Class A and Class B. The registry lists I, II, III, IV, V, VI_0, VI_h, VII_0, VII_h, VIII and IX. The Jacobi condition is n a = 0 in the corresponding canonical convention.
2. htt/bass/background/einstein_bianchi.py supplies an all-type background/shear integration surface, but BianchiCosmology stores beta as a scalar and v_hat_e as a fixed unit direction. The module documentation explicitly describes beta as held fixed in that integrator.
3. htt/bass/background/nonperturbative_tilt.py contains an exact King-Ellis rapidity RHS and a reduced six-variable state, but SUPPORTED_FAMILIES is limited to FLRW, Bianchi I, V, VII_0 and VII_h orthogonal/tilted branches.
4. htt/bass/background/codazzi_tilt_rhs.py wraps that reduced family RHS and enforces a Codazzi residual gate. It does not make the five-family RHS an all-eleven-type solver.
5. htt/bass/transport/bianchi_i_hierarchy.py is the Bianchi-I hierarchy path. It is not a generic Class-A/Class-B radiation hierarchy.
6. htt/bass/los/bianchi_propagator.py, tilted collision/visibility code, tilt_kinematics.py, tilted species code and old FB plans are reusable components, but each must be audited for family coverage, source congruence, frame convention, approximation order and whether it is a physical solver or a scaffold.
7. The R48 type-similarity / tilt-orbit work already studies all 11 algebraic types and geometric orbit identifiability, but excludes the full Einstein tilted-fluid evolution, polarized Boltzmann transfer, observational likelihood and Cobaya inference.

The present work therefore has a clear structural gap: algebraic family coverage is broader than dynamical and radiative-transfer coverage.

### 2.2 Existing result reuse

Use the R48 integrated DAG and receipts as historical evidence, not as an automatic current PASS:
- R48 L4: all-type Bianchi algebra, Class-A/Class-B catalogue, curvature-only degeneracies and geometry-only tilt orbit rank.
- R48 L1: Bianchi-I endpoint-map derivation and PR3/FFP10 pilot. It is not an all-family transfer.
- R48 L2: count-dipole estimands and selection/covariance limits.
- R48 L3: VSH and frame-spin identifiability.
- R48 L5: directional optical/Hubble jet.
- R48 L6: ordered boost composition and global-tilt versus observer-boost separation.
- R48 CORE-05: HTT five-view likelihood/push-forward contract remains SPEC_ONLY_PARTIAL.
- R48 CORE-07..09: production inference, adversarial benchmark and publication adjudication were NOT_RUN/HOLD.

R48 physical audit also found distinct inline and source-bound likelihood stacks, conflicting count-response constants, an unresolved count-channel frame-arrow conflict, a latent first-order velocity-closure default, and missing Wigner transport in production paths. These are live defects, not merely historical style issues.

## 3. General tilted-Bianchi physical state

### 3.1 Homogeneous geometry

Let N^a be the unit normal to the homogeneous spatial slices, N^a N_a = -c^2. Let e_alpha^a be an orthonormal spatial invariant triad. The invariant-frame commutator is

[e_alpha,e_beta] = C^gamma_(alpha beta) e_gamma,

with

C^alpha_(beta gamma) = epsilon_(beta gamma delta) n^(delta alpha)
                     + a_beta delta^alpha_gamma
                     - a_gamma delta^alpha_beta,

where n^(alpha beta) is symmetric and the Jacobi condition is n^(alpha beta) a_beta = 0. Class A has a_alpha=0; Class B has a_alpha nonzero. Preserve the repository's exact axis, epsilon, sign and h conventions. Do not silently identify the legacy StructureConstants and BianchiAlgebra representations until an explicit conversion map and round-trip tests exist.

The eleven type strata are:
- Class A: I, II, VI_0, VII_0, VIII, IX.
- Class B: III = VI_(h=-1), IV, V, VI_h, VII_h.
- h is a continuous family parameter where its defining nonzero eigenvalue products exist; h=-1 is the III/VI_h boundary, not an independent duplicated family.

The family classifier describes the homogeneous group action. It is not by itself a local-isometry classifier, topology classifier or observational label. Retain action-equivalent type sets where the metric admits more than one simply-transitive action.

### 3.2 Distinct congruences and vector tilt

For each species s, define its fluid 4-velocity relative to the homogeneous normal by

u_s^a = Gamma_s (N^a + c V_s^alpha e_alpha^a),
V_s^a N_a = 0,
V_s^2 = delta_alpha_beta V_s^alpha V_s^beta < 1,
Gamma_s = (1 - V_s^2)^(-1/2).

The dimensionless tilt is the three-vector V_s^alpha. If useful, define its rapidity beta_s = artanh(|V_s|) and direction vhat_s^alpha = V_s^alpha/|V_s|, but beta_s and vhat_s are derived coordinates, not the canonical state. At V_s=0 the direction is undefined and must not be assigned a fake default as physical evidence.

At minimum preserve separate fields for:
- N: homogeneous orbit normal;
- u_m: matter congruence;
- u_r: radiation/plasma congruence where physically distinct;
- u_s: every additional fluid or effective component;
- O: local observer tetrad.

Relative velocities beta_Nm, beta_Nr, beta_mr, beta_ON and derived compositions must carry source/target frame IDs, epoch, triad basis, handedness and boost convention. For non-collinear chains, apply exact Lorentz transformations and carry the induced Wigner rotation to spatial vectors, STF tensors, polarization bases and covariance matrices. A vector subtraction is a named first-order approximation only.

### 3.3 Perfect-fluid stress seen by the homogeneous normal

For a fluid with rest-frame energy density epsilon_s, pressure p_s and tilt V_s, use

T_ab^(s) = (epsilon_s + p_s) u_a^(s) u_b^(s) / c^2 + p_s g_ab.

Define h_ab = g_ab + N_a N_b/c^2. The normal-frame energy density is

epsilon_N^(s) = T_ab^(s) N^a N^b / c^2
              = (epsilon_s + p_s) Gamma_s^2 - p_s.

Define the normal-frame energy-flux density and spatial stress by

J_a^(s) = - h_a^c T_cd^(s) N^d,
S_ab^(s) = h_a^c h_b^d T_cd^(s).

Then, in the orthonormal normal frame,

J_a^(s) = c (epsilon_s + p_s) Gamma_s^2 V_a^(s),
S_ab^(s) = p_s h_ab + (epsilon_s + p_s) Gamma_s^2 V_a^(s) V_b^(s),
pi_ab^(s) = (epsilon_s + p_s) Gamma_s^2 V_<a^(s) V_b>^(s).

Sum these projections over physical species before forming the total source. A cancellation of total momentum flux does not imply that every species is untilted. Preserve species-relative flows.

The Einstein Hamiltonian and momentum constraints, shear propagation, spatial-curvature evolution, and each fluid's energy/momentum conservation must be evaluated in the same normal-frame and extrinsic-curvature convention. In particular the ADM momentum constraint is a nontrivial algebraic/differential relation between C^alpha_(beta gamma), the normal shear and the total J_alpha. Derive its c factors and sign from the repository's declared K_ab convention; never patch the sign by matching a mock output. Enforce the constraint at initial data and through evolution, not only as a post-hoc scalar residual.

### 3.4 Constraint-induced family restrictions

The allowed tilt fibre is type-, matter-, and stress-model-dependent. The local solver must not apply one universal three-component tilt prior to every family. Build an explicit admissibility registry whose entries are proven from the full constraints or marked unresolved.

Important literature-supported checkpoints:
- Bianchi I: for a single homogeneous perfect fluid with positive enthalpy, the standard momentum constraint removes genuine fluid tilt. A nonzero beta in a Bianchi-I pipeline therefore requires a different interpretation or a multi-component counter-streaming construction with total momentum treated consistently.
- Bianchi II: classical tilted perfect-fluid results include irrotational branches; the tilt and allowed shear components are restricted by the constraint.
- Bianchi VI_0 and VI_h: tilted self-similar branches exist only on restricted state-parameter and family strata. The VI_h parameter changes the admissible equilibrium structure.
- Class B III/IV/V/VII_h: dedicated tilted-fluid dynamical systems exist; self-similarity and asymptotic attractors are not generic and depend on family and equation of state.
- Bianchi VIII/IX: genuinely tilted perfect-fluid branches can require nonzero fluid vorticity; do not force a zero-vorticity fluid closure simply because the homogeneous normal is hypersurface orthogonal.
- Results about absence of a proper homothetic vector or absence of a particular self-similar equilibrium are not no-solution theorems for general time-dependent models.

Each registry entry must specify: family stratum, fluid count, equation of state, anisotropic stress assumption, tilt dimension, constraint equations, known exact branches, excluded branches, vorticity/acceleration restrictions, source citation, and whether the statement is theorem, literature result, numerical observation or unresolved.

### 3.5 Fluid kinematics versus normal kinematics

Compute the kinematics of every congruence from its own covariant derivative:

theta_(s) = nabla_a u_s^a,
A_(s)^a = u_s^b nabla_b u_s^a,
sigma_(s)ab = projected STF nabla_(a u_(s)b),
omega_(s)ab = projected antisymmetric nabla_[a u_(s)b].

The normal shear Sigma_N, fluid shear sigma_(s), fluid vorticity omega_(s), and acceleration A_(s) are different physical objects. Their relation contains derivatives of V_s^alpha and the invariant-frame commutators/connection. A spatially homogeneous vector has time-dependent triad components, but its covariant derivatives are not zero. Never identify a sky STF carrier with Sigma_N or sigma_(s) without the declared response map.

## 4. General-family computational programme

### 4.1 Dynamical system

The production state must include the full independent normal geometry variables, the complete STF shear (five real components), family structure parameters, lapse/normal acceleration where relevant, and one three-vector tilt per species. The reduced state (Omega_r, Omega_m, Sigma^2, W^2, beta, Omega_k) is a valid reduced model for its registered family only; it is not a substitute for the general state.

Required equations and checks:
1. Jacobi identity and structure-constant convention.
2. Hamiltonian constraint.
3. Three momentum constraints with total normal-frame energy flux.
4. Five-component shear propagation including spatial-curvature, anisotropic-stress and tilt terms.
5. Evolution/propagation of the Bianchi curvature variables and commutators.
6. Energy and Euler equations for each fluid, including the exact vector-tilt evolution.
7. Codazzi/Gauss-Codazzi residuals at every accepted integration step.
8. Exact FLRW, untilted, single-fluid admissible, multi-fluid counter-streaming, and known self-similar limits.

The first implementation should be an expansion-normalized tetrad/orthonormal-frame system because this is the established language for the Bianchi dynamical-system literature and is already close to the project's (a,n,C) algebra representation. Keep a direct metric/coframe oracle for sign and curvature validation. Do not make the reduced scalar beta solver the authority for the new vector state.

### 4.2 Implementation sequence

- Stage A: freeze one canonical (a,n,C) convention and bridge every legacy type representation through exact transformations.
- Stage B: implement the all-family normal-frame Einstein constraints and the typed multi-fluid source projections.
- Stage C: implement full vector tilt evolution with equation-of-state and anisotropic-stress choices; add type-specific admissibility constraints.
- Stage D: validate Class A and Class B branches independently, including h-continuation and boundary strata.
- Stage E: implement null geodesic, screen basis, redshift, Sachs/Jacobi and polarization transport over the resulting background.
- Stage F: connect radiation Stokes I,Q,U or harmonic T/E/B source evolution to the common tensor state.
- Stage G: expose family-specific source-conditioned likelihoods to Cobaya and common-posterior HTT push-forward.

### 4.3 Family coverage matrix

Do not mark a family as supported because its algebra object exists or because its untilted shear background integrates.

| Family | Algebra catalogue | Existing reduced tilt RHS | Required general extension | Initial validation role |
|---|---|---|---|---|
| I | Present | Present, restricted | Enforce single-fluid no-tilt theorem; add explicit multi-fluid relative-flow lane | exact flat anisotropic limit |
| II | Present | Absent | Add constraint-compatible vector tilt | first non-flat Class-A check |
| VI_0 | Present | Absent in reduced RHS | add tilted Class-A state space | known self-similar branch |
| VII_0 | Present | Present, reduced | general vector tilt and curvature transport | flat-FLRW-limit Class-A check |
| VIII | Present | Absent | add tilted/vortical branches | non-compact Class-A and curvature oracle |
| IX | Present | Absent | add constraint-compatible tilted branch and closed-curvature treatment | positive-curvature/Class-A control |
| III | Present | Absent | VI_(h=-1) bridge and Class-B constraints | h=-1 boundary |
| IV | Present | Absent | Class-B momentum/curvature and tilt equations | exceptional Class-B stratum |
| V | Present | Present, reduced | general vector tilt and non-self-similar branches | open-FLRW-limit Class-B control |
| VI_h | Present | Absent | continuous h family; h=-1 and h=-1/9 checks | Class-B parameter continuation |
| VII_h | Present | Present, reduced | general vector tilt, handedness and polarization transport | established CMB template comparator |

“Absent” means absent from the current reduced exact-tilt family registry, not absent from all historical code or from the literature.

## 5. Observables and common likelihood

### 5.1 CMB low-ell morphology

The deterministic homogeneous signal and the stochastic anisotropic covariance are different terms in one map/harmonic generative model. For a selected Bianchi model M_B and physical parameter state Theta,

a_lm^obs = a_lm^iso + mu_lm^B(Theta,M_B) + delta a_lm^observer( beta_ON )
           + noise/foreground contribution.

The likelihood must also admit the model-dependent harmonic covariance

Cov[a_lm,a_l'm'] = C_lm,l'm'(Theta,M_B, transfer, beam, mask, foreground, noise).

Do not multiply a deterministic Bianchi-template likelihood and a BipoSH covariance likelihood as if they were independent observations when both are functions of the same a_lm. Use one joint map/harmonic likelihood or a mathematically justified conditional factorization.

The radiation state must carry I,Q,U or T,E,B, including the Bianchi-family geodesic direction, polarization screen transport, Thomson visibility and reionization. A temperature-only Bianchi-I endpoint map is a validation subset, not the final operator. For families without an FLRW limit, use an explicitly non-perturbative branch and do not pretend a linearized near-FLRW transfer is valid.

### 5.2 Count dipoles and local/global kinematics

Model the Quaia, NVSS and RACS catalogues as separate marked point processes with their own selection functions, redshift distributions, flux/size response, completeness, shot noise and clustering covariance. The observer boost and global matter/radiation tilt are different model parameters. Count response coefficients must be measured from the actual source selection or marginalized with declared priors; literal constants from the old inline likelihood are not observations.

### 5.3 Astrometry

Use Gaia CRF3/ICRF frame identity, scanning law, source-level proper-motion covariance, reference-frame spin and any source-velocity nuisance. A B1 VSH coefficient is not automatically fluid vorticity. A free reference-frame spin can be exactly degenerate with an absolute rigid-rotation mode. The likelihood must expose this null direction rather than claim vorticity detection.

### 5.4 Directional distance and Hubble expansion

For a chosen smooth source/observer congruence u^a and a regular local direction e^a,

H_u(e) = theta_u/3 - A_a^(u)e^a/c + sigma_ab^(u)e^a e^b,
d_L(z,e) = c z/H_u(e) + O(z^2).

This is a local low-z law for that congruence. It is not automatically the homogeneous-normal Hubble coefficient. At finite redshift use the integrated optical/redshift solution, with source windows, curvature terms and remainder bounds. Pantheon+ and CF4 cannot be assigned arbitrary directions or block-diagonal cross-covariance.

### 5.5 The HTT five-view contribution

For one common physical posterior/compatibility law P(Theta, nuisance | D, M_B), compute:
- x: sample-by-functional tensor/vector/scalar array x[s,alpha], with rank, parity, units, frame, epoch, source operator and physical state identity;
- Q: declared anchor/gauge/margin bodies and uncertainty;
- Pi: law-conditional exceedance surfaces under explicitly named posterior and matched-null laws;
- F: directional support/occupancy profiles from admitted anchor bodies;
- G_F: depth path across redshift shells with full data and cross-shell covariance, distinct from posterior covariance.

These are five derived views of the same common law. They are not five independent likelihood factors and they must never be populated by independent marginal fits. Include in x the direct components of Sigma_N, omega_(s), A_(s), every V_s, structure parameters (a,n), cross-congruence invariants and predicted observable carriers. Keep the optional legacy scalar x_C strictly as an ablation.

## 6. Novelty, significance and adversarial comparison

### 6.1 What is established prior art

The following are not new contributions:
- General Bianchi classification by Lie algebra structure and Class A/B.
- Tilted homogeneous perfect-fluid cosmologies and their type-dependent constraints.
- Exact/self-similar or dynamical-system branches in selected Bianchi types.
- Nearly-FLRW Bianchi polarized CMB multipole hierarchies.
- Coherent temperature/polarization patterns for the Bianchi types with an FLRW limit.
- Local Lorentz boost, aberration and observer-frame dipole physics.
- Generic vector/tensor rotational invariants.

Key primary sources:
1. King & Ellis (1973), “Tilted homogeneous cosmological models”, Communications in Mathematical Physics 31, 209–242. The fluid flow need not be normal to homogeneous surfaces and can carry expansion, rotation and shear. DOI: 10.1007/BF01646266.
2. Hewitt (1991), “An exact tilted Bianchi II cosmology”, Classical and Quantum Gravity 8, L109–L114. DOI: 10.1088/0264-9381/8/5/004.
3. Hewitt & Wainwright (1992), “Dynamical systems approach to tilted Bianchi cosmologies: Irrotational models of type V”, Physical Review D 46, 4242. DOI: 10.1103/PhysRevD.46.4242.
4. Barrow & Hervik (2003), “The future of tilted Bianchi universes”, Classical and Quantum Gravity 20. arXiv:gr-qc/0304050. Their analysis covers all Class-B models and VI_0 stability against tilted-fluid perturbations.
5. Apostolopoulos (2004), “Equilibrium points of the tilted perfect fluid Bianchi VI_h state space”, arXiv:gr-qc/0407040. It gives the VI_h tilted evolution equations and h-dependent equilibrium restrictions.
6. Apostolopoulos (2004/2005), “Self-similar Bianchi models: II. Class B models”, arXiv:gr-qc/0411102; published CQG 22, 323–338. It derives the exceptional VI_(-1/9) tilted branch and restrictions on self-similar solutions in other Class-B families.
7. Shogin & Hervik (2015), “Dynamics of tilted Bianchi models of types III, IV, V in presence of diffusion”, CQG 32, 055008. arXiv:1402.2785. It numerically integrates tilted Class-B models III/IV/V with additional diffusion physics.
8. Pontzen & Challinor (2007), “Bianchi model CMB polarization and its implications for CMB anomalies”, MNRAS 380, 1387–1398. DOI: 10.1111/j.1365-2966.2007.12221.x. It derives a polarized multipole hierarchy in the nearly-FLRW limit for Bianchi-classified models.
9. Sung & Coles (2011), “Temperature and polarization patterns in anisotropic cosmologies”, JCAP 06 (2011) 036. DOI: 10.1088/1475-7516/2011/06/036. It explicitly studies the FLRW-limit families I, V, VII_0, VII_h and IX.
10. Planck Collaboration (2016), “Planck 2015 results XVIII: Background geometry and topology of the Universe”, A&A 594, A18. DOI: 10.1051/0004-6361/201525829. The physically coupled Bianchi VII_h analysis found no evidence and quoted a model-specific 95% upper bound (omega/H)_0 < 7.6e-10. This is a competitor/baseline, not a constraint to copy into a different model.
11. Fournodavlos, Marshall & Oliynyk (2026), “Future Stability of Tilted Two-Fluid Bianchi I Spacetimes”, Annales Henri Poincare, published 7 July 2026. DOI: 10.1007/s00023-026-01727-7. They prove future nonlinear stability for tilted two-fluid Bianchi-I Einstein-Euler solutions with positive cosmological constant and linear equations of state in the range 1/3 < K_(1) <= K_(2) < 5/7. Their introduction explicitly notes that the Bianchi-I momentum constraint requires two or more fluids for tilt. This is a direct prior-art boundary: do not claim the two-fluid Bianchi-I solution itself as new; use it as a required benchmark and derive any new contribution from the general-family, cross-probe, source-conditioned tensor inference.

### 6.2 Candidate project-specific contribution

The conditional novelty is a common, frame-covariant, source-conditioned tensor posterior that connects all admissible Bianchi family strata and their tilted matter/radiation congruences to CMB harmonic morphology/covariance, source-count dipoles, astrometric vector harmonics and direction/redshift-dependent distances. It combines:
- type-specific physical admissibility and momentum-constraint fibres;
- exact frame composition and Wigner transport;
- action-aware partial identification rather than forced unique family labels;
- source-level selection/covariance/transfer contracts;
- one joint posterior and the HTT (x,Q,Pi,F,G_F) push-forward;
- adversarial comparison with established geometric classifiers, BipoSH/multipole/power-tensor readouts, observer-boost estimators and Bianchi VII_h template fits.

This is a plausible methods contribution, not an established novelty claim. It becomes publishable only if the method is shown to add calibrated information beyond each competitor and to fail gracefully where the data identify only a quotient class.

### 6.3 Adversarial benchmark matrix

Benchmark the tensorized HTT method against:
A. scalar x_C ablation;
B. standard Bianchi family-specific deterministic template likelihood;
C. BipoSH covariance-only and mean-template-only readouts;
D. multipole vectors/power tensor low-ell summaries;
E. local observer-boost-only model;
F. global tilted-Bianchi model with exact frame transport;
G. isotropic FLRW plus local structure/selection nuisance;
H. class-agnostic geometry-only (a,n) orbit classifier;
I. separate single-probe fits without shared latent state.

For every competitor use the same source rows, maps, masks, beams, selection, covariance, nuisance priors, and held-out split where the model permits it. Report:
- recovery bias and coverage under each family/type/tilt stratum;
- false-family identification rate under action-equivalent metrics;
- posterior calibration/SBC, split-Rhat, bulk/tail ESS and PPC;
- leave-one-probe-out predictive log score and held-out tracer/cut prediction;
- robustness to selection/covariance misspecification and frame-spin nuisance;
- runtime and parameter-count cost;
- where HTT wins, ties, loses or is not comparable.

The main benchmark is not scalar-versus-tensor in isolation. It is whether the common typed posterior produces better calibrated, more informative physical inferences without false geometry claims.

## 7. Data plan and the NPIPE bypass

No new data acquisition is required for the first publication attempt. The R48 DATA_INVENTORY and DOWNLOAD_MANIFEST already record held Planck PR3, FFP10, NPIPE PR4, Planck ancillary/component maps, Quaia, NVSS, RACS, Gaia/CRF3/scanning law, Pantheon+, CF4 and DESI data bundles. Local availability and exact hashes must be rechecked by the local agent; the GitHub inventory is not proof that every current local byte still exists.

### 7.1 Primary calibrated CMB lane: Planck PR3 + FFP10

Use PR3 SMICA/HM observed maps and the same-release FFP10 ensemble as the primary low-ell estimator and matched null. The existing 60-pair pilot is only a pilot: it reported near-zero component means within 1.32 standard errors and a Gram-norm null scale around 2.2e-5, but sample-sd uncertainty is about 9% at N=60 and no coverage/SBC was run. Do not call this a calibrated likelihood.

Local tasks:
1. Reconcile PR3 observed maps, HM/split maps, masks, beam/transfer window and component convention.
2. Verify FFP10 product type and pipeline matching. Hash and header-audit the actual chosen simulation files.
3. Use a seeded, stratified MC sequence: smoke test N=60; pilot N=200; calibrated production target N>=500 or a stopping rule based on Monte-Carlo uncertainty and coverage. Do not claim a fixed final N before checking resource cost.
4. Calibrate the estimator and the full likelihood, not only a five-component null mean. Run injected templates across B amplitude, orientation, handedness, family strata, mask and noise.
5. Keep deterministic template mean and stochastic anisotropic covariance in a single generative model.
6. Compare SMICA with available PR3 component-separated controls; preserve split-map noise diagnostics.
7. Recover the effective beam/window from the already held RIMO/beam products or mark the relevant scale range unavailable; do not silently assume a unit beam.

### 7.2 NPIPE PR4 lane: observed-map robustness without a matched-null claim

The catalogue records 22 NPIPE PR4 items (~19.78 GB). The prior PR4 receipt reports that full-ring and half-ring maps were acquired, but the matched official NPIPE simulations were unavailable through the NERSC path. A half-ring difference is a noise-only single realization per frequency. It cannot estimate the full sky-signal plus noise sampling distribution or CMB cosmic variance.

Therefore:
- NPIPE is not a blocker.
- Do not use PR3 FFP10 as if it were an NPIPE matched null.
- Use PR3+FFP10 for calibrated primary inference.
- Use NPIPE full maps as a separate observed-map robustness lane only after beam, frequency, mask, pixelization, calibration and transfer harmonization.
- Use NPIPE half-ring differences only for a scoped noise diagnostic, with one-realization limitations.
- An optional NPIPE synthetic null may be constructed from a declared C_l and validated NPIPE noise model, but must be labeled SYNTHETIC/TRANSFER-CONDITIONAL, never matched official PR4 calibration.
- If the NPIPE beam/RIMO product is available in the existing catalogue, derive/check its transfer; no map comparison before that.
- No result may mix PR3 FFP10 and PR4 NPIPE into one nominal matched-null distribution.

The existing PR4 lane receipt is PROBE_DONE_NOISE_ONLY; PR4_NULL_NOT_FORMABLE. Preserve that result, but supersede the earlier user decision to exclude the entire NPIPE path: NPIPE is now an optional robustness/noise lane, not a prerequisite for the science result.

### 7.3 Other existing probes

Use the already held bundles:
- Quaia and NVSS as the primary source-count channels; RACS as an independent replication channel after its completeness/flux operator is source-bound.
- Gaia DR3/CRF3 plus Gaia scanning law; require the exact frame-spin tie and source-level covariance or retain vorticity as a null/partial-identification direction.
- Pantheon+ full covariance and CF4 row-level/group method identity; keep exact two-axis covariance subsetting and selection.
- DESI directional/full-shape products only where the estimator actually preserves angular information; isotropic BAO is a background expansion control, not an anisotropy measurement.
No mock/random catalogue or hard-coded dipole may be promoted to an observed input.

## 8. Publication gate and immediate priorities

### Publication assessment

Current state: not yet an empirical discovery paper. It is a conditional methods-paper candidate and a strong theory/software programme, but production observational inference is not complete. The historical R38/R39 joint-chain claims are quarantined because their adapters contained zero/default likelihoods, hard-coded data carriers and unsupported covariance/fallback assumptions. R48 has improved the contracts and source inventory, but CORE-05 remains SPEC_ONLY_PARTIAL and CORE-07..09 NOT_RUN/HOLD.

### Next five highest-value tasks

1. Generalize the physical state and admissibility constraints for vector tilt across all 11 types and multiple fluids; explicitly repair or reinterpret the Bianchi-I single-fluid tilt path.
2. Build and test a single all-family normal-frame Einstein RHS with per-species vector tilt and full Gauss-Codazzi/momentum constraints.
3. Generalize the photon geodesic / polarized hierarchy from Bianchi I to a family-dispatched geometry operator; keep an external AniCLASS/ABSolve comparison as a competitor, not native validation.
4. Implement source-bound CMB PR3+FFP10 likelihood and then connect the other existing probes through one common latent state.
5. Execute calibrated posterior inference and the adversarial benchmark. Only then adjudicate publication claims.

A bounded publishable result may be a calibrated family-quotient or partial-identification result, even when no unique Bianchi label is identifiable. A null or non-detection can be publishable if the likelihood is properly calibrated, the family domain is explicit, and the inference has demonstrable information gain over established methods.

## 9. References and prior-art links

- King & Ellis (1973): https://doi.org/10.1007/BF01646493
- Hewitt (1991): https://doi.org/10.1088/0264-9381/8/5/004
- Hewitt & Wainwright (1992): https://doi.org/10.1103/PhysRevD.46.4242
- Barrow & Hervik (2003): https://arxiv.org/abs/gr-qc/0304050
- Apostolopoulos (2004) VI_h: https://arxiv.org/abs/gr-qc/0407040
- Apostolopoulos (2004) Class-B self-similar: https://arxiv.org/abs/gr-qc/0411102
- Shogin & Hervik (2015): https://arxiv.org/abs/1402.2785
- Pontzen & Challinor (2007): https://doi.org/10.1111/j.1365-2966.2007.12221.x
- Sung & Coles (2011): https://doi.org/10.1088/1475-7516/2011/06/036
- Planck Collaboration (2016): https://doi.org/10.1051/0004-6361/201525829

## 10. Execution status for this R49 turn

Completed here:
- GitHub read-only review of the R48 DAG, source inventory, PR #573/#574 metadata, physical-state audit, previous Bianchi geometry/tilt reports and relevant code paths.
- Literature comparison with primary sources listed above.
- Constructive definition of the general tilted-Bianchi state, stress projections, constraint/transfer workstream, family coverage matrix, novelty boundary, data plan and local execution contract.
- Successor DAG and local restart prompt authored on a dedicated GitHub branch.

Not executed here:
- No remote desktop use.
- No local repository checkout or shell test.
- No raw data rehash, map processing, sampler run or real posterior.
- No native subagent dispatch; native_subagent=NOT_RUN due unavailable dispatch interface.
- No PR merge and no main-branch mutation.
