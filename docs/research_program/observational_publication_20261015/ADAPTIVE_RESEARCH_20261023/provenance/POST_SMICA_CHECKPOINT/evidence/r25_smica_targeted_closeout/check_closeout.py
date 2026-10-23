"""Targeted report/binding check only; never imports or runs numerical candidate/tests."""
from pathlib import Path, PurePosixPath
from datetime import datetime, timezone
import hashlib, json, tarfile, time, resource, difflib, sys
start=time.perf_counter()
started=datetime.now(timezone.utc).isoformat()
root=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
new=root/'docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023'
c=new/'smica_spectral_nullspace'
a=Path('/mnt/extdrive/workdir/htt_open_data/r25_smica_spectral_nullspace/report_repair_93531c756f145f01')
b=a/'original'
p=Path('/mnt/extdrive/workdir/htt_open_data/r25_smica_blind_review')
out=Path('/mnt/extdrive/workdir/htt_open_data/r25_smica_targeted_closeout')
packet_path=Path('/mnt/extdrive/workdir/htt_open_data/r25_root_space_recovery/receipts/SMICA_REPAIR_REVIEW_PACKET.json')
packet=json.loads(packet_path.read_text())
expected_packet='fd2e685ec5a644c26e9fe30b739ede21c27ce399b7e6cca0a6d2d34e8217fade'
expected_input='69ad48a48c5f61a5314050a45077bde99af83e97ffe9b8ed270533ee9368710a'
expected_candidate='d89b6c381c6987ac5051b77bcd053aa5a835764718e196735c5434fc94eaace9'
expected_base='4faba983677d56b5d12705a77c0fea498bd3b3263000653ee8151462e3d064d0'
repair_packet='93531c756f145f01059fad1db2ad7e5f2c2f84d90f3797adb27cd54dfc7ada69'
def digest(path):
 with Path(path).open('rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def seal(path):
 path=Path(path)
 return {'path':str(path),'sha256':digest(path),'size_bytes':path.stat().st_size}
def verified(path,spec):
 actual=seal(path)
 assert actual['sha256']==spec['sha256'],(str(path),'hash mismatch',actual,spec)
 if 'size_bytes' in spec: assert actual['size_bytes']==spec['size_bytes'],(str(path),'size mismatch')
 return actual
def diff_fields(old,new,prefix=''):
 if isinstance(old,dict) and isinstance(new,dict):
  result=[]
  for k in sorted(set(old)|set(new)):
   q=prefix+'/'+k
   if k not in old: result.append({'field':q,'kind':'added','after':new[k]})
   elif k not in new: result.append({'field':q,'kind':'removed','before':old[k]})
   else: result.extend(diff_fields(old[k],new[k],q))
  return result
 return [] if old==new else [{'field':prefix,'kind':'changed','before':old,'after':new}]
assert packet['packet_id']==expected_packet and packet['task_id']=='R25-SMICA-SPECTRAL-NULLSPACE'
assert packet['input_identity']=='sha256:'+expected_input
assert packet['candidate_identity']=='sha256:'+expected_candidate and packet['review_only'] is True
inp=new/'R25-SMICA-SPECTRAL-NULLSPACE_INPUT.json'
contract=json.loads(inp.read_text())
input_seal=verified(inp,{'sha256':expected_input})
manifest_seal=verified(c/'MANIFEST.json',{'sha256':expected_candidate})
base_seal=verified(b/'MANIFEST.json',{'sha256':expected_base})
manifest=json.loads((c/'MANIFEST.json').read_text())
base_manifest=json.loads((b/'MANIFEST.json').read_text())
current=json.loads((c/'RETURN.json').read_text())
previous=json.loads((b/'RETURN.json').read_text())
raw=json.loads((c/'RAW_RECEIPT.json').read_text())
repair=json.loads((a/'REPAIR_RAW_RECEIPT.json').read_text())
prior=json.loads((new/'reviews/SMICA_SPECTRAL_REVIEW.json').read_text())
prior_raw=json.loads((p/'REVIEW_RAW_RECEIPT.json').read_text())
prior_stdout=json.loads((p/'check_independent.stdout').read_text())
prior_seals=json.loads((p/'FINAL_SEALS.json').read_text())
assert prior['candidate_identity']=='sha256:'+expected_base
assert prior['input_identity']=='sha256:'+expected_input
assert prior['validation_evidence']['independent_numeric_checks']=='PASS'
assert len(prior['findings'])==1 and prior['findings'][0]['code']=='REPORT_NUMERICAL_SUMMARY_MISMATCH'
assert prior_raw['candidate_identity']=='sha256:'+expected_base
assert prior_raw['independent_check']==prior_stdout
assert prior_stdout['exit_code']==0 and prior_stdout['targets_verified']==112
assert prior_stdout['exact_witnesses_verified']==4
assert prior_stdout['exact_rank']==24 and prior_stdout['exact_nullity']==144
history={v['phase']:v for v in json.loads(packet['spawn_args']['message'].split('Assignment:\n',1)[1])['history_refs']}
prior_receipt=verified(p/'REVIEW_RAW_RECEIPT.json',history['review']['receipt'])
repair_receipt=verified(a/'REPAIR_RAW_RECEIPT.json',history['repair']['receipt'])
retained_review_artifacts={name:verified(spec['path'],spec) for name,spec in prior_raw['artifacts'].items()}
archived={name:verified(spec['path'],spec) for name,spec in repair['archived_originals'].items()}
assert archived['MANIFEST.json']['sha256']==expected_base
assert archived['REPORT.md']['sha256']==prior_seals['candidate_files']['REPORT.md']['sha256']
assert archived['RETURN.json']['sha256']==prior_seals['return']['sha256']
old_report=(b/'REPORT.md').read_text()
new_report=(c/'REPORT.md').read_text()
old_sentence='Among pair contrasts, the smallest lost norm fraction is about 0.4791 for E2/E3 (30−143 GHz) and 0.6796 for B2/B3 (30−143 GHz).'
new_sentence='Among pair contrasts, the smallest lost norm fraction is about 0.7479 for E2/E3 (30−143 GHz) and 0.8169 for B2/B3 (30−143 GHz).'
assert old_report.count(old_sentence)==1
assert old_report.replace(old_sentence,new_sentence)==new_report
report_line=next(i for i,line in enumerate(new_report.splitlines(),1) if new_sentence in line)
manifest_changes=diff_fields(base_manifest,manifest)
assert len(manifest_changes)==1 and manifest_changes[0]['field']=='/files/REPORT.md/sha256'
file_seals={name:verified(c/name,spec) for name,spec in manifest['files'].items()}
assert set(file_seals)=={'compute.py','test_compute.py','RESULT.json','figure.png','REPORT.md','RAW_RECEIPT.json'}
preserved={}
for name,spec in base_manifest['files'].items():
 if name=='REPORT.md': continue
 preserved[name]=verified(c/name,spec)
 assert preserved[name]['sha256']==prior_seals['candidate_files'][name]['sha256']
for path,expected in packet['review_context']['scope']['candidate_seals'].items():
 verified(path,{'sha256':expected})
return_changes=diff_fields(previous,current)
allowed={'/packet_id','/candidate_identity','/raw_receipt','/outcome','/base_packet_id','/base_candidate_identity','/validation/repair_issue','/validation/report_minima_corrected','/validation/report_sha256','/validation/preserved_numeric_and_raw_hashes','/validation/production_reruns','/validation/numeric_test_reruns','/validation/independent_targeted_closeout'}
assert {v['field'] for v in return_changes}==allowed
assert current['packet_id']==repair_packet and current['candidate_identity']=='sha256:'+expected_candidate
assert current['base_packet_id']==previous['packet_id'] and current['base_candidate_identity']==previous['candidate_identity']
assert current['raw_receipt']==str(a/'REPAIR_RAW_RECEIPT.json')
assert current['outcome']=='success' and current['validation']['independent_targeted_closeout']=='PENDING'
assert current['validation']['repair_issue']=='REPORT_NUMERICAL_SUMMARY_MISMATCH'
assert current['validation']['report_minima_corrected'] is True
assert current['validation']['report_sha256']==file_seals['REPORT.md']['sha256']
assert current['validation']['preserved_numeric_and_raw_hashes'] is True
assert current['validation']['production_reruns']==current['validation']['numeric_test_reruns']==0
assert current['qualified_products']==[]
for key,value in previous['validation'].items(): assert current['validation'][key]==value
for key in ['task_id','input_identity','agent_id']:
 assert current[key]==previous[key]==repair[key]
assert repair['packet_id']==repair_packet and repair['candidate_identity']==current['candidate_identity']
assert raw['production_attempts_started']==raw['test_attempts_started']==1
assert raw['limits']==contract['limits']|{} or all(contract['limits'][k]==v for k,v in raw['limits'].items())
archive=Path(contract['source']['archive'])
archive_seal=verified(archive,{'sha256':contract['source']['sha256'],'size_bytes':contract['source']['bytes']})
assert archive_seal['sha256']==prior_seals['source_archive']['sha256']
source_members={}
with tarfile.open(archive,'r:gz') as tar:
 for member in tar:
  name=PurePosixPath(member.name).name
  if name in contract['source']['members']:
   assert name not in source_members and member.isfile()
   data=tar.extractfile(member).read()
   source_members[name]={'sha256':hashlib.sha256(data).hexdigest(),'size_bytes':len(data)}
for name,expected in contract['source']['members'].items(): assert source_members[name]['sha256']==expected
assert len(source_members)==len(contract['source']['members'])
source_identity_seals=[]
for spec in manifest['source_identities']:
 if 'path' in spec: source_identity_seals.append(verified(spec['path'],spec))
 else: assert source_members[spec['member']]['sha256']==spec['sha256']
raw_seals={name:verified(spec['path'],spec) for name,spec in raw['raw_files'].items()}
for name,spec in prior_seals['raw_files'].items(): assert raw_seals[name]==verified(spec['path'],spec)
result=json.loads((c/'RESULT.json').read_text())
assert set(result['operators'])=={'E2','E3','B2','B3'}
extrema={}
for key,operator in result['operators'].items():
 targets=operator['targets']
 pairs=[t for t in targets if t['target'].startswith('contrast_')]
 units=[t for t in targets if t['target'].startswith('unit_')]
 assert len(targets)==operator['target_count']==28 and len(pairs)==21 and len(units)==7
 assert len({t['target'] for t in targets})==28
 smallest=min(pairs,key=lambda t:t['lost_fraction'])
 largest=max(pairs,key=lambda t:t['lost_fraction'])
 extrema[key]={'minimum':[smallest['lost_fraction'],smallest['target']], 'maximum':[largest['lost_fraction'],largest['target']], 'pairs_inspected':len(pairs),'units_present':len(units),'rounded_minimum':format(smallest['lost_fraction'],'.4f')}
 assert smallest['target']=='contrast_30_143'
 assert extrema[key]['rounded_minimum']==('0.7479' if key[0]=='E' else '0.8169')
 for extreme in ['minimum','maximum']:
  assert extrema[key][extreme]==prior_stdout['pair_extrema'][key][extreme]
 assert repair['stored_pair_minima'][key]=={'lost_fraction':smallest['lost_fraction'],'target':smallest['target']}
assert result['tensor']['input_dimension']==168 and result['tensor']['output_dimension']==24
assert result['tensor']['rank']==24 and result['tensor']['nullity']==144
assert manifest['claim_tier']=='C0'
assert manifest['claim_status']=='CANDIDATE_PENDING_INDEPENDENT_REVIEW'
assert current['validation']['original_acceptance']=='UNCHANGED'
summary={'check':'targeted_report_binding_and_preservation','packet_id':expected_packet,'task_id':packet['task_id'],'input_identity':packet['input_identity'],'candidate_identity':packet['candidate_identity'],'base_candidate_identity':'sha256:'+expected_base,'agent_id':'/root/rc_fd2e685ec5a644c2','started_utc':started,'ended_utc':datetime.now(timezone.utc).isoformat(),'wall_seconds':time.perf_counter()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'report_line':report_line,'exact_corrected_sentence':new_sentence,'exact_report_replacement_only':True,'pair_extrema_from_full_stored_result':extrema,'manifest_changes':manifest_changes,'return_changes':return_changes,'input_seal':input_seal,'candidate_seal':manifest_seal,'base_seal':base_seal,'current_return_seal':seal(c/'RETURN.json'),'candidate_files':file_seals,'preserved_files':preserved,'source_archive':archive_seal,'source_members':source_members,'raw_files':raw_seals,'archived_originals':archived,'previous_review_receipt':prior_receipt,'repair_receipt':repair_receipt,'retained_review_artifacts':retained_review_artifacts,'retained_numeric_component':{'method':'Unchanged independently checked numerical evidence reused; script and stdout inspected, identities reverified; no numerical execution repeated','targets':112,'exact_witnesses':4,'tensor_shape':[24,168],'rank':24,'nullity':144,'independent_kernel_vectors':144,'original_review_blocker_preserved':'REPORT_NUMERICAL_SUMMARY_MISMATCH','original_review_verdict_not_promoted':True},'production_reruns_by_this_review':0,'numeric_test_reruns_by_this_review':0,'candidate_imports_or_execution':False,'candidate_or_controller_changes':False,'child_agents':False,'runtime':{'requested_model':'gpt-6-astra','requested_effort':'xhigh','transport_selected_model':packet['route']['transport_selected']['model'],'transport_selected_effort':packet['route']['transport_selected']['effort'],'observed_runtime':'UNKNOWN'},'historical_states':'48 tasks, 17/42, alternate18/42, R9, one-use and native/ODE boundaries unchanged','scientific_claim_ceiling':'C0 fixed released-row information audit only; no physical foreground amplitude or original acceptance promotion','validation_result':'PASS_TARGETED_CHECKS','exit_code':0}
name=sys.argv[1] if len(sys.argv)>1 else 'INITIAL_CHECK.json'
assert '/' not in name
(out/name).write_text(json.dumps(summary,indent=2)+'\n')
(out/'CANDIDATE_DIFF.patch').write_text(''.join(''.join(difflib.unified_diff((b/name).read_text().splitlines(True),(c/name).read_text().splitlines(True),fromfile='original/'+name,tofile='current/'+name)) for name in ['REPORT.md','MANIFEST.json','RETURN.json']))
print(json.dumps({'output':str(out/name),'checks':summary['validation_result'],'pair_extrema':extrema,'wall_seconds':summary['wall_seconds'],'candidate_identity':summary['candidate_identity']},indent=2))
