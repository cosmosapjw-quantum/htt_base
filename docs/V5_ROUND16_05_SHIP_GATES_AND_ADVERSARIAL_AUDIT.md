# V5 Round-16 — Ship Gates & Adversarial Audit Protocol
_Authority: this doc + 00. Status: implementation-ready._

This document is the cross-cutting ship-gate / audit reference for Round-16. It (a) re-anchors the 15-stage `GATE_LADDER` with Round-16 enrichments, (b) provides the adversarial audit template applied at every PR, (c) gives the per-tier (A/B/C) ship criteria, and (d) catalogues forbidden patterns that must be detected before any release.

## 1. The 15-stage gate ladder (Round-16 frozen content)

The gate names remain identical to the Round-15 freeze. The *content* (forbidden_shortcut_checks, known_limit_checks, metadata) is enriched with Round-16 audit-driven additions.

| Gate # | Name | New required check (Round-16) | Closes |
|--------|------|-------------------------------|--------|
| 1 | `authority_freeze` | (none) | — |
| 2 | `tensor_helper_correctness` | (none) | — |
| 3 | `family_registry_freeze` | (none) | — |
| 4 | `geometry_diagnostics_gate` | `S_AB_nonzero_for_non_FLRW` (probe P2 of doc 03 §9) | G3 |
| 5 | `matter_projection_gate` | `tilted_species_projection_uses_evolved_beta` | G4 |
| 6 | `background_core_gate` | `codazzi_residual_below_1e-6_throughout_run` | G4 |
| 7 | `exact_thomson_gate` | (existing: `no_flrw_only_collision_shortcut`) | — |
| 8 | `visibility_history_gate` | `tilted_visibility_evaluated_with_evolved_beta` | G4 |
| 9 | `tilt_boost_separation_gate` | `tilt_evolution_status` ∈ {"evolved", "frozen_diagnostic"} | G4 |
| 10 | `ic_provenance_gate` | `template_card_authorized` propagated from runtime_controls | G9 |
| 11 | `family_backend_gate` | `mode_mixing_block_populated_when_sigma_2M_nonzero` | G2 |
| 12 | `hierarchy_layout_gate` | `mass_matrix_non_identity_for_class_b_or_anisotropic` | G3 |
| 13 | `production_cutoff_gate` | `D_2_converges_under_lmax_sweep_within_1e-3` | G1, G2 |
| 14 | `output_split_gate` | `b_mode_output_support`, `map_output_support` (R15-AUDIT-PATCH P-05/P-08) | G5, G10 |
| 15 | `fitting_gate` | `dataset_kind_real_planck_only_when_template_card_authorized_and_15_gates_open` | G8 |

### 1.1 New `forbidden_shortcut_checks` semantics

For Round-16, every gate carries (at minimum) these Boolean checks. A `False` value sends `passed=False` and the gate fails closed.

```python
# Common to gates 7..15:
"no_flrw_zero_b_marketed_as_prediction": bool   # G5
"no_unpopulated_map_marketed_as_output":  bool   # G10
"no_silent_template_card_ic_promotion":   bool   # G9
"no_static_beta_marketed_as_evolved_tilt":bool   # G4 (NEW)
"no_axis_aligned_only_marketed_as_full_family": bool  # G3 (NEW)
"no_synthetic_data_marketed_as_planck":   bool   # G8 (NEW)
"no_mass_identity_marketed_as_classB_kernel":   bool  # G3 (NEW; gate 12)
"no_diagonal_RHS_marketed_as_bianchi_anisotropy": bool  # G2 (NEW; gate 11)
```

Each check is implemented as a runtime invariant in the corresponding `*_gate_bundle` builder. Any check returning `False` produces a `GateBundle.passed=False` and (transitively) blocks downstream gates.

### 1.2 Code locations

```
bass/validation/ver3_gate_stop.py        # GATE_LADDER + hard_gate_before_fitting (existing)
bass/runtime/gate_fragments.py          # per-gate bundle builders (extend in Round-16)
bass/forward/ver3_output_archive.py     # output_split_gate_bundle (already extended)
bass/runtime/test_gate_fragments_*.py    # per-gate regression
```

Round-16 PRs that touch any gate bundle MUST update `bass/validation/test_ver3_gate_stop.py` to verify the new `forbidden_shortcut_checks` are exercised.

## 2. Tier-by-tier ship criteria (canonical)

This is the **release decision tree** for the manuscript and any external claim:

### 2.1 Tier-A — FLRW closure

**Sufficient PRs**: S1 (Codazzi-tilt) + S2 (IMEX-ARK4) + S5 (FLRW IC) + S13 (Python D_2 closure) + S15 (production switch).

**Allowed claims**:
- "PSTF Python-side D_2 closure at 1002.086744 μK² bit-identical to MB-95 production path."
- "FLRW + Type I + Type V + Type IX with full mode coverage in our PSTF/tetrad solver."
- "Exact electron-frame Thomson collision with non-perturbative `γ_e (1 - v_e·ê)` rate."
- "Codazzi-consistent tilted background evolution via King-Ellis exact ODE."

**Forbidden claims**:
- "Bianchi anisotropy spectrum" (requires Tier-B).
- "Data-fitted" (requires Tier-C).
- "11-family support" without the explicit "registry-complete + Tier-A solver-complete" hedge.

**Manuscript scope**: Phase-1 figures (D_2 anchor, FLRW C_ℓ vs CAMB, IMEX cosmological-range stability proof).

### 2.2 Tier-B — Bianchi anisotropy

**Sufficient PRs**: Tier-A + S3 (RHS k-mixing scalar) + S4 (RHS k-mixing tensor) + S6 (off-axis Class-A intrinsic) + S7 (off-axis Class-B) + S8 (Type V LoS) + S9 (Type IX LoS) + S10 (solvable collocation LoS) + S11 (B-mode projector) + S12 (real-space maps).

**Allowed claims**:
- "Non-trivial Bianchi anisotropy spectrum predictions for all 11 types with full mode coverage (II, III, IV, VI₀, VI_h, VII₀, VII_h, VIII no longer axis-aligned-only)."
- "B-mode prediction via Wigner-D Bianchi-tensor projector (Path B)."
- "T(n̂)/Q(n̂)/U(n̂) HEALPix maps as deterministic forward-model output."
- "Family-specific IC seeds enforced by the 15-stage gate ladder (template_card guard)."

**Forbidden claims**:
- "Real-data fitted" (requires Tier-C).
- "Statistical detection" (requires Tier-C with null ensemble + FPR).
- "Bound on Bianchi tilt" (requires MES full-cov + Planck likelihood).

**Manuscript scope**: Phase-2 figures (Bianchi T-only and T+E spectra; B-mode; map-domain morphology).

### 2.3 Tier-C — Statistics-grade with real data

**Sufficient PRs**: Tier-B + S14 (real-data Planck likelihood scaffold) + ABSolve cross-validation (5% per-ℓ in T+E for at least Type V at small σ).

**Allowed claims**:
- "Planck-likelihood-fitted Bianchi parameter constraints."
- "Map-domain MES full-covariance bound with explicit nuisance projection (local boost, mask, foreground)."
- "Information gain `I_j^{morph}` from BiPoSH off-diagonals over diagonal MES."

**Forbidden claims** (still):
- "Detection of Bianchi cosmology" without explicit FPR + null ensemble + PPC.
- "Family identification" without C5-tier criteria from `ver2_upgrade x_Q_F_Pi_G`.

**Manuscript scope**: Phase-3 fitted-parameter table; full MES corollary; full atlas observables vector.

### 2.4 Tier promotion table

| Promotion | Sufficient new PRs | Audit gate that locks it |
|-----------|---------------------|-------------------------|
| Tier-A → Tier-B | S3, S4, S6, S7, S8, S9, S10, S11, S12 | gate 11 + 12 + 14 (b_mode_output_support, map_output_support, mode_mixing_block) |
| Tier-B → Tier-C | S14 + ABSolve agreement | gate 15 + dataset.kind whitelist + null ensemble FPR ≤ α |

## 3. Adversarial audit protocol (PR-level)

Every PR-S* in 00 §2 must pass the following audit, with results pasted into the PR description. The audit is a **code-checkable predicate set**, not a vibes review.

### 3.1 Detection probe set (10 axes)

Each probe maps to a concrete grep / test / metadata check.

```
A1. TOY / NAIVE APPROXIMATION
   Probe: grep -nE '(?i)\b(toy|naive|mock|fake|placeholder|approx|dummy|temp[a-z_]*)\b' \
          bass/<changed_modules>
   Allowed: imports of test fixtures, names containing 'approximation_status' metadata
            keys, removed/justified-with-cite/downgraded-with-flag.
   Failure: any production identifier whose value is a stub.

A2. PRETEND PERTURBATION AS NONPERTURBATIVE
   Probe: grep -nE '(small[_\s]*beta|small[_\s]*v|first[_\s]*order)' bass/<changed_modules>
   Allowed: explicit linearization in /validation/ with linearization_status flag.
   Failure: linearized form on the production RHS without an audit-time switch.

A3. TEMPORARY ANALYTIC MODEL
   Probe: grep -nE '(static|frozen_diagnostic|placeholder|hardcoded)' bass/<changed_modules>
   Allowed: metadata flags (component_status, *_block_reason).
   Failure: hard-coded numeric value in production where a runtime computation is expected.

A4. MOCK / SURROGATE / SYNTHETIC ONLY
   Probe: assert dataset.kind whitelist forbids real-data fitting unless explicit
          allow_real_data flag flipped + all 15 gates open + template_card_authorized=True
          for any non-strong family.
   Failure: a code path where real data is silently swapped with a synthetic surrogate.

A5. TILT & ANISOTROPY CORRECTION MUST BE APPLIED
   Probe: for every shear/curvature/source term, verify its tilt-induced correction
          (sinh β, γ_e, v_e·ê) is at the same code-block level (no asymmetric
          application). Specifically: the same `if tilt_active:` guard wraps both
          the tilt-collision and the tilt-source contributions, never just one.
   Failure: tilt is applied to collision but dropped from the source builder, or
            vice versa.

A6. FAMILY-SPECIFIC CODE PATH SILENTLY FLRW
   Probe: for each non-FLRW family at σ ≠ 0, run a probe transfer and assert
          |Δ_ℓ^family - Δ_ℓ^FLRW| / |Δ_ℓ^FLRW| ≥ 1e-3 at ℓ ∈ {2..10}.
   Failure: a family backend whose output is bit-identical to FLRW.

A7. CONVERGENCE REGRESSION SWEEP
   Probe: re-run the production_cutoff_gate sweep at L_max ∈ {6, 10, 20, 40};
          assert |D_2(L) - D_2(L+Δ)| ≤ 1e-3 μK² for each pair AND the 4 D_2 values
          monotonically converge.
   Failure: D_2 oscillates with L_max or fails to converge.

A8. CROSS-CODE EXTERNAL REFERENCE (FLRW-touching PRs only)
   Probe: run test_flrw_external_camb (skips if camb not installed).
          When CAMB present: per-ℓ tolerance ≤ 1% at ℓ ∈ [2, 30].
   Failure: persistent ≥ 1% disagreement after PR-S13 closes.

A9. OPTIMIZATION FAIRNESS
   Probe: for any PR touching parallel/sparse/cache/batching, re-run
          test_optimization_fairness with bit-identity to ≤ 1e-12.
          Plus: ARK4 vs Rodas5P (FLRW) match to ≤ 1e-10.
   Failure: parallel result differs from sequential at ≤ 1e-12.

A10. GATE-LADDER REGRESSION
    Probe: hard_gate_before_fitting(prepared_bundle) returns
           allowed=True iff all 14 upstream gates are open AND the corresponding
           Round-16 forbidden_shortcut_checks all returned True.
    Failure: a gate marked `passed=True` while a Round-16 check should have failed.
```

### 3.2 Probe template (paste-into-PR)

```
## Adversarial Audit (PR-S<N>)

A1. Toy/naive: <files grepped> → <hits> [each: removed | justified-with-<paper> | downgraded]
A2. Pretend perturbation: <files> → <hits> [each: removed | linearization-flagged | n/a]
A3. Temp analytic model: <files> → <hits> [each: removed | metadata-flagged | n/a]
A4. Mock/surrogate: dataset.kind whitelist verified → <pass/fail>
A5. Tilt+anisotropy applied symmetrically: code-block check → <pass/fail>
A6. Family path non-FLRW: per-family probe → <pass for {II, III, IV, V, VI_0, VI_h, VII_0, VII_h, VIII, IX}>
A7. Convergence sweep: D_2(L_max=6/10/20/40) = <values>; max diff = <X> μK²
A8. CAMB cross-check: <pass/skip-if-no-camb> → <max per-ℓ diff X% at ℓ=Y>
A9. Optimization fairness: parallel-vs-sequential bit-identity → <max abs diff X>
A10. Gate ladder: hard_gate_before_fitting result → allowed=<bool>; missing=<list>

Adversarial verdict: <PASS | NEEDS-FIX>
```

## 4. Forbidden patterns catalogue

These are *banned constructs* that must be absent from production. Each carries a grep probe and audit gate.

| Pattern | Why banned | Probe | Audit gate |
|---------|-----------|-------|-----------|
| TCA pre-phase (unconditional analytic ℓ=2 replacement at startup) | Breaks Bianchi coupling structure (ROADMAP_v3 §3.1) | grep "tca_pre_phase\|tca_initial\|tca_seed" | A1, A2 |
| FLRW UFA on photons | Eats anisotropic transport (ROADMAP_v3 §3.1) | grep "ufa.*photon\|photon_ufa" | A1, A6 |
| Photon RSA | Destroys low-ℓ ISW + reionization signal (ROADMAP_v3 §3.1) | grep "rsa\|radiation_streaming" | A1 |
| Static β as production tilt | Violates G4 and "globally tilted" claim | grep "tilt_freeze=True" outside /validation/ | A5, gate 9 |
| Hard-coded Bessel j_ℓ for non-FLRW family | Violates G3 mode coverage | grep "j_ell\|spherical_jn" in bass/los/families/type_*.py | A6 |
| `M = sp.eye(N)` for Bianchi mass matrix | Violates G3 sparse-layout invariance | grep "mass_matrix.*eye\|identity_mass" | A6 + gate 12 |
| Single FLRW seed for non-strong family | Violates G9 IC provenance | grep "flrw_seed" in bass/los/families/type_{II,III,IV,VI,VIII}*.py | A6 + gate 10 |
| `b_mode_output_support="flrw_zero_only"` marketed as "B-mode prediction" | Violates G5 honest envelope | output_split_gate `forbidden_shortcut_checks` enforces | gate 14 |
| `map_output_support="not_implemented"` with non-None map fields | Violates G10 contract | `SolverCoreOutput.__post_init__` enforces | gate 14 |
| Synthetic data with `dataset.kind="planck2018"` | Violates G8 data-binding | `bass/inference/__main__.py` whitelist | gate 15 |
| Doppler source WITH 1/k factor | RETRACTED 2026-04-26 — adding `/k` is the false trail (parallel-cycle Appendix X, see `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md:9, 17, 405-407, 2218`); BASS's `v_b` is dimensionless `θ_b/k`, so `(g v_b)'` is canonical and `/k` would double-divide. Empirical: `/k` patch shifts D_2 by only -0.012% (vs 7-orders-of-magnitude gap). | grep `gradient.*gvb` and verify NO trailing `/ k`; assert `test_sharp_visibility_doppler_analytic_protects_no_over_k_patch` passes | A2 |

## 5. Per-PR closure checklist (paste into the PR)

```
□ Code change implements the spec in V5_ROUND16_<NN>_<NAME>.md §<X>
□ Adversarial audit (probe table) attached
□ All targeted tests pass (path: htt/bass/<module>/test_*.py)
□ No new gate is silently introduced (15 stages preserved; only forbidden_shortcut_checks may grow)
□ Forbidden patterns catalogue (§4 of this doc) re-checked: 0 hits
□ Performance: profiling output attached if PR touches the integrator/LoS/atlas
□ Tier promotion impact noted (or "no tier promotion") in PR title
□ CHANGELOG entry under [Unreleased] with the gap ID closed
□ CLAUDE.md §3 phase status updated (line 41–43) when PR-S13 / S15 lands
```

## 6. Round-16 → Round-17 gate handover

Round-17 inherits this gate ladder unchanged. New gaps surfaced during Round-16 implementation must:

1. Append a row to the gap registry in `V5_ROUND16_00_MASTER_PLAN.md §1`.
2. Add a corresponding `forbidden_shortcut_checks` field to the relevant gate.
3. Add a regression test under `bass/validation/`.

The audit-friendly pattern: every closed gap has (a) a name, (b) a code path that fails closed without the fix, (c) a regression test that catches the regression. No exceptions.

## 7. Cross-doc traceability

| Round-16 Gap | Doc 01 § | Doc 02 § | Doc 03 § | Doc 04 § | Test file |
|--------------|----------|----------|----------|----------|-----------|
| G1 (D_2 closure) | — | 1, 2 | 1 (canonical `(g v_b)'`; /k retracted), 2 | 1, 8 | `test_d2_pstf_closure.py` (xfail; real scope in `docs/V5_ROUND17_PR_S13_REAL_SCOPE.md`) |
| G2 (RHS k-mixing) | — | 2 | — | 2 | `test_mode_mixing_blocks.py`; `test_hierarchy_rhs_v16_flrw_limit.py` |
| G3 (off-axis modes) | 2 | 3 | 2.4 | 2.1, 2.2 | `test_off_axis_modes_per_family.py` |
| G4 (Codazzi tilt) | 3 | — | — | 9 | `test_background_codazzi_tilt_evolution.py` |
| G5 (B-mode) | — | 6 | 2.5 | — | `test_b_mode_projector.py` (PR-S11); `test_eb_mixing_under_parity_odd_shear.py` |
| G6 (non-FLRW e2e) | — | 4 | 2 | — | per-family `test_*_e2e.py` |
| G8 (real-data) | — | — | 6.1 | 9 | `test_planck_likelihood_scaffold.py` (PR-S14) |
| G9 (IC factories) | — | 4 | — | 9 | `test_seed_factory_per_family.py` |
| G10 (maps) | — | — | 3 | — | `test_map_producer.py` |
| G11 (fairness) | — | — | — | 6 | `test_optimization_fairness_v16.py` |

## 8. Self-CoVe of this gate document

| Q | Answer |
|---|--------|
| Q1. Are all 11 gaps from §1 of doc 00 owned by a gate? | Yes (§1 + §7 traceability table). |
| Q2. Does each new check have a matching forbidden pattern in §4? | Yes (§4 catalogue × §1.1 checks). |
| Q3. Does each tier (A/B/C) have a mutually exclusive PR set? | Yes (§2.4 promotion table). |
| Q4. Is the audit protocol applicable to a fresh PR? | Yes (§3.2 paste-into template). |
| Q5. Does the gate ladder block real-data fitting in any tier ≤ B? | Yes (gate 15 + dataset.kind whitelist + template_card_authorized). |
| Q6. Does the new gate content require breaking changes to existing tests? | Minimal: only `_solver_output()` test fixtures need `map_output_support: "not_implemented"` (already in R15-AUDIT-PATCH P-08). |
| Q7. Is the doc self-contained for a new session? | Yes — drop into a new session, read 00 → here, then start PR-S1 with the audit template ready. |
| Q8. Does this prevent stealth approximation reintroduction? | Yes: the §4 catalogue + §3.1 probe set + per-PR §5 checklist must all pass. Multi-layer defense. |

## 9. Hand-off statement

This document closes the Round-16 design package. A new session opening `docs/V5_ROUND16_*` finds:

1. **Doc 00**: Gap registry, sequencing, audit protocol, multi-agent debate consensus.
2. **Doc 01**: Background + geometry + Codazzi tilt + recombination/reionization extensions.
3. **Doc 02**: Hierarchy RHS k-mixing + off-axis + IC factories + collision + B-source.
4. **Doc 03**: LoS + maps + atlas + MES + statistics gate + real-data scaffold.
5. **Doc 04**: IMEX-ARK4 + sparse layout + adaptive controller + fairness + code-port.
6. **Doc 05** (this): Gate ladder + adversarial audit + ship criteria + forbidden catalogue.

Each PR-S* in 00 §2 references the relevant doc-section pair and ends with the §3.2 audit template. Tier-A closure (FLRW D_2 = 1002.086744 μK² Python-side bit-identical) is the first manuscript-blocking deliverable; Tier-B unblocks Bianchi-anisotropy figures; Tier-C unblocks data-fitted parameter tables.

The Round-15 audit patch closed visibility/enforcement debt; Round-16 closes the *substance* debt. After Tier-A + Tier-B + Tier-C close, the production switch in PR-S15 retires the MB-95 path and `sync_gauge_camb.rs` becomes legacy reference only — at which point the dual-track architecture concludes.

---

**End of Round-16 Design Package.** Begin implementation at PR-S1 (V5_ROUND16_01 §3).
