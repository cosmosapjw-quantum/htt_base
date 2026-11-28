"""Execute the fixed R120 native family-manifold plan with source identity checks."""
import argparse,gzip,hashlib,json,math,os,shutil,subprocess,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import initial_geometry,lie_text
from scripts.r120.plan_grid import make

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/"docs/research_program/observational_publication_20261015/R120_NATIVE_FAMILY_MANIFOLD_20261128"
R114=DOC.parent/"R114_LOCAL_UNIVERSAL_LIE_SKY_20261125/C1_HARMONIC_LONG_ATLAS.json"

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def sources(scratch):
    p=json.loads((DOC/"R7_NATIVE_PILOT.json").read_text());c=json.loads((DOC/"C1.json").read_text())
    if sha(DOC/"R7_NATIVE_PILOT.json")!=c["r7_receipt_sha256"] or sha(DOC/"SOURCE_LOCK.json")!=c["source_lock_sha256"]:
        raise ValueError("source receipt changed")
    binary=scratch/"target/release/examples/homogeneous_sky";table=scratch/"merged_ZERO.tsv"
    if sha(binary)!=c["binary_sha256"]["bass"] or sha(table)!=c["opacity_sha256"]:
        raise ValueError("native binary or history mismatch")
    x=json.loads(R114.read_text());a=x["cosmology_anchors"]
    ts=np.loadtxt(table,skiprows=1)
    if ts.ndim!=2 or ts.shape[1]!=2 or not np.isfinite(ts).all() or ts[0,0]!=0 or abs(ts[-1,0]-a["duration"])>1e-12 or np.any(np.diff(ts[:,0])<=0) or np.any(ts[:,1]<0):
        raise ValueError("invalid ionization history")
    return binary,table,x,p

def execute(scratch,mode,workers=4):
    plan=json.loads((DOC/"SCAN_PLAN.json").read_text())
    if plan!=make():raise ValueError("scan plan changed")
    binary,table,ref,pilot=sources(scratch);a=ref["cosmology_anchors"]
    lmax=plan["ell_max"]; stop=math.log(1601/21)
    points={p["name"]:p for p in plan["points"]}
    if mode=="smoke":names=["VIh"];steps=plan["base_steps"];hl=plan["base_harmonic_lmax"];grid=plan["base_los_grid"]
    elif mode=="base":names=list(points);steps=plan["base_steps"];hl=plan["base_harmonic_lmax"];grid=plan["base_los_grid"]
    elif mode=="fine":names=plan["fine_time"];steps=plan["fine_steps"];hl=plan["base_harmonic_lmax"];grid=plan["base_los_grid"]
    elif mode=="angular":names=plan["fine_angular"];steps=plan["fine_steps"];hl=plan["fine_angular_harmonic_lmax"];grid=plan["fine_angular_los_grid"]
    else:raise ValueError("unknown mode")
    root=scratch/("scan_"+mode);root.mkdir()
    archived=DOC/"raw"/mode
    if mode!="smoke":archived.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,RAYON_NUM_THREADS="2",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1")
    def run(name):
        p=points[name];geom=initial_geometry(p,a["omega_lambda_emit"]);lie=root/(name+".lie")
        lie.write_text(lie_text(p,a["omega_lambda_emit"]))
        dest=root/name
        args=[str(binary),"--out",str(dest),"--lie-ic",str(lie),"--duration",repr(a["duration"]),"--steps",str(steps),
            "--feedback","recoil","--collision","sdirk2","--lie-update","congruence",
            "--omega-lambda",repr(a["omega_lambda_emit"]),"--dust-fraction",repr(a["dust_fraction"]),"--baryon-fraction","0.157",
            "--neutrino-fraction",repr(ref["neutrino_fraction_hyrec"]),"--ionization",str(table),"--n-h-emit-m3",repr(a["n_h_emit_m3"]),
            "--h-emit-s",repr(a["h_emit_s"]),"--observer-frame","host","--route","harmonic","--harmonic-lmax",str(hl),
            "--nmu","8","--nphi","16","--lmax","4","--los-lmax",str(lmax),"--los-ntheta",str(grid[0]),"--los-nphi",str(grid[1]),
            "--recombination","matched","--t-unit-k",repr(2.72548*1601),"--recombination-stop-eta",repr(stop)]
        if name=="FLRW":
            j=args.index("--lie-ic");args[j:j+2]=["--family","FLRW","--shear","0"]
        rec={"point":name,"mode":mode,"steps":steps,"harmonic_lmax":hl,"los_grid":grid,"initial_geometry":geom,"argv":args}
        t=time.monotonic()
        try:
            result=subprocess.run(args,capture_output=True,text=True,timeout=180,env=env)
            rec.update(exit_code=result.returncode,wall_s=time.monotonic()-t)
            if result.returncode:raise RuntimeError(result.stderr[-3000:])
            raw=(dest/"los_modes.tsv").read_bytes();x,cl=decode_signed_modes(raw,lmax)
            native=np.loadtxt(dest/"los_cl.tsv",skiprows=1)
            if native.shape!=(lmax+1,7) or not np.array_equal(native[:,0],np.arange(lmax+1)):raise ValueError("invalid native spectrum")
            np.testing.assert_allclose(cl,native[:,1:],rtol=2e-11,atol=1e-24)
            dg=np.genfromtxt(dest/"diagnostics.tsv",names=True);rc=np.genfromtxt(dest/"recombination.tsv",names=True)
            if not all(np.isfinite(dg[k]).all() for k in dg.dtype.names) or not all(np.isfinite(rc[k]).all() for k in rc.dtype.names):raise ValueError("nonfinite diagnostics")
            if abs(dg["eta"][-1]-a["duration"])>1e-11 or np.any(np.diff(dg["eta"])<=0):raise ValueError("clock mismatch")
            r=dict(line.split("=",1) for line in (dest/"run.txt").read_text().splitlines() if "=" in line)
            if r["lie_type_initial"]!=p["expected_type"] or r["lie_type_final"]!=p["expected_type"]:raise ValueError("native family label changed or mismatched")
            if r["observer_frame"]!="host":raise ValueError("observer frame mismatch")
            ids=np.flatnonzero(rc["eta"]<=stop+1e-12)
            if not len(ids) or ids[-1]==len(rc)-1:raise ValueError("missing REC owner boundary")
            drift=float(np.max(np.abs(rc["delta_xe"][ids[-1]:]-rc["delta_xe"][ids[-1]])))
            if drift!=0:raise ValueError("REC correction drift after stop")
            band=x[4:]
            rec.update(status="validated_scoped",signed_norm=float(np.linalg.norm(band)),
                channel_norms=np.linalg.norm(band,axis=0).tolist(),spectrum_abs_error=float(np.max(abs(cl-native[:,1:]))),
                max_gauss=float(np.max(abs(dg["gauss"]))),max_codazzi=float(np.max(np.sqrt(sum(dg[k]**2 for k in ("codazzi_x","codazzi_y","codazzi_z"))))),
                max_jacobi=float(np.max(abs(dg["jacobi_norm"]))),min_screen=float(np.min(dg["min_screen_eigenvalue"])),
                depth=float(dg["proper_depth"][-1]),post_stop_drift=drift,delta_xe_final=float(r["delta_xe_final"]),
                type_initial=r["lie_type_initial"],type_final=r["lie_type_final"],h_initial=r["lie_h_initial"],h_final=r["lie_h_final"],
                observer_beta=r["observer_beta"],initial_host_beta=r["initial_host_beta"],frame_radiation_beta=r["frame_radiation_energy_beta"],
                file_sha256={f:sha(dest/f) for f in ("los_modes.tsv","los_cl.tsv","diagnostics.tsv","recombination.tsv","run.txt")})
            if mode=="smoke":
                orig,_=decode_signed_modes((DOC/"R7_VIh_LOS.tsv").read_bytes(),lmax)
                rec["pilot_relative_error"]=float(np.linalg.norm(x-orig)/np.linalg.norm(orig))
                if rec["pilot_relative_error"]>2e-11:raise ValueError("pilot replay difference")
            else:
                keep=archived/name;keep.mkdir()
                shutil.copy2(lie,keep/"point.lie")
                for f in ("los_modes.tsv","los_cl.tsv","run.txt"):shutil.copy2(dest/f,keep/f)
                for f in ("diagnostics.tsv","recombination.tsv"):
                    (keep/(f+".gz")).write_bytes(gzip.compress((dest/f).read_bytes(),compresslevel=6,mtime=0))
        except (Exception,) as ex:
            rec.update(status="failed_or_unqualified",error=str(ex),wall_s=time.monotonic()-t)
        print(name,mode,rec["status"],round(rec["wall_s"],2),rec.get("signed_norm"),rec.get("error",""),flush=True)
        return rec
    start=time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:records=list(pool.map(run,names))
    receipt={"mode":mode,"plan_sha256":sha(DOC/"SCAN_PLAN.json"),"binary_sha256":sha(binary),"opacity_sha256":sha(table),
             "workers":workers,"rayon_threads":2,"wall_s":time.monotonic()-start,"records":records,
             "scope":"finite deterministic native output, no observational family claim"}
    out=DOC/("C5_SMOKE.json" if mode=="smoke" else ("SCAN_"+mode.upper()+".json"))
    out.write_text(json.dumps(receipt,indent=2,allow_nan=False)+"\n")
    print("SUMMARY",mode,len(records),sum(v["status"]=="validated_scoped" for v in records),receipt["wall_s"],flush=True)
    if mode=="smoke" and records[0]["status"]!="validated_scoped":raise SystemExit(1)

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--scratch",type=Path,required=True);ap.add_argument("--mode",choices=["smoke","base","fine","angular"],required=True);ap.add_argument("--workers",type=int,default=4);a=ap.parse_args()
    if not 1<=a.workers<=4:raise ValueError("workers must be 1..4")
    execute(a.scratch,a.mode,a.workers)
