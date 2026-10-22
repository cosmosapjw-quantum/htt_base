# G02-B — independent review (verbatim final report of a fresh read-only reviewer)

**Verdict: PASS_WITH_NOTES (scoped Lean pass). No blocking finding.**

Reviewer: fresh-context, read-only in-session subagent (subscription), self-reported as claude-opus-5-5.

## Checks

- **Card and source identity.**
  - The card and zip hashes match.
  - Source hashes match for CAS-02.json, OPTICAL_THEOREMS.md and COMMON_SPEC.md.
  - Contract quotes are verbatim (C03 1+tanh², projection and regularity tracked separately, eqs (22)/(23), STAB-R0/AMPLITUDE/OFFSHELL).
  - Source line numbers check out, except one drift noted below (N3).
- **Freeze.** The freeze (11:45:12Z) predates the first proof compile (11:48:30Z). All 43 frozen signatures match the Lean file; the only difference is an explicit-binder variant with the same meaning.
- **T1 (operator norm).**
  - The actual Fréchet derivative of `future` is emb∘chartJac.
  - ‖Du‖ = √lamMax(d) for every d, including d = 0.
  - lamMax is proved to be the attained maximum eigenvalue.
  - Probes: `fderiv_future`, and ‖fderiv future 0‖ = 1.
  - SVD cross-check agrees to ≤ 4.4e−16.
- **T2 (rapidity bound).**
  - 0 ≤ R is derived, not assumed.
  - The bound is sharp on ‖d‖ = sinh χ.
  - Monotonicity holds on [0,∞), and R = 0 is covered.
  - mpmath agrees to 2.7e−51 over R ∈ {0, …, 20}; 20,000 random points gave 0 violations.
- **T3 (ball projection).** The radial metric projection satisfies the variational inequality, the nearest-point property and nonexpansiveness (constant 1). R = 0 is covered. 20,000 random points gave 0 violations.
- **T4 (Lipschitz bounds).**
  - Mathlib's mean-value theorem is applied on the convex ball, using the actual derivative.
  - These give eq (22), √(1+tanh²R)·η_d, and eq (23), with monopole cosh χ.
  - Cauchy–Schwarz is used only with Euclidean norms.
  - The Lipschitz ratio is about 1.000 numerically.
- **T5 (link to C04).**
  - CAS_02_C04 is applied with the second ball hypothesis derived from `ballProj_norm_le`.
  - The constants are explicit: M = √cosh 2R, regularity √(1+tanh²R), projection constant 1, and min(‖S‖, ‖S*‖).
  - The explicit-εH variant matches source line 180.
- **Negative controls.** Genuine but weak at R = 0 (see N1). The reviewer added an R = 1 witness in Lean.
- **Non-circularity.** No hypothesis assumes a conclusion, and physical admissibility is never asserted.
- **Integrity.**
  - All hashes match.
  - Imports are verified: Cas02 9922d424 = HEAD blob; InverseBound c5ea92df = pr/498@c0365da5 blob.
  - compile_03 exit 1 is kept; every other receipt exits 0.
  - 52/52 theorems use only the axioms propext, Classical.choice and Quot.sound, with no forbidden tokens.
- **Independent recompile.** Exit 0. The InverseBound olean is byte-identical. Cas02/G02B oleans built from scratch paths differ only because of the embedded path; rebuilding from the original paths reproduces them byte-for-byte.

## Notes

- **N1.** The R = 0 negative control is degenerate. Suggested stronger controls: the off-ball slope at R = 1 (0.980 > tanh 1), and the unclipped error 1.0824 > 1 without the projection.
- **N2.** The card's wolfram, sympy and sage tool tasks were not run. This is a scoped Lean pass only.
- **N3.** SOURCE_RECOVERY cites "lines 158-159"; the correct reference is line 162.
- **N4.** Freeze timing rests on file mtimes only.
- **N5.** Lipschitz-constant sharpness on the whole ball is not proved.
- **N6.** Building S* from eq (8), and STAB-AMPLITUDE, are outside this module.
- **N7.** One deprecation warning and some linter warnings.

## Not proved

- Physical admissibility or exact-image membership of the clipped output (STAB-OFFSHELL).
- Sharpness of the C04 constant.
- Amplitude-independent stability.
- Building S* from supplied coefficients.
- Calibration of η and εH.
- The CAS tool axes.
- Scientific admission (HOLD).

