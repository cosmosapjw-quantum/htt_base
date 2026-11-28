"""Physical-state versus signed terminal projection and opacity response."""
import json,hashlib
import numpy as np
from common.physical_memory_budget import layout
from common.native_morphology_atlas import decode_signed_modes
from scripts.r126.verify_sources import DOC
from scripts.r126.plan import make
def sha(b):return hashlib.sha256(b).hexdigest()
def norm(x):return float(np.linalg.norm(x))
def read(rec):
    p=DOC/rec["path"];assert sha(p.read_bytes())==rec["sha256"]
    with np.load(p,allow_pickle=False) as f:return {k:f[k] for k in f.files}
def pack(x):
    z=np.asarray(x);return np.stack((z.real,z.imag),axis=-1).tolist()
def physical(A,m):
    # Scalar coefficients are real physical coordinates; keep both real and
    # imaginary state rows (the latter carry the parity-odd screen).
    return np.vstack((A.real,A.imag)) if m==0 else A
def state_map(a,m):return physical(np.sqrt(a["wf"])[:,None]*a["endpoint"]@a["whitener"],m)
def pad(Y,m,L0,L1,n):
    z=np.zeros((n,Y.shape[1]),complex);first=3 if m<2 else 2;z[:first]=Y[:first]
    for old,new in zip(layout(m,L0),layout(m,L1)):z[new.start:new.start+old.stop-old.start]=Y[old]
    return z
def spec(A,err=None):
    _,s,Vh=np.linalg.svd(A,full_matrices=False);v=Vh[-1].conjugate()
    return {"singular_values":s.tolist(),"smallest_right_ri":pack(v),"smallest_residual":norm(A@v),
            "empirical_op_difference":err,"count_above_difference":None if err is None else int(np.sum(s>err))}
def load_native(mode):
    r=json.loads((DOC/f"SCAN_{mode.upper()}.json").read_text());c=json.loads((DOC/"C2_CONSTANTS.json").read_text());l=json.loads((DOC/"C1.json").read_text())
    assert r["plan_sha256"]==sha((DOC/"SCAN_PLAN.json").read_bytes()) and r["binary_sha256"]==l["binary_sha256"]
    assert r["opacity_sha256"]==c["intervention_opacity_sha256"] and r["original_opacity_sha256"]==c["original_opacity_sha256"] and r["opacity_scale"]==.25
    assert [v["name"] for v in r["records"]]==make()[mode]
    data={}
    for v in r["records"]:
        if v["status"]!="validated_scoped":raise ValueError(v)
        raw=(DOC/"raw"/mode/v["name"]/"los_modes.tsv").read_bytes();assert sha(raw)==v["hashes"]["los_modes.tsv"]
        x,_=decode_signed_modes(raw,8);data[v["name"]]=x[1:]
    return {r["name"]:r for r in r["records"]},data
def main():
    report=json.loads((DOC/"C6_BUDGET.json").read_text());records=report["runs"];out={};native={}
    mb,b=load_native("base");mf,f=load_native("fine")
    for fam in ("VII0","VIIh"):
        for m in (0,1,2):
            key=f"{fam}_m{m}";cases={}
            for tag in ("0","025","05","1"):
                row=records[f"{key}_L16_s{tag}"];lo=read(row)
                tight=tag in ("025","1");r=records[f"{key}_L20_s{tag}"] if tight else row
                a=read(r) if tight else lo;H=a["whitener"];labels=a["labels"].tolist();B=a["initial"];Y=a["endpoint"]
                W=state_map(a,m);R0=a["response_host"]@H
                high=physical(R0[3:] if m<2 else R0,m);R=physical(R0,m)
                rad=physical(a["response_radiation"]@H,m);normal=physical(a["response_normal"]@H,m)
                stgap=rgap=hgap=radgap=ngap=None
                if tight:
                    np.testing.assert_allclose(a["M"],lo["M"],rtol=1e-13,atol=1e-15)
                    Wlo=physical(np.sqrt(a["wf"])[:,None]*pad(lo["endpoint"],m,16,20,len(a["wf"]))@H,m)
                    Rlo=lo["response_host"]@H
                    stgap=float(np.linalg.norm(W-Wlo,ord=2));rgap=float(np.linalg.norm(R-physical(Rlo,m),ord=2))
                    hgap=float(np.linalg.norm(high-physical(Rlo[3:] if m<2 else Rlo,m),ord=2))
                    radgap=float(np.linalg.norm(rad-physical(lo["response_radiation"]@H,m),ord=2));ngap=float(np.linalg.norm(normal-physical(lo["response_normal"]@H,m),ord=2))
                # Per unit initial physical size, not per coordinate or a probability.
                initial=np.diag(a["M"]).real
                j=np.diag(a["J"]).real/initial;d=np.diag(a["D"]).real/initial;nc=np.diag(a["N"]).real/initial
                cols={n:{"endpoint_size_squared_over_initial":float(j[i]),"collision_budget_over_initial":float(d[i]),"noncollision_budget_over_initial":float(nc[i]),
                         "host_sky_norm_per_unit_initial_size":norm(a["response_host"][:,i])/np.sqrt(initial[i])}
                      for i,n in enumerate(labels)}
                _,sv,Vh=np.linalg.svd(R,full_matrices=False)
                # Compare the weakest signed sky direction with the full endpoint
                # state size in the SAME input direction (not distinct extremizers).
                vv=Vh[-1].conjugate()
                weak={"sky_norm":norm(R@vv),"endpoint_state_norm":norm(W@vv),
                      "collision_budget":float(np.vdot(H@vv,a["D"]@(H@vv)).real),
                      "noncollision_budget":float(np.vdot(H@vv,a["N"]@(H@vv)).real)}
                item={"scale":r["scale"],"tau":r["tau"],"L":r["L"],"columns":cols,"state":spec(W,stgap),"host":spec(R,rgap),
                      "high":spec(high,hgap),"radiation":spec(rad,radgap),"normal":spec(normal,ngap),"host_weak_direction":weak,
                      "metric_condition":float(np.linalg.cond(a["M"])),"max_closure":r["closure_relative"],
                      "min_D_eigenvalue":r["min_D_eigenvalue"],"constraint":r["max_constraint"]}
                if key=="VII0_m0":
                    i=labels.index("B");b0=norm(a["initial"][:,i]);bf=norm(Y[:,i]);expected=float(np.exp(-r["tau"]))
                    item["scalar_B_exact"]={"attenuation":bf/b0,"expected_exp_minus_tau":expected,
                         "relative_difference":abs(bf/b0-expected)/expected,"sky_norm":norm(a["response_host"][:,i]),"nonpolarization_leak":norm(Y[:layout(m,r["L"])[2].start,i])}
                cases[tag]=item
            out[key]=cases
            if fam=="VIIh" and m in (1,2):
                a=read(records[key+"_L20_s025"]);label="relative_dust" if m==1 else "metric";j=a["labels"].tolist().index(label);ref=a["sky_host"][:,:,j]
                names=[f"{key}_{label}_{side}_host" for side in ("pos","neg")]
                vals={}
                for mode,data,meta in (("base",b,mb),("fine",f,mf)):
                    pos,neg=names;odd=(data[pos]-data[neg])/1e-4
                    vals[mode]={"relative_signed_error":norm(odd-ref)/norm(ref),"norm":norm(odd),"reference_norm":norm(ref),
                                "tau_abs_error":abs(meta[pos]["depth"]-records[key+"_L20_s025"]["tau"])}
                native[key]={"column":label,**vals,"time_error_ratio":vals["base"]["relative_signed_error"]/vals["fine"]["relative_signed_error"]}
            x=cases["1"];z=cases["025"];print(key,"rank state/host/high",x["state"]["count_above_difference"],x["host"]["count_above_difference"],x["high"]["count_above_difference"],
                  "quarter rank",z["state"]["count_above_difference"],z["host"]["count_above_difference"],"B damping",x["columns"]["B"],"weak",x["host_weak_direction"],flush=True)
    smoke=json.loads((DOC/"C5_SMOKE.json").read_text())["records"][0]
    result={"sectors":out,"native":native,"counts":{"base":len(b),"fine":len(f),"oracle":len(records)},
            "smoke_LOS_byte_replay":smoke["hashes"]["los_modes.tsv"]==mb[smoke["name"]]["hashes"]["los_modes.tsv"],
            "scope":"state-size metric and finite singular spectra; empirical matrix differences not certified rank; no observational covariance; lambda!=1 controlled opacity interventions"}
    (DOC/"C8_ANALYSIS.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("NATIVE",json.dumps(native),"SMOKE",result["smoke_LOS_byte_replay"],flush=True)
if __name__=="__main__":main()
