# PMG-WU-011 processed cut-sky local-boost response — design

## 1. Status and approval boundary

This is a **design-only stacked successor** to PMG-WU-010. It adds no production implementation, no RED tests, no raw-data access, no observed statistic, and no claim promotion.

Implementation must not begin from this branch until the design has been reviewed. After approval, the next artifact is a separate test-first implementation plan.

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
jira_owner: BASS-21
confluence_plan: 21823493
confluence_theory_seed: 22151174
research_workspace: 1-n_oX1tLHvoova1Jdlh8Xn0EXJxM_HiPjjAeEPE9Rq4
```

The PR #441 theorem ledger remains `USER_SUPPLIED_SUMMARY / FORMAL_DOSSIER_PENDING`. WU-010 and WU-011 bounded algebra or numerical tests are not a replay of P01–P27.

## 3. Scientific objective

Construct and validate the processed low-ell coefficient response of a finite **local observer Lorentz boost** after the repository's actual ordered mask, beam/pixel, filtering, nuisance, and joint cut-sky estimation operations.

The target is a content-bound synthetic response operator and diagnostic envelope. It is not an observational velocity measurement.

The ordered data path is

```text
positive absolute thermodynamic-temperature sky
  -> exact finite local observer boost
  -> fixed target-frame mask / support
  -> source-to-target beam and pixel transfer
  -> declared filtering and nuisance projection
  -> joint real-harmonic l=0..5 cut-sky solve
  -> retained l=2..5 carrier
  -> optional l=2,3 STF/orbit morphology
```

The order is part of the contract. No operator may be commuted, omitted, or commonized without a new content identity and an explicit differential diagnostic.

## 4. Fixed conventions

- spacetime metric: `(-,+,+,+)`;
- photon momentum: `p^a=(epsilon/c)(u^a+e^a)`;
- outward observer-sky direction: `n^a=-e^a`;
- boosted observer: `u_tilde^a=gamma(u^a+beta^a)`;
- dimensionless local velocity: `beta^a=v^a/c`, with `beta^2<1`;
- scalar observable: strictly positive thermodynamic blackbody temperature, Doppler weight `d=1`;
- harmonic convention: orthonormal Condon–Shortley;
- stored-real layout: `(a_l0, Re a_l1, Im a_l1, ..., Re a_ll, Im a_ll)` without hidden `sqrt(2)` rescaling;
- local observer boost is distinct from global matter-frame tilt, electron-frame collision kinematics, and Bianchi geometry.

The processed response must preserve explicit temperature units. `beta`, condition numbers, relative singular floors, and normalized residuals are dimensionless.

## 5. Load-bearing mathematical contract

Let

- `S_abs` construct an admitted positive absolute-temperature sky;
- `B_beta` be the exact WU-010 finite local boost;
- `G_beta` be its first-order generator;
- `P` be the frozen ordered processing operator;
- `H_ret` return the retained `l=2..5` stored-real carrier.

Define

```text
R_proc(beta) = H_ret P B_beta S_abs,
R_proc(0)    = H_ret P S_abs,
G_proc(beta) = H_ret P G_beta S_abs.
```

The finite-to-linear gate is

```text
||R_proc(beta)-R_proc(0)-G_proc(beta)|| = O(|beta|^2)
```

on a preregistered beta grid and fit interval.

### 5.1 Transfer noncommutation

For a diagonal harmonic transfer `D_b`,

```text
(D_b a)_{lm}=b_l a_{lm},
[D_b,G]_{l'm',lm}=(b_{l'}-b_l)G_{l'm',lm}.
```

Therefore a nonconstant beam, pixel window, or diagonal filter generally differs at first order when applied before versus after a boost.

### 5.2 Mask transport

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

A sharp binary mask has a distributional boundary contribution. The implementation must use the finite pixelized mask directly or a declared apodized surrogate; it must not treat a binary mask derivative as an ordinary smooth function.

### 5.3 Factored processing commutator

If

```text
P=P_nuisance P_filter P_transfer P_mask,
```

then

```text
[P,G]
 = P_nuisance P_filter P_transfer [P_mask,G]
 + P_nuisance P_filter [P_transfer,G] P_mask
 + P_nuisance [P_filter,G] P_transfer P_mask
 + [P_nuisance,G] P_filter P_transfer P_mask.
```

This exact product rule defines the component-removal mutation lanes. It is a diagnostic decomposition, not permission to reorder the physical pipeline.

## 6. Architecture choice

### Recommended: hybrid finite pixel-space reference plus coefficient-level Jacobian

1. **Finite reference path.** Execute the exact WU-010 field pullback on a synthetic positive sky, then run the existing ordered map-processing and joint cut-sky estimator.
2. **Linear response path.** Evaluate the processed first-order generator on the same source sky and operator.
3. **Coefficient Jacobian.** Build a bounded response matrix by injecting a frozen basis of source carrier and out-of-band modes along three Cartesian beta directions.
4. **Differential audit.** Compare the finite reference, linear response, and response matrix over the preregistered beta grid.

This approach is recommended because it gives an exact finite oracle while producing the coefficient-level object needed by later inference. It does not assume that a scalar transfer function captures processing-induced mode mixing.

### Rejected as primary: analytic full-sky kernel followed by scalar transfer

This fails whenever transfer coefficients vary across boost-coupled modes or the mask/filter creates additional mode mixing.

### Rejected as primary: Monte Carlo-only black-box calibration

Simulation-only calibration can hide convention, operator-order, rank, and sign errors. Simulations remain useful as a validation layer after the exact finite and first-order paths agree.

## 7. Proposed types and module boundaries

No public API is frozen by this design, but implementation should preserve the following separation.

### `PositiveAbsoluteSkySpec`

Owns the monopole, retained carrier, optional higher-mode content, units, harmonic convention, and positivity certificate. It must refuse nonpositive samples; clipping is forbidden.

### `ProcessedBoostOperator`

Owns exact identities for mask, beam, pixel windows, filtering, nuisance projection, joint cut-sky estimator, retained layout, thresholds, and processing order.

### `ProcessedBoostEvaluation`

Carries one finite or first-order retained carrier together with source/operator IDs, beta, residuals, and refusal metadata.

### `ProcessedBoostResponseReceipt`

Carries the coefficient response matrix, source basis, singular spectrum, condition number, alias blocks, nuisance rank, mutation results, plot identities, and terminal state.

The new module must call the existing WU-010 APIs and `planck_pr3_operator` interfaces rather than duplicating their formulae. Historical `boost_biposh_residual.ExactBoostOperator` remains a separate fixed-axis parity oracle.

## 8. Work lanes

### W11-A — authority and schema freeze

Freeze predecessor heads, module identities, operator order, stored-real layout, thresholds, terminal states, and claim firewall.

### W11-B — synthetic positive-sky constructor

Construct a positive monopole plus controlled `l=2`, optional `l=3`, and registered higher-mode probes. Record exact harmonic content and positivity margin.

### W11-C — zero-boost identity

Require `R_proc(0)` to reproduce the existing no-boost processed estimator. Any changed predecessor output is a blocking regression.

### W11-D — finite-to-linear convergence

Use a frozen beta grid. Fit the residual slope only on a preregistered interval; require a stable scaled residual plateau.

### W11-E — sign mutation

Flip `n=-e` to `n=e`, flip beta, and separately omit the boost-induced dipole. Each mutation must leave an `O(|beta|)` failure.

### W11-F — mask/beam/pixel/filter sensitivity

Remove or alter exactly one processing component per mutation and bind the changed operator identity. Compare sharp and apodized masks.

### W11-G — out-of-band aliasing

Inject registered modes above `l=5` and construct the leakage block into the retained carrier. Separate exact boost mixing from processing aliasing.

### W11-H — nuisance projection

Keep monopole/dipole handling explicit. Measure the projected response rank and verify that the boost-induced dipole is not deleted before the declared projection.

### W11-I — historical fixed-axis parity

Compare with `boost_biposh_residual.ExactBoostOperator` only on its declared fixed-axis overlap domain and matched transfer convention. No silent substitution is allowed.

### W11-J — finite-null and inference design

Preregister how operator uncertainty, response conditioning, same-sky dependence, and row-equivariant processing enter any later finite rank or identified set. No observed rank is computed in the initial synthetic work unit.

## 9. Mandatory RED-first tests

The implementation plan must start with failing tests for:

1. missing production processed-response module;
2. moved authority or operator identity;
3. nonpositive absolute temperature;
4. zero-boost predecessor replay;
5. finite-to-linear `O(beta^2)` order;
6. wrong-sign `O(beta)` mutation survival;
7. transfer-order noncommutation;
8. mask-boundary sensitivity;
9. out-of-band alias block;
10. nuisance rank and induced-dipole handling;
11. historical fixed-axis parity;
12. typed terminal and claim-firewall rejection.

The RED state must be recorded before production code is added.

## 10. Diagnostics and plots

At minimum:

- zero-boost coefficient residual;
- finite-to-linear log-log residual and scaled plateau;
- correct versus sign-mutation separation;
- singular values and condition number;
- response matrix heatmap;
- out-of-band leakage heatmap;
- mask, beam, pixel, filter, and nuisance differential table;
- sharp versus apodized mask response;
- historical fixed-axis parity residual.

Every plot must be generated at registered dimensions and included in the receipt manifest with SHA-256.

## 11. Typed terminal states

```text
PASS_SYNTHETIC_PROCESSED_RESPONSE
BLOCKED_BY_MOVED_AUTHORITY
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

A terminal carrying coefficients or plots may depend only on output-bearing successful prerequisites.

## 12. Literature anchors

- Ferreira & Quartin, *Physical Review D* **104**, 063503 (2021): Doppler/aberration estimators with realistic beaming, noise, and masks.
- Gruetjen & Shellard, *Physical Review D* **89**, 063008 (2014): masked-sky mode coupling.
- Leung et al., *Astrophysical Journal* **928**, 175 (2022), DOI `10.3847/1538-4357/ac562f`: simulation-derived two-dimensional transfer matrix for attenuation and mode mixing.
- Wandelt, Hivon & Gorski, arXiv `astro-ph/0008111`: exact cut-sky harmonic coupling framework.
- Notari, Quartin & Catena, arXiv `1304.3506`: partial-sky boost bias.

These papers motivate the architecture but do not validate this repository's specific operator. Repository-specific response and claim gates remain mandatory.

## 13. Claim boundary

WU-011 may establish a synthetic or later admitted **processed local-observer boost response operator**. It may not, by itself:

- admit a Planck absolute-temperature product;
- estimate or subtract beta;
- determine global matter-frame tilt;
- exclude foregrounds or spectral distortions;
- calibrate polarization;
- identify a Bianchi family or causal origin;
- promote the PR #441 theorem ledger to formal-dossier replay.

## 14. Validation and review sequence

1. written design review;
2. separate implementation plan;
3. RED contract commit;
4. bounded production implementation;
5. focused and repository-wide verification;
6. independent PHYS–MATH review;
7. independent PHYS–MATH–CODE review;
8. plot-driven hostile audit;
9. fresh frozen-head read-only review;
10. GitHub–Jira–Confluence–research-workspace readback.

## 15. Spec self-review

- no `TBD` or `TODO` remains;
- the processing order is explicit;
- full-sky and processed claims are separated;
- strict-positive temperature, units, signs, and stored-real conventions are fixed;
- implementation, empirical inference, polarization, global tilt, and Bianchi attribution remain outside this design-only branch;
- the work unit is narrow enough for one subsequent implementation plan.