# AUDIT — Phase LB-3 (closure & truncation)

**Date**: 2026-04-19
**Phase**: LB-3 — four closure strategies (``HardCut``,
``FreeStreaming``, ``PowerLaw``, ``TCA``) exposed through the LB-2a
``ClosureStrategy.get_closure`` protocol, plus ``measure_closure_error``
diagnostic and ``build_default_closure`` factory.
**Baseline commit**: `1797ff7` (pre-session, LB-2b)
**Baseline test count**: 2,322 passing (post LB-2b)
**Post-audit test count**: 2,369 passing (47 new: 28 in
``test_closure.py`` + 9 in ``test_closure_diagnostics.py`` + 10 covering
factory validation / edge cases / integration smoke)
**Verdict**: **통과** (no P0/P1; three P2/P3 items documented below).

---

## 1. Audit target reconstruction

| Layer | Artifact | Role |
|---|---|---|
| Physics / math source | Ma-Bertschinger 1995 §6 eq (53); Kolb-Turner §9.4; Pontzen-Challinor 2007 §5 | Free-streaming recursion, fluid-tail power law, ℓ=2 TCA |
| Strategies | ``bass/hierarchy/closure.py`` (LB-3) | Four ``ClosureStrategy`` implementations + ``TCAClosure`` algebraic extension |
| Reused | ``bass/closure/quadrupole_tca.py`` (W6-04) | ``solve_tca_closure`` wrapped, **not** reimplemented |
| Diagnostic | ``bass/hierarchy/closure_diagnostics.py`` | Per-ℓ Frobenius norm of ``dy/dη`` divergence between truncation depths |
| Factory | ``build_default_closure(L_max, strategy_name, …)`` | Named dispatch; raises on unknown strategies |
| Spec | ``docs/lowell_bianchi/03_closure_truncation_spec.md`` §3 (revised), §4–§7, §10.2 (revised), §11 (revised) | Protocol alignment note + new ``build_default_closure`` contract + C-01..C-16 revisited to reference the ``get_closure`` single-method protocol |

Source of truth: LB-2a ``closure_interface.py`` protocol (``get_closure(state, ell_requested) -> PSTFTensor``) was inherited verbatim; the originally-sketched multi-method protocol (``closure_next`` / ``closure_next_next`` / ``override_at_ell`` / ``algebraic_closure``) was collapsed into ``get_closure`` at LB-2a. The LB-3 spec was updated in-session to reflect this (new §3.1–§3.3) and the C-tests now reference the canonical single-method form.

## 2. Contract / interface table

| API | Input contract | Output | Units / invariants |
|---|---|---|---|
| ``HardCutClosure().get_closure(state, ell)`` | ``ell ≥ 0``; ``state`` is ``PSTFHierarchyState`` | ``zero_pstf(ell)`` above tower; defensive copy within | dimensionless; PSTF |
| ``FreeStreamingClosure(k, eta).get_closure(state, ell_req)`` | ``k ≥ 0`` finite, ``η`` finite; ``ell_req ≥ 0`` | ``PSTFTensor(ell=ell_req)`` via iterated MB eq (53) per-m | PSTF at each intermediate step; zero at ``kη < k_eta_floor`` |
| ``PowerLawExtrapolationClosure(α).get_closure(state, ell_req)`` | ``α > 0``; ``state.L ≥ 1`` for extrapolation | ``PSTFTensor(ell=ell_req)`` with each m-slot scaled by ``(L/ell_req)^α`` | PSTF |
| ``TCAClosure(inner, thr).get_closure(state, ell_req)`` | Valid ``inner`` ClosureStrategy | Delegates to ``inner.get_closure`` | identical to ``inner`` |
| ``TCAClosure.override_at_ell(ell)`` | ``ell ≥ 0`` | ``True`` iff ``ell == 2`` | — |
| ``TCAClosure.tca_scalars(*, source_T, source_E, Gamma_T, H_local)`` | ``Gamma_T ≥ 0`` finite, ``H_local > 0`` finite | ``(Θ_2, E_2)`` scalars via W6-04 ``solve_tca_closure`` | raises ``RuntimeError`` below ``Γ_T/H < threshold`` |
| ``TCAClosure.algebraic_closure(state, ell=2, eta, *, …)`` | ``ell == 2`` | ``PSTFTensor(ell=2)`` with ``m=0`` slot (index 2) carrying ``Θ_2``, zero elsewhere | PSTF |
| ``measure_closure_error(state_ref, driver, *, L_trunc, closure_ref, closure_trunc, driver_kwargs)`` | ``0 ≤ L_trunc ≤ state_ref.L``; ``driver_kwargs`` must include ``eta`` | ``dict[int, float]`` — Frobenius-norm of per-ℓ ``dy/dη`` difference | same units as ``dy/dη`` |
| ``build_default_closure(L_max, strategy_name, …)`` | ``L_max ≥ 0``; ``strategy_name`` ∈ {``hardcut``, ``freestream``, ``powerlaw``, ``tca``} (case-insensitive) | Fresh ``ClosureStrategy`` instance | raises ``ValueError`` on unknown name |

All strategies **return a fresh PSTFTensor** (never an alias into ``state.tensors``); within-tower queries return defensive copies matching LB-2a HardCut precedent (verified by C-03, C-03b).

## 3. Phys-math audit ledger

| Check | Result | Evidence |
|---|---|---|
| HardCut: ``Π_{L+1} = Π_{L+2} = 0`` above tower | ✅ | ``test_c01_hardcut_returns_zero_above_tower`` (C-01) |
| FreeStream: MB-1995 eq (53) in the ``m=0`` scalar limit | ✅ | ``test_c05_freestream_matches_ma_bertschinger_recursion`` (C-05) |
| FreeStream: per-m lift (tensor generalisation of MB) | ✅ | ``test_c05b_freestream_per_m_recursion_off_axis`` (explicit hand-check of the all-ones tower) |
| FreeStream: two-step recursion for ``Π_{L+2}`` | ✅ | ``test_c06_freestream_two_step_recursion`` against hand-rolled two-step scalar |
| FreeStream: ``k = 0`` degenerates to HardCut | ✅ | ``test_c04_freestream_k_zero_is_hardcut`` (C-04) |
| FreeStream: ``η = 0`` → zero (numerator/denominator guard) | ✅ | ``test_c04b_freestream_eta_zero_is_hardcut`` |
| PowerLaw: ``Π_{L+1} = Π_L × (L/(L+1))^α`` slot-by-slot | ✅ | ``test_c07_powerlaw_scaling_at_ell_plus_1`` parametrised over α ∈ {1, 2, 2.7, 3} |
| PowerLaw: ``Π_{L+2}`` extension | ✅ | ``test_c08_powerlaw_scaling_at_ell_plus_2`` |
| PowerLaw: ``α ≤ 0`` rejected at construction | ✅ | ``test_c08b_powerlaw_alpha_zero_raises`` |
| TCA: ``override_at_ell(ℓ)`` == True iff ℓ==2 | ✅ | ``test_c09_tca_override_at_ell_2_only`` (C-09) |
| TCA: algebraic closure bit-identical to ``solve_tca_closure`` | ✅ | ``test_c10_algebraic_closure_bit_identical_to_w604`` compares both ``Θ_2`` tensor and ``(Θ_2, E_2)`` scalars |
| TCA: threshold gating raises below ``Γ_T/H < 100`` | ✅ | ``test_c11_below_threshold_algebraic_closure_raises`` |
| TCA: ``get_closure`` delegates to ``inner`` exactly | ✅ | ``test_c12_tca_get_closure_delegates_to_inner`` |
| PSTF invariants preserved under all strategies | ✅ | ``test_c15_driver_integration_smoke`` parametrised over 4 strategies |
| FLRW limit (σ=0): all four strategies agree bit-for-bit | ✅ | ``test_c15b_flrw_limit_closures_agree_at_zero_shear`` |
| ``measure_closure_error`` is zero when ``L_trunc == state_ref.L`` with identical closures | ✅ | ``test_c14_self_comparison_is_exact_zero`` |
| ``measure_closure_error`` is strictly > 0 at T7-affected ranks when truncating | ✅ | ``test_c13_shear_driven_closure_error_finite_and_positive`` verifies err(ℓ=2), err(ℓ=3) > 0 while err(ℓ=0) = err(ℓ=1) = 0 |

### Per-m lift as tensor generalisation of the MB scalar recursion

MB-1995 eq (53) is a scalar-along-k̂ recursion on the Legendre coefficients Π_ℓ(k). In the PSTF real-spherical-harmonic packing used at LB-2a, the axisymmetric (``m = 0``) scalar corresponds to the ``m = 0`` amplitude slot at index ℓ of the ``(2ℓ+1,)``-packed array. For off-axis (``m ≠ 0``) anisotropic states, the exact covariant free-streaming recursion involves Wigner-3j angular couplings — we adopt the simplest consistent generalisation: apply the MB scalar recursion **per-m**, matching the ``m``-slot of Π_L and Π_{L-1} to the corresponding ``m``-slot of the target Π_{L+1}. This is exact in the axisymmetric limit (matches MB bit-for-bit; C-05 at atol 1e-12) and preserves PSTF rank; it is an approximation for off-axis modes, flagged as F1 below.

## 4. Equation-to-code mapping

| Spec formula | Code path | Hand-verification |
|---|---|---|
| ``Π_{L+1} = ((2L+1)/(kη)) Π_L − Π_{L-1}`` (MB eq 53) | ``FreeStreamingClosure.get_closure`` upward loop; ``coeff = (2 ell_prev1 + 1) / k_eta`` applied to ``_per_m_slot_mapping(Pi_prev1, ell_prev1, ell_target)`` | C-05, C-05b, C-06 |
| ``Π_{L+1} = Π_L × (L/(L+1))^α`` (Kolb §9.4) | ``PowerLawExtrapolationClosure.get_closure``; ``scale = (L/ell_req)^α × _per_m_slot_mapping`` | C-07, C-08 |
| ``Π_2 = Γ_T M^{-1} · (S_T, S_E)`` (W6-04) | ``TCAClosure.tca_scalars`` → ``solve_tca_closure``; returns ``(Θ_2, E_2)``; stored into ``PSTFTensor(ell=2)`` at index 2 (m=0 slot) | C-10 (bit-identical) |
| Γ_T / H gating | ``TCAClosure.tca_scalars`` raises ``RuntimeError`` if ``Gamma_T / H_local < gamma_threshold_over_H`` | C-11 |
| ``err_ℓ = ||dy_ref_ℓ − dy_trunc_ℓ||_F`` (spec §8) | ``measure_closure_error`` ``np.sqrt(np.sum(diff**2))`` per ℓ over the ``(2ℓ+1,)`` component arrays | C-13, C-14 |

No dead code; TCAClosure's algebraic branch is not wired into ``hierarchy_rhs_photon`` (by design — LB-5 integrator's ODE-vs-algebraic dispatch is the consumer), but C-10 exercises the code path directly.

## 5. Numerical / pipeline audit

| Item | Finding |
|---|---|
| Solver suitability | LB-3 introduces no ODE solvers; all four strategies are pure algebra on ``PSTFTensor`` components. Integration smoke at C-15 uses the LB-2b driver unchanged (non-stiff at zero collision). |
| Tolerance sensitivity | C-05..C-08 pass at ``atol ≤ 1e-12``; C-10 bit-identical (``1e-14``). The largest per-m slot transfer at ℓ=8 still inherits the LB-2a ε·3^ℓ round-trip bound (~7e-11) — well below any C-test tolerance. |
| Overflow / underflow | Division by ``kη`` guarded by ``k_eta_floor = 1e-30`` in ``FreeStreamingClosure``; PowerLaw at ``state.L == 0`` bypasses the ``L/ell_req`` division (returns ``zero_pstf``); ``gamma_T > 0`` strictly enforced by the underlying ``solve_tca_closure``. |
| PSTF invariants under closure | Per-m slot lift preserves STF-ness: the packed components of a real-spherical-harmonic rank-ℓ tensor are dual to the Q_ℓ basis, and zero-padding outer |m| slots does not introduce trace or asymmetry. Verified empirically by C-15 (``verify_pstf_invariants`` at every ℓ after one RHS call). |
| Interpolation artifacts | None at LB-3 — all evaluations are at fixed ``η`` (no grid lookup). The shear proxy at C-13/C-14 reuses LB-2b's nearest-grid ``proper_shear_at_eta``, inheriting F2 from LB-2b (flagged for LB-5). |
| State mutation | ``get_closure`` returns fresh ``PSTFTensor`` objects with a ``.copy()`` on every within-tower read (HardCut precedent); C-03 verifies that modifying the returned tensor does not propagate back to ``state.tensors``. |
| Determinism | All strategies are pure functions of ``(state, ell_requested)`` (plus bound ``k``/``η`` for FreeStream). TCA's cached CanonicalDecision is constructed with fixed numerical inputs (no RNG). |
| Baseline reproduction | Full LB-2a + LB-2b suite unchanged: 2,322 baseline → 2,322 unchanged + 47 new = 2,369. |

## 6. Ranked failure modes

| ID | Type | Severity | Summary | Action |
|---|---|---|---|---|
| F1 | physics | P2 | ``FreeStreamingClosure`` uses a *per-m* slot-by-slot lift of MB-1995 eq (53), which is exact only in the axisymmetric (``m=0``) limit. For an off-axis anisotropic mode the true covariant free-streaming recursion involves Wigner-3j angular couplings between ``(ℓ, m)`` and ``(ℓ ± 1, m')``. Error scales as the off-axis PSTF power fraction. Acceptable at LB-3 (baseline reference for axisymmetric Bianchi I) — the polarisation-hierarchy LB-4 session will revisit for E/B-mode closure where off-axis anisotropy matters. | Documented; not repaired. Spec §5 updated with a "per-m lift" paragraph and F1 cross-reference. |
| F2 | interface | P2 | ``measure_closure_error`` signature deviates from spec §8 ``(state, L_ref, L_trunc, …)`` — collapsed to ``(state_ref, L_trunc, …)`` because the "reference tower" is naturally the deeper ``state_ref`` (its own ``.L`` fixes ``L_ref``). The spec §11.5 C-tests were updated in-session to the new signature; the §8 narrative still references the old prose. | Minor spec doc polish deferred — not load-bearing; §11 is the authoritative test list. |
| F3 | implementation | P3 | ``TCAClosure._always_allowing_tca_decision`` constructs a permissive ``CanonicalDecision`` at the algebraic step, bypassing the actual physical gating (β-policy, σ-floor, source tangency). This mirrors the pattern used in the W6-04 test suite (``_allowing_decision``) and is acceptable while the TCA branch is not wired into production integration (LB-3 exercises it only via C-10..C-12 tests). LB-5 integrator must thread the *real* ``CanonicalDecision`` derived from the hierarchy state at each η. | Flagged for LB-5 integrator session; TCA docstring notes the requirement. |

No P0 / P1 items.

## 7. Verifier results

| Verifier | Result | Notes |
|---|---|---|
| Physics (formula + limits) | **PASSED** | MB eq (53) exact in axisymmetric limit (1e-12); Kolb power-law exact per-m (1e-14); TCA bit-identical to W6-04 (1e-14); FLRW limit (σ=0) bit-identical across all four strategies. |
| Code (contract satisfaction) | **PASSED** | All four strategies satisfy ``ClosureStrategy`` Protocol (C-02); shape/rank validated at every call (C-03); state never mutated (C-03b). TCA's algebraic extension raises cleanly on out-of-scope inputs (ell ≠ 2 → ValueError; Γ_T/H below threshold → RuntimeError). |
| Numerical (stability + regression) | **PASSED** | 2,369 / 2,369 green (baseline 2,322 + 47 new); PSTF invariants preserved under driver integration at every ℓ; no NaN/Inf on the shear-driven Bianchi I fixture. |

## 8. Minimal repair plan — applied in-session

No P0 / P1 repairs needed. Three doc-level tightenings applied:

| Patch | Target | Status |
|---|---|---|
| A | `03_closure_truncation_spec.md §3` — new §3.1/§3.2/§3.3 reconciling the ``get_closure`` single-method protocol with the TCA algebraic-override extension | ✅ |
| B | `03_closure_truncation_spec.md §4` — implementation note clarifying that all four strategies expose ``get_closure`` and that the ``closure_next`` / ``closure_next_next`` pseudocode forms are pedagogical | ✅ |
| C | `03_closure_truncation_spec.md §10.2`, `§11.1..§11.4` — new ``build_default_closure`` signature and revised test table referencing ``get_closure`` | ✅ |

## 9. Minimal test set (delivered — 47 new tests)

**Baseline reproduction**: ``test_c01_hardcut_returns_zero_above_tower``, ``test_c05_freestream_matches_ma_bertschinger_recursion``, ``test_c07_powerlaw_scaling_at_ell_plus_1``, ``test_c10_algebraic_closure_bit_identical_to_w604``, ``test_c14_self_comparison_is_exact_zero`` — pass criteria ``1e-12`` .. ``1e-14``.

**Edge / adversarial**: ``test_c04b_freestream_eta_zero_is_hardcut``, ``test_c08b_powerlaw_alpha_zero_raises``, ``test_c11b_algebraic_closure_rejects_non_quadrupole_ell``, ``test_c14b_input_validation``, ``test_freestream_validates_inputs``, ``test_negative_ell_rejected_by_all_strategies``, ``test_tca_rejects_bad_inner``.

**Physics sanity**: ``test_c04_freestream_k_zero_is_hardcut``, ``test_c05b_freestream_per_m_recursion_off_axis``, ``test_c06_freestream_two_step_recursion``, ``test_c09_tca_override_at_ell_2_only``, ``test_c11_below_threshold_algebraic_closure_raises``, ``test_c12_tca_get_closure_delegates_to_inner``, ``test_c13_shear_driven_closure_error_finite_and_positive``, ``test_c15b_flrw_limit_closures_agree_at_zero_shear``.

**Numerical stability**: ``test_c15_driver_integration_smoke`` (parametrised over 4 strategies), ``test_c03b_within_tower_returns_copy``.

**Regression**: full bass+tsc run — **2,369 green** (baseline 2,322 + 47 new).

## 10. 최종 판정

* **치명적 오류 있음 / 부분 통과 / 통과** → **통과** (no P0/P1; three documented P2/P3 items)
* **지금 당장 구현/수정한 1개**: spec §3 / §10.2 / §11 doc tightening to reconcile the LB-2a-shipped ``get_closure`` protocol with the LB-3 TCA algebraic extension. No numeric change; purely contract clarification so future readers do not follow the outdated multi-method sketch.
* **지금 손대면 안 되는 1개**: rewriting ``FreeStreamingClosure`` with full Wigner-3j angular coupling. The per-m lift is sufficient for the axisymmetric Bianchi I regime that LB-3 targets, and a full off-axis generalisation belongs with the E/B-mode polarisation closure at LB-4 where the off-axis structure is physically first-class.

## Gallery refresh

``plots/physics_gallery/09_pstf_hierarchy/`` extended by 2 LB-3 plots (14 total):

* ``13_closure_error_vs_L_trunc.png`` — per-ℓ Frobenius-norm of ``dy/dη`` difference between HardCut at ``L_trunc ∈ {2,…,6}`` and the ``L_ref = 6`` reference run on a Bianchi-I-like tower. Physically-correct pattern emerges: ``ℓ=4`` error peaks at ``L_trunc = 4`` (T7 references Π_6), ``ℓ=3`` at ``L_trunc ∈ {3, 4}`` (T7 references Π_5; T3 references Π_4 at ``L_trunc=3``), ``ℓ=2`` at ``L_trunc ∈ {2, 3}`` (T7 references Π_4 / Π_3); ``ℓ=0, 1`` are flat at the 1e-18 floor because the T3/T7 stencil at ℓ ∈ {0, 1} does not reference ranks above the truncation.
* ``14_closure_strategy_comparison.png`` — per-ℓ ``dy/dη`` norm for all four strategies on an identical Bianchi-I state, with a right-panel residual-vs-HardCut. Confirms the closure activates only at ``ℓ = L_max`` (where T3/T4 use Π_{L_max+1} and T7 uses Π_{L_max+2}); ``FreeStream`` and ``PowerLaw`` diverge from ``HardCut`` by ~1e-8 at ``ℓ=4`` and ~1e-10 at ``ℓ=3`` (via one T7 cascade); ``TCA ∘ HardCut`` coincides with bare ``HardCut`` because the algebraic override is not invoked on the tower-top path.

Both plots were visually inspected; physical behaviour matches spec §2 / §6 expectations (T7 stencil width 2 upward → error ring at ranks {L_trunc, L_trunc−1}; closure activates at the tower top only).

## Outstanding items carried forward

* **F1** (P2): ``FreeStreamingClosure`` per-m lift is exact only for axisymmetric (``m=0``) states. Off-axis generalisation via Wigner-3j deferred to LB-4 polarisation closure.
* **F2** (P2): ``measure_closure_error`` spec §8 narrative not yet fully rewritten for the collapsed ``(state_ref, L_trunc)`` signature. §11.5 test table is authoritative and matches the code.
* **F3** (P3): ``TCAClosure._always_allowing_tca_decision`` bypasses the real ``CanonicalDecision`` gating — intentional at LB-3 (only exercised by tests), must be replaced by a hierarchy-state-derived decision in LB-5.
