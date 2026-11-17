"""One-shot additive R65 integration after actual research and fresh PASS review.

Draft only until root reviews and executes. Preserves original42 nodes, paper
acceptances, all R63/R64 paper pointers and existing cards. Does not train, fit,
commit, push, create a PR/worktree/clone/agent prompt, or launch a successor.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import yaml

BASELINE = 'd76ef3a4e9b33c4703a02647b3aa850004d04253'
CORE_HASH = 'e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d'
PR = 'PR-R65-DIPOLE-ANOMALY'
PARENT = 'PR-R64-DIRECTIONAL-HUBBLE'
BASE = Path('docs/research_program/observational_publication_20261015')
FOLDER = BASE / 'R65_DIPOLE_ANOMALY_20261117'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def encoded(value):
    return json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n'


def remove_pr(value):
    if isinstance(value, dict):
        return {k: remove_pr(v) for k, v in value.items()}
    if isinstance(value, list):
        return [remove_pr(v) for v in value if v != PR]
    return value


def run(root, review_status):
    root = Path(root).resolve()
    folder = root / FOLDER
    record_path = folder / 'RESEARCH_RECORD.json'
    record = load(record_path)
    if record.get('baseline_commit') != BASELINE or record.get('selected_paper') != 'P4':
        raise ValueError('unexpected R65 baseline or paper')
    stages = record.get('stages', [])
    if len(stages) != 10 or any(s.get('number') != j or s.get('status') != 'complete'
                                for j, s in enumerate(stages[:9], 1)):
        raise ValueError('completed R1-R9/C1-C9 required')
    if stages[9].get('number') != 10 or stages[9].get('status') == 'complete':
        raise ValueError('stage10 must remain incomplete until this reviewed finalization')
    if record.get('submission_status') != 'NOT_READY_TO_SUBMIT':
        raise ValueError('research submission decision changed')
    review = load(folder / 'REVIEW/final_review.json')
    if (not review_status.strip() or review.get('verdict') != 'PASS'
            or not isinstance(review.get('findings'), list)):
        raise ValueError('fresh independent PASS and explicit findings list required')
    if any(f.get('status') != 'CLOSED' for f in review['findings']):
        raise ValueError('review findings remain open')
    if review.get('journal_submission', review.get('submission_status')) != 'NOT_READY_TO_SUBMIT':
        raise ValueError('review changed submission decision')
    if any(review.get(k) not in (None, 'NOT_READY_TO_SUBMIT')
           for k in ('journal_submission', 'submission_status')):
        raise ValueError('conflicting submission decisions')
    summary_path = folder / 'RESULTS/INTERPRETATION_SUMMARY.json'
    s = load(summary_path)
    expected_dimensions = dict(observed_models=12, independent_bin_fits=36,
                               total_observed_optimizations=102, bootstrap_catalogues=512,
                               RACS_posterior_models=6, tests_passed=37,
                               original_observed_models=8, source_refinement_observed_models=4,
                               original_tests_passed=24, overlap_tests_passed=13,
                               new_RACS_training_or_fits=0)
    if (s.get('baseline_commit') != BASELINE or s.get('publication_status') != 'NOT_READY_TO_SUBMIT'
            or any(s.get(k) != v for k, v in expected_dimensions.items())
            or s.get('integrated_flux_input_gap_closed') is not True
            or any(s.get(k) is not False for k in ('physical_anomaly_claim','global_tilt_claim','bianchi_assignment'))):
        raise ValueError('unexpected actual science dimensions or claim/status contract')
    provider_counts = s['provider_source_geometries']['provider_integrated']['observed_counts_per_bin']
    if sum(provider_counts) != 263158 or len(provider_counts) != 3:
        raise ValueError('reviewed actual provider integrated sample differs')
    if set(s['source_definition_paired_results']) != {'dipole','dipole_stf'}:
        raise ValueError('paired source-definition results incomplete')
    if s['source_definition_covariance_ablation'].get('physical_anomaly_significance') is not False:
        raise ValueError('source selection contrast relabeled as physical anomaly significance')

    titles = [
        ('Fix the single P4 dipole-anomaly question and existing-checkout completion contract',
         ['RESEARCH_RECORD.json','DESIGN.md']),
        ('Reuse dipole history, exact source identities and current primary literature',
         ['REVIEW/r65_history.md','REVIEW/r65_history_sources.json','REVIEW/r65_literature.md','REVIEW/r65_sources.json']),
        ('Separate count dipole, observer boost, nuisance quotient and physical frame claims',
         ['DESIGN.md','THEORY.md']),
        ('Fix the actual disjoint-bin conditional ring likelihood and posterior projection experiment',
         ['DESIGN.md']),
        ('Derive the declination quotient, bin response and signed five-view/weighted posterior transports',
         ['THEORY.md','REVIEW/WOLFRAM_CHECK.json','REVIEW/SYMPY_CHECK.json']),
        ('Verify affected likelihood derivatives, nulls, weights, covariance and same-source overlap',
         ['RESULTS/AFFECTED_TEST_RECEIPT.json','RESULTS/OVERLAP_TEST_RECEIPT.json']),
        ('Execute actual NVSS models, conditional bootstrap and six RACS weighted posterior pushforwards',
         ['RESULTS/NVSS_EXECUTION.json','RESULTS/RACS_EXECUTION.json']),
        ('Resolve integrated-flux input, compute paired source-selection contrasts and decide finite P4 route',
         ['R8_SOURCE_REFINEMENT.md','REVIEW/r65_nvss_flux_source.md','RESULTS/PROVIDER_NVSS_EXECUTION.json',
          'RESULTS/FINAL_INTERPRETATION_EXECUTION.json','RESULTS/INTERPRETATION_SUMMARY.json','REPORT_KO.md','RESEARCH_PLAN_KO.md']),
        ('Close one fresh independent final review and any bounded correction episode',
         ['REVIEW/final_review.md','REVIEW/final_review.json','VALIDATION.md']),
        ('Preserve finite P4 manuscript gates, additive canonical DAG and scoped release',
         ['RESEARCH_PLAN_KO.md','VALIDATION.md','DAG_VALIDATION.json']),
    ]
    missing = sorted({f for _, ev in titles[:9] for f in ev if not (folder/f).is_file()})
    if missing:
        raise ValueError('completed-stage evidence missing: '+', '.join(missing))
    backlog = root / 'docs/codex_handoff/pr_backlog.yaml'
    status = root / 'docs/codex_handoff/pr_status.yaml'
    old_text, status_text = backlog.read_text(), status.read_text()
    old, status_before = yaml.safe_load(old_text), yaml.safe_load(status_text)
    if len(old['prs']) != 288 or len(status_before['completed']) != 223:
        raise ValueError('canonical counts changed from288/223')
    if any(c['id'] == PR for c in old['prs']) or PR in status_before['completed']:
        raise ValueError('R65 insertion is one-shot')
    if not any(c['id'] == PARENT for c in old['prs']) or PARENT not in status_before['completed']:
        raise ValueError('completed R64 predecessor not preserved')
    card = dict(
        id=PR, wave=0, title='Measure identified radio-dipole components and paired peak-versus-integrated source-selection contrasts',
        owner='HTT', depends=[PARENT],
        files=[str(FOLDER),'scripts/r65','tests/r65','htt/htt/htt/infer/r65_count_quotient.py',
               'htt/htt/htt/infer/r65_racs.py','htt/htt/htt/infer/r65_overlap.py',
               'docs/codex_handoff/pr_backlog.yaml','docs/codex_handoff/pr_status.yaml',
               str(BASE/'PUBLICATION_DAG.json'),str(BASE/'README.md')],
        tests=[
            'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -m pytest -p no:cacheprovider -q tests/r65',
            '.venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml',
            '.venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check',
            '.venv/bin/python -B scripts/htt_publication_dag.py --validate'],
        dod=[
            'Complete one sequential ten-stage owner-selected P4 study with actual count fields and source-conditional weighted posterior carriers.',
            'Derive the exact declared ring-response quotient, disjoint-bin response and signed tensor/five-view maps; retain c and source conventions.',
            'Execute12 observed models,36 bin fits,102 observed optimizations,512 conditional bootstrap catalogues and six actual RACS posterior pushforwards.',
            'Resolve the integrated-flux input gap and preserve same-provider peak/integrated memberships, full cross covariance, paired contrast and finite response-precision diagnostic.',
            'Close one actual fresh independent review; preserve original42, existing P4/R63 pointer, all paper acceptances and NOT_READY_TO_SUBMIT with finite manuscript gates.'],
        notes=str(FOLDER/'RESEARCH_DAG.json'),
        kill='No physical anomalous observer velocity, unrestricted global tilt, Bianchi attribution, generic new no-go or independent multiplication of same-source selections; no automatic successor or local-agent prompt.',
        level='L0',scope='science',risk='R2',claim_tier_ceiling='C0',user_authorized=True,
        authorization='2026-11-17 owner explicitly selected dipole anomaly for one sequential full ten-stage study; inherited non-force GitHub publication authority persists.')
    needle = '  - '+PARENT+'\n'
    if old_text.count(needle) != 2:
        raise ValueError('expected two predecessor entries in ordered lists')
    new_text = old_text.replace(needle,needle+'  - '+PR+'\n')
    new_text = new_text.rstrip()+'\n'+yaml.safe_dump([card],sort_keys=False,allow_unicode=True,width=105)
    parsed = yaml.safe_load(new_text)
    if len(parsed['prs']) != 289 or parsed['prs'][:-1] != old['prs']:
        raise ValueError('old cards changed')
    if remove_pr({k:v for k,v in parsed.items() if k!='prs'}) != {k:v for k,v in old.items() if k!='prs'}:
        raise ValueError('old backlog metadata changed')
    if PR in status_text or '\ncompleted:\n' not in status_text:
        raise ValueError('unexpected status source')
    new_status = status_text.replace('\ncompleted:\n','\ncompleted:\n- '+PR+'\n',1)
    new_status = new_status.rstrip()+'\n\n# '+PR+': complete_scoped C0. Actual radio count nuisance quotient and same-source flux-definition contrast; original42/P4 acceptance and R63 pointer preserved. No automatic successor or local-agent prompt.\n'
    expected_status = copy.deepcopy(status_before)
    expected_status['completed'] = [PR]+expected_status['completed']
    if yaml.safe_load(new_status) != expected_status or len(expected_status['completed']) != 224:
        raise ValueError('status mutation exceeds one completion')

    publication = root / BASE / 'PUBLICATION_DAG.json'
    pub = load(publication)
    if len(pub['nodes']) != 42 or digest(pub['nodes']) != CORE_HASH:
        raise ValueError('original42 payload changed')
    papers_before = copy.deepcopy(pub['papers'])
    previous = copy.deepcopy(pub['current_scientific_route'])
    if previous['canonical_pr'] != PARENT:
        raise ValueError('unexpected predecessor route')
    p4 = next(p for p in pub['papers'] if p['id']=='P4')
    if 'current_scoped_dipole_anomaly' in p4:
        raise ValueError('P4 dipole companion pointer already exists')
    pub.setdefault('previous_scientific_routes',[]).append(previous)
    pub['current_scientific_route'] = dict(
        date='2026-11-17',source_base_sha=BASELINE,canonical_pr=PR,selected_paper='P4',
        scope='Only dipole anomaly: one sequential ten-stage actual-data theory/coding study',
        report=str(FOLDER/'REPORT_KO.md'),plan=str(FOLDER/'RESEARCH_PLAN_KO.md'),
        research_dag=str(FOLDER/'RESEARCH_DAG.json'),status='COMPLETE_SCOPED_C0',review=review_status,
        active_result=str(FOLDER/'RESULTS/INTERPRETATION_SUMMARY.json'),
        original_six_tracks_and_42_gates_preserved=True,automatic_successor=False,
        local_agent_prompt_created=False,submission_status='NOT_READY_TO_SUBMIT',new_no_go=False,
        authorization='Current explicit owner single ten-stage branch request; inherited non-force GitHub publication authority.')
    p4['current_scoped_dipole_anomaly'] = dict(
        pr=PR,report=str(FOLDER/'REPORT_KO.md'),plan=str(FOLDER/'RESEARCH_PLAN_KO.md'),
        research_dag=str(FOLDER/'RESEARCH_DAG.json'),original_acceptance_status_preserved=True)
    restored = copy.deepcopy(pub['papers'])
    next(p for p in restored if p['id']=='P4').pop('current_scoped_dipole_anomaly')
    if restored != papers_before or digest(pub['nodes']) != CORE_HASH:
        raise ValueError('old paper contracts, existing R63/P4 pointer or original42 states changed')
    pub['next_action'] = (
        'Consolidate the achieved same-source selection-dependent radio dipole result into P4. '
        'Use one bounded selection/morphology/component-grouping null and compare one conventional method on the identical estimand and source selection. '
        'Require explicit flux-bin LSS cross covariance before extending the result to a physical excess claim. '
        'Optionally refit one actual RACS field under the same nuisance quotient before a same-estimand comparison. '
        'Integrated-flux input is resolved; remaining calibration obligations do not erase that result. '
        'End with the achieved manuscript claim or its exact remaining submission gate; do not automatically launch another loop.')
    tasks = [dict(id=f'R65-{j:02d}',theory_stage=f'R{j}',coding_stage=f'C{j}',title=title,
                  depends_on=[] if j==1 else [f'R65-{j-1:02d}'],status='complete_scoped',evidence=ev)
             for j,(title,ev) in enumerate(titles,1)]
    future = [
        dict(id='P4-R65-SOURCE-NULL',depends_on=['R65-10'],status='pending_conditional',
             completed='Provider integrated-flux column and exact bytes qualified; paired peak/integrated same-component migration and source-Poisson covariance executed.',
             needed='Choose one physically specified selection/morphology/component-grouping null, preserving parent peak detection, resolved-source response, spectral assumptions and matched memberships.',
             stop='Measure the paired target shift under that one qualified null or record the exact unavailable input; no new source-size cut without a scientific selection contract.'),
        dict(id='P4-R65-LSS-CROSS',depends_on=['R65-10'],status='unresolved_input',
             needed='Obtain or justify actual flux-bin redshift/bias and angular clustering cross inputs, then transport them through the fixed mask/ring quotient and paired-source operators.',
             stop='Deliver one covariance/sensitivity result for the named dipole/selection contrast; do not call source-Poisson tails a calibrated physical anomaly significance.'),
        dict(id='P4-R65-MATCHED-COMPARISON',depends_on=['R65-10'],status='pending_conditional',
             needed='Run one conventional method using the same observable, retained sources, nuisance response and covariance as the R65 quotient carrier.',
             stop='Report target agreement, bias/variance and precise scope; generic GLS/five-view/multiple-bin novelty or information superiority is not established.'),
        dict(id='P4-R65-RACS-REFIT',depends_on=['R65-10'],status='optional_for_same_estimand_comparison',
             completed='Six weighted source-conditional RACS posterior geometric pushforwards executed; these are not refits removing declination selection.',
             needed='Select one actual RACS count field, its calibration inputs and the true same quotient/estimand for an optional bounded refit.',
             stop='Produce one matched projection result or retain existing source-conditional posterior scope; no assumed independent joint NVSS significance.'),
        dict(id='P4-R65-PAPER',depends_on=['P4-R65-SOURCE-NULL','P4-R65-MATCHED-COMPARISON'],
             required_for_physical_excess_claim=['P4-R65-LSS-CROSS'],
             optional_for_stronger_claim=['P4-R65-RACS-REFIT'],status='pending_conditional',
             needed='Consolidate a source/selection-dependent radio dipole manuscript at the achieved claim level, retaining paired uncertainty, response-precision limits and conventional prior art.',
             stop='Keep P4 NOT_READY_TO_SUBMIT until its actual acceptance is met; integrate into the existing P4 companion if standalone novelty is insufficient, with no successor launch.'),
    ]
    scoped = dict(schema='htt.r65.research_dag/1',baseline_commit=BASELINE,canonical_pr=PR,parent_pr=PARENT,
                  selected_paper='P4',claim_tier='C0',scope='Single sequential ten-stage dipole-anomaly study',
                  status='COMPLETE_SCOPED_C0',tasks=tasks,future_science=future,
                  original_42_node_payload_sha256=CORE_HASH,original_42_node_states_changed=False,
                  key_results=dict(sources=s['sources'],**expected_dimensions,
                                   provider_integrated_selected_components=263158,
                                   integrated_flux_input_gap_closed=True,
                                   source_definition_paired_results=s['source_definition_paired_results'],
                                   source_definition_covariance_ablation=s['source_definition_covariance_ablation'],
                                   beta_residual_precision=s['provider_beta_residual_precision'],
                                   RACS_projection_scope=s['RACS_projection_scope'],
                                   new_independent_sources=0,new_joint_survey_likelihood=False),
                  interpretation_summary_sha256=hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                  conditions='Conditional ring-count law and empirical same-source Poisson influence covariance; apparent source-definition change does not isolate instrumental bias from population change. Physical selection, component morphology and bin LSS cross covariance remain to qualify.',
                  physical_anomaly_claim=False,global_tilt_claim=False,bianchi_assignment=False,new_no_go=False,
                  automatic_successor=False,local_agent_prompt_created=False,submission_status='NOT_READY_TO_SUBMIT')

    readme = root / BASE / 'README.md'
    text = readme.read_text()
    header = '# HTT 관측논문 6트랙 출판 중심 DAG\n\n'
    old_header = '## Current directional Hubble study — R64, 2026-11-17'
    if text.count(header)!=1 or text.count(old_header)!=1:
        raise ValueError('README differs from observed baseline')
    text = text.replace(old_header,'## Previous directional Hubble study — R64, 2026-11-17',1)
    text = text.replace('현재 선택된 P3 companion 경로다','이전 P3 companion 경로다',1)
    entry = (
        '## Current dipole-anomaly study — R65, 2026-11-17\n\n'
        '[R65 실제 radio dipole·source-selection 결과](R65_DIPOLE_ANOMALY_20261117/REPORT_KO.md), '
        '[P4 논문 계획](R65_DIPOLE_ANOMALY_20261117/RESEARCH_PLAN_KO.md), '
        '[연구 DAG](R65_DIPOLE_ANOMALY_20261117/RESEARCH_DAG.json)이 현재 선택된 P4 companion 경로다. '
        '실제 NVSS의 declination-ring nuisance quotient와 disjoint flux bins에서12개 model·36개 bin fit·102개 observed optimization, '
        '512개 conditional bootstrap과6개 RACS weighted posterior pushforward를 수행하고37개 affected test를 통과했다. '
        'Provider integrated-flux 입력을 확보해263,158개 component와 동일 provider의 peak_flux 선택을 비교했다. '
        '실제 shared-source covariance를 보존한 peak→integrated dipole 차이는 선언한 Poisson working law 안에서 남으며, '
        '이 차이를 instrumental bias나 physical velocity anomaly로 단정하지 않는다. RACS 결과는 source posterior의 geometric projection이고 '
        '동일 nuisance quotient로 refit한 결과가 아니다. 원래42개 gate·P4 acceptance와 R63 local/global companion pointer를 보존하며 '
        '제출 상태는 NOT_READY_TO_SUBMIT이다. 좁은 companion의 다음 작업은 source/component-null·matched-estimand·원고 통합으로 제한한다. '
        'LSS cross covariance는 물리적 excess 주장 확장에 필요하며, RACS 동일 nuisance refit은 더 강한 비교를 선택할 때만 추가한다.\n\n')
    text = text.replace(header,header+entry,1)
    receipt = dict(canonical_card_added=PR,old_backlog_entries=288,new_backlog_entries=289,
                   old_completed_count=223,new_completed_count=224,
                   previous_cards_semantically_unchanged=True,original_node_payload_sha256=CORE_HASH,
                   original_nodes_unchanged=True,original_paper_contracts_preserved=True,
                   old_P4_keys_and_R63_pointer_preserved=True,selected_scope='P4 companion only',review=review_status,
                   interpretation_sha256=hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                   stage10_completed_only_after_review=True,new_no_go=False,
                   automatic_successor=False,local_agent_prompt_created=False)
    finalized_record = copy.deepcopy(record)
    finalized_record['stages'][9]['status'] = 'complete'
    restored_record = copy.deepcopy(finalized_record)
    restored_record['stages'][9]['status'] = record['stages'][9].get('status')
    if restored_record != record:
        raise ValueError('research record mutation exceeds stage10 completion')
    payloads = {backlog:new_text,status:new_status,publication:encoded(pub),readme:text,
                record_path:encoded(finalized_record),folder/'RESEARCH_DAG.json':encoded(scoped),
                folder/'DAG_UPDATE_RECEIPT.json':encoded(receipt)}
    if any(p.exists() for p in (folder/'RESEARCH_DAG.json',folder/'DAG_UPDATE_RECEIPT.json')):
        raise ValueError('scoped DAG already exists; refuse repeated insertion')
    # As in R64: every scientific, review, old-card/core/paper preservation and
    # one-shot check is completed before the first write. Root owns execution,
    # mirror generation, validation and any separately authorized publication.
    for path,body in payloads.items():
        path.write_text(body.rstrip()+'\n')
    print(encoded(receipt),end='')
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path.cwd())
    parser.add_argument('--review-status',required=True)
    args=parser.parse_args()
    run(args.root,args.review_status)
