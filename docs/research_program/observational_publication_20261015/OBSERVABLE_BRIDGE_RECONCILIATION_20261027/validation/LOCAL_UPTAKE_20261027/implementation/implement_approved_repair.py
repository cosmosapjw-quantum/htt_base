import os
os.environ['PYTHONDONTWRITEBYTECODE']='1';os.environ['GIT_OPTIONAL_LOCKS']='0'
import sys,csv,io,decimal,difflib,copy
sys.path.insert(0,'/mnt/extdrive/workdir/htt_open_data/r35_p5_reviewed_publication')
import publish
from publish import *
O=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_intake_serialization_repair');publish.O=O;contractpath=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_blind_intake_binding_review/REPAIR_CONTRACT.json');assert sha(contractpath)=='019ad3396b0b732bf40149d69ddf84fc9652f28f3a48288282e542ca424af7b9';c=json.loads(contractpath.read_text());REL='docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027';D=R/REL;T=REL+'/imports/v15/cas/response_frontier.csv';E=REL+'/EVIDENCE_MANIFEST.json';F=REL+'/FRONTIER.json';H=REL+'/HANDOFF_CURRENT_SESSION.md';L=REL+'/DELIVERY_MANIFEST.json'
assert run('REPAIR_HEAD_BEFORE',['git','rev-parse','HEAD']).decode().strip()==c['base']['HEAD'];assert run('REPAIR_BRANCH_BEFORE',['git','branch','--show-current']).decode().strip()==c['base']['branch'];assert run('REPAIR_ORIGIN_BEFORE',['git','remote','get-url','origin']).decode().strip()==c['base']['origin'];statusbefore=run('REPAIR_STATUS_BEFORE',['git','status','--porcelain=v1','-z']);assert not run('REPAIR_INDEX_BEFORE',['git','diff','--cached','--name-only','-z']);out('REPAIR_PROTECTION_BEFORE.json',protection())
indexpath=pathlib.Path(subprocess.check_output(['git','rev-parse','--git-path','index'],cwd=R).decode().strip());indexpath=indexpath if indexpath.is_absolute() else R/indexpath;indexbefore=indexpath.read_bytes();statepath=R/'.agent-harness/runtime/r23-continuous/STATE.json';statebefore=statepath.read_bytes();state=json.loads(statebefore);assert len(statebefore)==c['state_at_review']['bytes'] and hashlib.sha256(statebefore).hexdigest()==c['state_at_review']['sha256'];assert len(state['tasks'])==98 and len(state['packets'])==201 and len(state['events'])==677;assert not any(k.startswith('R36-') for k in state['tasks']);assert not any('OBSERVABLE_BRIDGE_RECONCILIATION_20261027' in str(x) for x in state['frontiers'])
pre=O/'approved_repair_preimages';pre.mkdir(exist_ok=False);before={};targets={}
for x in c['preimages_and_exact_target_identities']:
 p=R/x['before']['path'];b=p.read_bytes();assert len(b)==x['before']['bytes'] and hashlib.sha256(b).hexdigest()==x['before']['sha256'];before[x['before']['path']]=b;targets[x['after']['path']]=x['after'];q=pre/x['before']['path'];q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
for x in c['protected_inputs']:assert sha(R/x['path'])==x['sha256'] and (R/x['path']).stat().st_size==x['bytes']
for x in c['raw_failure_to_retain']:
 if 'sha256' in x:assert sha(pathlib.Path(x['path']))==x['sha256']
# Build the exact candidate in memory, preserving original formatting.
after=dict(before);assert before[T].count(b'\r')==0 and before[T].count(b'\n')==241;after[T]=before[T].replace(b'\n',b'\r\n');attrs=next(x['append_text'] for x in c['exact_changes'] if x['path']=='.gitattributes');after['.gitattributes']=before['.gitattributes']+attrs.encode()
e=json.loads(before[E]);orig_e=copy.deepcopy(e);h03=c['protected_inputs'][0];assert e['files'][155]['path']==h03['path'];e['files'][155]['sha256']=h03['sha256'];e['files'][155]['bytes']=h03['bytes'];after[E]=before[E].replace(orig_e['files'][155]['sha256'].encode(),h03['sha256'].encode(),1).replace(b'"bytes": 111343',b'"bytes": 111342',1);assert json.loads(after[E])==e
old_manifest_hash=hashlib.sha256(before[E]).hexdigest();new_manifest_hash=hashlib.sha256(after[E]).hexdigest();front=json.loads(before[F]);assert len(front['tasks'])==11;front_expected=copy.deepcopy(front)
for task in front_expected['tasks']:task['input_identity']='sha256:'+new_manifest_hash;task['input_sources'][0]['sha256']=new_manifest_hash
assert before[F].count(old_manifest_hash.encode())==22;after[F]=before[F].replace(old_manifest_hash.encode(),new_manifest_hash.encode());assert json.loads(after[F])==front_expected
# Zero-tolerance CSV field and Decimal JSON parity before appending the handoff.
a_csv=list(csv.reader(io.StringIO(before[T].decode(),newline='')));b_csv=list(csv.reader(io.StringIO(after[T].decode(),newline='')));assert a_csv==b_csv and len(a_csv)==241 and all(len(x)==6 for x in a_csv)
h03bytes=(R/h03['path']).read_bytes();prior_h03=h03bytes+b'\n';assert hashlib.sha256(prior_h03).hexdigest()==orig_e['files'][155]['sha256'];assert json.loads(h03bytes,parse_float=decimal.Decimal)==json.loads(prior_h03,parse_float=decimal.Decimal)
parity={'CSV_rows':241,'CSV_columns_each':6,'CSV_token_matrix_exact_equal':True,'H03_Decimal_JSON_value_exact_equal':True,'H03_source_unchanged_sha256':sha(R/h03['path']),'historical_H03_plus_LF_sha256':hashlib.sha256(prior_h03).hexdigest(),'tolerance':'zero; exact parsed fields/Decimal values','scientific_computation':False};out('APPROVED_REPAIR_PARITY.json',parity)
note=next(x['append_text'] for x in c['exact_changes'] if x['path']==H);after[H]=before[H]+note.encode();delivery=json.loads(before[L]);delivery_expected=copy.deepcopy(delivery)
for row in delivery_expected['files']:
 if row['path'] in [E,F,H]:row['sha256']=hashlib.sha256(after[row['path']]).hexdigest();row['bytes']=len(after[row['path']])
after[L]=(json.dumps(delivery_expected,indent=2,ensure_ascii=False)+'\n').encode()
for path,b in after.items():assert len(b)==targets[path]['bytes'] and hashlib.sha256(b).hexdigest()==targets[path]['sha256'],path
candidate_dir=O/'approved_repair_candidates';candidate_dir.mkdir(exist_ok=False)
for path,b in after.items():q=candidate_dir/path;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(b)
# All guards and exact targets passed; mutate only the six approved paths once.
for path in ['.gitattributes',T,E,F,H,L]:assert (R/path).read_bytes()==before[path];(R/path).write_bytes(after[path])
closures={}
for name,count in [('EVIDENCE_MANIFEST.json',156),('IMPORT_MANIFEST.json',120),('DELIVERY_MANIFEST.json',196)]:
 a=json.loads((D/name).read_text());assert len(a['files'])==count;checks=[]
 for row in a['files']:
  p=R/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],row['path'];checks.append({'path':row['path'],'sha256':sha(p),'bytes':p.stat().st_size})
 closures[name]={'count':count,'verified':count,'files':checks}
out('APPROVED_REPAIR_MANIFEST_CLOSURE.json',closures)
attr=run('REPAIR_ATTRIBUTES_AFTER',['git','check-attr','text','--',T]).decode().strip();assert attr.endswith(': text: unset');filtered=run('REPAIR_HASH_OBJECT_PATH',['git','hash-object','--path='+T,T]).decode().strip();unfiltered=run('REPAIR_HASH_OBJECT_NO_FILTERS',['git','hash-object','--no-filters',T]).decode().strip();assert filtered==unfiltered
argv=['.venv/bin/python','scripts/codex_harness/publication_frontier_preflight.py','--state','.agent-harness/runtime/r23-continuous/STATE.json','--frontier',F,'--manifest',E];stdout=run('APPROVED_REPAIR_PREFLIGHT',argv);pf=json.loads(stdout);assert pf['status']=='APPEND_READY' and pf['evidence_files_verified']==156 and len(pf['candidate_root_tasks'])==9 and pf['writes_state'] is False
assert statepath.read_bytes()==statebefore and indexpath.read_bytes()==indexbefore
for x in c['protected_inputs']:assert sha(R/x['path'])==x['sha256'] and (R/x['path']).stat().st_size==x['bytes']
for x in c['raw_failure_to_retain']:
 if 'sha256' in x:assert sha(pathlib.Path(x['path']))==x['sha256']
assert run('REPAIR_HEAD_AFTER',['git','rev-parse','HEAD']).decode().strip()==c['base']['HEAD'];assert not run('REPAIR_INDEX_AFTER',['git','diff','--cached','--name-only','-z']);statusafter=run('REPAIR_STATUS_AFTER',['git','status','--porcelain=v1','-z'])
def others(raw):return sorted(x for x in raw.split(b'\0') if x and x[3:].decode() not in after)
assert others(statusbefore)==others(statusafter)
diff=run('REPAIR_EXACT_DIFF',['git','diff','--binary','--no-ext-diff','--']+list(after));out('REPAIR_PROTECTION_AFTER.json',protection());identities=[{'path':p,'bytes':len(after[p]),'sha256':sha(R/p)} for p in after];out('SIX_FINAL_IDENTITIES.json',identities)
result={'status':'REPAIR_READY_FOR_FRESH_DIFFERENT_REVIEW','contract_sha256':sha(contractpath),'base_HEAD':c['base']['HEAD'],'six_final_identities':identities,'parity':parity,'closure':{k:{x:y for x,y in v.items() if x!='files'} for k,v in closures.items()},'preflight':pf,'Git_filtered_blob_oid':filtered,'Git_unfiltered_blob_oid':unfiltered,'exact_diff_sha256':sha(O/'REPAIR_EXACT_DIFF.stdout'),'STATE_bytes_before_after_identical':True,'STATE_sha256':hashlib.sha256(statebefore).hexdigest(),'Git_index_bytes_before_after_identical':True,'unrelated_status_entries_unchanged':True,'protection':protection(),'historical_failures_unchanged':True,'commit':False,'push':False,'scientific_runs':0,'requested_executor':'gpt-6.1-sol/medium','observed_executor':'UNKNOWN'};out('REPAIR_RETURN.json',result)
(O/'FRESH_REVIEW_CONTRACT.md').write_text('Review the exact six-path diff and final identities against the immutable Astra REPAIR_CONTRACT.json SHA019ad3396b0b732bf40149d69ddf84fc9652f28f3a48288282e542ca424af7b9. Verify zero-tolerance CSV token/Decimal JSON parity, 156/120/196 exact manifest closure, active CSV -text/filter preservation and actual APPEND_READY preflight with nine roots. Existing H03/R32 source and historical H03_REPLAY identities must remain unchanged. No staging, commit, STATE append, scientific admission or publication is authorized by this implementation return. Incoming preimages and first failed preflight remain evidence.\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['six_final_identities','preflight']},indent=2));print('FINAL_PREFLIGHT',pf['status'],'roots',len(pf['candidate_root_tasks']))
