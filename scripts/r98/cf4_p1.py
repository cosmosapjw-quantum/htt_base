"""CF4 joint log-distance tomography and shared one-coordinate finite-law calibration sweeps."""
from __future__ import annotations

import json
import math
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.linalg import block_diag, solve_triangular
from scipy.stats import chi2

from scripts.r95 import sq_cf4_synthesis as r95
from scripts.r97 import cf4_genealogy_and_partial_id as r97

ROOT = r95.ROOT
PUB = ROOT / "docs/research_program/observational_publication_20261015"
P1 = PUB / "CONTINUATION_20261018/P1"
R97 = PUB / "R97_SCIENCE_EXECUTION_20261122"
R30_DIR = PUB / "EXTERNAL_AUDIT_20261025_R35/CF4_FINITE_COMPONENT/sources/r30_cf4_pv_tensor_numeric/fast_window_fixture_repair"
BRIDGE_DIR = PUB / "OBSERVABLE_BRIDGE_RECONCILIATION_20261027/covariance"
R36_CORR_DIR = Path("/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual")
TARGET_INV = R36_CORR_DIR / "TARGET_INVENTORY.npz"
OUT = PUB / "R98_FOURTH_RESEARCH_CYCLE_20261123/CF4_P1_RESULTS.json"
MAG = np.log(10.) / 5.
C = 299792.458
HREF = 74.6
METHODS = ["SNIa", "FP", "TFR", "SBFm", "SBFir", "SNII", "DirectCal"]
EVENTS = ["z025", "z040", "z060", "z080", "any", "all"]


def _load_r30_and_bridge():
    for d in (str(R30_DIR), str(BRIDGE_DIR), str(R36_CORR_DIR / "deps")):
        if d not in sys.path:
            sys.path.insert(0, d)
    import science as r30_sci  # noqa: PLC0415
    from covariance_bridge import gls_svd, transport_covariance  # noqa: PLC0415
    import finufft  # noqa: PLC0415
    return r30_sci, gls_svd, transport_covariance, finufft


def json_default(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    raise TypeError(type(x).__name__)


def magnitude_weights(t3):
    prec = t3["e_vals_6"] ** -2
    total = prec.sum(axis=1, keepdims=True)
    fractions = np.divide(prec, total, out=np.zeros_like(prec), where=total > 0)
    only = total[:, 0] == 0
    if not np.array_equal(only, t3["dmav"] == 0) or not np.isfinite(t3["cal_vals"][only]).all():
        raise ValueError("unsupported group or DirectCal genealogy mismatch")
    return np.column_stack((fractions, only))


def catalog():
    raw = r97.RAW_CF4
    spans = [(0, 7), (8, 14), (15, 20), (39, 44), (45, 50), (51, 57),
             (58, 63), (64, 69), (83, 91), (92, 100), (33, 38)]
    rows = [[float(line[a:b]) for a, b in spans] for line in
            (raw / "table4.dat").read_text(encoding="ascii").splitlines() if line.strip()]
    ids, mu, emu, cz, v, ds, wf, ramp, ra, dec, vls = np.array(rows).T
    ids = ids.astype(np.int64)
    if len(ids) != 38053 or len(np.unique(ids)) != len(ids):
        raise ValueError("full release identity")
    ids3 = [int(line[:7]) for line in (raw / "table3.dat").read_text().splitlines() if line.strip()]
    if set(ids3) != set(ids) or len(ids3) != len(ids):
        raise ValueError("table3/table4 group keys")
    ra, dec = np.deg2rad(ra), np.deg2rad(dec)
    n = np.column_stack((np.cos(ra)*np.cos(dec), np.sin(ra)*np.cos(dec), np.sin(dec)))
    return ids, mu, emu, cz, v, ds, wf, ramp, n, vls


def log_sigma(v, emu):
    if np.any(v <= 0) or np.any(emu <= 0):
        raise ValueError("positive corrected velocity and modulus uncertainty required")
    return np.hypot(MAG * emu, 250. * (1. + v/C) / v)


def tomography(H, n, cz, v, mu, emu):
    X = H.velocity_design(np.ones(len(cz)), n)
    y = np.log(v / HREF) - MAG*(mu - 25.)
    sigma = log_sigma(v, emu)
    fits = [H.fit(X, y, H.window(cz/C, sigma, center), influence=True) for center in H.CENTERS]
    A = np.vstack([f["A"] for f in fits])
    cov, _ = H.joint_covariance(A, sigma)
    return X, y, sigma, A, cov, (A @ y).reshape(4, 9)


def support_width(T, cov5, r, common_mag, direct_mag):
    """Sharp component support of box × ellipsoid × box, no ridge."""
    T = np.asarray(T)
    E = T[:, 1:6]
    rel = r * np.sqrt(np.maximum(0., np.einsum("ij,jk,ik->i", E, cov5, E)))
    return common_mag*np.abs(T.sum(axis=1)) + rel + direct_mag*np.abs(T[:, 6])


def _exact_finite_slice(q, vec_q, d, vec_den, radius, w, threshold):
    """Sweep exact algebraic roots of the quadratics on the serialized binary inputs."""
    from fractions import Fraction
    import sympy as sp

    def rational(x):
        return Fraction(*x.as_integer_ratio())

    scale, tau = rational(radius), rational(threshold)
    events = {}
    at_left = np.empty(d.shape, dtype=bool)
    at_zero = np.empty_like(at_left)
    for j in range(4):
        v = [scale*rational(x) for x in vec_q[j]]
        h = scale*rational(vec_den[j])
        a = sum(t*t for t in v) - (tau*h)**2
        for i in range(len(q)):
            qi = [rational(x) for x in q[i,j]]
            den = rational(d[i,j])
            b = 2*(sum(t*z for t,z in zip(qi,v)) - tau**2*den*h)
            c = sum(t*t for t in qi) - (tau*den)**2
            at_left[i,j], at_zero[i,j] = a-b+c > 0, c > 0
            roots = []
            if a == 0:
                if b != 0:
                    roots = [(sp.Rational(-c/b), b > 0)]
            else:
                disc = b*b-4*a*c
                if disc == 0:
                    roots = [(sp.Rational(-b/(2*a)), a > 0)]
                elif disc > 0:
                    # Monic coordinates canonicalize common roots of proportional quadratics.
                    center = sp.Rational(-b/(2*a))
                    half = sp.sqrt(sp.Rational(disc/(4*a*a)))
                    roots = [(center-half,a < 0),(center+half,a > 0)]
            for root, right_value in roots:
                if -1 <= root <= 1:
                    events.setdefault(root,[]).append((i,j,right_value))

    def masses(flags):
        return w @ np.column_stack((flags,flags.any(axis=1),flags.all(axis=1)))

    nominal = masses(at_zero)
    lows, highs = nominal.copy(), nominal.copy()
    low_at, high_at = np.zeros(6), np.zeros(6)

    def observe(flags, coordinate):
        mass = masses(flags)
        lower, higher = mass < lows, mass > highs
        if lower.any() or higher.any():
            witness = float(coordinate*scale)
            low_at[lower], high_at[higher] = witness, witness
            lows[lower], highs[higher] = mass[lower], mass[higher]

    left, right = sp.Integer(-1), sp.Integer(1)
    points = sorted(set(events) | {left,right})
    state = at_left.copy()
    for k,coordinate in enumerate(points):
        affected = events.get(coordinate,())
        for i,j,_ in affected:
            state[i,j] = False  # strict inequality at a root, including coincident roots
        observe(state,coordinate)
        if k+1 < len(points):
            for i,j,right_value in affected:
                state[i,j] = right_value
            observe(state,(coordinate+points[k+1])/2)
    return dict(radius=radius,threshold=threshold,events=EVENTS,nominal=nominal,
                min_mass=lows,max_mass=highs,min_at=low_at,max_at=high_at,
                n_distinct_interior_roots=len(points)-2,n_intervals=len(points)-1,
                method="exact binary-rational coefficients and ordered real algebraic root events")


def finite_slice(draw_q, vec_q, denom, vec_den, radius, weights, threshold):
    """Enumerate all strict quadratic events, endpoints and open cells for a single shared offset.

    Ordinary events use extended precision. Ill-conditioned polynomials or unresolved root
    separations switch to exact binary-rational coefficients and real algebraic roots.
    Output witnesses use the same offset for all draws and four windows.
    """
    q = np.asarray(draw_q, dtype=np.longdouble)
    d = np.asarray(denom, dtype=np.longdouble)
    v = np.asarray(vec_q, dtype=np.longdouble) * radius
    h = np.asarray(vec_den, dtype=np.longdouble) * radius
    w = np.asarray(weights, dtype=float)
    tau = np.longdouble(threshold)
    if (q.ndim != 3 or q.shape[1] != 4 or d.shape != q.shape[:2] or v.shape != q.shape[1:]
            or h.shape != (4,) or w.shape != (len(q),) or radius < 0 or threshold <= 0
            or any(not np.isfinite(e).all() for e in (q,d,v,h,w)) or np.any(w < 0)
            or not np.isclose(w.sum(), 1., rtol=0, atol=1e-12) or np.min(d-np.abs(h)) <= 0):
        raise ValueError("invalid paired finite-law or denominator domain")
    a = np.broadcast_to((v*v).sum(axis=1) - tau*tau*h*h, d.shape)
    b = 2*((q*v).sum(axis=2) - tau*tau*d*h)
    c = (q*q).sum(axis=2) - tau*tau*d*d
    # At a cancellation even binary80 can silently turn a positive squared term into zero.
    # The magnitude bound includes all terms of the preceding dot products, not just
    # the magnitude of the rounded coefficients. Rebuild from original binary inputs.
    guard = 128*np.finfo(np.longdouble).eps*max(1,q.shape[-1])
    def near(value, magnitude):
        return (magnitude > 0) & (np.abs(value) <= guard*magnitude)
    def exact():
        return _exact_finite_slice(q,np.asarray(vec_q,dtype=np.longdouble),d,
                                   np.asarray(vec_den,dtype=np.longdouble),radius,w,threshold)
    mag_a = (v*v).sum(axis=1)+(tau*h)**2
    mag_b = 2*(np.abs(q*v).sum(axis=2)+np.abs(tau*tau*d*h))
    mag_c = (q*q).sum(axis=2)+(tau*d)**2
    disc = b*b-4*a*c
    # Include accumulated uncertainty in a,b,c even when a or b is small.
    mag_disc = 2*np.abs(b)*mag_b + 4*(np.abs(a)*mag_c+np.abs(c)*mag_a)
    if (near(a,mag_a).any() or near(b,mag_b).any() or near(c,mag_c).any()
            or ((a!=0)&near(disc,mag_disc)).any()):
        return exact()
    r1 = np.full_like(d, np.inf)
    r2 = np.full_like(d, np.inf)
    linear = (a == 0) & (b != 0)
    r1[linear] = -c[linear] / b[linear]
    disc = b*b - 4*a*c
    tangent = (a != 0) & (disc == 0)
    r1[tangent] = -b[tangent] / (2*a[tangent])
    two = (a != 0) & (disc > 0)
    u = -.5*(b[two] + np.copysign(np.sqrt(disc[two]), b[two]))
    r1[two], r2[two] = u/a[two], c[two]/u
    roots = np.r_[r1.ravel(), r2.ravel()]
    # Preserve ordering and strict root coincidences when distinct algebraic roots may
    # round to the same number. Near endpoint/zero cases also get exact classification.
    finite = roots[np.isfinite(roots)]
    relevant = finite[(finite >= -1.-guard) & (finite <= 1.+guard)]
    boundaries = np.sort(np.r_[np.longdouble([-1.,0.,1.]),relevant])
    if np.any(np.diff(boundaries) <= guard):
        return exact()
    interior = np.unique(roots[(roots > -1.) & (roots < 1.)])
    points = np.r_[np.longdouble(-1.), interior, np.longdouble(1.)]
    sweep = np.sort(np.r_[points, .5*(points[1:]+points[:-1])])
    lows, highs = np.full(6, 2.), np.full(6, -1.)
    lo_at, hi_at = np.zeros(6), np.zeros(6)
    lower_root, upper_root = np.minimum(r1,r2), np.maximum(r1,r2)
    constant = (a==0)&(b==0)
    nominal = None
    for s in np.r_[np.longdouble(0.), sweep]:
        # Classify by root order to avoid a second nearly cancelling polynomial evaluation.
        yes = (a > 0).copy()
        yes[two] = np.where(a[two] > 0,
                            (s < lower_root[two]) | (s > upper_root[two]),
                            (s > lower_root[two]) & (s < upper_root[two]))
        yes[linear] = np.where(b[linear] > 0,s > r1[linear],s < r1[linear])
        yes[constant] = c[constant] > 0
        yes[tangent] = (a[tangent] > 0) & (s != r1[tangent])
        flags = np.column_stack((yes, yes.any(axis=1), yes.all(axis=1)))
        totals = w @ flags
        if nominal is None:
            nominal = totals.copy()
        lo_at[totals < lows], hi_at[totals > highs] = float(s*radius), float(s*radius)
        lows, highs = np.minimum(lows, totals), np.maximum(highs, totals)
    return dict(radius=radius, threshold=threshold, events=EVENTS, nominal=nominal,
                min_mass=lows, max_mass=highs, min_at=lo_at, max_at=hi_at,
                n_distinct_interior_roots=len(interior), n_intervals=len(points)-1,
                method="guarded extended-precision roots and open intervals; rational fallback when ill-conditioned")


def summaries(x):
    return dict(n=len(x), mean=float(np.mean(x)), median=float(np.median(x)),
                rms=float(np.sqrt(np.mean(np.square(x)))), q05_q95=np.quantile(x, [.05,.95]))


def prediction_cv(H, n, cz, v, mu, emu):
    """Every selected group held out once, all models scored on identical modulus/error target."""
    X = H.velocity_design(np.ones(len(mu)), n)
    d = H.proxy_distance(mu)
    sig_v, sig_l = H.working_sigma(d, emu), log_sigma(v, emu)
    kernels = np.exp(-.5*((cz[:, None]/C-np.array(H.CENTERS))/H.WIDTH)**2)
    blend = kernels / kernels.sum(axis=1)[:, None]
    octant = (n >= 0).astype(int) @ np.array([1,2,4])
    report = {}
    for model in ["velocity_cz", "velocity_fV", "log_cz", "log_fV"]:
        vel = cz if model.endswith("cz") else v
        islog = model.startswith("log")
        features = X if islog else X*d[:, None]
        y = np.log(vel/HREF)-MAG*(mu-25.) if islog else vel
        sigma = sig_l if islog else sig_v
        pred_mu = np.full(len(mu), np.nan)
        octants = []
        for k in range(8):
            tr = octant != k
            te = ~tr
            theta = np.stack([H.fit(features[tr], y[tr], (kernels[:,j]/sigma**2)[tr],
                                     influence=False)["theta"] for j in range(4)])
            field = X[te] @ theta.T
            if not islog and np.any(field <= 0):
                raise ValueError("nonpositive predicted angular H")
            logh = field if islog else np.log(field/HREF)
            pred_mu[te] = 25. + (np.log(vel[te]/HREF) - (blend[te]*logh).sum(axis=1))/MAG
            error = (mu[te]-pred_mu[te])*MAG/sig_l[te]
            octants.append(dict(octant=k, n=int(te.sum()), mean_standardized_square=np.mean(error**2)))
        if not np.isfinite(pred_mu).all():
            raise ValueError("holdout coverage")
        standardized = (mu-pred_mu)*MAG/sig_l
        report[model] = dict(rms_mag=np.sqrt(np.mean((mu-pred_mu)**2)),
                             mean_standardized_square=np.mean(standardized**2),
                             mean_gaussian_nll_mag=np.mean(.5*standardized**2+np.log(sig_l/MAG*np.sqrt(2*np.pi))),
                             octants=octants)
    return report

def upstream_anchor_genealogy(raw2, ids, sel, positive, cz, t3, Wfull):
    """D01: Cross-tabulate all 55,877 table2 galaxies and anchors against 38,053/35,970 groups."""
    gid_to_idx = {int(g): i for i, g in enumerate(ids)}
    spans = [(41, 47), (53, 59), (65, 71), (77, 83), (90, 96), (102, 107), (113, 119), (126, 131)]
    gal_names = ["SNIa", "TF", "FP", "SBF", "SNII", "TRGB", "Cepheid", "maser"]
    gal_pres = np.array([[bool(row[a:b].strip()) for a, b in spans] for row in raw2], dtype=bool)
    gal_gidx = np.fromiter((gid_to_idx.get(int(row[8:15]), -1) for row in raw2), dtype=np.int64, count=len(raw2))
    mapped = gal_gidx >= 0
    unmapped = ~mapped
    unmapped_1pgc = sorted({int(row[8:15]) for row, um in zip(raw2, unmapped) if um})
    unmapped_counts = {k: int(c) for k, c in zip(gal_names, gal_pres[unmapped].sum(axis=0))}
    grp_has_gal_anchor = np.zeros((len(ids), 3), dtype=bool)  # TRGB, Cepheid, maser
    for k in range(3):
        np.logical_or.at(grp_has_gal_anchor[:, k], gal_gidx[mapped], gal_pres[mapped, 5 + k])

    t3_pres = t3["dm_present_7"]  # order: ["CAL", "SNIA", "FP", "TF", "SBFO", "SBFI", "SNII"]
    t3_names = ["CAL_table3", "SNIa", "FP", "TFR", "SBFm", "SBFir", "SNII"]
    sel_mask = np.zeros(len(ids), dtype=bool)
    sel_mask[sel] = True
    z = cz / C
    pos_low = positive & (z < 0.01)
    pos_high = positive & (z > 0.10)

    def _cohort_anchor_block(mask):
        cal_grp = t3_pres[mask, 0]
        pure_cal = Wfull[mask, 6] > 0
        mixed_cal = cal_grp & (~pure_cal)
        anchor_cols = grp_has_gal_anchor[mask]
        overlap_3x7 = (anchor_cols.T @ t3_pres[mask].astype(np.int64)).tolist()
        return {
            "n_groups": int(np.sum(mask)),
            "cal_table3_present_groups": int(np.sum(cal_grp)),
            "pure_directcal_groups": int(np.sum(pure_cal)),
            "mixed_cal_plus_velocity_groups": int(np.sum(mixed_cal)),
            "table2_anchor_groups": {k: int(np.sum(anchor_cols[:, i])) for i, k in enumerate(["TRGB", "Cepheid", "maser"])},
            "any_table2_anchor_groups": int(np.sum(anchor_cols.any(axis=1))),
            "multi_anchor_groups": {
                "TRGB_and_Cepheid": int(np.sum(anchor_cols[:, 0] & anchor_cols[:, 1])),
                "TRGB_and_maser": int(np.sum(anchor_cols[:, 0] & anchor_cols[:, 2])),
                "Cepheid_and_maser": int(np.sum(anchor_cols[:, 1] & anchor_cols[:, 2])),
            },
            "anchor_by_table3_method_matrix_3x7": {
                "rows_table2_anchors": ["TRGB", "Cepheid", "maser"],
                "cols_table3_methods": t3_names,
                "counts": overlap_3x7,
            },
        }

    return {
        "galaxies_total": len(raw2),
        "galaxies_mapped_to_table3_groups": int(np.sum(mapped)),
        "galaxies_unmapped_not_in_table3": int(np.sum(unmapped)),
        "unmapped_unique_1pgc_ids": unmapped_1pgc,
        "unmapped_galaxy_method_counts": unmapped_counts,
        "unique_groups_total": len(ids),
        "positive_log_domain_groups": int(np.sum(positive)),
        "nonpositive_groups": int(np.sum(~positive)),
        "selected_groups": len(sel),
        "outside_selected_total": int(len(ids) - len(sel)),
        "outside_selected_positive_low_z": int(np.sum(pos_low)),
        "outside_selected_positive_high_z": int(np.sum(pos_high)),
        "table2_galaxy_indicator_counts_all": {k: int(c) for k, c in zip(gal_names, gal_pres.sum(axis=0))},
        "pure_directcal_selected_ids": ids[sel_mask & (Wfull[:, 6] > 0)].tolist(),
        "mixed_cal_selected_ids": ids[sel_mask & t3_pres[:, 0] & (Wfull[:, 6] == 0)].tolist(),
        "all_release_38053": _cohort_anchor_block(np.ones(len(ids), dtype=bool)),
        "selected_35970": _cohort_anchor_block(sel_mask),
        "D01_status": "OPEN_BOUNDED_NUISANCE_ONLY",
        "missing_upstream_blocks": [
            "pre_intercalibration_per_anchor_moduli_and_covariance (TRGB/Cepheid/maser combined into single table3 CAL column)",
            "anchor_training_set_membership_indicator",
            "DirectCal_cross_covariance_with_SNIa_zero_point",
        ],
    }


def _direct_fourier_modes(targets, positions, n, gq, A):
    out = np.empty((len(targets), A.shape[0]), dtype=np.complex128)
    for i, (k, ux, uy, uz) in enumerate(targets):
        u = np.array([ux, uy, uz], dtype=float)
        src = gq * (n @ u) * np.exp(1j * k * (positions @ u))
        out[i] = A @ src
    return out


def _finufft_log_modes(finufft, targets, positions, n, gq_list, A, eps=1e-12):
    """Matrix-free NUFFT projection of A @ diag(gq * (n . u)) exp(i k u . x) without N^2 allocation."""
    xmax = np.max(np.abs(positions), axis=0)
    scale = np.array([2. ** max(0, math.ceil(math.log2(v / (math.pi / 2.)))) for v in xmax])
    scaled = np.ascontiguousarray((positions / scale).T)
    freq = np.ascontiguousarray((targets[:, 1:] * targets[:, :1] * scale).T)
    p = A.shape[0]
    m_jac = len(gq_list)
    coeff = np.ascontiguousarray(
        np.concatenate(
            [(A[:, :, None] * (gq[:, None] * n)[None, :, :]).transpose(0, 2, 1).reshape(p * 3, -1) for gq in gq_list],
            axis=0,
        ),
        dtype=np.complex128,
    )
    plan = finufft.Plan(
        3, 3, n_trans=m_jac * p * 3, eps=eps, isign=1, dtype="complex128",
        nthreads=1, upsampfac=2.0, maxbatchsize=1, fftw=64,
    )
    plan.setpts(*(np.ascontiguousarray(v) for v in scaled), *(np.ascontiguousarray(v) for v in freq))
    field = np.asarray(plan.execute(coeff)).reshape(m_jac, p, 3, len(targets))
    return np.einsum("jadt,td->jta", field, targets[:, 1:])


def _cov_from_projected_modes(bands, modes_ta, amp, r30_sci, radii_Mpc):
    p = modes_ta.shape[1]
    outputs, factors = [], []
    for band in bands:
        parts = []
        for ik, k in enumerate(band["k"]):
            w = modes_ta[band["indices"][ik]]
            smooth = np.exp(-0.5 * (k * radii_Mpc) ** 2)
            scale = np.sqrt(band["wk"][ik] * r30_sci.power(k, amp) * band["wu"] / (2. * math.pi ** 2))
            block = np.einsum("r,ta,t->rat", smooth, w, scale).reshape(len(radii_Mpc) * p, -1)
            parts.extend([block.real, block.imag])
        F = np.concatenate(parts, axis=1)
        C_band = 0.5 * (F @ F.T + (F @ F.T).T)
        outputs.append(C_band)
        factors.append(F)
    return outputs, factors


def _covariance_diagnostics(mat):
    sym = 0.5 * (mat + mat.T)
    ev = np.linalg.eigvalsh(sym)
    tr = float(np.trace(sym))
    tol = 1e-12 * max(tr, float(np.max(np.abs(ev))))
    if tr <= 0 or ev[0] < -tol:
        raise ValueError(f"covariance PSD violation: trace={tr}, min_eig={ev[0]}")
    return {
        "trace": tr,
        "min_eigenvalue": float(ev[0]),
        "max_eigenvalue": float(ev[-1]),
        "rank_1e_12": int(np.sum(ev > 1e-12 * ev[-1])),
        "rank_1e_10": int(np.sum(ev > 1e-10 * ev[-1])),
        "condition": float(ev[-1] / ev[0]) if ev[0] > 1e-15 * ev[-1] else None,
        "is_rank_deficient": bool(ev[0] <= 1e-12 * ev[-1]),
    }


def log_pv_and_selection_covariance(H, inp, ids, n, cz, v, mu, emu, positive, selected, sel, Wfull, W, A, sigma_work, cov_work, b, cov5, T, coords, weights_p1):
    """D02 / M01: Matrix-free log-space EH98 S_PV(R) and low-rank selection/boundary covariance."""
    t_start = time.perf_counter()
    r30_sci, gls_svd, transport_covariance, finufft = _load_r30_and_bridge()
    z_sel = cz[sel] / C
    chi64, g64, j64, _, _ = r30_sci.background(z_sel, 64)
    chi32, g32, j32, _, _ = r30_sci.background(z_sel, 32)
    bg_rel_err = float(max(
        np.max(np.abs(chi64 - chi32) / chi64),
        np.max(np.abs(g64 - g32) / np.abs(g64)),
        np.max(np.abs(j64 - j32) / np.abs(j64)),
    ))
    if bg_rel_err > 1e-9:
        raise ValueError(f"background quadrature drift 32 vs 64: {bg_rel_err}")

    # Two physical peculiar-velocity -> log-distance Jacobians (units: (km/s)^-1)
    q_WF = (1.0 + v[sel] / C) / v[sel]
    q_cosmo = -MAG * j64
    q_ratio = q_cosmo / q_WF

    # Quadrature targets from locked TARGET_INVENTORY.npz (or reconstructed if absent)
    if not TARGET_INV.exists():
        raise FileNotFoundError(f"missing cached TARGET_INVENTORY: {TARGET_INV}")
    with np.load(TARGET_INV, allow_pickle=False) as inv:
        targets = np.asarray(inv["target"], dtype=float)
        bands_by_stage = {}
        for name, ang_ord, rad_ord in (("B", 53, 16), ("C", 53, 32)):
            _, _, _, wu_double = r30_sci.angular_rule(ang_ord)
            wu = wu_double / (4. * math.pi)
            stage_bands = []
            for bi, (lo, hi) in enumerate(r30_sci.BANDS):
                k_grid, wk = r30_sci.cc_rule(rad_ord, lo, hi)
                idx_mat = np.asarray(inv[f"{name}{bi}"], dtype=np.int64)
                stage_bands.append({"k": k_grid, "wk": wk, "wu": wu, "indices": idx_mat})
            bands_by_stage[name] = stage_bands

    amp, _ = r30_sci.power_amplitude()
    radii_hinv = np.array([5.0, 10.0, 20.0], dtype=float)
    radii_Mpc = radii_hinv / r30_sci.H
    positions = chi64[:, None] * n[sel]

    t_nu = time.perf_counter()
    gq_pair = [g64 * q_WF, g64 * q_cosmo]
    modes_pair = _finufft_log_modes(finufft, targets, positions, n[sel], gq_pair, A, eps=1e-12)
    nufft_seconds = time.perf_counter() - t_nu

    # Independent direct Fourier summation parity check on 6 spread modes
    probe_idx = [0, 1, 2, len(targets) // 3, len(targets) // 2, len(targets) - 1]
    probe_targets = targets[probe_idx]
    direct_wf = _direct_fourier_modes(probe_targets, positions, n[sel], gq_pair[0], A)
    direct_cos = _direct_fourier_modes(probe_targets, positions, n[sel], gq_pair[1], A)
    nufft_err_wf = float(np.max(np.abs(modes_pair[0, probe_idx] - direct_wf)) / np.max(np.abs(direct_wf)))
    nufft_err_cos = float(np.max(np.abs(modes_pair[1, probe_idx] - direct_cos)) / np.max(np.abs(direct_cos)))
    if max(nufft_err_wf, nufft_err_cos) > 1e-6:
        raise ArithmeticError(f"finufft vs direct log-PV parity failed: wf={nufft_err_wf}, cos={nufft_err_cos}")

    # Stage B & Stage C S_PV matrices in dimensionless log-distance units
    spv = {}
    for m_idx, jlabel in enumerate(("WF_log", "Cosmo_log")):
        c_B, _ = _cov_from_projected_modes(bands_by_stage["B"], modes_pair[m_idx], amp, r30_sci, radii_Mpc)
        c_C, _ = _cov_from_projected_modes(bands_by_stage["C"], modes_pair[m_idx], amp, r30_sci, radii_Mpc)
        tot_B = c_B[0] + c_B[1]
        tot_C = c_C[0] + c_C[1]
        rel_B_vs_C = float(np.linalg.norm(tot_C - tot_B) / np.linalg.norm(tot_C))
        spv[jlabel] = {
            "total_108x108": tot_C,
            "band1_108x108": c_C[0],
            "band2_108x108": c_C[1],
            "stage_B_vs_C_rel_fro": rel_B_vs_C,
            "by_R": {
                int(R): _covariance_diagnostics(tot_C[36 * ri : 36 * (ri + 1), 36 * ri : 36 * (ri + 1)])
                for ri, R in enumerate(radii_hinv)
            },
        }

    # Decompose independent per-group noise N(sigma_v_nl)
    d_meas = (MAG * emu[sel]) ** 2
    n_var = {
        0: d_meas,
        150: d_meas + (150.0 * q_WF) ** 2,
        250: d_meas + (250.0 * q_WF) ** 2,
    }
    N_mats = {
        sig_nl: H.joint_covariance(A, np.sqrt(d_v))[0]
        for sig_nl, d_v in n_var.items()
    }
    n250_parity = float(np.max(np.abs(N_mats[250] - cov_work)))
    if n250_parity > 1e-12:
        raise ArithmeticError(f"diagonal N(250) parity error: {n250_parity}")

    # Low-rank selection & boundary-truncation response C_sel = J_sel @ Sigma_sel @ J_sel^T (rank <= 9)
    z_full = cz / C
    pos_low = positive & (z_full < 0.01)
    pos_high = positive & (z_full > 0.10)
    _, _, _, _, _, b_with_low = tomography(H, n[selected | pos_low], cz[selected | pos_low], v[selected | pos_low], mu[selected | pos_low], emu[selected | pos_low])
    _, _, _, _, _, b_with_high = tomography(H, n[selected | pos_high], cz[selected | pos_high], v[selected | pos_high], mu[selected | pos_high], emu[selected | pos_high])
    J_sel_cut = np.column_stack(((b_with_low - b).ravel(), (b_with_high - b).ravel()))

    inv_var_w = 1.0 / (sigma_work ** 2)
    J_sel_malm = np.zeros((36, 7), dtype=float)
    mu_sel = mu[sel]
    mu_global_sd = float(np.std(mu_sel))
    for m_col in range(7):
        wm = W[:, m_col] * inv_var_w
        if np.sum(wm) > 0:
            mu_bar = float(np.sum(wm * mu_sel) / np.sum(wm))
            var_m = float(np.sum(wm * (mu_sel - mu_bar) ** 2) / np.sum(wm))
            sd_m = math.sqrt(var_m) if var_m > 1e-6 else mu_global_sd
            J_sel_malm[:, m_col] = A @ (W[:, m_col] * (mu_sel - mu_bar) / sd_m)
    J_sel = np.column_stack((J_sel_cut, J_sel_malm))
    # Nominal selection scale: unit boundary truncation indicator (sd=1) + 0.05 mag per SD Malmquist depth tilt
    Sigma_sel = np.diag([1.0, 1.0] + [0.05 ** 2] * 7)
    C_sel = 0.5 * (J_sel @ Sigma_sel @ J_sel.T + (J_sel @ Sigma_sel @ J_sel.T).T)

    # Full 7-channel calibration block Sigma_cal (rank 5 overlap + common 0.087 mag + DirectCal 0.5 mag sensitivity)
    Sigma_cal = np.zeros((7, 7), dtype=float)
    Sigma_cal[1:6, 1:6] = cov5
    Sigma_cal += (0.087 ** 2) * np.ones((7, 7), dtype=float)
    Sigma_cal[6, 6] += 0.5 ** 2

    J_joint = np.column_stack((T, J_sel))
    Sigma_joint = block_diag(Sigma_cal, Sigma_sel)
    bridge_res = transport_covariance(
        A,
        n_var[150],
        calibration_response=J_joint,
        calibration_covariance=Sigma_joint,
        ownership={
            "independent": ["modulus_measurement_noise", "nonlinear_velocity_dispersion_150_kms"],
            "calibration": ["SNIa_rank5_overlap_cov5", "common_zp_0p087_mag", "DirectCal_0p5_mag", "redshift_boundary_truncation", "per_method_malmquist_tilt_0p05_mag_per_sd"],
        },
    )
    bridge_n_diff = float(np.max(np.abs(bridge_res["independent"] - N_mats[150])))
    if bridge_n_diff > 1e-12:
        raise ArithmeticError(f"transport_covariance independent block mismatch: {bridge_n_diff}")

    # Assemble 4-term C_36 models across R in {5, 10, 20} and WF vs Cosmo Jacobians
    designs = {
        "shared_monopole": np.tile(np.eye(9)[:, 0], 4)[:, None],
        "affine_monopole": np.column_stack((
            np.tile(np.eye(9)[:, 0], 4),
            np.repeat(np.array(H.CENTERS) - 0.05, 9) * np.tile(np.eye(9)[:, 0], 4),
        )),
        "shared_9D_mean": np.tile(np.eye(9), (4, 1)),
    }
    y_vec = b.ravel()

    # Exact baseline check: J_cal @ Sigma_cal @ J_cal^T + C_sel matches bridge calibration block
    CK_cal = T @ Sigma_cal @ T.T
    ck_diff = float(np.max(np.abs((CK_cal + C_sel) - bridge_res["calibration"])))
    if ck_diff > 1e-12:
        raise ArithmeticError(f"calibration + selection block decomposition mismatch: {ck_diff}")

    models_36 = {}
    configs = [
        ("working_diag_250_no_PV", cov_work, None),
        ("correlated_WF_R5_nl150_cal087_sel", bridge_res["total"] + spv["WF_log"]["total_108x108"][:36, :36], spv["WF_log"]["total_108x108"][:36, :36]),
        ("correlated_WF_R10_nl150_cal087_sel", bridge_res["total"] + spv["WF_log"]["total_108x108"][36:72, 36:72], spv["WF_log"]["total_108x108"][36:72, 36:72]),
        ("correlated_WF_R20_nl150_cal087_sel", bridge_res["total"] + spv["WF_log"]["total_108x108"][72:108, 72:108], spv["WF_log"]["total_108x108"][72:108, 72:108]),
        ("correlated_Cosmo_R5_nl150_cal087_sel", bridge_res["total"] + spv["Cosmo_log"]["total_108x108"][:36, :36], spv["Cosmo_log"]["total_108x108"][:36, :36]),
    ]
    C_primary = None
    for m_name, C36, C_pv_block in configs:
        C36_sym = 0.5 * (C36 + C36.T)
        if m_name == "correlated_WF_R5_nl150_cal087_sel":
            C_primary = C36_sym
        fits = {dname: gls_svd(y_vec, Xmat, C36_sym, relative_rank_tolerance=1e-10) for dname, Xmat in designs.items()}
        bic = {dname: float(fv["statistic"] + fv["rank"] * math.log(36.0)) for dname, fv in fits.items()}
        chosen = min(bic, key=bic.get)
        # Inner windows (0,1) -> outer windows (2,3) Schur log-predictive chi2 (18 dof)
        C11, C21, C22 = C36_sym[:18, :18], C36_sym[18:, :18], C36_sym[18:, 18:]
        D_12 = designs["shared_9D_mean"]
        D1, D2 = D_12[:18], D_12[18:]
        L11 = np.linalg.cholesky(C11)
        C11i_D1 = solve_triangular(L11.T, solve_triangular(L11, D1, lower=True), lower=False)
        C11i_y1 = solve_triangular(L11.T, solve_triangular(L11, y_vec[:18], lower=True), lower=False)
        C11i_C12 = solve_triangular(L11.T, solve_triangular(L11, C21.T, lower=True), lower=False)
        cov_b1 = np.linalg.inv(D1.T @ C11i_D1)
        b1 = cov_b1 @ (D1.T @ C11i_y1)
        H_sc = D2 - C21 @ C11i_D1
        y2_pred = D2 @ b1 + C21 @ solve_triangular(L11.T, solve_triangular(L11, y_vec[:18] - D1 @ b1, lower=True), lower=False)
        C22_pred = (C22 - C21 @ C11i_C12) + H_sc @ cov_b1 @ H_sc.T
        C22_pred = 0.5 * (C22_pred + C22_pred.T)
        L22 = np.linalg.cholesky(C22_pred)
        r2 = solve_triangular(L22, y_vec[18:] - y2_pred, lower=True)
        schur_chi2 = float(r2 @ r2)
        schur_logdet = float(2.0 * np.sum(np.log(np.diag(L22))))
        models_36[m_name] = {
            "matrix_diag": _covariance_diagnostics(C36_sym),
            "trace_decomposition": {
                "independent_N": float(np.trace(cov_work if C_pv_block is None else N_mats[150])),
                "coherent_S_PV": 0.0 if C_pv_block is None else float(np.trace(C_pv_block)),
                "calibration_cal087_overlap_directcal": 0.0 if C_pv_block is None else float(np.trace(CK_cal)),
                "selection_boundary_malmquist": 0.0 if C_pv_block is None else float(np.trace(C_sel)),
            },
            "gls_fits": {
                dname: {
                    "chi2": float(fv["statistic"]),
                    "rank": int(fv["rank"]),
                    "residual_dof": int(fv["residual_dof"]),
                    "bic": bic[dname],
                    "H0_log_implied_kms_Mpc": float(HREF * math.exp(fv["beta"][0])),
                    "beta_0_log": float(fv["beta"][0]),
                    "beta_0_sd": float(math.sqrt(fv["beta_covariance"][0, 0])),
                    "dipole_norm": float(np.linalg.norm(fv["beta"][1:4])) if fv["beta"].size >= 4 else None,
                    "stf5_norm": float(np.linalg.norm(fv["beta"][4:9])) if fv["beta"].size >= 9 else None,
                    "scaled_condition": float(fv["scaled_condition"]),
                }
                for dname, fv in fits.items()
            },
            "bic_selected_model": chosen,
            "inner_to_outer_18dof_schur_chi2": schur_chi2,
            "inner_to_outer_18dof_schur_loglik": float(-0.5 * (18.0 * math.log(2.0 * math.pi) + schur_logdet + schur_chi2)),
        }

    # Propagate the full correlated R=5 WF 36D Cholesky draws into P1 common-nuisance finite slices
    draws_corr = (y_vec + coords @ np.linalg.cholesky(C_primary).T).reshape(-1, 4, 9)
    L5 = np.linalg.cholesky(cov5)
    radius5 = math.sqrt(chi2.ppf(0.95, 5))
    corr_slices = {}
    slice_dirs = {"DirectCal_minus_SNIa": (np.eye(7)[6], 0.5)}
    for k in range(5):
        gk = np.zeros(7)
        gk[1:6] = L5[:, k]
        slice_dirs[f"relative_cholesky_{k}"] = (gk, radius5)
    for kname, (direction, cap) in slice_dirs.items():
        log_der = (T @ direction).reshape(4, 9)
        corr_slices[kname] = finite_slice(draws_corr[:, :, 4:], log_der[:, 4:], np.ones((len(draws_corr), 4)), np.zeros(4), cap, weights_p1, 0.05)

    return {
        "provenance": {
            "frames": {"sky": "outward_ICRS_J2000", "redshift": "CMB_frame_z_proxy", "H_ref_log_kms_Mpc": HREF, "Vpwf_reference_H_kms_Mpc": 75.0},
            "gauge": "SNIa rank-5 post-intercalibration overlap + explicit common ZP 0.087 mag + DirectCal sensitivity 0.5 mag",
            "transfer_source": "EH98_NO_WIGGLE_APPROXIMATION_R30_R36 (Stage C: k in [0.005, 0.05] h/Mpc)",
            "matrix_free_35970x35970_avoided": True,
        },
        "background_quadrature_32_vs_64_max_rel": bg_rel_err,
        "pv_jacobian_comparison": {
            "q_WF_min_max_per_kms": [float(q_WF.min()), float(q_WF.max())],
            "q_cosmo_min_max_per_kms": [float(q_cosmo.min()), float(q_cosmo.max())],
            "q_cosmo_over_q_WF_min_max": [float(q_ratio.min()), float(q_ratio.max())],
            "nufft_vs_direct_6mode_rel_wf": nufft_err_wf,
            "nufft_vs_direct_6mode_rel_cosmo": nufft_err_cos,
            "nufft_seconds": nufft_seconds,
            "wf_vs_cosmo_R5_relative_fro": float(
                np.linalg.norm(spv["Cosmo_log"]["total_108x108"][:36, :36] - spv["WF_log"]["total_108x108"][:36, :36])
                / np.linalg.norm(spv["WF_log"]["total_108x108"][:36, :36])
            ),
        },
        "noise_trace_by_sigma_nl": {str(k): float(np.trace(M)) for k, M in N_mats.items()},
        "spv_log_stage_B_vs_C_rel_fro": {k: spv[k]["stage_B_vs_C_rel_fro"] for k in spv},
        "spv_log_diagnostics_by_R": {k: spv[k]["by_R"] for k in spv},
        "selection_covariance": {
            "J_sel_shape": list(J_sel.shape),
            "C_sel_diagnostics": _covariance_diagnostics(C_sel),
            "boundary_shift_norm_low_z_lt_0p01": float(np.linalg.norm(J_sel_cut[:, 0])),
            "boundary_shift_norm_high_z_gt_0p10": float(np.linalg.norm(J_sel_cut[:, 1])),
            "malmquist_method_column_norms": np.linalg.norm(J_sel_malm, axis=0).tolist(),
        },
        "transport_covariance_models_36d": models_36,
        "correlated_P1_common_nuisance_slices_R5_WF": corr_slices,
        "elapsed_seconds": time.perf_counter() - t_start,
    }
def compute():
    start = time.perf_counter()
    H = r95._load_h03()
    inp = H.source(r95.SELECT)
    files = {"selected": r95.SELECT, "R27_factor": r97.R27_NPZ, "R36_cov": r97.R36_NPZ,
             "R36_targets": TARGET_INV, "P1_draws": P1/"results/paired_functional_arrays.npz",
             "H03_stat": P1/"source/H03_SOURCE_TOMOGRAPHY.json",
             "R97_CF4": R97/"CF4_GENEALOGY_AND_PARTIAL_ID.json", "R97_P1": R97/"PHY_AND_P1_P4_P6_SYNTHESIS.json"}
    files.update({name: r97.RAW_CF4/name for name in ["table2.dat","table3.dat","table4.dat","ReadMe"]})
    def identities():
        return {name: {"path": str(path), "sha256": r97._sha(path)} for name,path in files.items()}
    source_ids = identities()
    prev = json.loads(files["R97_CF4"].read_text())
    pins = {"selected":"selected_35970","R27_factor":"r27_factor_npz","R36_cov":"r36_matrices_npz",
            "table3.dat":"table3_dat","table4.dat":"table4_dat","ReadMe":"ReadMe"}
    if any(source_ids[k]["sha256"] != prev["sources_sha256"][p] for k,p in pins.items()):
        raise ValueError("R97 predecessor source check")
    if source_ids["table2.dat"]["sha256"] != prev["cf4_genealogy"]["table2_comparison"]["table2_sha256"]:
        raise ValueError("table2 identity drift")

    ids,mu,emu,cz,v,ds,wf,ramp,n,vls = catalog()
    z = cz/C
    positive = (cz > 0) & (v > 0)
    selected = (z >= .01) & (z <= .10)
    ix = np.argsort(ids[selected])
    sel = np.flatnonzero(selected)[ix]
    if not np.array_equal(ids[sel], inp.ids) or np.max(abs(n[sel]-inp.n)) > 1e-10:
        raise ValueError("CMB redshift cut or sky identity drift")
    if not (np.array_equal(mu[sel], inp.mu) and np.array_equal(emu[sel], inp.e_mu)
            and np.array_equal(z[sel], inp.z)):
        raise ValueError("selected modulus/error/redshift mismatch")
    t3 = r97._parse_complete_table3_for_selected(ids)
    Wfull = magnitude_weights(t3)
    W = Wfull[sel]
    with np.load(r97.R27_NPZ, allow_pickle=False) as p:
        if not (np.array_equal(p["group_id"], inp.ids) and p["channel_names"].tolist() == METHODS
                and np.array_equal(p["selected_support_7"] > 0, W > 0)):
            raise ValueError("R27 method and group identities differ")
    with np.load(r97.R36_NPZ, allow_pickle=False) as p:
        r36theta = p["theta"].copy()
    cohort = {}
    for name,ii in (("all",np.ones(len(ids),bool)),("selected",selected),("outside_selected",~selected)):
        tcal = ii & np.isfinite(t3["cal_vals"]) & (t3["dmav"]>0)
        cohort[name] = dict(n=int(ii.sum()), positive_log_domain=int(np.sum(ii & positive)),
                            method_numeric_presence=t3["dm_present_7"][ii].sum(axis=0),
                            direct_only=int(np.sum((Wfull[:,6]>0)&ii)),
                            multi_velocity_methods=int(np.sum(((Wfull[:,:6]>0).sum(axis=1)>1)&ii)),
                            cal_minus_registered_modulus_mixed_groups=summaries(t3["cal_vals"][tcal]-mu[tcal]))
    raw2 = [row for row in files["table2.dat"].read_text(encoding="ascii").splitlines() if row.strip()]
    sel_ids = set(inp.ids.tolist())
    t2_selected = np.fromiter((int(row[8:15]) in sel_ids for row in raw2),bool,len(raw2))
    t2methods = [(41,47),(53,59),(65,71),(77,83),(90,96),(102,107),(113,119),(126,131)]
    t2pres = np.array([[bool(row[a:b].strip()) for a,b in t2methods] for row in raw2])
    t2 = dict(total=len(raw2), selected_group_members=int(t2_selected.sum()),
              released_indicators=["SNIa","TF","FP","SBF","SNII","TRGB","Cepheid","maser"],
              presence_all=t2pres.sum(axis=0),presence_selected=t2pres[t2_selected].sum(axis=0))
    velocity_products = {}
    for name,mask in (("all_release",np.ones(len(ids),bool)),("selected",selected)):
        velocity_products[name] = {
            "DS_minus_WF_kms":summaries(ds[mask]-wf[mask]),
            "ramp_minus_WF_kms":summaries(ramp[mask]-wf[mask]),
            "ramp_nonidentical_to_WF":int(np.sum(ramp[mask]!=wf[mask]))}
    # Fit the log convention to the *released* Vpwf, independently of the assumed physical dispersion.
    # ReadMe table4 V3k/fV3k/Vpds/Vpwf/Vpec are integer km/s; DMzp is F6.3 mag.
    dist_full = np.exp(MAG*(mu-25.))
    pred_ds = (v-75.*dist_full)/(1.+75.*dist_full/C)
    velocity_products["DS_75_minus_release_all_kms"] = summaries(pred_ds-ds)
    velocity_products["DS_75_max_abs_all_kms"] = np.max(abs(pred_ds-ds))
    for label,mask in (("all_positive",positive),("selected",selected)):
        scale = v[mask]/(1.+v[mask]/C)
        x = np.log(v[mask]/dist_full[mask])  # numerical v/d in km/s/Mpc
        slope,intercept = np.polyfit(x,wf[mask]/scale,1)
        record = dict(n=int(mask.sum()),model="Vpwf/[v/(1+v/c)] = slope*ln(numerical v/d)+intercept",
                      slope=slope,intercept=intercept,implied_reference_H=np.exp(-intercept/slope),
                      inverse_ln10=1/np.log(10.))
        for href in (75.,HREF):
            for base,fac in (("ln",1.),("log10",1/np.log(10.))):
                residual = scale*fac*(x-np.log(href))-wf[mask]
                record[f"{base}_H{href:g}_minus_released_kms"] = {**summaries(residual),
                                                                "max_abs":np.max(abs(residual))}
        velocity_products["released_WF_convention_"+label] = record
    # Use released rounded DS/WF values to check the Local-Sheet ramp; at rounded v=0
    # v log(v) has a zero right limit. At negative v the release uses Vpds.
    frac = np.where(v<0.,0.,np.clip(vls/3000.,0.,1.))
    ramp_res = (1-frac)*ds+frac*wf-ramp
    velocity_products["ramp_from_released_integer_DS_WF_and_Vls"] = {
        **summaries(ramp_res),"max_abs":np.max(abs(ramp_res)),
        "above_1kms_group_ids":ids[abs(ramp_res)>1.],
        "nonpositive_v_WF_zero_count":int(np.sum((~positive)&(wf==0))),
        "convention":"clip(Vls/3000,0,1) for fV>=0; use DS for fV<0"}
    if (velocity_products["DS_75_max_abs_all_kms"]>1. or
            velocity_products["released_WF_convention_all_positive"]["log10_H75_minus_released_kms"]["max_abs"]>1.):
        raise ValueError("immutable published velocity column replay drift")

    X,y,sig,A,cov,b = tomography(H, n[sel],cz[sel],v[sel],mu[sel],emu[sel])
    T = -MAG*(A@W)
    bcz = (A@(np.log(cz[sel]/HREF)-MAG*(mu[sel]-25.))).reshape(4,9)
    Xb,yb,sb,Ab,Cb,bb = tomography(H,n[positive],cz[positive],v[positive],mu[positive],emu[positive])
    del Xb,yb,sb,Ab
    log_cv = prediction_cv(H,n[sel],cz[sel],v[sel],mu[sel],emu[sel])
    f = r97.cf4_p0b.profile_method_offsets(t3["dm_vals_6"][sel], t3["e_vals_6"][sel])
    cov5 = f["cov_working_mag2"][1:,1:]
    f7 = np.zeros((7,7))
    f7[:6,:6] = f["F"]
    source_rank = np.linalg.matrix_rank(f7)
    if source_rank != 5 or np.linalg.matrix_rank(cov5)!=5:
        raise ValueError("overlap covariance rank")
    direct = np.eye(7)[6]
    delta = np.array([.02,-.11,.17,-.08,.07,-.03,.42])
    mu_shifted = mu[sel]+W@delta
    _,_,_,_,cov_delta,shifted = tomography(H,n[sel],cz[sel],v[sel],mu_shifted,emu[sel])
    _,_,_,_,cov_common,b_common = tomography(H,n[sel],cz[sel],v[sel],mu[sel]+.087,emu[sel])
    common_expected = np.zeros((4,9)); common_expected[:,0] = -MAG*.087
    tol = 1e-11
    checks = dict(finite_seven_mode_refit=float(np.max(abs(shifted.ravel()-b.ravel()-T@delta))),
                  common_refit=float(np.max(abs((b_common-b)-common_expected))),
                  common_covariance_invariance=float(np.max(abs(cov_common-cov))),
                  arbitrary_covariance_invariance=float(np.max(abs(cov_delta-cov))),
                  A_design_identity=float(np.max(abs(A@X-np.tile(np.eye(9),(4,1))))),
                  weight_sum=float(np.max(abs(W.sum(axis=1)-1))))
    if max(checks.values()) > tol:
        raise ArithmeticError("affine covariance or design identity")
    radius = np.sqrt(chi2.ppf(.95,5))
    width = {}
    for d0 in (0., .1, .5):
        width[str(d0)] = support_width(T,cov5,radius,.087,d0).reshape(4,9)
    high_after_global_shift = HREF*np.exp(b_common[:,0])
    defs = dict(log_reference_H_kms_Mpc=HREF,C_kms=C,stf="H03 J2000 orthonormal Frobenius",
                angular_order=["1","nx","ny","nz","xx-yy","xx+yy-2zz","xy","xz","yz"],
                gaussian_window_centers=H.CENTERS,window_sigma_z=H.WIDTH,
                fixed_log_sigma="hypot(ln(10)/5*e_mu,250*(1+fV/c)/fV)",
                input_law="conditional fixed-z independent working modulus/peculiar scatter")
    fit = dict(selected_log_coefficients_4x9=b,selected_log_covariance_36x36=cov,
               selected_same_weights_uncorrected_cz_log_coefficients_4x9=bcz,
               extended_positive_log_coefficients_4x9=bb,extended_positive_covariance_36x36=Cb,
               geometric_monopole_kms_Mpc=HREF*np.exp(b[:,0]),
               geometric_monopole_common_shift_plus_0087mag=high_after_global_shift,
               H03_velocity_theta_4x9=r36theta.reshape(4,9),
               log_norm_STF=np.linalg.norm(b[:,4:],axis=1),
               positive_domain_log_norm_STF=np.linalg.norm(bb[:,4:],axis=1),
               overlap_fisher_rank=source_rank,post_registration_contrasts_SN_gauge=f["delta_mag"],
               relative_cov_5x5_mag2=cov5, common_null_residual=np.max(abs(f7@np.ones(7))),
               direct_null_residual=np.max(abs(f7@direct)),direct_only_selected=inp.ids[W[:,6]>0],
               J_log_per_mag_36x7=T, product_set_component_halfwidths=width,
               halfwidth_inputs={"common_bound_mag":.087,"direct_bounds_mag":[0.,.1,.5],
                                "relative_radius":radius,"relative_dimension":5,"upstream_posterior":None},
               source_refit_check=checks, design_weight_backend="NumPy/SciPy H03 pivot-free economic QR",
               covariance_min_eigenvalue=np.linalg.eigvalsh(cov)[0])

    archived = json.loads(files["H03_stat"].read_text())
    old_mu = np.array([z["theta9"] for z in archived["monopole_dipole_STF2_windows"]])
    old_cov = np.array(archived["joint_covariance_36x36"])
    with np.load(files["P1_draws"], allow_pickle=False) as p:
        old, w, oldq = p["draws"], p["weights"], p["q_app"]
        if len(old)!=2048 or not np.array_equal(p["centers"],H.CENTERS):
            raise ValueError("P1 finite-law inputs")
    from scipy.stats import norm, qmc
    coords = solve_triangular(np.linalg.cholesky(old_cov),
                              (old.reshape(-1,36)-old_mu.ravel()).T,lower=True).T
    u = qmc.Sobol(36,scramble=True,seed=160916).random_base2(10)
    z0 = norm.ppf(np.clip(u,np.finfo(float).eps,1.-np.finfo(float).eps))
    coord_err=np.max(abs(coords-np.vstack((z0,-z0))))
    if coord_err > 1e-10 or np.max(abs(old_mu.ravel()-r36theta))>1e-10:
        raise ValueError("old P1 Cholesky coordinates/H03 source replay")
    draws = (b.ravel()+coords@np.linalg.cholesky(cov).T).reshape(-1,4,9)
    ndraw = len(draws)
    root_sweeps = {}
    L = np.linalg.cholesky(cov5)
    directions = {"DirectCal_minus_SNIa":(direct,.5)}
    for k in range(5):
        g = np.zeros(7); g[1:6] = L[:,k]
        directions["relative_cholesky_"+str(k)] = (g,radius)
    source_jac = np.array(prev["source_modulus_perturbation"]["J_source_fixed_w_36x7"])
    for key,(direction,cap) in directions.items():
        log_der = (T@direction).reshape(4,9)
        old_der = (source_jac@direction).reshape(4,9)
        row = dict(direction_mag_per_s=direction,parameter_cap=cap,
                   parameter_unit="mag" if key.startswith("DirectCal") else "dimensionless",
                   new_log_STF=finite_slice(draws[:,:,4:],log_der[:,4:],np.ones((ndraw,4)),np.zeros(4),cap,w,.05),
                   R97_source_linearized_H03_ratio=finite_slice(old[:,:,4:],old_der[:,4:],old[:,:,0],old_der[:,0],cap,w,.05))
        root_sweeps[key]=row
    if np.max(abs(np.linalg.norm(old[:,:,4:],axis=2)/old[:,:,0]-oldq))>1e-14:
        raise ValueError("H03 signed denominator mismatch")
    old_report=json.loads(files["R97_P1"].read_text())["P1_five_view_with_r97_cf4_bounds"]
    p1 = dict(n_draw=ndraw, max_original_normal_coordinate_error=coord_err,
              antithetic_log_mean_maxabs=np.max(abs(draws.mean(axis=0)-b)),
              original_q_definition="norm(STF_H)/H",new_q_definition="norm(STF_logH)",
              finite_law="one shared 36D archived antithetic Sobol draw per 4-window record; same triangular coordinate convention",
              shared_1d_extrema=root_sweeps,older_R97_7d_per_draw_outer_source_jacobian={
                  k:old_report["source_modulus_jacobian_bounds_95pct"][k] for k in
                  ["per_draw_sharp_lower","per_draw_sharp_upper","per_draw_sharp_any_all_lower","per_draw_sharp_any_all_upper"]},
              historical_scope="R97 uses ridged rank-7 working ellipsoid; these 1D slices use explicit independent DirectCal and rank-5 relative coordinates. No nesting assumption.",
              physical_Q=None,physical_Pi=None,physical_F=None,physical_GF=None)
    anchor_gen = upstream_anchor_genealogy(raw2, ids, sel, positive, cz, t3, Wfull)
    cov_ext = log_pv_and_selection_covariance(H, inp, ids, n, cz, v, mu, emu, positive, selected, sel, Wfull, W, A, sig, cov, b, cov5, T, coords, w)
    if source_ids != identities():
        raise RuntimeError("source input changed during execution")
    return dict(schema="htt.r98.cf4_log_distance_joint_slices/1",assertion_tested=
                "all selected/full-domain fits and finite real-root shared 1D conditional diagnostic extrema",
                software={"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,
                          "machine":platform.machine(),"system":platform.system(),"blas_threads":os.getenv("OPENBLAS_NUM_THREADS"),
                          "omp_threads":os.getenv("OMP_NUM_THREADS")},
                baseline="52fee3f277d715cdb982dfbe751fefac10513060",
                checkout_at_run=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                inputs_unchanged_before_after=True,inputs=source_ids,definitions=defs,
                census=dict(release=cohort,table2=t2,table3_presence_order=["CAL"]+METHODS[:6],
                            raw_low_z=int(np.sum(z<.01)),raw_high_z=int(np.sum(z>.10)),
                            nonpositive_log_domain=int(np.sum(~positive)),selected_exact_cut=True,
                            actual_z_range=np.array([z[sel].min(),z[sel].max()])),
                upstream_anchor_genealogy=anchor_gen,
                catalogue_velocity_products=velocity_products, fit=fit,
                correlated_source_and_selection_extension=cov_ext,
                octant_product_predictions=log_cv,P1=p1,
                status=dict(SQ_CF4="BLOCKED_INPUT",P3="WORKING_MODEL_COMPARISON_EXECUTED",P1="FINITE_CONDITIONAL_SLICES_EXECUTED",
                            physical_Pi=None,publication_ready=False),
                elapsed_seconds=time.perf_counter()-start)


if __name__ == "__main__":
    result = compute()
    OUT.write_text(json.dumps(result,indent=2,allow_nan=False,default=json_default)+"\n")
    print(json.dumps({"output":str(OUT),"elapsed_s":result["elapsed_seconds"],"sha256":r97._sha(OUT),
                      "n":result["census"]["release"]["selected"]["n"],"status":result["status"]}))
