"""Physical interference, finite-start independent I response, and weak tangent."""
import hashlib,json
import numpy as np
from common.native_morphology_atlas import decode_signed_modes
from common.morphology_conditioning import signed_split,amplitude_shape,scaled_diagnostic
from common.morphology_manifold import central_derivative
from common.finite_start_bianchi_i import axial_sky
from scripts.r120.analyze_scan import get_scan as r120_scan
from scripts.r121.analyze_scan import load as r121_scan
from scripts.r122.verify_sources import DOC
from scripts.r122.plan import make

def sha(b):return hashlib.sha256(b).hexdigest()

def compact(x):
    if isinstance(x,np.ndarray):return x.tolist()
    if isinstance(x,np.generic):return x.item()
    if isinstance(x,dict):return {k:compact(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)):return [compact(v) for v in x]
    return x

def load(mode):
    x=json.loads((DOC/f"SCAN_{mode.upper()}.json").read_text());r=x["records"];plan=make()
    if [a["name"] for a in r]!=plan[mode]:raise ValueError("registered population mismatch")
    lock=json.loads((DOC/"C1.json").read_text())
    if x["plan_sha256"]!=sha((DOC/"SCAN_PLAN.json").read_bytes()) or x["binary_sha256"]!=lock["binary_sha256"] or x["opacity_sha256"]!=lock["opacity_sha256"]:raise ValueError("scan source mismatch")
    a={}
    for v in r:
        if v["status"]!="validated_scoped":continue
        n=v["name"];raw=(DOC/"raw"/mode/n/"los_modes.tsv").read_bytes()
        if sha(raw)!=v["hashes"]["los_modes.tsv"]:raise ValueError("raw source mismatch "+n)
        sky,_=decode_signed_modes(raw,8);a[n]=sky[4:]
    return {v["name"]:v for v in r},a

def norm(x):return float(np.linalg.norm(x))

def interference(a,n):
    p,z,m=(a[n+"_"+k] for k in ("pos","zero","neg"));z,o,e=signed_split(p,z,m)
    nz,no,ne=map(norm,(z,o,e));d=z+e
    gap=norm(p)**2-norm(m)**2;rhs=float(4*np.vdot(d,o).real)
    np.testing.assert_allclose(gap,rhs,rtol=1e-10,atol=1e-18)
    return {"zero":nz,"odd":no,"even":ne,"zero_odd_ratio":nz/no,
        "cosine_zero_odd":float(np.vdot(z,o).real/(nz*no)),
        "plus_norm":norm(p),"minus_norm":norm(m),"signed_squared_gap":gap,"identity_rhs":rhs}

def der(a,n,w):return central_derivative(a[n+"_minus"],a[n+"_plus"],w)
def stencils(a,prefix="VII",shear_width=.02):
    tag="02" if shear_width==.02 else "01"
    return np.asarray([der(a,prefix+"_log_k_02",.02),der(a,prefix+"_log_A_02",.02),
        der(a,prefix+"_u_0005",.0005),der(a,prefix+"_log_shear_"+tag,shear_width)])

def qsummary(q):
    return {k:v for k,v in q.items() if k in ("amplitude","rotation_rank","grad_log_amplitude","shape_singular_values","absolute_singular_values","shape_gram","absolute_gram")}

def oracle_cmp(a,meta,tag,eps,target,tau):
    p=a["I_"+tag+"_pos"];m=a["I_"+tag+"_neg"]
    odd=(p-m)/(2*eps);even=(p+m)/2
    on=odd[2];ref=target[2]
    err=odd-target
    outside=odd.copy();outside[2]=0
    return {"eps":eps,"T20_per_seed":[float(on[0].real),float(on[0].imag)],
        "E20_per_seed":[float(on[1].real),float(on[1].imag)],"B20_per_seed":[float(on[2].real),float(on[2].imag)],
        "T20_relative_error":float(abs(on[0]-ref[0])/abs(ref[0])),"E20_relative_error":float(abs(on[1]-ref[1])/abs(ref[1])),
        "full_signed_relative_error":norm(err)/norm(target),"off_axis_per_seed_norm":norm(outside),
        "B_per_seed_norm":norm(odd[:,2]),"even_midpoint_norm":norm(even),
        "native_tau_plus":meta["I_"+tag+"_pos"]["depth"],"native_tau_minus":meta["I_"+tag+"_neg"]["depth"],
        "oracle_tau":tau,"tau_abs_diff_plus":abs(meta["I_"+tag+"_pos"]["depth"]-tau),
        "scope":"odd finite-seed derivative; even midpoint not baseline-subtracted, no zero-seed I table run"}

def main():
    mb,b=load("base");mf,f=load("fine")
    _,old120=r120_scan("fine");_,oldbase=r121_scan("base");_,oldfine=r121_scan("fine")
    cross={}
    for tag,lam in (("025",.025),("035",.035),("045",.045)):
        n="VI_l"+tag;cross[tag]={"lambda":lam,**interference(b,n)}
    # Interpolate only between adjacent actually bracketed points, in log coordinates.
    br=[]
    for i,j in (("025","035"),("035","045")):
        x,y=cross[i],cross[j];r0,r1=x["zero_odd_ratio"],y["zero_odd_ratio"]
        if (r0-1)*(r1-1)<=0:
            L=np.exp(np.log(x["lambda"])-np.log(r0)*(np.log(y["lambda"])-np.log(x["lambda"]))/(np.log(r1)-np.log(r0)))
            br.append({"bracket":[x["lambda"],y["lambda"]],"log_interpolation":float(L)})
    refined=interference(f,"VI_l035")
    prior=json.loads((DOC/"R7_PRIOR_CROSSOVER.json").read_text())
    cols16=np.asarray([der(old120,"VIIh_log_k_02",.02),der(old120,"VIIh_log_A_02",.02),
                      der(oldbase,"VII_u_0005",.0005),der(old120,"VIIh_log_shear_02",.02)])
    cols32=stencils(oldfine);cols64=stencils(f);cols64hold=stencils(f,shear_width=.01)
    center16,center32,center64=old120["VIIh"],oldfine["VII_center"],f["VII_center"]
    q16=amplitude_shape(center16,cols16);q32=amplitude_shape(center32,cols32);q64=amplitude_shape(center64,cols64)
    qhold=amplitude_shape(center64,cols64hold)
    d=np.asarray(make()["scales"])
    a=q16["shape_projected"]*d;c=q32["shape_projected"]*d;e=q64["shape_projected"]*d;held=qhold["shape_projected"]*d
    _,s,vh=np.linalg.svd(e,full_matrices=False);weak=vh[-1]
    move=scaled_diagnostic(q64["shape_projected"],{"time_3200":q32["shape_projected"],"heldout_width":qhold["shape_projected"]},d)
    fixed=scaled_diagnostic(q64["shape_projected"],{"time_3200_fixed_center":amplitude_shape(center64,cols32)["shape_projected"]},d)
    delta1=norm(c-a);delta2=norm(e-c);width=norm(held-e)
    empirical=delta2+width
    richardson=e+(e-c)/3
    absq=scaled_diagnostic(q64["rotation_projected"],{"time_3200":q32["rotation_projected"],"heldout_width":qhold["rotation_projected"]},d)
    tangent={"q1600":qsummary(q16),"q3200":qsummary(q32),"q6400":qsummary(q64),
        "moving_projection":move,"fixed_projection":fixed,"absolute":absq,
        "scaled_singular_1600":np.linalg.svd(a,compute_uv=False),"scaled_singular_3200":np.linalg.svd(c,compute_uv=False),
        "scaled_singular_6400":s,"heldout_singular":np.linalg.svd(held,compute_uv=False),
        "time_frobenius_1600_3200":delta1,"time_frobenius_3200_6400":delta2,"time_difference_ratio":delta1/delta2,
        "width_frobenius":width,"empirical_sum":empirical,"count_above_empirical_sum":int(np.sum(s>empirical)),
        "weak_direction_scaled_coordinates":weak,"weak_direction_signal":norm(e@weak),
        "weak_direction_time_difference":norm((e-c)@weak),"weak_direction_width_difference":norm((held-e)@weak),
        "richardson_singular_diagnostic":np.linalg.svd(richardson,compute_uv=False),
        "scope":"finite moving/fixed projection and observed differences; Richardson assumes second-order, not a continuum certificate"}
    oracle=json.loads((DOC/"C6_ORACLE.json").read_text());ref=oracle["methods"]["Radau"]
    target=axial_sky(ref["endpoint"],1.)
    comp={"base_hi":oracle_cmp(b,mb,"hi",1e-4,target,ref["tau"]),
          "base_lo":oracle_cmp(b,mb,"lo",5e-5,target,ref["tau"]),
          "fine_lo":oracle_cmp(f,mf,"lo",5e-5,target,ref["tau"])}
    out={"counts":{"base":len(b),"fine":len(f)},"crossover":{"base":cross,"refined_center":refined,"interpolation":br,"prior_prediction":prior["predicted_crossovers"]},
         "tangent":tangent,"oracle_comparison":comp,"physical_five_view":{"x":"native signed T/E/B","Q":None,"Pi":None,"F":None,"G_F":None},
         "scope":"finite deterministic source-response and independent first-order I only"}
    out=compact(out);(DOC/"C8_ANALYSIS.json").write_text(json.dumps(out,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"counts":out["counts"],"crossover":out["crossover"],"oracle_comparison":comp,
      "tangent":{k:out["tangent"][k] for k in ("scaled_singular_1600","scaled_singular_3200","scaled_singular_6400","heldout_singular","time_frobenius_1600_3200","time_frobenius_3200_6400","time_difference_ratio","width_frobenius","empirical_sum","count_above_empirical_sum","weak_direction_scaled_coordinates","weak_direction_signal","weak_direction_time_difference","weak_direction_width_difference","richardson_singular_diagnostic")}},indent=2))
if __name__=="__main__":main()
