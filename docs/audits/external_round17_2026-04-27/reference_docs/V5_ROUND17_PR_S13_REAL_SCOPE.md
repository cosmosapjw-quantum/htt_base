# V5 Round-17 — PR-S13 Real Scope (Python-side D_2 = 1002.086744 µK² PSTF closure)
_Authority: this doc + `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md` (R7-authoritative). Created 2026-04-26 after the Round-16 /k-mandate retraction. P2 measurement appended 2026-04-27._

> **2026-04-27 P2 update.** Sub-track (a) has been **empirically
> measured via `compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0)`**
> at N_k=65 (script
> `scripts/v5_round17_linear_probe_measurement.py`) and produces
> **D_2 = 6.4395e+03 μK²**, residual ratio ≈ **6.43** vs the Rust
> MB-95 anchor 1002.086744 μK². This closes 6.4 orders of magnitude
> of the +2.04e+10 μK² canonical-path gap and confirms (a) as the
> dominant gap (per §3 (a) "within ~25× of anchor → primordial
> normalization confirmed"). The residual 6.43× is **not a single
> missing convention factor** — see §7 below for the V5_ROUND12_TO_14
> D-2 triangulation. Sub-track ordering recommendation revised in §4.

---

## 1. Why this doc exists

The Round-16 handoff (`docs/V5_ROUND16_NEXT_SESSION_HANDOFF.md`, commit `607e759`) instructed a "Doppler /k correction" as PR-S13's load-bearing fix. That instruction was empirically falsified on 2026-04-26:

| Configuration | D_2 (µK²) | Δ vs Rust MB-95 anchor (1002.086744 µK²) |
|---|---:|---:|
| Current Python PSTF (canonical `(g v_b)'`) | 2.0451 × 10¹⁰ | +2.0451 × 10¹⁰ (≈ 7 orders of magnitude) |
| Python PSTF + `/k` Doppler patch          | 2.0448 × 10¹⁰ | +2.0448 × 10¹⁰ |
| Effect of `/k` patch on D_2 | — | −0.012% (vs spec-claimed 0.5%) |

The /k patch was (a) inherited from the parallel-cycle ChatGPT derivation explicitly retracted as Appendix X "false trail" in the R7-authoritative Opus derivation, (b) banned by the in-tree regression-armor test [`test_sharp_visibility_doppler_analytic_protects_no_over_k_patch`](../htt/bass/los/test_flrw_bessel_projector.py), and (c) inconsistent with BASS's `v_b` slot already carrying the dimensionless `θ_b/k` (verified at [`htt/bass/hierarchy/seed_compatibility.py:210`](../htt/bass/hierarchy/seed_compatibility.py#L210)).

The *actual* gap is ~7 orders of magnitude, dominated by **primordial-amplitude normalization**. This doc enumerates the real PR-S13 closure work.

## 2. Forbidden moves (carried from Round-16 §8 + this session)

- **Do not add a Doppler `/k` factor.** The canonical `(g v_b)'` form is correct (R7 derivation §2.3, lines 405-407). The regression-armor test must continue to pass.
- **Do not mark `htt/bass/spectrum/test_d2_pstf_closure.py` xpass without verifying the actual numerical value against the Rust `bass_rs dump_dl_spectrum_sparse` output.** The xfail mask hid both the latent `L_max_tower=4 / ell_max_transfer=8` config bug (fixed 2026-04-26) AND the +2.04 × 10¹⁰ µK² gap. Visibility wins over coverage metrics.
- **Do not enter sub-tracks (a)/(b)/(c) below without explicit user confirmation.** Each is multi-day; the user prompt explicitly forbids autonomous entry.

## 3. Real PR-S13 sub-tracks (each requires user confirmation to enter)

### (a) Primordial-amplitude alignment — **leading hypothesis**

**Hypothesis.** The Python PSTF pipeline returns transfer functions whose effective seed is `max(|Σ_±|, 1e-6)` (per the existing `test_d2_pstf_closure.py` docstring lines 55-60, [`htt/bass/spectrum/test_d2_pstf_closure.py:55-60`](../htt/bass/spectrum/test_d2_pstf_closure.py#L55-L60)) rather than the physical primordial curvature amplitude. The Rust MB-95 path produces the anchored 1002.086744 µK² because it pairs unit-amplitude transfer functions with `P_R(k) = A_s · (k / k_pivot)^(n_s−1)` exactly once at C_ℓ assembly. The Python pipeline appears to either (i) double-multiply by the seed or (ii) skip the `A_s ≈ 2.1 × 10⁻⁹` factor entirely.

**Quick diagnostic to run before committing to (a):**
1. Inspect [`htt/bass/spectrum/cl_assembly.py`](../htt/bass/spectrum/cl_assembly.py) to confirm whether `P_R(k)` multiplication is wired or stubbed.
2. Run the Python pipeline at `primordial_b_k_sq = 1.0` (default) AND at the canonical `A_s = 2.1 × 10⁻⁹`; compare D_2 values.
3. If D_2 scales linearly with `primordial_b_k_sq` and the canonical-`A_s` run lands within ~25× of the anchor, primordial normalization is confirmed as the dominant gap. The remaining ~25× residual is likely the (b) state-layout migration.
4. If D_2 does *not* scale linearly, the gap is structural (not amplitude) and (a) is not the right next move.

**Estimated effort.** 1-2 days for diagnostic + cl_assembly wiring fix.

**Ship gate.** D_2 within 1% of the Rust anchor (not yet 1e-9 bit-identity). xfail stays in place.

### (b) State-layout migration `m=0` → `m∈{-2..+2}`

**Scope.** Per `docs/V5_ROUND16_02_SOLVER_LAYER.md §1` and Round-16 handoff §4.1 steps 1-4:

1. Migrate the state vector: extend `pack_combined_state` / `unpack_combined_state` in [`htt/bass/hierarchy/pack_unpack.py`](../htt/bass/hierarchy/pack_unpack.py) from m=0 to m∈{-2..+2}, preserving the FLRW limit at the m=0 slice exactly (so existing FLRW tests stay bit-identical).
2. Wire `mode_mixing_blocks` into `hierarchy_rhs.py`: extend [`htt/bass/hierarchy/hierarchy_rhs.py`](../htt/bass/hierarchy/hierarchy_rhs.py) to call `assemble_A_mix_block` + `assemble_A_curv_block` + `assemble_EB_mixing_block` per η, contracting against the evolved background `σ_2M(η)` from `BackgroundEvolved.sigma_squared_at(η)` (PR-S1).
3. Extend `BackgroundEvolved` to expose the full 5-vector `σ_2M(η)` (not just the scalar `sigma_squared_at`).
4. Wire `seed_factory` into `ic.py`: replace the existing FLRW-only IC build in [`htt/bass/hierarchy/ic.py`](../htt/bass/hierarchy/ic.py) with the per-family dispatch from `bass.hierarchy.seed_factory.get_seed_factory`.
5. Wire `family_propagators` into the LoS pipeline: dispatch non-FLRW families to `bass.los.family_propagators.get_propagator(family)`.

**Estimated effort.** 3-5 days. Do not start without (a) result.

**Ship gate.** D_2 within 1e-9 of Rust anchor (bit-identity). xfail removed.

### (c) Real-IC injection at η(z_*)

**Scope.** Carried from `docs/V5_RUNTIME_TRACK_DIAGNOSIS.md` Blocker 3. Not blocked by IMEX stability (Round-15 closed Blocker 2). Implement `BackgroundMonitor.from_recombination(background_monitor, z_*)` constructor.

**Estimated effort.** 1-2 days.

**Ship gate.** Per-cell monopole-frame contract closes at sub-percent (folds in CLAUDE.md §3 Round-15 P2 lift).

## 4. Recommended sub-track ordering

**Original (2026-04-26).** (a) → (c) → (b).

**Revised (2026-04-27, post-§7 P2 measurement).** (a-switch) → (c) → (b) → D-2.
Rationale, in light of the §7 finding that the residual 6.43× ratio is the V5_ROUND12_TO_14 D-2 signature (Lowell §13.2 leading-order seed valid only for `x = k·η_init ≪ 1`):

- **(a-switch) — fast.** (a) is empirically closed by the existing `compute_flrw_d_ell_linear_probe` path. The remaining (a)-implementation work is to switch the canonical `compute_flrw_d_ell` default to call the linear-probe path (or equivalently, fix `unit_amplitude_normalization=True` to no longer divide by `max(|Σ_±|, 1e-6) = 1e-6` in the FLRW limit) and update `test_d2_pstf_closure.py` xfail message to point at D-2. 1-2 days. Does **not** close `xpass` — the residual 6.43× remains.
- **(c) — independent.** Real-IC injection at η(z_*); closes the CLAUDE.md §3 Round-15 P2 monopole-frame caveat. 1-2 days. Does **not** directly close the 6.43× residual.
- **(b) — Bianchi enabling.** State-layout migration `m=0 → m∈{-2..+2}` plus the rest of §3 (b)'s steps 2-5. Required for off-axis Bianchi families regardless of FLRW closure status. 3-5 days. Does **not** close the FLRW 6.43× residual.
- **D-2 — multi-month.** Push integrator η_init to z ~ 10⁹ via tight-coupling-enabled startup (CLAUDE.md §3 Round-15 P2 actionable). Only after D-2 lands does `test_d2_pstf_closure.py` flip `xpass` and Phase 1 declare PSTF bit-identity. The conditional inline DAE-relaxation in `htt/bass/hierarchy/integrator.py:434-498` is the permitted mechanism (TCA *pre-phase* remains banned per CLAUDE.md §6).

## 5. What this doc does NOT do

- Does not authorize entering any sub-track. User confirmation required.
- Does not retract the Round-16 PR-S1..S12, S14 primitives — those remain landed and tested at the primitive layer (287 tests pass).
- Does not extend the gap registry with new gaps. G1 is reframed (still open, real scope is here), not split.

## 6. Cross-references

- Empirical retraction record: `CHANGELOG.md` `[Unreleased]` Round-16 P2 entry (commit `224a177`).
- R7-authoritative derivation: `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md`.
- Retracted parallel-cycle source: `docs/V5_ROUND15_P1_PSTF_DERIVATION_CHATGPT.md` (kept for traceability; do not use as authority).
- Regression-armor test: `htt/bass/los/test_flrw_bessel_projector.py::TestSharpVisibilityAnalyticOracles::test_sharp_visibility_doppler_analytic_protects_no_over_k_patch`.
- State-layout migration spec: `docs/V5_ROUND16_02_SOLVER_LAYER.md §1`.
- Runtime-track diagnosis: `docs/V5_RUNTIME_TRACK_DIAGNOSIS.md`.
- **R17 P2 measurement script (added 2026-04-27)**: `scripts/v5_round17_linear_probe_measurement.py`.
- **D-2 triangulation reference (added 2026-04-27)**: `docs/V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md` §"Three independent defects" + §"What was tried + why it failed". 10-auditor 4-cycle consensus that no single multiplicative factor closes the residual.

---

## 7. R17 P2 measurement (2026-04-27)

### 7.1 Result

`compute_flrw_d_ell_linear_probe(probe_b_k_sq=1.0)` was run at the same `(k_grid, L_max_tower, ell_max_transfer)` as `htt/bass/spectrum/test_d2_pstf_closure.py` (k_grid = `np.logspace(-4.0, -1.5, 65)`; L_max_tower = ell_max_transfer = 8; n_workers=4). Wall time 31.4 min. Script: `scripts/v5_round17_linear_probe_measurement.py`. Run on commit `7722f95`.

| Path | D_2 (μK²) | Δ vs anchor | Ratio |
|---|---:|---:|---:|
| Rust MB-95 anchor | 1002.087 | — | 1.00 |
| Canonical `compute_flrw_d_ell` (Round-16 P2 measurement) | 2.0451 × 10¹⁰ | +2.0451 × 10¹⁰ | 2.04 × 10⁷ |
| **R17 (C) `compute_flrw_d_ell_linear_probe`** | **6.4395 × 10³** | **+5.4374 × 10³** | **6.43** |

### 7.2 Closure of (a) — primordial-amplitude alignment

The 6.4-orders-of-magnitude jump from canonical 2.04 × 10¹⁰ μK² to linear-probe 6.44 × 10³ μK² is closed by the `unit_amplitude_normalization=False` toggle (forced by the linear-probe path) plus the bias-subtraction pair (b_k_sq=0 + b_k_sq=probe_b_k_sq, then `Δ_pure = Δ_target − Δ_bias`). The empirical signature matches §3 (a) ship gate: residual ratio < 25× → "primordial normalization confirmed as the dominant gap."

`compute_flrw_d_ell_linear_probe` is therefore the **already-existing remediation path** for (a). The (a) implementation work reduces to switching the canonical pipeline default to invoke this path (or to disable the spurious 1e-6 floor in the canonical path directly).

### 7.3 The residual 6.43× is D-2, not a single missing factor

Trajectory of the convention-audit residual ratio across investigations:

| Round | N_k | D_2^probe / D_2^Route-B | Closed by |
|---|---:|---:|---|
| R9 (Section 2 of `V5_ROUND9_FINDINGS.md`) | 4 | 2.93e+04 | (R9-D fix: B_K_sq factor on `pi_nu`, `G_3` in `_seed_formulae`, applied Round-10/11) |
| R9 dense | 24 | 1.36e+04 | (same) |
| R12-14 (post-R11, `V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md` TL;DR) | — | 7.57e+02 | — |
| **R17 P2 (this measurement)** | **65** | **6.43** | (Round-15 P0 D-1 LoS grid decoupling, plus other Round-15/16 closures) |

The factor 117× improvement R12-14 → R17 came principally from Round-15 P0 (`bass.los.los_grid_builder.build_los_grid()` decoupled LoS quadrature from IMEX η-grid). The remaining 6.43× has the V5_ROUND12_TO_14 D-2 signature: the Lowell §13.2 leading-order seed `_seed_formulae` is valid only for `x = k·η_init ≪ 1`, and at η_init ≈ 261 Mpc the validity boundary is `k ≈ 4e-3 Mpc⁻¹`. The k_grid here spans `[1e-4, 3.16e-2] Mpc⁻¹` — over half the points sit in `x > 1` invalid territory:

| k [Mpc⁻¹] | x = k·η_init | Lowell §13.2 validity |
|---|---:|---|
| 1e-4 | 0.026 | ✓ |
| 4e-3 | 1.04 | boundary |
| 1e-2 | 2.6 | invalid |
| 3.16e-2 (k_max) | 8.25 | catastrophic (`O(x²) >> 1`) |

The IMEX integrator faithfully evolves wrongly-seeded sub-horizon modes forward, over-amplifying Φ, Ψ, Θ_0 at recombination. R12-14 verdict (10 external auditors, 4 cycles): **"Per-(k, ℓ) data falsify any single multiplicative factor."** R14 finding F1: per-(k, ℓ) std/|mean| was 108-357% across all candidate factors (4√2, n_output increase, k_min clipping, Doppler resampling) — incompatible with any single calibration constant. The only structural fix is D-2 closure: extend integrator η_init to z ~ 10⁹ via tight-coupling-enabled startup so that `x = k·η_init ≪ 1` holds for all Planck-relevant k.

### 7.4 What this means for the §3 sub-tracks

- **(a) primordial-amplitude alignment** is empirically closed by the linear-probe path. The (a) implementation work is the default switch (1-2 days). It does **not** remove the residual 6.43×, which is D-2 (not (a)).
- **(c) real-IC injection at η(z_*)** is independent of the residual; addresses the CLAUDE.md §3 Round-15 P2 monopole-frame contract closure.
- **(b) state-layout migration** is required for the off-axis Bianchi families regardless of FLRW closure; not the source of the FLRW 6.43× residual.
- **D-2 (multi-month) is the only sub-track that closes the residual to bit-identity** and flips `test_d2_pstf_closure.py` to `xpass`.

### 7.5 Forbidden moves carried forward (post-P2)

- Do not attempt to absorb the 6.43× into a `calibration_factor` value baked into `compute_flrw_d_ell_linear_probe` defaults. The R12-14 4-cycle verdict explicitly forbids this (per-(k, ℓ) variance falsifies any single factor). `calibration_factor` remains an opt-in diagnostic knob, not a production calibration.
- Do not declare PR-S13 (a) or G1 closed solely on the linear-probe path landing at 6.43× ratio. (a)-switch closes one piece; full G1 closure requires D-2.
- Do not edit `_seed_formulae` to add higher-x correction terms (V5_ROUND12_TO_14 §"D-2" sub-option (D-2b) is non-viable: ~20 orders required to converge at x=14).

---

**End of Round-17 PR-S13 real-scope ticket.** R17 P2 measurement appended 2026-04-27.
