"""Minimal independent falsifier and bounded corrected-center forecast."""
from pathlib import Path
import importlib.util,json,numpy as np,math
OUT=Path(__file__).resolve().parent
P=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-10-GEOMETRY-IMAGE')
spec=importlib.util.spec_from_file_location('r36',P/'geometry_image.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
t=json.loads((P/'TABLE.json').read_text());records={};L=np.diag([.05]*7+[.01]*5);L[7,5]=.005
for name in ['I','flatVII0']:
 z=np.array(t['images'][name]['z0']);z[7:]=0
 J,H=m.derivatives(z);out=m.joint(z);rank=int(np.linalg.matrix_rank(J));b=[m.bounds(out,J,H,L,np.eye(10)[k]) for k in range(10)]
 records[name]={'contract_center':z.tolist(),'density':float(out[6]),'joint_rank':rank,'joint_singular_values':np.linalg.svd(J,compute_uv=False).tolist(),'energy_lower_bound':b[6]['center']-b[6]['radius'],'geometry_unchanged':bool(np.array_equal(out[:6],np.array(t['images'][name]['Y0'])[:6])),'geometry_J_unchanged':bool(np.array_equal(J[:6,:6],np.array(t['images'][name]['geometry_J'])))}
 # The exact derivative at I has only d(ebar)/dhbar=12.
 if name=='I':
  expect=np.zeros((10,12));expect[6,6]=12
  assert np.array_equal(J,expect)
assert records['I']['joint_rank']==1 and records['flatVII0']['joint_rank']==6
invalid=[]
for u in [1e-30,1e-26,1e-22]:
 try:m.frame(np.diag([1.,.7,1.1])*u,np.array([.3,0,0])*u,2*u,np.zeros((3,3)),12*u*u,np.zeros(3))
 except ValueError as e:
  assert str(e)=='INVALID_JACOBI';invalid.append({'u':u,'status':str(e)})
 else:raise AssertionError('invalid tiny Jacobi admitted')
report={'corrected_centers':records,'tiny_invalid_Jacobi':invalid,'meaning':'Frozen zero-shear I center has only energy-h first derivative, hence rank1. Saved rank3 is valid only at the different nonzero-shear center. Geometry image depends on N alone, so restoring S=0 preserves intrinsic tensors and matched-II/VII0 separation.'}
(OUT/'CENTER_COUNTEREXAMPLE.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
