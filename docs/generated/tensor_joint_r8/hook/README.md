# R8 worktree hook correction

This unit addresses the actual wrong-checkout start/stop failure encountered in
R8-AC. Native event capture showed the parent session ID and actual child agent
ID, while cwd remained the original checkout. The parent now explicitly stages
one worktree/git-dir/run/assignment binding immediately before each native spawn.
Start validates it, injects the target context, and records it by actual child ID.
Stop consumes that child's completed start record. It never selects a run from
the task name or a later pending assignment. Original active-run pointers remain
unchanged; unbound legacy invocations retain their existing behavior.

The launcher's three hook files were updated locally after preserving exact
prior bytes. The implementation is committed on the R8 branch. A session binding
is an operational local record, not model-profile attestation or scientific
acceptance. Stage calls are serialized before their corresponding spawn calls;
an unconsumed pending binding refuses overwrite.

```sh
python3 .agent-harness/scripts/bind_hook_context.py \
  --launcher-root /home/cosmosapjw/Dropbox/bianchi/htt_base \
  --repo-root /mnt/sn850x2t/htt_base_e2e/TENSOR-JOINT-R8-20260909/worktree \
  --session-id <actual-parent-session-id> \
  --run-id <registered-run> --assignment-id <registered-assignment>
```

Five new tests use two real Git worktrees with identical task names. They cover
separate receipts, a new pending assignment not retargeting an earlier child,
swapped/stale/missing contexts, legacy behavior and typed rejection when a bound
Git worktree disappears. Together with the existing enforcement suite,
**100 tests passed**. Independent review additionally ran all five plus two
legacy subprocess cases: **7 passed**. Review found the uncaught Git lookup
failure; its raw start/stop failures and successful repair checks are retained.
The existing suite also exposed an import-location regression, repaired by
retaining the source-script root only for unbound legacy invocations.

The initial broader asset suite was not clean: AGENTS/fragment suffix mismatch,
incomplete in-progress probe envelope, and installer omissions of referenced
long-horizon-rescue specs were reported in its raw log. The suffix mismatch is
also present in baseline 9ed6ab5c; installer/registry code was not changed here.
No full installer compatibility claim is made. The final producer envelope is
validated separately; historical initial failures are retained.

Evidence: `.agent-harness/runs/R8-HOOK-20260909/` at repository root. The old
reviewer's native start remains non-admitted and its stop was correctly refused:
this repair does not manufacture a retrospective binding. A separate fresh
native child supplies the positive operational check. R8 science, mocks, laws,
CAS verdicts and qiso numerical results are unchanged in this unit.

The fresh native child `01a08273-dcb6-77a3-a8a8-106a630c1b3d` received the
correct R8 context and reached native task completion without a stop rejection.
Its platform task-complete event and actual start binding are retained in
`artifacts/native_completion.json` and `artifacts/native_start_binding.json`.
A separately labelled post-completion replay through the deployed stop consumer
also returned exit 0 with empty stdout/stderr. This establishes the tested
operational path; launch/profile attestation remains unverified and it grants no
scientific capability.
