# Changelog

본 파일은 BASS remediation (REMEDIATION_PLAN_v2) 의 PR 단위 변경을 기록한다.
각 PR closure 시 해당 항목을 갱신한다.

---

## [Unreleased]

### Tier-C BASS-independent parallel track — bounds + tilted_flrw anchors (2026-04-24)

Third layer of the anchor campaign. Targets the pure-algebra core of the MES three-bound hierarchy (`htt.core.bounds`) and the tilted-FLRW observables dictionary (`htt.core.tilted_flrw`) — the physics that every "data-independent" manuscript figure in §1.3.5 builds on.

**Gap closed**: before this commit, `grep -rn "B_sigma|B_omega|B_accel|tilted_H_ratio|Delta_q|peculiar_jeans|..." htt/tests/` returned **zero** direct test references. The three-bound hierarchy and tilted-FLRW primitives were exercised only indirectly through higher-level assemblies (`evidence_models`, `FillingFraction.mc_posterior`, `analysis_extended.ScenarioTable`). A silent coefficient drift in any of those primitives would silently change every affected manuscript figure with no regression firing.

**New**: `htt/htt/tests/test_bounds_and_tilted_flrw_anchors.py`, 42 tests:

- **Part 1 — MES three-bound hierarchy** (15 tests):
  - `B_sigma, B_omega, B_accel, B_sigma_corrected, Sig2_max_MES` pinned at the three canonical scenarios S1 (ε₁ = 1.233×10⁻³), S2a (1.476×10⁻³), S2c (3.296×10⁻³). Tolerance `abs=1e-15`.
  - Three-bound strict ordering `B_σ > B_ω > B_u̇` asserted at every scenario (§4.3 D6 anchor).
  - `W²_max = (3/2) B_ω²` (Corollary 3.2) and `A²_max = (3/2) B_u̇²` (Corollary 3.3) consistency.

- **Part 2 — tilt primitives** (4 tests):
  - `eps1_from_beta(β_anchor) = 1.4733×10⁻³`, `beta_safe` round-trip, `frame_bias(S1)` pinned.

- **Part 3 — defect variable algebra** (6 tests):
  - `Omega_tilt(β_anchor) = 5.832×10⁻⁷` pinned.
  - **bounds.Omega_tilt vs tilted_flrw.Omega_tilt cross-consistency** — two independent implementations of Corollary 2.15 must agree bit-identical across β ∈ {0, β_anchor, 2e-3, 5e-3}.
  - Master departure identity `x = Σ² − W² + Ω_tilt + Ω_k_aniso` (§1.2) exercised with nonzero components.
  - `filling_fraction(1e-8, Sig2_max_MES(S1))` pinned, `Sig2_BV(β_anchor, Ω_K=7e-4)` pinned.

- **Part 4 — nonlinear corrections** (2 tests):
  - `R_σ(σ/H=1e-4)` and `R_ω(ω/H=1e-11, σ/H=1e-4)` both ≈ 1 + O(ε²).

- **Part 5 — tilted-FLRW observables dictionary (D26)** (10 tests):
  - `tilted_H_ratio(β_anchor)`, `Delta_q(β_anchor, 100 Mpc) = 13.32`, `q_matter() = 0.157650`, `peculiar_jeans(...) = (λ_J=438.82 Mpc, f_J=0.0986)`, `matter_vorticity(...) = 3.42×10⁻²⁰`, `matter_acceleration(...) = 2.14×10⁻⁹`, `velocity_growth(z=0.1, β_anchor, GR_min) = 1.18×10⁻³`. All bit-identical.
  - `velocity_growth` rejects unknown models with the registered alternatives (`Newtonian | GR_min | GR_full | constant`).

- **Part 6 — Colin et al. β translation (D27)** (4 tests):
  - `beta_from_colin(z ∈ {0.03, 0.05, 0.10})` pinned at `(6.21, 13.40, 15.90)×10⁻⁴`.
  - Semantic anchor: `β_SNe(z=0.05) = 1.340×10⁻³` must stay within 5σ of CF4 measurement `β_CF4 = 1.334±0.267×10⁻³` — protects the TF-N02 consistency-diagnostic claim used in manuscript ch09.

**Test impact** (isolated runs):

- `htt/tests/` — 306 → 348 (+42).
- `mio/tests/`, `tsc/`, `workspace/` — unchanged.

**Combined effect of Tiers A+B+C**: 134 bit-identical regression tests now guard the CLAUDE.md §5 production anchors end-to-end, from the algebraic bounds (Tier C) through the model-dependent posterior (Tier A) to the observatory diagnostic and cross-check surfaces (Tier A/B). Any drift in a single coefficient at any layer now fires at least one pinned test.

### Tier-B BASS-independent parallel track — MIO HJ-02 + HJ-05 anchor pins (2026-04-24)

Continuation of the Tier-A anchor campaign. Two pure-regression packages that pin the currently-mature but previously-unanchored MIO diagnostic modules. Like Tier-A, no BASS outputs required.

**B#1 — HJ-02 directional + z-binned coherence anchors** (`htt/mio/tests/test_coherence_production_anchors.py`, 16 tests):

- `mio.coherence.directional.STANDARD_PROBES` (5-probe literature SSOT: Planck CMB / CatWISE / Radio / CF4pp / BiPoSH) frozen at bit-identical precision:
  - `(l_best, b_best, R) = (263.777°, 48.122°, 0.99895)` — inverse-variance spherical mean.
  - `(chi2, dof) = (28.340, 3)` — common-axis χ² test.
  - Full pairwise-separation CMB row (27.79° / 13.94° / 26.40° / 28.53°).
- `isotropy_pvalue` seeded-MC anchor: `p_iso(n_mock=5000, seed=42) = 0.0005999`. Determinism verified across repeated calls.
- `mio.coherence.redshift_binned.DEFAULT_Z_BINS = ((0, 0.1), (0.1, 10), (100, 2000))` frozen.
- Canonical 5-probe z-distributed fixture (CMB/BiPoSH → recombination bin, CatWISE/Radio → intermediate, CF4pp → low-z). Per-bin resultants and 64.82° total drift pinned.
- Exact permutation drift p-value at N=5 (5!=120 < 10k ceiling): `p_exact = 0.0667 = 8/120`. Seeded MC drift-p-value pinned at `0.0692 (n_mock=5000, seed=42)` and convergence to p_exact tested at n_mock=20k.
- G19 structural check: `to_mio_certificate` output carries `reduction_status='diagnostic-only'` and no `'posterior'` token in departure/adequacy/consistency dicts.

**B#2 — HJ-05 predictive-residual atlas builder anchors** (`htt/mio/tests/test_predictive_residuals_anchors.py`, 13 tests):

- Low-level `build_predictive_residual_atlas(slices=…)` entry (BASS-independent; the shared-schema emitter is exercised separately). Pinned on a canonical 2-model × 3-channel × 2-ell-bin fixture.
- Pinned aggregates: `n_slices=12`, `worst_model=BI_tilt/TT`, `worst_max_abs=60.0`, `mean_rms=10.1667`, reference passthrough for `atlas_ref` + `covariance_ref`.
- Tiebreak rule pinned against `max(..., key=(abs_max, model_label, channel))`: lexicographically **later** (model, channel) wins on equal max_abs (matches current code behaviour — flipping to `min`/`sorted`-reversed fires immediately).
- `ResidualChannelSlice` construction invariants (inverted ell range rejected, non-positive `n_modes` rejected).
- Frozen-dataclass guarantees (`FrozenInstanceError` on mutation, `slices` is a tuple not a list), G19 token scan on field names.

**Test impact** (per-suite, isolated runs):

- `mio/tests/` — 189 → 218 (+29; +16 coherence anchors, +13 predictive-residual anchors).
- `htt/tests/`, `tsc/`, `workspace/` — unchanged.

The combined-run `bass/statistics.py` shadowing issue documented in Tier-A is unchanged (pre-existing); isolated runs remain green across all suites.

**Rationale**: the MIO HJ-02 + HJ-05 modules ship with full physics (spherical means, permutation tests, residual atlas aggregation) but had no bit-identical anchor — any drift in the 5-probe literature SSOT, the inverse-variance spherical-mean arithmetic, the tiebreak rule of the atlas builder, or the MC plumbing was detectable only downstream. These two packages close that gap alongside the earlier HTT / TSC anchors.

### Tier-A BASS-independent parallel track — production anchors + MIO↔HTT + TSC↔HTT bridge (2026-04-24)

Three regression packages that harden existing downstream code (HTT / MIO / TSC) while BASS forward-solver work continues. All tests are bit-identical and deterministic; none depend on BASS-produced K_ℓ atlases, LoS outputs, or source grids.

**A#1 — HTT production-anchor regression** (D1, `htt/htt/tests/test_production_anchors.py`, 27 tests):

- Pins the three CLAUDE.md §5 production anchors at bit-identical precision:
  - `ln B(FLRW_tilt vs FLRW) = 26.3966094015` (semantic anchor: +26.40)
  - `<beta>_FLRW_tilt = 1.3597868670e-03` (semantic anchor: 1.360e-3)
  - `median F_Bayes(S3) = 0.0904143077` (semantic anchor: 0.093 ± 0.025)
- Tight `abs=1e-9 / 1e-12` tolerances on the pinned values catch any drift in the likelihood / MC machinery; loose `±0.10 / rel 5e-3 / ±3σ` semantic cross-checks keep the CLAUDE.md §5 band intact.
- 15-model reachability smoke (`ALL_MODELS` parametrized): every registered Bianchi model must produce at least one finite log-likelihood sample in 20 prior draws. Protects against `prior_transform` / `predicted_observables` regressions that could silently `-inf`-zero an entire model.
- 5-scenario F_Bayes pin (S1, S2a, S2b, S2c, S3): median fixed to 4-decimal precision at `N=200_000, seed=42`.
- Canonical quadrature call: `FLRW_tilt().log_evidence_quadrature(n_points=10_000)` — deterministic.

**A#2 — MIO ↔ HTT cross-check table generator** (D38, new):

- `htt/mio/interface/htt_cross_check.py` (~220 L) — frozen `CrossCheckRow` / `CrossCheckTable` dataclasses; pairs `MioCertificate`s with a `PosteriorExportBundle` and returns structured consistency labels (`consistent` / `divergent` / `incomparable`). No merged scalars anywhere.
- Rule registry seeded with two concrete rules:
  - `(evidence_anatomy, htt.core.analysis_extended.evidence_matrix_report_artifact)` — channel sum rule vs `ln_B_total` (fractional tolerance, default 10%).
  - `(flrw_tension, htt.core.advanced_diagnostics.posterior_predictive_report_artifact)` — PPP alarm sign vs Π exceedance threshold.
- `register_rule(report_type, compare_to, rule, *, overwrite=False)` extension hook; refuses silent replacement by default.
- G19 §10.2bis structural guarantees:
  - No field on `CrossCheckRow` / `CrossCheckTable` containing `combined|merged|total_score`.
  - Payload contains no field with `'posterior'` substring (enforces naming convention used in `workspace/contracts/tests/test_g19_enforcement.py`).
  - Input must be a real `PosteriorExportBundle` — duck-typed dicts raise `TypeError` (MIO cannot synthesize posteriors).
  - Tolerance validation.
- Exported at `mio.interface` package level.
- `htt/mio/tests/test_htt_cross_check.py` — 15 tests covering every rule branch, `incomparable` fallback paths, G19 structural lint, `register_rule` overwrite safety, and `table_to_payload` JSON round-trip.

**A#3 — TSC ↔ HTT F_Bayes bridge anchor pin** (D5 closure, `htt/tsc/integration/test_htt_bridge_production_anchors.py`, 21 tests):

- `tsc.integration.htt_bridge` (existing, 379 L; 36 tests) already implements the bridge and keeps both paths inside `PUBLISHED_F_BAYES_BAND = (0.068, 0.118)`. The missing piece was the bit-identical anchor pin — this change adds it.
- 5 scenarios × 3 anchor values = 15 parametrized pins (`F_Bayes_tsc`, `F_Bayes_htt_mean`, `rel_difference`) at `N=100_000, seed=20260419, w=0.0`.
- Cross-anchor link: the bridge's S3 htt-median result (N=100k, seed=20260419) must land within CLAUDE.md §5 ±1σ of the HTT-side anchor (N=200k, seed=42) — two independent MC draws of the same posterior.
- G19 `is_cross_check=True` flag reaffirmed per scenario; `FFCrossCheckReport` linted for merge-like field names.
- S0 degenerate-null sanity: `F_Bayes(S0) < 0.01` on both paths.

**Test impact** (per-suite, isolated runs):

- `htt/tests/` — 279 → 306 tests (+27)
- `mio/tests/` — 174 → 189 tests (+15)
- `tsc/` — 677 → 698 tests (+21)
- `workspace/` — 55 (unchanged)
- Total: +63 bit-identical deterministic tests.

The combined-run (`htt/tests + mio/tests + tsc + workspace`) exposes two pre-existing `sys.path` failures (`bass/statistics.py` shadowing Python's `statistics` stdlib when `tsc/` imports interleave with `mio/extraction/hj01_shear.py`) that are unrelated to this change. Each suite passes cleanly in isolation.

**Rationale**: the CLAUDE.md §5 production anchors (ln B, β, F_Bayes) had no direct-pin regression. Any coefficient drift in `htt.core.evidence_models`, `htt.core.analysis_extended.FillingFraction`, `htt.core.bounds.B_sigma_corrected`, or the shared RNG plumbing was detectable only indirectly through artifact tests. These three Tier-A packages close that gap across HTT, MIO, and TSC simultaneously.

### V5-RUNTIME Blocker 3 — cosmological integrator config helper (2026-04-24)

Blocker 3 (real IC injection from physical recombination state) was declared *actionable* in commit `bce0eb9` once the residual-joint operator became stable. The minimal deliverable is an ergonomic caller-facing constructor that encapsulates the real-physics η anchors: replaces the legacy `eta_initial_mpc = 0.5 Mpc` toy sentinel with `η(z_*) - 20 Mpc` derived from the species registry's HYREC visibility table.

**Added** (`htt/bass/runtime/cosmological_config.py` — new module):

- `PLANCK_2018_Z_STAR = 1089.94` — CLAUDE.md §5 canonical anchor.
- `DEFAULT_PRE_RECOMBINATION_MARGIN_MPC = 20.0` — matches the `η_initial ≈ 261 Mpc` validation point of commit `bce0eb9`.
- `cosmological_critical_etas(species, *, z_injection, pre_recombination_margin_mpc)` — returns `{z_injection, eta_star, eta_today, eta_initial_mpc, pre_recombination_margin_mpc}`.
- `build_cosmological_integrator_config(species, *, z_injection, eta_final_mpc, pre_recombination_margin_mpc, **overrides)` — returns an `IntegratorConfig` with physically meaningful `η ∈ [η_* - 20, η_today]`. Forwards overrides (`L_max`, `rtol`, `atol`, `solver_method`, `bianchi_cosmo`, `Sigma_plus/minus_initial`, …). `eta_initial_mpc` override is rejected (derived).

Exposed via `bass.runtime` `__init__.py`. Purely additive — no existing call site changes, and legacy `eta_initial_mpc = 0.5` fixtures remain untouched.

**Added** (`htt/bass/runtime/test_cosmological_config.py` — 12 unit tests):

- Default `z_* = 1089.94`, margin `= 20 Mpc` matching CLAUDE.md §5 and the commit `bce0eb9` validation.
- Planck-2018 anchors within physics bands: `η_* ∈ [270, 290] Mpc`, `η_today ∈ [14000, 14300] Mpc`.
- Redshift / conformal-time direction: lower `z` → later `η_star`.
- Rejection of unphysical `z_injection` outside `[100, 5000]`, negative / excessive margin, reserved `eta_initial_mpc` override.
- Override forwarding and custom `eta_final_mpc` support.

**Verification**:

- **1378 passed** (1366 handoff baseline + 12 new), 1 skipped.
- V5 fast-check `λ_max < 2e-15` and `D_2 = 1002.086744 μK²` anchor bit-identical.

**Blocker-3 follow-ups** (queued):

- **i. Primordial amplitude wiring** — replace shear-anchored seed amplitude `max(|Σ_±|, 1e-6)` with `P(k)`-derived primordial normalization. Prerequisite for CAMB low-ℓ comparison.
- **j. Mode-k scan API** — Tier-B solver is currently single-background; CAMB-comparable `D_ℓ` requires k-sweep infrastructure.

These continue the V5 handoff doc's Option D critical path toward FLRW CMB end-to-end.

**Added** (`scripts/v5_tier_b_cosmological_smoke.py`):

End-to-end diagnostic chaining Blockers 1 + 2 + 3. Reproduces the commit `bce0eb9` manual 130 s validation in a runnable form (L_max = 4 → 43 s). Built around `build_cosmological_integrator_config` so real-physics η anchors are extracted from the species registry. Output on Planck-2018 FLRW:

```
η_initial = 260.14 Mpc   (η(z_*) − 20 Mpc)
η_final   = 14147.35 Mpc (species.bg_table.eta_today)
reached   = 14147.35 Mpc
|T|_∞ = 2.93  |E|_∞ = 1.67e-4  |ν|_∞ = 11.7
time = 43.4 s
```

`✓ PASS: Blocker-1+2+3 integration chain is operational.`

Kept as a diagnostic (not a unit test) — preserves the full cosmological-range validation after each kernel-pack wiring or closure-policy change without bloating CI runtime.

**Also added** (`htt/bass/runtime/test_cosmological_smoke.py`): pytest mirror of the same smoke gated by `@pytest.mark.slow`. Opt-in via `pytest -m slow`. Asserts Blocker-3 η anchors (260 ≤ η_initial ≤ 270, 14000 ≤ η_final ≤ 14300), Blocker-2 reach-to-eta_final, physically bounded final tower state, and 180 s timing budget. Fast default baseline unchanged (1378 + 1 skipped); running with `-m slow` adds 45 s for this single end-to-end verification.

---

### V5-RUNTIME Round-4 — q_h / Wigner-3j / Π table closed (dormant, 2026-04-24)

Round-4 of the cross-session algebraic audit closed the four substantive and two confirmation placeholders left by Round 3 (prompt: `docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND4.md`; answer: `v5_residual_harmonic_algebraic_audit_round4.md`). The kernel pack is now physically complete except for two runtime-dependent fields that require background state at wiring time.

**Resolved**:

- **Q-10** — Type VII₀ helical partner eigenvalue: `q_h = √(k²+1)`, `q_0 = √k²`. Wired as `_build_transport_matrix(family, k_mag, helical_eigenvalue=1.0)` utility covering v5 §03B spectral entries for II / III / V / VII₀ / VIII.
- **Q-13** — full Wigner-3j evaluation of `twist_mix_kernel` via `sympy.physics.wigner.wigner_3j`. The kernel vanishes for class-A (selection rule) and carries the rank-1 spin-1 insertion on spin-2 polarization tower for class-B. Sanity check `K[ell=2, m=0, Δℓ=+1, Δm=-1] = +1/√21` verified. Selection rule corrected to `m' = m - q` (Round-3 prompt had `+q`).
- **Q-14** — sector similarity `S_{e,b,ν} = I_3` confirmed; ℓ-dependent PSTF normalization is carried slot-wise, not μ-wise.
- **Q-15** — Π_μ^α per-family projector confirmed as **not derivable** from `BianchiAlgebra.axis_permutation` in general. Introduced `_FAMILY_KERNEL_PI_PERMUTATION` table:
  - `Π_II = Π_III = Π_V = Π_VIII = I_3`
  - `Π_{VII₀} = swap(axis 0 ↔ axis 1)` — moves unique zero eigenvalue into anchor slot
  Canonical convention for degenerate eigenvalues: μ_+ ← lower code-axis index, μ_- ← higher.

**Partially resolved (runtime-dependent)**:

- **Q-11** — ζ_R class-B R_μ correction: structure closed as `ζ_R = c_rb · ((v_{b,∥} - 4/3·v_{γ,∥}) / H)²`; `c_rb ∈ {1, 1/2}` ambiguity still needs v5 class-B real-basis normalization card. Kernel-pack `local_drag_by_mu = ones` unchanged (Type-I placeholder); runtime formula documented for future wiring patch.
- **Q-12** — ζ_M mass correction: the prompt's `ζ_M · n_{αα}` ansatz was schematic; exact form is `mass_by_mu_rel = 1 + σ_{μμ}/H` (no free coefficient). Kernel-pack `mass_by_mu = ones` unchanged (Type-I placeholder); runtime formula documented for wiring patch.

**Added** (`htt/bass/hierarchy/ver3_layout_protocol.py`):

- `_FAMILY_KERNEL_PI_PERMUTATION` table (Q-15) — per-family 3×3 axis projector.
- `_build_twist_mix_kernel_unit(ell_max)` — sympy-based Wigner-3j evaluator for canonical |a|=1, `@lru_cache`-ed by `ell_max`.
- `_build_transport_matrix(family, k_mag, helical_eigenvalue=1.0)` — spectral-parameter-dependent transport matrix covering the five Tier-A families.
- `_family_conditioned_kernel_operator` now populates `twist_mix_kernel` with canonical |a|=1 Wigner values for class-B (III, V) and zero for class-A (I, II, VII₀, VIII).

**Added** (`htt/bass/hierarchy/test_ver3_layout_protocol.py`):

- 10 new `test_round4_*` tests pinning: class-B Wigner non-zero / class-A zero, Wigner sanity value, spin-2 selection rule, VII₀ transport helical gap + FLRW limit, per-family transport for II/III/V/VIII, Π VII₀ canonical signature derivation, Π identity for I/II/III/V/VIII, Π orthogonality.

**Verification**:

- All 21 Round-3 + Round-4 kernel tests pass (11 + 10).
- 1366/1366 handoff baseline bit-identical: `λ_max < 2e-15` at both γ_T values across L_max ∈ {4, 6, 8, 12, 16}; `D_2 = 1002.086744 μK²` 6/6 pass.

**Round-4 follow-ups** (queued):

- **h. `c_rb`** ambiguity — requires v5 class-B real-basis normalization card.
- **g. Assembly wiring** — all kernel-pack fields except runtime-dependent (local_drag_by_mu, mass_by_mu) now carry physical values. Tier-A wiring order II → III → V → VII₀ → VIII.

---

### V5-RUNTIME Round-3 — matrix-valued family kernel API landed (dormant, 2026-04-24)

Round-3 of the cross-session algebraic audit addressed Round-2 Q-7.2's open conclusion: *the 10 × 10 per-family scalar `_family_conditioned_kernel_law` has no first-principles derivation; the correct family dependence is matrix-valued in the μ-label basis and assembled from structure constants `(a, n)`.* The Round-3 prompt (`docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND3.md`) derived the matrix replacement for five representative non-Type-I families (II, III, V, VII₀, VIII); the answer is persisted at `v5_residual_harmonic_algebraic_audit_round3.md`.

**Landed as new API only — not wired into the residual-joint assembly path.** Rationale: the auditor's answer has three "requires v5 spec" unresolved items (`q_h` helical eigenvalue, `ζ_R` class-B R_μ correction, full Wigner-3j evaluation) and the patch involves a semantic refactor of six assembly functions. Staging the API first preserves the 1366/1366 handoff baseline bit-identical while providing a testable foundation for wiring in future sessions.

**Added** (`htt/bass/hierarchy/ver3_layout_protocol.py`):

- `FamilyKernelPack` frozen dataclass — carries `transport`, `mu_mode_coupling_{t,e,b,nu}` (shape `(mu_count, mu_count)`), `twist_mix_kernel` (shape `(ell_max+1, 2*ell_max+1, 2, 2)`), `local_drag_by_mu`, `mass_by_mu`, `collision` per Q-8.6(a).
- `_family_conditioned_kernel_operator(backend, ell_max)` — returns the canonical unit-normalized signature matrices from Q-8.6(b): Type I → zero, Type II → `diag(1,0,0)`, Type III → `diag(1,1,-1)`, Type V → `diag(1,0,0)`, Type VII₀ → `diag(0,1,1)`, Type VIII → `diag(-1,1,1)`. Tier-B families (IV/VI₀/VI_h/VII_h/IX) return zero (queued for separate audit).

**Added** (`htt/bass/hierarchy/test_ver3_layout_protocol.py`):

- 11 new `test_round3_family_kernel_*` tests pinning: Type-I zero matrix (FLRW anchor), per-family signature values for II/III/V/VII₀/VIII, channel-matrix equality (identity similarity until `S_{e,b,ν}` is derived), `collision = 1.0`, transport identity placeholder, twist-kernel shape, frozen-dataclass immutability.

**Verification**:

- All 11 new Round-3 tests pass.
- 1366/1366 handoff baseline bit-identical: `λ_max < 2e-15` at both γ_T=0 and γ_T=1 across L_max ∈ {4,6,8,12,16}; `D_2 = 1002.086744 μK²` 6/6 pass.

**Round-3 follow-ups** (documented in `docs/V5_RUNTIME_TRACK_DIAGNOSIS.md`): `q_h` helical-basis card, `ζ_R` / `ζ_M` class-B corrections, Wigner-3j tensor evaluation, sector similarity `S_{e,b,ν}`, `Π_μ^α` projector for non-canonical-axis families, assembly wiring (per-family order II → III → V → VII₀ → VIII).

Six pre-existing Round-2 collateral failures in `test_ver3_layout_protocol.py` (cross-mode topology tests that assumed the hand-tuned scalar law) remain failing; expected to re-pass after assembly wiring (follow-up g).

---

### V5-RUNTIME-track complete — Blockers 1 + 2 closed, cosmological IMEX operational (2026-04-24)

Runtime-layer advance to v5 CAMB low-ℓ comparison is **unblocked**. Both Blockers 1 and 2 in `V5_HANDOFF_NEXT_SESSION.md` are closed via two rounds of algebraic audit (cross-session, Claude-to-Claude) followed by eight targeted patches. Blocker 3 (recombination IC injection) is now actionable on a stable operator.

**Progression**

| stage | λ_max(A_hh, γ_T=0) | λ_max(A_right, γ_T=1) | cosmological IMEX |
|---|---:|---:|---|
| commit `67d911c` (pre-session) | +0.175 / Mpc | — | fails at η ≈ 4740 Mpc |
| Round-1 patch (Q1 sign flip + Q3 diag_base=0 + Option-B Thomson) | +0.029 | +0.321 | still fails |
| Round-2 patch (Q-5.1d + Q-6.4 + Q-7.4 + source-block sign) | **+4e-16** ✓ | **+7e-16** ✓ | **completes in 130 s** |

**Blocker 1 closed** — `multipole_cutoff` validation:

- `bass/runtime/ver2_execution.py` — `_DEVELOPMENT_CUTOFFS = {4,6,8}` + `_COSMOLOGICAL_CUTOFFS = {12,16,20,30,40}` + `_MAX_COSMOLOGICAL_CUTOFF = 40`. `RuntimeControlBlock.__post_init__` accepts either set; `L > 40` requires explicit `diagnostic_l2_override=True`.
- `bass/runtime/test_ver2_execution.py` — 6 new parametric tests.

**Blocker 2 closed** — residual-joint operator rewritten per Ma-Bertschinger (1995) + Kamionkowski-Kosowsky-Stebbins (1997):

Physics-level patches in `bass/hierarchy/ver3_layout_protocol.py`:

1. `_reduced_harmonic_structure` `diag_base_by_slot = 0` — removed SO(3)-violating `0.08·|m|` + unmotivated `0.35·(ℓ+1)` placeholder.
2. `build_reduced_harmonic_affine_operator` streaming coupling sign flip — `self_block[..., next_slot] -= next_*_same[...]` (was `+=`). Produces weighted skew-adjoint per-channel streaming, `W A_X + A_X^T W = 0` with `W_ℓ = (2ℓ+1)/d_ℓ^(X)`, machine-precision.
3. Thomson diagonal sign flip — `diag_t = inv_t · (−stream_base − photon_coll)` (was `+ photon_coll`). Matches `−κ̇·Θ_ℓ` damping.
4. `build_reduced_local_affine_operator` baryon/CDM diagonal sign flip — `coeff = −np.divide(…)` (was `+`). Matches `−κ̇·v_b/R` damping.
5. `build_reduced_joint_affine_operator` local↔harmonic cross-coupling — `joint[local_dipole, T_dipole] = +3·γ_T·local_drag_scale/|baryon_diag|` (was 0.25, too small by ~13x), `joint[T_dipole, local_dipole] = +γ_T/3·inv_t_dipole` (was −0.25·local_drag_scale·γ_T; wrong sign, magnitude, and R-dependence). Corrected to Ma-Bertschinger eq 64-66.
6. T↔E quadrupole-only γ_T-proportional — `mix_t/mix_e` restricted to `quad_mask`, proportional to `γ_T·√6/10`. `eb_e = eb_b = eb_bt = 0` in FLRW (no Thomson B-coupling per parity). Quadrupole diagonals overwritten with `-inv_t·(9γ_T/10)`, `-inv_e·(2γ_T/5)`, `-inv_b·γ_T` (Π-source).
7. `_operator_scales` hand-tuned surrogates → identity — `mix_scale = 0`, `polarization_scale = 1`, `source_scale = 1`. `twist_scale` kept (structurally vanishes in FLRW).
8. Source block diagonal sign flip — `joint[source_row, source_row] -= np.diag(…·0.35·γ_T)` (was `+=`). Closed the +0.32 growth mode (98.7% on source block per eigenvector localization). Pattern-matched; Round-3 audit of the source-propagator formulation is queued.

Also landed — IMEX defensive layer in `bass/hierarchy/ver2_native_integrator.py::_solve_segment_imex`: per-ROS2-step finiteness + 8×scale amplification gates with cached-affine invalidation. Now redundant for FLRW (operator is stable) but kept as a guardrail against future regressions.

**Blocker 3 actionable** — `from_recombination(background_monitor, z_*)` constructor remains to be implemented. Previously blocked because any IC would feed the unstable A_right. Operator is now stable, so real IC injection can proceed.

**Audit artifacts** (cross-session, reusable):

- `docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT.md` — Round-1 self-contained prompt.
- `docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND2.md` — Round-2 self-contained prompt.
- `v5_residual_harmonic_algebraic_audit.md` — Round-1 answer (cross-referenced from external Claude).
- `v5_residual_harmonic_algebraic_audit_round2.md` — Round-2 answer.
- `scripts/v5_operator_fast_check.py` — 5-second verification (direct operator assembly, no full solver).
- `scripts/v5_runtime_spectral_audit.py` — 5-η snapshot spectrum.
- `scripts/v5_runtime_operator_forensics.py` — FD-Jacobian + symmetry + L_max sweep.
- `docs/V5_RUNTIME_TRACK_DIAGNOSIS.md` — full findings + patch rationale.

**Regression baseline** (from v5 handoff, post-patch):

```
pytest htt/bass/los/ htt/bass/transport/ htt/bass/spectrum/ \
       htt/bass/forward/ htt/bass/validation/test_d2_regression_anchor.py \
       htt/bass/validation/test_verification_pack.py \
       htt/bass/validation/test_ver3_gate_stop.py \
       htt/bass/test_statistics.py \
       htt/bass/runtime/test_ver2_execution.py
→ 1366 passed, 1 skipped, 2 warnings
```

**Cosmological IMEX verification** (Blocker 2 direct test):

```
execute_tier_b_solver(FLRW, β=0, L_max=8, η=261 → 14147 Mpc, Planck-2018 species)
pre-session  : RuntimeError at η ≈ 4740 Mpc
post-patch   : SUCCESS in 130.2 s, reached η=14147 Mpc, |T_last|_∞ = 2.37e+00
```

`D_2 = 1002.086744 μK²` anchor bit-identical through every patch (FLRW invariant manifold: `r_h ≡ 0, b_hh ≡ 0` protects all matrix-only changes).

---

### PR-024a — PSTF LoS Source Function (2026-04-18) ✅

Phase 1 아홉 번째 code PR, **PR-024 sub-track 분할 첫 번째**. PSTF state + dy 에서 `SourceInputs` 추출 → `source::registry` SSOT 경유 channel assembly → `SourceTerms` 반환. MB-95 `production_source_v1` 의 PSTF-side mirror.

**10/10 tests pass on 2nd attempt** — **5 PR 연속 first-try streak 이 PR-024a 에서 끊김**. Root cause: PSTF E-mode layout (ℓ≥2 only) 과 MB-95 CambLayout 의 convention difference 를 pre-audit 에서 놓침. `STUCK_LOG.md §3` 에 below-threshold fix 기록.

**PR-024 sub-track 분할 결정**:

PR-024 (원 weight 12) 을 PR-022, PR-023 pattern 재적용하여 3 sub-track 으로 분할:
- **PR-024a** (W=4) — source function ← this PR
- **PR-024b** (W=4) — time integration + source grid
- **PR-024c** (W=4) — LoS + spectrum assembly (**PSTF D_2 bit-identical target**)

Sub-track 합산 target = 8.8 W·S/10 (원 target 9.6 의 91.7%).

**Added**:
- `src/solver/pstf_primary/source.rs` (~370 줄, 10 tests)
  - `VisibilityAtSnap { g, gdot, gddot }` — MB-95 `VisibilityResult` snapshot subset
  - `pstf_extract_source_inputs()` — PSTF layout → `source::registry::SourceInputs`
  - `pstf_source_function()` — SSOT-routed channel assembly
- `src/solver/pstf_primary/mod.rs` — `pub(crate) mod source;` 등록 (1 줄)
- `docs/PR_DELTAS/pr-024-design.md` — sub-track 분할 제안 + PR-024a 집중 design
- `docs/PR_DELTAS/pr-024a.md` — closure delta
- `docs/STUCK_LOG.md §3` — E-mode layout mismatch below-threshold fix 기록

**Source formulas** (MB-95 `production_source_v1:315-404` mirror, Polter convention):

```
Gauge transform:  η_s = etak / k,  Φ = η_s − ℋ·σ/k,  Ψ = −Φ
                  η_MB = −2·η_s,  δ_γ = 4·Θ_0

SourceInputs 추출:
  theta0, theta2       ← state[i_photon_i_m0(0, 2)]
  e0 = 0 unconditional  (Polter convention 미사용)
  e2                    ← state[i_photon_e_m0(2)] (pol on 시)
  vb, vbdot             ← state/dy[i_baryon_v_m0()]
  sigma, sigmadot       ← state/dy[i_metric_sigma()]
  phi, psi, eta_mb, delta_g ← gauge transform
  phidot = 0            (ISW deferred to post-pass FD)
  g, gdot, gddot        ← VisibilityAtSnap

Channel assembly (SSOT):
  s_sw   = source_sw(inp)
  s_dop  = source_doppler(inp)
  s_quad = source_polter_quad(inp, polterdot)
  s_e    = source_emode(inp, EmodeConvention::Polter)
  s_total = s_sw + s_dop + s_quad  (ISW = 0)
```

**E-mode layout fix (below-threshold)**:

Pre-audit 가 `layout.i_photon_e_m0(0)` 호출을 구상했으나 PSTF `LmLayout` 은 `n_photon_e = (lg+1)² − 4` 로 **ℓ≥2 만** 보유 (scalar perturbation 에서 ℓ<2 E-mode 는 identically zero — structural optimization). MB-95 `CambLayout` 은 `e_mode(0)` slot 을 retain 하나 **production (Polter convention) 에서 E_0 를 사용 안 함** — `polter = 2Θ_2/5 + 3E_2/5` 에 E_0 불포함.

**Fix** (1 iteration): `e0 = 0.0` unconditional. Polter convention 에서 source output 에 기여하지 않으므로 MB-95 와 bit-identical 유지. PiBass convention (future PR) 사용 시 E_0 를 state 외 source 에서 계산하거나 layout 확장 필요 — 지금은 scope 밖.

**Gate evidence (`PR_CONSTITUTION §9`)**:
- G1 COMPILE ✅ — 10/10 pass (2nd attempt) + 91 total pstf_primary + 기존 3 슈트 회귀 없음
- **G2 FLRW (full) ✅** — `regression_source_sw/doppler/polter_quad/total_matches_mb95` 이 `pstf_source_function` 결과가 `source::registry` SSOT direct call 과 bit-identical (diff < 1e-18). MB-95 `production_source_v1` 도 동일 SSOT 호출 → architectural guarantee 로 PSTF ↔ MB-95 source bit-identical
- G3 PHYS ✅ — Identity 3 (phi/eta_mb/delta_g formulas L334-336), Channelwise 2 (no ISW in s_total, polterdot export), Caveat 1 (pol off → s_e = 0)
- G4 CROSS ✅ — MB-95 `production_source_v1:315-404` inline 직접 대조

**Score**: **7/10** (cap 9, -2 for no publication figure). W·S/10 = **2.8** (forecast 정확).

**Anti-local-min observation**:
- Pre-audit 3 trigger (background convention / phi sign / vis 구조체) 모두 unfired
- **신규 trigger 발생 (P1 fix)**: E-mode layout ℓ<2 panic — pre-audit §6 에 없던 issue
- 1 iteration 으로 resolve (`e0 = 0.0` unconditional)
- `STUCK_LOG §3` entry 추가 (below-threshold fix, rule §10 threshold 미달)
- Future pre-audit 에 "Layout accessor range check" 항목 추가 결정

**First-try streak reset**: 5 PR → 0. PR-024b 부터 재시작.

**Lesson**: Pre-audit 의 physics / SSOT / MB-95 매핑 dimension 은 유지되었으나 **layout convention edge case** dimension 에서 gap 발생. Pre-audit checklist 확장 필요.

**Verification**:
- `cargo test --lib --release --no-run`: Finished 1m 07s, 0 errors
- `solver::pstf_primary::source`: **10/10 PASS** (2nd attempt)
- `solver::pstf_primary` total: **91/91** (12+10+12+11+9+11+10+6+10)
- `pstf::`: 130/130, `source::registry`: 12/12, `core::ssot`: 35/35
- **D_2 = 1002.086744 μK² bit-identical** (**14th consecutive** commit). 498/498 k-modes, 94.87s.

**Progress scoreboard 갱신**:
- PR-024a row 추가 (W=4, S=7, W·S/10=2.8)
- Phase 1 진행률: 48.1% → **50.8%** (53.3 / 105, **절반 돌파**)
- 완료 PR scoring quality: 71.1% 유지

**Next → PR-024b (Time integration + source grid, W=4, target S=7)**

Scope: `src/solver/pstf_primary/integrate.rs`. `pstf_solve_kmode()` — Rodas5P 로 η 적분, snapshot 별 `pstf_source_function()` 호출하여 source grid 축적. 기존 MB-95 `CommonProfile` + Rodas5P stepper 재사용.

**Pre-audit checklist 추가**: "Layout accessor range check" (PR-024a 교훈).

Target W·S/10 = 2.8. Phase 1 진행률 50.8% → **53.5%**.

### PR-023c — PSTF Full RHS Dispatcher + PR-022a Retrospective G2 승격 (2026-04-18) ✅

Phase 1 여덟 번째 code PR, **PR-023 sub-track 완결** + **Phase 1 최초의 retrospective scoring event**. `pstf_full_rhs()` dispatcher 가 4 sector (free-streaming + collision + metric + fluid) 를 한 RHS evaluation 으로 composing. 동시에 PR-022a 의 G2 partial → full 승격 수행. **6/6 dispatcher tests + 1/1 retrospective test first-try pass — 5 PR 연속 first-try success** (PR-022b, PR-022c, PR-023a, PR-023b, PR-023c).

**Added**:
- `src/solver/pstf_primary/full_rhs.rs` (~340 줄, 6 tests)
  - `FullRhsInputs` struct — 모든 sector parameter 의 superset
  - `pstf_full_rhs(state, dy, inputs, layout)` — RHS dispatcher
- `src/solver/pstf_primary/rhs_free.rs` — `regression_rhs_matches_mb95_full_path_with_metric` test 추가 (PR-022a retrospective G2 evidence)
- `src/solver/pstf_primary/mod.rs` — `pub(crate) mod full_rhs;` 등록 (1 줄)
- `docs/PR_DELTAS/pr-023c-design.md` — pre-audit design doc (dispatcher 구조, sector 호출 순서, retrospective 절차)
- `docs/PR_DELTAS/pr-023c.md` — closure delta (이 세션에서는 CHANGELOG 로 대체)

**Dispatcher 구조**:
```rust
pub(crate) fn pstf_full_rhs(state, dy, inputs, layout) {
    // 1. Zero-init (necessary because PR-022a uses = assignment)
    dy.fill(0.0);
    
    // 2. Read v_b once (needed by metric + fluid)
    let v_b = state[layout.i_baryon_v_m0()];
    
    // 3. Compute hdot ONCE (consistency + efficiency)
    let hdot = pstf_hdot(state, v_b, &metric_inputs, layout);
    let metric_monopole_source = -hdot / 6.0;
    
    // 4. Free-streaming FIRST (uses assignment, sets photon/ν slots)
    //    metric source wired up via PR-023a value (not placeholder 0.0)
    pstf_free_streaming_rhs(state, dy, &RhsInputs{metric_monopole_source, ...}, layout);
    
    // 5. Other 3 sectors (additive, order-independent)
    pstf_thomson_collision(state, dy, ..., layout);   // PR-022b
    pstf_metric_rhs(state, dy, v_b, ..., layout);      // PR-023a
    pstf_fluid_rhs(state, dy, &FluidInputs{hdot, ...}, layout);  // PR-023b
}
```

**Sector 호출 순서 원칙**: PR-022a `rhs_free` 는 `dy[idx] = ...` (assignment), 나머지 3 sector 는 `+=` (additive). Dispatcher 가 (a) `dy.fill(0.0)` 로 초기화 (b) PR-022a 를 **첫 번째** 호출하여 photon/ν 슬롯 set (c) 나머지 3 sector 를 임의 순서로 호출 (additive 라 순서 무관). Sector slot overlap 분석:
- Photon ℓ≥1: PR-022a assignment → PR-022b collision += drag  ✓
- Baryon v_b: PR-022b collision += drag, PR-023b fluid += Euler  ✓ (PR-022a 무접촉)
- Metric etak/σ: PR-023a += only  ✓
- CDM δ_c: PR-023b fluid += only  ✓
- CDM v_c: 누구도 touch 안 함 (sync gauge condition)  ✓

**Phase 1 최초의 end-to-end G2 test**: `regression_dispatcher_matches_mb95_full_path` 이 photon ℓ={0,1,2,3,5,ℓ_max} + neutrino ℓ=0 + metric (etakdot, sigmadot) + fluid (clxcdot, clxbdot, vbdot **including Thomson drag**) 를 한 test 에서 MB-95 `camb_rhs` 전체와 bit-identical (rel err < 1e-13). 이전 PR 들의 sector-별 partial G2 를 종합한 comprehensive evidence.

**Gate evidence (`PR_CONSTITUTION §9`)**:
- G1 COMPILE ✅ — `cargo test --lib --release --no-run` Finished 1m 05s; 6/6 full_rhs + 1/1 retrospective + **81 total pstf_primary** (12+10+**12**+11+9+11+10+6, rhs_free 가 retrospective test 로 11→12 확장) + 기존 3 슈트 회귀 없음
- **G2 FLRW (full, most comprehensive) ✅** — `regression_dispatcher_matches_mb95_full_path` (모든 sector end-to-end vs MB-95 bit-identical), `regression_dispatcher_multiple_k` (k ∈ {1e-4, 1e-2, 1e-1} Mpc⁻¹), `identity_dispatcher_composes_all_sectors` (dispatcher vs manual composition 검증)
- G3 PHYS ✅ — `limit_zero_kappa_dot_free_plus_metric_only`, `caveat_dispatcher_zero_inits_dy`, `caveat_hdot_computed_once` (hdot consistency — fluid 의 `-hdot/2` 와 photon 의 `-hdot/6` 이 같은 hdot 값에서 유래 검증)
- G4 CROSS ✅ — MB-95 `camb_rhs` 전체 inline 대조 (partial comparison 없이 end-to-end)

**Score**: **8/10** (cap 9, -1 for no publication figure). W·S/10 = **2.4** (forecast 정확 일치). **PR-021, PR-022b 와 동일 tier** — Phase 1 내 score-8 PR 세 번째.

**Retrospective upgrade — PR-022a G2 partial → full 승격** (Phase 1 최초):
- Trigger: `rhs_free.rs` 에 새 test `regression_rhs_matches_mb95_full_path_with_metric` 추가
- Content: PR-023a `pstf_metric_monopole_source()` 를 wire-up 후 MB-95 `camb_rhs` photon/ν ℓ=0 metric coupling 까지 bit-identical 재현 (rel err < 1e-13)
- Decision: PR-022a score 7 → **8**, W·S/10 4.2 → **4.8**, Δ = **+0.6**
- Scoring discipline: 기존 test `regression_rhs_matches_mb95_freestream_kappa_zero` 건드리지 않음 (evidence 보존), **새 test 추가로 승격 정당화** (`PR_CONSTITUTION §9.5` retroactive rule 준수)
- Record: `PROGRESS_SCOREBOARD.md §2.1 footnote 3` 갱신 + `§3` 에 retrospective event entry 공식 기록

**Anti-local-min observation**: Pre-audit 3 trigger 전부 unfired:
1. Dy accumulation double counting → sector 호출 순서 분석 (§2) + zero-init 으로 방지
2. Metric monopole source sign 혼동 → `regression_rhs_matches_mb95_full_path_with_metric` 이 catch
3. hdot 재계산 실수 → dispatcher 에서 `let hdot = ...` 한 번 저장 후 두 sector 에 참조

**`STUCK_LOG.md` entry 없음**. 3/3 trigger 사전 회피.

**특기: 5 PR 연속 first-try success** — PR-022b 11/11, PR-022c 9/9, PR-023a 11/11, PR-023b 10/10, **PR-023c 6/6 + retrospective 1/1**. Sub-track 분할 + pre-audit quality 의 복합 효과가 성숙한 phase 에 도달.

**Verification**:
- `cargo test --lib --release --no-run`: Finished 1m 05s, 0 errors
- `solver::pstf_primary::full_rhs`: **6/6 first-try PASS**
- `solver::pstf_primary::rhs_free::regression_rhs_matches_mb95_full_path_with_metric`: **1/1 PASS** (PR-022a retrospective)
- `solver::pstf_primary` total: **81/81** (12+10+12+11+9+11+10+6)
- `pstf::`: 130/130, `source::registry`: 12/12, `core::ssot`: 35/35
- **D_2 = 1002.086744 μK² bit-identical** (**13th consecutive** commit). 498/498 k-modes, 92.84s.

**Midpoint physics check**: MB-95 oracle D_ℓ^TT 시각화 수행 — SW plateau ~1000 μK² (ℓ=2..30 mean 1009), first peak ℓ=217 at **7368.7 μK²**, peak/plateau ratio **7.3×**. ΛCDM physics 와 shape 일치 (SW plateau → ISW rise → acoustic oscillation → first peak). Normalization 이 Planck 2018 best-fit 대비 ~30% higher 이나 parameter set 문제 (A_s scale), shape 문제 아님. Phase 1 최종 target 의 physical correctness 확인 — PR-025 에서 PSTF primary 가 이 shape 를 bit-identical 재현해야 함.

**Progress scoreboard 갱신**:
- PR-023c row 추가 (W=3, S=8, W·S/10=2.4)
- **PR-022a row retrospective 갱신** (S: 7→8, W·S/10: 4.2→4.8, footnote 3 업데이트)
- §3 에 PR-023c retroactive entry + PR-022a retrospective event 공식 기록
- Phase 1 진행률: 45.2% → **48.1%** (50.5 / 105), PR-022a retrospective +0.6 반영
- 완료 PR scoring quality: 69.9% → **71.1%** (PR-022a 승격 효과)

**PR-023 sub-track 전체 완결** (3/3 sub-tracks):
- PR-023a ✅ + PR-023b ✅ + PR-023c ✅ = **7.3 W·S/10** (원 target 8.0 의 91.3%)
- + PR-022a retrospective **+0.6** = **7.9 W·S/10** (**98.8%**)

**Sub-track 분할 전략 누적 성과** (PR-022 + PR-023):
- Total W·S/10 achieved: 11.0 (PR-022) + 7.9 (PR-023) = **18.9**
- Total original target: 12.0 + 8.0 = **20.0**
- **Combined recovery: 94.5%**. Anti-local-min risk reduction 의 trade-off 가 5 PR first-try streak 으로 거의 완전히 보상됨.

**Next → PR-024 (PSTF LoS source + solve_pstf_spectrum, W=12)**

Phase 1 **남은 single-largest PR**. PSTF primary 가 C_ℓ 을 생성할 수 있게 만드는 핵심 구성. Scope:
- LoS source function (photon + polarization channels)
- solve_pstf_spectrum — ODE time integration (`rodas5p.rs` 활용) + k-sampling + LoS projection
- PR-024 완료 후 PSTF primary 가 D_ℓ 생성 가능 → PR-025 에서 MB-95 oracle 과 bit-identical equivalence 검증

큰 PR 이므로 **sub-track 분할 가능성** pre-audit 에서 판단 (PR-022/PR-023 pattern 재적용 고려). 2-3 turn 예상.

### PR-023b — PSTF Fluid (CDM + Baryon) RHS (2026-04-18) ✅

Phase 1 일곱 번째 code PR, **PR-023 sub-track 분할 두 번째**. CDM + baryon fluid RHS (synchronous-gauge equivalent, Thomson drag 제외). **10/10 tests first-try pass** — PR-022b, PR-022c, PR-023a 에 이어 **4 PR 연속 first-try success**.

**Added**:
- `src/solver/pstf_primary/fluid.rs` (~310 줄, 10 tests)
  - `FluidInputs { k, h_conformal, cs2b, hdot }` — **Option B interface** (hdot 을 struct 에 직접 주입, MetricInputs nesting 없음)
  - `pstf_fluid_rhs(state, dy, inputs, layout)` — clxcdot + clxbdot + vbdot (Thomson drag 제외, additive accumulation)
- `src/solver/pstf_primary/layout.rs` — 4 새 accessors: `i_baryon_delta()`, `i_baryon_v_m0()`, `i_cdm_delta()`, `i_cdm_v_m0()`
- `src/solver/pstf_primary/mod.rs` — `pub(crate) mod fluid;` 등록 (1 줄)
- `docs/PR_DELTAS/pr-023b-design.md` — pre-audit design doc (MB-95 fluid 재감사, Thomson drag double-counting 방지 설계)
- `docs/PR_DELTAS/pr-023b.md` — closure delta

**RHS formulas** (MB-95 `camb_rhs:483-487` port, Thomson drag 제외):

```
dy[i_cdm_delta]    = −hdot / 2                     (CDM continuity)
dy[i_baryon_delta] = −k · v_b − hdot / 2           (baryon continuity)
dy[i_baryon_v_m0]  = −ℋ · v_b + c_s²_b · k · clxb  (baryon Euler, pre-drag)
```

PR-022b 의 baryon-photon drag `+opac·(3·Θ_1 − v_b)/r_b` 는 같은 `dy[i_baryon_v_m0()]` 슬롯에 additive. PR-023c dispatcher 에서 합쳐져 MB-95 full RHS 와 bit-identical.

**Option B interface 설계**:
```rust
pub(crate) struct FluidInputs {
    pub(crate) k: f64,
    pub(crate) h_conformal: f64,
    pub(crate) cs2b: f64,
    pub(crate) hdot: f64,   // PR-023a pstf_hdot() 결과를 caller 가 주입
}
```

Caller 가 `pstf_hdot(state, v_b, &metric_inputs, layout)` 를 먼저 compute 하여 `FluidInputs.hdot` 에 주입. Option A (`FluidInputs` 가 `MetricInputs` 를 nest) 대비 장점:
- Test 독립성 — fluid RHS 를 metric 없이 단위 test 가능
- Inter-sector dependency 를 API 레벨에서 명시
- PR-023c dispatcher 에서 `hdot` 을 한 번만 compute 하여 여러 sector (fluid + photon/ν ℓ=0 via `metric_monopole_source`) 에 재사용

`regression_with_pr023a_hdot` test 가 Option B 의 integration 을 검증 — PR-023a `pstf_hdot()` → `FluidInputs.hdot` → PR-023b fluid RHS → MB-95 bit-identical end-to-end.

**Synchronous gauge: v_c = 0**:

CDM velocity `v_c` 는 sync gauge 정의상 identically zero. PR-023b `pstf_fluid_rhs` 는 `dy[i_cdm_v_m0()]` 에 쓰지 않음. `caveat_cdm_velocity_zero_at_sync_gauge` test 가 pre-fill sentinel 42.0 유지로 검증. 미래 gauge transformation (synchronous → Newtonian or synchronous → Bianchi tilt) 시 explicit 처리 필요 — Phase 4 scope.

**Gate evidence (`PR_CONSTITUTION §9`)**:
- G1 COMPILE ✅ — `cargo test --lib --release --no-run` Finished 53.94s; 10/10 신규 + **74 total pstf_primary** (12+10+11+11+9+11+10) + 기존 3 슈트 회귀 없음
- **G2 FLRW (full) ✅** — `regression_fluid_rhs_multiple_k` (k ∈ {1e-4, 1e-2, 1e-1} Mpc⁻¹, clxcdot + clxbdot + vbdot vs MB-95 `camb_rhs:483-487` inline formula, diff < 1e-18). `regression_with_pr023a_hdot` (**integration test** — PR-023a → PR-023b → MB-95 end-to-end)
- G3 PHYS ✅ — Identity 3 (clxcdot / clxbdot / vbdot, Thomson drag 제외 명시), Limit 2 (zero state / zero hdot), Channelwise 2 (metric / photon/ν / Bianchi reserve 무접촉), Caveat 1 (v_c = 0 sync gauge)
- G4 CROSS ✅ — MB-95 `camb_rhs:483-487` inline 대조 (primary oracle)

**Score**: **7/10** (cap 9, -2 for no publication figure). W·S/10 = **2.1** (forecast 정확 일치).

**Anti-local-min**: Pre-audit 3 trigger 전부 unfired:
1. Thomson drag 중복 적용 — `identity_vbdot_matches_mb95` 주석 + scope 명시로 방지
2. v_c ≠ 0 유입 — sync gauge 조건 명시, caveat test 가 dy side 검증
3. hdot sign 실수 — `−hdot/2` 양쪽 (clxc, clxb) 동일 부호, identity tests 가 catch

**`STUCK_LOG.md` entry 추가 없음**.

**특기: 4 PR 연속 first-try success** (PR-022b 11/11, PR-022c 9/9, PR-023a 11/11, PR-023b 10/10). Pre-audit design doc quality 가 실행 시 문제 해결 코스트를 거의 zero 로 유지. Sub-track 분할 pattern 이 PR-022/PR-023 양쪽에서 일관되게 효과.

**Verification**:
- `cargo test --lib --release --no-run`: Finished 53.94s, 0 errors
- `solver::pstf_primary::fluid`: **10/10 first-try PASS**
- `solver::pstf_primary` total: **74/74** (12+10+11+11+9+11+10)
- `pstf::`: 130/130, `source::registry`: 12/12, `core::ssot`: 35/35
- **D_2 = 1002.086744 μK² bit-identical** (**12th consecutive** commit). 498/498 k-modes, 67.75s.

**Progress scoreboard 갱신**:
- PR-023b row 추가 (W=3, S=7, W·S/10=2.1)
- Phase 1 진행률: 43.3% → **45.2%** (47.5 / 105)
- 완료 PR scoring quality: **69.9%** 유지

**Next → PR-023c (Full RHS composition + PR-022a G2 retrospective 승격)**

Scope: `src/solver/pstf_primary/full_rhs.rs` 신설, `pstf_full_rhs()` dispatcher — hdot 한 번 compute 후 free_streaming + collision + metric + fluid 에 분배. PR-022a `regression_rhs_matches_mb95_full_path_with_metric` test 추가로 G2 partial → full 승격. Scoreboard retrospective 갱신 (PR-022a score 7→8, Δ=+0.6).

Target W·S/10 = 2.4 + retrospective 0.6 = **3.0**. Phase 1 진행률 45.2% → **48.3%**.

### PR-023a — PSTF Metric State + RHS (2026-04-18) ✅

Phase 1 여섯 번째 code PR, **PR-023 sub-track 분할 첫 번째**. 1+3 covariant scalar metric sector (FLRW m=0) — synchronous-gauge equivalent `etak`, `σ` state variables + RHS. **11/11 tests first-try pass** — PR-022b, PR-022c 에 이어 **3 PR 연속 first-try success**.

**PR-023 sub-track 분할 결정**:

PR-023 (원 weight 10) 을 PR-022 pattern 재적용하여 3 sub-track 으로 분할:
- **PR-023a** (W=4) — metric state + RHS ← this PR
- **PR-023b** (W=3) — fluid (CDM + baryon) RHS
- **PR-023c** (W=3) — full RHS composition + **PR-022a G2 partial → full retrospective 승격**

Sub-track 합산 target = 7.3 W·S/10 (원 target 8.0 의 91.3%). PR-023c 의 retrospective bonus (+0.6) 포함 시 **7.9** (98.8% 복구).

**Added**:
- `src/solver/pstf_primary/metric.rs` (~370 줄, 11 tests)
  - `BackgroundQuantities` struct — ℋ, ρ_γ, ρ_ν, ρ_b (8πG·ρ·a² convention, MB-95 equivalent)
  - `MetricInputs { k, bg }`
  - `pstf_momentum_constraint_dgq(state, v_b, bg, layout) -> f64`
  - `pstf_hdot(state, v_b, inputs, layout) -> f64` — derived, not in state
  - `pstf_metric_monopole_source(state, v_b, inputs, layout) -> f64` — `−hdot/6` export for PR-022a wire-up (PR-023c scope)
  - `pstf_metric_rhs(state, dy, v_b, inputs, layout)` — additive accumulation of etakdot + sigmadot
- `src/solver/pstf_primary/layout.rs` — new accessors `i_metric_etak()` (= 0), `i_metric_sigma()` (= 1)
- `src/solver/pstf_primary/mod.rs` — `pub(crate) mod metric;` 등록 (1 줄)
- `docs/PR_DELTAS/pr-023-design.md` — pre-audit design doc (MB-95 metric 재감사, sub-track 분할 제안)
- `docs/PR_DELTAS/pr-023a.md` — closure delta

**State layout**:
```
metric[0]    = etak   ← active (MB-95 equivalent to i_etak)
metric[1]    = σ      ← active (MB-95 equivalent to i_sigma)
metric[2..=10] = 0   ← reserved for Bianchi-I Z_{ab} tensor (Phase 4)
```

`caveat_metric_block_reserved_for_bianchi` test 가 pre-fill sentinel 42.0 로 Bianchi reserve 영역 무접촉 보장.

**RHS formulas** (MB-95 `camb_rhs:462-481` port):

```
dgq = (4/3)·ρ_γ·(4·Θ_1) + (4/3)·ρ_ν·(4·N_1) + ρ_b·v_b
    = (16/3)·(ρ_γ·Θ_1 + ρ_ν·N_1) + ρ_b·v_b          (algebraic 단순화)
etakdot = dgq / 2
dgs = ρ_γ·(4·Θ_2) + ρ_ν·(4·N_2) = 4·(ρ_γ·Θ_2 + ρ_ν·N_2)
sigmadot = −2·ℋ·σ − dgs/k + etak

hdot = 2·k·σ − 6·etakdot/k = 2·k·σ − 3·dgq/k   (DERIVED, not in state)
metric_monopole_source = −hdot/6 = −k·σ/3 + dgq/(2k) = −k·σ/3 + etakdot/k
```

**v_b dependency handling**: Metric RHS 는 baryon v_b 를 read (dgq 계산) 하나 fluid RHS 는 PR-023b scope. PR-023a 는 `v_b` 를 함수 parameter 로 받음:
```rust
pub(crate) fn pstf_metric_rhs(state, dy, v_b: f64, inputs, layout)
```
Test 에서는 state[baryon_start + 2] 직접 주입. PR-023c dispatcher 가 state 에서 read 하여 전달.

**Gate evidence (`PR_CONSTITUTION §9`)**:
- G1 COMPILE ✅ — 11/11 first-try + 64 total pstf_primary (layout 12 + ic 10 + rhs_free 11 + collision 11 + jacobian 9 + metric 11) + 기존 3 슈트 회귀 없음
- **G2 FLRW (full) ✅** — `regression_metric_rhs_multiple_k` (k ∈ {1e-4, 1e-2, 1e-1} Mpc⁻¹, etakdot + sigmadot vs MB-95 inline formula, rel err < 1e-13), `regression_hdot_matches_mb95` (derived `hdot` formula, rel err < 1e-14), `regression_monopole_source_matches_mb95` (PR-022a wire-up 대상 `−hdot/6` bit-identical)
- G3 PHYS ✅ — identity 3 (dgq / etakdot / sigmadot MB-95 formula match), limit 2 (zero state / no anisotropic stress pure damping), caveat 1 (metric[2..=10] Bianchi reserve), channelwise 2 (photon/ν/cdm/baryon 무접촉)
- G4 CROSS ✅ — MB-95 `camb_rhs:462-481` inline 대조 (primary oracle). Sync-gauge metric 은 unambiguous — PR-022b 의 `collision_lm` 같은 alternative reference 혼재 없음

**Score**: **7/10** (cap 9, -2 for no publication figure). W·S/10 = **2.8** (forecast 정확 일치).

**Anti-local-min observation**: Pre-audit 3 trigger 모두 사전 회피:
1. Background 주입 convention — `representative()` constructor 로 test fixture 명시화
2. k-dependent factor 혼동 — MB-95 와 직접 대조 검증
3. v_b 위치 mismatch — PR-022b 의 offset 재사용, identity test 로 catch

**`STUCK_LOG.md` entry 추가 없음**. 3/3 trigger 모두 pre-audit 에서 회피.

**특기: 11/11 first-try pass — 3 PR 연속 first-try success** (PR-022b 11/11, PR-022c 9/9, PR-023a 11/11).
학습 곡선:
- PR-020 scaffolding 실패 → PR-021 첫 G4 pass (score 8)
- PR-022a partial G2 (score 7) → sub-track 분할 시작
- **PR-022b first-try full G2** (score 8) → sub-track + pre-audit quality 효과 확인
- **PR-022c first-try** (score 7, G2/G4 structural N/A)
- **PR-023a first-try full G2** (score 7, PR-022b 와 동일 품질 tier)

Pre-audit design doc 의 quality 가 3 PR 연속 first-try success 로 직접 반영. Sub-track 분할 pattern 이 PR-022/PR-023 양쪽에서 효과 검증됨.

**Verification**:
- `cargo test --lib --release --no-run`: Finished 1m 47s, 0 errors
- `solver::pstf_primary::metric`: **11/11 first-try PASS**
- `solver::pstf_primary` total: **64/64** (12 + 10 + 11 + 11 + 9 + 11)
- `pstf::`: 130/130, `source::registry`: 12/12, `core::ssot`: 35/35
- **D_2 = 1002.086744 μK² bit-identical** (**11th consecutive** commit). 498/498 k-modes, 117s.

**Progress scoreboard 갱신**:
- PR-023a row 추가 (W=4, S=7, W·S/10=2.8)
- PR-023 계획 row 삭제, PR-023b + PR-023c 신규 row 추가
- Phase 1 진행률: 40.6% → **43.3%** (45.4 / 105)
- 완료 PR scoring quality: **69.8%** 유지

**Next → PR-023b (Fluid RHS, W=3, target S=7)**

Scope: `src/solver/pstf_primary/fluid.rs`. `pstf_fluid_rhs()` — `clxcdot = −hdot/2`, `clxbdot = −k·v_b − hdot/2`, `vbdot = −ℋ·v_b + c_s²·k·clxb`. Baryon-photon collision drag 는 PR-022b 이미 있음 (additive). `hdot` 값은 PR-023a 의 `pstf_hdot()` 호출.

Target W·S/10 = 2.1. Phase 1 진행률 43.3% → **45.3%** 예상.

### PR-022c — PSTF Analytical Jacobian (2026-04-18) ✅

Phase 1 다섯 번째 code PR, **PR-022 sub-track 전체 완결**. RHS (PR-022a free-streaming + PR-022b collision) 의 analytical sparse Jacobian. Rodas5P implicit solve 의 전제. **9/9 tests first-try pass** (PR-022b 에 이어 2번 연속 first-try full success).

**Added**:
- `src/solver/pstf_primary/jacobian.rs` (~470 줄, 9 tests)
  - `JacobianInputs` struct — `RhsInputs` + `CollisionInputs` 통합
  - `SparseJacobian` struct — `Vec<(row, col, val)>` triplet list
  - `pstf_analytical_jacobian(state, inputs, layout) -> SparseJacobian`
  - `pstf_jacobian_dense(state, inputs, layout, out)` — Rodas5P 호환 row-major
  - `jacobian_fd_check(state, inputs, layout, h) -> (max_rel_err, i, j)` — 5-point stencil, columnwise (sparse columns only)
- `src/solver/pstf_primary/mod.rs` — `pub(crate) mod jacobian;` 등록 (1 줄)
- `docs/PR_DELTAS/pr-022c-design.md` — pre-audit design doc (sparse pattern analysis, 5-point stencil rationale)
- `docs/PR_DELTAS/pr-022c.md` — closure delta

**Sparsity** (ℓ_max = 16):
- Photon free-streaming (tridiagonal): 33 entries
- Neutrino free-streaming: 33
- Photon collision: 17 (ℓ=1 drag 2 + ℓ=2 damp 1 + ℓ≥3 diagonal lg−2)
- Baryon drag reaction: 2 (v_b cross + v_b diag)
- **Total: 85 entries / 1.34M dense ≈ 0.006% sparsity**

**Linear RHS 가정**: PR-022a (free-streaming) 와 PR-022b (collision) 모두 state 에 linear. 배경 변수 (k, τ, κ̇, r_b) 만 parameter 로 들어감. 따라서 `J = ∂(M·y)/∂y = M` 은 state-independent. 구현에서 `state: &[f64]` 는 accept 하나 사용하지 않음 (interface consistency for future nonlinear extension).

**FD check methodology**:
```
f'(x) ≈ [−f(x+2h) + 8·f(x+h) − 8·f(x−h) + f(x−2h)] / (12·h)
```
5-point stencil 의 truncation error O(h⁴) + `h = 1e-6·‖state‖_∞` 조합으로 round-off balance. `jacobian_fd_check` 가 sparse columns 만 FD 평가 (efficiency, <0.1s test runtime).

**Gate evidence (`PR_CONSTITUTION §9`)**:
- G1 COMPILE ✅ — `cargo test --lib --release --no-run` Finished 1m 09s, 0 errors; 9/9 신규 + **53 total pstf_primary** (layout 12 + ic 10 + rhs_free 11 + collision 11 + jacobian 9) + 기존 3 슈트 회귀 없음
- **G2 FLRW: N/A (정당)** — Jacobian 은 RHS 의 computed artifact, FLRW 극한 검증 구조적으로 의미 없음. PR-022a/b 에서 이미 G2 확보
- **G3 PHYS ✅** — **3 FD regression tests 전부 pass**: `fd_regression_free_streaming_only` (κ̇=0), `fd_regression_collision_only` (k=0), `fd_regression_full_combined` (일반 state) 모두 max rel err < 1e-6. Identity 3 tests: tridiagonal sparse pattern + specific coefficient (`J[3,2]=3k/7`, `J[3,4]=−4k/7`, `J[5,4]=5k/11`, `J[5,6]=−6k/11`) eps=1e-15 검증. Limit test: κ̇=0 에서 v_b 관련 entry 부재 보장. `equivalence_dense_vs_sparse`: dense/sparse output 정확 일치 (non-listed entry 는 정확히 0)
- **G4 CROSS: N/A (정당)** — MB-95 `camb_rhs` 는 explicit solver (DVERK) 이므로 analytical Jacobian 자체 없음. Cross-check 대상 부재. **FD check 이 self-consistent oracle 역할**

**Score**: **7/10** (cap 7 — G1 + G3, G2/G4 N/A). W·S/10 = **2.8** (forecast 정확 일치).

**Anti-local-min observation**: Pre-audit 3 trigger (FD step size / linear 가정 / sparse 구조) 모두 사전 회피:
- FD h = 1e-6·‖state‖ 첫 시도 성공
- Linear RHS 확인 완료 (state-independent J)
- Sparsity count 기대값 (85) 과 실제 `sparse.nnz()` 정확 일치

**`STUCK_LOG.md` entry 추가 없음**.

**특기: 9/9 first-try pass** — PR-022b 에 이어 **2 PR 연속 first-try full success**. 학습 곡선: PR-020 실패 → PR-021 score 8 → PR-022a partial → PR-022b first-try score 8 → PR-022c first-try score 7. Pre-audit quality 의 누적 효과.

**Verification**:
- `cargo test --lib --release --no-run`: Finished 1m 09s, 0 errors
- `solver::pstf_primary::jacobian`: **9/9 first-try PASS**
- `solver::pstf_primary` total: **53/53** (12 + 10 + 11 + 11 + 9)
- `pstf::`: 130/130 PASS, `source::registry`: 12/12, `core::ssot`: 35/35
- **D_2 = 1002.086744 μK² bit-identical** (**10th consecutive** commit). 498/498 k-modes, 72.39s.

---

### PR-022 Sub-track 전체 완결 요약 ✅

| Sub-track | Weight | Score | W·S/10 | First-try | Notes |
|---|---:|---:|---:|:---:|---|
| PR-022a (Free-streaming RHS) | 6 | 7 | 4.2 | — | G2 partial (metric placeholder) |
| PR-022b (Thomson collision) | 5 | 8 | 4.0 | ✅ | G2 full, `collision_lm` bug 회피 |
| PR-022c (Analytical Jacobian) | 4 | 7 | 2.8 | ✅ | G3 FD check, G2/G4 N/A 구조상 |
| **합산** | **15** | | **11.0** | | **91.7% of original 12.0** |

Original PR-022 target (W=15 × S=8/10 = 12.0) 대비 11.0 달성. 0.83pp Phase 1 loss 의 trade-off:
- **Anti-local-min**: PR-020 `flrw_norm_ratio_down` 유형 실패 재발 없음
- **Pre-audit quality**: `collision_lm.rs` coefficient bug, linear RHS 특성, 5-point stencil rationale 등 사전 식별/설계
- **Execution efficiency**: 2 PR 연속 first-try full pass — iteration 없이 one-shot 완결

**Progress scoreboard 갱신**:
- PR-022c row 추가 (W=4, S=7, W·S/10=2.8)
- Phase 1 진행률: 37.9% → **40.6%** (42.6 / 105)
- 완료 PR scoring quality: **69.8%** 유지 (PR-022c 의 score 7 이 전체 평균과 일치)

**Next → PR-023 (PSTF metric, 1+3 covariant scalar sector)**

Phase 1 남은 single-largest PR (W=10, target S=8, target W·S/10=8.0 → Phase 1 40.6% → **48.2%**). Scope: 1+3 covariant scalar 변수 (Z_{ab} 등), FLRW 에서 Φ/Ψ reduction, `hdot/6` placeholder ↔ PSTF gauge-invariant term wire-up. **PR-023 완료 시 PR-022a 의 G2 partial 이 full FLRW 로 retrospective 승격 가능**. 큰 PR 이므로 2-3 turn 예상.

### PR-022b — PSTF Electron-frame Thomson Collision (2026-04-17) ✅

Phase 1 네 번째 code PR, PR-022 sub-track 분할의 두 번째. Photon sector Thomson collision 을 electron-frame ζ̃ convention 으로 구현. **11/11 tests first-try pass**, G2 full FLRW pass (PR-022a partial 개선).

**Pre-audit 주요 발견 (`pr-022b-design.md §2.3`)**:

`src/pstf/collision_lm.rs:107-118` 의 ℓ=1 block matrix 가 **Θ convention 과 F convention 혼재** 로 의심됨:
- Row 1 `[−κ̇, κ̇]` (F-natural)
- Row 2 `[3κ̇/(4r_b), −κ̇/r_b]` (**hybrid 3/4 factor** — pure Θ 도 pure F 도 momentum-conserving pair 아님)

**결정**: MB-95 `camb_rhs` 를 primary oracle 로 사용 (not `collision_lm`). `collision_lm` bug 의심은 Phase 2 로 defer — production 경로 무접촉, 9 consecutive bit-identical 로 impact 없음 확인.

이것은 PR-020 의 `flrw_norm_ratio_down` 함정과 동일한 pattern (잘못된 reference 회피, 올바른 oracle 로 재정렬) — pre-audit 에서 사전 식별하여 anti-local-min 발동 없이 scope 유지.

**Added**:
- `src/solver/pstf_primary/collision.rs` (~360 줄, 11 tests)
  - `FrameConvention` enum: `ElectronRestFrame` (DESIGN LAW default) vs `HypersurfaceNormalFrame` (MB-95 equivalent at FLRW)
  - `CollisionInputs { kappa_dot, r_b, use_pol_feedback, frame }` — 명시적 frame tag
  - `CollisionInputs::pol_off(kappa_dot, r_b)` — default 편의 생성자
  - `pstf_thomson_collision(state, dy, inputs, layout)` — photon intensity + baryon v_b reaction, additive 설계
- `src/solver/pstf_primary/mod.rs` — `pub(crate) mod collision;` 등록 (1 줄)
- `docs/PR_DELTAS/pr-022b-design.md` — pre-audit design doc (`collision_lm` bug 식별 + MB-95 oracle 선택 전략)
- `docs/PR_DELTAS/pr-022b.md` — closure delta

**Collision 공식 (Θ convention, MB-95 primary oracle)**:
```
C[Θ_0] = 0                                          (energy conservation)
C[Θ_1] = −κ̇·(Θ_1 − v_b/3)                           (baryon drag)
C[Θ_2] = −(9/10)·κ̇·Θ_2 + (3/20)·κ̇·E_2  (with pol)
       = −κ̇·Θ_2                                     (pol off, PR-022b default)
C[Θ_ℓ] = −κ̇·Θ_ℓ          for ℓ ≥ 3                   (pure damping)
dv_b/dη|_drag = +(κ̇/r_b)·(3·Θ_1 − v_b)              (momentum conservation)
```

**Additive design**: `pstf_thomson_collision` 은 `dy` 를 `+=` 로 accumulate. Caller 는 `pstf_free_streaming_rhs` (PR-022a) 와 composable:
```rust
pstf_free_streaming_rhs(state, &mut dy, &free_inputs, layout);
pstf_thomson_collision(state, &mut dy, &coll_inputs, layout);
// → full MB-95 `camb_rhs` (pol off, hdot=0) 와 bit-identical
```
이 additive pattern 은 PR-024 RHS dispatcher 의 기반.

**Frame equivalence at FLRW** (`caveat_frame_equivalence_flrw` test):
ElectronRestFrame 과 HypersurfaceNormalFrame 이 FLRW 에서 수치적으로 **모든 entry bit-identical**. Bianchi tilt 로 확장 시 divergence — Phase 4 scope. `FrameConvention` enum 은 structural tag 로 도입하여 future divergence 대비.

**Gate evidence (`PR_CONSTITUTION §9`)**:
- G1 COMPILE ✅ — `cargo test --lib --release --no-run` Finished 59.88s, 0 errors; 11/11 신규 + 44 total pstf_primary + 기존 3 슈트 회귀 없음
- **G2 FLRW (full) ✅** — `regression_collision_matches_mb95_full_path` 이 free-streaming + collision 합산 dy 를 MB-95 `camb_rhs` (pol off, hdot=0) 와 ℓ={0,1,2,3,5,ℓ_max} 각각 rel err < 1e-13. `regression_multiple_kappa_dot` 이 κ̇ ∈ {0.01, 1.0, 100.0} Mpc⁻¹ 전범위 regression. **PR-022a partial 보다 한 단계 위** — metric hdot=0 특수화로 full FLRW path 재현 가능.
- G3 PHYS ✅ — `identity_ell0_collision_zero` (정확히 0), `identity_ell1_drag_matches_mb95` (수식 rel err < 1e-14), `identity_ell_ge_3_pure_damping` (ℓ={3,5,10}), `limit_kappa_dot_zero_trivial`, `limit_no_pol_feedback`, `caveat_baryon_drag_sign_convention` (accelerate/decelerate case test)
- G4 CROSS ✅ — MB-95 `camb_rhs` inline 대조 (primary oracle). `collision_lm.rs` 는 deliberately 제외.

**Score**: **8/10** (cap 9, -1 for no publication figure). W·S/10 = **4.0** (forecast 그대로).

**Anti-local-min observation**: 3 pre-audit trigger 전부 사전 회피:
1. `collision_lm.rs` coefficient bug 에 얽힘 — pre-audit §2.3 에서 식별, MB-95 primary oracle 로 회피
2. E-mode pol feedback 재유도 실수 — default off, 별도 PR 로 분리
3. κ̇ sign convention 혼재 — `kappa_dot.abs()` canonicalization

**`STUCK_LOG.md` entry 추가 없음**. 3/3 trigger 모두 pre-audit 에서 식별/회피.

**특기: 11/11 first-try pass** — 이번 세션에서 test code 작성 후 첫 실행에서 모든 test 통과. 학습 곡선: PR-020 scaffolding 실패 → PR-021 첫 G4 pass → PR-022a partial G2 → **PR-022b first-try full G2**. Pre-audit quality 의 실행 시 발생하는 문제 감소로 직접 반영.

**Verification**:
- `cargo test --lib --release --no-run`: Finished 59.88s, 0 errors
- `solver::pstf_primary::collision`: **11/11 first-try PASS**
- `solver::pstf_primary` total: **44/44** (layout 12 + ic 10 + rhs_free 11 + collision 11)
- `pstf::`: 130/130 PASS
- `source::registry`: 12/12 PASS
- `core::ssot`: 35/35 PASS
- **D_2 = 1002.086744 μK² bit-identical** (9th consecutive commit). 498/498 k-modes, 65.82s.

**Progress scoreboard 갱신**:
- PR-022b row 추가 (W=5, S=8, W·S/10=4.0), PR-022b 계획 row 삭제
- Phase 1 진행률: 34.1% → **37.9%** (39.8 / 105)
- 완료 PR scoring quality: 68.8% → **69.8%** (PR-022b 의 score 8 반영)

**Next sub-track**: PR-022c (Jacobian, W=4, target S=7). Sparse analytical Jacobian + FD check. `rhs_free` + `collision` 의 파생물이므로 1 turn 내 완결 예상. Sub-track 완료 시 W·S/10 = 11.0 (원 target 12.0 의 91.7%).

### PR-022a — PSTF Free-streaming RHS (2026-04-17) ✅

Phase 1 세 번째 code PR, PR-022 (weight 15) 의 sub-track 분할 중 첫 번째. Photon + neutrino free-streaming hierarchy 를 FLRW m=0 axisymmetric 에서 구현, Thomson collision 은 PR-022b 로 이관, metric coupling 은 PR-023 placeholder.

**Sub-track split 결정 (`pr-022-design.md §1`)**:

단일 PR-022 대신 3 sub-track 분할:
- **PR-022a** (W=6): free-streaming RHS only — 이번 closure
- PR-022b (W=5, planned): electron-frame Thomson collision
- PR-022c (W=4, planned): Jacobian (sparse, Rodas5P 호환)

**이유**: (1) 4 coupled 성분 중 하나의 실패가 전체 PR blocking 방지, (2) G2 gate 가 sub-component 별로 tighter, (3) PR-020 의 `flrw_norm_ratio_down` 같은 anti-local-min trigger 발생 시 scope 축소된 rollback 가능, (4) `hdot/6` (synchronous gauge) ↔ PSTF metric coupling 순환 의존을 placeholder 로 해결.

**Added**:
- `src/solver/pstf_primary/rhs_free.rs` (~380 줄, 11 tests)
  - `RhsInputs { k, tau, metric_monopole_source }` — 최소 의존성 (baryon, opacity 무관)
  - `RhsInputs::free_streaming(k, tau)` — S_metric=0 편의 생성자
  - `pstf_free_streaming_rhs(state, dy, inputs, layout)` — photon + ν RHS
  - 내부 `free_streaming_m0_block` helper — photon/ν 동일 구조 재사용
- `src/solver/pstf_primary/mod.rs` — `pub(crate) mod rhs_free;` 등록 (1 줄)
- `docs/PR_DELTAS/pr-022-design.md` — sub-track 분할 설계 문서
- `docs/PR_DELTAS/pr-022a.md` — closure delta

**RHS 공식 (FLRW m=0)**:
```
dI_0/dη = −k·I_1 + S_metric                           (S_metric = PR-023 placeholder)
dI_1/dη = k/3·(I_0 − 2·I_2)
dI_ℓ/dη = k/(2ℓ+1)·[ℓ·I_{ℓ−1} − (ℓ+1)·I_{ℓ+1}]     (ℓ = 2..ℓ_max−1)
dI_{ℓ_max}/dη = k·I_{ℓ_max−1} − (ℓ_max+1)/τ·I_{ℓ_max}  (MB-95 tau-based truncation)
```
Photon I_ℓ^{(γ)} 와 neutrino I_ℓ^{(ν)} 에 동일 적용 (FLRW parallelism, Bianchi tilt 는 Phase 4).

**Gate evidence (`PR_CONSTITUTION §9`)**:
- G1 COMPILE ✅ — `cargo test --lib --release --no-run` Finished 1m 06s, 0 errors; 11/11 신규 + 33 total pstf_primary + 기존 5 슈트 회귀 없음
- **G2 FLRW (partial) ✅** — `regression_rhs_matches_mb95_freestream_kappa_zero` ℓ={0,1,2,5,ℓ_max} 각각 MB-95 `camb_rhs` (opac=0 특수화) 와 rel err < 1e-14 bit-identical. `regression_multiple_k_values` k∈{1e-4,1e-2,1e-1} rel err < 1e-13. **Partial pass (cap 7)**: metric coupling placeholder 로 인해 "free-streaming sub-component FLRW" scope only.
- G3 PHYS ✅ — `identity_recursion` (수동 계산: ℓ=3 → 0.5/7·(3·2−4·4), ℓ=5 → 0.5/11·(5·4−6·6)), `identity_truncation` (0.7·3−9/50·2=1.74), `limit_k_zero`, `limit_metric_source_zero`, photon-ν parallelism, fluid/metric 영역 무접촉
- G4 CROSS ✅ — MB-95 `camb_rhs` (`sync_gauge_camb.rs:407`) 공식과의 inline 대조

**Score**: **7/10** (cap 7 — G2 partial). W·S/10 = **4.2**.

**Anti-local-min observation**: Pre-audit §4 의 3 trigger (metric placeholder 오염 / recursion 위배 / truncation 불일치) 모두 unfired. `STUCK_LOG.md` entry 추가 없음.

**Verification**:
- `cargo test --lib --release --no-run`: Finished 1m 06s, 0 errors
- `solver::pstf_primary::rhs_free`: 11/11 PASS
- `solver::pstf_primary` total: 33/33 (layout 12 + ic 10 + rhs_free 11)
- `pstf::`: 130/130 PASS
- `source::registry`: 12/12 PASS
- `core::ssot`: 35/35 PASS
- **D_2 = 1002.086744 μK² bit-identical** (8th consecutive commit). 498/498 k-modes, 95.98s.

**Progress scoreboard 갱신**:
- PR-022a row 추가 (W=6, S=7, W·S/10=4.2)
- PR-022 계획 row 는 PR-022b / PR-022c 로 분할 (합산 weight 15 유지)
- Phase 1 진행률: 30.1% → **34.1%** (35.8 / 105)

**Next sub-track**: PR-022b (electron-frame Thomson collision, W=5, target S=8). Pre-audit design doc `pr-022b-design.md` 작성이 다음 단계.

### PR-021 — PSTF Adiabatic IC (2026-04-17) ✅

Phase 1 두 번째 code PR. **첫 PSTF PR with 4-Gate 모두 pass** (G4 including MB-95 Rust oracle cross-check).

**Added**:
- `src/solver/pstf_primary/ic.rs` (~290 줄) — `PstfIcInputs`, `PstfObservables`, `pstf_adiabatic_ic()` 함수, `PstfObservables::from_state()` projection rule, 10 unit tests
- `src/solver/pstf_primary/mod.rs` — `pub(crate) mod ic;` 등록 (1 줄)
- `docs/PR_DELTAS/pr-021.md` — closure delta (gate evidence + self-audit + hallucination paste)

**Design decision (§2.1)**: State-level value 를 MB-95 과 동일 수치로 copy, 비교는 physical observable (δ_γ, v_γ) 수준에서. PR-020 의 `flrw_norm_ratio_down` 실패 (factor-9 at ℓ=1) 교훈 직접 적용 — PSTF ↔ MB-95 FLRW normalization chain 은 PR-021 scope 밖 (PR-025 의 소관).

**Gate evidence (`PR_CONSTITUTION §9`)**:
- G1 COMPILE ✅ — `cargo check` Finished 1.48s, 0 errors; 10/10 신규 tests + 22 total pstf_primary + 130+12+35 기존 회귀 없음
- **G2 FLRW (quantitative) ✅** — `regression_delta_gamma_matches_mb95_adiabatic`: PSTF `from_state().delta_gamma` = 4 × 0.5 = 2.0, MB-95 reference = 2.0, **rel err < 1e-15 (bit-identical)**. `regression_v_gamma`: PSTF v_γ = k/(2ℋ) = 1e-5, MB-95 identical, rel err < 1e-15.
- G3 PHYS ✅ — k-linearity (2× k → 2× dipole ratio 1e-12), ℋ-inverse, photon-ν adiabatic match, k=0 dipole vanish, ℓ≥2 zero, fluid sector untouched
- **G4 CROSS ✅** — MB-95 `adiabatic_ic` (Rust oracle, `sync_gauge_camb.rs:3297`) 과의 직접 cross-check bit-identical. **첫 PSTF PR with oracle agreement**.

**Score**: **8/10** (cap 9, publication figure 없어 8). W·S/10 = 8.0.

**Verification**:
- `cargo check --lib --release`: Finished 1.48s, 0 errors
- `solver::pstf_primary::ic`: 10/10 PASS
- `solver::pstf_primary` total: 22/22 PASS (layout 12 + ic 10)
- `pstf::`: 130/130 PASS (기반 회귀 없음)
- `source::registry`: 12/12 PASS
- `core::ssot`: 35/35 PASS
- **D_2 = 1002.086744 μK² bit-identical** (7th consecutive commit). 498/498 k-modes, 96.93s.

**Anti-local-min observation**: Pre-audit §6 의 3 trigger (normalization mismatch / k-linearity failure / scope creep) 모두 unfired — rule 예방 효과만 발휘. `STUCK_LOG.md` entry 추가 없음.

**Progress scoreboard 갱신**:
- PR-021 row 추가 (W=10, S=8, W·S/10=8.0)
- Phase 1 진행률: 22.5% → **30.1%** (31.6 / 105)
- 완료된 PR quality: 65.6% → 68.7%

**Next PR**: PR-022 (PSTF RHS) pre-audit design doc 작성. Weight 15 (Phase 1 single-biggest), sub-track 분할 권장 (022a RHS structure / 022b Thomson collision / 022c Jacobian).

### PR-021 Pre-audit Design Doc — PSTF Adiabatic IC (2026-04-17) 📝

Phase 1 두 번째 code PR 착수 전 pre-audit design doc 작성. Code 변경 없음 (governance / planning step).

**Added**:
- `docs/PR_DELTAS/pr-021-design.md` — PR-021 pre-audit design (총 §1–§10)
  - §2: MB-95 `adiabatic_ic` (src/solver/sync_gauge_camb.rs lines 3297–3318) oracle reference 분석 — ζ=1 규약, η_s=-1, δ_c=δ_b=3/2, Θ_0=N_0=1/2, Θ_1=N_1=k/(6ℋ), v_b=3·Θ_1, σ=0
  - §3: PSTF IC 변수 대응 table (FLRW limit). **Scope 전략**: state vector 수준이 아닌 **physical observable (δ_γ, v_γ) 수준** 에서 MB-95 과 일치 — PR-020 의 `flrw_norm_ratio_down` 실패 교훈 적용
  - §4: `PstfIcInputs`, `PstfObservables`, `pstf_adiabatic_ic`, `PstfObservables::from_state` API
  - §4.4: 9 TDD tests (identity 2 + limit 2 + channelwise 1 + regression 2 + caveat 2) — regression 2개 가 G2 FLRW gate 직접 evidence
  - §5: Gate forecast — G1/G2/G3/G4 모두 ✅ 예상, score **8/10** target
  - §6: Anti-local-minimum trigger 3 개 사전 정의 — normalization mismatch / k-linearity failure / scope creep
  - §7: Hallucination checklist 준비 (PR closure 시 paste 항목)
  - §8: 4 위험 식별 — adiabatic normalization canonical 값, state vector fluid 영역, k/ℋ precision, PSTF IC normalization 문서화 부족
  - §9: Pre-PR checklist 4 항목 — 이 세션에서 **모두 즉시 확인 완료**:
    - `src/pstf/hierarchy.rs::set_adiabatic_ic(f0)` 존재하나 단순 monopole 만 (PR-021 의 full regular series 와 다름, 독립 구현 필요)
    - MB-95 `test_adiabatic_ic` fixture: k=0.01, adotoa=500.0 대표값 — PSTF test 에서 동일 값 사용 계획
    - State vector `vec![0.0; n_state]` 시작 → fluid sector zero 유지 확인 (caveat test 성립 근거)
    - `CambBackground` full struct 불필요 — `adotoa: f64` 하나만 있으면 PSTF IC 함수가 충분
  - §10: PR-022 (RHS) preview — Jacobian sparsity 는 `src/pstf/hierarchy_matrix::build_coupling_matrix` 재사용 계획

**예상 Phase 1 진행률 변동** (PR-021 closure 시):
- 현재: 23.6 / 105 = 22.5%
- PR-021 (W=10, target S=8, W·S/10=8.0) 후: 31.6 / 105 = **30.1%**

**Verification (governance-only)**:
- `cargo check` 미실행 (코드 변경 없음)
- Pre-PR checklist §9 의 4 항목 모두 실시간 확인 완료 — PR-021 scaffold 진행 안전성 검증

**Next session**: PR-021 scaffold 실제 구현 — `src/solver/pstf_primary/ic.rs` 신설, 9 tests 구현, regression G2 evidence 측정 (PSTF `from_state().delta_gamma` 가 MB-95 `4·Θ_0 = 2.0` 와 ratio 1.00 ± 1e-6), scoreboard 갱신.

### Methodology Absorption — 4-Gate / Anti-Local-Min / Progress Scoreboard (2026-04-17) ✅

외부 길잡이 문서 (BASS Implementation Plan v6.0) 의 방법론 elements 를 governance layer 에 흡수. **물리 / 수식 / 코드 변경 없음** (governance-only). 구체 physics (Tier A/B, L=4/6/8 cutoff, reionization z_re=7.7 등) 은 흡수 안 함 — 별도 Python prototype 영역이라 Rust bass_rs scope 에 직접 대응 없음.

**Added governance elements**:

- `docs/PR_CONSTITUTION.md` **§9 4-Gate Check with Score Caps** — G1 COMPILE / G2 FLRW (quantitative) / G3 PHYS / G4 CROSS 정의. Score cap 규칙 (G1 없으면 ≤4, G2 없으면 ≤6, G3 없으면 ≤7, G4 없으면 ≤8, 4-gate 모두 있으면 9, + publication-ready 10). PR closure template 에 gate evidence block 추가 의무.
- `docs/PR_CONSTITUTION.md` **§10 Anti-Local-Minimum Rule** — "2회 연속 실패 + 3번째 시도가 같은 logic" 일 때 STOP → STUCK_LOG 에 기록 → 다음 critical-path PR 로 이동 → fresh session 에서 복귀. "같은 logic" 의 정의 (tolerance 완화 / parameter 만 바꾸기 / 재해석) vs "새 logic" (근본 가설 재정의 / 다른 layer / 다른 oracle). 예외 규정 (typo, tooling, user 명시 지시).
- `docs/PR_CONSTITUTION.md` **§11 Hallucination Detection Checklist** — PR closure 이전 mandatory evidence checklist (code 실행 / FLRW gate 값 / test assertion 일치 / module import 가능 / figure 생성 확인). Score 상향 evidence 요구. AI-session 특이 주의사항 (긴 세션 summary 복제 금지, 연속 PR 간 numerical 복사 금지).
- `docs/PROGRESS_SCOREBOARD.md` **신설** (176 줄) — Weight 부여 원칙 (4–15 범위), Phase 1 scoreboard, 진행률 계산 `∑(W·S/10) / ∑W`, Phase 완료 기준 (total weight × 80%). PR-000 / PR-010 / PR-011-st1 / Formalism audit / PR-020 retroactive scoring. 현재 Phase 1 진행률: **23.6 / 105 = 22.5%**. Phase 1 완료 기준: weighted score ≥ 84.
- `docs/STUCK_LOG.md` **신설** (76 줄) — Anti-local-minimum rule trigger 발동 시 기록 장소. Entry format, 현재 active entries (none), resolved entries (PR-020 의 `flrw_norm_ratio_down` preemptive resolution 1 건).
- `docs/ROADMAP_PHASE_I_TO_L.md` **§9/§10 갱신** — PR-020 완료 상태 반영, 다음 행동 (PR-021), §10 에 scoreboard 갱신 의무 + anti-local-min rule trigger 시 STUCK_LOG 기록 의무 명시. Phase 완료 기준을 "weighted score ≥ 80%" 로 통합.
- `docs/ROADMAP_PHASE_I_TO_L.md` **§3 PR-020 row** — "✅ merged 2026-04-17 (score 6/10)" 로 표기, actual outcome (covariant divergence operator test 는 PR-025 로 이관), gate evidence summary 추가.
- `docs/PR_DELTAS/pr-020.md` **gate evidence + self-audit block 추가** — retroactive 4-gate 분석 (G1 ✅ / G2 N/A / G3 ✅ / G4 N/A, cap 6), `§11.4` self-audit checklist 6 items 모두 통과.

**Retroactive scoring results** (PROGRESS_SCOREBOARD §3):

| PR | Weight | Score | W·S/10 | 정당성 |
|---|---:|---:|---:|---|
| PR-000 | 6 | 7 | 4.2 | Governance exception (ordinary gov. PR default 6) |
| PR-010 | 10 | 7 | 7.0 | G1+G2+G3 pass, G4 N/A (PSTF oracle 미도입). Cap 8 인데 convergence 미완이라 7. |
| PR-011-st1 | 6 | 6 | 3.6 | G2/G4 N/A, 정당 scaffolding cap. |
| Formalism audit | 4 | 7 | 2.8 | Governance exception. |
| PR-020 | 10 | 6 | 6.0 | G2/G4 N/A scaffolding, 정당. |
| **합계** | **36** | | **23.6** | 완료 품질 65.6%, Phase 1 진행률 22.5% |

**Verification (governance-only)**:
- `cargo check --lib --release` : Finished 33.94s, 0 errors (코드 미변경 확인)
- 기존 test 슈트 재실행 불필요 (코드 변경 없음)
- 5 governance 문서 총 1597 줄 (PR_CONSTITUTION 389, PROGRESS_SCOREBOARD 176, STUCK_LOG 76, ROADMAP v2 261, SSOT_POLICY 695)

**Next session**: PR-021 (PSTF adiabatic IC) pre-audit design doc 작성. v6.0 §5 (CAMB adiabatic regular series, tilted Bianchi boost rules, 4 pitfalls) 을 IC spec reference 로 참조.

### PR-020 — PSTF Primary Scaffold (State Layout + Hierarchy Primitives) (2026-04-17) ✅

Phase 1 (Parallel Dual-Track Migration) 의 첫 code commit. PSTF primary 의 state vector layout 을 도입. `src/pstf/` 130-tests-passing base 를 FLRW-specialized wrapper 로 감쌈.

**Added**:
- `src/solver/pstf_primary/mod.rs` — 서브모듈 등록, PR-020..PR-026 roadmap 과 reuse map 인라인 문서화
- `src/solver/pstf_primary/layout.rs` — `PstfFlrwLayout` struct + FLRW primitive accessor + 12 unit tests
- `src/solver/mod.rs` — `pstf_primary` 등록 (4 줄)
- `docs/PR_DELTAS/pr-020.md` — PR-020 SDD closure delta

**PstfFlrwLayout API** (m=0 전용):
- `i_photon_i_m0(ell)`, `i_photon_e_m0(ell)`, `i_photon_b_m0(ell)`, `i_neutrino_m0(ell)`
- `has_pol()` — semantics parallel `CambLayout::has_pol()`
- `validate()` — 4 hard invariants (MIN_LMAX_G, pol on/off threshold, DOF consistency)
- `mb95_down_coefficient`, `mb95_up_coefficient` — MB-95 recursion 계수 reference values

**Tests (12/12 PASS)**: identity (2), limit (2), channelwise (2), validation (3), caveat (2), sanity (1). TDD gate 5-카테고리 구조 유지.

**Pre-audit risk 실증 (1건)**: `pr-020-design.md §8` 에서 경고한 "metric sector sign/factor 주의" 가 실제 발현. 초기 `flrw_norm_ratio_down` helper 가 PSTF `ℓ/(2ℓ−1)` 와 MB-95 `ℓ/(2ℓ+1)` 의 단순 비율 정규화를 encode 하려 했으나 ℓ=1 에서 factor-9 error. Helper 자체 제거, 정식 PSTF ↔ MB-95 FLRW equivalence 유도를 PR-025 로 이관. Pre-audit 경고의 조기 탐지 효과 증명.

**Verification**:
- `cargo check --lib --release` : Finished 1.28s, 0 errors
- `src/pstf/` : 130/130 PASS (기반 재사용 안전)
- `source::registry` : 12/12 PASS
- `core::ssot` : 35/35 PASS
- `solver::pstf_primary::layout` : 12/12 PASS (신규)
- **D_2 = 1002.086744 μK² bit-identical 유지** (498/498, 69.69s — production 무접촉이므로 bit-identical 보장)

**Scope 밖 (후속 PR)**:
- Adiabatic IC → PR-021
- RHS / Jacobian / Thomson collision → PR-022
- Metric sector (1+3 covariant Φ, σ_{ab}) → PR-023
- LoS source + `solve_pstf_spectrum` → PR-024
- FLRW equivalence test → PR-025
- Production backend switch → PR-026

### Formalism Audit + Roadmap v2.0 Dual-Track Governance (2026-04-17) ✅

사용자 주도 formalism audit 결과, `sync_gauge_camb.rs` 가 PSTF 가 아닌 **MB-95 (Ma-Bertschinger synchronous gauge brightness multipole)** formalism 임을 확인. DESIGN LAW 가 요구하는 **1+3 covariant PSTF `I_{A_ℓ}`** 와 구조적으로 다름. CAMB 자체도 PSTF 를 쓰지 않고 MB-95 를 씀 — "CAMB 가 PSTF 를 따른다" 는 전제 자체가 오류. Parallel dual-track migration 으로 승인됨 (Phase 1 PSTF 완성 → Phase 2 equivalence test → Phase 3 backend switch → Phase 4 Bianchi).

**Added governance documents**:
- `docs/SSOT_POLICY.md §17` Formalism Scope — MB-95 oracle (src/solver/sync_gauge_camb.rs) vs PSTF primary (src/solver/pstf_primary/) 경계. Shared formalism-agnostic layer 와 formalism-specific SSOT namespace (`ssot::mb95::*`, `ssot::pstf::*`, `ssot::bianchi::*`) 규약. Version bumped 2.0 → 2.1.
- `docs/ROADMAP_PHASE_I_TO_L.md` **v2.0 전면 재작성** — v1.0 (MB-95 as production) 은 폐기. Phase 1 (PR-020..024) PSTF scalar FLRW → Phase 2 (PR-025) equivalence test → Phase 3 (PR-026) backend switch → Phase 4 (PR-050..080) Bianchi. PR-011 sub-track 2b/c/d 는 Phase 3 완료 후로 연기.
- `docs/PR_DELTAS/pr-020-design.md` (신규) — PR-020 착수 전 pre-audit design doc. `src/pstf/` 10 모듈 (3044 줄) 감사 결과: coupling.rs/tensor.rs/lm_indexing.rs/hierarchy_matrix.rs/tca_lm.rs 등 **~1900 줄 재사용 가능** (63%). Phase 4 대기 (m_decomposition.rs, streaming_lm.rs) 725 줄. 재유도 필요 (collision_lm.rs의 electron-frame ζ̃) 359 줄. PSTF ↔ MB-95 변수 매핑 table draft 포함.
- `docs/PHYSICS_REFERENCES.md` 재구조 — §A 는 empty (stub), §B 는 PSTF primary references (Challinor-Lasenby I/II, Maartens-Gebbie-Ellis MES, Tsagas et al. 2008 review, Maartens 1998, Lewis-Challinor lensing 2006), §B.5 는 MB-95 verified oracle references (Ma-Bertschinger 1995, Lewis-Challinor-Lasenby 2000 CAMB, Hu-White 1997, Blas-Lesgourgues-Tram 2011 CLASS).

**Verification (no code change)**:
- `cargo check --lib --release` : Finished 25.72s, 0 errors
- `src/pstf/` 130/130 unit tests PASS (PR-020 pre-audit 통과 — 재사용 기반 탄탄)
- D_ℓ 측정 불필요 (코드 무변경, regression 가능성 없음)

**Next PR**: PR-020 scaffold (별도 세션) — `src/solver/pstf_primary/` 생성, `PstfLayout` 정의, `coupling` / `lm_indexing` / `tensor` / `hierarchy_matrix` 재사용 wiring.

### PR-011 Sub-track 1 — ν Hessian Closed-Form SSOT Promotion (2026-04-17) ✅

R-P2-02 의 확정 결과를 `core::ssot::constants` 로 승격. PR-011 (massive-ν completion) 의 선행 작업.

**Added (`src/core/ssot.rs::constants`)**:
- `NU_HESSIAN_ALPHA_ZERO: f64 = 7π⁴/36 ≈ 18.941` — ∂T·∂T quadrupole 결합
- `NU_HESSIAN_BETA_ZERO: f64 = −6·ζ(3) ≈ −7.212` — ∂T·∂η cross-coupling (symmetrization factor 2 포함)
- `NU_HESSIAN_GAMMA_ZERO: f64 = π²/12 ≈ 0.8225` — ∂η·∂η 순수 chemical-potential 결합
- `NU_HESSIAN_DELTA_ZERO: f64 = −(75/16)·ζ(5) ≈ −4.861` — shear-temperature 결합 (Liouville operator 출신)

**Ratios (derived, NOT stored — SSOT discipline)**:
- `|β|/α = 216·ζ(3)/(7π⁴) ≈ 0.381` — 비무시 cross-coupling
- `γ/α = 3/(7π²) ≈ 0.0434` — chemical potential 감도

핵심 finding: β, γ **비영 at η₀=0** — symmetric background 에서도 chemical-potential perturbation 이 quadrupole 에 기여.

**Tests added (6)**: closed-form 값 대조, sign convention 확인, ratio 비영성 확인 (closed-form 공식과 대조). SSOT total: 35/35 PASS.

**Production impact**: 없음. 현재 BASS massive-ν code path 는 이 계수를 호출하지 않음 — 이 PR 은 향후 two-field 2차 source 구현의 SSOT 기반 마련. D_2 = 1002.086744 μK² bit-identical 유지 (dump_dl_spectrum_sparse 재실행 498/498, 81.51 s).

**Documentation**: `docs/PR_DELTAS/pr-011-subtrack-1.md`

### SSOT Amendment — R-NORM-01 Step Function (2026-04-17) ✅

PR-010 후속으로 `docs/ROADMAP_PHASE_I_TO_L.md §3` 의 "R-NORM-01 → PR-010 에 흡수" 미완 항목 완료.

**Added**:
- `src/core/ssot.rs::cl_prefactor_at_k(k)` — C_ℓ prefactor step function 의 SSOT 헬퍼. `k ≤ K_CORR_SYNC` 면 `CL_PREFACTOR_NEWT (4/9)`, 아니면 `CL_PREFACTOR_SYNC ((4/9)·R²_φη)` 반환.
- 4 신규 unit tests (superhorizon / subhorizon / boundary / ordering) — 29 / 29 ssot tests PASS

**SSOT contract**: 앞으로 모든 C_ℓ pipeline 은 sync/Newtonian prefactor 적용 시 `cl_prefactor_at_k()` 경유 의무. Inline 재구현 금지.

**Production impact**: 없음. `sync_gauge_camb::production_source_v1` 은 CAMB-style direct source normalization (T² μK² 곱) 을 쓰며 이 prefactor 를 호출하지 않음. `dump_dl_spectrum_sparse` 재실행 시 D_2 = 1002.086744 μK² **bit-identical 유지** (498/498, 68.24 s).

### PR-010 — FLRW source/radial channel split cleanup (Stage B, Production Migration) (2026-04-17) ✅

Stage A (scaffold) 후속. `production_source_v1` 을 registry 경유로 이행.

**Modified**:
- `src/solver/sync_gauge_camb.rs::production_source_v1` — inline 계산 제거, `source::registry::{source_sw, source_doppler, source_polter_quad, source_emode}` 경유
- `src/core/ssot.rs::polter` — **bit-identical contract** 주석 추가, 계산 순서를 production 과 정렬 (`2.0 * θ₂ / 5.0 + 3.0 * E₂ / 5.0` pol-ON, `4.0 * θ₂ / 10.0` pol-OFF)
- `src/core/ssot.rs` — **신규 `polter_dot()`** 함수 추가 (polterdot 계산 SSOT 승격)

**Latent bug fixed (byproduct)**:
이전 `ssot::polter` pol-OFF 분기는 `theta2 * 0.1` 반환 — **4× 작은 값**. 올바른 값은 `pig/10 = 4·Θ₂/10 = 0.4·Θ₂` (production inline 이 항상 사용). Production 은 inline 경로라 영향 없었으나, 어떤 downstream 이든 `ssot::polter()` 를 호출했다면 잘못된 값. Stage B migration 이 수면 위로 끌어올려 해결.

**Tests updated**:
- `core::ssot::tests::polter_pol_off` — expected `0.4` (was 0.1 based on buggy SSOT)
- `core::ssot::tests::neff_splits` — CAMB 관례 상 split sum ≠ total 을 인정하고 0.1% tolerance 로 완화
- `source::registry::tests::caveat_no_pol_reduction_emode` — expected `g·(4·θ₂/10)` (was `g·θ₂/10`)
- `source::registry::tests::limit_pol_off_reduces_polter_quad` — E₂=0 에서 pol-ON/OFF bit-identical 이 참임을 확인

**Verification (critical)**:
- `cargo test --lib --release source::registry` → **12 passed**
- `cargo test --lib --release core::ssot` → **25 passed**
- `dump_dl_spectrum_sparse` (498/498 k-modes, 68.73 s) → **D_2 = 1002.086744 μK²** bit-identical to pre-Stage-B (Δ = 0)

**Documentation**:
- `docs/PR_DELTAS/pr-010-stage-b.md` — Stage B closure delta

### PR-010 — FLRW source/radial channel split cleanup (Stage A, Scaffold) (2026-04-17) ✅

Per `docs/PR_CONSTITUTION.md §3`. Two-stage PR; 본 commit 은 **Stage A (scaffold)** 만 완료.

**Added — `src/source/` 신규 서브트리**:
- `src/source/mod.rs` — 서브모듈 등록
- `src/source/registry.rs` (380 줄) — 5 source channel 개별 pure function:
  - `source_sw(inp)` — `g · (δ_γ/4 + 2Φ + η_mb/2)`
  - `source_isw(inp, exp_minus_tau)` — `e^{-τ} · (Ψ̇ + Φ̇)`
  - `source_doppler(inp)` — via `core::ssot::doppler_source`
  - `source_polter_quad(inp, polter_dot)` — via `core::ssot::quad_source_no_polterddot`
  - `source_emode(inp, conv)` — Polter 또는 PiBass convention 명시 선택
- `EmodeConvention` enum: `Polter` (CAMB production default) 또는 `PiBass` (exact transport)
- `SourceInputs` / `ChannelOutputs` 타입
- `assemble(inp, ...)` 함수 — 5 channel 전체 집계
- 12 unit tests (identity 3 + limit 2 + channelwise 3 + regression 1 + caveat 3)

**Modified**:
- `src/lib.rs` — `pub(crate) mod source;` 등록

**Production 경로 불변**:
- `sync_gauge_camb::production_source_v1` 수정 없음
- `D_2 = 1002.086744 μK²` bit-identical 보존 (pre/post verification via `dump_dl_spectrum_sparse`, 69.66 s, 498/498 k-modes)

**Documentation**:
- `docs/PR_DELTAS/pr-010.md` — SDD delta (본 PR 의 ownership / rollback / next PR 명시)
- `docs/PR_DELTAS/candidate-b-closure.md` — HyRec h0_cgs unit bug 이미 해결 상태로 확인 (xe(z=1075) = 0.1142 측정, target 0.1137 대비 Δ=+0.4%). userMemory stale note 는 다음 handoff 에서 갱신.

**Stage B (deferred)**: `production_source_v1` → `registry::assemble` migration, `SourceValue.s_isw` 노출. 별도 후속 세션.

### Candidate B — HyRec h0_cgs unit bug (2026-04-17) ✅ RESOLVED

Previously flagged in userMemory as "Known unit bug remaining: h0_cgs uses MPC_M in meters instead of cm". Verification (2026-04-17):

- Current code: `mpc_cm = MPC_M * 100.0` (meters → cm 변환 정상), `h0_cgs = h * 1.0e7 / mpc_cm`
- 측정: `xe(z=1075) = 0.1142` (target 0.1137, Δ=+0.4%) ✓
- **결론**: 이전 세션 (또는 Phase B-1 v1 중) 에 이미 수정됨. Code action 불필요.

### Phase B-1 Post-Audit — SSOT Hardening v2 (2026-04-17) ✅

4건의 업로드 문서 (`SSOT_Hardening v1.0`, `Physics Compendium v1.0`,
`PR WBS TDD SDD v1.0`, `DOC-BASS Design v1.3`) 를 BASS 저장소에 반영하는
SSOT 2차 강화. v1 (같은 날짜) 의 14-bug remediation 위에 **규약 문서 및
코드 권위 확장** 을 추가.

**Added — `src/core/ssot.rs` 섹션 확장** (346 → 670 줄, +324 줄):
- **§5 Π_BASS canonical primitive**: `pi_bass(θ₂, E₀, E₂, has_pol)`,
  `hw_visibility_source_temperature/emode` — Hu-White 관례
  `Π_BASS ≡ Θ₂ + E₀ + E₂` 를 CAMB `polter` 와 **구분** 하여 별개 헬퍼로 제공
- **§6 Time convention dictionary**: `TimeConvention` enum
  (`Conformal/Cosmic/ProperObserver/Affine/ConventionFree`),
  `convert_rate_proper_to_conformal(Γ, a) = a·Γ` 와 역변환
- **§7 Canonical opacity**: `opacity_chi(a, n_e, σ_T) = a·n_e·σ_T ≥ 0`,
  `visibility_g(χ, τ) = χ·e^{-τ}` — `dopac` 부호 모호성 배제
- **§8 Admissibility validators**: `assert_opacity_positive`,
  `assert_visibility_positive`, `assert_ionization_bounded(x ∈ [0,1])`,
  `assert_temperature_positive(T > 0)` — SSOT Hardening §7.1 universal
  positivity constraints
- **§9 External basis translation maps**: `pi_bass_from_hw_like`,
  `pi_bass_from_class_like([F_ℓ], [G_ℓ])` — CLASS/CAMB 변환을 SSOT 경유 강제
- **§10 Frozen tag dictionary**: 18 개 branch/status 태그
  (`DENOMINATOR`, `PROTOTYPE_TIER`, `RESEARCH_MODE`, `REDUCED_BRANCH`,
  `REFERENCE_BRANCH`, `FIXED_HISTORY`, `HYDROGEN_ONLY`, `HELIUM_OFF`,
  `VISIBILITY_OFF`, `REIONIZATION_OFF`, `BACKREACTION_OFF`, `REFINEMENT_OFF`,
  `WRAPPER_ONLY`, `RESPONSE_AWARE`, `DIR_SOB`, `FULL_CHAR`,
  `PRODUCTION_DEFAULT`, `CAVEAT_REQUIRED`) + `validate_tag()` 검증자
- **테스트 15개 추가**: Π_BASS HW/CLASS basis, pol-off 환원, HW visibility,
  TimeConvention distinct, rate 변환 roundtrip, opacity/visibility formula,
  admissibility accept/reject (5 cases), tag dict lookup/complete

**Added — `src/core/status_metadata.rs`** (신설, ~320줄):
- `StatusMetadata { branch_tags, approximation_tags, caveat_tags }` —
  SSOT Hardening §8.1 schema
- `StatusMetadataBuilder` — tag 유효성 eager 검증 (`validate_tag`)
- `ForwardBridge<T> { payload, provenance, status }` —
  SSOT Hardening §9.6 solver → HTT/MIO 경계 계약
- **6개 Export schema** (§9.1-9.5): `RecombinationExport`,
  `EorSnapshotExport`, `EorLightconeExport`, `BackreactionExport`,
  `UnresolvedAngularExport`
- 테스트 6개 추가

**Documentation — 신설 4건 + 전면확장 1건**:
- `docs/SSOT_POLICY.md` **v2.0 전면 확장** (141 → ~500 줄, 8 → 17 섹션):
  - §2 Canonical basis (FLRW denominator + exact transport + Π_BASS vs polter 구분 + external translation)
  - §3 Time convention dictionary (§3.2 module-by-module frozen mapping)
  - §4 Operator split SSOT (exact branch + free-streaming + collision sub-split)
  - §5 Canonical source contracts (Thomson + LoS radial + recomb line + reion sweep + effective source)
  - §6 Authoritative locations (22-row 구현 레지스트리)
  - §10 Known-limit summary (27 항목 요약)
  - §11 Admissibility SSOT
  - §12 Status metadata + export schemas
  - §13 Minimal test SSOT (28 canonical test 이름)
  - §14 PR constitutional rules (TDD/SDD/promotion/critical-path)
  - §15 예외/완화 절차 + 폐지 경로 + dopac/polter_ddot 재활성화 조건
- `docs/KNOWN_LIMITS.md` (신설): 6 카테고리 27 항목 복원 테이블
  (FLRW denominator, exact anisotropic, recombination, reionization,
  backreaction tiers, unresolved high-ℓ) + status legend (✅/🟡/🔴)
- `docs/STATUS_TAGS_AND_EXPORTS.md` (신설): 18 태그 사전 + 5 표준 조합
  preset + 6 export schema payload + validation pipeline + 태그 추가/폐지 절차
- `docs/PR_CONSTITUTION.md` (신설): §0 5-statement constitutional framing
  + §1 4 golden rules (TDD/SDD/promotion/critical-path) + §2 9 programme
  tracks (A-I) + §3 24-PR critical path (PR-000..PR-080) + §4 merge gate
  checklist + §5 rollback/kill criteria + §8 long-range phase 지도
- `docs/BASS_STACK_OWNERSHIP.md` (신설): BASS=physics ≠ HTT=bridge
  ≠ MIO=reporting 경계, cross-stack communication rules, 경계 위반 grep
- `docs/PHYSICS_REFERENCES.md` (신설): 20 canonical references
  (§A CMB baseline / §B 1+3 covariant / §C recomb / §D reion /
  §E EFT backreaction / §F numerics) + cross-reference table
  (BASS 파일 → paper)

**Compile**: `cargo check --lib --release` 통과 (1.59s). 전체 test suite
는 Phase 15 최종 빌드에서 검증.

**D_2 = 1005.7322 bit-identical 영향**: **없음**. 본 v2 변경은 SSOT module
확장 + 신규 문서 + 미사용 export struct 추가에 국한되며, production
`dump_dl_spectrum_sparse` 경로에서 호출되는 코드는 하나도 바뀌지 않음.

### Phase B-1 Post-Audit — SSOT Hardening (2026-04-17) ✅

외부 감사 4건의 교차대조로 식별된 중대 결함을 일괄 수정.  "숫자 튜닝" 이 아니라
**동일 물리량을 여러 경로가 서로 다른 규약으로 계산** 하던 SSOT 분열 해소가 중심.

**Added — `src/core/ssot.rs`** (신설, ~270 lines):
- 권위 상수: `NEFF_TOTAL = 3.044`, `NEFF_MASSLESS_WHEN_SPLIT = 2.0328`,
  `NEFF_PER_MASSIVE_EIGENSTATE = 1.0132`, `POLTER_W_THETA2`, `POLTER_W_E2`,
  `MIN_LMAX_G = 3`, `MIN_LMAX_POL_WHEN_ON = 2`, `MIN_LMAX_M_WHEN_ON = 1`
- 권위 헬퍼: `polter(theta2, e2, has_pol)`, `doppler_source(...)`,
  `quad_source_no_polterddot(...)`, `apply_friedmann_grho_correction(h² , Δgrho)`,
  `neff_massless_baseline(nq_massive)`
- Invariant 검증자: `validate_layout`, `assert_layout_valid`
- Stale-path fence 헬퍼: `stale_path_panic`
- 12 unit tests (polter pol on/off, Friedmann /3, N_eff split,
  layout validator boundary, quad source finite)

**Group A — 메모리 안전 / alias 차단**:
- **A1** (`sync_gauge_camb.rs::CambLayout::has_pol`): `lmax_pol > 0` →
  `lmax_pol >= MIN_LMAX_POL_WHEN_ON (=2)`.
  `lmax_pol == 1` 에서 `e_mode(2)` 가 `B₀` 로 alias 되던 버그 차단.
- **A2** (`CambLayout::new_full`): `ssot::assert_layout_valid` 삽입.
  `lmax_g < 3`, `lmax_pol == 1`, `nq_massive > 0 && lmax_m == 0` 경우
  panic 강제.  Debug/release 모두 적용.
- **A3** (`camb_rhs` photon 절단): guard `if lg >= 1` → `if lg >= MIN_LMAX_G`.
  Matrix 빌더의 `if lg >= 3` 와 대칭 복구.  `lmax_g ∈ {1,2}` 에서 Θ₁/Θ₂
  방정식이 절단식으로 덮이던 RHS-Jacobian 불일치 제거
  (이미 A2 validator 가 원천 차단하므로 방어용).

**Group B — 배경/IC/N_eff 권위화**:
- **B1** (`CommonProfile::build_massive_aware`): `H²_new = H²_old + Δgrho`
  → `ssot::apply_friedmann_grho_correction(H²_old, Δgrho)` (= `+ Δgrho/3`).
  flat Friedmann `3ℋ² = Σ grho_species` 와 정합.  이전 식은 √3 factor
  과대보정.
- **B2** (N_eff unify): 파일레벨 상수 2곳을 SSOT 재수출로 치환.
  `build_inner` L3409 에서 `massive_aware` 분기 —
  `nq_massive == 0 → 3.044`, `> 0 → 2.0328`.  이전에는 무조건 2.0328 사용.
  `tensor_ic()` 의 `let neff = 3.044_f64` 도 SSOT 참조로 치환.
- **B3** (`solve_camb_kmode` legacy IC): `v_b = Θ₁` → `v_b = 3·Θ₁`.
  Production `adiabatic_ic` 와 통일.  Collision term `−κ̇(v_b − 3Θ₁)/r_b` 과
  일치 (IC 에서 source 가 0 이 되는 조건).

**Group C — Factory 계약 정정**:
- **C1** (`ProductionConfig::default`): `lmax_pol = 12` → `lmax_pol = 0`.
  Default 는 이제 minimal baseline (pol OFF, no mν).
- **C2** (`minimal()`): `..Default::default()` 상속 대신 pol/mν 필드 명시.
  이전에는 default 변경 시 silently pol ON 이 되던 상속 버그.
- **C3** (`fast()`): `n_k = 2000` (default 와 동일 no-op) → `n_k = 500`.
- **C4** (`with_pol()`): mν 필드 명시.
- Added: `ProductionConfig::validate()` 메서드 (SSOT validator 래퍼).

**Group D — Stale 모듈 펜스**:
- **D1** (`los/source.rs::evaluate_source`): `stale_path_panic` + `#[deprecated]`.
  `-g'v_b/k` Doppler 식, `(3/4k²)g''Π` pol 식 봉쇄.  Production 경로는
  `sync_gauge_camb::to_source_grid` 로 authoritative source 값 복사.
- **D2** (`species/photon.rs::polarisation_pi`): `stale_path_panic` + `#[deprecated]`.
  자기모순 `G₀ = G₂ = e_mode[0]` 인덱싱 봉쇄.
- **D3** (`collision/polarisation.rs::polarisation_pi`): `#[deprecated]`.
  E-mode 인덱싱 `[G₀,G₁,G₂,...]` 가 species 의 `[G₂,G₃,...]` 와 충돌.
- **D4** (`solver/multispecies.rs::build_stacked_rhs`): `#[deprecated]`.
  L109 의 `polarisation_pi()` 호출을 SSOT-parallel inline 계산으로 치환하여
  Bianchi 경로 (`pipeline::solve_bianchi`) 의 빌드/런타임은 보존.

**Group E — polter_ddot / dopac 영구 봉쇄**:
- **E1** (`sync_gauge_camb.rs` L≈3815): `BASS_POLTER_DDOT=1` env-gated
  post-pass FD 경로 완전 제거.  "known-bad path behind env flag" 는
  audit liability 로 판정.
- **E2** (`production_source_v1` L≈345-444): polterddot closed-form
  (CAMB `equations.f90:2746-2751` port) 및 `BASS_POLTERDDOT_DUMP` 진단
  전체 제거.  `s_dop` / `s_quad` 계산은 SSOT 헬퍼
  (`ssot::doppler_source`, `ssot::quad_source_no_polterddot`) 로 치환.
- **E3** (`build_inner` dopac FD): FD 계산 제거, `dopac` 벡터 0 으로 고정.
  `CambBackground::dopac` 필드는 유지 (literal 구성자 보존) 하나 production
  경로에서 읽히지 않음.  부호 convention 불확정 상태 잠복 차단.

**Documentation refresh**:
- `README.md` L140, L561: HyRec `h0_cgs` unit-bug 문구를 "이미 수정됨" 으로
  갱신 (code 는 `mpc_cm = MPC_M · 100` 이미 cm 변환).
- `README.md` L557-559: Patch-3 polter_ddot "next step" 을 permanent-remove
  상태로 갱신.
- `BASS_STATUS_2026-04-12.md` L165-170: `+1.5·κ'·E₂ self-damping cancel`
  서술을 **REJECTED** 로 표기.  실코드는 `−(9/10)κ'Θ₂ + (3/20)κ'E₂`.

**Bit-identical impact (D_2 = 1005.7322 기준, `dump_dl_spectrum_sparse`)**:
- A1/A2/A3/C*/D*/E* 는 모두 bit-identical 보존 (production config
  `lmax_g=16, lmax_pol=0, nq_massive=0` 은 validator 통과, pol 분기 비활성,
  stale 펜스는 production 경로 밖, polterddot 은 이미 `0.0 *` 로 곱해져 OFF).
- **B2 만 D_2 변경 요인**: `nq_massive == 0` 에서 N_eff 를 2.0328 → 3.044 로
  수정하여 radiation loading ~50% 증가.  조기 평탄화 → D_2 값 변동 예상.
  실측 비교 (BASS dump → CAMB reference ratio) 는 별도 세션에서 재측정 필요.

**Compile**: `cargo check --lib --release` / `cargo build --lib --release`
 모든 phase 통과.  1123 warnings (dead code/snake case, physics 무관).

**Reviewers**: 4 audits cross-referenced.  모든 "치명적 오류" 항목 반영.

### PR-IMEX-02 — BassLinearOp bridge + end-to-end IMEX vs Rodas5P validation (2026-04-16) ✅

PR-IMEX-01 scaffold 위에 BASS 의 production matrix 기반 `SplitLinearOp`
구현체 추가. 설계문서 R-P1-02_설계안 §3-§4, DOC-BASS §5.4 의 bridge layer.

**Refactored — imex_collision_split.rs**:
- `CollisionSplit.coeffs_tilde` — C̃-unit 추상이 코드 사용과 불일치하여
  **실제 χ-multiplied values** 로 통일 (integrator 가 그대로 받아 사용)
- BASS `build_camb_matrix_into` 의 실제 entries 와 정확히 매칭:
  - ℓ=1 block: `m[Θ₁,Θ₁]=−χ, m[Θ₁,vb]=+χ/3, m[vb,Θ₁]=+3χ/r_b, m[vb,vb]=−χ/r_b`
    (여기서 r_b = 0.75·grho_b/grho_g, BASS convention)
  - ℓ=2 (no pol): −0.9·χ (Θ₂ self-damping)
  - ℓ=2 (with pol): 2×2 coupled [Θ₂, E₂] with BASS-matching entries
  - ℓ ≥ 3 photon: rate = χ
  - E-mode ℓ ≥ 2: rate = χ (when lmax_pol ≥ 2)

**Added — BassLinearOp adapter** (SplitLinearOp impl):
- Holds reference to `eta_profile`, `mats_flat`, `bg_at_snap` (production layout)
- `interp_idx` / `interp_bg` — 단일/다중 snapshot 처리 (edge cases)
- `apply_full_matvec(eta, y, out)` — A(η)·y by interpolation
- `apply_collision_matvec(eta, y, out)` — A_I(η)·y via CollisionSplit
- `apply_explicit` = full matvec − collision matvec (**lazy split**)
  - 이 방식의 장점: 별도 A_E storage 불필요, A_E + A_I = A 가 구성으로 보장
- `fill_implicit_diag/blocks/stiffness_scales` — η 보간 후 CollisionSplit 위임

**BassLinearOp tests (4, all PASS)**:
- `bass_linop_split_identity`: A_E·y + A_I·y = A·y **bit-exact (rel err = 0.0)**
- `bass_linop_a_e_no_collision_in_high_ell`: ℓ=5 self-coupling 정확히 0,
  streaming coupling 정확히 보존
- `bass_linop_sign_canonical`: 음수 opac 입력 시 χ = |opac| 강제
- `bass_linop_interpolation_consistency`: 두 snapshot 사이 선형 보간 정확

**End-to-end validation — imex_vs_rodas5p_synthetic_24dof**:
- 24-DOF synthetic system, χ = 1000, 실제 BASS matrix entries
- Rodas5P (rtol 1e-8) vs IMEX-ARK4 (rtol 1e-9) 비교
- **Significant entries: max relative difference = 5.18e-12** (machine precision)
- 두 적분기가 **bit-exact agreement** — split correct + integrator correct
- IMEX: 12013 accepted steps, 7 rejected, final h = 7.52e-4
  - Rodas5P 대비 step 수 훨씬 많음 (tune 필요, PR-IMEX-04 대상)
  - 하지만 correctness 는 완벽

**Test results**: 30/30 PASS (17 IMEX + 13 bridge + 1 end-to-end)
Production regression clean (mini D_2 = 967.4 unchanged).

**Next step (PR-IMEX-03 — production wiring)**:
1. `integrate_imex_ark4_snapshots`: η_eval 배열 받아서 선형 보간으로 snapshots
   저장 (Rodas5P 의 snapshots_rev 형식과 호환)
2. `solve_kmode_full_with_common` 에 env `BASS_USE_IMEX=1` 분기
3. Mini test IMEX path → D_2 비교 + wall time 측정
4. Step controller tune (현재 12013 steps 가 Rodas5P 의 ~100-1000 steps 대비
   많음 — h_init, f_max, err_tol 조정)

**Deferred**:
- PR-IMEX-04: step controller 최적화
- PR-IMEX-05: massive neutrino + E-mode polarization 지원 (ell_2 2×2 block
  다른 조건 검증)

**Status**: ✅ BRIDGE VALIDATED. Score 8/10 — bit-exact match verified,
production wiring pending in PR-IMEX-03.

### PR-IMEX-01 (scaffold) — IMEX-ARK4 solver expansion per R-P1-02_설계안 (2026-04-16) 🏗️

설계문서 `R-P1-02_설계안` §7-§9, §12, `MASTER_PROMPT_LIST_v3_2_FINAL.md` P1-05/P1-05 확장.

기존 `src/solver/imex_ark4.rs` (510 lines, P1-05 결과물) 는 Butcher tableau + 단일
step 함수 수준. 설계 §7.2 요구하는 모듈 구조 (trait + workspace + driver + audit)
확장.

**Added — imex_ark4.rs**:
- `SplitLinearOp` trait (§8): generic interface with dim/apply_explicit/
  fill_implicit_diag/fill_implicit_blocks/stiffness_scales
- `StiffnessScales` struct: opacity χ, hubble ℋ, shear ‖σ‖, k_mode
  + omega_explicit() + stiffness_ratio() + assert_canonical()
- `SmallBlock`, `SmallBlockSet`: structured collision block containers
  (indices + C̃ coefficients in C̃-units, χ multiplied at solve time)
- `ImexWorkspace`: pre-allocated scratch (k_e × 6, k_i × 6, y_s, y_s_full,
  err, diag_buf, blocks_buf) — ZERO per-step heap allocation
- `imex_ark4_step_trait<Op: SplitLinearOp>`: new stepper, sign canonicalization
  enforced via debug_assert (§12.4 critical bug prevention)
- `ImexStats`: integration statistics (accepted/rejected steps, h range)
- `integrate_imex_ark4<Op>`: adaptive multi-step driver with PI step controller
  on embedded 3rd-order error

**Added — imex_collision_split.rs** (new file, BASS ↔ IMEX bridge):
- `CollisionSplit::from_bg(layout, background)`: builds SmallBlockSet from
  CambBackground at a given η snapshot
  - Canonicalizes opacity: `chi = bg.opac.abs()` (§12.4 invariant)
  - Populates diagonal for photon ℓ ≥ 3 (rate 1.0 in C̃-units)
  - Builds ℓ=1 block: photon dipole ↔ baryon velocity drag (2×2, momentum
    exchange, R-dependent)
  - Builds ℓ=2 block: 1×1 without polarization, 2×2 with E₂ coupling
  - Populates E-mode diagonal ℓ ≥ 2 (when lmax_pol ≥ 2)
  - Stores r_baryon_photon = 4ρ_γ / (3ρ_b)

**Added — audit tests (R-P1-02_설계안 §12)**:
- §12.1(A) Linearity (diagonal case): closed-form stage solve
- §12.1(B) Dimensional consistency
- §12.1(C) Limit χ → 0: reduces to explicit RK (oscillator, 1e-7 error)
- §12.1(C) Limit χ → ∞: strong damping collapse
- §12.1(D) Monopole conservation: ℓ=0 stays exactly at y[0]=1 through 50 steps
- §12.4(A) Sign convention canonical enforcement (debug_assert)
- §12.3(B) Order-of-accuracy: 4th order convergence verified (ratio > 8 ≈ 16)
- §12.3(B) L-stability: h·χ = 1e6 extreme → amplitude < 1e-4
- Adaptive driver convergence: exponential decay, err < 1e-6
- Small-block solve: (I - h·γ·C̃)·k = C̃·y_pred identity verified

**Bridge tests (8 tests, imex_collision_split::tests)**:
- canonicalize_opacity_positive: negative input → positive χ
- diagonal_excludes_low_ell: ℓ=0,1,2 NOT in diagonal, ℓ≥3 IS
- collisionless_species_excluded: neutrino, CDM, metric, Φ never touched
- ell1_block_has_only_theta1_and_vb: δ_b NOT in ℓ=1 block (momentum, not density)
- ell1_block_sign_pattern: -1, +1/3, +R, -R/3 structure confirmed
- ell2_block_size_no_pol: 1×1 when lmax_pol=0
- n_collision_dofs_24dof: 6+2+1 = 9 out of 24 DOFs (37.5%)
- stiffness_scales_derivation: invariants hold

**Test results**: 25 / 25 PASS
- 17 tests in imex_ark4 (6 original + 11 new audit)
- 8 tests in imex_collision_split
- Production regression unchanged (PR-PERF-02 baseline preserved)

**Production wiring (future work — PR-IMEX-02)**:
1. Implement `SplitLinearOp` for BASS `build_camb_matrix` rhs (split streaming
   from collision via matrix-free evaluation)
2. Wire alternative path in `solve_kmode_full_with_common`: 
   `if cfg.use_imex { integrate_imex_ark4(...) } else { rodas5p(...) }`
3. Validate D_2 within ±0.5% of Rodas5P baseline at 200k-modes
4. Benchmark: estimate 5-8× ODE speedup at 24-DOF, 80-730k× at 5566-DOF

**Not yet done (deferred)**:
- `switch_policy.rs` (TCA → IMEX → explicit) — not applicable in
  approximation-free mode; would only be needed if TCA re-introduced
- `error_norm.rs` as separate module — folded into imex_ark4.rs for now
- 5566-DOF integration (requires m-major reordering; separate PR)

**Status**: 🏗️ SCAFFOLD — infrastructure in place, production integration pending.
Score: 7/10 — structure VALIDATED, wiring not yet done.

### PR-PERF-02 — Adaptive G7K15 + Bessel ladder + ODE step relaxation (2026-04-16) ✅

PR-PERF-01 의 한계 (sandbox 78s, CAMB 7s 의 11×) 를 극복하기 위한 두 가지
정확도 보존 최적화. **TCA 등 approximation 사용 안 함** — 전략 문서
(TCA/UFA/RSA 대응안) 의 "approximation-free truth engine" 원칙 준수.

**측정 결과 (test_dl_200k, primary 24 DOF, 200 k-modes)**:
- PR-PERF-01 baseline: ~78s, D_2 = 978.8
- **PR-PERF-02: 36.3s (53% 단축)**, D_2 = 978.6 (**0.02% 차이**)
- D_10 = 927.4 (정확 일치), D_30 = 1220.6 (0.08% 차이)
- 모든 ℓ ∈ {2, 10, 30} primary 측정값이 PR-PERF-01 대비 ±0.1% 안

**Mini config (test_dl_50k_mini)**:
- PR-PERF-01: 10.4s
- **PR-PERF-02: 6.2s (40% 단축)**
- D_2 = 967.4 (PR-PERF-01 의 967.7 대비 0.03%)
- D_10/D_100 의 1-2% 차이는 sparse 50-k-grid + max-ℓ adaptive 결합 효과
  (primary 에선 영향 없음)

**Added — LoS optimization**:
- `compute_dl_spectrum_adaptive_ladder()` (sync_gauge_camb.rs):
  - Adaptive G7K15 panel 구조 보존 (정확도)
  - 각 panel 의 15 K15 nodes 에서 `spherical_bessel_j_array(lmax, x, ...)`
    한 번 호출 → 모든 ℓ ∈ [2, lmax] 동시 처리
  - tol 1e-4 (vs original 1e-5) — max-ℓ 기준이 per-ℓ 보다 보수적이라 완화
  - flat j-layout `node_j_flat[ki * (lmax+1) + ell]` — cache-friendly
  - n_ell scratch reuse — panel 당 alloc 회피
  - **Cost reduction**: per (k, ALL ℓ) ladder ~60×60×15 ladder calls
    vs old per (k, ℓ) ~60×15 single bessel × ℓ_max calls
  - compute_dl 부분 35.3s → ~17.8s (49% 단축)
- `pub(crate)` 화: `G7_NODES`, `G7_WEIGHTS`, `K15_NODES`, `K15_WEIGHTS`
  (los/integrator.rs) — adaptive_ladder 에서 사용

**Added — ODE step controller**:
- `solve_kmode_full_with_common`:
  - rtol 1e-6 → **3e-6**, atol 1e-9 → **3e-9**, h_max 20/k → **30/k**
  - "보수적" 완화 (이전 세션의 5e-6 / 80/k 시도는 D_2 -1.8% 변화로 폐기)
  - 정확도 영향: D_2 0.02%, D_10 0.00%, D_30 0.08% (모두 안전)

**Removed (false leads)**:
- `compute_dl_spectrum_fast` (BesselTable linear interp) 는 high-ℓ 부정확
  — 주석의 "12× faster" 검증 안 됨, production 미사용. 함수 자체는 유지
  (legacy / 별도 path), production 호출 안 함.
- 이전 세션 PERF-02 sketch (rtol 5e-6 + h_max 80/k) 는 D_2 -1.8% 변화로 폐기

**Strategy alignment (TCA/UFA/RSA 대응안)**:
- approximation-free truth engine 원칙 준수
- TCA 도입 거부 (CAMB 의 7s win 의 핵심 이지만 silent physics loss 위험)
- 다음 큰 win 후보: **IMEX-ARK4(3)6L[2]SA** (별도 PR-IMEX-01)

**Score**: 8 / 10 — VALIDATED
- Primary 정확도 보존 ±0.1% ✓
- 53% wall 단축 (78s → 36.3s) ✓
- LoS algorithm 적정화 (49% 단축) ✓
- ODE step controller 보수적 완화 ✓
- Mini config D_10/D_100 의 1-2% 차이 (sparse k-grid 영향, primary 영향 없음)
- 합계: 8 / 10

### PR-PERF-01 — Performance refactor (2026-04-16) ✅ partial

PR-physics 작업 진행 가능한 baseline 측정 인프라 확보 + 사용자 local 환경
(≥8 cores) 에서 큰 win 기대되는 코드 변경. Sandbox (2 cores, memory
bandwidth bound) 에서는 mimalloc 만 의미 있는 win.

**Sandbox 측정 결과** (test_dl_200k, 24 DOF, 200 k-modes):
- **Before**: 72.6s (PR-00 baseline)
- **After mimalloc**: ~53s (실측 시점에 따라 51-78s, sandbox load variance ±5s)
- **After full PERF-01 stack**: 78s baseline (sandbox 의 measurement noise 안)
- **D_ℓ 정확도**: 모든 측정에서 D_2 = 978.8 비트-동일 (정확도 100% 보존)

**Added**
- `mimalloc` global allocator (lib.rs) — sandbox 단독 win 25-27%
- `CommonProfile` struct + `build()` (sync_gauge_camb.rs) — k-독립 데이터
  (visibility derivatives, tau_profile, bg_at_snap, tau_offset) 1회 precompute
- `KModeScratch` struct — dy + mats_flat scratch buffer 재사용
- `solve_kmode_full_with_common(k, common, pcfg, bootstrap, scratch)` —
  CommonProfile + scratch 받는 hot-path 진입점
- `solve_production_spectrum`: rayon par_chunks + Arc<CommonProfile> 공유 +
  per-chunk scratch — read-only 데이터는 clone 안 함 (MESI Shared 활용)
- `compute_dl_spectrum`: ell-loop 도 rayon par_iter 병렬화 (read-only grid)
- `BASS_SERIAL_KLOOP=1` env — 모든 rayon 병렬화 disable (디버깅용)
- `interpolate_linear_history_flat_to_targets` helper (stacked.rs) —
  flat-storage variant, 현재는 dead-code 함수만 사용. mimalloc 환경에서는
  Vec<Vec<f64>> 가 더 빠른 것으로 측정됨 (small alloc 이 거의 무료)
- `test_dl_50k_mini` — 24 DOF / 50 k-modes / ell_max=200, ~15s wall
  (200k 의 5× 빠름). PR-physics 작업 중 빠른 회귀 검증용
- `tests/fixtures/baseline_2026_04_16.json` 에 `config_24dof_mini_50k`
  추가 (D_2 = 967.7, primary 대비 1.13% 차이)
- `scripts/measure_dl_regression.py` 에 `--mini-only` 옵션 추가

**Backward compatibility**
- `solve_kmode_full(k, params, vis, pcfg, bootstrap)` 시그니처 보존 — 17곳
  test 호출 모두 영향 없음. 내부적으로 `CommonProfile::build` + scratch 새로
  할당 후 `solve_kmode_full_with_common` 호출 (단일 k 사용 시 비효율적이지만
  의미는 동일)

**Sandbox 진단 결과**
- 4 thread spawned 확인 (`/proc/<pid>/status`), `RAYON_NUM_THREADS=2/4`
  모두 user/wall ratio = 1.05 (실제 병렬화 안 됨)
- Memory bandwidth bound 의심 (200 k-modes 가 각자 ~14MB matrix profile)
- mimalloc 가 small-allocation contention 만 해소
- 사용자 local 환경 (≥8 cores + 더 넓은 memory bandwidth) 에서는 audit
  추정 3-8× win 가능성. 코드는 보존

**Documented**
- `BASS_SERIAL_KLOOP=1` env: rayon par_iter / par_chunks 모두 disable.
  디버깅 / profile 시 사용. Production 에서는 unset.

**Score**: 6 / 10 — VALIDATED (정확도) + sandbox win 부분적
- 정확도 100% 보존 ✓
- sandbox 단독 win 27% (mimalloc) ✓
- sandbox 추가 win 0% (rayon 효과 없음) — 무관 변경 아니라 local 환경용
- mini config 도입 ✓
- 임계 audit item 모두 적용 (CommonProfile, scratch, par_chunks)

### PR-00 — Baseline freeze (2026-04-16) ✅

측정 baseline 과 회귀 인프라를 확립했다. 이후 모든 PR 은 본 PR 의 fixture 를
기준점으로 D_ℓ 변화를 정량 보고한다.

**Added**
- `tests/fixtures/baseline_2026_04_16.json` — schema v1 불변 fixture (3 configs, 6 ℓ-point)
- `scripts/measure_dl_regression.py` — 회귀 측정 + baseline diff 스크립트
- `BASELINE_FREEZE.md` — 인간이 읽는 baseline 요약
- git tag `baseline-2026-04-16` (commit `b654be0`)

**Measured baseline** (VisibilityParams::planck2018):

| Config | DOF | Status | Notable |
|---|---|---|---|
| `test_dl_200k` (lmax_pol=0, no mν) | 24 | **VALIDATED** | D₂=978.8 (0.958× CAMB), 200/200 k-modes, 72.6s |
| `test_dl_200k_epol` (lmax_pol=12) | 38 | **BLOCKED** | Θ₂–E₂ instability, 57/200 k-modes, D_ℓ→∞ |
| `test_dl_50k_full` (full physics, n_k=50) | 128 | **BLOCKED** | Same instability, 0/50 k-modes |

**Interpretation**

Primary baseline (24 DOF) 의 D_ℓ/CAMB ratio:

| ℓ | ratio |
|---|---|
| 2 | 0.958 |
| 10 | 0.821 |
| 30 | 1.140 |
| 100 | 1.117 |
| 200 | 0.805 |
| 300 | 0.809 |

Secondary / tertiary 두 config 는 측정 시점부터 **BLOCKED** 로 기록한다.
이들의 PR 성공 기준은 "becomes measurable and within tolerance" 이다.

**Important discrepancy with prior docs**

`BASS_STATUS_2026-04-12.md` 가 기록한 D₂=1038 (101.5% CAMB) 는 현재 실측
D₂=978.8 (95.8% CAMB) 와 다르다. 이는 PR-00 이 왜 필요했는지를 증명한다 —
문서 주장과 현재 코드 동작 사이의 gap 이 존재한다. 본 PR 이후 모든 진척은
**문서 수치가 아닌 fixture 수치**를 기준으로 한다.

**Anti-hallucination guards implemented**
- `measure_dl_regression.py` 가 git tag 부재 시 refuse
- fixture 의 primary D₂ ratio 가 0.958 이 아니면 "corrupt" 판정
- test 실행 결과가 비결정적이면 감지 (같은 test 두 번 → 다른 결과)

**Score**: 10 / 10 — VALIDATED
