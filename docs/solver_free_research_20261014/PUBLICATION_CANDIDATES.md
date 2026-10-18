# 출판 후보와 실제 결과의 분리 감사

기준 commit은 `89621f4c9a6f63449813587a0fadeb13287f8e10`, 비교 기준은 `7e944771`이다. PR 번호 증가와 기존 PR #532의 7개 commit 증가를 구별한다. 이 worker는 부모가 제공한 선택 파일과 exact-ref refinement를 읽었으며 commit ancestry/전체 diff의 최종 확인은 부모가 담당한다. requested runtime은 gpt-6.1-sol/high, observed runtime은 UNKNOWN이다.

현재 가장 설득력 있는 출판 경로는 **선택 관측법칙, 같은 sky를 유지하는 joint scan, Gaia 영향 연산자의 응용 방법론**이다. 해당 계산은 이미 존재하므로 원고 개발에 사용할 수 있다. 신규성과 주장에 필요한 validation을 아직 채우지 않아 즉시 제출 가능 판정까지 확보한 것은 아니다. 방법론 논문에 native Bianchi solver를 새 전제로 추가할 이유는 없다. 이번 cross-law·Gaia geometry·Union assumed-prior·관측 bound 계산은 완료되었으며 publication novelty는 provisional, 제출 상태는 **NOT_READY_TO_SUBMIT**이다. 실제 결과와 미래 물리 추론은 아래에서 별도로 정리한다.

## 이미 존재하는 방법론

| ID | 현재 구성과 근거 | 문헌 대비 남은 신규성 | 최소 다음 분석 |
|---|---|---|---|
| M01 | CF4 law `∫p(eta)Πfi / ∫p(eta)ΠZi`; 같은 2048 draw 거리 사상. `results/cf4_crosslaw/result.json`의 두 law 교차 생성·적합32catalogue/64fit 전부 accepted | PRE/POST law mismatch의 conditional H bias/RMSE 차이는 실제 계산했다. CF3/CF4 선행 수식과의 응용 신규성 비교는 남는다. | 완료 결과를 재사용해 precision-target population/calibration family를 확대하고 실제 survey selection·method overlap·source-motion 법칙을 연결한다. |
| M02 | 60 training/240 calibration을 분리하고 같은 latent sky 행에서 48 processing/statistic choices의 max를 계산. `smica_response_scan_v2/calibration.json` | joint max, dependent resampling, plus-one rank 자체는 알려진 방법이다. identity/provenance를 유지한 processing factory와 기존 anomaly 재평가의 재현성 기여가 후보이다. | 실제 sky/FFP source의 beam·mask·downgrade·dipole/quad correction bridge를 맞춘다. 역사적 선택은 retrospective 범위로 유지한다. |
| M03 | 6×9512 실제 영향 연산자; basis-invariant per-source disk support, 동시6D ellipsoid와 attaining witness 완료. `results/gaia_geometry/result.json` | dual norm·sandwich·chi-square identity는 표준이다. 실제 Gaia operator의 geometry 적용 신규성은 provisional이다. | 다음은 PSD angular covariance family와 empirical correlation amplitude/scale 또는 independent cohort의 연결이다. |
| M04 | endpoint `[I,I]` rank3/6, intrinsic dipole 사영 후 rank0; response/covariance error 충분조건과 finite rank checks 완료. `results/observation_bounds/result.json` | 동일 열의 nullspace와 singular-value perturbation은 표준이다. 별도 physical response를 포함한 global no-go는 입증하지 않았다. | 같은 frame/congruence의 실제 distinct source/depth/multipole/history response를 공급해 projected separation을 검산한다. |

## 현재 실제로 얻은 결과

| ID | 정확한 값과 source | 현재 출판 지위와 새 분석 기준 |
|---|---|---|
| R01 | `posterior/result.json`: rho=0에서 Ωm=0.3574564654±0.0270842954, H0rd=9974.6252554±204.1809881 km/s | 조건부 compressed-Gaussian 재현/민감도 결과. assumed node-prior sensitivity와 public Stan/paper discrepancy 조사는 완료했다. exact FITS generating run-code/prior binding은 미해결이며 certified likelihood correction은 아니다. |
| R02 | CF4 baseline MLE H=73.0121990187, report posterior mean=73.216174. `injection_v1/result.json`에서 H bias −0.3571247738, RMSE1.9537025919, 32/32 resolved. 최신 calibration .1mag refinement H=67.2919183135 | 실제 24 fixed-slot 조건부 방법 적용. full CF4 H0 측정과 구별된다. 두 선택 semantics의 paired 생성·적합 비교는 R08에서 완료했다. empirical selection law와 family 확대가 다음이다. |
| R03 | tensor rank17/241=0.070539, same-sky48선택 scan63/241=0.2614107884. tensor 값은 current scientific report, scan은 직접 calibration JSON | retrospective morphology 재평가 후보. 두 rank와 역사 p=.039를 독립 증거로 합산하거나 개선량으로 읽을 근거가 없다. matched processing bridge와 choice attribution이 다음 분석이다. |
| R04 | `class_noise_v1/result.json`: joint zmax4.7787425068, 0/160 exceedance, rank1/161=0.0062111801; EE 주도 | independent split-noise proxy와 관측의 불일치 결과. released joint split law·signal leakage·systematics를 source 제품으로 맞추면 instrument/validation 논문 후보가 된다. |
| R05 | Gaia 4756 source의 spin/glide 계수 [3.6675,−.3739,−6.1202,−1.1794,−1.3989,.2472] µas/yr. box10 support [16.0821,13.9264,15.9274,15.6091,14.9711,14.8981] µas/yr | fixed outcome-selected Gaussian proxy의 민감도 결과. 이미 모든 coordinatewise1.96σ 구간에0이 포함된다. disk·동시 ellipsoid 적용은 R09에서 완료했다. 다음은 PSD angular covariance/selection의 robust frontier다. |
| R06 | current scientific report: PR3 reference A=1.009562±.026253, fixed-CMB .995252±.024119; BK18 fixed HL Q=545.104273; FFP 첫 pair formal linearity | release/native parity와 operator 검증. 이 worker는 보고서값을 확인했고 개별 result를 모두 읽지 않았다. 동일 정보·reference cosmology의 재사용 때문에 새 독립 cosmological constraint의 근거로 합산할 수 없다. |
| R07 | report: COSMOS784016행/79batch, CCHP183543 photometry행, KiDS5 N(z), SDSS33641 join행 | 실자료 control/retention 결과. count 자체의 신규성은 낮다. 구체적인 calibration/selection estimand와 comparison baseline을 하나 정하면 별도 응용 후보를 판정할 수 있다. |

## 이번 연구에서 추가로 완료한 실제 결과

다음 source 경로는 이 문서 디렉터리 기준이며 각 `result.json`의 scope를 따른다. 모두 **NOT_READY_TO_SUBMIT**, novelty provisional이다.

| ID | 완료 결과와 source | 해석과 다음 단계 |
|---|---|---|
| R08 | `results/cf4_crosslaw/result.json`: law당16개, 새 conditional catalogue32개, paired fit64개 전부 accepted. PRE 생성에서 POST−PRE H=2.09633403, MCSE=.01670186; POST 생성에서2.04813049, MCSE=.02026723 | matched PRE bias−.237853/RMSE2.400705 vs wrong POST1.858481/3.077939; matched POST.009982/2.989571 vs wrong PRE−2.038148/3.553717. H는 endpoint km/s/Mpc. 새32개는 기존 injection32개와 별도 pool이며 coverage로 합산하지 않는다. 실제 CF4 H0/selection 측정은 아니다. |
| R09 | `results/gaia_geometry/result.json`:4756 source의 disk10 support=[12.7749,11.5432,13.1219,12.5970,11.6854,12.4345] µas/yr; joint95%6D radius3.548462659;4756 tangent rotations와20000 fixed-law stress draw | disk와 같은 숫자 coordinate box는 다른 admissible sets다. joint/marginal width ratio1.8104734, rho0부터 joint region이0을 포함한다. outcome-selected Gaussian proxy이며 empirical Gaia coverage가 아니다. 다음은 PSD angular covariance다. |
| R10 | `results/union_prior/result.json`: assumed λ={0,.5,1}; λ1 mean shifts/baseline SD는 Ωm+.0613041853,H0rd−.0222748537,M−.2742355359; joint-grid TV=.0243559499 | public Stan cosmo_model{2,6} branch와 논문 prior 설명의 차이는 조사했다. 해당 코드와 exact frozen FITS의 생성 binding은 미해결이다. prior removal/no-removal 어느 쪽도 certified correction이 아니며 scenario integral은 Bayes factor가 아니다. |
| R11 | `results/observation_bounds/result.json`: CLASS assumed equal-score budget.9893361124에서 첫 nonreject interval; IID tail upper와alpha.05 사이 TV margin.0272082505. synthetic finite fold response−.3675694638, normalizer term+.1324305361, FD error2.204×10⁻¹⁰ | standard interval-rank·quotient derivative·singular-value identities의 finite checks다. score budgets는 assumed이며 physical split law를 보정하지 않는다. fold는 dimensionless synthetic observation이고 physical global response/MES bound를 공급하지 않는다. |

## 이번에 수행한 solver-free 추가 계산 세 가지

`compact_publication_calculations.py`를 실제 실행했고 `ADDITIONAL_CALCULATIONS.json`에 입력 hash와 결과를 남겼다. 원자료 재적합·ODE·native solver는 실행하지 않았다.

1. **ADD01 — CF4 accepted sensitivity 요약.** 같은 preselection semantics의 scenario MLE H 범위는 67.2919183–74.7612064 km/s/Mpc이다. .1mag calibration 폭에서 baseline 대비 이동은 −5.7202807이다. 동일 law의 group leave-out H 범위는72.1995103–73.4321050이고, 최대 endpoint B 벡터 이동은123.3682270 km/s다. scenario prior 변화와 한 group 제거가 서로 다른 민감도임을 수치로 드러낸다.
2. **ADD02 — 유한 Monte Carlo 정보량.** SMICA scan의 fixed-threshold IID tail probability Clopper–Pearson95% 구간은 [.2041683,.3185745]이다. CLASS 0/160의 같은 조건부 tail 구간은 [0,.02279175]이고 realized rank는1/161이다. CF4 H Wald coverage proxy32/32의95% 구간은 [.89111884,1]이다. 이 구간은 actual rank에 붙이는 불확실성 구간이나 physical null/coverage 인증이 아니다.
3. **ADD03 — Gaia 동시 proxy interval와 deterministic budget.** 여섯 coefficient의 Gaussian-proxy Bonferroni95% critical은2.6382573이다. box10을 더한 halfwidth는[25.0882,22.1192,25.6024,24.7657,23.0424,23.5872] µas/yr이다. box10 support는 기존1.96σ sampling 폭의2.216–2.497배다. bias support와1.96σ가 같아지는 coordinate bound는4.005–4.513 µas/yr이다. union bound와 support inequality로 고정 Gaussian law 아래 동시 rectangle을 구성할 수 있으며 실제 outcome selection·cross-source covariance의 경험적 coverage는 별도 문제다.

## 발견 및 해소 기록

**CLOSED01:** `selected_v2`에는 sensitivity02/05의 낮은 차수 quadrature 실패 flag가 보존되어 있다. exact current commit에서 `cf4/quadrature_refinement_v2/result.json`, `refinement_02.json`, `refinement_05.json`을 읽어 최신 해소를 확인했다. 원래 criterion10⁻⁶을 유지한 ΔlogL는 각각5.684341886×10⁻¹⁴,1.455191523×10⁻¹¹이다. refined H는73.3556441798,67.2919183135이다. 현재 미해결 numerical blocker로 보고하지 않는다. 소스 표는 후속 refinement를 우선 참조해야 한다.

**POTENTIAL01 — source 조사 완료, exact binding 미해결:** Alex G. Kim(2024)의 논문은 released Gaussian이 standard-normal node prior를 포함한 posterior approximation이라고 설명한다. 실제 public Stan commit `a141f8f6f72c46b653e4d324f2ecf9c5684bf15a`의 `stan_code_fixed.txt`427–430행은 cosmo_model{2,6} branch에 그 prior가 없고 else branch에만 normal(0,1)을 둔다. 이 discrepancy와 assumed λ sensitivity는 R10에서 조사·계산 완료했다. public code가 exact frozen FITS를 생성했다는 binding이 없으므로 prior 제거 또는 비제거 어느 쪽도 정답으로 인증하지 않는다. 원래 compressed-Gaussian working-law 결과는 보존하며 physical likelihood promotion은 SOURCE_BINDING_UNRESOLVED다. 부모의 일반 code audit을 기다리는 상태로 기술하지 않는다.

## 미래 달성 가능한 결과

ID의 기존 의미를 유지한다. F01–F06은 CF4/Gaia/CMB/local-history/MES/Bianchi이며, 새 F07–F09는 Union/rawQE/JWST 등이다.

| ID | 목표 | 필요한 새 입력과 최소 판정 |
|---|---|---|
| F01 | CF4/SDSS empirical selection·shared calibration law | R08 cross-law 비교 완료. 다음은 precision-target population/calibration family 확대와 method/group selection, overlap, source-motion의 product-linked held-out recovery. native solver 불필요. |
| F02 | Gaia robust frame inference | R09 disk·joint geometry 완료. 다음은 PSD angular covariance family와 empirical amplitude/scale 또는 independent cohort, outcome-selection 검증. native solver 불필요. |
| F03 | Planck/CLASS physical split-null 공동 진단 | matching beam/mask/polarization/processing/split law와 exchangeability. R11 assumed-budget ranks는 실제 law를 대체하지 않는다. native solver 불필요. |
| F04 | local boost–global history 구분 | R11 robust rank 충분조건 완료. 같은 frame/congruence에서 distinct history/source-motion을 실제 처리에 통과시킨 physical response가 필요하다. |
| F05 | physical MES/F/Q/Pi와CAS07 distance bound | actual ray/source domain·units, tensor state·positive denominator/ceiling·remainder. distance posterior나 Gaia linear support로 채워지지 않는다. |
| F06 | Bianchi family/morphology inference | 외부 native low-ell all-mT/E/B atlas, matched masks/null covariance/family-equivalence admission. 이번 범위 밖이며 repo native solver/ODE 구현 금지. |
| F07 | Union3 exact source-bound joint inference | R10 assumed-prior sensitivity 완료. frozen FITS generating prior/center/parameterization/run-code binding으로 public Stan/paper discrepancy를 해결한다. λ=1을 certified correction으로 고르지 않는다. |
| F08 | ACT raw-QE response/mean-field/bias validation | raw splits/beam/mask/filter/noiseC/response/meanfield/disconnectedbias·simulation IDs. derived kappa는 raw QE가 아니다. |
| F09 | JWST/SDSS/COSMOS/KiDS 응용 | admissible per-SN/host observations와 method/shared calibration/selection/overlap의 구체 estimand·held-out validation. row-count/retention은 completeness가 아니다. |

## 1차 문헌과 검색의 한계

- L01 [Planck 2018 results. VII. Isotropy and statistics of the CMB](https://www.aanda.org/articles/aa/full_html/2020/09/aa35201-19/aa35201-19.html), 2020: multi-statistic simulation, component-separation와 split-null 처리가 이미 선행한다. Exa publisher 검색/부분 fetch.
- L02 [Planck 2013 results. XXVII. Doppler boosting of the CMB: Eppur si muove](https://www.aanda.org/articles/aa/full_html/2014/11/aa21556-13/aa21556-13.html), 2014: aberration/modulation의 별도 velocity response. Exa 원논문 검색.
- L03 [Cosmicflows-4](https://iopscience.iop.org/article/10.3847/1538-4357/ac94d8), 2023: group/method overlap·shared calibration·FP selection normalization. SciSpace focused semantic search와 Exa publisher highlights/fetch를 함께 사용.
- L04 [The peculiar velocity field up to z∼0.05 by forward-modelling Cosmicflows-3 data](https://doi.org/10.1093/mnras/stz078), 2019: hierarchical distance/velocity와selection/calibration systematics. SciSpace abstract 확인; 수식 원문 대조는 남는다.
- L05 [Gaia Early Data Release3. The celestial reference frame (Gaia-CRF3)](https://www.aanda.org/articles/aa/full_html/2022/11/aa43483-22/aa43483-22.html), 2022: cross-match 뒤proper-motion filtering 및angular systematic errors. SciSpace focused 결과와 Exa publisher 자료를 비교했다.
- L06 [Permutation P-values Should Never Be Zero: Calculating Exact P-values When Permutations Are Randomly Drawn](https://gksmyth.github.io/pubs/PermPValuesPreprint.pdf), 2010: finite Monte Carlo rank의 선행. Exa author PDF 검색/fetch.
- L07 [Exact and Approximate Stepdown Methods for Multiple Hypothesis Testing](https://www.tandfonline.com/doi/abs/10.1198/016214504000000539), 2005: dependent resampling과 strongFWER 조건. Exa 원논문 검색.
- L08 [Comments on the Union3 “Spline-Interpolated Distance Moduli” Model](https://arxiv.org/html/2412.14181v1), Alex G.Kim, 2024: 논문의 released posterior prior 설명. public Stan과의 discrepancy 및 exact FITS binding은 R10에서 구별한다. Exa 검색과 실제 부분 원문 fetch.
- L09 [Union3 release repository](https://github.com/rubind/union3_release), 2024: compressed FITS/readme와fiducial spline perturbation 정의. Exa readme fetch.

SciSpace의 넓은 첫 질문은 중복 preferred-axis 논문과 arXiv ingestion year를2022로 표시한 항목을 반환했다. CF4/Gaia를 각각 다시 질문하고 Exa publisher와 대조하여 확인한 원전만 채택했다. Exa 일부 fetch는 author list에서 잘려 관련 검색 highlights와 targeted author/release fetch를 함께 사용했다. 후속 Union 조사는 actual public Stan과 논문 설명의 차이를 확인했고 assumedλ 계산을 완료했다. exact FITS 생성 binding은 여전히 미해결이다. 검색은 novelty 부재의 완전 증명이 아니며 모든 수식을 대조한 systematic review도 아니다. 이 범위에서 확인한 선행과 다음 검증을 정확히 기록했다.

현재 요청의 문헌·출판후보 정리는 완료되었다. production 수정·main merge·원고 제출 여부는 이 감사의 실행 결과와 구별한다. `PUBLICATION_CANDIDATES.json`이 ID별 기계 판정과 source를 보존한다.
