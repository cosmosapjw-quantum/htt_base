"""Freeze D07 review identities without repeating the numerical campaign."""
from pathlib import Path
import hashlib,json,subprocess
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
files={}
for path in sorted(HERE.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts or path.name=='CANDIDATE.json':continue
    blob=path.read_bytes();files[str(path.relative_to(HERE))]={'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}
digest=hashlib.sha256('\n'.join(k+' '+v['sha256'] for k,v in files.items()).encode()).hexdigest()
raw=json.loads((HERE/'LP_RAW.json').read_text());result=json.loads((HERE/'D07_RESULT.json').read_text())
initial=json.loads((HERE/'CANDIDATE_INITIAL.json').read_text())
candidate={'task':'D07_JOINT_CALIBRATION_20261018','state':'FROZEN_FOR_SAME_REVIEWER_TARGETED_CLOSEOUT',
           'repo':str(ROOT),'branch':subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip(),
           'D03_task_intake_head':'6219ff0923890aab487135c98db5dd0d5f6dbdf7','campaign_head':'NOT_DIRECTLY_OBSERVED',
           'initial_freeze_head_direct_observation':initial['live_head_at_freeze'],
           'live_head_at_repair_freeze':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
           'initial_candidate_digest_sha256':initial['candidate_digest_sha256'],
           'candidate_digest_sha256':digest,'files':files,'requested_executor_profile':'Sol/high from parent dispatch',
           'exact_requested_model':'UNVERIFIED','observed_executor':'UNKNOWN',
           'contract_framer':'Astra/xhigh requested; UNKNOWN observed; must not review own framing',
           'independent_reviewer':'SAME_REVIEWER_CLOSEOUT_PENDING; numerical component PASS reported by controller','LP_calls_cumulative':raw['calls_started'],'LP_cap':97,'campaigns':1,
           'campaign_elapsed_s':result['elapsed_s'],'scientific_acceptance':'HOLD','commit_push':'NOT_PERFORMED',
           'original_inputs':'D03 aggregate c326fc79b4cfd255d4655cb47b27a4b399403179c3342ac30ae7113c80dcc388; selected NPZ 86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c',
           'presentation_repair':'raw 97 LP endpoints and witnesses retained; 9 tiny ordering ambiguities labelled; no LP rerun or tolerance/budget change',
           'post_review_repair':'one metadata/language repair; original receipt preserved; eta is absolute common calibration and theta latent apparent coefficients, unbounded in the declared model; physical interpretation UNAVAILABLE',
           'next_command':'.venv/bin/python -m unittest discover -s '+str(HERE.relative_to(ROOT))+' -p test_d07.py -v',
           'visual_inspection':'PNG viewed: both panels, raw endpoint segments, labels and conditional/HOLD caveats readable',
           'runtime_authority':'docs/harness/CURRENT_CODEX_RUNTIME.md; no obsolete CUH-G registration created'}
(HERE/'CANDIDATE.json').write_text(json.dumps(candidate,indent=2)+'\n')
print(json.dumps({'candidate_digest_sha256':digest,'files':len(files),'d07_code_sha256':files['d07.py']['sha256'],'result_sha256':files['D07_RESULT.json']['sha256'],'witness_sha256':files['D07_DESIGN_WITNESSES.npz']['sha256']}))
