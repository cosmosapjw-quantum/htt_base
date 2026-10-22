# G04-A — independent review (verbatim final report of a fresh read-only reviewer)

**Verdict: PASS_SCOPED. No blocking finding.**

Scope: flat Minkowski η in inertial coordinates, finite C^n with n ≥ 1, local, simple eigenvalue.

Reviewer: a fresh-context, read-only in-session subagent (subscription fallback). It reports itself as claude-opus-5-5; the requested model was gpt-6-astra/ultra.

## Checks
- **Source recovery.** Checked against ENERGYFRAME_THEOREMS EF1 (line 27), the conventions (line 7), the IFT assertion (line 91), and the CAS-04 assumptions and C01–C04 definitions, verbatim.
- **Freeze.** The freeze (11:22:31Z) predates the first G04-A compile (11:39:17Z). The pre-freeze Sig.lean holds only `sorry` signature stubs. 22 of 22 frozen statements appear verbatim.
- **Numerical cross-check.** mpmath at 50 digits on a random quadratic symmetric T:
  - frame orthonormality error 9e−51;
  - hproj residual 7e−31;
  - budget Q matches c²ΣD²/(ε+p_i)² to 4e−31, and stays within the δ bound;
  - accel = c²η(e_i, ∂_u u).
- **Negative controls** (reviewer, in Lean):
  - ε + p = 0 breaks the gap.
  - T = 0 has non-unique future unit eigenvectors.
- **No conclusion assumed.** SmoothEnergyFrame is exactly E1's output. hproj is derived. Existence and smoothness come from the IFT. In C04, w = u and ε + p ≠ 0 are derived.
- **Non-vacuity.** A constant fluid fires both composites, including the conservation premise.
- **Integrity.** All sha256 values match AUTHOR_RETURN. All five receipts exit 0. Axioms are propext, Classical.choice and Quot.sound only (49/49). No forbidden tokens.
- **Independent recompile.** Exit 0. G04AEigenline.olean is bit-identical (0070b848…). Proof.olean depends on the source path.

## Mathematical verification
- **E0.** L is invertible on u⊥ iff ε + p_i ≠ 0 for all i, for any orthonormal rest eigenbasis.
- **E1.** The bordered IFT derivative (w, m) ↦ (Tw + ε0 w − m u0, 2η(u0, w)) was checked by hand.
  - Injectivity follows from normalization, self-adjointness and the gap.
  - Persistence uses fderiv continuity and openness of the invertible maps.
  - Future orientation persists by continuity.
- **E1u.** Pointwise uniqueness: the rest space is PSD, self-adjointness and the gap apply, and normalization gives η(u,v) = −1.
- **E2.** The path bridge x + (r sin s)X stays in V for all s, and the rescaling by c/r is sound.
- **E3.** Proof.lean's hproj (gap ε + p_i, q = rateArr, d = sourceArr) is derived from E2 by pairing with e_i.
- **E4.**
  - minGap = min|ε + p_i| > 0.
  - Equality-support is preserved componentwise.
  - The Euler step gives c²∇_u u = −c² h∇p/(ε+p).

## Notes
1. Flat-metric scope. The curved EF1 version is not proved; do not cite this as curved EF1.
2. The post-freeze composites were documented only in AUTHOR_RETURN. Resolved by AMENDMENTS.md.
3. The barotropic and dust parts of C04 are not lifted to the actual fields; only Euler is.
4. The fluid hypotheses are required on all of S. Harmless.
5. Scratch iterations were not kept as receipts.
6. Proof.olean is path-dependent.
7. The Wolfram, SymPy and Sage axes were not run.

## Not proved
- The curved covariant version.
- Global continuation or a uniform radius.
- The degenerate eigenvalue case.
- A smoothly diagonalizing rest basis.
- C^∞ or analytic regularity.
- Barotropic and dust C04 at the actual fields.
- Four-axis acceptance.
- Scientific admission (HOLD).

