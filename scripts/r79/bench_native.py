"""R79 actual-source accuracy and speed: original Gaia VSH and CF4 group sky.

No new cosmic shear fit or physical source mixing. Source access read-only.
"""
import argparse,hashlib,json,platform,resource,time
from pathlib import Path
import numpy as np
from astropy.io import fits
from scripts.r69.gaia_e2_b2 import prepare,templates
from scripts.r67.gaia_frame import accumulate as old_accumulate
from htt.obsstat.pre_dag_fast import accumulate_gaia,hemisphere_moments

GAIA=Path("/mnt/extdrive/workdir/raw/observational_bundles/Gaia_CRF3_astrometry/gaia_crf3_astrometry_full.fits")
CF4=Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
PIN_GAIA="e69cfff82f762c00d1d6a259c6d003fd20f805f3b1fcd4acc81d847c485120c0"
PIN_CF4="b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94"

def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def benchmark(call,repeat=5):
    call()
    times=[]
    out=None
    for _ in range(repeat):
        start=time.perf_counter()
        out=call()
        times.append(time.perf_counter()-start)
    return out,{"runs_seconds":times,"median_seconds":float(np.median(times)),
                "minimum_seconds":float(min(times))}

def load_gaia(nrows):
    # Gaia input is sky-sorted. A first-row-only sample is geometrically
    # ill-conditioned (F condition ~866184) and unrepresentative of the
    # all-sky 16D scientific fit. Stratify by original row index instead.
    with fits.open(GAIA,memmap=True) as f:
        table=f[1].data
        z=table[np.linspace(0,len(table)-1,nrows,dtype=np.int64)]
        ra,dec,y1,y2,e1,e2,rho,valid,qual=prepare(z)
        selected=valid&qual
        _,B=templates(ra[selected],dec[selected])
        yy=np.column_stack((y1[selected],y2[selected]))
        return B,yy,e1[selected],e2[selected],rho[selected]

def load_cf4():
    values=[]
    for line in CF4.open():
        try:
            r=float(line[21:26]);l=np.deg2rad(float(line[101:109]));b=np.deg2rad(float(line[110:118]))
            if r>0 and np.isfinite(r+l+b):
                values.append((r,np.cos(b)*np.cos(l),np.cos(b)*np.sin(l),np.sin(b)))
        except (ValueError,IndexError):
            continue
    a=np.asarray(values,dtype=np.float64)
    if a.shape!=(38053,4):raise ValueError("full CF4 group count source changed")
    sel=(a[:,0]>=40)&(a[:,0]<400)
    n=a[sel,1:]
    lon=np.deg2rad(264.021);lat=np.deg2rad(48.253)
    axis=np.array([np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)])
    return n,axis,len(a)

def compare_gaia(a,b):
    F,score,chi=a
    f,s,c=b
    def rel(x,y):
        return float(np.linalg.norm(np.asarray(x)-np.asarray(y))/
                     max(np.linalg.norm(np.asarray(x)),1e-200))
    diffs={"F_relative_frobenius":rel(F,f),
           "score_relative_2norm":rel(score,s),
           "chisq_relative":rel(chi,c),
           "solution_beta_relative":rel(np.linalg.solve(F,score),
                                        np.linalg.solve(f,s)),
           "covariance_relative":rel(np.linalg.inv(F),np.linalg.inv(f)),
           "F_min_eigen_relative":rel(np.linalg.eigvalsh(F)[0],
                                     np.linalg.eigvalsh(f)[0])}
    return diffs

def compare_hemisphere(a,b):
    result={}
    for field in ("weights","means","second"):
        aa=np.asarray(a[field]);bb=np.asarray(b[field])
        result[field+"_maximum_abs"]=float(np.max(np.abs(aa-bb)))
        result[field+"_relative_l2"]=float(np.linalg.norm(aa-bb)/
                          max(np.linalg.norm(aa),1e-200))
    if list(a["counts"])!=list(b["counts"]):
        raise ValueError("CF4 source mask source-count disagreement")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--gaia-so",type=Path,required=True)
    p.add_argument("--hemi-so",type=Path,required=True)
    p.add_argument("--n",type=int,default=60000)
    p.add_argument("--repeat",type=int,default=5)
    args=p.parse_args()
    if not 1000<=args.n<=150000 or not 3<=args.repeat<=10:
        raise ValueError("bounded original source benchmark required")
    if sha(GAIA)!=PIN_GAIA or sha(CF4)!=PIN_CF4:
        raise ValueError("original Gaia/CF4 bytes changed")
    B,y,e1,e2,rho=load_gaia(args.n)
    inputs=(B,y,e1,e2,rho)
    ref,raw=benchmark(lambda:old_accumulate(*inputs),args.repeat)
    npout,python=benchmark(lambda:accumulate_gaia(*inputs),args.repeat)
    native,native1=benchmark(lambda:accumulate_gaia(*inputs,native_lib=args.gaia_so,threads=1),args.repeat)
    native4,native4t=benchmark(lambda:accumulate_gaia(*inputs,native_lib=args.gaia_so,threads=4),args.repeat)
    native8,native8t=benchmark(lambda:accumulate_gaia(*inputs,native_lib=args.gaia_so,threads=8),args.repeat)
    errors={name:compare_gaia(ref,x) for name,x in
             (("python",npout),("C++1",native),("C++4",native4),("C++8",native8))}
    for name,v in errors.items():
        if max(v.values())>2e-11:
            raise AssertionError(f"{name} Gaia numerical parity exceeded 2e-11: {v}")
    dirs,axis,n_all=load_cf4()
    truew=np.ones(len(dirs))
    covref,covpy=benchmark(lambda:hemisphere_moments(dirs,axis,weights=truew),args.repeat)
    covnat,covna=benchmark(lambda:hemisphere_moments(dirs,axis,weights=truew,native_lib=args.hemi_so),args.repeat)
    cerr=compare_hemisphere(covref,covnat)
    if max(cerr.values())>3e-11:raise AssertionError(f"Fortran group source parity failed: {cerr}")
    assert abs(covref["second"][0].trace()-1)<2e-13
    assert abs(covref["second"][1].trace()-1)<2e-13
    out={"schema":"htt.r79.actual_source_precision_speed_comparison/1",
     "scope":"Original selected Gaia 16D VSH and CF4 full table4 group mask only, not cross-probe inference",
     "source_sha256":{"Gaia_CRF3_raw":PIN_GAIA,"CF4_table4_raw":PIN_CF4},
     "Gaia_quality_selected_count":len(B),"Gaia_source_rows_read":args.n,
     "Gaia_sampling":"uniform_row_index_stride_across_full_original_Gaia_catalogue; no sky-reweighted source inference",
     "Gaia_original_F_condition":float(np.linalg.cond(ref[0])),
     "Gaia_original_numpy":raw,"Gaia_new_numpy":python,
     "Gaia_native_cpp_1":native1,"Gaia_native_cpp_4":native4t,"Gaia_native_cpp_8":native8t,
     "Gaia_native_to_original_median_speedup_1":raw["median_seconds"]/native1["median_seconds"],
     "Gaia_native_to_original_median_speedup_4":raw["median_seconds"]/native4t["median_seconds"],
     "Gaia_native_to_original_median_speedup_8":raw["median_seconds"]/native8t["median_seconds"],
     "Gaia_all_parity_errors":errors,
     "CF4_full_group_count":n_all,"CF4_mask_40_400_count":len(dirs),
     "CF4_numpy_hemisphere":covpy,"CF4_native_fortran_hemisphere":covna,
     "CF4_native_to_numpy_median_speedup":covpy["median_seconds"]/covna["median_seconds"],
     "CF4_hemisphere_parity":cerr,
     "CF4_hemisphere_counts":covref["counts"].tolist(),
     "repetitions":args.repeat,
     "peak_maxrss_kib":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
     "python":platform.python_version(),"numpy":np.__version__,
     "native_preflight_claim":"optional verified mathematical kernel, not source matched cosmological parameter estimate",
     "changed_original_R60_R78_source_code":False}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"Gaia_n":len(B),"Cpp1_x":out["Gaia_native_to_original_median_speedup_1"],
      "Cpp4_x":out["Gaia_native_to_original_median_speedup_4"],
      "Cpp8_x":out["Gaia_native_to_original_median_speedup_8"],
      "Fortran_x":out["CF4_native_to_numpy_median_speedup"],
      "max_Gaia_parity":max(max(z.values()) for z in errors.values()),
      "max_CF4_parity":max(cerr.values())}))
if __name__=="__main__":main()
