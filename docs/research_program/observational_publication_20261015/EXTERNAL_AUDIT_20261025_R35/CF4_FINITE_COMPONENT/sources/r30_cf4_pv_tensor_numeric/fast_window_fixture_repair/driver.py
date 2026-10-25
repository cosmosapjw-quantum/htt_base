"""One-use R32 producer. Import is inert; runner and controller GO are required."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time

import numpy as np
from scipy.integrate import quad

import science as s
import fast_science as fast

ROOT = Path(__file__).resolve().parent
PREVIOUS = ROOT.parent / 'normalization_repair' / 'actual_run'
AMP = 765245.0820764016
DIRECT_NAMES = (
    'o35_b0_k0x1.acd9661a17d9ep-7.npz',
    'o35_b0_k0x1.b6450588a5f25p-7.npz',
    'o35_b0_k0x1.b97353b4b2faap-7.npz',
)


class Hold(RuntimeError):
    pass


def demand(ok, detail):
    if not bool(ok):
        raise Hold(detail)


def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):
            h.update(block)
    return h.hexdigest()


def atomic_json(path, payload):
    path=Path(path); temp=path.with_name(path.name+'.tmp')
    with open(temp,'w') as f:
        json.dump(payload,f,indent=2,allow_nan=False)
        f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)
    fd=os.open(path.parent,os.O_DIRECTORY|os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def atomic_npz(path, **arrays):
    path=Path(path); temp=path.with_name(path.name+'.tmp.npz')
    np.savez_compressed(temp,**arrays)
    with open(temp,'rb') as f:os.fsync(f.fileno())
    os.replace(temp,path)
    fd=os.open(path.parent,os.O_DIRECTORY|os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def source_data(bindings):
    s.verify_bindings(bindings)
    p={key:value['path'] for key,value in bindings['immutable_numeric_inputs'].items()}
    with np.load(p['corrected_factor'],allow_pickle=False) as z:
        factor={key:z[key] for key in z.files}
    with np.load(p['selected_source'],allow_pickle=False) as z:
        ids,zobs,n,method=(z[k] for k in ('group_id','z_CMB','n_J2000','method_family'))
    with open(p['corrected_result']) as f:result=json.load(f)
    demand(ids.shape==(35970,) and n.shape==(35970,3), 'SOURCE_SHAPE')
    demand(np.array_equal(ids,factor['group_id']) and
           hashlib.sha256(np.asarray(ids,dtype='<i8').tobytes()).hexdigest()==
           'f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88',
           'SOURCE_ID_ORDER')
    demand(np.all(np.isfinite(zobs)) and np.all((zobs>0)&(zobs<=.5)) and
           np.all(np.isfinite(n)) and np.max(abs(np.linalg.norm(n,axis=1)-1))<=2e-13,
           'SOURCE_DOMAINS')
    nonref=factor['nonreference_row_index']; refs=factor['difference_reference_row_index']
    demand(len(nonref)==35019 and len(refs)==35019 and
           factor['L_binary64'].shape==(5,35019), 'FIXED_OPERATOR_SHAPE')
    demand(int(np.sum(factor['exact_zero_leverage_mask']))==945 and
           int(np.sum(factor['mixed_zero_leverage_mask']))==944, 'ZERO_INDEXING')
    return {'ids':ids,'z':zobs,'n':n,'method':method,'factor':factor,'result':result}


def prior_controls(packet):
    path=Path(packet['reused_controls']['path'])
    demand(path==PREVIOUS/'CONTROLS.json' and
           digest(path)==packet['reused_controls']['sha256'], 'REUSED_CONTROLS_IDENTITY')
    prior=json.loads(path.read_text())
    demand(prior['status']=='PASS' and prior['amplitude']==AMP and
           prior['fixture']['pair_relative_frobenius']<=1e-5 and
           prior['fixture']['pair_max_normalized_entry']<=1e-6,
           'REUSED_SCALAR_CONTROL_CONTENT')
    saved=[]
    for name in DIRECT_NAMES:
        path=PREVIOUS/'spectral'/name
        demand(digest(path)==packet['saved_direct_spectral_sha256'][name],
               f'SAVED_DIRECT_SPECTRAL_IDENTITY {name}')
        with np.load(path,allow_pickle=False) as z:
            saved.append({key:z[key] for key in z.files})
    return prior,saved


def direct_oracle(k,u,positions,n,jg,L,nonref,refs):
    """Independent full-cohort difference-before-L contraction in long double."""
    x=np.asarray(positions,dtype=np.longdouble)
    uu=np.asarray(u,dtype=np.longdouble)
    kval=np.longdouble(k)
    aa=np.asarray(jg,dtype=np.longdouble)*(np.asarray(n,dtype=np.longdouble)@uu)
    theta_r=kval*(x[refs]@uu)
    delta=kval*((x[nonref]-x[refs])@uu)
    # expm1 resolves nearly equal phases without subtracting two exponentials.
    er=np.exp(np.clongdouble(1j)*theta_r)
    dd=er*((aa[nonref]-aa[refs])+aa[nonref]*np.expm1(np.clongdouble(1j)*delta))
    ll=np.asarray(L,dtype=np.longdouble)
    re=ll@dd.real; im=ll@dd.imag
    oracle=np.asarray(re,dtype=float)+1j*np.asarray(im,dtype=float)
    abs_scale=np.asarray(np.abs(ll)@(np.abs(aa[nonref])+np.abs(aa[refs])),dtype=float)
    demand(np.all(np.isfinite(oracle)) and np.all(np.isfinite(abs_scale)),
           'DIRECT_ORACLE_NONFINITE')
    return oracle,abs_scale


def direct_controls(target,maps,high,low,roundoff,saved,positions,n,jg,L,nonref,refs):
    keymap={(float(k).hex(),*(float(v).hex() for v in direction)):i
            for i,(k,*direction) in enumerate(target)}
    selected={}
    saved_results=[]
    for z in saved:
        k=float(z['k']);band=int(z['band']);
        stage=maps['A'][band]
        node=np.where(stage['k']==k)[0]
        demand(len(node)==1,'SAVED_DIRECT_NODE_MAPPING')
        A=np.einsum('t,ta,tb->ab',stage['angular_weights'],
                    high[stage['target_indices'][node[0]]],
                    high[stage['target_indices'][node[0]]].conj()).real
        truth=z['A'];scales=np.sqrt(np.diag(truth))
        demand(np.all(scales>0),'SAVED_DIRECT_NONPOSITIVE_DIAGONAL')
        fro=float(np.linalg.norm(A-truth)/np.linalg.norm(truth))
        entry=float(np.max(abs(A-truth)/np.outer(scales,scales)))
        demand(fro<=1e-6 and entry<=1e-6,
               f'NUMERICAL_METHOD_ACCURACY_HOLD saved_spectral {fro} {entry}')
        samples=[]
        for direction,expected in zip(z['sample_u'],z['sample_w'].T):
            key=(k.hex(),*(float(v).hex() for v in direction))
            demand(key in keymap,'SAVED_SAMPLE_TARGET_ABSENT')
            idx=keymap[key];selected[idx]='saved_sample'
            diff=abs(high[idx]-expected)
            samples.append(float(np.max(diff)))
            demand(np.linalg.norm(diff)<=1e-8*max(np.linalg.norm(expected),1e-30),
                   'NUMERICAL_METHOD_ACCURACY_HOLD saved_complex_sample')
        saved_results.append({'band':band,'k_hex':k.hex(), 'relative_frobenius':fro,
                              'max_normalized_entry':entry,'sample_max_abs':samples})
    # Three unique physical endpoints/split, at the first four paired directions.
    for band in maps['A']:
        for kval in (band['k'][0],band['k'][-1]):
            for u in band['directions'][:4]:
                key=(float(kval).hex(),*(float(v).hex() for v in u))
                demand(key in keymap,'ENDPOINT_TARGET_ABSENT')
                selected[keymap[key]]='endpoint_split'
    # Deterministic first-index ties, no row/field/coordinate deletion.
    for name in ('A','C'):
        indices=np.unique(np.concatenate([v['target_indices'].ravel() for v in maps[name]]))
        directions=maps[name][0]['directions']
        absolute_scales=np.empty((len(directions),5))
        # Magnitude scales depend on direction, not k. Vectorize all rows in
        # modest direction blocks; never materialize an N x N array.
        for start in range(0,len(directions),32):
            ub=directions[start:start+32]
            ai=np.abs(jg[nonref,None]*(n[nonref]@ub.T))
            ar=np.abs(jg[refs,None]*(n[refs]@ub.T))
            absolute_scales[start:start+len(ub)]=(np.abs(L)@(ai+ar)).T
        lookup={tuple(float(v).hex() for v in u):i for i,u in enumerate(directions)}
        which=np.asarray([lookup[tuple(float(v).hex() for v in target[idx,1:])]
                          for idx in indices])
        for a in range(5):
            mag=np.abs(high[indices,a]);hi=int(np.argmax(mag))
            selected[int(indices[hi])]=f'{name}_coordinate_{a}_maximum'
            scale=absolute_scales[which,a]
            score=np.divide(mag,scale,out=np.full_like(mag,np.inf),where=scale>0)
            selected[int(indices[int(np.argmin(score))])]=f'{name}_coordinate_{a}_cancellation'
    demand(len(selected)<=44,f'DIRECT_TARGET_SELECTION_COUNT {len(selected)}')
    records=[];low_delta=[];high_delta=[];allowance=[]
    for idx,reason in sorted(selected.items()):
        kval,*direction=map(float,target[idx])
        oracle,abs_scale=direct_oracle(kval,direction,positions,n,jg,L,nonref,refs)
        diff=high[idx]-oracle
        denom=float(np.linalg.norm(oracle))
        if denom:
            demand(np.linalg.norm(diff)/denom<=1e-8,
                   f'NUMERICAL_METHOD_ACCURACY_HOLD direct_l2 target={idx}')
        else:
            demand(np.all(abs_scale==0) and np.all(high[idx]==0),
                   f'NUMERICAL_METHOD_ACCURACY_HOLD exact_zero target={idx}')
        for a in range(5):
            if abs_scale[a]:
                demand(abs(diff[a])/abs_scale[a]<=1e-10,
                       f'NUMERICAL_METHOD_ACCURACY_HOLD direct_component target={idx} a={a}')
            else:
                demand(diff[a]==0, f'DIRECT_ZERO_COMPONENT target={idx} a={a}')
        low_delta.extend(abs(low[idx]-oracle).tolist())
        high_delta.extend(abs(diff).tolist())
        allowance.extend(roundoff[idx].tolist())
        records.append({'index':idx,'reason':reason,'k_hex':kval.hex(),
                        'u_hex':[v.hex() for v in direction],
                        'oracle_real':oracle.real.tolist(),'oracle_imag':oracle.imag.tolist(),
                        'high_error_abs':abs(diff).tolist(),
                        'low_error_abs':abs(low[idx]-oracle).tolist(),
                        'coefficient_abs_scale':abs_scale.tolist()})
    lo=float(np.linalg.norm(low_delta));hi=float(np.linalg.norm(high_delta))
    floor=float(np.linalg.norm(allowance))
    demand(hi<=max(.1*lo,floor),f'NUMERICAL_METHOD_ACCURACY_HOLD eps_scaling {lo} {hi} {floor}')
    return {'saved_spectral':saved_results,'oracle_targets':records,
            'low_error_l2':lo,'high_error_l2':hi,'rounding_floor_l2':floor,
            'eps_scaling_status':'ROUNDING_FLOOR_LIMITED' if lo<=floor and hi<=floor else 'PASS'}


def support_and_bounds(joints,bounds):
    observations=[]
    for label,joint,bound in zip(('band1','band2','sum'),
                                 (joints[0],joints[1],joints[0]+joints[1]),
                                 (bounds[0],bounds[1],bounds[0]+bounds[1])):
        sym,diag=s.matrix_diagnostics(joint)
        sd=np.sqrt(np.diag(sym))
        demand(np.all(sd>0),'NUMERICAL_SUPPORT_UNCERTAIN zero_diagonal')
        normalized=float(np.max(bound/np.outer(sd,sd)))
        demand(normalized<=5e-5,
               f'NUMERICAL_METHOD_ACCURACY_HOLD normalized_bound {label}={normalized}')
        block=[]
        for r in range(3):
            sl=slice(5*r,5*r+5);mat=sym[sl,sl];bb=bound[sl,sl]
            eig,vec=np.linalg.eigh(mat)
            support=eig>1e-10*eig[-1]
            demand(np.any(support),'NUMERICAL_SUPPORT_UNCERTAIN empty')
            H=(vec[:,support]/np.sqrt(eig[support]))@vec[:,support].T
            fro=float(np.linalg.norm(bb)/np.linalg.norm(mat))
            white=float(np.linalg.norm(abs(H)@bb@abs(H),2))
            demand(fro<=3e-5 and white<=2e-4,
                   f'NUMERICAL_METHOD_ACCURACY_HOLD propagated_bound {label} {r} {fro} {white}')
            block.append({'radius':r,'relative_frobenius_bound':fro,
                          'whitened_spectral_bound':white})
        observations.append({'matrix':label,'joint_diagnostics':diag,
                             'max_normalized_joint_entry_bound':normalized,
                             'diagonal_blocks':block})
    return observations


def bounded_convergence(earlier,later,be,bl):
    findings=[];passed=True
    for label,A,B,EA,EB in zip(('band1','band2','sum'),
                               (earlier[0],earlier[1],earlier[0]+earlier[1]),
                               (later[0],later[1],later[0]+later[1]),
                               (be[0],be[1],be[0]+be[1]),
                               (bl[0],bl[1],bl[0]+bl[1])):
        observed=B-A
        envelope=EA+EB
        D=abs(observed)+envelope
        sd=np.sqrt(np.diag(B));demand(np.all(sd>0),'NUMERICAL_SUPPORT_UNCERTAIN diagonal')
        norm=D/np.outer(sd,sd)
        for r in range(3):
            sl=slice(5*r,5*r+5); old=A[sl,sl];new=B[sl,sl]
            delta=observed[sl,sl];error=envelope[sl,sl]
            eig,vec=np.linalg.eigh(new);oe=np.linalg.eigvalsh(old)
            ranks={str(t):int(np.sum(eig>t*eig[-1])) for t in (1e-12,1e-10,1e-8)}
            oldr={str(t):int(np.sum(oe>t*oe[-1])) for t in (1e-12,1e-10,1e-8)}
            support=eig>1e-10*eig[-1]
            if len(set(ranks.values()))!=1 or ranks!=oldr or not np.any(support):
                passed=False;findings.append({'matrix':label,'radius':r,
                    'status':'NUMERICAL_SUPPORT_UNCERTAIN','ranks':ranks,'earlier_ranks':oldr});continue
            H=(vec[:,support]/np.sqrt(eig[support]))@vec[:,support].T
            entry=float(np.max(norm[sl,sl]))
            fro=float((np.linalg.norm(delta)+np.linalg.norm(error))/np.linalg.norm(new))
            white=float(np.linalg.norm(H@delta@H,2)+
                        np.linalg.norm(abs(H)@error@abs(H),2))
            ok=entry<=.005 and fro<=.003 and white<=.02
            passed &=ok
            findings.append({'matrix':label,'radius':r,'max_normalized_entry_including_sensitivity':entry,
                'relative_frobenius_including_sensitivity':fro,
                'whitened_spectral_including_sensitivity':white,'ranks':ranks,'pass':bool(ok)})
        for r in range(3):
            for t in range(r+1,3):
                entry=float(np.max(norm[5*r:5*r+5,5*t:5*t+5]))
                ok=entry<=.005;passed &=ok
                findings.append({'matrix':label,'cross_radii':[r,t],
                                 'max_normalized_entry_including_sensitivity':entry,'pass':bool(ok)})
    return bool(passed),findings


def fixture(packet,deadline,output):
    """Changed route on original smooth signed/duplicate-position fixture."""
    x=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,1,0],
                [0,0,0],[1,0,1],[0,1,1]],float)
    n=np.array([[1,1,1],[1,0,1],[0,1,1],[1,1,0],[-1,1,1],
                [1,1,1],[1,-1,1],[1,1,-1]],float)
    n/=np.linalg.norm(n,axis=1)[:,None]
    jg=np.array([-.7,-.8,-.9,-.65,-1.1,-.75,-.95,-.85])
    nonref=np.arange(1,8);refs=np.zeros(7,dtype=int)
    L=np.array([[1,-2,0,.5,0,0,1],[-.5,0,1,0,2,0,-1],
                [0,1,-1,0,0,2,.5],[1,0,0,-1,1,-1,0],
                [0,.5,.4,.2,-.7,1,-.2]],float)
    target,maps=fast.inventory([('fixture',53,32)])
    coeff,unique,expansion,_,q=fast.coefficient_fields(L,nonref,refs,jg[:,None]*n,7)
    scales,xs=fast.power_two_scales(x[nonref]);ts,forecast=fast.conservative_grid_admission(xs,target,scales)
    def progress(eps,w,timing):
        atomic_npz(output/f'FIXTURE_EPS_{eps:.0e}.npz',targets=target,window=w)
    (lo,hi),timing,_=fast.run_pair(xs,ts,coeff,target,x,jg[:,None]*n,unique,expansion,
                                  deadline,progress)
    joints,_,_=fast.stage_from_windows(maps['fixture'],hi,np.zeros_like(hi.real),AMP)
    pair=np.zeros((15,15))
    K=np.zeros((5,8))
    for p,i in enumerate(nonref):K[:,i]+=L[:,p];K[:,refs[p]]-=L[:,p]
    for r in range(3):
        for t in range(3):
            for a in range(5):
                for b in range(5):
                    def integrand(k):
                        smooth=math.exp(-.5*(k*s.RADII[r]/s.H)**2-.5*(k*s.RADII[t]/s.H)**2)
                        mat=(jg[:,None]*jg[None,:])*s.pair_kernel(k,x,n)
                        return float(s.power(k,AMP))*smooth*(K@mat@K.T)[a,b]/(2*math.pi**2)
                    pair[5*r+a,5*t+b]=quad(integrand,*s.BANDS[0],epsrel=1e-10,epsabs=1e-12)[0]
    scale=np.sqrt(np.diag(pair));demand(np.all(scale>0),'FIXTURE_ZERO_VARIANCE')
    delta=joints[0]-pair
    fro=float(np.linalg.norm(delta)/np.linalg.norm(pair))
    entry=float(np.max(abs(delta)/np.outer(scale,scale)))
    demand(fro<=1e-5 and entry<=1e-6 and abs(pair[0,1])>0,
           f'FIXTURE_BESSEL_HOLD {fro} {entry}')
    k=maps['fixture'][0]['k'][8];u=maps['fixture'][0]['directions'][:4]
    for direction in u:
        key=(float(k).hex(),*(float(v).hex() for v in direction))
        index=next(i for i,(kk,*vv) in enumerate(target)
                   if (float(kk).hex(),*(float(v).hex() for v in vv))==key)
        direct,_=direct_oracle(k,direction,x,n,jg,L,nonref,refs)
        demand(np.linalg.norm(hi[index]-direct)<=1e-8*max(np.linalg.norm(direct),1e-30),
               'FIXTURE_PHASE_SIGN_SCALING_HOLD')
    def small_eval(xx,nn,jjg,ll,nr,rr,directions):
        targets=np.column_stack((np.full(len(directions),k),directions))
        cc,un,ex,_,_=fast.coefficient_fields(ll,nr,rr,jjg[:,None]*nn,7)
        ss,xsmall=fast.power_two_scales(xx[nr]);tt,_=fast.conservative_grid_admission(xsmall,targets,ss)
        (small_lo,small_hi),_,_=fast.run_pair(xsmall,tt,cc,targets,xx,jjg[:,None]*nn,
                                              un,ex,deadline,lambda *_:None)
        return small_lo,small_hi
    _,baseline=small_eval(x,n,jg,L,nonref,refs,u)
    _,antipodal=small_eval(x,n,jg,L,nonref,refs,-u)
    # Real coefficients and the outer u factor imply w(k,-u)=-conj(w(k,u)).
    # Serialize both conventions before the unchanged threshold assertion.
    finite=bool(np.all(np.isfinite(antipodal)) and np.all(np.isfinite(baseline)))
    if not finite:
        atomic_json(output/'ANTIPODAL_CONTROL.json',{'status':'NONFINITE_HOLD',
            'corrected_residual':'NOT_FINITE','old_sign_residual':'NOT_FINITE',
            'eps':fast.EPS[1],'mapping':'k,u to k,-u','expected':'minus_conjugate'})
        raise Hold('FIXTURE_ANTIPODAL_NONFINITE_HOLD')
    antipodal_corrected_max=float(np.max(abs(antipodal+baseline.conj())))
    antipodal_old_sign_max=float(np.max(abs(antipodal-baseline.conj())))
    antipodal_scale=float(max(np.max(abs(baseline)),1e-30))
    antipodal_threshold=1e-9*antipodal_scale
    atomic_json(output/'ANTIPODAL_CONTROL.json',{'status':'MEASURED_BEFORE_ASSERTION',
        'corrected_minus_conjugate_max_abs':antipodal_corrected_max,
        'old_plus_conjugate_debug_max_abs':antipodal_old_sign_max,
        'baseline_scale_with_original_floor':antipodal_scale,
        'relative_threshold':1e-9,'floor':1e-30,
        'absolute_threshold':antipodal_threshold,'eps':fast.EPS[1],
        'mapping':'k,u to k,-u','expected':'minus_conjugate'})
    demand(antipodal_corrected_max<=antipodal_threshold,
           'FIXTURE_ANTIPODAL_HOLD')
    perm=np.array([3,5,1,7,2,0,6,4]);inv=np.argsort(perm)
    _,permuted=small_eval(x[perm],n[perm],jg[perm],L,inv[nonref],inv[refs],u)
    demand(np.max(abs(permuted-baseline))<=1e-9*max(np.max(abs(baseline)),1e-30),
           'FIXTURE_PERMUTATION_HOLD')
    rot=np.array([[0,-1,0],[1,0,0],[0,0,1]],float)
    _,rotated=small_eval(x@rot.T,n@rot.T,jg,L,nonref,refs,u@rot.T)
    demand(np.max(abs(rotated-baseline))<=1e-9*max(np.max(abs(baseline)),1e-30),
           'FIXTURE_ROTATION_HOLD')
    _,scaled=small_eval(x,n,2*jg,L,nonref,refs,u)
    demand(np.max(abs(scaled-2*baseline))<=1e-9*max(np.max(abs(baseline)),1e-30),
           'FIXTURE_SCALING_HOLD')
    pts,wt,paired,pwt=s.angular_rule(53)
    _,full=small_eval(x,n,jg,L,nonref,refs,pts)
    _,paired_windows=small_eval(x,n,jg,L,nonref,refs,paired)
    paired_gram=np.einsum('t,ta,tb->ab',pwt/(4*math.pi),
                          paired_windows,paired_windows.conj()).real
    full_gram=np.einsum('t,ta,tb->ab',wt/(4*math.pi),full,full.conj()).real
    demand(np.max(abs(paired_gram-full_gram))<=1e-9*max(np.max(abs(full_gram)),1e-30),
           'FIXTURE_PAIRED_UNPAIRED_HOLD')
    sym,diag=s.matrix_diagnostics(joints[0]+joints[1])
    demand(time.monotonic()<deadline,'BUDGET_CONVERGENCE_HOLD fixture')
    return {'bessel_relative_frobenius':fro,'bessel_max_normalized_entry':entry,
            'joint_diagnostics':diag,'transform_timing':timing,'grid_forecast':forecast,
            'paired_unpaired_max_abs':float(np.max(abs(paired_gram-full_gram))),
            'permutation_max_abs':float(np.max(abs(permuted-baseline))),
            'rotation_max_abs':float(np.max(abs(rotated-baseline))),
            'antipodal_max_abs':antipodal_corrected_max,
            'antipodal_old_sign_debug_max_abs':antipodal_old_sign_max,
            'scaling_max_abs':float(np.max(abs(scaled-2*baseline)))}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--input',required=True)
    args=parser.parse_args()
    packet=json.loads(Path(args.input).read_text())
    output=Path(packet['output_dir']);output.mkdir(parents=True,exist_ok=True)
    deadline=float(os.environ['R32_CHILD_DEADLINE_MONOTONIC'])
    status={'status':'STARTED','scientific_admission':False,'original_H02_H04':'HOLD',
            'global_rigorous_type3_error_enclosure':'NOT_ESTABLISHED',
            'component':'conditional fixed-band five-coordinate apparent STF error only'}
    try:
        demand(packet.get('controller_go') is True,'MISSING_CONTROLLER_GO')
        bindings=json.loads(Path(packet['input_bindings']).read_text())
        demand(digest(packet['input_bindings'])==packet['input_bindings_sha256'],
               'INPUT_BINDINGS_SHA')
        data=source_data(bindings);prior,saved=prior_controls(packet)
        c,g,j,*_=s.background(data['z'],64)
        n=data['n'];positions=c[:,None]*n;jg=j*g;b=jg[:,None]*n
        f=data['factor'];L=f['L_binary64'];nonref=f['nonreference_row_index']
        refs=f['difference_reference_row_index']
        # Exact indexing/cancellation on the saved Ddiff, including zero rows.
        demand(np.array_equal(data['ids'][nonref],f['group_id'][nonref]) and
               np.all(np.isfinite(positions)),'POSITION_OR_DDIFF_INDEX')
        support=f['selected_support_7']
        channel_i=np.argmax(support[nonref],axis=1)
        channel_r=np.argmax(support[refs],axis=1)
        offsets=np.arange(7.,dtype=float)
        demand(np.all(np.sum(support[nonref],axis=1)==1) and
               np.all(np.sum(support[refs],axis=1)==1) and
               np.array_equal(channel_i,channel_r) and
               np.array_equal(channel_i,f['nonreference_channel']) and
               np.array_equal(refs,f['reference_row_by_channel'][channel_i]) and
               np.array_equal(offsets[channel_i]-offsets[channel_r],np.zeros(len(nonref))),
               'SEVEN_CHANNEL_ADDITIVE_ZERO_CANCELLATION')
        coeff,unique,expansions,exp_evidence,q=fast.coefficient_fields(L,nonref,refs,b)
        atomic_json(output/'EXACT_REFERENCE_SUMS.json',{'sums':exp_evidence,
                    'all_five_by_three_fields':True,'nonreference_columns':len(nonref)})
        stages=[('A',35,16),('B',53,16),('C',53,32)]
        target,maps=fast.inventory(stages)
        scales,xscaled=fast.power_two_scales(positions[nonref])
        tcols,forecast=fast.conservative_grid_admission(xscaled,target,scales)
        atomic_json(output/'TARGET_INVENTORY.json',{'target_count':len(target),
                    'stages':[(a,b,c) for a,b,c in stages], 'power_two_scale':scales.tolist(),
                    'forecast':forecast,'eps_requests':list(fast.EPS)})
        atomic_npz(output/'TARGETS.npz',targets=target,
                   **{f'{name}_band{bi}_indices':v['target_indices']
                      for name,group in maps.items() for bi,v in enumerate(group)})
        def progress(eps,w,timing):
            atomic_npz(output/f'WINDOWS_EPS_{eps:.0e}.npz',targets=target,window=w)
            atomic_json(output/'PROGRESS.json',{'completed_eps':eps,'timing':timing,
                'utc_unix':time.time(),'target_count':len(target),'all_five':True})
            if eps==fast.EPS[0]:
                remaining=deadline-time.monotonic()
                projected=2.5*timing['seconds']+12
                demand(projected<=remaining,
                       f'BUDGET_CONVERGENCE_HOLD high_eps_forecast={projected} remaining={remaining}')
        (low,high),transform_timing,reference=fast.run_pair(
            xscaled,tcols,coeff,target,positions,b,unique,expansions,deadline,progress)
        roundoff,roundmeta=fast.roundoff_envelope(target,positions,coeff,q,b,unique,
                                                   expansions,reference,high)
        sensitivity=10*abs(high-low)+roundoff
        atomic_npz(output/'SENSITIVITY.npz',targets=target,roundoff=roundoff,
                   sensitivity=sensitivity,low=low,high=high)
        stage_results={}
        for name,order,radial in stages:
            joints,bounds,spectra=fast.stage_from_windows(maps[name],high,sensitivity,AMP)
            atomic_npz(output/f'STAGE_{name}.npz',band1=joints[0],band2=joints[1],
                       total=joints[0]+joints[1],bound1=bounds[0],bound2=bounds[1],
                       A1=spectra[0][0],A2=spectra[1][0],
                       BA1=spectra[0][1],BA2=spectra[1][1],
                       k1=maps[name][0]['k'],k2=maps[name][1]['k'],
                       w1=maps[name][0]['radial_weights'],w2=maps[name][1]['radial_weights'])
            diagnostics=support_and_bounds(joints,bounds)
            stage_results[name]=(joints,bounds,spectra,diagnostics)
            atomic_json(output/f'STAGE_{name}.json',{'order':order,'radial_intervals':radial,
                         'diagnostics':diagnostics,'full_5x5_and_15x15':True})
        method_direct=direct_controls(target,maps,high,low,roundoff,saved,
                                       positions,n,jg,L,nonref,refs)
        atomic_json(output/'DIRECT_CONTROLS.json',method_direct)
        a,ae,*_=stage_results['A'];bb,be,*_=stage_results['B'];cc,ce,*_=stage_results['C']
        angular_ok,angular=bounded_convergence(a,bb,ae,be)
        radial_ok,radial=bounded_convergence(bb,cc,be,ce)
        status.update({'angular_A_B_pass':angular_ok,'radial_B_C_pass':radial_ok,
                       'angular_A_B':angular,'radial_B_C':radial})
        demand(radial_ok,'RADIAL_CONVERGENCE_HOLD')
        final=cc; final_bound=ce; final_name='C';optional=None
        if not angular_ok:
            remaining=deadline-time.monotonic()
            predicted=2.5*sum(v['seconds'] for v in transform_timing)+12
            demand(predicted<=remaining,
                   f'ANGULAR_CONVERGENCE_HOLD optional_D_forecast={predicted} remaining={remaining}')
            td,md=fast.inventory([('D',65,32)])
            sd,xd=fast.power_two_scales(positions[nonref]);tt,fd=fast.conservative_grid_admission(xd,td,sd)
            def dprogress(eps,w,timing):
                atomic_npz(output/f'D_WINDOWS_EPS_{eps:.0e}.npz',targets=td,window=w)
            (dl,dh),dt,dr=fast.run_pair(xd,tt,coeff,td,positions,b,unique,expansions,deadline,dprogress)
            de,_=fast.roundoff_envelope(td,positions,coeff,q,b,unique,expansions,dr,dh)
            dj,db,ds=fast.stage_from_windows(md['D'],dh,10*abs(dh-dl)+de,AMP)
            ddiag=support_and_bounds(dj,db)
            atomic_npz(output/'STAGE_D.npz',band1=dj[0],band2=dj[1],total=dj[0]+dj[1],
                       bound1=db[0],bound2=db[1],A1=ds[0][0],A2=ds[1][0],
                       BA1=ds[0][1],BA2=ds[1][1],k1=md['D'][0]['k'],k2=md['D'][1]['k'],
                       w1=md['D'][0]['radial_weights'],w2=md['D'][1]['radial_weights'])
            optional,findings=bounded_convergence(cc,dj,ce,db)
            status.update({'angular_C_D_pass':optional,'angular_C_D':findings,
                           'optional_D_transform_timing':dt,'optional_D_diagnostics':ddiag})
            demand(optional,'ANGULAR_CONVERGENCE_HOLD')
            final=dj;final_bound=db;final_name='D'
        fixture_result=fixture(packet,deadline,output)
        demand(time.monotonic()<deadline,'BUDGET_CONVERGENCE_HOLD closeout')
        basis=f['STF_basis_5x3x3']
        joints=(final[0],final[1],final[0]+final[1])
        blocks=np.stack([m.reshape(3,5,3,5).transpose(0,2,1,3) for m in joints])
        corr=np.stack([m/np.outer(np.sqrt(np.diag(m)),np.sqrt(np.diag(m))) for m in joints])
        tensor=np.stack([np.einsum('rtab,aij,bkl->rtijkl',v,basis,basis) for v in blocks])
        eig=[];vectors=[]
        for matrix in joints:
            values,vec=np.linalg.eigh(matrix)
            for col in range(15):
                pivot=np.argmax(abs(vec[:,col]))
                if vec[pivot,col]<0:vec[:,col]*=-1
            eig.append(values);vectors.append(vec)
        atomic_npz(output/'PRODUCT.npz',group_id=data['ids'],positions=positions,
                   n_J2000=n,j=j,g=g,STF_basis_5x3x3=basis,
                   mixed_zero_leverage_mask=f['mixed_zero_leverage_mask'],
                   exact_zero_leverage_mask=f['exact_zero_leverage_mask'],
                   additional_zero_leverage_mask=f['extra_zero_leverage_mask'],
                   b_fact=np.asarray(data['result']['display_b_fact']),
                   band_joint=np.stack(final),total_joint=joints[2],
                   band_sensitivity_bound=np.stack(final_bound),
                   covariance_blocks=blocks,coordinate_correlations=corr,
                   tensor_covariance=tensor,joint_eigenvalues=np.stack(eig),
                   joint_signed_eigenvectors=np.stack(vectors),
                   radii_hinv_mpc=s.RADII,bands_physical=np.asarray(s.BANDS),
                   angular_order=np.array(65 if final_name=='D' else 53),
                   joint_stage_A=np.stack(a),joint_stage_B=np.stack(bb),
                   joint_stage_C=np.stack(cc))
        status.update({'status':'CONDITIONAL_NUMERICAL_PASS_PENDING_INDEPENDENT_REVIEW',
                       'final_stage':final_name,'reused_controls_sha256':packet['reused_controls']['sha256'],
                       'amplitude':AMP,'direct_controls':method_direct,'fixture':fixture_result,
                       'roundoff':roundmeta,'transform_timing':transform_timing,
                       'full_tensor_images':{v:'UNDEFINED/HOLD' for v in ('x','F','Pi','Q','G_F')},
                       'claim_ceiling':'conditional finite band-PV component; no total law, physical tensor images, or original H02/H04 acceptance'})
    except Exception as exc:
        status.update({'status':'HOLD','first_failure':f'{type(exc).__name__}: {exc}'})
        raise
    finally:
        status['utc_unix']=time.time()
        atomic_json(output/'RESULT.json',status)


if __name__=='__main__':
    main()
