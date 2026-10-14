"""Pinned minimal dependency build for the CAS15 strength-based continuation.
This is not a historical four-axis adjudication. Compiled imports stay temporary.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, subprocess, tempfile
T = Path(__file__).resolve().parent
ROOT = next(p for p in T.parents if (p / 'formal_mathlib/lean-toolchain').is_file())
ORACLE = Path('/home/cosmosapjw/lean_oracles/viii_oracle')
p = argparse.ArgumentParser()
p.add_argument('--log-dir', type=Path)
a = p.parse_args()
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
log = a.log_dir or T / 'build_logs' / stamp
log.mkdir(parents=True, exist_ok=False)
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
steps = []
sources = [('CAS15ProjectionAccepted', T / 'Projection.lean'),
           ('CAS15Frobenius', T / 'Frobenius.lean'),
           ('CAS15Mixed', T / 'Mixed.lean'),
           ('CAS15Spectral', T / 'Spectral.lean'),
           ('Synthesis', T / 'Synthesis.lean'),
           ('CoercivityBridge', T / 'CoercivityBridge.lean'),
           ('OrderedMatchingBridge', T / 'OrderedMatchingBridge.lean'),
           ('FullSynthesis', T / 'FullSynthesis.lean')]
record = {'steps': steps, 'sources': {str(s.relative_to(ROOT)): sha(s) for _,s in sources},
          'scientific_admission': 'HOLD', 'historical_four_axis_adjudication': 'NOT_RUN'}
def save():
    (log / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
try:
    assert sha(T / 'Projection.lean') == 'e32abc568e0400d5e5a1a6ddaf0044abe897bd9c77ea2f9c50bf4fdb072c4904'
    assert (ROOT / 'formal_mathlib/lean-toolchain').read_bytes() == (ORACLE / 'lean-toolchain').read_bytes()
    manifests = [json.loads((r / 'lake-manifest.json').read_text()) for r in [ROOT / 'formal_mathlib', ORACLE]]
    revs = [{q['name']:q['rev'] for q in m['packages']} for m in manifests]
    assert revs[0] == revs[1]
    record['toolchain'] = (ORACLE / 'lean-toolchain').read_text().strip()
    record['package_revisions'] = revs[0]
    record['manifest_difference_class'] = 'packaging metadata; package revisions equal'
    with tempfile.TemporaryDirectory(prefix='htt-cas15-build-') as temp:
        tmp = Path(temp)
        env = {**os.environ, 'LEAN_PATH': str(tmp)}
        def run(name, argv):
            started = datetime.datetime.now(datetime.timezone.utc)
            r = subprocess.run(argv, cwd=ORACLE, env=env, text=True, capture_output=True)
            (log / (name + '.stdout')).write_text(r.stdout)
            (log / (name + '.stderr')).write_text(r.stderr)
            steps.append({'name': name, 'argv': argv, 'cwd': str(ORACLE), 'LEAN_PATH': env['LEAN_PATH'],
                          'exit': r.returncode, 'started_utc': started.isoformat(),
                          'elapsed_seconds': (datetime.datetime.now(datetime.timezone.utc)-started).total_seconds()})
            save()
            print(name, 'exit', r.returncode, flush=True)
            return r.returncode
        code = run('version', ['lake', 'env', 'lean', '--version'])
        if not code:
            for name, src in sources:
                target = tmp / (name + '.lean')
                target.write_bytes(src.read_bytes())
                code = run(name, ['lake', 'env', 'lean', '-R', str(tmp), '-o', str(tmp/(name+'.olean')), str(target)])
                if code:
                    break
        record['exit'] = code
except Exception as e:
    record['preflight_failure'] = repr(e)
    record['exit'] = 1
    (log / 'preflight.stderr').write_text(repr(e) + '\n')
save()
print('logs:', log, flush=True)
raise SystemExit(record['exit'])
