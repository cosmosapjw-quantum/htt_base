# MES R4 — 관측 source/기준틀 계약 조사

작성: 2026-09-27 KST. 역할: 독립 문헌/관측 입력 조사. R3 보고서와 Astra v4.0.0 PROJECT_INSTRUCTIONS 및 MODEL_ROUTING을 읽었다. 생산 코드나 저장소 변경 없음.

## 결론

문헌에서 얻은 μas/yr 수치로 실제 관측 오차의 규모를 고정할 수 있다. 그러나 이를 우주론적 shear/와도 또는 모든 광원의 미분 remainder를 제한하는 deterministic hard ball로 승격할 근거는 아직 없다. Gaia-CRF3의 무회전 조건은 quasar reference 선택을 통해 부과된다. 따라서 그 frame의 통계적 spin 불확실성은 물리적인 Fermi–Walker frame과의 절대 각속도 불확실성과 다르다.

## 직접 읽은 원문과 사용 범위

### S1: Gaia-CRF3

Gaia Collaboration (Klioner et al.), A&A 667 A148 (2022), DOI 10.1051/0004-6361/202243483, arXiv:2204.12574. 출판본 31쪽 PDF의 §§1,3.4,4,5,6 관련 부분을 실제 읽었다.

원문: https://openaccess.inaf.it/server/api/core/bitstreams/00c08eed-35d0-4511-860d-26b9bac65acf/content

증거: p.3의 6개 기준틀 자유도, p.15 §5의 no-net-rotation, Eq.(12), p.16의 source-subset sensitivity. Citation refs: turn12view0, turn13view0, turn13view1, turn13view2, turn13view4, turn17view0.

- 관측해는 orientation 3개와 spin 3개의 자유도를 외부 조건으로 고정한다.
- Frame rotator는 선택된 QSO들의 net rotation을 없앤다. 사용한 spin sources는 428,034개다.
- 최종 frame-rotator subset 재적합: spin norm 약 0.8 μas/yr; 성분별 uncertainty 약 0.4 μas/yr.
- 전체 CRF3 대상 Eq.(12): spin=(-3.44±0.30,+1.57±0.28,-1.24±0.32) μas/yr. 이 기호는 우리 물리 와도와 동일시하지 않는다.
- subset 선택에 따른 spin 차이는 수 μas/yr이고, 논문은 이를 더 정밀한 no-rotation 보증으로 표현할 수 없다고 명시한다.
- Gaia proper motions에는 acceleration 신호가 남아 있으며 별도 지정값을 미리 제거하지 않는다. ICRF3의 고정 acceleration epoch correction과 구분한다.

### S2: Position drift with Gaia

Kouvelis, Heinesen, Shalgar & Korzyński, arXiv:2508.02810v1 (2025-08-04). 현재 abs 페이지에 v1만 기재됨. 원문 §§2–5, Table 1, Appendix A를 실제 읽었다.

원문: https://arxiv.org/html/2508.02810v1

증거: Eqs.(9)–(15), Table 1, §§3.1,4.2,5. Citation refs: turn6view1, turn7view3, turn7view4, turn7view5, turn17view2, turn18view0.

- Gaia DR3 5-parameter QSOs 1,215,942개; QSOC z 정보 1,170,933개, z=0.0826–6.12295.
- Table 1 glide 성분=(-0.22±0.43,-4.11±0.34,-2.53±0.34) μas/yr; norm=4.86±0.34 μas/yr.
- Electric quadrupole coefficient 표준편차는 0.23–0.46 μas/yr. 이는 해당 basis의 통계 오차다.
- Eq.(15)는 각 source 내부 2×2 covariance만 포함하며 source 사이 covariance는 포함하지 않는다.
- ℓ≤4를 공동 적합한다. Quadrupole의 물리 원인은 확정하지 않는다. Redshift별 glide 변화 2–3σ, rotation은 magnitude 관련 계통오차 가능성이 크다.
- 측정된 spin은 frame-rotator sources 대비 source 집합의 상대회전이다.

해석상 주의: Eq.(12), Eq.(14), Appendix A의 계수와 basis normalization을 외부 표준 VSH와 곧장 동일시하지 않았다. 이번 R4에서 Table 1의 quadrupole norm을 Σ의 Frobenius norm으로 환산하지 않는다. 이 문제를 해결하려면 저자의 실제 fit basis 또는 재현 코드와 계수 정의를 일치시켜야 한다.

### S3: 기존 proper-motion anisotropy 분석

Darling, MNRAS Letters 442 L66 (2014), “Hubble expansion is isotropic in the epoch of dark energy”.

원문: https://academic.oup.com/mnrasl/article/442/1/L66/955473

증거: §§2–5, Tables 2–3, Eqs.(4),(6). Citation refs: turn4view1, turn17view1.

VLBI sources 429개에서 Bianchi-I 전단 모형을 적합했다. H0=72 km/s/Mpc를 15.2 μas/yr로 놓았다. Table 2의 세 eigen-expansion fractions는 (+0.17±0.07,-0.19±0.07,+0.02±0.07). 논문의 7%는 best-constrained direction의 1σ 규모다. 전체 shear norm의 95% model-independent bound가 아니다. 표3의 표준 VSH quadrupole norm은 6.2±2.1 μas/yr이며 significance는 낮다. 외부 Galactic acceleration dipole을 제거했다. Morphology basis 자체는 일반 E2이나 cosmological parameter 해석에는 모형을 썼다.

## 추가 nearby 후보: 존재는 확인, 이번 body에는 미채택

1. Paine et al. (2020), ApJ 890 146, arXiv:1912.11935. Primary abstract는 Gaia DR2와 Cosmicflows-3의 nearby galaxies 232개를 확인한다. 원문 본문은 이번 fetch 경로에서 열리지 않아 distance likelihood·selection·cross covariance를 확인하지 못했다. 공개 저자 포스터도 있으나 현재 이론 명제의 입력 authority로 대체하지 않았다. https://arxiv.org/abs/1912.11935
2. Maloney et al. (2026), arXiv:2606.00280v1. Primary abstract는 Gaia DR2/DR3 및 low-z spectroscopic catalog의 galaxies 67,173개를 확인한다. D>5 Mpc cosmic proper motion과 near-field 결과가 있다. 본문 fetch는 실패했으므로 redshift-derived distance와 독립 distance를 구분하는 계약은 아직 미확인이다. https://arxiv.org/abs/2606.00280

따라서 “matched nearby PM/distance 자료는 존재하지 않는다”는 결론은 금지한다. 이번에 확보한 수치와 source identity만으로 R4의 matched D,2D,4D 계약이 충족되지는 않았다는 것이 정확한 상태다. 앞선 후보 원문의 재료 취득이 최소 후속조치다.

## R4로 들여올 수 있는 구체 관측 계약

계약 O1: 추론 대상은 먼저 관측 response coefficient다. κ_catalog(n)=P_nΣn+(ω−Ω_frame)×n+P_nb_pec+s(n)라는 R3 식을 유지한다. Gaia의 frame convention을 Ω_frame=0이라는 물리 가정으로 바꾸지 않는다.

계약 O2: 절대 ω가 목표이면 독립 기준틀 보정의 body U_frame을 요구한다. 이것이 없으면 공통 shift (ω,Ω_frame)→(ω+δ,Ω_frame+δ)는 불변이다. 실자료 검수는 relative rotation 또는 quotient 공간에서만 닫는다. 서로 다른 z bin의 차이에서도 magnitude/colour/sky weights에 의한 frame residual을 공동 latent로 유지한다.

계약 O3: 발표된 1σ 값은 likelihood의 통계적 scale이며 hard bound가 아니다. 미지의 source 간 covariance, calibration VSH, intrinsic source motion은 별도의 집합/확률법칙이 필요하다. 관측된 quadrupole 전체를 systematic contamination upper bound로 쓰거나 전부 physical shear로 쓰면 서로 다른 가정을 한 것이다. 각 가정을 명시해야 한다.

계약 O4: 삼중-shell 소거에 들어갈 공통 u/D는 동일한 observer velocity 또는 실제 검증된 coherent source field의 template이어야 한다. source population이 다른 shell의 독립 peculiar velocities까지 같은 u로 놓을 수 없다. 차이는 잔차 budget에 포함한다. Angular selection을 맞추거나 common weighted response operator를 만들어야 multipole별 소거가 성립한다.

계약 O5: D는 독립적으로 지정된 거리다. cz/Hfid를 D로 쓰고 다시 cz/D에서 H를 검증하면 calibration 순환이 생긴다. Distance uncertainty 및 shell window는 moment constraints Σ_j w_j E_j[D^-1]=0, Σ_j w_j E_j[D]=0 형태로 반영해야 한다. 중심값 D,2D,4D는 실제 weight-moment 계약의 특수 경우다.

계약 O6: 매끈함만으로는 알려진 유한 ||g''|| 상한이 생기지 않는다. 근원 물리 jet이나 외부 데이터가 제공하는 uniform bound M을 선언하고 provenance를 붙여야 한다. 조건부 M-family는 계산 가능하지만 실증된 deterministic body는 아니다.

## Wolfram 실제 단위 검산

평년은 Julian year 31557600 s, au=149597870700 m, pc=(648000/π) au로 고정했다. H0=70 km/s/Mpc는 sensitivity 비교용 명시적 기준값이며 이번에 측정한 값이 아니다.

실행 입력:

```wolfram
N[With[{muasyr=Pi/(180*3600*10^6*31557600),
 h=70000/(10^6*(648000/Pi)*149597870700)},
 {muasyr,h,h/muasyr,3*h/muasyr,
 (0.34*muasyr)/(3*h),(3*h*10^-5)/muasyr,
 0.34/((3*h*10^-5)/muasyr)}],16]
```

실제 출력:

```text
{1.5362818500441605e-19, 2.2685455026110555e-18,
 14.766466859878909, 44.299400579636726,
 0.007675047417149231, 0.00044299400579636726,
 767.5047417149232}
```

따라서 1 μas/yr=1.5362818500441605e-19 s^-1. 0.34 μas/yr는 0.0076750 Θ0이다. 코드의 b=10^-5 계산은 설명용 기준값에 대한 환산이며 MES 상한이라고 주장하지 않는다. Owner가 채택한 실제 R4 sensitivity benchmark는 epsilon1=0, epsilon2=epsilon3=10^-5, H=70의 조건부 MES norm ceiling 0.00151884 μas/yr 및 drift RMS 0.000679244 μas/yr이다. 본 분담에서는 그 MES 계수를 재검증하지 않았으며 최종 권위는 owner의 유도·Wolfram 증거다. 발표 VSH 오차 0.23–0.46 μas/yr와의 비교는 규모 비교까지만 허용한다. Basis 변환, 공동 noise inverse, 삼중-shell noise amplification, systematics를 적용하지 않았으므로 정확한 detectability factor로 쓰지 않는다.

종결 판정: 문헌 사실 LITERATURE_SUPPORTED, 기준틀 및 입력 계약 DERIVED/CONDITIONAL, 단위 환산 WOLFRAM_NUMERICALLY_CHECKED. 실자료 catalog fit NOT_RUN. Useful empirical MES improvement UNRESOLVED.
