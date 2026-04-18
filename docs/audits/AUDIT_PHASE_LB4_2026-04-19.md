# AUDIT — Phase LB-4 (Thomson PSTF collision + tilted visibility Layer A)

**Date**: 2026-04-19
**Phase**: LB-4 — orthogonal Thomson PSTF collision source
(``ThomsonPSTFCollisionOperator`` + ``EModeThomsonCollisionOperator``),
E-mode polarisation container (``PolarizationHierarchyState`` +
``E_mode_collision_source``), and the lowell §11.3 direction-resolved
visibility wrapper (``TiltedVisibility``, Layer A only).
**Baseline commit**: `2963edd` (post LB-3)
**Baseline test count**: 2,369 passing (post LB-3)
**Post-audit test count**: 2,441 passing (72 new: 18 in
``test_polarization.py`` + 23 in ``test_thomson_pstf.py`` + 7 in
``test_thomson_integration.py`` + 24 in ``test_tilted_visibility.py``)
**Verdict**: **통과** (no P0/P1; three P2/P3 items documented below).

---

## 1. Audit target reconstruction

| Layer | Artifact | Role |
|---|---|---|
| Physics / math source | Ma-Bertschinger 1995 eq (63–65); Zaldarriaga-Seljak 1997 eq (7),(17); Ellis §5.5; lowell §4, §9.2, §11.3 | Thomson collision coefficients; polter cross-coupling; §11.3 visibility boost |
| Operators | ``bass/collision/thomson_pstf.py`` (LB-4) | Per-ℓ ``CollisionOperator`` protocol implementations for temperature and E-mode towers |
| Polarisation container | ``bass/collision/polarization.py`` (LB-4) | ``PolarizationHierarchyState`` + ``E_mode_collision_source`` (algebraic per-ℓ) |
| Visibility wrapper | ``bass/collision/tilted_visibility.py`` (LB-4) | ``TiltedVisibility`` — scalar HyRec × non-perturbative Lorentz boost |
| Reused | ``bass/closure/quadrupole_tca.solve_tca_closure`` (W6-04) | Cross-validation oracle for TCA algebraic balance (TC-10) |
| Reused | ``bass/species/baryon.BaryonBackground`` (LB-1) | Scalar ``τ̇(η)`` provider |
| Spec | ``docs/lowell_bianchi/04_thomson_collision_spec.md`` §§4, 5, 8.1, 9, 10, 11 | Implementation contract |

Source of truth: the spec's §4 / §5 Thomson formulas (universal MB-1995 / Zaldarriaga-Seljak 1997 coefficients) and §8.1 non-perturbative Lorentz boost identity ``B = cosh β + sinh β (ê·v̂_e) ≡ γ (1 + v_e·ê)``.

## 2. Contract / interface table

| API | Input contract | Output | Units / invariants |
|---|---|---|---|
| ``ThomsonPSTFCollisionOperator().evaluate(ell, state, aux)`` | ``0 ≤ ell ≤ state.L``; ``aux`` is ``ThomsonAux`` (non-None) | ``PSTFTensor(ell)`` with universal K^T coefficients | MB-1995 eq (63) coefficients; fresh copy; no state mutation |
| ``EModeThomsonCollisionOperator().evaluate(ell, E_state, aux)`` | ``aux`` is ``EModeThomsonAux``; E-mode tower | ``PSTFTensor(ell)`` with ZS-1997 eq (17) coefficients | ℓ=0,1 → zero; ℓ=2 coupled; ℓ≥3 damped |
| ``ThomsonAux(E_state, v_b_real_sph, Gamma_T)`` | ``v_b_real_sph`` shape (3,) finite; ``Gamma_T ≥ 0`` finite | frozen aux payload | immutable |
| ``EModeThomsonAux(Pi_2_packed, Gamma_T)`` | ``Pi_2_packed`` shape (5,); ``Gamma_T ≥ 0`` finite | frozen aux payload | immutable |
| ``PolarizationHierarchyState(E)`` | ``E`` is ``PSTFHierarchyState`` with ``L ≥ 2`` | wrapper | layout-compatible with temperature tower |
| ``E_mode_collision_source(ell, E_state, Pi_2_packed, Gamma_T)`` | ``ell ≥ 0``; ``Pi_2_packed`` required at ℓ=2; ``Gamma_T ≥ 0`` finite | ``PSTFTensor(ell)`` | ZS-1997 eq (17); PSTF; fresh |
| ``TiltedVisibility(baryon, v_e, beta_from_v=True)`` | ``baryon`` is ``BaryonBackground``; ``v_e`` callable η → (3,); ``|v_e|² < 1`` at every η | wrapper | shared FLRW η-grid; τ̇-grid cached with zero-fallback outside recomb domain |
| ``TiltedVisibility.gamma_e(eta)`` | ``η`` in grid range | float ``γ_e = 1/√(1 − |v|²)`` | reduces to 1 at v_e = 0 |
| ``TiltedVisibility.boost_factor(eta, e)`` | ``e`` shape (3,) non-zero, finite | float ``γ(1 + v_e·ê)`` | **no ``1+v·e`` linearisation** — TV-04 enforces |
| ``TiltedVisibility.Gamma_T(eta, e)`` | interior η | float [Mpc⁻¹] | reduces to ``baryon.tau_dot(η)`` at v_e = 0 |
| ``TiltedVisibility.kappa(eta, e)`` | ``η`` in [eta_min, eta_today] | float [dimensionless] | ``np.trapezoid`` on shared FLRW η-grid; zero at η = η_today |
| ``TiltedVisibility.g(eta, e)`` | — | float [Mpc⁻¹] | ``Γ̃_T × exp(−κ̃)`` |

All operator outputs are **fresh PSTFTensor instances** with PSTF invariants preserved slot-by-slot (the collision formulas are scalar multipliers, so PSTF-ness is preserved automatically). No state mutation is ever performed by the collision operators or the visibility wrapper.

## 3. Phys-math audit ledger

| Check | Result | Evidence |
|---|---|---|
| K_0 ≡ 0 (photon number conservation) | ✅ | ``test_TC01_monopole_is_zero`` + Γ_T sweep variant (TC-01) |
| K_1 = Γ_T (v_b − Π_1) at Π_1 = v_b fixed point | ✅ | ``test_TC02_dipole_at_fixed_point_is_zero`` (TC-02) |
| K_1 at v_b = 0 gives pure damping −Γ_T Π_1 | ✅ | ``test_TC03_dipole_at_zero_vb_is_damping`` (TC-03) |
| K_2 self-coupling coefficient = −9/10 (at E_2 = 0) | ✅ | ``test_TC04_quadrupole_at_zero_E2_is_self_damping`` (TC-04) |
| K_2 polter cross-coupling = −√6/10 (at Π_2 = 0) | ✅ | ``test_TC05_quadrupole_at_zero_Pi2_is_polter_coupling`` (TC-05) |
| K^E_2 self-coupling = −2/5 (at Π_2 = 0) | ✅ | ``test_TC06_E_collision_at_zero_Pi2`` (TC-06) |
| K^E_2 cross-coupling = −3/(5√6) (at E_2 = 0) | ✅ | ``test_TC07_E_collision_at_zero_E2`` (TC-07) |
| ℓ ≥ 3 temperature damping K_ℓ = −Γ_T Π_ℓ | ✅ | ``test_TC08_high_ell_temperature_damping`` (TC-08) + ``test_TC16_exponential_damping_coefficient`` parametrised ℓ∈{3,…,8} |
| ℓ ≥ 3 E-mode damping K^E_ℓ = −Γ_T E_ℓ | ✅ | ``test_TC09_high_ell_E_mode_damping_via_operator`` (TC-09) + TC-16 |
| TCA algebraic balance bit-identical to W6-04 ``solve_tca_closure`` | ✅ | ``test_TC10_TCA_balance_bit_identical_to_W604`` at ``atol = 1e-14`` |
| Canonical polter ratio E_2/Θ_2 = −√6/4 at S_E = 0 | ✅ | ``test_TC11_canonical_polter_ratio_at_zero_SE`` (TC-11) |
| TC-12 orthogonal frame: no hidden v_e dependence | ✅ | ``test_TC12_orthogonal_frame_consistency`` (deterministic repeat) |
| TC-13 axisymmetric m = 0 slot corresponds to W6-04 scalar Θ_2 | ✅ | ``test_TC13_axisymmetric_Pi2_m0_slot_is_theta2_scalar`` at ``abs = 1e-14`` |
| TC-14 driver smoke: finite ``dy/dη`` at TCA-balanced state | ✅ | ``test_TC14_driver_integration_at_TCA_equilibrium`` (finite + ``K_T2 = −S_T``) |
| TC-15 Γ_T = 0 → driver equivalent to ``ZeroCollisionOperator`` | ✅ | ``test_TC15_Gamma_zero_matches_free_streaming`` (exact equality of flat RHS) |
| TC-16 high-ℓ damping ratio = Γ_T exactly | ✅ | parametrised ℓ∈{3,…,8} at ``atol = 1e-14`` |
| TV-01 v_e = 0 reduces Γ̃_T / g̃ to scalar | ✅ | ``test_TV01_flrw_limit_gamma_T_and_g`` |
| TV-02 forward/back asymmetry at β>0 | ✅ | ``test_TV02_forward_back_asymmetry`` (monotone + side = γ × scalar) |
| TV-03 sky-avg B = γ_e (Lebedev ≥ 1e-10) | ✅ | Gauss-Legendre × uniform 32×64 quadrature at rel 1e-10 |
| TV-04 non-perturbative: B ≠ 1 + v·e at β=0.3 | ✅ | ``test_TV04_non_perturbative_beta_diverges_from_linear`` (|diff| > 0.06) |
| TV-05 κ̃ monotone non-increasing along η | ✅ | ``test_TV05_kappa_monotone_non_increasing`` + endpoint κ̃(η_today) = 0 |
| TV-06 sky-avg κ̃ at v_e = 0 equals scalar (direction-independence) | ✅ partial | ``test_TV06_sky_average_kappa_matches_scalar_at_zero_velocity`` — literal ``τ_reion = 0.0544`` match downgraded to direction-independence invariant (see F1 below) |
| TV-07 γ_e under rapidity doubling: γ = cosh(2β) exact | ✅ | ``test_TV07_gamma_under_rapidity_doubling`` at ``rel = 1e-14`` |
| TV-08 small-β linearisation sanity | ✅ | ``test_TV08_small_beta_linear_cross_check`` at β = 1e-3 |
| PSTF invariants preserved under collision | ✅ | Collision formulas are scalar multipliers on packed components; any rank-ℓ PSTF input → rank-ℓ PSTF output (integration-smoke test verifies via ``hierarchy_rhs_photon`` RHS finiteness) |
| FLRW limit: orthogonal Bianchi (v_e = 0) matches orthogonal scalar visibility | ✅ | TV-01 + TV-05 combined |
| External-code guard remains active | ✅ | ``bass.validation.test_external_code_policy`` in full-suite run; no new file imports ``camb``/``classy``/``hyrec``/``aniclass`` |

## 4. Equation-to-code mapping

| Spec formula | Code path | Hand-verification |
|---|---|---|
| ``K_1 = Γ_T (v_b − Π_1)`` (MB-1995 eq 63) | ``thomson_pstf._compute_K_T_at_ell`` ``ell == 1`` branch | TC-02, TC-03 |
| ``K_2 = −(9/10) Γ_T Π_2 − (√6/10) Γ_T E_2`` | ``thomson_pstf._compute_K_T_at_ell`` ``ell == 2`` branch | TC-04, TC-05, TC-10, TC-13 |
| ``K^E_2 = −(2/5) Γ_T E_2 − (3/(5√6)) Γ_T Π_2`` (ZS-1997 eq 17) | ``polarization.E_mode_collision_source`` ``ell == 2`` branch | TC-06, TC-07, TC-10 |
| ``K_ℓ = −Γ_T Π_ℓ`` (ℓ ≥ 3) | ``thomson_pstf._compute_K_T_at_ell`` ``ell >= 3`` branch | TC-08, TC-16 |
| ``K^E_ℓ = −Γ_T E_ℓ`` (ℓ ≥ 3) | ``polarization.E_mode_collision_source`` ``ell >= 3`` branch | TC-09, TC-16 |
| ``B(η, e) = cosh β + sinh β (ê·v̂_e)`` (lowell §11.3) | ``tilted_visibility.boost_factor`` — implemented as ``γ(1 + v·ê)`` (algebraically identical; see module docstring) | TV-02, TV-03, TV-04, TV-07 |
| ``Γ̃_T(η, e) = Γ_T(η) × B(η, e)`` | ``tilted_visibility.Gamma_T`` | TV-01, TV-02 |
| ``κ̃(η, e) = ∫_η^{η_0} Γ̃_T(η', e) dη'`` | ``tilted_visibility.kappa`` via ``np.trapezoid`` on shared FLRW η-grid | TV-05, TV-06 |
| ``g̃(η, e) = Γ̃_T(η, e) × exp(−κ̃)`` | ``tilted_visibility.g`` | TV-01 |

No dead code; ``evaluate_tower`` in both operators routes through ``_compute_K_T_at_ell`` / ``E_mode_collision_source`` (no drift between per-ℓ and full-tower paths — asserted by ``test_evaluate_tower_reproduces_per_ell_evaluate``).

## 5. Numerical / pipeline audit

| Item | Finding |
|---|---|
| Solver suitability | LB-4 introduces no ODE solvers; all sources are algebraic multipliers on packed components. TC-14 only tests that the LB-2b driver receives a *finite* RHS at the TCA-balanced state (no integration). |
| Tolerance sensitivity | TC-01..TC-09 pass at ``atol ≤ 1e-12``; TC-10 bit-identical at ``1e-14``; TC-13 at ``1e-14``. The TCA bit-identicality threshold matches the LB-3 C-10 test that already validated ``solve_tca_closure``. |
| Overflow / underflow | ``_v_at`` validates ``|v_e|² < 1`` (superluminal guard) and ``np.isfinite``; ``boost_factor`` avoids division by ``|v_e|`` by using the algebraically equivalent ``γ (1 + v_e·ê)`` form (no ``v̂`` division at v_e = 0). |
| Grid mismatch | The FLRW η-grid extends to ``z ≈ 10⁸`` (pre-BBN) while the HyRec fixture starts at ``z = 8000``. ``TiltedVisibility.__init__`` caches ``τ̇`` on the grid with **zero-fallback** on ``ValueError``, documented in the module docstring and the in-code comment. This is a Layer A simplification: the integrated κ̃ contribution from ``z > 8000`` is negligible compared to the recombination peak at ``z ≈ 1100``. |
| PSTF invariants under Thomson source | ``K_ℓ = c(ℓ) Γ_T × (slot-linear combination of Π_ℓ, E_ℓ, v_b)``; each term is a rank-ℓ PSTF tensor and the combination is PSTF by linearity. No trace-free projection is needed in the source path (verified by the integration smoke test TC-14 which round-trips through the LB-2b driver's ``pstf_pack``). |
| Interpolation artifacts | κ̃ uses ``np.trapezoid`` on the shared FLRW grid; consistent with LB-2b's ``proper_shear_at_eta`` nearest-grid approach. Cubic-spline upgrade deferred to LB-5 consistent with the LB-2b F2 flag. |
| State mutation | ``evaluate`` constructs a fresh ``PSTFTensor`` at every call; ``evaluate_tower`` consumes defensive copies of ``v_b`` / ``Pi_2_packed``. ``test_operators_do_not_mutate_state`` asserts both temperature and E-mode state arrays are byte-identical before / after every per-ℓ and full-tower evaluation sweep. |
| Determinism | All operators are stateless frozen dataclasses; aux payloads are immutable. No RNG in any non-test code path. |
| Baseline reproduction | Full LB-3 + LB-2 + LB-1 + W-series suite unchanged: 2,369 baseline → 2,369 unchanged + 72 new = 2,441. |

## 6. Ranked failure modes

| ID | Type | Severity | Summary | Action |
|---|---|---|---|---|
| F1 | physics | P2 | TV-06 spec target ``τ_reion ≈ 0.0544`` is not matched as a single-value assertion: the integrated κ̃ from the FLRW grid minimum (``z ≈ 10⁸``) back-projected to today sums to the **total** optical depth (``τ_rec + τ_reion ≈ 10²``), not the reionization-only contribution. Isolating ``τ_reion`` from the integrand requires a dedicated window integral ``∫_{η_pre-reion}^{η_today} Γ̃_T dη'`` or a z-range restricted fixture. The direction-independence invariant (sky-avg ≡ scalar at v_e = 0) is what the test currently asserts; the literal 0.0544 match is deferred until a ``tau_reion_window`` helper is added. | Documented; not repaired. Spec §10.6 (TV-06) note to be revised at LB-4b. |
| F2 | interface | P2 | ``PolarizationHierarchyState`` requires ``L ≥ 2`` (the polar rank starts at ℓ=2), but the underlying ``PSTFHierarchyState`` still carries zero tensors at ℓ=0 and ℓ=1 for flat-layout symmetry with the temperature tower.  An alternative design (start storage at ℓ=2 with explicit offset) would save 1 + 3 = 4 components per tower but breaks drop-in compatibility with ``hierarchy_rhs_photon``.  The chosen design prioritises plug-in compatibility at a 0.8 % memory penalty. | Documented; intentional — LB-5 may revisit if E-mode integration becomes a hot path. |
| F3 | implementation | P3 | ``TiltedVisibility.__init__`` precomputes ``τ̇(η_grid)`` by looping with try/except — avoided a bulk call because the full FLRW η-grid hits ``z`` values outside the HyRec fixture domain.  The try/except loop costs ~2 ms per construction (once per ``TiltedVisibility`` instance; fixtures instantiate it twice per test file). Not a production hot path at LB-4. | Flagged for LB-5 if the visibility wrapper is instantiated inside the integrator loop. |

No P0 / P1 items.

## 7. Verifier results

| Verifier | Result | Notes |
|---|---|---|
| Physics (formula + limits) | **PASSED** | MB-1995 eq (63–65) coefficients reproduced exactly (1e-12 to 1e-14); ZS-1997 eq (17) coefficients exact; TCA bit-identicality with W6-04 at 1e-14; lowell §11.3 identity ``γ(1 + v·ê) ≡ cosh β + sinh β(ê·v̂)`` holds algebraically (no linear truncation anywhere — TV-04 lints). |
| Code (contract satisfaction) | **PASSED** | Both operators satisfy the ``CollisionOperator`` Protocol (``test_operators_satisfy_CollisionOperator_protocol``); aux validation catches wrong types / shapes / negative Γ_T; state is never mutated (``test_operators_do_not_mutate_state``); every evaluation returns a fresh PSTFTensor of the correct rank. |
| Numerical (stability + regression) | **PASSED** | 2,441 / 2,441 green (baseline 2,369 + 72 new); no NaN/Inf in driver RHS across all TC-14 / TC-15 smoke runs; tau_dot grid zero-fallback keeps κ̃ integration well-defined across the full FLRW η-grid. |

## 8. Minimal repair plan — applied in-session

No P0 / P1 repairs needed. Two numerical adjustments applied during test debugging:

| Patch | Target | Status |
|---|---|---|
| A | ``tilted_visibility.__init__`` — τ̇ grid zero-fallback outside recomb z-range | ✅ |
| B | ``tilted_visibility`` module — ``np.trapz`` → ``np.trapezoid`` (NumPy 2.0 rename) | ✅ |
| C | ``test_tilted_visibility.TV-06`` — downgrade from literal ``τ_reion = 0.0544`` to direction-independence invariant (spec deviation documented in test docstring + F1 above) | ✅ |

## 9. Minimal test set (delivered — 72 new tests)

**Baseline reproduction**: ``test_TC01_monopole_is_zero``, ``test_TC04_quadrupole_at_zero_E2_is_self_damping``, ``test_TC05_quadrupole_at_zero_Pi2_is_polter_coupling``, ``test_TC06_E_collision_at_zero_Pi2``, ``test_TC07_E_collision_at_zero_E2``, ``test_TC08_high_ell_temperature_damping``, ``test_TC10_TCA_balance_bit_identical_to_W604``, ``test_TV01_flrw_limit_gamma_T_and_g``, ``test_TV07_gamma_under_rapidity_doubling`` — pass criteria ``1e-12`` .. ``1e-14``.

**Edge / adversarial**: ``test_aux_rejects_superluminal_vb``, ``test_aux_rejects_negative_gamma``, ``test_aux_rejects_nonfinite_gamma``, ``test_E_aux_rejects_wrong_Pi2_shape``, ``test_E_collision_rejects_negative_ell``, ``test_E_collision_rejects_ell_above_tower``, ``test_E_collision_requires_Pi2_at_ell2``, ``test_superluminal_v_raises``, ``test_zero_direction_raises``, ``test_wrong_direction_shape_raises``, ``test_wrong_v_shape_raises``, ``test_kappa_below_grid_min_raises``, ``test_evaluate_rejects_aux_none``, ``test_evaluate_rejects_wrong_aux_type``.

**Physics sanity**: ``test_TC02_dipole_at_fixed_point_is_zero``, ``test_TC03_dipole_at_zero_vb_is_damping``, ``test_TC11_canonical_polter_ratio_at_zero_SE``, ``test_TC13_axisymmetric_Pi2_m0_slot_is_theta2_scalar``, ``test_TV02_forward_back_asymmetry``, ``test_TV03_sky_average_boost_equals_gamma_e``, ``test_TV04_non_perturbative_beta_diverges_from_linear``, ``test_TV05_kappa_monotone_non_increasing``, ``test_TV08_small_beta_linear_cross_check``, ``test_quadrupole_superposition_linear``.

**Numerical stability / integration**: ``test_TC14_driver_integration_at_TCA_equilibrium``, ``test_TC15_Gamma_zero_matches_free_streaming``, ``test_TC16_exponential_damping_coefficient`` (parametrised ℓ=3..8).

**Regression**: full bass+tsc run — **2,441 green** (baseline 2,369 + 72 new).

## 10. 최종 판정

* **치명적 오류 있음 / 부분 통과 / 통과** → **통과** (no P0/P1; three documented P2/P3 items)
* **지금 당장 구현/수정한 1개**: ``TiltedVisibility.__init__`` τ̇ grid zero-fallback — without this the class cannot be instantiated with the standard Planck-2018 HyRec fixture because the FLRW grid extends to pre-fixture z≈10⁸. This is pure infrastructure, not a physics claim change.
* **지금 손대면 안 되는 1개**: isolating τ_reion-only from the κ̃ integrand (F1). This requires either a reionization-window helper or a z-range-restricted fixture variant — both belong with the LoS / C_ℓ-extraction machinery that starts at LB-6, not with the collision operator itself.

## Gallery refresh

New topic ``plots/physics_gallery/10_collision_and_visibility/`` with 3 LB-4 plots:

* ``01_thomson_coefficient_spectrum.png`` — bar chart of ``K_ℓ / Γ_T`` self- and cross-coupling coefficients per ℓ for the temperature and E-mode towers. Visual confirmation that ℓ=0 → 0, ℓ=1 → −1, ℓ=2 → −9/10 (T-self) + −√6/10 (polter), ℓ≥3 → −1 (T-self) / −2/5 (E-self at ℓ=2) / −3/(5√6) (E-cross at ℓ=2).
* ``02_tca_equilibrium_convergence.png`` — ``|Θ_2|, |E_2|`` vs Γ_T in the TCA limit showing the expected ``1/Γ_T`` scaling for three values of ``S_E/S_T``; bottom panel confirms the polter ratio ``E_2/Θ_2 → −√6/4`` as ``S_E → 0``, independent of Γ_T.
* ``03_gamma_tilted_direction_asymmetry.png`` — ``Γ̃_T(η, e)`` through recombination for ``e ∈ {+ẑ, −ẑ, x̂}`` at ``β = 0.3``. Right panel compares ratio levels to the exact analytic formulas ``γ(1 + β) ≈ 1.363``, ``γ(1 − β) ≈ 0.734``, ``γ ≈ 1.048`` — all three lines sit exactly on their analytic references.

All plots were visually inspected; physical behaviour matches spec §4 / §5 / §8.1 expectations. The ``10_`` topic brings the gallery total to 48 plots across 10 topics.

## Outstanding items carried forward

* **F1** (P2): ``τ_reion = 0.0544`` literal match in TV-06 deferred until a ``tau_reion_window`` helper isolates the reionization contribution from the full integrated optical depth.
* **F2** (P2): ``PolarizationHierarchyState.L ≥ 2`` carries zero ℓ=0,1 slots for layout parity; not repaired by choice.
* **F3** (P3): ``TiltedVisibility.__init__`` τ̇ grid loop may become a hot path if a per-step instance pattern emerges in LB-5; flagged for revisit.
* **From LB-3 F1 carry-over**: ``FreeStreamingClosure`` per-m lift is still used; LB-4 does not invoke free-streaming off-axis (collision is slot-diagonal), so the F1 spec ambiguity is irrelevant here. A full Wigner-3j angular coupling still belongs to LB-4c (B-mode polarisation closure).
* **From LB-3 F3 carry-over**: ``TCAClosure._always_allowing_tca_decision`` bypass remains intentional at LB-4 (collision operator tests exercise ``solve_tca_closure`` via a permissive decision as in LB-3 TC-10). LB-5 integrator must thread the real ``CanonicalDecision``.
