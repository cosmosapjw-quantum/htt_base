# REV-R081 - CF4 forward-likelihood adapter track

## Scope

- Owner: OBSSTAT for object-level CF4 catalog binding; HTT for the diagnostic score consumer.
- Plan source: `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`.
- Canonical PR DAG status is already complete at `62/62`; this is a supplemental revision delta and does not overwrite `docs/codex_handoff/pr_status.yaml`.
- Claim ceiling: `diagnostic_only`.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-observable-statistics/SKILL.md`
- `.agents/skills/htt-local-global-discrimination/SKILL.md`
- `.agents/skills/htt-physics-math-audit/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `htt/htt/htt/core/catalog_likelihood.py`
- `htt/htt/htt/infer/dipole_vector_likelihood.py`
- `htt/obsstat/observable_vector.py`
- `htt/obsstat/scalar_lowell.py`
- `htt/test_packaging_imports.py`
- `workdir/compact_products/cf4/query_batch.npz`

## Web/doc checks

- WEB_CHECK_STATUS: done.
- Python `dataclasses` docs checked for frozen dataclass validation and `__post_init__`: <https://docs.python.org/3/library/dataclasses.html>.
- Python `hashlib.sha256` docs checked for byte hashing: <https://docs.python.org/3/library/hashlib.html#hashlib.sha256>.
- Python `json` docs checked for JSON object loading behavior: <https://docs.python.org/3/library/json.html>.
- NumPy docs checked for `np.load(..., allow_pickle=False)`, `np.asarray`, `np.linalg.svd`, and vectorized linear algebra:
  <https://numpy.org/doc/stable/reference/generated/numpy.load.html>,
  <https://numpy.org/doc/stable/reference/generated/numpy.asarray.html>,
  <https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html>.

## Divergence and review

- code cartographer:
  - Steelman: put object-catalog schema under `obsstat.catalogs.cf4`, put HTT score code under `htt.rest_frame.cf4_likelihood`, and expose both through existing package shims.
  - Attack: compact CF4 query grids in `workdir/compact_products/cf4/query_batch.npz` are grid summaries with `sgx/sgy/sgz/vr_mean/vr_std`, not object catalogs; silent promotion must fail.
- harness engineer:
  - Steelman: red-test missing schema, malformed shapes, peculiar-velocity Gaussian gates, package imports, and hash provenance.
  - Attack: a green toy likelihood is insufficient if repo-root `from htt import *` does not expose `rest_frame` or if malformed `sha256:` strings pass.
- physics/statistics auditor:
  - Steelman: a distance-variable forward score is useful before native low-ell solver arrival if it stays diagnostic and keeps local/global vectors explicit.
  - Attack: diagonal independent noise, rank-deficient local/global/calibration design, and nonexistent Gaussian velocity manifests cannot support production likelihood, local/global interpretation, or exact peculiar-velocity Gaussian semantics.
- claim-gate reviewer:
  - Steelman: OBSSTAT validates features/catalog rows only; HTT returns a blocked diagnostic score payload with owner, claim tier, hashes, command, and caveats.
  - Attack: `allowed_use` must reject inference-like terms, input hashes must be real `sha256:[64 hex]`, and no native/family/morphology claim can leak into docs or payloads.
- regression tester:
  - Steelman: package import tests cover repo-root, temp-cwd, nested-cwd, and star-import behavior.
  - Attack: the initial failure was the repo-root `htt/__init__.py` shim, not the nested `htt/htt/htt/__init__.py`; root lazy export was required.

Subagents closed: yes. Completed review agents were closed after findings were patched.

## Implemented changes

- Added `obsstat.catalogs.cf4`:
  - object-level CF4-like schema requirements,
  - checksum and metadata validation,
  - byte-bound `.npz` checksum validation,
  - no compact-grid promotion,
  - readable Gaussian velocity manifest validation for exact peculiar-velocity Gaussian semantics,
  - strict Gaussian noise-model labels,
  - OBSSTAT allowed-use claim firewall.
- Added `htt.rest_frame.cf4_likelihood`:
  - diagonal diagnostic distance-variable Gaussian score,
  - strict `sha256:[64 hex]` config/input hashes,
  - response-rank audit over local-flow, global-vector, and calibration columns,
  - explicit blockers for rank, covariance, local/global overlap, matched nulls, PPC, and LOOCV.
- Updated package import surfaces:
  - `htt/__init__.py`
  - `htt/htt/__init__.py`
  - `htt/htt/htt/__init__.py`
  - `htt/obsstat/__init__.py`
  - `htt/test_packaging_imports.py`
- Added design artifact:
  - `docs/generated/cf4_forward_likelihood_design.md`

## Artifact metadata

- owner: HTT / OBSSTAT
- implementation_scope: `obsstat` catalog contract plus `htt` diagnostic score
- claim_tier: `diagnostic_only`
- transfer_source: `none`
- sky_support_status: `cf4_object_catalog_coordinates_required`
- null_mock_status: `not_statistical`
- covariance_status: `diagonal_only_no_group_method_covariance`
- config_hash: `sha256:33d2c8dc9cd21399beb1618d59d4fc41bb8fa63b0f6619906765a9d86d2b79a5`
- input_hashes:
  - `sha256:c681cef2a8b3d3bc7551cf4cf42134b0b6ea35ef9ef2c4f0af9635885d4bf13a`
  - `sha256:e59353019191d5c0cd7c448e9105db9295896c080cf6ae58e918d0b5f37feb30`
  - `sha256:4257f3305dd284bf9a08fbb9665833c4c810bb77415ca419bb6e92b2abde6c94`
- generating_command: `Codex apply_patch REV-R081; focused pytest and claim scan commands below`
- git_commit_or_worktree_state: `431026f+dirty`

## Validation

| Command | Result | Notes |
|---|---:|---|
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_cf4_catalog_adapter.py tests/htt/test_cf4_likelihood.py` | PASS | `20 passed`; includes red-to-green tests for manifest, byte-bound catalog checksums, strict Gaussian labels, hashes, allowed-use, rank blockers. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/obsstat/test_cf4_catalog_adapter.py tests/htt/test_cf4_likelihood.py htt/test_packaging_imports.py` | PASS | `32 passed`; CF4 plus package import surfaces. |
| `venv/bin/python -B -m py_compile htt/__init__.py htt/htt/__init__.py htt/htt/htt/__init__.py htt/obsstat/__init__.py htt/obsstat/catalogs/__init__.py htt/obsstat/catalogs/cf4.py htt/htt/htt/rest_frame/__init__.py htt/htt/htt/rest_frame/cf4_likelihood.py tests/obsstat/test_cf4_catalog_adapter.py tests/htt/test_cf4_likelihood.py htt/test_packaging_imports.py` | PASS | Touched Python files compile. |
| `venv/bin/python -B scripts/check_claim_language.py --dry-run htt/__init__.py htt/htt/__init__.py htt/htt/htt/__init__.py htt/obsstat/__init__.py htt/obsstat/catalogs/__init__.py htt/obsstat/catalogs/cf4.py htt/htt/htt/rest_frame/__init__.py htt/htt/htt/rest_frame/cf4_likelihood.py htt/test_packaging_imports.py tests/obsstat/test_cf4_catalog_adapter.py tests/htt/test_cf4_likelihood.py docs/generated/cf4_forward_likelihood_design.md` | PASS | No forbidden claim language detected. |
| `venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | PASS | `OK: 62 PRs, DAG valid`. |
| `git diff --check` | PASS | No whitespace errors. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -m smoke -q` | PASS | `6 passed, 7571 deselected`. |
| `venv/bin/python -B -m pytest -p no:cacheprovider --collect-only -q` | PASS | `7518/7577 tests collected (59 deselected)`. |

## Claim-tier impact

This revision creates no HTT evidence, no posterior odds, no native solver result, no morphology atlas result, and no Bianchi family-identification support. It adds a schema-bound CF4 catalog lane and a blocked diagonal diagnostic score lane.

Residual blockers:

- production object-level CF4 catalog binding not present,
- matched nulls not bound,
- publication-grade covariance not bound,
- group/method/calibration-correlated covariance not bound,
- local/global response overlap not externally audited,
- rank-deficient response designs marked no-claim,
- PPC and LOOCV not bound.
