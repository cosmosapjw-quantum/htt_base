"""Signed native response compared with independent finite-L tensor oracle."""
import hashlib,json
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from scripts.r123.verify_sources import DOC
from scripts.r123.plan import make
def sha(b):return hashlib.sha256(b).hexdigest()
def un(v):
    a=np.asarray(v,dtype=float);return a[...,0]+1j*a[...,1]
def pack(v):
    a=np.asarray(v);return np.stack((a.real,a.imag),axis=-1).tolist()
def norm(v):return float(np.linalg.norm(v))
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
        x,_=decode_signed_modes(raw,8);sky[name]=x[4:]
    return {v["name"]:v for v in records},sky
def cmp(sky,meta,family,tag,eps,ref,tau):
    p=sky[f"{family}_{tag}_pos"];m=sky[f"{family}_{tag}_neg"];odd=(p-m)/(2*eps);even=(p+m)/2
    mask=np.concatenate([abs(np.arange(-l,l+1))==2 for l in range(2,9)])
    err=odd-ref
    return {"eps":eps,"response_norm":norm(odd),"relative_signed_error":norm(err)/norm(ref),
        "channel_relative_errors":(np.linalg.norm(err,axis=0)/np.linalg.norm(ref,axis=0)).tolist(),
        "channel_norms":np.linalg.norm(odd,axis=0).tolist(),"even_midpoint_norm":norm(even),
        "forbidden_m_per_seed_norm":norm(odd[~mask]),"T_E_B_l2_m2_ri":pack(odd[4]),
        "tau":meta[f"{family}_{tag}_pos"]["depth"],"tau_abs_error":abs(meta[f"{family}_{tag}_pos"]["depth"]-tau)},odd
def main():
    mb,b=load("base");mf,f=load("fine");ma,a=load("angular")
    oracle=json.loads((DOC/"C6_ORACLE.json").read_text());r=oracle["runs"];rows={}
    for family in ("VII0","VIIh"):
        target=un(r[family+"_L20_tight"]["sky_ri"]);target8=un(r[family+"_L8"]["sky_ri"]);target12=un(r[family+"_L12"]["sky_ri"])
        tau=r[family+"_L20_tight"]["tau"]
        hi,xhi=cmp(b,mb,family,"hi",1e-4,target,tau)
        lo,xlo=cmp(b,mb,family,"lo",5e-5,target,tau)
        fine,xf=cmp(f,mf,family,"lo",5e-5,target,tau)
        ang,xa=cmp(a,ma,family,"lo",5e-5,target,tau)
        rows[family]={"base_hi":hi,"base_lo":lo,"fine_lo":fine,"angular_lo":ang,
          "base_seed_difference_relative":norm(xhi-xlo)/norm(xlo),"time_difference_relative":norm(xlo-xf)/norm(xf),
          "angular_difference_relative":norm(xf-xa)/norm(xa),
          "same_L_error":{"base_L8":norm(xlo-target8)/norm(target8),"fine_L8":norm(xf-target8)/norm(target8),"angular_L12":norm(xa-target12)/norm(target12)},
          "oracle_reference":{"norm":norm(target),"channel_norms":np.linalg.norm(target,axis=0).tolist(),"T_E_B_l2_m2_ri":pack(target[4]),
            "B_over_E":norm(target[:,2])/norm(target[:,1]),"tau":tau},
          "time_error_ratio_to_L20":lo["relative_signed_error"]/fine["relative_signed_error"],
          "native_angular_relative_vs_oracle_truncation":norm(xf-xa)/norm(xa),
          "scope":"finite signed odd derivative; same-L comparison is diagnostic, not guaranteed same nonlinear hierarchy or LOS algorithm"}
    smoke=json.loads((DOC/"C5_SMOKE.json").read_text())["records"][0]
    replay=mb[smoke["name"]]
    exact=smoke["hashes"]["los_modes.tsv"]==replay["hashes"]["los_modes.tsv"]
    out={"counts":{"base":len(b),"fine":len(f),"angular":len(a)},"families":rows,
         "smoke_LOS_byte_replay":exact,"flat_I_relative_to_R122_Radau":oracle["flat_I_relative_to_R122_Radau"],
         "oracle_convergence":oracle["convergence_to_finite_L20_tight"],
         "physical_five_view":{"x":"signed deterministic T/E/B finite-start derivative","Q":None,"Pi":None,"F":None,"G_F":None},
         "scope":"balanced VII0/VIIh tensor sector, table-only scalar opacity; no fitted rotation, phase or amplitude"}
    (DOC/"C8_ANALYSIS.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps(out,indent=2,allow_nan=False))
if __name__=="__main__":main()
