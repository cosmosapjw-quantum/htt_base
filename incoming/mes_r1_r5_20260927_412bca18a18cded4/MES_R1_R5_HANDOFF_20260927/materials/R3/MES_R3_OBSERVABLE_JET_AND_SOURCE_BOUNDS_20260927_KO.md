# MES R3 — 실제 광학 관측과 비측지 복사 source를 잇는 조건부 텐서 추론
2026-09-27 KST
Work unit: MES_R3_OBSERVABLE_JET_AND_SOURCE_BOUNDS_20260927


## 판정과 이번 진전


독립 판정: PROMOTE_CONDITIONAL_THEORY. 관측 광학 연결·명시적 유계 잔차·공동 추론 계약은 다음 이론 단계에서 사용 가능하다. 비측지·collision-source 확장은 이번에 사후 추가한 exploratory derivation이며 계수 대수를 실제 Wolfram에서 확인했다. 실제 데이터 분석, 관측 제약 수치, 일반 비선형 MES 정리, 15성분의 실자료 식별은 수행·주장하지 않는다.


이번 루프는 R2를 폐기하지 않고, 원 저장소의 이미 확보된 내용을 적극 재사용했다. 새 진전은 다음 세 부분의 연결이다.
1. 추상적인 photon ray generator R,V와 별개로 실제 nearby-source distance–redshift 및 proper motion의 선도계수를 운동학량에 연결.
2. geodesic 복사식에 acceleration과 collision moment를 되살려 가속도·와도·electron tilt가 필요로 하는 source/derivative budget을 명시.
3. 그 공동 jet/source 집합을 기존 R9의 nuisance-aware confidence image와 R2 tensor normalization에 연결.


수학적 신규성은 주장하지 않는다. 특히 배경 팽창항을 상쇄한 geodesic shear/vorticity 식은 R7 T3의 재사용이다.


## 입력·authority·하네스


원 저장소 main을 현재 조회하여 commit 85e261f49c9df9389946eef74d80c1ccd0509816, tree f6a72851ff39dbb8db454143c3d547475ac2f2f7을 기준으로 읽었다.
55쪽 대응 보고서:
artifacts/research_reports/pedagogical_render_20260907_r1/FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.md
blob 4f4dcf050e2d71b79a6a7bcc739d3045f23bfe62.
RETURN_TO_MAIN의 55페이지 기록을 확인했다. 첨부 report(1).pdf 자체와 byte identity를 확인한 것은 아니다. 해당 보고서 §§4–10, §12, Appendix E를 중심으로 직접 읽었다. 별도 2026-09-13 theory_synthesis는 36쪽·55 sources이므로 혼동하지 않았다.


R2 원본 MES_GENERALIZED_TENSOR_R2_KO.md를 실제 읽었다. 이전 ZIP 검증 기록은 historical receipt이며 이번 턴의 재실행 증거로 사용하지 않았다.
R7 THEORY blob 166e38093a4eed7a4bd4f59848c8eecbc96b6e3c.
R9 THEORY blob 53f39fa80ec6fb65cb0be6bfa1fc4b3fe35c71e6.
R9 revision2 THEORY_EXTENSION blob 72e5414fd71788f74d8b961ef706089371833c3c.
Repo integration synthesis blob ddfdcb823b8997d9b0e1c9053fbb3bee6e151c69.


호스트의 별도 ‘연구 루프 · 모델별 하네스’ 진입점은 노출되지 않았으나, 저장소에서 physmath-research-gpt6-astra v4.0.0의 START_HERE, PROJECT_INSTRUCTIONS, MODEL_ROUTING, RESEARCH_STATE template, integrated work-run을 찾아 실제 읽고 적용했다. Research Systematically 스킬도 적용했다. 모델 선택 근거는 사용자의 Astra 채택 선언이다. 호스트 모델 identity를 별도로 인증하거나 모델을 변경한 것은 아니다. Repo state는 NOT_RUN template이고 과거 과학 결과가 아니다.


SciSpace 검색과 원 논문 조회, Wolfram 실제 실행을 수행했다. 생산 코드·Git branch·PR·native 검수등록은 변경하지 않았다. VIGILODE는 의존성에서 제외했다.


## 1. 공통 컨벤션


g=(-,+,+,+), U·U=-c², h_ab=g_ab+U_a U_b/c², epsilon_123=+1.
dot=U^a nabla_a는 proper-time derivative.
bar D_a=c h_a{}^b nabla_b는 rate-normalized spatial derivative.
Theta=nabla_a U^a, H=Theta/3, a_a=A_a/c.
Omega_ab=h_a{}^c h_b{}^d nabla_[c U_d], omega^a=(1/2)epsilon^{abc}Omega_bc.
이 omega는 v=omega×x인 rigid rotation에서 양의 회전벡터다.
Theta,sigma,Omega,omega,a의 단위는 s^-1; beta는 무차원.


55쪽 보고서는 unit observer u=U/c, 길이 parameter와 반대 index-order vorticity를 사용한다:
omega_rep_ab=−Omega_ab/c.
따라서 omega_R2^a=−(c/2)epsilon^{abc}omega_rep_bc,
||omega_rep||_F=sqrt(2)|omega_R2|/c.
R7의 rate-unit omega tensor도 R2 Omega와 부호가 반대다.


n은 outward/sourceward 하늘 방향, e=−n은 photon propagation 방향이다.
vartheta_l은 propagation-direction fractional temperature multipole로 고정한다. outward sky의 odd l은 부호를 뒤집는다. 각 방향 흑체/선형 thermodynamic-temperature 근사가 필요한 곳을 분리한다.


## 2. 실제 관측량으로 연결되는 국소 12성분 응답


단일 smooth timelike congruence에 속하는 nearby emitter와 observer, geometric optics, caustic 없는 구간, 비회전 Fermi–Walker 기준축을 가정한다. 거리 쪽에서 photon conservation/distance duality 및 유효 Taylor remainder도 요구한다. 특정 Bianchi class, Einstein matter evolution, metric ansatz는 요구하지 않는다.


국소 leading coefficients는
\[
 {\cal H}(n)=H-a\cdot n+\sigma:nn,\qquad
 d_L(z,n)=c z/{\cal H}(n)+O(z^2),
\]
\[
 \kappa_0(n)=P_n\sigma n+\omega\times n,\qquad P_n=I-nn^T.
\]
Hcal은 d_L/z의 multipole가 아니라 역 slope c z/d_L의 vertex limit이다. Hcal=0이 가능한 방향에서는 z-based inverse expansion을 그대로 사용하지 않고 distance-parameter branch로 남긴다.


첫 식은 Heinesen 2021의 general cosmography; 둘째는 Heinesen–Korzynski 2024 Appendix C Eq.(46)로 확인했다. 해당 Appendix는 arbitrary acceleration을 유지한다. 같은 congruence의 A는 kappa_0에서 상쇄된다. 별도 peculiar-observer acceleration은 aberration drift dipole을 만들 수 있지만 이것을 cosmic congruence의 A와 동일시하지 않는다. kappa_0는 R2의 V(e)와 다른 observable이다.


구면평균 <f>=(4pi)^-1 int f dOmega에 대해
\[
 H=\langle{\cal H}\rangle,\quad
 a=-3\langle n{\cal H}\rangle,\quad
 \sigma={15\over2}\langle n_{\langle a}n_{b\rangle}{\cal H}\rangle,
\]
\[
 \sigma=5\langle n_{\langle a}\kappa_{b\rangle}\rangle,\quad
 \omega={3\over2}\langle n\times\kappa\rangle.
\]
두 shear estimator가 다른 데이터를 통해 같은 tensor를 가리키는 것이 consistency test다.


증명에 필요한 구면 모멘트는 <n_i n_j>=delta_ij/3,
<n_i n_j n_k n_l>=(delta_ij delta_kl+delta_ik delta_jl+delta_il delta_jk)/15이다.
odd integrals와 symmetric/antisymmetric cross contractions는 0이다. 따라서
\[
 \langle{\cal H}^2+|\kappa_0|^2\rangle
 =H^2+|a|^2/3+\|\sigma\|_F^2/3+2|\omega|^2/3.
\]
이 양의 형식은 이상적인 12성분 응답의 injectivity를 보인다. full Frobenius metric의 STF basis를 사용해야 한다. 동일한 수학적 L2 가중치에서 inverse-error norm은 sqrt(3) times observable-error norm으로 제한된다; 실제 likelihood는 실제 covariance를 사용한다.


관측 catalog의 frame angular velocity를 Omega_frame라 하면
kappa_cat=P sigma n+(omega−Omega_frame)×n+P b_pec+source residual.
자유 frame spin은 omega와 정확히 퇴화한다. b_pec는 별도 관측자 acceleration/aberration term의 rate coefficient다. 자유 source dipole/quadrupole도 일치하는 response를 흡수할 수 있다. 구면 모드의 algebraic rank와 실제 nuisance-projected information은 구별한다.


## 3. 유한거리 오차를 숨기지 않는 관측 계약


고정 distance coordinate D에서
z(D,n)=D Hcal(n)/c+r_z(D,n), |partial_D² z|≤M_z
를 가정하면
|c z/D−Hcal|≤c M_z D/2.
이는 Taylor integral remainder에 의한 조건부 bound다. source redshift/peculiar-motion 오차에 |c delta z_source|≤v_*를 추가하면
\[
 b_H(D)\le L_H D+v_*/D,\qquad L_H=cM_z/2.
\]
proper motion 역시 |partial_D kappa|≤L_kappa와 transverse source velocity budget v_perp를 정당화하면
\[
 b_\kappa(D)\le L_\kappa D+v_{\perp,*}/D.
\]
거리·calibration·observer frame correction의 오차는 별도 항 또는 공동 latent variable로 포함한다. 이 식은 균일한 derivative 및 source bounds를 전제로 하며 CMB 한 장에서 그러한 상수를 얻었다는 뜻이 아니다. 어떤 D를 쓰는지 명시해야 한다. affine distance를 실제 d_A/d_L로 대체하면 변환 remainder도 포함한다.


L,v>0이고 동일한 L가 유효구간 전체에서 성립하면 b(D)=LD+v/D의 최솟값은
D*=sqrt(v/L), b(D*)=2sqrt(Lv).
D*가 허용구간 밖이면 그 구간 경계에서 최소화한다. L=0,v=0은 별도 단조 극한이다. 관측 오차를 임의 clipping하는 절차가 아니다. ‘가까울수록 무조건 좋다’는 선택은 v/D 항 때문에 성립하지 않는다.


한 원점의 leading kinematic jet를 서로 다른 redshift shell의 독립 omega(z)로 읽지 않는다. 여러 shell은 remainder와 source response의 검증·분리에 도움을 주지만, 각각의 emitting event kinematics로 해석하려면 추가 transport map이 필요하다.


## 4. 원 보고서/R7 결과의 재사용과 비측지·source 확장


이 절은 거의 등방적인 expanding background의 retained FIRST-ORDER radiation model이다. A,sigma,omega,vartheta_l 및 해당 perturbative jets는 일차이고, discarded products에는 별도 nonlinear remainder가 필요하다. Theta>0,rho>0을 가정한다. zeroth-order collision monopole는 0이다. 비영 background energy injection이 있으면 아래 cancellation 식에 추가항이 생긴다.


보고서의 brightness moments를 physical rate unit로 쓴다:
q_a=(4/3)rho vartheta_a,
pi_ab=(8/15)rho vartheta_ab,
xi_abc=(8/35)rho vartheta_abc.
q는 energy-density coordinate이고 실제 flux는 c q다.


collision/source moments C1_a,C2_ab의 단위는 energy density/time이다.
eta1=3 C1/(4rho), eta2=15 C2/(8rho).
다음 retained equations를 사용한다:
\[
 \dot q_{\langle a\rangle}+{4\over3}\Theta q_a+
 {1\over3}\bar D_a\rho+{4\over3}\rho a_a+
 \bar D^b\pi_{ab}=C1_a,
\]
\[
 \dot\pi_{\langle ab\rangle}+{4\over3}\Theta\pi_{ab}
 +{8\over15}\rho\sigma_{ab}
 +{2\over5}\bar D_{\langle a}q_{b\rangle}
 +\bar D^c\xi_{abc}=C2_{ab}.
\]
background dot rho=−4Theta rho/3 cancels before norms. This gives
\[
 \boxed{a_a=-\dot\vartheta_a-\tfrac14\bar D_a\ln\rho
 -\tfrac25\bar D^b\vartheta_{ab}+\eta1_a,}
\]
\[
 \boxed{\sigma_{ab}=-\dot\vartheta_{\langle ab\rangle}
 -\bar D_{\langle a}\vartheta_{b\rangle}
 -\tfrac37\bar D^c\vartheta_{abc}+\eta2_{ab}.}
\]
이것은 가속도·collision source를 허용한 일차 관계다. quadrupole의 acceleration×dipole 항은 이 근사에서 이차이므로 남지 않는다. eta2=0인 식은 R7 T3 재사용이다.


C_ab=bar D_[a vartheta_b], E_ab=bar D_[a bar D^c vartheta_b]c라 두면,
R2 convention의 scalar commutator는
bar D_[a bar D_b]f=Omega_ab dot f.
또 일차에서
bar D_[a dot vartheta_b]=dot C_ab+(Theta/3)C_ab.
dipole 식의 curl을 취하면
\[
 \boxed{\Omega_{ab}={3\over\Theta}\dot C_{ab}+C_{ab}
 +{6\over5\Theta}E_{ab}
 +{3\over\Theta}\bar D_{[a}(a_{b]}-\eta1_{b]}).}
\]
모든 항의 단위는 s^-1이다. geodesic collisionless limit에서 R7의 opposite-sign omega tensor 식으로 정확히 돌아간다. 이 확장에는 acceleration curl과 collision dipole curl가 필요하다. 이를 0으로 놓는 것은 추가 물리 가정이다.


이 식의 source coefficient와 underlying moment structure는 Maartens–Gebbie–Ellis 1999 Eqs.(92)–(93)와 대조했다. 논문은 c=1을 사용하므로 여기서는 rate convention으로 복원했다. generic eta2에 polarization의 영향을 포함할 수 있지만, 이 문서에서 spin-2 transport나 polarized collision kernel을 새로 유도·검증한 것은 아니다.


## 5. 명시적인 유계 jet/source body


한 공통 jet J에 dot vartheta1,bar D ln rho,bar D vartheta2,
dot vartheta2,bar D vartheta1,bar D vartheta3,
C,dot C,E,curl a,eta1,eta2,curl eta1을 함께 담는다.
이들은 같은 radiation/congruence의 변수이며 cross-correlation과 differential constraints를 유지한다. 서로 독립인 실현 가능한 spacetime들이 자동으로 존재한다는 뜻은 아니다.


Theta를 고정하면 위 식은 (a,sigma,Omega)=L J인 선형 map이다. compact한 joint domain U_J에서
K_rad=L U_J,
h_Krad(w)=h_UJ(L^T w)
가 정확하다. eta1/curl eta1의 동일성을 포함한 U_J를 먼저 만들고 투영한다.
독립 block balls의 Minkowski 합은 방향 정보가 줄어드는 안전한 outer approximation일 수 있지만 그것을 실제 attainable body와 동일시하지 않는다.


예를 들어 U_J={J0+S^(1/2)u:||u||≤rho_J}이면
h_Krad(w)=w·LJ0+rho_J sqrt(w^T L S L^T w).
이 ellipsoid는 deterministic envelope다. covariance와 confidence level이 주어졌다는 뜻은 아니다. 같은 형태를 확률영역으로 쓰려면 해당 sampling law가 필요하다.


쉽게 검토 가능한 scalar outer bounds도 얻는다. 아래 epsilon은 표시한 연산자의 full Frobenius norm을 Theta 또는 Theta²로 나눈 bound다:
\[
 {|a|\over\Theta}\le
 {\|\dot\vartheta_1\|\over\Theta}
 +{\|\bar D\ln\rho\|\over4\Theta}
 +{2\sqrt3\over5}{\|\bar D\vartheta_2\|\over\Theta}
 +{\|\eta1\|\over\Theta},
\]
\[
 {\|\sigma\|\over\Theta}\le
 {\|\dot\vartheta_2\|\over\Theta}
 +{\|\bar D\vartheta_1\|\over\Theta}
 +{3\sqrt3\over7}{\|\bar D\vartheta_3\|\over\Theta}
 +{\|\eta2\|\over\Theta},
\]
\[
 {\|\Omega\|\over\Theta}\le
 3{\|\dot C\|\over\Theta^2}
 +{\|C\|\over\Theta}
 +{6\over5}{\|E\|\over\Theta^2}
 +3{\|\mathrm{curl}_{2}a\|\over\Theta^2}
 +3{\|\mathrm{curl}_{2}\eta1\|\over\Theta^2}.
\]
curl_2 v denotes bar D_[a v_b], not the dual vector without its conversion factor.
For omega vector norm, divide the last bound by sqrt2.
The sqrt3 bounds are safe contraction bounds, not asserted sharp constants.
Source-free geodesic expressions reduce to the already known R7 tightened envelopes.


Varying Theta requires a common joint domain with Theta≥Theta_min>0; map then need not be linear. Compactness plus continuity still bounds the image. This is a CONSTRUCTIVE CONDITIONAL BODY FAMILY. Its astrophysically useful numerical radii are not yet derived from observations. A constant asserted solely for convenience is a sensitivity parameter, not evidence.


## 6. cold-Thomson electron tilt gives a local algebraic response


With cold electrons and first-order relative velocity in the specified U frame, the dipole collision moment has
\[
 \eta1=\Gamma(\beta_e-\vartheta_1),\qquad
 \Gamma=c\,n_e\sigma_T.
\]
This follows from the physical momentum-transfer term in MGE Eq.(92).
If Gamma>0,
\[
 \boxed{\beta_e=\vartheta_1+\Gamma^{-1}
 [a+\dot\vartheta_1+\tfrac14\bar D\ln\rho
 +\tfrac25\mathrm{div}_{\bar D}\vartheta_2].}
\]
It is a local first-order electron tilt relation, not a claim that one observed CMB sky measures every term. The vector vartheta1 is the radiation-flux frame velocity at this order; beta_e is relative to the already declared U. A frame change/observer beta_o has a separate endpoint action.


If Gamma has a positive lower bound and the displayed joint quantities are bounded, beta_e has a finite outer bound. The sensitivity contains Gamma^-1. At Gamma=0 the collision equation has zero beta response: division is undefined and the tilt remains unmeasured by this channel. This exact degeneracy is scientifically useful and must not be regularized away.


A global tilt field additionally requires spatial/time derivatives and congruence consistency. curl eta1 contains gradients of Gamma and of beta_e; the pointwise inverse does not provide those derivatives. No global matter model, arbitrary relativistic-tilt formula or astrophysical opacity estimate is claimed.


## 7. likelihood와 MES normalization을 실제로 연결하는 방법


관측 data는 가능한 harmonic phases/full tensor carrier, CMB boost-sensitive information, calibrated distance–redshift, proper motions를 포함한다. 같은 data에서 만든 derived summaries를 독립 data처럼 곱하지 않는다.


물리 feasible body K_phys와 정규화 reference body B_ref를 구별한다. 원래의 MES 기준을 사전에 고정해 비교하려면 새로운 sharper bound가 생겨도 B_ref를 소급 교체하지 않는다. geodesic theorem bound, generalized conditional bound, declared reference scale의 provenance를 각각 붙인다. theta 자체와 beta의 보편적 MES ceiling은 이번에 생기지 않았다.


R9의 기존 confidence support를 재사용한다. Known justified joint Gaussian law를 whitening하고 unrestricted nuisance image를 제거한 뒤
y=Dk+b'+epsilon, b'∈B', P=DD^+, r=rankD.
\[
 C_\alpha(y)=\{k:\exists b'\in B',\|P(y-Dk-b')\|\le c_r\},
 \quad c_r=\sqrt{\chi^2_{r,1-\alpha}}.
\]
ell kerD=0, t=ell D^+이면
sup ell k=t y+h_B'(-t)+c_r||t||.
이것은 새 통계 정리가 아니라 R9 T2의 재사용이다. 위 물리 jet/source 및 finite-distance residual의 실제 image를 B'에 넣는 것이 이번 연결이다.
D가 full rank이고 B' compact이면 bounded target가 생긴다. rank-deficient일 때 physical constraints로 bounded해질 수도 있으므로 matrix kernel만으로 모든 연구를 배제하지 않는다. (I−P)y의 lack-of-fit 정보는 별도 보존하며 같은 b'를 공유한다.
Data-dependent response, uncertain distances, estimated covariance는 위 pivot을 자동 상속하지 않는다.


likelihood는 기본 data space에서 세운다:
L(d | k,J,eta,frames,calibration,law).
CMB denominator를 만드는 multipoles와 kinematics/source constraints를 한 공동 confidence/posterior state Xi(d)에 포함한다.
\[
 {\cal T}(d)=\{T_{B_ref(\xi)}(k(\xi)-k_ref(\xi)):\xi\in\Xi(d)\}.
\]
Scalar interval도 같은 Xi 위에서 극값을 구한다. MES model을 시험할 때는 observation-based set과 theory body를 따로 만든 뒤 비교한다. 먼저 MES 안으로 추정치를 강제한 뒤 D≥0을 ‘검증’으로 읽지 않는다.


R2 normalization remains
T=y/rho_B(y/||y||), ||T||=gamma_B(y),
D_percent=100(1−gamma_B)=100(1−sqrt(F_amp)).
이것은 기준 경계까지 남은 상대 여유이며 posterior probability나 FLRW의 우주 점유율이 아니다.
b=0,unknown,infinite 또는 공동 denominator가 0을 포함하면 undefined/unbounded branch를 유지한다.


## 8. x,Q,Pi,F,G_F의 이름·의미를 화해시키기


원 repo와 thread R2는 같은 문자에 다른 정의가 존재한다. 다음처럼 분리하며 이전 정의를 지우지 않는다.


- signed legacy x: 해당 Hamiltonian/matter/curvature 정의 및 원래 signed contraction 보존. ||T||²로 치환하지 않음.
- Q_gauge: repo의 premise gauge/margin.
- Q_outer=T⊗T: thread R2의 positive outer-product tensor.
- F_amp=tr Q_outer=||T||²: R2의 squared budget fraction.
- F_support(w): repo의 identified-set directional support-utilization profile; F_amp와 동의어 아님.
- Pi_tail(q)=E[(T⊗T)/F_amp 1(F_amp>q)]: trace=P(F_amp>q), zero tensor at F_amp=0. posterior와 sampling law를 구별.
- G_tensor_ab=T_a⊗(U_b→a T_b)/F_amp,b: norm²=F_amp,a/F_amp,b under specified isometric transport and positive denominator.
- G_path: repo의 registered depth/mask/feature coherence path, tensor growth ratio와 자동 동일하지 않음.


Full signed T and original harmonic carrier remain available. Q_outer loses global sign. Different redshifts require a declared tensor transport/frame map. Redshift labels alone do not create tomography.


동일 관측조건의 비교는 동일 selected data, calibration, frame, nuisance/source allowance, approximation regime와 reference construction을 뜻한다. 3-vector와 5-STF의 같은 budget fraction은 같은 statistical significance를 뜻하지 않는다.


## 9. 실행·독립 검토·실패 상태


CAS1 CONFIRMATORY: exact polynomial sphere averaging; inverse/Gram residuals 28개 모두0; same-congruence acceleration cancellation vector도 {0,0,0}.
CAS2 CONFIRMATORY: Taylor remainder mD²/2, optimum2sqrt(Lv), positive second derivative2v/D³; radius1 nuisance의 displacement1.5는 center cancellation 불가/two-state overlap 가능; shared-data ratio=1/2.
CAS2에서 Wolfram wrapper가 formal symbol L에 undefined-symbol warning을 냈다. 출력은 평가된 exact expressions다. 이 warning을 숨기거나 numerical runtime 실패로 분류하지 않았다.
CAS3 CONFIRMATORY: 18 exact angular directions에서 distance-only rank9, Hcal+proper-motion rank12, free frame-spin quotient rank9. 독립 calibrated beta block을 가정한 algebraic augmentation은 rank15지만 실제 CMB beta-response 검증이 아니다.
CAS4 EXPLORATORY: nongeodesic/collision source dipole,quadrupole,curl normalized-algebra residuals0.
CAS4B EXPLORATORY: Thomson tilt inverse residual0; Gamma=0에서 beta response0.
이들은 lightweight CAS이고 ODE/PDE/Boltzmann evolution을 실행하지 않았다.


Independent reviewer는 candidate 생성에 참여하지 않았고 fixed report/R7/R9와 primary optics equations를 별도 읽었다. inverse factors, signs, norms, joint-inference caveats를 검토했다.
기본 verdict PROMOTE_CONDITIONAL_THEORY; new acceleration/source branch의 evidence stage는 exploratory로 유지.
리뷰는 source/equation contract 범위이며 전체 문서 byte hash·해시 결속·실관측 pipeline을 인증한 것이 아니다.


Source retrieval anomalies:
- initially guessed INTEGRATED_RESEARCH_CONTRACT.md path 404; actual integrated prompt path found/read. Scientific failure 아님.
- some arXiv HTML URLs unavailable; PDF/v1 HTML retrieval succeeded. Paper inaccessible라고 단정하지 않음.
- Wolfram tool probe returned 2+2=4. It could not see the provided scratch PDF path (FileExistsQ=False); repo counterpart read instead. Python/C++ availability는 이 작업에서 판단하지 않음.
- Library/workspace attachment byte identity, previous ZIP restore verification는 미수행.
- Local write/terminal API unavailable in this tool exposure; structured document/export path is used for deliverable. No scientific result is inferred from filesystem accessibility.


## 10. 닫힌 DAG와 다음 bounded work unit


R3-00 source intake(R2,55p,R7,R9,harness): COMPLETE.
R3-01 actual-observable optical response and conventions: COMPLETE conditional.
R3-02 finite-distance/source residual body family: COMPLETE conditional; actual radii UNRESOLVED.
R3-03 accelerated radiation/source extension: EXPLORATORY DERIVED/CAS-CHECKED.
R3-04 legacy/tensor statistic semantic bridge: COMPLETE definition-level.
R3-05 CAS1–3 and independent equation decision: COMPLETE scoped.
R3-06 actual data likelihood: NOT_RUN.
R3-07 full nonlinear theorem or production migration: OUT_OF_SCOPE.


Selected next task:
Choose one fixed nearby-source congruence, one matched distance/proper-motion sample, and one explicit reference-frame calibration contract. Use current sources to form physically motivated bounds/covariance for unresolved peculiar motions and finite-distance jets, then show for at least one shear or acceleration target that the robust observational interval is meaningfully narrower than the preregistered MES/reference radius. If no useful interval follows, identify which measured/conditional budget dominates; do not repeat the abstract rank audit.
Keep beta_e opacity-dependent local channel and beta_o endpoint boost as separate routes. A common state must connect them before global tilt attribution.
Do not extrapolate low-z series to last scattering.
No additional broad solver construction is required for this next test.


## Primary/source links


55-page report counterpart: https://github.com/cosmosapjw-quantum/htt_base/blob/85e261f49c9df9389946eef74d80c1ccd0509816/artifacts/research_reports/pedagogical_render_20260907_r1/FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.md
R7 prior theory: https://github.com/cosmosapjw-quantum/htt_base/blob/85e261f49c9df9389946eef74d80c1ccd0509816/docs/research_program/tensor_joint_r7/THEORY.md
R9 prior theory: https://github.com/cosmosapjw-quantum/htt_base/blob/85e261f49c9df9389946eef74d80c1ccd0509816/docs/research_program/tensor_joint_r9/THEORY.md
Astra research core: https://github.com/cosmosapjw-quantum/htt_base/blob/85e261f49c9df9389946eef74d80c1ccd0509816/harness/physmath-research-gpt6-astra/PROJECT_INSTRUCTIONS.md
MES 1995: https://arxiv.org/pdf/astro-ph/9501016
Maartens-Gebbie-Ellis 1999 Eqs92-93: https://arxiv.org/pdf/astro-ph/9808163
Heinesen 2021 general Hubble law: https://arxiv.org/pdf/2010.06534
Heinesen-Korzynski 2024 Appendix C Eq46/E: https://arxiv.org/html/2406.06167v1


## Frozen preregistration (before CAS1-3; CAS4/4B are later exploratory additions)
{
  "id": "MES_R3_OBSERVABLE_JET_AND_JOINT_BODY_20260927",
  "question": "Can an actual finite nearby-source distance-redshift and position-drift experiment yield morphology-preserving conditional bounds on H,A,sigma,omega, with beta constrained through a separately declared CMB boost law, without spacetime evolution?",
  "scope": "General metric/congruence; local controlled distance expansion; no Bianchi class, no real-data inference; source report and current repo as supporting material. VIGILODE excluded.",
  "hypotheses": [
    {
      "id": "H1",
      "prediction": "H(n)=H-a.n+S:nn, mu(n)=P S n+omega cross n provide full rank12 (H1,a3,S5,omega3) in ideal calibrated frame. mu leading A cancels for same congruence.",
      "falsifier": "Rank<12 or failure of independent local geodesic/direction derivation."
    },
    {
      "id": "H2",
      "prediction": "Explicit derivative and bounded endpoint-motion budgets make finite-distance residual compact; radius scales L D+v/D. Free frame spin or free source modes restore the matching nullspace.",
      "falsifier": "Compact residual but unbounded preimage despite full column rank; or prescribed null directions measurably distinguishable."
    },
    {
      "id": "H3",
      "prediction": "One common latent confidence set must feed T,Q,F,Pi,G and same-data MES body. Support for bounded nuisance yields robust region; cancellation vs two-state overlap differs factor2 in norm.",
      "falsifier": "Counterexample to set projection/support/overlap or nonzero-reference recentering."
    }
  ],
  "tests": [
    {
      "id": "CAS1",
      "kind": "confirmatory",
      "target": "Exact rational sphere moment inverse and Gram matrix of observed H,mu including A/rotation signs"
    },
    {
      "id": "CAS2",
      "kind": "confirmatory",
      "target": "Remainder integral and LD+v/D optimum; ellipsoidal nuisance cancellation vs two-state overlap witness"
    },
    {
      "id": "CAS3",
      "kind": "confirmatory",
      "target": "Finite design rank and frame-spin/source nuisance rank loss; same-data ratio dependence example"
    }
  ],
  "stop": "Close all three bounded tests and one independent decision pass; no recursive audit and no cosmological solver. Physical budget magnitudes and real-data law remain unresolved.",
  "prereg_state": "Frozen before CAS experiments; source reconnaissance and candidate identities exploratory."
}


## Reproducible Wolfram code and returned evidence


### CAS1
```wl
ClearAll["Global\`*"];
v={x,y,z}; a={a1,a2,a3}; w={w1,w2,w3};
ss={{s1,s3,s4},{s3,s2,s5},{s4,s5,-s1-s2}};
pr=IdentityMatrix[3]-Outer[Times,v,v];
hh=h-a.v+v.ss.v; mu=pr.ss.v+Cross[w,v];
mom[p_]:=Total[(#[[2]] If[AnyTrue[#[[1]],OddQ],0,Times@@(If[#==0,1,Factorial2[#-1]]& /@ #[[1]])/Factorial2[Total[#[[1]]]+1]])& /@ CoefficientRules[Expand[p],v]];
stf[m_]:=(m+Transpose[m])/2-IdentityMatrix[3] Tr[m]/3;
inv={mom[hh]-h,Sequence@@(3(mom /@(-v hh))-a),Sequence@@Flatten[15/2 Map[mom,pr hh-2 IdentityMatrix[3] hh/3,{2}]+ss]};
(* Separate direct STF inverse, avoiding projector sign ambiguity *)
is=15/2 Map[mom,(Outer[Times,v,v]-IdentityMatrix[3]/3)hh,{2}];
im=5 Map[mom,stf[Outer[Times,v,mu]],{2}];
iw=3/2 (mom /@ Cross[v,mu]);
gram=FullSimplify[{mom[hh^2]-(h^2+a.a/3+2 Tr[ss.ss]/15),mom[mu.mu]-(Tr[ss.ss]/5+2 w.w/3),mom[hh^2+mu.mu]-(h^2+a.a/3+Tr[ss.ss]/3+2w.w/3)}];
res=FullSimplify[Join[{mom[hh]-h},-3(mom /@ (v hh))-a,Flatten[is-ss],Flatten[im-ss],iw-w,gram]];
<|"TestID"->"CAS1","ResidualCount"->Length[res],"AllZero"->(Union[res]=={0}),"Residuals"->res,"LeadingDriftAccelerationCancellation"->FullSimplify[pr.a-pr.(a-ss.v-Cross[w,v])-mu]|>
```
Raw tool result:
{
  "content": [
    {
      "type": "text",
      "text": "Out[1]= <|\"TestID\" -> \"CAS1\", \"ResidualCount\" -> 28, \"AllZero\" -> True, \"Residuals\" -> {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0}, \"LeadingDriftAccelerationCancellation\" -> {0, 0, 0}|>"
    }
  ],
  "isError": false
}


### CAS2
```wl
ClearAll["Global\`*"];
bud=L dd+vv/dd; dd0=Sqrt[vv/L];
rem=Integrate[(dd-t) m,{t,0,dd}];
costs={1,9/4,4,25/4};
checks=<|"RemainderIntegral"->rem,"OptimumDerivative"->FullSimplify[D[bud,dd]/.dd->dd0,Assumptions->L>0&&vv>0],"OptimumValue"->FullSimplify[bud/.dd->dd0,Assumptions->L>0&&vv>0],"ConvexSecondDerivative"->D[bud,{dd,2}],"OverlapWitness"->{(3/2)^2<=1,(3/2)^2<=4},"SameDataRatio"->FullSimplify[Exp[zz]/(2Exp[zz])]|>;
<|"TestID"->"CAS2","Checks"->checks|>
```
Raw tool result:
{
  "content": [
    {
      "type": "text",
      "text": "Symbol::undefined2: Warning: Global symbols \"L, L, L, L\" are undefined.\nGeneral::messages: Messages were generated which may indicate errors.\n\nOut[1]= <|\"TestID\" -> \"CAS2\", \"Checks\" -> <|\"RemainderIntegral\" -> (dd^2*m)/2, \"OptimumDerivative\" -> 0, \"OptimumValue\" -> 2*Sqrt[L*vv], \"ConvexSecondDerivative\" -> (2*vv)/dd^3, \"OverlapWitness\" -> {False, True}, \"SameDataRatio\" -> 1/2|>|>"
    }
  ],
  "isError": false
}


### CAS3
```wl
ClearAll["Global\`*"];
vv={xx,yy,zz}; av={a1,a2,a3}; wv={w1,w2,w3}; sm={{s1,s3,s4},{s3,s2,s5},{s4,s5,-s1-s2}}; pp=IdentityMatrix[3]-Outer[Times,vv,vv];
hh=hh0-av.vv+vv.sm.vv; muv=pp.sm.vv+Cross[wv,vv];
pars={hh0,a1,a2,a3,s1,s2,s3,s4,s5,w1,w2,w3};
dirs=Join[IdentityMatrix[3],-IdentityMatrix[3],({#[[1]],#[[2]],0}/Sqrt[2]&/@Tuples[{-1,1},2]),({#[[1]],0,#[[2]]}/Sqrt[2]&/@Tuples[{-1,1},2]),({0,#[[1]],#[[2]]}/Sqrt[2]&/@Tuples[{-1,1},2])];
pol=Join[{hh},muv]; des=Join@@Table[Table[Coefficient[pol[[j]],p]/.Thread[vv->n],{j,4},{p,pars}],{n,dirs}];
r1=MatrixRank[des]; nn=des[[All,10;;12]];
quotient=MatrixRank[Join[des,nn,2]]-MatrixRank[nn];
low=Table[Coefficient[hh,p]/.Thread[vv->n],{n,dirs},{p,pars}];
spinNull=Simplify[des[[All,10;;12]]-nn];
<|"TestID"->"CAS3","Directions"->Length[dirs],"FullRank"->r1,"DistanceOnlyRank"->MatrixRank[low],"FreeFrameSpinQuotientRank"->quotient,"CalibratedIndependentBoostAddedRank"->r1+MatrixRank[IdentityMatrix[3]],"FrameSpinAndUnrestrictedBoostNuisanceRank"->quotient,"SpinDegeneracyResidual"->Union[Flatten[spinNull]]|>
```
Raw tool result:
{
  "content": [
    {
      "type": "text",
      "text": "Out[1]= <|\"TestID\" -> \"CAS3\", \"Directions\" -> 18, \"FullRank\" -> 12, \"DistanceOnlyRank\" -> 9, \"FreeFrameSpinQuotientRank\" -> 9, \"CalibratedIndependentBoostAddedRank\" -> 15, \"FrameSpinAndUnrestrictedBoostNuisanceRank\" -> 9, \"SpinDegeneracyResidual\" -> {0}|>"
    }
  ],
  "isError": false
}


### CAS4
```wl
ClearAll["Global\`*"];
rhoDot=-(4/3)th rr;
dip=(4/3)(rr dt1+rhoDot t1)+(4/3)th ((4/3)rr t1)+rr gg/3+(8/15)rr dv2+(4/3)rr acc-(4/3)rr eta1;
quad=(8/15)(rr dt2+rhoDot t2)+(4/3)th ((8/15)rr t2)+(8/15)rr sig+(2/5)(4/3)rr dv1+(8/35)rr dv3-(8/15)rr eta2;
aa=-dt1-gg/4-(2/5)dv2+eta1;
ss=-dt2-dv1-(3/7)dv3+eta2;
(* R2 positive-curl convention; D_[a D_b]ln rho=Omega_ab dot ln rho *)
curlEq=dc+(th/3)cc-(th/3)om+(2/5)ee+ca-ce;
ww=3 dc/th+cc+6 ee/(5 th)+3(ca-ce)/th;
<|"TestID"->"CAS4_EXPLORATORY_ACCELERATED_SOURCE_EXTENSION","DipoleResidual"->Together[dip/.acc->aa],"QuadrupoleResidual"->Together[quad/.sig->ss],"CurlResidual"->Together[curlEq/.om->ww],"GeodesicCollisionlessLimit"->(ww/.{ca->0,ce->0}),"RateDimensionOrders"->{"acc,sig,eta1,eta2,dt1,dt2,dv1,dv2,dv3,gg,th: inverse-time","dc,ee,ca,ce: inverse-time-squared"}|>
```
Raw tool result:
{
  "content": [
    {
      "type": "text",
      "text": "Out[1]= <|\"TestID\" -> \"CAS4_EXPLORATORY_ACCELERATED_SOURCE_EXTENSION\", \"DipoleResidual\" -> 0, \"QuadrupoleResidual\" -> 0, \"CurlResidual\" -> 0, \"GeodesicCollisionlessLimit\" -> cc + (3*dc)/th + (6*ee)/(5*th), \"RateDimensionOrders\" -> {\"acc,sig,eta1,eta2,dt1,dt2,dv1,dv2,dv3,gg,th: inverse-time\", \"dc,ee,ca,ce: inverse-time-squared\"}|>"
    }
  ],
  "isError": false
}


### CAS4B
```wl
ClearAll["Global\`*"];
accR=-dt1-gg/4-2dv2/5+gam (be-t1);
beR=t1+(acc+dt1+gg/4+2dv2/5)/gam;
<|"TestID"->"CAS4B_EXPLORATORY_THOMSON_TILT","Residual"->Together[accR/.be->beR]-acc,"DegenerateAtZeroOpacity"->Simplify[D[accR,be]/.gam->0]|>
```
Raw tool result:
{
  "content": [
    {
      "type": "text",
      "text": "Out[1]= <|\"TestID\" -> \"CAS4B_EXPLORATORY_THOMSON_TILT\", \"Residual\" -> 0, \"DegenerateAtZeroOpacity\" -> 0|>"
    }
  ],
  "isError": false
}


## 보충 독립 검토와 spectral closure 명시


보충 판정: EXPLORATORY_CONDITIONAL_PROMOTE.
Reviewer가 MGE 1999 Eqs.(91)–(93) 원문과 화면을 직접 대조하고 generic-source 정규화 및 cold-Thomson beta_e 식을 독립 대수검토했다. CAS4–4B를 reviewer가 다시 실행한 것은 아니다.


중요한 의미 보완:
일반 collision/source를 허용하는 §4–6에서 vartheta_l은 q=(4/3)rho vartheta1, pi=(8/15)rho vartheta2, xi=(8/35)rho vartheta3로 정의한 brightness-normalized multipole로 해석할 수 있다. 이를 실제 thermodynamic-temperature multipole로 동일시하려면 초기 Planckian perturbation 및 spectral-distortion 통제가 필요하다. 배경 C0=0만으로 temperature closure가 보장되지 않는다.
Cold elastic Thomson branch는 작은 전자 bulk velocity, thermal Compton/recoil 보정 생략, 적절한 초기 스펙트럼을 전제로 한다. eta2의 9/10 damping coefficient를 polarized equation에 그대로 적용하지 않았고, generic source로 유지했다.
curl eta1=bar D_[a{Gamma(beta_e−vartheta1)_{b]}}에서는 Gamma의 gradient를 임의로 생략하지 않는다.
Gamma=0, numerator=0인 경우에도 역산은 undefined이고 tilt는 그 channel에서 미식별이다.


최종 분류:
- 실제 광학 leading response, finite residual contract, R7/R9 재사용과 joint image: PROMOTE_CONDITIONAL_THEORY.
- 비측지·source·Thomson tilt 연결: EXPLORATORY_CONDITIONAL_PROMOTE.
- empirical bound와 full nonlinear MES, 구현/실자료 pipeline: NOT_RUN / UNRESOLVED.
이것은 새 독립 실관측 결과 또는 full package hash audit의 인증이 아니다.