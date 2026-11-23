"""Joint electric/magnetic VSH redshift curvature under actual shared spatial deletions."""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path

import numpy as np
from scipy.linalg import cholesky, solve_triangular

from scripts.r103 import gaia_frame_curvature as g


OUT = g.BASE / "R105_RESEARCH_20261124/GAIA_FRAME_PARITY.json"
MAG = np.r_[3:6,11:16,19:22,27:32]  # spin B1 and magnetic B2 in each curvature row
ELE = np.r_[0:3,6:11,16:19,22:27]


def joint_modes(y, cov):
    """Working-law factorization with paired electric/magnetic covariance, no tail law."""
    y = np.asarray(y, dtype=float)
    c = np.asarray(cov, dtype=float)
    if y.shape != (32,) or c.shape != (32,32) or not np.isfinite(y).all() or not np.isfinite(c).all():
        raise ValueError("need two complete finite R98 VSH curvature vectors and matching covariance")
    if not np.allclose(c,c.T,rtol=1e-11,atol=0):
        raise ValueError("asymmetric covariance")
    def energy(v, K):
        z = solve_triangular(cholesky(K, lower=True), v, lower=True)
        return float(z @ z)
    ym, ye = y[MAG], y[ELE]
    cm, ce, me = c[np.ix_(MAG,MAG)], c[np.ix_(ELE,ELE)], c[np.ix_(MAG,ELE)]
    # Conditional residual relative to zero electric + magnetic means as a working model.
    # Integrating out arbitrary electric means instead leaves the marginal magnetic statistic.
    L_e = cholesky(ce, lower=True)
    e_to_m = solve_triangular(L_e, me.T, lower=True).T
    fitted_m = e_to_m @ solve_triangular(L_e, ye, lower=True)
    c_cond = cm - e_to_m @ e_to_m.T
    c_cond = 0.5*(c_cond + c_cond.T)
    e_quad = energy(ye,ce)
    rm_quad = energy(ym-fitted_m,c_cond)
    full = energy(y,c)
    if abs(e_quad+rm_quad-full) > 5e-10 * max(1.,full):
        raise ArithmeticError("conditional/marginal factorization failed")
    L_m = cholesky(cm, lower=True)
    canonical = np.linalg.svd(solve_triangular(L_m, e_to_m, lower=True),compute_uv=False)
    a, b = np.arange(8), np.arange(8,16)
    c_cross = cm[np.ix_(a,b)]
    L1, L2 = cholesky(cm[:8,:8], lower=True), cholesky(cm[8:,8:],lower=True)
    W = solve_triangular(L2,solve_triangular(L1,c_cross,lower=True).T,lower=True)
    return {"electric_working_quadratic":e_quad,"magnetic_marginal_working_quadratic":energy(ym,cm),
            "magnetic_given_zero_mean_electric_working_quadratic":rm_quad,
            "joint_working_quadratic":full, "factorization_abs_residual":abs(full-e_quad-rm_quad),
            "magnetic_row_0_plus_row_1_discarding_crosscov":energy(ym[:8],cm[:8,:8])+energy(ym[8:],cm[8:,8:]),
            "largest_cross_curvature_magnetic_canonical_correlation":float(np.linalg.svd(W,compute_uv=False)[0]),
            "largest_electric_magnetic_canonical_correlation":float(canonical[0]),
            "joint_covariance_eigenvalue_ratio":float(np.linalg.cond(c)),
            "magnetic_joint_covariance":cm.tolist(),
            "magnetic_conditional_residual":(ym-fitted_m).tolist()}


def frame_shifted_rhs(fisher, rhs, z):
    # Known proper-motion coefficient offsets (microas/year), common across patches.
    # Translate the original normal-equation RHS in mas/year; use all off-diagonal entries of F.
    base = np.array([8.,-3.,2.,-4.,5.,6.])
    slope = np.array([-3.,4.,5.,2.,-7.,1.])
    shell_offsets = base[None] + np.asarray(z)[:, None]*slope[None]
    return rhs + np.einsum("spij,sj->spi",fisher[...,:6], shell_offsets)/1000


def run(source=g.SOURCE, cache_path=None):
    raw = Path(source).read_bytes()
    if sha256(raw).hexdigest() != g.SOURCE_SHA:
        raise ValueError("wrong R98 input receipt")
    src = json.loads(raw)
    ref = src["joint_160d_patch_covariance"]
    cache = Path(cache_path or ref["cache_path"])
    if sha256(cache.read_bytes()).hexdigest() != ref["sha256"]:
        raise ValueError("incorrect shared patch cache")
    with np.load(cache,allow_pickle=False) as obj:
        f = np.stack([obj[n+"__F"] for n in g.SHELLS])
        s = np.stack([obj[n+"__s"] for n in g.SHELLS])
    z = np.asarray(src["redshift_bin_medians"])
    w = g.curvature_rows(z)
    full, one, two, _ = g.shared_patch_refits(f,s)
    baseline = [w @ a for a in (full,one,two)]
    shifted = g.shared_patch_refits(f,frame_shifted_rhs(f,s,z))
    errors = [float(np.max(np.abs(cur - w @ inj))) for cur,inj in zip(baseline,shifted[:3])]
    if max(errors)>1e-9:
        raise ArithmeticError("affine frame changed curvature in an actual patch refit")
    y = baseline[0].reshape(-1)
    reports = {}
    for d, curves in enumerate(baseline[1:],1):
        C = g.delete_covariance(curves,len(one),d)
        reports[f"delete_{d}"] = joint_modes(y,C)
    return {"schema":"htt.r105.gaia_frame_parity/1", "sha256_r98_receipt":g.SOURCE_SHA,
            "sha256_patch_cache":ref["sha256"], "n_source_qualified":src["source_row_census"]["quaia_qualified"],
            "source_rows_reread_this_run":0, "joint_shells":list(g.SHELLS),"median_redshifts":z.tolist(),
            "n_delete_1":len(one),"n_delete_2":len(two),"proper_motion_units":"microarcsec/year per unit redshift squared",
            "magnetic_order":"spin x,y,z then five R98 B2 coefficients; lower then upper curvature triples",
            "source_rhs_affine_glide_spin_injection_max_abs_full_jk1_jk2":errors,
            "magnetic_vector":y[MAG].tolist(), "covariance_diagnostics":reports,
            "calibrated_p":None, "physical_Pi":None,"physical_GF":None,
            "scope":"B1/B2 are magnetic VSH sectors; their spatial inversion parities differ by ell. Covariance coupling between adjacent curvature rows and between electric/magnetic modes is measured from the same 48 patches. Conditional residual assumes zero physical electric means. Spatial deletions do not supply an independent noise or AGN-centroid ensemble."}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=g.SOURCE)
    p.add_argument("--cache", type=Path)
    p.add_argument("--output", type=Path, default=OUT)
    a=p.parse_args()
    obj=run(a.source,a.cache)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(obj,indent=2,allow_nan=False)+"\n")


if __name__=="__main__":
    main()
