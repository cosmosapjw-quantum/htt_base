# Installation

## One-command install

```bash
bash scripts/install_codex_handoff.sh /path/to/htt_base
```

## Manual install

```bash
PKG=/path/to/codex_handoff_htt_presolver_v3_skillset_augmented_2026-06-11
REPO=/path/to/htt_base
cd "$REPO"
mkdir -p .agents .codex docs/codex_handoff scripts/codex_harness docs/harness
cp "$PKG/AGENTS.md" AGENTS.md
cp "$PKG/agent.md" agent.md
cp -R "$PKG/.agents"/* .agents/
cp -R "$PKG/.codex"/* .codex/
cp -R "$PKG/docs"/* docs/codex_handoff/
cp -R "$PKG/machine_readable"/* docs/codex_handoff/
cp -R "$PKG/scripts/codex_harness"/* scripts/codex_harness/
cp -R "$PKG/harness_templates/docs/harness"/* docs/harness/
```

## Verify

```bash
python scripts/codex_harness/verify_skill_layout.py .
python scripts/codex_harness/skill_index.py .
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml
```

## Recommended first Codex prompt after installation

Use:

```text
Read AGENTS.md, docs/codex_handoff/02_long_range_PR_backlog.md, docs/codex_handoff/08_skill_trigger_matrix.md, and .agents/skills. Start at PR-000. Before editing, invoke $htt-dag-orchestrator, $htt-harness-engineering, and $htt-scientific-code-validation. After the PR, invoke $htt-adversarial-review-loop, fix concrete findings, update docs/harness ledgers, and record commands run.
```
