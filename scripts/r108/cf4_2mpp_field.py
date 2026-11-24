"""R108 lane cf4, A2 (H02): project a CF3-independent mean velocity grid (2M++, Carrick et al. 2015) onto the R104
CF4 windows and the R103/R104 6dFGSv group-blocked held-out evaluation.

The projection is scripts/r104/cf4_2mrs_field.py (cf4_windows, sixdf_folds) with the field interpolation passed in
as a function, so that any Cartesian Galactic grid can be used.  Before a new field is projected, the same code is
run on the R104 2MRS-NeuralNet grid and must reproduce R104 CF4_2MRS_FIELD.json (36 components, per-window missing
weights, PGC/PGC1 fold sums) to REPLAY_TOL: this is the reproduction gate.

2M++ grid convention (Carrick et al. 2015, MNRAS 450, 317; files twompp_density.npy (257^3) and
twompp_velocity.npy (3,257,257,257), Galactic Cartesian, observer at cell (128,128,128)).  The box side, the
velocity units/scaling (whether beta*=0.43 is already applied) and the axis order are set by the README on the
download portal; they are command-line parameters here and the run records them.  The predicted CMB-frame velocity
is v = s_beta * v_grid + V_ext, V_ext = (89, -131, 17) km/s (Galactic Cartesian), transported to redshift z by
g(z)/g(0) as in R104.  No inter-group posterior covariance is estimated from a mean field.

Inputs
  R104 field (gate): ~/Downloads/htt_r104_fields/2mrs_nn/{x,y,z}Velocity.npy (SHA-256 in scripts/r104/cf4_2mrs_field.py)
  R104 reference:    docs/.../R104_DATA_SOLVER_CONTINUATION_20261124/CF4_2MRS_FIELD.json
  2M++ field:        --velocity PATH (twompp_velocity.npy), optional --expected-sha256
  CF4/6dFGSv inputs: as read by scripts.r104.cf4_2mrs_field (R98 catalogue, R100 intake)

Units: velocities km/s; grid box in h^-1 Mpc; window coefficients in the R98 natural-log distance basis; fold
scores in nats.

Usage (repo root, PYTHONPATH=.:htt:htt/src):
  python -B -m scripts.r108.cf4_2mpp_field --gate-only --output docs/.../CF4/TWOMPP_FIELD.json
  python -B -m scripts.r108.cf4_2mpp_field --velocity ~/Downloads/htt_r108/cf4/D04/twompp_velocity.npy \
      --box-mpch 400 --beta-scale 1 --output docs/.../CF4/TWOMPP_FIELD.json

Deterministic.  Claim class: NUMERICAL (gate) / CONDITIONAL on the README grid convention (2M++ projection).
"""
from __future__ import annotations

import argparse
import json
import shlex
import sys
import time
from pathlib import Path

import numpy as np

from scripts.r108.common import git_state, sha256_file, write_json

ROOT = Path(__file__).resolve().parents[2]
R104_REF = ROOT / "docs/research_program/observational_publication_20261015/R104_DATA_SOLVER_CONTINUATION_20261124/CF4_2MRS_FIELD.json"
OUT_DEFAULT = ROOT / "docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/CF4/TWOMPP_FIELD.json"
RECEIPTS = Path.home() / "Downloads/htt_r108/cf4/RECEIPTS.jsonl"
REPLAY_TOL = 1e-8
V_EXT_C15 = (89., -131., 17.)


class Grid:
    """Cell-centred Cartesian grid: position x (h^-1 Mpc, Galactic) of index i is (i - centre) * step."""

    def __init__(self, field, step, centre, rmax):
        self.field = np.asarray(field, float)          # (n, n, n, 3)
        self.n = self.field.shape[0]
        if self.field.shape != (self.n, self.n, self.n, 3):
            raise ValueError("field must be (n, n, n, 3)")
        self.step, self.centre, self.rmax = float(step), float(centre), float(rmax)

    def interpolate(self, x_h):
        """Trilinear interpolation; a point is defined only if inside the grid, r <= rmax and all 8 corners finite."""
        u = np.asarray(x_h, float) / self.step + self.centre
        base = np.floor(u).astype(int)
        hi = self.n - 2
        inside = np.all((base >= 0) & (base <= hi), axis=1) & (np.linalg.norm(x_h, axis=1) <= self.rmax)
        b = np.clip(base, 0, hi)
        frac = u - b
        vel = np.zeros((len(u), 3))
        finite = inside.copy()
        for corner in np.ndindex(2, 2, 2):
            c = np.array(corner)
            w = np.prod(np.where(c, frac, 1. - frac), axis=1)
            v = self.field[b[:, 0] + c[0], b[:, 1] + c[1], b[:, 2] + c[2]]
            finite &= np.isfinite(v).all(axis=1)
            vel += w[:, None] * np.where(np.isfinite(v), v, 0.)
        vel[~finite] = np.nan
        return vel, finite


def r104_grid():
    from scripts.r104 import cf4_2mrs_field as r104
    return Grid(r104.load_field(), r104.STEP, r104.CENTRE, r104.RMAX)


def twompp_grid(path, box_mpch, beta_scale, vext, axis_order, rmax):
    v = np.load(path, allow_pickle=False, mmap_mode="r")
    if v.ndim != 4 or 3 not in (v.shape[0], v.shape[-1]):
        raise ValueError(f"unexpected 2M++ velocity shape {v.shape}")
    comp_first = v.shape[0] == 3
    n = v.shape[1] if comp_first else v.shape[0]
    arr = np.moveaxis(np.asarray(v, float), 0, -1) if comp_first else np.asarray(v, float)
    if axis_order == "zyx":
        arr = np.transpose(arr, (2, 1, 0, 3))
    arr = beta_scale * arr + np.asarray(vext, float)[None, None, None, :]
    step = box_mpch / (n - 1)
    return Grid(arr, step, (n - 1) / 2., rmax), dict(shape=list(v.shape), dtype=str(v.dtype), n=n, step_mpch=step,
                                                       centre_index=(n - 1) / 2., components_first=comp_first)


def cf4_windows(grid):
    """scripts.r104.cf4_2mrs_field.cf4_windows with the interpolation of `grid`."""
    from scripts.r103 import manticore_cf4_pv as pv
    from scripts.r104 import cf4_2mrs_field as r104
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
    ng = r104.to_galactic(n[j])
    vel, ok = grid.interpolate(ng * (r * r104.H_LITTLE)[:, None])
    radius_ok = r * r104.H_LITTLE <= grid.rmax
    vlos = np.where(ok, np.einsum("ij,ij->i", np.nan_to_num(vel), ng), 0.) * pv.velocity_growth_ratio(g, g0)
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

    return {"n_groups": int(len(j)), "n_radius_le_rmax": int(radius_ok.sum()), "n_common": int(ok.sum()),
            "n_radius_pass_nonfinite_neighbour": int((radius_ok & ~ok).sum()), "g0_kms_per_Mpc": g0,
            "vlos_common_kms": {"mean": float(vlos[ok].mean()), "rms": float(np.sqrt((vlos[ok] ** 2).mean()))},
            "missing_abs_influence_fraction_per_window": miss_win.tolist(),
            "missing_abs_influence_fraction_36": miss_comp.tolist(),
            "observed_coefficients_full_36": (A @ y).tolist(), "observed_coefficients_common_36": obs_c.tolist(),
            "b_field_common_refit_36": b_common.tolist(), "b_field_fullA_zero_filled_36": b_full_zero.tolist(),
            "chi2_measurement_cov_common": {"observed": chi2(obs_c), "observed_minus_field": chi2(obs_c - b_common),
                                            "dof": 36, "covariance": "R98 joint measurement covariance only"}}


def sixdf_folds(grid):
    """scripts.r104.cf4_2mrs_field.sixdf_folds with the interpolation of `grid`."""
    from scripts.r103 import cf4_shared_field_holdout as h
    from scripts.r104 import cf4_2mrs_field as r104
    r100, r99 = h.r100, h.r99
    t2 = r100.load_cf4_table2()
    six = r100.load_sixdf_pv()
    match = h.sixdf_match_ambiguity_policies(t2, six, arcsec=15., dv_kms=500.)
    inc = match["policies"]["unique_only_r101"]["included"]
    closest = match["closest_table2_indices"]
    mark = np.where(inc, six["delta_d"], np.nan)
    cz = six["cz_gal"]
    x = np.column_stack((np.ones(len(cz)), cz / 1e4 - 1.1, six["delta_d"], six["is_grouped"]))
    offsets = np.array([-300., -100., 0., 100., 300.])
    sci, *_ = r100.old._load_r30_and_bridge()
    r, g, *_ = sci.background(cz / r100.C, 64)
    g0 = float(sci.background(np.array([0.]), 64)[1][0])
    ng = r104.to_galactic(r104.hp.ang2vec(six["ra"], six["dec"], lonlat=True))
    vel, ok = grid.interpolate(ng * (r * r104.H_LITTLE)[:, None])
    vpred = np.where(ok, np.einsum("ij,ij->i", np.nan_to_num(vel), ng), 0.) * (g / g0)

    def means(offset):
        return np.array([r99.finite_shift(sci, cz / r100.C, np.arctanh((u + offset) / r100.C), "bolometric")
                         / (5. * r100.MAG) for u in offsets])

    m0, m1 = means(0.), means(vpred)
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
            o0 = h.selected_probit_holdout(mark, m0, six["epsilon_d"], icpt, b[2], np.full(len(offsets), .2), included=inc, train=train)
            o1 = h.selected_probit_holdout(mark, m1, six["epsilon_d"], icpt, b[2], np.full(len(offsets), .2), included=inc, train=train)
            o2 = h.selected_probit_holdout(mark, m2, six["epsilon_d"], icpt, b[2], np.ones(1), included=inc, train=train)
            folds.append({"field_only_fresh_minus_zero": o2["fresh_minus_zero"], "fold": fold, "n_test": int(len(ite)),
                          "n_test_selected": int(inc[ite].sum()),
                          "before_fresh_minus_zero": o0["fresh_minus_zero"], "before_shared_minus_zero": o0["shared_minus_zero"],
                          "after_fresh_minus_zero": o1["fresh_minus_zero"], "after_shared_minus_zero": o1["shared_minus_zero"]})
        reports[key] = {"folds": folds, **{f"cv_{k}": sum(f[k] for f in folds) for k in
                        ("before_fresh_minus_zero", "before_shared_minus_zero", "after_fresh_minus_zero",
                         "after_shared_minus_zero", "field_only_fresh_minus_zero")}}
    return {"n_parent": int(len(mark)), "n_selected": int(inc.sum()), "n_field_defined": int(ok.sum()),
            "n_field_undefined_set_to_zero": int((~ok).sum()),
            "vpred_kms": {"mean": float(vpred[ok].mean()), "rms": float(np.sqrt((vpred[ok] ** 2).mean()))},
            "offset_convention": "after: mixture over common radial speed u + field v_pred(galaxy); field_only: single "
                                 "component v_pred; zero: no-flow mean; v_pred=0 where undefined",
            "link_policies": reports}


def gate(windows, six, ref):
    """Largest absolute difference against R104 CF4_2MRS_FIELD.json."""
    rw, rs = ref["cf4_windows"], ref["sixdf_holdout"]
    pairs = [("missing_abs_influence_fraction_36", "missing_abs_influence_fraction_36"),
             ("observed_coefficients_common_36", "observed_coefficients_common_36"),
             ("b_field_common_refit_36", "b_2mrs_common_refit_36"),
             ("b_field_fullA_zero_filled_36", "b_2mrs_fullA_zero_filled_36")]
    worst = {a: float(np.max(abs(np.asarray(windows[a]) - np.asarray(rw[b])))) for a, b in pairs}
    worst["n_common"] = abs(windows["n_common"] - rw["n_common"])
    for key in ("pgc", "pgc1"):
        for k in ("cv_before_fresh_minus_zero", "cv_before_shared_minus_zero", "cv_after_fresh_minus_zero",
                  "cv_after_shared_minus_zero", "cv_field_only_fresh_minus_zero"):
            worst[f"{key}:{k}"] = abs(six["link_policies"][key][k] - rs["link_policies"][key][k])
    return dict(max_abs_difference=worst, tolerance=REPLAY_TOL, passed=all(v <= REPLAY_TOL for v in worst.values()))


def d04_receipts():
    out = []
    if RECEIPTS.is_file():
        for line in RECEIPTS.read_text().splitlines():
            rec = json.loads(line)
            if rec.get("id") == "D04":
                out.append({k: rec.get(k) for k in ("name", "url", "final_url", "bytes", "sha256", "status", "error",
                                                    "fetched_at_utc", "route")})
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--output", type=Path, default=OUT_DEFAULT)
    p.add_argument("--gate-only", action="store_true")
    p.add_argument("--velocity", type=Path)
    p.add_argument("--expected-sha256")
    p.add_argument("--box-mpch", type=float, default=400.)
    p.add_argument("--beta-scale", type=float, default=1.,
                   help="multiplier on the stored grid (1 if the README says beta*=0.43 is already applied, else 0.43)")
    p.add_argument("--vext", type=float, nargs=3, default=list(V_EXT_C15))
    p.add_argument("--axis-order", choices=("xyz", "zyx"), default="xyz")
    p.add_argument("--rmax", type=float, default=200.)
    p.add_argument("--trace-opens", type=Path, default=None,
                   help="record every file opened by the run (JSON lines) for the pre-existing-input receipts")
    a = p.parse_args(argv)
    if a.trace_opens:
        from scripts.r108.cf4_receipts import install_open_trace
        install_open_trace(a.trace_opens, "scripts.r108.cf4_2mpp_field")
    t0 = time.time()
    ref = json.loads(R104_REF.read_text())
    g104 = r104_grid()
    w104, s104 = cf4_windows(g104), sixdf_folds(g104)
    gt = gate(w104, s104, ref)
    payload = dict(schema="htt.r108.cf4.twompp_field/1", git=git_state(),
                   script=dict(path=str(Path(__file__).resolve().relative_to(ROOT)), sha256=sha256_file(Path(__file__))),
                   command=" ".join(shlex.quote(x) for x in [sys.executable, "-B", "-m", "scripts.r108.cf4_2mpp_field",
                                                             *sys.argv[1:]]),
                   input_sha256={"r104_reference": sha256_file(R104_REF)}, r104_reproduction_gate=gt,
                   physical_Pi=None, calibrated_p=None, inter_group_posterior_covariance=None)
    if not gt["passed"]:
        payload["status"] = "GATE_FAILED"
        write_json(a.output, payload)
        raise SystemExit(f"R104 reproduction gate failed: {gt}")
    if a.gate_only or a.velocity is None or not a.velocity.is_file():
        payload.update(status="BLOCKED", classification="BLOCKED",
                       missing_input=dict(item="D04", files=["twompp_velocity.npy", "twompp_density.npy",
                                                             "README (grid box, units, beta scaling, axis order)"],
                                          portal="https://git.aquila-consortium.org/guilhem_lavaux/cosmicflows-deployer/raw/branch/main/download/index.html",
                                          receipts=d04_receipts()),
                       note="projection code passed the R104 reproduction gate and is ready; no 2M++ grid was obtained")
        payload["wall_seconds"] = time.time() - t0
        write_json(a.output, payload)
        print(json.dumps(dict(status=payload["status"], gate=gt["passed"]), indent=1))
        return 0
    sha = sha256_file(a.velocity)
    if a.expected_sha256 and sha != a.expected_sha256:
        raise ValueError("2M++ velocity SHA-256 mismatch")
    grid, meta = twompp_grid(a.velocity, a.box_mpch, a.beta_scale, a.vext, a.axis_order, a.rmax)
    lg_cell = grid.field[int(meta["centre_index"])][int(meta["centre_index"])][int(meta["centre_index"])]
    w, s6 = cf4_windows(grid), sixdf_folds(grid)
    payload.update(status="COMPUTED", classification="CONDITIONAL",
                   conditional_on="2M++ README grid convention as passed on the command line",
                   input_sha256=dict(payload["input_sha256"], twompp_velocity=sha),
                   grid=dict(meta, box_mpch=a.box_mpch, beta_scale=a.beta_scale, vext_kms=a.vext, axis_order=a.axis_order,
                             rmax_mpch=a.rmax, velocity_at_observer_cell_kms=lg_cell.tolist()),
                   cf4_windows=w, sixdf_holdout=s6,
                   r104_2mrs_for_comparison=dict(
                       sixdf={k: {kk: vv for kk, vv in v.items() if kk != "folds"}
                              for k, v in ref["sixdf_holdout"]["link_policies"].items()},
                       n_common=ref["cf4_windows"]["n_common"]),
                   wall_seconds=time.time() - t0)
    write_json(a.output, payload)
    print(json.dumps(dict(status=payload["status"], gate=gt["passed"]), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
