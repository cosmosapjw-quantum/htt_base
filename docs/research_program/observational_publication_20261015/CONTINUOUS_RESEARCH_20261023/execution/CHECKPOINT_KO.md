# 실제 로컬 실행 checkpoint — 2026-10-23

소유자 checkout에서 PR561 기준855107f23을 fast-forward로 반영했다.
사용자의 기존 GR-statistics 변경은 보존했다. 전체42개 acceptance 목표는
활성이며, 원래42개+새 연구6개의 동일 durable campaign을 계속 실행한다.

## 검토를 마친 새 결과: R23-SN

- 공개 MODEL000 오차 격자를 전파한 23행 조건부 IRLS fit:
  χ²/19=0.8984302156. 기존 measurement-only3.2323283226 실패와 기준3은 유지한다.
- x0/x1/c/t0의 네 published-summary parity 기준은 모두 실패했다.
  IRLS 고정점은 parameter-dependent 정규화 Gaussian MLE가 아니다.
- 새 코드·수치·[그림](R23-SN/BASELINE_PARITY.png)·[보고서](R23-SN/REPORT.md),
  별도 Astra의 [독립 검토와 같은 reviewer의 그림 closeout](R23-SN/INDEPENDENT_REVIEW.json)을 완료했다.
  candidate는 ee09c46c5a8dd9c46735b73cbaf4a76357a1b956f5920c4bc4e3976f9f9b785d.
- 정확한 잔여 입력은 nominal PFITdatawithsys PS1.nml,
  out_train_v7_1_bd17fix/SALT2.MODEL000의 INFO·오차 격자,
  CID010010/IDSURVEY15의 observed PS1 FITRES와 생성 설정이다.
  고정c447 release3223항목에서 미확인이다. 다른 모든 공개 경로의 부재를
  주장하지 않는다. 원래 H04/V04 admission과 empirical κ/η는 HOLD/UNKNOWN이다.

PUBLICATION_DAG에는 H04/V04 참고 근거만 연결했다. 원래42개 state,
acceptance, dependency와 output은 바꾸지 않았다. 수정 V03 범위18/42,
원래 external-output 기준17/42, 여섯 논문 NOT_READY는 그대로다.

## 다음 실제 전이

로컬 `.agent-harness/runtime/r23-continuous/STATE.json`은48-task 원본과
packet/실제 agent/result, 첫 실패, 이전 ultra 사용을 보존한다. 재초기화하지 않는다.
현재 R23-Q와 R23-CMB는 실행 후 별도 독립 검토 대기, R23-DISTANCE는
정당한 조건부 평균·공동오차/부분식별 모형의 Astra 연구 대기다.
R23-CONGRUENCE는 실제 native agent가 read-only 이론 작업 중이다.
R23-ATLAS와 의존성이 풀리는 원래 노드도 router 순서로 이어간다.

```bash
.venv/bin/python scripts/codex_harness/research_controller.py --state .agent-harness/runtime/r23-continuous/STATE.json summary
```

running packet은 기존 agent/result와 reconcile한다. 완료된 실제 결과를
record한 다음 `next`의 정확한 spawn_args를 실제 호출하고 ack한다.
이 문서는 전체 완료 선언이나 외부 제약 최종 판정이 아니다.
requested model/effort와 실제 backend 관측은 다르며, 후자는 UNKNOWN이다.
