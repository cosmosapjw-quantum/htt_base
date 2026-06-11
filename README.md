# Codex Handoff Package v3 — HTT Pre-solver Skillset Augmentation

This package upgrades the previous HTT pre-solver Codex handoff with the uploaded custom research-harness skills, rewritten as repo-scoped HTT/BASS/MIO skills.

It contains:

- `AGENTS.md` and `agent.md` compatibility copy;
- `.agents/skills/` with the original repo skills plus augmented research-harness skills;
- `.codex/agents/` custom subagents;
- `.codex/rules/` project-local command rules;
- `docs/` PR DAG, source authority map, skill inventory, installation guide, and adversarial audit notes;
- `scripts/codex_harness/` DAG/progress/skill-layout harness scripts;
- `harness_templates/docs/harness/` bootstrap ledgers.

The main design choice is strict separation:

```text
common/contracts -> obsstat -> HTT/MIO -> result packs/manuscript
future BASS/native solver -> transfer/atlas adapters -> obsstat/HTT/MIO
```

This package does not implement the external low-ell solver. It prepares the repo to consume solver outputs later.
