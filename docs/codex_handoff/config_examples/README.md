# Codex config hotfix notes

This package intentionally does **not** install a project-local `.codex/config.toml`.

Reason: some Codex versions parse `[agents]` as a role map and will raise:

```text
invalid configuration: invalid type: integer `32768`, expected struct AgentRoleToml in `agents`
```

The repo does not need project-local config to use this handoff package. The required pieces are:

- `AGENTS.md` at repo root.
- `.agents/skills/<skill>/SKILL.md`.
- `.codex/agents/*.toml` standalone custom agent files.
- `.codex/rules/default.rules`.

If you need global subagent thread caps, configure them in your user-level Codex config only after checking your installed Codex version's config schema.
