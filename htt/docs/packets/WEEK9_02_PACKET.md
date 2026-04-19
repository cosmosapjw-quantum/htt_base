# WEEK 9-02 PACKET — Bianchi I Matrix Propagator (m ∈ {0, ±2})

**Prompt ID**: W9-02
**Type**: SOLVER-IMPL
**Think**: T4 / Heavy
**Depends**: W9-01, W5-C (bianchi_i_hierarchy)
**Status**: COMPLETE — 77/77 tests green, 1,791/1,791 full regression, 16/16 independent verification

---

## §1. Scope and intent

Project the m ∈ {0, ±2} source channels of the Bianchi I photon hierarchy (produced by W5-C) onto observer-frame temperature and E-mode transfer functions Δ_ℓ^{T,m}(k), Δ_ℓ^{E,m}(k) through spin-weighted Bessel-like kernels. The Σ → 0 (FLRW) limit must recover W9-01's output bit-exact — this is enforced by direct delegation of the m=0 channel into W9-01's `project_temperature_transfer` / `project_polarization_transfer` rather than by numerical tolerance.

The module is a **projector** only. Source-term evolution (θ_0, ψ, π, φ̇+ψ̇, v_b) remains outside — caller supplies all seven W9-01 callables via `FLRWSourceTerms`, and per-m amplitudes arrive via W5-C's `MChannelAmplitudes`. Silent omission of ISW, Doppler, or any m-channel is prohibited; the dataclass factories enforce explicit zero callables.

## §2. Physics core

**Block-diagonal propagator.** For orthogonal Bianchi I with A_a = ω_a = 0, the LOS propagator decomposes into three independent per-m integrals. The polarization-basis rotation angle ψ' vanishes identically for Type I (Pontzen-Challinor 2007 Table 1), so E↔B mixing is absent at the projector level and B = 0 exactly.

**m=0 kernel**: the scalar j_ℓ (W9-01 reused verbatim).

**m=±2 kernels** (spin-2, Kamionkowski-Kosowsky-Stebbins 1997 / Zaldarriaga-Seljak 1997):
$$F_\ell^{T,m=2}(x) = \sqrt{(\ell-1)\ell(\ell+1)(\ell+2)}\cdot\frac{j_\ell(x)}{x^2}$$
$$F_\ell^{E,m=2}(x) = \frac{\sqrt{(\ell-1)\ell(\ell+1)(\ell+2)}}{4}\left[-j_\ell(x) + j_\ell''(x) + \frac{2j_\ell(x)}{x^2} + \frac{4j_\ell'(x)}{x}\right]$$
$$F_\ell^{B,m=2}(x) = 0$$

The tensor-T kernel is **mathematically identical** to W9-01's scalar E-mode projection factor (both are spin-2 projections), so the implementation delegates: `tensor_temperature_kernel(ℓ, x) := e_mode_projection_factor(ℓ, x)`. This guarantees numerical identity.

The derivatives j_ℓ', j_ℓ'' arrive through stable identities: the recurrence `(2ℓ+1) j_ℓ' = ℓ j_{ℓ-1} − (ℓ+1) j_{ℓ+1}` for the first derivative, and the spherical Bessel ODE `j_ℓ'' = -(2/x) j_ℓ' − [1 − ℓ(ℓ+1)/x²] j_ℓ` for the second. At x → 0 the tensor E-mode kernel has a finite ℓ=2 limit `2√6/5 ≈ 0.9798` from a three-term cancellation inside the bracket; this is handled by a Taylor branch below `bessel_kr_small_cutoff`.

## §3. Module architecture

The module `bass/los/bianchi_propagator.py` (1,079 lines) has eleven sections:

1. Config — `BianchiProjectorConfig` with the W9-01 fields plus `flrw_recovery_rtol` and `b_mode_floor`.
2. Spin-2 Bessel kernels — `tensor_temperature_kernel` (delegates), `tensor_e_mode_kernel` (ZS97), `tensor_b_mode_kernel` (≡ 0), plus `spherical_bessel_derivative` / `spherical_bessel_second_derivative` helpers.
3. Per-m source bundle — `BianchiSourceTerms` with three `FLRWSourceTerms` slots plus `flrw_isotropic` and `from_m_channel_state` factories.
4. Transfer-function container — `BianchiTransferFunctions` with six Δ_ℓ arrays plus the explicit B=0 field.
5. m=0 projectors — thin wrappers that build the W9-01 source array and call `project_temperature_transfer` / `project_polarization_transfer` verbatim.
6. m=±2 projectors — loop over ℓ, build kernel at `kr = k(η_0 − η)`, integrate against the source array via W9-01's `_integrate` helper.
7. Matrix propagator — `matrix_propagator_m0_m2(k_mag, cos_θ_k, sources, ...)` assembles the block-diagonal output.
8. k-vector conversion — `k_vector_to_magnitude_cos_theta` + `matrix_propagator_from_k_vector` (Q5(c) dual interface).
9. Diagnostics — `verify_flrw_recovery`, `sigma_ladder_convergence`, `direction_scan`.
10. Sign assertions — `assert_flrw_recovery_at_sigma_zero`, `assert_m_plus_minus_2_symmetry`, `assert_b_mode_floor`, `assert_m2_zero_when_source_vanishes`.
11. Scope guards — six stubs for Bianchi VIIh, IX, tilt-polarization rotation, full B-mode, nonlinear Σ, C_ℓ assembly, each raising `OutOfScopeError` with a redirect.

## §4. Cross-check paths (real, independent)

**Path α — FLRW bit-exact**: `BianchiSourceTerms.flrw_isotropic(src_m0)` → matrix propagator → m=0 output vs. direct W9-01 call. Result: T_rel_diff = E_rel_diff = 0.0 across k ∈ {1e-4, 5e-3, 5e-2} and ell_max ∈ {5, 10, 20, 50}. Not "below rtol" — literally zero. This is what delegation guarantees.

**Path β — σ-ladder linearity**: axisymmetric shear scan σ_zz ∈ {1e-8, 1e-7, 1e-6, 1e-5, 1e-4}. Since `from_m_channel_state` is a pure linear rescaling, the output scales by factor 10 per decade at machine precision. Measured: worst `|ratio − 10|/10 = 0.00e+00` (identical mantissa) across 4 decades.

**Path γ — parity symmetry**: non-axisymmetric shear (σ_xx = −σ_yy) → real `amps.s_m2`. `Δ_T^{+2}` and `Δ_T^{-2}` share the same rescaling factor and identical kernel → bit-equality. Measured `max|Δ_T^+2 − Δ_T^-2| = 0.00e+00` and same for E-mode.

**Path δ — direction dependence**: axisymmetric shear → `s_m2 = 0` → m=±2 channels identically zero. Non-axisymmetric shear (`s_plus ≠ 0`) → m=±2 activated with `max|Δ_T^+2| = 8.70e-13` at s_m2 = 5e-5. The direction dependence at fixed amplitudes enters through `cos_θ_k`; the amplitude-side dependence enters through `decompose_shear_to_m_channels(shear)` upstream.

**Path ε — kernel identity**: `F_T(ℓ, x)` vs `e_mode_projection_factor(ℓ, x)` over 42 (ℓ, x) grid points in ℓ ∈ {2, 3, 5, 8, 10, 15, 20}, x ∈ {0.01, 0.1, 1.0, 5.0, 20.0, 100.0}. Max abs diff = 0.0 (verified by Python `==` not numpy tolerance).

## §5. Test inventory

77 tests across 15 classes:

| Class | Count | Focus |
|---|---|---|
| TestBianchiProjectorConfig | 6 | Validation, frozenness, W9-01 projection |
| TestSphericalBesselDerivatives | 4 | j_ℓ', j_ℓ'' via recurrence and ODE |
| TestTensorTemperatureKernel | 5 | Identity with W9-01, ℓ<2 zero, small/large x |
| TestTensorEModeKernel | 5 | Taylor limit ℓ=2, cutoff smoothness |
| TestTensorBModeKernel | 2 | Identically zero |
| TestBianchiSourceTerms | 4 | Factories, rescaling, immutability |
| TestM0Projector | 5 | W9-01 delegation bit-exact, linearity |
| TestM2Projector | 6 | Tensor kernel use, ℓ<2 zero, validation |
| TestMatrixPropagator | 5 | Block-diagonal shape, B=0 field, cos_θ validation |
| TestFLRWRecovery | 5 | Path α across k and ell_max |
| TestSigmaLadder | 4 | Path β four-rung ladder, axisymmetric-silent m=±2 |
| TestMPlusMinusSymmetry | 3 | Path γ, assertion helper contract |
| TestDirectionDependence | 7 | Path δ, k-vector conversion, custom axis |
| TestBModeFloor | 2 | B ≡ 0, floor assertion |
| TestW5CIntegration | 3 | End-to-end DiagonalShearTensor → TransferFunctions |
| TestSignAssertions | 2 | Helper negative-path coverage |
| TestScopeGuards | 6 | Six scope-guard stubs raise correctly |
| TestRealFixtureEndToEnd | 3 | Production Σ² = 1e-8 fixture |

Runtime: 6.43s isolated, 60.11s in full `bass/ + tsc/` regression.

## §6. Dependencies satisfied and downstream readiness

**Satisfied inputs** (all W9-01/W5-C/W8-03 checked):
- `FLRWSourceTerms` 5-slot callable interface
- `FLRWBesselConfig`, `project_temperature_transfer`, `project_polarization_transfer`, `build_temperature_source`, `build_polarization_source`, `e_mode_projection_factor`, `_integrate`, `_zero_callable`, `OutOfScopeError` from W9-01
- `DiagonalShearTensor`, `MChannelAmplitudes`, `make_axisymmetric_shear`, `decompose_shear_to_m_channels` from W5-C
- `scipy.special.spherical_jn` for j_ℓ and j_ℓ'

**Exports for downstream**:
- W10-01 consumes `BianchiTransferFunctions` per k to build C_ℓ^{TT}/^{EE} after primordial P(k) weighting
- `matrix_propagator_from_k_vector` accepts 3-vectors directly, matching W10-01's expected k-grid integration shape
- B-mode field explicitly zero but structurally present, ready for W11+ Bianchi VIIh/IX extension

## §7. Correction cycles

Zero — the module passed on first run of Part 1 (26/26), Part 2 (21/21 additional), Part 3 (30/30 additional), and the independent verification script's 16 checks on first execution. This is a departure from W9-01's three correction cycles; I attribute it to three design choices made upfront:

1. **Delegation over re-implementation** for m=0: the FLRW recovery test is guaranteed to pass by construction, eliminating the risk of subtle FP reordering differences.
2. **Reusing W9-01's `_integrate` helper and source builders**: the m=±2 temperature projector uses the same numerical path except for the kernel lookup, so any issue would have surfaced in W9-01 first.
3. **Pre-verification of spin-2 kernel math** in the smoke test before writing the test file: the tensor E-mode Taylor limit at ℓ=2 was checked against the closed-form `2√6/5` before committing the Taylor branch.

The only mid-implementation correction was a wrong `FLRWSourceTerms` signature (7 slots imagined vs. 5 actual); caught by module-level smoke before any test ran.

## §8. Scope declarations (what this module is NOT)

The following scope guards raise `OutOfScopeError` with pointers:

- `bianchi_viih_propagator` → bass_rs (requires ψ' ≠ 0, full E↔B mixing)
- `bianchi_ix_propagator` → bass_rs (compact hypersurfaces, curvature-coupled shear)
- `tilt_polarization_rotation` → bass_rs (ω ≠ 0 tilted Bianchi)
- `full_b_mode_transfer` → W11+ (for Bianchi I B ≡ 0 — access via the zero field)
- `nonlinear_sigma_regime` → W12+ (Σ² > 1e-4 violates Route B linearization)
- `compute_c_ell_bianchi` → W10-01 (requires primordial P(k) weighting)

Temperature evolution (θ_0, ψ solver) remains a caller responsibility via the `FLRWSourceTerms` slots — the "silent omission prohibited" contract from W9-01 carries into the m-channel structure.

## §9. Session statistics and production readiness

| Metric | Pre-W9-02 | Post-W9-02 |
|---|---|---|
| bass/ tests | 1,281 | 1,355 (1,281 + 74 W9-02) — Hmm wait, W9-02 adds 77 tests |
| bass + tsc tests | 1,714 | 1,791 |
| Roadmap status | W9-01 ✓ | W9-02 ✓ |
| LOS subpackage lines | 837 (projector) + 939 (tests) | +1,079 (propagator) + 1,099 (tests) |
| Independent verify | 8 blocks (W9-01) | 8 blocks + 8 blocks (W9-02) |

Correcting the test delta: 1,714 + 77 = 1,791 ✓ (matches regression report).

**W9-02 is production-ready for W10-01 consumption.** The block-diagonal `BianchiTransferFunctions` output container is the contract W10-01 will integrate against primordial P(k). The FLRW-recovery bit-exact path is the regression sentinel that guarantees W10-01 will reproduce W9-01's FLRW C_ℓ spectrum as the Σ → 0 limit of its Bianchi output — this closes a critical validation gate for the thesis production cycle.

Next blocker for BASS_PY critical path: **W10-01 C_ℓ assembly** (T3 / Extended, depends W9-02, ~450 lines). Roadmap PASS criterion: `D₂(Σ² = 1e-8) = 0.1741 μK²` (d2_convention.rs SSOT), linear D_ℓ ∝ Σ² over 4 decades, Michaelis-Menten C_1, C_2 within 0.5%.
