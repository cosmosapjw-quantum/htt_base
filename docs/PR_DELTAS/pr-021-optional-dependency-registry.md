# PR-021 PR delta: optional dependency registry and skip-audit report

## Goal

Add COMMON L1 harness infrastructure that records optional dependency
availability and makes dependency-caused skips attributable. This is
machine-local harness provenance only. It does not validate native solver
behavior, transfer calibration, HTT posterior/evidence, MIO diagnostics, null
adequacy, morphology compatibility, production readiness, or
family-identification evidence.

The existing `docs/PR_DELTAS/pr-021.md` is stale material from an older PR
numbering scheme and was not used as active evidence for this DAG PR.

## Evidence read

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml` PR-021 card
- `docs/codex_handoff/pr_status.yaml`
- `htt/conftest.py`
- `pytest.ini`
- `htt/pytest.ini`
- `htt/pyproject.toml`
- `scripts/codex_harness/test_pytest_taxonomy.py`
- `htt/bass/forward/test_map_producer.py`
- `htt/bass/inference/test_fb113_bayes_factor_skeleton.py`
- `htt/bass/spectrum/test_flrw_external_camb.py`
- `htt/bass/perturbation/test_fb53_regular_adiabatic_ic_skeleton.py`
- `docs/generated/test_command_matrix.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`

## Web/doc checks

- WEB_CHECK_STATUS: done
- Python `importlib.util.find_spec` documentation checked for module
  discoverability probes.
  URL: https://docs.python.org/3/library/importlib.html
- Pytest skip documentation checked for the semantics of skips under unmet
  conditions.
  URL: https://docs.pytest.org/en/stable/how-to/skipping.html
- Pytest output/report documentation checked for short skip/fail summary
  attribution.
  URL: https://docs.pytest.org/en/stable/how-to/output.html

## Subagent divergence

- code_cartographer:
  - Steelman: add a small COMMON registry and report; keep marker-backed skips
    limited to existing `requires_healpy` and `requires_dynesty`.
  - Attack: do not append to stale `docs/PR_DELTAS/pr-021.md`; include
    `astropy` and `camb` as reportable dependencies even without pytest
    markers.
- harness_engineer:
  - Steelman: deterministic CLI with `--dry-run`, `--output`, Markdown
    metadata, and unit tests with injectable probes.
  - Attack: conftest must import the registry only after `htt/src` is on
    `sys.path`; collection hooks cannot rescue bad top-level imports.
- physics_stat_auditor:
  - Steelman: dependency status improves reproducibility before native solver
    arrival.
  - Attack: skipped optional tests are non-run coverage or blockers, not
    validation evidence.
- claim_gate_reviewer:
  - Steelman: safe wording is COMMON L1 harness/reporting infrastructure.
  - Attack: avoid any language implying optional dependency presence validates
    maps, evidence, sky support, transfers, MIO certificates, or family
    compatibility.
- regression_tester:
  - Steelman: simulate dependency states through injectable probes instead of
    relying on the local environment.
  - Attack: `find_spec()` proves discoverability only; the report should remain
    availability provenance, not import-health certification.

## Chosen plan

1. Add failing PR-021 tests in `tests/contracts/test_optional_dependencies.py`.
2. Add `common.optional_dependencies` with immutable registry rows, marker
   mapping, and injectable status scans.
3. Make `htt/conftest.py` consume the common marker registry without changing
   skip reason strings.
4. Add `scripts/codex_harness/optional_dep_report.py` with deterministic
   Markdown output, `--output`, and `--dry-run`.
5. Generate `docs/generated/optional_dependency_status.md` with required
   artifact metadata and explicit claim caveats.
6. Run focused PR-card tests, prior taxonomy tests, optional marker collection,
   smoke/package subsets, DAG/status checks, and claim scanners.

## Files changed

- `htt/src/common/optional_dependencies.py`
- `htt/conftest.py`
- `scripts/codex_harness/optional_dep_report.py`
- `docs/generated/optional_dependency_status.md`
- `tests/contracts/test_optional_dependencies.py`
- `docs/PR_DELTAS/pr-021-optional-dependency-registry.md`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/harness/VALIDATION_LEDGER.md`
- `docs/harness/PROJECT_STATE.md`
- `docs/harness/NEXT_SESSION_PROMPT.md`
- `docs/harness/BLOCKERS.md`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | ---: | --- |
| `venv/bin/python -m pytest tests/contracts/test_optional_dependencies.py -q` before implementation | repo root | FAIL | Red phase: missing `common.optional_dependencies` and missing `optional_dep_report.py`. |
| `python scripts/codex_harness/optional_dep_report.py --dry-run` before implementation | repo root | FAIL | Red phase: report script absent. |
| `venv/bin/python -m pytest tests/contracts/test_optional_dependencies.py -q` | repo root | PASS | `5 passed`; registry, injected missing/present statuses, conftest registry use, report metadata, and dry-run. |
| `python scripts/codex_harness/optional_dep_report.py --dry-run` | repo root | PASS | Prints default report path and report body using `/usr/bin/python`; `dynesty` is reported missing in that interpreter. |
| `python scripts/codex_harness/optional_dep_report.py` | repo root | PASS | Wrote `docs/generated/optional_dependency_status.md`; no diff after immediate regeneration. |
| `venv/bin/python -m py_compile htt/src/common/optional_dependencies.py scripts/codex_harness/optional_dep_report.py htt/conftest.py` | repo root | PASS | Touched Python modules compile. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `8 passed`; marker taxonomy and named skip reasons preserved. |
| `venv/bin/python -m pytest --collect-only -q tests/contracts scripts/codex_harness/test_pytest_taxonomy.py` | repo root | PASS | `30 tests collected`. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6799/6858 tests collected (59 deselected)`. |
| `venv/bin/python -m pytest -m "requires_healpy or requires_dynesty" --collect-only -q` | repo root | PASS | `23/6858 tests collected`; optional marker collection remains attributable. |
| `venv/bin/python -m pytest -m smoke -q` | repo root | PASS | `6 passed, 6852 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; runner child exit code preserved. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect --dry-run` | repo root | PASS | Prints venv-backed collect command. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke --dry-run` | repo root | PASS | Prints venv-backed smoke command. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-021 docs> && python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-021 docs>` | repo root | PASS | No forbidden claim patterns or unmarked strong claims detected. |
| `git diff --check -- <PR-021 files>` | repo root | PASS | No whitespace errors in scoped PR-021 diff. |

## Claim hygiene and scientific scope

Numerical/scientific impact: none; registry/reporting harness only.

Artifact/claim-tier impact: COMMON L1 diagnostic-only generated report. The
report records local availability for `healpy`, `dynesty`, `astropy`, and
`camb`, plus skip/report attribution paths. Missing dependencies are skip
causes or documented blockers. Present dependencies are availability
provenance only.

This PR does not create or validate native solver outputs, transfer
calibration, HTT posterior/evidence, MIO diagnostic adequacy, null/mock/covariance
adequacy, sky-support validity, morphology compatibility, or
family-identification evidence.

## Residual risks

- `importlib.util.find_spec` checks module discoverability, not ABI/import
  health. A future PR can add optional safe import probes if needed.
- `camb` and `astropy` are reported as documented-blocker dependencies rather
  than marker-backed pytest skip dependencies. Adding markers for them would be
  a separate taxonomy change.
- The generated report is machine-local and intentionally records
  `worktree_state: dirty` because unrelated files were already dirty in this
  workspace.
