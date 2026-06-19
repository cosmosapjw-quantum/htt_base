# REV-R079: add research method diagnostics

owner: COMMON
implementation_scope: revision_method_diagnostics
claim_tier: diagnostic_only
transfer_source: mixed_none_empirical_proxy_external_or_proxy
config_hash: sha256:cc6e2520973432a222fead2c0006a370fac2ebed531348e4511cdd55f9d45ae0
input_hashes:
- path: docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md
  sha256: c681cef2a8b3d3bc7551cf4cf42134b0b6ea35ef9ef2c4f0af9635885d4bf13a
- path: docs/codex_handoff/pr_dag_research_program.yaml
  sha256: 63dd73215f0e0eb9e60bac3dff70a5177db74c3d9cef936d6ad90ef64e557aeb
- path: htt/htt/htt/infer/finite_mock.py
  sha256: 40c0333ee3983d2713082b3f744e496365884fe4e9a63c444ec4e7502e72610a
- path: htt/htt/htt/infer/nuisance_rank.py
  sha256: ff4537a7735f3794ad7e431f007fa0926c53475bd2eef5eed2239f063ebfbc88
- path: htt/htt/htt/infer/fisher_compression.py
  sha256: 842ac28c220b631cd677f1efb3c9d53461a3d1e359796b8a5e46a51e8f35be64
- path: htt/mio/formalism/channel_occupancy_vector.py
  sha256: 184900356617fb5b2ed8a49fd137fe992fb98f183bb8b4d715b58c7bdbbd898b
- path: htt/bass/transfer/evidence_stability.py
  sha256: 1c3eb283b17e7dea73630feb43342360056f98bd3161c9a12430c92626a19ba5
- path: scripts/generate_revision_experiment_assets.py
  sha256: 805ae684e4eafd68ab9017d4253ac5771f2580bbd9c6b1f7410c1db0edde96c6
- path: tests/contracts/test_revision_experiment_assets.py
  sha256: 1ee278f599a3bf8391121c48d4dbe864e744b52900181e8cd87cf6862b03ae69
- path: docs/generated/revision_experiment_assets.json
  sha256: d39ae0128821f64ae4bb663b9efa0463c67d41beb1906e8ae59b70cab4fd27bb
sky_support_status: mixed_not_directional_and_existing_input_metadata
null_mock_status: diagnostic_method_level_only
generating_command: REV-R079 hand implementation plus `venv/bin/python scripts/generate_revision_experiment_assets.py --write`
git_commit_or_worktree_state: pending_rev_r079_commit
caveats:
- Method diagnostics only; not observed evidence.
- No native low-ell solver implementation or native transfer validation.
- No family identification, family ranking, or geometry-detection claim.
- MIO occupancy rows are diagnostic only and are not posterior, odds, or evidence terms.
- BASS evidence-stability row is transfer-conditional and requires identical prior support.

## Evidence Gathering

- Read Task 6 of `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`.
- Read REV-R078 proposal DAG and registries to keep PR-N02, PR-N03, PR-N04, and transfer-stability ownership lanes separated.
- Read existing `scripts/generate_revision_experiment_assets.py` and `tests/contracts/test_revision_experiment_assets.py`.
- Read existing HTT/MIO/BASS package export patterns.
- Web/documentation check: verified current NumPy linear-algebra routines for SVD/eigh usage, SciPy exact binomial confidence-interval support, and pytest `approx`/temporary-path behavior. Implementation uses NumPy SVD/eigh and a closed-form zero-trigger bound, so no new SciPy dependency is introduced.

## Divergence And Selection

- Code cartographer steelman: add small production modules in the existing HTT/MIO/BASS roots and extend the current revision generator. Attack: do not vendor the archived external package or make a second generator/SSoT.
- Harness engineer steelman: narrow numerical invariants catch the migration. Attack: tests must also catch clipping, stale generated assets, import-surface gaps, and lane leakage.
- Physics/statistics auditor steelman: the formulas are valid as diagnostic controls. Attack: rank, Fisher, finite-mock, occupancy, and transfer-stability outputs must not become evidence, native validation, or family claims.
- Claim-gate reviewer steelman: ownership separation is clear if BASS owns transfer stability and MIO owns only channel occupancy. Attack: MIO transfer-stability wording would reopen evidence leakage.
- Regression tester steelman: focused tests plus generator check and package import smoke are sufficient for this PR. Attack: research-only audit package refresh is stale but belongs to REV-R087.

## Changes

- Added HTT `zero_trigger_upper_bound` for exact zero-trigger finite-mock FPR upper bounds.
- Added HTT nuisance-projected rank diagnostics using covariance whitening and nuisance projection.
- Added HTT covariance Fisher full-vs-diagonal compression diagnostics.
- Added MIO channel-matched occupancy vector diagnostics with no clipping and cross-channel denominator rejection.
- Added BASS transfer-conditional evidence-shift bound diagnostics.
- Exported the new modules from HTT, MIO, and BASS package surfaces.
- Updated `scripts/generate_revision_experiment_assets.py` so generated assets use the new diagnostics rather than inline `3/N` and clipped occupancy.
- Updated revision experiment assets and manifests, including method diagnostics in `docs/generated/revision_experiment_assets.json`.
- Strengthened revision asset tests and package-import tests.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m py_compile htt/htt/htt/infer/finite_mock.py htt/htt/htt/infer/nuisance_rank.py htt/htt/htt/infer/fisher_compression.py htt/mio/formalism/channel_occupancy_vector.py htt/bass/transfer/evidence_stability.py scripts/generate_revision_experiment_assets.py`
  - result: passed.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q tests/htt/test_finite_mock.py tests/htt/test_nuisance_rank.py tests/htt/test_fisher_compression.py tests/mio/test_channel_occupancy_vector.py tests/bass/test_evidence_stability.py`
  - result: 12 passed.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_revision_experiment_assets.py --write`
  - result: regenerated revision experiment assets and five revision figures.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/generate_revision_experiment_assets.py --check`
  - result: revision experiment assets pass check.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_finite_mock.py tests/htt/test_nuisance_rank.py tests/htt/test_fisher_compression.py tests/mio/test_channel_occupancy_vector.py tests/bass/test_evidence_stability.py tests/contracts/test_revision_experiment_assets.py htt/test_packaging_imports.py`
  - result: 28 passed.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider --collect-only -q tests/htt/test_finite_mock.py tests/htt/test_nuisance_rank.py tests/htt/test_fisher_compression.py tests/mio/test_channel_occupancy_vector.py tests/bass/test_evidence_stability.py tests/contracts/test_revision_experiment_assets.py htt/test_packaging_imports.py`
  - result: 28 tests collected.
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_response_overlap.py tests/htt/test_mes_cov_bound.py tests/mio/test_budget_spec.py tests/bass/test_external_transfer_registry.py`
  - result: 63 passed.

## Review Status

- `/review` loop 1 found two must-fix issues: generated BASS evidence-stability
  incorrectly used MIO denominator `relative_shift` as a log-likelihood delta,
  and nested `method_diagnostics` lacked full generated-result metadata.
- Patched generated evidence-stability to fail closed with
  `bound_status=not_evaluated_missing_loglike_delta`, `evidence_shift_upper_bound=None`,
  `required_input_kind=max_loglike_delta`, and
  `rejected_proxy_input_kind=denominator_relative_shift`.
- Patched every generated method diagnostic to include owner, scope, claim tier,
  transfer source, config hash, input hashes, sky/null status, generating
  command, worktree state, and caveats.
- Patched generator semantics so channel occupancy sends raw numerators to the
  MIO helper without clipping and forecast no-claim metadata includes both
  rank-specific reasons and still-failed promotion gates.
- `/review` loop 2 found no remaining scientific, claim-gate, harness, or
  regression must-fix issues. The only procedural blocker was that files had
  not yet been staged for staged-scope inspection.
- Patched REV-R079 figure manifests to use a single blocker label,
  `native_morphology_atlas_not_available`, rather than mixing native/family
  morphology-atlas vocabulary.
- `/review` loop 3 rechecked the staged diff after explicit staging. Claim-gate
  and regression reviewers found no blockers, no root audit uploads staged, no
  forbidden claim literals, coherent generated manifest metadata, and passing
  staged whitespace/generator/focused-test checks.

## Known Residuals

- `scripts/build_research_only_audit_package.py --check` is stale after REV-R079 generated-artifact changes. This is expected to be handled by REV-R087 audit-package refresh.
- Root-level uploaded audit files remain untracked because archived tracked copies already exist under `docs/audits/external_research_inputs_2026-06-20/`.
