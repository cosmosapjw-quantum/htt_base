# Round-15 P2 — D-2 integrator η_init extension plan

_Draft 2026-04-26, after Round-15 P1 closure (commits `f6173d8` →
`2ad6e8d`). Working WBS only — explicitly no timeline annotations._

---

## §0. Mission

Extend the BASS IMEX cosmological integrator's lower η-bound from the
current production value (`η_init ≈ 261 Mpc`, `z ≈ 1100`, set by
`DEFAULT_PRE_RECOMBINATION_MARGIN_MPC = 20.0` in
[htt/bass/runtime/cosmological_config.py:52](../htt/bass/runtime/cosmological_config.py#L52))
to a deep radiation-dominated value (`η_init ~ 0.01 Mpc`, `z ~ 10⁹`).

This closes the empirical residual that Round-15 P1 §10 / `k_adapted_η100`
identified: at the four valid (k, ℓ) cells with k ≤ 10⁻², artificially
lifting η_init to 100 Mpc moves dominant low-k cells into Case A
(ratios 0.93–1.04). Production-quality recovery requires the
integrator to actually run from z ~ 10⁹, not just the LoS quadrature
to extrapolate (the BASS PCHIP source extractor uses `extrapolate=False`
and cannot evaluate below the integrator's η[0]).

P2 also closes the Round-15 P1 monopole-frame contract at sub-percent
once primordial-amplitude alignment is enabled by a common pre-recomb
domain between BASS and CAMB.

---

## §1. Pre-flight gates

These gates must clear **before** the WBS Phase B begins. They are not
themselves engineering tasks; they are policy/algebra adjudications.

### §1.1 CLAUDE.md ban on "TCA pre-phase" — adjudication required

[CLAUDE.md §6](../CLAUDE.md#L116) bans:

> the approximation-free-banned constructs: **TCA pre-phase**, **FLRW
> UFA**, **photon RSA**

Any path from `η_init = 0.01 Mpc` (z ~ 10⁹) to recombination must
traverse the photon–baryon Thomson-coupled regime where κ̇ vastly
exceeds H. Three architectural options exist:

| Path | Description | Approximation-free? |
|---|---|---|
| **α** | Algebraically-exact second-order TCA (Cyr-Racine & Sigurdson 2011, arXiv:1012.0569 / PRD 83, 103521). Standard CAMB / CLASS practice. Information-preserving asymptotic expansion in `kτ_c`. | Depends on the project owner's reading of the §6 ban. The expansion preserves all photon multipole information to the order kept; it is *not* a phenomenological fluid replacement. CLAUDE.md banned-list wording is ambiguous on this distinction. |
| **β** | No TCA. Direct stiff-implicit solver from `η_init = 0.01` with `Rodas5P` / `IMEX-ARK4` taking time-steps τ < `τ_c(η)`. | Yes. Uncertain whether numerically tractable; cost grows like `τ_c⁻¹` ~ `a⁻⁴` per step in radiation domination. |
| **γ** | Per-`k` matching-asymptotic: analytic super-horizon adiabatic mode for `kη ≪ 1`, full PSTF ODE for `kη ≳ 1`. Sub-horizon side still traverses Thomson regime, so collapses back to **α** or **β** unless `β` is tractable. | Yes (each region is exact in its limit). |

The plan below is structured to **first clear §1.1 in Phase A.1**
before any code changes. If Path α is approved, Phases B-G proceed as
written. If Path β is selected, Phases B and F substitute a stiff-solver
benchmark for the TCA equations and re-derive the cost envelope. If
Path γ is selected, Phases B+C are restructured around a per-`k`
analytic-mode handler.

The default path that the rest of this document describes is **Path α**
(it is the only path with a known feasibility envelope from CAMB's
production deployment). Section §1.1 explicitly flags the
adjudication so the project owner records the chosen path with
explicit reasoning.

### §1.2 Anchor invariants

The following must remain unaffected by every commit in this work
package:

- **Route-B Python golden** `D_2 = 1002.086744 μK²`
  ([htt/bass/validation/test_d2_regression_anchor.py](../htt/bass/validation/test_d2_regression_anchor.py))
  — analytic MM-curve; separate code path; bit-identical.
- **Route-B Rust** `D_2 = 1002.086744 μK²` (independent Rust binary,
  MB-95 sync_gauge_camb.rs path) — bit-identical.
- **fb53 super-horizon IC tests** (43 + 9 R10/R11 in
  `htt/bass/perturbation/test_fb53_regular_adiabatic_ic_skeleton.py`)
  — seed-level, no LoS; must remain bit-identical.
- **D-1 fix resolution-independence** at the LoS projector — pinned
  by the 9 sharp-visibility + extended R5 oracles in
  `htt/bass/los/test_flrw_bessel_projector.py`.
- **Fast baseline 1762 passed** (post-P1.γ) — must remain at 1762 +
  new P2 tests with no regression in the existing set.
- **Honest claim envelope** ([CLAUDE.md §1](../CLAUDE.md#L14)): the
  registry + shear-source coverage envelope (FLRW, I, V, IX full;
  others axis-aligned) must not be silently expanded by P2 work. P2
  is FLRW-scope; Bianchi extension hooks are catalogued but deferred.

### §1.3 Definitions

| Symbol | Definition |
|---|---|
| `η_init^(P2)` | The new IMEX integrator lower η-bound, target ~ 0.01 Mpc. |
| `η_match(k)` | Conformal time at which a per-k path-α / path-γ algebraic-state branch yields to the full PSTF hierarchy. CAMB criterion: `kτ_c(η_match) = ε`, with `ε ≈ 0.02` for second-order TCA. |
| `τ_c(η)` | Thomson mean free path `1/κ̇(η) = (a n_e σ_T)⁻¹`. |
| `R(η)` | Baryon loading factor `4ρ_γ / (3ρ_b)` (CAMB convention). |
| `TCA-active state` | Reduced photon-sector state vector during Path α: photon octupole `I_3` and E-mode multipoles `ℓ ≥ 2` are algebraic (quasi-static); only `{δ_b, δ_c, δ_γ, δ_ν, v_b, Θ_1, Θ_2, E_2, Φ, Ψ}` evolved dynamically (and only `Θ_2 = π_γ/2`, `E_2 = π_γ/4` as quasi-static algebraic followers, with first- and second-order CRS2011 corrections). |
| `recomb_table.z_max` | HyRec recombination table maximum redshift; current value `8000` per the runtime warning in [htt/bass/species/registry.py:265](../htt/bass/species/registry.py#L265). |

---

## §2. Work breakdown structure

### Phase A — Algebraic and policy foundation

#### A.1 Adjudicate CLAUDE.md TCA-ban for Path α

- **Inputs**: CLAUDE.md §6 banned-list wording; CRS2011 abstract +
  TCA-equation derivations from
  `project/04_implementation_specs/CAMB_Tight-Coupling_…_Implementation_Guide_for_bass_rs.md`;
  Round-15 P1 derivation docs.
- **Activity**: Project owner reviews the algebraically-exact-vs-
  phenomenological distinction. Outcome is one of: (a) Path α
  approved with refined CLAUDE.md wording, (b) Path β selected
  (stiff-solver), (c) Path γ selected (matching-asymptotic).
- **Deliverable**: `docs/V5_ROUND15_P2_PATH_VERDICT.md` (new) — one
  paragraph statement of the chosen path with explicit reasoning,
  signed off by the project owner. Includes any refinement to the
  CLAUDE.md banned-list wording if Path α is selected.
- **Acceptance**: file exists, references CRS2011 by DOI, names the
  selected path.
- **Blocks**: A.2, B.*, C.*, D.*, E.*, F.*. Nothing else may begin
  until this is resolved.

#### A.2 PSTF-convention TCA derivation (Path α only)

- **Inputs**: CAMB↔BASS PSTF mapping spec; Challinor-Lasenby
  2000-I/II; Maartens 1998 covariant velocity; Tsagas-Challinor-
  Maartens 2008.
- **Activity**: lift CRS2011 second-order TCA equations from MB-95
  synchronous-gauge to BASS PSTF / 1+3 covariant variables. Produce
  closed-form expressions for: (i) quasi-static π_γ, (ii) slip
  equation `q_γ − (4/3)v_b`, (iii) baryon velocity v_b' RHS, (iv)
  E-mode polarization quadrupole E_2 = π_γ/4 (with second-order
  corrections), (v) octupole I_3 at switchback initialisation, (vi)
  E-mode octupole E_3 at switchback initialisation. All equations
  in BASS variables: `Θ_ℓ = I_ℓ/4`, `q_γ = (4/3)v_γ = 4Θ_1`,
  `σ = (2/3)Θ_2`, `polter = (3/4)I_2 + (9/2)E_2`.
- **Deliverable**: `docs/V5_ROUND15_P2_TCA_PSTF_DERIVATION.md` (new)
  — step-by-step derivation cited to CRS2011 / Lewis-Challinor /
  CAMB Notes equation numbers. Each formula tagged with the BASS
  file/line site where it will eventually be implemented (Phase B).
- **Acceptance**: external-LLM audit (similar pattern to P1 hand-
  off) verifies ≥ 80% of equations at first read; corrections
  applied and a second audit pass clears the residual.
- **Depends on**: A.1 verdict (Path α).
- **Blocks**: B.2, B.3, B.4.

#### A.3 Recombination history range extension

- **Inputs**: HyRec table generator under `htt/bass/recombination/`;
  Saha-Boltzmann analytic solution for fully-ionized regime
  (z > ~10⁵ where x_e ≡ 1 to numerical precision).
- **Activity**: confirm whether the existing HyRec table can be
  re-generated to z_max = 10⁹, or whether the runtime registry
  should append a Saha extrapolation for z > recomb_table.z_max.
  The registry already supports the `recombination_warning_policy`
  knob ([species/registry.py:200](../htt/bass/species/registry.py#L200))
  but currently only suppresses the warning, not extends the
  domain.
- **Deliverable**: `docs/V5_ROUND15_P2_RECOMB_RANGE_AUDIT.md` (new)
  with one of:
  - (i) Patched HyRec generator producing `z_max ≥ 10⁹`. Run-time
    cost is minimal because x_e is fully saturated; the table
    becomes mostly trivial values for z > ~10⁵.
  - (ii) Saha-extrapolation policy in `bass.recombination` that
    returns `x_e = 1`, `T_m = T_γ`, `κ̇` from `n_e = n_b` algebra
    for all z > `recomb_table.z_max`. Backed by an analytic-
    derivation appendix.
- **Acceptance**: a registry test runs at `η_init = 0.01 Mpc` and
  queries `x_e(z = 10⁸)` without raising and with `|x_e − 1| < 1e-12`.
- **Depends on**: A.1 verdict (any path requires extended recomb
  domain).
- **Blocks**: B.5, C.1.

#### A.4 Background table range audit

- **Inputs**: `species.bg_table` accessor used in
  [htt/bass/spectrum/tier_b_source_extraction.py:204-206](../htt/bass/spectrum/tier_b_source_extraction.py#L204).
- **Activity**: verify the FLRW background table generator covers
  η ∈ [0.01, 14147] Mpc; that `interp_a(η)`, `interp_calH(η)`, and
  `rho_*(η)` evaluate cleanly at η = 0.01 Mpc; that the
  radiation-dominated analytic asymptote `a(η) ∝ η`, `ℋ(η) = 1/η`
  holds at the η_init = 0.01 endpoint.
- **Deliverable**: `docs/V5_ROUND15_P2_BG_RANGE_AUDIT.md` (new) with
  numerical comparison of BASS bg_table outputs vs analytic RD
  asymptotes at η = 0.01, 0.1, 1.0 Mpc. If catastrophic cancellation
  is observed in any quantity, propose a high-precision numeric
  override or a hybrid analytic / tabulated scheme for η < 1 Mpc.
- **Acceptance**: relative error of `bg_table` outputs vs analytic
  RD asymptotes at η = 0.01 Mpc is ≤ 10⁻⁶ for `a`, `ℋ`, `ρ_γ`,
  `ρ_ν`; ≤ 10⁻⁴ for matter species (small at z = 10⁹ but should
  remain non-negative finite).
- **Depends on**: A.1 verdict.
- **Blocks**: B.5, C.1, D.2.

#### A.5 Analytic super-horizon mode catalogue (used by Path γ; tagging-only for Path α)

- **Inputs**: Maartens 1998 §III; Dodelson §6.3; Round-15 P1
  derivation appendices Y.1–Y.4 (k_eq formula; coupled-mode
  analysis).
- **Activity**: derive closed-form super-horizon adiabatic-mode
  expressions for `δ_γ(η, k)`, `δ_b(η, k)`, `δ_c(η, k)`,
  `δ_ν(η, k)`, `v_b(η, k)`, `Φ(η, k)`, `Ψ(η, k)` valid in the
  `kη ≪ 1` regime. Distinguish RD and MD asymptotic forms; provide
  smooth interpolation across radiation-matter equality.
- **Deliverable**: `docs/V5_ROUND15_P2_SUPERHORIZON_MODE.md` (new) —
  closed-form catalogue plus Python reference implementation
  fragment intended for inclusion as a regression-test fixture.
- **Acceptance**: at η = 0.01 Mpc, k ∈ {10⁻⁴, 10⁻³, 10⁻²} Mpc⁻¹,
  the catalogue's predictions match the existing
  `build_flrw_regular_seed` (Phase C.1) ratios `δ_γ : δ_b : δ_c :
  δ_ν = 4/3 : 1 : 1 : 4/3` to machine precision (since both are
  the same exact super-horizon adiabatic mode, just at different η).
- **Depends on**: A.1 verdict.
- **Blocks**: A.2 (cross-check), Phase C.1, Phase F.5.

---

### Phase B — TCA-active integrator state and RHS (Path α)

If Path β / γ is selected in A.1, Phase B is restructured. The
sub-tasks below assume Path α.

#### B.1 TCA-active state dataclass

- **Inputs**: A.2 output equations; existing `PSTFHierarchyState`
  in `htt/bass/hierarchy/`.
- **Activity**: introduce `TCAReducedState` dataclass at
  `htt/bass/hierarchy/tca_state.py` (new file) holding
  `{δ_b, δ_c, δ_γ, δ_ν, v_b, Θ_1, Θ_2_qs, E_2_qs, Φ, Ψ}` plus a
  `tca_active` flag and the values of `κ̇`, `R` cached at the
  current η. Provide `to_full_pstf_state(eta_match)` adapter that
  reconstructs the full hierarchy state at switchback.
- **Deliverable**: `htt/bass/hierarchy/tca_state.py` + unit tests
  in `htt/bass/hierarchy/test_tca_state.py`.
- **Acceptance**: 8+ unit tests covering construction, the cached
  `κ̇`/`R` accessors, and the `to_full_pstf_state` adapter
  (verified against an equivalent PSTFHierarchyState built from the
  same multipoles).
- **Depends on**: A.2.
- **Blocks**: B.2, B.3, B.4.

#### B.2 Quasi-static π_γ helper

- **Inputs**: A.2 quasi-static formula (CRS2011 second-order):
  `π_γ = (32/45) (k/κ̇)(σ + (3/4) q_γ) [1 + 11 κ̈/(6 κ̇²)]
        − (32/45) (k/κ̇²)(σ̇ + (3/4) q̇_γ)·(11/6)`
- **Activity**: implement `quasi_static_pi_gamma(k, kappa_dot,
  kappa_ddot, sigma, sigma_dot, q_gamma, q_gamma_dot)` at
  `htt/bass/hierarchy/tca_quasistatic.py` (new file).
- **Deliverable**: function + unit tests; CAMB-Fortran cross-check
  fixture (record CAMB's `pig` value at a single (k, η, x_e) cell
  by running `scripts/v5_round15_p2_camb_tca_extract.py` (new),
  compare BASS to ≤ 0.1%).
- **Acceptance**: 5 cross-check cells across (k, x_e) all within
  0.1% of CAMB.
- **Depends on**: A.2, B.1.
- **Blocks**: B.4.

#### B.3 Slip equation + v_b' RHS in TCA-active sector

- **Inputs**: A.2 slip equation:
  `q_γ − (4/3)v_b = (τ_c / (3(1+R)))[k δ_γ − 4 k c_s² δ_b
                                    + 4 ℋ v_b]`
  and the second-order v_b' equation (CAMB Notes eq. 7.1–7.2).
- **Activity**: implement `slip_q_gamma_minus_v_b(...)` and
  `v_b_dot_tca(...)` at `htt/bass/hierarchy/tca_slip.py` (new
  file). Both must accept the `BaryonBackground` baryon sound-
  speed `c_s²` (already produced by `species[BARYON]._recomb`).
- **Deliverable**: functions + unit tests + analytic super-horizon
  limit cross-check (slip → 0 as `kτ_c → 0` and `v_b → 3 Θ_1` per
  Maartens 1998).
- **Acceptance**: super-horizon-limit test passes to machine
  precision; CAMB-Fortran cross-check at 5 cells ≤ 0.1%.
- **Depends on**: A.2, B.1.
- **Blocks**: B.4.

#### B.4 TCA RHS dispatcher + switchback

- **Inputs**: B.1 / B.2 / B.3 outputs;
  [hierarchy_rhs.py:343](../htt/bass/hierarchy/hierarchy_rhs.py#L343)
  full PSTF photon RHS.
- **Activity**: implement
  `dispatch_photon_rhs(state, eta, k, ...)` at
  `htt/bass/hierarchy/tca_dispatcher.py` (new file). Logic:
  - If `kτ_c(η) > ε` (TCA-active): evaluate B.1's reduced state
    via B.2 + B.3, return the reduced RHS.
  - Else: switchback. Initialize the full PSTF state via
    `to_full_pstf_state`, including CRS2011 second-order I_3 and
    E_2/E_3 forms (CAMB Notes eq. 7.4 / 7.6), then return the
    full RHS via `hierarchy_rhs_photon_from_state`.
  - The IMEX integrator's outer loop (`bass.runtime`) detects the
    `tca_active` flag flip and restarts the ODE with the expanded
    state at η_match.
- **Deliverable**: dispatcher module + unit tests covering
  switchback continuity (state vector pre- vs post-switchback
  identical to machine epsilon for evolved quantities, and the
  R5.5/R5.4 oracles still pass on the post-switch trajectory).
- **Acceptance**: switchback continuity test, plus a smoke-test
  IMEX run from η=0.01 to η=14147 at k=10⁻³ that completes within
  10× the wall-time of the current production η_init=261 run.
- **Depends on**: B.1, B.2, B.3.
- **Blocks**: B.5, C.1, D.*.

#### B.5 IMEX integration over [η_init = 0.01, η_today]

- **Inputs**: B.4 dispatcher; existing `build_cosmological_integrator_config`.
- **Activity**: lower
  `DEFAULT_PRE_RECOMBINATION_MARGIN_MPC` is *not* the right knob
  (it derives `η_init = η_star − margin`); instead introduce an
  override parameter `eta_initial_override_mpc` to
  `build_cosmological_integrator_config` (or extend the existing
  margin path with a much larger value, e.g. `margin = η_star −
  0.01 ≈ 281`). Verify IMEX-ARK4 and Rodas5P stability under the
  TCA-active state, and the existing eigenvalue-residual machinery
  in `ver3_layout_protocol.py` still produces `λ_max ≈ 1e-16` at
  the TCA-active η range.
- **Deliverable**:
  - `htt/bass/runtime/cosmological_config.py` extension supporting
    `eta_initial_override_mpc`.
  - End-to-end smoke test
    `htt/bass/runtime/test_p2_full_range_integration.py` (new):
    runs IMEX from η=0.01 to η=14147 at three k values and verifies
    no NaN, no integration failure, λ_max ≤ 1e-12 at three
    representative η.
- **Acceptance**: smoke test passes; benchmark report records
  TCA-active vs full-hierarchy timing ratio (expected ~1, since
  TCA-active state has fewer dynamical components).
- **Depends on**: A.3, A.4, B.4.
- **Blocks**: C.1, D.*, E.*, F.*.

---

### Phase C — IC seed extension to η_init = 0.01 Mpc

#### C.1 Adiabatic super-horizon seed at z = 10⁹

- **Inputs**: `seed_compatibility.build_flrw_regular_seed`
  ([line 161](../htt/bass/hierarchy/seed_compatibility.py#L161)) +
  A.5 super-horizon catalogue.
- **Activity**: verify the existing seed formula
  `δ_γ : δ_b : δ_c : δ_ν = 4/3 : 1 : 1 : 4/3` with `θ = 0` remains
  exact at z = 10⁹ super-horizon (`kη(z = 10⁹) ~ 10⁻⁶` for
  k = 10⁻²; vastly super-horizon). Verify the seed amplitude
  convention (`theta_common = amp/3.0` for the non-adiabatic mode;
  `theta_common = 0` for adiabatic) preserves primordial-curvature
  normalization across η_init choices. Add explicit RD vs MD
  branch indicator to the descriptor (currently the seed assumes
  MD-equivalent ratios; the RD limit must be cross-checked).
- **Deliverable**:
  - Audit memo `docs/V5_ROUND15_P2_SEED_RD_NORMALIZATION_AUDIT.md`
    documenting that the existing adiabatic-ratio seed is the same
    super-horizon mode at z = 10⁹ and z = 1100 (only η differs).
  - New seed unit tests at η = 0.01 Mpc cover the same observables
    as the existing fb53 super-horizon-IC suite at η = 261 Mpc.
- **Acceptance**: new seed tests at z = 10⁹ pass; existing fb53
  tests remain bit-identical.
- **Depends on**: A.5, B.5.
- **Blocks**: C.2, C.3, F.*.

#### C.2 Tilted-seed extension

- **Inputs**: existing `promote_tilted_seed`
  ([seed_compatibility.py:224](../htt/bass/hierarchy/seed_compatibility.py#L224)).
- **Activity**: verify the boost-order γ-factor expansion remains
  numerically stable at radiation-domination electron-tilt
  amplitudes. The honest-claim envelope (CLAUDE.md §1) restricts
  Bianchi-coupled tilts to the `tilt_background_owner=
  policy-fixed` runtime control; verify this policy is preserved
  at extended η_init.
- **Deliverable**: a tilted-seed cross-check at η = 0.01 Mpc with
  small `electron_velocity` (|v| ~ 1e-3) and the existing tests
  remain bit-identical.
- **Acceptance**: existing tilted-seed tests + a new RD-era test
  (`abs(γ−1) ≤ 1e-6` for `|v| = 1e-3` at z = 10⁹) all pass.
- **Depends on**: C.1.
- **Blocks**: F.5.

#### C.3 Constraint-projection re-validation

- **Inputs**:
  [seed_compatibility.build_constraint_projection](../htt/bass/hierarchy/seed_compatibility.py#L267).
- **Activity**: re-validate the first-pass boost-consistency
  reduction at very early η. Catalog any constraint residuals that
  scale with `a(η)` and verify they remain below
  `atol = 1e-10` at η = 0.01 Mpc.
- **Deliverable**: constraint-residual unit test at z = 10⁹.
- **Acceptance**: test passes with the existing default `atol`.
- **Depends on**: C.1.
- **Blocks**: F.*.

---

### Phase D — Source extractor adaptation

#### D.1 PCHIP `extrapolate=False` domain check

- **Inputs**: `extract_flrw_sources_from_tier_b`
  ([tier_b_source_extraction.py:130](../htt/bass/spectrum/tier_b_source_extraction.py#L130));
  the integrator's η-grid output.
- **Activity**: with the integrator producing η[0] = 0.01 Mpc,
  the PCHIP interpolator domain extends to that bound. Verify
  the LoS pipeline's `_los_and_wrap` clamping (`eta_init_los =
  np.maximum(integrator_eta[0], 0.0)` at
  [flrw_pipeline.py:341](../htt/bass/spectrum/flrw_pipeline.py#L341))
  produces a non-NaN PCHIP evaluation at the new lower bound.
- **Deliverable**: regression smoke test that runs
  `compute_linear_probe_transfer_function` at k = 10⁻³ with the
  P2 integrator config and verifies finite Δ_T at all ℓ.
- **Acceptance**: smoke test passes.
- **Depends on**: B.5, C.1.
- **Blocks**: E.1, F.*.

#### D.2 Constraint-algebra numerical stability

- **Inputs**:
  [tier_b_source_extraction.py:278](../htt/bass/spectrum/tier_b_source_extraction.py#L278)
  formula
  `four_pi_g_a2_over_k2 = 1.5 (H_0_mpc² · a²) / k²`.
- **Activity**: at z = 10⁹, `a² ≈ 10⁻¹⁸`. The product
  `four_pi_g_a2_over_k2 · δρ_tot` is finite (radiation-dominated
  density `δρ_tot` is large), but the numerical balance between
  factors must be checked for catastrophic cancellation in
  float64. Run a precision audit comparing float64 vs float128
  (mpmath / numpy.longdouble) for the Φ, Ψ reconstruction at
  η = 0.01, 0.1, 1.0 Mpc.
- **Deliverable**:
  - Audit memo
    `docs/V5_ROUND15_P2_CONSTRAINT_PRECISION_AUDIT.md`.
  - If catastrophic cancellation observed: a high-precision
    override path in the source extractor (e.g., re-arranged
    formula or longdouble at the cost of a small slowdown).
- **Acceptance**: relative deviation Φ_float64 / Φ_float128 − 1
  ≤ 1e-10 at η = 0.01 Mpc; if not, the override path achieves
  this.
- **Depends on**: A.4, B.5.
- **Blocks**: D.3, D.4, E.*.

#### D.3 Anisotropic-stress in radiation domination

- **Inputs**:
  [tier_b_source_extraction.py:295-302](../htt/bass/spectrum/tier_b_source_extraction.py#L295).
- **Activity**: at z = 10⁹, ρ_ν / ρ_total ≈ 0.405 (standard
  3 effective species), so the neutrino-anisotropic-stress
  contribution to (Ψ − Φ) is significant. Verify the formula
  `psi_minus_phi = 3 × four_pi_g_a2_over_k2 × stress_intensity`
  produces a numerically stable Ψ − Φ at z = 10⁹, and that the
  `anisotropic_stress=True` default exercises this path
  consistently.
- **Deliverable**: regression test that exercises the source
  extractor at η = 0.01 Mpc with `anisotropic_stress` toggled,
  compared to an analytic radiation-era expectation.
- **Acceptance**: test passes; deviation from analytic RD
  (Ψ − Φ)/Ψ ratio is ≤ 1% at z = 10⁹.
- **Depends on**: D.2.
- **Blocks**: E.*, F.*.

#### D.4 ISW-driver `_fd4_derivative` audit at extended η

- **Inputs**:
  [_fd4_derivative](../htt/bass/spectrum/tier_b_source_extraction.py#L88).
- **Activity**: the 4th-order centered finite-difference scheme
  computes Φ̇+Ψ̇ on the integrator η-grid. With η_init lowered to
  0.01 Mpc, the η-grid spans 6 orders of magnitude on what is
  currently a uniform-linear sampling — so the FD4 stencil is
  asymmetric near the lower boundary. Verify the boundary 2nd-
  order one-sided differences remain accurate. Optional: switch to
  log-uniform spacing in η at the early-time end.
- **Deliverable**:
  - FD4 accuracy audit on a synthetic adiabatic mode (Φ̇+Ψ̇ from
    A.5 catalogue compared to FD4 evaluation on a representative
    grid).
  - If accuracy degrades: introduce a hybrid analytic / FD4 driver
    that uses the analytic super-horizon expression for η < η_eq.
- **Acceptance**: ISW driver `(Φ̇+Ψ̇)/Φ̇_analytic − 1` ≤ 1% at
  η = 0.1 Mpc (deep RD).
- **Depends on**: A.5, B.5, D.2.
- **Blocks**: F.*.

---

### Phase E — LoS pipeline integration

#### E.1 `_los_and_wrap` η-domain re-verification

- **Inputs**:
  [flrw_pipeline.py::_los_and_wrap](../htt/bass/spectrum/flrw_pipeline.py#L306)
  (Round-15 P0 implementation).
- **Activity**: confirm the existing P0 implementation remains
  correct with `integrator_eta[0] = 0.01 Mpc`. The
  `eta_init_los = np.maximum(integrator_eta[0], 0.0)` clamp does
  not need adjustment, but the down-stream `build_los_grid` call
  must handle the new lower bound (E.2).
- **Deliverable**: integration smoke test re-using the P0 test
  fixture but with the P2 integrator config.
- **Acceptance**: smoke test passes; Δ_T finite at all (k, ℓ).
- **Depends on**: B.5, D.*, E.2.
- **Blocks**: F.*.

#### E.2 `build_los_grid` zone restructuring for extended η_init

- **Inputs**:
  [bass/los/los_grid_builder.py::build_los_grid](../htt/bass/los/los_grid_builder.py).
- **Activity**: the current grid spans
  `[η_init, recomb_eta + 5·FWHM]` as zone 1 with
  `Δη ≈ recomb_fwhm / n_per_recomb_fwhm ≈ 2.4 Mpc`, and
  `[zone1_end, η_today]` as zone 2 with k-adapted Δη. With
  `η_init = 0.01`, zone 1 expands to span 4 orders of magnitude
  in η, most of which has g(η) ≈ 0 (pre-recombination). Add a
  pre-recombination zone (zone 0) at the very early end with much
  sparser spacing (e.g., logarithmic in η, controlled by a
  `pre_visibility_step_decade` parameter). Zone 0 ends where the
  recombination visibility transitions out of its tail (e.g.,
  `recomb_eta − 10·FWHM ≈ 91 Mpc`).
- **Deliverable**:
  - `bass/los/los_grid_builder.py` extension: optional `eta_pre_visibility_start_mpc` argument with default behaviour matching the P0 (no extra zone) path.
  - Updated tests in
    `htt/bass/los/test_los_grid_builder.py` covering the new zone-0
    behaviour.
- **Acceptance**: tests pass; resolution-independence preserved
  (the existing `test_recombination_zone_resolves_visibility_fwhm`
  and friends still pass at zone-0 enabled).
- **Depends on**: E.1.
- **Blocks**: E.3, F.*.

#### E.3 Activate `sparse_late_isw` flag

- **Inputs**:
  [bass/los/los_grid_builder.py::build_los_grid](../htt/bass/los/los_grid_builder.py)
  — the existing `sparse_late_isw=True` parameter is currently a
  documented no-op.
- **Activity**: implement the sparse-late-ISW behaviour: once the
  Bessel kernel `j_ℓ[k(η_0 − η)]` is well-resolved by zone 2's
  k-adapted spacing, late-time samples can drop further (zone 3
  with `Δη = 2π / (k · n_per_oscillation_late)` where
  `n_per_oscillation_late < n_per_oscillation`). Validates against
  the R5.4 ISW Limber oracle.
- **Deliverable**: zone-3 implementation + unit test at high ℓ
  (R5.4 Limber regime).
- **Acceptance**: R5.4 oracle still passes at the same tolerance;
  total grid size at k = 10⁻¹ Mpc⁻¹ reduces by at least 30% vs the
  zone-2-only path.
- **Depends on**: E.2.
- **Blocks**: F.*.

---

### Phase F — Validation gates

#### F.1 Anchor regression sweep

- **Activity**: run the standard fast-baseline test set + the 9
  Round-15 P1 oracles + the new P2 unit tests in a single pass.
  Verify Route-B Python golden D_2, fb53 + R10/R11, and
  resolution-independence are all bit-identical.
- **Deliverable**: a one-line CHANGELOG note recording the test
  count.
- **Acceptance**: test count ≥ 1762 (fast baseline post-P1.γ) +
  P2 additions; zero unexpected failures.
- **Depends on**: B.5, C.*, D.*, E.*.
- **Blocks**: F.2.

#### F.2 §10 decisive test re-run with extended η_init

- **Inputs**: `scripts/v5_round15_decisive_los_test.py` (the
  3-column diagnostic introduced in P0 + P1).
- **Activity**: re-run the §10 test with the P2 integrator
  producing `integrator_eta[0] ≈ 0.01 Mpc`. The
  `k_adapted_η100` column was the artificial-extension test that
  defined the post-P0 / pre-P2 empirical anchor; the new
  `k_adapted` (production) column should now match it.
- **Deliverable**:
  `docs/audits/v5_round15_p2_section10_post_extension.txt`.
- **Acceptance**: at the four valid (k, ℓ) cells with k ≤ 10⁻²,
  the production `k_adapted` column matches the P0/P1
  `k_adapted_η100` reference column to within 5%; and both match
  CAMB direct to within 5%. Median |ratio| across the 12 cells
  drops further from the post-P0 value of 1.00.
- **Depends on**: F.1.
- **Blocks**: F.3.

#### F.3 Monopole-frame diagnostic re-run

- **Inputs**: `scripts/v5_round15_p1_monopole_frame_diagnostic.py`.
- **Activity**: re-run the monopole-frame diagnostic with the P2
  integrator output. With both BASS and CAMB now sharing the same
  η-domain back to z = 10⁹, the primordial-amplitude alignment
  becomes possible (the `Θ_0^(BASS) ~ k²` artifact noted in the
  P1 first-run transcript was a normalization-mismatch artifact;
  with full-domain integration both BASS and CAMB carry the same
  primordial curvature normalization).
- **Activity 2**: also extend the diagnostic to compute and
  report explicit primordial-amplitude-aligned ratios:
  `Θ_0^(BASS) / A_BASS` vs `Θ_0^(CAMB) / A_CAMB(A_s)`. The
  alignment factor is computable from `seed.amplitude` (BASS) and
  CAMB's `A_s = 2.1e-9` setting.
- **Deliverable**:
  `docs/audits/v5_round15_p2_monopole_frame_post_extension.txt`.
- **Acceptance**: at η = η_init = 0.01 Mpc and at η = 281 Mpc
  (recombination), the `cand/CAMB` ratio reaches 0.99–1.01 for
  k ∈ {10⁻³, 5·10⁻³, 10⁻²}. This closes the Round-15 P1 monopole
  contract at sub-percent.
- **Depends on**: F.2.
- **Blocks**: F.4.

#### F.4 R5 oracle regression

- **Activity**: all 9 P1 sharp-visibility + extended-analytic
  oracles must continue to pass. They are test-only and do not
  depend on integrator η_init, so this is a strict invariant.
- **Deliverable**: included in F.1's test sweep; explicit re-
  affirmation in the P2 CHANGELOG.
- **Acceptance**: 9 oracles pass at the existing tolerances.
- **Depends on**: F.1.
- **Blocks**: F.6.

#### F.5 TCA cross-check against CAMB Fortran

- **Inputs**: `scripts/v5_round15_p2_camb_tca_extract.py` (B.2
  cross-check fixture).
- **Activity**: extract CAMB Fortran's `pig`, `qg`, `vb`, switchback
  initialised octupole and E-mode multipoles at 5 distinct
  (k, x_e) cells. Verify BASS TCA-active state matches to ≤ 0.1%
  cell-by-cell.
- **Deliverable**:
  `docs/audits/v5_round15_p2_tca_camb_cross_check.txt`.
- **Acceptance**: 5/5 cells within 0.1%.
- **Depends on**: B.2, B.3, B.4.
- **Blocks**: F.6.

#### F.6 End-to-end D_ℓ TT/EE comparison

- **Inputs**: full BASS PSTF primary pipeline at extended η_init.
- **Activity**: compute D_ℓ TT and D_ℓ EE for ℓ ∈ [2, 100] from
  the P2 BASS pipeline; compare to CAMB at the same Planck-2018
  cosmology. The §10 oracle (CAMB internal `delta_p_l_k`) is
  faithful at low ℓ even at moderate k (per P1 §3.3 finding); the
  P2 pipeline should now reach the post-P0 § 10 four-cell anchor
  precision across the full ℓ range.
- **Deliverable**:
  `docs/audits/v5_round15_p2_end_to_end_dl_comparison.txt`.
- **Acceptance**: residual `|D_ℓ^BASS − D_ℓ^CAMB| / D_ℓ^CAMB` at
  ℓ ∈ [2, 50] is ≤ 5% mode-by-mode. (Higher-ℓ Silk-damping regime
  is out of scope for P2 — it requires a photon-baryon Silk-
  diffusion treatment beyond TCA.)
- **Depends on**: F.4, F.5.
- **Blocks**: G.*.

---

### Phase G — Documentation + audit closure

#### G.1 CHANGELOG closure entry

- **Activity**: append a single coherent CHANGELOG entry under
  `[Unreleased]` summarizing P2 closure: TCA-active integrator,
  extended η_init, anchor preservation, F.* gate outcomes.
- **Deliverable**: `CHANGELOG.md` updated.
- **Acceptance**: entry follows the `Round-15 P0` / `Round-15 P1`
  formatting precedent.
- **Depends on**: F.6.
- **Blocks**: G.2, G.3.

#### G.2 CLAUDE.md §3 phase-status update

- **Activity**: update [CLAUDE.md §3](../CLAUDE.md#L40) to mark
  Round-15 P2 as **CLOSED** with the F.* anchor numbers; advance
  to whatever P3 / Phase-2 / PR-024c track applies.
- **Deliverable**: CLAUDE.md edited (gitignored — local-only).
- **Acceptance**: status reflects P2 outcome.
- **Depends on**: G.1.
- **Blocks**: G.3.

#### G.3 Phase-boundary AUDIT_PROMPT.md self-trigger

- **Activity**: per [CLAUDE.md §7](../CLAUDE.md#L127) closing
  checklist, run the standard `docs/audits/AUDIT_PROMPT.md` on
  the P2 commit chain. Fix any P0/P1 findings in-session as
  `AUDIT(tag):` commits.
- **Deliverable**: audit transcript appended to `docs/audits/`.
- **Acceptance**: P0 findings addressed in-session; P1+ findings
  filed as separate follow-up tickets.
- **Depends on**: G.1.
- **Blocks**: G.4.

#### G.4 Banned-list refinement

- **Activity**: if Path α was approved in A.1, finalize the
  CLAUDE.md §6 banned-list wording to distinguish phenomenological
  TCA (banned) from algebraically-exact CRS2011 TCA (allowed for
  P2). If Path β or γ was selected, document the chosen path's
  rationale in the same §6 entry.
- **Deliverable**: CLAUDE.md §6 wording refined.
- **Acceptance**: future contributors can read the banned-list
  entry and unambiguously determine whether a proposed
  approximation falls inside or outside the ban.
- **Depends on**: A.1, G.3.
- **Blocks**: nothing — this is the closing task.

---

### Phase H — Bianchi extension hooks (deferred catalogue)

These tasks are catalogued but **not** scheduled for execution as
part of P2; they exist to prevent silent envelope expansion. They
become actionable only after P2 closes and a separate Bianchi-track
WBS is opened.

#### H.1 Anisotropic background pre-recombination

- **Activity**: extend `BianchiCosmology` shear table σ_{ab}(η)
  to η = 0.01 Mpc. The default `tilt_background_owner =
  policy-fixed` runtime control must remain the only exercised path
  unless an explicit Bianchi-track decision opens the
  `nonperturbative_tilt_rhs` gate.

#### H.2 TCA × Bianchi shear-coupling check

- **Activity**: verify that the T7 (shear-up), T8 (shear-same),
  T9 (shear-down) PSTF operators in
  [hierarchy_rhs.py:343](../htt/bass/hierarchy/hierarchy_rhs.py#L343)
  remain quiescent during the TCA-active state vector — they
  couple to E_2, Θ_2, both of which are quasi-static algebraic
  followers in TCA. No algebraic loop must form.

#### H.3 Mode subset envelope preservation

- **Activity**: confirm the FB-2.2 / FB-2.3 axis-aligned mode
  dispatch in `bass/closure/nabla_dispatch.py` continues to raise
  `OutOfScopeError` on off-axis modes regardless of η_init. P2
  cannot silently expand the honest-claim envelope listed in
  CLAUDE.md §1.

---

## §3. Dependency graph (linearized)

```
A.1 — TCA-ban path verdict
  ├── A.2 — PSTF TCA derivation (Path α)
  ├── A.3 — recomb table range
  ├── A.4 — bg_table range
  └── A.5 — super-horizon mode catalogue

A.2, A.5
  └── B.1 — TCA state dataclass
       ├── B.2 — quasi-static π_γ
       ├── B.3 — slip + v_b'
       └── B.4 — RHS dispatcher
            └── B.5 — IMEX over [0.01, 14147]

A.3, A.4, A.5, B.5
  └── C.1 — adiabatic seed at z=10⁹
       ├── C.2 — tilted seed at RD
       └── C.3 — constraint projection at RD

B.5, C.1
  └── D.1 — PCHIP domain
  └── D.2 — constraint-algebra precision
       ├── D.3 — anisotropic stress at RD
       └── D.4 — ISW driver FD4

B.5, C.*, D.*
  └── E.1 — _los_and_wrap re-verify
       └── E.2 — build_los_grid zone-0
            └── E.3 — sparse_late_isw zone-3

B.5, C.*, D.*, E.*
  └── F.1 — anchor sweep
       └── F.2 — §10 re-run
            └── F.3 — monopole diagnostic re-run
                 └── F.4 — R5 oracle regression
                      └── F.5 — TCA Fortran cross-check
                           └── F.6 — end-to-end D_ℓ comparison

F.6
  └── G.1 — CHANGELOG
       └── G.2 — CLAUDE.md §3
            └── G.3 — AUDIT_PROMPT.md
                 └── G.4 — banned-list refinement (CLAUDE.md §6)

H.1 / H.2 / H.3 — parallel catalogue, not scheduled
```

---

## §4. Risk register

| ID | Risk | Likelihood | Impact | Mitigation |
|---|---|:---:|:---:|---|
| R-1 | A.1 Path α rejected (CLAUDE.md ban applies); Path β stiff-solver unviable | M | High | Path γ (matching-asymptotic, full-ODE post-HC for sub-horizon modes) becomes the fallback; cost estimate from a B.5-equivalent benchmark |
| R-2 | TCA switchback discontinuity > machine epsilon at η_match | M | Medium | B.4 has explicit continuity test; second-order CRS2011 forms must include all CAMB-Notes 7.4–7.6 terms |
| R-3 | float64 catastrophic cancellation in Φ, Ψ at z = 10⁹ | M | High | D.2 audit; longdouble override available; in worst case, reformulate Φ via Bardeen-Wagoner gauge-invariant variables |
| R-4 | HyRec table generator cannot extend beyond z = 10⁵ without numerical instability | L | Low | A.3 fallback: Saha extrapolation for `z > recomb_table.z_max` (x_e ≡ 1 to numerical precision in fully-ionized regime) |
| R-5 | IMEX-ARK4 / Rodas5P stability fails at TCA-active state for some k range | M | Medium | B.5 smoke test catches early; re-derive Jacobian sparsity for TCA-active reduced state |
| R-6 | F.6 D_ℓ comparison fails at moderate ℓ despite §10 valid-domain match | M | Medium | Most likely cause is residual D-3-like source-extractor convention mismatch revealed only after D-2 truncation lifted; investigate via R5 oracle isolation |
| R-7 | Bianchi-extension envelope silently expands due to sub-task at H.* | L | High | H.* tasks are explicitly catalogued as deferred; honest-claim envelope test (CLAUDE.md §1.14) fails CI if expanded |
| R-8 | Anchor regression in fb53 / R10/R11 super-horizon IC tests | L | High | C.1 explicit bit-identical test at the existing η_init; new tests at η = 0.01 are additive only |
| R-9 | Wall-time blowup in fast baseline due to TCA-active integrator runs in tests | M | Low | Fast baseline tests already use small fixtures; TCA-active fixtures should be cheaper, not more expensive |
| R-10 | Banned-list wording refinement (G.4) introduces new ambiguity for downstream contributors | L | Low | G.4 reviewer requirement: any new wording must include an explicit example of what is banned and what is allowed |

---

## §5. References

### §5.1 In-repo

- [docs/V5_ROUND15_P0_D1_FIX_SUMMARY.md](V5_ROUND15_P0_D1_FIX_SUMMARY.md) — D-1 LoS grid decoupling outcome.
- [docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md](V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md) — Opus R6 / R7-corrected derivation; Appendices X (retracted parallel cycle including the AF-1 false trail) and Y (k_eq formula, recombination κ̇ values, coupled-residual estimate).
- [docs/V5_ROUND15_P1_PSTF_DERIVATION_CHATGPT.md](V5_ROUND15_P1_PSTF_DERIVATION_CHATGPT.md) — ChatGPT R10 + P1.5 integrated SSoT; R5 oracle catalogue.
- [docs/audits/v5_round15_p1_monopole_frame_diagnostic_2026-04-26.txt](audits/v5_round15_p1_monopole_frame_diagnostic_2026-04-26.txt) — first monopole-frame diagnostic; demonstrates the normalization-confound that P2 will resolve.
- [docs/lowell_bianchi_solver_reference.md](lowell_bianchi_solver_reference.md) — central tetrad/PSTF design, 18 sections.
- [project/04_implementation_specs/CAMB_Tight-Coupling_Approximation_Mapped_to_the_1_3_PSTF_Covariant_Hierarchy_…md](../project/04_implementation_specs/CAMB_Tight-Coupling_Approximation_Mapped_to_the_1_3_PSTF_Covariant_Hierarchy__Variable_Conventions__TCA_Equations__and_Implementation_Guide_for_bass_rs.md) — CAMB CRS2011 TCA mapped to BASS PSTF variables.
- [docs/PHYSICS_REFERENCES.md](PHYSICS_REFERENCES.md) — canonical bibliography.
- [CLAUDE.md §6](../CLAUDE.md) — banned-list wording (subject to G.4 refinement).

### §5.2 External

- Cyr-Racine, F.-Y. & Sigurdson, K. (2011), arXiv:1012.0569 / PRD 83, 103521. Algebraically-exact second-order TCA.
- Lewis, A., Challinor, A. & Lasenby, A. (2000), ApJ 538, 473. CAMB original paper.
- Ma, C.-P. & Bertschinger, E. (1995), ApJ 455, 7. Sync ↔ Newtonian gauge dictionary.
- Maartens, R. (1998), PRD 58, 124006. Covariant velocity / density.
- Challinor, A. & Lasenby, A. (2000), Ann. Phys. 282 I+II. PSTF photon + polarization hierarchies.
- Tsagas, C. G., Challinor, A. & Maartens, R. (2008), Phys. Rep. 465, 61. 1+3 covariant review.

---

## §6. Acceptance for the entire P2 work package

Phase G.4 closes P2 when **all** of the following are jointly true:

1. F.1 — fast-baseline test count remains at or above the post-P1.γ
   anchor of 1762, all P2 additions pass.
2. F.2 — §10 production `k_adapted` column matches the P0/P1
   `k_adapted_η100` reference at the four valid k ≤ 10⁻² cells, both
   within 5% of CAMB direct.
3. F.3 — primordial-amplitude-aligned monopole-frame diagnostic
   reaches sub-percent agreement (cand/CAMB ∈ [0.99, 1.01]) at
   η_init and η_recomb for k ∈ {10⁻³, 5·10⁻³, 10⁻²}.
4. F.4 — all 9 R5 oracles still pass at the existing tolerances.
5. F.5 — TCA cross-check against CAMB Fortran reaches ≤ 0.1% at
   5/5 cells.
6. F.6 — full-pipeline D_ℓ TT/EE comparison reaches ≤ 5% at
   ℓ ∈ [2, 50] mode-by-mode.
7. G.1, G.2, G.3, G.4 documentation closure tasks complete.

Failure of any single criterion (1)–(7) keeps P2 open until the
specific gate is re-cleared, with a corresponding follow-up
sub-commit.
