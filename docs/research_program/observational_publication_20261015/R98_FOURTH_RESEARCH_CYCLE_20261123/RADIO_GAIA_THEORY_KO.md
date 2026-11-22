# R98 전파·Gaia 전체 자료 분석: 이론식, 구현, 판정

## 1. 계산 범위와 측정량

여기서 적합한 것은 전파 하늘의 조건부 셀 강도와 Gaia/Quaia의 겉보기 접평면 고유운동이다. 전파 쌍극자를 우주론적 물질 속도로, E2/B2를 normal-frame shear/vorticity로 동일시하는 추가 응답 모형은 별도 의무다. 물리 signature는 (-,+,+,+)이고 속도 변환에는 c를 보존한다. 전파 계수는 무차원, Gaia 결과는 μas yr⁻¹이다.

R89의 파일 전체 reader와 선언된 마스크를 재사용했다. 실제 로컬 입력의 행 수는 NVSS 1,773,484, RACS-low DR1 2,123,638, SPICE-RACS DR2 3,980,923, SUMSS 211,050, LoTSS DR3 v1.0 FITS 13,667,877이다. 다섯 파일 합 21,756,972는 서로 중복될 수 있는 카탈로그 행 수이며 독립 천체 수가 아니다. 첫 R98 실행에서 파일 전체의 SHA-256과 전체 reader를 실행해 지도를 만들었으며, 이후 재실행은 그 지도와 출처 receipt의 SHA, 원본 stat identity 및 reader SHA를 대조한다. --audit-inputs는 원본 전체 byte hash를 다시 계산한다.

전파 sky는 ICRS NSIDE=16의 셀로 만들었다. NVSS/RACS/SPICE/SUMSS/LoTSS의 선언된 마스크 내 셀 수는 1731/1202/1872/477/966이다. 마스크 안의 0-count 셀도 likelihood에 포함했다. RACS RMS cut은 각 천체의 측정 RMS로 사후 선별하지 않고 공간 footprint로 적용한다. LoTSS의 기존 raw-density interior 마스크는 조건부 분석용이며, 새로운 독립 coverage mask로 교체하는 D05 의무가 남는다.

LoTSS 공식 소개 페이지는 13,664,379 source를 기재하지만 로컬 v1.0 FITS NAXIS2는 13,667,877이다. 3,498행 차이의 원인은 추정하지 않았다. 실제 분석은 로컬 파일의 exact hash와 NAXIS2에 고정된다. 공식 v1.0 파일에 HTTP Range 요청으로 table header 8,640 bytes를 확인했으며 NAXIS2=13,667,877로 로컬과 일치했다. 해당 table header의 byte hash도 일치한다. 웹 소개 문구와 공개 FITS header의 차이이고, 전체 공개 payload가 로컬과 동일함까지 입증한 것은 아니다. 상세 receipt는 ACQUISITION_PREFLIGHT.json을 따른다.

Gaia CRF3 1,614,173행과 Quaia–CRF3 join 692,154행을 전부 방문했다. CRF3 품질 선별은 R69의 finite covariance, RUWE<1.4, visibility_periods_used≥8, duplicated_source=False이며 1,580,645행이다. 이것을 R89의 더 좁은 five-parameter subset과 혼동하지 않는다. Quaia 적합 표본은 five-parameter solution, RUWE, finite pm/covariance, 양의 relative selection 등을 만족하는 634,233행이다. 각 적합의 제외 조건과 적격 수는 JSON과 코드에 고정되어 있다.

## 2. 전파의 positive mean 모형

각 관측 셀의 방향을 n_i, 개수를 N_i라 한다. 기본 네 열과 STF를 포함한 아홉 열을 비교한다.

$$
\eta_i=b_0+\mathbf b\cdot\mathbf n_i,\qquad
\eta_i=b_0+\mathbf b\cdot\mathbf n_i+
 \sum_{A=1}^{5}q_A T_A(\mathbf n_i),\qquad
\mu_i=e^{\eta_i}>0.
$$

T_A는 CF4 H03에서 재사용한 고정 STF 기저다. q를 넣었을 때 b 자체를 전천 정규화 쌍극자라 부르지 않는다. 네 열 모형에서는 방향 적분을 정확히 할 수 있다. r=|b|에 대해 Z=4π sinh(r)/r이므로,

$$
\langle\mathbf n\rangle=\nabla_{\mathbf b}\log Z
 =\left(\coth r-\frac1r\right)\frac{\mathbf b}{r},\qquad
\mathbf D=3\langle\mathbf n\rangle.
$$

r→0에서는 D=[1−r²/15+2r⁴/315+…]b를 써 cancellation을 피한다. 이는 모델의 전천 l=1/monopole 정규화이며, 마스크로 가려진 실제 sky의 무모형 재구성은 아니다.

Boehme 등의 compound Poisson motivation에 따른 NB1 셀 law를 사용한다. 고정 p에서

$$
r_i=\mu_i\frac{1-p}{p},\quad
P(N_i=n)=\frac{\Gamma(n+r_i)}
{\Gamma(r_i)\Gamma(n+1)}(1-p)^{r_i}p^n,\quad
E N_i=\mu_i,\quad {\rm Var}\,N_i=\frac{\mu_i}{1-p}.
$$

여기서 r_i는 NB의 shape이고 위 식의 |b|와 다른 변수다. 원 논문의 선형 angular mean에 대해 R98은 exp link를 명시적으로 선택했다. 원 논문을 그대로 재현했다는 주장이 아니다. p는 training 셀의 sample mean/variance로 추정하며, held-out 셀을 이용해 재조정하지 않는다. 실제 분산은 angular signal과 선택효과도 포함할 수 있으므로 p를 순수한 다중 component 발생률로 해석하지 않는다.

eta에 대한 log-likelihood의 정확한 score는

$$
\frac{\partial\ell_i}{\partial\eta_i}
=r_i\{\psi(n_i+r_i)-\psi(r_i)+\log(1-p)\}.
$$

이 식과 NB2의 고정-shape score k(n−μ)/(k+μ)를 구별했다. CAS 확인과 독립 finite-difference/직접 logpmf 비교를 수행했다. p→0에서는 Poisson을 사용한다. 수치 구현은 scripts/r98/cross_survey.py의 logpmf_score와 fit_count_model이다.

## 3. 수치 안정성과 out-of-patch 비교

X=QR인 thin QR 분해를 이용하여 Z=Q√n, θ=Rb/√n으로 바꿨다. 이 좌표변환은 Xb=Zθ를 보존하며 likelihood, 열공간, 모형의 자유도를 바꾸지 않는다. 남쪽 SUMSS footprint의 dipole–quadrupole 공선성에서 L-BFGS의 score 잔차가 충분히 줄지 않는 현상을 이 변환과 BFGS로 교정했다. 임의 ridge나 coefficient clamp로 실패를 숨기지 않았다.

48개 공통 ICRS patch를 네 spatial fold로 배정했다. 19개 flux cut의 모든 셀을 한 번씩 held-out 평가했다. 각 fold의 b,p는 나머지 셀만으로 결정한다. 소스와 cut의 상관이 있으므로 아래 Δ log score들을 합쳐 독립 Bayes factor나 유의도로 쓰지 않는다.

| Survey | 모든 cut에서 NB1₄−Poisson₄ held-out log score 범위 | NB1₉−NB1₄ 범위 |
|---|---:|---:|
| NVSS | +15.06…+50.17 | −8.04…+2.29 |
| RACS-low DR1 | +2.36…+34.40 | −9.69…+1.33 |
| SPICE-RACS DR2 | +30.19…+93.85 | +30.40…+38.79 |
| SUMSS | +11.27…+27.22 | −0.74…+7.15 |
| LoTSS DR3 | +37.86…+431.95 | −23.70…+10.73 |

NB1₄는 19/19의 선언된 cut에서 Poisson₄보다 높은 예측 점수를 보였다. 아홉 열 모형의 개선은 보편적이지 않다. 이 결과는 과산포를 포함한 조건부 셀 law의 유용성을 지지하지만 물리적 쌍극자 원인의 판별에는 LSS/선택/SED 응답이 필요하다.

## 4. Gaia의 전체 VSH 적합과 동일 기준의 모형 비교

각 천체의 2-vector y_i=(μα*, μδ), 2×2 측정 공분산 C_i, 2×16 설계행렬 B_i에 대해

$$
F=\sum_i w_i B_i^T C_i^{-1}B_i,\quad
s=\sum_i w_i B_i^T C_i^{-1}y_i,\quad
\hat\beta=F^{-1}s.
$$

16개 성분은 E1 3개, B1 3개, E2 5개, B2 5개다. 실제 source covariance의 pmra–pmdec 상관을 유지한다. 축퇴·finite 검사는 R69 reader와 accumulation kernel에서 수행한다.

총 열 가지 적합은 CRF3 전체/품질, Quaia inverse-noise, relative-selection 곱셈, IPW floor 0.20/0.35, 그리고 z 경계 0.8/1.5/2.1의 네 bin이다. 네 redshift bin은 각각 92,686 / 238,552 / 174,944 / 128,051행이다. relative selection은 절대 inclusion probability로 검증된 것이 아니므로 IPW를 완전한 population correction이라 부르지 않는다.

다른 가중치 모형의 자체 weighted chi-square는 서로 직접 비교할 수 없다. 네 Quaia 가중치 모형은 동일한 inverse-noise 평가함수와 동일한 held-out patch로 다시 평가했다.

| Training weight | 공통 inverse-noise out-of-patch χ² |
|---|---:|
| inverse-noise | 1,406,885.5343 |
| relative selection 곱셈 | 1,406,890.4112 |
| IPW, floor 0.20 | 1,406,887.7392 |
| IPW, floor 0.35 | 1,406,891.4258 |

모두 같은 634,233행에 대해 두 접평면 성분을 평가했다. 작은 score 차이는 모형 선택·자료의존 가중치·공간계통오차의 영향을 함께 받는다. 물리적 null이 검증되지 않아 이를 cosmological p-value로 변환하지 않는다.

## 5. 여러 자료의 공통 패치 공분산

각 자료/모형에 같은 patch k를 제거하여 β_A^(−k)를 얻는다. K=48에서

$$
C_{AB}^{\rm patch}=\frac{K-1}{K}
\sum_{k=1}^K(\beta_A^{(-k)}-\bar\beta_A)
(\beta_B^{(-k)}-\bar\beta_B)^T.
$$

대조량 β_A−β_B의 공분산은

$$
C_\Delta=C_{AA}+C_{BB}-C_{AB}-C_{BA}.
$$

서로 겹치는 카탈로그를 독립으로 가정하여 C_A+C_B만 쓰는 방식을 피했다. Gaia 10×16=160차원 joint 행렬의 rank는 최대 47이며 실제 47이다. 160차원 inverse 또는 χ²를 계산하지 않았다. 이는 실제 하늘 한 개의 공간 진단이며 posterior draws 또는 정당화된 cosmological covariance law와 동일하지 않다.

| Gaia 대조 | E2 차이 norm | B2 차이 norm | tr CΔ / tr(CA+CB) |
|---|---:|---:|---:|
| CRF3 전체–품질 | 0.1343 | 0.1377 | 0.000798 |
| CRF3 품질–Quaia | 0.7068 | 0.8603 | 0.02455 |
| Quaia 기본–selection 곱셈 | 0.9397 | 0.4018 | 0.01237 |
| Quaia 기본–IPW 0.20 | 1.1790 | 0.6557 | 0.02232 |
| IPW 0.20–0.35 | 0.3508 | 0.3429 | 0.003044 |
| 최저–최고 redshift bin | 8.5373 | 6.6026 | 0.4862 |

norm 단위는 μas yr⁻¹이다. 특히 서로 거의 같은 source set의 대조에서 양의 상관이 크게 상쇄된다. 독립가정이 항상 보수적인 것도 아니다. 전파의 10개 survey pair에서는 trace ratio가 0.4203–1.0789였다.

전파 5×3=15차원 joint log-dipole 행렬의 rank는 15이다. 그러나 각 survey의 nonempty global patch 수는 42/40/44/18/26으로 다르다. 같은 48개 patch 좌표에서 비어 있는 patch를 제거한 반복도 유지했으므로 이를 동일-information jackknife 또는 calibrated covariance로 간주할 수 없다. 다음 단계에서는 source overlap와 mask/selection을 함께 가진 mock 하늘이 필요하다.

## 6. 실행·가속·정확성

전체 Gaia 행을 60,000행 chunk로 방문하고 patch별 충분통계 F,s,yᵀC⁻¹y,n만 유지했다. 큰 batch에는 기존 검증된 C++ kernel을 사용하고 작은 batch에는 NumPy를 쓴다. 실제 집계는 C++ 385회·5,919,468 source visits, NumPy 316회·446,515 visits다. 이 수는 중복 모형 방문 수이며 고유 source 수가 아니다. 마지막 kernel 호출만으로 전체 backend를 보고하던 오류 가능성을 제거했다.

최종 warm replay는 Gaia 약 10.05초, 전파 약 1.79초였다. 앞선 cold Gaia 실행은 약 21.49초였고 전파 최초 전체 hash/stream은 I/O 비용이 지배했다. 이 숫자들을 서로 나누어 알고리즘 speedup이라 부르지 않는다. 메모리는 마지막 원격 측정에서 Gaia 약 470 MiB(KiB 원단위 480,968), 전파 약 185 MiB(KiB 189,708) 수준이었다.

수치 및 cache 검증은 test_r98_cross_survey.py와 CMB_C9_CROSS_REVIEW.md에 있다. 독립 검토는 NB1 score, 전체 SUMSS folds, Gaia full joint covariance와 paired contrasts, 동일 평가함수의 예측 점수를 재계산했다. 두 cache 오염 회귀 반례도 고쳤다. 실패한 원본 감사가 오래된 map을 재승인하지 않으며, 명시적 원본 감사가 변조된 map을 새로 봉인하지 않는다.

## 7. 다음 구성적 의무

- D04/M05: Gaia release-specific angular errors, AGN photocentre 및 frame nuisance를 source covariance와 함께 구성한다.
- D05/M06: 전파 RMS/coverage/zero-source 영역, component association, multi-frequency SED 및 LSS를 포함하는 matched mock law를 도입한다.
- M02/M07: source-local boost, observer boost 및 normal-frame kinematics의 유한 적색편이 응답을 같은 광학 연산자로 계산한다.
- A04/A05: 새로운 법칙이 주어지면 모든 원본 행·모형·flux/redshift cut을 같은 source genealogy에서 재평가한다. 이미 계산한 전체 working-law 결과는 비교 기준으로 보존한다.

## 원전과 추적성

- Boehme et al., PRL 135, 201001 (2025), equations (4)–(8): https://doi.org/10.1103/6z32-3zf4 .
- Quaia release/relative selection maps: https://zenodo.org/records/10403370 .
- Gaia-CRF3, A&A 667 A148, release-specific astrometry: https://arxiv.org/abs/2204.12574 .
- LoTSS DR3 v1.0 catalogue and RMS/coverage products: https://lofar-surveys.org/dr3.html .
- 완료한 계산: RADIO_FULL_MODELS.json, GAIA_FULL_SHARED_PATCH.json, CROSS_PHY_RESULTS.json.
- 원본 구현과 재사용 한계: LEGACY_REUSE_DECISIONS.md, LEGACY_CONTENT_AUDIT.json.
