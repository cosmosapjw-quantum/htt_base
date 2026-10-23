"""Independent saved-carrier and small-fixture audit; never traverse production pairs."""
import importlib.util,json,os,sys,time,resource
from pathlib import Path
import numpy as np
from scipy.stats import chi2
from threadpoolctl import threadpool_info
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
P=ROOT/'docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/gaia_pair_separation'
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_pair_blind_review')
RAW=Path('/mnt/extdrive/workdir/htt_open_data/r25_gaia_pair_separation/raw')
start=time.monotonic(); evidence={}; failures=[]
def ck(name,fun):
 try:
  value=fun(); evidence[name]={'pass':True,'evidence':value}
 except Exception as e:
  failures.append({'name':name,'error':repr(e)}); evidence[name]={'pass':False,'error':repr(e)}
def close(a,b,tol=1e-10):
 err=float(np.max(np.abs(np.asarray(a)-np.asarray(b)),initial=0)); assert err<=tol,(err,tol); return err
spec=importlib.util.spec_from_file_location('compute',P/'compute.py'); c=importlib.util.module_from_spec(spec);sys.modules['compute']=c;spec.loader.exec_module(c)
a=np.load(P/'arrays.npz',allow_pickle=False); v={k:a[k] for k in a.files};a.close()
r=json.loads((P/'RESULT.json').read_text()); ref=r['reference']; H=v['H'].reshape(117,-1); D=v['D'].reshape(117,13); d=v['d'].reshape(-1); C=v['C']; W=v['W']; z=v['z']; M=v['M']; Cd=v['Cd']
def carrier():
 expected={'H':(9,13,9512),'D':(9,13,13),'d':(9,13),'Cd':(117,117),'W':(88,117),'M':(88,13),'z':(88,), 'covariance_eigenvectors':(117,117),'covariance_eigenvalues':(117,),'source_id':(4756,),'X':(4756,2,13),'B':(4756,2,3),'C':(4756,2,2)}
 for k,shape in expected.items():assert v[k].shape==shape,(k,v[k].shape)
 assert all(np.isfinite(x).all() for x in v.values())
 with np.load(RAW/'full_carrier.npz',allow_pickle=False) as raw:
  for k in raw.files:assert np.array_equal(v[k],raw[k]),k
 assert np.array_equal(Cd,np.load(RAW/'covariance.npy'))
 with np.load(ROOT/'docs/observational_reboot_20261014/results/gaia_frame_v1/qualified_rows.npz',allow_pickle=False) as src:
  order=np.argsort(src['source_id']); assert np.array_equal(v['source_id'],src['source_id'][order]);assert len(np.unique(v['source_id']))==4756
  for k in ['ra','dec','octant']:assert np.array_equal(v[k],src[k][order])
  assert np.array_equal(v['y'],src['proper_motion'][order]*1000); assert np.array_equal(C,src['covariance'][order]*1e6)
 assert np.sum(v['counts'])==11307390; assert (v['counts']>0).all()
 assert np.array_equal(v['counts'],r['pair_counts_per_bin']);assert np.array_equal(v['source_counts'],r['source_counts_per_bin'])
 return {'shapes':{k:list(shape) for k,shape in expected.items()},'all_raw_carrier_arrays_exact':True,'units_conversion_exact':True,'pair_counts':v['counts'].tolist(),'all_bins_nonempty':True}
ck('source_and_complete_carrier',carrier)
def actual():
 errors={'d_Hy':close(d,H@v['y'].ravel(),1e-9),'D_HX':close(D,H@v['X'].reshape(-1,13),1e-9),'HB':close(H@v['B'].reshape(-1,3),0,1e-10)}
 # Independent covariance propagation through each source Cholesky factor.
 factors=np.linalg.cholesky(C); F=np.einsum('aij,ijk->aik',H.reshape(117,4756,2),factors).reshape(117,-1); independent_Cd=F@F.T
 errors['Cd_cholesky']=close(Cd,independent_Cd,1e-10)
 errors['C_symmetry']=close(C,C.swapaxes(1,2),1e-12)
 # Saved tangent geometry and all 13 model columns from independent Cartesian formulas.
 n,E=v['n'],v['E'];errors['tangent']=close(np.einsum('nia,ni->na',E,n),0,1e-12);errors['EtE']=close(np.einsum('nia,nib->nab',E,E),np.eye(2),1e-12)
 G=np.eye(3)[None,:,:]-n[:,:,None]*n[:,None,:]; S=v['STF']; Sn=np.einsum('kij,nj->nki',S,n)
 V=np.concatenate([G,np.swapaxes(Sn-n[:,None,:]*np.einsum('ni,nki->nk',n,Sn)[:,:,None],1,2),np.swapaxes(np.cross(n[:,None,:],Sn),1,2)],axis=2)
 errors['X_cartesian']=close(np.einsum('nia,nik->nak',E,V),v['X'],1e-12)
 errors['d_response_g']=close(v['d'][:,:3],r['typed_response_profile']['g_vector'],1e-12)
 for group,sl in [('E2_stf_tensor',slice(3,8)),('B2_stf_tensor',slice(8,13))]:
  tensor=np.einsum('bk,kij->bij',v['d'][:,sl],S);errors[group]=close(tensor,r['typed_response_profile'][group],1e-12);close(np.trace(tensor,axis1=1,axis2=2),0,1e-12)
 return {'max_abs_errors':errors,'min_source_covariance_eigenvalue':float(np.linalg.eigvalsh(C).min()),'cross_bin_shared_covariance_max_abs':float(np.max(np.abs(Cd[:13,13:])))}
ck('actual_operator_covariance_and_tensors',actual)
def reference():
 U=v['covariance_eigenvectors']; ev=v['covariance_eigenvalues']; retain=ev>1e-10*ev.max(); idx=np.flatnonzero(retain)
 assert np.array_equal(idx,ref['retained_indices']); assert len(idx)==88
 errs={'eigenorthogonality':close(U.T@U,np.eye(117),1e-12),'reconstruction':close((U*ev)@U.T,Cd,1e-10),'z':close(W@d,z,1e-12),'M':close(W@D,M,1e-12)}
 W0=U[:,retain].T/np.sqrt(ev[retain,None]); Wfixed=(np.eye(88)-0.5*(W0@Cd@W0.T-np.eye(88)))@W0;errs['declared_covariance_only_W']=close(Wfixed,W,1e-12)
 for k in ['W','M','z','covariance_eigenvalues','covariance_eigenvectors']:errs['json_'+k]=close(v[k],ref[k],1e-12)
 white=float(np.linalg.norm(W@Cd@W.T-np.eye(88),ord=2)); assert white<=1e-9
 fits={};Ps={}
 for name,p in [('E1',3),('full13',13)]:
  m=M[:,:p]; model=ref['models'][name]; Q,R=np.linalg.qr(m,mode='reduced'); beta=np.linalg.solve(R,Q.T@z); Pm=Q@Q.T; resid=z-Pm@z
  errs[name+'_representative']=close(beta,model['fit_representative'],1e-10);errs[name+'_profile']=close(m@beta,model['profile'],1e-12);errs[name+'_residual']=close(resid,model['residual'],1e-12)
  errs[name+'_unprojected_profile']=close((D[:,:p]@beta).reshape(9,13),model['unprojected_fit_profile'],1e-10);errs[name+'_unprojected_residual']=close((d-D[:,:p]@beta).reshape(9,13),model['unprojected_residual_profile'],1e-10)
  T=float(resid@resid);errs[name+'_T']=close(T,model['T'],1e-10)
  sv=np.linalg.svd(m,compute_uv=False);errs[name+'_sv']=close(sv,model['singular_values'],1e-12)
  fits[name]={'T':T,'numerical_rank':p,'smallest_singular_value':float(sv[-1]),'all_columns_retained':True};Ps[name]=Pm
 delta=fits['E1']['T']-fits['full13']['T']; assert delta>=-1e-10;errs['Delta']=close(delta,ref['Delta_E1_minus_full'],1e-10)
 nesting=float(np.linalg.norm((np.eye(88)-Ps['full13'])@Ps['E1'],2));assert nesting<1e-10
 ball=ref['projected_mean_ball'];assert ball['dimension']==88;errs['ball_center']=close(ball['center'],z,1e-12);errs['ball_radius2']=close(ball['radius_squared'],chi2.ppf(.95,88),1e-12)
 assert ref['tail_status']=='TAIL_UNRESOLVED_INCOMPLETE_IMAGE_CERTIFICATION';assert ball['status']=='NUMERICAL_WORKING_CHI_SQUARE_APPROXIMATION_ONLY'
 return {'max_abs_errors':errs,'whitening_spectral_residual':white,'models':fits,'nesting_spectral':nesting,'Delta':delta,'retained_modes':88,'discarded_modes':29,'discarded_smallest_eigenvalue':float(ev[~retain].min()),'full_tail_status':ref['tail_status'],'mean_ball_radius_squared':ball['radius_squared'],'model_coefficients_no_finite_confidence_region':True}
ck('fixed_projection_descriptive_fits',reference)
# Independently assemble pair rows on only eight deterministic fixture sources.
def fixtures():
 n,E=c.geometry(np.array([3.,4.,48.,119.,201.,294.,327.,183.]),np.array([-39.,-39.,21.,72.,-12.,44.,-61.,39.]));X,B=c.designs(n,E); rng=np.random.default_rng(251023);y=rng.normal(size=(8,2));Ctoy=np.array([[[2+i*.1,.2],[.2,1+i*.15]] for i in range(8)])
 pairs=[(i,j) for i in range(8) for j in range(i+1,8)]; L=[]; AA=[];bins=[];oracles=[]
 for i,j in pairs:
  row=np.zeros(16);row[2*i:2*i+2]=n[j]@E[i];row[2*j:2*j+2]=n[i]@E[j];L.append(row);ct=n[i]@n[j]
  an=np.concatenate([(1-ct)*(n[i]+n[j]),[2*n[i]@S@n[j]-ct*(n[i]@S@n[i]+n[j]@S@n[j]) for S in c.STF],[np.cross(n[i],n[j])@S@(n[j]-n[i]) for S in c.STF]])
  AA.append(an); theta=np.arctan2(np.linalg.norm(np.cross(n[i],n[j])),ct);bins.append(min(np.searchsorted(np.deg2rad(c.BINS),theta,side='right')-1,8))
 L=np.array(L);AA=np.array(AA);bins=np.array(bins);errs={'analytic_E1_E2_B2_all_pairs':close(AA,L@X.reshape(16,13),1e-12),'spin':close(L@B.reshape(16,3),0,1e-12)}
 hd,dd,yd,counts,_,near=c.accumulate(n,E,X,y); manual=np.zeros((9,13,16))
 for b in range(9):
  take=bins==b
  if take.any():manual[b]=AA[take].T@L[take]/take.sum()
 errs['independent_dense_H']=close(hd,manual,1e-12);errs['independent_d']=close(yd, (manual.reshape(117,16)@y.ravel()).reshape(9,13),1e-12);errs['independent_D']=close(dd,(manual.reshape(117,16)@X.reshape(16,13)).reshape(9,13,13),1e-12)
 covsrc=np.zeros((16,16))
 for i in range(8):covsrc[2*i:2*i+2,2*i:2*i+2]=Ctoy[i]
 cov=c.covariance(hd,Ctoy);errs['shared_source_Cd']=close(cov,manual.reshape(117,16)@covsrc@manual.reshape(117,16).T,1e-11)
 lists=[(i,np.array([j])) for i,j in pairs]; rng.shuffle(lists)
 shuffled=c.accumulate(n,E,X,y,pair_list=lists); dup=c.accumulate(n,E,X,y,pair_list=lists*3)
 for k,(a,b) in enumerate(zip([hd,dd,yd],shuffled[:3])):errs['pair_permutation_'+str(k)]=close(a,b,1e-12)
 for k,(a,b) in enumerate(zip([hd,dd,yd],dup[:3])):errs['duplication_'+str(k)]=close(a,b,1e-12)
 errs['duplication_covariance']=close(cov,c.covariance(dup[0],Ctoy),1e-11)
 axis=np.array([1.,2.,3.]);axis/=np.linalg.norm(axis);ang=.43;K=np.array([[0,-axis[2],axis[1]],[axis[2],0,-axis[0]],[-axis[1],axis[0],0]]);R=np.eye(3)+np.sin(ang)*K+(1-np.cos(ang))*(K@K)
 Q5=np.einsum('aij,bji->ab',c.STF,np.einsum('ik,bkl,jl->bij',R,c.STF,R));Q=np.zeros((13,13));Q[:3,:3]=R;Q[3:8,3:8]=Q5;Q[8:,8:]=Q5
 nr=n@R.T;Er=np.einsum('ij,njk->nik',R,E);Xr,Br=c.designs(nr,Er);hr,dr,yr,cr,_,_=c.accumulate(nr,Er,Xr,y)
 errs['rotation_X']=close(Xr@Q,X,1e-12);errs['rotation_H']=close(hr,np.einsum('ij,bjk->bik',Q,hd),1e-12);errs['rotation_D']=close(dr,np.einsum('ij,bjk,lk->bil',Q,dd,Q),1e-12);errs['rotation_d']=close(yr,yd@Q.T,1e-12);assert np.array_equal(cr,counts)
 # response != coefficient exact fixture; low covariance mode remains positive; full-image counterexample and fiber.
 ni=np.array([1.,0.,0.]);nj=np.array([0.,1.,0.]);e1=(ni+nj);assert np.array_equal(e1*(e1@ni),[1.,1.,0.]);assert np.linalg.eigvalsh(np.diag([1.,1e-14])).min()>0
 tiny=np.array([[1.,1.],[0.,1e-13]]);errs['small_model_counterexample']=close(tiny@np.array([-1e13,1e13]),[0.,1.],1e-12)
 assert np.array_equal(np.array([[1.,0.]])@np.array([0.,137.]),[0.]);assert near[1]==1
 return {'max_abs_errors':errs,'fixture_sources':8,'fixture_unique_pairs':28,'all_pair_duplication_factor':3,'antipodal_endpoint_count':int(near[1]),'actual_production_pair_traversals':0,'independent_Cd_shared_cross_bin_max_abs':float(np.max(np.abs(cov[:65,65:])))}
ck('independent_small_controls',fixtures)
def provided_tests():
 spec=importlib.util.spec_from_file_location('test_compute',P/'test_compute.py'); t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
 names=sorted(n for n in vars(t) if n.startswith('test_'))
 for n in names:getattr(t,n)()
 return {'test_functions':names,'passed':len(names),'invocation':'direct; no pytest cache or repository writes'}
ck('candidate_tests',provided_tests)
pools=threadpool_info();assert all(p['num_threads']==1 for p in pools),pools
result={'status':'PASS' if not failures else 'FAIL','evidence':evidence,'failures':failures,'threadpool_info':pools,'environment_threads':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']},'elapsed_seconds_internal':time.monotonic()-start,'max_rss_bytes_internal':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,'production_pair_traversals':0}
(OUT/'NUMERICAL_AUDIT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));sys.exit(bool(failures))
