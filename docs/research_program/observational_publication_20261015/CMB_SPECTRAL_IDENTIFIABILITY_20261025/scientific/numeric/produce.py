#!/usr/bin/env python3
"""Frozen R30 finite-table spectral moment calculation; no sky data."""
import hashlib
import argparse
import json
import math
import os
from pathlib import Path
import platform
import time

import mpmath as mp
import numpy as np
import scipy
from scipy import linalg
from astropy.io import fits
import astropy

ROOT = Path(__file__).resolve().parent
PACKET = "38cdf6b948a41ee93372fb48be413f7617e0de5bc2b6b3a704b153cc4ef011d3"
BASE_PACKET = "b7adef654c4a44203860dc5206b80b0ebf67457709d16d46db22e2d534d40ca8"
TASK = "R30-CMB-NOMINAL-BANDPASS-MOMENT-IDENTIFIABILITY"
INPUT = "sha256:cfe7be664ca43841e1197653dc4391b9c64c239cca54eebce9a06def80d916be"
EXPECTED = {"LFI_RIMO_R3.31.fits": "a4794d80b378e00aef1b5e324e2759c3fa791873f2a3edcb53c93678a48dd94b", "HFI_RIMO_R3.00.fits": "deb55a5c6f76a8578e86c122f56c3f61998b803818b09c4f3e709897881fe222"}
H, K, C = 6.62607015e-34, 1.380649e-23, 299792458.0
TC, TD, NS, ND = 2.7255, 20.0, 30e9, 353e9
HM=KM=CM=TCM=TDM=NSM=NDM=None
BANDS = [("030", 25, "LFI"), ("044", 26, "LFI"), ("070", 27, "LFI"), ("100", 2, "HFI"), ("143", 4, "HFI"), ("217", 5, "HFI"), ("353PSB", 9, "HFI")]
THRESHOLDS = (1e-7, 1e-8, 1e-6)
MP_CACHE = {}

def set_mp_constants(dps):
    """Parse stipulated decimal literals anew in each active precision context."""
    global HM,KM,CM,TCM,TDM,NSM,NDM
    mp.mp.dps=dps
    HM,KM,CM,TCM,TDM,NSM,NDM=(mp.mpf(x) for x in (
        "6.62607015e-34","1.380649e-23","299792458","2.7255","20",
        "30000000000","353000000000"))

def digest(path):
    d = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            d.update(block)
    return d.hexdigest()

def exact(v):
    n, d = float(v).as_integer_ratio()
    return mp.mpf(n) / d

def f64_spectra(nu):
    x = H*nu/(K*TD)
    xd = H*ND/(K*TD)
    xc = H*nu/(K*TC)
    xcs = H*NS/(K*TC)
    xcd = H*ND/(K*TC)
    def b(n, z, temp):
        return 2*H*n**3/C**2/np.expm1(z)*z/(-np.expm1(-z))/temp
    bs, bd = b(NS, xcs, TC), b(ND, xcd, TC)
    cmb = b(nu, xc, TC)
    syn = bs*(nu/NS)**(-1)
    B = lambda n,z: 2*H*n**3/C**2/np.expm1(z)
    dust = bd*(nu/ND)**1.5*B(nu,x)/B(ND,xd)
    lns, lnd = np.log(nu/NS), np.log(nu/ND)
    g = lambda z: z/(-np.expm1(-z))
    gp = lambda z: 1/(-np.expm1(-z))-z*np.exp(-z)/(-np.expm1(-z))**2
    D = g(x)-g(xd)
    E = x*gp(x)-xd*gp(xd)
    return np.stack((cmb,syn,syn*lns,dust,dust*lnd,dust*D,syn*lns**2,dust*lnd**2,dust*D*lnd,dust*(D**2-D-E)),axis=-1)

def mp_spectra(nu):
    x = HM*nu/(KM*TDM); xd = HM*NDM/(KM*TDM)
    xc = HM*nu/(KM*TCM)
    BB = lambda n,z: 2*HM*n**3/CM**2/mp.expm1(z)
    g = lambda z: z/(-mp.expm1(-z))
    gp = lambda z: 1/(-mp.expm1(-z))-z*mp.exp(-z)/(-mp.expm1(-z))**2
    bc = BB(nu,xc)*g(xc)/TCM
    bns = BB(NSM,HM*NSM/(KM*TCM))*g(HM*NSM/(KM*TCM))/TCM
    bnd = BB(NDM,HM*NDM/(KM*TCM))*g(HM*NDM/(KM*TCM))/TCM
    s = bns*(nu/NSM)**(-1)
    d = bnd*(nu/NDM)**mp.mpf("1.5")*BB(nu,x)/BB(NDM,xd)
    ls, ld = mp.log(nu/NSM), mp.log(nu/NDM)
    D = g(x)-g(xd); E = x*gp(x)-xd*gp(xd)
    return (bc,s,s*ls,d,d*ld,d*D,s*ls**2,d*ld**2,d*D*ld,d*(D**2-D-E))

def read_tables():
    for fn, sha in EXPECTED.items():
        p = ROOT/"source"/fn
        assert digest(p) == sha, (fn, "immutable input mismatch")
    out = {}
    headers = {}
    with fits.open(ROOT/"source"/"LFI_RIMO_R3.31.fits",memmap=True) as lfi, fits.open(ROOT/"source"/"HFI_RIMO_R3.00.fits",memmap=True) as hfi:
        assert np.array_equal(hfi[2].data,hfi[3].data), "F100 duplicate differs"
        for name,ix,kind in BANDS:
            hdu=(lfi if kind=="LFI" else hfi)[ix]
            assert hdu.name == ("BANDPASS_"+name if kind=="LFI" else "BANDPASS_"+("PSB353" if name=="353PSB" else "F"+name))
            nu=np.asarray(hdu.data["WAVENUMBER"],dtype=np.float64).copy()
            tau=np.asarray(hdu.data["TRANSMISSION"],dtype=np.float64).copy()
            flag=np.asarray(hdu.data["FLAG"]).astype(str).reshape(-1)
            assert len(nu)==len(tau)==len(flag)
            assert np.all(np.isfinite(nu)) and np.all(np.isfinite(tau))
            assert np.all(np.diff(nu)>0)
            if kind=="LFI":
                assert np.all(tau>=0)
            assert set(flag).issubset({"F","T"}), (name,set(flag))
            out[name]=(nu,tau,flag,kind)
            headers[name]={"hdu_index":ix,"extname":hdu.name,"rows":len(nu),"PROCVER":hdu.header.get("PROCVER"),"DATE":hdu.header.get("DATE"),"comments":[str(x) for x in hdu.header.get("COMMENT",[])],"frequency_raw_unit":"GHz" if kind=="LFI" else "cm^-1","transmission_dtype":str(hdu.data["TRANSMISSION"].dtype),"frequency_dtype":str(hdu.data["WAVENUMBER"].dtype)}
    return out,headers

def select(tables,name,branch,bt):
    raw,trans,flag,kind=tables[name]
    if kind=="LFI":
        sel=np.isfinite(raw)&(raw>0)
        shift=(raw[-1]-raw[0])/(2*(len(raw)-1)) if branch=="B" else 0.0
        nu=(raw[sel]+shift)*1e9
        tau=trans[sel]*(float(name)*1e9/nu)**2
    else:
        assert set(flag).issubset({"F","T"})
        sel=(raw>0)&(flag=="F")&(trans>bt)
        nu=raw[sel]*100*C
        tau=trans[sel]
        shift=0.0
    assert len(nu)>1 and np.all(np.diff(nu)>0) and np.all(tau>=0)
    assert np.trapezoid(tau,nu)>0
    return nu,tau,{"retained_rows":int(sel.sum()),"frequency_min_Hz":float(nu[0]),"frequency_max_Hz":float(nu[-1]),"lfi_added_shift_raw_GHz":float(shift),"selection_index_sha256":hashlib.sha256(np.flatnonzero(sel).astype("<i8").tobytes()).hexdigest()}

def float_matrix(tables,branch,bt):
    rows=[]; selections={}; unity=[]
    for name,*_ in BANDS:
        nu,tau,meta=select(tables,name,branch,bt)
        f=f64_spectra(nu)
        integ=np.trapezoid(tau[:,None]*f,nu,axis=0)
        assert integ[0]>0
        rows.append(integ[1:]/integ[0]); unity.append(float(integ[0]/integ[0])); selections[name]=meta
    return np.asarray(rows),selections,unity

def mp_matrix(tables,branch,bt,dps):
    set_mp_constants(dps)
    rows=[]
    for name,*_ in BANDS:
        raw,trans,flag,kind=tables[name]
        nu64,tau64,_=select(tables,name,branch,bt)
        key=(dps,branch if kind=="LFI" else "HFI",name)
        if key not in MP_CACHE:
            if kind=="LFI":
                shift=(exact(raw[-1])-exact(raw[0]))/(2*(len(raw)-1)) if branch=="B" else mp.mpf(0)
                inds0=[i for i,v in enumerate(raw) if v>0]
                nus=[(exact(raw[i])+shift)*10**9 for i in inds0]
                taus=[exact(trans[i])*(mp.mpf(int(name))*10**9/n)**2 for i,n in zip(inds0,nus)]
            else:
                inds0=[i for i in range(len(raw)) if raw[i]>0 and flag[i]=="F" and trans[i]>1e-8]
                nus=[exact(raw[i])*100*CM for i in inds0]
                taus=[exact(trans[i]) for i in inds0]
            MP_CACHE[key]=[(i,n,t,mp_spectra(n)) for i,n,t in zip(inds0,nus,taus)]
        cached=MP_CACHE[key]
        retained=[v for v in cached if kind=="LFI" or trans[v[0]]>bt]
        assert len(retained)==len(nu64)
        sumv=[mp.mpf(0)]*10
        old=None
        for _,n,t,v in retained:
            if old is not None:
                pn,pt,pv=old
                width=(n-pn)/2
                for j in range(10): sumv[j]+=width*(pt*pv[j]+t*v[j])
            old=(n,t,v)
        rows.append([z/sumv[0] for z in sumv[1:]])
    return rows

def minor_pivots(F):
    q=[]; unused=list(range(F.shape[1])); picks=[]
    for _ in range(7):
        scores=[]
        for j in unused:
            v=F[:,j].copy()
            for z in q: v-=np.dot(z,v)*z
            scores.append((float(np.linalg.norm(v)),j,v))
        maximum=max(t[0] for t in scores)
        score,j,v=min((t for t in scores if maximum-t[0]<=1e-14*maximum),key=lambda t:t[1])
        assert score>0
        q.append(v/score); picks.append(j); unused.remove(j)
    return picks

def assess(F):
    a=np.ones(7)
    scales=np.linalg.norm(F,axis=0)
    assert np.all(scales>0)
    G=F/scales
    u,s,vh=np.linalg.svd(G,full_matrices=True)
    rank=int(np.sum(s>=1e-10)); middle=int(np.sum((s>1e-12)&(s<1e-10)))
    aug=np.column_stack((G,a/np.linalg.norm(a)))
    sa=np.linalg.svd(aug,compute_uv=False)
    ra=int(np.sum(sa>=1e-10))
    pr=a-u[:,:rank]@(u[:,:rank].T@a)
    dist=float(np.linalg.norm(pr)/np.linalg.norm(a))
    answer={"matrix_7xk":F.tolist(),"column_scales":scales.tolist(),"normalized_singular_values":s.tolist(),"normalized_augmented_singular_values":sa.tolist(),"resolved_rank":rank,"ambiguous_singular_count":middle,"augmented_resolved_rank":ra,"principal_angle_sine":dist,"principal_angle_rad":float(np.arcsin(min(1,dist))),"resolved_condition":float(s[0]/s[rank-1]) if rank else None,"full24_coordinate_order":"frequency-major blocks of E2(m0,sqrt2Re,-sqrt2Im),E3,B2,B3","tensor_dimensions":{"A":[168,24],"B":[168,24*F.shape[1]]}}
    A=np.kron(a[:,None],np.eye(24))
    B=np.kron(F,np.eye(24))
    if F.shape[1]==5 and rank==5 and ra==6 and not middle:
        w=pr/np.dot(a,pr)
        H24=np.kron(w[None,:],np.eye(24))
        wa=float(w@a); wf=w@G
        ar=H24@A-np.eye(24); br=H24@B
        assert abs(wa-1)<=1e-9 and np.linalg.norm(wf)<=1e-9
        assert np.linalg.norm(ar,axis=0).max()<=1e-9 and np.linalg.norm(br,axis=0).max()<=1e-9
        answer.update({"decision":"NUMERIC_RESOLVED_QUOTIENT","w":w.tolist(),"wTa":wa,"wTF_normalized":wf.tolist(),"w_norm2":float(np.linalg.norm(w)),"full24_HA_column_residuals":np.linalg.norm(ar,axis=0).tolist(),"full24_HB_column_residuals":np.linalg.norm(br,axis=0).tolist(),"full24_lost_target_rank":0,"full24_identified_target_rank":24})
    elif F.shape[1]==9 and rank==7 and not middle:
        c=np.linalg.pinv(F,rcond=1e-12)@a
        rel=float(np.linalg.norm(F@c-a)/np.linalg.norm(a))
        piv=minor_pivots(G); selected=G[:,piv]
        det=float(np.linalg.det(selected)); smin=float(np.linalg.svd(selected,compute_uv=False)[-1])
        W=A-B@np.kron(c[:,None],np.eye(24))
        per=np.linalg.norm(W,axis=0)/np.linalg.norm(A,axis=0)
        assert rel<=1e-10 and np.max(per)<=1e-9
        answer.update({"decision":"NUMERIC_FULL_ROW_RANK_DEGENERACY","cmb_in_foreground_coefficients_9":c.tolist(),"cmb_reconstruction_relative_residual":rel,"independent_minor_zero_based_indices":piv,"minor_normalized_determinant":det,"minor_normalized_smin":smin,"full24_degeneracy_relative_residuals":per.tolist(),"full24_lost_target_rank":24,"full24_identified_target_rank":0,"witness":"for every signed24 v, delta_s=v; delta_u=-c tensor v"})
    else:
        answer.update({"decision":"NUMERIC_RANK_HOLD","full24_identified_target_rank":"HOLD","full24_lost_target_rank":"HOLD"})
    return answer

def derivative_control():
    set_mp_constants(120)
    errs=[]; zeros={}
    def syn(beta,n):
        x=HM*NSM/(KM*TCM)
        return (2*HM*NSM**3/CM**2/mp.expm1(x)* (x/(-mp.expm1(-x)))/TCM)*(n/NSM)**(beta+2)
    def dust(beta,t,n):
        x=HM*n/(KM*TDM*(1+t)); xd=HM*NDM/(KM*TDM*(1+t))
        xc=HM*NDM/(KM*TCM)
        bnd=2*HM*NDM**3/CM**2/mp.expm1(xc)*(xc/(-mp.expm1(-xc)))/TCM
        B=lambda nn,xx: 2*HM*nn**3/CM**2/mp.expm1(xx)
        return bnd*(n/NDM)**beta*B(n,x)/B(NDM,xd)
    for ghz in (20,30,70,100,217,353,600):
        n=mp.mpf(ghz)*10**9; spec=mp_spectra(n)
        numerical=[mp.diff(lambda beta:syn(beta,n),mp.mpf(-3),k) for k in (1,2)]
        numerical.extend((mp.diff(lambda beta:dust(beta,mp.mpf(0),n),mp.mpf("1.5"),k) for k in (1,2)))
        numerical.extend((mp.diff(lambda t:dust(mp.mpf("1.5"),t,n),mp.mpf(0),k) for k in (1,2)))
        numerical.append(mp.diff(lambda beta:mp.diff(lambda t:dust(beta,t,n),mp.mpf(0)),mp.mpf("1.5")))
        for analytical,actual in zip((spec[2],spec[6],spec[4],spec[7],spec[5],spec[9],spec[8]),numerical):
            err=abs(analytical-actual)/max(mp.mpf(1),abs(actual))
            errs.append(float(err))
            assert err<=mp.mpf("1e-30")
        if ghz==30: zeros["syn_beta_at_ref"]=[float(spec[2]),float(spec[6])]
        if ghz==353: zeros["dust_beta_t_at_ref"]=[float(spec[j]) for j in (4,5,7,8,9)]
    assert max(abs(z) for values in zeros.values() for z in values)<1e-45
    return {"max_independent_120digit_relative_derivative_error":max(errs),"reference_derivative_zeros":zeros}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--output-dir",required=True)
    args=parser.parse_args()
    out=Path(args.output_dir).resolve()
    assert out.parent==ROOT and out!=ROOT and out.is_dir()
    assert not (out/"RESULT.json").exists(),"fresh output required"
    started=time.monotonic()
    go=json.loads((ROOT.parent/"r30_spectral_dispatch"/"ROOT_REPAIR_GO.json").read_text())
    assert go["packet_id"]==PACKET and go["input_identity"]==INPUT
    assert go["agent_id"]=="/root/rc_b7adef654c4a4420"
    assert go["status"]=="ROOT_GO_BOUNDED_REPAIR"
    tables,headers=read_tables()
    dcontrol=derivative_control()
    branches={}
    for branch in ("A","B"):
      for bt in THRESHOLDS:
        key=f"{branch}_BT_{bt:.0e}"
        M,sel,unity=float_matrix(tables,branch,bt)
        M80=mp_matrix(tables,branch,bt,80)
        M120mp=mp_matrix(tables,branch,bt,120)
        M120=np.asarray([[float(v) for v in row] for row in M120mp])
        rel_f=float(np.linalg.norm(M-M120)/max(1,np.linalg.norm(M120)))
        rel_mp=float(mp.sqrt(mp.fsum((M80[i][j]-M120mp[i][j])**2 for i in range(7) for j in range(9)))/max(mp.mpf(1),mp.sqrt(mp.fsum(v*v for row in M120mp for v in row))))
        assert rel_f<=1e-11 and rel_mp<=1e-50,(key,rel_f,rel_mp)
        f1=assess(M[:,:5]); f2=assess(M)
        for n in (5,9):
            singular_mp=np.linalg.svd(M120[:,:n]/np.linalg.norm(M120[:,:n],axis=0),compute_uv=False)
            singular_f=np.asarray((f1 if n==5 else f2)["normalized_singular_values"])
            assert np.all(np.abs(singular_mp-singular_f)<=1e-10+1e-8*np.abs(singular_mp))
        assert np.allclose(M[:,:5],np.asarray(f2["matrix_7xk"])[:,:5],atol=0,rtol=0)
        assert all(v==1 for v in unity)
        # Synthetic controls: duplicate column, then blackbody nuisance. Both must destroy the respective rank/quotient.
        dup=np.column_stack((M[:,:5],M[:,0]))
        dup_rank=int(np.linalg.matrix_rank(dup/np.linalg.norm(dup,axis=0),tol=1e-10))
        cmb=np.column_stack((M[:,:5],np.ones(7)))
        cmb_res=float(np.linalg.norm(np.ones(7)-cmb@np.linalg.pinv(cmb)@np.ones(7)))
        assert dup_rank==5 and cmb_res<=1e-9
        branches[key]={"lfi_convention":branch,"hfi_threshold":bt,"selected_nodes":sel,"cmb_unity_responses":unity,"float64_vs_120_relative_frobenius":rel_f,"mp80_vs_mp120_relative_frobenius":rel_mp,"F1":f1,"F2":f2,"synthetic_controls":{"duplicate_six_column_rank":dup_rank,"injected_CMB_nuisance_projection_residual":cmb_res}}
    elapsed=time.monotonic()-started
    result={"packet_id":PACKET,"base_packet_id":BASE_PACKET,"base_candidate_identity":None,"base_raw_receipt":{"path":str(ROOT/"RAW_RECEIPT.json"),"sha256":"de3e9bfd950804dfffde883cac54191aea6d7a05b753c28bae142df012b35e1f"},"repair_plan_identity":"bed6207a978d4bd747e3addcc21b9f6d3278fd6425d403ad3a8558c6851c818b","task_id":TASK,"input_identity":INPUT,"agent_id":"/root/rc_b7adef654c4a4420","scope":"finite released table common spatial response conditional model; no sky fit","status":"PRODUCER_COMPUTED_PENDING_INDEPENDENT_CHECK","independent_review":"PENDING","original_L03_acceptance":"UNCHANGED_HOLD","requested_runtime":{"model":"gpt-6-sol","effort":"high"},"observed_runtime":"UNKNOWN","environment":{"python":platform.python_version(),"numpy":np.__version__,"scipy":scipy.__version__,"astropy":astropy.__version__,"mpmath":mp.__version__},"source_sha256":EXPECTED,"headers":headers,"derivative_controls":dcontrol,"branches":branches,"diagnostic_bundle":{"x":"NOT_MEASURED","observed_quotient_tensor":"NOT_MEASURED","Q":"NOT_EVALUATED","F_physical":"NOT_EVALUABLE","Pi":"NOT_CALIBRATED","G_F":"NOT_APPLICABLE_FREQUENCY_IS_NOT_DEPTH"},"remaining_hold":["actual spatial and component-specific response","omitted moment and frequency-tail remainder","real noise and joint null","blackbody contaminant"],"producer_inner_elapsed_seconds":elapsed}
    path=out/"RESULT.json"
    path.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print(json.dumps({"packet_id":PACKET,"task_id":TASK,"branch_summaries":{k:{"F1":v["F1"]["decision"],"F2":v["F2"]["decision"],"F1_distance":v["F1"]["principal_angle_sine"],"F2_smin":v["F2"]["normalized_singular_values"][-1]} for k,v in branches.items()},"producer_inner_elapsed_seconds":elapsed,"result_sha256":digest(path)},indent=2))

if __name__=="__main__":
    main()
