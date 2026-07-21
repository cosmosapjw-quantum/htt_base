"""PR-175 SymPy axis: eleven-type invariant identities vs external anchor.

Runs the exact Koszul frame chain (Engine A) for every canonical
representative, compares with the external Ellis-MacCallum anchor
formula, and verifies the class-B vector constraint and the VI_h/VII_h
h-relation. Exact rationals only; no family ranking or identification.
"""

from __future__ import annotations

import json
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from common.pr175_invariant_oracle import (  # noqa: E402
    CANONICAL_TYPES,
    anchor_ricci_scalar,
    engine_a_ricci_scalar,
    structure_constants,
)


def run_axis() -> dict:
    computed: dict[str, str] = {}
    anchor_ok = True
    for name in CANONICAL_TYPES:
        exact = engine_a_ricci_scalar(name)
        anchor = anchor_ricci_scalar(name)
        anchor_ok = anchor_ok and (exact == anchor)
        computed[f"R_{name}"] = str(exact)

    # Class-B constraint DERIVED from the constructed structure constants:
    # reconstruct n^{ab} = (1/2) eps^{bcd} C^a_{cd} (symmetric part) and
    # a_b = (1/2) C^d_{db}, then require a_b n^{ba} = 0 and the Jacobi
    # identity C^e_{[bc} C^a_{d]e} = 0 for every representative.
    import sympy as sp

    eps = [[[int((i - j) * (j - k) * (k - i) / 2) for k in range(3)]
            for j in range(3)] for i in range(3)]
    class_b_ok = True
    for name in CANONICAL_TYPES:
        C = structure_constants(name)
        n_rec = sp.zeros(3, 3)
        for a_i in range(3):
            for b_i in range(3):
                n_rec[a_i, b_i] = sp.Rational(1, 2) * sum(
                    eps[b_i][c][d] * C[a_i][c][d] for c in range(3)
                    for d in range(3)
                )
        n_sym = sp.Rational(1, 2) * (n_rec + n_rec.T)
        a_rec = [sp.Rational(1, 2) * sum(C[d][d][b_i] for d in range(3))
                 for b_i in range(3)]
        a_dot_n = [sum(a_rec[b_i] * n_sym[b_i, a_i] for b_i in range(3))
                   for a_i in range(3)]
        class_b_ok = class_b_ok and all(v == 0 for v in a_dot_n)
        jacobi_ok = True
        for a_i in range(3):
            for b_i in range(3):
                for c_i in range(3):
                    for d_i in range(3):
                        cyc = sum(
                            C[e][b_i][c_i] * C[a_i][d_i][e]
                            + C[e][c_i][d_i] * C[a_i][b_i][e]
                            + C[e][d_i][b_i] * C[a_i][c_i][e]
                            for e in range(3)
                        )
                        jacobi_ok = jacobi_ok and (sp.simplify(cyc) == 0)
        class_b_ok = class_b_ok and jacobi_ok
    h_ok = True
    for name in ("VI_h", "VII_h"):
        entry = CANONICAL_TYPES[name]
        a = Fraction(entry["a"])
        n2, n3 = Fraction(entry["n"][1]), Fraction(entry["n"][2])
        h = Fraction(entry["h"])
        h_ok = h_ok and (a**2 == abs(h) * abs(n2 * n3)) and (
            (h > 0) == (n2 * n3 > 0)
        )

    checks = {
        "eleven_type_ricci_scalar_matches_anchor": bool(anchor_ok),
        "class_b_vector_constraint_a_dot_n_zero": bool(class_b_ok),
        "vi_vii_h_relation_consistent": bool(h_ok),
    }
    return {
        "all_pass": all(checks.values()),
        "checks": checks,
        "computed": computed,
    }


if __name__ == "__main__":
    print(json.dumps(run_axis(), sort_keys=True))
