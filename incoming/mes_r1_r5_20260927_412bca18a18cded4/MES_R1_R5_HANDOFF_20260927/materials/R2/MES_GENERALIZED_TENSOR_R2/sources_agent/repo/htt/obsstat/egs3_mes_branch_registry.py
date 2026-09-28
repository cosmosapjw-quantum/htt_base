"""MES-BR: MES coefficient branch registry + eps1 attribution triple (v9,
REV-R173; answers the 2026-07-10 reviews' MES provenance findings — R1 3.5
branch split, R2 V3 dual-ceiling card).

BRANCHES (coefficient provenance; the frozen registry values are UNCHANGED —
this module only classifies them and carries the attribution-conditional
alternatives alongside):

  MES_G  (VERIFIED, geodesic)
      sigma  (5/3, 3, 3/7)   rederived bit-exact from the archived primary
                             source (mes_rederivation seal) and printed as
                             SAG1997 eq (3);
      omega  (10/3, 2/15, 0) geodesic triple printed as SAG1997 eq (4) and
                             equal to MESa eq (60); NOT the registered triple;
      accel  ---             NO acceleration bound exists in any accessible
                             source (the congruence is geodesic there).
  MES_NG (UNVERIFIED, non-geodesic)
      omega  (3/4, 2, 2/7)   the REGISTERED triple; attributed to MESb
                             (PRD 51, 5942; print-only, inaccessible);
                             primary_sourced_not_rederivable.
      accel  (3/4, 1, 3/14)  the REGISTERED triple; appears in NO accessible
                             source.
  ACCEL_WITHHELD
      the acceleration ceiling is WITHHELD from every observational lane
      until an accessible derivation exists.

EPS1 ATTRIBUTION TRIPLE. The single registered number 771/625000 = 1.2336e-3
wears several hats; this registry names them so no lane can silently swap
attributions:

  eps1_observer_boost      = 771/625000 -- the observed CMB dipole dT/T,
                             numerically the solar kinematic dipole
                             beta = v/c (369.82 km/s);
  eps1_cosmological        = 0          -- the SAG1997 convention: the paper
                             attributes the whole dipole to observer peculiar
                             motion and sets eps1 = 0 in its equations
                             (archived tex, eqs 12 and the epsilon reset);
  eps1_conservative_total  = 771/625000 -- the full observed dipole with no
                             attribution split; this is what the frozen
                             B_sigma/B_omega evaluators currently consume.

W^2 CEILINGS (attribution-conditional; ALL carried, NONE promoted):

  registered        = (3/2) B_omega_NG(ssot eps)^2   = 1.3087e-6
                      (bit-identical to the frozen W2_max anchor);
  hybrid_literature = (3/2) B_omega_G(ssot eps)^2    = 2.537e-5
                      -- a HYBRID: geodesic (literature) coefficients times
                      the FULL observer dipole (eps1_conservative_total),
                      i.e. NOT SAG's own convention; comparison-only;
  sag_consistent    = (3/2) B_omega_G(0, eps2, eps3)^2 ~ 3.4e-13
                      -- the geodesic coefficients under SAG's own eps1 = 0.

  DOMINANCE DISCLOSURE: under both coefficient branches the eps1 term
  carries ~99% of B_omega at the ssot epsilons, so every nonzero W^2
  ceiling in play is essentially an observer-boost quantity; the K5 lower
  endpoint is therefore keyed to the eps1 ATTRIBUTION CHOICE, and the card
  carries all three ceilings as labeled branches.

Frozen surfaces untouched: three_bound_hierarchy (COEFFS, W2_max),
egs3_mes_provenance, egs3_mes_rederivation are imported READ-ONLY.
Claim discipline: provenance classification + exact rational algebra at tier
diagnostic_only; no observational claim is enabled by any branch.
"""
from __future__ import annotations

from fractions import Fraction

import sympy as sp

from htt.tsc.admissibility.three_bound_hierarchy import COEFFS, W2_max
from htt.obsstat.egs3_mes_provenance import eps_registry_provenance
from htt.obsstat.egs3_mes_rederivation import sag1997_discrepancy_report

__all__ = [
    "GEODESIC_OMEGA_TRIPLE",
    "EPS1_TRIPLE",
    "branch_table",
    "eps1_attribution_triple",
    "w2_ceiling_branches",
    "mes_branch_registry_seal",
]

#: SAG1997 eq (4) / MESa eq (60) geodesic vorticity triple (NOT registered).
GEODESIC_OMEGA_TRIPLE = (Fraction(10, 3), Fraction(2, 15), Fraction(0))

EPS1_TRIPLE = {
    "eps1_observer_boost": Fraction(771, 625000),
    "eps1_cosmological": Fraction(0),
    "eps1_conservative_total": Fraction(771, 625000),
}

_SOLAR_V_KMS = 369.82
_C_KMS = 299792.458


def branch_table() -> dict:
    """The MES coefficient branch registry (provenance classification)."""
    return {
        "MES_G": {
            "status": "VERIFIED_GEODESIC",
            "sigma": {
                "triple": tuple(str(c) for c in COEFFS["sigma"]),
                "provenance": "rederived bit-exact from the archived primary "
                              "source (mes_rederivation seal); printed as "
                              "SAG1997 eq (3)",
            },
            "omega": {
                "triple": tuple(str(c) for c in GEODESIC_OMEGA_TRIPLE),
                "provenance": "SAG1997 eq (4) == MESa eq (60); geodesic "
                              "congruence; NOT the registered triple",
            },
            "accel": {
                "triple": None,
                "provenance": "no acceleration bound exists in any "
                              "accessible source (geodesic congruence)",
            },
        },
        "MES_NG": {
            "status": "UNVERIFIED_NON_GEODESIC",
            "omega": {
                "triple": tuple(str(c) for c in COEFFS["omega"]),
                "provenance": "REGISTERED; attributed to MESb (PRD 51, 5942; "
                              "print-only, inaccessible); "
                              "primary_sourced_not_rederivable",
            },
            "accel": {
                "triple": tuple(str(c) for c in COEFFS["accel"]),
                "provenance": "REGISTERED; appears in NO accessible source",
            },
        },
        "ACCEL_WITHHELD": {
            "status": "WITHHELD",
            "rule": "the acceleration ceiling enters NO observational lane "
                    "until an accessible derivation exists",
        },
        "registered_values_unchanged": True,
    }


def eps1_attribution_triple() -> dict:
    """The eps1 naming split with the numeric-coincidence cross-check."""
    beta_solar = _SOLAR_V_KMS / _C_KMS
    eps1 = float(EPS1_TRIPLE["eps1_observer_boost"])
    rel = abs(eps1 - beta_solar) / beta_solar
    return {
        "eps1_observer_boost": str(EPS1_TRIPLE["eps1_observer_boost"]),
        "eps1_observer_boost_float": eps1,
        "eps1_cosmological": str(EPS1_TRIPLE["eps1_cosmological"]),
        "eps1_cosmological_rationale": "SAG1997 attributes the whole dipole "
                                       "to observer peculiar motion and sets "
                                       "eps1 = 0 (archived tex)",
        "eps1_conservative_total": str(EPS1_TRIPLE["eps1_conservative_total"]),
        "consumed_by_frozen_evaluators": "eps1_conservative_total",
        "solar_kinematic_beta": beta_solar,
        "relative_difference_to_solar_beta": rel,
        "numeric_coincidence_confirmed": bool(rel < 2e-4),
        "reading": "the registered eps1 IS the observed CMB dipole dT/T, "
                   "numerically the solar kinematic dipole; it is an "
                   "observer-boost quantity, not a cosmological vorticity "
                   "bound",
    }


def _b_omega(triple, e1: Fraction, e2: Fraction, e3: Fraction) -> Fraction:
    c1, c2, c3 = triple
    return c1 * e1 + c2 * e2 + c3 * e3


def w2_ceiling_branches() -> dict:
    """The three attribution-conditional W^2 ceilings, exact where possible."""
    prov = eps_registry_provenance()
    vals = prov["ssot_registry"]["values"]
    e1 = Fraction(str(vals["eps1"]))
    e2 = Fraction(str(vals["eps2"]))
    e3 = Fraction(str(vals["eps3"]))

    b_ng = _b_omega(COEFFS["omega"], e1, e2, e3)
    b_g = _b_omega(GEODESIC_OMEGA_TRIPLE, e1, e2, e3)
    b_g_sag = _b_omega(GEODESIC_OMEGA_TRIPLE, Fraction(0), e2, e3)

    w2_registered = Fraction(3, 2) * b_ng ** 2
    w2_hybrid = Fraction(3, 2) * b_g ** 2
    w2_sag = Fraction(3, 2) * b_g_sag ** 2

    # dominance shares of the eps1 term in each B_omega
    share_ng = float(COEFFS["omega"][0] * e1 / b_ng)
    share_g = float(GEODESIC_OMEGA_TRIPLE[0] * e1 / b_g)

    # cross-checks against the frozen surfaces (read-only)
    frozen_w2 = W2_max(float(e1), float(e2), float(e3))
    sag_report = sag1997_discrepancy_report()
    return {
        "eps_inputs": {"eps1": str(e1), "eps2": str(e2), "eps3": str(e3),
                       "eps1_attribution": "eps1_conservative_total "
                                           "(observer-boost dominated)"},
        "registered": {
            "value_float": float(w2_registered),
            "value_exact": str(w2_registered),
            "coefficients": "MES_NG omega (3/4, 2, 2/7); UNVERIFIED "
                            "provenance (MESb print-only)",
            "bit_identical_to_frozen_W2_max":
                bool(float(w2_registered) == frozen_w2),
            "eps1_term_share_of_B_omega": share_ng,
        },
        "hybrid_literature": {
            "value_float": float(w2_hybrid),
            "value_exact": str(w2_hybrid),
            "coefficients": "MES_G omega (10/3, 2/15, 0); VERIFIED geodesic",
            "hybrid_disclosure": "geodesic (literature) coefficients times "
                                 "the FULL observer dipole — NOT SAG's own "
                                 "eps1=0 convention; comparison-only",
            "matches_mes_rederivation_report": bool(
                abs(float(w2_hybrid)
                    - sag_report["w2_ceiling_literature_supported_comparison_only"])
                / float(w2_hybrid) < 1e-12),
            "eps1_term_share_of_B_omega": share_g,
        },
        "sag_consistent": {
            "value_float": float(w2_sag),
            "value_exact": str(w2_sag),
            "coefficients": "MES_G omega (10/3, 2/15, 0) under SAG's own "
                            "eps1 = 0",
            "reading": "with the dipole attributed entirely to the observer "
                       "boost (SAG convention) the geodesic vorticity "
                       "ceiling collapses by ~12 orders of magnitude — the "
                       "eps2 term carries it",
        },
        "ordering": {
            "sag_lt_registered_lt_hybrid": bool(w2_sag < w2_registered
                                                < w2_hybrid),
            "hybrid_over_registered": float(w2_hybrid / w2_registered),
        },
        "dominance_disclosure": "the eps1 term carries "
                                f"{share_ng:.2%} (registered) / "
                                f"{share_g:.2%} (geodesic) of B_omega at the "
                                "ssot epsilons; every nonzero ceiling is "
                                "essentially an observer-boost quantity and "
                                "the K5 lower endpoint is keyed to the eps1 "
                                "attribution choice",
        "no_branch_promoted": True,
    }


def mes_branch_registry_seal() -> dict:
    """Fail-closed MES-BR seal (registry id MES-BR)."""
    table = branch_table()
    eps1 = eps1_attribution_triple()
    ceilings = w2_ceiling_branches()
    # exact-ordering re-derivation of the 19.9x exclusion factor (sympy)
    ratio = sp.Rational(ceilings["hybrid_literature"]["value_exact"]) / \
        sp.Rational(ceilings["registered"]["value_exact"])
    ok = (table["registered_values_unchanged"]
          and eps1["numeric_coincidence_confirmed"]
          and ceilings["registered"]["bit_identical_to_frozen_W2_max"]
          and ceilings["hybrid_literature"]["matches_mes_rederivation_report"]
          and ceilings["ordering"]["sag_lt_registered_lt_hybrid"]
          and 15 < float(ratio) < 25)
    return {
        "seal": "egs3.mes_branch_registry",
        "theorem_id": "MES-BR",
        "status": "PASS" if ok else "FAIL",
        "branch_table": table,
        "eps1_attribution_triple": eps1,
        "w2_ceiling_branches": ceilings,
        "hybrid_over_registered_exact": str(sp.nsimplify(ratio)),
        "claim_boundary": "provenance classification + exact rational "
                          "algebra on registered constants; diagnostic_only; "
                          "no branch enables any observational claim; the "
                          "frozen registry values are unchanged",
    }
