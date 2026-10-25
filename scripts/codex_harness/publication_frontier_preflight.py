#!/usr/bin/env python3
"""Read-only uptake check for R32; the existing controller alone appends state."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REL = 'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def located(root, value):
    path = Path(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('repository-relative source/owned path required: '+value)
    resolved = (root/path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError('path escapes repository: '+value)
    return resolved

def overlaps(a, b):
    a, b = Path(a), Path(b)
    return a == b or a in b.parents or b in a.parents

def check(root, state=None):
    import research_controller as rc
    root = Path(root).resolve()
    frontier = json.loads((root/REL/'FRONTIER.json').read_text())
    manifest_path = root/REL/'EVIDENCE_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text())
    for row in manifest['files']:
        path = located(root, row['path'])
        if sha(path) != row['sha256']:
            raise ValueError('changed evidence: '+row['path'])
    owned = []
    for task in frontier['tasks']:
        for row in task['input_sources']:
            if sha(located(root,row['path'])) != row['sha256']:
                raise ValueError('changed task input: '+row['path'])
        for path in task['owned_paths']:
            located(root,path)
            if not path.startswith(REL+'/products/'+task['id']+'/') and path != REL+'/products/'+task['id']:
                raise ValueError('write ownership outside new task product: '+path)
            if any(overlaps(path, prior) for prior in owned):
                raise ValueError('overlapping new task outputs: '+path)
            owned.append(path)
    result={'schema':'htt.publication_frontier_preflight/1','writes_state':False,
            'frontier_id':frontier['frontier_id'],'frontier_identity':rc.digest(frontier),
            'evidence_files_verified':len(manifest['files']),
            'candidate_root_tasks':[t['id'] for t in frontier['tasks'] if t['requires']=={'all':[]}],
            'original42_effect':'none','state_observed':state is not None,
            'next_action':'At the current host checkpoint, append-frontier once, then actual next/spawn/ack/record/review/next.'}
    # Validate the same controller API even without access to the live state.
    current = copy.deepcopy(state) if state is not None else rc.initialize(
        {'campaign_id':'PREFLIGHT_ONLY','tasks':[{'id':'PREFLIGHT-ANCHOR','goal':'validate','acceptance':'validate','input_identity':'fixture','initial_state':'completed','reuse_evidence':'preflight only'}]},
        'in-memory validation only')
    before = copy.deepcopy(current)
    already = [f for f in current.get('frontiers',[]) if f['frontier']['frontier_id']==frontier['frontier_id']]
    if already:
        if len(already)!=1 or already[0]['identity']!=rc.digest(frontier):
            raise ValueError('same frontier ID has different frozen content; do not reset or rename to replay')
        result['status']='ALREADY_APPENDED'
        result['next_action']='Do not append again. Continue existing next/spawn/ack/record/review/next with actual task states.'
    else:
        for old in current['tasks'].values():
            if old['state'] in {'planned','running'}:
                for prior in old['spec'].get('owned_paths',[]):
                    if any(overlaps(prior,path) for path in owned):
                        raise ValueError('active writer overlaps new product paths; finish/checkpoint existing writer first: '+prior)
        rc.append_frontier(current,frontier,frontier['authorization'])
        # Every old object stays intact; only the task map, frontier list and
        # append event may grow. No state write or launch occurs in this tool.
        if any(current['tasks'][key]!=value for key,value in before['tasks'].items()):
            raise ValueError('append changed historical task')
        for key,value in before.items():
            if key not in {'tasks','frontiers','events'} and current[key]!=value:
                raise ValueError('append changed protected state: '+key)
        if current['events'][:len(before['events'])]!=before['events']:
            raise ValueError('append changed event history')
        result['status']='STATIC_VALIDATED' if state is None else 'APPEND_READY'
    result['active_tasks']=[key for key,t in before['tasks'].items() if t['state'] in {'planned','running'}]
    if result['active_tasks']:
        result['dispatch_rule']='Preserve active packet; controller next waits/replays it. No competing worker or forced cancellation.'
    result['runtime_original_progress']='read existing controller summary; this preflight does not infer original physical completion'
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,help='Existing state, read only; omit for static validation')
    args=parser.parse_args()
    state=json.loads(args.state.read_text()) if args.state else None
    print(json.dumps(check(ROOT,state),indent=2))

if __name__=='__main__':
    try: main()
    except (ValueError,OSError,KeyError) as exc:
        raise SystemExit('PUBLICATION_PREFLIGHT_ERROR: '+str(exc))
