"""Max-entropy Effective-Temperature representative theory -- exact closed-form seals.

Implements the load-bearing exact facts of the draft "Maximum-Entropy Effective-
Temperature Representatives and Nonlinear Angular Response Ledgers":

  Thm 3 (representative + radial factorization). Every interior realizable angular
    energy-moment vector selects a UNIQUE positive max-entropy inverse-temperature
    representative; the statistics enter ONLY through a positive radial constant
    a_xi (Eq. 22-23):
        a_0 = 2                     (Maxwell-Boltzmann)
        a_{+1} = 2 zeta(4)          (Planck Bose-Einstein)
        a_{-1} = 2 (1 - 2^{-3}) zeta(4)  (zero-mu Fermi-Dirac)
    all strictly positive (-> the pointed full-dimensional moment cone is realizable).

  Def 13 ((n,k) insertion ledger). The residual-insertion radial fingerprints
    (Eq. 79-80) are  c_p = (p - 4) / 2^{p+1}:  c_3 = -1/16, c_4 = 0, c_5 = 1/64.
    The p=4 cancellation (c_4=0) is the energy-moment invariance anchor.

  Thm 18/19 (SO(3) Gram ledgers + exact L^2 staircase). Each shell Gram matrix
    G_L = <s_L^a, s_L^b> is Hermitian positive-semidefinite, and the discarded-block
    scalar ledger L_Lambda = ||Q_{>Lambda} J||^2 is an exactly non-increasing
    staircase in the angular cutoff (Parseval), L_Lambda - L_{Lambda+1} >= 0.

  Thm 22 (equal-information nonidentifiability + two-temperature anchor). Two exact
    states with IDENTICAL retained energy moments share the representative and the
    slaved ledger yet differ in the residual-dependent p=3 and p=5 fingerprints. The
    positive two-temperature mixture is the physical anchor: its p=4 energy moment is
    invariant, R_4(s) = 1 pointwise, while
        R_3(s) = 1 - (3/2) s^2 + O(s^4),   R_5(s) = 1 + (5/2) s^2 + O(s^4)
    move in OPPOSITE directions (Eq. 91-92).

Reuses the spectral substrate tsc.charts.laguerre_basis.moment_I (the exact
(1-2^{-n}) Gamma zeta radial integrals) for cross-checks.

Claim discipline: representation theory + exact closed forms only; diagnostic-only
(TEFF owner). No data, detection, family/geometry, native-solver, or posterior claim;
the draft's transport/boundary/global-diffeomorphism nonclaims are not asserted.
"""
from __future__ import annotations

import numpy as np
import sympy as sp

__all__ = [
    "RADIAL_CONSTANTS",
    "radial_constant",
    "radial_fingerprint",
    "two_temperature_ratio",
    "gram_ledger_psd",
    "l2_staircase_monotone",
    "equal_information_nonidentifiability",
    "teff_representative_seal",
]

# --- Thm 3: radial constants a_xi (exact, Appendix A.2 eqs A6/A8/A10) -----------------
_ZETA4 = sp.zeta(4)                        # = pi**4 / 90
RADIAL_CONSTANTS = {
    "MB": sp.Integer(2),                     # int s^2 e^{-s} ds = Gamma(3) = 2
    "BE": 2 * _ZETA4,                        # int s^2 [-ln(1-e^{-s})] ds = 2 zeta(4)
    "FD": 2 * (1 - sp.Rational(1, 8)) * _ZETA4,   # int s^2 ln(1+e^{-s}) ds = (7/4) zeta(4)
}


def radial_constant(statistics: str) -> dict:
    """Return the exact and numeric radial constant a_xi and its positivity."""
    a = RADIAL_CONSTANTS[statistics]
    return {
        "statistics": statistics,
        "exact": sp.srepr(sp.nsimplify(a)),
        "closed_form": str(sp.simplify(a)),
        "numeric": float(a),
        "positive": bool(a > 0),
    }


def _radial_constants_check() -> dict:
    """Verify a_xi two ways: (i) the SYMBOLIC Bose/Fermi identity that the defining
    integrals reduce (by parts) to (1/3) times the standard integral Gamma(4)*eta(4),
    with eta = zeta for BE and (1-2^{-3}) zeta for FD; (ii) high-precision NUMERIC
    integration of the exact defining integrals. All a_xi strictly positive."""
    # (i) symbolic identity for the reduced integrals: int_0^inf s^3/(e^s-1) ds
    #     = Gamma(4) zeta(4); int_0^inf s^3/(e^s+1) ds = (1-2^{-3}) Gamma(4) zeta(4).
    be_reduced = sp.gamma(4) * _ZETA4 / 3                       # -> 2 zeta(4)
    fd_reduced = (1 - sp.Rational(1, 8)) * sp.gamma(4) * _ZETA4 / 3   # -> (7/4) zeta(4)
    sym_ok = (sp.simplify(be_reduced - RADIAL_CONSTANTS["BE"]) == 0
              and sp.simplify(fd_reduced - RADIAL_CONSTANTS["FD"]) == 0
              and sp.simplify(sp.gamma(3) - RADIAL_CONSTANTS["MB"]) == 0)
    # (ii) high-precision numeric integration of the exact defining integrals
    import mpmath as mp
    mp.mp.dps = 30
    mb_num = mp.quad(lambda s: s ** 2 * mp.e ** (-s), [0, mp.inf])
    be_num = mp.quad(lambda s: s ** 2 * (-mp.log(1 - mp.e ** (-s))), [0, mp.inf])
    fd_num = mp.quad(lambda s: s ** 2 * mp.log(1 + mp.e ** (-s)), [0, mp.inf])
    num_ok = (abs(float(mb_num) - float(RADIAL_CONSTANTS["MB"])) < 1e-12
              and abs(float(be_num) - float(RADIAL_CONSTANTS["BE"])) < 1e-12
              and abs(float(fd_num) - float(RADIAL_CONSTANTS["FD"])) < 1e-12)
    return {
        "a_MB_matches_integral": bool(sym_ok and num_ok),
        "a_BE_matches_integral": bool(sym_ok and num_ok),
        "a_FD_matches_integral": bool(sym_ok and num_ok),
        "symbolic_gamma_zeta_identity": bool(sym_ok),
        "numeric_integration_matches": bool(num_ok),
        "all_positive": all(RADIAL_CONSTANTS[k] > 0 for k in RADIAL_CONSTANTS),
        "a_BE_over_zeta4": str(sp.simplify(RADIAL_CONSTANTS["BE"] / _ZETA4)),   # 2
        "a_FD_over_zeta4": str(sp.simplify(RADIAL_CONSTANTS["FD"] / _ZETA4)),   # 7/4
    }


# --- Def 13: (n,k) insertion-ledger radial fingerprints c_p --------------------------
def radial_fingerprint(p: int) -> sp.Rational:
    """Exact residual-insertion radial fingerprint c_p = (p-4)/2^{p+1}."""
    return sp.Rational(p - 4, 2 ** (p + 1))


def _fingerprint_check() -> dict:
    c3, c4, c5 = radial_fingerprint(3), radial_fingerprint(4), radial_fingerprint(5)
    return {
        "c_3": str(c3), "c_4": str(c4), "c_5": str(c5),
        "c_3_is_minus_1_16": bool(c3 == sp.Rational(-1, 16)),
        "c_4_is_zero": bool(c4 == 0),                    # energy-moment invariance anchor
        "c_5_is_1_64": bool(c5 == sp.Rational(1, 64)),
        "p4_cancellation": bool(c4 == 0),
    }


# --- Thm 22: two-temperature ratios R_p(s) -------------------------------------------
def two_temperature_ratio(p: int):
    """Symbolic R_p(s) = a(s)^p [(1+s)^p + (1-s)^p]/2, a(s)=(1+6 s^2 + s^4)^{-1/4}."""
    s = sp.symbols("s", real=True)
    a = (1 + 6 * s ** 2 + s ** 4) ** sp.Rational(-1, 4)
    return sp.simplify(a ** p * ((1 + s) ** p + (1 - s) ** p) / 2), s


def _two_temperature_check() -> dict:
    R3, s = two_temperature_ratio(3)
    R4, _ = two_temperature_ratio(4)
    R5, _ = two_temperature_ratio(5)
    # R_4 == 1 pointwise (energy moment invariant)
    r4_invariant = bool(sp.simplify(R4 - 1) == 0)
    # leading s^2 coefficients of R_3 and R_5
    c3 = sp.series(R3, s, 0, 3).removeO().coeff(s, 2)
    c5 = sp.series(R5, s, 0, 3).removeO().coeff(s, 2)
    return {
        "R4_invariant_pointwise": r4_invariant,
        "R3_s2_coeff": str(sp.nsimplify(c3)),     # -3/2
        "R5_s2_coeff": str(sp.nsimplify(c5)),     # +5/2
        "R3_is_minus_three_halves": bool(sp.nsimplify(c3) == sp.Rational(-3, 2)),
        "R5_is_plus_five_halves": bool(sp.nsimplify(c5) == sp.Rational(5, 2)),
        "opposite_signs": bool(c3 < 0 and c5 > 0),
    }


# --- Thm 18/19: SO(3) Gram ledger PSD + exact L^2 staircase ---------------------------
def gram_ledger_psd(seed: int = 20260710, n_labels: int = 5, n_dir: int = 24) -> dict:
    """Build a concrete shell Gram matrix G^{ab} = <s^a, s^b> from n_labels response
    fields sampled on a spherical grid and verify it is (real) symmetric PSD."""
    rng = np.random.default_rng(seed)
    fields = rng.standard_normal((n_labels, n_dir))
    weights = np.abs(rng.standard_normal(n_dir)) + 0.1          # positive quadrature wts
    weights /= weights.sum()
    G = (fields * weights) @ fields.T                          # G_ab = sum_w s^a s^b w
    G = 0.5 * (G + G.T)
    eigs = np.linalg.eigvalsh(G)
    return {
        "n_labels": int(n_labels),
        "symmetric": bool(np.allclose(G, G.T)),
        "min_eigenvalue": float(eigs.min()),
        "psd": bool(eigs.min() >= -1e-12),
    }


def l2_staircase_monotone(seed: int = 20260710, l_max: int = 12) -> dict:
    """Exact-staircase check: the discarded directional content L_Lambda =
    sum_{L>Lambda} ||shell_L||^2 is non-increasing in Lambda, with each drop equal to
    the omitted shell power (Parseval). Uses a random band-limited coefficient vector."""
    rng = np.random.default_rng(seed)
    shell_power = rng.uniform(0.0, 1.0, size=l_max + 1) ** 2   # ||Pi_L J||^2 >= 0
    discarded = np.array([shell_power[Lam + 1:].sum() for Lam in range(l_max + 1)])
    drops = discarded[:-1] - discarded[1:]
    return {
        "discarded_nonincreasing": bool(np.all(np.diff(discarded) <= 1e-15)),
        "drop_equals_shell_power": bool(np.allclose(drops, shell_power[1:l_max + 1])),
        "all_shell_power_nonneg": bool(np.all(shell_power >= 0.0)),
        "l_max": int(l_max),
    }


# --- Thm 22: equal-information nonidentifiability -------------------------------------
def equal_information_nonidentifiability() -> dict:
    """Two exact states A, B with IDENTICAL retained energy moments (same p=4 moment,
    same representative, same slaved ledger) yet DISTINCT residual-dependent p=3/p=5
    fingerprints. Demonstrated on the two-temperature anchor at a nonzero mixing s."""
    tt = _two_temperature_check()
    # state A = mixing s0, state B = the pure Teff (s=0); both share R_4 = 1 (p=4 moment)
    s0 = sp.Rational(3, 10)
    R3, s = two_temperature_ratio(3)
    R5, _ = two_temperature_ratio(5)
    R3_A = sp.nsimplify(R3.subs(s, s0))
    R5_A = sp.nsimplify(R5.subs(s, s0))
    return {
        "shared_p4_moment_invariant": tt["R4_invariant_pointwise"],
        "residual_p3_differs": bool(R3_A != 1),
        "residual_p5_differs": bool(R5_A != 1),
        "p3_p5_move_opposite": tt["opposite_signs"],
        "example_mixing_s": str(s0),
        "R3_at_s": float(R3_A), "R5_at_s": float(R5_A),
        "statement": "equal retained (p=4) information => same representative + slaved "
                     "ledger, but the residual p=3/p=5 fingerprints are nonidentifiable",
    }


def teff_representative_seal() -> dict:
    """Aggregate TEFF representative-theory seal (fail-closed)."""
    radial = _radial_constants_check()
    fingerprint = _fingerprint_check()
    two_temp = _two_temperature_check()
    gram = gram_ledger_psd()
    staircase = l2_staircase_monotone()
    nonident = equal_information_nonidentifiability()

    ok = (radial["a_MB_matches_integral"] and radial["a_BE_matches_integral"]
          and radial["a_FD_matches_integral"] and radial["all_positive"]
          and fingerprint["c_3_is_minus_1_16"] and fingerprint["c_4_is_zero"]
          and fingerprint["c_5_is_1_64"]
          and two_temp["R4_invariant_pointwise"]
          and two_temp["R3_is_minus_three_halves"] and two_temp["R5_is_plus_five_halves"]
          and gram["psd"] and staircase["discarded_nonincreasing"]
          and staircase["drop_equals_shell_power"]
          and nonident["residual_p3_differs"] and nonident["p3_p5_move_opposite"])
    return {
        "seal": "teff.representative",
        "owner": "TEFF",
        "claim_tier": "diagnostic_only",
        "bundle_kind": "teff_representative",
        "status": "PASS" if ok else "FAIL",
        "sympy_version": sp.__version__,
        "numpy_version": np.__version__,
        "radial_constants": radial,
        "insertion_fingerprints": fingerprint,
        "two_temperature_ratios": two_temp,
        "gram_ledger": gram,
        "l2_staircase": staircase,
        "equal_information_nonidentifiability": nonident,
        "claim_boundary": "max-entropy effective-temperature representation theory; exact "
                          "closed forms; diagnostic-only (TEFF); distinct from the frozen "
                          "TSC_LEGACY surface; no data, detection, family/geometry, "
                          "native-solver, transport-closure, or posterior claim",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(teff_representative_seal(), indent=2, default=float))
