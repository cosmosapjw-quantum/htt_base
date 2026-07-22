# Shared-context subagent harness

This harness does not make separate subagents share a hidden model state or free KV cache. It replaces that unavailable assumption with a deterministic, versioned context contract:

1. durable policy in `AGENTS.md`;
2. compact Tier-0 context in `context/`;
3. a generated context pack injected by `SubagentStart`;
4. registered assignment slices;
5. sibling-result isolation for blind cross-validation;
6. machine-readable result envelopes and deduplication.

## Install

1. Merge `AGENTS.md.fragment` into the repository root `AGENTS.md`.
2. Merge `.codex/config.toml` into the existing project config.
3. Copy `.codex/hooks/`, `.codex/agents/`, `.agents/skills/`, and `.agent-harness/` into the repo.
4. Start Codex in the trusted repository and run `/hooks`; review and trust the project hooks.
5. Edit the shared context templates.

## Cost defaults (PR-124 preflight)

- New generic assignments default to `fork_turns=none`; forking the full
  parent history requires an explicit, recorded justification.
- Context is delivered exactly once: the `SubagentStart` hook injects the
  pack (`context_delivery_mode=hook_injected`). Agents must NOT re-read
  `CONTEXT_PACK.md` unless the injection reported `truncated`, in which case
  a single file fallback is performed and recorded.
- The spawn budget is cumulative per `work_unit_id` (normally the PR id),
  not per run — creating a new run does not reset it.
- Run directories are not committed; see `runs/RETENTION.md`.
- The active-run pointer lives at ignored local path
  `.agent-harness/runtime/ACTIVE_RUN`; a clean clone intentionally has no
  active run.

## Start a run

```bash
python3 .agent-harness/scripts/build_context_pack.py
python3 .agent-harness/scripts/init_run.py \
  --work-unit PR-124 \
  --spec-ref docs/specs/current.md \
  --base-ref main \
  --head-ref HEAD

python3 .agent-harness/scripts/new_assignment.py \
  --assignment-id A-WX \
  --agent-type cas_wolfram_xact \
  --independence-mode blind-results \
  --risk-tier R3 \
  --claim-id C-001 \
  --required-input .agent-harness/context/SHARED_CONTEXT.md \
  --allowed-tool wolframscript \
  --required-output 'axis result envelope (templates/CAS_AXIS_RESULT.json)' \
  --cas-axis wolfram_xact \
  --cas-contract .agent-harness/templates/CAS_CONTRACT.json \
  --task 'Verify C-001 with Wolfram Language and xAct under CAS-001.'

python3 .agent-harness/scripts/launch_receipt.py create \
  --assignment-id A-WX --requested-profile cas_wolfram_xact --attested
python3 .agent-harness/scripts/launch_receipt.py verify --assignment-id A-WX

python3 .agent-harness/scripts/validate_harness.py
```

Registration is fail-closed (audit H3): empty `claim_ids`,
`required_inputs`, `allowed_tools`, or `required_outputs`, an unknown
`agent_type`, or a CAS agent without `--cas-axis`/`--cas-contract` is
rejected before the assignment file is written. New assignments are sealed
with `assignment_sha256`, and every assigned claim ID must already exist in
the canonical `context/CLAIM_REGISTRY.jsonl`. Only claim identity is consumed
from that registry; a stored claim, novelty, or gate status is never treated
as current scientific authority. The seal is a deterministic drift checksum,
not a signature or proof of who wrote the assignment.

Paste the header printed by `new_assignment.py` at the start of the subagent spawn prompt. The assignment JSON supplies the unique result path.

## Strict result contract (MA-03)

New runs use `templates/RESULT_ENVELOPE.json` schema v2. Every assigned claim
must have exactly one typed terminal disposition:

- `findings_present` names one or more finding IDs;
- `examined_no_findings` explicitly records a completed review with no
  finding and requires nonempty evidence references plus an exact evidence
  fingerprint; or
- `not_examined` is allowed only for an `inconclusive` or `error` result.

The envelope also binds the assignment seal, canonical result path, launch
receipt when present, role and independence mode, declared reads, timestamps,
tools, commands, artifacts, findings, and reported errors. Artifact references
are accepted only after path confinement, blind-sibling authorization,
byte-count, and SHA-256 checks. Finding severity is one of `low`, `medium`,
`high`, or `critical`; finding and command fingerprints use the exact
`sha256:<64 lowercase hex>` form. Routine result JSON is capped at 64 KiB,
with larger raw evidence stored once through `evidence_store.py` and
referenced by its typed descriptor.

`SubagentStop`, `merge_results.py`, and `validate_harness.py` all call the same
file-level kernel in `scripts/strict_result_validation.py`. The repository has
no separate production "agent result replay" consumer: replaying a serialized
stop-hook event exercises the same hook and kernel. The hermetic
research-receipt replay utilities under
`scripts/codex_harness/` are a different evidence domain and are intentionally
not coupled to this result contract.

Current launch receipts and the agent-declared read/execution lists are
`self_declared`, not platform-authenticated. The legacy-looking `--attested`
flag means only that the caller asserts the requested local profile was loaded;
it does not create platform provenance. Missing receipts are recorded as
`unverified`, and a JSON field that promotes itself to
`platform_authenticated` is rejected until a platform-owned verifier exists.
Local receipt validation still binds the assigned/requested/actual profile,
installed config and sandbox, fork mode, and context-delivery mode.
Pre-MA-03 runs listed in `HISTORICAL_RUNS.json` are read-only schema-v1
inputs: validation does not rewrite or silently upgrade them, and result merge
refuses to regenerate their stored aggregate.

## Spawn prompt template

```text
RUN_ID=<run-id>
ASSIGNMENT_ID=<assignment-id>
CONTEXT_VERSION=<sha256>
INDEPENDENCE_MODE=shared-core|blind-results|adjudication

Execute only the registered assignment. The SubagentStart hook injects the canonical pack once — do not re-read CONTEXT_PACK.md unless the injection says it was truncated. Load the assignment file before analysis. Do not inspect sibling results unless the assignment permits it. Write the declared result artifact and end with HARNESS_RESULT.
```

## Finish

```bash
python3 .agent-harness/scripts/merge_results.py
python3 .agent-harness/scripts/validate_harness.py
python3 .agent-harness/scripts/close_run.py --run-id <RUN_ID>
```

Normal close validates the run, writes `RUN_SUMMARY.json`, and clears only
the local pointer. It never deletes the run directory. If a pointer is
invalid or dangling, inspect it first; explicit recovery is
`python3 .agent-harness/scripts/close_run.py --abandon`, which also leaves all
run data untouched.

The adjudicator should consume `MERGED_RESULTS.json` plus only the disputed
evidence needed for a targeted decision. Opposite verdicts on the same
`(claim_id, evidence_fingerprint)` are emitted as a `conflicts` object and
fail the merge — no majority vote. Resolved findings are recorded in
`.agent-harness/ledger/FINDING_LEDGER.jsonl` so later runs do not re-raise
them.

`MERGED_RESULTS.json.process_status` reports only envelope/merge integrity.
Its `claim_gate_status` is always `NOT_EVALUATED`; a zero merge exit code is
never a novelty, scientific-validity, or claim-acceptance decision.

## Four-axis CAS gate

```bash
python3 .agent-harness/scripts/cas_gate.py preflight --all
python3 .agent-harness/scripts/cas_gate.py check-axis --contract <C.json> --result <R.json>
python3 .agent-harness/scripts/cas_gate.py adjudicate --contract <C.json> --results R1.json R2.json R3.json R4.json
```

The four axes (Wolfram+xAct, SymPy, SageMath+Singular, Lean) are mandatory
and non-collapsible; `CAS_4AXIS_PASS` requires all four PASS under one
contract hash. Exceptions must be preregistered before any axis result is
read (`docs/audits/shared_context_cas_harness_final_audit_20260717/` §5).
