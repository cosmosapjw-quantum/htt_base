"""One authorized scientific campaign; later verification never repeats LPs."""
from pathlib import Path
import datetime,hashlib,json,os,platform,subprocess,sys
import numpy,scipy,matplotlib,astropy
HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'AGENTS.md').exists())
receipt_path=HERE/'RUN_RECEIPT.json'
old=json.loads(receipt_path.read_text()) if receipt_path.exists() else None
commands=[['d07.py','ALIAS_SKY_HOST_75'],['annotate_endpoints.py'],['-m','unittest','discover','-s',str(HERE),'-p','test_d07.py','-v'],['plot_d07.py']]
if '--verify-only' in sys.argv:commands=commands[1:]
r={'task':'D07_JOINT_CALIBRATION_20261018','D03_task_intake_head':'6219ff0923890aab487135c98db5dd0d5f6dbdf7','cwd':str(ROOT),
   'wrapper_start_head_direct_observation':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
   'campaign_head':'NOT_DIRECTLY_OBSERVED',
   'requested_model':'UNVERIFIED','requested_profile':'Sol/high (parent dispatch; exact model not evidenced)',
   'requested_effort':'high','observed_model':'UNKNOWN','observed_effort':'UNKNOWN',
   'python':sys.executable,'python_version':platform.python_version(),'packages':{m.__name__:m.__version__ for m in [numpy,scipy,matplotlib,astropy]},
   'threads':2,'commands':[],'prior_receipt':old,
   'framer_clarification':'75 same-release explicit alias+SN-sky corroboration+valid named-host J2000 rows; two UNKNOWN directions retained; CF4 linkage not required'}
for spec in commands:
    args=[sys.executable]+([str(HERE/spec[0])]+spec[1:] if spec[0].endswith('.py') else spec)
    item={'argv':args,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'STARTED'}
    r['commands'].append(item);receipt_path.write_text(json.dumps(r,indent=2)+'\n')
    proc=subprocess.run(args,cwd=ROOT,text=True,capture_output=True,env={**os.environ,'OPENBLAS_NUM_THREADS':'2','OMP_NUM_THREADS':'2','MKL_NUM_THREADS':'2'},timeout=620)
    item.update(state='FINISHED',exit_code=proc.returncode,stdout=proc.stdout,stderr=proc.stderr)
    r['code_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.glob('*.py')}
    receipt_path.write_text(json.dumps(r,indent=2)+'\n')
    print(spec[0],proc.returncode,proc.stdout[-2500:],proc.stderr[-2500:],flush=True)
    if proc.returncode:sys.exit(proc.returncode)
