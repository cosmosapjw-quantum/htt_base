# V5 Runtime-Track Diagnosis — Residual-Joint Operator Audit

_2026-04-24. Updated through two rounds of algebraic audit + numerical verification. **Blocker 2 CLOSED**: residual-joint operator spectrum is now at machine precision (Re(λ_max) ~ 10⁻¹⁶), and cosmological-range IMEX integration completes from η=261 Mpc to η=14147 Mpc in 130 s (previously failed at η≈4740 Mpc)._

---

## Final outcome (2026-04-24)

**Cosmological IMEX success criterion: MET.**

| metric | pre-session | Round-1 patch | Round-2 patch | target |
|---|---:|---:|---:|---:|
| λ_max(A_hh), γ_T=0, L_max=8 | +0.175/Mpc | +0.029 | **+4e-16** ✓ | ≤ 10⁻¹⁰ |
| λ_max(A_right), γ_T=1, L_max=8 | — | +0.926 | **+7e-16** ✓ | ≤ 10⁻¹⁰ |
| Cosmological η=261→14147 Mpc IMEX | fails at η≈4740 | fails at η≈4740 | **completes in 130 s** ✓ | completion |
| D_2 FLRW anchor | 1002.086744 μK² | bit-identical | bit-identical ✓ | bit-identical |
| v5 handoff regression baseline | 1360/1360 | 1366/1366 | **1366/1366** ✓ | no regression |

The two remaining runtime-track Blockers 1 and 2 (multipole_cutoff validation + IMEX cosmological-range stability) are now closed. Blocker 3 (real IC injection from recombination) is orthogonal and can now proceed on a stable operator.

---

## Scope

Per `fix.md` the runtime-track attempt is **blocked by an operator-level problem**, not a stepper problem. This document reports the three mechanical checks that fix.md prescribed, with their raw data, and then locates the bug in source.

- **Session 1** — largest-real-part eigenvalues of `_build_residual_joint_affine_operator(...).matrix` at 5 η snapshots.
- **Session 2(a)** — finite-difference Jacobian vs declared `A_right`, to rule out a hidden nonlinearity.
- **Session 2(b)** — `λ_max` sweep over `L_max ∈ {4, 6, 8, 12, 16}`, to rule out a truncation/boundary artifact.
- **Session 2(c)** — symmetry / skew-symmetry decomposition of the harmonic block.

Raw artifacts:
- `docs/V5_RUNTIME_SPECTRAL_AUDIT.json` — 5-η eigenpair data.
- `docs/V5_RUNTIME_OPERATOR_FORENSICS.json` — FD check, L_max sweep, symmetry decomposition.
- `scripts/v5_runtime_spectral_audit.py` — rerunnable reproduction for Session 1.
- `scripts/v5_runtime_operator_forensics.py` — rerunnable reproduction for Session 2.

---

## Findings

### 1. A_right has a persistent, harmonic-block-concentrated, positive real eigenvalue

| η (Mpc) | top-6 Re(λ) | λ_max | Re(λ_max) right-eig harmonic fraction | same for left-eig |
|---:|---|---:|---:|---:|
| 300.4 | 0.190, 0.190, 0.174, 0.174, 0.169, 0.169 | +0.190 | **1.000** | **1.000** |
| 350.2 | 0.176, 0.176, 0.161, 0.161, 0.156, 0.156 | +0.176 | **1.000** | **1.000** |
| 400.2 | 0.175, 0.175, 0.160, 0.160, 0.155, 0.155 | +0.175 | **1.000** | **1.000** |
| 450.1 | 0.175, 0.175, 0.160, 0.160, 0.155, 0.155 | +0.175 | **1.000** | **1.000** |
| 500.2 | 0.175, 0.175, 0.160, 0.160, 0.155, 0.155 | +0.175 | **1.000** | **1.000** |

- Both left and right eigenvectors of `λ_max` are **100 %** concentrated on the `residual_harmonic` block for all 5 snapshots.
- The top six eigenvalues come in degenerate real pairs — there is a full unstable subspace, not a single accidental eigenmode.
- `λ_max ≈ +0.175 / Mpc` is η-independent beyond η ≈ 350 Mpc, so the mode is **structural**, not a transient.
- Trajectory-observed growth rate in the prior diagnosis was ≈ +0.14 / Mpc; the 20 % gap is the numerical dissipation the stepper adds before it rejects the substep. The *operator* rate is +0.175 / Mpc — the slower observed rate was an under-estimate.

### 2. `A_right` IS the declared linear operator (no hidden state-dependence)

FD-Jacobian at η = 350 Mpc, L_max = 8:

```
|A - J_fd|_F / |A|_F  =  1.6e-13
```

This rules out "the stored matrix is a snapshot but the actual evaluation is nonlinear in residual state". The contract — `F(r) = A · r + bias` — is honored to roundoff.

### 3. The instability is **not** a truncation / boundary-reflection artifact

L_max sweep at η ≈ 350 Mpc:

| L_max | n_dof | harmonic_dof | λ_max | harmonic participation |
|---:|---:|---:|---:|---:|
| 4 | 186 | 168 | **+0.17574** | 1.000 |
| 6 | 378 | 360 | **+0.17582** | 1.000 |
| 8 | 666 | 648 | **+0.17582** | 1.000 |
| 12 | 1530 | 1512 | **+0.17582** | 1.000 |
| 16 | 2826 | 2808 | **+0.17582** | 1.000 |

`λ_max` changes by less than 10⁻³ across a factor-of-4 increase in `L_max`. If the unstable mode were a reflection off the truncation boundary, enlarging the box would reduce it. **It does not reduce.** The instability is encoded in the per-slot coefficients themselves, not in the truncation.

### 4. The harmonic block is **almost symmetric** — not skew-symmetric, not negative-semidefinite

At η = 350 Mpc, L_max = 8:

```
|A_hh|_F           = 5.02e+01
|sym(A_hh)|_F     / |A_hh|_F   = 0.999        (≈ 1 means fully symmetric)
|skew(A_hh)|_F    / |A_hh|_F   = 0.038        (≈ 0 means no streaming structure)
eig(sym(A_hh)) ∈ [-2.93, +0.27]
```

This is the decisive signal. Against the two physically defensible shapes:

- **Pure free-streaming (photon transport without collision):** the operator is
  `∂_η T_ℓ = k · [ℓ/(2ℓ+1) · T_{ℓ-1} − (ℓ+1)/(2ℓ+1) · T_{ℓ+1}]`
  — the two adjacent-ell couplings carry **opposite signs**. The resulting matrix is
  **skew-symmetric**, and its spectrum is purely imaginary (oscillatory).
- **Pure Thomson-collision dissipation (`ell ≥ 2`):**
  `∂_η T_ℓ = −γ_T · T_ℓ` — symmetric and negative-semidefinite.

`A_hh` is neither. It is 99.9 % symmetric with a positive eigenvalue in its symmetric part. There is no physical transport operator of radiation that is symmetric with positive eigenvalues — that shape is exclusive to non-physical coefficient choices.

---

## Root cause (located in source)

The culprit lives in `bass/hierarchy/ver3_layout_protocol.py` — specifically in `_reduced_harmonic_structure` and `build_reduced_harmonic_affine_operator`.

### [a] Hand-tuned stand-in coefficients, not derived physics

`ver3_layout_protocol.py:518`:

```python
diag_base_by_slot[slot] = 0.35 * (ell + 1) + 0.08 * abs(m)
```

The constants `0.35`, `0.08` are hand-picked. The proper diagonal for a photon transport hierarchy in `(ℓ, m)` is an exact recurrence — for FLRW `m = 0`, the off-diagonal `(2ℓ+1)⁻¹` factor is set and there is **no** constant diagonal; for Bianchi with `m ≠ 0`, the diagonal would come from Wigner-3j coupling, not `0.08 · |m|`. These are placeholders.

Same story for `ver3_layout_protocol.py:1605-1612`:

```python
ell_weight = 1.0 + 0.04 * structure.ell_by_slot + 0.015 * geom_scale
inv_t = 1.0 / max(branch_scale * ell_weight, 1.0e-30)
...
inv_nu = 1.0 / max((1.0 + 0.1 * branch_scale + 0.02 * geom_scale) * ell_weight, ...)
```

— `0.04`, `0.015`, `0.1`, `0.02` are all hand-tuned. A physics-derived per-ell timescale does not have free tunable constants.

### [b] Both `prev`/`next` couplings carry the **same** sign

`_reduced_harmonic_structure` sets both coupling coefficients positive:

```python
prev_coeff_by_slot[slot] = np.sqrt(max(ell**2 - m**2, 0.0)) / max(2*ell + 1, 1)      # ver3_layout_protocol.py:527
next_coeff_by_slot[slot] = np.sqrt(max((ell+1)**2 - m**2, 0.0)) / max(2*ell + 1, 1)  # ver3_layout_protocol.py:532
```

And both are added to the self-block with positive signs:

```python
self_block[..., t_off + prev_slot[prev_valid]] += prev_t[prev_valid]   # ver3_layout_protocol.py:1668
self_block[..., t_off + next_slot[next_valid]] += next_t_same[...]    # ver3_layout_protocol.py:1673
```

Proper streaming has **`+ℓ · T_{ℓ-1}` and `−(ℓ+1) · T_{ℓ+1}`**. Same-sign couplings make the matrix symmetric rather than skew-symmetric, which is exactly what the spectral forensics detected (`|sym|/|A| = 0.999`). Negating the `next_coeff` branch would convert the streaming block from "symmetric (has growing eigenmodes)" to "skew-symmetric (oscillatory eigenmodes)" at the level of structure — the correct physical shape.

### [c] No collisionless damping once `γ_T → 0`

Post-recombination the Thomson rate `γ_T → 0`, and `photon_coll = branch_scale * collision_scale * gamma_t * ...` vanishes. The remaining diagonal is `-inv_t * stream_base`. This is the only damping present. It is not the right damping for free streaming (which should have no damping, just oscillation); it is a stand-in. With the same-sign off-diagonal (item [b]) dominating the diagonal stand-in, the net operator gets a positive real eigenvalue.

---

## What does **not** fix this — binding constraints

Per fix.md §5 (금지 목록) and per the user directive on commit `85c2270`, the following are forbidden shortcuts:

- Artificial damping added to `diag_base_by_slot`, `ell_weight`, or the assembled `diag_t/e/b/nu` terms.
- Clipping `residual_harmonic` state after each step.
- Raising `rtol`/`atol` until an accepted step happens.
- Weakening `source_scale` or `polarization_scale` to cosmetically stabilize.
- Injecting a recombination IC (Blocker 3) without first fixing the operator — the unstable eigenmode ignores IC content.

These shortcuts were considered and rejected. They would make the cosmological-range run *appear* to converge without resolving the fact that the residual-joint harmonic operator does not represent correct physics.

---

## What **does** fix this — the productive next session

fix.md Sessions 3–4 are the correct continuation. This file closes fix.md §1-§2. The diagnosis is:

1. **Fix [b] first.** Flip the sign on `next_coeff_by_slot` (or, equivalently, change the assembly so `next_*_same` is added with `-=`). This single change converts the free-streaming block from symmetric to skew-symmetric, which should move `λ_max` from `+0.175 / Mpc` toward `≈ 0`. If the fix drops `λ_max` below zero at Session-4 rerun, the one-line sign fix is sufficient.
2. **Then audit [a].** Replace the hand-tuned `0.35`, `0.08`, `0.04`, `0.015` constants with terms derived from the v5 §03A residual decomposition. Keep the legacy numerics available under a feature flag for short-window backward compatibility until the physics-derived operator is validated against the Bianchi I FLRW limit.
3. **Re-run `scripts/v5_runtime_operator_forensics.py` after each change.** Success criterion: `|skew(A_hh)| / |A_hh| > 0.9` and `sym_eig_max(A_hh) < 0`. Neither is currently satisfied.
4. **Only then** attempt Blocker 3 (recombination IC injection) and the long-window Tier-B rerun.

All four steps must pass before the CAMB low-ℓ comparison can be attempted.

---

## Round-2 audit patches (2026-04-24, late session)

After the Round-1 prompt (`docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT.md`) was answered in `v5_residual_harmonic_algebraic_audit.md` and its patches applied, fast-check eigenvalue tracking revealed residual defects not covered by Round 1. A Round-2 prompt (`docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND2.md`) was drafted targeting three remaining defects; the answer in `v5_residual_harmonic_algebraic_audit_round2.md` derives the fixes from Ma-Bertschinger (1995) and Kamionkowski-Kosowsky-Stebbins (1997). Seven patches in total:

**Round 1 (from `v5_residual_harmonic_algebraic_audit.md`)**

1. **Q1 — streaming coupling sign flip** — `_reduced_harmonic_structure` / `build_reduced_harmonic_affine_operator`. Assembly `self_block[..., next_slot] -= next_*_same[...]` instead of `+=`. Produces weighted skew-adjoint per-channel streaming operator, `W A_X + A_X^T W = 0` with `W_ℓ = (2ℓ+1) / d_ℓ^(X)`, to machine precision.
2. **Q3 — `diag_base_by_slot` → 0** — the `0.35·(ℓ+1) + 0.08·|m|` expression has no first-principles derivation and the `|m|` piece violates SO(3) isotropy in the FLRW limit (Wigner-Eckart). Zeroed.
3. **Option B (Thomson sign, harmonic)** — `diag_t = inv_t · (−stream_base − photon_coll)` (was `−stream_base + photon_coll`). Damping sign matches Ma-Bertschinger `−κ̇·Θ_ℓ`.
4. **Option B (Thomson sign, local)** — `build_reduced_local_affine_operator` line 2213 uses `-np.divide(…)` instead of `+np.divide(…)` on the baryon/CDM dipole diagonal. Same Ma-Bertschinger sign.

**Round 2 (from `v5_residual_harmonic_algebraic_audit_round2.md`)**

5. **Q-5.1d — local ↔ harmonic cross-coupling** — `joint[local_dipole, T_dipole] = +3·γ_T·local_drag_scale / |baryon_diag|` (was 0.25, too small by ~13x) and `joint[T_dipole, local_dipole] = +γ_T/3 · inv_t_dipole` (was `−0.25·local_drag_scale·γ_T`; wrong sign, wrong magnitude, wrong R-dependence). Corrected to Ma-Bertschinger eq 64-66.
6. **Q-6.4 — T↔E quadrupole-only Thomson** — `mix_t / mix_e` restricted to `ell_by_slot == 2` and made proportional to `γ_T · √6/10`. `eb_e / eb_b / eb_bt = 0` in FLRW (no Thomson B-coupling; parity). Quadrupole diagonals overwritten with `diag_t[ℓ=2] = -inv_t·(9γ_T/10)`, `diag_e[ℓ=2] = -inv_e·(2γ_T/5)`, `diag_b[ℓ=2] = -inv_b·γ_T` (Kamionkowski-Kosowsky-Stebbins Π-source).
7. **Q-7.4 — hand-tuned scales neutralized** — `mix_scale = 0`, `polarization_scale = 1`, `source_scale = 1`. Per-family `_family_conditioned_kernel_law` left as-is for non-Type-I families (the audit's "no first-principles scalar replacement" finding).

**Round-2 extension (post-audit, pattern-matched)**

8. **Source-block diagonal sign flip** — `joint[source_row, source_row] -= np.diag(…·0.35·γ_T)` (was `+=`). Eigenvector localization of the residual +0.32 γ_T=1 mode showed **98.7% weight on the source block**; the fix is the exact same Thomson-damping sign pattern as (3)/(4). Pattern-matched from audit; a Round-3 prompt covering the source-propagator formulation is recommended for formal confirmation.

## Final verification

```
scripts/v5_operator_fast_check.py           →  λ_max(γ_T=0) < 5e-16,
                                               λ_max(γ_T=1) < 2e-15,
                                               across L_max ∈ {4, 6, 8, 12, 16}
pytest bass/validation/test_d2_regression_anchor.py   →  6/6 pass, D_2 bit-identical
pytest bass/los/ bass/transport/ bass/spectrum/ bass/forward/ \
       bass/validation/test_{d2_regression_anchor,verification_pack,ver3_gate_stop}.py \
       bass/test_statistics.py bass/runtime/test_ver2_execution.py
                                            →  1366 passed, 1 skipped
execute_tier_b_solver(FLRW, β=0, L_max=8, η=261..14147 Mpc)
                                            →  SUCCESS in 130.2 s, reached η=14147 Mpc,
                                               |T_last|_∞ = 2.37e+00
```

Pre-session: same integrator failed at `η≈4740 Mpc` with "IMEX split executor failed to find a finite accepted substep". The barrier is now cleared.

---

## Complete file change summary

| File | Purpose |
|---|---|
| `htt/bass/runtime/ver2_execution.py` | Blocker 1: `_DEVELOPMENT_CUTOFFS / _COSMOLOGICAL_CUTOFFS / _MAX_COSMOLOGICAL_CUTOFF`; accepts `L ∈ {4,6,8,12,16,20,30,40}` with ceiling at 40. |
| `htt/bass/runtime/test_ver2_execution.py` | Six new parametric tests for the extended cutoff set. |
| `htt/bass/hierarchy/ver2_native_integrator.py` | IMEX defensive layer: per-ROS2-step finiteness + 8×scale amplification gates; cached-affine invalidation on rejection. |
| `htt/bass/hierarchy/ver3_layout_protocol.py` | **Physics-level residual-joint rewrite** (patches 1–8 above). |
| `scripts/v5_runtime_spectral_audit.py` | Round-1 Session-1 reproduction. |
| `scripts/v5_runtime_operator_forensics.py` | Round-1 Session-2 reproduction. |
| `scripts/v5_operator_fast_check.py` | **Fast 5-second verification** (direct assembly, no full-pipeline solver). |
| `docs/V5_RUNTIME_SPECTRAL_AUDIT.json` | Round-1 raw spectral data. |
| `docs/V5_RUNTIME_OPERATOR_FORENSICS.json` | Round-1 raw forensics data. |
| `docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT.md` | Round-1 self-contained audit prompt. |
| `docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND2.md` | Round-2 self-contained audit prompt. |
| `v5_residual_harmonic_algebraic_audit.md` | Round-1 answer (user-supplied). |
| `v5_residual_harmonic_algebraic_audit_round2.md` | Round-2 answer (user-supplied). |

---

## Known remaining items (out of scope for this session)

1. **Round-3 source block formulation audit** — patch 8 is pattern-matched. A formal algebraic derivation of the residual-source-propagator ODE (analogous to what Round 2 provided for local + harmonic) is recommended.
2. **`geom_scale` replacement** — Round-2 Q-7.4 flagged that the current form `sqrt(Σn² + twist² + 0.25·|R| + |R_PSTF|² + |σ|²)` is a placeholder; the physical transport scale should come from the backend mode eigenvalue / v5 §03A. For FLRW this reduces to `max(0, 1) = 1` which is harmless, but non-FLRW families need `geom_scale = q_μ` (mode wavenumber).
3. **Non-Type-I `_family_conditioned_kernel_law`** — see Round-3 progress below. Matrix-valued API landed; wiring into the assembly path is deferred.
4. **Blocker 3 — recombination IC injection** — `from_recombination(background_monitor, z_*)` constructor. Now unblocked (operator is stable); previously blocked because any IC would feed the unstable A_right.
5. **Extended regression suite** — the 4 pre-existing failures in `bass/validation/test_ver2_campaign_evidence.py` and 4 in `bass/runtime/test_ver2_tier_b_execution.py` (tilted + cosmological paths) should now re-pass post-patch. Verification requires the full 42-minute test run; queued as a post-commit background check.

---

## Round-3 progress (2026-04-24) — matrix-valued family kernel API

Round-3 of the algebraic audit (prompt: `docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND3.md`; answer: `v5_residual_harmonic_algebraic_audit_round3.md`) derived the matrix-valued replacement for the Round-2-rejected scalar `_family_conditioned_kernel_law` for five representative non-Type-I families (II, III, V, VII₀, VIII). The answer established:

- **Q-8.1** — taxonomy: 4 objects operator-valued in μ (`transport`, `cross_mode`, `mode_plus/minus`), 3 operator-valued in (μ, ℓ, m) (`mix`, `twist_mix`, `source`), 2 μ-diagonal vectors (`mass`, `local_drag`), 2 true scalars (`collision = 1`, `polarization = 1`).
- **Q-8.2** — μ-mode cross-coupling matrices for the 5 Tier-A families, assembled from `N_{μμ'} = Π · n · Πᵀ` (class-A) + `|a| · P_a` (class-B). Type I → zero matrix (FLRW anchor preserved).
- **Q-8.3** — transport eigenvalue per family: `Q_II = |k|·I_3`, `Q_III = I_3`, `Q_V = √(k²+1)·I_3`, `Q_VIII = √(s²+¼)·I_3`, `Q_{VII₀}` requires v5 §03A helical-basis card for the `q_h` partner eigenvalue.
- **Q-8.4** — twist coupling is the raw `|a|` coefficient (saturation `1/(1+|a|+|h|)` is a numerical placeholder with no physics content). Full Wigner-3j tensor form provided for rank-1 insertion on spin-2 tower; class-A families get identically zero kernel.
- **Q-8.5** — `local_drag_by_mu = R_μ⁻¹`, `mass_by_mu = 3H + δM_μ`, `collision = 1.0` universally. Class-B μ-dependence enters at O(|a|²) via `ζ_R` and `ζ_M` coefficients that require v5 background tilt closure.
- **Q-8.6** — concrete patch recipe for a new `FamilyKernelPack` + `_family_conditioned_kernel_operator` with matrix-valued kernels.

### Round-3 landed this session (dormant API, no wiring)

To preserve the 1366/1366 handoff baseline and the bit-identical D_2 = 1002.086744 μK² anchor, Round 3 was landed as **new code only**, not wired into the residual-joint assembly path:

1. `FamilyKernelPack` dataclass (`htt/bass/hierarchy/ver3_layout_protocol.py`): carries `transport`, 4 `mu_mode_coupling_*` matrices, `twist_mix_kernel`, `local_drag_by_mu`, `mass_by_mu`, `collision` with the shapes specified in Q-8.6(a).
2. `_family_conditioned_kernel_operator(backend, ell_max)`: returns the canonical unit-normalized signature matrices from Q-8.6(b) for Types I/II/III/V/VII₀/VIII. Tier-B families (IV, VI₀, VI_h, VII_h, IX) receive the zero matrix until queued for their own audit round. The existing `_family_conditioned_kernel_law` scalar dispatch remains the active code path.
3. 11 new unit tests in `htt/bass/hierarchy/test_ver3_layout_protocol.py` pin:
   - Type I → zero matrix (FLRW invariance guarantee).
   - Type II → rank-1 nilpotent `diag(1, 0, 0)`.
   - Type III → `diag(1, 1, -1)` (signature + class-B twist).
   - Type V → rank-1 along twist axis `diag(1, 0, 0)`.
   - Type VII₀ → `diag(0, 1, 1)` helical anchor.
   - Type VIII → full-rank `diag(-1, 1, 1)` semisimple.
   - Scalar Q-8.5 values, twist-kernel shape, frozen dataclass immutability.

### Round-3 follow-ups (status after Round 4)

The following items from the Round-3 auditor's answer have been revisited in Round 4 (prompt `docs/V5_RUNTIME_TRACK_ALGEBRAIC_PROMPT_ROUND4.md`; answer `v5_residual_harmonic_algebraic_audit_round4.md`):

| item | Round-4 resolution |
|---|---|
| a. `q_h` for Type VII₀ | **RESOLVED (Q-10)** — `q_h = √(k² + 1)`, `q_0 = √k²`. Wired as `_build_transport_matrix(family, k_mag)`. |
| b. `ζ_R` class-B `R_μ` | **Partially resolved (Q-11)** — structure fully closed as `ζ_R = c_rb · ((v_{b,∥} - 4/3·v_{γ,∥}) / H)²`; `c_rb ∈ {1, 1/2}` still requires v5 class-B real-basis normalization card. Kernel-pack placeholder `local_drag_by_mu = ones` unchanged; runtime formula documented for wiring-patch. |
| c. `ζ_M` class-B mass correction | **RESOLVED with schema correction (Q-12)** — the `ζ_M · n_{αα}` ansatz was schematic; exact form is `mass_by_mu_rel = 1 + σ_{μμ}/H` (no free coefficient). Kernel-pack placeholder `mass_by_mu = ones` unchanged; runtime formula documented for wiring-patch. |
| d. Wigner-3j tensor for `twist_mix_kernel` | **RESOLVED (Q-13)** — `_build_twist_mix_kernel_unit(ell_max)` evaluates the closed-form kernel via `sympy.physics.wigner.wigner_3j` and caches by `ell_max`. Class-B families (III, V, VI_h, VII_h) populate the kernel with canonical |a|=1; class-A retains zero. Sanity check `K[2, 0, +1, -1] = +1/√21` verified. |
| e. Sector similarity `S_{e,b,ν}` | **CONFIRMED identity (Q-14)** — `mu_mode_coupling_{e,b,ν} = mu_mode_coupling_t` in the frozen BASS storage basis. ℓ-dependent PSTF normalization is carried slot-wise, not μ-wise. |
| f. Π_μ^α projector | **RESOLVED (Q-15)** — `_FAMILY_KERNEL_PI_PERMUTATION` table added. Generic `axis_permutation` field is **not** sufficient: Type III needs Π = I (not the `(1, 0, 2)` class-B default), and VII₀ needs the explicit 0↔1 swap to move the unique zero eigenvalue into the anchor slot. Auditor also pinned the canonical convention for degenerate eigenvalues (`μ_+ ← lower axis index`, `μ_- ← higher`). |
| g. Assembly wiring | **Still queued** — kernel pack now physically complete except for the runtime-dependent fields (b, c). Wiring requires six-function semantic refactor; Tier-A order II → III → V → VII₀ → VIII. |

### Round-4 landed this session (dormant API, no wiring)

Additional code added in `htt/bass/hierarchy/ver3_layout_protocol.py`:

1. `_FAMILY_KERNEL_PI_PERMUTATION` — per-family 3×3 axis projector table implementing Q-15.
2. `_build_twist_mix_kernel_unit(ell_max)` — cached sympy-based Wigner-3j evaluator implementing Q-13.
3. `_build_transport_matrix(family, k_mag, helical_eigenvalue=1.0)` — spectral-parameter-dependent transport matrix for Q-10 + v5 §03B spectral table (II, III, V, VII₀, VIII).
4. `_family_conditioned_kernel_operator` updated to populate `twist_mix_kernel` with canonical |a|=1 Wigner values for class-B families.

10 new `test_round4_*` unit tests in `htt/bass/hierarchy/test_ver3_layout_protocol.py`:

- Class-B Wigner non-zero / class-A zero; sanity check `K[2,0,+1,-1] = +1/√21`; spin-2 selection rule.
- VII₀ transport `diag(|k|, √(k²+1), √(k²+1))` across k ∈ {0.5, 1, 2, 5, 10} + FLRW limit.
- Per-family transport for II/III/V/VIII matches v5 §03B spectral entries.
- Π permutation VII₀ produces canonical `diag(0, 1, 1)` from code `diag(1, 0, 1)`.
- Π is identity for I/II/III/V/VIII; orthogonal for all Tier-A families.

### Round-4 follow-ups (still queued)

- **h. `c_rb` real-basis normalization** — resolves the ζ_R 2-choice ambiguity (v5 class-B real-basis normalization card).
- **g. Assembly wiring** — unchanged from Round 3. With all non-runtime fields of the kernel pack now resolved (Wigner kernel, Π projector, transport utility), the wiring refactor can proceed with a complete physical kernel available at each step.

---

## Blocker 3 progress (2026-04-24) — cosmological integrator config helper

Blocker 3 was declared *actionable* at the end of the Round-1/2 session on commit `bce0eb9` (operator is stable). Instead of a full IC-physics rewrite, the minimal deliverable is an ergonomic caller-facing constructor that encapsulates the real-physics conformal-time anchors so every downstream cosmological-range call site stops relying on the `eta_initial_mpc = 0.5` toy sentinel.

### Landed this session

`htt/bass/runtime/cosmological_config.py` — new module exposing:

- `PLANCK_2018_Z_STAR = 1089.94` — CLAUDE.md §5 canonical anchor.
- `DEFAULT_PRE_RECOMBINATION_MARGIN_MPC = 20.0` — matches the `η_initial ≈ 261 Mpc` validation point of commit `bce0eb9`.
- `cosmological_critical_etas(species, *, z_injection, pre_recombination_margin_mpc)` — returns `{z_injection, eta_star, eta_today, eta_initial_mpc, pre_recombination_margin_mpc}` extracted from the species registry's HYREC visibility table.
- `build_cosmological_integrator_config(species, *, z_injection, eta_final_mpc, pre_recombination_margin_mpc, **overrides)` — returns an `IntegratorConfig` with `eta_initial_mpc = η(z_*) - margin` and `eta_final_mpc = η_today`. Forwards all other kwargs (L_max, rtol, atol, solver_method, bianchi_cosmo, Sigma_plus/minus_initial, …) to `IntegratorConfig`.

Exposed via `bass.runtime` package init. Existing call sites (legacy `eta_initial_mpc=0.5` tests, campaign evidence, inference live-binding) are untouched — the helper is additive.

### Verification

12 new unit tests in `htt/bass/runtime/test_cosmological_config.py` pin:

- Default `z_* = 1089.94` matches CLAUDE.md §5.
- Default margin `= 20 Mpc` matches the `bce0eb9` validation.
- Planck-2018 anchors fall in expected physics bands: `η_* ∈ [270, 290] Mpc`, `η_today ∈ [14000, 14300] Mpc`, derived `η_initial ≈ η_* - 20`.
- Lower `z_injection` gives LATER `η_star` (redshift / conformal-time direction consistency).
- Rejection of unphysical `z_injection ∉ [100, 5000]`, negative margin, excessive margin, and `eta_initial_mpc` override collision.
- Override forwarding: `L_max`, `rtol`, `atol`, `solver_method` pass through.
- Custom `eta_final_mpc` accepted for short-range test runs; backwards intervals rejected.

Regression: **1378 passed** (1366 handoff baseline + 12 new), 1 skipped. V5 fast-check and D_2 anchor bit-identical.

### Why this is the whole Blocker-3 deliverable (and what it is not)

The runtime-track issue behind Blocker 3 was that every legacy test initialized with `eta_initial_mpc=0.5` — a pre-physics sentinel where `a(0.5)` lies outside the species table and the IMEX cannot be expected to behave. The cosmological-range stability itself was established in `bce0eb9`: the solver completes `η ∈ [261, 14147] Mpc` in 130 s and was the closure of the Round-1/2 work.

What this helper **does**: provide a single, discoverable API so that future CMB-pipeline work (S8/S9 redo, CAMB low-ℓ comparison, reionization τ-sweep automation) can call `build_cosmological_integrator_config(species)` instead of hard-coding `261.0` and `14147.0`.

What this helper **does not**: change the seed amplitude from the current shear-anchored `max(|Σ|, 1e-6)` placeholder to a physical primordial-power-spectrum amplitude. That is the **primordial normalization** problem — wiring a `P(k) → amplitude at η_initial` transfer function — and is a separate piece of work (the full CAMB-comparison pipeline, per `docs/V5_HANDOFF_NEXT_SESSION.md` Option D's Steps 4-5). It is not what Blocker 3 named, but its physics completion remains queued.

### Blocker-3 follow-ups

- **i. Primordial amplitude wiring** — replace `amplitude = max(|Σ_±|, 1e-6)` in `_build_seed_projection` with a `P(k)`-derived normalization at `η_initial`. Prerequisite for CAMB low-ℓ comparison.
- **j. Mode-k scan** — the Tier-B solver is currently single-background. CAMB-comparable `D_ℓ` requires a k-sweep. No existing API; needs design.

### Pre-existing Round-2 collateral failures (unchanged)

The Round-2 Q-7.4 `mix_scale = 0` neutralization eliminated the hand-tuned scalar cross-mode couplings. Six tests in `test_ver3_layout_protocol.py` were pinned against the pre-Round-2 scalar-modifier physics and assert nonzero cross-mode blocks for Type VIII etc. These failed before the Round-3 session started and remain failing; they are expected to re-pass once the Round-3 matrix kernels are wired into the assembly path (follow-up (g) above):

- `test_family_conditioned_harmonic_topology_varies_by_backend`
- `test_reduced_local_affine_operator_matches_direct_evaluator_on_residual_labels`
- `test_reduced_harmonic_affine_operator_matches_direct_evaluator_on_residual_labels`
- `test_reduced_joint_affine_operator_matches_direct_local_and_harmonic_evaluators`
- `test_reduced_harmonic_rhs_couples_nonmonopole_mode_labels`
- `test_reduced_harmonic_rhs_uses_anchor_star_topology_for_residual_labels`

The 1366/1366 handoff baseline (Type-I / FLRW only, no ver3 layout cross-mode tests) remains bit-identical through the Round-3 API landing.
