# R61 연구계획 — 하나의 운동학 측정 논문으로 수렴

## 목표와 현재 판정

작업 제목은 **Joint kinematic constraints and depth contrasts in Cosmicflows-4**다. 목표는 실제 거리–적색편이 자료가 허용하는 공동 normalized kinematics와 유한 깊이 변화의 범위를 측정하고, local kinematics로 해석할 때 추가되는 오차를 정량화하는 것이다. 기본 주장은 conditional inference이며, FLRW 위반·global tilt·Bianchi 분류·네 운동학 sector의 완전 복원은 이 논문의 acceptance에 넣지 않는다.

R61에서 joint11 nonlinear images, actual source의 rank16 STF depth response, common angular-calibration cancellation, exact-log response sensitivity를 실제로 실행했다. 새 STF slope의 nominal p값은 0.563–0.943이고, zero-redshift extrapolation의 RMS 오차는 covariance-optimal pivot보다 2.69–3.01배 크다. 이 결과는 null outcome도 포함하는 명확한 측정 논문 구조를 제공한다. 다만 실제 survey coverage·독립 calibration budget·finite-z physical interpretation이 확보되었다고 말할 수는 없다. 숫자는 [REPORT_KO.md](REPORT_KO.md)와 그 generated JSON을 기준으로 한다.

## 1. 이미 실행한 단일 연구 단위

| 산출물 | 현재 상태 | 재사용 또는 새 계산 |
|---|---|---|
| 35,970 CF4 groups, 32D retained carrier, 7 operators | 입력 identity 검증 후 재사용 | R54/R58 |
| full covariance와 physical pullback | 재사용, apparent/local 구분 유지 | R58/R60 |
| Σ, a 크기, β 크기, directional RMS, β·a | actual joint11 image 및 finite calibration 계산 | R61 |
| βᵀsβ | 실제 28조건 global numerical enclosure와 witness | R61 |
| 공동 타원체와 coordinate box 비교 | 동일한 confidence event에서 비교 | R61 |
| Kp, K1, ΔK와 전체 cross-depth covariance | 실제 source/operator를 이용한 fit16 | R61 |
| common angular calibration cancellation | 유도 및 source-level response injection 검산 | R61 |
| bounded omitted velocity slope | 기존 R60 응답으로 새 depth contrast의 bias 계산 | R60/R61 |
| local extrapolation와 exact-log response | 실제 covariance pivot, uncertainty inflation, nonlinear fit | R61 |
| H/omega 및 Gaia physical-transfer 부족분 | 기존 실제 입력 감사 재사용, 무리한 물리 변환 배제 | 기존 연구/R61 |

이 결과를 다른 이름의 audit나 mock-only demonstration으로 반복하지 않는다. 필요한 수학·수치 검산과 한 번의 독립 심사를 거친 뒤 이번 10단계를 종료한다. 저장소의 원래 42개 과학 gate는 scoped 결과 때문에 자동으로 완료 처리하지 않는다.

## 2. 논문 주장 세 개와 허용 범위

**Claim A: 공동 상태에서 직접 운동학 함수의 범위를 계산할 수 있다.** 동일한 full-covariance confidence domain에서 norms, mixed scalar, 방향별 expansion support를 산출한다. β·a의 정확한 quadratic extrema와 βᵀsβ의 enclosing/feasible endpoint를 구분한다. 유한 calibration의 β·a 구간은 보수적 outer bound다. ordinary full GLS와 정보량이 같다는 사실을 명시하고, 성분별 축약과만 같은 input/cutoff에서 geometry를 비교한다.

**Claim B: 정해진 깊이 차이는 공통 각도 calibration에 불변이다.** K1과 ΔK에 대한 affine cancellation을 증명하고 실제 source operator에서 검산한다. 깊이에 따라 변하는 calibration과 flow를 별도 sensitivity로 표시한다. 이 표현을 임의 calibration이나 selection에 대한 불변성으로 확대하지 않는다.

**Claim C: 현재 자료에서 관측 깊이와 local limit는 서로 다른 정밀도를 가진다.** covariance-optimal pivot, $z=0$ extrapolation cost, response linearization의 실제 영향을 제시한다. K1을 시간미분으로 부르지 않는다. 거리 cosmography의 effective deceleration과 omitted angular modes가 무엇을 오염시킬 수 있는지 식으로 명시한다.

## 3. 투고 전 남겨 둔 최소 과학 작업

### P1. 유한 깊이 응답을 물리 cosmography와 연결

입력은 이미 owned source의 z, n, 거리 지표와 동일한 operator다. 추가로 선택해야 할 것은 **한 가지** 물리적으로 정의된 low-z cosmographic family 또는 명시적 coarse-grained spacetime/flow family다. 표준 전개

$$
D_L={cz\over\mathfrak H_o(n)}[1+\tfrac12(1-\mathfrak Q_o(n))z+O(z^2)]
$$

에서 log-distance 응답으로 이동하고, observer boost와 distance correction을 함께 적용한다. 실제 mask에서 omitted angular multipoles와 higher-order z terms가 retained32D에 어떻게 투영되는지 계산한다. 새 basis를 무한히 늘리지 말고, 기존 Kp/K1에 대한 bias map과 remainder bound를 산출한다.

**완료 조건:** δy에 대한 ||C⁻¹/²δy||와 $b^TV^{-1}b\le\|C^{-1/2}\delta y\|^2$를 이용하여, 보고하는 domain에서 physical interpretation 오차가 허용되는지 판정한다. 논문이 요구하는 joint-error budget을 사전에 선택한다. 예를 들어 0.25 information-metric standard units를 목표로 택할 수 있지만 이는 물리 상수가 아니라 연구의 error-allocation 선택이다. 실패하면 해당 항을 모형에 포함하거나, 결과의 명칭을 finite-depth apparent kinematics로 유지한다.

**현재 가능한 부분:** leading와 second-order log-distance 연결, bias inequality, fitted-state exact-log 진단은 이번에 완료했다. 일반 congruence에서 confidence domain 전체의 uniform remainder는 확보하지 않았다.

### P2. angular/depth calibration을 독립 자료로 제한

필요 입력은 하늘 위치·distance indicator·관측 깊이에 따라 기록된 calibration/zero-point 정보 또는 서로 겹치는 독립 distance tracers다. 실제 우주 신호와 같은 CF4 residual만으로 calibration prior를 만든 뒤 그 prior로 신호를 검증하는 순환을 피한다.

공통 calibration ξ0와 depth-dependent calibration을 구분한다. 일반 b(z,n)에 대해서는 endpoint 차이만 제한하지 않고, 새로 공개한 $B_\Delta$에 전달된 $\sqrt{2/15}\lVert B_\Delta O b\rVert$를 제한해야 한다. 같은 affine-z STF subspace에 속하는 calibration에서만 물리 endpoint 차이가 이 estimator contrast와 일치한다. 깊이에 무관한 공통 angular calibration은 K1 contrast에서 소거되지만, 깊이에 따라 변하는 calibration은 남는다. source indicator 구성이나 survey footprint가 z에 따라 바뀌는 경우도 후자의 response로 넣는다. 실제 보정오차가 deterministic bound인지 stochastic likelihood인지 정하고, 그에 맞게 joint set 또는 likelihood를 재구성한다.

**완료 조건:** empirical/externally supported ρ 및 ρ_delta와 그 support를 제시하고, 현재 결과표를 그 입력으로 한 번 다시 산출한다. 5D shear origin의 R60/R61 취약점인 약 1.315 mmag를 비교 기준으로 보되, 이를 실제 calibration precision으로 오해하지 않는다. calibration 근거가 없으면 고정 ρ별 sensitivity table을 본문에 남기고 physical detection claim을 닫는다.

**현재 가능한 부분:** 실제 0/1/5/10 mmag 계산과 calibration invariance는 완료했다. 독립적인 catalog calibration measurement를 새로 얻은 것은 아니다.

### P3. matched-source 비교와 실제 survey uncertainty

가장 가까운 경쟁 분석은 latent distances, calibration, flow를 공동으로 다루는 [Stiskalek et al.](https://arxiv.org/html/2509.14997v2)이다. 그 논문의 CF4 W1 TFR 및 SNe sample과 현재 35,970-group carrier는 같은 실험이 아니다. 따라서 nominal p값이나 parameter-error 크기만 대조하는 benchmark를 만들지 않는다.

한 가지 공통 sample을 정하고 같은 source cuts, zero-point convention, velocity kernel, nuisance, selection, covariance를 사용한다. 먼저 full GLS와 tensor coordinates가 같은 likelihood를 재현함을 기준선으로 삼고, 그 다음 scalar/coordinate-box 축약이 mixed functional과 depth contrast에서 잃는 정보를 측정한다. 실제 survey law를 다루려면 distance-indicator errors, grouping, selection, velocity correlations를 보존하는 source-matched simulations 또는 정당화된 empirical procedure가 필요하다.

**완료 조건:** 동일 관측 질문에 대해 interval coverage, systematic bias, nuisance sensitivity를 비교한다. 기존 Gaussian injection의 조건부 coverage와 survey coverage를 별도 표로 쓴다. calibrated physical limit가 남으면 이를 논문의 중심 결과로 승격하고, 그렇지 않으면 calibration-limited measurement/methods paper의 범위로 제출 여부를 판단한다.

**현재 가능한 부분:** retained32D fixed-law에서 exact GLS와의 동등성, 전역 함수범위, coordinate-box 비교는 완료했다. raw-source likelihood의 충분성 및 release-matched survey coverage는 입증하지 않았다.

### P4. 단일 원고로 통합하고 종료

P1–P3의 결과를 받아 아래 원고에 한 번 통합한다. 새 theory brand나 무제한 nuisance catalogue를 만드는 방향으로 확장하지 않는다. 최종 판정은 “허용된 물리 조합의 제약”, “조건부 관측 방법의 응용”, “현재 독립논문으로 부족” 가운데 근거에 맞춰 내린다. 유의한 비영 결과를 만들기 위해 model family를 사후 축소하지 않는다.

기존 원래 P6의 H/omega 전체 실험이나 여러 probe를 합친 inverse problem은 별도 확장이다. 이 단일 논문의 필수 목표로 새롭게 묶지 않는다. 원래 DAG acceptance는 그대로 보존한다.

## 4. 원고 구성과 실제 그림

1. **Measurement question and owned experiment.** 실제 groups, operators, frame, 동일 sample의 model union.
2. **Kinematics and physical response.** Hdir와 finite-depth log response, rank/null directions, calibration degeneracy.
3. **One joint confidence domain.** 11D/16D cutoff, deterministic calibration body, stochastic covariance 조건.
4. **Nonlinear physical images.** norms, mixed contractions, global numerical bounds, 실제 coordinate-box 비교.
5. **Depth contrasts.** calibration cancellation, actual K1/ΔK fit, cross-depth covariance, null result와 상한.
6. **Response and error budget.** pivot, local extrapolation, finite velocity slope, log closure, source-level remainder.
7. **Matched comparison and interpretation.** 기존 GLS/cosmography/flow 분석과 역할 비교; 실제 없는 정보는 없는 것으로 표시.
8. **Conclusion and data release.** 재현 가능한 source identity, scripts, endpoints, hypotheses와 남은 관측 조건.

현재 그림은 joint norm intervals, mixed contraction intervals, direction-dependent support map, depth curve와 extrapolation cost다. `RESULTS/FIGURES/KINEMATIC_CONSTRAINTS_FINAL.png`는 범례를 분리한 본문용 norm 그림이고, PDF도 함께 제공한다. 수치 그림에는 생성 결과와 renderer의 identity를 남긴다. 모형별 곡선은 독립 표본이나 physical history의 확정 복원으로 설명하지 않는다.

## 5. 최소 추가 관측이 어떤 sector를 여는가

| 더 강한 목표 | 필요한 관측과 response | 현재 상태 |
|---|---|---|
| absolute H, Theta | 제거하지 않은 monopole, 독립 absolute distance scale, 동일한 source/velocity nuisance | 현재32D에서 미식별 |
| physical shear/acceleration | source-matched distance calibration과 finite-z/congruence response | 현재 조건부 normalized images |
| vorticity | nearby tangential proper motion, nonrotating frame/spin calibration, source-depth transfer와 full covariance | 현재 거리 실험에서 미측정 |
| 고적색편이 Gaia의 local 해석 | redshift distribution, selection, line-of-sight/history response, catalog frame solution | 기존 입력으로 직접 변환하지 않음 |

이 표는 일반적인 불가능성 주장이 아니다. 어떤 새로운 관측이 likelihood kernel을 줄일 수 있는지를 지정한 것이다. 실제 입력 없이 nuisance를 0으로 고정하여 측정 완료로 바꾸지 않는다.

## 6. 실행성과 종료

새 이론은 [THEORY.md](THEORY.md), 실제 결과는 [REPORT_KO.md](REPORT_KO.md), 실행 명령과 exit code는 [BATCH_EXECUTION.json](RESULTS/BATCH_EXECUTION.json)에 있다. `scripts/r61/run_r61_study.py`가 검증 후 세 실제-data runner를 순차 실행한다. 별도 box comparison은 이미 계산한 mixed endpoints를 재사용한다. 결과 디렉터리의 덮어쓰기를 거부하므로 재현 실행은 새로운 output 디렉터리를 사용한다.

이번 사용자 지정 10단계가 끝나면 멈춘다. local coding-agent 재개 프롬프트, 자동 실행 일정, 자동 후속 audit는 생성하지 않는다. 다음 연구를 재개할 때 필요한 것은 같은 감사를 반복하는 명령이 아니라 P1–P3의 구체적인 물리·관측 입력이다.
