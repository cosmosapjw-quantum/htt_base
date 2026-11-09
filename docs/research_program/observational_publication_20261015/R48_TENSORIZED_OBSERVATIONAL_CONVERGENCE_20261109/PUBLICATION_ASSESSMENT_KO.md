# R48 출판 가능성 평가 및 연구 주장 경계

기준일: 2026-11-09  
판정 범위: GitHub cosmosapjw-quantum/htt_base의 현재 연구선, 선택된 과거 PR/branch, 2026-10-26 내부 이론보고서, Library 자료와 확인된 선행문헌.

## 1. 심사 판정

| 산출물 | 판정 | 이유 |
|---|---|---|
| 관측 발견 논문 | **HOLD** | R42 Cobaya receipt ESS=53, ESS gate 실패; R42 SBC 시나리오 전부 미보정; Planck carrier는 743-byte low-ell E/B 요약이지 원시 지도 또는 전체 a_lm source-lock이 아님; Bianchi transfer adapter 미구현; 일부 응답 스케일 상수 hard-coded |
| 방법론 논문 | **조건부 진행** | 식별가능 함수량, posterior information loss, target-specific compression, source-/frame-aware tensor response를 연결하는 연구 후보가 있으나 실제 자료에서 보존 정보와 보정 성능을 입증해야 함 |
| 내부 이론 결과 | **범위 제한 PASS** | 2026-10-26 다섯 루프 A–E는 독립 심사에서 PASS_SCOPED_AFTER_TARGETED_REPAIRS를 받았지만, 해당 심사문서가 관측 검증·native Bianchi transfer·family identification은 아니라고 명시 |
| Bianchi-I 지오데식 지도 | **조건부 물리 템플릿** | 등방 last-scattering, homogeneous Bianchi-I, collisionless propagation의 명시적 한계에서만 사용. 현재 shear가 아니라 emission-to-observer integrated shape를 추적 |

## 2. R42–R47 연구선에 대한 주요 심사 소견

### 강점

1. R43–R46은 관측량의 식별가능 함수량, Bayes-factor 목적 통계량의 충분성, finite-model posterior information loss, target-specific posterior compression을 순차적으로 다룬다.
2. R47은 solver-free Bianchi-I 지오데식 응답을 관측 CMB 전체의 대체물로 과장하지 않고 temperature-only conditional model로 제한한다.
3. 5변수 T=(x,Q,Pi,F,G_F)를 하나의 공동 posterior/compatibility push-forward로 두고 서로 다른 물리량을 독립 likelihood factor처럼 합산하지 않는 원칙은 유지해야 한다.
4. 미식별 방향을 결과로 보존하는 R43의 설계는 중요한 통계적 안전장치다.

### 출판을 막는 결함

1. **Cobaya 수렴:** R42 receipt의 ESS=53, ess_passed=false는 production inference가 아니다. 과거 receipt에서 chain 재사용 경로가 sampler 미실행 상태에서 diagnostics를 fallback/hard-code할 여지가 있으므로 receipt producer부터 감사해야 한다.
2. **SBC 실패:** R42가 표시한 다섯 모델 시나리오의 coverage/SBC는 is_calibrated=false다. 보정된 posterior, Bayes factor, sigma 제한으로 해석해서는 안 된다.
3. **관측 입력 identity:** 743-byte observed_lowell_EB.npz는 원시 CMB map, 전체 a_lm, map transfer, mask/beam/noise covariance manifest와 동일하지 않다. C_ell Blackwell–Rao likelihood도 위상·multipole morphology 우도를 대신하지 않는다.
4. **응답 hard-coding 충돌:** R42 구현 감사 문서는 수정 완료를 주장하지만 full_observable_x_bundle.py에는 C_NVSS=3.6625, C_Quaia=3.3200, glide_scale=0.92, shear_scale=0.18 등의 source-bound가 아닌 기본 상수가 남아 있다. 문서의 완료 주장보다 실제 source가 우선이다.
5. **Bianchi adapter:** BianchiTransferAdapter의 native atlas/external transfer 경로는 NotImplementedError를 내므로 실행 가능한 Bianchi likelihood로 취급할 수 없다.
6. **물리적 frame/epoch 문제:** beta 파라미터의 프레임 합성, sigma/omega/A의 epoch, radiation congruence와 matter congruence, CMB last-scattering과 저적색편이 사이의 상태전이를 명시해야 한다. 단순 벡터합이나 모든 관측에 동일한 시점의 상태를 대입하면 안 된다.
7. **공분산/중복:** 서로 다른 probe의 독립성을 증명하지 않고 log-likelihood를 더하면 안 된다. 한 CMB sky의 SMICA/NPIPE 재처리본은 독립 관측이 아니다. source overlap, shared calibration, common LSS, mask and selection coupling을 점검해야 한다.

## 3. 과거 이론 루프의 재활용

2026-10-26 HTT_FIVE_THEORY_LOOPS.pdf의 A–E는 다음을 제공한다.

- A: bolometric brightness moments와 4차 각도 모멘트를 포함한 5차원 양의 radiative-shear response 및 조건부 오차 역산.
- B: 관측 dipole와 intrinsic radiation dipole의 단순 합만으로는 boost를 분리하지 못하며, 2차 quadrupole closure와 독립 aberration/modulation 채널이 필요하다는 관계.
- C: radial redshift와 transverse proper-motion의 공변 응답. B1 proper-motion 성분은 기준 프레임 spin과 퇴화할 수 있음.
- D: Bianchi 구조상수, Jacobi, Gauss–Codazzi와 spatial Ricci를 사용한 동차 기하학 호환성. 같은 scalar curvature가 같은 spatial Ricci tensor를 뜻하지 않음.
- E: 방향성 optical Hubble jet, finite-redshift distance coefficient, curvature-history 조합. H_dir(0,n)=c[Theta/3+sigma_ab n^a n^b-A_a n^a]라는 국소 계수와 finite-z estimand를 구별.

독립 심사는 이 다섯 결과를 **조건부 이론 결과로만** 통과시켰다. 관측 Hubble 이상, 실제 intrinsic dipole, cosmic vorticity, Bianchi family 관측 판정은 아니다.

## 4. 선행연구와의 경계

- **CMB morphology/statistical anisotropy:** multipole vectors, power tensor, BipoSH, cut-sky likelihood 및 Planck low-ell 검정은 이미 확립된 경쟁 방법이다. HTT가 이 통계량을 tensor container에 담는다는 사실만으로 novelty가 생기지 않는다.
- **local boost vs intrinsic dipole:** Nadolny et al. (JCAP 2021, arXiv:2106.05284)는 위치·flux 외에 redshift와 angular size를 이용해 관측자 속도와 intrinsic source anisotropy를 분리하는 전략을 제시했다. 따라서 단순한 redshift tomography만을 새 기여라 주장하면 안 된다.
- **directional Hubble:** Heinesen (2021)의 일반 luminosity-distance Hubble law multipole, Maartens et al. (JCAP 2024, arXiv:2312.09875)의 covariant observer boost 변환, Boubel et al. (arXiv:2412.14607)의 CF4 방향성 H0 분석, Sarma et al. (JCAP 2026) local-structure cosmography가 직접 경쟁/선행연구다.
- **compression:** MOPED/score compression(Alsing & Wandelt 2018) 및 nuisance-hardened compression(Alsing & Wandelt 2019, arXiv:1903.01473)은 Fisher 보존/계통 nuisance 제거의 강한 선행이다. HTT의 다섯 출력이나 compression identity 자체는 새 통계 정리로 포장하지 않는다.
- **Bianchi:** Bianchi CMB temperature/polarization transfer 및 model comparison은 독립적인 기존 축이다. solver-free BI geodesic response는 그 일부의 명시적 제한 모형이지 Bianchi 전체 계열을 대표하지 않는다.

참고 링크:
- BipoSH: https://arxiv.org/abs/1004.1260
- Multipole-vector anomaly analysis: https://arxiv.org/abs/0509502
- Kinematic/intrinsic dipole separation: https://arxiv.org/abs/2106.05284
- Observer-dependent covariant cosmography: https://arxiv.org/abs/2312.09875
- Directional H0 test with CF4: https://arxiv.org/abs/2412.14607
- Nuisance-hardened compression: https://arxiv.org/abs/1903.01473
- MOPED/score compression: https://arxiv.org/abs/1801.01497
- Local-structure covariant cosmography: https://doi.org/10.1088/1475-7516/2026/04/069

## 5. 검증할 novelty 가설

> 물리 상태 theta=(sigma_ab,omega_a,A_a,beta_RM,beta_MO)를 관측자·물질·복사 프레임과 epoch에 맞게 정의하고, CMB harmonic response, source-count point process, astrometric vector spherical harmonics, luminosity-distance response를 source-bound operator로 연결한다. 그 joint posterior에서 HTT의 T=(x,Q,Pi,F,G_F)를 유도하고, 사전에 고정한 물리 estimand에 대한 posterior information-loss를 정량화한다. 이를 full-data, BipoSH, multipole-vector/power-tensor, score/MOPED, nuisance-hardened compression과 matched mocks에서 적대적으로 비교한다.

이 가설의 기여는 세 조건이 함께 입증될 때만 유효하다.

1. **physical identifiability:** 기하/프레임/selection nuisance를 제거한 후에도 미리 지정한 물리 함수량이 식별된다.
2. **information retention:** HTT readout의 target-specific posterior KL loss가 경쟁 압축보다 작거나 허용 상한 아래에 있고 coverage를 해치지 않는다.
3. **calibrated advantage:** model-matched SBC, null FPR, posterior predictive checks, held-out cross-tracer prediction에서 사전에 정한 성능 문턱을 통과한다.

## 6. 이번 턴에서 실제 완료한 범위

- GitHub PR metadata 568건, branch metadata 307건을 페이지 전수 열거.
- 최신 R41–R47 stacked research line, 주요 head/parent SHA, R47 DAG와 data intake manifest를 확인.
- R42의 구현·Cobaya·SBC·data identity 문제를 source-level 대조.
- 2026-10-26 internal theory report와 independent review를 Library에서 직접 읽고 A–E의 reuse boundary를 정리.
- R47 Bianchi-I exact geodesic map의 small-anisotropy expansion sky monopole를 Wolfram Language로 symbolic 확인. B*=epsilon diag(b1,b2,-b1-b2)의 2차 sky mean은 -2 tr(B^2)/15이며, 온도 monopole 정규화와 anisotropic multipoles를 분리해야 함.
- Planck PR4/NPIPE, Quaia, Pantheon+, Gaia 및 관련 선행논문 원 배포처를 확인.

**미완료:** local source test, 실제 raw data download/hash, Cobaya production chain, matched E2E/SBC, observed anomaly estimate, native Bianchi-V/VIIh transfer. 이번 R48 문서는 위 항목을 local agent가 수행할 명확한 계약이다.
