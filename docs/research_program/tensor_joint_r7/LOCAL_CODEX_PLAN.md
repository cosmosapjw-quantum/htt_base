# Tensor Joint R7 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Actual scientific execution belongs to the user's workstation Local Codex.

**Goal:** From verified equations and existing producers to calibrated tensor/physical inference with independently terminating hypothesis and data branches.

**Architecture:** Existing obsstat/BASS inputs feed a common typed observation/state contract. HTT owns normalized likelihoods, confidence/posterior calculations and null competition; MIO consumes their supported diagnostic projections. A separate outcome-aware campaign runner schedules the nodes in `campaign_dag.json` and always emits the supported final conclusions.

**Tech Stack:** Existing repository Python/NumPy/SciPy and test environment; existing Rust/CAS/HEALPix only for modules that require them. Keep the established package layout, declared scientific conventions and source identities.

**Spec:** `docs/research_program/tensor_joint_r7/{SCIENTIFIC_CONTRACT,THEORY,DESIGN,REUSE_MAP,OWNED_ASSETS,VALIDATION_MATRIX}.md` and `campaign_dag.json`.

## Global constraints

- Base H=`5702024e06eff4979087f07f86ee7131d13961ac`; integrate selected Q/P/A/D/B donor changes with their tests. Do not treat the default branch as the latest handoff.
- Production implementation and all scientific computation run on the workstation. The R7 publication contains design, not implemented science.
- PR4/NPIPE acquisition and analysis remain excluded. Invalidated DESI PR-151 numerical outputs remain unusable.
- Retain full Q/O and frame; temperature K, orthonormal real harmonics; explicit Re/Im layout conversions. `Theta=3H>0`, vorticity/derivative convention exactly as T3.
- `f_B` is one diagnostic. q0=o0=`1e-5 K` for the registered all-strata distance; k=`ceil(sqrt(N))`. A scale change is a separately logged sensitivity, not an observed-data tuning opportunity.
- Gaussian known-law confidence level95%. If nuisance confidence needs separate coverage, use gamma=.01 and observational alpha=.04 so total alpha=.05. Proper posterior priors are separate model choices; no default posterior is substituted for confidence inversion.
- A scenario/simulator fit is labeled with its law. No metadata flag alone supplies physical response, true covariance, selection or exchangeability.
- Existing native adapter stub stays unavailable. Restricted R3 and supported external transfer are explicitly named providers.
- Every new source function below is **proposed**. Create its implementation/tests only when its DAG capability route is eligible.

## Milestone 1 — Source composition and independent algebra (R7-00/01/02)

**Files:** selectively integrate the exact paths in REUSE_MAP, starting with Q `htt/src/common/mes_krylov_completion.py` and `tests/common/test_mes_krylov_completion.py`; B boost modules; P survey successors; A/D anchor and irrep modules. Create `htt/src/common/r7_asset_use.py` and `tests/r7/test_asset_routes.py` for product-keyed intake/dispositions, then `tests/r7/test_conventions.py` and `tests/r7/test_source_composition.py`.

**Consumes:** pinned source files, actual local product manifests/headers and old handoff source definitions.
**Produces:** separate donor capability records; STF basis/layout conversion; convention fixtures. One donor failure cannot remove another donor's capability.

- [ ] Consume the existing workstation inventory and route every product in OWNED_ASSETS to a named likelihood, conditional law, control, scenario or unavailable subrecord. Do not rescan all storage. Test that WMAP controls continue without PR3, Union3 without JWST, and compressed DESI without raw DESI; none inherits the primary experiment calibration.
- [ ] Resolve each donor against the actual target import tree and record selected path/ref. Preserve conflicting historical functions under their old scope; direct new consumers to the selected implementation.
- [ ] Exercise the out-of-image packet sign-flip fixture against the target import, first confirming the old inverse failure and then the Q repair. Keep existing rotation/scaling/chart-unavailable tests.
- [ ] Add exact basis/trace/moment and T1 witness fixtures; test Re/Im-to-real conversion with one nonzero m>0 coefficient, including its norm.
- [ ] Verify exact L=10 rational certificate and T5 mask identity as separate extended claims. Four-axis CAS certification is a separate capability from basic STF conversion.
- [ ] Run the donor tests plus `python -m pytest tests/r7/test_conventions.py tests/r7/test_source_composition.py -q`; commit only the coherent integration and actual results.

## Milestone 2 — Normalized likelihood and confidence kernels (R7-05)

**Create:** `htt/src/common/r7_contracts.py`, `htt/htt/htt/infer/r7_gaussian_law.py`, `htt/htt/htt/infer/r7_confidence.py`, `tests/r7/test_gaussian_law.py`.

**Interfaces:**
```python
gaussian_acceptance(residual, covariance, alpha, support_tol) -> AcceptanceResult
condition_gaussian(mean_y, mean_z, Cyy, Cyz, Czz, z) -> ConditionalGaussian
conditional_mean_derivative(mu_y_i, mu_z_i, W, W_i, z_minus_mu_z) -> array
calibration_information_gain(U, V, E, G) -> InformationResult
invert_acceptance(law, physical_domain, acceptance_rule) -> PhysicalRegion
```
`AcceptanceResult` has `inside_support`, `quadratic`, `rank`, `threshold`, `accepted`, `numeric_status`. Support tolerance is tied to covariance/error bounds; exact zero eigenvalues are not silently rounded positive. `InformationResult` carries efficient matrices and null directions. Contract classes retain ordered dimensions and scope IDs defined in DESIGN.

- [ ] Write and run the following oracles before implementation:
```python
# Planned assertions; imports become the exact new public API.
assert not gaussian_acceptance([0., 1.], [[1.,0.],[0.,0.]], .05, 0.).inside_support
# x=theta+eta+e, c=eta+nu, var(e)=1, var(nu)=4:
gain = calibration_information_gain([[1.]], [[1.]], [[1.]], [[.25]])
assert abs(gain.new_information[0,0] - .2) < 1e-10
```
- [ ] Implement Gaussian conditioning, singular support and T4/T6 derivatives. Test exact duplicate `z=y` support and the exact `y-z=theta` correlated-noise oracle.
- [ ] Implement fixed Gaussian confidence inversion with chi-square rank and physical-domain restrictions; independently verify the coverage argument, not a Wilks degrees-of-freedom shortcut.
- [ ] Run `python -m pytest tests/r7/test_gaussian_law.py -q`; record unsupported nonlinear likelihoods as separate adapters.

## Milestone 3 — CMB response and full-orbit analysis (R7-04/06/11)

**Reuse:** carrier rebuild, B finite thermal pullback/boost_response, D processed error envelope. **Create:** `htt/obsstat/r7_cmb_product_response.py`, `htt/obsstat/r7_tensor_orbit.py`, `tests/r7/test_cmb_product_response.py`, `tests/r7/test_tensor_orbit.py`.

**Interfaces:**
```python
build_product_response(product_spec, source_spec, beta, processing_policy) -> ProductResponse
build_tensor_record(retained_row, measurement_meta, covariance_provider) -> TensorRecord
orbit_distance_bounds(Q, O, Qp, Op, q0, o0, rotation_cover) -> DistanceInterval
orbit_pool_scores(records, k, q0, o0, tolerance) -> ScorePool
```
`DistanceInterval` supplies a certified lower/upper bound and convention/error identity. `ScorePool` retains every input sample ID and finite scores or a typed numerical-unresolved status.

- [ ] Verify beta0, generator sign, Q-to-O response and finite monopole quadrupole with absolute positive temperature. Fit ell0..5 at NSIDE64 pixel centers before retaining2..5.
- [ ] Bind actual product correction, units, channel weight/temperature convention, beam and mask. Produce only `THERMAL_RESPONSE` until the released product experiment is justified.
- [ ] Retain full Q/O and covariance for every row. Add measured high modes with their cross-covariance; do not load them as independent constraints.
- [ ] Implement T1 objective with proper rotations only. Certify grid covering radius and scalar evaluation error or label a diagnostic approximation. Use eigenframe starts/local optimization only to improve upper bounds.
- [ ] Test exact rotation equivalence, the chiral chi0 witness, zero tensors, repeated eigenvalues, row permutation and tied kNN distances. Run `python -m pytest tests/r7/test_cmb_product_response.py tests/r7/test_tensor_orbit.py -q`.

## Milestone 4 — Four nuisance branches and same-state MES (R7-03/12/13)

**Create:** `htt/htt/htt/infer/r7_high_source.py`, `htt/src/common/r7_radiation_jet.py`, `htt/htt/htt/infer/r7_mes_region.py`, `tests/r7/test_high_source.py`, `tests/r7/test_mes_region.py`. Reuse A/D anchor/normalizer/response and H GF solvers.

**Interfaces:**
```python
cancellation_cost(K, S, d, range_tolerance) -> CostResult
profile_high_source(y, A, K, noise, policy, theta) -> ProfileResult
kinematics_from_radiation_jet(jet) -> PhysicalState
build_mes_region(experiment, jet_domain, model_domain, alpha_budget) -> PhysicalRegion
project_joint_region(region, functional, certified_bound_provider) -> ProjectionResult
```
`CostResult` has finite cost or infinity with a range witness. `ProjectionResult` explicitly separates certified outer bounds, feasible inner witnesses, unbounded/undefined states and unresolved numeric error. For nonlinear domains require an interval/convex-relaxation bound provider; if unavailable return unresolved outer range, not the local optimizer's inner range as confidence.

- [ ] Test center rho versus pairwise2rho with scalar K=S=1, rho1 and displacement2: center infeasible, pairwise overlap at boundary.
- [ ] Implement H0 quotient, H1 ellipsoid/positive-sky intersection, H2 full marginalized law and H3 joint measurement law, each with its coverage target.
- [ ] Implement T3 in propagation and outward conventions; test their equality and derivative of Q/Tbar. Keep missing jets typed.
- [ ] R7-13 consumes both direct admitted laws and R7-17 model-bound laws; the latter route settles after17. Implement the generic method here, but execute each instance only on its qualified law scope.
- [ ] Project tensor norms/orientations and registered F/G from the same accepted physical states. Use existing exact affine-box GF only where its hypotheses hold.
- [ ] Run `python -m pytest tests/r7/test_high_source.py tests/r7/test_mes_region.py -q`; record new mask or envelope tests independently of observed eligibility.

## Milestone 5 — Three catalogue adapters (R7-07/08/09, parallel)

**Create:** `htt/htt/htt/infer/r7_cf4_law.py`, `r7_desi_law.py`, `r7_jwst_law.py`, and `tests/r7/test_catalogue_laws.py`. Reuse exact existing producers from REUSE_MAP.

**Interfaces:** `build_cf4_law(product, selection, calibration, physical_provider=None)`, `build_desi_law(product, randoms, matched_mocks, selection)`, `build_jwst_law(host_products, covariance, calibration, measurement_family)` each returns a fully bound `JointObservationLaw`, a sealed `ObservationLawFactory` with named unfilled prediction slots, or a scoped unavailable/scenario result. A factory has no empirical eligibility. R7-10 composes factories; R7-17 binds them to supported physical providers before R7-18/19. The conditional CF4 affine law is already bound and does not wait for a native provider.

- [ ] CF4: bind original row/group order and full covariance; validate P affine design. If raw selection/calibration is supplied, implement DESIGN's normalized latent distance law; otherwise select the explicitly conditional affine experiment and withhold raw-law capability. Test radial antisymmetric null response.
- [ ] DESI: use P sample and18-vector definitions, refit normalization/nuisance in every mock, verify frame/window/weight law, rerun from permitted raw inputs. No old PR151 number enters the test or fit target.
- [ ] JWST: retain host distribution and measurement-family distinction; test shared geometry cancellation and exact covariance support. Retain absolute rows only once. Do not infer a competitor amplitude from a preparation function that does not fit one.
- [ ] Run P existing CF4/JWST integration tests and `python -m pytest tests/r7/test_catalogue_laws.py -q`. Each adapter commits independently; missing one catalogue does not prevent others.

## Milestone 6 — Shared calibration and depth (R7-10/14)

**Create:** `htt/htt/htt/infer/r7_joint_experiment.py`, `r7_depth_response.py`, `tests/r7/test_joint_experiment.py`.

**Interfaces:**
```python
compose_joint_law(laws, overlap_table, shared_latent_provider) -> ExperimentPartition
depth_response(z, directions, background, frame_policy) -> ResponseBlock
analyze_identifiable_combinations(law, theta, eta, error_budget) -> IdentificationResult
```
`ExperimentPartition` lists admitted joint/subset laws and unresolved cross-links; it is not permission to multiply unknown-dependent subsets. `IdentificationResult` includes singular spectrum, kernel, feasible region and actual parameter labels.

- [ ] Verify duplicate measurements add no information; shared calibration variance and covariance match V16. Match identity by object/product evidence, not positions alone.
- [ ] Implement exact R3 low-speed depth kernels, single-shell/constant-H degeneracy and full nuisance projection. Use source/observer frames consistently in raw distance law.
- [ ] When only cross-probe dependence is unavailable but marginal laws/coverage share the same estimand, construct the OWNED_ASSETS union-bound intersection with fixed alpha allocation. Missing marginal coverage contributes the full parameter domain. Keep alternative model-law regions unioned instead.
- [ ] Compute information increments from the full joint law, not marginal interval shrinkage or host counts. Return calibration-only estimands when physical response cancels.
- [ ] Run `python -m pytest tests/r7/test_joint_experiment.py -q`; publish scope-keyed results and supported data partitions.

Before physical-provider work, implement P0/P1 comparisons on already bound direct experiments using the fixed columns in DESIGN. These comparisons proceed even if both physical providers are absent.

## Milestone 7 — Restricted dynamics and selected external physics (R7-15/16/17, optional parallel providers)

**Create:** `htt/bass/transfer/r7_benchmark_provider.py`, `r7_external_provider.py`, `tests/r7/test_physical_providers.py`. Reuse H dust/matter/transport/Thomson and existing external adapter conventions. Preserve `native_adapter.py` stub.

**Interfaces:** `provider.capabilities()`, `provider.predict_harmonics(parameters, initial_conditions, observer)`, `provider.predict_distance(parameters, source, observer, direction, redshift)`, `provider.radiation_jet(event)`; missing channels raise a typed `UnsupportedObservable` and are never zero-filled.

- [ ] Select review87 `bianchi/matter/freestream.py::moments` with its existing Bose–Einstein function and `bianchi/rays/optical.py` screen/Jacobi mechanics before writing replacement code. Adapt the background derivatives to the actual R3 stress history; retain exact selected member and license.
- [ ] Bind R3 conserved momenta and source stress in proper units. Add its collisionless photon stress integral and Jacobi distance using `R3_MODEL_REFERENCE.md` equations, not a perfect-fluid substitution.
- [ ] Test Hamiltonian/energy/flux, dust FLRW, screen/Jacobi invariants, normal odd-mode and vorticity nulls. Use legacy inconsistent rapidity/Thomson equations only as negative fixtures.
- [ ] Validate supported external reference modes and identify metric beta_ij versus rate shear. Register stochastic additive approximation separately from anisotropic covariance response.
- [ ] Run `python -m pytest tests/r7/test_physical_providers.py -q`. Failure holds only that provider; CMB morphology, catalogue estimands and conditional MES continue.

## Milestone 8 — Matched calibration and observed execution (R7-18/19)

**Create:** `htt/htt/htt/infer/r7_calibration.py`, `scripts/observed_runs/run_tensor_joint_r7.py`, `tests/r7/test_calibration_scopes.py`. Reuse fixed-pool manifests and existing mock/refit machinery only after its actual law is bound.

**Interfaces:**
```python
calibrate_method(method, experiment, null_design, stress_design) -> CalibrationRecord
run_observed_scope(method, experiment, calibration) -> BranchResult
robust_union_pvalue(valid_model_pvalues) -> float
```
The scope key is `(experiment_id, law_id, model_id, dataset_ids, conventions, version, method_id, method_config_id)`. Configuration binds the statistic, scales/k, acceptance level, nuisance policy and fitting/selection procedure. `CalibrationRecord` also supports `EXACT_ACCEPTANCE_PROOF` with a domain and numerical obligations; this qualifies only that exact method. Unbound factories cannot supply it. It also carries exact/approximate validity, conditioning target and supported parameter domain. An experiment outside that domain is not eligible.

- [ ] Test wrong-scope calibration rejection, ties, NaN refusal, complete row selection symmetry and robust p(.01,.40)=.40. Keep within-law max statistic distinct from across-law supremum.
- [ ] Use fixed10000 independent synthetic trials per declared cell for operational stress and report CP intervals/power/refusal. Actual product nulls retain their actual pool limits and dependency law.
- [ ] Construct confidence regions with valid outer bounds and nuisance coverage allocation. If nuisance supremum is only a grid lower approximation, record unresolved robustness.
- [ ] Analyze every eligible real-data scope, retaining all failed/nonidentified branches. Do not transfer a synthetic-only calibration to the actual product. Run `python -m pytest tests/r7/test_calibration_scopes.py -q` before the observed driver.

## Milestone 9 — Outcome-aware campaign runner and synthesis (R7-20…25)

**Create:** `scripts/observed_runs/run_r7_campaign.py`, `tests/r7/test_campaign_routing.py`; build manuscript/results through existing report tools.

**Interfaces:** `settle_node(node, predecessor_results) -> BranchResult`, `synthesize_campaign(results) -> ConclusionPackage`. The delivered `validate_campaign.py` is a structural design validator, not this scientific executor.

- [ ] Implement DESIGN's settle-route-scope semantics. Node exceptions and no-route cases emit terminal records. Keep separate donor and experiment capabilities.
- [ ] Test optional decoder failure with surviving tensors, conditional CF4-only admission, native failure with surviving P0/P1/morphology/CF4, absent DESI with valid remaining subsets, missing shared covariance, wrong-scope calibration, failed extended mask proof with intact elementary STF, and every input unavailable. Every case must reach final honest synthesis.
- [ ] Produce the required plots and residual-error/hostile audits from actual results. A final summary may succeed while particular science outcomes remain rejected, nonidentified or unavailable.
- [ ] Write the R1/R2/A1-bound methods manuscript, a separate integrated-data result when supported, and the next minimal discriminator. Mark only actually executed DAG states complete.
- [ ] Run `python -m pytest tests/r7/test_campaign_routing.py -q` and the relevant completed milestone tests. Commit the scientific result and its actual validation record together.

## Local restart prompt

Read this plan, SCIENTIFIC_CONTRACT, DESIGN, REUSE_MAP, VALIDATION_MATRIX and the current `campaign_dag.json`. Restore the H-based R7 branch and inspect its latest handoff amendment. Apply the attached physmath coding harness at implementation layer with current repository AGENTS. Start R7-00 inventory and source binding, then parallelize independently eligible milestone tasks. Preserve all previous PR status/history. Do not ask for a new scientific choice where this contract provides an exact branch; use the unavailable/scenario outcome when its required physical input is absent. Request new theory only for a concrete in-domain counterexample or an unprovided physical response that the user elects to pursue.
