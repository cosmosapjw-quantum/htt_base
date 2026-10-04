#!/usr/bin/python3.12
"""Frozen no-argument SageMath/Singular axis runner for adopted CAS-06."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
S = HERE.parent
SOURCE = HERE / 'axis.sage.py'
CONTRACT = S / 'EXECUTION_CONTRACT.json'
ADMITTED = S / 'ADMITTED_INPUTS.json'
COMMON = REPO / 'docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md'
SAGE = '/usr/local/bin/sage'
SINGULAR = '/home/cosmosapjw/opt/sage/local/bin/Singular'
EXPECTED = {
    CONTRACT:'9936c95ac128126d34688bbd8ece9fb90c92aa7dfeea8fa7b41716ab449e88f3',
    ADMITTED:'711de321c374a85b4b0414d5df1f8a62b55368f73c2a3d31e502e209af8793eb',
    COMMON:'4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897'}
KEYS = ['CAS-06-C01','CAS-06-C02','CAS-06-C03','CAS-06-C04']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
attempt=HERE / 'attempts' / stamp
attempt.mkdir(parents=True,exist_ok=False)
commands=[]
issues=[]
checks={k:False for k in KEYS}

def run(argv,label,timeout=1800):
    rec={'argv':argv,'cwd':str(REPO),'started_at':now()}
    try:
        proc=subprocess.run(argv,cwd=REPO,capture_output=True,text=True,
                            timeout=timeout,check=False)
        rec['exit_code']=proc.returncode
        out,err=proc.stdout,proc.stderr
    except subprocess.TimeoutExpired as exc:
        rec['exit_code']=None
        rec['timeout_seconds']=timeout
        out=(exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout,bytes) else (exc.stdout or '')
        err=(exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr,bytes) else (exc.stderr or '')
        issues.append(label+' timeout')
    except Exception as exc:
        rec['exit_code']=None
        out='';err=repr(exc)
        issues.append(label+' launch failure')
    rec['completed_at']=now()
    for suffix,body in [('stdout',out),('stderr',err)]:
        path=attempt/(label+'.'+suffix+'.log')
        path.write_text(body)
        rec[suffix+'_path']=str(path.relative_to(REPO))
        rec[suffix+'_sha256']=sha(path)
    commands.append(rec)
    return out,err,rec['exit_code']

before={str(p.relative_to(REPO)):sha(p) for p in [*EXPECTED,SOURCE,Path(__file__)]}
for p,h in EXPECTED.items():
    if before[str(p.relative_to(REPO))]!=h: issues.append('frozen input hash mismatch: '+str(p))
for p in [SOURCE,Path(__file__)]:
    dst=attempt/p.name
    shutil.copy2(p,dst)
    dst.chmod(0o444)

version_out,version_err,version_ec=run([SAGE,'-sh','-c',
  'command -v Singular; Singular --version; sage --version'],'versions',60)
if version_ec!=0 or SINGULAR not in version_out or 'version 4.4.1 (44100' not in version_out or 'SageMath version 10.9' not in version_out:
    issues.append('pinned Sage/Singular toolchain not observed')

problems=[]
if not issues:
    sage_command='sage -python '+str(SOURCE.relative_to(REPO))
    sage_out,sage_err,sage_ec=run([SAGE,'-sh','-c',sage_command],'sage',1800)
    if sage_ec!=0: issues.append('Sage execution failed')
    match=re.search(r'^SAGE_CHECKS (\{.*\})$',sage_out,re.M)
    if match:
        try:
            parsed=__import__('ast').literal_eval(match.group(1))
            if set(parsed)==set(KEYS) and all(type(v) is bool for v in parsed.values()):
                checks=parsed
            else: issues.append('Sage check shape invalid')
        except Exception as exc: issues.append('Sage check parse: '+repr(exc))
    else: issues.append('Sage check line absent')
    match=re.search(r'^SINGULAR_PROBLEMS_JSON (\[.*\])$',sage_out,re.M)
    if match:
        try: problems=json.loads(match.group(1))
        except Exception as exc: issues.append('Singular problem parse: '+repr(exc))
    else: issues.append('Singular problem line absent')

singular_results={}
if problems and not issues:
    # A reduction zero is meaningful only relative to admitted metric/ODE
    # numerators; target residuals are queried, never ideal generators.
    vars='r,F,F1,F2,N,N1,N2,E,t,h,m,m1,m2,ep,ep1,ep2,kap,al,lam,mu,ep0,c,q,ps,s,X,y,B,C'
    lines=['ring rr=0,('+vars+'),dp;','option(redSB);']
    for item in problems:
        name=item['name']
        if not re.fullmatch(r'C0[12]_[A-Z0-9]+',name):
            issues.append('invalid problem name');break
        gens=','.join(item['generators'])
        lines.extend(['ideal I_'+name+'='+gens+';',
          'ideal G_'+name+'=std(I_'+name+');',
          'poly P_'+name+'=('+item['localization_multiplier']+')*('+item['numerator']+');',
          'poly Z_'+name+'=reduce(P_'+name+',G_'+name+');',
          'print("CERT_'+name+'="+string(Z_'+name+'));'])
    lines.append('quit;')
    script=attempt/'exact_reductions.sing'
    script.write_text('\n'.join(lines)+'\n')
    script.chmod(0o444)
    if not issues:
        sout,serr,sec=run([SINGULAR,'-q',str(script)],'singular',1800)
        if sec!=0 or re.search(r'\?\s|error|unknown identifier|parse error',sout+'\n'+serr,re.I):
            issues.append('Singular exit/error diagnostics')
        for item in problems:
            name=item['name']
            hits=re.findall(r'^CERT_'+name+r'=(.*)$',sout,re.M)
            if len(hits)!=1:
                issues.append('Singular missing/duplicate result '+name)
            else:
                singular_results[name]=hits[0].strip()
                if hits[0].strip()!='0': issues.append('Singular nonzero remainder '+name)

after={str(p.relative_to(REPO)):sha(p) for p in [*EXPECTED,SOURCE,Path(__file__)]}
if before!=after: issues.append('source/runner/input changed during attempt')
for k in KEYS:
    if not checks[k]: issues.append('failed Sage obligation '+k)
status='PASS' if not issues and len(singular_results)==2 else 'INCONCLUSIVE'
if any(x.startswith('failed Sage obligation') or x.startswith('Singular nonzero') for x in issues): status='FAIL'
result={'schema_version':1,'axis':'sage_singular','status':status,
    'evidence_class':'exact','contract_sha256':EXPECTED[CONTRACT],
    'completed_at':now(),'commands':commands,'checks':checks,
    'domain_assumption_diff':[],'counterexample':None,
    'source_input_hashes_before':before,'source_input_hashes_after':after,
    'source_snapshot':str((attempt/SOURCE.name).relative_to(REPO)),
    'runner_snapshot':str((attempt/Path(__file__).name).relative_to(REPO)),
    'singular_remainders':singular_results,
    'singular_denominators':{x['name']:x['denominator'] for x in problems},
    'singular_localization_multipliers':{x['name']:x['localization_multiplier'] for x in problems},
    'issues':issues,'analytic_obligations':'HOLD'}
(attempt/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
(HERE/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
payload={'checks':checks if status=='PASS' else {k:False for k in KEYS},
         'domain_assumption_diff':[],'counterexample':None}
print(json.dumps(payload,sort_keys=True))
sys.exit(0 if status=='PASS' else 1)
