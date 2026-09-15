# R9 review binding diagnosis — 2026-09-15

**Disposition: cause established; authenticated same-review closeout is blocked
under the current official path. No child was spawned or resumed.** This is
Host execution-identity diagnosis, not new scientific verification.

## Source and version

Repo cosmosapjw-quantum/htt_base, branch implementation/project-catalog-20260912.
User base e71b3375789460b6abf5c72bbc52b95801fa894d has the exact requested tree
644102d93326c71ecb7230c6b62755eeef2af518. Current diagnostic base is its direct
successor 8887b4ebb66058f508f7d1edd63caf0ec60cba46. Its D3 matrix/kernel proofs
are preserved, not attributed to this identity repair.

The current configured authority, hook commands and source events all identify
3379cc219ed6b5e44a2b50d7224324a89fdf77ab. Actual Start/Stop hook messages and
Pre/PostToolUse event records show that hooks executed in this client session.
A separate reload ceremony remains unverified; saved approvals are not used to
claim a valid child lifecycle. No policy, approval or registration was changed.

## Actual event chain

| UTC time / source | Observed fact |
|---|---|
| 06:24:22.743, parent transcript line 3995 | Spawn call call_aHoKbTLPpMup0jkd50hgmSv0 requests depth_mathlib_review, Terra/high, fork none. The lifecycle launch claim has this exact call ID and parent session. |
| 06:24:22.966, child transcript line 1 | Child UUID 01a0a3bc-edad-78d3-90b9-8d2322b416ed names parent 01a0987d-8380-72a1-a10b-fef9d0c9d3c2 and agent path /root/depth_mathlib_review. |
| 06:24:23.351, parent line 3998 | Tool response supplies that task path; it does not itself create a lifecycle binding. |
| Child turn-context line 8 | Actual model/effort match Terra/high, but cwd is /home/cosmosapjw/Dropbox/bianchi/htt_base. Registered cwd is /mnt/sn850x2t/htt_base_e2e/PROJECT-CATALOG-20260912/worktree. |
| 06:24:26.991, child line 9 | Start hook returns CHILD_CWD_MISMATCH and says execution is unverified. |
| 06:29:06.264, child line 137 | Stop hook returns CHILD_BINDING_MISSING. |
| 06:29:09.383, child line 145 | Native task_complete records duration_ms=286233. |

The official code validates actual child cwd in
`src/cuhg/codex_hooks/child_lifecycle.py` `_validate_event_identity` before
`bind_child` stores a child. That mismatch prevented binding. `child_exit` then
raises CHILD_BINDING_MISSING when no bound child exists. The raw child continued
to produce review artifacts after the advisory Start error; that explains why
files and successful recompilations coexist with the final hook rejection.
A subprocess run with the correct cwd does not change the child's turn cwd.

The two assignment hashes are **not a drift failure**. The repo seal d6352dd5…
hashes the canonical assignment payload with its seal excluded. The global
freeze sha256:e071cd1c… hashes the complete file bytes. Both match their respective
current calculations, the result seal and all six required source hashes.
`evidence.json` contains the exact full values and filtered source-event excerpts.
No hidden reasoning, account balances or unrelated conversation bodies are
included in this diagnostic package.

## Budget and official recovery

| Constraint | Evidence / disposition |
|---|---|
| Original review count | One permitted review was used. The prior terminal result remains STOP_BUDGET; this was review-round exhaustion, not a measured 1200-second timeout. |
| Same-issue closeout | Original contract recorded limit 1, used 0. This is not an existing continuation reservation. |
| Cumulative native task wall time | One observed child turn, 286.233 seconds. Arithmetic difference from 1200 is 913.767 seconds. Do not add nested compiler time again or treat this difference as spendable authority. |
| Report self timestamps | The report says 15:21–15:27:33 KST, starting before the actual native spawn. These self-declared times are not used for budget calculation. |
| Existing agent | Current agent inventory lists it completed. Resume eligibility is not established by its presence. |
| Official continuation context | null in the registered launch; no bound child or MATCH runtime observation. |
| Official command | native_workspace_job.py plan-continuation --run-dir /mnt/sn850x2t/htt_base_e2e/R9-DEPTH-MATHLIB-20260914 exits 2: WORKSPACE_JOB_UNAVAILABLE, Cannot read workspace_job.json. |

`official_continuation_probe.json` preserves the exact argv, output and exit.
The official planner requires an attributable closed candidate/review and measured
usage in its existing job before reserving a continuation. No job was prepared
retrospectively, no old budget reset, and no followup was attempted after this
failure. `global_hook.py` exposes registration only, not a historical rebind
command. The guarded binding API is an internal event handler; it was not used
to manufacture/replay Start or Stop events.

There are also independent obstacles to current authenticated replay: the launch
froze sandbox=null, which cannot satisfy the current non-null sandbox comparison,
and it froze HEAD 9ca515ad, while preserved later work has moved HEAD to 8887b4eb.
The official identity validator compares current Git identity too. Resetting the
checkout or editing the frozen registration to avoid these checks is outside
scope and was not done. The observed original cwd mismatch cannot be erased by
a correct future run.

## MLflow session analysis

The required skill's schema inspection found compiler operation spans, not chat
session traces. Searching the existing experiment for the actual child UUID in
metadata.mlflow.trace.session returned zero rows. The selected trace contains
compiler argv/cwd/source hash and output, with no child-session metadata.
These records support compilation only. `mlflow_session_analysis.json` records
this actual readback; no new trace, compiler run or synthetic experiment was made.

## Minimum next action and claim boundaries

A separate, explicitly authorized global harness/client maintenance scope is
needed to establish a supported same-task closeout path with original usage and
failures retained. It must launch from the actual registered worktree, freeze
the sandbox, and supply a valid existing-task continuation reservation. Current
policy cannot certify the mismatched historical execution retroactively. Any
proposal for a genuinely new review or changed budget must be explicit owner
work, not a renamed reset of this review. No such change is requested or performed
implicitly by this report.

Original launch_id:null, self_declared result, hook errors, STOP_BUDGET, NON_PASS,
fail findings and raw compiler/reviewer files remain unchanged. Raw parent-child
correspondence is now established; **authenticated review admission remains
UNVERIFIED/BLOCKED**. D1 general covariance/PSD/cross terms and D3 inverses retain
LEAN_CHECKED_GENERAL. The later 8887b4eb determinant/kernel bridge also remains
compiled; this diagnosis did not prove it. Complete D3 law/support, D2/D4 and
four-axis admission remain open, and the old fail is not a counterexample to
passed helpers. MQ1/MQ2, all science HOLDs, quarantine and alpha allocations remain.

This task stops after diagnostic delivery. The next mathematical handoff is the
remaining full-law/support/moment connection for the already flattened D3 map;
do not repeat the determinant/kernel work or begin the sixteen bundles before
FORMAL_DEPTH is released.

## Delivery validation

Host diff/preservation checks and canonical DAG validation passed; 206 PRs remain
in the valid DAG and status semantics are unchanged. The first line-hash check
incorrectly stripped terminating newlines; `delivery_validation_initial.json`
preserves that failure. Exact JSONL record bytes, including newline, match every
stored digest in the corrected `delivery_validation.json`. No source or evidence
hash was changed, and no scientific execution was repeated. This was Host
self-review only, not an authenticated independent review.
