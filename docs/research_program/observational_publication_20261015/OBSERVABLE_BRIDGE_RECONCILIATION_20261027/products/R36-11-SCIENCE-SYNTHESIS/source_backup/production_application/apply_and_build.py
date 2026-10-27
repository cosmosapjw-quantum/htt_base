import os,sys,pathlib,json,hashlib,subprocess,time,shutil
R=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base');B=pathlib.Path('/mnt/extdrive/workdir/htt_open_data');O=B/'r36_synthesis_publication';D=R/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-11-SCIENCE-SYNTHESIS';C=D/'repair_01';P4=R/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-06-P4-DESIGN';V=B/'r36_synthesis_repair_fresh_review'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def out(n,v):(O/n).write_text(json.dumps(v,indent=2)+'\n')
def run(n,args,cwd=R):
 t=time.monotonic()
 with open(O/(n+'.stdout'),'xb') as so,open(O/(n+'.stderr'),'xb') as se:
  p=subprocess.Popen(args,cwd=cwd,stdout=so,stderr=se,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_OPTIONAL_LOCKS='0',OPENBLAS_NUM_THREADS='1'))
  rec={'argv':[str(x) for x in args],'cwd':str(cwd),'pid':p.pid,'parent_pid':os.getpid(),'proc_stat':pathlib.Path(f'/proc/{p.pid}/stat').read_text(),'utc_start':time.time()};out(n+'_START.json',rec);code=p.wait()
 rec.update(exit_code=code,elapsed_seconds=time.monotonic()-t,stdout_sha256=sha(O/(n+'.stdout')),stderr_sha256=sha(O/(n+'.stderr')));out(n+'.json',rec);assert code==0,(n,code);return (O/(n+'.stdout')).read_bytes()
sys.path.insert(0,'/mnt/extdrive/workdir/htt_open_data/r35_p5_reviewed_publication');import publish
out('PUBLISHER_PROCESS.json',{'pid':os.getpid(),'parent_pid':os.getppid(),'proc_stat':pathlib.Path('/proc/self/stat').read_text(),'cwd':str(R),'source_sha256':sha(pathlib.Path(__file__)),'observed_runtime':'UNKNOWN'})
assert run('HEAD_BEFORE',['git','rev-parse','HEAD']).decode().strip()=='2a7c81355f5830384d1a27976fc1c08d1be2a329';assert not run('INDEX_BEFORE',['git','diff','--cached','--name-only','-z']);run('BRANCH',['git','branch','--show-current']);run('ORIGIN',['git','remote','get-url','origin']);run('STATUS_BEFORE',['git','status','--porcelain=v1','-z']);out('PROTECTION_BEFORE.json',publish.protection())
assert sha(C/'ARTIFACT_MANIFEST.json')=='83b167a9388071a1a82500716d338473bd8ac5c9abb3c978974a914a37066519';manifest=json.loads((C/'ARTIFACT_MANIFEST.json').read_text());assert len(manifest['artifacts'])==56
for row in manifest['artifacts']:assert sha(C/row['path'])==row['sha256'] and (C/row['path']).stat().st_size==row['bytes']
assert sha(V/'formal_binding_01/CONTROLLER_RETURN.json')=='c32e8b71932e957f0af625ec86965d732da633694d307b6ff8138d3a21dbd0b1';formal=json.loads((V/'formal_binding_01/CONTROLLER_RETURN.json').read_text());state=json.loads((R/'.agent-harness/runtime/r23-continuous/STATE.json').read_text());task=state['tasks']['R36-11-SCIENCE-SYNTHESIS'];assert task['state']=='completed' and task['qualified_products']==['observable_bridge_manuscript_update'] and task['history'][-1]['result']==formal
out('RECORDED_QUALIFICATION.json',{'task':'R36-11-SCIENCE-SYNTHESIS','state':'completed','packet':formal['packet_id'],'candidate_identity':formal['candidate_identity'],'qualified_products':task['qualified_products'],'latest_record_matches_exact_formal_RETURN':True,'STATE_writes':0})
plan=json.loads((C/'APPLICATION_PLAN.json').read_text());assert pathlib.Path(plan['destination'])==P4
before=[]
for q in P4.rglob('*'):
 if q.is_file() and '__pycache__' not in q.parts:before.append({'path':str(q),'bytes':q.stat().st_size,'sha256':sha(q)})
out('P4_BEFORE_FILES.json',before)
backup=O/'preproduction_preimages';backup.mkdir()
for rel,v in plan['files'].items():
 q=P4/rel;assert (sha(q) if q.exists() else None)==v['preimage_sha256'],rel
 if q.exists():t=backup/rel;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,t)
for rel in ['report/main.pdf','PUBLICATION_STATUS.json']:
 q=P4/rel
 if q.exists():t=backup/rel;t.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(q,t)
run('APPLY_REVIEWED',[str(R/'.venv/bin/python'),'-B',str(C/'apply_candidate.py'),'--apply-reviewed-candidate'])
run('POSTAPPLY_ASSEMBLE',[str(R/'.venv/bin/python'),'-B','report/r36_11/assemble.py'],P4)
run('POSTAPPLY_CHECK',[str(R/'.venv/bin/python'),'-B','report/r36_11/check.py'],P4)
run('POSTAPPLY_BUILD',['latexmk','-g','-pdf','-interaction=nonstopmode','-halt-on-error','-cd','report/main.tex'],P4)
run('POSTBUILD_CHECK',[str(R/'.venv/bin/python'),'-B','report/r36_11/check.py'],P4)
second=json.loads(run('APPLY_IDEMPOTENT',[str(R/'.venv/bin/python'),'-B',str(C/'apply_candidate.py'),'--apply-reviewed-candidate']));assert second['changed']==[]
info=run('PDFINFO',['pdfinfo',str(P4/'report/main.pdf')]).decode();assert 'Pages:           24' in info
run('PDFTEXT_CURRENT',['pdftotext',str(P4/'report/main.pdf'),'-']);run('PDFTEXT_SEALED',['pdftotext',str(C/'candidate/R32-06-P4-DESIGN/report/main.pdf'),'-']);assert (O/'PDFTEXT_CURRENT.stdout').read_bytes()==(O/'PDFTEXT_SEALED.stdout').read_bytes(),'PDF text differs'
for rel,v in plan['files'].items():assert sha(P4/rel)==v['final_sha256'],rel
for row in manifest['artifacts']:assert sha(C/row['path'])==row['sha256']
log=(P4/'report/main.log').read_text();import re
assert not re.search(r'undefined|Overfull|^!',log,re.M)
text=(P4/'report/main.tex').read_text();figs=re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}',text);assert len(figs)==5 and all((P4/'report'/x).is_file() for x in figs)
out('PRODUCTION_APPLICATION_RETURN.json',{'status':'APPLIED_BUILT_CHECKED_IDEMPOTENT','candidate_identity':formal['candidate_identity'],'destination':str(P4),'apply_changed':json.loads((O/'APPLY_REVIEWED.stdout').read_text())['changed'],'second_apply_changed':[],'new_applied_consumer':'report/r36_11/assemble.py','old_science_producer_runs':0,'PDF_pages':24,'figures':figs,'PDF_text_equal_sealed_candidate':True,'pdf_sha256':sha(P4/'report/main.pdf'),'tex_sha256':sha(P4/'report/main.tex'),'all56_frozen_candidate_files_unchanged':True,'STATE_writes':0,'protected':publish.protection()})
print((O/'PRODUCTION_APPLICATION_RETURN.json').read_text())
