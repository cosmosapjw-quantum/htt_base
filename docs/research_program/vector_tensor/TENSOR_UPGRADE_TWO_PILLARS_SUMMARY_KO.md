# 텐서 업그레이드 + 두 기둥 증명 레지스트리 — 한국어 핵심 요약

**패키지:** `STAT_FOUNDATIONS_TENSOR_UPGRADE_20260730.md` (업그레이드 명세) · `PROOF_REGISTRY_TWO_PILLARS_20260730.md` + `proof_registry_two_pillars.yaml` (증명 레지스트리, 58항목) · `tensor_foundations_oracle.py` (TF-01~TF-12, 전부 PASS, ≈12초)
**감사 기준:** HEAD `e7c2064` (PR-253~258 전부 merged; `machine_readable/pr_backlog.yaml`의 `PENDING` activation state는 여섯 카드 모두에 대해 stale) · **작성:** 2026-07-30

---

## 0. 이번 작업의 한 줄

첨부 검토노트의 진단이 맞다. 병목은 high-ℓ도 아니고 "코드가 아직 scalar"도 아니다. 병목은 **component-native한 머리(state)와 component-native한 꼬리(classification) 사이에 스칼라 허리(statistics)가 끼어 있는 것**, 그리고 `(σ,β)` orbit algebra가 `(σ, ω, A, β_RM, β_MO)` 전체로 아직 닫히지 않은 것이다. 이번 산출물은 그 허리를 규격화하고, 그 대수를 닫고, 그 결과를 두 기둥 증명 목록으로 정리한다.

## 1. 업그레이드의 정당화는 수사가 아니라 셈이다 ⟦V⟧

`x_C`가 틀린 게 아니다 — signed Gauss–Friedmann budget projection으로서는 정확히 옳고 BC1로 bit-identical 보존된다. 업그레이드의 근거는 **센 숫자**다.

- **TF-06:** **principal stratum(generic isotropy가 유한한 곳)에서** kinematic state의 SO(3) 불변량 자유도는 정확히 `dim − 3` = **9** (`σ,ω,β,ΔΩ_k`), 가속도를 넣으면 **12**, velocity frame을 쪼개면 **15**. `x_C`는 그중 **1개**를 분해한다. Stratum 조건은 장식이 아니다 — 벡터 하나만 있으면 isotropy가 `U(1)`이라 불변량은 0이 아니라 1이고, 오라클이 그 반례를 들고 다닌다. 그리고 이것은 **불변량 공간의 방향 수**이지 **데이터로부터의 식별 가능성**이 아니다(후자는 II-1.2/II-4.4의 별도 문제다).
- **TF-07:** Gauss budget은 네 불변량 `{tr σ², ω², β², ΔΩ_k}`를 **경유해서만**(factors through) 정의된다. 따라서 나머지 2차 불변량인 **helicity `β·ω` 방향의 도함수가 정확히 0**이고, 그 공통 level set에 횡단하는 모든 방향에서도 0이다. 등급(degree) 주장이 아니라 인수분해 주장인 이유는 repo의 tilt 항이 `Ω_tilt = (1+w)Ω_m sinh²β` — `β·β`의 우함수이지 단항식 `β²`가 아니므로 budget은 더 높은 짝수 거듭제곱에도 의존한다. 즉 "degree ≥ 3에서 항등적으로 0"은 **거짓**이고, 살아남는 참인 진술이 인수분해다. `x_C`의 맹목은 추정기 결함이 아니라 **제약식 자체의 구조**다. 검증: budget gradient가 네 불변량 gradient의 span 안에 있고(상대잔차 `9.5e-11`) helicity gradient는 밖에 있음(횡단 성분 ≥ 0.38), 그리고 네 budget 불변량과 `x_C`를 고정한 채 helicity만 움직이는 명시적 witness.
- 이미 repo에 있는 경험적 확증: PR-257 held-out 벤치마크에서 **`x_C`는 rank 0으로 전 draw에서 abstain**, 비스칼라 표현은 loss가 0.105~0.301 감소.

즉 "정보를 더 본다"가 아니라 **`x_C`가 9개 불변량 방향 중 정확히 1개만 분해한다**는 정량 명제다(나머지 8개가 데이터로 얼마나 회수되는지는 response rank와 부분식별이 정하는 별개 문제다). 그리고 budget은 네 불변량을 경유하므로 morphology와 나란히 보고해도 이중계산이 아니다(B-1).

## 2. 등록된 비-generic 반례를 닫았다 ⟦V⟧

PR-257은 12개 다항식을 동결하고 `generic_orbit_separation_status`를 정직하게 `UNPROVEN`으로 못박으면서 반례를 등록했다: `β=0`, `σ=diag(1,2,−3)`에서 `ω`와 `−ω`가 12개 값이 전부 같다.

**그 반례를 해소하는 생성원은 axial Krylov 행렬식 `K_ω = det[ω, σω, σ²ω]`이다.**

- **TF-01:** `ω`가 axial이므로 세 열이 각각 `det(R)`를 먹고 행렬식이 넷째를 먹어 `det(R)⁴ = 1` → **`K_ω`는 진짜 O(3) 스칼라**(polar 짝 `K_β`는 pseudoscalar). 그리고 `ω → −ω`에서 홀수.
- **TF-02:** 등록된 반례에서 `K_ω = ±120`으로 분리된다. `diag(1,2,−3)`의 SO(3) stabilizer는 commutant로부터 **계산해서**(주장이 아니라) Klein 4군임을 확인했고 그중 `ω↦−ω`인 원소가 없으므로 **두 상태는 실제로 다른 궤도**다. 오라클은 후보 생성원이 실제로 SO(3) 불변량인지도 분리를 허용하기 **전에** 검사한다(그렇지 않으면 `ω`의 임의의 홀함수가 "분리"해버린다).
- **범위(중요):** 등록된 반례는 `β=0`이라 §3.5의 principal stratum **바깥**에 있다. residual gauge를 전수 확인하면 generic `β`에서는 v2 12개가 이미 SO(3) 궤도를 분리하고, `K_ω`를 더해도 Jacobian rank는 오르지 않는다(syzygy상 당연). 즉 `K_ω`는 **generic 생성원의 누락이 아니라**, 벡터가 `σ`에 대해 cyclic하지 못한 곳에서 부호 1비트를 공급한다. 따라서 정확한 주장은 "**등록된 비-generic 반례를 닫았다**"이고, `generic_orbit_separation_status`와 `degree_completeness_status`는 **`UNPROVEN` 그대로**다(같은 전수 확인은 generic 분리 추측 I-2.7의 긍정적 방증이기는 하다).
- **TF-03:** `K_v² = det Gram`이고 Cayley–Hamilton(TF-04)으로 그 Gram은 짝수 불변량들의 다항식이다 → **Krylov 행렬식의 크기는 새 정보가 아니고, 새 내용은 부호 1비트(shear 고유틀에 대한 손대칭)뿐**이다. 이 1비트가 §4의 정확검정 대상이다.
- **TF-05:** `J_σ = √6 I₃/I₂^{3/2} ∈ [−1,1]`, `Δ_σ = ½I₂³ − 3I₃² = ½I₂³(1−J²)`이고 `Δ_σ`는 특성다항식의 판별식과 정확히 일치. `J=±1`은 축대칭, `J=0`은 `(λ,−λ,0)`. → **`tr σ³`는 "더 큰 진폭"이 아니라 진폭 없는 anisotropy TYPE 좌표**이며, Bianchi family 언급 없이 shear morphology를 명명할 수 있다.

카탈로그 v3는 손으로 나열하지 않는다: **Gram–Krylov 생성 규칙** + parity는 `(#ω + #ε)` 홀짝으로 기계적 + **Jacobian rank 수용검사**(TF-06의 9/12/15를 못 맞추면 parity 검사 전에 기각).

## 3. 스칼라 → functional-indexed family

```
x_φ = φ[𝒦] ,  Q_φ = N_φ/U_φ ,  F_φ ,  Π_φ(c | η) ,  G_{F,φ}
```
`x_C`는 `φ = ⟨c,·⟩` 인스턴스 하나다(BC1 보존, BC2로 승격 금지). 모든 functional은 **functional identity**를 들고 다닌다: `functional_id, source_state_id, output_rank, tensor_degree, O3_parity, frame, congruence, epoch_window, averaging_scale, normalization, anchor_id, perturbative_order`.

이 중 세 개가 실제로 일을 한다. `tensor_degree`는 TF-07을 기계화한다(degree ≥ 3인데 budget 기여를 주장하면 생성 시점에 거부). `O3_parity`는 어떤 통계가 정의 가능한지를 결정한다. `anchor_id`는 기존 channel-key 게이트다.

**적격성 규칙 두 개(§2.3 표):** ① **signed functional에 filling fraction 금지** — `tr σ³`에 occupancy를 붙이면 `defect_negative` 병리가 새 좌표에서 재생산된다; 올바른 짝은 signed `Q_φ` + `Π_φ`. ② **channel key가 일치하는 anchor 없이 occupancy 금지**.

**벡터 → 스칼라 붕괴는 임의적이지 않다 ⟦V⟧ TF-08:** product body의 Minkowski gauge는 **per-sector saturation의 최댓값** — `ρ = max_j s_j`, `E = max(ρ−1,0)`. 즉 레거시의 signed sum(shear와 vorticity가 상쇄)이 아니라 **L^∞ 결합**이고, 상쇄가 구조적으로 불가능하며 다중 sector 초과는 **최악의 sector에 의해서만** 반증된다. (gauge 정의를 bisection으로 직접 평가해 확인 — 최댓값이라고 가정하지 않았다.)

## 4. 새로 가능해지는 통계분석 두 가지 — 둘 다 "정확한" 검정

### 4.1 Parity 부호 검정 (TF-09) — 공분산 모델도, mock도 필요 없음

반사-홀수 불변량 `ψ`(즉 `K_β`, `β·ω`, `β·σω`, `β·σ²ω`)에 대해, **(H1)** 분석 기하(마스크·가중·픽셀화)를 함께 고정하는 반사 `P`에 대해 귀무법칙이 불변이고, **(H2)** 추정기 자체가 정확히 `P`-equivariant이며(마스크 deconvolution·정규화·가중 포함), **(H3)** `P(ψ̂=0)=0`이면: `ψ̂`의 법칙은 0에 대해 대칭이다. 따라서

```
sign(ψ̂) ~ Bernoulli(1/2)  정확히,   그리고  sign(ψ̂) ⫫ |ψ̂| .
```

왜 중요한가: **은하면 반사는 위도대칭 마스크 `|b|>b_cut`를 고정하고 parity-대칭 잡음/전경 분산모형도 고정한다.** 즉 (H1)–(H3) 하에서 이 정확성은 프로그램의 모든 짝수 통계량을 null ensemble에 의존하게 만드는 실패 모드들(mask coupling, 비등방 잡음, 공분산 척도 오설정)을 **그대로 통과**한다. 오라클 대조: 반사대칭인 세 null에서 `P(ψ̂>0) = 0.4988 / 0.4980 / 0.5022`로 유지되는 동안, 같은 상태의 짝수 통계량은 **평균은 대칭성 때문에 0으로 고정된 채 척도(sd)가 3.18 → 116.0으로 36.5배** 움직인다 — null-ensemble 보정이 깨지는 곳은 중심이 아니라 **꼬리**다.

같이 실어야 하는 규율 세 가지. **(a) 실전에서 구속력 있는 가정은 (H1)이 아니라 (H2)다** — 실제 selection function(깊이 대 적위)과 point-source 구멍은 `b → −b` 대칭이 아니다. 위반은 가정으로 덮지 말고 **선언된 위반**으로 들고 가야 하고, 정직한 버전은 자기 추정기의 equivariance 감사를 동반한다. **(b) (H3)는 명명된 stratum에서 실제로 깨진다** — 축대칭 궤적 `Δ_σ = 0`에서 Krylov 사슬이 rank-deficient가 되어 `K_β`가 항등적으로 0이고(⟦V⟧ max `|K_β| = 2.1e-14`), `MISSING_COMPONENT` sector도 마찬가지다. 0에 원자가 있으면 Bernoulli(1/2)도 독립성도 무너지므로 거기서는 **부호를 보고하지 말고 기권**해야 한다. **(c) rung 간 부호는 독립이 아니다** — 부호⫫크기는 **하나의** 통계량에 대한 진술이고, 중첩 마스크 rung은 §4.2가 증명하듯 filtration을 이루어 최대로 종속이다. 따라서 **이항 pooling은 무효**이고 결합은 임의 종속 하에서 타당한 arithmetic-mean e-value merge를 거쳐야 한다.

정직한 범위: TF-03이 식별한 sector당 1비트만 검정한다. 비대칭이 검출되면 **진짜 chirality 또는 parity-비대칭 계통오차**로 국소화되는데, 이 이분법 자체가 어떤 짝수 통계량보다 날카롭고 둘째 갈래는 구체적으로 점검 가능한 파이프라인 결함이다.

### 4.2 중첩 마스크 경로 = 역마팅게일 (TF-11)

중첩 마스크 사다리는 감소 filtration을 만든다. **각 rung이 "동일한 전천 타깃"의 조건부 기댓값을 보고할 때에만** 역마팅게일이 되고, Doob 부등식이 경로 전체를 공짜로 calibrate한다:
```
P( max_j |M_j| ≥ λ·sd(M_full) ) ≤ 1/λ² .
```
닫아야 할 설계 함정이 구체적이다: **각 cut을 독립적으로 적합하고 rung마다 자기 타깃으로 재정규화하면** 마팅게일 성질이 파괴되고 경험적 `P(sup ≥ 3) = 0.60`이 bound `0.111`을 크게 위반한다. 즉 ZoA morphology path는 "따로 적합한 컷들의 그림"이 아니라 **제대로 만들면 calibration이 공짜이고 잘못 만들면 없는** 순차적 객체다.

## 5. 왜 기존 anomaly 통계가 아니라 이것인가 — 최적성 논거 (II-5.1/5.2)

*(아래 셋은 모두 `PROPOSED` 상태이며, 의존 사슬은 I-2.8(OPEN) → I-2.7(PROPOSED, 4축 CAS 필요) → II-5.1/5.2/5.3이다. 카탈로그가 최대불변량이라는 전제는 I-2.7의 generic 분리가 증명되어야 확정된다.)*

- **최대불변량(maximal invariant):** 귀무와 대립이 모두 군 `G`에 대해 불변인 검정 문제에서 **모든 `G`-불변 검정통계량은 최대불변량의 함수**다(`G`는 표본공간에 작용하고 모수공간에 작용을 유도해야 한다). I-2.7이 증명되면 principal stratum에서 완성된 카탈로그가 SO(3)의 최대불변량이 되고 → **궤도공간 축약은 편의적 압축이 아니라 정준 축약이고, 잃는 것이 없다.** 등록된 외부 방향(dipole 축, 은하면)이 있으면 `G`는 그 stabilizer가 되고 최대불변량은 카탈로그 + 상대배향 좌표 → **alignment 통계가 카탈로그 "옆"이 아니라 "안"에 있어야 하는 이유**가 도출된다.
- **Hunt–Stein:** SO(3)는 컴팩트 → amenable → **최선의 불변 검정은 전체 검정 중 minimax**(단서 둘: 대립가설이 0에서 떨어져 있어야 minimax 진술이 공허하지 않고, "최선의 불변 검정"은 UMPI 검정의 존재를 전제하는데 이 문서는 그것을 구성하지 않는다). 손으로 고른 low-ℓ anomaly 통계량은 같은 함수류의 임의 원소일 뿐 최적성이 없다.
- **다중성 폐쇄:** 최대불변량이 유한차원(9/12/15)이고 카탈로그가 사전등록이므로 look-elsewhere가 **불명확한 족에 대한 추정**에서 **완결된 족에 대한 부기**로 바뀐다 — 보정을 잘하는 게 아니라 설계로 푸는 것.

## 6. 검토노트의 7개 우선순위 — 처리 현황

1. **state 통합** → 3층 구조 `CongruenceKinematics`(σ, ω, **A**) / `VelocityFrameBundle`(β_RO,RM,MO) / `JointAnisotropyState`(참조 조합). 거대 dataclass 확장이 아닌 이유는 물리적이다: σ/ω/A는 **선택한 congruence의 kinematics**이고 β_MO는 **프레임 사이의 관계**다. `beta_semantic_role` 필수 — 못 채우면 fail-closed(현재의 암묵적 동일시 차단). `A/(cΘ)` vs `A/Θ`는 `acceleration_normalization` enum으로 타입화하고 channel key에 포함.
2. **카탈로그 v2 → v3** → §2. Gram–Krylov 생성규칙 + Jacobian-rank 수용 + `K_ω` 완성 + stratification + 전용 4축 CAS 계약.
3. **full-a_lm counterpair** → 방향전환이 아니라 한 줄 확장: `(σ,ω,β) → (σ,ω,A,β_RM,β_MO)`, 단 acceleration 구현이 source-lock되기 전에는 0이 아니라 `MISSING_COMPONENT`. high-ℓ/ACT는 후속 auxiliary이지 게이트가 아님(노트에 동의).
4. **조건부 exceedance** → `ConditionalExceedanceSurface` 계약: `sampling_law`(5종) + `conditioning_source`(5종) 필수, 점식별 실패 시 단일 `Π` 금지하고 **envelope [Π̲, Π̄]** 출력. 식별집합이 convex **이고 유계**(활성 recession 방향 없음)이며 조건부 사상이 **단조**이거나 `Π̄`에 quasi-convex **또한 `Π̲`에 quasi-concave**일 때만 **꼭짓점 열거로 유한 계산**(기존 vertex/recession 표현 재사용), 아니면 `OPTIMIZER_REQUIRED`로 거부. Bauer 최대원리는 quasi-convex 함수의 **상한**만 극점에 놓고 **하한**은 일반적으로 내부다(`Π = η²` on `conv{−1,+1}`: 참 하한 0인데 꼭짓점 열거는 1) — 그리고 `Π̲`가 보수적 끝점이므로 quasi-convex만 가정하면 **하필 중요한 방향에서** 틀린다.
5. **PR-256 status 정제** ⟦V⟧ TF-10 → dipole만이면 rank 3/6 `NON_IDENTIFIED`; boost-only 채널을 넣으면 rank 6. **단 두 채널은 차수가 다르다:** aberration `ℓ↔ℓ+1`은 진짜 `O(β)` 선형 채널이라 선형 rank를 채우지만, kinematic quadrupole은 `O(β²)`이고(repo가 `frame_typed_algebra.py`에서 명시적으로 타입) `β=0` 주변에서는 Jacobian이 0이라 선형 rank에 기여하지 않는다 — fiducial `β_MO ≠ 0` 주변에서 상대진폭 `O(β) ≈ 10⁻³`로 들어오므로 이미 `WEAKLY_IDENTIFIED` 영역이다. 즉 quadrupole은 과결정 점검이지 둘째 선형 채널이 아니다. 그 채널이 약해질 때 **rank는 6인데 최소 principal angle이 0.704 → 0.001 rad**로 붕괴 → 이건 `SUM_ONLY`가 아니라 **`WEAKLY_IDENTIFIED`**(이미 선언돼 있고 호출처 0인 dead code — 정의 자유). 게이트는 각 하나가 아니라 `(ψ_min, s_min, κ, held-out wrong-source rate)`. **긍정적 절반:** boost sector가 과결정되므로 global tilt는 차감 관례로 제거되는 게 아니라 **잔차로 식별**된다(축 (a)의 식별 정리). 선형 식별은 aberration이 담당한다.
6. **ZoA morphology path** → §4.2의 역마팅게일 객체 + nested mask 간 joint covariance. 마스크 변화가 불연속이므로 `∂/∂b_c` 언어 대신 유한 경로 대비 + mock-calibrated change point로 시작(노트 동의).
7. **PR-258 open-set fusion** → `AnisotropyTypeReport`(kinematic stratum / orbit invariant intervals / parity class / shear multiplicity / vector support pattern / local-global status / compatible response classes / ZoA stability / low-ℓ morphology / **uncovered_directions** / assumptions). `uncovered_directions`는 장식이 아니라 등록된 anchored response의 영공간으로 **계산 가능**하다.

부수 정리: 정본 표기는 **`G_F`**다(`F_G`는 Python 식별자로는 0회 등장하고 `docs/ver2_upgrade/` 파일명 토큰으로만 잔존 — 코드에 재도입 금지). `MES amplitude anchor ≠ tensor morphology classifier` 방화벽은 B-1로 정리했다 — anchor도 budget도 네 2차 불변량을 경유하므로 **scale-free shape 좌표에는 MES-anchored ceiling이 없다**(그래서 null 대비 검정이어야 한다). 단 이는 *권위*에 관한 진술이지 대수적 독립성 진술이 아니다: `|J_σ| ≤ 1`(I-2.4)은 정확한 **대수적** 부등식이므로 `I₂`에 대한 anchor는 `|tr σ³| ≤ I₂^{3/2}/√6`를 유도한다 — 그 부등식은 anchored가 아니라 algebraic이고 축대칭 궤적에서 포화되며, saturation이나 occupancy로 보고해서는 안 된다.

## 7. 가속도 sector — WITHHELD에서 조건부 anchor로 (TF-12)

완전유체의 1+3 운동량 방정식 `(μ+p)A_a = −D_a p`는 4-가속도를 압력기울기에 **종속**시킨다. `c_s² = dp/dμ`와 등록된 무차원 기울기 한계 `|D_a ln μ|/Θ ≤ ε_g`로:

```
A²_max^Euler = (3/2) [ c_s²/(1+w) ]² ε_g²
```

**출처 경고(하중 있음):** `ε_g`는 **repo 어디에도 등록되어 있지 않다.** 오라클 기본값은 `C.eps2`(온도 사중극 `ΔT/T` 진폭)와 수치적으로 같은 **명시적 placeholder**이고 MES 권위를 전혀 갖지 않는다. TF-12가 확립하는 것은 결과의 **형태** — `[c_s²/(1+w)]²` 인자와 `c_s² = 0`에서의 정확한 영점 — 이지 어떤 절대 ceiling 값이 아니다. `ε_g`를 유도·등록하는 것이 PR-259가 가속도 수치를 내보내기 위한 선결 조건이며, `gradient_regularity_registered`는 그때까지 `False`다.

세 가지 긍정적 귀결. **(i) geodesic 전제가 가정이 아니라 유도된 후기 극한이 된다** (`c_s² → 0`) — MES shear/vorticity anchor가 비로소 *이유*를 갖는다. 이 부분은 등록되지 않은 입력에 전혀 의존하지 않는다. **(ii) 현재 `NO_MES_ANCHOR`인 sector가 다른 authority(운동량 제약, MES 아님)로부터 epoch-조건부 ceiling을 얻을 수 있다** — 반박된 non-geodesic MES triple의 부활이 **아니고**, MES `ACCEL` withholding도 건드리지 않는다. **(iii) 가속도 sector는 구성상 congruence-typed다** — 같은 시공간에서 물질 congruence는 `A=0`, 재결합 이전 광자-바리온 congruence는 `A≠0`. 이것이 state가 `congruence`를 들고 다녀야 하는 이유다(B-3). 복사기 slaving factor는 정확히 `1/4`.

## 8. 증명 레지스트리 — 두 기둥, 58항목

**기둥 I (수리물리/이론우주론) 30항목:** 상태·궤도구조, 불변량 대수(완성/syzygy/차수), 제약구조와 budget-morphology 분해, sector closure(가속도·vorticity·tilt), anchor geometry(PA-THM 4종 + 제한된 J1), realizability 사다리.
**기둥 II (실데이터 통계) 24항목:** estimand·식별성, gauge·stress 계산, **정확·분포무관 추론**(신규), 부분식별·coverage, 불변성·최적성·다중성(신규), 판별·분류·기권.
**Bridge 4항목:** 한 기둥에만 넣으면 물리 전제가 통계 보증으로 둔갑하는(또는 그 역) 명제들 — B-1 amplitude/shape 방화벽, B-2 one-way 논리 ↔ 검정 타당성, B-3 congruence typing ↔ 가속도 ceiling, B-4 parity typing ↔ 정확검정.

상태 분포: `ACTIVE` 16 · `ACTIVE_CONDITIONAL` 11 · `ORACLE_VERIFIED` 10 · `PROPOSED` 9 · `PROVEN_CAS4` 8 · `RESTRICTED` 2 · `OPEN` 2. **순수 no-go는 58개 중 4개**(I-2.8 ring completeness, I-4.2 radial-vorticity blindness, I-6.4 tensor realizability, II-1.1 scalar-sector rank-2)이고, 그 넷조차 자기를 제거할 객체를 명시한다.

**J1/J2 처리(선택하신 방식):** 반례를 정확히 보존하고 살아남는 조건부 형태로 재진술. J1 — 등록된 anchor body가 주어지면 gauge는 unit level set의 단조 재매개화까지 유일(선형형은 양의 동차성으로 고정); 반례가 증명한 것은 **anchor body가 반드시 등록되어야 한다**는 것이므로 `MESAnchorSpec` 타이핑이 관료주의가 아니라 하중을 받는다. J2 — 등록된 **결합**법칙 하에서 타당; 주변분포만으로는 비율의 초과확률이 결정되지 않는다(이것이 PR-250의 cross-covariance 의무가 선택사항이 아닌 이유이고, 제 이전 문서의 "no additional modeling" 표현을 반례가 정확히 반박한 지점이다).

**레거시 65항목:** status 편집 필요 **0건**. 대부분 그대로 보존, 5건만 텐서 범위로 재진술(`P1, P2, P18, P20, P34` — 특히 `P18` rank-2는 **scalar-sector** 진술임을 명시), `PR257-NONGENERIC-NONSEPARATION`은 "한계"에서 "영구 회귀 테스트"로 역할 변경.

## 9. 실행 순서

`PR-259` 상태 3층 + 가속도 + convention typing → `PR-260` 카탈로그 v3 + 4축 CAS → `PR-261` functional family + 적격성 표 → `PR-262` 조건부 exceedance + envelope → `PR-263` response-geometry status 정제 → `PR-264` ZoA 역마팅게일 경로 → `PR-265` parity 정확검정 lane + `AnisotropyTypeReport` 융합.

**Chokepoint 경고(명세 §8 표):** `orbit_catalogue_v2._state_payload`의 `state_id`는 12개 float + 8개 메타문자열을 묶으므로 **`_state_payload`를 버전화하지 않으면 저장된 모든 `state_id`가 조용히 무효화**된다. `component_breakdown`의 4-key 정확일치는 유지하고 family는 그 옆에 둔다(안이 아니라). `SourceSeparationGateStatus`는 5-status 정제와 동시에 확장해야 한다.

## 10. 한 문단 결론

이번 업그레이드는 "스칼라가 틀렸으니 벡터로 가자"가 아니라 **세 가지 센 사실** 위에 서 있다: 상태의 불변량 자유도는 9(→12→15)이고 `x_C`는 그중 1을 분해한다(TF-06); 제약식은 degree ≤ 2만 보고 helicity조차 못 본다(TF-07); 그리고 벡터 saturation을 하나의 수로 모으는 방식은 임의적이지 않고 product-ball gauge의 **최댓값**으로 강제된다(TF-08). 여기에 등록된 비-generic 반례를 닫았고(TF-01/02/03 — generic 분리 자체는 여전히 `UNPROVEN`), `tr σ³`를 진폭이 아닌 **타입 좌표**로 승격했으며(TF-05), 가속도 sector의 slaving **형태**를 운동량 제약으로 유도했고(TF-12 — 절대 ceiling은 `ε_g` 등록 전까지 없다), 무엇보다 **공분산 모델도 mock도 필요 없는 정확한 검정 두 개**(parity 부호 TF-09, 마스크 경로 역마팅게일 TF-11)를 텐서 층에서만 가능한 신규 분석으로 확보했다. 최적성 논거(최대불변량 + Hunt–Stein minimax)는 "왜 기존 anomaly 통계가 아니라 이것인가"에 대한 가장 깊은 답이지만 **아직 `PROPOSED`**이고 I-2.7의 generic 분리 증명에 걸려 있다 — 증명되면 궤도공간 축약은 편의가 아니라 **정준이며 minimax 최적**이 된다.
