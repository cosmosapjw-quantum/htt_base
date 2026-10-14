# G11-A — independent reviews (integral Bregman, TEFF-A0/A1)

Reviewers: fresh-context read-only subagents. Requested runtime: gpt-6-astra/ultra (unavailable). Observed runtime: claude-opus-5-5, the same session and model family as the author. They are separate contexts, not different principals.

## Review 1 — G11AIntegralBregman.lean (author subagent): PASS_WITH_NOTES, no blocking finding

**Provenance**
- The paper PDFs hash to the ADDED_PDFS_MANIFEST entries (`d014d58f…`, `299870d7…`), and the extract hashes match.
- `CAS-11.json` hashes to `6588ac42…`.
- `TEFF_POSITIVE_BRIDGE.md` hashes to `f04d96fe…`.
- The reused C01 `BregmanThreePoint.lean` (`12f3dd68…`) is byte-identical to blob `10e02af5` on the C01 v2 branch.

**Freeze discipline**
- FROZEN_TARGETS was frozen at 10:49:18Z, before the first wrapper compile at 10:51:16Z.
- All 53 declaration headers are unchanged across compiles 02, 03 and final.

**Faithfulness**
- `nu C` is (Lebesgue on (0,∞) with density C E²) × `volume.toSphere`. The reviewer proved the sphere's total mass is 4π.
- hBE and hFD match Paper II (24). ξ takes the values MB = 0, BE = +1, FD = −1. h′ and h″ match Paper I (14).
- `dom` is open and `cdom` is closed, with `interior cdom = dom`.
- Extended-value handling is correct: `Dext ≠ ⊤ ↔ integrable`. A budget is stated only as `Dext ≤ ofReal ε`. When the divergence is non-integrable, `Dext = ⊤` and no budget is given; the Bochner integral's 0 in that case is labelled junk.
- K1 derives integrability of the cross term rather than assuming it.
- K2 assumes finitely many retained moments with exact matching and an a.e. span condition.
- K4d adds a dominating function G and labels it ADDED (not in the source).
- 1/W ≤ h″, i.e. W bounds the reciprocal Hessian.

**Numerical check** (mpmath, 25 digits, dν = 2E² dE dΩ)
- The Pythagorean identity holds for MB, BE and FD to residual ≤ 4e−25.
- With an unmatched moment, the cross term is −0.10 to −0.13, which confirms moment matching is load-bearing.

**Concern**
- The generic `finite_budget`, `endpoint_limit` and `integral_endpoint_limit` have no `g ∈ dom` guard.
- With `log 0 = 0`, the MB case f = 3, g = 0 then gives a spurious finite "budget".
- This is resolved by `G11AGuarded.lean` (Review 2).

**Stop rule**
- The `convert` failure in compile_03 repeated, but it was a tactic-level problem with an unchanged statement. Recorded as a disclosed deviation.

**Checks**
- Axioms: only propext, Classical.choice, Quot.sound (38 theorems).
- No sorry.
- An independent rebuild from source in scratch exits 0 with identical audit lines.

## Review 2 — G11AGuarded.lean (lead): PASS_WITH_NOTES, no blocking finding

- The base file is unchanged (`85993ce7…`).
- `finite_budget_stat` and `integral_endpoint_limit_stat` require f ∈ cdom a.e. and g ∈ dom a.e.
- Nonnegativity and measurability are derived from these guards rather than assumed. Conclusions are identical, or extended with `0 ≤ Dfin`.
- The machine-checked probe shows the MB(3,0) counterexample cannot satisfy the guard whenever μ ≠ 0.
- The probe also shows the guards are satisfiable, so the theorems are not vacuous.
- Open/closed roles are correct: HasDerivAt is needed at the reference, which must lie in the interior.
- Axioms: only propext, Classical.choice, Quot.sound.
- An independent full-chain rebuild from source produces a byte-identical audit.

**Note.** The generic unguarded theorems remain exported. Statistics claims must cite the `_stat` forms.

## Not proved

- The direction-pointwise constraints of Paper II (29).
- The Fubini reduction of Paper I (17)/(21).
- Existence and finiteness of R_E, R_{N,E} and f*.
- The endpoint integral limit without the added premise G.
- An integral +∞ statement for a boundary reference on a set of positive measure.
- The Taylor/Hessian envelope and (A3)–(A6).
- A certified ε.
- Scientific admission (HOLD).
