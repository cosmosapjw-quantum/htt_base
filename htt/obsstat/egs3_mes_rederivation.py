"""EGS3 v8 (M4 resolution): rederivation of the MES bound coefficients from the
Maartens-Ellis-Stoeger (1995) primary sources.

This module answers external-review finding M4 -- "the MES epsilon coefficients are
registered external, never rederived" -- for the coefficient set that CAN be rederived
from a web-retrievable primary source, and pins the remainder to its exact primary-source
citation with a documented Paper-I/Paper-II lineage.

Primary sources (archived under docs/audits/mes_primary_sources/):

* MESa (Paper I): Maartens, Ellis, Stoeger, Phys. Rev. D 51, 1525 (1995),
  arXiv astro-ph/9501016. Assumes GEODESIC flow (u_dot=0): no acceleration bound,
  and its vorticity bound (eq 60) differs from the registry.
* companion: arXiv astro-ph/9510126 (Delta T / T summary), which states the shear bound
  is "MESb Eq (24)" and the remaining bounds are "MESb (Eq. (30)-(36))".
* MESb (Paper II): Maartens, Ellis, Stoeger, Phys. Rev. D 51, 5942 (1995). PRINT ONLY
  (not on arXiv); relaxes MESa's geodesic assumption -> source of the registered
  omega/accel coefficients and of the acceleration bound.

Result:

1. ``sigma_rederivation`` -- GENUINE bit-exact rederivation of B_sigma=(5/3,3,3/7) from
   MESa raw eq (51) + the stated reduction assumptions C1 (spatial <= time-derivative) and
   C2 (time-derivative ~ multipole/characteristic-time, Theta*t_R ~ 3 => e*_L~e_L/3). Both
   a SymPy symbolic proof and exact Fraction arithmetic. Matches registry exactly.
2. ``omega_mesa_rederivation`` -- the SAME machinery applied to MESa eq (52) reproduces
   MESa eq (60) omega=(10/3,2/15,0) exactly -> validates the reduction, and shows that
   MESa's omega does NOT equal the registered (3/4,2,2/7).
3. ``omega_accel_provenance`` -- documents that the registered omega/accel are MESb Eqs
   (30)-(36) values under the relaxed (non-geodesic) assumption set (print-only source),
   with the exact Paper-I->Paper-II lineage. Honest status ``primary_sourced_not_rederivable``.

Invariance: no coefficient value changes; this is a provenance upgrade. B_sigma/B_omega/
B_accel, the (3/2) ceilings, W2_max=1.309e-6, and every x_C anchor stay bit-identical.

Claim discipline: symbolic rederivation + primary-source provenance seal; no data,
detection, family/geometry, native-solver, or posterior claim.
"""
from __future__ import annotations

from fractions import Fraction

import sympy as sp

from htt.tsc.admissibility.three_bound_hierarchy import COEFFS, W2_max

__all__ = [
    "reduce_raw_bound",
    "sigma_rederivation",
    "omega_mesa_rederivation",
    "omega_accel_provenance",
    "mes_coefficient_primary_crosswalk",
    "mes_rederivation_seal",
]

# --- MES reduction assumptions (stated in MESa, eq (57)-context, C1 and C2) -----------
# C1: a spatial-gradient bound is <= the same-order time-derivative bound
#     (e_L' <= e_L*, e_L'' <= e_L**, ...). => a mark of any kind counts once toward order.
# C2: a k-th time derivative is estimated as e_L / (Theta t_R)^k with Theta t_R ~ 3,
#     so e_L^(k-mark) ~ (1/3)^k e_L.
# Net: a raw term with total derivative order d reduces by the factor (1/3)^d.
_THETA_TR = Fraction(3, 1)  # Theta * t_R ~ 3 (MESa eq (36)/(57) context)


def _reduction_factor(order: int) -> Fraction:
    """C1+C2 net reduction for a raw term of total derivative order ``order``."""
    return Fraction(1, 1) / (_THETA_TR ** order)


# --- Raw (pre-reduction) bounds, transcribed from MESa (multipole L, derivative order) --
# Each term is (coefficient, multipole L in {1,2,3}, total derivative order d).
# MESa eq (51) raw shear bound  |sigma|/Theta < (8/3) e2 + e2* + 5 e1' + (9/7) e3'
#   (the leading rational is 8/3, not 3/8: only 8/3 closes to eq (59)'s "3 e2"; the
#    companion eq (6) is the identical bound.)
_RAW_SIGMA = [
    (Fraction(8, 3), 2, 0),   # (8/3) e2
    (Fraction(1, 1), 2, 1),   # e2*      (one time derivative)
    (Fraction(5, 1), 1, 1),   # 5 e1'    (one spatial derivative -> C1 -> e1*)
    (Fraction(9, 7), 3, 1),   # (9/7) e3'
]
# MESa eq (52) raw vorticity bound |omega|/Theta < 9 e1' + 3 e1'* + (6/5) e2''
_RAW_OMEGA_MESA = [
    (Fraction(9, 1), 1, 1),   # 9 e1'
    (Fraction(3, 1), 1, 2),   # 3 e1'*   (mixed second order)
    (Fraction(6, 5), 2, 2),   # (6/5) e2''
]

# Reduced targets published by MESa.
_EQ59_SIGMA = (Fraction(5, 3), Fraction(3, 1), Fraction(3, 7))   # eq (59)
_EQ60_OMEGA = (Fraction(10, 3), Fraction(2, 15), Fraction(0, 1))  # eq (60)


def reduce_raw_bound(raw_terms) -> tuple[Fraction, Fraction, Fraction]:
    """Apply C1+C2 to a raw bound and return exact (c1, c2, c3) for (e1, e2, e3)."""
    acc = {1: Fraction(0), 2: Fraction(0), 3: Fraction(0)}
    for coeff, L, order in raw_terms:
        acc[L] += coeff * _reduction_factor(order)
    return acc[1], acc[2], acc[3]


def _symbolic_reduce(raw_terms):
    """SymPy mirror: build the reduced linear form as a symbolic expression."""
    e1, e2, e3 = sp.symbols("e1 e2 e3", positive=True)
    esym = {1: e1, 2: e2, 3: e3}
    expr = sum(
        sp.Rational(coeff.numerator, coeff.denominator)
        * sp.Rational(1, int(_THETA_TR) ** order)
        * esym[L]
        for coeff, L, order in raw_terms
    )
    return sp.expand(expr), (e1, e2, e3)


def sigma_rederivation() -> dict:
    """GENUINE bit-exact rederivation of B_sigma=(5/3,3,3/7) from MESa eq (51)+C1+C2."""
    reduced = reduce_raw_bound(_RAW_SIGMA)
    expr, (e1, e2, e3) = _symbolic_reduce(_RAW_SIGMA)
    target = (sp.Rational(5, 3) * e1 + sp.Rational(3, 1) * e2 + sp.Rational(3, 7) * e3)
    symbolic_ok = sp.simplify(expr - sp.expand(target)) == 0
    registry = COEFFS["sigma"]
    return {
        "raw_bound": "MESa eq (51): |sigma|/Theta < (8/3)e2 + e2* + 5 e1' + (9/7)e3'",
        "reduction": "C1 (spatial<=time-deriv) + C2 (e*_L ~ e_L/3, e**_L ~ e_L/9)",
        "reduced_coeffs": [str(c) for c in reduced],
        "reduced_symbolic": str(expr),
        "matches_eq59": reduced == _EQ59_SIGMA,
        "matches_registry": reduced == registry,
        "symbolic_identity_holds": bool(symbolic_ok),
        "target_eq59": "MESa eq (59) = companion eq (7) = (5/3)e1 + 3 e2 + (3/7)e3",
        "rederived": bool(reduced == _EQ59_SIGMA == registry and symbolic_ok),
    }


def omega_mesa_rederivation() -> dict:
    """Same machinery on MESa eq (52) -> eq (60) omega=(10/3,2/15,0); validates the
    reduction AND shows MESa's omega != the registered (3/4,2,2/7)."""
    reduced = reduce_raw_bound(_RAW_OMEGA_MESA)
    registry = COEFFS["omega"]
    return {
        "raw_bound": "MESa eq (52): |omega|/Theta < 9 e1' + 3 e1'* + (6/5)e2''",
        "reduced_coeffs": [str(c) for c in reduced],
        "matches_eq60": reduced == _EQ60_OMEGA,
        "target_eq60": "MESa eq (60) = (10/3)e1 + (2/15)e2 (no octopole; geodesic flow)",
        "mesa_omega_differs_from_registry": reduced != registry,
        "registry_omega": [str(c) for c in registry],
        "note": "MESa (geodesic, u_dot=0) omega != registry -> registry is MESb (Paper II)",
    }


def omega_accel_provenance() -> dict:
    """Document the registered omega/accel as MESb Eqs (30)-(36) values under the
    relaxed (non-geodesic) assumption set. MESb is print-only (not on arXiv)."""
    return {
        "registered_omega": [str(c) for c in COEFFS["omega"]],   # (3/4, 2, 2/7)
        "registered_accel": [str(c) for c in COEFFS["accel"]],   # (3/4, 1, 3/14)
        "primary_source": "MESb = Maartens, Ellis, Stoeger, Phys. Rev. D 51, 5942 (1995)",
        "primary_equations": "MESb Eqs (30)-(36) (companion astro-ph/9510126 line 248)",
        "assumption_lineage": (
            "MESa (Paper I, PRD 51 1525) assumes geodesic flow u_dot=0 -> no acceleration "
            "bound and omega=(10/3,2/15,0) [eq 60]. MESb (Paper II, PRD 51 5942) relaxes to "
            "fully-observational assumptions -> introduces the acceleration bound and revises "
            "omega to (3/4,2,2/7); accel=(3/4,1,3/14)."
        ),
        "status": "primary_sourced_not_rederivable",
        "obstruction": "MESb is print-only (not on arXiv); its internal derivation of the "
                       "relaxed-assumption coefficients is not reconstructable in-repo",
        "secondary_numbering_note": (
            "the 'Thm 3.1/3.2/3.3, Eq. 3.7/3.12/3.15' labels in the registry are a "
            "secondary-source reorganization, not MESa/MESb primary equation numbers"
        ),
        "v8_update_evidence_note": (
            "the v8-update literature sweep (see sag1997_discrepancy_report) found the "
            "MESb-citing SAG 1997 limit set (co-authored by Stoeger) carries the GEODESIC "
            "omega (10/3, 2/15, 0) and NO acceleration bound, contradicting this lineage "
            "narrative's premise; the registered values remain frozen pending a re-freeze "
            "cycle audit"
        ),
    }


def mes_coefficient_primary_crosswalk() -> dict:
    """Exact {paper, equation, assumption-set} per registered coefficient set."""
    return {
        "sigma": {
            "coefficients": "(5/3, 3, 3/7)",
            "primary": "MESa eq (59) [rederived from raw eq (51)]; companion eq (7)",
            "assumptions": "C1 + C2 reduction of the general bound eq (51)/eq (6)",
            "status": "rederived",
        },
        "omega": {
            "coefficients": "(3/4, 2, 2/7)",
            "primary": "MESb Eq (30)-(36) [Paper II, PRD 51 5942, print-only]",
            "assumptions": "MESb relaxed (non-geodesic) assumption set",
            "status": "primary_sourced_not_rederivable",
            "mesa_paper_I_value": "(10/3, 2/15, 0) [eq 60, geodesic] -- differs",
        },
        "accel": {
            "coefficients": "(3/4, 1, 3/14)",
            "primary": "MESb Eq (30)-(36) [Paper II, PRD 51 5942, print-only]",
            "assumptions": "MESb relaxed set; MESa has NO accel bound (geodesic u_dot=0)",
            "status": "primary_sourced_not_rederivable",
        },
        "reference_a": "Maartens, Ellis, Stoeger, Phys. Rev. D 51, 1525 (1995) [astro-ph/9501016]",
        "reference_b": "Maartens, Ellis, Stoeger, Phys. Rev. D 51, 5942 (1995) [print-only]",
    }


def sag1997_discrepancy_report() -> dict:
    """v8-update DOCUMENTED DISCREPANCY REPORT (the exit-gate-accepted branch
    of ticket mes_full_rederivation): the registered omega/accel coefficient
    triples are contradicted by, respectively absent from, every accessible
    primary/citing source.

    Evidence (archived: docs/audits/mes_primary_sources/
    sag1997_astro-ph_9904346_ApJ476_435.tex):
    * Stoeger, Araujo & Gebbie, ApJ 476, 435 (1997) [astro-ph/9904346] -- the
      MESb-citing COBE-limits paper co-authored by Stoeger, explicitly using
      the Maartens et al. 1995a,b assumption set -- transcribes (its eqs 3-4,
      source lines 153-157):
          |sigma|/Theta < (5/3) e1 + 3 e2 + (3/7) e3     [matches registry]
          |omega|/Theta < (10/3) e1 + (2/15) e2          [NOT the registry]
      for the congruence of timelike GEODESICS (line 180), with NO
      acceleration bound anywhere.
    * SAG's own printed numerics (eqs 23-24; e1=0, <e2>=1.1e-5, <e3>=2.5e-5)
      close ONLY on those triples -- checked exactly below.
    * MESb itself (PRD 51, 5942) is confirmed print-only: APS paywalled, no
      arXiv version, no ADS scan (retrieval log in the ticket).

    Consequence: (3/4, 2, 2/7) and (3/4, 1, 3/14) appear in NO accessible
    source; the registered W2_max = (3/2) B_omega(eps)^2 = 1.309e-6 rests on
    the unconfirmed triple. THE REGISTERED VALUES ARE NOT CHANGED HERE: the
    coefficient registry (three_bound_hierarchy.py) is a v7-frozen source and
    W2_max is a bit-identity production anchor -- any revision is a re-freeze
    cycle decision with explicit sign-off. The literature-supported
    alternative ceiling is computed for comparison only.

    Residual uncertainty (stated): MESb's inaccessibility means a distinct
    non-geodesic bound set inside it cannot be excluded; what is established
    is that every ACCESSIBLE source, including the same-group MESb-citing
    paper, carries the geodesic triple and no acceleration bound."""
    e1, e2, e3 = sp.symbols("e1 e2 e3", positive=True)
    sag_sigma = sp.Rational(5, 3) * e1 + 3 * e2 + sp.Rational(3, 7) * e3
    sag_omega = sp.Rational(10, 3) * e1 + sp.Rational(2, 15) * e2
    # SAG's own numeric closure (their eqs 12, 23, 24): e1=0, e2=1.1e-5, e3=2.5e-5
    subs = {e1: 0, e2: sp.Rational(11, 10) * 10 ** -5,
            e3: sp.Rational(25, 10) * 10 ** -5}
    sigma_num = float(sag_sigma.subs(subs))          # 4.37e-5 vs printed 4.4e-5
    omega_num = float(sag_omega.subs(subs))          # 1.4667e-6 vs printed 1.5e-6
    # the registered triple would give ~2.9e-5 against the printed 1.5e-6:
    reg_omega_expr = (sp.Rational(3, 4) * e1 + 2 * e2 + sp.Rational(2, 7) * e3)
    reg_omega_num = float(reg_omega_expr.subs(subs))
    exclusion_factor = reg_omega_num / omega_num
    # literature-supported alternative ceiling (COMPARISON ONLY, not registered)
    ssot = {e1: sp.Rational(12336, 10 ** 7),
            e2: sp.Rational(3559629, 10 ** 12),
            e3: sp.Rational(6065291, 10 ** 12)}
    w2_alt = float(sp.Rational(3, 2) * sag_omega.subs(ssot) ** 2)
    w2_registered = float(W2_max(1.2336e-3, 3.559629e-6, 6.065291e-6))
    return {
        "source": "Stoeger, Araujo & Gebbie, ApJ 476, 435 (1997) "
                  "[astro-ph/9904346]; archived docs/audits/mes_primary_sources/"
                  "sag1997_astro-ph_9904346_ApJ476_435.tex",
        "sag_sigma_triple": "(5/3, 3, 3/7) -- matches the registry",
        "sag_omega_triple": "(10/3, 2/15, 0) -- geodesic; equals MESa eq (60); "
                            "NOT the registered (3/4, 2, 2/7)",
        "sag_accel_bound": "ABSENT (geodesic congruence); the registered "
                           "(3/4, 1, 3/14) appears in no accessible source",
        "sag_numeric_closure_sigma": sigma_num,
        "sag_printed_sigma": 4.4e-5,
        "sag_numeric_closure_omega": omega_num,
        "sag_printed_omega": 1.5e-6,
        "numerics_close_on_sag_triples": bool(
            abs(sigma_num - 4.4e-5) < 5e-7 and abs(omega_num - 1.5e-6) < 5e-8),
        "registered_omega_under_sag_inputs": reg_omega_num,
        "registered_triple_excluded_by_factor": round(exclusion_factor, 2),
        "w2_ceiling_registered_unchanged": w2_registered,
        "w2_ceiling_literature_supported_comparison_only": w2_alt,
        "registry_action": "NONE this cycle (v7-frozen registry + bit-identity "
                           "anchor); revision deferred to a re-freeze cycle "
                           "with explicit sign-off (ticket "
                           "mes_full_rederivation -> discrepancy_documented)",
        "residual_uncertainty": "MESb print-only: a distinct non-geodesic "
                                "bound set inside it cannot be excluded; all "
                                "ACCESSIBLE sources carry the geodesic triple",
    }


def mes_rederivation_seal() -> dict:
    """Aggregate M4-resolution seal (fail-closed on what it CAN certify)."""
    sigma = sigma_rederivation()
    omega_mesa = omega_mesa_rederivation()
    provenance = omega_accel_provenance()
    crosswalk = mes_coefficient_primary_crosswalk()
    discrepancy = sag1997_discrepancy_report()

    ok = (sigma["rederived"]
          and sigma["matches_registry"]
          and sigma["symbolic_identity_holds"]
          and omega_mesa["matches_eq60"]
          and omega_mesa["mesa_omega_differs_from_registry"]
          and discrepancy["numerics_close_on_sag_triples"])
    return {
        "seal": "egs3.mes_rederivation",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "finding": "M4 (MES epsilon coefficients not rederived)",
        "sigma_rederivation": sigma,
        "omega_mesa_rederivation": omega_mesa,
        "omega_accel_provenance": provenance,
        "primary_crosswalk": crosswalk,
        "sag1997_discrepancy_report": discrepancy,
        "resolution": {
            "sigma": "rederived bit-exact from MESa eq (51) + C1 + C2 (SymPy + Fraction)",
            "omega_accel": "DOCUMENTED DISCREPANCY (v8-update): the accessible "
                           "MESb-citing literature (SAG 1997, same group) carries the "
                           "geodesic omega (10/3, 2/15, 0) and NO acceleration bound; "
                           "the registered triples appear in no accessible source; "
                           "registered values UNCHANGED (frozen registry + bit-identity "
                           "anchor), revision deferred to a re-freeze cycle",
            "ticket": "docs/research_program/egs3/tickets/mes_full_rederivation.yaml "
                      "-> discrepancy_documented",
        },
        "invariance": "no coefficient value changes; ceilings + W2_max=1.309e-6 + x_C "
                      "anchors bit-identical",
        "claim_boundary": "symbolic rederivation + primary-source provenance seal; the "
                          "print-only MESb omega/accel stay primary-sourced (exact citation, "
                          "not in-repo-rederivable); no data, detection, family/geometry, "
                          "native-solver, or posterior claim",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(mes_rederivation_seal(), indent=2))
