# REV-R076: separate HTT posterior exceedance from MIO diagnostics

owner: COMMON
implementation_scope: semantic_firewall
claim_tier: diagnostic_only
transfer_source: mixed_external_proxy_and_none
config_hash: sha256:manual-rev-r076
input_hashes:
- docs/generated/qfpi_semantic_reconciliation.md
- htt/htt/htt/infer/posterior_exceedance.py
- htt/mio/formalism/exceedance.py
- scripts/verify_formalism_figure_labels.py
- scripts/make_manuscript_figures.py
- docs/manuscript/appendices.tex
- htt/workspace/contracts/htt_to_mio.py
- htt/htt/htt/core/departure_posteriors.py
sky_support_status: mixed_not_applicable_and_inherited
null_mock_status: mixed_not_applicable_and_inherited
generating_command: manual REV-R076 semantic split plus tests
git_commit_or_worktree_state: pending_rev_r076_commit
caveats:
- not native transfer
- no family identification
- no geometry-detection claim
- MIO diagnostics remain diagnostic-only and are not posterior/evidence terms
- HTT posterior exceedance is model-conditional and not MIO Pi

## Intent

Formalize the Q/F/Pi namespace split after external audit: MIO owns
diagnostic Q/F/Pi/G surfaces, while HTT owns posterior pushforward and
posterior exceedance summaries.

## Changes

- Added `htt.infer.posterior_exceedance.posterior_exceedance_summary`, an
  HTT-owned `P_post` helper with provenance, transfer, caveat, and
  `mio_pi_compatible=false` metadata.
- Added HTT helper allow-list and recursive metadata guards for
  `claim_tier`, `transfer_source`, and free-form metadata so artifact fields
  cannot emit native-solver, family, geometry, or truth-certificate language.
- Added MIO `Pi` guards rejecting HTT posterior pushforward source kinds.
- Added figure-label verifier coverage rejecting
  `htt_posterior_pushforward_distribution` as a MIO `Pi` measure kind or
  source kind.
- Updated public/legacy surfaces to avoid `Q` occupancy wording and to
  distinguish `Pi_MIO` from `Pi_HTT`.
- Added `docs/generated/qfpi_semantic_reconciliation.md`.

## Subagent Review

- Code cartographer found the active MIO formalism and HTT posterior
  pushforward seams and warned against wrapping MIO `ExceedanceCurve` in HTT.
- Harness engineer required stable source-kind and measure-kind regressions.
- Physics/statistics auditor required public-surface cleanup of Q occupancy
  wording and bare Pi namespace crossing.
- Claim-gate reviewer required HTT caveats and MIO diagnostic-only language.
- Regression tester identified the fast suite and broader pre-existing
  preliminary handoff status drift.
- `/review` loop 1 found two must-fix claim-firewall leaks: unsafe HTT
  artifact claim fields/metadata and MIO `Pi` label metadata accepting an HTT
  posterior-pushforward `source_kind`.
- `/review` loop 2 approved the fixes. Residual follow-up risk: the HTT
  helper uses local allow-lists that must be synchronized if transfer-source
  vocabulary changes; legacy `layer_3_exceedance` aliases still rely on
  compatibility flags and caveats.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q tests/contracts/test_qfpi_semantic_split.py`
  - result: `2 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q tests/htt/test_posterior_exceedance.py tests/mio/test_exceedance.py tests/contracts/test_formalism_figure_labels.py`
  - result: `38 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q tests/htt/test_posterior_exceedance.py tests/contracts/test_formalism_figure_labels.py`
  - result after review-loop fixes: `22 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q htt/test_packaging_imports.py tests/mio/test_departure_bundle.py tests/mio/test_normalized_score.py tests/mio/test_filling_fraction.py tests/mio/test_exceedance.py tests/mio/test_isotropy_gap.py tests/mio/test_departure_report.py tests/htt/test_posterior_pushforward.py tests/htt/test_posterior_exceedance.py tests/contracts/test_formalism_figure_labels.py tests/contracts/test_qfpi_semantic_split.py tests/contracts/test_claim_language_lint.py tests/contracts/test_publication_claim_freeze.py`
  - result after review-loop fixes: `160 passed`
- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -B scripts/verify_formalism_figure_labels.py docs/generated/current_science_plot_payload.json`
  - result: OK
- `venv/bin/python scripts/check_claim_language.py htt/htt/htt/infer/posterior_exceedance.py scripts/verify_formalism_figure_labels.py tests/htt/test_posterior_exceedance.py tests/contracts/test_formalism_figure_labels.py docs/generated/qfpi_semantic_reconciliation.md docs/PR_DELTAS/rev-r076.md --dry-run`
  - result after review-loop fixes: no forbidden claim language detected
- `git diff --check`
  - result: pass

## Known Residuals

The larger MIO/HTT package-local suite still has pre-existing preliminary
handoff expectation drift (`production_candidate` expected vs
`diagnostic_only` actual) outside this semantic split. REV-R076 does not
promote those generated handoff statuses.
