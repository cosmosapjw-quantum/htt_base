import hashlib, importlib.util, itertools, json, sys
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from scipy.stats import chi2,ncx2
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=Path(__file__).resolve().parent
P=ROOT/'docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/products/R37-02-KINEMATICS'
CTL=OUT.parent
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
packet=read(CTL/'R37_NEXT_016_20261029.json')
assignment=json.loads(packet['spawn_args']['message'].split('Assignment:\n',1)[1])
(OUT/'assignment.json').write_text(json.dumps(assignment,indent=2)+'\n')
manifest=read(P/'ARTIFACT_MANIFEST.json');saved=read(P/'KINEMATIC_IMAGE_RESULT.json')
assert 'sha256:'+sha(P/'ARTIFACT_MANIFEST.json')==packet['candidate_identity']
checks={}
def hashcheck(p,expected):
 actual=sha(p);assert actual==expected,(str(p),actual,expected);return {'path':str(p),'sha256':actual,'match':True}
checks['assignment_sources']=[hashcheck(ROOT/i['path'],i['sha256']) for i in assignment['spec']['input_sources']]
checks['candidate_artifacts']=[hashcheck(P/i['path'],i['sha256']) for i in manifest['artifacts']]
assert all((P/i['path']).stat().st_size==i['size_bytes'] for i in manifest['artifacts'])
checks['consumed_sources']=[hashcheck(ROOT/i['path'],i['sha256']) for i in saved['inputs'].values()]
backup_root=Path(manifest['failed_candidate_backup']);bh=read(backup_root/'BACKUP_HASHES.json');backup=backup_root/'candidate'
checks['backup_files']=[hashcheck(backup/n,h) for n,h in bh['files_sha256'].items()]
assert 'sha256:'+sha(backup/'ARTIFACT_MANIFEST.json')==manifest['repair_of_candidate_identity']
oldmanifest=read(backup/'ARTIFACT_MANIFEST.json')
assert all(sha(backup/i['path'])==i['sha256'] for i in oldmanifest['artifacts'])
for item in assignment['history_refs']:
 hashcheck(Path(item['receipt']['path']),item['receipt']['sha256'])
checks['receipt_preservation']=hashcheck(P/'RAW_RECEIPT.json',manifest['recorded_original_receipt_sha256'])
assert sha(P/'RAW_RECEIPT.json')==sha(P/'RAW_RECEIPT_BEFORE_ENV_CORRECTION.json')==sha(backup/'RAW_RECEIPT.json')
cor=CTL/'R37_02_RECEIPT_ENV_CORRECTION_20261029';correction=read(cor/'CORRECTION.json')
checks['corrected_receipt']=hashcheck(cor/'CORRECTED_RAW_RECEIPT.json',correction['corrected_receipt_sha256'])
old=read(P/'RAW_RECEIPT.json');new=read(cor/'CORRECTED_RAW_RECEIPT.json')
checks['correction_changed_fields']=[k for k in set(old)|set(new) if old.get(k)!=new.get(k)]
assert set(checks['correction_changed_fields'])=={'timestamp_utc','environment','supersedes_receipt'}
checks['old_environment']=old['environment'];checks['corrected_environment']=new['environment']
import scipy,matplotlib,pytest
checks['current_environment']={'python':sys.version,'executable':sys.executable,'numpy':np.__version__,'scipy':scipy.__version__,'matplotlib':matplotlib.__version__,'pytest':pytest.__version__}
checks['candidate_identity']=packet['candidate_identity']
(OUT/'IDENTITY_AND_PROVENANCE_CHECKS.json').write_text(json.dumps(checks,indent=2)+'\n')
sp=importlib.util.spec_from_file_location('candidate',P/'kinematic_image.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);mod=m.load_optical_module()
# Recompute saved products by pure consumers only; never execute a producer main.
g=read(m.GAIA);prior=read(m.GAIA_PRE);pm=read(m.PM);opt=read(m.OPT);p6=read(m.P6)
computed={'gaia_E1_B1':m.gaia_product(g,prior),'pm_E2_STF5':m.pm_product(pm),'optical':m.optical_product(opt,p6,mod),'fixed_Q_sign_radius':m.chirality(mod)}
for k,v in computed.items():assert v==saved[k],k
assert computed['gaia_E1_B1']==read(P/'COMPRESSION_COMPARISON.json')
assert {'optical':computed['optical'],'fixed_Q_sign_radius':computed['fixed_Q_sign_radius']}==read(P/'OPTICAL_COMPATIBILITY.json')
# Independent nuisance normal-equation GLS, distinct from candidate Cholesky/SVD method.
def gls(y,j,c,n):
 ci=np.linalg.inv(c);w=ci-ci@n@np.linalg.solve(n.T@ci@n,n.T@ci);f=j.T@w@j
 th=np.linalg.solve(f,j.T@w@y);return th,np.linalg.inv(f),w
Y=np.array(g['full24_state_uasyr']);C=np.array(g['full24_cov_uasyr2']);z=np.array(g['depth_c_reported_z_centers'])
j=np.r_[np.zeros((18,6)),np.eye(6)];n=np.r_[np.eye(18),np.zeros((6,18))]
th,cov,w=gls(Y,j,C,n)
np.testing.assert_allclose(th,Y[18:],rtol=1e-11,atol=1e-11);np.testing.assert_allclose(cov,C[18:,18:],rtol=1e-11,atol=1e-11)
t=np.c_[np.eye(18),np.kron(z[:,None],np.eye(6))];y=t@Y;c=t@C@t.T;n18=np.tile(np.eye(6),(3,1));j1=np.kron(z[:,None],np.eye(6));j2=np.kron((z*z)[:,None],np.eye(6))
t1,c1,w1=gls(y,j1,c,n18);t2,c2,w2=gls(y,j2,c,n18)
lr=(y-j1@t1)@w1@(y-j1@t1)-(y-j2@t2)@w2@(y-j2@t2)
gs=saved['gaia_E1_B1'];assert abs(lr-gs['constrained_bin_depth']['full_deviance_difference'])<1e-8
np.testing.assert_allclose(t1,gs['constrained_bin_depth']['joint_signed_g_slope'],rtol=1e-10,atol=1e-10)
lost=np.linalg.norm(t@j-(t@n)@np.linalg.lstsq(t@n,t@j,rcond=None)[0]);assert lost<1e-12
l=np.linalg.cholesky(c);nn=np.linalg.solve(l,n18);proj=np.eye(18)-nn@np.linalg.pinv(nn);a=proj@np.linalg.solve(l,j1);b=proj@np.linalg.solve(l,j2);u,sv,_=np.linalg.svd(np.c_[a,b],full_matrices=False);rank=np.count_nonzero(sv>sv[0]*1e-11);u=u[:,:rank];assert rank==12
res=lambda x,h:np.linalg.norm(x-h@np.linalg.lstsq(h,x,rcond=None)[0])**2
errors=[]
for i in range(11):
 x=proj@np.cos(np.arange(18)+i/7);errors.append(abs(res(x,a)-res(x,b)-res(u.T@x,u.T@a)+res(u.T@x,u.T@b)))
assert max(errors)<1e-12
power_error=max(abs(v['scalar_energy_exact']-ncx2.sf(chi2.ppf(.95,6),6,v['mahalanobis_amplitude']**2)) for v in gs['free_bin_slope']['matched_power']);assert power_error<1e-14
assert gs['constrained_bin_depth']['joint_coverage']==prior['experiment2_constrained_bin_depth_family']['coverage95']
assert gs['constrained_bin_depth']['matched_power']==prior['experiment2_constrained_bin_depth_family']['power_at_mahalanobis_2p5']
num={'gaia':{'free_slope_error':float(np.max(abs(th-Y[18:]))),'free_covariance_error':float(np.max(abs(cov-C[18:,18:]))),'lost_slope_residual':float(lost),'independent_lr':float(lr),'lr_error':float(abs(lr-gs['constrained_bin_depth']['full_deviance_difference'])),'common_rank':int(rank),'eleven_deterministic_carrier_max_error':max(errors),'exact_power_error':power_error,'saved_MC_fields_exact':True},'pure_consumer_products_exactly_reproduced':list(computed)}
# Independent support via eigendecomposition, supporting points and unit transformation.
f=np.array(pm['gram']['primary_spin_glide6']['profile']['information']);ahat=np.array(pm['gram']['primary_spin_glide6']['joint']['selected_sample_full5_coefficients_uasyr']);ev,U=np.linalg.eigh(f);finv=(U/ev)@U.T;q=chi2.ppf(.95,5);qi=saved['pm_E2_STF5']['quotient_image']
np.testing.assert_allclose(ahat,qi['center_a_hat_uasyr'],atol=0)
np.testing.assert_allclose((U*np.sqrt(q/ev))@(U*np.sqrt(q/ev)).T,q*finv,rtol=1e-13,atol=1e-13)
err_support=[];err_units=[];err_attain=[]
for v in [*np.eye(5),np.array([.3,-.8,.2,1.1,-.4]),np.array([-2.,1.,.2,-.7,1.5]),np.zeros(5)]:
 for r in (0.,.5,1.,2.):
  expected=np.array([v@ahat-np.sqrt(q*(v@finv@v))-r*np.linalg.norm(v),v@ahat+np.sqrt(q*(v@finv@v))+r*np.linalg.norm(v)])
  actual=np.array(m.quotient_support(ahat,f,r,v,q));err_support.append(float(np.max(abs(expected-actual))))
  scaled=np.array(m.quotient_support(ahat*.001,f/1e-6,r*.001,v,q));err_units.append(float(np.max(abs(scaled-actual*.001))))
  if np.linalg.norm(v):
   delta=np.sqrt(q/(v@finv@v))*finv@v;ball=r*v/np.linalg.norm(v);err_attain.append(float(abs(v@(ahat+delta+ball)-actual[1])))
   assert abs(delta@f@delta-q)<1e-12
assert max(err_support)<1e-12 and max(err_units)<1e-14 and max(err_attain)<1e-12
np.testing.assert_allclose(qi['eigenmode_halfwidths_uasyr'],np.sqrt(q/ev)[None,:]+np.array(qi['radius_grid_uasyr'])[:,None],rtol=1e-14)
bo=np.zeros(5);bs=np.array([-1e-4,0,0,0,0]);s=np.zeros(5);endpoint=m.history_response(1.)@np.r_[(bo-bs)/1.,s];assert endpoint[0]==1e-4
hist=[]
for row in pm['history_images']:
 k=row['k'];H=np.c_[k*np.eye(5),-np.eye(5)];N=np.r_[np.eye(5),k*np.eye(5)]
 assert np.linalg.matrix_rank(H)==5 and np.linalg.matrix_rank(N)==5 and np.linalg.norm(H@N)==0
 np.testing.assert_allclose(H.T@f@H,row['information_10x10'],rtol=1e-13,atol=1e-12)
 q0=np.array([1.,-2.,3.,-4.,5.]);s0=k*q0-ahat;np.testing.assert_allclose(H@np.r_[q0,s0],ahat,rtol=1e-12,atol=1e-12)
 hist.append({'k':k,'rank':5,'null_dimension':5,'null_residual':float(np.linalg.norm(H@N))})
num['pm']={'endpoint_witness':endpoint.tolist(),'support_max_error':max(err_support),'support_attainment_max_error':max(err_attain),'uas_to_mas_max_error':max(err_units),'support_at_r0_least_informed':float(np.sqrt(q/ev[0])),'support_at_r1_least_informed':float(np.sqrt(q/ev[0])+1),'history':hist,'free_E2_nuisance_rank':saved['pm_E2_STF5']['nuisance']['free_E2_nuisance_rank']}
# Independent STF symmetrization, basis, covariance and ball-constrained optimum.
def stf3(x):
 sym=sum(x.transpose(p) for p in itertools.permutations(range(3)))/6;tr=np.einsum('iik->k',sym)
 return sym-(np.einsum('ij,k->ijk',np.eye(3),tr)+np.einsum('ik,j->ijk',np.eye(3),tr)+np.einsum('jk,i->ijk',np.eye(3),tr))/5
basis=[]
for ijk in np.ndindex(3,3,3):
 a0=np.zeros((3,3,3));a0[ijk]=1.;v=stf3(a0).ravel()
 for b0 in basis:v-=b0*(b0@v)
 if np.linalg.norm(v)>1e-13:basis.append(v/np.linalg.norm(v))
B3=np.array(basis).reshape(-1,3,3,3);S=np.array(p6['tensor']);kap=5/np.log(10.)
L=np.array([[np.sum(B*stf3(np.einsum('i,jk->ijk',e,S))) for e in np.eye(3)] for B in B3]);K=kap*L
os=saved['optical'];data=np.array(os['signed_summary_d3_O7']);dd=data[:3];oo=data[3:];co=np.array(os['full_summary_covariance_10x10']);A=np.c_[-K,np.eye(7)];cr=A@co@A.T
np.testing.assert_allclose(cr,os['residual_covariance_7x7'],rtol=1e-13,atol=1e-25)
q10=chi2.ppf(.95,10);ed=np.sqrt(q10*np.linalg.eigvalsh(co[:3,:3])[-1]);eo=np.sqrt(q10*np.linalg.eigvalsh(co[3:,3:])[-1]);assert np.linalg.norm(dd)+ed<.03
h=K.T@K;b=K.T@(oo-K@dd);fn=lambda lam:np.linalg.norm(np.linalg.solve(h+lam*np.eye(3),b))-ed
lam=brentq(fn,0,1.,xtol=1e-22);prof=dd+np.linalg.solve(h+lam*np.eye(3),b);rr=np.linalg.norm(oo-K@prof);expected_budget=np.sqrt(35/2)*kap*.08**3/(3*(1-.08))+eo
assert abs(rr-np.sqrt(os['minimum_compatibility']['residual_squared']))<2e-11
assert abs(expected_budget-os['shared_budget']['total'])<1e-15
inv=np.linalg.lstsq(K,oo,rcond=None)[0];perp=oo-K@inv;assert np.linalg.matrix_rank(L)==3
small=[]
for scale in (0.,1.,1e-8,1e-160,1e-200,1e-300):
 got=m.safe_joint_test(mod,oo,scale*S,dd,expected_budget,e_d=ed,d_max=.03)
 if scale==0:assert got['branch']=='S_ZERO_DIRECT_MEMBERSHIP' and got['inverse_d'] is None
 else:
  assert got['branch']=='INVERTIBLE_S' and np.isfinite(got['inverse_d']).all()
  np.testing.assert_allclose(np.array(got['inverse_d'])*scale,inv,rtol=2e-13,atol=1e-15)
  np.testing.assert_allclose(got['perpendicular_squared']+got['parallel_squared'],got['residual_squared'],rtol=1e-12,atol=1e-25)
 small.append({'scale':scale,'branch':got['branch'],'maxabs_inverse':float(np.max(np.abs(got['inverse_d']))) if scale else None,'compatible':got['compatible']})
try:m.safe_joint_test(mod,oo,1e-320*S,dd,expected_budget,e_d=0)
except ValueError as exc:assert 'nonrepresentable' in str(exc);rejection=str(exc)
else:raise AssertionError('unrepresentable inverse not rejected')
num['optical']={'q95_10':float(q10),'direct_radius':float(ed),'octupole_radius':float(eo),'covariance_error':float(np.max(abs(cr-np.array(os['residual_covariance_7x7'])))),'shared_budget':float(expected_budget),'independent_profile_residual':float(rr),'profile_residual_difference':float(abs(rr-np.sqrt(os['minimum_compatibility']['residual_squared']))),'perpendicular_dimension':4,'small_S':small,'unrepresentable_rejection':rejection,'guard_scope':'R37 consumer, fixed default KAPPA, saved finite o/d and STF tensor with tested scalar rescalings; no general optical API validation claimed'}
ch=saved['fixed_Q_sign_radius'];Q=np.array(ch['Q']);O=np.array(ch['O_full_3x3x3']);CQ=np.array([np.einsum('ijk,jk->i',B,Q) for B in B3]).T;vv=np.einsum('ijk,jk->i',O,Q);M=CQ@CQ.T;rad=np.abs(vv)/np.linalg.norm(CQ,axis=1);idx=int(np.argmin(rad));delta=-vv[idx]/M[idx,idx]*np.einsum('a,aijk->ijk',CQ[idx],B3);vb=np.einsum('ijk,jk->i',O+delta,Q)
assert abs(min(rad)-1/np.sqrt(3))<1e-14 and abs(np.linalg.norm(delta)-min(rad))<1e-14
chi=lambda v:np.linalg.det(np.c_[v,Q@v,Q@Q@v])
assert abs(chi(vv))>1e-5 and abs(chi(vb))<1e-15
num['chirality']={'Gram_identity_error':float(np.max(abs(M-(np.sum(Q*Q)*np.eye(3)/3+2*Q@Q/5)))),'radius':float(min(rad)),'attaining_norm':float(np.linalg.norm(delta)),'initial_chi':float(chi(vv)),'boundary_chi':float(chi(vb)),'scope':'fixed simple-spectrum Q, nonzero chi, ambient STF3; no new CAS or uncertain-Q admission'}
# Render existing vectors; all outputs outside repository.
import fitz
renders=[]
for name in ('optical_joint_compatibility','physical_region_vs_remainder','GLS_tensor_scalar_comparison','chirality_radius'):
 doc=fitz.open(P/(name+'.pdf'));assert len(doc)==1
 doc[0].get_pixmap(matrix=fitz.Matrix(1.6,1.6)).save(OUT/(name+'.png'))
 (OUT/(name+'.txt')).write_text(doc[0].get_text())
 renders.append({'file':name+'.pdf','pages':len(doc),'raster_images':len(doc[0].get_images()),'sha256':sha(P/(name+'.pdf'))})
num['pdf_renders']=renders
(OUT/'INDEPENDENT_NUMERICS.json').write_text(json.dumps(num,indent=2)+'\n')
print(json.dumps({'source_checks':len(checks['assignment_sources']),'artifact_checks':len(checks['candidate_artifacts']),'backup_files':len(checks['backup_files']),'numerics':num},indent=2))
