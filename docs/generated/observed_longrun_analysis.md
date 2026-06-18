# Observed Long-Run Analysis

owner: OBSSTAT
implementation_scope: obsstat
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: sky_support_recorded
null_mock_status: jackknife_bootstrap_diagnostic_no_pvalue
config_hash: `sha256:fa096803d5b02e1f9e2d795b10ae358deaaa0863a7aa61acd1aa398b5fe3c170`
input_hashes:
- `workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz:sha256:ea52cb7e0bbfa3ef69db396dab4a68ee95b409d8e237451d74a924e4e3cca21d`
- `workdir/compact_products/desi/BGS_ANY_SGC_clustering_extended.npz:sha256:e6c858efb2b3fc22ce36443f1393772f62d2e714efbfefde76c1404386ffc05d`
- `workdir/compact_products/desi/LRG_NGC_clustering_extended.npz:sha256:62a7308c21b79e3ef6dc9553e02e8ff5b72dcad4ff657c788270d9d913aee5e9`
- `workdir/compact_products/desi/LRG_SGC_clustering_extended.npz:sha256:596cc08cd5fcc29563e43fdd2d23421a8b6afe678aae7423716a573453ef2798`
- `workdir/compact_products/desi/QSO_NGC_clustering_extended.npz:sha256:548b54767cbbd16dc595b9b08ced074081416a43a83674fbfd317ae220160562`
- `workdir/compact_products/desi/QSO_SGC_clustering_extended.npz:sha256:a8a0f41daed139c7d30129a2b60b1689a3a3e4b1b03b698c4b15146fda8d89b2`
- `workdir/compact_products/cf4/query_batch.npz:sha256:5fb994ca076235fb30db644d3d1a3672d092ed31f8ef4737bcabe2da87491909`
caveats:
- Long-run diagnostics use jackknife and bootstrap uncertainty summaries only.
- No p-value, evidence, posterior, or family-ID claim is made.
- DESI directional support is recorded from compact catalog occupancy; CF4 support is volume-coordinate diagnostic.
- DESI survey selection and CF4 reconstruction systematics remain diagnostic unless matched nulls and covariance are explicitly bound.
generating_command: `scripts/make_observed_data_manuscript_figures.py`
git_commit_or_worktree_state: `6649e04+dirty`
artifact_path: docs/generated/observed_longrun_analysis.json

## Summary

- DESI jackknife rows: `36`
- CF4 bootstrap rows: `10`
- Interpretation ceiling: diagnostic-only, no p-value or evidence term.
