#!/usr/bin/env python3
"""Execute the R7 settle/capability/scope DAG with preserved resume attempts."""
from __future__ import annotations
import argparse
from dataclasses import dataclass,replace
from datetime import datetime,timezone
import hashlib
import inspect
import json
from pathlib import Path
import sys
import traceback

ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT/'htt/src',ROOT/'htt',ROOT/'htt/htt',ROOT):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
from common.r7_contracts import BranchResult,TERMINAL,json_value,content_id
from common.r7_evidence import file_state


def _write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(json_value(value),indent=2,sort_keys=True,allow_nan=False)+'\n')
    tmp.replace(path)


def _sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _branch(value):
    value=dict(value)
    for name in ('capabilities','evidence','assumptions','reasons','valid_estimands'):
        value[name]=tuple(value.get(name,()))
    return BranchResult(**value)


def settle_node(node,predecessor_results) -> BranchResult:
    """Receive all settled ancestors; direct settle edges remain mandatory."""
    results={r.node_id:r for r in predecessor_results.values()} if isinstance(predecessor_results,dict) else {r.node_id:r for r in predecessor_results}
    pending=[p for p in node['settle_after'] if p not in results or results[p].process_status not in TERMINAL]
    if pending:return BranchResult(node['id'],'PENDING','NOT_EVALUATED',reasons=('waiting for terminal predecessors: '+','.join(pending),))
    available=set(c for r in results.values() for c in r.capabilities)
    routes=node.get('capability_routes',())
    eligible=node.get('always_run',False) or any(set(route)<=available for route in routes)
    if not eligible:
        missing=[sorted(set(route)-available) for route in routes]
        producer=node.get('_capability_producers',{})
        details={c:[{'node':p,'status':results[p].process_status if p in results else 'NOT_AN_ANCESTOR',
                     'reasons':results[p].reasons if p in results else ()} for p in producer.get(c,())]
            for route in missing for c in route}
        return BranchResult(node['id'],'BLOCKED_WITH_RECEIPT','INPUT_UNAVAILABLE',
            reasons=('no satisfied capability route',),product_results={'missing_routes':missing,'failed_producers':details})
    execute=node.get('_execute')
    if execute is None:
        return BranchResult(node['id'],'COMPLETED_FAILED_WITH_RECEIPT','NOT_EVALUATED',
            reasons=('eligible node has no registered scientific executor',))
    try:
        result=execute(node,results)
        if not isinstance(result,BranchResult) or result.node_id!=node['id']:raise TypeError('executor must return this node BranchResult')
        if result.process_status not in TERMINAL:raise ValueError('an executor must terminate with a result')
        if set(result.capabilities)-set(node['declared_outputs']):raise ValueError('executor emitted undeclared capabilities')
        # Success alone never supplies all declared outputs. The executor must
        # bind each emitted capability to its own validation artifact and scope.
        bindings=result.product_results.get('capability_evidence',{})
        for capability in result.capabilities:
            binding=bindings.get(capability)
            if not binding or not binding.get('scope') or not binding.get('artifacts'):
                raise ValueError('capability lacks scope-specific evidence: '+capability)
            for path in binding['artifacts']:
                if not Path(path).is_file():raise ValueError('capability evidence artifact missing: '+str(path))
        return result
    except Exception as exc:
        return BranchResult(node['id'],'COMPLETED_FAILED_WITH_RECEIPT','VALIDATION_FAILED',
            reasons=(f'{type(exc).__name__}: {exc}',),product_results={'exception':traceback.format_exc()})


@dataclass(frozen=True)
class ConclusionPackage:
    process_complete: bool
    node_outcomes: tuple
    scope_results: tuple
    product_results: dict
    missing_discriminators: tuple
    empirical_scope_count: int
    interpretation: str


def synthesize_campaign(results) -> ConclusionPackage:
    rows=tuple(results.values()) if isinstance(results,dict) else tuple(results)
    outcomes=tuple({'node_id':r.node_id,'process_status':r.process_status,'scientific_outcome':r.scientific_outcome,
        'reasons':r.reasons,'evidence':r.evidence,'capabilities':r.capabilities} for r in rows)
    scopes=[];products={};discriminators=[]
    for row in rows:
        scopes.extend(row.product_results.get('scope_results',()))
        products.update(row.product_results.get('asset_uses',{}))
        if row.next_discriminator:discriminators.append(row.next_discriminator)
    unique={}
    for scope in scopes:
        key=content_id(scope.get('scope',scope))
        if key in unique and content_id(unique[key])!=content_id(scope):
            previous=unique[key]
            unique[key]={'scope':scope.get('scope'),'empirical':False,'outcome':'NUMERICALLY_UNRESOLVED',
                'reason':'conflicting results under the same exact scope','conflicting_records':[previous,scope]}
        elif key not in unique:unique[key]=scope
    scopes=list(unique.values())
    empirical=sum(1 for r in scopes if r.get('empirical',False) and r.get('outcome') in
        {'COMPATIBLE','REJECTED_CONJUNCTION','PARTIALLY_IDENTIFIED','NONIDENTIFIED','CONDITIONAL_BOUND'})
    return ConclusionPackage(bool(rows) and all(r.process_status in TERMINAL for r in rows),outcomes,tuple(scopes),products,
        tuple(dict.fromkeys(discriminators)),empirical,
        'Results are restricted to their declared experiment, law, model, data, conventions and method scope. '
        'Blocked or failed computations do not reject a physical model. '
        +('Eligible empirical scopes are reported separately with their uncertainty.' if empirical else
          'No calibrated empirical scope was admitted; available numerical/analytic and descriptive controls remain separate.'))


def _topology(dag):
    nodes=dag.get('nodes',());byid={n['id']:n for n in nodes}
    if len(byid)!=len(nodes):raise ValueError('duplicate DAG node ID')
    remaining=set(byid);ordered=[];ancestors={}
    while remaining:
        ready=sorted(i for i in remaining if set(byid[i]['settle_after'])<=set(ordered))
        if not ready:raise ValueError('DAG cycle or missing predecessor')
        for i in ready:
            direct=set(byid[i]['settle_after']);ancestors[i]=direct|set().union(*(ancestors[p] for p in direct)) if direct else set()
            ordered.append(i);remaining.remove(i)
    return byid,ordered,ancestors


def run_campaign(dag_path,run_dir,*,resume=False,executors=None,input_identities=None,implementation_sources=None,tracer=None):
    dag_path=Path(dag_path).resolve();run_dir=Path(run_dir).resolve()
    dag=json.loads(dag_path.read_text());nodes,order,ancestors=_topology(dag)
    state_path=run_dir/'campaign_state.json'
    if state_path.exists() and not resume:raise ValueError('run already exists; use --resume to preserve attempts')
    state=json.loads(state_path.read_text()) if state_path.exists() else {'campaign_id':dag['campaign_id'],'nodes':{},'history':[]}
    if state['campaign_id']!=dag['campaign_id']:raise ValueError('resume campaign identity mismatch')
    if executors is None:
        from scripts.observed_runs.run_tensor_joint_r7 import campaign_executors
        executors,input_identities,implementation_sources,tracer=campaign_executors(ROOT,run_dir)
    inputs=input_identities or {};sources=implementation_sources or {};results={};output_ids={}
    producer={}
    for node in nodes.values():
        for cap in node['declared_outputs']:producer.setdefault(cap,[]).append(node['id'])
    for node_id in order:
        node=dict(nodes[node_id]);predecessors={p:results[p] for p in order if p in ancestors[node_id]}
        fingerprints={str(p):file_state(p) for p in sources.get(node_id,())}
        fingerprint=content_id({'node':node,'inputs':inputs.get(node_id,{}),'implementation_sources':fingerprints,
            'runner':_sha(__file__),'file_identity_implementation':inspect.getsource(file_state),
            'predecessors':{p:output_ids[p] for p in node['settle_after']}})
        previous=state['nodes'].get(node_id)
        if previous and previous['fingerprint']==fingerprint:
            path=run_dir/previous['result_path']
            evidence_ok=all(Path(p).is_file() and _sha(p)==sha for p,sha in previous.get('evidence_sha256',{}).items())
            if path.is_file() and _sha(path)==previous['result_sha256'] and evidence_ok:
                results[node_id]=_branch(json.loads(path.read_text()));output_ids[node_id]=previous['result_sha256'];continue
        attempt=1 if previous is None else previous['attempt']+1
        # A killed process may have created its attempt directory before state
        # publication. Preserve that partial attempt instead of overwriting it.
        existing=list((run_dir/'nodes'/node_id).glob('attempt-*'))
        if existing: attempt=max(attempt,1+max(int(p.name.split('-')[-1]) for p in existing))
        directory=run_dir/'nodes'/node_id/f'attempt-{attempt:04d}'
        directory.mkdir(parents=True,exist_ok=False)
        node['_capability_producers']=producer;node['_run_dir']=run_dir;node['_attempt_dir']=directory
        node['_execute']=executors.get(node_id)
        started=datetime.now(timezone.utc).isoformat()
        result=replace(settle_node(node,predecessors),attempt=attempt)
        if result.process_status not in TERMINAL:raise RuntimeError('topologically ready node did not settle')
        result_path=directory/'result.json';_write(result_path,result)
        entry={'attempt':attempt,'fingerprint':fingerprint,'result_path':str(result_path.relative_to(run_dir)),
            'result_sha256':_sha(result_path),'started_at':started,'completed_at':datetime.now(timezone.utc).isoformat()}
        evidence=set(result.evidence)
        for binding in result.product_results.get('capability_evidence',{}).values(): evidence.update(binding['artifacts'])
        entry['evidence_sha256']={str(p):_sha(p) for p in evidence if Path(p).is_file()}
        _write(directory/'execution.json',entry)
        if previous:state['history'].append({'node_id':node_id,**previous})
        state['nodes'][node_id]=entry;state['dag_sha256']=_sha(dag_path);_write(state_path,state)
        results[node_id]=result;output_ids[node_id]=entry['result_sha256']
        if tracer is not None:
            try:tracer.record_node(result,entry)
            except Exception as exc:
                # Tracing is operational and never changes eligibility/outcome.
                _write(directory/'tracing_failure.json',{'type':type(exc).__name__,'message':str(exc)})
    conclusion=synthesize_campaign(results);_write(run_dir/'conclusion.json',conclusion)
    return results,conclusion


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dag',type=Path,required=True);parser.add_argument('--run-dir',type=Path,required=True)
    parser.add_argument('--resume',action='store_true');args=parser.parse_args(argv)
    results,conclusion=run_campaign(args.dag,args.run_dir,resume=args.resume)
    print(json.dumps({'process_complete':conclusion.process_complete,'nodes':len(results),'empirical_scope_count':conclusion.empirical_scope_count,
        'conclusion':str(args.run_dir/'conclusion.json')},sort_keys=True))
    return 0 if conclusion.process_complete else 2


if __name__=='__main__':raise SystemExit(main())
