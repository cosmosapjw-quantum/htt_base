"""Structural R8 design check. Never executes or validates scientific methods."""
import argparse
import json
from fractions import Fraction
from pathlib import Path

def validate(d):
    assert d['status']=='DESIGN_ONLY_NOT_EXECUTED'
    assert d['policy']['runtime_policy_override'] is False
    ns=d['nodes']; by={n['id']:n for n in ns}
    assert len(by)==len(ns) and len(ns)>0
    seen=set()
    offered={n['id']:{c for a in n['actions'] for c in a['produces']} for n in ns}
    valid=set(d['validation_ids'])
    for n in ns:
        assert set(n['after'])<=seen, f"cycle/order/missing dependency: {n['id']}"
        assert n['dependency_mode']=='terminal_receipts' and n['settle_unavailable']
        assert n['execution_status']=='NOT_RUN' and n['science_status']=='NOT_EVALUATED'
        assert n['outputs'] and n['contract_refs']
        for a in n['actions']:
            assert a['on_missing'] in d['process_terminal']
            assert a['produces_only_after']=='declared_validation_and_scope_admission'
            assert a['emits_receipt_always'] is True
            assert set(a['validation'])<=valid
            for r in a['requires']:
                assert r['node'] in n['after'], f"unawaited provider: {n['id']}"
                assert r['capability'] in offered[r['node']], f"unknown capability: {r}"
        seen.add(n['id'])
    synth=[n for n in ns if n['kind']=='synthesis']
    assert len(synth)==1
    assert set(synth[0]['after'])==set(by)-{synth[0]['id']}
    assert sum(map(Fraction,d['error_allocation'].values()))==Fraction(1,20)
    # Graph-only failure routing: capabilities are mock symbols, not scientific evidence.
    for failed in [set(),set(by)-{synth[0]['id']},*({k} for k in by if k!=synth[0]['id'])]:
        settled=set(); caps={}
        for n in ns:
            assert set(n['after'])<=settled
            caps[n['id']]=set()
            if n['id'] not in failed:
                for a in n['actions']:
                    if all(r['capability'] in caps[r['node']] for r in a['requires']):
                        caps[n['id']].update(a['produces'])
            settled.add(n['id'])
        assert 'SYNTHESIS' in caps[synth[0]['id']]
    # Provider failure must not remove morphology or exact-law structural routes.
    for forbidden in ['R8-18','R8-19','R8-20']:
        def ancestors(k):
            out=set(by[k]['after'])
            for p in by[k]['after']: out |= ancestors(p)
            return out
        assert forbidden not in ancestors('R8-07')
        assert forbidden not in ancestors('R8-12')
    # Action-level survivor checks for independently reviewed capability splits.
    def action_route(disabled):
        caps={}
        for n in ns:
            caps[n['id']]=set()
            for a in n['actions']:
                if (n['id'],a['action']) in disabled: continue
                if all(r['capability'] in caps[r['node']] for r in a['requires']):
                    caps[n['id']].update(a['produces'])
        return caps
    distance=action_route({('R8-19','record_radiation_jet_unavailable')})
    assert 'R3_DISTANCE_FACTORY' in distance['R8-20']
    assert 'P2_DISTANCE_RESULTS' in distance['R8-21']
    assert not any('R3_JET_CHANNEL' in cs for cs in offered.values())
    finite=action_route({('R8-14','recession_certificates')})
    assert 'PHYSICAL_IMAGE' in finite['R8-16']
    assert 'NONID_RESULTS' not in finite['R8-16']
    return {'status':'PASS_STRUCTURAL_ONLY','nodes':len(ns),'actions':sum(len(n['actions']) for n in ns),
            'routing_scenarios':len(ns)+3,'science_executed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('dag',nargs='?',type=Path,default=Path(__file__).with_name('campaign_dag.json'))
    print(json.dumps(validate(json.loads(p.parse_args().dag.read_text())),sort_keys=True))
