"""Run the fixed R121 chart using restored production binary, preserving raw evidence."""
import argparse,gzip,hashlib,json,math,os,shutil,subprocess,time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import initial_geometry,lie_text
from scripts.r120.native_scan import sources
from scripts.r121.verify_sources import DOC,OLD
from scripts.r121.plan import make

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def execute(scratch,mode,workers):
    plan=json.loads((DOC/"SCAN_PLAN.json").read_text())
    if plan!=make():raise ValueError("plan mismatch")
    lock=json.loads((DOC/"C1.json").read_text())
    if sha(DOC/"SOURCE_IDENTITY.json")!=lock["source_identity_sha256"]:raise ValueError("source identity receipt mismatch")
    binary,table,ref,_=sources(scratch)
    if sha(binary)!=lock["binary_sha256"] or sha(table)!=lock["opacity_sha256"]:raise ValueError("source mismatch")
    anchors=ref["cosmology_anchors"];pts={p["name"]:p for p in plan["points"]};stop=math.log(1601/21)
    names=["VII_center"] if mode=="smoke" else plan[mode]
    steps=plan["fine_steps"] if mode=="fine" else plan["base_steps"]
    root=scratch/("scan_"+mode);root.mkdir()
    archive=DOC/"raw"/mode
    if mode!="smoke":archive.mkdir(parents=True,exist_ok=False)
    env=dict(os.environ,RAYON_NUM_THREADS="2",OPENBLAS_NUM_THREADS="1",OMP_NUM_THREADS="1")
    def run(name):
        p=pts[name];geo=initial_geometry(p,anchors["omega_lambda_emit"]);lie=root/(name+".lie")
        lie.write_text(lie_text(p,anchors["omega_lambda_emit"]));out=root/name
        args=[str(binary),"--out",str(out),"--lie-ic",str(lie),"--duration",repr(anchors["duration"]),"--steps",str(steps),
            "--feedback","recoil","--collision","sdirk2","--lie-update","congruence",
            "--omega-lambda",repr(anchors["omega_lambda_emit"]),"--dust-fraction",repr(anchors["dust_fraction"]),
            "--baryon-fraction","0.157","--neutrino-fraction",repr(ref["neutrino_fraction_hyrec"]),
            "--ionization",str(table),"--n-h-emit-m3",repr(anchors["n_h_emit_m3"]),"--h-emit-s",repr(anchors["h_emit_s"]),
            "--observer-frame","host","--route","harmonic","--harmonic-lmax","8","--nmu","8","--nphi","16",
            "--lmax","4","--los-lmax","8","--los-ntheta","16","--los-nphi","32","--recombination","matched",
            "--t-unit-k",repr(2.72548*1601),"--recombination-stop-eta",repr(stop)]
        if name=="FLRW":
            i=args.index("--lie-ic");args[i:i+2]=["--family","FLRW","--shear","0"]
        rec={"name":name,"mode":mode,"steps":steps,"argv":args,"initial_geometry":geo,"lie_sha256":sha(lie)}
        t=time.monotonic()
        try:
            r=subprocess.run(args,capture_output=True,text=True,env=env,timeout=180)
            rec["exit_code"]=r.returncode
            if r.returncode:raise RuntimeError(r.stderr[-3000:])
            a,cl=decode_signed_modes((out/"los_modes.tsv").read_bytes(),8)
            c=np.loadtxt(out/"los_cl.tsv",skiprows=1)
            if c.shape!=(9,7) or not np.array_equal(c[:,0],np.arange(9)):raise ValueError("native spectrum layout")
            np.testing.assert_allclose(c[:,1:],cl,rtol=2e-11,atol=1e-24)
            dg=np.genfromtxt(out/"diagnostics.tsv",names=True);rc=np.genfromtxt(out/"recombination.tsv",names=True)
            if not all(np.isfinite(q[k]).all() for q in (dg,rc) for k in q.dtype.names):raise ValueError("nonfinite diagnostic")
            if abs(dg["eta"][-1]-anchors["duration"])>1e-11 or np.any(np.diff(dg["eta"])<=0):raise ValueError("clock mismatch")
            rt=dict(l.split("=",1) for l in (out/"run.txt").read_text().splitlines() if "=" in l)
            if rt["lie_type_initial"]!=p["expected_type"] or rt["lie_type_final"]!=p["expected_type"]:raise ValueError("family mismatch")
            if rt["observer_frame"]!="host":raise ValueError("frame mismatch")
            ids=np.flatnonzero(rc["eta"]<=stop+1e-12)
            if not len(ids) or ids[-1]==len(rc)-1:raise ValueError("missing REC stop")
            drift=float(np.max(abs(rc["delta_xe"][ids[-1]:]-rc["delta_xe"][ids[-1]])))
            if drift!=0:raise ValueError("post-stop drift")
            screen=float(np.min(dg["min_screen_eigenvalue"]))
            if screen<0:raise ValueError("negative sampled screen")
            h0,h1=rt["lie_h_initial"],rt["lie_h_final"]
            if h0.startswith("Some("):
                v0=float(h0[5:-1]);v1=float(h1[5:-1]);hd=abs(v1-v0)/abs(v0)
                if hd>1e-10 or not np.isclose(v0,p["parameters"]["h"],rtol=1e-10,atol=1e-14):raise ValueError("h mismatch")
            else:hd=None
            rec.update(status="validated_scoped",norm=float(np.linalg.norm(a[4:])),channel_norms=np.linalg.norm(a[4:],axis=0).tolist(),
                spectrum_abs_error=float(np.max(abs(c[:,1:]-cl))),max_gauss=float(np.max(abs(dg["gauss"]))),
                max_codazzi=float(np.max(np.sqrt(sum(dg[k]**2 for k in ("codazzi_x","codazzi_y","codazzi_z"))))),
                max_jacobi=float(np.max(abs(dg["jacobi_norm"]))),min_screen=screen,post_stop_drift=drift,
                depth=float(dg["proper_depth"][-1]),h_relative_drift=hd,
                hashes={f:sha(out/f) for f in ("los_modes.tsv","los_cl.tsv","run.txt","diagnostics.tsv","recombination.tsv")})
            if mode=="smoke":
                old=json.loads((OLD/"SCAN_FINE.json").read_text());oldrow=next(v for v in old["records"] if v["point"]=="VIIh")
                raw=(OLD/"raw/fine/VIIh/los_modes.tsv").read_bytes()
                if hashlib.sha256(raw).hexdigest()!=oldrow["file_sha256"]["los_modes.tsv"]:raise ValueError("old source hash mismatch")
                prev,_=decode_signed_modes(raw,8)
                rec["replay_relative_error"]=float(np.linalg.norm(a-prev)/np.linalg.norm(prev))
                if rec["replay_relative_error"]>2e-11:raise ValueError("R120 replay mismatch")
            else:
                dst=archive/name;dst.mkdir()
                shutil.copy2(lie,dst/"point.lie")
                for f in ("los_modes.tsv","los_cl.tsv","run.txt"):shutil.copy2(out/f,dst/f)
                for f in ("diagnostics.tsv","recombination.tsv"):(dst/(f+".gz")).write_bytes(gzip.compress((out/f).read_bytes(),mtime=0))
        except Exception as e:
            rec.update(status="failed_or_unqualified",error=str(e))
        rec["wall_s"]=time.monotonic()-t
        print(name,mode,rec["status"],rec.get("norm"),rec.get("error",""),flush=True)
        return rec
    t=time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:r=list(pool.map(run,names))
    summary={"mode":mode,"plan_sha256":sha(DOC/"SCAN_PLAN.json"),"binary_sha256":sha(binary),"opacity_sha256":sha(table),
             "records":r,"wall_s":time.monotonic()-t,"scope":"finite deterministic native sky only"}
    path=DOC/("C5_SMOKE.json" if mode=="smoke" else "SCAN_"+mode.upper()+".json")
    path.write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    good=sum(v["status"]=="validated_scoped" for v in r)
    print("SUMMARY",mode,good,len(r),summary["wall_s"])
    if mode=="smoke" and good!=len(r):raise SystemExit(1)

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);p.add_argument("--mode",choices=["smoke","base","fine"],required=True);p.add_argument("--workers",type=int,default=4);a=p.parse_args()
    if not 1<=a.workers<=4:raise ValueError("workers must be 1..4")
    execute(a.scratch,a.mode,a.workers)
