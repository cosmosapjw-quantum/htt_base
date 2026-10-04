"""Frozen narrow local Lean helper oracle: only the eta contraction tactic."""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
PROJECT = pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/formal_mathlib')
THEOREM = '''import Mathlib
abbrev I := Fin 4
def sum4 (f : I → ℝ) : ℝ := f 0 + f 1 + f 2 + f 3
def sig (a : I) : ℝ := if a = 0 then -1 else 1
def delta (a b : I) : ℝ := if a = b then 1 else 0
def eta (a b : I) : ℝ := delta a b * sig a
theorem eta_contraction (a b : I) :
    sum4 (fun d => eta a d * eta d b) = delta a b := by
'''

def main(response_path: pathlib.Path, out_dir: pathlib.Path):
    response = json.loads(response_path.read_text())
    if response.get('ok') is not True:
        raise ValueError('managed response failed')
    result = response['result']
    if result.get('finish_reason') not in ('stop', 'eos_token'):
        raise ValueError('incomplete model payload')
    payload = json.loads(result['response_text'])
    if set(payload) != {'tactic'} or not isinstance(payload['tactic'], str):
        raise ValueError('exact tactic schema required')
    tactic = payload['tactic']
    if len(tactic) > 1200 or re.search(r'\b(sorry|admit|axiom|unsafe|native_decide)\b', tactic):
        raise ValueError('forbidden or oversized tactic')
    out_dir.mkdir(parents=True, exist_ok=False)
    source = out_dir / 'HelperOracle.lean'
    source.write_text(THEOREM + tactic + '\n#print axioms eta_contraction\n')
    argv = ['lake', 'env', 'lean', '-j1', str(source)]
    run = subprocess.run(argv, cwd=PROJECT, capture_output=True, text=True, timeout=120)
    (out_dir/'stdout.log').write_text(run.stdout)
    (out_dir/'stderr.log').write_text(run.stderr)
    (out_dir/'validation.json').write_text(json.dumps({
        'argv': argv, 'cwd': str(PROJECT), 'exit_code': run.returncode,
        'status': 'PASS' if run.returncode == 0 and 'sorryAx' not in run.stdout else 'FAIL'
    }, indent=2))
    print((out_dir/'validation.json').read_text())

if __name__ == '__main__':
    main(pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]))
