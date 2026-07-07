# REV-R145 - Integrate external delta patch (dl_pipeline + v5 external-audit report)

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none (acquisition-planning infrastructure; no downloads, no raw data)
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Apply the externally-developed patch `htt_base_delta_patch_20260707.zip`.

## Review before apply (claim-firewall)

Overlay package (git unavailable in the copy). MANIFEST claim boundaries hold: no native low-ell
solver result, no Bianchi family identification, MIO/HTT posterior/evidence kept distinct, no
raw/downloaded data. The v5 report's `method_validation_summary.json` values are explicitly local
synthetic/mathematical checks (notes: "not observational results"): current response rank 2,
enlarged response rank 4 (P18/P22 route demo), e-value MC mean 1.009, identified-interval example
[0.11,0.17] (P26/P31 semantics "without external data"), dust-FLRW oracle residual 0. Repo
semantic-guard + forbidden-affirmative scan on the v5 report: clean.

## Applied

- `dl_pipeline/` acquisition/planning support: `scripts/fetch.py` (+ACT DR6 / ACT-lensing planning),
  `config/sources.json`, `scripts/extract_htt_data.py` updated; new `scripts/download_inventory.py`
  (dry-run/probe inventory, no network) + `tests/test_download_inventory.py` + `tests/test_fetch_logging.py`.
- `scripts/build_external_audit_report_v5.py` + the generated `external_audit_research_report_20260707_v5/`
  package (tex, pdf, evidence matrix, KO ledgers, MANIFEST, method-validation JSON) + a root PDF.
- Preserved (absent from payload, unchanged): rev-r142 `dl_pipeline/scripts/download_jwst_anchors.py`
  and `dl_pipeline/data/jwst_distances_seed.csv`; and `extract_cf4_full.py`, `cf4_grid_adapter.py`
  (byte-identical in the payload).

## Not applied / left untracked

Raw patch zip `htt_base_delta_patch_20260707.zip`; the generator byproduct zip
`external_audit_research_report_20260707_v5.zip`; LaTeX build artifacts (.aux/.log/.out/.toc). No
external download or raw data was added.

## Validation

| Check | Status |
| --- | --- |
| re-run generator `scripts/build_external_audit_report_v5.py` | 18-page PDF built from repo-local sources |
| `pytest dl_pipeline/tests` | 14 passed |
| repo semantic-guard + forbidden-affirmative scan on v5 report | clean |
| code-capability + pr04 source-snapshot packages rebuilt + `--check` | current |
| `pytest tests/contracts` | 355 passed |
