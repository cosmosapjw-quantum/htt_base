"""2MRS-NeuralNet z=0 velocity field on the R98 CF4 windows and the R103 6dFGSv holdout.

Field: Lilow et al. 2MRS neural-network reconstruction (author ZIP), CMB-frame peculiar
velocity in km/s on 128^3 cell centres (i-63.5)*3.125 h^-1 Mpc, Galactic axes, NaN beyond
200 h^-1 Mpc. Directions are rotated ICRS->Galactic; comoving radii use the R100/R103
background (h=0.6736). A group/galaxy enters the common sample only if r<=200 h^-1 Mpc and
all eight trilinear neighbours are finite. The z=0 velocity is transported by g(z)/g(0).
The 36 window coefficients are refit on the common CF4 sample. The error maps are not
used: they do not define inter-group posterior covariance.
Units: v in km/s; window coefficients and b in the R98 log-distance (natural log) basis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import healpy as hp
import numpy as np

FIELD_DIR = Path.home() / "Downloads/htt_r104_fields/2mrs_nn"
ZIP_SHA = "c12efc1063b6c06dda127a9c51aa97926d8666f6a615e9fba8412ba4adbabcd7"
FIELD_SHA = {"x": "50edf12e9dd8a79959071eda57ccd197f2cfba2bae5233210ab6243541aa4643",
             "y": "c125f3d97aa8f9ed34110285e018df0849d955b62f0a472cebb34d196e2cb447",
             "z": "ae1e0dfadf48c27afcf7f30c53c2e978f7edeab3506c9e446ed7f73770b207d6"}
STEP, CENTRE, RMAX, H_LITTLE = 3.125, 63.5, 200.0, 0.6736


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def load_field(directory=FIELD_DIR):
    out = []
    for axis in "xyz":
        path = Path(directory) / f"{axis}Velocity.npy"
        if _sha(path) != FIELD_SHA[axis]:
            raise ValueError(f"2MRS-NeuralNet {axis} velocity identity mismatch")
        arr = np.load(path, allow_pickle=False)
        if arr.shape != (128,) * 3 or arr.dtype != np.float32:
            raise ValueError("unexpected 2MRS-NeuralNet grid")
        out.append(arr.astype(np.float64))
    return np.stack(out, axis=-1)


def to_galactic(n_icrs):
    n = np.asarray(n_icrs, dtype=float)
    rot = np.asarray(hp.Rotator(coord=["C", "G"]).mat, dtype=float)
    return n @ rot.T


def interpolate(field, x_h):
    """Trilinear cell-centre interpolation; returns velocity (N,3) and the finite/inside mask."""
    u = np.asarray(x_h, dtype=float) / STEP + CENTRE
    base = np.floor(u).astype(int)
    inside = np.all((base >= 0) & (base <= 126), axis=1) & (np.linalg.norm(x_h, axis=1) <= RMAX)
    b = np.clip(base, 0, 126)
    frac = u - b
    vel = np.zeros((len(u), 3))
    finite = inside.copy()
    for corner in np.ndindex(2, 2, 2):
        c = np.array(corner)
        w = np.prod(np.where(c, frac, 1.0 - frac), axis=1)
        v = field[b[:, 0] + c[0], b[:, 1] + c[1], b[:, 2] + c[2]]
        finite &= np.isfinite(v).all(axis=1)
        vel += w[:, None] * np.where(np.isfinite(v), v, 0.0)
    vel[~finite] = np.nan
    return vel, finite


def cf4_windows(field):
    from scripts.r103 import manticore_cf4_pv as pv
    from scripts.r98 import cf4_p1 as old
    H = old.r95._load_h03()
    inp = H.source(old.r95.SELECT)
    ids, mu, emu, cz, v, _, _, _, n, _ = old.catalog()
    j = np.flatnonzero((cz / old.C >= .01) & (cz / old.C <= .10))
    j = j[np.argsort(ids[j])]
    if not (np.array_equal(ids[j], inp.ids) and np.max(abs(n[j] - inp.n)) <= 1e-10):
        raise ValueError("selected row/sky alignment drift")
    sci, *_ = old._load_r30_and_bridge()
    r, g, *_ = sci.background(cz[j] / old.C, 64)
    g0 = float(sci.background(np.array([0.]), 64)[1][0])
    h_bg = old.C * 1e-7 / (float(sci.background(np.array([1e-7]), 64)[0][0]) * 100.0)
    if abs(h_bg - H_LITTLE) > 1e-4:
        raise ValueError(f"background h {h_bg} differs from {H_LITTLE}")
    ng = to_galactic(n[j])
    vel, ok = interpolate(field, ng * (r * H_LITTLE)[:, None])
    radius_ok = r * H_LITTLE <= RMAX
    vlos = np.where(ok, np.einsum("ij,ij->i", np.nan_to_num(vel), ng), 0.0) * pv.velocity_growth_ratio(g, g0)
    conv = (1. + v[j] / old.C) / v[j]
    X, y, sig, A, cov, coeff = old.tomography(H, n[j], cz[j], v[j], mu[j], emu[j])
    Xc, yc, sigc, Ac, covc, coeffc = old.tomography(H, n[j][ok], cz[j][ok], v[j][ok], mu[j][ok], emu[j][ok])
    b_full_zero = A @ (conv * vlos)
    b_common = Ac @ (conv[ok] * vlos[ok])
    absA = np.abs(A)
    miss_comp = absA[:, ~ok].sum(1) / absA.sum(1)
    miss_win = absA.reshape(4, 9, -1)[:, :, ~ok].sum((1, 2)) / absA.reshape(4, 9, -1).sum((1, 2))
    obs_c = Ac @ yc

    def chi2(vec):
        return float(vec @ np.linalg.solve(covc, vec))

    aux = {"ng": ng, "r_h": r * H_LITTLE, "vlos": vlos, "ok": ok}
    return aux, {"n_groups": int(len(j)), "n_radius_le_200": int(radius_ok.sum()), "n_common": int(ok.sum()),
            "n_radius_pass_nonfinite_neighbour": int((radius_ok & ~ok).sum()),
            "g0_kms_per_Mpc": g0, "h": h_bg,
            "vlos_common_kms": {"mean": float(vlos[ok].mean()), "rms": float(np.sqrt((vlos[ok] ** 2).mean()))},
            "missing_abs_influence_fraction_per_window": miss_win.tolist(),
            "missing_abs_influence_fraction_36": miss_comp.tolist(),
            "observed_coefficients_full_36": (A @ y).tolist(), "observed_coefficients_common_36": obs_c.tolist(),
            "b_2mrs_common_refit_36": b_common.tolist(), "b_2mrs_fullA_zero_filled_36": b_full_zero.tolist(),
            "chi2_measurement_cov_common": {"observed": chi2(obs_c), "observed_minus_2mrs": chi2(obs_c - b_common),
                                            "dof": 36, "covariance": "R98 joint measurement covariance only; no PV/field/calibration terms"}}


COURTOIS = Path.home() / "Downloads/htt_r104_fields/courtois_cf4/CF4_new_128-z008_velocity.fits"
COURTOIS_SHA = "4cd0cc0404ae949fe27297d3b167bfce57ded8539102706d8d92c699f19563d6"


def galactic_to_supergalactic():
    """Rows are SGX, SGY, SGZ in Galactic Cartesian (SGP l=47.37,b=6.32; SGL=0 at l=137.37,b=0)."""
    z = hp.ang2vec(47.37, 6.32, lonlat=True)
    x = hp.ang2vec(137.37, 0.0, lonlat=True)
    x = x - (x @ z) * z
    x /= np.linalg.norm(x)
    return np.vstack([x, np.cross(z, x), z])


def courtois_internal(aux, path=COURTOIS):
    """Internal comparison only: Courtois et al. CF4 grid has no unit/centre metadata."""
    from astropy.io import fits
    if not Path(path).exists():
        return {"status": "file_absent"}
    if _sha(path) != COURTOIS_SHA:
        raise ValueError("Courtois CF4 velocity identity mismatch")
    with fits.open(path) as hdul:
        data = np.asarray(hdul[0].data, dtype=np.float64)
        header = {k: hdul[0].header[k] for k in hdul[0].header}
    rot = galactic_to_supergalactic()
    ok = aux["ok"]
    nsg = aux["ng"][ok] @ rot.T
    xsg = nsg * aux["r_h"][ok][:, None]
    step = 1000.0 / 128
    variants = {}
    for order in ("components_SGX_SGY_SGZ", "components_SGZ_SGY_SGX"):
        comp = data if order.startswith("components_SGX") else data[::-1]
        grid = np.moveaxis(comp, 0, -1)  # spatial index (SGZ, SGY, SGX)
        for centre in (63.5, 64.0):
            u = xsg[:, ::-1] / step + centre
            base = np.clip(np.floor(u).astype(int), 0, 126)
            frac = u - base
            vel = np.zeros((len(u), 3))
            for corner in np.ndindex(2, 2, 2):
                c = np.array(corner)
                w = np.prod(np.where(c, frac, 1 - frac), axis=1)
                vel += w[:, None] * grid[base[:, 0] + c[0], base[:, 1] + c[1], base[:, 2] + c[2]]
            los = np.einsum("ij,ij->i", vel, nsg)
            ref = aux["vlos"][ok]
            slope = float(ref @ los / (los @ los))
            variants[f"{order}|centre_index_{centre}"] = {
                "pearson_r_with_2mrs_los": float(np.corrcoef(los, ref)[0, 1]),
                "ls_slope_2mrs_kms_per_unit": slope, "los_rms_native_units": float(np.sqrt((los ** 2).mean()))}
    return {"status": "internal_comparison_convention_variants_reported_without_selection",
            "sha256": COURTOIS_SHA, "header": header, "record_axes": "(SGZ,SGY,SGX), 1000 Mpc/h, 128^3",
            "unit": "unspecified in file/record; slope gives empirical km/s per native unit vs 2MRS", "n_common": int(ok.sum()),
            "variants": variants}


def sixdf_folds(field):
    from scripts.r103 import cf4_shared_field_holdout as h
    r100, r99 = h.r100, h.r99
    t2 = r100.load_cf4_table2()
    six = r100.load_sixdf_pv()
    match = h.sixdf_match_ambiguity_policies(t2, six, arcsec=15., dv_kms=500.)
    inc = match["policies"]["unique_only_r101"]["included"]
    closest = match["closest_table2_indices"]
    mark = np.where(inc, six["delta_d"], np.nan)
    cz = six["cz_gal"]
    x = np.column_stack((np.ones(len(cz)), cz / 1e4 - 1.1, six["delta_d"], six["is_grouped"]))
    grid = np.array([-300., -100., 0., 100., 300.])
    sci, *_ = r100.old._load_r30_and_bridge()
    r, g, *_ = sci.background(cz / r100.C, 64)
    g0 = float(sci.background(np.array([0.]), 64)[1][0])
    ng = to_galactic(hp.ang2vec(six["ra"], six["dec"], lonlat=True))
    vel, ok = interpolate(field, ng * (r * H_LITTLE)[:, None])
    vpred = np.where(ok, np.einsum("ij,ij->i", np.nan_to_num(vel), ng), 0.0) * (g / g0)

    def means(offset):
        return np.array([r99.finite_shift(sci, cz / r100.C, np.arctanh((u + offset) / r100.C), "bolometric")
                         / (5. * r100.MAG) for u in grid])

    m0, m1 = means(0.0), means(vpred)
    m2 = (r99.finite_shift(sci, cz / r100.C, np.arctanh(vpred / r100.C), "bolometric") / (5. * r100.MAG))[None]
    reports = {}
    for key in ("pgc", "pgc1"):
        group = np.where(closest >= 0, t2[key][np.maximum(closest, 0)], -1)
        clusters = h.build_group_clusters(six["groupid_raw"], secondary_keys=group)
        folds = []
        for fold, (itr, ite) in enumerate(h.group_kfold_indices(clusters, n_splits=5, seed=42)):
            train = np.ones(len(mark), dtype=bool)
            train[ite] = False
            fit = h.fit_probit_with_hessian(x[itr], inc[itr])
            b = fit.beta_hat
            icpt = b[0] + b[1] * x[:, 1] + b[3] * x[:, 3]
            o0 = h.selected_probit_holdout(mark, m0, six["epsilon_d"], icpt, b[2], np.full(len(grid), .2), included=inc, train=train)
            o1 = h.selected_probit_holdout(mark, m1, six["epsilon_d"], icpt, b[2], np.full(len(grid), .2), included=inc, train=train)
            o2 = h.selected_probit_holdout(mark, m2, six["epsilon_d"], icpt, b[2], np.ones(1), included=inc, train=train)
            folds.append({"field_only_fresh_minus_zero": o2["fresh_minus_zero"],"fold": fold, "n_test": int(len(ite)), "n_test_selected": int(inc[ite].sum()),
                          "before_fresh_minus_zero": o0["fresh_minus_zero"], "before_shared_minus_zero": o0["shared_minus_zero"],
                          "after_fresh_minus_zero": o1["fresh_minus_zero"], "after_shared_minus_zero": o1["shared_minus_zero"]})
        reports[key] = {"folds": folds, **{f"cv_{k}": sum(f[k] for f in folds) for k in
                        ("before_fresh_minus_zero", "before_shared_minus_zero", "after_fresh_minus_zero", "after_shared_minus_zero",
                         "field_only_fresh_minus_zero")}}
    return {"n_parent": int(len(mark)), "n_selected": int(inc.sum()), "n_field_defined": int(ok.sum()),
            "vpred_kms": {"mean": float(vpred[ok].mean()), "rms": float(np.sqrt((vpred[ok] ** 2).mean()))},
            "offset_convention": "after: mixture over common radial speed u + 2MRS v_pred(galaxy); field_only: single component v_pred; zero: no-flow mean (same in all); v_pred=0 where undefined",
            "link_policies": reports}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--field-dir", type=Path, default=FIELD_DIR)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    zip_path = a.field_dir / "2MRS-NeuralNet.zip"
    field = load_field(a.field_dir)
    aux, windows = cf4_windows(field)
    result = {"schema": "htt.r104.cf4_2mrs_field/1", "field_zip_sha256": _sha(zip_path) if zip_path.exists() else None,
              "field_zip_expected_sha256": ZIP_SHA, "field_sha256": FIELD_SHA,
              "cf4_windows": None, "sixdf_holdout": sixdf_folds(field),
              "manticore_real_realizations": 0, "physical_Pi": None, "calibrated_p": None,
              "scope": "Single reconstruction; no posterior inter-group covariance; scores are working-model log predictive differences."}
    result["cf4_windows"] = windows
    result["courtois_cf4_internal"] = courtois_internal(aux)
    a.output.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
