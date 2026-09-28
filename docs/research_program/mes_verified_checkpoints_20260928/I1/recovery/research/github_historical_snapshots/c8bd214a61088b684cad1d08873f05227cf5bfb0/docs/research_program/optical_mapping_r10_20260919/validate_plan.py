#!/usr/bin/env python3
"""Validate this plan's graph and exact input inheritance; never execute science."""
from __future__ import annotations
from collections import defaultdict, deque
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def require(test, message):
    if not test:
        raise AssertionError(message)

def main():
    dag = json.loads((HERE / 'campaign_dag.json').read_text())
    original_bytes = (ROOT / dag['inherited']['path']).read_bytes()
    original = json.loads(original_bytes)
    require(hashlib.sha256(original_bytes).hexdigest() == dag['inherited']['sha256'], 'R9 byte identity')
    require(dag['nodes'][:24] == original['nodes'], 'R9 nodes/actions/acceptance changed')
    require(dag['alpha'] == original['alpha'], 'R9 alpha changed')
    require(sum(dag['alpha'][k] for k in ['CMB','CF4','distance_calibration','DESI']) == 0.05, 'family alpha')
    require(sum(dag['alpha']['CMB_suballocation'][k] for k in ['morphology_test','candidate_confidence']) == dag['alpha']['CMB'], 'CMB alpha')
    require(dag['alpha']['no_redistribution'], 'missing-block donation')
    nodes = {n['id']: n for n in dag['nodes']}
    require(len(nodes) == len(dag['nodes']) == 36, 'unique node count')
    producers = defaultdict(set)
    for n in nodes.values():
        for cap in n['may_produce']:
            producers[cap].add(n['id'])
        for a in n.get('actions', []):
            require(a['produces'] in n['may_produce'], f'undeclared action output {n["id"]}')
    for cap, ids in producers.items():
        if len(ids) > 1:
            require(sorted(ids) == sorted(dag['alternative_producers'].get(cap, [])), f'undeclared alternatives {cap}')
    external = set(dag['external_capabilities'])
    adjacency = defaultdict(set)
    indegree = dict.fromkeys(nodes, 0)
    for n in nodes.values():
        reqs = list(n.get('requires_all', []))
        for group in n.get('requires_any', []):
            require(bool(group), 'empty OR group')
            reqs.extend(group)
        for a in n.get('actions', []):
            reqs.extend(a.get('requires_all', []))
        for c in n.get('conditional_requirements', []):
            require(c['selector'] == 'uses_T9_hierarchy', 'unknown method selector')
            reqs.extend(c['requires_all'])
        for cap in reqs:
            require(cap in producers or cap in external, f'dangling capability {cap}')
            for parent in producers.get(cap, ()):
                if n['id'] not in adjacency[parent]:
                    adjacency[parent].add(n['id'])
                    indegree[n['id']] += 1
    q = deque(k for k,v in indegree.items() if v == 0)
    order = []
    while q:
        i=q.popleft();order.append(i)
        for child in sorted(adjacency[i]):
            indegree[child] -= 1
            if indegree[child] == 0: q.append(child)
    require(len(order) == len(nodes), 'cycle including optional method edge')

    def ready(nid, caps, action=None, selectors=None):
        n=nodes[nid];caps=set(caps);selectors=selectors or {}
        if not set(n.get('requires_all',[])) <= caps:return False
        if any(not set(g)&caps for g in n.get('requires_any',[])):return False
        for rule in n.get('conditional_requirements',[]):
            flag=selectors.get(rule['selector'])
            if flag is None:return False
            if flag and not set(rule['requires_all'])<=caps:return False
        if action is not None:
            a=next(a for a in n.get('actions',[]) if a['id']==action)
            if not set(a.get('requires_all',[])) <= caps:return False
        return True

    scenarios=[]
    def check(name, condition):
        require(condition,name);scenarios.append({'name':name,'status':'PASS'})
    check('T9_missing_does_not_block_existing_morphology', ready('R9-13',['CMB_RANK_QUALIFIED','PRODUCT_INTAKE']))
    check('Optics_missing_does_not_block_CF4_qualified_result', ready('R9-17',['TUPLE_ADAPTER','CF4_QUALIFIED','PRODUCT_INTAKE'],'cf4'))
    check('CF4_missing_does_not_block_DESI', ready('R9-17',['TUPLE_ADAPTER','DESI_QUALIFIED','PRODUCT_INTAKE'],'desi'))
    check('CMB_rank_missing_does_not_block_candidate', ready('R9-15',['CMB_RESPONSE_QUALIFIED']))
    check('Local_ray_fixture_does_not_require_T9', ready('OP-05',['OPTICAL_FORWARD_SPEC'],selectors={'uses_T9_hierarchy':False}))
    check('Unknown_T9_use_is_not_false', not ready('OP-05',['OPTICAL_FORWARD_SPEC']))
    check('Actual_T9_consumer_requires_eligible_term', not ready('OP-05',['OPTICAL_FORWARD_SPEC'],selectors={'uses_T9_hierarchy':True}))
    check('Qualified_T9_allows_T9_fixture', ready('OP-05',['OPTICAL_FORWARD_SPEC','T9_CONSUMER_ELIGIBLE'],selectors={'uses_T9_hierarchy':True}))
    check('Missing_L_formula_has_invariant_Jacobi_route', ready('OP-03',['OPTICAL_CONVENTIONS']))
    check('Null_report_does_not_require_real_product', ready('OP-08',['OPTICAL_FIXTURES'],'null_report'))
    check('Response_binding_does_require_actual_intake', not ready('OP-08',['OPTICAL_FIXTURES'],'supported_response'))
    check('T9_prose_diagnosis_cannot_patch', not ready('OP-07',['T9_DIAGNOSIS','T9_PATCH_REQUIRED'],'repair'))
    check('T9_unresolved_cannot_grant_reuse', not ready('OP-07',['T9_DIAGNOSIS','FORMAL_T9'],'reuse'))
    check('Already_fixed_route_has_no_second_flip', ready('OP-07',['T9_DIAGNOSIS','FORMAL_T9','T9_NO_PATCH_NEEDED'],'reuse') and not ready('OP-07',['T9_DIAGNOSIS','FORMAL_T9','T9_NO_PATCH_NEEDED'],'repair'))
    check('CAS_optical_missing_does_not_block_exploratory_fixture',ready('OP-05',['OPTICAL_FORWARD_SPEC'],selectors={'uses_T9_hierarchy':False}))
    check('CAS_optical_missing_blocks_production_optical_method',not ready('OP-09',['OPTICAL_BINDING','TUPLE_ADAPTER','PRODUCT_INTAKE'],selectors={'uses_T9_hierarchy':False}))
    check('Optical_fixture_does_not_create_empirical_jet',not any('JET_RESPONSE_LAW' in n['may_produce'] for n in dag['nodes'][24:]))
    check('Missing_jet_blocks_only_physical_image',not ready('R9-20',['FORMAL_IMAGES','JOINT_SET']))
    check('Observed_candidate_requires_law_and_response_method', not ready('R9-14',['CMB_RESPONSE']))
    check('Any_partial_failure_can_return',dag['return_policy']['return_from']=='any_terminal_or_checkpoint' and not dag['return_policy']['requires_success'])
    check('No_implementation_claim_from_plan',not dag['authority']['production_mutated_this_delivery'] and not dag['authority']['canonical_promoted'] and all(n['execution_state']=='PLANNED' for n in dag['nodes'][24:]))
    raw=HERE/'source_addition'
    manifest=json.loads((raw/'MANIFEST.json').read_text())
    for name,item in manifest.items():
        b=(raw/name).read_bytes()
        require(len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],f'attachment {name}')
    require((ROOT/'docs/codex_handoff/pr_backlog.yaml').read_bytes()==(ROOT/'machine_readable/pr_backlog.yaml').read_bytes(),'canonical mirror')
    if (HERE/'MANIFEST.sha256').exists():
        for line in (HERE/'MANIFEST.sha256').read_text().splitlines():
            digest,name=line.split('  ',1)
            require(hashlib.sha256((HERE/name).read_bytes()).hexdigest()==digest,f'plan manifest {name}')
    return {'status':'PASS_STRUCTURAL_ONLY','nodes':len(nodes),'inherited_nodes_unchanged':24,'added_planned_nodes':12,'topological_order':order,'attachment_payload_hashes_matched':len(manifest),'failure_isolation_scenarios':scenarios,'science_or_CAS_executed':False,'publication_or_formal_admission':False}

if __name__ == '__main__':
    print(json.dumps(main(),ensure_ascii=False,indent=2))
