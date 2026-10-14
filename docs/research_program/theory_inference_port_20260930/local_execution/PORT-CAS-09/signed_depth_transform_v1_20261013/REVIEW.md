# P09-A — independent review (signed depth transform)

Reviewer: fresh-context, read-only subagent. Requested runtime gpt-6-astra/ultra (unavailable); observed runtime claude-opus-5-5. The reviewer is not the author.

**Verdict: PASS_WITH_NOTES (scoped). No blocking finding.**

## Faithfulness to the Python source

- **Source citations.** All seven source hashes in SOURCE_RECOVERY.md match the working tree, and every line citation was checked:
  - `depth_path.py:41-62` — H, T, restore
  - `typefree_depth.py:95` — h@c@h.T
  - `r9_depth_law.py:79-95`
  - `CAS_CONTRACT.json:111-114`
  - `PORT_MAP.json:48-60`
  - THEORY_EXTENSION D1/D3
- **H, T and restore.**
  - Contrast `x_{j+1} − K_j x_j` and the anchored T match the Python.
  - The entry lemmas match the block layout.
  - T is block lower triangular, has identity diagonal blocks, and det T = 1.
  - `restore` is the Python recursion (y0 = r0, y_{j+1} = r_{j+1} + K_j y_j). It is a two-sided inverse for every d, including d = 0.
  - Probe: `Rmat K *ᵥ r = restore K r` holds definitionally.

## Moments and law

- **Covariance.** `covMat` covers all ordered pairs (`rfl`), and `HCHt_apply` keeps all four cross terms.
- **Premises.** Only Integrable / MemLp 2 under a finite or probability measure. There is no independence hypothesis.
- **Law.** Stated as `Measure.map` with only AEMeasurable. The contrast law depends only on the full joint law.

## Negative control

- The full covariance gives HCHᵀ = 0.
- The block-diagonal part (`= 1`, three independent unit variables) gives 2 and −1 instead.
- So dropping the cross blocks changes the covariance, and the −1 entry also refutes automatic contrast independence.

## Numerical cross-check against the live depth_path.py

- 300 random cases (depth 0–4, rectangular K, every third case rank-deficient) agree to a maximum absolute error of 5.7e−14.
- Depth 0 is handled: T = I and H has shape (0, d0).
- A Student-t Monte Carlo with full cross covariance gives Cov(Hx) to 2.8e−3 relative error.

## Lean checks

- No circularity.
- Hashes match AUTHOR_RETURN.
- Failed compiles 01 and 02 are kept; 03, 04 and 05 exit 0.
- All 46 theorems plus the extra definitions use only the axioms propext, Classical.choice and Quot.sound. No sorry.
- Independent rebuild: olean `b8a4843a…` is bit-identical, and the audit stdout is identical.

## Notes

- **N1.** Some premises are weaker than in the frozen targets (unused Fintype dropped; the copy identities have no premise). The premise-free copy identities partly rely on Mathlib junk values; they mean variance only under MemLp 2.
- **N2.** Under IsFiniteMeasure, `cov` is unnormalised; the identity still holds by bilinearity.
- **N3.** Zero-size blocks are allowed (more general than the Python, and harmless).
- **N4.** `Rmat = restore` is not a named lemma.
- **N5.** The SymPy and Sage+Singular tool tasks were not run.

## Not proved

- Random, fitted or ω-dependent transport.
- Contrast independence (refuted).
- Rank and kernel of H (D3).
- PSD of V.
- Gaussian law, χ², support or pseudoinverse (D2).
- Software view policy and scenario gating.
- Any time interpretation of the block index.
- Full PORT-CAS-09.
- Scientific admission (HOLD).
