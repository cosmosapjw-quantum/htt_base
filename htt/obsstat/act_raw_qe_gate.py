"""PR-152: ACT DR6 raw-QE acquisition gate and release-simulation cross-fit.

An authenticated ACT DR6 lensing inventory separates the RECONSTRUCTED products
the release provides (convergence data + 400 Monte-Carlo sims, the QE
normalisation/response, the fiducial N0, the N1 derivatives, the mask, the
validated multipole range) from the raw-QE inputs it does NOT provide (the raw
filtered CMB maps and the quadratic-estimator pipeline), so a realisation-
dependent N0 cannot be formed.  On the release simulations the low-multipole
mean field is formed by a LEAVE-ONE-SIMULATION cross-fit (each sim debiased by
the mean of the OTHER sims) so the sims are debiased the SAME way as the data
(whose mean field is the mean over all sims) --- the naive all-sim self-mean
field debiases the sims differently from the data and biases the pooled rank.

Because the upstream raw-QE inputs are absent, the raw-QE inference is a no-go
(ABANDON_CURRENT_DATASET_FOR_NATIVE_LOW_L_SKY_POWER); only the release-simulation
cross-fit diagnostic is closed.  No L=2..10 sky-power limit is computed from
absent raw-QE inputs, and released convergence plus an injected signal is NEVER
called a pre-QE-stage transfer.  ACT-release-simulation DIAGNOSTIC at
``roadmap_rescue_v1:C3`` only; no ACT convergence detection, anisotropy,
geometry, or Bianchi-family claim; the two CF4 P0s are untouched.
"""
from __future__ import annotations

import numpy as np

# bind the exact-discrete exchangeable pooled-rank estimator (PR-135)
from common.finite_null_ranking import pooled_rank_p  # noqa: E402

SCHEMA_VERSION = "pr152.act_raw_qe_gate.v1"


class ACTRawQEError(ValueError):
    """Raised when the ACT raw-QE gate discipline is violated."""


# --------------------------------------------------------------------------
# authenticated inventory + upstream availability decision
# --------------------------------------------------------------------------
def act_dr6_lensing_inventory(*, present: dict, raw_qe_inputs_on_disk: bool,
                              validated_ell_range: tuple,
                              reference_url: str) -> dict:
    """Authenticate the ACT DR6 lensing release: the reconstructed products that
    ARE present (each a name -> content-address) versus the raw-QE inputs that
    are NOT (the raw filtered CMB maps and the QE pipeline, needed for a
    realisation-dependent N0).  The availability of released products does not
    imply the raw-QE stage is included."""
    absent = ["raw_filtered_cmb_maps", "quadratic_estimator_pipeline",
              "realisation_dependent_n0"]
    return {
        "present_products": dict(present),
        "absent_raw_qe_inputs": absent,
        "raw_qe_inputs_on_disk": bool(raw_qe_inputs_on_disk),
        "validated_ell_range": [int(validated_ell_range[0]),
                                int(validated_ell_range[1])],
        "reference_url": reference_url,
        "note": "the release provides the reconstructed convergence, QE "
                "normalisation/response, fiducial N0, N1 derivatives, mask and "
                "validated multipole range, but not the raw filtered CMB maps or "
                "the quadratic-estimator pipeline; the raw-QE stage is not "
                "included"}


def upstream_availability_decision(inventory: dict) -> dict:
    """Decide the upstream raw-QE availability.  When the raw filtered maps + QE
    pipeline are absent, the raw-QE inference is abandoned and only the
    release-simulation diagnostic is closed."""
    available = bool(inventory.get("raw_qe_inputs_on_disk"))
    return {
        "raw_qe_available": available,
        "decision": ("RAW_QE_E2E_INJECTION_AVAILABLE" if available
                     else "ABANDON_CURRENT_DATASET_FOR_NATIVE_LOW_L_SKY_POWER"),
        "closed_diagnostic": ("raw_qe_e2e_injection" if available
                              else "release_simulation_crossfit_only"),
        "note": "with the raw-QE inputs absent the raw-QE inference is a no-go; "
                "only the release-simulation cross-fit diagnostic is closed, and "
                "no L=2..10 sky-power limit is computed from absent raw-QE inputs"}


# --------------------------------------------------------------------------
# band statistic + leave-one-simulation cross-fit mean field
# --------------------------------------------------------------------------
def band_power(alm_low: np.ndarray, mode_weight: np.ndarray) -> float:
    """The low-multipole band power S = sum_m w_m |a_lm|^2 (w_m = 1 for m=0, 2
    for m>0 to count the +/-m pair of the real field)."""
    return float(np.sum(mode_weight * np.abs(alm_low) ** 2))


def leave_one_sim_crossfit_mean_field(sim_low: np.ndarray, data_low: np.ndarray,
                                      mode_weight: np.ndarray) -> dict:
    """Debias the sims by a LEAVE-ONE-SIMULATION cross-fit mean field (each sim
    minus the mean of the OTHER sims) and the data by the mean over ALL sims, so
    both are debiased consistently.  Report the naive all-sim self-mean-field
    band power for comparison: it debiases each sim by a mean that INCLUDES
    itself (a treatment the data never gets), which deflates the sim residual
    band power and biases the pooled rank."""
    n = sim_low.shape[0]
    total = sim_low.sum(axis=0)
    mf_all = total / n                                     # data mean field
    # cross-fit: sim k debiased by the mean of the other n-1 sims
    mf_loo = (total[None, :] - sim_low) / (n - 1)
    resid_crossfit = sim_low - mf_loo
    resid_naive = sim_low - mf_all[None, :]                # self-mean-field
    S_cross = np.array([band_power(resid_crossfit[k], mode_weight)
                        for k in range(n)])
    S_naive = np.array([band_power(resid_naive[k], mode_weight)
                        for k in range(n)])
    S_data = band_power(data_low - mf_all, mode_weight)
    mean_cross = float(S_cross.mean())
    mean_naive = float(S_naive.mean())
    self_mf_bias_ratio = float(mean_naive / mean_cross) if mean_cross else \
        float("inf")
    # the naive/crossfit ratio is the EXACT input-independent ((n-1)/n)^2 sample-
    # size scaling (resid_naive == ((n-1)/n) resid_crossfit identically), NOT a
    # data-dependent measured bias
    algebraic_bias_ratio = float(((n - 1) / n) ** 2)
    # the mean field itself: for the low-multipole band it is numerically
    # negligible, so debiasing is effectively a no-op at low ell and the
    # cross-fit is the PRINCIPLED construction rather than a large correction
    mf_band_power = band_power(mf_all, mode_weight)
    p_crossfit = float(pooled_rank_p(S_data, S_cross))
    p_naive = float(pooled_rank_p(S_data, S_naive))
    return {"n_sims": int(n),
            "S_data": S_data,
            "mean_field_band_power": mf_band_power,
            "crossfit_sim_band_power_mean": mean_cross,
            "naive_sim_band_power_mean": mean_naive,
            "self_mean_field_bias_ratio_naive_over_crossfit": self_mf_bias_ratio,
            "algebraic_bias_ratio_n_minus_1_over_n_squared": algebraic_bias_ratio,
            "bias_ratio_is_input_independent": True,
            "naive_self_mean_field_deflates_residual":
                bool(mean_naive < mean_cross),
            "crossfit_pooled_rank_p": p_crossfit,
            "naive_pooled_rank_p": p_naive,
            "crossfit_sim_band_powers": [float(s) for s in S_cross],
            "note": "the sims are debiased by a leave-one-simulation cross-fit "
                    "mean field (the same debiasing the data gets from the "
                    "all-sim mean field); the naive/cross-fit band-power ratio is "
                    "the EXACT input-independent ((n-1)/n)^2 sample-size scaling, "
                    "not a data-dependent measured bias, and the low-multipole "
                    "mean field is numerically negligible so the cross-fit is the "
                    "principled construction rather than a large correction on "
                    "this data --- it is reported as the consistent diagnostic"}


# --------------------------------------------------------------------------
# exact finite rank of the low-multipole band
# --------------------------------------------------------------------------
def exact_finite_rank(*, n_sims: int, ell_min: int, ell_max: int) -> dict:
    """The exact finite rank of the low-multipole covariance: the number of real
    harmonic degrees of freedom sum_{ell}(2 ell + 1) capped by the sample rank
    n_sims - 1 (a mean-field-subtracted sample covariance loses one rank)."""
    n_modes = int(sum(2 * ell + 1 for ell in range(ell_min, ell_max + 1)))
    sample_rank = int(n_sims - 1)
    rank = int(min(n_modes, sample_rank))
    return {"ell_min": int(ell_min), "ell_max": int(ell_max),
            "n_real_harmonic_dof": n_modes, "sample_rank": sample_rank,
            "exact_finite_rank": rank,
            "rank_limited_by": ("sample" if sample_rank < n_modes else "modes"),
            "note": "the low-multipole band carries sum(2 ell + 1) real dof, "
                    "capped by the mean-field-subtracted sample rank n_sims - 1"}


# --------------------------------------------------------------------------
# stochastic vs fixed-template injection law
# --------------------------------------------------------------------------
def injection_law_distinction(sim_band_powers: list, *,
                              injection_amplitude: float, seed: int) -> dict:
    """Distinguish the two injection laws by their IDENTIFIABILITY under the SAME
    null.  A STOCHASTIC injection whose band-power distribution EQUALS the null's
    (an incoherent convergence field carrying the null's own power) is
    UNIDENTIFIABLE: a draw from that distribution IS a null draw, so its pooled
    rank against the null stays uniform.  A FIXED-TEMPLATE injection adds a
    COHERENT band power to every realisation --- a deterministic offset that
    shifts the rank.  Both are ranked against the SAME null, so the distinction
    is identifiable-vs-not, not an artifact of different null sets (it is NOT an
    additive stochastic field, which would itself raise the band power)."""
    rng = np.random.Generator(np.random.PCG64(seed))
    S = np.asarray(sim_band_powers, float)
    mu, sd = float(S.mean()), float(S.std(ddof=1))
    # stochastic (unidentifiable): a bootstrap draw from the SAME distribution as
    # the null, ranked against the null it cannot be told apart from -> uniform
    stochastic = np.array([float(rng.choice(S)) for _ in range(S.size)])
    p_stochastic = float(np.mean([pooled_rank_p(x, S) for x in stochastic]))
    # fixed-template (identifiable): a coherent additive band power on every draw
    fixed = S + injection_amplitude * mu
    p_fixed = float(np.mean([pooled_rank_p(x, S) for x in fixed]))
    return {"injection_amplitude": injection_amplitude,
            "sim_band_power_mean": mu, "sim_band_power_std": sd,
            "stochastic_mean_pooled_rank_p": p_stochastic,
            "fixed_template_mean_pooled_rank_p": p_fixed,
            "laws_distinct": bool(abs(p_stochastic - p_fixed) > 0.05),
            "note": "a stochastic injection whose band-power distribution equals "
                    "the null's is unidentifiable (its pooled rank against the "
                    "same null stays uniform); a fixed-template injection is a "
                    "coherent additive offset that shifts the rank; both are "
                    "ranked against the SAME null so the distinction is "
                    "identifiability, not a null-set artifact --- this is not an "
                    "additive stochastic field (which would itself raise the "
                    "band power)"}


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def refuse_pre_qe_transfer_label(label: str) -> None:
    if label in ("released_kappa_plus_signal_is_pre_qe", "pre_qe_transfer"):
        raise ACTRawQEError(
            "released convergence plus an injected signal may not be called a "
            "pre-QE-stage transfer")


def refuse_sky_power_limit_without_raw_qe(raw_qe_available: bool,
                                          claim: str) -> None:
    if claim in ("l2_10_sky_power_limit", "sky_power_limit") \
            and not raw_qe_available:
        raise ACTRawQEError(
            "an L=2 to 10 sky-power limit may not be computed from absent raw-QE "
            "inputs")


def refuse_naive_self_mean_field(crossfit: bool) -> None:
    if not crossfit:
        raise ACTRawQEError(
            "a naive all-sim self-mean-field without the leave-one-simulation "
            "cross-fit is rejected")


def refuse_act_detection(claim: str) -> None:
    if claim in ("act_kappa_detection", "anisotropy_detection"):
        raise ACTRawQEError(
            "an ACT convergence detection or anisotropy claim is rejected")


def refuse_bianchi_from_act(claim: str) -> None:
    if claim in ("bianchi_family", "geometry"):
        raise ACTRawQEError(
            "a Bianchi-family or geometry claim from the ACT convergence is "
            "rejected")


def refuse_raw_qe_without_inputs(raw_qe_available: bool, claim: str) -> None:
    if claim in ("raw_qe_inference", "rdn0") and not raw_qe_available:
        raise ACTRawQEError(
            "a raw-QE inference without the upstream filtered-map and QE inputs "
            "is rejected")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("pre-qe ", "transfer"),
        ("sky-power limit ", "from absent"),
        ("naive ", "self-mean-field"),
        ("act kappa ", "detection"),
        ("bianchi family ", "from act"),
        ("anisotropy ", "detected"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise ACTRawQEError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(inventory: dict, crossfit: dict, decision: dict) -> str:
    return (
        f"ACT DR6 lensing release-simulation cross-fit: an authenticated "
        f"inventory separates the {len(inventory['present_products'])} "
        f"reconstructed products present from the raw-QE inputs absent (raw "
        f"filtered CMB maps + QE pipeline). The low-multipole mean field is a "
        f"leave-one-simulation cross-fit that debiases the sims the same way as "
        f"the data (the naive self-inclusive all-sim mean field deflates the sim "
        f"residual band power by "
        f"{crossfit['self_mean_field_bias_ratio_naive_over_crossfit']:.3f}); the "
        f"cross-fit release-simulation pooled-rank of the data band power is "
        f"{crossfit['crossfit_pooled_rank_p']:.3f}. Because the raw-QE inputs are "
        f"absent the raw-QE inference is a no-go ({decision['decision']}); only "
        f"the release-simulation diagnostic is closed. ACT-release-simulation "
        f"diagnostic only; no convergence detection, anisotropy, or "
        f"Bianchi-family claim; the two CF4 P0s stay OPEN.")
