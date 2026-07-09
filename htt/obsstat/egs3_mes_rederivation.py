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

from htt.tsc.admissibility.three_bound_hierarchy import COEFFS

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


def mes_rederivation_seal() -> dict:
    """Aggregate M4-resolution seal (fail-closed on what it CAN certify)."""
    sigma = sigma_rederivation()
    omega_mesa = omega_mesa_rederivation()
    provenance = omega_accel_provenance()
    crosswalk = mes_coefficient_primary_crosswalk()

    ok = (sigma["rederived"]
          and sigma["matches_registry"]
          and sigma["symbolic_identity_holds"]
          and omega_mesa["matches_eq60"]
          and omega_mesa["mesa_omega_differs_from_registry"])
    return {
        "seal": "egs3.mes_rederivation",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "finding": "M4 (MES epsilon coefficients not rederived)",
        "sigma_rederivation": sigma,
        "omega_mesa_rederivation": omega_mesa,
        "omega_accel_provenance": provenance,
        "primary_crosswalk": crosswalk,
        "resolution": {
            "sigma": "rederived bit-exact from MESa eq (51) + C1 + C2 (SymPy + Fraction)",
            "omega_accel": "pinned to MESb Eqs (30)-(36) with documented Paper-I/II lineage; "
                           "print-only source -> primary_sourced_not_rederivable",
            "ticket": "docs/research_program/egs3/tickets/mes_full_rederivation.yaml "
                      "-> partially_resolved",
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
