# PR-MES-I3-SCREEN — I3 조건부 입력 screening 등록

2026-09-28. Owner HTT; claim ceiling C0 `DIAGNOSTIC_ONLY`; transfer source 없음. 사용자 요청으로 기존 `main`에서 별도 I3 연구 입력을 등록했다. 정규 DAG의 PR-190은 R9의 기존 formal run과 결합된 후속 작업이다. 이 카드는 완료된 `PR-REPLAN-20260927`에 의존하는 독립 문서·경량 대수 검증 가지이며, PR-190/R9 실행이나 상태를 대체하지 않는다.

원본 I3 ZIP 4개 member의 CRC/SHA와 I1/I2/R3 참조 원문 SHA를 확인했다. 원본은 byte-preserved로 등록하고, Fermi/catalog frame을 혼용한 forward relation, 누락된 field 표시 및 catalog 시간 적합 response를 `REPORT_KO.md`에서 정정했다. 현재 관측 후보 Gaia-CRF3는 같은 congruence의 distance, source motion, frame calibration, cross-source covariance, selection response와 Taylor remainder가 없어 `HOLD_INPUT_INCOMPLETE`다. I2의 radiation-only Bianchi I 결론은 `DEFENDED_CONDITIONAL` 그대로다.

## 검증

- Wolfram exact symbolic: 전천 bilinear/회전 직교 및 tilt Gram 잔차 0. 원본 raw와 이번 범위별 재검산을 `VALIDATION_KO.md`에 기록했다.
- SymPy 1.14.0: 네 잔차 0; Sage: 네 identity True; Singular: determinant 0/pass. Singular 첫 명령은 괄호 해석 오류로 실패했고 수정본을 재실행했다.
- Lean 4.31.0/mathlib: 구면 moment를 가정한 계수 환원과 determinant 증명 컴파일. Optical transport, 구면 moment 자체, 자료법칙은 증명 범위 밖이다.
- Gaia 공식 schema, Gaia-CRF3 원 논문, I1/I2/R3 근거를 대조했다. 관측 row/likelihood는 실행하지 않았다.
- `python3 -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice` 및 canonical/mirror 검사를 실행했다.

## 검토와 잔여 위험

Host의 한 차례 범위별 수학·단위·frame·claim self-review에서 두 표기 오류와 catalog 시간 적합 response 누락을 수정했다. 별도 I3 독립 decision reviewer 및 등록된 동일 CAS 계약의 4축 판정은 없으므로 formal/physical admission을 내리지 않았다. 네 도구에서 통과한 이상적 전천 대수는 mask와 nuisance 공분산 아래의 관측적 직교 또는 식별을 뜻하지 않는다. 생산 코드, R9 상태, 사용자의 기존 수정은 변경하지 않았다.

다음 소비 결정은 같은 source/observer congruence의 거리와 유효 window, 운동·frame·systematic 공동법칙, 원 covariance와 selection response가 실제로 확보된 후에만 가능하다.

## 5-PR checkpoint

진행 도구의 현재 결과는 완료 155/209 = 74.16%, dependency-weighted 79.97%다. 변경 package는 연구 문서·검산 스크립트와 DAG mirror이며 production 과학 모듈은 그대로다. DAG harness 42개 테스트가 통과했고 무거운 solver/ODE, empirical likelihood와 전체 suite는 이 문서 범위에 없어 실행하지 않았다. 금지 claim 문구 scan에서 신규 파일의 위반은 없었다. Subagent는 사용하지 않았다. 다음 정규 DAG node는 PR-190이지만 기존 R9 run의 formal/lifecycle 장애가 남아 있어 이 I3 진척으로 해소되지 않는다. I3의 관측 입력 결손은 위에 열거했고 새 replan edge는 만들지 않았다.
