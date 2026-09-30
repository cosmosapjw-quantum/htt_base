# CAS11-C02: finite Gram implication proved

Owner: HTT research / Host Codex. Scope: the frozen finite-dimensional mathematical component CAS11-C02 only. Contract SHA-256: `c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a`.

The observed frozen-runner result is **CAS_4AXIS_PASS** (2026-09-30 13:09:12 UTC), with no exceptions, missing axes, assumption differences or counterexamples. See [ADJUDICATION.json](ADJUDICATION.json), [RUN_RESULT.json](RUN_RESULT.json) and [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json). All sealed source bytes were unchanged during execution.

For every positive finite dimension, real symmetric positive-semidefinite matrix R, real vector e and epsilon >= 0, the hypothesis `(a.e)^2 <= 2 epsilon (a.R.a)` for every real vector a implies `e in range(R)` and `e.Rdagger.e <= 2 epsilon`, where Rdagger is the spectral Moore-Penrose inverse. PSD is an assumption, not a newly established physical property.

In an orthonormal eigenbasis, testing zero-eigenvalue directions forces e to have zero null-space coordinates. Set x = Rdagger e; then Rx=e and q=e.Rdagger.e=x.e=x.R.x >= 0. Applying the premise at x yields q^2 <= 2 epsilon q. If q=0 the conclusion follows directly; otherwise division by positive q gives the bound. This covers every finite rank, R=0 and epsilon=0 without inverting a singular matrix or dividing by zero.

| Axis | Observed result and proof coverage |
| --- | --- |
| Wolfram Engine + xAct | PASS. Wolfram 15.0, xTensor 1.3.0 and xPerm 1.2.4 loaded. Ten exact quantified scalar certificates plus an explicit arbitrary-dimension spectral/finite-sum proof. xAct loading is recorded; no tensor theorem is attributed to it. [Proof](../wolfram_xact/completion/PROOF.md). |
| SymPy | PASS. SymPy 1.14.0; universal analytic proof, exact symbolic identities, 76 checks including boundary cases and negative controls. A supplementary 220-digit ill-conditioned singular fixture has maximum error 8.75e-104 under 1e-70. Numerical fixtures do not establish universality. [Proof](../sympy/completion/PROOF.md). |
| SageMath + Singular | PASS. SageMath 10.9 and actual standalone Singular version 4330; 14 polynomial certificates checked by both engines and two positive-cone witnesses, with an arbitrary-dimension analytic proof. The preflight also observes Sage's bundled Singular 44100; these are distinct executables, not conflicting theorem assumptions. [Proof](../sage_singular/completion/proof.md). |
| Lean + mathlib | PASS. Entire quantified theorem `CAS11C02.finiteGramForward` compiled using pinned Lean 4.31.0 and mathlib `fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`. Axioms: propext, Classical.choice, Quot.sound; no sorry/admit/custom axiom. [Source](../lean/FiniteGram.lean). |

The first three axes use standard spectral-theorem and finite-sum/order arguments in their written proofs, checked at their algebraic obligations by actual engines. They are not complete theorem-kernel formalizations. Lean supplies the complete formal proof. The independent contexts used one neutral contract and did not read sibling proofs before adjudication. Author identities and retained earlier attempts are in [CONTINUATION.json](CONTINUATION.json). Total historical token/cost usage remains NOT_MEASURED.

Reproduce from the repository root with the exact argv in [COMMAND.json](COMMAND.json). [RUN_SPEC.json](RUN_SPEC.json) invokes the unchanged frozen runner through [record_axis.py](record_axis.py), which only records and forwards each actual subprocess output/exit status. Full observed logs are under `observed/`; engine-specific raw logs and earlier failed attempts remain in each axis directory. Local toolchain paths are recorded; another machine must supply those dependencies.

Independent read-only Astra/ultra review: **PASS**, no mathematical or report blockers. The reviewer checked all 15 integration source seals, seven contract inputs and 87 source/log/payload consistency comparisons. See [REVIEW.md](REVIEW.md) and [observed runtime](REVIEW_RUNTIME.json). Host accepts that scoped result; no repair was required. The review covers the finite proof and Host integration, without contributor lifecycle or scientific admission.

Additional checks: the 213-node DAG validates; staged Python syntax and JSON parse pass. Authored-file whitespace checks pass. The full diff whitespace check flags only 22 original trailing-whitespace lines in two raw Singular version banners; those engine-output bytes are intentionally preserved.

This result closes the contracted finite Gram implication only. It does not close CAS11-C01/C03/C04, establish physical residual construction or continuum bounds, admit the parent research claim, or identify a Bianchi family. Transfer-dependent results and other scientific HOLD states remain unchanged. Runner CAS eligibility is not overall scientific admission. Sky/null/covariance/transfer inputs are not applicable to this finite algebra theorem; there is no observational or statistical result here.
