# R82 · R78 21–30번 코딩 연구 C1–C10 종합 보고서

**2026-11-20 KST.** 기존 연구 브랜치 research/r69-observable-physics-bridges-20261118, 시작 HEAD 74b1b61a8d71bad61cf0c56b1647c90c3e065aad. R78 과학 DAG의 기존 42개 payload, 전체 60개 node/129 edge, 291개 software PR backlog, 최초 318개 관련 없는 미추적 항목과 원 자료를 변경하지 않았어. R79의 1–10, R81의 11–20 구간에 이어 이번 21–30은 E2,E3,X01,X02,X03,S01,S02,S03,S04,S05에 대한 **사전 계산 코드 구현**이야. 이는 원래 과학 DAG의 배열 순서나 위상정렬 인덱스가 아니야.

## 1. 열 노드의 코딩 결과

| 번호 | 원래 노드 | 실제 계산·입력 계약 | 원래 과학 상태 |
|---:|---|---|---|
| 21 | E2 | Planck9 same-sky/FFP10 기존 처리·공통 마스크 26,846 pixel의 historical source hash·관측 중복 검사 | completed_scoped |
| 22 | E3 | 기존 signed samplewise statistical functional/pushforward의 독립 참조 보존 | completed_scoped |
| 23 | X01 | 6논문 source SHA/release/overlap graph 정본 확인 | completed_scoped |
| 24 | X02 | 기존 6논문 novelty comparator 문헌·estimand/source SHA 보존 | completed_scoped |
| 25 | X03 | 역사적 선택 ledger와 prospective null 미등록 상태 검증 | completed_scoped |
| 26 | S01 | 원래 P1 typed x,Q,F,Pi,G_F 제약을 기존 Python 테스트와 대조 | completed_scoped |
| 27 | S02 | C++17/OpenMP optional 공동 strict-tail, 원자료에서 더 빠른 NumPy sorted 기본경로, 결측질량 경계 | blocked_input |
| 28 | S03 | Fortran/OpenMP anchor–floor 3개 거리창 ratio/strict/tie/mean batch | pending |
| 29 | S04 | 실 physical unknown mass 1을 보존하는 수학적 lower/upper 및 누락 source 검증 | pending |
| 30 | S05 | 결과표·source provenance·재현 패키지, 논문 출판 여부와 분리 | pending |

입력은 정확한 2,048개 공동 sample ID × 네 개 겹치는 CF4 redshift window, 한 원본 가중치 1/2048이야. 원래 source 파일 CONTINUATION_20261018/P1/results/paired_functional_arrays.npz SHA256 cd38f438a0bf07385b07478c7b5c122df5af1e9bb48a5575fe1cad40ef261f27을 재확인했어. 기존 apparent q_app = ||STF5_app|| / H_app는 *working Gaussian source diagnostic*이며 물리적 x_C/U_sigma가 아니야. 물리적 Q,F,G_F는 원래 자료에서 모두 미측정/정의역 미확정, 합산 unknown mass=1이야.

## 2. 수치 알고리즘과 정확한 의미

Joint-tail: 모든 threshold에서 네 source window의 strict q_j>t, ANY, ALL을 같은 original draw ID에서 계산해. code 0은 finite known, code 1 unmeasured_defined, code 2 domain_uncertified이고 missing q에는 NaN과 typed reason을 함께 요구해. Unknown을 ±infinity의 논리적 가능성으로 처리한 weighted survival 정렬 알고리즘과 searchsorted(side=right)로 exact ties를 제외하며, 알려진 mass만 재정규화하지 않아. Lower/upper는 무제약 수학적 사건 완성의 pointwise bound일 뿐 물리적 admissible posterior는 아니며 physical_Pi=None을 유지해.

Apparent floor: g_j(B,delta)=max(A_j/B,delta)/max(A_0/B,delta)=max(A_j,B delta)/max(A_0,B delta), j=1,2,3. B·delta가 각각 양수여도 곱이 floating-point 0 또는 infinity가 되면 계산 전에 거부해. Signed STF 원소는 clip하지 않고 비음수 *apparent amplitude*에만 floor를 적용해. 이 수치는 물리적 transported G_F가 아니야.

## 3. 실제 원본 수치 결과

기존 P1 결과의 t=0.05 네 창별 strict mass: [0,0.06640625,0.59814453125,0.00537109375], ANY 0.60302734375=1235/2048, ALL 0. 신규 C++/NumPy는 원래 threshold/7-anchor 결과를 재현했고, Fortran floor는 원래 6-floor strict/tie 결과를 정확히 재현했어. 실제 source에서 native C++ strict-tail 상대오차 0, Fortran floor weighted mean 상대오차 약 4.49e-16이야. 물리적 unknown mass=1, Q/F/G_F event bound=[0,1]와 physical_Pi=None은 그대로 보존했어.

## 4. 벤치마크 및 기본 lane 선정

같은 메모리 내 원자료 2048x4, OpenBLAS=1, 5회 중앙값:

| 계산 | 기존 NumPy 반복 | 검증된 최적 경로 | 가속 |
|---|---:|---:|---:|
| 1024 strict thresholds | 0.065461 s | sorted NumPy 0.001805 s | 36.27x |
| 4096 strict thresholds | 0.263094 s | sorted NumPy 0.002384 s | 110.37x |
| 32x24 anchor/floor | 0.030032 s | Fortran 8-worker 0.001664 s | 18.05x |
| 64x64 anchor/floor | 0.154123 s | Fortran 8-worker 0.007738 s | 19.92x |

C++ 8-thread tail은 결과는 정확하지만 정렬 NumPy보다 느려 기본으로 채택하지 않았어. Fortran floor는 chunked NumPy보다 15–17배 빠르고 원본 결과를 보존해 기본 auto로 채택했어. Source+binary SHA를 매 native 사용 시 검사하고 binary는 /tmp에만 컴파일해. 실제 기본 lane 재측정에서도 4096 strict thresholds 약 81.68x, 32x24 floor 약 16.95x 가속을 확인했어. 전체 CF4 group refit, Planck map 재계산이나 물리 inference 전처리·검출까지 그 속도로 빨라졌다고 주장하지 않아.

## 5. C1–C10 증거와 판정

C1 원본 2048-joint baseline; C2 E2–S05 source/claim mapping; C3 strict mass/tie/floor 수학 및 단위계; C4 bounded implementation resource DAG; C5 TDD RED→C++/Fortran compile→16 tests PASS; C6 원 P1 12개 포함 224 scoped tests PASS, R78 32/32; C7 원본 S02/S03/E2–X03 source hash와 물리 미확인 상태 replay; C8 정확도·속도·메모리/기존 NumPy/C++/Fortran benchmark; C9 sorted NumPy 기본값과 floor overflow/underflow 방지 red-green, 총 228 scoped tests PASS, R78 32/32; C10 원본 연구 상태와 분리한 10-node software preflight machine-readable matrix, provenance, handoff 및 Git 영수증.

**과학 판정:** 이번 R82는 CODE_PREPARATION_IMPLEMENTATION_VERIFIED만 해당해. 새로운 physical x_C posterior, calibrated Planck matched null, real optical-to-kinematic frame transfer, P1 full joint source covariance, 이상도 물리적 검출 또는 S05 원고 완성은 아니다. 42/60-node DAG 상태와 NEXT_ID=SQ-CF4를 그대로 둔다. 해당 과학 source를 확보한 뒤에만 차단된 S02와 후속 S03–S05를 과학적으로 실행할 수 있어.
