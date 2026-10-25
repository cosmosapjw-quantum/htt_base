"""Contract-specific tests of additive uptake; no live controller state access."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/codex_harness'))
import research_controller as rc
import publication_frontier_preflight as pf

FRONTIER=json.loads((ROOT/pf.REL/'FRONTIER.json').read_text())

def state():
    s=rc.initialize({'campaign_id':'TEST-EXISTING','tasks':[
        {'id':'OLD-HOLD','goal':'physical input','acceptance':'unchanged physical law','input_identity':'old-input'},
        {'id':'OLD-ACTIVE','goal':'existing work','acceptance':'keep current packet','input_identity':'active-input'}]},'test')
    s['tasks']['OLD-HOLD'].update(state='held',attempt=4,history=[{'raw':'preserved-failure'}],ultra_used=['one-use'])
    s['tasks']['OLD-ACTIVE'].update(state='running',attempt=2,packet_id='old-packet',authors=['old-worker'])
    s['packets']={'old-packet':{'task_id':'OLD-ACTIVE','packet_id':'old-packet','state':'running'}}
    s['ultra_repairs']={'OLD-REPAIR':'consumed'}
    s['events']=[{'type':'historic','failure':'preserved'}]
    return s

def test_append_preserves_every_old_state_object_and_busy_dispatch():
    s=state();before=copy.deepcopy(s)
    rc.append_frontier(s,FRONTIER,'test owner instruction')
    for k,v in before.items():
        if k not in ('tasks','events','frontiers'):assert s[k]==v
    for k,v in before['tasks'].items():assert s['tasks'][k]==v
    assert s['events'][:-1]==before['events']
    outcome=rc.next_packet(s,{},set())
    assert 'spawn_args' not in outcome and s['tasks']['OLD-ACTIVE']==before['tasks']['OLD-ACTIVE']

def test_blocked_originals_do_not_block_independent_publication_products():
    s=state();s['tasks']['OLD-ACTIVE']['state']='held'
    rc.append_frontier(s,FRONTIER,'test')
    ready=rc.summary(s)['ready']
    roots=[t['id'] for t in FRONTIER['tasks'] if t['requires']=={'all':[]}]
    assert len(roots)==7 and set(roots)<=set(ready)
    assert 'R32-08-H03-PAPER' not in ready
    dep=s['tasks']['R32-03-H03-STRUCTURED'];dep['state']='completed'
    assert 'R32-08-H03-PAPER' not in rc.summary(s)['ready']
    dep['qualified_products']=['structured_frontier']
    assert 'R32-08-H03-PAPER' in rc.summary(s)['ready']

def test_preflight_is_read_only_and_append_is_idempotently_detected():
    s=state();before=copy.deepcopy(s)
    result=pf.check(ROOT,s)
    assert s==before and result['status']=='APPEND_READY'
    rc.append_frontier(s,FRONTIER,'test')
    before=copy.deepcopy(s)
    assert pf.check(ROOT,s)['status']=='ALREADY_APPENDED' and s==before
    changed=copy.deepcopy(FRONTIER);changed['tasks'][0]['goal']='changed frozen task'
    s['frontiers'][0]['identity']=rc.digest(changed)
    with pytest.raises(ValueError,match='different frozen content'):pf.check(ROOT,s)

def test_duplicate_append_is_atomic():
    s=state();rc.append_frontier(s,FRONTIER,'test');before=copy.deepcopy(s)
    with pytest.raises(rc.ControllerError,match='already appended'):rc.append_frontier(s,FRONTIER,'test')
    assert s==before

def test_active_output_overlap_rejected_without_mutation():
    s=state();s['tasks']['OLD-ACTIVE']['spec']['owned_paths']=[pf.REL+'/products']
    before=copy.deepcopy(s)
    with pytest.raises(ValueError,match='active writer overlaps'):pf.check(ROOT,s)
    assert s==before

def test_reject_changed_evidence_and_path_escape(tmp_path):
    # Isolate only the manifest/empty source required for hash-failure handling.
    dst=tmp_path/pf.REL;dst.mkdir(parents=True)
    (dst/'FRONTIER.json').write_text(json.dumps(FRONTIER))
    (tmp_path/'datum').write_text('tampered')
    (dst/'EVIDENCE_MANIFEST.json').write_text(json.dumps({'files':[{'path':'datum','sha256':'0'*64}]}))
    with pytest.raises(ValueError,match='changed evidence'):pf.check(tmp_path)
    with pytest.raises(ValueError,match='repository-relative'):pf.located(ROOT,'../state.json')

def test_original_dag_and_operative_ready_route_remain_separate():
    spec=importlib.util.spec_from_file_location('pub_dag',ROOT/'scripts/htt_publication_dag.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    dag=m.load()
    assert m.validate(dag)['node_count']==42
    assert dag['publication_output_route_20261025']['frontier']==pf.REL+'/FRONTIER.json'
    assert all(t['promotes_original_acceptance'] is False for t in FRONTIER['tasks'])
    assert len({t['owned_paths'][0] for t in FRONTIER['tasks']})==9
