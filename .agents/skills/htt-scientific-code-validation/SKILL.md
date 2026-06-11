---
name: htt-scientific-code-validation
summary: Validate scientific code, tests, numerical artifacts, and generated result packs in the HTT/MIO/BASS pre-solver repo.
description: Use after edits to Python/Rust/scientific scripts, tests, numerical artifacts, generated figures, transfer adapters, local/global discrimination code, MIO reports, obsstat features, or validation harnesses.
---

# HTT Scientific Code Validation Skill

## Purpose

Prevent fake validation, numerical drift, hidden calibration, and premature research claims.

## Validation hierarchy

Use the smallest relevant command first, but record skipped broader checks honestly.

1. Import/collection smoke: `python -m pytest --collect-only` for touched package.
2. Unit tests for touched module.
3. Contract/claim firewall tests.
4. Numerical invariant tests.
5. Result-pack regeneration tests.
6. Manuscript/figure provenance checks.

## Required workflow

1. Classify the change: contracts, harness, docs, numerical method, physics model, inference, MIO diagnostic, obsstat feature, plotting, manuscript.
2. Identify affected owners: `common`, `obsstat`, `bass_py`, `htt`, `mio`, `tsc_legacy`, manuscript.
3. Identify the exact validation commands.
4. Run them when possible. If not run, state why.
5. Capture command, cwd, return code, stdout/stderr tail, and time.
6. Check for mock/demo result leakage.
7. Check transfer provenance and claim tier.
8. Update `docs/harness/VALIDATION_LEDGER.md` or generated validation artifacts.

## HTT-specific validation commands

Prefer these patterns, adapted to the actual repo layout:

```bash
python -m pytest --collect-only
python -m pytest tests/contracts -q
python -m pytest tests/common -q
python -m pytest mio/tests -q
python -m pytest htt/tests -q
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml
python .agents/skills/htt-scientific-code-validation/scripts/check_no_mock_results.py
```

## Required output

```markdown
## Validation summary

## Changed files

## Commands run
| Command | CWD | Result | Notes |
|---|---|---:|---|

## Numerical/scientific impact

## Artifact/claim-tier impact

## Failures and skipped checks

## Remaining risks

## Next validation step
```

## Hard prohibitions

- Never claim a test passed without running it.
- Never silently relax tolerances.
- Never treat demo/smoke artifacts as publication-grade evidence.
- Never hide external transfer dependence.
- Never overwrite reference artifacts without a manifest and explanation.
