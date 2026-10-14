"""Compile only the ordered matching source and its spectral dependency."""
from pathlib import Path
import datetime, hashlib, json, os, subprocess, tempfile

BASE = Path(__file__).resolve().parent.parent
ORACLE = Path('/home/cosmosapjw/lean_oracles/viii_oracle')
STAMP = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
LOG = Path(__file__).resolve().parent / STAMP
LOG.mkdir()
sources = [('CAS15Spectral', BASE / 'Spectral.lean'),
           ('OrderedMatchingBridge', BASE / 'OrderedMatchingBridge.lean')]
record = {'requested_runtime': {'model': 'gpt-6.1-sol', 'effort': 'high'},
          'observed_runtime': 'UNKNOWN',
          'scientific_admission': 'HOLD', 'historical_four_axis_adjudication': 'NOT_RUN',
          'source_sha256': {str(s): hashlib.sha256(s.read_bytes()).hexdigest() for _, s in sources},
          'steps': []}
with tempfile.TemporaryDirectory(prefix='cas15-ordered-matching-') as tmp:
    env = {**os.environ, 'LEAN_PATH': tmp}
    def run(name, argv):
        start = datetime.datetime.now(datetime.timezone.utc)
        proc = subprocess.run(argv, cwd=ORACLE, env=env, capture_output=True, text=True)
        (LOG / (name + '.stdout')).write_text(proc.stdout)
        (LOG / (name + '.stderr')).write_text(proc.stderr)
        record['steps'].append({'name': name, 'argv': argv, 'cwd': str(ORACLE),
            'LEAN_PATH': tmp, 'exit': proc.returncode, 'started_utc': start.isoformat(),
            'elapsed_seconds': (datetime.datetime.now(datetime.timezone.utc)-start).total_seconds()})
        (LOG / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
        print(name, 'exit', proc.returncode, flush=True)
        print(proc.stdout, end='', flush=True)
        print(proc.stderr, end='', flush=True)
        return proc.returncode
    code = run('version', ['lake', 'env', 'lean', '--version'])
    if not code:
        for name, src in sources:
            target = Path(tmp) / (name + '.lean')
            target.write_bytes(src.read_bytes())
            code = run(name, ['lake', 'env', 'lean', '-R', tmp, '-o',
                str(Path(tmp) / (name + '.olean')), str(target)])
            if code:
                break
record['exit'] = code
record['toolchain'] = (ORACLE / 'lean-toolchain').read_text().strip()
record['package_revisions'] = {p['name']: p['rev']
    for p in json.loads((ORACLE / 'lake-manifest.json').read_text())['packages']}
(LOG / 'execution.json').write_text(json.dumps(record, indent=2) + '\n')
print('logs:', LOG, flush=True)
raise SystemExit(code)
