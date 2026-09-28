---
title: "HTT 전 이력 독립 감사 · R4"
subtitle: "후속 구현의 실제 성과, 남은 통계 결함, 관측 응답과 재사용"
date: "2026-09-08"
lang: ko
fontsize: 10pt
geometry: "a4paper,margin=22mm"
colorlinks: true
toc: true
toc-depth: 1
---

# 판정과 이번 조사에서 달라진 점

**프로젝트에는 재사용할 수 있는 수학·추정 연산자·관측 분석 자산이 있다. 동시에 일부 결과 생성 경로의 통계적 해석은 성립하지 않는다.** 내부의 PASS, quarantine, claim ceiling 대신 실제 함수, 수학적 정의역, 호출부, 저장 결과와 외부 원문을 기준으로 판정했다. “오래된 구현에 반례가 있다”와 “그 반례가 현재 관측 결과를 무효화한다”는 서로 다른 주장이다.

이번 조사는 GF 구간 계산의 후속 버전, CF4 추정·성장률 계열과 병렬 브랜치의 affine 추정기, N1–N5 관측 nuisance와 깊이별 후속 모형에 집중했다. 이전 감사의 적용 범위를 바로잡는 발견도 포함한다.

| 이번 판정 | 핵심 근거 | 실질적 의미 |
|---|---|---|
| 이전 GF 비판의 적용 범위 교정 | v8의 signed quotient 수리, v9 T2G 정리와 실제 호출 경로 | 이미 고친 부분을 다시 개발할 필요가 없다 |
| CF4의 유효한 후속 구현 확인 | 공유 속도장 mock, full covariance affine GLS | 독립 잡음만 쓴다는 일반 비판은 부정확하다 |
| CF4의 새로운 수학적 결함 확인 | amplitude MLE의 비단조 score, 같은 표본 추정량의 교차공분산 누락 | 해당 point estimate·비교·후속 구간을 재검증해야 한다 |
| N1–N5의 설명·생성·추론 불일치 확인 | 문헌 귀속, parity, 생성 covariance, proxy Bayes/MES 점수 | 현재 null trigger rate를 물리적 공동 분석의 보정으로 읽을 수 없다 |
| PR062의 개선과 잔여 한계 확인 | 방향·깊이·mock별 union 보존, 그러나 경험적 생성식 | 자료 구조는 재사용하고 실제 selection 응답을 연결해야 한다 |

**전수 정독은 아직 완료되지 않았다.** 이번 보고서는 전체 완료 보고서를 가장한 표본 감사를 제공하지 않는다. 뒤의 파일 목록 집계와 전문 읽기 기록으로 조사 상태를 구별한다. 과학 코드, CAS, 모의실험, 관측자료 분석은 실행하지 않았다. 인용한 수치 중 저장 결과는 기존 파일에서 읽은 값이며, 반례와 수정식은 직접 유도했다. 과학 실행은 사용자의 워크스테이션 Local Codex에 남아 있다.

# 전 이력의 조사 범위

주 기준은 handoff commit `5702024e06eff4979087f07f86ee7131d13961ac`이다. 그러나 그 시점만으로 프로젝트를 대표시키지 않았다. CF4의 병렬 후속 구현은 `analysis/mes-methodology-recovery-20260825`의 commit `5a3825f903546891fd90e3d708481707d59babf4`에서 읽었다. 해당 파일은 handoff에 없다. 각 판정의 ref와 Git blob은 별도 원장에 보존했다.

이전 확정 182개 브랜치 참조에서 도달하는 2,061개 커밋의 부모 관계와, 그 커밋들이 가리키는 **2,003개 고유 root tree의 보존 목록을 모두 대조**했다. 새로 이동한 모든 원격 ref를 재수집했다는 의미는 아니다.

| 목록 집계 항목 | 값 |
|---|---:|
| 도달 가능한 커밋 | 2,061 |
| 고유 root tree 및 확보한 목록 | 2,003 / 2,003 |
| 전 이력의 고유 blob | 18,885 |
| 전 이력의 고유 경로 | 11,379 |
| 브랜치 끝점들의 고유 blob | 8,630 |
| 끝점들에는 없고 과거 tree에만 남은 blob | 10,255 |
| 고유 blob의 기록상 byte 합계 | 722,631,354 |

여기서 blob은 같은 내용이면 경로와 커밋이 달라도 한 번만 센다. 파일의 새 버전은 별도 blob이다. 따라서 “현재 파일을 전부 읽기”와 “과거 버전까지 전부 읽기”의 작업량 차이가 크다. 위 분모에는 코드·문서·JSON뿐 아니라 이진 파일도 포함된다. Git에 추적되지 않은 원자료, 접근 불가능한 참조와 외부 output directory는 포함하지 않는다.

전문 읽기 수와 교차검토 수는 다르다. 동일 내용을 두 심사자가 읽어도 고유 blob 수는 늘리지 않는다. 부분 읽기와 변경분만 읽은 기록도 전문 읽기로 승격하지 않는다. 최종 수치는 동봉 `coverage.json`과 아래 표에 일치시켰다.

| 전문 읽기 항목 | 고유 blob 수 |
|---|---:|
| 이전까지 전문 읽음 | 162 |
| 이번에 새로 전문 읽음 | 51 |
| 누적 전문 읽음 | 213 |
| 전 이력 목록 중 읽음 | 213 / 18,885 |
| 끝점 목록 중 읽음 | 202 / 8,630 |

목록 cache는 `path / blob SHA / byte length`를 보존한다. 파일 mode와 하위 tree의 원래 레코드는 없으므로 원시 Git tree 객체의 SHA를 독립 재구성했다고 주장하지 않는다. 대신 2,003개 평탄화 목록의 모든 대응 관계를 보존하는 delta checkpoint와 정규화 manifest hash를 만들고, 원본 cache와의 일치를 검사했다. 이는 **자료 목록의 보존 검사**이며 과학 계산이 아니다.

# 연구사의 해석과 이전 감사의 교정

이전 조사에서 확인한 흐름은 초기 Rust/BASS의 CMB 전달 계산과 큰 evidence 주장, HTT의 관측 응답·다중 채널 진단, MIO의 방향·짝·형태 통계, obsstat의 부분 식별·공동 구간, tensorized MES와 Q/O 기하의 결합이다. 이번 조사에서는 이 흐름 안에 실제로 반례를 받아 정리를 고친 이력이 확인됐다.

| 계열 | 유지되는 평가 | 이번에 보완하는 평가 |
|---|---|---|
| BASS legacy | 저장 baseline에는 일부 성공과 큰 전달 오차가 공존하며, 초기 evidence와 충돌식에는 별도 문제가 있다 | 이 오래된 문제로 후기 모든 BASS 구현을 묶어 판정하지 않는다 |
| 후기 BASS·외부 donor | 유효한 dust 동역학, 일부 광학·Thomson 연산자는 재사용 후보다 | 일반 finite-tilt Einstein–Boltzmann 모형의 완결 여부는 여전히 별도다 |
| HTT 관측 진단 | 실제 Planck·ACT 결과와 재현 경로가 존재한다 | N1–N5 proxy 보정이 그 관측 분석 전체의 보정을 대신하지 않는다 |
| MIO | full Q/O·공동집합과 연결할 잠재력이 있다 | 이전에 읽은 iid reference와 순서 의존 pair 문제의 successor 전수 추적은 남는다 |
| obsstat GF | 구형 unrestricted API에 수학적 반례가 있다 | v8·v9의 실제 수리와 정확한 정의역을 인정한다 |
| CF4 | PR145–148 보존 분석은 실재하나 해석별 재검증이 필요하다 | 별도 affine GLS 구현에는 그 계열의 일부 결함이 적용되지 않는다 |

이 구분은 내부 등급을 수용해서 만든 것이 아니다. 동일한 독립 기준이 부정적 결과와 긍정적 결과에 모두 적용된다. 연구 방향의 연속성은 보이지만, 공통 이름과 공통 보고서 형식만으로 모든 계열이 같은 생성분포·물리적 모수·관측 likelihood를 공유하는 것은 아니다.

# GF: 반례가 이미 수정된 실제 경로

## v8은 signed numerator 문제를 고쳤다

구형 `egs3_gf_interval.py`는 분모가 양수라는 조건만으로 numerator/denominator 극값의 pairing을 고정한다. 이전 반례는 이 unrestricted 함수에 대해 맞다. 그러나 `egs3_gf_interval_v8.py`는 각 shared-box vertex에서

\[
\left\{N_-/D_-,\;N_-/D_+,\;N_+/D_-,\;N_+/D_+\right\}
\]

를 모두 평가한다. shared 변수가 \(N,D\)에 affine하게 들어가고, 두 잔여변수가 서로 및 shared 변수와 독립적으로 고정 구간 안에서 움직이며, 전체 유한 box에서 분모가 양수인 경우에는 signed numerator에도 올바르다. 일반 비선형·비볼록 공동집합까지 해결한다는 뜻은 아니다.

저장 seal에는 구형 구간 \([-3/5,-19/39]\), 수정 구간 \([-3/4,-19/49]\), 독립 Fraction grid의 같은 수정 결과가 있다. 양수 영역 200개와 signed containment 400개의 과거 점검도 보존되어 있다. 이번 재실행 수치는 아니다. [고정 v8 source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/obsstat/egs3_gf_interval_v8.py)

## v9 T2G는 strictness의 조건을 정확히 좁혔다

\(N(s)=s, D(s)=1+s, s\in[0,1]\)이면 joint 범위는 \([0,1/2]\), 서로 독립화한 product 범위는 \([0,1]\)이다. lower endpoint는 줄어들지 않는다. `egs3_fractional_program.py`는 이 zero-endpoint 반례를 반영하고 다음을 구별한다.

- signed domain의 일반 결론은 joint 범위의 product relaxation에 대한 포함 관계다.
- endpoint equality는 그 product endpoint를 shared 제약을 지키는 점에서 달성할 수 있을 때 성립한다.
- 단순한 argmin–argmax 교집합 corollary는 전체 box에서 \(N>0\)일 때만 적용한다. 구현은 그 전제 위반을 거부한다.

Sage source는 Charnes–Cooper 변수 \(t=1/D\), \(y=ts\) 등을 사용한 별도의 exact LP를 구성한다. 저장된 세 fixture의 15개 check는 같은 corner 함수를 한 번 더 호출한 검증보다 강한 증거다. 여전히 모든 입력·모든 실행 환경의 인증은 아니다. [고정 T2G source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/obsstat/egs3_fractional_program.py)

실제 연결은 `Makefile`의 v9 target → v9 seal runner → `fractional_program_seal` → `joint_interval / product_interval` → v8 exact 함수다. v8 수정 commit `619b9b1f…`, v9 수정 commit `55ecf558…`는 handoff의 조상이다. 따라서 **수정 파일이 고립되어 있을 뿐이라는 평가도 맞지 않는다.**

구형 experiment와 v7 witness caller도 남지만, 확인한 기본 toy는 \(N_{\min}>0\)여서 signed 반례가 그 저장 결과를 반증하지는 않는다. 정확한 잔여 문제는 “잘못된 unrestricted legacy API가 여전히 호출 가능하며 migration이 전면적이지 않다”이다. 미독 caller에 대한 전수 결론은 보류한다.

## GF의 재사용 가치

T2G는 nuisance를 공유하는 선형분수 비율의 도달 범위와 endpoint witness를 계산하는 자산이다. 이를 관측 공동집합에 연결하면 독립화 때문에 생기는 과도한 범위를 줄일 수 있다. 그러나 **입력 공동집합이 실제 자료법칙을 반영한다는 조건, 확률적 coverage, 물리적 sharpness는 별도**다. box를 정확히 최적화한 것과 관측 모수를 정확히 제한한 것은 같지 않다.

# CF4: 살아 있는 자산과 결과 경로의 결함

## 공유 속도장과 affine GLS는 실제로 구현되어 있다

PR146은 \(v=Lz\), \(LL^T=C+\epsilon I\)의 공유 속도장을 만든다. PR148도 전체 표본에 하나의 장을 생성한 뒤 깊이별로 분할·재추정한다. 저장 joint covariance에는 200 mocks에서 얻은 비대각 성분이 있다. 따라서 “독립 은하 잡음만 쓰고 shell covariance를 대각으로 놓는다”는 비판은 이 구현에 적용되지 않는다.

병렬 branch의 `cf4_current_stack.py`는

\[
v_r=r a+\boldsymbol n\cdot\boldsymbol B+r n_i S_{ij}n_j,
\qquad \operatorname{tr}S=0
\]

라는 9모수 관측식을 구현한다. 여기서 속도 gradient는 \(G=aI+S\), \(a=\operatorname{tr}G/3\)이고, \(B\)의 단위는 km/s, \(a,S\)의 단위는 km/s/Mpc다. 주어진 거리·설계와 알려진 양의 정부호 \(C\)에 조건부인 affine GLS다. 1개 trace, 3개 bulk 성분, 5개 STF shear 성분의 설계행렬, 행 ID에 결합된 full \(C\), 선택한 행의 principal submatrix \(C_{II}\), Cholesky whitening, trace를 제거한 8열 응답의 rank 검사가 있다. 별도 텐서 수축으로 합성 신호를 만드는 검사도 존재한다. [병렬 affine source](https://github.com/cosmosapjw-quantum/htt_base/blob/5a3825f903546891fd90e3d708481707d59babf4/htt/obsstat/cf4_current_stack.py)

이 연산자는 아래의 PR145 비교 함수나 PR148 amplitude solver를 호출하지 않고, toy centroid grouping도 하지 않는다. 따라서 위 결함을 이유로 affine GLS 전체를 재작성할 필요는 없다. 다만 \(a,S\)의 단위와 기준거리·기준계가 고정되어야 하며, 이 추정값이 곧 우주론적 shear tensor라는 결론에는 관측 전방식이 더 필요하다.

current-stack 관측 runner의 `--output`은 필수이고 결과가 외부 directory에 저장될 수 있다. 정독한 source·runbook·receipt 범위에서는 그 runner의 성공한 관측 결과를 고정 source identity에 연결하지 못했다. PR291의 nonexecution receipt와 PR313·314 기록도 읽었지만, 이것으로 모든 후속 외부 실행을 부정하지 않는다. 현재 판정은 **“연산자와 합성 검사 존재; 해당 경로의 관측 실행 성숙도 미확인”**이다. PR145–148의 별도 CF4 보존 분석은 존재한다.

## amplitude MLE의 단조성 전제는 거짓이다

`cf4_growth_covariance.amplitude_mle`는 \(C(A)=AS+N\), \(A\ge0\)의 whitening된 Gaussian 우도를 다룬다. \(p_i\)와 \(\lambda_i\ge0\)를 사용하면 상수항을 제외한 우도는

\[
\ell(A)=-\frac12\sum_i\left[\log(1+A\lambda_i)+
\frac{p_i^2}{1+A\lambda_i}\right].
\]

구현은 score가 단조감소한다고 설명하고 \(\ell'(0)\le0\)이면 즉시 \(A=0\)을 반환한다. 다음은 정확한 반례다.

\[
\lambda=(100,1),\quad p^2=(0,20),\qquad
\ell'(0)=-\frac{81}{2}<0,
\]
\[
\ell(1)-\ell(0)=\frac{10-\log202}{2}>0.
\]

반환하는 0은 global MLE가 아니다. 단일 차원의 score root를 한 번 찾는 것으로도 모든 경우를 해결할 수 없다. 이 함수는 point estimate뿐 아니라 mock covariance·깊이별 growth difference 계산에 들어가므로 후속 산출물까지 재검증 대상이다. 실제 CF4 입력에서 영향의 크기는 아직 계산하지 않았다. [고정 amplitude source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/obsstat/cf4_growth_covariance.py)

### Local Codex에 넘길 수 있는 수정 정리

양수 고유값이 하나 이상이면

\[
U=\max\left(0,\max_{\lambda_i>0}\frac{p_i^2-1}{\lambda_i}\right)
\]

를 잡는다. \(A>U\)에서는

\[
\ell'(A)=\frac12\sum_{\lambda_i>0}
\frac{\lambda_i(p_i^2-1-A\lambda_i)}{(1+A\lambda_i)^2}<0.
\]

따라서 모든 global maximizer는 \([0,U]\)에 있다. 이는 임의의 cap에 의존하지 않는 유한 탐색영역이다. \(U=0\)이면 0이 유일한 maximizer이고, 모든 \(\lambda_i=0\)이면 이 likelihood는 \(A\)를 식별하지 못한다.

구간 \(J=[a,b]\)에서 component 함수

\[
\phi_i(t)=-\tfrac12(\log t+p_i^2/t),\qquad t=1+A\lambda_i
\]

의 최대값은 두 endpoint와 범위 안의 \(t=p_i^2\)에서 얻는다. 따라서

\[
B(J)=\sum_i\sup_{A\in J}\phi_i(1+A\lambda_i)
\]

는 \(\sup_{A\in J}\ell(A)\)의 상계다. 유효한 표본점 우도의 하계 \(L\)와 전체 탐색 partition \(\mathcal P\)에 대해

\[
\max_{J\in\mathcal P}B(J)-L\le\varepsilon
\]

를 만족하면 목적함숫값의 \(\varepsilon\)-global optimality를 인증할 수 있다. 이는 maximizer의 유일성이나 \(A\) 위치 오차의 인증은 아니다. 수치 구현은 outward rounding 또는 명시적인 평가오차 enclosure를 포함해야 한다. 작은 고유값을 0으로 바꾸면 바꾼 모형에 대한 인증임을 표시해야 한다. 이 수정 정리와 경계 경우는 독립 수학 검토를 거쳤으며 코드는 실행하지 않았다.

## 같은 자료의 두 추정량을 독립으로 비교한다

PR145 runner는 같은 표본으로 bulk-only WLS와 bulk+monopole WLS를 계산한다. `compare_vectors`는 차이의 공분산 대신 두 covariance를 더하기만 한다. 올바른 식은

\[
C_\Delta=C_0+C_1-C_{01}-C_{10}.
\]

또한 공통 가중행렬 \(W\), 3열 방향행렬 \(D\)에 대해 두 정상방정식에서

\[
\widehat B_0-\widehat B_1
=(D^TWD)^{-1}D^TW\mathbf1\,\widehat M
\]

이 나온다. 고정 설계에서 차이의 covariance rank는 최대 1이다. 현재 3자유도 \(\chi^2\) 변환은 이 구조와 맞지 않는다. 저장 report의 `mahalanobis_chi2=0.003754`, `consistency_sigma≈7.7e-05`는 해당 비교 인터페이스에 연결된다. 이를 타당한 estimator-consistency 유의성으로 읽을 수 없다. 기록의 오래된 module 경로 때문에 현재 ref에서 재실행한 결과라고도 간주하지 않았다. [고정 비교 source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/obsstat/cf4_velocity_estimators.py)

## 결과값 자체를 거부하는 분기는 제거 대상이다

PR145 runner에는 \(404<|\widehat B|<406\ {\rm km\,s^{-1}}\)이면 과거 headline 405와 비슷하다는 이유로 출력을 중단하는 분기가 있다. 이는 자료 품질이나 수학적 유효성 조건이 아니다. 일반 실행경로로 사용하면 결과에 의존하는 선택 규칙이 된다. 현재 보존값 \(319.758054\ {\rm km\,s^{-1}}\)는 그 구간 밖이며, 조작이나 재시도가 있었다는 증거는 없다. 비판 대상은 **정당하게 계산된 특정 수치의 출력을 금지하는 규칙**이다. [고정 실제 caller](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/scripts/codex_harness/run_pr145_velocity_estimators.py)

## 공유 mock이 있어도 관측 오차법칙은 별도다

PR146의 toy grouping은 거리순으로 연속 3개 행을 묶는다. 공간적 이웃 여부를 보지 않으며, 평균 위치에서 새 covariance를 만드는 것은 일반적인 압축 \(ACA^T\)와 같지 않다. 거리 threshold와 추가 속도항으로 만든 selection·Malmquist stressor도 실제 CF4 관측 likelihood를 대신하지 않는다. 이 toy regrouping과 centroid covariance 결함은 이미 grouped catalogue와 제공된 full covariance를 소비하는 current-stack에는 적용되지 않는다.

저장 coverage report는 lognormal-distance stressor에서 68% monopole coverage가 0.26으로 낮아진 경우를 보존한다. PR148의 deepest shell은 \(f\sigma_8=3.711666\), 명목 공동 구간 \([2.410233,5.013098]\)을 출력하지만 같은 계열은 distance-error misspecification과 nonidentification도 기록한다. Bonferroni 보정은 그 자체로 비Gaussian·경계점 추정량의 주변 구간이나 잘못된 생성모형을 고치지 않는다. 이 구간에 실제 95% 공동 coverage가 보장된다는 근거는 확인되지 않았다.

CF4 원문은 거리 측정 방법·그룹·공유 zero-point calibration의 연결을 설명한다. 따라서 upstream covariance와 거리 변수의 likelihood를 그 구조에 맞추어야 한다. affine GLS와 finite nuisance sweep은 유효한 연산자·민감도 도구지만, sweep의 최솟값·최댓값이 자동으로 공동 신뢰집합이 되지는 않는다. [Cosmicflows-4 원문](https://arxiv.org/html/2209.11238v2)

# N1–N5: 물리 null과 proxy 통계의 간격

## 원문에 대응하지 않는 문헌 귀속과 parity

A14 N1은 `arXiv:2507.NNNNN`라는 미완성 식별자로 Bashir의 2025 SBI posterior와 \(A_{\rm scan}\)의 평균 \(3\times10^{-4}\), 표준편차 \(10^{-4}\)를 귀속한다. 실제 확인한 Bashir–Chingangbam–Appleby 논문은 2025년 11월의 FLASK 기반 clustering·mask 재평가다. 이 문서가 적은 SBI 제목·시기·posterior 값의 출처 대응은 확인되지 않았다. [Bashir 등 원문](https://arxiv.org/html/2511.00822v1)

WISE scanning과 photometric uncertainty의 결합을 명시적으로 SBI에 넣은 확인 가능한 연구는 Oayda–Lewis의 2026년 논문이다. 이 연구는 주로 **quadrupole과 ecliptic bias**를 다루며, magnitude·colour·위치별 photometric error와 selection을 생성과정에 넣는다. 이것을 고정 북황극 방향의 양수 scalar dipole로 대체하는 것은 원논문의 구현이 아니다. 해당 연구도 잔여 photometric error 문제가 남는다고 설명하므로 만능 보정으로 채택해서는 안 된다. [Oayda–Lewis 원문, §4](https://arxiv.org/html/2602.05070v1)

독립적인 parity 점검은 간단하다. 스캔 패턴 \(g(\boldsymbol n)\)이 두 황극에서 대칭이면 \(g(-\boldsymbol n)=g(\boldsymbol n)\)이므로

\[
\int_{S^2}g(\boldsymbol n)\boldsymbol n\,d\Omega=0.
\]

대칭 mask를 곱해도 마찬가지다. 실제 dipole 누출을 만들려면 비대칭 mask·selection·오염 또는 대응하는 mode coupling을 계산해야 한다. 이 명제는 실제 WISE가 완벽히 대칭이라는 주장이 아니다. A14의 대칭적인 극·위도 profile만으로 dipole을 유도할 수 없다는 뜻이다.

A14 N4의 문헌 제목과 작은 양수 amplitude prior 귀속도 실제 논문과 대응시켜야 한다. von Hausegger–Dalang의 관련 연구는 관측 redshift로 자른 표본에서 생기는 경계항을 다룬다. 그 응답은 경우에 따라 dipole 방향을 반전시킬 만큼 클 수 있다. 따라서 모든 깊이의 효과를 양수의 작은 additive bias로 고정할 근거가 되지 않는다. [Redshift tomography 원문](https://arxiv.org/html/2412.13162v2)

## 문서에 있는 방향·CF4 fingerprint가 실제 생성되지 않는다

초기 `NullDataset`은 CW·radio scalar amplitude와 선언한 상관계수를 담는다. A14 문서가 설명하는 방향 posterior·sky pattern은 그 객체에서 생성되지 않는다. N3 문서의 \(0.3A_{\rm clust}\) CF4 주입도 현재 코드에는 없고, 모든 N1–N5가 `b_CF4=0`, `b_CF4_s=inf`를 반환한다. active runner는 CF4를 읽지 않는다. 따라서 현재 이 경로가 CF4 fingerprint로 N3를 식별한다고 쓰면 틀린다.

또한 fixture `obs_defaults.json`의 CW 값은 \(1.6\times10^{-3}\), A14 N1의 관측 비교는 약 \(1.55\times10^{-2}\)다. 양쪽이 같은 number-count dipole인지, 속도 환산 proxy인지 명시되지 않은 상태에서 하나의 \(\epsilon_1\)로 결합하면 안 된다. fixture를 실제 관측제품으로 승격하려면 단위뿐 아니라 **관측량 정의와 응답계수**를 확인해야 한다. [고정 null source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/htt/htt/nulls/clustering.py)

## 생성 covariance와 추론 covariance가 다르다

N2는 고정한 baseline과 contamination fraction 아래

\[
X=|\mu+\sigma_C Z_C|,\quad
Y=|\mu/2+\sigma_R Z_R|,\quad Z_C\perp Z_R
\]

를 만든다. 따라서 ensemble에서 \(X\perp Y\), \(\operatorname{Cov}(X,Y)=0\)이다. 그러나 반환 metadata는 \(\rho=0.3\)이고 runner가 이를 quadratic form에 직접 사용한다. 유한 표본상관이 정확히 0이라는 주장은 아니다.

N5에는 실제 공유 잠재변수 \(A_{\rm common}\)가 있다. 다만 `rho_shared`는 표본 생성에 들어가지 않고 metadata에만 들어간다. 같은 seed와 나머지 입력에서 이 값을 바꾸면 amplitude 표본은 같고 추론 점수만 달라진다. 측정잡음과 절댓값 적용 전 실제 latent correlation은

\[
\rho_{\rm latent}=
\frac{10^{-8}}{\sqrt{(2\times10^{-8})(3.25\times10^{-8})}}
=\sqrt{2/13},
\]

이다. 추가 측정잡음과 folding 이후에는 다시 달라진다. 이 sweep은 현재 **추론 covariance의 민감도 조사**이지 생성 nuisance 상관의 sweep이 아니다.

## 공통속도 evidence와 MES를 실제로 계산하지 않는다

`_fast_lnB_approx`는 \(\frac12y^TC^{-1}y-\log100\)을 사용한다. 알려진 응답 \(a\)와 단일 공통 scalar 속도 \(\beta\)의 Gaussian 모형 \(y=a\beta+\varepsilon\)에서 unconstrained 최대우도 개선은

\[
2\Delta\log L=\frac{(a^TC^{-1}y)^2}{a^TC^{-1}a}.
\]

반면 \(y^TC^{-1}y\)는 두 평균을 각각 자유롭게 맞추는 saturated alternative의 개선이다. 공통속도로 설명하지 못하는 contrast까지 신호 개선으로 센다. \(C=\sigma^2I\), \(a=(1,1)^T\), \(y=(d,0)^T\)이면 전자는 \(d^2/(2\sigma^2)\), 후자는 \(d^2/\sigma^2\)다. 고정 Occam 항은 이 모형 차이를 해소하지 못한다. 이 비교는 likelihood 개선의 비교이며 임의의 실제 Bayes factor에 대한 상계 정리는 아니다.

이어지는 `Pi_approx=clip(lnB/15,0,1)`에는 MES event, physical tensor, conditional likelihood가 없다. `Pi_approx>0.95`는 proxy score가 14.25를 넘는 규칙이다. 따라서 저장 trigger rate를 tensorized MES posterior의 FPR로 해석할 수 없다. 테스트는 smoke·schema·JSON 형식을 확인하며, 5×15 heatmap formatter의 테스트 값은 인공적으로 채운 배열이다. **formatter와 smoke test의 존재는 75개 물리적 모형 비교의 실행 증거가 아니다.** [고정 runner](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/htt/htt/nulls/runner.py)

## family별 FPR을 합치는 법도 정해야 한다

`union_fp_Pi005=1-\prod_i(1-p_i)`는 독립 사건이면 정확하지만 일반적인 conservative upper bound는 아니다. 확률이 각각 \(1/10\)인 배반 사건 두 개의 union은 \(1/5\), 코드식은 \(19/100\)이다. 독립성 없이 유효한 상계는 \(\min(1,\sum_i p_i)\)다.

그보다 먼저, 서로 다른 null family의 분포 \(P_i\)는 같은 확률공간의 여러 사건과 다르다. composite null 보증은 \(\sup_iP_i(\mathrm{reject})\), 명시적 mixture는 \(\sum_i\pi_iP_i(\mathrm{reject})\), 같은 sky에서 여러 검정의 familywise error는 공동 생성법칙 아래 rejection union으로 정의한다. 어느 질문을 푸는지부터 고정해야 한다. [고정 common interface](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/htt/htt/nulls/common_interface.py)

# PR062의 깊이·방향 후속 구현

`selection_response_depth.py`와 `survey_axis_coherence.py`는 초기 scalar 객체보다 분명히 진전됐다. 방향 단위벡터·깊이 bin·공유 mock amplitude를 보존하고, **하나의 mock 안에서 어느 bin이라도 trigger하면 한 번 세는** union을 직접 계산한다. 상관된 bin들의 독립확률 곱을 요구하지 않는 점은 올바르다.

그러나 실제 생성식에는 `1+0.12*depth_index`, `1+0.08*depth_index`, 임의 jitter 배율이 들어간다. selection-function hash·mask hash·covariance status는 provenance로 전달되지만 해당 생성 함수가 selection 함수의 값이나 관측 covariance 행렬을 평가하는 것은 아니다. statistic도

\[
G_F=\exp\{(\beta/\beta_{\rm scale})^2\}
\]

라는 선언된 proxy이며 계산에서는 exponent를 60으로 cap한다. config hash가 있다는 이유로 이것을 공동집합에서 유도한 GF나 실제 MES posterior로 동일시할 수 없다. [고정 depth source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/htt/htt/nulls/selection_response_depth.py)

여기서 계산한 FPR은 정의된 proxy 생성모형에 대해서는 의미가 있다. 하지만 실제 catalog에서 동일 관측량을 추정하고 같은 분석 pipeline을 거친 null law의 보정은 아니다. Wilson one-sigma interval과 별도 trial multiplier도 그대로 명시되어 있으므로 이를 자동으로 95% 가족단위 보증으로 바꾸어 읽지 않는다.

재사용 대상은 방향·깊이·mock ID·manifest·mock별 rejection 집계다. 교체하거나 근거를 추가해야 할 부분은 selection·boost·측정오차를 잇는 생성식과 실제 분석 statistic이다. 후속 구조가 있다는 이유로 초기 결함을 숨기지도, 초기 결함 때문에 후속 구조 전체를 버리지도 않는다.

# 실제 관측 응답과 tensorized MES로 연결하는 방법

## number-count amplitude와 속도를 구별한다

단색·단순 flux cut의 작은 boost에서는 number-count dipole이 \([2+x(1+\alpha)]\boldsymbol\beta\)에 비례한다. CMB의 \(\Delta T/T\simeq\boldsymbol\beta\cdot\boldsymbol n\)와 응답계수가 다르다. 넓은 photometric band에는 그 band와 경계 표본에 맞는 응답이 필요하다. [Bonnefous 원문](https://arxiv.org/html/2602.05700v2)

에너지 flux 관례에서 \(F_X=\int T_X(\nu)S_\nu\,d\nu\)라 둔다. Doppler factor \(\delta\)에 대해 \(\epsilon=\log\delta=\boldsymbol\beta\cdot\boldsymbol n+O(\beta^2)\)로 정의하면

\[
S_\nu^{\rm obs}(\nu)=e^\epsilon S_\nu(e^{-\epsilon}\nu),
\quad
q_X=\left.\frac{d\log F_X^{\rm obs}}{d\epsilon}\right|_0
=1-\frac{\int T_X\nu\,\partial_\nu S_\nu\,d\nu}{F_X}.
\]

단일 hard flux cut의 응답은 경계 표본의 평균을 사용한 \(2+x\langle q_X\rangle_{F_*}\)이다. \(T_X\)에는 사용한 photon/energy response 관례를 포함해야 한다. 혼합 SED·colour cut·관측잡음·공간 completeness가 있으면 이 한 계수를 모든 bin에 복사하지 말고 전체 선택확률의 boost derivative를 사용한다. 위 식은 선형 local boost의 기준식이며 일반 global tilt의 전방모형은 아니다.

관측 redshift bin \([z_a,z_b]\)에는, flux 선택 후의 등방 평균 분포 \(n(z)\)에 대해 경계 기여

\[
B_b=\frac{(1+z_b)n(z_b)-(1+z_a)n(z_a)}
{\int_{z_a}^{z_b}n(z)\,dz}
\]

가 더해진다. 이는 \(1+z_{\rm obs}=(1+z)e^{-\epsilon}\)에 따라 표본이 bin 경계를 드나들기 때문이다. redshift 오차가 있으면 hard boundary 대신 오차를 포함한 selection kernel을 미분한다. 방향 부호를 보존해야 한다. [von Hausegger–Dalang, 식 (13)](https://arxiv.org/html/2412.13162v2)

## 통계의 공통 객체는 이름이 아니라 공동 자료법칙이다

관측자료를 \(Y\), 공통 cosmological realization을 \(Z\), 관측 응답·선택·calibration을 \(\eta\), physical tensors와 local velocity를 \(\theta\)로 놓는다. 각 survey의 \(Y_s\)는 같은 \((Z,\theta)\)와 해당 \(\eta_s\)에서 생성되어야 한다. 다른 제품이 같은 지도를 재처리하거나 같은 은하를 공유하면 그 의존성이 남는다. 독립 주변 likelihood들을 곱하는 것은 별도 가정이다.

그다음 tensorized MES의 deterministic 조건을 \(\mathcal B_{\rm MES}\), nuisance와 물리적 정의역을 \(\mathcal D\), 보정된 공동 관측집합을 \(\mathcal C_Y\)라 하면

\[
\Theta_Y=\{(\theta,\eta)\in\mathcal D\cap\mathcal B_{\rm MES}:
R(\theta,\eta)\in\mathcal C_Y\}
\]

와 그 projection을 분석할 수 있다. 이 표현은 이전 보고서의 유효한 공동식별 구조를 계승한 **연결 명세**다. 현재 N1–N5나 PR062가 이 전체 연산을 구현했다는 주장은 아니다.

Full Q/O와 CF4의 STF 계수를 유지하면 \(\operatorname{tr}Q^2\), \(\operatorname{tr}Q^3\), \(O:O\), \(O_{ijk}Q_{jk}\) 같은 관측 수축 및 방향 정보를 직접 검토할 수 있다. 관측 STF shear와 spacetime kinematical shear를 같다고 놓지 않고 \(R\)로 연결해야 한다. parity-odd 형태를 시험하려면 반사대칭 benchmark만으로 calibration을 끝낼 수 없다는 이전 지적도 유지된다.

GF v9는 \(\Theta_Y\)의 특수한 box/affine 부분문제에, affine GLS는 \(R\)의 거리자료 추정 부분에, Q/O fibre 도구는 관측 형태의 기하에 재사용한다. 어느 하나가 다른 계층의 미완성을 대신하지 않는다.

# 외부 자료·코드와 기존 구현의 재사용

| 자산 | 바로 활용할 수 있는 부분 | 반드시 남겨야 할 대응 조건 |
|---|---|---|
| GF v8·v9와 exact LP witness | signed ratio 범위·shared endpoint 검사 | box/affine/분모 양수 정의역; 실제 공동집합의 타당성 |
| CF4 affine current-stack | 9열 추정·full covariance slicing·rank | 행 ID·좌표계·단위·관측 covariance의 출처 |
| PR146·148 correlated mocks | 공유 장을 각 shell에 일관되게 투영 | 실제 거리·selection·grouping·calibration law |
| PR062 null-bank 구조 | 방향·깊이·mock별 rejection 집계 | 경험적 beta 생성과 GF proxy를 실제 응답·통계로 연결 |
| 기존 Q/O·MES·MIO 도구 | full tensor와 불변량·부분식별 | source-response와 parameter Jacobian 구별; 같은 자료의 의존성 |
| Secrest 공개 자료·코드 | sample 생성·mask·dipole baseline 재현 | 배포 sample cut과 최종 분석 cut의 차이 |
| CF4++ 공개 grid | field 형태·posterior 요약·예측 비교 | 원 CF4와의 재사용 관계; full joint covariance 부재 |

Secrest의 Zenodo v3에는 sample 생성 코드, mask, dipole·Monte Carlo 코드, 추가 correction 자산이 공개되어 있다. 배포 FITS는 \(W1<16.5\), 최종 결과는 \(W1<16.4\)라는 차이를 명시한다. 이 차이를 입력 계약에 반영하면 baseline을 새로 만들 작업을 줄일 수 있다. 이번에는 archive를 내려받아 실행하지 않았다. [공식 자료 묶음](https://zenodo.org/records/8303800)

CF4++ 공식 페이지는 10,000 HMC steps에 걸친 velocity·density의 mean/RMS grid와 조회 예제를 제공한다. mean/RMS만으로 voxel 사이의 joint covariance를 복원할 수는 없다. 따라서 원 CF4 likelihood와 별개의 독립 측정처럼 곱할 수 없다. 같은 페이지의 옛 2023 FITS에 적용되는 velocity 배율을 다른 NPZ 제품에 자동 적용해서도 안 된다. [CosmicFlows 공식 자료](https://projets.ip2i.in2p3.fr/cosmicflows/)

문헌 사이의 CatWISE tension 판정도 하나로 고정하지 않는다. Abghari 등은 높은 multipole과 mask coupling의 불확실성을 강조하고, Bashir 등은 다른 생성모형 아래 잔여 tension을 보고한다. 논문들의 서로 다른 sigma를 같은 실험의 독립 likelihood처럼 결합하지 않는다. 이 프로젝트의 강점은 full multipole과 공통 관측 연산을 보존해 그 차이를 시험할 수 있다는 점이다. [Abghari 등](https://arxiv.org/html/2405.09762v2), [Bashir 등](https://arxiv.org/html/2511.00822v1)

# 독립 기준에 따른 실행 우선순위와 미완료 범위

| 우선 작업 | 이미 결정된 내용 | Local Codex가 확인할 산출물 |
|---|---|---|
| GF migration 점검 | v8·v9를 수리된 경로로 인정 | caller별 정의역·구형 API 진입 목록 |
| CF4 amplitude 수정 | 유한 \([0,U]\)와 objective 상계 정리 | exact 반례, global gap, 경계·비식별 반환 상태 |
| 동일표본 비교 수정 | cross covariance와 rank≤1 구조 | 공동 mock 또는 선형 추정행렬로 만든 \(C_\Delta\) |
| 출력 수치 금지 규칙 제거 | 405 주변값 자체는 품질 기준이 아님 | 정의역·자료 품질만으로 출력 허용 여부 결정 |
| survey null 재연결 | signed/vector 응답·mask·error-before-selection | 동일 sky와 동일 분석 pipeline에서 얻는 null law |
| tensorized MES 연결 | physical constraints·관측집합·response의 교집합 | full tensor·불변량·joint identified set, 정의역 명시 |

이 표는 새 통합 분석 전체를 즉시 release하는 DAG가 아니다. 이번에 수학적으로 닫은 수정과 이미 유효한 구현을 식별하는 감사 후속표다. 실제 PR3/CF4 입력 모형, native global-tilt 전달함수, 모든 자료의 공유 calibration·선택법칙까지 완성한 상태는 아니다.

남은 전수 정독은 18,885개 blob 중 미독 내용과 버전 변화의 의미를 확인하는 작업이다. 특히 MIO reference·짝 규칙의 후속 caller, DESI·JWST·radio의 관측 result lineage, 최신 tensorized MES authority의 미독 부분, BASS의 긴 hierarchy·closure 문서, 과거 삭제된 JSON·원고·코드 버전이 남아 있다. 단순 검색·파싱·파일 목록 확보를 정독으로 세지 않는다.

이번 결과로 확인한 가장 현실적인 발전 경로는 **유효한 GF·affine GLS·full Q/O를 살리면서 공동 생성법칙과 실제 관측 응답을 연결하는 것**이다. 프로젝트 전체를 폐기할 근거도, 현재 모든 headline을 관측적으로 확정할 근거도 없다. 최종 전수 판정은 미독 범위가 닫힌 뒤에만 가능하다.

# 검토와 근거 묶음

GF successor와 CF4 successor를 별도 정적 심사로 읽었다. N1–N5의 생성 covariance·proxy likelihood·union 해석은 독립 재독을 거쳤다. CF4 global-search 수정 정리도 별도 수학 검토를 받았고, rounding 인증과 목적함숫값/모수위치의 구별을 반영했다.

동봉 묶음은 보고서 원문·PDF, 이번 exact source cache, 전문 읽기 원장, claim-source 대응표, 독립 검토 기록, 전 이력의 고유 blob 목록과 손실 없는 평탄화 tree checkpoint를 포함한다. 이전 보고서는 별도 역사 문서로 보존하며 **GF에 관한 이번 적용 범위 교정을 우선해서 읽어야 한다.**

`coverage.json`은 작업 완성도의 유일한 숫자 요약이다. source cache hash 일치는 읽은 바이트의 동일성을 보장하며 과학적 정확성을 보장하지 않는다. 과거 저장 PASS와 이번 정적 검토, 앞으로 Local Codex가 수행할 재실행은 각각 별개의 근거다.
