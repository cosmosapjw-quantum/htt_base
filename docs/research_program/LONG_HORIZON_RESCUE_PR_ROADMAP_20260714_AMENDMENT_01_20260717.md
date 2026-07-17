# LONG_HORIZON_RESCUE_PR_ROADMAP — AMENDMENT 01 (2026-07-17)

| 항목 | 값 |
|---|---|
| status | `PROPOSED_ONLY_NOT_IN_ACTIVE_DAG` (원문과 동일) |
| amendment-of | `docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md` |
| authority | `docs/audits/shared_context_cas_harness_final_audit_20260717/` (root adjudication `ADJ-ROADMAP-001`: targeted amendment, full regeneration 금지) |
| scope | 네 곳의 최소 line edit + 이 amendment 문서 하나. 다른 어떤 절도 재생성하지 않음 |
| claim tier | diagnostic_only / process governance. 과학 finding·claim state 변경 없음 |

## 개정 1 — §4.5: 7단계 = lifecycle checklist (7-agent 의무 폐지)

7-step typed pipeline은 *lifecycle checklist*로 유지하되, "각 단계를 별도
subagent로 실행"하는 고정 의무를 폐지한다. 실제 agent 수는 위험도별 예산을
따른다 (audit §6):

| 위험도 | 예시 | 기본 agent 예산 | 테스트 예산 |
|---|---|---:|---|
| R0 mechanical | 문구, 비실행 metadata | 0 (optional) | changed-file lint/schema |
| R1 harness | hook, assignment, packaging | 최대 2 targeted | harness unit/negative + 1 E2E receipt |
| R2 scientific non-CAS | numerical/statistical contract | 최대 4 (서로 다른 claim/failure class) | targeted property/mutation + smallest smoke |
| R3 CAS mandatory | CAS가 필요한 수학·물리 명제 | **4 axis slot 예약** (optional review와 별도) | 4 axis receipts + targeted checks + snapshot당 1 integrated gate |

R3의 네 축은 비용 압력으로 한 agent에 합치거나 세 축으로 줄이지 않는다 —
slot이 부족하면 일반 mapper/reviewer를 줄인다. custom profile 사용은
launcher receipt(`.agent-harness/scripts/launch_receipt.py`)로 attestation하고,
미attestation agent는 `generic_prompted` + `correlation_group=parent_llm`으로
강등한다(독립 reviewer 중복 계상 금지). shared context는 정확히 한 번 전달한다
(hook 주입 또는 file fallback; `.agent-harness/README.md`).

review wave 추가 조건(audit §6): 새 evidence class, 달라진 failure hypothesis,
또는 evidence fingerprint를 바꾼 patch — 이 세 경우에만 추가한다. 같은 diff와
같은 질문의 "final/recheck/attempt N" 반복은 금지하며, 두 wave 후 같은 P1이
반복되면 reviewer를 늘리지 않고 root가 scope 축소/revert/block을 결정한다.

## 개정 2 — PR-124: "Dual-engine" → "Four-axis CAS contract + derivation-lineage oracle"

PR-124 카드 제목과 DoD의 "dual-engine"을 four-axis CAS contract로 교체한다.
계약·adjudication 구현체는 `.agent-harness/templates/CAS_CONTRACT.json`(v2),
`.agent-harness/templates/CAS_AXIS_RESULT.json`,
`.agent-harness/templates/CAS_ADJUDICATION.json`,
`.agent-harness/scripts/cas_gate.py`다. 명시 원칙: **네 engine의 agreement와
최소 두 개의 실제 독립 derivation lineage는 서로 다른 지표다** — 같은 AST를 두
backend에서 평가한 것은 여전히 derivation 하나이며, 네 축 agreement는 유도
독립성을 대체하지 않는다. `scripts/run_egs3_v9_seals.py`는 legacy diagnostic
runner이며 four-axis gate가 아니다(Makefile `v9-seals` 주석 참조).

## 개정 3 — §17.1: every-PR full collect/smoke → targeted + receipts

매 PR 고정 의무를 targeted PR selector + 가장 작은 관련 smoke + exact test
receipt 재사용(`.agent-harness/scripts/test_receipt.py`)으로 낮춘다. full
collect-only/smoke 전량 실행은 five-PR checkpoint, packaging/collection 영향
변경, release snapshot에서 한 번씩만 수행한다. 예외: CAS가 필요한 PR(R3)은
언제나 네 axis receipt 전부를 요구한다.

## 개정 4 — §20/§21: historical plan 고정 + live SSoT 포인터

§20--§21을 PR-119 intake 이전의 historical plan으로 고정한다. 살아있는 상태의
SSoT는 `docs/codex_handoff/pr_status.yaml`(mirror
`machine_readable/pr_status.yaml`)과 `docs/PR_DELTAS/`이며, 이 장문 문서에
progress를 재삽입하지 않는다.

## 불변 조건

- PR4/NPIPE 데이터 부재 시 해당 lane skip 원칙은 이 amendment로 변경되지 않는다
  (다른 synthetic/proxy 성공으로 대체 금지).
- `PROPOSED_ONLY_NOT_IN_ACTIVE_DAG` 라벨, 48+17 card 구조, 8-field 양식,
  dependency 원칙, claim ceiling은 모두 원문 그대로다.
- roadmap 파일 hash pin(`scripts/codex_harness/intake_long_horizon_roadmap.py`
  `EXPECTED_ROADMAP_SHA256`)은 이 amendment와 함께 갱신되었다 — pin 갱신
  자체가 명시적 재승인 기록이며, 이 문서가 그 승인 근거다.
