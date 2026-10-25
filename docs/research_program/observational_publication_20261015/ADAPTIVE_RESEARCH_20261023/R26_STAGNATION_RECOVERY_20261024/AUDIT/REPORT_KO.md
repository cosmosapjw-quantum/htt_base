# 원래42 DAG 정체에 대한 독립 적대 감사

**판정: 원래 과학 acceptance의 새 완료는 확인되지 않았다. 주된 원인은 계산량 부족보다 목표와 실행 경로의 불일치다.** 원래 입력을 채우지 않는 조건부 문제를 계속 완료하고, 특정 방법의 실패를 원래 목표의 필수 의존성으로 고정하며, 이미 복구 불가능한 실행 계약의 증거를 반복 보완하는 구조다. 그러나 “아무 연구도 진행되지 않았다”는 주장도 틀리다. 실제 자료 취득, 조건부 모형 비교, 부분식별 구간, 실패·비식별성 결과가 생겼다. 이 유효한 결과와 원래6편/42조건의 달성을 구분해야 한다.

요청: 별도 `gpt-6-astra/ultra`. **관측 runtime: UNKNOWN.** 이 감사는 프로젝트 하네스·skill을 실행·import하거나 PASS를 판단 기준으로 사용하지 않았다. JSON/텍스트·읽기 전용 Git·원시 실행 receipt·일차 문헌을 직접 읽었다. 수치 재실행, bulk download, 하위 agent, 소스/STATE/Git 수정은0이다. 초기 독립 판단을 먼저 동결했고, 이전 standalone 전략 감사의 verdict는 읽지 않았다. 전략 문서가 인용한 과거 감사 주장은 감사 대상의 진술로만 취급했다.

**집계가 설명하는 것과 설명하지 못하는 것**

감사 시작 snapshot은 완료44/전체75, held10, 명목 ready20, running1이다. 완료44에는 상속된18개가 포함되며, 상속분을 제외한 실행 완료는26개다. 원래 수용은 external17/42, V03 analytic alternate를 포함하면18/42다. 새 원래 수용 증가는0이다. 명목 ready20개를 현재 의존성과 독립적으로 대조하면 선행조건을 모두 충족한 작업은0개였다. 원래 남은 경로는 S02→S03→S04→S05→S06, H02→H04→V04→V05→V06, H02→H04→K04→K05→K06처럼5단계다. H02는9개, L03은6개 원래 후속 노드에 영향을 준다. 이것은 구조적 길이·영향 범위이며 실행시간 추정이 아니다.

현재 controller의 원래 완료 수치는 immutable 원본 snapshot의 `completed_scoped`를 세고 `UNCHANGED_NOT_GRANTED_BY_CONTROLLER`라고 반환한다([코드913–944행](/home/cosmosapjw/Dropbox/bianchi/htt_base/scripts/codex_harness/research_controller.py:913)). 따라서 그 숫자가 고정됐다는 사실만으로 연구 무진전을 입증할 수는 없다. 이번에는 실제 root HOLD, 새 계약, 저장된 결과도 대조했다. 그 대조에서도 원래 acceptance를 새로 만족시키는 데이터·모델 연결은 찾지 못했다. 새 조건부 결과를 원래42에 합산했다는 증거는 없다. 오히려 계획은 두 집계를 명시적으로 구별한다. 문제는 **두 집계를 구별하면서도 원래42를 닫는 실행 전이를 마련하지 않은 것**이다.

**가장 중요한 원인**

1. **선택한 방법이 원래 목표의 필수조건으로 변했다.** 원래 H04는 H02·H03을 요구하지만 실행 spec은 `R23-SN`도 AND로 요구한다. V04에도 같은 SN 작업, S04/K04에는 `R23-CONGRUENCE`가 추가됐다. 특정 SN010010 producer parity가 실패하면 다른 적격 데이터법칙으로 H04를 충족할 가능성까지 막힌다. controller는 실제로 모든 추가 dependency의 완료를 요구한다. 단, 지금 H02 자체도 미충족이므로 이 edge 문제만 고친다고 H04가 PASS하는 것은 아니다. 기존 frozen task를 덮어쓰기보다, 대체 경로가 **동일 원래 의무**를 충족할 때 그것을 소비하는 명시적 전이가 필요하다. 다른 estimand를 OR로 묶어 통과시키는 방식은 허용되지 않는다.

2. **유효하지만 원래 gate를 닫지 못하는 결과에 작업이 집중됐다.** R24/R25의27개 새 작업 중23개가 완료됐다. Gaussian/Haar reference, tensor image, bias frontier, source tag는 실제 방법 연구다. 예를 들어628행 중354행의 미정의 결과 때문에 경험적 event 비율의 최소 구간 폭이 **354/628=0.5636942675**라는 결과는 실질적이다([원시 결과](/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/METHOD_EXECUTION_20261023/selection_envelope/RESULT.json)). 그러나 이것은 physical x_C의 posterior가 아니며 physical unknown mass는1이다. 많은 관측 view, 더 정밀한 같은 조건부 tail, quasar 분류 tag는 common-congruence response나 실제 선택·공분산법칙을 대신하지 않는다. 이 차이를 아는 controller가 원래42 완주를 계속 실행 약속처럼 유지한 책임은 크다. 다만 소유자가 새 방법 연구도 허용했으므로 조건부 연구 자체를 무단 범위 이탈이라고 판정하지 않는다.

3. **실제 규모 실행의 병목을 source review가 대신하지 못했다.** 감사 도중 full7의143GHz 첫 projection이4GiB를 넘었다. `wait4` 최고 RSS는 **4,300,365,824B**, 관측 `/proc` HWM은4,296,433,664B, 해당 phase83.62초, 종료코드−9다([원시 receipt](/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/run/RAW_RECEIPT.json)). 이는 **CODE/RESOURCE_LAYOUT 실패**이며 데이터나 물리 가설의 기각이 아니다. supervisor의 상한 감시·종료·reap은 옳았다. 코드에는 NSIDE2048 전체 Q/U double buffer만805,306,368B, FITS column reference와 추가 half-map 복사가 있다([422–453행](/mnt/extdrive/workdir/htt_open_data/r26_full7_preparation/full7_consumer.py:422)). 정확한 allocation 순간은 기록되지 않아 원인 지점을 단정하지 않는다. 작은27개 controls의 통과가 실제50,331,648pixel 가능성을 보장하지 않았다는 점은 확실하다. 동일 packet의 실패를 기록하고, 완료된 support와 누적 사용량을 보존해야 한다.

4. **절차상 HOLD의 복구와 과학 연구가 뒤섞였다.** distance 비교는20-fit cap인데 최초 실패 뒤 retry까지 최소21회가 수행됐고, staged4는 원래 최고 RSS 증거가 없으며, Gaia tag 작업은 요구된 pre-PM 통제의 원래 실행 증거가 없다. 이 역사 조건을 현재 검산이나 새 hash로 복구할 수 없다. 기존 HOLD를 보존하는 것은 맞지만, 저장된 수치 자체가 거짓이라고 확대하거나 같은 역사 상태를 계속 구제하는 것도 잘못이다. 해당 receipt는 terminal operational HOLD로 남기고 허용되는 사후 기술 결과의 사용범위를 별도로 결정해야 한다. 독립 검토가 실제 결함을 잡았으므로 검토 자체를 제거할 근거는 없다.

**원래42는 현재 조건으로 모두 달성 가능한가**

그 보장은 불가능하다. B02에는 실제 polarized family/mode atlas가 필요하며, 현재 payload 없이 내부 solver/ODE를 금지한 조건에서는 생성할 수 없다. V03의 제한된 analytic history가 유효해도 원래 external history를 충족하지 않는다. L03·H02·K03·S02에는 계산을 더 하는 것만으로 식별되지 않는 source law/response가 남아 있다. 동시에 “진짜 법칙을 외부 생산자가 완제품으로 주기 전에는 아무 모델 연구도 못 한다”는 해석은 과도하다. 명시적 근사 모델·적용 범위·residual bound를 실제 source에서 검증하는 경로는 열려 있어야 한다.

| 원래 root | 지금 가능한 일 | 지금 완료를 막는 것 |
|---|---|---|
| S02/S04 | 같은 target의 정당화된 좁은 functional/outer set; 기존 실제 부분식별 결과의 범위 결정 | apparent coefficient/628 residual를 physical signed x_C로 바꿀 source/frame·remainder 법칙 없음 |
| L03 | 실제 full-mission FFP와 처리 민감도 연구 | 원래 joint split·foreground·weights·selection law와 해당 통계의 coverage 미충족 |
| H02 | 공개 contributor subset의 source-null 모델 검증 | 전체CF4 method/group/shared calibration·선택법칙 및 matched mocks 미충족 |
| K03 | 공개 nonradial/observer response의 source-specific 검증 | quasar centroid→matter 및 target congruence·cross-source covariance 연결 미충족 |
| B02 / external V03 | 자격을 갖춘 기존 외부 payload 수용 | 현재 payload 없음; synthetic/internal evolution 대체 금지 |

[Planck VII](https://arxiv.org/html/1906.02552v2)는 실제 공개 FFP CMB/noise를 full-mission weights로 처리하고 재조합한다. 이것은 자료가 없다는 주장을 반박하지만, 새 통계의 잔여 foreground·split selection 법칙을 자동 보증하지 않는다. 기존8쌍 pilot은 이미 있으므로 그것을 다시 실행하는 것은 진전이 아니다. [CF4 estimator 연구](https://arxiv.org/html/2306.11269v2)는 전체CF4/6dFGSv/CF4TF mocks를 요청 제공으로 설명하고 공개SDSS mocks를 별도로 가리킨다. [Gaia observer acceleration 연구](https://arxiv.org/html/2012.02036v1)의 물리 response도 실재하지만, 이를 이 프로젝트의 common-congruence four-acceleration A_a로 바로 옮길 수 없다.

**권고하는 다음 세 행동**

1. **현재 full7 판별 계산부터 끝낸다.** 같은 operator·support·sentinel·canonical coefficients·cap 아래 memory lifetime/streaming만 한 번 수리한다.143GHz의 이미 사용한187.58초를 보존하면900초 cap까지712.42초가 남는다. 다른 제품별 잔여량은 [REPLAN.json](REPLAN.json)에 있다. 완료된 support를 새 의미 없이 다시 계산하지 않는다. 결과는 E-fit/B-heldout 잔차와 실제 처리 민감도 결론으로 소비한다. 작은 잔차가 physical null을 인증하지 않으며, 미제공 noise/error law 없이 큰 잔차를 물리 가설 기각으로 쓰지 않는다. 재차 cap/control 실패 시 멈추고 같은 task/budget을 rename하지 않는다.

2. **이미 있는 실제 부분식별·음성 결과를 한 개의 제한된 결과물로 완결한다.**628/274 결과, covariance에 따른 비교 반전, optical uncertainty와 공개SN277 총 공분산 결과를 재사용한다. P1의 허용된 좁은 functional과 같은 estimand인지 한 번 판단하고, 일치하지 않으면 별도 empirical methods 결과로 명시한다. 새 catalogue pass나 같은 fit 반복은 필요 없다. 원래 S02–S04를 자동 승격하지 않으며, physical unknown mass1과 미측정Q anchor를 유지한다. “다음 sensitivity node”를 끝없이 만드는 대신 이 질문의 결과를 끝낸다.

3. **H02의 실제 공개 source-null 경로를 좁혀 검사한다.** 기존 intake가 가리킨 Zenodo6640513는 v1.0.0이다. 생산자는 corrected specObjID를 가진 **[v1.1.0/6824749](https://zenodo.org/records/6824749)**를 권고하며,20.2MB catalogue·284MB randoms·10.6GB mocks와 작은 설명서를 공개한다. 우선 설명서와 실제CF4 contributor/group를 release-consistent하게 연결한다. 초기 검사는 metadata와 필요한 catalogue≤32MiB, 새fit0으로 제한하는 것을 권고한다. source/operator가 맞을 때만 정확한 subset null 재현을 별도로 예산화한다. 전체CF4 law로 확대하지 않는다. 이번 감사의 설명서 요청은429였으므로 본문은 검증하지 않았고 재시도·bulk download도 하지 않았다. 전체 archive를 먼저 받으라는 권고가 아니다.

즉시 보장할 **새 원래 노드 완료 수는0**이다. 그 사실을 숨기기 위해 acceptance를 낮추거나 denominator를 바꾸면 안 된다. 권고는 원래 ledger를 보존하면서 실제 정보를 바꿀 경로만 원래 수용에 연결하고, 현재 가능한 방법 결과에는 명시적 종료점을 두는 것이다. 원래42에 대한 새 승격은 해당 결과가 원래 objective·acceptance·prerequisites를 실제 충족할 때만 판단한다.

94 packet 중 review40·execute30·repair12·acquisition7·research5를 확인했다. 그러나 그 개수로 벽시계 낭비율이나 billed tokens를 계산할 수 없다. framework의14,968,847-token/34,734-second 수치도 실제 model identity나 요금 증거가 아니다. compaction·강한 모델·동시 실행 정책이 주된 원인이라는 정량적 주장은 이 자료로 지지하지 않는다. 이번 감사 역시 한 slot을 점유하고 Gaia preparation을 미뤘다. **이 감사의 후속은 위 연구 행동이며, 또 하나의 전면 감사가 아니다.**

42개 모두의 원문 acceptance·의존성·결손·최소 행동은 [REPLAN.json](REPLAN.json),7개 finding과 최소 반증 조건은 [FINDINGS.json](FINDINGS.json), exact source hashes와 일차 출처는 [EVIDENCE_BINDINGS.json](EVIDENCE_BINDINGS.json)에 있다. 이 결과는 프로젝트 하네스 PASS나 과학 admission이 아니다.

초기 기록 정정: 동결된 `INITIAL_FINDINGS_FROZEN.json`의 `v03_external_not_met:false`는 필드명을 반대로 붙인 오류다. 값은 원본의 긍정형 필드 `original_external_output_satisfied:false`를 옮긴 것이다. 초기 파일은 수정하지 않았으며 [별도 정정](INITIAL_FINDING_LABEL_CORRECTION.json)을 남겼다. **V03 외부 payload는 미충족, external17/42·analytic18/42**가 정확한 해석이다.
