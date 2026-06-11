# PR-003 PR delta: DAG manifest and progress engine

## Goal

Make the PR DAG harness deterministic enough to drive follow-on work without
overstating scientific progress. PR-003 validates DAG structure and policy
ordering, generates the PR-card Mermaid graph artifact, validates status
snapshots before computing progress, and reports count, dependency-weighted,
and critical-path bookkeeping percentages.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `machine_readable/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/codex_handoff/03_PR_dependency_graph.mmd`
- `docs/codex_handoff/03_PR_dependency_graph.dot`
- `scripts/codex_harness/validate_pr_dag.py`
- `scripts/codex_harness/progress_report.py`
- `docs/codex_handoff/01_source_authority_map.md`
- `docs/codex_handoff/checkpoint_protocol.md`

## Web/doc checks

- WEB_CHECK_STATUS: done
- PyYAML documentation: `yaml.safe_load` limits YAML construction to simple
  Python objects instead of arbitrary Python objects.
  URL: https://pyyaml.org/wiki/PyYAMLDocumentation
- Mermaid flowchart documentation: flowcharts are defined as nodes and edges
  in text syntax.
  URL: https://mermaid.js.org/syntax/flowchart.html
- GitHub Markdown documentation: GitHub supports Mermaid diagrams in fenced
  `mermaid` code blocks.
  URL: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams

## Subagent divergence

- code_cartographer:
  - Steelman: the existing two scripts already validate duplicates, missing
    dependencies, cycles, and simple count progress.
  - Attack: `progress_report.py` ignored policy order, accepted stale/unknown
    status ids, and the PR-card graph path `docs/codex_handoff/pr_dag.mmd`
    was missing.
- harness_engineer:
  - Steelman: PR-003 should be a deterministic COMMON L0 control plane.
  - Attack: progress reports must reject invalid status, incomplete dependency
    closure, completed/blocked overlap, and non-positive checkpoint intervals.
- physics_stat_auditor:
  - Steelman: DAG bookkeeping blocks claim work from outrunning contracts,
    transfer provenance, null calibration, and artifact manifests.
  - Attack: progress percentages are not solver-validity, rank/null
    calibration, transfer validity, or family-identification evidence.
- claim_gate_reviewer:
  - Steelman: safe language is "DAG-card bookkeeping" and "pre-solver
    coordination progress."
  - Attack: reject wording that says "framework ready", "science validated",
    "native runtime ready", or "family-classification advancement."
- regression_tester:
  - Steelman: the happy-path commands were green before PR-003.
  - Attack: edge probes showed unknown completed/blocked ids and invalid DAGs
    could still produce authoritative-looking progress output.

## Chosen plan

1. Add focused subprocess tests for policy-order validation, Mermaid graph
   generation, policy-ordered unblocked progress, critical-path metrics, and
   unknown status rejection.
2. Rework `validate_pr_dag.py` around reusable validation functions and a
   `--write-mermaid` option.
3. Rework `progress_report.py` to reuse DAG validation, validate status
   snapshots, order unblocked PRs by policy order, and emit JSON/human metrics.
4. Generate `docs/codex_handoff/pr_dag.mmd` from the validated backlog.
5. Sync `docs/codex_handoff/pr_status.yaml` and `machine_readable/pr_status.yaml`
   after marking PR-003 complete.

## Files changed

- `docs/PR_DELTAS/pr-003-dag-progress.md`
- `docs/codex_handoff/pr_dag.mmd`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/harness/VALIDATION_LEDGER.md`
- `scripts/codex_harness/validate_pr_dag.py`
- `scripts/codex_harness/progress_report.py`
- `scripts/codex_harness/test_pr_dag_harness.py`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` before implementation | repo root | FAIL | Red phase: four expected failures for missing policy-order rejection, Mermaid writer, unblocked ordering, and unknown status rejection. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` after reviewer edge-case tests | repo root | FAIL | Red phase: two expected failures for non-mapping `policy` and empty-DAG progress reporting. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pr_dag_harness.py -q` | repo root | PASS | `6 passed`. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --write-mermaid docs/codex_handoff/pr_dag.mmd` | repo root | PASS | `OK: 62 PRs, DAG valid`; generated PR-card Mermaid graph. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`; policy order begins `PR-000,PR-001,PR-003,PR-002`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml` | repo root | PASS | After status update: `Completed 3/62 = 4.84%`; unblocked next `PR-002, PR-004, PR-005`; checkpoint not due. |
| `python scripts/codex_harness/progress_report.py machine_readable/pr_backlog.yaml machine_readable/pr_status.yaml --json` | repo root | PASS | Same count, dependency-weighted, critical-path, and unblocked metrics as docs status. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; echo status_cmp=$?` | repo root | PASS | `status_cmp=0`. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6813 tests collected`; existing unknown marker warnings remain for PR-002 taxonomy. |
| Scoped forbidden-claim `rg` over PR-003 files | repo root | PASS | No forbidden-risk phrases in changed PR-003 files. |

## Review findings and fixes

- Finding: `docs/codex_handoff/pr_dag.mmd` was missing. Fix: add
  reproducible Mermaid generation through `validate_pr_dag.py --write-mermaid`.
- Finding: `progress_report.py` listed unblocked PRs in raw file order. Fix:
  order unblocked PRs by validated `policy.topological_order`.
- Finding: status files could contain unknown ids or dependency-incomplete
  completed ids. Fix: reject unknown `completed`, unknown `blocked`,
  completed/blocked overlap, invalid `in_progress`, and completed PRs whose
  dependencies are incomplete.
- Finding: docs and machine-readable status snapshots had drifted. Fix: sync
  both files after marking PR-003 complete.
- Finding: malformed non-mapping `policy` payloads were silently ignored. Fix:
  reject non-mapping policy values and add a regression test.
- Finding: an empty but schema-valid DAG could crash progress reporting. Fix:
  report an empty critical path with zero percentages and add a regression test.

## Claim hygiene and scientific scope

PR-003 is COMMON L0 bookkeeping. It checks graph structure and status hygiene,
then computes reproducible DAG-card progress. It does not validate solver
behavior, transfer functions, HTT likelihoods, posterior/evidence behavior, MIO
diagnostics, obsstat features, null calibration, morphology, or Bianchi family
identification.

Percent complete counts completed DAG cards only. It is not evidence of solver
validity, native transfer readiness, rank sufficiency, null calibration,
statistical adequacy, or publication readiness.

## Residual risks

- `progress_report.py` now reports a critical-path metric, but PR-005 still owns
  five-PR checkpoint files and adaptive replan protocol output.
- Existing `03_PR_dependency_graph.mmd` and `.dot` remain historical graph
  artifacts; `docs/codex_handoff/pr_dag.mmd` is the PR-003 generated artifact.
- Full repository tests were not run; PR-003 verified focused harness tests and
  the PR-card commands.

## Commit

Commit message:

`PR-003: harden DAG progress harness`
