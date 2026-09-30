# Standalone activation plan — not executed

The staged overlay contains only the corrected `global_dispatch.py` and
`direct_author_continuation.py`. All other imports use the unchanged immutable
`3b243df626bce98ee31ba899d48c9bceddef1bfd` authority. It excludes the unrelated dirty
review-closeout implementation, CLI and installer changes.

Artifacts:

- `author-continuation-runtime/`: two-file runtime overlay and manifest.
- `runtime-author-continuation.patch`: equivalent patch against that authority's
  handler, for a separate overlay only. Never apply it inside the immutable bundle.
- `repair-total.diff`: all four owned source/test files relative to the supplied
  `source-baseline.json` and its saved dirty baseline.
- `build-continuation-artifact.py`: reproducible staging, with no installation.
- `continuation-artifact-test.log`: isolated subprocess check against the real
  unchanged authority dependencies. First followup allowed, duplicate denied,
  original launch preserved. This is not a native client receipt.

Exact staged PreToolUse command:

```text
env PYTHONPATH=/mnt/sn850x2t/local_ai_foundry/60_runtime/cuhg/policy-authorities/3b243df626bce98ee31ba899d48c9bceddef1bfd/src /usr/bin/python3.12 /tmp/cas11-c02-routing-repair-20260930/author-continuation-runtime/src/cuhg/codex_hooks/global_dispatch.py
```

For a later live activation, replace only the currently configured standalone
author-repair PreToolUse command with this command (or the same files at a durable
separate overlay path). Preserve all other handlers/events, descriptor, immutable
authorities and state. Replace the one managed command rather than stacking a
second handler: a later old handler could deny after a continuation is consumed.
Do not use the full dirty-source installer or reviewer overlay for this artifact.
This source-only repair has not changed hooks.json or trust, and provides no trust
bypass or automatic reload command.

The existing parent still invokes its cached immutable handler. No live reload
tool is exposed in this session. Merely staging this artifact, editing configuration
elsewhere, or observing a fresh child's corrected handler cannot prove that the
existing parent has reloaded. The external client must load the corrected command
for that same parent before its native followup can succeed. A supported reopen is:

```bash
codex resume --cd /home/cosmosapjw/Dropbox/bianchi/htt_base 01a0f18d-406e-74f2-8ab8-49e56ffa0b94
```

Client hook caching/trust and restoration of the existing child handles must be
observed after reopening; this command alone is not activation evidence. If that
client retains the old handler or cannot restore a child handle, stop at that
external client limit. Do not create another registration, use a child as a new
standalone parent, edit immutable handlers/trust, or fabricate events.

Once the original parent actually uses the corrected handler, one exact positive
execution path is its real native `collaboration.followup_task` call:

```json
{
  "target": "01a0f192-3705-7bd2-a9db-240f78953765",
  "message": "Continue only the existing GRSTAT-CAS11-C02-20260930T090559Z-wolfram_xact task in this same author thread and registered worktree. The prior stop was the author-route runtime defect, not proof completion. Preserve the original scientific contract, accumulated work and failures. Use native apply_patch and the existing validators. Do not register another task, spawn children, reset accounting, or promote outcomes."
}
```

This uses launch `cl_01a62782af09d704bc761d9990a8ab94`, its existing Sol/high runtime
and real native tool-use ID. No preliminary workspace job or reservation writer
is needed. The PreToolUse branch atomically records the consumption. If the native
call then fails or its outcome is unknown, the consumption remains pending and
cannot be retried blindly or refunded.

After the real child returns and its normal SubagentStop records the new runtime,
the metadata-only accounting operation can close that consumption without another
model call or replaying admission:

```bash
env PYTHONPATH=/mnt/sn850x2t/local_ai_foundry/60_runtime/cuhg/policy-authorities/3b243df626bce98ee31ba899d48c9bceddef1bfd/src \
  /usr/bin/python3.12 /tmp/cas11-c02-routing-repair-20260930/author-continuation-runtime/src/cuhg/codex_hooks/direct_author_continuation.py \
  record-return \
  --root /home/cosmosapjw/.codex/runtime/global-hooks/v1 \
  --launch-id cl_01a62782af09d704bc761d9990a8ab94 \
  --session-id 01a0f18d-406e-74f2-8ab8-49e56ffa0b94 \
  --child-id 01a0f192-3705-7bd2-a9db-240f78953765 \
  --client-cwd /home/cosmosapjw/Dropbox/bianchi/htt_base
```

Replacing `record-return` with `inspect` performs a prospective metadata check
without reserving a turn. Neither operation fabricates hook events or executes
validators. A later real followup also records the preceding observed return
before consuming the next turn. All historical launch and exit records remain.
