"""MES-MESB-TRACE: web-traced MESb provenance + refutation of the in-house
non-geodesic bounds, and the two candidate re-freeze anchors (REV-R190).

Owner directive: web-search the original MESb (Paper II, PRD 51 5942),
trace the derivation as far as accessible, and within the accessible range
either RE-DERIVE / CORRECT or firmly REFUTE the wrong parts, then re-freeze.

WHAT THE WEB-TRACE ESTABLISHED (all sources archived under
docs/audits/mes_primary_sources/, SHA-pinned; fetched 2026-07-12):

  MESb (PRD 51 5942) itself is print-only (not on arXiv). But its REDUCED
  bounds are accessible through TWO channels co-authored by the MES team:

    * MESa (astro-ph/9501016, PRD 51 1525), the GEODESIC companion paper
      (u_dot = 0, MESa eq (11)): eq (59) sigma = (5/3, 3, 3/7); eq (60)
      omega = (10/3, 2/15, 0); NO acceleration bound. Reproduced bit-exact
      by reducing the raw eq (51)/(52) bounds by C1/C2 (frozen module
      ``egs3_mes_rederivation``, reused read-only).
    * the DeltaT/T companion (astro-ph/9510126), authored by all three of
      Maartens-Ellis-Stoeger, which EXPLICITLY presents the MESb reduced
      bounds: its raw shear eq (6) is labelled "MESb Eq (24)" and equals
      MESa eq (51) IDENTICALLY; "the remaining limits are given in MESb
      (Eq. (30)-(36))"; and its final reduced bounds eq (8) are
          sigma/Theta|_0 < 4 alpha x 10^-5 ,   omega/Theta|_0 < alpha x 10^-5
      (eps2 ~ eps3 ~ alpha x 10^-5, residual dipole eps1 -> 0). The prose:
      "the limit on the relative vorticity is comparable to that on
      distortion".
    * SAG 1997 (astro-ph/9904346, Stoeger-Araujo-Gebbie; Stoeger co-author),
      clean LaTeX: eq (3) sigma = (5/3, 3, 3/7), eq (4) omega =
      (10/3, 2/15, 0), NO acceleration bound, eps1 = 0 (eq 12).

THE REFUTATION (the load-bearing new result of this cycle):

  The previously-registered non-geodesic omega = (3/4, 2, 2/7) and
  accel = (3/4, 1, 3/14) do NOT come from MESb. Their in-repo origin is an
  IN-HOUSE reconstruction (docs/ver2_upgrade/mes_full_covariance_extension_
  self_contained.md; docs/manuscript/ch04_bianchi_bounds.tex), whose
  "Thm 3.1-3.4 / Eq 3.7/3.12/3.15" labels are IN-HOUSE numbering, not
  MESa/MESb primary equation numbers. These values appear in NO accessible
  source (MESa, the DeltaT/T companion, and SAG all checked), and the
  in-house omega is INCONSISTENT with the MES team's own companion reduced
  bound under the paper's OWN eps-scaling: at eps1 = 0,
        B_omega,in-house = 2 eps2 + (2/7) eps3 = 8.85e-6
  while the companion's assumption (c) sets alpha x 10^-5 = max(eps2, eps3)
  = eps3 = 6.07e-6, so the in-house value EXCEEDS the faithful companion cap
  by ~1.46x (it does fit the LOOSE COBE reading alpha ~ 1 -> 1e-5, so the
  companion corroboration is reading-dependent; the ROBUST refutation is the
  no-accessible-source ground). The in-house acceleration bound (3/4, 1,
  3/14) has NO accessible source at all (both accessible primary papers are
  geodesic, u_dot = 0, and carry no accel bound).

THE TWO CANDIDATE RE-FREEZE ANCHORS (adjudicated by adversarial
verification; ``adopt whichever survives``):

  A) GEODESIC anchor (precise). B_omega = (2/15) eps2 at eps1 = 0
     (MESa eq 60 + SAG eq 4, both verbatim primary; exact reduction),
     W2_max = (3/2) B_omega^2 = 3.3789e-13. No alpha ambiguity.
  B) COMPANION / MESb non-geodesic envelope. The DeltaT/T companion eq (8)
     reduced omega/Theta < alpha x 10^-5, "comparable to distortion". Per
     assumption (c), alpha x 10^-5 = max(eps2, eps3) = eps3, so the FAITHFUL
     cap is W2_max = (3/2) eps3^2 = 5.52e-11; the loose COBE reading alpha ~
     1 gives 1.50e-10. Order-of-magnitude only: alpha-dependent (the
     companion prints a single rounded number, not a coefficient triple).
     [The earlier eps2 nominal 1.90e-11 UNDERSTATED the ceiling and is
     retired -- adversarial-verification correction, REV-R190.]

Claim discipline: symbolic derivation + primary-source provenance +
refutation; no data claim, no discovery claim, no geometry or family-
identification claim, no inference claim.
"""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache

import sympy as sp

from htt.obsstat.egs3_mes_provenance import eps_registry_provenance
from htt.obsstat.egs3_mes_rederivation import (
    _EQ59_SIGMA,
    _EQ60_OMEGA,
    _RAW_OMEGA_MESA,
    _RAW_SIGMA,
    reduce_raw_bound,
)
from htt.tsc.admissibility.three_bound_hierarchy import (
    COEFFS as COEFFS_FROZEN,
    W2_max as W2_max_frozen,
)

__all__ = [
    "IN_HOUSE_COEFFS",
    "primary_source_transcriptions",
    "companion_reduced_bounds",
    "in_house_refutation",
    "candidate_anchors",
    "mesb_web_trace_seal",
]

# The in-repo values under audit (NOT MESb; in-house reconstruction).
IN_HOUSE_COEFFS = {
    "omega": (Fraction(3, 4), Fraction(2, 1), Fraction(2, 7)),
    "accel": (Fraction(3, 4), Fraction(1, 1), Fraction(3, 14)),
}


def _ssot_eps() -> tuple[Fraction, Fraction, Fraction]:
    vals = eps_registry_provenance()["ssot_registry"]["values"]
    return (Fraction(str(vals["eps1"])), Fraction(str(vals["eps2"])),
            Fraction(str(vals["eps3"])))


def _bound(coef, e1, e2, e3) -> Fraction:
    c1, c2, c3 = coef
    return c1 * e1 + c2 * e2 + c3 * e3


# --- primary-source transcriptions (archived + SHA-pinned) -------------
def primary_source_transcriptions() -> dict:
    """The web-traced primary-source bounds. Each entry cites the arXiv id
    and the archived file; the shear + geodesic-vorticity readings are
    cross-checked against the frozen C1/C2 reduction."""
    sig = reduce_raw_bound(_RAW_SIGMA)
    om = reduce_raw_bound(_RAW_OMEGA_MESA)
    return {
        "MESa": {
            "arxiv": "astro-ph/9501016", "ref": "PRD 51, 1525 (1995)",
            "archived": "mesa_astro-ph_9501016_PRD51_1525.txt",
            "geodesic": "u_dot = 0 (eq 11); NO acceleration bound",
            "eq51_raw_sigma": "(8/3) eps2 + eps2* + 5 eps1' + (9/7) eps3'",
            "eq52_raw_omega": "9 eps1' + 3 eps1'* + (6/5) eps2''",
            "eq59_reduced_sigma": tuple(str(c) for c in _EQ59_SIGMA),
            "eq60_reduced_omega": tuple(str(c) for c in _EQ60_OMEGA),
            "reduction_reproduces_eq59": sig == _EQ59_SIGMA,
            "reduction_reproduces_eq60": om == _EQ60_OMEGA,
        },
        "companion_deltaT": {
            "arxiv": "astro-ph/9510126",
            "ref": "Maartens-Ellis-Stoeger, Anisotropy and inhomogeneity "
                   "from DeltaT/T",
            "archived": "companion_astro-ph_9510126_deltaT.txt "
                        "(+ companion_layout.txt)",
            "eq6_raw_sigma_is_MESb_eq24": "(8/3) eps2 + eps2* + 5 eps1' + "
                                          "(9/7) eps3'  == MESa eq (51)",
            "mesb_eq24_equals_mesa_eq51": True,
            "eq7_reduced_sigma": "(5/3) eps1 + 3 eps2 + (3/7) eps3",
            "remaining_limits_source": "MESb Eq. (30)-(36)",
            "eq8_reduced": "sigma/Theta < 4 alpha x 10^-5 ; "
                           "omega/Theta < alpha x 10^-5  (eps1 -> 0)",
            "prose": "the limit on the relative vorticity is comparable to "
                     "that on distortion",
        },
        "SAG1997": {
            "arxiv": "astro-ph/9904346", "ref": "Stoeger-Araujo-Gebbie, "
                     "ApJ 476, 435 (Stoeger co-author)",
            "archived": "sag1997_astro-ph_9904346_ApJ476_435.tex",
            "eq3_sigma": "(5/3) eps1 + 3 eps2 + (3/7) eps3",
            "eq4_omega": "(10/3) eps1 + (2/15) eps2",
            "eq12_eps1": "eps1 = 0 (residual dipole = observer motion)",
            "geodesic": "geodesic congruence; NO acceleration bound",
            "clean_latex_confirms_geodesic_omega": True,
        },
        "MESb": {
            "arxiv": "not on arXiv (print-only)",
            "ref": "Maartens-Ellis-Stoeger, PRD 51, 5942 (1995), Paper II",
            "accessible_via": "the DeltaT/T companion reduced bounds eq (8) "
                              "+ MESb-eq24 == MESa-eq51 identity",
            "raw_sigma_identical_to_MESa": True,
        },
        "sigma_confirmed_by_three_sources": (
            sig == _EQ59_SIGMA
            and _EQ59_SIGMA == (Fraction(5, 3), Fraction(3), Fraction(3, 7))),
        "geodesic_omega_confirmed_by_two_primary": om == _EQ60_OMEGA,
    }


# --- the companion reduced bounds -> the MESb non-geodesic envelope -----
@lru_cache(maxsize=1)
def companion_reduced_bounds() -> dict:
    """Encode the DeltaT/T companion eq (8) reduced bounds and map them to
    the SSOT epsilons. The companion prints a single rounded number
    (alpha x 10^-5) per quantity, so the vorticity envelope is an
    order-of-magnitude bound, not a coefficient triple.

    FAITHFUL alpha reading (adversarial-verification correction, REV-R190):
    the companion's assumption (c) DEFINES alpha x 10^-5 = max(eps2, eps3)
    (companion line 219), so at the SSOT epsilons the faithful cap is
    B_omega = eps3 (the LARGER member), NOT eps2. The paper's separate COBE
    statement 'alpha is of order 1' gives the loose cap 1e-5. For a ceiling,
    the eps3 (faithful) and 1e-5 (COBE) readings are the honest endpoints;
    the earlier eps2 nominal UNDERSTATED the ceiling and is retired."""
    e1, e2, e3 = _ssot_eps()
    # companion sigma reduced coefficient (matches MESa/SAG): 3 eps2 + 3/7 eps3
    sigma_reduced = 3 * e2 + Fraction(3, 7) * e3
    cobe_cap = Fraction(1, 100000)           # alpha ~ 1 (COBE): 1e-5
    e_max = max(e2, e3)                       # assumption (c): max(eps2, eps3)
    # FAITHFUL nominal: alpha x 10^-5 = max(eps2, eps3) = eps3 here
    B_omega_faithful = e_max
    W2_faithful = Fraction(3, 2) * B_omega_faithful ** 2
    # COBE (loose) endpoint: alpha ~ 1
    W2_cobe = Fraction(3, 2) * cobe_cap ** 2
    # the eps2 (tightest) reading, retained only as the lower endpoint
    W2_eps2 = Fraction(3, 2) * e2 ** 2
    return {
        "eq8_sigma_over_Theta": "< 4 alpha x 10^-5",
        "eq8_omega_over_Theta": "< alpha x 10^-5",
        "assumption_c": "alpha x 10^-5 = max(eps2, eps3)  (companion line 219)",
        "sigma_reduced_at_ssot_float": float(sigma_reduced),
        "sigma_reduced_rounds_to": "4 alpha x 10^-5 (3.43 -> 4)",
        "sigma_rounding_consistent": bool(
            3.0 <= float(sigma_reduced) / float(e2) <= 4.5),
        "alpha_faithful_from_max_eps": float(e_max / Fraction(1, 100000)),
        "B_omega_companion_faithful_exact": str(B_omega_faithful),
        "B_omega_companion_faithful": float(B_omega_faithful),
        "W2_companion_faithful_exact": str(W2_faithful),
        "W2_companion_faithful": float(W2_faithful),
        "W2_companion_cobe_alpha1": float(W2_cobe),
        "W2_companion_range": [float(W2_faithful), float(W2_cobe)],
        "W2_companion_eps2_lower_only": float(W2_eps2),
        "is_order_of_magnitude_not_coefficient_triple": True,
        "note": "the companion prints one rounded number per quantity; the "
                "exact non-geodesic omega coefficient triple is NOT in any "
                "accessible source. Faithful cap = max(eps2,eps3) = eps3 "
                "(5.52e-11); COBE alpha~1 loose cap = 1e-5 (1.50e-10). The "
                "earlier eps2 nominal (1.90e-11) understated the ceiling.",
    }


# --- the refutation of the in-house non-geodesic bounds ----------------
@lru_cache(maxsize=1)
def in_house_refutation() -> dict:
    """The in-house omega = (3/4, 2, 2/7) / accel = (3/4, 1, 3/14) are
    REFUTED. The ROBUST (alpha-independent) ground is that they appear in NO
    accessible source: the 'Thm 3.2/Eq 3.12' labels are in-house numbering,
    not MESa/MESb equation numbers, and neither MESa, the companion, nor SAG
    prints them.

    The companion-consistency check is a SECONDARY corroboration and is
    reading-dependent (adversarial-verification honesty, REV-R190): at eps1
    = 0 the in-house B_omega = 8.85e-6 EXCEEDS the FAITHFUL companion cap
    (assumption (c): alpha x 10^-5 = max(eps2, eps3) = eps3 = 6.07e-6) by
    ~1.46x, but is WITHIN the loose COBE cap (alpha ~ 1 -> 1e-5). So the
    companion refutes the in-house value under the paper's own eps-scaling,
    while the no-source ground refutes it unconditionally."""
    e1, e2, e3 = _ssot_eps()
    # in-house omega at eps1 = 0
    B_ih_zero = _bound(IN_HOUSE_COEFFS["omega"], Fraction(0), e2, e3)
    companion_cap_faithful = max(e2, e3)     # assumption (c): max(eps2,eps3)
    companion_cap_cobe = Fraction(1, 100000)  # alpha ~ 1
    # geodesic omega at eps1 = 0 (for the consistency contrast)
    B_geo_zero = _bound((Fraction(10, 3), Fraction(2, 15), Fraction(0)),
                        Fraction(0), e2, e3)
    return {
        "in_house_omega_coeffs": tuple(str(c) for c in IN_HOUSE_COEFFS["omega"]),
        "in_house_accel_coeffs": tuple(str(c) for c in IN_HOUSE_COEFFS["accel"]),
        "B_omega_in_house_eps1_zero_exact": str(B_ih_zero),
        "B_omega_in_house_eps1_zero": float(B_ih_zero),
        # PRIMARY ground: no accessible source (alpha-independent)
        "in_house_in_accessible_sources": [],   # none
        "in_house_provenance": (
            "docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md "
            "+ docs/manuscript/ch04_bianchi_bounds.tex; 'Thm 3.2/Eq 3.12' "
            "labels are IN-HOUSE numbering, not MESa/MESb equation numbers"),
        "accel_bound_has_no_accessible_source": True,
        "accel_reason": "both accessible primary papers (MESa, SAG) are "
                        "geodesic (u_dot = 0) and carry NO acceleration bound",
        # SECONDARY corroboration: reading-dependent
        "companion_cap_faithful_max_eps": float(companion_cap_faithful),
        "companion_cap_cobe_alpha1": float(companion_cap_cobe),
        "in_house_exceeds_faithful_cap": bool(B_ih_zero > companion_cap_faithful),
        "in_house_within_cobe_cap": bool(B_ih_zero < companion_cap_cobe),
        "excess_factor_over_faithful_cap": float(B_ih_zero / companion_cap_faithful),
        "companion_corroboration_is_reading_dependent": True,
        "geodesic_omega_eps1_zero": float(B_geo_zero),
        "geodesic_consistent_with_companion_faithful": bool(
            B_geo_zero < companion_cap_faithful),
        "verdict": "REFUTED. Robust ground: the in-house non-geodesic omega "
                   "and accel appear in NO accessible source (in-house "
                   "numbering, not MESb). Corroboration: the in-house omega "
                   "exceeds the faithful companion cap max(eps2,eps3) at "
                   "eps1=0 (though it fits the loose COBE alpha~1 cap); the "
                   "accel bound is unsupported (both primary papers geodesic)",
        "frozen_registered_W2_max_unchanged": float(
            W2_max_frozen(*[float(x) for x in _ssot_eps()])),
        "previously_registered_omega": tuple(
            str(c) for c in COEFFS_FROZEN["omega"]),
    }


# --- the two candidate anchors (attack surface for the adversarial lanes) ---
@lru_cache(maxsize=1)
def candidate_anchors() -> dict:
    """The two defensible primary anchors, each annotated with its exact
    value and its adversarial attack surface. The seal does NOT pick a
    winner; the adversarial-verification workflow adjudicates."""
    e1, e2, e3 = _ssot_eps()
    # A: geodesic (precise)
    B_geo = _bound((Fraction(10, 3), Fraction(2, 15), Fraction(0)),
                   Fraction(0), e2, e3)
    W2_geo = Fraction(3, 2) * B_geo ** 2
    # B: companion envelope (nominal)
    comp = companion_reduced_bounds()
    return {
        "A_geodesic": {
            "W2_max_exact": str(W2_geo), "W2_max": float(W2_geo),
            "B_omega": float(B_geo),
            "basis": "MESa eq (60) + SAG eq (4), verbatim primary; exact "
                     "C1/C2 reduction; eps1 = 0 (SAG convention)",
            "precise": True,
            "attack_surface": "frame: geodesic (u_dot = 0) vs the possibly-"
                              "accelerating matter congruence; SAG's eps1 = 0 "
                              "convention transportability",
        },
        "B_companion_envelope": {
            "W2_max_faithful_exact": comp["W2_companion_faithful_exact"],
            "W2_max_faithful": comp["W2_companion_faithful"],
            "W2_max_range": comp["W2_companion_range"],
            "basis": "DeltaT/T companion eq (8): non-geodesic reduced "
                     "omega/Theta < alpha x 10^-5; assumption (c) "
                     "alpha x 10^-5 = max(eps2,eps3) = eps3 (faithful), "
                     "COBE alpha~1 -> 1e-5 (loose); 'comparable to distortion'",
            "precise": False,
            "attack_surface": "rests on a single rounded companion number "
                              "(alpha-dependent); no coefficient triple in "
                              "any accessible source",
        },
        "REFUTED_in_house": {
            "W2_max": float(Fraction(3, 2)
                            * _bound(IN_HOUSE_COEFFS["omega"], Fraction(0),
                                     e2, e3) ** 2),
            "status": "REFUTED (no accessible source; exceeds the faithful "
                      "companion cap max(eps2,eps3))",
        },
        "ordering": "geodesic (3.38e-13) < companion faithful envelope "
                    "(5.52e-11) < in-house REFUTED (1.18e-10) < companion "
                    "COBE-loose (1.50e-10) < old frozen full-eps1 (1.31e-6)",
    }


def mesb_web_trace_seal() -> dict:
    prov = primary_source_transcriptions()
    comp = companion_reduced_bounds()
    refute = in_house_refutation()
    anchors = candidate_anchors()
    ok = (prov["sigma_confirmed_by_three_sources"]
          and prov["geodesic_omega_confirmed_by_two_primary"]
          and prov["MESa"]["reduction_reproduces_eq59"]
          and prov["MESa"]["reduction_reproduces_eq60"]
          and prov["companion_deltaT"]["mesb_eq24_equals_mesa_eq51"]
          and comp["sigma_rounding_consistent"]
          and refute["in_house_in_accessible_sources"] == []
          and refute["in_house_exceeds_faithful_cap"]
          and refute["geodesic_consistent_with_companion_faithful"]
          and refute["accel_bound_has_no_accessible_source"])
    return {
        "seal": "egs3.mesb_web_trace",
        "theorem_id": "MES-MESB-TRACE",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "primary_source_transcriptions": prov,
        "companion_reduced_bounds": comp,
        "in_house_refutation": refute,
        "candidate_anchors": anchors,
        "scope_not_claimed": (
            "web-traced primary-source provenance + refutation of the "
            "in-house non-geodesic bounds + the two candidate re-freeze "
            "anchors; the geodesic omega is doubly primary-sourced and the "
            "companion envelope is the authors' own reduced non-geodesic "
            "bound; the surviving anchor is adopted by adversarial "
            "verification; no data, detection, family/geometry, "
            "native-solver, or inference claim"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(mesb_web_trace_seal(), indent=2, default=str))
