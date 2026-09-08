#!/usr/bin/env python3
"""Validate R7 design structure and mock routing; never execute scientific nodes."""
from __future__ import annotations

import json
import re
from pathlib import Path


def validate(root: Path) -> dict:
    dag = json.loads((root / 'campaign_dag.json').read_text())
    rows = dag['nodes']
    nodes = {n['id']: n for n in rows}
    assert len(nodes) == len(rows), 'duplicate node ID'
    order, remaining = [], set(nodes)
    ancestors = {}
    while remaining:
        ready = sorted(i for i in remaining if set(nodes[i]['settle_after']) <= set(order))
        assert ready, 'cycle or missing predecessor'
        for i in ready:
            preds = nodes[i]['settle_after']
            ancestors[i] = set(preds).union(*(ancestors[p] for p in preds))
            order.append(i)
            remaining.remove(i)
    outputs = {}
    for n in rows:
        for cap in n['declared_outputs']:
            assert cap not in outputs, f'duplicate producer for {cap}'
            outputs[cap] = n['id']
    checks = set(re.findall(r'\| (V\d\d) \|', (root / 'VALIDATION_MATRIX.md').read_text()))
    for n in rows:
        assert n['initial_process_status'] == 'PENDING'
        assert n['initial_scientific_outcome'] == 'NOT_EVALUATED'
        assert set(n['validation_ids']) <= checks, f"missing validation for {n['id']}"
        assert n['capability_routes'], 'no eligibility route'
        for route in n['capability_routes']:
            for cap in route:
                assert cap in outputs, f'unknown capability {cap}'
                assert outputs[cap] in ancestors[n['id']], f'{cap} not supplied by a predecessor'
    assert set(nodes) - {'R7-25'} <= ancestors['R7-25'], 'orphan from final synthesis'
    for file in root.rglob('*.md'):
        for link in re.findall(r'\]\(([^)]+)\)', file.read_text()):
            if '://' not in link and not link.startswith('#'):
                target = (file.parent / link.split('#')[0]).resolve()
                assert target.exists(), f'broken document link {file.name}: {link}'

    # Explicit successful-output assumptions in metadata fixtures, never the real
    # executor emission rule or a validation of any scientific capability.
    direct_laws = {'CMB_LAW','CF4_LAW','CF4_CONDITIONAL_LAW','DESI_LAW',
                   'JWST_LAW','PROJECTED_LAW','BACKGROUND_LAW','AUX_DISTANCE_LAW'}
    factories = {'CF4_LAW_FACTORY','DESI_LAW_FACTORY','JWST_LAW_FACTORY'}
    input_caps = set(nodes['R7-00']['declared_outputs']) - {'SOURCE_BINDINGS'}
    def route_fixture(failed=(), withheld=()):
        available, result = set(), {}
        for i in order:
            n = nodes[i]
            assert all(p in result for p in n['settle_after'])
            eligible = n['always_run'] or any(set(r) <= available for r in n['capability_routes'])
            if i in failed:
                status = 'COMPLETED_FAILED_WITH_RECEIPT'
            elif not eligible:
                status = 'BLOCKED_WITH_RECEIPT'
            else:
                status = 'COMPLETED_SUCCESS'
                emits = set(n['declared_outputs']) - set(withheld)
                if i == 'R7-06':
                    if not ({'PR3_INPUT','SKY_CONTROL_INPUT'} & available and 'DONOR_TENSOR' in available):
                        emits -= {'CMB_RECORDS','CMB_LAW'}
                    if 'PROJECTED_AUX_INPUT' not in available:
                        emits.discard('PROJECTED_LAW')
                if i == 'R7-07' and 'CF4_INPUT' not in available:
                    emits -= {'CF4_RECORDS','CF4_LAW','CF4_CONDITIONAL_LAW','CF4_LAW_FACTORY','CF4_SCENARIO'}
                if i == 'R7-08':
                    if 'DESI_INPUT' not in available:
                        emits -= {'DESI_RECORDS','DESI_LAW','DESI_LAW_FACTORY','DESI_SCENARIO'}
                    if 'BACKGROUND_AUX_INPUT' not in available:
                        emits.discard('BACKGROUND_LAW')
                if i == 'R7-09':
                    if 'JWST_INPUT' not in available:
                        emits -= {'JWST_RECORDS','JWST_LAW','JWST_LAW_FACTORY','JWST_SCENARIO'}
                    if 'DISTANCE_AUX_INPUT' not in available:
                        emits -= {'AUX_DISTANCE_RECORDS','AUX_DISTANCE_LAW'}
                if i == 'R7-10':
                    if not direct_laws & available:
                        emits -= {'ADMITTED_EXPERIMENTS','JOINT_LAW','SUBSET_LAWS','MARGINAL_EXPERIMENT_FAMILY'}
                    if not factories & available:
                        emits.discard('EXPERIMENT_FACTORIES')
                if i == 'R7-17' and not ('EXPERIMENT_FACTORIES' in available and
                        {'R3_BENCHMARK','SUPPORTED_EXTERNAL_TRANSFER'} & available):
                    emits.discard('MODEL_BOUND_EXPERIMENTS')
                available.update(emits)
            result[i] = status
        assert result['R7-25'] == 'COMPLETED_SUCCESS'
        return result, available

    baseline, _ = route_fixture()
    assert all(v == 'COMPLETED_SUCCESS' for v in baseline.values())
    native_failed, _ = route_fixture(failed={'R7-15','R7-16'})
    assert all(native_failed[i] == 'COMPLETED_SUCCESS' for i in ['R7-11','R7-14','R7-17'])
    no_desi, caps = route_fixture(withheld={'DESI_INPUT'})
    assert 'DESI_LAW' not in caps and 'BACKGROUND_LAW' in caps
    assert no_desi['R7-07'] == no_desi['R7-09'] == 'COMPLETED_SUCCESS'
    carrier_failed, caps = route_fixture(withheld={'DONOR_TENSOR'})
    assert 'CMB_RECORDS' not in caps and carrier_failed['R7-11'] == 'BLOCKED_WITH_RECEIPT'
    assert carrier_failed['R7-07'] == 'COMPLETED_SUCCESS'
    chart_failed, caps = route_fixture(withheld={'DONOR_KRYLOV'})
    assert 'CMB_RECORDS' in caps and chart_failed['R7-11'] == 'COMPLETED_SUCCESS'
    extended_failed, _ = route_fixture(withheld={'MASK_BOUND_VERIFIED','FOUR_AXIS_CAS'})
    assert extended_failed['R7-11'] == 'COMPLETED_SUCCESS'
    no_joint, _ = route_fixture(withheld={'JOINT_LAW'})
    assert no_joint['R7-19'] == 'COMPLETED_SUCCESS'
    all_missing, _ = route_fixture(withheld=input_caps)
    assert all_missing['R7-19'] == 'BLOCKED_WITH_RECEIPT'
    root_failed, _ = route_fixture(failed={'R7-00'})
    assert root_failed['R7-19'] == 'BLOCKED_WITH_RECEIPT'
    cf4_only = input_caps - {'CF4_INPUT'}
    conditional, caps = route_fixture(withheld=cf4_only | {'CF4_LAW','CF4_LAW_FACTORY','CF4_SCENARIO'})
    assert 'CF4_CONDITIONAL_LAW' in caps and conditional['R7-19'] == 'COMPLETED_SUCCESS'
    scenario, caps = route_fixture(withheld=cf4_only | {'CF4_LAW','CF4_CONDITIONAL_LAW','CF4_LAW_FACTORY'})
    assert 'CF4_SCENARIO' in caps and scenario['R7-19'] == 'BLOCKED_WITH_RECEIPT'
    factory_only = cf4_only | {'CF4_LAW','CF4_CONDITIONAL_LAW'}
    unbound, caps = route_fixture(withheld=factory_only | {'R3_BENCHMARK','SUPPORTED_EXTERNAL_TRANSFER'})
    assert 'EXPERIMENT_FACTORIES' in caps and 'ADMITTED_EXPERIMENTS' not in caps
    assert unbound['R7-19'] == 'BLOCKED_WITH_RECEIPT'
    bound, caps = route_fixture(withheld=factory_only)
    assert 'MODEL_BOUND_EXPERIMENTS' in caps and bound['R7-19'] == 'COMPLETED_SUCCESS'
    assert bound['R7-13'] == 'COMPLETED_SUCCESS' and 'MES_REGION_METHOD' in caps
    wmap_only, caps = route_fixture(withheld=(input_caps - {'SKY_CONTROL_INPUT'}) | {'CMB_LAW'})
    assert 'CMB_RECORDS' in caps and wmap_only['R7-11'] == 'COMPLETED_SUCCESS'
    union3_only, caps = route_fixture(withheld=input_caps - {'DISTANCE_AUX_INPUT'})
    assert 'AUX_DISTANCE_LAW' in caps and 'JWST_LAW' not in caps
    assert union3_only['R7-19'] == 'COMPLETED_SUCCESS'

    # Exact-scope/evidence metadata predicates; actual binding/domain proofs are
    # Local Codex work, not supplied by these sample booleans.
    fields = ('experiment_id','law_id','model_id','dataset_ids','conventions','version',
              'method_id','method_config_id')
    scope = dict(zip(fields, ('e','l','m',('PR3',),'c','v','method','config')))
    matches = lambda a,b: all(a[k] == b[k] for k in fields)
    assert matches(scope, dict(scope))
    for field in fields:
        other = dict(scope); other[field] = 'mismatched'
        assert not matches(scope, other), f'scope mismatch accepted: {field}'
    def evidence_eligible(e):
        return (e['kind'] in {'EXACT_ACCEPTANCE_PROOF','CALIBRATED_SIMULATOR'}
                and e['domain_contains'] and e['numeric_valid'] and e['conditioning_matches'])
    exact = dict(kind='EXACT_ACCEPTANCE_PROOF', domain_contains=True,
                 numeric_valid=True, conditioning_matches=True, simulation_calibration=False)
    assert evidence_eligible(exact)
    for field, value in [('kind','FACTORY_ONLY'),('domain_contains',False),
                         ('numeric_valid',False),('conditioning_matches',False)]:
        other = dict(exact); other[field] = value
        assert not evidence_eligible(other)
    return {'status':'PASS_DESIGN_STRUCTURE_ONLY','nodes':len(rows),
            'validation_rows':len(checks),'routing_fixtures':15,'scope_mismatch_fixtures':8,
            'evidence_scope_fixtures':5,'scientific_nodes_executed':0,
            'limitations':['Metadata routing only; does not implement a scientific executor, prove physical laws, or verify calibration records.']}


if __name__ == '__main__':
    print(json.dumps(validate(Path(__file__).resolve().parent), indent=2))
