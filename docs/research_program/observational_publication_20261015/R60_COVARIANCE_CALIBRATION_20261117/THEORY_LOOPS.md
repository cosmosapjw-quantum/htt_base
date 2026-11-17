# R60 여섯 독립 이론 연구 루프

기준: 2026-11-17, 6fe19c5139004a1f281ec85c592e5ab4c7590d5f. physmath-research-loop 내장 규약 1.0.0의 R1–R10을 적용한다. 각 루프는 별도의 질문·판별량·종료 결론을 가진다. 공통 likelihood·입력이 유지되는 단계는 기존 근거를 재사용한다. scoped 계산의 종료와 여섯 우주론적 질문의 최종 해결은 구분한다.

## 공통 정의와 근거

metric은 (-,+,+,+), U.U=-c², h_ab=g_ab+U_aU_b/c², n은 observer에서 source로 향하는 unit spatial vector다. H=Theta/3, sigma는 STF expansion shear [1/time], omega는 axial vorticity [1/time], A=∇_U U [length/time²], beta는 두 명시된 frame 사이 velocity/c다.

현재 likelihood의 관측 좌표는 alpha=(V3,d_H3,kappa5), 단위 (km/s,1,1)이다. 각 nuisance operator에서 y~N(X alpha,C), J=X^T C^-1 X, t=X^T C^-1 y, q0=y^T C^-1 y를 사용한다. 정규화 likelihood는

$$
-2\ln L=\alpha^TJ\alpha-2t^T\alpha+q_0+\ln\det C+n\ln(2\pi).
$$

C가 고정이고 alpha에 무관할 때 exact factorization으로 t가 충분하다. C(lambda)를 변화시키면 고정 t만으로는 충분하지 않아 원 y,X,N,S를 유지한다. 이 식은 새로운 GLS 정리가 아니다. signed tensor를 scalar로 축약할 때 잃는 정보와 물리적 nuisance 방향을 보존하는 데 사용한다.

독립 수학 검토: [REVIEW/tensor_theory_audit.md](REVIEW/tensor_theory_audit.md), [REVIEW/tensor_theory_checks.json](REVIEW/tensor_theory_checks.json), [REVIEW/tensor_theory_wolfram_checks.json](REVIEW/tensor_theory_wolfram_checks.json). 내부 lineage와 원전 비교는 REVIEW/history_audit.md 및 REVIEW/literature_delta_report.md에 있다.

## L1 — Low-ell morphology와 물리 관측량

### R1 연구 위치·계약

질문은 보유 Commander quadrupole의 모양을 정보 손실 없이 표현하고, 그 표현 중 어느 부분이 실제 shear-history 관측량인지 구별하는 것이다. 완료 대상은 실제 signed T2 tensor, 정확한 harmonic map, pipeline 비교 및 transfer 의무다.

### R2 근거·재사용

R39의 typed x, R51 observed carrier/source contract, R54의 Thomson T/E kernels를 재사용한다. R51 response_J의 beam은 SMICA INT_BEAM×pixel window다. 따라서 그 inverse를 Commander-specific beam deconvolution으로 채택하지 않는다. Commander-matched MC가 완비되지 않은 상태를 유지한다.

### R3 주장·전제 정렬

입력 d=(a20,sqrt2 Re a21,-sqrt2 Im a21,sqrt2 Re a22,-sqrt2 Im a22)는 실제 retained estimator 계수다. estimator는 common mask와 finite ell<=6 coupling inverse를 사용한다. 변환은 이 계수의 정확한 representation이며 미지의 full-sky 계수의 unbiasedness를 추가로 주장하지 않는다.

### R4 가설·표현 탐색

scalar C2, largest-|eigenvalue| axis, full STF tensor/eigenframe를 동일한 두 pipeline에 적용하여 무엇이 손실되는지 비교한다. 원 자료를 유지하는 full STF를 primary x로 선택한다.

### R5 구성적 유도

Frobenius orthonormal basis E=(xx-yy,xx+yy-2zz,xy,xz,yz)의 정규화를 각각 sqrt2,sqrt6,sqrt2,sqrt2,sqrt2로 두면

$$
q=\frac{(d_{2r},-d_0,d_{2i},-d_{1r},-d_{1i})}{\sqrt{8\pi/15}},
\quad Q_T=\sum_Aq_AE_A,\quad T_2(n)=n^TQ_Tn.
$$

구면 4차 moment를 사용하면 integral T2² dOmega=(8pi/15)tr Q²=Σ_m|a2m|², C2=(8pi/75)trQ²다. trace-free ordered eigenvalues lambda_-<lambda_0<lambda_+에서는 |lambda_-|-|lambda_+|=lambda_0이므로 largest-absolute selector는 lambda_0=0에서 branch를 바꾼다. 이는 eigenvalue degeneracy와 다른 현상이다.

물리적 Bianchi-I 선형 transfer의 좁은 subcase는 delta T/T0=-n Sigma_T n, Sigma_T=integral K_T s dN이며 s=sigma/H다. R54의 k=0 Thomson 계산은 K_T=(6 exp(-tau)+exp(-3tau/10))/7, K_E=(sqrt6/7)(exp(-3tau/10)-exp(-tau))를 준다. current shear는 이 integral을 history law로 역전할 때만 정의된다. 자유로운 stress/history에서는 T kernel을 상쇄하는 history가 존재할 수 있으므로 단일 T2 tensor를 current shear로 나누어 읽지 않는다.

### R6 독립 검증

analytic map을 R51 ideal template와 대조하고, 별도의 complex spherical harmonics synthesis와 angular quadrature를 실행했다. independent Cartesian harmonic polynomial 검토도 수행했다. 차원은 q,Q가 microkelvin이고 Sigma가 무차원이며, physical sign은 template의 minus와 직접 대응한다.

### R7 판별 검증

Commander C2=207.0624434 microkelvin², ordered eigenvalues=(-17.9675337,0.8088642,17.1586694) microkelvin. SMICA와 Frobenius 상대 차이 8.274%, matched axes 2.0665–2.5077도, largest-absolute selected axes 88.4993도다. independent synthesis error는 약 7e-15 microkelvin 수준이다.

### R8 결과 판정

새 실제 관측 적용은 scalar axis의 branch-switch failure다. tensor representation의 유용성이 직접 확인되었다. 이는 원전의 STF/spectral mathematics보다 새로운 정리라는 주장이 아니다. anomaly significance/current shear/Bianchi type은 unresolved다.

### R9 정식 결과·코딩 연결

scripts/r60/run_r60_commander_morphology.py와 RESULTS/COMMANDER_MORPHOLOGY.json이 normalized map, 전체 eigenframe, source hash와 pipeline comparison을 저장한다. Q와 Pi를 물리 law 없이 만들어 넣지 않는다.

### R10 종료·재개

결정론적 morphology 단위는 완료한다. likelihood 측정으로의 다음 의무는 Commander-specific beam/KQ convention과 independent matched simulations, 허용할 stress/history family다. 이 의무를 SMICA null 대여로 대체하지 않는다.

## L2 — Dipole anomaly와 선택·보정의 구별

### R1 연구 위치·계약

Quaia_G20 및 NVSS의 기존 excess vector가 어떤 covariance/systematic 가정에서 비정상으로 분류되는지 정량화한다. 속도나 전역 tilt로 먼저 이름 붙이지 않는다.

### R2 근거·재사용

R54_L03_RESULT.json의 observed vector, 500개 same-estimator Poisson+clustering mocks, receipt-systematic covariance를 재사용한다. mocks에는 higher clustering multipoles와 selection systematics가 모두 포함되지 않았고 data expectation이 쓰였다. 원래 finite-mock Pi와 Gaussian working approximation은 구별한다.

### R3 주장·전제 정렬

flux counts N(>S)∝S^-x, source spectrum S_nu∝nu^-a_s, rest sample isotropy라는 제한된 조건에서 observer Doppler factor D=1+beta_OR.n을 사용한다. redshift-selected sample과 evolving population에는 추가 selection response가 필요하다.

### R4 가설·표현 탐색

동일 observed excess e3에 대해 mock-only covariance와 receipt systematic을 포함한 covariance를 연속적인 선언된 family로 연결한다. systematic scaling과 deterministic mean-offset budget은 서로 다른 모델로 별도 보고한다.

### R5 구성적 유도

aberration으로 dOmega_obs=D^-2 dOmega_rest, flux boost로 S_obs=D^(1+a_s)S_rest이므로

$$
n_{\rm obs}(>S_{\lim})=D^{2+x(1+a_s)}n_{\rm rest}(>S_{\lim}),
\quad D_{\rm kin}=[2+x(1+a_s)]\beta_{OR}.
$$

이 계수는 모든 probe에 보편적이지 않다. 실제 excess e=D_obs-D_kin은 calibration/LSS/frame response를 포함한다.

C(lambda)=C_mock+lambda S_receipt와 고정 e에서 W=e^T C^-1 e라 두면 dW/dlambda=-(C^-1e)^T S_receipt(C^-1e)<=0이다. 이는 평균을 다시 적합하는 CF4 Wald와 다르다.

최소 deterministic offset은 min ||b||, subject to (e-b)^T C_mock^-1(e-b)<=chi-square_3(.95)로 정의한다. C=U diag(c_i)U^T이면 b=U diag(tau/(c_i+tau))U^T e이고 residual constraint가 tau를 결정한다. 여기서 chi-square 기준은 estimated/data-conditioned covariance에 대한 nominal 기준이다.

### R6 독립 검증

S_receipt의 PSD, endpoint의 원 Gaussian p 재현, monotonic derivative와 finite grid를 확인했다. offset의 scalar root와 독립 Cartesian SLSQP가 2.5e-11 이내에서 일치했다. 방향 없는 zero offset은 임의 axis를 저장하지 않는다.

### R7 판별 검증

Quaia: finite-mock Pi=.005988024; nominal Gaussian p(0)=.000417023, p(1)=.309208812, .05 crossing lambda=.253689111. NVSS: finite-mock Pi=.329341317, nominal p=.322792035→.421167779로 crossing 없음. Quaia 최소 offset norm=.0038996227 count-dipole units, NVSS는0.

### R8 결과 판정

관측 excess의 판단은 systematic law에 민감하다. anomaly 부재도, global tilt 검출도 이 계산에서 결론 내리지 않는다. 새 결과는 명시한 systematic budget이 결론을 바꾸는 정도다. 새로운 universality/no-go 주장은 없다.

### R9 정식 결과·코딩 연결

scripts/r60/run_r60_count_dipole_sensitivity.py, RESULTS/COUNT_DIPOLE_SENSITIVITY.json에 signed vector, 행렬, full path, calibration witness, 원 finite-mock Pi를 별도 보존한다.

### R10 종료·재개

이번 conditional sensitivity는 완료. 다음 physical gate는 catalogue selection/depth별 response와 independent systematic injections, count/CMB/CF4 공통 frame 및 cross-probe covariance다. 다양한 tail 중 유리한 값만 선택하는 경로는 닫는다.

## L3 — Beyond-FLRW kinematic quantities의 측정

### R1 연구 위치·계약

theta=(sigma,omega,A,beta) 자체와 mixed functional을 likelihood의 상태변수로 둔다. 현재 관측으로 식별되는 quotient와 유한 보정 budget을 추가할 때 생기는 physical confidence set을 구성한다.

### R2 근거·재사용

R39 VECTOR_TENSOR_X_FRAMEWORK, R58 rank/nullspace carrier, Heinesen의 general congruence 및 Maartens의 observer-covariant cosmography를 재사용한다. 유한-z CF4 response와 local Taylor coefficient를 동일시하지 않는다.

### R3 주장·전제 정렬

∇_bU_a=sigma_ab+omega_ab+H h_ab-U_b A_a/c². 미래방향 incoming null vector K=U-cn에서 U.K=-c²이다. 추론에서 고정한 congruence와 sourceward direction을 유지한다.

### R4 가설·표현 탐색

apparent coefficients를 물리량으로 단순 재명명하는 후보 대신, (sigma/H,omega/H,A/(cH),beta,d_cal,q_cal)를 모두 가진 22D state와 실제 response map을 사용한다.

### R5 구성적 유도

K^aK^b∇_bU_a/c²=H+sigma:nn-A.n/c이며 omega는 antisymmetry로 사라진다. full sky에서는 H=<mathscr H>, A_i=-3c<mathscr H n_i>, sigma_ij=(15/2)<mathscr H(n_i n_j-delta_ij/3)>다.

V=c beta, d=-a+d_cal, kappa=s+q_cal에서 a=A/(cH),s=sigma/H. 응답 kernel은 자유 omega3, (a,d_cal)→(a+u,d_cal+u), (s,q_cal)→(s+S,q_cal-S)를 포함해 차원11이다. 따라서 physical likelihood는 정의 가능하나 individual s,a의 유한 구간은 무제약 calibration에서 나오지 않는다.

선택한 calibration body의 Gram은 G=diag(I3/3,2I5/15). marginal/profile h covariance를 C_h라 하면

$$
\rho_*=\min_{h\in E_h}\sqrt{h^TGh},\qquad
E_h=\{h:(h-\hat h)^TC_h^{-1}(h-\hat h)\le\chi^2_d(.95)\}.
$$

이는 실제 고유한 관측 threshold를 만드는 기존 Q_min이다. E_h+B_rho의 support는 u.hhat±[sqrt(chi-square_d u^TC_hu)+rho sqrt(u^TG^-1u)]다. 물리 a,s의 sign map을 함께 적용한다. mixed physical functional은 이 같은 집합에서 profile/pushforward하며 duplicated x를 새로운 독립 data로 취급하지 않는다.

### R6 독립 검증

전천 angular moments, STF Gram, SO(3) action 및 Schur complement=C_h^-1을 Python과 Wolfram으로 검산했다. convex KKT 해를 독립 SLSQP와 대조했다. singular directions에 pseudoinverse variance=0을 물리적 측정값으로 출력하지 않는다.

### R7 판별 검증

실제 CF4에서 union STF threshold는 full-sky RMS .00131474845mag이고 angular8은0이다. directional F_support도 실제 ICRS xyz에서 rho0,.001,.005,.01로 저장했다. rho는 estimated systematic가 아니다.

### R8 결과 판정

physical inference에 필요한 calibration 수준을 정량화했다. 현재 증거는 apparent tensor와 특정 physical combinations를 지지하며, A/sigma의 개별 검출이나 omega 측정은 미완료다. 제한된 response의 kernel을 모든 관측에 대한 no-go로 확대하지 않는다.

### R9 정식 결과·코딩 연결

r60_covariance_calibration.py의 calibration_distance, calibration_breakdown, calibrated_support와 실제 witness를 equation→function→output으로 연결한다. 직접 theta 및 mixed x 계약은 TENSOR_PHYSICAL_LIKELIHOOD.md에 고정했다.

### R10 종료·재개

조건부 identified-set 단위 완료. 독립 calibration의 physical body를 측정하거나 source-bound 추가 probe가 kernel을 줄이는지 평가하는 것이 다음 과학 의무다. priors로만 좁힌 posterior와 likelihood identification을 구분한다.

## L4 — Anisotropy morphology와 Bianchi classification

### R1 연구 위치·계약

현재 apparent STF가 일반 비축대칭 형태를 요구하는지 먼저 판별하고, 그 판정과 공간 homogeneous class의 식별을 분리한다. 일반/tilted Bianchi 목표는 유지한다.

### R2 근거·재사용

R49의 Bianchi convention/geometry·transfer 실패 기록, R50의 physical-response 감사, R58 kappa likelihood를 재사용한다. Saadeh 등의 near-isotropic template 추론과 Pereira–Pitrou의 perturbative correspondence가 source-bound 선행방법이다. 미검증 synthetic family coefficients는 사용하지 않는다.

### R3 주장·전제 정렬

공간 Lie brackets를 [e_b,e_c]=C^a_bc e_a, C^a_bc=epsilon_bcd n^{da}+a_b delta^a_c-a_c delta^a_b로 정하면 n은 symmetric, Jacobi는 n^{ab}a_b=0이다. 여기서 structure-vector a는 4-acceleration A와 다르다. 이를 결정하려면 geometry/dynamics가 필요하며, 한 점의 shear eigenvalues만으로 충분하지 않다.

### R4 가설·표현 탐색

일반 STF와 axial STF의 비교를 현재 관측에서 직접 할 수 있는 분류 문제로 택했다. axisymmetric morphology를 Bianchi-I, VII_h 등의 이름으로 치환하지 않는다.

### R5 구성적 유도

unit n에 대해 u(n)=sqrt(3/2) STF(nn)를 STF5로 나타내고 k=a u(n)라 둔다. 고정 n의 해는

$$
a(n)=\frac{u^TS^{-1}\hat k}{u^TS^{-1}u},\quad
\Delta(n)=(\hat k-a u)^TS^{-1}(\hat k-a u).
$$

어떤 n에서 Delta<=chi-square_5(.95)이면 axial intersection의 constructive witness다. 전역 최소화가 증명될 필요는 없다. full coefficient lift는 alpha_w=alphahat+Cov(alpha,k)S^-1(k_w-khat)이며 같은 quadratic distance를 갖는다. 이 항등식은 동일 cutoff에 대해 성립하고 두 차원의 서로 다른95% cutoff를 동일시하지 않는다.

### R6 독립 검증

basis Gram, trace0, norm1, axial eigenvalue multiplicity와 eigenaxis norm을 검사했다. 별도 oracle이 full lift identity를 검산했다. Fibonacci scan/local optimizer는 feasible candidate 생성기이며 전역최적 인증기로 서술하지 않는다.

### R7 판별 검증

일곱 모델 모두 axial witness를 얻었다. Delta=[5.02879,4.11741,4.09065,1.09106,2.72028,1.34960,1.84756]이며 cutoff11.07050보다 작다. 각 component/eigenvalue를 결과에 저장했다.

### R8 결과 판정

현재 data law에서 triaxiality가 요구되지 않는다. 이는 isotropy 입증도, 어느 공통 축 모델의 재현도, Bianchi class 확정도 아니다. 새 결과는 관측 신뢰집합 내부의 feasible morphology다.

### R9 정식 결과·코딩 연결

scripts/r60/run_r60_axisym_witness.py 및 RESULTS/AXISYMMETRIC_WITNESSES.json. 실제 Bianchi likelihood는 geometry parameters→Einstein-compatible state/history→photon/matter transfer→동일 관측 operator의 map을 요구한다.

### R10 종료·재개

morphological compatibility 단위 완료. 다음 의무는 literature-bound transfer와 동역학 manifold를 검증한 제한된 family 비교다. 현재 repo 정책에 따라 native Bianchi solver를 새로 구현하지 않았다. 일반 강한 비등방/tilted classes의 상태는 unresolved다.

## L5 — Redshift와 방향에 의존하는 Hubble observable

### R1 연구 위치·계약

네 겹치는 depth window의 full covariance를 유지한 apparent log-H vector/STF가 어느 nuisance/covariance 조건에서 영점을 배제하는지 계산한다.

### R2 근거·재사용

R54 log-distance estimator 및 exact cosmic body, R58 공통 11parameter fit을 재사용한다. Kalbouneh/Vicente의 harmonic/STF cosmography 및 full covariance를 선행방법으로 명시한다. 서로 다른 sample/normalization의 p를 직접 순위화하지 않는다.

### R3 주장·전제 정렬

eta의 natural-log distance ratio convention, g(z)={(1+z)/(E(z)chi_hat(z))-1}/c, 입력 z_CMB와 luminosity distance model을 유지한다. z=.01–.1에서 local H tensor라고 부르기 위한 approximation/transport는 별도 의무다. four windows를 독립 관측으로 취급하지 않는다.

### R4 가설·표현 탐색

기존 한 개 covariance로 고정한 결론을 C(lambda)=N+lambda S family와 mean-calibration budget에 걸쳐 평가한다. dimension11/8/5의 distinct null을 미리 분리한다.

### R5 구성적 유도

full GLS score, profiled block Wald와 nuisance Schur precision을 사용한다. covariance-dependent logdet를 버리면 amplitude likelihood가 잘못된다. 고정-mean whitened likelihood는

$$
\ell(a)-\ell(0)=\frac12\sum_i\left[p_i^2\frac{a\lambda_i}{1+a\lambda_i}
-\ln(1+a\lambda_i)\right].
$$

각 summand peak a_i=max(0,(p_i²-1)/lambda_i)로 전체 maximizer의 유한 upper domain을 얻고, interval별 summand maxima 합으로 upper bound를 만든다. midpoint Taylor upper bound도 함께 사용해 score cancellation을 보존한다.

lambda=(100,1),p²=(0,20)에서 score(0)<0이나 a=(1699+sqrt2821801)/400가 global maximum이다. 이는 기존 helper의 boundary shortcut을 반박한다. 또한 y=(0,1),X=(1,0)^T,C=I+lambda 11^T에서 fitted Wald=lambda²/[(1+lambda)(1+2lambda)]가 증가하므로 covariance scan의 전역 단조성을 가정하지 않는다.

### R6 독립 검증

two-mode exact stationary roots, cap/flat/invalid inputs, legacy400mode input, GLS/QR equivalence, block Wald/profile LR, direct logdet 및 REML determinant identity를 독립 검증했다. 한 fixed full-QR contrast matrix가 mean을 제거하므로 restricted likelihood에 fixed-mean amplitude bound를 적용할 수 있다. 일반 profile likelihood에 그 bound를 옮기지 않는다.

### R7 판별 검증

model-max p11=.0153427, p8=.0549609,p5=.0261897. finite-grid refined crossings는 lambda11=1.26461668,lambda5=1.24267056. full covariance를 무시한 ablation보다 좋아진다는 것은 기존 내부 검증이고, full covariance를 쓰는 선행연구 대비 우월성은 새로 주장하지 않는다.

### R8 결과 판정

특정 fixed-law에서 apparent STF에 conditional evidence가 있으나, 1.315mmag calibration 및 약24% cosmic variance 변화가 결론을 바꾼다. 실제 physical shear나 covariance amplitude의 측정은 아니다.

### R9 정식 결과·코딩 연결

run_r60_sensitivity.py가 reference identity·parity, 전체 grid, 모든 bracket crossing, exact calibration witnesses, support와 plot을 저장한다. 기존 amplitude consumer는 shared common helper를 사용하도록 교정했다.

### R10 종료·재개

actual sensitivity/optimizer repair 완료. 다음 primary 의무는 원 source sample에서 forward law·selection·zero points를 맞춘 comparator와 coverage다. 무한 audit 또는 또 하나의 scalar p-value 탐색으로 넘어가지 않는다.

## L6 — Local boost와 global tilt의 구별

### R1 연구 위치·계약

observer O, radiation R, matter M, homogeneous normal N을 구분한다. 이번에는 constant velocity와 한 개 finite radial basis가 CF4에서 얼마나 구별되는지 실제 응답으로 판별한다. 이 basis를 global-tilt dynamics라고 가정하지 않는다.

### R2 근거·재사용

R54 CONST_V/closure 계산과 calibration alternative, Stiskalek의 flow/zero-point 문제, Maartens/Yoo의 observable-specific frame response를 재사용한다. R54 closure p=.0865는 특정 constant closure에 대한 조건부 값이다.

### R3 주장·전제 정렬

저속에서 beta_MR=beta_MN-beta_RN처럼 상대속도 차이가 관측된다. global normal N을 geometry/matter로 정의하지 않으면 beta_MN을 상대속도 하나로 분리할 수 없다. source endpoint, redshift and direction transformation, luminosity distance factor를 일관되게 유지해야 한다.

### R4 가설·표현 탐색

V(z)=V0+V1 z/zstar,zstar=.05 한 개 대안을 선택했다. 일반 time/depth dependence를 무제한 추가하지 않는다. 먼저 무제약 선형 응답의 식별성을 검사하고, 유효범위를 벗어나면 finite sensitivity body로 물리적 해석을 제한한다.

### R5 구성적 유도

E(z)=1+(1+q0)z+O(z²), chi_hat=z-(1+q0)z²/2+O(z³)이므로 czg(z)=1-(1+q0)z/2+O(z²). 따라서 g(z) V1 z/zstar의 leading angular pattern은 n.V1/(c zstar)다.

d_eff=d_H+V1/(c zstar), R_res=O[(gz/zstar-1/(c zstar))n]로 stable chart를 만들고 T로 원 physical d_H를 복원한다. fixed C에서 full14 rank이면 V1=0 nested LR는 conditional chi-square3이며, slope block Wald와 같다.

유한 budget에서는 원11 estimator의 정확한 평균 bias B V1을 사용한다:
B=(X^TC^-1X)^-1X^TC^-1Z. ||V1||<=b에서 physical alpha의 confidence union은 E_alpha+(-B ball_b)다. residual 정보는 이 conservative marginal set에 사용하지 않는다. target support는 기존 radius에 b||B^Tu||를 더한다. whitened SVD trust-region으로 영점과의 거리 및 feasible V1 witness를 얻는다.

### R6 독립 검증

raw operator와 원 R58 y/X/N을 재구성해 비교했다. chart/direct-physical fit, 전체 covariance back-transform, low-z limit, LR/Wald 항등식, actual84 budget witnesses의 KKT를 독립 검산했다. 작은 비영 response를 절단하거나 multiplier의 absolute tolerance로 budget을 위반하는 경우를 테스트하고 unresolved response는 fail closed한다.

### R7 판별 검증

nested p=.190–.858; d_H error inflation125–141. 무제약 fit speed/c=.159–.531로 physical use를 거절했다. finite V1 budgets0–3000 km/s에서 STF5 zero exclusion은 유지되고, b=1000km/s는 d_H support를 성분별 약.065 넓힌다. 선형 모델의 formal STF threshold22506km/s는 perturbative regime 밖임을 표시한다.

### R8 결과 판정

현재 finite response에서 constant와 radial-flow decomposition은 매우 약하게 식별된다. 이 결과는 global tilt의 검출도 universal non-identifiability theorem도 아니다. 충분한 독립 depth/kinematic response를 확보하면 구별 가능성은 다시 평가한다.

### R9 정식 결과·코딩 연결

run_r60_radial_velocity.py 및 RESULTS/RADIAL에는 raw response columns, physical/chart transforms, signed estimates, covariance, bounded-body witnesses와 유효범위가 저장된다. V1의 자유 fit을 velocity prior 없이 physical parameter의 posterior로 발표하지 않는다.

### R10 종료·재개

이번 finite response 단위 완료. 다음 physical route는 독립 observer aberration/Doppler calibration, source-redshift-resolved counts/distances, 동일 물질 congruence의 propagation model이다. 이를 Bianchi family transfer와 결합할 때 Einstein constraints와 joint covariance를 먼저 명시한다.

## 판정과 종료

새 universal strong no-go 성과는 채택하지 않는다. NG1–NG7 중 literature-new universal theorem을 요구하는 기준이 충족되지 않았고, 현재 결과는 finite-response kernel·구성적 반례·실제 민감도다. 반례는 정확히 거짓인 monotone-score/monotone-Wald 명제를 반박하는 범위로 보존한다.

여섯 루프의 scoped 산출물은 실제 관측계산/유도/교정으로 닫으며, 전체 physical identification은 RESEARCH_PLAN_KO.md의 구체적인 원자료·transfer·calibration 의무로 남긴다. 새로운 audit-only successor를 자동 생성하지 않는다.
