"""common: cross-cutting utilities shared by bass, htt, and tsc.

Landing log:

* COMMON-A — ``contracts`` + ``sky_geometry`` (INDEPENDENT_TRACKS_PLAN §2.6).
* COMMON-B — ``healpix_selection`` (§3.1).
* COMMON-C — ``bulkflow_estimator`` (§3.1).
* COMMON-D — ``bulkflow_likelihood`` (§3.1) — Layer C BulkFlowLikelihood +
  prior_transform + run_dynesty adapter.
* COMMON-E — ``posterior_summary`` (§3.1) — Layer D samples_to_lb_posterior,
  credible_cone, hpd_region_healpix, axis_from_posterior.
* COMMON-F — ``mock_calibration`` (§3.1) — run_zoa_null_mocks,
  run_injected_dipole_mocks, coverage_test, apply_bias_correction.
* COMMON-G — ``conventions`` (ver3 PR-01) — invariant-basis gamma helpers:
  gamma-trace, PSTF, raise/lower.
"""

from common.conventions import gamma_norm2_tensor, gamma_trace, lower_vector, pstf_gamma, raise_vector

__all__ = [
    "gamma_trace",
    "gamma_norm2_tensor",
    "pstf_gamma",
    "raise_vector",
    "lower_vector",
]
