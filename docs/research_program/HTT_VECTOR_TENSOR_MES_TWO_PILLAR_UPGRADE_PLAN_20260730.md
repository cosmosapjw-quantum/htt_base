# HTT vector/tensor MES 및 두 기둥 증명 프로그램 통합 업그레이드 계획

문서 ID: `HTT-VT-MES-2P-UPGRADE-PLAN-20260730`  
상태: `PROPOSED_NOT_REGISTERED_IN_CANONICAL_DAG`  
대상 기준: `research/pr04-multicomponent@e7c20643c0dd323481f0887aff8e437a1bf7950a`  
작성일: 2026-07-30  
소유자: `COMMON` 계획 문서; 구현 소유권은 아래 패키지별로 분리  
최대 현재 claim posture: pre-solver `diagnostic_only` / roadmap `C2`  
과학 상태 변경: 없음  
관측 사용 승인: 없음  
PR-151 부분 자료 사용: 금지  
native solver 또는 Bianchi family 식별: 없음

이 문서는 첨부된 여덟 텍스트의 모든 업그레이드 제안을 하나의 실행
프로그램으로 정리한 **비정본 제안서**다. 현재 canonical DAG나 theorem
registry를 자동으로 변경하지 않는다. 첫 실행 단계인 `VT-00`에서 현재
권위 문서와 owner 승인을 거쳐 별도 change-set으로 등록되어야 한다.

## 0. 종합 판단

현재 프로젝트는 scalar formalism을 처음 vector화하는 단계가 아니다.
PR-254부터 PR-258까지 다음 기반이 이미 구현되어 있다.

1. typed anchor body, gauge, normalizer benchmark;
2. covariance-supported anchored response geometry;
3. radiation-observer, radiation-matter, matter-observer velocity-response 분리;
4. degree-bounded shear/vorticity/velocity orbit catalogue와 low-\(\ell\)
   matched-counterpair morphology benchmark;
5. finite response-class quotient, open-set abstention, future-native
   `NEEDS_NATIVE` schema.

따라서 다음 프로그램의 중심은 기존 scalar API를 넓히는 것이 아니라,
다음 사슬을 정본화하는 것이다.

\[
\text{typed physical state}
\longrightarrow
\text{SO(3) orbit + O(3) parity type}
\longrightarrow
\text{premise anchor and response geometry}
\longrightarrow
\text{functional/set/path-valued statistics}
\longrightarrow
\text{conditional partial type report}.
\]

첨부안의 핵심 방향은 채택할 가치가 크지만, 그대로 구현할 수는 없다.
독립 물리·통계 감사에서 다음 의미론적 수정이 선행조건으로 확인되었다.

| ID | 원안의 문제 | 이 계획의 결정 |
| --- | --- | --- |
| C-01 | O(3) orbit과 SO(3) orbit을 혼용하면서 pseudoscalar 부호를 보존 | **SO(3) orbit + O(3) parity metadata**를 정본으로 채택. O(3) quotient 출력은 reflection sign을 quotient한다. |
| C-02 | explicit-\(c\) 가속도 정규화와 \(c=1\) Euler 식을 혼합 | 한 convention contract로 다시 유도한다. 등록된 gradient bound 전에는 수치 acceleration ceiling을 금지한다. |
| C-03 | Jacobian rank를 global orbit separation/completeness로 확대 | rank는 local functional independence만 증명한다. global reconstruction, stabilizer, degree completeness는 별도 정리로 둔다. |
| C-04 | `F`를 occupancy, sample pushforward, support utilization의 세 의미로 중복 사용 | `LegacyFView`, `CertifiedFunctionalPushforward`, `SupportUtilizationProfile`을 별도 타입으로 분리한다. |
| C-05 | signed \(\Delta\Omega_k\)를 sign-definite 행에 넣고, \(F\)가 없는 functional에 \(G_F\)를 허용 | eligibility matrix를 수정하고 shape drift는 `FunctionalDepthPath`의 별도 diagnostic으로 둔다. |
| C-06 | `PROFILE_LIKELIHOOD`를 sampling law로 취급 | 확률법칙, likelihood objective, posterior measure를 서로 다른 enum/contract로 분리한다. |
| C-07 | 일반 polytope에서 monotonicity만으로 \(\Pi\) envelope의 vertex extremum을 주장 | quasi-convex/quasi-concave 또는 box-order 증명이 없으면 `OPTIMIZER_REQUIRED`로 중단한다. |
| C-08 | Doob inequality를 “exact, calibration-free test”로 표현 | centered \(L^2\) reverse-martingale의 보수적 path bound로만 사용한다. |
| C-09 | local full rank를 global tilt의 물리적 식별로 승격 | `SEPARABLE_CANDIDATE`까지만 허용하고 systematics/null/held-out/global-injectivity gate를 요구한다. |
| C-10 | 실행 오라클의 단일 PASS를 증명 완료로 읽을 위험 | 오라클, analytic derivation, four-axis CAS, formal proof, statistical validation을 별도 evidence grade로 유지한다. |

최종 추천 명칭은 첨부안의
**Orbit-Resolved Premise-Anchored Inference**를 유지한다. 다만 이 명칭은
framework 이름일 뿐 geometry나 Bianchi family 식별을 뜻하지 않는다.

## 1. 근거와 현재 기준점

### 1.1 첨부 자료 원장

| 소스 | 역할 | 현재 resolvable locator | SHA-256 | 이 문서에서의 증거 등급 |
| --- | --- | --- | --- | --- |
| A1 종합 판단/청사진 | 전체 방향, 상태·orbit·functional·PR DAG | `/home/cosmosapjw/.codex/attachments/2f68ba95-040f-4c28-b5c0-506800e5ac2e/pasted-text.txt` | `f66d426ee711239f620fff10d4fc7ce04d267282c05afc8c6181be4fe7a8513a` | 제안 |
| A2 구현 전 설계·증명 계약 | convention, MES body, VT-T/S, phase/test/kill 기준, legacy 65개 inventory | `/home/cosmosapjw/.codex/attachments/baaadaf8-3177-48e2-a9c3-94139e502d91/pasted-text.txt` | `113cd5a40b352c099fbab8a6e884655fbeba4d579f482fdb56cc4343b31d1ab2` | 제안 + 일부 repo 진단 |
| A3 machine-readable draft | canonical objects, VT-00–12, statuses, tests, kill switches | `/home/cosmosapjw/.codex/attachments/33d1378d-1d38-46f1-a6b8-b23bc5bdb558/pasted-text.txt` | `75d8ac2f40aeb501d046d9c35f56f9bb4e393e191e90eb024cd7b44800682a55` | `PROPOSED_NOT_REGISTERED` |
| A4 Tensor Upgrade | functional eligibility, TF-01–12, exact-test 제안, type ladder | `/home/cosmosapjw/.codex/attachments/c6c1a870-2e28-4467-a7a4-965ffe085ef3/pasted-text.txt` | `f2593ecc293be2a8b4d5e20be0abd545e6ad07026f9b8c713d11ff341721c8d3` | 제안; 수정 필요 |
| A5 Master Proof Registry | 두 기둥 narrative registry | `/home/cosmosapjw/.codex/attachments/6f5b2332-a487-496c-afe7-950b8334627d/pasted-text.txt` | `bd05a0fe26b15effa9450c4281c90e9496498ae92f9f08c3018f6e8671db54be` | 제안 |
| A6 machine-readable registry mirror | 58개 proposition/bridge metadata | `/home/cosmosapjw/.codex/attachments/cb21e207-0d12-4aa6-b827-9179f6fa7e68/pasted-text.txt` | `2dbe47f44b3920318acd78b1f636ca0ba1dc051358da483ea98db2ba6a719c9a` | governance proposal; theorem validation 아님 |
| A7 tensor-foundation oracle | TF-01–12 독립 NumPy/SymPy oracle | `/home/cosmosapjw/.codex/attachments/dda6bc29-ca28-4627-924c-cd0f5779fd18/pasted-text.txt` | `f716cb1bd36930428339f8a7906862f31e9b8a0b5796083bc392bb1811599daf` | 실행형 진단; proof 아님 |
| A8 한국어 요약 | 핵심 결과·우선순위·실행 순서 | `/home/cosmosapjw/.codex/attachments/3462d358-0455-4725-81fd-752b1a51d727/pasted-text.txt` | `5e213beacdee58c1b5116ee4cc98b146ae0d451a936ad058e6aaf27ab6e89981` | 제안 요약 |

첨부 자료의 URL·문헌 언급은 이 문서에서 외부 사실의 독립 검증으로
사용하지 않았다. 관련 정리를 claim-bearing 상태로 올릴 때 해당 PR이
primary literature와 current tool semantics를 별도로 검증해야 한다.

### 1.2 최신 branch와 canonical 상태

작성 시점의 활성 checkout은
`fix/pr151-portable-background-resume@c0269bf5`이며 최신 연구 branch가
아니다. 이 작업은 checkout을 바꾸지 않고 원격과 분리된 detached
worktree에서 최신 대상을 확인했다.

- `git ls-remote`로
  `refs/heads/research/pr04-multicomponent =
  e7c20643c0dd323481f0887aff8e437a1bf7950a`를 확인했다.
- `e7c20643`은 PR-258 candidate `926ae2de`를 PR-257 merge
  `d62d63de`에 병합한 GitHub PR #366 merge commit이다.
- 최신 대상의 DAG는 `205 PRs, DAG valid`다.
- status 기준 완료율은 `152/205 = 74.15%`, dependency-weighted
  `80.72%`다.
- canonical tracked status는 PR-258을 여전히 `pending`으로 두며,
  `Unblocked next`는 `PR-204, PR-258, PR-190`이다.

즉, GitHub merge와 tracked closeout status가 일치하지 않는다. 다음
과학 change-set은 PR-258의 `COMPLETED_SUCCESS` closeout을 canonical
workflow로 동기화한 뒤에만 시작한다. merge commit의 존재만으로
그 status를 수동 변경하지 않는다.

### 1.3 이번 계획 작성 중 실행한 검증

| 검증 | 실제 결과 | 해석 |
| --- | --- | --- |
| 최신 DAG validator | `OK: 205 PRs, DAG valid` | 구조 검증만 통과 |
| 최신 progress report | `152/205`, weighted `80.72%` | 과학적 validity와 무관 |
| PR-257/258 + PR-124/125 집중 88 tests, NumPy 2.4.2 | `87 passed, 1 failed` | PR-124 historical freeze hash 실패 |
| 동일 88 tests, 격리 NumPy 2.3.5 | `87 passed, 1 failed` | 같은 hash 실패; 수치 0 실패는 재현되지 않음 |
| A7 oracle 기본 실행 | TF-01–TF-12 `12 PASS` | single-oracle diagnostic |
| A7 oracle `fast=True` | TF-11 실패 | CI용 empirical threshold가 현재 seed/sample 수에서 불안정 |

남은 재현 실패는 다음과 같다.

```text
tests/contracts/test_pr124_cas_lineage.py::test_frozen_modules_untouched
expected: cc3ba841...
actual:   281a35d1...
```

이는 역사적 PR-124 freeze scope와 PR-252 이후 successor-authority
scope를 분리해야 한다는 첨부 진단을 재현한다.

첨부가 보고한 PR-258의 `0.0` 대 `4.81482486096809e-35` 실패는 위 두
NumPy 환경에서 재현되지 않았다. 따라서 이를 확정 blocker로 과장하지
않는다. 대신 cross-platform portability risk로 등록하고, 원 보고
환경에서 재현되면 scale-aware zero canonicalization을 구현한다.
approximate assertion으로 계약을 약화하는 방식은 금지한다.

## 2. 새 canonical state와 convention contract

### 2.1 세 상태층

#### `CongruenceKinematics`

\[
\mathcal K_u(z,\mathcal W,L)=
\left(
\widehat\sigma_{\langle ab\rangle},
\widehat\omega_a,
\widehat A_a
\right).
\]

필수 payload와 metadata는 다음과 같다.

```text
sigma_stf5
omega_axial3
acceleration_polar3 | MISSING_COMPONENT
frame
congruence
epoch_window
averaging_scale
basis
units_convention
velocity_normalization
parity
perturbative_order
```

자연단위 branch에서는
\(\widehat\sigma=\sigma/\Theta\),
\(\widehat\omega=\omega/\Theta\),
\(\widehat A=A/\Theta\)를 쓸 수 있다. explicit-\(c\) branch에서는
\(\widehat A=A/(c\Theta)\)와 이에 맞는 1+3 Euler equation 및
dimensionless gradient를 함께 고정해야 한다. 두 branch의 식을 metadata
없이 혼합하지 않는다.

가속도 수치 ceiling은 현재 없다. 완전유체, heat flux 및 anisotropic
stress 부재, barotropy, \(1+w\ne0\), named congruence/epoch와 등록된
gradient regularity bound가 모두 있어야 Euler-slaved conditional
ceiling을 만들 수 있다. 그 authority는 `MOMENTUM_CONSTRAINT_NOT_MES`다.
과거 반박된 non-geodesic MES acceleration triple을 복구하지 않는다.

#### `VelocityFrameBundle`

\[
\mathcal V=
\left(
\beta_{{\rm RO},a},
\beta_{{\rm RM},a},
\beta_{{\rm MO},a}
\right),
\qquad
\beta_{\rm RO}
=
\beta_{\rm RM}+\beta_{\rm MO}+O(\beta^2).
\]

- `beta_RM`: radiation–matter, global-matter-tilt candidate;
- `beta_MO`: matter–observer, local boost;
- `beta_RO`: radiation–observer, closure-derived view.

`beta_RO`는 독립 orbit coordinate가 아니다. missing velocity를 다른 두
값으로 자동 추론하지 않는다. closure는 residual과 perturbative order를
보존하고 fail closed한다. legacy `beta` adapter는 semantic role을
입증하지 못하면 abstain한다.

#### `GeometryState`

초기 payload는 signed scalar curvature-budget departure
\(\Delta\Omega_k\)만 가져도 된다. 장기 geometry layer는 다음을 별도
optional block으로 확장한다.

\[
{}^{(3)}S_{ab},\quad E_{ab},\quad H_{ab},\quad
\pi_{ab},\quad\Delta\Omega_k.
\]

\(\Delta\Omega_k\)와 anisotropic spatial-curvature tensor
\({}^{(3)}R_{\langle ab\rangle}\)를 동일시하지 않는다. Weyl/3-curvature
정보가 없는 report의 geometry field는 `PARTIAL`이다.

#### `JointAnisotropyState`

```python
JointAnisotropyState(
    congruence_kinematics=...,
    velocity_frames=...,
    geometry_state=...,
    frame=...,
    congruence=...,
    epoch_window=...,
    averaging_scale=...,
    units=...,
    perturbative_order=...,
)
```

`DepartureState`, `SummaryDepartureState`, `ComponentBreakdown`은
byte/value-stable migration adapter로 유지한다. 새 active inference가
이 adapter를 primary state로 사용하지 않는다.

### 2.2 representation과 quotient

초기 kinematic representation은

\[
V_{\rm kin}=
V_2^\sigma
\oplus V_{1,\rm axial}^{\omega}
\oplus V_{1,\rm polar}^{A}
\oplus V_{1,\rm polar}^{\beta_{\rm RM}}
\oplus V_{1,\rm polar}^{\beta_{\rm MO}}
\oplus V_0^{\Delta\Omega_k}
\]

이며 차원은 \(5+3+3+3+3+1=18\)이다. principal stratum에서 SO(3)
stabilizer가 finite일 때 quotient dimension은 \(18-3=15\)다. 이 셈은
data identifiability나 global separation 정리가 아니다.

프로그램의 정본 group contract는 다음과 같다.

- axis choice quotient: `SO(3)`;
- improper transformation: `O(3)` parity metadata;
- polar vector: \(A,\beta_{\rm RM},\beta_{\rm MO}\);
- axial vector: \(\omega\);
- pseudoscalar sign을 보존하는 report: SO(3) orbit report;
- true O(3) equivalence report: reflection-related sign을 quotient.

### 2.3 필수 limit tests

모든 state/adapter PR은 다음을 서로 다른 fixture로 검사한다.

1. FLRW zero section;
2. no-tilt;
3. local-boost-only exact FLRW;
4. global-tilt-only candidate;
5. acceleration from a non-geodesic congruence;
6. repeated-eigenvalue shear;
7. zero shear;
8. missing component;
9. explicit-\(c\) ↔ natural-unit round trip.

`beta_MO != 0` 또는 `A != 0`만으로 spacetime이 non-FLRW라고 판정하지
않는다. 모든 departure 문장은 frame과 congruence를 양화한다.

## 3. MES를 scalar bound에서 typed anchor body로

### 3.1 `MESAnchorBody`

관측 요약 \(y\), nuisance/premise \(\nu\), 상태공간 \(V\)에 대해

\[
\mathcal A_{\rm MES}(y,\nu)\subset V
\]

를 등록한다. 지원 형태는 block ball, covariance ellipsoid, symmetric
polytope, product body와 finite conditional family다. missing acceleration
anchor를 0-radius ball로 만들지 않는다.

closed, convex, absorbing, origin-containing body에서만 Minkowski gauge를

\[
\rho_{\mathcal A}(k)=
\inf\{\lambda>0:k\in\lambda\mathcal A\}
\]

로 정의한다. balanced, bounded, nonempty-interior가 추가되어야 norm 또는
distance 언어를 사용할 수 있다.

- \(\rho=0\): 고정된 congruence의 kinematic zero section;
- \(\rho=1\): 등록된 anchor boundary;
- \(\rho>1\): 해당 typed anchor/premise와의 incompatibility;
- \(\rho\le1\): FLRW converse, 선형성, source identification을 뜻하지 않음.

closed, convex, balanced 조건에서는 support duality

\[
\rho_{\mathcal A}(k)=
\sup_{\ell\ne0}
\frac{|\ell(k)|}{h_{\mathcal A}(\ell)}
\]

를 사용한다. finite directional catalogue는 global gauge의 lower
approximation일 뿐 모든 방향을 보지 않는 한 equality를 주장하지 않는다.

### 3.2 amplitude, orbit, nonlinearity 분리

canonical diagnostic은 하나의 scalar가 아니라

\[
\left(
\rho_{\mathcal A},
[k/\rho_{\mathcal A}]_{SO(3)},
d_\perp
\right)
\]

다.

- \(\rho_{\mathcal A}\): premise-anchor stress;
- normalized orbit: amplitude-free morphology;
- \(d_\perp\): declared linear/nuisance tangent 밖의 covariance-supported
  residual;
- covariance-null residual: \(d_\perp\)와 별도 보존.

\(\rho>1\)을 nonlinearity라고 부르지 않는다. nonlinearity는 registered
forward response, tangent/manifold, held-out nonlinear candidate와
linear/systematics/frame/derivative-failure alternatives의 비교가 있을 때만
평가한다.

### 3.3 product gauge와 normalizer

등록된 product of block balls에서만

\[
\rho_{\prod_j\mathcal A_j}(u)
=
\max_j\frac{\|u_j\|}{B_j}
\]

를 canonical scalar summary로 쓴다. radius가 zero/missing이면 값을
채우지 않고 typed error를 반환한다. MES, Fisher, expansion,
template-limit, dynamical-breakdown, prior-quantile normalizer 중 universal
winner를 선언하지 않는다. anchor choice가 결론을 바꾸면
`ONE_ANCHOR_AMONG_FAMILY`를 보고한다.

### 3.4 random anchor와 partial identification

같은 realization에서 나온 numerator와 anchor는 joint random object다.
component별 독립 Fieller interval을 붙이지 않고 joint covariance 또는
joint feasible body를 우선한다. structural null과 leading-order
no-channel을 구분하고, denominator identified interval이 zero에서
분리되지 않으면 `RATIO_UNIDENTIFIED`를 반환한다.

필수 anchor statuses:

```text
DEFINED
NO_MES_ANCHOR
ANCHOR_DEGENERATE
CHANNEL_MISMATCH
RATIO_UNIDENTIFIED
STRUCTURAL_NULL
WITHHELD_DERIVATION_MISMATCH
ONE_ANCHOR_AMONG_FAMILY
```

## 4. \((x,Q,\Pi,F,G_F)\)의 typed successor

### 4.1 하나의 문자에 여러 객체를 숨기지 않는다

첨부안에는 `F`에 대한 세 가지 유용하지만 서로 다른 제안이 있다.

1. sign-clean sample의 `CertifiedFunctionalPushforward`;
2. identified set과 anchor의 directional `SupportUtilizationProfile`;
3. domain measure가 있을 때의 occupancy.

이 셋을 하나의 float `F`로 합치지 않는다. successor API는 다음처럼
분리한다.

```text
FunctionalValue
FunctionalStressCoordinate
FunctionalStressProfile
AcceptanceBodyScore
CertifiedFunctionalPushforward
SupportUtilizationProfile
OccupancyMeasure          # optional; explicit domain/measure required
ConditionalExceedanceSurface
FunctionalDepthPath
LegacyXQPiFGView
```

### 4.2 `TensorFunctionalSpec`

모든 functional은 다음을 content-bound metadata로 가진다.

```text
functional_id
source_state_schema
source_state_id
input_representation
output_rank
tensor_degree | homogeneity_degree
O3_parity
quotient_group
frame
congruence
epoch_window
averaging_scale
normalization_id
anchor_id
response_id
perturbative_order
```

출력은 scalar, pseudoscalar, polar/axial vector, PSTF tensor, invariant
vector, orbit stratum, identified set, observable vector 또는 depth path일 수
있다. equivariant output은

\[
\phi(RX)=\rho_\phi(R)\phi(X)
\]

를 만족해야 한다. 모든 출력을 무형식 float array로 평탄화하지 않는다.

raw value

\[
X_\phi=\phi[\mathcal K,\mathcal V,\mathcal G]
\]

와 anchor-normalized stress coordinate를 구분한다. degree \(d>0\)의
homogeneous scalar functional에 matching anchor bound \(U_\phi>0\)가
있을 때만

\[
x_\phi=
\operatorname{sgn}\phi(k)
\left(\frac{|\phi(k)|}{U_\phi}\right)^{1/d}
\]

를 만든다. \(U_\phi=0\)은 `STRUCTURAL_NULL` 또는
`ANCHOR_DEGENERATE`다.

legacy

\[
x_C=\Sigma^2-W^2+\Omega_{\rm tilt}+\Delta\Omega_k
\]

는 `GaussBudgetProjection`이라는 한 functional과
`BC1_LEGACY_PROJECTION` view로 byte/value-stable하게 유지한다. richer
representation 자체는 `BC2_NO_REPRESENTATION_PROMOTION`에 의해 claim을
올리지 못한다.

### 4.3 수정된 eligibility matrix

| functional class | 예 | raw \(X\) | normalized \(Q\) | certified pushforward/support | \(\Pi\) | depth object |
| --- | --- | --- | --- | --- | --- | --- |
| nonnegative, matching anchor | \(\|\sigma\|^2,\|\omega\|^2,\beta^2\) | 허용 | 허용 | sign/admissibility/measure 조건부 | 허용 | `FunctionalDepthPath`; positive one-dimensional case만 legacy \(G_F\) |
| nonnegative, no anchor | \(\|A\|^2\) under current MES | 허용 | `ANCHOR_UNAVAILABLE` | 금지 | registered null 아래 조건부 | generic path only |
| signed scalar | \(\Delta\Omega_k,\operatorname{tr}\sigma^3,\beta\cdot\sigma\beta\) | 허용 | positive typed magnitude/acceptance body가 있을 때만 signed score | occupancy 금지; directional support는 가능 | 허용 | signed support difference/shape path |
| pseudoscalar | \(K_\beta,\beta\cdot\omega\) | 허용 | typed signed score | occupancy 금지 | reflection-null 조건부 | parity path; \(G_F\) 아님 |
| scale-free shape | \(J_\sigma\) | \(I_2>0\)에서 허용 | 이미 normalized; 별도 acceptance body만 가능 | occupancy 금지 | 허용 | `ShapeDepthPath` |
| homogeneous discriminant | \(\Delta_\sigma\) | 허용 | matching typed scale가 있을 때만 | MES occupancy로 해석 금지 | 허용 | `ShapeDepthPath` |
| signed budget projection | \(x_C\) | BC1 | legacy only | legacy only | legacy only | legacy only |

### 4.4 `AcceptanceBodyScore`와 \(Q\)

functional profile \(\mathbf x_\Phi\)의 preregistered acceptance body
\(\mathcal B\)에 대해

\[
Q_{\mathcal B}(\mathbf x)=p_{\mathcal B}(\mathbf x)
\]

를 정의한다.

- unit cube: \(Q=\|\mathbf x\|_\infty\);
- covariance ellipsoid:
  \(Q=(\mathbf x^\mathsf TW\mathbf x)^{1/2}\);
- one-dimensional body: legacy scalar \(Q\).

report는 coordinate, gauge/stress, boundary direction, active
faces/blocks와 identified-set gauge interval \([\rho_-,\rho_+]\)를 함께
보존한다. scalar \(Q\)는 등록된 decision rule에 대해서만 충분할 수
있으며 full state의 sufficient statistic이라고 부르지 않는다.

### 4.5 `SupportUtilizationProfile`과 sample pushforward

closed convex identified set \(\mathcal I\)와 anchor \(\mathcal A\)에 대해

\[
f_{\mathcal I,\mathcal A}(u)
=
\frac{h_{\mathcal I}(u)}{h_{\mathcal A}(u)},
\qquad
F^*_{\mathcal I,\mathcal A}
=
\sup_u f_{\mathcal I,\mathcal A}(u)
\]

를 directional support-utilization으로 보고한다.

\[
\mathcal I\subseteq\mathcal A
\Longleftrightarrow F^*\le1
\]

은 필요한 convex/support 조건 아래에서만 claim한다. report는 signed 및
antipodal ratios, witness directions, active blocks, anchor/identified-set
IDs를 보존한다.

`CertifiedFunctionalPushforward`는 별도 object다.

```text
sample_by_functional
functional_ids
anchor_ids
sign/admissibility decisions
sample covariance
quantiles
optional preregistered scalarization
```

ratio-of-means로 sample-wise ratio의 분포를 대체하지 않는다. 물리적
occupancy나 filling fraction 언어는 explicit domain과 measure가 있을
때만 `OccupancyMeasure`에 허용한다.

### 4.6 `ConditionalExceedanceSurface`

\[
\Pi_{\phi,T}(c\mid\eta)
=
P_\nu
\left[
T(\mathcal Q_{\mathcal A}(X_\phi))\ge c
\mid \eta
\right]
\]

에서 \(\eta\)는 local/global velocity, depth, mask, systematics, frame,
anchor branch 등을 명시한다. \(T\)도 preregistered functional이다.

확률법칙 enum은 다음과 같이 제한한다.

```text
NULL_SIMULATION
FIXED_INJECTION
BOOTSTRAP
RESAMPLING
POSTERIOR_PREDICTIVE
POSTERIOR_PUSHFORWARD
```

`PROFILE_LIKELIHOOD`는 sampling law가 아니며 별도 likelihood/profile
objective다. posterior/PPC mode는 `model_id`, `likelihood_id`,
`prior_id`, data/transfer lineage를 요구하고 HTT가 소유한다. MIO는
mock/null-calibrated diagnostic surface만 소유한다.

partial identification에서는

\[
\underline\Pi(c)=
\inf_{\eta\in\mathfrak I_\eta}\Pi(c\mid\eta),
\qquad
\overline\Pi(c)=
\sup_{\eta\in\mathfrak I_\eta}\Pi(c\mid\eta)
\]

를 보고한다. general polytope에서 coordinatewise monotonicity만으로
vertex enumeration을 허용하지 않는다. 다음 중 하나가 있어야 한다.

- supremum의 certified quasi-convexity;
- infimum의 certified quasi-concavity;
- scalar interval 또는 box-order theorem;
- 검증된 global optimizer.

그 외에는 `OPTIMIZER_REQUIRED`다.

### 4.7 `FunctionalDepthPath`와 legacy \(G_F\)

canonical object는 scalar ratio가 아니라 joint depth/mask path다.

```text
FunctionalDepthPath(
    depth_grid,
    mask_path,
    transported_state,
    orbit_invariant_intervals,
    support_profiles,
    paired_contrasts,
    cross_depth_mask_covariance,
    stratum_transitions,
    change_points,
)
```

두 bin/window의 paired contrast는

\[
\Delta_{ab}=\mathbf F_a-\mathbf F_b,\qquad
C_{\Delta,ab}=C_{aa}+C_{bb}-C_{ab}-C_{ba}
\]

를 보존한다. frame/basis transport가 등록되었을 때만 서로 다른 depth의
방향을 비교한다. zero 또는 sign-changing functional에는 ratio/log를
강제하지 않고 support difference를 쓴다. positive one-dimensional
functional에서만 legacy
\(\exp[\log F_a-\log F_b]\) view를 복원한다.

nested mask에 대해서는 다음 조건이 모두 입증될 때만 reverse-martingale
path를 추가한다.

1. decreasing sigma-field;
2. 하나의 centered square-integrable target \(T\);
3. 각 rung가 \(E[T\mid\mathcal F_j]\);
4. tower consistency;
5. identical target와 preprocessing.

이때 Doob의 결과는 \(E[T^2]\)로 정규화된 보수적 finite-path bound다.
independent rung refit, rung-specific renormalization 또는 다른 target은
해당하지 않는다.

## 5. Orbit catalogue v3와 type atlas

### 5.1 보존할 PR-257 baseline

현재 degree-bounded catalogue의 열두 좌표는 다음과 같다.

\[
\operatorname{tr}\sigma^2,\quad
\operatorname{tr}\sigma^3,\quad
\beta^2,\quad
\beta\cdot\sigma\beta,\quad
\beta\cdot\sigma^2\beta,\quad
K_\beta=\det[\beta,\sigma\beta,\sigma^2\beta],
\]

\[
\omega^2,\quad
\omega\cdot\sigma\omega,\quad
\omega\cdot\sigma^2\omega,\quad
\beta\cdot\omega,\quad
\beta\cdot\sigma\omega,\quad
\beta\cdot\sigma^2\omega.
\]

이 catalogue의 현 claim은 `degree-bounded diagnostic`이다.
`generic_orbit_separation_status`와 `degree_completeness_status`는
`UNPROVEN`으로 유지한다.

### 5.2 Gram–Krylov generator

typed vector family

\[
v_i\in
\{\omega,A,\beta_{\rm RM},\beta_{\rm MO}\}
\]

에 대해

\[
B_{ij}^{(k)}=v_i^\mathsf T\sigma^k v_j,\qquad k=0,1,2
\]

를 생성한다. real trace-free symmetric \(3\times3\) shear에 대해

\[
\sigma^3=
\frac12\operatorname{tr}(\sigma^2)\sigma+
\frac13\operatorname{tr}(\sigma^3)I
\]

이므로 \(k\ge3\) contraction은 환원한다. parity/handedness candidate는
다음 형태를 쓴다.

\[
\epsilon_{abc}v_i^av_j^bv_k^c,\qquad
\det[v_i,\sigma v_j,\sigma^2v_k].
\]

모든 generator는 polar/axial 입력과 SO(3)/O(3) 변환법칙을
machine-readable하게 보존한다. 특히 다음을 구분한다.

- \(K_\omega\): O(3)-even scalar;
- \(K_\beta\): O(3)-odd pseudoscalar;
- polar·axial contraction: pseudoscalar;
- pseudoscalar sign: SO(3) orbit coordinate지만 O(3) orbit invariant는 아님.

`K_omega`는 PR-257의 \(\beta=0\),
\((\sigma,\omega)\leftrightarrow(\sigma,-\omega)\) non-generic witness를
분리한다. 이는 그 witness를 닫는 것뿐이며 generic rank나 completeness를
올리지 않는다. \(K_v^2\)는 Krylov Gram determinant로 기존 even
invariants의 polynomial이므로 새 정보는 sign bit뿐이다.

### 5.3 shear strata

\[
I_2=\operatorname{tr}\sigma^2,\qquad
I_3=\operatorname{tr}\sigma^3,
\]

\[
\Delta_\sigma=\frac12I_2^3-3I_3^2,\qquad
J_\sigma=\sqrt6\,\frac{I_3}{I_2^{3/2}}.
\]

- \(I_2=0\): zero-shear stratum; \(J_\sigma\)는 undefined이므로 abstain;
- \(\Delta_\sigma>0\): simple-spectrum triaxial stratum;
- \(\Delta_\sigma=0,\ I_2>0\): repeated-eigenvalue/axisymmetric stratum;
- \(|J_\sigma|\le1\): \(I_2>0\)인 real STF shear의 algebraic shape bound.

\(J_\sigma\)는 shape coordinate이지 MES anchor나 physical occupancy가
아니다.

### 5.4 cyclic charts와 finite atlas

\[
K(v)=[v,\sigma v,\sigma^2v]
\]

에서 \(\det K(v)\ne0\)인 vector를 cyclic reference로 쓴다.
simple-spectrum/cyclic stratum에서 spectral-projector reconstruction을
통해 local chart를 구성한다. 모든 typed vector를 reference 후보로
평가해 finite chart atlas를 만들되 다음을 report한다.

```text
chart_id
reference_vector_id
exact_cyclicity
Krylov singular spectrum
condition_number
reconstruction residual
chart-overlap residual
stabilizer/stratum
uncovered directions
parity type
```

정확한 nonzero determinant와 numerically stable chart를 구분한다.
어느 candidate도 안정적이지 않으면 분류를 강제하지 않는다.

필수 orbit statuses:

```text
GENERIC_SEPARATING_CHART
WEAKLY_IDENTIFIED_CHART
DEGENERATE_STRATUM
PARITY_TYPED_ONLY
UNCOVERED_DIRECTIONS
COMPLETENESS_UNPROVEN
```

`GENERIC_SEPARATING_CHART`는 해당 chart/domain의 constructive
reconstruction을 뜻할 뿐 global invariant ring completeness가 아니다.
repeated-eigenvalue stratum에는 별도 stabilizer/O(2)-quotient theorem이
필요하다.

### 5.5 증명 경계

다음 evidence를 서로 대체하지 않는다.

1. random Jacobian full rank: sampled regular point의 local independence;
2. constructive inverse: 선언된 chart/domain의 orbit separation;
3. stabilizer analysis: degenerate strata 처리;
4. Hilbert/Molien series: degree/ring completeness;
5. four-axis CAS: 같은 contract 아래 algebraic identity 확인;
6. numerical/property tests: implementation consistency.

global orbit separation은 2와 3이, degree completeness는 4가 있어야 한다.

## 6. Response geometry와 `AnisotropyTypeReport`

### 6.1 local/global response 상태

dipole-only response는
\((\beta_{\rm RM},\beta_{\rm MO})\)의 여섯 parameter를 세 observable로
보므로 일반적으로 rank 3이다. registered boost-only channel이 추가되면
declared model 안에서 full local rank가 가능하다.

다음 상태를 atomic contract로 사용한다.

```text
MISSING_RESPONSE_PROVIDER
NON_IDENTIFIED
SUM_ONLY
WEAKLY_IDENTIFIED
SEPARABLE_CANDIDATE
```

판정은 단순 rank가 아니라 covariance whitening과 nuisance projection
이후의

```text
rank
minimum principal angle
minimum singular value
condition number
held-out wrong-source rate
```

를 함께 쓴다. full rank라도 angle/singular value가 작으면
`WEAKLY_IDENTIFIED`다.

aberration은 observer boost에 대한 first-order channel이다. kinematic
quadrupole은 \(O(\beta^2)\)이며 \(\beta=0\)에서 Jacobian이 0이므로
first-order independent channel로 세지 않고 nonzero fiducial에서의
second-order over-identification check로 쓴다.

`SEPARABLE_CANDIDATE`는 declared two-source model 안의 local
identifiability다. global tilt의 물리적 식별이 아니다. calibration,
foreground, survey window, local structure, response-provider mismatch와
global noninjective counterpairs를 통과하기 전에는 “identified residual”을
금지한다.

### 6.2 세 type level

1. `KinematicOrbitType`: typed state의 SO(3) orbit/stratum;
2. `ObservableMorphologyCompatibility`: declared transfer, mask, covariance와
   feature space에서의 compatibility;
3. `GeometryDynamicalCompatibility`: Weyl/3-curvature/native outputs가 있을
   때만 조건부로 확장.

level 2는 transfer-conditional이며 level 3 또는 Bianchi family ID가
아니다. finite response class는 continuous manifold, physical source,
geometry 또는 family가 아니다.

### 6.3 report schema

```text
AnisotropyTypeReport
  state_contract
  premise_contract
  anchor_body_id and gauge interval
  functional profile and active blocks
  shear stratum and chart conditioning
  SO3 orbit coordinates and O3 parity types
  observable morphology feature blocks
  response rank/null/principal-angle metadata
  local_global_status
  depth_mask_path and joint covariance
  finite response-class compatibility
  unknown/ambiguous abstention
  geometry_type = PARTIAL unless native requirements pass
  uncovered directions
  transfer/null/covariance/sky/mask provenance
  allowed_use and forbidden_use
```

unknown class에는 nearest-known label을 노출하지 않는다. finite class
equivalence와 non-clique closure는 pairwise equality가 아니다.

### 6.4 세 과학축에서 기대하는 positive 결과

#### Global tilt 대 local boost

목표는 “global tilt 검출”이 아니라 다음을 정량화하는 것이다.

- dipole-only `SUM_ONLY`/`NON_IDENTIFIED`;
- aberration/second-order check가 추가한 rank와 conditioning;
- source-specific nuisance/systematics를 포함한 held-out wrong-source FPR;
- local/global `SEPARABLE_CANDIDATE` 또는 honest abstention.

#### Low-\(\ell\) morphology

scalar-, state-, anchor-, orbit-, low-\(\ell\)-feature representation을
matched counterpair에서 비교한다.

```text
same scalar / different tensor phase
same C_ell / different m-phase
same anchor stress / different orbit
same finite support / unknown perturbation
```

power tensor, multipole vectors, T/E/B blocks, BiPoSH/off-diagonal covariance를
feature extractor로 사용할 수 있지만 deterministic template와 stochastic
covariance likelihood를 분리한다.

#### Anisotropy type classification

pre-native taxonomy는

\[
\text{kinematic stratum}\times\text{observable morphology class}
\]

의 partial/open-set report다. native low-\(\ell\) morphology atlas, matched
masks/covariance/nulls, equivalence-class breaking, PPC/LOOCV와 provider gates
전에는 Bianchi family classifier가 아니다.

## 7. 두 기둥 증명 프로그램

### 7.1 현재 registry 기준

최신 `THEOREM_SIGNATURES_V2.yaml`의 live inventory는 다음과 같다.

```text
legacy records:            65
fully typed CHECKED:       12
MIGRATION_PENDING:         53
primary Pillar T:          31
primary Pillar S:          34
owner:                     COMMON
claim tier:                diagnostic_only
```

`CHECKED`는 current v2 typed signature가 완전하다는 뜻이지 vector/tensor
lift나 새 theorem이 완료되었다는 뜻이 아니다. `MIGRATION_PENDING`은
theorem count와 all-parameter prose에서 제외한다.

legacy `THEOREM_REGISTRY.yaml`은 byte-frozen 상태로 유지한다. 새 entry와
수정된 typing은 successor registry에만 추가한다.

### 7.2 첨부 두 기둥 registry의 현재 판정

A5/A6은 arithmetic상 58개의 unique registry row를 가진다.

```text
Pillar I rows:     30
Pillar II rows:    24
Bridge rows:        4
total rows:        58
```

이는 “58개 정리”가 아니다. compound row와 mixed status가 있으므로
`registry rows`라고만 부른다. 현 상태로 canonical adoption은
`BLOCKED_FOR_REGISTRY_ADOPTION`이다.

필수 수리사항은 다음과 같다.

1. frozen 65-ID partition에서 누락된
   `P3, P4, P5, P8, P12, P13, U1`을 복구한다.
2. postbaseline `PR257-NONGENERIC-NONSEPARATION`은 legacy 65 partition
   밖에서 별도 등록한다.
3. mixed rows `II-1.4`, `II-3.3`, `II-5.5`를 atomize하거나
   `component_statuses`를 추가해 conditional component를 승격하지 않는다.
4. bridge `B-1`의 “degree <= 2”를 삭제하고 named-invariant
   factorization/fiber statement로 고친다.
5. `II-5.3`의 “finite-dimensional coordinate ⇒ finite test family”를
   폐기하고 finite preregistered test list와 multiplicity procedure로
   대체한다.
6. `II-3.2`를 corrected centered-\(L^2\) reverse-martingale theorem으로
   내린다.
7. oracle/synthetic/pending-card row를 `ACTIVE`, identification,
   optimal/minimax/complete 언어로 승격하지 않는다.
8. 각 row에 registry owner, scientific owner, claim tier, evidence type,
   transfer lane, assumptions, allowed/forbidden use와 target signature state를
   추가한다.

### 7.3 TF-01–TF-12의 corrected disposition

| TF ID | 내용 | 이번 실행 | 채택 상태 |
| --- | --- | --- | --- |
| TF-01 | polar/axial Krylov parity | PASS | analytic/CAS typing 후보; safe |
| TF-02 | \(\beta=0\) non-generic witness closure | PASS | witness 한정; generic separation 불변 |
| TF-03 | Krylov square = Gram polynomial | PASS | algebraic proof/CAS 대상; sign bit 해석 |
| TF-04 | STF Cayley–Hamilton reduction | PASS | algebraic proof/CAS 대상 |
| TF-05 | shear discriminant와 \(J_\sigma\) | PASS | \(I_2>0\) domain 필수; zero shear abstain |
| TF-06 | principal-stratum invariant dimensions 9/12/15 | PASS | sampled oracle만으로 exact/global claim 금지 |
| TF-07 | budget factorization과 morphology blindness | PASS | named invariant factorization만 허용 |
| TF-08 | product gauge = max saturation | PASS | registered product body 조건부 |
| TF-09 | reflection-odd sign symmetry | PASS | H1–H3 조건부 정리; practical test는 program-only |
| TF-10 | local/global response rank/status ladder | PASS | synthetic local discrimination candidate |
| TF-11 | nested-mask reverse martingale | full PASS, fast FAIL | corrected centered-\(L^2\) theorem 필요; CI empirical gate 재설계 |
| TF-12 | Euler acceleration slaving | PASS | formula shape만 조건부; 수치 ceiling 금지 |

A7의 `12 PASS`는 독립 재구현이 production과 일치한다는 진단이다.
four-axis theorem proof, human derivation, implementation admission 또는
관측 validation을 뜻하지 않는다.

### 7.4 새 VT theorem obligations

#### Pillar T — mathematical physics/theoretical cosmology

| ID | proposition | 현재 disposition |
| --- | --- | --- |
| VT-T1 | typed 1+3 normalization conversion | `READY_AFTER_CONVENTION_REPAIR` |
| VT-T2 | equivariant anchor-body gauge | `READY_FOR_PROOF` |
| VT-T3 | polar support-gauge duality | `READY_FOR_PROOF` |
| VT-T4 | homogeneous functional stress lower bound | `READY_FOR_PROOF` |
| VT-T5 | shear shape/discriminant strata | `READY_FOR_PROOF`, four-axis CAS |
| VT-T6 | STF Cayley–Hamilton contraction reduction | `READY_FOR_PROOF`, four-axis CAS |
| VT-T7 | Krylov determinant factorization/cyclicity | `READY_FOR_PROOF`, four-axis CAS |
| VT-T8 | cyclic-chart SO(3) reconstruction + O(3) parity quotient | `PROGRAM`, global/stabilizer proof와 CAS |
| VT-T9 | polar/axial parity transformation law | `READY_FOR_PROOF` |
| VT-T10 | anchor amplitude–orbit factorization | `READY_FOR_PROOF` |
| VT-T11 | supported linear-response quotient | `CONDITIONAL_PROGRAM` |
| VT-T12 | local/global Schur/principal-angle identifiability | `CONDITIONAL_PROGRAM`, attribution language 제한 |
| VT-T13 | invariant 1+3 evolution identities | `CONDITIONAL_PROGRAM`, four-axis CAS |
| VT-T14 | kinematic-to-geometric type escalation | `PROGRAM_OBLIGATION`, native gate |

#### Pillar S — statistics/real-data analysis

| ID | proposition | 현재 disposition |
| --- | --- | --- |
| VT-S1 | functional-profile data-processing dominance | `READY_FOR_PROOF` |
| VT-S2 | acceptance-body \(Q\) unification | `READY_FOR_PROOF` |
| VT-S3 | matched-null max-\(Q\) simultaneous/FWER calibration | `CONDITIONAL_PROGRAM` |
| VT-S4 | conditional \(\Pi\) survival surface | `READY_AFTER_LAW_TYPING` |
| VT-S5 | partially identified \(\Pi\) envelopes | `CONDITIONAL_PROGRAM`; optimizer contract 필요 |
| VT-S6 | joint random-anchor confidence-body pushforward | `CONDITIONAL_PROGRAM` |
| VT-S7 | certified sample-wise functional pushforward | `READY_FOR_PROOF` |
| VT-S8 | paired depth-contrast covariance | `READY_FOR_PROOF` |
| VT-S9 | ZoA finite-path morphology test | `CONDITIONAL_PROGRAM`; exact-calibration 언어 금지 |
| VT-S10 | weak-identification error bound | `CONDITIONAL_PROGRAM` |
| VT-S11 | orbit-response composition identifiability | `CONDITIONAL_PROGRAM` |
| VT-S12 | matched-counterpair morphology power | `CONDITIONAL_PROGRAM` |
| VT-S13 | open-set abstention/coverage | `CONDITIONAL_PROGRAM` |
| VT-S14 | depth-conditioned local/global discrimination | `PROGRAM_OBLIGATION` |

### 7.5 TC/ST 제안 원장의 보존

A1의 더 긴 theorem catalogue도 폐기하지 않는다. 아래 45개 항목은
VT-T/S obligation, A6의 가장 가까운 row, owner/PR, named consumer/test에
지금 연결한다. `new direct signature`는 A6에 같은 명제 row가 없다는
뜻이며 theorem count를 묵시적으로 늘리지 않는다. 각 VT disposition은
§7.4의 상태를 상속하고, 표의 test를 통과해도 그보다 높은 상태로 자동
승격되지 않는다.

#### Theory/cosmology `TC-01`–`TC-20`

| A1 obligation | VT / A6 target | 상태·선행조건 | owner / PR | named consumer / decisive test |
| --- | --- | --- | --- | --- |
| TC-01 extended typed state | VT-T1; I-1.1–I-1.3 | convention repair 후 | COMMON / PR-260 | `JointAnisotropyState`; units/frame/parity round trip |
| TC-02 shear strata | VT-T5; I-2.4 | PR-260 state 후 proof-ready | COMMON+obsstat / PR-262,268 | `OrbitStratumReport`; zero/repeated/simple-spectrum fixtures |
| TC-03 generic Gram–Krylov separation | VT-T7/T8; I-2.6–I-2.8 | principal-stratum inverse+stabilizer+CAS | COMMON / PR-262,268 | `OrbitAtlasReport`; constructive inverse, counterpair, four-axis CAS |
| TC-04 handedness/parity | VT-T9; I-1.1/I-2.1/I-2.3 | SO(3)/O(3) contract 후 | COMMON / PR-262,268 | orbit/parity report; proper/improper metamorphic tests |
| TC-05 degenerate stabilizers | VT-T8; I-1.3/I-2.4/I-2.8 | separate stabilizer theorem 필요 | COMMON / PR-262,268 | stratum abstention; axisymmetric/zero-shear/O(2) tests |
| TC-06 velocity-frame closure | VT-T1; I-4.5/B-3 | PR-256 semantics+order metadata | COMMON / PR-260 | `VelocityFrameBundle`; closure residual/missing-component tests |
| TC-07 tangent-space classification | VT-T11/T12; I-1.2/II-1.2/II-1.4 | registered response provider 필요 | HTT / PR-266,268 | `AnisotropyTypeReport`; whitened rank/angle/singular-value counterpairs |
| TC-08 MES anchor lifting | VT-T2/T3; I-5.1/I-5.2 | PR-254 body contract 후 | COMMON / PR-261,268 | `MESAnchorBody`; body axioms, gauge/support duality |
| TC-09 stress–orbit factorization | VT-T4/T10; I-3.1/I-5.3/B-1 | corrected named-invariant factorization | COMMON+MIO / PR-261,263,268 | stress/orbit report; equal-stress/different-orbit counterpairs |
| TC-10 acceleration source placement | VT-T1/T13; I-4.1/I-5.6/B-3 | congruence+Euler+gradient authority 필요 | COMMON / PR-260,268 | kinematic state; explicit-\(c\) dimensional and premise-failure tests |
| TC-11 radial-vorticity reopening | VT-T13; I-4.2/I-4.3 | no-go와 higher-order channel 분리 | COMMON+HTT / PR-266,268 | response report; leading-order blindness/reopening mutation |
| TC-12 quotient-response descent | VT-T11; I-5.4/II-1.2 | equivariant response+nuisance quotient | COMMON+HTT / PR-266,268 | response quotient; rotation/nuisance/rank invariance |
| TC-13 morphology reopening | VT-T11; I-3.1/II-6.2 | registered observable feature block | obsstat+HTT / PR-266,270 | morphology compatibility; matched scalar/\(C_\ell\) counterpairs |
| TC-14 irreducible selection rules | VT-T9/T13; I-1.1/I-2.1 | typed polar/axial irreps 필요 | COMMON+obsstat / PR-262,268 | feature generator; forbidden parity/channel mutation tests |
| TC-15 depth transport | VT-T13; B-3 + new direct transport signature | basis/frame transport map 필요 | COMMON+obsstat / PR-265,268 | `FunctionalDepthPath`; transported-direction round trip |
| TC-16 open-set type quotient | VT-T11/T14; II-6.1/B-2 | PR-258 provider+abstention semantics | COMMON+HTT / PR-266,268 | type report; non-clique/equivalence/unknown refusal tests |
| TC-17 realization ladder | VT-T14; I-6.1–I-6.4 | linear/full/interior/constraint tiers 분리 | COMMON / PR-268 | geometry compatibility; unrealizable-point/no-converse tests |
| TC-18 LRS/KS reopening | VT-T13/T14; I-4.5/I-6.2 | exact solution/convention and native ceiling | COMMON+BASS / PR-268 | geometry/native adapter; branch/convention regression |
| TC-19 extended-state FLRW forward implication | VT-T1/T14; B-2 + new direct signature | forward-only; converse 금지 | COMMON / PR-260,268 | state/type report; FLRW/local-boost/non-FLRW countermodels |
| TC-20 future-native transfer functor | VT-T14; I-6.4 + new native-adapter signature | external native provider 전 `OPEN` | BASS+COMMON / PR-268,272 | native adapter schema; missing/wrong-provider refusal |

#### Statistics/data `ST-01`–`ST-25`

| A1 obligation | VT / A6 target | 상태·선행조건 | owner / PR | named consumer / decisive test |
| --- | --- | --- | --- | --- |
| ST-01 functional pushforward | VT-S1/S7; II-2.2 | typed functional+anchor 필요 | COMMON+MIO / PR-263,269 | `CertifiedFunctionalPushforward`; sample-wise vs ratio-of-means |
| ST-02 covariance/null retention | VT-S8/S10; II-1.5/II-4.5 | joint numerator-anchor/depth covariance | obsstat+HTT / PR-261,265,269 | path/inference reports; dropped-cross-block mutation |
| ST-03 support completeness | VT-S1; II-2.2 + new directional-coverage signature | finite catalogue는 lower bound only | COMMON+MIO / PR-263,269 | `SupportUtilizationProfile`; uncovered-direction refusal |
| ST-04 gauge–support duality | VT-S2; I-5.1/II-2.1 | closed convex balanced declared domain | COMMON / PR-261,263,269 | `AcceptanceBodyScore`; primal/dual/property tests |
| ST-05 set-\(Q\)/directional-\(F\) image | VT-S2/S7; II-2.1/II-2.2 | eligibility matrix 통과 | COMMON+MIO / PR-263,269 | score/support reports; signed/unanchored negative controls |
| ST-06 normalizer-rank invariance | VT-S1; I-5.4/II-2.3 | positive invertible rescaling only | COMMON+HTT / PR-261,263,269 | information-gain report; rank-before/after mutation |
| ST-07 anchored Fisher interpretation | VT-S10; II-1.2/II-2.3 | likelihood/response provider 필요 | HTT / PR-266,269 | response report; whitened spectrum and wrong-source test |
| ST-08 joint-covariance Schur information | VT-S8/S10; II-1.5/II-6.3 | full cross blocks 필요 | obsstat+HTT / PR-265,266,269 | depth/response inference; Schur vs block-diagonal mutation |
| ST-09 generic confidence construction | VT-S4/S5/S6; II-4.1–II-4.4 | law, joint body, optimizer certified | HTT / PR-264,269 | \(\Pi\) surface/envelope; registered-DGP coverage |
| ST-10 degenerate tangent-cone inference | VT-S10; I-1.3/II-4.4 | stratum-specific asymptotics 필요 | HTT / PR-269 | weak-ID result; boundary/degenerate undercoverage tests |
| ST-11 conditional \(\Pi\) coverage | VT-S4; II-4.3/II-4.5 | sampling law+joint anchor law | MIO(null)+HTT(posterior) / PR-264,269 | exceedance surface; substitution and composite-null coverage |
| ST-12 \(\Pi\) envelopes | VT-S5; II-4.4 | convexity/box theorem 또는 optimizer | HTT / PR-264,269 | partial-ID envelope; interior-extremum counterexample |
| ST-13 e-value merge | VT-S3/S9; II-3.3 | finite-null correction+arbitrary dependence | MIO+HTT / PR-264,265,269 | multi-lane report; dependent-lane calibration |
| ST-14 estimated-covariance Hotelling/\(t\) | VT-S4; II-4.3 | covariance-estimation regime 명시 | HTT / PR-269 | conditional inference; Hotelling/\(t\)/plug-in coverage |
| ST-15 depth/mask simultaneous bands | VT-S8/S9; II-3.2/II-3.3 | same centered target+nested filtration | obsstat+MIO / PR-265,269 | depth path; noncentered/rung-renormalized negatives |
| ST-16 set-valued \(G_F\) propagation | VT-S5/S8; II-4.1/II-4.2/II-4.4 | signed/zero path에는 ratio 금지 | MIO+HTT / PR-265,269 | path envelope; sign-change/zero-denominator tests |
| ST-17 angle/singular-value abstention | VT-S10/S13; II-1.2 | calibrated thresholds+held-out wrong source | HTT / PR-266,269 | type report; small-angle/constant-rank weak-ID tests |
| ST-18 open-set consistency | VT-S13; II-6.1 | frozen known/unknown DGP와 threshold | HTT / PR-266,270 | open-set report; unknown-to-known false assignment |
| ST-19 E-optimal reopening design | VT-S10/S14; II-6.3 | candidate observable cost/response 등록 | HTT+obsstat / PR-266,269,270 | design report; minimum-singular-value improvement |
| ST-20 anchor stress/nonlinear-gain independence | VT-S1/S10; II-2.3/B-1 | forward manifold+anchor 분리 | MIO+HTT / PR-261,266,270 | stress/nonlinearity report; equal-stress different-residual pair |
| ST-21 scalar data-processing bound | VT-S1; I-3.1/II-6.2 | exact scalar projection 보존 | COMMON+HTT / PR-263,269,270 | scalar baseline; full-vs-projection counterpairs |
| ST-22 cross-survey fusion | VT-S6/S14; II-1.5 + new fusion signature | common estimand+joint cross-survey covariance | HTT / PR-269,271 | fusion surface; overlap/double-count/cross-block tests |
| ST-23 prior exposure | VT-S4/S6; II-1.3 | typed likelihood/prior/null response | HTT / PR-264,269 | posterior-functional report; null-direction KL test |
| ST-24 mask change point | VT-S8/S9; II-3.2 | common target+mask path 필요 | obsstat+MIO / PR-265,269 | depth/mask report; mask-vs-depth attribution controls |
| ST-25 legacy compatibility | VT-S1/S2/S7; II-2.1 + frozen 65 | successor contracts 완료 후 | COMMON / PR-263,267,269 | `LegacyXQPiFGView`; exact byte/value and retraction preservation |

이 목록은 obligation inventory이며 theorem count가 아니다. PR-259는 이
표를 machine-readable하게 옮기는 작업이지, 누락된 의미 연결을 새로
발명하는 작업이 아니다.

## 8. 코드 소유권과 제안 경로

### 8.1 소유권

| package | 소유 범위 | 금지 범위 |
| --- | --- | --- |
| `common` | state/function/action/anchor/report contracts, semantic guards, theorem signature schema | posterior, evidence, observational feature extraction |
| `obsstat` | tensor/low-\(\ell\)/BiPoSH/mask/depth feature extraction, null feature distributions | model-dependent posterior/evidence, family certificate |
| `mio` | diagnostic functional profiles, support utilization, null-calibrated conditional surfaces, depth coherence | model-dependent odds/likelihood/evidence and epistemic-certification language |
| `htt` | model-dependent identified sets, posterior functionals, source-conditioned surfaces, open-set/response inference | native transfer fabrication or attribution of model-dependent inference to MIO |
| `bass_py` / future `BASS_native` adapter | transfer/provider provenance and schema-only native handoff | in-repo native low-\(\ell\) solver simulation |
| manuscript/docs | generated consumers of validated status | hand-maintained theorem counts or claim promotion |

### 8.2 첨부 모듈 제안의 adopted crosswalk

중복 SSOT를 피하기 위해 첨부의 파일명을 그대로 모두 새로 만들지는
않는다.

| 첨부 제안 | adopted target | 결정 |
| --- | --- | --- |
| `htt/src/common/kinematic_state_v2.py` | `joint_anisotropy_state.py` 또는 기존 state module의 versioned successor | 새 canonical state; v1/v2 adapter 보존 |
| `state_functionals.py` | 같은 이름의 common contract module | 채택 |
| `orbit_catalogue_v3.py` | 새 v3 module; `orbit_catalogue_v2.py` adapter/frozen regression | 채택 |
| `anchor_utilization.py` | 기존 `anchor_geometry.py` 확장 + 별도 `support_utilization.py` | 기존 anchor body를 재작성하지 않음 |
| `conditional_exceedance.py` | common schema + MIO null implementation + HTT posterior implementation | 동일 이름의 의미 중복을 피하고 owner를 타입에 포함 |
| `depth_path_geometry.py` | common path contract; obsstat extractor; MIO/HTT consumers | 채택 |
| `theorem_registry_v2.py` | 기존 `theorem_signatures.py`의 v3 successor loader | parallel registry를 새로 만들지 않음 |
| `mio/formalism/state_diagnostics.py` | MIO diagnostic owner | 채택 |
| `mio/formalism/support_utilization.py` | MIO diagnostic owner | 채택 |
| `mio/formalism/depth_morphology.py` | MIO diagnostic owner | 채택 |
| `htt/statistics/orbit_inference.py` | HTT inference owner | 채택 |
| `htt/statistics/posterior_functionals.py` | HTT inference owner | 채택 |
| `htt/statistics/source_conditioned_surfaces.py` | HTT inference owner | 채택 |
| `htt/statistics/depth_path_inference.py` | HTT inference owner | 채택 |
| `obsstat/tensor_feature_packets.py` | obsstat extractor | 채택 |
| `obsstat/lowell_orbit_features.py` | 기존 low-\(\ell\) counterpair API와 통합 | 채택 |
| `obsstat/cf4_morphology_path.py` | data gate 이후 | 조건부 채택 |
| `obsstat/weak_lensing_spin2_features.py` | HSC/KiDS data/response admission 이후 | 조건부 채택 |

핵심 public type은 다음으로 제한한다.

```text
CongruenceKinematics
VelocityFrameBundle
GeometryState
JointAnisotropyState
TensorFunctionalSpec
FunctionalValue
FunctionalStressProfile
AcceptanceBodyScore
CertifiedFunctionalPushforward
SupportUtilizationProfile
ConditionalExceedanceSurface
FunctionalDepthPath
OrbitCatalogueV3Spec
OrbitStratumReport
OrbitAtlasReport
AnisotropyTypeReport
TheoreticalProofRecord
StatisticalProofRecord
LegacyXQPiFGView
```

## 9. 실행 DAG: PR-259–PR-272

### 9.1 prerequisite gate `G0`

새 PR을 시작하기 전에 다음이 모두 충족되어야 한다.

1. `e7c20643`의 PR-258 merge와 exact target ancestry 재확인;
2. canonical `pr_status.yaml`에서 PR-258을 registered closeout workflow로
   `COMPLETED_SUCCESS` 동기화;
3. canonical/compatibility mirror byte comparison;
4. PR-124 historical freeze scope와 PR-252 successor authority scope 분리;
5. PR-258 numerical-zero issue를 원 보고 환경에서 재현하거나
   `NOT_REPRODUCED_ENVIRONMENT_SENSITIVE`로 기록;
6. PR-151 partial data 금지와 pre-native claim ceiling 재확인;
7. `VT-00` formal replan 전 owner 승인.

G0는 새 과학 결과가 아니다. status sync, human acceptance, merge 또는
commit은 이 계획 문서가 승인하지 않는다.

### 9.2 dependency graph

```text
G0 / PR-258 closeout
  |
PR-259  formal replan + registry partition contract
  |
PR-260  canonical state/conventions
  | \
  |  +--------------------+
  v                       v
PR-261 anchor/functionals PR-262 orbit atlas v3
  \                       /
   +-------- PR-263 x/Q/F --------+
              |                   |
              v                   v
          PR-264 Pi          PR-265 depth/mask path
              \                   /
               +---- PR-266 response/type report
                         |
             PR-267 registry v3 + oracle hardening
                    /             \
                   v               v
           PR-268 Pillar T   PR-269 Pillar S
                    \             /
                     PR-270 blind integration
                         |       \
                         v        v
                 PR-271 data   PR-272 proof/report pack
                   pilot          ^
                         \_________|
                     only if data gate passes
```

### 9.3 PR cards

#### PR-259 — Formal DAG replan and exact registry partition

Owner: `COMMON`  
Depends on: G0 / PR-258 completed-success sync  
Maps: `VT-00`, early `VT-08`, original PR-259

Deliver:

- PR-259–272 cards and dependency contracts;
- exact partition of all 65 frozen legacy IDs;
- postbaseline IDs in a separate namespace;
- corrected 58-row proposal schema with component statuses;
- PR-to-VT-to-TC/ST crosswalk;
- no scientific status promotion.

PASS:

- 65 baseline IDs mapped exactly once;
- no missing, duplicate, or foreign ID;
- seven omitted IDs restored;
- mixed rows do not widen component status;
- DAG validator and mirror comparison pass.

FAIL:

- orphan ID;
- simulation/oracle counted as proof;
- PR-258 still pending;
- status promotion performed by the proposal itself;
- a new ledger/gate without a named consumer.

#### PR-260 — Canonical joint state and convention SSOT

Owner: `COMMON`  
Depends on: PR-259; consumes PR-249, PR-256  
Maps: `VT-01`, original PR-260

Deliver:

- `CongruenceKinematics`;
- `VelocityFrameBundle`;
- `GeometryState`;
- `JointAnisotropyState`;
- explicit-\(c\)/natural-unit convention adapters;
- byte/value-stable legacy adapters.

PASS:

- O(3) parity, SO(3) action, units, frame/congruence round trip;
- local-boost-only FLRW and global-tilt-only fixtures remain distinct;
- missing \(A\) or velocity stays missing;
- no acceleration numerical ceiling without a registered gradient authority;
- legacy scalar values reproduce exactly.

FAIL:

- missing component replaced by zero;
- `beta_MO` inserted into geometric departure;
- \(A\) or legacy `beta` semantic role guessed;
- explicit-\(c\) dimensional mismatch.

#### PR-261 — Anchor body and functional contracts

Owner: `COMMON` with `MIO` consumer review  
Depends on: PR-260, PR-254  
Maps: `VT-02`, part of original PR-262

Deliver:

- `TensorFunctionalSpec`;
- anchor-body/gauge/support contract extensions;
- raw value versus stress coordinate separation;
- structural-null/degenerate/missing statuses;
- joint random-anchor schema.

PASS:

- gauge sublevel, support duality and product-body identities on declared domains;
- zero/missing radius fails closed;
- normalizer rank invariance;
- random numerator-anchor cross-covariance retained;
- source/frame/congruence/anchor identities content-bound.

FAIL:

- all outputs flattened to untyped arrays;
- normalizer described as information gain;
- missing anchor fabricated;
- anchor branch omitted from an artifact.

#### PR-262 — Orbit catalogue v3 and stratified atlas

Owner: `COMMON` contract, `obsstat` implementation  
Depends on: PR-260, PR-257  
Maps: `VT-03`, original PR-261

Deliver:

- Gram–Krylov generator;
- \(K_\omega\) witness closure;
- shear strata and cyclic charts;
- SO(3) orbit/O(3) parity contract;
- chart conditioning, overlap, uncovered-direction report;
- CAS contract drafts for proof PRs.

PASS:

- proper/improper metamorphic tests for every generator;
- simple/repeated/zero shear strata;
- exact cyclicity separated from numerical weak identification;
- non-generic witness closed without changing generic/completeness status;
- sampled Jacobian tests labeled local only.

FAIL:

- pseudoscalar called O(3) invariant;
- finite fixtures promoted to global separation;
- chart atlas called a complete invariant ring;
- \(J_\sigma\) evaluated at \(I_2=0\).

#### PR-263 — Functional \(x/Q/F\) successors and compatibility

Owner: `COMMON` contracts, `MIO` diagnostics  
Depends on: PR-261, PR-262  
Maps: `VT-04`, original PR-263 and part of PR-262

Deliver:

- `FunctionalStressProfile`;
- `AcceptanceBodyScore`;
- `CertifiedFunctionalPushforward`;
- `SupportUtilizationProfile`;
- corrected eligibility matrix;
- exact legacy `x,Q,F` views.

PASS:

- signed curvature and pseudoscalar cases route correctly;
- no \(F/G_F\) on unanchored/signed functionals;
- identified-set gauge interval and support witness directions;
- sample-wise pushforward differs from ratio-of-means;
- product/non-product negative controls.

FAIL:

- `F` called probability or physical volume by default;
- support utilization, sample pushforward and occupancy share one ambiguous field;
- legacy byte/value drift;
- shared covariance removed.

After PR-263, run the first five-PR checkpoint for PR-259–263.

#### PR-264 — Conditional \(\Pi\) and identified envelopes

Owner: `MIO` null diagnostic; `HTT` posterior modes  
Depends on: PR-263, PR-250  
Maps: `VT-05`, original PR-264

Deliver:

- probability-law, likelihood-objective and posterior-measure separation;
- typed conditioning surface;
- lower/upper partial-ID envelopes;
- certified optimizer/refusal contract;
- simultaneous/max-\(Q\) calibration lane.

PASS:

- posterior lineage includes model/likelihood/prior/data/transfer IDs;
- MIO and HTT surfaces cannot substitute for each other;
- interior-extremum counterexamples kill invalid vertex shortcut;
- unbounded/uncertified optimization returns `OPTIMIZER_REQUIRED`;
- coverage battery passes on registered DGPs.

FAIL:

- profile likelihood accepted as a probability law;
- point \(\Pi\) from unidentified conditioning;
- \(\Pi\) labeled truth probability;
- marginal anchor intervals used as a joint law.

#### PR-265 — Functional depth/mask path

Owner: `obsstat` extractor, `MIO` diagnostic, `HTT` inference consumer  
Depends on: PR-263  
Maps: `VT-06`, original PR-265

Deliver:

- `FunctionalDepthPath`;
- paired contrasts and full cross-depth/mask covariance;
- frame/basis transport;
- support difference for signed/zero paths;
- corrected reverse-martingale optional lane;
- ZoA/mask change-point diagnostics.

PASS:

- paired/unpaired covariance mutation tests;
- nested sigma-field and same-target verification;
- non-centered and rung-renormalized negative controls;
- Doob result labeled conservative conditional \(L^2\) bound;
- mask variation and depth variation reported separately.

FAIL:

- bins/masks treated as independent;
- arbitrary zero-safe ratio that changes semantics;
- \(G_F\) labeled global-tilt evidence;
- “exact calibration” without the corrected theorem.

#### PR-266 — Response geometry and `AnisotropyTypeReport`

Owner: `COMMON` report contract, `HTT` inference, `MIO` diagnostic
producer/reviewer, `obsstat` features  
Depends on: PR-262, PR-264, PR-265; consumes PR-255/256/258  
Maps: `VT-07`

Deliver:

- weak-identification status extension;
- local/global response gates;
- three-level type ladder;
- open-set abstention integration;
- complete `AnisotropyTypeReport`;
- geometry/native escalation firewall.

PASS:

- dipole rank-3 versus boost-channel rank ladder;
- angle, singular value, condition number and held-out wrong-source gates;
- quadrupole Jacobian zero at \(\beta=0\);
- global noninjective/systematics counterpairs;
- unknown/ambiguous never force a label;
- geometry type remains `PARTIAL`.

FAIL:

- full rank called physical global-tilt identification;
- finite class called family/geometry;
- missing provider represented as zero response;
- covariance-null residual absorbed into supported score.

#### PR-267 — Theorem registry v3 and oracle hardening

Owner: `COMMON`  
Depends on: PR-261, PR-262, PR-266  
Maps: full `VT-08`, original PR-259 completion

Deliver:

- corrected two-pillar narrative and synchronized YAML;
- direct successor signatures, without changing the frozen legacy registry;
- per-row owner/tier/evidence/transfer/allowed-use metadata;
- exact-partition machine report and adjudication note;
- stable TF oracle runner.

PASS:

- 65 legacy signatures preserved;
- 58 proposal rows correctly typed as rows, not theorems;
- B-1, II-3.2, II-5.3 repaired;
- oracle/default/CI modes have deterministic semantics;
- TF-11 fast-mode stochastic failure is removed by analytic contract tests or
  explicitly non-gating Monte Carlo diagnostics.

FAIL:

- primary-status count becomes theorem count;
- `ORACLE_VERIFIED` becomes proof;
- compound row widens a component;
- pending/synthetic card becomes `ACTIVE`.

#### PR-268 — Pillar T proof migration and new proofs

Owner: `COMMON` registry with physics/math adjudication  
Depends on: PR-266, PR-267  
Maps: `VT-09`, original PR-266

Deliver:

- 31 legacy Pillar T migrations;
- VT-T1–T14 dispositions;
- four-axis contracts/results where algebraic claims require them;
- analytic derivations, assumptions, domains and stratum exclusions;
- counterexamples for intentionally restricted claims.

PASS:

- exact same contract across Wolfram+xAct, SymPy, Sage+Singular and Lean;
- `CAS_4AXIS_PASS` only when all four pass;
- acceleration and geometry/native programs remain conditional/open;
- orbit global separation and ring completeness stay separate.

FAIL:

- numerical fit counted as exact theorem;
- unavailable engine collapsed into fewer axes;
- exception registered after reading results;
- local chart proof printed as all-strata theorem.

After PR-268, run the second five-PR checkpoint for PR-264–268.

#### PR-269 — Pillar S proof migration and validation

Owner: `COMMON` registry, `HTT`/`obsstat` scientific owners  
Depends on: PR-266, PR-267  
Maps: `VT-10`, original PR-267

Deliver:

- 34 legacy Pillar S migrations;
- VT-S1–S14 dispositions;
- exact-versus-asymptotic tags;
- coverage, covariance, multiplicity and optimization batteries;
- finite preregistered test-family contract replacing II-5.3.

PASS:

- retained-DGP coverage;
- covariance estimation regime explicit;
- multiple functional/mask/threshold/stratum choices in multiplicity plan;
- sign test H1–H3 and abstention;
- reverse-martingale conditions machine-checked.

FAIL:

- undercoverage hidden;
- optimizer failure silently returns a point;
- nested mask signs pooled binomially;
- Hunt–Stein/minimax language without a complete decision problem.

#### PR-270 — Blind synthetic integration and adversarial validation

Owner: `HTT` integration; independent reviewers  
Depends on: PR-268, PR-269  
Maps: `VT-11`, original PR-268

Deliver:

- scalar vs state vs orbit vs full-method blind comparison;
- matched scalar/\(C_\ell\)/anchor counterpairs;
- coverage, confusion, abstention, wrong-source and robustness metrics;
- mutation battery;
- frozen diagnostic artifact pack.

PASS:

- richer representation reduces declared confusion or expands honest
  abstention without inflating false source/type candidates;
- empirical claims carry null/covariance/sky/transfer metadata;
- scalar baseline retained;
- all failures/negative results preserved.

FAIL:

- false source/type ID not reduced;
- unknown forced to known;
- same samples tune thresholds and report held-out performance;
- synthetic performance described as real-data/family validation.

#### PR-271 — Admitted existing-data pilot

Owner: `obsstat` data adapters, `HTT` inference  
Depends on: PR-270 and separate data admission gates  
Maps: original PR-269

Candidate lanes:

- Planck public low-\(\ell\) products;
- CF4 admitted compact products;
- HSC/KiDS spin-2 products if response/covariance admission passes.

Required:

- exact release/product/source identity;
- `artifact_mode`, applicable `claim_tier`, owner와 scope;
- exact generating procedure, config/input identities와 random seeds/tolerances;
- git commit 또는 dirty worktree identity;
- `sky_support_status`, mask/selection identity와 directional convention;
- `null_mock_status`, covariance status와 joint-block availability;
- common mask/selection definition;
- joint covariance including cross blocks;
- nuisance refit;
- transfer/provider provenance;
- predeclared nulls and thresholds.
- allowed/forbidden use와 caveats.

Hard stops:

- PR-151 partial bytes;
- incomplete/background acquisition;
- DESI partial data;
- same-data likelihood double counting;
- unavailable joint covariance;
- native/family-dependent response fabricated from a proxy.

The honest terminal result may be `NO_ADMITTED_DATA_PILOT`. 이 경우
PR-272는 synthetic/methods-only 결과만 소비한다.

#### PR-272 — Proof atlas, report and external replication pack

Owner: `COMMON` builder, manuscript consumers  
Depends on: PR-270; conditionally consumes PR-271  
Maps: `VT-12`, original PR-270

Deliver:

- registry-generated theorem list;
- proof atlas and artifact manifest;
- methods/report text generated from validated statuses;
- reproducible commands and isolated-environment receipts;
- external replication package;
- manuscript build/figure/provenance audits.

PASS:

- clean checkout rebuild;
- generated theorem list equals registry;
- only validated/conditional-safe claims promoted;
- figures are concrete analysis, not governance graphics;
- no manual theorem count;
- all report metadata and forbidden-use labels present.

FAIL:

- failed/open/proposed row printed as established;
- stale or quarantined figure enters report;
- external transfer described as native;
- MIO diagnostic and HTT posterior combined;
- public manuscript claims family identification.

### 9.4 원안 PR 번호 crosswalk

| 원안 | adopted location | 변경 이유 |
| --- | --- | --- |
| PR-259 registry | PR-259 schema/partition + PR-267 full registry | state/orbit contracts 전에 새 theorem을 성급히 고정하지 않기 위해 분리 |
| PR-260 state | PR-260 | 유지 |
| PR-261 orbit | PR-262 | anchor/function contract와 병렬화 |
| PR-262 functional \(X\) | PR-261 contract + PR-263 values | raw functional과 anchor-normalized statistic 분리 |
| PR-263 \(Q/F\) | PR-263 | 유지, 세 `F` 의미 분리 |
| PR-264 \(\Pi\) | PR-264 | 유지, law/objective 수정 |
| PR-265 \(G_F\) path | PR-265 | 유지, generic path와 legacy ratio 분리 |
| PR-266 Pillar T | PR-268 | response/type와 corrected registry 이후로 이동 |
| PR-267 Pillar S | PR-269 | 동일 |
| PR-268 blind benchmark | PR-270 | proof gates 이후 |
| PR-269 data pilot | PR-271 | admitted-data hard gate 추가 |
| PR-270 report/pack | PR-272 | proof/data split 반영 |

## 10. 통합 검증 계획

### 10.1 validation matrix

| 축 | 필수 검증 |
| --- | --- |
| conventions | signature, units, \(c\), frame, congruence, epoch, normalization round trip |
| limits | FLRW, no tilt, local boost, global tilt, zero denominator, singular covariance, rank deficiency |
| group action | SO(3) equivariance, O(3) parity, proper/improper metamorphic tests |
| orbit | simple/repeated/zero strata, cyclic/noncyclic charts, overlaps, global counterpairs |
| anchor | body axioms, gauge/support duality, product/non-product controls, random-anchor covariance |
| functional | eligibility, structural null, signed/shape paths, legacy byte/value reproduction |
| statistics | \(\Pi\) coverage, optimizer counterexamples, covariance estimation, multiplicity, abstention |
| depth/mask | joint covariance, paired contrasts, transport, martingale assumptions, change points |
| response | rank/angle/singular values, nuisance projection, wrong-source FPR, provider binding |
| integration | matched counterpairs, open-set unknowns, false-candidate rate, mutation tests |
| packaging | isolated wheel/import, source identity, `pip check`, no repo-root hidden dependency |
| claims | banned language, owner/tier/transfer/null/covariance/sky metadata |

### 10.2 four-axis CAS

다음 claim은 하나의 `CAS_CONTRACT.json` 아래 네 비축약 축을 요구한다.

1. Wolfram Engine + xAct;
2. SymPy + 필요한 high-precision numeric checks;
3. SageMath + Singular;
4. Lean + mathlib/project libraries.

`CAS_4AXIS_PASS`는 네 축 모두 같은 contract hash로 PASS일 때만
가능하다. engine 미설치/timeout은 `CAS_BLOCKED`이지 computation-class
exception이 아니다. 다수결을 금지하고 conflict는 minimal counterexample로
재심한다.

### 10.3 기본 명령

각 PR은 최소한 다음을 실행하고 PR delta에 실제 결과를 기록한다.

```bash
python scripts/codex_harness/validate_pr_dag.py \
  docs/codex_handoff/pr_backlog.yaml

python scripts/codex_harness/progress_report.py \
  docs/codex_handoff/pr_backlog.yaml \
  docs/codex_handoff/pr_status.yaml

python scripts/codex_harness/run_subset.py --list
python -m pytest -m smoke -q
python -m pytest --collect-only -q
```

source-layout `PYTHONPATH`는 `htt/bass/statistics.py`가 stdlib
`statistics`를 shadow할 수 있으므로 임의로 조립하지 않는다. repository
harness 또는 isolated installed package를 우선하고,
`inspect.getsourcefile()`로 실제 import source를 기록한다.

### 10.4 five-PR checkpoints

- PR-263 후: PR-259–263 capability/claim/test checkpoint;
- PR-268 후: PR-264–268 statistics/registry/proof checkpoint;
- PR-272 후: final program checkpoint.

각 checkpoint는 completed count, dependency-weighted progress, collection
status, failures/skips, claim drift, blockers와 next slice를 기록한다. 새
DAG가 등록되면 denominator가 바뀌므로 현재 `74.15%`에서 단순 선형
예측을 하지 않는다.

## 11. 즉시 kill switches와 claim-withholding criteria

### 11.1 구현 즉시 중단

1. scalar anchor stress를 nonlinearity 또는 FLRW distance/converse로 표현;
2. observer boost를 geometric departure에 합산;
3. missing \(A\), anchor, response provider를 zero로 대체;
4. pseudoscalar를 O(3) invariant로 표기;
5. generic chart를 complete invariant ring으로 승격;
6. shared/cross covariance 제거;
7. \(\Pi\)를 truth probability로 표현;
8. `F`를 기본 physical occupancy/filling fraction으로 표현;
9. \(G_F\)를 global-tilt evidence로 표현;
10. unknown class를 nearest known class로 강제;
11. PR-151 partial data 사용;
12. `PROFILE_LIKELIHOOD`를 sampling law로 사용;
13. monotonicity만으로 general-polytope vertex envelope 출력;
14. Doob bound를 exact calibration이라고 표기;
15. local full rank를 physical global-tilt identification으로 표현;
16. covariance-null residual을 supported score에 흡수;
17. registry statement와 executable contract 불일치;
18. fast oracle의 stochastic threshold 실패를 test relaxation으로 숨김;
19. legacy registry/status를 새 proposal이 직접 수정;
20. native/family response를 synthetic/external proxy로 채움.

### 11.2 claim 보류

- nonidentical generic orbits가 같은 catalogue를 가지면 complete classifier
  claim 보류;
- normalizer가 response rank를 바꾸면 implementation error;
- support/orbit profile이 held-out confusion을 개선하지 못하면 empirical
  significance claim 보류;
- anchor family에 따라 source conclusion이 뒤집히면
  `ONE_ANCHOR_AMONG_FAMILY`;
- \(\Pi\) envelope가 대부분 \([0,1]\)이면 source-information claim 보류;
- mask/ZoA variation이 depth variation보다 크면 depth coherence claim 보류;
- local/global tangent overlap 또는 \(s_{\min}\)이 작으면
  `WEAKLY_IDENTIFIED`/`SUM_ONLY`;
- degenerate stratum에서 undercoverage이면 tangent-cone/second-order
  method 전까지 inference claim 보류;
- parity H1–H3 중 하나라도 실패하면 sign test abstain;
- finite-dimensional invariant coordinates만으로 multiplicity closure를
  주장하지 않음;
- admitted data/joint covariance가 없으면 real-data pilot claim 없음.

## 12. 산출물과 성공 기준

### 12.1 required artifacts

```text
canonical state and adapter contracts
typed functional and anchor-body schemas
orbit catalogue v3 and stratum reports
functional stress/Q/pushforward/support/depth reports
conditional exceedance and optimizer reports
AnisotropyTypeReport
corrected two-pillar registry and exact 65-ID migration report
TF oracle with stable CI semantics
four-axis CAS contracts/results/adjudications
synthetic benchmark and mutation pack
optional admitted-data pilot
generated proof atlas/report/replication pack
```

### 12.2 program-level success

이 프로그램은 다음을 달성하면 성공이다.

1. scalar cancellation을 보존해야 할 budget projection과
   cancellation-free anchor stress를 구분;
2. amplitude, orbit morphology, response nonlinearity를 서로 다른 object로
   제공;
3. local/global/unknown/weak-identification을 fail closed하게 구분;
4. 모든 legacy proof ID와 scalar 값을 손실 없이 재현;
5. proposed/conditional/proved/validated 상태를 자동 소비자가 혼동하지
   않음;
6. native solver 도착 시 adapter가 새 state/orbit/type contract를 소비할
   수 있음;
7. negative/partial/no-data 결과도 정직한 terminal artifact로 남음.

family identification, geometry detection 또는 관측 excess는 이 프로그램의
성공 기준이 아니다.

### 12.3 최초 실행 순서

실행 승인이 주어지면 첫 작업은 코드 구현이 아니라 다음 세 가지다.

1. PR-258 tracked closeout sync를 owner workflow로 완료;
2. 재현된 PR-124 freeze-scope 실패를 별도 정확성 change-set 또는
   PR-259 prerequisite로 해소;
3. PR-259 formal replan에서 이 문서의 corrected crosswalk만 canonical
   DAG에 등록.

그 뒤 PR-260 state capability로 즉시 이동한다. assurance-only PR을
연속해서 늘리지 않는다.

## Appendix A. 첨부 제안 전수 추적표

### A.1 상위 업그레이드 제안

| ID | source | 제안 | 채택 위치 | named consumer / decisive test |
| --- | --- | --- | --- | --- |
| U1 | A1, A2, A8 | scalar-first active SSOT를 typed state → orbit/type → response → conditional partial classification 사슬로 교체하고 scalar는 compatibility view로 보존 | §§0, 2–6; PR-260–266 | `AnisotropyTypeReport`; scalar-equal tensor-counterpair/open-set abstention |
| U2 | A1, A2, A3 | `CongruenceKinematics`, `VelocityFrameBundle`, `GeometryState`, `JointAnisotropyState`와 frame/congruence/epoch/window/scale/basis/units/parity/order metadata 도입 | §2; PR-260 | orbit/response adapters; frame/unit/epoch round trip and missing-component refusal |
| U3 | A1, A2, A4 | STF shear, axial vorticity, polar acceleration/velocity, optional curvature의 typed irreps와 derived \(\beta_{\rm RO}\) closure | §2.2; PR-260 | `OrbitCatalogueV3Spec`; proper/improper action and closure-residual tests |
| U4 | A1, A2, A3 | scalar MES를 closed-convex `MESAnchorBody`로 lift하고 \(r\), orbit shape, \(d_\perp\), covariance-null residual을 분리 | §3; PR-261 | functional/type reports; body axioms, gauge/support, null-residual mutation |
| U5 | A1, A2, A3, A4 | \(x,Q,F,\Pi,G_F\)를 functional/set/path-valued typed successor로 교체하되 exact scalar projection을 보존 | §4; PR-263–265 | MIO/HTT/report builders; eligibility, joint covariance, optimizer, exact legacy replay |
| U6 | A1, A2, A4, A7 | PR-257 degree-bounded catalogue를 parity-typed stratified Gram–Krylov atlas, cyclic charts, conditioning, abstention으로 확장 | §5; PR-262 | `OrbitAtlasReport`/obsstat; stratum/metamorphic/reconstruction/CAS tests |
| U7 | A1, A2, A3, A5, A6, A8 | object/proof-grade/consumer/supersession metadata가 있는 two-pillar successor registry와 65개 legacy one-time migration | §7, Appendices A.2/B; PR-259/267–269 | theorem/report generators; 65 exact partition, 58 row typing, status/claim lint |
| U8 | A2, A3, A8 | premise/anchor, kinematic orbit, observable morphology, local/global status, depth/mask path, open-set abstention, provenance를 잇는 `AnisotropyTypeReport` | §6; PR-266 | HTT/MIO/manuscript consumers; schema, owner separation, unknown/partial refusal |
| U9 | A1, A2, A8 | rank/principal angle, minimal reopening observable, morphology block, \(K\times M\) pre-native taxonomy를 사용하되 geometry/family escalation은 native gate 뒤로 보류 | §6; PR-266/270–272 | response design and blind benchmark; rank/angle/wrong-source/matched-counterpair tests |

이 표의 아홉 행은 서로 대체 가능한 요약이 아니다. PR-259의 formal
replan은 이 source→consumer→test edge를 machine-readable DAG로 옮기고
검증해야 하며, 연결되지 않은 행을 “묵시적으로 반영됨”으로 닫을 수
없다.

### A.2 A5/A6 58-row 제안 registry의 corrected disposition

아래 표는 A5/A6의 모든 unique row를 보존한다. 표의 status token은
**A6의 제안 상태를 감사 결과로 제한해 옮긴 것**이며, current canonical
registry에 채택되었다는 뜻이 아니다. `row`는 theorem 수가 아니며,
`MIXED` row는 atomization 전까지 구성요소보다 높은 status를 가질 수
없다.

| Row | Pillar | A6 status / 감사 disposition | target / 필요한 조치 |
| --- | --- | --- | --- |
| I-1.1 | I | `ORACLE_VERIFIED` | typed TF-01 signature 신설; analytic/CAS adjudication 전 theorem count 제외 |
| I-1.2 | I | `ORACLE_VERIFIED` | typed TF-06 signature 신설; exact-dimension prose 전 proof 추가 |
| I-1.3 | I | `PROPOSED` | orbit-stratification signature; theorem count 제외 |
| I-2.1 | I | `PROVEN_CAS4` | PR-257 parity signature를 CAS contract에 결속; catalogue completeness로 확대 금지 |
| I-2.2 | I | `PROVEN_CAS4` | PR-257 Cayley–Hamilton signature; TF-04는 보조 oracle evidence |
| I-2.3 | I | `PROVEN_CAS4` | PR-257 Krylov–Gram signature; TF-03만으로 data-test validity 주장 금지 |
| I-2.4 | I | `ORACLE_VERIFIED` | typed TF-05 signature; all-strata prose 전 domain 명시 |
| I-2.5 | I | `ORACLE_VERIFIED` | typed TF-02 signature; 단일 witness closure만 허용 |
| I-2.6 | I | `PROPOSED` | catalogue-v3 construction spec; 구현/완료 아님 |
| I-2.7 | I | `PROPOSED` | principal-stratum separation signature; generic separation 미증명 |
| I-2.8 | I | `OPEN` | invariant-ring completeness open item; downstream assumption 금지 |
| I-2.9 | I | `PROVEN_CAS4` | PR-257 nonseparation signature; postbaseline이며 frozen 65 밖 |
| I-3.1 | I | `ORACLE_VERIFIED` | typed TF-07 signature; B-1 수정 전 채택 금지 |
| I-3.2 | I | `ACTIVE_CONDITIONAL` | `SIG-P1` migration; budget-coordinate 범위로 제한 |
| I-3.3 | I | `ACTIVE` | `SIG-OMK-REOPEN` migration; theorem prose 전 full typing |
| I-4.1 | I | `ACTIVE_CONDITIONAL` | typed TF-12 signature; \(\epsilon_g\) 권위 전 formula-shape only |
| I-4.2 | I | `ACTIVE` | `SIG-P9` migration; radial-vorticity no-go 보존 |
| I-4.3 | I | `ACTIVE_CONDITIONAL` | `SIG-P22` migration; 조건부 상태 보존 |
| I-4.4 | I | `ACTIVE_CONDITIONAL` | `SIG-P13` migration; A6 누락 partition 복구 |
| I-4.5 | I | `ACTIVE` | `SIG-KE-FRAME/OBS/DYN` 각각 migration; numerical dynamics와 proof 분리 |
| I-5.1 | I | `PROVEN_CAS4` | `PA-THM-GAUGE-SUBLEVEL`; converse/physical-truth claim 금지 |
| I-5.2 | I | `PROVEN_CAS4` | `PA-THM-PRODUCT-BALL`; gauge와 signed sum 구분 |
| I-5.3 | I | `PROVEN_CAS4` | `PA-THM-ONE-WAY-MES`; one-way implication만 |
| I-5.4 | I | `PROVEN_CAS4` | `PA-THM-RANK-INVARIANCE`; rescaling을 information gain으로 해석 금지 |
| I-5.5 | I | `RESTRICTED` | `J1-EXACT` counterexample/surviving statement로 교체 |
| I-5.6 | I | `ACTIVE` | `SIG-MES-BR/REFREEZE/MESB-TRACE` 보존; acceleration authority 추가 금지 |
| I-6.1 | I | `ACTIVE_CONDITIONAL` | `SIG-T3-lin` migration |
| I-6.2 | I | `ACTIVE_CONDITIONAL` | `SIG-T3-full` caveat 보존; full realizability 금지 |
| I-6.3 | I | `ACTIVE_CONDITIONAL` | `SIG-T3-int` migration |
| I-6.4 | I | `OPEN` | tensor realizability open item; type ladder와 동일시 금지 |
| II-1.1 | II | `ACTIVE` | `SIG-P18` scope만 restate; status 불변 |
| II-1.2 | II | `ORACLE_VERIFIED` | typed TF-10 signature; diagnostic candidate only |
| II-1.3 | II | `ACTIVE` | `SIG-P28`를 functional별로 migration |
| II-1.4 | II | `MIXED` | `P8 ACTIVE`, `P10 ACTIVE_CONDITIONAL`, `P30 ACTIVE`; atomize/component map |
| II-1.5 | II | `ACTIVE_CONDITIONAL` | `SIG-P34` tensor scope; status 승격 금지 |
| II-2.1 | II | `ORACLE_VERIFIED` | TF-08와 product-ball CAS evidence를 별도 보존 |
| II-2.2 | II | `PROPOSED` | functional well-posedness contract를 artifact 전 강제 |
| II-2.3 | II | `ACTIVE_PENDING_BINDING` | PR-253 `MesInformationGainReport`의 exact merged evidence를 결속 |
| II-3.1 | II | `ORACLE_VERIFIED` | typed TF-09; H1–H3 실패 시 abstain |
| II-3.2 | II | `ORACLE_VERIFIED_NEEDS_REWRITE` | typed TF-11; centered-\(L^2\) reverse-martingale로 수정 |
| II-3.3 | II | `MIXED` | `P19 ACTIVE_CONDITIONAL`, `P29 ACTIVE`; atomize/component map |
| II-4.1 | II | `ACTIVE` | `SIG-T1p`와 `SIG-DL1`을 원자적으로 보존 |
| II-4.2 | II | `ACTIVE` | `SIG-T2G` 보존; `P36/T2p` retraction을 숨기지 않음 |
| II-4.3 | II | `ACTIVE_CONDITIONAL` | `SIG-T4p/T5p` migration; estimated-covariance regime open |
| II-4.4 | II | `PROPOSED` | `TS-ENVELOPE` signature; 구현/test 전 claim 금지 |
| II-4.5 | II | `RESTRICTED` | `J2-UNIFORM` counterexample; marginals에서 uniform validity 추론 금지 |
| II-5.1 | II | `PROPOSED` | `TS-MAXIMAL-INVARIANT`; conditional future tense |
| II-5.2 | II | `PROPOSED` | `TS-MINIMAX`; optimal/minimax caption 금지 |
| II-5.3 | II | `PROPOSED_INVALID_AS_WRITTEN` | finite preregistered test family + multiplicity contract로 전면 수정 |
| II-5.4 | II | `ACTIVE` | `SIG-P20` catalogue-typed migration 후 사용 |
| II-5.5 | II | `MIXED` | `P16 ACTIVE`, `P17 ACTIVE_CONDITIONAL`; atomize/component map |
| II-6.1 | II | `PROPOSED_REQUIRED` | PR-258 open-set classification signature/card를 증거 결속 후 등록 |
| II-6.2 | II | `DIAGNOSTIC_ONLY_REQUIRED` | PR-257 synthetic benchmark artifact; real-data/family claim 금지 |
| II-6.3 | II | `DIAGNOSTIC_ONLY_REQUIRED` | PR-256 benchmark artifact; discrimination candidate only |
| B-1 | Bridge | `PROPOSED_INVALID_DERIVATION` | degree-\(\le2\) 주장을 폐기하고 named-invariant factorization/fiber guard로 수정 |
| B-2 | Bridge | `ACTIVE_CONDITIONAL` | one-way/refutation semantic guard; theorem-count 증가 없음 |
| B-3 | Bridge | `ACTIVE_CONDITIONAL` | congruence/epoch channel-key guard; premise 없으면 saturation 금지 |
| B-4 | Bridge | `ORACLE_VERIFIED` | parity-to-test guard; exact-test 사용은 hypothesis-gated |

## Appendix B. frozen 65-ID legacy migration inventory

이 표는 current live successor-registry audit의 전수 inventory다.
`CHECKED`는 v2 signature completeness만 뜻하며 vector/tensor lift 또는
proof promotion이 아니다. A6이 disposition partition에서 누락한
`P3, P4, P5, P8, P12, P13, U1`도 모두 포함한다.

| ID | Pillar | Legacy status | v2 signature | title |
| --- | --- | --- | --- | --- |
| P1 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Signed comparator identity and Domain-checked semantics |
| P2 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Diagnostic variables Q, F, Pi, G_F, and P_post are distinct |
| P3 | T | `ACTIVE_CONDITIONAL` | `CHECKED` | Diagonal MES three-bound hierarchy |
| P4 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Frame-attribution safe-route correction |
| P5 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Conditional Bianchi V momentum-response formula |
| P6 | T | `ACTIVE` | `MIGRATION_PENDING` | Flat-FLRW first jet |
| P7 | T | `ACTIVE` | `MIGRATION_PENDING` | Non-collinear boost composition and first-jet separation |
| P8 | S | `ACTIVE` | `MIGRATION_PENDING` | Response rank and duplicated channels |
| P9 | T | `ACTIVE` | `MIGRATION_PENDING` | Radial-vorticity blindness |
| P10 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Single-shell degeneracy and broad-depth rank recovery |
| P11 | T | `ACTIVE` | `CHECKED` | PSD second-moment cone |
| P12 | T | `ACTIVE` | `MIGRATION_PENDING` | Scalar tilt trace is not sufficient |
| P13 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Shear memory of anisotropic stress |
| P14 | T | `ACTIVE` | `MIGRATION_PENDING` | Dust-FLRW oracle |
| P15 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Quadrupole filling under registered closure |
| P16 | S | `ACTIVE` | `MIGRATION_PENDING` | Single-sky sampling dispersion |
| P17 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Multi-ell Fisher floor and transfer-profile refinement |
| P18 | S | `ACTIVE` | `CHECKED` | Graded rank-2 comparator |
| P19 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Exceedance and e-value calibration |
| P20 | S | `ACTIVE` | `MIGRATION_PENDING` | Rao-Blackwell reachable-sector domination |
| P21 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Volterra depth-memory representation |
| P22 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Transverse reopening of the vorticity sector |
| P23 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Diagonal covariance compression loses morphology |
| P24 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Full-covariance MES tightening |
| P25 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Rank-failure no-result and morphology information gain |
| P26 | S | `SUPERSEDED` | `MIGRATION_PENDING` | Partial-identification interval for x_C (one-sided nonnegative cone) |
| P27 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | MES-rank route reconciliation |
| P28 | S | `ACTIVE` | `MIGRATION_PENDING` | Posterior prior-exposure under null directions |
| P29 | S | `ACTIVE` | `MIGRATION_PENDING` | Finite-cover e-value combination |
| P30 | S | `ACTIVE` | `MIGRATION_PENDING` | Parameter duplication versus observation duplication |
| P31 | S | `SUPERSEDED` | `MIGRATION_PENDING` | Identified-set sharpness over PSD and ceiling cones |
| P32 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Optical ansatz branch identifiability |
| P33 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Depth-gap delta-method propagation |
| P34 | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Vector-g response covariance propagation |
| P35 | S | `SUPERSEDED` | `MIGRATION_PENDING` | Two-stage identified-set coverage with Imbens-Manski endpoint correction |
| P36 | S | `RETRACTED` | `MIGRATION_PENDING` | Joint-feasible-set depth-gap interval propagation (“strict whenever”) |
| T1p | S | `ACTIVE` | `CHECKED` | Signed-box two-branch identified interval |
| DL1 | S | `ACTIVE` | `CHECKED` | Lower-gap monotonicity of the all-curvature branch |
| L-T2-EXIST | S | `ACTIVE` | `CHECKED` | Existence-level depth-gap strictness lemma |
| T2p | S | `RETRACTED` | `MIGRATION_PENDING` | Depth-gap strictness per-endpoint iff via coefficient signs |
| T2pp | S | `ACTIVE` | `MIGRATION_PENDING` | Signed-numerator domain repair of the fixed-pairing quotient interval |
| T3-lin | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Linearized realization of the identified-interval endpoints |
| T3-full | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Exact constraint-surface endpoint witnesses |
| T3-int | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Interior x_C-value family |
| T4p | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Estimated-covariance residual test is Hotelling T-squared/F |
| T5p | S | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Exact deterministic-width Imbens-Manski endpoint coverage |
| T8p | S | `ACTIVE` | `MIGRATION_PENDING` | Noncentral-chi-square power monotonicity |
| T9p | T | `ACTIVE` | `MIGRATION_PENDING` | Multi-component tilt composition |
| MES-PROV | T | `ACTIVE` | `CHECKED` | MES coefficient provenance |
| U1 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Beta-channel toy correspondence |
| U2 | T | `ACTIVE_CONDITIONAL` | `MIGRATION_PENDING` | Fingerprint envelope ceilings at eps1 |
| U3 | S | `ACTIVE` | `MIGRATION_PENDING` | Rank-2 response schema correspondence |
| U4 | S | `SUPERSEDED` | `MIGRATION_PENDING` | Teff fingerprint statistical closure |
| T2G | S | `ACTIVE` | `CHECKED` | General fractional-program interval theorem |
| TSUM | T | `ACTIVE` | `CHECKED` | Two-temperature fingerprint sum bound |
| U4-v9 | S | `ACTIVE` | `MIGRATION_PENDING` | Teff fingerprint statistical closure, v9 rerun |
| MES-BR | T | `ACTIVE` | `CHECKED` | MES coefficient branch registry |
| BV-DYN | T | `ACTIVE` | `MIGRATION_PENDING` | Tilted-LRS Bianchi V evolution seal |
| K5-CARD-v2 | S | `ACTIVE` | `MIGRATION_PENDING` | K5/CF4 identified-interval card v9 |
| KE-FRAME | T | `ACTIVE` | `MIGRATION_PENDING` | King-Ellis tilted-congruence frame kinematics and constraint algebra |
| KE-OBS | T | `ACTIVE` | `MIGRATION_PENDING` | Exact vorticity classification of group-invariant tilted congruences |
| KE-DYN | T | `ACTIVE` | `MIGRATION_PENDING` | Rotating perfect-fluid development and flat-curvature obstructions |
| OMK-REOPEN | T | `ACTIVE` | `MIGRATION_PENDING` | Higher-order anisotropic-curvature reopening transfer |
| MES-REFREEZE | T | `ACTIVE` | `CHECKED` | MES geodesic derivation and vorticity-anchor refreeze |
| MES-MESB-TRACE | T | `ACTIVE` | `CHECKED` | MESb source trace and non-geodesic-bound refutation |

전수 합계는 `65 = 31 T + 34 S`, v2 상태는
`12 CHECKED + 53 MIGRATION_PENDING`, 역사적 상태는
`4 SUPERSEDED + 2 RETRACTED`다. PR-259/267은 이 합계를
machine-readable test로 고정하되 frozen v1 registry의 byte를 수정하지
않는다.
