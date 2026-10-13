# G11-B — independent review (verbatim final report of a fresh read-only reviewer)

**Verdict: PASS_WITH_NOTES (scoped). No blocking finding.** Reviewer: a fresh-context, read-only in-session subagent running under the subscription fallback. Its model is claude-opus-5-5, self-reported. The requested gpt-6-astra/ultra was not used.

## Checks
- **Sources.** Hashes verified for the supplement (A1)/(A2) at S:41-51, the proof at S:76-83, Paper I Eq. (14), the endpoint continuity statements in Papers I and II, and the CAS-11 segment reading.
- **Freeze.** The freeze (11:25:12Z) predates the first compile (11:28:47Z). All 15 statements are byte-equal to the frozen ones.
- **B0 (Taylor remainder).** Derived by hand and confirmed in sympy for MB/BE/FD. The mpmath residual is ≤ 1e-50.
- **B1.**
  - The constant 1/2 is sharp (ratio → 1).
  - The endpoint case is reached by a t→1⁻ limit, not by a separate convexity argument. Endpoint limits converge for MB, BE and FD at a=0, and for FD at a=1.
  - A 3000-point sweep gives a margin ≥ 0.
  - The envelope is only required on the open domain, which is a weaker hypothesis.
- **B3.** The endpoint premises are proved. Lower semicontinuity comes from Fatou. No domination premise is needed.
- **B2.**
  - The pointwise bound passes to lintegral by `lintegral_mono_ae`.
  - The Bochner form goes through the domain-guarded `finite_budget_stat`.
  - hε0 is needed and consistent with the source.
- **Domain.** W > 0 exactly as in (A2). The reference g lies in the open domain, f in the closed domain.
- **Negative controls** (reviewer, in Lean):
  - A violated envelope falsifies the conclusion.
  - A boundary reference gives the junk value −1 and falsifies it.
  - FD a=1 is a valid instance.
- **Non-vacuity.** Shown by `B2_integral_instance` and `B3_instance`.
- **Hashes and exit codes.** All hashes match. compile_01 exited 1 and is kept (proof-only diff); 02 and 03 exited 0.
- **Axioms.** Only propext, Classical.choice, Quot.sound, across 20 declarations plus 6 reviewer controls.
- **Independent rebuild.** The G11-B olean is byte-identical. G11AIntegralBregman differs only by its embedded source path.

## Notes
- N1: The closed-segment envelope is harmless on {f = g}.
- N2: W > 0 is kept for fidelity to the source.
- N3: The B3 integral route is a supplement. The source endpoint statement is delivered by B2.
- N4: The freeze is anchored by mtimes; committing anchors it.
- N5: Tool axes — Wolfram NOT_EXECUTED (it is not PASS); SymPy covered by the author's and reviewer's checks; Sage NOT_NEEDED.
- N6: B2_nu has no separate instance on a nonzero nu C.
- N7: The linter warnings come from the imported G11-A.

## Not proved
- Certified ε.
- (A3)–(A6).
- A boundary reference.
- W = 0 or W = ∞.
- L²(W dν) integrability of kernels.
- The Wolfram axis.
- Scientific admission (HOLD).

