# PR-001 PR delta: Editable install and import-path stabilization

## Goal

Stabilize the editable install and public import surface for the existing
`htt/` Python layout without renaming public packages or changing scientific
behavior. PR-001 fixes package metadata, exposes the legacy nested `htt.*`
compatibility package through the active editable install, and documents the
host interpreter policy that affects the literal system-Python command.

## Evidence read

- `docs/codex_handoff/pr_backlog.yaml` PR-001 card
- `docs/codex_handoff/pr_status.yaml`
- `docs/PR_DELTAS/pr-000-intake.md`
- `htt/pyproject.toml`
- `htt/conftest.py`
- `htt/htt/__init__.py`
- `htt/htt/htt/__init__.py`
- `htt/htt/setup.py`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.codex/agents/*.toml`

## Web/doc checks

- WEB_CHECK_STATUS: done
- pip build-system documentation: editable installs for `pyproject.toml` builds use the PEP 660 editable wheel hook.
  URL: https://pip.pypa.io/en/stable/reference/build-system/
- PEP 668 documents externally managed base environments and says tools should guide users toward virtual environments unless explicitly overridden.
  URL: https://peps.python.org/pep-0668/
- PEP 440 defines Python distribution version identifiers; the previous `0.8.2-w8-02` form was rejected by setuptools, while `0.8.2+w8.2` is accepted as a local version.
  URL: https://peps.python.org/pep-0440/

## Subagent divergence

- code_cartographer:
  - Steelman: the install story should expose `bass`, `tsc`, `common`, `mio`, `workspace`, and compatible `htt.*` imports from repo root and temp cwd without pytest `conftest.py` path mutation.
  - Attack: the active `pyproject.toml` excluded `htt*`; the existing venv had stale nested-`htt` state, so clean temp-venv proof was required.
- harness_engineer:
  - Steelman: patch only package discovery and metadata; verify in an isolated venv and avoid relying on user-site installs.
  - Attack: do not hide install failures with broad `sys.path` hacks, skips, or persistent `--break-system-packages` config.
- physics_stat_auditor:
  - Steelman: import reproducibility enables later rank, null, transfer, HTT/MIO firewall, and claim-tier tests from clean environments.
  - Attack: packaging success is not solver, transfer, posterior, MIO diagnostic, rank, null, or family-identification validation.
- claim_gate_reviewer:
  - Steelman: safe wording is COMMON L0 packaging/import stabilization only.
  - Attack: reject any wording that turns collect-only into scientific validation or implies native solver readiness.
- regression_tester:
  - Steelman: minimum verification is editable install, collect-only, and temp-dir imports with the same interpreter and no `PYTHONPATH`.
  - Attack: repo-root/venv collection alone was masked by `htt/conftest.py` and stale editable state.

## Chosen plan

1. Add focused packaging tests in `htt/test_packaging_imports.py`.
2. Change `htt/pyproject.toml` version to PEP 440 local form `0.8.2+w8.2`.
3. Add `htt*` to package discovery so editable install exposes legacy HTT compatibility imports.
4. Add `matplotlib` and `PyYAML` to the `dev` extra because existing collected tests import them during collection.
5. Add a repo-root `htt/__init__.py` shim for outer-checkout shadowing.
6. Patch `htt/htt/__init__.py` so the installed nested wrapper exposes the inner `htt/htt/htt` package on `htt.__path__` before importing public `htt.core`, `htt.infer`, `htt.nulls`, and related subpackages.

## Files changed

- `htt/pyproject.toml`
- `htt/__init__.py`
- `htt/htt/__init__.py`
- `htt/test_packaging_imports.py`
- `docs/PR_DELTAS/pr-001-packaging.md`
- `docs/codex_handoff/pr_status.yaml`
- `docs/harness/VALIDATION_LEDGER.md`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `python -m pip install -e './htt[dev]'` | repo root | FAIL | `/usr/bin/python` is PEP 668 externally managed; no global override applied. |
| `python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; expected until a venv interpreter is active. |
| `python -m pip install --break-system-packages --dry-run -e './htt[dev]'` | repo root | PASS dry-run | Confirms repo metadata now builds; not used as a persistent install strategy. |
| `venv/bin/python -m pytest htt/test_packaging_imports.py -q` | repo root | PASS | `5 passed`, including repo-root and temp-cwd import probes with no `PYTHONPATH`. |
| `venv/bin/python -m pip install -e './htt[dev]'` | repo root | PASS | Built editable `bass-py-0.8.2+w8.2`. |
| `venv/bin/python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q` | repo root | PASS | `1541 tests collected`. |
| `venv/bin/python -m pip check` | repo root | PASS | No broken requirements found. |
| Clean venv with `PATH="$tmp/venv/bin:$PATH" python -m pip install -e './htt[dev]'` | repo root | PASS | PR-card command succeeds when `python` is an isolated venv interpreter. |
| Clean venv with `PATH="$tmp/venv/bin:$PATH" python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q` | repo root | PASS | `1541 tests collected`. |
| Clean venv with `PATH="$tmp/venv/bin:$PATH" python -m pytest htt/test_packaging_imports.py -q` | repo root | PASS | `5 passed`. |
| Clean venv temp-dir import probe | temp cwd | PASS | Imported `bass`, `common`, `mio`, `tsc`, `workspace`, `htt.core`, `htt.infer`, `htt.nulls`, and `htt.integration.to_mio` with no `PYTHONPATH`. |
| `python .agents/skills/htt-scientific-code-validation/scripts/check_no_mock_results.py` | repo root | FAIL | Pre-existing legacy/audit `calibration_factor` and mock-result mentions outside the PR-001 packaging diff; no PR-001 changed file was implicated. |
| `git diff --check -- <PR-001 files>` | repo root | PASS | No whitespace errors. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml` | repo root | PASS | `Completed 2/62 = 3.23%`; unblocked next `PR-002`, `PR-003`; checkpoint not due. |

## Validation summary

Change class: COMMON harness/packaging. Affected owners: COMMON package
contracts and HTT legacy compatibility imports. No numerical, solver, transfer,
likelihood, posterior, MIO diagnostic, or obsstat feature behavior was changed.

No generated science artifacts were created. No transfer source is exercised by
this PR. Claim tier impact is L0 infrastructure only.

## Review findings and fixes

- Finding: `htt/pyproject.toml` version `0.8.2-w8-02` was not PEP 440 and blocked editable builds. Fix: use local version `0.8.2+w8.2`.
- Finding: `htt*` was excluded from package discovery, so clean editable installs did not expose legacy HTT compatibility imports. Fix: include `htt*`.
- Finding: clean collection imported `matplotlib` and `yaml` at module-import time but `dev` installed only `pytest`. Fix: add `matplotlib>=3.8` and `PyYAML>=6.0` to `dev`.
- Finding: repo-root `import htt` resolved to the outer directory and shadowed the nested public HTT package. Fix: add `htt/__init__.py` shim and update nested wrapper path handling.
- Finding: temp-dir import behavior was manually verified but not regression-tested. Fix: add `test_temp_cwd_import_surface_without_pythonpath`.

## Claim hygiene and scientific scope

PR-001 stabilizes editable installation and import discovery for the existing
Python package layout. It documents nested package behavior and records
collect-only/import-path evidence.

This PR does not validate transfer functions, native solver outputs,
posterior/evidence behavior, MIO diagnostic certificates, TSC/Teff science
ownership, null calibration, rank adequacy, morphology, or Bianchi family
identification.

## Residual risks

- The host default `/usr/bin/python` remains externally managed by PEP 668. PR-card commands pass when `python` points to an active venv; forcing `/usr/bin/python` would require a user/system policy decision.
- `htt/htt/setup.py` remains as a legacy nested-package setup file. PR-001 preserves compatibility rather than deleting or renaming it.
- Full test execution was not run; PR-001 verified focused packaging tests, editable install, temp-dir imports, and collect-only.

## Commit

Commit message:

`PR-001: stabilize editable install imports`
