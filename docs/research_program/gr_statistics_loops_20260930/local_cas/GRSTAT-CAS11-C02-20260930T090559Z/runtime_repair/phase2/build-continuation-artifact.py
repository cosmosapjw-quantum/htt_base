"""Build a two-file source overlay; never install or alter an authority bundle."""
import difflib
import hashlib
import json
from pathlib import Path

REPO = Path('/home/cosmosapjw/codex_global_harness')
OUT = Path('/tmp/cas11-c02-routing-repair-20260930')
BASE = Path('/mnt/sn850x2t/local_ai_foundry/60_runtime/cuhg/policy-authorities/3b243df626bce98ee31ba899d48c9bceddef1bfd')
REL = 'src/cuhg/codex_hooks/global_dispatch.py'
HELPER = 'src/cuhg/codex_hooks/direct_author_continuation.py'
bundle = OUT / 'author-continuation-runtime'
source = (REPO / REL).read_text()
review = """                elif not isinstance(context, dict):
                    from cuhg.codex_hooks.direct_review_closeout import consume
                    consume(root, launch_id=binding['launch_id'], session_id=session,
                        child_id=binding['child']['child_id'], client_cwd=event.get('cwd'),
                        tool_use_id=event.get('tool_use_id'), message=input_.get('message'))
                else:
                    from cuhg.models.native_workspace_job import consume_continuation
"""
original = """                else:
                    if not isinstance(context, dict):
                        raise ValueError('CONTINUATION_RESOURCE_BINDING_REQUIRED')
                    from cuhg.models.native_workspace_job import consume_continuation
"""
assert source.count(review) == 1, 'Reviewer integration changed; preserve and inspect.'
standalone = source.replace(review, original)
# The script directory is on sys.path; every other cuhg import remains in BASE.
standalone = standalone.replace('from cuhg.codex_hooks.direct_author_continuation import',
                                'from direct_author_continuation import')
assert 'direct_review_closeout' not in standalone
(bundle / REL).parent.mkdir(parents=True, exist_ok=True)
(bundle / REL).write_text(standalone)
(bundle / HELPER).write_bytes((REPO / HELPER).read_bytes())

def diff(before, after, name):
    return ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
        fromfile='a/' + name if before else '/dev/null', tofile='b/' + name))

files = [REL, HELPER, 'tests/unit/test_registered_child_author_routing.py',
         'tests/unit/test_direct_author_continuation.py']
manifest = json.loads((OUT / 'source-baseline.json').read_text())
for name, digest in manifest['files'].items():
    assert hashlib.sha256((OUT / 'baseline' / name).read_bytes()).hexdigest() == digest
total = ''
for name in files:
    before = (OUT / 'baseline' / name).read_text() if name in manifest['files'] else ''
    total += diff(before, (REPO / name).read_text(), name)
(OUT / 'repair-total.diff').write_text(total)
(OUT / 'runtime-author-continuation.patch').write_text(
    diff((BASE / REL).read_text(), standalone, REL) + diff('', (REPO / HELPER).read_text(), HELPER))
command = f'env PYTHONPATH={BASE}/src /usr/bin/python3.12 {bundle / REL}'
(bundle / 'HOOK_COMMAND.txt').write_text(command + '\n')
(bundle / 'manifest.json').write_text(json.dumps({
    'status': 'STAGED_NOT_INSTALLED', 'base_authority': str(BASE), 'hook_command': command,
    'event': 'PreToolUse', 'unrelated_reviewer_changes_included': False,
    'files': {name: hashlib.sha256((bundle / name).read_bytes()).hexdigest() for name in (REL, HELPER)},
}, indent=2) + '\n')
print(command)
