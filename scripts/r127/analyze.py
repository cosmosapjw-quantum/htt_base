"""Exact finite-table FD, native double stencil, and signed window diagnostics."""
import argparse,json,time,gzip
from pathlib import Path
import numpy as np
from common.opacity_memory_kernel import NodalWindows,solve_state
from common.initial_data_response import observe_columns
from common.physical_memory_budget import build_context
from common.native_morphology_atlas import decode_signed_modes
from scripts.r127.run_tangent import inputs,context,seed_matrix,sha
from scripts.r127.plan import groups,LABELS,make
from scripts.r127.verify_sources import DOC
def norm(x):return float(np.linalg.norm(x))
def read(r):
    p=DOC/r["path"];assert sha(p.read_bytes())==r["sha256"]
    with np.load(p,allow_pickle=False) as f:return {k:f[k] for k in f.files}
def load_native(mode):
    r=json.loads((DOC/f"SCAN_{mode.upper()}.json").read_text());const=json.loads((DOC/"C2_CONSTANTS.json").read_text());lock=json.loads((DOC/"C1.json").read_text())
    assert r["plan_sha256"]==sha((DOC/"SCAN_PLAN.json").read_bytes()) and r["binary_sha256"]==lock["binary_sha256"]
    assert r["opacity_sha256"]==const["original_opacity_sha256"]
    assert [v["name"] for v in r["records"]]==make()[mode]
    p={v["name"]:v for v in make()["points"]};sky={}
    for v in r["records"]:
        n=v["name"];pt=p[n];w=pt["window"]+("_minus" if pt["opacity_sign"]<0 else "_plus")
        assert v["intervention_sha256"]==const["tables"][w]["sha256"] and v["window"]==pt["window"] and v["opacity_sign"]==pt["opacity_sign"]
        if v["status"]!="validated_scoped":raise ValueError(v)
        raw=(DOC/"raw"/mode/n/"los_modes.tsv").read_bytes();assert sha(raw)==v["hashes"]["los_modes.tsv"]
        x,_=decode_signed_modes(raw,8);sky[n]=x[1:]
    return {v["name"]:v for v in r["records"]},sky
def main(scratch):
    inp=inputs(scratch);w=NodalWindows(inp["table"],groups(inp["table"]))
    r=json.loads((DOC/"C6_TANGENT.json").read_text())["runs"];k=json.loads((DOC/"C7_KERNEL.json").read_text())["runs"]
    mb,b=load_native("base");mf,f=load_native("fine")
    const=json.loads((DOC/"C2_CONSTANTS.json").read_text())
    out={};native={};root=DOC/"fd";root.mkdir(exist_ok=False)
    for key,rr in k.items():
        tight=read(r[key+"_L20"]);coarse=read(r[key+"_L12"]);a=read(rr)
        g=a["group_gradient"];mass=a["absolute_mass"];tau=a["tau"];loss=a["loss"]
        d=tight["dsky"];dl=coarse["dsky"];den=max(norm(d),1e-30)
        cancel=np.divide(abs(g),mass,out=np.zeros_like(g),where=mass>0)
        out[key]={"tau":tau.tolist(),"loss_over_initial_size":loss.tolist(),"loss_total":float(loss.sum()),
                  "channel_gradient":g.tolist(),"channel_absolute_mass":mass.tolist(),"channel_signed_over_absolute_mass":cancel.tolist(),
                  "total_goal_gradient":g.sum(axis=0).tolist(),"goal_gradient_per_tau":(g.sum(axis=0)/tau).tolist(),
                  "global_derivative":float(g.sum()),"adjoint_tangent_relative":rr["adjoint_tangent_relative"],
                  "tangent_L12_to_L20_relative":norm(d-dl)/den,
                  "tangent_heldout_L12_to_L20_relative":norm(d[:,:,:,0]-dl[:,:,:,0])/max(norm(d[:,:,:,0]),1e-30),
                  "tangent_max_constraint":r[key+"_L20"]["max_constraint"]}
        print(key,"tau",np.round(tau,6).tolist(),"loss",np.round(loss,8).tolist(),"total",np.round(g.sum(axis=0),9).tolist(),"B",np.round(g[2],9).tolist(),"Ldiff",out[key]["tangent_L12_to_L20_relative"],flush=True)
        if key not in ("VIIh_m1","VIIh_m2"):continue
        m=int(key[-1]);col="relative_dust" if m==1 else "metric";window="rec_peak" if m==1 else "rei_donor";j=LABELS.index(window)
        c=context(inp,"VIIh",m,20);weights,names=seed_matrix(c,"VIIh");assert names[1]==col
        y=c["system"]["basis"]@weights[:,1];target=d[j,:,:,1]
        fs={};arrays={"tangent":target}
        for h in (.03,.01):
            vals=[]
            for sign in (-1,1):
                e=np.zeros(5);e[j]=sign*h;tab=w.perturb(e)
                if h==.03:
                    name=window+("_minus" if sign<0 else "_plus");raw=gzip.decompress((DOC/(name+".tsv.gz")).read_bytes())
                    assert sha(raw)==const["tables"][name]["sha256"]
                    np.testing.assert_array_equal(tab,np.loadtxt(__import__("io").BytesIO(raw),skiprows=1))
                cp=build_context(**dict(inp,table=tab),a0=.005,m=m,L=20)
                z=solve_state(cp,y,rtol=2e-11,max_step=.015)["end"]
                sky=observe_columns(z[:,None],cp["system"],"host")[:,:,0];vals.append(sky)
            x=(vals[1]-vals[0])/(2*h);tag="h03" if h==.03 else "h01"
            arrays[tag]=x;arrays[tag+"_minus"]=vals[0];arrays[tag+"_plus"]=vals[1]
            fs[tag]={"width":h,"norm":norm(x),"relative_to_tangent":norm(x-target)/norm(target),"absolute_to_tangent":norm(x-target)}
        ref=arrays["h03"];runs={}
        for mode,data in (("base",b),("fine",f)):
            def odd(sign):
                suffix=window+"_"+sign
                pos=f"{key}_{col}_pos_host_{suffix}";neg=f"{key}_{col}_neg_host_{suffix}"
                return (data[pos]-data[neg])/1e-4
            x=(odd("plus")-odd("minus"))/.06;arrays["native_"+mode]=x
            runs[mode]={"norm":norm(x),"relative_to_matched_fd":norm(x-ref)/norm(ref),"relative_to_tangent":norm(x-target)/norm(target)}
        path=root/(key+".npz");np.savez_compressed(path,**arrays)
        native[key]={"column":col,"window":window,"tangent_norm":norm(target),"fd":fs,"native":runs,
                    "time_error_ratio":runs["base"]["relative_to_matched_fd"]/runs["fine"]["relative_to_matched_fd"],
                    "path":str(path.relative_to(DOC)),"sha256":sha(path.read_bytes())}
        print("NATIVE",key,native[key],flush=True)
    smoke=json.loads((DOC/"C5_SMOKE.json").read_text())["records"][0]
    result={"sectors":out,"native":native,"counts":{"base":len(b),"fine":len(f),"tangent":len(r),"adjoint":len(k),"independent_FD_solves":8},
            "smoke_LOS_byte_replay":smoke["hashes"]["los_modes.tsv"]==mb[smoke["name"]]["hashes"]["los_modes.tsv"],
            "scope":"fixed-clock source-knot perturbations; signed finite-state goals, not physical REC/REI parameter derivatives or survey likelihood",
            "physical_five_view":{"x":"signed TEB nodal response","Q":None,"Pi":None,"F":None,"G_F":None}}
    (DOC/"C8_ANALYSIS.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("COUNTS",result["counts"],"SMOKE",result["smoke_LOS_byte_replay"],flush=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
