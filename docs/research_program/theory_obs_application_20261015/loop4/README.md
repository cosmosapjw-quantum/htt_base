# HTT theory-observation loop4: source acquisition and coherent joint laws (2026-10-15)

Two separate tracks:
1. Verified external primary input intake for Planck SMICA
   PR3 half-mission and CF4 grouped/method-specific source data.
2. Independent mathematical model of actual and counterfactual
   selection and shared calibration, plus correlated split-CMB law.

See THEORY_LOOP_KO.md and CODING_LOOP_KO.md, then
INPUT_ACQUISITION.json, BLOCKER_DELTA.json, MANIFEST.json,
and results/*/REPORT_KO.md.

Physically complete Planck E2E null, per-survey CF4
selection/cross-calibration and native Bianchi/optical
finite-distance response are still required. No
physical H0, q, beta or shear detection is asserted.

Expanded CF4 source investigation:
results/cf4_release_source_map_v2 (37,825 group
shared calibration shifts, 108 direct overlaps);
results/cf4_galaxy_calibrator_join_v1 (Table2
individual method errors and remaining unjoined
group IDs). Correlated multi-method Gaussian
normalizer in htt/obsstat/cf4_shared_selected_law.py.
