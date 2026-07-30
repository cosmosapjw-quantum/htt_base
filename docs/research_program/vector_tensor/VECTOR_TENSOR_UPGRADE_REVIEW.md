> **PR-260 tracked-source normalization.** The attachment identity is retained
> in `PROGRAM_INTAKE_REGISTRY_V1.yaml`. One standalone seven-equals line was
> normalized to the single equality relation it denotes because Git treats the
> original byte sequence as a merge-conflict sentinel. No source claim or
> status was promoted.

# 종합 판단

지금은 “scalar formalism을 이제 처음 vector화하는 단계”가 아니야. 최신 branch는 PR-254의 typed anchor geometry, PR-255의 matrix-valued anchored response geometry, PR-256의 local/global velocity-response 분리, PR-257의 ((\sigma,\omega,\beta)) orbit catalogue와 low-(\ell) morphology benchmark, PR-258의 open-set response-class quotient까지 이미 병합된 상태다. 최신 원격 HEAD도 PR-258 merge인 `e7c2064…`다.

첨부 텍스트의 진단이 정확하다. 현재 핵심은

[
\text{kinematic component state}
\longrightarrow
O(3)\text{ orbit/type}
\longrightarrow
(x,Q,\Pi,F,G_F)
\longrightarrow
\text{conditional partial classification}
]

이며, 남은 병목은 다음 세 가지다.

1. (\sigma_{ab},\omega_a,\beta_a)를 담은 현재 state와 (\beta_{\rm RO},\beta_{\rm RM},\beta_{\rm MO}) frame bundle, 그리고 아직 빠져 있는 (A_a)를 하나의 정본 구조로 통합하는 일.
2. 기존의 scalar (x,Q,\Pi,F,G_F)를 단순한 componentwise vector로 바꾸는 데서 그치지 않고, **tensor/orbit/set/path-valued functional family**로 일반화하는 일.
3. 오래된 theorem registry와 PR-254–258에서 새로 구현된 수학을 하나의 증명 체계로 다시 편성하는 일.

특히 active MIO surface는 이미 과거 scalar (Q,F,\Pi,G_F) builder를 `mio.legacy_projection`으로 격리하고, 현재 formalism에는 typed state, identified set, anchor stress, orbit/nonlinearity object만 노출한다. 그러므로 scalar API를 다시 확장하기보다, **새 vector/tensor successor를 별도 정본으로 세우고 과거 값은 compatibility view로만 유지**해야 한다.

내가 권하는 새 formalism의 이름은 다음이다.

[
\boxed{
\textbf{Orbit-Resolved Premise-Anchored Inference}
}
]

물리 state의 (O(3)) orbit, MES를 포함한 premise anchor, 관측 response geometry, partial identification, depth/mask path를 하나의 체계로 묶는 방식이다.

---

# 1. 새 canonical state

## 1.1 세 개의 객체로 분리한다

현재 `DepartureState`는

[
(\sigma_{ab}[5],\omega_a[3],\beta_a[3],\Delta\Omega_k)
]

를 보존하고 frame, congruence, epoch/window, averaging scale, basis, units, parity와 perturbative order를 기록한다. 하지만 (A_a)가 없고, `beta_a`의 물리적 역할도 PR-256의 세 velocity와 완전히 통합되어 있지 않다.

이를 다음처럼 나누는 것이 가장 안전하다.

### A. CongruenceKinematics

[
\mathcal K_u(z,\mathcal W,L)=
\left(
\widehat\sigma_{\langle ab\rangle},
\widehat\omega_a,
\widehat A_a
\right),
]

[
\widehat\sigma_{ab}=\frac{\sigma_{ab}}{\Theta},
\qquad
\widehat\omega_a=\frac{\omega_a}{\Theta},
\qquad
\widehat A_a=
\frac{A_a}{c\Theta}.
]

코드가 (c=1), (u^au_a=-1) convention을 사용하는 branch에서는 (\widehat A_a=A_a/\Theta)지만, 두 convention을 metadata 없이 혼합하면 안 된다.

### B. VelocityFrameBundle

[
\mathcal V=
\left(
\beta_{{\rm RO},a},
\beta_{{\rm RM},a},
\beta_{{\rm MO},a}
\right),
]

[
\beta_{\rm RO}
==============

\beta_{\rm RM}+\beta_{\rm MO}
+O(\beta^2).
]

* (\beta_{\rm RM}): radiation–matter, global-matter-tilt candidate
* (\beta_{\rm MO}): matter–observer, local boost
* (\beta_{\rm RO}): radiation–observer, derived closure quantity

PR-256은 이 분해를 이미 fail-closed 방식으로 구현하며, missing velocity를 다른 둘로부터 자동 추론하지 않는다.

### C. GeometryState

초기 버전은

[
\mathcal G=
\left(
\Delta\Omega_k
\right)
]

만 가져도 되지만, “full anisotropy type”으로 가려면 장기적으로

[
\mathcal G=
\left(
{}^{(3)}S_{ab},
E_{ab},
H_{ab},
\pi_{ab},
\Delta\Omega_k
\right)
]

까지 올라가야 한다.

여기서 (\Delta\Omega_k)는 scalar curvature-budget departure이고,

[
{}^{(3)}S_{ab}
==============

{}^{(3)}R_{\langle ab\rangle}
]

가 실제 anisotropic spatial-curvature tensor다. 두 물체를 같은 것으로 부르면 안 된다.

최종 정본은

```python
JointAnisotropyState(
    congruence_kinematics=...,
    velocity_frames=...,
    geometry_state=...,
    frame=...,
    congruence=...,
    epoch_window=...,
    averaging_scale=...,
    units=...,
    perturbative_order=...,
)
```

가 되어야 한다.

---

## 1.2 representation space

초기 complete kinematic state의 representation은

[
\mathcal V_{\rm kin}
====================

V_2^\sigma
\oplus
V_{1,\rm axial}^{\omega}
\oplus
V_{1,\rm polar}^{A}
\oplus
V_{1,\rm polar}^{\beta_{\rm RM}}
\oplus
V_{1,\rm polar}^{\beta_{\rm MO}}
\oplus
V_0^{\Delta\Omega_k}.
]

차원은

[
5+3+3+3+3+1=18.
]

(\beta_{\rm RO})는 독립 좌표가 아니라 closure-derived view다.

이렇게 해야 local boost와 global tilt가 같은 polar-vector representation에 속하면서도, **서로 다른 frame morphism과 response provider를 갖는 distinct typed blocks**로 남는다.

---

# 2. orbit catalogue v3

현재 PR-257 catalogue는 이미

[
V_2^\sigma
\oplus
V_{1,\rm axial}^{\omega}
\oplus
V_{1,\rm polar}^{\beta}
]

에 대해 12개 polynomial을 구현한다.

[
\operatorname{tr}\sigma^2,\quad
\operatorname{tr}\sigma^3,\quad
\beta^2,\quad
\beta\cdot\sigma\beta,\quad
\beta\cdot\sigma^2\beta,
]

[
\det(\beta,\sigma\beta,\sigma^2\beta),
]

[
\omega^2,\quad
\omega\cdot\sigma\omega,\quad
\omega\cdot\sigma^2\omega,
]

[
\beta\cdot\omega,\quad
\beta\cdot\sigma\omega,\quad
\beta\cdot\sigma^2\omega.
]

parity와 Cayley–Hamilton syzygy도 검사하지만, generic orbit separation과 invariant-ring completeness는 명시적으로 `UNPROVEN`이다.

이 조심스러운 경계는 유지해야 한다. tensor invariant 문헌에서는 integrity basis와 separating/function basis가 서로 같지 않을 수 있고, 최근에도 제안된 vector–tensor functional basis가 실제 orthogonal transformation에서 invariant하지 않는다는 반례가 보고되었다. 따라서 “많은 invariant를 계산했다”와 “orbit을 완전히 분리한다”는 전혀 다른 claim이다. ([[Springer Link](https://link.springer.com/article/10.1007/s42558-024-00056-1)][1])

## 2.1 수작업 invariant 목록에서 Gram–Krylov generator로

[
v_i\in
{
\omega,A,\beta_{\rm RM},\beta_{\rm MO}
}
]

에 대해 다음 family를 생성한다.

[
G^{(k)}_{ij}
============

v_i^{a}(\sigma^k)_{ab}v_j^b,
\qquad
k=0,1,2.
]

trace-free (3\times3) shear에는

[
\sigma^3
========

\frac12
\operatorname{tr}(\sigma^2)\sigma
+
\frac13
\operatorname{tr}(\sigma^3)I
]

가 성립하므로 (k\ge3) contraction은 (k=0,1,2)로 환원된다.

parity-odd 또는 handedness quantities는

[
\epsilon_{abc}v_i^av_j^bv_k^c,
]

[
\det(v_i,\sigma v_j,\sigma^2v_k)
]

형태로 생성한다.

각 vector의 parity는 반드시 붙는다.

* (\omega): axial
* (A,\beta_{\rm RM},\beta_{\rm MO}): polar

따라서 예를 들면

[
\beta_{\rm RM}\cdot\omega,
\qquad
A\cdot\omega
]

는 pseudoscalar이고,

[
\omega\cdot
(\beta_{\rm RM}\times A)
]

는 scalar다.

## 2.2 shear stratum

[
I_2=\operatorname{tr}\sigma^2,
\qquad
I_3=\operatorname{tr}\sigma^3.
]

[
\Delta_\sigma
=============

\frac12I_2^3-3I_3^2.
]

real symmetric trace-free (\sigma)에서는

[
\Delta_\sigma\ge0.
]

* (\Delta_\sigma>0): generic triaxial stratum
* (\Delta_\sigma=0,\ I_2>0): repeated-eigenvalue, axisymmetric stratum
* (I_2=0): isotropic shear origin

shape coordinate는

[
J_\sigma
========

\sqrt6,
\frac{I_3}{I_2^{3/2}},
\qquad
-1\le J_\sigma\le1.
]

이것은 amplitude와 shear eigenvalue morphology를 분리한다.

## 2.3 새 positive theorem 후보: generic orbit separation

가장 강한 새 수리물리 결과 후보는 이것이다.

> **Generic Gram–Krylov separation theorem**
> (\sigma)가 distinct eigenvalues를 가지고, 등록된 vector family가 충분한 support를 가질 때,
> [
> \operatorname{tr}\sigma^2,\ \operatorname{tr}\sigma^3,
> v_i\cdot\sigma^kv_j,\quad k=0,1,2
> ]
> 와 적절한 parity/handedness invariant가 generic (O(3)) 또는 (SO(3)) orbit을 분리한다.

증명 경로는 명확하다.

1. (I_2,I_3)가 shear eigenvalues를 permutation까지 결정한다.
2. distinct eigenvalue일 때 spectral projectors (P_\alpha)는 (\sigma)의 2차 polynomial이다.
3. (v_i\cdot P_\alpha v_j)는 각 eigenspace에서 vector component들의 Gram matrix다.
4. 이 Gram family는 (O(3)) orbit을 결정한다.
5. (SO(3))에서는 남는 mirror ambiguity를 하나의 signed pseudoscalar가 제거한다.

현재의 degree-bounded catalogue에서 **coordinate-free generic kinematic anisotropy classifier**로 올라갈 수 있는 중요한 positive theorem이다. Tensor invariant theory에서도 irreducible SO(3) components와 joint invariants를 이용해 복합 tensor의 integrity basis를 구성하는 접근이 표준적이다. ([[arXiv](https://arxiv.org/abs/1605.09561)][2])

degenerate shear strata에서는 stabilizer가 커지므로 별도의 (O(2))-quotient theorem이 필요하다. generic theorem을 전체 space에 억지로 확장하지 말고 stratified orbit atlas로 구성해야 한다.

---

# 3. (x,Q,\Pi,F,G_F)의 vector/tensor successor

## 3.1 (x): functional-indexed object

앞으로 (x)는 하나의 scalar가 아니라 등록된 functional의 출력이다.

[
X_\phi
======

\phi[\mathcal K,\mathcal V,\mathcal G],
]

[
\phi:
\mathcal X
\longrightarrow
W_\phi.
]

(W_\phi)는 다음 중 하나일 수 있다.

* scalar
* pseudoscalar
* polar/axial vector
* PSTF tensor
* invariant vector
* orbit stratum
* identified set
* depth path

equivariant functional에는

[
\phi(R\cdot X)
==============

\rho_\phi(R)\phi(X)
]

를 요구한다.

예:

| Functional            | Output                        |
| --------------------- | ----------------------------- |
| identity              | full state                    |
| shear block           | PSTF5                         |
| vorticity block       | axial vector                  |
| (I_2,I_3,J_\sigma)    | scalar vector                 |
| Gram–Krylov catalogue | invariant/pseudoscalar vector |
| Gauss budget          | scalar (x_C)                  |
| response projection   | observable vector             |

기존

[
x_C
===

\Sigma^2-W^2+\Omega_{\rm tilt}+\Delta\Omega_k
]

는

[
X_{\phi_C},
\qquad
\phi_C=\text{GaussBudgetProjection}
]

라는 한 functional로 남긴다.

현재 `ComponentBreakdown`은 정확히 네 scalar component만 요구하고 하나의 signed projection을 만든다. 이것은 새 state의 primary object가 아니라 `GaussBudgetProjection` 또는 legacy compatibility view로 이름과 위치를 제한해야 한다.

---

## 3.2 (Q): anchor-normalized coordinate report

일반 anchor body (\mathcal A)에 대해

[
\rho_{\mathcal A}(x)
====================

\inf{
\lambda>0:x\in\lambda\mathcal A
}
]

를 사용한다.

단순 vector quotient가 아니라 다음을 함께 내야 한다.

[
\mathcal Q_{\mathcal A}(x)
==========================

\left(
q_{\mathcal A},
\rho_{\mathcal A},
b_{\mathcal A},
\mathcal F_{\rm active}
\right),
]

* (q_{\mathcal A}=D_{\mathcal A}^{-1}x): invertible normalizer가 있을 때의 coordinate
* (\rho_{\mathcal A}): gauge/stress
* (b_{\mathcal A}=x/\rho_{\mathcal A}(x)): boundary direction, (\rho>0)일 때
* (\mathcal F_{\rm active}): active face 또는 active blocks

identified set (\mathcal I_X)에는 point (Q) 대신

[
\mathcal Q_{\mathcal A}(\mathcal I_X)
=====================================

{
\mathcal Q_{\mathcal A}(x):x\in\mathcal I_X
}
]

와 gauge interval

[
[
\rho_-,\rho_+
]
=

\left[
\inf_{x\in\mathcal I_X}\rho_{\mathcal A}(x),
\sup_{x\in\mathcal I_X}\rho_{\mathcal A}(x)
\right]
]

를 출력한다.

현재 `anchor_geometry.py`는 product block balls, ellipsoids와 symmetric polytopes, finite conditional families와 missing/withheld anchors를 이미 지원하므로 이 계층을 새로 쓰기보다 확장해야 한다.

---

## 3.3 (F): directional support-utilization profile

과거 (F)를 “전체 anisotropy budget의 몇 퍼센트”로 해석하면 scalar cancellation과 denominator arbitrariness가 다시 들어온다.

새 (F)는 identified set과 anchor의 **directional support ratio**가 적합하다.

closed convex set (\mathcal I)의 support function은

[
h_{\mathcal I}(u)
=================

\sup_{x\in\mathcal I}u^\mathsf Tx.
]

[
f_{\mathcal I,\mathcal A}(u)
============================

\frac{h_{\mathcal I}(u)}
{h_{\mathcal A}(u)},
\qquad
h_{\mathcal A}(u)>0.
]

전체 utilization은

[
F^*_{\mathcal I,\mathcal A}
===========================

\sup_u
f_{\mathcal I,\mathcal A}(u).
]

핵심 정리는

[
\mathcal I\subseteq\mathcal A
\quad\Longleftrightarrow\quad
F^*\le1.
]

singleton (\mathcal I={x})에서는 적절한 convex-body 조건 아래

[
F^*=\rho_{\mathcal A}(x).
]

따라서 scalar saturation을 버리지 않으면서도, **어느 physical direction이 anchor를 가장 압박하는지 witness direction을 함께 제공**한다.

support function은 convex identified set을 완전히 표현할 수 있고, partial-identification inference에서도 identified set 자체와 그 support function에 대한 confidence construction이 사용된다. ([[arXiv](https://arxiv.org/abs/1212.3267)][3])

실제 report는 다음을 포함해야 한다.

```python
SupportUtilizationProfile(
    direction_ids=...,
    signed_support_ratios=...,
    antipodal_support_ratios=...,
    maximum_utilization=...,
    witness_directions=...,
    active_blocks=...,
    anchor_id=...,
    identified_set_id=...,
)
```

* signed profile: source direction/handedness
* antipodal profile: unoriented axis
* maximum profile: overall premise stress

---

## 3.4 (\Pi): conditional exceedance surface

새 정의는

[
\Pi_{\phi,T}
\left(
c\mid\eta
\right)
=

P_\nu
\left[
T\left(
\mathcal Q_{\mathcal A}(X_\phi)
\right)\ge c
\mid\eta
\right].
]

[
\eta=
\left(
\beta_{\rm MO}(z),
\beta_{\rm RM},
\mathcal W,
\mathcal S_{\rm sys},
\text{frame},
\text{anchor branch}
\right).
]

(T)는 사전 등록된 functional이다.

* radial gauge exceedance: (\rho_{\mathcal A}>c)
* block maximum
* directional support exceedance
* orbit-distance exceedance
* parity-odd statistic
* max-over-morphology family

`sampling_law`를 반드시 구분한다.

```text
NULL_SIMULATION
FIXED_INJECTION
BOOTSTRAP
PROFILE_LIKELIHOOD
POSTERIOR_PREDICTIVE
POSTERIOR_PUSHFORWARD
```

local/global state나 nuisance가 point-identified되지 않으면 하나의 (\Pi)를 내지 않는다.

[
\underline\Pi(c)
================

\inf_{\eta\in\mathfrak I_\eta}
\Pi(c\mid\eta),
]

[
\overline\Pi(c)
===============

\sup_{\eta\in\mathfrak I_\eta}
\Pi(c\mid\eta).
]

MIO는 mock/null-calibrated surface를 소유하고, posterior-conditioned surface는 HTT가 소유해야 한다.

---

## 3.5 (G_F): depth/mask orbit path

단순

[
G_F(z)=\frac{F(z)}{F(z_{\rm ref})}
]

는 denominator zero, orientation change와 cross-bin covariance를 처리하지 못한다.

새 객체는

[
\mathfrak G_F
=============

\left{
F_z(u),,
\Delta\log F_z(u),,
d_{\rm orbit}(z,z_0),,
\text{stratum transitions}
\right}.
]

frame/basis transport (\mathcal P_{z\to z_0})가 등록됐을 때

[
G_F(z,z_0;u)
============

## \log f_z(u)

\log f_{z_0}
\left(
\mathcal P^*_{z\to z_0}u
\right).
]

0 또는 sign-changing direction에는 ratio/log를 강제하지 않고 support difference를 쓴다.

[
\Delta h(u)
===========

## h_{\mathcal I_z}(u)

h_{\mathcal I_{z_0}}
(\mathcal P^*u).
]

orbit drift는

[
d_{\rm orbit}
\left(
[\mathcal K(z)],
[\mathcal P\mathcal K(z_0)]
\right)
]

로 별도 보고한다.

CF4의 ZoA 분석에는

```python
DepthMorphologyPath(
    depth_grid=...,
    mask_path=...,
    affine_state=...,
    orbit_invariant_intervals=...,
    support_profiles=...,
    cross_depth_mask_covariance=...,
    change_points=...,
)
```

가 맞다.

nested masks와 depth bins가 같은 sky를 공유하므로 모든 (z), (b_{\rm cut}) 결과의 joint covariance를 포함해야 한다.

---

# 4. 두 기둥의 새 증명 registry

현재 theorem registry는 ACTIVE, CONDITIONAL, SUPERSEDED, RETRACTED, WITHHELD와 sharpness level을 잘 구분한다. 하지만 legacy P-series, v9 theorem, PR-254–258 executable contracts가 하나의 object ontology로 통합되어 있지는 않다.

새 registry에는 최소한 다음 필드를 추가해야 한다.

```yaml
pillar: THEORY_MATHPHYS | STATISTICS_DATA
object_level:
  STATE | ORBIT | ANCHOR | RESPONSE |
  IDENTIFIED_SET | DEPTH_PATH | LEGACY_VIEW
statement_kind:
  THEOREM | LEMMA | PROPOSITION |
  COUNTEREXAMPLE | ALGORITHMIC_CONTRACT
proof_grade:
  ANALYTIC_PROOF
  FORMAL_CAS_PROOF
  CERTIFIED_NUMERICAL_PROOF
  FINITE_SAMPLE_STATISTICAL_PROOF
  ASYMPTOTIC_PROOF
  SIMULATION_VALIDATION
  CONJECTURE
positive_scientific_delta:
supersedes:
downstream_consumers:
```

`SIMULATION_VALIDATION`은 증명으로 세면 안 된다.

---

## 4.1 기둥 I — 이론우주론·수리물리

| ID        | 명제·결과                                                                                                          | 상태            |
| --------- | -------------------------------------------------------------------------------------------------------------- | ------------- |
| **TC-01** | Extended typed kinematic-state decomposition과 (O(3)) polar/axial/STF action                                    | 기존 PR-251 확장  |
| **TC-02** | Shear discriminant (\Delta_\sigma)와 triaxial/axisymmetric/isotropic stratum theorem                            | 신규            |
| **TC-03** | Generic Gram–Krylov (O(3))-orbit separation theorem                                                            | 신규 핵심         |
| **TC-04** | (SO(3)) mirror ambiguity를 signed pseudoscalar가 완성하는 handedness theorem                                         | 신규            |
| **TC-05** | Repeated-eigenvalue stabilizer와 degenerate orbit strata classification                                         | 신규            |
| **TC-06** | (\beta_{\rm RO}=\beta_{\rm RM}+\beta_{\rm MO}+O(\beta^2)) typed frame-closure theorem                          | PR-256 강화     |
| **TC-07** | Local/global tangent-space exact overlap, weak separation, direct-sum classification                           | PR-256 강화     |
| **TC-08** | MES scalar invariant ceiling이 STF/vector block ball 또는 ellipsoid를 유도하는 anchor-lifting theorem                  | 신규            |
| **TC-09** | MES amplitude anchor와 orbit morphology의 factorization: 같은 stress에서 다른 orbit 가능                                 | 신규 positive   |
| **TC-10** | Four-acceleration은 Hamiltonian density block이 아니라 Raychaudhuri/transport source block이라는 decomposition theorem | 신규            |
| **TC-11** | Radial-vorticity null과 transverse/spin-2 reopening의 representation theorem                                     | P9/P22 강화     |
| **TC-12** | Equivariant physical response가 orbit quotient 위의 response map을 유도하는 descent theorem                            | 신규            |
| **TC-13** | Morphology row가 기존 response span 밖일 때 physical rank가 증가하는 reopening theorem                                    | PR-255/257 강화 |
| **TC-14** | BiPoSH, pole, parity blocks의 irreducible selection-rule theorem                                                | P23/PR-257 강화 |
| **TC-15** | Depth-memory kernel의 frame-equivariant transport theorem                                                       | P21 강화        |
| **TC-16** | Kinematic orbit type (\to) response-equivalence type (\to) open-set anisotropy type quotient                   | PR-258 강화     |
| **TC-17** | Algebraic, constraint-surface, local-dynamical, global-dynamical realization ladder                            | T3/KE/BV 통합   |
| **TC-18** | LRS III/KS curvature–shear slaving 및 higher-order response reopening                                           | OMK-REOPEN 보존 |
| **TC-19** | Extended-state FLRW forward implication: 모든 anisotropic irreps의 zero state                                     | P6/EGS 계승     |
| **TC-20** | Native Bianchi transfer가 kinematic orbit을 observable morphology orbit으로 보내는 future response-functor theorem    | Track II      |

TC-03, TC-05와 TC-16이 성립하면 “Bianchi label을 맞히는 classifier”와 다른, **coordinate-free kinematic anisotropy taxonomy**를 제시할 수 있다.

---

## 4.2 기둥 II — 통계학·실제 데이터 분석

| ID        | 명제·결과                                                                                 | 상태                      |
| --------- | ------------------------------------------------------------------------------------- | ----------------------- |
| **ST-01** | Functional-indexed state pushforward (X_\phi=\phi(X))의 type/equivariance preservation | 신규                      |
| **ST-02** | Vector/tensor functional의 covariance propagation과 null-space retention                | P34 강화                  |
| **ST-03** | Convex identified set의 support-function completeness                                  | 신규                      |
| **ST-04** | Gauge–support duality와 anchor inclusion iff theorem                                   | 신규 핵심                   |
| **ST-05** | Set-valued (Q)와 directional (F)의 exact image theorem                                  | 신규                      |
| **ST-06** | Invertible anchor normalizer가 response rank를 바꾸지 않는 theorem                           | PR-254/255 정식화          |
| **ST-07** | Anchored Gram/Fisher spectrum의 eigenvalue·eigendirection interpretation               | PR-255 강화               |
| **ST-08** | Same-joint-covariance Schur morphology information theorem                            | PR-255 강화               |
| **ST-09** | Generic orbit stratum에서 invariant estimator의 simultaneous confidence region           | 신규                      |
| **ST-10** | Eigenvalue-degenerate stratum의 tangent-cone/second-order inference                    | 신규                      |
| **ST-11** | Conditional exceedance surface의 null/coverage validity                                | 신규                      |
| **ST-12** | Partially identified conditioning에서 lower–upper exceedance envelope theorem           | 신규                      |
| **ST-13** | Vector/tensor finite-cover e-value merge와 anytime validity                            | P19/P29 강화              |
| **ST-14** | Estimated covariance를 갖는 vector/tensor statistic의 Hotelling/(t) inference             | T4p 강화                  |
| **ST-15** | Joint depth/mask path의 simultaneous confidence band                                   | 신규                      |
| **ST-16** | Set-valued (G_F)의 shared-nuisance fractional/support propagation                      | T2G 확장                  |
| **ST-17** | Local/global principal angle과 minimum singular value에 따른 error/abstention bound       | PR-256 강화               |
| **ST-18** | Open-set response-class classifier의 finite-library consistency와 unknown rejection     | PR-258 강화               |
| **ST-19** | Minimal reopening observable의 E-optimal/semidefinite design theorem                   | 신규 positive             |
| **ST-20** | MES anchor stress와 nonlinear model gain의 논리적·통계적 독립성                                  | PR-255 phase diagram 강화 |
| **ST-21** | Scalar compression은 response rank를 증가시킬 수 없다는 data-processing theorem 및 equality 조건   | 신규                      |
| **ST-22** | Cross-survey dependence를 포함한 joint response/identified-set fusion                     | 신규                      |
| **ST-23** | Null-orbit direction posterior movement의 prior-exposure decomposition                 | P28 강화                  |
| **ST-24** | Nested ZoA/mask path의 covariance-aware morphology change-point theorem                | 신규                      |
| **ST-25** | 새 state/orbit formalism에서 legacy (x_C,Q,F,\Pi,G_F) 값을 정확히 재생하는 compatibility theorem  | migration               |

support-function 기반 partial-identification inference는 이미 identified set 전체를 다루는 통계적 기반을 제공한다. 다만 flat face, boundary와 degeneracy에서는 regularized support estimator나 directionally differentiable functional용 inference가 필요하다. ([[arXiv](https://arxiv.org/abs/1904.00111)][4])

---

# 5. 기존 proof의 migration

기존 proof를 삭제하거나 번호를 재사용하면 안 된다.

## 그대로 보존·강화

* P6–P14: theory pillar로 이동
* P8–P10, P17–P25, P28–P30: statistics/response pillar로 이동
* T2G: ST-16의 scalar special case
* T4p/T5p: ST-14와 endpoint special-case proof
* KE-FRAME, KE-OBS, KE-DYN, BV-DYN, OMK-REOPEN: TC-17/18
* MES-REFREEZE/MES-MESB-TRACE: TC-08의 source-specific branches

## 의미를 변경해 이관

* P1: `GaussBudgetProjection` compatibility theorem
* P2: legacy scalar semantics에서 functional-family semantics로 supersede
* P3/P27: MES ceiling과 response route를 TC-08/ST-06으로 분리
* P15: scalar quadrupole filling을 one-dimensional closure example로 강등
* P18: hard-coded rank-2 design에서 general anchored response theorem으로 이동
* P23–P25: matrix-valued morphology information으로 승격
* P33: point-identified scalar (G_F) special case
* P34: ST-02의 scalar linear-functional corollary

## 역사적 반례로 유지

현재 registry가 이미 올바르게 처리하는 다음 항목은 복구하지 않는다.

* P26: superseded
* P31: superseded
* P35: superseded
* P36: retracted
* T2p: retracted

`migrate_theorem_registry_v2.py`는 기존 registry의 모든 ID가 새 두 기둥 중 하나 또는 `HISTORICAL_COUNTEREXAMPLE`에 정확히 한 번 배정되었는지 검사해야 한다. 누락 ID가 하나라도 있으면 build를 실패시킨다.

---

# 6. 코드 구조

```text
htt/src/common/
  kinematic_state_v2.py
  state_functionals.py
  orbit_catalogue_v3.py
  anchor_utilization.py
  conditional_exceedance.py
  depth_path_geometry.py
  theorem_registry_v2.py

htt/mio/formalism/
  state_diagnostics.py
  support_utilization.py
  conditional_exceedance.py
  depth_morphology.py

htt/htt/htt/statistics/
  orbit_inference.py
  posterior_functionals.py
  source_conditioned_surfaces.py
  depth_path_inference.py

htt/obsstat/
  tensor_feature_packets.py
  lowell_orbit_features.py
  cf4_morphology_path.py
  weak_lensing_spin2_features.py
```

## 핵심 public types

```python
CongruenceKinematics
VelocityFrameBundle
GeometryState
JointAnisotropyState

StateFunctionalSpec
StateFunctionalValue

OrbitCatalogueV3Spec
OrbitStratumReport

AnchorCoordinateReport
SupportUtilizationProfile

ConditionalExceedanceSurface
DepthMorphologyPath

TheoreticalProofRecord
StatisticalProofRecord
```

기존 `DepartureState`, `SummaryDepartureState`, `ComponentBreakdown`은 migration adapter로 유지한다.

---

# 7. 실제 PR DAG

현재 internal sequence가 PR-258까지 왔으므로 다음과 같이 이어가는 게 자연스럽다.

| PR         | 핵심 작업                                                 | 엄격한 PASS                                                                          | 즉시 FAIL                                                |
| ---------- | ----------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------ |
| **PR-259** | Theorem Registry v2와 전 ID migration                   | 기존 ID 100% 매핑, proof grade·pillar·consumer 포함                                     | orphan ID 또는 simulation을 proof로 계상                     |
| **PR-260** | JointAnisotropyState, (A_a), (\beta_{\rm RM/MO}) 통합   | O(3), parity, units, frame round-trip; legacy byte 재현                             | missing (A_a) 또는 (\beta)를 0으로 채움                       |
| **PR-261** | Orbit catalogue v3                                    | Gram–Krylov generator, shear strata, parity, CAS/Jacobian, generic reconstruction | generic separation을 finite fixture만으로 선언               |
| **PR-262** | Functional-indexed (X_\phi) algebra                   | scalar/vector/tensor/orbit output, equivariance, Gauss legacy projection exact    | 모든 output을 float array로 평탄화                            |
| **PR-263** | Vector/set (Q)와 support-profile (F)                   | gauge/support duality, anchor inclusion, active faces, rank invariance            | (F)를 probability나 physical volume로 표현                  |
| **PR-264** | Conditional (\Pi) surface                             | sampling law typing, lower/upper envelopes, simultaneous calibration              | unidentified conditioning에 point (\Pi) 출력              |
| **PR-265** | (G_F) depth/mask path                                 | cross-depth covariance, transport, zero-safe contrasts, ZoA path                  | bins/masks를 독립 표본으로 처리                                 |
| **PR-266** | Theory/MathPhys proof pillar                          | TC-01–20 statement, assumptions, analytic/CAS artifacts                           | numeric fit을 exact theorem으로 승격                        |
| **PR-267** | Statistics/Data proof pillar                          | ST-01–25, finite/asymptotic 구분, coverage battery                                  | retained DGP에서 undercoverage 또는 silent optimizer fail  |
| **PR-268** | 세 과학축 blind benchmark                                 | scalar vs state vs orbit vs full method의 rank·coverage·confusion 비교               | 새 방법이 false source/type ID를 줄이지 못함                     |
| **PR-269** | 기존 데이터 pilot                                          | Planck/CF4/HSC/KiDS에서 joint covariance와 nuisance refit                            | DESI partial data 또는 same-data likelihood double count |
| **PR-270** | proof atlas·internal report·external replication pack | clean checkout에서 theorem list, figures, artifacts 재생성                             | manual theorem list가 registry와 불일치                     |

---

# 8. 세 과학축에서의 positive 결과

## 8.1 Global tilt versus local boost

목표는 단순 no-go가 아니라 다음 quantity를 계산하는 것이다.

[
\psi_{\min}
===========

\text{smallest principal angle}
\left(
T\mathcal M_{\rm local},
T\mathcal M_{\rm global}
\right),
]

[
s_{\min}
========

\sigma_{\min}^{+}
\left[
R_{\rm local},R_{\rm global}
\right].
]

출력은

```text
NON_IDENTIFIED
SUM_ONLY
WEAKLY_IDENTIFIED
SEPARABLE_CANDIDATE
```

로 분리한다. 현재 PR-256에는 `WEAKLY_IDENTIFIED`가 빠져 있어 full-rank지만 작은 principal angle인 경우가 `SUM_ONLY`와 혼동될 수 있다.

CMB observer motion은 Doppler와 aberration이라는 유사하지만 비동일한 off-diagonal coupling을 만들며, intrinsic dipole도 별도 coupling을 만든다. 이를 독립 측정해야 local/intrinsic degeneracy를 깰 수 있다는 기존 연구와 정확히 연결된다. ([[arXiv](https://arxiv.org/abs/2107.10846)][5])

remote dipole/quadrupole fields는 서로 다른 spacetime locations에서 보이는 CMB multipoles를 표본화하므로, local endpoint boost와 coherent global source를 구분하는 추가 response row가 될 수 있다. ([[arXiv](https://arxiv.org/abs/1806.01290?utm_source=chatgpt.com)][6])

새 방법론의 positive output은 다음이다.

> 어떤 redshift, remote-field, polarization 또는 velocity observable을 추가해야 (\psi_{\min})과 (s_{\min})이 사전 검출 기준을 넘어서는가.

즉 source detection 이전에 **minimal discrimination design**을 계산한다.

---

## 8.2 Low-(\ell) morphology

PR-257은 이미 동일 (C_\ell)과 동일 anchor stress를 유지하면서 phase, orientation, parity만 바꾸는 matched counterpair를 정의한다.

다음 단계는 representation별로

[
F_{\mathcal A}^{\rm diag},
\qquad
F_{\mathcal A}^{\rm pole},
\qquad
F_{\mathcal A}^{\rm BiPoSH},
\qquad
F_{\mathcal A}^{\rm TEB}
]

를 계산하고,

[
\Delta r,
\qquad
\Delta\lambda_i,
\qquad
\Delta W(\mathcal I),
\qquad
\Delta L_{\rm heldout}
]

를 비교하는 것이다.

BiPoSH는 일반 spherical covariance의 non-statistically-isotropic sector를 표현하며 Doppler boost, weak lensing, beam, mask와 cosmological anisotropy를 서로 다른 covariance pattern으로 나타낼 수 있다. ([[arXiv](https://arxiv.org/abs/1509.07137)][7])

positive claim은

> “BiPoSH가 더 anomalous하다”

가 아니라

> “BiPoSH/TEB block이 MES-normalized kinematic state의 특정 null eigendirection을 재현 가능하게 열었다”

가 되어야 한다.

---

## 8.3 Anisotropy type classification

최종 type은 세 단계다.

[
\mathsf K:
\text{kinematic orbit type},
]

[
\mathsf M:
\text{observable morphology-response class},
]

[
\mathsf G:
\text{geometric/dynamical type}.
]

현재 pre-native 단계에서는

[
\mathsf K\times\mathsf M
]

까지 간다.

출력 예시는 다음과 같다.

```text
KINEMATIC STRATUM
  triaxial shear
  nonzero axial sector
  generic beta_RM support
  beta_MO partially aligned
  acceleration unresolved

MORPHOLOGY CLASS
  low-ell parity-odd response present
  BiPoSH class R7/R9 equivalent
  stable under registered mask family

SOURCE STATUS
  local/global weakly identified
  remote-dipole row is minimal reopening observable

OPEN-SET STATUS
  two compatible response classes
  one unknown-source alternative
```

PR-258의 response-equivalence, unknown rejection, minimal reopening observable machinery는 바로 이 구조의 (\mathsf M) layer다.

weak-lensing E/B와 off-diagonal correlations가 anisotropic expansion의 eigendirections를 복원할 수 있다는 이론 결과는 향후 HSC/KiDS spin-2 block이 (\mathsf M) layer를 실제로 넓힐 수 있음을 보여준다. ([[arXiv](https://arxiv.org/abs/1503.01127?utm_source=chatgpt.com)][8])

---

# 9. 반드시 넣어야 할 kill criteria

1. **Orbit v3가 generic test에서 두 비동일 orbit을 동일하게 매핑한다.**
   `complete classifier` claim을 금지하고 degree-bounded catalogue로 유지한다.

2. **(A_a) 또는 (\beta_{\rm RM/MO}) missing branch가 0으로 직렬화된다.**
   전체 PR을 fail시킨다.

3. **Normalizer 선택만 바꿨는데 response rank가 변한다.**
   구현 오류다. Invertible normalization은 rank를 만들 수 없다.

4. **Support profile을 도입해도 scalar (x_C) 대비 held-out source/type confusion이 줄지 않는다.**
   방법론의 empirical significance claim을 보류한다.

5. **MES, Fisher, template normalizer를 바꿀 때 source conclusion이 지속적으로 뒤집힌다.**
   MES는 primary가 아니라 `ONE_ANCHOR_AMONG_FAMILY`로 유지한다.

6. **Conditional (\Pi)의 identified envelope가 대부분 ([0,1])이다.**
   해당 data/response는 source inference에 실질 정보가 없다는 결과로 보고한다.

7. **Mask/ZoA path가 physical depth path보다 큰 variation을 만든다.**
   global coherence claim을 금지한다.

8. **Local/global tangent spaces가 overlapping하거나 (s_{\min})이 사전 threshold 이하이다.**
   `WEAKLY_IDENTIFIED` 또는 `SUM_ONLY`가 유일한 출력이다.

9. **Orbit-invariant confidence procedure가 eigenvalue-degenerate strata에서 undercoverage한다.**
   standard delta method를 금지하고 tangent-cone/second-order procedure로 전환한다.

10. **Registry의 proof statement와 executable contract가 다르다.**
    모든 consumer를 invalidate한다.

---

# 최종 중심 주장

새 formalism의 핵심 문장은 다음처럼 세울 수 있다.

> **The fundamental inferential object is not a scalar FLRW-defect score but a frame- and scale-typed kinematic state modulo spatial rotations. MES supplies an amplitude anchor on selected irreducible blocks; orbit invariants retain anisotropy type; response geometry determines which orbit directions are observable; and support-function inference reports the resulting set-valued, depth-dependent classification.**

한국어로는 다음이다.

> **기본 물체는 하나의 (x_C)가 아니라 회전군의 작용을 받는 kinematic tensor/vector state다. MES는 그 state의 일부 block에 amplitude anchor를 제공하고, orbit invariant는 anisotropy type을 보존하며, response geometry는 어떤 방향이 관측 가능한지를 결정한다. (Q,\Pi,F,G_F)는 이 state와 identified set 위의 서로 다른 functional로 일반화된다.**

이 체계가 완성되면 기존 scalar formalism은 버려지는 게 아니다.

* (x_C): Gauss-budget support direction
* (Q): anchor coordinate/gauge report
* (F): directional support-utilization profile
* (\Pi): conditional calibrated exceedance surface
* (G_F): depth/mask-dependent orbit path

로 각각 정확한 위치를 갖게 된다.

그리고 가장 중요한 차별점은 “무엇을 못한다”가 아니다. 이 formalism은 실제로 다음을 계산할 수 있다.

* coordinate-free kinematic anisotropy types
* morphology가 새 physical direction을 여는 정도
* local/global degeneracy를 깨는 최소 observable
* premise anchor가 가장 압박받는 tensor direction
* depth와 mask에 따른 anisotropy orbit의 이동
* known class, equivalence class, unknown class 사이의 calibrated open-set 분류

이 다섯 가지가 이론우주론·수리물리 기둥과 실제 데이터 통계 기둥을 하나의 연구 프로그램으로 묶는 positive scientific core다.

[1]: https://link.springer.com/article/10.1007/s42558-024-00056-1 "https://link.springer.com/article/10.1007/s42558-024-00056-1"
[2]: https://arxiv.org/abs/1605.09561 "https://arxiv.org/abs/1605.09561"
[3]: https://arxiv.org/abs/1212.3267 "https://arxiv.org/abs/1212.3267"
[4]: https://arxiv.org/abs/1904.00111 "https://arxiv.org/abs/1904.00111"
[5]: https://arxiv.org/abs/2107.10846 "https://arxiv.org/abs/2107.10846"
[6]: https://arxiv.org/abs/1806.01290?utm_source=chatgpt.com "Simulated reconstruction of the remote dipole field using the kinetic Sunyaev Zel'dovich effect"
[7]: https://arxiv.org/abs/1509.07137 "https://arxiv.org/abs/1509.07137"
[8]: https://arxiv.org/abs/1503.01127?utm_source=chatgpt.com "Weak-lensing $B$-modes as a probe of the isotropy of the universe"
