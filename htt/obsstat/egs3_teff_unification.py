"""EGS3 v8-update U1/U2: the beta-channel correspondence -- one boost rapidity feeds
the comparator tilt sector AND the Teff two-temperature fingerprints, with MES-
registry ceilings propagating to exact fingerprint ceilings.

This module is the kinematic half of the unification lane that couples the three
previously separate structures -- the MES bound registry
(``egs3_mes_provenance`` / ``three_bound_hierarchy``), the graded comparator
(``egs3_graded_comparator`` / ``egs3_parent_identity``), and the active Teff
representative theory (``htt.teff.representative``) -- into one sealed system.
All frozen modules are imported read-only.

U1 (beta-channel correspondence, exact + disclosed reduction).
  A boosted blackbody sky at rapidity beta has EXACT antipodal temperatures
  T_+/- = T_0 / (gamma (1 -/+ v)) = T_0 e^{+/-beta}. The equal-weight
  two-temperature anchor c(1 +/- s) of the Teff theory therefore matches the
  antipodal TWO-POINT reduction of the boost sky with

      s = tanh(beta)   EXACTLY   (c = T_0 cosh beta; scale drops out).

  Combined with the T9' antipodal-pair tilt corollary
  Omega_tilt = 2 (1+w) Omega_m sinh^2(beta)  (egs3_parent_identity /
  egs3_nonlinear_realization), the normalized tilt t :=
  Omega_tilt / ((1+w) Omega_m) = 2 sinh^2 beta eliminates beta exactly:

      s^2 = t / (2 + t)              (exact, all orders),

  so the Teff ratios become exact closed forms in the COMPARATOR sector,
  R_3(t), R_5(t), with the exact leading series

      R_3 - 1 = -(3/4) t + (87/32) t^2 + O(t^3)
      R_5 - 1 = +(5/4) t - (185/32) t^2 + O(t^3)
      R_4     =  1  identically (the p=4 anchor is s-invariant).

  ANTIPODAL-SPECIFICITY PIN: a single-species tilt (Omega_tilt =
  (1+w) Omega_m sinh^2 beta) gives R_3 - 1 = -(3/2) t_1 + O(t_1^2) -- the
  -(3/4) coefficient is a property of the antipodal PAIR channel.

  Disclosed caveats (part of the theorem statement, NOT footnotes):
  (i) the boost sky is a CONTINUUM of direction-dependent blackbodies; the
      two-point antipodal reduction is a REGISTERED TOY ANCHOR sampling the
      two boost poles, not an angular average (a full-sky average has
      different coefficients and is not claimed);
  (ii) the equal-weight two-temperature MIXTURE is not a blackbody and not
      the observed sky: R_3/R_5 are properties of the Teff equal-information
      representation (its Thm 22 anchor), NOT a predicted CMB spectral
      distortion -- no data or signal-discovery statement;
  (iii) beta here is the RAPIDITY (v gamma = sinh beta); a velocity-defined
      beta_v = v differs from tanh beta at O(beta^3) ~ 1e-9 for CF4-scale
      inputs -- disclosed, never silently mixed.

U2 (MES -> Teff fingerprint ceilings, exact).
  With s_max := eps_1 (the registered SSOT MES dipole amplitude, leading-order
  dipole <-> boost identification, disclosed as such), the deviations obey the
  PROVED envelopes (polynomial root-isolation proofs on u = s^2, exact):

      0 <= 1 - R_3(s) <= (3/2) s^2      for 0 < s < 1
      0 <= R_5(s) - 1 <= (5/2) s^2      for 0 < s < 1

  giving exact rational ceilings at the registry value: |R_3 - 1| <=
  (3/2) eps_1^2 and |R_5 - 1| <= (5/2) eps_1^2. The ceiling map
  u -> (k/2) u^2 is strictly increasing, so the MES ordering theorem
  B_sigma > B_omega > B_accel (imported from the frozen
  ``mes_ordering_theorem``) maps to an identically ordered ceiling triple --
  DISCLOSED as a formal order-preservation instantiation (the three MES
  budgets are NOT three physical rapidity ceilings). The CF4 bulk-flow
  rapidity (K5 card, |B| = 340.7264 km/s) sits strictly below the MES dipole
  ceiling in BOTH channels: fingerprint (3/2) s_CF4^2 = 1.94e-6 < 2.28e-6 =
  (3/2) eps_1^2, mirroring the tilt-sector containment.

Claim discipline. Exact symbolic correspondence between registered in-repo
mathematical objects at tier diagnostic_only; no data claim, no
signal-discovery claim, no spectral-distortion prediction, no
Bianchi-class-identification-of-the-sky claim, no native-solver-produced
claim, no probabilistic-inference claim.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np
import sympy as sp

from htt.obsstat.egs3_mes_provenance import (
    eps_registry_provenance, mes_ordering_theorem,
)
from htt.teff.representative import two_temperature_ratio

__all__ = [
    "BETA_CF4",
    "antipodal_boost_reduction",
    "beta_channel_correspondence",
    "fingerprint_envelope_proofs",
    "fingerprint_ceilings",
    "teff_unification_seal",
]

# CF4 bulk-flow rapidity: |B| = 340.7264 km/s (K5 card CF4_bulk_amplitude,
# input mode REAL) over c; the rapidity-vs-velocity distinction is O(beta^3).
_CF4_BULK_KMS = 340.7264
_LIGHT_SPEED_KMS = 299792.458
BETA_CF4 = _CF4_BULK_KMS / _LIGHT_SPEED_KMS


def _exact_ratios_in_s():
    """R_3, R_4, R_5 as exact SymPy expressions of the mixing s (imported from
    the active Teff lane; read-only)."""
    s = sp.Symbol("s", positive=True)
    out = {}
    for p in (3, 4, 5):
        expr, svar = two_temperature_ratio(p)
        out[p] = sp.simplify(expr.subs(svar, s))
    return s, out


def antipodal_boost_reduction() -> dict:
    """U1 step 1: the antipodal two-point reduction of the boost sky IS the
    two-temperature anchor with s = tanh(beta), exactly."""
    beta = sp.Symbol("beta", positive=True)
    T_plus, T_minus = sp.exp(beta), sp.exp(-beta)     # T_+/-/T_0 = e^{+/-beta}
    # gamma(1 -/+ v) = cosh(beta) -/+ sinh(beta) = e^{-/+beta}: verify
    v = sp.tanh(beta)
    gamma = 1 / sp.sqrt(1 - v ** 2)
    antipodal_exact = sp.simplify(
        (1 / (gamma * (1 - v)) - T_plus).rewrite(sp.exp)) == 0
    c = (T_plus + T_minus) / 2                        # = cosh(beta)
    s_reduced = sp.simplify((T_plus - c) / c)
    s_is_tanh = sp.simplify(s_reduced - sp.tanh(beta)) == 0
    # eliminate beta by the antipodal tilt: t = 2 sinh^2(beta) => s^2 = t/(2+t)
    t_of_beta = 2 * sp.sinh(beta) ** 2
    s2_identity = sp.simplify(
        sp.tanh(beta) ** 2 - t_of_beta / (2 + t_of_beta)) == 0
    return {
        "antipodal_temperatures": "T_+/- = T_0 e^{+/-beta} (exact)",
        "boost_pole_identity_exact": bool(antipodal_exact),
        "s_reduced": str(s_reduced),
        "s_equals_tanh_beta_exact": bool(s_is_tanh),
        "tilt_normalization": "t = Omega_tilt/((1+w) Omega_m) = 2 sinh^2 beta "
                              "(T9' antipodal corollary)",
        "s_squared_equals_t_over_2_plus_t_exact": bool(s2_identity),
        "reduction_caveat": "two-point antipodal reduction of a continuum "
                            "boost sky; registered toy anchor, not an angular "
                            "average",
    }


def beta_channel_correspondence() -> dict:
    """U1 step 2: exact closed forms R_3(t), R_5(t) on the comparator tilt
    coordinate and their exact series; R_4 == 1 identically; the antipodal
    -(3/4) vs single-species -(3/2) specificity pin."""
    s, R = _exact_ratios_in_s()
    t = sp.Symbol("t", positive=True)
    sub_anti = sp.sqrt(t / (2 + t))
    R3_t = sp.simplify(R[3].subs(s, sub_anti))
    R5_t = sp.simplify(R[5].subs(s, sub_anti))
    r3_series = sp.series(R3_t, t, 0, 3).removeO()
    r5_series = sp.series(R5_t, t, 0, 3).removeO()
    c3_lead = r3_series.coeff(t, 1)
    c5_lead = r5_series.coeff(t, 1)
    c3_next = r3_series.coeff(t, 2)
    c5_next = r5_series.coeff(t, 2)
    # single-species pin: t1 = sinh^2 beta -> s^2 = t1/(1+t1)
    t1 = sp.Symbol("t1", positive=True)
    R3_t1 = sp.simplify(R[3].subs(s, sp.sqrt(t1 / (1 + t1))))
    c3_single = sp.series(R3_t1, t1, 0, 2).removeO().coeff(t1, 1)
    return {
        "R3_of_t_exact": str(R3_t),
        "R5_of_t_exact": str(R5_t),
        "R4_identically_one": bool(sp.simplify(R[4] - 1) == 0),
        "leading_R3_coeff": str(c3_lead),
        "leading_R5_coeff": str(c5_lead),
        "second_order_R3_coeff": str(c3_next),
        "second_order_R5_coeff": str(c5_next),
        "leading_coeffs_exact": bool(c3_lead == sp.Rational(-3, 4)
                                     and c5_lead == sp.Rational(5, 4)
                                     and c3_next == sp.Rational(87, 32)
                                     and c5_next == sp.Rational(-185, 32)),
        "single_species_R3_coeff": str(c3_single),
        "antipodal_specificity_pin": bool(c3_single == sp.Rational(-3, 2)),
        "correspondence": "R_3 - 1 = -(3/4) Omega_tilt/((1+w) Omega_m) + O(t^2) "
                          "-- one rapidity feeds the comparator tilt sector and "
                          "the Teff fingerprint channel",
    }


def fingerprint_envelope_proofs() -> dict:
    """U2 step 1: EXACT envelope proofs on u = s^2 by polynomial root
    isolation (Sturm-based sympy real_roots; zero tolerance):

      (a) R_3 <= 1 on (0,1):        (1+6u+u^2)^3 - (1+3u)^4 has all-positive
                                    coefficients (no roots in (0,1]);
      (b) 1 - R_3 <= (3/2) u:       (1+3u)^4 - (1-(3/2)u)^4 (1+6u+u^2)^3 has
                                    no roots in (0, 2/3) and is positive
                                    inside (the bound is trivial for
                                    u >= 2/3 where 1-(3/2)u <= 0 < R_3);
      (c) R_5 >= 1 on (0,1):        (1+10u+5u^2)^4 - (1+6u+u^2)^5 no roots,
                                    positive inside;
      (d) R_5 - 1 <= (5/2) u:       (1+(5/2)u)^4 (1+6u+u^2)^5 - (1+10u+5u^2)^4
                                    no roots in (0,1], positive inside.

    The pointwise two-sided ordering R_5 + R_3 >= 2 is only NUMERICALLY
    certified (fractional powers block polynomialization); the exact ordering
    statement shipped is at the CEILING level, (3/2) u < (5/2) u."""
    u = sp.Symbol("u", positive=True)
    D = 1 + 6 * u + u ** 2
    N3 = 1 + 3 * u
    N5 = 1 + 10 * u + 5 * u ** 2

    def _no_roots(poly, lo, hi, sample):
        roots = [r for r in sp.real_roots(sp.Poly(sp.expand(poly), u))
                 if lo < r < hi]
        return (not roots) and bool(poly.subs(u, sample) > 0)

    p_a = D ** 3 - N3 ** 4
    p_b = N3 ** 4 - (1 - sp.Rational(3, 2) * u) ** 4 * D ** 3
    p_c = N5 ** 4 - D ** 5
    p_d = (1 + sp.Rational(5, 2) * u) ** 4 * D ** 5 - N5 ** 4
    proofs = {
        "a_R3_below_one": _no_roots(p_a, 0, sp.Rational(1001, 1000),
                                    sp.Rational(1, 10)),
        "b_one_minus_R3_below_3half_u": _no_roots(p_b, 0, sp.Rational(2, 3),
                                                  sp.Rational(1, 10)),
        "c_R5_above_one": _no_roots(p_c, 0, sp.Rational(1001, 1000),
                                    sp.Rational(1, 10)),
        "d_R5_minus_one_below_5half_u": _no_roots(p_d, 0,
                                                  sp.Rational(1001, 1000),
                                                  sp.Rational(1, 10)),
    }
    # numeric certificate for the pointwise sum ordering (not claimed exactly)
    s, R = _exact_ratios_in_s()
    f = sp.lambdify(s, R[5] + R[3] - 2, "numpy")
    grid = np.sqrt(np.linspace(1e-8, 0.999999, 4001))
    pointwise_min = float(np.min(f(grid)))
    return {
        "method": "polynomial root isolation on u = s^2 (sympy real_roots, "
                  "Sturm); exact, zero tolerance",
        "proofs": proofs,
        "all_envelopes_proved": bool(all(proofs.values())),
        "pointwise_sum_ordering_numeric_min": pointwise_min,
        "pointwise_sum_ordering_note": "R_5 + R_3 >= 2 certified numerically "
                                       "only (min > 0 on the grid); the exact "
                                       "shipped ordering is ceiling-level",
    }


def fingerprint_ceilings() -> dict:
    """U2 step 2: exact rational ceilings at the registered MES dipole
    amplitude + the ceiling-ordering instantiation + the CF4 containment."""
    reg = eps_registry_provenance()
    eps1_float = float(reg["ssot_registry"]["values"]["eps1"])
    eps1 = sp.Rational(sp.nsimplify(eps1_float, rational=True))
    ceil_r3 = sp.Rational(3, 2) * eps1 ** 2
    ceil_r5 = sp.Rational(5, 2) * eps1 ** 2
    # exact endpoint evaluations of the identified fingerprint intervals
    s, R = _exact_ratios_in_s()
    r3_at = sp.simplify(R[3].subs(s, eps1))
    r5_at = sp.simplify(R[5].subs(s, eps1))
    endpoint_within = bool(sp.N(1 - r3_at, 30) <= sp.N(ceil_r3, 30)
                           and sp.N(r5_at - 1, 30) <= sp.N(ceil_r5, 30))
    # ceiling map strictly increasing (exact derivative)
    uu = sp.Symbol("uu", positive=True)
    increasing = bool(sp.diff(sp.Rational(3, 2) * uu ** 2, uu).subs(uu, 1) > 0)
    # MES ordering -> ordered ceilings (formal order-preservation instantiation)
    order = mes_ordering_theorem()
    ordering_key = "sigma_gt_omega_on_positive_orthant & omega_gt_accel_on_positive_orthant"
    mes_ordered = bool(order["sigma_gt_omega_on_positive_orthant"]
                       and order["omega_gt_accel_on_positive_orthant"]
                       and order["ordering_holds_at_ssot_eps"])
    B = eps_registry_provenance()["registered_ceilings_from_ssot"]
    b_sigma, b_omega, b_accel = (float(B["B_sigma"]), float(B["B_omega"]),
                                 float(B["B_accel"]))
    ceilings_ordered = ((3 / 2) * b_sigma ** 2 > (3 / 2) * b_omega ** 2
                        > (3 / 2) * b_accel ** 2)
    # CF4 containment: same rapidity in both channels
    s_cf4 = float(np.tanh(BETA_CF4))
    fp_cf4 = 1.5 * s_cf4 ** 2
    ceil_num = 1.5 * eps1_float ** 2
    return {
        "eps1_registered": eps1_float,
        "eps1_exact_rational": str(eps1),
        "ceiling_R3_exact": str(ceil_r3),
        "ceiling_R5_exact": str(ceil_r5),
        "ceiling_R3_float": float(ceil_r3),
        "ceiling_R5_float": float(ceil_r5),
        "identified_interval_R3": [float(sp.N(r3_at, 20)), 1.0],
        "identified_interval_R5": [1.0, float(sp.N(r5_at, 20))],
        "endpoints_within_quadratic_envelopes": endpoint_within,
        "ceiling_map_strictly_increasing": increasing,
        "mes_ordering_source": ordering_key,
        "mes_ordering_holds": mes_ordered,
        "ordered_ceiling_triple_from_mes_budgets": bool(ceilings_ordered),
        "ordered_ceiling_disclosure": "formal order-preservation instantiation "
                                      "of B_sigma > B_omega > B_accel through "
                                      "the strictly increasing ceiling map; the "
                                      "MES budgets are NOT three physical "
                                      "rapidity ceilings",
        "cf4_containment": {
            "beta_cf4": BETA_CF4,
            "s_cf4_tanh": s_cf4,
            "fingerprint_3half_s2": fp_cf4,
            "mes_dipole_ceiling_3half_eps1_2": ceil_num,
            "fingerprint_below_ceiling": bool(fp_cf4 < ceil_num),
        },
    }


def teff_unification_seal() -> dict:
    """Fail-closed U1+U2 seal: the beta-channel correspondence + MES-to-Teff
    fingerprint ceilings, coupling the MES registry, the comparator tilt
    sector, and the active Teff lane in one exact statement."""
    red = antipodal_boost_reduction()
    cor = beta_channel_correspondence()
    env = fingerprint_envelope_proofs()
    ceil = fingerprint_ceilings()
    ok = (red["boost_pole_identity_exact"] and red["s_equals_tanh_beta_exact"]
          and red["s_squared_equals_t_over_2_plus_t_exact"]
          and cor["R4_identically_one"] and cor["leading_coeffs_exact"]
          and cor["antipodal_specificity_pin"]
          and env["all_envelopes_proved"]
          and env["pointwise_sum_ordering_numeric_min"] > 0
          and ceil["endpoints_within_quadratic_envelopes"]
          and ceil["ceiling_map_strictly_increasing"]
          and ceil["mes_ordering_holds"]
          and ceil["ordered_ceiling_triple_from_mes_budgets"]
          and ceil["cf4_containment"]["fingerprint_below_ceiling"])
    return {
        "seal": "egs3.teff_unification",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "numpy_version": np.__version__,
        "theorem_U1": "one boost rapidity feeds both channels: s = tanh(beta) "
                      "exactly under the antipodal two-point reduction; "
                      "s^2 = t/(2+t) with t = Omega_tilt/((1+w) Omega_m); "
                      "R_3 - 1 = -(3/4) t + O(t^2), R_5 - 1 = +(5/4) t + "
                      "O(t^2), R_4 == 1 identically (antipodal-specific: "
                      "single species gives -(3/2))",
        "theorem_U2": "proved envelopes 1 - R_3 <= (3/2) s^2 and R_5 - 1 <= "
                      "(5/2) s^2 on 0 < s < 1 (polynomial root isolation); "
                      "exact rational ceilings at the registered MES dipole "
                      "amplitude; strictly-increasing ceiling map carries the "
                      "MES ordering; CF4 rapidity contained in both channels",
        "antipodal_boost_reduction": red,
        "beta_channel_correspondence": cor,
        "fingerprint_envelope_proofs": env,
        "fingerprint_ceilings": ceil,
        "disclosed_caveats": [
            "two-point antipodal reduction of a continuum boost sky "
            "(registered toy anchor, not an angular average)",
            "the two-temperature mixture is the Teff equal-information "
            "representation anchor, NOT a predicted CMB spectral distortion",
            "rapidity-vs-velocity beta differs at O(beta^3) ~ 1e-9 (disclosed)",
            "s_max = eps_1 uses the leading-order dipole <-> boost "
            "identification",
            "the ordered ceiling triple is a formal order-preservation "
            "instantiation, not three physical rapidity ceilings",
            "pointwise R_5 + R_3 >= 2 is numerically certified only",
        ],
        "claim_boundary": "exact symbolic correspondence between registered "
                          "in-repo objects (MES registry, comparator tilt "
                          "sector, Teff representative anchor); "
                          "diagnostic_only; no data, signal-discovery, "
                          "spectral-distortion, "
                          "Bianchi-class-identification-of-the-sky, "
                          "native-solver-produced, or probabilistic-inference "
                          "claim",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(teff_unification_seal(), indent=2, default=float))
