# D1–D4 actual four-axis attempt and scope adjudication

Host disposition: **FORMAL_DEPTH BLOCKED; no D1–D4 full proposition admitted.**
All four engines actually executed each current contract, in order D1, D3, D2,
D4. This completes the bounded verification attempt, not the required proofs.
The direct derivations in `THEORY_EXTENSION.md` at bc5e028d remain prior work.

`host_execution.json` preserves the exact `cas_gate.py run-adjudicate` commands,
exit codes and elapsed times. Each `adjudication_D*.json` is the unmodified gate
output; `host_execution/<proposition>/<axis>/` retains actual engine stdout,
stderr, exit and source identity. Every `solver_executed` flag is true and no axis
timed out. The four aggregate results are **CAS_FAIL**, with exit 2. Wolfram,
SymPy and Sage each report FAIL; Lean reports MISALIGNED_ASSUMPTIONS. These raw
labels are not changed to CAS_BLOCKED. The separate Host admission is BLOCKED
because full obligations remain unproved; no mathematical counterexample was
reported. The boolean gate has no unknown obligation value, so the authors
correctly left unmet obligations false. SymPy deliberately exits 1 after emitting
those false flags; its final algebra assertions did not fail.

## What each axis actually established

| Axis and actual version | Checked scope | Missing full obligations |
|---|---|---|
| Wolfram Engine 15.0.0; xTensor 1.3.0 / xPerm 1.2.4 loaded in a separate one-shot probe | Exact rational rectangular block fixture d=(2,3,1), singular covariance and finite transformed identities | Universal finite block/second-moment argument, real PSD pullback proof, Gaussian support/chi-square and full-past conditional-law proofs. xAct loading alone adds no theorem evidence. |
| SymPy 1.14.0 | Compatible symbolic one-step covariance expansion; two-step block inverse algebra; diagonal whitening algebra; nonsingular innovation cross-covariance cancellation | Quantification over arbitrary depth, complete PSD/support and Gaussian probability arguments. |
| Sage 10.9 with `/usr/bin/Singular` 4.3.2 | Repaired runner checks actual proposition-specific polynomial residuals modulo the zero ideal, with nonzero negative control; finite scalar identities | General rectangular block induction and real PSD/probability results. The original zero modulo unit-ideal calculation is not accepted as validation. |
| Repo-pinned Lean 4.31.0 core | Both inverse compositions for homogeneous and time-varying homogeneous trajectories; residual-after-reconstruction for finite dependent heterogeneous blocks | Reverse dependent-block composition, real matrix covariance/PSD, determinant and full-law preservation. `import Mathlib` fails; singular Gaussian and conditional-law formalizations are absent. |

Lean's exact missing-library diagnostic is retained in
`.agent-harness/runs/R9-THEORY-20260914/artifacts/depth_lean/raw_logs/mathlib_probe.stdout`:
`unknown module prefix 'Mathlib'`. The compilation command and failed reverse
dependent-composition attempts are in that assignment's execution receipt and
raw logs. Core availability does not imply the probability library is configured.
The compiled abstract positivity helper is Int-valued and is not D1 real PSD.

## Proposition-level remaining work and R9-24

| Proposition | Direct derivation | Machine evidence now | Remaining obligation before full acceptance |
|---|---|---|---|
| D1 full HCHᵀ, cross-step blocks and PSD | Existing D1 | Symbolic/finite identities only | All compatible blocks and finite second moments; real quadratic pullback PSD theorem with no independence assumption. |
| D3 T(Y)=(Y0,HY) | Existing D3 | Compiled recursion helpers, including one heterogeneous composition | Reverse heterogeneous composition; real block specialization, kernel/surjectivity/determinant one; preservation of complete singular joint law/support and initial cross terms. |
| D2 singular Gaussian support | Existing D2 | Restricted diagonal/finite algebra only | Gaussian pushforward and affine support; spectral whitening to chi-square(rank V), deterministic rank zero, off-support rejection before pseudoinverse score. |
| D4 full-past innovation | Existing D4 | Restricted nonsingular cancellation only | PSD range consistency and singular Schur complement; conditional Gaussian on past support; independence from the whole past and joint independence of successive innovations. |

`OBLIGATIONS.md` and the four contracts are the exact assumption/consumer map.
R9-24 continues to require all of FORMAL_DEPTH. Existing adapter implementation
and tests do not grant DEPTH_METHOD. Data-fitted transports, selection or
covariance are outside these fixed-law theorems.

## Failures, repairs and independence

Original Wolfram parsing, SymPy normalization/structural block-comparison and
Lean elaboration failures are preserved alongside repaired sources. Sage's
vacuous Singular reduction was replaced in a separate repaired runner; actual
residual reductions and the nonzero control were executed in all four final
Host runs. No target, mathematical tolerance, contract or validator was relaxed.
The Sage author's original result file remains bound to the original source;
the repaired source is bound by the Host execution receipts, not retroactively
by that original envelope.

Five tasks were registered before dispatch, with separate blinded axis slices
and an independent moving-q review. The four axes did not inspect sibling
derivations before submission. Engine diversity and source independence do not
establish authenticated model/lifecycle identity. Current hook lifecycle remains
UNVERIFIED; local-model dispatch count is zero.

Strict result-envelope validation found that the Wolfram and Sage authors wrote
axis summaries instead of the required registered result schema. Their originals
and exact validation errors are preserved in `result_validation.json`; they are
not accepted as valid registered result envelopes. SymPy and Lean envelopes
validate. The separate moving-q review belongs to the following theory increment. This packaging failure
does not erase directly observed engine executions, but it precludes a whole-run
harness PASS. No additional dispatch or policy/schema relaxation is used to
relabel the run. Admission and scientific/novelty HOLDs remain unchanged.

Next single formal task: finish the reverse heterogeneous-block reconstruction
composition in the existing pinned Lean core source. It is a finite algebraic
obligation that does not require new observation data or the missing Gaussian
library. Completing it alone will still not admit D3 or FORMAL_DEPTH.
