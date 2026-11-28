"""Re-read source-nodal identity, tangent/adjoint endpoints, finite FD and native raw."""
import argparse,gzip,io,json
from pathlib import Path
import numpy as np
from common.physical_memory_budget import observation
from common.initial_data_response import observe_columns
from common.opacity_memory_kernel import NodalWindows
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import lie_text
from scripts.r127.run_tangent import inputs,context,seed_matrix,sha
from scripts.r127.analyze import read,load_native,norm
from scripts.r127.plan import groups,LABELS,make
from scripts.r127.verify_sources import DOC

def main(scratch):
    inp=inputs(scratch);w=NodalWindows(inp["table"],groups(inp["table"]));const=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    for name,r in const["tables"].items():
        raw=gzip.decompress((DOC/(name+".tsv.gz")).read_bytes());assert sha(raw)==r["sha256"]
        alpha=np.zeros(5);alpha[LABELS.index(r["window"])]=r["width"]
        np.testing.assert_array_equal(np.loadtxt(io.BytesIO(raw),skiprows=1),w.perturb(alpha))
    tr=json.loads((DOC/"C6_TANGENT.json").read_text());kr=json.loads((DOC/"C7_KERNEL.json").read_text());ar=json.loads((DOC/"C8_ANALYSIS.json").read_text())
    assert tr["source_sha256"]==const["original_opacity_sha256"] and tr["plan_sha256"]==sha((DOC/"SCAN_PLAN.json").read_bytes())
    expect={f"{fam}_m{m}_L{L}" for fam in ("VII0","VIIh") for m in (0,1,2) for L in (12,20)}
    assert set(tr["runs"])==expect
    for key,r in tr["runs"].items():
        a=read(r);c=context(inp,r["family"],r["m"],r["L"]);s=c["system"];V,names=seed_matrix(c,r["family"])
        assert a["names"].tolist()==names and r["seeds"]==names
        np.testing.assert_array_equal(a["initial"],s["basis"]@V)
        assert all(np.isfinite(v).all() for k,v in a.items() if k!="names")
        y=a["endpoint"];dy=a["tangent"];O=observation(c);z=O@y;dz=np.stack([O@q for q in dy])
        np.testing.assert_allclose(z,a["z"],rtol=1e-13,atol=1e-14);np.testing.assert_allclose(dz,a["dz"],rtol=1e-13,atol=1e-14)
        np.testing.assert_allclose(observe_columns(y,s,"host"),a["sky"],atol=0,rtol=0)
        np.testing.assert_allclose(np.stack([observe_columns(q,s,"host") for q in dy]),a["dsky"],atol=0,rtol=0)
        g=np.stack([np.real(np.einsum("ip,wip->wp",z[i::3].conj(),dz[:,i::3,:])) for i in range(3)])
        np.testing.assert_allclose(g,a["goal"],atol=1e-14,rtol=1e-13)
        C=s["constraint"](inp["table"][-1,0],np.concatenate([y,*dy],axis=1))
        np.testing.assert_allclose(C,a["constraint"][-1],rtol=1e-8,atol=1e-14)
        np.testing.assert_allclose(np.max(abs(a["constraint"])),r["max_constraint"],rtol=1e-13,atol=1e-15)
    maxgap=0.;minloss=0.;maxquad=0.;maxduality=0.;prior=[]
    assert set(kr["runs"])=={f"{fam}_m{m}" for fam in ("VII0","VIIh") for m in (0,1,2)}
    for key,r in kr["runs"].items():
        a=read(r);t=tr["runs"][key+"_L20"];b=read(t);assert r["tangent_sha256"]==t["sha256"]
        np.testing.assert_array_equal(a["source_eta"],inp["table"][:,0]);np.testing.assert_array_equal(a["source_xe"],inp["table"][:,1]);np.testing.assert_array_equal(a["groups"],w.groups)
        g=np.stack([a["knot_gradient"][:,w.groups==j].sum(axis=1) for j in range(5)],axis=1)
        np.testing.assert_allclose(g,a["group_gradient"],rtol=1e-13,atol=1e-14);np.testing.assert_allclose(g,r["group_gradient"],rtol=1e-13,atol=1e-14)
        assert np.all(a["absolute_mass"]+1e-14>=abs(g))
        np.testing.assert_allclose(a["tangent_goal"],b["goal"][:,:,0],rtol=1e-13,atol=1e-14)
        err=norm(g-a["tangent_goal"])/max(norm(a["tangent_goal"]),1e-30)
        np.testing.assert_allclose(err,r["adjoint_tangent_relative"],rtol=1e-10,atol=1e-14)
        np.testing.assert_allclose(a["tau"],b["tau"],rtol=1e-10,atol=1e-12)
        maxgap=max(maxgap,err);minloss=min(minloss,float(a["loss"].min()));maxquad=max(maxquad,r["quadrature_group_abs"]);maxduality=max(maxduality,r["duality_abs"])
        if "prior_R126_global_abs_gap" in r:prior.append(r["prior_R126_global_abs_gap"])
    points={v["name"]:v for v in make()["points"]};rawcount=0;native={};skies={}
    for mode in ("base","fine"):
        rec,sky=load_native(mode);skies[mode]=sky;rows=[]
        for n,r in rec.items():
            d=DOC/"raw"/mode/n
            assert r["status"]=="validated_scoped" and r["exit_code"]==0
            assert sha((d/"point.lie").read_bytes())==r["lie_sha256"]
            assert (d/"point.lie").read_text()==lie_text(points[n],3.610288143119805e-10)
            data={};assert set(r["hashes"])=={"los_modes.tsv","los_cl.tsv","run.txt","diagnostics.tsv"}
            for k,h in r["hashes"].items():
                v=gzip.decompress((d/(k+".gz")).read_bytes()) if k=="diagnostics.tsv" else (d/k).read_bytes()
                assert sha(v)==h;data[k]=v;rawcount+=1
            x,cl=decode_signed_modes(data["los_modes.tsv"],8)
            np.testing.assert_allclose(cl,np.loadtxt(io.BytesIO(data["los_cl.tsv"]),skiprows=1)[:,1:],atol=1e-24,rtol=2e-11)
            dg=np.genfromtxt(io.BytesIO(data["diagnostics.tsv"]),names=True);assert np.min(dg["min_screen_eigenvalue"])>=0
            np.testing.assert_allclose(dg["proper_depth"][-1],r["depth"],rtol=1e-13)
            rt=dict(l.split("=",1) for l in data["run.txt"].decode().splitlines() if "=" in l)
            assert rt["observer_frame"]==points[n]["observer_frame"] and rt["lie_type_initial"]==rt["lie_type_final"]==points[n]["expected_type"]
            rows.append(r)
        native[mode]={"verified":len(rows),"max_gauss":max(r["max_gauss"] for r in rows),"max_codazzi":max(r["max_codazzi"] for r in rows),"max_jacobi":max(r["max_jacobi"] for r in rows),"min_screen":min(r["min_screen"] for r in rows)}
    for key,r in ar["native"].items():
        a=read(r);col=r["column"];window=r["window"];b=read(tr["runs"][key+"_L20"])
        np.testing.assert_array_equal(a["tangent"],b["dsky"][LABELS.index(window),:,:,1])
        for tag in ("h03","h01"):
            h=r["fd"][tag]["width"];z=(a[tag+"_plus"]-a[tag+"_minus"])/(2*h)
            np.testing.assert_array_equal(z,a[tag])
        for mode,data in skies.items():
            def odd(s):
                return (data[f"{key}_{col}_pos_host_{window}_{s}"]-data[f"{key}_{col}_neg_host_{window}_{s}"])/1e-4
            z=(odd("plus")-odd("minus"))/.06;np.testing.assert_array_equal(z,a["native_"+mode])
    out={"tangent_verified":len(tr["runs"]),"kernel_verified":len(kr["runs"]),"fd_records_verified":len(ar["native"]),
        "native_verified":sum(v["verified"] for v in native.values()),"native_raw_verified":rawcount,"native":native,
        "max_adjoint_tangent_relative":maxgap,"max_quadrature_group_abs":maxquad,"max_duality_abs":maxduality,"min_window_loss":minloss,"max_R126_global_abs_gap":max(prior),
        "scope":"direct source/hash, endpoint, nodal and finite FD re-read; no independent fresh-context reviewer or trajectory reintegration"}
    (DOC/"C9_AUDIT.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
