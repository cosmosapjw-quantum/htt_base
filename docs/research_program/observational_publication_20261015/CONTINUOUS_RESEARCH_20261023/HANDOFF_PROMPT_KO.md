# 로컬 Codex에 그대로 전달할 연속 실행 프롬프트

```text
기존 /home/cosmosapjw/Dropbox/bianchi/htt_base checkout에서 PR561의 최신
research/htt-open-input-theory-20261018 변경을 확인하고 작업하라. 사용자 변경을
보존하고 새 clone/worktree를 만들지 말라. fetch 후 local/remote 차이를 확인하고
안전한 fast-forward가 가능하면 반영하라. reset/force/자동 main merge는 하지 말라.

목표는 원래6개 논문 DAG의42개 acceptance를 실제 근거로 충족하는 것이다.
노드 하나, 테스트 하나, 문서 하나를 마치고 종료하지 말라. 각 단계 후 dependency,
입력, scientific delta를 갱신하고 다음 ready action을 즉시 실행하라. 전체 목표는
진행률 숫자가 아니라 원래 scientific acceptance다. 원래42개 노드와18개 scoped
완료/원래 external-V03 기준17개라는 구분을 유지하라.

먼저 AGENTS.md, docs/harness/CURRENT_CODEX_RUNTIME.md,
docs/harness/CONTINUOUS_RESEARCH_CONTROLLER.md,
docs/research_program/observational_publication_20261015/CONTINUOUS_RESEARCH_20261023/
의 README_KO.md, THEORY_AND_RESULTS.md, FRONTIER.json,
REVIEW_AND_EXECUTION.json을 읽어라. physmath-research-loop와 해당 repo skills를
적용하라. 오래된 executor의 one-step 종료는 worker 경계이며 전체 run 종료가 아니다.

이미 만든 controller state가 있다면 새 run으로 초기화하지 말고 기존 packet/agent/
outcome을 먼저 reconcile해 resume하라. 처음이면 build_research_campaign.py로
원래42개와 authored frontier6개를 합친48-task campaign을 생성하라. 아래 문서의
명령은 템플릿이다. available-profile은 이 실행 환경에서 실제 지원하는 정확한
model/effort 쌍으로만 채워라. 기존 native_routing 정책과 허용 fallback을 사용하라.

실행 반복은 next → 반환된 spawn_args로 실제 native spawn → 실제 agent ID ack
→ 결과와 raw receipt record → 별도 독립 검토 → next다. planned를 dispatched로
쓰지 말라. 요청 모델과 observed runtime을 분리하고 관측 못하면 UNKNOWN이다.
parent 포함 최대4개, nested agent 금지, 파일별 한 writer, 연구/검토 agent는
read-only다. 구현·이론 기여자는 자기 산출물을 독립 검토하지 못한다.

과학적 blocker가 발생하면 정확한 실패/입력/질문을 묶고 기존 router의
review_or_research 또는 자격이 되는 blocker_escalation으로 실제 상위 모델을
호출하라. 현재 사용자는 이 solver-free 목표 내 구체적 연구·수정과 escalation을
이미 승인했다. 그 라벨 때문에 다시 승인받으려 멈추지 말라. 기존 one-use 및
동일 issue 제한은 유지하고, 새로운 repair ID로 같은 실패 예산을 초기화하지 말라.
외부 입력/전송 한도만으로 초고사고 모델을 반복 호출하지 말라.

R23-Q를 우선해 기존 a22_20261023/astrometry/full_stats.npz와margin_stats.npz를
해시 확인하고 새 finite nuisance quotient로 실제 계산하라.755850행 catalogue를
다시 만들지 말라. augmented rank/estimability와 실패했던 l4/template-mean controls,
선택 법칙 변경을 검사하라. K03의 cosmic/NNR/clock 물리 acceptance와 구분하라.
그 뒤 R23-DISTANCE, R23-SN, R23-CMB, R23-CONGRUENCE, R23-ATLAS와 새로 ready가
된 원래 노드를 의존성에 따라 계속 수행하라. 실행 가치에 따라 독립 lane을 병렬화하되
동시 writer 충돌을 금지하라. 한 lane의 외부 입력이 다른 lane을 막지 않게 하라.

공개 무인증 외부 데이터는 필요한 경우 스스로 내려받아도 된다. 다운로드 총량/파일별/
압축 해제 상한은 없다. 실제 외장하드 mount·여유 공간과2GiB reserve를 확인하고,
기존 cache/수집 영수증을 먼저 사용하라. raw data는 Git에 올리지 말라. 실제 새
source/product 가설이 없는 반복 검색이나 이미 완료한 full campaign 재실행은 피하라.

native low-ell Bianchi solver 구축, ODE/Einstein–Boltzmann evolution은 금지한다.
기존 solver-free 이론·해석적 응답·공개 existing transfer는 provenance와 가정하에
사용하라. 조건부 diagnostic, toy/control 통과, 테스트 수로 empirical coverage,
global tilt, cosmic A, Bianchi family identification을 주장하지 말라. baseline fail을
허용오차 완화로 지우지 말고 원인 자체를 수정하라.

매 완료 단위에 실제 결과·재생성 가능한 figure/report·영향받는 검사·독립 검토를
기록한 뒤 같은 승인된 research branch에 non-force push하고 PR561을 갱신하라.
원래 과학 노드가 새로 acceptance를 충족해 독립 검토를 통과했을 때는 그 근거를
PUBLICATION_DAG.json의 해당 node state/evidence와 CONTINUATION_TASKS.json의
all_original_nodes intake_state에 함께 반영하라. acceptance/dependency는 바꾸지 말라.
controller의 source_completed_scoped는 시작 시 source snapshot이므로 현재 진전과
구별하라. 새 frontier scoped 완료만으로 원래 scientific state를 갱신하면 안 된다.
진행률이 그대로면 다음 단위는 문서/해시 추가가 아니라 새로운 과학적 입력/모형/추정량
또는 실제 실행 capability를 만들어야 한다. 원래 source-bound acceptance를 바꾸려면
별도 scope decision으로 표시하고 기존 합격으로 소급하지 말라.

종료는42개 원래 acceptance가 충족되거나, 남은 모든 분기의 정확한 외부 입력·금지된
작업·실제 환경 제한을 증거로 확인한 경우에만 허용한다. 후자이면 미완료로 보고하고
exact payload/source/next command를 남겨라. READY 작업이나 연구 가능한 결함이
남아 있는데 노드 하나를 했다는 이유로 최종 답변하지 말라. 세션/컨텍스트가 끊기면
durable state와 raw receipts를 저장하고 다음 host가 같은 goal을 이어받게 하라.

2026-10-23 ChatGPT의 Desktop Commander 월간 quota는 로컬 Codex 실행 제한이
아니다. 이 transport를 재연결/재시작하지 말고 로컬에서 직접 실행하라. 코드 push와
로컬 activation을 구별하고, 실제 activation evidence 없이 켜졌다고 말하지 말라.
```

첫 생성 명령 예시다. `R23_STATE.json`이 이미 있으면 덮어쓰지 말고
`research_controller.py --state ... summary`와 현재 packet을 먼저 확인한다.

```sh
P=docs/research_program/observational_publication_20261015
R=.agent-harness/runtime/r23-continuous
mkdir -p "$R"
python scripts/codex_harness/build_research_campaign.py \
  --dag "$P/PUBLICATION_DAG.json" \
  --plan "$P/OPEN_INPUTS_20261018/CONTINUATION_TASKS.json" \
  --frontier "$P/CONTINUOUS_RESEARCH_20261023/FRONTIER.json" \
  --output "$R/CAMPAIGN.json" --state "$R/STATE.json" \
  --authorization 'Owner: whole42 solver-free DAG, autonomous research/repair and policy-eligible escalation' \
  --next --available-profile gpt-6.1-sol/medium \
  --available-profile gpt-6-sol/high \
  --available-profile gpt-6-astra/xhigh \
  --available-profile gpt-6-astra/ultra
```

이 명령 자체는 native worker를 호출하지 않는다. Codex host가 반환된
`spawn_args`를 실제 호출하고 `ack/record/next`를 반복해야 한다.
기본 parent는 기존 router의 gpt-6.1-sol/medium, 과학 구현은 지원되는
gpt-6-sol/high, 별도 이론/검토는 gpt-6-astra/xhigh, 자격 있는 고위험 과학
blocker는 gpt-6-astra/ultra를 권장한다. 실제 catalogue에 없는 프로필은
정책상 fallback만 사용하며, 위 예시를 모델 가용성의 증거로 사용하지 않는다.
