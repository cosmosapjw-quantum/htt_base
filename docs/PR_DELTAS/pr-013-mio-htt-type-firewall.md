# PR-013 PR delta: MIO/HTT posterior-certificate type firewall

## Goal

Add a COMMON/HTT contract firewall that makes MIO diagnostic certificates
terminal diagnostic artifacts, not HTT likelihood/evidence inputs. This PR
adds an explicit `HTTPosteriorBundle`, a single allowed `HttLikelihoodTerm`
atom, and recursive rejection of direct, nested, and JSON-shaped MIO
diagnostic inputs.

This PR does not implement a native low-ell solver, change transfer
calibration, generate artifacts, merge MIO diagnostics into HTT evidence, or
make morphology/family claims.

## Evidence read

- `AGENTS.md`
- `docs/codex_handoff/pr_backlog.yaml` PR-013 card
- `docs/codex_handoff/pr_status.yaml`
- `htt/src/common/contracts.py`
- `htt/workspace/contracts/mio_certificate.py`
- `htt/workspace/contracts/htt_to_mio.py`
- `htt/htt/htt/infer/likelihood_scope_guard.py`
- `htt/mio/interface/htt_cross_check.py`
- `htt/workspace/contracts/tests/test_g19_enforcement.py`
- `htt/mio/tests/test_htt_cross_check.py`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `.agents/skills/htt-ssot-handoff-maintainer/SKILL.md`

## Web/doc checks

- WEB_CHECK_STATUS: done
- Python `dataclasses` documentation checked for frozen dataclass behavior
  and post-init initialization.
  URL: https://docs.python.org/3/library/dataclasses.html
- Python typing documentation checked for runtime limits of static type hints
  and protocol-like API shape. The final patch uses concrete runtime checks.
  URL: https://docs.python.org/3/library/typing.html
- Python `abc` documentation checked while considering abstract interfaces.
  The final patch did not add abstract base classes.
  URL: https://docs.python.org/3/library/abc.html

## Subagent divergence

- code_cartographer:
  - Steelman: add `workspace.contracts.htt_posterior` as the canonical
    PR-013 surface, preserve `PosteriorExportBundle` as cross-check-only, and
    export the new contract from `workspace.contracts`.
  - Attack: do not rename the existing HTT-to-MIO export, put posterior fields
    on `MioCertificate`, or treat static text scans as the only guard.
- harness_engineer:
  - Steelman: make `tests/contracts/test_mio_htt_no_merge.py` the focused RED
    suite and protect existing ownership, MIO certificate, HTT-to-MIO, and
    cross-check tests.
  - Attack: package smoke alone is insufficient because root smoke fails until
    the PR-013 target imports and collects cleanly.
- physics_stat_auditor:
  - Steelman: MIO certificates may expose diagnostics, p-values, residuals,
    adequacy flags, and cross-check hints, but those values must not enter HTT
    likelihood/evidence APIs.
  - Attack: object-only rejection is too weak; copied dict payloads and nested
    metadata keys must also fail.
- claim_gate_reviewer:
  - Steelman: HTT owns posterior/evidence semantics; MIO owns diagnostic
    certificates; cross-check tables remain report-only comparisons.
  - Attack: the prior G19 static lint used stale `bass_py/...` scan roots, so
    PR-013 needs a real-root scan over the current checkout.
- regression_tester:
  - Steelman: run focused PR-013 tests plus adjacent G19, cross-check,
    ownership, directional shell, package, smoke, collect, and contract suites.
  - Attack: do not treat package import checks as a substitute for root
    collection or the PR-card tests.

All five PR-013 role threads were closed before commit.

## Chosen plan

1. Add failing PR-013 contract tests for direct certificates, HTT term owner,
   MIO diagnostic metadata, MIO-shaped dict payloads, HTT manifest owner, and
   current-root static scanning.
2. Add `htt/workspace/contracts/htt_posterior.py` with frozen
   `HttLikelihoodTerm`, frozen `HTTPosteriorBundle`, and
   `reject_mio_likelihood_inputs`.
3. Extend `MioCertificate` with diagnostic-only query properties and an
   `as_likelihood_term()` method that raises.
4. Export the new HTT posterior contract from `workspace.contracts`.
5. Record PR-013 completion in both status files and update handoff docs.

## Files changed

- `htt/workspace/contracts/htt_posterior.py`
- `htt/workspace/contracts/mio_certificate.py`
- `htt/workspace/contracts/__init__.py`
- `tests/contracts/test_mio_htt_no_merge.py`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/PR_DELTAS/pr-013-mio-htt-type-firewall.md`
- `docs/harness/VALIDATION_LEDGER.md`
- `docs/harness/PROJECT_STATE.md`
- `docs/harness/CLAIM_LEDGER.md`
- `docs/harness/NEXT_SESSION_PROMPT.md`
- `docs/harness/BLOCKERS.md`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | ---: | --- |
| `venv/bin/python -m pytest tests/contracts/test_mio_htt_no_merge.py -q` before implementation | repo root | FAIL | Red phase: missing `workspace.contracts.htt_posterior`. |
| `venv/bin/python -m pytest tests/contracts/test_mio_htt_no_merge.py -q` after implementation | repo root | PASS | `14 passed`; covers direct certificate, owner, metadata, dict payload, manifest-owner, valid bundle, nested certificate, and real-root static scan checks. |
| `venv/bin/python -m py_compile htt/workspace/contracts/htt_posterior.py htt/workspace/contracts/mio_certificate.py htt/workspace/contracts/__init__.py tests/contracts/test_mio_htt_no_merge.py` | repo root | PASS | Touched Python files compile. |
| `venv/bin/python -m pytest tests/contracts/test_ownership_firewall.py htt/workspace/contracts/tests/test_mio_certificate.py htt/workspace/contracts/tests/test_htt_to_mio_roundtrip.py htt/workspace/contracts/tests/test_g19_enforcement.py htt/mio/tests/test_htt_cross_check.py -q` | repo root | PASS | `41 passed`; existing ownership, MIO, HTT-to-MIO, G19, and cross-check contracts preserved. |
| `venv/bin/python -m pytest htt/htt/tests/test_ver2_likelihood_scope_guard.py htt/htt/tests/test_ver2_directional_shell.py -q` | repo root | PASS | `21 passed`; HTT likelihood-scope and directional shell guards preserved. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`; PR-013 follows topological order. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After status update: `11/62 = 17.74%`; dependency-weighted `21.54%`; critical path `4/21 = 19.05%`; checkpoint not due. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`; packaging import smoke remains green. |
| `venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6877 deselected`. |
| `venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6824/6883 tests collected (59 deselected)`. |
| `venv/bin/python -m pytest tests/contracts -q` | repo root | PASS | `47 passed`; top-level contract suite remains green. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-013 files>` | repo root | PASS | No forbidden claim patterns detected after scanner-safe test/doc wording. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-013 docs>` | repo root | PASS | No unmarked strong claims detected. |
| `git diff --cached --check` | repo root | PASS | Staged PR-013 diff has no whitespace errors. |

## Review findings and fixes

- Finding: a direct object guard alone would not catch JSON-shaped MIO
  certificate payloads. Fix: `reject_mio_likelihood_inputs` rejects mappings
  with MIO owner markers or enough certificate schema markers.
- Finding: nested `mio_*` diagnostic keys could be smuggled into HTT likelihood
  term metadata. Fix: `HttLikelihoodTerm` recursively rejects MIO p-value,
  evidence, likelihood, posterior, score, and related key shapes.
- Finding: the existing G19 scalar-merge text scan points at stale roots in
  this checkout. Fix: PR-013 adds a static regression that verifies current
  production roots exist and scans them for MIO diagnostic scalar names near
  HTT evidence terms.
- Finding: cross-check rows/tables expose report-only comparison values. Fix:
  the new guard rejects `mio.interface.htt_cross_check` row/table objects as
  HTT likelihood inputs without importing MIO from the contract module.

## Claim hygiene and scientific scope

Numerical/scientific impact: none; type-contract and guard logic only.

Artifact/claim-tier impact: COMMON/HTT L2 contract metadata. PR-013 makes the
MIO/HTT separation executable for the new posterior bundle path and preserves
existing cross-check-only exports. It does not add solver outputs, transfer
calibration, null/mock/covariance evidence, sky-support evidence, morphology
compatibility evidence, or family-ID evidence.

## Residual risks

- PR-013 defines the new canonical `HTTPosteriorBundle` but does not migrate
  every legacy HTT inference entry point to that constructor. Existing
  likelihood-scope tests remain green, and deeper migration is left to
  downstream HTT inference PRs.
- The real-root static scan is intentionally high-signal and narrow; it catches
  explicit MIO diagnostic scalar names near HTT evidence terms but is not a
  full semantic analyzer.
