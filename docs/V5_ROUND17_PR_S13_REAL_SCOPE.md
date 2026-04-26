# V5 Round-17 — PR-S13 Real Scope (Python-side D_2 = 1002.086744 µK² PSTF closure)
_Authority: this doc + `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md` (R7-authoritative). Created 2026-04-26 after the Round-16 /k-mandate retraction._

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

(a) → (c) → (b). Rationale:
- (a) is fast and likely the dominant gap; defer (b) until (a) tells us how much residual remains.
- (c) is independent of state layout and removes the CLAUDE.md-flagged Round-15 P2 caveat.
- (b) is the largest investment; commit only after (a) and (c) measurements confirm it's needed for bit-identity.

## 5. What this doc does NOT do

- Does not authorize entering any sub-track. User confirmation required.
- Does not retract the Round-16 PR-S1..S12, S14 primitives — those remain landed and tested at the primitive layer (287 tests pass).
- Does not extend the gap registry with new gaps. G1 is reframed (still open, real scope is here), not split.

## 6. Cross-references

- Empirical retraction record: `CHANGELOG.md` `[Unreleased]` Round-16 P2 entry (commit `06e6f4f`).
- R7-authoritative derivation: `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md`.
- Retracted parallel-cycle source: `docs/V5_ROUND15_P1_PSTF_DERIVATION_CHATGPT.md` (kept for traceability; do not use as authority).
- Regression-armor test: `htt/bass/los/test_flrw_bessel_projector.py::TestSharpVisibilityAnalyticOracles::test_sharp_visibility_doppler_analytic_protects_no_over_k_patch`.
- State-layout migration spec: `docs/V5_ROUND16_02_SOLVER_LAYER.md §1`.
- Runtime-track diagnosis: `docs/V5_RUNTIME_TRACK_DIAGNOSIS.md`.

---

**End of Round-17 PR-S13 real-scope ticket.**
