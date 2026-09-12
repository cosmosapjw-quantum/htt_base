#!/usr/bin/env python3
"""Structural and failure-isolation checks; never grants scientific capabilities."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent
d=json.loads((P/'campaign_dag.json').read_text());ns=d['nodes']
ids=[x['id'] for x in ns];assert len(ids)==len(set(ids))==24
producers={c:n['id'] for n in ns for c in n['may_produce']}
assert len(producers)==sum(len(n['may_produce']) for n in ns)
external=set(d['external_capabilities']);known=set(producers)|external
edges={n['id']:set() for n in ns}
for n in ns:
    assert n['scope'] and n['acceptance'] and n['on_missing']
    needs=n['requires_all']+[c for group in n['requires_any'] for c in group]
    for a in n.get('actions',[]):
        needs+=a['requires_all'];assert a['produces'] in n['may_produce']
    assert set(needs)<=known
    edges[n['id']].update(producers[c] for c in needs if c in producers)
vis=set();stack=set()
def visit(i):
    assert i not in stack,'cycle'
    if i in vis:return
    stack.add(i)
    for j in edges[i]:visit(j)
    stack.remove(i);vis.add(i)
for i in ids:visit(i)

def closure(block=()):
    # ASSUME each available action qualifies, solely to inspect isolation topology.
    # Scientific execution never calls this helper as an admission engine.
    caps=set(external);deny=set(block)
    changed=True
    while changed:
        before=len(caps)
        for n in ns:
            if not set(n['requires_all'])<=caps:continue
            if not all(set(g)&caps for g in n['requires_any']):continue
            for a in n.get('actions',[{'requires_all':[],'produces':c} for c in n['may_produce']]):
                if set(a['requires_all'])<=caps and a['produces'] not in deny:caps.add(a['produces'])
        changed=len(caps)!=before
    return caps
tests=[]
def check(name,blocked,present,absent):
    c=closure(blocked);assert set(present)<=c,(name,'missing',set(present)-c)
    assert not set(absent)&c,(name,'unexpected',set(absent)&c)
    tests.append({'name':name,'status':'PASS','blocked_capabilities':blocked})
check('all_assumed_qualified',[],['JOINT_SET','PHYSICAL_IMAGE','CMB_MORPHOLOGY_RESULT'],[])
check('CF4_law_missing',['CF4_LAW'],['DESI_SET','CMB_MORPHOLOGY_RESULT','JOINT_SET'],['CF4_SET'])
check('CMB_rank_unresolved',['CMB_RANK_QUALIFIED'],['CMB_PARAMETER_SET','DESI_SET'],['CMB_MORPHOLOGY_RESULT'])
check('CMB_candidate_law_missing',['CMB_CANDIDATE_LAW'],['CMB_MORPHOLOGY_RESULT','DESI_SET'],['CMB_PARAMETER_SET'])
check('jet_missing',['JET_RESPONSE_LAW'],['JOINT_SET','CMB_MORPHOLOGY_RESULT'],['PHYSICAL_IMAGE'])
check('nullspace_certificate_missing',['IDENTIFICATION_REPORT'],['PHYSICAL_IMAGE'],[])
check('purpose_error_unused',['PURPOSE_ERROR_SET'],['CMB_MORPHOLOGY_RESULT','DESI_SET'],[])
check('rank_formal_missing',['FORMAL_RANK'],['DESI_SET','CMB_PARAMETER_SET'],['ORBIT_METHOD','CMB_MORPHOLOGY_RESULT'])
check('response_formal_missing',['FORMAL_RESPONSE'],['CMB_MORPHOLOGY_RESULT','DESCRIPTIVE_CONTROLS'],['CF4_SET','CMB_PARAMETER_SET'])
check('JWST_law_missing',['JWST_LAW'],['CF4_SET','DESI_SET'],['JWST_SET'])
check('all_empirical_laws_missing',['CMB_CANDIDATE_LAW','CMB_EXCHANGEABLE_POOL','CF4_LAW','JWST_LAW','DESI_LAW'],['DESCRIPTIVE_CONTROLS','SCIENTIFIC_REPORT'],['JOINT_SET','PHYSICAL_IMAGE','CMB_MORPHOLOGY_RESULT'])
assert not any('BASS' in c for c in known)
assert d['alpha']['no_redistribution']
assert sum(d['alpha'][k] for k in ['CMB','CF4','distance_calibration','DESI'])<=d['alpha']['family']+1e-15
assert sum(d['alpha']['CMB_suballocation'][k] for k in ['morphology_test','candidate_confidence'])<=d['alpha']['CMB']
out={'nodes':len(ns),'dependency_edges':sum(map(len,edges.values())),'structural':'PASS','isolation_scenarios':tests,
 'interpretation':'Assumed-capability graph tests only. No CAS, law, mock or observation capability is earned by these tests.'}
(P/'evidence/dag_checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
