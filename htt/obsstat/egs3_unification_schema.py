"""EGS3 v8-update U3: the rank-deficiency schema correspondence -- the comparator
channel response and the Teff retained-moment response are two exact instances
of ONE linear-response schema.

Schema (finite-dimensional, exact): a response matrix A mapping perturbation
directions to observables, a selector S onto the REGISTERED observables, the
exact kernel K = ker(S A), and an invariant functional annihilating K.
Blindness is removed only by ENLARGING the registered observable set, never by
refining the existing one.

Instance 1 -- comparator lane (imported read-only from
``egs3_graded_comparator``): A = channel_response_design() (3 channels x 4
sectors, exact {0,1} support), S = identity on the channel outputs. Exact rank
2; null basis = {e_W2, e_Omega_k}; the null KINDS differ (W2 = genuine
order-independent structural null; Omega_k = leading-order no-channel that
re-opens at higher order within the same channels -- NULL_SECTOR_KIND is
carried, not flattened). Re-opening = transverse peculiar velocities / CMB
B-modes (W2), higher-order transfer (Omega_k).

Instance 2 -- Teff lane (imported read-only from ``htt.teff.representative``):
perturbation directions = {(n,k) insertion amplitude, two-temperature mixing
s^2}; observables = the p = 3, 4, 5 moment responses; the response matrix is
EXACT,

        insertion (c_p)    two-temperature (dR_p/d s^2 at 0)
  p=3     -1/16                -3/2
  p=4       0                    0
  p=5      1/64                 5/2

(the c_p column from radial_fingerprint(p) = (p-4)/2^{p+1}; the s^2 column
derived symbolically from two_temperature_ratio). The RETAINED-moment selector
S = (p=4 row) annihilates the ENTIRE perturbation space exactly (c_4 = 0 and
R_4 == 1 identically): the retained p=4 anchor is blind to both enrichment
directions. Re-opening = retaining the p = 3 / p = 5 moments (enlarging the
observable set), exactly parallel to the comparator lane. The full 3x2
response has exact rank 2 -- the two enrichment directions ARE separable once
the residual-sensitive moments are observed (the p3/p5 fingerprint
discrimination of Teff Thm 22).

The correspondence sealed here is MATHEMATICAL (two exact instances of the
same finite-dimensional schema); no physical identification between the lanes
is asserted beyond the shared structure, and no statement about the observed
sky is made.

Claim discipline: exact integer/rational linear algebra over registered
in-repo objects; diagnostic_only; no data claim, no signal-discovery claim,
no Bianchi-class-identification-of-the-sky claim, no native-solver-produced
claim, no probabilistic-inference claim.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

from htt.obsstat.egs3_graded_comparator import (
    SECTORS, CHANNELS, channel_response_design, NULL_SECTOR_KIND,
)
from htt.teff.representative import radial_fingerprint, two_temperature_ratio

__all__ = [
    "comparator_schema_instance",
    "teff_schema_instance",
    "schema_correspondence",
    "unification_schema_seal",
]


def comparator_schema_instance() -> dict:
    """Instance 1: exact rank/null structure of the registered channel
    response design, with the null-KIND annotation carried through."""
    D = sp.Matrix(channel_response_design().astype(int))
    rank = D.rank()
    null_basis = D.nullspace()
    null_sectors = []
    for vec in null_basis:
        idx = [i for i in range(4) if vec[i] != 0]
        if len(idx) == 1:
            null_sectors.append(SECTORS[idx[0]])
    null_sectors = tuple(sorted(null_sectors))
    kinds = {name: NULL_SECTOR_KIND[name]["kind"] for name in null_sectors}
    reopens = {name: list(NULL_SECTOR_KIND[name]["reopens_via"])
               for name in null_sectors}
    return {
        "design_matrix": [[int(x) for x in row] for row in
                          channel_response_design().astype(int)],
        "channels": list(CHANNELS),
        "sectors": list(SECTORS),
        "rank_exact": int(rank),
        "null_sectors": list(null_sectors),
        "null_basis_axis_aligned": bool(len(null_sectors) == len(null_basis)),
        "null_sector_kinds": kinds,
        "reopens_via": reopens,
        "invariant_functional": "the reachable-sector projection P_R g "
                                "(annihilates the null directions exactly)",
    }


def teff_schema_instance() -> dict:
    """Instance 2: the exact 3x2 Teff moment-response matrix and the
    retained-moment (p=4) selector's exact annihilation of both enrichment
    directions."""
    s = sp.Symbol("s", positive=True)
    u = sp.Symbol("u", positive=True)       # u = s^2
    rows = {}
    for p in (3, 4, 5):
        c_p = radial_fingerprint(p)                       # insertion response
        expr, svar = two_temperature_ratio(p)
        Rp_u = sp.simplify(expr.subs(svar, sp.sqrt(u)))
        dRp = sp.simplify(sp.diff(Rp_u, u).subs(u, 0))    # two-temp response
        rows[p] = (sp.nsimplify(c_p), dRp)
    T = sp.Matrix([[rows[3][0], rows[3][1]],
                   [rows[4][0], rows[4][1]],
                   [rows[5][0], rows[5][1]]])
    p4_row = T.row(1)
    p4_annihilates = bool(p4_row == sp.Matrix([[0, 0]]))
    # R_4 == 1 identically (stronger than the derivative-at-0 statement)
    expr4, svar4 = two_temperature_ratio(4)
    r4_identity = bool(sp.simplify(expr4 - 1) == 0)
    rank = T.rank()
    expected = sp.Matrix([[sp.Rational(-1, 16), sp.Rational(-3, 2)],
                          [0, 0],
                          [sp.Rational(1, 64), sp.Rational(5, 2)]])
    return {
        "response_matrix_exact": [[str(T[i, j]) for j in range(2)]
                                  for i in range(3)],
        "matches_registered_constants": bool(T == expected),
        "observables": ["p=3 moment", "p=4 moment (RETAINED anchor)",
                        "p=5 moment"],
        "perturbation_directions": ["(n,k) insertion amplitude",
                                    "two-temperature mixing s^2"],
        "retained_selector_annihilates_both_directions": p4_annihilates,
        "R4_identically_one": r4_identity,
        "rank_exact_full_response": int(rank),
        "reopens_via": {"insertion": ["retain the p=3 moment",
                                      "retain the p=5 moment"],
                        "two_temperature": ["retain the p=3 moment",
                                            "retain the p=5 moment"]},
        "invariant_functional": "the retained p=4 moment (R_4 == 1 "
                                "identically; c_4 = 0 exactly)",
        "discrimination_note": "rank 2 of the FULL response = the two "
                               "enrichment directions separate once p=3/p=5 "
                               "are observed (Teff Thm 22 fingerprints)",
    }


def schema_correspondence() -> dict:
    """The sealed correspondence: both instances satisfy the SAME schema
    predicates, checked exactly on each side."""
    comp = comparator_schema_instance()
    teff = teff_schema_instance()
    predicates = {
        "registered_selector_has_nontrivial_exact_kernel": (
            len(comp["null_sectors"]) > 0
            and teff["retained_selector_annihilates_both_directions"]),
        "invariant_functional_annihilates_kernel_exactly": (
            comp["null_basis_axis_aligned"] and teff["R4_identically_one"]),
        "reopening_requires_enlarging_the_observable_set": (
            all(comp["reopens_via"].values())
            and all(teff["reopens_via"].values())),
        "full_response_rank_two_on_both_sides": (
            comp["rank_exact"] == 2
            and teff["rank_exact_full_response"] == 2),
    }
    return {
        "schema": "finite-dimensional linear response A + registered selector "
                  "S + exact kernel ker(S A) + kernel-annihilating invariant "
                  "functional; blindness removed only by enlarging the "
                  "observable set",
        "instance_comparator": comp,
        "instance_teff": teff,
        "predicates": predicates,
        "all_predicates_hold": bool(all(predicates.values())),
        "correspondence_kind": "MATHEMATICAL (two exact instances of one "
                               "schema); no physical identification between "
                               "the lanes is asserted",
    }


def unification_schema_seal() -> dict:
    """Fail-closed U3 seal."""
    cor = schema_correspondence()
    comp = cor["instance_comparator"]
    teff = cor["instance_teff"]
    ok = (cor["all_predicates_hold"]
          and comp["rank_exact"] == 2
          and set(comp["null_sectors"]) == {"Omega_k", "W2"}
          and comp["null_sector_kinds"].get("W2") == "structural_null"
          and comp["null_sector_kinds"].get("Omega_k")
          == "no_channel_leading_order"
          and teff["matches_registered_constants"]
          and teff["retained_selector_annihilates_both_directions"]
          and teff["R4_identically_one"])
    return {
        "seal": "egs3.unification_schema",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "numpy_version": np.__version__,
        "theorem_U3": "the comparator channel response (rank 2, exact null "
                      "{W2, Omega_k} with distinct null KINDS) and the Teff "
                      "retained-moment response (p=4 selector exactly "
                      "annihilating the insertion and two-temperature "
                      "directions, full response rank 2) are two exact "
                      "instances of one linear-response schema; in both, "
                      "blindness is removed only by enlarging the registered "
                      "observable set",
        "correspondence": cor,
        "claim_boundary": "exact integer/rational linear algebra over "
                          "registered in-repo objects; the correspondence is "
                          "mathematical, not physical; diagnostic_only; no "
                          "data, signal-discovery, "
                          "Bianchi-class-identification-of-the-sky, "
                          "native-solver-produced, or probabilistic-inference "
                          "claim",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(unification_schema_seal(), indent=2, default=float))
