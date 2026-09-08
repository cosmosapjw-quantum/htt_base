# Verified reuse map and historical reintegration

Read-only source research; no import/test/runtime pass is claimed. A donor is reused only after its actual downstream import and assumptions pass the listed gate. Copy selected changes with tests into the target branch; do not merge entire historical branches to obtain one function.

| Pin | Exact commit |
|---|---|
| H, current handoff | [5702024e06eff4979087f07f86ee7131d13961ac](https://github.com/cosmosapjw-quantum/htt_base/tree/5702024e06eff4979087f07f86ee7131d13961ac) |
| Q, repaired decoder | [9f7d06dec0fce1c3a8a53fa5372c84d9c679c037](https://github.com/cosmosapjw-quantum/htt_base/tree/9f7d06dec0fce1c3a8a53fa5372c84d9c679c037) |
| P, survey successor | [5a3825f903546891fd90e3d708481707d59babf4](https://github.com/cosmosapjw-quantum/htt_base/tree/5a3825f903546891fd90e3d708481707d59babf4) |
| A, anchor/response | [6bafca66285ef071081453313bb7d2d6b261599c](https://github.com/cosmosapjw-quantum/htt_base/tree/6bafca66285ef071081453313bb7d2d6b261599c) |
| D, directional tensors | [de73549c16ac6ceb63f924c86611e0a5ceb4711d](https://github.com/cosmosapjw-quantum/htt_base/tree/de73549c16ac6ceb63f924c86611e0a5ceb4711d) |
| B, boost implementation | [29427a1f7f2c5d46e43ffe03053c4ac13e969228](https://github.com/cosmosapjw-quantum/htt_base/tree/29427a1f7f2c5d46e43ffe03053c4ac13e969228) |

## Active code reuse

| Pin/path | Actual existing interface | R7 action and limiting condition |
|---|---|---|
| H `scripts/observed_runs/rebuild_mes_tensor_carriers.py` | `harmonic_stf_matrices`, `project_carrier` | Keep `(N,32)` to Q/O/power conversion, frame and absolute amplitudes; its chart-unavailable records already preserve tensors. Reuse feature conversion separately from old statistical interpretation. |
| Q `htt/src/common/mes_krylov_completion.py` | `krylov16`, `reconstruct_krylov16`, `ordinary_power_bispectrum` | Port existing conditioned STF inverse and full replay checks into H consumer. Preserve `OrbitChartUnavailable` versus malformed input. |
| D `htt/src/common/observable_irrep_state.py` | `ObservableIrrepCarrier`, `build_real_harmonic_irrep_block`, `build_cartesian_stf_irrep_block` | Reuse typed blocks. Existing directional adapter supports measured STF2, not a fabricated dipole/octupole. Preserve separate measured dipole type. |
| B `htt/obsstat/lorentz_sky_pullback.py` | `pullback_thermodynamic_temperature_field`, `thermodynamic_temperature_pullback` | Exact positive thermal sky benchmark. Callback is evaluated at inverse-aberrated direction. Product-specific response remains a separate adapter. |
| B `htt/obsstat/boost_response.py` | `quadrupole_boost_octupole`, `boost_response_metric`, `boost_response_matrix`, `project_onto_boost_image`, `boost_orthogonal_residual` | Reuse algebraic coordinate, projector and injection checks. Stored Re/Im harmonic layout is not the carrier's orthonormal real basis: insert explicit sqrt(2) metric conversion. |
| D `htt/obsstat/processed_boost_error_envelope.py` | `build_output_error_envelope`, `validate_error_envelope_holdouts`, `certify_error_whitened_row_rank` | Reuse additive-family envelopes, zero-family handling and typed certificates. Holdout coverage proves only that set of controls, not all actual errors. |
| D `htt/obsstat/mes_directional_moments.py` | `estimate_joint_fit_directional_moments` | Reuse 9-column weighted monopole/dipole/STF2 fit. Existing arithmetic is diagonal-weighted despite covariance identity metadata; add actual full-covariance whitening when required. |
| D `htt/src/common/mes_directional_state.py` | `build_mes_directional_state`, `bind_mes_directional_stf2_observable`, `assess_physical_stress_readiness` | Preserve amplitude/shape split and missing physical-response status. Correct odd-field STF2 parity at adapter boundary before new odd-field use. |
| A/D `htt/src/common/mes_premise_normalization.py` | `normalize_mes_premise` | Bind numerator, anchor, sector, frame and order; propagate shared uncertainty. |
| A `htt/src/common/anchor_geometry.py` | `AnchorVector`, `AnchorFamily`, `evaluate_anchor_gauge` | Product-ball/ellipsoid/polytope admissibility subproblems; product bodies are outer relaxations unless actually justified. |
| A `htt/src/common/anchored_response_geometry.py` | `measure_anchored_response_geometry`, `measure_schur_morphology_information` | Reuse nuisance-projected and incremental response with full joint covariance. Shape count is not response rank. |
| H `htt/obsstat/egs3_gf_interval_v8.py`, `egs3_fractional_program.py` | `exact_joint_interval_v8`, `joint_interval`, `endpoint_equality_report` | Reuse signed numerator/positive denominator affine box subproblem. Not a general nonlinear MES optimizer. |
| P `htt/obsstat/cf4_current_stack.py` | `Cf4OperatorInputs`, `build_cf4_affine_design`, `analyze_cf4_current_stack` | Keep ordered full covariance/row IDs. Column coefficients: `(trace/3,Bx,By,Bz,Sxx,Syy,Sxy,Sxz,Syz)`; design `(r,nx,ny,nz,r(nx²-nz²),r(ny²-nz²),2r nxny,2r nxnz,2r nynz)`. Bind true distance/selection law separately. |
| H `htt/obsstat/cf4_forward_simulator.py` | `build_cholesky_generator`, `forward_mock_coverage` | Reuse correlated draws/refitting controls. Sorted-distance pseudo-groups, deterministic stressors and numerical jitter do not define real catalogue selection/covariance. |
| H `htt/obsstat/cf4_growth_covariance.py`, `cf4_velocity_estimators.py` | existing covariance-amplitude and estimator comparison paths | On use, replace unjustified endpoint-only amplitude-MLE decision by bounded global search; keep same-data estimator cross-covariance and actual contrast rank. Do not repair unused paths pre-emptively. |
| P `htt/obsstat/desi_successor_formalism.py` | `DESISelection`, `DESIRealization`, `fit_realization`, `build_mock_support`, `evaluate_response_rank` | Reuse NGC/SGC × three z bins × xyz, per-realization nuisance refit and separate mock tiers. Bind exact BGS BRIGHT sample. PR-151 old results remain invalidated. |
| H `htt/htt/htt/infer/jwst_host_hierarchy.py` | `HostPair`, `contrast_covariance`, `gaussian_hierarchical_posterior`, `student_t_hierarchical_posterior` | Retain host model, calibration correlations and residual alternatives. Repair exact support at singular covariance in `_gaussian_log_components`/`_psd_inverse_logdet` when consumed. |
| P `htt/obsstat/jwst_distance_consistency.py` | `build_pr309_inputs`, `analyze_pr309_current_stack` | Reuse row/covariance/competitor preparation. It does not fit competitor amplitudes; R7 supplies that inference contract. Unavailable admitted field is not a zero field. |
| H `htt/bass/background/bi_continuation/dynamics.py` | `BIState`, `rhs`, `shear_rhs_from_physical`, `constraint_residuals`, `dust_flrw_exact` | Correct dust donor. Photon anisotropic moments must be supplied separately; a perfect-fluid w=1/3 substitute is a different model. |
| H `htt/bass/background/matter_projection.py` | `SpeciesRestFrameState`, `project_species_to_normal_frame`, `total_matter_projection` | Use orthonormal Euclidean tetrad with explicit density/rapidity/unit conversion. Existing containers do not establish arbitrary spatial-metric support. |
| H `htt/bass/transport/geodesics.py` | `redshift_log_derivative`, `photon_geodesic_rhs` | Reuse energy/direction/screen transport; add/test Jacobi distance only in the scoped R3 provider. |
| H `htt/bass/collision/thomson_pstf.py` | `ThomsonPSTFCollisionOperator`, `EModeThomsonCollisionOperator` | Reuse orthogonal-electron damping/polarization normalization oracle; not finite-tilt transfer certification. |
| H `htt/bass/transfer/native_adapter.py` | `FutureNativeLowEllAdapterStub` | Preserve NotImplementedError for absent native delivery. Add a differently named scoped benchmark/external provider. |

## Tests already worth retaining

Q: `tests/common/test_mes_krylov_completion.py` including out-of-image input, rotations and singular charts. B: `htt/test_wu010_audit_closure.py` including STF/harmonic agreement. D: `htt/test_wu011_task7c_error_envelope.py`, `tests/obsstat/test_mes_directional_moments.py`, `tests/common/test_mes_directional_state.py`. A: `tests/pr_cards/test_pr_254_normalizer_anchor_geometry.py`. H: `research_gates/egs3/tests/test_egs3_axis_e_gf_v8.py`, `test_egs3_axis_e_fractional_program.py`, `tests/htt/test_jwst_host_hierarchy.py`, `htt/bass/collision/test_thomson_pstf.py`, `htt/bass/transport/test_ver2_geodesics.py`. P: `tests/integration/test_cf4_current_stack.py`, `tests/integration/test_jwst_sn_current_stack.py`.

Run these only in the composed Local Codex checkout. An existing test at a donor ref is not a pass on the new integration.

## Historical work as current research inputs

| Historical idea | Recovered scientific role | What is re-derived or rejected |
|---|---|---|
| BASS stress cones and memory | Constrained matter-state admissibility and shear source ablation | At fixed massive-dust energy require PSD momentum moment **and** trace below energy; an arbitrary PSD path is not an Einstein/dust solution. |
| BASS kinetic/optical code in attachments | Independent normalization, geodesic and collision checks after version/units review | Do not copy old exact-labeled empirical transfer coefficients or unsupported channels. Archive names are source candidates, not execution evidence. |
| Axis-C boost removal | Controlled same-likelihood deprojection and second-order noise test | Keep interference `-2 Q:Qkin`; replace cross-information/variance not derived from the injection law. |
| MIO x/F/G and cancellation witnesses | Same-state signed comparator and depth-gap image of a joint region | `x_C=0` is not isotropy; separate ceiling order is not admissibility. Reuse corrected GF, not old proxy scores. |
| CF4 constrained realizations | Calibration and uncertainty within longitudinal prior support | Radial affine response annihilates antisymmetric gradient; resampling cannot create observed curl. |
| DESI cap/depth windows | Real selection response and a distinct long-baseline direction/depth channel | Revalidate coordinate system, sample identity and weighted likelihood; discard invalidated numerical outputs. |
| JWST host comparisons | Shared calibration control that can increase joint information via T6 | Same-host geometric mean cancels; include overlapping measurements once. |
| Teff/TSC | Reproducible historical comparator and useful semantic guards in common | No new full-solver ownership or recycled Bayes claim without its generating law. |

The directly inspected attachment members and every reported observational asset are bound in [OWNED_ASSETS.md](OWNED_ASSETS.md). In particular reuse review87 photon quadrature and full screen/Jacobi mechanics, while adapting its restricted background derivatives. The BASS background/high-l bundle contains a pre-code harness, not solver code.

Attachment provenance candidates: `bianchirustcoreRDAGcomplete.tar.gz`, `BASS_v1_BACKGROUND_HIGHL_HARNESS_PROJECT_SOURCE_BUNDLE_20260803(1).zip`, `bianchireview87.tar(1).gz`, xAct package and low-ell automation kit. Their existing file/member inventories from the R6 investigation guide targeted local review. Rust installer and bootstrap are environment assets; do not rebuild the stack merely because they are attached. Pin the actual selected member and license before code transfer. The two newly provided physmath harnesses are version 3.1.0 and govern this run; they do not replace the project physics.
