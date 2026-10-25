"""Independent, one-shot CF4 finite covariance check. No producer imports."""
import hashlib, json, math, time, traceback
from fractions import Fraction
from pathlib import Path
import numpy as np
from scipy.integrate import quad
from scipy.special import spherical_jn

OUT=Path(__file__).resolve().parent
RUN=Path('/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_numeric/fast_window_fixture_repair/actual_run')
BIND=Path('/mnt/extdrive/workdir/htt_open_data/r30_cf4_pv_tensor_framing/INPUT_BINDINGS.json')
H=.6736; OM=.3153; OB=.02237; NS=.9649; AMP=765245.0820764016
RAD=np.array([5.,10.,20.])/H
SCORES=[]
def sha(p):
    d=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1048576),b''):d.update(b)
    return d.hexdigest()
def check(ok,name,metrics=None):
    SCORES.append({'gate':name,'pass':bool(ok),'metrics':metrics})
    if not ok:raise ValueError(name)
def tf(k):
    om=OM*H*H; fb=OB/om; th=2.7255/2.7
    s=44.5*np.log(9.83/om)/np.sqrt(1+10*(om*fb)**.75)
    ke=.0746*om/th**2
    al=1-.328*np.log(431*om)*fb+.38*np.log(22.3*om)*fb*fb
    ge=om*(al+(1-al)/(1+(.43*k*s)**4))
    q=(k/(13.41*ke))*om/ge
    l=np.log(2*2.718282+1.8*q);c=14.2+731/(1+62.5*q)
    return l/(l+c*q*q)
def power(k):return AMP*(k/.05)**NS*tf(k)**2
def matrix_from_spectrum(z,b):
    k=z[f'k{b}'];w=z[f'w{b}'];A=z[f'A{b}']; BA=z[f'BA{b}']
    m=np.zeros((15,15));bound=np.zeros_like(m)
    for kk,ww,a,ba in zip(k,w,A,BA):
        s=np.exp(-.5*(kk*RAD)**2)
        weight=ww*power(kk)/(2*np.pi**2)
        tile=np.kron(np.outer(s,s),a)
        m+=weight*tile
        bound+=weight*np.kron(np.outer(s,s),ba)
    return m,bound
def direct(k,u,x,n,jg,L,ii,rr):
    # Difference before signed contraction; long-double phase differences.
    xx=x.astype(np.longdouble); nn=n.astype(np.longdouble)
    uu=u.astype(np.longdouble); jj=jg.astype(np.longdouble)
    amp=jj*(nn@uu); base=np.longdouble(k)*(xx[rr]@uu)
    delta=np.longdouble(k)*((xx[ii]-xx[rr])@uu)
    v=np.exp(np.clongdouble(1j)*base)*((amp[ii]-amp[rr])+amp[ii]*np.expm1(np.clongdouble(1j)*delta))
    LL=L.astype(np.longdouble)
    return (LL@v.real).astype(float)+1j*(LL@v.imag).astype(float)
def kernel(k,x,n):
    sep=x[:,None,:]-x[None,:,:];r=np.linalg.norm(sep,axis=2)
    j2=spherical_jn(2,k*r);j0=spherical_jn(0,k*r)
    sh=sep/np.where(r[:,:,None]>0,r[:,:,None],1)
    ni=np.einsum('id,ijd->ij',n,sh);nj=np.einsum('jd,ijd->ij',n,sh)
    return (j0+j2)*(n@n.T)/3-j2*ni*nj
def fixture():
    x=np.array([[0,0,0],[1,0,0],[0,1,0],[0,0,1],[1,1,0],[0,0,0],[1,0,1],[0,1,1]],float)
    n=np.array([[1,1,1],[1,0,1],[0,1,1],[1,1,0],[-1,1,1],[1,1,1],[1,-1,1],[1,1,-1]],float)
    n/=np.linalg.norm(n,axis=1)[:,None]
    jg=np.array([-.7,-.8,-.9,-.65,-1.1,-.75,-.95,-.85])
    L=np.array([[1,-2,0,.5,0,0,1],[-.5,0,1,0,2,0,-1],[0,1,-1,0,0,2,.5],[1,0,0,-1,1,-1,0],[0,.5,.4,.2,-.7,1,-.2]])
    K=np.zeros((5,8))
    for p,i in enumerate(range(1,8)):K[:,i]+=L[:,p];K[:,0]-=L[:,p]
    with np.load(RUN/'FIXTURE_EPS_1e-12.npz',allow_pickle=False) as z: target=z['targets'];v=z['window']
    # Independent CC32 and Lebedev angular reconstruction from saved windows.
    from scipy.integrate import lebedev_rule
    points,aw=lebedev_rule(53);points=points.T
    from scipy.spatial import cKDTree
    match=cKDTree(points).query(-points)[1];take=np.where(np.arange(len(points))<match)[0]
    lookup={(float(row[0]).hex(),*(float(t).hex() for t in row[1:])):i for i,row in enumerate(target)}
    j=np.arange(33);theta=j*np.pi/32;cw=np.empty(33);cw[[0,-1]]=1/(32**2-1)
    for q in range(1,32):cw[q]=2/32*(1-sum(2*np.cos(2*m*theta[q])/(4*m*m-1) for m in range(1,16))-np.cos(32*theta[q])/(32**2-1))
    lo=.005*H;hi=.02*H;ks=(lo+hi)/2+(hi-lo)*np.cos(theta)/2;cw*= (hi-lo)/2
    angular=np.zeros((15,15))
    for k,w in zip(ks,cw):
        ids=[lookup[(float(k).hex(),*(float(t).hex() for t in points[i]))] for i in take]
        vals=v[ids];A=np.einsum('t,ta,tb->ab',2*aw[take]/(4*np.pi),vals,vals.conj()).real
        s=np.exp(-.5*(k*RAD)**2)
        angular+=w*power(k)/(2*np.pi**2)*np.kron(np.outer(s,s),A)
    pair=np.zeros((15,15))
    for r in range(3):
      for t in range(3):
       for a in range(5):
        for b in range(5):
         def f(k):
          gram=K@((jg[:,None]*jg[None,:])*kernel(k,x,n))@K.T
          return power(k)*np.exp(-.5*k*k*(RAD[r]**2+RAD[t]**2))*gram[a,b]/(2*np.pi**2)
         pair[5*r+a,5*t+b]=quad(f,lo,hi,epsrel=1e-10,epsabs=1e-12)[0]
    sd=np.sqrt(np.diag(pair));check(np.all(sd>0),'fixture_positive_diagonal')
    fro=np.linalg.norm(pair-angular)/np.linalg.norm(pair);entry=np.max(abs(pair-angular)/np.outer(sd,sd))
    check(fro<=1e-5 and entry<=1e-6,'fixture_independent_Bessel',{'relative_fro':float(fro),'max_normalized_entry':float(entry),'duplicate_position':True})
def main():
    bindings=json.loads(BIND.read_text());input_file=Path(bindings['immutable_numeric_inputs']['corrected_factor']['path'])
    checks={str(BIND):'d5cfe88bf297ee7d7ab6ae5b6758c951cf2491b189de8c37e6756511232dc2c4',str(input_file):bindings['immutable_numeric_inputs']['corrected_factor']['sha256'],str(RUN/'RESULT.json'):'ae5d4a97c433c998e5777e6c4372ccb3dd3f800d29d5a52576fc183ea2fc5985',str(RUN/'PRODUCT.npz'):'cfec008002fea776611d6abb70448a8b5cbed0d774a49d3377a5cfcf828a857d'}
    for p,h in checks.items():check(sha(p)==h,'sealed_sha_'+Path(p).name)
    result=json.loads((RUN/'RESULT.json').read_text())
    check(result['status']=='CONDITIONAL_NUMERICAL_PASS_PENDING_INDEPENDENT_REVIEW','candidate_status')
    with np.load(input_file,allow_pickle=False) as z:f={k:z[k] for k in z.files}
    with np.load(RUN/'PRODUCT.npz',allow_pickle=False) as z:p={k:z[k] for k in z.files}
    ii=f['nonreference_row_index'];rr=f['difference_reference_row_index'];L=f['L_binary64']
    check(len(p['group_id'])==35970 and len(ii)==35019 and len(np.unique(rr))==6,'cohort_reference_shape',{'rows':len(p['group_id']),'columns':len(ii),'references':len(np.unique(rr))})
    for name in ('mixed_zero_leverage_mask','exact_zero_leverage_mask','additional_zero_leverage_mask'):
        key={'additional_zero_leverage_mask':'extra_zero_leverage_mask'}.get(name,name)
        check(np.array_equal(p[name],f[key]),'source_mask_'+name,{'count':int(np.sum(p[name]))})
    check(np.array_equal(p['group_id'],f['group_id']),'all_source_ids_order')
    support=f['selected_support_7'];ci=np.argmax(support[ii],axis=1);cr=np.argmax(support[rr],axis=1)
    check(np.all(ci==cr) and np.all(support[ii].sum(axis=1)==1) and np.all(support[rr].sum(axis=1)==1),'seven_channel_zero_offsets')
    exact=json.loads((RUN/'EXACT_REFERENCE_SUMS.json').read_text())['sums'];labels=np.unique(rr)
    for a in range(5):
      for h,row in enumerate(labels):
       total=sum((Fraction.from_float(float(q)) for q in L[a,rr==row]),Fraction())
       stored=exact[a][h]
       expansion=sum((Fraction.from_float(float.fromhex(s)) for s in stored['expansion_hex']),Fraction())
       check(stored['row']==int(row) and total==expansion==Fraction(int(stored['numerator_at_2_minus_1074']),1<<1074),'exact_dyadic_reference_'+str(a)+'_'+str(row))
    x=p['positions'];n=p['n_J2000'];jg=p['j']*p['g']
    with np.load(RUN/'SENSITIVITY.npz',allow_pickle=False) as z: low=z['low'];high=z['high'];sens=z['sensitivity'];roundoff=z['roundoff'];targets=z['targets']
    check(high.shape==(len(targets),5) and np.all(np.isfinite(high)) and np.all(np.isfinite(low)) and np.all(sens>=10*abs(high-low)),'all_target_sensitivity',{'targets':len(targets)})
    records=json.loads((RUN/'DIRECT_CONTROLS.json').read_text())['oracle_targets']
    errors_hi=[];errors_lo=[];worst_rel=0.;worst_component=0.;selected=[]
    for item in records:
        i=int(item['index']);u=np.asarray(targets[i,1:]);k=float(targets[i,0]);selected.append(i)
        check(float.fromhex(item['k_hex'])==k and np.array_equal([float.fromhex(q) for q in item['u_hex']],u),'direct_target_identity_'+str(i))
        oracle=direct(k,u,x,n,jg,L,ii,rr)
        e_hi=np.linalg.norm(high[i]-oracle);e_lo=np.linalg.norm(low[i]-oracle)
        errors_hi.append(e_hi*e_hi);errors_lo.append(e_lo*e_lo)
        worst_rel=max(worst_rel,float(e_hi/max(np.linalg.norm(oracle),1e-30)))
        coeffscale=np.asarray(item['coefficient_abs_scale'])
        worst_component=max(worst_component,float(np.max(abs(high[i]-oracle)/np.maximum(coeffscale,1e-30))))
    check(len(set(selected))==len(selected) and 0<len(selected)<=44,'direct_target_inventory',{'count':len(selected)})
    check(worst_rel<=1e-8 and worst_component<=1e-10,'independent_full_cohort_windows',{'max_relative_l2':worst_rel,'max_component_by_coefficient_l1':worst_component})
    ehi=math.sqrt(sum(errors_hi));elo=math.sqrt(sum(errors_lo));floor=float(np.linalg.norm(roundoff[selected]))
    check(ehi<=max(.1*elo,floor),'independent_eps_scaling',{'high_l2':ehi,'low_l2':elo,'roundoff_floor_l2':floor})
    fixture()
    stages={}
    for name in ('A','B','C'):
      with np.load(RUN/f'STAGE_{name}.npz',allow_pickle=False) as z:
       mats=[];bounds=[]
       for b in (1,2):
        m,bb=matrix_from_spectrum(z,b);stored=z[f'band{b}'];sb=z[f'bound{b}']
        check(np.max(abs(m-stored))<=1e-12*max(np.max(abs(stored)),1e-30),'spectral_joint_'+name+str(b),{'max_abs':float(np.max(abs(m-stored)))})
        check(np.max(abs(bb-sb))<=1e-12*max(np.max(abs(sb)),1e-30),'spectral_bound_'+name+str(b))
        mats.append(m);bounds.append(bb)
       check(np.max(abs(mats[0]+mats[1]-z['total']))<=1e-12*max(np.max(abs(z['total'])),1e-30),'band_sum_'+name)
       stages[name]=(mats,bounds)
    final=stages['C'][0]
    check(np.allclose(np.stack(final),p['band_joint'],rtol=1e-12,atol=0),'product_band_joint')
    check(np.allclose(sum(final),p['total_joint'],rtol=1e-12,atol=0),'product_total_joint')
    basis=p['STF_basis_5x3x3'];check(basis.shape==(5,3,3),'basis_shape')
    for b,m in enumerate([*final,sum(final)]):
      blocks=m.reshape(3,5,3,5).transpose(0,2,1,3)
      t=np.einsum('rtab,aij,bkl->rtijkl',blocks,basis,basis)
      check(np.allclose(blocks,p['covariance_blocks'][b],rtol=1e-12,atol=0),'full_5x5_blocks_'+str(b))
      check(np.allclose(t,p['tensor_covariance'][b],rtol=1e-12,atol=0),'full_rank4_tensor_'+str(b))
    for name,(mats,bounds) in stages.items():
      for lab,m,bb in zip(('band1','band2','sum'),(*mats,sum(mats)),(*bounds,sum(bounds))):
        trace=np.trace(m);eig=np.linalg.eigvalsh((m+m.T)/2);sd=np.sqrt(np.diag(m))
        check(m.shape==(15,15) and bb.shape==(15,15) and np.all(np.isfinite(m)) and np.all(np.diag(m)>0),'joint_shape_finite_'+name+lab)
        check(np.max(abs(m-m.T))<=1e-12*trace and eig[0]>=-1e-12*trace,'joint_symmetry_psd_'+name+lab,{'min_eigenvalue':float(eig[0]),'trace':float(trace)})
        norm=float(np.max(bb/np.outer(sd,sd)))
        check(norm<=5e-5,'sensitivity_entry_'+name+lab,{'max_normalized_entry':norm})
        for r in range(3):
          sl=slice(5*r,5*r+5);sub=m[sl,sl];B=bb[sl,sl]
          val,vec=np.linalg.eigh(sub);ok=val>1e-10*val[-1]
          check(np.any(ok),'nonempty_support_'+name+lab+str(r))
          inv=(vec[:,ok]/np.sqrt(val[ok]))@vec[:,ok].T
          fro=np.linalg.norm(B)/np.linalg.norm(sub);white=np.linalg.norm(abs(inv)@B@abs(inv),2)
          check(fro<=3e-5 and white<=2e-4,'sensitivity_block_'+name+lab+str(r),{'relative_fro':float(fro),'whitened':float(white),'ranks':[int(sum(val>t*val[-1])) for t in (1e-12,1e-10,1e-8)]})
    for early,late in (('A','B'),('B','C')):
      old,bo=stages[early];new,bn=stages[late]
      for lab,A,B,EA,EB in zip(('band1','band2','sum'),(*old,sum(old)),(*new,sum(new)),(*bo,sum(bo)),(*bn,sum(bn))):
        delta=B-A;env=EA+EB;sd=np.sqrt(np.diag(B));joint=np.max((abs(delta)+env)/np.outer(sd,sd))
        check(joint<=.005,'joint_convergence_'+early+late+lab,{'max_normalized_entry':float(joint)})
        for r in range(3):
          sl=slice(5*r,5*r+5);x=B[sl,sl];d=delta[sl,sl];e=env[sl,sl]
          val,vec=np.linalg.eigh(x);prior=np.linalg.eigvalsh(A[sl,sl]);thresholds=(1e-12,1e-10,1e-8)
          ranks=[int(sum(val>t*val[-1])) for t in thresholds];oldr=[int(sum(prior>t*prior[-1])) for t in thresholds]
          check(len(set(ranks))==1 and ranks==oldr,'support_'+early+late+lab+str(r),{'early_ranks':oldr,'late_ranks':ranks})
          ok=val>1e-10*val[-1];inv=(vec[:,ok]/np.sqrt(val[ok]))@vec[:,ok].T
          fro=(np.linalg.norm(d)+np.linalg.norm(e))/np.linalg.norm(x)
          white=np.linalg.norm(inv@d@inv,2)+np.linalg.norm(abs(inv)@e@abs(inv),2)
          check(fro<=.003 and white<=.02,'block_convergence_'+early+late+lab+str(r),{'relative_fro':float(fro),'whitened':float(white)})
    check(result['angular_A_B_pass'] is True and result['radial_B_C_pass'] is True,'mandatory_convergence_report')
    check(result['global_rigorous_type3_error_enclosure']=='NOT_ESTABLISHED' and result['original_H02_H04']=='HOLD','claim_ceiling')
    check(all(result['full_tensor_images'][q]=='UNDEFINED/HOLD' for q in ('x','F','Pi','Q','G_F')),'physical_image_holds')
    return {'status':'SCOPED_INDEPENDENT_NUMERICAL_PASS','source_hashes':checks,'direct_targets':len(selected),'direct_max_relative_l2':worst_rel,'direct_max_component_scale':worst_component,'eps_high_l2':ehi,'eps_low_l2':elo,'eps_floor_l2':floor,'global_rigorous_type3_error_enclosure':'NOT_ESTABLISHED','original_H02_H04':'HOLD','scientific_admission':False}
if __name__=='__main__':
    start=time.monotonic();res=None
    try:res=main()
    except BaseException as e:res={'status':'HOLD','first_failure':f'{type(e).__name__}: {e}','traceback':traceback.format_exc(),'scientific_admission':False}
    res['elapsed_seconds']=time.monotonic()-start;res['gates']=SCORES
    path=OUT/'CHECK_RESULT.json';tmp=OUT/'CHECK_RESULT.tmp';tmp.write_text(json.dumps(res,indent=2,allow_nan=False));tmp.replace(path)
    with open(path,'rb') as f:import os;os.fsync(f.fileno())
    print(json.dumps({k:v for k,v in res.items() if k!='gates' and k!='traceback'},allow_nan=False),flush=True)
    raise SystemExit(0 if res['status']=='SCOPED_INDEPENDENT_NUMERICAL_PASS' else 1)
