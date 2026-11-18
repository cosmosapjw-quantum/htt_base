# R69-P1 확장: 일반 low-\ell · 유한 z 광학 · 모든 Bianchi Lie algebra / tilted matter

2026-11-19 (KST). **상태:** 수리적 유도 및 Lie-Codazzi CAS 검산, P1 실제 CF4 sky-only geometry 재사용. 별도 실자료 대우주론 likelihood는 미검증. Root source HEAD 8dd029d934f8fe287691c06c5cf7e256608965b5; 원 R69과 기존 P1–P6 42 science nodes는 변경하지 않음. 이 문서의 일반화는 새 7축 실자료 분석을 완료했다는 뜻이 아니다.

## A. 연구 루프의 향후 고정 규칙

모든 후속 물리 연구 루프의 기본 판정은 *검정력*뿐 아니라 *물리적 설명력*·*기하학적 의미*·*반증 가능한 관측 패턴*이다.
(1) 실제 물리 질문 → (2) signed full tensor/multipole carrier x → (3) GR/kinetic/Sachs/Einstein forward map → (4) Q,Π,F,G_F의 정의가능한 것만 엄격히 유도 → (5) 반례와 극한 → (6) 원자료의 실제 source operator와 covariance → (7) 과학적 해석·중단 조건.
고정된 물리적 기준/관측 scale/null/transport가 없으면 네 양을 임의로 채우지 않는다. 두 개의 scale-free 설명량만 가능하면 그 둘(예: signed STF orbit χ와 full-sky angular occupancy F_Ω)을 내고, 이것들이 Π나 원래 G_F를 대체한다고 주장하지 않는다. 실제로 K와 μ가 제공될 때만 그 intrinsic Q와 F를 네 양의 부분집합으로 인정한다. x는 항상 이 네 결과에 앞선 원천 signed carrier이며 추가 독립 likelihood가 아니다.
기본 탐색 domain은 \ell=0,..,L을 원하는 L까지 선택할 수 있게 열고, z≪1만이 아닌 광학 Jacobi 방정식의 finite-z forward evolution 및 선택된 z_c 주변의 local expansion을 모두 검토한다.
Bianchi 적용은 I만이 아니라 모든 3D Lie algebra satisfying Jacobi, Class A/B, imperfect/kinetic/tilted/multifluid total T_ab을 대상으로 하며 정리의 전제는 일반 Lie algebra에 대해 명시한다.

## B. 일반 low-ell와 finite-redshift의 정확한 계층

부호 (-,+,+,+), u·u=-c², observer→source n. Matter congruence와 observer가 일치하는 regular lightcone vertex에서 H(n)=H[1+d·n+S:nn], d=-A/(cH), S=σ/H∈STF(3), H>0. z→0에서 D_L=cz/H(n)+O(z²). 이 식은 local \ell≤2의 원인이지만 log-distance, finite-z 혹은 boosted-observer field가 \ell≤2만 갖는다는 뜻이 아님.

먼저 exact smooth local series, A=(1-Q(n))/2,
B=(3Q(n)²+Q(n)-1+R(n)-J(n))/6:
D_L(z,n)=cz/H(n)[1+A(n)z+B(n)z²+O(z³)].
여기서 Q(n),R(n),J(n)은 *effective covariant cosmographic coefficients*이며 신호의 CMB positivity Q 또는 MIO Q가 아니다. 정확한 정의·소스별 사용식은 Heinesen arXiv:2010.06534 및 Adamek et al. arXiv:2402.12165. 다항식의 \mathfrak Q, \mathfrak R, \mathfrak J를 별도 물리 source term과 혼동 금지.

임의 smooth reference D_ref(z)에서 eta=ln[D_ref(z)/D_L(z,n)]를 둔다. 그러면
eta = ln[D_ref(z) H(n)/(cz)] - A(n)z - [B(n)-A(n)²/2]z²+...,
ln H(n)=ln H + ln(1+d·n+S:nn).
Leading d,S의 p차 비선형 항은 최대 \ell=2p까지 조화성분을 만들며, 일반 finite z에서 cosmographic q,jerk, curvature, lensing 및 observer-frame boost가 추가 multipoles를 만든다. \ell=4/3을 원래 S/d의 tied polynomial로 얻은 결과는 z→0 및 finite order에서만 성립; \ell=4를 독립 shear 관측량으로 선형 동일시 금지.
일반적으로 \eta_{\ell m}(z)≡∫_{S²}Y^*_{\ell m}(n)\eta(z,n)dΩ, 0≤\ell≤L. Mask가 있으면 관측 \tilde eta_{\ell m}(z)=Σ_{\ell'm'}M_{\ell m,\ell'm'}(z)eta_{\ell'm'}(z)+selection/calibration/PV noise이고 \ell'>L의 leakage도 포함한다.

finite z에서 원칙적 exact map:
1+z(n)=[-k·U_e]/[-k·U_o], D_L=(1+z)²D_A, k^a∇_a k^b=0,
D_A''(λ)=-(R_{ab}k^ak^b/2+|σ_opt|²)D_A with twist-free lightcone, Jacobi vertex BC.
Optical shear obeys the Sachs optical equation with Weyl curvature as source. Tilt changes U_e, U_o; Lie structure determines spatial connection and ray direction evolution. Anisotropic expansion normal shear acts along the ray but is not in general the complete finite-z observable. Solve the Einstein+matter trajectory and ray/Jacobi equations (and source selection), do not use a single scalar χ to reconstruct the sky.
A Taylor expansion at arbitrary nonzero z_c can be used as *effective finite-window* cosmography (Bendtsen–Heinesen–Koksbang arXiv:2608.07008), but its coefficients need not equal local observer θ,σ at z=0.

## C. GENERAL BIANCHI–TILT: 구조상수에서 운동량/형태/설명량까지

**Theorem B1 (Jacobi–Codazzi–tilt–shape; algebraic universal conditional identity, not a new GR theorem).**
Assume a spatially homogeneous Bianchi spacetime with simply transitive 3D Lie algebra, left-invariant spatial metric, geodesic hypersurface-orthogonal future normal n and homogeneous normal lapse, orthonormal invariant frame e_i at each t, zero spatial shift, arbitrary tilted imperfect/kinetic total energy-momentum obeying Einstein equation. Frame e_i may rotate with t, in which case use covariant time derivative D_t, not bare component derivative. Define [e_i,e_j]=C^k_ij e_k and choose
C^k_ij = ε_ijℓ N^{ℓ k} + a_i δ^k_j - a_j δ^k_i, N=N^T, a,N have [length]^-1; σ=σ^T, trσ=0, [σ]=s^-1.
Then:
  (B1a) Jacobi ⇔ N^{ij}a_j=0.
  (B1b) With K^i_j=-(H δ^i_j+σ^i_j)/c (K unit m^-1) and j^N_i=-h_i{}^a T_ab n^b (J m^-3, n²=-1),
    C_i(σ,N,a):= -3σ_ij a^j + ε_ijk σ^j{}_l N^{lk}
     =D_j σ^j_i= -(8πG/c³)j_i^N.
  (B1c) For a single perfect fluid, j_i^N=(epsilon+p)Γ² β_i, Γ=(1-β²)^-1/2, β=v/c; for multi-fluid sum over species with any intrinsic heat/anisotropic flux included in total j. Normal-frame stress of tilted perfect fluids:
    π^N_ij=Σ_A(epsilon_A+p_A)Γ_A² β_{A<i}β_{Aj>}  + transformed intrinsic π (if any).
  (B1d) If total matter obeys the dominant energy condition and ρ_N=T_ab n^a n^b>0, |j^N|≤ρ_N, so
    Q_Lie := c³ |C(σ,N,a)|/(8πG ρ_N) ≤1.
    This is a *physical momentum-cone compatibility gauge*, not a significance or Bianchi label; no measured rho_N means no physical Q numerical bound. At ρ_N=0, DEC forces C=0; gauge ratio undefined.
  (B1e) Hamiltonian:
    ^3R+(6H²-trσ²)/c² = 16πGρ_N/c⁴+2Λ.
    Mixed shear evolution with geodesic normal:
    D_tσ+3Hσ = D := (8πG/c²)π^N - c²(^3R)_STF.
    I2=trσ²>0,I3=trσ³, chi=√6 I3/I2^(3/2):
    D_t chi=3√6/I2^(3/2)[tr(σ²D)-(I3/I2)tr(σD)].
    Under frame rotation σ→RσR^T, extra [Ω,σ] vanishes from traces, so the shape derivative is frame invariant. Isotropic H dilution cancels *only from chi*, not generally from shear amplitude or its covariant direction.
Proof: Koszul connection 2Γ_ijk=C_ijk-C_jki+C_kij; for homogeneous spatial STF, D_jσ^j_i=Σ_{jm}[Γ^j_jm σ^m_i−Γ^m_ji σ^j_m], expand using C to obtain B1b; direct Jacobi triple [e1,[e2,e3]]+cyclic gives -2Na. Insert ADM constraints. Flux bound follows DEC. Tracefree spatial Einstein evolution gives B1e, and differentiate I2/I3, cancelling -3H terms. CAS verifies the algebra for arbitrary symmetric N and S (VERIFY_BIANCHI_LIE.py). No novelty priority or global dynamical classification claim.

**Examples and explanatory consequences, all Bianchi types not just Type I**
- I: N=a=0 ⇒ j_total=0. One perfect fluid with epsilon+p>0 must have β=0, but two equal and opposite tilted dust fluids have j_total=0 and π^N≠0, so shear shape can still evolve.
- II, Class A: N=diag(ν,0,0), a=0, σ_12=s gives C_3=−νs. Thus noncommuting σ,N can support nonzero normal momentum/tilt even though a=0. Numerical symbolic ν=.3,s=.2 gives C_3=−.06 (normalized units). This is momentum compatibility, not full initial data by itself.
- V, Class B: N=0,a≠0. If j_total=0 ⇒ σ a=0, so any nonzero STF σ has eigenvalues (λ,−λ,0), chi=0. With tilted j≠0 this conclusion *fails*. Instantaneous dimensionless example c=8πG=1,a=.1 e3, σ=diag(-1/6,-1/6,1/3), dust normal ρ_N=1, β=.1 e3 gives j=.1 e3, C=−.1 e3, chi=+1, Q_Lie=.1. Type-V ^3R=-6a²=-.06; choosing H²=(2ρ_N−^3R+trσ²)/6=(2+.06+1/6)/6 satisfies Hamiltonian at that instant. Do not claim a completed self-consistent global solution or a cosmological detection.
- VI_h,VII_h/IV (Class B), VIII/IX (Class A), III as VI_-1, and every admissible Lie algebra obey the same B1 identities with type-specific N,a; no single chi value identifies the family. Beware degeneracies n_i=0, H=0, σ=0, null fluids, finite-z observer tilt and changing eigenframes. The Kantowski–Sachs model is not a simply transitive Bianchi case and needs a separate symmetry-class theorem.

## D. 정확한 5뷰 해석, 관측 스케일 없을 때의 두 설명량

x: actual signed tensor/multipoles (NOT scalar power alone), source congruence + epoch + frame + optical/kinetic/mask operator.
Q (when physical body exists): Q_H=−min_{|n|=1}(d·n+S:nn) for Hdir>0; Q_Lie above for Einstein momentum DEC; Q_gamma from radiation moment cone; distinguish these Q labels and the statistical whitening norm.
Π: P_{matched null/source law}[T≥T_obs], with full cross-multipole and cross-depth covariance, handling unknown-axis and Bianchi stratum nonregularity. Without null/calibration Π=UNAVAILABLE.
F: select bounded K, a physically motivated μ and event. If only full-sky angular morphology can be defined, F_Ω(z)=area{n: eta(z,n)>sky mean eta(z,·)}/4π. This is *solid angle* not energy or model-parameter mass, and depends on actual same source observer frame and full-sky transfer. If no sky reconstruction, F may be unavailable.
G_F: only when same type of F at transported physical epochs/depths, valid selection and joint covariance; raw \eta(z2)-\eta(z1), harmonic slope or different catalog releases are G_x-type auxiliary quantities, NOT an automatic G_F.
No calibrated amplitude law: use at most the justified geometrical pair (i) signed shape/orbit χ, and (ii) intrinsic F_Ω *if sky map and area measure exist*; or intrinsic Q+F if their physical bodies are actually specified. If neither exists, keep only source-qualified x and constraints; do not force even two fictional outputs.

## E. Seven axes: explicit physical target and x→four possibilities

A1 P1 tensorized inference: x=[signed STF5+coupled low-ell (η_lm(z), source cov)] rather than five independent cosmological parameters. Q=Hdir positivity or optical physical body; Π=calibrated heldout likelihood; F=sky exceedance geometry; G_F=transported sky-event depth evolution. First nontrivial prediction: tied \ell=3 (d⊗S), \ell=4 (S⊗S), with finite-z 𝔔/𝔍 counterterms; original CF4 31,649 geometry rank12 but l4 small.
A2 P2 low-ell CMB: x=[a_lm^{T,E,B},pi_gamma/rho,kinetic flux], Q=photon PSD moment-cone, Π=matched T/E/B sky-noise/cosmic variance law, F=photon energy directional occupancy ONLY if higher angular moments/closure known, G_F=NA for one sky. The physical map is Einstein–Boltzmann propagation of photon distribution, not present-day normal σ or scalar C2.
A3 radio source counts: x=d_b(z,S_cut) plus even/odd multipoles and source associations; Q=causal beta only after Doppler/count slope source response is fixed; Π=clustering+mask/null; F=source fraction under survey measure; G_F=real redshift physical bins with transfer, NOT flux-cut changes. Kinematic d_b=k_b β+u_b with population slope k_b, unknown intrinsic u_b.
A4 P6 kinematics: x=[θ,σ5,ω3,A3,relative β3] and optical response; Q=causal speed and Einstein constraints, Π=CF4/Gaia source-qualified combined null only, F=normal-frame directional expansion sky areas, G_F=physical evolution with correct tetrad. No vorticity in the leading Hdir scalar.
A5 P5 Bianchi: x=[a3,N6,σ5,ρ_N,j_N,π_N,β species], Q=Q_Lie if DEC+ρ known and/or photon positivity; Π=Bianchi family-specific optical/kinetic likelihood with nonregular strata; F=normal-frame angular FΩ or explicitly normalized physical-state measure, not a uniform measure on noncompact Lie-algebra space; G_F=Einstein+kinetic optical forward time history. General theorem B1 applies Class A/B with tilt.
A6 P3 directional H(z,n): η=ln[D_ref/D_L] and H_D^{-1}=d(D_L/(1+z))/d(... appropriate distance), exact R64 formula H_D/H_ref=e^η/(1−Bη_z) only in its declared flat reference and D_L convention; Q=derivative positivity with source physical domain, Π=same-source null, F=physical sky positive/negative expansion anisotropy area, G_F=matched depth if optical transport qualified.
A7 P4 observer boost vs global tilt: x=[u_O,u_M,u_R, normal n histories], Γ_MR=−g(u_M,u_R)/c² local invariant; Q=relative causal beta, Π=radio+CMB+Gaia+kSZ with shared physical source model, F=chosen bounded velocity hyperboloid measure, G_F=transported physical tilt history. Local aberration/observer acceleration is not global matter tilt.

## F. R1–R10 addendum accounting and stop rule

R1: generalized user objective and 6-paper/7-axis identities fixed.
R2: R68/R69/R61/R67 sources and Heinesen/Maartens/Adamek/Kalbouneh, tilted Bianchi source and 2026 arbitrary-z paper inspected.
R3: local physical vs apparent tensor, source law, Lie conventions, units and four-view semantics typed.
R4: local high-harmonic, arbitrary-z Sachs, Lie algebra/tilt, Fisher/sky occupancy alternatives enumerated.
R5: general Bianchi Lie-Jacobi-Codazzi momentum/shape identities explicitly derived, local log-H harmonic closure reused.
R6: Type I compensated tilt and Type V tilted χ counterexamples, mask, nonregular null, arbitrary optical nuisance checked.
R7: exact arbitrary Jacobi/Codazzi CAS, Type I/II/V finite examples and shape-rate finite difference; P1 previously ran actual CF4 geometry. No physical cosmic null.
R8: select B1 identity and finite-z exact transfer as explanatory bridge; physical anomaly/bound unavailable.
R9: forward model contracts and source-specific x/Q/Π/F/G_F statuses for seven axes.
R10: preserve supplementary result and future-loop rule. **Native subagent: NOT_RUN (not exposed); independent full scientific review: NOT_RUN; repo push: NOT_REQUESTED/NOT_RUN.**
Next loop target after P1: P2 photon kinetic moments linked with curved/tilted Bianchi Lie connection via Boltzmann hierarchy and optical transfer, then its real Commander source systematics. Do not add arbitrary posterior/p-value, and do not edit legacy six-paper gates.
