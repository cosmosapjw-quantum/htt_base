"""C1 fixed-source baseline: original R69 Gaia VSH template and R67 accumulation."""
import argparse,hashlib,json,platform,resource,time
from pathlib import Path
import numpy as np
from astropy.io import fits
from threadpoolctl import threadpool_info
from scripts.r69.gaia_e2_b2 import prepare,templates
from scripts.r67.gaia_frame import accumulate_numpy

GAIA=Path("/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits")
PIN="e69cfff82f762c00d1d6a259c6d003fd20f805f3b1fcd4acc81d847c485120c0"

def sha_file(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--n",type=int,default=60000)
    parser.add_argument("--repeat",type=int,default=3)
    parser.add_argument("--out",type=Path,required=True)
    a=parser.parse_args()
    if not (1000<=a.n<=150000 and 2<=a.repeat<=15):raise ValueError("bounded benchmark input required")
    if sha_file(GAIA)!=PIN:raise RuntimeError("Gaia source hash mismatch")
    t0=time.perf_counter()
    with fits.open(GAIA,memmap=True) as f:
        z=f[1].data[:a.n]
        ra,dec,y1,y2,e1,e2,rho,valid,qual=prepare(z)
        good=valid&qual
        n=int(np.sum(good))
        _,B=templates(ra[good],dec[good])
        mu=np.column_stack((y1[good],y2[good]))
        e1,e2,rho=e1[good],e2[good],rho[good]
    inputs_sec=time.perf_counter()-t0
    accumulate_numpy(B,mu,e1,e2,rho)
    times=[];out=None
    for i in range(a.repeat):
        t=time.perf_counter();out=accumulate_numpy(B,mu,e1,e2,rho);times.append(time.perf_counter()-t)
    F,score,chisq=out
    payload={
      "schema":"htt.r79.gaia_source_gaussian_accumulate_baseline/1",
      "baseline_code":"scripts.r67.gaia_frame.accumulate + scripts.r69.gaia_e2_b2.templates/prepare",
      "source_path":str(GAIA),"source_sha256":PIN,
      "read_rows":a.n,"quality_valid_rows":n,"matrix_shape":list(B.shape),
      "input_seconds":inputs_sec,"repeat_seconds":times,
      "median_seconds":float(np.median(times)),"min_seconds":min(times),
      "F_trace":float(np.trace(F)),"F_norm":float(np.linalg.norm(F)),
      "score_norm":float(np.linalg.norm(score)),"chisq":float(chisq),
      "F_min_eigen":float(np.linalg.eigvalsh(F)[0]),
      "B_dtype":str(B.dtype),"maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
      "numpy":np.__version__,"python":platform.python_version(),"blas":threadpool_info(),
      "claim":"source-qualified original 16D weighted Gaia normal equations; not inferred physical shear",
      "benchmark_repeat":a.repeat,"native_compilation":"NOT_YET"
    }
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"n":n,"median_sec":payload["median_seconds"],"shape":B.shape,
      "F_min_eigen":payload["F_min_eigen"],"maxrss_kib":payload["maxrss_kib"]}))

if __name__=="__main__":main()
