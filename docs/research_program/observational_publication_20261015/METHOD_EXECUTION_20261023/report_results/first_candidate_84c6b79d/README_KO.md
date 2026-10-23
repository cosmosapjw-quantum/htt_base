# R24 solver-free 연구: 실행 결과와 남은 과학 입력

Owner: HTT/obsstat. 기준일: 2026-10-23. 범위: **C0 조건부 관측·방법 진단**, transfer_source: `none`. 이 보고서는 고정된 실제 결과를 종합하며 새 모델, solver, ODE, 표본 또는 과학적 수용 결정을 만들지 않는다. 시작 source HEAD는 `dfaf171c37f2636c942a99bf2b9803b57295ac14`, publication base HEAD는 `2c869f634e6673703f9434785fab3c4cfab76218`이다. 최종 commit은 host의 검토·push receipt로 확정한다. 보고서 생성 시점에는 검토된 미커밋 후보가 포함되어 있었다. 최종 publication identity는 host receipt와 PR commit에서 확인한다.

**13개 bounded conditional 연구 노드는 실제 dispatch·ack·raw receipt·controller record·독립 검토를 거쳐 completed다.** 이는 원래 external acceptance **17/42**, analytic alternate **18/42**를 바꾸지 않는다. [고정 checkpoint](SCIENCE_EXECUTION_CHECKPOINT.json)는 이전 48개 task object, 기존 packet, campaign identity와 ultra state의 보존을 확인한다. R9/UNKNOWN과 기존 HOLD는 그대로다. 13개 연구 history의 raw receipt 36개가 확인되었고 추가 ultra launch는 0이다. 이 단위의 완료는 전체 42개 과학 목표의 완료도, 앞으로 가능한 모든 방법의 소진도 아니다.

## 실제 실행과 독립 검토

표의 수치는 각 생성 결과에 직접 연결된다. 상세한 current candidate identity, input identity, 최종 review와 law는 [기계 판독 요약](report_results/RESULT_SUMMARY.json)에 있다. 일부 개별 author REPORT에는 작성 당시의 review pending 문구가 남아 있다. 이 종합 보고서는 이후 최종 독립 review와 checkpoint를 기준으로 현재 상태를 표시한다. 어느 scoped PASS도 물리적 수용으로 읽지 않는다.

| 실제 task | 소비한 결과와 해석 | 최종 review의 focused 검사 | 생성 그림 |
|---|---|---:|---|
| `R24-DISTANCE-MODELS` | [거리 모델: 공분산 가정에 따라 A/B 예측 순위 반전](distance/RESULT.json) | 3 | [그림](distance/DISTANCE_MODELS.png) |
| `R24-CMB-ORBIT` | [CMB full STF/orbit: 동일 scalar power에서도 phase/orbit 구별](cmb/RESULT.json) | 18 | [그림](cmb/PROCESSING_SUPPORT.png) |
| `R24-K03-DESIGN` | [K03 설계: epsilon=.3 최적 power 0.050074856412](k03_design/RESULT.json) | 2 | [그림](k03_design/POWER_SENSITIVITY.png) |
| `R24-SN-RELEASE` | [SN 공개 release: 277행 total covariance 1회 사용 조건부 적합](sn_release/RESULT.json) | 3 | [그림](sn_release/RELEASE_CONTRAST.png) |
| `R24-SELECTION-ENVELOPE` | [선택 envelope: Gamma=1에서도 628-frame 폭 최소 354/628](selection_envelope/RESULT.json) | 3 | [그림](selection_envelope/SELECTION_ENVELOPE.png) |
| `R24-OPTICAL-SHEAR` | [optical STF: 8개 projected ellipsoid 모두 zero 포함](optical_shear/RESULT.json) | 3 | [그림](optical_shear/OPTICAL_SHEAR.png) |
| `R24-BOOST-ACCELERATION` | [boost/acceleration: 선형 calibration 퇴화, depth 공간과 거의 중첩](boost_acceleration/RESULT.json) | 5 | [그림](boost_acceleration/RESPONSE_GEOMETRY.png) |
| `R24-K03-DEPTH-MOMENTS` | [K03 reported-z slope: 755850행 1회 통과, 정보 보존 1.584853%](k03_depth_moments/RESULT.json) | 상세 receipt | [그림](k03_depth_moments/POWER.png) |
| `R24-CMB-ENVELOPE` | [CMB 오염 envelope: 공통 성분은 split difference로 제한 불가](cmb_envelope/RESULT.json) | 5 | [그림](cmb_envelope/ENVELOPE.png) |
| `R24-TENSOR-BUNDLE` | [full tensor bundle: full24와 동일 4096 replicate law 보존](tensor_bundle/RESULT.json) | 5 | [그림](tensor_bundle/TENSOR_DIAGNOSTICS.png) |
| `R24-OPTICAL-NONLINEAR-QUOTIENT` | [비선형 optical quotient: linear/quadratic 소거 후 cubic shape와 overlap](nonlinear_optical/RESULT.json) | 6 | [그림](nonlinear_optical/OPTICAL_QUOTIENT.png) |
| `R24-DEPTH-IMAGES` | [보정 depth 함수상: Y18 slope 포함 수정; 35/72 norm Pi 변경](depth_images/RESULT.json) | 7 | [그림](depth_images/NORM_IMAGES.png) |
| `R24-CMB-CHIRALITY` | [CMB parity 보조량: 60개 finite carrier chi 비영; 15양/45음](cmb_chirality/RESULT.json) | 3 | [그림](cmb_chirality/PROCESSING_SENSITIVITY.png) |

Controller correctness의 초기 review 54개 검사 뒤에 followup ack 보완의 최종 검사는 **49 controller + 11 builder = 60개**, 독립 검토의 subtest는 43개다. [최종 controller 검토](FOLLOWUP_ACK_REVIEW_FINAL.json)의 범위는 실행 제어의 정확성이다. 과학적 검정력이나 수용 성공률이 아니다. 이 보고 작업에서는 과학 분석이나 pytest를 재실행하지 않았고, 출처 hash·크기, 링크와 표기 수치의 정합성만 확인했다.

## 결과가 보여 주는 구별과 한계

**거리와 선택.** [동일 274행 비교](distance/REPORT.md)는 628개 선택 표식 중 공개 DMbest가 있는 274행과 354개 미정의를 그대로 보존한다. 세 모델, 네 공분산, 60개 whole-group held-out 적합에서 group 항이 없으면 B optical STF가 A calibration/flow보다 앞서고, group scale .29 mag에서는 A가 근소하게 앞선다. 예를 들어 `(a,b)=(0,0)` 점수는 A −220.320, B −196.843이고 `(0,.29)`는 A −194.273, B −195.138이다. normalized Gaussian working law의 training ML plug-in scale을 썼으므로 계수·scale 불확실성을 포함한 predictive coverage가 아니다. PGC9031은 317 km/s로 유지되며 C union의 flow fraction 2.261954–2.445192가 작은 속도 근사의 적용영역을 위반한다. 불리한 행을 사후 삭제하지 않았다.

[선택 envelope](selection_envelope/REPORT.md)는 동일 OOF residual에 엄격한 `abs(residual)>t`를 적용한다. 274행의 uniform empirical reference와 density ratio Gamma 가정에서 sharp event endpoint를 계산했다. 미정의 354행 때문에 Gamma=1조차 628-frame 폭이 최소 `354/628=0.563694`이고, t=.5 mag, Gamma=2에서는 0.7333–0.7548이다. 이는 알려진 628-frame의 availability 분석이며 5,460 parent의 propensity나 물리 confidence가 아니다. unrestricted missing completion의 signed mean은 임의로 커질 수 있다. 97개 LP/D07 endpoint crossing과 기존 물리 unknown mass 1도 지워지지 않는다.

**CMB는 전체 형태를 쓰되 동일 하늘의 processing으로 해석한다.** [보정 orbit 결과](cmb/REPORT.md)는 scalar power만으로 사라지는 phase 정보를 full rank-2/rank-3 STF Q/O로 유지한다. scalar-equal control은 C2/C3를 상대 2.22e−16까지 유지하면서 orbit lower 2.624e−5를 보인다. 15개 primary와 45개 pilot carrier는 독립 하늘 60개가 아니다. primary L32 split/full lower는 0.01265095–0.01801714이며 고정 저장 tensor에 대한 경계다. foreground나 processing의 물리 오차를 포함하지 않는다.

[오염 envelope](cmb_envelope/REPORT.md)에서 모든 split을 `g+f_common+f_s+n_s`로 쓰면 g에 h를 더하고 common foreground에서 h를 빼도 관측값은 같다. split difference만으로 common 성분을 유한하게 제한하지 못한다. cross-split noise의 `tr(N12)`도 UNKNOWN이며 centered 공통 부호 noise 반례에서는 5다. pairwise radius envelope는 각 scenario의 보수적 외곽이며 cross-operator 공동 물리 region이 아니다. L32 네 split lower는 rho=.10에서 양수지만 .25에서 모두 0이다. 이는 lower certificate의 소실이지 실제 orbit 거리가 0이라는 증거가 아니다.

[추가 parity 진단](cmb_chirality/REPORT.md)은 저장 binary64 carrier를 exact rational로 해석한다. 60개 모두 chi가 비영이고 15개 양수, 45개 음수다. 같은 processing split/full에서 부호가 다른 비교는 18/48, primary/pilot zero-window는 0/15, window 변경은 3/30이다. rho `0,1e−6,1e−5,1e−4,1e−3,.05`의 보수적 sign certificate 통과 수는 `60,60,39,0,0,0`이다. 실패는 inconclusive이며 sign reversal이 아니다. proper-rotation mirror 구별은 이 유한 carrier의 결정론적 성질이다. matched total-field law, cross-operator covariance와 물리 오염 제약이 없으므로 cosmological chirality, null significance 또는 family 주장을 만들지 않는다.

**K03는 새 관측 요약과 약한 조건부 정보량을 구분한다.** [설계 분석](k03_design/REPORT.md)의 epsilon=.3 oracle upper power는 0.050074856412이고, 80%에 필요한 정보 배수는 1.17502e7이다. epsilon이나 covariance update는 측정된 물리 remainder가 아니다. [새 depth moments](k03_depth_moments/REPORT.md)는 승인된 1회 full pass로 755,850행을 처리했다. reported-z 세 bin은 200,785 / 369,335 / 185,730행이다. 기존 102열을 profile한 여섯 slope의 정보 보존은 1.584853%, score는 12.140206이다. working-law tail 0.058913은 실제 empirical p-value가 아니다. 해당 좌표는 reported-z이며 true depth나 physical history가 아니다. catalogue pass를 다시 쓰지 않았고 K03 physical HOLD와 소진된 R23-Q ultra를 유지한다.

**광학·boost·SN의 해석 범위.** [optical shear](optical_shear/REPORT.md)의 8개 full-coefficient reference ellipsoid는 모두 projected zero STF를 포함한다. 양의 shear lower를 얻지 못했다. 0.95는 선택한 Gaussian reference quantile이며 관측 95% confidence가 아니다. magnitude intercept는 양의 물리 H를 측정하지 않고 optical tensor는 등록된 G congruence의 local shear가 아니다. Model A의 undefined STF도 zero로 대체하지 않는다.

[boost quotient](boost_acceleration/REPORT.md)는 선형 acceleration dipole과 calibration dipole의 정확한 설계 퇴화를 보이며, inverse-velocity와 고정 quadratic log-velocity depth 공간의 최소각은 약 .783–.796도다. 이 거의 중첩은 물리 acceleration 측정이 아니다. q=.1에서 leading-low-z finite-q 값 .2287874528 mag와 선형 값 .2171472410 mag는 다르다. [비선형 quotient](nonlinear_optical/REPORT.md)는 nuisance 투영으로 linear/quadratic가 사라진 뒤 cubic 잔차를 보존한다. 두 가설의 동일 remainder ball이 `rho=d0/2`에서 겹치면 조건부 maximin benchmark는 size .05로 내려간다. finite-z/boost/selection/calibration remainder는 미측정이므로 이 비영 shape도 물리 귀속을 허용하지 않는다.

[SN 공개 release](sn_release/REPORT.md)는 고정 Pantheon+ release의 277행, 238 CID, 15 survey code를 사용한다. 공개 total covariance를 정확히 한 번 쓰며 PV를 임의로 빼거나 latent PV를 다시 더하지 않았다. calibration–flow full cross covariance를 유지한 조건부 적합이다. CF4와의 cross covariance와 source-qualified 선택법칙은 없다. 공개 release 적합은 기존 nominal trained model/PS1 configuration/observed FITRES parity 실패를 수리하지 않는다.

## full tensor와 depth 함수상

전체 `(x,F,Pi,Q,G_F)`가 결과다. x는 rank/parity가 있는 tensor/functional bundle이며 CMB의 full Q/O와 K03의 **full24**를 scalar로 대체하지 않는다. F의 exact coordinate support, conservative norm outer bound, pushforward와 reference occupancy는 서로 다른 의미다. Q_ref의 10 µas/year direct-sum ball과 고정 CMB scale은 계산 기준이며 physical MES anchor가 아니다. Q의 물리 anchor는 unavailable이다. Pi는 동일한 **4096개 공동 Gaussian replicate row**에서 strict exceedance를 세는 유한 빈도다. 물리 Pi는 **[0,1], unknown mass 1**로 남고, 이전 2048 physical sample의 unknown 상태를 새 law로 메우지 않는다.

[tensor bundle](tensor_bundle/REPORT.md)와 [보정 depth images](depth_images/REPORT.md)는 full24 평균·공분산, slope와 bin cross-block, 동일 sample law를 유지한다. `Y_b=gamma_b+c_b theta`의 Y18과 anchored `Z18=(Y0,Y1−Y0,Y2−Y1)`은 모두 보존한다. Y→Z는 rank18로 invertible이지만 delta만 남기면 rank12로 common mode가 사라지고 full24→Y18은 여섯 방향을 잃는다. 따라서 Y18/Z18은 full24의 대체물이 아니다. 수정된 36-coordinate 함수상은 세 bin, 인접 contrast와 deep–shallow의 E1 polar/B1 axial 벡터를 포함한다. shared rho `0,1,2,4,8`에서 양의 norm lower 수는 `12,12,10,4,1`이다. norm 구간은 sharp nonlinear image가 아니라 conservative outer다. cross-depth covariance를 0으로 놓는 counterfactual에서 contrast scale 비율이 .196–.326으로 달라져 공동 covariance의 실질적 영향을 보여 준다.

## 첫 실패, 수리와 보존 한계

CMB 첫 후보는 정규화된 `(sqrt2 Re,−sqrt2 Im)`을 raw Re/Im으로 받는 STF projection에 넘긴 convention 오류였다. 첫 후보와 raw는 `PRE_PROJECTION_REPAIR/`에 보존했고 12개 basis·정확 회전·독립 harmonic 검사로 경계를 고쳤다. 첫 pilot/primary 차이도 삭제하지 않고 별도 source row로 유지한다. depth 첫 후보는 raw intercept를 써서 shared slope를 누락했다. [최초 검토](DEPTH_REVIEW_INITIAL_RAW.json), [수리 receipt](DEPTH_REPAIR_HOST_RECEIPT.json), [최종 독립 검토](DEPTH_REVIEW_FINAL_RAW.json)가 연결된다. `first_candidate_03222b7d/`를 보존하며 수정 후 평균은 최대 8.02452 µas/year, covariance entry는 최대 10.2636 (µas/year)² 변했다. norm Pi 35/72, E·B Pi 18/18 cell이 바뀌었다.

boost의 finite-q 범위, CMB envelope의 clipping kink와 centered noise 반례, nonlinear power의 overlap 이후 잘못된 보간도 각 bounded repair와 최초 receipt를 남겼다. 반면 [chirality draft transition](CHIRALITY_DRAFT_TRANSITION.json)의 옛 manifest/figure/receipt byte copy는 **보존되지 않았다**. 옛 reported hash와 run metadata만 남으며 과거 draft의 byte 검증을 주장하지 않는다. 최종 e974 manifest는 새 독립 검토에 재결합되어 통과했다. 실제 누적 생산 시작 4회 20.13초, test 시작 3회 7.63초를 모두 계산했고 final run만으로 비용을 다시 시작하지 않았다. token·금액 사용량과 observed model identity는 UNKNOWN/NOT_INDEPENDENTLY_OBSERVED이며 0으로 보고하지 않는다.

## 여섯 논문의 다음 입력 조건

아래는 [source-specific step-back](FRONTIER_STEPBACK.json)의 residual이다. 기존 [METHOD_FRONTIER](../METHOD_REBOOT_20261023/METHOD_FRONTIER.json)의 경로에 더해 K03 depth, nonlinear quotient, chirality가 실제 처리되었다. 새 입력이 오면 해당 의무만 다시 평가하며 완료된 인접 분석을 반복하지 않는다.

| 논문 경로 | 현재 결과를 넘어가기 위한 정확한 payload trigger |
|---|---|
| P1 통계 functional | source-qualified selection/physical law, source-congruence map, physical MES anchor 또는 calibrated identified interval. 현재 finite scenario image만으로 대체 불가 |
| P2 CMB | 동일 FULL/HM/OE processing의 total-field/noise/foreground/weight-estimation/selection joint law, common-contaminant 제약과 cross-operator response |
| P3 거리 | parent targeting/detection/rejected-source 확률, source-qualified calibration/group/PV covariance, finite-z response/remainder와 명명된 source-congruence map. SN은 별도로 pinned nominal training/PS1/FITRES parity product 필요 |
| P4 local/global | 실제 외부 history, 선택·calibration·joint covariance가 적격인 response와 독립 injection law. analytic alternate는 original external-history 의무를 충족하지 않음 |
| P5 family | 외부 native polarized all-m/high-ell family/mode/history atlas, admissible IC/epoch·convention·normalization, mask/operator/null/equivalence 검증. 내부 solver/ODE 제조로 대체 금지 |
| P6 kinematic | centroid/matter/source-class response, selected reported→true-depth/PM likelihood, residual Gaia calibration/cross-source/spatial covariance, physical history와 congruence |

기존 628/274 authored-law 실패 **T=4.555321823822732, p=.000976324139614352**는 그 옛 law의 실패로 남는다. 새 조건부 모델의 p-value로 재해석하지 않는다. V03 외부 history, B02 native atlas, K03 physical, SN nominal parity의 HOLD와 기존 R9 상태도 그대로다. 물리 법칙·anchor·응답이 없는 곳은 UNKNOWN/HOLD이며 조건부 그림이 그 빈칸을 채우지 않는다.

[재개 안내](report_results/RESUME.md)는 실제 state와 다음 명령, 각 입력 trigger를 묶는다. controller는 native host가 packet을 dispatch·ack·record하고 다음을 요청하는 프로토콜이며 daemon이 아니다. 이 보고 후보의 독립 검토와 host push가 다음 publication 단계다. source push, owner-local 설치, live activation, merge, 투고는 각각 별도 사건이며 여기서는 수행했다고 보고하지 않는다.
