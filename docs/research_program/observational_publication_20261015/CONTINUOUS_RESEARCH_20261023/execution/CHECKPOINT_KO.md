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

## 검토를 마친 새 결과: R23-Q 및 R23-CONGRUENCE

- R23-Q는 기존 full/margin sufficient statistics의 해시를 확인하여 계산했다.
  catalogue를 재구축하지 않았다. signal rank18, nuisance rank84이며 여섯
  contrast가 추정 가능하다. 고정 Gaussian score의 paired l4/template controls는
  full973/1024, margin965/1024다. 같은 잡음으로 구성한 두 주입은 독립 실험이 아니다.
  과거 l4 291/1024와 template0/1024 실패는 유지한다.
- [코드·보고서·그림](R23-Q/REPORT.md)과 별도 Astra의
  [독립 검토](R23-Q/INDEPENDENT_REVIEW.json)를 완료했다.
  23 tests와6 subtests, 독립 QR/SVD reference가 통과했다.
  candidate16580ce01d8a2c7c448793f7a3b58e1dc649b418ec151c8f6913787f2117ce8d.
  이는 고정 선택 행·공급한 공분산 아래 조건부 결과다. sourcewise selection,
  경험적 공간 공분산, 실제 cosmic/NNR/clock 응답은 미확보다. K03/K05는 HOLD다.
- R23-CONGRUENCE는 고정 reference의 응답 B=h−A와 같은 매개변수가 만드는
  U=J_m−D_H J_H−D_D J_D를 유도했다. A가 nuisance 공간에 속하는 같은 행·metric에서는
  B와h의 quotient가 같다. 이는 제한된 모형의 항등식이며 새 empirical rank가 아니다.
  [보고서·유리수 반례 그림](R23-CONGRUENCE/REPORT.md)과
  [독립 검토](R23-CONGRUENCE/INDEPENDENT_REVIEW.md)를 완료했다.
  author9개 및 independent9개 exact residual은0이다. candidate
  196386fd0664bbd0a4ed0db37d91aedb2226f6573e3817fb6519420a46e604b6.
  empirical processing Jacobian과 물리 remainder bound는 미확보이며 K04/S04는 HOLD다.

PUBLICATION_DAG에 K03/K05 및 K04/S04의 참고 근거만 추가했다.
원래42개의 상태·수용기준·의존성과18/42 대17/42 구분은 그대로다.
scoped frontier PASS로 원래 scientific 완료 수를 올리지 않았다.

## 다음 실제 전이

로컬 `.agent-harness/runtime/r23-continuous/STATE.json`은48-task 원본과
packet/실제 agent/result, 첫 실패, 이전 ultra 사용을 보존한다. 재초기화하지 않는다.
현재 R23-Q는 scoped 독립 검토 후 완료했고 R23-CMB는 별도 독립 검토 대기다.
R23-DISTANCE는 정당한 조건부 평균·공동오차/부분식별 모형의 Astra 연구 대기다.
K03 acquisition packet3b2331050b0548e1을 실제 gpt-6-sol/high agent
`/root/rc_3b2331050b0548e1`에 호출·ack했다. Marcori et al. arXiv1805.12121v1의
direction/redshift drift를 이용한 새 해석적 물리 응답 경로를 조사한다.
PM/NNR/clock 유도는 연구 가능한 경로이며 입력 부재만으로 소진되었다고 보지 않는다.
R23-ATLAS와 의존성이 풀리는 원래 노드도 router 순서로 이어간다.

```bash
.venv/bin/python scripts/codex_harness/research_controller.py --state .agent-harness/runtime/r23-continuous/STATE.json summary
```

running packet은 기존 agent/result와 reconcile한다. 완료된 실제 결과를
record한 다음 `next`의 정확한 spawn_args를 실제 호출하고 ack한다.
이 문서는 전체 완료 선언이나 외부 제약 최종 판정이 아니다.
requested model/effort와 실제 backend 관측은 다르며, 후자는 UNKNOWN이다.
