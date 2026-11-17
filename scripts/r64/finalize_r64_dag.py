"""One-shot additive R64 integration after completed research and fresh review.

Does not launch a successor, modify original42 nodes or paper acceptances,
commit, push, or create a local coding-agent prompt. Root owns execution.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

import yaml

BASELINE = '33d87dd3e4a787e477327d37ee00b40e790211c9'
CORE_HASH = 'e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d'
PR = 'PR-R64-DIRECTIONAL-HUBBLE'
PARENT = 'PR-R63-LOCAL-BOOST-GLOBAL-TILT'
BASE = Path('docs/research_program/observational_publication_20261015')
FOLDER = BASE / 'R64_DIRECTIONAL_HUBBLE_20261117'


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
    record = load(folder / 'RESEARCH_RECORD.json')
    if record.get('baseline_commit') != BASELINE or record.get('selected_paper') != 'P3':
        raise ValueError('unexpected R64 baseline or paper')
    stages = record.get('stages', [])
    if len(stages) != 10 or any(s.get('number') != j or s.get('status') != 'complete'
                                for j, s in enumerate(stages[:9], 1)):
        raise ValueError('completed R1-R9/C1-C9 required')
    if record.get('submission_status') != 'NOT_READY_TO_SUBMIT':
        raise ValueError('research submission decision changed')
    review = load(folder / 'REVIEW/final_review.json')
    if not review_status.strip() or review.get('verdict') != 'PASS' or 'findings' not in review:
        raise ValueError('fresh independent PASS and explicit findings required')
    if any(f.get('status') != 'CLOSED' for f in review['findings']):
        raise ValueError('review findings remain open')
    if review.get('journal_submission', review.get('submission_status')) != 'NOT_READY_TO_SUBMIT':
        raise ValueError('review changed submission decision')
    if any(review.get(k) not in (None, 'NOT_READY_TO_SUBMIT')
           for k in ('journal_submission', 'submission_status')):
        raise ValueError('conflicting submission decisions')
    summary_path = folder / 'RESULTS/INTERPRETATION_SUMMARY.json'
    s = load(summary_path)
    if (s.get('publication_status') != 'NOT_READY_TO_SUBMIT' or
            s.get('unique_observed_models') != 42 or s.get('observed_models') != 21 or
            s.get('tests_passed') != 62 or s.get('operators') != 7 or s.get('sources', {}).get('n') != 35970 or
            s.get('augmentation', {}).get('observed_models') != 21):
        raise ValueError('unexpected actual science dimensions or status')
    augmented = s['augmentation']['models']
    if any(m['field_velocity_rank'] != 39 or m['field_velocity_parameters'] != 39
           for m in augmented if m['degree'] == 3):
        raise ValueError('J3 rank-recovery result differs from reviewed result')

    titles = [
        ('Fix the single P3 question and existing-checkout completion contract',
         ['RESEARCH_RECORD.json', 'DESIGN.md']),
        ('Reuse Hubble PR/branch history, source identities and current primary literature',
         ['REVIEW/r64_history.md', 'REVIEW/r64_history_sources.json', 'REVIEW/r64_literature.md', 'REVIEW/r64_sources.json']),
        ('Separate Hcal, distance-defined H_D and finite-window H_W with source conventions',
         ['DESIGN.md', 'THEORY.md', 'TENSOR_LIKELIHOOD.md']),
        ('Fix the source-integrated finite distance-field and calibration experiment',
         ['DESIGN.md']),
        ('Derive optical and calibration maps and implement joint signed-tensor inference',
         ['THEORY.md', 'TENSOR_LIKELIHOOD.md', 'REVIEW/WOLFRAM_CHECK.json', 'REVIEW/SYMPY_CHECK.json']),
        ('Verify affected normalization, derivatives, nulls, covariance and five-view code',
         ['RESULTS/AFFECTED_TEST_RECEIPT.json']),
        ('Execute21 original actual-CF4 full36 fits and source calibration diagnostics',
         ['RESULTS/OBSERVED_EXECUTION_01.json', 'RESULTS/OBSERVED/DIRECTIONAL_HUBBLE_RESULT.json']),
        ('Recover existing correlated source rows, execute21 augmentations and decide the paper route',
         ['R8_RESOLUTION_AMENDMENT.md', 'RESULTS/AUGMENTED_EXECUTION_02.json', 'RESULTS/AUGMENTATION_TEST_RECEIPT.json',
          'RESULTS/WHITENING_STABILITY.json', 'RESULTS/INTERPRETATION_SUMMARY.json', 'REPORT_KO.md', 'RESEARCH_PLAN_KO.md']),
        ('Close one fresh independent final review and any bounded correction episode',
         ['REVIEW/final_review.md', 'REVIEW/final_review.json', 'VALIDATION.md']),
        ('Preserve a finite P3 plan, additive canonical DAG and authorized scoped release',
         ['RESEARCH_PLAN_KO.md', 'VALIDATION.md', 'DAG_VALIDATION.json']),
    ]
    missing = sorted({f for _, ev in titles[:9] for f in ev if not (folder / f).is_file()})
    if missing:
        raise ValueError('completed-stage evidence missing: ' + ', '.join(missing))
    backlog = root / 'docs/codex_handoff/pr_backlog.yaml'
    status = root / 'docs/codex_handoff/pr_status.yaml'
    old_text, status_text = backlog.read_text(), status.read_text()
    old, status_before = yaml.safe_load(old_text), yaml.safe_load(status_text)
    if len(old['prs']) != 287 or len(status_before['completed']) != 222:
        raise ValueError('canonical counts changed from287/222')
    if any(c['id'] == PR for c in old['prs']) or PR in status_before['completed']:
        raise ValueError('R64 insertion is one-shot')
    if not any(c['id'] == PARENT for c in old['prs']) or PARENT not in status_before['completed']:
        raise ValueError('completed R63 predecessor not preserved')
    card = dict(
        id=PR, wave=0, title='Recover source-dependent directional Hubble information and quantify calibration-sensitive derivative resolution',
        owner='HTT', depends=[PARENT],
        files=[str(FOLDER), 'scripts/r64', 'tests/r64', 'htt/htt/htt/infer/r64_directional_hubble.py',
               'docs/codex_handoff/pr_backlog.yaml', 'docs/codex_handoff/pr_status.yaml',
               str(BASE / 'PUBLICATION_DAG.json'), str(BASE / 'README.md')],
        tests=[
            'OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. .venv/bin/python -m pytest -p no:cacheprovider -q tests/r64 tests/r58/test_mixed_tensor_likelihood.py tests/r58/test_five_views.py',
            '.venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml',
            '.venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check',
            '.venv/bin/python -B scripts/htt_publication_dag.py --validate'],
        dod=[
            'Complete one sequential ten-stage owner-selected P3 study using existing history, primary sources and actual owned CF4 operators/covariance.',
            'Derive Hcal/H_D/finite-H_W distinctions, eta normalization, represented calibration invariants, optical closure equation and counterexamples.',
            'Run signed tensor distance-field likelihoods with source integration, free coherent V, full shared covariance and common-region nonlinear images.',
            'Resolve the actual36-row J3 null with existing correlated method/sky summaries; retain all source/calibration alternatives and uncertainty/domain limitations.',
            'Close one fresh independent review; preserve original42/P3 acceptance and NOT_READY_TO_SUBMIT with finite observational and matched-method work.'],
        notes=str(FOLDER / 'RESEARCH_DAG.json'),
        kill='No general physical Hubble/acceleration detection, universal CF4 derivative no-go, independent multiplication of correlated summaries or invented calibration law; no automatic successor or local-agent prompt.',
        level='L0', scope='science', risk='R2', claim_tier_ceiling='C0', user_authorized=True,
        authorization='2026-11-17 owner explicitly selected redshift- and direction-dependent Hubble factor for one full ten-stage loop; inherited non-force GitHub publication authority persists.')
    needle = '  - ' + PARENT + '\n'
    if old_text.count(needle) != 2:
        raise ValueError('expected two predecessor entries in ordered lists')
    new_text = old_text.replace(needle, needle + '  - ' + PR + '\n')
    new_text = new_text.rstrip() + '\n' + yaml.safe_dump([card], sort_keys=False, allow_unicode=True, width=105)
    parsed = yaml.safe_load(new_text)
    if len(parsed['prs']) != 288 or parsed['prs'][:-1] != old['prs']:
        raise ValueError('old cards changed')
    if remove_pr({k: v for k, v in parsed.items() if k != 'prs'}) != {k: v for k, v in old.items() if k != 'prs'}:
        raise ValueError('old backlog metadata changed')
    if PR in status_text or '\ncompleted:\n' not in status_text:
        raise ValueError('unexpected status source')
    new_status = status_text.replace('\ncompleted:\n', '\ncompleted:\n- ' + PR + '\n', 1)
    new_status = new_status.rstrip() + '\n\n# ' + PR + ': complete_scoped C0. Actual CF4 source-row information recovery and calibration-sensitive distance derivatives; original42/P3 acceptance preserved. No automatic successor or local-agent prompt.\n'
    expected_status = copy.deepcopy(status_before)
    expected_status['completed'] = [PR] + expected_status['completed']
    if yaml.safe_load(new_status) != expected_status or len(expected_status['completed']) != 223:
        raise ValueError('status mutation exceeds one completion')

    publication = root / BASE / 'PUBLICATION_DAG.json'
    pub = load(publication)
    if len(pub['nodes']) != 42 or digest(pub['nodes']) != CORE_HASH:
        raise ValueError('original42 payload changed')
    papers_before = copy.deepcopy(pub['papers'])
    previous = copy.deepcopy(pub['current_scientific_route'])
    if previous['canonical_pr'] != PARENT:
        raise ValueError('unexpected predecessor route')
    p3 = next(p for p in pub['papers'] if p['id'] == 'P3')
    if 'current_scoped_directional_hubble' in p3:
        raise ValueError('P3 companion pointer already exists')
    pub.setdefault('previous_scientific_routes', []).append(previous)
    pub['current_scientific_route'] = dict(
        date='2026-11-17', source_base_sha=BASELINE, canonical_pr=PR, selected_paper='P3',
        scope='Only redshift- and direction-dependent Hubble factor; one integrated ten-stage theory/coding study',
        report=str(FOLDER / 'REPORT_KO.md'), plan=str(FOLDER / 'RESEARCH_PLAN_KO.md'),
        research_dag=str(FOLDER / 'RESEARCH_DAG.json'), status='COMPLETE_SCOPED_C0', review=review_status,
        active_result=str(FOLDER / 'RESULTS/INTERPRETATION_SUMMARY.json'),
        original_six_tracks_and_42_gates_preserved=True, automatic_successor=False,
        local_agent_prompt_created=False, submission_status='NOT_READY_TO_SUBMIT',
        authorization='Current explicit owner ten-stage branch request; inherited non-force GitHub publication authority.')
    p3['current_scoped_directional_hubble'] = dict(
        pr=PR, report=str(FOLDER / 'REPORT_KO.md'), plan=str(FOLDER / 'RESEARCH_PLAN_KO.md'),
        research_dag=str(FOLDER / 'RESEARCH_DAG.json'), original_acceptance_status_preserved=True)
    restored = copy.deepcopy(pub['papers'])
    next(p for p in restored if p['id'] == 'P3').pop('current_scoped_directional_hubble')
    if restored != papers_before or digest(pub['nodes']) != CORE_HASH:
        raise ValueError('old paper contracts or original42 states changed')
    pub['next_action'] = (
        'Consolidate R64 source-dependent information recovery into P3. Qualify the actual shared-calibration/selection law, '
        'perform one matched-estimand prior-art comparison and overlap-aware distinct-tracer prediction, and design precision '
        'for named distance-derivative targets on the already full-rank experiment. Physical Hcal claims additionally require '
        'one qualified optical or independent-H channel. Do not repeat the solved rank problem or automatically launch a successor.')
    tasks = [dict(id=f'R64-{j:02d}', theory_stage=f'R{j}', coding_stage=f'C{j}', title=title,
                  depends_on=[] if j == 1 else [f'R64-{j-1:02d}'], status='complete_scoped', evidence=ev)
             for j, (title, ev) in enumerate(titles, 1)]
    future = [
        dict(id='P3-R64-SOURCE-LAW', depends_on=['R64-10'], status='unresolved_input',
             completed='Existing full36/method32/sky36 response and cross covariance reused; free24 method-angular nuisance executed.',
             needed='Use actual H02 method-resolved group/object genealogy, anchor and survey calibration covariance, selection/mask/quality response to construct J_gamma Sigma_gamma J_gamma^T and transported mean/covariance.',
             stop='Quantify named target shifts under obtained source inputs and delimit missing inputs; no demand to solve every possible systematic.'),
        dict(id='P3-R64-PRECISION', depends_on=['R64-10'], status='pending_conditional',
             completed='All selected68/72-row J3 experiments already have field+V rank39; H_D and q_D images are implemented.',
             needed='Use derivative target variance and weak directions to evaluate one available source weighting, higher-precision distance support or independent coherent-velocity anchor.',
             stop='Deliver one numerical precision/domain-margin design table or its concrete feasibility gap; do not repeat nullity0 checks.'),
        dict(id='P3-R64-MATCHED-COMPARISON', depends_on=['R64-10'], status='pending_conditional',
             needed='Match one feasible source/estimand subset across log-Hubble harmonic/STF and distance-derivative methods, with two source signal families and actual O/C/nuisance response.',
             stop='Report target bias, variance and domain resolution; mark unavailable source inputs instead of claiming exact reproduction or a significance ranking.'),
        dict(id='P3-R64-TRACER-PREDICTION', depends_on=['P3-R64-SOURCE-LAW'], status='pending_conditional',
             needed='Choose one distinct tracer prediction with explicit used-source/group overlap, common anchors and PV cross covariance; retain conditional innovation and parameter-estimation variance.',
             stop='Compute one identified prediction and decide agreement/residual origin; existing method rows and H02 internal holdouts are not new independent evidence.'),
        dict(id='P3-R64-PHYSICAL-MAP', depends_on=['P3-R64-SOURCE-LAW'], status='optional_for_physical_claim',
             needed='Choose one actual-input optical closure or independent H observable with compatible congruence/endpoint/redshift/flux/clock/ruler conditions and joint law.',
             stop='Produce one distance-expansion consistency result, or close P3 at the distance-defined claim level with Hcal unresolved.'),
        dict(id='P3-R64-PAPER', depends_on=['P3-R64-SOURCE-LAW', 'P3-R64-MATCHED-COMPARISON', 'P3-R64-TRACER-PREDICTION', 'P3-R64-PRECISION'],
             optional_for_stronger_claim=['P3-R64-PHYSICAL-MAP'], status='pending_conditional',
             needed='Consolidate one source-dependent information/derivative-resolution manuscript at the achieved claim level; integrate into existing P3 if standalone novelty is thin.',
             stop='Preserve P3 NOT_READY if its actual source/heldout/competing-estimand gate remains unmet; no automatic new branch or loop.'),
    ]
    scoped = dict(schema='htt.r64.research_dag/1', baseline_commit=BASELINE, canonical_pr=PR, parent_pr=PARENT,
                  selected_paper='P3', claim_tier='C0', scope='Single ten-stage directional redshift-dependent Hubble study',
                  status='COMPLETE_SCOPED_C0', tasks=tasks, future_science=future,
                  original_42_node_payload_sha256=CORE_HASH, original_42_node_states_changed=False,
                  key_results=dict(sources=s['sources'], initial_models=21, augmented_models=21, unique_observed_models=42,
                                   tests_passed=62, initial_degree_summary=s['degree_summary'],
                                   augmented_models_summary=augmented, calibration_comparison=s['augmentation']['method_calibration_comparison'],
                                   new_independent_sources=0, new_pair_sum=False),
                  interpretation_summary_sha256=hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                  conditions='Fixed inherited Gaussian law and finite mean; source dependence is not a causal calibration detection. Full coefficient rank does not imply a precise physical Hcal or certified nonlinear domain.',
                  automatic_successor=False, local_agent_prompt_created=False, submission_status='NOT_READY_TO_SUBMIT')

    readme = root / BASE / 'README.md'
    text = readme.read_text()
    header = '# HTT 관측논문 6트랙 출판 중심 DAG\n\n'
    old_header = '## Current local-boost/global-history discrimination study — R63, 2026-11-17'
    if text.count(header) != 1 or text.count(old_header) != 1:
        raise ValueError('README differs from observed baseline')
    text = text.replace(old_header, '## Previous local-boost/global-history discrimination study — R63, 2026-11-17', 1)
    text = text.replace('현재 선택된 P4 companion 경로다', '이전 P4 companion 경로다', 1)
    entry = (
        '## Current directional Hubble study — R64, 2026-11-17\n\n'
        '[R64 실제 거리장·정보 회복 결과](R64_DIRECTIONAL_HUBBLE_20261117/REPORT_KO.md), '
        '[P3 논문 계획](R64_DIRECTIONAL_HUBBLE_20261117/RESEARCH_PLAN_KO.md), '
        '[연구 DAG](R64_DIRECTIONAL_HUBBLE_20261117/RESEARCH_DAG.json)이 현재 선택된 P3 companion 경로다. '
        'CF4 35,970개 group의 full36과 기존 correlated method/sky rows를 사용해 총42개 fit을 실행했다. '
        '68/72행으로 확장하면 J3 거리장+V 계수 rank39/39가 회복되지만, method-dependent adequacy와 넓은 H_D/q_D '
        '구간은 남는다. mono_method68 J2의 common-field p=.007642는24개 angular nuisance를 profile하면.584765가 '
        '되며 다른 operator의 결과도 보존했다. 고정 working covariance의 조건부 관측 결과다. '
        '일반 physical Hubble/가속도 검출이나 CF4 전체의 불가능성을 주장하지 않는다. '
        '원래42개 gate와 P3 acceptance를 보존하며 제출 상태는 NOT_READY_TO_SUBMIT이다. 자동 다음 루프·local agent prompt는 없다.\n\n')
    text = text.replace(header, header + entry, 1)
    receipt = dict(canonical_card_added=PR, old_backlog_entries=287, new_backlog_entries=288,
                   old_completed_count=222, new_completed_count=223,
                   previous_cards_semantically_unchanged=True, original_node_payload_sha256=CORE_HASH,
                   original_nodes_unchanged=True, original_paper_contracts_preserved=True,
                   old_P3_keys_preserved=True, selected_scope='P3 companion only', review=review_status,
                   interpretation_sha256=hashlib.sha256(summary_path.read_bytes()).hexdigest(),
                   automatic_successor=False, local_agent_prompt_created=False)
    payloads = {backlog: new_text, status: new_status, publication: encoded(pub), readme: text,
                folder / 'RESEARCH_DAG.json': encoded(scoped), folder / 'DAG_UPDATE_RECEIPT.json': encoded(receipt)}
    if any(p.exists() for p in (folder / 'RESEARCH_DAG.json', folder / 'DAG_UPDATE_RECEIPT.json')):
        raise ValueError('scoped DAG already exists; refuse repeated insertion')
    for path, body in payloads.items():
        path.write_text(body.rstrip() + '\n')
    print(encoded(receipt), end='')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--review-status', required=True)
    args = parser.parse_args()
    run(args.root, args.review_status)
