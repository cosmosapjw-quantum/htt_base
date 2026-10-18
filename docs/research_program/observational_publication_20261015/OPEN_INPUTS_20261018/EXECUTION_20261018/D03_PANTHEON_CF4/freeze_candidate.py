"""Bind only the D03 candidate for the parent's fresh read-only reviewer."""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
files={}
for path in sorted(HERE.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts or path.name=='CANDIDATE.json':continue
    data=path.read_bytes();files[str(path.relative_to(HERE))]={'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
stream='\n'.join(name+' '+info['sha256'] for name,info in files.items())
result=json.loads((HERE/'results/D03_RESULT.json').read_text())
candidate={'task':'D03_PANTHEON_CF4_20261018','state':'FROZEN_FOR_FRESH_INDEPENDENT_REVIEW',
           'repo':str(ROOT),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
           'base_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
           'requested_model':'gpt-6-sol','requested_effort':'high','observed_model':'UNKNOWN','observed_effort':'UNKNOWN',
           'reviewer':'PENDING_PARENT_DISPATCH','commit_push':'NOT_PERFORMED_BY_WORKER',
           'candidate_digest_sha256':hashlib.sha256(stream.encode()).hexdigest(),'files':files,
           'counts':result['graph_counts'],'scientific_status':'HOLD: original H02/S02/H04/S04/K04 not admitted',
           'residual_failures':result['unresolved'],
           'next_command':'.venv/bin/python -m unittest discover -s '+str(HERE.relative_to(ROOT))+' -p test_d03.py -v',
           'runtime_authority':'docs/harness/CURRENT_CODEX_RUNTIME.md; obsolete global CUH-G absent, not recreated',
           'remote_mutation':'none','visual_inspection':'D03_COMPARISON.png viewed; titles/labels/points readable; limits explicit'}
(HERE/'CANDIDATE.json').write_text(json.dumps(candidate,indent=2)+'\n')
print(json.dumps({'candidate_digest_sha256':candidate['candidate_digest_sha256'],'files':len(files),'code':{k:v['sha256'] for k,v in files.items() if k.endswith('.py')},'result_sha256':files['results/D03_RESULT.json']['sha256']}))
