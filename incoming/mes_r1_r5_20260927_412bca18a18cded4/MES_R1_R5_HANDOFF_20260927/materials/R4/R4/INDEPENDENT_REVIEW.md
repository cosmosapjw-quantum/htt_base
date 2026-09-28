# MES R4 독립 decision review

작성일: 2026-09-27 KST. Reviewer: `/root/independent_decision`.

**최종 판정: `PROMOTE_CONDITIONAL_THEORY`.** 하네스 Phase 8의 `PROMOTE`를 아래에 명시한 조건부 이론 결과와 다음 이론 단계에만 적용한다. 실제 자료로 MES 기준보다 좁은 구간을 얻는 empirical gate는 **`HOLD / UNRESOLVED`**다. 관측 percentage, 전체 운동학의 관측 식별, 일반 비선형 MES 정리, 생산 구현은 승격하지 않는다.

## 1. 독립성 및 검토한 고정 입력

이 reviewer는 후보 생성, 후보의 검증 설계 또는 Wolfram 실행 코드 작성에 참여하지 않았다. 별도 subagent context에서 원문과 실제 저장된 검산 출력 및 코드를 읽고 수리적 타당성을 판단했다. 최초 지적에 따른 같은 후보의 수정 확인은 이번 decision review 안에서 수행했으며, 리뷰의 리뷰를 추가하지 않았다. 모델 identity/ultra 설정을 독립 인증했다는 주장은 없다.

적용 지침은 `harness/PROJECT_INSTRUCTIONS.md`, `harness/docs/MODEL_ROUTING.md`, `harness/prompts/phases/08_external_decision_gate.md`다. 하네스의 초기 `state/RESEARCH_STATE.md`는 `NOT_RUN` 템플릿이며 연구 실행 증거로 사용하지 않았다.

최종 검토 대상의 SHA-256:

| 파일 | SHA-256 |
|---|---|
| `MES_R4_REPORT_KO.md` | `b982b05898696dcaa04d566e69fa97363b1c97e880d7f5307235afb7b7af76fb` |
| `closure_derivation.md` | `3812787cb1f749e3ba85159995be990858c71be72351154ca4f9866db07e86de` |
| `PREREGISTRATION.json` | `bac0400bc2403b13e477b46cef6e0c905f01ad5cb7694a7a82464c3edf0dfee8` |
| `verification/CAS_SHELL_AND_SCALE_raw.json` | `25d24ce6573d6792ac6fa9d71e9274074c3af9b08533add1c53dcb07d81c75e0` |
| `verification/CAS_ADAPTERS_SOURCE_raw.json` | `da4a133bb7cc3803ef04e7b7a98de4e3263caefedcf4efdee87a7e74bec9c7cb` |
| `verification/CAS_GEOMETRY_TILT_RAW_V2.json` | `f86405372d86f5d7fa8265e48dfcb6ddd974e2a4b53bd7ebe35b8fb82859b7f6` |
| `REPORT_CANDIDATE_V1_FROZEN.md` | `1b21e6097326c64a4237f4c04b42b699e1e22d65e36ad1553f95a51cb9740a04` |

추가로 위 CAS의 `.wl` 입력, geometry V1 실패 출력, `sources/OBSERVATIONAL_SOURCE_LEDGER.md`, `REVISION_LOG.md`, R3의 컨벤션·정규화·관측응답 관련 구간을 읽었다. 관측 문헌의 원문을 reviewer가 별도로 다시 취득한 것은 아니다. 문헌 수치는 source investigator의 원문 확인 기록에 근거하며, 본 독립 검토는 그 수치의 사용 범위와 이론·관측 계약의 정합성을 검토했다. 파일 hash는 identity 근거이며 과학적 타당성의 대체물이 아니다.

## 2. 핵심 수학 판정

### 공간균질 미분 closure — `PROMOTE`, derived + finite-fixture CAS checked

Koszul 식의 부호와 지표 순서는 정확하다. 미분 방향을 첫 index로 잡으면 metric compatibility와 torsion-free 조건이 함께 맞는다. 직교 frame의 invariant tensor 성분에 작용하는 공변 미분은 각 covariant index slot에 연결을 빼는 식이다. 본문의 연결행렬과 실행 코드의 covariant-slot 행렬이 transpose 관계임을 수정본에서 명시했다.

두 번째 미분에는 첫 미분의 covariant index에도 연결이 작용한다. 따라서 companion의

\[
(\bar D_a\bar D_bT)_I
=c^2\{R_aR_b+\gamma^d{}_{ab}R_d\}T_I
\]

가 맞다. 두 번째 항의 부호는 양수다. 단순히 동일 rank의 연산자 두 개만 곱한 식은 일반적으로 틀리며, 이 후보는 해당 항을 보존한다.

첫 미분의 norm은 slot별 operator norm과 삼각부등식으로, 두 번째 미분은 rank가 r+1이 된 tensor에 동일 결과를 적용하여 얻어진다. 따라서 \(crG\), \(c^2r(r+1)G^2\)의 coarse bound는 일반 증명으로 성립한다. STF 입력에서 새 derivative index까지 STF라고 간주하지 않은 점도 정확하다. 가장 큰 singular value가 고정 geometry에서 최적인 상수를 준다는 주장은 tensor Hilbert metric을 사용할 때 맞다.

실제 V2 CAS는 두 비가환 fixture에서 rank 1,2,3 전체 Cartesian tensor 공간을 검사했다. 첫 미분 행렬 크기는 각각 (9,3), (27,9), (81,27), 두 번째는 (27,3), (81,9), (243,27)이다. 재귀 계산과 닫힌 Hessian의 차는 모두 0이고, derivative-index slot 기여는 모두 비영이다. 두 차수의 coarse bound Gram 차는 모두 양의 준정부호로 확인됐다. 이 결과는 유한 fixture 검산이며 모든 Lie algebra를 전산 열거한 증거가 아니다. 일반성은 위 해석적 증명에 의존한다.

고정 구조상수에서 h→λ²h에 따른 연결의 λ⁻¹ scaling은 정확하다. Lie algebra만으로 dimensional bound가 정해지지 않는다는 결론도 맞다. 공간 slice의 법선 D에 관한 결과를 tilted D에 그대로 사용하지 않은 제한은 필수이며 보존돼 있다.

### 전체 운동학의 tilt jet adapter — `PROMOTE`, exact geometric identity / empirical input unresolved

\(F_{AB}=c(E_Au_B-\Gamma^C{}_{AB}u_C)\)와 projector를 이용한 Θ,A,σ,Ω의 분해는 정확하다. \(F_{AB}U^B=0\) 덕분에 projected tensor의 trace가 Θ와 같아진다. β의 값과 β의 time jet를 구분하며, β=0이나 βdot≠0이면 A=cβdot가 남는다는 극한은 옳다. 유한 tilt에서 radiation tensor의 projected spatial derivative에 normal time jet가 섞인다는 설명도 옳다.

V2 CAS는 특정 비영 β=(1/3,1/4,0), 임의 symbolic time jet, Minkowski connection에서 정규화·공간성·trace·분해를 확인했다. β=0의 비영 time-jet 극한과 비등방 normal K 극한도 확인했다. 일반 connection에 대한 모든 성분을 CAS로 검증한 것으로 확대하지 않는다. 일반식의 근거는 공변 미분의 정의와 projector 항등식이다.

이 adapter는 주어진 순간 jet를 운동학량으로 보내는 map이다. Einstein/matter compatibility, 입력 jet의 관측 가능성 또는 상한은 별개의 미완료 조건이다. β,b를 포함하는 전체 joint 입력이 compact라는 수정 조건하에서 compact image가 따른다. 단순 bounded/nonclosed domain이면 bounded image만 보장한다.

### 세 shell 보상식 — `PROMOTE`, derived + exact CAS checked

가중치 (-2,5,-2)는 상수항을 보존하고 1/r와 r을 제거한다. 표시된 Peano kernel은 구간별로 연속이며 비양수이고, 절대적분은 7D²다. 따라서 공통 Hilbert carrier에서 \(7MD^2\) bound가 성립하고 일정 방향의 상수 g''가 이를 포화하므로 해당 함수 class에서 7은 sharp하다. 독립 동일분산 noise의 variance factor 33, 동일 deterministic allowance의 factor 9도 정확하다.

세 출력 (k0,u,q)의 변환은 가역이며 원자료 또는 변환자료의 공동 likelihood 하나를 사용해야 한다. 동일 covariance를 함께 변환하고 고차 잔차의 공동 image를 남기므로 morphology와 coherent-motion carrier를 버리지 않는다. u를 제거한 k0만을 보관하면 β 관련 정보 일부가 사라진다는 점을 후보가 명시한다.

공통 u, 동일 angular response, 지정된 거리 coordinate와 smooth-part bound M은 실질적 가정이다. 서로 다른 source의 임의 고유속도는 자동으로 소거되지 않는다. 유한 shell window에서는 역거리와 거리의 실제 평균에 맞추어 가중치 및 kernel을 다시 계산해야 한다. 후보의 일반화된 moment/kernel 식은 맞으며 7을 자동 재사용하지 않은 점이 적절하다.

## 3. 원래 연구 동기 및 추론 계약

| 검토 항목 | 판정 |
|---|---|
| 부호·방향·morphology | full tensor carrier와 실제 operator image를 보존한다. scalar norm은 보고용 상한이며 유일한 결과로 대체하지 않는다. |
| 모든 운동학량과 β | 대상에서 제외하지 않는다. normal branch에서 A,ω가 0인 것을 일반 관측 제약으로 쓰지 않는다. |
| 동일 조건에서의 MES 정규화 | 분자·분모를 같은 joint state에서 평가한다. 자료 의존 분모를 임의 독립 수치로 고정하지 않는다. |
| Q,F,Π,G_F | 기존 정의의 서로 다른 의미를 유지한다. Q_outer의 부호 손실은 원 T 보존으로 보완하며 deterministic set만으로 Π 확률을 만들지 않는다. |
| redshift 비교 | 여러 shell은 동일 vertex의 k0를 추정한다. 다른 사건의 k(z) 및 G를 얻으려면 transport/response가 추가로 필요하다고 명시한다. |
| local boost/global tilt | coherent u, electron dipole, β field jet를 동일시하지 않는다. optical depth의 적분 제약을 pointwise opacity lower bound로 바꾸지 않는다. |
| novelty | 일반적인 Koszul/Peano 기법 자체를 새 정리로 선전하지 않는다. 연구 기여는 해당 추론 문제의 명시적 조건부 연산자·오차 계약이다. |
| tractability | 순간 대수계산과 국소 함수공간 bound로 범위를 닫는다. 광범위한 Boltzmann/evolution solver를 필요조건으로 추가하지 않는다. |

정확한 collisionless witness는 한 사건의 작은 sky amplitude가 spacetime derivative bound를 주지 않는다는 정보 한계를 뒷받침한다. 이를 자기일관적 Einstein–matter 우주의 반례나 MES 정리의 반례로 확대하지 않은 범위 제한은 정확하다.

관측 coefficient의 0.23–0.46 μas/yr와 선언된 MES benchmark를 다른 carrier의 규모 비교로만 사용한다. 실제 유의도·정확한 개선 배수·physical shear posterior로 변환하지 않는다. frame-spin 퇴화, cross-source covariance, source residual 및 거리 계약의 미확인을 숨기지 않는다. 따라서 empirical 목표를 달성하지 못했다는 본문의 명시는 충분히 분명하다.

## 4. 발견 사항과 처리

이번 reviewer가 요청한 수정은 다음과 같으며 최종 후보에서 모두 반영됐다.

1. Θ로 나누는 식에 Θ>0을 해당 위치에서 명시.
2. 연결행렬의 row/column과 covariant-slot transpose 대응을 통일·설명.
3. compact image 주장에 β와 time jet까지 포함하는 전체 joint compactness 명시.
4. companion의 분수 조판에 있던 form-feed 제거.
5. opacity 반례에 Δt를 복원하여 Γ의 역시간 단위를 명시.

이와 별도로 후보 생성 단계의 second-derivative 식에서 누락된 `+` 조판 오류는 owner/후보 유도자가 이미 바로잡고 기록했다. 해당 오류가 초기 display를 오해하게 할 수 있었다는 기록을 유지한다.

Geometry CAS V1의 singleton KroneckerProduct 및 행렬 stacking 문제는 **구현 실패**다. V1 출력의 False/미평가 표현을 이론 반례나 runtime 부재로 분류하지 않는다. V1 code/raw를 보존했고, 수정 V2의 정상 차원·정확 잔차·PSD 결과만 최종 검산에 채택했다. 검증 criterion이나 tolerance를 바꾸어 통과시킨 흔적은 확인되지 않았다. 최초 preregistration은 탐색 유도 후 CAS 전에 작성됐다고 정확히 제한하며 discovery 자체의 prospective prediction으로 주장하지 않는다.

## 5. 승격 범위와 종료 조건

현재의 조건부 이론 결과를 다음 R5의 **finite homogeneous tilted jet operator와 공동 허용집합 구성**에 사용할 수 있다. 본 검토 범위에서 남은 fatal issue는 발견되지 않았다. 필수 수정과 요청된 CAS evidence가 닫혔으므로 추가 reviewer 또는 동일 검산 반복은 요구하지 않는다.

아래는 완료로 바꾸지 않는다.

- 실제 nearby catalog 취득·fit 및 source/frame/distance 공동 likelihood 검증.
- 물리적 provenance를 가진 M, radiation time-jet, collision/source 및 고차 나머지의 수치 상한.
- 모든 운동학 성분의 절대 관측 식별, 특히 frame-free ω와 pointwise/global β.
- 실제로 MES/reference radius보다 좁은 robust 관측 구간과 observed deviation percentage.
- 일반 비선형 MES 확장 정리 또는 Einstein–matter 일관성이 검증된 전 우주론 모델.

따라서 반환 문구는 “R4 조건부 이론 단계 완료, empirical constraint 목표 미완료”가 정확하다. 다음 단계는 본문에서 지정한 jet/image 구성으로 진행할 수 있으며, 실관측 percentage 게시에는 위 empirical gate를 별도로 통과해야 한다.
