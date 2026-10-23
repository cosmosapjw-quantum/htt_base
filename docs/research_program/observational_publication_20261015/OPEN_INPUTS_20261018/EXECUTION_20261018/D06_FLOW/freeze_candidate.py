"""Freeze the bounded D06 result for the parent's independent review."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'AGENTS.md').exists())
files = {}
for path in sorted(HERE.rglob('*')):
    if not path.is_file() or '__pycache__' in path.parts or path.name == 'CANDIDATE.json':
        continue
    blob = path.read_bytes()
    files[str(path.relative_to(HERE))] = {'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest()}
result = json.loads((HERE / 'D06_RESULT.json').read_text())
stream = '\n'.join(name + ' ' + meta['sha256'] for name, meta in files.items())
candidate = {'task': 'D06_FLOW_20261018', 'state': 'FROZEN_FOR_FRESH_INDEPENDENT_REVIEW',
             'repo': str(ROOT), 'branch': subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True).strip(),
             'intake_head': '1528ebd3c4ace48a561b9dcaa6d5f891121a22a5',
             'candidate_git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
             'requested_model_effort': 'Sol/high; exact model UNVERIFIED (original accepted spawn unavailable in worker context)',
             'observed_model_effort': 'UNKNOWN',
             'candidate_digest_sha256': hashlib.sha256(stream.encode()).hexdigest(), 'files': files,
             'D03_candidate_digest': result['D03_candidate_digest'],
             'scientific_status': result['scientific_status'],
             'source_resolution': result['source_resolution'], 'matched_support': result['matched_support'],
             'independent_review': 'PENDING_PARENT_DISPATCH', 'commit_push': 'NOT_PERFORMED_BY_WORKER',
             'next_command': '.venv/bin/python -m pytest -q ' + str(HERE.relative_to(ROOT) / 'test_flow_control.py')}
(HERE / 'CANDIDATE.json').write_text(json.dumps(candidate, indent=2) + '\n')
print(json.dumps({'candidate_digest_sha256': candidate['candidate_digest_sha256'],
                  'files': files, 'matched_support': result['matched_support']}, indent=2))
