"""Capture raw axis evidence and emit one deterministic runner JSON document."""
import hashlib
import json
from pathlib import Path
import subprocess
from datetime import datetime, timezone


HERE = Path(__file__).resolve().parent
SINGULAR = Path('/home/cosmosapjw/opt/sage/local/bin/Singular')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture(name, argv):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    stem = '%s_%s' % (name, stamp)
    result = subprocess.run(argv, cwd=HERE, capture_output=True, timeout=1800)
    out = HERE / (stem + '.stdout.log')
    err = HERE / (stem + '.stderr.log')
    out.write_bytes(result.stdout)
    err.write_bytes(result.stderr)
    record = {
        'argv': argv,
        'cwd': str(HERE),
        'exit_code': result.returncode,
        'stdout_path': str(out),
        'stdout_sha256': sha(out),
        'stderr_path': str(err),
        'stderr_sha256': sha(err),
        'stdout_bytes': len(result.stdout),
        'stderr_bytes': len(result.stderr),
        'utc': stamp,
    }
    (HERE / (stem + '.execution.json')).write_text(json.dumps(record, indent=2) + '\n')
    return record


def passed(name, record):
    if record['exit_code'] != 0:
        return False
    stdout = Path(record['stdout_path']).read_text(errors='replace')
    stderr = Path(record['stderr_path']).read_text(errors='replace')
    if stderr:
        return False
    if name == 'sage_version':
        return 'SageMath version 10.9' in stdout
    if name == 'singular_version':
        return 'version 4.4.1 (44100' in stdout
    if name == 'sage_proof':
        return stdout.count('PASS ')==10 and 'SAGE_GENERIC_CERTIFICATE_PASS' in stdout and 'FAIL' not in stdout
    if name == 'singular_proof':
        return stdout.count('PASS ')==6 and 'SINGULAR_GENERIC_CERTIFICATE_PASS' in stdout and 'FAIL' not in stdout and '?' not in stdout and 'error occurred' not in stdout.lower()
    return False


def main():
    sage = 'sage'
    commands = [
        ('sage_version', [sage, '--version']),
        ('singular_version', [str(SINGULAR), '--version']),
        ('sage_proof', [sage, str(HERE / 'bregman_generic.sage')]),
        ('singular_proof', [str(SINGULAR), '-q', str(HERE / 'bregman_generic.sing')]),
    ]
    checks = []
    for name, argv in commands:
        try:
            checks.append(passed(name, capture(name, argv)))
        except Exception:
            checks.append(False)
    ok = all(checks) and len(checks) == len(commands)
    print(json.dumps({
        'checks': {'CAS-11-C01': ok},
        'domain_assumption_diff': [],
        'counterexample': None,
    }, sort_keys=True))
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
