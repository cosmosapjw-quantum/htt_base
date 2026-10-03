# Current project runtime (v5, 2026-09-29)

Validated against Codex CLI 0.158.0. Global CUH-G is selected dynamically by
`~/.codex/runtime/global-execution-policy.json`; no stale absolute authority SHA
is embedded in project skills. Project science contracts still own acceptance.

## Start and execute

Work in the repo root. Record dirty files before edits; use disjoint write ownership.
A new worktree requires owner approval of a concrete need. Preserve open task IDs,
usage, frozen validators, one-use allocations and old OUTCOME_UNKNOWN states.

```sh
python -B scripts/codex_harness/project_runtime.py check
bash scripts/install_codex_handoff.sh "$PWD" --activate
cuhg-telemetry run --project "$PWD" --task TASK_ID -- python -B YOUR_ENTRYPOINT.py
```

Use the explicit existing interpreter for a scientific environment. When one is
required, pass `--runtime-receipt FILE` to `cuhg-telemetry run` and launch `-m MODULE`
using the installed runtime binding interface. A configured server or a hook file
is not proof of telemetry delivery: query the resulting MLflow run. Spool/export
failure is an observation gap and cannot abort the scientific command.

Adaptive soft targets guide route selection and replanning. They are not default
hard token ceilings. Count planning, handoff, failures, repair, review and fallback.
Bonsai CPU manages context; on failure continue from original references. Respect
actual RAM and the managed fleet; never start unmanaged model servers.

## Native workers and author observation

Run `global_hook.py register --help` from the exact installed global authority.
Register a bounded opportunity before `spawn_agent`; use its returned launch ID,
model/effort profile and fresh context. Never inherit the Host profile implicitly.
Domain agent TOMLs provide task guidance, not permission to bypass global routing.
Use the registered native profile as `agent_type`. For example, a registration
selecting `cuhg_gpt6_sol_worker` must not be spawned as `cas_sympy`, even when
both TOMLs specify `gpt-6-sol/high`. Supply the SymPy assignment and its frozen
contract in the bounded task message. Adding explicit model/effort to an
unobserved domain role does not fix `ROUTING_PROFILE_MISMATCH`. Apply the hook's
registered spawn fields and reuse the existing launch; do not register again or
alter the contract. A sandbox mismatch still requires reconciling the actual
client permissions with the frozen registration.
No nested children. Review and implementation have separate requested/observed
identities. Preserve the global same-task dispatch/accounting ledger.

Run `scripts/codex_harness/observe_codex_runtime.py --help` from the same authority.
Supply the actual local transcript, session ID, turn ID and cwd. This reads only
runtime metadata into its output; it never treats a requested model as observed.
An observation proves those runtime fields, not authorship of an arbitrary diff.
Tie the author turn to the candidate change record separately. Missing/ambiguous
observations remain unknown; do not manufacture attestation or a model rank.
The current router supports the explicit Host Astra/ultra blind-review exception.

New tasks use the global lifecycle. Project SubagentStart/SubagentStop hooks remain
empty to avoid running two lifecycle engines concurrently. The project SessionStart
hook is advisory compact context and cannot stop progress. The historical v1 hooks
remain executable at `harness_templates/legacy_hooks/` for frozen-run regression;
they are not newly registered or automatically activated.

## Context and legacy resources

The generated core must fit bootstrap + role context within 12,000 characters.
Historical decisions are reference-only; their original reopen conditions remain.
Use `build_context_pack.py --current` for CURRENT_CONTEXT_INDEX/PACK. The original
index and pack remain frozen for active historical runs. New context
must never retroactively rewrite an assignment or activate R9. Full legacy protocol
is in `LEGACY_SHARED_CONTEXT_V1.md`. Physmath 3.1 vendor files remain reproducibility
material; active workflows use the installed physmath 4.0 skills when appropriate
and project-specific scientific boundaries. Do not bulk-copy stale vendored skills
or overwrite local custom skills/profiles with a newer upstream directory.

## Installation and review

The same-root installer activates by validating current assets and writing only
ignored `.agent-harness/runtime/current-runtime.json`. It does not reset ACTIVE_RUN,
change trust settings, restart services, overwrite user edits or create a worktree.
Installing into another empty directory retains the older merge-only distribution
path. Divergent configuration is never replaced automatically.

Codex discovers hooks in all active layers; matching hooks run concurrently.
Hook installation and user trust are separate. Use `/hooks` or the supported client
API to inspect trust after changing definitions. Transcript layout is not a stable
public API; unsupported layouts are reported instead of inferred.

The October 3 incident's resumed coordinator and three children report
`0.159.0-alpha.12.1`; the later empty thread reports `0.160.0`. An installed daemon
version alone does not identify the executable that handled an earlier turn.
In this extension, Hook stats counts finished invocations for a turn: `blocked`
and `failed` are distinct native statuses, and `stopped` is separate. Preserve
the individual `hook/completed` notifications (including `run.id`, `eventName`,
`sourcePath`, timestamps and `entries`) while the client is live. Rollouts and
the history database may omit these notifications. The two October 3
`ROUTING_PROFILE_MISMATCH` blocks are confirmed; the reported six failed runs
cannot be assigned to commands or causes from the retained transcript alone.

Reference checked 2026-09-29:
- https://learn.chatgpt.com/docs/hooks
- https://learn.chatgpt.com/docs/agent-configuration/subagents
- https://learn.chatgpt.com/docs/config-file/config-reference

## Scientific ceilings and publication

No native family identification, quantitative Q/F/Pi/G_F, MES ratio, likelihood or
p-value admission follows from this upgrade. Historical Loop2 STOP_INVALID remains
a past result; a new independent review is recorded as a new event. Four-axis CAS
rules, exact frozen feature/hash contracts and original DB/raw data are unchanged.
Classify SHA drift by field: source/input, deterministic evidence, numerical output,
or packaging. Inspect both original preimages before modifying any numerical path.
R1 routine publication uses remote identity; R3 authority/recovery changes require
content verification. Report code, review, remote merge, installation and actual
activation separately. End with a runnable handoff and exact remaining blockers.
