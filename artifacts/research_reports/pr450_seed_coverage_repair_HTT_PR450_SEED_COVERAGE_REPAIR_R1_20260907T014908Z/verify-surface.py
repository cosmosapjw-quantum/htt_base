from pathlib import Path
import hashlib, importlib.util, json, subprocess, sys
repo, out = map(Path, sys.argv[1:])
def git(*args):
    return subprocess.check_output(['git', '-C', str(repo), *args])
value = json.loads((out/'surface-a.json').read_bytes())
assert (out/'surface-a.json').read_bytes() == (out/'surface-b.json').read_bytes()
ref = '463f0999949bf8534c60ad7973b7342705c2e3d6'
path = 'docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json'
raw = git('show', ref+':'+path)
assert git('rev-parse', ref+':'+path).decode().strip() == '56af1713ef8c4718598e10012819d5ab62c6e37a'
digest = hashlib.sha256(raw).hexdigest()
assert digest == '8d92325a72b83dd96d1b78df071c47687426bfe1d10bfbe6768a3ab6f9bb244a'
assert value['source'] == {'mode':'GIT_OBJECT','commit':ref,'git_blob':'56af1713ef8c4718598e10012819d5ab62c6e37a','path':path,'sha256':digest}
source = json.loads(raw)
assert len(source['rows']) == 152
assert len(source['supplemental_scoped_candidates']) == 5
seed_path = 'docs/research_program/theory_promotion/closeout/REGISTERED_SURVIVOR_SEED.json'
seed = json.loads((repo/seed_path).read_bytes())
seed_by_id = {row['candidate_id']:row for row in seed['rows']}
output_by_id = {row['candidate_id']:row for row in value['candidates']}
assert len(value['candidates']) == len(output_by_id) == 37
assert output_by_id.keys() == seed_by_id.keys()
for key, row in output_by_id.items():
    for field in ('candidate_id','source_kind','survivor_class','parent_candidate_id','triage_disposition'):
        expected = seed_by_id[key].get(field) if field == 'parent_candidate_id' else seed_by_id[key][field]
        assert row[field] == expected, (key,field)
source_by_id = {r['claim_id']:r for r in source['rows']}
source_by_id.update({r['candidate_id']:r for r in source['supplemental_scoped_candidates']})
for key, row in output_by_id.items():
    original = source_by_id[key]
    assert row['source_statement_identity_sha256'] == original['statement_identity_sha256' if row['source_kind']=='SCOPED_CHILD' else 'source_statement_identity_sha256']
    assert row['evidence_refs'] == sorted(original.get('evidence_refs', []))
    assert row['source_terminal_state'] == original['scientific_terminal_state']
    assert row['observed_data_used'] is False
child = output_by_id['PR284_NEW:FINITE-REGISTERED-PATH']
assert child['parent_candidate_id'] == 'PILLAR_S:II-3.2'
assert child['triage_disposition'] == 'DEFERRED'
assert child['source_terminal_state'] == 'UNRESOLVED'
assert child['source_release_disposition'] == 'NOT_ELIGIBLE_CAS_CONFLICT'
relevant = set(output_by_id) | {r['parent_candidate_id'] for r in value['candidates'] if r['parent_candidate_id'] is not None}
expected_links = [{**link,'source':'PR405_SEMANTIC_LINK'} for link in source['semantic_links'] if relevant.intersection(link['claims'])]
actual_links = [link for link in value['relations'] if link['source']=='PR405_SEMANTIC_LINK']
assert sorted(expected_links,key=lambda r:json.dumps(r,sort_keys=True)) == sorted(actual_links,key=lambda r:json.dumps(r,sort_keys=True))
spec = importlib.util.spec_from_file_location('extractor', repo/'scripts/extract_theory_survivor_surface.py')
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
content_id = value['content_id']
without_id = {k:v for k,v in value.items() if k != 'content_id'}
assert content_id == 'sha256:'+hashlib.sha256(mod.canonical_bytes(without_id)).hexdigest()
assert mod.canonical_bytes(value) == (out/'surface-a.json').read_bytes()
assert value['unique_theorem_count'] is None
assert value['release_authority'] is False and value['observed_data_used'] is False
assert value['invariants']['truth_novelty_publication_unassigned'] is True
receipt=json.loads((out/'EXECUTION_RECEIPT.json').read_bytes())
assert receipt['surface_content_id'] == content_id
assert receipt['surface_sha256'] == hashlib.sha256((out/'surface-a.json').read_bytes()).hexdigest()
assert receipt['terminal']=='PASS_REGISTERED_SURVIVOR_SURFACE_TRIAGE'
result={'status':'PASS','matrix':value['source'],'matrix_bytes':len(raw),'source_universe':{'broad':152,'scoped':5,'total':157},'coverage':value['coverage'],'seed_rows_compared':37,'seed_fields_compared':['candidate_id','source_kind','survivor_class','parent_candidate_id','triage_disposition'],'source_statement_hashes_and_evidence_preserved':True,'semantic_links_preserved':len(actual_links),'pr284':child,'content_id':content_id,'surface_sha256':receipt['surface_sha256'],'replay_bytes_equal':True,'unique_theorem_count':None,'release_authority':False,'observed_data_used':False}
(out/'surface-verification.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':'PASS','coverage':value['coverage'],'content_id':content_id,'surface_sha256':receipt['surface_sha256']},sort_keys=True))
