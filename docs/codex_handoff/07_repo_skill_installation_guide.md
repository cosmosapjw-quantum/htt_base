# Repo Skill Installation Guide

## Canonical Codex locations

Use repository-local skills at:

```text
<repo>/.agents/skills/<skill-name>/SKILL.md
```

The `SKILL.md` file must include `name` and `description` frontmatter. Optional `scripts/`, `references/`, `templates/`, and `assets/` directories can live inside the skill folder.

## Install into `htt_base`

From outside the repo:

Use `docs/codex_handoff/INSTALL.md` as the current install guide. The older
archive commands below are retained only as provenance for the v3 handoff
package and should not be used for a fresh install.

Manual installation:

```bash
cd /path/to/htt_base
mkdir -p .agents .codex docs/codex_handoff scripts/codex_harness docs/harness
cp -R /path/to/package/.agents/* .agents/
cp -R /path/to/package/.codex/* .codex/
cp /path/to/package/AGENTS.md AGENTS.md
cp /path/to/package/agent.md agent.md
cp -R /path/to/package/docs/* docs/codex_handoff/
cp -R /path/to/package/machine_readable/* docs/codex_handoff/
cp -R /path/to/package/scripts/codex_harness/* scripts/codex_harness/
cp -R /path/to/package/harness_templates/docs/harness/* docs/harness/
```

## Verify installation

```bash
python scripts/codex_harness/verify_skill_layout.py .
python scripts/codex_harness/skill_index.py .
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml
```

## Optional Codex config

The current repository intentionally does not install project-local
`.codex/config.toml`. Codex config schemas differ across releases, and stale
`[agents]` scalar settings can trigger `AgentRoleToml` parse failures. Keep
`.codex/agents/*.toml` and `.codex/rules/default.rules` as the versioned
project-local Codex assets. Trust the project `.codex` layer before relying on
project-local rules. Keep `AGENTS.md` as the canonical instruction file;
`agent.md` is a compatibility copy only.

## Skill invocation examples

```text
Use $htt-scientific-code-validation to validate this PR and update the validation ledger.
Use $htt-claim-provenance-ledger and $htt-claim-firewall to audit the changed report.
Use $htt-family-identification-gate before any family-ranking claim.
Use $htt-latex-paper-build to compile and audit the manuscript figure references.
```
