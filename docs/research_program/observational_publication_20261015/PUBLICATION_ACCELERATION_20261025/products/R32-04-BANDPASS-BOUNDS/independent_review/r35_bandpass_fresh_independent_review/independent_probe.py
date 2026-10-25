import ast,datetime,hashlib,json,math,sys,time
from pathlib import Path
import numpy as np
import scipy
start=time.monotonic()
root=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
p=root/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025'
cand=p/'products/R32-04-BANDPASS-BOUNDS'
out=Path('/mnt/extdrive/workdir/htt_open_data/r35_bandpass_fresh_independent_review')
source=json.loads((p/'evidence/R31/report/data/RESULT.json').read_text())
result=json.loads((cand/'RESULT.json').read_text())
d=np.asarray(result['common_reference_column_scales'])
report={'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'python':sys.version,'numpy':np.__version__,'scipy':scipy.__version__,'candidate_manifest_sha256':hashlib.sha256((cand/'ARTIFACT_MANIFEST.json').read_bytes()).hexdigest(),'inputs':{},'branches':{}}
for file in [p/'evidence/R31/report/data/RESULT.json',p/'evidence/R31/scientific/framing/SPECTRAL_ONLY_CONTRACT.md',Path('/mnt/extdrive/workdir/htt_open_data/r35_h03_bandpass_contract_intake/CONTRACT.md')]:
 report['inputs'][str(file)]=hashlib.sha256(file.read_bytes()).hexdigest()
for name,src in source['branches'].items():
 F=np.asarray(src['F2']['matrix_7xk']);a=np.asarray(src['cmb_unity_responses']);b=result['branches'][name]
 br={}
 for metric,sc in [('common_reference',d),('raw_identity',np.ones(9))]:
  G=F/sc
  u,s,vt=np.linalg.svd(G,full_matrices=True)
  coeff=(vt[:7].T@((u.T@a)/s))/sc
  c=np.asarray(b[metric]['minimum_coefficients_c9'])
  ell=np.linalg.norm(sc*coeff)
  N=np.asarray(b[metric]['coefficient_nullspace_directions_2x9']).T
  V=np.asarray(b[metric]['whitened_right_singular_directions_7x9'])
  projections=np.asarray(b[metric]['CMB_left_projections_7'])
  reconstructed_c=(V.T@(projections/np.asarray(b[metric]['singular_values_7'])))/sc
  br[metric]={'ell_independent_svd':float(ell),'ell_vs_stored_relative':float(abs(ell-b[metric]['minimum_budget_ell'])/ell),'c_vs_stored_relative':float(np.linalg.norm(c-coeff)/np.linalg.norm(coeff)),'Fc_exported_relative':float(np.linalg.norm(F@c-a)/np.linalg.norm(a)),'exported_nullspace_F_N_relative':float(np.linalg.norm(F@N)/np.linalg.norm(F)),'exported_nullspace_G_N_relative':float(np.linalg.norm(G@N)/np.linalg.norm(G)),'nullspace_after_unwhitening_F_N_relative':float(np.linalg.norm(F@(N/sc[:,None]))/np.linalg.norm(F)),'singular_reconstruction_c_relative':float(np.linalg.norm(reconstructed_c-c)/np.linalg.norm(c)),'sigma_min':float(s[-1]),'condition_F_Mhalf':float(s[0]/s[-1]),'positive_norm_increment_check':float(np.linalg.norm(sc*(c+vt[-1]/sc))**2-np.linalg.norm(sc*c)**2)}
  if metric=='common_reference':
   # SVD square-root inverse; independent of producer K Cholesky/inverse.
   H=(u/s).T
   Kinv=H.T@H
   z=Kinv@a
   ell2=float(np.linalg.norm(H@a)**2)
   with np.load(cand/'report/generated'/f'{name}_full24.npz') as zf:
    arrays={k:zf[k] for k in zf.files}
   Y=arrays['synthetic_Y'];s0=Y.T@z/ell2;J0=float(np.linalg.norm(H@(Y-a[:,None]*s0))**2)
   radius=.5;rho=math.sqrt(J0+ell2*radius**2)
   U=arrays['synthetic_boundary_U'];sb=arrays['synthetic_boundary_s']
   A=np.kron(a[:,None],np.eye(24));B=np.kron(F,np.eye(24));C=np.kron(c[:,None],np.eye(24))
   br['full24']={'source_F_exact':bool(np.array_equal(F,arrays['F'])),'source_a_exact':bool(np.array_equal(a,arrays['a'])),'A_exact':bool(np.array_equal(A,arrays['A'])),'B_exact':bool(np.array_equal(B,arrays['B'])),'C_exact':bool(np.array_equal(C,arrays['C'])),'all24_relative':float(np.max(np.linalg.norm(A-B@arrays['C'],axis=0)/np.linalg.norm(A,axis=0))),'generic_J0_independent':J0,'generic_center_error':float(np.linalg.norm(s0-arrays['synthetic_center'])),'generic_U_reconstruction_relative':float(np.linalg.norm(Y-np.outer(a,sb)-F@U)/np.linalg.norm(Y)),'generic_boundary_budget_relative_error':float(abs(np.linalg.norm(d[:,None]*U)-rho)/rho),'one_budget':float(np.linalg.norm(d[:,None]*arrays['one_U'])),'pair1_budget':float(np.linalg.norm(d[:,None]*arrays['pair_U1'])),'pair2_budget':float(np.linalg.norm(d[:,None]*arrays['pair_U2'])),'center_operator_relative':float(np.linalg.norm(arrays['full24_center_linear_operator']@Y.ravel()-s0)/np.linalg.norm(s0)),'shape_error':float(np.linalg.norm(arrays['full24_shape_matrix']-ell2*np.eye(24))/ell2)}
 report['branches'][name]=br
# Inspect the actual pure identified helper without executing the consumer/main or imports.
tree=ast.parse((cand/'consumer.py').read_text())
helper=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='identified')
ns={'np':np,'math':math,'require':lambda c,m: None if c else (_ for _ in ()).throw(AssertionError(m))}
exec(compile(ast.Module(body=[helper],type_ignores=[]),str(cand/'consumer.py'),'exec'),ns)
name='A_BT_1e-07';F=np.asarray(source['branches'][name]['F2']['matrix_7xk']);a=np.ones(7)
G=F/d;u,s,vt=np.linalg.svd(G,full_matrices=False);H=(u/s).T;Kinv=H.T@H;z=Kinv@a;ell2=float(a@z)
sol={'Kinv':Kinv,'z':z,'ell2':ell2,'ell':math.sqrt(ell2)}
with np.load(cand/'report/generated'/f'{name}_full24.npz') as arrays:Y=arrays['synthetic_Y'].copy()
base=ns['identified'](Y,F,a,d,sol,0);J0=base['J0'];probe=[]
for scale in [1.,1e-6]:
 for label,rho in [('empty',.5*math.sqrt(J0)),('ball',math.sqrt(J0+ell2*.5**2))]:
  actual=ns['identified'](scale*Y,F,a,d,sol,scale*rho)
  probe.append({'case':label,'amplitude_scale':scale,'rho':scale*rho,'actual_status':actual['status'],'actual_radius':actual['radius'],'J0':actual['J0'],'gap':(scale*rho)**2-actual['J0'],'expected_status':label.upper(),'expected_radius':None if label=='empty' else .5*scale})
negative=ns['identified'](np.zeros((7,24)),F,a,d,sol,-1.)
report['boundary_probe']=probe
report['negative_rho_probe']={'rho':-1,'actual_status':negative['status'],'radius':negative['radius'],'domain_note':'rho is a nonnegative radius; helper currently omits its domain guard'}
report['elapsed_seconds']=time.monotonic()-start
(out/'raw/independent_probe.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({'manifest':report['candidate_manifest_sha256'],'branches':report['branches'],'boundary_probe':probe,'negative_rho_probe':report['negative_rho_probe'],'elapsed_seconds':report['elapsed_seconds']},indent=2))
