"""Record the finite R61 release gates without refitting the scientific results."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
import yaml

root = Path(__file__).resolve().parents[2]
folder = root / 'docs/research_program/observational_publication_20261015/R61_KINEMATIC_MEASUREMENT_20261117'
base = folder.parent
python = str(root / '.venv/bin/python')
env = dict(os.environ, OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
           PYTHONDONTWRITEBYTECODE='1', PYTHONPATH='htt/src:htt:.')
commands = [
    ('current_tests', [python, '-B', '-m', 'pytest', '-q', 'tests/r61']),
    ('sync_mirrors', [python, '-B', 'scripts/codex_harness/sync_pr_dag_mirrors.py', '--write']),
    ('validate_canonical', [python, '-B', 'scripts/codex_harness/validate_pr_dag.py', 'docs/codex_handoff/pr_backlog.yaml']),
    ('progress', [python, '-B', 'scripts/codex_harness/progress_report.py', 'docs/codex_handoff/pr_backlog.yaml', 'docs/codex_handoff/pr_status.yaml', '--json']),
    ('check_mirrors', [python, '-B', 'scripts/codex_harness/sync_pr_dag_mirrors.py', '--check']),
    ('validate_publication', [python, '-B', 'scripts/htt_publication_dag.py', '--validate']),
    ('export_publication', [python, '-B', 'scripts/htt_publication_dag.py', '--export']),
]
receipt = {'schema': 'htt.r61.release_validation/1',
           'started_utc': datetime.now(timezone.utc).isoformat(),
           'baseline_commit': 'fb6ae9f21585e194ef29dabc91d79a529e0ac57e',
           'scientific_claim': 'Structural release gates do not establish physical transfer or submission readiness.',
           'commands': []}
for name, cmd in commands:
    log = folder / 'RESULTS' / ('FINAL_' + name.upper() + '.log')
    t = time.monotonic()
    with log.open('w') as stream:
        proc = subprocess.run(cmd, cwd=root, env=env, stdout=stream, stderr=subprocess.STDOUT, check=False)
    item = {'name': name, 'argv': cmd, 'exit_code': proc.returncode,
            'elapsed_seconds': time.monotonic() - t,
            'log': str(log.relative_to(folder)),
            'log_sha256': hashlib.sha256(log.read_bytes()).hexdigest()}
    receipt['commands'].append(item)
    print(json.dumps(item), flush=True)
    if proc.returncode:
        receipt['status'] = 'FAILED'
        (folder / 'DAG_VALIDATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
        sys.exit(proc.returncode)

def old_file(path):
    return subprocess.check_output(['git', 'show', receipt['baseline_commit'] + ':' + path], cwd=root).decode()

backlog_path = 'docs/codex_handoff/pr_backlog.yaml'
previous = yaml.safe_load(old_file(backlog_path))
current = yaml.safe_load((root / backlog_path).read_text())
assert len(previous['prs']) == 284 and len(current['prs']) == 285
assert previous['prs'] == current['prs'][:-1]
assert current['prs'][-1]['id'] == 'PR-R61-KINEMATIC-MEASUREMENT'
publication_path = str((base / 'PUBLICATION_DAG.json').relative_to(root))
previous_pub = json.loads(old_file(publication_path))
current_pub = json.loads((root / publication_path).read_text())
assert len(current_pub['nodes']) == 42 and previous_pub['nodes'] == current_pub['nodes']
assert all(p['publication_status'] == 'NOT_READY_TO_SUBMIT' for p in current_pub['papers'])
dag = json.loads((folder / 'RESEARCH_DAG.json').read_text())
assert len(dag['tasks']) == 10 and len(dag['future_science']) == 4
nodes = {n['id']: n for n in dag['tasks'] + dag['future_science']}
assert len(nodes) == 14
done, active = set(), set()
def visit(key):
    assert key in nodes and key not in active
    if key in done:
        return
    active.add(key)
    for dep in nodes[key]['depends_on']:
        visit(dep)
    active.remove(key)
    done.add(key)
for key in nodes:
    visit(key)
for index, node in enumerate(dag['tasks']):
    assert node['status'] == 'complete_scoped'
    assert node['depends_on'] == ([] if index == 0 else [dag['tasks'][index-1]['id']])
    for evidence in node['evidence']:
        assert evidence == 'DAG_VALIDATION.json' or (folder / evidence).is_file(), evidence
assert dag['automatic_successor'] is False and dag['local_agent_prompt_created'] is False
receipt['local_checks'] = {'previous_284_cards_unchanged': True,
    'new_card_count': 285, 'original_42_nodes_unchanged': True,
    'six_submission_statuses_preserved': True, 'local_DAG_acyclic': True,
    'sequential_stages': 10, 'explicit_future_input_tasks': 4,
    'evidence_files_present': True, 'no_automatic_successor': True}
receipt['status'] = 'PASS_SCOPED'
receipt['finished_utc'] = datetime.now(timezone.utc).isoformat()
(folder / 'DAG_VALIDATION.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'status': receipt['status'], **receipt['local_checks']}), flush=True)
