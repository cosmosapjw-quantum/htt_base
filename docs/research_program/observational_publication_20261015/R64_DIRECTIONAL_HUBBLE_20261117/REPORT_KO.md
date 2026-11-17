# R64 — 적색편이·방향 의존 Hubble factor: 실제 CF4 정보 회복과 보정 민감도

기준 commit `33d87dd3e4a787e477327d37ee00b40e790211c9`. 대상은 P3의 redshift- and direction-dependent Hubble factor 한 가지다. 한 번의 순차적 10단계 이론·코딩 연구이며, 자동 후속 루프와 local coding-agent용 프롬프트는 생성하지 않는다. 아래 수치는 `RESULTS/INTERPRETATION_SUMMARY.json`과 그 파일이 지정하는 실제 carrier에서 읽었다.

## 1. 연구 판정

이번 작업의 실제 진전은 기존 36차원 압축의 한계를 확인한 뒤, 이미 계산되어 있던 **방법별 통계량과 교차 공분산을 회수하여 68차원 실험으로 확장하고 삼차 모형의 rank를39/39로 회복한 것**이다. 따라서 초기에 발견한36/39 비식별성을 CF4 원자료의 근본적인 측정 불가능성으로 주장하지 않는다. 같은 catalogue를 다른 방법으로 압축했을 때 보존되는 정보가 달라진다는 실제 계산 결과다.

동시에 정보 회복은 물리적 Hubble 측정의 완성을 뜻하지 않는다. 방법별 정보를 보존한 실험에서는, 원래36행에서 충분해 보였던 공통 거리장이 일부 방법 구성에서 부적합해진다. 방법별 angular zero-point nuisance를 허용하면 적합도가 크게 개선되지만, 그 개선과 미분량의 정밀도는 방법 구성에 의존한다. 관측 자료가 추가적인 radial angular evolution을 요구한다는 증거는 현재의 유한 Gaussian 평균모형들에서 나오지 않았다.

따라서 논문의 중심 후보는 **CF4 방향별 거리–적색편이 추론에서 회복 가능한 radial information, source dependence, calibration quotient와 nonlinear distance-rate uncertainty**다. 새로운 우주론적 비등방 팽창 검출, 일반적인 물리적 H(z,n) 복원 또는 CF4의 보편적 no-go는 주장하지 않는다. 현재 P3 제출 판정은 **NOT_READY_TO_SUBMIT**이다. 과학 결과·코드의 scoped completion과 저널 투고 준비를 구분한다.

## 2. 기존 연구를 어디까지 재사용했는가

H01/H03의 네 관측 적색편이 창과 monopole·dipole·STF5, H02의 실제 source join·method/sky 비교, R32/R37의 optical/Hubble 해석, R54의 로그 거리 추정량·correlated peculiar-velocity covariance, R58의 full tensor likelihood, R61의 calibration-invariant depth contrast, R63의 실제 published-redshift chart 처리를 이어받았다. 관련44개 현재 source의 SHA256·baseline blob와 읽은 범위는 `REVIEW/r64_history_sources.json`에 있다. 과거573개 PR inventory와 관련 branch refs를 재사용했지만, 그 inventory를 현재 GitHub의 모든 PR을 새로 읽었다는 주장으로 바꾸지 않았다.

원래 입력은 CF4 **35,970개 group**, 관측 적색편이 범위 **0.010003587–0.099999180**, 네 겹치는 Gaussian 창 중심 **0.025,0.04,0.06,0.08**, 폭0.012다. 초기 관측 벡터의 **36개 좌표**는 네 블록 `[monopole,polar3,STF5]`이며, R58의32차원 carrier에서 빠졌던 네 monopole을 복구했다. source catalogue, covariance 및 기존 operator를 새 데이터처럼 다시 생성하지 않았다.

기본 실제 likelihood는 `white + inherited Planck18 linear-z0 peculiar-velocity body`다. 실제 shared calibration/group covariance, empirical selection law 또는 모든 distance method의 flux/frame response까지 검증된 관측 법칙은 아니다. 모든 아래 p와 신뢰영역에는 이 조건이 붙는다.

## 3. Hubble factor의 정의와 직접 유도

Signature는(-,+,+,+), 관측 방향 n은 observer→source, c=299792.458km/s를 유지한다. 다음 세 물체를 구분한다.

\[
\mathcal H(x,n)=\Theta/3+\sigma_{ab}n^an^b-A_an^a/c,
\qquad
H_D(z,n_o)=\frac{c}{\partial_z[D_L(z,n_o)/(1+z)]},
\qquad H_W=\text{actual finite-window estimator}.
\]

첫 식은 지정한 congruence의 null contraction이고, 두 번째는 고정된 관측 방향에서 거리 함수의 미분으로 정의한 rate이며, 세 번째는 실제 선택·가중·보정 연산자의 결과다. 일반 시공간에서는 같은 대상이 아니다. 방향별 congruence Hubble 계수와 일반 cosmography의 선행 정식화는 [Heinesen,2010.06534v2](https://arxiv.org/html/2010.06534v2)를 따르고, 유한 polynomial fit을 실제 local Taylor coefficient와 동일시하지 않는 제한은 [Koksbang,2412.12637v3](https://arxiv.org/html/2412.12637v3)와 함께 검토했다.

Past-directed affine parameter lambda를 길이 단위로 두고, ell=E(-u+n), E_o=1인 같은 emitter/observer congruence, geometric optics, photon conservation 및 regular ray branch를 가정하면

\[
\frac{dz}{d\lambda}=\frac{(1+z)^2\mathcal H}{c},
\qquad D_{A,\lambda\lambda}=-\mathscr F D_A,
\qquad \mathscr F=|\sigma_{\rm opt}|^2+\tfrac12R_{ab}\ell^a\ell^b.
\]

Vertex 조건은 D_A(0)=0,D_{A,lambda}(0)=1이다. Etherington relation으로 R=D_L/(1+z)=(1+z)D_A이므로

\[
R_z=D_A+\frac{cD_{A,\lambda}}{(1+z)\mathcal H},\qquad
H_D=\frac{(1+z)\mathcal H}{D_{A,\lambda}+(1+z)\mathcal H D_A/c}.
\]

따라서 적절한 vertex matching에서는 H_D→Hcal_o이지만, 유한 깊이에서는 optical solution이 필요하다. 실제 redshift-only catalogue correction은 이 congruence/flux matching의 대체물이 아니다.

이는 단순한 입력 부족 선언에 그치지 않는다. 광학 source를 제공하면 물리적 rate를 구성할 수 있는 식도 정리했다. Y=Hcal²라 놓으면

\[
\frac12\left(R'-\frac{R}{1+z}\right)Y'+R''Y+
\frac{c^2\mathscr F R}{(1+z)^4}=0.
\]

이는 주어진 optical source와 적절한 초기값 아래 Y에 대한 선형 ODE다. 계수 R'-R/(1+z)=0인 지점, optical closure와 실제 endpoint convention은 별도 처리해야 한다. 이번 CF4 실험이 그 optical source를 측정했다는 뜻은 아니다.

**반례.** Milne의 expanding congruence에서는 physical H=H0(1+z),q=0이지만

\[
H_D=\frac{2H_0(1+z)^2}{1+(1+z)^2},\qquad
q_D=\frac{1-(1+z)^2}{1+(1+z)^2}.
\]

일반적으로 curved FLRW도 H_D=H/sqrt[1+Omega_k(H0R/c)²]이다. 이 구분은 [Clarkson–Bassett–Lu,0712.3457v2](https://arxiv.org/html/0712.3457v2)의 거리–H–곡률 관계와 일치한다. 거리 미분으로 H와q를 재구성하는 구성 자체는 [Seikel–Clarkson–Smith,1204.2832v2](https://arxiv.org/html/1204.2832v2)에 선례가 있다.

## 4. 보정에 불변인 radial observable와 구현 교정

Smooth flat reference chi'=c/H_ref, eta=ln(D_L,ref/D_L), B=H_ref chi/c에 대해

\[
\frac{H_D}{H_{\rm ref}}=\frac{e^\eta}{1-B\eta_z},
\]
\[
q_D=q_{\rm ref}+(1+z)\left[\eta_z+
\frac{B'\eta_z+B\eta_{zz}}{1-B\eta_z}\right],
\qquad B'=1+(H_{\rm ref}'/H_{\rm ref})B.
\]

양의 거리 미분을 쓰는 정의역은 D=1-B eta_z>0이다. z-independent angular shift eta→eta+a(n)는 H_D에 e^a만 곱하므로 같은 방향의 radial ratio와q_D는 함수 수준에서 정확히 불변이다. 유한 estimator의 invariance는 실제 O b(n) nuisance span에 대해서만 성립한다. 임의의 누락된 고차 angular calibration까지 제거하지는 않는다.

기존 eta_repo는 고정된 수치 단위로 ln H0를 포함한다. 따라서 eta_relative=eta_repo−ln H_ref,0이며,

\[
H_D[\mathrm{km\,s^{-1}\,Mpc^{-1}}]
=\frac{E(z)e^{\eta_{\rm repo}}}{1-E(z)\widehat\chi(z)\eta_{{\rm repo},z}}.
\]

이 normalization을 코드에 명시했다. 또한 기존 catalogue-dependent piecewise-linear quadrature table을 그대로 미분하지 않았다. 고정64점 Gauss–Legendre smooth reference로 옮기는 알려진 offset O ln(chi_smooth/chi_legacy)를 실제 관측 벡터에 반영했다. source별 최대|delta eta|는 **1.62004×10^-9**로 작지만, 이 변환을 해야 미분식과 수치 chart가 일치한다.

R63의 실제 q_pub=c ln[(1+V3k/c)/(1+Vh/c)]도 같은 O,C,X에서 first-order affine sensitivity로 전파했다. 이는 새로운 독립 observer velocity 측정이 아니다. q_pub라는 catalogue correction과 deceleration q_D는 다른 양이다.

## 5. likelihood와 tensorized five-variable framework

선택한 평균모형은

\[
\eta_{\rm repo}(z,n)=g(z)n\cdot V+
\sum_{j=0}^J P_j((z-0.055)/0.045)\,b(n)\cdot a_j,
\quad b=(1,n_x,n_y,n_z,nE_1n,\ldots,nE_5n).
\]

V3은 km/s 단위의 자유 coherent-velocity nuisance다. 현재 optical H_D image는 이 nuisance를 제외한 polynomial eta의 함수이며, 그 분해에 조건부다. 물리적 peculiar-velocity 복원이 검증되었다는 뜻은 아니다. 모형 파라미터 수는 J1=21,J2=30,J3=39다. 각 source에서 template을 계산한 뒤 X=O B_source로 만들었으며, 창 중심에서 template을 평가해 대체하지 않았다.

여기서 g(z)n·V는 **일차 속도 응답의 tangent template**이다. 이번 Gaussian 평균족에서는 계수에 물리적인 속도 prior를 가하지 않았고, 모든 source에서 |g_i n_i·V|≪1 또는 고차 나머지가 작다는 유효영역을 강제하거나 인증하지 않았다. 식별된 확장 실험에서도 V 대표값의 크기는 최대5788.052km/s이며, ||V||/(c z_min)≈1.93이라는 저적색편이 척도를 준다. 이는 특정 source의 실제 radial response 값이 아니다. 초기 J3의 최대21168.238km/s는 비식별 fibre의 gauge-dependent 대표값이므로 물리적 속도로 읽을 수 없다. 따라서 nuisance를 뺀 다항식 image는 선택한 통계적 분해의 조건부 결과이며, 검증된 물리적 velocity deboost가 아니다. 물리적 deboost를 주장하려면 실제 source 응답과 비선형 나머지를 제한한 별도 관측모형이 필요하다.

\[
-2\ln L(\theta|y)=\|C^{-1/2}(y-X\theta)\|^2+\ln\det C+N\ln(2\pi).
\]

이것은 표준 GLS다. 새로운 Gaussian likelihood 이론이라는 주장은 하지 않는다. tensorization의 실질적 역할은 **signed monopole/vector/STF 전체, nuisance 방향, 교차 covariance와 depth transport를 보존하여 실제 관측량의 image와 식별성을 판단하는 것**이다. x_C 또는 각 multipole amplitude만 먼저 남기면 이번 source별 정보 회복과 calibration fibre를 동일하게 다룰 수 없다.

| View | 이번 실제 구현 |
|---|---|
| x | full signed parameter carrier, source y/C, 9-component eta depth path 및 정의역이 허용하는 H_D/q_D image |
| Q | 지정한 nested radial-angular null에서 sqrt(Delta chi2/chi2_df(.95)); 통계적 noise reference이며 physical MES ceiling 아님 |
| Pi | 동일 fixed-C law의 chi-square upper tail; truth probability가 아님 |
| F | 하나의 joint confidence cylinder에서 signed linear support intervals; null이면 unbounded로 보존 |
| G_F | eta(z)−eta(.04)의 vector/STF 경로와 전체 cross-depth covariance; 임의로 F의 미분이라고 정의하지 않음 |

다섯 view는 하나의 likelihood에서 파생한다. 독립적인 다섯 likelihood로 곱하거나 Fisher information이 늘었다고 주장하지 않는다. 물리적 theta=(Theta,sigma,A,omega,beta,...)를 추론하려면 qualified source/optical map eta_processed(theta,gamma)를 O에 통과시켜 이 likelihood에 pullback해야 한다. 이 연결의 범위와 실제 코드 대응은 `TENSOR_LIKELIHOOD.md`에 있다.

## 6. 초기36행 실제 분석: 낮은 차수에서는 추가 radial angular term이 요구되지 않는다

7개 기존 보정 operator ×3차수로21개 fit을 실행했다. 아래 null은 자유V, constant angular field 및 radial monopole을 허용한 뒤 높은 radial-order의 dipole/STF를0으로 두는 가설이다. 정적 anisotropy나 우주 전체의 isotropy 가설과 같지 않다.

| 모형 | 실제 rank | residual df | adequacy p 범위 | 추가 radial angular term null p 범위 |
|---|---:|---:|---:|---:|
| J1 |20–21 /21|15–16|0.3129–0.8119|0.4899–0.9482|
| J2 |29–30 /30|6–7|0.4732–0.8809|0.5678–0.8261|
| J3 |36 /39|0|saturated; 정의 안 됨|0.5264–0.9180, 조건부 평균공간 비교만|

J1의 네 leave-one-window 예측은 full cross covariance와 parameter-estimation variance를 포함했다. 실제 p 범위는 **0.2280–0.8194**다. 같은 source들이 중첩되는 내부 예측이며 독립 자료의 재현이 아니다.

`log_mono_radial`은 O z=0이므로 radial monopole이 구조적으로 제거된다. 해당 경우 J1/J2의27개 depth coordinates 중24개 angular coordinates는 estimable이지만3개 monopole contrasts는 아니다. J3의 초기36행에서는 구체적인 null parameter displacement가 whitened mean을약10^-15 수준에서 보존하면서 H_D(.08)/H_D(.04)를 바꾸는 witness도 계산했다. 이는 **그 유한 압축과 평균모형에 관한 실제 반례**다.

대표되는 common l<=2 calibration shift의 identified depth 변화는 최대 **8.24×10^-17**이었다. 반면 source에0.01×P3(n.axis)의 z-independent l=3 angular calibration을 넣으면 J1/J2의 identified depth coefficient에 최대약0.0035–0.0059의 bias가 생겼다. 이는 고차 angular calibration에 대한 불변성 일반화가 실패한다는 deterministic sensitivity이며, 그 calibration이 실제 존재한다는 측정은 아니다.

## 7. 같은 원자료의 추가 정보를 회복하여36행 한계를 극복했다

R8에서 기존 L05 covariance가36×36만이 아니라 **288×288 joint cache**임을 확인했다. 그 안의 방법별32행과 sky-deletion36행, 그리고 기존36행과의 cross block을 실제로 재사용했다. 신규 pair sum이나 독립 source 추가는0이다.

실행한 결합은 log36+method32, log_mono36+method32, log_split36+method32와 log36+jk_no_equator36이다. 방법별 통계량은 .01≤z<.055에서 네 radial monopole bins를 제거하고 각 method의 polar3+STF5를 보존한 실제 연산자다. 별도의 L04 cache를 독립 block처럼 연결하지 않았다.

모든68/72행 결합에서 J3의 거리장36성분과 coherent V3를 합친 계수 rank가 **39/39**로 회복되었다. 세68행 실험에서는 추가로24개 method-angular nuisance를 허용해 정확히 profile한 뒤에도39/39를 유지했다. 이것이 이번 연구의 구성적인 정보 회복 결과다.

하지만 모형 적합도는 압축 방법에 따라 달랐다. 다음은 method monopole을 제거한 `mono_method`68행의 정확한 수치다.

| 모형 | 공통 optical field: chi2/df, p |24개 method-angular nuisance 추가: chi2/df, p | nuisance 추가 LR p |
|---|---|---|---:|
| J1 |74.9800/47,0.0058505|23.3854/23,0.438465|0.0008834|
| J2 |62.3519/38,0.0076419|12.2683/14,0.584765|0.0013817|
| J3 |53.6948/29,0.0035071|5.09569/5,0.404314|0.0021263|

원래36행을 사용해 추가32행을 예측하는 conditional innovation도 J1 p=0.0021474,J2 p=0.0032690을 주었다. 중첩 자료의 cross covariance를 포함하므로 독립성을 가정한 두 fit 비교가 아니다. 기존36행의 높은 adequacy p만으로 source dependence가 해결되었다고 말할 수 없다는 실제 결과다.

이 개선을 모든 방법에 일반화하지 않았다. `log_method`의 nuisance 포함 J3는 p=0.01619로 여전히 낮다. `split_method` 공통-field J1/J2/J3는 p=0.1115/0.09684/0.11467이며, nuisance 포함은0.6928/0.6279/0.6151이다. sky72행의 공통-field 값은0.07569/0.06470/0.05311이다. 동일 working covariance 아래 mean flexibility가 적합도를 개선한다는 사실은 calibration 오류의 원인을 인과적으로 특정하지 않는다.

확장21개 fit에서도 추가 radial-angular mean의 nominal p는약**0.466–0.971**이며 새로운 evolution detection을 요구하지 않는다. 각 operator/model은 중첩 자료의 민감도 대안이므로 p를 곱하거나 최솟값을 global significance로 바꾸지 않는다. 이 확장은 발견된 압축 한계를 해결하기 위한 exploratory R8 amendment이며, 최초부터 preregistered된 검정이라고 주장하지 않는다.

## 8. H_D와q_D에 대해 실제로 어느 정도 말할 수 있는가

동일한 joint confidence cylinder의 support를 사용해 delta eta, D(z),D(z*)의 범위를 구하고, 모두양수인 denominator 구간에 한해 H_D(z)/H_D(z*)의 보수적인 enclosure를 산출했다. 이는 독립-coordinate error propagation이 아니며 sharp profile-likelihood interval도 아니다. `DOMAIN_NOT_CERTIFIED`는 이 방법이 양의 분모를 인증하지 못했다는 뜻이지, 그 사실만으로 정확한 nonlinear image가 무한하다는 증명은 아니다.

예를 들어 `mono_method68 + method-angular nuisance`, ICRS+x 방향에서

| 모형 | H_D(.08)/H_D(.04) 대표값 |95% joint-region enclosure |q_D(.08) enclosure|
|---|---:|---|---|
| J1 |0.96786|[0.48544,2.13896]|[-14.9006,10.3740]|
| J2 |0.80949|[0.17340,7.52099]|[-250.638,167.667]|
| J3 |보수적 interval 미제공|분모 양성 미인증|분모 양성 미인증|

J3의 algebraic rank 회복은 실제이지만 정밀도와 nonlinear-domain 문제는 남는다. 같은68행+nuisance J3에서54개 고정 방향×3개 nonreference redshift, 총162개 ratio evaluation 중53개에서만 해당 보수적 finite enclosure를 얻었다. 나머지109개는 domain 미인증이다. 이 count는 연속 하늘의 면적 비율이나 posterior occupancy가 아니다.

따라서 현재 결과로 방향별 cosmic acceleration이나 정밀한 physical H(z,n)를 측정했다고 주장할 수 없다. 다만 무엇이 기존 압축에서 사라졌는지, 이미 있는 source information으로 어떤 null을 없앨 수 있는지, 그리고 source별 freedom을 허용했을 때 어느 미분량이 여전히 약한지는 실제 데이터로 말할 수 있게 되었다.

## 9. 선행연구 대비 기여와 심사 가능성

[Kalbouneh et al.,2510.02510v2](https://arxiv.org/html/2510.02510v2)는 로그 expansion-rate fluctuation, radial shells, harmonic GLS와 covariant cosmography를 이미 사용한다. [Vicente et al.,2607.07821v1](https://arxiv.org/html/2607.07821)는 l=1,2,3의 모든 angular DOF, STF, mask response와 covariance를 복원한다. [Salzano et al.,2512.02526v2](https://arxiv.org/html/2512.02526v2)는 log-Hubble formulation, radial sample diagnostics와 PV correction을 비교한다. 따라서 로그화, tensorization, covariance, radial evolution 각각은 이번 작업의 독립적인 신규성 주장이 될 수 없다.

가능한 manuscript contribution은 다음의 **실제 source-matched 결합 결과**다. 첫째, 실제 covariance를 보존한 단일 likelihood에서 radial shape와 calibration fibre를 구분한다. 둘째, 기존 압축을 추가 correlated source summaries로 확장해 식별성을 회복하고, 가려졌던 source-dependent inadequacy를 드러낸다. 셋째, rank 회복과 nonlinear H_D/q_D precision이 다르다는 것을 같은 실제 자료에서 보여준다. 넷째, physical congruence interpretation에는 어떤 optical/endpoint 입력이 더 필요한지 구성적으로 제시한다.

이는 현재 **유망한 methods/application 기여 후보**이며 신규성 증명이나 출판 보장은 아니다. 단독 논문이 너무 얇으면 기존P3의 핵심 방법·결과 절로 통합하는 것이 적절하다. 외부 논문의 특정 anisotropy significance를 반박하려면 sample·operator·log convention·covariance·nuisance를 먼저 맞춰야 한다. 현재의 radial-angular null은 타 논문의 static quadrupole detection과 같은 가설이 아니다.

제출을 막는 실질적 항목은 실제 shared-calibration/selection law, 같은 estimand로 맞춘 경쟁 분석, overlap-aware tracer prediction, 그리고 physical H를 주장할 경우의 optical closure다. 새로운 branch를 계속 만들면서 같은 압축을 반복할 이유는 없다. 구체적인 유한 후속작업은 `RESEARCH_PLAN_KO.md`와 additive P3 DAG에 한정한다.

## 10. 검증·재현·완료 범위

기본62개 테스트는 최초 affected60개와 R8의 새로운 nuisance projection 위험을 다룬2개로 구성된다. Wolfram의7개 대수 차이, SymPy의8개 대수 차이는 모두0이며, deSitter/EdS limits, Milne counterexample, source design, covariance-preserving profile, null/domain behavior와 ellipsoid witnesses를 검증했다. 이는 기존 프로젝트의4축 CAS admission 전체를 새로 PASS했다는 뜻이 아니다.

초기21개와 확장21개, 총42개의 고유 실제-data fit을 저장했다. 최초 augmentation 실행은 최종 metadata hash 저장에서 string/Path adapter 오류가 나서 결과 carrier를 저장하지 못했다. 해당1줄을 수정하여 필요한 실행만 재수행했고,21개 출력 fit summary가 모두이전과 정확히 같음을 확인했다. Summary producer의 JSON-list abs 오류도 파생 보고 단계에서 교정했다. 실패 로그·수정 receipt는 보존했다. 이론식이나 실제 적합 결과를 그 오류 해결 과정에서 바꾸지 않았다.

실제 결과, source/코드 hash, primary execution, repair와 독립심사 상태의 최종 근거는 `VALIDATION.md`, `REVIEW/final_review.json` 및 `RESULTS/`다. 기존42개 publication nodes와 과거 paper acceptance를 그대로 두고 P3 companion 결과만 추가한다. 이번 scope의 완료는 반복적인 successor 연구를 자동으로 승인하지 않는다.
