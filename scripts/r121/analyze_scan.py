"""Compare signed weak-curvature responses and scaled tangents from real native data."""
import argparse, gzip, hashlib, json, shutil, subprocess, re
from pathlib import Path
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_conditioning import signed_split,amplitude_shape,scaled_diagnostic,spin2_support
from common.morphology_manifold import central_derivative
from scripts.r120.analyze_scan import get_scan as prior_scan
from scripts.r121.verify_sources import DOC,OLD
from scripts.r121.plan import make

def sha(b):return hashlib.sha256(b).hexdigest()
def compact(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,dict):return {k:compact(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [compact(v) for v in x]
    if isinstance(x,np.generic):return x.item()
    return x

def load(mode):
    x=json.loads((DOC/f"SCAN_{mode.upper()}.json").read_text())
    expected=make()[mode];r=x["records"]
    if [v["name"] for v in r]!=expected:raise ValueError("scan list mismatch")
    lock=json.loads((DOC/"C1.json").read_text())
    if x["binary_sha256"]!=lock["binary_sha256"] or x["opacity_sha256"]!=lock["opacity_sha256"] or x["plan_sha256"]!=sha((DOC/"SCAN_PLAN.json").read_bytes()):raise ValueError("scan source mismatch")
    skies={}
    for v in r:
        n=v["name"]
        if v["status"]!="validated_scoped":continue
        raw=(DOC/"raw"/mode/n/"los_modes.tsv").read_bytes()
        if sha(raw)!=v["hashes"]["los_modes.tsv"]:raise ValueError("raw identity mismatch "+n)
        sky,_=decode_signed_modes(raw,8);skies[n]=sky[4:]
    return r,skies

def parity(a,n):
    return signed_split(a[n+"_pos"],a[n+"_zero"],a[n+"_neg"])

def norms(q):return [float(np.linalg.norm(x)) for x in q]

def parity_record(q):
    z,o,e=q
    r={"norms":dict(zip(("zero","odd","even"),norms(q))),"channel_norms":dict(zip(("zero","odd","even"),[np.linalg.norm(x,axis=0).tolist() for x in q]))}
    r["cos_zero_odd"]=float(np.vdot(z,o).real/(np.linalg.norm(z)*np.linalg.norm(o))) if np.linalg.norm(z)*np.linalg.norm(o)>0 else None
    return r

def der(a,n,w):return central_derivative(a[n+"_minus"],a[n+"_plus"],w)

def summary(q):
    return {k:v for k,v in q.items() if k in ("amplitude","rotation_rank","rotation_singular_values","grad_log_amplitude","absolute_gram","shape_gram","absolute_singular_values","shape_singular_values")}

def relative(a,b,floor):
    n=np.linalg.norm(b)
    return float(np.linalg.norm(a-b)/n) if n>floor else None

def external(scratch):
    root=scratch/"aniclass";ref=Path.home()/"workdir/htt_external_physics_20261015/reference_code/AniCLASS"
    rev=subprocess.check_output(["git","-C",str(ref),"rev-parse","HEAD"],text=True).strip()
    binary_sha=sha((ref/"class").read_bytes())
    if rev!="be1e43fcb1d7549710ba3ca2baa74bb0216bd228" or binary_sha!="16f5948f95a9ac1c893c7a0d34921248b914c2e52e2f77b365e92b55a17cbed4":raise ValueError("external source identity")
    code=int((root/"exit").read_text())
    out=DOC/"external_aniclass";out.mkdir(exist_ok=False)
    keep=["input.ini","execution.log","exit"]
    alm=None;external_hashes={}
    if code==0:
        paths=list(root.glob("*_alm_q0_t.dat"))
        if len(paths)!=1:raise ValueError("external alm output count")
        path=paths[0];raw=path.read_bytes();a=np.loadtxt(path)
        if a.shape!=(11,7) or not np.isfinite(a).all() or not np.array_equal(a[:,0],np.arange(2,13)):
            raise ValueError("external tensor output layout")
        # Dense CLASS tensor output carries only non-zero m=+2 by construction.
        alm={"file":path.name,"sha256":sha(raw),"ell_range":[2,12],"dense_channel_count":6,
             "positive_m":2,"negative_m":"real-sky conjugate if reconstructed; not independently output",
             "nonzero_ell_rows":int(np.count_nonzero(np.linalg.norm(a[:,1:],axis=1)>0))}
        keep.append(path.name)
        for f in root.glob("*_perturbations_*.dat"):
            raw=f.read_bytes();external_hashes[f.name]=sha(raw)
            (out/(f.name+".gz")).write_bytes(gzip.compress(raw,mtime=0))
    # Preserve exact upstream whitespace/bytes without importing generated text
    # whitespace defects into the HTT source diff.
    for n in keep:
        raw=(root/n).read_bytes()
        (out/(n+".gz")).write_bytes(gzip.compress(raw,mtime=0))
        external_hashes[n]=sha(raw)
    if alm is not None:alm["archive_file"]=alm["file"]+".gz"
    return {"exit_code":code,"source_commit":rev,"binary_sha256":binary_sha,"input_sha256":sha((root/"input.ini").read_bytes()),
            "alm":alm,"archived_raw_sha256":external_hashes,"scope":"external conditional tensor support only; different cosmological parameters, regular mode initialization, normalization and donor; no absolute BASS parity"}

def main(scratch):
    rb,b=load("base");rf,f=load("fine");_,p=prior_scan("fine")
    floor=100*max(float(np.linalg.norm(f["FLRW"])),float(np.linalg.norm(p["FLRW"])))
    groups={};refinements={}
    for n in ("VI","VII"):
        group={}
        for tag,lam in (("10",.1),("03",.03),("01",.01)):
            key=f"{n}_l{tag}"
            q=parity(b,key)
            group[tag]={"lambda":lam,**parity_record(q),"zero_over_lambda2":float(np.linalg.norm(q[0])/lam**2),
                        "odd_over_zero":float(np.linalg.norm(q[1])/np.linalg.norm(q[0])) if np.linalg.norm(q[0])>floor else None}
            if all(key+"_"+m in f for m in ("pos","zero","neg")):
                v=parity(f,key)
                refinements[key]={"fine":parity_record(v),"absolute_deltas":norms([x-y for x,y in zip(q,v)]),
                     "relative_deltas":[relative(x,y,floor) for x,y in zip(q,v)]}
        for a,c in (("10","03"),("03","01")):
            x,y=group[a],group[c]
            n0,n1=x["norms"]["zero"],y["norms"]["zero"]
            y["zero_log_slope_from_previous"]=float(np.log(n1/n0)/np.log(y["lambda"]/x["lambda"])) if min(n0,n1)>floor else None
        groups[n]=group
    cols=[der(p,"VIIh_log_k_02",.02),der(p,"VIIh_log_A_02",.02),der(b,"VII_u_0005",.0005),der(p,"VIIh_log_shear_02",.02)]
    cols_f=[der(f,"VII_log_k_02",.02),der(f,"VII_log_A_02",.02),der(f,"VII_u_0005",.0005),der(f,"VII_log_shear_02",.02)]
    q=amplitude_shape(p["VIIh"],cols,floor=floor);qf=amplitude_shape(f["VII_center"],cols_f,floor=floor)
    width={}
    for tag,w in (("001",.001),("002",.002)):
        ds=list(cols);ds[2]=der(b,"VII_u_"+tag,w)
        width[tag]=amplitude_shape(p["VIIh"],ds,floor=floor)
    scales=make()["scales"]
    moving=scaled_diagnostic(qf["shape_projected"],{"time":q["shape_projected"]},scales)
    fixed=amplitude_shape(f["VII_center"],cols,floor=floor)
    fixed_d=scaled_diagnostic(qf["shape_projected"],{"time_fixed_projection":fixed["shape_projected"]},scales)
    widths=scaled_diagnostic(q["shape_projected"],{k:v["shape_projected"] for k,v in width.items()},scales)
    absolute=scaled_diagnostic(qf["rotation_projected"],{"time":q["rotation_projected"]},scales)
    # Sum observed time difference and max width difference, no proof of true error.
    est=moving["empirical_frobenius_scale"]+widths["empirical_frobenius_scale"]
    singular=moving["singular_values"]
    near={}
    for tag,w in (("0005",.0005),("001",.001),("002",.002)):
        a=b["VII_u_"+tag+"_minus"];c=b["VII_u_"+tag+"_plus"]
        near[tag]={"width":w,"minus_norm":float(np.linalg.norm(a)),"center_norm":float(np.linalg.norm(p["VIIh"])),
                   "plus_norm":float(np.linalg.norm(c)),"absolute_derivative_norm":float(np.linalg.norm((c-a)/(2*w))),
                   "even_delta_norm":float(np.linalg.norm((a+c)/2-p["VIIh"]))}
    tensors={"base_hi":spin2_support(b["VII_tensor_hi"]),"base_lo":spin2_support(b["VII_tensor_lo"]),"fine_lo":spin2_support(f["VII_tensor_lo"])}
    ext=external(scratch)
    # Read actual old/fine arrays and preserve numerical results before declaring science status.
    out={"scope":"finite source-conditional signed native sky; l=2..8, host frame; no survey likelihood",
        "shape_floor":floor,"weak":groups,"refinements":refinements,"near_balanced":near,
        "tangent":{"coarse":summary(q),"fine":summary(qf),"scaled_shape_time":moving,"scaled_shape_width":widths,
            "fixed_reference_projection_time":fixed_d,"scaled_absolute_time":absolute,
            "empirical_combined_difference":est,"count_above_combined_difference":int(np.count_nonzero(singular>est)),
            "coordinate_order":make()["coordinates"],"rank_scope":"empirical finite errors only"},
        "tensor_support":tensors,"external_aniclass":ext,
        "counts":{"base":len(b),"fine":len(f)}}
    out=compact(out);(DOC/"C8_ANALYSIS.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"weak":{n:{k:{"norms":v["norms"],"slope":v.get("zero_log_slope_from_previous"),"zero_over_lambda2":v["zero_over_lambda2"]} for k,v in z.items()} for n,z in out["weak"].items()},
         "tangent":{k:out["tangent"][k] for k in ("scaled_shape_time","scaled_shape_width","scaled_absolute_time","empirical_combined_difference","count_above_combined_difference")},
         "tensor_support":tensors,"external":ext,"counts":out["counts"]},indent=2))
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--scratch",type=Path,required=True);a=p.parse_args();main(a.scratch)
