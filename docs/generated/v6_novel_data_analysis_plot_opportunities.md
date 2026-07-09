# V6 Novel Data Analysis Plot Opportunities

## Artifact metadata

- owner: OBSSTAT/HTT/MIO routed per candidate
- implementation_scope: code-and-artifact inventory, no new figure generated
- claim_tier: diagnostic_only
- transfer_source: mixed; none for OBSSTAT catalog summaries, external-transfer-conditional where CF4 WF products are used
- config_hash: manual_scan_20260709T000517
- input_hashes: source artifacts retain their own manifests; primary scanned artifacts were `docs/generated/observed_longrun_analysis.json`, `docs/generated/cf4_bulkflow_apex_depth_report.json`, `docs/generated/cf4_bulkflow_likelihood_report.json`, `docs/generated/cf4_affine_flow_report.json`, `docs/generated/lowell_morphology_real_map_report.json`, `docs/generated/k1_global_maxscan.json`, `docs/generated/k1_biposh_smica.json`, `docs/generated/k5_cf4_release_coverage.json`, `docs/generated/k6_cf4_curl_posterior.json`, `docs/generated/pr08_006_joint_artifact.json`, and repo-local modules under `htt/obsstat`, `htt/htt/htt/infer`, `htt/htt/htt/nulls`, `htt/htt/htt/rest_frame`, and `htt/mio`
- sky_support_status: mixed; inherit from source artifact before plotting
- null_mock_status: mixed; diagnostic-only unless matched null metadata are explicitly bound
- caveats: opportunity inventory only; every report-facing figure still needs a generating script, manifest, source JSON, claim lane, and caption audit; no geometry or family conclusion is implied
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
| P01 | CF4 depth-apex phase portrait | `cf4_bulkflow_apex_depth_report.json`, `cf4_bulkflow_likelihood_report.json`, `lowell_morphology_real_map_report.json` | Data geometry of CF4 depth-dependent apex versus CMB dipole and low-ell morphology axis. |
| P02 | K5 group-GLS versus CF4++ WF consistency plot | `k5_cf4_release_coverage.json`, `cf4_bulkflow_likelihood_report.json`, `cf4_affine_flow_report.json` | Compare catalog-level GLS and WF affine summaries without promoting either to native-solver validation. |
| P03 | Scalar low-ell versus BiPoSH two-channel anomaly plane | `k1_global_maxscan.json`, `lowell_morphology_real_map_report.json`, `k1_biposh_smica.json` | Compare scalar and covariance-channel descriptors under their own null status. |
| P04 | K1 max-scan contribution waterfall | `k1_global_maxscan.json`, `lowell_morphology_real_map_report.json` | Show which registered low-ell statistics dominate the max-scan score. |
| P05 | CF4 affine gradient spectrum | `cf4_affine_flow_report.json`, `k6_cf4_curl_posterior.json` | Display bulk, expansion, shear, and curl-suppressed affine sectors by radius. |
| P06 | Observed-sector response vector | `pr08_006_joint_artifact.json`, K1/K5/K6 generated artifacts | Place measured diagnostic coordinates in a shared observed-sector panel without gate/status styling. |
| P07 | Depth-window coverage stability surface | Existing CF4 GLS and forward-mock coverage machinery | Denser depth grid for bulk-flow coverage residuals and stability. |
| P08 | CF4 shell leverage / leave-one-depth-out plot | Existing CF4 GLS shell estimator | Show how shell removal shifts amplitude, apex angle, and coverage sensitivity. |
| P09 | Low-ell axis uncertainty geometry plot | `lowell_morphology_real_map_report.json` | Show eigenvalue gaps, effective rank, and preferred-axis conditioning. |
| P10 | CF4/JWST anchor leverage forecast | `jwst_cf4_anchors.json`, `bass_extended_joint_forecast.json` | Forecast-only anchor leverage on distance errors and local-flow precision. |
| P11 | Planck low-ell residual map with CF4 apex-track overlay | SMICA low-ell products plus CF4 apex-depth report | Visualize actual low-ell residual geometry with CF4 apex track overlays. |
| P12 | K1-K5 joint diagnostic scatter against null/mock axes | K1 GRF null max-score and K5 forward-mock coverage distribution | Joint diagnostic page only; no joint calibrated probability unless a matched joint null is built. |

## Additional immediately drawable opportunities

| ID | Plot concept | Source evidence | Why it is more novel than current figures | First plotting route |
| --- | --- | --- | --- | --- |
| A01 | DESI redshift-jackknife ridge | `observed_longrun_analysis.json`: 36 DESI rows from BGS/LRG/QSO x NGC/SGC x six redshift bins | Uses repo-local compact DESI products to show tracer-by-depth resultant amplitude, not a literature reproduction. | Plot `weighted_resultant_amplitude` and `jackknife_std` versus `z_mid` by tracer and cap. |
| A02 | DESI NGC minus SGC asymmetry surface | Same DESI jackknife table | Localizes sky-cap asymmetry as a function of tracer and redshift. | For each tracer/bin, plot Delta amplitude with jackknife uncertainty. |
| A03 | DESI tracer hand-off continuity strip | Same DESI jackknife table | Shows how BGS, LRG, and QSO occupancy-driven directional summaries connect across redshift. | One continuous redshift axis, marker size by `n_rows`, uncertainty by `jackknife_std`. |
| A04 | CF4 radial velocity sign-transition curve | `observed_longrun_analysis.json`: 10 CF4 radial bootstrap rows from `workdir/compact_products/cf4/query_batch.npz` | Uses radial shell velocity summaries rather than bulk-only literature-style amplitude plots. | Plot `vr_mean_km_s` with p16/p84 band versus `radius_mid_mpc_h`; mark zero crossings. |
| A05 | CF4 radial delta-stability band | Same CF4 bootstrap table | Separates radial density/contrast stability from velocity amplitude. | Plot `delta_mean` with bootstrap band and optional `n_rows` rug/axis. |
| A06 | CF4 forward-coverage residual by depth | `cf4_bulkflow_likelihood_report.json` depth windows | Converts existing coverage checks into a data-analysis residual curve. | Plot `forward_mock_recovered_kms - bulk_amplitude_kms` and `forward_mock_coverage_1sigma` versus depth. |
| A07 | CF4 shell-to-shell apex separation matrix | `cf4_bulkflow_apex_depth_report.json` | Shows whether depth shells share a stable direction or fragment angularly. | Matrix of pairwise shell apex separations plus rows for full-sample apex and CMB dipole. |
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
2. Produce A04-A07 next: they convert CF4 products from familiar bulk-flow rechecks into radial and shell-geometry analyses.
3. Produce A08-A09 next: they add low-ell conditioning and scalar/covariance-channel stability without relying on family-level language.
4. Keep A10-A11 internal until the probe sources are explicitly bound into report manifests.
5. Treat B01-B06 as small implementation tasks, not ready-made report figures.

## Scan conclusion

The broad code scan found at least 17 additional data-analysis opportunities beyond the prior 12 concepts. The strongest report-facing expansion is not another governance or claim-gate surface; it is a concrete DESI+CF4+K1 figure set using already generated v6 products and repo-local compact data.
