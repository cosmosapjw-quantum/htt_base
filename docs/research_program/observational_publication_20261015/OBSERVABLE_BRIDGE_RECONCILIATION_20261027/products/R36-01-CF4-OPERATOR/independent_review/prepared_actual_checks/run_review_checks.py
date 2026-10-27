"""Retain exact reviewer commands and raw process outcomes."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_operator_fresh_review')
EXPORT=ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR/export_operator.py'
ENV={'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1',
     'PYTHONDONTWRITEBYTECODE':'1','MPLCONFIGDIR':str(OUT/'mplconfig')}
commands=[
    ('independent_numerics',[str(ROOT/'.venv/bin/python'),'-B',str(OUT/'check_candidate.py')],0),
    ('actual_consumer',[str(ROOT/'.venv/bin/python'),'-B',str(EXPORT),'consume'],0),
    ('permuted_id_consumer',[str(ROOT/'.venv/bin/python'),'-B',str(EXPORT),'consume','--product',str(OUT/'permuted_id_fixture')],1),
]
receipt={'schema':'htt.r36.independent_raw_receipt/1','mode':'PREPARATION_ONLY_NOT_FORMAL_CONTROLLER_RETURN',
         'cwd':str(ROOT),'env_overrides':ENV,'commands':[]}
for name,argv,expected in commands:
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    t=time.monotonic()
    proc=subprocess.run(argv,cwd=ROOT,env={**os.environ,**ENV},stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    elapsed=time.monotonic()-t
    log=OUT/(name+'.log')
    log.write_text(proc.stdout)
    matched=proc.returncode==expected
    if name=='permuted_id_consumer':
        matched=matched and 'AssertionError: operator source row identity' in proc.stdout
    entry={'name':name,'argv':argv,'started_utc':started,'exit_status':proc.returncode,
           'expected_exit_status':expected,'expected_outcome_matched':matched,
           'elapsed_seconds':elapsed,'log':str(log),
           'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()}
    receipt['commands'].append(entry)
    (OUT/'RAW_REVIEW_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(entry),flush=True)
    if not matched:
        raise SystemExit(2)
