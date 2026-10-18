# HTT 후속 이론 연구 루프: 실제 Planck 복수 처리 + SH0ES 전체 거리 사다리

기준일: 2026-10-15 KST. 기준 Git checkout obs/solver-free-dossier-20261014,
기준 HEAD 13d8d85fa470d645d008986e8f77d8d0f70fdf54.
연구 가설과 처리된 실제 관측자료의 역할을 구분한다.
이전 loop1–4의 채택된 국소 광학 inverse, local Lorentz pullback,
STF multipole invariants, finite harmonic mask, nuisance quotient,
공유 calibration/selection 법칙을 가정 및 claim tier 그대로 사용한다.

## R1–R2: 물리 목표와 문헌·선행방법의 구분

질문 1: 같은 Planck 하늘의 실제 half-mission HM, odd-even OE,
SMICA/NILC 성분분리와 tSZ-deprojected 방법을 동시에 처리하면,
HTT 저차 Q/O 모양과 polarized E/B가 관측 처리에 얼마나 민감한가?
목표는 anomaly p-value가 아니라 실제 관측 operator/source response
자체를 정량화하는 것이다.

질문 2: 공식 SH0ES 2022 거리 사다리의 3492개 y, 47 x 3492 L,
3492 x 3492 전체 공분산 C가 실제 식별하는 방향은 무엇인가?
이를 CF4 그룹거리/공유 영점으로 안전하게 연결하려면 어떤
공통 anchor source identity 및 cross covariance가 필수인가?

기본 문헌:
- Planck 2018 results IV: Diffuse component separation, A&A 641 A4
  https://www.aanda.org/articles/aa/full_html/2020/09/aa33881-18/aa33881-18.html
- ESA Planck PR3 CMB maps: https://wiki.cosmos.esa.int/planck-legacy-archive/index.php/CMB_maps
  OE split은 instrumental noise tracer, HM은 instrumental
  systematics tracer. 둘 다 물리적으로 독립된 우주 하늘은 아니다.
- Riess et al. 2022, ApJL 934 L7, DOI 10.3847/2041-8213/ac5c5b.
- Source-pinned SH0ES matrices and official fitting code:
  https://github.com/PantheonPlusSH0ES/DataRelease/tree/main/SH0ES_Data
  pinned commit c447f0fea703fcd0fff57de5000947b5ca81286b.
- Tully et al. 2023 ApJ 944 94, CDS J/ApJ/944/94: CF4 55,877
  individual, 38,053 current grouped release source rows.
- 기존 HTT Report A 이론, optical/energyframe theorem과
  statistics/information-loss/nuisance quotient 검산 자료.

## R3: 명시된 단위와 물리적 연산자

Metric signature (-,+,+,+). 관측 sky coordinate는 Planck HEALPix
Galactic frame, native map NESTED NSIDE2048, thermodynamic K_CMB.
Fine native confidence Int/Pol mask와 HM/OE missing-pixel Int/Pol mask를
각각 교집합하고 NSIDE64 RING으로 집계한다. 발표 release common
temperature confidence와 편광 confidence mask를 구별한다.
원천 temperature는 microK_CMB, Q/U도 같은 temperature 단위.
Q/U는 spin-2 bundle의 국소 polarization basis에서 정의된다.

온도는 실수 정규직교 조화함수의 l=0..5 전체를 동시 mask OLS로
적합한 뒤 l=2..5의 32개 계수만 유지한다.
편광은 Q/U를 각각 scalar Ylm으로 역산하면 spin gauge가 틀리므로,
spin2 E/B 응답의 실수 64개 계수를 l=2..5에서 joint mask LS로 적합한다.
이 유한기저 밖의 실제 high-l E/B, beam 및 component separation
transfer는 included가 아니다.

## R4: Four-way same-sky contrast theorem (bounded)

같은 전달법칙과 같은 적합 연산자 P_M 아래의 네 계수벡터
x=(HM1,HM2,OE1,OE2)를 생각하자. 선형 변환

  mu4=(HM1+HM2+OE1+OE2)/4,
  dHM=(HM1-HM2)/2,
  dOE=(OE1-OE2)/2,
  dPart=(HM1+HM2-OE1-OE2)/2

의 matrix determinant는 +1/4이며 invertible이다.
네 입력 모두에 동일한 physical sky 계수 s를 더해도
dHM,dOE,dPart는 불변이고 mu4만 s만큼 변한다.
Wolfram exact arithmetic 및 합성 숫자 주입으로 검증했다.

**핵심 가정:** HM과 OE의 true-sky transfer가 동일해야
dPart에 sky contribution이 정확히 소거된다.
서로 다른 compsep/beam 응답 R_s에서는 차이
P_M (R_i-R_j) T_phys가 일반적으로 남으므로,
관측된 차이를 무조건 noise/systematic의 independent sample이라
해석하는 주장은 금지한다. 동일 mask를 적용해도
R_i-R_j가 사라지는 것은 아니다.

같은 l-band에서 x1,x2의 cross power는

  Ccross=<x1,x2>/(2l+1)
       = (||m||² - ||d||²)/(2l+1),
  m=(x1+x2)/2,d=(x1-x2)/2.

이는 finite-dimensional identity이며 독립 noise law가 아니다.

## R5: 공개 Planck 관측 실험의 법칙

관측 x_s = P_M R_s[T(G),foreground_s] + n_s + common_syst,
각 s의 처리는 fixed source. 모든 map의 temperature 공통 선택
mask는 같은 26,846개 NSIDE64 픽셀이고, 편광은 다른
30,021개의 NSIDE64 픽셀. T OLS의 condition=3.60138,
spin E/B OLS condition=3.13096, 각각 P X identity 잔차
4.00e-15 및 2.44e-15로 확인했다.

HM/OE split의 source 평균 차이와 cleaning 방법 차이는
one sky의 source-process sensitivity이며, noise covariance의
estimator나 Planck physical null PTE가 아니다.
같은 sky에서는 같은 process를 쓴 HM split noise가 일부
나누어질 수 있으나, OE와 HM의 noise도 상관되어 있다.
실제 split covariances C_ij가 주어지지 않은 상태에서
차이 벡터의 norm을 반복 random samples로 세면 안 된다.

## R6–R7: 실제 source 실행과 Q/O를 통한 이론 연결

동일 mask 실제 T l2–5에서 half-difference 노름:
  SMICA HM 0.4247235 microK;
  SMICA OE 0.5409386 microK;
  NILC HM 0.5097788 microK.

같은 mask, 같은 SMICA full l2–5 노름에 대한 method/source 차이:
  SMICA HMmean−OEmean 0.10211%;
  SMICA full−HMmean 0.07539%;
  NILC HMmean−SMICA HMmean 2.10883%;
  NILC full−SMICA full 2.11829%;
  SMICA noSZ full−normal full 5.35176%.

이는 algorithm/foreground treatment/beam/source variation에
민감한 표본수치이지 foreground physical uncertainty
distribution의 estimator가 아니다.

HTT STF 이론에서 Q_ab∈STF2, O_abc∈STF3,
ideal full-sky local first-order boost는

  delta_beta O_abc = 3 beta_<a Q_bc>

이다. 발표-source beta_ref norm=0.00123357354를 fixed
Galactic Cartesian frame에서 대입하면 이 대수 반응 norm은
현재 SMICA nominal fitted O의 0.1122766%다.
실제로 관측된 NILC vs SMICA full O 변형 norm은 위
ideal 반응의 13.607배, noSZ vs nominal SMICA는 54.638배.
따라서 관측 processing nuisance 진단은 물리 신호의
방향/모양을 논하기 전에 실제 필수 단계다.

**엄격한 scope:** 분모는 full-sky Q→O 대수 생성자이며
true Planck Q/U/beam/mask/compsep map forward response가
아니다. 이것은 정확한 physical beta bias, upper bound,
global Bianchi tilt, causal source acceleration 또는
anomaly significance 측정이 아니다.
SMICA full의 Q shape invariant 약 -0.18801,
SMICA noSZ의 Q shape 약 -0.23389.
칠성분 chirality 약 -0.01528 vs -0.03093,
동일 하늘에서 처리방식의 형태 의존성을 확인했다.

## R8: spin-2 polarized response와 한정된 EB

실제 SMICA source l2..5에서 Q/U의 유한 spin2 design
64차원을 동시에 적합했다. 각 split의 EB norm 차이는
  SMICA HM 0.4312804 microK,
  SMICA OE 0.3458642 microK.
같은 mask의 method 평균 대조:
  NILC HMmean vs SMICA HMmean EB 0.7373482 microK.
l2 E/B fitted spectra는 실제 source E/B coefficient-space에
정의되지만, 빠진 l>5 polarization과 mask mixing 및
component separation transfer로부터 자유로운 genuine
CMB lowE/BB power가 아니다.
EB parity test의 full physical null, pixel noise covariance,
angle-dependent instrument calibration 없이
이론적 parity violation, tensor GW 또는 anisotropic
Thomson transfer evidence로 승격할 수 없다.

## R9: SH0ES full-C ladder exact GLS, 그리고 cross-catalogue gauge

2022 release의 source를 변화시키지 않고

  q_hat=(L C^{-1} L^T)^{-1} L C^{-1}y,
  Cov(q_hat)=(L C^{-1} L^T)^{-1}

의 모든 47개 parameter를 full correlated C를
Cholesky whitening하여 GLS 적합한다.
Observed equations 3492, residual DOF 3445.
chi2=3552.7593303 (chi2/DOF=1.0313),
normal matrix condition approximately 2.6271e7,
normal gradient residual sufficiently small (<1e-9).

공식 별도 lstsq_results.txt center q_ref로 평가한
chi2_ref는 3559.57897335, delta chi2=6.81964305.
최대 한 coordinate 차이는 0.0496177 native units.
따라서 동일 C,L,y의 정확한 no-prior GLS와
lstsq_results.txt 사이의 SMALL but measurable disagreement가
남아 있고, 원본 코드/문서상의 prior-center 생산법을
독립 확인하기 전에는 정확재현이라 부르지 않는다.
공식 README는 Cepheid slope -3.285가 이미 baseline
pre-subtracted됨을 명시하므로 free-slope coordinate를
절대 slope로 오인하지 않는다.

프로파일 Fisher 정보:
  F_t = t^T[C^{-1}-C^{-1}A(A^TC^{-1}A)^{-1}A^TC^{-1}]t,
  A=L^T.

t가 col(A)에 있으면 exact algebra에서 F_t=0.
source column0를 t로 사용한 actual 수치 ratio
F_t/(t^T C^-1 t)=6.3e-28.
전체 3492행 공통 가산방향 t=1은 약 8.45575e-7의
상대정보만 남긴다. 이는 mathematical source-space
template의 nearly-degenerate direction이고,
CF4의 영점 또는 H0 parameter의 실제 prior인 것처럼
운반하면 안 된다.

이론적으로 공통 physical anchor parameter eta와 그
공분산 K를 실제로 두 probe가 공유한다면

  Cjoint = [[D_SH+Z_SH K Z_SH^T,   Z_SH K Z_CF^T],
            [Z_CF K Z_SH^T,      D_CF+Z_CF K Z_CF^T]].

그러므로 Z_SH K Z_CF^T≠0이면 두 public data products는
조건부 독립이 아니다. 합성 고정초기법칙에서
분산 sigma_eta²인 공유 anchor와 각 분산 sigma²인
두 observable을 평균할 때 실제 variance는
sigma_eta²+sigma²/2이고, 독립으로 오인하면
(sigma_eta²+sigma²)/2가 되어 shared anchor variance
절반만큼 과소평가한다. Wolfram/NumPy exact test.

실제 SH0ES와 CF4의 행/host/anchor ID 대응인
Z_SH 및 Z_CF가 현재 주어진 compact 47parameter
matrix에서 자동 생성되는 것은 아니며,
분포 혼합이나 실제 CF4 selection covariance를
검증하기 전 CF4-H0 joint posterior는 NOT_ADMITTED.

## R10: 채택/보류와 다음 물리 기여

채택 가능한 source-bound results:
- 실제 같은 mask에서 T harmonic/STF geometry의
  9개 source 처리 비교와 exact multi-split contrast;
- polarized spin2 joint finite imaging + masked split contrasts;
- local beta reference와 processing delta의 algebraic
  dimensioned contrast;
- source C,L,y full Cholesky-GLS and
  cross-catalogue shared-anchor anti-double-counting lemma.

미해결 물리 입력:
- split-specific beam, frequency/component-separation response
  및 실제 E2E correlated split-noise/foreground simulations;
- Planck high-l CMB source and full spin2 Boltzmann/Bianchi
  transfer, alignment with true physical beta/nonlocal tilt;
- SH0ES 47-coordinate source ID, Cf4 release group/host
  zero-point mapping Z_CF, shared anchor covariance K,
  full CF4 sample-selection normalization and peculiar velocity law;
- original SH0ES lstsq_results construction correspondence.

이번 결론은 기존 HTT 이론을 실제 자료에 적용한
재현 가능한 source-bound mathematical/observational result다.
No new H0,q,beta,background shear, primordial B,
cosmological parity violation, or Bianchi likelihood detection.
Native subagent tool is not available in this host:
native_subagent=NOT_RUN; used serial computation and bounded
self/audit tests.

## R10 실제 재개 보강: 공개 SH0ES Cepheid host와 CF4 source 위치 대응

공식 SH0ES table2.tex는 개별 WFC3-IR Cepheid의 field name,
J2000 RA/Dec를 제공한다. 이것을 host label 41개로
묶고 각 group의 normalized spherical centroid를
구성했다. CF4 Table2에서 e_DMceph>0, DMceph>0인
개별 galaxy 69개의 source J2000 위치와 4 arcmin
고정 문턱으로 대응했다.

실제 결과는 **37/41 positional candidates**이고
최대 각차 2.2324806 arcmin, accepted candidate의
두번째 nearest-source 후보와 최소 각차는
13.2098974 arcmin이다. 현 조건의 competing candidate는
0개, 대응하지 못한 field는
LMC, M31, N4536, SMC 네 개다.

N3972와 N3982는 별개의 SH0ES Cepheid host field지만
CF4 그룹 1PGC=37642에 둘 다 배정되어, 대응 후보
37개의 고유 그룹 수는 36이다. 이는 CF4 그룹화와
SH0ES 별개 host 모수의 다대일 가능성을 보여준다.
그러나 source 위치 후보를 HOST_IDENTITY_CERTIFIED로
표시하거나 37개 후보 전체에 공통 영점 공분산을
할당하면 아직 과학적 근거가 불충분하다.
본 source matching은 exact hostname cross-ID,
Cepheid event ID, 47 parameter design row ordering,
SNIa event overlap 및 source-calibration law의 검증을
대체하지 않는다. 현재 얻은 것은 실제 source
ID 후보를 확보한 단계다.

정확한 입력 source hash/개별 후보 위치·PGC/1PGC와
차이값: results/shoes_cf4_astrometry_candidates_v1/result.json.
마스크/geometry 규약과 관계없는 원래 SH0ES-CF4 물리
통합 likelihood는 여전히 HOLD다.
