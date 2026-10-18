# 여섯 논문: 현재 근거, solver-free 목표, 투고 최소조건

2026-10-18. 분석 기준 GitHub `cosmosapjw-quantum/htt_base@967ef7c8f0b132ecaaba343045d333d4ebf299c1`, branch `research/htt-sixpaper-p2-l01-r10c10-runtime-recovery-20261017`. 현재 날짜와 이전 검토일의 차이는 2026-10-18 − 2026-10-14 = 4일이다. PR 점검 구간은 10월 14–18일이며, 아래 문헌 비교는 주제별 과거 원전과 2026년 논문을 포함한다.

이 문서는 scoped publication assessment / 연구 설계다. 원래 six-paper 목표와 canonical DAG를 보존한다. 42개 중 14개 completed_scoped, 28개 pending; 현재 ready는 L01/S02. 여섯 논문 모두 NOT_READY_TO_SUBMIT다. 이번 원전 대조는 실행 허가나 공개 투고를 뜻하지 않으며, 논문 신규성·게재 가능성을 보증하지 않는다. 현재 투고 가능하다고 입증된 목록은 비어 있다. 이미 재사용할 수 있는 결과와 앞으로 완성할 논문 후보는 다음과 같다.

## 1. 논문별 현재 결과와 완성 목표

| 논문 | 지금 입증·계산된 내용 | 새 solver/ODE 없이 할 수 있는 다음 과학 결과 | 최소 투고 격차 |
|---|---|---|---|
| P1 signed x, Q, F, Pi, G_F | 원 draw ID/weight와 coupling을 보존하는 typed pushforward; signed x와 sector F 분리; strict exceedance와 unknown-mass 구간; S01 math/isolated tests. 실제 공통-congruence x posterior는 없음. | S02에서 실제 보존 draw/source를 받아 관측 조건부 함수와 missing-sector 구간을 계산; S03에서 같은 draw의 anchor/floor/depth/selection 동시 민감도. Γ sensitivity는 기존 일곱 gate 연구에 이미 있으므로 새 정리로 중복하지 않음. | S04의 실제 관측 law 또는 외부 물리 bound가 제공하는 비자명한 identified set, coverage, 실제 데이터 그림. 일반 missing-mass bound는 Manski 선행 내용. |
| P2 low-ell morphology | 실제 source-mask finite harmonic K; scalar-T부터 spin-2 finite-mask 차이까지 발전. PR557/558의 사용자-local 수치 ||ΔK||=0.4396287723908507, E-high→B-low norm=0.2564294649638681은 ell6..8→2..5 finite geometry. H02/L03 보존 paired bank의 200 heldout sky rank=147/201≈0.73134는 조건부 기술통계. | L01 source/beam/mask/remainder를 이어서 실제 처리 민감도·공통-sky covariance를 정량화. L02 predeclared O(3) shape와 orientation statistic 분리. 기존 공개 simulation을 재처리하는 L03, 이후 one-score-per-sky joint null로 L04. 물리 anomaly가 없어도 calibrated processing sensitivity/null 논문 가능. | 실제 map과 simulation의 처리·selection·T/E/B·noise/systematic law 적합성, ell 범위 밖 잔여항, 전체 choice family의 look-elsewhere. K norm과 Gaussian toy만으로 p-value를 만들 수 없음. |
| P3 directional H_W | 실제 35,970 selected groups의 apparent 32d four-window coefficient/Schur diagnostics, method/patch sensitivity. H02 angular calibration gauge와 실제 source Gram/Fisher dependence. | 공개 raw W1-TF와 group genealogy를 잇는 한정된 selected likelihood; shared zeropoint/velocity 및 cross-window covariance; calibration bound별 identified-set 곡선과 heldout tests. 대립 flow·anisotropy 모델을 같은 selection으로 비교. | H02 실 selection/covariance가 핵심. H04 physical mapping, H05 Boubel/Stiskalek/Duangchan/Kalbouneh 재현·대조. 현재 conditional e_DMzp diagonal law를 실제 분산 law로 승격 불가. |
| P4 observer boost/global tilt | beta_RO, beta_RM, beta_MO와 B_W 구별; endpoint gauge, finite Lorentz taxonomy. 두 history-window rank2→독립 observer anchor를 더해 rank3인 제조 예시. | 실제 released CMB observer-boost processing(V02), nuisance-projected response와 uncertainty에 대한 stable-rank/identified-subspace 평가. 문헌의 optical boosted Hubble relation을 적용하는 제한된 frame-consistency 분석. | V03의 독립 물리 global-history kernel가 필요. 다른 redshift bin 두 개만으로 constant global component를 observer endpoint와 분리했다고 주장 불가. H04와 공통 likelihood/covariance가 뒤따라야 함. |
| P5 Bianchi family | family/mode inventory; finite templates; Bianchi-I의 정확한 collisionless photon-redshift/blackbody regression. 이들은 polarized family inference가 아님. | 기존 공개 transfer output이 실제 확보되면 source-qualified 일부 family의 observation-operator equivalence와 mode/IC/prior coverage를 비교. 자료 부재 중에는 frozen transfer-ready 비교 프로토콜·분석적 regression까지만 수행. | B02 polarized physical source transfer, B03 실제 Planck response/null, B04 evidence·injection/equivalence. 새 native solver/ODE 작성 없이 all-11 observational classification은 현재 완성 불가. 이미 검증된 외부 subset이면 subset 논문 목표를 별도로 좁힐 수 있지만 원래 all-11 목표는 보존. |
| P6 kinematical fields | 같은 u의 단위·congruence 계약; nᵀωn=0; actual apparent STF identified subspace; galaxy tangent+quasar frame calibration의 제조 rank12→15 예시; finite optical benchmark. | Heinesen/Maartens 광학 relation과 frame correction을 유지하며 데이터가 식별하는 선형 조합과 finite-z truncation error를 계산. 실제 공개 nonradial data가 있으면 source-matched weighted singular values/상한. | K03 transverse source/covariance, K04 finite-z same-congruence optical response와 H02/H04, K05 history/sector coupling. 실제 cosmic omega/A를 가짜 narrow prior로 대체하지 않음. leading radial null은 모든 관측에서의 vorticity no-go가 아님. |

우선순위 판단: P2와 P3는 실제 자료와 재사용 연산자가 많아 가장 가까운 solver-free 관측 논문 후보이다. P1은 이 둘의 유효 likelihood/identified-set application을 공급받으면 독립 방법 논문 후보가 된다. P4/P6는 식별 가능한 subset를 목표로 계속 진행할 수 있다. P5의 원래 물리 family 비교에는 외부 polarized transfer가 필수다. 이것은 실행·과학 입력 현황에 대한 판단이며 journal acceptance 순위가 아니다.

## 2. 원전의 식·결과와 직접 비교

### P1: 확률구간 자체는 새 기여가 아니다

Manski, *Partial identification with missing data: concepts and findings*, IJAR 39 (2005), [DOI](https://doi.org/10.1016/j.ijar.2004.10.006); [저자 원전 설명](https://isipta03.sipta.org/charles.pdf). 관측 여부 z를 두면 P(y)=P(y|z=1)P(z=1)+P(y|z=0)P(z=0)이고 마지막 분포가 알려지지 않아 identification region이 생긴다. HTT의 known-tail a와 unknown mass u에 대한 [a,a+u]는 이 기존 missing-data 구조의 사건 확률 특수형이다. 기여 후보는 물리적으로 가능한 missing-sector completion, source coupling, window/denominator sensitivity를 실제 자료에 연결하는 데 있다.

Giacomini–Kitagawa, *Robust Bayesian inference for set-identified models* (2021), [Econometrica 원문](https://jstor.econometricsociety.org/publications/econometrica/2021/07/01/robust-bayesian-inference-set-identified-models/file/ecta200254.pdf): 구조 parameter에 대한 조건부 prior class를 통해 posterior lower/upper probabilities와 posterior mean set을 다룬다. HTT의 partial interval이 하나의 calibrated posterior credible interval인지, prior-robust set인지, deterministic outer bound인지 분리해야 한다.

### P2: Planck은 같은 sky의 여러 처리와 simulation 한계를 이미 다룬다

Planck 2018 VII, [A&A 641 A7 원문](https://www.aanda.org/articles/aa/full_html/2020/09/aa35201-19/aa35201-19.html), DOI 10.1051/0004-6361/201935201. Temperature의 이전 large-scale anomalies를 재확인하지만 polarization에서 이에 대응하는 unambiguous anomaly를 주장하지 않는다. 새로운 tensor 표현만으로 이 선행 결과를 넘어서는 것은 아니다. HTT는 동일 source 처리하의 invariant statistic, complete trial family 및 실제 null adequacy를 더 입증해야 한다.

Planck 2018 IV §§3.5/4.4, [원문](https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html), DOI 10.1051/0004-6361/201833881. 999 CMB-only와 300 noise-plus-systematics realization을 제공하고, 실자료의 frequency weights/mixing 등을 고정한 선형 component-separation propagation을 쓴다. 같은 realization의 full/HM/OE products를 별개 CMB skies로 셀 수 없다. E2E simulations도 data 대비 수% residual bias가 보고된다. 따라서 실제 FFP10 활용은 가능하지만 fixed-weight bank라는 사실만으로 완전 exchangeability가 자동 성립하지 않는다.

### P3: CF4 논문들의 서로 다른 estimand와 null을 맞춰야 한다

Tully et al., *Cosmicflows-4*, ApJ 944 94 (2023), [DOI](https://doi.org/10.3847/1538-4357/ac94d8). 논문 초록 55,877 galaxies/38,065 groups와 release table의 38,053 rows, HTT의 35,970 selected subset는 서로 다른 counts다. Published distance calibration, group overlap, method aggregation을 raw independence로 해석하면 안 된다.

Boubel et al., *Testing anisotropic Hubble expansion*, JCAP03(2025)066, [본문](https://arxiv.org/html/2412.14607), [DOI](https://doi.org/10.1088/1475-7516/2025/03/066). Eq.(3.4–3.6)의 direction-dependent TF zeropoint a0(n), a0 anisotropy=5 log10[h(n)/hbar]를 fits한다. 0.063±0.016 mag dipole는 H0=70 가정에서 2.10±0.53 km/s/Mpc에 대응한다. 그러나 constant-H0+bulk-flow에 대한 anisotropic-H0 모델 선호는 약하다. §5.1은 velocity-dipole 대 zeropoint-dipole mocks를 비교한다. HTT에 필요한 차이는 같은 sky/depth selection에서 covariance와 flow nuisance를 갖춘 복제 및 확장이다.

Stiskalek, Desmond & Lavaux, MNRAS 546(2), staf2048 (2026), [본문](https://arxiv.org/html/2509.14997), [DOI](https://doi.org/10.1093/mnras/staf2048). §3의 forward likelihood는 거리 적분과 calibration/velocity를 함께 사용한다. Eqs.(5–7)의 distance prior는 n(r) f(r)/∫n f, f(r)=r^p exp[-(r/R)^q]로 선택을 현상론적으로 근사한다. CF4 conditional zeropoint dipole는 0.087±0.019 mag, 4.1±0.9%, 모델 odds 877:1이지만 더 자유로운 radial velocity-dipole가 local flow/systematics로 설명하며 standard-model-compatible bulk curve를 얻는다. 이 논문의 결론을 “dipole가 유의하지 않음”으로 바꾸면 틀린 비교다. HTT의 새 결과는 significant template와 physical expansion 사이를 실제 data law로 판별해야 한다.

Duangchan et al., A&A 708 A119 (2026), [본문](https://www.aanda.org/articles/aa/full_html/2026/04/aa56645-25/aa56645-25.html), [DOI](https://doi.org/10.1051/0004-6361/202556645). Eq.(3)은 v_r^i=V_r+V·rhat_i; 다음 거리/redshift forward 관계로 distance modulus likelihood를 만든다. §3.4는 survey/sky/magnitude를 흉내 낸 64 mocks로 selection amplification을 보정한다. fiducial 160 Mpc/h에서 H0=75.9±1(stat) km/s/Mpc; nested spheres는 독립이 아니며 추가 systematic이 오차를 키울 수 있다. “Prior-free”는 velocity-field power prior를 쓰지 않는다는 범위다. Flat distance relation, mock cosmology, large-radius radial-flow behavior의 가정은 남는다.

Kalbouneh et al., [arXiv:2510.02510 본문](https://arxiv.org/html/2510.02510). Eq.(4.1)의 redshift-dependent real harmonic expansion, Eq.(4.2)의 coefficient-covariance χ², Table1/§4.1의 shell/method tests가 P3/P6와 직접 겹친다. 0.01<z<0.1 CF4/Pantheon+에서 낮은 z의 dipole와 quadrupole, common-axis interpretation을 보고한다. Null은 uniform ΛCDM measurement noise 및 400 km/s bulk-flow leakage 등으로 구체화된다. HTT의 common-calibration/selection/cross-window uncertainty가 이런 null을 얼마나 바꾸는지를 재현 가능하게 보이는 것이 차별화 후보다. 논문의 harmonic orthogonality를 불완전 selection 아래 통계 독립성 보장으로 받아들이지 않는다.

### P4/P6: frame과 optical law의 기존 결과

Planck 2013 XXVII, [원문](https://www.aanda.org/articles/aa/full_html/2014/11/aa21556-13/aa21556-13.html). High-ell aberration/modulation으로 알려진 dipole 방향의 observer velocity component 384±78(stat)±115(syst) km/s를 측정한다. 이는 intrinsic global matter-radiation tilt의 별도 증거가 아니라 observer-motion 측정 채널이다. 이 독립 채널을 anchor로 쓸 경우 실제 response·systematic covariance를 포함해야 한다.

Heinesen, JCAP05(2021)008, [원문 PDF](https://arxiv.org/pdf/2010.06534), [DOI](https://doi.org/10.1088/1475-7516/2021/05/008). General luminosity-distance series의 Eqs.(3.7–3.10)에서 dL=z/H_eff+(1−Q_eff)z²/(2H_eff)+…(논문 c=1 convention)를 얻고, 첫 세 차수 9/25/61 자유도를 정리한다. 첫 optical H_eff는 expansion·acceleration·shear를 포함한다. finite redshift window coefficient를 곧바로 θ/3 혹은 shear로 치환하는 데 필요한 rest-frame/clock/series remainder는 별도 의무다.

Maartens et al., JCAP09(2024)070, [원문](https://arxiv.org/html/2312.09875v3), [DOI](https://doi.org/10.1088/1475-7516/2024/09/070). §§3–4에서 matter-frame expansion tensor와 boosted observer의 Hubble multipoles를 구별하며, Eq.(3.5–3.6)는 Doppler와 shear-aberration의 결합을 명시한다. Luminosity-distance cosmographic relation은 그대로 boost-invariant하지 않아 적절한 redshift factor가 필요하다. P4/P6에서 velocity frame별 보정을 다시 작성하는 것만은 새 이론이 아니다.

MES, [1995 원전](https://arxiv.org/abs/astro-ph/9501016), DOI 10.1103/PhysRevD.51.1525; SAG [1997 원전의 1999 수정본](https://arxiv.org/abs/astro-ph/9904346), DOI 10.1086/303633. Covariant radiation multipoles와 거의-FLRW 조건의 연결이 선행한다. 한 observer의 masked Planck sqrt(C_l)/T0는 모든 fundamental observers의 multipole/derivative control을 자동 제공하지 않는다. 실제 physical epsilon 전달조건 없이 숫자를 MES bound에 대입한 것은 conditional proxy 계산이다.

### P5: subset/mode/initial-condition 범위가 중요하다

Saadeh et al., PRL117,131302 (2016), [원문](https://arxiv.org/html/1605.07178), [DOI](https://doi.org/10.1103/PhysRevLett.117.131302). 논문의 anisotropic-models section은 VIIh와 그 I/V/VII0 limits, near-FLRW open/flat 범위를 사용한다. 모든 11 family를 검증한 것이 아니다. Table2 joint-mode 95% bounds는 vector shear/H<4.7×10^-11, regular tensor<1.0×10^-6, log evidence ratio −11.7±0.3이다. Polarization과 initial regular/irregular modes가 크게 다르므로 오늘의 shear 크기만 비교해서는 안 된다.

동저자 MNRAS462,1802 (2016), [원전](https://arxiv.org/abs/1604.01024), [DOI](https://doi.org/10.1093/mnras/stw1731)는 ANICOSMO/ABSolve framework에 high-ell Bianchi power를 포함한다. Low-ell orientation template만으로 새 family discrimination을 주장할 수 없다.

Fleury, Pitrou & Uzan, PRD91,043511 (2015), [원전](https://arxiv.org/abs/1410.8473), [DOI](https://doi.org/10.1103/PhysRevD.91.043511)는 Bianchi-I null geodesic, redshift/direction drift, analytical Sachs/Jacobi matrix를 이미 유도했다. Repo의 exact collisionless benchmark는 좋은 regression oracle지만 그 자체의 새 물리 결과는 아니다.

## 3. 이미 있는 결과의 수치 범위

- H02 실제 source에 대한 X=Σ_m D_mX이므로 beta→beta+delta, gamma_m→gamma_m−delta가 동일 catalogue prediction을 준다. 이 finite fitting law에서 global angular beta는 unanchored calibration과 분리되지 않는다. universal cosmological no-go가 아니다.
- 조건부 Gaussian prior gamma_m~N(0,τ²I)의 I_beta(τ)=ΣG_m(I+τ²G_m)^−1. 실제 source의 최소/최대 eigenvalues는 τ=0: 23973.0578/142523.2615; τ=.02 mag: 6373.9560/8808.0655; τ=.5 mag: 15.98336/15.99628. τ→∞는 0. 이것은 calibration assumption에 대한 정보 민감도이고 관측 calibration 측정치가 아니다.
- 실제 finite L03 bank는 six processing conditions×300 paired sky rows다. 100 scale calibration+200 heldout에서 Tobs=.98218956, count>=Tobs 146, rank147/201. 독립 1800 skies도, physical p=.7313도 아니다.
- K03 rank12→15, V03 rank2→3, Bianchi-I local H=.852 vs finite-window .854041049, selection density ratio462.975789은 모두 manufactured input의 결과다.
- PR534의 corrected shear-scalar relation ||a||/(3sqrt2)와 fiducial .00783892505는 Aij=sigmaij/H라는 미입증 bridge에 조건부다. apparent STF를 covariant Bianchi shear로 측정한 것이 아니다.

## 4. 소스·검토 범위와 다음 실행

직접 읽은 repo source: AGENTS.md, CURRENT_CODEX_RUNTIME.md, PUBLICATION_DAG/SCIENTIFIC_SCOPE/NOVELTY, H02_L03/RESEARCH_LOOP 및 실제 Fisher JSON, X02 matrix, physical_input_3week_audit/PHYSICAL_INPUT_RESEARCH, idle_data_seven_gate 이론/제조 수치. PR534–559는 부모가 제공한 body snapshot에서 science scope를 대조했다. 모든 diff/실자료를 재실행한 감사가 아니다.

Exa 9개 쿼리×5=45 result slots, SciSpace 두 자연어 쿼리에서 20개 discovery rows를 얻었다. 중복과 비원전은 걸러 사용했다. 45개 서로 다른 논문을 정독했다는 의미가 아니다. Primary article sections/equations/results를 위와 같이 읽었으며, complete published-likelihood replication은 미실행이다.

다음 행동: 부모의 L01/S02 실행결과와 위 논문별 차이를 결합하되, canonical node acceptance는 각각 따로 판단한다. P3의 immediate new analytic calculation은 동반 파일 CALIBRATION_ENVELOPE_EXTENSION.md를 참고한다. 모든 논문의 final submit state는 기존처럼 유지한다.

