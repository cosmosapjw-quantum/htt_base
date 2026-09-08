#!/usr/bin/env python3
"""R8 action-scoped executor. Unimplemented science stays explicitly incomplete.

Resume preserves attempts and fingerprints missing/present inputs, source bytes,
predecessor receipts and artifacts. Live laws are reconstructed and rebound on
an observed rerun; serialized IDs never create a live calibration object.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from fractions import Fraction as F
import hashlib
import inspect
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT/'htt',ROOT/'htt/src',ROOT/'htt/htt',ROOT):sys.path.insert(0,str(p))
from common.r7_contracts import content_id,json_value
from common.r7_evidence import evidence_dependencies
from common.r7_asset_use import intake_inventory,verify_selected_sources
from htt.infer.r8_law_registry import admit_product,bind_method,run_scope,ScopedRefusal

@dataclass(frozen=True)
class Handler:
    execute: object
    dependencies: tuple=()
    config_id: str='R8_AC_INITIAL_V1'


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def identity(path):
    path=Path(path)
    return {'path':str(path.resolve()),'state':'PRESENT' if path.is_file() else 'MISSING',
            'sha256':digest(path) if path.is_file() else None}

def write(path,value):
    from scripts.observed_runs.r8_mocks import encode
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(value,default=encode,indent=2,allow_nan=False)+'\n');temp.replace(path)


def _artifact_valid(result):
    return all(identity(e['path'])==e for e in result.get('artifacts',()))


def execute_campaign(dag,run_dir,handlers,*,resume=False):
    run_dir=Path(run_dir);nodes={n['id']:n for n in dag['nodes']}
    if len(nodes)!=len(dag['nodes']):raise ValueError('duplicate node ID')
    if any(dep not in nodes for n in nodes.values() for dep in n['after']):raise ValueError('unknown predecessor')
    ordered=[];todo=dict(nodes)
    while todo:
        ready=[k for k,n in todo.items() if set(n['after'])<=set(ordered)]
        if not ready:raise ValueError('cyclic DAG')
        for k in ready:ordered.append(k);todo.pop(k)
    results={};new_attempts=0
    for nid in ordered:
        node=nodes[nid];predecessors={d:results[d] for d in node['after']};actions=[]
        for rule in node['actions']:
            action=rule['action'];handler=handlers.get(action)
            deps=list(handler.dependencies) if handler else []
            if handler:
                file=inspect.getsourcefile(handler.execute)
                if file:deps.append(Path(file))
            fingerprint=content_id({'rule':rule,'predecessors':predecessors,'inputs':[identity(p) for p in deps],
                'configuration':handler.config_id if handler else 'NOT_IMPLEMENTED',
                'executor':digest(__file__),'python':sys.version,'numpy':np.__version__})
            base=run_dir/nid/action;latest=base/'latest.json'
            if resume and latest.is_file():
                old=json.loads(latest.read_text())
                if old['fingerprint']==fingerprint and _artifact_valid(old):actions.append(old);continue
            previous=sorted(base.glob('attempt_*')) if base.exists() else []
            number=1+max((int(p.name.split('_')[1]) for p in previous),default=0)
            attempt=base/f'attempt_{number:04d}';attempt.mkdir(parents=True,exist_ok=False)
            missing=[req for req in rule['requires'] if req['capability'] not in results[req['node']]['capabilities']]
            start=time.monotonic()
            if handler is None:
                data={'process_status':'BLOCKED_WITH_RECEIPT','scientific_outcome':'NOT_EVALUATED',
                      'reason':'NOT_IMPLEMENTED_IN_INITIAL_AC_INCREMENT','capabilities':[]}
            elif missing:
                data={'process_status':'BLOCKED_WITH_RECEIPT','scientific_outcome':'NOT_EVALUATED',
                      'reason':'REQUIRED_CAPABILITY_UNAVAILABLE','missing':missing,'capabilities':[]}
            else:
                try:
                    data=handler.execute(attempt,predecessors)
                    if not isinstance(data,dict):raise TypeError('action must return a scoped result')
                    if set(data.get('capabilities',()))-set(rule['produces']):raise ValueError('action emitted undeclared capability')
                    if data.get('capabilities') and not data.get('evidence'):
                        raise ValueError('capability requires actual validation/source evidence')
                except Exception as exc:
                    data={'process_status':'COMPLETED_FAILED_WITH_RECEIPT','scientific_outcome':'NOT_EVALUATED',
                          'reason':f'{type(exc).__name__}: {exc}','capabilities':[]}
            data.setdefault('capabilities',[]);data.setdefault('process_status','COMPLETED_SUCCESS')
            data.setdefault('scientific_outcome','NOT_EVALUATED')
            artifacts=[identity(p) for p in data.pop('evidence',())]
            if any(e['state']!='PRESENT' for e in artifacts):
                data.update(process_status='COMPLETED_FAILED_WITH_RECEIPT',scientific_outcome='NOT_EVALUATED',
                            reason='Declared evidence file missing',capabilities=[])
            result={**data,'node_id':nid,'action':action,'fingerprint':fingerprint,'attempt':number,
                    'artifacts':artifacts,'elapsed_seconds':time.monotonic()-start}
            write(attempt/'result.json',result);write(latest,result);actions.append(result);new_attempts+=1
        results[nid]={'actions':actions,'capabilities':sorted(set(c for a in actions for c in a['capabilities'])),
                      'process_status':'TERMINAL_ACTION_RECEIPTS','scientific_outcomes':sorted(set(a['scientific_outcome'] for a in actions))}
    summary={'nodes':results,'new_attempts':new_attempts,'node_count':len(nodes),
             'full_plan_accepted':False,'acceptance_scope':'INITIAL_AC_INCREMENT; terminal receipt is not completed science',
             'unimplemented_actions':[f'{n}/{a["action"]}' for n,r in results.items() for a in r['actions']
                                      if a.get('reason')=='NOT_IMPLEMENTED_IN_INITIAL_AC_INCREMENT']}
    write(run_dir/'summary.json',summary);return summary


def _read_owned_laws(attempt):
    """Known selected locators only; no default covariance or storage scan."""
    from scripts.observed_runs.run_tensor_joint_r7 import DATA,_compressed_bao
    from htt.infer.r7_desi_law import build_compressed_bao_law
    records={};live={}
    try:
        raw=_compressed_bao(attempt);payload=raw['payload'];law=build_compressed_bao_law(payload)
        product={'product_id':'desi_compressed','observed':law.observed,
                 'measurement_ids':law.measurement_ids,'source_ids':law.specification['source_ids']}
        admitted=admit_product(product,{'law':law,'frame':'NONANGULAR_BACKGROUND_COMPRESSION','conditioning_id':law.conditioning_target})
        if isinstance(admitted,ScopedRefusal):records['desi_compressed']={'outcome':admitted.status,'reasons':admitted.reasons}
        else:
            live['desi_compressed']=(admitted,{'released_reference':[1.]},_compressed_confidence)
            records['desi_compressed']={'outcome':'CONDITIONAL_LAW_BOUND','scope':admitted.scope,
                'original_data_source':identity(payload['source_path']),'raw_catalogue_coverage':'UNVERIFIED',
                'stat_only_alternative':'NOT_MULTIPLIED','fiducial':payload['DV_over_rd_fid']}
    except Exception as exc:records['desi_compressed']={'outcome':'INPUT_UNAVAILABLE','reason':str(exc)}
    # Product status is based on the selected existing release documentation.
    # Quoted distance errors are not a law for conditioned velocity residuals.
    checks={
      'cf4_full':(DATA/'raw/cf4_full/ReadMe','Full covariance in source group order and a law for the conditioned sampling variable are not supplied; raw distance errors are not substituted.'),
      'jwst_anchors':(DATA/'raw/jwst_anchors/jwst_anchors_manifest.json','Quoted per-method errors do not supply shared host/calibration covariance; earlier independent-error fit remains a scenario.'),
      'union3':(DATA/'rrss_observational_inputs/union3_release-main/mu_mat_union3_cosmo=2_mu.fits','A matrix alone does not bind row/redshift/compression and the selected likelihood.'),
      'desi_raw':(DATA/'raw/desi_dr1_mocks/observed/v1.5/BGS_BRIGHT-21.5_NGC_clustering.dat.fits','P sample magnitude cuts and matched random normalization are not bound; PR151 numerical outputs excluded.')}
    for name,(path,reason) in checks.items():
        # Read only bounded named text metadata; FITS payload decode belongs to
        # the existing product-specific intake adapter, not a fabricated law.
        if path.is_file() and path.suffix in {'.json',''}:
            with path.open('rb') as stream:header=stream.read(65536)
            detail={'metadata_read_bytes':len(header),'header_sha256':hashlib.sha256(header).hexdigest()}
        else:detail={}
        records[name]={'outcome':'INPUT_UNAVAILABLE','law_status':'NO_ADMITTED_SELECTED_LAW',
                       'reason':reason,'input':identity(path),**detail}
    return records,live


def _compressed_confidence(live_law):
    """Source-specific location inversion for the released scalar BAO producer."""
    from htt.infer.r8_partial_law import normal_critical_square,_sqrt_rational_bounds
    native=live_law.law;variance=F(float(native.covariance[0,0]));center=F(float(native.observed[0]))
    radius=_sqrt_rational_bounds(variance*normal_critical_square(F(1,20))[1])[1]
    lo=max(F(0),center-radius);hi=center+radius
    return {'conditional_CI95_outer_exact':[str(lo),str(hi)],
        'conditional_CI95_display':[float(lo),float(hi)],'estimand':native.specification['mean_definition'],
        'domain':native.domain_id,'interpretation':'Conditional released Gaussian summary only; no isotropy/global-tilt/posterior claim.'}


def execute_admitted_products(live_products,*,include_confidence=False):
    """Dispatch explicit source-authorized queries through each live law.

    Product loaders supply their supported queries/region procedure. No node,
    parameter-name or product-name switch chooses the acceptance calculation.
    One product refusal/exception does not suppress a surviving subset.
    """
    outputs={}
    for key,request in live_products.items():
        try:
            live_law,queries,region_procedure=request
            method=bind_method(live_law,F(1,20))
            output={'candidates':{name:json_value(run_scope(live_law,method,x)) for name,x in queries.items()}}
            if include_confidence and region_procedure is not None:output['confidence_region']=region_procedure(live_law)
            outputs[key]=output
        except Exception as exc:outputs[key]={'outcome':'VALIDATION_FAILED','reason':str(exc)}
    return outputs


def usable_scopes(outputs):
    return sorted(key for key,value in outputs.items() if value.get('outcome')!='VALIDATION_FAILED' and value.get('candidates'))


def production_handlers(evidence_dir):
    from scripts.observed_runs.run_tensor_joint_r7 import DATA,INVENTORY,EXTERNAL_INVENTORY
    evidence_dir=Path(evidence_dir)
    pins=ROOT/'docs/generated/tensor_joint_r7/source_bindings.json'
    source_map=json.loads(pins.read_text());donors=tuple(ROOT/x['path'] for x in source_map['records'])
    inventories=(INVENTORY,EXTERNAL_INVENTORY/'assets.csv')
    product_deps=(DATA/'raw/desi_dr1_fullshape_bgs_bright_v1.2/likelihood/likelihood_bao-recon_syst_BGS_BRIGHT-21.5_GCcomb_z0.1-0.4.h5',
       DATA/'raw/cf4_full/ReadMe',DATA/'raw/jwst_anchors/jwst_anchors_manifest.json',
       DATA/'rrss_observational_inputs/union3_release-main/mu_mat_union3_cosmo=2_mu.fits',
       DATA/'raw/desi_dr1_mocks/observed/v1.5/BGS_BRIGHT-21.5_NGC_clustering.dat.fits')
    kernels=tuple(ROOT.glob('htt/htt/htt/infer/r8_*.py'))+(ROOT/'htt/src/common/r8_contracts.py',)
    donor_laws=tuple(ROOT/'htt/htt/htt/infer'/p for p in ('r7_gaussian_law.py','r7_desi_law.py'))+(ROOT/'scripts/observed_runs/run_tensor_joint_r7.py',)
    def sources(attempt,preds):
        failures=verify_selected_sources(ROOT,source_map)
        data={'donor_failures':failures,'selected_count':len(donors),
            'inventories':[[r.to_dict() for r in intake_inventory(p)] for p in inventories]}
        write(attempt/'source_binding.json',data)
        return {'scientific_outcome':'SOURCE_INTAKE_ONLY','capabilities':[] if failures else ['SOURCE_BOUND'],
                'evidence':[attempt/'source_binding.json'],'details':data}
    def history(attempt,preds):
        p=ROOT/'docs/generated/tensor_joint_r7/ADJUDICATION.md'
        return {'scientific_outcome':'HISTORICAL_SCOPED','capabilities':['HISTORY_SCOPED'],'evidence':[p],
                'reason':'Preserved R7 full-plan STOP_INVALID; no old CAS or Gaussian campaign promoted to R8.'}
    def products(attempt,preds):
        records,_=_read_owned_laws(attempt);write(attempt/'products.json',records)
        return {'scientific_outcome':'CONDITIONAL_BOUND','capabilities':['KNOWN_GAUSSIAN_FACTORY'] if any(v['outcome']=='CONDITIONAL_LAW_BOUND' for v in records.values()) else [],
                'evidence':[attempt/'products.json'],'products':records}
    def dispatch(attempt,preds):
        records,live=_read_owned_laws(attempt)
        accepted=execute_admitted_products(live,include_confidence=False)
        write(attempt/'acceptance.json',accepted)
        return {'scientific_outcome':'CONDITIONAL_BOUND' if usable_scopes(accepted) else 'NOT_EVALUATED','capabilities':['GAUSSIAN_ACCEPTANCE'] if usable_scopes(accepted) else [],
                'capability_scopes':{'GAUSSIAN_ACCEPTANCE':usable_scopes(accepted)},
                'evidence':[attempt/'acceptance.json'],'products':accepted}
    def observed(attempt,preds):
        records,live=_read_owned_laws(attempt)
        outputs=execute_admitted_products(live,include_confidence=True)
        write(attempt/'observed_subsets.json',outputs)
        return {'scientific_outcome':'CONDITIONAL_BOUND' if usable_scopes(outputs) else 'NOT_EVALUATED','capabilities':['OBSERVED_GAUSSIAN'] if usable_scopes(outputs) else [],
                'capability_scopes':{'OBSERVED_GAUSSIAN':usable_scopes(outputs)},
                'evidence':[attempt/'observed_subsets.json'],'products':outputs}
    def unavailable_law(attempt,preds):
        records,_=_read_owned_laws(attempt);write(attempt/'law_refusals.json',records)
        return {'scientific_outcome':'INPUT_UNAVAILABLE','capabilities':[],
                'evidence':[attempt/'law_refusals.json'],'products':records,
                'reason':'No actual selected singular/marginal/moment/simulator premises supplied by these source products.'}
    cas_dir=ROOT/'.agent-harness/runs/R8-AC-20260909/artifacts/observed_cas'
    cas_contract=ROOT/'.agent-harness/runs/R8-AC-20260909/CAS_CONTRACT.json'
    cas_dependencies=tuple(evidence_dependencies(ROOT,cas_dir/'adjudication.json',cas_contract))
    def algebra(attempt,preds):
        report=json.loads((cas_dir/'adjudication.json').read_text())
        if report['contract_sha256']!=digest(cas_contract):raise ValueError('CAS contract changed')
        contract=json.loads(cas_contract.read_text())
        if contract['identity']['contract_id']!='R8-ORBIT-RANK-JOINT-JET-V1':raise ValueError('Not the new R8 contract')
        records={}
        for obligation in contract['target']['exact_test_obligations']:
            records[obligation]={axis:e['payload']['checks'].get(obligation)
                for axis,e in report['execution_evidence'].items()}
        write(attempt/'per_obligation_checks.json',records)
        return {'scientific_outcome':'PROOF_PARTIALLY_UNRESOLVED','capabilities':[],
            'aggregate_status':report['aggregate_status'],'per_obligation_checks':records,
            'reason':'Full CAS component is not admitted. Individually compiled/count/support checks are retained without overriding the existing aggregate gate.',
            'evidence':[cas_dir/'adjudication.json',cas_contract,attempt/'per_obligation_checks.json']}
    def method_receipt(attempt,preds):
        validation=evidence_dir/'validation.json';data=json.loads(validation.read_text())
        if data['exit_code']!=0 or any(digest(ROOT/path)!=sha for path,sha in data['source_sha256'].items()):
            raise ValueError('Current kernel validation missing or stale')
        return {'scientific_outcome':'METHOD_TESTED_PROOF_SCOPE_HELD','capabilities':[],
            'evidence':[validation],
            'reason':'Implementation/tests recorded; broad support/partial-law CAS promotion withheld while registered Lean scope is unresolved.'}
    def toy(attempt,preds):
        path=evidence_dir/'mocks/mock5.json';data=json.loads(path.read_text());held=sorted({c['law'] for c in data['cells'] if not c['diagnostic_pass']})
        passed=sorted({c['law'] for c in data['cells']}-set(held))
        return {'scientific_outcome':'METHOD_PARTIALLY_HELD','capabilities':['SIMULATOR_METHOD'] if passed else [],
                'capability_scopes':{'SIMULATOR_METHOD':passed},
                'evidence':[path],'held_adapters':held,'results':data,
                'reason':'Mixture adapter held. Supported method scope is restricted to the separately passed toy laws; no real product simulator admission.'}
    return {'bind_sources':Handler(sources,(pins,*donors,*inventories)),
            'orbit_obligations':Handler(algebra,cas_dependencies),
            'rank_obligations':Handler(algebra,cas_dependencies),
            'gaussian_support':Handler(method_receipt,(evidence_dir/'validation.json',*kernels)),
            'partial_laws':Handler(method_receipt,(evidence_dir/'validation.json',*kernels)),
            'import_historical_records':Handler(history,(ROOT/'docs/generated/tensor_joint_r7/ADJUDICATION.md',)),
            'known_nonsingular_law':Handler(products,product_deps+donor_laws+kernels),
            'known_singular_law':Handler(unavailable_law,product_deps+donor_laws+kernels),
            'marginal_or_moment_law':Handler(unavailable_law,product_deps+donor_laws+kernels),
            'simulator_law':Handler(unavailable_law,product_deps+donor_laws+kernels),
            'nonsingular_dispatch':Handler(dispatch,product_deps+donor_laws+kernels),
            'gaussian_observation':Handler(observed,product_deps+donor_laws+kernels),
            'toy_simulator_validation':Handler(toy,(evidence_dir/'mocks/mock5.json',))}


def main():
    p=argparse.ArgumentParser();p.add_argument('--dag',type=Path,required=True);p.add_argument('--run-dir',type=Path,required=True)
    p.add_argument('--resume',action='store_true');p.add_argument('--dry-plan',action='store_true');p.add_argument('--evidence-dir',type=Path,default=ROOT/'docs/generated/tensor_joint_r8/ac')
    a=p.parse_args();dag=json.loads(a.dag.read_text());handlers=production_handlers(a.evidence_dir)
    if a.dry_plan:
        print(json.dumps({'mode':'DRY_PLAN_NO_SCIENTIFIC_EXECUTION','run_dir':str(a.run_dir),
            'fixed_products':['desi_compressed','cf4_full','jwst_anchors','union3','desi_raw'],
            'allocation':dag.get('error_allocation'),
            'actions':[{'node':n['id'],'action':r['action'],'implemented':r['action'] in handlers,
                        'requires':r['requires'],'possible_outputs':r['produces']} for n in dag['nodes'] for r in n['actions']]},indent=2))
        return
    result=execute_campaign(dag,a.run_dir,handlers,resume=a.resume)
    print(json.dumps({k:result[k] for k in ('node_count','new_attempts','full_plan_accepted')}))
if __name__=='__main__':main()
