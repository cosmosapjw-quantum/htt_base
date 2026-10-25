"""Read-only R30 numeric checker; does not import producer science functions.

The fresh reviewer runs this once within its separate 60-second allocation.
It reconstructs saved spectral integrals and a few actual Fourier windows,
not the full catalogue angular calculation.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import signal
import time

import numpy as np
from scipy.integrate import quad
from scipy.special import spherical_jn

H=.6736
OM=.3153
OBHH=.02237
TCMB=2.7255
NS=.9649
RADII=np.array([5.,10.,20.])


def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):
            h.update(b)
    return h.hexdigest()


def transfer(k):
    omhh=OM*H*H
    fb=OBHH/omhh
    s=44.5*math.log(9.83/omhh)/math.sqrt(1+10*(omhh*fb)**.75)
    keq=.0746*omhh/(TCMB/2.7)**2
    alpha=1-.328*math.log(431*omhh)*fb+.38*math.log(22.3*omhh)*fb*fb
    gamma=omhh*(alpha+(1-alpha)/(1+(.43*k*s)**4))
    q=(k/(13.41*keq))*omhh/gamma
    l=math.log(2*2.718282+1.8*q)
    c=14.2+731/(1+62.5*q)
    return l/(l+c*q*q)


def power(k,amplitude):
    return amplitude*(k/.05)**NS*transfer(k)**2


def check(cond,label):
    if not cond:
        raise AssertionError(label)


def signed_exact_center(factor,result):
    L=factor['L_binary64']; y=factor['y_binary64']
    ii=factor['nonreference_row_index'];rr=factor['difference_reference_row_index']
    accum=[Fraction(0) for _ in range(5)]
    for p,(i,r) in enumerate(zip(ii,rr)):
        contrast=Fraction.from_float(float(y[i]))-Fraction.from_float(float(y[r]))
        if contrast:
            for a in range(5):
                value=float(L[a,p])
                if value:
                    accum[a] += Fraction.from_float(value)*contrast
    saved=[Fraction(int(v[0]),int(v[1])) for v in result['exact_b_fact']]
    check(accum == saved,'EXACT_CENTER_FACTOR_IDENTITY')
    check(np.allclose([float(v) for v in saved],result['display_b_fact'],rtol=0,atol=1e-16),
          'SIGNED_CENTER_DISPLAY')
    return [float(v) for v in accum]


def reconstruct(stage,amplitude):
    out=[]
    for bi in (1,2):
        aa=stage[f'A{bi}']; kk=stage[f'k{bi}']; ww=stage[f'w{bi}']
        total=np.zeros((15,15))
        for a,k,w in zip(aa,kk,ww):
            sr=np.exp(-.5*(k*RADII/H)**2)
            total+=w*power(float(k),amplitude)/(2*math.pi**2)*np.kron(np.outer(sr,sr),a)
        check(np.allclose(total,stage[f'band{bi}'],rtol=1e-11,atol=1e-17),
              f'SPECTRAL_RECONSTRUCTION_B{bi}')
        out.append(total)
    check(np.allclose(out[0]+out[1],stage['total'],rtol=1e-11,atol=1e-17),'SPECTRAL_TOTAL')
    return out


def compare_saved_stages(earlier,later):
    issues=[]
    for label in ('band1','band2','total'):
        old=earlier[label];new=later[label]
        check(np.all(np.diag(new)>0),f'CONVERGENCE_ZERO_DIAGONAL_{label}')
        scale=np.sqrt(np.diag(new))
        normalized=abs(new-old)/np.outer(scale,scale)
        if float(np.max(normalized)) > .005:issues.append((label,'entry',float(np.max(normalized))))
        for r in range(3):
            sl=slice(5*r,5*r+5)
            d=new[sl,sl]-old[sl,sl]
            relative=float(np.linalg.norm(d)/np.linalg.norm(new[sl,sl]))
            if relative > .003:issues.append((label,r,'frobenius',relative))
            eig,vec=np.linalg.eigh(new[sl,sl])
            old_eig=np.linalg.eigvalsh(old[sl,sl])
            ranks_new=[int(np.sum(eig>tol*eig[-1])) for tol in (1e-12,1e-10,1e-8)]
            ranks_old=[int(np.sum(old_eig>tol*old_eig[-1])) for tol in (1e-12,1e-10,1e-8)]
            if len(set(ranks_new)) != 1 or ranks_new != ranks_old:
                issues.append((label,r,'support',ranks_old,ranks_new));continue
            selected=eig>1e-10*eig[-1]
            root=(vec[:,selected]/np.sqrt(eig[selected]))@vec[:,selected].T
            whitened=float(np.linalg.norm(root@d@root,2))
            if whitened > .02:issues.append((label,r,'whitened',whitened))
    return issues


def partial_actual_windows(spectral_paths,factor,product):
    L=factor['L_binary64']; ii=factor['nonreference_row_index'];rr=factor['difference_reference_row_index']
    positions=product['positions'];n=product['n_J2000']; jg=product['j']*product['g']
    findings=[]
    for path in spectral_paths:
        with np.load(path,allow_pickle=False) as z:
            k=float(z['k']);directions=z['sample_u'];saved=z['sample_w']
        actual=np.empty_like(saved)
        for column,u in enumerate(directions):
            phase=np.einsum('ic,c->i',positions,u)
            velocity=np.einsum('ic,c->i',n,u)
            row=jg*velocity*(np.cos(k*phase)+1j*np.sin(k*phase))
            # A distinct scalar-direction contraction of the saved L D_diff.
            actual[:,column]=np.einsum('ap,p->a',L,row[ii]-row[rr])
        scale=max(1.,float(np.max(abs(saved))))
        deviation=float(np.max(abs(actual-saved)))
        check(deviation <= 2e-10*scale,f'ACTUAL_WINDOW_{path.name}')
        findings.append({'path':str(path),'maximum_absolute_difference':deviation})
    return findings


def pair_fixture(amplitude):
    # Fresh small-pair kernel, no producer function import or full-N^2 allocation.
    x=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,1,0],
                [0,0,0],[1,0,1],[0,1,1]],float)
    n=np.array([[1,1,1],[1,0,1],[0,1,1],[1,1,0],[-1,1,1],
                [1,1,1],[1,-1,1],[1,1,-1]],float)
    n/=np.linalg.norm(n,axis=1)[:,None]
    jg=np.array([-.7,-.8,-.9,-.65,-1.1,-.75,-.95,-.85])
    L=np.array([[1,-2,0,.5,0,0,1],[-.5,0,1,0,2,0,-1],
                [0,1,-1,0,0,2,.5],[1,0,0,-1,1,-1,0],
                [0,.5,.4,.2,-.7,1,-.2]],float)
    K=np.zeros((5,8))
    for p in range(7):
        K[:,p+1]+=L[:,p];K[:,0]-=L[:,p]
    delta=x[:,None,:]-x[None,:,:]
    length=np.linalg.norm(delta,axis=2)
    shat=np.divide(delta,length[:,:,None],out=np.zeros_like(delta),where=length[:,:,None]>0)
    dot=n@n.T
    ni=np.einsum('ic,ijc->ij',n,shat)
    nj=np.einsum('jc,ijc->ij',n,shat)
    left=K*jg[None]
    def kernel(k):
        j0=spherical_jn(0,k*length);j2=spherical_jn(2,k*length)
        return (j0+j2)*dot/3-j2*ni*nj
    entries=np.zeros((5,5))
    for a in range(5):
        for b in range(5):
            def integrand(k):
                smooth=math.exp(-(k*10/H)**2)
                return power(k,amplitude)*smooth*(left[a]@kernel(k)@left[b])/(2*math.pi**2)
            entries[a,b]=quad(integrand,.005*H,.02*H,epsrel=1e-10,epsabs=1e-12)[0]
    return entries


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True,help='controller packet used by numerical command')
    p.add_argument('--output',required=True,help='read-only numerical product directory')
    p.add_argument('--max-seconds',type=int,default=55)
    args=p.parse_args()
    if args.max_seconds > 55 or args.max_seconds <= 0:
        raise ValueError('review checker must reserve finalization inside 60 seconds')
    signal.signal(signal.SIGALRM,lambda *_: (_ for _ in ()).throw(TimeoutError('review checker time cap')))
    signal.alarm(args.max_seconds)
    began=time.monotonic()
    packet=json.load(open(args.input));bindings=json.load(open(packet['input_bindings']))
    review=bindings['read_only_evidence']['exact_factor_independent_review']
    for item in (bindings['contract'],*bindings['immutable_numeric_inputs'].values(),review):
        check(digest(item['path'])==item['sha256'],'IMMUTABLE_SHA_'+Path(item['path']).name)
    reviewed=json.load(open(review['path']))
    check(reviewed['status']=='SCOPED_PASS_EXACT_FACTOR_METADATA_AND_ACTUAL_RESULT_CLOSEOUT' and
          reviewed['candidate_identity']=='sha256:'+bindings['immutable_numeric_inputs']['corrected_result']['sha256'],
          'EXACT_FACTOR_CLOSEOUT')
    paths={k:v['path'] for k,v in bindings['immutable_numeric_inputs'].items()}
    with np.load(paths['corrected_factor'],allow_pickle=False) as z:
        factor={key:z[key] for key in z.files}
    with np.load(paths['selected_source'],allow_pickle=False) as z:
        ids=z['group_id']
    with open(paths['corrected_result']) as f: result=json.load(f)
    check(np.array_equal(ids,factor['group_id']),'GROUP_ID_PARITY')
    check(hashlib.sha256(np.asarray(ids,dtype='<i8').tobytes()).hexdigest()==
          'f54706b8ff5c50c25a5a74c4b153f7f9e719a28582db044e00e5930dd30e3c88','ID_SHA')
    check(int(np.sum(factor['mixed_zero_leverage_mask']))==944 and
          int(np.sum(factor['exact_zero_leverage_mask']))==945 and
          bool(factor['exact_zero_leverage_mask'][1484]),'CORRECTED_MASKS')
    center=signed_exact_center(factor,result)
    output=Path(args.output)
    controls=json.load(open(output/'CONTROLS.json'))
    for k,v in zip(controls['transfer_spots_k_mpc_inv'],controls['transfer_spots']):
        check(abs(transfer(float(k))-v) <= 1e-13,'TRANSFER_SPOT')
    amp=float(controls['amplitude'])
    result_numeric=json.load(open(output/'RESULT.json'))
    check(result_numeric['status']=='CONDITIONAL_NUMERICAL_PASS_PENDING_INDEPENDENT_REVIEW',
          'PRODUCER_STATUS')
    final=result_numeric['final_stage']
    with np.load(output/f'STAGE_{final}.npz',allow_pickle=False) as z:
        stage={k:z[k] for k in z.files}
    reconstructed=reconstruct(stage,amp)
    saved_stages={}
    for name in ('A','B','C')+(('D',) if final=='D' else ()):
        with np.load(output/f'STAGE_{name}.npz',allow_pickle=False) as z:
            saved_stages[name]={key:z[key] for key in ('band1','band2','total')}
    angular_ab=compare_saved_stages(saved_stages['A'],saved_stages['B'])
    radial_bc=compare_saved_stages(saved_stages['B'],saved_stages['C'])
    check(not radial_bc,'RADIAL_CONVERGENCE_RECHECK')
    if final=='D':
        angular_cd=compare_saved_stages(saved_stages['C'],saved_stages['D'])
        check(not angular_cd and angular_ab,'OPTIONAL_ANGULAR_CONVERGENCE_RECHECK')
    else:
        angular_cd=[]
        check(not angular_ab,'ANGULAR_CONVERGENCE_RECHECK')
    with np.load(output/'PRODUCT.npz',allow_pickle=False) as z:
        product={k:z[k] for k in z.files}
    check(np.allclose(np.stack(reconstructed),product['band_joint'],rtol=1e-11,atol=1e-17),
          'PRODUCT_JOINT')
    check(np.array_equal(ids,product['group_id']) and
          np.array_equal(product['mixed_zero_leverage_mask'],factor['mixed_zero_leverage_mask']) and
          np.array_equal(product['exact_zero_leverage_mask'],factor['exact_zero_leverage_mask']),
          'PRODUCT_COHORT_MASK')
    check(np.allclose(product['b_fact'],center,rtol=0,atol=1e-16),'PRODUCT_SIGNED_CENTER')
    sample_paths=[]
    for order,bi,node in ((35,0,0),(53,1,8),(53,0,16)):
        k,_w=(stage[f'k{bi+1}'],stage[f'w{bi+1}'])
        # Use an actual retained spectrum at the selected band/order.
        if order==35:
            with np.load(output/'STAGE_A.npz',allow_pickle=False) as zz:
                kk=float(zz['k1'][node])
        elif order==53 and node==8:
            with np.load(output/'STAGE_B.npz',allow_pickle=False) as zz:
                kk=float(zz['k2'][node])
        else:
            kk=float(k[node])
        sample_paths.append(output/'spectral'/f'o{order}_b{bi}_k{kk.hex()}.npz')
    windows=partial_actual_windows(sample_paths,factor,product)
    pair=pair_fixture(amp)
    stored=np.asarray(controls['fixture']['pair_band1_r10'])
    fro=float(np.linalg.norm(pair-stored)/np.linalg.norm(stored))
    check(fro <= 1e-8,'INDEPENDENT_SMALL_PAIR_KERNEL')
    check(time.monotonic()-began <= args.max_seconds,'CHECKER_TIME')
    print(json.dumps({'status':'INDEPENDENT_NUMERIC_CHECK_PASS_PENDING_REVIEWER_DECISION',
                      'elapsed_seconds':time.monotonic()-began,
                      'exact_center':center,'spectral_reconstruction':'PASS',
                      'angular_A_B_issues':angular_ab,'radial_B_C_issues':radial_bc,
                      'angular_C_D_issues':angular_cd,
                      'partial_actual_windows':windows,'pair_relative_frobenius':fro,
                      'scientific_admission':False,'original_H02_H04':'HOLD'},indent=2))


if __name__=='__main__':
    main()
