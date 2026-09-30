# Local Codex 전달 프롬프트 — tilt와 observer motion의 분리

첨부한 TILT_BOOST_RESEARCH_20260930.zip 또는 같은 내용의 개별 파일을 읽고, 기존 htt_base의 연구·통계 모듈과 연결해 다음 작업을 수행해줘. 주된 목적은 실제 보유 자료를 이용해 관측자–물질 상대운동을 제약하고, 추가 기하학적 입력이 충족될 때 cosmological tilt의 공동 허용집합으로 연결하는 것이다. 특정 Bianchi type이나 외부 Boltzmann solver를 미리 선택하지 않는다.

## 1. 먼저 고정할 근거

REPORT_KO.md, CLAIMS.json, INDEPENDENT_REVIEW.md, INDEPENDENT_DECISION.json, REVIEW_CORRECTIONS.md, OBSERVATION_CONTRACT.schema.json, NEXT_TASKS.json을 읽어라. 상세 유도는 geometry_findings.md, observations_findings.md, prior_stats_findings.md다. evidence/*.wl과 대응 raw JSON은 여기에서 실행한 소규모 기호 검산이다. 이것을 local xAct/Lean/실제 데이터 테스트가 이미 통과했다는 근거로 사용하지 마라.

이 묶음의 historical repository pin은 3aeecb100d9b938bfffdade093ae8938d84efcfd이며 현재 HEAD라는 주장이 아니다. 실제 checkout의 AGENTS.md, git status, HEAD, 연구 모듈과 최신 handoff를 우선 읽고 차이를 기록해라. 기존 사용자 변경과 원본 자료를 보존하라. 코드 전체 DB나 proof DB의 대량 다운로드/삭제는 이번 작업에 필요하지 않다.

기존 I2 DEFENDED_CONDITIONAL, I3 HOLD_INPUT_INCOMPLETE 및 BIC-07의 관측→공간 jet 결손을 유지하라. 이번 conditional theory promotion을 실관측 승격으로 대체하지 마라.

## 2. 모델 계약

N=선언된 균질 spacelike orbit normal, U=이름을 명시한 물질 성분의 흐름, O=관측자다. Radiation frame R은 별도로 정의한다. 모든 물리 four-velocity는 제곱 -c^2, signature는 (-+++)다.

분류는 eta_UN × eta_OU의 두 축이다. O/U, U/O, O/N, O/R을 reference tag 없이 혼용하지 마라. 방향 비교는 같은 사건과 tetrad로 변환한 four-vector로 수행하라. velocity value, velocity gradient, observer acceleration, source acceleration, astrometric frame spin을 각각 다른 입력으로 취급하라.

Bianchi action이 하나로 식별되지 않으면 허용 action의 집합을 유지하라. 기하학적 N이 없으면 observer–matter 또는 matter–radiation streaming까지만 보고하라. N=R을 이름이나 CMB dipole만으로 강제하지 마라.

## 3. 가장 먼저 수행할 실제 자료 조사

CF4, SDSS PV, Union3/거리 앵커의 작은 metadata와 table schema부터 확인하라. 실제 파일 목록과 해시, sky position, raw redshift 및 frame, 독립 거리 또는 modulus, 보정 이력, source 중복, covariance, selection을 추출하라. 사용자 목록에 있다고 해서 필요한 column이 존재한다고 가정하지 마라.

이미 CMB-frame correction 또는 model peculiar-velocity correction을 한 값을 그대로 observer-motion 추정 입력으로 쓰지 마라. 원래 관측 redshift를 복구할 수 있는지 확인하고, 불가능하면 그 branch를 HOLD로 남겨라. Derived peculiar velocity만으로 같은 velocity model을 다시 검정하는 순환을 피하라. Union3 자료가 압축 likelihood뿐이고 source 방향이 없으면 angular cosmography를 강행하지 마라.

공통 source·distance 계약을 충족하는 자료부터 선택한다. 보유 Planck/ACT map 및 대응 noise/E2E 자료는 다음 cross-check이며, 전부 메모리에 읽지 말고 필요한 resolution/field를 streaming 처리하라. C_l만으로 directional off-diagonal morphology를 대체하지 마라. Redshift drift 또는 아직 확보하지 않은 Gaia 자료가 존재한다고 가정하지 마라.

## 4. 우선 구현할 bounded analysis

관측자 tetrad에서 K=-o+n을 쓴다. 지역 source congruence, smoothing scale, 거리 범위 및 remainder budget을 정하고,
z(d_A,n)=z0(n)+H_O(n)d_A/c+높은 차수 및 잔차
를 공동 추정한다. z0=0을 강제하지 않는다. Reciprocity가 사용 가능하면 d_A=d_L/(1+z)^2로 변환하고, 그 과정의 오차·상관을 함께 전파하라.

A. Intercept 경로:
Z=1+z0=zeta0+zeta·n, zeta0^2-|zeta|^2=1, zeta0>=1에서 beta_U/O=zeta/zeta0를 구한다. 영거리 외삽의 remainder와 cosmological source flow를 local virial region 너머로 연장하는 가정을 먼저 검증한다. 식별되지 않으면 기울기 경로와 별도로 unresolved를 반환한다.

B. Geodesic slope 경로:
H_O=h0+h1·n+q:nn, tr(q)=0.
S00=h0, S0i=-h1_i/2, Sij=qij.
혼합 tensor g^-1 S의 유일한 future timelike eigenline을 구한다. 고유값 s_t에 대해 B=S-s_t g다. Source acceleration이 unrestricted면 이 역변환을 사용하지 마라. Eigensolver의 숫자만 믿지 말고 confidence region 전체에서 timelike branch, norm과 gap을 확인하라. Rank deficiency는 slope-only 판별 실패이지 intercept를 포함한 전체 관측의 실패가 아니다. 이 계산은 omega를 복원하지 않는다.

C. Endpoint 제어량:
R=(1+z)d_A=d_L/(1+z)을 동일 source/ray 기준으로 만들고 aberration reindexing을 적용한다. 같은 incoming ray가 아닐 때 redshift ratio의 완전 소거를 주장하지 마라. 필요한 경우 finite-angle bound와 source-matching 오차를 사용한다. Observed-z로 만든 bin의 z 차이를 독립 depth 정보로 쓰지 마라.

D. CMB cross-check:
고정하거나 추론하는 intrinsic covariance family와 공동 noise law를 선언해 O/R을 추정한다. 자유로운 intrinsic sky의 역 Lorentz 퇴화를 보존하라. Absolute blackbody inverse-temperature criterion은 제한된 scalar-temperature null의 분석적 fixture다. Monopole-subtracted 실지도나 임의 polarization 전체에 무조건 적용하지 마라.

## 5. 기하학적 분기와 과학 검증

Local Wolfram/xAct로 Codazzi 부호와 units, geodesic null-sky lift, boost/intercept convention을 검증하라. SageMath/Singular는 대수적 kernel과 degeneracy strata를 확인하는 작은 작업으로만 사용하고, 검증하지 않은 physical state를 arbitrary algebraic solution과 동일시하지 마라.

Lean/mathlib에서는 우선 null-cone quadratic-form lemma, nonzero spatial expansion eigenvalue 아래 timelike eigenline uniqueness, invariant-clock algebra와 단조 inverse bound 등 작고 독립적인 명제를 formalize하라. Full GR나 관측 reconstruction을 proof assistant가 검증한 것처럼 확장하지 마라. 미완료 정리는 admission 없이 명시적인 미완료 파일/목록으로 남겨라.

N을 복원할 수 있는 branch에서는 metric differential order <=2 scalar I의 nonzero timelike gradient와 물리적 U를 사용해
Xi=h_U(dI,dI)/[-g^-1(dI,dI)]=gamma_UN^2-1
을 계산한다. Ricci-built I가 아니면 Ricci와 그 미분만으로 충분하다고 가정하지 마라. Metric 3-jet을 실제 데이터가 제공했다는 주장을 별도로 입증해야 한다.

단일 perfect fluid의 flux inversion과 Bianchi I structural exclusion은 그 물질 모형에서만 적용한다. 다유체 counterflow의 total flux=0을 각 성분의 non-tilt로 승격하지 마라. Nonzero acceleration/vorticity의 neighbourhood field statement와 pointwise U=N을 구별하라.

## 6. 통계 및 완료 기준

한 공동 likelihood/신뢰집합에서 type/action, eta_UN, eta_OU, tensor observables와 nuisance를 함께 전파하라. 서로 다른 fit에서 고른 extrema를 결합하지 마라. 동시 coverage와 false-exclusion rate를 모의실험으로 확인하라. 최소 fixture는 boosted non-tilted, tilted material-comoving, combined motion, rank-deficient slope, accelerated source, multifluid counterflow, arbitrary intrinsic-sky degeneracy다. 각 fixture의 physical/kinematic 수준을 구별하라.

기존 x,Q,Pi,F,G_F는 정의 버전과 tensor carrier를 먼저 확인하라. 동일 관측조건의 MES denominator가 존재하는 경우에만 normalization하고, state-dependent denominator는 joint fit 안에 유지하라. Ratio/percentage를 posterior probability로 표시하지 마라. Null-space 때문에 사라지는 morphology는 원래 tensor와 함께 보고하라.

최종 결과에는 다음을 포함하라.

- 실행한 commit와 변경 파일, 사용한 실제 데이터·변환·column 계약.
- 명제별 local engine 실행 기록과 재현 명령, 미실행 항목.
- 추정된 공동 범위와 reference frame, 성분, epoch/domain.
- 조건부 배제, 사전 tolerance의 practical equivalence, unresolved의 구분.
- geometric N이 없는 branch의 명확한 한계와 다음 최소 입력.
- 기존 과학적 HOLD의 해소 여부 및 근거. 입력이 충족되지 않으면 유지.

Orchestrator는 NEXT_TASKS.json의 DAG와 acceptance를 사용해 파일/모듈별 작은 작업을 분리하고, 각 하위 모델의 결과를 검증한 뒤 통합하라. 문서상의 계획이나 기호 예제 통과만으로 과학적 완료를 선언하지 마라. 데이터·계약의 concrete blocker가 없는 동안 승인된 구현·검증 작업을 계속 진행하라.

