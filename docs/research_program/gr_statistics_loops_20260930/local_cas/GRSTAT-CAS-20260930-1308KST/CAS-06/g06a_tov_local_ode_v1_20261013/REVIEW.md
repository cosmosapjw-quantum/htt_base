# G06-A — independent review (TOV local ODE)

Reviewer: fresh-context read-only subagent. The requested runtime was gpt-6-astra/ultra (unavailable); the observed runtime was claude-opus-5-5. The reviewer is not the author.

**Verdict: PASS_WITH_NOTES (scoped). No blocking finding.**

## Checks

- **Source recovery.**
  - PR #477 `adopted_successor_v1/ADMITTED_INPUTS.json` (sha256 `711de321…`) `definitions.C01` gives the metric diag(−e^{2ν}, 1/F, r², r² sin²θ) with F = 1 − 2m/r − Λr²/3.
  - It gives the ODE m′ = κr²ε/2, ν′ = (m + καεr³/2 − Λr³/3)/(r²F), ε′ = −(1+α)εν′/α.
  - The EOS is p = αε with 0 < α < 1 and κ > 0; the domain is r > 0, F > 0, ε > 0.
- **Reused modules.** CAS06ScalarAccepted, CAS06Foundation, C03Action and CAS06Bundles are byte-identical to PR #477 head.
- **ODE faithfulness.** Signs, the κ/2 factor and α all match the source. With κ = 8π the system is the standard TOV.
- **Domain.** The strict open set is proved open. r = 0, F = 0, ε ≤ 0 and α = 0 are each proved excluded.
- **Smoothness.** The RHS is C^n for all n ≤ ∞ and locally Lipschitz.
- **Existence (T3).** Mathlib Picard–Lindelöf on the lifted autonomous field gives actual solution functions with HasDerivAt for all three equations, with positivity preserved on (r0−δ, r0+δ).
- **Uniqueness (T4).** Proved on a common open interval using pointwise local Lipschitz bounds and connectedness; no global constant.
- **Einstein equations (T5).** The hypotheses are only admissibility, solution and chart; no Einstein or curvature equation is assumed.
  - It instantiates the accepted `C01_TOV_metric_bundle`, whose Einstein tensor is derived from the actual chart metric.
  - All 16 components are covered (all 10 independent ones): G + Λg = κT with T̂ = diag(ε, αε, αε, αε).
- **Independent sympy check.** All 16 components of G + Λg − κT simplify to 0 on the ODE. Two negative controls (flipped ε′ sign; dropped ½) fail as expected.
- **Non-vacuity.** The capstone gets its solution from existence; an inhabitation example compiles.
- **Frozen vs proved.** All 13 frozen signatures match after whitespace normalization.
- **Receipts.** compile_01–08 exit codes are 0,0,0,0,1,0,0,0 and all hashes match. compile_05 is the real first failure; only proof text changed after it.
- **Axioms.** Only propext, Classical.choice and Quot.sound, across 15 + 219 dependency reports. No sorry in `lean/` or in the audit.
- **Independent rebuild.** Dependencies were taken from `git show` of PR #477, not from the working tree. All modules and the audit exit 0; the audit stdout is identical after path normalization.

## Notes

- **N1.** The solution's own C^∞ regularity is not stated. The field is C^∞; the solution has the derivatives the Einstein equations need. A bootstrap theorem is optional.
- **N2.** The working-tree bytes must be preserved on commit.
- **N3.** "Frozen before proving" rests only on file mtimes (19:45 vs 19:48 KST). The signatures match exactly.
- **N4.** Curvature correctness is inherited from the accepted bundle and independently cross-checked by sympy. Uniqueness is on common open intervals, not maximal intervals.

## Not proved

- Global regular-star existence.
- Centre regularity at r = 0.
- Maximal interval of existence; continuation to F = 0 or r = 0.
- C^∞ regularity of the solution functions.
- EOS admissibility beyond 0 < α < 1.
- Historical four-axis acceptance.
- Scientific admission (HOLD).
