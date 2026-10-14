# 다음 추가분석으로 얻을 수 있는 결과

CF4 두 law 교차 생성·적합, Gaia disk·joint geometry, Union assumed-prior sensitivity·public source 조사, 유한 observation bounds 계산은 완료했다. 다음 목록은 그 결과 이후의 연구이며 publication novelty는 provisional, 제출 상태는 **NOT_READY_TO_SUBMIT**이다. 기존 F01–F06 의미를 유지하고 F07–F09를 추가한다.

| ID | 추가 결과 | solver 없이 가능한 부분 | 실제 추가 입력 / 검증 기준 |
|---|---|---|---|
| F01 | CF4 empirical selection·shared calibration 비교 | 완료된 cross-law32catalogue/64fit을 재사용한 precision-target population/calibration family 확대, same-draw LOO | 실제 survey selection·method/group overlap·source-motion·shared zero point. law당16개 전부 accepted인 conditional experiment는 실제 survey coverage가 아님 |
| F02 | Gaia correlation-aware robust frontier | 완료된4756-source disk·동시6D ellipsoid 위에 sky positions와 PSD angular covariance family 적용 | correlation amplitude/scale의 empirical source 또는 independent cohort, outcome-selection law. 가정 grid는 측정된 covariance가 아님 |
| F03 | Planck/CLASS matched physical split-null | 원제품 header·beam/pixel·U sign·filter 대응, injection transfer와 null adequacy stress; 완료된 assumed score-budget ranks 재사용 | raw-vs005a 생성 convention과 joint split/systematic simulations, exchangeability. 같은 sky를 독립 증거로 중복하지 않음 |
| F04 | 실제 local boost/global history 분리 | 완료된 nuisance contrast·response/covariance error 충분조건, detector selection response | 공통 congruence/frame의 distinct physical history/source-motion response. 외부 analytic/transfer 입력 수용 가능; 이 repo ODE/native solver 구축 금지 |
| F05 | 실제 finite-distance remainder/MES interval | supplied bounds의 algebraic propagation과 source-contract 검산 | 실제 ray/source normalization, domain·units·curvature/derivative envelopes, positive denominator/ceiling. unknown을0으로 채우지 않음 |
| F06 | Bianchi family/morphology 경쟁 | 현재는 외부 atlas specification 검토만 가능 | qualified external native all-mT/E/B atlas와 masks/null covariance/family-equivalence admission. 이번 실행 범위 밖이며 native solver/ODE 구축 금지 |
| F07 | Union3 exact source-bound joint inference | 완료된 λ={0,.5,1} assumed-prior sensitivity와 public Stan/paper discrepancy 조사 재사용, released-chain comparison | exact frozen FITS generating prior/center/parameterization/run-code binding. 논문 설명과 public Stan{2,6} branch의 차이는 미해결 source binding이며 certified prior correction이 아님 |
| F08 | ACT raw-QE validation | 공개 release source audit·adapter, 기존 reconstructed products 비교 | raw splits/filter/noise/response/mean field/disconnected bias·simulation IDs. 파생 kappa를 raw QE로 부르지 않음 |
| F09 | JWST/SDSS/COSMOS/KiDS 응용 결과 | 구체 estimand의 shared-calibration/selection comparisons, source overlap graph | admissible per-SN/host photometry·method calibration·selection law. row-count·retention은 completeness가 아님 |

## 완료 결과와 남은 질문

- **CF4:** `results/cf4_crosslaw/result.json`은 law당16개, 새32conditional catalogues·64fit 전부 accepted다. PRE 생성에서 POST−PRE H=2.09633403(MCSE.01670186), POST 생성에서2.04813049(MCSE.02026723). matched PRE bias−.237853/RMSE2.400705 vs wrong POST1.858481/3.077939; matched POST.009982/2.989571 vs wrong PRE−2.038148/3.553717. H는 endpoint km/s/Mpc이다. 기존 injection32개와 별도 pool이며 pooled coverage를 만들지 않는다. 다음 질문은 실제 selection과 family generality다.
- **Gaia:** `results/gaia_geometry/result.json`의 physical tangent disk support와 joint geometry는 완료했다.4756 tangent rotations,20000 fixed-law MC는 수치·조건부 법칙 검산이며 empirical Gaia coverage가 아니다. 다음은 angular PSD covariance와 outcome selection이다.
- **Union:** `results/union_prior/result.json`의 λ1 mean shifts/baseline SD는 Ωm+.0613042,H0rd−.0222749,M−.2742355이고 joint-grid TV=.02435595다. actual public code/논문 조사는 완료했다. source binding은 미해결이며 prior removal/no-removal 어느 쪽도 인증하지 않는다. 일반 부모 code audit을 기다리는 상태가 아니다.
- **Observation bounds:** `results/observation_bounds/result.json`의 assumed rank-error budget와 finite selected-fold normalizer response는 완료했다. actual physical score errors·selection law·distinct response는 다음 입력이다.

## 원고 우선순위

1. **선택 관측법칙·operator 방법론 원고:** 완료된 M01/R08과 M03/R09를 하나의 질문으로 묶을지 별도 application 원고로 나눌지 선행 연구와 비교한다. 표준 수식에 새 이름을 붙이는 것으로 novelty를 주장하지 않는다.
2. **CMB 처리·null 재평가 원고:** SMICA와 CLASS를 독립 anomaly 증거로 합산하지 않는다. matched processing/source bridge와 실패 원인 attribution이 핵심 연구다.
3. **거리 압축 product 재현·민감도 note:** 측정된 Union sensitivity는 조건부 결과로 보고할 수 있다. physical likelihood remapping 주장은 exact source binding을 해결한 뒤 판단한다.

공통 제출 기준은 estimand와 실제 기여, primary literature와의 차이, source-qualified data law, 수치오차와 통계오차의 분리, robustness/comparison baseline, 재현 코드·plot·table와 독립 검토다. 완료된 유한 계산과 test PASS가 publication novelty나 실제 physical inference를 자동으로 입증하지 않는다. **NOT_READY_TO_SUBMIT**와 기존 과학 HOLD는 유지한다.
