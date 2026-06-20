# Current Manuscript Plot List

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_and_external_transfer_conditioned
sky_support_status: mixed_not_directional_and_diagnostic_sky_support
null_mock_status: mixed_not_statistical_and_current_code_diagnostic_null_banks
config_hash: `sha256:5d5f382530a84f273563e05faeb31150abc406e06c58e319ca27891b6b1c8d73`
input_hashes:
- `scripts/make_current_manuscript_figures.py:sha256:c9b96da469c2c8ba008748c20c6bc28344fbe41143176879bf7df96ea8068efa`
- `docs/generated/current_manuscript_figure_curation.json:sha256:1bff29c98803b711203a90c988ecdbabdf241d2daf13666a314faa7673ec49f8`
- `docs/generated/current_science_plot_payload.json:sha256:f189db49aec48195d005a4382927f243538af267cec0c6264e5f177cee0466b5`
- `docs/generated/gf_matched_null_forecast_report.json:sha256:b933094897220c7ca5e1483c6cc4fe3dd9947dc6234ba8aa73fa227c6c35e3fd`
- `docs/generated/publication_claim_freeze.md:sha256:1ba0877a820632d98f7baa1d6bb80bb40ce38bc9f7d2dc5f4777ffec2a837309`
- `docs/generated/result_pack_A.md:sha256:ff6616ee58976624cfd89692dfc117da435fde9b6f5a79f8cd5ab4d0b94081c2`
- `docs/generated/result_pack_B.md:sha256:7d55ded6678510deedf62eaeacad89e94b7d0d9481632fb19b9a5178cbea7413`
- `docs/generated/result_pack_C.md:sha256:a8335933b110bae061ff527f91aef424996311396cc52881eec05e583577e2fe`
- `docs/generated/status_snapshot.json:sha256:da0dbc84e54addf1c927361d1e1620aad45a7cf55188c82b6d8996ebb8a7982d`
- `docs/generated/transfer_sensitivity_report.md:sha256:b2634c82ef783687cc2d304c50bb64487fa4556833bcc1a55464f7cae136903c`
- `htt/htt/htt/departure/response_overlap.py:sha256:2ea56655e8b8c419239459bdbe4d79c755d00115ce4bd6e6e00b447d51c1f139`
- `htt/htt/htt/nulls/local_boost_depth_null.py:sha256:b0d5d0b6a4b3fe534d1eefc630b9954a33d82555520f644f779dd6725e25609c`
- `htt/htt/htt/nulls/selection_response_depth.py:sha256:cac8f08d6618519e95147acde5ae0f567035206d14c595b3b917bf548a2a3cd3`
- `htt/mio/formalism/budget_spec.py:sha256:e836268d37323288d4b9e6bc3442f8eab2b3928ac6ebc91b7caef46d6210166a`
- `htt/mio/formalism/component_breakdown.py:sha256:9653e5b3dc63ebe740a78f7517e0df9f079b9a9bfd7a683c44f681ca2a06178b`
- `htt/mio/formalism/departure_bundle.py:sha256:f04d692646c0d2232373701fb29088d60bb2549106232ff05d2dff644291b80d`
- `htt/mio/formalism/exceedance.py:sha256:f2e8d0ef0f4c660f3d035e7daeb2829d48559321bbe0d27ce5e65d5a51c1283d`
- `htt/mio/formalism/filling_fraction.py:sha256:69cb198e205690816295e0e13b77cb6e673a88f000e9d7632c6650d08cbdbb70`
- `htt/mio/formalism/isotropy_gap.py:sha256:a98bd229360d4f928f33b45524401643ef8c5fd3d780f027515891b93ed40f5a`
- `htt/mio/formalism/normalized_score.py:sha256:5e44adfd1dbfdfa572e610e726fb78cae6a5996e82f52c910274608f3d66ec9b`
- `htt/src/common/departure_contracts.py:sha256:84682381cfb7b0356a69e74f3df1a6fbbc7be75ad84f937970485e7605d2f4d4`
caveats:
- Excluded legacy figure references are removed from manuscript use, not deleted from disk.
- Current figures include governance summaries and conditioned current-code physics diagnostics.
- No figure claims native low-ell output, geometry-detection status, or Bianchi family-ID.
generating_command: `python scripts/make_current_manuscript_figures.py`
git_commit_or_worktree_state: `f9a56f7+dirty`
artifact_path: docs/generated/current_manuscript_plot_list.md

## Excluded Legacy Plot References

- Excluded includegraphics references: `0`
- Exclusion rule: no current manifest-ready sidecar, missing source, or non-current legacy/ver2 figure provenance.
- Physical legacy files are retained for audit/recovery; they are not manuscript figures after curation.

## Current Plot Sequence

- Current manifest-backed plot count: `10`
- Conditioned physics diagnostics are appendix-eligible only until observed-data/native-solver promotion gates exist.

| Flow slot | Figure | Source artifacts | Claim tier | Artifact mode | Allowed use | Caveat |
| --- | --- | --- | --- | --- | --- | --- |
| Framework and repository status | `figures/current/fig_current_dag_progress.png` | `docs/generated/status_snapshot.json` | diagnostic_only | `governance_diagnostic` | `external_audit` | Diagnostic-only figure; not externally validated native low-ell output. |
| Framework claim boundary | `figures/current/fig_current_scalar_morphology_boundary.png` | `docs/generated/result_pack_A.md` | diagnostic_only | `governance_diagnostic` | `external_audit` | Diagnostic-only figure; not externally validated native low-ell output. |
| Observational pipeline | `figures/current/fig_current_transfer_provenance.png` | `docs/generated/transfer_sensitivity_report.md` | diagnostic_only | `governance_diagnostic` | `external_audit` | Diagnostic-only figure; not externally validated native low-ell output. |
| Observational pipeline | `figures/current/fig_current_transfer_sensitivity_tornado.png` | `docs/generated/current_science_plot_payload.json`<br>`docs/generated/transfer_sensitivity_report.md`<br>`htt/mio/formalism/budget_spec.py` | diagnostic_only | `paper_appendix_conditioned` | `paper_appendix` | Conditioned physics diagnostic; not an observed-data production result. |
| Results and robustness | `figures/current/fig_current_local_global_gates.png` | `docs/generated/result_pack_B.md` | diagnostic_only | `governance_diagnostic` | `external_audit` | Diagnostic-only figure; not externally validated native low-ell output. |
| Results and robustness | `figures/current/fig_current_local_global_rank_fpr.png` | `docs/generated/current_science_plot_payload.json`<br>`htt/htt/htt/departure/response_overlap.py`<br>`htt/htt/htt/nulls/local_boost_depth_null.py`<br>`htt/htt/htt/nulls/selection_response_depth.py` | diagnostic_only | `paper_appendix_conditioned` | `paper_appendix` | Deterministic gate stress payload; not an observed-data production result. |
| Results and robustness | `figures/current/fig_current_mio_certificate_status.png` | `docs/generated/result_pack_C.md` | diagnostic_only | `governance_diagnostic` | `external_audit` | Diagnostic-only figure; not externally validated native low-ell output. |
| Results and robustness | `figures/current/fig_current_qfpi_gf_semantic_split.png` | `docs/generated/current_science_plot_payload.json`<br>`docs/generated/result_pack_A.md`<br>`htt/src/common/departure_contracts.py`<br>`htt/mio/formalism/budget_spec.py`<br>`htt/mio/formalism/component_breakdown.py`<br>`htt/mio/formalism/departure_bundle.py`<br>`htt/mio/formalism/exceedance.py`<br>`htt/mio/formalism/filling_fraction.py`<br>`htt/mio/formalism/normalized_score.py` | diagnostic_only | `paper_appendix_conditioned` | `paper_appendix` | Normalized display only; proxy bars are not canonical Pi, F, or G_F diagnostics. |
| Results and robustness | `figures/current/fig_current_mio_depth_residual_vectors.png` | `docs/generated/current_science_plot_payload.json`<br>`docs/generated/gf_matched_null_forecast_report.json`<br>`docs/generated/result_pack_C.md`<br>`htt/htt/htt/nulls/local_boost_depth_null.py`<br>`htt/htt/htt/nulls/selection_response_depth.py`<br>`htt/mio/formalism/isotropy_gap.py` | diagnostic_only | `paper_appendix_conditioned` | `paper_appendix` | Diagnostic readiness plot; not a production certificate. |
| Governance and submission boundary | `figures/current/fig_current_public_claim_freeze.png` | `docs/generated/publication_claim_freeze.md` | diagnostic_only | `governance_diagnostic` | `external_audit` | Diagnostic-only figure; not externally validated native low-ell output. |

## Claim Boundary

- These plots support only claim-tiered observational/statistical framework reporting.
- Transfer-dependent surfaces remain transfer-conditional.
- MIO certificate/status plots are diagnostic-only and do not rank models.
- Scalar diagnostics and low-ell summaries do not provide Bianchi family-ID.
