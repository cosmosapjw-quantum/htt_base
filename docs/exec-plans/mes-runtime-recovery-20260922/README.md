# MES runtime recovery (local, 2026-09-22)

The owner requested diagnosis and repair using GPT-6 Astra only for this task,
without a task-level token/call/wall budget. Existing scientific task limits,
failed attempts and admission states are unchanged. Base: f90ed9e49e18b75ea716df70cebf2cea28d9c95b.

## Reproduced causes

1. The prompt classifier returned no payload phase for the Korean runtime repair
   request. Its generated instructions nevertheless required `run`, which refused
   that observation before making an execution state. `fallback` then required the
   state. Earlier code raised FileNotFoundError; the installed version correctly
   returned PRE_ADMISSION_STATE_REQUIRED but provided no usable Host transition.
2. `global_hook.py inspect` unconditionally recommended workspace-job continuation.
   The MES registration has claim=null, child=null and continuation_context=null:
   it is an unlaunched direct registration, which never creates workspace_job.json.
   Its absence is expected, not evidence of a deleted or corrupt scientific job.
3. Its client really is at the original checkout while its source registration is
   at the isolated MES worktree. CLIENT_WORKTREE_MISMATCH is a valid identity check.
   Shell cwd overrides do not move the client. This check is preserved.
4. The standard five-profile selector had no explicit owner-selected Astra path.
   A Host request may now bind an observed model/effort with explicit owner evidence
   for this task only. Default profiles and historical launch profiles are unchanged.

## Repair behavior

`execute_task.py fallback --host-task-json TASK --evidence-json EVIDENCE` supports
an explicit owner-directed PARENT reservation before model-task admission. It
binds the original observation, repository, task, input hashes, scope and external
validator. Evidence must include the same task_id, host_authorized=true,
reason_code=EXPLICIT_OWNER_DIRECT and a reason. No model is invoked, no local success
is invented, no classified observation is rewritten, and no admitted/unknown or
partial execution is replaced. Repeated identical requests are idempotent; changed
requests are refused. The status is HOST_RESERVED_PRE_ADMISSION, not completion.

Prompts without a classified payload now describe this Host path rather than an
impossible model-task run. Ordinary model candidate execution stays unchanged.

`global_hook.py inspect` distinguishes a direct unclaimed launch, a registered
workspace job and a claimed direct launch without resource context. It never
creates missing jobs, computes a budget or authenticates an unexecuted reviewer.

An owner-selected native model uses owner_selected_model, owner_selected_effort,
owner_model_authorized=true and owner_model_evidence_ref in the Host request,
and must be in the current client's observed capabilities. This does not change
the current parent, historical profiles or provider policy.

## Evidence and activation boundary

Actual source/test/runtime evidence is retained in the sibling directory
`../evidence` of this local repair worktree's parent, including the original failures,
the successful same-opportunity Host reservation, new direct-launch diagnosis and
an actual registered Astra review. The MES registration remains byte-equivalent
as a JSON object; its Terra reviewer has not been executed by this repair.

This is runtime maintenance, not new MES/R9 scientific evidence. Existing MES replay,
33 unit/regression tests and the e70663a runner tests are carried forward unchanged.
Physical inputs and empirical MES D remain HOLD/HOLD_NOT_COMPUTED.

Global policy promotion still requires its existing merged-source procedure. A
locally installed hook hotfix, if recorded in the return, is separate from that
promotion; it must preserve the existing hook backup and trust decisions. No remote
publication, broad model policy change or scientific admission is implied.
