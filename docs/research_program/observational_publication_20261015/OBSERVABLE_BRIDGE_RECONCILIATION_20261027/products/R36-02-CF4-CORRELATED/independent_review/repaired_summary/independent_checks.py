from pathlib import Path
import contextlib, difflib, hashlib, importlib.util, io, json, math, os, shutil, subprocess, sys, time
import numpy as np
REPO=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
BASE=REPO/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-02-CF4-CORRELATED'
CAND=BASE/'repair_01'
EXT=Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual')
AUTHOR=Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_repair_actual')
HERE=Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_summary_repair_independent_review')
EXPECTED='a0edd2e76d0b74630d47bbccd5cd90dcb4e372ca1772ee202585a34270d68fb4'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def read(p): return json.loads(Path(p).read_text())
def write(p,v): Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
start=time.time()
manifest=read(CAND/'ARTIFACT_MANIFEST.json'); base=read(BASE/'ARTIFACT_MANIFEST.json')
assert sha(CAND/'ARTIFACT_MANIFEST.json')==EXPECTED
assert 'sha256:'+sha(BASE/'ARTIFACT_MANIFEST.json')==manifest['base_candidate_identity']
rows=[]
def bind(path,expected,expected_size=None,label=''):
 actual=sha(path); size=Path(path).stat().st_size
 r={'path':str(path),'sha256':actual,'bytes':size,'sha_match':actual==expected,'size_match':expected_size is None or size==expected_size,'label':label}
 rows.append(r)
 assert r['sha_match'] and r['size_match'],r
for section,root in [('product_files',BASE),('external_files',EXT)]:
 for name,v in base[section].items(): bind(root/name,v['sha256'],v['bytes'],'retained_base_'+section)
for name,v in manifest['new_files'].items(): bind(CAND/name,v['sha256'],v['bytes'],'candidate')
for name,v in manifest['retained_cache_files'].items(): bind(EXT/name,v['sha256'],v['bytes'],'unchanged_cache')
bind(Path(manifest['independent_blocker_path']),manifest['independent_blocker_sha256'],label='frozen_repair_plan')
bind(Path(manifest['actual_ack_path']),manifest['actual_ack_sha256'],label='author_execution_ack_identity_only')
source=REPO/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz'
operator=Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_exact_operator_actual/A_RAW_36x35970.npz')
bind(source,base['source_identity']['selected_source_sha256'],label='retained_source')
bind(operator,base['source_identity']['operator_artifact_sha256'],label='retained_operator')
# Preserve historical candidate and the three pointer-correction preimages.
initial=read(AUTHOR/'INITIAL_MANIFEST_POINTER_ERROR.json')
first_return=read(AUTHOR/'INITIAL_RETURN_POINTER_ERROR.json')
first_raw=read(AUTHOR/'INITIAL_RAW_RECEIPT_POINTER_ERROR.json')
assert first_return['candidate_identity']=='sha256:'+sha(AUTHOR/'INITIAL_MANIFEST_POINTER_ERROR.json')
assert first_raw['candidate_identity']==first_return['candidate_identity']
preimages=manifest['author_self_found_pointer_correction']['changed_file_preimages']
preimage_diffs={}
for name,v in initial['new_files'].items():
 path=Path(preimages[name]['path']) if name in preimages else CAND/name
 bind(path,v['sha256'],v['bytes'],'initial_pointer_error_candidate')
 if name in preimages:
  assert v['sha256']==preimages[name]['sha256']
  preimage_diffs[name]=''.join(difflib.unified_diff(path.read_text().splitlines(True),(CAND/name).read_text().splitlines(True),fromfile=str(path),tofile=str(CAND/name)))
write(HERE/'PREIMAGE_DIFFS.json',preimage_diffs)
preimage_evidence={n:{'path':str(AUTHOR/n),'sha256':sha(AUTHOR/n)} for n in ['INITIAL_MANIFEST_POINTER_ERROR.json','INITIAL_RETURN_POINTER_ERROR.json','INITIAL_RAW_RECEIPT_POINTER_ERROR.json','RETURN_V2.json','RAW_RECEIPT_V2.json']}
for n in ['RETURN_V2.json','RAW_RECEIPT_V2.json']:
 assert read(AUTHOR/n)['candidate_identity']=='sha256:'+EXPECTED
# Independently calculate 12 trace ratios and 12 Frobenius relative differences.
# Explicit scalar fsum uses no functions from the producer or repaired consumer.
with np.load(EXT/'STAGE_C.npz',allow_pickle=False) as z: full=z['total']
with np.load(EXT/'SENSITIVITY_MATRICES.npz',allow_pickle=False) as z: subsets={name:z[name] for name in z.files}
assert full.shape==(108,108)
old=read(BASE/'SENSITIVITY.json'); fixed=read(CAND/'SENSITIVITY.json')
assert set(subsets)==set(fixed['results'])==set(old['results'])
calc=[];r5=[];changes=[]
for name in sorted(subsets):
 assert subsets[name].shape==(108,108)
 for ir,radius in enumerate((5,10,20)):
  idx=range(ir*36,(ir+1)*36)
  sub=subsets[name]
  tr=math.fsum(float(sub[i,i]) for i in idx)
  trref=math.fsum(float(full[i,i]) for i in idx)
  normdiff=math.sqrt(math.fsum(float(sub[i,j]-full[i,j])**2 for i in idx for j in idx))
  normref=math.sqrt(math.fsum(float(full[i,j])**2 for i in idx for j in idx))
  ratio=tr/trref; frob=normdiff/normref
  row=fixed['results'][name]['bands_sum_blocks'][ir]
  prev=old['results'][name]['bands_sum_blocks'][ir]
  assert row['R_hinv_Mpc']==radius
  diffs={'trace_ratio_abs':abs(ratio-row['trace_ratio_to_full_sample']),'frob_abs':abs(frob-row['frobenius_relative_to_full_sample'])}
  assert max(diffs.values())<1e-14
  assert row['trace']==prev['trace'] and row['rank_1e_10']==prev['rank_1e_10']
  if ir==0:
   assert row==prev;r5.append(name)
  else:
   for field in ('trace_ratio_to_full_sample','frobenius_relative_to_full_sample'):
    assert row[field]!=prev[field]
    changes.append({'path':f'results/{name}/bands_sum_blocks/{ir}/{field}','before':prev[field],'after':row[field]})
  calc.append({'case':name,'radius':radius,'subset_trace':tr,'full_trace':trref,'independent_trace_ratio':ratio,'independent_relative_frobenius':frob,'errors':diffs})
# Aside from the two comparison fields and provenance, every value stays identical.
normalized=json.loads(json.dumps(fixed)); normalized.pop('repair')
for name in subsets:
 for ir in (1,2):
  for field in ('trace_ratio_to_full_sample','frobenius_relative_to_full_sample'):
   normalized['results'][name]['bands_sum_blocks'][ir][field]=old['results'][name]['bands_sum_blocks'][ir][field]
assert normalized==old
old_result=read(BASE/'RESULT.json');new_result=read(CAND/'RESULT.json')
normalized_result=json.loads(json.dumps(new_result)); normalized_result.pop('repair')
assert normalized_result==old_result
# Resolve actual result references from the actual containing directory.
pointers=[]
for field in ['footprint_method_sensitivity','controls','sample_covariance_uncertainty']:
 value=new_result[field]; filename,_,fragment=value.partition('#');path=CAND/filename
 rec={'field':field,'value':value,'resolved_path':str(path),'exists':path.is_file(),'fragment':fragment}
 try:
  data=read(path)
  rec['read_success']=True
  if fragment:rec['fragment_exists']=fragment in data
 except Exception as e:
  rec['read_success']=False;rec['exception_type']=type(e).__name__;rec['exception']=str(e)
 pointers.append(rec)
assert pointers[0]['read_success']
# Execute an unchanged copy of the bounded summary-only source into review-owned output.
consumer=HERE/'consumer_copy';consumer.mkdir(exist_ok=True)
shutil.copyfile(CAND/'run_sensitivity.py',consumer/'run_sensitivity.py')
assert sha(consumer/'run_sensitivity.py')==sha(CAND/'run_sensitivity.py')
spec=importlib.util.spec_from_file_location('independent_consumer_execution',consumer/'run_sensitivity.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
module.BASE=BASE; module.HERE=consumer
captured=io.StringIO();begin=time.monotonic()
with contextlib.redirect_stdout(captured):module.main()
consumer_seconds=time.monotonic()-begin
(HERE/'consumer_copy_stdout.log').write_text(captured.getvalue())
consumer_matches={n:sha(consumer/n)==sha(CAND/n) for n in ['RESULT.json','SENSITIVITY.json']}
assert all(consumer_matches.values())
# Exactly the three supplied focused regressions. Disable repo bytecode and pytest cache writes.
cmd=[str(REPO/'.venv/bin/python'),'-B','-m','pytest','-q','-p','no:cacheprovider',str(CAND/'test_sensitivity_repair.py')]
env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
begin=time.monotonic();proc=subprocess.run(cmd,cwd=REPO,env=env,capture_output=True,text=True);elapsed=time.monotonic()-begin
(HERE/'regressions.stdout.log').write_text(proc.stdout);(HERE/'regressions.stderr.log').write_text(proc.stderr)
assert proc.returncode==0,proc.stdout+proc.stderr
assert '3 passed' in proc.stdout
# Ensure all observed immutable/candidate files remain identical after checks.
for r in rows:assert sha(Path(r['path']))==r['sha256'],r
assert sha(CAND/'ARTIFACT_MANIFEST.json')==EXPECTED
assert 'sha256:'+sha(BASE/'ARTIFACT_MANIFEST.json')==manifest['base_candidate_identity']
report={'schema':'htt.r36.summary_repair_independent_checks/1','candidate_identity':'sha256:'+EXPECTED,'base_candidate_identity':manifest['base_candidate_identity'],'input_identity':manifest['input_identity'],'bindings':rows,'preimage_evidence':preimage_evidence,'initial_pointer_error_candidate_identity':first_return['candidate_identity'],'independent_summary_comparisons':calc,'unchanged_R5_cases':r5,'changed_summary_values':changes,'sensitivity_other_fields_unchanged':True,'result_fields_except_provenance_unchanged':True,'result_pointers':pointers,'consumer_copy':{'source_sha256':sha(consumer/'run_sensitivity.py'),'output_sha_equal':consumer_matches,'seconds':consumer_seconds,'write_directory':str(consumer),'source_transforms_or_covariance_producers_run':False},'focused_regressions':{'command':cmd,'cwd':str(REPO),'exit_code':proc.returncode,'seconds':elapsed,'stdout':str(HERE/'regressions.stdout.log'),'stderr':str(HERE/'regressions.stderr.log')},'all_bound_files_unchanged_after_review':True,'sourceful_reproduction':{'python_executable':sys.executable,'python_version':sys.version,'numpy_version':np.__version__},'runtime':{'requested_model':'gpt-6-astra','requested_reasoning':'xhigh','observed_runtime':'UNKNOWN'},'forbidden_expensive_work_run':False,'old_R30_600s_bank_charged':False,'elapsed_seconds':time.time()-start}
write(HERE/'INDEPENDENT_CHECKS.json',report)
print(json.dumps({'candidate':report['candidate_identity'],'bound_file_checks':len(rows),'independent_rows':len(calc),'changed_summary_values':len(changes),'R5_unchanged':len(r5),'max_abs_error':max(max(r['errors'].values()) for r in calc),'regressions':proc.stdout.strip(),'consumer_matches':consumer_matches,'unresolved_result_fields':[p['field'] for p in pointers if not p['exists']],'all_bound_files_unchanged':True},indent=2))
