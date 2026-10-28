"""SYNTHETIC_UNIT_FIXTURE: independent prepared consumer probes, no real qualification."""
import copy, hashlib, importlib.util, json, math, pathlib, shutil, sys
import pytest
from scipy.stats import binom
ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'code'))
import assemble as a
import test_assemble as fixture
EDITOR_SOURCE = pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_manuscript_framing/EDITOR_CONTRACT.json')
SCIENCE_SOURCE = pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_contract_preparation/IMPLEMENTATION_CONTRACT.json')

def dump(p, data):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2) + '\n')
    return p

def export_fixture(root):
    root.mkdir(parents=True)
    (root/'.SYNTHETIC_UNIT_FIXTURE').write_text('Synthetic export; no actual source qualification.\n')
    editor = {'source_task':'SYNTHETIC_UNIT_FIXTURE_TASK','source_packet_id':'SYNTHETIC_SOURCE_PACKET','source_input_identity':'SYNTHETIC_INPUT','provenance':{'author':'SYNTHETIC_FRAMER'}}
    roles = {k:k for k in ['result','observed_row','mask_response_json','mask_response_npz','raw_input_inventory','observed_replay_parity','observed_replay_run','scientific_contract','source_scope_note']}
    roles['mc_rows'] = [f'mc_{i:04d}' for i in range(300,400)]
    roles['source_receipts'] = ['synthetic_receipt']
    keys = list(roles)[:-2] + roles['mc_rows'] + roles['source_receipts']
    files = {}; entries = {}
    for key in keys:
        name = 'COMMANDER_RESULT.json' if key=='result' else key + ('.npz' if key=='mask_response_npz' else '.json')
        p = root/'payload'/name
        p.parent.mkdir(exist_ok=True)
        if key=='scientific_contract':shutil.copyfile(SCIENCE_SOURCE,p)
        elif key=='mask_response_npz':p.write_bytes(b'SYNTHETIC_UNIT_FIXTURE_ONLY')
        else:dump(p, {'fixture_only':'SYNTHETIC_UNIT_FIXTURE','key':key})
        entries[key] = {'path':'/SYNTHETIC_UNIT_FIXTURE_SOURCE/'+name, 'sha256':a.sha(p), 'bytes':p.stat().st_size}
        files[key] = dict(entries[key],manifest_section='candidate_files',manifest_key=key,original_path=entries[key]['path'],relative_path=str(p.relative_to(root)))
        files[key].pop('path')
    manifest = {k:'SYNTHETIC_UNIT_FIXTURE' for k in ['schema','owner','scope','claim_tier','transfer_source','qualification_status']}
    manifest.update(task_id=editor['source_task'],packet_id=editor['source_packet_id'],input_identity=editor['source_input_identity'],agent_id='SYNTHETIC_AUTHOR',acceptance_met=False,qualified_products=[],source_bindings={},candidate_files=entries)
    mp=dump(root/'ARTIFACT_MANIFEST.json',manifest)
    for key,role in [('row','observed_row'),('author_parity_receipt','observed_replay_parity'),('run_receipt','observed_replay_run')]:
        editor.setdefault('selected_observed_replay',{})[key]={'sha256':files[role]['sha256']}
    index={'schema':'htt.r36.pr4_morphology_publication_export/1','source_candidate_identity':'sha256:'+a.sha(mp),'source_manifest':{'relative_path':mp.name,'sha256':a.sha(mp),'bytes':mp.stat().st_size},'files':files,'roles':roles,'raw_inputs_policy':'METADATA_AND_REVIEWED_RECEIPTS_ONLY'}
    ip=dump(root/'PUBLICATION_EXPORT.json',index)
    raw=dump(root/'SYNTHETIC_RAW_RECEIPT.json',{'fixture_only':'SYNTHETIC_UNIT_FIXTURE'})
    binding={'status':'QUALIFIED_FINAL_SOURCE_BOUND','fixture_only':'SYNTHETIC_UNIT_FIXTURE','source_candidate_identity':'sha256:'+a.sha(mp),'source_candidate_manifest_path':str(mp),'source_candidate_manifest_sha256':a.sha(mp),'publication_export_path':str(ip),'publication_export_sha256':a.sha(ip),'source_packet_id':editor['source_packet_id'],'review_packet_id':'SYNTHETIC_DISTINCT_REVIEW_PACKET','formal_raw_receipt_path':str(raw),'formal_raw_receipt_sha256':a.sha(raw),'independent_scientific_reviewer_identity':'SYNTHETIC_INDEPENDENT_REVIEWER'}
    for stem,key in [('qualified_result','result'),('qualified_observed_replay_row','observed_row'),('replay_comparison_receipt','observed_replay_parity')]:
        binding[stem+'_path']=str(root/files[key]['relative_path']);binding[stem+'_sha256']=files[key]['sha256']
    formal={'fixture_only':'SYNTHETIC_UNIT_FIXTURE','task_id':editor['source_task'],'source_packet_id':editor['source_packet_id'],'input_identity':editor['source_input_identity'],'outcome':'success','acceptance_met':True,'review_status':'PASS_SCOPED_CONDITIONAL','substantive_failure':False,'candidate_identity':binding['source_candidate_identity'],'publication_export_identity':'sha256:'+binding['publication_export_sha256'],'packet_id':binding['review_packet_id'],'qualified_products':['pr4_morphology_result'],'agent_id':binding['independent_scientific_reviewer_identity'],'findings':[],'raw_receipt_sha256':a.sha(raw)}
    return binding,editor,manifest,formal

def test_cp_all_counts_binomial_inversion():
    for k in range(101):
        lo,hi=a.cp_interval(k)
        assert (lo==0 if k==0 else abs(binom.sf(k-1,100,lo)-.025)<1e-12)
        assert (hi==1 if k==100 else abs(binom.cdf(k,100,hi)-.025)<1e-12)
        assert (hi-lo)/2<=.105
    assert a.rank_summary(.2,[.2]*100)['p_rank']==1
    assert a.rank_summary(.2,[.1]*100)['p_rank']==1/101

def test_distinct_review_packet_accepted_only_for_bound_identity(tmp_path):
    b,e,m,f=export_fixture(tmp_path/'export')
    a.validate_export(b,e);a.formal_source_gate(b,e,m,f)
    for key in ['packet_id','source_packet_id','candidate_identity','publication_export_identity','input_identity','task_id']:
        bad=copy.deepcopy(f);bad[key]='SYNTHETIC_WRONG_IDENTITY'
        with pytest.raises(ValueError):a.formal_source_gate(b,e,m,bad)
    for key,value in [('acceptance_met',1),('substantive_failure',0),('qualified_products',['other']),('agent_id','SYNTHETIC_AUTHOR'),('raw_receipt_sha256','0'*64)]:
        bad=copy.deepcopy(f);bad[key]=value
        with pytest.raises(ValueError):a.formal_source_gate(b,e,m,bad)

def test_manifest_byte_and_export_identity(tmp_path):
    b,e,m,f=export_fixture(tmp_path/'export')
    a.validate_export(b,e)
    p=pathlib.Path(b['source_candidate_manifest_path']);p.write_text(json.dumps(m))
    with pytest.raises(ValueError,match='exact manifest bytes'):a.validate_export(b,e)
    b,e,m,f=export_fixture(tmp_path/'export2')
    p=pathlib.Path(b['publication_export_path']);p.write_text(p.read_text()+'\n')
    with pytest.raises(ValueError,match='index identity'):a.validate_export(b,e)

def test_export_relocation_preserves_payload_bytes(tmp_path):
    old=tmp_path/'old';new=tmp_path/'new';b,e,m,f=export_fixture(old)
    before={str(p.relative_to(old)):a.sha(p) for p in old.rglob('*') if p.is_file()}
    shutil.copytree(old,new)
    b={k:(str(new/pathlib.Path(v).relative_to(old)) if k.endswith('_path') else v) for k,v in b.items()}
    a.validate_export(b,e);a.formal_source_gate(b,e,m,f)
    assert before=={str(p.relative_to(new)):a.sha(p) for p in new.rglob('*') if p.is_file()}

def test_payload_copy_mutation_rejects(tmp_path):
    b,e,m,f=export_fixture(tmp_path/'export')
    pathlib.Path(b['qualified_result_path']).write_text('{}\n')
    with pytest.raises(ValueError,match='payload byte identity'):a.validate_export(b,e)

def test_optional_nonempty_review_stays_pending(tmp_path):
    b,e,m,f=export_fixture(tmp_path/'export');f['findings']=[{'fixture_only':'SYNTHETIC_UNIT_FIXTURE','severity':'nonblocking','resolution':'example_shape_not_a_real_reviewer_format'}]
    with pytest.raises(a.PendingSourceQualification,match='ADAPTER_PENDING'):a.formal_source_gate(b,e,m,f)

def test_independent_response_coordinate_oracle():
    r=fixture.synthetic_response();d=a.response_data(r);expected=[]
    for prefix,field in [('E',a.FIELDS[0]),('B',a.FIELDS[1])]:
        for ell in [2,3,4]:
            expected.append([col[field][f'{ell},0'][0] for col in r['columns']])
            for m in range(1,ell+1):
                expected.extend([[math.sqrt(2)*col[field][f'{ell},{m}'][0] for col in r['columns']],[-math.sqrt(2)*col[field][f'{ell},{m}'][1] for col in r['columns']]])
    assert d['values']==expected and len(expected)==42
    r['columns'].pop()
    with pytest.raises(ValueError):a.response_data(r)

def test_actual_pending_binding_rejects_without_output():
    b=a.strict_json(ROOT/'code/FINAL_SOURCE_BINDING.json')
    with pytest.raises(a.PendingSourceQualification):a.ensure_final_adapter(b)
