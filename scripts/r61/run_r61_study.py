#!/usr/bin/env python3
"""Run the bounded R61 verification and three actual-data calculations in order."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo-root',default='.')
    parser.add_argument('--output',required=True)
    parser.add_argument('--research-record')
    args=parser.parse_args();root=Path(args.repo_root).resolve();out=Path(args.output).resolve()
    out.mkdir(parents=True,exist_ok=True)
    receipt=out/'BATCH_EXECUTION.json'
    if receipt.exists():raise ValueError('refusing to replace an execution receipt')
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1',
             PYTHONPATH='htt/src:htt:.')
    commands=[('TESTS',[sys.executable,'-B','-m','pytest','-q','tests/r61']),
      ('IMAGES',[sys.executable,'-B','scripts/r61/run_r61_kinematic_images.py','--repo-root',str(root),'--output',str(out/'IMAGES')]),
      ('DEPTH',[sys.executable,'-B','scripts/r61/run_r61_depth_measurement.py','--repo-root',str(root),'--output',str(out/'DEPTH')]),
      ('MIXED',[sys.executable,'-B','scripts/r61/run_r61_mixed_invariant.py','--repo-root',str(root),'--output',str(out/'MIXED')])]
    report={'schema':'htt.r61.execution/1','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'runner_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'status':'RUNNING','commands':[]}
    def save():receipt.write_text(json.dumps(report,indent=2)+'\n')
    def stage(number,status,evidence):
        if not args.research_record:return
        p=Path(args.research_record);d=json.loads(p.read_text())
        d['stages'][number-1]['status']=status
        d.setdefault('stage'+str(number),{})['status']=status
        d['stage'+str(number)]['execution_evidence']=evidence
        d['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        p.write_text(json.dumps(d,indent=2)+'\n')
    save()
    for name,cmd in commands:
        start=time.perf_counter();log=out/(name+'_EXECUTION.log')
        print('START',name,flush=True)
        with log.open('w') as handle:
            proc=subprocess.run(cmd,cwd=root,env=env,stdout=handle,stderr=subprocess.STDOUT)
        report['commands'].append({'name':name,'argv':cmd,'exit_code':proc.returncode,
              'wall_seconds':time.perf_counter()-start,'log':str(log.relative_to(out)),
              'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest()})
        save();print('END',name,'exit',proc.returncode,flush=True)
        if proc.returncode:
            report['status']='FAILED_PRESERVED';save()
            print('\n'.join(log.read_text().splitlines()[-45:]),flush=True)
            raise SystemExit(proc.returncode)
        if name=='TESTS':
            stage(6,'complete','RESULTS/TESTS_EXECUTION.log; all R61 tests; existing symbolic and isolated mixed checks')
            stage(7,'in_progress','RESULTS/BATCH_EXECUTION.json')
    report['status']='COMPLETE';report['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
    stage(7,'complete','RESULTS/IMAGES, RESULTS/DEPTH, RESULTS/MIXED; all three real-data runners exited zero')
    stage(8,'in_progress','Numerical interpretation and publication assessment')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
