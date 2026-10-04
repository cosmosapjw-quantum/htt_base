#!/usr/bin/env python3
"""Execute both CAS engines on every call and emit one typed JSON object."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[7]
CONTRACT=ROOT/'docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-05/neutral_admission_20261003/EXECUTION_CONTRACT_V3.json'
NEUTRAL=ROOT/'docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-05/neutral_admission_20261003/NEUTRAL_INPUT.json'
COMMON=ROOT/'docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md'
EXPECTED={CONTRACT:'a67bf54921c80d35865d28dfce86d0ff9670270a807d5f2f45f25e3e7029537f',NEUTRAL:'0868c1f15226e71926dad034319b85c73a9ca9c7d3c72064e06ff65d0112b27b',COMMON:'4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def invoke(argv, run_dir, label):
    try:
        cp=subprocess.run(argv,cwd=ROOT,text=True,capture_output=True,timeout=1800)
        rc=cp.returncode; out=cp.stdout; err=cp.stderr
    except subprocess.TimeoutExpired as exc:
        rc=124; out=(exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout,bytes) else (exc.stdout or '')
        err=(exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr,bytes) else (exc.stderr or '')
        err+='\nTIMEOUT_1800_SECONDS\n'
    (run_dir/f'{label}.stdout').write_text(out); (run_dir/f'{label}.stderr').write_text(err)
    return {'argv':argv,'cmd':' '.join(argv),'cwd':str(ROOT),'exit':rc,'stdout':str(run_dir/f'{label}.stdout'),'stderr':str(run_dir/f'{label}.stderr'),'stdout_sha256':sha(run_dir/f'{label}.stdout'),'stderr_sha256':sha(run_dir/f'{label}.stderr')},out
def compact(s): return s.replace(' ','').replace('\n','')
def main():
    run_dir=HERE/'runs'/(dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);run_dir.mkdir(parents=True)
    commands=[]; evidence={}; diffs=[]; checks={n:False for n in ('CAS-05-C01','CAS-05-C02','CAS-05-C03')}
    for p,digest in EXPECTED.items():
        observed=sha(p)
        if observed!=digest: diffs.append(f'INPUT_HASH_MISMATCH:{p}:{observed}')
    # Versions and every engine invocation are retained with exact argv/cwd/exit.
    versions={}
    for label,argv in [('sage_version',['sage','-python','-c','import sage.version; print(sage.version.version)']),('singular_version',['Singular','--version'])]:
        rec,out=invoke(argv,run_dir,label);commands.append(rec);versions[label]=out.splitlines()[0] if out else ''
    rec,sage_out=invoke(['sage','-python',str(HERE/'sage_axis.py')],run_dir,'sage');commands.append(rec)
    rec,singular_out=invoke(['Singular','-q',str(HERE/'singular_axis.sing')],run_dir,'singular');commands.append(rec)
    if commands[-2]['exit']==0 and commands[-1]['exit']==0 and not diffs:
        try:
            sage=json.loads(sage_out); evidence['sage']=sage
            singular_lines=singular_out.splitlines(); flags={}; jets={}; bianchi=[]
            for line in singular_lines:
                if line.startswith('JET:'):
                    _,mu,a,c,val=line.split(':',4); key=(int(mu)-1,int(a)-1,int(c)-1)
                    if key in jets: raise ValueError('duplicate Singular jet')
                    jets[key]=val
                elif line.startswith('BIANCHI:'): bianchi.append(line)
                elif ':' in line:
                    key,val=line.split(':',1); flags[key]=val
            parity=len(jets)==40 and all(compact(jets[(mu,a,c)])==compact(sage['delta_G_jet'][str(mu)][a][c]) for mu in range(4) for a in range(4) for c in range(a,4))
            singular_valid=(flags.get('IMAGES_OK')=='1' and flags.get('J2_OK')=='1' and flags.get('BIANCHI_OK')=='1' and flags.get('RIGHT_INVERSE_GROEBNER')==','.join(['0']*12) and len(bianchi)==4 and parity)
            checks['CAS-05-C01']=sage['checks']['CAS-05-C01'] is True
            checks['CAS-05-C02']=sage['checks']['CAS-05-C02'] is True
            checks['CAS-05-C03']=sage['checks']['CAS-05-C03'] is True and singular_valid
            evidence['singular']={'flags':flags,'bianchi':bianchi,'forty_jet_coefficients':{f'{mu}{a}{c}':val for (mu,a,c),val in jets.items()},'sage_singular_exact_parity':parity}
        except Exception as exc:
            diffs.append(f'ENGINE_OUTPUT_PARSE_OR_COMPARE:{type(exc).__name__}:{exc}')
    else:
        if commands[-2]['exit']!=0: diffs.append('SAGE_ENGINE_EXIT_NONZERO')
        if commands[-1]['exit']!=0: diffs.append('SINGULAR_ENGINE_EXIT_NONZERO')
    status='PASS' if all(checks.values()) and not diffs else ('MISALIGNED_ASSUMPTIONS' if any(x.startswith('INPUT_HASH') for x in diffs) else ('FAIL' if not diffs and any(x is False for x in checks.values()) else 'INCONCLUSIVE'))
    result={'axis':'sage_singular','status':status,'contract_sha256':sha(CONTRACT),'completed_at':dt.datetime.now(dt.timezone.utc).isoformat(),'evidence_class':'exact','checks':checks,'domain_assumption_diff':diffs,'counterexample':None,'computed_exact_evidence':evidence,'commands':commands,'tool_versions':versions,'source_input_hashes':{str(p):sha(p) for p in EXPECTED},'axis_source_hashes':{p.name:sha(p) for p in (HERE/'sage_axis.py',HERE/'singular_axis.sing',HERE/'run.py')},'run_dir':str(run_dir),'author_runtime':{'registered_profile':'cuhg_gpt6_sol_worker','requested_model':'gpt-6-sol','requested_effort':'high','observed_model':'unknown_from_axis_process','observed_effort':'unknown_from_axis_process','shared_llm_family':'OpenAI GPT-6 Sol'}}
    (run_dir/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    (HERE/'result.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    sys.stdout.write(json.dumps({'checks':checks,'domain_assumption_diff':diffs,'counterexample':None,'computed_exact_evidence':evidence},sort_keys=True)+'\n')
if __name__=='__main__': main()
