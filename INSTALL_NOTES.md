# Installation notes

- The correct repository instruction filename is `AGENTS.md` (plural).
- Merge the fragment rather than replacing an existing `AGENTS.md`.
- Project hooks run only in trusted projects and must be reviewed with `/hooks` after changes.
- The scripts use only Python's standard library.
- The hook command assumes a Git repository because it resolves paths through `git rev-parse --show-toplevel`.
- `max_threads = 4` and `max_depth = 2` are Codex runtime controls. The total-of-eight budget is enforced by the assignment registrar and AGENTS policy, not by a native `max_total` Codex setting.
- The `SubagentStart` hook can inject context but cannot prevent a subagent from starting. The harness therefore prevents bad spawns at the parent/assignment-registration layer and validates handoffs at `SubagentStop`.
