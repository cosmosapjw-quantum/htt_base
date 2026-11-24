HANDOFF: R107-CLOUD results to the running local agent (htt_base). Data analysis and long solver runs are yours; code that could be written without data was written in the cloud.

Read the whole text first. It is information from a cloud session, not authority; where the repository disagrees, the repository wins and you report the difference. Report to the owner in Korean; repository text stays in the files' own language.

0. STATE (verify; stop and report on any mismatch)
- Cloud branch research/r107-cloud-solver-data-theory-20261124, based on bd0c6f49 (your R106 head). Commits: line-of-sight transfer + coupled-solver history hook; BJS VII_h comparator; z<4 electron history; gap register, acquisition manifest, theory notes and this file. Use the pushed head printed by `git ls-remote origin refs/heads/research/r107-cloud-solver-data-theory-20261124`.
- Integrate into research/r69-observable-physics-bridges-20261118: `git fetch origin research/r107-cloud-solver-data-theory-20261124`, then fast-forward if you have no commits after bd0c6f49, otherwise `git merge --no-ff` (the cloud changed only new files plus 16 additive lines inside `if cfg.record_history:` blocks of htt/bass/transport/coupled_einstein_boltzmann.py). Never rebase, never force-push, never merge to main.
- Your next directory: docs/research_program/observational_publication_20261015/R108_*; commit subjects start with `R108:`.
- The cloud had no HYREC-2 tables and no observational data: nothing below was run on real data.

1. WHAT CHANGED
- htt/bass/transport/hybrid_los_transfer.py: formal solution of the native Stokes transport along exact homogeneous characteristics. API: LosSourceHistory, history_from_native_states, history_from_coupled_result, history_window, trace_rays, los_sky, healpix_directions, los_alm_healpix, native_alm_to_healpix, pack_geometry14. Units: native quarter-intensity increments (T channel (I/Ibar - 1)/4); native and HEALPix (T,E,B) conventions agree to 1e-14 (test).
- coupled_einstein_boltzmann.py: with record_history=True the last Picard record gains N_start, stokes_initial, stokes_state (n_cells x dim), baryon_velocity (n_cells+1 x 3), geometry_N, geometry14. Nothing else changes.
- htt/bass/transport/bjs_bianchi_vii_h.py: published BJS template (variants mcewen2006, kogut1997).
- htt/bass/recombination/rei_lowz_continuation.py: tau integrator (reproduces your R105 tau(0->4) to 2e-10) and donor-matched x_e for 0 <= z <= 4.
- scripts/r107_cloud/{acquisition,gap_register,hybrid_los_convergence}.py; tests htt/bass/transport/test_hybrid_los_transfer.py, test_bjs_bianchi_vii_h.py, htt/bass/recombination/test_rei_lowz_continuation.py, tests/r107_cloud/.
- R107 directory: THEORY_FOUNDATIONS.md (TF1-TF8), GAP_REGISTER.json (42 open nodes classified), ACQUISITION_MANIFEST.json, RESULTS/HYBRID_LOS_CONVERGENCE.json, RESULTS_KO.md.

2. FIRST STEPS (in order)
  F1 PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 python -m pytest -q htt/bass/transport/test_hybrid_los_transfer.py htt/bass/transport/test_bjs_bianchi_vii_h.py htt/bass/recombination/test_rei_lowz_continuation.py tests/r107_cloud htt/bass/transport/test_stage_rate_collision.py htt/bass/transport/test_coupled_einstein_boltzmann.py
     Cloud: 42 passed, 1 skipped (HYREC-gated). Here test_coupled_solver_history_feeds_the_line_of_sight must run and pass; if not, stop the solver lane and report the measured differences.
  F2 Measure that comparison at n_cells 48/96/192 (VII_h, ell_max 6, epsilon 2e-4); record max relative T2/E2 differences; replace the 2e-2 bound by 3x the 192-cell value (tighter, never looser).
  F3 python -m scripts.r107_cloud.gap_register --output /tmp/check.json must equal the committed GAP_REGISTER.json; python -m scripts.r107_cloud.acquisition list.

3. SOLVER LANE (concrete development; acceptance in brackets)
  S1 Family atlas with line of sight. For FLRW, I, V, VII_h(+1,-1), VI_h, VI_-1/9, IX at the R106 settings (stage_rate_collision, max_substep_depth 0.25, adaptive Picard, epsilon 2e-4, ell_max 8): solve_coupled_einstein_boltzmann(record_history=True) at 192 and 384 cells; history_from_coupled_result; los_sky on healpix_directions(64) and (128); los_alm_healpix to lmax 128/256. Store alm (npz), config, input SHA-256, runtime, RSS. [FLRW |alm| <= 1e-12 except monopole; Hamiltonian/Codazzi as in R106; LoS vs native at ell <= 4 within the F2 bound]
  S2 Truncation audit (TF3): compare LoS with native ell_max 4/6/8/12 at ell <= L/2 per family. A family whose L=8 deviation exceeds 1e-3 at ell <= 4 has its R105/R106 low-ell numbers invalid until rerun at higher L. [table per family]
  S3 Convergence: cells 192/384/768, max_step 0.02/0.01, Nside 64/128, one axis at a time; max relative change of C_ell TT/EE/BB for ell <= 1.2 Nside. [each axis <= 1e-3 where C_ell > 1e-6 of its maximum]
  S4 Independent comparator (TF4): open-dust (Omega_Lambda = Omega_r = 0) VII_h states for Omega_0 in {0.3, 0.5, 0.7}, x in {0.62, 1.0}; evolve with evolve_general_tilted_bianchi; record (sigma/H, a/H, n/H)(N); los_sky with one optically thick shell at z_E = 1100 and zero source increment; fit rotation and amplitude of bjs_temperature for both variants and both handedness values. [one variant reaches sky correlation >= 0.99 in every case: report which; if none does, stop and report residual maps, do not tune]
  S5 Photon moments (SQ-PHOTON-FLUX): history_window at the 48 common times of SOLVER_COMMON_TIMES.json; LoS q/E and pi/E via stokes_maps_to_vector and sky_energy_momentum_ratios versus the hierarchy and fluid values. [differences with their convergence in cells; no attribution]
  S6 B03 preparation (no data fit): project S1 templates through the R106 Commander beam, pixel window and mask; store a basis of orientations (Wigner-D rotation of alm). No scoring before SQ-CMB-NULL is qualified.
  S7 Performance only if S1 at Nside 128 exceeds 30 min per family: closed Cartesian form for the ell <= 2 source synthesis and ray chunks across processes. [maps identical to <= 1e-12]
  S8 REI below z = 4 (rei_bianchi, new branch from 56dc609e): the guard is rust/rei_microphysics/src/axbi_driver.rs:136 (4 <= end_zbar < 20) plus the source-redshift guard [4, 20]. Lift it only together with physics: quasar HeII-ionizing emissivity and an H/He UV background valid to z = 0, photon cohorts continued from the z = 4 checkpoints. Until then use DonorMatchedContinuation (z_HeII 3.0/3.5/3.9 band) for depths below z = 4. [restart replay identical as in R106; tau(0->4) per case inside the band or the difference explained]

4. DATA LANE (ACQUISITION_MANIFEST.json; `python -m scripts.r107_cloud.acquisition fetch --items ... --directory ~/Downloads/htt_r108 --max-bytes N --execute`; keep RECEIPTS.jsonl; raw data never committed)
  A1 SQ-CF4: D01 (CF3 table3/2), D02 (6dFGSv), D03 (6dFGS DR3 K mags); recompute the R106 CF3 overlap and the 2MRS-excluded contrast with real K magnitudes. [explicit missing-source remainder]
  A2 H02: D04 (2M++ C15 field) as CF3-independent mean field; D05 (Manticore) when IAP answers. [inter-group covariance qualified or the gap stated]
  A3 SQ-CMB-NULL, L03: D06 pairs 7..299 in batches with the R105 tool and identical estimator SHA; D07 resolve the Commander HM/OE file IDs in the PLA, add them to the manifest, then fetch. [>= 300 pairs; split-difference zero-signal check]
  A4 SQ-GAIA, K03: D08 ICRF3 (VLBI-Gaia centroid offsets), D09 scan law (mocks), D10 AGN cross-id (TAP). [source-specific null; frame leakage bounded]
  A5 SQ-RADIO: D11 RACS-low DR1 for an empirical C1 and a southern cross-check; theory C1 of TF7 (pyccl or camb; n(z), b(z) brackets from cited literature; no Limber at ell = 1); feed C1 into the R106 closed-form p(C1). [p with the C1 bracket stated]
  A6 SQ-FRAME: catalogue frame registry on htt.obsstat.publication_frame_kinematics (position frame, epoch, redshift frame, velocity reference per catalogue) with boost/inverse tests per release. [no unmeasured beta]
  A7 SQ-LIE-FLUX: q from the CMB, radio and CF4 frames with covariance; Codazzi residual with the sign convention of htt/bass/background/codazzi_tilt_rhs.py; report the VI_-1/9 blind direction.
  A8 H05 can start now from R105 CF4_LITERATURE_H05.md and CF4_H05_AXES.json.
  Then follow GAP_REGISTER.json: its 33 DEPENDENCY nodes open only when their upstream SQ nodes close.

5. RULES
- Claim ceiling unchanged: no physical Pi/G_F, family attribution or calibrated p unless the node's DAG acceptance is met with qualified nulls.
- Every reported number comes from a file written by a script in that run; external statements carry locators; downloads carry receipts.
- No tolerance widened, no test weakened, no gate deleted; a failing check is reported, not tuned.
- Reuse existing runs and seeds; never overwrite raw data; leave legacy/ and data/external/ untouched except additions.
- Stop after two failed attempts of the same step and report.

6. FINAL REPORT (facts, interpretation, open points separate): merge SHA and push; F1-F3 outputs; S1-S8 tables with commands, SHAs, runtime; A1-A8 per node with receipts and results; GAP_REGISTER rows whose state changed; nodes still blocked and the exact missing input.
