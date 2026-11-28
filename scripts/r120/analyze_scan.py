"""Analyze actual native scan: finite-difference quotient metric and contraction bounds."""
import hashlib,json
from pathlib import Path
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_manifold import central_derivative, quotient_metric
from common.morphology_orbit import profile_bounds
from scripts.r120.native_scan import DOC

def digest(raw):return hashlib.sha256(raw).hexdigest()

def get_scan(mode):
    r=json.loads((DOC/f"SCAN_{mode.upper()}.json").read_text())
    meta={x["point"]:x for x in r["records"]}
    if len(meta)!=len(r["records"]):raise ValueError("duplicate run receipt")
    a={}
    for name,v in meta.items():
        if v["status"]!="validated_scoped":continue
        raw=(DOC/"raw"/mode/name/"los_modes.tsv").read_bytes()
        if digest(raw)!=v["file_sha256"]["los_modes.tsv"]:raise ValueError("native LOS identity mismatch "+name)
        modes,_=decode_signed_modes(raw,8);a[name]=modes[4:]
    return meta,a

def vector_delta(a,b,denom):
    return float(np.linalg.norm(a-b)/denom)

def stencil(a,name,w,coords):
    deriv=[]
    for c in coords:
        key=f"{name}_{c}_{int(w*100):02d}"
        deriv.append(central_derivative(a[key+"_minus"],a[key+"_plus"],w))
    return np.array(deriv)

def quotient(a,name,w,coords):
    d=stencil(a,name,w,coords);q=quotient_metric(a[name],d,2,8)
    return d,q

def compact(q):
    return {k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in q.items() if k!="projected"}

def main():
    plan=json.loads((DOC/"SCAN_PLAN.json").read_text())
    B,b=get_scan("base");F,f=get_scan("fine");A,a=get_scan("angular")
    coord=plan["coordinates"]
    local={}
    for n in ("VIh","VIIh"):
        try:
            d04,q04=quotient(b,n,.04,coord);d02,q02=quotient(b,n,.02,coord)
            df,qf=quotient(f,n,.02,coord)
        except KeyError as e:
            local[n]={"status":"incomplete_stencil","missing":str(e)};continue
        width=q04["projected"]-q02["projected"];time=q02["projected"]-qf["projected"]
        delta_w=float(np.linalg.norm(width,ord=2));delta_t=float(np.linalg.norm(time,ord=2))
        s=qf["singular_values"]
        local[n]={"status":"computed_finite_chart","coordinates":coord,
            "base_04":compact(q04),"base_02":compact(q02),"fine_02":compact(qf),
            "projected_operator_difference_width":delta_w,"projected_operator_difference_time":delta_t,
            "raw_derivative_relative_to_center_width_difference":(np.linalg.norm((d04-d02).reshape(4,-1),axis=1)/np.linalg.norm(b[n])).tolist(),
            "raw_derivative_relative_to_center_time_difference":(np.linalg.norm((d02-df).reshape(4,-1),axis=1)/np.linalg.norm(f[n])).tolist(),
            "width_column_difference":np.linalg.norm(width,axis=0).tolist(),
            "time_column_difference":np.linalg.norm(time,axis=0).tolist(),
            "fine_singular_values_above_empirical_max_difference":int(np.count_nonzero(s>max(delta_w,delta_t))),
            "rank_note":"empirical two-grid comparison only, not continuum rank or Fisher rank"}
    floor=100*max(np.linalg.norm(x["FLRW"]) for x in (b,f,a) if "FLRW" in x)
    names=[p["name"] for p in plan["points"] if p["name"] in b and p["name"]!="FLRW" and np.linalg.norm(b[p["name"]])>floor]
    index={n:i for i,n in enumerate(names)}
    lo,ident,hi=profile_bounds([b[n] for n in names],2,8,seed=120,samples=(64,256))
    def pair(n,m):
        if n not in index or m not in index:return None
        i,j=index[n],index[m]
        return {"lower":float(lo[i,j]),"identity_upper":float(ident[i,j]),"sampled_upper_256":float(hi[256][i,j]),
                "sampled_upper_64":float(hi[64][i,j]),
                "signed_relative_to_endpoint":vector_delta(b[n],b[m],np.linalg.norm(b[m])),
                "norm_ratio_to_endpoint":float(np.linalg.norm(b[n])/np.linalg.norm(b[m]))}
    canonical=[p["name"] for p in plan["points"] if p["kind"]=="representative" and p["name"] in index]
    representative=[]
    for i,n in enumerate(canonical):
        for m in canonical[i+1:]:representative.append({"pair":[n,m],**pair(n,m)})
    contractions=[]
    for n in ("VIh","VIIh"):
        for direction,endpoint in (("k_down","V_A005"),("A_down","VI0" if n=="VIh" else "VII0"),("both_down","I")):
            for tag in ("20","05"):
                name=f"{n}_{direction}_{tag}"
                contractions.append({"point":name,"endpoint":endpoint,"ratio":int(tag)/100,"metrics":pair(name,endpoint)})
    zero={}
    for n in ("VIh","VIIh"):
        zero[n]={key:{"norm":float(np.linalg.norm(b[name])),
                "channel_norms":np.linalg.norm(b[name],axis=0).tolist()} for key,name in (
                    ("positive",n),("zero",n+"_zero_shear"),("negative",n+"_negative_shear")) if name in b}
    times={}
    for n,x in f.items():
        if n not in b:continue
        times[n]={"norm_base":float(np.linalg.norm(b[n])),"norm_fine":float(np.linalg.norm(x)),
             "signed_delta":float(np.linalg.norm(b[n]-x)),
             "relative_delta":vector_delta(b[n],x,np.linalg.norm(x)) if np.linalg.norm(x)>floor else None,
             "gauss_base":B[n]["max_gauss"],"gauss_fine":F[n]["max_gauss"]}
    angular={}
    for n,x in a.items():
        if n not in f:continue
        angular[n]={"norm_fine":float(np.linalg.norm(f[n])),"norm_angular":float(np.linalg.norm(x)),
             "signed_delta":float(np.linalg.norm(f[n]-x)),
             "relative_delta":vector_delta(f[n],x,np.linalg.norm(x)) if np.linalg.norm(x)>floor else None,
             "gauss_fine":F[n]["max_gauss"],"gauss_angular":A[n]["max_gauss"]}
    by_mode={}
    for label,m in (("base",B),("fine",F),("angular",A)):
        good=[v for v in m.values() if v["status"]=="validated_scoped"]
        by_mode[label]={"requested":len(m),"validated_scoped":len(good),"failures":[{"name":n,"error":v.get("error")} for n,v in m.items() if n not in [x["point"] for x in good]],
          "max_gauss":max(x["max_gauss"] for x in good),"max_codazzi":max(x["max_codazzi"] for x in good),
          "max_jacobi":max(x["max_jacobi"] for x in good),"min_screen":min(x["min_screen"] for x in good),
          "max_spectrum_abs_error":max(x["spectrum_abs_error"] for x in good),"max_post_stop_drift":max(x["post_stop_drift"] for x in good)}
    out={"scope":"native signed dimensionless full-sky l=2..8, finite unweighted quotient; no observational covariance",
        "numeric_shape_floor":float(floor),"shape_names":names,"excluded_from_shape":[n for n in b if n not in index],
        "by_mode":by_mode,"local":local,"representative_pairs":representative,"contractions":contractions,
        "zero_shear":zero,"time_refinement":times,"joint_angular_harmonic_refinement":angular,
        "physical_five_view":{"x":"source-bound signed native T/E/B","Q":None,"Pi":None,"F":None,"G_F":None}}
    (DOC/"C8_ANALYSIS.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"runs":by_mode,"floor":float(floor),"excluded":out["excluded_from_shape"],
        "local":{n:{"fine_singular_values":v.get("fine_02",{}).get("singular_values"),
                   "width_op":v.get("projected_operator_difference_width"),"time_op":v.get("projected_operator_difference_time"),
                   "projected_norms":v.get("fine_02",{}).get("projected_column_norms")} for n,v in local.items()},
        "closest_representatives":sorted(representative,key=lambda q:q["sampled_upper_256"])[:5],
        "zero_shear":zero,"contractions":contractions,"angular":angular},indent=2))
if __name__=="__main__":main()
