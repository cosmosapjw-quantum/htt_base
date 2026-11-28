"""Finite response conditioning, held-out mixtures and supported native parity."""
import ast,hashlib,json
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.initial_data_response import response_matrix
from scripts.r125.verify_sources import DOC
from scripts.r125.plan import make

def sha(b):return hashlib.sha256(b).hexdigest()
def pack(x):
    a=np.asarray(x);return np.stack((a.real,a.imag),axis=-1).tolist()
def norm(x):return float(np.linalg.norm(x))
def load(mode):
    r=json.loads((DOC/f"SCAN_{mode.upper()}.json").read_text());records=r["records"]
    if [v["name"] for v in records]!=make()[mode]:raise ValueError("scan population mismatch")
    lock=json.loads((DOC/"C1.json").read_text())
    if r["plan_sha256"]!=sha((DOC/"SCAN_PLAN.json").read_bytes()) or r["binary_sha256"]!=lock["binary_sha256"] or r["opacity_sha256"]!=lock["opacity_sha256"]:raise ValueError("scan source mismatch")
    sky={}
    for v in records:
        name=v["name"]
        if v["status"]!="validated_scoped":continue
        raw=(DOC/"raw"/mode/name/"los_modes.tsv").read_bytes()
        if sha(raw)!=v["hashes"]["los_modes.tsv"]:raise ValueError("native sky hash")
        x,_=decode_signed_modes(raw,8);sky[name]=x[1:]
    return {v["name"]:v for v in records},sky
def read_oracle(rec):
    p=DOC/rec["path"]
    if sha(p.read_bytes())!=rec["sha256"]:raise ValueError("oracle identity")
    with np.load(p,allow_pickle=False) as f:return {k:f[k] for k in f.files}
def spectral(ref,lo,mid,labels):
    U,s,Vh=np.linalg.svd(ref,full_matrices=False)
    d12=float(np.linalg.norm(lo-ref,ord=2));d20=float(np.linalg.norm(mid-ref,ord=2));err=max(d12,d20)
    v=Vh[-1].conjugate()
    return {"singular_values":s.tolist(),"difference_L12_to_tight_op":d12,"difference_L20_to_tight_op":d20,
        "empirical_scale":err,"count_above_empirical_scale":int(np.count_nonzero(s>err)),
        "weak_direction_ri":pack(v),"weak_direction_residual":norm(ref@v),
        "weak_direction_delta":max(norm((lo-ref)@v),norm((mid-ref)@v)),
        "column_norms":dict(zip(labels,np.linalg.norm(ref,axis=0).tolist())),
        "scope":"chosen unit-coordinate harmonic Euclidean metric, finite discrepancies not rigorous error bound"}
def native(mode,meta,skies,key,col,m,ref,endpoint):
    names=[f"{key}_{col}_{side}_host" for side in ("pos","neg")];p,n=names
    x,y=skies[p],skies[n];eps=5e-5;odd=(x-y)/(2*eps);even=(x+y)/2
    mask=np.concatenate([abs(np.arange(-l,l+1))==m for l in range(1,9)])
    out={"response_norm":norm(odd),"reference_norm":norm(ref),"relative_signed_error":norm(odd-ref)/norm(ref),
         "high_relative_error":norm(odd[3:]-ref[3:])/norm(ref[3:]) if norm(ref[3:])>1e-14 else None,
         "dipole_abs_error":norm(odd[:3]-ref[:3]),"forbidden_m_per_seed_norm":norm(odd[~mask]),"even_midpoint_norm":norm(even),
         "native_T_E_B_l2_m_ri":pack(odd[3+2+m]),"reference_T_E_B_l2_m_ri":pack(ref[3+2+m])}
    def rtxt(name):
        raw=(DOC/"raw"/mode/name/"run.txt").read_bytes()
        if sha(raw)!=meta[name]["hashes"]["run.txt"]:raise ValueError("run.txt identity")
        return dict(l.split("=",1) for l in raw.decode().splitlines() if "=" in l)
    a,b=rtxt(p),rtxt(n)
    out["dust_modes"]=[a["initial_dust_mode"],b["initial_dust_mode"]]
    def vec(r,k):
        v=r[k];v=v[5:-1] if v.startswith("Some(") else v
        z=np.asarray(ast.literal_eval(v),float)
        if z.shape!=(3,) or not np.isfinite(z).all():raise ValueError("velocity shape")
        return z
    if m<2:
        vals={}
        for k,j in (("frame_host_beta",1),("frame_spectator_beta",2)):
            v=(vec(a,k)-vec(b,k))/(2*eps);z=complex(v[2]) if m==0 else complex(v[0],-v[1])
            vals[k]={"native_ri":pack(z),"oracle_ri":pack(endpoint[j]),"absolute_error":float(abs(z-endpoint[j]))}
        vi=(vec(a,"initial_host_beta")-vec(b,"initial_host_beta"))/(2*eps)
        vals["initial_host_beta"]={"native":vi.tolist(),"expected":[0.,0.,.843] if m==0 else [.843,0.,0.],
                                    "absolute_error":norm(vi-([0.,0.,.843] if m==0 else [.843,0.,0.]))}
        out["velocities"]=vals
    return out,odd
def main():
    mb,b=load("base");mf,f=load("fine");report=json.loads((DOC/"C6_ORACLE.json").read_text());records=report["runs"]
    out={};maxheld=0.
    for family in ("VII0","VIIh"):
        for m in (0,1,2):
            key=f"{family}_m{m}";rows={tag:read_oracle(records[key+"_"+tag]) for tag in ("L12","L20","tight","heldout")}
            ref=rows["tight"];labels=ref["labels"].tolist();held=rows["heldout"];w=held["weights"]
            end_error=norm(held["endpoint"][:,0]-ref["endpoint"]@w)/norm(held["endpoint"][:,0])
            checks={}
            for frame in ("normal","host","radiation","spectator"):
                x=ref["sky_"+frame];r=response_matrix(x,m)
                actual=response_matrix(held["sky_"+frame],m)[:,0]
                delta=norm(actual-r@w)/norm(actual)
                maxheld=max(maxheld,delta)
                lo=response_matrix(rows["L12"]["sky_"+frame],m);mid=response_matrix(rows["L20"]["sky_"+frame],m)
                checks[frame]={"full":spectral(r,lo,mid,labels),"high":spectral(response_matrix(x,m,True),response_matrix(rows["L12"]["sky_"+frame],m,True),response_matrix(rows["L20"]["sky_"+frame],m,True),labels),
                    "heldout_sky_relative":delta,"dipole_column_norms":dict(zip(labels,np.linalg.norm(x[:3],axis=(0,1)).tolist()))}
            col="metric" if m==2 else "relative_dust";j=labels.index(col);target=ref["sky_host"][:,:,j]
            lo,x0=native("base",mb,b,key,col,m,target,ref["endpoint"][:,j])
            fine,x1=native("fine",mf,f,key,col,m,target,ref["endpoint"][:,j])
            out[key]={"labels":labels,"frames":checks,"heldout_endpoint_relative":end_error,
                "prior_shear_relative":report["prior_shear_relative"][key],
                "tight_max_constraint":records[key+"_tight"]["max_constraint"],
                "native":{"column":col,"base":lo,"fine":fine,"time_error_ratio":lo["relative_signed_error"]/fine["relative_signed_error"],"base_fine_relative":norm(x0-x1)/norm(x1)}}
            h=checks["host"];r=checks["radiation"];sv=h["full"]["singular_values"]
            print(key,"host rank",h["full"]["count_above_empirical_scale"],"high",h["high"]["count_above_empirical_scale"],"rad",r["full"]["count_above_empirical_scale"],"sv",sv,"err",h["full"]["empirical_scale"],"native",lo["relative_signed_error"],fine["relative_signed_error"],"held",h["heldout_sky_relative"],flush=True)
    smoke=json.loads((DOC/"C5_SMOKE.json").read_text())["records"][0]
    result={"counts":{"base":len(b),"fine":len(f),"oracle_solves":len(records)},"sectors":out,"max_heldout_sky_relative":maxheld,
        "smoke_LOS_byte_replay":smoke["hashes"]["los_modes.tsv"]==mb[smoke["name"]]["hashes"]["los_modes.tsv"],
        "physical_five_view":{"x":"signed finite-start initial-data operator","Q":None,"Pi":None,"F":None,"G_F":None},
        "scope":"selected finite-dimensional initial space; Euclidean signed response rank diagnostics, not survey identifiability"}
    (DOC/"C8_ANALYSIS.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("COUNTS",result["counts"],"SMOKE",result["smoke_LOS_byte_replay"],"MAX_HELDOUT",maxheld)
if __name__=="__main__":main()
