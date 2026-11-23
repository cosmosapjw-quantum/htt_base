"""R101 conditional execution map for the unchanged R78 sixty-node science DAG.

`prepare` writes a compact map; `analysis --node SQ-CF4` runs concrete reusable
conditional jobs. Scientific admission is separately queried by `science` and
retains every inherited original acceptance and status. Model execution does
not substitute for unavailable source calibration or a native family atlas.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'docs/research_program/observational_publication_20261015'
OUT=BASE/'R101_SIXTH_SOLVER_RESPONSE_20261123'
SOURCE=BASE/'R100_SOURCE_LAW_OPTICAL_MULTIPROBE_20261123/NODE60_EXECUTION_PREPARATION.json'
DAG=BASE/'R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json'
DAG_SHA='90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11'

JOBS={
 'CF4_RESPONSE':('scripts.r101.cf4_predictive_response',['--source-marks'],'CF4_PREDICTIVE_RESPONSE.json'),
 'CHEMISTRY_COLLISION':('scripts.r101.chemistry_coherency',[],'CHEMISTRY_COHERENCY.json'),
 'MOVING_PROJECTION':('scripts.r101.moving_projection_checks',[],'MOVING_PROJECTION.json'),
 'HYREC_COLLISION':('scripts.r101.coherency_history',[],'HYREC_COHERENCY_HISTORY.json'),
 'NATIVE_COLLISION_CHECKS':('scripts.r101.coherency_checks',[],'NATIVE_COLLISION_CHECKS.json'),
}
AXIS_JOBS={
 'COMMON':['MOVING_PROJECTION'], 'P1':['CF4_RESPONSE','MOVING_PROJECTION'],
 'P2':['HYREC_COLLISION','NATIVE_COLLISION_CHECKS','CHEMISTRY_COLLISION'],
 'P3':['CF4_RESPONSE'], 'P4':['MOVING_PROJECTION'],
 'P5':['NATIVE_COLLISION_CHECKS','CHEMISTRY_COLLISION','MOVING_PROJECTION'],
 'P6':['MOVING_PROJECTION','CF4_RESPONSE']}
PHY_JOBS={
 'PHY-01':['CF4_RESPONSE','MOVING_PROJECTION'],
 'PHY-02':['HYREC_COLLISION','NATIVE_COLLISION_CHECKS','CHEMISTRY_COLLISION'],
 'PHY-03':['CHEMISTRY_COLLISION','MOVING_PROJECTION'],
 'PHY-04':['MOVING_PROJECTION'],
 'PHY-05':['MOVING_PROJECTION','NATIVE_COLLISION_CHECKS'],
 'PHY-06':['CF4_RESPONSE','HYREC_COLLISION','NATIVE_COLLISION_CHECKS','CHEMISTRY_COLLISION','MOVING_PROJECTION'],
 'PHY-07':['CF4_RESPONSE','MOVING_PROJECTION']}
SQ_JOBS={
 'SQ-CF4':['CF4_RESPONSE'],'SQ-NATIVE':['NATIVE_COLLISION_CHECKS','HYREC_COLLISION','CHEMISTRY_COLLISION'],
 'SQ-PHOTON-FLUX':['HYREC_COLLISION','CHEMISTRY_COLLISION'],
 'SQ-LIE-FLUX':['MOVING_PROJECTION','NATIVE_COLLISION_CHECKS'],
 'SQ-CMB-NULL':['HYREC_COLLISION'],'SQ-CROSS-COV':['CF4_RESPONSE','MOVING_PROJECTION']}

DATA_ACTIONS={
 'D01':'Analyze native SDSS/6dF sign genealogy; obtain unshifted method/anchor tables and independent calibration covariance.',
 'D02':'Use all 8885 released 6dFGSv match indicators; obtain other CF4 parent/rejection denominators before union claims.',
 'D03':'Acquire the existing Commander matched-noise allowlist; split by independent simulation/noise genealogy.',
 'D04':'Supply release-matched AGIS scan/AGN centroid controls; retain rank-47 supported covariance subspace.',
 'D05':'Fetch prepared LoTSS RMS/weight files when online; apply interior holes and source associations before count fits.',
 'D06':'Supply independent normal-frame rho,j,pi; a constraint inversion is not an independent measurement.'}
SOLVER_ACTIONS={
 'M08':{'kind':'CODE_AND_THEORY','completed':'signed IQUV collision repair; exact stiff collision/source cells; bounded Fourier transport',
        'next':'Implement k-dependent general-Lie streaming, electron-frame transforms and Einstein/species coupling on the existing R100 state; prove constraints and converge signed all-m transfer before atlas qualification.'},
 'M09':{'kind':'CODE_AND_THEORY_WITH_RATE_INPUT','completed':'clock-correct positive finite chemistry, opacity/reward and tangent; exact original HYREC inputs/tables recovered',
        'next':'Separate actual HYREC reaction clock, density, radiation frequency/escape and thermal expansion interfaces. Supply anisotropic radiation/atomic rates; couple their Jacobians and test against FULL/FLRW.'},
 'A03':{'kind':'NATIVE_SOLVER_ANALYSIS','completed':'direct collision and conditional transfer substeps executable',
        'next':'Run I-IX/admissible Class-B mode families, constraints, ell/m and time convergence, and independent FLRW/curved-limit comparisons. Do not wait indefinitely for an external implementation.'}}


def build():
    if hashlib.sha256(DAG.read_bytes()).hexdigest()!=DAG_SHA:raise ValueError('canonical R78 DAG identity changed')
    baseline=json.loads(SOURCE.read_text());dag=json.loads(DAG.read_text())
    if len(baseline['nodes'])!=60 or {n['id'] for n in baseline['nodes']}!={n['id'] for n in dag['nodes']}:
        raise ValueError('sixty-node identity mismatch')
    nodes=[]
    for n in baseline['nodes']:
        node_id=n['id'];jobs=SQ_JOBS.get(node_id,PHY_JOBS.get(node_id,AXIS_JOBS.get(n['paper'],[])))
        blockers=n['all_blockers_including_dependencies']
        nodes.append({'id':node_id,'paper':n['paper'],'original_acceptance':n['original_acceptance'],
                      'science_status':n['science_status'],'effective_hard_dependencies':n['effective_hard_dependencies'],
                      'conditional_jobs':jobs,'required_data_actions':{k:DATA_ACTIONS[k] for k in blockers if k in DATA_ACTIONS},
                      'remaining_solver_actions':{k:SOLVER_ACTIONS[k] for k in blockers if k in SOLVER_ACTIONS},
                      'other_model_or_analysis_blockers':[k for k in blockers if k not in DATA_ACTIONS and k not in SOLVER_ACTIONS],
                      'source_specific_next_actions':n.get('next_action',[]),'new_scientific_acceptance':False})
    return {'schema':'htt.r101.conditional_execution/1','parent':'f8931fbef075d55c2c2a3caee8b8f5db5174b16b',
            'science_authority':str(DAG.relative_to(ROOT)),'science_authority_sha256':DAG_SHA,
            'r100_overlay_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            'original_42_sha256':baseline['original_42_payload_sha256'],'next_id':baseline['next_id'],
            'counts':{'nodes':len(nodes),'canonical_edges':len(dag['edges']),'new_science_acceptances':0},
            'jobs':{k:{'module':v[0],'args':v[1],'result':v[2]} for k,v in JOBS.items()},'nodes':nodes}


def render(data):
    lines=['# R101 60-node conditional execution map','',
           'Canonical scientific dependencies/acceptances and statuses are inherited unchanged. A job runs a reusable conditional capability; it does not complete its mapped scientific node.','',
           '| Node | Axis | Inherited science state | Executable R101 jobs | Residual inputs/models |','|---|---|---|---|---|']
    for n in data['nodes']:
        blocked=list(n['required_data_actions'])+list(n['remaining_solver_actions'])+n['other_model_or_analysis_blockers']
        lines.append(f"| {n['id']} | {n['paper']} | {n['science_status']} | {', '.join(n['conditional_jobs'])} | {', '.join(blocked)} |")
    return '\n'.join(lines)+'\n'


def execute(job_ids):
    OUT.mkdir(parents=True,exist_ok=True);receipts=[]
    for name in dict.fromkeys(job_ids):
        module,args,filename=JOBS[name];command=[sys.executable,'-B','-m',module,*args]
        p=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
        (OUT/(name+'.stderr.log')).write_text(p.stderr)
        status='EXECUTED_CONDITIONAL' if p.returncode==0 else 'EXECUTION_FAILED'
        try:value=json.loads(p.stdout) if p.returncode==0 else None
        except json.JSONDecodeError:value=None;status='INVALID_OUTPUT'
        if value is not None:(OUT/filename).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
        else:(OUT/(name+'.stdout.log')).write_text(p.stdout)
        receipts.append({'job':name,'command':command,'returncode':p.returncode,'status':status,
                         'result':filename if value is not None else None})
        # Independent capabilities continue when one external source is absent.
    (OUT/'EXECUTION_RECEIPT.json').write_text(json.dumps(receipts,indent=2)+'\n')
    return receipts


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['prepare','analysis','science'])
    p.add_argument('--node',default='SQ-CF4');p.add_argument('--all',action='store_true')
    args=p.parse_args(argv);data=build();OUT.mkdir(parents=True,exist_ok=True)
    if args.mode=='prepare':
        (OUT/'NODE60_EXECUTION.json').write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
        (OUT/'NODE60_EXECUTION.md').write_text(render(data));print(json.dumps(data['counts']));return 0
    row=next((n for n in data['nodes'] if n['id']==args.node),None)
    if row is None:raise ValueError('unknown node '+args.node)
    if args.mode=='science':print(json.dumps(row,indent=2));return 0 if row['science_status']=='INHERITED_COMPLETED_SCOPED' else 3
    jobs=list(JOBS) if args.all else row['conditional_jobs'];receipts=execute(jobs)
    print(json.dumps(receipts,indent=2));return 0 if all(x['status']=='EXECUTED_CONDITIONAL' for x in receipts) else 3


if __name__=='__main__':raise SystemExit(main())
