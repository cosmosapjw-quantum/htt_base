# #560 이후 실제 변경 검토

검토 기준은 이전 게시 HEAD `1e095a2749cce9b28e45aac043a82218c21f84e5`와 이번 intake `4a68995507bf8e672b2551d9030f3ad9f0d2152e`이다. GitHub 최신 PR 목록상 새 번호는 없고, #560이 2026-10-18 09:49 UTC에 갱신되었다. PR 본문의 초기14/42 요약을 최신 상태로 오인하지 않았다. HEAD 비교의6커밋과 해당 과학 보고서·현행 DAG를 읽었다. 전체203개 파일을 독립 재검증했다는 뜻은 아니다.

| 커밋 | 실제 진전 | 남은 의무 / 이번 후속 |
|---|---|---|
| 5450b044 | S02 공동 보정 소거, H02 실제20방법/창 중심·중첩·공통 보정 LP | 공통 angular anchor가 없다. 이번 앵커 quotient/설계 계산으로 필요한 기하와 정밀도를 명시한다. |
| 9616f534 | 원래 native pixel support에서 Planck full/HM/OE 처리와 remainder; L01 완료 | 완료 스트림 재실행하지 않는다. CMB 추가 자료는 남은 null 입력만 취득한다. |
| 538b0f93 | parity-aware 형태 통계와 변환 검사; L02 완료 | 통계량 정의와 물리 p-value를 분리한다. |
| c0ed65c0 | Kourkchi2020 TF 원천10,737/9,792행, 7,573galaxy→6,697selected group 연결 | final accepted catalogue 밖 대상/실패 자료가 필요. 이번 Dupuy2021 GBT628대상으로 일부 해소한다. |
| 75ed2ac3 | 원래 estimator로8실제 IQU CMB/noise 쌍 처리·±5%잡음 민감도 | rank≤7,8행은 stochastic independence/coverage 증거가 아니다. Split noise URL을 이번에 직접 확인했다. |
| 4a689955 | 원래 native-child 처리를 맞춘 국소 boost 유한 응답; V02 완료 | global-history V03와 atlas B02는 별개 외부 입력이다. |

최신 canonical은17/42완료, 직접8입력 blocker(S02,S04,L03,H02,V03,B02,K03,K04), 의존대기17개다. 기존 acceptance/의존성/완료상태를 그대로 보존한다. 이 PR의 자료 접근·조건부 정리만으로 원래 과학 노드를 완료 처리하지 않는다.

## CI의 구체적 실패와 최소 수정

최신 run39116855480에서 Rust compile와 Python package smoke는 성공했다. Repository contracts는 `test_shared_context_packet_is_merged_and_versioned`의 `agents_text.endswith(fragment)`에서 실패했다:1failed/144passed/3skipped. `CI_FAILURE_EXCERPT.txt`에 실제 로그의 관련 부분을 남겼다.

원인은 authoritative AGENTS.md의2026-10-08 native 실행 설명이 호환 fragment에 반영되지 않은 것이다. **AGENTS.md는 변경하지 않고** AGENTS.md.fragment만 현재 본문의 정확한 suffix로 동기화했다. 기존 실패를 선택 파일 fixture에서 재현하고, 원래 테스트 함수 전체를 수정 없이 실행하여 PASS를 확인했다. 테스트 완화·실행 정책 변경·새 승인 절차는 없다. 전체 CI의 후속 결과는 게시 이후 별도로 확인한다.

## 이전 방법론의 재사용과 현재 한계

1. CF4의 전역 scalar 영점은 intercept 제거로 소거될 수 있으나 공통 angular 보정은 남는다. 같은 그룹의 거리차와 공개된 중첩은 상대 보정을 조사하며 절대 angular gauge를 고정하지 않는다.
2. L03에서 같은 simulation 번호를 붙이는 일과 upstream seed/cross-split 공분산을 확인하는 일은 다르다. PR3 split noise의 공개 접근 가능성은 확인했지만 HM FFP10 CMB 부재에 관한 Planck VIII 설명은 그대로 적용한다.
3. V02의 endpoint local boost와 V03의 global history는 서로 대체하지 않는다. 공개 코드나 그림을 numeric polarized atlas로 이름만 바꾸지 않는다.
4. 원래17개 완료 작업과 과거 HOLD/UNKNOWN·R9 기록은 재개하면서 보존한다. 새 입력으로 해결할 수 있는 다음 실험을 실행하고, 반복 검토만으로 연구 진척을 세지 않는다.
