#!/usr/bin/env python3
"""Reviewer-authored R30 check. No author-module imports; single bounded run."""
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time

import numpy as np
import mpmath as mp
from astropy.io import fits

ROOT = Path(__file__).resolve().parent
NUMERIC = Path('/mnt/extdrive/workdir/htt_open_data/r30_cmb_spectral_response_numeric')
CANDIDATE = NUMERIC / 'attempt_38cdf6b948a41ee9/RESULT.json'
SOURCES = {
    'LFI_RIMO_R3.31.fits': 'a4794d80b378e00aef1b5e324e2759c3fa791873f2a3edcb53c93678a48dd94b',
    'HFI_RIMO_R3.00.fits': 'deb55a5c6f76a8578e86c122f56c3f61998b803818b09c4f3e709897881fe222',
}
BANDS = [('030',25,True),('044',26,True),('070',27,True),('100',2,False),('143',4,False),('217',5,False),('353PSB',9,False)]
AUDIT = {'status':'STARTED', 'independence':'reviewer-written source; no producer/checker scientific imports', 'requested_runtime':{'model':'gpt-6-astra','effort':'xhigh'}, 'observed_runtime':'UNKNOWN', 'checks':{}, 'branches':{}}

def require(ok, label):
    if not bool(ok):
        raise AssertionError(label)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def exact(x):
    p,q = float(x).as_integer_ratio()
    return mp.mpf(p)/q

def spectral_factory():
    # Called only inside the desired workdps. Decimal constants never use floats.
    h,k,c,Tc,Td,ns,nd = map(mp.mpf, ('6.62607015e-34','1.380649e-23','299792458','2.7255','20','30000000000','353000000000'))
    def cmb(n):
        z=h*n/(k*Tc)
        e=mp.exp(-z)
        return 2*h*h*n**4*e/(c*c*k*Tc*Tc*(1-e)**2)
    bs,bd = cmb(ns),cmb(nd)
    def original_syn(n,beta):
        return bs*(n/ns)**(beta+2)
    def original_dust(n,beta,t):
        T=Td*(1+t)
        return bd*(n/nd)**(beta+3)*mp.expm1(h*nd/(k*T))/mp.expm1(h*n/(k*T))
    def analytic(n):
        s=bs*ns/n
        d=original_dust(n,mp.mpf('1.5'),mp.mpf(0))
        ls,ld=mp.log(n/ns),mp.log(n/nd)
        x,xd=h*n/(k*Td),h*nd/(k*Td)
        def log_grad_terms(z):
            e=mp.exp(-z)
            den=1-e
            return z/den, z/den-z*z*e/(den*den)
        g,zgp=log_grad_terms(x)
        gd,zdgp=log_grad_terms(xd)
        D,E=g-gd,zgp-zdgp
        return [cmb(n),s,s*ls,d,d*ld,d*D,s*ls*ls,d*ld*ld,d*D*ld,d*(D*D-D-E)]
    return analytic,original_syn,original_dust,cmb,bs,bd

def derivative_checks():
    rows=[]
    with mp.workdps(120):
        analytic,syn,dust,cmb,bs,bd=spectral_factory()
        for ghz in (20,30,70,100,217,353,600):
            n=mp.mpf(ghz)*10**9
            val=analytic(n)
            ds=[mp.diff(lambda b:syn(n,b),mp.mpf(-3),j) for j in (1,2)]
            ds += [mp.diff(lambda b:dust(n,b,mp.mpf(0)),mp.mpf('1.5'),j) for j in (1,2)]
            ds += [mp.diff(lambda t:dust(n,mp.mpf('1.5'),t),mp.mpf(0),j) for j in (1,2)]
            ds += [mp.diff(lambda b,t:dust(n,b,t),(mp.mpf('1.5'),mp.mpf(0)),(1,1))]
            an=[val[j] for j in (2,6,4,7,5,9,8)]
            errs=[abs(x-y)/max(1,abs(y)) for x,y in zip(an,ds)]
            # Strengthen the stipulated absolute floor with dimensionless derivative checks.
            units=[bs,bs,bd,bd,bd,bd,bd]
            scaled=[abs((x-y)/u)/max(1,abs(y/u)) for x,y,u in zip(an,ds,units)]
            require(max(errs)<=mp.mpf('1e-30'),f'derivatives {ghz}')
            require(max(scaled)<=mp.mpf('1e-30'),f'dimensionless derivatives {ghz}')
            if ghz==30: require(val[2]==0 and val[6]==0,'syn pivot zeros')
            if ghz==353: require(all(val[j]==0 for j in (4,5,7,8,9)),'dust pivot zeros')
            rows.append({'GHz':ghz,'contract_errors':[str(x) for x in errs],'dimensionless_errors':[str(x) for x in scaled]})
    return rows

def intake():
    tables={}
    for name,digest in SOURCES.items():
        require(sha(NUMERIC/'source'/name)==digest,'immutable source '+name)
    with fits.open(NUMERIC/'source/LFI_RIMO_R3.31.fits',memmap=False) as lfi, fits.open(NUMERIC/'source/HFI_RIMO_R3.00.fits',memmap=False) as hfi:
        require(np.array_equal(hfi[2].data,hfi[3].data),'duplicate F100 complete data')
        for name,idx,is_lfi in BANDS:
            hdu=(lfi if is_lfi else hfi)[idx]
            expected='BANDPASS_'+(name if is_lfi else ('PSB353' if name=='353PSB' else 'F'+name))
            require(hdu.name==expected,'explicit HDU '+name)
            freq=np.array(hdu.data['WAVENUMBER'],dtype=np.float64)
            trans=np.array(hdu.data['TRANSMISSION'],dtype=np.float64)
            flags=np.asarray(hdu.data['FLAG']).astype(str).reshape(-1)
            require(np.isfinite(freq).all() and np.isfinite(trans).all(),'finite raw source '+name)
            require(np.all(np.diff(freq)>0),'raw monotonic '+name)
            require(set(flags)<=set(('F','T')),'flag alphabet '+name)
            if is_lfi: require(np.all(trans>=0),'LFI nonnegativity '+name)
            tables[name]=(freq,trans,flags,is_lfi)
    return tables

def selection(table,threshold):
    f,t,flags,lfi=table
    mask=np.isfinite(f)&(f>0)
    if not lfi: mask &= (flags=='F')&(t>threshold)
    ids=np.flatnonzero(mask)
    require(len(ids)>1 and np.all(np.diff(f[ids])>0),'selected support')
    require(np.all(np.isfinite(t[ids])) and np.all(t[ids]>=0),'selected transmission')
    return ids

def quadrature(cache,indices):
    # Node weights, independently assembled from adjacent retained coordinates.
    nodes=[cache[int(i)] for i in indices]
    n=len(nodes)
    weights=[]
    for j,(nu,tau,vals) in enumerate(nodes):
        left=nu-nodes[j-1][0] if j else mp.mpf(0)
        right=nodes[j+1][0]-nu if j<n-1 else mp.mpf(0)
        weights.append((left+right)*tau/2)
    require(mp.fsum(weights)>0,'positive finite transmission integral')
    ints=[mp.fsum(w*row[2][k] for w,row in zip(weights,nodes)) for k in range(10)]
    require(ints[0]>0,'positive calibration integral')
    unity=mp.fsum(w*row[2][0] for w,row in zip(weights,nodes))/ints[0]
    require(unity==1,'CMB direct unity')
    return [v/ints[0] for v in ints[1:]],nodes[0][0],nodes[-1][0]

def responses(tables,digits):
    matrices={}
    metas={}
    with mp.workdps(digits):
        fun,*_=spectral_factory()
        caches={}
        for branch in ('A','B'):
            for name,idx,lfi in BANDS:
                key=(branch if lfi else 'shared',name)
                if key in caches: continue
                f,t,flags,_=tables[name]
                ids=selection(tables[name],1e-8)
                shift=(exact(f[-1])-exact(f[0]))/(2*(len(f)-1)) if lfi and branch=='B' else mp.mpf(0)
                nodes={}
                for i in ids:
                    nu=(exact(f[i])+shift)*10**9 if lfi else exact(f[i])*100*299792458
                    tau=exact(t[i])*(mp.mpf(int(name))*10**9/nu)**2 if lfi else exact(t[i])
                    nodes[int(i)]=(nu,tau,fun(nu))
                caches[key]=nodes
            for threshold in (1e-7,1e-8,1e-6):
                key=f'{branch}_BT_{threshold:.0e}'
                rows=[]; metadata={}
                for name,idx,lfi in BANDS:
                    ids=selection(tables[name],threshold)
                    response,lo,hi=quadrature(caches[(branch if lfi else 'shared',name)],ids)
                    rows.append(response)
                    metadata[name]={'retained_rows':len(ids),'frequency_min_Hz':float(lo),'frequency_max_Hz':float(hi),'selection_index_sha256':hashlib.sha256(ids.astype('<i8').tobytes()).hexdigest()}
                matrices[key]=mp.matrix(rows)
                metas[key]=metadata
    return matrices,metas

def rank_info(G):
    s=np.linalg.svd(G,compute_uv=False)
    require(not np.any((s>1e-12)&(s<1e-10)),'unresolved rank gap')
    return s,int(np.count_nonzero(s>=1e-10))

def independent_pivots(G):
    # Reorthogonalized residual QR, lowest index when norms are equal at roundoff.
    remaining=list(range(G.shape[1])); chosen=[]; Q=[]; margins=[]
    for _ in range(7):
        residual={}
        for j in remaining:
            v=G[:,j].copy()
            for __ in range(2):
                for q in Q: v-=q*np.dot(q,v)
            residual[j]=v
        norms={j:float(np.linalg.norm(v)) for j,v in residual.items()}
        best=max(norms.values())
        candidates=[j for j in remaining if best-norms[j]<=1e-14*best]
        j=min(candidates)
        require(best>0,'QR pivot nonzero')
        Q.append(residual[j]/np.linalg.norm(residual[j])); chosen.append(j); remaining.remove(j)
        margins.append(sorted(norms.values(),reverse=True)[:2])
    return chosen,margins

def validate_matrices(label,M,record):
    a=np.ones(7); I=np.eye(24); A=np.kron(a[:,None],I)
    out={}
    for k in (5,9):
        F=M[:,:k]; raw=np.asarray(record['F1' if k==5 else 'F2']['matrix_7xk'])
        r=record['F1' if k==5 else 'F2']
        require(raw.shape==F.shape,'raw dimensions')
        require(np.linalg.norm(raw-F)/max(1,np.linalg.norm(F))<=1e-11,'raw matrix parity')
        scale=np.linalg.norm(F,axis=0); G=F/scale
        s,rank=rank_info(G)
        sa,ra=rank_info(np.column_stack((G,a/np.linalg.norm(a))))
        require(np.allclose(r['column_scales'],scale,rtol=1e-11,atol=1e-12),'column scales')
        for measured,expected in ((s,r['normalized_singular_values']),(sa,r['normalized_augmented_singular_values'])):
            require(np.all((np.abs(measured-np.asarray(expected))<=1e-10)|(np.abs(measured-np.asarray(expected))<=1e-8*np.abs(measured))),'singular spectrum parity')
        require(rank==r['resolved_rank'] and ra==r['augmented_resolved_rank'],'rank report')
        require(r['ambiguous_singular_count']==0,'rank ambiguity report')
        projector=np.eye(7)-G@np.linalg.pinv(G,rcond=1e-12)
        pa=projector@a
        dist=np.linalg.norm(pa)/np.linalg.norm(a)
        require(abs(dist-r['principal_angle_sine'])<=1e-10,'principal distance')
        require(abs(float(s[0]/s[-1])-r['resolved_condition'])<=1e-8*float(s[0]/s[-1]),'condition')
        mult=np.array([(-1 if i%2 else 1)*(0.37+0.41*i) for i in range(k)])
        Gr=(F*mult)/np.linalg.norm(F*mult,axis=0)
        sr,rr=rank_info(Gr)
        pr=np.eye(7)-Gr@np.linalg.pinv(Gr,rcond=1e-12)
        invariance=float(np.linalg.norm(pr-projector))
        require(rr==rank and invariance<=1e-9,'nonzero rescaling invariance')
        B=np.kron(F,I)
        require(r['tensor_dimensions']=={'A':[168,24],'B':[168,24*k]},'full tensor dimensions')
        current={'rank':rank,'augmented_rank':ra,'spectrum':s.tolist(),'condition':float(s[0]/s[-1]),'principal_angle_sine':float(dist),'rescaling_projector_difference':invariance}
        if k==5:
            require(rank==5 and ra==6,'first-order rank requirements')
            w=np.linalg.lstsq(np.column_stack((a,G)).T,np.r_[1.,np.zeros(k)],rcond=None)[0]
            wc=np.asarray(r['w'])
            require(np.linalg.norm(w-wc)<=1e-8*max(1,np.linalg.norm(w)),'minimum-norm weights')
            H=np.kron(wc[None,:],I)
            ha=np.linalg.norm(H@A-I,axis=0)
            hb=np.linalg.norm(H@B,axis=0)
            require(ha.shape==(24,) and hb.shape==(120,),'complete quotient actions')
            require(max(ha)<=1e-9 and max(hb)<=1e-9,'full quotient identity/annihilation')
            require(abs(wc@a-1)<=1e-9 and np.linalg.norm(wc@G)<=1e-9,'weight constraints')
            require(r['decision']=='NUMERIC_RESOLVED_QUOTIENT' and r['full24_identified_target_rank']==24 and r['full24_lost_target_rank']==0,'quotient decision')
            require(np.asarray(r['full24_HA_column_residuals']).shape==(24,) and np.asarray(r['full24_HB_column_residuals']).shape==(120,),'saved all quotient controls')
            current.update({'weights':w.tolist(),'weight_norm':float(np.linalg.norm(w)),'HA_all24':ha.tolist(),'HB_all120':hb.tolist()})
        else:
            require(rank==7 and ra==7,'second-order full row rank')
            c=np.linalg.lstsq(F,a,rcond=None)[0]; cc=np.asarray(r['cmb_in_foreground_coefficients_9'])
            require(cc.shape==(9,),'all nine witness coefficients')
            require(np.linalg.norm(cc-c)<=1e-8*max(1,np.linalg.norm(c)),'pseudoinverse witness parity')
            rel=np.linalg.norm(F@cc-a)/np.linalg.norm(a)
            require(rel<=1e-10,'published CMB witness')
            allres=[]
            for j in range(24):
                v=I[:,j]
                allres.append(float(np.linalg.norm(A@v+B@(-np.kron(cc,v)))/np.linalg.norm(A@v)))
            require(max(allres)<=1e-9,'every signed24 degeneracy coordinate')
            picks,margins=independent_pivots(G)
            require(picks==r['independent_minor_zero_based_indices'],'deterministic QR pivots')
            minor=G[:,picks]; det=float(np.linalg.det(minor)); sm=float(np.linalg.svd(minor,compute_uv=False)[-1])
            require(abs(det-r['minor_normalized_determinant'])<=1e-8*abs(det),'selected minor determinant')
            require(abs(sm-r['minor_normalized_smin'])<=1e-10,'selected minor smin')
            require(r['decision']=='NUMERIC_FULL_ROW_RANK_DEGENERACY' and r['full24_identified_target_rank']==0 and r['full24_lost_target_rank']==24,'degeneracy decision')
            require(np.asarray(r['full24_degeneracy_relative_residuals']).shape==(24,),'saved all degeneracy coordinates')
            current.update({'coefficients':c.tolist(),'witness_residual':float(rel),'full24_degeneracy':allres,'minor_indices':picks,'minor_determinant':det,'minor_smin':sm,'QR_pivot_top_two_norms':margins})
        out['F1' if k==5 else 'F2']=current
    require(np.array_equal(np.asarray(record['F1']['matrix_7xk']),np.asarray(record['F2']['matrix_7xk'])[:,:5]),'exact first-order nesting')
    F=M[:,:5]
    dup=np.column_stack((F,F[:,0])); _,dr=rank_info(dup/np.linalg.norm(dup,axis=0))
    inj=np.column_stack((F,np.ones(7))); Gi=inj/np.linalg.norm(inj,axis=0)
    invalid=np.linalg.norm((np.eye(7)-Gi@np.linalg.pinv(Gi))@np.ones(7))
    require(dr==5 and invalid<=1e-9,'synthetic rank-loss and CMB-confounder rejection')
    out['synthetic_only']={'duplicate_column_rank':dr,'injected_CMB_projection':float(invalid)}
    return out

def run():
    require(not (ROOT/'CHECK_RESULT.json').exists(),'one-use checker output must be fresh')
    require(sha(CANDIDATE)=='b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f','candidate identity')
    candidate=json.loads(CANDIDATE.read_text())
    tables=intake()
    AUDIT['checks']['derivatives']=derivative_checks()
    m80,_=responses(tables,80)
    m120,meta=responses(tables,120)
    require(set(candidate['branches'])==set(m120),'exact six frozen branches')
    for key,M120 in m120.items():
        with mp.workdps(120):
            delta=mp.norm(m80[key]-M120)/max(1,mp.norm(M120))
            require(delta<=mp.mpf('1e-50'),'80/120 response parity '+key)
            candidate_mp=mp.matrix([[exact(x) for x in row] for row in candidate['branches'][key]['F2']['matrix_7xk']])
            fdelta=mp.norm(candidate_mp-M120)/max(1,mp.norm(M120))
            require(fdelta<=mp.mpf('1e-11'),'float/120 response parity '+key)
        M=np.asarray(M120.tolist(),dtype=float)
        record=candidate['branches'][key]
        require(record['lfi_convention']==key[0],'branch declaration')
        for name,values in meta[key].items():
            reported=record['selected_nodes'][name]
            for field in ('retained_rows','selection_index_sha256'): require(reported[field]==values[field],'selection '+key+name+field)
            for field in ('frequency_min_Hz','frequency_max_Hz'): require(math.isclose(reported[field],values[field],rel_tol=1e-14),'frequency extrema')
        require(record['cmb_unity_responses']==[1]*7,'CMB unity report')
        result=validate_matrices(key,M,record)
        result.update({'mp80_vs_mp120':str(delta),'float64_vs_mp120':str(fdelta),'selected_nodes':meta[key],'matrix120_decimal':[[mp.nstr(x,125) for x in row] for row in M120.tolist()]})
        AUDIT['branches'][key]=result
        print(json.dumps({'branch':key,'status':'INDEPENDENT_CHECK_PASSED','mp80_120':str(delta),'float120':str(fdelta)}),flush=True)
    expected={'x':'NOT_MEASURED','observed_quotient_tensor':'NOT_MEASURED','Q':'NOT_EVALUATED','F_physical':'NOT_EVALUABLE','Pi':'NOT_CALIBRATED','G_F':'NOT_APPLICABLE_FREQUENCY_IS_NOT_DEPTH'}
    require(candidate['diagnostic_bundle']==expected,'claim domains')
    require(candidate['original_L03_acceptance']=='UNCHANGED_HOLD','original acceptance ceiling')
    AUDIT['checks']['diagnostic_bundle']=expected
    AUDIT['checks']['sources']=SOURCES
    AUDIT['checks']['conditional_theorem']='P_A=(P_F*a) tensor I24: nonzero frequency residual gives rank24; zero residual gives rank0. F2 full row rank implies full signed24 lost space in the free linear moment family.'
    AUDIT['checks']['claim_scope']='finite spectral model only; no sky, noise covariance, tail/remainder bound, physical realization of signed moments, or campaign acceptance'
    AUDIT['status']='INDEPENDENT_NUMERICAL_CHECK_PASS'

if __name__=='__main__':
    started=time.monotonic()
    try:
        run()
    except BaseException as exc:
        AUDIT['status']='INDEPENDENT_NUMERICAL_CHECK_FAILED'
        AUDIT['first_failure']={'type':type(exc).__name__,'message':str(exc)}
        raise
    finally:
        AUDIT['inner_elapsed_seconds']=time.monotonic()-started
        AUDIT['environment']={'python':platform.python_version(),'numpy':np.__version__,'mpmath':mp.__version__}
        target=ROOT/'CHECK_RESULT.json'
        with target.open('x') as f:
            json.dump(AUDIT,f,indent=2,allow_nan=False)
            f.write('\n'); f.flush(); os.fsync(f.fileno())
