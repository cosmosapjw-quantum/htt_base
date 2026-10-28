#!/usr/bin/env python3
"""Check the finite convergence package; no live runtime read, write or launch.

Scheduling cases below are explicitly synthetic in-memory states. They test the
production controller API, not scientific completion or qualification of a task.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import yaml

BASE = 'bdead6a8f51282ca647224b460b0f65de085568b'
PACKAGE = Path('docs/research_program/observational_publication_20261015/CONVERGENCE_20261028')
IDS = ('R37-00-FIRST-REPORT', 'R37-01-RADIATION', 'R37-02-KINEMATICS',
       'R37-03-HUBBLE', 'R37-04-CLASSIFICATION', 'R37-05-FINAL-REPORT')
NEW_PRS = {'PR-R37-CONVERGENCE', *('PR-' + key for key in IDS)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return yaml.safe_load(path.read_text())


def base_object(root, relative):
    return yaml.safe_load(subprocess.check_output(
        ['git', 'show', BASE + ':' + str(relative)], cwd=root, text=True))


def source_path(root, value):
    require(isinstance(value, str) and value, 'empty source path')
    path = Path(value)
    require(not path.is_absolute() and '..' not in path.parts,
            'source must be repository-relative: ' + value)
    resolved = (root / path).resolve()
    require(resolved.is_relative_to(root), 'source escapes repository: ' + value)
    return resolved


def source_identity(sources):
    return 'sha256:' + hashlib.sha256(json.dumps(
        sources, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def check_sources(root, frontier, manifest):
    files = manifest['files']
    paths = [row['path'] for row in files]
    require(len(paths) == len(set(paths)), 'duplicate manifest path')
    indexed = {row['path']: row for row in files}
    for row in files:
        path = source_path(root, row['path'])
        require(path.is_file(), 'missing evidence: ' + row['path'])
        require(hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'],
                'changed evidence: ' + row['path'])
        if 'size_bytes' in row:
            require(path.stat().st_size == row['size_bytes'], 'wrong evidence size: ' + row['path'])
    for task in frontier['tasks']:
        sources = task['input_sources']
        require(sources and len(sources) <= 256, 'unbounded/empty task inputs: ' + task['id'])
        require(len({row['path'] for row in sources}) == len(sources),
                'duplicate task input: ' + task['id'])
        for row in sources:
            require(row['path'] in indexed, 'task input outside evidence manifest: ' + row['path'])
            require(row['sha256'] == indexed[row['path']]['sha256'],
                    'task/manifest hash disagreement: ' + row['path'])
        require(task['input_identity'] == source_identity(sources),
                'task input identity disagrees with compact canonical source list: ' + task['id'])
        for field in ('source_contract', 'execution_spec'):
            require(task[field] in {row['path'] for row in sources},
                    field + ' absent from task-bound sources: ' + task['id'])
    return {'manifest_files': len(files),
            'task_input_counts': {task['id']: len(task['input_sources']) for task in frontier['tasks']}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[5])
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / 'scripts/codex_harness'))
    import research_controller as rc
    import native_routing
    import publication_frontier_preflight as preflight

    results = []

    def run(name, function):
        try:
            detail = function()
            results.append({'check': name, 'status': 'PASS', 'detail': detail})
        except Exception as error:
            results.append({'check': name, 'status': 'FAIL', 'error': str(error),
                            'error_type': type(error).__name__})

    frontier = load(root / PACKAGE / 'FRONTIER.json')
    output = load(root / PACKAGE / 'OUTPUT_DAG.json')
    contract = load(root / PACKAGE / 'RUN_CONTRACT.json')
    manifest = load(root / PACKAGE / 'EVIDENCE_MANIFEST.json')
    policy = native_routing.load_policy(root / 'docs/harness/NATIVE_ROUTING_POLICY_V1.json')
    profiles = {(row['requested']['model'], row['requested']['effort']) for row in policy['routes'].values()}
    hints = {'preferred_tasks': tuple(contract['preferred_tasks']),
             'deferred_tasks': tuple(contract['deferred_tasks']),
             'allow_discovery': contract['new_adaptive_discovery']}

    def originals():
        path = PACKAGE.parent / 'PUBLICATION_DAG.json'
        old, current = base_object(root, path), load(root / path)
        require(len(old['nodes']) == len(current['nodes']) == 42, 'original node count changed')
        require(len(old['papers']) == len(current['papers']) == 6, 'original paper count changed')
        require(old['nodes'] == current['nodes'] and old['papers'] == current['papers'],
                'original scientific node/paper contracts changed')
        return {'nodes_preserved': 42, 'papers_preserved': 6, 'frozen_base': BASE}

    def canonical():
        relative = Path('docs/codex_handoff/pr_backlog.yaml')
        old, current = base_object(root, relative), load(root / relative)
        old_cards = {row['id']: row for row in old['prs']}
        cards = {row['id']: row for row in current['prs']}
        require(len(old_cards) == 266, 'unexpected frozen canonical inventory')
        require(len(cards) == len(current['prs']), 'duplicate canonical card')
        require(set(cards) - set(old_cards) == NEW_PRS, 'new canonical scope is not exactly seven cards')
        require(all(cards.get(key) == value for key, value in old_cards.items()),
                'old canonical card deleted or changed')
        relative = Path('docs/codex_handoff/pr_status.yaml')
        old_status, status = base_object(root, relative), load(root / relative)
        for key, value in old_status.items():
            if key in {'generated_on', 'notes'}:
                continue
            updated = status.get(key)
            if isinstance(value, list):
                updated = [item for item in updated if not isinstance(item, str) or item not in NEW_PRS]
            elif isinstance(value, dict):
                updated = {item: data for item, data in updated.items() if item not in NEW_PRS}
            elif isinstance(value, str) and updated in NEW_PRS:
                raise ValueError('old scalar status replaced: ' + key)
            require(value == updated, 'old status/history changed: ' + key)
        for mirror in ('machine_readable/pr_backlog.yaml', 'machine_readable/pr_backlog.json'):
            require(load(root / mirror) == current, 'canonical mirror differs: ' + mirror)
        require(load(root / 'machine_readable/pr_status.yaml') == status, 'status mirror differs')
        return {'old_cards_preserved': 266, 'new_cards': sorted(NEW_PRS), 'status_mirrors_equal': True}

    def graph():
        rows = frontier['tasks']
        require(tuple(row['id'] for row in rows) == IDS, 'finite task inventory/order changed')
        require(frontier['source_head'] == output['source_head'] == contract['source_head'] == BASE,
                'frozen source identities disagree')
        require(frontier['original42_effect'] == 'none', 'frontier promotes original acceptance')
        require(output['units'] == rows and output['task_count'] == 6, 'output/frontier units disagree')
        require(rows[0]['requires'] == {'all': []}, 'first report blocked on old scientific holds')
        baseline = {'all': [{'task_id': IDS[0], 'evidence': 'qualified',
                             'product': 'convergence_baseline_report'}]}
        for row in rows[1:]:
            require(row['requires'] == baseline, 'unexpected success barrier: ' + row['id'])
        for row in rows:
            require(row['promotes_original_acceptance'] is False and row['initial_state'] == 'ready',
                    'unexecuted task promoted: ' + row['id'])
            require(row['owned_paths'] == [str(PACKAGE / 'products' / row['id'])],
                    'task owns another unit or historical source: ' + row['id'])
        require(output['edges'] == [{'from': IDS[0], 'to': key, 'type': 'qualified_report'} for key in IDS[1:]],
                'report prerequisite edges differ')
        require(output['science_to_final_edges'] == [
            {'from': key, 'to': IDS[-1], 'type': 'consume_if_qualified_otherwise_preserve_hold'}
            for key in IDS[1:-1]], 'final report conditional consumption differs')
        require(contract['preferred_tasks'] == list(IDS[:-1]) and contract['deferred_tasks'] == [IDS[-1]],
                'delivery preference/defer contract changed')
        require(contract['new_adaptive_discovery'] is False, 'finite scope permits new discovery')
        return {'units': 6, 'first_report_is_root': True, 'final_all_science_success_barrier': False}

    def fixture():
        tasks = [{'id': key, 'goal': 'fixture legacy continuation', 'acceptance': 'fixture only',
                  'input_identity': 'fixture-input', 'kind': 'numeric'}
                 for key in ('LEGACY-READY', 'LEGACY-HOLD')]
        state = rc.initialize({'campaign_id': 'CONVERGENCE-IN-MEMORY-ONLY', 'tasks': tasks}, 'fixture only')
        state['tasks']['LEGACY-HOLD'].update(state='held', hold={'class': 'input'})
        state['tasks']['LEGACY-HOLD']['ultra_used'] = ['historical-one-use-witness']
        state['ultra_repairs'] = {'historical-allowance': {'used': True}}
        state['events'].append({'type': 'historical-fixture-witness'})
        rc.enable_adaptive(state, 'historical fixture adaptive authorization')
        return state

    def appended():
        state = fixture()
        rc.append_frontier(state, frontier, frontier['authorization'])
        return state

    def preservation():
        state = fixture()
        old_packet = rc.next_packet(state, policy, profiles)
        before = copy.deepcopy(state)
        rc.append_frontier(state, frontier, frontier['authorization'])
        require(all(state['tasks'][key] == row for key, row in before['tasks'].items()), 'append changed old tasks')
        for key, value in before.items():
            if key not in {'tasks', 'frontiers', 'events'}:
                require(state[key] == value, 'append changed protected state: ' + key)
        require(state['events'][:-1] == before['events'], 'append rewrote history')
        require(len(state['tasks']) == len(before['tasks']) + 6, 'append task count changed')
        frozen = copy.deepcopy(state)
        require(rc.next_packet(state, policy, profiles, **hints) == old_packet, 'preferences preempt active packet')
        require(state == frozen, 'packet replay changes accounting')
        rc.acknowledge(state, old_packet['packet_id'], 'synthetic-fixture-agent')
        frozen = copy.deepcopy(state)
        require(rc.next_packet(state, policy, profiles, **hints)['status'] == 'AWAITING_NATIVE_OUTCOME',
                'running writer bypassed')
        require(state == frozen, 'running writer accounting changed')
        try:
            rc.append_frontier(state, frontier, frontier['authorization'])
        except rc.ControllerError:
            pass
        else:
            raise ValueError('duplicate frontier appended')
        require(state == frozen, 'rejected repeat append changed state')
        return {'old_packet_and_writer_preserved': True, 'one_use_and_adaptive_history_preserved': True,
                'repeat_append_rejected_without_mutation': True}

    def scheduling():
        state = appended()
        require(set(rc.summary(state)['ready']) == {'LEGACY-READY', IDS[0]}, 'report dependencies bypassed')
        require(rc.next_packet(copy.deepcopy(state), policy, profiles, **hints)['task_id'] == IDS[0],
                'first report does not precede legacy work')
        state['tasks'][IDS[0]]['state'] = 'completed'
        require(rc.summary(state)['ready'] == ['LEGACY-READY'], 'completion alone passed qualification gate')
        state['tasks'][IDS[0]]['qualified_products'] = ['convergence_baseline_report']
        require(set(rc.summary(state)['ready']) == {'LEGACY-READY', *IDS[1:]}, 'qualified baseline not reusable')
        require(rc.next_packet(copy.deepcopy(state), policy, profiles, **hints)['task_id'] == IDS[1],
                'science preference or final deferral failed')
        for key in IDS[1:-1]:
            state['tasks'][key].update(state='held', hold={'class': 'input'})
        require(rc.next_packet(copy.deepcopy(state), policy, profiles, **hints)['task_id'] == 'LEGACY-READY',
                'nonpreferred existing work starved by final report')
        state['tasks']['LEGACY-READY'].update(state='held', hold={'class': 'input'})
        require(rc.next_packet(copy.deepcopy(state), policy, profiles, **hints)['task_id'] == IDS[-1],
                'final report blocked by scientific holds')
        state['tasks'][IDS[-1]]['state'] = 'completed'
        before = copy.deepcopy(state)
        result = rc.next_packet(state, policy, profiles, **hints)
        require(result['status'] == 'HOLD_UNRESOLVED_BRANCHES' and state == before,
                'finite exhaustion changed state or started a new frontier')
        discovery = rc.next_packet(copy.deepcopy(state), policy, profiles)
        require(discovery['phase'] == 'discovery', 'negative control does not exercise adaptive exhaustion')
        return {'baseline_requires_qualified_product': True, 'legacy_work_continues': True,
                'final_emits_with_external_holds': True, 'no_discovery_is_effective_and_preserves_history': True}

    def source_negatives():
        bad = copy.deepcopy(frontier)
        bad['tasks'][0]['input_sources'][0]['sha256'] = '0' * 64
        try:
            check_sources(root, bad, manifest)
        except ValueError:
            pass
        else:
            raise ValueError('changed direct source hash accepted')
        bad = copy.deepcopy(frontier)
        bad['tasks'][0]['input_identity'] = 'sha256:' + '0' * 64
        try:
            check_sources(root, bad, manifest)
        except ValueError:
            pass
        else:
            raise ValueError('wrong canonical source identity accepted')
        return {'changed_hash_rejected': True, 'wrong_identity_rejected': True}

    run('original_science_preserved', originals)
    run('canonical_cards_statuses_and_mirrors', canonical)
    run('finite_dependency_and_delivery_contract', graph)
    run('manifest_and_direct_source_bindings', lambda: check_sources(root, frontier, manifest))
    run('source_binding_negative_controls', source_negatives)
    run('production_preflight', lambda: preflight.check(root, frontier_path=PACKAGE/'FRONTIER.json',
                                                       manifest_path=PACKAGE/'EVIDENCE_MANIFEST.json'))
    run('append_and_active_packet_preservation', preservation)
    run('ready_order_legacy_continuation_and_finite_exhaustion', scheduling)
    report = {'schema': 'htt.convergence_package_validation/1', 'source_head': BASE,
              'status': 'PASS' if all(row['status'] == 'PASS' for row in results) else 'FAIL',
              'checks': results, 'live_runtime_read_or_mutation': False, 'native_launch': False,
              'scientific_acceptance_promotion': False,
              'scope': 'Static source bindings and synthetic production-controller integration; no observational fit or scientific qualification.'}
    print(json.dumps(report, indent=2))
    return 0 if report['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
