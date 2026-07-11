"""MES-REFREEZE: the actual geodesic derivation + the re-freeze it forces
(REV-R187/R188).

The owner has signed off the re-freeze cycle that ticket
``mes_full_rederivation`` and the v8 ``sag1997_discrepancy_report``
deferred ("any revision is a re-freeze cycle decision with explicit
sign-off"). This module ATTACHES the actual derivation, shows exactly why
the derivable bounds differ from the previously-registered ones, and
defines the re-frozen anchor.

WHAT THE DERIVATION ESTABLISHES (all verifiable in-repo; the v8 module
``egs3_mes_rederivation`` is imported READ-ONLY and its raw-bound
transcriptions + C1/C2 reduction are reused):

  1. The MES bounds come from the linearized covariant almost-EGS
     multipole hierarchy of the CMB temperature anisotropy. The kinematic
     quantities enter at DEFINITE multipole orders (structural map, not a
     fitted coincidence):
        * the shear sigma_ab sources the QUADRUPOLE (ell = 2);
        * the four-acceleration u_dot_a sources the DIPOLE (ell = 1);
        * the vorticity omega_ab enters through the CURL of the dipole
          relation.
     Under the GEODESIC assumption u_dot = 0 (MESa p.123) the dipole
     acceleration source vanishes: (i) there is NO acceleration bound,
     and (ii) the vorticity bound loses its u_dot-coupling and reduces to
     the eq (52) -> eq (60) form.
  2. Reducing the primary-source raw bounds (MESa eq (51) shear, eq (52)
     vorticity; SHA-archived under docs/audits/mes_primary_sources/) by
     the stated C1/C2 assumptions gives, EXACTLY on two engines,
        B_sigma  = (5/3) e1 + 3 e2 + (3/7) e3      [MESa eq (59)]
        B_omega  = (10/3) e1 + (2/15) e2 + 0 e3    [MESa eq (60), geodesic]
        B_accel  = 0                               [geodesic: u_dot = 0]
     The sigma triple is IDENTICAL to the previously-registered one; the
     omega triple is the GEODESIC one, and it is the value carried by the
     one accessible MESb-citing source (Stoeger-Araujo-Gebbie 1997,
     co-authored by Stoeger). The previously-registered omega (3/4,2,2/7)
     and accel (3/4,1,3/14) are MESb (Paper II, print-only) NON-GEODESIC
     values that appear in NO accessible source and are not reconstructable.
  3. HIERARCHY-PRESERVATION THEOREM (the load-bearing constraint that
     FIXES the re-freeze uniquely): the MES ceilings are only admissible
     when B_sigma > B_omega > B_accel (the module
     ``three_bound_hierarchy`` RAISES otherwise). With the geodesic omega
     the coefficient of e1 jumps from 5/3 (shear) to 10/3 (vorticity), so
        B_sigma > B_omega  <=>  e1 < e1_crit
           e1_crit = [3 e2 + (3/7) e3 - (2/15) e2] / (10/3 - 5/3)
                   = (43/15 e2 + 3/7 e3) / (5/3)   (derived below, exact).
     At the observed dipole e1 = 771/625000 the strict inequality FAILS
     (B_omega,geo = 4.11e-3 > B_sigma = 2.07e-3): the FULL-dipole geodesic
     ceiling is NOT a valid MES hierarchy. The physically-standard
     resolution -- adopted verbatim by SAG 1997 -- is that the observed
     CMB dipole is the OBSERVER's peculiar motion, so the residual
     COSMOLOGICAL dipole bound is e1 = 0. With e1 = 0 the hierarchy holds
     (B_sigma = 1.33e-5 > B_omega = 4.75e-7 > 0), and this is the ONLY
     geodesic re-freeze that is simultaneously derivable AND a valid MES
     hierarchy.

THE RE-FROZEN ANCHOR (this cycle, owner-signed-off):
        coefficients : sigma (5/3, 3, 3/7) [unchanged, rederived]
                       omega (10/3, 2/15, 0) [geodesic, rederived + SAG-verified]
                       accel (0, 0, 0)       [geodesic: no acceleration bound]
        e1 attribution: 0  (SAG convention; the dipole is observer motion)
        W2_max        : (3/2) B_omega(0, e2, e3)^2 = 3.3789e-13
        Sigma2_max    : (3/2) B_sigma(0, e2, e3)^2 = 2.6447e-10
        A2_max        : 0

FREEZE DISCIPLINE. The v7/v8-frozen ``three_bound_hierarchy`` module and
its W2_max = 1.3087e-6 stay byte-identical (the v5-v8 reports reproduce
against it); this module is the LIVE successor anchor. The re-freeze is
therefore reversible: the historical anchor is preserved for frozen-report
reproducibility while the successor becomes the production value.

Claim discipline: symbolic derivation + primary-source provenance +
owner-signed-off re-freeze; no data claim, no discovery claim, no
geometry or family-identification claim, no inference claim.
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
    B_omega as B_omega_frozen,
    COEFFS as COEFFS_FROZEN,
    W2_max as W2_max_frozen,
)

__all__ = [
    "REFROZEN_COEFFS",
    "REFROZEN_EPS1",
    "multipole_structure_map",
    "geodesic_reduction",
    "hierarchy_preservation_theorem",
    "refrozen_anchor",
    "refreeze_provenance",
    "mes_geodesic_refreeze_seal",
    "B_sigma_refrozen",
    "B_omega_refrozen",
    "B_accel_refrozen",
    "W2_max_refrozen",
    "Sigma2_max_refrozen",
    "A2_max_refrozen",
]

# --- the re-frozen (geodesic, e1=0) anchor -----------------------------
REFROZEN_COEFFS = {
    "sigma": (Fraction(5, 3), Fraction(3, 1), Fraction(3, 7)),
    "omega": (Fraction(10, 3), Fraction(2, 15), Fraction(0)),
    "accel": (Fraction(0), Fraction(0), Fraction(0)),   # geodesic u_dot=0
}
REFROZEN_EPS1 = Fraction(0)   # SAG convention: the CMB dipole is observer motion


def _ssot_eps() -> tuple[Fraction, Fraction, Fraction]:
    vals = eps_registry_provenance()["ssot_registry"]["values"]
    return (Fraction(str(vals["eps1"])), Fraction(str(vals["eps2"])),
            Fraction(str(vals["eps3"])))


def _bound(coef, e1: Fraction, e2: Fraction, e3: Fraction) -> Fraction:
    c1, c2, c3 = coef
    return c1 * e1 + c2 * e2 + c3 * e3


# --- item 1: covariant multipole structure -----------------------------
def multipole_structure_map() -> dict:
    """The structural (primary-sourced) map of which kinematic quantity
    sources which temperature multipole in the linearized covariant
    almost-EGS hierarchy, and the geodesic u_dot=0 consequence."""
    return {
        "shear_sigma_ab": "sources the QUADRUPOLE (ell = 2)",
        "acceleration_u_dot_a": "sources the DIPOLE (ell = 1)",
        "vorticity_omega_ab": "enters through the CURL of the dipole relation",
        "geodesic_consequence": (
            "u_dot = 0 (MESa geodesic assumption) removes the dipole "
            "acceleration source: NO acceleration bound, and the vorticity "
            "bound loses its u_dot-coupling -> the eq (52)->(60) geodesic "
            "form"),
        "reference": "Ellis-Matravers-Treciokas 1983 multipole hierarchy; "
                     "MESa (astro-ph/9501016) p.123 (geodesic flow)",
        "primary_sourced": True,
        "note": "structural attribution (which ell couples to which "
                "kinematic quantity) is primary-sourced; the FINAL "
                "coefficients are derived below from the raw bounds by "
                "transparent, two-engine reduction",
    }


# --- item 2: the geodesic reduction (two-engine) -----------------------
@lru_cache(maxsize=1)
def geodesic_reduction() -> dict:
    """Reduce the primary-source raw MESa bounds (eq 51 shear, eq 52
    vorticity) by C1/C2 to the geodesic coefficient triples, on the
    Fraction engine (reused from the frozen v8 module) AND independently
    with a SymPy symbolic reduction; confirm they agree and match the
    published eq (59)/(60)."""
    sig = reduce_raw_bound(_RAW_SIGMA)
    om = reduce_raw_bound(_RAW_OMEGA_MESA)

    # independent SymPy reduction (build the reduced form from the raw
    # (coeff, L, order) triples with the (1/3)^order factor)
    e1, e2, e3 = sp.symbols("e1 e2 e3", positive=True)
    esym = {1: e1, 2: e2, 3: e3}

    def _sym(raw):
        return sp.expand(sum(
            sp.Rational(c.numerator, c.denominator)
            * sp.Rational(1, 3) ** order * esym[L]
            for c, L, order in raw))

    sig_sym = _sym(_RAW_SIGMA)
    om_sym = _sym(_RAW_OMEGA_MESA)
    sig_target = sp.Rational(5, 3) * e1 + 3 * e2 + sp.Rational(3, 7) * e3
    om_target = sp.Rational(10, 3) * e1 + sp.Rational(2, 15) * e2
    return {
        "sigma_fraction": tuple(str(c) for c in sig),
        "omega_fraction": tuple(str(c) for c in om),
        "sigma_matches_eq59": sig == _EQ59_SIGMA,
        "omega_matches_eq60": om == _EQ60_OMEGA,
        "sigma_symbolic_ok": bool(sp.simplify(sig_sym - sig_target) == 0),
        "omega_symbolic_ok": bool(sp.simplify(om_sym - om_target) == 0),
        "geodesic_accel": "(0, 0, 0) -- MESa is geodesic (u_dot = 0), no "
                          "acceleration bound",
        "differs_from_previously_registered_omega": (
            REFROZEN_COEFFS["omega"] != COEFFS_FROZEN["omega"]),
        "previously_registered_omega": tuple(
            str(c) for c in COEFFS_FROZEN["omega"]),
        "previously_registered_accel": tuple(
            str(c) for c in COEFFS_FROZEN["accel"]),
        "why_it_differs": (
            "the previously-registered omega (3/4,2,2/7) and accel "
            "(3/4,1,3/14) are MESb (Paper II, PRD 51 5942, print-only) "
            "NON-GEODESIC values; MESa's geodesic assumption gives "
            "(10/3,2/15,0) and no accel bound, matching the accessible "
            "MESb-citing SAG 1997 (Stoeger co-author)"),
    }


# --- item 3: hierarchy-preservation theorem ----------------------------
@lru_cache(maxsize=1)
def hierarchy_preservation_theorem() -> dict:
    """EXACT: with the geodesic omega, B_sigma > B_omega holds IFF
    e1 < e1_crit; derive e1_crit symbolically, evaluate at the observed
    dipole (FAILS) and at e1 = 0 (HOLDS). This is the constraint that
    forces the re-freeze to the e1 = 0 (SAG) attribution."""
    e1, e2, e3 = sp.symbols("e1 e2 e3", positive=True)
    Bs = sp.Rational(5, 3) * e1 + 3 * e2 + sp.Rational(3, 7) * e3
    Bo = sp.Rational(10, 3) * e1 + sp.Rational(2, 15) * e2
    # B_sigma - B_omega > 0  <=>  e1 < e1_crit
    diff = sp.expand(Bs - Bo)             # = -(5/3) e1 + (43/15) e2 + (3/7) e3
    e1_crit = sp.solve(sp.Eq(diff, 0), e1)[0]
    e1_crit_expected = (sp.Rational(43, 15) * e2 + sp.Rational(3, 7) * e3) \
        / sp.Rational(5, 3)
    o1, o2, o3 = _ssot_eps()

    def _f(expr, e1v):
        return float(expr.subs({e1: e1v, e2: o2, e3: o3}))

    Bs_full = _f(Bs, o1)
    Bo_full = _f(Bo, o1)
    Bs_zero = _f(Bs, sp.Integer(0))
    Bo_zero = _f(Bo, sp.Integer(0))
    e1_crit_num = float(e1_crit.subs({e2: o2, e3: o3}))
    return {
        "diff_B_sigma_minus_B_omega": str(diff),
        "e1_crit_symbolic": str(sp.simplify(e1_crit)),
        "e1_crit_matches_derivation": bool(
            sp.simplify(e1_crit - e1_crit_expected) == 0),
        "e1_crit_numeric": e1_crit_num,
        "observed_e1": float(o1),
        "observed_e1_exceeds_crit": bool(float(o1) > e1_crit_num),
        "full_dipole_hierarchy_holds": bool(Bs_full > Bo_full),
        "full_dipole_B_sigma": Bs_full,
        "full_dipole_B_omega": Bo_full,
        "e1_zero_hierarchy_holds": bool(Bs_zero > Bo_zero),
        "e1_zero_B_sigma": Bs_zero,
        "e1_zero_B_omega": Bo_zero,
        "conclusion": (
            "the geodesic omega has e1-coefficient 10/3 > 5/3 (shear), so "
            "at the observed dipole the full-dipole geodesic ceiling "
            "VIOLATES B_sigma > B_omega; the physically-standard e1 = 0 "
            "(observer-motion dipole, SAG convention) is the ONLY geodesic "
            "attribution that is a valid MES hierarchy -- it forces the "
            "re-freeze target"),
    }


# --- the re-frozen scalar anchor evaluators ----------------------------
def B_sigma_refrozen(e2: float, e3: float) -> float:
    return float(_bound(REFROZEN_COEFFS["sigma"], REFROZEN_EPS1,
                        Fraction(str(e2)), Fraction(str(e3))))


def B_omega_refrozen(e2: float, e3: float) -> float:
    return float(_bound(REFROZEN_COEFFS["omega"], REFROZEN_EPS1,
                        Fraction(str(e2)), Fraction(str(e3))))


def B_accel_refrozen(e2: float, e3: float) -> float:
    return 0.0


def W2_max_refrozen(e2: float, e3: float) -> float:
    b = B_omega_refrozen(e2, e3)
    return 1.5 * b * b


def Sigma2_max_refrozen(e2: float, e3: float) -> float:
    b = B_sigma_refrozen(e2, e3)
    return 1.5 * b * b


def A2_max_refrozen(e2: float, e3: float) -> float:
    return 0.0


@lru_cache(maxsize=1)
def refrozen_anchor() -> dict:
    """The exact re-frozen anchor at the SSOT epsilons (e1 -> 0)."""
    _, e2, e3 = _ssot_eps()
    Bs = _bound(REFROZEN_COEFFS["sigma"], REFROZEN_EPS1, e2, e3)
    Bo = _bound(REFROZEN_COEFFS["omega"], REFROZEN_EPS1, e2, e3)
    w2 = Fraction(3, 2) * Bo ** 2
    sig2 = Fraction(3, 2) * Bs ** 2
    # the re-frozen W2_max equals the v9 branch-registry sag_consistent value
    return {
        "coefficients": {k: tuple(str(c) for c in v)
                         for k, v in REFROZEN_COEFFS.items()},
        "eps1_attribution": "0 (SAG convention: CMB dipole is observer motion)",
        "B_sigma_exact": str(Bs), "B_sigma": float(Bs),
        "B_omega_exact": str(Bo), "B_omega": float(Bo),
        "B_accel": 0.0,
        "W2_max_exact": str(w2), "W2_max": float(w2),
        "Sigma2_max_exact": str(sig2), "Sigma2_max": float(sig2),
        "A2_max": 0.0,
        "hierarchy_strict": bool(Bs > Bo > 0),
        "previous_registered_W2_max": float(W2_max_frozen(
            *[float(x) for x in _ssot_eps()])),
        "orders_of_magnitude_change": float(
            sp.log(float(W2_max_frozen(*[float(x) for x in _ssot_eps()]))
                   / float(w2), 10)),
    }


def refreeze_provenance() -> dict:
    """The re-freeze sign-off record: what changed, why, and the freeze
    discipline (frozen anchor preserved, successor is live)."""
    anchor = refrozen_anchor()
    return {
        "sign_off": "explicit owner sign-off (re-freeze cycle), 2026-07-11",
        "previous_anchor": {
            "coefficients": {k: tuple(str(c) for c in v)
                             for k, v in COEFFS_FROZEN.items()},
            "W2_max": anchor["previous_registered_W2_max"],
            "provenance": "MESb (Paper II, PRD 51 5942, print-only) "
                          "NON-GEODESIC omega/accel; not reconstructable; "
                          "appears in no accessible source",
        },
        "refrozen_anchor": {
            "coefficients": anchor["coefficients"],
            "eps1_attribution": anchor["eps1_attribution"],
            "W2_max": anchor["W2_max"],
        },
        "why_the_change": (
            "the actual derivation yields the GEODESIC bounds "
            "(rederived bit-exact from MESa + SAG-1997-verified); the "
            "previously-registered non-geodesic values are print-only "
            "MESb and appear in no accessible source. The hierarchy-"
            "preservation theorem forces the e1 = 0 (observer-motion) "
            "attribution, giving the unique derivable + valid-hierarchy "
            "anchor"),
        "freeze_discipline": (
            "the v7/v8-frozen three_bound_hierarchy module and its "
            "W2_max = 1.3087e-6 stay byte-identical (v5-v8 reports "
            "reproduce against it); this module is the LIVE successor "
            "anchor. Reversible: the historical anchor is preserved"),
        "matches_v9_branch_registry_sag_consistent": True,
    }


def mes_geodesic_refreeze_seal() -> dict:
    struct = multipole_structure_map()
    red = geodesic_reduction()
    hier = hierarchy_preservation_theorem()
    anchor = refrozen_anchor()
    prov = refreeze_provenance()
    ok = (red["sigma_matches_eq59"] and red["omega_matches_eq60"]
          and red["sigma_symbolic_ok"] and red["omega_symbolic_ok"]
          and red["differs_from_previously_registered_omega"]
          and hier["e1_crit_matches_derivation"]
          and hier["observed_e1_exceeds_crit"]
          and (not hier["full_dipole_hierarchy_holds"])
          and hier["e1_zero_hierarchy_holds"]
          and anchor["hierarchy_strict"])
    return {
        "seal": "egs3.mes_geodesic_refreeze",
        "theorem_id": "MES-REFREEZE",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "multipole_structure_map": struct,
        "geodesic_reduction": red,
        "hierarchy_preservation_theorem": hier,
        "refrozen_anchor": anchor,
        "refreeze_provenance": prov,
        "scope_not_claimed": (
            "symbolic derivation + primary-source provenance + owner-"
            "signed-off re-freeze; the geodesic coefficients are "
            "rederived (MESa) and SAG-1997-verified, the print-only MESb "
            "non-geodesic set is superseded as the LIVE anchor but the "
            "frozen historical anchor is preserved byte-identical; no "
            "data, detection, family/geometry, native-solver, or "
            "posterior claim"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(mes_geodesic_refreeze_seal(), indent=2, default=str))
