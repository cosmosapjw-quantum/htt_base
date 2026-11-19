"""R79 C7. Full original Gaia-CRF3 quality/mask and 192-region score replay.

Use source-defined R69 templates/selection and compare actual original saved
16D fits and patch-sandwich to a newly compiled optional C++ accumulator.
No inferred physical shear/vorticity or release null.
"""
import argparse,hashlib,json,platform,resource,time
from pathlib import Path
import numpy as np
from astropy.io import fits
from scripts.r69.gaia_e2_b2 import prepare,templates,fit_case
from htt.obsstat.pre_dag_fast import accumulate_gaia

GAIA=Path("/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits")
OLD=Path("docs/research_program/observational_publication_20261015/R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GAIA_E1B1E2B2.json")
PIN="e69cfff82f762c00d1d6a259c6d003fd20f805f3b1fcd4acc81d847c485120c0"

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):h.update(b)
    return h.hexdigest()

def mask_and_templates(z):
    ra,dec,y1,y2,e1,e2,rho,valid,qual=prepare(z)
    if not np.any(valid):
        return None
    _,B=templates(ra[valid],dec[valid])
    yy=np.column_stack([y1[valid],y2[valid]])
    e1,e2,rho=e1[valid],e2[valid],rho[valid]
    q=qual[valid]
    decv=dec[valid]
    masks={"all":np.ones(np.sum(valid),bool),"quality":q,
           "quality_north":q&(decv>=0),"quality_south":q&(decv<0)}
    return B,yy,e1,e2,rho,ra[valid],decv,masks

def rel(x,y):
    a=np.asarray(x,dtype=float)
    b=np.asarray(y,dtype=float)
    return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-200))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--lib",required=True,type=Path)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--chunk",type=int,default=65536)
    p.add_argument("--threads",type=int,default=8)
    p.add_argument("--patch",action="store_true")
    args=p.parse_args()
    if not 1024<=args.chunk<=65536 or not 1<=args.threads<=16:
        raise ValueError("bounded source-memory budget required")
    if sha(GAIA)!=PIN:raise ValueError("original Gaia source hash changed")
    old=json.loads(OLD.read_text())
    if old["actual_input"]!=str(GAIA):raise ValueError("original R69 receipt input path differs")
    labels=("all","quality","quality_north","quality_south")
    accum={k:{"F":np.zeros((16,16)),"score":np.zeros(16),"chisq":0.,"N":0} for k in labels}
    t0=time.perf_counter()
    with fits.open(GAIA,memmap=True) as f:
        table=f[1].data
        for start in range(0,len(table),args.chunk):
            item=mask_and_templates(table[start:start+args.chunk])
            if item is None:continue
            B,yy,e1,e2,rho,ra,dec,masks=item
            for k,m in masks.items():
                if not np.any(m):continue
                Fi,score,chi=accumulate_gaia(
                    B[m],yy[m],e1[m],e2[m],rho[m],native_lib=args.lib,
                    threads=args.threads)
                a=accum[k]
                a["F"]+=Fi;a["score"]+=score;a["chisq"]+=chi;a["N"]+=int(np.sum(m))
    fit_seconds=time.perf_counter()-t0
    fits_new={k:fit_case(v) for k,v in accum.items()}
    comparisons={}
    for key in labels:
        fresh=fits_new[key];saved=old["results"][key]
        assert fresh["n_sources"]==saved["n_sources"],(key,fresh["n_sources"],saved["n_sources"])
        assert fresh["rank"]==saved["rank"]==16
        tests={
            "beta_coeff_relative":rel(fresh["coefs_microasyr"],saved["coefs_microasyr"]),
            "formal_cov_relative":rel(fresh["formal_cov_microasyr2"],saved["formal_cov_microasyr2"]),
            "chi2_per_dof_abs":abs(fresh["chi2_per_dof_working"]-saved["chi2_per_dof_working"]),
            "E2_shape_chi_abs":abs(fresh["E2_shape_chi"]-saved["E2_shape_chi"]),
            "F_condition_relative":rel(fresh["F_condition"],saved["F_condition"])}
        if max(tests.values())>2e-9:
            raise AssertionError(f"source R69 replay mismatch: {key} {tests}")
        comparisons[key]={"n":fresh["n_sources"],"errors":tests,
            "E2_shape_chi":fresh["E2_shape_chi"],
            "F_condition":fresh["F_condition"]}
    patch_comparison=None
    patch_seconds=0.
    if args.patch:
        # Exactly R69 original region-level residual-score sandwich, bounded
        # second pass after fitted quality coefficients. No resampling null.
        import healpy as hp
        start_patch=time.perf_counter()
        cov=np.linalg.inv(accum["quality"]["F"])
        beta=np.asarray(fits_new["quality"]["coefs_microasyr"])/1000
        score_patch=np.zeros((192,16))
        with fits.open(GAIA,memmap=True) as f:
            table=f[1].data
            for start in range(0,len(table),args.chunk):
                ra,dec,y1,y2,e1,e2,rho,valid,qual=prepare(table[start:start+args.chunk])
                m=valid&qual
                if not np.any(m):continue
                _,B=templates(ra[m],dec[m])
                yy=np.column_stack([y1[m],y2[m]])
                residual=yy-np.einsum("nij,j->ni",B,beta)
                e1,e2,rho=e1[m],e2[m],rho[m]
                inv=1/(1-rho*rho)
                w0=inv*(residual[:,0]/e1**2-rho*residual[:,1]/(e1*e2))
                w1=inv*(residual[:,1]/e2**2-rho*residual[:,0]/(e1*e2))
                sourcescore=B[:,0,:]*w0[:,None]+B[:,1,:]*w1[:,None]
                idx=hp.ang2pix(4,np.pi/2-dec[m],ra[m]%(2*np.pi))
                for j in range(16):
                    score_patch[:,j]+=np.bincount(idx,weights=sourcescore[:,j],minlength=192)
        cpatch=cov@score_patch.T@score_patch@cov
        expected=np.asarray(old["results"]["quality"]["spatial_patch_192_cov_microasyr2"])/1e6
        error=rel(cpatch,expected)
        if error>2e-8:raise AssertionError(f"R69 original patch covariance differs by {error}")
        patch_seconds=time.perf_counter()-start_patch
        patch_comparison={"relative_covariance":error,
                          "patch_192_cov_positive_min_eigen":float(np.linalg.eigvalsh(cpatch)[0]),
                          "source":"same original Gaia catalogue/quality mask and R69 patch residual score"}
    out={
        "schema":"htt.r79.gaia_16D_full_source_replay/1",
        "original_source_sha256":PIN,
        "original_R69_saved_result_sha256":sha(OLD),
        "source_total_rows":int(sum(v["N"] for k,v in accum.items() if k=="all")),
        "selection":"original R69 valid, RUWE<1.4, 8+ visibility periods, nonduplicated source",
        "covariance":"same 2x2 per-source astrometric statistical error, no LSS/scanning calibration",
        "operator":"original R69 tangent templates; new C++ compensated normal equations + original R69 fit_case",
        "chunk_rows":args.chunk,"threads":args.threads,"library_sha256":sha(args.lib),
        "original_saved_fit_comparison":comparisons,
        "original_saved_patch_covariance_comparison":patch_comparison,
        "native_fit_elapsed_seconds":fit_seconds,
        "original_patch_second_pass_seconds":patch_seconds,
        "maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "numpy":np.__version__,"python":platform.python_version(),
        "scientific_limits":"Original source processing reproduced but no new proper-motion cosmology, cosmic shear, vorticity, tilted Bianchi or source-calibrated null."
    }
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"n_full":out["source_total_rows"],"fit_s":fit_seconds,
                      "patch_s":patch_seconds,
                      "max_error":max(max(v["errors"].values()) for v in comparisons.values()),
                      "patch":patch_comparison, "rss_mib":out["maxrss_kib"]/1024}))
if __name__=="__main__":main()
