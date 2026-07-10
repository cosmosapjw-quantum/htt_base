"""EGS3 v8-update: T3-int -- connected exact family realizing the identified-interval
INTERIOR, plus simultaneous four-sector attainability in exact tilted Bianchi V.

Discharges the residual King-Ellis initial-data item of ticket ``t3_king_ellis``
("realizing every INTERIOR point ... by a single connected exact family"). Two
results, both exact symbolic GR at the constraint level:

1. INTERVAL interior (proved here at the x_C-VALUE level, exact). A
   piecewise-connected two-segment family of homogeneous data 4-tuples whose
   x_C sweeps the ENTIRE registered interval [11/100, 17/100] continuously and
   strictly monotonically. SCOPE: this is an exact statement about the
   comparator VALUES (piecewise-linear inversion); the Gauss closure is a
   bookkeeping identity (Omega_Lambda defined to close it), segment II's
   momentum closure is genuinely computed (transverse shear + antipodal pair,
   a-independent), and segment I's momentum closure is INHERITED-ASSERTED from
   the frozen endpoint module (rotating-build caveat re-disclosed below):

     Segment I  (Bianchi I, t in [0,1]):  g(t) = (12, 4(1-t), 3, 0)/100,
        x_C = (11 + 4t)/100  -- the rigid-rotation amplitude is scaled down;
        the frozen v8 endpoint argument (trivial structure constants, curl-free
        rotation mode, antipodal zero-flux tilt pair) holds for EVERY t.
     Segment II (Bianchi V, u in [0,1]):  g(u) = (12, 0, 3, 2u)/100,
        x_C = (15 + 2u)/100  -- the curvature vector a(u) = H sqrt(2u)/10 is
        dialed up; the exact (0i) constraint 3 a_b sigma^{ab} + kappa q^a = 0
        holds for EVERY u (transverse shear s1 = 0, antipodal pair q = 0).

   The junction is EXACT: segment I at t=1 and segment II at u=0 are the SAME
   initial-data set, and Bianchi V with a = 0 degenerates exactly to Bianchi I
   at the level of structure constants ([e_1, e_i] = a e_i -> abelian). Every
   interior x_C value is therefore exactly realized by an explicit family
   member (`realize_interior_point`), in exact Fraction arithmetic.

2. SIMULTANEOUS four-sector attainability + the vorticity slaving relation
   (derived here, exact). For a group-invariant tilt velocity v on Bianchi V
   (structure constants [e_1, e_2] = a e_2, [e_1, e_3] = a e_3), the fluid
   vorticity is derived from the commutator algebra: curl(v)^1 = 0,
   curl(v)^(2,3) = +/- a v_(3,2)  --  i.e. |curl v| = a |v_perp| EXACTLY
   (in this frame convention; the overall factor is convention-anchored).
   Consequences:
     * a tilt ALIGNED with the a-vector is irrotational (curl v = 0);
     * a TRANSVERSE tilt carries vorticity omega ~ a v_perp: with an antipodal
       pair (+v, -v) the net flux q still cancels exactly and each component
       carries EQUAL vorticity magnitude, so a configuration with ALL FOUR
       sectors (Sigma^2, W^2, Omega_tilt, Omega_k) simultaneously nonzero
       exists with exactly-zero Gauss+momentum residuals;
     * the DERIVED OBSTRUCTION to free box-interior dial-in: in this class the
       vorticity is SLAVED, W^2 proportional to a^2 v_perp^2 (a curvature-tilt
       product) -- it is not a free dial. Realizing an ARBITRARY box-interior
       point (independent W^2 and Omega_k) within one exact connected family
       remains open; what is realized is the full x_C interval (result 1) plus
       the simultaneous-nonzero corner class (this result).

Scope kept honest: this is NOT a verified interior realization by fully
momentum-constraint-checked tilted GR initial data -- the proven parts are the
exact x_C-value interval sweep, the genuinely computed segment-II/witness
constraint closures, and the sign-blind curl magnitude/alignment facts; the
Gauss closure is bookkeeping; dynamics stay deferred (King-Ellis). The curl is
derived from the VERIFIED Levi-Civita connection (metric-compatible +
torsion-free in-seal); the spatial curl is a linear-order (gamma -> 1) proxy
for the covariant comparator vorticity.

Claim discipline: exact symbolic GR algebra; the Bianchi I/V labels are the
realizing construction, NOT a sky class statement; no data claim, no
signal-discovery claim, no Bianchi-class-identification-of-the-sky claim, no
native-solver-produced claim, no probabilistic-inference claim.
"""
from __future__ import annotations

from fractions import Fraction

import sympy as sp

from htt.obsstat.egs3_linearized_realization import REGISTERED_ENDPOINTS
from htt.obsstat.egs3_nonlinear_realization import (
    antipodal_flux_exact, bianchi_V_momentum_constraint,
)

__all__ = [
    "INTERVAL_LO",
    "INTERVAL_HI",
    "family_member",
    "realize_interior_point",
    "symbolic_family_residuals",
    "bianchi_v_group_invariant_curl",
    "simultaneous_four_sector_witness",
    "interior_family_seal",
]

INTERVAL_LO = Fraction(11, 100)
INTERVAL_HI = Fraction(17, 100)
_JUNCTION = Fraction(15, 100)
_OMEGA_M = Fraction(3, 10)


def family_member(segment: str, s: Fraction) -> dict:
    """One exact family member. segment 'I' (t in [0,1], Bianchi I, W^2 sweep)
    or 'II' (u in [0,1], Bianchi V, Omega_k sweep); s is the exact parameter."""
    s = Fraction(s)
    if not 0 <= s <= 1:
        raise ValueError("family parameter must lie in [0, 1]")
    if segment == "I":
        g = {"Sigma2": Fraction(12, 100), "W2": Fraction(4, 100) * (1 - s),
             "Omega_tilt": Fraction(3, 100), "Omega_k": Fraction(0)}
        bianchi_class = "I"
        momentum_terms = ("trivial structure constants; rigid-rotation amplitude "
                          "scaled by (1-t); antipodal pair q=0. INHERITED "
                          "CAVEAT (frozen endpoint module): the rotating "
                          "tilted Bianchi I build's momentum constraint is "
                          "ASSERTED, not explicitly verified -- and a "
                          "group-invariant tilt is irrotational in Bianchi I "
                          "(trivial structure constants), so the nonzero W^2 "
                          "rides on a separate rotational mode whose "
                          "constraint-level consistency is part of the "
                          "deferred King-Ellis item")
    elif segment == "II":
        g = {"Sigma2": Fraction(12, 100), "W2": Fraction(0),
             "Omega_tilt": Fraction(3, 100), "Omega_k": Fraction(2, 100) * s}
        bianchi_class = "V" if s > 0 else "I (exact a->0 boundary of V)"
        momentum_terms = ("3 a(u) sigma_1 + kappa q^1 with sigma_1=0 (transverse) "
                          "and q=0 (antipodal pair): zero for every u")
    else:
        raise ValueError("segment must be 'I' or 'II'")
    x_C = g["Sigma2"] - g["W2"] + g["Omega_tilt"] + g["Omega_k"]
    omega_lambda = 1 - _OMEGA_M - g["Omega_k"] - g["Omega_tilt"] - g["Sigma2"] + g["W2"]
    gauss_residual = (_OMEGA_M + omega_lambda + g["Omega_k"] + g["Omega_tilt"]
                      + g["Sigma2"] - g["W2"]) - 1
    return {
        "segment": segment,
        "parameter": str(s),
        "bianchi_class": bianchi_class,
        "exact_invariants": {k: str(v) for k, v in g.items()},
        "x_C": str(x_C),
        "omega_lambda_closure": str(omega_lambda),
        "gauss_residual_exact_zero": bool(gauss_residual == 0),
        "gauss_closure_note": "Gauss is closed by DEFINING Omega_Lambda (bookkeeping closure, not an independent constraint -- same disclosure as the frozen endpoint module)",
        "momentum_terms": momentum_terms,
    }


def realize_interior_point(x_target) -> dict:
    """Exact family member realizing ANY x_C in [11/100, 17/100] (Fraction).

    Piecewise-linear inversion: segment I for x <= 15/100 (t = (x-11/100)/(4/100)),
    segment II above (u = (x-15/100)/(2/100)). Exact rational arithmetic."""
    x = Fraction(x_target)
    if not INTERVAL_LO <= x <= INTERVAL_HI:
        raise ValueError("x_C target outside the registered interval")
    if x <= _JUNCTION:
        member = family_member("I", (x - INTERVAL_LO) / Fraction(4, 100))
    else:
        member = family_member("II", (x - _JUNCTION) / Fraction(2, 100))
    realized = Fraction(member["x_C"])
    member["target_x_C"] = str(x)
    member["exactly_realized"] = bool(realized == x)
    return member


def symbolic_family_residuals() -> dict:
    """SymPy: the Gauss residual is IDENTICALLY zero along both segments (as a
    symbolic function of the family parameter), the momentum data (s1=0, q=0)
    are parameter-independent, and x_C is continuous and strictly monotone
    across the junction."""
    t, u = sp.symbols("t u", real=True)
    om = sp.Rational(3, 10)
    # segment I
    S1 = {"Sigma2": sp.Rational(12, 100), "W2": sp.Rational(4, 100) * (1 - t),
          "Omega_tilt": sp.Rational(3, 100), "Omega_k": sp.Integer(0)}
    # segment II
    S2 = {"Sigma2": sp.Rational(12, 100), "W2": sp.Integer(0),
          "Omega_tilt": sp.Rational(3, 100), "Omega_k": sp.Rational(2, 100) * u}

    def gauss(S):
        ol = 1 - om - S["Omega_k"] - S["Omega_tilt"] - S["Sigma2"] + S["W2"]
        return sp.simplify((om + ol + S["Omega_k"] + S["Omega_tilt"]
                            + S["Sigma2"] - S["W2"]) - 1)

    def xc(S):
        return sp.simplify(S["Sigma2"] - S["W2"] + S["Omega_tilt"] + S["Omega_k"])

    x1, x2 = xc(S1), xc(S2)
    junction_match = sp.simplify(x1.subs(t, 1) - x2.subs(u, 0)) == 0
    return {
        "gauss_residual_segment_I": str(gauss(S1)),
        "gauss_residual_segment_II": str(gauss(S2)),
        "gauss_identically_zero": bool(gauss(S1) == 0 and gauss(S2) == 0),
        "gauss_closure_note": "identically zero BECAUSE Omega_Lambda is DEFINED to close it (bookkeeping identity, no constraint content)",
        "x_C_segment_I": str(x1),
        "x_C_segment_II": str(x2),
        "dxC_dt": str(sp.diff(x1, t)),        # +1/25 > 0
        "dxC_du": str(sp.diff(x2, u)),        # +1/50 > 0
        "strictly_monotone": bool(sp.diff(x1, t) > 0 and sp.diff(x2, u) > 0),
        "junction_exact_match": bool(junction_match),
        "endpoints": {"t=0": str(x1.subs(t, 0)), "t=1": str(x1.subs(t, 1)),
                      "u=0": str(x2.subs(u, 0)), "u=1": str(x2.subs(u, 1))},
    }


def bianchi_v_group_invariant_curl() -> dict:
    """SymPy derivation of the curl of a group-invariant vector field on
    Bianchi V from the LEVI-CIVITA connection of the invariant orthonormal
    frame, with the connection VERIFIED metric-compatible and torsion-free
    in-seal (2026-07 adversarial repair: an earlier index convention produced
    the opposite overall sign; the magnitude and alignment facts are
    sign-blind and unchanged).

    Frame: [e_1, e_2] = a e_2, [e_1, e_3] = a e_3, [e_2, e_3] = 0. With
    C_{jmk} = <[e_j, e_m], e_k>, the Koszul connection components are
    Gamma_{jmk} = <nabla_{e_j} e_m, e_k> = (C_{jmk} - C_{mkj} + C_{kjm})/2,
    and for an invariant field (constant frame components)
    (curl v)^i = eps^{ibc} v_m Gamma_{bmc}. Result: curl v = (0, a v3, -a v2).
    """
    a = sp.Symbol("a", real=True)
    v1, v2, v3 = sp.symbols("v1 v2 v3", real=True)
    v = [v1, v2, v3]
    # C[j][m][k] = C_{jmk} = <[e_j, e_m], e_k>
    C = [[[sp.Integer(0)] * 3 for _ in range(3)] for _ in range(3)]
    C[0][1][1], C[1][0][1] = a, -a       # [e1,e2] = a e2
    C[0][2][2], C[2][0][2] = a, -a       # [e1,e3] = a e3

    def Gamma(j, m, k):   # Koszul: <nabla_{e_j} e_m, e_k>
        return sp.Rational(1, 2) * (C[j][m][k] - C[m][k][j] + C[k][j][m])

    rng = range(3)
    metric_compatible = all(
        sp.simplify(Gamma(j, m, k) + Gamma(j, k, m)) == 0
        for j in rng for m in rng for k in rng)
    torsion_free = all(
        sp.simplify(Gamma(j, m, k) - Gamma(m, j, k) - C[j][m][k]) == 0
        for j in rng for m in rng for k in rng)
    curl = [sp.simplify(sum(sp.LeviCivita(i, b, c)
                            * sum(v[m] * Gamma(b, m, c) for m in rng)
                            for b in rng for c in rng)) for i in rng]
    aligned = [sp.simplify(c_.subs({v2: 0, v3: 0})) for c_ in curl]
    curl_sq = sp.simplify(sum(c_ ** 2 for c_ in curl))
    # exact DERIVED slaving relation: |curl v|^2 = a^2 (v2^2 + v3^2) = a^2 v_perp^2
    slaving = sp.simplify(curl_sq - a ** 2 * (v2 ** 2 + v3 ** 2)) == 0
    return {
        "structure_constants": "[e1,e2]=a e2, [e1,e3]=a e3, [e2,e3]=0 (Bianchi V)",
        "connection_metric_compatible": bool(metric_compatible),
        "connection_torsion_free": bool(torsion_free),
        "curl_components": [str(c_) for c_ in curl],
        "aligned_tilt_is_irrotational": bool(all(c_ == 0 for c_ in aligned)),
        "curl_squared": str(curl_sq),
        "slaving_identity_a2_vperp2": bool(slaving),
        "note": "Levi-Civita connection verified metric-compatible + "
                "torsion-free in-seal; curl=0 iff v || a and |curl v| = "
                "a|v_perp| are sign-blind; the SPATIAL curl of v is a "
                "LINEAR-ORDER (gamma->1) proxy for the covariant fluid "
                "vorticity of the tilted congruence -- gamma/projection "
                "factors and the /(6H^2) comparator normalization are NOT "
                "applied here",
    }


def simultaneous_four_sector_witness() -> dict:
    """Exact witness: a Bianchi V configuration with ALL FOUR sectors nonzero
    and exactly-zero Gauss + momentum residuals.

    Data: a > 0 (Omega_k = a^2/H^2 > 0), transverse diagonal shear
    sigma = diag(0, s+, -s+) (Sigma^2 > 0), antipodal TRANSVERSE tilt pair
    (+v, -v) with v perpendicular to the a-vector (Omega_tilt > 0, q_net = 0
    exactly), and the DERIVED spatial curl of each pair member
    |curl v| = a |v_perp| > 0 -- a LINEAR-ORDER (gamma -> 1) proxy for a
    nonzero comparator W^2 (the covariant vorticity invariant carries
    gamma/projection factors and the /(6H^2) normalization not applied here). The momentum constraint keeps only
    3 a_b sigma^{ab} + kappa q^a; both terms vanish exactly (transverse shear;
    antipodal pair)."""
    flux = antipodal_flux_exact()
    momV = bianchi_V_momentum_constraint()
    curl = bianchi_v_group_invariant_curl()
    a, v, H = sp.symbols("a v H", positive=True)
    w2_each = sp.simplify((a * v) ** 2)       # |curl v|^2 for v perp a
    all_nonzero = bool(w2_each != 0)
    return {
        "construction": "Bianchi V; a>0; transverse shear diag(0,s+,-s+); "
                        "antipodal transverse tilt pair (+v,-v), v perp a",
        "momentum_exact_zero": bool(momV["momentum_exact_zero"]
                                    and flux["q_net_is_exact_zero"]),
        "spatial_curl_squared_each_component_linear_order_proxy": str(w2_each),
        "vorticity_nonzero_for_a_v_positive": all_nonzero,
        "four_sectors_simultaneously_nonzero": bool(
            all_nonzero and momV["momentum_exact_zero"]
            and flux["q_net_is_exact_zero"]),
        "slaving_obstruction": "the rotational mode is SLAVED: |curl v|^2 = a^2 v_perp^2 "
                               "(a curvature-tilt product; linear-order proxy for "
                               "W^2) -- the rotational mode is NOT a free dial in "
                               "this class; arbitrary independent "
                               "(W^2, Omega_k) box-interior dial-in by one exact "
                               "connected family remains open (derived "
                               "obstruction, recorded in t3_king_ellis)",
    }


def interior_family_seal() -> dict:
    """Fail-closed T3-int seal: exact interval-interior realization by a
    connected two-segment family + simultaneous four-sector witness + the
    derived vorticity slaving relation."""
    import numpy as np

    sym = symbolic_family_residuals()
    curl = bianchi_v_group_invariant_curl()
    simul = simultaneous_four_sector_witness()
    # exact interior spot realizations across the interval (Fractions)
    targets = [Fraction(11, 100), Fraction(23, 200), Fraction(13, 100),
               Fraction(29, 200), Fraction(15, 100), Fraction(31, 200),
               Fraction(16, 100), Fraction(33, 200), Fraction(17, 100)]
    spots = [realize_interior_point(x) for x in targets]
    spots_ok = all(s["exactly_realized"] and s["gauss_residual_exact_zero"]
                   for s in spots)
    endpoints_consistent = (
        Fraction(realize_interior_point(INTERVAL_LO)["x_C"]) == INTERVAL_LO
        and Fraction(realize_interior_point(INTERVAL_HI)["x_C"]) == INTERVAL_HI)
    ok = (sym["gauss_identically_zero"] and sym["strictly_monotone"]
          and sym["junction_exact_match"] and spots_ok and endpoints_consistent
          and curl["aligned_tilt_is_irrotational"]
          and curl["slaving_identity_a2_vperp2"]
          and simul["four_sectors_simultaneously_nonzero"])
    return {
        "seal": "egs3.interior_family",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "numpy_version": np.__version__,
        "theorem": "T3-int: every x_C in [11/100, 17/100] is exactly realized by "
                   "an explicit member of one connected two-segment exact family "
                   "(Bianchi I W^2-sweep glued at 15/100 to the exact a->0 "
                   "boundary of a Bianchi V Omega_k-sweep); plus an exact Bianchi "
                   "V witness with ALL FOUR sectors simultaneously nonzero, whose "
                   "vorticity obeys the derived slaving |curl v|^2 = a^2 "
                   "v_perp^2",
        "symbolic_family": sym,
        "interior_spot_realizations": spots,
        "group_invariant_curl": curl,
        "simultaneous_four_sector_witness": simul,
        "scope_not_claimed": "constraint-level initial data only (Gauss+momentum); "
                             "NOT dynamical King-Ellis evolution (deferred); NOT "
                             "free box-interior dial-in of independent (W^2, "
                             "Omega_k) -- the derived slaving relation is the "
                             "recorded obstruction; the x_C-interval statement is "
                             "the proven part",
        "claim_boundary": "exact symbolic GR initial-data realization; Bianchi "
                          "I/V labels are the realizing construction, NOT a sky "
                          "class statement; no data, signal-discovery, "
                          "Bianchi-class-identification-of-the-sky, "
                          "native-solver-produced, or probabilistic-inference "
                          "claim",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(interior_family_seal(), indent=2))
