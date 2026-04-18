pub(crate) mod rodas5p;
pub(crate) mod dopri5;  // CL-08: Dopri5 explicit stepper for non-stiff regime
pub(crate) mod block_diag;
pub(crate) mod stacked;
pub(crate) mod regime;
pub(crate) mod solve_linear;
pub(crate) mod multispecies;
pub(crate) mod pipeline;
pub(crate) mod flrw_kmode;
pub(crate) mod flrw_cl_pipeline;  // CL-04A + CL-05: Track A C_ℓ orchestrator
pub(crate) mod teff_cl;           // CL-11: Teff intensity hierarchy for Track B
pub(crate) mod track_b_pipeline;  // CL-13+CL-04B: Track B orchestrator + cross-check
pub(crate) mod crosscheck;        // CL-14: 5-metric cross-check suite
pub(crate) mod dual_track_validation; // CL-06B + CL-09: end-to-end validation + report
#[cfg(test)]
mod regression_tests;
// acc_extensions: planned, not yet implemented
pub(crate) mod bdf2_linear;  // BDF-2 solver for oscillatory Boltzmann hierarchy
pub(crate) mod diffsol_bdf;  // diffsol BDF wrapper (A-stable, differentiable)
pub(crate) mod profiler;
pub(crate) mod matrix_cache;
pub(crate) mod tetrad_streaming;
pub(crate) mod sync_kmode;  // Synchronous gauge solver (CDM frame, PSTF-native)
pub(crate) mod tca_prephase;
pub(crate) mod tca_extended;
pub(crate) mod tca_second_order;
pub(crate) mod boundary_eft;
pub(crate) mod sync_gauge_camb;  // PREP-04: CAMB-convention solver (shadow port)
pub(crate) mod sync_gauge_v2;
pub(crate) mod pstf_kmode;
pub(crate) mod pstf_cl_pipeline;
pub(crate) mod truth_engine;  // P1-00: Truth Engine Contract
pub(crate) mod imex_ark4;    // P1-05: IMEX-ARK4(3)6L[2]SA solver
pub(crate) mod imex_collision_split;  // PR-IMEX-01: BASS → IMEX bridge
pub(crate) mod nonlinear_rodas5p;
pub(crate) mod pstf_primary;  // PR-020..PR-024b: PSTF primary migration (Bianchi+tilt target)
