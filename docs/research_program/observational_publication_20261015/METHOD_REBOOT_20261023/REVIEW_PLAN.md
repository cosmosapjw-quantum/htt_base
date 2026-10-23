# R24 연구 실행계획 독립 검토

검토자: `/root/r24_dag_audit` · 2026-10-23. 범위: README, 방법론 frontier, 로컬 Codex 인계의 실행 가능성·상태 보존·연구/수용기준 분리. **판정: PASS_SCOPED_RESEARCH_PLAN.** 현재 검토본에 열린 blocking finding은 없다. 이는 계획 검토이며 production 설치, 실제 48-task 재가동, 원래 scientific acceptance, 논문 readiness의 PASS가 아니다.

## 검토한 정확한 파일

| 파일 | SHA-256 |
|---|---|
| `README_KO.md` | `2c198924df262473662d7748b247fbd08e13602337d8b25131df615490ee8fb6` |
| `METHOD_FRONTIER.json` | `e8f41d4947c7b90a6b31e557e2a3dc08e5ed50401c3636edeeb947c8832107c2` |
| `HANDOFF_PROMPT_KO.md` | `02a0bf844c08467f19981f3491b7549b0a58307ea54dd78fd2b768380e4f3e89` |
| `inputs/MODEL_TO_DATA.md` | `2f1a636a88d43bcc95bd00f2e7327509032dcd1d1d4683b5a67ebd68ab724a99` |
| `HARNESS_FIXTURES.py` | `8d642f94af8f924ab1d486b24047b3f720cf7e33aa67abc6a8711ccc116ed2f0` |

현재 controller·builder의 기준 source는 `cosmosapjw-quantum/htt_base@cd2bf729f12a4229f0bb423850372a511dcff78b`다. 이전 독립 감사에서 읽은 pinned AGENTS와 repo `htt-dag-orchestrator`, `htt-claim-firewall`, `htt-claim-provenance-ledger`를 적용했다. 다른 검토자의 수학적 최종 판정에 의존하여 이 계획 판정을 내리지 않았다. 수식 자체의 재심사·문헌 신규성 전수조사는 이번 범위가 아니다.

## 핵심 확인

- 원래 external-output **17/42**, analytic alternate **18/42**, 원래 V03 외부 history 미충족이 유지된다. 새 과업의 `promotes_original_acceptance`는 모두 false다. 새로운 결과가 원래 계약을 만족할 때만 정확한 objective/acceptance/prerequisite mapping을 검토한다.
- 기존 **48-task state를 재초기화하지 않는다.** 원래 task와 packet, 결과, one-use/ultra, R23-COMMON-E1/R23-Q, R9/UNKNOWN을 보존하는 append 계획이다. 실제 state에 아직 append했다고 주장하지 않는다.
- `MODEL_TO_DATA.md`는 외부 provider가 물리 전달 소비 경로에만 선행하며 관측 morphology·local boost·거리 보정의 보편적 선행조건은 아니라고 명시한다. 새 계획은 이 독립 진행 원칙을 복원한다. full `(x,F,Π,Q,G_F)`, 원 벡터 또는 `(Y₀,ΔY)`, 전체 cross covariance, singular/undefined strata를 보존한다.
- confidence image에는 같은 state–nuisance–anchor–remainder 신뢰사건이 필요하다. 새 jet나 외부 물리 응답을 같은 frame/covariance라는 이유만으로 그 사건에 붙이지 않는다. 기존 R9 alpha의 사후 전용을 금지한다. 새 depth 기각 검정을 실제 구현할 때에는 원 R9 문서의 제품 내 사전 배분·전체 scan calibration 규칙이 계속 적용된다.
- `METHOD_FRONTIER.json`은 **계획 스키마**다. `implementation`, `observational`, `statistics` 같은 kind를 현 controller enum으로 오인하지 않도록 `lowering_contract`가 존재하며, 실제 acceptance/input_identity/owned_paths/repair와 `theory/numeric/code/input`을 bind한 후 append한다. 존재하지 않는 명령을 이미 설치된 것으로 안내하지 않는다.
- 첫 묶음에 같은 cohort의 거리 모델 비교, 기존 CMB tensor 실험과 작은 controller 패치가 함께 있다. HARNESS 결과는 packet 출력만으로 완료되지 않으며 PR-R24-A에 실제 소비 작업 `R24-DISTANCE-MODELS`가 포함된다. 입력 접근이 실패하더라도 그 정확한 원인만 기록하고 독립 실행 가능한 연구를 계속한다.
- `all/any`는 같은 의무의 필요조건/충분한 대안에 적용한다. 서로 다른 estimand를 OR로 합쳐 원래 claim을 통과시키지 않는다. 실패를 밝혀 완료된 연구 작업과 qualified confidence bundle을 구별한다.
- **두 방법 실패는 재계획 신호이지 연구 종료 상한이 아니다.** 새로 판별 가능한 방법·가정·관측량·반례가 있으면 계속하며, 동일한 실패의 이름만 바꾼 반복은 막는다. 내 이전 감사의 two-method parking 제안은 이 owner 지시에 맞게 정정했다.
- profile은 권장 배정이며 실제 가용성/observed identity가 아니다. 인계문은 launch 전에 현재 host의 정확한 model/effort capability를 확인하고, requested와 observed를 분리하며 근거 없는 runtime 관측은 UNKNOWN으로 남긴다.

## 발견 후 닫힌 실무 finding

| Finding | 초기 문제 | 최종 closeout |
|---|---|---|
| P1: checkout 정책 충돌 | handoff가 별도 `branch/worktree` 사용을 함께 권장 | 기존 primary checkout 안에서 branch 사용. 새 worktree는 이후 owner의 명시적 예외 없이는 금지 |
| P2: native 순서 오류 | 구현 raw result 뒤 record 전에 별도 review를 배치 | 구현 `spawn→ack→raw result→record→next`로 review packet을 얻고, 독립 reviewer의 `spawn→ack→raw result→record→next`를 별도 수행 |
| P3: 실행 스키마 불명확 | 계획 kind/필드가 현 controller 입력과 다름 | `direct_controller_input:false`, lowering 계약과 실제 입력/수용기준/소유 경로 binding 명시 |
| P4: protocol-only 완료 위험 | HARNESS의 소비 결과가 packet만으로 표현됨 | 실제 named consumer 결과 또는 source-specific 입력 실패 판별 필요. PR-A task 목록에 소비 작업 포함 |
| P5: capability 오인 | 권장 profile과 실제 지원 여부의 구분 부족 | 현재 정확한 host capability 확인을 routing 전에 요구 |
| P6: R9 링크 이동성 | 로컬 패키지에서 저장소 상대경로 해석이 어려움 | README가 pinned GitHub 경로로 연결. 원래 상대경로는 저장소 배치에서는 유효했음 |

## 실행한 검사

1. JSON을 실제 파싱하고 12개 task ID의 유일성, `requires` 식의 구조, leaf 참조의 존재, 순환 부재를 검사했다. 결과: `FRONTIER_STRUCTURE_PASS 12 tasks`.
2. 모든 task가 `PROPOSED_NOT_APPENDED`이고 원래 acceptance 자동 승격을 하지 않는지, state 재초기화 금지와 계획의 직접 controller 입력 금지, PR-A의 named consumer 포함을 검사했다. 통과했다.
3. `PYTHONDONTWRITEBYTECODE=1 python HARNESS_FIXTURES.py`를 실행했다. 두 embedded source의 Git blob SHA가 pinned 파일과 일치함을 먼저 검증하고 네 동작을 독립 in-memory fixture로 재현했다:
   - transport만 복구한 같은-input 재개 거절 및 HOLD 유지;
   - 두 enabling action이 AND로 처리되어 충분한 한 대안의 완료만으로 ready가 되지 않음;
   - identity label만 바꾼 재개 수용;
   - 같은 input/같은 미소진 repair를 사용한 재개 수용.

결과는 `PINNED_BEHAVIORS_REPRODUCED`, checks=4다. router와 receipt 함수는 명시적인 fixture stub이다. 실제 native agent, 원자료 receipt, scientific acceptance를 가장하지 않는다. 이 스크립트는 **이전 구현의 문제 재현**이며, 미래 수정된 controller의 회귀검사를 대신하지 않는다. 실제 패치에는 현재 수정 소스를 대상으로 하는 별도 focused regression tests가 필요하다.

## 실질적 제한과 다음 행동

계획의 12개 task는 모두 아직 runtime 미추가 상태다. 실제 자료 경로, source release, row/frame/units, covariance 중복, 파일 소유권, 허용 profile은 로컬 host가 각 실행 직전에 구체화해야 한다. 이 검토는 그 자료가 현재 owner cache에 존재하거나 이미 정상 실행된다는 증거가 아니다.

다음 행동은 작은 패치만 반복하는 것이 아니라 **기존 checkout에서 최소 append/obligation/resume 수정을 검증하면서 같은 cohort의 거리 비교 또는 독립 CMB tensor 계산을 실제 판별 결과까지 진행**하는 것이다. 한 제품의 법칙이 적격하면 그 제품의 full functional bundle을 완성한다. 다른 제품의 full source가 없다는 이유로 기다리지 않는다. 반대로 조건부 가정, 선택 이후의 exploratory 상태, 부족한 common-mode law, finite-domain 한계는 그 결과에 그대로 남긴다.

이번 검토에서 production controller/state, Git, 원자료와 기존 scientific 상태는 변경하지 않았다. 새 검토 계층이나 추가 전역 gate를 제안하지 않는다.

## 최종 한 필드 동기화 closeout

초기 검토 frontier의 SHA-256은 `0e3d256d8c792a30d478f56176d80fc342b169a4e7893751dedca3cfb47590c4`였다. 이후 `continuation.escalation`을 이미 검토한 handoff와 맞춘 현재 frontier `e8f41d4947c7b90a6b31e557e2a3dc08e5ed50401c3636edeeb947c8832107c2`를 대상으로 **그 routing/전이 의미만** 추가 검토했다. 현재 12-task JSON은 정상 파싱되며 계획 상태·17/18 기준·원래 state와 one-use/R9/UNKNOWN 보존이 유지된다.

새 문구는 현재 host의 정확한 model/effort capability 확인 → 구현 `spawn/ack/raw-result/record/next`로 review 예약 → 별도 reviewer의 같은 실제 전이 → shared one-use 및 requested/observed 구분을 명시한다. 기존 handoff와 일치한다. 결과: `SCOPED_ESCALATION_DELTA_PASS`; 전체 판정은 **PASS_SCOPED_RESEARCH_PLAN**을 유지한다.

README, handoff, HARNESS_FIXTURES의 SHA-256은 위 최초 검토값과 같음을 확인했다. frontier는 JSON 직렬화도 바뀌었으므로 이전 파일과의 bytewise equality나 한 필드 외 모든 byte의 diff 검증을 주장하지 않는다. 이 closeout은 원래 수학·자료·전체 계획을 다시 감사하거나 production 실행을 재인증한 것이 아니다.
