#!/usr/bin/env python3
"""Contract controls for finite pooling box, including an independent vertex oracle."""
from fractions import Fraction as F
from itertools import product

from run_closure import finite_box, interval, sqrt_bounds_inverse_weight


def row(pgc, dm, err):
    return {"pgc": pgc, "dm": dm, "err": err}


def check():
    for width in (F(1, 2), F(1)):
        one = [row(11, "35.123", "0.47")]
        z = finite_box(one, width)
        assert (z["lower"], z["upper"]) == interval(one[0]["dm"], width)
        assert z["convex_hull"] == interval(one[0]["dm"], width)
        rows = [row(11, "35.123", "0.47"), row(12, "36.874", "0.83")]
        z = finite_box(rows, width)
        vertex_min, vertex_max = [], []
        for s1, s2 in product((0, 1), repeat=2):
            ws = []
            for r, side in zip(rows, (s1, s2)):
                lo, hi = interval(r["err"], width)
                ws.append(1 / (hi if side == 0 else lo)**2)
            den = sum(ws, F())
            vertex_min.append(sum((interval(r["dm"], width)[0] * w for r, w in zip(rows, ws)), F()) / den)
            vertex_max.append(sum((interval(r["dm"], width)[1] * w for r, w in zip(rows, ws)), F()) / den)
        assert z["lower"] == min(vertex_min)
        assert z["upper"] == max(vertex_max)
        assert z["convex_hull"][0] <= z["lower"] <= z["upper"] <= z["convex_hull"][1]
        shifted = [row(r["pgc"], str(F(r["dm"])+3), r["err"]) for r in rows]
        # Keep the same lexical quantum in the translated tokens.
        shifted = [row(11, "38.123", "0.47"), row(12, "39.874", "0.83")]
        zs = finite_box(shifted, width)
        assert zs["lower"]-z["lower"] == zs["upper"]-z["upper"] == 3
        target_lo, target_hi = interval("36.111", width)
        assert (target_lo-zs["upper"], target_hi-zs["lower"]) == (target_lo-z["upper"]-3, target_hi-z["lower"]-3)
    all_rows = [row(11, "35.123", "0.47"), row(12, "36.874", "0.83")]
    only_sdss = [all_rows[0]]
    assert finite_box(all_rows, F(1,2))["nominal"] != finite_box(only_sdss, F(1,2))["nominal"]
    for w in (F(1,9), F(17,4), F(1,10000)):
        lo, hi = sqrt_bounds_inverse_weight(w)
        assert lo*lo*w <= 1 <= hi*hi*w
        assert hi-lo <= F(1, 10**55)
    print("PASS five contract controls plus certified square-root enclosure")


if __name__ == "__main__":
    check()
