"""Apply the owner-authorized R61 scoped scientific DAG update exactly once."""
import hashlib
import json
from pathlib import Path
import yaml

root=Path.cwd()
base=Path('docs/research_program/observational_publication_20261015')
folder=base/'R61_KINEMATIC_MEASUREMENT_20261117'
pr='PR-R61-KINEMATIC-MEASUREMENT'
backlog=Path('docs/codex_handoff/pr_backlog.yaml')
status=Path('docs/codex_handoff/pr_status.yaml')
old_backlog=backlog.read_text();data=yaml.safe_load(old_backlog)
if any(x['id']==pr for x in data['prs']):raise ValueError('R61 card already exists')
card={
'id':pr,'wave':0,'title':'Measure conditional beyond-FLRW kinematic images and calibration-qualified depth contrasts',
'owner':'HTT','depends':['PR-R60-COVARIANCE-CALIBRATION'],
'files':[str(folder),'scripts/r61','tests/r61','htt/htt/htt/infer/r61_kinematic_images.py',
'htt/htt/htt/infer/r61_mixed_invariant.py','htt/htt/htt/infer/r61_box_comparison.py',
str(backlog),str(status),str(base/'PUBLICATION_DAG.json')],
 'tests':['OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -B -m pytest -q tests/r61',
'.venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml',
'.venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check',
'.venv/bin/python -B scripts/htt_publication_dag.py --validate'],
'dod':['Execute the single owner-selected ten-stage theory/coding loop on existing CF4 inputs, with full joint covariance and exact source identities.',
'Compute joint nonlinear kinematic images, actual mixed-function enclosures and actual coordinate-box comparison; separate additional triangle slack.',
'Fit one finite STF depth response, propagate cross-depth covariance and calibrations, and report local-extrapolation and response sensitivity.',
'Complete one fresh independent scientific review; close R61-F1 with affine-z or estimator-induced calibration budgets and preserve the actual counterexample.',
'Publish a finite paper plan and scoped results while preserving unresolved absolute expansion, vorticity, local transfer and survey coverage.'],
'notes':str(folder/'RESEARCH_DAG.json'),
'kill':'No physical shear/vorticity/FLRW discovery from conditional apparent coefficients; no endpoint-only bound for arbitrary depth-dependent calibration; no independent-factor multiplication of the seven source variants; no automatic successor or local-agent prompt.',
'level':'L0','scope':'science','risk':'R2','claim_tier_ceiling':'C0','user_authorized':True,
'authorization':'Current 2026-11-17 owner request selects only beyond-FLRW kinematic quantity measurement and all ten theory/coding stages; earlier source push authorization persists.'}
needle='  - PR-R60-COVARIANCE-CALIBRATION\n'
assert old_backlog.count(needle)==2
updated=old_backlog.replace(needle,needle+'  - '+pr+'\n')
updated=updated.rstrip()+'\n'+yaml.safe_dump([card],sort_keys=False,allow_unicode=True,width=105)
parsed=yaml.safe_load(updated);assert len(parsed['prs'])==len(data['prs'])+1
assert parsed['prs'][:-1]==data['prs']
backlog.write_text(updated)
s=status.read_text();assert '\ncompleted:\n' in s and pr not in s
s=s.replace('\ncompleted:\n','\ncompleted:\n- '+pr+'\n',1)
s+='\n# '+pr+': complete_scoped C0. One owner-selected ten-stage kinematic study; actual joint images, mixed extrema, coordinate-box comparison, rank16 STF depth contrast and local extrapolation. Fresh review PASS WITH MINOR REVISIONS; R61-F1 closed with released calibration-bias operator and actual endpoint-zero counterexample. Original42 science gates and unresolved physical/survey conditions preserved. No local-agent prompt or automatic successor.\n'
status.write_text(s)
publication=base/'PUBLICATION_DAG.json';pub=json.loads(publication.read_text())
core_before=hashlib.sha256(json.dumps(pub['nodes'],sort_keys=True).encode()).hexdigest()
previous=pub['current_scientific_route'];assert previous['canonical_pr']=='PR-R60-COVARIANCE-CALIBRATION'
pub.setdefault('previous_scientific_routes',[]).append(previous)
pub['current_scientific_route']={
'date':'2026-11-17','source_base_sha':'fb6ae9f21585e194ef29dabc91d79a529e0ac57e','canonical_pr':pr,
'selected_paper':'P6','scope':'Beyond-FLRW kinematic quantity measurement only; one integrated ten-stage study',
'report':str(folder/'REPORT_KO.md'),'plan':str(folder/'RESEARCH_PLAN_KO.md'),'research_dag':str(folder/'RESEARCH_DAG.json'),
'status':'COMPLETE_SCOPED_C0','review':'PASS_WITH_MINOR_REVISIONS; R61-F1 targeted closure complete',
'active_depth_result':str(folder/'RESULTS/DEPTH_CORRECTED/KINEMATIC_DEPTH.json'),
'original_six_tracks_and_42_gates_preserved':True,'automatic_successor':False,'local_agent_prompt_created':False,
'authorization':'Current explicit owner request for one branch and ten complete theory/coding stages; prior GitHub push authority retained.'}
pub['next_action']='Use the completed R61 kinematic report and finite paper plan. Stronger physical claims require a controlled finite-z response, independently supported calibration/bias budgets and matched-source survey coverage. No automatic audit successor.'
for paper in pub['papers']:
 if paper['id']=='P6':
  paper['current_scoped_measurement']={'pr':pr,'report':str(folder/'REPORT_KO.md'),'plan':str(folder/'RESEARCH_PLAN_KO.md'),'original_acceptance_status_preserved':True}
assert hashlib.sha256(json.dumps(pub['nodes'],sort_keys=True).encode()).hexdigest()==core_before
publication.write_text(json.dumps(pub,indent=2,ensure_ascii=False)+'\n')
readme=base/'README.md';s=readme.read_text();marker='## Current observed convergence — 2026-11-17'
assert marker in s
s=s.replace(marker,'## Previous multi-branch result — R60, 2026-11-17',1)
new='''## Current kinematic measurement study — R61, 2026-11-17

[R61 실제 운동학 결과·심사](R61_KINEMATIC_MEASUREMENT_20261117/REPORT_KO.md), [단일 논문 연구계획](R61_KINEMATIC_MEASUREMENT_20261117/RESEARCH_PLAN_KO.md), [연구 DAG](R61_KINEMATIC_MEASUREMENT_20261117/RESEARCH_DAG.json)이 현재 선택된 P6 가지의 진입점이다. 사용자 지정 10단계 이론·코딩 연구를 수행했고, 실제 CF4 공동 신뢰범위·혼합 불변량·STF 깊이 차이·국소 외삽 오차를 산출했다. 독립 심사의 R61-F1은 실제 calibration bias operator와 반례로 교정했다. 기존 다른 연구 가지와 42개 과학 gate의 상태는 보존하며 submission readiness를 자동 승인하지 않는다.

'''
s=s.replace('# HTT 관측논문 6트랙 출판 중심 DAG\n\n','# HTT 관측논문 6트랙 출판 중심 DAG\n\n'+new,1)
s=s.replace('을 현재 결과의 진입점으로 사용한다. 기존 six-track/42-node 과학 gate는 보존한다.','은 이전 여섯 가지 통합 결과의 진입점이다. 기존 six-track/42-node 과학 gate는 보존한다.',1)
readme.write_text(s)
titles=[
('Bind the kinematic question and live source identities',['REVIEW/owned_inputs.md','RESEARCH_RECORD.json']),
('Reuse internal history and verify primary physical sources',['REVIEW/kinematic_sources.md','REVIEW/paper_positioning.md']),
('Define physical state, likelihood and null directions',['THEORY.md']),
('Select finite observables, calibration body and depth response',['THEORY.md','RESEARCH_PLAN_KO.md']),
('Derive and implement quadratic and mixed confidence images',['THEORY.md','REVIEW/mixed_invariant_derivation.md']),
('Check symbolic identities and affected numerical implementations',['RESULTS/TESTS_EXECUTION.log','RESULTS/SYMBOLIC_CHECKS.json']),
('Execute the three actual owned-data measurements',['RESULTS/BATCH_EXECUTION.json']),
('Interpret measurements and correct the box comparison',['REPORT_KO.md','RESULTS/BOX_COMPARISON/R61_BOX_COMPARISON_RESULT.json']),
('Apply one fresh review and close its concrete finding',['REVIEW/final_review.md','REVIEW/R61_F1_CLOSURE.json']),
('Update paper plan and DAG, validate and publish the scoped branch',['VALIDATION.md','DAG_VALIDATION.json'])]
tasks=[]
for j,(title,evidence) in enumerate(titles,1):
 tasks.append({'id':f'R61-{j:02d}','theory_stage':'R'+str(j),'coding_stage':'C'+str(j),'title':title,
 'depends_on':[] if j==1 else [f'R61-{j-1:02d}'],'status':'complete_scoped','evidence':evidence})
future=[
{'id':'P1-PHYSICAL-REMAINDER','depends_on':['R61-10'],'status':'unresolved_input','needed':'A source/congruence-qualified finite-z cosmographic family and bounded higher-order/angular leakage; current fitted-state log closure does not provide a uniform physical remainder.'},
{'id':'P2-CALIBRATION','depends_on':['R61-10'],'status':'unresolved_input','needed':'Independent angular calibration information and an estimator-induced depth-bias budget; endpoint values alone are insufficient for arbitrary calibration.'},
{'id':'P3-MATCHED-SURVEY','depends_on':['P1-PHYSICAL-REMAINDER','P2-CALIBRATION'],'status':'unresolved_input','needed':'A matched raw-source comparison and selection/error/grouping/velocity law for survey-level coverage.'},
{'id':'P4-PAPER-DECISION','depends_on':['P3-MATCHED-SURVEY'],'status':'pending','needed':'One manuscript integration and evidence-based submission decision; no automatic additional research or review loop.'}]
dag={'schema':'htt.r61.research_dag/1','baseline_commit':'fb6ae9f21585e194ef29dabc91d79a529e0ac57e','canonical_pr':pr,
'parent_pr':'PR-R60-COVARIANCE-CALIBRATION','selected_paper':'P6','claim_tier':'C0','scope':'single ten-stage beyond-FLRW kinematic measurement study',
'owner_authorization':'Explicit current request; prior non-force GitHub publication authorization persists. No local-agent restart prompt.',
'status':'COMPLETE_SCOPED_C0','tasks':tasks,'future_science':future,
'original_42_node_payload_sha256':core_before,'original_42_node_states_changed':False,
'key_results':{'joint11_Sigma_union':[0,0.06254876346135956],'mixed_union':[-6.281510541990794e-7,5.044205982216458e-7],
'depth_slope_p_range':[0.5633190899534043,0.9432869179435148],'depth_RMS_union':[0,0.16340399602136726],
'actual_box_to_joint_width_range':[4.3857657902090255,5.81407726799209],
'calibration_counterexample_induced_RMS':[0.0009915764512313727,0.0014134199001246842]},
'conditions':'Fixed Gaussian law, chosen response and calibration family; apparent normalized kinematics, no unqualified local or survey inference.',
'next_action':'Use the single-paper plan; obtain the P1-P3 physical and observational inputs before promoting the claims.',
'automatic_successor':False,'local_agent_prompt_created':False,'submission_status':'NOT_READY_TO_SUBMIT'}
(folder/'RESEARCH_DAG.json').write_text(json.dumps(dag,indent=2,ensure_ascii=False)+'\n')
(folder/'DAG_UPDATE_RECEIPT.json').write_text(json.dumps({'canonical_card_added':pr,'old_backlog_entries':len(data['prs']),'new_backlog_entries':len(parsed['prs']),'previous_cards_semantically_unchanged':True,'original_node_payload_sha256':core_before,'original_nodes_unchanged':True,'selected_scope':'P6 only'},indent=2)+'\n')
print(json.dumps({'canonical_pr':pr,'new_card_count':len(parsed['prs']),'original42_nodes_unchanged':True,'new_scoped_tasks':10,'future_tasks':4},indent=2))
