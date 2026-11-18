# R67: 일곱 과학 축의 융합 연구계획 (수렴형)

연구 기준 2026-11-18, 기준 commit 1d833bbe0e6c70a42f2d0af002c2e6a7cfcd0593. 정확한 **7 연구 축 / 6 논문 P1–P6**, 기존 science 42개와 수용 조건 보존. 실제 실행 성과는 [REPORT_KO.md](REPORT_KO.md), [FUSION_DAG.json](FUSION_DAG.json), [CONDITIONAL_DATA_REGISTRY.json](CONDITIONAL_DATA_REGISTRY.json), [CODING_10_STAGES.md](CODING_10_STAGES.md)에 분리한다. 논문 투고 상태 NOT_READY_TO_SUBMIT. 일반적인 겉보기 다중극 검출을 새로운 cosmological anisotropy라고 승격하지 않는다.

## 중심 과학 질문

같은 관측 source와 frame에서 얻은 저차 방향 의존 신호를
(a) 실제 indicator/source selection·거리 영점,
(b) 관측자 운동·지속적인 상대 유동,
(c) 유한 깊이의 spacetime kinematics,
(d) CMB photon stress·Bianchi geometry
로 실증적으로 분리할 수 있는가? **구별력이 없다면 그 물리적 상한과 정보의 영공간을 관측자료로 제시**하는 것도 정당한 결과다. 새 메타 통계를 계속 개발하지 않으며, x/Q/Pi/F/G_F는 각 likelihood의 종속 표현으로 사용한다.

## 주력 1: CF4 같은 그룹 비교를 이용한 Hubble anisotropy의 물리적 해석 제한

### 이미 이번에 얻은 결과
38,053 CF4 group row ID는 실제 table3/table4에서 일치. FP–TF 중복694, FP–SN202, TF–SN286, 고유 multi-indicator group998, 세 가지 모두 있는 group92. 그룹별 물리적 거리를 정확히 제거한 상대 indicator의 radial3+signed angular8 모델을 만들었으며 joint relative TF/SN 22계수는 rank22. **검정값과 conditional p값**은 REPORT_KO.md에 있다. 독립 검토에서 발견한 rank-deficient QR 경계, 공유 source covariance 계약 결함을 교정한 후 actual CF4 32,768 wild bootstrap 재실행 수치가 유지됐다.

### 남은 단 한 번의 결정적인 full-source 분석
다음 정보가 있으면 기존 R64의 CF4 grouped/window 68/72D 표현과 같은 원본 group IDs로 묶되 **단일 공통 covariance/likelihood**로 계산한다.
1. 원 개별거리 지표별 selection/measurement model, upsteam registration/zero-point posterior 또는 calibration Jacobian, group membership. 기존 full CF4 table2/3/4와 R64 source operator를 우선 사용하고 별도 대량 다운로드를 가정하지 않는다.
2. method–method 및 group–group global covariance (or conservative envelope)와 physical peculiar-velocity covariance를 분리한다. 총 covariance C=N_stat+S_pv+J_cal Σ_cal J_cal^T+C_selection.
3. 사전에 정의한 angular model: isotropic+radial bulk, bulk with depth, directional Hubble dipole, STF quadrupole. 잔차의 radial dependence와 method composition/footprint를 함께 fit. 공통 부분식별을 유지한다.
4. Group-overlap difference를 추가 독립 데이터로 곱하지 않고, full source y를 mean/contrast로 재기저화한다. Mean–contrast covariance가 0인지 실제 C로 검산한다.
5. Original unaugmented/augmented CF4 operator, Stiskalek–Desmond–Lavaux 2026 CF4 W1/Pantheon+ model, matched source/method/cuts에서 effect size, heldout calibrated predictive log-score, conditional coverage 및 nuisance sensitivity를 나란히 비교한다.

**성공:** 실제 보정 law 하에서도 남는 하나의 방향별 physical response identified combination과 정확한 uncertainty, 또는 선행분석 대비 분산·bias·coverage의 실측 개선. **실패/종료:** calibration body가 물리 신호 전체와 교차하면 H(z,n) 발견은 철회하고, 실자료의 calibrated nonidentifiability/robust null을 방법론 결과로 출판 검토한다. 추가 indicator를 받으려면 source-specific precision/covariance rank가 기존 holdout으로 부족함을 보여야 한다.

## 주력 2: local boost vs matter/radiation tilt의 독립 비방사 정보

이번 Gaia-CRF3 sourcewise E/B l=1 실제 적합은 1,580,645 quality source, rank6이고 full-sky E norm5.567 μas/yr, B norm4.290 μas/yr. Spatial 192-patch error 및 hemisphere disparity가 강하다. 이는 observer acceleration/frame-spin diagnostic이지 velocity/tilt/vorticity 검출이 아니다. R63가 사용한 compensated history는 CF4에 사실상 구별력이 없다. 새로운 통합 posterior를 만들려면:
1. Gaia PMRA* 좌표·절대 frame rotation vs active source motion 부호, reference frame systematics/AGN structure noise, VLBA 713개 real proper-motion crossmatch를 고정.
2. 가능한 경우 실제 quasar redshift labels/selection을 확인해 E/B l=2 depth response를 model-bound하게 비교한다. Makarov–Heinesen–Schücker 2026 Gaia-Bianchi-I 선행 분석과 동일한 estimand 및 redshift trend를 복원 비교해야 한다. 여전히 cosmic omega_a와 position drift의 B-mode는 다르다.
3. CMB aberration/Doppler, radio counts selection, CF4 bulk history가 대응하는 상대속도 β_{O|R}, β_{M|R}와 그 시간미분을 별도 frame operator로 적합. 물리적 transfer나 shared-covariance 없으면 형식적 rank 합산 금지.
4. Nuisance-projected J_eff의 새로운 nonzero singular value와 실질적 power 증가를 목표로 한다.

**성공:** local boost와 global tilt 간 한 제한된 이력 family의 실제 소스·시점 자격을 갖춘 구별/상한 또는 calibrated nonidentifiability. **종료:** 추가 관측은 물리 frame mapping 없이 관측자 proper motion systematics만 늘리면 별도 frame-calibration paper로 분리하고 global tilt claim 중단.

## 조건부 주력 3: low-ell CMB photon stress → anisotropic geometry

R66 signed STF/π_γ actual PR3–PR4, R62 source-response-aware shape classes, R61 finite-depth σ-like apparent tensor는 물리적으로 독립된 대상이다. 한 restricted Bianchi I 또는 V geodesic normal+stress closure를 명시한 뒤 source/observer Jacobi transfer, radiation polarization source and optical response, δT/T and shear history의 경계조건을 일치시켜 그 계열 내에서 family recovery vs isotropic null을 검산한다. 실제 Planck Commander source-qualified scalar T MC 0200 product unit/beam 처리와 same sky T/E/B noise/foreground null은 물리 claim을 시작하기 전 인증한다. **종료:** 모형·transfer가 없으면 현재의 signed stress와 tensor shape compatibility를 독립 관측 결과로 보존하고 Bianchi family posterior로 승격하지 않는다.

## 조건부 주력 4: HSC Y3/KiDS spin-2 lensing × velocity/expansion

Raw HSC Y3 SACC 170×170 covariance 및 local 108 parents×13 region source mocks, KiDS catalog and mock, ACT lensing 등이 존재한다. 하지만 lensing shear γ^{WL} = line-of-sight Jacobi tidal image와 matter kinematic σ_ab는 같은 양이 아니다. 먼저 하나의 source-redshift/kernel with calibrated selection에서 동역학적 transfer를 유도하고, \(K_{\mathrm{WL}}\sigma\)와 PV/H_D source response의 공통 nullspace가 실제로 줄어드는지 실험한다. 필수 transfer/selection qualification이 없으면 단순 C_ell cross-correlation을 우주론적 rotation 검출로 선언하지 않는다.

## 추가자료 7종 활성화 규칙

정본은 CONDITIONAL_DATA_REGISTRY.json. ① PR4 Commander T MC는 정확한 제품 단위/시뮬레이션 교환가능성 확인 후, ② DESI DR1 full FP PV은 공식 공개·CF4와 source-match 필요성 입증 후, ③ 부족한 RACS RMS tile은 실제 footprint 비교 후, ④ Gaia QSO redshift/structure flags는 l2 physical history 필요시, ⑤ kSZ remote-dipole W_v/b_v/공분산은 velocity transfer qualified 뒤, ⑥ HSC 추가 mock은 108 independent parent의 covariance coverage가 사전 정밀도 기준에 부족할 때만, ⑦ Bianchi transfer benchmark는 선택한 family의 물리 방정식이 구체화된 뒤 필요하다. **자동 download/offline gate 생성 없음.**

## 하나의 출판 결론과 중단 규약

현재 **완료된 과학 결과**는 same-group CF4 relative-calibration partial identification과 group-wild working law의 민감도, Gaia E/B observer-frame 실측 coefficient 및 spatial systematic sensitivity다. CMB signed radiation-stress, radio source count and weak-lensing 자료는 source-qualified posterior를 계산한 결과로 합쳐진 것이 아니다. 원 논문은 CF4 overlap zero-point/selection, Gaia VSH/Bianchi I, polarized transfer의 존재를 우선 인정한다.

주 논문 후보: *Source-matched calibration modes and the interpretability of directional distance anisotropy in Cosmicflows-4*. 각 결과의 source group, physical target, frame, units, covariance, calibration, prior/null, response approximation을 본문과 기계 판독 예측에 함께 붙인다. 새 실자료 likelihood 없이 단지 DAG/메타 문서를 보강하는 추가 루프는 진행하지 않는다. 원래 P1–P6 acceptance와 NOT_READY_TO_SUBMIT은 보존한다.
