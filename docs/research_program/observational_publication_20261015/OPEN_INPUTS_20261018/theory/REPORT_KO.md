# 공통 angular calibration을 닫는 유한 anchor 사상

2026-10-18. Owner `htt`; scope `R4–R8`, 유한 회귀·부분식별·공개 geometric-distance 표본의 설계 계산. `C0 / CONDITIONAL / DIAGNOSTIC_ONLY`, transfer `none`. 기준 commit `4a68995507bf8e672b2551d9030f3ad9f0d2152e` (PR #560). 요청 runtime `gpt-6-astra/xhigh`, 실제 관찰 `UNKNOWN`. 부모가 fresh review와 publication을 담당한다. Native solver/ODE, raw CF4 재fit, physical status 승격은 수행하지 않았다.

**새 결과는 공통 angular calibration을 측정하기 위해 어떤 방향과 정밀도가 필요한지 계산 가능한 조건이다.** 공개된 여섯 megamaser 방향의 실제 design에서 monopole와 quadrupole를 자유롭게 두면 dipole의 남는 rank는 0이다. 그러나 세 개의 추가 방향을 명시적으로 구성하면 전체 9개 계수의 rank가 9가 된다. 원 H02의 선택된 `nx` interval을 기준으로 이 설계에 필요한 anchor 정밀도를 계산했다. 이는 알려진 회귀 대수를 기존 HTT 자료에 적용한 좁은 결과이며 새로운 GR 정리나 일반적 관측 불가능성 주장이 아니다.

## 1. 선택한 구성과 원본 연결

R4에서 두 경로를 비교했다. (a) finite-z optical 잔차를 물리 shear에 곧바로 연결하면 아직 source-qualified response와 peculiar-flow law가 필요하다. (b) 동일 대상의 optical-distance와 geometric-distance 차이는 Hubble 법칙을 사용하지 않고 공통 angular calibration을 직접 제한할 수 있다. 여기서는 (b)를 끝까지 전개했다. 이것이 (a)의 물리 사상을 대체하지는 않는다.

H02가 정의한 모형은 각 좌표에서 `b_mw=theta_w+eta+gamma_m+epsilon_mw`다. 같은 대상의 두 방법 차이는 `gamma_m-gamma_k`를 남기며 `theta_w,eta`를 지운다. 그러므로 relative calibration을 더 정확히 얻는 일과 common eta를 anchor하는 일은 서로 다른 측정이다. 방법-중첩 graph의 단순 연결성만으로 8개 angular 계수의 relative calibration이 식별된다는 주장도 하지 않는다. 각 edge의 방향 design이 충분해야 한다.

| 재사용 원본 | 실제 재사용 식·내용 | 이번 증가분 |
|---|---|---|
| dossier §12.2, p.12 | `J_surv=P_(Im K)^perp J`, rank difference | common calibration anchor에 실제 `J=N`, `K=[1,Q]`를 대입 |
| dossier §13, pp.12–13 | radial affine design과 duplicated-response kernel의 구분 | 같은 대상 차이는 물리 field를 지우므로 cross-method와 absolute-anchor의 역할을 분리 |
| dossier §23.3, pp.21–22 | `A_anch=P_perp W J L`; 가역 normalization은 rank를 만들지 않음 | 새로운 anchor **관측 행**을 추가하여 실제 rank를 늘리는 구성 |
| H02 report + `h02_actual_centers.json` | raw Cartesian 8개 basis, working covariance, 공통 eta gauge | exact frozen JSON의 base coefficients/covariance를 `h02_base_summary.json`에 보존; nx interval 목표를 계산에 연결 |
| S02 report | 한 창의 erasure rho 및 공통 angular g+depth residual eta의 minimax | arbitrary angular function과 finite l≤2 calibration class가 다름을 보존 |

S02 point-fit erasure radius `.0402–.0773 mag`는 임의 방향 함수의 sup bound다. 이번 dipole coefficient bound와 동일한 단위 mag를 갖지만 서로 같은 수량은 아니다. S02 수치를 이 계산의 임계값으로 바꾸지 않았다.

## 2. 관측 정의, frame와 단위

방향 `n=(cos dec cos RA, cos dec sin RA, sin dec)`는 equatorial Cartesian이다. H02와 같은 basis를 쓴다.

Frozen `h02_actual.py` blob `e75949a903c86c1ffb257e19bc0017c58dceccb2`, `overlap_diagnostics`는 table3 `RAdeg/DEdeg`로 이 벡터를 구성한 뒤 selected directions와 `atol=2e−12`로 비교하며 오류 문구도 `raw/selected J2000 geometry mismatch`다. 따라서 H02 nx를 Galactic x로 바꾸지 않았다. 원문 excerpt는 `H02_FRAME_EVIDENCE.json`에 보존했다.

`q(n)=(nx²−nz², ny²−nz², 2nxny, 2nxnz, 2nynz)`.

`T(qcoef)=[[q1,q3,q4],[q3,q2,q5],[q4,q5,−q1−q2]]`이므로 `nᵀTn=q(n)·qcoef`이다. 이 basis는 STF이지만 Frobenius orthonormal은 아니다. Monopole `a`, dipole `d`, quadrupole `qcoef`의 단위는 모두 mag이다. `n,A`는 무차원이다. 지표 서명 `(-,+,+,+)`를 유지하되 이번 유한 회귀에는 spacetime metric을 사용하지 않는다.

동일 대상 비교 자체로 방법별 relative angular calibration이 사라지지는 않는다. `X_i=(n_i,q(n_i))`, common calibration `eta=(d,qcoef)`이고 실제 calibration contributor가 m(i)라면 raw 비교는

`r_raw,i = mu_catalogue,i − mu_geometric,i = a + X_i eta + X_i gamma_m(i) + e_i`. (1a)

즉 raw 자료는 **eta+gamma_m**를 측정한다. 서로 같은 catalogue에 속한다는 조건만으로 gamma_m=0이 되지 않는다. H02의 FP/TF/SN/OTHER는 pooled catalogue의 partition이므로 이 label을 실제 raw calibration contributor로 자동 대입하지도 않는다. Contributor mapping이나 알려진 mixture weights를 확보해 `G`를 구성해야 한다. 방법별 미지 scalar offset이 남으면 그것도 추가 nuisance column으로 넣는다.

이 문서의 기존 방향 rank와 정밀도 숫자는 gamma_m와 방법별 상대 scalar offset을 **정확히 알고 뺀 ideal case**(또는 명시적으로0에 고정한 경우)다. 그때

`r_corr = r_raw − G gamma_known = A p + e`, `p=(a,d,qcoef)`,
`r_corr,i = a + n_i·d + q(n_i)·qcoef + e_i`. (1b)

Gamma를 추정값으로 보정하면 `r_corr=r_raw−G gamma_hat=A p+G Delta_gamma+e`이므로 남는 불확실성을 아래 식(3b)에 반드시 전달한다. 실제 anchor의 gamma가 알려졌다는 관측 결과는 현재 없다.

독립 reviewer가 제시한 정확한 falsifier는 `s_x=.010`, `eta_x=.015`, `gamma_m,x=−.015`, 허용 bound `delta=.020 mag`다. Exact raw anchor는 `eta_x+gamma_m,x=0`이지만 `theta_x=s_x−eta_x=−.005`다. Raw0을 eta0으로 읽으면 theta=.010이라는 잘못된 양수 판정을 얻는다. Gamma를 알고 `r_corr=0−(−.015)=.015`로 고치면 음수 theta가 정확히 복원된다. 이 반례와 correction을 별도 test에 넣었다.

`mu_geometric`과 catalogue modulus는 같은 거리 정의와 observer convention이어야 한다. Maser가 제공하는 것은 angular-diameter distance `D_A`다. 투명한 metric propagation/광자수 보존의 distance duality를 채택하고 luminosity-distance modulus와 비교한다면

`mu_geom,L=25+5log10(D_A/Mpc)+10log10(1+z_observed)`.

이때 z는 그 observer/source pair의 실제 redshift다. `z_CMB`를 보정 없이 집어넣거나 `D_A`를 곧바로 `D_L`이라 부르면 안 된다. CF4 method별 published modulus가 어떤 거리 정의를 쓰는지 먼저 연결해야 한다. 본 계산은 이 비교 잔차를 관측했다고 가정하지 않고 **공개 방향과 거리 precision의 design**만 계산한다. Peculiar velocity를 별도 Hubble-law noise로 추가하지도 않았다. Hubble-law를 쓰지 않는 same-object 차이의 장점이며, 실제 modulus convention·frame 변환 의무는 남는다.

NGC4258는 H02의 z≥.01 cut 밖이다. 그 보정이 같은 angular 함수로 고z selected catalogue에 전달된다는 것은 추가 가정이다. 기존 CF4 zero-point 체계에 이미 들어간 calibrator라면 independent validation으로 재사용할 수 없고, joint fit/cross-covariance 또는 상류 보정에서 제외한 별도 관측이 필요하다.

## 3. 정확한 식별·부분집합 lemma와 증명

임의의 유한 실수 design을 `A=[Z,N]`로 쓰자. `Z`는 nuisance (여기서는 monopole+STF quadrupole), `N`은 목표 dipole다. 양의 definite 측정 covariance가 주어지면 먼저 실제 whitener를 곱한다. Covariance가 주어지지 않은 이번 rank 계산은 unweighted다.

**Lemma A (nuisance quotient).** 목표 dipole 전체의 noiseless 식별 필요충분조건은

`ker(P_Zperp N)={0}`, 즉 `rank[Z,N]−rank Z=3`. (2)

그보다 낮은 rank일 때 식별 가능한 dipole의 선형 함수는 `row(P_Zperp N)`다. 특정 `l·d`의 조건은 `l ⟂ ker(P_Zperp N)`이다.

증명: 두 parameter 상태가 같은 관측을 주는 조건은 `Z delta_u+N delta_d=0`이다. 이는 `N delta_d∈Im Z`와 동치이고, 정확히 `P_Zperp N delta_d=0`다. 이 kernel에서 소멸하는 선형 함수만 두 상태에 같은 값을 준다. 직교분해에 의해 rank identity가 따른다. 이는 유한 회귀의 조건부 lemma다.

**Lemma B (sharp residual-ball projection).** 관측 `b`, 선언된 오차 radius `R≥0`에 대해

`S_R={p: ||A p−b||_2≤R}`,
`p0=A^+b`, `r0=||(I−AA^+)b||_2`.

`S_R`은 `R<r0`일 때 공집합이다. Nonempty이고 목표 `l`이 `row(A)`에 있으면 그 목표의 exact interval은

`lᵀp0 ± sqrt(R²−r0²) ||(A^+)ᵀl||_2`. (3)

`l∉row(A)`이면 양방향 무한 interval이다. R은 deterministic bound로 선언할 수 있다. Confidence-set 의미는 올바른 오류법칙으로 R을 별도 정당화한 경우에만 붙는다.

증명: `p=p0+h+k`, `h∈row(A)`, `k∈ker A`로 분해한다. Least-squares normal equation에 의해
`||Ap−b||²=||Ah||²+r0²`.
`l`에 nullspace 성분이 있으면 k를 배수로 늘려 target을 임의로 이동시킨다. 그렇지 않으면 `lᵀh=((A^+)ᵀl)ᵀ(Ah)`이고 Cauchy–Schwarz가 (3)을 준다. `Ah`를 `(A^+)ᵀl` 방향으로 선택하면 equality를 달성한다. 이 벡터는 `Im A`에 있으므로 실제 h가 존재한다. R=r0에서 estimable target은 한 점이며 nullspace target은 계속 무한이다.

**불확실한 방법별 보정의 전파.** Relative calibration uncertainty가 `Delta_gamma∈Gamma`이면 실제로 투영할 집합은

`S={ (p,Delta_gamma): ||A p+G Delta_gamma−r_corr||≤R, Delta_gamma∈Gamma }`. (3a)

H02에서도 같은 gamma를 쓴다면 두 자료의 제약을 **동일 gamma 변수**에 함께 적용한다. 서로 독립인 보정 posterior처럼 곱하지 않는다. `l∈row(A)`, `w=(A^+)ᵀl`, `|Delta_gamma_j|≤delta_j`의 symmetric box에서 다음은 항상 성립하는 outer halfwidth다.

`|lᵀp−lᵀA^+ r_corr| ≤ R||w||₂ + Σ_j delta_j |(Gᵀw)_j|`. (3b)

증명: `Aᵀw=l`에 의해 target error는 `−wᵀe−wᵀG Delta_gamma`다. 첫 항에 Cauchy–Schwarz, 둘째 항에 box support function을 적용한다. 임의 Gamma에서는 뒤 항을 support bounds `h_Gamma(±Gᵀw)`로 바꾼다. 식(3a)의 잔차 호환 제약까지 강제하면 (3b)는 보수적일 수 있으므로 이 경우 sharp라고 부르지 않는다. Gaussian noise planning factor를 쓸 때도 보정 box 항은 없어지지 않는다.

구체적으로 9개 anchor가 모두 하나의 방법에 속하고 `|Delta_gamma_x|≤.02 mag`만 안다면, 거리가 정확해도 common eta_x의 `.02 mag` halfwidth가 남는다. `eta_x→eta_x+t`, `gamma_x→gamma_x−t`가 같은 관측을 주기 때문이다. 생성 JSON의 이 값은 **단일방법 scenario**이며 실제 anchor의 method assignment를 얻었다는 뜻이 아니다. 이 scenario는 H02 목표 하한 `.009956 mag`보다 보정 불확실성 자체가 크므로 아래 ideal precision 숫자를 실제 충분조건으로 사용할 수 없다.

**H02 연결.** H02가 `s_x=theta_x+eta_x∈[L,U]`를 제공하고 anchor가 `eta_x∈[a−rho,a+rho]`를 제공한다면 `theta_x∈[L−a−rho,U−a+rho]`는 항상 outer interval이다. 두 집합을 독립적으로 조합할 수 있는 Cartesian compatibility model에서는 sharp하다. 상관된 joint calibration law가 있으면 이를 outer bound로만 사용한다. `theta_x>0`를 이 모형에서 보장하려면 `L>a+rho`이면 충분하다. 두 confidence 사건의 failure probabilities는 독립성 없이 합으로 bound된다. 각각 95%라고 해서 joint95%가 되는 것은 아니다.

여기 theta는 선언한 additive calibration 모형 안의 latent apparent coefficient이며 expansion/shear/tilt로 식별된 물리량이 아니다.

## 4. 공개 여섯 방향에서 실제 계산

[Pesce et al. 2020, Table 1](https://arxiv.org/abs/2001.09213)의 6개 geometric distance를 썼다. 첫 5개 방향은 [Villaraos et al. 2022, Table 1](https://doi.org/10.1093/mnras/stac2973)의 J2000 위치 및 그 표에 명시된 MCP 원전 계보, NGC4258 방향은 [NASA object metadata](https://science.nasa.gov/asset/hubble/ngc-4258/)를 썼다. NASA의 rounded position을 정밀 astrometric 재분석으로 취급하지 않는다. 같은 celestial position에 관한 minute-scale perturbation에도 아래 rank가 안정적이다.

| object | RA | Dec | D_A [Mpc] | linearized symmetric modulus scale [mag] |
|---|---|---|---:|---:|
| UGC3789 | 07:19:30.9490 | +59:21:18.3150 | 51.5 | .179199 |
| NGC6264 | 16:57:16.12780 | +27:50:58.5774 | 132.1 | .312324 |
| NGC6323 | 17:13:18.03991 | +43:46:56.7465 | 109.4 | .565694 |
| NGC5765b | 14:50:51.51950 | +05:06:52.2502 | 112.2 | .101606 |
| CGCG074-064 | 14:03:04.457746 | +08:56:51.03483 | 87.6 | .187153 |
| NGC4258 | 12:18:57.5 | +47:18:14 | 7.58 | .031512 |

마지막 열은 `s_mu=(5/ln10)(sigma_plus+sigma_minus)/(2D)`라는 **planning scale**이다. 비대칭 16/84 percentile을 Gaussian variance라고 검증한 값이 아니다. 작은 fractional-error approximation은 특히 NGC6323에서 거칠다. Optical comparison noise/covariance를 더하지 않은 조건부 계산이므로 실제 정밀도 평가로 쓰지 않는다.

`rank A=6`, `rank Z=6`, `rank[P_Zperp N]=0`. 여기서 수치 rank는 rank difference로 계산했다. Projection residual의 roundoff를 작은 양의 singular value로 세지 않는다. `s_min(Z)=.09349940592`, explicit `C=−Z⁻¹N`에 대해 `max|ZC+N|=1.5266e−16`이다. 임의 dipole 변화 v에 nuisance 변화 Cv를 주면 동일 6개 anchor 예측이 나온다. 표본이 부족하다는 말 대신 실제 witness를 `anchor_arrays.npz`에 보존했다.

각 방향 오차가 1 arcmin 이하라는 perturbation scenario에서는 `||delta Z||≤2 sqrt(30) epsilon=.00318652`다. 각 quadratic-form basis matrix의 operator norm이1이므로 row 변화가 `≤2 sqrt(5)epsilon`; 여섯 행의 Frobenius bound와 Weyl 부등식을 적용했다. 따라서 `s_min(Z')≥.09031>0`. 이는 astrometric 오류를 추정한 결과가 아니라 rounded-coordinate 선택에 대한 안정성 확인이다.

Quadrupole을 **고정하고 gamma_m도 정확히 알고 제거한 좁은 모형**에서는 6×4 dipole+monopole design이 full rank다. 위 planning scales를 독립 Gaussian standard deviations로 임시 채택했을 때 dipole 계수 standard-error design은 `(.317063,.328993,.354785) mag`다. 현재 maser 거리 precision만으로 H02의 `.01 mag` 수준 common-angular 목표를 정밀 측정했다는 결론은 나오지 않는다. 이는 관측 calibration estimate도, 6개 자료를 이용한 fitted posterior도 아니다.

## 5. ambiguity를 실제로 닫는 constructive augmentation과 목표 정밀도

**전체9개 unknown** (monopole1+dipole3+STF5)을 모두 식별하려면 최소9개 scalar rows가 필요하다. **Dipole만** 식별하는 일반적 최소 행 수가9라는 뜻은 아니다. 세 개의 선형독립 축 u_j와 그 antipodes −u_j의6개 행에서는 `r(u_j)−r(−u_j)=2u_j·d`라서 자유로운 even monopole/quadrupole이 소거되고 dipole3성분이 식별된다. 전체9계수의 식별은 여전히 안 된다. 이 반례를 새 test로 실행했다. 이 parity 논증 역시 gamma가 제거된 모형에 관한 것이며 unknown method-specific dipole는 함께 제거되지 않는다.

이번 **고정된 기존 maser6행**은 nuisance rank가 이미6이므로 k행을 추가해 얻는 dipole quotient rank는 `≤k`다. 따라서 이6행을 그대로 유지하며 자유로운 monopole+quadrupole 아래 dipole3성분을 모두 식별하려면 적어도3행 추가가 필요하다. 여섯 기존 행의 nullspace orthonormal basis를 K라 하고 세 추가 행을 B라 하면

`det([A;B])² = det(A Aᵀ) det(BK)²`. (4)

증명: `R^9=row(A)⊕ker(A)`의 orthonormal basis로 우측 좌표변환하면 위 stacked matrix는 block lower-triangular이고, 기존6행의 Gram determinant가 첫 block determinant의 제곱이다. 나머지가 BK다. 따라서 작은3×3 determinant만으로 candidate triple을 비교할 수 있다.

고정된 64-point Fibonacci equal-area candidate grid의 모든 `C(64,3)=41664` triple을 비교했다. 선택 index는 `(37,39,56)`이며 새 방향은

`(.66188669,.72963347,−.17187500)`,
`(.77437229,−.58772096,−.23437500)`,
`(−.49591014,.40974565,−.76562500)`.

이는 **관측된 추가 galaxy가 아닌 prospective design points**다. 실제 공개 대상 탐색은 이 방향 근처에 독립 geometric-distance와 같은 optical calibration을 공유하는 대상이 있는지 확인하는 작업이 된다. 이 유한 grid에서는 D-optimal이며 전 구면 전역 최적을 주장하지 않는다. 추가 후 rank9, 최소 singular value `.09633574407`다. `x,y,z` dipole 목표의 단위 L2오차 확대율은 `(2.88787940,4.00768472,5.61942657)`이다.

H02의 Gaussian-working-law, relative calibration bound delta=.02인 base nx outer interval `[.0099562061,.0110329350] mag`를 설계 목표로 재사용한다. **Anchor의 gamma_m가 정확히 알려져 제거되고** common-anchor 중심이0이라는 예시에서 x의 strict positive lower bound를 보존하려면 deterministic L2 residual budget이 `.00344758376 mag`보다 작으면 충분하다. 이 bound는 9개 anchor 전체 residual의 Euclidean norm이며 대상 하나당 bound가 아니다. 불확실한 gamma에는 `R||w||+Σ delta_j|(Gᵀw)_j|<L−anchor_center`가 대응하는 보수적 충분조건이다.

Gamma_m가 정확히 알려진 ideal case에서 독립·동일 Gaussian noise sigma와 사전 지정된 x좌표의 1.96-sigma halfwidth로 **설계상 번역**하면 다음과 같다.

| 모형 | x error amplification | 필요한 per-anchor sigma |
|---|---:|---:|
| 기존6방향, quadrupole 고정 | 2.35509201 | <.00215689959 mag |
| 9방향 구성, quadrupole 자유 | 2.88787940 | <.00175897130 mag |

이 숫자는 기존6개 측정 모두까지 이 정밀도로 개선한다는 균일 precision scenario다. 새3개만 매우 정확히 측정하면 같은 숫자가 자동 성립하지 않는다. 1.96은 x 한 좌표의 Gaussian planning factor이며 H02와 결합한 joint confidence 보장이 아니다. 목표 좌표·delta·law가 바뀌면 요구 정밀도도 다시 계산한다.

## 6. 검증, 문헌 대비, R8 판정

Fitted nuisance 제거는 [Lovell 1963](https://doi.org/10.1080/01621459.1963.10480682)의 partial regression 계열이며 식(2)–(4)는 표준 선형대수의 직접 증명이다. [Padmanabhan et al. 2008](https://arxiv.org/abs/astro-ph/0703454)은 relative와 absolute photometric calibration을 분리한다. 그 관측 문제와 여기의 거리-modulus calibration은 같지 않지만, overlap 정보만으로 absolute gauge를 정하지 않는다는 설계 원리는 재사용할 수 있다. 본 contribution은 이 일반 이론의 발견이 아니라 H02 basis·공개 maser geometry·실제 conditional 목표를 연결한 실행이다.

Wolfram context를 먼저 호출한 뒤 exact symbolic STF identity와 6방향 nuisance cancellation을 계산했다. 첫 evaluator는 보호 심볼 `N,C`에 대입해 오류가 났고 이를 보존했다. 일반 변수명으로 고친 한 번의 targeted repair는 `STF difference=0`, `rank Z=6`, `ZC+N=0` 6×3 exact matrix, `rank[Z,N]=6`, `det Z=3`을 반환했다. 이는 rational/surd 대표 방향의 exact identity이며 실제 galaxy 좌표의 exact CAS 증명으로 둔갑시키지 않는다.

기존8개 tests와 targeted review repair의4개 tests, 총 **12개 tests가 모두 PASS**했다. 새 검증은 antipodal6행의 dipole 식별 반례, 단일방법 gamma의 exact alias와 `.02 mag` uncertainty floor, 두방법 box uncertainty의 support bound 달성, reviewer의 raw-anchor false-positive와 known-gamma correction 반례다. 기존 검증은 source-direction gauge witness와 unbounded target; sharp endpoint attainment; nonzero residual budget; full inverse 대 independent centered Schur covariance; augmentation determinant identity; rotation invariance; duplicate/equatorial rank counterexamples; STF tensor/basis normalization이다. PNG의 ideal-known-relative-calibration 표기도 수정해 생성했다. Scientific null simulations와 raw catalogue 재fit은 NOT_RUN이다.

```bash
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 anchor_bridge.py
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 test_anchor_bridge.py
/opt/codex/runtimes/codex-primary-runtime/dependencies/python/bin/python3 plot_anchor_bridge.py
```

위 cwd는 이 report가 있는 worker directory다. Repo `.venv`는 이 read-only intake snapshot에 없었다. 설치나 환경 변경 없이 제공된 primary-runtime Python을 명시적으로 사용했고 version은 JSON에 저장했다. Historical CUH-G 재등록/telemetry 설치는 현재 native policy에 따라 하지 않았다.

| claim | owner/status | 근거·한계 |
|---|---|---|
| 식(2)–(4)의 유한 regression result | htt / DERIVED / C0 | 명시된 선형 calibration class, 증명·CAS·수치 falsifier |
| 공개6방향의 quotient rank0와 witness | htt / CONDITIONAL / C0 | 방향 design의 수치 실행·perturbation bound; calibration 잔차 측정 아님 |
| rank9 prospective augmentation | htt / CONDITIONAL / C0 | 명시된 가상 추가 방향, 유한 grid exhaustive search |
| 정밀도 요구 숫자 | htt / DIAGNOSTIC_ONLY / C0 | gamma_m가 정확히 알려진 ideal deterministic/Gaussian scenario; 불확실 gamma는 식(3a/b) 추가; physical theta 아님 |
| H02 independent calibration validation, S02 physical sector map | HOLD 유지 | matched optical/geometric residual과 upstream independence/transport, physical response는 여전히 미공급 |

R4 construction, R5 proof, R6 author-side dimensions/limits/counterexamples, R7 light computation, R8 scope decision을 수행했다. 부모의 독립 reviewer가 발견한 raw residual의 gamma_m 누락과9행 최소조건의 모호함은 이 targeted repair로 수정했으며 final closeout은 기존 reviewer/부모 담당이다. 이 문서가 original acceptance를 바꾸거나 scientific node를 완료로 선언하지 않는다. 다음 실제 행동은 raw-calibration genealogy와 실제 contributor mapping을 지킨 matched distances 및 relative calibration bounds를 (1a), (3a)에 넣고, 같은 gamma를 H02와 공유한 joint feasible set에서 목표를 투영하는 것이다. Gamma가 정확히 보정된 때만 (1b), (3)으로 단순화한다. 이 단계는 solver 없이 가능하다.
