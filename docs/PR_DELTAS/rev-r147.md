# REV-R147 - v6.1 report refresh checkpoint + external v6-review intake + Phase-0 hygiene

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none (report refresh + external-review intake; no downloads, no raw data, no new physics claim)
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Checkpoint the post-rev-r146 working tree (the v6.1 data-analysis-refresh session) and
ingest the four 2026-07-09 external review bundles as the isolated base for the v7
(Fifth Revision) build. Establish a clean, reproducible baseline before any v7 work.

## What this commit captures

- **v6.1 report package** (`external_audit_research_report_20260709_v6_1/` + root
  `external_audit_research_report_v6_1.pdf`): the Fourth-Revision report re-slugged to
  v6.1 with a current-data figure refresh (25 `fig_data_*` diagnostics, manifest-backed,
  diagnostic-only). Frozen v6 package (`external_audit_research_report_20260708_v6/`) left
  byte-frozen (restored from any working-tree drift per the frozen-package rule).
- **Data-analysis surface** (v6.1 session): `scripts/make_report_data_analysis_figures.py`,
  `scripts/build_v6_compact_data_analysis.py`, `scripts/build_v6_no_download_research_cards.py`,
  `scripts/curate_figure_lanes.py`, `scripts/k1_global_maxscan.py`; generated packs under
  `docs/generated/` (`report_data_analysis_figure_pack`, `v6_compact_data_analysis`,
  `figure_lane_curation_report`, `v6_*` inventories); `figures/data_analysis_current/`.
- **v7 groundwork scripts** (untracked → tracked): `scripts/build_v7_external_audit_synthesis.py`
  (hashes + routes the four review zips → `docs/generated/v7_external_audit_synthesis_matrix.{json,md}`),
  `scripts/build_v7_paper_a_revision_packet.py` (→ `v7_paper_a_revision_packet.*` +
  `v7_paper_a_skeleton.tex`), `scripts/run_v7_fortification_witnesses.py` (5 witnesses:
  F1 signed box / M1 G_F strictness / M3 estimated-cov Hotelling-F / M8 gate policy /
  K5 plugin firewall), `scripts/k5_cf4_identified_interval_card.py` (PLUGIN-firewalled
  K5/CF4 identified-interval card, `observational_claim_allowed=false`).
- **Code-side audit fixes already landed by the v6.1 session** (committed here):
  `htt/obsstat/egs3_identified_set.py` (signed component boxes + `curvature_branch_bounds`
  + `signed_curvature_branch_reports` + `estimated_covariance_f` two-stage threshold),
  `htt/obsstat/egs3_gf_interval.py` (`gf_strictness_criterion`/`_witness`). x_C anchors
  bit-identical (guarded).
- **External review intake**: `docs/audits/external_2026-07-09/` archives the four bundles'
  human-readable review documents (critic review, referee report F1–F3/M1–M10/m1–m12,
  R1–R12 recommendations, T1–T9/T1′–T9′/T3-lin theorem candidates + proofs, fortification
  plan, WP0–WP8 work packages, claim-defense matrix, Saadeh-2016 bibliography, 12-experiment
  summary) + `ARCHIVE_MANIFEST.md` with pinned zip SHA256s. Source `.zip`s stay untracked at
  root (read there by the synthesis generator; hashes preserved in the manifest).

## Phase-0 hygiene

- Regenerated four stale audit packages (final-report, pr04, research-evaluation,
  code-capability) whose manifests had drifted from the v6.1 session's results-table/report
  changes; their `--check` contract tests now pass.
- Restored the frozen v6 package + its root PDF to committed state; removed stray pdflatex
  byproducts from the frozen dir.

## Claim discipline

Diagnostic-only. No data claim, detection, family/geometry/native-solver/posterior/evidence
claim is introduced. The v7 groundwork artifacts are synthesis/routing (external-review
intake) and PLUGIN-firewalled diagnostic cards; all v7 public claims remain diagnostic-only
or blocked until their gates pass. External bundle code is reference-only — reimplemented,
never imported.

## Validation (baseline established for v7)

| Check | Status |
| --- | --- |
| `make egs3-gates` | 109 OK |
| `make egs3-seals` + `--check` | both seals PASS; current |
| `pytest tests/contracts` | 373 passed, 2 pre-existing failures (see below) |
| frozen v6 package | byte-frozen (restored) |

Two pre-existing contract failures, **not** v7-caused, documented and deferred:
1. `test_cf4pp_lnb_provenance::test_cf4pp_lnb_report_check_mode_passes` — the CF4++
   provenance generator fetches external URLs (oup.com / ifa.hawaii.edu); network-blocked
   in this sandbox (environmental).
2. `test_expanded_manuscript_figure_suite::test_conditioned_legacy_gallery_covers_existing_noncurrent_figures`
   — v6.1 figure-reorg drift: root figures were moved into
   `figures/quarantined_legacy/root_sources/` and a new `figures/data_analysis_current/`
   lane was added without migrating the conditioned-legacy gallery (still 88 `root__`-named
   copies; the candidate sweep now returns 118). A full curation migration is the v6.1
   session's unfinished business, tangential to the v7 report; deferred as a separate ticket.
