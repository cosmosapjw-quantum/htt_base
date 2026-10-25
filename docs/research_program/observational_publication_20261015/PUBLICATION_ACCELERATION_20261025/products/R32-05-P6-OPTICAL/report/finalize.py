"""Package the actual candidate without claiming acceptance or runtime identity."""
from pathlib import Path
import json,hashlib,sys,platform
import numpy,matplotlib
R=Path(__file__).resolve().parent;ROOT=R.parents[6]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
repo='/home/cosmosapjw/Dropbox/bianchi/htt_base'; rel=str(R.relative_to(Path(repo)))
commands=[
 {'command':'Misplaced packaging heredocs in repository root, then .venv/bin/python '+rel+'/finalize.py','cwd':repo,'exit':2,'note':'Failure preserved in raw/packager_first_failure.*; narrow recovery retained in raw/misplaced_file_recovery.json'},
 {'command':'ls '+rel,'cwd':repo,'exit':2,'note':'First actual failure: assigned report directory absent; retained raw/intake_first_failure.txt'},
 {'command':'.venv/bin/python '+rel+'/reproduce.py > '+rel+'/raw/consumer.stdout 2> '+rel+'/raw/consumer.stderr','cwd':repo,'exit':0,'runs':1},
 {'command':'python build_source.py > raw/source_build.stdout 2> raw/source_build.stderr','cwd':str(R),'exit':0},
 {'command':'latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > raw/latexmk_first.stdout 2> raw/latexmk_first.stderr','cwd':str(R),'exit':0,'note':'Successful first build; overfull equation (26) recorded'},
 {'command':'python build_source.py > raw/source_build_final.stdout 2> raw/source_build_final.stderr','cwd':str(R),'exit':0,'note':'Layout-only wrap of equation (26)'},
 {'command':'latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > raw/latexmk_final.stdout 2> raw/latexmk_final.stderr','cwd':str(R),'exit':0},
 {'command':'pdftotext -layout main.pdf raw/main.txt','cwd':str(R),'exit':0},
 {'command':'pdfinfo main.pdf > raw/pdfinfo.txt','cwd':str(R),'exit':0},
 {'command':'pdftoppm -scale-to 1100 -png main.pdf raw/layout > raw/layout_render.stdout 2> raw/layout_render.stderr','cwd':str(R),'exit':0},
 {'command':'python validate_candidate.py > raw/candidate_audit.stdout 2> raw/candidate_audit.stderr','cwd':str(R),'exit':0},
 {'command':'.venv/bin/python '+rel+'/finalize.py','cwd':repo,'exit':0,'note':'RESULT packager; successful creation and print is this command receipt'}]
save(R/'raw/commands.json',commands)
save(R/'raw/environment.json',{'python_executable':sys.executable,'python_version':platform.python_version(),'numpy':numpy.__version__,'matplotlib':matplotlib.__version__,'requested_model':'gpt-6.1-sol','requested_reasoning_effort':'medium','observed_runtime_identity':'UNKNOWN','checkout_branch_at_intake':'research/htt-adaptive-methods-20261023','checkout_HEAD_at_intake':'dff1f6a330bffec122225c3b0e8edb19e8b7d122','origin_at_intake':'https://github.com/cosmosapjw-quantum/htt_base.git','existing_dirty_state':'preserved; implementation restricted to assigned report directory'})
# All immutable candidate outputs are sealed, including source scripts and raw failures.
outputs=[]
for p in sorted(R.rglob('*')):
 if p.is_file() and p.name!='RESULT.json':outputs.append({'path':str(p.relative_to(R)),'sha256':sha(p),'bytes':p.stat().st_size})
manifest={'sources':json.loads((R/'generated/sources.json').read_text()),'outputs':outputs}
manifest_identity=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(',',':')).encode()).hexdigest()
result={'schema':'htt.p6.optical_inverse_candidate/1','task_id':'R32-05-P6-OPTICAL','packet_id':'4061878216a65321d922f6c919d44fd3406ce3e8bfefe7d7e02a1329d703ceec','assignment_input_identity':'sha256:f900ec93d972751795cdd825ee0f362eabed3a2aae60b59e4c24d265ee6ec132','assignment_input_identity_scope':'Controller-provided packet identity; retained source files independently checked against manifest','candidate_path':str(R),'candidate_only':True,'acceptance_passed':False,'original_acceptance_passed':False,'qualified_products':[],'proposed_qualified_products':['optical_inverse_note'],'owner':'mio','scope':'Conditional finite optical inverse methods and retained apparent tensor diagnostic','claim_tier':'C0','transfer_source':'none (retained apparent CF4 statistic empirical_proxy)','requested_executor':{'model':'gpt-6.1-sol','reasoning_effort':'medium'},'observed_executor':'UNKNOWN','scientific_author_observed_runtime':'UNKNOWN','build_status':'BUILT_CANDIDATE_PENDING_INDEPENDENT_REVIEW','consumer_run_count':1,'focused_checks_passed':len(json.loads((R/'generated/checks.json').read_text())['checks']),'candidate_audit':json.loads((R/'generated/candidate_audit.json').read_text()),'diagnostic_statuses':json.loads((R/'generated/retained_tensor_region.json').read_text())['diagnostic_statuses'],'sky_support_status':'retained finite J2000 CF4 selected directions; no full-sphere observational reconstruction','null_mock_status':'UNKNOWN; none generated','limitations':['All response and Hubble error radii assumed; same-event/congruence/frame physical response qualification absent','Working C is an adopted deterministic shape; no empirically calibrated covariance or joint probability law','No physical H value or physical shear detection estimated','Finite inverse theorem is for the declared linear model; nonlinear global injectivity is not inferred','Missing vorticity, tilt, curvature, energy, H and history sectors remain unresolved','Independent review, scientific admission and publication are pending'],'manifest_canonical_json_sha256':manifest_identity,'manifest':manifest}
save(R/'RESULT.json',result)
print(json.dumps({'RESULT_sha256':sha(R/'RESULT.json'),'manifest_sha256':manifest_identity,'output_files':len(outputs),'candidate_path':str(R)},indent=2))
