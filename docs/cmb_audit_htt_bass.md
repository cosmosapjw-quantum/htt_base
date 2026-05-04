# CMB Audit for `htt/bass`

Date: 2026-05-01

Scope: `htt/bass`

Prompt source: `docs/cmb_audit.txt`

This document follows the section order required by `docs/cmb_audit.txt` and audits the actual executable state of `htt/bass`, with explicit separation between:

- shipped executable physics,
- registry or contract coverage,
- bounded research surfaces,
- diagnostic-only or proxy outputs,
- and fitting or statistics claims that are not yet enforced end-to-end.

The audit is based on direct code inspection plus targeted runtime tests.

2026-05-01 re-audit delta: this file now reflects the post-patch executable
state. The live fitting path is hard-gated, output split readiness requires an
explicit stochastic channel, Planck low-ell TT likelihood is FLRW-only and
file-backed, visibility interpolation is shape-preserving, IMEX fallback use is
reported in solver metadata, tilted Thomson headline claims require a full
electron-frame Stokes authority path, and the angular Mueller-integral Stokes
authority path is now executable and gate-auditable separately from the
projected PSTF runtime collision loop.

2026-05-01 second re-audit delta: the Tier-B runtime default
`tilt_background_owner` is now `nonperturbative_tilt_rhs`. Tilted background
runs use the dynamic King-Ellis rapidity closure by default; the old
fixed-velocity closure remains available only as an explicit legacy diagnostic
owner. Source-propagator readiness now checks its own operator/provenance/layout
gates independently from the fitting hard-stop ladder, so a closed exact
Thomson fitting gate cannot falsely downgrade a family backend that is otherwise
operator-ready.

2026-05-03 re-audit delta: the tilted full-Stokes runtime collision now
projects `Q/U` through a spin-weighted harmonic `E/B` projection kernel, closing
the earlier scalarized polarization projection gap inside the restricted
collision/RHS envelope. The FLRW low-ell spectrum path now assembles TT, EE, and
TE from the same BASS transfer grid and can export an `ell/cl_*/d_*` archive for
CAMB plotting. This is an output-schema improvement, not a CAMB-agreement or
statistics-ready claim; the TT/EE/TE external CAMB harness remains xfailed until
the Python PSTF closure reaches the external tolerance.

2026-05-03 second re-audit delta: deep pre-recombination FLRW/Tier-B starts no
longer see a silent `Gamma_T=0` outside the HyRec fixture. The baryon species
now has a fully-ionized `x_e=1+2f_He` analytic Thomson opacity fallback above
the table ceiling; tilted visibility, auxiliary `Gamma_T_at`, seed `tau_c`,
TCA gating, and runtime scalar visibility fast paths route to that authority
path. `FLRWPipelineConfig.superhorizon_x_max_at_start` can raise per-k
`z_injection` so regular adiabatic seeds are injected with
`k eta_init <= x_max`; shared-background k chunking is disabled in that mode.
A direct smoke at `k=0.05`, `L=4`, `n_output=12`, `x_max=0.1` selected
`z_injection≈2.304e5`, satisfied `k eta_init≈0.1`, and returned finite TT/EE
transfer arrays. This closes a real startup/opacity physics gap, but it does
not close the external CAMB TT/EE/TE agreement gate.

2026-05-03 third re-audit delta: native Tier-B runs now preserve the regular
seed matter/metric extras (`delta_b`, `theta_b`, `delta_c`, `theta_c`,
`eta_cov`, `Z`) in `IntegrationResult.solver_info`. The FLRW source extractor
also has an opt-in MB-95 diagnostic reconstruction of synchronous `etak/sigma`
using the Rust-oracle momentum/stress metric ODE. That path is deliberately not
the production default: a direct smoke showed that inserting post-hoc MB-95
metric variables into a Tier-B photon history that was not co-evolved with the
MB-95 monopole source silently changes the transfer physics. The production
source frame therefore remains the explicit PSTF/Newtonian-constraint path
until scalar metric variables are co-evolved in the Tier-B state.

2026-05-03 fourth re-audit delta: an opt-in native Tier-B scalar-metric path now
does co-evolve MB-95 synchronous `(etak, sigma)` as part of the main state. The
runtime initializes `etak=-k eta_cov/2` from the regular seed, evolves
`etak_dot=dgq/2` and `sigma_dot=-2Hsigma-dgs/k+etak`, injects `-h_dot/6` into
photon and neutrino monopoles, injects the MB-95
`h_dot/15 + 2*etak_dot/(5*k)` source into photon and neutrino quadrupoles, and
uses `-k v - h_dot/2` for baryon/CDM continuity. The same coevolved path now
adds the MB-95 baryon Euler pressure-gradient term
`c_s,b^2*k*delta_b`, where `c_s,b^2` is computed from HyRec matter
temperature and ionization history with a fully-ionized early fallback.
Source extraction treats `IntegrationResult.scalar_metric_history` as the
MB-95 authority only when metadata proves the monopole, quadrupole,
matter-continuity, and baryon-pressure couplings were active. The older
neutrino-quadrupole temperature-feedback helper is
superseded on this path to avoid duplicate metric sourcing. Requests that
combine this path with IMEX are automatically routed to full-RHS BDF
(`native_scalar_metric_bdf_full_rhs`) until an IMEX scalar-metric implicit
block and error estimator exist. This is a genuine physics implementation
step, but remains restricted-envelope: the external CAMB TT/EE/TE comparison is
still not passing and no statistics-ready claim opens.

2026-05-03 fifth re-audit delta: the native Tier-B RHS also now has a separate
opt-in `IntegratorConfig.co_evolve_scalar_streaming=True` path for the MB-95
scalar m=0 photon/neutrino intensity free-streaming recursion,
`Theta0_stream=-k*Theta1` and
`Theta_l_stream=k/(2l+1)*(l*Theta_{l-1}-(l+1)*Theta_{l+1})`. The formula is
unit-tested and can run in short scalar-metric probes, but a full-range FLRW
smoke exposed BDF/TCA/cutoff instability. It therefore defaults to disabled and
is recorded as a development-envelope physics path, not as output-ready or
statistics-ready evidence.

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
- Exact electron-frame Thomson semantics exist both as the projected PSTF
  runtime collision layer and, for authority checks, as a full angular
  electron-frame Stokes Mueller-integral path.
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

### FLRW low-ell spectrum export path

`compute_flrw_d_ell(...)` and `compute_flrw_d_ell_linear_probe(...)` in
`htt/bass/spectrum/flrw_pipeline.py` now return `cl_tt`, `cl_ee`, `cl_te`,
`d_tt`, `d_ee`, and `d_te` from one transfer-function grid.  The cross spectrum
uses the standard same-grid integral `4π ∫ dlnk P_R(k) Δ_T(k) Δ_E(k)` through
`assemble_cl_TT_EE_TE_isotropic_from_grid(...)`; it is not a separate fitted
source.  `scripts/export_flrw_lowell_pstf_spectrum.py` writes these arrays to an
NPZ archive or to resumable transfer chunks that are later assembled by the same
`C_l` path. `scripts/compare_flrw_lowell_pstf_to_camb.py` writes a per-channel
TT/EE/TE residual JSON report, and `scripts/plot_flrw_lowell_camb_comparison.py`
can overlay that archive against the shipped CAMB reference.

This is output-ready plumbing.  It remains below statistics-ready because
`htt/bass/spectrum/test_flrw_external_camb.py` intentionally keeps the TT/EE/TE
CAMB comparison as an xfail until the Python PSTF normalization and seed-history
closure is actually solved.

The same pipeline now exposes startup controls for physical early starts:

- `z_injection` and `pre_recombination_margin_mpc` are explicit
  `FLRWPipelineConfig` fields and CLI metadata in
  `scripts/export_flrw_lowell_pstf_spectrum.py`.
- `superhorizon_x_max_at_start` resolves a per-k injection redshift from the
  FLRW background table to enforce `k eta_init <= x_max`.
- Shared-background k chunking is intentionally disabled under that option
  because different k values can require different background/visibility
  anchors.

This is a solver-startup validity control. It is not an optimization claim and
not evidence that the current Python PSTF transfer functions match CAMB.

### Integrator family reality

`IntegratorFamily.IMEX_SPLIT` now resolves to the native
`IMEX_MIDPOINT_BDF` split executor on the Tier-B route. The solver records:

- `executor_realization = native_imex_midpoint_bdf_split`
- `solver_family_realization = native_imex_midpoint_bdf_split`
- accepted IMEX step bounds
- `imex_full_rhs_fallback_used`

The remaining audit condition is not whether IMEX exists, but whether any
full-RHS fallback or benchmark comparison is declared honestly before an
optimization claim is made.

---

## 3. Physics Implementation Audit

### 3.1 Background evolution

The background path is real. `solve_background_evolution(...)` in `htt/bass/background/evolution.py:155-195` integrates the VER2 S1 background with explicit branch handling and matter closures.

This is not registry-only metadata. It performs actual ODE evolution, computes background history, and feeds the native hierarchy path.

### 3.2 Tilt in the background

The production tilted-background owner has been upgraded. The default
`RuntimeControlBlock.tilt_background_owner` is now `nonperturbative_tilt_rhs`,
and `_build_background_monitor(...)` routes nonzero-tilt runs through
`integrate_tilt_rapidity_history(...)` plus
`DynamicTiltedSpeciesRegistryClosure`. The output metadata records:

- `tilt_background_owner_requested = "nonperturbative_tilt_rhs"`
- `tilt_background_owner = "nonperturbative_tilt_rhs"` for tilted runs
- `tilt_background_owner = "orthogonal_zero_tilt"` for zero-tilt runs
- `tilt_background_owner_status = "production_dynamic_nonperturbative_rapidity"`
  on the tilted branch

The old `TiltedSpeciesRegistryClosure` fixed-velocity closure still exists, but
it is now an explicit legacy diagnostic owner selected by
`tilt_background_owner="fixed_velocity_closure"` and reported as
`legacy_fixed_velocity_closure` / `research_contract_only`.

### 3.3 Collision / Thomson implementation

The production collision operator in the native path is the projected electron-frame Thomson source:

- `project_thomson_source(...)` in `htt/bass/collision/electron_frame.py`
- consumed by runtime and native integrator code in `htt/bass/runtime/ver2_execution.py` and `htt/bass/hierarchy/ver2_native_integrator.py`

This is a legitimate PSTF collision implementation and explicitly forbids FLRW-only shortcuts. It is not a scalar toy path.

The exact projected PSTF surface:

- `exact_thomson_source(...)` in `htt/bass/collision/electron_frame.py`
- `exact_thomson_gate_bundle(...)` in `htt/bass/collision/electron_frame.py`

is a higher-level contract wrapper over the projected source plus scalar versus directional bookkeeping.
That path is legitimate for the orthogonal/linear PSTF runtime envelope, but
the tilted branch is fail-closed if it only sees a boosted PSTF wrapper.

The newly added full-Stokes authority surface is separate:

- `full_stokes_thomson_source(...)` in `htt/bass/collision/electron_frame.py`
- `AngularStokesThomsonSource`
- `exact_thomson_gate_bundle(...)` accepting the angular source with
  `operator_scope = "full_electron_frame_stokes"`

It evaluates the classical Thomson/Rayleigh Mueller kernel in the scattering
plane, rotates Stokes `Q/U` between screen bases, applies the
`Gamma_T gamma_e (1 - v_e.e)` directional opacity contract, and exposes
machine-readable gate evidence for angular quadrature normalization and screen
basis orthonormality. The full-Stokes source now also declares and tests
screen-basis spin-2 rotation covariance: rotating the local polarization basis
and rotating the input `Q/U` samples gives an equivalently rotated source and
collision. For a tilted branch, the gate also requires actual
directional opacity modulation rather than merely declaring a full-Stokes
operator scope. Tests lock the isotropic unpolarized null collision,
90-degree Rayleigh polarization, tilt-dependent opacity, no-tilt tilted-branch
blocking, linearity, screen-basis rotation covariance, tilted gate opening, and
agreement with the existing PSTF quadrupole collision after angular projection.

The early-time Thomson-rate path is now physically nonzero. Inside HyRec
support `BaryonBackground.tau_dot` remains the strict table authority. For `z`
above the table ceiling, `tau_dot_with_early_fully_ionized_fallback(...)` uses
the same Planck-2018 recombination microphysics constants and
`x_e=1+2f_He`. The tilted visibility wrapper, integrator auxiliary state, seed
`tau_c` calculation, and runtime scalar visibility fast path now either consume
this fallback directly or defer to the electron-frame authority path instead of
clipping/zeroing early queries. This specifically addresses deep superhorizon
starts for high-k transfer diagnostics.

Tilted Tier-B runtime traces now build their exact-Thomson authority probe from
this full angular Stokes source, so the tilted exact-Thomson gate opens only
when the runtime state supplies a full-Stokes angular quadrature probe with
directional electron-frame opacity. This improves the collision authority
status materially. The tilted native hierarchy RHS now also consumes
PSTF-projected full-Stokes angular `I,Q,U` collision channels, using a cached
Mueller kernel that is tested against the full angular source. The polarization
projection is now a spin-weighted harmonic `Q/U <-> E/B` path with explicit
screen-basis rotation into the spherical basis, band-limited E/B roundtrip
tests, pure-E leakage checks, and runtime owner metadata
`full_stokes_spin2_angular_polarization`. This upgrades the tilted collision
RHS from scalarized polarization projection to a restricted-envelope spin-2
projection path; full headline/data-fitting claims still require broader
cutoff, source-propagation, family, and likelihood validation.

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

`htt/bass/inference/live_binding.py` now resolves the output-aware gate
registry, stores the resolved registry on the solver-output metadata, and
raises `FittingBlockedError` unless the upstream gates, full covariance
readiness, explicit output split evidence, sky support, and tilt/boost
separation checks all pass. This closes the former live-posterior bypass. A
live posterior call can still exist as a programming surface, but it is now
behind the validation gate rather than ahead of it.

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

What remains incomplete:

- full family-specific operator numerics for every backend surface,
- evidence that every optimized backend comparison used identical equations,
  tolerance, cutoff, observable, and hidden-fallback policy.

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

The main remaining release-honesty gap is narrower: docs must continue to
distinguish the new angular Stokes authority path from a runtime-integrated
tilted Stokes hierarchy, and must not promote FLRW-only Planck low-ell checks
into Bianchi template fitting.

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

This patch cycle also ran the collision/readiness command:

```bash
venv/bin/python -m pytest \
  htt/bass/hierarchy/test_spin2_projection.py \
  htt/bass/collision/test_full_stokes_thomson.py \
  htt/bass/collision/test_ver3_exact_thomson.py \
  htt/bass/collision/test_thomson_integration.py \
  htt/bass/validation/test_publication_readiness.py \
  -q
```

Result:

- `32 passed`

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

- No unresolved P0 remains from this re-audit batch. The previous live-fitting
  bypass is closed: `build_live_observer_boost_problem(...)` now resolves the
  output-aware gate registry, stores the resolved registry on the solver output,
  and blocks fitting unless every upstream gate, full covariance readiness,
  explicit tilt/boost separation, and explicit output split evidence are present.

### P1

- Non-Type-I exact source propagation is not the default executable reality. The default native bridge is approximate for non-Type-I families. See `htt/bass/forward/ver2_solver_output.py:588-597`.
- Production collision uses projected Thomson for orthogonal/linear PSTF
  authority. Tilted collision now consumes projected full-Stokes angular
  `I,Q,U` channels and uses spin-weighted harmonic `Q/U -> E/B` projection.
  This is a major collision/RHS upgrade, but headline polarization/data-fitting
  claims remain restricted until cutoff, family, source-propagator, and
  likelihood validation are closed.
- Off-axis tilted boost and generic mode transport are not closed. See `htt/bass/hierarchy/ver2_native_integrator.py:418-429`.
- The production tilted background path now uses the dynamic nonperturbative rapidity owner by default, but that does not yet close generic off-axis tilted mode transport or full angular Stokes runtime integration.

### P2

- Reionization is homogeneous tanh only. See `htt/bass/recombination/history_visibility.py:47-70`.
- Massive neutrino baseline is not shipped on the default species path. See `htt/bass/species/neutrino.py:10-12` and `51-57`.
- Observable covariance may be a sparse or proxy representation rather than a full inferential covariance object.

### P3

- Development multipole cutoffs remain narrow, but production-cutoff promotion
  now checks executed cutoff deltas against a declared tolerance.
- Some operator or backend surfaces are clearly contract-first rather than full physics-first.
- Early-time or table-coverage edges still generate warnings in smoke tests.

---

## 11. Top 12 Load-Bearing Risks

1. Non-Type-I families do not have default exact source propagation.
2. Tilted runtime exact-Thomson gates consume the full angular Mueller-integral
   Stokes authority probe, and the tilted native RHS now projects `Q/U` through
   a spin-2 harmonic E/B path. The remaining risk is validation breadth, not a
   scalarized projection gap.
3. Off-axis boost and generic tilted mode coupling remain deferred.
4. Type I tilted branch is intentionally blocked under current Codazzi
   projection policy.
5. Production tilted background evolution uses dynamic nonperturbative rapidity by default; fixed velocity is legacy diagnostic only.
6. Reionization support is homogeneous tanh only.
7. Default neutrino background is massless-only.
8. Observable covariance surfaces are often proxies or reduced summaries.
9. Layout protocol operator matrices require continued residual evidence.
10. Real Planck low-ell TT likelihood is deliberately FLRW-only; Bianchi data
    fitting still needs a harmonic/template covariance likelihood.
11. Runtime policy is still low-ell and cutoff-bounded.
12. Optimization claims require explicit same-equation, same-tolerance,
    same-cutoff, same-observable, no-hidden-fallback evidence.

---

## 12. Minimal Patch / Optimization Plan

The smallest remaining patch set that would materially improve audit status is:

1. Promote exact versus approximate source-propagator status to a first-class
   public-facing readiness field for every non-Type-I family.
2. Extend the dynamic nonperturbative tilt owner beyond representative
   axis-aligned tilted contracts into broader off-axis mode transport.
3. Close or hard-block the off-axis `FB-5.2` subset so that no approximate
   fallback can be misread as generic support.
4. Add a harmonic/template covariance likelihood before any Bianchi real-data
   fitting claim.
5. Expand cutoff convergence campaigns beyond the current low-ell bounded
   regime.

---

## 13. Final Verdict

`htt/bass` is a real executable Bianchi CMB codebase with meaningful Tier B native physics, explicit observer-neutral output semantics, enforced fitting gates, honest output split metadata, and a usable Type I validation bridge.

It is not yet a finished all-family exact CMB engine with fitting-ready statistics semantics.

The correct overall label is:

- executable,
- bounded,
- low-ell,
- observer-neutral,
- hard-gated at the statistics boundary,
- research-candidate Tier B solver,

with strong registry and governance scaffolding, but still incomplete all-family exactness and incomplete end-to-end fitting enforcement.

---

## 14. Headline Claims Allowed / Not Allowed

### Allowed

- `htt/bass` ships a real native Tier B production route.
- Type I has an exact matrix propagator path.
- Non-Type-I families have bounded approximate propagator families.
- The code explicitly separates global tilt from local observer boost.
- Supported tilted runtime contracts use the dynamic nonperturbative rapidity
  background owner by default; fixed velocity is explicit legacy diagnostic.
- A full angular electron-frame Stokes Thomson authority path exists, is used
  by tilted runtime exact-Thomson gates, supplies tilted projected `I,Q,U`
  collision RHS channels, and is tested against known
  Thomson/Rayleigh limits including tilted opacity.
- The solver output is observer-neutral and forbids direct likelihood or posterior semantics.
- Live inference is hard-gated and remains diagnostic unless gate, covariance,
  output split, sky support, and tilt/boost separation checks all pass.
- Planck low-ell TT likelihood is file-backed and FLRW-only.
- Visibility interpolation preserves positive opacity and monotone optical depth.
- Reionization and observable-vector surfaces exist in bounded, caveated form.
- A Tier A validation reference exists and can be contrastively compared to Tier B.

### Not allowed

- All 11 families are solved with exact source propagation by default.
- Generic off-axis tilted transport is implemented.
- Full angular Stokes `Q/U` polarization is already the time-integrated
  production hierarchy collision RHS.
- Bianchi real-data fitting through a C_l-only Planck likelihood is valid.
- The observable layer is a full-covariance, evidence-ready, fully inferential stack.
- Supported dynamic tilt background evolution implies a fully general off-axis
  tilted hierarchy.

---

## 15. One-Line Reason

`htt/bass` is already a serious bounded solver, but its strongest all-family,
runtime-integrated tilted-Stokes, and real-data Bianchi inference claims still
need additional physics paths and harmonic-level validation before
publication-grade status.

---

## Appendix A: Key Evidence Index

- Family registry coverage: `htt/bass/background/bianchi_types.py:150-178`
- Native Tier B route: `htt/bass/runtime/ver2_execution.py:1154-1235`
- Tier A validation route: `htt/bass/runtime/ver2_execution.py:929-1021`
- Tier A vs Tier B comparison: `htt/bass/runtime/ver2_execution.py:1024-1093`
- Development cutoff policy: `htt/bass/runtime/ver2_execution.py:140-152`
- Native IMEX split metadata and fallback reporting: `htt/bass/hierarchy/ver2_native_integrator.py`
- Background production owner: `htt/bass/background/evolution.py:155-195`
- Dynamic tilted background owner: `htt/bass/runtime/ver2_execution.py::_build_background_monitor`
- Nonperturbative tilt RHS: `htt/bass/background/nonperturbative_tilt.py`
- Legacy fixed-velocity tilted closure: `htt/bass/species/barotropic_closures.py`
- Projected Thomson production path: `htt/bass/collision/electron_frame.py`
- Angular full-Stokes Thomson authority and tilted gate checks:
  `htt/bass/collision/electron_frame.py`
- Spin-2 `Q/U <-> E/B` projection and same-physics cached kernel checks:
  `htt/bass/hierarchy/spin2_projection.py`,
  `htt/bass/hierarchy/test_spin2_projection.py`
- Angular/PSTF Thomson cross-validation:
  `htt/bass/collision/test_full_stokes_thomson.py`
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
- Live inference binding and hard-gated statistics decision: `htt/bass/inference/live_binding.py`
- File-backed FLRW-only Planck low-ell TT likelihood: `htt/bass/inference/planck_likelihood.py`
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

```bash
venv/bin/python -m pytest \
  htt/bass/collision/test_full_stokes_thomson.py \
  htt/bass/collision/test_ver3_exact_thomson.py \
  htt/bass/collision/test_thomson_integration.py \
  htt/bass/validation/test_publication_readiness.py \
  -q
```
