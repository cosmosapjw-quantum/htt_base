"""R108 gaia lane: the R106 Gaia/Quaia curvature estimator with a fixed design, for mock and control fields.

Purpose
  Wraps scripts/r106/gaia_null_refit.py (unchanged R98 shell x patch normal equations, R103 curvature
  rows at the four shell median redshifts, shared-patch delete-one / delete-two jackknife covariance,
  R106 quadratic forms and the R104 per-draw exclusion rule) so that any proper-motion field y_i
  (mas/yr, one 2-vector per qualified Quaia source) can be pushed through the identical estimator.
  The design X (whitened VSH templates) and the per-source Fisher blocks are computed once; a new
  field only needs the whitened right-hand side Y = L^T y and 16 bincounts.
  Whitening W = L L^T (catalogue inverse covariance) implies that catalogue-covariance Gaussian noise
  has whitened components that are iid N(0,1); noise draws therefore need no per-source transform.
Inputs (pinned SHA-256, checked at load by the R106 helpers)
  Quaia x Gaia join  2fbaa40a8afe58066064efa8a7784ac508c5b2c67b41c779676eab7df8cf9ef4
  Gaia-CRF3 FITS     e69cfff82f762c00d1d6a259c6d003fd20f805f3b1fcd4acc81d847c485120c0
  R98 receipt        0a56bc358b6048f4b018d93d2b55be2f2ac5526e22191a44ca6a9f1148a9d800 (+ its patch cache)
  R106 GAIA_OBSERVED.json (replay target, sha recorded)
Units: input fields mas/yr; curvature vector microarcsec/yr per unit z^2; quadratic forms dimensionless.
Usage: library (load_context, stats_from_field, ...); `python -m scripts.r108.gaia_estimator replay`
  checks the R106 observed statistics bit-for-bit (relative 1e-10) through the fast path.
Deterministic.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

import numpy as np

from scripts.r103 import gaia_frame_curvature as g
from scripts.r106 import gaia_null_refit as r106
from scripts.r108.common import REPO, git_state, sha256_file

R106_OBSERVED = REPO / "docs/research_program/observational_publication_20261015/R106_RESEARCH_20261124/GAIA/GAIA_OBSERVED.json"
NPATCH, NSHELL, NCOEF = r106.NPATCH, r106.NSHELL, r106.NCOEF
RULE = r106.PRIMARY_RULE
HEADLINE = ("spin6", "magnetic16", "joint32", "glide6", "E2_10", "B2_10", "electric16")


def cholesky_factors(e1, e2, rho):
    """Lower factors of the per-source inverse covariance (same algebra as r106.whiten)."""
    inv = 1.0 / (1.0 - rho ** 2)
    w00 = inv / e1 ** 2
    w11 = inv / e2 ** 2
    w01 = -rho * inv / (e1 * e2)
    l00 = np.sqrt(w00)
    l10 = w01 / l00
    l11 = np.sqrt(w11 - l10 ** 2)
    return l00, l10, l11


def whiten_field(L, y):
    """Y = L^T y for fields y [n,2] in mas/yr."""
    l00, l10, l11 = L
    return np.column_stack((l00 * y[:, 0] + l10 * y[:, 1], l11 * y[:, 1]))


def rhs(X, Y, key):
    """Shell x patch right-hand sides s[4,48,16] = sum_i X_i^T Y_i (16 bincounts)."""
    s = np.empty((NSHELL * NPATCH, NCOEF))
    for j in range(NCOEF):
        s[:, j] = np.bincount(key, weights=X[:, 0, j] * Y[:, 0] + X[:, 1, j] * Y[:, 1], minlength=NSHELL * NPATCH)
    return s.reshape(NSHELL, NPATCH, NCOEF)


def stats(f, s, w, rules=(RULE,)):
    """R106 statistics for all 48 patches and the per-draw rule-selected exclusion."""
    allp = np.arange(NPATCH)
    y, c1, c2, meas, one_w = r106.refit_parts(f, s, w, allp)
    out = {"all48": {"vec": y, "jk1": r106.qforms(y, c1), "jk2": r106.qforms(y, c2)}}
    for r in rules:
        p = r106.select_exclusion(meas, one_w, r)
        ye, c1e, c2e = r106.refit(f, s, w, np.setdiff1d(allp, p))
        out[f"excl_selected__{r}"] = {"vec": ye, "jk1": r106.qforms(ye, c1e), "jk2": r106.qforms(ye, c2e),
                                      "pair": [int(p[0]), int(p[1])]}
    return out


def load_context(with_colour=True):
    """Pinned inputs, fixed design and the R98 replay check."""
    t0 = time.monotonic()
    src, meta, f_ref, s_ref, nsrc = r106.load_r98()
    z = np.asarray(src["redshift_bin_medians"])
    w = g.curvature_rows(z)
    inputs = {"r98_receipt": g.SOURCE_SHA, "r98_patch_cache": meta["sha256"],
              "quaia_crf3_join": r106.check_pinned(r106.JOIN, r106.JOIN_SHA, "quaia_crf3_join")}
    q = r106.load_quaia()
    X, Y = r106.whiten(q["ra"], q["dec"], q["y"], q["e1"], q["e2"], q["rho"])
    L = cholesky_factors(q["e1"], q["e2"], q["rho"])
    key = (q["shell"].astype(np.int64) * NPATCH + q["patch"]).astype(np.int64)
    f0, s0 = r106.group_normal(X, Y, q["shell"], q["patch"])
    s_fast = rhs(X, whiten_field(L, q["y"]), key)
    replay = {"F_max_rel": float(np.max(np.abs(f0 - f_ref)) / np.max(np.abs(f_ref))),
              "s_max_rel": float(np.max(np.abs(s0 - s_ref)) / np.max(np.abs(s_ref))),
              "fast_rhs_vs_group_normal_max_rel": float(np.max(np.abs(s_fast - s0)) / np.max(np.abs(s0)))}
    if max(replay.values()) > 1e-10:
        raise ArithmeticError(f"R98 / fast-path replay failed: {replay}")
    ctx = {"w": w, "z_med": z, "q": q, "X": X, "L": L, "key": key, "f": f0, "s_obs": s0, "nsrc": nsrc,
           "inputs": inputs, "replay": replay, "load_s": time.monotonic() - t0}
    if with_colour:
        inputs["gaia_crf3_fits"] = r106.check_pinned(r106.CRF3, r106.CRF3_SHA, "gaia_crf3_fits")
        crf3 = r106.load_crf3()
        bprp, hit = r106.quaia_bp_rp(q, crf3)
        if not hit.all():
            raise RuntimeError("Quaia rows without a CRF3 BP-RP match")
        ctx["bp_rp"] = bprp
        ctx["crf3"] = crf3
    return ctx


def stats_from_field(ctx, y=None, Ywhite=None, rules=(RULE,)):
    """Statistics of a field y [n,2] (mas/yr) or of an already whitened field."""
    if Ywhite is None:
        Ywhite = whiten_field(ctx["L"], y)
    return stats(ctx["f"], rhs(ctx["X"], Ywhite, ctx["key"]), ctx["w"], rules)


def r106_replay(ctx):
    """Observed statistics through the fast path versus R106 GAIA_OBSERVED.json."""
    obs = json.loads(R106_OBSERVED.read_text())
    st = stats(ctx["f"], ctx["s_obs"], ctx["w"])
    diff = {}
    for cfg, ref in (("all48", "all48"), (f"excl_selected__{RULE}", "excl_8_47")):
        for jk in ("jk1", "jk2"):
            for k in HEADLINE:
                a, b = st[cfg][jk][k], obs["configs"][ref][jk][k]
                diff[f"{cfg}__{jk}__{k}"] = abs(a - b) / abs(b)
    pair = st[f"excl_selected__{RULE}"]["pair"]
    vec_diff = float(np.max(np.abs(st["all48"]["vec"] - np.asarray(obs["configs"]["all48"]["curvature_vector_row0_row1"]))))
    ok = max(diff.values()) < 1e-10 and pair == list(r106.EXCLUDE) and vec_diff < 1e-9
    return {"max_rel_diff": max(diff.values()), "selected_pair": pair, "vec_max_abs_diff": vec_diff, "ok": ok,
            "r106_observed_sha256": sha256_file(R106_OBSERVED),
            "observed": {cfg: {jk: {k: st[cfg][jk][k] for k in HEADLINE} for jk in ("jk1", "jk2")}
                         for cfg in st}}


def _rel(pp):
    return str(pp.relative_to(REPO)) if pp.is_relative_to(REPO) else str(pp)


def main_script_identity():
    """Path and SHA-256 of the script run as __main__ (``python -m scripts.r108.X`` registers it only as __main__,
    so the scripts.* module scan below never sees it)."""
    p = getattr(sys.modules.get("__main__"), "__file__", None)
    if not p:
        return {"path": None, "sha256": None, "reason": "no __main__.__file__ (interactive or embedded interpreter)"}
    pp = Path(p).resolve()
    return {"path": _rel(pp), "sha256": sha256_file(pp)}


def provenance(extra_inputs=None):
    mods = {}
    for name, mod in sorted(sys.modules.items()):
        p = getattr(mod, "__file__", None)
        if p and (name == "scripts" or name.startswith("scripts.")):
            pp = Path(p).resolve()
            mods[_rel(pp)] = sha256_file(pp)
    main = main_script_identity()
    if main["path"] is not None:
        mods[main["path"]] = main["sha256"]
    return {"git": git_state(), "module_sha256": mods, "main_script": main, "argv": [sys.executable, *sys.argv],
            "extra_inputs": extra_inputs or {}}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=("replay",))
    ap.parse_args(argv)
    ctx = load_context(with_colour=False)
    rep = r106_replay(ctx)
    print(json.dumps({"replay": ctx["replay"], "r106": {k: rep[k] for k in ("max_rel_diff", "selected_pair",
                                                                             "vec_max_abs_diff", "ok")}}))
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
