# V6 Novel Data Analysis Plot Opportunities

## Artifact metadata

- owner: OBSSTAT/HTT/MIO routed per candidate
- implementation_scope: code-and-artifact inventory, no new figure generated
- claim_tier: diagnostic_only
- transfer_source: mixed; none for OBSSTAT catalog summaries, external-transfer-conditional where CF4 WF products are used
- config_hash: manual_scan_20260709T000517
- input_hashes: source artifacts retain their own manifests; the active CF4 inputs are `docs/generated/cf4_p0_quarantine_block.json`, `docs/generated/cf4_bulkflow_apex_depth_report.json`, and `docs/generated/cf4_affine_flow_report.json`, with the latter two restricted to reconstruction-conditioned method/systematics diagnostics. Other scanned inputs were `docs/generated/observed_longrun_analysis.json`, `docs/generated/lowell_morphology_real_map_report.json`, `docs/generated/k1_global_maxscan.json`, `docs/generated/k1_biposh_smica.json`, `docs/generated/k6_cf4_curl_posterior.json`, and repo-local modules under `htt/obsstat`, `htt/htt/htt/infer`, `htt/htt/htt/nulls`, `htt/htt/htt/rest_frame`, and `htt/mio`. Historical P0 CF4 value-bearing artifacts exist only under `legacy/cf4_p0` with public use false.
- sky_support_status: mixed; inherit from source artifact before plotting
- null_mock_status: mixed; CF4 P0 findings remain OPEN and no quarantined numerical calibration is active
- caveats: opportunity inventory only; every report-facing figure still needs a generating script, manifest, source JSON, claim lane, and caption audit; reconstruction-conditioned CF4 functionals may support method/systematics interpretation only; no observed bulk amplitude, global-tilt inference, cosmological inference, geometry, or family conclusion is implied
- generating_command: manual broad scan with `rg`, `find`, `jq`, and targeted module reads on 2026-07-09
- git_commit_or_worktree_state: 8280b8f+dirty

## Report-facing rule

Do not use figures or tables about internal development history, claim gates, limitation narration, self-audit, reviewer reassurance, or other meta-governance material in the report. Report-facing figures should analyze concrete data or already-bound data products. Meta/governance plots remain quarantined or internal-only unless the user explicitly asks for an internal audit appendix.

## Count summary

- Baseline novel plot concepts already listed: 12.
- Additional code-scan opportunities found: 17.
- Of the 17 additions, 11 are immediately drawable from existing artifacts or hardcoded diagnostic probe sets, and 6 need a small driver or real-data binding before they should be report-facing.
- Best first wave: DESI redshift-jackknife plots, CF4 radial bootstrap plots, CF4 coverage/apex geometry plots, and K1 scalar/BiPoSH conditioning plots.

## Baseline 12 concepts

| ID | Plot concept | Primary inputs | Claim-safe use |
| --- | --- | --- | --- |
| P01 | CF4 reconstruction-conditioned depth-apex phase portrait | `cf4_bulkflow_apex_depth_report.json`, `cf4_p0_quarantine_block.json` | Method/systematics-only comparison of depth-dependent reconstruction functionals; no measured bulk amplitude or cosmological interpretation. |
| P02 | K5 group-GLS versus CF4++ WF consistency plot | historical artifacts under `legacy/cf4_p0` | `QUARANTINED_OPEN_P0`; no active report-facing plot or replacement value while the canonical findings remain OPEN. |
| P03 | Scalar low-ell versus BiPoSH two-channel anomaly plane | `k1_global_maxscan.json`, `lowell_morphology_real_map_report.json`, `k1_biposh_smica.json` | Compare scalar and covariance-channel descriptors under their own null status. |
| P04 | K1 max-scan contribution waterfall | `k1_global_maxscan.json`, `lowell_morphology_real_map_report.json` | Show which registered low-ell statistics dominate the max-scan score. |
| P05 | CF4 affine reconstruction-functional spectrum | `cf4_affine_flow_report.json`, `cf4_p0_quarantine_block.json` | Display reconstruction-conditioned affine sectors as method/systematics diagnostics only. |
| P06 | Observed-sector response vector | historical CF4 coordinate artifacts under `legacy/cf4_p0` | `QUARANTINED_OPEN_P0`; the prior shared observed-sector coordinate is not an active data figure. |
| P07 | Depth-window coverage stability surface | historical CF4 likelihood machinery under `legacy/cf4_p0` | `QUARANTINED_OPEN_P0`; no active coverage calibration or residual surface. |
| P08 | CF4 shell leverage / leave-one-depth-out plot | Existing CF4 GLS shell estimator | Show how shell removal shifts amplitude, apex angle, and coverage sensitivity. |
| P09 | Low-ell axis uncertainty geometry plot | `lowell_morphology_real_map_report.json` | Show eigenvalue gaps, effective rank, and preferred-axis conditioning. |
| P10 | CF4/JWST catalogue-linkage audit | `jwst_cf4_anchors.json`, `cf4_p0_quarantine_block.json` | Catalogue linkage and error-metadata mechanics only; the global-tilt forecast is quarantined. |
| P11 | Planck low-ell residual map with CF4 apex-track overlay | SMICA low-ell products plus CF4 reconstruction-conditioned apex report | Conditional method/systematics geometry only; no cross-probe source or cosmological inference. |
| P12 | K1-K5 joint diagnostic scatter against null/mock axes | historical K5 calibration artifacts under `legacy/cf4_p0` | `QUARANTINED_OPEN_P0`; no active joint data plot or joint calibrated probability. |

## Additional immediately drawable opportunities

| ID | Plot concept | Source evidence | Why it is more novel than current figures | First plotting route |
| --- | --- | --- | --- | --- |
| A01 | DESI redshift-jackknife ridge | `observed_longrun_analysis.json`: 36 DESI rows from BGS/LRG/QSO x NGC/SGC x six redshift bins | Uses repo-local compact DESI products to show tracer-by-depth resultant amplitude, not a literature reproduction. | Plot `weighted_resultant_amplitude` and `jackknife_std` versus `z_mid` by tracer and cap. |
| A02 | DESI NGC minus SGC asymmetry surface | Same DESI jackknife table | Localizes sky-cap asymmetry as a function of tracer and redshift. | For each tracer/bin, plot Delta amplitude with jackknife uncertainty. |
| A03 | DESI tracer hand-off continuity strip | Same DESI jackknife table | Shows how BGS, LRG, and QSO occupancy-driven directional summaries connect across redshift. | One continuous redshift axis, marker size by `n_rows`, uncertainty by `jackknife_std`. |
| A04 | CF4 radial velocity sign-transition curve | `observed_longrun_analysis.json`: 10 CF4 radial bootstrap rows from `workdir/compact_products/cf4/query_batch.npz` | Uses radial shell velocity summaries rather than bulk-only literature-style amplitude plots. | Plot `vr_mean_km_s` with p16/p84 band versus `radius_mid_mpc_h`; mark zero crossings. |
| A05 | CF4 radial delta-stability band | Same CF4 bootstrap table | Separates radial density/contrast stability from velocity amplitude. | Plot `delta_mean` with bootstrap band and optional `n_rows` rug/axis. |
| A06 | CF4 forward-coverage residual by depth | historical likelihood report under `legacy/cf4_p0` | `QUARANTINED_OPEN_P0`; the former coverage curve is not an active figure. | No plotting route while C1-K5-MV-F1 remains OPEN. |
| A07 | CF4 reconstruction shell-to-shell apex separation matrix | `cf4_bulkflow_apex_depth_report.json`, `cf4_p0_quarantine_block.json` | Shows reconstruction sensitivity across depth shells without treating an apex as a measured cosmological vector. | Pairwise separation matrix labelled method/systematics only. |
| A08 | K1 low-ell tensor conditioning panel | `lowell_morphology_real_map_report.json` | Distinguishes low-ell axis stability from scalar tail strength. | Plot eigenvalues, eigenvalue gaps, effective rank, and condition number. |
| A09 | K1 scalar/BiPoSH map-stability matrix | `k1_global_maxscan.json`, `k1_biposh_smica.json` | Tests whether scalar and covariance-channel descriptors co-move across map choices. | Heatmap or paired scatter of scalar global score and BiPoSH descriptor percentiles. |
| A10 | MIO directional pairwise separation heatmap | `htt/workspace/results/mio_directional_coherence.json` or `mio.coherence.directional.STANDARD_PROBES` | Summarizes multi-probe angular consistency in a compact diagnostic. | Lower priority: hardcoded/literature probes must be source-bound before report use. |
| A11 | Redshift-bin directional drift line | `mio.coherence.redshift_binned.STANDARD_Z_PROBES` or a bound probe tuple | Captures depth drift of directional probes rather than only pooled coherence. | Lower priority: descriptive only unless matched null/mock metadata are attached. |

## Additional conditional opportunities

| ID | Plot concept | Implemented code surface | Missing piece before report-facing use |
| --- | --- | --- | --- |
| B01 | DESI data-random dipole by tracer, cap, and redshift | `htt/obsstat/catalogs/spectroscopic_dipole.py`, `htt/obsstat/catalogs/redshift_selection.py` | Need certified data+random catalogs, selection correction, and matched null/covariance metadata. |
| B02 | CF4 forward-likelihood residual anatomy | `htt/htt/htt/rest_frame/cf4_likelihood.py` | Need a driver that builds a real `Cf4Catalog`, baseline, and local/global basis. Diagonal diagnostic only. |
| B03 | CF4 low-z ablation survival curve | `htt/htt/htt/infer/lowz_ablation.py` | Current default is synthetic; bind real CF4 redshift and beta arrays before plotting. |
| B04 | K1 precision-v2 deformation plot | `htt/obsstat/lowell_precision.py`, K1 E2E/noise routes | Wait for K1 E2E/noise products, then compare v1 GRF and v2 precision/E2E feature shifts. |
| B05 | Planck multi-experiment residual coherence panel | `workdir/obs_bundle` Planck/ACT/SPT/BK/lensing products plus obsstat feature modules | Needs a small driver to cross-compare residual sign/coherence bands with claim-safe captions. |
| B06 | Local/survey-systematic null-bank overlays | `htt/htt/htt/nulls/local_boost_depth_null.py`, `htt/htt/htt/nulls/selection_response_depth.py` | Null-bank mechanics exist, but a data comparison needs bound survey/null metadata. |

## Priority queue

1. Produce A01-A03 first: they are the most underused actual-data results already present in the v6 generated artifacts.
2. Produce A04-A05 and A07 only under their reconstruction-conditioned method/systematics manifests; A06 remains quarantined.
3. Produce A08-A09 next: they add low-ell conditioning and scalar/covariance-channel stability without relying on family-level language.
4. Keep A10-A11 internal until the probe sources are explicitly bound into report manifests.
5. Treat B01-B06 as small implementation tasks, not ready-made report figures.

## Scan conclusion

The broad code scan found at least 17 candidate directions beyond the prior 12 concepts. The active report-facing expansion is a concrete DESI+K1 set plus explicitly reconstruction-conditioned CF4 method/systematics figures. P0-derived CF4 values, coverage calibration, global-tilt forecasts, and shared observed-sector coordinates remain quarantined with no active replacement value.
