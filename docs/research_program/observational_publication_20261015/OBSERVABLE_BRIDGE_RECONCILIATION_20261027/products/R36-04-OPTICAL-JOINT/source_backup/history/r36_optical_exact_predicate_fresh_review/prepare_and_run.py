import hashlib, json, os, shutil, subprocess, sys, time
from pathlib import Path

ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_exact_predicate_fresh_review')
REL=Path('docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-04-OPTICAL-JOINT/repair_03')
CAND=ROOT/REL
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
def check(record,role):
    p=Path(record['path']); p=p if p.is_absolute() else ROOT/p
    got=sha(p) if p.exists() else None
    records.append(dict(path=str(p),role=role,expected=record['sha256'],actual=got,bytes=p.stat().st_size if p.exists() else None,match=got==record['sha256']))
manifest=json.loads((CAND/'ARTIFACT_MANIFEST.json').read_text())
check(dict(path=str(CAND/'ARTIFACT_MANIFEST.json'),sha256='ec4421a423a87889cc268c65d551a772846ca93298b028d08143201ec824137b'),'candidate_manifest')
for group in ('source_bindings','candidate_files'):
    for r in manifest[group].values(): check(r,group)
for r in manifest['validation']['evidence'].values(): check(r,'author_raw_evidence_identity_only')
evidence=ROOT/REL.parents[2]/'EVIDENCE_MANIFEST.json'
for r in json.loads(evidence.read_text())['files']: check(r,'retained_input_preimage')
for parent in (CAND.parent,CAND.parent/'repair_01',CAND.parent/'repair_02'):
    pm=json.loads((parent/'ARTIFACT_MANIFEST.json').read_text())
    for r in pm.get('candidate_files',{}).values(): check(r,'preserved_historical_candidate')
git={k:subprocess.check_output(v,cwd=ROOT,text=True) for k,v in {
    'head':['git','rev-parse','HEAD'],'branch':['git','branch','--show-current'],
    'origin':['git','remote','get-url','origin'],'status':['git','status','--short']}.items()}
identity=dict(packet_id='95e5a85a0b844f73611609f1b2d45d40320a3b89309ca558aa2b84f550c6b134',
    candidate_identity='sha256:ec4421a423a87889cc268c65d551a772846ca93298b028d08143201ec824137b',
    requested_runtime={'model':'gpt-6-astra','effort':'xhigh'}, observed_runtime='UNKNOWN',
    ack=json.loads(Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/ACK_032_GO.json').read_text()),
    records=records,git=git)
(OUT/'IDENTITY_INITIAL.json').write_text(json.dumps(identity,indent=2)+'\n')
bad=[r for r in records if not r['match']]
print('identity records',len(records),'mismatches',len(bad),flush=True)
if bad:
    print(json.dumps(bad,indent=2));sys.exit(1)
fixture=OUT/'small_fixture'; dest=fixture/REL;dest.mkdir(parents=True,exist_ok=True)
for name in ('optical_joint.py','consume.py','test_optical_joint.py'):
    shutil.copy2(CAND/name,dest/name)
for rel in (REL.parents[2]/'EVIDENCE_MANIFEST.json',Path('docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/evidence/research/latest_results.json')):
    target=fixture/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',MPLCONFIGDIR=str(OUT/'mpl_config'),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
receipts=[]
for label,cmd in [('PYTEST',[sys.executable,'-B','-m','pytest','-q','-c','/dev/null','-p','no:cacheprovider',str(dest/'test_optical_joint.py')]),('CONSUMER',[sys.executable,'-B',str(dest/'consume.py')])]:
    start=time.time()
    proc=subprocess.run(cmd,cwd=dest,env=env,text=True,capture_output=True)
    (OUT/(label+'.stdout')).write_text(proc.stdout);(OUT/(label+'.stderr')).write_text(proc.stderr)
    receipts.append(dict(label=label,command=cmd,cwd=str(dest),exit_code=proc.returncode,elapsed_seconds=time.time()-start))
    print(label,proc.returncode,proc.stdout[-1200:],proc.stderr[-1200:],flush=True)
(OUT/'EXECUTION_RECEIPTS.json').write_text(json.dumps(receipts,indent=2)+'\n')
if all(r['exit_code']==0 for r in receipts):
    original=json.loads((CAND/'RESULT.json').read_text());actual=json.loads((dest/'RESULT.json').read_text())
    comparison=dict(result_exact_semantic_equality=actual==original,table_byte_equality=sha(dest/'TABLE.csv')==sha(CAND/'TABLE.csv'))
    (OUT/'CONSUMER_COMPARISON.json').write_text(json.dumps(comparison,indent=2)+'\n');print(comparison)
