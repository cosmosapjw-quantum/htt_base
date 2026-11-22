"""CF4 joint log-distance tomography and shared one-coordinate finite-law calibration sweeps."""
from __future__ import annotations

import json
import os
import platform
import subprocess
import time
from pathlib import Path

import numpy as np
import scipy
from scipy.linalg import solve_triangular
from scipy.stats import chi2

from scripts.r95 import sq_cf4_synthesis as r95
from scripts.r97 import cf4_genealogy_and_partial_id as r97

ROOT = r95.ROOT
PUB = ROOT / "docs/research_program/observational_publication_20261015"
P1 = PUB / "CONTINUATION_20261018/P1"
R97 = PUB / "R97_SCIENCE_EXECUTION_20261122"
OUT = PUB / "R98_FOURTH_RESEARCH_CYCLE_20261123/CF4_P1_RESULTS.json"
MAG = np.log(10.) / 5.
C = 299792.458
HREF = 74.6
METHODS = ["SNIa", "FP", "TFR", "SBFm", "SBFir", "SNII", "DirectCal"]
EVENTS = ["z025", "z040", "z060", "z080", "any", "all"]


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

def compute():
    start = time.perf_counter()
    H = r95._load_h03()
    inp = H.source(r95.SELECT)
    files = {"selected": r95.SELECT, "R27_factor": r97.R27_NPZ, "R36_cov": r97.R36_NPZ,
             "P1_draws": P1/"results/paired_functional_arrays.npz", "H03_stat": P1/"source/H03_SOURCE_TOMOGRAPHY.json",
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
                catalogue_velocity_products=velocity_products, fit=fit,octant_product_predictions=log_cv,P1=p1,
                status=dict(SQ_CF4="BLOCKED_INPUT",P3="WORKING_MODEL_COMPARISON_EXECUTED",P1="FINITE_CONDITIONAL_SLICES_EXECUTED",
                            physical_Pi=None,publication_ready=False),
                elapsed_seconds=time.perf_counter()-start)


if __name__ == "__main__":
    result = compute()
    OUT.write_text(json.dumps(result,indent=2,allow_nan=False,default=json_default)+"\n")
    print(json.dumps({"output":str(OUT),"elapsed_s":result["elapsed_seconds"],"sha256":r97._sha(OUT),
                      "n":result["census"]["release"]["selected"]["n"],"status":result["status"]}))
