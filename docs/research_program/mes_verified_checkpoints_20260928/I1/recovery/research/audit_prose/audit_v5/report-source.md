---
title: "HTT 전 이력 독립 감사 · R5"
subtitle: "Tensorized MES의 실제 구현과 MIO·DESI·JWST 관측 계보"
date: "2026-09-08"
lang: ko
fontsize: 10pt
geometry: "a4paper,margin=22mm"
colorlinks: true
toc: true
toc-depth: 1
---

# 이번 조사에서 바뀐 판정

**후속 구현의 재사용 가치는 이전 평가보다 크다. 그러나 관측량, 물리적 응답, 공동분포 사이의 연결에는 구체적인 단절이 남아 있다.** MES에는 실제 방향 moment 추정과 행렬 연산이 있고, DESI·JWST에는 실제 관측자료를 사용한 보존 결과가 있다. 이를 단순한 문서나 toy 모음으로 평가하면 틀린다. 반대로 명칭, PASS, claim ceiling, provenance certificate만으로 물리적 추론이 검증되었다고 평가해도 틀린다.

| 영역 | 독립적으로 인정하는 성과 | 이번에 특정한 제한 또는 결함 |
|---|---|---|
| Tensorized MES | 벡터·STF2 추정, 조건부 anchor 기하, nuisance 제거·Schur 응답 | 물리적 분자·응답 미결합, 일부 adapter의 parity 손실 |
| MES 비교 실험 | 좌표변환 후 예측·Gaussian 우도 불변성 검사 | 일부 비교 우위는 지정 계수로 결정됨; coverage가 실제 공동집합 coverage는 아님 |
| MIO | 동일 가중치로 보정한 방향 통계, typed residual 연결 | 독립 방향 null을 물리적 FLRW null로 해석할 수 없음 |
| DESI | 실제 BGS_ANY 자료의 dipole 분석 계보, 후속 18차원 관측 연산자 | ICRS/Galactic 혼합, 가중 count와 Poisson mock 법칙 불일치 |
| JWST | 실제 논문 표의 host 계층모형·covariance 민감도 | method contrast에서 공통 거리 응답 소거; singular covariance 경계식 결함 |

이번 판정은 원심사·업그레이드 제안에 대응하는 전체 연구의 독립 평가를 이어가는 것이다. R4에서 확인한 GF v8/v9 수리, CF4 affine GLS의 강점, 구형 MLE·교차공분산의 결함도 유지한다. 오래된 BASS의 문제를 모든 후속 구현으로 일반화하지 않으며, 이번 successor의 개선을 과거 결과에 소급 적용하지 않는다.

**전체 전수 정독은 아직 완료되지 않았다.** 새 고유 내용 52개를 전문 읽어 누적 265개가 되었다. 고정한 전 이력 목록의 18,885개 blob 중 일부다. 이 보고서는 그 한계를 숨긴 전체 완료 보고서가 아니다. 과학 코드·CAS·모의실험·관측자료 분석은 실행하지 않았다. 아래 수치는 기존 저장 파일에서 읽은 값이며, 수학적 반례는 해석적으로 유도했다. 과학 실행은 워크스테이션 Local Codex의 범위로 유지했다.

# 버전과 정독 범위

같은 이름의 파일도 내용과 ref가 다르면 별도로 조사했다. 이 보고서의 짧은 ref 표기는 다음과 같다. 전체 commit SHA는 각 링크와 동봉 원장에 보존했다.

| 표기 · commit 앞 12자리 | 역할 |
|---|---|
| H · [5702024e06ef](https://github.com/cosmosapjw-quantum/htt_base/commit/5702024e06eff4979087f07f86ee7131d13961ac) | 이어받은 handoff 기준 |
| P · [5a3825f90354](https://github.com/cosmosapjw-quantum/htt_base/commit/5a3825f903546891fd90e3d708481707d59babf4) | 병렬 통계 후속 구현 |
| A · [6bafca66285e](https://github.com/cosmosapjw-quantum/htt_base/commit/6bafca66285ef071081453313bb7d2d6b261599c) | Anchor·response donor |
| D · [de73549c16ac](https://github.com/cosmosapjw-quantum/htt_base/commit/de73549c16ac6ceb63f924c86611e0a5ceb4711d) | 방향 MES 후속 파일 |
| E · [af147f1a3549](https://github.com/cosmosapjw-quantum/htt_base/commit/af147f1a3549c81ccfdef7130698580c028512d3) | DESI PR151 관측 계보 |

H만 읽으면 A·P·D에 있는 연산자를 놓친다. 반대로 병렬 파일의 존재만으로 H에서 import되고 실제 호출된다고 가정할 수 없다. 이번에는 `mes_directional_state.py`의 세 역사적 blob도 목록에서 구별했다. D의 내용을 읽었다고 이전 두 버전의 전문 읽기를 대신하지 않았다.

기존에 고정한 182개 branch ref에서 2,061개 commit, 2,003개 고유 root tree의 부모 관계와 평탄화 파일 목록을 확보했다. 이들 목록의 보존 검사는 R4에 포함되어 있다. 이번에 모든 원격 ref를 다시 갱신하지는 않았다.

| 항목 | 수 |
|---|---:|
| 전 이력 고유 blob / 경로 | 18,885 / 11,379 |
| 고정 branch 끝점들의 고유 blob | 8,630 |
| 끝점에는 없고 과거에만 있는 blob | 10,255 |
| R4까지 전문 읽은 고유 blob | 213 |
| 이번 전문 읽기 중 신규 고유 blob | 52 |
| 누적 전문 읽기 | 265 |
| 누적 중 branch 끝점에도 있는 blob | 246 |

이번 읽기 기록은 58행이다. 그중 전문 읽기 56개, 부분 읽기 2개이며, 전문 읽기 중 4개는 이전 전문 읽기와 중복된다. 같은 blob의 재검토는 누적 수를 늘리지 않는다. Root의 기존 부분 읽기 두 개를 이번에 끝까지 읽은 경우에는 새 전문 읽기로 승격했다. 각 새 캐시는 Git의 `blob <length>\0<bytes>` SHA와 대조했다. 이것은 원본 보존 검사이며 연구 계산의 재현 검사가 아니다.

동봉 `read_ledger_increment.json`, `read_ledger_cumulative.json`, `coverage.json`이 판정 범위를 기록한다. `HISTORICAL_READING_STATUS.csv`에는 18,885개 전체의 FULL / PARTIAL_OR_DELTA / UNREAD 상태가 있다. 이 분모에는 코드·문서·JSON과 이진 파일이 함께 들어 있으므로 단순 비율을 과학적 완성도로 읽으면 안 된다. Git 밖의 대용량 원자료와 외부 실행 directory도 별도다.

# Tensorized MES: 실제 계산과 물리적 의미

## 문서와 구현에 모두 존재하는 성과

H의 T3와 K1R은 관측 저다중극 \((Q_{ab},O_{abc})\), 물리적 congruence의 \((\sigma_{ab},\omega_a,A_a)\), radiation/matter/observer 사이 속도, MES 조건부 상한, 공동 식별집합을 구별한다. 이 구별은 물리적으로 필요하다. 같은 STF2 표현을 가진다는 이유로 \(Q_{ab}=\sigma_{ab}\)가 되지는 않는다.

T3의 온도 convention에서는

\[
\epsilon_2^2=\frac{Q:Q}{T_0^2}=\frac{75C_2}{8\pi T_0^2},\qquad
\epsilon_3^2=\frac{O:O}{T_0^2}=\frac{245C_3}{8\pi T_0^2}.
\]

따라서 sky RMS와 PSTF norm을 구별하는 실제 정규화가 있다. 원심사의 “기존 multipole 표현과의 관계”를 설명할 때 이 변환은 재사용할 수 있다. 다만 이 대수적 변환 자체가 새로운 물리 이론이나 기존 multipole-vector 표현보다 강한 관측 정보라는 주장은 성립하지 않는다.

A의 `anchor_geometry.py`는 product block ball, ellipsoid, 대칭 H-polytope의 gauge를 실제 계산한다. 예를 들어

\[
\rho(x)=\max_j\frac{\|x_j\|}{R_j},\qquad
\rho_Q(x)=\sqrt{x^TQx}
\]

를 다루며, \(1-\rho\), \(1/\rho\), \(1/\rho-1\), \(\max(\rho-1,0)\)를 서로 다른 지표로 구별한다. 유한 anchor family의 각 값과 범위를 보존하고, 연속 family의 최적화를 수행하지 않은 경우에는 완료된 수치로 위장하지 않는다. 이 연산들은 재사용할 가치가 있다. [Anchor 기하 source](https://github.com/cosmosapjw-quantum/htt_base/blob/6bafca66285ef071081453313bb7d2d6b261599c/htt/src/common/anchor_geometry.py)

## 방향 moment 추정기는 실제로 구현되어 있다

D의 OBSSTAT 및 COMMON 후속 파일은

\[
q(n)=q_0+V_an^a+T_{ab}n^an^b,\qquad T^a{}_a=0
\]

라는 \(\ell\le2\) 영역을 다룬다. Full-sky 경로는 0~4차 quadrature moment를 검사하고

\[
V_a=\frac3{4\pi}\sum_i w_iq_in_{ia},\qquad
T_{ab}=\frac{15}{8\pi}\sum_iw_iq_i n_{i\langle a}n_{ib\rangle}
\]

를 계산한다. Masked/discrete 경로는 상수 1개, dipole 3개, STF2 5개의 **9열 공동 weighted least squares**를 수행한다. Active row, rank 9, column-normalized condition을 검사한다. 분석적 다항식의 moment 회수, 회전·반사, mask·rank에 관한 테스트 코드도 존재한다. 이번에 테스트를 실행한 것은 아니다. [Moment estimator source](https://github.com/cosmosapjw-quantum/htt_base/blob/de73549c16ac6ceb63f924c86611e0a5ceb4711d/htt/obsstat/mes_directional_moments.py)

이는 내용 없는 schema가 아니다. 그러나 quadrature가 degree 4까지 정확하다는 사실이 실제 입력장의 bandlimit를 증명하지는 않는다. 소스의 테스트에도 \(\ell=4\) 입력이 STF2로 alias되는 사례가 있다. Full Q/O 분석에 필요한 STF3는 이 adapter의 범위 밖이고, canonical 연결은 STF2만 전달한다.

`normalize_mes_premise`는 주어진 좌표를 양의 anchor로 실제 나눈다. 반면 `build_mes_directional_state`는 numerator channel key를 독립된 field 계약에서 가져오지 않고 **anchor의 key를 복사해서 전달**한다. 따라서 key equality는 물리적 분자와 분모가 같은 sector임을 독립 확인한 증거가 아니다. 현재 observer-coordinate index의 정의로는 사용할 수 있지만, 이를 물리적 shear 또는 vorticity stress로 승격할 수는 없다.

`covariance_identity`와 `transfer_identity`도 현재는 content identity 문자열이다. Dense covariance 전파, 물리적 response matrix \(R\), \(\partial y/\partial\beta\), 같은 자료로 만든 random anchor와 numerator의 공동분포는 이 경로에서 계산되지 않는다. 물리적 stress readiness 함수가 response-bound numerator를 추가로 요구하는 것은 실제 연산 범위와 일치한다. [Directional state source](https://github.com/cosmosapjw-quantum/htt_base/blob/de73549c16ac6ceb63f924c86611e0a5ceb4711d/htt/src/common/mes_directional_state.py)

## 두 adapter의 parity 손실

독립 검토와 호출 경계 대조에서 좁고 구체적인 결함을 확인했다. OBSSTAT의 moment-to-canonical adapter와 COMMON의 MES-to-canonical adapter는 field parity를 비교하지 않는다. 그러나 canonical `ObservableIrrepState`는 해당 \(\ell=2\) harmonic/STF2 표현에 EVEN parity를 강제한다. 두 함수의 전체 이름은 동봉 검토 기록에 보존했다.

예를 들어 odd STF2 입력

\[
T=\operatorname{diag}(1,-1,0),\qquad G=-I
\]

는 \(\det(G)GTG^T=-T\)로 변환되어야 한다. 출력의 even STF2 계약은 \(GTG^T=T\)를 요구한다. Frame·단위·source·operator·성분을 일치시킨 API 입력에서 odd 표식이 even canonical type으로 넘어가는 정적 허용 경로가 있다.

이는 **O(3) type mismatch**다. 온도 scalar의 기존 even 경로를 오염시켰다는 증거는 아니다. 최소 수정은 두 adapter에서 SCALAR_EVEN / EVEN_STF2를 요구하고, odd STF2는 별도 canonical 표현이 생길 때까지 거부하는 것이다. Standalone estimator의 odd-parity 변환법까지 잘못됐다고 확대해서는 안 된다. Canonical 파일은 이 결함에 필요한 계약·validator·builder 부분만 읽었으며 전문 정독 수에 넣지 않았다.

# MES 상한과 식별 정리의 적용 조건

## 별개 상한의 대소관계는 물리적 허용 조건이 아니다

H의 `mes_theorem_authority.py`를 끝까지 읽었고, 전 이력 목록에서 이 경로의 고유 blob은 하나였다. 이 모듈의 strict hierarchy는 \(B_\sigma>B_\omega>0\)를 요구한다. 그러나

\[
\frac{|\sigma_{ab}|}{\Theta}<B_\sigma,\qquad
\frac{|\omega_{ab}|}{\Theta}<B_\omega
\]

라는 별개 upper bound들에서 그 순서는 도출되지 않는다. 양의 상한들이 어느 순서여도 두 좌변이 충분히 작으면 부등식의 동시 만족은 가능하다. 이것은 상한들의 논리적 관계에 대한 반례이며, 임의의 CMB multipole 조합에 해당하는 정확한 Einstein 해를 구성했다는 주장은 아니다.

따라서 이 순서를 물리적 admissibility filter로 사용하면 정당화되지 않은 제한이 들어간다. 계수 일치, 여러 CAS 기록, scan 결과의 일치는 추가 제한의 물리적 정리를 대신하지 않는다. **다만 최신 T3/K1R과 이번 방향 MES 후속 모듈에는 그 순서를 요구하는 일반 정리가 없다.** 구형 authority 검사를 전체 tensorized MES의 오류로 일반화하면 안 된다. [Authority source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/src/common/mes_theorem_authority.py)

## 문헌의 derivative 전제가 실제로 필요하다

원논문의 일반 형태는

\[
B_{\sigma,\mathrm{raw}}
=\frac83\epsilon_2+\epsilon_2^*+5\epsilon_1'
+\frac97\epsilon_3',
\]
\[
B_{\omega,\mathrm{raw}}
=9\epsilon_1'+3\epsilon_1'{}^*
+\frac65\epsilon_2''.
\]

여기서 prime/star는 논문이 정의한 공간·시간 derivative bound다. 익숙한 고정 계수형

\[
B_\sigma=\frac53\epsilon_1+3\epsilon_2+\frac37\epsilon_3,
\qquad B_\omega=\frac{10}3\epsilon_1+\frac2{15}\epsilon_2
\]

에는 논문의 추가 derivative 추정 C1/C2와 선형화·geodesic 등 전제가 들어간다. 한 관측자의 현재 multipole 진폭만으로 이 전제를 검증한 것은 아니다. 또한 여기서 vorticity 상한은 \(|\omega_{ab}|\) convention이며, axial vector로 바꿀 때 등록된 norm 변환이 필요하다. [Maartens, Ellis & Stoeger, 식 (51), (52), (59), (60)](https://arxiv.org/pdf/astro-ph/9501016)

후속 문헌의 Bianchi VII\(_0\) dust 사례는 작은 CMB anisotropy·shear와 큰 Weyl anisotropy가 양립할 수 있음을 보인다. 이를 MES 전체의 반증으로 읽기보다, derivative·시공간 영역 전제를 생략한 해석을 막는 사례로 사용해야 한다. [Nilsson 등](https://arxiv.org/html/astro-ph/9904252v1)

재사용 방향은 derivative control들을 명시적 nuisance family로 유지하고, signal response와 anchor에 **같은** family member를 적용하는 것이다. 이미 있는 GF joint-range 연산과 조건부 anchor family를 이 문제에 연결할 수 있다. 그 family의 실제 물리적 허용 범위와 관측 calibration까지 자동으로 정해지는 것은 아니다. 1995년 companion 논문은 이번에 metadata·초록까지 확인했으나 전문 접근을 완료하지 못했으므로, 그 논문의 별도 non-geodesic 계수를 새로 검증했다고 주장하지 않는다. [Companion 논문 정보](https://journals.aps.org/prd/abstract/10.1103/PhysRevD.51.5942)

## K1R-T9에는 exact-data 조건을 추가해야 한다

T8의 일반식은 \(\Theta=F_y\cap R^{-1}(C_y)\)다. T9는 exact linear response와 \(X_0\in\Theta\)만으로

\[
\Theta=F_y\cap(X_0+\ker R)
\]

를 쓴다. **선형식이 정확한 것과 데이터 compatibility region이 한 점인 것은 다르다.**

정확한 반례는 \(R=I\), \(F_y=[-2,2]\), \(C_y=[-1,1]\), \(X_0=0\)이다. 일반식의 \(\Theta\)는 \([-1,1]\)인데 kernel fibre는 \(\{0\}\)다. Noise가 남으면 full column rank만으로 singleton이 되지 않는다.

T9를 의도한 exact-data 정리로 보존하려면

\[
C_y\cap R(F_y)=\{RX_0\}
\]

같은 조건을 추가하면 된다. 일반 \(C_y\)에서는 정확한 singleton criterion이

\[
\left\{h:X_0+h\in F_y,\ Rh\in C_y-RX_0\right\}=\{0\}
\]

이다. 이는 전체 K1R을 폐기할 결함이 아니라 T9의 정의역을 좁혀 고칠 수 있는 문제다. 독립 수학 검토에서도 같은 결론을 확인했다. [K1R source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/docs/research_reports/theory_packs/K1R_TYPED_KINEMATICAL_MES_THEOREM_PACK.md)

# 기존 행렬 연산과 PR254 비교 실험

## Schur·nuisance 연산은 재작성할 이유가 적다

A의 `anchored_response_geometry.py`에는 supplied covariance와 response를 받아 whitening, nuisance projection, singular value, 공통 식별 부분공간을 계산하는 실제 구현이 있다. 개략적으로

\[
M=P_NWRD
\]

이며, \(W\)는 covariance support의 whitening, \(P_N\)은 whitened nuisance 방향 제거, \(D\)는 선택한 좌표 정규화다. Covariance의 양의 반정부호 검사와 수치 rank tolerance를 구별하고, covariance nullspace로 버려지는 response도 따로 기록한다.

기존 자료 \(b\)와 추가 자료 \(m\)의 공동 covariance가 주어지면

\[
C_{m|b}=C_{mm}-C_{mb}C_{bb}^{+}C_{bm},\qquad
R_{m|b}=R_m-C_{mb}C_{bb}^{+}R_b
\]

를 계산하는 Schur 경로도 있다. 이는 같은 하늘·같은 host·같은 calibration을 쓰는 자료를 무조건 독립이라고 더하는 것보다 필요한 구조에 가깝다. 구현의 rank·principal-angle·incremental information 계산은 의미가 있다. [Response geometry source](https://github.com/cosmosapjw-quantum/htt_base/blob/6bafca66285ef071081453313bb7d2d6b261599c/htt/src/common/anchored_response_geometry.py)

다만 같은 공통 식별 부분공간에서의 log-pseudodeterminant 차이로 얻은 ellipsoid volume ratio는 **국소 Gaussian 근사량**이다. 비선형·비볼록한 전체 물리적 공동집합의 부피 축소로 일반화할 수 없다. 모듈에 넣을 실제 \(R,C,N\)의 관측·물리적 유도도 아직 별도다.

Singular covariance는 추가로 구별해야 한다. 알려진 정확한 \(C\)에서 \(Q_0\)가 nullspace basis라면

\[
Q_0^T(y-RX-N\eta)=0
\]

은 정확한 관측 제약이다. \(C=\operatorname{diag}(1,0)\), \(R=(0,1)^T\)이면 support-only response rank는 0이어도 \(X=y_2\)가 정확히 식별된다. 현재 모듈의 명시적 quotient 계산을 버그라고 부르는 대신, **전체 추론에서는 이 exact row를 별도로 보존**해야 한다. 유한 mock covariance의 표본 rank 결손을 물리적으로 잡음이 0이라는 뜻으로 읽으면 안 된다.

## PR254의 좋은 검사와 결론을 지지하지 않는 검사

PR254 generator와 저장 JSON을 모두 읽었다. \(u'=D^{-1}u\), \(R'=RD\) 아래에서 예측이 보존되고, covariance determinant와 Gaussian 정규화항을 포함한 실제 우도가 일치하는지 검사한다. Synthetic response의 rank·condition도 계산한다. 이 부분은 유효한 재사용 검증이다.

그러나 목적별 비교 지표 중 일부는 물리적 perturbation에서 계산되지 않는다.

| 지표 | 실제 생성 방식 | 판정 |
|---|---|---|
| Source sensitivity | `0.1 × SOURCE_COUPLING[k]` | normalizer마다 미리 지정한 상수 |
| Premise sensitivity | `std(stress) × PREMISE_COUPLING[k]` | 공통 표본 분산에 지정 계수를 곱함 |
| MES/Fisher 등의 map | 고정된 작은 행렬들 | 실제 MES 전제나 \(R^TC^{-1}R\)에서 도출하지 않음 |

Premise-stress에서 다른 비교 지표는 공통이고, MES에 가장 작은 coupling 0.15를 주었다. 따라서 그 축에서 MES가 유리한 것은 실험으로 발견한 물리적 성질이 아니다. Portability의 source sensitivity도 expansion normalization에 가장 작은 0.10을 준 설정을 반영한다. 저장 결과의 `ONE_ANCHOR_AMONG_FAMILY`라는 신중한 명칭과 별개로, **선택한 비교 축에 목적별 우위가 사전 주입되어 있다**는 독립 판정이 필요하다.

또한 \(Z\sim N(0,1)\)에 대해 generator는

\[
s=1+0.05\{Z-\Phi^{-1}(0.95)\}
\]

로 stress를 만든다. 따라서 \(P(s>1)=0.05\)는 생성식에 내장된다. `partial_id_coverage_rate`는 \(|Z|\le\Phi^{-1}(0.975)\)의 빈도이며, 실제 구성한 partial-identification confidence set이 참 물리 상태를 포함하는지를 검사하지 않는다.

저장된 20,000회 결과의 exceedance 0.05185, coverage label 0.9487은 이 toy의 보존 값이다. 이번 재실행 결과도, 실제 MES 공동검정의 size·coverage 인증도 아니다. 그렇다고 우도 불변성이나 행렬 검증까지 무가치해지는 것은 아니다. [PR254 generator](https://github.com/cosmosapjw-quantum/htt_base/blob/6bafca66285ef071081453313bb7d2d6b261599c/scripts/codex_harness/run_pr254_normalizer_benchmark.py)

# MIO: 무엇을 검정하고 있었는가

## 방향 coherence null과 물리 null

H의 `directional.py`는 다섯 probe의 방향을 inverse-cone-variance로 가중하고, 독립적인 uniform \(S^2\) 방향 표본을 같은 가중치로 비교한다. \((k+1)/(B+1)\)의 rank 계산은 그 **지정된 독립 방향 null**에 대해 재사용할 수 있다.

하지만 표준적인 관측자 운동 자체가 CMB와 물질 number-count dipole에 공통 방향을 만들 수 있다. 따라서 “독립 임의 방향에서 드물다”를 “FLRW 우주에서 드물다”로 바꿔 읽을 수 없다. 방향 일치와 kinematic amplitude 일치도 다른 검정이다. [Secrest 등 원논문의 kinematic dipole 논의](https://arxiv.org/pdf/2009.14826)

저장 `mio_directional_coherence.json`에는

\[
R=0.9989520684,\quad p=0.0002999700,\quad
\chi^2=28.33953685,\quad \mathrm{dof}=3
\]

이 있다. 이는 문헌 기본 방향과 placeholder cone error를 사용한 해당 경로의 결과이며, raw survey 자료의 공동 fit 결과는 아니다.

가중치만으로도 해석의 제한을 정확히 보일 수 있다. CMB 가중치는 4, 나머지 합은 \(161/3600\)이므로 삼각부등식에 의해 모든 방향 배치에서

\[
R\ge\frac{4-161/3600}{4+161/3600}
=\frac{14239}{14561}\simeq0.978.
\]

즉 \(R\)이 1에 가깝다는 사실만으로 강한 공동 정렬을 주장하기 어렵다. **이 하한은 같은 가중치를 사용한 Monte Carlo p-value 자체를 반증하지 않는다.** 문제는 물리 null과 입력 오차 모델을 지정하지 않고 그 p-value를 우주론적 증거로 승격하는 데 있다. [Directional source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/mio/coherence/directional.py)

## 오차·자료·문서 연결의 결함

독립적인 작은 cone을 2차원 tangent Gaussian의 좌표별 표준편차로 모델링하고 공통 축의 두 모수를 fit하면 자연스러운 잔차 차원은 \(2N-2\)다. 코드의 \(N-2\)와 다르다. 그러나 cone containment angle은 곧 좌표별 Gaussian 표준편차가 아니며, 유한 각도에서 weighted resultant가 geodesic \(\chi^2\) minimizer인 것도 일반적으로 아니다. **dof 3을 8로 고쳐 새 관측 유의성을 선언하는 방식으로 수리할 수 없다.** 오차분포와 fitting rule을 먼저 고정해야 한다.

`has_covariance`와 `has_null_mocks`는 certificate 상태에 영향을 주지만, 실제 방향 p-value 계산에 covariance matrix나 supplied mock을 넣지 않는다. Redshift-binned 경로도 label permutation을 수행하며, metadata와 hash만으로 heterogeneous probe의 교환가능성이 생기지는 않는다.

CMB dipole와 BiPoSH에 \(z_{\rm eff}=1100\)이라는 라벨을 붙이는 것은 그곳의 matter velocity를 관측한 것과 같지 않다. Observer boost를 통해 생긴 신호에는 observer response kernel이 필요하다. 깊이 분석은 임의의 scalar redshift label보다 각 자료의 radial/window response를 기준으로 구성해야 한다.

A35 문서의 Radio·CF4·BiPoSH 방향은 실제 code/JSON의 방향과도 다르다. 문서의 best axis \((260.9,42.5)\)와 JSON의 \((263.777,48.122)\)는 같은 결과가 아니다. 따라서 문서의 큰 각도·chi-square 설명을 JSON에 그대로 귀속할 수 없다. Placeholder 오차의 영향이 무시 가능하다는 문장도 검증된 결론으로 읽지 않는다.

## 기존 비판의 적용 범위 교정

PR142 runner의 실제 기본 실험은 **unpaired iid Gaussian toy**와 한 성분 mean shift다. 이전에 지적한 paired \(\Pi\)의 순서 문제는 이 unpaired 저장 toy를 반증하지 않는다. 보존 결과는 \(F\simeq2.14550\), \(p_F\simeq0.08397\), \(\Pi\simeq0.95498\), \(p_\Pi\simeq0.00467\)이며, 해당 generator·검정 범위에 귀속해야 한다. 이 경로의 hidden successor 수리가 있었다고도 주장하지 않는다.

`predictive_residuals.py`에는 실제 typed observable/forward-output에서 TT·TE·EE \(C_\ell\) residual을 만들고 채널·지원 범위를 맞추는 연산이 있다. 그러나 covariance reference는 수치 계산에 쓰이지 않고, full Q/O tensor morphology를 소비하는 경로도 아니다. 저장된 여섯 zero residual은 실제 관측 fit의 성공을 증명하지 않는다. 형식·지원 범위 연결은 재사용하고, correlated residual likelihood는 별도로 연결해야 한다.

# DESI: 실제 관측 계보와 두 수정 의무

## 관측 결과의 존재는 인정해야 한다

E의 dipole card, exact-selection card, PR151 runner와 generated JSON은 실제 DESI DR1 BGS_ANY **5,522,353행**과 random catalog를 사용한 분석 기록으로 연결된다. 이를 toy-only라고 평가하는 것은 부정확하다. 이번에는 raw catalog를 다시 열거나 fit하지 않았으며, manifest가 저장 card의 해시를 연결한다는 사실을 raw catalog 전체의 독립 검증으로 확대하지 않았다.

## ICRS 방향을 Galactic 방향으로 비교했다

`extract_desi_compact.py`는 RA/DEC에서 직접 \(n\)을 만든다. `desi_dipole_measure.py`는 같은 RA/DEC에서 random을 픽셀화하고, 추정 벡터에 회전 없이 `dipole_direction_l_b_deg`라는 이름을 붙인다. 이어 Galactic CMB 방향 \((264.021,48.253)\)과 내적한다. DESI 공식 데이터 모델의 RA/DEC는 **ICRS**다. [DESI 공식 데이터 모델](https://desidatamodel.readthedocs.io/en/stable/DESI_ROOT/survey/catalogs/RELEASE/LSS/SPECPROD/LSScats/VERSION/data_clustering.html)

따라서 이 producer 아래의 저장 방향 \([172.503,-44.665]\)와 CMB separation **122.481도**는 좌표계가 잘못 결합된 결과다. Producer는 H에도 같은 blob으로 남아 있다. 회전은 벡터 크기를 보존하므로 이 결함만으로 진폭 **0.009493**을 부정하지 않는다. 올바른 Galactic 방향·각도는 여기서 계산하지 않았다. [Dipole producer](https://github.com/cosmosapjw-quantum/htt_base/blob/af147f1a3549c81ccfdef7130698580c028512d3/scripts/desi_dipole_measure.py)

## 가중 count와 mock의 분산 법칙이 다르다

실제 입력은 \(D_p=\sum w_{d,i}\), \(R_p=\sum w_{r,i}\)다. 그러나 PR151의 mock은 평균 \(\alpha R_p(1+\delta_p)\)인 정수 Poisson count를 생성한다. 일반적인 weighted Poisson sum은

\[
\mathbb E\!\left[\sum_iw_i\right]=\int w\lambda,
\qquad
\operatorname{Var}\!\left[\sum_iw_i\right]=\int w^2\lambda.
\]

정확한 반례로 모든 가중치가 2이고 \(N\sim\mathrm{Pois}(\lambda)\)이면 실제 \(2N\)의 평균·분산은 \(2\lambda,4\lambda\), 이 mock의 분산은 \(2\lambda\)다. 매 realization에서 alpha와 nuisance를 다시 fit하는 좋은 절차가 이 기본 표본법칙의 차이를 자동으로 고치지는 않는다.

저장 **p=0.721393**은 해당 GRF+Poisson 대리모형의 조건부 rank 결과다. Weighted survey와 release-matched null에 자동으로 보정된 값은 아니다. 실제 영향의 크기는 미평가다. 잘못된 p-value 수치를 새로 계산한 것처럼 제시하지 않는다. [Mock source](https://github.com/cosmosapjw-quantum/htt_base/blob/af147f1a3549c81ccfdef7130698580c028512d3/htt/obsstat/desi_exact_selection_mock.py)

## 후속 18차원 연산자는 중요한 재사용 자산이다

P의 DESI successor는 2 cap × 3 redshift bin × 3 Cartesian component의 관측벡터를 만들고, 각 realization의 normalization·nuisance를 재적합한다. EZmock 1,000개를 covariance용으로, Abacus 25개를 별도 검증군으로 쓰는 경로와 whitening 후 candidate/base response rank·overlap 진단이 있다. [Successor source](https://github.com/cosmosapjw-quantum/htt_base/blob/5a3825f903546891fd90e3d708481707d59babf4/htt/obsstat/desi_successor_formalism.py)

이는 BGS_BRIGHT-21.5, \(0.1<z<0.4\)라는 다른 표본 계약이다. 과거 BGS_ANY 결과를 그대로 재현했다고 말할 수 없다. 이번 정독 범위에서는 이 successor의 실제 관측 실행 완료 결과를 확인하지 못했다. Preflight의 정확한 `R_MAG_APP/R_MAG_ABS` 열 이름도 공식 DR1 모델에 그대로 있지 않으므로 표본 정의·photometry adapter와 연결해야 한다. 이름 불일치만으로 원자료 자체를 사용할 수 없다고 판정해서는 안 된다.

# JWST: 계층모형의 성과와 거리 응답의 소거

## 실제 자료와 조건부 posterior가 존재한다

H의 PR154에는 CCHP 7 host의 JAGB-TRGB, SH0ES 13 host의 JWST-HST 비교가 있다. 원자료 CSV·core·runner의 SHA256은 저장 JSON의 입력 해시와 일치한다. Latent-host Gaussian GLS, host scatter, variance-matched multivariate-t measurement likelihood, method-cell PSD covariance envelope와 \(DCD^T\) contrast covariance, 민감도 sweep 및 독립 oracle test 코드가 있다. **단순 독립-host t-test만 있다는 이전 인상은 교정해야 한다.** [Host hierarchy source](https://github.com/cosmosapjw-quantum/htt_base/blob/5702024e06eff4979087f07f86ee7131d13961ac/htt/htt/htt/infer/jwst_host_hierarchy.py)

| 저장된 독립-host Gaussian 기준 결과 | \(\delta\) 중앙값 [mag] | 95% 구간 [mag] |
|---|---:|---:|
| CCHP | 0.000114 | [-0.064772, 0.062934] |
| SH0ES | -0.039214 | [-0.087093, 0.008887] |

이는 명시된 covariance·prior·host model에 조건부인 **기존 파일의 결과**다. 실제 full covariance를 확인한 재분석도, 이번 posterior 재실행도 아니다. CCHP 값은 원논문 Table 2와, SH0ES 값은 원논문 부록 표와 대응했다. SH0ES CSV의 Table 1 주석은 위치 표기의 오류이며 자료가 허구라는 뜻은 아니다. [CCHP 원논문](https://arxiv.org/html/2408.06153v3), [Perfect Host 원논문](https://arxiv.org/html/2509.01667v1)

## Method contrast는 공통 기하학적 거리를 소거한다

같은 host에 대해

\[
\mu_{Ah}=\mu_{\mathrm{geom},h}(\theta)+z_A+\varepsilon_{Ah},\qquad
\mu_{Bh}=\mu_{\mathrm{geom},h}(\theta)+z_B+\varepsilon_{Bh}
\]

이면

\[
\Delta\mu_h=z_A-z_B+\varepsilon_{Ah}-\varepsilon_{Bh},
\qquad \partial_\theta\Delta\mu_h=0.
\]

이 조건 아래에서는 local boost·global tilt·Bianchi가 만드는 **공통 기하 거리 응답이 difference에서 사라진다.** 이 자료는 calibration·method systematics를 제약하여 공동 분석을 간접적으로 개선할 수 있다. 직접적인 거리 응답을 얻으려면 absolute distance/redshift를 유지하거나, 두 방법에 실제로 다른 selection·관측 반응이 생기는 differential response를 유도해야 한다.

이 결과는 여러 데이터가 있다는 이유로 response matrix에 임의의 독립 열을 추가하면 안 된다는 구체적 사례다. km/s template를 method-difference mag에 직접 붙여 rank가 증가했다고 해도 물리적 식별을 입증하지 못한다.

NGC4258의 공통 maser 기하 거리 오차와 방법별 zero-point 측정 오차도 분리해야 한다. CCHP 원문은 TRGB 0.025 mag, JAGB 0.041 mag의 방법별 오차를 설명한다. 공통 기하 anchor는 contrast에서 소거될 수 있고, 방법별 오차는 여러 host에 공유될 수 있다. 해당 오차가 개별 표의 marginal variance에 이미 들어갔는지 확인한 뒤 배치해야 한다. Rank-one 항을 무조건 더하면 중복 계산 위험이 있다. Companion calibration papers까지의 variance accounting은 이번에 완결하지 않았다. [CCHP calibration 논의, §VIII](https://arxiv.org/html/2408.06153v3)

## Singular covariance posterior에는 정확한 경계 반례가 있다

`_gaussian_log_components`는 \(C+\tau^2I\)의 pseudoinverse로 conditional mean·variance를 만들지만, \(\tau=0\)에서 covariance nullspace가 부과하는 \(\delta\) 제약을 적용하지 않는다.

\[
C=\operatorname{diag}(1,0),\quad y=(0,1)^T,\qquad
y=\delta\boldsymbol1+\varepsilon
\]

를 생각하자. 두 번째 관측식에서 정확히 \(\delta=1\)이다. 하지만 구현식은 평균 0, 분산 \((1+s_\delta^{-2})^{-1}>0\)를 준다. Marginal covariance \(C+s_\delta^2\boldsymbol1\boldsymbol1^T\)는 양의 정부호라 그 grid endpoint가 자동 제거되지도 않는다.

이는 singular PSD envelope 경계의 conditional posterior 결함이다. 저장된 SPD 독립-host 기준 결과를 이 반례가 무효화하지는 않는다. 연속 \(\tau\) 적분의 한 endpoint와 유한 grid 계산의 영향도 구별해야 한다. 재사용할 때는 exact constraint를 처리하거나 정당화된 \(\tau\to0^+\) 극한을 사용하고, 실제 수치 영향은 Local Codex가 검증해야 한다.

Gaussian 경로의 `normalization_relative_error`는 같은 \(\tau\) 간격에서 적분 상한을 0.5에서 0.75로 늘리는 tail 점검이다. 전체 quadrature 오차상한과 같지 않다. 적분 범위와 해상도 수렴은 서로 다른 검사다.

## P의 observed worker는 아직 소비 경로가 닫히지 않았다

P의 JWST runner는 `build_pr309_inputs`에 ADMITTED_FIELD를 전달한다. Core는 필수 competitor인 2MRS가 이 mode이면 무조건 예외를 발생시킨다. 파일 경로를 채우는 것만으로 완료될 경로가 아니다. 이는 source·명세·테스트가 드러내는 미완성 consumer 연결이며, 별도의 H PR154 관측 결과와 구별해야 한다.

같은 core에는 128³ neural velocity field의 실제 trilinear interpolation과 Galactic radial projection이 있다. 이 연산자는 재사용 후보지만, 실제 worker와 아직 연결되지 않았다. Field RMSE는 자동으로 전체 covariance가 되지 않으며, method contrast에 넣을 물리적 응답도 앞 절의 소거 조건을 먼저 통과해야 한다. [JWST current-stack source](https://github.com/cosmosapjw-quantum/htt_base/blob/5a3825f903546891fd90e3d708481707d59babf4/htt/obsstat/jwst_distance_consistency.py)

# 통합 연구의 잠재력과 구체적인 연결 순서

## 연구사는 일관되지만 공동 우도는 아직 하나가 아니다

초기 BASS의 전달 계산, HTT의 관측 응답, MIO의 방향·형태 진단, obsstat의 공동 구간, tensorized MES의 물리 상태와 불변량은 같은 장기 질문으로 연결될 수 있다. 이번 successor 정독은 그 흐름 안에 유효한 연산자가 상당히 있음을 확인했다. 원심사의 문헌상 기여·표현 비교·실증 요구와 업그레이드의 full-tensor·다중 자료 목표를 구별한 이전 심사 대응표도 유지한다.

하지만 모든 결과를 하나의 우도에 넣는 작업은 아직 끝나지 않았다. 특히 MIO나 MES index가 이미 사용한 \(y\)의 결정론적 요약 \(s=g(y)\)이면

\[
p(y,s\mid\theta)=p(y\mid\theta)\,\delta_{g(y)}(s)
\]

라는 결합 구조를 갖는다. 이를 독립 증거처럼 곱하면 같은 정보를 반복 사용한다. 서로 다른 기구·catalog의 자료도 공유 calibration, 동일 host, mask, foreground, simulation seed 등을 통해 의존할 수 있다.

또한 R4에서 확인한 CF4 affine 모형의 radial velocity만으로는 일반적인 vorticity가 식별되지 않는다. 같은 원점을 쓰는 affine gradient의 반대칭 부분 \(\Omega^T=-\Omega\)에 대해

\[
n_i\Omega_{ij}(rn_j)=r\,n^T\Omega n=0.
\]

따라서 radial affine 자료의 정확한 null direction이 있다. 숫자상 rank 부족을 해결하는 임의의 열을 넣을 문제가 아니다. Vorticity에는 추가 관측 성분이나 명시적인 물리 모형 제약이 필요하다. 이 결론은 그 affine 관측식의 정의역에 한정되며 일반 우주론의 모든 관측이 vorticity에 둔감하다는 주장은 아니다.

\newpage

## 재사용과 수정의 우선순위

| 작업 | 먼저 재사용할 자산 | 반드시 닫을 조건 |
|---|---|---|
| 관측 표현 정리 | Directional moments, canonical Q/O, CF4 affine 설계, DESI 18-vector | Frame·parity·단위·kernel·표본 ID |
| MES 물리 연결 | T3/K1R, anchor geometry, GF joint range | 독립된 physical numerator 계약, derivative premise, 실제 response |
| 공동 선형 진단 | Anchored response, nuisance projection, Schur 연산 | 실제 block covariance와 exact null rows |
| CMB 검정 | 기존 Planck/FFP10 경로와 retained full Q/O | Map processing response, noise 재사용·공동 null, nuisance 재적합 |
| 거리·속도 통합 | CF4 covariance/affine 모형, JWST hierarchy, 2MRS interpolation | Absolute distance 보존, contrast 소거, selection·calibration 공동법칙 |
| 물리적 대안 비교 | Native BASS·kinetic·광학 donor, R3 benchmark | 일반 transfer·산란·perturbation, local/global 구분 |

이 순서는 기존 자산을 최대한 활용하면서 원심사 대응과 장기 연구 목표를 연결한다. 모든 분석을 다시 작성하자는 결론도, 이름이 같은 상태를 단순 연결하면 된다는 결론도 아니다.

Local Codex에 넘길 **이번 발견의 최소 수리 계약**은 다음과 같다. 이 항목들은 전체 이론 freeze를 대신하지 않는다.

1. **MES parity:** even scalar/STF2 adapter에는 even만 허용하고 위 inversion witness의 odd 입력을 거부한다. Odd canonical type을 확장하면 그 O(3) 법칙을 별도로 보존한다.
2. **K1R-T9:** exact-data 조건을 추가하고 identity-response interval 반례를 일반 confidence-region 경로에서 유지한다.
3. **MES 비교:** 지정 coupling의 점수를 실제 source/premise perturbation의 산출값으로 바꾸기 전에는 물리적 normalizer 우위로 보고하지 않는다. 공동집합 coverage는 참 상태의 포함 여부를 직접 평가한다.
4. **MIO:** 독립 방향 reference와 공통 local-boost 물리 null을 별도 정의한다. 실제 covariance·joint mocks가 계산 함수에 들어가게 하고 각 probe의 kernel과 오차모형을 고정한다.
5. **DESI:** ICRS에서 Galactic으로 동일한 회전을 data·random·response에 적용하고 방향을 다시 산출한다. 가중 count의 법칙 또는 release-matched mocks를 사용하며 cap·selection·refit을 일치시킨다.
6. **JWST:** Singular conditional posterior에 exact constraint를 반영하고, tail와 grid 해상도 수렴을 구별한다. 공통 거리 신호의 소거와 zero-point variance 포함 규칙을 정한 뒤 2MRS worker를 연결한다.
7. **공동 추론:** 같은 자료에서 만든 anchor·morphology·MIO 요약을 하나의 생성법칙 안에서 재계산한다. 알려진 정확한 covariance의 null rows와 유한 mock의 rank 결손을 구분한다.

구현 담당자가 임의의 물리적 응답을 발명하지 않아도 되는 것은 위에 고정한 좁은 수리들이다. 실제 PR3/CF4/거리 자료의 최종 공동 likelihood, 일반 Bianchi 전달과 비등방 불변량의 응답은 여전히 여기서 이론 판단을 더 해야 하는 영역이다.

# 독립 검토와 남아 있는 전수조사

MIO·방향 MES와 DESI·JWST를 두 독립 경로로 검토하고 주 심사자가 중요 반례·호출 경계를 교차 확인했다. K1R-T9, PR254 비교·coverage, covariance의 exact constraint도 별도로 수학 검토했다. 실제 테스트 실행은 하지 않았다.

판정과 적용 범위는 `FINDINGS_R5.csv`, source의 ref·blob·읽기 수준은 원장에 있다. 기존 R4 패키지와 이전 연구사·결과·정독 이력을 보존했다. 미독 caller나 외부 실행 결과까지 이번 반례가 반증하는 것은 아니다.

남은 작업은 양쪽이다. 첫째, 역사적 BASS·MIO·obsstat의 아직 읽지 않은 버전, 오래된 JSON·dossier·보고서·삭제 파일을 계속 읽어야 한다. 둘째, 주장과 실제 producer의 연결을 확인한 뒤 그 결함이 후속 결과에 미치는 범위를 닫아야 한다. 특히 radio/ACT/Planck의 미독 successor, 과거 evidence 생성의 모든 대체 경로, JWST companion calibration과 외부 실행 결과는 이번 범위에서 새로 완결하지 않았다.

**현재 판정은 “유효한 연구 자산과 실제 관측 결과가 존재하며 잠재력은 크지만, 전수 정독과 통합 물리·통계 추론의 완료는 아직 아니다”이다.** 이 결론은 저장소가 스스로 허용한 claim ceiling을 따르거나 무시해서 얻은 것이 아니라, 읽은 수식·함수·입력·결과·문헌 사이의 실제 대응을 기준으로 얻었다.
