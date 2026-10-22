# G12-C-FINITE-CHART-ACTION-1 — independent review

Reviewer: fresh-context read-only subagent; requested gpt-6-astra/ultra (unavailable), observed claude-opus-5-5. Not the author.

**Verdict: PASS_WITH_NOTES (scoped). No blocking finding.**

## Checks

- **Statements.** All four public statements are byte-faithful to `CONTRACT.json`. The definitions in lines 1–160 are byte-identical to `raw/compile_07_12.source.lean`. `sigmaChart` is the explicit chart pushforward and is never identified with `Measure.toSphere`.
- **Hand-checked math.**
  - Moments are 4π, 4π/3 δ and 4π/15(δδ+δδ+δδ); odd moments vanish.
  - The fourth-moment contraction gives 2eᵀAe without symmetry of A, and the trA terms vanish.
  - The result is c + eᵀAe/10. The `linear_combination` residual is exactly 0.
  - Value lemmas are genuine computations from the `sphereMean` definition: radial R and angular J factors via `integral_pow`, `sq_sqrt`, `integral_cos_pow`, `integral_sin_pow` and the odd-power lemmas.
  - Means are 1, 1/3, 1/5, 1/15, and 0 when an exponent is odd.
- **Numerical check.** Gauss–Legendre on three random traceless non-symmetric A gives error ≤ 9.2e−16; the fourth-moment tensor matches to 5.8e−15.
- **Hypotheses.** Only `htrace` and `e : S2`; an instantiation with a traceless non-symmetric A typechecks.
- **Axioms.** Only propext, Classical.choice, Quot.sound; no sorry or escape hatch.
- **Receipts.**
  - compile_07_14 and compile_08_01 exit 0 with matching hashes.
  - The seven packet import source hashes match.
  - Import oleans are unchanged before and after each compile.
- **Theorem 4.** `scalar_thomson_moment` gives moment 0 = 1, moment 1 = 0 and moment 2 = 1/10, each re-derived.
- **Independent recompile.** Exit 0; olean sha256 `36e73a28952bc5bb8e602611502bc14fe928c11987a05484bb282b8786214a06`, bit-identical; byte-identical stdout.

## Notes (recorded in RETURN.json; theorems unchanged)

- **N1.** Besides the two linter warnings there is an info-level message, "Try this: ring_nf", at line 63 (`phiMeasure_univ`, in the frozen region). It is not an error.
- **N2.** The packet's `consumed_exports` overstates provenance.
  - The final corollary consumes `CAS12ScalarWrapper.scalar_thomson_moment`, not `CAS12ConventionalRodrigues.scalar_thomson_rodrigues_moment`. ConventionalRodrigues is imported but unused; mathematically equivalent, since G12-B derives from the same lemma.
  - `CAS16C03.fullMonomialTheorem` is listed as consumed but is not used; the degree ≤ 4 means are computed directly, which is stronger.
- **N3.** The delegation `allowed_files` names `AUTHOR_RETURN.json`; the final author return is `AUTHOR_RETURN_v2.json` (the successor; v1 is preserved).

## Not proved

- `sigmaChart` = canonical sphere measure.
- All-ℓ spherical-harmonic / Funk–Hecke action.
- Arbitrary L² fields.
- Energy-dependent collision.
- Spin/polarized scattering.
- Historical four-axis acceptance.
- Scientific admission (HOLD).
