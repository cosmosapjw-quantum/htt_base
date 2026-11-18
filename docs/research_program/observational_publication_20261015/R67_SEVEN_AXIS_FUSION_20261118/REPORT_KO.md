# R67 통합 연구 보고: 7갈래 융합 관측·운동학 연구

작성 기준 2026-11-18. 원본 six-paper DAG P1–P6와 일곱 연구 축을 구별한다. 연구 축은 5변수 tensorized 통계(P1), low-ell CMB 형태론(P2), radio dipole anomaly(P4 companion), beyond-FLRW kinematics(P6), Bianchi/anisotropy 분류(P5), redshift/direction Hubble(P3), observer boost vs global tilt(P4)다.

## 요약과 주장 수준
- **실제 자료에서 계산 완료:** CF4의 같은 그룹에서 FP, TF, SN 거리모듈러스 차이로 공통 물리적 거리를 제거한 signed angular/radial relative-calibration 네트워크(998개 그룹, 1090 contrast rows, rank22), 그 null/민감도 검산. Gaia CRF3의 전천 161만 개 proper motion에서 l=1 E/B observer-frame 계수와 공간패치 민감도.
- **확보한 과학적 결과:** 같은 CF4 source의 상대 보정 항은 관측상 full-rank로 분해할 수 있지만, 단순 Gaussian 근사의 각도 성분 nominal p≈0.02가 group-wild resampling에서는 ≈0.15–0.18로 약해진다. 여러 쌍을 하나의 서로 의존하는 네트워크로 처리하면 16-angular group-wild p≈0.245다. 특정 물리적 anisotropy의 검출이 아니라 그룹의 공통거리와 상대 보정을 분리한 조건부 음성/검증 결과다.
- **물리적 의미:** 방향별 거리 잔차의 일부가 실제 물리적 H(z,n), shear, local bulk 대신 indicator/selection calibration에 기인할 수 있는 반례를 직접 검토할 방법. Gaia E/B 실자료는 관측자 가속도·프레임 회전을 진단하지만 cosmological omega 또는 global matter tilt가 아니다.
- **출판성:** 실제 관측 데이터와 재현 가능한 계수·검산·서로 다른 오차가 있는 methods/application 후보. 그 자체로 독립 고유의 새 Bianchi 이론, new-physics anomaly, Gaussian score 이상의 정보 우월성을 주장할 수 없다. 현재 P1–P6 제출은 모두 NOT_READY_TO_SUBMIT.

## 실행 결과 1: CF4 그룹별 상대 거리 보정

원본 table3/table4의 ID 38,053개가 순서까지 일치한다. 한 그룹에서 공통 거리 μ_g를 제거하고, 상대 지표 보정을 1 + log-distance radial polynomial degree2 + signed dipole3 + STF quadrupole5로 적합한다. Working variance는 그룹별 published errors의 제곱 합이며, 실제 upstream shared calibration covariance는 미확보다.

| 비교 | 실제 중복 그룹 | 중앙 Δμ (mag) | 상대 angular model full-sky RMS (mag) | naive χ² p (8 angular) | group-wild p (B=32768) |
|---|---:|---:|---:|---:|---:|
| FP−TF | 694 | −0.0080 | 0.0778176 | 0.019972 | 0.145076 |
| FP−SN | 202 | −0.1615 | 0.106410 | 0.018136 | 0.176051 |
| TF−SN | 286 | −0.1500 | 0.063426 | 0.621494 | 0.873539 |

세 쌍을 독립 곱하지 않았다. 998개 고유 다중방법 그룹 중 92개가 세 지표를 모두 갖는다. 1182개의 pair incidences 대신 실제 독립 차원은 1090개다. FP gauge를 둔 relative TF/SN (각11차원) 모델은 rank22/22, 정규화 설계행렬 condition5.86578. 추가 16개의 signed angular 열을 포함할 때 nominal χ² tail0.026805, 그룹 단위 wild-tail0.244896. 이는 같은 그룹에서 세 방법이 갖는 오차 상관을 제거한 것이 아니며, full within-group 2/3-dimensional profile covariance를 유지한 **선언된 independent-method-error working model**에만 정확하다.

해석 구별:
1. 각 출력의 dipole/STF 계수, RMS와 p값은 관측 처리에 의존한다. Calibration angular RMS는 검출 크기나 실제 total calibration error의 측정이 아니다.
2. 고정 z에서 ∆lnH_app=−(ln10/5)∆μ, 따라서 차등 방법 오차가 directional H 추론에 전달될 수 있다. 이 relation을 실제 H_phys=Θ/3의 측정으로 승격하지 않는다.
3. TF/FP/SN 측정은 source population과 survey footprints가 다르며, 그 catalog 자체가 원래 method registration을 수행했다. Group-wild null은 global registration uncertainty, LSS/shared selection을 포함하지 않는다. 후속엔 실제 source-level selection/joint covariance 또는 injection coverage를 요구한다.

FP−TF radial-only polynomial order0/1/2/3의 별도 group-wild p는0.07125/0.13665/0.13763/0.15081. Working nominal χ²는 이에 비해 훨씬 작아진다. |standardized radial residual|>3인 4개 그룹을 후행 제외한 sensitivity p=0.13421, 주 분석에서 제외하지 않았다. Primary B2048 이후 B8192, B32768 실험을 별도 보존했고 마지막 B32768을 보고한다. 이 반복은 모델 부적합을 고치지 않으며 Monte Carlo 표본 오차만 줄인다.

## 실행 결과 2: Gaia-CRF3 observer-frame E/B field

로컬 Gaia FITS의 실제 PMRA* / PMDEC와 2×2 per-source error+correlation을 사용해 전천 l=1 electric/glide 3 + magnetic/rotation 3을 fit. ICRS, μas/year. Full N=1,614,173, quality (RUWE<1.4, visibility periods>=8, not duplicated) N=1,580,645. Quality:
- E = (−0.19502, −5.13629, −2.13875) μas/year, norm=5.56720, 방향 ICRS RA≈267.83°, Dec≈−22.59°.
- B = (3.60819,1.71990,−1.55664) μas/year, norm=4.28954.
- Rank6/6, Fisher condition1.978; per-source statistical formal errors0.265–0.304 μas/year, but source-independent law is incomplete.
- 192 spatial-patch cluster sandwich σ≈(0.742,0.735,0.755,0.733,0.620,0.985) μas/year. Not calibrated official large-angle systematic posterior.
- North-only quality subset E norm4.516/B8.479, south E8.231/B6.710: pronounced geographic sensitivity.

Observer-frame acceleration (E l1) and possible frame spin/systematics (B l1) are familiar phenomena; this exercise does not newly detect acceleration or cosmological vorticity. Makarov/Heinesen/Schücker 2026 already fit Gaia l2 VSH in Bianchi I, finding the predicted redshift rise not robust. A real beyond-FLRW kinematic inference needs source redshifts, frame matching, l2 optical response, AGN/scan priors and probably independent VLBA/ICRF verification. Exact Gaia coefficients and joint covariance diagnostics in RESULTS/GAIA_EB_FRAME.json.

## 10-step research/coding trace
The ten theoretical phases R1–R10, including definitions, primary literature, physical-claim audit, four different fusion routes, proof of same-group projection, counterexamples, actual numerical test, scientific verdict, source-typed joint Fisher and stop conditions are written in THEORY_10_STAGES.md. The corresponding C1–C10 implementation status, commands, tests and missing independent-review tool are in CODING_10_STAGES.md. Scope is one integrated portfolio, not seven new independent 10-cycle projects.

Code paths:
- scripts/r67/fusion.py and run_r67_fusion.py: source group quotient, three pairs, full 22D calibration network, group-bootstrap.
- scripts/r67/sensitivity.py: radial polynomial and large-residual sensitivity.
- scripts/r67/gaia_frame.py: actual Gaia vector-spherical-harmonic E/B fit and spatial-systematic proxy.
- scripts/r67/likelihood_contract.py: typed physical parameter/frame/epoch, independent-source/cross-covariance guard, nuisance Schur.
- scripts/r67/plot_r67.py: R67_FUSION_DIAGNOSTICS.png and PDF.
- tests/test_r67_fusion.py, test_r67_gaia_frame.py, test_r67_likelihood_contract.py: 15 synthetic/source-integrity/semantic tests PASS. Independent Wolfram exact shared-source projection/difference covariance identity passed. These tests do not certify unknown astrophysical selection or transfer.

## Fused publication candidates, ranked
1. **Source-matched directional distance inference under method selection (P1+P3+P6, supported)**: add the observed same-group method quotient to the existing R64 source-level H likelihood with **correct full cross-covariance**, compare conditioned angular H_D/shear-like summaries and nuisance sensitivity, one fixed heldout. Existing data are sufficient to design this; catalog-wide shared calibration/selection may need independent release or direct source-forward modelling. The present result is a publishable methods/result component if comparator shows a real coverage/error-model benefit.
2. **Observer-frame dipoles and nonradial kinematics (P4+dipole+P6, exploratory)**: Gaia/ICRF E/B and existing radio count/CMB observer dipole can jointly constrain distinct frame parameters only after exact source and epoch maps; E dipole is derivative of boost not boost itself. Do not combine Gaussian summaries on shared sky/selection without cross law. VLBA713 exists locally, may improve independent error budgeting.
3. **Radiation stress → anisotropic cosmography/Bianchi compatibility (P2+P5+P6, conditional)**: actual Commander signed stress proxy and R62 shape classes are available, but cannot identify Bianchi family or present matter shear without validated photon/metric/polarized transfer. Choose restricted I/V family with declared pressure, tilt/normal congruence, Jacobi response and prior; perform family recovery with actual matched null. No automatic solver build.
4. **Lensing consistency as separate physical check (P1+P3+P5+P6, deferred)**: HSC Y3 and KiDS data are present; cosmic weak-lensing shear and local u-congruence shear are not interchangeable. Requires explicit optical transfer and cross-tracer covariance; download more mocks only if precision/coverage criterion proves local assets insufficient.

## Conditional additional data only
See CONDITIONAL_DATA_REGISTRY.json. Nothing is downloaded as a side effect of this update. DESI DR1 98,292-object final FP PV release is useful only after an official, source-matched file is public and the existing Fuji/CF4/SDSS selection test is insufficient; PR4 Commander bare T MC0200–0299 after product-unit+beam and exchangeability qualification; RACS RMS missing coverage after 267 candidate tiles are actually validated; quasar redshift/jet motion ancillary only when Gaia l2 transfer is admitted; kSZ remote dipole windows/bias only when velocity response is matched. Additional HSC mock files are not 1404 independent cosmic skies by filename count.

## Stop conditions and honesty
- Same-group relative method angular null under working law must not be reported as physical isotropy proof or calibrator detection.
- Existing x,Q,Pi,F,G_F represent dependent views of an admitted likelihood. No naive addition of p-values or odds.
- P1–P6 original 42 science gates and original paper acceptances stay unchanged. The new conditional data nodes are dormant triggers, not automatic tasks.
- Current publication status: NOT_READY_TO_SUBMIT, significant joint physical discovery unresolved, request for 10-stage feasible research and actual code implemented to declared scope.
- Native host subagent creation was unavailable: NOT_RUN. Any CLI fresh-context review is reported with its actual execution receipt rather than invented identity.

## Review/correction after first candidate
Fresh independent CLI reviewer (read-only) flagged deficient-rank nuisance QR, mismatch-tolerant shared covariance, a negative RMS label, an insufficient baseline paper-preservation check and one CF4 table4 SHA transcription error. These were repaired, targeted regression tests extended to 19 PASS and the primary 32,768-draw CF4 data execution reproduced the same physical/statistical estimates; only the nonnegative derived lnH RMS and code guards changed. Review originally returned NEEDS_REPAIR, and final targeted closure was performed by the parent rather than a second independent reviewer. Scoped C0 methods/data product, **NOT_READY_TO_SUBMIT**. See REVIEW/review_closure.json.
