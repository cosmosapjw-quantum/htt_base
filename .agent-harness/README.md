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
- Context is delivered exactly once: the `SubagentStart` hook injects a
  validated, bounded view (`context_delivery_mode=hook_injected`). Pack drift,
  a missing active run, or total-budget overflow blocks the spawn; there is no
  full-pack fallback.
- The spawn budget is cumulative per `work_unit_id` (normally the PR id),
  not per run — creating a new run does not reset it.
- Run directories are not committed; see `runs/RETENTION.md`.
- The active-run pointer lives at ignored local path
  `.agent-harness/runtime/ACTIVE_RUN`; a clean clone intentionally has no
  active run.

## Authority and context scope

`AGENTS.md` is durable policy. `CONTEXT_INDEX.json` is the sole persistent
harness context configuration; its `shared_files` are the only inputs that
rotate the global context version and enter the generated view. Files under
`reference_only_files` matter only when a task explicitly names them.
`SHARED_CONTEXT.md` is a historical pointer, not a default conventions source.
Use the governing spec or scientific contract for the current work unit.

## Start a run

```bash
python3 .agent-harness/scripts/build_context_pack.py
python3 .agent-harness/scripts/init_run.py \
  --work-unit PR-247 \
  --change-set CS-PR247-PUBLICATION-INTEGRITY-P0 \
  --publication-group PG-PR247-PUBLICATION-INTEGRITY-P0 \
  --spec-ref docs/research_program/long_horizon_rescue/pr247_spec.yaml \
  --target-ref origin/research/pr04-multicomponent \
  --integration-policy \
    docs/research_program/long_horizon_rescue/pr247_publication_policy.json

python3 .agent-harness/scripts/new_assignment.py \
  --assignment-id A-WX \
  --agent-type cas_wolfram_xact \
  --workflow-role implementer \
  --independence-mode blind-results \
  --risk-tier R3 \
  --claim-id C-001 \
  --required-input docs/specs/current.md \
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

`init_run.py` never guesses `main`. If `--target-ref` is omitted, an existing
`origin/HEAD` must resolve to one remote-tracking branch. A schema-v2 run keeps
`work_unit_id`, canonical `change_set_id`, and canonical
`publication_group_id` separate. Implementer assignments are allowed only
while the candidate is mutable; reviewer/adjudicator assignments require one
exact frozen seal and a read-only reviewer profile.

Registration is fail-closed (audit H3): empty `claim_ids`,
`required_inputs`, `allowed_tools`, or `required_outputs`, an unknown
`agent_type`, or a CAS agent without `--cas-axis`/`--cas-contract` is
rejected before the assignment file is written. New assignments are sealed
with `assignment_sha256`. Long-lived claim IDs must already exist in the
canonical `context/CLAIM_REGISTRY.jsonl`; `RUN-*` IDs are reserved for
run-local review questions, must begin `RUN-<run_id>-`, and cannot be used to
promote a scientific claim or enter the cross-run finding ledger.
Only claim identity is consumed from the registry; a stored claim, novelty,
or gate status is never treated as current scientific authority. The seal is
an automatically generated same-run drift checksum, not a signature,
scientific provenance grade, or publication requirement. `--required-input`
pins the local bytes used by the current assignment; this is an internal run
binding, not a demand that the upstream research archive expose matching
bytes. `--live-input` explicitly records path-only evolving material with no
exact-replay claim. External literature/data/software provenance belongs in
resolvable evidence references. CAS contracts remain exactly pinned.

Paste the header printed by `new_assignment.py` at the start of the subagent spawn prompt. The assignment JSON supplies the unique result path.

## Strict result contract (MA-03 + PR-247)

Schema-v2 run plans use assignment/result schema v3; legacy non-historical
schema-v1 run plans continue to use assignment/result schema v2. Every
assigned claim must have exactly one typed terminal disposition:

- `findings_present` names one or more finding IDs;
- `examined_no_findings` explicitly records a completed review with no
  finding and requires nonempty evidence references; or
- `not_examined` is allowed only for an `inconclusive` or `error` result.

The validator binds the registered assignment, canonical result path, launch
receipt when present, role and independence mode, declared reads, timestamps,
tools, commands, artifacts, findings, and reported errors. Artifact references
are accepted only after path confinement, blind-sibling authorization,
byte-count, and SHA-256 checks. That hash protects the bytes of a referenced
local artifact; it does not establish scientific validity. Finding severity
is one of `low`, `medium`, `high`, or `critical`. Each substantive finding
needs a bounded, self-declared stable evidence identity scoped to that finding
or proposition; it may be a digest, DOI/release plus section or observable,
source revision plus test, or a finding-specific review-scope label.
`examined_no_findings` and artifact command identities do not require a
fingerprint. These identities are deduplication aids, not authenticated
provenance. Results must echo the automatically generated assignment seal so
a later assignment rewrite cannot validate an earlier verdict. Routine result
JSON is capped at 64 KiB, with larger raw evidence stored once through
`evidence_store.py` and referenced by its typed descriptor.

### Exactness boundary and anti-inflation rule

Source identity, scientific reproducibility, and exact replay are different
claims. Literature, public datasets, and external software normally need a
resolvable DOI/URL/product release/version plus methods, assumptions, and
tolerances sufficient for an independent scientific rerun. Exact byte hashes
are required only for internal assignment/context bindings, CAS contracts,
content-addressed blobs, explicitly frozen inputs, and local artifacts whose
byte identity is itself material. They are not universal upstream provenance
requirements. Hash completeness, gate count, ledger rows, or generated
Markdown/JSON volume are never research progress metrics.

Do not create a permanent claim row, gate, receipt, or policy file solely to
make a run structurally pass. Use a `RUN-*` question for bounded process work,
reuse this kernel, and downgrade provenance honestly when exact upstream bytes
are unavailable. After two consecutive assurance-only PRs, the next PR must
deliver a named downstream scientific capability, data execution/integration,
experiment, or interpretable result. Another harness repair counts only when a
reproduced high-severity defect directly blocks that named task.

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

Execute only the registered assignment. The SubagentStart hook injects one validated bounded view; do not re-read CONTEXT_PACK.md. If the hook reports a context violation, stop instead of using a file fallback. Load the assignment before analysis, respect sibling-result isolation, write the declared result, and end with HARNESS_RESULT.
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
evidence needed for a targeted decision. `evidence_fingerprint` is a bounded,
stable identity for the scoped finding/proposition (for example a DOI or
dataset release plus a relevant section, observable, or test), not a demand
for an upstream SHA and not merely a whole-source label. Opposite verdicts on
the same `(claim_id, evidence_fingerprint)` are emitted as a `conflicts` object
and fail the merge even when their prose differs — no majority vote. Statement
text is explanatory prose, not identity, so paraphrases of the same scoped
finding deduplicate and cannot create new resolved-ledger items. Different
sub-findings from one source use different scoped identities rather than a new
schema field. Resolved findings are recorded in
`.agent-harness/ledger/FINDING_LEDGER.jsonl` so later runs do not re-raise them.

`MERGED_RESULTS.json.process_status` reports only envelope/merge integrity.
Its `claim_gate_status` is always `NOT_EVALUATED`; a zero merge exit code is
never a novelty, scientific-validity, or claim-acceptance decision.

## Freeze, review, integrate, and hand off to the publisher

Ordinary agents stop before publication:

```bash
python3 .agent-harness/scripts/candidate_seal.py create \
  --change-set CS-PR247-PUBLICATION-INTEGRITY-P0 \
  --publication-group PG-PR247-PUBLICATION-INTEGRITY-P0 \
  --target-ref origin/research/pr04-multicomponent \
  --integration-policy \
    docs/research_program/long_horizon_rescue/pr247_publication_policy.json \
  --output .prguard/runtime/CANDIDATE_SEAL.json

python3 .agent-harness/scripts/bind_candidate.py \
  --seal .prguard/runtime/CANDIDATE_SEAL.json

python3 .agent-harness/scripts/new_assignment.py \
  --assignment-id A-REVIEW \
  --agent-type claim_gate_reviewer \
  --workflow-role reviewer \
  --independence-mode blind-results \
  --risk-tier R2 \
  --claim-id RUN-<run-id>-publication-review \
  --required-input .prguard/runtime/CANDIDATE_SEAL.json \
  --allowed-tool read \
  --allowed-tool pytest \
  --required-output REVIEW_COVERAGE.json \
  --task 'Falsify the exact frozen candidate without modifying it.'

python3 .agent-harness/scripts/integration_rehearsal.py create \
  --seal .prguard/runtime/CANDIDATE_SEAL.json \
  --output .prguard/runtime/INTEGRATION_RECEIPT.json
```

The coverage matrix must bind concrete executable-oracle argv and an
assignment-produced output artifact. The integration receipt binds the
recomputed target/candidate merge tree and the exact command logs. Any target,
candidate, tree, diff, changed-file, remote, policy, review, or integration
drift blocks the gate.

`pr_publication_gate.py` validates but never publishes. A separate serialized
publisher, running outside ordinary agent sandboxes with its own credentials,
key, nonce ledger, and `pr_inventory.py` output, may call `check` and then
`consume`. Its authorization fixes the PR title/body/base/head/draft state;
the body carries exactly one matching `Change-Set-ID:` and
`Publication-Group-ID:` line. Its fixed push refspec uses the sealed commit
SHA as the source, not the movable local branch. Repository hooks are only
guardrails; managed policy and credential/network isolation are the capability
boundary. See `docs/harness/PUBLICATION_INTEGRITY.md`.

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
