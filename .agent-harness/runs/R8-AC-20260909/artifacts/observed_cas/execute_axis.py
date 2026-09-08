"""Execute independent axis sources and normalize their explicitly scoped checks.

Original tool output is retained. A negative fixture refuting a forbidden
shortcut is not a counterexample to the registered theorem. Missing proofs stay
null, causing the unchanged aggregate gate to withhold full acceptance.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];RUN=ROOT/'.agent-harness/runs/R8-AC-20260909';HERE=Path(__file__).resolve().parent
axis=sys.argv[1];py='/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python'
commands={
 'wolfram_xact':['wolframscript','-file',str(RUN/'artifacts/wolfram_xact/verify.wls')],
 'sympy':[py,str(RUN/'artifacts/sympy/verify.py')],
 'sage_singular':['sage','-python',str(RUN/'artifacts/sage_singular/verify.py')],
 'lean':[py,str(RUN/'artifacts/lean/verify.py')]}
command=commands[axis];p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
(HERE/(axis+'.stdout')).write_text(p.stdout);(HERE/(axis+'.stderr')).write_text(p.stderr)
contract=json.loads((RUN/'CAS_CONTRACT.json').read_text());names=contract['target']['exact_test_obligations']
raw={};checks={n:None for n in names};counterexample=None;diff=[]
if axis=='wolfram_xact' and p.returncode==0:
 raw=json.loads((RUN/'artifacts/wolfram_xact/checks.json').read_text());checks=raw['contract_checks']
elif axis=='sympy':
 raw=json.loads(p.stdout);checks={k: v.get('status')=='PASS' for k,v in raw['checks'].items()};counterexample=raw.get('counterexample');diff=raw.get('domain_assumption_diff',[])
elif axis=='sage_singular' and p.returncode==0:
 raw=json.loads((RUN/'artifacts/sage_singular/checks.json').read_text());byname={c['name']:c for c in raw['checks']}
 groups={names[0]:['O1_'],names[1]:['O2_'],names[2]:['O3_'],names[3]:['J2_factor_','J2_reduced_','J2_off_','J2_penrose_'],names[4]:['J2_gaussian_','J2_not_']}
 checks={k:bool(selected:=[v for n,v in byname.items() if any(n.startswith(prefix) for prefix in prefixes)]) and all(v['status']=='PASS' for v in selected) for k,prefixes in groups.items()}
 expected={'spectral descriptors are complete joint orbit invariants','rank upper endpoints as exact scores','projected quadratic alone tests singular support','Gaussian marginals plus covariance imply joint Gaussian'}
 if {c['target'] for c in raw['counterexample']}!=expected:counterexample=raw['counterexample']
 diff=raw.get('domain_assumption_diff',[])
elif axis=='lean':
 raw=json.loads(p.stdout);checks=raw['checks'];diff=raw['domain_assumption_diff'];counterexample=raw['counterexample']
(HERE/(axis+'.raw.json')).write_text(json.dumps(raw,indent=2)+'\n')
out={'checks':checks,'counterexample':counterexample,'domain_assumption_diff':diff,'axis':axis,
 'original_exit_code':p.returncode,'command':command,'original_source_sha256':hashlib.sha256(Path(command[-1]).read_bytes()).hexdigest(),
 'contract_sha256':hashlib.sha256((RUN/'CAS_CONTRACT.json').read_bytes()).hexdigest(),
 'raw_output_path':str(HERE/(axis+'.raw.json'))}
(HERE/(axis+'.normalized.json')).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out));sys.exit(p.returncode)
