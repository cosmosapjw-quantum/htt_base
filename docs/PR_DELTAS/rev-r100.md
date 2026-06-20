# REV-R100 - Gate G_F Evolution Claims

owner: MIO
implementation_scope: mio
claim_tier: blocked
transfer_source: none
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: `Codex REV-R100 gate G_F evolution claims`
git_commit_or_worktree_state: pending_rev_r100_commit

## Evidence Read

- `AGENTS.md`
- `docs/superpowers/plans/2026-06-20-audit-ver2-research-hardening.md` (Task 13)
- `htt/mio/formalism/isotropy_gap.py`
- `scripts/make_current_manuscript_figures.py` (G_F matched-null forecast payload)
- `docs/manuscript/ch08_robustness.tex`, `ch10_future.tex`

## DAG Rationale

Canonical `PR-*` status remains complete at `62/62`. This PR implements
supplemental REV task 13: reclassify G_F / beta(z) evolution curves as
registered phenomenological models only when their evolution equation,
redshift-bin covariance, and selection transfer status are explicit; otherwise
they remain blocked toy curves and are not local/global discriminators.

## Role Split

- Physics/statistics auditor steelman: a toy beta(z) law with unbound selection
  covariance and unbound Boltzmann/GR evolution is not a local/global
  discriminator.
- Harness engineer steelman: pin the gate with a classifier and contract tests
  and bind it into the G_F matched-null forecast payload.
- Claim-gate reviewer steelman: the manuscript future/robustness sections must
  call the current beta(z)/G_F curves blocked toy curves.

## Changes

- `htt/mio/formalism/isotropy_gap.py`: new `classify_gf_evolution_model(...)`.
  Blocks `local_global_discriminator_allowed` and sets `claim_tier=blocked` for a
  toy evolution law or any unbound evolution/selection status, with
  `blocked_reasons`.
- `scripts/make_current_manuscript_figures.py`: the G_F matched-null forecast
  payload now records a `gf_evolution_model` gate (toy, blocked) and the report
  markdown renders it.
- `docs/manuscript/ch08_robustness.tex`, `ch10_future.tex`: the beta(z)/G_F
  evolution curves are labelled blocked toy curves, registered models only when
  the gate conditions are explicit.
- Regenerated `docs/generated/gf_matched_null_forecast_report.{json,md}` and the
  dependent current-figure surfaces (provenance refresh).
- Test: `tests/mio/test_gf_evolution_gate.py`.

## Artifact Metadata

- owner: MIO
- implementation_scope: mio
- claim_tier: blocked
- config_hash:
  - `htt/mio/formalism/isotropy_gap.py:sha256:389c6b772284b42172d07db559af629c36a3cf26df9d8248fc5b54a47ac666ab`
  - `scripts/make_current_manuscript_figures.py:sha256:c0f22cc28c853955d86e7ab84ff088fe5d54e907637d8c847a8b8f3a9e38274a`
- input_hashes:
  - `docs/generated/gf_matched_null_forecast_report.json:sha256:f583900af07102065788972af81d25b3ef6413ab79ba63745dd03cb9259a66d5`
  - `tests/mio/test_gf_evolution_gate.py:sha256:64999cd8d34369788552e6531f317ba1652740e5b84e9087bbc1b4b41f68598c`
  - `docs/manuscript/ch08_robustness.tex:sha256:02f5146647080ab679e49fc2c982d3015b2dac43258b99dc5dc6e4365291907b`
  - `docs/manuscript/ch10_future.tex:sha256:5c9142072e3e3df6ff315f8e13c15b9681298ffb7ff14192d152a3bd3673af8b`
- caveats:
  - G_F evolution curves remain blocked toy curves until registered;
  - a registered model requires explicit evolution equation, redshift-bin
    covariance, and selection transfer status;
  - no native low-ell solver output is introduced.

## TDD Red

- `venv/bin/python -B -m pytest -p no:cacheprovider tests/mio/test_gf_evolution_gate.py -q` initially failed with `ImportError` because `classify_gf_evolution_model` did not exist.

## Validation

| Command | Status | Notes |
| --- | --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/make_current_manuscript_figures.py --check` | PASS | `current manuscript figure artifacts are current`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/mio/test_gf_evolution_gate.py tests/contracts/test_current_manuscript_figures.py tests/contracts/test_audit_ver2_claim_firewall.py` | PASS | `14 passed`. |
| `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/check_claim_language.py --dry-run ...isotropy_gap.py ch08 ch10` | PASS | `No forbidden claim language detected.` |
