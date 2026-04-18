# RODAS5P-Centered Partitioned Hybrid for Full CMB Hierarchy — BACKUP BRANCH

> **STATUS — BACKUP / BENCHMARK BRANCH (2026-04-18)**
>
> This plan is **no longer the mainline solver direction**. On 2026-04-18 the
> project selected **pure IMEX-ARK4 (Kennedy–Carpenter)** as the mainline
> reference path for Phase 2+ Bianchi scale-up. This document is retained as
> the **frozen backup / benchmark reference** — implemented only to the
> extent needed for A/B comparison at the IMEX mainline PR-exit gates.
>
> **Authoritative decision**: [`docs/IMEX_DECISION_2026-04-18.md`](IMEX_DECISION_2026-04-18.md)
>
> **Critique record that refined the decision**: [`docs/IMEX_DECISION_CRITIQUE_NOTES.md`](IMEX_DECISION_CRITIQUE_NOTES.md)
>
> **Supporting cost model**: [`project/04_implementation_specs/solver_strategy_5566dof_v2.md`](../project/04_implementation_specs/solver_strategy_5566dof_v2.md)
>
> Do **not** implement sections §8 A1–A9 of this plan as mainline work.
> The ablation-ladder methodology (baseline contract freeze, one-variable-
> per-PR, unified metrics) is solver-neutral and is **borrowed by the IMEX
> PR ladder** (IMEX-00 … IMEX-09 in `IMEX_DECISION_2026-04-18.md` §6).
>
> If future empirical evidence blocks the IMEX mainline, this plan becomes
> the fallback. Otherwise it remains historical reference.

---

## Master Plan, Ablation Ladder, and PR/WBS Execution Packet

**문서 목적**  
이 문서는 지금까지의 논의를 하나의 실행 문서로 재구성한 종합 계획안이다. 목표는 다음 네 가지를 동시에 만족하는 것이다.

1. `full hierarchy`를 유지한 채 `TCA/RFA/URF` 없이도 대형 CMB hierarchy를 안정적으로 적분한다.  
2. `LSODA`식 전역 stiff/nonstiff solver switching을 피하고, `RODAS5P`의 robustness를 유지한다.  
3. 고전적 대칭 `IMEX-RK pair`가 아니라, `RODAS5P-centered partitioned hybrid`를 설계·검증한다.  
4. 무엇이 빨라졌고 무엇이 틀어졌는지 분리할 수 있도록, 보수적인 `ablation study` 체계 위에서 단계별로 승격한다.

---

## 0. Executive decision

## 0.1 최종 채택안

다음 네 축을 **수정 채택**한다.

- `species-first / m-major` ordering 유지
- recombination/visibility는 **ODE 외부 pretabulation** 유지
- `scalar-only prototype`은 버리고 **full-hierarchy from start + progressive activation** 채택
- implicit block은 **Thomson collision 중심의 low-ℓ core**로 제한

## 0.2 핵심 수정점

다음은 명시적으로 **보류 또는 금지**한다.

- full hierarchy라고 해서 **full state 전체를 RODAS5P implicit**에 넣지 않는다.
- Phase 1에서는 **layout compactification**을 하지 않는다.
- 초기 의사결정에 **aggressive speedup claim**을 쓰지 않는다.
- neutrino / mixed block은 explicit 처리하더라도 **full-state error control**에서는 반드시 포함한다.

## 0.3 한 줄 정의

> 이 방법은 고전적 IMEX가 아니라, `RODAS5P`를 외부 주권 적분기로 유지한 채 low-ℓ Thomson core만 linearly implicit, high-ℓ damped tail은 integrating factor, 나머지는 explicit predictor-corrector로 처리하는 **RODAS5P-centered partitioned hybrid**다.

---

## 1. 현재 시스템에 대한 확정 전제

## 1.1 상태벡터 ordering

현재 authoritative ordering은 다음 구조를 따른다.

- top-level: `species-first`
  - metric
  - baryon
  - CDM
  - photon I
  - photon E
  - photon B
  - neutrino Θ
  - neutrino η
- species 내부: `m-major`
- 고정 `m` 내부: `ℓ` contiguous

이 ordering은 hybrid 설계에 유리하다.

- photon/polarization collision tail의 diagonal damping run이 contiguous하게 놓인다.
- block view를 만들기 쉽다.
- `split_state(y) -> (C, M, T)`를 정의하기 좋다.

## 1.2 recombination / visibility

현재 전제는 다음과 같다.

- `x_e`, `T_m`, `κ̇`, `g(η)`, `τ(η)`는 **ODE 내부 진화식이 아니라 외부 precomputed profile**이다.
- ODE는 이들을 `known time-dependent coefficient`로 읽기만 한다.
- 따라서 `κ̇(η)`를 stiff coefficient로 보고 tail damping을 integrating-factor로 빼는 설계가 가능하다.

이건 이번 hybrid 설계에 매우 중요하다. 만약 future anisotropic recombination이 들어오면, 그때는 이 분리가 깨질 수 있으므로 해당 block을 다시 implicit 영역에 편입해야 한다.

## 1.3 full hierarchy from start + progressive activation

별도 scalar-only 분기를 새로 만드는 건 비추천이다. 이유는 다음과 같다.

- `Θ_2 ↔ E_2` recoupling과 `Θ_1 ↔ v_b` drag가 이미 stiff core 정의의 핵심이다.
- scalar-only로 먼저 가면 split 구조를 나중에 다시 설계해야 한다.
- CAMB validation 및 기존 polarization test asset과의 대응이 흐려진다.

따라서 다음 activation sequence를 채택한다.

- **Checkpoint A**: TT-only, pol off, no massive-ν
- **Checkpoint B**: polarization on
- **Checkpoint C**: production truncation scale-up
- **Checkpoint D**: massive-ν extension

---

## 2. 이 방법은 왜 단순 IMEX가 아닌가

## 2.1 classical IMEX와의 차이

고전적 IMEX는 보통 전체 시스템을

\[
y' = F(y,t) + G(y,t)
\]

로 나누고, explicit tableau와 implicit tableau를 **동등한 지위**로 결합한다. 즉 method 자체가 하나의 pair로 설계된다.

반면 여기서 설계하는 방법은 다르다.

- 외부 macro-stepper, adaptive step-size, accept/reject, embedded error control은 **계속 RODAS5P 단일 체제**다.
- 내부에서만 상태를 세 블록으로 나눈다.
  - `y_C`: stiff collision core
  - `y_M`: mixed block
  - `y_T`: diagonally damped tail
- 각 블록은 서로 다른 kernel로 처리한다.
  - `y_C`: linearly implicit Rosenbrock
  - `y_M`: explicit predictor-corrector
  - `y_T`: integrating factor + explicit source
- 최종 accept/reject는 **full-state defect norm**으로 공동 판정한다.

즉 이건 `IMEX pair`라기보다 **RODAS5P-centered kernel decomposition**이다.

## 2.2 LSODA switching과의 차이

이 방법은 `stiff면 solver A, nonstiff면 solver B` 식의 전역 solver switching이 아니다.

- solver identity는 계속 `RODAS5P`
- 바뀌는 것은 solver가 아니라 **internal kernel mode**
  - tight mode
  - loose mode
- 따라서 solver thrashing을 줄이고, step마다 stiff/nonstiff 재판정으로 solver를 갈아타는 불안정을 피한다.

## 2.3 operator splitting과의 차이

이 방법은 완전 decoupled된 subflow composition도 아니다.

- core solve가 mixed/tail predictor를 참조하고
- tail IF update가 core stage 결과를 다시 참조하고
- 마지막 accept/reject가 full-state 차원에서 공동으로 일어나기 때문이다.

따라서 가장 정확한 명명은 다음 중 하나다.

- `RODAS5P-centered partitioned hybrid`
- `partitioned Rosenbrock hybrid`
- `block-implicit hybrid with integrating-factor tails`

문서상 표준 명칭은 **RODAS5P-centered partitioned hybrid**로 통일한다.

---

## 3. 목표 시스템과 block split

## 3.1 prototype 레벨의 상태벡터

초기 scalar-sector prototype에서 다음 상태를 상정한다.

\[
y=(\delta_b, v_b, \delta_c, v_c, \Phi, \Psi,
\Theta_0,\Theta_1,\ldots,\Theta_{L_\gamma},
E_2,\ldots,E_{L_E},
N_0,\ldots,N_{L_\nu})
\]

recombination 변수 `(x_e, T_m)`는 현재 설계에서 ODE state에 넣지 않는다.

## 3.2 추천 split

### Core block

\[
y_C=(\Theta_0,\Theta_1,\Theta_2,\Theta_3,E_2,E_3,v_b)
\]

선택적으로 `δ_b`를 포함할 수 있지만, 초기 버전은 제외를 기본값으로 한다.

### Mixed block

\[
y_M=(\delta_b,\delta_c,v_c,\Phi,\Psi,N_0,N_1,N_2)
\]

### Tail block

\[
y_T=(\Theta_{\ell\ge4},E_{\ell\ge4},N_{\ell\ge3})
\]

## 3.3 물리적 근거

- low-ℓ photon-baryon-polarization 블록은 collision-induced **non-diagonal stiffness**가 강하다.
- 특히 핵심 변수는
  - `v_b`
  - `Θ_1`
  - `Θ_2`
  - `E_2`
- 반면 high-ℓ photon/pol tail은 pre-recombination에서 stiff하더라도 대부분 `-κ̇ × state` 형태의 **강한 선형 감쇠**에 가깝다.
- neutrino는 collisionless라서 stiff block의 직접 원인은 아니지만, source coupling 때문에 무시 가능한 블록은 아니다.

---

## 4. 하이브리드 적분기의 수학적 구조

전체 시스템을 다음처럼 쓴다.

\[
\begin{aligned}
y_C' &= F_C(y_C,y_M,y_T,\eta),\\
y_M' &= F_M(y_C,y_M,y_T,\eta),\\
y_T' &= -\kappa'(\eta) D_T y_T + G_T(y_C,y_M,y_T,\eta).
\end{aligned}
\]

여기서:

- `κ̇(η) ≥ 0` 는 외부 profile에서 공급되는 Thomson opacity
- `D_T` 는 tail damping diagonal matrix
- `F_C` 안에는 최소한 다음 coupling이 들어가야 한다.
  - `Θ_1 ↔ v_b`
  - `Θ_2 ↔ E_2`
  - low-ℓ collision subblock

## 4.1 차원 / 부호 / 극한 체크

- `κ̇`의 차원은 conformal-time 기준 `1/η`
- `h κ̇`는 무차원 stiffness indicator
- collision diagonal term은 반드시 damping 방향, 즉 기본적으로 `-κ̇` 계열이어야 한다.

known limit:

- `κ̇ → 0`: free-streaming / nonstiff limit
- `κ̇ → ∞`: tight-coupled manifold 접근

중요한 건 **TCA를 코드에 넣는 것**이 아니라, 수치해가 TCA manifold 근처에 **안정하게 붙는지**를 검증하는 것이다.

---

## 5. 알고리즘 요약

## 5.1 Outer integrator

- outer controller = `RODAS5P`
- macro-step = `h`
- accept/reject = unified full-state error norm

## 5.2 Internal kernels

### Core

RODAS5P-style linearly implicit solve:

\[
\left(I-\gamma_i h J_{CC}^{*}\right)\Delta y_C^{(i)} = h R_C^{(i)}
\]

여기서

\[
J_{CC}^{*} \approx \frac{\partial F_C}{\partial y_C}
\]

### Mixed

explicit predictor-corrector

### Tail

integrating factor with frozen stage coefficient:

\[
y_T^{n+1}=e^{-h\kappa^*_T D_T} y_T^n + \int_0^h e^{-(h-s)\kappa^*_T D_T} G_T(s) \, ds
\]

실장 레벨에서는 `phi_1` 기반 diagonal update를 쓴다.

## 5.3 Unified acceptance

core 오차만 보고 accept하면 안 된다. 최종 규칙은 다음과 같다.

\[
\|e\|_{\mathrm{full}}^2
=
\|e_C/W_C\|^2
+
\|e_M/W_M\|^2
+
\|e_T/W_T\|^2
\]

여기서:

- `e_C`: RODAS5P embedded estimator
- `e_M, e_T`: predictor/corrector defect

## 5.4 Kernel hysteresis

solver switching이 아니라 internal kernel switching만 허용한다.

\[
\chi = h \max(\kappa')
\]

- tight mode on: `χ > χ_on`
- loose mode restore: `χ < χ_off`
- hysteresis: `χ_on > χ_off`

예시 초기값:

- `χ_on = 0.5`
- `χ_off = 0.2`

---

## 6. 검증 원칙

## 6.1 절대 규칙

한 PR / 한 실험에서 한 변수만 바꾼다.

같은 비교축에서 절대 동시에 바꾸지 말 것:

- tolerance
- hierarchy truncation (`L_γ, L_ν, L_pol`)
- recombination / visibility table
- gauge/source interpolation
- layout/메모리 구조
- compiler flags / thread count / hardware

즉 **solver kernel만 바뀌게** 만들어야 한다.

## 6.2 baseline

모든 비교의 baseline은 항상 `full-Rodas5P`다.

## 6.3 기록해야 할 공통 메트릭

### 성능

- wall time
- peak RSS
- accepted steps
- rejected steps
- Jacobian rebuild count
- factorization count
- linear solve total time
- linear solve mean time

### 수치

- `||y_hybrid - y_rodas|| / ||y_rodas||`
- block별 drift norm: core / mixed / tail
- stage defect norms: `e_C, e_M, e_T`

### 물리

- `TT` transfer difference
- `EE` transfer difference
- low-ℓ `C_ℓ` 차이
- `D_2` drift
- visibility peak vicinity source drift

### 안정성

- reject burst
- mode oscillation count
- NaN / Inf / negative pathology
- limit recovery (`κ̇→0`, large `κ̇`)

---

## 7. Progressive activation plan

## Stage 0 — baseline regime

- `L_γ = 12`
- `L_ν = 8`
- `L_pol = 0`
- solver = full RODAS5P
- 목적 = TT-only FLRW baseline 확정

## Stage 1 — solver-kernel ablation

같은 setup에서 A1~A6 수행

## Stage 2 — polarization activation

- `L_pol = L_γ`
- `Θ_2 ↔ E_2` recoupling gate
- EE 생성 확인

## Stage 3 — production truncation scale-up

- `L_γ = 25`
- `L_ν = 15`
- CAMB / current validation gate 비교

## Stage 4 — massive neutrino extension

- massive-ν momentum bins 추가
- 이 단계 이전까지는 layout 구조 불필요하게 흔들지 않는다.

---

## 8. Ablation ladder

## A0. Baseline contract freeze

### 목적

비교 기준선 확정. 이후 모든 hybrid 실험은 이 baseline 대비로만 평가한다.

### 변경 범위

- 코드 변경 최소화
- profiling harness / output dump / metrics logging 추가 가능
- solver kernel 변경 금지

### 추천 변경 파일

- `src/solver/pstf_primary/integrate.rs`
- `src/solver/pstf_primary/full_rhs.rs`
- `src/solver/pstf_primary/layout.rs`
- `tests/` 아래 baseline snapshot 추가
- `scripts/bench/` 또는 `scripts/validate/` 아래 baseline runner 추가

### 테스트

- existing FLRW smoke tests
- TT-only transfer regression
- baseline metrics dump sanity

### 통과 기준

- baseline outputs 재현
- metrics logger가 step/reject/Jacobian count를 안정적으로 기록
- output drift = 없음 또는 roundoff 수준

### smoke command

```bash
cargo test --release pstf_primary -- --nocapture
cargo run --release --bin pstf_benchmark -- --mode baseline --l-gamma 12 --l-nu 8 --l-pol 0
python scripts/validate/compare_baseline.py --case flrw_tt_only
```

---

## A1. Block view only

### 목적

`split_state(y)->(C,M,T)` indexing/view가 observables를 건드리지 않는다는 것 확인.

### 변경 범위

- block view 추가
- 실제 적분은 여전히 full RODAS5P
- 수학적 update 변경 금지

### 추천 변경 파일

- `src/solver/pstf_primary/layout.rs`
- `src/pstf/lm_indexing.rs`
- `src/solver/pstf_primary/state_views.rs` *(신규 추천)*
- `tests/test_state_views.rs` *(신규 추천)*

### 테스트

- block split/join roundtrip
- contiguous run test
- 기존 baseline과 state trajectory 비교

### 통과 기준

- split/join 후 상태 동일
- baseline과 수치 차이 = roundoff 수준
- wall time 열화 거의 없음

### smoke command

```bash
cargo test --release state_views -- --nocapture
cargo test --release pstf_primary::layout -- --nocapture
cargo run --release --bin pstf_benchmark -- --mode baseline_with_views --l-gamma 12 --l-nu 8 --l-pol 0
```

---

## A2. Core Jacobian extraction only

### 목적

`J_CC` 정의가 맞는지 검증. 아직 hybrid update는 하지 않는다.

### 변경 범위

- `J_CC = ∂F_C/∂y_C` builder 추가
- full-Rodas equivalent path 유지
- tail IF / mixed explicit 아직 금지

### 추천 변경 파일

- `src/solver/pstf_primary/jacobian.rs`
- `src/solver/pstf_primary/core_jacobian.rs` *(신규 추천)*
- `src/solver/pstf_primary/state_views.rs`
- `tests/test_core_jacobian_structure.rs`

### 테스트

- `Θ_1 ↔ v_b` coupling 존재
- `Θ_2 ↔ E_2` dense block 존재
- finite-difference Jacobian vs analytic/block Jacobian 비교

### 통과 기준

- `J_CC` sparsity / block structure가 기대와 일치
- FD 비교 오차가 허용 범위 이내
- full-Rodas equivalent mode에서 observables drift 없음

### smoke command

```bash
cargo test --release core_jacobian -- --nocapture
cargo run --release --bin pstf_debug_jacobian -- --l-gamma 12 --l-nu 8 --l-pol 0
python scripts/validate/check_core_jacobian_fd.py --case flrw_tt_only
```

---

## A3. Tail integrating-factor only

### 목적

가장 싼 부분 최적화만 먼저 넣어서 정확도/속도 tradeoff 확인.

### 변경 범위

- photon `I/E` tail (`ℓ >= ℓ_core+1`)에 한해 IF update 도입
- mixed block은 아직 기존 경로 유지
- acceptance는 아직 core 중심이어도 되지만 full-state defect를 기록은 시작

### 추천 변경 파일

- `src/solver/pstf_primary/tail_if.rs` *(신규 추천)*
- `src/solver/pstf_primary/full_rhs.rs`
- `src/solver/pstf_primary/integrate.rs`
- `tests/test_tail_if_scalar.rs`
- `tests/test_tail_if_limit.rs`

### 테스트

- diagonal damping analytic update test
- `κ̇ → 0` limit에서 explicit tail 일치
- large `κ̇`에서 안정성 유지
- baseline 대비 `TT` drift 비교

### 통과 기준

- observables drift가 baseline tolerance band 안
- reject 수 감소 또는 최소한 증가하지 않음
- NaN/Inf 없음

### smoke command

```bash
cargo test --release tail_if -- --nocapture
cargo run --release --bin pstf_benchmark -- --mode hybrid_a3 --l-gamma 12 --l-nu 8 --l-pol 0
python scripts/validate/compare_observables.py --ref baseline --cand hybrid_a3 --metrics tt,d2
```

---

## A4. Mixed predictor-corrector

### 목적

lagged coupling이 실제로 안전한지 측정.

### 변경 범위

- mixed block explicit predictor-corrector 추가
- core는 계속 RODAS5P
- 이 단계부터 full-state defect norm을 반드시 계산

### 추천 변경 파일

- `src/solver/pstf_primary/mixed_predictor.rs` *(신규 추천)*
- `src/solver/pstf_primary/integrate.rs`
- `src/solver/pstf_primary/full_rhs.rs`
- `tests/test_mixed_predictor_consistency.rs`

### 테스트

- predictor/corrector defect sanity
- core/mixed/tail coupling lag sensitivity
- low-ℓ transfer drift test

### 통과 기준

- full-state defect가 폭주하지 않음
- low-ℓ observable drift 허용 범위 이내
- baseline 대비 성능/정확도 tradeoff가 해석 가능

### smoke command

```bash
cargo test --release mixed_predictor -- --nocapture
cargo run --release --bin pstf_benchmark -- --mode hybrid_a4 --l-gamma 12 --l-nu 8 --l-pol 0
python scripts/validate/compare_observables.py --ref baseline --cand hybrid_a4 --metrics tt,d2,transfer_lowell
```

---

## A5. Unified full-state acceptance

### 목적

“core는 맞는데 tail이 틀린” 거짓 accept 제거.

### 변경 범위

- accept/reject를 core embedded error-only에서 full-state weighted norm으로 승격
- `e_C, e_M, e_T` 통합

### 추천 변경 파일

- `src/solver/pstf_primary/error_control.rs` *(신규 추천)*
- `src/solver/pstf_primary/integrate.rs`
- `tests/test_full_state_acceptance.rs`

### 테스트

- synthetic case에서 tail defect만 클 때 reject되는지 확인
- core만 작은 케이스의 false accept 제거 확인
- hybrid A4 vs A5 비교

### 통과 기준

- false accept 제거가 분명
- 안정성 개선이 수치적으로 확인
- 성능 손해가 있더라도 해석 가능하고 정당화 가능

### smoke command

```bash
cargo test --release error_control -- --nocapture
cargo run --release --bin pstf_benchmark -- --mode hybrid_a5 --l-gamma 12 --l-nu 8 --l-pol 0
python scripts/validate/check_false_accept.py --ref hybrid_a4 --cand hybrid_a5
```

---

## A6. Kernel hysteresis

### 목적

mode thrashing 방지.

### 변경 범위

- `χ = h max(κ̇)` 기반 mode selector 추가
- `χ_on > χ_off` hysteresis 적용
- solver switching은 금지, kernel switching만 허용

### 추천 변경 파일

- `src/solver/pstf_primary/hybrid_controller.rs` *(신규 추천)*
- `src/solver/pstf_primary/integrate.rs`
- `tests/test_kernel_hysteresis.rs`

### 테스트

- threshold crossing 반복 synthetic run
- hysteresis off vs on mode oscillation count 비교
- reject burst 비교

### 통과 기준

- mode oscillation count 감소
- reject burst 감소 또는 최소 유지
- observables drift 증가 없음

### smoke command

```bash
cargo test --release kernel_hysteresis -- --nocapture
cargo run --release --bin pstf_benchmark -- --mode hybrid_a6 --l-gamma 12 --l-nu 8 --l-pol 0
python scripts/validate/compare_hysteresis.py --off hybrid_a5 --on hybrid_a6
```

---

## A7. Polarization activation

### 목적

physics activation checkpoint B. `Θ_2 ↔ E_2` recoupling과 EE 생성 확인.

### 변경 범위

- `L_pol = L_γ`
- split / core Jacobian / tail IF를 polarization on에서도 유지

### 추천 변경 파일

- `src/solver/pstf_primary/layout.rs`
- `src/solver/pstf_primary/full_rhs.rs`
- `src/solver/pstf_primary/core_jacobian.rs`
- `tests/test_pol_recoupling.rs`
- `tests/test_ee_generation.rs`

### 테스트

- polarization on/off comparison
- `Θ_2 ↔ E_2` recoupling regression
- EE transfer 생성
- existing bass_py factor gate와 대조

### 통과 기준

- EE 생성
- `Θ_2 ↔ E_2` recoupling test pass
- TT/EE drift가 tolerance band 안

### smoke command

```bash
cargo test --release pol_recoupling -- --nocapture
cargo run --release --bin pstf_benchmark -- --mode hybrid_pol --l-gamma 12 --l-nu 8 --l-pol 12
python scripts/validate/compare_observables.py --ref baseline_pol --cand hybrid_pol --metrics tt,ee,d2
```

---

## A8. Production truncation scale-up

### 목적

production-scale validation.

### 변경 범위

- `L_γ = 25`
- `L_ν = 15`
- current validation / CAMB gate 대조

### 추천 변경 파일

- `config/production_hybrid.toml` *(신규 추천)*
- `scripts/bench/run_scaleup.sh`
- `scripts/validate/compare_camb_gate.py`

### 테스트

- wall time / RSS / reject count at scale
- TT/EE / low-ℓ `C_ℓ`
- `D_2` gate
- visibility-weighted source drift

### 통과 기준

- current validation gate 통과
- full-Rodas 대비 실제 wall-time 이득 확인
- catastrophic drift 없음

### smoke command

```bash
cargo run --release --bin pstf_benchmark -- --mode hybrid_prod --l-gamma 25 --l-nu 15 --l-pol 25
python scripts/validate/compare_camb_gate.py --ref camb --cand hybrid_prod
python scripts/validate/compare_full_rodas.py --ref full_rodas_prod --cand hybrid_prod
```

---

## A9. Massive-neutrino extension (후속)

### 목적

solver kernel 검증 후 physics/layout 확장.

### 변경 범위

- massive-ν momentum bins 추가
- layout 확장
- hybrid split 재점검

### 주의

이 단계는 **solver kernel이 충분히 검증된 이후**로 미룬다. 초기 hybrid 검증과 섞지 않는다.

### 추천 변경 파일

- `src/pstf/lm_indexing.rs`
- `src/solver/pstf_primary/layout.rs`
- `src/solver/pstf_primary/full_rhs.rs`
- `tests/test_massive_nu_layout.rs`
- `tests/test_massive_nu_hybrid.rs`

### smoke command

```bash
cargo test --release massive_nu -- --nocapture
cargo run --release --bin pstf_benchmark -- --mode hybrid_massive_nu --l-gamma 25 --l-nu 15 --l-pol 25
```

---

## 9. PR/WBS master roadmap

## PR-00. Baseline contract freeze

### WBS

- WBS-00-01 baseline config 고정
- WBS-00-02 metrics logger 추가
- WBS-00-03 reference outputs snapshot 저장
- WBS-00-04 benchmark runner 작성

### Deliverables

- baseline contract md
- benchmark log json/csv
- reference output snapshot

---

## PR-01. State block views

### WBS

- WBS-01-01 `split_state()` 설계
- WBS-01-02 block index table 고정
- WBS-01-03 join/split roundtrip test
- WBS-01-04 contiguous run assertions

### Deliverables

- `state_views.rs`
- view tests
- baseline equivalence report

---

## PR-02. Core Jacobian extraction

### WBS

- WBS-02-01 `J_CC` 포함 변수 확정
- WBS-02-02 analytic Jacobian block builder 작성
- WBS-02-03 FD comparison harness 작성
- WBS-02-04 structure/sparsity report 생성

### Deliverables

- `core_jacobian.rs`
- FD validation report
- block structure figure/table

---

## PR-03. Tail integrating-factor prototype

### WBS

- WBS-03-01 photon I tail damping IF
- WBS-03-02 photon E tail damping IF
- WBS-03-03 `phi_1` safe scalar kernel 구현
- WBS-03-04 `κ̇→0` / large-`κ̇` limit tests
- WBS-03-05 A3 benchmark report

### Deliverables

- `tail_if.rs`
- limit tests
- A3 benchmark report

---

## PR-04. Mixed predictor-corrector

### WBS

- WBS-04-01 mixed variable set 확정
- WBS-04-02 predictor 구현
- WBS-04-03 corrector/defect 계산
- WBS-04-04 lag sensitivity test
- WBS-04-05 A4 benchmark report

### Deliverables

- `mixed_predictor.rs`
- defect report
- A4 benchmark report

---

## PR-05. Unified full-state acceptance

### WBS

- WBS-05-01 weighted norm 설계
- WBS-05-02 `e_C/e_M/e_T` 통합
- WBS-05-03 false-accept synthetic tests
- WBS-05-04 A5 report

### Deliverables

- `error_control.rs`
- false-accept tests
- A5 report

---

## PR-06. Kernel hysteresis controller

### WBS

- WBS-06-01 `χ` estimator 구현
- WBS-06-02 `χ_on/χ_off` hysteresis logic 구현
- WBS-06-03 mode oscillation logger
- WBS-06-04 A6 report

### Deliverables

- `hybrid_controller.rs`
- hysteresis tests
- A6 report

---

## PR-07. Polarization activation

### WBS

- WBS-07-01 `L_pol` activation
- WBS-07-02 `Θ_2 ↔ E_2` recoupling validation
- WBS-07-03 EE transfer validation
- WBS-07-04 polarization benchmark report

### Deliverables

- polarization-enabled hybrid path
- recoupling test report
- EE benchmark report

---

## PR-08. Production scale-up

### WBS

- WBS-08-01 `L_γ=25, L_ν=15` production config
- WBS-08-02 large-scale profiling
- WBS-08-03 CAMB/current-gate comparison
- WBS-08-04 promotion or rollback decision

### Deliverables

- production benchmark report
- validation report
- promotion decision memo

---

## PR-09. Optional multirate tail subcycling

### 성격

옵션. A3~A8이 안정적으로 통과한 뒤에만 고려.

### WBS

- WBS-09-01 tail subcycling design
- WBS-09-02 synchronization correctness test
- WBS-09-03 performance-only benchmark

### 보류 조건

A8까지 wall-time 이득이 충분하지 않거나, tail RHS cost가 여전히 지배적일 때만 열 것.

---

## PR-10. Optional Rosenbrock-Krylov linears

### 성격

옵션. Jacobian factorization이 주 병목이라는 profiling 근거가 있을 때만 고려.

### WBS

- WBS-10-01 Krylov feasibility audit
- WBS-10-02 preconditioner sketch
- WBS-10-03 linears-only benchmark

### 보류 조건

A8 profiling에서 factorization/solve time이 total wall-time의 지배항일 때만 열 것.

---

## 10. 권장 파일 맵

아래는 **이번 대화와 업로드된 분석안 기준의 권장 파일 맵**이다. 실제 저장소와 1:1 재검증한 것은 아니므로, 구현 전에 repo tree에 맞춰 이름은 조정해라.

## Core files

- `src/solver/pstf_primary/integrate.rs`
- `src/solver/pstf_primary/full_rhs.rs`
- `src/solver/pstf_primary/layout.rs`
- `src/pstf/lm_indexing.rs`
- `src/solver/pstf_primary/jacobian.rs`

## New recommended files

- `src/solver/pstf_primary/state_views.rs`
- `src/solver/pstf_primary/core_jacobian.rs`
- `src/solver/pstf_primary/tail_if.rs`
- `src/solver/pstf_primary/mixed_predictor.rs`
- `src/solver/pstf_primary/error_control.rs`
- `src/solver/pstf_primary/hybrid_controller.rs`

## Test files

- `tests/test_state_views.rs`
- `tests/test_core_jacobian_structure.rs`
- `tests/test_tail_if_scalar.rs`
- `tests/test_tail_if_limit.rs`
- `tests/test_mixed_predictor_consistency.rs`
- `tests/test_full_state_acceptance.rs`
- `tests/test_kernel_hysteresis.rs`
- `tests/test_pol_recoupling.rs`
- `tests/test_ee_generation.rs`
- `tests/test_massive_nu_layout.rs`
- `tests/test_massive_nu_hybrid.rs`

## Benchmark / validation scripts

- `scripts/bench/run_hybrid_ablation.sh`
- `scripts/validate/compare_baseline.py`
- `scripts/validate/check_core_jacobian_fd.py`
- `scripts/validate/compare_observables.py`
- `scripts/validate/check_false_accept.py`
- `scripts/validate/compare_hysteresis.py`
- `scripts/validate/compare_camb_gate.py`
- `scripts/validate/compare_full_rodas.py`

---

## 11. 각 단계의 yes/no gate

## Gate G0 — baseline locked

- baseline contract 문서화 완료
- benchmark harness 정상 동작
- reference outputs frozen

## Gate G1 — block views safe

- split/join exact
- baseline drift = roundoff 수준

## Gate G2 — core Jacobian sane

- expected coupling blocks present
- FD check pass
- full-Rodas equivalent path 보존

## Gate G3 — tail IF safe

- `κ̇→0`, large-`κ̇` limit pass
- TT / D2 drift 허용 범위 이내
- reject count non-worse or better

## Gate G4 — mixed predictor safe

- full-state defect stable
- low-ℓ transfer drift 허용 범위 이내

## Gate G5 — acceptance honest

- false-accept 제거 확인
- numerical stability visibly improved

## Gate G6 — hysteresis useful

- mode oscillation 감소
- reject burst 감소 또는 유지

## Gate G7 — polarization promoted

- EE 생성
- `Θ_2 ↔ E_2` recoupling test pass

## Gate G8 — production worthy

- current validation gate pass
- full-Rodas 대비 실제 wall-time 이득 존재
- catastrophic observable drift 없음

---

## 12. 금지사항 / red lines

다음은 초반 PR에서 금지한다.

1. `A3`와 `A4`를 동시에 넣는 것  
   → tail IF가 좋은지, mixed predictor가 나쁜지 분간이 안 된다.

2. layout compactification을 초반에 넣는 것  
   → memory/layout bug와 solver bug가 섞인다.

3. speedup claim을 먼저 세우는 것  
   → profiling-first로만 판단한다.

4. scalar-only 별도 프로토타입을 만드는 것  
   → 같은 split을 두 번 설계하게 된다.

5. TCA/RFA/URF를 사실상 timestepper 내부 hidden closure로 심는 것  
   → 이름만 다를 뿐 네가 피하려는 근사와 본질적으로 같아질 수 있다.

---

## 13. 최종 권고

지금 가장 정직한 시작점은 다음이다.

- 먼저 **A0 → A1 → A2 → A3**까지 간다.
- 특히 첫 실제 hybrid 승격은 `A3 (tail IF only)`로 제한한다.
- `A4 (mixed predictor)`는 `A3`가 안정적이라는 증거가 나온 다음에 넣는다.
- `A5 (full-state acceptance)`는 실질적으로 production 승격의 필수 조건이다.
- `A6 (hysteresis)`는 solver switching이 아니라 kernel switching만 허용하는 안정화 레이어다.
- polarization / scale-up / massive-ν는 solver kernel 검증이 끝난 뒤에만 단계적으로 올린다.

한 줄로 요약하면 이렇다.

> **IMEX로 갈아타는 게 아니라, RODAS5P를 왕좌에 그대로 둔 채 low-ℓ collision core만 암묵적으로 붙들고, tail은 IF로 빼고, mixed는 천천히 explicit로 분리하며, full-Rodas baseline과의 차이를 ablation ladder로 끝까지 추적하는 것.**

---

## 14. 다음 액션 제안

가장 먼저 할 일은 두 가지다.

1. `PR-00 baseline contract freeze`를 실제 repo 기준으로 확정  
2. `PR-01 state block views`와 `PR-02 core Jacobian extraction`을 바로 시작

이 두 개가 닫히기 전까지는 tail IF도, mixed predictor도 넣지 않는 게 맞다.
