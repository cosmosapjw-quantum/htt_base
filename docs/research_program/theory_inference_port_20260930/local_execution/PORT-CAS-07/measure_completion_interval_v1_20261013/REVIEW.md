# P07-A — independent review (measure-completion interval)

Reviewer: fresh-context read-only subagent; requested gpt-6-astra/ultra (unavailable), observed claude-opus-5-5. Not the author.

**Verdict: PASS_WITH_NOTES. No blocking finding.**

## Checks

- **Faithfulness.** Checked against CAS_CONTRACT `CAS-07` ("P(g>t) ∈ [known_mass, known_mass+undefined_mass]; strict >; original normalized joint mass; no survivor renormalization"), the PORT_MAP F-port limit, and the Python owner `htt/src/common/typefree_functionals.py:460 strict_exceedance`.
  - `IsCompletion` fixes the values on D and lets Dᶜ take any measurable value.
  - Undefined mass is neither dropped nor imputed.
- **Bounds.** Hold for an arbitrary measure.
- **Endpoints.** Both are attained by genuine measurable completions: `D.piecewise g t` and `D.piecewise g (t+1)`.
- **Measurability of D.** Required for upper attainment. The reviewer proved this in Lean: on (Bool, ⊥) with dirac true and a non-measurable D, the upper endpoint is 2 and is unattainable.
- **Strictness and scope.** Strict threshold respected; no intermediate-value claim.
- **Probability version.** The upper endpoint is ≤ 1, so the Python `min(1, ·)` cap is inactive in exact arithmetic.
- **Non-vacuity.** A two-atom instantiation gives the interval [1/2, 1]; both endpoints and a threshold-valued completion compile.
- **Receipts.** Source sha256 `c50940f14401670998176f4a9e8af03f4107fc891859780448d6e5a878726d9d`; compile_01–03 exit 0 with matching hashes.
- **Axioms.** Only propext, Classical.choice, Quot.sound; no escape hatches.
- **Independent rebuild.** Bit-identical olean; byte-identical stdout.

## Notes

- **N1.** The first conjunct of `probability_range` is just `prob_le_one`.
- **N2.** Assuming g measurable on all of Ω loses no generality (use `D.piecewise g 0`), but that reduction is not formalized.
- **N3.** `hD` and `hg` are unused in `completion_bounds` (frozen context).
- **N4.** Randomized completions and intermediate values are not covered.

## Not proved

- Option-valued typing of the original joint law and the bridge from finite atoms to (Ω, D, g).
- The float/fsum layer.
- Conversion of the ℝ≥0∞ endpoints to ℝ (`toReal`).
- Statistical calibration and the full PORT-CAS-07.
- Historical four-axis acceptance.
- Scientific admission (HOLD).
