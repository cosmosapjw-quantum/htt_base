# REV-R094 - Block Scalar Occupancy Overclaim

owner: MIO
implementation_scope: mio
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R094 block scalar occupancy overclaim`
git_commit_or_worktree_state: pending_rev_r094_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 7)
- `htt/mio/formalism/channel_occupancy_vector.py`
- `scripts/make_current_manuscript_figures.py`
- `docs/manuscript/ch03_framework.tex`, `ch09_discussion.tex`
- `tests/mio/test_channel_occupancy_vector.py`
- `tests/contracts/test_audit_ver2_claim_firewall.py`

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 7: promote the channel-matched occupancy vector and block
scalar `Q`/`F` displays from using occupancy language unless the numerator and
denominator channels match or a joint admissible-ceiling proof is attached.

## Role Split

- Physics/statistics auditor steelman: scalar `Q = x/x_max` and `F = x_C/U`
  place a departure (tilt-sector) numerator over a shear-sector ceiling, so they
  are channel-mismatched proxy scores, not physical occupancy.
- Code cartographer steelman: keep `channel_matched_occupancy` strict and add a
  small language classifier the manuscript and figure code can call, rather than
  a new subsystem.
- Harness engineer steelman: pin the classifier with focused tests and add a
  manuscript firewall assertion so the proxy framing cannot regress.
- Claim-gate reviewer steelman: occupancy language stays reserved for the
  channel-matched vector lane.

## Changes

- `htt/mio/formalism/channel_occupancy_vector.py`: added
  `classify_occupancy_language(...)`. Returns `proxy_score_only` with
  `channel_mismatch` when channels differ and no ceiling proof is attached;
  `channel_matched_occupancy` when they match; `joint_admissible_ceiling` when a
  proof is attached. `channel_matched_occupancy` is unchanged and still strict.
- `scripts/make_current_manuscript_figures.py`: the departure display contract
  now records `scalar_q_f_occupancy_language` via the classifier, marking scalar
  `Q`/`F` as `proxy_score_only` with `channel_mismatch`.
- `docs/manuscript/ch03_framework.tex` (Layer 2) and
  `docs/manuscript/ch09_discussion.tex` (filling diagnostic): scalar `Q`/`F` are
  labelled channel-mismatched proxy scores; occupancy language is reserved for
  the channel-matched occupancy vector.
- `docs/generated/channel_occupancy_repair_report.md`: new contract report.
- Regenerated `docs/generated/current_science_plot_payload.json` and the
  dependent current-figure and revision-asset surfaces.
- Tests: added `classify_occupancy_language` contract tests and a manuscript
  occupancy-language firewall assertion.

## Artifact Metadata

- owner: MIO
- implementation_scope: mio
- claim_tier: diagnostic_only
- config_hash:
  - `htt/mio/formalism/channel_occupancy_vector.py:sha256:f39647086afa752d10726aedff43dcb11eadb43ad2f6325621148810b7dd4b3e`
  - `scripts/make_current_manuscript_figures.py:sha256:c9b96da469c2c8ba008748c20c6bc28344fbe41143176879bf7df96ea8068efa`
- input_hashes:
  - `docs/generated/channel_occupancy_repair_report.md:sha256:67fb79dbdf417dd338f6a0a9bc49d9a23911de3ab34d53ea569c9cbe61fe944a`
  - `docs/manuscript/ch03_framework.tex:sha256:8422fdd3018cf20019d76d77d116298abebf9f15e4659c91c09c6fe7cb947f54`
  - `docs/manuscript/ch09_discussion.tex:sha256:54e3f5570ff5ff1322a211771b6cca47dda95c74703b853efef1070f2b7ef05f`
  - `tests/mio/test_channel_occupancy_vector.py:sha256:f58ff821680fde2a4533fbe2a08c4fe6b4f6ccc6bd106dd6d6ceed4476e9f3fc`
  - `docs/generated/current_science_plot_payload.json:sha256:f189db49aec48195d005a4382927f243538af267cec0c6264e5f177cee0466b5`
- caveats:
  - no native low-ell solver result is introduced;
  - scalar `Q`/`F` remain proxy scores; occupancy language is blocked unless
    channels match or a joint admissible-ceiling proof is attached.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/mio/test_channel_occupancy_vector.py::test_scalar_proxy_rows_cannot_use_occupancy_language` initially failed with `ImportError` because `classify_occupancy_language` did not exist.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/make_current_manuscript_figures.py --check` | PASS | `current manuscript figure artifacts are current`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_revision_experiment_assets.py --check` | PASS | `revision experiment assets pass check`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/mio/test_channel_occupancy_vector.py tests/contracts/test_audit_ver2_claim_firewall.py tests/contracts/test_current_manuscript_figures.py` | PASS | `17 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ...occupancy... ch03 ch09` | PASS | `No forbidden claim language detected.` |
