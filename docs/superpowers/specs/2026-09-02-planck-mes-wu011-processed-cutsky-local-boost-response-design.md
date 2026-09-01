# PMG-WU-011 processed cut-sky local-boost response — design v2

## 1. Status, correction, and approval boundary

This is a **design-only stacked successor** to PMG-WU-010. It adds no production implementation, no RED tests, no raw-data access, no observed statistic, and no claim promotion.

Version 2 corrects a load-bearing operator-order error in the first design commit. The repository's `fit_joint_cutsky_alm` does **not** apply beam/pixel commonization before the weighted harmonic solve. It performs the joint `ell=0..5` solve first, commonizes the fitted coefficients by the target/source transfer ratio, and only then retains `ell=2..5`. WU-011 must reproduce that order rather than invent a new pipeline.

The implementation plan may begin only from this corrected design. Production implementation remains a separate test-first stacked branch.

## 2. Exact authority

```yaml
repository: cosmosapjw-quantum/htt_base
scientific_base_pr: 441
scientific_base_head: 04680e99d56b9974fe1120854370af1fb94fb1d6
predecessor_pr: 442
predecessor_reviewed_code: 8a59ee1126b9eccdaa6fecb14de442e8c68b988d
predecessor_document_closeout: 29427a1f7f2c5d46e43ffe03053c4ac13e969228
predecessor_reviews:
  - 5080263134
  - 5080373512
design_pr: 443
design_v1_head: 0ec000b3170aa314fda6066ee2bf12fd7fe5edaf
joint_cutsky_estimator_id: joint_weighted_real_harmonic_l0_l5_retain_l2_l5:v1
joint_cutsky_source_sha: fb60cafbb2bac1cfa48730de919631b6806e6c7b
jira_owner: BASS-21
confluence_plan: 21823493
confluence_theory_seed: 22151174
research_workspace: 1-n_oX1tLHvoova1Jdlh8Xn0EXJxM_HiPjjAeEPE9Rq4
```

The PR #441 theorem ledger remains `USER_SUPPLIED_SUMMARY / FORMAL_DOSSIER_PENDING`. WU-010 and WU-011 bounded algebra or numerical tests are not a replay of P01–P27.

## 3. Scientific objective

Construct and validate a content-bound synthetic low-ell coefficient response of a finite **local observer Lorentz boost** after the repository's actual source transfer, pixel synthesis, fixed weighted mask, simultaneous nuisance/retained harmonic fit, post-fit beam/pixel commonization, and retained-carrier selection.

The target is a processed response operator and diagnostic envelope. It is not an observational velocity measurement.

The baseline ordered path is

```text
strictly positive absolute thermodynamic-temperature sky
  -> exact finite local observer boost
  -> source beam and source pixel-window convolution
  -> synthesis on the registered HEALPix grid
  -> fixed target-frame weighted mask inside the joint normal equations
  -> simultaneous real-harmonic ell=0..5 solve
       ell=0,1: nuisance coefficients
       ell=2..5: retained candidates
  -> post-fit target/source beam-pixel commonization
  -> retained ell=2..5 carrier
  -> optional ell=2,3 STF/orbit morphology
```

No additional map filter exists in this baseline path. A later filter is a separate extension with a new operator identity; it is not silently represented by an `F_ell`.

The order is part of the contract. No operation may be commuted, omitted, or commonized at another stage without a new content identity and an explicit differential diagnostic.

## 4. Fixed conventions

- spacetime metric: `(-,+,+,+)`;
- photon momentum: `p^a=(epsilon/c)(u^a+e^a)`;
- outward observer-sky direction: `n^a=-e^a`;
- boosted observer: `u_tilde^a=gamma(u^a+beta^a)`;
- dimensionless local velocity: `beta^a=v^a/c`, with `beta^2<1`;
- scalar observable: strictly positive thermodynamic blackbody temperature, Doppler weight `d=1`;
- harmonic convention: orthonormal Condon–Shortley;
- scientific stored-real layout: `(a_l0, Re a_l1, Im a_l1, ..., Re a_ll, Im a_ll)` without hidden `sqrt(2)` rescaling;
- internal joint-fit real basis: the existing `planck_pr3_operator.real_alm_layout` convention, including its explicit `sqrt(2)` normalization and imaginary-sign adapter;
- local observer boost is distinct from global matter-frame tilt, electron-frame collision kinematics, and Bianchi geometry.

The processed response preserves temperature units. `beta`, condition numbers, relative singular floors, and normalized residuals are dimensionless. Every conversion between the scientific stored-real layout and the joint-fit basis must be explicit and round-trip tested.

## 5. Actual repository operator

Let

- `S_abs` construct a strictly positive intrinsic thermodynamic-temperature sky;
- `B_beta` be the exact WU-010 finite local boost;
- `G_beta` be its first-order generator, linear in `beta`;
- `D_src` be the diagonal source beam-times-pixel transfer;
- `Y_src` synthesize source-band coefficients on the registered HEALPix grid;
- `J_W` be the frozen weighted joint `ell=0..5` least-squares map-to-coefficient operator;
- `D_com` be the post-fit diagonal commonization with entries `d_l=(b_l^target p_l^target)/(b_l^source p_l^source)`, constrained by `0<d_l<=1`;
- `H_ret` select the fitted/commonized `ell=2..5` block.

The baseline processed operators are

```text
R_proc(beta) = H_ret D_com J_W Y_src D_src B_beta S_abs,
R_proc(0)    = H_ret D_com J_W Y_src D_src S_abs,
G_proc(beta) = H_ret D_com J_W Y_src D_src G_beta S_abs.
```

The finite-to-linear gate is

```text
||R_proc(beta)-R_proc(0)-G_proc(beta)|| = O(|beta|^2)
```

on a preregistered beta grid and fit interval.

### 5.1 Joint solve and nuisance profiling

The actual implementation solves all `ell=0..5` coefficients simultaneously. It does not delete monopole/dipole from the map before fitting. With the design partitioned into nuisance columns `N` (`ell=0,1`) and retained columns `R` (`ell=2..5`), the mathematically equivalent retained solution is

```text
M_N = I - N (N^T W N)^(-1) N^T W,
a_R_hat = (R^T W M_N R)^(-1) R^T W M_N m.
```

This Frisch--Waugh--Lovell expression is a diagnostic identity only. Production must call the existing joint solver and compare against it; it must not replace the solver.

The boost-induced dipole is present in the finite boosted map and is profiled by the simultaneous fit. Deleting it before the solve is a sign/order mutation and must fail.

### 5.2 Source transfer and post-fit commonization

For a diagonal transfer `D_b` and first-order boost generator `G`,

```text
[D_b,G]_{l'm',lm}=(b_l' - b_l) G_{l'm',lm}.
```

The physical source transfer occurs after the sky boost and before synthesis. The repository commonization occurs after the joint solve. The source-order mutation has the exact first-order difference

```text
Delta_src = H_ret D_com J_W Y_src [D_src,G] S_abs.
```

A nonconstant source beam or pixel window therefore cannot be commuted through the boost. A scalar attenuation factor cannot represent general mask- and fit-induced mode mixing; the response must be a matrix.

### 5.3 Fixed target-frame mask

For Doppler weight one,

```text
T_tilde(n_tilde)=D(n)T(n),
dOmega_tilde=D(n)^(-2)dOmega.
```

A fixed target-frame mask obeys

```text
Integral W(n_tilde)|T_tilde(n_tilde)|^2 dOmega_tilde
 = Integral W(A_beta n)|T(n)|^2 dOmega.
```

For an axis-aligned smooth mask,

```text
mu_tilde=(mu+beta)/(1+beta mu),
W(mu_tilde)=W(mu)+beta(1-mu^2)W'(mu)+O(beta^2).
```

A sharp binary mask has a distributional boundary contribution. Production must use the finite pixelized weights directly. A smooth derivative calculation is allowed only for a separately identified apodized surrogate.

### 5.4 Source-band and alias contract

The fit band ends at `ell=5`, but the first-order boost couples neighboring multipoles. Exact first-order response into the retained band therefore requires a source basis through at least `ell=6`. The finite pixel reference is not truncated after boosting.

The initial Jacobian source registry is

```text
ell=0..6 scientific stored-real basis,
49 source coordinates,
3 Cartesian beta directions,
32 retained output coordinates.
```

The response tensor has shape `(3,32,49)` or the equivalent flattened shape `(32,147)`. The `ell=6 -> retained ell<=5` block is the mandatory first out-of-band alias block. Optional `ell=7` finite probes are diagnostics of higher-order and mask leakage, not part of the first-order completeness claim.

## 6. Architecture choice

### Recommended hybrid

1. **Finite reference path.** Construct a positive intrinsic sky, apply the exact WU-010 field pullback, apply `D_src`, synthesize a map, and call `fit_joint_cutsky_alm`.
2. **Linear response path.** Evaluate the WU-010 first-order generator on the same sky, apply the same `D_src`, synthesis, joint solve, post-fit commonization, and retained selection.
3. **Coefficient Jacobian.** Inject the frozen `ell=0..6` source basis along the three Cartesian beta directions and record the retained response.
4. **Differential audit.** Compare finite, linear, and Jacobian predictions over the preregistered beta grid.
5. **Historical parity.** Compare the generic finite map path with `boost_biposh_residual.ExactBoostOperator` only on its declared fixed-axis, bandlimit, map pixelization, and transfer overlap domain.

This gives an exact finite oracle while producing the coefficient-level object needed by later inference. It does not assume a scalar transfer function captures processing-induced mixing.

### Rejected as baseline: transfer before boost

Applying `D_src` before `B_beta` changes the result by the nonzero commutator above. It is retained only as a mutation lane.

### Rejected as baseline: standalone filtering layer

The existing joint estimator path has no generic filter object. Adding one in WU-011 would invent a new pipeline. Filtering remains a typed successor extension.

### Rejected as primary: Monte Carlo-only calibration

Simulation-only calibration can hide convention, operator-order, rank, and sign errors. Simulations are validation after the exact finite and first-order paths agree.

## 7. Types and module boundaries

### `PositiveAbsoluteSkySpec`

Owns the absolute monopole, scientific stored-real `ell=1..source_lmax` coefficients, source band, units, convention, HEALPix positivity margin, and content identity. It refuses nonpositive samples; clipping is forbidden.

### `ProcessedBoostOperator`

Owns the exact mask, `JointCutSkyOperator`, source and target beam/pixel arrays, source band, HEALPix grid, processing-order identifier, predecessor code identities, thresholds, and content identity.

It must verify that the supplied joint operator was built from the exact same mask and that `fit_joint_cutsky_alm` remains the execution entry point.

### `ProcessedBoostEvaluation`

Carries one zero, finite, or first-order retained carrier together with source/operator IDs, beta, weighted residual norm, positivity margin, and typed refusal metadata.

### `ProcessedBoostResponseReceipt`

Carries the response tensor, source/output registries, singular spectra by beta direction and combined design, condition numbers, alias blocks, nuisance diagnostics, mutation results, plot identities, and terminal state.

The new module calls WU-010 APIs and `planck_pr3_operator`; it does not duplicate the Lorentz or joint-solve formulae. `ExactBoostOperator` remains separate.

## 8. Work lanes

### W11-A — authority, order, and schema freeze

Freeze predecessor heads, code blob identities, source and fit bands, basis layouts, processing order, thresholds, terminal states, and claim firewall.

### W11-B — positive-sky and source-transfer constructor

Construct a positive monopole plus controlled source coefficients through `ell=6`. Apply the source beam and pixel window only after the finite or first-order boost. Record positivity margins before and after the boost.

### W11-C — zero-boost replay

Require `R_proc(0)` to match a direct call to the existing no-boost `fit_joint_cutsky_alm` path. Any predecessor-output drift is blocking.

### W11-D — finite-to-linear convergence

Use a frozen beta-direction registry and beta-amplitude grid. Fit the residual slope only on a preregistered interval and require a stable residual divided by `|beta|^2`.

### W11-E — sign and dipole mutations

Flip `n=-e` to `n=e`, flip beta, and omit the boost-induced dipole before the joint fit. Each mutation must leave an `O(|beta|)` failure.

### W11-F — mask and transfer sensitivity

Mutate exactly one of the target-frame mask, source beam, source pixel window, target beam, or target pixel window. Bind each changed identity. Compare binary and apodized masks without differentiating the binary boundary.

### W11-G — out-of-band aliasing

Construct the `ell=6` source-to-retained block and optional `ell=7` finite probe. Separate intrinsic boost coupling from fixed-mask/joint-fit leakage.

### W11-H — nuisance profile

Compare the simultaneous full solve with the weighted Frisch--Waugh--Lovell retained solution. Reject pre-solve dipole deletion and any nuisance rank loss.

### W11-I — historical fixed-axis parity

Compare with `ExactBoostOperator` only under matched fixed axis, `nside`, `lmax`, Doppler convention, and source transfer. No silent replacement is allowed.

### W11-J — receipt, plots, and future inference contract

Generate content-bound matrices, diagnostics, plot hashes, and typed terminal. Preregister how response uncertainty and same-sky row-equivariant processing would enter later calibration. No observed rank is computed.

## 9. Mandatory RED-first tests

The implementation plan starts with failing tests for

1. missing `processed_boost_response` production module;
2. moved PR #442 authority or changed joint-estimator identity;
3. scientific stored-real versus internal joint-fit basis mismatch;
4. nonpositive absolute temperature;
5. zero-boost predecessor replay;
6. finite-to-linear `O(beta^2)` order;
7. wrong-sign and omitted-dipole `O(beta)` mutation survival;
8. source-transfer/boost noncommutation;
9. binary/apodized mask sensitivity;
10. `ell=6` alias block shape and nontriviality;
11. nuisance rank and full-solve/FWL equality;
12. historical fixed-axis parity;
13. typed terminal and claim-firewall rejection.

The RED state must be recorded before production code is added.

## 10. Diagnostics and plots

At minimum:

- zero-boost retained-coefficient residual;
- finite-to-linear log-log residual and `residual/|beta|^2` plateau;
- correct versus sign and omitted-dipole mutations;
- response singular values and condition number;
- response tensor slices or registered matrix heatmaps;
- `ell=6` leakage heatmap;
- mask and transfer differential table;
- binary versus apodized mask response;
- full-solve versus FWL residual;
- historical fixed-axis parity residual.

Every plot is generated at registered dimensions and included in the receipt manifest with SHA-256.

## 11. Typed terminal states

```text
PASS_SYNTHETIC_PROCESSED_RESPONSE
BLOCKED_BY_MOVED_AUTHORITY
BLOCKED_BY_BASIS_MISMATCH
BLOCKED_BY_MISSING_ABSOLUTE_T
BLOCKED_BY_OPERATOR_IDENTITY_MISMATCH
BLOCKED_BY_REPLAY_MISMATCH
BLOCKED_BY_LINEARIZATION_FAILURE
BLOCKED_BY_SIGN_MUTATION_SURVIVAL
BLOCKED_BY_RANK_DEFICIENCY
BLOCKED_BY_CONDITION_CEILING
BLOCKED_BY_TRANSFER_UNRESOLVED
BLOCKED_BY_NUISANCE_DEFINITION
BLOCKED_BY_ALIAS_UNCONTROLLED
BLOCKED_BY_HISTORICAL_PARITY_FAILURE
BLOCKED_BY_NULL_EXCHANGEABILITY_FAILURE
NO_ADMISSIBLE_NEW_RESULT
```

A terminal carrying coefficients or plots depends only on output-bearing successful prerequisites.

## 12. Literature anchors

- Ferreira & Quartin, *Physical Review D* **104**, 063503 (2021): Doppler/aberration estimators with realistic beaming, noise, and masks.
- Gruetjen & Shellard, *Physical Review D* **89**, 063008 (2014): masked-sky mode coupling.
- Leung et al., *Astrophysical Journal* **928**, 175 (2022), DOI `10.3847/1538-4357/ac562f`: simulation-derived two-dimensional transfer matrix for attenuation and mode mixing; a scalar `F_ell` can miss mixing and signal-spectrum dependence.
- Wandelt, Hivon & Gorski, arXiv `astro-ph/0008111`: exact cut-sky harmonic coupling framework.
- Notari, Quartin & Catena, arXiv `1304.3506`: partial-sky boost bias.
- Aluri et al., arXiv `1510.02454`: mask-induced correlations and simulated recovery of Doppler-boost anisotropy.

These motivate the architecture but do not validate this repository operator.

## 13. Claim boundary

WU-011 may establish a synthetic or later admitted **processed local-observer boost response operator**. It may not, by itself:

- admit a Planck absolute-temperature product;
- estimate or subtract beta;
- determine global matter-frame tilt;
- exclude foregrounds or spectral distortions;
- calibrate polarization;
- identify a Bianchi family or causal origin;
- promote the PR #441 theorem ledger to formal-dossier replay.

The separate Bianchi photon hierarchy is not a substitute for this processed response: its formula atlas excludes finite electron tilt, recombination/reionization, line-of-sight integration, solver construction, numerical evolution, and inference.

## 14. Validation and review sequence

1. corrected written-design review;
2. separate implementation plan;
3. RED contract commit;
4. bounded production implementation;
5. focused and repository-wide verification;
6. independent PHYS--MATH review;
7. independent PHYS--MATH--CODE review;
8. plot-driven hostile audit;
9. fresh frozen-head read-only review;
10. GitHub--Jira--Confluence--research-workspace readback.

## 15. Spec self-review

- no placeholder remains;
- the actual `fit_joint_cutsky_alm` order is explicit;
- source transfer and post-fit commonization are separated;
- simultaneous nuisance profiling is explicit;
- source-band completeness through `ell=6` is fixed;
- full-sky and processed claims are separated;
- strict-positive temperature, units, signs, and both real-basis conventions are fixed;
- implementation, empirical inference, polarization, global tilt, and Bianchi attribution remain outside this design-only branch;
- the work unit is narrow enough for one implementation plan.
