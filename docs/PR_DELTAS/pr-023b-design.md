# PR-023b Design Document — PSTF Fluid (CDM + Baryon) RHS

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-18
> **Target PR**: PR-023b (sub-track b of PR-023)
> **Dependency**: PR-020 ✅, PR-021 ✅, PR-022a ✅, PR-022b ✅, PR-022c ✅, PR-023a ✅
> **Weight**: 3
> **Target score**: 7

---

## §1. Scope

PSTF primary state vector 위에서 **CDM + baryon fluid RHS** 를 synchronous-gauge equivalent 로 구현. PR-023a 의 `pstf_hdot()` 값을 호출하여 metric coupling (`−hdot/2`) 을 주입. Baryon-photon Thomson drag 는 PR-022b 에 이미 구현 — PR-023b 는 additive 로 합쳐짐.

### 포함된 것
- `src/solver/pstf_primary/fluid.rs` (예상 ~280 줄)
  - `FluidInputs` struct — `k`, `c_s²_b` (baryon sound speed), `h_conformal`, `hdot` (PR-023a 에서 수령)
  - `pstf_fluid_rhs()` — CDM + baryon continuity/Euler equations

### 포함되지 않은 것
- Metric RHS (etakdot, sigmadot): PR-023a ✅
- Baryon-photon drag (`opac·(3Θ_1 − v_b)/r_b`): PR-022b ✅ (additive)
- Full RHS composition: PR-023c (next, sub-track 마지막)
- Massive ν fluid: future PR

---

## §2. Pre-audit — MB-95 fluid RHS 정확한 구조

MB-95 `camb_rhs:483-487`:
```
clxcdot = -hdot / 2                                          (L483)
clxbdot = -k · v_b - hdot / 2                                (L484)
vbdot   = -ℋ · v_b + c_s²b · k · clxb                        (L486-487)
          + opac · (3·Θ_1 - v_b) / r_b                       ← PR-022b 에 이미 있음
```

### 2.1 PR-023b 의 fluid-only 부분

Thomson drag term 을 제외한 나머지:
```
dy[clxc]  = −hdot / 2
dy[clxb]  = −k · v_b − hdot / 2
dy[v_b]   = −ℋ · v_b + c_s²_b · k · clxb     (Thomson drag 는 PR-022b 가 추가)
```

CDM velocity `v_c` 는 **synchronous gauge 정의상 0** — gauge freedom 을 v_c = 0 으로 고정함. 따라서 `dy[v_c]` 는 0, 즉 dy 에 write 하지 않음.

### 2.2 State layout 매핑

PSTF `LmLayout` 의 fluid 배치 (n_baryon = 4, n_cdm = 4):
```
Baryon block: [δ_b (=clxb), v_b_{m=-1}, v_b_{m=0}, v_b_{m=+1}]
              offset 0    offset 1     offset 2   offset 3

CDM block:    [δ_c (=clxc), v_c_{m=-1}, v_c_{m=0}, v_c_{m=+1}]  (v_c_* = 0)
              offset 0     offset 1    offset 2   offset 3
```

PSTF layout accessor 를 추가:
```rust
impl PstfFlrwLayout {
    pub(crate) fn i_baryon_delta(&self) -> usize { self.inner.baryon_start }
    pub(crate) fn i_baryon_v_m0(&self) -> usize { self.inner.baryon_start + 2 }
    pub(crate) fn i_cdm_delta(&self) -> usize { self.inner.cdm_start }
    pub(crate) fn i_cdm_v_m0(&self) -> usize { self.inner.cdm_start + 2 }  // v_c=0 at sync
}
```

**중요**: 이전 PR 들 (PR-022b, PR-023a) 에서 `baryon_start + 2` 를 raw 로 사용했던 것을 `i_baryon_v_m0()` 로 치환 가능 (optional refactor, PR-023b scope 외). 일관성을 위해 PR-023b 에서 accessor 만 추가하고 기존 코드는 건드리지 않음 — retrospective refactor 는 PR-023c 에서 고려.

### 2.3 `hdot` 수령 방법

PR-023a 의 `pstf_hdot(state, v_b, inputs, layout)` 를 직접 호출:
```rust
let hdot = pstf_hdot(state, v_b, &metric_inputs, layout);
let dy_clxc = -hdot / 2.0;
let dy_clxb = -k * v_b - hdot / 2.0;
let dy_vb   = -h_conformal * v_b + cs2b * k * clxb;
```

이것은 `FluidInputs` 이 `MetricInputs` 를 포함하거나 (option A), 또는 `hdot` 값을 직접 받거나 (option B). **Option B 선택** — 더 flexible:

```rust
pub(crate) struct FluidInputs {
    pub(crate) k: f64,
    pub(crate) h_conformal: f64,  // ℋ
    pub(crate) cs2b: f64,          // c_s²_b baryon sound speed
    pub(crate) hdot: f64,           // PR-023a pstf_hdot() result, passed in
}
```

Caller (test 및 PR-023c dispatcher) 가 `pstf_hdot(state, v_b, &metric_inputs, layout)` 을 먼저 compute 하여 `FluidInputs.hdot` 에 주입. Inter-sector dependency 를 명시적으로 드러냄.

---

## §3. API 설계

### 3.1 FluidInputs struct

```rust
pub(crate) struct FluidInputs {
    pub(crate) k: f64,
    pub(crate) h_conformal: f64,
    pub(crate) cs2b: f64,
    pub(crate) hdot: f64,
}
```

### 3.2 Main function

```rust
pub(crate) fn pstf_fluid_rhs(
    state: &[f64],
    dy: &mut [f64],
    inputs: &FluidInputs,
    layout: &PstfFlrwLayout,
);
```

Touches:
- `dy[i_cdm_delta()]` += `-hdot/2`
- `dy[i_baryon_delta()]` += `-k·v_b − hdot/2`
- `dy[i_baryon_v_m0()]` += `-ℋ·v_b + cs2b·k·clxb`

Untouched:
- Metric sector (PR-023a scope)
- Photon / neutrino sectors (PR-022a/b scope)
- Polarization (not in PR-023b)
- v_c (= 0 at sync gauge, no evolution)
- Bianchi reserve

### 3.3 New layout accessors

```rust
impl PstfFlrwLayout {
    pub(crate) fn i_baryon_delta(&self) -> usize { self.inner.baryon_start }
    pub(crate) fn i_baryon_v_m0(&self) -> usize { self.inner.baryon_start + 2 }
    pub(crate) fn i_cdm_delta(&self) -> usize { self.inner.cdm_start }
    pub(crate) fn i_cdm_v_m0(&self) -> usize { self.inner.cdm_start + 2 }
}
```

---

## §4. TDD gate (10 tests 예상)

### Identity (3 tests)
- `identity_clxcdot_matches_mb95` — `-hdot/2` bit-identical for representative hdot values
- `identity_clxbdot_matches_mb95` — `-k·v_b − hdot/2` 수식 일치
- `identity_vbdot_matches_mb95` — `-ℋ·v_b + cs2b·k·clxb` 수식 (**Thomson drag 제외**)

### Limit (2 tests)
- `limit_zero_state_trivial` — state=0, hdot=0 이면 fluid dy 전부 0
- `limit_zero_hdot_clxcdot_zero` — hdot=0 에서 clxcdot=0 (MB-95 `-hdot/2` 자명)

### Regression (2 tests) — G2 full FLRW
- `regression_fluid_rhs_multiple_k` — k ∈ {1e-4, 1e-2, 1e-1} 에서 MB-95 inline formula 와 bit-identical
- `regression_with_pr023a_hdot` — PR-023a `pstf_hdot()` 값을 `FluidInputs.hdot` 로 주입 후 MB-95 와 bit-identical (integration test)

### Channelwise (2 tests)
- `channelwise_metric_untouched` — fluid RHS 가 metric sector (etak, σ, Bianchi reserve) 무접촉
- `channelwise_photon_nu_untouched` — photon / ν sectors 무접촉

### Caveat (1 test)
- `caveat_cdm_velocity_zero_at_sync_gauge` — `dy[i_cdm_v_m0()]` 가 fluid RHS 에서 0 유지 (v_c = 0 gauge 조건)

**총 10 tests**.

---

## §5. Gate forecast

| Gate | 예상 | 근거 |
|---|---|---|
| G1 COMPILE | ✅ | 새 파일, 기존 회귀 없음 |
| **G2 FLRW (full)** | **✅** | `regression_fluid_rhs_multiple_k` + `regression_with_pr023a_hdot` 이 direct MB-95 formula 대조. PR-022b 의 drag term 은 additive 라 bit-identical 유지 |
| G3 PHYS | ✅ | Identity / limit / caveat / channelwise |
| G4 CROSS | ✅ | MB-95 `camb_rhs:483-487` inline 대조 |

**Score: 7/10** forecast. W=3 × S=7/10 = **W·S/10 = 2.1** (forecast 정확).

Phase 1 진행률: 43.3% → **45.3%**.

---

## §6. Anti-local-min triggers

1. **Thomson drag 중복 적용** — PR-022b 가 이미 baryon `dy[v_b]` 에 `+opac·(3Θ_1 − v_b)/r_b` 를 추가함. PR-023b 가 이것을 다시 추가하면 double-counting. **해결**: PR-023b `vbdot` 공식에 **drag 를 포함하지 않음**. `regression_with_pr023a_hdot` test 가 PR-022b + PR-023b 합산이 MB-95 full 과 bit-identical 인지 검증.

2. **v_c ≠ 0 유입** — sync-gauge 에서 v_c = 0 이지만, 실수로 state[i_cdm_v_m0()] 를 nonzero 로 initialize 하면 이후 로직이 망가질 수 있음. `caveat_cdm_velocity_zero_at_sync_gauge` test 가 PR-023b 의 dy[v_c] 가 fluid RHS 에 의해 touch 되지 않음을 보장. (State level invariant 는 PR-021 IC 에서 이미 v_c=0 유지, PR-023b 는 dy side 만 검증.)

3. **`hdot` sign 실수** — `dy[clxc] = −hdot/2`, `dy[clxb] = −k·v_b − hdot/2` 양쪽 모두 `−hdot/2` 이므로 부호 일관. `identity_*` tests 가 catch.

---

## §7. Pre-PR checklist

- [x] MB-95 `camb_rhs:483-487` 재감사 완료 (§2)
- [x] Thomson drag 가 PR-022b 에 있음 확인 (§6 trigger 1)
- [x] v_c = 0 sync gauge 조건 확인 (§2.1)
- [x] `FluidInputs` 에 `hdot` 을 직접 받는 option B 선택 (§2.3)
- [x] Layout accessors 추가 계획 (§3.3)

---

## §8. 즉시 다음 행동

동일 turn 내:
1. **PR-023b scaffold** — `src/solver/pstf_primary/fluid.rs` 신설
2. `FluidInputs`, `pstf_fluid_rhs()` 구현
3. Layout accessors 4개 추가 (`i_baryon_delta`, `i_baryon_v_m0`, `i_cdm_delta`, `i_cdm_v_m0`)
4. 10 tests 작성 (§4)
5. D_2 12th consecutive bit-identical 재확인
6. `pr-023b.md` closure delta + scoreboard 갱신 (43.3% → 45.3%)

PR-023b 완료 후 **PR-023c (composition + PR-022a G2 retrospective 승격)** 진입 — sub-track 마지막.

---

*PR-023b 는 PR-023 sub-track 의 두 번째. Fluid sector 는 simple continuity/Euler (CDM + baryon), Thomson drag 는 PR-022b 이미 있음 (additive). Option B interface (`hdot` 직접 주입) 로 inter-sector dependency 명시화. PR-023c 가 sub-track 의 마지막 단계 — PR-022a G2 partial → full 승격 및 전체 dispatcher 조립.*
