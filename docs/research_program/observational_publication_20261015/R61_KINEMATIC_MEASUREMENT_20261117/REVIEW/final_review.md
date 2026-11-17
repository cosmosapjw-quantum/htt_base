# R61 독립 최종 심사 — R9/C9

검토일: 2026-11-17. 검토자: 별도 native read-only reviewer. 요청 runtime은 부모 설정 상속이며, 실행 모델·effort의 관측 metadata는 **UNKNOWN**이다. 과학 코드·보고서의 작성에 참여하지 않았고 원격 저장소에 파일을 쓰거나 Git mutation을 수행하지 않았다.

## 판정

**PASS WITH MINOR REVISIONS — 조건부 측정 결과를 수용하되, 게시 전에 R61-F1의 calibration 가정을 교정한다.**

주요 수학, 실제 수치 범위, source/operator 연계, 11D/16D confidence cutoff, mixed-invariant witness 및 비교 해석에서 추가적인 중대 결함을 발견하지 않았다. 한 가지 필요한 교정은 일반적인 깊이 의존 calibration에 대한 문장의 가정 범위다. 아래 실제 source-level 반례에 의해 이 문장은 그대로 게시할 수 없다. 현재 보고된 수치 표에는 그 일반 calibration 예산이 적용되지 않았으므로, 이 finding은 기존 신뢰구간 숫자나 공통 calibration 소거 정리의 실패가 아니다.

R61-F1을 지정된 식으로 교정하고 영향을 받는 metadata·경로의 targeted closeout을 남기면, 이 연구 단위의 조건부 방법론·측정 응용 결과를 저장소에 게시할 수 있다. 다른 독립 심사나 전체 연구 루프의 재시작은 요구하지 않는다. 원고의 최종 투고 준비는 기존 RESEARCH_PLAN_KO.md의 P1–P3에서 분리해 관리하는 과학 작업이며 이번 코드 게시 판정과 동일하지 않다.

## 검토 대상과 identity

원격 장치: edd1b263-56a0-4391-8a2a-677dd00eabf5. 기존 checkout: /home/cosmosapjw/Dropbox/bianchi/htt_base. 관측 HEAD: fb6ae9f21585e194ef29dabc91d79a529e0ac57e. 관측 branch: research/r61-kinematic-measurement-20261117. R61 변경은 심사 시점에 미커밋 상태였다.

문서 경로의 공통 접두사는 docs/research_program/observational_publication_20261015/R61_KINEMATIC_MEASUREMENT_20261117이다. THEORY.md, REPORT_KO.md, RESEARCH_PLAN_KO.md, RESEARCH_RECORD.json 및 직접 연결된 owned-input 기록을 읽었다. 세 수학 모듈, 네 실제-data runner, 세 테스트 파일, R58 fit_linear와 R54/R58/R60 연결을 검사했다. 현행 AGENTS.md·HTT 지침·CURRENT_CODEX_RUNTIME.md를 적용했고 과거 CUH-G 및 4축 감사 체계를 재활성화하지 않았다.

| 대상 | 심사한 SHA-256 |
|---|---|
| R58 OWNED_TENSOR_CARRIERS.npz | 42f6bc5158fdf2f876720db12c44b088bc2db9734887e0d84ae098b234a7e64d |
| RESULTS/IMAGES/KINEMATIC_IMAGES.json | 2aa780b488378f85293077c59c10cd6c13cb05e92628a9c681b9fe8c3b896be8 |
| RESULTS/DEPTH/KINEMATIC_DEPTH.json | ec7dd00710bd6a38eb69b9e1798a657e715a4e6af04391483c5eb89c974bd72c |
| RESULTS/MIXED/R61_MIXED_INVARIANT_RESULT.json | 09389238702253d0cdec08933f0d2454afb68ea9e4d48b140b52254c581bdbab |
| RESULTS/BOX_COMPARISON/R61_BOX_COMPARISON_RESULT.json | 28d77071909b5fb605b781f786c45b9c0f3aae524a604f81a4e73aaf64454a13 |

심사 당시 결과 JSON의 실행 모듈·runner hash는 현재 파일들과 모두 일치했다. DEPTH에 기록된 raw dependency hash 불일치는 없었다. BATCH_EXECUTION.json의 24개 기본 테스트와 세 실제 실행, BOX_EXECUTION.json의 10개 추가 수학 테스트와 box 실행은 모두 exit code 0이며, 여섯 로그의 실제 hash가 receipt와 일치했다. 이는 과거 실행 근거의 검증이며, reviewer가 전체 34개 테스트를 다시 실행했다는 뜻은 아니다.

직접 검산 환경: 기존 .venv/bin/python, Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1. OPENBLAS_NUM_THREADS=1, OMP_NUM_THREADS=1, PYTHONDONTWRITEBYTECODE=1을 사용했다. 본 리뷰의 세부 수치와 코드 hash는 동반 r61_final_review.json에 보존한다.

## 필요한 교정: R61-F1

**심각도: 중간. 분류: 이론 가정/측정량 의미의 과도한 일반화.**

대상은 교정 전 THEORY.md 158행, REPORT_KO.md 137행, scripts/r61/run_r61_depth_measurement.py 115행의 depth_dependent_calibration metadata 및 그 문장을 담은 저장된 DEPTH 결과다. RESEARCH_PLAN_KO.md의 ρ_delta에 대한 후속 입력 계약도 같은 정의를 사용해야 한다.

현재 문장은 깊이 의존 calibration의 두 물리 endpoint 차이가 full-sky RMS ρ_delta 이하이면, fitted RMS contrast 구간을 ρ_delta만큼 넓히면 된다고 읽힌다. 임의의 source calibration b(z,n)에 대해 이 결론은 성립하지 않는다. 관측된 K1은 전체 source sample의 masked, covariance-weighted 회귀 계수이므로 두 endpoint에서의 calibration 값만으로 그 bias가 제한되지 않는다.

### 실제 입력에서의 최소 반례

Frobenius 정규직교 STF 기저의 첫 성분을 E0로 두고

\[
Q_{\rm cal}(z)
=0.01\,\frac{z-0.02}{0.05}\frac{z-0.08}{0.05}E_0,\qquad
\delta\eta_i=n_i^TQ_{\rm cal}(z_i)n_i
\]

를 사용했다. 이 매끄러운 calibration은 z=0.02와 z=0.08에서 각각 정확히 0이므로 두 물리 endpoint의 angular RMS 차이는 0이다.

기존 source n,z, R54 operator O_m, 저장된 X16 및 C를 그대로 읽고, Cholesky whitening 뒤 독립 QR 분해로 회귀 bias를 계산했다. R58 fit_linear나 R61의 최적화 함수는 이 계산에 사용하지 않았다. 실제로

\[
\delta\widehat{\alpha}_{16}
=(X_{16}^TC^{-1}X_{16})^{-1}X_{16}^TC^{-1}O_m\delta\eta,
\quad
\delta\widehat{\Delta K}=1.2\,S_{K_1}\delta\widehat{\alpha}_{16}
\]

의 RMS는 0이 아니었다.

| 모형 | \(\sqrt{2/15}\|\delta\widehat{\Delta K}\|_F\) |
|---|---:|
| log | 0.0013577954572978846 |
| log_mono | 0.0013502720710796372 |
| log_split | 0.001333502036971493 |
| log_survey | 0.0013489249154436194 |
| log_mono_radial | 0.0014134199001246876 |
| log_mono_galactic | 0.0009915764512313727 |
| log_mono_error | 0.0013574074148312327 |

이 반례는 일반 endpoint-only bound의 부족함을 보여 준다. 공통 calibration 소거 정리에는 모순되지 않는다.

### 최소 수정과 종료 조건

다음 두 경우를 구분하면 된다.

1. Calibration이 **실제 fitted angular subspace**에 속하는 경우: 공통 dipole \(d_0\cdot n\)과 \(Q_{\rm cal}(z)=Q_p+((z-z_p)/z_*)Q_1\)인 affine STF calibration이면 fitted contrast bias는 정확히 \(1.2Q_1\)이다. 이때 \(\sqrt{2/15}\|1.2Q_1\|_F\le\rho_\Delta\)인 몸체는 기존 RMS 구간을 \(\rho_\Delta\)만큼 넓히는 근거가 된다. 깊이에 따라 변하는 dipole은 현재 X16의 공통 dipole 열에 포함되지 않으므로 이 조건에 자동으로 들어가지 않는다.
2. 일반 source calibration의 경우: \(L_\Delta=1.2[0_{5\times11}\ I_5]\), \(T_\Delta=L_\Delta V_{16}X_{16}^TC^{-1}\)를 정의하고, 실제 induced bias에 \(\sqrt{2/15}\|T_\Delta\delta y\|_F\le\rho_\Delta\), \(\delta y=O_m\delta\eta\)라는 예산을 요구한다. 두 물리 endpoint 값만으로 이 예산을 대체하지 않는다.

기존 numerical depth 표에는 일반 \(\rho_\Delta\) 보정이 적용되지 않았다. 실제로 추가한 것은 알려진 R60 velocity-slope response에 대한 bias body다. 따라서 이 finding의 수정은 주요 수치 결론을 바꾸지 않는다. 부모 저자가 계획한 corrected DEPTH 출력의 targeted 재실행과 numerical payload 동일성 확인은 해당 교정의 종료 근거로 충분하다. 원본 DEPTH와 실행 receipt는 역사적 근거로 보존한다.

## 수학 및 구현에서 수용한 부분

### 동일 confidence event와 투영

THEORY.md §2–§5와 r61_kinematic_images.py / r61_mixed_invariant.py는 하나의 joint11 Gaussian ellipsoid를 사용한다. 선형 projection에는 principal covariance \(L V L^T\)를 사용하고 cutoff \(\chi^2_{11}(0.95)=19.67513757268249\)를 그대로 유지한다. 전체 precision의 단순 부분행렬로 잘못 치환하지 않는다. Scalar image 및 별도 marginal5의 의미가 구분돼 있다.

고정 Gaussian 법칙과 선언된 calibration 몸체 아래에서 함수상에 의한 동시 coverage 주장은 타당하다. 일곱 모형을 독립 likelihood처럼 곱하지 않고 union으로 다룬다. 각각의 scalar norm이 0을 포함하는 사실과 joint origin의 포함 여부를 구분한 보고서의 설명도 맞다.

### Quadratic trust region

r61_kinematic_images.py의 quadratic_ball_extreme은 \(B+\lambda I\succeq0\), stationarity, complementarity에 기반한 global trust-region 특성을 구현한다. Interior PSD, boundary secular equation 및 singular hard case가 분리돼 있고 feasible witness와 dual enclosure/gap을 함께 반환한다. Maximization의 부호 변환과 \(\beta\cdot a=-V\cdot d_H/c\)의 교차항 정규화도 맞다.

정규화 및 calibration factor \(\sqrt{15/2}\rho\), \(\sqrt3\rho\), directional support \(\sqrt8\rho\)를 직접 대조했다. 이는 각각 STF, dipole, combined angular RMS 몸체의 support와 일치한다. finite-calibration \(\beta\cdot a\)에 사용한 합성 upper bound는 문서에서 보수적인 outer enclosure로 설명한다.

### Mixed cubic reduction과 branch bounds

r61_mixed_invariant.py의 조건부 Schur complement는 beta–kappa cross-covariance를 유지한다. Fixed beta에서 kappa support를 제거한 식과 calibration support \(\sqrt5\rho|\beta|^2\)가 올바르다.

bound 메서드의 직접 cubic expansion과 Young 부등식에 의한 polynomial upper bound를 대조했다. Quadratic, cubic 및 quartic remainder의 계수와 부호가 맞으며, domain은 box와 unit ball의 교집합이다. Pruned node의 ceiling을 보존하므로 pruning tolerance를 이미 확정된 극값으로 잘못 쓰지 않는다. 최종 witness를 원래 tensor·calibration 형태로 재구성하고 gap을 계산한다.

저장된 28개 경우의 56개 witness를 원래 11D ellipsoid로 최소-Mahalanobis lift하여 별도로 검사했다. 최대 cutoff excess는 \(3.55\times10^{-14}\), projection 오차는 \(6.94\times10^{-18}\), 직접 phi 재구성 차이는 0이었다. Calibration 제곱 몸체의 최대 음수 slack은 \(3.39\times10^{-21}\)로 부동소수점 수준이었다. 기록된 최대 endpoint gap은 \(9.997373791918429\times10^{-11}\)이며 모든 실제 경우가 선언한 tolerance를 충족한다.

Float64 analytic enclosure는 directed-rounded interval proof로 승격되지 않는다. 대칭적인 stress case의 NODE_CAP도 실제 28개 자료 조건의 수렴과 구분돼 있다.

### 실제 coordinate box 비교

r61_box_comparison.py의 32개 kappa corner와 endpoint마다 27개 beta face를 열거하는 원리는 완전한 exact-arithmetic characterization을 제공한다. Fixed beta에서 kappa 의존성이 선형이고, 각 최적점은 최소 face의 상대내부에서 stationary라는 논거가 맞다. Singular stationary affine set의 feasibility를 LP로 처리하고, 수치적 rank ambiguity를 명시적으로 거부한다.

Actual-box/joint-width ratio와 legacy triangle-bound/actual-box ratio를 분리한 해석을 수용한다. 전체 joint domain을 coordinate box로 바꾸는 효과를 측정하며, covariance off-diagonal만의 기여나 full GLS에 대한 Fisher-information 이득으로 부르지 않는다. Numerical guard의 지위도 적절히 표시돼 있다.

## 실제 수치와 보고 내용의 대조

보고서의 주요 수치는 원 결과 JSON의 값과 표시 정밀도에서 모두 일치했다.

| 항목 | 독립 확인 값 |
|---|---:|
| λ=1, 0 mmag union Σ upper | 0.06254876346135956 |
| 같은 조건의 \(\|a\|\) upper | 0.10153818103285009 |
| 같은 조건의 \(\|\beta\|\) upper | 0.004205530562272829 |
| 같은 조건의 directional RMS upper | 0.060494503390557966 |
| \(\beta\cdot a\) union | [−3.8599227143877195e−5, 3.5735683455422957e−4] |
| \(\beta^Ts\beta\) union | [−6.281510541990794e−7, 5.044205982216458e−7] |
| Actual-box/joint 폭 비율, 28조건 | 4.3857657902090255–5.81407726799209 |
| Legacy triangle / actual-box 폭 비율 | 1.7500238794652834–2.0744367352337556 |
| Marginal5 union의 최소 Σ lower | 0.0006769293716914084 |
| 이에 대응하는 calibration threshold | 1.314748450056195 mmag |
| Joint apparent-response origin의 모형별 p 최대 | 0.015342738288599698 |
| STF slope nominal p 범위 | 0.5633190899534047–0.9432869179435147 |
| ΔK RMS joint16 union | [0, 0.16340399602136726] |
| Velocity-slope 1000 km/s 예산을 더한 upper | 0.16354400782395404 |
| Velocity-slope 3000 km/s 예산을 더한 upper | 0.16382403142912755 |
| Trace-optimal pivot | 0.054812751921037274–0.056384171231329605 |
| z=0 / optimal-pivot RMS 오차 비 | 2.6902703969139723–3.0055674528781333 |

저장된 X16, y, C에서 whitening 후 QR로 일곱 16D fit을 독립 재계산했다. Estimate의 최대 차이는 \(6.12\times10^{-15}\) standard deviation, covariance의 성분별 SD-normalized 최대 차이는 \(7.43\times10^{-15}\)였다. Slope Wald statistic, p, pivot 및 extrapolation ratio도 원 결과와 일치했다. Source/operator parity 기록의 최대 data 차이는 약 \(2.0\times10^{-15}\)이고 raw dependency identity도 일치한다.

공통 additive angular calibration에 대한 GLS affine-equivariance와 slope annihilation은 정확하다. 실제 injection의 최대 slope 변화 \(4.90\times10^{-17}\)와 부합한다. R60의 유한 velocity-slope 응답을 \(V_{16}X_{16}^TC^{-1}Z_{V1}\)로 전파한 bias map 및 spectral-norm enlargement도 올바르다.

Exact-log closure의 최대 성분 이동 0.0527058–0.1367532 SD, whitened remainder 0.0751988–0.2490160, 양수인 all-sky factor lower bound를 결과와 대조했다. 두 초기값과 inactive numerical bounds를 stationary-fit 진단으로 한정하고 global nonlinear optimum/coverage로 사용하지 않는 해석을 수용한다.

## 물리 주장과 논문화 범위

Metric \((-+++)\), \(U^aU_a=-c^2\), sourceward direction 및 c를 복원한 leading coefficient는 원전과 정합적이다. Heinesen의 luminosity-distance 계수에서 log-distance ratio를 취하면 \(z(\mathfrak Q-q_f)/2\)가 나오므로, 적절한 full-sky projection과 remainder control 아래의 Q2 연결도 맞다. K1이 proper-time shear derivative라는 결론은 내리지 않는다.

다음 원전을 직접 열어 핵심 식과 적용 조건을 확인했다.

- [Heinesen 2010.06534v2](https://arxiv.org/html/2010.06534v2), 식 (25)–(30): leading directional Hubble coefficient, \(D_L^{(1)},D_L^{(2)}\), light-ray spatial derivative가 포함되는 effective deceleration.
- [Maartens et al. 2312.09875v3](https://arxiv.org/html/2312.09875v3), observer dependence 및 §4.2: redshift의 변경만으로 luminosity-distance experiment의 boost 변환이 완성되지 않는다는 조건.
- [Heinesen–Korzyński 2406.06167v1](https://arxiv.org/html/2406.06167v1), §II–IV와 식 (9), (12): geodesic/coarse-grained/nearby 조건과 Fermi–Walker frame의 leading position drift \(P(\sigma+\omega)n\).

현재 32D experiment가 absolute H/Theta 및 vorticity를 측정했다고 하지 않는 점, 독립 calibration·finite-z transfer·survey coverage가 열려 있다는 점, fixed-C nominal inference와 physical detection을 분리한 점이 핵심 claim boundary다. 현재 결과에서 새로운 GR 정리, 일반적인 측정 불가능 정리, FLRW 배제, Bianchi family 식별 또는 full GLS보다 높은 Fisher 정보를 채택할 근거는 제시하지 않으며 보고서도 그렇게 주장하지 않는다.

R61-F1의 정확한 범위 교정 뒤에는 **기존 CF4 조건부 실험의 공동 비선형 confidence images, affine common-calibration에 불변인 finite-depth contrast, 응답 가정에 따른 측정 정밀도**라는 주장으로 수렴하는 것이 타당하다. Source-matched comparison과 독립 calibration/selection budget은 이미 계획된 논문 과제이며, 이번 범위에 새 과학 gate를 추가하지 않는다.

## 교정 종료 기록의 계약

본 문서는 교정 전 candidate에 대한 독립 판정이며 R61-F1은 여기에서 OPEN이다. 생산 저자는 원본 결과를 보존하면서 문장·metadata를 교정하고, 선택한 targeted 실행과 numerical payload 동일성 및 새 파일 identity를 별도 closeout에 기록한다. 이 하나의 교정이 닫히면 scoped review는 완료된다. 심사 결과가 기존 42개 과학 gate나 다른 unresolved transfer/coverage 상태를 자동으로 변경하지 않는다.
