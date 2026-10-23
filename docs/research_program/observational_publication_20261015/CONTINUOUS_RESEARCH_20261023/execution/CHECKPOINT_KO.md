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

## 검토를 마친 새 결과: R23-DISTANCE 및 atlas intake

- [실제274행 조건부 거리 fit](R23-DISTANCE/conditional_fit/REPORT.md)은
  7열 설계·267자유도, 한 개의 명시적 공동 covariance 아래 실행했다.
  354개의 미관측 거리는 undefined로 유지했다. 4096개 공동 그룹 mock의
  조건부 구간 coverage는3890/4096으로 사전 범위3854–3926에 들었다.
- 실제 자료의 잔차 진단 T=4.5553218238, p=0.0009763241396은
  **채택한 조건부 모형을 비판한다**. 이 실패를 유지했고 모형·seed·허용오차를
  조정하지 않았다. 측정 폭0.1dex의 조건부 contrast는0.082865876mag,
  해당 모형의 구간[0.021790086,0.143941666]mag다. 실제 모형 진단 실패로
  이를 경험적으로 검증된 구간이나 물리 TFR/H0/PV 추론으로 사용하지 않는다.
- 공개 modulus 오차가 이미 선폭·보정 계수 오차를 전파한다는 원 논문
  Appendix C를 반영했다. 사용한 공동 calibration 배분과 단일 그룹 잔차는
  명시적 working assumptions다. source-qualified calibration/PV 법칙은 미확보다.
- 새 코드·숫자·그림,3 tests와 별도 Astra의
  [독립 eigenvalue/SVD 검토](R23-DISTANCE/conditional_fit/INDEPENDENT_REVIEW.json)를
  완료했다. candidate는 dddb9635d8d761aa0ac194f93546f86da61f03a5ac6598f1e9df71843bd8c0ff.
  최초 미평가 candidate·실패·중간 packaging seal은 모두 보존했다.
  authored conditional 실험의 완료이며 원래 H02/S02는 HOLD다.
- [Atlas source intake](R23-ATLAS/REPORT.md)와
  [별도 독립 검토](R23-ATLAS/INDEPENDENT_REVIEW.json)는 기존10개 source receipt를
  재사용했다. 새 숫자 atlas나 새 과학 계산은 없다. 확인한 Sung71항목은
  64그림+7TeX/style이며, registry11종은 all-m T/E/B 자격이 없다.
  source별 확인 범위를 넘는 보편적 부재를 주장하지 않는다. B02는 HOLD다.

PUBLICATION_DAG의 H02/S02/B02에는 위 참고 근거만 연결했다.
원래42개 state/acceptance/dependency/output 및 CONTINUATION_TASKS는 유지했다.

## 검토·targeted closeout을 마친 새 결과: R23-CMB

- 같은 관측 하늘의 retained PR3 L128 Eℓ2–4에서 HM/OE 차이의 공동 span을
  계산했다. 기존45개 window cell을 재실행하지 않고 새15개 projection 지점만
  계산했다. 두 nuisance 방향 rank2, α=0,0.25,0.5,0.75,1을 고정했다.
- 원 window에서 그 span의 power 비율은0.07664763244다. α0→1의
  alignment²는0.67950074→0.45631847이다. 20deg/30deg의 power 비율은
  0.096857252/0.018694186이다. 30deg에서는 axis 변화가 비단조다.
  이 값은 실현 하나의 기하학이며 stochastic covariance나 calibrated p가 아니다.
- [코드·수치·그림·보고서](R23-CMB/REPORT.md)를 첫 독립 reviewer가 재현했다.
  공통 성분과 전체 결정론적 차이의 상쇄를 혼동한 한 문장을 수정했고,
  [같은 reviewer의 targeted closeout](R23-CMB/REVIEW_TARGETED_CLOSEOUT.json) 및
  [최종 candidate 독립 검토](R23-CMB/INDEPENDENT_REVIEW.json)를 완료했다.
  수치 재실행 없이8개 payload는 byte-identical임을 확인했다.
  원래 candidate와 finding은 PRE_WORDING_REPAIR/REVIEW_INITIAL에 보존했다.
  최종 candidate022d91f327ddadb05159f748dbd56a64d47c678cf1c8f234ac3115a87967acae.
- 공통 foreground와 cross-noise/weights의 source law 및 statistic-specific
  null coverage는 미확보다. PR4 ordering 변환만으로 CMB+residual 합성이
  정당해지지 않으며 별도 PR4 분석을 원래 PR3 L03 완료로 바꾸지 않는다.
  PUBLICATION_DAG의 L03에는 참고 근거만 연결했다. 원래 acceptance는 HOLD다.

## 다음 실제 전이

로컬 `.agent-harness/runtime/r23-continuous/STATE.json`은48-task 원본과
packet/실제 agent/result, 첫 실패, 이전 ultra 사용을 보존한다. 재초기화하지 않는다.
현재 R23-Q와 R23-DISTANCE는 scoped 독립 검토 후 완료했다.
R23-CMB의 새15개 projection 지점은 독립 검토에서 재현됐으며 한 문장을 고친 뒤
같은 reviewer의 targeted closeout과 controller final-candidate 검토를 완료했다.
K03은 Marcori et al. arXiv1805.12121v1을 이용한 새 해석적 응답을 유도하고,
기존755850행에서 새 교차 통계량을 단1회 계산했다. 실제 rank6·조건수7.32446,
principal angles43.855/44.092/44.292deg이나 formal Rnorm(b)958.89로
small-velocity 물리 해석은 불가하다. 별도 독립 검토 전이며 원래 K03는 HOLD다.
H02와 S02의 실제 acquisition은 필요한 source law와 physical joint response를
확보하지 못해 정확한 입력 HOLD를 기록했다. source law·source null·parent targeting을
새 working covariance로 대체하지 않는다. 지금 L03 acquisition packet3ea648d69d772951을
실제 gpt-6-sol/high `/root/rc_3ea648d69d772951`에 호출·ack해 원래 PR3 null 입력을
조사한다. 그 뒤 K03의 독립 물리/수치 검토와 남은 DAG 분기 점검을 계속한다.
R23-ATLAS와 의존성이 풀리는 원래 노드도 router 순서로 이어간다.

```bash
.venv/bin/python scripts/codex_harness/research_controller.py --state .agent-harness/runtime/r23-continuous/STATE.json summary
```

running packet은 기존 agent/result와 reconcile한다. 완료된 실제 결과를
record한 다음 `next`의 정확한 spawn_args를 실제 호출하고 ack한다.
이 문서는 전체 완료 선언이나 외부 제약 최종 판정이 아니다.
requested model/effort와 실제 backend 관측은 다르며, 후자는 UNKNOWN이다.
