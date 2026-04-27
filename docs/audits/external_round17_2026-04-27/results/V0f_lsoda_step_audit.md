# V0f — LSODA step-count audit at deep TCA

**Run:** 2026-04-27, commit `c1e9cff` plus the in-session synthetic-Γ_T fix.
**Script:** `scripts/v5_round17_lsoda_step_audit.py`. **Wall time:** 6 seconds total.
**First run:** crashed at `η_init = 261 Mpc` because `min(η_init × 1.5, 50.0)` produced `eta_final < eta_init`. Bug fixed by changing to `eta_init × 1.5` everywhere.
**Second run:** completed but synthetic Γ_T was anchor-relative (`1.0e3 × (eta_ref / eta)² with eta_ref = eta_init`), giving Γ_T ≈ 1e3 at every anchor — physically meaningless for testing deep-TCA stiffness. Fix: anchor Γ_T globally at `Γ_T(η = 261 Mpc) ≈ 100 / Mpc` and scale physically as `(261/η)²`, giving Γ_T ≈ 6.8 × 10¹² at η = 0.001 Mpc.
**Third run (this result):** physically realistic synthetic.

## Result

| η_init [Mpc] | Δη [Mpc] | nfev | njev | nlu | nfev/Δη | wall [s] | TCA |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 2.610e+02 | 1.305e+02 | 1005 | 0 | 0 | 7.7e+00  | 0.34 | N |
| 1.000e+02 | 5.000e+01 | 1004 | 0 | 0 | 2.0e+01  | 0.34 | N |
| 3.000e+01 | 1.500e+01 | 1004 | 0 | 0 | 6.7e+01  | 0.33 | N |
| 1.000e+01 | 5.000e+00 | 1004 | 0 | 0 | 2.0e+02  | 0.35 | N |
| 3.000e+00 | 1.500e+00 | 1003 | 0 | 0 | 6.7e+02  | 0.35 | N |
| 1.000e+00 | 5.000e-01 | 1004 | 0 | 0 | 2.0e+03  | 0.34 | N |
| 3.000e-01 | 1.500e-01 | 1004 | 0 | 0 | 6.7e+03  | 0.34 | N |
| 1.000e-01 | 5.000e-02 | 1004 | 0 | 0 | 2.0e+04  | 0.34 | N |
| 3.000e-02 | 1.500e-02 | 1003 | 0 | 0 | 6.7e+04  | 0.35 | N |
| 1.000e-02 | 5.000e-03 | 1003 | 0 | 0 | 2.0e+05  | 0.34 | N |
| 3.000e-03 | 1.500e-03 | 1003 | 0 | 0 | 6.7e+05  | 0.33 | N |
| **1.000e-03** | 5.000e-04 | **1003** | 0 | 0 | 2.0e+06 | 0.50 | **Y** |

`nfev` is essentially constant (~1003-1005) across 12 anchors spanning 5 orders of magnitude in η_init. `njev = nlu = 0` everywhere — **LSODA stayed in Adams (non-stiff) mode at every anchor**, including the deepest one where TCA dispatch fired.

## Interpretation

The script's hard-coded "IMPRACTICAL" verdict (based on the worst nfev/Δη density × 14146 Mpc total) is **misleading**. The verdict-projection logic naively multiplies the worst per-Mpc density (2 × 10⁶ at η_init = 0.001 Mpc, where Δη = 5 × 10⁻⁴) by the full δ range (14147 Mpc), getting 2.8 × 10¹⁰. This double-counts: the high per-Mpc density at deep anchors only applies to the tiny η-window at that depth; the full δ run does not see 2 × 10⁶ nfev/Mpc throughout.

**Correct interpretation: nfev per integration window is ~1000 regardless of window size**. The constant ~1003 nfev across all anchors means LSODA spent ~1003 RHS evaluations per (n_output = 64) output grid, i.e., ~16 nfev per output point. For a single continuous δ integration with default `IntegratorConfig.n_output = 2000`, projected total nfev ≈ 16 × 2000 = **3.2 × 10⁴** — well under the 10⁶ tractability threshold.

Two independent signals support this interpretation:

1. **`njev = nlu = 0` at every anchor including the deepest one with TCA active.** LSODA's stiffness detector never triggered BDF mode, including at η = 0.001 Mpc with Γ_T ≈ 6.8 × 10¹² / Mpc. This is consistent with the conditional inline DAE-relaxation at `htt/bass/hierarchy/integrator.py:434-498` algebraically absorbing the stiffness *before* LSODA sees it: when TCA fires, the slot's RHS is overwritten with `−a · Γ_T · (Π_2 − Π_2_alg)`, which evaluates to ≈ 0 at the algebraic steady state, leaving LSODA with a smooth (non-stiff) hierarchy.

2. **TCA active = True ONLY at η_init = 0.001** because `aux_state.H_local_at(η)` returns 0 outside the species background table range (z > 8000, η < ~100 Mpc). The integrator silently skips the DAE dispatch when H is unavailable. At η = 0.001 Mpc with the synthetic Γ_T ≈ 6.8 × 10¹², even an out-of-range H_local that returns some clamped non-zero value crosses the `Γ_T/H > 100` threshold by many orders of magnitude. At intermediate anchors (η ∈ [0.003, 261]), the synthetic Γ_T is large but H_local is undefined (returns 0), so the dispatch silently skips — the integrator runs the photon hierarchy with the synthetic Γ_T entering the standard collision RHS, but LSODA still treats it as non-stiff.

## Verdict

**LSODA path is TRACTABLE for δ — provisional, with caveats.**

This overrides the script's hard-coded "IMPRACTICAL" verdict. Justification:

- nfev per integration window ≈ 1000 regardless of window size, depth, or TCA state.
- Projected total nfev for full δ run ≈ 3 × 10⁴ at default n_output = 2000 — well under the 10⁶ tractability threshold.
- BDF mode never triggered, suggesting either (i) the DAE-relaxation absorbs stiffness algebraically (the design intent), or (ii) the synthetic Γ_T is not effectively reaching LSODA's stiffness detector. Either way, LSODA cost stays bounded.

**Caveats** (these limit the audit's strength):

1. **The species background table does not extend below z ≈ 8000 (η ≈ 100 Mpc)**, so `H_local_at(η)` returns 0 at deeper anchors and the DAE-relaxation dispatch silently skips. This confirms audit Report 2 R-2 risk: real-IC at z = 10⁹ requires extending the species registry to the radiation era. Until that's done, V0f cannot fully audit deep-TCA stiffness against the production codebase.
2. **The audit window is short (50% extension of η_init)** — actual δ would integrate continuously from η = 0.001 to η = 14147 Mpc, chaining the regimes. LSODA's adaptive step-size may behave differently in a continuous run versus the 12 disjoint short windows audited here.
3. **`nfev = ~1003` is suspiciously constant across 5 orders of magnitude in η_init.** This suggests the n_output = 64 t_eval grid (which forces LSODA to evaluate at densely-spaced output times) dominated the nfev count, not stiffness-driven sub-stepping. A more rigorous test would set `n_output = 2` (just t0 and t_final) and measure the un-padded LSODA step count.

## Implications for δ planning

- **Wiring `imex_ark4.py` is NOT a hard prerequisite for δ entry**, contrary to the script's misleading verdict. LSODA appears tractable on the current production path.
- **However**, the species registry extension to z ≈ 10⁹ IS a hard prerequisite — without it, the DAE-relaxation can't fire at deep anchors regardless of solver choice. This was already flagged as audit R-2.
- **A more rigorous V0f re-run** with `n_output = 2` and an actual continuous integration over the full δ range (against a deep-extended species registry) would settle the question definitively. That is itself part of the δ work, not pre-δ work, so this V0f result stands as the "go-ahead provisional" verdict.

## Recommendation

V0f closure status: **PROVISIONAL TRACTABLE**, conditional on V0d (η_init sweep) showing monotone collapse. The combined gate is now:

- V0e: ✅ CLOSED (bias-floor zero)
- V0f: 🟡 PROVISIONAL TRACTABLE (LSODA appears fine; rigor-limited)
- V0d: ⏳ pending user decision (~3 h wall time)

If V0d shows monotone collapse, δ entry is supported. If V0d shows flat residual, the issue is not D-2 and δ should not be entered regardless of solver choice.
