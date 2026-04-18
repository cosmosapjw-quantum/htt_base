# AUDIT — Phase LB-2a (PSTF storage + orthogonal-subset RHS terms)

**Date**: 2026-04-19
**Phase**: LB-2a — `bass/hierarchy/` subpackage, ``PSTFTensor`` /
``PSTFHierarchyState`` + terms T1/T2/T3/T8/T9, closure/collision
interfaces, 154 new tests.
**Baseline commit**: `424ebcd` (pre-session)
**Baseline test count**: 2,141 passing
**Post-audit test count**: 2,295 passing (154 new)
**Verdict**: **통과** (one P1 doc-level drift fixed in-session; no
numerical or contract breakage)

---

## 1. Audit target reconstruction

| Layer | Artifact | Role |
|---|---|---|
| Physics/math source | Ellis §4.5-4.6, lowell §6, Pontzen-Challinor 2007 eq C4 | Nine-term 1+3 covariant PSTF hierarchy |
| PSTF storage | `bass/hierarchy/pstf_tensor.py` | rank-ℓ (2ℓ+1)-packed; tower container |
| Basis / STF projector | `bass/hierarchy/contractions.py` | Q_ℓ orthonormal basis, ℓ ≤ 8 precomputed |
| Term functions | `bass/hierarchy/terms.py` | T1, T2, T3, T8, T9 pure functions; T4-T7 stubbed |
| Closure hook | `bass/hierarchy/closure_interface.py` | HardCutClosure baseline |
| Collision hook | `bass/hierarchy/collision_interface.py` | ZeroCollisionOperator baseline |
| Tests | `bass/hierarchy/test_*.py` | H-01..H-17 + additional coverage |

Source of truth: `docs/lowell_bianchi/02_multipole_hierarchy_spec.md §1`
(nine-term formula) and `§11` (test criteria H-01..H-17). Code
generates values; hand-worked numerical targets at ℓ = 2 (T8 and T9)
pin the contraction + STF-projection path.

## 2. Contract / interface table

| API | Input contract | Output contract | Units |
|---|---|---|---|
| `PSTFTensor(ell, components)` | `components.shape == (2ℓ+1,)` enforced | float64 packed | — (depends on consumer) |
| `zero_pstf(ell)` | `ell ≥ 0` | all-zero tensor | — |
| `pstf_from_tensor(T)` | rank-ℓ ndarray, axes length 3 | PSTFTensor (STF-projects silently) | — |
| `pstf_to_tensor(t)` | PSTFTensor | rank-ℓ symmetric trace-free ndarray | — |
| `sym_trace_free(T)` | rank-ℓ ndarray, axes length 3 | STF ndarray, same shape | — |
| `T1_expansion(ℓ, Π, Θ)` | rank match; Θ scalar | rank-ℓ tensor | [Θ] = 1/Mpc (proper-time) |
| `T2_gradient(ℓ, Π_{ℓ−1}, nabla_op=None)` | nabla_op `kind='gradient'` | rank-ℓ tensor | — |
| `T3_divergence(ℓ, Π_{ℓ+1}, nabla_op=None)` | nabla_op `kind='divergence'` | rank-ℓ tensor | — |
| `T8_shear_same(ℓ, Π_ℓ, σ)` | σ shape (3,3); symmetric | rank-ℓ tensor | [σ] = 1/Mpc (proper σ_ab) |
| `T9_shear_down(ℓ, Π_{ℓ−2}, σ)` | σ shape (3,3) | rank-ℓ tensor | [σ] = 1/Mpc (proper σ_ab) |

Invariants: every ``pstf_to_tensor`` output passes
``verify_pstf_invariants`` (symmetric + trace-free on every pair),
tested at ℓ ∈ {2,3,4,5}; round-trip pack∘unpack = id within
``atol = 1e-14 × 3**ell`` (machine precision at low ℓ; ~7e-11 at
ℓ = 8 due to accumulated 6561-dim QR rounding).

## 3. Phys-math audit ledger

| Check | Result | Evidence |
|---|---|---|
| T1 prefactor ``(4/3) Θ`` | ✅ | `terms.py:155`; test `test_h13_T1_scales_linearly_in_theta` |
| T8 prefactor ``5ℓ/(2ℓ+3)`` | ✅ | matches spec §1; hand-worked ℓ=2 → 10/7 in `test_h12_T8_ell_2_axisymmetric_hand_value` |
| T9 prefactor ``−(ℓ+2)`` | ✅ | matches spec §1; hand-worked ℓ=2 → −4 in `test_h16_T9_ell_2_shear_injection` |
| σ = 0 limit: T8, T9 → 0 | ✅ | tested at ℓ ∈ {0..3} in `test_h17_flrw_sum_is_T1_only_at_background` |
| ω = A = 0 orthogonal: T4/T5/T6 dropped | ✅ | stubs raise `NotImplementedError`; no silent zero |
| Homogeneous background: T2, T3 → 0 | ✅ | `zero_nabla_operator` default; tested |
| PSTF projection: output symmetric + trace-free | ✅ | `test_T8_output_is_pstf_at_ell_3`, `test_T9_ell_3_output_is_pstf`, and H-05 / H-06 |
| STF basis orthonormality | ✅ | `Q^T Q = I_{2ℓ+1}` tested ℓ=0..8 |
| (2ℓ+1) dimension count | ✅ | explicit shape assertions; matches Arfken Ch 16 |
| Anti-symmetric input → 0 under STF projection | ✅ | `test_h10_antisymmetric_projects_to_zero`; Levi-Civita at rank-3 |

## 4. Equation-to-code mapping

| Spec formula | Code path | Hand-verification |
|---|---|---|
| `(4/3) Θ Π_{A_ℓ}` | `T1_expansion` — ``(4/3) * Theta * Pi`` | ℓ=2 unit × (4/3) |
| `σ^b_{⟨a_ℓ} Π_{A_{ℓ−1}⟩ b}` | `T8_shear_same` — ``np.tensordot(Pi, σ, axes=([-1],[1]))`` then STF | σ=Π=diag(−2,1,1)/√6 → (σσ)_STF = diag(1/3,−1/6,−1/6); × 10/7 matches |
| `σ_{⟨a_ℓ a_{ℓ−1}} Π_{A_{ℓ−2}⟩}` | `T9_shear_down` — ``np.tensordot(σ, Π, axes=0)`` then STF, × −(ℓ+2) | ℓ=2, Π₀=1 → −4 σ_{ab} (σ already STF) |
| `∇̃_{⟨a_ℓ} Π_{A_{ℓ−1}⟩}` | `T2_gradient` with pluggable `nabla_operator` | default `zero_nabla_operator` for homogeneous background |
| `((ℓ+1)/(2ℓ+3)) ∇̃^b Π_{A_ℓ b}` | `T3_divergence` — same hook | default zero |

No dead code, no silent fallbacks: deferred terms raise
`NotImplementedError` with explicit LB-2b pointers.

## 5. Numerical / pipeline audit

| Item | Finding |
|---|---|
| Import-time cost (STF basis cache ℓ=0..8) | ~0.1 s one-off; Q_ℓ ∈ R^{6561×17} at top rank (~110 KB) |
| Round-trip precision | ≤ 3×ε_mach at ℓ≤4; ~3^ℓ × ε_mach at ℓ≤8 (test atol scales) |
| STF basis orthonormality | `Q^T Q = I` to 1e-13 |
| PSTF invariants on basis columns | tr = 0 to 1e-12, symmetric to 1e-12 at every ℓ |
| Determinism | zero random state in production code; tests use fixed seeds |
| Overflow/underflow | no `exp`/`log` on physical quantities in this layer |
| Solver stiffness | N/A (pure algebraic layer) |

## 6. Ranked failure modes

| ID | Type | Severity | Summary | Action |
|---|---|---|---|---|
| **F1** | interface / doc | **P1** | `T8_shear_same` / `T9_shear_down` / `T1_expansion` docstrings did not specify whether `sigma_tensor` / `Theta` are proper-time (σ [1/Mpc], Θ=3H) or conformal (Σ, Hσ=Σ/a). Without explicit convention LB-2b driver could feed `TetradBackgroundState.sigma_tensor` (which is the Pontzen-Σ convention) and get a silent ``a`` factor wrong. | ✅ fixed in-session: docstrings now state "proper-time", reference `00_conventions.md §3`, and warn explicitly about `TetradBackgroundState.sigma_tensor` needing conversion in LB-2b |
| F2 | testing | P2 | Round-trip atol scales with `3**ell`; still machine-precision-ratio. No physics impact. | document via test docstring; left as-is |
| F3 | doc | P3 | `L_MAX_CACHED = 8` is a module constant but not clearly tagged as "recompile if you need ℓ > 8". | inline module docstring already describes "pre-built at import time"; sufficient |
| F4 | impl | P3 | `pstf_pack` silently strips non-STF content. Intentional (spec §2.3) but could surprise a user passing a non-STF tensor expecting an error. | documented in `pstf_pack` docstring ("any non-symmetric-trace-free content is silently projected away") |

## 7. Verifier results

| Verifier | Result | Notes |
|---|---|---|
| Physics (formula + limits) | **PASSED** | T1/T8/T9 match spec prefactors; σ=0 and FLRW limits reproduce; hand-worked ℓ=2 values pin contraction interpretations |
| Code (contract satisfaction) | **PASSED** | shape validation enforced; all docstrings cite Ellis/lowell/Pontzen-Challinor; F1 interface units ambiguity fixed in-session |
| Numerical (stability + regression) | **PASSED** | 2,295 / 2,295 tests green; Q_ℓ orthonormal to 1e-13; round-trip at ε_mach |

## 8. Minimal repair plan — applied in-session

| Patch | Target | Status |
|---|---|---|
| A | `T1_expansion` docstring: tag Θ as proper-time (3H_mpc), cross-reference `00_conventions.md §3` and `FLRWBackgroundTable.Theta`. Prevents accidental substitution of conformal Hubble 𝓗 = aH. | ✅ `bass/hierarchy/terms.py:155-165` |
| B | `T8_shear_same` docstring: tag `sigma_tensor` as proper-time σ_ab (1/Mpc), explicit warning that `TetradBackgroundState.sigma_tensor` is Σ_ab (conformal) and needs a 1/a conversion in LB-2b driver. | ✅ `bass/hierarchy/terms.py` |
| C | `T9_shear_down` docstring: mirror of Patch B for T9. | ✅ `bass/hierarchy/terms.py` |

No code behaviour changed — these are doc-only patches. Tests unchanged; all 2,295 pass.

## 9. Minimal test set (delivered as part of LB-2a — 154 tests)

Baseline reproduction: `test_h13_T1_unit_quadrupole`, `test_h16_T9_ell_2_shear_injection`, `test_h12_T8_ell_2_axisymmetric_hand_value` — pass criterion `atol = 1e-13` against hand-worked numbers.
Edge / adversarial: `test_h15_T9_at_ell_{0,1}_is_zero`, `test_pstf_pack_wrong_axis_raises`, `test_h03_pstf_wrong_shape_raises`, `test_T4/T5/T6/T7_raises_not_implemented`.
Physics sanity: `test_h17_flrw_sum_is_T1_only_at_background` — σ = 0 + homogeneous → only T1 survives at every ℓ.
Numerical stability: `test_basis_is_orthonormal[ell=0..8]`, `test_pstf_pack_roundtrip[ell=0..8]`, `test_basis_columns_are_symmetric_and_trace_free[ell=2..8]`.
Regression: full bass+tsc run — **2,295 green** (baseline 2,141 + 154 new).

## 10. 최종 판정

* **치명적 오류 있음 / 부분 통과 / 통과** → **통과** (P1 F1 doc-drift fixed in-session; no numeric regression)
* **지금 당장 구현/수정한 1개**: F1 — proper-time σ_ab / Θ units now explicit in term docstrings. Without this, LB-2b risks feeding `TetradBackgroundState.sigma_tensor` (Pontzen-Σ) directly into T8/T9 and missing a 1/a factor silently.
* **지금 손대면 안 되는 1개**: adding a runtime units-assertion on `sigma_tensor` (e.g., via a wrapper dataclass `ProperShear`). Invasive for a pure-function layer; defer to LB-2b where units are consumed through the driver.

## Outstanding items carried forward

* **F2** (P2): round-trip atol scaling — documented in test; no action.
* **F3** (P3): `L_MAX_CACHED = 8` discoverability — left inline; reassess if LB-6 pushes ℓ > 8.
* **F4** (P3): `pstf_pack` silent-strip semantics — already documented; leave for user diligence.
* **LB-2b prerequisite**: driver must convert `TetradBackgroundState.sigma_tensor` → proper σ_ab by dividing by `a` at each η (or use an on-grid `sigma_proper_tensor` that the driver materialises).
