"""Disposable, in-memory tests of unchanged controller bodies; no live state.

The only AST omissions are the unavailable router import and __main__ launch.
No routing, native dispatch, installation, or scientific admission is claimed.
"""
from pathlib import Path
import ast
import copy
import hashlib
import json
import sys

HERE = Path(__file__).resolve().parent
WORK = HERE.parents[1]
SOURCE = WORK / 'baseline/scripts/codex_harness/research_controller.py'

def load_controller():
    tree = ast.parse(SOURCE.read_text())
    omitted = []
    body = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == 'native_routing':
            omitted.append('native_routing import (routing not exercised)')
        elif isinstance(node, ast.If) and ast.unparse(node.test) == "__name__ == '__main__'":
            omitted.append('__main__ invocation (CLI not exercised)')
        else:
            body.append(node)
    tree.body = body
    ns = {'__name__': 'htt_controller_disposable', '__file__': str(SOURCE)}
    exec(compile(tree, str(SOURCE), 'exec'), ns)
    return ns, omitted

RC, OMITTED = load_controller()
checks = []

def passes(name, fn):
    fn()
    checks.append({'name': name, 'result': 'PASS'})

def rejects(fn, text):
    try:
        fn()
    except RC['ControllerError'] as exc:
        assert text in str(exc), str(exc)
        return
    raise AssertionError('expected rejection: ' + text)

def old_state():
    state = RC['initialize']({'campaign_id': 'DISPOSABLE', 'tasks': [{
        'id': 'OLD', 'goal': 'Preserved experiment', 'acceptance': 'Original acceptance',
        'input_identity': 'original input', 'kind': 'theory'
    }]}, 'disposable test')
    state['tasks']['OLD'].update(state='held', attempt=7,
        history=[{'packet_id': 'historical', 'result': {'outcome': 'blocker'}}],
        hold={'reason': 'one-use exhausted'}, ultra_used=['OLD-ULTRA'])
    state['ultra_repairs']['OLD-ULTRA'] = {'task_id': 'OLD', 'packet_id': 'historical'}
    state['events'].append({'type': 'preserved_event'})
    return state

def task(key, requires=None):
    return {'id': key, 'goal': 'Construct a distinct covariance pushforward',
        'acceptance': 'Source-qualified operator and scoped independent review',
        'input_identity': 'actual test fixture', 'kind': 'theory',
        'contract_origin': 'new_conditional_research', 'promotes_original_acceptance': False,
        'requires': {'all': []} if requires is None else requires,
        'owned_paths': ['scoped/products/' + key],
        'input_sources': [{'path': str(SOURCE), 'sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(), 'role': 'fixture'}],
        'semantic_delta': {'kind': 'method', 'before': {'operator': 'working diagonal covariance'},
            'after': {'operator': 'joint source covariance pushforward', 'target': key},
            'discriminator': 'full cross-window covariance and kernel validation',
            'scope': 'new conditional result'}}

def frontier(*tasks, key='F'):
    return {'frontier_id': key, 'tasks': list(tasks)}

def append_preserves():
    s = old_state(); before = copy.deepcopy(s)
    RC['append_frontier'](s, frontier(task('NEW')), 'disposable authorization')
    assert s['tasks']['OLD'] == before['tasks']['OLD']
    for key, value in before.items():
        if key not in {'tasks','frontiers','events'}: assert s[key] == value, key
    assert s['events'][:len(before['events'])] == before['events']
    assert RC['summary'](s)['ready'] == ['NEW']
    assert RC['summary'](s)['original_science']['admission'] == 'UNCHANGED_NOT_GRANTED_BY_CONTROLLER'
    checks.append({'name': 'old held history and consumed ultra record retained', 'result': 'PASS'})

def append_once():
    s = old_state(); f = frontier(task('NEW'))
    RC['append_frontier'](s, f, 'test'); before = copy.deepcopy(s)
    rejects(lambda: RC['append_frontier'](s,f,'test'), 'frontier already appended')
    assert s == before

def product_dependency():
    s = old_state()
    a=task('A'); b=task('B', {'all':[{'task_id':'A','evidence':'qualified','product':'covariance_product'}]})
    RC['append_frontier'](s,frontier(a,b),'test')
    assert RC['summary'](s)['ready'] == ['A']
    s['tasks']['A']['state']='completed'
    s['tasks']['A']['qualified_products']=[]
    assert RC['summary'](s)['ready'] == []
    s['tasks']['A']['qualified_products']=['unrelated_product']
    assert RC['summary'](s)['ready'] == []
    s['tasks']['A']['qualified_products']=['covariance_product']
    assert RC['summary'](s)['ready'] == ['B']

def no_promotion():
    s=old_state(); before=copy.deepcopy(s); t=task('NEW');t['promotes_original_acceptance']=True
    rejects(lambda:RC['append_frontier'](s,frontier(t),'test'),'preserve original scientific acceptance')
    assert s==before

def no_completed_import():
    s=old_state(); t=task('NEW');t['initial_state']='completed';t['reuse_evidence']='old review'
    rejects(lambda:RC['append_frontier'](s,frontier(t),'test'),'actual execution and review')

def same_action_rename():
    s=old_state(); a=task('A');RC['append_frontier'](s,frontier(a),'test')
    b=copy.deepcopy(a);b['id']='B';b['owned_paths']=['elsewhere'];b['input_identity']='changed label'
    rejects(lambda:RC['append_frontier'](s,frontier(b,key='F2'),'test'),'logical research action already exists')

def metadata_only_change():
    s=old_state(); t=task('NEW');t['semantic_delta'].update(before={'input_identity':'old'},after={'input_identity':'new'})
    rejects(lambda:RC['append_frontier'](s,frontier(t),'test'),'label/hash/identity change alone')

def cycle_rejected():
    s=old_state();before=copy.deepcopy(s)
    a=task('A',{'all':[{'task_id':'B','evidence':'completed'}]})
    b=task('B',{'all':[{'task_id':'A','evidence':'completed'}]})
    rejects(lambda:RC['append_frontier'](s,frontier(a,b),'test'),'obligation dependency cycle')
    assert s==before

def source_shape_difference():
    s=old_state();t=task('NEW')
    RC['append_frontier'](s,frontier(t),'test')
    rejects(lambda:RC['_source_refs'](t['input_sources']),'source reference must be a string')

def append_does_not_validate_source_bytes():
    s=old_state();t=task('NEW');t['input_sources']=[{'path':'definitely_missing_fixture','sha256':'0'*64}]
    RC['append_frontier'](s,frontier(t),'test')
    assert 'NEW' in s['tasks']

for name, fn in [
    ('append preserves historical state and makes distinct root ready',append_preserves),
    ('duplicate frontier rejected without mutation',append_once),
    ('exact qualified product gates dependent readiness',product_dependency),
    ('original acceptance promotion rejected',no_promotion),
    ('new completed import rejected',no_completed_import),
    ('same logical action rename rejected',same_action_rename),
    ('metadata-only scientific delta rejected',metadata_only_change),
    ('typed obligation cycle rejected transactionally',cycle_rejected),
    ('direct append versus adaptive source shape mismatch reproduced',source_shape_difference),
    ('append structural validation does not replace source preflight',append_does_not_validate_source_bytes)
]: passes(name,fn)

result={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'source_git_commit':'a55036ad09c53a9215dee3282e425d37cfb95443',
    'method':'Unchanged controller AST bodies; router import and CLI invocation omitted only',
    'omitted':OMITTED,'checks':checks,'check_count':len(checks),
    'live_state_read':False,'live_state_mutation':False,'native_dispatch':False,
    'full_module_import_or_CLI_test':False,'scientific_acceptance':False}
(HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
