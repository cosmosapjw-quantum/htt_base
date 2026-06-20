# REV-R082 - Spectroscopic data-random dipole estimator contracts

## Scope

- Owner: OBSSTAT.
- Plan source: `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`.
- Canonical PR DAG status is already complete at `62/62`; this is a supplemental revision delta and does not overwrite `docs/codex_handoff/pr_status.yaml`.
- Claim ceiling: `diagnostic_only`.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-observable-statistics/SKILL.md`
- `.agents/skills/htt-local-global-discrimination/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/generated/data_binding_gap_report.md`
- `docs/generated/research_program_experiment_registry.yaml`
- `htt/src/common/data_contracts.py`
- `htt/obsstat/catalogs/cf4.py`
- `htt/obsstat/__init__.py`
- `htt/obsstat/catalogs/__init__.py`
- `htt/test_packaging_imports.py`

## Web/doc checks

- WEB_CHECK_STATUS: done.
- NumPy `average` documentation checked for weighted-average behavior: <https://numpy.org/doc/stable/reference/generated/numpy.average.html>.
- NumPy `histogram` documentation checked for weight-array semantics used by future binning/null extensions: <https://numpy.org/doc/stable/reference/generated/numpy.histogram.html>.
- von Hausegger and Dalang, Phys. Rev. D 111, 123547 checked for observed-redshift selection correction motivation: <https://link.aps.org/doi/10.1103/PhysRevD.111.123547>.

## Divergence and review

- code cartographer:
  - Steelman: keep the estimator in OBSSTAT, add schema/feature modules with package alias wiring, and avoid HTT likelihood/MIO certificate surfaces.
  - Attack: dropping REV-R081 CF4 exports or relying only on direct imports would create package-surface regressions; direct module tests are not enough.
- harness engineer:
  - Steelman: red-test missing modules, then validate focused estimator tests, package imports, claim scanner, smoke, and collect-only.
  - Attack: generated docs and PR delta were absent initially; tests must assert full artifact metadata, not only the dipole vector.
- physics/statistics auditor:
  - Steelman: data-random first moment is a useful pre-production feature if data/random parity, alpha definition, weights, and redshift-selection metadata are explicit.
  - Attack: no p-values, local/global interpretation, or production use is justified without certified randoms/masks, selection weights, covariance, nulls, PPC/LOOCV, and rank/response gates.
- claim-gate reviewer:
  - Steelman: safe language is “OBSSTAT feature only” and “metadata/toy correction hook”, with `publication_ready=false`.
  - Attack: toy fixtures must not become an observed dipole result, HTT evidence, MIO posterior/certificate, native solver validation, or family/geometry claim.
- regression tester:
  - Steelman: protect REV-R081 by extending `obsstat.catalogs` exports and package import smoke rather than replacing them.
  - Attack: top-level `obsstat.*` and `htt.obsstat.*` aliases can diverge if submodule aliasing is not updated.

Subagents closed: pending at implementation time; close after post-fix review.

## Implemented changes

- Added `obsstat.catalogs.redshift_selection`:
  - observed-redshift correction metadata,
  - strict `sha256:[64 hex]` config/input hashes,
  - bound/not-bound status and blockers,
  - toy correction hook for tests only that does not close the survey-specific blocker,
  - von Hausegger-Dalang reference metadata.
- Added `obsstat.catalogs.spectroscopic_dipole`:
  - spectroscopic data/random catalog schemas,
  - release/tracer/region/bin parity checks,
  - finite coordinate/redshift/weight validation,
  - weighted first-moment estimator,
  - data-random feature payload with alpha and weight provenance,
  - diagnostic-only blockers for random/mask certification, nulls, covariance, systematics, PPC, and LOOCV.
- Updated package import surfaces:
  - `htt/obsstat/catalogs/__init__.py`
  - `htt/obsstat/__init__.py`
  - `htt/test_packaging_imports.py`
- Added tests:
  - `tests/obsstat/test_redshift_selection.py`
  - `tests/obsstat/test_spectroscopic_dipole.py`
- Added design artifact:
  - `docs/generated/spectroscopic_dipole_design.md`

## Artifact metadata

- owner: OBSSTAT
- implementation_scope: `obsstat`
- claim_tier: `diagnostic_only`
- transfer_source: `none`
- sky_support_status: `data_random_sky_coordinates_bound`
- mask_status: `random_catalog_bound_mask_not_certified`
- null_mock_status: `not_bound`
- covariance_status: `not_bound`
- production_status: `diagnostic_only`
- config_hash: `sha256:1d914b2c8694222f3cd852b2baf64669a62d9c568e75e76d7f3f8367f053bfb9`
- input_hashes:
  - `sha256:c681cef2a8b3d3bc7551cf4cf42134b0b6ea35ef9ef2c4f0af9635885d4bf13a`
  - `sha256:390ea1e2cb035745a40b23f0cd6b50cb4bbb7641afecde515d0048d23e7bce37`
  - `sha256:1618002933e3e939abf7b1a9304711eb6587ddf5f74f5a1ff0bec389671f71a0`
- generating_command: `Codex apply_patch REV-R082; focused pytest and claim scan commands below`
- git_commit_or_worktree_state: `586c4c0+dirty`

## Validation

| Command | Result | Notes |
|---|---:|---|
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_spectroscopic_dipole.py tests/obsstat/test_redshift_selection.py` before implementation | FAIL | Red phase: `7 failed`, missing planned modules. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_spectroscopic_dipole.py tests/obsstat/test_redshift_selection.py htt/test_packaging_imports.py` | PASS | `19 passed`; estimator, correction metadata, and package imports. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat` | PASS | `84 passed`; OBSSTAT package regression suite. |
| `venv/bin/python -B -m py_compile htt/obsstat/catalogs/spectroscopic_dipole.py htt/obsstat/catalogs/redshift_selection.py htt/obsstat/catalogs/__init__.py htt/obsstat/__init__.py htt/test_packaging_imports.py tests/obsstat/test_spectroscopic_dipole.py tests/obsstat/test_redshift_selection.py` | PASS | Touched Python files compile. |
| `venv/bin/python -B scripts/check_claim_language.py --dry-run htt/obsstat/catalogs/spectroscopic_dipole.py htt/obsstat/catalogs/redshift_selection.py htt/obsstat/catalogs/__init__.py htt/obsstat/__init__.py tests/obsstat/test_spectroscopic_dipole.py tests/obsstat/test_redshift_selection.py docs/generated/spectroscopic_dipole_design.md docs/PR_DELTAS/rev-r082.md` | PASS | No forbidden claim language detected. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_cf4_catalog_adapter.py tests/htt/test_cf4_likelihood.py htt/test_packaging_imports.py tests/contracts/test_data_contracts.py` | PASS | `44 passed`; protects REV-R081 and data readiness contracts. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -m smoke -q` | PASS | `6 passed, 7582 deselected`. |
| `venv/bin/python -B -m pytest -p no:cacheprovider --collect-only -q` | PASS | `7529/7588 tests collected (59 deselected)`. |
| `venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | PASS | `OK: 62 PRs, DAG valid`. |
| `git diff --check` | PASS | No whitespace errors. |

## Claim-tier impact

This revision creates no HTT evidence, no posterior odds, no MIO certificate, no native solver result, no observed dipole measurement claim, and no Bianchi family-identification support. It adds an OBSSTAT diagnostic feature lane and redshift-selection metadata needed before future raw-data analyses.

Residual blockers:

- random/mask certification not complete,
- certified selection weights not complete,
- matched nulls not bound,
- covariance not bound,
- survey systematics not bound,
- PPC/LOOCV not bound,
- survey-specific redshift-selection correction not bound for observed-redshift bins,
- response/rank and local/global interpretation gates not bound.
