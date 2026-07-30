HTT vector/tensor MES 및 증명 프로그램 업그레이드 청사진

작성 기준: htt_base commite7c20643c0dd323481f0887aff8e437a1bf7950a (2026-07-30)

이 문서는 구현 전 설계·증명 계약이다. 관측 검출, FLRW 근접성 증명,Bianchi family 식별 또는 PR-151 자료의 사용을 허가하지 않는다.

0. 감사 결론

첨부문서는 PR-256까지의 상태를 기술한다. 현재 HEAD에는PR-257(저차수 다중극 형태론과 12개 orbit polynomial)과PR-258(open-set response classes)가 이미 병합되어 있다.

현행 DepartureState는((\sigma_{\langle ab\rangle},\omega_a,\beta_a,\Delta\Omega_k))만포함한다. (A_a)가 없고, (\beta_a)는 PR-256의(\beta_{\rm RO},\beta_{\rm RM},\beta_{\rm MO})와 결합되지 않았다.

PR-257 catalogue는(V_2^\sigma\oplus V_{1,\mathrm{axial}}^\omega\oplus V_{1,\mathrm{polar}}^\beta) 위의 degree-bounded diagnostic이다.generic orbit separation과 completeness는 코드에서 모두UNPROVEN이다.

기존 theorem registry에는 65개 레코드가 있지만, typed successorregistry에서 완전한 CHECKED signature를 가진 정리는 12개뿐이다.53개는 MIGRATION_PENDING이다. 따라서 “65개 증명 완료”라고보고하면 현재 저장소 자체의 honesty gate를 위반한다.

scalar (x_C,Q,\Pi,F,G_F)는 삭제 대상이 아니다. 정확한 역사적재현과 one-dimensional pushforward로 보존하되, 능동 추론의 SSOT는component/orbit/response-native 객체로 이동해야 한다.

1. 고정할 물리 convention

1.1 시공간 및 1+3 분해

metric signature: ((-+++))

(u^a u_a=-c^2)

(h_{ab}=g_{ab}+u_a u_b/c^2)

(A_a=u^b\nabla_bu_a)

convention:

[\nabla_bu_a=-\frac{1}{c^2}A_a u_b\frac{1}{3}\Theta h_{ab}\sigma_{ab}\omega_{ab}.]

(\sigma_{ab}=\sigma_{\langle ab\rangle})는 spatial, symmetric,trace-free이고, (\omega_a=\frac12\varepsilon_{abc}\omega^{bc})는axial vector이다. 코드가 (c=1)을 쓰더라도 직렬화된 metadata에는units_convention과 velocity_normalization을 남긴다.

1.2 무차원 변수

[\widehat\sigma_{ab}=\frac{\sigma_{ab}}{\Theta},\qquad\widehat\omega_a=\frac{\omega_a}{\Theta},\qquad\widehat A_a=\frac{A_a}{c\Theta},\qquad\beta_a=\frac{v_a}{c}.]

기존 sector normalization은 자동 동일시하지 않고 명시적 adapter로만변환한다. 예를 들어 (H=\Theta/3)이고(\omega_{ab}\omega^{ab}=2\omega_a\omega^a)인 convention에서는

[\Sigma^2_{\rm std}=\frac{\sigma_{ab}\sigma^{ab}}{6H^2}=\frac32\widehat\sigma_{ab}\widehat\sigma^{ab},\qquadW^2_{\rm std}=\frac{\omega_{ab}\omega^{ab}}{6H^2}=3\widehat\omega_a\widehat\omega^a.]

이 계수는 vorticity dual convention이 바뀌면 함께 바뀌므로 contract에고정한다.

1.3 세 층의 상태

CongruenceKinematics
  sigma_stf5, omega_axial3, acceleration_polar3
  frame, congruence, epoch_window, averaging_scale
  basis, units, parity, perturbative_order

VelocityFrameBundle
  beta_RO, beta_RM, beta_MO
  beta_RO = beta_RM + beta_MO + O(beta^2)
  closure status and response-provider provenance

JointAnisotropyState
  kinematics_ref
  velocity_bundle_ref
  curvature_ref
  optional geometry_ref = (E_ab, H_ab, 3R_<ab>, pi_ab, ...)

(\beta_{\rm MO})는 exact FLRW에서도 observer boost로 존재할 수 있으므로geometric FLRW distance의 성분이 아니다. (A_a)도 congruence를 바꾸면exact FLRW에서 생길 수 있다. 따라서 모든 “departure” 문장은 frame과congruence를 양화해야 한다.

2. MES를 scalar bound에서 anchor body로 올리기

2.1 핵심 정의

관측 요약 (y), nuisance/전제 (\nu), 상태공간 (V)에 대해 MES가허용하는 집합을

[\mathcal A_{\rm MES}(y,\nu)\subset V]

로 둔다. scalar amplitude 상계는 ball, full-covariance 상계는supported quotient의 ellipsoid, 여러 sector의 독립 상계는 productbody이다. 검증된 acceleration anchor가 없으면 (A)-sector를 0으로채우지 않고 NO_MES_ANCHOR로 남긴다.

(\mathcal A)가 원점을 포함하는 closed convex absorbing set이면Minkowski gauge를

[r_{\mathcal A}(k)=p_{\mathcal A}(k)=\inf{\lambda>0\in\lambda\mathcal A}]

로 정의한다.

(r=0): 고정된 congruence의 FLRW kinematic zero section

(r=1): 등록된 MES anchor boundary

(r>1): 등록된 선형 전제/anchor와의 incompatibility

(r\le1): FLRW의 converse 또는 “선형적임”을 증명하지 않음

balanced, bounded, nonempty-interior 조건까지 있으면 (p_{\mathcal A})는norm이다. 이 조건이 없으면 “distance”라는 명칭을 쓰지 않는다.

2.2 support-function duality

(\mathcal A)가 closed, convex, balanced이면

[p_{\mathcal A}(k)=\sup_{\ell\ne0}\frac{|\ell(k)|}{h_{\mathcal A}(\ell)},\qquadh_{\mathcal A}(\ell)=\sup_{a\in\mathcal A}|\ell(a)|.]

따라서 기존 scalar (x)는 잘못된 객체가 아니라 한 방향(\ell)에서 본 gauge의 하한이다. 모든 방향의 scalar ratio를 모으면vector/tensor anchor gauge를 정확히 복원한다. 유한 catalogue는preregistered lower approximation을 준다.

2.3 amplitude, morphology, nonlinearity의 분리

[r=p_{\mathcal A}(k),\qquads=\frac{k}{r}\quad(k\ne0),\qquad[s]_G\in V/G.]

(r): MES saturation/stress

([s]_G): rotation/parity를 quotient한 morphology/type

(d_\perp): 관측공간에서 등록된 linear tangent 밖의 residual

[d_\perp^2=\left|(I-P_{T_{\rm lin}})C^{+1/2}(y-\mu_0)\right|^2,]

단, covariance-null residual은 별도로 보존한다. “비선형성”은(r>1)과 동의어가 아니며, forward response가 있을 때의(d_\perp) 또는 held-out nonlinear candidate competition으로평가한다.

이 프로그램의 canonical diagnostic은 scalar 하나가 아니라

[\boxed{(r_{\mathcal A},\ [s]G,\ d\perp)}]

이다.

3. (x,Q,\Pi,F,G_F)의 vector/tensor lift

3.1 typed functional catalogue

각 functional은 최소한 다음 metadata를 가진다.

functional_id, source_state_schema, input_representation
output_rank, homogeneity_degree, O3_parity, quotient_group
frame, congruence, epoch_window, averaging_scale
normalization_id, anchor_id, response_id

(\phi\to\mathbb R)가 degree (d)의 homogeneous polynomial이면

[U_\phi(\mathcal A)=\sup_{a\in\mathcal A}|\phi(a)|,\qquadx_\phi(k)=\operatorname{sgn}\phi(k)\left(\frac{|\phi(k)|}{U_\phi(\mathcal A)}\right)^{1/d}.]

이 root-normalization은 degree가 다른 invariant들도 임계값 1로비교하게 한다. (U_\phi=0)은 0으로 나누지 않고STRUCTURAL_NULL 또는 ANCHOR_DEGENERATE를 반환한다.

homogeneity로부터

[|x_\phi(k)|\le p_{\mathcal A}(k)]

이므로 각 functional은 global anchor stress의 인증된 하한이다.

3.2 (x): scalar가 아니라 functional profile

[\mathbf x_\Phi(k)=(x_{\phi_1},\ldots,x_{\phi_p}).]

예:

[x_{\operatorname{tr}\sigma^2},\quadx_{\operatorname{tr}\sigma^3},\quadx_{\beta\sigma\beta},\quadx_{\omega\sigma\omega},\quadx_{\beta\cdot\omega}.]

legacy (x_C)는 BC1_LEGACY_PROJECTION으로 이 profile의 독립적인historical pushforward에 남는다.

3.3 (Q): preregistered acceptance-body gauge

functional space의 acceptance body (\mathcal B\subset\mathbb R^p)를등록하고

[Q_{\mathcal B}(\mathbf x)=p_{\mathcal B}(\mathbf x)]

로 정의한다.

unit cube: (Q=|\mathbf x|_\infty)

covariance ellipsoid:(Q=(\mathbf x^\top W\mathbf x)^{1/2})

one-dimensional body: 기존 scalar (Q)

(\mathbf x), covariance, active set을 항상 함께 보존한다. scalar(Q)는 그 decision rule에 대해서만 충분하며 상태의 충분통계량이라고부르지 않는다.

3.4 (\Pi): 조건부 exceedance surface

[\Pi_{\mathcal B}(c\mid z,\mathcal W,\nu)=\Pr_\nu!\left[Q_{\mathcal B}>c\mid Z=z,\mathcal W\right].]

필수 conditioning에는 가능한 경우(\beta_{\rm MO}(z),\beta_{\rm RM},) depth, mask, sky window를 포함한다.sampling law (\nu)는 다음 중 하나로 고정한다.

injection/mock law

bootstrap/resampling law

profile law

posterior predictive law

posterior pushforward law

MIO mock (\Pi)와 HTT posterior exceedance는 같은 기호 아래에서대체할 수 없다.

partial identification이면

[\underline\Pi(c)=\inf_{\theta\in\Theta_I}\Pi(c;\theta),\qquad\overline\Pi(c)=\sup_{\theta\in\Theta_I}\Pi(c;\theta)]

를 보고한다.

3.5 (F): certified sample-wise functional pushforward

active (F)는 “filling fraction”이 아니다. sign, ceiling,admissibility, anchor-support gate를 통과한 표본별(\mathbf x_\Phi^{(m)})의 pushforward로 정의한다.

CertifiedFunctionalPushforward
  sample_by_functional matrix
  functional/anchor ids
  mean, covariance, quantiles (derived summaries)
  sign and admissibility decisions
  scalarization policy, if one was preregistered

기존 (F=x_C/U)는 (p=1) legacy reducer로 byte-stable하게 유지한다.

3.6 (G_F): depth/mask path와 paired contrast

canonical object는 (G_F) scalar가 아니라(F(z,\mathcal W)) path이다. 두 bin/window의 paired contrast는

[\Delta_{ab}=\mathbf F_a-\mathbf F_b,]

[C_{\Delta,ab}=C_{aa}+C_{bb}-C_{ab}-C_{ba},]

[D_{ab}^2=\Delta_{ab}^{\mathsf T}C_{\Delta,ab}^{+}\Delta_{ab}.]

covariance-null residual과 orbit-stratum transition을 별도로 보고한다.양의 1차원 functional에서는[G_F=\exp(\log F_a-\log F_b)]가 legacy pushforward로 복원되지만, global tilt evidence로 해석하지않는다.

4. 완전 invariant ring 대신 generic separating atlas

4.1 표현

독립 orbit 분석의 기본 표현을

[V=S^2_0(\mathbb R^3)\oplus V_{\rm axial}^{\omega}\oplus V_{\rm polar}^{A}\oplus V_{\rm polar}^{\beta_{\rm RM}}\oplus V_{\rm polar}^{\beta_{\rm MO}}]

로 둔다. (\beta_{\rm RO})는 closure 검증에 보존하지만 독립 좌표로중복 삽입하지 않는다.

4.2 shear invariants와 strata

[I_2=\operatorname{tr}(\widehat\sigma^2),\qquadI_3=\operatorname{tr}(\widehat\sigma^3),]

[J_\sigma=\frac{\sqrt6,I_3}{I_2^{3/2}},\qquad\Delta_\sigma=\frac12 I_2^3-3I_3^2=\frac12 I_2^3(1-J_\sigma^2).]

real symmetric STF tensor에 대해 (|J_\sigma|\le1)이고(\Delta_\sigma\ge0)이다. (I_2=0)은 isotropic shear,(\Delta_\sigma=0)은 repeated-eigenvalue stratum이다.

Cayley-Hamilton:

[\widehat\sigma^3=\frac12 I_2\widehat\sigma+\frac13 I_3\mathbf1.]

따라서 vector contraction에 필요한 (\widehat\sigma)의 power는(0,1,2)로 줄어든다.

4.3 Gram-Krylov catalogue

각 typed vector (v_p)와 (n=0,1,2)에 대해

[B_{pq}^{(n)}=v_p^\top\widehat\sigma^n v_q]

를 계산한다. polar-axial cross contraction은 pseudoscalar이고,같은 parity끼리의 contraction은 scalar이다.

SO(3) invariant와 O(3) scalar/pseudoscalar covariant를 구분한다.pseudoscalar의 부호는 O(3) orbit 위의 상수가 아니므로, O(3)quotient에서 그대로 “invariant”라고 부르지 않는다.

4.4 cyclic-chart reconstruction

[K(v)=[v,\widehat\sigma v,\widehat\sigma^2v].]

(\det K(v)\ne0)인 vector를 cyclic reference라 한다. simple-spectrumstratum에서 다음 14개 값

[I_2,I_3,\quadv^\top\sigma^n v,\quadv^\top\sigma^n w_j\quad(n=0,1,2;\ j=1,2,3)]

은 한 STF tensor와 네 labeled vector의 generic orbit을 재구성하는한 chart를 이룬다. signed scalar/pseudoscalar 좌표를 유지하면oriented (SO(3)) orbit을 재구성하고, reflection law를 함께 quotient하면parity-typed (O(3)) equivalence class를 얻는다. 14는[5+4\times3-\dim SO(3)=14]와 일치한다.

모든 vector를 reference 후보로 계산하면 finite atlas가 된다.어느 후보도 cyclic하지 않으면 강제 분류하지 않고 degeneracystratum과 uncovered directions를 반환한다. (\det K(v)\ne0)라는exact 조건과 수치적으로 안정적인 조건은 다르므로, 각 chart는Vandermonde/Krylov singular spectrum, condition number 및WEAKLY_IDENTIFIED 상태도 함께 보고한다. 이 결과는 “전체 invariantring의 완전성”보다 약하지만 실제 분석에 필요한 generic separation을constructive하게 제공한다.

5. 새 positive theorem 프로그램

상태 표기:

READY: 현재 정의만으로 짧은 해석적 증명이 가능한 후보

CONDITIONAL: response/dynamics/regularity 전제가 필요한 후보

PROGRAM: CAS, simulation 또는 native input이 필요한 후보

Pillar T — 이론우주론 및 수리물리

ID

상태

positive statement

VT-T1

READY

Typed 1+3 kinematic decomposition과 기존 (\Sigma^2,W^2) normalization 사이의 convention-exact 변환

VT-T2

READY

Equivariant anchor-body gauge theorem: (\mathcal A(g y)=g\mathcal A(y))이면 (p_{\mathcal A(gy)}(gk)=p_{\mathcal A(y)}(k))

VT-T3

READY

Polar dual theorem: 모든 directional MES ratio의 supremum이 vector/tensor gauge를 복원

VT-T4

READY

Homogeneous functional bound: (

x_\phi

\le p_\mathcal A), 따라서 각 invariant ratio는 global stress의 인증 하한

VT-T5

READY

Shear shape theorem: (

J_\sigma

\le1), (\Delta_\sigma=\frac12I_2^3(1-J_\sigma^2)), multiplicity strata의 정확한 분류

VT-T6

READY

STF Cayley-Hamilton reduction으로 모든 vector-shear contraction을 power (0,1,2)에 축약

VT-T7

READY

Krylov determinant factorization과 cyclicity criterion; determinant/Gram residual을 orbit-chart validity gate로 사용

VT-T8

READY

Simple-spectrum cyclic chart의 generic (SO(3)) orbit reconstruction, parity-typed (O(3)) quotient 및 14-dimensional minimal local coordinate count

VT-T9

READY

Polar/axial parity theorem: scalar, pseudoscalar, SO(3) invariant, O(3) covariant의 변환법칙

VT-T10

READY

Amplitude-orbit factorization: (k\ne0)에서 anchor stress와 normalized orbit shape의 유일 분해

VT-T11

CONDITIONAL

Linear-response quotient theorem: supported tangent, nuisance tangent, covariance null을 분리한 observable morphology map

VT-T12

CONDITIONAL

Local/global source theorem: Schur information이 양수일 필요충분조건과 principal-angle 기반 weak-identification bound

VT-T13

CONDITIONAL

Invariant evolution identities: (I_2,I_3,J_\sigma)의 1+3 propagation을 (E_{ab},H_{ab},\pi_{ab},A_a,\omega_a) source로 분해

VT-T14

PROGRAM

Kinematic/orbit type에서 geometry type으로 승격하는 충분 observable set; Weyl/3-curvature가 없으면 partial type report 유지

Pillar S — 통계학 및 실제 분석

ID

상태

positive statement

VT-S1

READY

Functional-profile dominance: deterministic scalarization은 원 profile보다 식별정보를 늘릴 수 없고, 등록된 acceptance decision에 대해서만 충분

VT-S2

READY

Acceptance-body (Q) theorem: vector threshold, max statistic, covariance ellipsoid를 하나의 gauge로 통일

VT-S3

CONDITIONAL

Matched-null max-(Q) calibration과 simultaneous/FWER 제어

VT-S4

READY

Conditional (\Pi) surface의 survival monotonicity와 sampling-law typing

VT-S5

CONDITIONAL

Partially identified (\Pi) envelope의 honest lower/upper coverage

VT-S6

CONDITIONAL

Joint random numerator-anchor confidence-body pushforward; component별 독립 Fieller 사용보다 joint law를 우선

VT-S7

READY

Certified sample-wise (F) pushforward와 ratio-of-means 비대체 정리

VT-S8

READY

Paired depth contrast covariance 정리와 cross-covariance 누락의 정확한 오차항

VT-S9

CONDITIONAL

ZoA/mask path의 pseudoinverse Mahalanobis contrast, eigenspace drift, stratum transition을 결합한 finite-path test

VT-S10

CONDITIONAL

Full-rank이지만 작은 singular value/principal angle인 WEAKLY_IDENTIFIED cell의 오분류 상계

VT-S11

CONDITIONAL

Generic separating orbit chart와 injective supported response가 결합될 때 anisotropy type이 identifiable하다는 composition theorem

VT-S12

CONDITIONAL

Matched counterpair에서 scalar-equal/anchor-equal sky를 phase, orientation, parity feature가 구별하는 power theorem

VT-S13

CONDITIONAL

Open-set type report의 abstention/coverage 및 finite-library sensitivity

VT-S14

PROGRAM

Depth-conditioned local/global discrimination: (\beta_{\rm MO}(z)), (\beta_{\rm RM}), mask path를 조건화한 response-class analysis

수학적 invariant 자체는 고전 invariant theory와 겹치므로 “세계 최초”주장을 하지 않는다. 프로젝트의 차별점 후보는 MES anchor gauge,generic orbit atlas, supported response geometry, conditional partialidentification을 하나의 재현 가능한 분석 체계로 결합하는 데 있다.

6. 최종 출력 contract

AnisotropyTypeReport
  premise_contract
  anchor_stress:
    gauge interval, functional lower bounds, anchor ids
  kinematic_type:
    shear multiplicity, cyclic charts and condition numbers
    invariant intervals, parity
  observable_morphology:
    alm/power-tensor/BiPoSH features, supported response rank
  local_global:
    MISSING_RESPONSE_PROVIDER | NON_IDENTIFIED | SUM_ONLY
    | WEAKLY_IDENTIFIED | SEPARABLE_CANDIDATE
  depth_mask_path:
    paired contrasts, ZoA stability, stratum transitions
  open_set:
    equivalence class, candidate, unknown/ambiguous abstention
  geometry_type:
    PARTIAL unless Weyl/curvature/native requirements are met
  uncovered_directions
  assumptions, covariance/null provenance, sampling law
  allowed_use, forbidden_use

7. 구현 DAG 초안

현재 canonical status에서 PR-258은 GitHub에는 병합되었지만 trackedstatus에는 아직 pending이다. 그 closeout을 성공 dependency로동기화하기 전에는 다음 과학 change-set을 실행하지 않는다.

VT-00 / formal replan — 새 카드와 claim boundary만 등록

VT-01 / state SSOT — 세 상태층, convention, legacy adapter

VT-02 / anchor body — convex body, gauge, support, functional metadata

VT-03 / orbit atlas — (A,\beta_{\rm RM},\beta_{\rm MO}) 확장,shear strata, cyclic charts, parity

VT-04 / (x,Q,F) — functional profile와 scalar compatibility

VT-05 / conditional (\Pi) — sampling-law split, identified envelopes

VT-06 / path (G_F) — depth/ZoA joint covariance와 finite contrasts

VT-07 / response/type report — weak-identification status와AnisotropyTypeReport

VT-08 / theorem registry v3 — 65개 legacy record의 두 기둥 배치,representation/signature/proof-obligation schema

VT-09 / Pillar T proofs — 기존 31개 migration + VT-T1–T14

VT-10 / Pillar S proofs — 기존 34개 migration + VT-S1–S14

VT-11 / synthetic integration — matched counterpairs, coverage,mutation and calibration

VT-12 / manuscript integration — 검증된 정리만 본문 승격

VT-02와 VT-03은 VT-01 이후 병렬 가능하다. VT-04–VT-07은 두 결과를모두 필요로 한다. 실제 PR-151 자료는 acquisition 완료와 별도의data-release gate 이후에만 VT-11/12에 연결한다.

7.1 2026-07-30 baseline remediation gate

현재 환경(Python 3.12.13, NumPy 2.3.5)에서 PR-257/258,PR-124/125 focused suite는 86 passed, 2 failed였다.

PR-258 correlation-null unit-congruence test에서 수학적으로 0인supported squared distance가 한 scaling에서는 0.0, 다른scaling에서는 4.81482486096809e-35로 직렬화된다. covariancequotient의 scale-aware zero canonicalization을 contract로 고정해야하며, 단순히 test를 approximate equality로 약화하지 않는다.

PR-124 freeze test는three_bound_hierarchy.py의 옛 hashcc3ba8...를 요구하지만, PR-252 consumer migration은 현재 hash281a35...를 의도적으로 등록했고mes_successor_registry.py도 후자를 권위값으로 사용한다.PR-124 historical freeze와 post-PR252 successor authority의 범위를명시적으로 분리해 stale pin을 해소해야 한다.

이 두 항목과 PR-258의 tracked pending/GitHub merged 상태 동기화가VT-00의 선행조건이다.

8. 검증 및 kill switches

필수 검증

exact legacy (x_C,Q,\Pi,F,G_F) reproduction

O(3)/SO(3) equivariance 및 parity metamorphic tests

dimensional analysis와 (c=1\leftrightarrow c) unit round trip

FLRW zero, no-tilt, local-boost, global-tilt limit을 서로 분리

rank-deficient covariance와 structural-null destructive tests

simple/repeated/zero shear spectrum strata

cyclic chart reconstruction과 chart-overlap consistency

exact cyclicity와 numerically weak chart를 분리하는 condition gate

matched scalar-equal, (C_\ell)-equal, anchor-equal counterpairs

conditional (\Pi) coverage와 sampling-law substitution rejection

paired/unpaired depth covariance mutation

open-set unknown/ambiguous abstention

claim-language and provenance lint

CAS

새 algebraic completeness/separation 주장은 동일 contract에 대해Wolfram+xAct, SymPy, Sage+Singular, Lean의 네 축을 통과해야 한다.수치 일치만으로 physical proof 또는 global invariant-ring completeness를선언하지 않는다.

즉시 중단 조건

scalar amplitude stress를 nonlinear distance 또는 FLRW converse로 표현

(\beta_{\rm MO})를 geometric departure에 직접 합산

missing acceleration/MES/response provider를 0으로 채움

pseudoscalar를 O(3) invariant라고 표기

complete invariant basis를 generic chart 결과로부터 선언

component별 ratio uncertainty에서 shared covariance를 제거

(F)를 occupancy/filling으로, (\Pi)를 truth probability로,(G_F)를 global-tilt evidence로 해석

covariance-null residual을 supported score에 흡수

unknown response class를 nearest known class로 강제

PR-151 partial bytes를 fixture, calibration 또는 conclusion에 사용

9. 문헌상의 위치

MES의 출발점:[Maartens, Ellis & Stoeger (1995), arXiv/9501016](https://arxiv.org/abs/astro-ph/9501016)

almost-isotropy의 converse 제한:[Nilsson et al. (1999), arXiv/9904252](https://arxiv.org/abs/astro-ph/9904252)

symmetric tensors/vectors의 isotropic representation:[Smith (1971), DOI 10.1016/0020-7225(71)90023-1](https://doi.org/10.1016/0020-7225(71\)90023-1)

scalar/vector/tensor isotropic function의 irreducible representation:[Shariff (2022), arXiv:2207.09617](https://arxiv.org/abs/2207.09617)

identified set의 support-function inference:[Liao & Simoni (2012), arXiv:1212.3267](https://arxiv.org/abs/1212.3267)

intersection-bound inference:[Chernozhukov, Lee & Rosen (2009), arXiv:0907.3503](https://arxiv.org/abs/0907.3503)

저차수 CMB morphology:[Copi, Huterer & Starkman (2003), arXiv/0310511](https://arxiv.org/abs/astro-ph/0310511)

BipoSH statistical-isotropy formalism:[Hajian & Souradeep (2004), arXiv/0501001](https://arxiv.org/abs/astro-ph/0501001)

Appendix A. 기존 65개 proof record의 두 기둥 migration inventory

T는 이론우주론/수리물리, S는 통계/데이터 분석의 primary pillar다.CHECKED는 현행 v2 typed signature가 완전하다는 뜻이며, 새vector/tensor lift까지 완료됐다는 뜻은 아니다.

ID

Pillar

Legacy status

v2 signature

Title

P1

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Signed comparator identity and Domain-checked semantics

P2

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Diagnostic variables Q, F, Pi, G_F, and P_post are distinct

P3

T

ACTIVE_CONDITIONAL

CHECKED

Diagonal MES three-bound hierarchy

P4

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Frame-attribution safe-route correction

P5

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Conditional Bianchi V momentum-response formula

P6

T

ACTIVE

MIGRATION_PENDING

Flat-FLRW first jet

P7

T

ACTIVE

MIGRATION_PENDING

Non-collinear boost composition and first-jet separation

P8

S

ACTIVE

MIGRATION_PENDING

Response rank and duplicated channels

P9

T

ACTIVE

MIGRATION_PENDING

Radial-vorticity blindness

P10

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Single-shell degeneracy and broad-depth rank recovery

P11

T

ACTIVE

CHECKED

PSD second-moment cone

P12

T

ACTIVE

MIGRATION_PENDING

Scalar tilt trace is not sufficient

P13

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Shear memory of anisotropic stress

P14

T

ACTIVE

MIGRATION_PENDING

Dust-FLRW oracle

P15

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Quadrupole filling under registered closure

P16

S

ACTIVE

MIGRATION_PENDING

Single-sky sampling dispersion

P17

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Multi-ell Fisher floor and transfer-profile refinement

P18

S

ACTIVE

CHECKED

Graded rank-2 comparator

P19

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Exceedance and e-value calibration

P20

S

ACTIVE

MIGRATION_PENDING

Rao-Blackwell reachable-sector domination

P21

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Volterra depth-memory representation

P22

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Transverse reopening of the vorticity sector

P23

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Diagonal covariance compression loses morphology

P24

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Full-covariance MES tightening

P25

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Rank-failure no-result and morphology information gain

P26

S

SUPERSEDED

MIGRATION_PENDING

Partial-identification interval for x_C (one-sided nonnegative cone)

P27

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

MES-rank route reconciliation

P28

S

ACTIVE

MIGRATION_PENDING

Posterior prior-exposure under null directions

P29

S

ACTIVE

MIGRATION_PENDING

Finite-cover e-value combination

P30

S

ACTIVE

MIGRATION_PENDING

Parameter duplication versus observation duplication

P31

S

SUPERSEDED

MIGRATION_PENDING

Identified-set sharpness over PSD and ceiling cones

P32

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Optical ansatz branch identifiability

P33

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Depth-gap delta-method propagation

P34

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Vector-g response covariance propagation

P35

S

SUPERSEDED

MIGRATION_PENDING

Two-stage identified-set coverage with Imbens-Manski endpoint correction

P36

S

RETRACTED

MIGRATION_PENDING

Joint-feasible-set depth-gap interval propagation ("strict whenever")

T1p

S

ACTIVE

CHECKED

Signed-box two-branch identified interval (curvature signed, two-sided)

DL1

S

ACTIVE

CHECKED

Lower-gap monotonicity of the all-curvature branch

L-T2-EXIST

S

ACTIVE

CHECKED

Existence-level depth-gap strictness lemma

T2p

S

RETRACTED

MIGRATION_PENDING

Depth-gap strictness per-endpoint iff via coefficient signs

T2pp

S

ACTIVE

MIGRATION_PENDING

Signed-numerator domain repair of the fixed-pairing quotient interval

T3-lin

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Linearized realization of the identified-interval endpoints

T3-full

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Exact constraint-surface endpoint witnesses

T3-int

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Interior x_C-value family

T4p

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Estimated-covariance residual test is Hotelling T-squared/F

T5p

S

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Exact deterministic-width Imbens-Manski endpoint coverage

T8p

S

ACTIVE

MIGRATION_PENDING

Noncentral-chi-square power monotonicity

T9p

T

ACTIVE

MIGRATION_PENDING

Multi-component tilt composition

MES-PROV

T

ACTIVE

CHECKED

MES coefficient provenance

U1

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Beta-channel toy correspondence

U2

T

ACTIVE_CONDITIONAL

MIGRATION_PENDING

Fingerprint envelope ceilings at eps1

U3

S

ACTIVE

MIGRATION_PENDING

Rank-2 response schema correspondence

U4

S

SUPERSEDED

MIGRATION_PENDING

Teff fingerprint statistical closure

T2G

S

ACTIVE

CHECKED

General fractional-program interval theorem

TSUM

T

ACTIVE

CHECKED

Two-temperature fingerprint sum bound

U4-v9

S

ACTIVE

MIGRATION_PENDING

Teff fingerprint statistical closure, v9 rerun

MES-BR

T

ACTIVE

CHECKED

MES coefficient branch registry

BV-DYN

T

ACTIVE

MIGRATION_PENDING

Tilted-LRS Bianchi V evolution seal

K5-CARD-v2

S

ACTIVE

MIGRATION_PENDING

K5/CF4 identified-interval card v9

KE-FRAME

T

ACTIVE

MIGRATION_PENDING

King-Ellis tilted-congruence frame kinematics and constraint algebra

KE-OBS

T

ACTIVE

MIGRATION_PENDING

Exact vorticity classification of group-invariant tilted congruences

KE-DYN

T

ACTIVE

MIGRATION_PENDING

Rotating perfect-fluid development and flat-curvature obstructions

OMK-REOPEN

T

ACTIVE

MIGRATION_PENDING

Higher-order anisotropic-curvature reopening transfer

MES-REFREEZE

T

ACTIVE

CHECKED

MES geodesic derivation and vorticity-anchor refreeze

MES-MESB-TRACE

T

ACTIVE

CHECKED

MESb source trace and non-geodesic-bound refutation

합계:

registry records: 65

current fully typed CHECKED: 12

current MIGRATION_PENDING: 53

historical SUPERSEDED: 4

historical RETRACTED: 2

primary Pillar T: 31

primary Pillar S: 34
