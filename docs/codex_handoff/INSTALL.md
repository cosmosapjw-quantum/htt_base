# htt_base Codex Asset Install Guide

This repository carries project-scoped Codex instructions, skills, custom
subagents, and execpolicy rules. Keep these assets in the checkout so they stay
versioned with the PR DAG and the HTT/MIO/BASS/obsstat claim boundaries.

Do not copy these files into user-global Codex locations. User-global files can
shadow or outlive this repository and may accidentally apply pre-solver
scientific boundaries to unrelated projects.

## Asset Paths

- `AGENTS.md`: repository operating contract, scientific boundaries, PR loop,
  and preferred commands.
- `.agents/skills`: repository-local skills. Each skill must have a
  `SKILL.md` with frontmatter containing `name` and `description`.
- `.codex/agents`: project custom subagent profiles. Read-only reviewers must
  remain read-only; implementation-focused harness/test roles may use
  `workspace-write`.
- `.codex/config.toml` and `.codex/hooks.json`: trusted-project concurrency and
  lifecycle-hook settings for the versioned shared-context protocol. The
  repository pins four concurrent threads, depth two, and fail-closed context
  and result-envelope hooks.
- `.agent-harness`: canonical shared context, assignment/result schemas,
  registrar, validator, and per-run evidence. Build the context pack before
  every spawn and never reuse an assignment identifier.
- `.codex/rules/default.rules`: project-local execpolicy examples and command
  decisions for common harness, pytest, and git operations.
- `docs/codex_handoff/pr_backlog.yaml`: DAG authority for the next PR.
- `docs/codex_handoff/pr_status.yaml`: completed/blocked/in-progress status.

## Verification

Run these from the repository root after changing instructions, skills, agents,
or rules:

```bash
python scripts/codex_harness/verify_skill_layout.py .
python scripts/codex_harness/skill_index.py .
python scripts/codex_harness/validate_codex_config_shape.py .
python .agent-harness/scripts/validate_harness.py
codex features list
codex execpolicy check --pretty --rules .codex/rules/default.rules -- python -m pytest -q
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python -m pytest scripts/codex_harness/test_codex_assets.py -q
```

The `codex execpolicy check` command validates rule syntax and example matches.
It does not execute the checked command.

## Loading Rules

Codex reads repository `AGENTS.md` as project instructions, scans
`.agents/skills` from the current working directory up to the repository root,
and loads trusted project `.codex` layers for custom agents, rules, config, and
hooks. Use `/hooks` after opening or resuming a trusted project session to
confirm the three shared-context lifecycle hooks are active.

Start Codex from `/home/cosmosapjw/Dropbox/bianchi/htt_base` or a child path of
that checkout so repository-local skills and project instructions are in scope.
If project trust is disabled, project `.codex` layers can be skipped by Codex;
in that case, verify with the explicit commands above before relying on rules or
custom subagents.

`scripts/install_codex_handoff.sh` copies the canonical harness context,
scripts, and templates, then builds and validates a fresh context pack. It does
not copy an `ACTIVE_RUN`, prior run results, or raw logs, and it fails closed if
the destination already has an active harness run. Existing `AGENTS.md`,
`agent.md`, `AGENTS.md.fragment`, and `.codex` files are merge-only: identical
files are retained, while divergent files or symlinks stop the installation
before the first destination write so repository policy and intentional Codex
settings cannot be silently replaced.

## Scientific Scope

These assets are L0 orchestration infrastructure. These L0 install checks do
not validate scientific behavior: native solver outputs, transfer calibration,
HTT posterior/evidence implementations, MIO diagnostic reports, null
calibration, morphology compatibility, or family-identification gates.

The allowed language remains:

- `claim-tiered observational/statistical framework`
- `transfer-conditional result`
- `diagnostic-only certificate`
- `local/global discrimination candidate`
- `morphology compatibility`
- `external-transfer path`

Do not use these install checks as evidence for `Bianchi family identified`,
native solver readiness, or a model-independent truth certificate.
