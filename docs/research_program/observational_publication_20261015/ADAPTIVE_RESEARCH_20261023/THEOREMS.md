# 조건부 방법의 수학적 유도

Owner: HTT 방법 연구. Source base: `10f3ea585c6608e794900efe7e4f8f42c0747a3b`.
상태: 기존 **T1–T6는 [PLAN_REVIEW_CLOSEOUT](reviews/PLAN_REVIEW_CLOSEOUT.md)의 한정된 검토 scope**를 따른다. 아래 추가 **T7–T10은 PENDING_FRESH_INDEPENDENT_REVIEW**다. 기존 Astra 자문 계약의 식을 명시적 가정 아래 전개한 문서다. 새 물리 법칙, 관측 calibration 또는 CAS 4축 검증을 주장하지 않는다. 출처의 일반 정리와 아래 직접 유도를 구별한다. 일차 문헌의 적용 절과 한계는 [METHOD_SOURCE_NOTES](METHOD_SOURCE_NOTES.md)에 있다.

## T1. 공분산 상계와 contrast 검정

가정: d∈R^r, E d=0, Cov(d)=C, 결정론적 V≻0와 C≼V가 주어진다. 그러면 T=dᵀV⁻¹d≥0이고

E T=tr(V⁻¹C)=tr(V⁻¹/²CV⁻¹/²)≤r.

따라서 Markov 부등식으로 Pr(T≥r/α)≤α (0<α<1)다. Gaussian d라면 B=V⁻¹/²CV⁻¹/²의 고유값 λ_i∈[0,1]를 써 T의 법칙을 Σλ_i Z_i²로 표현할 수 있다. 같은 독립 표준정규 Z_i에서 Σλ_i Z_i²≤ΣZ_i²이므로 chi-square_r upper tail이 보수적이다. 비Gaussian에서는 이 결합 주장을 쓰지 않는다. 평균이 0이 아니면 E T에 μᵀV⁻¹μ가 추가되어 영가설 경계가 달라진다.

현재 적용: μ24,C24와 보정 M24→Y18를 유지한다. H=[[-1,1,0],[0,-1,1]]⊗I6, A=HM, d=Aμ24, Vτ=A(C24+τ²I24)Aᵀ. A가 row rank12이면 AAᵀ≻0이며 q=τ²에 대해

dT/dq=−dᵀVτ⁻¹AAᵀVτ⁻¹d<0 (d≠0).

따라서 T(0)보다 낮은 양의 threshold의 crossing은 유일하다. 이미 threshold 아래면 nonnegative crossing이 없다. C24+τ²I가 실제 공분산의 상계라는 가정은 관측으로 입증되지 않았다. 현재 curve와 standalone α=.05, 비교용 1/80은 탐색적 reference이며 R9 alpha를 재사용하지 않는다. 이 12-contrast 귀무는 기존 slope6=0과 다르다.

## T2. bias ball의 정확한 witness와 support

V≻0, 선형 A∈R^(r×p), 고정 d, ||b||₂≤δ에서 min ||V⁻¹/²(d−Ab)||₂²를 생각한다. z=V⁻¹/²d, B=V⁻¹/²A의 rank를 k라 하고, 양의 singular value s_i>0만 포함하는 compact rank-k SVD B=U_k diag(s_i) W_kᵀ를 쓴다. U_k∈R^(r×k), W_k∈R^(p×k)는 orthonormal column을 가지며 y=U_kᵀz, c=W_kᵀb다. k=0이면 B=0이므로 모든 feasible b의 목적값은 ||z||²이고 최소 norm 해 b=0이다. 아래 secular 식은 k>0에만 쓴다. 목적함수는 Σ_(i=1)^k(y_i−s_i c_i)²+||(I−U_kU_kᵀ)z||²이고 불필요한 ker B 성분은 최소 norm 해에서 0이다. unconstrained 최소 norm 해는 c_i=y_i/s_i, b=W_k c다. δ≥||B†z||이면 이것이 해다. 그보다 작고 δ>0이면 Lagrange 조건으로

c_i=s_i y_i/(s_i²+λ), λ>0,
Σ s_i² y_i²/(s_i²+λ)²=δ².

좌변은 관련 y가 비영이면 λ에 대해 연속·엄격 감소하므로 유일한 root다. δ=0은 b=0으로 직접 계산한다. B가 full row rank이면 영 residual에 필요한 최소 radius는

δ0=||Aᵀ(AAᵀ)⁻¹d||₂,

왜냐하면 whitening이 Ab=d의 해집합을 바꾸지 않기 때문이다. rank가 부족하면 잔류 직교 성분을 보존하며 이 식을 무조건 쓰지 않는다. 반례 V=I2, A=diag(1,0), d=(0,1)에서는 k=1, y=0이고 orthogonal residual norm²=1이다. 모든 δ≥0에서 최소 목적값은1이며 δ0=||B†z||=0을 영 residual radius로 해석하면 틀린다. retained positive singular subspace 밖의 잔차를 반드시 남긴다. coefficient bias 단위·metric을 계약에서 고정해야 radius를 해석할 수 있다.

한편 ambient mean-shift ball과 ellipsoid의 합 K=μhat+δ B₂+{e:eᵀU⁻¹e≤ρ²}, U≻0의 support는

h_K(u)=uᵀμhat+δ||u||₂+ρ sqrt(uᵀUu).

각 독립 제약의 선형 최대를 더하면 된다. coefficient ball을 A로 보낸 경우 bias 항은 δ||Aᵀu||다. 두 radius를 혼동하지 않는다. 이 support는 선형 함수상에 정확하다. norm의 단순 spectral bound는 일반적으로 보수적 outer이며 joint nonlinear image 전체가 아니다. Gaia의 실제 bias bound를 측정했다는 뜻도 아니다.

## T3. 임의 의존성과 공동 상태

공통 target θ에 대해 Pr(θ∈C_j)≥1−α_j인 집합들이 있으면, 독립성 없이

Pr(θ∈∩C_j)≥1−Σα_j.

이는 사건 합집합 bound다. target/frame이 다른 집합을 그대로 교차하면 이 결론은 없다. 새로운 physical common target부터 정당화해야 한다.

각 centered vector X_j의 marginal covariance C_j만 알려졌다고 하자. Z=Σa_jᵀX_j에 대해 covariance Cauchy–Schwarz로

Var Z≤(Σ sqrt(a_jᵀC_j a_j))².

이 bound는 허용된 모든 공동 coupling에 대해 sharp하다. v_j=a_jᵀC_ja_j>0일 때 같은 scalar Z0(분산1)를 사용해 X_j=(C_ja_j/√v_j)Z0+ε_j로 구성하고, Cov ε_j=C_j−C_ja_ja_jᵀC_j/v_j≽0이며 a_jᵀε_j=0이 되게 한다. 그러면 모든 projection이 √v_j Z0로 일치한다. v_j=0 항은 0이다. 이 extremal coupling은 물리 공동 law가 관측되었다는 뜻이 아니다. projection별 sharp endpoint가 하나의 모든-functional 동시 attainable state를 주는 것도 아니다. 따라서 full tensor 공동 상태·cross block을 먼저 정의하고 나중에 projection한다.

## T4. dependent conditional e-value

[Universal Inference](https://arxiv.org/html/1912.11436v4), §5 De-randomization과 §6 Conditional likelihood for non-i.i.d. data에 이미 의존하는 split 통계의 평균과 비-iid conditional likelihood 방법이 있다. 아래는 correlated-catalogue 적용에 필요한 가정을 드러내는 특수화와 직접 유도이며 방법적 novelty를 주장하지 않는다.

고정 training/validation 분할 (Y_T,Y_V)에 대해 q(·|Y_T)가 적분1인 비음수 density이고, 귀무 family p_θ(·|Y_T)의 실제 conditional density를 denominator D=sup_(θ∈Θ0)p_θ(·|Y_T)가 지배한다고 가정한다. 같은 dominating measure를 쓰고, D=0인 null 확률0 영역의 e 정의를 명시한다. e=q(Y_V|Y_T)/D(Y_V|Y_T)이면 각 귀무 θ에서

E_θ[e|Y_T]=∫q(v|Y_T)p_θ(v|Y_T)/D(v|Y_T)dv≤∫q(v|Y_T)dv=1.

tower property로 E e≤1이다. q의 training 추정은 허용되지만 validation을 본 뒤 q를 바꾸면 이 적분 증명이 적용되지 않는다. training–validation dependence는 무시하지 않고 실제 조건부분포에 포함한다. training-fit parameter uncertainty를 별도 적분하는 일은 이 e-value 유효성의 필요조건이 아니다. training-measurable q가 정규화되면 충분하며 그 예측 정확성은 power에 영향을 준다. 실제 선택법칙의 미적격, 사후 적응, null-density 상계의 수치 보증 부족은 별개의 한계다. fixed 비음수 weights Σw_k=1의 fold 평균은 선형성으로 유효하지만 의존 fold들의 곱은 일반적으로 유효하지 않다. 예컨대 같은 e∈{0,2}가 각 확률1/2이면 E e=1, E e²=2다. 전체 자료로 covariance/scenario/fold를 고른 현재 적용은 탐색이다. prospective 주장에는 그 선택을 training에 한정하거나 전체 선택절차를 별도로 정당화해야 한다. Gaussian plug-in predictive score 자체를 이 e-value로 바꾸어 부르지 않는다.

## T5. 같은 Gram·다른 형태와 유한 Haar rank

여기서 ell∈{2,3}로 한정한다. 각 ell의 orthonormal real harmonic carrier X_ell∈R^(d×m), d=2ell+1, m=60을 고정한다. R이 SO3의 irreducible orthogonal representation D_ell(R)의 Haar draw이면 E[D_ell(R)X]=0이며 Schur orthogonality로

E[(D X)_aj(D X)_bk]=δ_ab (XᵀX)_jk/d.

Haar O(d) action도 같은 식을 만족한다. 두 법칙 모두 XᵀX를 samplewise 보존한다. 서로 독립인 ell action은 cross-ell covariance0을 준다. 이 같은 second moment가 같은 law를 뜻하지 않는다. ell2 STF의 tr(Q³)/||Q||³는 spatial rotation 아래 고정되지만 O(5)는 같은 norm의 서로 다른 STF spectrum을 연결한다. 두 법칙의 shape/orientation 비교가 가능한 이유다. Gaussian row-isotropy 가정은 O(d) invariance의 충분조건이며 실제 mask/foreground 처리의 자격 증명은 아니다.

독립 pilot로 statistic 변환을 고정하고, 귀무 group-invariance 아래 관측과 B개의 reference가 교환가능하다고 하자. p=(1+Σ1{T_b≥T_obs})/(B+1)은 ties를 약하게 세므로 conservative rank다. ties가 없을 때 각 rank가 균등하고, ties의 weak count는 그 p를 작게 만들지 않는다. group orbit 조건부로 독립 Haar 기준표본과 invariant 관측의 교환가능성을 얻는다. source invariance가 없으면 공식은 계산된 reference rank일 뿐 관측 p가 아니다. pilot의 독립성은 transform 선택과 evaluation rank의 결합을 막는다. Monte Carlo tail interval은 reference simulation 확률의 오차이며 physical uncertainty가 아니다.

O(d) joint orbit의 support는 max_O tr(UᵀOX)=||XUᵀ||_*다. SVD와 orthogonal Procrustes의 trace bound에서 얻으며 독립 ell에는 합한다. 이는 orbit convex hull의 support이고 convex hull 모든 점이 실제 orbit에 있다는 뜻은 아니다. SO3 representation subgroup에는 일반 O(d) 최대식을 그대로 equality로 쓰지 않는다.

## T6. 압축과 선형 식별 가능성

관측 y=Ms에서 target Ls가 모든 s에 대해 식별될 필요충분조건은 ker M⊆ker L이다. 필요성: M(s+h)=Ms인 h∈ker M에 대해 Lh≠0이면 같은 관측의 다른 target이 생긴다. 충분성: y∈im M에 대해 K(y)=Ls로 정의하면 두 preimage의 차이가 ker M에 속하므로 well-defined이며 선형이다. 따라서 L=KM이다.

w≠0인 가중 압축 M=wᵀ, frequency contrast L=lᵀ라면 l이 w의 span 밖에 있을 때 h=l−w(wᵀl)/(wᵀw)는 Mh=0, Lh=||h||²>0의 exact witness다. 실제 SMICA는 beam·ell·polarization·recalibration을 포함한 실제 M을 써야 한다. 알려진 response column에 대한 constrained ILC nulling과 이미 압축된 map에서 arbitrary frequency signal을 복구하는 일은 다르다. moment expansion도 명시된 spectral basis와 remainder 가정이 있어야 한다. 이 결과는 압축의 정보 손실을 증명하며 common foreground의 실제 크기나 B02 physical family atlas를 제공하지 않는다.

## 공통 적용 경계

위 식의 C≼U, bias radius, shared target, conditional likelihood, group invariance, M/L은 각각 독립적으로 입증할 가정이다. 현재 4096 full24 row의 uniform empirical Pi, CMB finite-MC conditional reference Pi, 물리 Pi unknown mass1은 서로 다른 확률 객체다. Q_ref10 또는 CMB fixed scale은 physical MES anchor가 아니다. joint tensor x의 rank/parity와 covariance를 유지하고 F의 undefined sign/denominator strata, Q의 미정의 anchor, G_F의 실제 depth와 processing-window 구별을 보존한다. 이 문서의 독립 검토 전에는 수학 유도 자체도 admission 완료로 표시하지 않는다.


## 추가 자문 유도의 상태와 출처

다음 네 명제는 실제 native Astra 자문 [THEORY_ADVISOR_SUPPLEMENT](reviews/THEORY_ADVISOR_SUPPLEMENT.md)의 직접 증명을 전개한다. `/root/r25_statistics_theory`, requested Astra/xhigh, observed UNKNOWN. 자문은 독립 검토가 아니며 **T7–T10 PENDING_FRESH_INDEPENDENT_REVIEW**다. 기존 frozen distance candidate의 보고서는 여기서 수정하지 않는다. 그 문구·결정은 실제 reviewer/repair 경로에 속한다. 새 CAS4축·물리적 수용·novelty를 주장하지 않는다.

## T7. calibration convex hull, Farkas와 공동 tensor law

유한 target U와 관측 subset O를 두고 h_u∈R^k의 첫 좌표가 항상1이라고 하자. t=|U|⁻¹Σ_U h_u, H=[h_i]_(i∈O)다. Hp=t,p≥0이면 첫 좌표에서 Σp_i=1이므로 t는 관측 column의 convex hull에 있다. 역으로 hull의 convex combination은 feasible p다. 모든 p_i>0인 representation이 존재할 필요충분조건은 t∈relint(conv{h_i})다. 필요성은 hull의 proper supporting face에 t가 있다면 그 face 밖의 양의 weight column이 supporting equality를 깨는 데서 따른다. 충분성은 관측 uniform 평균 hbar가 relint에 있고, t에서 t−hbar 방향으로 약간 더 간 t'가 hull 안에 있음을 이용한다. t=(1−epsilon)t'+epsilon*hbar로 쓰면 hbar 성분이 모든 column에 양의 weight를 준다. t=hbar이면 uniform 자체가 해다.

Infeasible일 필요충분조건은 Hᵀlambda≥0, tᵀlambda<0인 separator의 존재다. feasible이면 pᵀHᵀlambda≥0이므로 그런 witness는 불가능하다. 역으로 compact hull에 t의 projection c를 두고 a=c−t라 하면 aᵀh_i≥aᵀc, aᵀt=aᵀc−||a||²다. 상수 첫 좌표 벡터 e0를 써 lambda=a−(aᵀc)e0로 두면 Hᵀlambda≥0, tᵀlambda=−||a||²<0이다. 관측 column이 없는 empty case는 별도 명시한다.

Cell c의 mass m_c와 관측 수 n_c>0가 고정되면 Σ_(i∈c)p_i=m_c 아래 Σp_i²≥m_c²/n_c이며 equality iff 모든 p_i=m_c/n_c다. cell별 합으로 unique minimum weight-concentration 해를 얻는다. ESS=1/Σp_i²는 independent observation count가 아니다. 현재 full628 unsupported-cell witness는 gap−1/628이고, fine625 velocity functional은 관측에서0이지만 target 평균2547/625 km/s이므로 signed balance조차 불가능하다. 이 수치는 고정 계약의 데이터 주장으로 독립 결과 검토와 구별한다.

유한 차원 tensor space에서 T_u=B h_u+e_u라면 정확 balance에 의해

mean_U T_u−Σ_O p_i T_i=mean_U e_u−Σ_O p_i e_i.

따라서 remainder/transport 가정 없이 outcome mean을 식별하지 못한다. 두 target이 h=1로 같고 관측 T=0, missing T=M이면 target mean M/2는 임의다. 같은 p를 모든12 scalar/vector/STF carrier에 적용한 mu_p=Σp_i delta_(T_i^1,…,T_i^12)는 cross-model·component 의존성을 보존한다. 양의 weights는 원자 support와 convex hull을 보존하지만 occupancy를 바꾼다. 선형 회전 representation R에서 Σp_i R T_i=RΣp_i T_i이므로 동시에 회전하는 full carrier에 equivariant다. 이는 survey MAR·선택확률·physical coverage의 증명이 아니다.

## T8. pair rotation kernel, shared-source covariance와 whitening

N,V의 행을 unit 방향 n_iᵀ와 tangent velocity v_iᵀ라 하자. K=VNᵀ+NVᵀ의 ij성분은 kappa_ij이고 d cos(theta_ij)/dt=a_mu*kappa_ij다. tangency로 K_ii=2n_iᵀv_i=0이므로 모든 off-diagonal pair가 K를 정한다. numerator는 coincident/antipodal 방향에도 정의되지만 theta-dot는 −sin(theta)로 나누어야 하므로 그 경계에서 같은 관측량이 아니다.

rank N=3이고 K=0이면 P=N(NᵀN)⁻¹Nᵀ에 대해 0=(I−P)KN=(I−P)V(NᵀN)이다. 따라서 V=NA. K=N(A+Aᵀ)Nᵀ이므로 양쪽에 N의 left inverse를 적용하면 A+Aᵀ=0이다. 모든3차원 skew A는 common rotation에 해당한다. 역으로 scalar triple product로 rotation pair response는0이다. rank N<3이면 이 증명은 성립하지 않으며 planar 방향의 normal motions 같은 추가 kernel이 가능하다.

Pair row L_ij와 design X에 a_ij=L_ijX라 하면 H_b=mean a_ijᵀL_ij, d_b=H_by, D_b=H_bX다. 따라서 E d=D beta이고 d는 beta 자체가 아니다. common-spin design B는 LB=HB=0이다. 어떠한 joint source covariance Sigma에도 Cov(d)=H Sigma Hᵀ는 정확하다. block-diagonal C0는 별도 working 가정이다. 그 아래에도 shared i를 가진 두 pair는

Cov(kappa_ij,kappa_ik)=(n_jᵀE_i)C_i(E_iᵀn_k)

로 일반적으로0이 아니다. H가 최대117행이고 tangent 좌표가9512개이면 dim ker H≥9395다. 따라서 fullK rotation-only theorem을 압축H의 완전성으로 해석하지 않는다.

C0≻0이면 uᵀHC0Hᵀu=||C0^(1/2)Hᵀu||²이므로 ker(HC0Hᵀ)=ker Hᵀ, range(HC0Hᵀ)=rangeH다. exact d,D의 support는 따르지만 numerical threshold가 버린 양의 mode를 exact-null로 바꾸지 않는다. fixed y-independent W와 Gaussian working law에서 정확히 W Cd Wᵀ=I_r이고 M=WD의 **complete** image/projector P_M를 쓰면 residual mean은0이고 (I−P_M)z의 covariance는 orthogonal projector다. orthonormal basis에서 독립 표준정규 nu=r−rank M개의 제곱합이 되어 T_low~chi²_nu다. nested E1/full image에 대해 P_full−P_E1도 projector이며, E1 mean null일 때만 Delta가 central chi²_(q_full−q_E1)다. E1·full 각각의 residual degrees는 r−q_E1,r−q_full이다. zeroDOF는 explicit degenerate state다.

대신 certified ||W Cd Wᵀ−I||₂≤delta<1이면 residual covariance eigenvalues는1+delta 이하이므로 T를 (1+delta)chi²_nu와 coupling해 upper tail chi²_nu의 survival at T/(1+delta)를 얻는다. projected mean의95%ball radius²는 (1+delta)chi²_r(.95)로 보수적으로 잡는다. statistic/tail/quantile 평가도 보수적으로 처리해야 certified 결론이다. computed residual≤1e−9는 certificate가 아닌 numerical control이다. exact/certified whitening 없이는 ordinary values를 NUMERICAL_WORKING_CHI_SQUARE_APPROXIMATION으로 쓴다. complete model image가 없으면 full-model TAIL_UNRESOLVED다. 작은 mode를 threshold로 삭제한 M=[[1,1],[0,1e−13]], beta=(−1e13,1e13)의 mean(0,1) 반례가 그 이유다. 새 certification algorithm을 가정하지 않고 descriptive fallback과 모든 unprojected/discarded mode를 보존한다.

## T9. Gaussian conditional union-null supremum

고정 training sigma-field T_j에 대해 normalized training-measurable q_j와 D_j≥sup_(theta∈H0)p_theta,j(·|T_j)를 두면 q_j/D_j의 conditional expectation은1이하다. D=∞에는 ratio0을 두고 zero-denominator의 null-measure-zero case는 명시한다. union null H0=∪_s H0s에는 D=max_s sup_theta p_s가 필요하다. denominator를 평균하면 각 null density를 지배하지 않을 수 있다. fixed convex fold average는 의존성 아래에도 expectation≤1이지만 선택된 max나 product는 보장되지 않는다. fair Bernoulli validation 결과를 본 뒤 그 결과에 point mass q를 고르면 각각 normalized이어도 e=2가 항상 된다.

각 고정 covariance shape V_s에서 training T/validation J를 분할하고 A_s=V_JT V_TT⁻¹, S_s=V_JJ−V_JT V_TT⁻¹V_TJ≻0, r_s=y_J−A_s y_T, Z_s=X_A,J−A_s X_A,T라 하자. conditional null mean Z_s beta, covariance sigma² S_s의 logdensity는

−.5[m log(2pi)+m log(sigma²)+logdet S_s+R(beta)/sigma²],

R(beta)=(r_s−Z_s beta)ᵀS_s⁻¹(r_s−Z_s beta), m=|J|다. 먼저 R_s=min_beta R(beta)를 구하고 R_s>0이면 sigma² derivative로 sigmahat²=R_s/m이며

log sup p_s=−.5[m{log(2pi)+1+log(R_s/m)}+logdet S_s].

R_s=0이면 unrestricted sigma→0에서 supremum∞이므로 e=0이다. singular S에는 별도의 measure/support가 필요하며 pseudo-density를 조용히 대입하지 않는다. union-null에서는 이 각 supremum의 max 또는 그 certified upper bound를 쓴다. training-fit uncertainty 적분은 q의 유효성에 필수 조건이 아니다. q의 normalization와 training-measurability가 핵심이며 정확성은 power에 관련된다. 현재 실제 selected/adaptive law의 미적격과 outward-certified null-density bound 부재는 별개 한계다. 이 명제는 Universal Inference §§5–6의 correlated-catalogue 특수화이며 novelty 주장이 아니다.

## T10. E-to-B exact-relation perturbation certificate

computed A_E,A_B∈R^(12×2), y_E,y_B∈R^12와 exact delivered counterpart starred quantities가 operator/vector error bounds eps_AE,eps_AB,eps_yE,eps_yB 안에 있다고 하자. s≤sigma_min(A_E), s>eps_AE≥0, R_E≥||y_E−A_E ctilde||, U_B≥||A_B||를 certified하게 평가한다. 같은 c*가 A_E* c*=y_E*, A_B* c*=y_B*를 만족하면

C=(upper||y_E||+eps_yE)/(s−eps_AE),
Delta_c=(eps_yE+eps_AE C+R_E)/s,
tau0=eps_yB+eps_AB C+U_B Delta_c

는 각각 ||c*||, ||c*−ctilde||, ||y_B−A_B ctilde||의 상계다. 첫 식은 ||A_E*c||≥(s−eps_AE)||c||에서 따른다. 둘째는

A_E(c*−ctilde)=(y_E*−y_E)+(A_E−A_E*)c*+(y_E−A_E ctilde)

에 triangle inequality를 적용하고 s로 나눈 결과다. 셋째는 y_B−A_B ctilde=(y_B−y_B*)+(A_B*−A_B)c*+A_B(c*−ctilde)에서 따른다. error independence는 필요하지 않다. A/y/s/errors의 단위는 K_CMB, C/Delta_c는 무차원이다. residual evaluation error eps_eval가 있으면 관측 residual>tau0+eps_eval가 exact relation을 반증한다. certified residual lower bound까지 쓰면 더 보수적이다. threshold를 넘지 않았다는 사실은 equality의 증거가 아니다. 필요한 bounds가 없거나 s≤eps_AE이면 NUMERICALLY_UNRESOLVED다.

a=1e−5, eta=1e−7, orthonormal u/v,p/q에서 A_E=a[u,u+eta v], A_B=a[p,q]를 두자. exact target anchor2에5e−13 v의 E perturbation을 주면 coefficients가(0,1)→(−.5,1.5)로 바뀌고 B discrepancy는 a/sqrt2≈7.07e−6 K_CMB다. singular ratio>1e−8과 두 구현의 작은 차이는 error certificate가 아니다. 이 결과는 delivered tensor relation만 다루며 physical foreground component 수·cosmological null을 식별하지 않는다.

## 추가 명제의 full-tensor 통계 적용

모든 원자·source ID·operator·covariance·rank와 polar/axial convention을 joint state Z에 보존한다. scalar phi(Z)는 그 함수상이다. valid joint region C가 있을 때만 phi(C)의 simultaneous coverage가 따르며 region이 없는 곳에 coverage를 만들지 않는다. ellipsoid는 내부 확률분포가 아니다. F의 set/support와 named-measure occupancy를 구별하고 Pi_mu(phi,t)=mu{q_phi>t}에서 weighted empirical·Gaussian working·physical selected-source law를 구분한다. e-ratio는 Pi도 posterior도 아니다. Q에는 matching anchor/gauge가 필요하며 physical MES는 unavailable이다. G_F는 실제 지원되는 depth를 요구한다. angle/frequency/fold는 depth가 아니다. 원래17/42, alternate18/42, 역사 allocation·one-use·R9 UNKNOWN은 바뀌지 않는다.
