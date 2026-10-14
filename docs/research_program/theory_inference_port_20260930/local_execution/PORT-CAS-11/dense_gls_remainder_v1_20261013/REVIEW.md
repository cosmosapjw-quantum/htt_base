# P11-A — independent review (dense GLS and deterministic remainder)

Reviewer: fresh-context read-only subagent. Requested runtime gpt-6-astra/ultra was unavailable; observed runtime was claude-opus-5-5. The reviewer is not the author.

**Verdict: PASS_WITH_NOTES. No blocking finding.**

## Checks

- **Sources and ownership.** Checked against the card and CAS_CONTRACT CAS-11 (sha256 904d95fe…). PORT_MAP indeed has no PORT-CAS-11 entry. The owning code is `htt/htt/htt/infer/endpoint_cosmography.py:257`, which computes `bias_bound = np.abs(influence) @ bounds`.
- **R0/R1 (estimator properties).**
  - Rank k gives injectivity, and the Gram matrix XᵀC⁻¹X is positive definite.
  - MX = 1 and the normal equations hold.
  - The exact split `wrss_split` gives the unique minimizer.
  - No ridge or jitter term is used.
- **R1g.** The link to G08A Moore–Penrose holds for any whitening W.
- **R2.** MCMᵀ = (XᵀC⁻¹X)⁻¹ for a dense positive-definite C.
- **R3a (componentwise bound) matches the owning code numerically.** The real `fit_endpoint_cosmography` was run on a toy problem (N=60, dense SPD C, rank-13 design, cond ≈ 5e8):

  | Quantity | Max relative difference |
  |---|---|
  | coefficients | 1.4e−13 |
  | covariance | 3.7e−15 |
  | bias bound | 3.4e−15 |

  The bound is sharp: it is attained by r = b·sign(M_i·).
- **R3b/R3c (norm corollaries).** The ℓ∞ (max row sum) and ℓ2 operator-norm corollaries are correctly stated.
- **R3d/R3e (remainder split).** Exact.
- **R4 (rank-deficiency control).** Rank < k gives det(gram) = 0 and no left inverse. The concrete control Xbad is genuine.
- **R5a/R5b (actual law).**
  - At this pin, `multivariateGaussian` is the standard Gaussian pushed forward through CFC.sqrt.
  - The map identity is proved through `IsGaussian.ext` (characteristic functions) for positive-semidefinite C.
  - R5b gives My ~ N(θ + Mr, (XᵀC⁻¹X)⁻¹).
  - A Monte Carlo check (2e5 samples) agrees.
- **R6.** The rank-13 instance is non-vacuous.
- **No circularity.**
- **Hashes and receipts.** All hashes match AUTHOR_RETURN, and compile steps 01–03 exit 0.
- **StatementCheck quarantine.** `raw/StatementCheck.lean` contains `sorry` bodies but is quarantined:
  - it lives in its own namespace;
  - it was compiled without `-o`, so it produced no olean;
  - nothing imports it.
- **Axioms.** All 23 audited declarations, plus 11 extra helpers, use only propext, Classical.choice and Quot.sound.
- **Independent rebuild.** The rebuilt olean `200fab11…` is bit-identical, and the audit stdout is byte-identical.

## Notes

- **N1.** W is a hypothesis in R1g, so "gls_minimum applies" is not proved inside this module. An optional corollary via `whitening_exists` would close this.
- **N2.** Confidence/remainder separation is delivered as the exact law plus the deterministic bound. There is no coverage or confidence-interval theorem.
- **N3.** "Fixed independent selection" and "known C" hold only semantically. X is a fixed parameter, and no estimator appears.
- **N4.** hβ in R3b is redundant.
- **N5.** The bit-for-bit G08A olean depends on the repo source path; the P11 olean does not.

## Not proved

- Coverage, confidence-interval, χ² or calibration statements.
- Estimated covariance Ĉ.
- Physical rank 13 of the design (G09-B).
- Floating-point equivalence of the Python Cholesky/SVD path (checked numerically only).
- Conditioning semantics.
- The SymPy, Sage and Wolfram axes.
- Full PORT-CAS-11.
- Scientific admission (HOLD).
