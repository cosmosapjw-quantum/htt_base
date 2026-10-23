# 조건부 방법의 수학적 유도

Owner: HTT 방법 연구. Source base: `10f3ea585c6608e794900efe7e4f8f42c0747a3b`.
상태: **DERIVED_PENDING_INDEPENDENT_REVIEW**. 기존 Astra 자문 계약의 식을 명시적 가정 아래 전개한 문서다. 새 물리 법칙, 관측 calibration 또는 CAS 4축 검증을 주장하지 않는다. 출처의 일반 정리와 아래 직접 유도를 구별한다. 일차 문헌의 적용 절과 한계는 [METHOD_SOURCE_NOTES](METHOD_SOURCE_NOTES.md)에 있다.

## T1. 공분산 상계와 contrast 검정

가정: d∈R^r, E d=0, Cov(d)=C, 결정론적 V≻0와 C≼V가 주어진다. 그러면 T=dᵀV⁻¹d≥0이고

E T=tr(V⁻¹C)=tr(V⁻¹/²CV⁻¹/²)≤r.

따라서 Markov 부등식으로 Pr(T≥r/α)≤α (0<α<1)다. Gaussian d라면 B=V⁻¹/²CV⁻¹/²의 고유값 λ_i∈[0,1]를 써 T의 법칙을 Σλ_i Z_i²로 표현할 수 있다. 같은 독립 표준정규 Z_i에서 Σλ_i Z_i²≤ΣZ_i²이므로 chi-square_r upper tail이 보수적이다. 비Gaussian에서는 이 결합 주장을 쓰지 않는다. 평균이 0이 아니면 E T에 μᵀV⁻¹μ가 추가되어 영가설 경계가 달라진다.

현재 적용: μ24,C24와 보정 M24→Y18를 유지한다. H=[[-1,1,0],[0,-1,1]]⊗I6, A=HM, d=Aμ24, Vτ=A(C24+τ²I24)Aᵀ. A가 row rank12이면 AAᵀ≻0이며 q=τ²에 대해

dT/dq=−dᵀVτ⁻¹AAᵀVτ⁻¹d<0 (d≠0).

따라서 T(0)보다 낮은 양의 threshold의 crossing은 유일하다. 이미 threshold 아래면 nonnegative crossing이 없다. C24+τ²I가 실제 공분산의 상계라는 가정은 관측으로 입증되지 않았다. 현재 curve와 standalone α=.05, 비교용 1/80은 탐색적 reference이며 R9 alpha를 재사용하지 않는다. 이 12-contrast 귀무는 기존 slope6=0과 다르다.

## T2. bias ball의 정확한 witness와 support

V≻0, 선형 A∈R^(r×p), 고정 d, ||b||₂≤δ에서 min ||V⁻¹/²(d−Ab)||₂²를 생각한다. z=V⁻¹/²d, B=V⁻¹/²A=U diag(s_i) Wᵀ를 thin SVD로 쓰고 y=Uᵀz라 한다. 목적함수는 Σ(y_i−s_i c_i)²+||(I−UUᵀ)z||²이고 불필요한 ker B 성분은 최소 norm 해에서 0이다. unconstrained 최소 norm 해는 c_i=y_i/s_i다. δ≥||B†z||이면 이것이 해다. 그보다 작고 δ>0이면 Lagrange 조건으로

c_i=s_i y_i/(s_i²+λ), λ>0,
Σ s_i² y_i²/(s_i²+λ)²=δ².

좌변은 관련 y가 비영이면 λ에 대해 연속·엄격 감소하므로 유일한 root다. δ=0은 b=0으로 직접 계산한다. B가 full row rank이면 영 residual에 필요한 최소 radius는

δ0=||Aᵀ(AAᵀ)⁻¹d||₂,

왜냐하면 whitening이 Ab=d의 해집합을 바꾸지 않기 때문이다. rank가 부족하면 잔류 직교 성분을 보존하며 이 식을 무조건 쓰지 않는다. coefficient bias 단위·metric을 계약에서 고정해야 radius를 해석할 수 있다.

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

고정 training/validation 분할 (Y_T,Y_V)에 대해 q(·|Y_T)가 적분1인 비음수 density이고, 귀무 family p_θ(·|Y_T)의 실제 conditional density를 denominator D=sup_(θ∈Θ0)p_θ(·|Y_T)가 지배한다고 가정한다. 같은 dominating measure를 쓰고, D=0인 null 확률0 영역의 e 정의를 명시한다. e=q(Y_V|Y_T)/D(Y_V|Y_T)이면 각 귀무 θ에서

E_θ[e|Y_T]=∫q(v|Y_T)p_θ(v|Y_T)/D(v|Y_T)dv≤∫q(v|Y_T)dv=1.

tower property로 E e≤1이다. q의 training 추정은 허용되지만 validation을 본 뒤 q를 바꾸면 이 적분 증명이 적용되지 않는다. training–validation dependence는 무시하지 않고 실제 조건부분포에 포함한다. fixed 비음수 weights Σw_k=1의 fold 평균은 선형성으로 유효하지만 의존 fold들의 곱은 일반적으로 유효하지 않다. 예컨대 같은 e∈{0,2}가 각 확률1/2이면 E e=1, E e²=2다. 전체 자료로 covariance/scenario/fold를 고른 현재 적용은 탐색이다. prospective 주장에는 그 선택을 training에 한정하거나 전체 선택절차를 별도로 정당화해야 한다. Gaussian plug-in predictive score 자체를 이 e-value로 바꾸어 부르지 않는다.

## T5. 같은 Gram·다른 형태와 유한 Haar rank

각 ell의 orthonormal real harmonic carrier X_ell∈R^(d×m), d=2ell+1, m=60을 고정한다. R이 SO3의 irreducible orthogonal representation D_ell(R)의 Haar draw이면 E[D_ell(R)X]=0이며 Schur orthogonality로

E[(D X)_aj(D X)_bk]=δ_ab (XᵀX)_jk/d.

Haar O(d) action도 같은 식을 만족한다. 두 법칙 모두 XᵀX를 samplewise 보존한다. 서로 독립인 ell action은 cross-ell covariance0을 준다. 이 같은 second moment가 같은 law를 뜻하지 않는다. ell2 STF의 tr(Q³)/||Q||³는 spatial rotation 아래 고정되지만 O(5)는 같은 norm의 서로 다른 STF spectrum을 연결한다. 두 법칙의 shape/orientation 비교가 가능한 이유다. Gaussian row-isotropy 가정은 O(d) invariance의 충분조건이며 실제 mask/foreground 처리의 자격 증명은 아니다.

독립 pilot로 statistic 변환을 고정하고, 귀무 group-invariance 아래 관측과 B개의 reference가 교환가능하다고 하자. p=(1+Σ1{T_b≥T_obs})/(B+1)은 ties를 약하게 세므로 conservative rank다. ties가 없을 때 각 rank가 균등하고, ties의 weak count는 그 p를 작게 만들지 않는다. group orbit 조건부로 독립 Haar 기준표본과 invariant 관측의 교환가능성을 얻는다. source invariance가 없으면 공식은 계산된 reference rank일 뿐 관측 p가 아니다. pilot의 독립성은 transform 선택과 evaluation rank의 결합을 막는다. Monte Carlo tail interval은 reference simulation 확률의 오차이며 physical uncertainty가 아니다.

O(d) joint orbit의 support는 max_O tr(UᵀOX)=||XUᵀ||_*다. SVD와 orthogonal Procrustes의 trace bound에서 얻으며 독립 ell에는 합한다. 이는 orbit convex hull의 support이고 convex hull 모든 점이 실제 orbit에 있다는 뜻은 아니다. SO3 representation subgroup에는 일반 O(d) 최대식을 그대로 equality로 쓰지 않는다.

## T6. 압축과 선형 식별 가능성

관측 y=Ms에서 target Ls가 모든 s에 대해 식별될 필요충분조건은 ker M⊆ker L이다. 필요성: M(s+h)=Ms인 h∈ker M에 대해 Lh≠0이면 같은 관측의 다른 target이 생긴다. 충분성: y∈im M에 대해 K(y)=Ls로 정의하면 두 preimage의 차이가 ker M에 속하므로 well-defined이며 선형이다. 따라서 L=KM이다.

가중 압축 M=wᵀ, frequency contrast L=lᵀ라면 l이 w의 span 밖에 있을 때 h=l−w(wᵀl)/(wᵀw)는 Mh=0, Lh=||h||²>0의 exact witness다. 실제 SMICA는 beam·ell·polarization·recalibration을 포함한 실제 M을 써야 한다. 알려진 response column에 대한 constrained ILC nulling과 이미 압축된 map에서 arbitrary frequency signal을 복구하는 일은 다르다. moment expansion도 명시된 spectral basis와 remainder 가정이 있어야 한다. 이 결과는 압축의 정보 손실을 증명하며 common foreground의 실제 크기나 B02 physical family atlas를 제공하지 않는다.

## 공통 적용 경계

위 식의 C≼U, bias radius, shared target, conditional likelihood, group invariance, M/L은 각각 독립적으로 입증할 가정이다. 현재 4096 full24 row의 uniform empirical Pi, CMB finite-MC conditional reference Pi, 물리 Pi unknown mass1은 서로 다른 확률 객체다. Q_ref10 또는 CMB fixed scale은 physical MES anchor가 아니다. joint tensor x의 rank/parity와 covariance를 유지하고 F의 undefined sign/denominator strata, Q의 미정의 anchor, G_F의 실제 depth와 processing-window 구별을 보존한다. 이 문서의 독립 검토 전에는 수학 유도 자체도 admission 완료로 표시하지 않는다.
