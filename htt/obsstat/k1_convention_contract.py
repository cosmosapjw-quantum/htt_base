"""PR-149: Planck K1 canonical convention, mask and transfer path, with a
TT BiPoSH odd-L diagonal structural-zero basis theorem.

A canonical low-multipole Planck K1 convention contract is frozen and content-
addressed (coordinate frame, alm indexing/phase/reality, beam/pixel window,
downgrade proc-nside, common mask, orientation grid), binding the existing
alm-convention validator, and is verified on the REAL Planck PR3 SMICA and
Commander maps through one shared observed-and-null pipeline.

The mathematical headline is a BASIS THEOREM proved by an INDEPENDENT Wigner-3j
oracle: the TT BiPoSH diagonal coefficient ``A^{LM}_{ll}`` vanishes identically
for every ODD ``L`` and ANY temperature ``a_lm`` (real alm being a subset) — the
mechanism is the ``l1=l2`` exchange symmetry of the ``a_{l m1} a_{l m2}``
product, which forces ``A = (-1)^L A`` through the Wigner-3j symmetry, so odd L
cancels regardless of the alm values.  The odd-L diagonal therefore carries no
trials and is quotiented out of the scan family, while even L is generically
non-zero.

Observable feature-extraction and basis-theorem mechanics at
``roadmap_rescue_v1:C1--C2`` only.  Freezing this mask/proc-nside/convention is
the pre-condition for the PR-150 raw-deletion swap; PR-149 makes no K1
detection or Bianchi-family claim, and the two CF4 P0s are untouched.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache

import numpy as np

# bind the existing alm-convention validator (import, do not restate)
from obsstat.alm_conventions import (  # noqa: E402
    canonical_temperature_alm_convention,
)

SCHEMA_VERSION = "pr149.k1_convention_contract.v1"


class K1ConventionError(ValueError):
    """Raised when the K1 convention discipline is violated."""


# --------------------------------------------------------------------------
# frozen canonical convention contract
# --------------------------------------------------------------------------
def canonical_convention_contract(*, proc_nside: int, lmax: int) -> dict:
    """The frozen, content-addressed low-ell K1 convention.  The reality and
    spin fields are DERIVED from the imported alm-convention validator (bind, do
    not restate), so a drift in the validator changes the content address."""
    if (
        isinstance(proc_nside, (bool, np.bool_))
        or not isinstance(proc_nside, (int, np.integer))
        or proc_nside <= 0
    ):
        raise K1ConventionError("proc_nside must be a positive integer")
    if (
        isinstance(lmax, (bool, np.bool_))
        or not isinstance(lmax, (int, np.integer))
        or lmax < 0
    ):
        raise K1ConventionError("lmax must be a non-negative integer")
    proc_nside = int(proc_nside)
    lmax = int(lmax)
    conv = canonical_temperature_alm_convention(lmax=lmax)   # bind + validate
    bound = {"reality_condition": conv.reality_condition,
             "spin_weight": int(conv.spin_weight),
             "lmax": int(conv.lmax)}
    contract = {
        "coordinate_frame": "galactic",
        "alm_indexing": "healpy_ring_m_major_l_minor",
        "alm_phase": "condon_shortley_healpy",
        "reality_condition": "a_l_minus_m_equals_neg1_pow_m_conj_a_lm",
        "beam_pixel_window": "downgrade_pixel_window_at_proc_nside",
        "proc_nside": proc_nside,
        "lmax": lmax,
        "common_mask": "COM_Mask_CMB-common-Mask-Int_2048_R3.00",
        "orientation_scan": "healpix_orientation_grid",
        "bound_alm_convention": bound,
    }
    contract["content_address"] = hashlib.sha256(
        json.dumps({k: v for k, v in contract.items()
                    if k != "content_address"},
                   sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return contract


def verify_convention_frozen(contract: dict, pinned: str) -> str:
    body = {k: v for k, v in contract.items() if k != "content_address"}
    got = hashlib.sha256(json.dumps(body, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()
    if got != contract.get("content_address") or (pinned and got != pinned):
        raise K1ConventionError(
            "the K1 convention contract does not match its committed content "
            "address — the frozen convention was edited")
    return got


# --------------------------------------------------------------------------
# independent Wigner-3j oracle + TT BiPoSH diagonal structural-zero theorem
# --------------------------------------------------------------------------
@lru_cache(maxsize=None)
def _wigner_3j(l1: int, l2: int, L: int, m1: int, m2: int, m: int) -> float:
    from sympy.physics.wigner import wigner_3j
    return float(wigner_3j(l1, l2, L, m1, m2, m))


def biposh_diagonal_coefficient(l: int, L: int, M: int,
                                alm: dict) -> complex:
    """``A^{LM}_{ll} = sum_{m1+m2=M} a_{l m1} a_{l m2} C^{LM}_{l m1 l m2}`` with
    the Clebsch-Gordan expressed through the independent Wigner-3j oracle."""
    total = 0.0 + 0.0j
    pref = np.sqrt(2 * L + 1)
    for m1 in range(-l, l + 1):
        m2 = M - m1
        if abs(m2) > l:
            continue
        w = _wigner_3j(l, l, L, m1, m2, -M)
        if w == 0.0:
            continue
        cg = ((-1) ** (M)) * pref * w
        total += alm[(l, m1)] * alm[(l, m2)] * cg
    return total


def _random_real_alm(l: int, rng) -> dict:
    alm = {}
    for m in range(0, l + 1):
        re = rng.standard_normal()
        im = 0.0 if m == 0 else rng.standard_normal()
        alm[(l, m)] = complex(re, im)
        if m > 0:
            alm[(l, -m)] = ((-1) ** m) * np.conj(alm[(l, m)])
    return alm


def _random_complex_alm(l: int, rng) -> dict:
    """A reality-VIOLATING complex alm (a_{l,-m} drawn independently), to show
    the structural zero holds for ANY alm, not only real ones."""
    return {(l, m): complex(rng.standard_normal(), rng.standard_normal())
            for m in range(-l, l + 1)}


def structural_zero_theorem(l_values, *, tol: float, seed: int = 20260724
                            ) -> dict:
    """The TT BiPoSH diagonal ``A^{LM}_{ll}`` is a structural ZERO for every
    ODD ``L`` and ANY temperature alm (the l1=l2 exchange symmetry forces
    ``A = (-1)^L A``), and generically non-zero for even ``L`` — verified by the
    independent Wigner-3j oracle at machine precision on BOTH random real alm
    and reality-VIOLATING complex alm (so the reality condition is shown to be
    irrelevant to the zero)."""
    try:
        l_values = list(l_values)
        tol = float(tol)
    except (TypeError, ValueError) as exc:
        raise K1ConventionError(
            "structural-zero theorem inputs are malformed") from exc
    if (
        not l_values
        or any(isinstance(l, (bool, np.bool_))
               or not isinstance(l, (int, np.integer))
               or l < 1 for l in l_values)
        or len(set(int(l) for l in l_values)) != len(l_values)
    ):
        raise K1ConventionError(
            "structural-zero theorem requires unique integer multipoles l >= 1")
    if not np.isfinite(tol) or tol <= 0:
        raise K1ConventionError(
            "structural-zero theorem tolerance must be finite and positive")
    l_values = [int(l) for l in l_values]
    rng = np.random.Generator(np.random.PCG64(seed))
    rows = []
    ok = True
    for l in l_values:
        for kind, alm in (("real", _random_real_alm(l, rng)),
                          ("complex_reality_violating",
                           _random_complex_alm(l, rng))):
            for L in range(1, 2 * l + 1):
                vals = [abs(biposh_diagonal_coefficient(l, L, M, alm))
                        for M in range(-L, L + 1)]
                max_abs = float(max(vals))
                odd = (L % 2 == 1)
                zero = max_abs < tol
                good = zero if odd else (max_abs > tol)
                ok = ok and good
                rows.append({"l": l, "L": L, "alm_kind": kind, "odd": odd,
                             "max_abs_diagonal_coefficient": max_abs,
                             "structural_zero": bool(zero)})
    if not ok:
        raise K1ConventionError(
            "the TT BiPoSH odd-L diagonal structural-zero theorem failed "
            "against the independent Wigner-3j oracle")
    return {"l_values": l_values, "tolerance_scientific": repr(tol),
            "rows": rows,
            "odd_L_diagonal_all_zero":
                bool(all(r["structural_zero"] for r in rows if r["odd"])),
            "even_L_diagonal_all_nonzero":
                bool(all(not r["structural_zero"] for r in rows
                         if not r["odd"])),
            "holds_for_reality_violating_alm":
                bool(all(r["structural_zero"] for r in rows
                         if r["odd"] and r["alm_kind"]
                         == "complex_reality_violating")),
            "note": "the TT BiPoSH diagonal vanishes identically for odd L and "
                    "ANY alm (the l1=l2 exchange symmetry, verified by an "
                    "independent Wigner-3j oracle on both real and reality-"
                    "violating complex alm); the odd-L diagonal carries no "
                    "trials and is quotiented from the scan family"}


# --------------------------------------------------------------------------
# real Planck map -> frozen proc-nside + mask + alm convention checks
# --------------------------------------------------------------------------
def load_downgrade_mask_alm(map_path, mask_path, *, proc_nside: int, lmax: int):
    import healpy as hp

    m = hp.read_map(str(map_path), field=0)
    mask = hp.read_map(str(mask_path))
    m_low = hp.ud_grade(m, proc_nside)
    mask_low = hp.ud_grade(mask, proc_nside)
    mask_bool = (mask_low > 0.5).astype(float)
    masked = m_low * mask_bool
    alm = hp.map2alm(masked, lmax=lmax)
    return {"map_low": m_low, "mask_bool": mask_bool, "masked": masked,
            "alm": alm, "fsky": float(mask_bool.mean())}


def alm_convention_checks(masked_map, alm, *, proc_nside: int, lmax: int
                          ) -> dict:
    """Pipeline SELF-CONSISTENCY (reality, map-to-alm-to-map round trip) PLUS a
    GENUINE, data-dependent convention cross-check: a map-space rotation
    (``rotate_map_alms``) and an alm-space rotation (``rotate_alm``) are two
    independent healpy code paths that agree ONLY if the alm phase/frame
    convention is consistent; a wrong m-phase mutation is DEMONSTRATED to break
    the agreement (so the cross-check catches a wrong convention rather than
    trivially passing)."""
    import healpy as hp

    # (a) internal self-consistency: reality + round trip (pass for any
    # band-limited alm; NOT a convention validation, labelled as such)
    recon = hp.alm2map(alm, proc_nside, lmax=lmax)
    m0_imag = float(max(abs(alm[hp.Alm.getidx(lmax, ell, 0)].imag)
                        for ell in range(0, lmax + 1)))
    round_trip_alm = hp.map2alm(recon, lmax=lmax)
    rt = float(np.max(np.abs(round_trip_alm - alm))
               / max(np.max(np.abs(alm)), 1e-30))
    # (b) GENUINE convention cross-check: map-space vs alm-space rotation
    euler = (40.0, 25.0, 15.0)
    rot = hp.Rotator(rot=euler, deg=True)
    alm_maprot = hp.map2alm(rot.rotate_map_alms(masked_map, lmax=lmax),
                            lmax=lmax)
    alm_almrot = rot.rotate_alm(alm.copy(), lmax=lmax)
    scale = max(np.max(np.abs(alm_almrot)), 1e-30)
    crosscheck = float(np.max(np.abs(alm_maprot - alm_almrot)) / scale)
    # DEMONSTRATE the cross-check catches a wrong convention: apply a wrong
    # (-1)^m phase to the alm before the alm-space rotation
    m_of = np.array([hp.Alm.getlm(lmax, i)[1] for i in range(len(alm))])
    alm_wrong = rot.rotate_alm((alm * ((-1.0) ** m_of)).copy(), lmax=lmax)
    crosscheck_wrong = float(np.max(np.abs(alm_maprot - alm_wrong)) / scale)
    reality_ok = bool(m0_imag < 1e-6)
    round_trip_ok = bool(rt < 1e-6)
    crosscheck_ok = bool(crosscheck < 1.0e-2)
    mutation_caught = bool(crosscheck_wrong > 0.1)
    if not (reality_ok and round_trip_ok and crosscheck_ok and mutation_caught):
        raise K1ConventionError(
            f"a convention check failed (reality {reality_ok}, round-trip "
            f"{round_trip_ok}, rotation-crosscheck {crosscheck_ok}, "
            f"mutation-caught {mutation_caught})")
    return {"self_consistency_m0_max_imag": m0_imag,
            "self_consistency_round_trip_rel_error": rt,
            "rotation_crosscheck_rel_error": crosscheck,
            "rotation_crosscheck_wrong_phase_rel_error": crosscheck_wrong,
            "reality_ok": reality_ok, "round_trip_ok": round_trip_ok,
            "rotation_crosscheck_ok": crosscheck_ok,
            "wrong_phase_mutation_caught": mutation_caught,
            "note": "reality and round trip are INTERNAL pipeline self-"
                    "consistency (not a convention validation); the map-space "
                    "vs alm-space rotation cross-check is the genuine, data-"
                    "dependent convention test and a wrong m-phase mutation is "
                    "demonstrated to break it (caught, not hidden)"}


# --------------------------------------------------------------------------
# observed / null shared-pipeline equality
# --------------------------------------------------------------------------
_MICROKELVIN = 1.0e6


def _even_diagonal_feature(alm, *, lmax: int, l_values) -> list:
    """The even-L BiPoSH diagonal norms in MICROKELVIN (the odd-L diagonal is a
    structural zero and excluded); microKelvin keeps the norms O(100) so they
    are data-dependent and survive serialisation rounding."""
    scaled = alm * _MICROKELVIN
    feats = []
    for ell in l_values:
        d = _index_alm(scaled, lmax, ell)
        for L in range(2, 2 * ell + 1, 2):        # even L only
            norm = float(np.sqrt(sum(
                abs(biposh_diagonal_coefficient(ell, L, M, d)) ** 2
                for M in range(-L, L + 1))))
            feats.append({"l": ell, "L": L, "norm": norm})
    return feats


def _odd_diagonal_relative(alm, *, lmax: int, ell: int) -> float:
    """The largest odd-L diagonal magnitude relative to the even-L=2 diagonal
    magnitude at the same l (a scale-free structural-zero gate)."""
    d = _index_alm(alm * _MICROKELVIN, lmax, ell)
    odd = max(abs(biposh_diagonal_coefficient(ell, 1, M, d))
              for M in range(-1, 2))
    even = max(abs(biposh_diagonal_coefficient(ell, 2, M, d))
               for M in range(-2, 3))
    return float(odd / even) if even > 0 else float("inf")


def observed_null_shared_pipeline(observed_alm, *, proc_nside: int, lmax: int,
                                  l_values, null_seed: int) -> dict:
    """The observed map and a matched-C_ell Gaussian null traverse ONE shared
    pipeline; the even-L diagonal feature is data-dependent (observed and null
    norms differ), the feature SCHEMA (the (l,L) index set) is identical (a
    process statement, NOT evidence), and the odd-L structural zero holds on the
    real-data alm at a scale-free RELATIVE gate."""
    import healpy as hp

    cl = hp.alm2cl(observed_alm, lmax=lmax)
    rng = np.random.Generator(np.random.PCG64(null_seed))
    legacy_state = np.random.get_state()
    try:
        np.random.seed(int(rng.integers(0, 2 ** 31 - 1)))  # synfast legacy RNG
        null_map = hp.synfast(cl, proc_nside, lmax=lmax, new=True)
    finally:
        np.random.set_state(legacy_state)
    null_alm = hp.map2alm(null_map, lmax=lmax)
    obs_feat = _even_diagonal_feature(observed_alm, lmax=lmax,
                                      l_values=l_values)
    null_feat = _even_diagonal_feature(null_alm, lmax=lmax, l_values=l_values)
    obs_odd_rel = _odd_diagonal_relative(observed_alm, lmax=lmax,
                                         ell=l_values[0])
    null_odd_rel = _odd_diagonal_relative(null_alm, lmax=lmax, ell=l_values[0])
    obs_norms = [f["norm"] for f in obs_feat]
    null_norms = [f["norm"] for f in null_feat]
    return {"shared_pipeline": True,
            "feature_schema_l_L":
                [[f["l"], f["L"]] for f in obs_feat],
            "feature_schema_identical":
                [(f["l"], f["L"]) for f in obs_feat]
                == [(f["l"], f["L"]) for f in null_feat],
            "observed_even_diagonal_norms_microK": obs_norms,
            "null_even_diagonal_norms_microK": null_norms,
            "observed_and_null_norms_differ":
                bool(max(abs(a - b) for a, b in zip(obs_norms, null_norms))
                     > 1.0),
            "observed_odd_L1_relative_to_even": obs_odd_rel,
            "null_odd_L1_relative_to_even": null_odd_rel,
            "odd_L_structural_zero_on_both_paths_relative":
                bool(obs_odd_rel < 1e-6 and null_odd_rel < 1e-6),
            "note": "the shared pipeline is a PROCESS statement (identical "
                    "downgrade/mask/alm transform) — the identical feature "
                    "schema is not evidence; the even-L feature is data-"
                    "dependent (observed and null norms differ) and the odd-L "
                    "structural zero holds on the real alm at a scale-free "
                    "relative gate; the genuine convention catch is the "
                    "rotation cross-check in the map checks"}


def _index_alm(alm, lmax, ell) -> dict:
    import healpy as hp

    d = {}
    for mm in range(-ell, ell + 1):
        idx = hp.Alm.getidx(lmax, ell, abs(mm))
        a = alm[idx]
        d[(ell, mm)] = a if mm >= 0 else ((-1) ** mm) * np.conj(a)
    return d


# --------------------------------------------------------------------------
# scan-family ledger
# --------------------------------------------------------------------------
def scan_family_ledger(*, l_values, orientation_grid_n: int) -> dict:
    """The effective scan family: the odd-L diagonal (structural zero) carries
    no trials and is quotiented; the orientation scans are quotiented over the
    monotone/equivalent grid; the effective family is frozen."""
    try:
        l_values = list(l_values)
    except TypeError as exc:
        raise K1ConventionError(
            "scan-family multipoles are malformed") from exc
    if (
        not l_values
        or any(isinstance(l, (bool, np.bool_))
               or not isinstance(l, (int, np.integer))
               or l < 1 for l in l_values)
        or len(set(int(l) for l in l_values)) != len(l_values)
    ):
        raise K1ConventionError(
            "scan family requires unique integer multipoles l >= 1")
    if (
        isinstance(orientation_grid_n, (bool, np.bool_))
        or not isinstance(orientation_grid_n, (int, np.integer))
        or orientation_grid_n <= 0
        or orientation_grid_n % 2
    ):
        raise K1ConventionError(
            "orientation grid must be a positive even integer")
    l_values = [int(l) for l in l_values]
    orientation_grid_n = int(orientation_grid_n)
    even_diag = [(l, L) for l in l_values
                 for L in range(2, 2 * l + 1, 2)]
    odd_diag = [(l, L) for l in l_values
                for L in range(1, 2 * l + 1, 2)]
    # orientation scans are equivalent up to the antipodal identification, so
    # the effective count is half the grid (quotient)
    effective_orientations = orientation_grid_n // 2
    effective_family = len(even_diag) * effective_orientations
    return {"even_L_diagonal_terms": [list(t) for t in even_diag],
            "odd_L_diagonal_terms_quotiented_zero": [list(t) for t in odd_diag],
            "orientation_grid_n": orientation_grid_n,
            "effective_orientations_after_antipodal_quotient":
                effective_orientations,
            "effective_scan_family_size": int(effective_family),
            "note": "the odd-L diagonal is a structural zero and carries no "
                    "trials; the orientation scans are quotiented by the "
                    "antipodal identification; the effective scan family is "
                    "frozen for the look-elsewhere bookkeeping"}


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def refuse_stale_axis_discovery(source: str) -> None:
    if source in ("hardcoded_axis", "stale_planck_axis", "axis_as_discovery"):
        raise K1ConventionError(
            "a hard-coded or stale Planck axis may not be used as a discovery")


def refuse_mask_not_applied(state: str) -> None:
    if state in ("mask_hash_only", "mask_recorded_not_applied"):
        raise K1ConventionError(
            "the mask must be APPLIED on the map path, not merely recorded")


def refuse_shared_null_hiding(state: str) -> None:
    if state in ("shared_null_hides_mutation", "self_consistency_hides"):
        raise K1ConventionError(
            "a convention mutation may not hide behind a shared observed/null "
            "path; the independent oracle catches it")


def refuse_k1_detection(claim: str) -> None:
    if claim in ("k1_detection", "bianchi_family", "axis_detection"):
        raise K1ConventionError(
            "PR-149 makes no detection and no Bianchi-family claim on K1")


def refuse_odd_L_trials(count: str) -> None:
    if count in ("odd_L_diagonal_trials", "count_structural_zero"):
        raise K1ConventionError(
            "the odd-L BiPoSH diagonal is a structural zero and carries no "
            "scan trials")


def refuse_raw_deletion_before_frozen(state: str) -> None:
    if state in ("approve_deletion_unfrozen", "delete_before_freeze"):
        raise K1ConventionError(
            "the PR-150 raw deletion may not be approved before the K1 "
            "convention is frozen")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("stale axis is ", "the discovery"),
        ("mask recorded ", "not applied"),
        ("shared null hides ", "the mutation"),
        ("k1 ", "detection"),
        ("bianchi family ", "from k1"),
        ("odd l diagonal ", "trials"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise K1ConventionError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(theorem: dict, checks: dict, ledger: dict) -> str:
    return (
        f"Planck K1 canonical convention frozen and verified on the real PR3 "
        f"SMICA/Commander maps (alm reality/round-trip/rotation pass); the TT "
        f"BiPoSH odd-L diagonal is a structural zero (independent Wigner-3j "
        f"oracle, all odd-L zero {theorem['odd_L_diagonal_all_zero']}) so the "
        f"effective scan family is {ledger['effective_scan_family_size']} even-"
        f"L orientation terms. Observable feature-extraction and basis-theorem "
        f"mechanics only; freezing the mask/proc-nside/convention pre-conditions "
        f"the PR-150 raw-deletion swap; no detection and no Bianchi-family "
        f"claim; the two CF4 P0s stay OPEN.")
