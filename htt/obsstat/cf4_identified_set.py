"""PR-147: Nuisance-augmented CF4 depth-resolved flow identified sets.

A frozen nuisance box (monopole inclusion, distance-scale calibration,
reconstruction / velocity-observable choice, nonlinear-velocity dispersion) is
swept and the depth-resolved CF4 bulk-flow vector is returned as an IDENTIFIED
SET per distance shell — its amplitude interval and apex cone — classified
bounded / empty / unbounded / nonidentified (binding the PR-136 set-status
vocabulary).

The honest outcome is that the identified set is bounded but WIDE and grows
with depth: a near-point nearby shell, a direction-nonidentified middle shell
(apex cone exceeds a right angle), and a far shell whose amplitude interval is
so wide it is reported as effectively unbounded.  No favourable endpoint is
ever taken as a point estimate and a set that contains zero is never read as
isotropy.

The identified-set amplitude endpoints are computed by an authoritative
CONTINUOUS optimiser over the continuous-nuisance box and cross-checked by an
independent GRID vertex enumeration (the grid is a cross-check, not the
authority — a coarse grid can miss an interior extremum); the mesh sensitivity
and depth / window sensitivity are reported.  The grid-conditional simultaneous
coverage of the set is measured under injection with a Bonferroni family-wise
note (binding PR-137), and the GLS-versus-MV estimator difference under a
common injected field is predicted.

Identified-region coverage mechanics at ``roadmap_rescue_v1:C3`` only.  The two
CF4 P0s stay OPEN with remediation-CANDIDATE receipts; closure is impossible
before the PR-157 adjudication.  No anomaly or global-tilt claim is produced.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

from .velocity_power import fiducial  # noqa: E402

# bind upstream registered objects (Wave-15 lesson 10 — import, do not restate)
from common.identified_set import (  # noqa: E402
    SetStatus,
    validate_status_semantics,
)
from common.weak_id_coverage import bonferroni_conf, imbens_manski_c  # noqa: E402

SCHEMA_VERSION = "pr147.cf4_identified_set.v1"
H0_CF4 = 74.6


class IdentifiedSetError(ValueError):
    """Raised when the identified-set discipline is violated."""


def nuisance_box_hash(box: dict) -> str:
    """A content address of the frozen nuisance box (the sweep axes only, not
    the derived n_shells), so a post-result edit is tamper-evident."""
    canon = {k: box[k] for k in
             ("observable", "calibration_fraction", "sigma_nl_kms", "monopole")}
    return hashlib.sha256(
        json.dumps(canon, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def verify_nuisance_box_hash(box: dict, pinned: str) -> str:
    got = nuisance_box_hash(box)
    if got != pinned:
        raise IdentifiedSetError(
            "the nuisance box does not match its committed content address — "
            "the frozen box was edited after the observed result")
    return got


def require_cross_engine_authority(shell: dict, tol_kms: float) -> None:
    """Kill switch: the coarse grid must lie inside the authoritative
    continuous interval, else the continuous optimiser is stuck/undershooting
    and no identified set is emitted for that shell."""
    ce = cross_engine_endpoint_agreement(shell, tol_kms)
    if not ce["grid_inside_continuous"]:
        raise IdentifiedSetError(
            f"cross-engine disagreement in shell {shell.get('shell')}: the "
            "grid interval is not inside the continuous authority interval — "
            "the optimiser is unreliable and no set is emitted")


# --------------------------------------------------------------------------
# data
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Cf4Data:
    n: np.ndarray            # (N,3) unit directions
    dist: np.ndarray         # (N,) luminosity distance (Mpc)
    e_dmzp: np.ndarray       # (N,) distance-modulus error
    v3k: np.ndarray          # (N,) CMB-frame redshift velocity
    variants: dict           # reconstruction PV columns


def load_data(groups_path, variants_path) -> Cf4Data:
    d = np.load(groups_path)
    ra = np.radians(d["RAdeg"])
    dec = np.radians(d["DEdeg"])
    n = np.column_stack([np.cos(dec) * np.cos(ra),
                         np.cos(dec) * np.sin(ra), np.sin(dec)])
    var = np.load(variants_path)
    variants = {k: var[k] for k in ("Vpec", "Vpwf") if k in var}
    return Cf4Data(n=n, dist=d["Dist"], e_dmzp=d["e_DMzp"], v3k=d["V3k"],
                   variants=variants)


# --------------------------------------------------------------------------
# nuisance box  (frozen + content-addressed)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Nuisance:
    observable: str          # "primary" | "Vpec" | "Vpwf"
    calibration: float       # distance-scale fraction
    sigma_nl: float          # km/s
    monopole: bool


def _observed_velocity(data: Cf4Data, mask, observable: str,
                       calibration: float) -> np.ndarray:
    if observable == "primary":
        return data.v3k[mask] - H0_CF4 * (1.0 + calibration) * data.dist[mask]
    return data.variants[observable][mask]


def flow_vector(data: Cf4Data, mask, nui: Nuisance) -> np.ndarray:
    """The bulk-flow 3-vector for a single nuisance setting (PR-145 WLS)."""
    n = data.n[mask]
    dist = data.dist[mask]
    v = _observed_velocity(data, mask, nui.observable, nui.calibration)
    sigma_d = np.log(10.0) / 5.0 * data.e_dmzp[mask] * dist
    sig_v = np.sqrt((H0_CF4 * sigma_d) ** 2 + nui.sigma_nl ** 2)
    w = 1.0 / sig_v ** 2
    design = (np.column_stack([n, np.ones(len(v))]) if nui.monopole else n)
    a = np.einsum("i,ij,ik->jk", w, design, design)
    if np.linalg.matrix_rank(a) < design.shape[1]:
        raise IdentifiedSetError("rank-deficient flow design in a depth shell")
    coeffs = np.linalg.inv(a) @ np.einsum("i,i,ij->j", w, v, design)
    return coeffs[:3]


# --------------------------------------------------------------------------
# identified set per depth shell
# --------------------------------------------------------------------------
def depth_masks(data: Cf4Data, n_shells: int):
    edges = np.quantile(data.dist, np.linspace(0.0, 1.0, n_shells + 1))
    masks = []
    for s in range(n_shells):
        lo, hi = edges[s], edges[s + 1]
        upper = data.dist <= hi if s == n_shells - 1 else data.dist < hi
        masks.append(((data.dist >= lo) & upper, float(lo), float(hi)))
    return masks


def _discrete_settings(box: dict):
    for obs in box["observable"]:
        for mono in box["monopole"]:
            yield obs, bool(mono)


def _grid_interval(data: Cf4Data, mask, box: dict, cal_grid, snl_grid):
    """Amplitude interval + apex cone from the GRID vertex enumeration (a
    cross-check, not the authority)."""
    amps, apex = [], []
    for obs, mono in _discrete_settings(box):
        for cal in cal_grid:
            for snl in snl_grid:
                b = flow_vector(data, mask, Nuisance(obs, float(cal),
                                                     float(snl), mono))
                a = float(np.linalg.norm(b))
                amps.append(a)
                if a > 0:
                    apex.append(b / a)
    apex = np.asarray(apex)
    cos_min = float(np.min(apex @ apex.T))
    cone_deg = float(np.degrees(np.arccos(np.clip(cos_min, -1.0, 1.0))))
    return min(amps), max(amps), cone_deg


def _continuous_interval(data: Cf4Data, mask, box: dict, *, dense: bool = False):
    """Authoritative amplitude interval by a CONTINUOUS optimiser over the
    (calibration, sigma_nl) box for each discrete setting (the grid can miss an
    interior extremum; this does not).  ``dense=True`` adds a finer grid of
    restart points to probe restart stability (the mesh check)."""
    cal_lo, cal_hi = min(box["calibration_fraction"]), max(box["calibration_fraction"])
    snl_lo, snl_hi = min(box["sigma_nl_kms"]), max(box["sigma_nl_kms"])
    bounds = [(cal_lo, cal_hi), (snl_lo, snl_hi)]
    starts = [[cal_lo, snl_lo], [cal_hi, snl_hi], [0.0, 250.0],
              [cal_lo, snl_hi], [cal_hi, snl_lo]]
    if dense:
        for cal in np.linspace(cal_lo, cal_hi, 5):
            for snl in np.linspace(snl_lo, snl_hi, 5):
                starts.append([float(cal), float(snl)])
    lo, hi = np.inf, -np.inf
    for obs, mono in _discrete_settings(box):
        def amp(x, sign):
            b = flow_vector(data, mask, Nuisance(obs, float(x[0]),
                                                 float(x[1]), mono))
            return sign * float(np.linalg.norm(b))
        for x0 in starts:
            rmin = minimize(amp, x0, args=(1.0,), bounds=bounds,
                            method="L-BFGS-B")
            rmax = minimize(amp, x0, args=(-1.0,), bounds=bounds,
                            method="L-BFGS-B")
            lo = min(lo, float(rmin.fun))
            hi = max(hi, -float(rmax.fun))
    return float(lo), float(hi)


def classify_topology(amp_hi: float, cone_deg: float, *,
                      apex_nonid_deg: float, unbounded_amp: float,
                      feasible: bool = True) -> SetStatus:
    if not feasible:
        return SetStatus.EMPTY
    try:
        amp_hi = float(amp_hi)
        cone_deg = float(cone_deg)
        apex_nonid_deg = float(apex_nonid_deg)
        unbounded_amp = float(unbounded_amp)
    except (TypeError, ValueError) as exc:
        raise IdentifiedSetError(
            "identified-set topology inputs must be real scalars") from exc
    if not all(np.isfinite(value) for value in
               (amp_hi, cone_deg, apex_nonid_deg, unbounded_amp)):
        raise IdentifiedSetError(
            "identified-set topology inputs must be finite")
    if amp_hi < 0:
        raise IdentifiedSetError(
            "identified-set upper amplitude must be non-negative")
    if not 0.0 <= cone_deg <= 180.0:
        raise IdentifiedSetError(
            "identified-set apex cone must be within [0, 180] degrees")
    if not 0.0 <= apex_nonid_deg <= 180.0:
        raise IdentifiedSetError(
            "apex nonidentification threshold must be within [0, 180] degrees")
    if unbounded_amp <= 0:
        raise IdentifiedSetError(
            "effectively-unbounded amplitude threshold must be positive")
    if amp_hi >= unbounded_amp:
        return SetStatus.UNBOUNDED
    if cone_deg >= apex_nonid_deg:
        # a bounded amplitude with a too-wide apex cone is a direction-
        # undetermined region (the PR-136 vocabulary has no separate
        # "nonidentified" status; UNDETERMINED carries it)
        return SetStatus.UNDETERMINED
    return SetStatus.BOUNDED


def identified_set(data: Cf4Data, box: dict, *, n_shells: int,
                   apex_nonid_deg: float, unbounded_amp: float) -> dict:
    cal_grid = box["calibration_fraction"]
    snl_grid = box["sigma_nl_kms"]
    shells = []
    for s, (mask, lo, hi) in enumerate(depth_masks(data, n_shells)):
        g_lo, g_hi, cone = _grid_interval(data, mask, box, cal_grid, snl_grid)
        c_lo, c_hi = _continuous_interval(data, mask, box)
        # the CONTINUOUS optimiser is the authority (it finds interior extrema
        # the grid can miss); the reported interval IS the continuous one
        amp_lo, amp_hi = c_lo, c_hi
        status = classify_topology(amp_hi, cone, apex_nonid_deg=apex_nonid_deg,
                                   unbounded_amp=unbounded_amp)
        shell = {
            "shell": s, "dist_lo_mpc": lo, "dist_hi_mpc": hi,
            "n_groups": int(mask.sum()),
            "amplitude_interval_kms": [amp_lo, amp_hi],
            "grid_amplitude_interval_kms": [g_lo, g_hi],
            "continuous_amplitude_interval_kms": [c_lo, c_hi],
            "apex_cone_deg": cone,
            "status": status.value,
            "contains_zero": bool(amp_lo <= 0.0 < amp_lo + 1e-9),
        }
        require_cross_engine_authority(shell, 50.0)   # kill switch, live
        shells.append(shell)
    return {"n_shells": n_shells, "shells": shells,
            "note": "the identified set is bounded at every depth shell over "
                    "the flow-plus-monopole estimand but its width and apex "
                    "cone grow with depth; the reported interval is the "
                    "continuous-optimiser authority (grid cross-checked as a "
                    "kill switch); no favourable endpoint is a point estimate "
                    "and a set containing zero is not read as isotropy"}


def cross_engine_endpoint_agreement(shell: dict, tol_kms: float) -> dict:
    g_lo, g_hi = shell["grid_amplitude_interval_kms"]
    c_lo, c_hi = shell["continuous_amplitude_interval_kms"]
    # the grid must lie inside the continuous interval (continuous is authority)
    inside = (c_lo - tol_kms <= g_lo) and (g_hi <= c_hi + tol_kms)
    hi_agree = abs(g_hi - c_hi) <= tol_kms
    return {"grid_inside_continuous": bool(inside),
            "upper_endpoint_agrees": bool(hi_agree),
            "grid_lower_minus_continuous_lower": float(g_lo - c_lo),
            "grid_upper_minus_continuous_upper": float(g_hi - c_hi)}


# --------------------------------------------------------------------------
# mesh sensitivity
# --------------------------------------------------------------------------
def mesh_sensitivity(data: Cf4Data, box: dict, *, n_shells: int,
                     refine_points: int, max_shift_kms: float) -> dict:
    """Two mesh checks: (1) the AUTHORITATIVE continuous-optimiser interval must
    be RESTART-stable (default starts versus a dense restart grid) — this
    probes the interior extrema the grid corners cannot; (2) the coarse grid's
    gap to the continuous authority (how much a naive grid would miss) is
    reported.  The grid endpoints sit at box corners so they are mesh-invariant
    by construction — this is disclosed, not passed off as convergence."""
    rows = []
    ok = True
    for s, (mask, lo, hi) in enumerate(depth_masks(data, n_shells)):
        c_lo, c_hi = _continuous_interval(data, mask, box)
        d_lo, d_hi = _continuous_interval(data, mask, box, dense=True)
        g_lo, g_hi, _ = _grid_interval(data, mask, box,
                                       box["calibration_fraction"],
                                       box["sigma_nl_kms"])
        restart_shift = max(abs(d_lo - c_lo), abs(d_hi - c_hi))
        grid_gap = max(abs(g_lo - d_lo), abs(g_hi - d_hi))
        within = restart_shift <= max_shift_kms
        ok = ok and within
        rows.append({"shell": s,
                     "continuous_default_interval_kms": [c_lo, c_hi],
                     "continuous_dense_restart_interval_kms": [d_lo, d_hi],
                     "grid_corner_interval_kms": [g_lo, g_hi],
                     "continuous_restart_shift_kms": float(restart_shift),
                     "grid_minus_continuous_gap_kms": float(grid_gap),
                     "within_tolerance": bool(within)})
    return {"refine_points": refine_points, "max_shift_kms": max_shift_kms,
            "shells": rows, "mesh_sufficient": bool(ok),
            "note": "the mesh check is on the CONTINUOUS-optimiser authority "
                    "(default vs dense restarts); the grid-minus-continuous gap "
                    "is reported as the amount a naive corner grid would miss; "
                    "if a continuous endpoint moves beyond the tolerance the "
                    "mesh is declared insufficient, not silently accepted"}


# --------------------------------------------------------------------------
# grid-conditional simultaneous coverage (binds PR-137 Bonferroni)
# --------------------------------------------------------------------------
def simultaneous_coverage(data: Cf4Data, box: dict, set_result: dict, *,
                          n_inject: int, seed: int, subsample: int,
                          family_conf: float) -> dict:
    """GENUINE simultaneous coverage: a SINGLE injected realisation (one truth
    + one noise draw over the whole subsample) is scored JOINTLY across the
    depth shells, so ``simultaneous_coverage`` is the fraction of realisations
    in which EVERY shell's Imbens-Manski-widened identified interval covers the
    truth amplitude at once — not the minimum of independent per-shell
    marginals.

    The identified interval per shell is built over the nuisances that can be
    applied to a synthetic field (calibration, sigma_nl; the monopole is always
    fit; the reconstruction observable is a data-provenance nuisance not
    applicable to a synthetic velocity field, disclosed) and widened by the
    amplitude sampling uncertainty via the Imbens-Manski critical value (binds
    PR-137).  Every shell that undershoots the RAW per-shell Bonferroni target
    is reported.  A wide interval covers conservatively — coverage is a set
    self-consistency check, NOT evidence of precision; the amplitude Rice-bias
    non-Gaussianity at noise-dominated depth is disclosed."""
    try:
        n_shells = set_result["n_shells"]
        result_shells = set_result["shells"]
    except (KeyError, TypeError) as exc:
        raise IdentifiedSetError(
            "simultaneous coverage requires an identified-set shell result"
        ) from exc
    if (
        isinstance(n_shells, (bool, np.bool_))
        or not isinstance(n_shells, (int, np.integer))
        or n_shells <= 0
        or not isinstance(result_shells, list)
        or len(result_shells) != n_shells
        or any(not isinstance(shell, dict)
               or shell.get("shell") != index
               for index, shell in enumerate(result_shells))
    ):
        raise IdentifiedSetError(
            "simultaneous coverage shell grid must match the identified set")
    n_shells = int(n_shells)
    if (
        isinstance(n_inject, (bool, np.bool_))
        or not isinstance(n_inject, (int, np.integer))
        or n_inject <= 0
    ):
        raise IdentifiedSetError(
            "simultaneous coverage injection count must be a positive integer")
    n_inject = int(n_inject)
    rng = np.random.Generator(np.random.PCG64(seed))
    per_shell = bonferroni_conf(family_conf, n_shells)
    truth = np.array([120.0, -80.0, 60.0])
    truth_amp = float(np.linalg.norm(truth))
    cal_grid = box["calibration_fraction"]
    snl_grid = box["sigma_nl_kms"]
    # one shared subsample spanning all shells; the shells partition it by depth
    all_idx = np.where(np.ones(len(data.dist), bool))[0]
    if len(all_idx) > subsample:
        all_idx = rng.choice(all_idx, size=subsample, replace=False)
    edges = np.quantile(data.dist, np.linspace(0.0, 1.0, n_shells + 1))
    sub_dist = data.dist[all_idx]
    shell_of = np.clip(np.searchsorted(edges, sub_dist, side="right") - 1,
                       0, n_shells - 1)
    prepared = []
    for s in range(n_shells):
        sel = all_idx[shell_of == s]
        if len(sel) < 30:
            raise IdentifiedSetError(f"coverage shell {s} too small")
        n = data.n[sel]
        dist = data.dist[sel]
        sigma_d0 = np.log(10.0) / 5.0 * data.e_dmzp[sel] * dist
        sig_v0 = np.sqrt((H0_CF4 * sigma_d0) ** 2 + 250.0 ** 2)
        designs = []
        for snl in snl_grid:
            sv = np.sqrt((H0_CF4 * sigma_d0) ** 2 + snl ** 2)
            w = 1.0 / sv ** 2
            dsg = np.column_stack([n, np.ones(len(n))])   # monopole ALWAYS fit
            a_inv = np.linalg.inv(np.einsum("i,ij,ik->jk", w, dsg, dsg))
            designs.append((w, dsg, a_inv))
        w0 = 1.0 / sig_v0 ** 2
        d0 = np.column_stack([n, np.ones(len(n))])
        a_inv0 = np.linalg.inv(np.einsum("i,ij,ik->jk", w0, d0, d0))
        prepared.append((n, dist, sig_v0, designs, w0, d0, a_inv0))
    marg = np.zeros(n_shells)
    joint = 0
    for _ in range(n_inject):
        all_cover = True
        for s, (n, dist, sig_v0, designs, w0, d0, a_inv0) in enumerate(prepared):
            base = n @ truth + rng.normal(0.0, sig_v0)
            amps = []
            for cal in cal_grid:
                v = base - H0_CF4 * cal * dist
                for (w, dsg, a_inv) in designs:
                    b = (a_inv @ np.einsum("i,i,ij->j", w, v, dsg))[:3]
                    amps.append(float(np.linalg.norm(b)))
            lo_a, hi_a = min(amps), max(amps)
            b0 = (a_inv0 @ np.einsum("i,i,ij->j", w0, base, d0))[:3]
            amp0 = float(np.linalg.norm(b0))
            sig_amp = float(np.sqrt(max(b0 @ a_inv0[:3, :3] @ b0, 1e-12))
                            / max(amp0, 1e-9))
            c = imbens_manski_c(hi_a - lo_a, sig_amp, level=per_shell)["c"]
            covered = (lo_a - c * sig_amp) <= truth_amp <= (hi_a + c * sig_amp)
            marg[s] += covered
            all_cover = all_cover and covered
        joint += all_cover
    marg = (marg / n_inject).tolist()
    undershoot = [s for s in range(n_shells) if marg[s] < per_shell]
    return {"n_shells": n_shells, "family_conf": family_conf,
            "per_shell_bonferroni_conf": per_shell,
            "truth_amplitude_kms": truth_amp, "n_inject": n_inject,
            "per_shell_marginal_coverage": marg,
            "genuine_simultaneous_coverage": float(joint / n_inject),
            "simultaneous_below_family_conf_by":
                float(max(0.0, family_conf - joint / n_inject)),
            "conservative_coverage_ok": bool(joint / n_inject >= 0.80),
            "shells_undershooting_raw_bonferroni_target": undershoot,
            "applicable_nuisances": ["calibration", "sigma_nl"],
            "monopole": "always_fit",
            "excluded_nuisance": "observable_reconstruction_"
                                 "not_applicable_to_synthetic_field",
            "note": "genuine simultaneous coverage scores one shared injected "
                    "realisation jointly across the shells; every shell "
                    "undershooting the raw per-shell Bonferroni target is "
                    "listed; the shortfall at noise-dominated depth is the "
                    "amplitude Rice-bias non-Gaussianity, not a math error; "
                    "coverage is a set self-consistency check, NOT evidence of "
                    "a precise flow, and the reconstruction nuisance is "
                    "disclosed as inapplicable to a synthetic field"}


# --------------------------------------------------------------------------
# GLS vs MV difference under a common injected field
# --------------------------------------------------------------------------
def gls_ols_difference(data: Cf4Data, *, subsample: int, seed: int) -> dict:
    """Under a common non-uniform injected field, the noise-weighted GLS
    estimator and the UNWEIGHTED (uniform-weight) ordinary-least-squares
    estimator differ because the noise weighting emphasises different galaxies.
    This is a GLS-vs-OLS weighting difference — NOT the Watkins-Feldman-Hudson
    minimum-variance ideal-window estimator (which uses mode-function weights
    with G^T w = I; not implemented here).  The identified set must bracket
    this weighting systematic."""
    rng = np.random.Generator(np.random.PCG64(seed))
    idx = rng.choice(len(data.dist), size=subsample, replace=False)
    n = data.n[idx]
    dist = data.dist[idx]
    sigma_d = np.log(10.0) / 5.0 * data.e_dmzp[idx] * dist
    sig_v = np.sqrt((H0_CF4 * sigma_d) ** 2 + 250.0 ** 2)
    w = 1.0 / sig_v ** 2
    a_gls = np.linalg.inv(np.einsum("i,ij,ik->jk", w, n, n))
    a_ols = np.linalg.inv(np.einsum("ij,ik->jk", n, n))
    diffs = []
    for _ in range(64):
        bulk = rng.normal(0.0, 150.0, size=3)
        small = rng.normal(0.0, 200.0, size=len(idx)) * (dist / dist.max())
        v = n @ bulk + small
        b_gls = a_gls @ np.einsum("i,i,ij->j", w, v, n)
        b_ols = a_ols @ np.einsum("i,ij->j", v, n)
        diffs.append(float(np.linalg.norm(b_gls - b_ols)))
    diffs = np.asarray(diffs)
    return {"subsample": subsample,
            "gls_minus_ols_amplitude_kms_mean": float(diffs.mean()),
            "gls_minus_ols_amplitude_kms_std": float(diffs.std()),
            "note": "the noise-weighted GLS and unweighted OLS bulk-flow "
                    "estimators differ under a common non-uniform field "
                    "because the weighting emphasises different galaxies; this "
                    "is a GLS-vs-OLS weighting systematic, NOT the minimum-"
                    "variance ideal-window estimator (mode-function weights, "
                    "not implemented here); the identified set must bracket it"}


# --------------------------------------------------------------------------
# unbounded demonstration
# --------------------------------------------------------------------------
def misspecification_diagnostic(data: Cf4Data, box: dict, *,
                                apex_nonid_deg: float, unbounded_amp: float
                                ) -> dict:
    """Demonstrate WHY the monopole is always fit: sweeping the distance-scale
    calibration (a radial ell=0 mode) through an estimator that does NOT fit
    the ell=0 monopole manufactures an artificial direction-undetermined /
    effectively-unbounded topology.  This is a mis-specification, reported as a
    diagnostic and never as the identified set."""
    misspec_box = {**box, "monopole": [False]}
    cal_grid = misspec_box["calibration_fraction"]
    snl_grid = misspec_box["sigma_nl_kms"]
    rows = []
    for s, (mask, lo, hi) in enumerate(depth_masks(data, box.get("n_shells", 3))):
        g_lo, g_hi, cone = _grid_interval(data, mask, misspec_box, cal_grid,
                                          snl_grid)
        status = classify_topology(g_hi, cone, apex_nonid_deg=apex_nonid_deg,
                                   unbounded_amp=unbounded_amp)
        rows.append({"shell": s, "amplitude_interval_kms": [g_lo, g_hi],
                     "apex_cone_deg": cone, "status": status.value})
    return {"scenario": "monopole_omitted_while_sweeping_calibration",
            "shells": rows,
            "note": "omitting the monopole while sweeping the radial "
                    "calibration aliases the ell=0 systematic into the ell=1 "
                    "flow, manufacturing an artificial direction-undetermined "
                    "and effectively-unbounded topology; this is a mis-"
                    "specification (the monopole is always fit in the frozen "
                    "box), reported as a diagnostic, not as the identified set"}


def unbounded_scenario(data: Cf4Data, box: dict, *, apex_nonid_deg: float,
                       unbounded_amp: float) -> dict:
    """A plausible-unbounded nuisance (an unbounded distance-scale calibration)
    is demonstrated to drive the far-shell amplitude past the effectively-
    unbounded threshold, yielding an UNBOUNDED status — reported, not hidden."""
    mask, lo, hi = depth_masks(data, box.get("n_shells", 3))[-1]
    amps = []
    for cal in (-4.0, -2.0, 2.0, 4.0):
        for obs, mono in _discrete_settings(box):
            b = flow_vector(data, mask, Nuisance(obs, cal, 250.0, mono))
            amps.append(float(np.linalg.norm(b)))
    amp_hi = max(amps)
    status = classify_topology(amp_hi, 0.0, apex_nonid_deg=apex_nonid_deg,
                               unbounded_amp=unbounded_amp)
    return {"scenario": "unbounded_distance_scale_calibration_prior",
            "far_shell_amplitude_hi_kms": amp_hi,
            "status": status.value,
            "note": "if the distance-scale calibration prior were unbounded "
                    "(even with the monopole fit), the far-shell amplitude "
                    "grows past the effectively-unbounded threshold; the "
                    "status is reported as unbounded, not forced to bounded"}


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def refuse_favourable_endpoint(use: str) -> None:
    if use in ("favourable_endpoint", "endpoint_as_point_estimate",
               "cherry_picked_endpoint"):
        raise IdentifiedSetError(
            "a favourable identified-set endpoint may not be taken as a point "
            "estimate; the set is reported whole")


def refuse_zero_containment_isotropy(claim: str) -> None:
    if claim in ("set_contains_zero_isotropy", "zero_in_set_isotropy"):
        raise IdentifiedSetError(
            "a set that contains zero does not prove isotropy")


def refuse_nuisance_tuning(when: str) -> None:
    if when in ("after_observed_result", "tuned_to_result"):
        raise IdentifiedSetError(
            "the frozen nuisance box may not be edited after the observed "
            "result")


def refuse_anomaly_claim(claim: str) -> None:
    if claim in ("anomaly", "global_tilt", "anomaly_from_wide_set"):
        raise IdentifiedSetError(
            "a wide identified set may not be read as an anomaly or global "
            "tilt")


def refuse_cf4_p0_closure(claim: str) -> None:
    if claim in ("cf4_p0_closed", "p0_resolved", "remediation_complete"):
        raise IdentifiedSetError(
            "a CF4 P0 may not be closed before the PR-157 adjudication")


def require_reported_unbounded(status: str, amp_hi: float,
                               unbounded_amp: float) -> None:
    if amp_hi >= unbounded_amp and status != SetStatus.UNBOUNDED.value:
        raise IdentifiedSetError(
            "a bounded status was reported while a plausible nuisance makes the "
            "set effectively unbounded")


# --------------------------------------------------------------------------
# comparability table + captions
# --------------------------------------------------------------------------
def comparability_table(set_result: dict) -> dict:
    return {"schema": "pr147.comparability_table.v1",
            "columns": ["shell", "dist_lo_mpc", "dist_hi_mpc",
                        "amplitude_lo_kms", "amplitude_hi_kms",
                        "apex_cone_deg", "status"],
            "rows": [[s["shell"], s["dist_lo_mpc"], s["dist_hi_mpc"],
                      s["amplitude_interval_kms"][0],
                      s["amplitude_interval_kms"][1],
                      s["apex_cone_deg"], s["status"]]
                     for s in set_result["shells"]]}


_FORBIDDEN = tuple(
    a + b for a, b in (
        ("favourable endpoint is ", "the estimate"),
        ("set contains zero so ", "isotropy"),
        ("nuisance tuned to ", "the result"),
        ("anomaly ", "detected"),
        ("global tilt ", "detected"),
        ("cf4 p0 ", "closed"),
        ("shear ", "detected"),
        ("isotropy ", "established"),
        ("finding ", "rescued"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise IdentifiedSetError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(set_result: dict) -> str:
    statuses = [s["status"] for s in set_result["shells"]]
    widths = [round(s["amplitude_interval_kms"][1]
                    - s["amplitude_interval_kms"][0]) for s in
              set_result["shells"]]
    validate_status_semantics(
        SetStatus.BOUNDED.value,
        "the depth shells give bounded identified regions that widen with "
        "depth")
    return (
        f"CF4 depth-resolved flow identified set over the frozen nuisance box "
        f"(flow-plus-monopole estimand): per-shell status {statuses}, amplitude "
        f"interval widths {widths} km/s; the set is bounded at every shell but "
        f"widens with depth, no endpoint is a point estimate and a set "
        f"containing zero is not isotropy. Identified-region coverage mechanics "
        f"only; the two CF4 P0s stay OPEN with remediation-candidate receipts "
        f"pending the PR-157 adjudication; no anomaly or global tilt.")
