from pathlib import Path
import hashlib,json,sys
from fractions import Fraction as F
import numpy as np
repo=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
review=Path(__file__).resolve().parent
rel=Path('docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-04-OPTICAL-JOINT/repair_04')
cand=repo/rel
fixture=review/'small_fixture'/rel
sys.path.insert(0,str(fixture))
from optical_joint import joint_test,KAPPA,lift_matrix
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=json.loads((cand/'RESULT.json').read_text()); b=json.loads((fixture/'RESULT.json').read_text())
comparison={'RESULT_semantically_equal':a==b,'TABLE_bytes_equal':(cand/'TABLE.csv').read_bytes()==(fixture/'TABLE.csv').read_bytes(),'RESULT_candidate_sha256':sha(cand/'RESULT.json'),'RESULT_replay_sha256':sha(fixture/'RESULT.json'),'TABLE_candidate_sha256':sha(cand/'TABLE.csv'),'TABLE_replay_sha256':sha(fixture/'TABLE.csv')}
assert comparison['RESULT_semantically_equal'] and comparison['TABLE_bytes_equal']
center=np.array([np.nextafter(.25,0),0.,0.]); radius=F(1,8); controls={}
for label,s in [('zero',np.zeros((3,3))),('nonzero',np.diag([.001,-.001,0.]))]:
    out=joint_test(np.zeros(7),s,center,.001,e_d=.125,d_max=.125)
    witness=[F.from_float(float(x)) for x in out['profiled_d']]
    direct2=sum((witness[i]-F.from_float(float(center[i])))**2 for i in range(3))
    physical2=sum(x*x for x in witness)
    assert direct2<=radius**2 and physical2<=radius**2
    assert out['compatible'] and out['certified_upper_bound']<.001
    k=KAPPA*lift_matrix(s)
    residual2=sum(sum(F.from_float(float(k[i,j]))*witness[j] for j in range(3))**2 for i in range(7))
    assert residual2<=F.from_float(.001)**2
    controls[label]={'out':out,'exact_direct_squared':str(direct2),'exact_physical_squared':str(physical2),'radius_squared':str(radius**2),'exact_response_residual_squared':str(residual2)}
exterior=np.array([np.nextafter(.25,np.inf),0,0])
assert sum(F.from_float(float(x))**2 for x in exterior)>(2*radius)**2
outer=joint_test(np.zeros(7),np.zeros((3,3)),exterior,.001,e_d=.125,d_max=.125)
assert outer['physical_set_empty'] and not outer['compatible']
controls['exterior']=outer
manifest=json.loads((cand/'ARTIFACT_MANIFEST.json').read_text())
source=repo/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/evidence/research/latest_results.json'
assert manifest['source_bindings'][str(source)]['sha256']==sha(source)==b['source']['p6_saved_results_sha256']
comparison['saved_P6_source_bound_by_candidate_manifest_and_RESULT']=True
root_input=repo/rel.parents[2]/'EVIDENCE_MANIFEST.json'
v=json.loads(root_input.read_text())
contract=repo/rel.parents[2]/'imports/cosmology/research/HUBBLE_PROTOCOL.json'
binding=next(x for x in v['files'] if x['path']==str(contract.relative_to(repo)))
assert sha(contract)==binding['sha256'] and contract.stat().st_size==binding['bytes']
comparison['HUBBLE_PROTOCOL_bound_by_frozen_input_manifest']=binding
(review/'FIXTURE_COMPARISON.json').write_text(json.dumps(comparison,indent=2)+'\n')
(review/'EXACT_WITNESS_CHECKS.json').write_text(json.dumps(controls,indent=2)+'\n')
initial=json.loads((review/'SOURCE_SEALS_INITIAL.json').read_text())
final=[]
for item in initial['checks']:
    p=Path(item['path']); match=sha(p)==item['sha256'] and p.stat().st_size==item['bytes']
    assert match,p
    final.append({'path':str(p),'sha256':sha(p),'unchanged':match})
assert sha(cand/'ARTIFACT_MANIFEST.json')==initial['manifest_sha256']
(review/'SOURCE_SEALS_FINAL.json').write_text(json.dumps({'manifest_sha256':initial['manifest_sha256'],'checks':final},indent=2)+'\n')
print(json.dumps({'RESULT_semantically_equal':True,'TABLE_bytes_equal':True,'zero_witness':controls['zero']['out']['profiled_d'],'nonzero_witness':controls['nonzero']['out']['profiled_d'],'nonzero_upper':controls['nonzero']['out']['certified_upper_bound'],'exterior_empty':True,'source_files_unchanged':len(final)},indent=2))
