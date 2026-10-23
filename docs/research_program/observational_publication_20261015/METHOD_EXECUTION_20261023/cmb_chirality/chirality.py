"""Exact finite-carrier parity-odd diagnostic for retained CMB STF bundles."""
from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
INPUT = HERE.parent / "R24-CMB-CHIRALITY_INPUT.json"
Q0 = F(1, 100000)  # exact prescribed K_CMB, distinct from binary64 1e-5
RHOS = (F(0), F(1, 1000000), F(1, 100000), F(1, 10000), F(1, 1000), F(1, 20))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_check():
    if sha(INPUT) != "ecc3f8645bc904445d513f87a0b1b1e9fe07a081c6bd0a1a4a98d6594d850bc3":
        raise ValueError("frozen assignment drift")
    spec = json.loads(INPUT.read_text())
    for row in spec["sources"]:
        p = ROOT / row["path"]
        if not p.is_file() or p.stat().st_size != row["bytes"] or sha(p) != row["sha256"]:
            raise ValueError(f"immutable input drift: {row['path']}")
    return spec


def ratio(x):
    return f"{x.numerator}/{x.denominator}"


def tensor2(c):
    a, b, d, e, f = [F.from_float(float(x)) / Q0 for x in c]
    return ((a, d, e), (d, b, f), (e, f, -a-b))


def tensor3(c):
    a, b, d, e, f, g, h = [F.from_float(float(x)) / Q0 for x in c]
    entries = {(0,0,0):a,(0,0,1):b,(0,0,2):d,(0,1,1):e,
               (0,1,2):f,(0,2,2):-a-e,(1,1,1):g,(1,1,2):h,
               (1,2,2):-b-g,(2,2,2):-d-h}
    return tuple(tuple(tuple(entries[tuple(sorted((i,j,k)))] for k in range(3))
                       for j in range(3)) for i in range(3))


def mv(q, v):
    return tuple(sum(q[i][j]*v[j] for j in range(3)) for i in range(3))


def det(columns):
    a,b,c = columns
    return a[0]*(b[1]*c[2]-b[2]*c[1])-a[1]*(b[0]*c[2]-b[2]*c[0])+a[2]*(b[0]*c[1]-b[1]*c[0])


def chi(q,o):
    v = tuple(sum(o[i][j][k]*q[j][k] for j in range(3) for k in range(3)) for i in range(3))
    return det((v,mv(q,v),mv(q,mv(q,v))))


def metric(q,o):
    return sum(z*z for row in q for z in row)+sum(z*z for plane in o for row in plane for z in row)


def decimal_of(x, prec):
    with localcontext() as ctx:
        ctx.prec = prec
        return Decimal(x.numerator)/Decimal(x.denominator)


def decimal_chi(q,o,prec):
    # Independent Decimal contraction; no rational intermediate v or columns.
    with localcontext() as ctx:
        ctx.prec = prec
        a = [[decimal_of(z,prec) for z in row] for row in q]
        b = [[[decimal_of(z,prec) for z in row] for row in plane] for plane in o]
        v = [sum(b[i][j][k]*a[j][k] for j in range(3) for k in range(3)) for i in range(3)]
        w = [sum(a[i][j]*v[j] for j in range(3)) for i in range(3)]
        u = [sum(a[i][j]*w[j] for j in range(3)) for i in range(3)]
        return v[0]*(w[1]*u[2]-w[2]*u[1])-v[1]*(w[0]*u[2]-w[2]*u[0])+v[2]*(w[0]*u[1]-w[1]*u[0])


def rotate(q,o,r):
    rq = tuple(tuple(sum(r[i][a]*r[j][b]*q[a][b] for a in range(3) for b in range(3)) for j in range(3)) for i in range(3))
    ro = tuple(tuple(tuple(sum(r[i][a]*r[j][b]*r[k][c]*o[a][b][c] for a in range(3) for b in range(3) for c in range(3)) for k in range(3)) for j in range(3)) for i in range(3))
    return rq,ro


def quaternion_rotation(x,y,z,w):
    s=x*x+y*y+z*z+w*w
    if not s: raise ValueError("zero quaternion")
    return ((1-2*(y*y+z*z)/s,2*(x*y-z*w)/s,2*(x*z+y*w)/s),
            (2*(x*y+z*w)/s,1-2*(x*x+z*z)/s,2*(y*z-x*w)/s),
            (2*(x*z-y*w)/s,2*(y*z+x*w)/s,1-2*(x*x+y*y)/s))


def exact_controls():
    q=((F(1),F(0),F(0)),(F(0),F(2),F(0)),(F(0),F(0),F(-3)))
    e={(0,0,0):1,(0,0,1):0,(0,0,2):0,(0,1,1):0,(0,1,2):0,
       (0,2,2):-1,(1,1,1):1,(1,1,2):1,(1,2,2):-1,(2,2,2):-1}
    o=tuple(tuple(tuple(F(e[tuple(sorted((i,j,k)))]) for k in range(3))
                  for j in range(3)) for i in range(3))
    assert chi(q,o)==2000 and metric(q,o)>0
    for coords in ((1,2,3,4),(2,-3,5,7)):
        r=quaternion_rotation(*(F(x) for x in coords))
        assert det(tuple(tuple(r[i][j] for i in range(3)) for j in range(3)))==1
        assert all(sum(r[i][k]*r[j][k] for k in range(3))==(i==j) for i in range(3) for j in range(3))
        a,b=rotate(q,o,r)
        assert chi(a,b)==2000 and metric(a,b)==metric(q,o)
    assert chi(q,tuple(tuple(tuple(-z for z in row) for row in plane) for plane in o))==-2000
    zero2=tensor2((0,0,0,0,0)); zero3=tensor3((0,0,0,0,0,0,0))
    for a,b in ((q,zero3),(zero2,o),(tensor2((1,1,0,0,0)),o),
                (q,tensor3((1,0,0,-1,0,0,0)))):
        assert chi(a,b)==0
    return "PASS"


def bundle_result(bundle):
    if len(bundle["harmonic12_K_CMB"])!=12 or len(bundle["STF2_components_K_CMB"])!=5 or len(bundle["STF3_components_K_CMB"])!=7:
        raise ValueError("incomplete carrier")
    q=tensor2(bundle["STF2_components_K_CMB"]); o=tensor3(bundle["STF3_components_K_CMB"])
    x=chi(q,o); m2=metric(q,o)
    if sum(q[i][i] for i in range(3)) or any(sum(o[i][i][k] for i in range(3)) for k in range(3)):
        raise AssertionError("STF completion")
    # Reproduce the registered binary64 decoder's trace completion and
    # quantify its rounding plus the deliberate exact-vs-binary scale change.
    import numpy as np
    from htt.obsstat.planck_lowell_irrep_projection import stf2_components_to_tensor, stf3_components_to_tensor
    q_registered=stf2_components_to_tensor(bundle["STF2_components_K_CMB"])
    o_registered=stf3_components_to_tensor(bundle["STF3_components_K_CMB"])
    completion_abs=max(abs(float(q[i][j]*Q0)-q_registered[i,j]) for i in range(3) for j in range(3))
    completion_abs=max(completion_abs,max(abs(float(o[i][j][k]*Q0)-o_registered[i,j,k]) for i in range(3) for j in range(3) for k in range(3)))
    physical_scale=max(max(abs(float(z)) for z in bundle["STF2_components_K_CMB"]),max(abs(float(z)) for z in bundle["STF3_components_K_CMB"]))
    if completion_abs>1e-12*physical_scale:
        raise AssertionError("exact STF completion diverges from registered decoder")
    errors=[]
    if x:
        for p in (90,130):
            with localcontext() as ctx:
                ctx.prec=p
                err=abs(decimal_chi(q,o,p)-decimal_of(x,p))/abs(decimal_of(x,p))
            if err>=Decimal("1e-60"):
                raise AssertionError(f"Decimal {p} disagreement {err}")
            errors.append(str(err))
    cert=[]
    for rho in RHOS:
        ok=bool(x and m2 and x*x>36*rho*rho*(1+rho)**16*m2**9)
        cert.append({"rho":ratio(rho),"status":"CERTIFIED_SIGN_PRESERVED" if ok else "INCONCLUSIVE"})
    with localcontext() as ctx:
        ctx.prec=80
        normalized=str(decimal_of(x,80)/(decimal_of(m2,80).sqrt()**9)) if m2 else None
    qnorm2=sum(z*z for row in q for z in row)
    onorm2=sum(z*z for plane in o for row in plane for z in row)
    return {"carrier":bundle,"full_Q_dimensionless_exact": [[ratio(z) for z in row] for row in q],
            "full_O_dimensionless_exact": [[[ratio(z) for z in row] for row in plane] for plane in o],
            "chi_exact":ratio(x),"chi_sign":(x>0)-(x<0),"m2_exact":ratio(m2),
            "Q_norm2_exact":ratio(qnorm2),"O_norm2_exact":ratio(onorm2),"detQ_exact":ratio(det(q)),
            "mirror_chi_exact":ratio(-x),"mirror_blocknorms_and_detQ_unchanged_exact":True,
            "chi_over_m9_decimal80":normalized,"mirror_SO3_distance_lower_exact":ratio(abs(x)/(3*m2**4)) if m2 else None,
            "mirror_O3_distance_exact":"0/1", "decimal90_130_relative_errors":errors,
            "registered_decoder_completion_max_abs_K_CMB":completion_abs,
            "registered_decoder_completion_scaled_difference":completion_abs/physical_scale if physical_scale else 0,
            "perturbation_scenarios":cert,
            "zero_strata":(["CHI_ZERO_INCONCLUSIVE"] if not x else [])+(["M_ZERO_NORMALIZED_UNDEFINED"] if not m2 else [])}


def key(b): return (b["source"],b["product"],b["lmax"],b["secondary_window_degrees"])


def compare(rows):
    by={key(z["carrier"]):z for z in rows}
    out=[]
    for z in rows:
        b=z["carrier"]
        if b["product"]=="full": continue
        f=by[(b["source"],"full",b["lmax"],b["secondary_window_degrees"])]
        out.append({"kind":"same_processing_split_vs_full","a":key(f["carrier"]),"b":key(b),"chi_signs":[f["chi_sign"],z["chi_sign"]],"same_sky":True})
    for z in rows:
        b=z["carrier"]
        if b["source"]=="pilot_cached" and b["secondary_window_degrees"]==0:
            p=by[("hash_pinned_primary",b["product"],b["lmax"],0)]
            out.append({"kind":"primary_vs_pilot_zero_window","a":key(p["carrier"]),"b":key(b),"chi_signs":[p["chi_sign"],z["chi_sign"]],"same_sky":True})
        if b["source"]=="pilot_cached" and b["secondary_window_degrees"] in (20,30):
            p=by[("pilot_cached",b["product"],b["lmax"],0)]
            out.append({"kind":"pilot_window_vs_zero","a":key(p["carrier"]),"b":key(b),"chi_signs":[p["chi_sign"],z["chi_sign"]],"same_sky":True})
    return out


def figure(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,(ax,sc)=plt.subplots(2,1,figsize=(11,7),gridspec_kw={"height_ratios":[2,1]},sharex=True)
    colors={"full":"black","hm1":"tab:blue","hm2":"tab:cyan","oe1":"tab:red","oe2":"tab:orange"}
    for product,color in colors.items():
        subset=[z for z in rows if z["carrier"]["product"]==product]
        xs=[i for i,z in enumerate(rows) if z in subset]
        ys=[float(Decimal(z["chi_over_m9_decimal80"])) if z["chi_over_m9_decimal80"] else 0 for z in subset]
        ax.scatter(xs,ys,label=product,s=18,color=color)
    ax.axhline(0,color="gray",lw=.7)
    ax.set(xlabel="saved carrier index (source order)",ylabel="chi / m^9",title="Parity-odd processing sensitivity, one PR3 sky")
    ax.legend(ncol=5,fontsize=8)
    import numpy as np
    cert=np.array([[p["status"]=="CERTIFIED_SIGN_PRESERVED" for p in z["perturbation_scenarios"]] for z in rows]).T
    sc.imshow(cert,aspect="auto",origin="lower",cmap="RdYlGn",vmin=0,vmax=1,extent=(-.5,len(rows)-.5,-.5,len(RHOS)-.5))
    sc.set_yticks(range(len(RHOS)),[str(float(r)) for r in RHOS])
    sc.set_ylabel("scenario radius rho")
    sc.set_xlabel("saved carrier index (source order)")
    sc.axvline(14.5,color="black",lw=.8)
    sc.set_title("pinned primary (0–14)  |  pilot cached (15–59)",fontsize=9)
    from matplotlib.patches import Patch
    sc.legend(handles=[Patch(facecolor="#006837",label="certified sign preserved"),
                       Patch(facecolor="#a50026",label="inconclusive")],
              loc="upper right",fontsize=7,ncol=2,framealpha=.9)
    fig.tight_layout()
    fig.savefig(HERE/"PROCESSING_SENSITIVITY.png",dpi=160)
    fig.savefig(HERE/"PROCESSING_SENSITIVITY.pdf")
    plt.close(fig)


def main():
    t=time.monotonic(); spec=source_check(); exact_controls()
    src=json.loads((ROOT/spec["sources"][0]["path"]).read_text())
    if len(src["bundles"])!=60 or len({key(b) for b in src["bundles"]})!=60:
        raise ValueError("60 unique saved carriers required")
    rows=[bundle_result(b) for b in src["bundles"]]
    # Exact orthogonal parity law on every saved rational carrier.
    r=quaternion_rotation(F(1),F(2),F(3),F(4))
    for b,z in zip(src["bundles"],rows):
        q=tensor2(b["STF2_components_K_CMB"]); o=tensor3(b["STF3_components_K_CMB"])
        a,c=rotate(q,o,r)
        assert chi(a,c)==chi(q,o) and metric(a,c)==metric(q,o)
        neg=tuple(tuple(tuple(-v for v in row) for row in plane) for plane in o)
        assert chi(q,neg)==-chi(q,o) and metric(q,neg)==metric(q,o)
    comparisons=compare(rows)
    result={"task_id":"R24-CMB-CHIRALITY","host_packet":"4f44a7acafa117163796f8e20728bd5afc749262f65f3ecc8724224bac70d038","input_sha256":sha(INPUT),"source_sha256":{s["path"]:s["sha256"] for s in spec["sources"]},
            "owner":"obsstat","claim_tier":"C0_PROCESSED_MAP_DIAGNOSTIC","status":"CANDIDATE_PENDING_INDEPENDENT_REVIEW",
            "scope":"finite saved corrected PR3 processed E pseudoalm carriers on one sky", "transfer_source":"none",
            "sky_support_status":"one processed observed PR3 sky", "null_mock_status":"ABSENT_MATCHED_TOTAL_FIELD_LAW",
            "generated_by":".venv/bin/python -B docs/research_program/observational_publication_20261015/METHOD_EXECUTION_20261023/cmb_chirality/chirality.py",
            "q0_o0_K_CMB_exact":ratio(Q0),"coordinate_convention":spec["theory_contract"]["coordinate_convention"],
            "harmonic_basis":src["harmonic_basis"],"projection_identity":src["projection_identity"],
            "x":{"full_rank2_rank3_carriers":"retained in all bundles","supplementary_scalar":"chi"},
            "Q":{"status":"FIXED_COMPUTATIONAL_SCALE","not_MES_Q":True},
            "Pi":{"status":"UNAVAILABLE","physical_unknown_interval":[0,1],"missing":"matched total-field law"},
            "F":{"deterministic_orbit_and_radius_certificates":True,"probability_status":"UNAVAILABLE"},
            "G_F":{"status":"SAME_SKY_PROCESSING_WINDOW_SENSITIVITY","physical_depth":False,"cross_operator_joint_response_covariance":"UNAVAILABLE"},
            "bundles":rows,"comparisons":comparisons,"p_value":None,"physical_attribution":"UNAVAILABLE",
            "same_sky_not_independent":True,"controls":"PASS","caveats":src["caveats"]}
    (HERE/"RESULT.json").write_text(json.dumps(result,indent=2)+"\n")
    figure(rows)
    receipt={"task_id":"R24-CMB-CHIRALITY","actual_agent":"/root/cmb_chirality","requested_model_effort":"gpt-6-sol/high","observed_model_effort":"UNKNOWN",
             "host_packet":"4f44a7acafa117163796f8e20728bd5afc749262f65f3ecc8724224bac70d038","input_sha256":sha(INPUT),"source_hashes_checked":result["source_sha256"],
             "bundles_processed":len(rows),"comparisons":len(comparisons),"nonzero_chi":sum(bool(z["chi_sign"]) for z in rows),
             "zero_chi":sum(not z["chi_sign"] for z in rows),"production_elapsed_seconds":time.monotonic()-t,
             "production_limit_seconds":120,"max_RSS_MiB_limit":512,"BLAS_threads":1,"status":"PASS_EXECUTION_PENDING_REVIEW"}
    if receipt["production_elapsed_seconds"]>120: raise TimeoutError("production hard limit exceeded")
    (HERE/"RAW_RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
    manifest={"task_id":"R24-CMB-CHIRALITY","input_sha256":sha(INPUT),"artifacts":{p.name:{"sha256":sha(p),"bytes":p.stat().st_size} for p in (HERE/"RESULT.json",HERE/"PROCESSING_SENSITIVITY.png",HERE/"PROCESSING_SENSITIVITY.pdf",HERE/"RAW_RECEIPT.json")}}
    (HERE/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))


if __name__=="__main__": main()
