# G10-C — independent review (verbatim final report of a fresh read-only reviewer)

**Verdict: PASS_WITH_NOTES.** No blocking finding. Reviewer: fresh-context read-only in-session subagent (subscription fallback), observed claude-opus-5-5 (self-reported).

## Checks

- **Card acceptance.** The finite quintic is never called C∞; `q0_not_smooth` and `q0_not_contDiff_three` prove it is not. Support, plateau and bounds are preserved after mollification. Receipts are present.
- **Source fidelity** (INFORMATION_LIMIT_THEOREMS Thm III, lines 148–153, sha 775b7d15…):
  - q0 = G(2r/a − 1/2), with all three source branches and closed endpoints.
  - `IsMollifier` means C∞, ≥ 0, unit integral and support in [−a/8, a/8], quantified over all mollifiers. M0 gives existence.
  - `↑⊤` here is C∞, not analytic.
- **M3 (q0 is C² but not C³).** Gpp's one-sided derivatives are 0 and F‴(0) = −60. Sympy and numerics agree (−477.7 vs −480 at a = 1).
- **M4.**
  - qe = q0(r)·q0(−r) equals q0 for r ≥ −a/4.
  - So ρ⋆q0 = ρ⋆qe for r ≥ −a/8, which covers all radial r ≥ 0. Numerically the difference is 0 there.
  - The restriction is real: qe(−1) = 0 but q0(−1) = 1.
- **M2 (exact bounds).**
  - The derivative of the convolution is moved onto the compactly supported C² qe.
  - Convolving with a probability density does not raise the sup norm.
  - The constants are exactly 15/(4a) and 40/(√3 a²), with no loss. Numerically 3.47 ≤ 3.75 and 19.11 ≤ 23.09.
  - The q0 constant is attained.
- **M1.** Plateau 1 on |r| ≤ a/8, support zero for |r| ≥ 7a/8, values in [0,1]; checked numerically.
- **M5 (radial C∞).** At x = 0 the function is locally constant 1; elsewhere it is the norm composed with a smooth function.
- **C04 copy.** F/F′/F″ and the bound proofs are text-identical to `CutoffExtrema.lean` (sha ab2f98d2…).
- **Hypotheses.** No circular hypotheses. `IsMollifier` is satisfiable and non-trivial.
- **Hashes.** All hashes match.
- **Compile history.** compile_01 exit 1 (kept); 02 and 03 exit 0; only proof text changed between them.
- **Axioms.** All 84 public theorems use only propext, Classical.choice and Quot.sound (the reviewer's own audit). No forbidden tokens.
- **Independent recompile.** Exit 0, with the same four linter warnings.

## Notes

1. The literal ρ⋆q0 is not certified for r < −a/8. This is irrelevant for radial use and was disclosed.
2. `g10c_main` omits the radial 0 ≤ X ≤ 1 and `radial_ray`; both follow from `smoothCutoff_mem`.
3. There is no d/dr statement for X(r·n); the downstream (I13) step will need one.
4. The C04 directory is untracked locally; its provenance rests on verified on-disk hashes.
5. The author's audit covered 23 of 84 theorems; the reviewer's audit covers all 84.
6. Process items:
   - Linter warnings.
   - The freeze ordering is evidenced only by mtimes.
   - The source is ILT, which is marked `orchestrator_identity_only` for the C04 axes. Its use was disclosed, and the lead accepts it for this G10-C card.
7. The numerical checks are cross-checks only.

## Not proved

- The (I12) test field.
- The ray derivatives χ′ and χ″.
- The (I13) inequality, the (I14) chain and the 1147/1152 margin.
- The exp and √3 inputs.
- Theorem III and its identifiability consequences.
- The two-point bounds.
- Scientific admission (HOLD).

