# PR-000 PR delta: Codex intake, repo snapshot, and immutable baseline inventory

## Goal

Create the current DAG's PR-000 intake baseline without changing scientific
behavior. This PR records repository roots, import/package surfaces, optional
dependency state, collect-only status, generated artifact surfaces, stale
figure/report candidates, and the current worktree state.

This is separate from `docs/PR_DELTAS/pr-000.md`, which is a prior historical
Engineering Constitution Freeze record and is not the active PR-000 intake delta
for the current Codex DAG.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.codex/agents/*.toml`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `htt/pyproject.toml`
- `htt/htt/setup.py`
- `docs/PR_DELTAS/pr-000.md`
- Current filesystem layout under `htt/`, `src/`, `docs/`, `figures/`, `scripts/codex_harness/`, `machine_readable/`, and generated/cache directories.

## Web/doc checks

- WEB_CHECK_STATUS: done
- Source: pytest official documentation for `--collect-only`, which describes it as collecting/showing tests without executing them. This supports using collect-only as an intake/import-path probe, not as scientific validation.
- URL: https://docs.pytest.org/en/stable/reference/reference.html

## Subagent divergence

- code_cartographer:
  - Steelman: use DAG and packaging manifests first, then observed filesystem state. Record Rust root, Python roots, nested legacy `htt`, generated surfaces, stale old PR-000 delta, and exact collection behavior.
  - Attack: do not confuse root `src/` Rust source with Python `htt/src/common`; do not treat extracted hotfix bundles, `target/`, `venv/`, caches, or old PR delta text as active baseline science.
- harness_engineer:
  - Steelman: keep `repo_inventory.json` descriptive and non-behavioral; use command matrix with command, interpreter, result, and blocker interpretation.
  - Attack: do not install packages, rewrite import paths, regenerate figures, hash every large data file, or add broad skips in PR-000.
- physics_stat_auditor:
  - Steelman: inventory current boundaries and unknown/pending rank, null, transfer, mask, and covariance status so later PRs cannot launder existing artifacts into claims.
  - Attack: collection is not validation; names like `posterior`, `production_candidate`, or `MIO certificate` in existing files must be inventoried as surfaces, not endorsed as scientific state.
- claim_gate_reviewer:
  - Steelman: safe language is COMMON-owned L0 intake, C0 inventory/provenance only, no scientific behavior changes.
  - Attack: reject language implying solver validation, family identification, posterior/evidence semantics under MIO ownership, truth-status reports, active Teff/TSC ownership, or production readiness.
- regression_tester:
  - Steelman: the smallest credible checks are `git status`, Python version, `pip show pytest`, required collect-only, DAG validation, and delta dry-run.
  - Attack: collect-only does not validate generated inventory content, artifact metadata completeness, stale figures, or no scientific behavior changes.

## Chosen plan

Add only the PR-000 intake artifacts named by the DAG:

- `docs/generated/repo_inventory.json`
- `docs/generated/test_command_matrix.md`
- `docs/PR_DELTAS/pr-000-intake.md`
- `docs/codex_handoff/pr_status.yaml`

The plan records the literal required command failure under `/usr/bin/python` and
the successful equivalent collection under `venv/bin/python`. It treats the
system-Python failure as an environment prerequisite for PR-001, not as a reason
to edit science code in PR-000.

## Files changed

- Added `docs/generated/repo_inventory.json`
- Added `docs/generated/test_command_matrix.md`
- Added `docs/PR_DELTAS/pr-000-intake.md`
- Updated `docs/codex_handoff/pr_status.yaml`

## Tests run

| Command | Result |
| --- | --- |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | PASS: `OK: 62 PRs, DAG valid` |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml` | PASS before edit: `Completed 0/62 = 0.0%`; unblocked next `PR-000` |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml` | PASS after status update: `Completed 1/62 = 1.61%`; unblocked next `PR-001, PR-003` |
| `python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q` | FAIL: `/usr/bin/python: No module named pytest` |
| `python -m pip show pytest` | FAIL: `WARNING: Package(s) not found: pytest` |
| `venv/bin/python -m pytest --version` | PASS: `pytest 9.0.3` |
| `venv/bin/python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q` | PASS: `1541 tests collected in 1.28s` |
| `python scripts/codex_harness/new_pr_delta.py PR-000 --dry-run` | PASS: scaffold script emits a template, but not the active DAG file name |

## Review findings and fixes

- Finding: `docs/PR_DELTAS/pr-000.md` is a stale historical PR-000 closure record, not the active current-DAG intake delta. Fix: create `docs/PR_DELTAS/pr-000-intake.md` and identify the old file as legacy history.
- Finding: the literal PR-card collect-only command fails before collection because `/usr/bin/python` lacks `pytest`. Fix: record the exact failure and add venv collection evidence without changing interpreter paths or installing packages in PR-000.
- Finding: existing figures and reports lack PR-000 manifest provenance. Fix: inventory them as stale/baseline surfaces with unknown manifest, transfer, sky-support, covariance, and null-mock status; do not promote any result.
- Finding: PR-000's own generated artifacts need artifact metadata. Fix: add owner, scope, claim tier, transfer source, config hash, input hashes, sky/null applicability, caveats, generating command, and git/worktree state to `repo_inventory.json` and `test_command_matrix.md`.

## Claim hygiene and scientific scope

PR-000 is an intake/inventory PR only. It makes no scientific behavior changes
and does not validate any HTT, MIO, BASS, obsstat, TSC, transfer, likelihood,
posterior, null, morphology, or family-identification claim.

Allowed claim tier: inventory / specified / smoke-observed only where directly
supported by command output. Test collection is not scientific validation.

Transfer provenance: no artifact inventoried here is promoted to native low-ell
solver evidence. External/AniCLASS, empirical proxy, legacy
generated, and future native-schema surfaces remain distinct.

MIO/HTT firewall: MIO artifacts are diagnostic-only and must not be described as
posterior, evidence, odds, truth-status reports, or model-selection outputs. HTT
owns posterior/evidence semantics; PR-000 does not run or validate them.

Family-identification gate: scalar x/Q/Pi/F/G/G_F values, low-ell summaries,
direction coherence, BiPoSH/covariance placeholders, or generated result packs
do not identify a Bianchi family. Family identification remains blocked until a
native low-ell morphology atlas, equivalence-class graph, transfer provenance,
rank audit, null/mask/covariance calibration, and HTT PPC/LOOCV gates exist.

Rank/null status: response-rank, nuisance-projection, matched null mocks,
mask/sky support, covariance, and look-elsewhere calibration are recorded as
pending or unknown unless a later PR supplies explicit artifacts.

## Residual risks

- The required PR-000 command fails as written under `/usr/bin/python` because
  `pytest` is not installed there. PR-001 should stabilize editable install and
  import/test invocation.
- Current worktree already contains unrelated modified/untracked handoff/config
  hotfix files. PR-000 records them as preexisting and does not revert or absorb
  them.
- Figure/report inventory is group-level, not a per-file manifest. Later
  artifact-manifest PRs must provide owner, scope, claim tier, transfer source,
  config hash, input hashes, sky support, covariance/null status, caveats,
  generating command, and git/worktree state before using those outputs.

## Commit

Commit message:

`PR-000: record immutable intake baseline`
