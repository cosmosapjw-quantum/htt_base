"""Re-read source identities, conditional spectra, direct shape and native stencils."""
import argparse,json,gzip,io
from pathlib import Path
import numpy as np
from common.opacity_memory_kernel import NodalWindows
from common.fixed_tau_shapes import source_metrics,perturb_nodes,real_map,visibility
from common.physical_memory_budget import build_context,metric_weights
from common.initial_data_response import observe_columns
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import lie_text
from scripts.r127.plan import groups
from scripts.r127.run_tangent import inputs,context,seed_matrix
from scripts.r128.verify_sources import DOC
from scripts.r128.spectra import read,sha,norm,project_amplitude
from scripts.r128.analyze import load_native
from scripts.r128.plan import make

def main(scratch):
    inp=inputs(scratch);w=NodalWindows(inp["table"],groups(inp["table"]))
    const=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    old=DOC.parent/"R127_OPACITY_MEMORY_KERNEL_20261128"
    for name,k in (("C6_TANGENT.json","R127_tangent_sha256"),("C7_KERNEL.json","R127_kernel_sha256"),("C2_CONSTANTS.json","R127_group_receipt_sha256")):
        assert sha((old/name).read_bytes())==const[k]
    prior=json.loads((old/"C6_TANGENT.json").read_text())["runs"]
    spec=json.loads((DOC/"C6_SPECTRA.json").read_text());path=DOC/"C6_SPECTRA.npz";assert sha(path.read_bytes())==spec["npz_sha256"]
    with np.load(path,allow_pickle=False) as f:arr={k:f[k] for k in f.files}
    metrics={};maxnull=maxorth=maxsv=0.;count=0
    active={"full":[0,1,2,3,4],"tail_locked":[0,1,2,3],"late_swap":[2,3]}
    for fam in ("VII0","VIIh"):
        c=context(inp,fam,0,20);q=source_metrics(c,w);metrics[fam]=q
        for k in ("t","nodal","M_tau","M_clock"):np.testing.assert_array_equal(q[k],arr[fam+"_"+k])
        for m in (0,1,2):
            key=f"{fam}_m{m}";r=spec["sectors"][key];a=read(old,prior[key+"_L20"]);lo=read(old,prior[key+"_L12"])
            c=context(inp,fam,m,20);wi,_=metric_weights(c,0.);y=a["initial"][:,0]
            size=float(np.vdot(y,wi*y).real);np.testing.assert_allclose(size,r["initial_physical_size"],rtol=1e-13)
            scale=np.sqrt(size);d=a["dsky"][:,:,:,0]/scale;dl=lo["dsky"][:,:,:,0]/scale;R=real_map(d);RL=real_map(dl)
            for met in ("M_tau","M_clock"):
                M=q[met]
                for tag,inds in active.items():
                    for profile,A,AL in (("full",R,RL),("high",real_map(d[:,3:]),real_map(dl[:,3:])),("amplitude_profiled",project_amplitude(R,a["sky"][:,:,0]/scale),project_amplitude(RL,lo["sky"][:,:,0]/scale))):
                        prefix=f"{key}_{met}_{tag}_{profile}_";v=r["metrics"][met][tag][profile]
                        B,X,XL=(arr[prefix+k] for k in ("B","X","XL"))
                        assert B.shape==(5,len(inds)-1) and np.all(B[np.setdiff1d(np.arange(5),inds)]==0)
                        maxnull=max(maxnull,float(np.max(abs(q["t"]@B))))
                        maxorth=max(maxorth,float(np.max(abs(B.T@M@B-np.eye(B.shape[1])))))
                        np.testing.assert_allclose(X,A@B,rtol=1e-13,atol=1e-14);np.testing.assert_allclose(XL,AL@B,rtol=1e-13,atol=1e-14)
                        s=np.linalg.svd(X,compute_uv=False);gap=float(np.linalg.norm(X-XL,ord=2))
                        maxsv=max(maxsv,float(np.max(abs(s-v["singular_values"]))))
                        np.testing.assert_allclose(s,v["singular_values"],rtol=1e-12,atol=1e-14)
                        np.testing.assert_allclose(gap,v["empirical_op_difference"],rtol=1e-10,atol=1e-13)
                        assert int(np.sum(s>gap))==v["count_above_difference"]
                        V=np.array(v["directions"]);np.testing.assert_allclose(V.T@M@V,np.eye(V.shape[1]),atol=1e-12)
                        np.testing.assert_allclose(np.linalg.norm(A@V,axis=0),s,rtol=1e-12,atol=1e-14);count+=1
    sr=json.loads((DOC/"C7_SHAPES.json").read_text());tabs=json.loads((DOC/"SHAPE_TABLES.json").read_text())["tables"];maxdepth=maxmass=maxfd=0.
    assert set(sr["runs"])==set(make()["directions"])
    for name,r in sr["runs"].items():
        a=read(DOC,r);m=r["m"];c=context(inp,"VIIh",m,20);q=metrics["VIIh"];s=c["system"];weights,names=seed_matrix(c,"VIIh")
        np.testing.assert_array_equal(a["initial"],s["basis"]@weights[:,names.index(r["seed"])])
        f=a["f"];assert np.all(f[w.groups==4]==0)
        maxdepth=max(maxdepth,abs(float(q["nodal"]@f)));assert abs(q["nodal"]@f)<2e-12
        if name=="intra_rec":
            assert np.all(f[w.groups!=1]==0) and np.ptp(f[w.groups==1])>1
        else:np.testing.assert_array_equal(f,np.array(r["group_coefficients"])[w.groups])
        np.testing.assert_array_equal(a["base"],observe_columns(a["endpoint"][:,None],s,"host")[:,:,0])
        np.testing.assert_array_equal(a["tangent"],observe_columns(a["tangent_state"][:,None],s,"host")[:,:,0])
        for tag in ("h03","h01"):
            h=r["fd"][tag]["width"];fd=(a[tag+"_plus"]-a[tag+"_minus"])/(2*h)
            np.testing.assert_array_equal(fd,a[tag]);err=norm(fd-a["tangent"])/norm(a["tangent"])
            np.testing.assert_allclose(err,r["fd"][tag]["relative_to_tangent"],rtol=1e-12,atol=1e-14)
            maxfd=max(maxfd,err)
            for sign in (-1,1):
                side="minus" if sign<0 else "plus";tab=perturb_nodes(w,f,sign*h);cp=build_context(**dict(inp,table=tab),a0=.005,m=m,L=20)
                vi=visibility(cp,NodalWindows(tab,w.groups),12);v=r["visibility"][tag+"_"+side]
                for k in ("tau","mass","mean_z","mean_eta"):np.testing.assert_allclose(vi[k],v[k],rtol=1e-12,atol=1e-13)
                maxdepth=max(maxdepth,abs(vi["tau"]-sr["visibility_baseline"]["tau"]))
                maxmass=max(maxmass,abs(vi["mass"]-vi["exact_mass"]))
                if tag=="h03" and name in ("early_rec","late_swap"):
                    n=name+"_"+side;raw=gzip.decompress((DOC/(n+".tsv.gz")).read_bytes());assert sha(raw)==tabs[n]["sha256"]
                    np.testing.assert_array_equal(np.loadtxt(io.BytesIO(raw),skiprows=1),tab)
    nr=json.loads((DOC/"C8_NATIVE.json").read_text());p=DOC/"C8_NATIVE.npz";assert sha(p.read_bytes())==nr["npz_sha256"]
    with np.load(p,allow_pickle=False) as f:narr={k:f[k] for k in f.files}
    points={v["name"]:v for v in make()["points"]};native_count=raw_count=0;diag={}
    for mode in ("base","fine"):
        rec,sky=load_native(mode);rows=[]
        for n,r in rec.items():
            p=DOC/"raw"/mode/n
            assert r["status"]=="validated_scoped" and r["exit_code"]==0
            assert sha((p/"point.lie").read_bytes())==r["lie_sha256"]
            assert (p/"point.lie").read_text()==lie_text(points[n],3.610288143119805e-10)
            data={}
            assert set(r["hashes"])=={"los_modes.tsv","los_cl.tsv","run.txt","diagnostics.tsv"}
            for k,h in r["hashes"].items():
                raw=gzip.decompress((p/(k+".gz")).read_bytes()) if k=="diagnostics.tsv" else (p/k).read_bytes()
                assert sha(raw)==h;data[k]=raw;raw_count+=1
            x,cl=decode_signed_modes(data["los_modes.tsv"],8)
            np.testing.assert_allclose(cl,np.loadtxt(io.BytesIO(data["los_cl.tsv"]),skiprows=1)[:,1:],rtol=2e-11,atol=1e-24)
            dg=np.genfromtxt(io.BytesIO(data["diagnostics.tsv"]),names=True);assert np.min(dg["min_screen_eigenvalue"])>=0
            np.testing.assert_allclose(dg["proper_depth"][-1],r["depth"],rtol=1e-13)
            rt=dict(l.split("=",1) for l in data["run.txt"].decode().splitlines() if "=" in l)
            assert rt["observer_frame"]==points[n]["observer_frame"] and rt["lie_type_initial"]==rt["lie_type_final"]==points[n]["expected_type"]
            native_count+=1;rows.append(r)
        diag[mode]={"verified":len(rows),"max_gauss":max(r["max_gauss"] for r in rows),"max_codazzi":max(r["max_codazzi"] for r in rows),"max_jacobi":max(r["max_jacobi"] for r in rows),"min_screen":min(r["min_screen"] for r in rows)}
        for name,m,col in (("early_rec",1,"relative_dust"),("late_swap",2,"metric")):
            def odd(s):return (sky[f"VIIh_m{m}_{col}_pos_host_{name}_{s}"]-sky[f"VIIh_m{m}_{col}_neg_host_{name}_{s}"])/1e-4
            x=(odd("plus")-odd("minus"))/.06;np.testing.assert_array_equal(x,narr[name+"_"+mode])
            a=read(DOC,sr["runs"][name]);err=norm(x-a["h03"])/norm(a["h03"])
            np.testing.assert_allclose(err,nr["runs"][name]["native"][mode]["relative_to_same_width_oracle"],rtol=1e-12)
    out={"spectra_verified":count,"shape_npz_verified":len(sr["runs"]),"native_verified":native_count,"native_raw_verified":raw_count,
         "max_null_residual":maxnull,"max_metric_orthogonality_error":maxorth,"max_singular_value_replay_error":maxsv,
         "max_fixed_background_depth_difference":maxdepth,"max_visibility_mass_error":maxmass,"max_FD_tangent_relative":maxfd,"native":diag,
         "scope":"direct source/hash/finite evidence re-read, not independent trajectory reintegration or fresh reviewer"}
    (DOC/"C9_AUDIT.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
