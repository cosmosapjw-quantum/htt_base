# G10-A — independent review

Reviewer: fresh-context read-only subagent; requested gpt-6-astra/ultra (unavailable), observed claude-opus-5-5. The lead authored the wrapper; the reviewer did not.

**Verdict: PASS_SCOPED. No blocking finding.**

## Checks

- **Rest-space pairing.** `eDot u v` is the metric-free pairing uᵃvₐ (u contravariant, v covariant).
- **Covector norm.** `gDot` equals g⁻¹ = diag(−1,1,1,1) in the orthonormal frame, matching bᵀg⁻¹b.
- **Projection and invariant.** `b` is the rest projection hₐᵇ S_bc uᶜ; `Jgeo` matches C02.
- **Acceleration.** `A = 2c·b` matches COMMON_SPEC `A_cov = 2c B u` when S = B. For arbitrary symmetric S, A is the projected extension; this is a modelling definition, not derived physics.
- **Domain.** c > 0, g(u,u) = −1 and u⁰ > 0 are explicit and sufficient.
- **Rest-space theorems.** `rest_space_nonneg` and `rest_space_zero_iff` hold for every rest-space covector, not only A.
- **Negative controls.** Checked by hand and in Lean:
  - S = diag(1,0,0,0), u = (1/2,0,0,0) gives Jgeo = −3/16;
  - the superseded u = (2,0,0,0) gives 12 (explains the preserved exit-1 attempt);
  - u = v = (1,0,0,0) shows orthogonality is needed;
  - the ambient form is not positive.
- **On-shell sanity check.** The boosted point u = (5/4, 3/4, 0, 0) gives Jgeo ≥ 0.
- **No circularity.**
- **Hashes.** `Main.lean` equals the PR #489 blob `a9dc6a580e931c2ba383b14d8b7a2dcba281e2d0`. Wrapper sha256 matches compile_03.
- **Exit codes.** compile_01/02/03/04 = 0/1/0/0; stderr empty; all receipt hashes match.
- **Axioms.** Only propext, Classical.choice, Quot.sound; no escape hatches.
- **Independent recompile.** Exit 0 in the scratchpad, including an extended audit.

## Notes

- **N1.** `Vec4` does not encode variance; `gDot` means g⁻¹ on covectors only in the orthonormal frame.
- **N2.** `acceleration_orthogonal` holds by construction, because A is defined through the rest projection. It is not a derivation of u·A = 0 from the normalization of U.
- **N3.** `0 < u.t` is redundant for the conclusions; it is kept for contract fidelity.

## Not proved

- Smooth/covariant field version on a manifold.
- Identification of S with B_ab = ∇_(a U_b), including deriving B u ⊥ u.
- Physical geodesicity of a congruence.
- CAS-10 C01, C03 and C04 consequences.
- Scientific admission (HOLD).
