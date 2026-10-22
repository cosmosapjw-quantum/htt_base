# R192-A — independent review (verbatim final report of a fresh read-only reviewer)

# R192-A independent review (OMK all-order recurrence and resonance)

Reviewer: Claude Opus 5.5 (`claude-opus-5-5`), a fresh read-only reviewer who did not author the package. I modified no repository file and ran no state-changing git command. All scratch output is in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r192-a_rerun/`.

## Verdict: PASS_WITH_NOTES

There are no blocking findings. The Lean system matches the recovered source verbatim. Every frozen target is proved with the stated quantifiers. My independent sympy solve of the invariance equation agrees with the Lean recurrence and with `pr131_coefficients.json` through order 6. The module recompiles with exit 0 under the pinned toolchain, and the only axioms are propext, Classical.choice and Quot.sound.

## Per-check table

| # | Check | Result | Evidence |
|---|---|---|---|
| 1a | Card read | PASS | `unzip -p …zip …/tasks/R192-A.json`. Acceptance: (i) the recurrence holds for all n, not a finite scan; (ii) if c2≠0, the exact claim Σ=κK is removed or a counterexample is recorded. Pitfall: stop on any coefficient/denominator mismatch. |
| 1b | Source hashes | PASS | `sha256sum` matches SOURCE_RECOVERY / AUTHOR_RETURN for all seven sources plus the zip (`2d0b6da9…`). `pr_backlog.yaml` is now `5cf688f2…`. The `7bc52116` version hashes to `b204c187…` as cited, and its PR-192 entry (lines 6014-6054) diffs empty against current lines 6078-6118. |
| 1c | Vector field is verbatim | PASS | `pr131_spec.yaml` lines 82-84 and `omk_near_flrw_expansion.py` lines 72-82 match the Lean `qOMK`, `fSigma` and `fK`. My audit `example`s prove, at real points (A=F), `fSigma = -K-(S/2)((1+3w)K+3(1-w)(1-S²))`, the q formula and the fK formula. I also checked by `rfl` that `invRes = PowerSeries.derivative F h * fK w h X − fSigma w h X`, which is the residual in py line 113. |
| 1d | Domain and resonance family | PASS | Declared domain `(-1/3,1)` open (spec line 160, py line 45). T9 gives `denom>0` on the domain. T9b places every resonance in `[-5/3,-1/3)`. T8b gives `denom w n = 0 ⇔ w = -(2n+3)/(6n-3)` for all n. T8d shows the marginal points w=-1/3 and w=1 are not denominator zeros. sympy solve of `n g + a = 0` for n=1..7 gives -5/3, -7/9, -3/5, -11/21, -13/27, -5/11, -17/39, all equal to the formula. |
| 1e | Recurrence for all n (card acceptance i) | PASS | T2 `coeff_invRes_succ` is stated for every n via a power-series coefficient identity (`coeff_invRes_succ_raw`), not a scan. Hand derivation: the coefficient of K^n in `h'·K(g(1-K)+2a h²+2h) + K + (g/2)K h + a h − a h³` gives exactly `(ng+a)c_n = rhsR`. Independently, for n=1..6 the coefficient of c_n in the raw residual equals `n g + a`. |
| 1f | Pitfall: independent c1..c4 | PASS (no mismatch) | `py/indep.py` solves the residual order by order straight from the vector field. It matches the literal `rhsR/denom` for n=1..6 and C1/C2/C3_EXACT symbolically. JSON values: dust (-2/5, -26/175, -94/875), radiation (-1/3, -1/9, -2/27), all True. The spec c2 form `κ(g/2−2κ)/(2g−s)` is True. Reviewer c4 = -2(32805w⁷+…+47991)/((3w+5)⁴(5w+3)(9w+7)²(21w+11)); dust c4 = -31994/336875, radiation c4 = -5/81. The dust c4 is also proved in Lean in my audit (`example … : c 4 = -31994/336875`), which exercises n=4 of the formal recurrence. |
| 1g | Card acceptance ii: c2≠0 means Σ=κK is false | PASS | T11 holds for every κ when `9w²+18w+13≠0`; that polynomial has roots `-1±2i/3`, so it is nonzero for all real w (T11b on the domain). The T12 defect `κ(g/2−2κ)K² − aκ³K³` agrees with sympy (True). The T12b counterexample at w=0, K=1/10 gives -319/62500, reproduced by sympy. |
| 1h | Compatibility conditions | PASS (scoped) | T5/T6 hold for every w: invariant graphs are exactly the fixed points of `seqWith` with `rhsR = 0` at resonant orders, and T6b shows the resonant coefficient is free. N1-N3 are decided. My recomputed compatibility values are -1, -5/8 and -567/512, matching the author. I confirmed in Lean that `denom(-5/3)1 = denom(-7/9)2 = denom(-3/5)3 = 0`, so the negative controls sit exactly on the resonances and are genuine. n≥4 is stated but not decided, as AUTHOR_RETURN declares. |
| 1i | Amendments A1-A5 | PASS with note N3 below | **A1:** frozen T2 is genuinely false in characteristic 2. The proved witness `frozen_T2_fails_char_two` checks out, and my hand check also shows T8, T8c, T12 and `rhsR_two` fail in characteristic 2 (for example, T12 has LHS=K and RHS=0 there). The card domain is real w, so adding `[CharZero F]` is a correct, non-semantic repair. **A2/A3** are elaboration only; the `rfl` check confirms the derivative is the same. **A4:** unused hypotheses only make the statements stronger. **A5** consists of additions only. |
| 2 | No circularity; non-vacuity | PASS | No hypothesis restates a conclusion. T7's `hnr` is discharged on the domain by T9c. The T10 hypotheses are instantiated by V1 (`dust_solution_exists`, ℝ). T11's `hq` is discharged on ℝ by T11b. My audit file restates every frozen T/N signature (with A1) as an `example` closed by the author theorem, and all of them typecheck. |
| 3a | Integrity hashes and receipts | PASS | Hashes of lean, AxiomAudit, run_compile, probe, olean and all compile_01..05 sources/stdout/stderr match AUTHOR_RETURN. Exit codes are 1, 1, 0, 0, 0. Failed attempts 01/02 are retained with error logs. compile_04 source equals `lean/R192AOmkRecurrence.lean` (cmp), and compile_05 equals `raw/AxiomAudit.lean`. |
| 3b | Frozen before compile | PASS | `FROZEN_TARGETS.md` (sha `38effc4e…`) was committed in `6365e36d` on 2026-10-14 and has no diff vs HEAD. The first compile receipt is dated 2026-10-22T17:40Z. |
| 3c | Forbidden scan | PASS | `grep -nE "sorry\|admit\|native_decide\|^\s*axiom\|set_option\|opaque\|implemented_by\|extern\|unsafe\|macro\|elab\|private"` over T/lean and AxiomAudit returns no hits (rc=1). |
| 4 | Independent recompile | PASS | From cwd `/home/cosmosapjw/lean_oracles/viii_oracle` (Lean 4.31.0, commit 68218e87; mathlib `fabf563a…` per lake-manifest), I ran `lake env bash -c "LEAN_PATH=$S/out:$LEAN_PATH lean -R $S/src -o $S/out/R192AOmkRecurrence.olean $S/src/R192AOmkRecurrence.lean"` on a copy (sha `ace879f5…`). Exit 0, the same 4 unused-variable warnings, no errors. My audit `ReviewAudit.lean` (sha `535c5d83…`) runs `#print axioms` on all 63 declarations (51 theorems/lemmas, 12 defs) plus the restatement and instance checks. Exit 0. Every line is ⊆ {propext, Classical.choice, Quot.sound}; the defs and `agree_two` use only {propext, Quot.sound}. |

## Blocking findings

None.

## Non-blocking notes

1. **Off-by-one citations in SOURCE_RECOVERY.md.** For `omk_near_flrw_expansion.py`, `DECLARED_DOMAIN` is on line 45, not 44, and KAPPA/C2/C3_EXACT are on lines 47-51, not 46-50. The pr131 singular map is at lines 136-150, not 134-155. The content is correct and the hashes pin the files. Fix: correct the line numbers in a future addendum.
2. **The word "exact" remains in `htt/obsstat/egs3_omega_k_reopening.py` lines 39-41.** Card acceptance ii is met by the recorded counterexample (T11/T12b). The prose is still in that frozen module, so a downstream owner should annotate it as "linear slaving coefficient only".
3. **A1 is applied more broadly than needed.** My Lean probe proves `rhsR_one` for any `[Field F]` without CharZero. The physical domain is ℝ, so nothing changes in substance, but A1's description should say CharZero was added uniformly, not that each instance is necessary.
4. **My recompiled olean hash differs from the author's.** Mine is `2895ff6a…`; the author's is `4d94922c…`. This is expected because the build root path differs; the source hash is identical and the build succeeds.
5. **Compatibility at n=4 and n=5 (scan only, not a proof).** My sympy scan gives `rhsR = -29705/9216` at w=-11/21 and `-110630135/8388608` at w=-13/27. So the pattern of incompatibility at every resonance continues for n=4 and n=5, but it remains undecided in general.
6. **Generic-field formulation.** The generic `[Field F][CharZero F]` statements can be instantiated at `F = RatFunc ℚ`, which recovers the symbolic-in-w reading c_n(w) of the card.

## Not proved / not claimed

- Scientific admission: HOLD.
- Convergence or analyticity of Σ(K,w), and any finite-order remainder enclosure.
- Non-LRS perturbation stability (the remaining PR-192 slices) and the PR-187 / PR-191 dependencies.
- A decision of the compatibility condition at resonant orders n≥4.
- Any observational value, production use or publication use.
- Statements in nonzero characteristic beyond the char-2 counterexample.

## Scientific validation matrix (proposed scientific row for R192-A, not written)

| invariant | status |
|---|---|
| vector field matches source | PASS |
| recurrence for all n | PASS |
| resonance set | PASS |
| compatibility conditions characterized | PASS |
| compatibility decided for n≤3 | PASS |
| compatibility decided for n≥4 | NOT_TESTED (formal) |
| c1-c3 match source (independent c4 dust check) | PASS |
| linear-graph counterexample | PASS |
| convergence / remainder | NOT_APPLICABLE (out of scope) |
| scientific admission | HOLD |

Files are in `/tmp/claude-1000/-home-cosmosapjw-Dropbox-bianchi-htt-base/aa20be99-6b30-4316-9fe2-fbf4edfcb6c6/scratchpad/r192-a_rerun/`:
- `src/ReviewAudit.lean` (my audit file)
- `py/indep.py` (independent sympy solve)
- `rerun_main.stdout` (recompile output)
- `rerun_audit.stdout` (axiom audit output)

Reviewed package: `/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/ALL_OBLIGATIONS_20261011_SOURCE_RECONCILIATION/R192-A_omk_recurrence_v1_20261014/`
