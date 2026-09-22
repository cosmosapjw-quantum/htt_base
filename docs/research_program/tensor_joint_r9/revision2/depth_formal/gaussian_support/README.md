# D2 singular-Gaussian support bridge

Owner: HTT/common formal mathematics. Scope: the support component of the
unchanged `CAS_D2.json`, in the original primary checkout on `main` at base
`ce606eca7303b04fe64e55c08d1705564689bc7e`. Author/reviewer: Host Codex.
Transfer source: none. This is scoped formal evidence, not scientific admission,
an independent CAS axis submission, or completion of D2/FORMAL_DEPTH.

## Statement and derivation

`formal/R9Depth/GaussianSupport.lean` uses the actual pinned mathlib
`ProbabilityTheory.multivariateGaussian m C`. For any finite real Euclidean
space and specified symmetric PSD matrix C, it proves

`supp N(m,C) = {m + C u : u}`.

No invertibility, positive-definiteness, positive rank, or nonempty coordinate
index is assumed. A zero-dimensional space is permitted. Compatible feature
units and the full joint Gaussian law are premises; no observed law is inferred.

1. The one-dimensional standard Gaussian dominates Lebesgue measure in the
   absolute-continuity direction needed for positivity on every nonempty open
   set. Products and the Euclidean coordinate equivalence give full support to
   the standard Gaussian.
2. A continuous map with closed range maps full support exactly onto its range.
   Finite-dimensional affine linear ranges are closed, including singular ones.
3. The pinned construction is the pushforward by `x ↦ m + sqrt(C) x`.
   Self-adjointness and the Gram range identity prove `Im sqrt(C) = Im C`.
   The target support identity is not an assumption.
4. For any rectangular or singular real H, apply the same argument to
   `B = H sqrt(C)`. Since `B B* = H C Hᵀ` and `Im(B B*) = Im B`, the mapped
   support is `H m + Im(H C Hᵀ)`. The file also proves that this operator is the
   actual mapped covariance bilinear form. Gaussianity of the continuous linear
   pushforward uses mathlib's existing `IsGaussian` map instance.

`gaussian_eq_of_moments` connects an arbitrary Gaussian measure with its actual
specified mean and full covariance bilinear form to this concrete construction.
`mem_support_iff` gives the ordinary coordinate condition. The complement of the
affine support has measure zero. Zero covariance gives `dirac m`, with support
`{m}`; it does not replace an unknown covariance or mean by zero. Independent
standard coordinates occur only inside the mathematical Gaussian construction,
not as a replacement for missing physical correlations.

## Source and compilation

Pinned upstream source:
[mathlib Multivariate.lean](https://github.com/leanprover-community/mathlib4/blob/fabf563a7c95a166b8d7b6efca11c8b4dc9d911f/Mathlib/Probability/Distributions/Gaussian/Multivariate.lean).
Lean: `leanprover/lean4:v4.31.0`; mathlib:
`fabf563a7c95a166b8d7b6efca11c8b4dc9d911f`.
The existing shared cache is used without installation or package updates.

Run from the primary checkout with a fresh output path:

```bash
python3 -B docs/research_program/tensor_joint_r9/revision2/depth_formal/gaussian_support/compile.py --output /tmp/r9-d2-support-fresh
```

Final compilation: exit 0; all nine printed axiom dependencies are exactly
`propext`, `Classical.choice`, and `Quot.sound`, with no `sorryAx`.
`validation.json` confirms source/runner bindings and preserved state fields.
The bounded support work unit met its scoped acceptance; this is not D2 admission.

`final/execution.json` binds final source bytes, runner/helper, toolchain, actual
command, raw compiler output and axiom checks. `attempt*/` preserves the initial
API probes and all development compiler failures with their exact source copies;
failed compilations that print `sorryAx` are failures, never proof evidence.
The runner reuses the existing timeout/error capture helper without executing D3.
The canonical DAG was checked once: 207 cards, valid. No MES frozen replay,
completed D3 compilation, numerical product replay, full pytest suite, new child
review or four-axis execution was performed.

At the support compilation, the active local pointer named
`EXTERNAL-FUSION-FOLLOWUP-20260829`.
Its assignments concern unrelated external-fusion/report work. Historical R9
assignments cover D3 reverse composition or earlier D1/D3 review, not this D2
source. They were read and preserved, not rebound. The current user's D2
continuation supplies the Host scope. The observed routing opportunity returned
`NO_QUALIFIED_EXECUTOR` for Lean; the same opportunity records explicit PARENT
fallback. No local/native model was dispatched and no historical allowance reset.

## Remaining obligations and next action

The next single mathematical task is the supported pseudoinverse quadratic law:
derive positive-eigenspace whitening and prove `zᵀ V⁺ z ~ χ²(rank V)` under the
specified true Gaussian mean. Include the rank-zero deterministic branch and
enforce affine-support membership before using the score. This file proves no
chi-square distribution or pseudoinverse identity. It states the zero-rank
covariance case as `C=0`; a rank-function-to-zero-matrix interface is not added.

D4 full-past conditioning, range consistency, Schur-complement PSD and successive
innovation independence remain open. Current-contract four-axis evidence and
authenticated independent review remain required before FORMAL_DEPTH admission.
The existing R9 review usage, STOP_BUDGET/NON_PASS/CAS_FAIL and historical child
failures are unchanged. MES `CHILD_CONTINUATION_NOT_RESERVED` is separate and is
not a D2 mathematical prerequisite.

Physical source closure, target/source response and reference U_R/optical bridge
remain HOLD; empirical MES D remains `HOLD_NOT_COMPUTED`. Missing mean,
correlation and transfer remain unresolved. No production admission, target selection, observational coverage or alpha
spending follows from this local proof. The owner subsequently authorized
Codex-only continuation and publication on 2026-09-22; this is separate from
the historical MES approval.

## Subsequent Codex-only continuation, 2026-09-22

The owner approved official closure of the stale active pointer. Normal closure
failed its old context/input checks; `close_run.py --abandon` cleared the pointer
while preserving all 38 historical files and acceptance states. The new run is
`R9-D2-D4-CODEX-20260922`; no old assignment was rebound.

`codex_only_continuation.json` records the actual reserved Sol/high author in
an enforced workspace-write `codex exec` session. Native lifecycle registration
for the artifact subdirectory rejected its Git-root mismatch; the documented
CLI transport was used without fabricating a collaboration edge. The task
retains CODEX_ONLY/BUDGET_FIRST and made no local-model calls.

The first observed counter above the fixed 500000-token limit was 525425.
Host interrupted the process; final observed usage was 730883 tokens over
293.501 seconds, including cached input. No D2/D4 source candidate, compilation,
independent review or admission was returned. The suspended author and usage
were recorded by the official reconciliation command without a budget reset.
An owner-approved task-bound amendment is required for additional generation;
none is implied by the previous pointer approval. Raw runtime and failed
registration receipts remain under the existing ignored run directory.

Host differential review of the support source covered correctness, regressions,
validation coverage, claim boundaries and maintainability. No blocking defect
was found in the scoped support theorem. This is self-review, not independent
review or four-axis acceptance. The unchanged compiler evidence was verified
against source bytes; the original compile and MES/D3 runs were not repeated.
