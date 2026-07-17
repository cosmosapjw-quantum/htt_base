# Post-PR-118 장기 Rescue 연구 PR 로드맵 + Advocate divergence 통합 (단일 연구계획)

> **2026-07-14 병합:** 이 문서는 원 remediation 로드맵(PR-119--166)에 advocate divergence
> 탐색(`docs/research_program/advocate_rescue_divergence_20260714/`)의 net-new 후보를 추가한
> **단일 연구계획**이다. 원 로드맵의 양식·번호·판정 원칙을 보존하고, advocate 후보는 Wave 22--27
> (PR-167--183)로 추가한다. 실행 방식은 **spec-driven development**(각 PR은 구현 전 SPEC/acceptance/
> decisive-falsifier를 먼저 확정)이며 **개별 단계는 subagent-driven**(typed subagent로 위임)이다 —
> §4.5. advocate 후보의 family-ID/geometry 계열은 전부 `hypothesis_only`로만 남고 pre-native
> 승격 금지 원칙은 그대로다.

- **문서 상태:** `PROPOSED_ONLY_NOT_IN_ACTIVE_DAG`
- **기준 commit:** `294d74ce07de030da2f18720d3d45c8a2fef6e17`
- **작성일:** 2026-07-14
- **Owner:** `COMMON` (계획 조정); 각 실행 PR의 실제 owner는 개별 카드에 명시
- **Implementation scope:** `research_program_planning`
- **Claim tier:** `diagnostic_only`
- **Transfer source:** `mixed_none_and_external_transfer_conditional`
- **Public use:** `false`
- **Config hash:** `not_applicable_planning_document`
- **Input hashes:** section 2의 권위 자료 SHA256
- **Sky support / mask status:** `not_applicable_planning_document`
- **Covariance / null status:** `not_applicable_planning_document`; 각 실행 PR에서 별도 gate
- **Caveats:** 비용·기간은 planning envelope이며 과학 readiness 또는 rescue 판정이 아님
- **Generating command:** repository-local agent authoring via `apply_patch`; 검증 명령은 section 17과 closeout에 기록
- **Git/worktree:** 기준 commit 위의 uncommitted planning artifact; user-owned `legacy/`와 원본 harness ZIP은 입력·stage 대상 아님
- **현재 active DAG:** 65/65 완료, 다음 active PR 없음
- **중요:** 이 문서는 PR-119--PR-183의 후보 DAG다(원 remediation 119--166 + advocate divergence 167--183). `docs/codex_handoff/pr_backlog.yaml`과 mirror에 별도 intake하지 않는 한 어떤 카드도 active PR이 아니다.

## 1. 목적과 판정 원칙

이 로드맵의 목적은 기존 이론·통계 프레임워크를 버리고 새 분석을 덧붙이는 것이 아니라, 현재 도구의 잘못된 의미론·수치 oracle·식별 가정·검증 공백을 순서대로 고친 뒤 같은 프레임워크를 더 넓고 엄격하게 사용하는 것이다. 방법론과 이론 연구를 데이터별 재분석보다 앞에 둔다. 다만 장기 연구 중 현재 P0 결과가 다시 인용되는 것을 막기 위한 quarantine은 가장 먼저 실행한다.

이 문서는 다음 네 가지 결과를 구분한다.

1. **Literal rescue:** 원 claim의 quantifier, estimand, population, frame/order/domain, data release/support, statistic, transfer source, nuisance/prior/null/multiplicity policy와 claim tier가 모두 유지되고 결함만 교정된 경우다.
2. **Corrected supersession:** 기존 claim이 거짓이거나 정의가 바뀌어 원 finding을 `CORRECTED_SUPERSEDED` 또는 `FALSIFIED`로 닫고 새 claim ID를 발급하는 경우다.
3. **Rebuild:** 원 명제가 아직 반증되지 않았지만 provenance, covariance, matched null, coverage, proof 또는 독립 oracle이 없어 새 계산이 필요한 경우다.
4. **Blocked/abandoned:** 결정적 입력이나 native solver가 없거나, 합리적인 nuisance/domain에서 식별되지 않아 더 강한 명제를 중단하는 경우다.

PR 작성자는 자기 finding을 `rescued`로 표시할 수 없다. 작성자가 아닌 adjudicator가 production remediation receipt, 모든 downstream consumer와 negative scan을 확인한 뒤에만 authoritative ledger를 바꾼다. DAG의 process completion과 scientific disposition은 별도 축이다. 입력 부재나 decisive falsifier 실패로 끝난 카드도 `BLOCKED_WITH_RECEIPT` 또는 `ABANDONED_WITH_RECEIPT`라는 terminal execution resolution을 남기면 downstream adjudication dependency를 닫을 수 있지만, 과학 상태는 올라가지 않는다. 문구 완화, audit-only 계산, smoke test, DAG 완료, schema 추가만으로는 rescue가 아니다.

## 2. 권위 자료와 우선순위

이 문서는 다음 자료를 기준으로 한다.

| 자료 | SHA256 | 역할 |
|---|---|---|
| `docs/audits/jcap_prd_adversarial_audit_20260714/criticism_response_matrix.json` | `f0c8c5316d8384bf223addd21c3f319039a26134bdc8507f4ae432206e7e9b0d` | 102개 criticism과 현재 disposition의 권위 입력 |
| `docs/audits/jcap_prd_adversarial_audit_20260714/advocate_candidate_ledger.json` | `0ff8d5d24642ba7fce1652aad406392287545d9a70071715a26d4d71e1a8742f` | 장기 theory/statistics/code/data 후보와 falsifier |
| `docs/audits/jcap_prd_adversarial_audit_20260714/next_dag_candidates.json` | `2d8edfd7198050e1b209dccfc312f3848da01cfae50e5718332442c9210ea1d0` | `AUD-R01A`--`AUD-R05C` umbrella 카드 |
| `docs/audits/jcap_prd_adversarial_audit_20260714/final_referee_report.md` | `2c6e606c4a56e6c40ce2f466f57c087d4c79466599f5a67524633a622dd45ced` | as-shipped 및 post-surgery 심사 ceiling |
| `docs/harness/BLOCKERS.md` | `6009b2e2dde44333d88a3bc53c0dc26e755813008f45964232a37590a5af6a6d` | 현재 P0/data/theory/native blocker |
| active `pr_backlog.yaml` | `960bb4ebb6a4a262f2f5e3c5b622881f1736bbb93fd0af707876acefb9a18309` | 65/65 완료된 현재 DAG SSoT |
| `docs/research_program/advocate_rescue_divergence_20260714/07_ranked_candidate_ledger.json` | (dev-tier; commit `a56451c`) | Wave 22--27(PR-167--183)의 net-new advocate 후보 + decisive falsifier |
| `docs/research_program/advocate_rescue_divergence_20260714/08_steelman_response_matrix.json` | (dev-tier; commit `a56451c`) | 102 criticism 전수 steelman(76 concede-and-rebuild / 22 reframe / 3 terminal / 1 refute) |

우선순위는 hard gate를 먼저 적용한 뒤 평가한다.

- Hard gate: owner와 claim ceiling, decisive falsifier, 입력 provenance, upstream dependency, native boundary가 모두 명시되어야 한다.
- Scoring: open-risk retirement 25%, cross-lane leverage 20%, identifiability/falsifiability 20%, input readiness 15%, independent reproducibility 10%, novelty/publication value 10%.
- 비용은 점수에 숨기지 않고 `low/medium/high/blocked`로 별도 기록한다.
- `CO-04`, `CO-01`, `CO-05`처럼 여러 finding을 동시에 검증하는 기반을 데이터별 단발 분석보다 우선한다.

비용 표기는 비교용이다. `low`는 대체로 2 person-weeks 이내이며 새 대형 data/long run이 없는 작업, `medium`은 약 2--6 person-weeks 또는 제한된 simulation, `high`는 6 person-weeks 이상·다중 owner·대형 mock/독립 재현이 필요한 작업이다. `blocked`는 외부 data/native delivery/독립 panel 없이는 시작할 수 없음을 뜻한다. 실제 intake에서 자원과 hardware preflight 후 다시 산정한다.

개별 카드의 `C0`--`C6` 표기는 기존 scientific claim ladder를 가리키는 계획용 shorthand다. production artifact는 이것만 쓰지 않고 canonical `ClaimTier` enum(`exploratory`, `conditional`, `diagnostic_only`, `validated`, `blocked`)과 implementation scope를 함께 기록해야 한다. 이 둘은 순서가 같은 단일 enum이 아니므로 다음 fail-closed mapping을 PR-119의 초기 SSoT로 사용하고, 더 강하게 바꾸려면 별도 claim-firewall review가 필요하다.

| Scientific level | 의미 | 허용 canonical `ClaimTier` |
|---|---|---|
| C0 | invalid/missing/withheld | `blocked` |
| C1 | framework, definition, disclosure, mechanics | `exploratory` 또는 검증 범위가 닫힌 `diagnostic_only`; `validated` 금지 |
| C2 | 명시 domain/model/transfer 조건부 theorem 또는 mechanics | `conditional` |
| C3 | observer-side diagnostic | `diagnostic_only`; transfer dependence는 별도 `transfer_source`로 필수 표기 |
| C4 | local/global discrimination candidate | `conditional` at most |
| C5 | morphology compatibility | external-transfer이면 `conditional`; authenticated native와 모든 matched gate 후에만 `validated` 후보 |
| C6 | externally adjudicated native family/geometry claim | PR-165 전에는 `blocked`; PR-165의 모든 conjunctive gate 후에만 `validated` 후보 |

## 3. 현재 프레임워크의 구조적 한계와 극복 방향

| 한계 | 왜 치명적인가 | 극복 원칙 | 선행 PR |
|---|---|---|---|
| `x_C`, `Q`, `Pi`, `F`, `G_F` 같은 scalar compression의 비단사성 | 상쇄 방향과 blind sector가 남아 family/geometry 또는 FLRW converse를 식별하지 못한다 | kernel witness, 양의 성분에만 PSD cone, signed curvature에는 별도 실수축/branch, set-valued identified region과 mandatory abstention을 기본 출력으로 둔다 | PR-126, 127, 136, 137, 141 |
| frame·congruence·order·normalization이 prose에 묻힘 | 같은 기호가 local observer boost, matter tilt, curvature 또는 geometry를 섞는다 | typed frame/order/domain/premise contract와 theorem-to-consumer dependency를 강제한다 | PR-124, 125, 133 |
| near-FLRW/local expansion을 global exact relation으로 사용 | class boundary, transient, zero denominator에서 계수와 부호가 바뀔 수 있다 | 선형/고차 계수, singular map, interval remainder와 fail-closed domain API를 분리한다 | PR-131, 132 |
| convergence, sufficiency, one-way implication, converse가 혼동됨 | 작은 tail이나 green test가 정보 충분성 또는 물리 정리로 과장된다 | factorization이 없으면 sufficiency를 금지하고 반례·premise DAG를 proof artifact와 같이 유지한다 | PR-126, 128--130 |
| 두 symbolic/numeric engine이 같은 식을 복사할 위험 | 외형상 dual-engine이지만 같은 개념 오류를 공유한다 | derivation lineage, 알고리즘 독립성, mutation/counterexample kill rate를 receipt에 넣는다 | PR-123, 124 |
| native low-ell solver/atlas 부재 | external transfer와 scalar proxy로 morphology/family를 검증할 수 없다 | adapter와 challenge fixture만 준비하고 실제 delivery 전 post-native 카드는 dormant로 둔다 | PR-159--166 |
| deterministic template mean과 stochastic covariance 혼동 | likelihood, look-elsewhere, null 분포가 서로 다른 두 generative model을 한 점수로 합친다 | 별도 model branch와 comparison report를 만들며 자동 병합을 금지한다 | PR-134, 140, 141 |
| observed/null 비대칭과 finite-null 외삽 | observation에만 가능한 rank와 0 p-value, 과도한 Gaussian sigma가 생긴다 | observation-inclusive pooled rank, tie 처리, exact Monte Carlo interval, max-statistic calibration을 공통 API로 만든다 | PR-135, 143 |
| plug-in residual을 PPC로, channel ablation을 LOOCV로 부름 | posterior predictive와 out-of-sample predictive adequacy가 실제로 수행되지 않는다 | lineage-bound posterior draws, replicated data, SBC, train-only refit, held-out log predictive density를 요구한다 | PR-138, 139 |
| prior/evidence provenance 부재 | 임의 scalar 또는 비정규 prior가 Bayes evidence처럼 유통될 수 있다 | normalized prior registry와 두 독립 evidence engine, sensitivity/abstention을 결합한다 | PR-140, 141 |
| nuisance·selection·window의 부분식별 | point estimate와 sigma가 nuisance choice에 의해 결정되지만 이를 uncertainty로 숨긴다 | nuisance family를 사전 등록하고 identified set, grid-conditional simultaneous coverage를 산출하며 class-wide uniformity는 continuity/mesh theorem이 있을 때만 허용한다 | PR-134, 136, 137 |
| covariance가 lane별·same-data·cross-survey 수준에서 불완전 | correction과 comparator 또는 여러 probe를 독립 evidence처럼 곱하게 된다 | covariance component ontology, PSD/conditioning test, joint simulation과 cross-survey latent systematic을 명시한다 | PR-134, 143, 148, 155 |
| mock의 상관·effective N·per-mock refit 누락 | tail bound와 estimator uncertainty가 지나치게 작아진다 | independent unit 정의, cluster/effective-N audit, per-mock nuisance refit과 coverage를 요구한다 | PR-135, 143, 146, 151 |
| 데이터 lineage가 synthetic/authenticated observed를 구분하지 못함 | forecast fixture가 실제 survey evidence로 바뀐다 | row-level manifest, deterministic transform receipt와 `synthetic/local/authenticated` mode를 타입으로 분리한다 | PR-144, 149, 152--154 |
| MIO diagnostic의 확률 해석 유혹 | MIO가 HTT 소유의 모형의존 inference 역할을 침범한다 | `MeasureSpec`과 null calibration은 허용하되 MIO output은 `diagnostic_only`, 모형의존 inference는 HTT 소유로 유지한다 | PR-142 |
| 여러 survey의 방향 정합성을 독립 confirmation으로 간주 | 공통 sky, foreground, selection, calibration이 evidence를 상관시킨다 | negative control, joint covariance, response-rank와 held-out injections을 통과하지 못하면 `abstain`한다 | PR-155, 156 |

## 4. 전 PR 공통 실행 계약

모든 카드에 아래 규칙이 자동 적용된다. 개별 카드가 더 엄격하면 개별 규칙이 우선한다.

### 4.1 반드시 할 것

- PR 시작 시 active DAG와 dependency를 검증하고 PR card, touched file, prior delta, relevant test를 읽는다.
- claim/finding identity fingerprint를 변경 전 고정한다. 필드는 claim text와 quantifier, estimand/population, frame/order/domain, data release/support/mask/selection, statistic/pipeline, transfer, nuisance/prior/null/multiplicity, claim tier다.
- 성공 기준과 decisive falsifier를 observed result를 보기 전에 기록한다.
- 이론 PR은 assumptions, signature `(-,+,+,+)`, units, tetrad/frame, harmonic convention, limits와 domain을 명시한다.
- 통계 PR은 estimand, dependency graph, null generator, covariance, prior, multiplicity와 held-out unit을 명시한다.
- artifact마다 owner, implementation scope, claim tier, artifact mode, allowed/forbidden use, transfer source, config/input hash, sky/mask, covariance/null, caveats, command와 git/worktree를 기록한다.
- author와 non-author adjudicator를 분리하고, 독립 oracle의 소스·알고리즘 lineage를 기록한다.
- canonical `Owner`는 `COMMON|HTT|MIO|BASS|OBSSTAT|TSC_LEGACY` 중 하나만 사용한다. 공동 작업자는 `contributors`, 독립 심사자는 `adjudicator`, 코드 위치는 `implementation_scope`로 분리한다. 새 작업에는 `TSC_LEGACY`를 owner로 쓰지 않는다.
- 실제 실행 command, seed, 환경 hash, start/end, exit, wall time, peak resource, stdout/stderr hash를 receipt에 보존한다.
- 실패·blocked·abstain 결과도 성공적인 연구 산출물로 보존한다.

### 4.2 하지 말아야 할 것

- family/geometry identification, native-transfer validation 또는 global-tilt measurement를 pre-native 결과에서 주장하지 않는다.
- MIO output은 `diagnostic_only`로 유지하고 HTT 소유의 모형의존 inference 역할을 부여하지 않는다.
- TSC/Teff를 active science owner 또는 future solver 대체물로 되살리지 않는다.
- audit-only number, toy/synthetic result 또는 proxy input을 production/observed result로 복사하지 않는다.
- finite-null 해상도보다 작은 p-value나 sigma를 외삽하지 않는다.
- threshold, prior, mask, depth, discrepancy, nuisance set을 결과를 본 뒤 조정하여 같은 analysis ID로 유지하지 않는다.
- numerical convergence를 physical correctness 또는 observational validation이라고 부르지 않는다.
- schema·manifest·disclaimer만 늘리고 theorem, counterexample, calibrated simulation 또는 authenticated result가 없는 scientific PR을 연속으로 만들지 않는다.
- untracked `legacy/`와 원본 harness ZIP을 명시적 allowlist 없이 stage하지 않는다.

### 4.3 공통 kill switch

- 입력이 없거나 decisive job이 6시간을 넘으면 작은 proxy 성공으로 대체하지 않고 `BLOCKED`로 끝낸다.
- theory engine이 sign, normalization, coefficient 또는 domain에서 불일치하면 모든 consumer를 차단한다.
- response rank가 부족하면 `non_identified`; PPC/coverage/size가 실패하면 `inadequate`; predictive superiority가 없으면 `abstain`을 반환한다.
- remainder bound가 깨지면 domain을 축소하거나 정리를 폐기한다. local formula를 global exact relation으로 승격하지 않는다.
- observed와 null pipeline, data와 mock selection, correction과 comparator covariance가 다르면 science result 생성을 중단한다.
- native solver 입력의 authenticity/version/convention을 검증할 수 없으면 PR-159 이후 전체를 dormant/blocked로 유지한다.

### 4.4 production remediation receipt 최소 schema

```yaml
schema_version: semver
receipt_id: immutable_uuid_or_content_id
claim_or_finding_id: immutable
source_hash: sha256
identity_before: sha256
identity_after: sha256
identity_diff: {}
process_result: passed|failed|blocked|abandoned
execution_resolution: COMPLETED_SUCCESS|COMPLETED_FAILED_WITH_RECEIPT|BLOCKED_WITH_RECEIPT|ABANDONED_WITH_RECEIPT
scientific_status: OPEN|IN_REMEDIATION|EVIDENCE_READY|ADJUDICATION_PENDING|RESCUED|CORRECTED_SUPERSEDED|FALSIFIED|BLOCKED|ABANDONED
author_principal_id: string
adjudicator_principal_id: string
author_adjudicator_inequality_check: passed|failed
authority_attestations:
  - principal_id: string
    role: author|adjudicator|data_owner|oracle_owner
    attestation_hash: sha256
parent_receipt_ids: []
independence_edges: []
pre_registered_success: []
decisive_falsifier: string
owner: COMMON|OBSSTAT|HTT|MIO|BASS
contributors: []
implementation_scope: common|obsstat|htt|mio|bass_py|canonical_BASS|tsc_legacy
claim_tier_ceiling: exploratory|conditional|diagnostic_only|validated|blocked
scientific_claim_level: C0|C1|C2|C3|C4|C5|C6
transfer_source: none|empirical_proxy|AniCLASS_external|BASS_native_provisional|BASS_native_validated
sky_mask_covariance_null_status: {}
commit_or_worktree: string
environment_hash: sha256
input_hashes: []
config_hash: sha256
commands: []
seeds: []
resources: {}
independent_oracle_lineage: []
mutation_and_counterexample_results: []
downstream_consumers_before: []
downstream_consumers_after: []
stale_consumer_scan: passed|failed
recommended_disposition: RESCUED|CORRECTED_SUPERSEDED|FALSIFIED|BLOCKED|ABANDONED
```

`author_adjudicator_inequality_check`는 문자열 비교만으로 끝내지 않는다. PR-119가 repository-authority registry와 authorized principal/role을 검증하고, PR-122가 attestation content, parent graph와 independence edge를 재계산한다. 서명/attestation을 검증할 권위가 없으면 `scientific_status`는 `ADJUDICATION_PENDING`보다 올라갈 수 없다.

### 4.5 실행 방식: spec-driven development + 단계별 subagent-driven development

모든 PR(원 119--166과 advocate 167--183 모두)은 아래 실행 규율을 따른다. 이는 §4.1--4.4의
계약 위에 얹히는 *실행 방법*이며, 개별 카드가 더 엄격하면 개별 규칙이 우선한다.

**Spec-driven (구현보다 spec이 먼저).** 각 PR은 코드/증명/분석을 시작하기 전에 하나의 리뷰 가능한
`SPEC` 아티팩트를 먼저 확정한다. SPEC의 최소 필드는: (a) claim/finding identity fingerprint(§4.1),
(b) estimand/observable와 target population/domain, (c) frame/order/units/convention(이론) 또는
null generator/covariance/prior/multiplicity(통계), (d) 공개 인터페이스와 입출력 schema/type,
(e) pre-registered success + **decisive falsifier**(observed result를 보기 전에 고정), (f)
`claim_tier_ceiling`와 `scientific_claim_level`(C0--C6), (g) 소비하는/생성하는 upstream·downstream
edge다. SPEC은 non-author adjudicator가 승인해야 구현 단계가 열린다. 구현이 SPEC과 벌어지면
identity diff를 생성하고 `RESCUED`를 거부한다(SPEC 변경 = 새 version/claim ID). SPEC 없이 시작한
PR, 또는 결과를 본 뒤 SPEC을 고친 PR은 kill switch 대상이다.

**단계별 lifecycle checklist (AMENDMENT_01, 2026-07-17).** 각 PR은 단일 monolithic pass가 아니라
아래 typed 단계로 분해한다. 아래 7단계는 *lifecycle checklist*이며, "7단계 = 7개 별도 subagent"
의무가 아니다. 실제 agent 수는 위험도별 예산을 따른다 — R0 mechanical: 0(optional) / R1 harness:
최대 2 targeted / R2 scientific non-CAS: 최대 4(서로 다른 claim/failure class) / R3 CAS mandatory:
4개 axis slot 예약(optional review와 별도, 비용 압력으로 축소·병합 금지). custom profile 사용은
launcher receipt(`.agent-harness/scripts/launch_receipt.py`)로 attestation하며, attestation 없는
agent는 `generic_prompted`로 강등되어 독립 reviewer로 중복 계상되지 않는다. shared context는
정확히 한 번만 전달한다(hook 주입 또는 file fallback; `.agent-harness/README.md` once-delivery
규칙). author subagent와 adjudicator subagent는 반드시 다른 principal이다(§4.1의
author≠adjudicator를 subagent 수준까지 확장). 상세는
`docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714_AMENDMENT_01_20260717.md`를 따른다.

| 단계 | 위임 subagent(장착된 harness/skill) | 산출 |
|---|---|---|
| 1. spec | `research-contract` / `htt-revision-planner` | SPEC 아티팩트 + acceptance/falsifier |
| 2. localize | `code-cartographer` / `htt-*-investigator` | 실행·데이터·단위 흐름 지도 |
| 3. implement | `research-code-task`(physmath-coding-gpt56) | 최소 coherent patch + tests |
| 4. scientific validate | `scientific-validation` / `physics-math-validation` | 단위/부호/대칭/보존/극한/domain 검사 |
| 5. numerical validate | `numerical-validation` | 수렴/안정/seed 재현/성능 |
| 6. independent review | `independent-diff-review`(author와 다른 principal) | correctness/regression/silent-error/hidden-scope |
| 7. closeout | `reproducibility-closeout` / `htt-ssot-handoff-maintainer` | receipt + promote/hold/rework/revert |

subagent 산출은 hypothesis-discovery/review 증거이지 external replication이 아니다(§18.5). 각
단계 subagent의 소스·알고리즘 lineage와 dissent/minority report를 receipt에 보존한다. mounted
harness는 `harness/physmath-{research,coding}-gpt56/`(SCIENTIFIC_CONTRACT/VALIDATION_MATRIX가
BASS/HTT SSoT로 인스턴스화됨)와 그 13개 skill이며, `.claude/skills/`의 23개 htt-* skill을 병용한다.

## 5. 후보 DAG 개요

| Wave | PR | 핵심 목적 | checkpoint |
|---:|---|---|---|
| 13 | PR-119--123 | DAG intake, P0 quarantine, hermetic replay, evidence graph, independent oracle | 총 70 완료 후 |
| 14 | PR-124--128 | theorem oracle, convention/premise, FLRW/EGS, non-identification, NT2 coefficient | 총 75 완료 후 |
| 15 | PR-129--133 | estimator floor, sufficiency, OMK expansion/remainder, local/global type system | 총 80 완료 후 |
| 16 | PR-134--138 | estimand registry, finite null, partial ID/coverage, posterior lineage/PPC | 총 85 완료 후 |
| 17 | PR-139--143 | true holdout, evidence, abstaining mixture, MIO calibration, integrated synthetic audit | 총 90 완료 후 |
| 18 | PR-144--148 | CF4 provenance, P0 mechanics, E2E mocks, identified sets, depth covariance | 총 95 완료 후 |
| 19 | PR-149--153 | Planck/K1, DESI, ACT, JWST provenance | 총 100 완료 후 |
| 20 | PR-154--158 | JWST forecast, cross-survey tests, integrated injections, adjudication, manuscript | 총 105 완료 후 |
| 21+ | PR-159--166 | native delivery, atlas conformance, morphology equivalence, external gate | 총 110에서 checkpoint 후 잔여 3개 별도 closeout |
| 22 | PR-167 | advocate divergence intake + spec/subagent 실행계약 + gate-off quarantine | — |
| 23 | PR-168--171 | advocate 이론: MES four-accel honesty + bounds.py fix, M_max leakage ceiling, Buchert home, khronon no-go | — |
| 24 | PR-172--175 | advocate oracle + gates-off geometry substrate: metamorphic battery, MC error-budget, SW ray tracer, tetrad oracle | — |
| 25 | PR-176--179 | advocate data falsifiers: Tsagas div(v)→q-dipole, ACT in-band κ, DESI dipole z-tomography, directional cosmography | — |
| 26 | PR-180--181 | advocate 통계: boost-BipoSH residual vector, systematics-as-hypotheses model competition | — |
| 27 | PR-182--183 | advocate gates-off ambitious registry(hypothesis_only): parity/B-mode family bit + handedness veto, T-E coherence ratio | — |

기존 umbrella와의 대응은 다음과 같다. `AUD-R01A/B`는 PR-144--148, `AUD-R02A/B`는 PR-122--123과 PR-135/143/149/150, `AUD-R03`은 PR-124--133, `AUD-R04`는 PR-151--154, `AUD-R05A/B/C`는 PR-159--166으로 세분한다. 기존 `PR-R000`--`PR-R062` supplemental 제안은 active DAG가 아니며, 이 문서가 채택되면 formal intake에서 `superseded_by` crosswalk를 생성한다. 조용히 병렬 실행하지 않는다.

## 6. Wave 13 — 권위, quarantine, 재현성 기반

### PR-119 — Post-PR-118 DAG intake와 claim 상태기계

- **Owner / dependencies / cost:** `COMMON`; PR-118; low.
- **Targets:** 현재 `rescued=0` 권위 상태, `GAP-13`, `GAP-14`, 역사적 “three rescued” 문구와 SSoT 불일치.
- **실제로 할 것:** PR-119--166을 양쪽 backlog/status mirror에 추가하기 전 이 문서와 umbrella crosswalk를 검토한다. orchestration state, terminal execution resolution과 `OPEN → IN_REMEDIATION → EVIDENCE_READY → ADJUDICATION_PENDING → RESCUED | CORRECTED_SUPERSEDED | FALSIFIED | BLOCKED | ABANDONED` scientific state를 서로 다른 필드로 고정한다. `BLOCKED_WITH_RECEIPT`/`ABANDONED_WITH_RECEIPT`는 dependency를 닫되 scientific state를 올리지 않는 resolution으로 정의한다. active finding root, historical referee response, generated summary의 authority와 immutability, authorized-principal registry를 명시한다. 모든 카드에 canonical owner, contributors/adjudicator, implementation scope, dependency, DoD, kill switch, cost와 두 claim ceiling을 넣는다.
- **하지 말 것:** 역사적 agent/referee 원문을 현재 결론에 맞게 재작성하지 않는다. PR을 backlog에 넣었다는 이유로 finding을 `IN_REMEDIATION`보다 높이지 않는다.
- **주의·anti-drift:** 현재 65/65는 science readiness가 아니다. `next_dag_candidates.json`과 옛 `PR-R*` 제안을 동시에 active로 두지 않는다. ID alias와 `superseded_by`를 생성한다.
- **검증·산출물:** DAG validator, progress report, mirror byte/semantic parity, process/science 직교 상태 전이와 author-adjudicator inequality property tests, `docs/PR_DELTAS/pr-119.md`, proposal-to-active crosswalk와 reconciliation report.
- **Exit / kill:** 48개 ID, dependency, checkpoint가 양쪽 mirror에서 일치하고 기존 65개 완료 상태가 보존되어야 한다. cycle, duplicate ID, hidden completed 상태가 하나라도 있으면 이후 PR 금지.
- **최대 claim:** orchestration/ledger correctness C1; 과학 rescue 없음.

### PR-120 — 두 CF4 P0와 downstream consumer의 즉시 quarantine

- **Owner / dependencies / cost:** `COMMON`; contributor `OBSSTAT`; PR-119; low--medium.
- **Targets:** `C1-K5-MV-F1`, `C3-K5-VCORR-ML-F1`, `N-DATA-CF4-DOWNSTREAM` 및 이 값을 소비하는 result card, figure, manuscript, package.
- **실제로 할 것:** 두 P0 수치와 파생 `4.9σ`, global-tilt, shape-correction 문구의 producer/consumer graph를 만든다. active consumer는 blocked/quarantined source record만 소비하게 하고 legacy reproduction은 별도 mode로 보존한다. publication freeze와 package builder가 stale value를 거부하는 mutation test를 추가한다.
- **하지 말 것:** 이 PR에서 405 km/s를 94 km/s 등 audit-only 대체값으로 교체하거나 새로운 cosmological result를 계산하지 않는다.
- **주의·anti-drift:** quarantine은 remediation이 아니다. negative scan이 green이어도 P0는 open이다. archive와 역사적 audit 원문은 삭제하지 않는다.
- **검증·산출물:** hash-bound consumer inventory, stale-number mutation corpus, generated block record, claim-language scan, result-pack/manuscript negative tests.
- **Exit / kill:** active/public consumer의 stale P0 경로가 0이어야 한다. 숨은 hard-coded value 또는 generated copy가 남으면 모든 data PR을 block한다.
- **최대 claim:** unsafe result propagation 차단 C1.

### PR-121 — Hermetic install, owner namespace와 detached replay

- **Owner / dependencies / cost:** `COMMON`; PR-119; medium.
- **Targets:** environment-sensitive import, duplicate `htt` package path, optional dependency drift, `N-CODE-CLEAN-IMPORT` 계열 위험.
- **실제로 할 것:** clean temporary environment와 detached checkout에서 editable/non-editable install, import ownership, CLI와 대표 generators를 재생한다. dependency lock/receipt를 만들고 local cache, cwd, implicit `PYTHONPATH`, untracked 파일 의존을 mutation한다.
- **하지 말 것:** public package rename이나 대규모 layout migration을 한 번에 수행하지 않는다. optional dependency 미설치를 silent skip으로 바꾸지 않는다.
- **주의·anti-drift:** clean replay 성공은 science validation이 아니다. legacy import compatibility와 active owner를 구분한다.
- **검증·산출물:** clean-install matrix, wheel/sdist smoke, detached replay receipt, owner namespace test, temp-CWD import test, environment hash.
- **Exit / kill:** tracked inputs만으로 collect/smoke/representative generation이 재현되어야 한다. cwd 또는 untracked data가 없으면 결과가 달라질 경우 PR-122 이후 evidence를 신뢰하지 않는다.
- **최대 claim:** clean-install/replay mechanics C1.

### PR-122 — Claim-addressed evidence graph와 content-addressed build DAG

- **Owner / dependencies / cost:** `COMMON`; PR-119, PR-121; medium--high.
- **Targets:** `CO-01`, `CO-03`, `N-CODE-FALSE-GREEN`, `N-STAT-SPOOFABLE-GATE`, `C7-MES-F2`, `N-THEORY-D2-AUTHORITY`.
- **실제로 할 것:** claim → producer → input/config/environment → test/oracle → artifact → consumer edge를 typed graph로 표현한다. `process_result`와 `scientific_status`를 분리하고 blocked/missing/stale/invalid/skipped/xfail을 서로 다른 상태로 둔다. receipt ID/version, authorized principal attestation, parent/independence edge를 content-address하고 package/freeze가 exact receipt를 소비하도록 한다. test selector와 실제 collected/executed count를 edge에 넣어 zero-test Rust/Python target을 authority로 세지 않으며, active MES consumer가 typed successor registry를 거치지 않으면 release를 막는다.
- **하지 말 것:** graph가 있다는 이유로 estimand correctness나 independent validation을 주장하지 않는다. 기존 manifest를 포장하는 wrapper-only 구현을 만들지 않는다.
- **주의·anti-drift:** verifier와 policy가 새 trust root가 된다. mutation corpus가 없거나 self-oracle만 연결되면 false-green이 계속된다.
- **검증·산출물:** nonexistent/zero-collected test, stale generator, hash mismatch, blocked science, invalid manifest, fabricated/self-signed/circular-parent receipt, author=adjudicator, dependency cycle, stale MES triple, 임의 객체의 `ready_for_claims=true`, caller-supplied pseudo-PPC/Bayes scalar mutation; graph schema와 CLI; per-claim closure report.
- **Exit / kill:** 모든 mutation이 fail/downclaim되고 clean fixture만 reproducibly pass해야 한다. blocked science가 green package에 들어가면 release 작업 중단.
- **최대 claim:** fail-closed release/evidence mechanics C1.

### PR-123 — 독립 수치 oracle, K6 continuum branch와 mutation laboratory

- **Owner / dependencies / cost:** `COMMON`; contributors는 각 canonical lane owner; PR-121, PR-122; high.
- **Targets:** `CO-04`와 CF4, GRF, DESI, K6, ACT, JWST의 알려진 defect corpus; `C6-K6-CURL-F1/F3/F4`의 CF4-catalog-independent numerical mechanics.
- **실제로 할 것:** production과 알고리즘·소스 lineage가 다른 작은 reference를 만든다. shell-monopole leak, non-Hermitian rFFT plane, fixed-alpha mock, low-order curl stencil, ignored host error, asymmetric global rank, fitted-score pseudo-Bayes factor, plug-in pseudo-PPC, stale transfer range를 각각 mutation으로 고정한다. K6는 CF4 row/selection authority와 분리된 branch에서 analytic solid-body/potential/mixed Helmholtz/manufactured-boundary fields, 최소 4개 grid와 2개 stencil order, interpolation/boundary/amplitude-gradient decomposition, continuum extrapolation과 analytic `sqrt(2)` residual lock을 실행한다. manufactured solution, invariance/property, convergence, coverage를 lane별로 정의한다.
- **하지 말 것:** production 코드를 조금 바꾼 것을 independent implementation이라 부르지 않는다. mechanics pass를 matched data/null/covariance pass로 승격하지 않는다.
- **주의·anti-drift:** 같은 논문식·fixture·author를 공유한 oracle 간 상관을 기록한다. reference가 production보다 복잡해지면 새 defect source가 된다.
- **검증·산출물:** mutation kill matrix, oracle lineage manifest, per-lane independent reference, multi-seed property/coverage suite, K6 continuum-order/upper-bound/no-empirical-consumer card, surviving mutation report.
- **Exit / kill:** 사전 등록한 known mutation 하나라도 살아남거나 두 oracle의 독립성을 입증하지 못하면 해당 lane validation은 blocked다.
- **최대 claim:** lane-specific numerical mechanics C2; cosmological inference 아님.

### Checkpoint 070

PR-123 완료 후 총 70개 checkpoint를 실행한다. PR count 외에 open P0/P1, `EVIDENCE_READY`, non-author adjudication 수, stale consumer 수, matched-null/covariance readiness와 현재 최고 claim tier를 기록한다. P0 quarantine이 깨지거나 두 PR 연속으로 schema/manifest만 늘고 executable falsifier가 없으면 DAG를 중단하고 replan한다.

## 7. Wave 14 — 이론 기반 I: theorem authority와 non-identification

### PR-124 — Four-axis CAS contract + derivation-lineage oracle

- **Owner / dependencies / cost:** `COMMON`; contributor `BASS`; PR-123; medium.
- **Targets:** `CO-05`, `C8-FRAMEWORK-F3/F4`, `C7-MES-F1--F4`, `N-THEORY-D2-AUTHORITY`, theorem-count와 조건 누락.
- **실제로 할 것:** theorem registry가 quantified variables, hypotheses, frame/order/domain과 `published_proof / independent_derivation / checked_derivation / numerical_test / sanity_anchor / specification` 증거등급을 생성하게 한다. CAS 검증은 dual-engine이 아니라 four-axis CAS contract(Wolfram+xAct, SymPy, SageMath+Singular, Lean; `.agent-harness/templates/CAS_CONTRACT.json` v2와 `.agent-harness/scripts/cas_gate.py` adjudication, AMENDMENT_01)로 실행한다. 네 engine의 agreement와 최소 두 개의 실제 독립 derivation lineage는 서로 다른 지표다 — 전자는 계산 재현성, 후자는 유도 독립성이며 어느 쪽도 다른 쪽을 대체하지 않는다. MES에는 geodesic/non-geodesic/acceleration branch별 source DOI/arXiv 또는 scan authority, page/equation, convention translation, 실제 독립 derivation 수와 물리 가정 불확실성을 별도 필드로 둔다. legacy registry는 byte-stable reproduction으로 격리하고 active consumer는 typed successor pointer만 사용한다. D2 authority는 Python anchor와 출발식/author가 분리된 nonzero Rust target의 source/input/output/toolchain hash와 실제 collected/executed count를 요구한다. sanity anchor와 같은 식의 재평가는 theorem/independent-derivation count에서 제외한다.
- **하지 말 것:** 같은 AST나 generated expression을 두 backend에서 평가한 것을 두 derivation으로 세지 않는다. numeric spot check를 proof로 부르지 않는다.
- **주의·anti-drift:** theorem statement가 바뀌면 모든 consumer hash를 invalidate한다. all-parameter prose는 checked signature에서만 생성한다.
- **검증·산출물:** theorem inventory, MES source/equation/branch authority와 successor-registry table, convention translation fixtures, sign/unit/limit mutations, stale triple/branch swap/source-count inflation/zero-test mutation, nonzero independent Rust receipt, old overstatement negative test, all-consumer/manuscript reconciliation과 lineage receipt.
- **Exit / kill:** engine 간 sign/coefficient/domain 불일치가 0이어야 하며, MES active consumer의 stale triple이 0이고 D2 target이 실제 nonzero로 독립 실행되어야 한다. 하나라도 실패하면 해당 branch/theorem과 모든 dependent result를 blocked 처리한다.
- **최대 claim:** domain/frame-conditional derived mechanics C1.

### PR-125 — Canonical frame, order, domain과 premise contract

- **Owner / dependencies / cost:** `COMMON`; contributor `BASS`, implementation scope `common|bass_py`; PR-124; medium.
- **Targets:** `N-THEORY-FRAME-SCOPE`, `C8-FRAMEWORK-F2/F5`, 암묵적 signature/frame/order.
- **실제로 할 것:** normal, matter, electron, CMB, local-observer frame; perturbative order; background class; units; harmonic convention; redshift/depth convention을 typed object로 만든다. theorem, transfer, estimator artifact가 같은 contract를 참조하도록 한다.
- **하지 말 것:** frame transform이 없는 scalar alias를 만들어 차이를 숨기지 않는다. `beta=0`를 EGS/FLRW premise 전체로 대체하지 않는다.
- **주의·anti-drift:** legacy defaults는 reproduction mode에서만 허용하고 active producer는 explicit fields 없으면 fail한다.
- **검증·산출물:** frame round-trip, vorticity/tilt sign, FLRW/no-tilt/local-boost/global-tilt limits, unknown/default rejection, theorem-to-frame dependency graph.
- **Exit / kill:** active theorem/estimator가 암묵적 frame/order로 생성되면 downstream theory PR을 금지한다.
- **최대 claim:** convention contract correctness C1.

### PR-126 — One-way FLRW/EGS와 counterexample registry

- **Owner / dependencies / cost:** `COMMON`; contributor/consumer `BASS`; PR-124, PR-125; medium--high.
- **Targets:** `N-THEORY-FLRW-CONVERSE`, `N-THEORY-EGS-CONVERSE`, `TH-01`.
- **실제로 할 것:** exact EGS와 almost-EGS의 matter, differentiability, radiation multipole, observer congruence premises를 DAG로 분리한다. comparator-matched FLRW → `x_C=0`의 one-way statement와 `x_C=0`이 FLRW를 보장하지 않는 cancellation witness를 함께 봉인한다. almost-EGS는 정량 regularity/remainder가 없는 한 specified 상태로 둔다.
- **하지 말 것:** converse, truth certificate, `beta=0 ⇒ EGS`, scalar-to-geometry language를 사용하지 않는다.
- **주의·anti-drift:** counterexample를 새 premise로 사후 제거하면 새 theorem ID를 발급한다. exact와 almost theorem을 한 claim으로 합치지 않는다.
- **검증·산출물:** premise DAG, SymPy/independent tensor reassembly, random cancellation property test, nonzero-shear/beta-zero witness, generated safe theorem text.
- **Exit / kill:** premise-complete FLRW state에서 `x_C≠0`이 나오거나 counterexample registry를 통과하지 못하면 statement를 폐기한다.
- **최대 claim:** conditional mathematics C2; FLRW certificate 없음.

### PR-127 — Cancellation-preserving graded/PSD-cone non-identification theorem

- **Owner / dependencies / cost:** `COMMON`; contributors `HTT`, `BASS`; PR-125, PR-126; medium--high.
- **Targets:** `TH-02`, `N-STAT-ID-REGISTRY-HISTORY`, scalar family-ID 위험.
- **실제로 할 것:** response map의 kernel, cancellation cone, rank-deficient sectors와 set-valued equivalence class를 정의한다. shear/vorticity처럼 양의 quadratic component는 PSD cone으로, signed `Delta Omega_k`는 별도 `R` 축 또는 branch-signed cone으로 표현해 ambient algebraic carrier를 예컨대 `S_+^3 x R`로 둔다. 각 class/branch의 Hamiltonian·momentum constraint, matter positivity와 domain 조건을 만족하는 물리 subset `A_C`를 별도로 정의하고 constraint verifier가 없는 witness는 `algebraic_only`로 표시한다. constructive witnesses로 point identification 불가능 영역을 보이고, 추가 observable이 rank를 실제로 올리는 조건을 theorem/API로 만든다.
- **하지 말 것:** non-identification을 isotropy의 증명으로 해석하거나 nuisance class를 결과를 보고 축소하지 않는다.
- **주의·anti-drift:** scalar 차원 수가 parameter 수와 같다는 이유로 rank를 가정하지 않는다. signed 변수를 PSD projection으로 잘라 cancellation witness를 없애지 않는다. transfer/mask/window가 response rank를 바꾼다.
- **검증·산출물:** exact kernel witnesses, ambient-carrier와 `A_C` 분리, Gauss/Hamiltonian/momentum/matter-positivity constraint fixtures, randomized cone tests, rank under mask/window fixtures, empty/unbounded/multi-component identified-set outputs.
- **Exit / kill:** 독립 engine이 rank/kernel에 동의하지 않으면 stronger inference를 block한다.
- **최대 claim:** declared response map의 formal non-identification C2.

### PR-128 — NT2 coefficient authority와 downstream invalidation

- **Owner / dependencies / cost:** `COMMON`; contributors `OBSSTAT`, `BASS`; PR-124, PR-125, PR-127; medium.
- **Targets:** `N-THEORY-NT2-COEFFICIENT`, NT2 bracket consumer.
- **실제로 할 것:** specification-first로 `a2 = kappa Sigma (1+delta)`의 coefficient 방향과 domain을 정하고, exact Fraction과 독립 symbolic/numeric derivation을 수행한다. 올바른 lower bracket과 `F_lo`를 생성하고 reciprocal-wrong consumer를 전수 invalidate/regenerate한다.
- **하지 말 것:** 기존 출력과 가까운 계수를 선택하거나 upper MES placeholder와 lower theorem을 한 proven interval로 합치지 않는다.
- **주의·anti-drift:** coefficient normalization이나 response convention이 달라지면 새 config/theorem ID를 발급한다.
- **검증·산출물:** exact proof record, randomized admissible states, zero/negative denominator rejection, consumer graph와 before/after table.
- **Exit / kill:** admissible case 하나라도 bound를 위반하거나 engine이 coefficient 방향에 불일치하면 모든 NT2/F consumer를 blocked한다.
- **최대 claim:** closure/H3-conditional algebraic bracket C1--C2.

### Checkpoint 075

이론 PR의 green test 수가 아니라, theorem signature 수, independent derivation 수, surviving counterexample 수, blocked consumer 수와 최대 claim tier를 기록한다. PR-128은 기존 수치를 바꿀 수 있으므로 manuscript/result pack에는 아직 유입시키지 않는다.

## 8. Wave 15 — 이론 기반 II: estimator, sufficiency, asymptotic과 local/global 분리

### PR-129 — NTA3 estimator/domain registry와 universal-floor 금지

- **Owner / dependencies / cost:** `OBSSTAT`; contributors `BASS`, `HTT`; PR-124, PR-125; low--medium.
- **Targets:** `N-THEORY-NTA3-REGRESSION`.
- **실제로 할 것:** 이상적 full-sky Gaussian quadrupole-power estimator에 대한 `sd(Fhat)/F=sqrt(2/5)`를 estimator/domain-specific theorem으로 등록한다. multi-multipole Fisher quantity와 분리하고 독립 chi-square Monte Carlo로 확인한다.
- **하지 말 것:** universal/minimax/Cramér--Rao floor, mask/noise/general estimator에 대한 “더 잘할 수 없음” 문구를 유지하지 않는다.
- **주의·anti-drift:** 이것은 원 universal claim의 literal rescue가 아니라 corrected supersession이다.
- **검증·산출물:** typed estimator registry, analytic/MC comparison, all-consumer negative scan과 generated captions.
- **Exit / kill:** 선언한 이상 조건에서 MC가 사전 오차 이상 벗어나면 analytic/implementation을 재검토하고 claim을 내지 않는다.
- **최대 claim:** estimator-specific theorem C1.

### PR-130 — Low-multipole convergence와 statistical sufficiency의 분리

- **Owner / dependencies / cost:** `OBSSTAT`; contributors `BASS`, `HTT`; PR-128, PR-129; medium.
- **Targets:** `N-THEORY-NT2-SUFFICIENCY`.
- **실제로 할 것:** 등록 response에서 finite/infinite Fisher tail의 양수성·수렴률을 analytic bound와 arbitrary-precision sum으로 계산한다. factorization theorem이 없는 한 `sufficient`를 금지하고 truncation error/convergence만 보고한다.
- **하지 말 것:** tail이 작거나 L=80 결과가 안정적이라는 이유로 Rao--Blackwell/sufficiency를 주장하지 않는다.
- **주의·anti-drift:** response profile 또는 transfer가 바뀌면 tail theorem domain도 바뀐다. toy response를 observed low-ell information으로 해석하지 않는다.
- **검증·산출물:** tail bound/zeta expression, high-precision sum, transfer profile sensitivity, forbidden-sufficiency scan.
- **Exit / kill:** tail이 0이 아니거나 factorization이 없으면 exact sufficiency claim은 영구 금지한다.
- **최대 claim:** toy/transfer-conditional convergence theorem C1.

### PR-131 — Near-FLRW symbolic expansion과 singular-boundary map

- **Owner / dependencies / cost:** `COMMON`; contributor/consumer `BASS`, implementation scope `common|bass_py`; PR-124--128; high.
- **Targets:** `N-THEORY-OMK-DOMAIN`, `TH-07`의 symbolic half.
- **실제로 할 것:** named LRS-III/KS reduced system, background `q0/w`, frame와 expansion parameter를 고정한다. constraint-surface와 metric/tetrad 두 경로로 linear/next-order coefficient, transient mode, singular/zero-denominator boundary를 도출한다.
- **하지 말 것:** `q`를 고정하지 않은 global equality, six finite ceiling, observational curvature/shear 값을 이 PR에서 복구하지 않는다.
- **주의·anti-drift:** class mirror와 sign convention을 분리한다. fitted line은 derivation이 아니다.
- **검증·산출물:** symbolic Jacobian/eigenvector, independent finite-difference derivative as `K→0`, dimensional/sign/FLRW/vacuum/radiation/dust checks, singular map.
- **Exit / kill:** derivative plateau가 analytic coefficient와 불일치하거나 class 내부 singularity가 선언 domain에 들어오면 domain을 축소하거나 abandon한다.
- **최대 claim:** class-conditional asymptotic coefficient C2.

### PR-132 — Interval/high-precision remainder certification과 uncertainty propagation

- **Owner / dependencies / cost:** `COMMON`; contributor/consumer `BASS`; PR-131; high.
- **Targets:** `N-THEORY-OMK-DOMAIN`, OMK finite-use readiness.
- **실제로 할 것:** compact declared domain에서 `O(K^2)`와 transient remainder를 interval 또는 independent high-precision enclosure로 bound한다. domain API가 외부 평가를 거부하게 하고 remainder를 every downstream ceiling/forecast에 uncertainty로 전파한다. numerical enclosure, source/convention uncertainty, physical model-form uncertainty와 in-house conservative rule을 서로 다른 component로 보존하며 MES 소비자에도 같은 분리를 적용한다.
- **하지 말 것:** finite grid sampling을 uniform proof라고 부르거나 remainder를 central coefficient에 흡수하지 않는다.
- **주의·anti-drift:** bound가 넓어 유용하지 않아도 성공 결과다. domain을 observed value에 맞게 사후 확대하지 않는다.
- **검증·산출물:** interval/high-precision certificate, boundary adversarial states, propagation tests, domain rejection mutations.
- **Exit / kill:** admissible state가 enclosure를 벗어나면 즉시 claim block; domain 축소는 새 version으로 기록한다.
- **최대 claim:** explicit remainder를 가진 class-conditional asymptotic theorem C2.

### PR-133 — Local observer boost, global tilt와 source-response type system

- **Owner / dependencies / cost:** `COMMON`; contributors/consumers `BASS`, `OBSSTAT`, implementation scope `common|bass_py|obsstat`; PR-125, PR-127, PR-132; high.
- **Targets:** `N-THEORY-OMEGA-SEMANTICS`, `TH-03`, `TH-04`의 pre-solver interface.
- **실제로 할 것:** linear observer proxy `A_v`, physical `Omega_tilt`, vorticity, shear, curvature와 background geometry를 서로 다른 type으로 분리한다. frame/order transformation, response vector, blind/aligned sector, source-response equivalence edge를 기록한다. 각 후보는 `algebraic_witness -> constraint_admissible -> local_dynamics_admissible -> global_dynamics_admissible` 사다리 중 도달한 단계만 표시한다. deprojection은 synthetic local-boost estimator property로만 검증한다.
- **하지 말 것:** `A_v`와 `Omega_tilt` 자동 bridge, scalar value로 Bianchi family 또는 global tilt 측정, aligned-axis rank-1 예외 은폐를 하지 않는다.
- **주의·anti-drift:** transfer/mask/window가 response collinearity를 바꾸므로 analytic rank와 observed rank를 구분한다. algebraic cancellation이나 constraint 해를 실제 Einstein--matter trajectory 또는 global cosmology로 승격하지 않는다.
- **검증·산출물:** typed rename migration, harmonic boost derivation, local/global injections, frame/axis invariance, response graph와 non-bridge semantic guard.
- **Exit / kill:** pure local boost가 declared order에서 제거되지 않거나 global/local response가 rank-deficient이면 출력은 `non_identified`다.
- **최대 claim:** pre-solver discrimination diagnostic C2--C3; 측정/geometry 아님.

### Checkpoint 080

PR-133 후 이론 foundation을 freeze한다. 아직 data application을 시작하지 않는다. theorem registry에서 `derived`, `tested`, `specified`, `conditional`을 재계수하고, corrected-superseded 원 finding을 `rescued`로 잘못 센 행이 0인지 확인한다.

## 9. Wave 16 — 통계 기반 I: estimand, finite null, partial identification와 PPC

### PR-134 — Estimand, population, dependency, selection와 nuisance registry

- **Owner / dependencies / cost:** `COMMON`; contributors `OBSSTAT`, `HTT`; PR-122, PR-125, PR-133; high.
- **Targets:** estimand mismatch, hidden sample/window/depth conventions, `N-STAT-PRIOR-PROVENANCE`의 upstream, `C1-K5-MV-F4/F5`, `C3-K5-VCORR-ML-F6`.
- **실제로 할 것:** 각 analysis에 target population, observation unit, dependence cluster, selection/mask/window, preprocessing, estimand, nuisance family, prior/null/multiplicity와 allowed transformations를 typed registry로 만든다. deterministic-template mean와 stochastic covariance data factor를 별도 generative branch로 표현한다.
- **하지 말 것:** 모든 survey를 같은 “channel” type으로 평탄화하거나 dependency를 독립 행으로 가정하지 않는다. generic contract만 추가하고 실제 CF4/K1/DESI fixtures가 없는 PR로 끝내지 않는다.
- **주의·anti-drift:** registry 수정은 analysis-family 변경이다. observed result를 본 뒤 nuisance/depth/window를 수정하면 새 ID와 multiplicity를 요구한다.
- **검증·산출물:** CF4/K1/DESI/ACT/JWST representative contracts, round-trip/schema tests, hidden-default mutation, estimand fingerprint와 dependency graph.
- **Exit / kill:** active inference가 registry 없이 실행되거나 template/covariance branch를 혼합하면 통계 PR 전체를 block한다.
- **최대 claim:** estimand/analysis specification mechanics C1.

### PR-135 — Exchangeable observation-inclusive finite-null global ranking

- **Owner / dependencies / cost:** `OBSSTAT`; PR-123, PR-134; medium.
- **Targets:** `ST-03`, `N-STAT-K1-EXCHANGE`, `N-STAT-DEGENERATE-NULL`, `C2-K5-MOCKSIG-F3`, `C5-EXT-ACT-F4`.
- **실제로 할 것:** observation과 모든 null row를 같은 방식으로 score/maximize하는 pooled 또는 leave-one-row-out rank API를 만든다. `(+1)/(N+1)`, tie policy, discrete interval, max-statistic와 independent calibration/evaluation split을 지원한다. correlated scan statistics는 row 내부 dependence를 보존한다.
- **하지 말 것:** observation에만 가능한 local rank를 만들거나 0 p-value, finite resolution 아래 Gaussian sigma를 보고하지 않는다.
- **주의·anti-drift:** statistic family, scan range, mask 또는 tie policy가 바뀌면 global calibration을 전부 다시 한다.
- **검증·산출물:** exact enumeration small-N fixtures, super-uniform type-I simulations, tied/discrete cases, dependence-preserving max scan, finite-rank report schema. Monte Carlo p-value는 [Phipson--Smyth](https://arxiv.org/abs/1603.05766)의 exact-discrete 관점을 따른다.
- **Exit / kill:** registered null families와 operational N에서 super-uniformity/size가 실패하면 global p interpretation을 폐기한다.
- **최대 claim:** matched-null-conditioned global calibration C2.

### PR-136 — Generic partial-identification와 identified-set engine

- **Owner / dependencies / cost:** `HTT`; PR-127, PR-134; high.
- **Targets:** `ST-04`, `N-STAT-PI-COVERAGE`, CF4/fσ8/local-global point-identification 과장.
- **실제로 할 것:** equality/inequality constraints, nuisance projection, bounded/empty/unbounded/disconnected set와 response-rank deficiency를 한 API로 계산한다. full parameter와 subvector identified set을 분리하고 scalar summary 대신 set-valued artifact를 생성한다.
- **하지 말 것:** empty set을 detection으로, broad set을 central estimate로, solver nonconvergence를 non-identification으로 혼동하지 않는다.
- **주의·anti-drift:** nuisance class와 admissible set을 observed fit에 맞게 줄이지 않는다. projection과 optimization tolerance를 uncertainty 밖으로 숨기지 않는다.
- **검증·산출물:** analytic toy sets, kernel/cancellation fixtures, interval/LP/nonlinear cross-engine comparisons, set topology and provenance manifest. 방법론 기준은 identified set에 대한 Monte Carlo confidence set 연구인 [Chen--Christensen--Tamer](https://arxiv.org/abs/1605.00499)를 참조한다.
- **Exit / kill:** independent engine이 set boundary/status에 불일치하면 downstream numerical claim을 block한다.
- **최대 claim:** formal/algorithmic identified region C2.

### PR-137 — Weak-identification boundary와 grid-conditional simultaneous coverage

- **Owner / dependencies / cost:** `HTT`; contributor `OBSSTAT`; PR-123, PR-135, PR-136; high.
- **Targets:** `N-STAT-PI-COVERAGE`, `GAP-05`, near-null nuisance와 boundary posterior.
- **실제로 할 것:** point/partial/unidentified regimes를 연속적으로 가로지르는 DGP grid를 사전 등록한다. complete frozen algorithm의 simultaneous coverage, empty/unbounded rate, boundary behavior와 optimization failure를 측정한다. 기본 pre-registration은 nominal coverage 0.95, 허용 undercoverage 0.02, grid point당 최소 2,000 independent replicates를 최소 10 seed에 분배하고, family-wise 99% binomial lower bound가 0.93 경계에서 0.01 이내면 최대 10,000까지 연장한다. 최소 두 mesh refinement에서 coverage 변화와 optimizer endpoint error를 보고한다. continuity/mesh-error theorem이 있을 때만 nuisance class 전체의 uniform coverage라 부르고, 그렇지 않으면 grid-conditional simultaneous empirical coverage로 제한한다.
- **하지 말 것:** central/high-signal cases만 골라 coverage를 주장하거나 실패한 nuisance corner를 domain에서 조용히 제거하지 않는다.
- **주의·anti-drift:** threshold를 coverage 결과에 맞게 튜닝하면 calibration/evaluation split을 새로 만든다.
- **검증·산출물:** 최소 10-seed/2,000-replicate DGP grid, family-wise 99% binomial lower intervals, two-level mesh/optimizer-error report, boundary/adversarial fixtures, coverage dashboard와 fail-closed status.
- **Exit / kill:** retained grid point의 lower bound가 0.93 미만이거나 mesh refinement에서 coverage가 0.01 넘게 변하거나 optimizer error가 reported endpoint tolerance의 10%를 넘으면 scientific bound를 내지 않고 failure map을 보존한다. uniform이라는 단어는 continuity/mesh certificate가 없으면 lint가 거부한다.
- **최대 claim:** grid-conditional coverage-calibrated partial-identification mechanics C2; uniform class-wide claim은 별도 theorem이 있을 때만.

### PR-138 — Lineage-bound posterior draws, SBC와 실제 replicated-data PPC

- **Owner / dependencies / cost:** `HTT`; PR-122, PR-134, PR-137; high.
- **Targets:** `N-STAT-PSEUDO-PPC`, `ST-02`, arbitrary caller-supplied p-value/prediction.
- **실제로 할 것:** posterior draw를 normalized prior, likelihood/data/config/transfer와 sampler diagnostics에 content-address한다. prior predictive stress, simulation-based calibration, replicated observations, preregistered discrepancy와 posterior-predictive calibration을 구현한다. old plug-in residual은 별도 `residual_check` type으로 유지한다.
- **하지 말 것:** caller-supplied point prediction/p-value를 PPC receipt로 받거나 실패 후 discrepancy를 교체하지 않는다. invalid posterior에서 PPC를 실행하지 않는다.
- **주의·anti-drift:** PPC 통과는 model truth가 아니며, failure는 threshold tuning이 아니라 inadequacy 결과다. SBC는 computation calibration이고 observed fit 검증과 다르다.
- **검증·산출물:** rank-uniform SBC tests, replicated-data hashes, multiple frozen discrepancies, posterior lineage mutation, synthetic known-good/known-bad models. SBC 기준은 [Talts et al.](https://arxiv.org/abs/1804.06788)을 따른다.
- **Exit / kill:** SBC, sampler diagnostics 또는 frozen PPC가 실패하면 `inadequate/blocked`; evidence claim 금지.
- **최대 claim:** model/transfer-conditional predictive adequacy C2--C3.

### Checkpoint 085

PR-138 후 pseudo-PPC 소비자가 0인지, posterior lineage 누락이 fail하는지, finite-null API가 operational N에서 size를 통제하는지 확인한다. 통계 framework의 green test가 observational claim을 승격하지 않음을 checkpoint에 명시한다.

## 10. Wave 17 — 통계 기반 II: holdout, evidence, abstention와 MIO calibration

### PR-139 — Dependency-aware holdout와 train-only refit

- **Owner / dependencies / cost:** `HTT`; PR-134, PR-138; high.
- **Targets:** `N-STAT-PSEUDO-LOOCV`, `ST-02`.
- **실제로 할 것:** observation/group/survey/depth 단위의 dependency graph를 바탕으로 valid fold를 선택한다. 모든 preprocessing, nuisance fit, axis/feature selection을 training data에서만 다시 실행하고 held-out joint log predictive density를 계산한다. exact refit을 기준으로 PSIS 근사를 검증한다.
- **하지 말 것:** channel ablation이나 full-vs-fold evidence difference를 LOOCV라 부르지 않는다. dependent row를 독립 LOO unit으로 사용하지 않는다.
- **주의·anti-drift:** valid exchangeable unit이 없으면 `LOO_not_identified`; channel ablation은 별도 sensitivity로 남긴다. PSIS diagnostic이 나쁘면 exact refit으로 돌아간다.
- **검증·산출물:** leakage mutations, train-only transform hashes, exact-vs-PSIS comparison, influential fold report, dependency-bound ELPD. 기준 방법은 [Vehtari--Gelman--Gabry](https://arxiv.org/abs/1507.04544)를 참조한다.
- **Exit / kill:** leakage 또는 fold dependency 위반, approximate/exact disagreement가 허용폭을 넘으면 predictive comparison을 block한다.
- **최대 claim:** dependency-qualified held-out predictive score C2--C3.

### PR-140 — Normalized-prior coherent evidence와 두 독립 engine

- **Owner / dependencies / cost:** `HTT`; PR-122, PR-134, PR-138, PR-139; high.
- **Targets:** `N-STAT-PSEUDO-BAYES`, `N-STAT-PRIOR-PROVENANCE`, `ST-01`의 기반.
- **실제로 할 것:** normalized prior family, likelihood/data hash, evidence engine/config/diagnostics를 한 receipt에 묶는다. nested/bridge/thermodynamic 또는 analytic small-model reference 중 두 독립 경로를 사용하고 prior-scale, covariance, nuisance sensitivity를 사전 grid에서 평가한다.
- **하지 말 것:** fitted score, unnormalized prior, caller-supplied scalar를 Bayes factor로 부르지 않는다. 두 engine을 같은 samples/weights로 단순 후처리하지 않는다.
- **주의·anti-drift:** evidence agreement가 generative model correctness를 보장하지 않는다. prior-dominated 결과는 그대로 표시한다.
- **검증·산출물:** analytic evidence fixtures, prior normalization/property tests, engine disagreement policy, sensitivity surface와 arbitrary-summary mutation.
- **Exit / kill:** engine disagreement, insufficient ESS/diagnostics 또는 prior sensitivity가 preregistered ceiling을 넘으면 evidence claim은 `indeterminate`다.
- **최대 claim:** coherent model comparison conditional on registered model/prior C3.

### PR-141 — Contamination-aware local/global mixture와 mandatory abstention

- **Owner / dependencies / cost:** `HTT`; PR-133, PR-136--140; high.
- **Targets:** `ST-01`, `ST-07`, local boost/global tilt/systematics 분리.
- **실제로 할 것:** isotropy, local boost, survey/calibration systematic, shared/global anisotropy candidate를 명시적 competitor로 둔다. response-rank, posterior/predictive adequacy, held-out gain, prior sensitivity가 부족하면 mandatory abstention을 반환한다. deterministic/covariance branch를 따로 비교한다.
- **하지 말 것:** 모든 residual을 global component로 흡수하거나 MIO score를 likelihood factor로 사용하지 않는다.
- **주의·anti-drift:** model list와 contamination prior를 observed outcome 후 바꾸면 새 family와 multiplicity를 등록한다. positive global result를 목표 함수로 삼지 않는다.
- **검증·산출물:** synthetic recovery/confusion/abstention matrix, null/systematic/local/global held-out simulations, posterior calibration과 model misspecification cases.
- **Exit / kill:** rank deficiency, failed PPC/LOO, no predictive gain, high prior sensitivity이면 `abstain/non_identified`가 유일한 허용 결과다.
- **최대 claim:** local/global discrimination candidate C3; geometry/family 아님.

### PR-142 — MIO joint-measure `F/Pi/G_F` invariance와 matched-null calibration

- **Owner / dependencies / cost:** `MIO`; PR-134--137, PR-141; high.
- **Targets:** `ST-06`, `N-STAT-MIO-F-MEASURE`, MIO diagnostic calibration gap.
- **실제로 할 것:** identity, weights, pairing, depth/reference policy를 가진 `MeasureSpec`을 정의한다. `F`, `Pi`, `G_F`의 permutation/pairing/depth sensitivity, uncertainty와 matched-null distribution을 diagnostic report로 만든다. invalid/no-justified-measure 상태를 허용한다.
- **하지 말 것:** posterior probability, evidence, truth certificate, HTT likelihood term을 만들지 않는다. `Q`, `F`, `Pi`를 서로 대체하지 않는다.
- **주의·anti-drift:** joint measure 선택은 scientific assumption이다. 결과를 보고 weight/pairing을 변경하면 새 diagnostic family로 센다.
- **검증·산출물:** MeasureSpec contract, relabel/permutation invariance, paired/unpaired counterexamples, matched-null calibration, MIO/HTT no-merge tests.
- **Exit / kill:** scientifically defensible joint measure가 없으면 measure-family sensitivity만 보고하고 calibrated scalar를 내지 않는다.
- **최대 claim:** calibrated MIO diagnostic C2; posterior/evidence 없음.

### PR-143 — 통합 synthetic calibration과 hostile statistical adjudication

- **Owner / dependencies / cost:** `COMMON`; non-author adjudicator 별도; PR-135--142; high.
- **Targets:** 통계 foundation 전체, `GAP-05`, `CO-04/ST-03/ST-04` acceptance.
- **실제로 할 것:** known-null, local, global, systematic, weak-ID, dependent-mock, covariance-misspecified DGP를 blind challenge로 구성한다. 각 method가 size, coverage, calibration, abstention, computational failure를 preregistered 기준에서 충족하는지 non-author referee가 판정한다.
- **하지 말 것:** data-specific favorable case만 고르거나 failed method를 threshold retuning 후 같은 challenge ID로 재평가하지 않는다.
- **주의·anti-drift:** synthetic challenge 통과는 observed validity가 아니라 method readiness다. generator와 analyst의 분리를 receipt에 기록한다.
- **검증·산출물:** sealed challenge inputs, predictions, size/coverage/confusion results, independent referee report, method-ready/block matrix.
- **Exit / kill:** foundation method 하나가 실패하면 그 방법에 의존하는 data PR만 block하고 실패를 숨기지 않는다.
- **최대 claim:** pre-data method calibration C2--C3.

### Checkpoint 090

PR-143 완료 시에만 authenticated data 분석을 시작한다. checkpoint에는 method-ready 수, failed/abstain 수, empirical size/coverage, independent referee 판정, open P0/P1와 data readiness를 기록한다. 통계 foundation이 실패하면 데이터 PR을 강행하지 않는다.

## 11. Wave 18 — CF4와 velocity-field 연구

### PR-144 — Authenticated CF4 row/group/selection manifest

- **Owner / dependencies / cost:** `OBSSTAT`; PR-120, PR-134, PR-143; medium, 입력 권위에 따라 blocked 가능.
- **Targets:** 두 CF4 P0의 data lineage, `C1-K5-MV-F4/F5`, `N-DATA-CF4-DOWNSTREAM`.
- **실제로 할 것:** exact catalogue/release, row/group ID, RA/Dec/redshift frame, `Dist/e_DMzp/Vpds/Vpwf/Vpec` 정의·units·producer, indicator/calibration group, selection/completeness, grouping, duplicate/missing과 transformations를 row-level hash로 묶는다. 각 column이 observable, proxy, reconstruction 또는 derived correction인지 구분한다.
- **하지 말 것:** Vpec/Vpwf를 true flow로 선택하거나 audit 94 km/s 값을 observed replacement로 승격하지 않는다. 권위가 불명확한 column을 이름만 보고 사용하지 않는다.
- **주의·anti-drift:** release 또는 depth convention이 바뀌면 새 dataset identity다. raw data는 read-only 외부 경로에 두고 manifest만 version한다.
- **검증·산출물:** row count/ID parity, units/range/coordinate fixtures, source hash/transform replay, duplicate/group graph, `cf4_authenticated_manifest` 또는 explicit missing-authority report.
- **Exit / kill:** row/group/selection과 core column authority를 재현할 수 없으면 PR-145--148을 `BLOCKED`로 유지한다.
- **최대 claim:** dataset/estimand provenance C1.

### PR-145 — Radial-monopole와 velocity-shape estimator mechanics

- **Owner / dependencies / cost:** `OBSSTAT`; PR-123, PR-134--137, PR-144; high.
- **Targets:** `C1-K5-MV-F1` P0, `C3-K5-VCORR-ML-F1` P0, `C1-F2/F5`, `C3-F4/F5/F6`, `C9-F1/F2`.
- **실제로 할 것:** raw distance observable에서 standard MV/GLS, flow+radial-monopole constrained estimator, registered distance likelihood, velocity-correlation linear/nonlinear branches를 한 estimand registry에서 구현한다. Vpds/Vpec injection은 별도 config/seed/hash로 수행한다. 정확한 eight-region partition, leverage, non-railed nuisance fit과 common-window response를 추가한다.
- **하지 말 것:** constrained estimator의 중앙값을 truth로 선언하거나 기존 P0 headline에 가장 가까운 nuisance/model을 선택하지 않는다. ten-key partition을 “octant”로 유지하지 않는다.
- **주의·anti-drift:** estimator 비교는 vector와 full covariance로 하며 scalar amplitude overlap만 보고하지 않는다. correction과 data가 같으면 joint covariance가 필요하다.
- **검증·산출물:** independent constrained linear oracle, flow/monopole/calibration injections, per-column 68/95% coverage, partition/leverage mutations, dimensional/window tests, two P0 production-remediation candidate receipts.
- **Exit / kill:** rank deficiency 또는 preregistered bias/coverage 실패 시 P0는 open이고 point estimate를 내지 않는다. P0 폐쇄는 PR-157 adjudication 전에는 불가하다.
- **최대 claim:** observable-estimator mechanics C2.

### PR-146 — Correlated-flow, distance-error, selection/grouping E2E mocks

- **Owner / dependencies / cost:** `OBSSTAT`; PR-123, PR-135, PR-137, PR-144, PR-145; high.
- **Targets:** `C2-K5-MOCKSIG-F3/F5`, `C3-K5-VCORR-ML-F4/F5`, K5 catalogue mock/realization blocker. K6는 PR-123의 독립 branch 소유다.
- **실제로 할 것:** Hermitian GRF와 independent box/observer units, correlated flow, nonlinear variants, non-Gaussian distance error, indicator calibration, selection/Malmquist와 grouping을 포함하는 CF4 catalogue forward mocks를 만든다. every mock에서 estimator/nuisance를 재적합한다.
- **하지 말 것:** same-box octant를 independent mock으로 세거나 WF mean 하나를 posterior/CR ensemble로 사용하지 않는다. K6 numerical rescue를 CF4 catalogue authority에 다시 결속하지 않는다.
- **주의·anti-drift:** generator와 estimator가 같은 bug를 공유하지 않도록 independent reference를 사용한다. effective N와 covariance uncertainty를 보고한다.
- **검증·산출물:** generator component power/variance, mutation kill, per-depth simultaneous grid-conditional coverage, effective-N audit와 CF4 catalogue simulator card.
- **Exit / kill:** Hermitian/component variance, coverage 또는 release-selection match가 실패하면 rare-tail/significance claim을 생성하지 않는다.
- **최대 claim:** CF4 simulator/reconstruction-conditioned coverage C2.

### PR-147 — Nuisance-augmented CF4 identified sets

- **Owner / dependencies / cost:** `HTT`; PR-136, PR-137, PR-145, PR-146; high.
- **Targets:** `ST-04`, `N-DATA-CF4-DOWNSTREAM`, `C1-F2/F4/F5`, `C9-F3/F5`.
- **실제로 할 것:** monopole, calibration, distance convention, grouping, selection, reconstruction/window, nonlinear velocity nuisance를 declared set으로 묶는다. depth별 flow vector/amplitude/apex와 reconstruction compatibility를 bounded/empty/unbounded/nonidentified set으로 반환한다. common-window injected fields로 GLS/MV difference를 예측한다.
- **하지 말 것:** identified set에서 유리한 endpoint만 point estimate로 선택하거나 set이 0을 포함한다는 이유로 isotropy를 증명하지 않는다.
- **주의·anti-drift:** nuisance bounds와 depth grid는 observed result 전에 freeze한다. set topology 변화와 optimization uncertainty를 숨기지 않는다.
- **검증·산출물:** grid-conditional simultaneous coverage, mesh sensitivity, independent endpoint solver, depth/window sensitivity, machine-readable comparability table. class-wide uniformity는 PR-137의 continuity/mesh theorem이 있을 때만 표기한다.
- **Exit / kill:** coverage 실패 또는 plausible nuisance에서 unbounded면 그대로 보고하며 anomaly/global tilt claim을 중단한다.
- **최대 claim:** coverage-calibrated identified-region result C3.

### PR-148 — Depth-resolved `fσ8`와 same-data joint covariance bound

- **Owner / dependencies / cost:** `HTT`; PR-139--141, PR-147; high.
- **Targets:** `N-DATA-FS8-DEPTH`, 기존 `4.9σ` 및 growth/local-global downstream.
- **실제로 할 것:** frozen velocity observable/correction, depth/shell grid, comparator provenance와 same-data correlation을 명시한다. simultaneous depth coverage, shell stability, joint covariance 또는 defensible correlation bounds를 계산한다. estimator uncertainty와 theoretical comparator uncertainty를 분리한다.
- **하지 말 것:** shell-dependent bias를 하나의 weighted point로 숨기거나 correlation=0/1 endpoint를 선택해 원하는 sigma를 만들지 않는다. `4.9σ` 복구를 목표로 하지 않는다.
- **주의·anti-drift:** correction과 comparator가 같은 catalogue/mocks를 쓰면 cross-covariance가 필수다. depth cut 변경은 multiplicity family 변경이다.
- **검증·산출물:** joint simulation, covariance PSD/eigen diagnostics, simultaneous intervals, held-out depth prediction, identified growth-difference report.
- **Exit / kill:** covariance가 식별되지 않거나 depth instability가 preregistered limit을 넘으면 precision sigma 대신 bound/nonidentification을 보고한다.
- **최대 claim:** joint-covariance-conditioned growth difference bound C3; global tilt 없음.

### Checkpoint 095

두 P0는 PR-145 계산 성공만으로 닫지 않는다. PR-148 checkpoint에서 raw lineage, injection coverage, effective N, common-window, same-data covariance, stale consumer 수를 검토하고 non-author adjudication 대기 상태까지만 올린다.

## 12. Wave 19 — K1/Planck, DESI, ACT와 JWST provenance

### PR-149 — Planck/K1 canonical convention, mask와 transfer path

- **Owner / dependencies / cost:** `OBSSTAT`; PR-123, PR-125, PR-135, PR-143; medium--high.
- **Targets:** `N-DATA-K1-CONVENTION`, `C10-K1-JWST-F4/F5`, structural zero/trials 문제.
- **실제로 할 것:** observed/null map이 동일한 coordinate, alm indexing/phase/reality, beam/pixel/downgrade, mask, cut-sky feature, orientation/max scan을 통과하게 한다. TT BiPoSH odd-L diagonal structural zero와 monotone/equivalent scan을 quotient하고 effective family를 freeze한다.
- **하지 말 것:** hash만 기록하고 실제 map path에서 mask를 적용하지 않거나 hard-coded/stale Planck axis를 discovery 결과로 사용하지 않는다.
- **주의·anti-drift:** convention mutation이 observed/null 양쪽에 같이 들어가 self-consistency로 숨을 수 있으므로 independent alm/Wigner/rotation oracle가 필요하다. **이 카드가 mask/proc-nside/convention을 freeze하는 것이 PR-150의 PR3 raw 삭제 전제조건이다**(reduced-cache의 유일 재다운로드 trigger가 mask/proc-nside > 128 변경이므로, PR-149가 닫히기 전 PR3 raw를 삭제하지 않는다 — `docs/research_program/K1_E2E_REPRODUCIBILITY_RETENTION.md`).
- **검증·산출물:** alm reality/round-trip/rotation, arbitrary-real-alm structural zeros, mask/beam injections, observed/null path equality와 scan-family ledger.
- **Exit / kill:** canonical independent oracle와 coefficient/sign/order가 불일치하면 K1 statistic을 폐기한다. convention이 확정되기 전에는 PR-150의 raw-deletion swap을 승인하지 않는다.
- **최대 claim:** observable feature extraction/basis theorem C1--C2.

### PR-150 — K1 exchangeable global scan과 Planck E2E calibration

- **Owner / dependencies / cost:** `OBSSTAT`; PR-135, PR-149; high, E2E input에 따라 blocked.
- **Targets:** `N-STAT-K1-EXCHANGE`, `N-STAT-DEGENERATE-NULL`, `N-DATA-K1-STALE-DIRECTION`, `C10-F5`.
- **2026-07-15 사용자 지시의 명시적 supersession:** 원 카드의 PR3+PR4 joint 설계보다 이 문단이 우선한다. PR3/FFP10 E2E 다운로드는 완료 상태로 intake하되, PR4/NPIPE는 다운로드·size probe·intake·reduction·cache·데이터 분석을 전부 실행하지 않는다. 이 제한은 full-frequency, component-separated, single-channel, subset-stream, partial-range와 외부에서 이미 받은 payload까지 포함하며, 새 사용자 권한 없이는 재개하지 않는다.
- **SPEC:** estimand=exchangeable observation-inclusive pooled-rank global p under matched **PR3/FFP10 E2E null only**; support=Planck low-ℓ, PR-149 canonical mask/convention (frozen BEFORE any raw deletion); falsifier=super-uniform pooled rank fails on correlated GRF, OR observed/null pipeline is not byte-equivalent; ceiling=`roadmap_rescue_v1:C2` diagnostic-only. 원래의 joint PR3+PR4 C3 gate는 미충족/사용 불가다.
- **실제로 할 것:** 먼저 correlated idealised-GRF에서 pooled rank의 super-uniformity를 대규모 reduced simulation으로 확인한다. 그 뒤 다운로드가 완료된 PR3/FFP10 input manifest를 만들고 동일 mask/transfer/statistic/max scan을 E2E maps에 적용한다. fixed-axis와 re-estimated-axis/null multiplicity를 분리한다. PR3는 `scripts/k1_e2e_reduce.py`로 estimator-agnostic 캐시(Tier-2, NSIDE=128 float64 pre-mask 맵 + a_lm)로 줄이고 `scripts/k1_e2e_cache_gate.py`가 GREEN(safe_to_delete_raw, bit-exact 재현 + raw hash 일치)일 때만 raw 삭제한다. subagent 단계(§4.5): 3 `research-code-task`(reduce/gate 운용) → 5 `numerical-validation`(faithful-cache) → 7 `reproducibility-closeout`(retention receipt).
- **하지 말 것:** idealised GRF success를 Planck systematics calibration으로 승격하거나 E2E ensemble이 없는 상태에서 real-sky p-value를 내지 않는다. faithful-cache gate가 RED인데 PR3 raw를 삭제하지 않는다. PR4/NPIPE 명령, 수치, 표, 그림, p-value, method comparison 또는 PR3+PR4 결합 결과를 만들지 않는다. PR4에 허용되는 유일한 산출물은 비수치 `SKIPPED_BY_USER_SCOPE` receipt다.
- **주의·anti-drift:** PR4 부재를 optional cross-check 완료나 joint calibration으로 재해석하지 않는다. PR4 systematics-sensitivity 질문은 `BLOCKED`/미판정으로 남긴다. PR-149 mask/convention을 PR3 raw 삭제 전에 freeze하고 axis pre-specification과 data reuse를 기록한다.
- **검증·산출물:** PR3 input license/hash manifest, data/null byte-equivalent runner, finite-rank intervals, method-wise/global scan, type-I/power report, Tier-1 receipt(`docs/generated/k1_e2e_reduced_manifest_*.json`, committed), Tier-2 캐시(NVMe 잔존), faithful-cache gate receipt, 비수치 PR4 skip receipt.
- **Exit / kill:** PR3 E2E input/support가 없거나 observed/null path가 다르면 science state는 `BLOCKED`; idealised non-anomaly만 유지한다. PR3 raw는 gate GREEN 전 삭제 금지다. 어떤 PR4/NPIPE 데이터 명령이나 파생 수치가 실행되면 이 카드의 실행은 실패다.
- **최대 claim:** PR3/FFP10-E2E-conditional morphology diagnostic `roadmap_rescue_v1:C2`; PR4 systematics comparison, family/axis detection, joint C3 없음.

### PR-151 — DESI exact-selection mock와 per-mock refit

- **Owner / dependencies / cost:** `OBSSTAT`; PR-134, PR-135, PR-143; high.
- **Targets:** `N-DATA-DESI-READINESS`, `C4-EXT-DESI-F1`--`F7`.
- **실제로 할 것:** estimator의 `nz`, quadrature, lmax/mask leakage, NGC/SGC cap과 raw/corrected ratio를 repair한다. every mock에서 alpha와 nuisance를 재적합한다. official release/selection/window/randoms에 맞는 mock manifest를 만든 뒤 fast covariance tier와 high-realism validation tier를 분리한다. clustering, kinematic, selection/systematics injections을 동일 estimator로 비교한다.
- **하지 말 것:** hard-coded cap ratio, fixed-alpha mocks, generic GRF만으로 “clustering-dominated” causal attribution을 주장하지 않는다.
- **주의·anti-drift:** 현재 official DESI DR1 문서는 1000 EZmocks와 25 AbacusSummit validation mocks를 제공한다고 명시한다. 이 가용성은 estimator support를 자동 보장하지 않으므로 exact selection/weights/window match를 먼저 확인한다. [DESI DR1 docs](https://data.desi.lbl.gov/doc/releases/dr1/)
- **검증·산출물:** convergence curves, per-mock refit receipt, exact finite ranks, two-tier covariance/validation, cap-wise source-derived ratios와 component confusion matrix.
- **Exit / kill:** exact-support mock/selection이 없거나 causal components가 분리되지 않으면 survey-conditional null까지만 보고하고 attribution을 abandon한다.
- **최대 claim:** DESI-survey-conditional estimator/null result C3.

### PR-152 — ACT raw-QE acquisition gate와 release-simulation cross-fit

- **Owner / dependencies / cost:** `OBSSTAT`; PR-135, PR-143; medium if no-go, high if upstream inputs exist.
- **Targets:** `N-DATA-ACT-RANGE`, `C5-EXT-ACT-F1`--`F6`.
- **실제로 할 것:** release simulation에서는 leave-one-simulation/cross-fit mean field, exact finite rank, stochastic/fixed-template injection-law 구분, residual mean과 rounding uncertainty를 repair한다. 별도로 filtered maps/QE inputs, mask/filter, response, mean field, N0/N1, validated multipole range를 authenticated inventory로 조사한다.
- **하지 말 것:** released kappa alm에 signal을 더한 것을 pre-QE transfer라고 부르거나 input 부재에서 `L=2..10` sky-power limit을 계산하지 않는다.
- **주의·anti-drift:** [ACT DR6 official products](https://act.princeton.edu/act-dr6-data-products)가 공개되어 있어도 필요한 upstream QE 단계가 포함되는지는 별도 확인해야 한다. release-product diagnostic과 raw-QE inference를 분리한다.
- **검증·산출물:** cross-fit delta-p/MC resolution, injection coverage, product/range manifest, upstream availability decision. 입력이 있으면 mask→QE→response→mean-field→N0/N1 E2E injection을 추가한다.
- **Exit / kill:** 충분히 upstream input이 없으면 `ABANDON_CURRENT_DATASET_FOR_NATIVE_LOW_L_SKY_POWER`; release-simulation diagnostic만 닫는다.
- **최대 claim:** release conditional diagnostic C2, 또는 완전 E2E 통과 시 ACT-pipeline-conditioned measurement C3.

### PR-153 — JWST authenticated row, crossmatch와 calibration manifest

- **Owner / dependencies / cost:** `OBSSTAT`; PR-122, PR-134, PR-143; medium--high, source availability에 따라 blocked.
- **Targets:** `N-DATA-JWST-ACQUISITION`, `N-DATA-JWST-CROSSMATCH`, `C10-K1-JWST-F1/F2`.
- **실제로 할 것:** anchor별 authoritative URL/dataset ID, retrieval time/hash/license, object/host IDs와 aliases, coordinate/redshift evidence, original uncertainty, method/calibration group, deterministic transform을 row-complete manifest로 만든다. probabilistic identity match, ambiguity와 duplicate policy를 구현한다.
- **하지 말 것:** coordinate radius 하나만으로 identity를 확정하거나 synthetic 14-anchor fixture를 observed JWST data로 이름 바꾸지 않는다.
- **주의·anti-drift:** source row가 수정되면 dataset identity와 forecast를 새로 생성한다. prior, anchor count/fraction, covariance endpoint를 서로 교환하지 않는다.
- **검증·산출물:** independent row replay, crossmatch probability/tolerance sensitivity, leave-one-match/group report, label-substitution negative test.
- **Exit / kill:** authoritative row/identity/uncertainty를 재현하지 못하면 JWST lane은 `synthetic scenario`로 유지한다.
- **최대 claim:** authenticated anchor dataset C1.

### Checkpoint 100

PR-153 완료 후 총 100 checkpoint를 실행한다. Planck E2E, DESI exact support, ACT upstream QE, JWST row authority의 `available/blocked/no-go`를 각각 기록한다. 공개 입력이 있다는 사실과 현재 estimator에 필요한 exact input이 있다는 사실을 구분한다.

## 13. Wave 20 — Hierarchical forecast, cross-survey 식별, adjudication와 논문

### PR-154 — JWST hierarchical covariance forecast

- **Owner / dependencies / cost:** `HTT`; PR-138, PR-139, PR-153; high.
- **Targets:** `N-DATA-JWST-WEIGHTING`, `N-DATA-JWST-COVARIANCE`, `C10-F1/F3`.
- **실제로 할 것:** per-host measurement, host latent, zero-point, method/calibration group와 CF4 overlap covariance를 계층 모델에 넣는다. probabilistic match를 marginalize하고 leave-host/group-out, SBC, PPC와 forecast coverage를 수행한다.
- **하지 말 것:** 모든 row uncertainty를 global 1/3로 줄이거나 gain이 작다는 이유로 shared covariance를 제거하지 않는다.
- **주의·anti-drift:** forecast input과 prior를 endpoint 결과 후 변경하면 새 scenario다. synthetic과 authenticated rows를 합쳐 하나의 observed forecast로 부르지 않는다.
- **검증·산출물:** hierarchical simulation recovery, calibration-group deletion, match uncertainty propagation, held-out predictive score와 scenario table.
- **Exit / kill:** leave-group instability, failed coverage/PPC 또는 gain 소멸을 숨기지 않고 null/no-gain forecast로 보고한다.
- **최대 claim:** provenance/covariance-conditional forecast C3.

### PR-155 — Cross-survey direction negative controls와 joint covariance

- **Owner / dependencies / cost:** `HTT`; contributor `OBSSTAT`; PR-148, PR-150--154; high.
- **Targets:** `DA-07`, `N-DATA-K1-STALE-DIRECTION`, cross-probe independent-confirmation 위험.
- **실제로 할 것:** rotation, antipode, depth reversal, mask perturbation, cap/survey split, calibration deletion과 fixed/pre-estimated/re-estimated axis를 preregister한다. shared sky/foreground/selection/calibration/data overlap의 joint covariance 또는 conservative bound를 계산한다.
- **하지 말 것:** dependent p-values를 곱하거나 동일 Planck/CF4 information을 독립 confirmation으로 센다. failed/blocked lane을 joint score에 0으로 채우지 않는다.
- **주의·anti-drift:** negative control이 본 방향과 비슷한 coherence를 보이면 결과는 systematics/non-identification이다.
- **검증·산출물:** control matrix, direction uncertainty geometry, covariance decomposition, missing-sector artifact와 multiplicity correction.
- **Exit / kill:** joint covariance가 식별되지 않거나 negative-control distribution과 분리되지 않으면 coherence/shared-cause claim을 중단한다.
- **최대 claim:** diagnostic cross-survey falsification C2--C3.

### PR-156 — Multi-probe response-rank와 held-out local/global/systematics injection

- **Owner / dependencies / cost:** `HTT`; PR-133, PR-141, PR-143, PR-155; high.
- **Targets:** `ST-07`, `TH-03/04` pre-native use, local/global discrimination 장기 rescue.
- **실제로 할 것:** 통과한 lane만 사용해 local boost, global candidate, survey/systematic, isotropy response uncertainty를 nuisance projection 후 평가한다. blind held-out injections에서 rank interval, confusion, abstention, predictive gain과 prior sensitivity를 계산한다.
- **하지 말 것:** full-rank point estimate 하나로 식별을 선언하거나 shared latent cause를 Bianchi geometry로 이름 붙이지 않는다.
- **주의·anti-drift:** blocked lane은 zero response로 대체하지 않는다. response provider/transfer가 바뀌면 challenge를 재동결한다.
- **검증·산출물:** sealed injection bank, confusion/coverage/abstention surface, held-out score, response principal-angle/rank report.
- **Exit / kill:** plausible nuisance에서 rank가 사라지거나 PPC/LOO/null/prior gate 하나라도 실패하면 `abstain/non_identified`다.
- **최대 claim:** pre-solver local/global discrimination candidate C3.

### PR-157 — Pre-solver independent finding adjudication

- **Owner / dependencies / cost:** `COMMON`; non-author panel은 `adjudicator`; dependencies `PR-143, PR-144, PR-145, PR-146, PR-147, PR-148, PR-149, PR-150, PR-151, PR-152, PR-153, PR-154, PR-155, PR-156`; medium.
- **Targets:** 102-row matrix 중 literal rescue, corrected supersession, falsified/blocked/abandoned의 권위 갱신.
- **실제로 할 것:** PR-143--156 각각에서 `COMPLETED_SUCCESS | COMPLETED_FAILED_WITH_RECEIPT | BLOCKED_WITH_RECEIPT | ABANDONED_WITH_RECEIPT` terminal receipt를 수집하는 deterministic aggregation을 만든다. raw production receipts만 사용해 identity diff, falsifier, independent oracle, coverage/proof/domain, all-consumer freshness를 판정한다. literal rescue와 새 claim을 분리하고 반대의견을 보존한다.
- **하지 말 것:** PR author/후보 생성자가 자신의 상태를 승인하거나 methods score를 evidence로 사용하지 않는다. 미완료 lane을 bulk close하지 않는다.
- **주의·anti-drift:** 역사적 finding/source는 immutable하다. disposition 변경은 new adjudication record와 source hash로만 한다.
- **검증·산출물:** updated authoritative matrix, before/after counts generated from JSON, disputed rows, stale consumer scan, adjudicator prompt/response receipts.
- **Exit / kill:** PR-143--156 중 terminal receipt가 하나라도 없거나 identity/provenance/consumer 중 하나라도 불완전하면 해당 lane은 미판정 또는 `downclaimed/rebuild_required/blocked`로 유지한다. blocked/abandoned receipt는 aggregation을 끝내지만 rescue 표가 될 수 없다.
- **최대 claim:** adjudicated evidence state; 자체 과학 claim 없음.

### PR-158 — 검증된 claim만 사용하는 methods/negative-audit manuscript rebuild

- **Owner / dependencies / cost:** `COMMON`; contributors는 manuscript maintainers와 lane owners; PR-157; high.
- **Targets:** as-shipped REJECT를 positive headline 수정이 아닌 새 방어 가능한 thesis로 전환.
- **실제로 할 것:** methods/non-identification/conditional theorem/numerical upper bound/finite-null/identified-set 결과 중 PR-157에서 승인된 것만 manuscript와 figures에 생성한다. 모든 숫자는 generated source, 모든 figure는 manifest, 모든 blocked/no-go는 명시한다. clean LaTeX/PDF visual review와 digest-blind external-style review를 수행한다.
- **하지 말 것:** rescue 수를 늘려 narrative를 긍정적으로 만들거나 audit/governance figure를 science result figure로 채우지 않는다. open P0, family, geometry, native transfer, global-tilt detection headline을 넣지 않는다.
- **주의·anti-drift:** report-facing figure는 bound data/analysis를 보여야 하며 internal gates는 appendix로 제한한다. post-surgery score는 readiness 증거가 아니다.
- **검증·산출물:** generated claim/table/figure sources, provenance/freshness, claim/transfer lint, clean TeX build, rendered PDF inspection, independent referee decisions와 release manifest.
- **Exit / kill:** current authoritative ledger보다 강한 문구, manual number, stale figure, invalid manifest 또는 unresolved P0 consumer가 있으면 publication freeze를 reject한다.
- **최대 claim:** 실제 승인 결과에 따른 methods/negative-audit paper; pre-native family/geometry 없음.

### Checkpoint 105

PR-158 후 pre-solver program을 종료하거나 새 근거로 replan한다. 완료 수보다 literal rescue, corrected-superseded, falsified, blocked 수와 strongest defensible thesis를 보고한다. positive result가 없더라도 complete research outcome으로 인정한다.

## 14. Wave 21+ — Native solver/atlas 도착 후에만 활성화

PR-159--166은 현재 `DORMANT_BLOCKED_EXTERNAL`. 다만 external delivery가 pre-solver manuscript보다 먼저 도착하면 read-only authenticity freeze인 PR-159는 PR-122/124/125 substrate 위에서 숫자 순서를 건너뛰어 즉시 활성화할 수 있다. 이는 atlas science 소비를 여는 것이 아니다. PR-160 이후는 각 명시 dependency와 conformance gate를 별도로 충족해야 한다. native low-ell solver를 이 저장소에서 구현하거나 toy/external proxy로 activation trigger를 흉내 내지 않는다.

### PR-159 — Authenticated native-delivery intake

- **Owner / dependencies / cost:** `BASS`; implementation scope `bass_py`; PR-122, PR-124, PR-125와 authenticated external delivery event; blocked until delivery.
- **실제로 할 것:** producer identity/version/license, source/build/config hash, coefficient conventions, frame/units, parameter domain, output schema, test vectors와 rejection behavior를 검증한다. read-only immutable intake snapshot과 delivery receipt를 만든다.
- **하지 말 것:** 이름이나 파일 layout만 보고 native라고 승인하거나 AniCLASS/external/proxy를 native alias로 등록하지 않는다.
- **주의·anti-drift:** delivery update는 새 version이며 old/new output을 섞지 않는다. conformance와 physics validation을 분리한다.
- **검증·산출물:** authenticity/checksum, schema rejection fixtures, FLRW/no-tilt/domain boundary examples, native-source registry.
- **Exit / kill:** authenticity, convention 또는 version을 독립 확인할 수 없으면 PR-160--166을 계속 dormant로 둔다.
- **최대 claim:** authenticated delivery intake C1.

### PR-160 — Producer/consumer transport conformance와 closure rejection challenge

- **Owner / dependencies / cost:** `BASS`; implementation scope `bass_py`; PR-159, PR-121--125, PR-133; high.
- **실제로 할 것:** adapter round-trip, units/frame/harmonic indexing, parameter rejection, conservation/constraint residual, deterministic replay와 convergence metadata를 검증한다. legacy memory-kernel/Teff 아이디어는 causality, passivity, stability, reflection, phase와 observable-bias 기준을 가진 optional rejection challenge로만 비교한다.
- **하지 말 것:** adapter conformance를 physical correctness라고 부르거나 closure가 native reference를 대체하게 하지 않는다. TSC/Teff active owner를 복구하지 않는다.
- **주의·anti-drift:** native producer와 adapter가 같은 bug를 공유할 수 있어 external test vectors와 independent limit이 필요하다.
- **검증·산출물:** conformance corpus, rejected malformed/out-of-domain inputs, FLRW and known-limit comparisons, closure pass/fail/no-go report.
- **Exit / kill:** unit/frame/index mismatch, nondeterministic replay 또는 constraint failure가 하나라도 있으면 native output ingestion을 block한다.
- **최대 claim:** native transport/adapter conformance C2.

### PR-161 — Atlas convergence, interpolation, versioning와 held-out samples

- **Owner / dependencies / cost:** `BASS`; implementation scope `bass_py|canonical_BASS`; PR-127, PR-133, PR-160; high.
- **실제로 할 것:** native T/E/B mean/covariance/morphology atlas의 grid density, interpolation error, solver tolerance, parameter/orientation/handedness/version metadata와 held-out solver samples를 검증한다. PR-127의 ambient/constraint-admissible 분리와 PR-133의 source-response/admissibility ladder를 소비해 family/orientation/limiting-case group action과 equivalence annotation을 versioned schema에 넣는다.
- **하지 말 것:** nearest atlas entry 또는 interpolation central value를 family identification으로 사용하지 않는다.
- **주의·anti-drift:** atlas update는 모든 downstream feature/likelihood를 invalidate한다. interpolation uncertainty를 observational covariance에 몰래 흡수하지 않는다.
- **검증·산출물:** held-out interpolation coverage, solver-tolerance convergence, boundary/limiting family fixtures, versioned equivalence registry.
- **Exit / kill:** interpolation/solver error가 morphology separation보다 크거나 equivalence annotation이 불완전하면 inference PR을 block한다.
- **최대 claim:** native atlas numerical validation C3--C4.

### PR-162 — Matched-mask/null/covariance native morphology features

- **Owner / dependencies / cost:** `OBSSTAT`; PR-150, PR-155, PR-161; high.
- **실제로 할 것:** observed map, native injections와 null/systematic simulations를 같은 mask/beam/pixel/filter/alm/template/BiPoSH/covariance/maximization pipeline에 통과시킨다. interpolation/solver/foreground/instrument covariance를 분리한다.
- **하지 말 것:** full-sky atlas와 cut-sky observation을 직접 비교하거나 scalar feature 한 개로 family를 rank하지 않는다.
- **주의·anti-drift:** feature/scan/mask 선택은 held-out challenge 전에 freeze한다. deterministic mean와 covariance morphology branch를 유지한다.
- **검증·산출물:** held-out injection recovery, matched-null size, feature rank/conditioning, mask/foreground/systematic negative controls.
- **Exit / kill:** size/coverage/rank가 실패하면 morphology compatibility claim을 내지 않는다.
- **최대 claim:** matched-pipeline morphology feature validation C4--C5.

### PR-163 — Blinded morphology-equivalence challenge

- **Owner / dependencies / cost:** `COMMON`; challenge designer/analyst/adjudicator는 서로 다른 principals; PR-127, PR-133, PR-161, PR-162; high.
- **실제로 할 것:** training/validation/held-out native atlas entries, equivalent/near-equivalent families, nuisance/systematics와 null을 sealed challenge로 구성한다. analyst는 label을 보지 않고 equivalence set, uncertainty와 abstention을 제출한다.
- **하지 말 것:** best-fit single label accuracy만 최적화하거나 equivalent family를 오답으로 센 뒤 arbitrary tie-break를 만들지 않는다.
- **주의·anti-drift:** challenge designer/analyst/adjudicator를 분리한다. 실패 후 held-out set을 training에 넣으면 new challenge version이다.
- **검증·산출물:** equivalence-aware coverage/confusion/abstention, hidden-label receipts, nuisance robustness와 external referee report.
- **Exit / kill:** family-equivalence coverage 또는 null/systematic rejection이 실패하면 C5 이상 승격을 중단한다.
- **최대 claim:** blinded morphology-equivalence compatibility C5.

### Checkpoint 110

PR-163 후 총 110 checkpoint를 실행한다. native delivery authenticity, conformance, atlas convergence, matched-null size와 equivalence-set coverage를 별도 열로 기록한다. 어느 하나라도 실패하면 PR-164--166을 진행하지 않는다.

### PR-164 — HTT set-valued equivalence inference와 mandatory abstention

- **Owner / dependencies / cost:** `HTT`; PR-140--143, PR-163; high.
- **실제로 할 것:** native-atlas likelihood, normalized priors, interpolation/systematic nuisance, PPC, dependency-aware holdout와 equivalence-aware identified set을 결합한다. output은 single winner가 아니라 compatible equivalence set, excluded set, unidentified directions와 abstention이다.
- **하지 말 것:** MIO diagnostic을 likelihood에 넣거나 scalar/Bayes-factor 최고값을 family identified로 바꾸지 않는다.
- **주의·anti-drift:** prior, family universe와 equivalence policy를 unblinding 전에 freeze한다. family list 변경은 새 analysis다.
- **검증·산출물:** prior sensitivity, evidence-engine agreement, PPC/holdout, held-out set coverage, mandatory-abstention tests.
- **Exit / kill:** predictive gain/coverage/equivalence separation 중 하나라도 실패하면 compatibility set 또는 abstention에 머문다.
- **최대 claim:** native-atlas-conditioned morphology compatibility set C5.

### PR-165 — 외부 독립 validation과 family-identification gate 심사

- **Owner / dependencies / cost:** `COMMON`; repository author가 아닌 external/domain panel은 `adjudicator`; PR-164; high/external.
- **실제로 할 것:** raw native inputs, independent implementation/solver samples, matched pipelines와 complete receipts를 외부 심사에 제공한다. frame/domain/atlas/null/mask/covariance/equivalence/trials/PPC/holdout/independence gate를 각각 판정한다.
- **하지 말 것:** 내부 multi-agent agreement를 external replication이라 부르거나 하나의 failed gate를 다른 강한 score로 상쇄하지 않는다.
- **주의·anti-drift:** 외부 reviewer의 dissent와 blocked asset을 그대로 보존한다. family-ID gate는 conjunctive하다.
- **검증·산출물:** independent reproduction or explicit non-reproduction, gate matrix, dissent, raw command/data receipts와 signed decision.
- **Exit / kill:** 모든 gate가 통과하지 않으면 family identification program을 열지 않고 C5 compatibility/abstention을 유지한다.
- **최대 claim:** gate adjudication; 통과 전 family identification 없음.

### PR-166 — Post-native publication adjudication

- **Owner / dependencies / cost:** `COMMON`; contributors는 manuscript maintainers, external panel은 `adjudicator`; PR-165; medium--high.
- **실제로 할 것:** PR-165 판정에 따라 morphology-compatibility, non-identification 또는 별도의 family-identification review-ready claim만 생성한다. atlas/version/mask/null/covariance/equivalence/holdout provenance를 모든 숫자·그림에 결속한다.
- **하지 말 것:** PR-165가 reject/blocked인데 wording만 약하게 바꿔 family result를 남기지 않는다.
- **주의·anti-drift:** native version이나 atlas 변경 시 publication freeze를 invalidate한다.
- **검증·산출물:** full package reproduction, claim/transfer/family lint, clean PDF render, external reviewer response와 final manifest.
- **Exit / kill:** provenance/figure/family gate 불일치가 있으면 release를 reject한다.
- **최대 claim:** PR-165가 실제 승인한 범위. 기본값은 C5 morphology compatibility 또는 abstention이다.

## 14b. Wave 22--27 — Advocate divergence track (net-new, spec-driven + subagent-driven)

이 구간은 advocate divergence 탐색(commit `a56451c`)의 **genuinely net-new 16개 후보**를 원 DAG에
편입한 것이다. 원 119--166이 감사 결함을 순서대로 고치는 remediation이라면, 여기는 감사가 유일하게
방어 가능하다고 인정한 "반증 가능한 연구 프로그램"을 roadmap에 없는 net-new 관측·정리로 채운다.
모든 카드는 §4.5의 spec-driven(구현 전 SPEC/decisive-falsifier 확정) + 단계별 subagent-driven으로
실행하고, 32/48 frozen set과 비겹침(각 후보의 `non_overlap_justification`은 dev-tier ledger에
있음). final CRAG가 novelty를 정직하게 INCREMENTAL/CONFIRMATORY로 낮췄으므로(NEW 0건) 어떤 카드도
"first"를 주장하지 않는다 — 가치는 rescue leverage + cross-axis + honest non-overlap이다.
family-ID/geometry 계열(PR-174,175,182,183)은 전부 `hypothesis_only`, pre-native 승격 금지.
두 CF4 P0는 여전히 open이며 이 track은 P0 *주위*에 net-new를 짓는 것이지 P0를 덮지 않는다.

우선 실행은 방법론이 아니라 **PR-168**(순수 code-integrity + 이론 정직성, 최저 위험) 한 장이다.
gate-off 카드는 §14b 마지막 registry(PR-182/183)로 격리하고, 나머지는 defensible track이다.

### Wave 22 — Advocate intake와 실행계약

#### PR-167 — Advocate divergence intake + spec/subagent 실행계약 + gate-off quarantine

- **Owner / dependencies / cost:** `COMMON`; PR-119; low.
- **Targets:** advocate ledger의 16 net-new + 5 reclassified 후보를 backlog에 편입, §4.5 실행계약 배선, gate-off 후보의 hypothesis_only quarantine.
- **SPEC:** claim=`advocate track의 DAG 편입은 orchestration/ledger 정합성 문제이며 과학 rescue가 아니다`; 인터페이스=PR-167--183 카드 + `superseded/extends` crosswalk; falsifier=어떤 gate-off 후보라도 production/manuscript/public consumer에 도달하면 실패; ceiling=C1.
- **실제로 할 것:** subagent 단계(1 spec `research-contract` → 2 `htt-revision-planner` crosswalk → 6 `independent-diff-review` → 7 `reproducibility-closeout`). PR-167--183을 양쪽 mirror에 `pending`으로만 등록하고 과학 state는 바꾸지 않는다. 5개 reclassified 후보(§14b 표)는 frozen PR의 `extends` edge로만 등록한다. gate-off 후보(PR-174/175/182/183)에 `hypothesis_only`·`public_use=false` lint gate를 건다.
- **하지 말 것:** advocate 후보를 backlog에 넣었다는 이유로 `IN_REMEDIATION` 이상으로 올리지 않는다. reclassified 후보를 net-new PR로 승격하지 않는다.
- **주의·anti-drift:** advocate ledger는 dev-tier이며 immutable하다. §4.5 subagent 산출은 external replication이 아니다.
- **검증·산출물:** DAG validator(PR-119--183 unique), gate-off hypothesis_only lint, extends-crosswalk, `docs/PR_DELTAS/pr-167.md`.
- **Exit / kill:** 65개 원 상태 보존 + PR-167--183 dependency가 선행 ID만 가리키고 gate-off lint가 통과해야 한다. 하나라도 실패하면 advocate track 금지.
- **최대 claim:** orchestration/ledger correctness C1; 과학 rescue 없음.

### Wave 23 — Advocate 이론

#### PR-168 — MES four-acceleration honesty theorem + `bounds.py` 결함 수정

- **Owner / dependencies / cost:** `COMMON`; contributor `BASS`; PR-124, PR-167; low.
- **Targets:** advocate rank-1; `bounds.py`가 아직 shipping하는 반증된 in-house non-geodesic `B_accel=(3/4)e1+e2+(3/14)e3`(rev-r190 geodesic `A^2=0` 재채택과 모순); `C7-MES` 계열.
- **SPEC:** claim=`O(beta) four-acceleration T-dipole은 kinematic dipole과 spectrally degenerate이며 non-geodesic B_accel은 dead code다`; frame=geodesic, `(-,+,+,+)`; falsifier=O(beta) four-acceleration T-multipole kernel의 l-spectrum이 pure kinematic-dipole kernel에 비례하지 않는 독립 l>=2 구조를 가지면 degeneracy 반증(그러면 B_accel은 실관측량이고 삭제 금지); ceiling=C1.
- **실제로 할 것:** subagent(1 spec → 3 `research-code-task` 로 symbolic kernel + bounds.py 수정 → 4 `physics-math-validation`(sign/limit) → 6 `independent-diff-review` → 7 closeout). O(beta) four-acceleration T-multipole kernel을 유도하고 kinematic-dipole kernel과의 spectral degeneracy를 dual-engine으로 봉인. 확인되면 `bounds.py`의 non-geodesic `B_accel`을 삭제하고 all-consumer regeneration + stale scan.
- **하지 말 것:** degeneracy를 확인하기 전 bounds.py를 편집하지 않는다. B_accel 삭제를 새 관측 claim으로 포장하지 않는다.
- **주의·anti-drift:** frozen registry의 `W2_max`·geodesic 값은 byte-stable로 유지(successor 패턴). 이는 code-integrity + 정직성 gain이며 detection이 아니다.
- **검증·산출물:** dual-engine kernel seal, bounds.py before/after + consumer scan, manuscript reconciliation.
- **Exit / kill:** degeneracy가 반증되면 B_accel은 관측량으로 남고 삭제하지 않되 그 관측 claim은 별도 심사. 봉인 실패 시 bounds.py 미변경.
- **최대 claim:** geodesic-frame degeneracy 정리 + dead-code 삭제 C1.

#### PR-169 — Unsigned isotropy-leakage ceiling `M_max`와 Nilsson-class witnesses

- **Owner / dependencies / cost:** `COMMON`; contributors `HTT`,`BASS`; PR-126, PR-127, PR-167; medium.
- **Targets:** advocate rank-6; `N-THEORY-FLRW-CONVERSE`의 물리적 예화(감사가 x_C=0를 FLRW certificate로 오용한 상처).
- **SPEC:** claim=`x_C=Sigma^2-W^2+Omega_tilt+Omega_k의 W^2 부호(-) 때문에 x_C~0는 개별적으로 큰 Sigma^2,W^2와 양립 -> x_C~0는 FLRW/EGS certificate가 아니다`; object=unsigned ceiling M_max(=|Sigma^2|+|W^2|+...); falsifier=x_C~0이면서 개별 Sigma^2,W^2가 크고 M_max를 saturate하는 admissible Nilsson-class witness가 존재하지 않으면(M_max=0) x_C~0는 FLRW를 certify하고 claim 붕괴; ceiling=C2.
- **실제로 할 것:** subagent(1 spec → 3/4 symbolic witness 구성 + `scientific-validation` → 6 review). PR-127의 PSD-cone/ambient-carrier 위에서 saturating Nilsson-class witness를 constructive하게 구성. downclaim: 이는 Clarkson-Coley generalized-EGS acceleration loophole의 project-identity 적용(신정리 아님)임을 명시.
- **하지 말 것:** M_max를 isotropy 증명으로 해석하거나 signed 변수를 PSD projection으로 잘라 witness를 없애지 않는다.
- **주의·anti-drift:** transfer/mask가 response rank를 바꾸므로 witness의 admissibility(Gauss/momentum/positivity)를 verifier로 확인한다.
- **검증·산출물:** exact witness fixtures, admissibility verifier, all-consumer negative scan(x_C~0 -> FLRW 언어 제거).
- **Exit / kill:** witness가 admissibility를 통과하지 못하면 `algebraic_only`로만 남긴다.
- **최대 claim:** generalized-EGS 적용 conditional mathematics C2; FLRW certificate 없음.

#### PR-170 — Buchert covariant home + two-patch cancellation obstruction

- **Owner / dependencies / cost:** `COMMON`; contributor `BASS`; PR-124, PR-126, PR-167; medium--high.
- **Targets:** advocate rank-13; `N-THEORY-PROVENANCE-OWNERSHIP`("x_C는 in-house 구성물").
- **SPEC:** claim=`x_C의 shear sector가 Buchert/BMR averaging Q_D에 외부적으로-인정되는 covariant home을 갖는다: Omega_Q^(D)=-Q_D/(6H^2)=Sigma^2_std, 그리고 two-patch obstruction이 global backreaction~0 WITHOUT local isotropy를 물리적으로 예화`; falsifier=admissible한 어떤 구성도 local shear를 크게 유지한 채 global Q_D를 상쇄하지 못하면 obstruction/home claim 실패; ceiling=C2, downclaim(Q_D 내용은 표준 Buchert/Wiegand, Barrow-Tsagas가 이미 Bianchi 평균화).
- **실제로 할 것:** subagent(1 spec → 3/4 dual-engine SymPy+Wolfram으로 Omega_Q=Sigma^2 항등식 + two-patch obstruction 봉인). 외부 anchor(Buchert 2000, Wiegand-Buchert 2010, Barrow-Tsagas 2007)를 provenance로 명시. V-vs-VII_h `^3S_ab` 보정(V는 isotropic 3-curvature).
- **하지 말 것:** two-patch obstruction을 신정리로 부르거나 Q_D=Sigma^2를 새 물리로 팔지 않는다.
- **주의·anti-drift:** exact identity와 external-provenance bridge를 분리한다. spatially-constant expansion 가정을 명시.
- **검증·산출물:** dual-engine identity seal(11 type), two-patch witness, external-anchor provenance table.
- **Exit / kill:** identity가 어느 type에서 exact-rational로 닫히지 않으면 x_C는 Buchert home 없이 유지.
- **최대 claim:** provenance-hardened conditional identity C2.

#### PR-171 — Khronon / non-comoving dark-sector shear-leakage no-go ceiling

- **Owner / dependencies / cost:** `COMMON`; contributor `BASS`; PR-125, PR-167; medium.
- **Targets:** advocate rank-16; Omega_tilt의 microphysical source-space 축소(honesty envelope 강화).
- **SPEC:** claim=`momentum-conserving non-comoving dark fluid(Q^mu ∝ relative velocity, w_X<1/3, Gamma>=0)는 comoving으로 이완 -> generic fluid는 persistent tilt를 source할 수 없다; 가치는 surviving source가 넘어야 할 정량 suppression ceiling`; falsifier=그 fluid가 comoving으로 이완하지 않고 persistent tilt가 살아남으면 no-go 반증, 아니면 relaxation rate가 ceiling; ceiling=C2, hypothesis_only, downclaim(King-Ellis/Coley-Hervik-Lim의 tilt-decay가 선행).
- **실제로 할 것:** subagent(1 spec → 3/4 background relaxation ODE + 2x2 eigenvalue 안정성 symbolic). 정량 suppression ceiling(Pi_X/momentum-source < 10^-6..-7)을 산출. mechanism은 Coley-Hervik-Lim에 귀속, khronon dressing은 loophole로만.
- **하지 말 것:** no-go를 isotropy 증명으로 해석하거나 EoS 의존성을 숨기지 않는다.
- **주의·anti-drift:** tilt dynamics는 EoS·model 의존이므로 closure 가정을 명시.
- **검증·산출물:** 2x2 stability proof, ceiling number + closure assumptions, source-attribution table.
- **Exit / kill:** persistent tilt가 살아남으면 no-go 폐기.
- **최대 claim:** class-conditional source no-go + suppression ceiling C2(hypothesis_only).

### Wave 24 — Advocate oracle와 gates-off geometry substrate

#### PR-172 — Physics-invariant symmetry-transform metamorphic battery + B-parity MR

- **Owner / dependencies / cost:** `COMMON`; contributor `OBSSTAT`; PR-123, PR-167; medium. **extends** CO-04/PR-123(numerical-oracle lab)에 anisotropy-specific metamorphic 층을 더함.
- **Targets:** advocate rank-4; `N-CODE-FALSE-GREEN`, estimator frame/convention bug.
- **SPEC:** claim=`estimator는 물리 대칭이 요구하는 covariance를 만족해야 한다`; relations=rotation covariance, axis permutation, quadratic amplitude scaling, monopole projection(=hypothesis_only를 강제), discrete B-mode-parity MR; falsifier=변환 후 estimator 출력이 요구된 covariance를 어기거나 monopole projection이 nonzero anisotropy를 leak하면 frame/convention bug; ceiling=C1.
- **실제로 할 것:** subagent(1 spec → 3 `research-code-task`로 transform battery → 5 `numerical-validation` → 6 review). 기존 estimator에 pure-transform metamorphic relation을 씌우고 monopole-projection MR이 anisotropy leak을 차단하는지 확인.
- **하지 말 것:** metamorphic pass를 matched-data/null/covariance pass로 승격하지 않는다.
- **주의·anti-drift:** CO-04와의 delta(anisotropy-specific relations)를 명시; 같은 estimator를 두 번 평가한 것을 두 oracle로 세지 않는다.
- **검증·산출물:** metamorphic relation suite, monopole-leak negative test, CO-04 delta note.
- **Exit / kill:** 사전 등록한 대칭 위반이 살아남으면 해당 estimator를 blocked.
- **최대 claim:** estimator symmetry-consistency mechanics C1.

#### PR-173 — Monte-Carlo finite-ensemble error-budget certifier (fail-closed infra)

- **Owner / dependencies / cost:** `OBSSTAT`; contributor `COMMON`; PR-135, PR-167; low--medium.
- **Targets:** advocate rank-9; finite-null 해상도보다 작은 sigma/p 외삽(§18.3), DESI p_rank·CF4 injection RMSE·ACT band-power·fsigma8 MC·Pi(1) tail.
- **SPEC:** claim=`모든 stochastic headline은 MC-SE와 1/(N+1) p-resolution ceiling을 동반해야 하며 그 안이면 signal이 아니라 estimator noise다`; primitives=batch-means/jackknife MC-SE, seed-SEM, discrete p-interval; falsifier=어떤 headline의 central value가 자기 MC-SE 안에서 null과 겹치면 그 headline은 noise; ceiling=C1.
- **실제로 할 것:** subagent(1 spec → 3 wrapper → 5 `numerical-validation`). 기존 stochastic 출력을 감싸 fail-closed error-budget gate로 만들고 Essick-Farr 너머로 genericize.
- **하지 말 것:** MC-SE gate를 physical validation이라 부르지 않는다.
- **주의·anti-drift:** finite resolution 아래 값을 절대 외삽하지 않는다(§4.2).
- **검증·산출물:** per-headline MC-SE + resolution ceiling report, noise-flag negative tests.
- **Exit / kill:** gate가 어떤 shipped headline을 noise로 판정하면 그 headline을 downclaim.
- **최대 claim:** stochastic honesty infrastructure C1.

#### PR-174 — Exact real-space Sachs-Wolfe ray tracer (anisotropic background, gates-off)

- **Owner / dependencies / cost:** `COMMON`; contributor `BASS`; PR-167; medium. **gate_tier=gates_off_ambitious → hypothesis_only.**
- **Targets:** advocate rank-17; false-green이 요구하는 self-oracle-independent forward object(theory-g는 fail-closed, LoS는 FLRW Bessel).
- **SPEC:** claim=`SW-only 근사에서 anisotropic background를 통한 null-geodesic 적분이 closed-form parity/shear 예측과 일치한다`; scope=SW-only, **no-likelihood firewall**; falsifier=recovered T-quadrupole이 closed-form parity/shear 예측과 불일치하면 tracer 또는 analytic transfer 오류; ceiling=C1(hypothesis_only).
- **실제로 할 것:** subagent(1 spec → 3 legacy RK4 tracer 부활/적응 → 4/5 validation → 6 review). SW-only Delta T/T를 exact anisotropic background에서 적분, likelihood 절대 호출 금지 firewall.
- **하지 말 것:** likelihood/family/geometry claim을 붙이지 않는다. FLRW LoS Bessel 경로와 혼용하지 않는다.
- **주의·anti-drift:** hypothesis_only registry; production consumer 0.
- **검증·산출물:** SW-only tracer, closed-form parity/shear cross-check, no-likelihood firewall test.
- **Exit / kill:** cross-check 불일치 시 tracer/transfer 중 하나 blocked.
- **최대 claim:** SW-only forward mechanics C1(hypothesis_only).

#### PR-175 — Eleven-type tetrad geometry oracle from structure constants (gates-off)

- **Owner / dependencies / cost:** `COMMON`; contributor `BASS`; PR-124, PR-174, PR-167; medium. **gate_tier=gates_off_ambitious → hypothesis_only.**
- **Targets:** advocate rank-19; SW tracer의 covariant-geometry 짝(schema에 fit되지 않은 first-principles geometry check).
- **SPEC:** claim=`11 Bianchi type의 curvature/shear invariant를 structure constants로부터 두 독립 engine(symbolic + complex-step)으로 유도하고 external Buchert anchor와 일치시킨다`; falsifier=두 engine 불일치 또는 external anchor 불일치; ceiling=C2(hypothesis_only). NOTE: 기존 contracted-Bianchi falsifier는 tautology로 판명 -> external anchor + 독립 engine이 load-bearing.
- **실제로 할 것:** subagent(1 spec → 3 symbolic + complex-step 두 engine → 6 review). structure constants -> connection -> curvature/shear invariant, Buchert anchor 결속.
- **하지 말 것:** nearest atlas entry나 invariant 값을 family identification으로 쓰지 않는다.
- **주의·anti-drift:** 두 engine의 lineage 독립성을 receipt에 기록; tautological self-check 금지.
- **검증·산출물:** cross-engine invariant table, external-anchor agreement, lineage manifest.
- **Exit / kill:** engine/anchor 불일치 시 oracle blocked.
- **최대 claim:** cross-engine geometry mechanics C2(hypothesis_only).

### Wave 25 — Advocate data falsifiers

#### PR-176 — Tsagas div(v) → q-dipole cross-falsifier (ad-hoc closure 제거)

- **Owner / dependencies / cost:** `OBSSTAT`; contributors `BASS`,`HTT`; PR-133, PR-144, PR-167; medium.
- **Targets:** advocate rank-3; `N-THEORY-OMEGA-SEMANTICS`; `tilted_flrw.py`의 ad-hoc closure `Delta_q=(beta/9)(lambda_H/d)^3`(=이미 theta/H=beta·lambda_H/d를 대입한 형태), `divergence()`(velocity_field_curl.py)가 계산 후 폐기하는 theta.
- **SPEC:** estimand=`theta=div(v)`를 CF4/PV에서 직접 읽어 `Delta_q~(1/9)(lambda_H/lambda)^2(theta/H)` 형성, 세 데이터(CF4 div-v apex, SNe q-dipole apex, CMB low-l tilt axis)의 single-axis coherence; frame/units 명시; falsifier=결과 q-dipole apex가 SNe deceleration-dipole apex 및 CMB low-l tilt axis와 joint error 넘게 불일치하면 single-axis tilt dictionary 반증; depth-tomography로 local-boost((lambda_H/d)^3) vs global-tilt 판별; ceiling=C3(diagnostic, transfer 표기 필수).
- **실제로 할 것:** subagent(1 spec → 2 localize(divergence 경로) → 3 forward dictionary → 4/5 validation → 6 review). monopole-leak P0 면역(divergence는 dipole estimator와 다른 moment)임을 명시하고 SNe q-dipole은 독립 카탈로그.
- **하지 말 것:** div(v)와 bulk-flow dipole을 같은 estimand로 섞지 않는다. 두 dipole 재측정으로 축소하지 않는다.
- **주의·anti-drift:** coherence 결과를 보고 lambda/축을 조정하면 새 analysis. transfer/frame 명시.
- **검증·산출물:** theta=div(v) 측정, three-dataset apex table, depth-tomography law fit, joint-error covariance.
- **Exit / kill:** near-rigid translation(theta/H << v/(H·lambda))이면 channel은 |B| 이상 정보 없음 -> `non_informative`.
- **최대 claim:** cross-dataset tilt falsifier diagnostic C3.

#### PR-177 — Validated-band ACT DR6 κ anisotropic-modulation transfer (40<L<763)

- **Owner / dependencies / cost:** `OBSSTAT`; PR-152, PR-167; medium.
- **Targets:** advocate rank-8; shipped ACT read가 `ELL_MIN,ELL_MAX=2,10`으로 validated band(Qu et al. 40<L<763) 완전 밖.
- **SPEC:** estimand=validated band 내 quadrupolar off-diagonal kappa coupling; support=40<L<763; falsifier=in-band modulation amplitude가 certified MC floor에서 zero와 consistent면 anisotropic modulation 없음, mask-leakage에 귀속되지 않는 nonzero coupling이면 검출; ceiling=C3(diagnostic).
- **실제로 할 것:** subagent(1 spec → 3 in-band off-diagonal estimator → 5 numerical → 6 review). 기존 out-of-band 2,10 hardcode를 in-band modulation 측정으로 대체, mask-leakage negative control.
- **하지 말 것:** out-of-band low-L read를 유지하거나 mask leakage를 modulation으로 세지 않는다.
- **주의·anti-drift:** feature/scan은 결과 전 freeze; validated range 밖 외삽 금지.
- **검증·산출물:** in-band coupling + MC floor(PR-173), mask-leakage negative control.
- **Exit / kill:** MC floor에서 zero-consistent면 null; band 밖 요구 시 abandon.
- **최대 claim:** validated-band modulation diagnostic C3.

#### PR-178 — DESI number-count dipole redshift tomography

- **Owner / dependencies / cost:** `OBSSTAT`; PR-151, PR-167; medium.
- **Targets:** advocate rank-11; shipped single all-sky `number_count_dipole`(z_shell 경로 없음).
- **SPEC:** estimand=per-z-shell dipole 방향·진폭; falsifier=kinematic dipole은 방향 z-independent(진폭만 evolution-scaled)인데 clustering/window dipole은 z-변화 -> z-shell로 방향이 변하면 pure-kinematic 반증; reconstruction-free, mock-free; ceiling=C3(diagnostic).
- **실제로 할 것:** subagent(1 spec → 3 z-shell split estimator → 5 numerical → 6 review). survey 자체의 redshift leverage 사용(absent exact-selection mock 회피).
- **하지 말 것:** window/selection dipole을 kinematic으로 귀속하거나 부재 mock을 fabricate하지 않는다.
- **주의·anti-drift:** shell 경계·estimator를 결과 전 freeze.
- **검증·산출물:** per-shell dipole table + direction stability test.
- **Exit / kill:** window-dominated로 판명되면 diagnostic null.
- **최대 claim:** z-tomography kinematic-vs-clustering diagnostic C3.

#### PR-179 — Reconstruction-independent directional cosmography {H(n̂), q(n̂)} (raw CF4)

- **Owner / dependencies / cost:** `OBSSTAT`; contributor `HTT`; PR-144, PR-167; medium.
- **Targets:** advocate rank-20; P0 `C1-K5-MV`(disputed reconstruction + monopole)를 구성상 우회(재구성 없음).
- **SPEC:** estimand=raw `(mu,z,n̂)`에 직접 fit한 Heinesen multipole Hubble law `{H(n̂),q(n̂)}`; falsifier=`H(n̂)/q(n̂)`의 dipole이 MC floor에서 zero와 불일치하면 directional anisotropy, consistent면 reconstruction-independent 상한; ceiling=C3(diagnostic). downclaim: 방법은 ALREADY_KNOWN(Heinesen), reconstruction-free 적용이 distinct move.
- **실제로 할 것:** subagent(1 spec → 3 multipole Hubble fit on raw catalogue → 5 numerical → 6 review). reconstruction/monopole 처리 부재를 명시.
- **하지 말 것:** 재구성 field를 끌어들이거나 P0 estimator를 재사용하지 않는다.
- **주의·anti-drift:** raw distance-modulus systematics를 명시; mask/selection leakage caveat.
- **검증·산출물:** {H(n̂),q(n̂)} multipole fit + MC floor, raw-systematics disclosure.
- **Exit / kill:** dipole이 MC floor 안이면 reconstruction-independent upper bound로만 보고.
- **최대 claim:** reconstruction-free directional cosmography diagnostic C3.

### Wave 26 — Advocate 통계

#### PR-180 — Exact zero-parameter boost-BipoSH residual excitation vector

- **Owner / dependencies / cost:** `OBSSTAT`; contributor `HTT`; PR-134, PR-149, PR-167; medium.
- **Targets:** advocate rank-14; `N-DATA-K1-CONVENTION`, `N-DATA-PLANCK-MASK`; 감사의 "correlated self-oracle" 상처를 method로 전환.
- **SPEC:** estimand=measured dipole beta로 완전히 고정된(zero free parameter) aberration+Doppler L=1 BipoSH kernel의 residual excitation vector; support=canonical alm/BipoSH convention + recorded `fsky=0.788737` mask; falsifier=exact subtraction 후 살아남는 L=1 excitation은 non-kinematic residual, zero residual이면 pure boost 확인; ceiling=C3(diagnostic, 'geometric estimand' 라벨 제거).
- **실제로 할 것:** subagent(1 spec → 3 deterministic kernel(fit 아님) → 6 review). exact boost를 analytically pre-whiten하여 잔여 survey-direction test의 통계적 독립성 회복(cross-pollination CP-boost-restores-independence).
- **하지 말 것:** kernel을 fit하거나 residual을 geometric estimand로 부르지 않는다.
- **주의·anti-drift:** deterministic template과 stochastic covariance branch 분리(§18.1).
- **검증·산출물:** zero-parameter kernel + masked residual, independence-restoration test.
- **Exit / kill:** residual이 MC floor(PR-173) 안이면 pure-boost 확인으로만 보고.
- **최대 claim:** boost-residual diagnostic + independence-restoration C3.

#### PR-181 — Systematics-as-hypotheses normalized model competition (FPR calibration)

- **Owner / dependencies / cost:** `HTT`; contributor `OBSSTAT`; PR-140, PR-141, PR-143, PR-167; medium--high.
- **Targets:** advocate rank-21; 반복되는 "그건 survey systematic" 반론(EXT-DESI window-dominated, K5-MV, EXT-ACT).
- **SPEC:** claim=`각 등록 systematic-null을 first-class normalized generative model{cosmological-dipole / structured-systematic bank / null}로 승격하고 evidence가 adjudicate`; falsifier=beta_true=0에서 per-family FPR 보정 후 어떤 systematic model이 reactive signal을 calibrated FPR 넘게 재현하면 그 'detection'은 systematic(specificity gate); ceiling=C3(conditional), downclaim(ALREADY_KNOWN, ST-01 shared-cause abstention에 인접 -> 최약 non-overlap).
- **실제로 할 것:** subagent(1 spec → 3 normalized model bank + nested-sampling → 4 review). PR-140/141의 normalized-evidence + abstention 위에서 systematic bank를 model competition으로.
- **하지 말 것:** dependent evidence를 곱하거나 abstention을 detection으로 바꾸지 않는다.
- **주의·anti-drift:** ST-01/PR-141과의 delta(systematic bank as first-class model)를 명시; nuisance/prior를 결과 전 freeze.
- **검증·산출물:** per-family FPR calibration, model-competition evidence table, specificity gate.
- **Exit / kill:** systematic model이 signal을 FPR 넘게 재현하면 headline claim 차단.
- **최대 claim:** systematics-specificity model competition C3(conditional).

### Wave 27 — Advocate gates-off ambitious registry (hypothesis_only)

이 두 카드는 family-ID/geometry에 닿으므로 **절대 shipped data에서 family를 판정하지 않는다.**
완성해도 registry의 reference signal이며 pre-native 승격 금지(PR-165 전 blocked). completeness
critic이 handedness veto의 data-adjudication leak을 지적했고 이를 반영해 재규정했다.

#### PR-182 — Parity / B-mode family bit + handedness veto sign(EB/TB)=sign(x_h) (hypothesis_only)

- **Owner / dependencies / cost:** `COMMON`; contributors `BASS`,`OBSSTAT`; PR-167; medium. **gate_tier=gates_off_ambitious → hypothesis_only; native atlas reference signal.**
- **Targets:** advocate rank-7; native solver 없이 도달 가능한 유일한 family bit route(대칭 진술, solve 아님).
- **SPEC:** claim=`axisymmetric(I,V,VII0,III,IX) => B==0는 parity 정리; helical VII_h => B~E + parity-odd TB/EB; boost는 parity-odd 신호 identically zero`; **REFRAMED**: sign(EB/TB)=sign(x_h) handedness veto는 shipped data에서 Bianchi FAMILY를 판정하지 않고 future native atlas의 registered reference signal로만 남는다; falsifier(registry-level)=helical VII_h에서 sign(EB/TB)가 local CF4 velocity-curl handedness와 불일치하면 helical VII_h 반증, 일치는 corroboration only; ceiling=C1 theorem(hypothesis_only).
- **실제로 할 것:** subagent(1 spec → 3 parity theorem(solver-free) + sign-comparison registry → 6 review). B-mode-parity 정리를 solver-free로 봉인하고 handedness veto를 hypothesis_only reference signal로 등록. downclaim: parity split은 Pontzen-Challinor 2007(CONFIRMATORY), 유일 신규 sliver는 CMB parity sign↔local PV-curl handedness 결속.
- **하지 말 것:** 현재 데이터에서 family를 판정하거나 production/manuscript로 승격하지 않는다.
- **주의·anti-drift:** hypothesis_only·public_use=false lint(PR-167); native atlas 도착(PR-161--165) 전 dormant.
- **검증·산출물:** parity theorem seal(Pontzen-Challinor 귀속), handedness reference-signal registry entry, no-data-adjudication guard test.
- **Exit / kill:** guard가 data-family-adjudication을 감지하면 즉시 차단.
- **최대 claim:** solver-free parity theorem + registered handedness reference C1(hypothesis_only).

#### PR-183 — Low-ell T-E recombination-shear coherence ratio discriminant (needs-native)

- **Owner / dependencies / cost:** `BASS`; contributor `OBSSTAT`; PR-159--161, PR-167; blocked until native delivery. **gate_tier=gates_off_ambitious → hypothesis_only.**
- **Targets:** advocate rank-18; EGS converse를 하늘이 결정하는 최선의 empirical go/no-go.
- **SPEC:** claim=`recombination shear는 fixed TE sign/ratio의 coherent low-l E를 source하고, kinematic boost/tilt는 coherent E 없는 T-quadrupole을 준다`; falsifier=native low-l solve에서 recombination shear가 fixed-sign coherent low-l E를 못 만들거나, 측정된 low-l T-quadrupole이 그 sign의 coherent E 없이 나타나면 shear origin 반증(kinematic 선호); ceiling=C4(needs-native, hypothesis_only).
- **실제로 할 것:** interface-only 준비(§14 native 규율). data side(coherent E + TE sign 측정)는 지금 가능하나 THIS project의 정확한 TE sign/ratio 예측은 fail-closed native solver 필요 -> PR-159 이후 dormant.
- **하지 말 것:** theory-g fail-closed를 우회하거나 external proxy로 TE 예측을 fabricate하지 않는다.
- **주의·anti-drift:** data-side 측정과 native 예측을 분리; 정량 ratio는 native 전 blocked.
- **검증·산출물:** data-side coherent-E/TE-sign estimator(측정 가능분), native prediction interface stub(dormant).
- **Exit / kill:** native 없이 정량 예측을 만들면 차단.
- **최대 claim:** data-side coherent-E/TE diagnostic C3(측정분) + native-conditional discriminant C4(hypothesis_only, blocked).

### Checkpoint 130 (advocate track)

PR-183 후 총 130 checkpoint를 실행한다. advocate track에서는 다음을 별도 기록한다: spec-first 통과
카드 수, subagent 단계별(1--7) 완료·blocked 수, gate-off hypothesis_only lint 위반 수(0이어야 함),
data-adjudication guard(PR-182) 상태, 그리고 net-new vs extends(reclassified) 분류. gate-off leak이
하나라도 있거나 두 카드 연속으로 falsifier 없이 schema만 추가하면 advocate track을 중단·replan한다.
PR-168(code-integrity)이 최우선이며 나머지는 §16의 승격 gate를 그대로 통과해야 한다.

### 14b.1 Reclassified(net-new 아님) — frozen PR의 extends edge

completeness critic이 net-new로 오분류된 5개 advocate 후보를 frozen PR과 겹친다고 판정했다. 이들은
독립 PR이 아니라 아래 frozen PR의 `extends` edge로만 편입한다(PR-167).

| Advocate 후보 | 겹치는 frozen PR | net-new delta(only) |
|---|---|---|
| Manufactured-universe MMS (S26) | CO-04 / PR-123 | anisotropy-specific injected ground truth (B0/θ0/ω0) + β_true=0 specificity bracket |
| Occupancy pushforward x→Q→Π (S14) | ST-06 / PR-142 | F⊥–lnB obstruction theorem ONLY (F_Bayes=E[Q\|D]는 frozen MIO functional) |
| Partial-ID SBC (S12) | PR-136 / PR-138 | structural-null {W²,Ω_k} no-update invariance test |
| Unified partial-ID coverage toolkit (S13) | PR-136 / PR-137 / ST-04 | simultaneous multi-projection coverage certificate |
| Sign-locked one-sided Ω_tilt ceiling (S38) | ST-04 / PR-147 | sign-locked one-sided ceiling(point-measurement이 아님) |

## 15. Downclaimed 43건의 PR crosswalk

`Literal`은 같은 claim identity를 유지할 가능성이 있는 경우다. `Supersede`는 기존 finding을 닫되 새 정확한 claim ID를 만들어야 한다. `Rebuild`는 원 domain/estimand를 유지한 새 증거가 필요하다.

| Finding | 경로 | 주 PR | 추가 gate / 최종 ceiling |
|---|---|---|---|
| C1-K5-MV-F2 | Rebuild | PR-145, 147 | common-window vector + full covariance; estimator/survey conditional |
| C1-K5-MV-F4 | Rebuild | PR-144, 147 | all registered distance conventions + joint covariance |
| C1-K5-MV-F5 | Rebuild | PR-144--146 | registered distance likelihood E2E coverage |
| C10-K1-JWST-F1 | Supersede | PR-153, 154 | synthetic/authenticated endpoint 분리; conditional forecast |
| C10-K1-JWST-F5 | Rebuild | PR-135, 149, 150 | structural quotient + matched global null |
| C2-K5-MOCKSIG-F3 | Supersede | PR-135, 146 | finite-null interval; 기존 Gaussian sigma 폐기 |
| C2-K5-MOCKSIG-F5 | Rebuild | PR-137, 145, 146 | boundary/non-railed nuisance coverage |
| C3-K5-VCORR-ML-F4 | Rebuild | PR-145, 146 | per-column independent injection coverage |
| C3-K5-VCORR-ML-F5 | Rebuild | PR-145, 146 | exact 8 regions + leverage/coverage |
| C3-K5-VCORR-ML-F6 | Rebuild | PR-134, 145 | equivalence/discrepancy estimand + joint covariance |
| C4-EXT-DESI-F5 | Rebuild | PR-151 | matched component simulations; attribution may still fail |
| C4-EXT-DESI-F6 | Rebuild | PR-151 | same cap estimator + source-derived ratio/null |
| C5-EXT-ACT-F2 | Supersede | PR-152 | upstream correction wording + residual diagnostic |
| C5-EXT-ACT-F5 | Literal candidate | PR-135, 152 | release-simulation coupling bound only |
| C5-EXT-ACT-F6 | Supersede | PR-152 | stochastic estimand/injection law; deterministic claim 별도 |
| C6-K6-CURL-F1 | Supersede | PR-123 | numerical upper bound; observed vorticity 아님 |
| C6-K6-CURL-F3 | Supersede | PR-123 | kernel/amplitude-gradient/boundary decomposition |
| C6-K6-CURL-F4 | Literal candidate | PR-123 | analytic `sqrt(2)` lock + no empirical consumer |
| C7-MES-F3 | Supersede | PR-124, 157 | exact source count + independent derivation 분리 |
| C7-MES-F4 | Supersede | PR-124, 132 | symbolic/physical uncertainty/in-house rule 분리 |
| C8-FRAMEWORK-F3 | Supersede | PR-124 | sanity anchor를 theorem count에서 제외 |
| C8-FRAMEWORK-F4 | Supersede | PR-124 | checked signature의 conditional lemma |
| C8-FRAMEWORK-F5 | Supersede | PR-125, 157 | leading-order/channel/reopening qualifier가 quantifier/domain을 바꾸므로 qualified successor claim ID 발급 |
| C9-LCDMCV-RECON-F3 | Rebuild | PR-145, 147 | explicit windows + common flow + joint covariance |
| C9-LCDMCV-RECON-F5 | Supersede | PR-147 | machine comparability table; homogeneous range 폐기 |
| GAP-03 | Rebuild | PR-157 | corrected estimand에서 novelty 재심사 |
| GAP-05 | Rebuild | PR-127, 137, 143, 157 | executable kernel + grid-conditional coverage; class-wide uniformity는 별도 theorem + prior art |
| GAP-13 | Literal process rescue | PR-119, 157 | coverage accounting only |
| GAP-14 | Literal process rescue | PR-119, 157 | harness-internal digest-blind sampling only |
| N-DATA-ACT-RANGE | Rebuild/no-go | PR-152 | raw/upstream QE 없으면 abandon current dataset |
| N-DATA-FS8-DEPTH | Rebuild | PR-147, 148 | simultaneous depth coverage + joint covariance |
| N-DATA-JWST-ACQUISITION | Rebuild | PR-153 | row-complete authority |
| N-DATA-JWST-COVARIANCE | Rebuild | PR-154 | hierarchical/shared calibration covariance |
| N-DATA-JWST-CROSSMATCH | Rebuild | PR-153, 154 | probabilistic identity and propagated ambiguity |
| N-DATA-JWST-WEIGHTING | Rebuild | PR-154 | actual per-host uncertainty; no global shrink |
| N-DATA-K1-STALE-DIRECTION | Rebuild | PR-149, 150, 155 | pre-data axis or re-estimation + joint null |
| N-STAT-PSEUDO-LOOCV | Supersede | PR-139 | old output=channel ablation; new valid holdout claim |
| N-STAT-PSEUDO-PPC | Supersede | PR-138 | old output=residual check; new replicated-data PPC |
| N-THEORY-EGS-CONVERSE | Supersede | PR-126 | one-way premise theorem + counterexample |
| N-THEORY-FLRW-CONVERSE | Supersede | PR-126, 127 | one-way FLRW + non-injective coordinate |
| N-THEORY-NT2-SUFFICIENCY | Supersede | PR-130 | convergence/non-sufficiency; factorization 없으면 sufficiency 금지 |
| N-THEORY-NTA3-REGRESSION | Supersede | PR-129 | estimator-specific dispersion theorem |
| N-THEORY-OMK-DOMAIN | Supersede/new theorem | PR-131, 132 | class-conditional asymptotic + remainder |

주요 P0/rebuild 경로는 별도로 고정한다.

| Finding | PR | 종료 조건 |
|---|---|---|
| C1-K5-MV-F1 P0 | PR-120, 144--147, 157 | quarantine + authenticated lineage + nuisance-orthogonal E2E coverage + non-author adjudication |
| C3-K5-VCORR-ML-F1 P0 | PR-120, 144--146, 157 | shape-correction provenance/authority + independent implementation + all-consumer regeneration |
| N-DATA-CF4-DOWNSTREAM | PR-147, 148, 155, 156 | identified set, joint covariance, held-out rank; global interpretation은 별도 |
| N-STAT-K1-EXCHANGE | PR-135, 149, 150 | identical observed/null frozen scan + super-uniform finite ranks + E2E support |
| N-THEORY-NT2-COEFFICIENT | PR-124, 128 | independent derivations + exact consumer regeneration |
| N-THEORY-OMEGA-SEMANTICS | PR-125, 133 | frame/order types + local/global non-bridge |
| C7-MES-F1 | PR-122, 124, 132, 157 | branch/premise별 두 독립 derivation + convention test + manuscript reconciliation |
| C7-MES-F2 | PR-122, 124, 157 | legacy byte-stable, active successor pointer, stale triple consumer 0 |
| N-THEORY-D2-AUTHORITY | PR-122, 124, 157 | separately authored nonzero Rust target + source/input/output/toolchain hashes |
| C6-K6-CURL-F2 | PR-123, 157 | exact solid-body/potential/manufactured-boundary anchors + independent continuum-order oracle |

## 16. 단계별 연구 운영과 승격 gate

아래 단계는 달력 순서가 아니라 evidence dependency다. 앞 단계의 실패를 일정 압박으로 우회하지 않는다. 기간은 1명의 전일제 연구자 기준 planning envelope이며 약속된 마감이 아니다.

| 단계 | 범위 | 예상 규모 | 진입 조건 | 성공 시 얻는 것 | 실패 시 처분 |
|---|---|---:|---|---|---|
| A. 권위·재현성 봉합 | PR-119--123 | 4--8 person-weeks | formal DAG intake 승인 | P0 격리, hermetic replay, claim-addressed evidence와 독립 oracle | data result 생성 중단, harness/reproducibility report만 보존 |
| B. 장기 이론 재건 | PR-124--133 | 6--12 person-months | A의 mutation kill과 oracle lineage 통과 | premise-complete theorem, non-ID 영역, estimator/계수 authority, remainder와 local/global type system | 틀린 명제는 supersede/falsify; domain 밖은 blocked |
| C. 장기 통계 재건 | PR-134--143 | 6--12 person-months | B의 frame/domain/response contract freeze | exact finite null, partial ID/coverage, genuine PPC/holdout/evidence, abstaining inference | method-ready가 아닌 lane의 data PR만 차단 |
| D. authenticated data 재분석 | PR-144--158 | 8--18 person-months + compute/data | C의 blind synthetic adjudication 통과 | CF4/K1/DESI/ACT/JWST의 survey-conditional result와 독립 disposition | 입력·coverage·rank 실패 시 rebuild/abandon/negative result |
| E. native 후속 | PR-159--166 | 외부 delivery 의존 | signed native delivery와 conformance | atlas-conditioned morphology compatibility와 외부 gate | dormant, compatibility set 또는 abstention 유지 |

승격은 다음 conjunctive gate를 따른다.

1. **Mechanics gate:** 독립 derivation/oracle, mutation kill, convention/domain과 수치 수렴이 모두 통과한다.
2. **Identification gate:** response rank, nuisance class, set topology와 decisive falsifier가 명시된다. point identification이 아니면 set 또는 abstention으로 끝낸다.
3. **Calibration gate:** matched null, covariance, finite rank, size/coverage/SBC/PPC/holdout 중 해당 항목이 사전 기준을 통과한다.
4. **Provenance gate:** authenticated input, selection/mask/transfer/config/environment와 모든 consumer가 hash로 닫힌다.
5. **Independence gate:** claim author가 아닌 adjudicator가 raw receipt와 failed cases를 보고 판정한다.
6. **Claim gate:** 기존 claim identity가 유지될 때만 `RESCUED`; estimand/domain/statistic/quantifier가 바뀌면 반드시 `CORRECTED_SUPERSEDED`와 새 claim ID다.

가장 먼저 투자할 장기 축은 PR-124--143이다. 이 구간은 한 데이터셋의 유리한 수치를 얻는 대신 여러 downstream finding을 동시에 판별하는 방법론 자산을 만든다. PR-144 이후의 survey 분석은 이 자산을 소비하는 첫 응용이며, foundation 실패를 숨기기 위한 별도 구현을 만들 수 없다.

## 17. PR별 검증 명령과 증거 최소선

PR-119가 active DAG에 들어갈 때 실제 repository path와 CLI가 확정되어야 한다. 아래 `existing` 명령은 현재 저장소에서 실행 가능한 공통 baseline이고, `to-be-created` entrypoint는 해당 PR 자체가 구현·문서화·테스트해야 하므로 그 전 PR에서 성공했다고 기록할 수 없다.

### 17.1 모든 PR의 공통 baseline

```bash
venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml
git diff --check
```

테스트 실행 예산(AMENDMENT_01): 매 PR의 고정 의무는 해당 PR의 targeted selector +
가장 작은 관련 smoke이며, exact test receipt
(`.agent-harness/scripts/test_receipt.py`; source/selector/environment/seed
fingerprint가 같고 deterministic pass면 재실행하지 않음)를 재사용한다. full
`pytest --collect-only -q` + `pytest -m smoke -q` 전량 실행은 (a) five-PR
checkpoint, (b) packaging/collection에 영향을 주는 변경, (c) release snapshot에서
한 번 실행한다. **예외: CAS가 필요한 PR(R3)은 언제나 네 axis receipt 전부를
요구한다** — receipt 재사용은 축이 아니라 동일 fingerprint의 반복 실행에만
적용된다.

추가로 각 PR은 다음 세 층을 모두 실행한다.

- **Contract layer:** schema, owner, claim tier, artifact mode, transfer, state transition, negative claim-language test.
- **Scientific mechanics layer:** 해당 PR의 analytic fixture, independent oracle, manufactured solution, mutation/property/convergence/coverage test.
- **Consumer layer:** producer regeneration, all-consumer stale scan, result-pack/figure/manuscript/package가 invalid 또는 blocked receipt를 거부하는 negative test.

### 17.2 lane별 최소 증거

| PR 범위 | 최소 실행 증거 | 통과로 간주하지 않는 것 |
|---|---|---|
| PR-119--123 | detached clean replay, known-defect mutation kill matrix, fabricated receipt/`ready_for_claims` spoof rejection | local editable install 하나, schema round-trip만 통과 |
| PR-124--133 | 두 독립 derivation lineage, sign/unit/limit/domain, constructive counterexample, arbitrary precision 또는 interval enclosure | 같은 expression의 두 backend 평가, finite grid spot check |
| PR-134--143 | exact small-N reference, matched multi-seed DGP, simultaneous size/coverage, SBC, replicated-data PPC, leakage-free refit, abstention rate | caller-supplied p-value/PPC, fitted likelihood 차이, favorable high-signal case |
| PR-144--148 | authenticated row/selection/group manifest, full correction covariance, shell/null injection recovery와 all-consumer regeneration | audit-only replacement, diagonal error, same-data independence 가정 |
| PR-149--154 | exact release/mask/selection pipeline, observation-inclusive null, per-mock refit, upstream asset gate, row-level crossmatch | 현재 공개 summary를 raw asset으로 간주, local rank, synthetic row를 observed로 간주 |
| PR-155--158 | joint simulations/negative controls, held-out response rank, independent finding disposition, clean manuscript rebuild | 방향 일치만으로 confirmation, internal agent vote만으로 rescue |
| PR-159--166 | signed delivery receipt, transport conformance, atlas convergence, matched cut-sky simulations, blind equivalence coverage, external replication | external transfer를 native로 rename, single-label best fit, 내부 self-validation |

각 five-PR checkpoint에서는 공통 baseline에 더해 다음을 machine-readable table로 남긴다: completed/blocked count, open P0/P1, newly killed/surviving mutations, empirical size/coverage, stale consumers, independent adjudications, 최고 허용 claim tier, critical path와 다음 kill switch. 총 PR 수가 110이 된 PR-163 checkpoint 뒤 PR-164--166은 별도의 final closeout으로 처리한다.

## 18. Anti-drift 운영 지침과 대표 실패 모드

### 18.1 claim identity drift

- quantifier, estimand, population, domain, frame/order, data release/support, statistic, null/prior/nuisance 또는 transfer가 하나라도 바뀌면 identity diff를 생성한다.
- identity diff가 비어 있지 않은데 `RESCUED`를 요청하면 state machine이 거부한다. 새 결과가 더 좋아도 `CORRECTED_SUPERSEDED`다.
- “통계적으로 유의”, “family-compatible”, “global” 같은 단어를 삭제하는 것만으로 evidence state를 올리지 않는다.

### 18.2 이론 drift

- 기호 하나에 local observer boost, matter tilt, vorticity, curvature 또는 geometry 두 의미를 허용하지 않는다.
- algebraic witness, constraint-admissible state, local dynamical solution, global solution을 같은 `valid` boolean으로 평탄화하지 않는다.
- signed curvature를 PSD projection으로 잘라 상쇄 방향을 제거하지 않는다. `S_+^3 x R` 또는 동등한 signed branch representation을 유지한다.
- exact theorem, almost theorem, asymptotic formula, empirical fit, sanity anchor의 증거등급을 교환하지 않는다.
- interval remainder와 physical model-form/source uncertainty를 한 숫자로 합치지 않는다. 실패한 enclosure는 observational noise로 흡수하지 않는다.

### 18.3 통계 drift

- observation, null, mocks가 동일한 scoring/maximization/selection/refit 경로를 쓰지 않으면 p-value 생성 자체를 금지한다.
- posterior draw가 prior/likelihood/data/config/transfer에 결속되지 않으면 PPC/evidence를 만들지 않는다.
- `ready_for_claims` 속성, caller-provided p-value, fitted log-likelihood 차이, channel ablation이 각각 adequacy/PPC/Bayes factor/LOOCV로 통과하지 못하도록 adversarial mutation을 영구 유지한다.
- nuisance family, discrepancy, scan range, mask, depth, tie policy와 prior grid는 evaluation 결과를 보기 전에 freeze한다. 변경하면 새 analysis/multiplicity family다.
- near-null, boundary, disconnected 또는 unbounded identified set은 오류가 아니라 가능한 답이다. point estimate로 강제 변환하지 않는다.

### 18.4 데이터·코드 drift

- authenticated, local-derived, synthetic, proxy와 audit-only 입력을 서로 다른 enum으로 유지하고 implicit cast를 금지한다.
- raw release 또는 calibration asset이 없으면 작은 public product로 같은 estimand를 흉내내지 않고 `BLOCKED` 또는 새 estimand로 supersede한다.
- data correction, comparator, nuisance fit과 headline statistic이 같은 row를 공유하면 full joint covariance가 없을 때 곱셈/합산을 금지한다.
- generator 수정 뒤 source artifact만 새로 만들고 figure/result pack/manuscript를 그대로 두는 상태를 release failure로 취급한다.
- 두 연속 PR이 manifest/schema/gate만 추가하고 새로운 falsifier, counterexample, calibrated simulation 또는 authenticated regeneration을 만들지 못하면 즉시 replan한다.

### 18.5 독립성·자원·중단 규칙

- oracle 독립성은 파일 경로가 아니라 식의 출처, 알고리즘, implementation author, fixture와 random stream의 lineage로 판정한다.
- 단일 decisive run이 6시간을 넘거나 필수 입력을 확보하지 못하면 축소 성공을 원 결과의 대용으로 쓰지 않는다.
- 실패한 blind challenge를 고친 뒤 같은 held-out label로 재평가하면 그것은 training이다. 새 sealed challenge version을 만든다.
- subagent debate는 hypothesis discovery와 review 증거이지 external replication이 아니다. dissent와 minority report를 삭제하지 않는다.

## 19. CRAG 갱신 지점과 외부 방법론 기준

이 로드맵의 2026-07-14 targeted refresh는 방법론의 원전과 공식 data portal만 anchor로 사용했다. 실제 PR 시작 시 변동 가능한 release 구성, 라이선스, download size와 API를 다시 확인하고 URL/access time/hash를 intake receipt에 기록한다.

| 범위 | 현재 anchor | PR에서 확인할 사항 |
|---|---|---|
| finite Monte Carlo null | [Phipson--Smyth](https://arxiv.org/abs/1603.05766) | 관측 포함 rank, ties, finite resolution과 exact interval 구현 |
| partial identification | [Chen--Christensen--Tamer](https://arxiv.org/abs/1605.00499) | 현재 constraint class에서 confidence-set/coverage 가정의 적합성 |
| SBC | [Talts et al.](https://arxiv.org/abs/1804.06788) | sampler calibration과 observed adequacy를 분리하는 discrepancy |
| PSIS-LOO | [Vehtari--Gelman--Gabry](https://arxiv.org/abs/1507.04544) | dependence unit, Pareto diagnostic와 exact-refit fallback |
| Planck | [Planck Legacy Archive](https://pla.esac.esa.int/) | exact map/release/mask/simulation provenance와 redistribution 조건 |
| ACT DR6 | [ACT DR6 official data products](https://act.princeton.edu/act-dr6-data-products) | raw/upstream QE availability, masks, simulations와 transfer/filter metadata |
| DESI DR1 | [DESI DR1 official release documentation](https://data.desi.lbl.gov/doc/releases/dr1/) | exact tracer/selection; 공식 문서의 1000 EZmocks와 25 AbacusSummit mocks 중 estimand에 맞는 ensemble과 per-mock refit 가능성 |

웹 검색은 결론을 좋은 방향으로 조정하는 도구가 아니다. PR-119 intake, 각 data-release PR의 시작, PR-157 독립 adjudication과 PR-159 native intake에서만 목적·질의·선택 기준을 사전 기록한 짧은 CRAG을 허용한다. 방법/claim을 고르는 blind calibration 구간에서는 frozen corpus와 repository evidence만 사용한다.

## 20. 활성화 순서와 다음 실행 카드

> **HISTORICAL PLAN — frozen 2026-07-17 by AMENDMENT_01.** §20--§21은 PR-119
> intake 이전의 계획 기록으로 고정한다. 살아있는 진행 상태의 SSoT는
> `docs/codex_handoff/pr_status.yaml`(mirror `machine_readable/pr_status.yaml`)과
> 짧은 per-PR delta(`docs/PR_DELTAS/`)다. 이후 progress를 이 장문 문서에 다시
> 삽입하지 않는다.

이 문서는 active backlog를 수정하지 않는다. 채택 시 첫 실행은 **PR-119 하나만** formal intake하는 것이다. PR-119의 실제 순서는 다음과 같다.

1. 현재 65/65 DAG와 양쪽 status mirror를 hash/freeze한다.
2. PR-119--166의 ID/dependency를 parser로 검증하고 old `AUD-R*`/`PR-R*` proposal crosswalk를 만든다.
3. 48개 카드를 한 번에 `pending`으로만 등록하며 과학 finding state는 바꾸지 않는다.
4. claim identity fingerprint와 remediation state machine을 먼저 구현한다.
5. 다음으로 PR-120의 P0 consumer scan과 quarantine만 연다.
6. PR-121--123의 clean replay/evidence graph/oracle을 통과하기 전 이론 또는 데이터 계산을 authoritative로 수용하지 않는다.
7. PR-124--143을 장기 연구의 주 critical path로 배치하고 매 checkpoint에서 실패한 theorem/method의 downstream edge를 자동 block한다.
8. PR-144 이후에는 authenticated input을 가진 lane만 진행한다. ACT raw-QE처럼 입력이 없으면 그 lane만 abandon/block하고 다른 lane의 성공으로 대체하지 않는다.
9. PR-157에서 모든 finding을 non-author가 다시 판정한 뒤에만 PR-158 manuscript rebuild를 연다.
10. PR-159--166은 native delivery가 실제로 도착하기 전 `dormant_external_dependency` 상태를 유지한다. delivery가 먼저 도착하면 PR-159 read-only intake만 PR-122/124/125 후 조기 실행하고, PR-160--166의 science gate는 우회하지 않는다.

이 로드맵 자체의 수용 기준은 다음과 같다: PR-119--166이 정확히 한 번씩 정의되고 dependency가 선행 ID만 가리키며, 모든 카드에 owner/dependency/cost, 실제 작업, 금지사항, anti-drift, 검증, exit/kill과 claim ceiling이 있어야 한다. 43개 downclaimed finding과 주요 P0/rebuild finding은 실행 경로를 가져야 하고, pre-native family/geometry ceiling을 우회하는 카드가 없어야 한다.

## 21. 문서 작성·적대 심사·검증 closeout

이 closeout은 로드맵 문서의 정합성 증거이며, 어떤 과학 finding의 remediation 또는 rescue 증거도 아니다.

- 장기 이론, 장기 통계/데이터, 독립 roadmap referee 역할을 분리해 초안을 작성했다. 이 내부 multi-agent 검토는 external replication으로 세지 않는다.
- referee가 snapshot `0bae9813ca4b8e473e9d8b558726828100586b1286485feb8afc9f93f8ba0e05`에서 10개 P1을 제기했다: conditional adjudication dependency, premature native serialization, K6/CF4 결속, native equivalence dependency, owner/tier schema, literal-rescue identity, signed-curvature admissibility, MES/D2 authority, spoofable receipt, finite-grid uniformity다.
- 모두 수정한 뒤 snapshot `104d9363b8c5d2aae1ecbdc131b2e80a87fe10f5240609e387ab379a91254e24` 재심에서 9개가 resolved, owner-role 항목만 partial이었다. formal theory owner를 `COMMON`으로, BASS를 contributor/consumer로 교정한 snapshot `526366c4c090a3021071f0169ec1514580ad36b1043ef7312456c7c18e6b29cc`에 대해 referee는 잔여/신규 P1 이상이 없다고 판정했다.
- 구조 검사에서 PR-119--166이 정확히 48개이고, 각 카드의 7개 필수 필드가 각각 48회 존재하며, dependency는 모두 선행 PR만 가리켰다. downclaimed crosswalk는 header 제외 43행이다.
- 권위 입력 6개의 SHA256을 실제 파일과 재대조해 section 2와 일치함을 확인했다.
- `venv/bin/python -B scripts/check_claim_language.py --dry-run --format json <roadmap>` 결과는 `issue_count=0`이다.
- `venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` 결과는 기존 active `65 PRs, DAG valid`다. 이 문서가 active backlog/status를 수정하지 않았음을 별도로 확인했다.
- 관련 contract regression은 `23 passed`; full collect-only는 `7,898/7,957 collected, 59 deselected`; smoke는 `6 passed, 7,951 deselected`였다.
- trailing whitespace와 `git diff --no-index --check /dev/null <roadmap>` 검사는 clean이었다.
- worktree에는 이 planning document만 새 연구 산출물로 남겼다. user-owned `legacy/`와 두 원본 harness ZIP은 읽기/수정/stage하지 않았고, commit 또는 active DAG intake도 수행하지 않았다.

### 21.1 2026-07-14 advocate 병합 addendum

- 원 로드맵(PR-119--166)에 advocate divergence track(Wave 22--27, PR-167--183 = 16 net-new + 1 intake)을 편입해 단일 연구계획으로 병합했다. 원 카드의 8-field 양식·번호·판정 원칙을 보존하고 각 advocate 카드에 `SPEC` field(spec-driven)와 §4.5 subagent 단계 참조를 추가했다.
- 실행 방식은 spec-driven(구현 전 SPEC/decisive-falsifier 확정) + 단계별 subagent-driven(§4.5의 7단계 typed 위임)이다. mounted harness(`harness/physmath-{research,coding}-gpt56/`)와 그 13 skill + 23 htt-* skill을 위임 대상으로 명시했다.
- advocate 후보의 non-overlap은 `frozen_non_overlap_set.json`(32 candidates + 48 원 PR)으로 검증했고, final CRAG가 novelty를 INCREMENTAL/CONFIRMATORY로 낮췄으며(NEW 0건), completeness critic이 net-new로 오분류한 5개를 §14b.1의 `extends` edge로 강등했다. family-ID/geometry 계열(PR-174/175/182/183)은 hypothesis_only·public_use=false이며 pre-native 승격 금지 원칙은 원 로드맵과 동일하다.
- 이 병합 문서는 여전히 `PROPOSED_ONLY_NOT_IN_ACTIVE_DAG`다. active backlog(65/65)와 status mirror는 수정하지 않았다. advocate 근거 ledger는 dev-tier(commit `a56451c`)이며 immutable하다.
