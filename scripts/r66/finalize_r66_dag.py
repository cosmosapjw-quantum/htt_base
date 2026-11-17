"""One additive R66 closeout after actual data, tests and independent review.

Preserve original42/paper acceptances and all older cards. No commit, push,
successor loop, local-agent prompt, raw-data edit or external publication here.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import yaml

BASE=Path('docs/research_program/observational_publication_20261015')
FOLDER=BASE/'R66_LOWELL_PHYSICAL_OBSERVABLES_20261117'
PR='PR-R66-LOWELL-PHYSICAL-OBSERVABLES'
PARENT='PR-R65-DIPOLE-ANOMALY'
BASELINE='3dd1893a3f74af8e1387c844e07897efeabdd0bf'
CORE_HASH='e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d'


def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def read(p):return json.loads(p.read_text())
def encode(x):return json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
def without_pr(x):
    if isinstance(x,dict):return {k:without_pr(v) for k,v in x.items()}
    if isinstance(x,list):return [without_pr(v) for v in x if v!=PR]
    return x


def run():
    r=read(FOLDER/'RESEARCH_RECORD.json');review=read(FOLDER/'REVIEW/final_review.json')
    result=read(FOLDER/'RESULTS/OBSERVABLES.json');extraction=read(FOLDER/'RESULTS/OBSERVED_EXTRACTION.json');reference=read(FOLDER/'RESULTS/IDEAL_REFERENCE.json')
    assert r['baseline_commit']==BASELINE and r['selected_paper']=='P2'
    assert len(r['stages'])==10 and all(s['status']=='complete' for s in r['stages'][:9])
    assert r['stages'][9]['status']!='complete' and review['verdict']=='PASS'
    assert all(f.get('status')=='CLOSED' for f in review['findings'])
    assert review['submission_status']==r['submission_status']=='NOT_READY_TO_SUBMIT'
    assert extraction['status']=='OBSERVATIONS_COMPLETE'
    assert reference['status']=='COMPLETE_IDEAL_REFERENCE' and reference['N']==4096
    assert result['status']=='ACTUAL_OBSERVATIONS_IDEAL_REFERENCE_COMPLETE'
    assert result['physical_PTE_qualified'] is False and result['instantaneous_spacetime_shear_measured'] is False
    titles=[
        ('Fix the independent P2 low-ell-to-observable question',['RESEARCH_RECORD.json']),
        ('Reuse exact internal history and primary physical/statistical sources',['HISTORY.md','HISTORY_SOURCES.json','LITERATURE.md','SOURCES.json','SOURCE_ADDENDUM.md']),
        ('Choose a signed local radiation-stress target and physical claim scope',['THEORY.md','RESEARCH_RECORD.json']),
        ('Construct finite operator, physical image and nuisance identified set',['THEORY.md']),
        ('Implement native-pixel Commander extraction and tensor likelihood',['RESULTS/OBSERVED_EXTRACTION.json']),
        ('Validate units, moments, response, quotient, finite MC and same-sky covariance',['VALIDATION.md','RESULTS/TEST_RECEIPT.json']),
        ('Run two actual maps and an explicit ideal Gaussian reference; preserve the rejected zero-T bank',['RESULTS/OBSERVED_EXTRACTION.json','RESULTS/IDEAL_REFERENCE.json','RESULTS/SOURCE_FAILURE_AND_REPAIR.json','RESULTS/OBSERVABLES.json']),
        ('Evaluate physical corrections, paired estimator and conventional method',['PAIRED_CONSTRUCTION.md','IDEAL_REFERENCE.md','REPORT_KO.md','RESEARCH_PLAN_KO.md']),
        ('Close one fresh independent scientific/code review',['REVIEW/final_review.md','REVIEW/final_review.json']),
        ('Preserve original scientific gates and publish the scoped research unit',['RESEARCH_DAG.json','DAG_VALIDATION.json'])]
    assert all((FOLDER/p).is_file() for _,ev in titles[:9] for p in ev)
    backlog=Path('docs/codex_handoff/pr_backlog.yaml');status=Path('docs/codex_handoff/pr_status.yaml')
    bt,st=backlog.read_text(),status.read_text();b,s=yaml.safe_load(bt),yaml.safe_load(st)
    assert len(b['prs'])==289 and len(s['completed'])==224 and PARENT in s['completed']
    assert PR not in s['completed'] and all(p['id']!=PR for p in b['prs'])
    card=dict(id=PR,wave=0,title='Map actual Commander low multipoles to signed radiation-stress images and Doppler-nuisance quotients',
        owner='HTT',depends=[PARENT],files=[str(FOLDER),'scripts/r66','htt/htt/htt/infer/r66_radiation_quotient.py',
        'tests/test_r66_radiation_quotient.py',str(BASE/'PUBLICATION_DAG.json'),str(BASE/'README.md'),str(backlog),str(status)],
        tests=['OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -m pytest -p no:cacheprovider -q tests/test_r66_radiation_quotient.py',
        '.venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml',
        '.venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check','.venv/bin/python -B scripts/htt_publication_dag.py --validate'],
        dod=['Complete exactly one sequential ten-stage P2 theory/coding study using existing checkout and actual Commander data.',
             'Reuse R36 radiation physics and R60 STF; execute native map response, physical quotient and exact-in-model Gaussian law.',
             'Preserve signed data, shared-sky covariance, 100 rejected zero-I product identities, actual T content diagnostic, 4096 ideal synthetic carriers and original occupancy semantics.',
             'Report truncation/release dependence, nonlinear dipole-octupole contribution and same-input conventional power tensor comparison.',
             'Close one fresh independent review and preserve original42 and all existing paper acceptances.'],
        notes=str(FOLDER/'RESEARCH_DAG.json'),level='L0',scope='science',risk='R2',claim_tier_ceiling='C0',
        kill='No exact total-sky stress, instantaneous shear, unconditional anomaly, Bianchi attribution, new general no-go, automatic successor or local-agent prompt.',
        user_authorized=True,authorization='Explicit owner-selected low-ell physical-observables full10 study; inherited non-force branch push authorization.')
    needle='  - '+PARENT+'\n';assert bt.count(needle)==2
    bn=bt.replace(needle,needle+'  - '+PR+'\n').rstrip()+'\n'+yaml.safe_dump([card],sort_keys=False,allow_unicode=True,width=105)
    bp=yaml.safe_load(bn);assert len(bp['prs'])==290 and bp['prs'][:-1]==b['prs']
    assert without_pr({k:v for k,v in bp.items() if k!='prs'})=={k:v for k,v in b.items() if k!='prs'}
    assert '\ncompleted:\n' in st and PR not in st
    sn=st.replace('\ncompleted:\n','\ncompleted:\n- '+PR+'\n',1)
    expected=copy.deepcopy(s);expected['completed']=[PR]+expected['completed']
    assert yaml.safe_load(sn)==expected and len(expected['completed'])==225
    publication=BASE/'PUBLICATION_DAG.json';p=read(publication)
    assert len(p['nodes'])==42 and digest(p['nodes'])==CORE_HASH
    old_papers=copy.deepcopy(p['papers']);previous=copy.deepcopy(p['current_scientific_route'])
    assert previous['canonical_pr']==PARENT
    p2=next(x for x in p['papers'] if x['id']=='P2');pointer='current_scoped_lowell_physical_observables'
    assert pointer not in p2
    p.setdefault('previous_scientific_routes',[]).append(previous)
    p['current_scientific_route']=dict(date='2026-11-17',source_base_sha=BASELINE,canonical_pr=PR,selected_paper='P2',
        scope='Only low-ell morphology relating to physical observables; one full10 unit',status='COMPLETE_SCOPED_C0',
        report=str(FOLDER/'REPORT_KO.md'),plan=str(FOLDER/'RESEARCH_PLAN_KO.md'),research_dag=str(FOLDER/'RESEARCH_DAG.json'),
        active_result=str(FOLDER/'RESULTS/OBSERVABLES.json'),review='PASS: one fresh independent review',
        original_six_tracks_and_42_gates_preserved=True,submission_status='NOT_READY_TO_SUBMIT',
        automatic_successor=False,local_agent_prompt_created=False,new_no_go=False)
    p2[pointer]=dict(pr=PR,report=str(FOLDER/'REPORT_KO.md'),plan=str(FOLDER/'RESEARCH_PLAN_KO.md'),
                    research_dag=str(FOLDER/'RESEARCH_DAG.json'),original_acceptance_status_preserved=True)
    restored=copy.deepcopy(p['papers']);next(x for x in restored if x['id']=='P2').pop(pointer)
    assert restored==old_papers and digest(p['nodes'])==CORE_HASH
    p['next_action']='Consolidate the actual low-ell radiation-stress image into P2. Bind exact Commander response or retain the released-map conditional scope; compare one fixed conventional harmonic reconstruction on the same estimand, then decide integrated methods/results publication. Keep original42 acceptance and P2 submission gates. Do not launch another loop automatically.'
    tasks=[dict(id=f'R66-{i:02d}',theory_stage=f'R{i}',coding_stage=f'C{i}',title=t,
                depends_on=[] if i==1 else [f'R66-{i-1:02d}'],status='complete_scoped',evidence=ev)
           for i,(t,ev) in enumerate(titles,1)]
    future=[dict(id='P2-R66-RESPONSE',depends_on=['R66-10'],status='pending_conditional',
            needed='Bind exact Commander DQ/beam/temperature-unit/simulation response or close manuscript scope at the achieved conditional released-map result.',
            stop='One source-qualified response/rank update or explicit achieved-scope decision; no restricted SEVEM acquisition.'),
        dict(id='P2-R66-MATCHED-METHOD',depends_on=['R66-10'],status='pending_conditional',
            completed='Same-input conventional power-tensor comparison and paired GLS under an explicitly ideal reference executed; observed band sensitivity remains.',
            needed='One frozen conditional harmonic/QML reconstruction comparison if claiming whole-sky physical stress; independent fixed-rule validation for paired estimator.',
            stop='Same-estimand bias/variance/coverage table or integrate as P2 methods if only coordinate equivalence remains.'),
        dict(id='P2-R66-PAPER',depends_on=['P2-R66-RESPONSE','P2-R66-MATCHED-METHOD'],status='pending_conditional',
            needed='Integrate physical map, actual data, error hierarchy and closest-method comparison into P2 at achieved claim level.',
            stop='Submit only after existing P2 acceptance; otherwise preserve NOT_READY_TO_SUBMIT and end standalone novelty claim.')]
    dag=dict(schema='htt.r66.research_dag/1',baseline_commit=BASELINE,canonical_pr=PR,parent_pr=PARENT,selected_paper='P2',
        status='COMPLETE_SCOPED_C0',tasks=tasks,future_science=future,original_42_node_payload_sha256=CORE_HASH,
        original_42_node_states_changed=False,submission_status='NOT_READY_TO_SUBMIT',claim_tier='C0',
        qualified_actual_temperature_MC_count=0,zero_I_products_audited=100,ideal_synthetic_carriers=4096,physical_PTE_qualified=False,automatic_successor=False,local_agent_prompt_created=False,new_no_go=False)
    readme=BASE/'README.md';text=readme.read_text();header='# HTT 관측논문 6트랙 출판 중심 DAG\n\n'
    assert text.count(header)==1 and text.count('## Current dipole-anomaly study — R65, 2026-11-17')==1
    text=text.replace('## Current dipole-anomaly study — R65, 2026-11-17','## Previous dipole-anomaly study — R65, 2026-11-17',1)
    text=text.replace('현재 선택된 P4 companion 경로다','이전 P4 companion 경로다',1)
    entry='## Current low-ell physical-observables study — R66, 2026-11-17\n\n[R66 실제 Commander 결과](R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/REPORT_KO.md), [P2 논문화 계획](R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESEARCH_PLAN_KO.md), [연구 DAG](R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESEARCH_DAG.json)가 현재 선택된 P2 companion이다. 실제 PR3/PR4 온도를 처리하고 공개005a100개의 I=0을 확인해 온도법칙에서 제외했다. 별도 scalarT제품을 확인하고 명시적인 이상적 Gaussian공분산과4096합성carrier를 계산했다. 이를 바탕으로 signed radiation-stress proxy·DQ quotient·dipole–octupole 비선형 항·공동 operator covariance·같은 입력의 power tensor를 계산했다. R36/R60 이론·코드는 재사용이며 새 일반이론으로 주장하지 않는다. harmonic truncation과 release dependence 및 미확보 upstream response를 보존한다. 물리적 anomaly나 spacetime shear 측정은 주장하지 않으며 원래42개·모든 논문 acceptance와 NOT_READY_TO_SUBMIT을 유지한다. 다음 범위는 정확한 response/동일 estimand 비교/원고 통합 세 패키지로 수렴한다.\n\n'
    text=text.replace(header,header+entry,1)
    r['stages'][9]['status']='complete'
    receipt=dict(canonical_card_added=PR,old_backlog_entries=289,new_backlog_entries=290,
        old_completed_count=224,new_completed_count=225,five_PR_checkpoint_required=True,
        previous_cards_semantically_unchanged=True,original_node_payload_sha256=CORE_HASH,
        original_nodes_unchanged=True,original_paper_contracts_preserved=True,selected_scope='P2 companion only',
        stage10_completed_only_after_review=True,automatic_successor=False,local_agent_prompt_created=False)
    assert not (FOLDER/'DAG_UPDATE_RECEIPT.json').exists()
    payloads={backlog:bn,status:sn,publication:encode(p),readme:text,FOLDER/'RESEARCH_RECORD.json':encode(r),
              FOLDER/'RESEARCH_DAG.json':encode(dag),FOLDER/'DAG_UPDATE_RECEIPT.json':encode(receipt)}
    for path,body in payloads.items():path.write_text(body.rstrip()+'\n')
    print(encode(receipt))


if __name__=='__main__':run()
