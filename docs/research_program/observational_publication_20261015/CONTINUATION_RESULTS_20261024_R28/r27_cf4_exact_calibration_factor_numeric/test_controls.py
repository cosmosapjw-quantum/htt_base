"""Frozen finite controls; run once in the bounded actual invocation."""

from fractions import Fraction
import numpy as np

from factor import exact, exact_evaluation, factor_indices


def direct_contrasts(k, y, refs, nonrefs, channels):
    out = [Fraction(0) for _ in range(5)]
    for i in nonrefs:
        r = refs[int(channels[i])]
        for a in range(5):
            out[a] += exact(k[a, i]) * (exact(y[i]) - exact(y[r]))
    return out


def run():
    # Channels 0 and 1 have contrasts, channel 2 has one singleton, 3..6 empty.
    ids = np.array([21, 11, 31, 42, 52, 62, 72], dtype=np.int64)
    support = np.zeros((7, 7), dtype=np.bool_)
    support[0, 0] = support[1, 0] = support[2, 1] = support[3, 1] = True
    support[4, 2] = True
    support[5, [0, 1]] = True
    support[6, [0, 2]] = True
    singleton = support.sum(axis=1) == 1
    d = np.array([2., 1., 1., 3., 4., 5., 6.])
    k = np.zeros((5, 7), dtype=np.float64)
    k[:, 0] = [1., -1., 0., 0., 0.]
    k[:, 1] = [-1. + 2.**-52, 1., 0., 0., 0.]
    k[:, 2] = [0., 0., 1., 0., 0.]
    k[:, 3] = [0., 0., -1., 0., 0.]
    k[:, 4] = [0., 0., 0., 1., 0.]
    y = np.array([1., -2., np.nextafter(0., 1.), -np.nextafter(0., 1.),
                  7., 9., -3.])
    refs, nonrefs, channels = factor_indices(ids, support, singleton, d)
    assert refs.tolist() == [1, 2, 4, -1, -1, -1, -1]
    assert nonrefs.tolist() == [0, 3]
    old, sums, change, fact, price = exact_evaluation(k, y, d, refs, nonrefs, channels)
    assert fact == direct_contrasts(k, y, refs, nonrefs, channels)
    assert all(v == 0 for v in sums[3])
    assert sums[0][0] == Fraction(1, 2**52)
    assert price > 0 and any(v != 0 for v in change)
    assert fact[2] == Fraction(2, 2**1074)

    # D_diff A=0 for arbitrary exact support weights in mixed rows; no float test.
    weights = [(Fraction(1), Fraction(0)), (Fraction(1), Fraction(0)),
               (Fraction(0), Fraction(1)), (Fraction(0), Fraction(1)),
               (Fraction(0), Fraction(0)), (Fraction(2, 7), Fraction(5, 7)),
               (Fraction(3, 5), Fraction(0))]
    for i in nonrefs:
        c = int(channels[i]); r = int(refs[c])
        assert weights[i] == weights[r]
    # A huge admissible Gamma makes tiny uncorrected leakage arbitrarily large.
    leak = sums[0][0]
    assert leak != 0 and abs(float(leak)) < 1e-12
    gamma = Fraction(2**140)
    assert leak * leak * gamma > 1
    assert all(sum((exact(k[a, i]) * (weights[i][j] - weights[int(refs[int(channels[i])])][j])
                    for i in nonrefs), Fraction(0)) == 0
               for a in range(5) for j in range(2))

    # Permute rows and channel labels, then map references back by group ID.
    # The channel order changes, but the represented functional does not.
    p = np.array([5, 3, 6, 1, 4, 0, 2])
    q = np.array([3, 1, 6, 0, 2, 5, 4])
    rp, npidx, cp = factor_indices(ids[p], support[p][:, q], singleton[p], d[p])
    assert [None if r < 0 else int(ids[p[r]]) for r in rp] == [None if refs[c] < 0 else int(ids[refs[c]]) for c in q]
    old_p, sums_p, change_p, fact_p, price_p = exact_evaluation(k[:, p], y[p], d[p], rp, npidx, cp)
    assert (old_p, sums_p, change_p, fact_p, price_p) == (old, [sums[c] for c in q], change, fact, price)
    print("PASS: exact support contrasts, tiny leakage, subnormal parity, row/channel permutation")


if __name__ == "__main__":
    run()
