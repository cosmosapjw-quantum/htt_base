# PR-002 PR delta: pytest taxonomy and optional-dependency skip gates

## Goal

Register the repository pytest marker taxonomy at both checkout entry points and
make optional dependency handling explicit enough that missing `healpy` or
`dynesty` can skip marked tests with dependency-named reasons instead of
producing collection-time import failures or silent omissions.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml` PR-002 card
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `htt/pyproject.toml`
- `htt/conftest.py`
- `htt/bass/forward/test_map_producer.py`
- `htt/bass/inference/test_fb113_bayes_factor_skeleton.py`
- `htt/bass/perturbation/test_fb53_regular_adiabatic_ic_skeleton.py`
- `htt/bass/validation/test_d2_regression_anchor.py`

## Web/doc checks

- WEB_CHECK_STATUS: done
- pytest custom marker documentation: markers should be registered in pytest
  configuration to avoid unknown-marker warnings and make selection stable.
  URL: https://docs.pytest.org/en/stable/example/markers.html
- pytest marker how-to: marker expressions such as `-m smoke` select tests by
  registered marker names.
  URL: https://docs.pytest.org/en/stable/how-to/mark.html
- pytest skipping documentation: optional implementation/import tests can use
  `pytest.importorskip` to skip when an import is unavailable.
  URL: https://docs.pytest.org/en/stable/how-to/skipping.html
- pytest reference: `pytest.importorskip` accepts a `reason` argument.
  URL: https://docs.pytest.org/en/7.1.x/reference/reference.html

## Subagent divergence

- code_cartographer:
  - Steelman: add marker definitions where pytest actually reads config from
    repo root and from `htt/`; keep `htt/pyproject.toml` in sync for explicit
    config invocations.
  - Attack: a nested-only config would leave root PR-card commands with unknown
    markers, while a root-only config would not cover `cd htt` workflows.
- harness_engineer:
  - Steelman: create a focused taxonomy regression test that fails before the
    marker and skip gates exist, then run the PR-card smoke and collect-only
    commands through the project venv.
  - Attack: broad skips or unmarked importorskip calls can hide dependency
    coverage loss; every skip path must name the missing package.
- physics_stat_auditor:
  - Steelman: a deterministic smoke subset helps later scientific PRs separate
    harness health from numerical validation.
  - Attack: `smoke`, `fast`, and `collect-only` are not evidence for solver
    correctness, transfer validity, HTT posterior adequacy, MIO certificate
    validity, null calibration, or morphology compatibility.
- claim_gate_reviewer:
  - Steelman: safe wording is L0 test taxonomy and explicit optional-dependency
    skip policy.
  - Attack: reject wording that treats optional-dependency skips as validation
    or uses smoke passing as publication readiness.
- regression_tester:
  - Steelman: the smallest meaningful suite is a taxonomy test plus the PR-card
    smoke and collect-only commands.
  - Attack: the literal host `python` commands still fail because `/usr/bin/python`
    has no pytest; record that instead of implying global environment support.

## Chosen plan

1. Add root `pytest.ini` and nested `htt/pytest.ini` with `smoke`, `fast`,
   `slow`, `requires_healpy`, `requires_dynesty`, `anchor`, `verification`, and
   `ci` markers while preserving `test_*.py` and `*_test.py` discovery.
2. Keep `htt/pyproject.toml` marker metadata aligned for callers using
   `-c htt/pyproject.toml`.
3. Add collection-time optional dependency skip handling in `htt/conftest.py`.
4. Mark the existing D2 anchor regression file as `fast` and `smoke` so the
   PR-card smoke command runs a real deterministic subset.
5. Gate direct `healpy` and `dynesty` tests with dependency-named skip reasons.
6. Add a focused regression test for marker registration, smoke/collect-only
   warnings, direct optional-dependency hook behavior, pyproject alignment, and
   optional dependency gate text.

## Files changed

- `pytest.ini`
- `htt/pytest.ini`
- `htt/pyproject.toml`
- `htt/conftest.py`
- `htt/bass/validation/test_d2_regression_anchor.py`
- `htt/bass/forward/test_map_producer.py`
- `htt/bass/inference/test_fb113_bayes_factor_skeleton.py`
- `htt/bass/perturbation/test_fb53_regular_adiabatic_ic_skeleton.py`
- `scripts/codex_harness/test_pytest_taxonomy.py`
- `docs/PR_DELTAS/pr-002-test-taxonomy.md`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/harness/VALIDATION_LEDGER.md`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `venv/bin/python -m pytest scripts/codex_harness/test_pytest_taxonomy.py -q` before implementation | repo root | FAIL | Red phase: five expected failures for missing root/nested configs, unknown marker warnings, zero smoke tests, and missing optional dependency gate text. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `8 passed`; includes direct optional-dependency hook behavior with monkeypatched missing deps. |
| `venv/bin/python -m pytest -m smoke -q` | repo root | PASS | `6 passed, 6815 deselected`; L0 smoke reachability only. |
| `venv/bin/python -m pytest --collect-only -q` | repo root | PASS | `6762/6821 tests collected (59 deselected)` under default `not slow` addopts; no unknown marker warnings. |
| `venv/bin/python -m pytest -m "fast and not slow" -q` | repo root | PASS | `6 passed, 6815 deselected`. |
| `venv/bin/python -m pytest -m "requires_healpy or requires_dynesty" --collect-only -q` | repo root | PASS | `23/6821 tests collected (6798 deselected)`; marker selection is recognized. |
| `cd htt && ../venv/bin/python -m pytest -m smoke -q` | `htt/` | PASS | `6 passed, 6781 deselected`; nested config entry point works. |
| `python -m pytest -m smoke -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; literal host interpreter lacks pytest. |
| `python -m pytest --collect-only -q` | repo root | FAIL | `/usr/bin/python: No module named pytest`; use the project venv or activate an environment. |

## Review findings and fixes

- Finding: repo-root pytest commands did not read `htt/pyproject.toml`, leaving
  `smoke`, `fast`, `requires_healpy`, and `requires_dynesty` undefined. Fix:
  add root `pytest.ini`.
- Finding: `cd htt` workflows still needed local marker registration. Fix: add
  nested `htt/pytest.ini`.
- Finding: an explicit `python_files = test_*.py` setting would narrow pytest's
  default discovery and ignore tracked `*_test.py` modules. Fix: include both
  `test_*.py` and `*_test.py` in root and nested configs and assert this in the
  taxonomy regression test.
- Finding: optional dependency skip behavior was initially guarded only by
  static source-text assertions. Fix: add a direct hook test that loads
  `htt/conftest.py`, monkeypatches dependency availability to false, and
  verifies dependency-named skip reasons for `requires_healpy` and
  `requires_dynesty`.
- Finding: `htt/pyproject.toml` marker metadata could drift from the new
  configs. Fix: assert required markers and discovery patterns against
  `htt/pyproject.toml` in the taxonomy regression test.
- Finding: direct `healpy` import in `test_map_producer.py` could fail at
  collection before pytest could express the dependency. Fix: use
  dependency-named `pytest.importorskip` and mark the module
  `requires_healpy`.
- Finding: the dynesty cross-check had no explicit optional dependency marker.
  Fix: mark it `requires_dynesty` and add an import gate with a dynesty-specific
  reason.
- Finding: the CAMB fixture skipped without saying which dependency was absent.
  Fix: add a dependency-named `reason`.
- Finding: the smoke selector had no deterministic repository-local test body.
  Fix: mark the D2 regression anchor module as `fast` and `smoke`.

## Claim hygiene and scientific scope

PR-002 is COMMON L0 test harness taxonomy. It does not change production
scientific algorithms, transfer functions, solver behavior, HTT likelihoods,
posterior/evidence semantics, MIO diagnostics, obsstat feature extraction, null
mock calibration, or manuscript results.

Passing `smoke` and `collect-only` means the configured test harness can select
and import the checked subset. It is not evidence of native solver readiness,
transfer validation, posterior adequacy, diagnostic certificate validity,
morphology compatibility, or Bianchi family identification.

## Residual risks

- The active venv was not modified by uninstalling optional dependencies. The
  no-dependency branch is covered by a direct hook test with monkeypatched
  dependency availability.
- The literal `/usr/bin/python` PR-card commands still fail because that
  interpreter has no pytest installed. PR-001 already recorded the venv
  interpreter policy.
- Full test execution was not run; PR-002 verified focused taxonomy tests,
  smoke/fast marker selection, optional dependency marker selection, and
  collect-only.

## Commit

Commit message:

`PR-002: register pytest taxonomy`
