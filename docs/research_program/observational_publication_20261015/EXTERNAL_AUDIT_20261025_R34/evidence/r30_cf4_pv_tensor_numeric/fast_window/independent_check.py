"""Independent R32 reference checker for a fresh reviewer; inert at import.

No producer science modules are imported. This checks a saved candidate, not
re-running a full type-3 transform. The reviewer owns execution and verdict.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from scipy.integrate import quad
from scipy.special import spherical_jn

H=.6736; OM=.3153; OBHH=.02237; NS=.9649; TCMB=2.7255
RADII=np.array([5.,10.,20.]); BANDS=((.005*H,.02*H),(.02*H,.05*H))
AMP=765245.0820764016


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1<<20),b''):h.update(block)
    return h.hexdigest()


def require(ok,detail):
    if not bool(ok):raise ValueError(detail)


def transfer(k):
    k=np.asarray(k,float);omhh=OM*H**2;fb=OBHH/omhh;theta=TCMB/2.7
    ss=44.5*np.log(9.83/omhh)/np.sqrt(1+10*(omhh*fb)**.75)
    keq=.0746*omhh/theta**2
    alpha=1-.328*np.log(431*omhh)*fb+.38*np.log(22.3*omhh)*fb**2
    gamma=omhh*(alpha+(1-alpha)/(1+(.43*k*ss)**4))
    q=k/(13.41*keq)*omhh/gamma
    l0=np.log(2*2.718282+1.8*q);c0=14.2+731/(1+62.5*q)
    return l0/(l0+c0*q*q)


def power(k):return AMP*(np.asarray(k)/.05)**NS*transfer(k)**2


def exact_reference_check(factor,reference):
    L=factor['L_binary64'];rr=factor['difference_reference_row_index']
    labels=np.unique(rr);reported=reference['sums']
    require(len(reported)==5,'exact_reference_row_count')
    for a in range(5):
        for h,row in enumerate(labels):
            total=sum((Fraction.from_float(float(v)) for v in L[a,rr==row]),Fraction())
            item=reported[a][h]
            require(item['row']==int(row) and
                    total==Fraction(int(item['numerator_at_2_minus_1074']),1<<1074),
                    'exact_reference_dyadic_mismatch')
            terms=[Fraction.from_float(float.fromhex(v)) for v in item['expansion_hex']]
            require(sum(terms,Fraction())==total,'exact_reference_expansion_mismatch')
    return {'rows':labels.tolist(),'exact_5_by_reference':True}


def direct(k,u,x,n,jg,L,nonref,refs):
    xx=np.asarray(x,np.longdouble);uu=np.asarray(u,np.longdouble)
    aa=np.asarray(jg,np.longdouble)*(np.asarray(n,np.longdouble)@uu)
    pr=np.longdouble(k)*(xx[refs]@uu)
    dp=np.longdouble(k)*((xx[nonref]-xx[refs])@uu)
    signal=np.exp(np.clongdouble(1j)*pr)*(
        (aa[nonref]-aa[refs])+aa[nonref]*np.expm1(np.clongdouble(1j)*dp))
    ll=np.asarray(L,np.longdouble)
    return np.asarray(ll@signal.real,float)+1j*np.asarray(ll@signal.imag,float)


def pair_kernel(k,x,n):
    sep=x[:,None,:]-x[None,:,:];radius=np.linalg.norm(sep,axis=2)
    mu=n@n.T;z=k*radius;j2=spherical_jn(2,z)
    shat=np.divide(sep,radius[:,:,None],out=np.zeros_like(sep),where=radius[:,:,None]>0)
    ni=np.einsum('ic,ijc->ij',n,shat);nj=np.einsum('jc,ijc->ij',n,shat)
    return (spherical_jn(0,z)+j2)*mu/3-j2*ni*nj


def fixture_bessel(run):
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
    for p,i in enumerate(range(1,8)):K[:,i]+=L[:,p];K[:,0]-=L[:,p]
    pair=np.zeros((15,15))
    for r in range(3):
        for t in range(3):
            for a in range(5):
                for b in range(5):
                    def integrand(k):
                        smooth=math.exp(-.5*(k*RADII[r]/H)**2-.5*(k*RADII[t]/H)**2)
                        matrix=(jg[:,None]*jg[None,:])*pair_kernel(k,x,n)
                        return float(power(k))*smooth*(K@matrix@K.T)[a,b]/(2*math.pi**2)
                    pair[5*r+a,5*t+b]=quad(integrand,*BANDS[0],epsrel=1e-10,epsabs=1e-12)[0]
    z=np.load(run/'FIXTURE_EPS_1e-12.npz',allow_pickle=False)
    # The full fixture angular joint is saved in producer RESULT; the checker
    # independently reconstructs its finite angular/radial sum from windows.
    target=z['targets'];windows=z['window']
    from scipy.integrate import lebedev_rule
    pts,weights=lebedev_rule(53);pts=np.asarray(pts).T
    from scipy.spatial import cKDTree
    mates=cKDTree(pts).query(-pts)[1]
    chosen=np.where(np.arange(len(pts))<mates)[0]
    directions=pts[chosen];aw=2*np.asarray(weights)[chosen]/(4*math.pi)
    index={(float(k).hex(),*(float(v).hex() for v in u)):i
           for i,(k,*u) in enumerate(target)}
    def cc32(lo,hi):
        n=32;j=np.arange(n+1);theta=np.pi*j/n
        w=np.empty(n+1);w[0]=w[-1]=1/(n*n-1)
        interior=np.arange(1,n);v=np.ones(n-1)
        for m in range(1,n//2):v-=2*np.cos(2*m*theta[interior])/(4*m*m-1)
        v-=np.cos(n*theta[interior])/(n*n-1)
        w[interior]=2*v/n
        return (lo+hi)/2+(hi-lo)/2*np.cos(theta),w*(hi-lo)/2
    k,wk=cc32(*BANDS[0]);joint=np.zeros((15,15))
    for kval,rw in zip(k,wk):
        ids=[index[(float(kval).hex(),*(float(v).hex() for v in u))] for u in directions]
        v=windows[ids];A=np.einsum('t,ta,tb->ab',aw,v,v.conj()).real
        smooth=np.exp(-.5*(kval*RADII/H)**2)
        joint+=rw*float(power(kval))/(2*math.pi**2)*np.kron(np.outer(smooth,smooth),A)
    scale=np.sqrt(np.diag(pair));require(np.all(scale>0),'fixture_nonpositive_scale')
    fro=float(np.linalg.norm(joint-pair)/np.linalg.norm(pair))
    entry=float(np.max(abs(joint-pair)/np.outer(scale,scale)))
    require(fro<=1e-5 and entry<=1e-6,'fixture_Bessel_disagreement')
    return {'relative_frobenius':fro,'maximum_normalized_entry':entry}


def reconstruct(stage):
    with np.load(stage,allow_pickle=False) as z:
        out=[]
        for b in (1,2):
            A=z[f'A{b}'];k=z[f'k{b}'];weights=z[f'w{b}']
            m=np.zeros((15,15))
            for matrix,kk,w in zip(A,k,weights):
                smooth=np.exp(-.5*(kk*RADII/H)**2)
                m+=w*float(power(kk))/(2*math.pi**2)*np.kron(np.outer(smooth,smooth),matrix)
            require(np.allclose(m,z[f'band{b}'],rtol=1e-12,atol=1e-12),
                    'spectral_to_joint_disagreement')
            out.append(m)
        require(np.allclose(out[0]+out[1],z['total'],rtol=1e-12,atol=1e-12),
                'joint_sum_disagreement')
        return out


def numerical_gates(run,result):
    with np.load(run/'SENSITIVITY.npz',allow_pickle=False) as z:
        hi=z['high'];lo=z['low'];roundoff=z['roundoff'];sens=z['sensitivity']
        require(hi.shape==lo.shape==roundoff.shape==sens.shape and hi.shape[1]==5,
                'full_window_shape')
        require(np.all(np.isfinite(hi)) and np.all(np.isfinite(lo)) and
                np.all(np.isfinite(sens)) and np.all(sens>=10*abs(hi-lo)),
                'window_sensitivity_identity')
    stages={}
    names=('A','B','C')+ (('D',) if result['final_stage']=='D' else ())
    for name in names:
        with np.load(run/f'STAGE_{name}.npz',allow_pickle=False) as z:
            joints=[z['band1'],z['band2']]
            bounds=[z['bound1'],z['bound2']]
            stages[name]=(joints,bounds)
            for matrix,bound in zip(joints,bounds):
                require(matrix.shape==bound.shape==(15,15),'full_joint_shape')
                require(np.max(abs(matrix-matrix.T))<=1e-12*np.trace(matrix),
                        'pre_symmetry_gate')
                require(np.linalg.eigvalsh((matrix+matrix.T)/2)[0]>=-1e-12*np.trace(matrix),
                        'joint_PSD_gate')
            for matrix,bound in zip((joints[0],joints[1],joints[0]+joints[1]),
                                    (bounds[0],bounds[1],bounds[0]+bounds[1])):
                sd=np.sqrt(np.diag(matrix));require(np.all(sd>0),'positive_diagonal_gate')
                require(np.max(bound/np.outer(sd,sd))<=5e-5,'joint_sensitivity_gate')
                for r in range(3):
                    sl=slice(5*r,5*r+5);sub=matrix[sl,sl];bb=bound[sl,sl]
                    eig,vec=np.linalg.eigh(sub);support=eig>1e-10*eig[-1]
                    require(np.any(support),'support_empty_gate')
                    root=(vec[:,support]/np.sqrt(eig[support]))@vec[:,support].T
                    require(np.linalg.norm(bb)/np.linalg.norm(sub)<=3e-5 and
                            np.linalg.norm(abs(root)@bb@abs(root),2)<=2e-4,
                            'diagonal_sensitivity_gate')
    pairs=(('A','B'),('B','C'))+ ((('C','D'),) if result['final_stage']=='D' else ())
    for early,late in pairs:
        enforced=(early!='A' or result['angular_A_B_pass'] is True)
        (old,eo),(new,en)=stages[early],stages[late]
        allold=(old[0],old[1],old[0]+old[1]);allnew=(new[0],new[1],new[0]+new[1])
        alleo=(eo[0],eo[1],eo[0]+eo[1]);allen=(en[0],en[1],en[0]+en[1])
        for A,B,EA,EB in zip(allold,allnew,alleo,allen):
            D=B-A;E=EA+EB;sd=np.sqrt(np.diag(B))
            if not enforced:
                continue
            require(not enforced or np.max((abs(D)+E)/np.outer(sd,sd))<=.005,
                    'joint_convergence_gate')
            for r in range(3):
                sl=slice(5*r,5*r+5);old5=A[sl,sl];new5=B[sl,sl]
                eig,vec=np.linalg.eigh(new5);oe=np.linalg.eigvalsh(old5)
                ranks=[int(np.sum(eig>t*eig[-1])) for t in (1e-12,1e-10,1e-8)]
                oldr=[int(np.sum(oe>t*oe[-1])) for t in (1e-12,1e-10,1e-8)]
                require(not enforced or (len(set(ranks))==1 and ranks==oldr),
                        'numerical_support_gate')
                support=eig>1e-10*eig[-1]
                root=(vec[:,support]/np.sqrt(eig[support]))@vec[:,support].T
                require(not enforced or (np.linalg.norm(D[sl,sl])+np.linalg.norm(E[sl,sl]))/
                        np.linalg.norm(new5)<=.003,'frobenius_convergence_gate')
                require(not enforced or np.linalg.norm(root@D[sl,sl]@root,2)+
                        np.linalg.norm(abs(root)@E[sl,sl]@abs(root),2)<=.02,
                        'whitened_convergence_gate')
    require(result['radial_B_C_pass'] is True and
            (result['angular_A_B_pass'] is True or
             (result['final_stage']=='D' and result['angular_C_D_pass'] is True)),
            'reported_mandatory_convergence')
    return {'mandatory_A_B_C_full_15x15_gates':True,'targets':len(hi)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True)
    args=p.parse_args();packet=json.loads(Path(args.input).read_text())
    run=Path(packet['output_dir']);begin=time.monotonic()
    result=json.loads((run/'RESULT.json').read_text())
    require(result['status']=='CONDITIONAL_NUMERICAL_PASS_PENDING_INDEPENDENT_REVIEW',
            'producer_not_candidate')
    bindings=json.loads(Path(packet['input_bindings']).read_text())
    factor_path=bindings['immutable_numeric_inputs']['corrected_factor']['path']
    require(sha(factor_path)==bindings['immutable_numeric_inputs']['corrected_factor']['sha256'],
            'factor_sha_mismatch')
    with np.load(factor_path,allow_pickle=False) as z:factor={key:z[key] for key in z.files}
    exact=exact_reference_check(factor,json.loads((run/'EXACT_REFERENCE_SUMS.json').read_text()))
    with np.load(run/'PRODUCT.npz',allow_pickle=False) as z:
        x=z['positions'];n=z['n_J2000'];jg=z['j']*z['g']
        require(z['band_joint'].shape==(2,15,15) and
                z['covariance_blocks'].shape==(3,3,3,5,5) and
                z['tensor_covariance'].shape==(3,3,3,3,3,3),
                'product_full_tensor_shape')
    records=json.loads((run/'DIRECT_CONTROLS.json').read_text())['oracle_targets']
    selected=records[:min(4,len(records))]
    for item in selected:
        k=float.fromhex(item['k_hex']);u=np.array([float.fromhex(v) for v in item['u_hex']])
        expected=np.array(item['oracle_real'])+1j*np.array(item['oracle_imag'])
        found=direct(k,u,x,n,jg,factor['L_binary64'],
                     factor['nonreference_row_index'],factor['difference_reference_row_index'])
        require(np.linalg.norm(found-expected)<=1e-10*max(np.linalg.norm(expected),1e-30),
                'direct_oracle_disagreement')
    stage=result['final_stage'];joints=reconstruct(run/f'STAGE_{stage}.npz')
    with np.load(run/'PRODUCT.npz',allow_pickle=False) as z:
        require(np.allclose(np.stack(joints),z['band_joint'],rtol=1e-12,atol=1e-12),
                'product_joint_disagreement')
    fixture=fixture_bessel(run)
    gates=numerical_gates(run,result)
    require(time.monotonic()-begin<=60,'checker_wall_cap')
    print(json.dumps({'status':'INDEPENDENT_NUMERICAL_CHECK_PASS',
        'exact_reference':exact,'direct_subset_count':len(selected),
        'fixture':fixture,'full_spectral_to_joint':True,'gates':gates,
        'elapsed_seconds':time.monotonic()-begin,
        'claim_ceiling':'conditional finite band-PV component; no H02/H04 admission'},
        allow_nan=False,sort_keys=True))


if __name__=='__main__':main()
