# G08-A — independent reviews

Both reviewers were fresh-context and read-only, with requested gpt-6-astra/ultra (unavailable) and observed claude-opus-5-5. The second reviewer did not write the corollaries.

## Review 1: G08AWhitening.lean (author subagent) — PASS_WITH_NOTES, no blocking finding

- **Hashes and receipts.**
  - Source sha256 `e62280213d23063cf4309aa8bdc814b2925f44f50cb81859f6b91bcb976bf045`; ProjectionBridge `440e3820…` unchanged.
  - compile_02 and compile_04 are disclosed development failures; compile_03/05/06/07 exit 0.
- **Axioms.** All 23 public declarations use only propext, Classical.choice, Quot.sound.
- **Construction is genuine, not declared.**
  - W = Uᵀ diag(1/√d) U, from Mathlib's eigenvector basis; d_i > 0 comes from PosDef; IsUnit has an explicit inverse.
  - X = (AᵀA)⁺Aᵀ with zero eigenvalues sent to 0. This is valid for every rank, including A = 0.
  - Non-vacuity probes: X = 0 is rejected for A = [1]; X = A is rejected and X = A/4 accepted for [[1,1],[1,1]].
- **Target-by-target.**
  - `residualProjector_eq`: proved equal to the bridge's actual `starProjection`.
  - `gls_minimum`: gives both the infimum and attainment for the genuine C⁻¹ quadratic.
  - `projector_spectrum`: legitimate decreasing order; ν = n − rank A.
- **Numerical probe** (n=6, k=4, rank-2 F): X matches `np.linalg.pinv` to 4e−16; projector identities hold to ≤ 3e−15; eigenvalues are {0,0,1,1,1,1}; min Q = r·r is attained.
- **Independent rebuild.** The ProjectionBridge olean is identical. The G08AWhitening olean reproduces `54406d4c…` from the repo path; the olean embeds the source path.
- **Notes.**
  - N1: annihilation and the rank formula were not named theorems. Resolved by `G08ACorollaries.lean` (Review 2).
  - N2: `hC` is unused in `gls_quadratic_eq`.
  - N3: olean hashes depend on the source path.
  - N4: same model family for author and reviewer.

## Review 2: G08ACorollaries.lean (lead) — PASS_WITH_NOTES, no blocking finding

- **Theorems.**
  - `residual_annihilates`: (1−AX)A = 0.
  - `residual_rank`: rank(1−AX) = n − rank A. The natural-number subtraction is safe: rank A ≤ n is proved, and the subtraction-free form also compiles.
  - `nu_eq`: rank(WF) = rank F for invertible W.
  - `whitened_residual_rank`.
- **Integrity.** The base file is unchanged. corollary_01 (exit 1, missing `open Matrix`) is kept; corollary_02/03 exit 0. Axioms are only propext, Classical.choice, Quot.sound. A full-chain independent rebuild gives a bit-identical corollary olean.
- **Notes.**
  - The C and whitening conjunct in `nu_eq` are unused, so the theorem is more general than stated.
  - The whitened annihilation (1−WFX)(WF) = 0 is a direct instance and is not separately named.
  - The docstring label should say C01.

## Not proved

- Gaussian law, χ², coverage.
- Four-way decision (G08-C).
- Estimated C.
- Minimizer-set characterization θ̂ + ker WF.
- Independence of P from the choice of W.
- Scientific admission (HOLD).
