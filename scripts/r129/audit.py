"""Direct re-read of nested source, real IC nuisance, and finite stencil evidence."""
import argparse,json,gzip,io
from pathlib import Path
import numpy as np
from common.opacity_memory_kernel import NodalWindows
from common.fixed_tau_shapes import source_metrics,perturb_nodes
from common.profiled_opacity_shapes import nested_groups,NodalBasis,nodal_metric,aggregation,compact_sky,real_initial_map,real_shape_map,profile,unpack_ic
from common.physical_memory_budget import metric_weights
from common.initial_data_response import observe_columns
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import lie_text
from scripts.r127.plan import groups
from scripts.r127.run_tangent import inputs,context,seed_matrix
from scripts.r128.spectra import read,sha,norm
from scripts.r129.run_nested import locks
from scripts.r129.profile_maps import arrays,opnorm
from scripts.r129.analyze import load_native
from scripts.r129.plan import make
from scripts.r129.verify_sources import DOC

def main(scratch):
    inp=inputs(scratch);g=groups(inp["table"]);ng=nested_groups(g);w=NodalBasis(inp["table"],ng);old=locks()
    nr=json.loads((DOC/"C6_NESTED.json").read_text());mt=arrays(DOC/"C6_METRIC.npz")
    assert sha((DOC/"C6_METRIC.npz").read_bytes())==nr["metric_sha256"]
    np.testing.assert_array_equal(mt["groups"],ng);np.testing.assert_array_equal(mt["eta"],inp["table"][:,0]);np.testing.assert_array_equal(mt["xe"],inp["table"][:,1])
    assert set(nr["runs"])=={f"{fam}_m{m}_L{L}" for fam in ("VII0","VIIh") for m in (0,1,2) for L in (12,20)}
    qg={};maxagg=maxbase=maxconstraint=0.
    for fam in ("VII0","VIIh"):
        c=context(inp,fam,0,12);qg[fam]=nodal_metric(c,w)
        for k in ("t","M_tau","M_clock"):np.testing.assert_array_equal(qg[fam][k],mt[fam+"_"+k])
    for key,r in nr["runs"].items():
        a=read(DOC,r);fam,m,L=r["family"],r["m"],r["L"];c=context(inp,fam,m,L);s=c["system"];V,names=seed_matrix(c,fam)
        np.testing.assert_array_equal(a["initial"],s["basis"]@V[:,0])
        np.testing.assert_array_equal(a["sky"],observe_columns(a["endpoint"][:,None],s,"host")[:,:,0])
        np.testing.assert_array_equal(a["dsky"],observe_columns(a["tangent"],s,"host"))
        np.testing.assert_allclose(s["constraint"](a["eta"][-1],np.column_stack((a["endpoint"],a["tangent"]))),a["constraint"][-1],atol=1e-14,rtol=1e-10)
        p=old["R127"];z=read(p[0],p[1]["runs"][key]);agg=np.einsum("mcg,gk->kmc",a["dsky"],aggregation(4));e=norm(agg-z["dsky"][:4,:,:,0])/norm(z["dsky"][:4,:,:,0]);be=norm(a["sky"]-z["sky"][:,:,0])/norm(z["sky"][:,:,0])
        np.testing.assert_allclose(e,r["coarse_window_relative"],rtol=1e-10,atol=1e-15);np.testing.assert_allclose(be,r["baseline_relative"],rtol=1e-10,atol=1e-15)
        maxagg=max(maxagg,e);maxbase=max(maxbase,be);maxconstraint=max(maxconstraint,r["max_constraint"])
    pr=json.loads((DOC/"C7_PROFILE.json").read_text());ar=arrays(DOC/"C7_PROFILE.npz");assert sha((DOC/"C7_PROFILE.npz").read_bytes())==pr["npz_sha256"]
    count=0;null=orth=sv=fit=motion=0.;machinefit=0.
    for key,r in pr["sectors"].items():
        fam,m=key.rsplit("_m",1);m=int(m);a=read(DOC,nr["runs"][key+"_L20"]);al=read(DOC,nr["runs"][key+"_L12"])
        pp=old["R125"];it=read(pp[0],pp[1]["runs"][key+"_tight"]);il=read(pp[0],pp[1]["runs"][key+"_L12"])
        pp=old["R126"];b=read(pp[0],pp[1]["runs"][key+"_L20_s1"]);H=b["whitener"];M=b["M"];np.testing.assert_array_equal(ar[key+"_W"],H);np.testing.assert_array_equal(ar[key+"_M"],M)
        c=context(inp,fam,m,20);wi,_=metric_weights(c,0.);size=float(np.vdot(a["initial"],wi*a["initial"]).real);np.testing.assert_allclose(size,r["initial_size"],rtol=1e-13)
        for band,high in (("full",False),("high",True)):
            T=real_initial_map(compact_sky(it["sky_host"],m,high)@H,m);TL=real_initial_map(compact_sky(il["sky_host"],m,high)@H,m)
            Z=real_shape_map(compact_sky(a["dsky"],m,high))/np.sqrt(size);ZL=real_shape_map(compact_sky(al["dsky"],m,high))/np.sqrt(size)
            baseline=real_shape_map(compact_sky(a["sky"],m,high)[:,None])[:,0]/np.sqrt(size);bl=real_shape_map(compact_sky(al["sky"],m,high)[:,None])[:,0]/np.sqrt(size)
            for k,z in (("T",T),("TL",TL),("Z",Z),("ZL",ZL),("baseline",baseline),("baseL",bl)):np.testing.assert_array_equal(ar[f"{key}_{band}_{k}"],z)
            for met in ("M_tau","M_clock"):
                for n in (4,8,16):
                    prefix=f"{key}_{band}_{met}_{n}";v=r["bands"][band]["metrics"][met][str(n)]
                    N,S,SL=(ar[prefix+"_"+k] for k in ("N","S","SL"));null=max(null,float(np.max(abs(mt[fam+"_t"]@N))))
                    orth=max(orth,float(np.max(abs(N.T@mt[fam+"_"+met]@N-np.eye(n-1)))))
                    np.testing.assert_allclose(S,Z@N,atol=1e-14,rtol=1e-13);np.testing.assert_allclose(SL,ZL@N,atol=1e-14,rtol=1e-13)
                    np.testing.assert_allclose(np.linalg.svd(S,compute_uv=False),v["raw"]["singular_values"],rtol=1e-12,atol=1e-14)
                    for tag,p in v["profiles"].items():
                        Ti,TiL=T,TL
                        if tag=="amplitude":Ti,TiL=baseline[:,None],bl[:,None]
                        if tag=="shear":
                            Ti=real_initial_map(compact_sky(it["sky_host"][:,:,[0]],m,high),m);TiL=real_initial_map(compact_sky(il["sky_host"][:,:,[0]],m,high),m)
                        z=profile(Ti,S,p["cutoff"]);zl=profile(TiL,SL,p["cutoff"]);sval=np.linalg.svd(z["E"],compute_uv=False)
                        assert z["rank"]==p["rank"] and zl["rank"]==p["coarse_rank"]
                        np.testing.assert_allclose(sval,p["singular_values"],rtol=1e-12,atol=1e-14)
                        gap=opnorm(z["E"]-zl["E"]);np.testing.assert_allclose(gap,p["empirical_difference"],rtol=1e-11,atol=1e-14)
                        if z["rank"]==zl["rank"]:assert int(np.sum(sval>gap))==p["count_above_difference"]
                        else:assert p["count_above_difference"] is None
                        sv=max(sv,float(np.max(abs(sval-p["singular_values"]))));motion=max(motion,opnorm(z["P"]-zl["P"]))
                        if tag in ("factor10","machine"):
                            for k in ("P","E","C"):np.testing.assert_array_equal(z[k],ar[prefix+"_"+tag+"_"+k])
                        e=opnorm(S+Ti@z["C"]-z["E"])
                        if tag=="machine":machinefit=max(machinefit,e)
                        else:fit=max(fit,e)
                        count+=1
    direct=json.loads((DOC/"C7_DIRECT.json").read_text());tabs=json.loads((DOC/"SHAPE_TABLES.json").read_text())["tables"];maxdepth=0.
    for name,r in direct["native_cases"].items():
        a=read(DOC,r);f=a["f"];assert np.all(f[g==4]==0);c=context(inp,"VIIh",r["m"],20);ww=NodalWindows(inp["table"],g);q=source_metrics(c,ww)
        maxdepth=max(maxdepth,abs(float(q["nodal"]@f)))
        np.testing.assert_array_equal(f,np.r_[a["coeff"],0.][ng])
        for tag in ("h03","h01"):
            h=r["fd"][tag]["width"];z=(a[tag+"_plus"]-a[tag+"_minus"])/(2*h);np.testing.assert_array_equal(z,a[tag])
        for sign in (-1,1):
            side="minus" if sign<0 else "plus";n=name+"_"+side
            raw=gzip.decompress((DOC/(n+".tsv.gz")).read_bytes());assert sha(raw)==tabs[n]["sha256"]
            np.testing.assert_array_equal(np.loadtxt(io.BytesIO(raw),skiprows=1),perturb_nodes(ww,f,sign*.03))
    for name,r in direct["compensation"].items():
        a=read(DOC,r);c=context(inp,r["family"],r["m"],20);s=c["system"];wi,_=metric_weights(c,0.);ww=NodalWindows(inp["table"],g);q=source_metrics(c,ww)
        h=r["width"];assert np.all(a["f"][g==4]==0) and np.max(abs(h*a["f"]))<=.03+1e-15
        maxdepth=max(maxdepth,abs(float(q["nodal"]@a["f"])))
        shift=np.sqrt(np.vdot(a["physical_shift"],wi*a["physical_shift"]).real/np.vdot(a["initial"],wi*a["initial"]).real)*h
        np.testing.assert_allclose(shift,r["initial_relative_shift"],rtol=1e-12);assert shift<=.05+1e-14
        assert np.max(abs(s["constraint"](0.,np.column_stack((a["initial"],a["physical_shift"])))))<1e-11
        for tag in ("raw","comp"):
            z=real_shape_map(compact_sky((a[tag+"_plus"]-a[tag+"_minus"])/(2*h),r["m"])[:,None])[:,0]
            np.testing.assert_array_equal(z,a[tag+"_fd"])
        np.testing.assert_allclose(norm(a["comp_fd"])/norm(a["raw_fd"]),r["measured_retained_fraction"],rtol=1e-12)
    n=json.loads((DOC/"C8_NATIVE.json").read_text());na=arrays(DOC/"C8_NATIVE.npz");assert sha((DOC/"C8_NATIVE.npz").read_bytes())==n["npz_sha256"]
    points={v["name"]:v for v in make()["points"]};raw_count=run_count=0;diag={}
    for mode in ("base","fine"):
        rec,sky=load_native(mode);rows=[]
        for name,r in rec.items():
            p=DOC/"raw"/mode/name;assert r["status"]=="validated_scoped" and r["exit_code"]==0
            assert sha((p/"point.lie").read_bytes())==r["lie_sha256"] and (p/"point.lie").read_text()==lie_text(points[name],3.610288143119805e-10)
            data={}
            assert set(r["hashes"])=={"los_modes.tsv","los_cl.tsv","run.txt","diagnostics.tsv"}
            for k,h in r["hashes"].items():
                raw=gzip.decompress((p/(k+".gz")).read_bytes()) if k=="diagnostics.tsv" else (p/k).read_bytes()
                assert sha(raw)==h;data[k]=raw;raw_count+=1
            x,cl=decode_signed_modes(data["los_modes.tsv"],8);np.testing.assert_allclose(cl,np.loadtxt(io.BytesIO(data["los_cl.tsv"]),skiprows=1)[:,1:],rtol=2e-11,atol=1e-24)
            dg=np.genfromtxt(io.BytesIO(data["diagnostics.tsv"]),names=True);assert np.min(dg["min_screen_eigenvalue"])>=0
            np.testing.assert_allclose(dg["proper_depth"][-1],r["depth"],rtol=1e-13)
            rt=dict(l.split("=",1) for l in data["run.txt"].decode().splitlines() if "=" in l)
            assert rt["observer_frame"]==points[name]["observer_frame"] and rt["lie_type_initial"]==rt["lie_type_final"]==points[name]["expected_type"]
            run_count+=1;rows.append(r)
        diag[mode]={"verified":len(rows),"max_gauss":max(r["max_gauss"] for r in rows),"max_codazzi":max(r["max_codazzi"] for r in rows),"max_jacobi":max(r["max_jacobi"] for r in rows),"min_screen":min(r["min_screen"] for r in rows)}
        for name,m,col in (("rec_subswap",1,"relative_dust"),("rei_subswap",2,"metric")):
            def odd(side):return (sky[f"VIIh_m{m}_{col}_pos_host_{name}_{side}"]-sky[f"VIIh_m{m}_{col}_neg_host_{name}_{side}"])/1e-4
            x=(odd("plus")-odd("minus"))/.06;np.testing.assert_array_equal(x,na[name+"_"+mode])
            ref=read(DOC,direct["native_cases"][name])["h03"]
            np.testing.assert_allclose(norm(x-ref)/norm(ref),n["runs"][name]["native"][mode]["relative_to_same_width_oracle"],rtol=1e-12)
    out={"nested_verified":len(nr["runs"]),"profiles_verified":count,"direct_verified":len(direct["native_cases"])+len(direct["compensation"]),"native_verified":run_count,"native_raw_verified":raw_count,
         "max_nested_aggregation_relative":maxagg,"max_baseline_relative":maxbase,"max_constraint":maxconstraint,"max_depth_null_residual":null,"max_metric_orthogonality":orth,
         "max_singular_replay_error":sv,"max_fit_closure_empirical":fit,"max_fit_closure_machine":machinefit,"max_projector_motion":motion,"max_direct_depth_residual":maxdepth,"native":diag,
         "scope":"direct source/hash and finite matrix/FD re-read; not independent fresh-context reviewer or trajectory reintegration"}
    (DOC/"C9_AUDIT.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
