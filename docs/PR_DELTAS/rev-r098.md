# REV-R098 - Block Failed Predictive Adequacy

owner: HTT
implementation_scope: htt
claim_tier: blocked
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R098 block failed predictive adequacy`
git_commit_or_worktree_state: pending_rev_r098_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 11)
- `scripts/result_packs/generate_pack_B_local_global.py`
- `docs/manuscript/ch07_results.tex` (PPC section), `ch08_robustness.tex`
- `tests/result_packs/test_pack_B.py`

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 11: treat a failed posterior predictive check and an
unrun LOOCV as evidence blockers for channel (b), and make Result Pack B and
the manuscript robustness sections say so.

## Role Split

- Physics/statistics auditor steelman: channel (b) yields PPC p = 0.012 (below
  the registered 0.05 threshold) and LOOCV has not run; no channel evidence
  claim is admissible until a later model comparison fixes it.
- Harness engineer steelman: pin the adequacy gate with a contract test and bind
  the channel-(b) failure into Result Pack B.
- Claim-gate reviewer steelman: the required next models (single-beta,
  survey-specific amplitudes, mixture/outlier, systematic-response) must be named
  explicitly.

## Changes

- `htt/htt/htt/infer/predictive_adequacy.py`: new module with `adequacy_gate(...)`.
  Blocks `evidence_claim_allowed` and sets `adequacy_status=failed` when the PPC
  fails or LOOCV has not run, with `blocked_reasons` and `REQUIRED_NEXT_MODELS`.
  `main()` writes the channel-(b) report.
- `docs/generated/predictive_adequacy_report.{json,md}`: the channel-(b) gate
  (PPC failed, LOOCV not run, blocked).
- `scripts/result_packs/generate_pack_B_local_global.py`: Pack B now loads the
  adequacy report and exposes `predictive_adequacy_status` and a
  `predictive_adequacy` summary, reported in the markdown.
- `docs/manuscript/ch07_results.tex`, `ch08_robustness.tex`: the PPC sections
  now state that channel (b) carries no evidence claim until a later model
  comparison fixes it, and name the required next models.
- Regenerated `docs/generated/result_pack_B.md`.
- Test: `tests/htt/test_predictive_adequacy.py`.

## Artifact Metadata

- owner: HTT
- implementation_scope: htt
- claim_tier: blocked
- config_hash:
  - `htt/htt/htt/infer/predictive_adequacy.py:sha256:742cfa075140212715f788598e931af3dfc2a53cd7db766556aa0736cdfebe4c`
  - `scripts/result_packs/generate_pack_B_local_global.py:sha256:4f7a978d5eadb362a3b6e3553ca7b882a2e32088e086ad73da060a652111c51f`
- input_hashes:
  - `docs/generated/predictive_adequacy_report.json:sha256:84597ee109ce245b60911f51e1215271b3bec4ad17b6f16945e67e4e8298d463`
  - `docs/generated/result_pack_B.md:sha256:766ee58d61feb2072d6ce97fcdfa007ac7f248d7836876fb866fd9e1ed54e46c`
  - `tests/htt/test_predictive_adequacy.py:sha256:3c240523ddb9049a5b7b01bb5f0be681ae41d77a0d3e56f679e4d23998a1f328`
  - `docs/manuscript/ch07_results.tex:sha256:c7192cddaf714f1b985a5f5fabd60ffa50df6cac4c34fe8187377783496e06d5`
  - `docs/manuscript/ch08_robustness.tex:sha256:840bfb184476266d8f5ff3a18288d92758445beb457d92417a35f3c57c0d86aa`
- caveats:
  - blocked status holds until a later model comparison fixes channel (b);
  - no native low-ell solver output is introduced.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/htt/test_predictive_adequacy.py -q` initially failed with `ModuleNotFoundError`.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B htt/htt/htt/infer/predictive_adequacy.py` | PASS | Wrote the channel-(b) predictive adequacy report. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/result_packs/generate_pack_B_local_global.py` | PASS | Wrote `docs/generated/result_pack_B.md`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_predictive_adequacy.py tests/result_packs/test_pack_B.py` | PASS | `14 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/contracts/test_audit_ver2_claim_firewall.py` | PASS | `4 passed` (ch07/ch08 edits claim-safe). |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ...module... report.md ch07 ch08 pack_B` | PASS | `No forbidden claim language detected.` |
