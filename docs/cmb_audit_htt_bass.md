# CMB Audit for `htt/bass`

Date: 2026-04-22

Scope: `htt/bass`

Prompt source: `docs/cmb_audit.txt`

This document follows the section order required by `docs/cmb_audit.txt` and audits the actual executable state of `htt/bass`, with explicit separation between:

- shipped executable physics,
- registry or contract coverage,
- bounded research surfaces,
- diagnostic-only or proxy outputs,
- and fitting or statistics claims that are not yet enforced end-to-end.

The audit is based on direct code inspection plus targeted runtime tests.

---

## 1. Claim Reconstruction

The strongest claims that `htt/bass` currently makes in code are the following.

- It exposes all 11 Bianchi families at the registry and metadata level through `FamilySpec`, with explicit class label, backend preference, branch policy, gauge, and release metadata. See `htt/bass/background/bianchi_types.py:150-178`.
- It explicitly separates orthogonal global tilt from local observer boost and carries that split into output metadata. See `htt/bass/forward/ver2_solver_output.py:64-107`.
- It treats Tier B as a native production route, not merely a Lowell wrapper. See `htt/bass/runtime/ver2_execution.py:1154-1235`.
- It insists that solver outputs remain observer-neutral and forbids posterior, likelihood, and p-value semantics on the solver output object itself. See `htt/bass/runtime/ver2_execution.py:183-200` and `htt/bass/forward/ver2_solver_output.py:214-245`.
- It ships ver3 gate surfaces for family backend, exact Thomson, output split, and fitting hard stop, which implies a governance model in which readiness is intended to be machine-auditable. See `htt/bass/validation/ver3_gate_stop.py:256-286`.

The weaker but still visible claims are:

- Type I has an exact matrix propagator path.
- Non-Type-I families are represented on bounded approximate propagator families selected from structure constants.
- Exact electron-frame Thomson semantics exist as a contract layer.
- Low-ell observable vectors and live likelihood or posterior bindings exist, but they are caveated and in several places still marked diagnostic-only.

The code does not support the stronger claim that all 11 families already have a fully exact, fitting-ready, full-covariance, off-axis-complete CMB pipeline.

---

## 2. Executable Pipeline Reconstruction

### Tier B production path

The active Tier B execution route is `execute_tier_b_solver(...)` in `htt/bass/runtime/ver2_execution.py:1154-1235`.

The production pipeline is:

1. Build runtime config through `_native_runtime_config(...)`.
2. Build the background monitor through `_build_background_monitor(...)`.
3. Build the visibility source through `_build_visibility_source(...)`.
4. Construct `Ver2TierBIntegrator`.
5. Execute the native hierarchy integration.
6. Convert the native result to observer-neutral solver output with `build_solver_core_output_from_native_result(...)`.
7. Optionally run an executed cutoff campaign.

This is not a thin alias over Lowell. The docstring explicitly states that BF-01B-HCORE replaced the Lowell bridge on the production path and that Lowell is retained outside the production route. See `htt/bass/runtime/ver2_execution.py:1168-1177`.

### Tier A validation path

Tier A remains a validation reference route:

- `execute_tier_a_validation_solver(...)` in `htt/bass/runtime/ver2_execution.py:929-1021`
- uses `LowellBianchiIntegrator`
- emits a Tier-A-labelled observer-neutral reference bundle
- exposes TT, EE, and TE comparison payloads for contrast against Tier B

This is a real and useful cross-check surface, but it is not the production owner.

### Tier A vs Tier B comparison path

`compare_tier_a_to_tier_b(...)` in `htt/bass/runtime/ver2_execution.py:1024-1093` compares:

- `D_ell` channels TT, EE, TE
- ell-grid match
- k-grid match
- preferred-axis delta
- relative L2 and max absolute deltas

That is a meaningful executable audit surface rather than a placeholder.

### Integrator family reality

`IntegratorFamily.IMEX_SPLIT` is declared at the runtime API, but `_resolve_native_solver_method(...)` maps it to:

- solver method `BDF`
- realization string `imex_split_declared_bdf_executor`

See `htt/bass/runtime/ver2_execution.py:683-687`. This means IMEX is declared as a policy surface but not yet realized as an actual split executor.

---

## 3. Physics Implementation Audit

### 3.1 Background evolution

The background path is real. `solve_background_evolution(...)` in `htt/bass/background/evolution.py:155-195` integrates the VER2 S1 background with explicit branch handling and matter closures.

This is not registry-only metadata. It performs actual ODE evolution, computes background history, and feeds the native hierarchy path.

### 3.2 Tilt in the background

The key limitation is that the production background path treats tilted matter through a fixed-velocity closure:

- `TiltedSpeciesRegistryClosure` is explicitly described as a species-backed tilted matter closure with fixed velocity direction in `htt/bass/species/barotropic_closures.py:106-137`.
- the main background solver uses `tilted_barotropic_fixed_velocity` on the tilted branch in `htt/bass/background/evolution.py:181-186`.

There is also a separate exact nonperturbative tilt RHS in `htt/bass/background/nonperturbative_tilt.py:1-25`, but the module itself states that it complements the fiducial integrator, which does not model dynamic tilt. In other words, exact tilt dynamics exist in the repository, but they are not the active production background owner.

### 3.3 Collision / Thomson implementation

The production collision operator in the native path is the projected electron-frame Thomson source:

- `project_thomson_source(...)` in `htt/bass/collision/electron_frame.py:188-277`
- consumed by runtime and native integrator code in `htt/bass/runtime/ver2_execution.py:596-616` and `htt/bass/hierarchy/ver2_native_integrator.py:185-195`

This is a legitimate PSTF collision implementation and explicitly forbids FLRW-only shortcuts. It is not a scalar toy path.

However, the more ambitious exact surface:

- `exact_thomson_source(...)` in `htt/bass/collision/electron_frame.py:343-401`
- `exact_thomson_gate_bundle(...)` in `htt/bass/collision/electron_frame.py:404-420`

is a higher-level contract wrapper over the projected source plus scalar versus directional bookkeeping. That exact surface exists and is tested, but it is not the default owner of the native Tier B production collision loop.

### 3.4 Visibility and reionization

The visibility path is a scalar-history-first-pass contract. `ScalarHistoryMetadata` in `htt/bass/recombination/history_visibility.py:47-70` enforces:

- `reionization_mode` in `{"disabled", "tanh"}`
- `homogeneous_reionization_only=True`
- source scope fixed to `scalar_history_first_pass`

This means reionization support exists, but only in the bounded homogeneous tanh sense. There is no anisotropic or patchy reionization implementation on the current production path.

The solver output metadata is honest about low-z reionization coverage:

- `bounded_live_low_z_delta`
- `unavailable_due_to_runtime_domain`

See `htt/bass/forward/ver2_solver_output.py:280-343`.

### 3.5 Photon, polarization, TCA, and neutrinos

The native integrator is not a fake shell.

`htt/bass/hierarchy/ver2_native_integrator.py:517-615` evolves:

- photon temperature tower,
- photon E tower,
- neutrino tower,
- projected collision source,
- TCA substitution when `Gamma_T / H` is above threshold.

It also stores:

- `startup_manifold_applied`
- `tca_tracker_any_active`
- `neutrino_hierarchy_mode = "full_pstf_with_reduced_summary_export"`

See `htt/bass/hierarchy/ver2_native_integrator.py:729-761`.

This is a real bounded low-ell hierarchy integrator.

### 3.6 Neutrino limitation

The active baseline neutrino background in `htt/bass/species/neutrino.py:1-57` is massless only. A nonzero `m_nu_eV` raises `NotImplementedError`.

So the codebase contains a real neutrino tower surface, but the main shipped species baseline is still massless-neutrino background rather than a fully live massive-neutrino background in the default production route.

---

## 4. Family / Tilt / Boost Coverage Audit

### 4.1 Registry and backend coverage

At the registry and contract level, coverage is strong:

- all 11 families are represented through `FamilySpec`
- preferred backends are assigned
- branch policy metadata is frozen
- release status is `registry-complete`

See `htt/bass/background/bianchi_types.py:150-178`.

But the LOS backend protocol explicitly says:

> This module freezes backend-contract surfaces only. It does not claim that all family-specific numerics are implemented.

See `htt/bass/los/family_backend_protocol.py:1-5`.

This is one of the most important honesty signals in the repository.

### 4.2 Exact versus approximate source propagation

Source propagation is asymmetric across families.

`select_propagator_kernel_family(...)` in `htt/bass/los/ver2_source_propagator.py:189-209` selects:

- `bianchi_i_matrix_exact` for Type I
- approximate family kernels for non-Type-I families

Examples include:

- `class_a_helical_matrix_approx`
- `class_a_semisimple_matrix_approx`
- `class_b_open_matrix_approx`

The default native output builder refuses to call non-Type-I propagation exact when no explicit config is given. See `htt/bass/forward/ver2_solver_output.py:588-597`.

This is a decisive audit point: all-family source propagation is not exact by default.

### 4.3 Tilted branch coverage

Global tilt is a real model branch, not just metadata. The solver output records:

- `global_tilt_contract`
- `bianchi_branch`
- `theory_family`
- explicit separation from local observer boost

See `htt/bass/forward/ver2_solver_output.py:64-107`.

But executable tilt coverage is selective.

The tests in `htt/bass/runtime/test_ver2_tier_b_execution.py:302-395` show:

- orthogonal representative families execute
- tilted V, VII_0, and VIII execute as bounded runtime contracts
- Type I tilted is intentionally blocked and expected to raise `CodazziProjectionError`

This is strong evidence that the code is honest about partial tilted support.

### 4.4 Boost and off-axis limitations

Seed-stage tilt injection in the native integrator only supports axis-aligned directions:

- if the direction is not axis-aligned, `FB-5.2` is raised and the code falls back to orthogonal seed mode
- see `htt/bass/hierarchy/ver2_native_integrator.py:418-429`

Therefore the repository does not yet support generic off-axis boost or fully general tilted mode coupling on the production path.

---

## 5. Observables / Statistics Readiness Audit

### 5.1 Solver output semantics

The solver output is explicitly observer-neutral:

- `observer_neutral = True`
- `forbidden_products = ("posterior", "likelihood", "p_value")`

See `htt/bass/forward/ver2_solver_output.py:220-245`.

This is good scientific hygiene. The solver does not pretend to own the observational statistics layer.

### 5.2 Local boost versus global tilt

Local boost is deliberately not applied upstream:

- `local_boost_contract = "observer_side_only_not_applied_in_bass_output"`
- `tilt_boost_separation = "explicit_nonmerged"`

See `htt/bass/forward/ver2_solver_output.py:64-107`.

This split is technically and conceptually correct, and it is carried all the way into output metadata.

### 5.3 Harmonic outputs

The native Tier B output reconstructs:

- `alm_T`
- `alm_E`
- `alm_B`

from the final PSTF slice using:

- `coefficient_representation = "ver2_native_pstf_final_slice"`
- `angular_representation = "ver2_native_pstf_sphere_reconstruction"`

See `htt/bass/forward/ver2_solver_output.py:629-633`.

That is useful and nontrivial, but it is still a reconstruction layer, not direct proof of full harmonic transport completeness across all families.

### 5.4 ObservableVector readiness

`build_observable_vector_from_solver_output(...)` in `htt/bass/observational/observable_vector_builder.py:190-290` is carefully caveated.

It can return:

- `production_candidate`
- `blocked_missing_covariance`
- `diagnostic_only`

depending on covariance features and sky-support guards.

It also attaches caveats such as:

- `diagonal_cl_not_sufficient_for_directional_claims`
- `no_posterior_or_evidence_semantics`
- `proxy_morphology_not_full_biposh`
- `basis_reduced_covariance_not_full_biposh`

See `htt/bass/observational/observable_vector_builder.py:257-285`.

This means the observable layer is usable for bounded descriptive work, but not yet a clean license for strong inferential claims.

### 5.5 Live likelihood and posterior bindings

The repository does contain live binding code:

- `htt/bass/likelihood/live_binding.py`
- `htt/bass/inference/live_binding.py`

The likelihood binding marks the legacy-shaped decomposition as `diagnostic_only` and explicitly says these helpers do not promote BASS into the model-dependent inference owner. See `htt/bass/likelihood/live_binding.py:1-20` and `htt/bass/likelihood/live_binding.py:188-202`.

However, `htt/bass/inference/live_binding.py:162-239` still builds a live posterior problem and calls `run_posterior(...)` for a Type I native validation problem. This is the largest semantics mismatch in the current stack: the code is operationally capable of running a posterior while the governance layer says fitting must be hard-gated.

---

## 6. Numerical Maturity Audit

The numerical core is meaningfully more mature than a pure prototype.

Evidence:

- native `solve_ivp` stiff solve in `htt/bass/hierarchy/ver2_native_integrator.py:681-695`
- TCA startup manifold and dynamic TCA substitution in `htt/bass/hierarchy/ver2_native_integrator.py:450-460` and `571-615`
- checkpoint and restart support on the Tier B runtime path
- executed cutoff campaign support
- Type I Tier A versus Tier B comparison surface
- deterministic runtime tests

But numerical maturity is still bounded by the runtime policy itself. `RuntimeControlBlock` in `htt/bass/runtime/ver2_execution.py:140-152` enforces development cutoffs `L=4,6,8` unless an explicit diagnostic override is recorded.

That is a very important limitation. The shipped runtime is intentionally low-ell and development-bounded, not an unconstrained production Boltzmann hierarchy engine.

---

## 7. Optimization / Performance Honesty Audit

The repository is mostly honest about performance surfaces.

What is real:

- sparse or reduced covariance summaries,
- checkpoint and resume,
- cutoff campaign tooling,
- TCA-based stiffness reduction,
- runtime metadata that records what actually happened.

What is not yet fully real:

- true IMEX split execution,
- full family-specific operator numerics for every backend surface.

The strongest evidence is `htt/bass/hierarchy/ver3_layout_protocol.py:221-315`, where:

- free-streaming diagonal entries are built from `-0.1 * (ell + 1)`
- next-ell couplings use `0.05`
- mixing uses `0.02` or `0.03`
- implicit block uses plain `gamma_t` diagonals

Those are sensible contract or placeholder operators for shape-correct wiring, but they are not convincing as full physical operator ownership for all families.

Conclusion: optimization claims should be limited to bounded runtime engineering, not sold as evidence of a finished all-family production matrix engine.

---

## 8. Docs / Tests / Release Honesty Audit

The repository is notably better than average at self-limiting its claims.

Evidence:

- `htt/bass/los/family_backend_protocol.py:1-5` explicitly disclaims full family-specific numeric completion.
- `htt/bass/runtime/test_ver2_tier_b_execution.py:302-395` explicitly distinguishes exact Type I from approximate non-Type-I realizations.
- the same test file explicitly expects Type I tilted to be blocked under a Codazzi policy.
- Tier A validation tests in `htt/bass/runtime/test_ver2_tier_a_validation.py:150-222` treat Tier A as a validation-only angular truth surface rather than a production owner.
- output and observable code attach caveats rather than silently promoting themselves to inference ownership.

The main release-honesty gap is not documentation language. It is that the live inference binding is more permissive than the fitting governance model.

---

## 9. CoVe / Contrastive Verification Results

### 9.1 Tests executed

The following test command was run:

```bash
venv/bin/python -m pytest \
  htt/bass/runtime/test_ver2_tier_b_execution.py \
  htt/bass/collision/test_ver3_exact_thomson.py \
  htt/bass/recombination/test_ver3_visibility_adapter.py \
  htt/bass/forward/test_ver3_output_archive.py \
  htt/bass/validation/test_ver3_gate_stop.py \
  htt/bass/los/test_ver3_family_backend_protocol.py \
  -q
```

Result:

- `60 passed`
- `1 warning`
- runtime about recombination table z-range coverage

The following Tier A validation command was also run:

```bash
venv/bin/python -m pytest htt/bass/runtime/test_ver2_tier_a_validation.py -q
```

Result:

- `3 passed`
- `1 warning`

### 9.2 Contrastive validation result

`htt/bass/runtime/test_ver2_tier_a_validation.py:187-222` verifies that, for the shared Type I bridge:

- ell grid matches
- k grid matches
- preferred axis delta is approximately zero
- TT, EE, and TE relative L2 deltas are within tolerance `5e-2`

This supports the narrower claim that the bounded Type I Tier B native path is contrastively anchored against Tier A.

### 9.3 Reionization contrastive surface

The Tier B runtime tests also check the metadata split between:

- `unavailable_due_to_runtime_domain`
- `bounded_live_low_z_delta`

which supports the audit conclusion that low-z reionization claims are explicitly runtime-domain-bounded rather than silently overclaimed.

---

## 10. Ranked Risk Ledger (P0-P3)

### P0

- Fitting hard stop is implemented but not enforced by the live inference path. `hard_gate_before_fitting(...)` exists in `htt/bass/validation/ver3_gate_stop.py:256-286`, but the live posterior binding in `htt/bass/inference/live_binding.py:162-239` builds a posterior problem and runs `run_posterior(...)` without calling the fitting gate.

### P1

- Non-Type-I exact source propagation is not the default executable reality. The default native bridge is approximate for non-Type-I families. See `htt/bass/forward/ver2_solver_output.py:588-597`.
- Production collision uses projected Thomson rather than a separate exact-Thomson owner path. See `htt/bass/collision/electron_frame.py:188-277` and `htt/bass/hierarchy/ver2_native_integrator.py:185-195`.
- Off-axis tilted boost and generic mode transport are not closed. See `htt/bass/hierarchy/ver2_native_integrator.py:418-429`.
- The production tilted background path uses fixed-velocity closure rather than the exact dynamic nonperturbative tilt owner.

### P2

- Reionization is homogeneous tanh only. See `htt/bass/recombination/history_visibility.py:47-70`.
- Massive neutrino baseline is not shipped on the default species path. See `htt/bass/species/neutrino.py:10-12` and `51-57`.
- Observable covariance may be a sparse or proxy representation rather than a full inferential covariance object.

### P3

- Development multipole cutoffs remain narrow.
- Some operator or backend surfaces are clearly contract-first rather than full physics-first.
- Early-time or table-coverage edges still generate warnings in smoke tests.

---

## 11. Top 12 Load-Bearing Risks

1. Live posterior execution bypasses the fitting hard-stop contract.
2. Non-Type-I families do not have default exact source propagation.
3. Projected Thomson is the production collision owner, not a distinct exact owner path.
4. Off-axis boost and generic tilted mode coupling remain deferred.
5. Type I tilted branch is intentionally blocked under current Codazzi projection policy.
6. Production tilted background evolution uses fixed-velocity closure.
7. Reionization support is homogeneous tanh only.
8. Default neutrino background is massless-only.
9. Observable covariance surfaces are often proxies or reduced summaries.
10. Layout protocol operator matrices look template-like rather than fully physical.
11. Declared IMEX is realized as BDF fallback.
12. Runtime policy is still low-ell and development-cutoff bounded.

---

## 12. Minimal Patch / Optimization Plan

The smallest patch set that would materially improve audit status is:

1. Enforce `hard_gate_before_fitting(...)` in `htt/bass/inference/live_binding.py` before any posterior is created or executed.
2. Promote exact versus approximate source-propagator status to a first-class public-facing readiness field and fail closed on unsupported exact requests outside Type I unless an explicit config is supplied.
3. Decide whether production tilt ownership should stay fixed-velocity by policy or be upgraded to integrate the nonperturbative tilt RHS. Either choice should be made explicit and enforced.
4. Close or hard-block the off-axis `FB-5.2` subset so that no approximate fallback can be misread as generic support.
5. Tighten the observable-to-inference boundary so that proxy covariance products cannot be mistaken for full fitting surfaces.
6. If IMEX remains undeployed, rename or annotate the runtime family to avoid confusion between declared API and actual executor.

---

## 13. Final Verdict

`htt/bass` is a real executable Bianchi CMB codebase with meaningful Tier B native physics, explicit observer-neutral output semantics, honest metadata, and a usable Type I validation bridge.

It is not yet a finished all-family exact CMB engine with fitting-ready statistics semantics.

The correct overall label is:

- executable,
- bounded,
- low-ell,
- observer-neutral,
- research-candidate Tier B solver,

with strong registry and governance scaffolding, but still incomplete all-family exactness and incomplete end-to-end fitting enforcement.

---

## 14. Headline Claims Allowed / Not Allowed

### Allowed

- `htt/bass` ships a real native Tier B production route.
- Type I has an exact matrix propagator path.
- Non-Type-I families have bounded approximate propagator families.
- The code explicitly separates global tilt from local observer boost.
- The solver output is observer-neutral and forbids direct likelihood or posterior semantics.
- Reionization and observable-vector surfaces exist in bounded, caveated form.
- A Tier A validation reference exists and can be contrastively compared to Tier B.

### Not allowed

- All 11 families are solved with exact source propagation by default.
- Generic off-axis tilted transport is implemented.
- The live inference path is automatically fitting-gated and production-safe.
- The observable layer is a full-covariance, evidence-ready, fully inferential stack.
- The code ships a true IMEX split executor today.
- The production path currently owns fully dynamic nonperturbative tilt evolution.

---

## 15. One-Line Reason

`htt/bass` is already a serious bounded solver, but its strongest exactness and fitting-readiness contracts still live one layer above the default executable path, especially for non-Type-I families and live inference.

---

## Appendix A: Key Evidence Index

- Family registry coverage: `htt/bass/background/bianchi_types.py:150-178`
- Native Tier B route: `htt/bass/runtime/ver2_execution.py:1154-1235`
- Tier A validation route: `htt/bass/runtime/ver2_execution.py:929-1021`
- Tier A vs Tier B comparison: `htt/bass/runtime/ver2_execution.py:1024-1093`
- Development cutoff policy: `htt/bass/runtime/ver2_execution.py:140-152`
- IMEX to BDF fallback: `htt/bass/runtime/ver2_execution.py:683-687`
- Background production owner: `htt/bass/background/evolution.py:155-195`
- Fixed-velocity tilted closure: `htt/bass/species/barotropic_closures.py:106-137`
- Nonperturbative tilt side module: `htt/bass/background/nonperturbative_tilt.py:1-25`
- Projected Thomson production path: `htt/bass/collision/electron_frame.py:188-277`
- Exact Thomson wrapper surface: `htt/bass/collision/electron_frame.py:343-420`
- Visibility and homogeneous tanh limit: `htt/bass/recombination/history_visibility.py:47-70`
- Native hierarchy integration and TCA: `htt/bass/hierarchy/ver2_native_integrator.py:517-615`
- Native result metadata and neutrino export: `htt/bass/hierarchy/ver2_native_integrator.py:729-761`
- Axis-aligned tilt limitation: `htt/bass/hierarchy/ver2_native_integrator.py:418-429`
- Non-Type-I approximate propagator families: `htt/bass/los/ver2_source_propagator.py:189-245`
- Non-Type-I exact default rejection: `htt/bass/forward/ver2_solver_output.py:588-597`
- Observer-neutral output semantics: `htt/bass/forward/ver2_solver_output.py:214-245`
- Tilt versus boost output split: `htt/bass/forward/ver2_solver_output.py:64-107`
- Reionization runtime metadata: `htt/bass/forward/ver2_solver_output.py:280-343`
- Observable caveats and readiness status: `htt/bass/observational/observable_vector_builder.py:190-290`
- Live inference binding: `htt/bass/inference/live_binding.py:162-239`
- Fitting hard stop: `htt/bass/validation/ver3_gate_stop.py:256-286`
- Backend protocol disclaimer: `htt/bass/los/family_backend_protocol.py:1-5`
- Template-like layout operators: `htt/bass/hierarchy/ver3_layout_protocol.py:221-315`
- Representative orthogonal and tilted execution tests: `htt/bass/runtime/test_ver2_tier_b_execution.py:302-395`
- Tier A validation test and contrastive tolerance: `htt/bass/runtime/test_ver2_tier_a_validation.py:150-222`

## Appendix B: Test Commands Used in This Audit

```bash
venv/bin/python -m pytest \
  htt/bass/runtime/test_ver2_tier_b_execution.py \
  htt/bass/collision/test_ver3_exact_thomson.py \
  htt/bass/recombination/test_ver3_visibility_adapter.py \
  htt/bass/forward/test_ver3_output_archive.py \
  htt/bass/validation/test_ver3_gate_stop.py \
  htt/bass/los/test_ver3_family_backend_protocol.py \
  -q
```

```bash
venv/bin/python -m pytest htt/bass/runtime/test_ver2_tier_a_validation.py -q
```
