"""Execute the staged handler against a temporary fixture, never live hooks."""
import json
import os
from pathlib import Path
import subprocess
import sys

repo = Path('/home/cosmosapjw/codex_global_harness')
out = Path('/tmp/cas11-c02-routing-repair-20260930')
base = Path('/mnt/sn850x2t/local_ai_foundry/60_runtime/cuhg/policy-authorities/3b243df626bce98ee31ba899d48c9bceddef1bfd')
sys.path[:0] = [str(repo / 'src'), str(repo / 'tests'), str(repo / 'tests/unit')]
from unit.test_direct_author_continuation import DirectAuthorContinuationTests

fixture = DirectAuthorContinuationTests()
fixture.setUp()
try:
    handler = out / 'author-continuation-runtime/src/cuhg/codex_hooks/global_dispatch.py'
    env = {**os.environ, 'PYTHONPATH': str(base / 'src'), 'PYTHONDONTWRITEBYTECODE': '1',
           'CUHG_CONTINUOUS_POLICY': str(fixture.f.root / 'absent-policy.json')}
    env.pop('CUHG_TELEMETRY_ROOT', None)
    result = subprocess.run(['/usr/bin/python3.12', '-B', str(handler), '--self-check'],
                            env=env, text=True, capture_output=True, check=True)
    assert result.stdout.strip() == 'GLOBAL_ROUTING_HOOK_SELF_CHECK_PASS'
    event = fixture.f.root / 'fixture-event.json'
    event.write_text(json.dumps(fixture.event()))
    code = """import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import global_dispatch
print(json.dumps(global_dispatch.dispatch(json.loads(Path(sys.argv[2]).read_text()), root=Path(sys.argv[3]))))
"""
    args = ['/usr/bin/python3.12', '-B', '-c', code, str(handler.parent), str(event), str(fixture.f.state)]
    first = subprocess.run(args, env=env, text=True, capture_output=True, check=True)
    allowed = json.loads(first.stdout)['hookSpecificOutput']
    assert allowed['permissionDecision'] == 'allow', allowed
    second = subprocess.run(args, env=env, text=True, capture_output=True, check=True)
    denied = json.loads(second.stdout)['hookSpecificOutput']
    assert denied['permissionDecision'] == 'deny', denied
    assert fixture.store.get_launch(fixture.id) == fixture.original
    state = json.loads(fixture.store.path.read_text())
    assert len(state['direct_author_continuations'][fixture.id]) == 1
    assert 'direct_review_closeout' not in handler.read_text()
    print(json.dumps({'status': 'PASS', 'scope': 'ISOLATED_FIXTURE_NOT_CLIENT_ACTIVATION',
        'base_authority': str(base), 'first_followup': allowed['permissionDecision'],
        'duplicate': denied['permissionDecision'], 'launch_preserved': True,
        'reviewer_overlay_included': False}, indent=2))
finally:
    fixture.doCleanups()
