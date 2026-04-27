# V0e — Bias-floor reprobe at b_k_sq = 0

**Run:** 2026-04-27, commit `02cb6c0` plus the in-session
`primordial_b_k_sq` doc-fix at `htt/bass/hierarchy/integrator.py:145–155`.
**Script:** `scripts/v5_round17_bias_floor_reprobe.py`. **Wall time:** 7.97 min.

## Result

| k [Mpc⁻¹] | All ℓ ∈ {0, 1, 2, 3, 4} | `\|Δ_bias\|/\|Δ_target\|` |
|---|---|---|
| 1.0e-5  | Δ_bias = 0 (every ℓ) | **0.000e+00** |
| 1.0e-4  | Δ_bias = 0           | **0.000e+00** |
| 1.0e-3  | Δ_bias = 0           | **0.000e+00** |
| 1.0e-2  | Δ_bias = 0           | **0.000e+00** |
| 3.16e-2 | Δ_bias = 0           | **0.000e+00** |

`Δ_target` spans `[O(10⁻⁴), O(10²)]` across the 25 (k, ℓ) cells; every
bias value is bit-zero.

## Interpretation

The post-R10/R11 + post-R15-P0 codebase has **zero amplitude-independent
visibility-source floor**. With `b_k_sq = 0`, the Lowell §13.2 seed
formulae return all-zero moments (including
`pi_nu = -amp · (4/(3·denom)) · x² = 0` and
`G_3  = -amp · (4/(21·denom)) · x³ = 0`), and the IMEX evolves the
zero IC to zero transfer functions across the entire k range probed.
This is exactly what the R10/R11 fix was supposed to deliver — now
empirically verified for the first time on the post-R15-P0 codebase.

For reference, pre-R10/R11 the same probe gave
`|Δ_bias|/|Δ_target| = 3.08` at `k = 10⁻⁴, ℓ = 2` (per
`docs/V5_ROUND9_FINDINGS.md:271–308`). The 3.08 → 0 collapse is the
direct empirical signature of the R10/R11 ν-seed bug fix.

## Verdict

**Audit Report 2 §5.5 concern CLOSED.**

The 6.43× linear-probe residual is **not** contaminated by an
amplitude-independent floor that would survive bias-subtraction. The
residual is genuinely the bias-subtracted seed-evolution response —
i.e., consistent with D-2 being the dominant defect.

This raises the consensus audit verdict on Q1 (D-2 diagnosis) from
PARTIALLY-CONFIRMED / CONFIRMED 4.5/5 toward CONFIRMED 5/5 by ruling
out the "secondary amplitude-independent defect coexists with D-2"
alternative that Report 2 had to flag because the post-R11 measurement
was missing.

The remaining gates V0d (η_init sweep) and V0f (LSODA step audit) test
the *closure-mechanism* viability separately from the diagnosis. They
remain gated on explicit user decision (3 h and 1 h wall time
respectively).
