"""Signed response, independent constraints and observer-frame checks."""
import ast,hashlib,json
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.codazzi_linear_response import normalizations
from scripts.r124.verify_sources import DOC
from scripts.r124.plan import make

def sha(b):return hashlib.sha256(b).hexdigest()
def pack(x):
    a=np.asarray(x);return np.stack((a.real,a.imag),axis=-1).tolist()
def un(v):
    a=np.asarray(v);return a[...,0]+1j*a[...,1]
def norm(v):return float(np.linalg.norm(v))
def relative(x,y,floor=1e-12):return norm(x-y)/norm(y) if norm(y)>floor else None
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
def pair(mode,sky,meta,key,tag,frame,eps):
    pos=f"{key}_{tag}_pos_{frame}";neg=f"{key}_{tag}_neg_{frame}"
    x,y=sky[pos],sky[neg]
    def rt(n):
        raw=(DOC/"raw"/mode/n/"run.txt").read_bytes()
        if sha(raw)!=meta[n]["hashes"]["run.txt"]:raise ValueError("frame source hash")
        return dict(line.split("=",1) for line in raw.decode().splitlines() if "=" in line)
    p,n=rt(pos),rt(neg)
    def vector(s,k):
        v=s[k];v=v[5:-1] if v.startswith("Some(") else v
        a=np.asarray(ast.literal_eval(v),dtype=float)
        if a.shape!=(3,) or not np.isfinite(a).all():raise ValueError("invalid velocity")
        return a
    velocities={k:(vector(p,k)-vector(n,k))/(2*eps) for k in ("initial_host_beta","frame_host_beta","frame_spectator_beta","frame_photon_energy_beta","frame_radiation_energy_beta","observer_beta_used")}
    return (x-y)/(2*eps),(x+y)/2,velocities,meta[pos]["depth"],[p["initial_dust_mode"],n["initial_dust_mode"]]
def cmp(result,ref,m,tau):
    odd,even,vel,depth,dust=result;err=odd-ref
    mask=np.concatenate([abs(np.arange(-l,l+1))==m for l in range(1,9)])
    return {"full_relative":relative(odd,ref),"high_relative":relative(odd[3:],ref[3:]),
        "dipole_abs_error":norm(err[:3]),"dipole_relative":relative(odd[:3],ref[:3]),
        "response_norm":norm(odd),"dipole_norm":norm(odd[:3]),"high_norm":norm(odd[3:]),
        "channel_high_relative":[relative(odd[3:,i],ref[3:,i]) for i in range(3)],
        "B_high_norm":norm(odd[3:,2]),"forbidden_m_per_seed_norm":norm(odd[~mask]),
        "even_midpoint_norm":norm(even),"T1m_ri":pack(odd[1+m,0]),"tau_abs_error":abs(depth-tau),
        "initial_dust_modes":dust,"velocity_derivative_vectors":{k:v.tolist() for k,v in vel.items()}}
def carrier(v,m):
    return complex(v[2]) if m==0 else complex(v[0],-v[1])
def main():
    scans={k:load(k) for k in ("base","fine","normal","tensor")}
    oracle=json.loads((DOC/"C6_ORACLE.json").read_text());rows={}
    for fam in ("VII0","VIIh"):
        for m in (0,1):
            key=f"{fam}_m{m}";r=oracle["runs"][key+"_L20_tight"]
            h,n=un(r["sky_ri"]["host"]),un(r["sky_ri"]["normal"])
            def p(mode,tag,frame,eps):
                meta,sky=scans[mode];return pair(mode,sky,meta,key,tag,frame,eps)
            base_hi=p("base","hi","host",1e-4);base_lo=p("base","lo","host",5e-5)
            fine=p("fine","lo","host",5e-5);normal=p("normal","lo","normal",5e-5)
            fh=cmp(fine,h,m,r["tau"]);fn=cmp(normal,n,m,r["tau"])
            bh=cmp(base_hi,h,m,r["tau"]);bl=cmp(base_lo,h,m,r["tau"])
            _,g1=normalizations(m);vel=fine[2]
            frame_difference=fine[0]-normal[0];pred=np.zeros_like(frame_difference)
            b=carrier(vel["frame_host_beta"],m);pred[1+m,0]=g1*b
            if m==1:pred[0,0]=-pred[2,0].conjugate()
            velocities={}
            for nk,ok in (("initial_host_beta","initial_coflow"),("frame_host_beta","host_beta"),("frame_spectator_beta","spectator_beta"),("frame_photon_energy_beta","photon_energy_beta"),("frame_radiation_energy_beta","total_radiation_beta")):
                x=carrier(vel[nk],m);y=complex(un(r[ok+"_ri"]))
                velocities[nk]={"native_ri":pack(x),"oracle_ri":pack(y),"absolute_error":float(abs(x-y)),"relative_error":float(abs(x-y)/abs(y)) if abs(y)>1e-12 else None}
            rows[key]={"base_hi":bh,"base_lo":bl,"fine_host":fh,"fine_normal":fn,
                "seed_difference_relative":relative(base_hi[0],base_lo[0]),"time_difference_relative":relative(base_lo[0],fine[0]),
                "time_error_ratio":bl["full_relative"]/fh["full_relative"],"velocities":velocities,
                "oracle":{"normal_dipole_norm":norm(n[:3]),"host_dipole_norm":norm(h[:3]),"high_norm":norm(h[3:]),"high_channel_norms":np.linalg.norm(h[3:],axis=0).tolist(),"max_codazzi":r["max_codazzi"]},
                "frame":{"native_dipole_delta":norm(frame_difference[:3]),"native_high_delta":norm(frame_difference[3:]),
                  "doppler_prediction_norm":norm(pred),"doppler_abs_error":norm(frame_difference[:3]-pred[:3]),
                  "doppler_relative_error":relative(frame_difference[:3],pred[:3],1e-10),"native_minus_oracle_frame_delta_abs":norm(frame_difference-(h-n))}}
    old=DOC.parent/"R123_CURVED_LINEAR_ORACLE_20261128"
    prior=json.loads((old/"C6_ORACLE.json").read_text());oldanal=json.loads((old/"C8_ANALYSIS.json").read_text())
    tensor={}
    for fam in ("VII0","VIIh"):
        ref=un(prior["runs"][fam+"_L20_tight"]["sky_ri"])
        meta,sky=scans["tensor"];r=pair("tensor",sky,meta,fam+"_m2","lo","host",5e-5);x=r[0][3:]
        err=relative(x,ref)
        tensor[fam]={"relative_6400":err,"relative_3200":oldanal["families"][fam]["fine_lo"]["relative_signed_error"],
                     "error_ratio":oldanal["families"][fam]["fine_lo"]["relative_signed_error"]/err}
    smoke=json.loads((DOC/"C5_SMOKE.json").read_text())["records"][0]
    replay=scans["base"][0][smoke["name"]]
    out={"counts":{k:len(v[1]) for k,v in scans.items()},"sectors":rows,"tensor_refinement":tensor,
         "R123_oracle_sha256":sha((old/"C6_ORACLE.json").read_bytes()),"R123_analysis_sha256":sha((old/"C8_ANALYSIS.json").read_bytes()),
         "smoke_LOS_byte_replay":smoke["hashes"]["los_modes.tsv"]==replay["hashes"]["los_modes.tsv"],
         "oracle_convergence":oracle["convergence_to_L20_tight"],
         "physical_five_view":{"x":"signed finite-start T/E/B, physical observer frame","Q":None,"Pi":None,"F":None,"G_F":None},
         "scope":"finite linear anisotropy subsystem; table-only; no regular-mode or calibrated inference"}
    (DOC/"C8_ANALYSIS.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    for n,v in rows.items():
        print(n,json.dumps({"base":v["base_lo"]["full_relative"],"fine":v["fine_host"]["full_relative"],"normal":v["fine_normal"]["full_relative"],
              "ratio":v["time_error_ratio"],"high":v["fine_host"]["high_relative"],"dipole":v["fine_host"]["dipole_abs_error"],
              "seed_diff":v["seed_difference_relative"],"oracle":v["oracle"],"frame":v["frame"],"velocities":v["velocities"]}),flush=True)
    print("TENSOR",json.dumps(tensor),"COUNTS",out["counts"],"SMOKE",out["smoke_LOS_byte_replay"])
if __name__=="__main__":main()
