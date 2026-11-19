# R79 · R78 SQ-01–10 사전 코딩 연구 C1–C10 종합 보고서

작성: 2026-11-19 KST. 기존 연구 브랜치 research/r69-observable-physics-bridges-20261118. 입력 기준 HEAD 35b4bfc0759ede4cbda552c1516c37e7da06fb30, 최초 과학 통합 정본 R78 revision 3. 이 작업은 **과학 DAG를 실행하기 전** 1–10번째 source-qualification 노드의 계산 코드에 대한 사전 구현·가속·검증이며, 노드의 실제 과학적 소스 자격이 통과했다는 뜻이 아니다. 기존 42개 논문 과학 노드와 현재 R78 60-node/129-edge 상태는 모두 변경하지 않았다.

## 1. 실행한 열 개 프로그래밍 준비 노드

| 우선순위 | R78 노드 | 실제 구현·검증한 계산 기능 | Native 또는 기준 lane | 현재 물리학적 자료 상태 |
|---|---|---|---|---|
| 1 | SQ-CF4 | 가중 반구 1·2차 angular moment 및 radial 12-column design | Fortran ISO_C_BINDING + NumPy 기준 | CF4 exact selected 35,970-group indicator/PV 공분산 자격은 미완; 현재 외장 source path 차단 |
| 2 | SQ-GAIA | Gaia correlated per-star 2×2 GLS 16D weighted Fisher, score, chi2 | C++17/OpenMP, source-certified default auto | 원래 R69 source-fit과 192-patch 재현 완료. 실제 물리적 normal shear/omega 변환 미정; 현 원본 path 차단 |
| 3 | SQ-RADIO | 안정적인 185 ring log-sum-exp conditional occupancy F 및 beta-score | NumPy vectorization | 기존 R65/R74 원시선택 광원 점유율·기울기 재현, 물리적 3D beta와 LSS null 부재 |
| 4 | SQ-FRAME | SO(3) STF5 공변 변환 및 Bianchi Lie Jacobi | NumPy | 정상계와 observer/emitter source frame 공통 물리 전달은 미정 |
| 5 | SQ-P1-ANCHOR | 전체 Gaussian ellipsoid support (Cholesky) | NumPy/SciPy | P1 물리적 anchor/positive scale 미확정 |
| 6 | SQ-CMB-NULL | Welford–Chan sample mean/covariance streaming | NumPy | 실 CMB Commander matched T/E/B Monte Carlo 입력 없음 |
| 7 | SQ-PHOTON-FLUX | 광자 PSD stress/flux admissibility | NumPy symmetric eigenvalue | R66 실제 stress만 확보; 독립 photon flux 미측정 |
| 8 | SQ-LIE-FLUX | 일반 Class A/B Lie–Codazzi 3×5 map, Jacobi Na=0 | NumPy | 독립 정상계 rho,j,pi 미관측; native Bianchi solver 별도 금지 |
| 9 | SQ-OPTICAL | 2×2 Sachs/Jacobi fixed-affine optical tidal ODE RHS | SciPy solve_ivp | 실제 finite-z source/observer Jacobian/Einstein 동역학 미완성 |
| 10 | SQ-CROSS-COV | 공동 Gaussian Schur covariance와 source cross term 보존 | SciPy Cholesky | 실제 CF4/Gaia/radio/CMB 상호 공분산 미확보 |

각 노드는 C10_NODE_MATRIX.json에 Python API, 구현 상태, 출처 기반 수치 근거, 현재 block/dependency를 machine-readable로 보존했다. 실제 R78의 READY 상태와 과학적 claim gate는 변경하지 않았다.

## 2. 구현물과 자동 기본 lane

- htt/obsstat/pre_dag_fast.py: 열 노드 계산 API 및 명시적인 가속/NumPy 선택, thread-local backend receipt.
- htt/obsstat/analysis_lane.json: 실험적으로 검증된 certified native kernel의 SHA256, 최소 source 행 수, 기본 thread 수, NumPy fallback, 강제 native error 정책.
- htt/obsstat/native/vsh_normal.cpp: source별 완전한 2×2 correlated astrometric covariance를 보존하는 C++17 OpenMP fused Gaussian normal equations (F,b,chi2), 1/4/8 threads 검산.
- htt/obsstat/native/hemisphere_moments.f90: ISO_C_BINDING Fortran 가중 방향 분포의 2개 반구 1·2차 모멘트. Kahan 방식의 수치 누적.
- scripts/r67/gaia_frame.py: 기존 가속 진입점 자동 연결, 변경 전 정확한 독립 NumPy 코드는 accumulate_numpy로 명명하여 유지. 새 기초 물리 분석에서 써야 할 source-signature는 바꾸지 않았다.
- scripts/r79: 명시적 임시 native build, 원래 source benchmark, 원래 full Gaia source replay, 물리·통계 검산 코드.
- tests/obsstat/test_pre_dag_fast.py: 원래 reference와 native 비교, 고장·변형 source SHA 검출, cache binary integrity 및 native failure state 검사.

지원되는 source 연산의 기본 lane은 auto이며, C++/Fortran source SHA 및 binary manifest를 확인해 안전한 native를 사용한다. 기존 NumPy를 강제하려면 HTT_ANALYSIS_BACKEND=numpy, 인증 native를 필수로 사용하려면 HTT_ANALYSIS_BACKEND=native를 지정한다. 지원되지 않는 대상은 기존 NumPy/SciPy 경로로 남기며, native 원본 소스가 바뀌어 인증이 성립하지 않거나 compiler/binary가 없으면 auto가 원래 NumPy로 명시적으로 전환한다. native 계산 도중 반환 오류·비유한 값은 대체 실행으로 조용히 덮지 않고 실패 사유를 남기고 예외 처리한다. 바이너리는 Git에 commit하지 않고 /tmp에 compiler/source SHA별로 보존한다. 저정밀 fast-math나 CUDA/AVX512 종속 강제 구현을 사용하지 않았다.

## 3. 실제 속도와 원본 수치 검증

초기 기준: 원래 Gaia FITS 첫 60,000행 중 59,279개 품질 통과 sample의 기존 16D NumPy GLS 약 0.07078초(3회 중앙값). 첫 행들은 하늘이 한쪽에 몰린 **원래 catalog 정렬** 때문에 cond(F)≈866,184였고, 원래 double F 상대 차이가 6.17e-15임에도 해 오차가 1.53e-9로 증폭되는 것을 확인했다. 이에 따라 원래 FITS 전 범위에서 균등 row-stride를 사용한 별도 benchmark의 cond(F)≈8.06으로 통제했으며 기준 정확도는 완화하지 않았다.

동일 original Gaia source의 균등 row-stride, 원래 NumPy GLS와 똑같은 in-memory 행렬/오차, OpenBLAS=1 조건:
- 원본 Gaia 60k행→58,750 quality, 5회 중앙값 C++1 ≈1.95배, C++4 ≈6.97배, C++8 ≈9.72배 빨랐다.
- 원본 120k행→117,462 quality, 3회 중앙값 C++8 ≈9.99배 빨랐다.
- 실제 CF4 table4 40–400 Mpc group sample 31,649개, Fortran 반구 모멘트가 NumPy 대비 약 2.61배 빨랐다.
- Gaia 원래 F, score, chi2, fitted coefficients, inverse covariance and minimum eigenvalue 모두 동등 source에서 상대 차이 최대 약 2.08e-14 이하였고, CF4 반구 moment 차이는 최대 약 5.68e-15였다.

위 수치는 **메모리에 올라온 수학 커널의 중앙값 속도비**이며 FITS 읽기·template 생성·192-region patch·전체 observer astrophysics inference의 가속비는 아니다. auto 인증 SHA/manifest 검사 추가 후의 end-to-end 배속을 추정하거나 별도로 측정하지 않았다.

## 4. 원 자료 재현 및 정확성

C7에서 실제 가용했던 Gaia-CRF3 FITS **1,614,173 원본 source, 1,580,645 quality**를 65,536행 청크로 전부 처리하여 기존 R69 16D 결과의 최대 상대 차이 4.18e-13, 192-region patch covariance 상대 차이 1.29e-14를 확인했다. source SHA는 원래 R69 receipt와 일치했고 해당 검산 산출물 C7_GAIA_FULL_REPLAY.json에 보존되어 있다. C7_PHYSICS.json은 원래 R74 NVSS source 185-ring F 및 beta 기울기 최대 차이 약 5.56e-16, R66 PR3/PR4 photon PSD, R75 exceptional VI-1/9 rank2와 SO3 covariance, R61 11D joint ellipsoid, Sachs flat/constant Ricci 광학 테스트를 재현했다.

C9 적대적 감사에서는 source SHA 인증을 kernel 이름으로만 cache하여 소스 변조를 못 알아차리는 문제와 원래 NumPy reference 테스트 별칭을 가속 함수로 잘못 연결한 문제를 실제 red-green 테스트로 발견·수정했다. 이제 native SHA와 binary manifest를 매 호출 확인하며, runtime error를 성공한 backend로 기록하지 않는다. 174개의 관련 기존·신규 회귀 테스트와 R78 strict graph/authority 32개 검사가 통과했다. 이 결과는 repo 전체 테스트 PASS가 아니다. R78 이전의 별도 legacy 8개 테스트 실패는 R78/REGRESSION_RECEIPT.json이 관리하며 이 연구 범위에서 수정하거나 완료로 간주하지 않는다.

**현 실행환경 차단:** C9에서 추가 전체 Gaia FITS 읽기를 시도할 때 기존 /mnt/extdrive/workdir/raw 외장 source 경로가 없어 FileNotFoundError가 발생했다. 그 당시 NTFS source disk UUID 장치는 존재했지만 원래 자료 path가 가용하지 않았다. 해당 차단은 이론/수치 오류와 구분해 C9_ADVERSARIAL_REVIEW.json에 보존했다. 이전 C7과 C8의 실 source 실행 결과는 유효한 historical input receipt로 남기되, 원자료가 없는 지금 다시 실행해서 PASS했다고 주장하지 않는다. 승인된 환경에서 원본 drive path 접근이 복구되어야 새로운 SQ-CF4/SQ-GAIA source study가 가능하다.

## 5. 다음 단계, 범위·중단조건

C1–C10은 코드 및 안정성/가속 사전 준비라는 한정된 작업으로 완료된다. 실제 과학 DAG의 NEXT_ID=SQ-CF4는 변하지 않는다. 새 데이터 분석은 인증 auto native를 기본 선택하되, 실행할 실제 source original ID·covariance·source frame과 finite-z physics는 각 SQ node의 acceptance gate를 별도 통과해야 한다. SQ-P1-ANCHOR, SQ-CMB-NULL, SQ-PHOTON-FLUX, SQ-LIE-FLUX는 여전히 미확보 source가 있고, SQ-OPTICAL과 SQ-CROSS-COV도 물리적 선행조건이 필요하다.

다음 bounded 물리 계산은 원래 외장 source가 접근 가능해졌을 때 정확한 **CF4 35,970 selected source IDs**와 indicator/PV/selection covariance를 재구성하는 일이다. R77의 table4 full 38,053 그룹을 CF4 selected likelihood와 동등 표본으로 대체하거나, R78 science statuses를 전부 completed로 변경해서는 안 된다. H04/P3의 물리적 cosmological expansion claim은 본 사전 코딩 작업만으로 성립하지 않는다.
