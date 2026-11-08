# HTT R42: 최신 Tensor 5변수 프레임워크의 출판 가능성 및 경쟁 이론 심사

**기준일:** 2026-11-08 (Asia/Seoul)  
**기준 저장소:** `cosmosapjw-quantum/htt_base`  
**기준 R41 HEAD:** `0439ae8e4870b23abfcdb9499c4c214daf12314b`  
**R41 기반:** `research/r41-publication-gate-20261107`  
**R42 브랜치:** `research/r42-fivevar-competitive-benchmark-20261108`  
**검토 방식:** GitHub tree/blob/PR metadata/static source review 및 외부 원전 문헌 확인. Local dataset bytes, local SHA, pytest, Cobaya sampling, FITS replay는 이번 세션에서 실행하지 않음.

## 1. 심사 결론

**현재 관측적 발견 논문: HOLD. 방법론 논문: 조건부 CONTINUE.**

R42의 주된 비교 대상은 scalar 5변수 표현이 아니다. 비교의 중심은 현재 저장소에 구현된 최신 tensorized five-variable state
[
mathfrak T=(x,Q,Pi,F,G_F)
]
가 기존의 경쟁 이론 및 관측·추론 방법과 비교해 어떤 물리적 정보를 더 보존하고, 어떤 물리량을 추가로 식별하거나 예측하며, 어떤 조건에서 더 잘 보정된(out-of-sample calibrated) 추론을 제공하는가이다. (x_C) scalar ablation은 필요할 때만 보조 진단으로 유지하고, 논문의 주된 novelty 또는 경쟁 기준으로 삼지 않는다.

핵심적인 범주 구분도 고정한다. ((x,Q,Pi,F,G_F))는 독립적인 다섯 likelihood parameter나 다섯 독립 확률인자가 아니다. 공통 posterior/compatibility region 및 source-conditioned physical functional map에서 파생되는 다섯 종류의 결과다. 따라서 이 다섯 출력에 대해 별도의 독립 likelihood를 곱하거나, 서로 다른 물리 이론과 동일한 차원의 parameter vector처럼 직접 BIC 비교해서는 안 된다. 물리적 생성모형(generative theory)과 추론·요약 표현(inference/readout method)을 두 층으로 분리해 경쟁시킨다.

R41의 수치 결과 (R)-hat, ESS, (Deltachi^2), BIC, LOOCV, Fisher gain, SBC/PPC 및 데이터 검증 주장은 이번 GitHub-only 검토에서 재실행되지 않았다. 일부 값은 코드의 실행 경로와 상충하므로 전부 `QUARANTINED_NOT_REPRODUCED`로 유지한다. 이는 숫자가 반드시 틀렸다는 뜻이 아니라, 재현과 올바른 likelihood에서 다시 성립할 때까지 과학적 claim으로 사용할 수 없다는 뜻이다.

## 2. 현재 5변수 체계의 올바른 의미

R39 `htt/src/common/htt_five_variable_state.py`와 `full_observable_x_bundle.py`에서 확인한 의미는 다음과 같다.

| 요소 | 의미 | 필요한 과학적 보증 |
|---|---|---|
| (x) | 직접·정규화·혼합된 kinematical functionals와 관측 carrier를 담는 sample-wise/set-valued tensor bundle. (sigma_{ab},omega_a,A_a,beta_RM,beta_MO), (a_{ell m}^{T,E,B}), STF multipoles, VSH, count/distance multipoles 등의 typed observable space | 각 functional의 rank, parity, (SO(3)/O(3)) representation, units, frame, source/window/transfer, covariance와 estimator lineage |
| (Q) | anchor, gauge, margin, availability를 표현하는 물리적 anchor/uncertainty bodies | bound와 gauge margin은 CAS/정리/관측 calibration/명시적 prior 중 출처가 있어야 함. 미확인 anchor는 UNAVAILABLE로 보존 |
| (Pi) | posterior 또는 matched null law에 조건부인 exceedance/tail surface | null은 관측별 noise, mask, selection, covariance, foreground 및 nuisance를 반영한 matched ensemble이어야 함 |
| (F) | 물리적 uncertainty/compatibility image의 directional support (h_I(u)), anchor support (h_A(u)), occupancy (F(u)) | 방향 구면 quadrature의 균일성·수렴성, anchor의 의미, 분모 0 처리, 표본/credible-set 정의 |
| (G_F) | redshift/distance shell별 tensor-functional path와 full cross-shell covariance/depth contrast | 물리적으로 유도되거나 data-calibrated된 transport/kernel, 실제 shell selection, 전체 cross-shell covariance |

다섯 요소는 (T = pushforward[posterior(theta_K, psi, eta | d, model_M)])와 같은 공통 추론 결과의 push-forward/readout로 정의한다. 여기서 (theta_K)는 17차원 kinematic state chart이고, (mathfrak T)는 서로 다른 다섯 출력 기능이다. 두 종류의 “five variables”를 혼동하지 않는다.

## 3. 최신 코드에서 확인한 실질적 결함: 프레임워크 전체의 반증과 구분

### 3.1 (x): 관측 carrier 생성 경로

`full_observable_x_bundle.py`에는 count dipole의 (3.75,3.40), Gaia VSH response의 (0.92,0.18), CMB quadrupole의 고정 (tau) 계수 및 (sigma/H) scale, (B)-mode zero prediction 등 출처·적분·선택함수로부터 유도되지 않은 수치가 있다. 이들은 생산 likelihood의 물리적 forward response로 사용하면 안 된다. 각각 source-specific observation operator에서 유도·계산하거나 `UNAVAILABLE/TRANSFER_CONDITIONAL`로 유지해야 한다. 고정 숫자 사용의 발견은 tensorized state 전체가 잘못됐다는 반증이 아니라 현재 해당 carrier adapter가 물리적으로 닫히지 않았다는 구현/이론 연결 결함이다.

### 3.2 (Q): anchor/gauge

`construct_r39_five_variable_state`는 일부 anchor의 `norm_bound=1e-4`, `gauge_margin=1e-5` 등을 하드코딩한다. 수치적 anchor가 별도 이론·관측 근거 없이 도입됐다면 삭제하거나 `UNAVAILABLE` / `PRIOR_CONDITIONAL`로 분류해야 한다. (A_a) 및 frame-relative velocity anchor가 현재 unavailable로 표시된 부분은 정직하게 유지하고, geodesic premise (A_a=0)를 관측 anchor라고 오인하지 않는다.

### 3.3 (Pi): null law

현재 구현의 `MIO_DIAGNOSTIC_NULL`은 임의 seed와 (sigma=10^{-4})인 Gaussian으로 생성된다. 이것은 source-conditioned matched null이 아니다. 실제 CMB FFP/End-to-End MC, catalogue randoms, selection-preserving resampling, Gaia scan-law/systematic mocks 등 각 관측별 null 생성 경로로 교체해야 한다. 임의 null은 개발용 fixture로 격리하고 경험적 significance나 calibrated FPR에 사용하지 않는다.

### 3.4 (F): directional support

현재 50개 방향은 (phi,theta)를 같은 길이로 단순 대응해 생성하므로 구면 균일 quadrature가 보장되지 않는다. 결정론적 equal-area/Fibonacci 또는 HEALPix 방향 집합, 회전-equivariance test, 방향 수 증가에 따른 support convergence, (h_A(u)=0) 처리, MCMC tail/credible-set sampling uncertainty를 구현한다.

### 3.5 (G_F): depth path

현재 구현은 세 저적색편이 shell을 고정하고 (sigma(z)=sigma_0/(1+z)), identity transport kernel을 사용한다. 이 선택은 일반적인 Einstein/Bianchi dynamics에서 도출된 진화식이 아니며, 실제 깊이별 관측을 반영한 것도 아니다. 특정 이론의 해에서 유도한 transport와 phenomenological fit를 분리하고, shell-specific data/selection 및 full cross-shell covariance를 이용해야 한다. posterior samples에 동일한 (sigma_0) 배율만 곱해 계산한 공분산을 관측 간 독립 정보로 해석하지 않는다.

## 4. 경쟁 연구의 두 층 구조

### A. 물리적 생성모형 경쟁군

1. **FLRW + local LSS/peculiar-velocity baseline:** (Lambda)CDM/FLRW 배경, linear-theory velocity reconstruction, local structure/cosmic variance.
2. **Pure local observer boost:** exact Lorentz transformation, Doppler modulation, aberration, flux/redshift selection response. 모든 probe에 공통된 observer-frame map을 적용.
3. **Homogeneous anisotropic/Bianchi models:** Bianchi I 및 관측적으로 관련된 Bianchi V/VII(_h), LRS/Class A/Class B 제약. (n^{ab}a_b=0), tetrad/frame 및 field equations를 지키고 CMB temperature/polarization transfer를 포함.
4. **Tilted multi-fluid / dipole cosmology:** matter-radiation relative velocity와 그 동역학을 명시적으로 모델링. redshift evolution은 임의의 선형 interpolation이 아니라 Einstein/matter equations 또는 독립적으로 정당화된 phenomenology에서 유도.
5. **General covariant cosmography:** Kristian–Sachs/Heinesen 계열의 observer-dependent Hubble/deceleration multipoles. 특정 global metric을 가정하지 않는 강력한 경쟁 기준.
6. **Inhomogeneous/local-flow models:** local bulk-flow, density/tidal field 및 LTB-like radial structure가 저적색편이 신호를 설명하는 경쟁 가설.
7. **Phenomenological multipole + survey-systematics model:** dipole/quadrupole 및 dust, calibration, selection, scan-law template를 포함한 필수 nuisance baseline.

### B. 관측량 표현·추론 방법 경쟁군

1. full (a_{ell m}) harmonic likelihood / BipoSH covariance estimators;
2. multipole vectors, power/alignment tensors 및 low-(ell) morphology summaries;
3. multi-tracer count dipole + redshift/flux/angular-size response estimators;
4. Gaia VSH (E_1/B_1/E_2) 및 source-level astrometric likelihood;
5. hierarchical peculiar-velocity / Gaussian-process / field-level reconstruction;
6. score compression 및 nuisance-hardened compression;
7. conventional posterior mean/covariance/credible regions, convex support/depth-based summaries;
8. HTT tensor five-variable push-forward ((x,Q,Pi,F,G_F)).

HTT five-variable는 1차적으로 generative theory가 아니라 inference/readout architecture다. 따라서 Bianchi 또는 dipole cosmology의 대체 metric이라고 가정하지 않는다. 여러 생성모형에서 같은 source-conditioned posterior를 만들고, 서로 다른 readout가 물리적 식별성·calibration·predictive utility를 얼마나 보존하는지 비교한다. A와 B를 교차 조합해 물리적 설명력과 요약법의 기여를 따로 측정한다.

## 5. 우선 문헌과 novelty 경계

- Bianchi CMB all-mode likelihood: Saadeh et al., *How Isotropic is the Universe?* (2016), PRL 117 131302, https://doi.org/10.1103/PhysRevLett.117.131302 ; *A framework for testing isotropy with the CMB*, https://arxiv.org/abs/1604.01024 .
- Bianchi polarized transfer: Pontzen & Challinor, https://arxiv.org/abs/0706.2075 . External ABSolve 등 기존 구현의 존재도 반영한다. “Bianchi polarized transfer를 처음 구현했다”는 claim 금지.
- Low-(ell) morphology: Copi, Huterer & Starkman, PRD 70 043515 (2004), https://doi.org/10.1103/PhysRevD.70.043515 ; Hajian & Souradeep BipoSH formalism, https://arxiv.org/abs/astro-ph/0501001 .
- General anisotropic luminosity-distance multipoles: Heinesen, https://arxiv.org/abs/2010.06534 .
- Observer-dependent covariant Hubble multipoles and boost transformation: Maartens et al. (2024), JCAP 09 070, https://doi.org/10.1088/1475-7516/2024/09/070 .
- SN Hubble quadrupole: Dhawan et al. (2022), MNRAS, https://doi.org/10.1093/mnras/stac3812 ; Cowell et al., https://academic.oup.com/mnras/article/526/1/1482/7273134 .
- Local velocity vs intrinsic dipole: Nadolny et al. (2021), JCAP 11 009, https://doi.org/10.1088/1475-7516/2021/11/009 ; their method explicitly uses redshift and angular size in addition to flux/position.
- Redshift-bin kinematic dipole response: von Hausegger & Dalang (2025), PRD 111 123547, https://doi.org/10.1103/PhysRevD.111.123547 .
- Nuisance-hardened score compression: Alsing & Wandelt (2019), MNRAS 488 5093, https://doi.org/10.1093/mnras/stz1900 .
- 2026 competing local-anisotropy results: Zhou & Zhao, *Revisiting cosmic anisotropy with Pantheon+* (published 19 Oct 2026), https://doi.org/10.1140/epjc/s10052-026-16465-7 ; CF4/Pantheon+ analysis finding no evidence for local (H_0) anisotropy under radial peculiar-velocity modeling, MNRAS 546 (2026), https://doi.org/10.1093/mnras/staf2048 ; Salzano et al. (Sep 2026), https://doi.org/10.1016/j.dark.2026.102382 .

**Novelty statement must be earned:** a candidate claim is the *source-conditioned, physically typed, posterior-pushforward architecture that preserves tensor functional images, anchor/gauge uncertainty bodies, law-conditional exceedance surfaces, directional support and full-covariance depth paths, and demonstrates measurable calibrated/predictive gains over established model-specific and summary-statistic competitors*. This is not yet established. Convex support functions, multivariate depth, BipoSH, covariant multipoles, VSH and nuisance-hardened compression each have prior art. Individual ingredients are not to be claimed as inventions without a separate priority search and theorem.

## 6. 적대적 벤치마크의 핵심 acceptance

- Compare the **latest tensor five-variable state against competing theories and methods**, not a scalar five-variable version. (x_C) ablation is supplementary only.
- Every competing generative model receives the same common observed data and exact source rows wherever the corresponding forward theory applies. If a method cannot model a probe, declare the missing channel and compare on a predeclared common subset; do not silently impute a response.
- Same map/catalogue release, row keys/order, mask, beam, selection, redshift/flux cuts, covariance, calibration and nuisance handling. Cross-probe covariance must be estimated or the joint analysis must be explicitly conditional/blocked.
- Compare physical target functionals on the identifiable quotient after nuisance projection. Use a declared physical/prior metric; do not compare raw parameter ranks across different parameterizations.
- Evaluate injection/coverage, SBC, FPR and power under matched null/alternative ensembles; include local-structure, foreground, selection, scan-law, calibration and tracer-evolution adversarial injections.
- True held-out refit by probe and by redshift shell; use ELPD/appropriate multivariate proper scores. No use of full-data MAP on held-out folds.
- Fit each model separately. BIC requires a valid maximized likelihood and defensible asymptotics; Bayes factors require normalized proper priors and an actual evidence computation. A Cobaya MCMC chain alone is not evidence.
- Report failures of the competitors fairly as well as failures of HTT. HTT must be allowed to lose. A negative benchmark is a valid scientific result.

## 7. Six independent theory loops: current disposition

| Loop | Target question | Current supported core | Main unresolved work |
|---|---|---|---|
| L1 low-(ell) morphology | Which (T/E/B), (a_{ell m}), STF multipoles, multipole-vector/BipoSH functionals map to a physical source-conditioned observable? | Morphology statistics and mask sensitivity are established; deterministic templates and stochastic covariance must remain separate | Real frequency/split/map likelihood, mask/beam/bandpass, matched MC and physical transfer |
| L2 dipole anomaly | Can radiation dipole, observer boost, intrinsic radiation dipole and matter-count dipoles be separated? | Boost/aberration, multi-tracer and redshift tomography are established methods | Source-specific redshift/flux/size/spectral responses, local LSS and cross-catalogue covariance |
| L3 kinematic measurement | Which components of (	heta_K=(sigma_{ab},omega_a,A_a,beta_RM,beta_MO)) are identifiable? | 1+3 irreducible sectors and leading local optical map; Gaia spin/glide/shear are distinct observables | Source-level operator Jacobians, external frame-spin anchors, exact boosts/Wigner rotation, finite-(z) transport |
| L4 anisotropy classification | Which kinematical equivalence classes are compatible with Class A/B and Bianchi families? | Lie-algebra/Jacobi and tilted-frame constraints can classify compatibility | Integrate dynamics and transfer; compare all relevant family alternatives; compatibility is not family identification |
| L5 directional Hubble | What is (H(z,hat n)) and what is due to observer boost, shear, acceleration, LSS? | Local leading term and general multipole cosmography are prior art | Redshift-domain validity, observer/matter-frame transformation, exact distance likelihood and local-flow controls |
| L6 local boost vs global tilt | Is a common local Lorentz map sufficient, or is a dynamical relative congruence needed? | Nadolny multi-observable separation and 2025 redshift tomography are strong baselines | Actual redshift tomography with selection, angular size/flux/spectra, LSS covariance and physical tilt evolution |

### Correct theoretical caveat

At leading local optical order, the sourceward-direction convention may give
[
H_{mathrm{loc}}(hat n)=H+sigma_{ab}n^a n^b-(A_a n^a)/c,
]
with sign depending on photon/direction convention. The antisymmetric contraction (n^a n^bomega_{ab}=0) vanishes at this order. This does **not** prove vorticity is absent from all higher-order scalar distance coefficients. Derivatives, congruence transport and null propagation must be derived order by order. Gaia (B_1) catalogue spin is degenerate with rigid reference-frame rotation unless externally anchored; it is not automatically a direct measurement of cosmic vorticity.

## 8. Publication claim ceiling and immediate decision

- Empirical/detection paper: **HOLD** until actual source replay, physically derived operators, full sampler diagnostics and competitor benchmarks are produced.
- Methods paper: **CONDITIONALLY VIABLE**, centered on the two-layer (generative model × tensor five-variable readout) benchmark and physical-functional identifiability.
- Bianchi-family identification: **UNRESOLVED**, not categorically impossible. A native BASS solver is a provenance/product choice, not a universal scientific prerequisite if a validated external solver or analytic transfer is available. Any external transfer must be labelled external/transfer-conditional and independently benchmarked.
- Current R41 posterior, BIC, LOOCV, Fisher/SBC and source verification outputs remain quarantined pending replay.
- A valid scientific claim must not be downgraded solely because the harness has an overbroad text gate or demands a particular implementation origin. Conversely, passing a gate never proves a claim.

## 9. Review boundary and provenance

R41 commit `0439ae8e4870b23abfcdb9499c4c214daf12314b` is the immediate R42 parent. R41 PR #565 remains open/draft and targets R39, while R42 is a stacked child PR targeting the R41 research branch. A REST enumeration in this review returned 561 PR records (unique PR numbers 2–564); this was a metadata census, not full line-by-line reading of all diffs. R39's legacy audit says it reviewed 32 selected PR bodies and 17 full diffs. This session additionally inspected the current R38/R39/R40/R41 key dossiers and source paths. Do not claim a complete line-by-line audit of all 561 PRs; R42's local phase must complete a relevance-indexed source/diff audit and record per-PR coverage.

R42 branch changes are documentation/specification only. No production code was changed and no local experiment was run in this session.
