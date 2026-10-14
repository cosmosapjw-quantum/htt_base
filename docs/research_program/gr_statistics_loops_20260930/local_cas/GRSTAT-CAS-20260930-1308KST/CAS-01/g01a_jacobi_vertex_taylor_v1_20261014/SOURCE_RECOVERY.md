# G01-A source recovery (frame-level Lean unit)

This unit starts from the reviewed recovery
`../g01a_source_signature_recovery_v1_20261011/` (PASS_SCOPED;
`SOURCE_SIGNATURE_RECOVERY.md` sha256 `b97b94b1…94a7`, `RETURN.json` sha256
`c7757f0f…809b`) and the preserved blocker `../g01a_source_admission_v1_20261011/`.
Paths below are relative to `docs/research_program/gr_statistics_loops_20260930/`
unless absolute. Line numbers refer to the files at the hashes listed.

## Bound sources

| Source | SHA-256 | Lines used | Recovered item |
|---|---|---|---|
| `gr/OPTICAL_THEOREMS.md` | `5ae2b6a6…8c21` | 9 | smooth time-oriented Lorentzian spacetime, signature (-+++), unit future `o` |
| same | | 11–15 | `K(p,n) = -o + n`, `n·o = 0`, `K² = 0`, `o·K = 1` (observer normalization) → T11 |
| same | | 17 | affine length parameter `ℓ ≥ 0`, `∇_K K = 0`; `d_A` = source-screen area / observer solid angle; work before any conjugate point |
| same | | 48 | vertex Jacobi matrix in a parallel screen basis: `J(0)=0`, `J'(0)=I`, `J''=ℛJ`, smooth `ℛ`; `J(ℓ)=ℓI+O(ℓ³)`; `d_A=√det J = ℓ+O(ℓ³)` on the positive branch; screen change by multiples of the null tangent preserves inner products → T0, T4–T9 |
| `gr/FINITE_DISTANCE_THEOREM.md` | `d499eb7f…0e50ac` | 7 | same normalized affine ray; parallel-transported screen basis |
| same | | 9 | `D''(s) = -Ropt(s) D(s)`, `D(0)=0`, `D'(0)=I` (frozen sign) |
| same | | 11 | "This equation defines the sign of Ropt"; `‖Ropt(s)‖op ≤ Kc`, `Kc ≥ 0` on `0≤s≤L`; regularity "continuous Ropt" → `ScreenFrameData` |
| same | | 15–18 | `f`, `eta`, `eta(L) < 1` → T10b, T12 hypotheses |
| same | | 24–25, 47, 53 | Volterra identity `D = sI - ∫(s-t)Ropt D`; determinant/area-distance interval; screen area invariance (Ellis et al. §7.3) |
| `cas/contracts/CAS-01.json` | `9f1bbb01…9b57` | — | CAS-01 finite components C01–C04 only; G01-A obligations not in scope there |
| `local_cas/…/CAS-01/completion/rerun_20261003/RETURN.json` | `a2f7202d…a070` | 37 | open analytic obligation: "Jacobi vertex Taylor order and screen invariance under geometric ODE" |
| `local_cas/…/CAS-07/conditional_synthesis_v1_20261008/RETURN.md` | `d28239f3…c674` | 24, 87–89 | M04/M05 reuse; M04 Main.lean sha `39b7c460…76c9` |
| `local_cas/…/CAS-07/determinant_distance_bridge_v1_20261007/lean/Main.lean` | `0e10bfac…04af` | 12, 33, 48–60, 78 | `matrixOf`, `opnorm_error_eq`, `JacobiPremises K L` (all fields), `determinant_distance_bridge` (imported unchanged as `CAS07M05Accepted`) |
| `local_cas/…/CAS-07/jacobi_matrix_majorant_v1_20261007/lean/Main.lean` | `39b7c460…76c9` | 16–17, 66–87 | `Plane`, `Op`; `volterra_identity` (reused through the accepted olean) |
| `local_cas/…/CAS-07/eta_monotonicity_input_aligned_v1_20261007/lean/M01.lean` | — | 8–11 | `fd`, `eta` definitions (used through accepted olean) |

Git history consulted read-only: `c91429e29` (G01-A: recover optical source
signature), `11602167b` (CAS handoff). Implementation search: `grep` over `htt/`
for Jacobi/optical tidal/Ropt found no implementation of the optical Jacobi map
(only unrelated `propto` matches); there is no code-level definition to bind.

## Recovered definition used (frame level)

`ScreenFrameData K L` = (`R : ℝ → Op`, `ContinuousOn R [0,L]`,
`∀ t ∈ [0,L], ‖R t‖ ≤ K`) — FINITE_DISTANCE lines 7–11. The affine parameter is
the source's `s` (OPTICAL line 17 / FINITE line 7); only constant affine rescalings
are treated (T10), and T11 shows the observer normalization `o·K=1` fixes the
rescaling constant to `c=1`.

Two sign notations are recorded and kept distinct: FINITE `D''=-Ropt D` (frozen,
CAS07 `jacobi` field) and OPTICAL `J''=ℛJ`; T0 proves equivalence only under the
definition `ℛ := -Ropt`.

## Items that remain unrecoverable as formal objects (residuals)

| Item | Searched | Unlock condition |
|---|---|---|
| R1 Lorentzian manifold, Levi-Civita connection, Riemann sign, `Ropt_ab = R_{aKKb}` | Mathlib `fabf563a` (no pseudo-Riemannian curvature API), source docs above, `htt/` | a formal Lorentzian connection/curvature API with declared sign, or an explicitly admitted coordinate model |
| R2 affine null geodesic existence with `γ'(0)=-o+n`, screen bundle, parallel transport of an orthonormal screen frame, geometric-to-matrix Jacobi equivalence | same | R1 plus geodesic/parallel-transport ODE on the manifold |
| R3 screen-representative change by multiples of `K` (quotient screen) | OPTICAL line 48, FINITE line 53 (prose citing Ellis et al. §7.3) | R2 plus a formal screen quotient; T9 covers only the frame change between parallel orthonormal frames, assuming (not proving) that such a change is a constant `O ∈ O(2)` |
