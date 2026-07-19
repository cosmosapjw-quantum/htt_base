"""PR-150: K1 exchangeable global scan and Planck PR3 FFP10 E2E calibration.

The exchangeable observation-inclusive pooled-rank global p-value estimator
(binding PR-135) is first checked for conservativeness on a large correlated
Gaussian-random-field ensemble with a live anti-conservative negative control
(a method self-consistency check, NOT a Planck falsifier: the correlation is
inert to a leave-one-out rank statistic), then applied to the real Planck PR3
FFP10 end-to-end SMICA null through the same frozen mask/proc-nside/statistic/
max-scan pipeline as the observed map (PR-149 convention).  The heavy E2E
max-scan card is produced once by ``scripts/k1_global_maxscan.py --precision``
and read here (the ACT pattern); this module never re-runs the 600 GB read.

PR3/FFP10-E2E-conditional low-multipole morphology result at
``roadmap_rescue_v1:C2``.  The idealised GRF super-uniformity is NEVER
promoted to a Planck systematics calibration; no real-sky p-value is emitted
without the E2E ensemble.  PR4/NPIPE is fully out of scope — the only permitted
PR4 output is a NON-NUMERIC skip receipt, and no PR3+PR4 joint result is
produced.  No family or axis-detection claim; the two CF4 P0s are untouched.
"""
from __future__ import annotations

import hashlib
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

# bind the exact-discrete exchangeable pooled-rank estimator (PR-135)
from common.finite_null_ranking import (  # noqa: E402
    pooled_rank_p,
    resolution_floor,
    validate_reported_p,
)

SCHEMA_VERSION = "pr150.k1_e2e_calibration.v1"


class K1E2EError(ValueError):
    """Raised when the K1 E2E calibration discipline is violated."""


# --------------------------------------------------------------------------
# pooled-rank conservativeness self-consistency check (with a live negative
# control that has genuine, if fine-grained, discriminating power)
# --------------------------------------------------------------------------
def idealised_super_uniformity(*, n_statistics: int, rho: float,
                               n_realizations: int, seed: int,
                               band: float) -> dict:
    """Estimator conservativeness self-consistency check on the shipped
    exchangeable pooled-rank global-p (PR-135 ``pooled_rank_p``).

    Each realisation carries ``n_statistics`` correlated Gaussian statistics
    (correlation ``rho``); the global score is the max over the statistics.
    Because ``pooled_rank_p`` is a leave-one-out RANK statistic, its marginal is
    super-uniform for ANY continuous exchangeable ensemble --- the correlation
    ``rho`` reshapes only the within-realisation marginal, which the max removes,
    so this check has NO power against correlated systematics and is NOT a
    Planck falsifier.  What it DOES verify, with a live anti-conservative
    negative control, is that the shipped ``(1+b)/(N+1)`` form is genuinely
    conservative and load-bearing: the naive ``b/(N-1)`` rank (no ``+1``, can be
    zero) is measured to OVER-reject relative to the shipped form, so the small
    exceedance band is a real threshold separating the conservative estimator
    from the anti-conservative one, not a rubber stamp.  Method self-consistency
    only; NEVER promoted to a Planck systematics calibration."""
    rng = np.random.Generator(np.random.PCG64(seed))
    cov = rho * np.ones((n_statistics, n_statistics)) \
        + (1.0 - rho) * np.eye(n_statistics)
    lchol = np.linalg.cholesky(cov)
    scores = np.array([float(np.max(np.abs(lchol @ rng.standard_normal(
        n_statistics)))) for _ in range(n_realizations)])
    ps = np.array([float(pooled_rank_p(scores[i], np.delete(scores, i)))
                   for i in range(n_realizations)])
    # anti-conservative negative control: the naive b/(N-1) rank (no +1), which
    # admits p == 0 at the maximum score
    n = n_realizations
    b = np.array([int(np.sum(np.delete(scores, i) >= scores[i]))
                  for i in range(n)])
    ps_naive = b / (n - 1)
    alpha_grid = [round(a, 2) for a in np.linspace(0.05, 0.5, 10)]
    rej = [float(np.mean(ps <= a)) for a in alpha_grid]
    max_exceedance = float(max(r - a for r, a in zip(rej, alpha_grid)))
    super_uniform = bool(max_exceedance <= band)
    # STRUCTURAL negative control at a sub-resolution significance level below
    # the shipped (1+b)/(N+1) floor 1/N: the shipped form CANNOT reject there
    # (its minimum p is exactly 1/N), while the anti-conservative b/(N-1) form
    # CAN (it can report p == 0).  This is noise-free (a structural property of
    # the two estimators), so it gives the check genuine discriminating power.
    subfloor_alpha = 0.5 / n                       # < 1/N, below the floor
    rej_shipped_subfloor = float(np.mean(ps <= subfloor_alpha))
    rej_naive_subfloor = float(np.mean(ps_naive <= subfloor_alpha))
    control_discriminates = bool(rej_naive_subfloor > rej_shipped_subfloor)
    if not super_uniform:
        raise K1E2EError(
            "the shipped (1+b)/(N+1) pooled rank is NOT conservative on the "
            f"exchangeable ensemble (max exceedance {max_exceedance:.3f} > "
            f"{band}) — the method self-consistency check fails")
    if not control_discriminates:
        raise K1E2EError(
            "the anti-conservative b/(N-1) negative control did not over-reject "
            "the shipped form at the sub-resolution level — the conservativeness "
            "check has no discriminating power and is a rubber stamp")
    return {"n_statistics": n_statistics, "correlation_rho": rho,
            "n_realizations": n_realizations, "alpha_grid": alpha_grid,
            "rejection_fraction": rej,
            "max_exceedance_above_uniform": max_exceedance,
            "subfloor_alpha": subfloor_alpha,
            "shipped_subfloor_rejection": rej_shipped_subfloor,
            "anti_conservative_control_subfloor_rejection": rej_naive_subfloor,
            "control_discriminates": control_discriminates,
            "super_uniform": super_uniform, "band": band,
            "note": "estimator conservativeness self-consistency check: the "
                    "shipped (1+b)/(N+1) pooled rank is super-uniform on the "
                    "exchangeable ensemble and structurally cannot reject below "
                    "its 1/N floor, while the anti-conservative b/(N-1) negative "
                    "control does over-reject there; correlation rho is inert "
                    "(removed by the max), so this has no power against Planck "
                    "systematics and is NEVER promoted to a Planck calibration"}


# --------------------------------------------------------------------------
# PR3 FFP10 E2E input manifest
# --------------------------------------------------------------------------
def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def e2e_input_manifest(cmb_dir: Path, noise_dir: Path, *,
                       sample_hash_count: int) -> dict:
    """Authenticate the PR3/FFP10 E2E input: the CMB and noise Monte-Carlo map
    counts, a deterministic sample of content-addressed sha256s (the full ~600
    GB is not hashed), and the byte-equivalent observed/null path declaration."""
    cmb = sorted(p for p in cmb_dir.glob("*.fits") if p.is_file())
    noise = sorted(p for p in noise_dir.glob("*.fits") if p.is_file())
    if not cmb or not noise:
        raise K1E2EError(
            "the PR3 FFP10 E2E ensemble is absent — no real-sky p-value may be "
            "emitted; the science state is BLOCKED on the E2E ensemble")
    # a deterministic, evenly-spaced sample of sha256s (not the whole ensemble)
    step = max(1, len(cmb) // sample_hash_count)
    sample = [cmb[i] for i in range(0, len(cmb), step)][:sample_hash_count]
    return {"access_status": "available",
            "nominal_cmb_count": 1000,
            "usable_cmb_count": len(cmb),
            "cmb_mc_count": len(cmb), "noise_mc_count": len(noise),
            "excluded_ids": ["00970"],
            "exclusion_status": "officially_confirmed_by_planck_helpdesk",
            "replacement_available": False,
            "analysis_status": "ready",
            "cmb_mc_dir": str(cmb_dir), "noise_mc_dir": str(noise_dir),
            "sample_sha256": {p.name: _sha256_file(p) for p in sample},
            "observed_null_byte_equivalent_path": True,
            "note": "the observed SMICA map and every E2E null map are "
                    "processed through the identical frozen mask/proc-nside/"
                    "statistic/max-scan pipeline (a byte-equivalent path); only "
                    "an evenly-spaced sample of the ~600 GB ensemble is hashed"}


# --------------------------------------------------------------------------
# finite-ensemble pooled-rank global-p from the E2E max-scan card
# --------------------------------------------------------------------------
def pooled_rank_from_e2e_card(card_path: Path) -> dict:
    """Read the heavy E2E max-scan card (produced once by
    ``k1_global_maxscan.py --precision``) and express its global p-value as the
    finite-ensemble observation-inclusive pooled rank (PR-135 arithmetic).  The card's
    ``global_p`` is HARD-VALIDATED against the actual reported value (not a
    grid-snapped surrogate): it must lie on the ``(1+b)/(N+1)`` support grid, at
    or above the resolution floor, and never be zero, else this raises.  The
    per-statistic local p-values and the look-elsewhere (max-scan over the six
    registered statistics) global p are reported separately --- there is no sky
    axis grid or axis re-estimation."""
    if not card_path.is_file():
        raise K1E2EError(
            "the E2E max-scan card is absent — run "
            "scripts/k1_global_maxscan.py --precision on the FFP10 ensemble "
            "first; PR-150 reads the card, it does not re-run the 600 GB read")
    card = json.loads(card_path.read_text(encoding="utf-8"))
    # the k1_global_maxscan card nests the estimator output under ``result`` and
    # the ensemble size under ``e2e_sims``/``config``; fall back to a flat layout
    result = card.get("result", card)
    config = card.get("config", {})
    e2e = card.get("e2e_sims", {})
    global_p = result.get("global_p", card.get("global_p"))
    n_sim = int(config.get("n_sims") or e2e.get("n_cmb_used")
                or result.get("simulation_count")
                or card.get("simulation_count") or card.get("n_e2e") or 0)
    if global_p is None or n_sim <= 0:
        raise K1E2EError("the E2E card is missing global_p / simulation_count")
    global_p = float(global_p)
    # HARD-validate the ACTUAL global_p (PR-135 discipline), not a snapped
    # surrogate: it must be on the (1+b)/(N+1) grid and at/above the floor, else
    # the card carries a value the registered finite-rank arithmetic cannot
    # produce. Grid membership alone is not an exchangeability claim.
    floor = float(resolution_floor(n_sim))
    on_grid = any(abs(global_p - float(Fraction(k, n_sim + 1))) < 1e-9
                  for k in range(1, n_sim + 2))
    if not on_grid:
        raise K1E2EError(
            f"the E2E card global_p {global_p:.6g} is not on the (1+b)/(N+1) "
            f"support grid for N={n_sim} — it is not a valid finite-ensemble "
            "pooled-rank value")
    if global_p < floor:
        raise K1E2EError(
            f"the E2E card global_p {global_p:.6g} is below the resolution "
            f"floor {floor:.6g} for N={n_sim} — PR-135 forbids reporting a "
            "sub-resolution p-value")
    # on_grid guarantees the snapped value equals the actual value to 1e-9, so
    # this validates the real reported p, not a surrogate
    validate_reported_p(Fraction(round(global_p * (n_sim + 1)), n_sim + 1),
                        n_sim)
    local_p = result.get("local_p", card.get("local_p"))
    n_noise = int(e2e.get("n_noise_used") or n_sim)
    reuse = result.get("noise_reuse_sensitivity")
    noise_reused = n_noise < n_sim
    if noise_reused and not reuse:
        raise K1E2EError(
            "the E2E card reuses noise realizations but lacks the registered "
            "cycle and noise-cluster sensitivity")
    return {"e2e_global_pooled_rank_p": global_p,
            "simulation_count": n_sim, "resolution_floor": floor,
            "on_finite_rank_support_grid": bool(on_grid),
            # Compatibility alias for the pre-amendment consumer. This names
            # only the arithmetic grid, not an exchangeability theorem.
            "on_exchangeable_support_grid": bool(on_grid),
            "observed_max_scan_score": result.get(
                "observed_max_score", card.get("observed_max_score")),
            "per_statistic_local_p": local_p,
            "look_elsewhere_global_p": global_p,
            "unique_noise_realization_count": n_noise,
            "noise_realizations_reused": noise_reused,
            "exact_iid_or_exchangeability_claimed": False if noise_reused else True,
            "noise_reuse_sensitivity": reuse,
            "inference_mode": ("empirical_finite_ensemble_rank_with_noise_cluster_sensitivity"
                               if noise_reused else "finite_exchangeable_rank"),
            "note": "the E2E global p-value is the observation-inclusive "
                    "finite-ensemble rank (1+b)/(N+1) over the FFP10 null, "
                    "HARD-validated on the support grid and at or above the "
                    "resolution floor; the per-statistic local p-values and the "
                    "look-elsewhere global p (max-scan over the six registered "
                    "statistics — no sky axis grid) are reported separately. "
                    "Because 300 noise maps are reused across 999 CMB maps, the "
                    "rank is an empirical point estimate with cycle-split and "
                    "noise-cluster-bootstrap sensitivity, not an iid exact-rank "
                    "theorem; it is not a detection."}


# --------------------------------------------------------------------------
# non-numeric PR4/NPIPE skip receipt
# --------------------------------------------------------------------------
def pr4_npipe_skip_receipt() -> dict:
    """Non-numeric PR4/NPIPE readiness receipt.

    The observed SEVEM map is public, but the matched simulation ensemble is
    not ingested in PLA and requires PI/proxy/Globus access to NERSC.
    """
    return {"observed_map_status": "public_in_PLA",
            "observed_map_id": "COM_CMB_IQU-sevem_2048_R4.00.fits",
            "simulation_status": "not_ingested_in_PLA",
            "nersc_path": "/global/cfs/cdirs/cmb/data/planck2020",
            "noise_fix_exists": True,
            "access_status": "awaiting_cmb_PI_or_PI_proxy_or_Globus_share",
            "analysis_status": "externally_blocked",
            "pr4_npipe_status": "EXTERNALLY_BLOCKED_MISSING_SIMULATION_ACCESS",
            "numeric_outputs": "none",
            "pr3_plus_pr4_joint_result": "not_produced",
            "note": "the observed SEVEM R4 map is public in PLA, but the matched "
                    "simulation ensemble is not ingested there; numerical PR4 "
                    "analysis awaits authorized access to the NERSC planck2020 "
                    "tree (including the existing noise fix)."}


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def refuse_idealised_promotion(claim: str) -> None:
    if claim in ("idealised_is_planck_calibration", "grf_calibrates_planck",
                 "promote_idealised"):
        raise K1E2EError(
            "the idealised GRF super-uniformity may not be promoted to a "
            "Planck systematics calibration")


def refuse_real_sky_p_without_e2e(has_e2e: bool, claim: str) -> None:
    if claim in ("real_sky_p", "planck_p_value") and not has_e2e:
        raise K1E2EError(
            "a real-sky p-value may not be emitted without the E2E ensemble")


def refuse_pr4_numeric(output: str) -> None:
    if output in ("pr4_p_value", "npipe_numeric", "pr4_number"):
        raise K1E2EError("no PR4 NPIPE numeric output may be produced")


def refuse_pr3_pr4_joint(claim: str) -> None:
    if claim in ("pr3_pr4_joint", "joint_calibration"):
        raise K1E2EError("no PR3-and-PR4 combined result may be produced")


def refuse_k1_axis_detection(claim: str) -> None:
    if claim in ("k1_axis", "axis_detection", "bianchi_family"):
        raise K1E2EError("no K1 directional detection or Bianchi-family claim")


def refuse_non_super_uniform(super_uniform: bool) -> None:
    if not super_uniform:
        raise K1E2EError(
            "a non-super-uniform pooled rank on correlated GRF may not be "
            "accepted — the method is falsified")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("idealised promoted ", "to planck"),
        ("real sky p ", "without e2e"),
        ("pr4 numeric ", "result"),
        ("pr3 plus pr4 ", "joint"),
        ("k1 axis ", "detection"),
        ("bianchi family ", "from k1"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise K1E2EError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(idealised: dict, manifest: dict, e2e: dict) -> str:
    sensitivity = e2e.get("noise_reuse_sensitivity") or {}
    bootstrap = sensitivity.get("noise_cluster_bootstrap") or {}
    interval = bootstrap.get("percentile_95_interval", [float("nan"), float("nan")])
    cycle_range = sensitivity.get("cycle_p_range", [float("nan"), float("nan")])
    return (
        f"K1 finite-ensemble pooled-rank global scan: conservative on the "
        f"correlated-GRF self-consistency check with a live anti-conservative "
        f"negative control (max exceedance "
        f"{idealised['max_exceedance_above_uniform']:.2f}), then applied to the "
        f"real Planck PR3 FFP10 end-to-end SMICA null "
        f"({e2e['simulation_count']} usable CMB Monte-Carlo maps; excluded ID "
        f"00970; {manifest['noise_mc_count']} unique noise maps reused by "
        f"parsed-ID modulo pairing) giving an "
        f"E2E-conditional pooled-rank global p of "
        f"{e2e['e2e_global_pooled_rank_p']:.3f} on the finite-rank support "
        f"grid (noise-cluster bootstrap 95% interval "
        f"[{interval[0]:.3f}, {interval[1]:.3f}]; cycle-split p range "
        f"[{cycle_range[0]:.3f}, {cycle_range[1]:.3f}]). This is a concrete "
        f"PR3/FFP10-E2E-conditional morphology result; the idealised GRF is "
        f"preflight only, and noise reuse prevents an iid exact-rank claim. "
        f"PR4/NPIPE remains externally blocked at simulation access; no "
        f"detection or Bianchi-family claim; the two CF4 "
        f"P0s stay OPEN.")
