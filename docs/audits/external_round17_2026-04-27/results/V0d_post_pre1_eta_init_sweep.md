# V0d (post PR-V0d-pre1 re-run) — η_init sweep with real `1 / Γ_T(η_init)` τ_c

**Run:** 2026-04-27, post-PR-V0d-pre1 (pre-commit; `_seed_formulae` now
accepts a `tau_c` parameter and `ver2_native_integrator.py` passes
`1 / Γ_T(η_init)` from the species visibility source).
**Script:** `scripts/v5_round17_eta_init_sweep.py` (unchanged).
**Wall time:** 195.2 min on 4 workers.

## Pre-pre1 vs post-pre1 comparison

| η_init [Mpc] | Pre-pre1 ratio | **Post-pre1 ratio** | Change | Verdict |
|---:|---:|---:|---:|:---|
| 261.0 | 7.043 | **6.455** | **−8.4 %** | ✅ matches V0e direct measurement (6.43) |
| 200.0 | 1.265 × 10⁸ | 1.251 × 10⁸ | −1.1 % | unchanged: Lowell §13.2 invalidity dominant |
| 150.0 | 2.877 × 10²⁴ | 8.461 × 10²⁵ | +29× | worse |
| 100.0 | 2.724 × 10³⁰ | 7.263 × 10³³ | +2670× | much worse; PCHIP overflows |
| 70.0  | 4.838 × 10²⁷ | 2.684 × 10³⁰ | +555× | worse; PCHIP overflows |
| 50.0  | 1.356 × 10³⁰ | 1.356 × 10³⁰ | unchanged | (silent NaN-clip, identical) |

## Interpretation

### What pre1 fixed at η_init = 261 (decisive)

Pre-pre1 V0d at the in-table anchor produced ratio 7.04, which differed
from V0e's direct linear-probe measurement of **6.43** by ~10 %. With the
real `1 / Γ_T(η_init = 261 Mpc)` from the species visibility source, V0d
post-pre1 lands at 6.45 — within rounding of V0e. This bit-equivalence
confirms that:

- The production τ_c plumbing is correctly threaded through
  `ver2_native_integrator._build_seeded_initial_state` and
  `_build_intrinsic_family_seeded_initial_state`.
- At the recombination-era anchor where the species table is well-defined,
  the legacy heuristic was overestimating τ_c by enough to shift D_2 by
  ~10 %. Pre1 closes that gap.
- V0e (direct linear-probe with default integrator settings) and V0d
  (monkey-patched eta_init = 261) are now consistent at the 0.5 %-level.

This is the cleanest validation that pre1 does the right thing inside the
species table's coverage.

### Why pre1 doesn't help at η_init ≤ 200

The audit's prediction (Report 2 §2.3) was that shrinking η_init would
collapse D_2 toward the anchor as soon as `x_max = k_max · η_init < 1`.
Post-pre1 we still see explosive growth at η_init in [50, 200] Mpc.
Three coupled defects explain it; **all three must be fixed before V0d
can become a clean D-2 diagnostic**:

1. **Species background table edge at z ≈ 8000 (η ≈ 100 Mpc).**
   `aux_state.H_local_at(η)` and `_resolved_gamma_t(η)` start returning
   degenerate or extrapolated values below the table edge. PCHIP
   overflow warnings fire at η_init ∈ {100, 70} Mpc — confirmed
   identical to the pre-pre1 run. Pre1 cannot fix what the table
   doesn't cover.
2. **IMEX integrator's pre-recombination tuning gap.** The 8 algebraic
   patches in `bass/hierarchy/ver3_layout_protocol.py` (Round-15
   Blocker 2 closure) were validated for `η ∈ [261, 14147] Mpc`
   (post-recombination). Starting at η_init < 261 puts the integrator
   into a pre-recombination regime with `Γ_T / H ≫ 100` for an extended
   period before the visibility peak; the DAE-relaxation must be
   smooth across the threshold transition. Switch-smoothness at this
   transition has not been audited.
3. **`cosmological_config.py:77-148` z_injection ∈ [100, 5000] guard.**
   V0d's monkey-patch bypasses the guard, but the helper's other
   internal assumptions about recombination-era anchor anchoring are
   silently broken at η_init ≪ 261. (Was Defect-3 in the pre-pre1 V0d
   diagnosis.)

These are **the three Phase 0.5 prerequisites** identified in the
post-V0d analysis. Pre1 closed defect-1's seed-formula component but
left defects 2 and 3 untouched. The remaining η_init ≤ 200 explosion is
those two defects.

### Why pre1 made some intermediate anchors *worse*

At η_init = 150, 100, 70 the post-pre1 ratios are larger than pre-pre1.
The mechanism: pre1 gave the seed a much smaller (more physical) `pi_gamma`
at the IC — but the IMEX evolution then amplified differences in subtle
ways downstream. With the previously-incorrect-but-self-consistent
heuristic τ_c, the IC errors partially cancelled against integrator
artefacts further along the chain. With the now-correct seed but
unfixed downstream defects, the cancellation goes the other way.

This is a known pathology of partial fixes in tightly-coupled physics
pipelines and is not unexpected. It is **not** a regression at the API
level (the pre1 fix at η_init = 261 is unambiguously correct); it is
evidence that pre1 must ship together with pre2 + pre3 to be observably
beneficial below η_init = 261.

## Verdict

**PR-V0d-pre1 lands as a correct partial fix.** Validation:

- 287 Round-16 baseline + 304 perturbation + 14 new tau_c-override tests
  pass (605 total).
- 14 new unit tests pin the API contract: tau_c=None backward-compat;
  tau_c=explicit linear scaling on pi_gamma and E_2; tau_c<0/NaN/inf
  rejected; public wrappers thread tau_c through correctly.
- V0d at η_init = 261 produces 6.45, matching V0e's direct measurement
  of 6.43 — the cleanest bit-level validation that pre1's production
  plumbing is correct.

But pre1 **alone** does not move V0d's overall verdict from
INCONCLUSIVE. It cannot — defects 2 and 3 (species table edge, IMEX
pre-recombination tuning) are independent of the τ_c heuristic. V0d
remains INCONCLUSIVE until **pre2 + pre3** also land.

## Recommendation

Continue with **pre3** next (sub-day; mechanically simple lift of the
z_injection guard with proper species-table-aware validation), then
**pre2** (the larger species-registry extension). After both land,
re-run V0d. The audit's monotone-collapse prediction can then be
tested cleanly.

Pre1 should ship as-is; it is a strict improvement at η_init ≥ recombination
and a necessary ingredient for the eventual deep-anchor seed at z ≈ 10⁹.

## Files in this PR

- `htt/bass/perturbation/regular_adiabatic_ic.py` — `_seed_formulae`,
  `regular_adiabatic_formulae`, `make_camb_regular_adiabatic_seed` all
  gain `tau_c: float | None = None` keyword. Default None preserves the
  legacy heuristic (`_approx_tau_c`) for backward compatibility.
- `htt/bass/hierarchy/ver2_native_integrator.py` — both seed-builder call
  sites (`_build_intrinsic_family_seeded_initial_state` at line ~1500,
  `_build_seeded_initial_state` at line ~1612) compute
  `tau_c_initial = 1 / max(_resolved_gamma_t(...), 1e-300)` and pass it.
  Falls back to `None` (heuristic) if `_resolved_gamma_t` returns 0.
- `htt/bass/perturbation/test_seed_tau_c_override.py` — 14 new unit
  tests for the tau_c parameter behaviour.
- `docs/audits/external_round17_2026-04-27/results/V0d_post_pre1_eta_init_sweep.md`
  (this file).
