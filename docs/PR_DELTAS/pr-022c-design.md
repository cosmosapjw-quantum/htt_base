# PR-022c Design Document — PSTF Analytical Jacobian (Sparse, Rodas5P-compatible)

> **Status**: 📝 **DESIGN (pre-audit)** — 2026-04-18
> **Target PR**: PR-022c (sub-track c of PR-022, 마지막)
> **Dependency**: PR-020 ✅, PR-021 ✅, PR-022a ✅, PR-022b ✅
> **Weight**: 4
> **Target score**: 7

---

## §1. Scope

PSTF primary state vector 위에서 RHS (free-streaming + collision) 의 **analytical sparse Jacobian** 을 구현. Rodas5P (6-stage Rosenbrock) 의 implicit solve 가 analytical J 를 요구하므로, PR-024 에서 production 통합할 때 필수.

### 포함된 것
- `src/solver/pstf_primary/jacobian.rs` (예상 ~300 줄)
  - `JacobianInputs` struct — RhsInputs + CollisionInputs 통합
  - `pstf_analytical_jacobian()` — sparse CSR-like 구조 (triplet list `(row, col, val)`)
  - `pstf_jacobian_dense()` — dense row-major (Rodas5P 호환)
  - Block structure: k/(2ℓ+1) tridiagonal (free-streaming) + ℓ=1 drag 2×2 block (photon↔baryon) + ℓ=2 pol feedback 2×2 block (photon↔E-mode, pol on 시) + diagonal damping (ℓ≥3)
- Finite-difference check helper — 5-point stencil, rel err < 1e-6 tolerance

### 포함되지 않은 것
- Metric coupling Jacobian: PR-023
- Jacobian caching / reuse across time steps: PR-024 (production integration)
- Jacobian-vector product (matrix-free): future optimization

---

## §2. Sparse pattern analysis

### 2.1 Free-streaming block (from PR-022a)

Photon m=0 intensity hierarchy RHS:
```
dΘ_0/dη = −k·Θ_1 + S_metric             (S_metric = placeholder, PR-023)
dΘ_1/dη = k/3·(Θ_0 − 2·Θ_2)
dΘ_ℓ/dη = k/(2ℓ+1)·[ℓ·Θ_{ℓ-1} − (ℓ+1)·Θ_{ℓ+1}]   (ℓ=2..ℓ_max−1)
dΘ_{ℓ_max}/dη = k·Θ_{ℓ_max−1} − (ℓ_max+1)/τ · Θ_{ℓ_max}
```

Jacobian `J[row=Θ_ℓ, col=Θ_m]`:
- `J[0, 1] = −k`
- `J[1, 0] = k/3`
- `J[1, 2] = −2k/3`
- For ℓ ∈ [2, ℓ_max−1]:
  - `J[ℓ, ℓ−1] = k·ℓ/(2ℓ+1)`
  - `J[ℓ, ℓ+1] = −k·(ℓ+1)/(2ℓ+1)`
- `J[ℓ_max, ℓ_max−1] = k`
- `J[ℓ_max, ℓ_max] = −(ℓ_max+1)/τ`

**Sparsity**: Tridiagonal (bandwidth 1), **3·(ℓ_max+1) − 2** nonzero entries. For ℓ_max=16: **49 entries** in the photon intensity block.

Neutrino block is structurally identical (FLRW parallelism from PR-022a).

### 2.2 Collision block (from PR-022b)

Photon sector:
- `J[Θ_1, Θ_1] += −κ̇`
- `J[Θ_1, v_b] += +κ̇/3`
- `J[v_b, Θ_1] += +3·κ̇/r_b`
- `J[v_b, v_b] += −κ̇/r_b`
- For ℓ=2, pol off: `J[Θ_2, Θ_2] += −κ̇`
- For ℓ=2, pol on: `J[Θ_2, Θ_2] += −0.9·κ̇`, `J[Θ_2, E_2] += 3·κ̇/20`
- For ℓ ≥ 3: `J[Θ_ℓ, Θ_ℓ] += −κ̇`

**Sparsity**: ℓ=1 block 은 2×2 cross-coupling (Θ_1 ↔ v_b), 나머지는 diagonal. **ℓ_max + 2** collision entries (photon) + **2** baryon drag entries = **ℓ_max + 4** total. For ℓ_max=16: **20 entries**.

### 2.3 Total nonzero count (photon + neutrino, FLRW m=0)

| Block | Entries (ℓ_max=16) |
|---|---:|
| Photon free-streaming (tridiagonal) | 49 |
| Neutrino free-streaming (tridiagonal) | 49 |
| Photon collision (damping + ℓ=1 coupling) | 20 |
| Baryon drag reaction (ℓ=1 v_b row) | 0 (already counted in collision, cross-coupling)|
| Total | ~118 entries |

Full `n_state` at ℓ_max=16 full layout = **1,156 DOF** (PstfFlrwLayout.n_state). 118 / 1156² = **0.009%** sparsity — extremely sparse, crucial for Rodas5P efficiency.

---

## §3. API 설계

### 3.1 JacobianInputs struct

```rust
pub(crate) struct JacobianInputs {
    pub(crate) k: f64,
    pub(crate) tau: f64,
    pub(crate) metric_monopole_source: f64,  // PR-023 placeholder
    pub(crate) kappa_dot: f64,
    pub(crate) r_b: f64,
    pub(crate) use_pol_feedback: bool,
    pub(crate) frame: FrameConvention,
}

impl JacobianInputs {
    pub(crate) fn from_rhs_and_collision(
        rhs: &RhsInputs,
        collision: &CollisionInputs,
    ) -> Self { ... }
}
```

### 3.2 Sparse output: triplet list

```rust
/// (row, col, value) triplets
pub(crate) struct SparseJacobian {
    pub(crate) entries: Vec<(usize, usize, f64)>,
    pub(crate) n: usize,  // state dim
}

pub(crate) fn pstf_analytical_jacobian(
    state: &[f64],
    inputs: &JacobianInputs,
    layout: &PstfFlrwLayout,
) -> SparseJacobian;
```

Note: `state` 는 linear RHS 에서는 사용 안 되나, **nonlinear extension (future)** 을 위해 interface 에 포함. PR-022c 범위 에서는 Jacobian 이 state 에 독립 (linear free-streaming + linear Thomson collision).

### 3.3 Dense output (Rodas5P 호환)

```rust
/// Row-major dense: `out[i*n + j] = J[i, j]`
pub(crate) fn pstf_jacobian_dense(
    state: &[f64],
    inputs: &JacobianInputs,
    layout: &PstfFlrwLayout,
    out: &mut [f64],
);
```

Wrapper around `pstf_analytical_jacobian` + triplet → dense conversion.

### 3.4 FD check helper

```rust
/// Compute numerical Jacobian via 5-point stencil.
///
/// For each column j, perturb state[j] by ±h, ±2h and compute RHS,
/// then J_num[i, j] = (−RHS(+2h) + 8·RHS(+h) − 8·RHS(−h) + RHS(−2h))/(12h).
///
/// Returns: max relative error over all nonzero entries of J_analytical.
pub(crate) fn jacobian_fd_check(
    state: &[f64],
    inputs: &JacobianInputs,
    layout: &PstfFlrwLayout,
    h: f64,  // typical: 1e-6 · ||state||
) -> (f64, usize, usize);  // (max_rel_err, i_max, j_max)
```

Test 가 이것을 호출하여 analytical vs numerical 일치를 검증.

---

## §4. TDD gate (9 tests 예상)

### Identity (3 tests)
- `identity_free_streaming_tridiagonal_pattern` — photon free-streaming rows 의 non-zero column 이 정확히 `{ℓ-1, ℓ+1}` (plus ℓ_max truncation row 의 `{ℓ-1, ℓ}`)
- `identity_collision_diagonal_pattern` — collision-only (k=0, τ 무관) 에서 ℓ≥3 은 diagonal, ℓ=1 은 `{Θ_1, v_b}` cross, ℓ=2 (pol off) 은 diagonal
- `identity_coefficient_values_match_formula` — ℓ=3: `J[Θ_3, Θ_2] = 3k/7`, `J[Θ_3, Θ_4] = −4k/7`; ℓ=5: 같은 pattern 검증

### FD regression (3 tests) — **G3 의 핵심**
- `fd_regression_free_streaming_only` — collision=0 state 에서 analytical J vs 5-point FD, max rel err < 1e-6
- `fd_regression_collision_only` — k=0 state 에서 analytical J vs FD, max rel err < 1e-6
- `fd_regression_full_combined` — 일반적 state (adiabatic IC + baryon v_b + representative κ̇, k) 에서 analytical vs FD, max rel err < 1e-6

### Limit/Caveat (2 tests)
- `limit_kappa_dot_zero_no_collision_entries` — κ̇=0 에서 collision entries (ℓ=1 cross + diagonal) 가 모두 zero — sparse 에 포함되지 않거나 value=0
- `caveat_sparsity_count` — ℓ_max=16 에서 nonzero entry count == expected (§2.3 analysis 대로)

### Dense/sparse equivalence (1 test)
- `equivalence_dense_vs_sparse` — `pstf_jacobian_dense` 가 `pstf_analytical_jacobian` 의 triplet 을 정확히 dense 로 unroll (모든 non-triplet entry 는 0)

**총 9 tests**.

---

## §5. Gate forecast

| Gate | 예상 | 근거 |
|---|---|---|
| G1 COMPILE | ✅ | 새 파일, 기존 회귀 없음 |
| G2 FLRW | N/A | Jacobian 은 RHS 의 partial derivative — 수치 계산 자체는 FLRW 특정이 아님. FD check 이 G3 에서 다룸 |
| G3 PHYS | ✅ | **FD regression 3 tests 가 핵심** — analytical J 가 real RHS 의 derivative 와 1e-6 rel err 일치 |
| G4 CROSS | ⚠️ N/A | MB-95 `camb_rhs` 는 Jacobian 을 **computed numerically** (DVERK 가 explicit solver 라 J 불필요). Rodas5P 는 analytical 이지만 대응 MB-95 Jacobian 코드 없음. G4 포기 정당 |

**Score: 7/10** forecast.
- G1 ✅ + G3 ✅ (FD check 이 tight) → **cap 7** (G2 N/A 로 cap 8 미달, G4 없음)
- Weight 4 × 7/10 = **W·S/10 = 2.8**

Phase 1 진행률: 37.9% → **40.6%** (39.8 + 2.8)/105.

---

## §6. Anti-local-min triggers

1. **FD step size (h) 선택 실수** — h 가 너무 크면 truncation error, 너무 작으면 roundoff. 2회 fail 시 STOP + h 재조정. 5-point stencil 이 3-point 보다 truncation error 작음.

2. **Linear RHS 가정 위반** — PR-022b 의 collision 은 linear 이므로 J 는 state-independent 확인. Non-linearity 발견 시 `state` parameter 를 actual 하게 사용하도록 수정.

3. **Sparse 구조 오류** — ℓ_max truncation row 의 coefficient `−(ℓ_max+1)/τ` 는 PR-022a 에서와 동일 pattern. `τ` 를 inputs 에서 받아야 함 (free_streaming 과 동일).

---

## §7. Pre-PR checklist

- [x] Rodas5P 의 dense row-major Jacobian format 확인 (`rodas5p.rs:123-156`)
- [x] Sparse pattern 분석 완료 (§2.3)
- [x] FD check 5-point stencil 공식 확정 (§3.4)
- [ ] `h = 1e-6 · ||state||` 와 `h = 1e-8 · ||state||` 두 값으로 FD test, 더 안정한 것 선택
- [ ] ℓ=2 pol feedback test 는 pol-off default 로만 (PR-022b 동일)

---

## §8. 즉시 다음 행동

동일 turn 내 (1 turn completion):

1. **PR-022c scaffold** — `src/solver/pstf_primary/jacobian.rs` 신설
2. `JacobianInputs` + `SparseJacobian` + `pstf_analytical_jacobian` + `pstf_jacobian_dense` + `jacobian_fd_check` 구현
3. 9 tests 작성 (§4 specification)
4. FD check 가 main gate — rel err 수치 paste
5. D_2 10th consecutive bit-identical 재확인
6. `pr-022c.md` closure delta + scoreboard 갱신 (진행률 37.9% → 40.6%)
7. **PR-022 sub-track 전체 완결** — W·S/10 = 4.2 + 4.0 + 2.8 = **11.0** (원 target 12.0 의 91.7%)

---

*PR-022c 는 PR-022 sub-track 의 마지막. Analytical Jacobian 은 Rodas5P implicit solve 의 전제이므로 PR-024 production 통합 직전 필수. FD check 가 G3 의 핵심 evidence — MB-95 의 explicit solver 는 analytical J 없으므로 G4 N/A 정당.*
