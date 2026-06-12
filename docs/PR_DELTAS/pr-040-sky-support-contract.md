# PR-040 - Sky support, mask hash, and coordinate-frame contracts

Date: 2026-06-12

## PR card

- ID: `PR-040`
- Title: SkySupport, mask hash, and coordinate-frame contracts
- Owner: COMMON
- Dependencies: `PR-010`, `PR-021`
- Required test: `python -m pytest tests/htt/test_sky_support_contract.py -q`
- DoD:
  - Every sky-facing artifact records coordinate frame, mask hash, sky
    fraction, and completeness status.
  - Spherical means use unit vectors, never raw `mean(l), mean(b)`.
- Kill switch: reject if raw longitude/latitude means survive in production
  summaries.

## Evidence gathering

Repository evidence read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-observable-statistics/SKILL.md`
- `.agents/skills/htt-physics-math-audit/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml`
- `docs/codex_handoff/pr_status.yaml`
- `htt/src/common/AGENTS.md`
- `htt/src/common/contracts.py`
- `htt/src/common/sky_geometry.py`
- `htt/src/common/healpix_selection.py`
- `htt/src/common/artifact_manifest.py`
- `htt/workspace/contracts/preliminary_results.py`
- `htt/htt/htt/infer/axis_gate.py`
- `htt/htt/htt/infer/ver2_directional_shell.py`
- existing sky/manifest tests under `htt/src/common`, `tests/contracts`,
  `htt/mio/tests`, and `htt/htt/tests`

Documentation/web verification:

- Python `hashlib` docs verify `sha256()` hash objects and `hexdigest()` as
  the standard deterministic hexadecimal digest surface:
  https://docs.python.org/3/library/hashlib.html
- Python `dataclasses` docs verify generated methods and post-init validation
  on dataclass fields: https://docs.python.org/3/library/dataclasses.html
- HEALPix documentation confirms the equal-area sky-pixel premise used when
  interpreting a boolean equal-area mask fraction:
  https://healpix.sourceforge.io/

## Divergence and role review

- Code cartographer:
  - Steelman: harden the existing `common.contracts.SkySupport` SSoT because
    `ObservableVector`, HTT directional gates, workspace loaders, and MIO/BASS
    tests already consume it.
  - Attack: a second `SkySupport` schema in `common.sky_support` would split
    the contract and let artifacts satisfy one schema while consumers read
    another.
- Harness engineer:
  - Steelman: add the PR-card test path first and keep the verification
    battery focused on sky geometry, manifest validation, and directional
    shell consumers.
  - Attack: only running existing `test_sky_geometry.py` would prove the math
    helper but not the manifest/production-summary gate.
- Physics/statistics auditor:
  - Steelman: coordinate frame is sky-coordinate frame; mask fraction is an
    equal-area support fraction; spherical means must be resultant-vector
    means on the unit sphere.
  - Attack: `mock_coverage_status` is not completeness, and mask hash alone is
    not sufficient without frame and sky fraction.
- Claim-gate reviewer:
  - Steelman: any sky-facing diagnostic artifact must be coordinate-frame
    annotated and mask-hash tracked before it can be claim-bearing.
  - Attack: `sky_support_status: complete` without detailed support metadata
    hides the frame, mask, and sky fraction and should remain insufficient.
- Regression tester:
  - Steelman: test manifest sidecars, spherical direction math, and HTT/MIO
    directional consumers together.
  - Attack: full-suite-first would be noisy; targeted contract suites cover
    this PR's blast radius.

Subagents were closed after PR-040 review.

## Implementation

Changed files:

- `htt/src/common/sky_support.py`
- `htt/src/common/sky_geometry.py`
- `htt/src/common/contracts.py`
- `htt/src/common/artifact_manifest.py`
- `tests/htt/test_sky_support_contract.py`
- `tests/contracts/test_artifact_manifest.py`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/PR_DELTAS/pr-040-sky-support-contract.md`
- `docs/harness/VALIDATION_LEDGER.md`
- `docs/harness/PROJECT_STATE.md`
- `docs/harness/CLAIM_LEDGER.md`
- `docs/harness/DECISION_LOG.md`
- `docs/harness/NEXT_SESSION_PROMPT.md`
- `docs/harness/BLOCKERS.md`

Key changes:

- Added `common.sky_support` helpers:
  - deterministic SHA-256 mask hashes bound to mask bits, coordinate frame,
    pixelization, and optional `nside`;
  - equal-area sky-fraction calculation;
  - `build_sky_support_from_mask`;
  - `validate_sky_facing_artifact_metadata`.
- Extended canonical `common.contracts.SkySupport` with backward-compatible
  fields for coordinate frame, sky fraction, completeness status, pixelization,
  and `nside`, plus `to_metadata()`.
- Extended `common.sky_geometry.spherical_mean` outputs with
  `mean_method="unit_vector_resultant"`.
- Added `assert_no_raw_lonlat_mean_source` as an AST guard against
  production-facing raw longitude/latitude means.
- Tightened `common.artifact_manifest.validate_manifest_payload` so
  sky-facing statuses require PR-040 sky-support metadata; non-directional
  artifacts remain accepted with `sky_support_status: not_directional`.
- Bounded sky-facing `sky_support_status` vocabulary so over-strong status
  tokens such as `production_validated` cannot pass as sky-support metadata.

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | ---: | --- |
| `venv/bin/python -m pytest tests/htt/test_sky_support_contract.py -q` before implementation | repo root | FAIL | Red phase: missing `assert_no_raw_lonlat_mean_source` and `common.sky_support`. |
| `venv/bin/python -m pytest tests/htt/test_sky_support_contract.py -q` | repo root | PASS | `6 passed`; covers deterministic frame-bound mask hashes, equal-area sky fraction, support metadata, sky-facing metadata validation, unit-vector mean tagging, and raw lon/lat mean guard. |
| `venv/bin/python -m pytest tests/htt/test_sky_support_contract.py tests/contracts/test_artifact_manifest.py -q` | repo root | PASS | `19 passed`; PR-040 sky support and tightened manifest validation pass together. |
| `venv/bin/python -m pytest -q tests/contracts/test_artifact_manifest.py htt/src/common/test_sky_geometry.py htt/src/common/test_contracts.py htt/mio/tests/test_masked_sky_caveats.py htt/mio/tests/test_ver2_manifest_status.py htt/htt/tests/test_ver2_directional_shell.py` | repo root | PASS | `89 passed`; adjacent manifest, common, MIO masked-sky, MIO status, and HTT directional shell behavior preserved. |
| `venv/bin/python -m pytest htt/src/common -q` | repo root | PASS | `164 passed, 1 skipped`; full common package tests remain green. |
| `venv/bin/python -m pytest tests/contracts -q` | repo root | PASS | `60 passed`; top-level contract suite remains green. |
| `venv/bin/python -m py_compile htt/src/common/sky_support.py htt/src/common/sky_geometry.py htt/src/common/contracts.py htt/src/common/artifact_manifest.py tests/htt/test_sky_support_contract.py tests/contracts/test_artifact_manifest.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; package import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6896 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6843/6902 tests collected (59 deselected)`. |
| `venv/bin/python scripts/check_artifact_manifests.py --dry-run` | repo root | PASS | Exit 0; still reports 96 quarantined figures, 0 manifested figures, 0 manifest issues. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After marking PR-040 complete: `13/62 = 20.97%`; dependency-weighted `27.69%`; critical path `5/21 = 23.81%`; checkpoint not due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-040 files>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-040 docs>` before wording fix | repo root | FAIL | Flagged one full family-ID phrase without nearby status marker. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-040 docs>` after wording fix | repo root | PASS | No unmarked strong claims detected. |
| `git diff --check -- <PR-040 files>` | repo root | PASS | Scoped PR-040 diff has no whitespace errors. |
| `venv/bin/python -m pytest tests/htt/test_sky_support_contract.py tests/contracts/test_artifact_manifest.py -q` after reviewer fixes | repo root | PASS | `19 passed`; verifies bounded sky-facing status vocabulary and manifest compatibility. |
| `venv/bin/python -m pytest htt/src/common -q` after reviewer fixes | repo root | PASS | `164 passed, 1 skipped`; full common package tests remain green. |
| `venv/bin/python -m pytest tests/contracts -q` after reviewer fixes | repo root | PASS | `60 passed`; top-level contract suite remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` after reviewer fixes | repo root | PASS | `6 passed, 6896 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` after reviewer fixes | repo root | PASS | `6843/6902 tests collected (59 deselected)`. |

## Review findings and fixes

- Finding: PR-card tests alone would not prevent directional manifests from
  passing with only `sky_support_status`.
  - Fix: `validate_manifest_payload` now requires rich PR-040 sky-support
    metadata for sky-facing statuses.
- Finding: adding required `SkySupport` fields without defaults would break
  existing generated-artifact loaders.
  - Fix: canonical `SkySupport` accepts legacy defaults, while the new
    sky-facing metadata validator enforces required fields for directional
    artifacts.
- Finding: mask hashes could remain arbitrary prose if only the dataclass
  required non-empty strings.
  - Fix: `build_sky_support_from_mask` computes SHA-256 hashes from the mask
    payload and frame metadata; sky-facing validation requires `sha256:`.
- Finding: post-implementation review noted that the raw `SkySupport`
  docstring implied production use even though legacy defaults remain.
  - Fix: softened the dataclass docstring to "shared by sky-facing surfaces".
- Finding: post-implementation review noted that free-form
  `sky_support_status` could admit over-strong tokens once metadata existed.
  - Fix: sky-facing validation now accepts only bounded support-status
    vocabulary and rejects `production_validated`.

## Claim hygiene and scientific scope

Numerical/scientific impact: no solver, transfer, likelihood, posterior,
MIO diagnostic, null/mock/covariance, morphology atlas, or family-ID evidence
was generated.

Artifact/claim-tier impact: COMMON L2 contract/checker metadata. PR-040 makes
sky-facing metadata more auditable and blocks a known directional-summary
failure mode. Complete sky support does not imply null calibration, covariance
readiness, transfer validation, native solver validation, morphology
compatibility, or family-ID evidence.

## Residual risks

- Existing producers are not yet migrated to call
  `validate_sky_facing_artifact_metadata` at every artifact boundary.
- Legacy generated VER2 artifacts still load through backward-compatible
  `SkySupport` defaults where older payloads lack PR-040 fields.
- The raw-mean guard is an AST helper for production-summary source strings;
  broader repository-wide enforcement should be added when concrete production
  summary writers are migrated.
