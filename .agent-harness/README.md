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
rejected before the assignment file is written.

Paste the header printed by `new_assignment.py` at the start of the subagent spawn prompt. The assignment JSON supplies the unique result path.

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
