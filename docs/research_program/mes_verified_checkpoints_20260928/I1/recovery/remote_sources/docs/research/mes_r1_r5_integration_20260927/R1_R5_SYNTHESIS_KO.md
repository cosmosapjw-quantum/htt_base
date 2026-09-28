# R1–R5 MES tensor/optical 통합

2026-09-28 KST. Owner: LOCAL_CODEX_THEORY_HANDOFF_INTEGRATOR. Scope: 원본 조건부 이론과 현재 코드의 문서 통합. C0, transfer source none. 새 scientific admission·실관측 결과·신규성 판정은 없다. 원본은 intake에 byte-preserved이고 통합 정정은 이 디렉터리에만 둔다.

## 원문과 단계 identity

식별키는 연구계열+날짜+work-unit+원본 hash다. 2026-09-20 GENERALIZED_TENSOR_R3/R4/R5를 2026-09-27 단계와 교체하지 않는다. 전체 원본 ZIP identity와 proof/check/decision 경로는 IMPORT_RECEIPT와 CLAIM_LEDGER에 있다. 아래 보고서는 접근용 동일 byte 사본이며 원문을 대체하는 새 판정이 아니다.

| 단계 | 날짜 | 전체 보고서 | report SHA-256 |
|---|---|---|---|
| R1 | 2026-09-20 | [R1_2026-09-20_MES_FRESH_RESEARCH_R1_KO.md](../../../incoming/mes_r1_r5_20260927_412bca18a18cded4/MES_R1_R5_HANDOFF_20260927/reports/R1_2026-09-20_MES_FRESH_RESEARCH_R1_KO.md) | `9d0c6b4893e5e9e2022c03ef85241d7209b54d676449df814e32c795cea52a0a` |
| R2 | 2026-09-20 | [R2_2026-09-20_MES_GENERALIZED_TENSOR_R2_KO.md](../../../incoming/mes_r1_r5_20260927_412bca18a18cded4/MES_R1_R5_HANDOFF_20260927/reports/R2_2026-09-20_MES_GENERALIZED_TENSOR_R2_KO.md) | `1838f89f5782f0b32199851624d02a661bb8245dca06836144e69c9b541aa435` |
| R3 | 2026-09-27 | [R3_2026-09-27_MES_R3_OBSERVABLE_JET_AND_SOURCE_BOUNDS_20260927_KO.md](../../../incoming/mes_r1_r5_20260927_412bca18a18cded4/MES_R1_R5_HANDOFF_20260927/reports/R3_2026-09-27_MES_R3_OBSERVABLE_JET_AND_SOURCE_BOUNDS_20260927_KO.md) | `31b55cfaf7e3f0c40907ee4386a5fc424cd7066c1d989d55019de41a956227aa` |
| R4 | 2026-09-27 | [R4_2026-09-27_MES_R4_REPORT_KO.md](../../../incoming/mes_r1_r5_20260927_412bca18a18cded4/MES_R1_R5_HANDOFF_20260927/reports/R4_2026-09-27_MES_R4_REPORT_KO.md) | `b982b05898696dcaa04d566e69fa97363b1c97e880d7f5307235afb7b7af76fb` |
| R5 | 2026-09-27 | [R5_2026-09-27_MES_R5_REPORT_KO.md](../../../incoming/mes_r1_r5_20260927_412bca18a18cded4/MES_R1_R5_HANDOFF_20260927/reports/R5_2026-09-27_MES_R5_REPORT_KO.md) | `fb6e527cf2067e296c2f1bfa212cc0041f874ee256b6408937a2af7352807410` |

## 물리 목표에서 정확한 optical/radiation identity로

목표는 동일 selected data·frame·source·근사·물리 전제에서 Θ,σ,ω,A,β의 방향·부호·형태·상관을 보존하고 같은 조건의 reference 경계와 비교하는 것이다. 서로 다른 rank/parity를 한 scalar norm으로 먼저 합치지 않는다. R2의 묶음은 scalar expansion displacement, STF shear, axial vorticity, polar acceleration 및 polar tilt다. H*>0와 Θ_ref를 따로 고정한다. H=Θ/3 정의로 얻는 Θ/H=3은 팽창 이탈 측정이 아니다.

R1.SHEAR.LB는 한 사건의 정확한 STF 전단 연산자를 제공한다. B는 물리적 full-sky bolometric density이고 M_r=∫B e^⊗r dΩ다:

\[
L_B(S)=SM_2+M_2S-M_4:S-I(M_2:S)/3,
\quad S:L_B(S)\ge\lambda_{min}(M_2)\|S\|_F^2.
\]

이는 자기수반 5×5 block이며 brightness ℓ=0,2,4만 쓴다. 비음수 nonzero L1 density이면 M2>0이고 등방값은 8ρ/15이다. near-concentration의 conditioning은 별도다. 특이 angular measure에 관한 addendum의 더 약한 조건은 원 final decision이 전체를 판정한 것으로 확대하지 않는다. 관측 mask/noise는 이 양의 물리장과 동일하지 않다.

R2.RADIATION.WEAK는 R1 block을 포함하는 정확 all-kinematics 법칙을 이미 유도했다. ψℓ=e_<Aℓ>의 ambient homogeneous derivative로

\[
J_{A_\ell}=\int B\{(a+Se+\omega\times e)\cdot\partial_e\psi_\ell+
[4H+(1-\ell)S:ee+(2-\ell)a\cdot e]\psi_\ell\}\,d\Omega.
\]

E^4 f 에너지 경계항 소멸이 필요하며 bolometric 법칙에는 Planck 조건이 필요하지 않다. 온도 multipole와 연결할 때에만 blackbody/spectral 조건을 추가한다. J0=4Hρ+S:M2+2a·M1, J1=4HM1+SM1+ω×M1+(ρI+M2)a, J2=4Hπγ+L_B(S)+2a_<a M1_b>+[Rω,M2]다. 무한 hierarchy의 시간발전을 ℓ≤4에서 닫았다는 뜻은 아니다. R5 부록의 shear 재유도를 전체 exact radiation 미완료로 읽지 않는다.

광학 R=H+a·e+S:ee, V=−P_e(a+Se)−ω×e는 정확한 photon generator다. R2의 inverse는 H=<R>, a=3<eR>, S=15<ER>/2, ω=−3<e×V>/2이며 동일 L2 가중치의 inverse norm은 √3다. 이 수학적 norm을 실제 covariance 대신 쓰지 않는다.

## residual/jet 조건이 실제 제약을 만든다

정적 B는 L_B를 정하지만 시간·공간 미분, collision, 나머지 운동학의 r을 주지 않는다. R1의 정확 집합은 L_B^-1 R이고 R가 전공간이면 전단도 전공간이다. R2는 A_B k∈R와 물리 조건 C_phys를 교차하는 joint body로 확장한다. 양의 전단 block이나 알려진 잔차 연산자의 rank12가 관측 식별성을 보장하지 않는다.

R3는 실제 nearby-source 관측을 별도로 연결한다:

\[
\mathcal H(n)=H-a\cdot n+\sigma:nn,
\qquad\kappa_0(n)=P_n\sigma n+\omega\times n.
\]

같은 emitter/observer congruence의 A는 leading proper motion에서 상쇄된다. 별도 observer acceleration drift는 다른 carrier다. ideal calibrated frame의 rank12, 거리만의 rank9, free frame spin quotient rank9는 보고서에 기록된 검산 범위다. R3 별도 raw와 독립 판정 파일은 미확보이며 embedded code/returned text만 직접 읽었다.

유한거리 source error는 LD+v/D 같은 유계 함수와 거리변환 remainder로 들어간다. L,v의 물리값은 미확보다. Nongeodesic/collision/Thomson 확장은 FIRST ORDER 및 exploratory 보충 판정 범위다. C0=0만으로 temperature spectral closure가 되지 않는다. η1=Γ(β_e−ϑ1)의 inverse는 Γ>0에서만 정의되며 Γ=0에서 tilt channel은 미식별이다. ∫Γdt>0는 점별 Γ_min>0나 ∇Γ bound를 주지 않는다.

R4는 두 별도 branch를 제공한다. 공간균질 normal branch에서는 C와 SPD h의 Koszul 연결로 Dbar T의 모든 covariant slot을 계산하고 두 번째 미분의 derivative index에도 connection을 적용한다. crG, c²r(r+1)G²는 coarse bound다. h→λ²h에서 connection→λ^-1 connection이므로 Lie algebra 이름만으로 rate budget이 생기지 않는다. normal A=ω=0을 tilted/general 관측 결과로 옮기지 않는다. Exact tilted 1-jet adapter는 K,β,b와 full connection을 입력받는다.

일반 optical branch의 세 거리 보상은 y(r)=u/r+g(r)+e(r), 공통 u와 C² g, 동일 frame/response/distance 조건에서 k0hat=−2y(D)+5y(2D)−2y(4D)다. sharp remainder 7MD², equal independent noise variance33s², equal deterministic error≤9δ를 함께 보존한다. finite-width shell이면 실제 <1/r>,<r>와 Peano kernel을 다시 써야 한다. frame spin과 공통 calibration은 남는다. 원 세 shell 또는 가역 (k0,u,q)와 joint covariance를 유지한다.

세 보상 출력은 동일 원자료의 가역 변환이다:
\[
\widehat u=\frac{8D}{3}y(D)-4D y(2D)+\frac{4D}{3}y(4D),\qquad
\widehat q=\frac{y(D)}{3D}-\frac{y(2D)}D+\frac{2y(4D)}{3D}.
\]
q=g'(0)이며 나머지가 없을 때만 정확하다. 나머지는 같은 g에서 오는 joint residual image다. 원자료 likelihood와 변환 likelihood를 독립 자료처럼 곱하지 않는다. (R4 Eq.15)


## joint feasible set와 target별 boundedness

R5는 R4 exact jet를 고정 homogeneous tilt p에서 12×9 affine map k=k_C+A(p)j로 닫는다. q=cK 대칭6성분, b=cE0p 3성분이며 |p|<1이다. boost S와 W=S^-1, L_ij=−c gamma^k_ij p_k로

\[
B=gS(q+L)W+g^2p(Sb)^T,\quad
 a=g^2\{Sb+W(q+L)^Tp\},\quad B-pa^T=gW(q+L)W.
\]

q=g^-1 S(B−pa^T)S−L, b=W(a−B^Tp)가 역산이므로 rank9이며 ω−p×a/2=S w_C의 세 affine 제약이 있다. R3 general-observable rank12와 대상·가정이 다르다.

자유 b는 δa=z, δB=pz^T의 rank3 image를 만든다. p≠0에서 개별 shear/A에 무제한 방향이 있어도 Θ−p·a, σ−STF(pa^T), ω−p×a/2는 b-free다. 이를 physical shear로 재명명하지 않는다. nonempty compact J0+free linear N의 target image는 P A N=0일 때 그리고 그때만 유계다. arbitrary nonconvex recession-cone 정리로 확대하지 않고 empty set은 inconsistency로 남긴다.

Retained R3 radiation 식의 timejet block F12(x,Y)=(x+2Yp/5,Y+STF(px^T))는 det=(1−p²/5)²(1−4p²/15)>0, rank8이다. 실제 gF12에는 determinant g^8이 더해진다. 자유 v1,v2는 retained 8개 식을 모두 흡수한다. 이 결론은 unrestricted algebraic domain에 한정되며 positivity·weak regime·finite time·matter 조건을 버리지 않는다. exact finite-tilt geometry가 discarded radiation products를 복원하지 않는다. 같은 ξ=(geometry,β,j,radiation jets,source,remainder,frames,calibration)로 관측과 물리를 교차해 Xi(d)를 만든다.

## 관측 식별공간 → reference → tensor statistics/likelihood

자료 공간 law와 nuisance projection으로 I=range(R^T P R)를 먼저 정한다. reference는 P_I B로 투영하며 B∩I는 미관측 성분을 0으로 설정하는 추가 가정이다. R9의 support/coverage machinery는 실제 common state-jet-anchor event를 요구하므로 R3의 형식 연결로 data law가 생기지 않는다.

Reference upper bound, attainable maximum, declared sensitivity scale는 별개다. 원전 MES geodesic/first-order/all-observer derivative 조건, repo 등록 계수 및 nongeodesic attribution 미확보, 선언한 radius를 각각 표기한다. Θ나 β의 보편 MES ceiling은 없다. scalar sector bounds만 있으면 product gauge=max sector fraction이며 제곱합 ellipsoid를 발명하지 않는다.

Displacement y=k−k_ref, radial boundary ρ_B와 선언 metric에서 signed T=y/ρ_B(y/||y||), ||T||=γ_B(y), Q_outer=T⊗T, F_amp=||T||²다. amplitude margin은 D=100(1−√F_amp), quadratic occupancy는 100F_amp로 구분한다. Q_outer는 T→−T를 구별하지 못하므로 원 harmonic carrier와 signed T를 유지한다. same-data numerator/denominator는 같은 Xi 위에서 전파한다. R2 V1의 uncentered likelihood를 적용하지 않고 k∈k_ref+B를 쓴다.

q≥0이고 법칙을 선언한 경우에만 Pi_tail(q)=E[(Q_outer/F_amp)1(F_amp>q)]이며 F=0 integrand=0, trace=P(F_amp>q)다. G_tensor=T_a⊗(U T_b)/F_b는 isometric physical transport 및 F_b>0에서 norm²=F_a/F_b다. Legacy signed x,Q_gauge,F_support,G_path는 별도 정의이며 전체 x와 positive norm의 동일성을 만들지 않는다. deterministic feasible set, confidence region, posterior/sampling law를 혼합하지 않는다.

R5 비가환 disk는 하나의 (x,z)가 shear·omega·a를 함께 정하는 sensitivity fixture다. 선언된 equal-block 1/√3와 radii에서 J^TJ=I2, F=x²+z², D∈[0,100]이다. uniform area law를 따로 선언해야 Pi=(1−q)JJ^T/2를 계산한다. 실제 우주 percentage나 posterior가 아니다.

## 별도 Bianchi I branch와 claim ceiling

R1 끝점 K_opt는 일반 이론의 필수 전제가 아니다. 공통 등방 방출·collisionless Bianchi I에서 Y=n^T M n, K_opt=log(M/det(M)^(1/3))/2가 성립한다. 고정 주축에서만 K_opt=∫σdt를 쓴다. a_o=1, I=∫a^-3dt, W(s)=a³(s)∫_*^s a^-3dt, J=∫W P ds이면 σ_o=(K_opt+J)/I다. stress radius는 ||σ_o−K_opt/I||≤∫Wp/I이다. 누적 광학 변형, 현재 전단, 전역 almost-FLRW를 서로 대체하지 않는다. 전체 Einstein–matter compatibility와 물리 응력 예산은 남는다.

R1/R2 exact identities의 채택은 유지한다. R3 conditional body/observable 연결과 exploratory source 보충을 나누고 R4 V1 구현 실패/수정 V2, R5 등록 전 kinematic CAS/등록 후 radiation disk를 보존한다. 이번 통합은 이론을 문서에 반영한 것이며 production 구현 검증·실관측 likelihood·empirical percentage·native family identification의 완료가 아니다. 다음 연구는 기존 exact identities의 재유도보다 하나의 target과 실제 source/frame/timejet budget의 대응을 먼저 좁혀야 한다.
