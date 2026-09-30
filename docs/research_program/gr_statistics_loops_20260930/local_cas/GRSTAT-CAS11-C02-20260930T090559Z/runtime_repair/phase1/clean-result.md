# CAS11 C02 author-write repair — source only

Fixed the registered-child parent-gate error. No installation, commit, child
dispatch, scientific execution, admission or source-state promotion was performed.

## Exact files changed by this repair

- `/home/cosmosapjw/codex_global_harness/src/cuhg/codex_hooks/global_dispatch.py`:
  10 added lines and two substitutions relative to the supplied dirty baseline.
  Resolve each PreToolUse actor through its existing parent-session/child binding;
  pass an event-local child state to the author gate and nested-spawn check.
- `/home/cosmosapjw/codex_global_harness/tests/unit/test_registered_child_author_routing.py`:
  four regression tests using isolated synthetic runtime metadata.

The preexisting changes in `global_hook.py`, `install_local_router_hook.py` and
`global_dispatch.py` were preserved. This repair shares `global_dispatch.py` but
does not overlap its preexisting review-continuation hunk. The other two files
still match the supplied baseline exactly; no concurrent changes were observed.
`repair-only.diff` beside this report excludes the preexisting edits.

## Actual cause and evidence

The three observed child tool events used parent session
`01a0f18d-406e-74f2-8ab8-49e56ffa0b94` plus their correct `agent_id`:

- Wolfram: `01a0f192-3705-7bd2-a9db-240f78953765`
- SymPy: `01a0f192-cf62-78d0-b612-15473f2b8151`
- Sage: `01a0f193-17a5-7e30-99d0-3c9ee71d894e`

Their transcript session_meta rows identify that parent, their distinct task paths
and `cuhg_gpt6_sol_worker` role. Registry bindings and observed Sol/high runtime
match. The parent journal records each apply_patch denial with the child's ID
and turn ID, but its `is_child` is false. That flag was set only by
UserPromptSubmit. `check_edit` ignored the current event actor and therefore
applied the parent author-route requirement to all three registered children.

The fix recognizes an already bound actor without revalidating transcript bytes,
hashes, model tiers or Git HEAD. Parent state stays unchanged. Task-name aliases,
unbound actors and children belonging to another parent do not receive the
exemption. Child classification also preserves the existing nested-spawn ban.
Source validators, assumptions, tasks, budgets and admission behavior are unchanged.

The descriptor points to immutable `5c540279f995208221339bceead922be4260abe2`, while
all eight hooks invoke immutable `3b243df626bce98ee31ba899d48c9bceddef1bfd`.
The recorded denials came from the latter. Both global_dispatch.py files are
identical (SHA-256 `edd3a6fbba5f19edaf6b8aaffc53ed33098326ce43245b2f65a614da37306208`)
and contain this bug. Merely aligning those two authority references cannot fix it.
The preexisting untracked review overlay dynamically forwards to the descriptor,
but current hooks do not invoke that overlay; it would forward ordinary patches
to another affected handler.

## Validation

Before the runtime change, the new tests reproduced all three active-child patch
denials, the completed-child patch denial, and incorrect nested-spawn classification
(pytest: 5 failed, including three child subtests; 2 passed).

After the fix:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m pytest -q \
  tests/unit/test_registered_child_author_routing.py \
  tests/unit/test_author_routing.py \
  tests/unit/test_global_hook_dispatch.py \
  tests/unit/test_global_hook_lifecycle.py
59 passed, 54 subtests passed
```

Telemetry for that run was redirected to this report directory and marked TEST.
The final active-child fixture omits the stop-time runtime observation, matching
first-write timing; its focused rerun passed: 4 tests, 8 subtests.
`git diff --check` passed. Protected hooks.json, policy descriptor and lifecycle.json
remain byte-identical across the repair; historical exits and C04 are preserved.

## Continuation and Lean

All three completed author registrations have `continuation_context=null` and
retain RUNTIME_ONLY_SUCCESS / NON_ADMISSION. Their semantic child identity survives
completion, but this fix does not reserve another generation. Installed followup
handling requires workspace continuation context. The dirty source's alternative
closeout supports named reviewers only, not these Sol/high authors. There is no
supported direct-author continuation reservation for these records today.
Do not fabricate a workspace job, replay hook events, reregister, reset costs,
or use a standalone child resume to evade that missing accounting path. Supporting
their next generation needs a separate same-task continuation change; none was
invented in this minimal classification repair.

Lean `cl_5e39fc6af15cd91b0753690877580da3` / `c02_lean` is still unclaimed/unbound.
Read-only source/worktree preflight returned no issues and no blocking unbound
claims; registered HEAD remains `42a3320b03428bce9457e999ddef18135244a425`.
It supports its first real dispatch using that existing registration from the
original parent and worktree, with its frozen Sol/high profile, fresh brief and
matching inherited sandbox. Live sandbox/trust/liveness must still be observed
at that real dispatch. No Lean registration or dispatch was performed here.

## Minimal later activation (not executed)

The existing installer can point the managed handlers at the corrected source:

```bash
/usr/bin/python3.12 /home/cosmosapjw/codex_global_harness/scripts/codex_harness/install_local_router_hook.py \
  --hooks-file /home/cosmosapjw/.codex/hooks.json \
  --source-root /home/cosmosapjw/codex_global_harness \
  --python /usr/bin/python3.12
```

Use the existing Host client's `/hooks` interface to review/trust and reload the
changed handler. If it retains cached configuration, reopen the original Host
session using the supported client resume interface, preserving its session ID:

```bash
codex resume --cd /home/cosmosapjw/Dropbox/bianchi/htt_base 01a0f18d-406e-74f2-8ab8-49e56ffa0b94
```

Do not use `--review-closeout-overlay` for this repair: it forwards ordinary
patches to the still-broken installed authority. The installer changes managed
hook commands, not the descriptor or lifecycle registry. Pointing at this working
checkout also activates its preexisting dirty review-closeout code; the isolated
repair diff is available for later integration into the chosen release source.
Native hook reload/trust, surviving child handles and actual corrected-handler
execution remain unverified. No live canary or fabricated hook event was run.

The shell-written finite_gram.wl was neither read nor executed. Mathematical
candidate contents were not reused; there are no scientific claims in this repair.
