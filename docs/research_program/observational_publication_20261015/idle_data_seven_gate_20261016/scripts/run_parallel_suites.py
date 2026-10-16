#!/usr/bin/env python3
"""Concurrent isolated pytest subprocesses (NOT native scientific subagents)."""
import concurrent.futures
import json
import os
import pathlib
import re
import subprocess
import sys
from time import time

ROOT=pathlib.Path(__file__).resolve().parents[1]
TESTS=sorted((ROOT/'tests').glob('test_*.py'))


def run_test(path):
    env=os.environ.copy();env['PYTHONPATH']=str(ROOT/'src')
    for k in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        env[k]='1'
    st=time()
    p=subprocess.run([sys.executable,'-m','pytest','-q',str(path)],
                     env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,
                     timeout=30,check=False)
    return {'suite':path.name,'exit_code':p.returncode,
            'elapsed_s':round(time()-st,5),'stdout':p.stdout,'stderr':p.stderr,
            'process_kind':'INDEPENDENT_PYTEST_SUBPROCESS'}


def main():
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TESTS)) as ex:
        records=list(ex.map(run_test,TESTS))
    txt='\n'.join(x['stdout'] for x in records)
    passed=sum(int(x.group(1)) for r in records for x in re.finditer(r'(\d+) passed',r['stdout']))
    result={'execution':'CONCURRENT_ISOLATED_SUBPROCESS_SUITES_NOT_NATIVE_SUBAGENTS',
            'tests_passed':passed,'all_pass':all(r['exit_code']==0 for r in records),
            'source_scope':'MANUFACTURED_NOT_PHYSICAL_INPUT','records':records}
    output=ROOT/'results'/'PARALLEL_TEST_RECEIPT.json'
    output.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    for r in records:
        print(r['suite'],r['exit_code'],r['stdout'].strip().replace('\n',' | '))
    print('TOTAL',passed,'PASS' if result['all_pass'] else 'FAIL')
    if not result['all_pass']:sys.exit(1)

if __name__=='__main__':main()
