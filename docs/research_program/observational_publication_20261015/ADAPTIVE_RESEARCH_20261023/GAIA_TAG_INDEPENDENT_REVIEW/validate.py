#!/usr/bin/env python3
# Independent checks of frozen source, saved maps, and deterministic toy controls.
# No proper_motion member is read and no observed fit is evaluated.
import time
START=time.perf_counter()
import json, hashlib, resource, traceback, runpy, os, xml.etree.ElementTree as ET
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(150,150))
import numpy as np
from scipy.linalg import qr, solve_triangular
from threadpoolctl import threadpool_info
OUT=Path(__file__).parent
CAND=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_release_tag_association')
PARENT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_source_properties_20261023')
PACK=Path('/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/receipts/POST_SOURCE_INTEGRATION_REVIEW_PACKET.json')
INPUT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_tag_association_proposal/INPUT.json')
NPZ=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/observational_reboot_20261014/results/gaia_frame_v1/qualified_rows.npz')
checks={}; failures=[]
def seal(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mx(x):return float(np.max(np.abs(x)))
def rel(a,b):return float(np.linalg.norm(a-b)/max(np.linalg.norm(b),1e-300))
def ck(name,value,tol=0):
    checks[name]={'value':float(value),'ceiling':float(tol),'pass':bool(np.isfinite(value) and value<=tol)}
    if not checks[name]['pass']: failures.append(name)
def exact(name,ok):ck(name,0 if ok else 1)
S=np.zeros((5,3,3));S[0]=np.diag([1,-1,0])/np.sqrt(2);S[1]=np.diag([-1,-1,2])/np.sqrt(6)
for k,(i,j) in enumerate([(0,1),(0,2),(1,2)],2):S[k,i,j]=S[k,j,i]=1/np.sqrt(2)
HOSTS=['3','5','6','ROW_NULL']
def geometry(a,d):
    n=np.column_stack((np.cos(d)*np.cos(a),np.cos(d)*np.sin(a),np.sin(d)))
    e=np.stack((np.column_stack((-np.sin(a),np.cos(a),np.zeros(len(a)))),np.column_stack((-np.sin(d)*np.cos(a),-np.sin(d)*np.sin(a),np.cos(d)))),axis=1)
    # Closed spin component formulas, independent of author's cross-product construction.
    spin=np.stack((np.column_stack((-np.sin(d)*np.cos(a),-np.sin(d)*np.sin(a),np.cos(d))),np.column_stack((np.sin(a),-np.cos(a),np.zeros(len(a))))),axis=1)
    sn=np.einsum('kij,nj->nki',S,n)
    electric=sn-np.einsum('ni,nki->nk',n,sn)[:,:,None]*n[:,None,:]
    magnetic=np.cross(n[:,None,:],sn)
    X=np.concatenate((e,np.einsum('nai,nki->nak',e,electric),np.einsum('nai,nki->nak',e,magnetic)),axis=2)
    return n,e,spin,X

def design(spin,X,t,h,model):
    base=np.concatenate((spin,X),axis=2)
    if model=='M0':return np.concatenate((base,base*t[:,None,None]),axis=2)
    return np.concatenate([base*(h==k)[:,None,None] for k in HOSTS]+[base*t[:,None,None]],axis=2)
def white(C):
    L=np.linalg.cholesky(C)
    return np.linalg.solve(L,np.broadcast_to(np.eye(2),C.shape))
def fullqr(F,W):
    fw=np.einsum('nab,nbp->nap',W,F).reshape(-1,F.shape[-1])
    q,r=qr(fw,mode='economic')
    return solve_triangular(r,q.T),fw

def field(n,e,c):
    se=np.einsum('k,kij->ij',c[6:11],S);sb=np.einsum('k,kij->ij',c[11:16],S)
    g=c[3:6];sn=n@se.T
    v=np.cross(c[:3],n)+(g-(n@g)[:,None]*n)+(sn-np.einsum('ni,ni->n',n,sn)[:,None]*n)+np.cross(n,n@sb.T)
    return np.einsum('nai,ni->na',e,v)
def toyout(n,e,t,h,c,model):
    if model=='M0':return field(n,e,c[:16])+t[:,None]*field(n,e,c[16:])
    y=t[:,None]*field(n,e,c[64:])
    for k,label in enumerate(HOSTS):y+=(h==label)[:,None]*field(n,e,c[16*k:16*k+16])
    return y

def sphere(delta):
    zz=np.repeat([-np.sqrt(3/5),0,np.sqrt(3/5)],8);aa=np.tile(np.arange(8)*np.pi/4,3)
    n,e,sp,x=geometry(aa,np.arcsin(zz));w=np.repeat([5/18,4/9,5/18],8)/8
    c=np.r_[np.zeros(3),delta];f=field(n,e,c)
    quad=float(w@np.sum(f*f,axis=1));analytic=float((2/3)*np.sum(delta[:3]**2)+(1/5)*np.sum(delta[3:]**2))
    return abs(quad-analytic)/max(1,analytic),np.sqrt(analytic)

try:
    packet=json.loads(PACK.read_text());scope=packet['review_context']['scope']
    exact('input_identity',seal(INPUT)==packet['input_identity'][7:])
    exact('candidate_identity',seal(CAND/'MANIFEST.json')==packet['candidate_identity'][7:])
    for group in ['source_seals','candidate_seals']:
        bad=[]
        for p,v in scope[group].items():
            expected=v['sha256'] if isinstance(v,dict) else v
            if seal(p)!=expected:bad.append(p)
        exact(group+'_complete',not bad)
        checks[group+'_bad_paths']=bad
    manifest=json.loads((CAND/'MANIFEST.json').read_text())
    exact('manifest_file_seals',all(seal(CAND/p)==v['sha256'] and (CAND/p).stat().st_size==v['bytes'] for p,v in manifest['files'].items()))
    props=json.loads((PARENT/'products/property_table.json').read_text())['rows']
    masks=json.loads((PARENT/'products/property_wire_masks.json').read_text())['wire_empty_TD_indices']
    ids=np.array([int(r['retained_source_id']) for r in props],dtype=np.int64)
    exact('ids_canonical',len(ids)==4756 and np.all(np.diff(ids)>0) and hashlib.sha256(''.join(f'{v}\n' for v in ids).encode()).hexdigest()=='a5df0e9ec295b127beaa1309618b62540564d7e5f70abdc1ab27c9ac8747a614')
    t=np.array([int(r['vari_best_class_name']=='AGN') for r in props]);h=np.array([str(r['host_galaxy_flag']) if r['host_galaxy_flag'] is not None else 'ROW_NULL' for r in props])
    exact('literal_tag_states',all((r['vari_best_class_name']=='AGN' and r['field_states']['vari_best_class_name']=='PRESENT' and i not in masks['vari_best_class_name']) or (r['vari_best_class_name'] is None and r['field_states']['vari_best_class_name']=='ROW_NULL' and i in masks['vari_best_class_name']) for i,r in enumerate(props)))
    exact('tag_counts',t.sum()==3216 and (t==0).sum()==1540)
    raw=ET.parse(PARENT/'raw/property_attempt1.vot').getroot(); ns={'v':'http://www.ivoa.net/xml/VOTable/v1.3'}
    # Namespace-independent XML traversal, preserving every wire TD rather than recoding text.
    fields=[x.attrib['name'] for x in raw.iter() if x.tag.rsplit('}',1)[-1]=='FIELD']
    rows=[[x.text for x in tr] for tr in raw.iter() if tr.tag.rsplit('}',1)[-1]=='TR']
    checks['raw_fields']=fields
    raw_by_id={str(int(r[fields.index('retained_source_id')])):r for r in rows}
    exact('raw_wire_join',len(raw_by_id)==4756 and all(str(v) in raw_by_id for v in ids))
    for fieldname in ['vari_best_class_name','host_galaxy_flag']:
        col=fields.index(fieldname)
        exact('raw_'+fieldname,all((raw_by_id[str(ids[i])][col] is None and r[fieldname] is None) or str(raw_by_id[str(ids[i])][col])==str(r[fieldname]) for i,r in enumerate(props)))
    with np.load(NPZ,allow_pickle=False) as z:
        source=z['source_id'];ra=z['ra'];dec=z['dec'];cov=z['covariance']
    order=np.argsort(source);exact('astrometric_id_alignment',np.array_equal(source[order],ids))
    ra,dec,C=ra[order],dec[order],cov[order]*1e6
    n,e,sp,X=geometry(np.deg2rad(ra),np.deg2rad(dec));W=white(C)
    ck('independent_whitening',mx(np.einsum('nai,nij,nbj->nab',W,C,W)-np.eye(2)),1e-10)
    ck('STF_orthonormal',mx(np.einsum('aij,bij->ab',S,S)-np.eye(5)),5e-13)
    ck('STF_trace',mx(np.trace(S,axis1=1,axis2=2)),5e-13)
    octant=((n>=0)*np.array([1,2,4])).sum(axis=1)
    domain=json.loads((CAND/'DOMAIN.json').read_text())
    exact('counts_host',domain['tag_host_counts']=={hh:{'AGN':int(np.sum((h==hh)&(t==1))),'ROW_NULL':int(np.sum((h==hh)&(t==0)))} for hh in HOSTS})
    exact('counts_octant',domain['tag_octant_counts']=={str(o):{'AGN':int(np.sum((octant==o)&(t==1))),'ROW_NULL':int(np.sum((octant==o)&(t==0)))} for o in range(8)})
    saved={};obs={}
    for model in ['M0','M1']:
        maps=dict(np.load(CAND/f'{model}_PRE_PM_MAPS.npz',allow_pickle=False));o=dict(np.load(CAND/f'{model}_OBSERVED.npz',allow_pickle=False));r=json.loads((CAND/f'{model}_PRE_PM_SUPPORT.json').read_text());j=json.loads((CAND/f'{model}_OBSERVED.json').read_text())
        F=design(sp,X,t,h,model);FW=np.einsum('nab,nbp->nap',W,F).reshape(-1,F.shape[-1]);p=F.shape[-1]
        ck(model+'_full_joint_map_identity',mx(maps['J']@FW-np.eye(p)),1e-8)
        ck(model+'_all13_target_map_identity',mx(maps['T']@FW-np.eye(p)[-13:]),1e-8)
        ck(model+'_physical_map',rel(maps['A'],np.einsum('kna,nab->knb',maps['T'].reshape(13,-1,2),W).reshape(13,-1)),1e-10)
        ck(model+'_joint_covariance',rel(maps['joint_covariance'],maps['J']@maps['J'].T),1e-10)
        ck(model+'_target_covariance',rel(maps['V'],maps['T']@maps['T'].T),1e-10)
        ck(model+'_all_covariance_cross_terms',rel(maps['V'],maps['joint_covariance'][-13:,-13:]),1e-10)
        ck(model+'_coefficient_tail_order',mx(o['coefficients'][-13:]-o['delta']),1e-10)
        for k,other in [('full_joint_covariance','joint_covariance'),('delta_covariance','V'),('target_map_whitened','T'),('joint_map_whitened','J')]:ck(model+'_saved_'+k,rel(o[k],maps[other]),1e-12)
        ck(model+'_tensor_E',mx(o['tensor_E']-np.einsum('k,kij->ij',o['delta'][3:8],S)),1e-12)
        ck(model+'_tensor_B',mx(o['tensor_B']-np.einsum('k,kij->ij',o['delta'][8:],S)),1e-12)
        ck(model+'_delta_json_order',mx(o['delta']-j['delta_FULL13']),1e-12)
        ck(model+'_coefficients_json_order',mx(o['coefficients']-j['coefficients']),1e-12)
        er,amp=sphere(o['delta']);ck(model+'_saved_sphere_quadrature',er,1e-11);ck(model+'_reported_sphere_RMS',abs(amp-j['full_sphere_RMS_microas_per_year']),1e-10)
        L=np.linalg.cholesky(maps['V']);q=solve_triangular(L,o['delta'],lower=True);ck(model+'_working_quadratic',abs(float(q@q)-j['working_quadratic_W']),1e-10)
        norms=np.linalg.norm(FW,axis=0);Fs=FW/norms;Q,_=qr(Fs[:,:-13],mode='economic');K=Fs[:,-13:]-Q@(Q.T@Fs[:,-13:]);u,sk,vt=np.linalg.svd(K,full_matrices=False)
        for title,arr in [('Z',Fs[:,:-13]),('augmented',Fs),('K',K)]:ck(model+'_spectrum_'+title,rel(np.linalg.svd(arr,compute_uv=False),np.asarray(r['singular_values_'+title])),1e-10)
        ck(model+'_scales',rel(norms,np.asarray(r['preprojection_scales'])),1e-12)
        exact(model+'_residual_floor',sk[-1]>1e-8*max(1,sk[0]))
        for tau in [9512*2**-52,1e-12,1e-10,1e-8]:
            sz=np.asarray(r['singular_values_Z']);sa=np.asarray(r['singular_values_augmented']);exact(model+'_rank_'+str(tau),np.sum(sz>tau*sz[0])==p-13 and np.sum(sa>tau*sa[0])==p and np.sum(sk>tau*sk[0])==13)
        lev=np.sum(u.reshape(-1,2,13)**2,axis=(1,2))/13
        ck(model+'_source_leverage',mx(lev-maps['source_leverage_share']),1e-10);ck(model+'_leverage_trace',abs(13*float(lev.sum())-13),1e-10)
        ck(model+'_octant_leverage',max(abs(float(lev[octant==k].sum())-r['octant_leverage_shares'][str(k)]) for k in range(8)),1e-10)
        saved[model]=maps;obs[model]=o
    cmp=dict(np.load(CAND/'COMPARISON.npz'));T0=saved['M0']['T'];T1=saved['M1']['T'];V00=T0@T0.T;V11=T1@T1.T;V01=T0@T1.T;Vdiff=(T1-T0)@(T1-T0).T
    for key,x in [('V00',V00),('V11',V11),('V01',V01),('V10',V01.T),('Vdiff',Vdiff),('T0',T0),('T1',T1)]:ck('comparison_'+key,rel(cmp[key],x),1e-10)
    ck('nested_cross_covariance_identity',rel(V01,V00),1e-10);ck('difference_covariance_cancellation_identity',np.linalg.norm(Vdiff-(V11+V00-V01-V01.T))/max(np.linalg.norm(V00),np.linalg.norm(V11)),1e-10)
    ck('saved_difference_vector',mx(cmp['delta_difference']-(obs['M1']['delta']-obs['M0']['delta'])),1e-12)
    # Only use author functions on synthetic inputs. No author main/toys/observed is called.
    author=runpy.run_path(str(CAND/'execute.py'),run_name='audit_import_only')
    z=np.tile(np.repeat([-np.sqrt(3/5),0,np.sqrt(3/5)],8),8);alpha=np.tile(np.arange(24)%8*np.pi/4,8);qh=np.tile(np.arange(24),8);hi=np.repeat(np.arange(4),48);tt=np.tile(np.repeat([0,1],24),4);hh=np.array(HOSTS)[hi]
    nn,ee,bb,xx=geometry(alpha,np.arcsin(z));s1=2+(hi+2*tt)/4;s2=3+(2*hi+tt)/4;rho=(-1.)**(qh+hi+tt)/4;CC=np.zeros((192,2,2));CC[:,0,0]=s1*s1;CC[:,1,1]=s2*s2;CC[:,0,1]=CC[:,1,0]=rho*s1*s2;WW=white(CC)
    ab,ax,ass,ae=author['basis'](nn);ck('toy_author_basis_spin',mx(ab-bb),5e-13);ck('toy_author_basis_FULL13',mx(ax-xx),5e-13);ck('toy_author_STF',mx(ass-S),5e-13)
    af={};ref={}
    for model in ['M0','M1']:
        ff=design(bb,xx,tt,hh,model);p=ff.shape[-1];coef=np.column_stack((np.eye(p),(-1.)**np.arange(p)*(np.arange(p)+1)/16));yy=np.stack([toyout(nn,ee,tt,hh,coef[:,k],model) for k in range(p+1)],axis=2)
        ck(model+'_toy_field_all_coefficients',mx(yy-np.einsum('nap,pq->naq',ff,coef)),5e-13)
        aa=author['factor'](ff,WW,model,False);exact(model+'_toy_eligible',aa['status']=='ELIGIBLE');jj,fw=fullqr(ff,WW);wy=np.einsum('nab,nbq->naq',WW,yy).reshape(384,p+1);chat=aa['J']@wy
        # Each column uses its own frozen amplitude denominator.
        errors=np.max(np.abs(chat-coef),axis=0)/np.maximum(1,np.max(np.abs(coef),axis=0));ck(model+'_toy_each32or80_plus_composite_recovery',float(errors.max()),1e-10)
        residuals=np.linalg.norm(wy-fw@chat,axis=0)/np.maximum(1,np.linalg.norm(wy,axis=0));ck(model+'_toy_each_probe_residual',float(residuals.max()),1e-11)
        ck(model+'_toy_QR_full_map',rel(aa['J'],jj),1e-10);ck(model+'_toy_QR_target_map',rel(aa['T'],jj[-13:]),1e-10);ck(model+'_toy_QR_joint_cov',rel(aa['joint_cov'],jj@jj.T),1e-10);ck(model+'_toy_QR_target_cov',rel(aa['V'],jj[-13:]@jj[-13:].T),1e-10)
        exact(model+'_toy_condition',aa['record']['condition_augmented']<=100 and aa['record']['condition_K']<=100)
        # Physical coefficient units: same geometric F, y_mas=y_micro/1000, C_mas=C_micro/1e6.
        am=author['factor'](ff,white(CC/1e6),model,False);wym=np.einsum('nab,nbq->naq',white(CC/1e6),yy/1000).reshape(384,p+1)
        ck(model+'_unit_fit_recovery',mx(am['J']@wym*1000-coef)/max(1,mx(coef)),1e-10);ck(model+'_unit_fit_joint_covariance',rel(am['joint_cov']*1e6,aa['joint_cov']),1e-10);ck(model+'_unit_fit_target_covariance',rel(am['V']*1e6,aa['V']),1e-10)
        theta=(qh%7)*np.pi/14;rr=np.zeros((192,2,2));rr[:,0,0]=rr[:,1,1]=np.cos(theta);rr[:,0,1]=-np.sin(theta);rr[:,1,0]=np.sin(theta)
        fr=np.einsum('nab,nbp->nap',rr,ff);cr=rr@CC@rr.transpose(0,2,1);wr=white(cr);ar=author['factor'](fr,wr,model,False);yr=np.einsum('nab,nbq->naq',rr,yy);wyr=np.einsum('nab,nbq->naq',wr,yr).reshape(384,p+1)
        ck(model+'_rotation_recovery',mx(ar['J']@wyr-coef)/max(1,mx(coef)),1e-10);ck(model+'_rotation_full_covariance',rel(ar['joint_cov'],aa['joint_cov']),1e-10)
        # Exact duplicate-removal has the identical reduced matrix and therefore identical maps.
        duplicated=np.concatenate((ff[:,:,:1],ff),axis=2);ad=author['factor'](duplicated[:,:,1:],WW,model,False)
        ck(model+'_duplicate_reduced_map',rel(ad['T'],aa['T']),1e-10);ck(model+'_duplicate_reduced_covariance',rel(ad['V'],aa['V']),1e-10)
        af[model]=aa;ref[model]=jj[-13:]
    ck('toy_QR_cross_covariance',rel(af['M0']['T']@af['M1']['T'].T,ref['M0']@ref['M1'].T),1e-10)
    ad=af['M1']['T']-af['M0']['T'];rd=ref['M1']-ref['M0'];ck('toy_QR_difference_covariance',np.linalg.norm(ad@ad.T-rd@rd.T)/max(np.linalg.norm(af['M0']['V']),np.linalg.norm(af['M1']['V'])),1e-10)
    no=design(bb,xx,np.zeros_like(tt),hh,'M0');exact('toy_zero_exposure',author['factor'](no,WW,'M0',False)['status']=='NO_EXPOSURE_SUPPORT')
    tc=(hi<2).astype(int);fc=design(bb,xx,tc,hh,'M1');exact('toy_within_host_alias',author['factor'](fc,WW,'M1',False)['status']!='ELIGIBLE')
    alias=np.concatenate((np.r_[np.eye(13),np.zeros((13,13))],np.r_[np.eye(13),1e-14*np.eye(13)]),axis=1).reshape(13,2,26);exact('toy_near_alias_floor',author['factor'](alias,np.tile(np.eye(2),(13,1,1)),'ALIAS',False)['status']!='ELIGIBLE')
    probes=np.column_stack((np.eye(13),(-1.)**np.arange(13)*(np.arange(13)+1)/16));ck('toy_sphere_ALL13_and_composite',max(sphere(probes[:,k])[0] for k in range(14)),1e-11)
    exact('one_thread',all(x['num_threads']==1 for x in threadpool_info()))
    exact('memory_under_2GiB',resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024<2147483648)
except Exception as e:
    failures.append('SCRIPT_EXCEPTION');checks['exception']={'type':type(e).__name__,'message':str(e),'traceback':traceback.format_exc()}
finally:
    elapsed=time.perf_counter()-START
    receipt={'packet_id':'429068ee8ebbdff0324a8fbc31f33d0d87ce35431c8350fc428a8d46876e49f2','task_id':'R25-GAIA-RELEASE-TAG-ASSOCIATION','input_identity':'sha256:00209480018bcb19f29c3c22a2d847c26560bcf950045978f10579967314e39f','candidate_identity':'sha256:3d2e96774c28cb5c3aa4d00757e022d61d1d696f50ff50e1b4dcdd31fc181793','review_arithmetic_seconds':elapsed,'author_charged_seconds':8.619179452070966,'cumulative_numeric_seconds':8.619179452070966+elapsed,'observed_fits_added':0,'proper_motion_member_accessed':False,'raw_first_failure':failures[0] if failures else None,'failures':failures,'checks':checks,'process_highwater_bytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'threadpools':threadpool_info(),'reviewer_requested':{'model':'gpt-6-astra','effort':'xhigh'},'observed_runtime':'UNKNOWN'}
    (OUT/'ARITHMETIC_FIRST.json').write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'seconds':elapsed,'failures':failures,'check_count':len(checks),'exception':checks.get('exception'),'peak_bytes':receipt['process_highwater_bytes']}))
