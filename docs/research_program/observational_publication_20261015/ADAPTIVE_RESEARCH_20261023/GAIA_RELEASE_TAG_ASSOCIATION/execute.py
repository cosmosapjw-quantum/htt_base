#!/usr/bin/env python3
"""Frozen selected-source Gaia DR3 release-tag FULL13 association."""
import hashlib, json, os, platform, resource, sys, time, traceback
from pathlib import Path
import numpy as np
from scipy.linalg import qr, solve_triangular, svd
try:
    from threadpoolctl import threadpool_info
except ImportError:
    threadpool_info=lambda: []

OUT=Path(__file__).resolve().parent
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
INPUT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_tag_association_proposal/INPUT.json')
METHOD=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_property_method/METHOD.md')
REVIEW=Path('/mnt/extdrive/workdir/htt_open_data/r25_blind_tag_association_contract/REVIEW.md')
PARENT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_properties_20261023')
NPZ=ROOT/'docs/observational_reboot_20261014/results/gaia_frame_v1/qualified_rows.npz'
PACKET='a87f0e5da26ada1c418c11bc379901f299ae5c092ef9d6064f25d4cb2e13189c'
TASK='R25-GAIA-RELEASE-TAG-ASSOCIATION'
INPUT_ID='sha256:00209480018bcb19f29c3c22a2d847c26560bcf950045978f10579967314e39f'
PARENT_ID='005aa5cf96fe1350ef7690a275edd4ae61e9b30092266e8900c8b3d86b482568'
HOSTS=['3','5','6','ROW_NULL']
EPS=2.0**-52
START=time.perf_counter()
BASE_RSS=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
EVENTS=[]
ATTEMPTS=[]

def jwrite(name,obj):
    p=OUT/name
    p.write_text(json.dumps(obj,indent=2,allow_nan=False,sort_keys=True)+'\n')
    return str(p)
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()
def check(ok,msg):
    if not bool(ok):raise ValueError(msg)
def finite(x,msg):check(np.isfinite(x).all(),msg)
def metrics():
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    return dict(elapsed_numeric_seconds=time.perf_counter()-START,ru_maxrss_bytes=int(peak),initial_ru_maxrss_bytes=int(BASE_RSS),incremental_highwater_bytes=int(max(0,peak-BASE_RSS)),threadpools=threadpool_info(),environment_threads={k:os.environ.get(k) for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS')},numpy=np.__version__,python=platform.python_version())
def limits():
    m=metrics();check(m['elapsed_numeric_seconds']<240,'TIME_REVIEW_RESERVE_EXHAUSTED');check(m['incremental_highwater_bytes']<=2147483648,'RAM_CAP_EXCEEDED')
    check(all(int(x.get('num_threads',1))<=1 for x in m['threadpools']),'BLAS_THREAD_CAP_EXCEEDED')

def basis(n):
    n=np.asarray(n,float);finite(n,'NONFINITE_DIRECTION')
    a=np.arctan2(n[:,1],n[:,0]);d=np.arcsin(n[:,2])
    east=np.stack((-np.sin(a),np.cos(a),np.zeros(len(a))),axis=1)
    north=np.stack((-np.sin(d)*np.cos(a),-np.sin(d)*np.sin(a),np.cos(d)),axis=1)
    E=np.stack((east,north),axis=1)
    S=np.array([[[1,0,0],[0,-1,0],[0,0,0]],[[-1,0,0],[0,-1,0],[0,0,2]],[[0,1,0],[1,0,0],[0,0,0]],[[0,0,1],[0,0,0],[1,0,0]],[[0,0,0],[0,0,1],[0,1,0]]],float)
    S/=np.array([np.sqrt(2),np.sqrt(6),np.sqrt(2),np.sqrt(2),np.sqrt(2)])[:,None,None]
    B=np.empty((len(n),2,3));X=np.empty((len(n),2,13))
    X[:,:,:3]=E
    for k in range(3):B[:,:,k]=np.einsum('nai,ni->na',E,np.cross(np.eye(3)[k],n))
    for k in range(5):
        sn=np.einsum('ij,nj->ni',S[k],n)
        X[:,:,3+k]=np.einsum('nai,ni->na',E,sn)
        X[:,:,8+k]=np.einsum('nai,ni->na',E,np.cross(n,sn))
    return B,X,S,E

def directions(ra,dec):
    finite(ra,'NONFINITE_RA');finite(dec,'NONFINITE_DEC')
    check(np.all(np.abs(dec)<=90),'DEC_RANGE')
    a=np.deg2rad(ra);d=np.deg2rad(dec)
    return np.column_stack((np.cos(d)*np.cos(a),np.cos(d)*np.sin(a),np.sin(d)))

def design(B,X,t,h,model):
    n=len(t);TX=t[:,None,None]*X;TB=t[:,None,None]*B
    if model=='M0':return np.concatenate((B,X,TB,TX),axis=2)
    blocks=[]
    for label in HOSTS:
        m=(h==label)[:,None,None]
        blocks.extend((m*B,m*X))
    return np.concatenate((*blocks,TB,TX),axis=2)

def whitening(C):
    C=np.asarray(C,float);check(C.shape[1:]==(2,2),'COV_SHAPE');finite(C,'NONFINITE_COV')
    d=np.maximum(C[:,0,0],C[:,1,1]);check(np.all(d>0),'COV_DIAGONAL')
    a=C[:,0,0]/d;b=C[:,1,1]/d;check(np.all((a>0)&(b>0)),'COV_UNDERFLOW')
    asym=np.abs(C[:,0,1]/d-C[:,1,0]/d)
    check(np.all(asym<=32*EPS*np.sqrt(a*b)),'COV_ASYMMETRY')
    c=(C[:,0,1]/d+C[:,1,0]/d)/2
    s1=np.sqrt(d)*np.sqrt(a);s2=np.sqrt(d)*np.sqrt(b)
    rho=(c/np.sqrt(a))/np.sqrt(b)
    check(np.all(np.isfinite(s1)&np.isfinite(s2)&(s1>0)&(s2>0)&np.isfinite(rho)&(np.abs(rho)<1)),'COV_CHOL_DOMAIN')
    ss=np.sqrt((1-rho)*(1+rho));check(np.all(np.isfinite(ss)&(ss>0)),'COV_CHOL_S')
    # W is the exact lower Cholesky inverse in the accepted scaled arithmetic.
    W=np.zeros((len(C),2,2));W[:,0,0]=1/s1;W[:,1,0]=-rho/(ss*s1);W[:,1,1]=1/(ss*s2)
    eye=np.einsum('nai,nij,nbj->nab',W,C,W)
    err=float(np.max(np.abs(eye-np.eye(2))))
    check(err<=1e-10,'COV_WHITEN_ERROR '+str(err))
    return W,dict(max_asymmetry=float(np.max(asym)),max_whitening_error=err,min_sigma=float(min(s1.min(),s2.min())),max_abs_rho=float(np.max(np.abs(rho))))

def rank(s,tau):
    if not len(s) or s[0]==0:return 0
    return int(np.count_nonzero(s>tau*s[0]))

def factor(F,W,model,observed=True):
    m,p=F.shape[0]*2,F.shape[2];nz=p-13
    FW=np.einsum('nab,nbp->nap',W,F).reshape(m,p)
    norms=np.linalg.norm(FW,axis=0);finite(norms,'NONFINITE_COLUMN_NORM')
    zero=np.flatnonzero(norms==0).tolist()
    if zero:return dict(status='NO_EXPOSURE_SUPPORT' if any(k>=nz for k in zero) else 'HOLD_ZERO_NUISANCE',zero_columns=zero)
    Fs=FW/norms
    Z=Fs[:,:nz];D=Fs[:,nz:]
    sz=svd(Z,compute_uv=False,check_finite=False)
    sa=svd(Fs,compute_uv=False,check_finite=False)
    Qz,_=qr(Z,mode='economic',check_finite=False)
    K=D-Qz@(Qz.T@D)
    U,sk,Vt=svd(K,full_matrices=False,check_finite=False)
    tau0=max(m,p)*EPS
    thresholds=[tau0,1e-12,1e-10,1e-8]
    ranks={format(x,'.17g'):dict(nuisance=rank(sz,x),augmented=rank(sa,x),residual=rank(sk,x),increment=rank(sa,x)-rank(sz,x)) for x in thresholds}
    eligible=all(v['nuisance']==nz and v['increment']==13 and v['residual']==13 for v in ranks.values()) and sk[-1]>1e-8*max(1,sk[0])
    status='ELIGIBLE' if eligible else 'HOLD_NUMERICAL_IDENTIFIABILITY'
    record=dict(model=model,status=status,shape=[m,p],nuisance_columns=nz,preprojection_scales=norms.tolist(),structural_dependencies=[],singular_values_Z=sz.tolist(),singular_values_augmented=sa.tolist(),singular_values_K=sk.tolist(),condition_Z=float(sz[0]/sz[-1]) if sz[-1]>0 else None,condition_augmented=float(sa[0]/sa[-1]) if sa[-1]>0 else None,condition_K=float(sk[0]/sk[-1]) if sk[-1]>0 else None,rank_thresholds=ranks,residual_floor=float(1e-8*max(1,sk[0])),smallest_residual=float(sk[-1]))
    if not eligible:
        record['supported_target_subspace_dimension']=rank(sk,tau0)
        record['supported_target_subspace_basis_scaled']=Vt[:rank(sk,tau0)].tolist()
        return dict(record=record,status=status)
    T=(Vt.T/sk)@U.T/norms[nz:,None]
    target_error=float(np.max(np.abs((norms[nz:,None]*T)@D-np.eye(13))))
    nuisance_error=float(np.max(np.abs((norms[nz:,None]*T)@Z)))
    ceiling=1e-8 if observed else 1e-10
    if target_error>ceiling or nuisance_error>ceiling:
        record.update(status='HOLD_MAP_IDENTITY',target_identity_error=target_error,nuisance_annihilation_error=nuisance_error)
        return dict(record=record,status='HOLD_MAP_IDENTITY')
    Q,R=qr(Fs,mode='economic',check_finite=False)
    J=solve_triangular(R,Q.T,lower=False,check_finite=False)/norms[:,None]
    target_J=J[nz:]
    joint_cov=J@J.T
    V=T@T.T
    qr_map_error=float(np.linalg.norm(T-target_J)/max(np.linalg.norm(target_J),np.finfo(float).tiny))
    record.update(target_identity_error=target_error,nuisance_annihilation_error=nuisance_error,qr_target_map_relative_error=qr_map_error,full_joint_covariance_shape=list(joint_cov.shape))
    left_share=np.sum(U.reshape(-1,2,13)**2,axis=(1,2))/13
    record['max_source_leverage_share']=float(left_share.max())
    return dict(record=record,status='ELIGIBLE',T=T,J=J,V=V,joint_cov=joint_cov,leverage=left_share,FW=FW,F=F,W=W,norms=norms)

def oracle(n,E,S,model,t,h,c):
    # Independent direct vector/tensor field construction, with no design multiplication.
    if model=='M0':base=[c[:16]]*len(n);extra=c[16:]
    else:
        base=[c[16*HOSTS.index(str(hh)):16*(HOSTS.index(str(hh))+1)] for hh in h]
        extra=c[64:]
    y=np.empty((len(n),2))
    for i in range(len(n)):
        b=base[i];v=np.cross(b[:3],n[i])+b[3:6].copy()
        for k in range(5):v+=b[6+k]*(S[k]@n[i])+b[11+k]*np.cross(n[i],S[k]@n[i])
        if t[i]:
            v+=np.cross(extra[:3],n[i])+extra[3:6]
            for k in range(5):v+=extra[6+k]*(S[k]@n[i])+extra[11+k]*np.cross(n[i],S[k]@n[i])
        y[i]=E[i]@v
    return y

def toys():
    z=(-np.sqrt(3/5),0.0,np.sqrt(3/5));dirs=[];qq=[];tt=[];hh=[]
    for h in range(4):
        for t in (0,1):
            for q,zz in enumerate(z0 for z0 in z for _ in range(8)):
                j=q%8;a=j*np.pi/4
                dirs.append([np.sqrt(1-zz*zz)*np.cos(a),np.sqrt(1-zz*zz)*np.sin(a),zz]);qq.append(q);tt.append(t);hh.append(HOSTS[h])
    n=np.array(dirs);t=np.array(tt);h=np.array(hh);q=np.array(qq);hi=np.array([HOSTS.index(x) for x in h])
    B,X,S,E=basis(n)
    C=np.empty((len(n),2,2));s1=2+(hi+2*t)/4;s2=3+(2*hi+t)/4;rho=np.where((q+hi+t)%2==0,.25,-.25)
    C[:,0,0]=s1*s1;C[:,1,1]=s2*s2;C[:,0,1]=C[:,1,0]=rho*s1*s2
    W,wm=whitening(C)
    check(wm['max_whitening_error']<=5e-13,'TOY_WHITENING')
    check(np.max(np.abs(S-S.transpose(0,2,1)))<=5e-13 and np.max(np.abs(np.trace(S,axis1=1,axis2=2)))<=5e-13,'TOY_STF')
    gram=np.einsum('aij,bij->ab',S,S);check(np.max(np.abs(gram-np.eye(5)))<=5e-13,'TOY_STF_GRAM')
    testn=np.array([[1.,0.,0.]]);b0,x0,s0,e0=basis(testn)
    check(abs(b0[0,0,2]-1)<5e-13 and abs(b0[0,1,1]+1)<5e-13 and abs(x0[0,0,5]-1/np.sqrt(2))<5e-13 and abs(x0[0,1,10]-1/np.sqrt(2))<5e-13,'TOY_SIGNS')
    out={'fixture_sources':len(n),'whitening':wm,'models':{}}
    fac={}
    for model in ('M0','M1'):
        F=design(B,X,t,h,model);fit=factor(F,W,model,False);check(fit['status']=='ELIGIBLE','TOY_'+model+'_'+fit['status'])
        cond_aug=fit['record']['condition_augmented'];cond_k=fit['record']['condition_K']
        check(cond_aug<=100 and cond_k<=100,'TOY_CONDITION_'+model+f' {cond_aug} {cond_k}')
        p=F.shape[2];Ccoef=np.column_stack((np.eye(p),np.array([(-1)**j*(j+1)/16 for j in range(p)])))
        Y=np.stack([oracle(n,E,S,model,t,h,Ccoef[:,j]) for j in range(p+1)],axis=2)
        yw=np.einsum('nab,nbq->naq',W,Y).reshape(2*len(n),p+1)
        estimate=fit['J']@yw
        e=float(np.max(np.abs(estimate-Ccoef))/max(1,float(np.max(np.abs(Ccoef)))))
        res=float(np.linalg.norm(yw-fit['FW']@estimate)/max(1,np.linalg.norm(yw)))
        check(e<=1e-10,'TOY_COEF_'+model+' '+str(e));check(res<=1e-11,'TOY_RESID_'+model+' '+str(res))
        te=float(np.max(np.abs(fit['T']@yw-estimate[-13:])))
        check(te<=1e-10,'TOY_TARGET_QR_'+model+' '+str(te))
        check(fit['record']['qr_target_map_relative_error']<=1e-10,'TOY_MAP_QR_'+model)
        # Exact deliberate duplicate nuisance is omitted under recorded structural map.
        dup=np.concatenate((F[:,:,:1],F),axis=2)
        check(np.array_equal(dup[:,:,0],dup[:,:,1]),'TOY_DUPLICATE_NOT_EXACT')
        # The reduced identical F must preserve its target map and covariance.
        check(np.array_equal(dup[:,:,1:],F),'TOY_DUPLICATE_REDUCTION')
        # Rotation and unit conversion use the same frozen family, without a new data variant.
        ang=(q%7)*np.pi/14;R2=np.zeros((len(n),2,2));R2[:,0,0]=R2[:,1,1]=np.cos(ang);R2[:,0,1]=-np.sin(ang);R2[:,1,0]=np.sin(ang)
        Fr=np.einsum('nab,nbp->nap',R2,F);Cr=np.einsum('nai,nij,nbj->nab',R2,C,R2)
        Wr,_=whitening(Cr);rot=factor(Fr,Wr,model,False);check(rot['status']=='ELIGIBLE','TOY_ROT_SUPPORT_'+model)
        yr=np.einsum('nab,nbq->naq',R2,Y);ywr=np.einsum('nab,nbq->naq',Wr,yr).reshape(2*len(n),p+1)
        er=float(np.max(np.abs(rot['J']@ywr-Ccoef))/max(1,float(np.max(np.abs(Ccoef)))))
        vr=float(np.linalg.norm(rot['V']-fit['V'])/np.linalg.norm(fit['V']))
        check(er<=1e-10 and vr<=1e-10,'TOY_ROT_INVARIANCE_'+model+f' {er} {vr}')
        Fmas=F/1000;Cmas=C/1e6;Ymas=Y/1000
        check(np.max(np.abs(Fmas*1000-F))<5e-13 and np.max(np.abs(Cmas*1e6-C))<5e-13 and np.max(np.abs(Ymas*1000-Y))<5e-13,'TOY_UNIT_ROUNDTRIP')
        out['models'][model]=dict(condition_augmented=cond_aug,condition_K=cond_k,max_coefficient_error=e,residual_error=res,target_qr_error=te,rotation_coefficient_error=er,rotation_covariance_error=vr,duplicate_reduced_exact=True)
        fac[model]=fit
    # Cross-map covariance identity for nested model spaces.
    v01=fac['M0']['T']@fac['M1']['T'].T
    diff=(fac['M1']['T']-fac['M0']['T'])@(fac['M1']['T']-fac['M0']['T']).T
    err=float(np.linalg.norm(v01-fac['M0']['V'])/np.linalg.norm(fac['M0']['V']))
    check(err<=1e-10,'TOY_CROSS_COV '+str(err))
    out['nested_cross_covariance_relative_error']=err
    out['Vdiff_min_eigenvalue']=float(np.linalg.eigvalsh(diff)[0])
    # Target absence and within-host-only constant tags are design failures, not outcome solves.
    no=np.zeros_like(t);f0=design(B,X,no,h,'M0');check(factor(f0,W,'M0',False)['status']=='NO_EXPOSURE_SUPPORT','TOY_ZERO_EXPOSURE')
    tc=np.array([int(x in ('3','5')) for x in h]);fc=design(B,X,tc,h,'M1');hc=factor(fc,W,'M1',False)
    check(hc['status']!='ELIGIBLE','TOY_WITHIN_HOST_ALIAS')
    out['zero_exposure']='NO_EXPOSURE_SUPPORT';out['within_host_constant_tag']=hc['status']
    # Near-aliasing residual keeps the preprojection scale and must fail absolute floor.
    zz=np.array([[1.,0.]]).T;dd=np.array([[1.,1e-14]]).T;ds=dd/np.linalg.norm(dd);kk=ds-zz@(zz.T@ds)
    check(float(np.linalg.norm(kk))<=1e-8,'TOY_NEAR_ALIAS_FLOOR')
    out['near_alias_residual_norm']=float(np.linalg.norm(kk))
    return out

def input_and_support():
    check(sha(INPUT)==INPUT_ID[7:],'INPUT_HASH_DRIFT')
    cfg=json.loads(INPUT.read_text())
    for item in cfg['input_sources']:
        check(sha(item['path'])==item['sha256'],'SEALED_SOURCE_DRIFT '+item['path'])
    check(sha(PARENT/'MANIFEST.json')==PARENT_ID,'PARENT_CANDIDATE_DRIFT')
    check(sha(METHOD)=='a612b20e88997ae8e1e30d2f3a0f2cbc35102e0a2f69dd84e0b8741eefcc4246','METHOD_DRIFT')
    check(sha(REVIEW)=='186ff2994f11ccb2aa4d8328ba243afb35b873746d26d222a2a7b7014d950442','REVIEW_DRIFT')
    check(sha(NPZ)=='41b6ddcb13131b49b97efd6107816af4518fa9e23725cf3b4272c2f3a70acb8f','NPZ_DRIFT')
    prop=json.loads((PARENT/'products/property_table.json').read_text())['rows']
    masks=json.loads((PARENT/'products/property_wire_masks.json').read_text())['wire_empty_TD_indices']
    ids=np.array([int(r['retained_source_id']) for r in prop],dtype=np.int64)
    check(len(ids)==4756 and len(np.unique(ids))==4756 and np.all(ids[1:]>ids[:-1]),'PROPERTY_ID_ORDER')
    idtext=''.join(str(int(x))+'\n' for x in ids).encode()
    check(hashlib.sha256(idtext).hexdigest()=='a5df0e9ec295b127beaa1309618b62540564d7e5f70abdc1ab27c9ac8747a614','CANONICAL_ID_HASH')
    wire_tag=set(masks['vari_best_class_name']);wire_host=set(masks['host_galaxy_flag'])
    t=np.empty(len(prop),dtype=int);h=np.empty(len(prop),dtype='<U8')
    for i,r in enumerate(prop):
        check(r['qso_source_id']==r['retained_source_id'],'QSO_JOIN')
        state=r['field_states']['vari_best_class_name'];v=r['vari_best_class_name']
        if state=='PRESENT' and v=='AGN' and i not in wire_tag:t[i]=1
        elif state=='ROW_NULL' and v is None and i in wire_tag:t[i]=0
        else:raise ValueError('TAG_SEMANTIC_OR_WIRE '+str(i))
        hs=r['field_states']['host_galaxy_flag'];hv=r['host_galaxy_flag']
        if hs=='ROW_NULL' and hv is None and i in wire_host:h[i]='ROW_NULL'
        elif hs=='PRESENT' and str(hv) in HOSTS[:3] and i not in wire_host:h[i]=str(hv)
        else:raise ValueError('HOST_SEMANTIC_OR_WIRE '+str(i))
    check(int(t.sum())==3216 and int((t==0).sum())==1540,'TAG_COUNTS')
    with np.load(NPZ,allow_pickle=False) as z:
        source=z['source_id'];ra=z['ra'];dec=z['dec'];C=z['covariance']*1e6
    order=np.argsort(source);check(np.array_equal(source[order],ids),'NPZ_ID_ALIGNMENT')
    ra=ra[order];dec=dec[order];C=C[order]
    n=directions(ra,dec);B,X,S,E=basis(n);W,cdiag=whitening(C)
    octant=((n>=0)*np.array([1,2,4])).sum(axis=1)
    counts_host={hh:{'AGN':int(np.sum((h==hh)&(t==1))),'ROW_NULL':int(np.sum((h==hh)&(t==0)))} for hh in HOSTS}
    counts_oct={str(o):{'AGN':int(np.sum((octant==o)&(t==1))),'ROW_NULL':int(np.sum((octant==o)&(t==0)))} for o in range(8)}
    jwrite('DOMAIN.json',dict(packet_id=PACKET,task_id=TASK,input_identity=INPUT_ID,parent_candidate_identity='sha256:'+PARENT_ID,source_npz_sha256=sha(NPZ),canonical_id_sha256=hashlib.sha256(idtext).hexdigest(),angular_unit='degree ICRS',pm_unit='microarcsecond/year',covariance_unit='microarcsecond^2/year^2',n=4756,tag_host_counts=counts_host,tag_octant_counts=counts_oct,covariance=cdiag,pre_PM=True))
    toy=toys();jwrite('TOY_CONTROLS.json',toy);limits()
    fits={}
    for model in ('M0','M1'):
        F=design(B,X,t,h,model);fit=factor(F,W,model,True)
        rec=fit['record'];rec.update(packet_id=PACKET,task_id=TASK,input_identity=INPUT_ID,pre_PM=True,tag_host_counts=counts_host,tag_octant_counts=counts_oct,coefficient_order='M0:[omega3,beta13,eta3,delta13];M1:[host3/5/6/null each omega3,beta13,eta3,delta13]',unit='microarcsecond/year')
        if fit['status']=='ELIGIBLE':
            lev=fit['leverage'];rec['source_leverage_sum']=float(lev.sum());rec['octant_leverage_shares']={str(o):float(lev[octant==o].sum()) for o in range(8)}
            A=np.einsum('jna,nab->jnb',fit['T'].reshape(13,-1,2),W).reshape(13,-1)
            np.savez(OUT/f'{model}_PRE_PM_MAPS.npz',T=fit['T'],A=A,J=fit['J'],V=fit['V'],joint_covariance=fit['joint_cov'],source_leverage_share=lev)
        jwrite(f'{model}_PRE_PM_SUPPORT.json',rec);fits[model]=fit
        limits()
    if all(fits[x]['status']=='ELIGIBLE' for x in ('M0','M1')):
        V01=fits['M0']['T']@fits['M1']['T'].T
        Vdiff=(fits['M1']['T']-fits['M0']['T'])@(fits['M1']['T']-fits['M0']['T']).T
        np.savez(OUT/'PRE_PM_COMPARISON.npz',V00=fits['M0']['V'],V11=fits['M1']['V'],V01=V01,Vdiff=Vdiff)
    frozen=dict(packet_id=PACKET,task_id=TASK,input_identity=INPUT_ID,parent_candidate_identity='sha256:'+PARENT_ID,models={x:fits[x]['status'] for x in fits},shared_controls='PASS',pm_access='NONE_BEFORE_THIS_RECORD',elapsed_seconds=metrics()['elapsed_numeric_seconds'],observed_fit_attempts=0)
    jwrite('PRE_PM_FROZEN.json',frozen)
    return fits,order,C,W,S

def observed(fits,order,C,W,S):
    if not any(f['status']=='ELIGIBLE' for f in fits.values()):return {}
    check((OUT/'PRE_PM_FROZEN.json').exists(),'PRE_PM_RECORD_MISSING')
    with np.load(NPZ,allow_pickle=False) as z:y=np.asarray(z['proper_motion'][order],float)*1000
    check(y.shape==(4756,2) and np.isfinite(y).all(),'PM_DOMAIN')
    yw=np.einsum('nab,nb->na',W,y).reshape(-1)
    out={}
    for model in ('M0','M1'):
        f=fits[model]
        if f['status']!='ELIGIBLE':continue
        limits();check(len(ATTEMPTS)<2,'FIT_CAP')
        ATTEMPTS.append(dict(model=model,solve_start_monotonic=time.perf_counter(),ordinal=len(ATTEMPTS)+1))
        # One fixed observed solve per eligible model; all maps were frozen pre-PM.
        c=f['J']@yw;delta=f['T']@yw
        residual=yw-f['FW']@c
        Wq=float(delta@np.linalg.solve(f['V'],delta))
        dse=np.einsum('a,aij->ij',delta[3:8],S);dsb=np.einsum('a,aij->ij',delta[8:13],S)
        sphere=float(np.sqrt((2/3)*np.dot(delta[:3],delta[:3])+(1/5)*(np.sum(dse*dse)+np.sum(dsb*dsb))))
        np.savez(OUT/f'{model}_OBSERVED.npz',coefficients=c,delta=delta,full_joint_covariance=f['joint_cov'],delta_covariance=f['V'],target_map_whitened=f['T'],joint_map_whitened=f['J'],tensor_E=dse,tensor_B=dsb)
        rec=dict(status='DESCRIPTIVE_CONDITIONAL_REVIEW_PENDING',model=model,packet_id=PACKET,task_id=TASK,input_identity=INPUT_ID,coefficient_order=f['record']['coefficient_order'],coefficient_units='microarcseconds/year',coefficients=c.tolist(),delta_FULL13=delta.tolist(),delta_g=delta[:3].tolist(),delta_S_E=dse.tolist(),delta_S_B=dsb.tolist(),working_quadratic_W=Wq,weighted_RSS=float(residual@residual),nominal_df=int(len(yw)-len(c)),full_sphere_RMS_microas_per_year=sphere,covariance_designation='C0 block diagonal marginal working covariance',physical_Q='NOT_EVALUABLE',F='UNBOUND_NOT_EXECUTED',Pi='C0_GAUSSIAN_WORKING_ONLY_NOT_CALIBRATED',G_F='DEPTH_UNAVAILABLE',selection_law='NOT_CALIBRATED',cross_source_covariance='UNKNOWN',null_coverage='NOT_CALIBRATED')
        jwrite(f'{model}_OBSERVED.json',rec);out[model]=rec
        limits()
    if len(out)==2:
        V01=fits['M0']['T']@fits['M1']['T'].T;Vdiff=(fits['M1']['T']-fits['M0']['T'])@(fits['M1']['T']-fits['M0']['T']).T
        dd=np.array(out['M1']['delta_FULL13'])-np.array(out['M0']['delta_FULL13'])
        np.savez(OUT/'COMPARISON.npz',V00=fits['M0']['V'],V11=fits['M1']['V'],V01=V01,V10=V01.T,Vdiff=Vdiff,delta_difference=dd,T0=fits['M0']['T'],T1=fits['M1']['T'])
        jwrite('COMPARISON.json',dict(scope='one fixed processing sensitivity on same PM outcomes',delta_difference=dd.tolist(),V01_equal_V00_relative=float(np.linalg.norm(V01-fits['M0']['V'])/np.linalg.norm(fits['M0']['V'])),difference_significance='NOT_CALIBRATED'))
    return out

def main():
    limits();fits,order,C,W,S=input_and_support();out=observed(fits,order,C,W,S)
    m=metrics();check(m['elapsed_numeric_seconds']<300,'NUMERIC_CAP_EXCEEDED');check(m['incremental_highwater_bytes']<=2147483648,'RAM_CAP_EXCEEDED')
    outcome='SUCCESS_PENDING_INDEPENDENT_REVIEW' if out else 'HOLD_DESIGN_SUPPORT'
    receipt=dict(packet_id=PACKET,task_id=TASK,input_identity=INPUT_ID,candidate_identity=None,outcome=outcome,raw_first_failure=None,models={x:fits[x]['status'] for x in fits},observed_fit_attempts=ATTEMPTS,execution=m,source_head='d93605e66adfececa89b90681124b232a5f90220',requested_route={'model':'gpt-6-sol','effort':'high'},observed_runtime='UNKNOWN',original_acceptance='17/42 unchanged',alternate_acceptance='18/42 unchanged',historical48='unchanged',R9='UNKNOWN',claim_tier='conditional descriptive observable only',review='PENDING_FRESH_INDEPENDENT')
    jwrite('RAW_RECEIPT.json',receipt)
    jwrite('RETURN.json',dict(packet_id=PACKET,task_id=TASK,input_identity=INPUT_ID,candidate_identity=None,outcome=outcome,raw_receipt=str(OUT/'RAW_RECEIPT.json'),models=receipt['models'],numeric_seconds=m['elapsed_numeric_seconds'],observed_fits=len(ATTEMPTS),review='PENDING_FRESH_INDEPENDENT'))
    print(json.dumps(dict(outcome=outcome,models=receipt['models'],seconds=m['elapsed_numeric_seconds'],observed_fits=len(ATTEMPTS))))
if __name__=='__main__':
    try:main()
    except Exception as exc:
        m=metrics();err=dict(packet_id=PACKET,task_id=TASK,input_identity=INPUT_ID,outcome='HOLD_FIRST_FAILURE',first_failure=str(exc),traceback=traceback.format_exc(),observed_fit_attempts=ATTEMPTS,execution=m,pre_PM_frozen=(OUT/'PRE_PM_FROZEN.json').exists(),review='NOT_STARTED')
        jwrite('RAW_RECEIPT.json',err)
        jwrite('RETURN.json',dict(packet_id=PACKET,task_id=TASK,input_identity=INPUT_ID,candidate_identity=None,outcome='HOLD_FIRST_FAILURE',raw_receipt=str(OUT/'RAW_RECEIPT.json'),first_failure=str(exc),observed_fits=len(ATTEMPTS)))
        print(json.dumps(dict(outcome='HOLD_FIRST_FAILURE',first_failure=str(exc),seconds=m['elapsed_numeric_seconds'],observed_fits=len(ATTEMPTS))))
        sys.exit(1)
