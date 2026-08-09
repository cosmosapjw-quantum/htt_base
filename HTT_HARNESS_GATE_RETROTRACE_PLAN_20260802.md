# HTT 하네스·claim gate 현대화 및 전면 재분석 계획

기준일: 2026-08-02 (KST)  
저장소: \`cosmosapjw-quantum/htt_base\`  
감사 기준: \`research/pr04-multicomponent@7214ef7e91763ed807e0e350e1cfeffb82cec0f5\`

## 1. 결론

지금 필요한 것은 gate를 일괄 해제하는 작업이 아니다. 오래된 하네스가 현재의 vector/tensor 의미론을 잘못 막는 부분은 typed successor로 교체하고, 과학적으로 본질적인 경계는 유지하며, 실제 증거가 생겼을 때만 개별 조건을 discharge하는 구조로 바꿔야 한다.

권고 순서는 다음과 같다.

1. 현재 실행환경과 하네스 부채를 먼저 고정한다.
2. 단일 \`claim_tier\` 대신 다축 promotion state를 도입한다.
3. 과거 runner와 frozen receipt는 변경하지 않고 successor harness로 감싼다.
4. 123개 source obligation과 28개 VT obligation을 record 단위로 재심사한다.
5. PR-247~260 preflight 뒤 PR-261~275를 현재 vector/tensor replay spine으로 재실행한다.
6. PR-151은 완전 취득 전에는 과학 입력으로 사용하지 않는다.
7. 관측 데이터가 admission을 통과하면 CF4·Planck·DESI·ACT·JWST 및 cross-survey 결과를 원자료부터 다시 계산한다.
8. 보고서·그림·원고는 모든 upstream receipt가 확정된 뒤 마지막에 재생성한다.

이 계획은 코드나 GitHub 상태를 변경하지 않은 read-only 감사 결과다.

## 2. 현재 기준선

- Canonical scientific DAG: 222 work units
  - completed 170
  - blocked 1 (\`PR-172\`)
  - pending 22
  - dormant external/native 28
  - background acquisition 1 (\`PR-151\`)
- 완료율: 76.58%, dependency-weighted 81.96%, critical path 98.70%.
- 현재 unblocked 후보는 \`PR-190\`, \`PR-204\`지만, 본 계획을 실행하려면 먼저 별도의 replan work unit을 DAG에 등록해야 한다.
- GitHub 공개 PR 레코드는 366건이다.
  - merged 28
  - closed draft/non-accepting attempt 338
  - 현재 target branch에 직접 병합된 것은 16건
- GitHub PR 번호와 내부 \`PR-NNN\` work unit은 동일한 식별자가 아니다. 특히 [GitHub PR #367](https://github.com/cosmosapjw-quantum/htt_base/pull/367)은 내부 PR-275 하나가 아니라 PR-259~275와 선행 수리들을 포함한 94-commit, 195-file publication cluster다.
- #367에 기록된 broad suite는 10,038 passed, 406 failed, 69 skipped, 59 deselected, 15 xfailed다. 이 receipt는 보존하되 green baseline으로 오인하지 않는다.
- 현 \`PROOF_ATLAS\`의 123개 source row와 별도 VT obligation 28개는 모두 \`NOT_ADJUDICATED\`다. evidence-layer의 analytic/CAS/synthetic 성공은 source 상태를 자동 승격하지 않는다.
- PR-274는 \`admitted_count=0\`, \`pilot_executed=false\`다. 관측 결과가 아직 없다.
- PR-273의 과거 truth는 이미 알려졌으므로 exact replay는 재현성 증거일 뿐, 새 blind validation은 아니다.

현 checkout에서 재현한 하네스 기준선은 green이 아니다.

- 기본 subset runner는 repo venv가 없으면 pytest가 없는 launcher Python으로 fallback하여 collection 전에 실패한다.
- pytest만 있는 임시 환경도 project distribution이 설치되지 않아 실패한다.
- clean non-editable install의 package lane은 5 failed / 22 passed다. 핵심 원인은 PR-124 authority receipt를 checkout-relative \`docs/\`에서 import-time에 찾는 구조다.
- root-wide smoke는 unrelated astropy \`SystemExit\` 때문에 중단되지만, 실제 smoke 3개 파일은 8/8, fast 1개 파일은 6/6 통과한다.
- source-mode broad collection에는 astropy/healpy optional import 5건이 skip attribution 전에 error가 된다.
- \`python -m pytest -q\`는 global \`-m not slow\`를 상속하므로 true full suite가 아니다.
- PR-275 generator check의 현재 차이는 \`REPLICATION_PACKAGE.json\`과 \`VECTOR_TENSOR_PROGRAM_REPORT.md\`의 environment identity뿐이다. 당시 환경과 현재 환경을 구분하지 않은 채 frozen output을 다시 쓰지 않는다.

NERSC는 Perlmutter 서비스 중단을 2026-07-22~2026-08-03으로 공지했다. 따라서 8월 2일 현재 PR-151에 대해 허용되는 작업은 기존 acquisition의 안전한 관찰과, 복구 후 완전성 검증 준비뿐이다. 부분 산출물의 분석 투입은 금지한다.  
출처: [NERSC service disruption notice](https://www.nersc.gov/users/user-news/major-power-upgrade-to-disrupt-services-july-20-august-7)

## 3. 무엇을 절대로 완화하지 않을 것인가

아래는 “blocker”가 아니라 의미론적 불변조건이다.

| 경계 | 유지할 규칙 | 가능한 positive route |
| --- | --- | --- |
| scalar → geometry | scalar \`x,Q,Pi,F,G_F\`, 방향·coherence·feature만으로 geometry/Bianchi family를 식별하지 않는다. | genuine native morphology atlas, admitted observations, mask/null/covariance/equivalence/open-set, HTT comparison을 별도로 통과한다. |
| x 해석 | \`x=1\`은 MES boundary이고 \`x>1\`은 premise-anchored omnibus tension이다. FLRW distance나 비선형성 크기 자체가 아니다. | vector/tensor state, orbit/response/depth 및 model discrepancy를 함께 보고 제한된 진술만 한다. |
| MIO → posterior | MIO는 diagnostic certificate만 소유한다. posterior, evidence, truth certificate를 만들지 않는다. | HTT가 명시적 likelihood/prior/null/PPC/LOOCV를 가진 별도 artifact를 생성한다. |
| external → native | external/AniCLASS transfer의 provenance는 절대 native로 재명명하지 않는다. | 실제 native producer가 새 artifact와 새 receipt를 만든다. |
| evidence substitution | proof, synthetic validation, data admission, observational diagnostic, native validation, inference는 서로 대체되지 않는다. | 해당 evidence branch에서만 승격한다. |
| restriction erasure | counterexample, local chart, conditional premise, partial chain rule, inconclusive result의 qualifier를 제거하지 않는다. | 더 강한 명제는 등록된 제한을 직접 제거하는 새 증거가 필요하다. |
| PR-151 partial use | 취득 중 partial bytes를 fixture, calibration, conclusion에 사용하지 않는다. | terminal completeness와 PR-274 재-admission 후 별도 실행 허가를 받는다. |
| missingness | 없는 component를 0으로 채우지 않는다. | typed \`MISSING/ABSTAIN/UNKNOWN/INDETERMINATE\`를 유지한다. |

## 4. 무엇을 조건부로 완화·격상할 수 있는가

현재의 blanket \`diagnostic_only\` 또는 \`native_solver_validation_absent\`를 모든 artifact에 일괄 적용하는 방식은 폐기 대상이다. 대신 다음과 같이 정확한 discharge 조건을 둔다.

| 현재 blocker | 승격 가능한 상태 | 필요한 최소 증거 |
| --- | --- | --- |
| source theorem \`NOT_ADJUDICATED\` | exact / conditional / restricted / refuted | exact statement와 source identity, assumptions, domain, frame, units, branch/order, required proof class, executable evidence, 비저자 독립 adjudication |
| missing theorem signature | signature complete | 원문을 바꾸지 않은 typed signature와 dependency/counterexample map |
| mechanics only | implementation verified | 독립 oracle, mutation/metamorphic failures, boundary/units/sign/dimension tests |
| synthetic only | validated synthetic | preregistered seed family, held-out split, coverage/multiplicity, misspecification, weak-ID/open-set tests |
| no admitted data | admitted for a frozen analysis | source/release/license/hash, sky/frame, mask, covariance, selection, transfer, required fields, complete acquisition |
| admitted data | authorized pilot | admission과 분리된 실행 승인, frozen protocol 및 resource receipt |
| observed diagnostic | model-conditional HTT inference | matched nulls, covariance, multiplicity, negative controls, likelihood/prior/PPC/LOOCV, partial-ID/abstention |
| local/global candidate | supported separation or identified set | response providers, supported covariance quotient, principal-angle/rank/condition thresholds, held-out wrong-source calibration |
| no native evidence | native-transfer validated | no-fallback native producer identity, conventions, units, frame/parity/ell support, held-out native tests |
| native transfer only | family claim eligible | 별도 native atlas, observational fit, family equivalence, open-set coverage, HTT comparison; 자동 승격 금지 |

모든 승격에는 다음 필드를 가진 machine receipt가 필요하다.

\`gate_id, subject_id, prior_state, target_state, evidence_branch, exact_statement_id, assumptions_hash, frame, units, branch, perturbative_order, data/mask/covariance/selection/transfer_ids, test_receipts, independent_adjudicator, invalidation_triggers, decision, human_note\`

## 5. 단일 claim tier를 대체할 상태 모델

한 개의 순서형 \`claim_tier\`는 artifact readiness, 과학적 의미, 증거종류, public use를 섞는다. 다음 product state로 분리한다.

\[
\mathcal G =
(\text{artifact readiness},
\text{evidence branch},
\text{scientific semantics},
\text{identification status},
\text{provenance grade},
\text{allowed use})
\]

증거 branch는 전순서가 아니다. 예를 들어 \`VALIDATED_SYNTHETIC\`과 \`ADJUDICATED_THEORY\`는 서로 다른 축이며 어느 한쪽이 다른 쪽보다 “높다”고 보지 않는다.

이론/수리물리:

\`REGISTERED → SIGNATURE_COMPLETE → EVIDENCE_MATCHED → ADJUDICATED_{EXACT, CONDITIONAL, RESTRICTED, REFUTED} → PUBLIC_THEORY\`

통계/데이터:

\`SPECIFIED → IMPLEMENTED → MECHANICS_VERIFIED → VALIDATED_SYNTHETIC → DATA_ADMITTED → OBSERVATIONAL_DIAGNOSTIC → MODEL_CONDITIONAL_INFERENCE → EXTERNALLY_REPRODUCED\`

Native provenance는 별도 branch다. external artifact의 “승격”이 아니라 새로운 native artifact의 생성으로만 진입한다.

Gate 판정은 \`PASS\`, \`PASS_WITH_CEILING\`, \`ABSTAIN\`, \`BLOCK\`, \`STALE_REPLACED\`를 사용한다. 단순 boolean은 이유·ceiling·invalidation을 표현하지 못하므로 외부 호환 view로만 남긴다.

## 6. 오래된 하네스의 처분 원칙

### 6.1 Frozen history와 live authority 분리

- 과거 runner, exact hash receipt, 실패 후보는 immutable archive로 둔다.
- 현재 파일을 과거 SHA와 강제로 일치시키지 않는다.
- current authority에는 typed successor edge를 등록한다.
- exact replay, scientific reproducibility, new scientific rerun을 별도 profile로 만든다.

권고 profile:

- \`replay-exact\`: 당시 환경·bytes 재현. 실패하면 과학 회귀가 아니라 replay-grade 실패로 기록.
- \`replay-scientific\`: 같은 estimand와 허용오차에서 독립 재현.
- \`validate-current\`: 현재 contracts와 changed surface 검증.
- \`science-synthetic\`: 새 seed/held-out/mutation/coverage.
- \`science-observed\`: admitted data와 별도 authorization이 있을 때만.
- \`native\`: genuine native artifact가 있을 때만.

### 6.2 Per-PR runner에서 capability manifest로

현재 \`scripts/codex_harness\`에는 다수의 one-off \`run_pr*.py/.sh\`와 literal SHA pin이 있다. 이들을 일괄 재작성하지 않는다.

새 manifest는 다음 capability를 선언한다.

- owner와 changed surface
- required environment/optional dependencies
- input identity와 replay grade
- focused/adjacent/contract/metamorphic/statistical/CAS/data/native lanes
- expected skip/abstain 사유
- claim ceiling
- output receipt와 invalidation edges

Legacy runner는 얇은 wrapper로 새 capability ID를 호출하거나 archive-only로 남긴다. PR-124처럼 frozen pin을 유지하면서 exact typed successor를 허용한 패턴을 일반화한다.

### 6.3 CI와 GitHub ruleset

항상 required:

- DAG/schema/status mirror
- owner/claim/transfer firewall
- frame/unit/congruence/branch/order/missingness contracts
- changed-surface focused tests
- generated artifact freshness
- frozen-history mutation guard

조건부 required:

- theory 경로 변경 시 signature/proof/CAS adjudication
- statistics 경로 변경 시 seed/coverage/multiplicity/weak-ID
- data 경로 변경 시 admission/null/covariance
- native 경로 변경 또는 native claim 요청 시 native gate

scheduled/nightly:

- broad full suite
- multi-environment/package replay
- 장시간 synthetic/E2E simulation
- 외부 서비스 및 large-data replay

외부 서버 불가용을 unrelated contract PR 전체의 실패로 만들지 않는다. 다만 해당 data/native claim을 요청하는 PR에는 fail-closed gate가 계속 적용된다.

GitHub의 strict required status check는 target branch 최신화를 요구해 더 많은 build를 발생시키고, loose mode는 build를 줄이는 대신 통합 실패 위험이 있다. 따라서 publication/claim-bearing branch는 strict, 일반 개발 branch는 changed-surface 조건부 check와 merge queue를 사용하고, required check는 예상 GitHub App source에 결박한다.  
출처: [GitHub ruleset documentation](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)

GitHub Actions artifact digest 검증은 전송된 bytes의 무결성 증거일 뿐 과학적 타당성 증거가 아니다.  
출처: [GitHub Actions artifact documentation](https://docs.github.com/en/enterprise-cloud@latest/actions/tutorials/store-and-share-data)

## 7. 재실행 work packages

아래 ID는 제안용이며 canonical DAG에 아직 등록된 PR 번호가 아니다.

| 순서 | Work package | 주요 산출물 | 완료 조건 |
| ---: | --- | --- | --- |
| R0 | Canonical replan & snapshot repair | 222-card 기준 status/claim snapshot, wave 28~53 metadata 보완, failure taxonomy | DAG/mirror byte consistency; stale 199/147 snapshot 제거 |
| R1 | Hermetic environment & baseline | exact/scientific/current profiles, dependency lock, sharded failure inventory | pytest/optional-dependency preflight; broad failures 전부 owner+class 배정 |
| R2 | Multi-axis gate lattice | 새 state/receipt schema, legacy adapters, policy migration | permanent boundary는 hard fail, dischargeable blocker는 evidence path 보유 |
| R3 | Capability harness successor | manifest runner, legacy wrapper map, path/risk CI | current PR 247~260 preflight green; frozen history 불변 |
| R4 | Proof obligation adjudicator | 123+28 record별 statement/evidence/adjudication | 53 migration-pending signature 처리; bulk promotion 0건 |
| R5 | Current synthetic replay | PR-261~272 replay, PR-273 old exact replay + fresh blind challenge | coverage/multiplicity/misspecification/weak-ID/open-set preregistration 통과 |
| R6 | Data admission successor | PR-151 terminal check, release registry, PR-274 재-admission, 별도 authorization | partial bytes 0; admitted input마다 완전한 identity |
| R7 | From-raw extraction | CF4·Planck·DESI·ACT·JWST typed feature/state products | raw→selection/mask/frame/units/transfer lineage 완전 |
| R8 | Null/covariance calibration | matched mocks, E2E, cross-covariance, finite-sim uncertainty | null/cov/multiplicity/negative-control receipt |
| R9 | MIO/HTT replay | vector/tensor MIO diagnostics와 별도 HTT likelihood/refit | MIO posterior leakage 0; PPC/LOOCV/coverage/partial-ID |
| R10 | Cross-survey/local-global | response rank, principal angles, identified sets, depth tomography | held-out source/systematics injections, mandatory abstention |
| R11 | Independent reproduction | 다른 구현·환경, blind hostile challenge, unblinding | source identity·scientific reproduction·exact replay를 분리 보고 |
| R12 | Regenerate publication surfaces | PR-275 atlas/report/figures/replication package, manuscripts | 모든 숫자 generated source 보유; claim ceiling 준수 |

의존관계는 \`R0 → (R1,R2) → (R3,R4) → R5 → R6 → R7 → R8 → R9 → R10 → R11 → R12\`다. R6는 PR-151이 끝나기 전까지 admission 준비까지만 수행한다.

## 8. 현재 vector/tensor replay spine

1. \`PR-247~260\`: publication integrity, typed statistical foundations, predecessor contracts, chronology/DAG를 재검증한다.
2. \`PR-261\`: raw typed component에서 \`JointAnisotropyState\`를 다시 만든다.
3. \`PR-262 || PR-263\`: tensor functional/anchor와 orbit/action/parity/strata를 병렬 재계산한다.
4. \`PR-264\`: vector/tensor \`x,Q,F,G_F\`를 재계산하고 scalar view는 regression-only로 비교한다.
5. \`PR-265 || PR-266\`: typed law를 가진 \`Pi\`, depth/mask/transport/coherence를 재실행한다.
6. \`PR-267 → PR-268\`: type report와 theorem registry를 재생성한다.
7. \`PR-269 → PR-270\`과 \`PR-271 → PR-272\`: Pillar T/CAS와 Pillar S/statistical validation을 병렬 수행한다.
8. \`PR-273\`: 과거 pack exact replay와 새 독립 blind challenge를 분리한다.
9. \`PR-274\`: 완전한 candidate만 admission한다. 실행 허가는 별도다.
10. \`PR-275\`: 모든 upstream freeze 뒤 마지막으로 생성한다.

Git의 우연한 branch ancestry보다 canonical semantic DAG를 우선한다.

## 9. 관측 데이터의 from-scratch 규칙

모든 관측 lane은 다음 순서를 공유한다.

\[
\text{authenticated release}
\rightarrow
\text{selection/mask/frame/units/transfer}
\rightarrow
\text{feature extraction}
\rightarrow
\text{null/covariance}
\rightarrow
\text{joint vector/tensor state}
\rightarrow
\text{functional/orbit/depth diagnostics}
\rightarrow
\text{MIO diagnostics}
\rightarrow
\text{HTT inference}
\rightarrow
\text{legacy scalar pushforward}
\]

- 과거 derived table, covariance, null distribution, posterior, figure의 숫자를 새 분석 입력으로 사용하지 않는다.
- scalar \`x,Q,Pi,F,G_F\`는 마지막 compatibility/pushforward lane이다.
- mask, selection, sky convention, frame, averaging scale, transfer가 바뀌면 downstream을 전부 무효화한다.
- covariance-null residual과 supported score를 섞지 않는다.
- estimated covariance uncertainty, same-data cross-covariance, finite-mock uncertainty를 포함한다.
- local/global/systematics response가 약하게 식별되면 set-valued result 또는 abstention을 낸다.
- 분석 계획, threshold, multiplicity family, seed, holdout, negative control을 unblinding 전에 고정한다.

## 10. 과거 work-unit 처분 요약

| 범위 | 기본 처분 |
| --- | --- |
| PR-000~118 | harness/contract 재검증. frozen bytes 보존. scalar/null/cov/inference/feature/figure 과학 산출물은 현 통계로 재실행. |
| PR-119~143 | authority·theory·statistics를 typed state에 맞춰 재유도/재심사. PR-143 등 synthetic 결과는 fresh replay. |
| PR-144~158 | CF4·Planck·DESI·ACT·JWST·cross-survey를 admission 후 원자료부터 전면 재실행. |
| PR-159~166 | genuine native delivery 전까지 dormant. proxy 금지. |
| PR-167~184 | proof/oracle은 재심사, PR-172는 repair, PR-176~181 data/stat outputs는 재실행, hypothesis/native 상태 유지. |
| PR-185~208 | completed foundation은 재검증, pending science는 current base에 재기획, PR-198~206 data/inference는 from-raw/full refit. |
| PR-209~228 | governance/theory 재검증·재심사; PR-221/224/226/227의 data/cross-survey 결과 재실행; reports 재생성. |
| PR-229~246 | native programme dormant. |
| PR-247~258 | current preflight foundation. proofs 재심사, synthetic response/morphology/open-set benchmark fresh replay. |
| PR-259~275 | 현재 authoritative upgrade spine. 261부터 파생량 재계산, 269~272 adjudication, 273 fresh blind, 274 admission, 275 last. |

모든 222개 work unit별 현재 상태, disposition, phase, 시작조건, 가능한 최대 claim ceiling은 동봉된 \`HTT_PR_RERUN_MATRIX_20260802.csv\`에 있다. 366개 GitHub publication/review record의 별도 lineage role은 \`HTT_GITHUB_PR_PUBLICATION_INDEX_20260802.csv\`에 있다.

## 11. 즉시 해결할 구체적 하네스 부채

1. \`docs/generated/status_snapshot.json\`과 claim ledger의 199/147 기준을 222/170 canonical source에서 재생성한다.
2. \`artifact_gate_outputs.yaml\`의 “completed면 diagnostic/native blocker” blanket default를 다축 state와 typed blocker로 교체한다.
3. \`StatusSnapshot\`의 blanket \`smoke_tested=false\`를 실제 receipt binding으로 대체한다.
4. REV-R084 legacy theorem registry는 historical authority로 격리하고 v3 proof programme를 막지 못하게 한다.
5. generic semantic guard 자체는 non-claim-bearing diagnostic으로 유지하되, downstream 전체의 claim ceiling을 결정하지 않게 한다.
6. exact current-file SHA pin은 frozen release에만 쓰고 live authority는 typed successor edge를 사용한다.
7. PR-151 watcher의 hardcoded host path는 live acquisition이 끝날 때까지 건드리지 않는다. terminal 이후 archive하고 portable successor를 만든다.
8. broad suite의 모든 실패를 다음 중 하나로 분류한다: \`semantic_regression\`, \`stale_fixture_or_byte_contract\`, \`packaging/install\`, \`optional_dependency_guard\`, \`data_unavailable\`, \`external/native_unavailable\`, \`historical_expected_failure\`.
9. 분류되지 않은 실패가 남아 있으면 promotion을 금지한다.
10. smoke/fast는 root marker filter가 아니라 versioned explicit path manifest로 실행하고, 별도의 active-import lane으로 좁은 테스트가 숨길 수 있는 import 회귀를 잡는다.
11. package portability gate는 유지한다. PR-124 receipt는 packaged resource로 만들거나 portable registry construction과 repository authority adjudication을 분리하되, receipt 부재·변조 시 authority 승격은 계속 fail-closed다.
12. broad-suite waiver는 touched import graph, shared contract, claim firewall, package lane이 모두 통과하고 나머지 실패 fingerprint가 명백히 unrelated일 때만 focused development에 허용한다. publication/release에는 waiver를 금지한다.

## 12. Kill switches

- statement, assumptions, frame, units, branch/order 또는 input identity가 adjudication 뒤 바뀌면 승격을 즉시 무효화한다.
- required CAS axis가 없거나 contract가 다르면 exact/CAS 승격을 막는다.
- conditional/restricted/partial/inconclusive qualifier가 사라지면 publication gate를 실패시킨다.
- held-out leakage, seed/threshold 사후 변경 또는 disclosed truth를 새 blind evidence로 부르면 synthetic 승격을 무효화한다.
- data/mask/covariance/selection/license/transfer/completeness 중 하나라도 없거나 PR-151 partial bytes가 들어오면 admission을 거부한다.
- 별도 실행 승인 없이 관측 계산이 시작되면 산출물을 non-claim-bearing으로 격리한다.
- external artifact를 native라 부르면 provenance hard fail이다.
- MIO가 posterior/evidence/truth를 내면 ownership hard fail이다.
- scalar 또는 feature diagnostic을 geometry/family 식별로 서술하면 claim review hard fail이다.
- generated report가 stale이거나 숫자를 수작업 수정하면 publication hard fail이다.

## 13. 실행 체크리스트

- [ ] R0 replan card를 canonical DAG에 등록
- [ ] exact/scientific/current 환경 profile과 lockfile 작성
- [ ] 현재 broad failure 전수 분류 및 owner 지정
- [ ] multi-axis gate/receipt schema 확정
- [ ] legacy runner·SHA pin·frozen artifact disposition graph 생성
- [ ] PR-247~260 preflight
- [ ] 53개 migration-pending signature 처리
- [ ] 123+28 obligation record별 adjudication
- [ ] PR-261~272 current replay
- [ ] PR-273 exact replay와 fresh blind challenge
- [ ] PR-151 terminal completeness 확인
- [ ] PR-274 re-admission과 별도 execution authorization
- [ ] 관측 lane 원자료 재추출·null/covariance·full refit
- [ ] independent reproduction 및 unblinding
- [ ] PR-275와 모든 manuscript/figure 마지막 재생성

## 14. 산출물

- \`HTT_HARNESS_GATE_RETROTRACE_PLAN_20260802.md\`: 본 계획
- \`HTT_PR_RERUN_MATRIX_20260802.csv\`: 222개 internal work-unit 전수 처분표
- \`HTT_GITHUB_PR_PUBLICATION_INDEX_20260802.csv\`: 366개 GitHub PR publication/review record 전수 인덱스
