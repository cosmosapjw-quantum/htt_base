from pathlib import Path
import json,hashlib,subprocess,os
R=Path('/mnt/extdrive/workdir/htt_open_data/r36_remaining_manuscript_fresh_review');repo=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base');pkg=repo/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-11-SCIENCE-SYNTHESIS/remaining_manuscript_candidate';c=json.loads((pkg/'EDITOR_CONTRACT.json').read_text());fixture=R/'fixture';s=fixture/c['publication_plan'][0]['root']/'r36_bridge';entry=s/'publication_overlay.py';py=repo/'.venv/bin/python';env=dict(os.environ,OPENBLAS_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(R/'tmp'));manifest=pkg/'candidate/OVERLAY_MANIFEST.json';results=[]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
common=['--contract',s/'EDITOR_CONTRACT.json','--repo',fixture,'--output-root',fixture]
def run(name,cmd,expected_failure=True):
 r=subprocess.run(list(map(str,cmd)),cwd=repo,env=env,capture_output=True,text=True);(R/'raw'/(name+'.stdout')).write_text(r.stdout);(R/'raw'/(name+'.stderr')).write_text(r.stderr);assert (r.returncode!=0)==expected_failure,(name,r.returncode);results.append({'name':name,'exit_code':r.returncode,'expected_rejection':expected_failure,'last_error_line':r.stderr.splitlines()[-1] if r.stderr else None});return r

def mutate(name,file,new,command):
 old=file.read_bytes()
 try:file.write_bytes(new);run(name,command)
 finally:file.write_bytes(old)
source=fixture/c['source_bindings']['02_result']['repo_relative_path'];mutate('negative_wrong_source',source,source.read_bytes()+b'\n',[py,entry,'check',*common])
body=s/'supernova.tex';mutate('negative_wrong_signed_number',body,body.read_bytes().replace(b'+0.017576',b'+0.117576'),[py,entry,'check',*common])
contract=s/'EDITOR_CONTRACT.json';mutate('negative_wrong_contract_binding',contract,contract.read_bytes().replace(b'a1f4f3e6',b'a2f4f3e6')+b'\n',[py,entry,'check',*common])
main=fixture/c['publication_plan'][0]['root']/'main.tex';mutate('negative_wrong_live_target',main,main.read_bytes()+b'%unexpected\n',[py,entry,'apply','--manifest',manifest,'--repo',fixture,'--reviewed-manifest-sha256',sha(manifest)])
run('negative_wrong_review_hash',[py,entry,'apply','--manifest',manifest,'--repo',fixture,'--reviewed-manifest-sha256','0'*64])
shadow=R/'path_mutation';shadow.mkdir(exist_ok=True);(shadow/'docs').symlink_to(pkg/'candidate/docs')
j=json.loads(manifest.read_text());j['files'][-1]['path']='../forbidden_path';bad=shadow/'OVERLAY_MANIFEST.json';bad.write_text(json.dumps(j));run('negative_parent_path',[py,entry,'apply','--manifest',bad,'--repo',fixture,'--reviewed-manifest-sha256',sha(bad)]);assert not (R/'forbidden_path').exists()
# Full covariance preservation is enforced by the exact overlay gate as well as direct independent value audit.
f=s/'NUMERICAL_SUPPLEMENT.json';q=json.loads(f.read_text());q['08_full_result']['primary']['full_16x16_covariance_mag2'][0][8]=0
mutate('negative_supplement_covariance_at_overlay_gate',f,(json.dumps(q)+'\n').encode(),[py,entry,'apply','--manifest',manifest,'--repo',fixture,'--reviewed-manifest-sha256',sha(manifest)])
pre={b['path']:sha(fixture/b['path']) for b in json.loads(manifest.read_text())['files']};run('assembler_second',[py,entry,'assemble',*common],False);assert all(sha(fixture/k)==v for k,v in pre.items())
run('positive_restored_check',[py,entry,'check',*common,'--built-pdfs'],False);r=run('positive_final_noop',[py,entry,'apply','--manifest',manifest,'--repo',fixture,'--reviewed-manifest-sha256',sha(manifest)],False);assert json.loads(r.stdout)['changed_targets']==0
(R/'MUTATIONS.json').write_text(json.dumps({'status':'PASS','all_manifested_objects_unchanged_by_second_assembly':True,'results':results},indent=2)+'\n');print('PASS7 actual mutation rejections; assembler idempotence; restored final check and no-op')
