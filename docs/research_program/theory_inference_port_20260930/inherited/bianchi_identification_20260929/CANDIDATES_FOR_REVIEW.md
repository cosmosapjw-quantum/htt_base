# 독립 판정용 명제 초안

현재 실행의 목적은 solver 없이 가능한 조건부 Bianchi 기하 식별 범위를 재정의하는 것이다. 실제 관측 판정이나 이전 HOLD 해제는 요청하지 않는다. signature (-,+,+,+), 물리적 4-속도 norm=-c². 리뷰 전 상태는 모두 PROPOSED.

## BIC-01: 동일 시공간의 복수 군작용 — 정확한 반례

M=I×R³, g=-c²dt²+A(t)²(dx²+dy²)+B(t)²dz², A,B>0. 세 translation은 Bianchi I. 또한 K1=∂x,K2=∂y,K3=∂z+q(x∂y-y∂x), q≠0는 Killing, det 공간성분=1, [K3,K1]=-qK2,[K3,K2]=qK1,[K1,K2]=0이므로 VII0 simply-transitive action. sigma_ab sigma^ab=2/3(H_A-H_B)²로 shear 비영인 경우도 포함. 동일 g, 동일 물질/관측자/경계조건으로 계산된 어떠한 데이터법칙도 선택한 두 G3를 구별할 수 없다. 이는 모든 generic I와 VII0가 동등하다는 주장이 아니다. 지표가 geometry면 허용 action의 집합을 답해야 함. Wolfram: evidence/wolfram_lrs.json.

## BIC-02: 공간 곡률 부호의 단방향 분류

국소 simply-transitive G3가 작용하는 spacelike homogeneous orbit의 Riemannian metric h를 가정. orthonormal invariant frame에서 C^i_jk=eps_jkl n^li+a_j delta^i_k-a_k delta^i_j, n symmetric, Jacobi n a=0. n diagonal이면 R3=-6|a|²-1/2 sum n_i²+sum_{i<j}n_i n_j. Class B: a=(a,0,0),n1=0 -> R3=-6a²-(n2-n3)²/2<0. Class A: I=0; rank1 II<0; rank2 opposite signs VI0<0; rank2 same signs VII0≤0. Mixed sign rank3 VIII: choose n1,n2>0,n3<0 -> R3=-(n1-n2)²/2-n3²/2+n3(n1+n2)<0. Thus R3>0 implies IX; converse false e.g n=(1,1,5) gives -5/2. R3=0 alone does not fix I, R3<0 does not exclude IX. Not valid as arbitrary rest-space curvature theorem if fluid omega≠0, or for Kantowski-Sachs outside assumed simplytransitive class. Wolfram Koszul computation: evidence/wolfram_curvature.json.

Optional GR observation bridge: with physical hypersurface normal N, theta_N and Sigma_N²=sigma_Nab sigma_N^ab, epsilon_N=T_ab N^a N^b/c², Einstein G+Lambda g=(8piG/c4)T gives R3=16piG epsilon_N/c4+2Lambda-2theta_N²/(3c²)+Sigma_N²/c². A uniform positive lower bound over a calibrated joint allowed set licenses conditional nonIX exclusion. Quantities of tilted source u cannot silently replace N.

## BIC-03: generic homogeneous spatial metric3jet sufficiency

Assume h is locally homogeneous on a neighborhood and its Ricci has three distinct eigenvalues lambda_i at p. Ricci eigenframe is invariant under connected local isometries (only discrete sign/permutation ambiguities). Eigenvalues constant spatially. Define Gamma^j_ki=<D_{e_k} e_i,e_j>. Then (D_k Ric)_ij=(lambda_i-lambda_j)Gamma^j_ki for i≠j; Gamma^i_ki=0. Thus Ric and D Ric determine all Gamma, hence C^j_ki=Gamma^j_ki-Gamma^j_ik. These invariant-frame brackets give the reciprocal group algebra, opposite but isomorphic to Killing algebra, so Bianchi type is determined up to Lie algebra isomorphism. Inputs are h3jet, not merely kinematical tensor and not observed automatically. The theorem assumes local homogeneity, does not certify it from an arbitrary single-point finite jet, does not give topology/global action. To infer spacetime action from slice action need same G3 to preserve time-dependent spatial geometry/extrinsic data or assume spacetime Bianchi already. Repeated eigenvalue branch uses other invariants/higher derivatives and can be truly nonunique. Wolfram nontrivial sample n=(1,2,4): Ric=diag(-3/2,-5/2,15/2), recovers connection+brackets exactly (evidence/wolfram_jet.json). General argument is analytic proof, sample is check only. Literature Ferrando–Sáez 2020 arXiv:2004.01877 §4 and §5; not novelty claim.

### BIC-03b: invariant tensor extension

위 증명은 Ric 대신 G3에 invariant인 임의의 spatial symmetric tensor T에 그대로 적용된다. h와 T가 같은 G3에 대해 homogeneous이고 T의 eigenvalues가 distinct이면 D_kT_ij=(lambda_i-lambda_j)Gamma^j_ki. 따라서 (h,T,D T)에서 symmetry-adapted algebra를 복원할 수 있다. T로 homogeneous slice normal N의 shear sigma_N를 택할 수 있다. 이 경우 shear의 값만으로는 부족하고 모든 spatial covariant derivatives가 필요하다. Tilted source u의 shear나 observed sky STF tensor를 그 자리에 넣으려면 별도 동일성/불변성 증명이 필요하다. simple T와 D T=0이면 Gamma=0이므로 C=0: Bianchi I의 조건부 충분조건. LRS I/VII0 반례는 Ric도 normal shear도 repeated eigenvalues라 이 충분조건을 위반하지 않는다. 이 확장도 review 요청. 일반정리 증명, 수치적/관측적 충분성 주장은 아님.

## BIC-04: leading drift tensor inversion (conditional)

Geodesic emitter/observer congruence, smoothly varying near-observer regime, all-sky limit, calibrated Fermi-Walker frame. Use omega matrix convention where leading drift kappa_i(e)=P_ij(e)(sigma_jk+omega_jk)e_k, P=I-eeT. Angular average M_ij=<kappa_i e_j>=sigma_ij/5+omega_ij/3 by second/fourth sphere moments. Hence sigma=5 sym M, omega=3 anti M; trace zero. Physical sigma,omega,kappa are per proper time, units s^-1; restore c consistently if derivative is length-time instead. This identifies kinematics under this ideal observation model, not G3. At finite depth fit extrapolated leading coefficient with remainder; masks require actual sampling operator and noise law. Wolfram: evidence/wolfram_sky.json. Literature Heinesen–Korzynski 2024 arXiv:2406.06167 equations9–10 and Appendix E. Full accelerated and higher-order terms not promoted (paper §VII discusses sign errata).

## BIC-05: reference spin obstruction survives tensorization

If physical omega and unconstrained frame spin have the same three toroidal dipole response columns, y=R_sigma s+R_omega w+N b+noise and col(R_omega)⊂col(N). If noise full law fixed and domain admits compensation then (w,b)→(w+h,b-c) leaves full law identical for R_omega h=Nc. Any deterministic statistic preserves this indistinguishability. Profiling/projecting spin removes absolute constant omega mode. Redshift binning does not restore a common null direction; only independently anchored frame or physically distinct redshift responses with their own proof can help. Same mean alone insufficient if noise covariance depends on w.

## BIC-06: calibrated partial type identification

For action label t define complete physical domain Theta_t and observable mean prediction M_t. Need response/nuisance/mask/observer/finite-redshift remainder included. Let Mout_t⊃M_t be a sound outer enclosure, and C_alpha(Y) a simultaneous confidence region for true observable mean with coverage≥1-alpha uniformly over the whole union model. Define S_alpha(Y)={t:C_alpha(Y)∩Mout_t≠empty}. For every admissible true t, P[t∈S_alpha]≥1-alpha since true mean lies in both sets on the coverage event. If same geometry admits several actions, same event includes all such labels. Empty intersection excludes under assumptions; nonempty intersection is only non-exclusion, not physical realization or posterior probability. Sets may be nonlinear/disconnected; no full-column-rank necessity. No Bonferroni across types needed if using one simultaneous region with this proved coverage; separately tested summaries may need calibration.

MES integration: carry current tensor observable and matched bodies/joint law into this set projection. Fixed invertible normalization preserves identification, lossy summary can destroy it, neither creates missing information. gamma quotient min is over algebraic fibre unless physical-domain intersection explicitly imposed. Symbol Q/F/Pi/G_F meanings stay versioned, never renamed as class probability. Existing I2 DEFENDED_CONDITIONAL and I3 HOLD_INPUT_INCOMPLETE remain unchanged.

## BIC-07 and BIC-08: ceilings only, no promotion requested

BIC-07 observable-to-full-spatial-curvature-jet reconstruction for actual held data: HOLD_MISSING_RESPONSE. Position/redshift drift literature gives selected curvature combinations, not all inputs of BIC-03. CMB morphologies and C_l alone do not supply connection coefficients; a complete physically warranted analytic radiative forward law is still required for type likelihood. Analytic exact models or local optical jets can be used without Boltzmann, but missing early-time scattering/initial radiation cannot be replaced by a gauge.

BIC-08 real-data universe classification: NOT_RUN. No current data fit, no cosmological bound, no claim of newly discovered mathematical theorem, no theorem DB/code DB downloads. Independent review approves only specified next research/formalization stage.
