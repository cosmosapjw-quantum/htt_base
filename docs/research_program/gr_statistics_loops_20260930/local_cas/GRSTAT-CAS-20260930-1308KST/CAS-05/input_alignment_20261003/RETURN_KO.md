# CAS05 cubic H 입력 결속 진단 — 2026-10-03

`EXTANT_REFERENCE_RECOVERED_SPECIFICATION_INCOMPLETE`. CAS05/06 입력 admission과
scientific admission은 HOLD다. CAS04는 CAS_BLOCKED다. frozen 계약을 수정하거나
과거 CAS_CONFLICT, STOP_BUDGET, raw, usage, launch/lifecycle를 재작성하지 않았다.

## 복구한 결속과 남은 승인

허용 입력은 기존 EXECUTION_CONTRACT.json과 COMMON_SPEC.md 두 개다.
C03는 세 번째 exact statement, 실제 JSON pointer는
`/semantics/exact_statement/2`다. 그 문장이 요구하는 cubic H의 extant 문자열은
같은 계약의 `/full_theorem_boundary/uncontracted_research_targets/3`에 있다:

```text
Cubic H_ij=-deltaij x0 S_kl xk xl/2,H0i=-x0 r^2 q_i/2-r^2 W_ij xj/5 gives j2H0 and deltaG0i=q_i x0+M_ij xj
```

이 문자열은 좌표에 대해 cubic인 텐서 성분 표현이다. Tr(H³)를 공급하지 않는다.
문자열을 찾은 사실은 계약 승인이나 완전한 중립 입력 명세가 아니다. H00,
대칭 성분과 varied metric/background 정의, r²와 공간 인덱스 범위,
상수 계수의 타입·단위·sym/skew 정규화, 12개 basis 및 Bianchi 미분 차수의
실행 가능한 결속이 필요하다. BINDING.json에는 누락 필드를 null로 남겼다.
`gr/**`는 orchestrator provenance이며 blind-worker 읽기 승인이 아니다.
기존 축의 스크립트·증명을 새로운 입력의 근거로 가져오지 않았다.

후속 입력은 원문 소유자/Host가 실제 정의를 공급하고 명시적으로 승인한 뒤
별도 버전의 계약에 결속해야 한다. 기존 v2 파일·판정은 그대로 보존한다.
CAS05 C01/C02와 CAS06의 별도 입력 의무는 이번 단위에서 해결하지 않았다.

## 실제 실행과 재사용

허용된 정확한 `local_assistance route`를 실행해 기존 Devstral locator를
`USE_QUALIFIED_HELPER`로 재사용했다. 해당 qualification의 artifact SHA256
결속 12개를 확인했다. 모델 `devstral-small-2-24b`, profile
`devstral-small-2-24b-cpu`, inference `7c6dfd66614d454788ac84d1f10d21aa`,
이미 해제된 managed lease `8b73b518cc814dd896808105568379a1`이다.
기존 raw-format FAIL과 한 outer JSON fence 제거 기록도 보존했다.
validator PASS의 범위는 extant pointer/input locator뿐이다.
이번 단위의 새 과학 local 추론/lease는 0건이다. 다른 두 검증된 helper나
Qwen/DeepSeek/Kimina 실패를 반복하지 않았다.

Host는 새 `ambiguity_probe.py`를 실제 Python 3.12.3 / SymPy 1.14.0으로
telemetry 경유 실행했다. 허용되지 않은 H00 값을 승인하는 대신,
미지의 두 완성 사이에 `h00=(x1)^3` 차이가 있을 때의 flat linear jet만 계산했다.
길이 좌표에 맞추려면 비영 length^-3 계수를 함께 둘 수 있다. 이 차이는
원점 j²=0, δG0i=0을 유지하지만 δG22=δG33=−3x1로 바꾼다.
16개 Einstein 잔차, 4개 선형 Bianchi 발산, 21개 j² 평가가 정확히 0이다.
따라서 해당 조건들은 누락된 H00/full jet를 결정하지 못한다.
이는 명세 비유일성 진단이며 CAS05의 반례/축 PASS/전체 정리 증명이 아니다.

원시 실행 stdout와 call ID를 Codex 로그에서 회수해 다음 durable 기록에 결속했다:
`/mnt/sn850x2t/local_ai_foundry/70_experiments/cuhg_cas05_input_binding_20261003/`.
BASELINE.json, locator-route.stdout, ambiguity.stdout, 각 execution.json,
HOST_RUNTIME.json을 참조한다. 원 로그는
`~/.codex/sessions/2026/10/03/rollout-2026-10-03T10-13-17-01a0f99e-b90f-7182-ae90-ac4de1537118_01a0ff52-96c0-7a20-bd54-a9cda91cc3c8.jsonl`이다.

## 비용·보존·다음 작업

재사용 locator의 과거 665 tokens는 알려진 local 누계 6,038에 이미 포함된다.
coder002/coder005/DeepSeek timeline의 unknown spend는 0이 아니다.
과거 native 관측 창 29,377,902 total 중 cached input 28,277,376도 그대로다.
전체 task 역사·통화 비용 및 이번 Host/context-manager 귀속량은 NOT_MEASURED다.
과거 목표 초과나 STOP_BUDGET를 새 과학 중단으로 해석하지 않는다.

시작 HEAD는 d07d68fd9b0fbb86d2b84e834f12d317da33e918이며 설치 authority는
d32480138583652abc40efc61cbdcbcfb8a647b8로 일치했다. fetch는 HEAD를 바꾸지 않았다.
기존 tracked dirty 4개와 과학 자료 1,709개를 baseline에 결속했다.
보존/독립 검토/게시의 실제 결과는 durable closeout receipt를 참조한다.
PR-DAG rescue-card CI 실패는 base에서 재현된 기존 별도 사항이며 재실행하지 않았다.

다음 단일 작업: **H00 및 완전한 대칭 metric polynomial 정의를 명시적인 중립
입력으로 확보·승인하고, 별도 후속 계약으로 결속한다.** 그 전에는 CAS05/06
입력 HOLD를 해제하지 않는다. CAS04 Wolfram 연결 수리, completed axes,
C01/C02/C03/C04와 R9는 이번 실행 범위 밖이다.
