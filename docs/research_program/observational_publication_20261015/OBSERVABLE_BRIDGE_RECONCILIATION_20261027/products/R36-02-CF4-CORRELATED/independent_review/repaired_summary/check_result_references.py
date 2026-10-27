"""Review-owned evidence for resolving inherited controls through the base manifest."""
from pathlib import Path
import hashlib,json
HERE=Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_summary_repair_independent_review')
CAND=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-02-CF4-CORRELATED/repair_01')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
manifest=read(CAND/'ARTIFACT_MANIFEST.json');base_path=Path(manifest['base_manifest_path']);base=read(base_path)
assert 'sha256:'+sha(base_path)==manifest['base_candidate_identity']
result=read(CAND/'RESULT.json')
records=[]
for field,relative,section,authority in [
 ('footprint_method_sensitivity','SENSITIVITY.json','new_files',manifest),
 ('controls','../CONTROLS.json','product_files',base),
 ('sample_covariance_uncertainty','../CONTROLS.json#sample_covariance_if_N64_p36','product_files',base),
]:
 filename,_,fragment=relative.partition('#');path=(CAND/filename).resolve()
 expected=authority[section][path.name]['sha256'];payload=read(path)
 assert sha(path)==expected
 if fragment:assert fragment in payload
 records.append({'field':field,'frozen_value':result[field],'explicit_resolution_from_result_directory':relative,'resolved_path':str(path),'sha256':expected,'read_and_hash_verified':True,'fragment':fragment,'fragment_exists':fragment in payload if fragment else None,'manifest_authority':str(CAND/'ARTIFACT_MANIFEST.json') if section=='new_files' else str(base_path)})
evidence={'schema':'htt.r36.review_result_reference_resolution/1','candidate_identity':'sha256:'+sha(CAND/'ARTIFACT_MANIFEST.json'),'purpose':'Review consumer explicitly resolves inherited parent controls via the pinned base manifest; does not edit or replace the frozen candidate. A downstream consumer can use this map, but bare document-relative controls references remain absent.','status':'SOURCE_IDENTITY_AND_READ_RESOLVED_WITH_EXPLICIT_MAP','references':records}
(HERE/'RESULT_REFERENCE_RESOLUTION.json').write_text(json.dumps(evidence,indent=2,sort_keys=True)+'\n')
print(json.dumps(evidence,indent=2))
