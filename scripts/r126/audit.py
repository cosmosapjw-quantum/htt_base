"""Re-read finite budgets, native raw evidence and backward-goal receipts."""
import argparse,gzip,hashlib,io,json
from pathlib import Path
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import lie_text
from common.physical_memory_budget import metric_weights,observation
from common.initial_data_response import observe_columns
from scripts.r126.verify_sources import DOC
from scripts.r126.plan import make
from scripts.r126.run_budget import inputs,context
from scripts.r126.analyze import read,load_native
def sha(b):return hashlib.sha256(b).hexdigest()
def main(scratch):
    inp=inputs(scratch);const=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    raw=gzip.decompress((DOC/"opacity_quarter.tsv.gz").read_bytes())
    assert sha(raw)==const["intervention_opacity_sha256"]
    tab=np.loadtxt(io.BytesIO(raw),skiprows=1)
    expect=inp["table"].copy();expect[:,1]*=.25;np.testing.assert_array_equal(tab,expect)
    budget=json.loads((DOC/"C6_BUDGET.json").read_text());adj=json.loads((DOC/"C7_ADJOINT.json").read_text())
    assert budget["opacity_sha256"]==const["original_opacity_sha256"]
    assert budget["constants_sha256"]==sha((DOC/"C2_CONSTANTS.json").read_bytes())
    plan=make();expected={}
    for fam in ("VII0","VIIh"):
        for m in (0,1,2):
            for L,scales in ((16,plan["oracle_scales"]),(20,plan["tight_scales"])):
                for scale in scales:
                    t={0.:"0",.25:"025",.5:"05",1.:"1"}[scale]
                    expected[f"{fam}_m{m}_L{L}_s{t}"]=(fam,m,L,scale)
    assert set(expected)==set(budget["runs"])
    closure=0.;wclosure=0.;psd=0.;constraint=0.;white=0.;gen=0.;counts=0
    for key,r in budget["runs"].items():
        fam,m,L,scale=expected[key];a=read(r);c=context(inp,fam,m,L);s=c["system"]
        assert r["scale"]==scale and r["L"]==L and r["m"]==m and r["family"]==fam
        assert all(np.isfinite(x).all() for n,x in a.items() if n!="labels")
        assert a["labels"].tolist()==s["labels"]
        np.testing.assert_array_equal(a["initial"],s["basis"])
        wi,_=metric_weights(c,0.);wf,_=metric_weights(c,inp["table"][-1,0])
        np.testing.assert_array_equal(wi,a["wi"]);np.testing.assert_array_equal(wf,a["wf"])
        M=a["initial"].conj().T@(wi[:,None]*a["initial"]);J=a["endpoint"].conj().T@(wf[:,None]*a["endpoint"])
        np.testing.assert_allclose(M,a["M"],rtol=1e-13,atol=1e-15);np.testing.assert_allclose(J,a["J"],rtol=1e-13,atol=1e-15)
        H=a["whitener"];E=J-M-a["N"]+a["D"]
        e=float(np.linalg.norm(E)/max(np.linalg.norm(M),np.linalg.norm(J),np.linalg.norm(a["D"]),np.linalg.norm(a["N"])))
        ew=float(np.linalg.norm(H.conj().T@E@H,ord=2));d=float(np.min(np.linalg.eigvalsh((a["D"]+a["D"].conj().T)/2)))
        np.testing.assert_allclose(e,r["closure_relative"],rtol=1e-7,atol=1e-14)
        np.testing.assert_allclose(ew,r["closure_whitened"],rtol=1e-7,atol=1e-11)
        np.testing.assert_allclose(d,r["min_D_eigenvalue"],rtol=1e-7,atol=1e-14)
        we=float(np.linalg.norm(H.conj().T@M@H-np.eye(M.shape[0]),ord=2))
        assert e<2e-8 and d> -1e-9 and we<1e-11
        if scale==0.:assert np.max(abs(a["D"]))==0.
        np.testing.assert_allclose(a["constraint"][-1],s["constraint"](a["eta"][-1],a["endpoint"]),rtol=1e-7,atol=1e-14)
        np.testing.assert_allclose(np.max(abs(a["constraint"])),r["max_constraint"],atol=1e-15,rtol=1e-12)
        for f in ("host","normal","radiation","spectator"):
            np.testing.assert_allclose(observation(c,f)@a["endpoint"],a["response_"+f],atol=1e-14,rtol=1e-13)
        np.testing.assert_allclose(observe_columns(a["endpoint"],s,"host"),a["sky_host"],atol=1e-14,rtol=1e-13)
        closure=max(closure,e);wclosure=max(wclosure,ew);psd=min(psd,d);white=max(white,we);constraint=max(constraint,r["max_constraint"]);counts+=1
    for v in budget["local_collision_audit"].values():
        gen=max(gen,v["relative_generator_gap"]);assert v["min_scaled_dissipation_eigenvalue"]>=-1e-12
    adjgap=0.
    for key,r in adj["runs"].items():
        a=read(r);br=budget["runs"][key+"_L20_s1"];b=read(br)
        assert r["budget_sha256"]==br["sha256"]
        z=b["response_host"]@a["weights"];v=b["response_host"].conj().T@a["z"]
        eg=float(np.linalg.norm(v-a["initial_gradient"])/np.linalg.norm(v))
        np.testing.assert_allclose(eg,r["adjoint_transfer_relative"],atol=1e-14,rtol=1e-10)
        np.testing.assert_allclose(.5*np.vdot(a["z"],a["z"]).real,r["objective"],rtol=1e-13)
        for f in r["fd"]:np.testing.assert_allclose(abs(f["value"]-r["gradient"]),f["absolute_error"],rtol=1e-13)
        adjgap=max(adjgap,eg)
    rawcount=0;native={}
    points={v["name"]:v for v in plan["points"]}
    for mode in ("base","fine"):
        rec,sky=load_native(mode);rows=[]
        for n,r in rec.items():
            d=DOC/"raw"/mode/n
            assert r["status"]=="validated_scoped" and r["exit_code"]==0
            assert sha((d/"point.lie").read_bytes())==r["lie_sha256"]
            assert (d/"point.lie").read_text()==lie_text(points[n],3.610288143119805e-10)
            data={}
            assert set(r["hashes"])=={"los_modes.tsv","los_cl.tsv","run.txt","diagnostics.tsv"}
            for k,h in r["hashes"].items():
                v=gzip.decompress((d/(k+".gz")).read_bytes()) if k=="diagnostics.tsv" else (d/k).read_bytes()
                assert sha(v)==h;data[k]=v;rawcount+=1
            x,cl=decode_signed_modes(data["los_modes.tsv"],8)
            np.testing.assert_allclose(cl,np.loadtxt(io.BytesIO(data["los_cl.tsv"]),skiprows=1)[:,1:],atol=1e-24,rtol=2e-11)
            dg=np.genfromtxt(io.BytesIO(data["diagnostics.tsv"]),names=True)
            np.testing.assert_allclose(dg["proper_depth"][-1],r["depth"],rtol=1e-13)
            assert np.min(dg["min_screen_eigenvalue"])>=0.
            rt=dict(l.split("=",1) for l in data["run.txt"].decode().splitlines() if "=" in l)
            assert rt["observer_frame"]==points[n]["observer_frame"] and rt["lie_type_initial"]==rt["lie_type_final"]==points[n]["expected_type"]
            rows.append(r)
        native[mode]={"verified":len(rows),"max_gauss":max(r["max_gauss"] for r in rows),"max_codazzi":max(r["max_codazzi"] for r in rows),
            "max_jacobi":max(r["max_jacobi"] for r in rows),"min_screen":min(r["min_screen"] for r in rows),"max_spectrum_abs_error":max(r["spectrum_abs_error"] for r in rows)}
    out={"budgets_verified":counts,"adjoints_verified":len(adj["runs"]),"native_verified":sum(v["verified"] for v in native.values()),"native_raw_files_verified":rawcount,"native":native,
         "max_budget_closure_relative":closure,"max_whitened_closure_op":wclosure,"min_D_eigenvalue":psd,"max_whitening_error":white,"max_sampled_constraint":constraint,"max_generator_gap":gen,"max_adjoint_transfer_relative":adjgap,
         "scope":"re-read hashes and exact finite-state identities; not independent trajectory reintegration or survey validation"}
    (DOC/"C9_AUDIT.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n");print(json.dumps(out,indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
