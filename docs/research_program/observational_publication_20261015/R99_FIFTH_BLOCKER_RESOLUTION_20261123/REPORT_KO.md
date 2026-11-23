# R99 · SQ-CF4 재진입 제5차 blocker 해소 보고서

2026-11-23, Asia/Seoul. 기준 branch: `research/r69-observable-physics-bridges-20261118`.

## 결과와 해석 범위

이론 R1–R10을 먼저 수행한 뒤 코딩 C1–C10으로 연결했다. 상세 단계 기록은 [CYCLE_RECORD.md](CYCLE_RECORD.md), 재실행·입력 인계는 [HANDOFF_KO.md](HANDOFF_KO.md)에 있다. 최신 R98-EXT를 출발점으로 네 계산 경로를 실제로 발전시켰다. 전체 CF4 선택 표본 35,970개 그룹의 비선형 거리 응답, 다섯 Bianchi/FLRW 배경의 유한 적색편이 Jacobi 거리, Gaia 전체 표본의 충분통계에 연결된 공유 오차장, LoTSS 1,580개 mosaic의 외곽 영역 합집합을 실행했다. 추가 자료는 정확한 버전·주소·용량·checksum·식별자 계약을 갖춘 8개 다운로드 작업으로 준비했다.

기존 60-node DAG의 과학 수락 조건은 유지한다. 기존 완료 상태는 **18/60 completed_scoped**, 이번에 새로 과학적 완료로 승격한 노드는 **0개**다. 새 코드와 유도가 수행 가능하게 만든 하위 과제와, 실제 자료·교정된 결합 확률법칙·독립 검증이 필요한 의무를 구분한다. 여전히 열린 21개 상위 의무(DATA 6, MODEL 9, ADDITIONAL_ANALYSIS 6)는 21개 노드라는 뜻이 아니다. 여러 노드가 같은 의무를 공유한다.

[BLOCKER_ACTIONS.md](BLOCKER_ACTIONS.md)와 [NODE60_EXECUTION_PREPARATION.json](NODE60_EXECUTION_PREPARATION.json)은 각 노드에 이번 변화, 재사용 가능한 결과, 남은 의무와 다음 계산을 연결한다. 과거 계산을 다시 했다는 이유만으로 이번 진전으로 세지 않았다.

## 1. 기준 문서와 보존한 출처

시작 시 로컬 HEAD와 GitHub branch는 모두 `eee33d7ed33e1af10d7c6a3c453810ecb227e461`였다. 최신 R98-EXT 과학 내용은 `369bbab5a8b8e7a372197064d01ff379a3f54590`에 포함되어 있었다. 그 확장에는 이미 NUFFT PV 투영, 공통 nuisance, 한 번의 복사 shear feedback, CMB 보정 민감도, Gaia rank-47 분석, SED 탐색이 있었다. 따라서 이를 “아직 코드 없음”으로 다시 분류하지 않았다.

과학 기준은 R78 `INTEGRATED_DAG.json`이다.

- 60개 노드, 129개 edge, 6개 논문 주제, 7개 PHY 교차 경로.
- 원문 SHA256: `90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11`.
- 원래 42개 노드 payload의 canonical SHA256: `e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d`.
- 다음 과학 진입점: SQ-CF4.
- R67의 7개 연구축과 R77/R78의 7개 PHY 조합은 별개 목록이다. 이번 매핑은 둘을 합치거나 대체하지 않는다.

기존 checkout과 Python 환경을 사용했다. 별도 worktree나 clone, main merge는 만들지 않았다. R98 결과와 기존 사용자 작업은 보존했다. 최종 검증은 새 결과, 관련 legacy 연산자, source identity와 DAG 구조에 한정한다. 과거 전체 회귀검사를 새로 통과했다는 주장은 하지 않는다.

## 2. CF4: 실제 단위 결함 교정과 source-space 비선형 응답

### 2.1 명시된 mag와 구현된 log-distance 단위의 불일치

R98의 일곱 방법별 depth-tilt nuisance는 진폭을 0.05 mag로 표시했지만, 구현된 응답 열은 dimensionless log-distance에 직접 가하는 \(+AG\)였다. 고정된 선택 표본, 가중치, 설계행렬과 투영 \(A\) 아래 distance modulus perturbation에는

\[
\delta y=-\frac{\ln 10}{5}G\,\delta\mu,\qquad
J_\mu=-\frac{\ln 10}{5}AG
\]

가 맞다. 동일한 nuisance 진폭을 mag로 해석하면 해당 일곱 열의 공분산은 \((\ln10/5)^2=0.212075924419136\)배가 된다. 적색편이 경계 두 열은 별도 기작이므로 이 인자를 곱하지 않았다.

전체 선택 표본의 실제 modulus를 일곱 방향으로 유한 이동하여 적합을 다시 계산했다. 교정 응답의 최대 오차는 \(4.9396\times10^{-16}\), 과거 열을 그대로 사용한 오차는 \(0.0215565\)였다. 일곱 열 공분산 trace는 0.00657935에서 0.00139532로 변했다. 이것은 관측자료가 변한 결과가 아니라 단위·부호 계약을 바로잡은 결과다.

R=5, WF 기반 18차원 조건부 Schur 진단은 다음과 같다.

| 값 | 과거 log-y 진폭 해석 재현 | 명시된 mag 진폭으로 교정 |
|---|---:|---:|
| 조건부 \(\chi^2\) | 11.99528442 | 12.11632063 |
| 조건부 log predictive density | 64.56989644 | 65.69895559 |

과거 수치를 먼저 재현했으며 그 오차는 \(3.04\times10^{-13}\) 이하였다. 이는 같은 자료와 가정한 공분산에 대한 내부 예측 진단이다. 독립적인 표본 검증이나 물리적 \(\Pi\), 유의확률을 의미하지 않는다. R98 파일은 수정하지 않고 R99에 교정된 실험을 추가했다.

### 2.2 거리 관측량에 따른 유한-z 응답

측정된 적색편이 \(z\), radial rapidity \(r=\operatorname{atanh}(u/c)\), \(\bar z=\operatorname{expm1}[\log(1+z)-r]>0\), \(\chi(z)=c\int_0^z dz'/H(z')\)를 사용한다. \(L=\log[\chi(z)/\chi(\bar z)]\), \(K=(1+z)/(H\chi)\)라 두면:

| 관측량 계약 | 유한 응답 \(f\) | \(u=0\)에서 \(\partial f/\partial u\) |
|---|---|---|
| background luminosity-distance proxy | \(L+r\) | \(K+1/c\) |
| native FP comoving log ratio | \(L\) | \(K\) |
| bolometric flux distance | \(L-r\) | \(K-1/c\) |

CF4에 섞인 모든 거리 방법을 bolometric flux로 일괄 해석하지 않는다. 각 방법의 실제 발행량과 교정 pipeline이 필요하다. [THEORY_CF4.md](THEORY_CF4.md)는 부호, 단위, 저적색편이 극한, 선택 정규화와 이 구분을 유도한다. 적색편이와 속도의 비선형 관계는 Davis–Scrimgeour의 원 논문과 교차 확인했다. 실제 혼합 자료에 대한 관측량 선택은 아직 source contract다.

### 2.3 공동 Gaussian field의 비선형 변환과 남은 공분산

기존 band-limited 선형 PV covariance를 latent Gaussian field로 사용하고, 양의 \(\bar z\)를 보장하는 truncated-rapidity marginal을 결합한 **명시적 민감도 모형**을 구현했다. 이 marginal이 실제 우주의 속도 법칙으로 검증되었다고 주장하지 않는다.

정규화된 Hermite 계수를 \(a_{ik}\)라 하면 평균은 \(Aa_0\), 첫 chaos의 상관 공분산은

\[
C_1=A\,\operatorname{diag}(a_1/\sigma)\,
 S\,\operatorname{diag}(a_1/\sigma)\,A^\mathsf T
\]

이다. 이 항은 기존 NUFFT 연산자를 재사용하여 full source에서 계산한다. 비선형 잔여 공분산은 PSD이며 임의 요약 대비 \(h\)에 대해

\[
\operatorname{Var}_{\ge2}(h^\mathsf T A f)
\le
\left[\sum_i |(A^\mathsf T h)_i|
\sqrt{\operatorname{Var}(f_i)-a_{i1}^2}\right]^2
\]

라는 보수적 상계를 함께 낸다. 독립 \(150\,\mathrm{km/s}\) 분산과 modulus 측정오차는 각각 한 번만 포함한다.

실행한 입력은 \(0.0100036\le z\le0.0999992\)의 35,970개 그룹, Fourier mode 39,282개다. 세 거리 정의 모두를 계산했다. Hermite 16→32차 결과 차이는 최대 \(1.89\times10^{-15}\), NUFFT와 직접 mode 투영의 차이는 약 \(2.1\times10^{-13}\)였다. Bolometric 모형에서 source별 비선형 잔여 분율 최대는 0.3618%, 36개 요약 좌표에 대한 보수적 잔여 대각 상계의 최대는 first-chaos 대각 대비 4.9961%였다. 상계와 실제 잔여값을 혼동하지 않는다.

legacy radial/transverse Bessel 공분산 적분과 20개 소스를 독립 비교했다. 상대 Frobenius 차이는 \(1.9082\times10^{-6}\), 대각 상대차는 \(1.8473\times10^{-8}\)였다. 전체 35,970-square dense matrix는 만들지 않았다.

### 2.4 대역 제한이 여전히 중요한 이유

명시된 R=5 선형 smoothing 모형에서 \(10^{-4}\le k\le1\,h/\mathrm{Mpc}\)를 비교 구간으로 정하면, 한 소스 속도 분산의 구간별 기여는 다음과 같다.

| 구간 | 비교 구간 분산 중 비율 |
|---|---:|
| \(10^{-4}\le k<0.005\) | 2.6586% |
| 기존 \(0.005\le k\le0.05\) | 55.7631% |
| \(0.05<k\le1\) | 41.5783% |

이 수치는 전체 36차원 tomography 공분산의 누락 비율이 아니다. 요약 투영은 위치·각도·창 함수에 따라 달라진다. 또한 고-k 선형 외삽이 실제 비선형 PV를 해결하지 않는다. 다음 계산에서는 각 누락 대역을 실제 \(A S A^\mathsf T\)에 투영하고 smoothing·비선형 모형·관측량 불확실성을 따로 비교해야 한다.

### 2.5 선택 정규화와 공개 upstream 자료

공통 장 \(F\)가 있는 선택 자료의 올바른 결합 likelihood는

\[
p(y\mid I)=
\frac{\int P(dF)\prod_i B_i(y_i,F)}
     {\int P(dF)\prod_i\alpha_i(F)}
\]

이다. \(P(dF)\)가 이미 detection에 조건부인 경우가 아니라면, field별로 정규화한 likelihood를 무조건부 prior로 평균하는 방식은 같은 분포가 아니다. 직접 Gaussian/probit 예에서 결합 포함확률은 0.295434인데 주변 포함확률의 곱은 0.25였고, 선택 후 평균도 -1.013468과 -0.751555로 달랐다. 공식의 차이가 실제 수치 차이로 이어진다.

선택 odds ratio의 범위 \(\Gamma\)와 공통 support를 가정할 때 얻는 부분식별 범위도 유도했다. 그러나 누락된 표본층의 비율과 support가 없으면 그것을 대신 추정한 것이 아니다. P1의 기존 2,048개 working draws에 source-level 식을 무조건 적용하지 않았다.

SDSS PV v1.1.0과 6dFGSv 공개 제품을 정확히 특정했다. SDSS의 group-level zero point, 64-bit 식별자, skew 분포의 mean/std 정의, simulation box를 공유하는 8개 observer를 보존해야 한다. 이 공개 부분자료는 CF4의 7-method upstream joint calibration과 전체 rejected-source denominator를 대신하지 못한다.

근거 및 실행: [CF4_RESULTS.json](CF4_RESULTS.json), [CF4_EXECUTION.md](CF4_EXECUTION.md), [THEORY_CF4.md](THEORY_CF4.md).

## 3. Bianchi: 광선 에너지·방향에서 실제 Jacobi 거리로 확장

기존 transport에는 광선 방향·에너지·편광 screen이 있었지만, 위치의 각도 변분을 포함한 beam focusing은 없었다. 동일한 homogeneous tetrad history에서 방향 변분 \(Q_A\)와 위치 connector \(X_A\)를 추가했다. \(N=\ln a\), 정상 congruence의 \(K=H I+\sigma\), 구조계수 \(C^k{}_{ij}\), 광선 공간방향 \(p\)를 사용하면 위치 변분은

\[
\frac{dX_A}{dN}
=\frac{Q_A+KX_A-p^iC^k{}_{ij}X_A^j}{H}
\]

를 만족한다. 각도 초기조건과 방향 변분 방정식, connection의 지표 순서, commutator 부호는 [THEORY_OPTICAL.md](THEORY_OPTICAL.md)에 명시했다. \(H>0\), synchronous homogeneous background, 적절한 normal-frame tetrad와 geometric optics가 적용 범위다.

면적, parity와 거리는

\[
S=-p\cdot(X_1\times X_2),\qquad
D_{A,n}=\frac{c}{H_*}\sqrt{|S|}
\]

로 얻는다. 관측자·방출자 Doppler factor \(D=\gamma(1-\boldsymbol\beta\cdot p)\)를 포함하여

\[
1+z=\frac{E_e}{E_o}\frac{D_e}{D_o},\qquad
D_{A,\mathrm{obs}}=D_oD_{A,n},\qquad
D_L=(1+z)^2D_A
\]

를 사용한다. 마지막 관계는 transparent metric optics를 가정한다. 관측 방향의 inverse aberration과 observer solid angle 변환을 중복 적용하지 않았다. caustic, 적색편이 root의 모호함, history 밖 목표는 명시적으로 구분한다.

**실제 실행:** R98 FLRW, I, V, VII_h, exceptional VI_h(\(h=-1/9\))의 다섯 배경, 12개 결정론적 antipodal 방향, 9개 적색편이 \(0.01,0.025,0.04,0.06,0.08,0.1,0.5,1,2\)에서 거리 540쌍을 계산했다. 관측자·방출자 운동 대조도 216쌍 계산했다.

| 검산 | 관측된 정확도/차이 |
|---|---:|
| Milne exact \(D_A\), 이론 단계 | 상대오차 \(1.53\times10^{-13}\) |
| Kasner exact \(D_A\), 이론 단계 | 상대오차 \(2.20\times10^{-13}\) |
| 실제 FLRW history 대 reference cosmology | 최대 상대차 \(4.58\times10^{-9}\) |
| boost를 포함한 FLRW | 최대 상대차 \(4.63\times10^{-9}\) |
| VI_h history 641→1281 samples | 거리 상대차 약 \(9.38\times10^{-10}\) |
| 비축방향 Bianchi I 독립 좌표광선 oracle | 관측각 차분 \(10^{-5}\)에서 상대차 \(1.66\times10^{-11}\) |

독립 oracle는 보존된 좌표 공변운동량으로 광선 끝점을 적분하고 관측각 중앙차분의 면적을 계산했다. 새 variational ODE를 그대로 복사한 검사가 아니다.

VI_h의 12방향 표본에서 \((D_{A,\max}-D_{A,\min})/\langle D_A\rangle\)는 \(z=0.01\)에서 약 \(7.0072\times10^{-4}\), \(z=0.5\)에서 \(6.2091\times10^{-4}\), \(z=2\)에서 \(1.3201\times10^{-4}\)였다. 이는 지정 배경·표본방향의 모델 값이며 연속 전천 최대나 관측 검출값이 아니다.

**남은 범위:** 위치 drift/proper motion, 실제 source calibration을 포함한 \(T_C(z),T_G(z)\), 동일 source/normal frame에서의 독립 heldout 검증은 아직 수행하지 않았다. 따라서 SQ-OPTICAL의 “Sachs/Jacobi + position-drift” 전체 수락은 열려 있다. 이번 모듈은 금지된 native low-\(\ell\) polarized Bianchi Boltzmann solver를 구현한 것이 아니다. R98-EXT의 한 번의 복사 feedback도 self-consistent Einstein–Boltzmann 고정점이나 완전한 I–IX 초기조건 atlas로 승격하지 않았다.

근거 및 실행: [OPTICAL_RESULTS.json](OPTICAL_RESULTS.json), [OPTICAL_EXECUTION.md](OPTICAL_EXECUTION.md), [THEORY_OPTICAL.md](THEORY_OPTICAL.md).

## 4. Gaia: 서로 다른 적합에 같은 오차장이 작용하도록 구현

R98 전체 source 충분통계의 exact SHA를 확인한 뒤, 10개 적합·48개 패치·16개 VSH 계수의 normal matrices를 사용했다. 대형 카탈로그를 다시 읽지 않아도 각 적합의 동일한 source 가중치와 설계가 반영된다.

패치 \(p\), 적합 \(a\)에서 첫 6개의 glide/spin 열을 \(E\)로 선택하면,

\[
J_{ap}=F_a^{-1}F_{ap}E,\qquad
C_{\mathrm{sys},ab}=J_a(K\otimes I_6)J_b^\mathsf T
\]

이다. 모든 적합에 동일한 6-component field가 작용한다. chord Gaussian kernel의 각도 scale 15°, 30°, 60°를 계산했다. 이 kernel과 진폭은 민감도 family이며 AGIS/AGN의 관측적으로 교정된 법칙이 아니다.

실제 normal-equation RHS를 perturb하여 다시 푼 값과 \(J\) 응답 사이 최대 오차는 \(5.3291\times10^{-15}\,\mu\mathrm{as/yr}\)였다. \(\sum_pJ_{ap}=E\)이므로 공간적으로 상수인 공통 field는 두 적합의 차이에서 상쇄된다. 실제 최저/최고 적색편이 대비의 잔여 응답은 \(4.0766\times10^{-16}\) 이하였다.

30° scenario에서 low/high-z 차이의 covariance trace는, 각 적합에 독립적인 field를 가정했을 때의 **0.00280152배**였다. 서로 겹치는 sky·source를 무시하면 대비의 오차를 크게 다르게 계산할 수 있음을 보여 준다. 관측 E2 차이의 norm과 같은 RMS를 만드는 scenario 진폭은 61.4193 \(\mu\mathrm{as/yr}\), B2는 50.5739 \(\mu\mathrm{as/yr}\)였다. 이는 적합된 진폭이나 신호 검출이 아니다.

기존 160차원 patch covariance의 rank는 47이다. 지지 부분공간의 이차형은 524.59283668이지만, 실제 계수벡터에는 norm 14.41087249 \(\mu\mathrm{as/yr}\)의 비지지 성분이 있다. 전체 **계수 Euclidean 제곱노름의 18.8374%**다. 이 수치를 물리 sky power의 18.8%라고 부르지 않는다. 독립 SVD가 같은 결과를 재현했다. 비지지 성분을 0으로 간주하거나 완전한 \(\chi^2\) 확률을 부여하지 않았다.

공유장 covariance를 empirical jackknife covariance에 바로 더하지 않았다. jackknife에 같은 공간 변동이 이미 들어 있을 수 있기 때문이다. calibrated total covariance에는 독립적인 측정 교차공분산, release-specific angular-error 정보와 AGN centroid law가 더 필요하다. 패치 내부의 작은 각도 변동과 실제 cosmological proper-motion transfer도 남아 있다.

근거 및 실행: [GAIA_SHARED_FIELD_RESULTS.json](GAIA_SHARED_FIELD_RESULTS.json), [GAIA_EXECUTION.md](GAIA_EXECUTION.md), [THEORY_CROSS_DATA.md](THEORY_CROSS_DATA.md).

## 5. LoTSS 외곽 geometry와 추가 자료 다운로드 준비

### 5.1 카탈로그 점유율에서 독립된 외곽 영역

공식 TAP에서 LoTSS DR3 mosaic 1,580개의 네 모서리 좌표를 받아 great-circle polygon의 Boolean 합집합을 계산했다. 중첩된 mosaic를 반복해서 세지 않는다. ICRS, fine nested HEALPix NSIDE 64/128/256에서 pixel-center 포함을 구한 뒤 NSIDE16 RING의 면적 fraction으로 내렸다.

| fine NSIDE | 외곽 합집합 면적(deg²) | NSIDE16 support cell |
|---|---:|---:|
| 64 | 22,480.4803 | 1,762 |
| 128 | 22,464.5337 | 1,771 |
| 256 | 22,475.1298 | 1,771 |

각 해상도에서 4,096개 방향을 독립 spherical halfspace 연산과 비교하여 불일치가 0이었다. 128→256의 L1 면적 변화는 0.0108337393 sr다. 경계 분해능 차이를 내부 결측·완전성 systematic의 오차 추정으로 사용하지 않는다. 외곽 면적은 최종 과학 sample의 공식 survey area와 다른 양이다.

실제 기존 full-sky count cache의 20/50/100 mJy 표본 659,841/339,865/194,914개는 모두 외곽 support 안에 있었다. support 안에서 count=0인 cell은 195/195/204개다. 내부 valid-weight/RMS를 아직 확인하지 않았으므로 이 cell을 검증된 “관측했지만 빈 하늘”로 취급하면 안 된다.

기존 mask의 966개 cell은 모두 새 fraction=1 영역이었다. 새 외곽 support에는 추가 805개 cell이 있지만, 기존 mask에는 density뿐 아니라 Galactic latitude/H I cut도 있었으므로 차이 전부를 density-cut 편향으로 설명하지 않는다.

고정 exposure \(e_p=\Omega_p f_p\)를 사용하는

\[
\mu_p=e_p\exp(X_p\beta)
\]

와 \(\log e_p\) offset을 구현했다. Poisson count는 0을 포함하고, support가 0인 곳의 양의 count는 거부한다. 현재 파일은 **외곽 geometry 기반 준비물**이다. valid-weight/RMS holes, flux/size completeness, source association와 SED, 공동 LSS null까지 완성한 radio likelihood는 아니다.

### 5.2 준비된 8개 제품

| 제품 ID | 고정한 크기(bytes) | 출처에서 확인한 상태/계약 |
|---|---:|---|
| sdss_pv_v1_1 | 20,231,640 | Zenodo 6824749, v1.1.0, published MD5, prefix HTTP206 |
| sdss_randoms_v1_1 | 284,000,071 | 같은 release와 published MD5 |
| sdss_mocks_v1_1 | 10,643,218,721 | 256 boxes ×8 observers, holdout은 box별 |
| sixdf_pv_table1 | 696,070 | 6dFGSv 공식 table1, prefix HTTP206, upstream checksum 없음 |
| sixdf_reconstruction_mocks | 17,344,070,928 | 공식 reconstruction archive, 내용의 PV matching은 미확정 |
| lotss_aux_1078 | 4,507,238,400 | live HTTP202 JSON → deferred, 과거 Online 표시로 대체하지 않음 |
| lotss_aux_355 | 6,025,820,160 | 관측 시 HEAD200와 크기 일치, 전송 시 재확인 필요 |
| commander_pr3_ffp10_noise_00000 | 603,987,840 | 기존 PR3/FFP10 signal에 맞춘 fullmission noise ID00000 |

각 stable URL, published MD5, source response SHA, 단위·columns·ID·genealogy는 [ACQUISITION_PLAN.json](ACQUISITION_PLAN.json)과 [ACQUISITION_SOURCES.md](ACQUISITION_SOURCES.md)에 있다. prefix SHA와 full-product checksum을 구분한다. signed redirect 주소를 저장하지 않았고 tape staging도 요청하지 않았다. HTTP202는 payload가 아니다. Commander 단일 pair는 matched joint null의 완성을 뜻하지 않는다.

첫 작은 subset은 SDSS PV와 6dFGSv table1, 합계 **20,927,710 bytes**다. 아래 명령은 실제 실행한 download plan이며 payload를 받지 않는다.

~~~bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
.venv/bin/python -m scripts.r99.acquisition plan \
  --ids sdss_pv_v1_1 sixdf_pv_table1 --max-bytes 22000000
~~~

이번 작업에서 저장한 13개 provider 응답은 총 847,746 bytes, 이 중 science prefix는 17,408 bytes였다. 전체 science payload 다운로드는 0개다. 다음 실제 전송에서는 fresh response, exact size, upstream checksum 또는 새 full SHA를 확인하고 raw ID를 부동소수점으로 읽지 않아야 한다.

근거 및 실행: [ACQUISITION_RESULTS.json](ACQUISITION_RESULTS.json), [ACQUISITION_EXECUTION.md](ACQUISITION_EXECUTION.md), [inputs/lotss_outer_exposure_nside16.npz](inputs/lotss_outer_exposure_nside16.npz).

## 6. 여섯 대주제와 일곱 교차 경로에 미친 변화

| 대주제 | 이번에 실제 추가한 계산/구성 | 과학적 수락을 막는 핵심 잔여 |
|---|---|---|
| P1: 공통 \(x,F,\Pi,Q,G_F\)와 finite law | 선택 정규화·부분식별 조건, CF4 단위 교정과 비선형 carrier | 물리 body/anchor, source-qualified joint law와 누락 질량 |
| P2: low-\(\ell\) morphology와 복사 관측량 | 최신 CMB genealogy를 유지한 Commander exact-job 준비; optical frame 재사용 가능 | matched noise/foreground/선택 weight null, 독립 photon flux |
| P3: 적색편이·방향별 Hubble 측정 | full CF4 3종 거리응답·PV projection·잔여상계, 실제 \(D_A(z,n)\) | upstream calibration/selection, full-k source law와 독립 coverage |
| P4: radio dipole·local/global velocity | independent outer geometry, count offset, finite observer/emitter boost 경로 | 내부 valid coverage, completeness/SED/LSS와 source-preserving reselection |
| P5: Bianchi 분류·동역학 | 실제 5개 background의 positional Jacobi/면적·프레임 전달 | 독립 \(\rho,j,\pi\), native transfer/IC atlas, 수렴한 복사·화학 feedback |
| P6: congruence-compatible 운동학 | 공유 Gaia field covariance·상쇄, 유한-z 거리·관측자 사전 | position drift, calibrated scan/AGN law, common normal-frame matter evidence |

| PHY 경로 | 이번 결과의 연결 | 남은 수락 조건 |
|---|---|---|
| PHY-01 (P3/P6/P5) | CF4 response와 Jacobi distance를 동일 background/frame에 연결할 연산자 | source-matched shear leakage, 독립 normal flux·heldout covariance |
| PHY-02 (P2/P6/P5) | PR3 product genealogy와 기존 photon-moment 제약 재사용 | 교정된 복사 moments/null, 독립 flux 및 source evidence |
| PHY-03 (P2/P4) | count exposure와 finite observer boost | 동일 \(\beta\)에서 paired flux/SED 재선택 및 count/CMB joint law |
| PHY-04 (P6/P4/P5) | Gaia 공통장의 E/B 교차공분산, LoTSS 외곽 support | source-frame proper motion, AGN/scan·radio LSS 공동 null |
| PHY-05 (P5/P6) | exceptional VI_h의 실제 Jacobi 거리와 parity | rank 결론을 검증할 독립 noisy flux covariance |
| PHY-06 (P1/P2/P5/P6) | 실제 background 광학과 기존 한-loop 복사 결과의 구별 | 수렴한 higher-moment feedback/chemistry, 맞는 초기조건과 covariance |
| PHY-07 (P1/P3/radio) | CF4 distance-type 응답·selection law, upstream intake 준비 | 실제 거리 변화·source overlap·radio selection의 교정된 결합 검증 |

표의 연결은 새 PHY 실험을 일곱 개 모두 실행했다는 뜻이 아니다. 이번 실제 계산은 네 shared lane이며 원래 모든 노드에 그 기여와 잔여 의무를 추적한다. 반복 비용이 큰 이전 전체 자료 계산은 exact identity가 유지되는 범위에서 재사용한다.

## 7. 검증, 발견한 실패와 수정

이론 도출, 수치 benchmark, 실제 source 계산과 구현 검증은 서로 다른 근거다. 문헌이 보증하는 범위도 별도로 유지했다.

- **DERIVED:** typed finite-z response, mag Jacobian, 공동 selection normalization, Hermite 잔여상계, homogeneous positional variation, observer solid-angle factor, shared angular response와 상쇄.
- **NUMERICALLY_CHECKED:** 명시한 Milne/Kasner/FLRW/비축 Bianchi I oracle, full CF4 perturbation·Bessel subset, real Gaia refit/SVD, footprint 독립 membership와 해상도 변화.
- **IMPLEMENTATION_VERIFIED:** 범위별 pytest와 실제 입력 실행. 최종 command·exit·elapsed·hash는 [VALIDATION.json](VALIDATION.json)에 기록한다.
- **UNRESOLVED / BLOCKED:** calibration·selection·AGN/LSS·독립 stress/flux·native transfer 등의 실제 입력/모형, 및 그것에 의존하는 과학 수락.
- truncated-rapidity marginal과 angular kernel은 **선언된 sensitivity model**이다. 관측적으로 교정된 참 법칙으로 표시하지 않는다.

한 번의 독립 C9 검토에서 다음 세 경계 사례를 발견하여 같은 수정 묶음에 처리했다.

1. CF4 \(\sigma=0\) 행: deterministic zero 모멘트가 정의되는데 helper가 거부했다. zero/positive 혼합을 지원하고 음수·비유한 분산은 거부하도록 수정했다. full 35,970-row 재실행 결과는 producer SHA를 제외하면 전 수치가 동일했다.
2. 광학 \(z=10^{-15}\): root 절대 오차 때문에 관측자 vertex로 조용히 축약되었다. 이를 재현한 regression과 root 처리를 수정했다. 수정 후 거리는 해석적 값과 상대오차 2×10^-13 이내이며 parity는 +1이다. 기존 540개 거리의 수정 전후 최대 상대차는 D_A 1.215×10^-13, D_L 1.239×10^-13이었다. 표현 불가능한 방출 사건은 명시적으로 거부한다. 상세 receipt는 OPTICAL_EXECUTION.md에 있다.
3. Gaia 단위 rescaling: eigenvalue의 절대 floor가 작은 단위에서 rank를 바꾸었다. 상대 eigenvalue cut와 zero covariance 처리를 분리했다. \(10^{-21},1,10^{21}\) 단위 배율 회귀를 추가했고 실제 rank 47·scenario 수치는 유지되었다.

독립 CF4 quadrature의 첫 시도는 endpoint에서 CDF가 roundoff로 경계를 넘으며 실패했다. 같은 rapidity endpoint-gap 적분변수에서 하한을 10^-12로 옮겨 실제 차이를 검산했다. 이 비교에는 유한 구간 절단이 포함되며 인증된 quadrature 오차 상계는 아니다. 이 실패는 독립 검사 스크립트의 수치 경계 문제로 보존하며 생산 코드의 물리 실패로 분류하지 않는다. Wolfram context 도구의 internal error도 기록하고, 이후 evaluator의 한정된 계산만 CAS 근거로 사용했다. 4축 CAS 전체 인증은 수행하지 않았다.

최종 통합 실행에서 범위 테스트 43개가 5.04초에 통과했고, 원래 strict-authority 검사 32개가 통과했다. preparation identity는 exit 0, SQ-CF4 science entry는 D01/D02/M01/A01 때문에 의도한 exit 3이었다. 검증 중 code/test/result SHA는 모두 유지되었다.

최종 DAG 검증은 graph/source identity 검증이다. 이를 GR model 승인이나 60개 과학 node의 완료로 읽지 않는다.

## 8. 다음 계산을 위한 확정된 인계

SQ-CF4를 다음 진입점으로 유지한다. 우선순위는 다음 의존관계에 따른다.

1. 준비된 20,927,710-byte upstream subset을 실제 intake하여 exact ID·단위·group-level calibration과 CF4 join을 확인한다. 제공되지 않는 rejected denominator와 joint calibration law는 계속 분리한다.
2. 새 비선형 관측량 연산자를 유지하면서 low/high-k를 실제 tomography covariance에 투영한다. 단일 source 분산 비율을 그 결과로 대체하지 않는다.
3. Jacobi module 위에 position drift를 구성하여 SQ-OPTICAL의 아직 비어 있는 proper-motion 전달을 계산한다. finite-z frame과 실제 background를 동일하게 유지한다.
4. LoTSS valid-weight/RMS 내부 support를 받아 외곽 exposure를 과학용 유효 exposure로 확장하고, flux/size/SED/LSS를 함께 다룬다.
5. Gaia angular field의 parameters를 release-specific source evidence에 연결하고 실제 proper-motion transfer와 공동 covariance를 검증한다. singular nullspace를 임의 precision으로 채우지 않는다.

이는 6차 주기를 실행했다는 기록이 아니라 이번 결과를 이어받을 구체적 인계다. 현재 막힌 science entry는 미충족 의무를 출력하고 종료 코드 3을 낸다. 자료 준비·현재 scoped 계산·수락된 과학 claim의 상태가 코드에서 분리된다.

## 일차 문헌과 공식 자료

- Tully et al., Cosmicflows-4: [arXiv:2209.11238](https://arxiv.org/abs/2209.11238), [DOI:10.3847/1538-4357/ac94d8](https://doi.org/10.3847/1538-4357/ac94d8). 발행된 자료·방법·전역 상호교정의 출처이며, 누락된 upstream joint law를 제공받았다는 뜻은 아니다.
- Howlett et al., SDSS peculiar-velocity catalogue: [DOI:10.1093/mnras/stac1681](https://doi.org/10.1093/mnras/stac1681), [Zenodo v1.1.0](https://zenodo.org/records/6824749). 정확한 파일·checksum·genealogy는 ACQUISITION_SOURCES.md의 실제 응답으로 고정했다.
- Davis & Scrimgeour, peculiar velocities: [arXiv:1405.0105](https://arxiv.org/abs/1405.0105). 관측 적색편이와 peculiar velocity 관계에 대한 일차 출처.
- Fleury, Pitrou & Uzan, Light propagation in a homogeneous and anisotropic universe: [arXiv:1410.8473](https://arxiv.org/abs/1410.8473). Bianchi I의 optical/Jacobi 결과다. 일반 homogeneous commutator를 포함하는 이번 구현의 직접 유도는 THEORY_OPTICAL.md에 있으며 이 논문이 모든 Bianchi family를 보증한다고 주장하지 않는다.
- Gaia Collaboration, Gaia-CRF3: [arXiv:2204.12574](https://arxiv.org/abs/2204.12574). frame·angular systematics와 source sample의 일차 출처. R99 kernel은 별도의 sensitivity model이다.
- [6dFGSv 공식 자료](https://www.mso.anu.edu.au/6dfgs/vfield/3dvfield.html), [LoTSS DR3 mosaic table](https://vo.astron.nl/tableinfo/lotss_dr3.mosaics), [LoTSS DR3 release](https://lofar-surveys.org/dr3.html). provider 원 응답과 조회 시점은 inputs/source_receipts.json에 보존했다.
