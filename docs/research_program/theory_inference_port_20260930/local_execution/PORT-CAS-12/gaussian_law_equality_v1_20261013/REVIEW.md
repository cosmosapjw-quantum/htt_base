# P12-A — independent review (Gaussian law equality)

Reviewer: fresh-context read-only subagent. Requested runtime was gpt-6-astra/ultra (unavailable); observed runtime was claude-opus-5-5. The reviewer is not the author.

**Verdict: PASS_WITH_NOTES. No blocking finding.**

## Checks

- **Mathlib definition at pin fabf563a.** `multivariateGaussian μ S := (stdGaussian).map (x ↦ μ + toEuclideanCLM (CFC.sqrt S) x)`.
- **G1 `law_eq_iff`.** Separate PSD hypotheses on each side; singular and zero covariance are allowed.
  - The forward direction derives μ from `∫ x` and S_ij from `cov[x i, x j]` taken against the measure (`integral_id_multivariateGaussian`, `covariance_eval_multivariateGaussian`). These are genuine moment identities.
  - The converse direction holds because both sides are the same pushforward.
- **G2.** Three covariance forms, and the mean for all S.
- **G3.** Zero covariance gives `dirac μ`.
- **G4.** Two concrete cases show that comparing mean only, or covariance only, is not enough. A reviewer probe added a non-diagonal rank-1 shift along the null direction.
  - Same mean with different rank-1 covariances: the laws differ.
  - Same covariance with a mean shift along the null direction: the laws differ.
- **G5.** At this pin `CFC.sqrt` returns 0 for a non-PSD S, so the law collapses to `dirac μ`. The unconditional iff is formally false, which justifies the PSD premise. This is a pin artifact.
- **Python semantics.** `compare_gaussian_state_laws` requires a shared space, conditioning, frame and order, and compares exact equality of means and covariances. Its admissibility gate rejects non-PSD inputs. The correspondence to the Lean theorem is informal.
- **No circularity.** compile_02 → compile_03 changed proof text only.
- **Hashes, exit codes, axioms.**
  - All hashes match. Exit codes are 0/1/0/0 (the first failure is kept).
  - All 19 declarations use only propext, Classical.choice and Quot.sound. No sorry in `lean/`.
  - The StatementCheck file is quarantined: separate namespace, no olean, imported by nothing.
- **Independent rebuild.** The olean `89829b57…` is byte-identical and the audit stdout is identical.

## Notes

- **N1.** The result is scoped to Mathlib's parametric family. The stronger claim (any IsGaussian measure is determined by its moments) is not proved here.
- **C1.** The Python PSD gate is floating-point while Lean's is exact. "Conditioning" is a declared tag, not an operator. The bridge between the two is informal.
- **N3.** G5 is a pin artifact and must not be cited as Gaussian mathematics.
- **N4.** The helper `N1_not_posSemidef` is not frozen, but its content is part of the frozen G5.

## Not proved

- Moment uniqueness for an arbitrary IsGaussian measure.
- Different measurement spaces or conditionings.
- Non-Gaussian laws.
- Global physical injectivity.
- SymPy and Sage tool tasks.
- Full PORT-CAS-12.
- Scientific admission (HOLD).
