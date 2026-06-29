#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reviewer_verification.py — independent re-checks of the claims audited in
RESEARCH_EVALUATION_REVIEW.md. Stdlib only; no project code imported, so these
are genuinely independent confirmations (or counter-demonstrations).

Checks:
  1. EGS3-B4 bracket nondegeneracy constant  C_up*kappa*(1+R) > 1
  2. EGS3-A3 Pi-as-e-value: unit null mean + Markov false-exceedance bound
  3. NT2-A1 Fisher floor: monotone decreasing in L, strictly < 0.632 for L>2
  4. EGS3-B3 radial-vorticity identity  n . Omega . n == 0  (antisymmetric Omega)
  5. EGS3-A1 rank: DEMONSTRATION of the review's key point -- a rank-2 response
     map is consistent with BOTH (a) Omega_k a genuine null (zero column) and
     (b) Omega_k degenerate with Sigma2 (collinear column). The rank count alone
     does NOT distinguish them; the report must show which holds for Omega_k.
"""
from __future__ import annotations

import math
import random


def check_bracket_constant():
    kappa, C_up = 4.0 / 21.0, 9.0
    val = C_up * kappa * (1.0 + 0.0)          # R=0 (tightest)
    ok = val > 1.0
    print(f"1. EGS3-B4 bracket constant C_up*kappa*(1+R)|R=0 = {val:.4f} (= 12/7)"
          f"  > 1 ? {ok}")
    # also confirm lower<upper (proper interval) for a sample a2,a3
    a2, a3 = 3e-5, 6e-6
    lo = a2 * kappa / (1 + a3 / a2)
    hi = C_up * a2
    print(f"   proper interval for a2=3e-5,a3=6e-6: [{lo:.2e}, {hi:.2e}], lo<hi ? {lo < hi}")
    return ok and lo < hi


def check_evalue(n=200000, alpha=0.1, beta=0.05, seed=7):
    rng = random.Random(seed)
    # registered null: x ~ U(0,1); threshold t so that P(x>t)=alpha
    t = 1.0 - alpha
    E = [(1.0 / alpha) if rng.random() > t else 0.0 for _ in range(n)]
    null_mean = sum(E) / n
    p_exceed = sum(1 for e in E if e >= 1.0 / beta) / n
    print(f"2. EGS3-A3 e-value E=1[x>t]/alpha (alpha={alpha}):")
    print(f"   null mean = {null_mean:.4f} (target 1.0); "
          f"P(E>=1/beta={1/beta:.0f}) = {p_exceed:.4f} <= beta={beta} ? "
          f"{p_exceed <= beta + 0.005}")
    return abs(null_mean - 1.0) < 0.02 and p_exceed <= beta + 0.005


def fisher_floor(L, f_sky=1.0):
    r = {2: 1.0}
    for ell in range(3, L + 1):
        r[ell] = (2.0 / ell) ** 1.5
    I = sum((2 * ell + 1) / 2.0 * f_sky * r[ell] ** 2 for ell in r)
    return 1.0 / math.sqrt(I)


def check_fisher_floor():
    floors = [(L, fisher_floor(L)) for L in (2, 3, 5, 10, 20)]
    mono = all(floors[i][1] >= floors[i + 1][1] for i in range(len(floors) - 1))
    below = all(f < 0.6325 for L, f in floors if L > 2)
    print("3. NT2-A1 Fisher floor vs L:", ", ".join(f"L{L}:{f:.4f}" for L, f in floors))
    print(f"   monotone decreasing ? {mono}; all (L>2) < 0.632 ? {below}; "
          f"single-l sqrt(2/5)={math.sqrt(0.4):.4f}")
    return mono and below


def check_radial_vorticity(n=100000, seed=11):
    rng = random.Random(seed)
    worst = 0.0
    for _ in range(n):
        w = (rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))   # axial vector
        nv = [rng.gauss(0, 1) for _ in range(3)]
        nr = math.sqrt(sum(c * c for c in nv)); nv = [c / nr for c in nv]
        # Omega antisymmetric: Omega_ab n^b = (w x n); radial = n . (w x n) = 0
        cx = w[1] * nv[2] - w[2] * nv[1]
        cy = w[2] * nv[0] - w[0] * nv[2]
        cz = w[0] * nv[1] - w[1] * nv[0]
        worst = max(worst, abs(cx * nv[0] + cy * nv[1] + cz * nv[2]))
    print(f"4. EGS3-B3 radial-vorticity n.Omega.n: max over {n} = {worst:.2e} (== 0)")
    return worst < 1e-12


def _rank(rows, tol=1e-9):
    """Gaussian-elimination rank of a small matrix (list of rows)."""
    M = [r[:] for r in rows]
    R = len(M)
    C = len(M[0]) if R else 0
    rank = 0
    for col in range(C):
        piv = None
        for r in range(rank, R):
            if abs(M[r][col]) > tol:
                piv = r
                break
        if piv is None:
            continue
        M[rank], M[piv] = M[piv], M[rank]
        pv = M[rank][col]
        M[rank] = [x / pv for x in M[rank]]
        for r in range(R):
            if r != rank and abs(M[r][col]) > tol:
                f = M[r][col]
                M[r] = [a - f * b for a, b in zip(M[r], M[rank])]
        rank += 1
    return rank


def demonstrate_omega_k_point():
    """The review's key point. Columns = sectors (Sigma2, W2, Omega_tilt, Omega_k);
    rows = channels (CMB-T quadrupole response, radial-velocity dipole response).
    W2 column is ZERO in both channels (genuine null). We show TWO response maps
    that BOTH give rank 2 but mean different things for Omega_k."""
    print("5. EGS3-A1 rank vs the Omega_k characterization (review's key point):")
    # columns: [Sigma2, W2, Omega_tilt, Omega_k]
    # (a) Omega_k a GENUINE null: its column is zero in both channels
    A_null = [
        [1.0, 0.0, 0.0, 0.0],   # CMB-T quadrupole sees Sigma2 only
        [0.0, 0.0, 1.0, 0.0],   # radial velocity sees Omega_tilt only
    ]
    # (b) Omega_k DEGENERATE with Sigma2: its column is collinear with Sigma2's
    A_degen = [
        [1.0, 0.0, 0.0, 0.7],   # CMB-T quadrupole sees Sigma2 AND Omega_k (collinear)
        [0.0, 0.0, 1.0, 0.0],
    ]
    ra, rd = _rank(A_null), _rank(A_degen)
    print(f"   (a) Omega_k genuine-null  response map -> rank {ra} (null = W2 and Omega_k)")
    print(f"   (b) Omega_k degenerate-w-Sigma2 map   -> rank {rd} "
          f"(null = W2 and the Sigma2-Omega_k combination; Omega_k NOT separately blind)")
    print("   => SAME rank 2, DIFFERENT meaning. The report must show which holds for")
    print("      Omega_k; the rank count alone cannot. (W2 is a genuine zero column in both.)")
    return ra == 2 and rd == 2


def main():
    print("=" * 76)
    print("Independent verification of RESEARCH_EVALUATION_REVIEW findings")
    print("=" * 76)
    results = {
        "bracket_constant": check_bracket_constant(),
        "evalue_markov": check_evalue(),
        "fisher_floor": check_fisher_floor(),
        "radial_vorticity": check_radial_vorticity(),
        "omega_k_demonstration": demonstrate_omega_k_point(),
    }
    print("\n" + "=" * 76)
    ok = sum(results.values())
    print(f"verification: {ok}/{len(results)} checks confirmed")
    for k, v in results.items():
        print(f"   {'PASS' if v else 'CHECK'}  {k}")
    print("=" * 76)
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
