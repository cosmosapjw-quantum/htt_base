from pathlib import Path
import importlib.util,sys,json,hashlib,platform
import numpy as np, healpy as hp
root=Path.cwd(); base=root/'docs/research_program/observational_publication_20261015/ADVERSARIAL_AUDIT_20261022/continuation'
spec=importlib.util.spec_from_file_location('r23_morphology',base/'cmb_counterpairs/morphology.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ex=json.loads((base/'cmb_counterpairs/EXPERIMENT.json').read_text()); native={e['product']:a for e,a in m.load_fields(ex) if e['lmax']==128}
rr=json.loads((base/'cmb_pilot/RESULT.json').read_text());payload=Path(rr['raw_processed_output']['path']);assert m.digest(payload)==rr['raw_processed_output']['sha256']
f=np.load(payload,allow_pickle=False)
def dense(p):
 a={}
 for l in (2,3,4):
  for k in range(l+1):
   z=complex(p[hp.Alm.getidx(4,l,k)]);a[l,k]=z
   if k:a[l,-k]=(-1)**k*z.conjugate()
 return a
def real(a):
 x=[]
 for l in (2,3,4):
  x.append(a[l,0].real)
  for k in range(1,l+1):x.extend([2**.5*a[l,k].real,2**.5*a[l,k].imag])
 return np.array(x)
def inverse(x):
 a={};i=0
 for l in (2,3,4):
  a[l,0]=complex(x[i]);i+=1
  for k in range(1,l+1):
   z=complex(x[i],x[i+1])/2**.5;i+=2;a[l,k]=z;a[l,-k]=(-1)**k*z.conjugate()
 return a
def feat(x):
 v=m.features(inverse(x));return {k:v[k] for k in ('J234','alignment23_squared','largest_axis_gaps','C_ell_K_CMB2','axis_status')}
rows=[]
for window in ('native',20,30):
 fields=native if window=='native' else {p:dense(f[f'{p}_L128_w{window}'][0]) for p in m.PRODUCTS}
 X={p:real(a) for p,a in fields.items()};x=X['full'];dh=(X['hm1']-X['hm2'])/2;do=(X['oe1']-X['oe2'])/2;D=np.stack([dh,do],axis=1)
 u,s,vt=np.linalg.svd(D,full_matrices=False);rank=int(sum(s>1e-10*s[0]));assert rank==2
 P=u[:,:rank]@u[:,:rank].T;removed=P@x;res=x-removed;coef=np.linalg.lstsq(D,x,rcond=1e-10)[0]
 perm=np.array([[0.,-2.],[3.,0.]]);uv,sv,vv=np.linalg.svd(D@perm,full_matrices=False);P2=uv@uv.T
 den=np.linalg.norm(x);nd=np.linalg.norm(D)
 checks={'projector_idempotence':float(np.linalg.norm(P@P-P)), 'orthogonality_relative':float(np.linalg.norm(D.T@res)/(nd*den)), 'reconstruction_relative':float(np.linalg.norm(x-(res+D@coef))/den),'basis_reparameterization_relative':float(np.linalg.norm((P2-P)@x)/den),'power_embedding_relative':float(abs(x@x-sum(abs(v)**2 for v in fields['full'].values()))/(x@x)),'half_sum_difference_HM_relative':float(np.linalg.norm((X['hm1']+X['hm2'])/2+dh-X['hm1'])/np.linalg.norm(X['hm1'])),'half_sum_difference_OE_relative':float(np.linalg.norm((X['oe1']+X['oe2'])/2+do-X['oe1'])/np.linalg.norm(X['oe1']))}
 assert max(checks.values())<1e-12
 path=[]
 for alpha in (0.,.25,.5,.75,1.):path.append(dict(alpha=alpha,features=feat(x-alpha*removed)))
 rows.append(dict(operator=window,rank=rank,singular_values_K_CMB=s.tolist(),singular_ratio=float(s[-1]/s[0]),difference_cosine=float(dh@do/np.linalg.norm(dh)/np.linalg.norm(do)),projection_coefficients_HM_OE=coef.tolist(),removed_power_fraction=float(removed@removed/(x@x)),full_norm_K_CMB=den,HM_difference_norm_K_CMB=float(np.linalg.norm(dh)),OE_difference_norm_K_CMB=float(np.linalg.norm(do)),full_minus_HM_sum_relative_norm=float(np.linalg.norm(x-(X['hm1']+X['hm2'])/2)/den),full_minus_OE_sum_relative_norm=float(np.linalg.norm(x-(X['oe1']+X['oe2'])/2)/den),path=path,validation=checks))
out=dict(task_id='R23-CMB',packet_id='cad530099dc22aecd453e2b11ebb437ac7e325ca772128a602bcaf2342f81d01',input_identity='sha256:6186378e8671b67dde9a54c55a8a40c2dafb8b24eb18a6934abf9d24276f14de',owner='obsstat',claim_tier='C0',status='DIAGNOSTIC_ONLY',scope='Observed full-map response to removing joint HM/OE difference span in ell2..4 processed E; not fitted physical noise or foreground',observed_skies=1,sky_id='actual-Planck-PR3-observed-sky',p_value=None,source_head_requested='a8e66da28461a415f5da3b3d609c482554d2dcd1',code_sha256=m.digest(base/'cmb_counterpairs/morphology.py'),experiment_sha256=m.digest(base/'cmb_counterpairs/EXPERIMENT.json'),A22_cached_payload_sha256=m.digest(payload),runtime=dict(python=platform.python_version(),numpy=np.__version__,healpy=hp.__version__,requested_model='gpt-6-astra',requested_effort='xhigh',observed_runtime='UNKNOWN'),rows=rows)
print(json.dumps(out,indent=2,allow_nan=False))
