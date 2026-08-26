# Planck MES Observable-Irrep Formalism and Execution Plan

> **For agentic workers:** REQUIRED SUB-SKILL: execute one `PMI-WU-*` work unit at a time with test-first implementation, one read-only fresh-context review, and the work unit's explicit PASS transition. Do not create another planning package.

**Goal:** Replace the scalar-only Planck MES analysis surface with a typed observable-irrep carrier formalism, preserve the historical scalar result as a frozen baseline, and execute coordinate-mechanism, carrier, robustness, morphology, and injection studies without conflating observables with physical anisotropy states.

**Architecture:** Keep `JointAnisotropyState` as the physical pre-solver state; introduce a separate `ObservableIrrepState` for observed harmonic carriers; retain `MESAnchorSpec` as a one-way premise bound; and require an explicit content-bound response operator before any observable is interpreted as physical shear, vorticity, tilt, curvature, or Bianchi family. Centralize finite-null reducers so scalar, irrep, and template families share one exchangeable observation-inclusive engine.

**Tech Stack:** Python 3.12, NumPy, SciPy/healpy where already required, PyYAML for package validation, pytest, Git/GitHub content identities.

**Spec:** `docs/codex_handoff/planck_mes_observable_irrep_execution/FORMALISM_CONTRACT.yaml`

## Global Constraints

- Metric signature remains `(-,+,+,+)`; no new natural-unit convention is introduced.
- The exact canonical base is `changeset/pr324-mes-methodology-stack-20260826@3cdeaba39e164c911a26c5daa37f0e15b29614d3` with tree `47bdbb72aae62ca4280a96897f80028b1b910c20`.
- The planning predecessor is `analysis/planck-mes-extended-data-execution-20260826@2669a55ef230d1ca9e79c09d3344f7b15c50ac0e` and is superseded before its scalar-only 999-map runtime.
- Historical scalar ranks and the 301-row order are immutable regression controls.
- `ObservableIrrepState` and `JointAnisotropyState` are distinct non-coercible types.
- Scalar ceilings, scalar features, and covariances cannot manufacture a direction, vector, STF tensor, or physical state.
- Raw/downloaded observational inputs are read-only and never committed.
- Statistical families, tails, templates, rotations, amplitude grids, and rejection rules are frozen before outcomes are inspected.
- One fresh-context review and at most one targeted repair are allowed per work unit.
- The full repository suite is not a default gate.

---

## A. Authority and Scope

**Authority order**

1. latest explicit user decision;
2. live canonical repository branch and exact commit/tree;
3. merged or branch-authoritative code/tests/contracts;
4. accepted durable machine artifacts;
5. project documentation;
6. issue/PR history;
7. historical proposals;
8. transcript-only claims.

**Canonical authority**

```yaml
repository: cosmosapjw-quantum/htt_base
base_branch: changeset/pr324-mes-methodology-stack-20260826
base_sha: 3cdeaba39e164c911a26c5daa37f0e15b29614d3
base_tree: 47bdbb72aae62ca4280a96897f80028b1b910c20
planning_predecessor: 2669a55ef230d1ca9e79c09d3344f7b15c50ac0e
planning_branch: analysis/planck-mes-observable-irrep-execution-20260827
```

**User-locked scientific controls**

- `GENERIC_12=133/301`
- `RAW_REDUCED_10=110/301`
- `EPS_REDUCED_10=109/301`
- `MES_10=98/301`
- `ANCHORS_ONLY_2=78/301`
- `MORPHOLOGY_ONLY_8=88/301`
- observation minimum `multipole_l3_absdot_0=16/301`
- both MES ceiling local ranks `74/301`
- paired 300 CMB+noise remains the Paper-A primary; 999 CMB-only is separate robustness.
- Commander remains descriptive and cannot emit a finite rank.
- Planck-only outputs do not identify local boost versus global tilt or a Bianchi family.

**Non-goals**

No physical response invention, no posterior/likelihood, no NPIPE without admitted data, no Commander pseudo-null, no all-family native Bianchi atlas, no broad multi-probe inference, no performance-first refactor.

## B. P0/P1 Threat Catalogue

The machine authority is `P0_P1_THREAT_CATALOG.json`. Every row below has a test, assertion, or explicit blocked gate.

| ID | Severity | Current-task blocking | Trigger | Detector |
|---|---:|:---:|---|---|
| `PMI-FM-001` | P0 | yes | Planck ObservableIrrepState or harmonic coefficients are inserted into JointAnisotropyState fields or labeled as physical shear, vorticity, acceleration, tilt, curvature, or Bianchi family. | `python -m pytest -q tests/common/test_observable_irrep_state.py::test_observable_state_cannot_construct_or_impersonate_physical_state` |
| `PMI-FM-002` | P0 | yes | A scalar C_l, MES anchor, scalar feature row, or covariance is used to fabricate a direction, axis, vector, or STF tensor. | `python -m pytest -q tests/obsstat/test_observable_irrep_adapter.py::test_scalar_only_inputs_fail_closed` |
| `PMI-FM-003` | P0 | yes | The real-harmonic ell/m order, sqrt(2) factors, imaginary sign, frame, parity, units, or block cardinality is inconsistent across extraction, serialization, replay, or rotation. | `python -m pytest -q tests/integration/test_planck_irrep_carrier.py::test_carrier_round_trip_and_identity_binding` |
| `PMI-FM-004` | P0 | yes | Coordinate-dependent canonical multipole-axis signs are used as O(3)-invariant handedness or physical vector orientation. | `python -m pytest -q tests/obsstat/test_lowell_irrep_morphology.py::test_axis_sign_flips_leave_allowed_invariants_unchanged_and_forbid_signed_claims` |
| `PMI-FM-005` | P1 | yes | New runners continue passing untyped retained_alm arrays or scalar rows across module boundaries after ObservableIrrepState is introduced. | `python scripts/validate_planck_mes_irrep_execution_plan.py --implementation-diff-from 3cdeaba39e164c911a26c5daa37f0e15b29614d3` |
| `PMI-FM-006` | P0 | yes | The exact historical six-family ranks, minimum feature, local ranks, row order, or source package bytes are modified instead of preserved as a baseline. | `python -m pytest -q tests/integration/test_planck_mes_coordinate_mechanism_audit.py::test_legacy_exact_rank_locks_are_unchanged` |
| `PMI-FM-007` | P1 | yes | The ECDF reducer is not exactly leave-one-out, mishandles ties, or fails monotone-invariance/permutation-equivariance. | `python -m pytest -q tests/obsstat/test_finite_null_family.py::test_loo_ecdf_midrank_is_monotone_invariant_with_ties` |
| `PMI-FM-008` | P1 | yes | Carrier files omit row/order/frame/mask/beam/pixel/operator/source/layout identities, or identities bind declarations but not exact numeric content. | `python -m pytest -q tests/integration/test_planck_irrep_carrier.py::test_carrier_identity_binds_exact_numeric_content` |
| `PMI-FM-009` | P0 | yes | Reducers, tails, family membership, templates, orientation grids, amplitude grids, or rejection rules are selected or tuned after inspecting observed or injection outcomes. | `python -m pytest -q tests/contracts/test_planck_mes_irrep_preregistration.py` |
| `PMI-FM-010` | P0 | yes | Raw/downloaded observational inputs are mutated, symlink escapes are followed, partial files are admitted, or absent NPIPE/HSC payloads are declared available. | `python -m pytest -q tests/integration/test_planck_mes_extended_data_inventory.py` |
| `PMI-FM-011` | P1 | yes | A large-data Planck map pass reports success while serializing only scalar features and discarding retained harmonic coefficients. | `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py::test_success_terminal_requires_carrier_and_scalar_projection` |
| `PMI-FM-012` | P0 | yes | The new carrier/robustness lane overwrites or replaces the frozen V1 scalar packages or is represented as a new primary without explicit authority. | `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py::test_v1_packages_and_exact_results_are_unchanged` |
| `PMI-FM-013` | P0 | yes | Scalar features recomputed from serialized harmonic carriers do not match the scalar features stored from the same map/operator execution. | `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py::test_carrier_reproduces_every_scalar_feature_row` |
| `PMI-FM-014` | P0 | yes | The 999 inventory fills missing 00970, drops 00818, duplicates or reorders rows, or reports a denominator inconsistent with the ordered IDs. | `python -m pytest -q tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py::test_exact_official_999_inventory_and_order` |
| `PMI-FM-015` | P0 | yes | Three Commander simulations or partial files are used to emit a finite rank/p-value, or Commander is compared under a mismatched operator while called same-operator. | `python -m pytest -q tests/integration/test_planck_mes_commander_irrep.py::test_commander_cannot_emit_finite_rank_or_open_partial_inputs` |
| `PMI-FM-016` | P0 | yes | Templates are added after scalar feature extraction, or directly to post-operator carriers without applying the registered orientation-dependent mask/beam/operator response, while called end-to-end. | `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_every_template_orientation_has_content_bound_operator_response` |
| `PMI-FM-017` | P0 | no | A Bianchi VII_h template is used without exact template bytes, solver commit/tree, conventions, transfer provenance, and response/operator identity. | `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_native_bianchi_template_requires_exact_authority_or_is_deferred` |
| `PMI-FM-018` | P0 | yes | The observation contributes to its own mean/covariance/template whitening, covariance is singular or silently regularized, or orientation maximization is not applied identically to all rows. | `python -m pytest -q tests/obsstat/test_harmonic_template_score.py::test_leave_one_out_whitening_and_orientation_max_are_permutation_equivariant` |
| `PMI-FM-019` | P1 | yes | The analytic observable-STF benchmark template, native Bianchi template, or another registered candidate silently disappears from execution or is mislabeled as refuted. | `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_candidate_disposition_ledger_is_complete` |
| `PMI-FM-020` | P1 | yes | Codex creates another planning/audit package, performs a complete unrelated raw-tree hash sweep, or runs the full repository suite before the next objective transition. | `python scripts/validate_planck_mes_irrep_execution_plan.py --implementation-diff-from 2669a55ef230d1ca9e79c09d3344f7b15c50ac0e` |
| `PMI-FM-021` | P1 | no | The manuscript, abstract, claim ledger, or release metadata consumes planned, failed, unreplayed, or deferred outputs as successful scientific evidence. | `python -m pytest -q tests/paper/test_planck_mes_irrep_methods_paper.py::test_paper_requires_successful_replayed_evidence_and_claim_boundaries` |
| `PMI-FM-022` | P1 | yes | Any SHA mismatch is promoted directly to scientific-integrity failure without classifying immutable source, deterministic evidence, scientific numerical output, or packaging metadata. | `python -m pytest -q tests/contracts/test_planck_mes_identity_classification.py` |
| `PMI-FM-023` | P1 | yes | The eps1=0 branch is reported with excessive precision without the exact eps1 coefficients and a registered eps1 sensitivity band. | `python -m pytest -q tests/integration/test_planck_mes_coordinate_mechanism_audit.py::test_eps1_sensitivity_uses_active_authority_and_full_grid` |
| `PMI-FM-024` | P1 | yes | Required rank distributions, injection power curves, or operator-response diagnostics are generated but not inspected, or their plot audit is absent. | `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_plot_audit_binds_all_required_figures_and_findings` |

## C. Invariant/Test Matrix

| Requirement | Invariant | Failure mode | Mechanical detector | Work unit |
|---|---|---|---|---|
| `Separate observable and physical states` | `PMI-INV-LAYER-SEPARATION` | `PMI-FM-001` | `python -m pytest -q tests/common/test_observable_irrep_state.py::test_observable_state_cannot_construct_or_impersonate_physical_state` | `PMI-WU-001` |
| `Forbid scalar-to-irrep creation` | `PMI-INV-NO-SCALAR-FABRICATION` | `PMI-FM-002` | `python -m pytest -q tests/obsstat/test_observable_irrep_adapter.py::test_scalar_only_inputs_fail_closed` | `PMI-WU-001` |
| `Lock real-harmonic layout` | `PMI-INV-CARRIER-CONVENTION` | `PMI-FM-003` | `python -m pytest -q tests/integration/test_planck_irrep_carrier.py::test_carrier_round_trip_and_identity_binding` | `PMI-WU-004` |
| `Preserve unoriented-axis semantics` | `PMI-INV-AXIS-SIGN` | `PMI-FM-004` | `python -m pytest -q tests/obsstat/test_lowell_irrep_morphology.py::test_axis_sign_flips_leave_allowed_invariants_unchanged_and_forbid_signed_claims` | `PMI-WU-006` |
| `Migrate every consumer to the new boundary` | `PMI-INV-MIGRATION-COMPLETE` | `PMI-FM-005` | `python scripts/validate_planck_mes_irrep_execution_plan.py --implementation-diff-from 3cdeaba39e164c911a26c5daa37f0e15b29614d3` | `PMI-WU-001` |
| `Preserve exact legacy scalar baseline` | `PMI-INV-LEGACY-RANKS` | `PMI-FM-006` | `python -m pytest -q tests/integration/test_planck_mes_coordinate_mechanism_audit.py::test_legacy_exact_rank_locks_are_unchanged` | `PMI-WU-002` |
| `Make ECDF reducer monotone invariant` | `PMI-INV-ECDF-MONOTONE` | `PMI-FM-007` | `python -m pytest -q tests/obsstat/test_finite_null_family.py::test_loo_ecdf_midrank_is_monotone_invariant_with_ties` | `PMI-WU-002` |
| `Bind exact carrier provenance` | `PMI-INV-CARRIER-IDENTITY` | `PMI-FM-008` | `python -m pytest -q tests/integration/test_planck_irrep_carrier.py::test_carrier_identity_binds_exact_numeric_content` | `PMI-WU-004` |
| `Freeze statistical and injection specifications` | `PMI-INV-PREREGISTRATION` | `PMI-FM-009` | `python -m pytest -q tests/contracts/test_planck_mes_irrep_preregistration.py` | `PMI-WU-002` |
| `Protect and accurately classify inputs` | `PMI-INV-RAW-IMMUTABLE` | `PMI-FM-010` | `python -m pytest -q tests/integration/test_planck_mes_extended_data_inventory.py` | `PMI-WU-003` |
| `Require carrier on every expensive map pass` | `PMI-INV-NO-CARRIER-DROP` | `PMI-FM-011` | `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py::test_success_terminal_requires_carrier_and_scalar_projection` | `PMI-WU-004` |
| `Keep V1 primary immutable and V2 additive` | `PMI-INV-V1-IMMUTABLE` | `PMI-FM-012` | `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py::test_v1_packages_and_exact_results_are_unchanged` | `PMI-WU-004` |
| `Make carrier and scalar feature rows agree` | `PMI-INV-CARRIER-FEATURE-PARITY` | `PMI-FM-013` | `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py::test_carrier_reproduces_every_scalar_feature_row` | `PMI-WU-004` |
| `Lock the official 999 inventory` | `PMI-INV-SMICA-999-ORDER` | `PMI-FM-014` | `python -m pytest -q tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py::test_exact_official_999_inventory_and_order` | `PMI-WU-005` |
| `Forbid Commander pseudo-calibration` | `PMI-INV-COMMANDER-NO-RANK` | `PMI-FM-015` | `python -m pytest -q tests/integration/test_planck_mes_commander_irrep.py::test_commander_cannot_emit_finite_rank_or_open_partial_inputs` | `PMI-WU-007` |
| `Apply injection through the real operator response` | `PMI-INV-OPERATOR-AWARE-INJECTION` | `PMI-FM-016` | `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_every_template_orientation_has_content_bound_operator_response` | `PMI-WU-006` |
| `Require native template authority or defer` | `PMI-INV-NATIVE-TEMPLATE-AUTHORITY` | `PMI-FM-017` | `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_native_bianchi_template_requires_exact_authority_or_is_deferred` | `PMI-WU-006` |
| `Use exchangeable leave-one-out harmonic score` | `PMI-INV-LOO-TEMPLATE-SCORE` | `PMI-FM-018` | `python -m pytest -q tests/obsstat/test_harmonic_template_score.py::test_leave_one_out_whitening_and_orientation_max_are_permutation_equivariant` | `PMI-WU-006` |
| `Track every template candidate` | `PMI-INV-CANDIDATE-COVERAGE` | `PMI-FM-019` | `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_candidate_disposition_ledger_is_complete` | `PMI-WU-006` |
| `Force execution after this package` | `PMI-INV-NO-SUCCESSOR-PLAN` | `PMI-FM-020` | `python scripts/validate_planck_mes_irrep_execution_plan.py --implementation-diff-from 2669a55ef230d1ca9e79c09d3344f7b15c50ac0e` | `PMI-WU-002` |
| `Keep manuscript evidence executed and replayed` | `PMI-INV-PAPER-EVIDENCE` | `PMI-FM-021` | `python -m pytest -q tests/paper/test_planck_mes_irrep_methods_paper.py::test_paper_requires_successful_replayed_evidence_and_claim_boundaries` | `PMI-WU-007` |
| `Classify identity mismatches before blocking` | `PMI-INV-IDENTITY-CLASSIFICATION` | `PMI-FM-022` | `python -m pytest -q tests/contracts/test_planck_mes_identity_classification.py` | `PMI-WU-003` |
| `Expose eps1 premise sensitivity` | `PMI-INV-EPS1-SENSITIVITY` | `PMI-FM-023` | `python -m pytest -q tests/integration/test_planck_mes_coordinate_mechanism_audit.py::test_eps1_sensitivity_uses_active_authority_and_full_grid` | `PMI-WU-002` |
| `Inspect plots before claims` | `PMI-INV-PLOT-INSPECTION` | `PMI-FM-024` | `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_plot_audit_binds_all_required_figures_and_findings` | `PMI-WU-006` |

## D. Ordered Work Units

### PMI-WU-001 — Introduce the observable-irrep SSOT and cross-layer firewalls

**Objective.** Create one typed observable-irrep state for low-ell harmonic carriers and route all new adapter boundaries through it without changing physical JointAnisotropyState semantics.

**Observable success.** Targeted tests pass for exact ell layouts, serialization, typed absence, directional adapter parity, scalar-only refusal, and physical/observable non-coercion; one small formalism registry is committed.

**Preconditions**
- `test "$(git rev-parse origin/changeset/pr324-mes-methodology-stack-20260826)" = 3cdeaba39e164c911a26c5daa37f0e15b29614d3` → exact canonical base SHA
- `git merge-base --is-ancestor 2669a55ef230d1ca9e79c09d3344f7b15c50ac0e HEAD` → planning predecessor is an ancestor
- `python scripts/validate_planck_mes_irrep_execution_plan.py` → PASS

**Load-bearing invariants**
- `PMI-INV-LAYER-SEPARATION` (P0): ObservableIrrepState is not a subclass, alias, payload-compatible substitute, or accepted constructor input for JointAnisotropyState.  
  Check: `python -m pytest -q tests/common/test_observable_irrep_state.py::test_observable_state_cannot_construct_or_impersonate_physical_state`
- `PMI-INV-NO-SCALAR-FABRICATION` (P0): Scalar-only inputs cannot create an observable irrep block.  
  Check: `python -m pytest -q tests/obsstat/test_observable_irrep_adapter.py::test_scalar_only_inputs_fail_closed`
- `PMI-INV-IRREP-LAYOUT` (P0): Spin-0 ell blocks require exactly 2*ell+1 real components in the registered sign/order convention.  
  Check: `python -m pytest -q tests/common/test_observable_irrep_state.py::test_real_harmonic_layout_and_round_trip`

**Ordered implementation**
1. **PMI-STEP-001** — Write and run RED tests for exact block cardinality, layout identity, serialization, typed absence, physical-state non-coercion, and scalar-only refusal.  
   Files: `tests/common/test_observable_irrep_state.py`, `tests/obsstat/test_observable_irrep_adapter.py`
2. **PMI-STEP-002** — Implement ObservableIrrepBlock, ObservableIrrepState, ObservableFieldParity, ObservableRepresentation, real_irrep_layout, canonical content identities, and strict payload replay.  
   Files: `htt/src/common/observable_irrep_state.py`
3. **PMI-STEP-003** — Implement packed-alm, retained-real-vector, and PR-326 directional-moment adapters; bind frame/operator/source identities and emit the layer registry.  
   Files: `htt/obsstat/observable_irrep_adapter.py`, `docs/research_program/post_pr275/observable_irrep_formalism_v1.yaml`
4. **PMI-STEP-004** — Add the smallest architecture rule that prevents obsstat observable states from importing or constructing physical state internals.  
   Files: `scripts/architecture/test_import_boundaries.py`

**Verification**
- targeted: `python -m pytest -q tests/common/test_observable_irrep_state.py tests/obsstat/test_observable_irrep_adapter.py`
- negative: `python -m pytest -q tests/common/test_observable_irrep_state.py tests/obsstat/test_observable_irrep_adapter.py -k 'scalar or physical or missing or forged or layout'`
- regression: `python -m pytest -q tests/common/test_mes_directional_state.py tests/contracts/test_mes_observed_authority.py tests/contracts/test_orbit_catalogue_v3.py`
- integration: `python -m pytest -q scripts/architecture/test_import_boundaries.py`

**PASS →** Start PMI-WU-002 immediately and produce the first map-free objective result.

**FAIL →** Emit BLOCKED_BY_P0 or BLOCKED_BY_P1 with the exact failed invariant; do not widen either state type and do not create another plan.

### PMI-WU-002 — Centralize finite-null reducers and execute the coordinate-mechanism audit

**Objective.** Preserve the legacy finite-null result exactly while adding a leave-one-out ECDF midrank reducer and executing the analytic/factorial/tail/tie/eps1 mechanism audit on the frozen 301-row package.

**Observable success.** A replayed map-free result reports the exact analytic identities, four-cell factorial family table, legacy-versus-ECDF ranks, registered-tail sensitivity, tie masses, N_eff, Monte Carlo scale, and eps1 curves; all historical exact ranks remain unchanged.

**Preconditions**
- `python -m pytest -q tests/common/test_observable_irrep_state.py tests/obsstat/test_observable_irrep_adapter.py` → PMI-WU-001 accepted
- `test -f docs/generated/pr315_planck_smica_feature_replay.npz && test -f docs/generated/planck_mes_morphology/planck_mes_morphology.npz` → frozen map-free inputs present

**Load-bearing invariants**
- `PMI-INV-LEGACY-RANKS` (P0): The legacy reducer exactly reproduces all six historical family ranks, minimum coordinate, and MES local ranks.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_coordinate_mechanism_audit.py::test_legacy_exact_rank_locks_are_unchanged`
- `PMI-INV-ECDF-MONOTONE` (P1): The leave-one-out midrank ECDF score is exactly invariant under strictly increasing coordinatewise transforms, including ties.  
  Check: `python -m pytest -q tests/obsstat/test_finite_null_family.py::test_loo_ecdf_midrank_is_monotone_invariant_with_ties`
- `PMI-INV-FACTORIAL-SPEC` (P0): EPS, SQUARE_ONLY, CARRIER_ONLY, and MES families are frozen before execution and their interaction is reported without an additive decomposition claim.  
  Check: `python -m pytest -q tests/contracts/test_planck_mes_irrep_preregistration.py::test_factorial_family_and_interaction_registry_is_exact`
- `PMI-INV-EPS1-SENSITIVITY` (P1): The exact eps1 coefficients and the complete [0,1e-5] sensitivity grid are reported without interpreting eps1 as measured.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_coordinate_mechanism_audit.py::test_eps1_sensitivity_uses_active_authority_and_full_grid`
- `PMI-INV-PLOT-INSPECTION` (P1): Every required mechanism figure is hash-bound to a plot-audit entry with explicit findings.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_coordinate_mechanism_audit.py::test_plot_audit_binds_all_mechanism_figures`

**Ordered implementation**
1. **PMI-STEP-101** — Freeze and RED-test the legacy reducer, LOO-ECDF midrank reducer, tail registry, factorial family registry, N_eff definition, eps1 grid, and tie semantics.  
   Files: `tests/obsstat/test_finite_null_family.py`, `tests/contracts/test_planck_mes_irrep_preregistration.py`
2. **PMI-STEP-102** — Implement the central reducers and make observation_inclusive_max_scan delegate to the legacy specification without changing its serialized result.  
   Files: `htt/obsstat/finite_null_family.py`, `htt/obsstat/planck_post275_lane.py`
3. **PMI-STEP-103** — Execute the frozen 301-row map-free mechanism audit, including analytic round trips, the 2x2 square/mix factorial, legacy/ECDF and tail tables, tie mass, N_eff, eps1 curves, MC scale, and row-score null distributions.  
   Files: `scripts/observed_runs/run_planck_mes_coordinate_mechanism_audit.py`, `tests/integration/test_planck_mes_coordinate_mechanism_audit.py`, `docs/generated/planck_mes_coordinate_mechanism/**`
4. **PMI-STEP-104** — Generate mechanism, score-distribution, and eps1-sensitivity figures; inspect them and write a hash-bound plot_audit.json before terminal success.  
   Files: `docs/generated/planck_mes_coordinate_mechanism/**`

**Verification**
- targeted: `python -m pytest -q tests/obsstat/test_finite_null_family.py tests/contracts/test_planck_mes_irrep_preregistration.py tests/integration/test_planck_mes_coordinate_mechanism_audit.py`
- negative: `python -m pytest -q tests/obsstat/test_finite_null_family.py tests/contracts/test_planck_mes_irrep_preregistration.py tests/integration/test_planck_mes_coordinate_mechanism_audit.py -k 'tie or permutation or monotone or posthoc or eps1 or plot'`
- regression: `python -m pytest -q tests/integration/test_planck_mes_morphology.py tests/paper/test_planck_mes_first_paper.py`
- integration: `python scripts/observed_runs/run_planck_mes_coordinate_mechanism_audit.py --replay docs/generated/planck_mes_coordinate_mechanism`

**PASS →** Start PMI-WU-003; the required map-free objective transition has occurred, so further planning output is forbidden.

**FAIL →** On legacy-rank or identity failure emit BLOCKED_BY_P0; on ECDF/spec failure emit BLOCKED_BY_P1; preserve the legacy engine and stop.

### PMI-WU-003 — Verify the local Planck inventory read-only and quarantine malformed inputs

**Objective.** Reuse the predecessor intake semantics to verify exact local Planck inventories, quarantine partial products, admit row 00818 semantically, and preserve raw bytes.

**Observable success.** SUCCEEDED intake receipts confirm exact SMICA/Commander inventories, row-00818 FITS semantics and digest, absence of NPIPE/HSC payloads, route dispositions, and unchanged raw metadata.

**Preconditions**
- `python -c "import json; p=json.load(open('docs/generated/planck_mes_coordinate_mechanism/terminal.json')); assert p['state']=='SUCCEEDED'"` → PMI-WU-002 objective executed
- `test -d /mnt/sn850x2t/htt_base_e2e/workdir/raw` → raw root exists

**Load-bearing invariants**
- `PMI-INV-RAW-IMMUTABLE` (P0): Raw/download/package-data inputs are unchanged before and after intake.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_extended_data_inventory.py::test_raw_tree_is_read_only_and_unchanged`
- `PMI-INV-EXACT-INVENTORY` (P0): SMICA CMB has 999 official rows excluding only 00970, noise has 300 rows, Commander has exactly three complete and four quarantined partial files, and NPIPE/HSC are absent.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_extended_data_inventory.py::test_exact_planck_inventory_and_quarantine`
- `PMI-INV-00818-SEMANTIC` (P0): Row 00818 is admitted or blocked by FITS semantics and content digest, not size alone.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_extended_data_inventory.py::test_00818_requires_semantic_fits_receipt`

**Ordered implementation**
1. **PMI-STEP-201** — Write and run RED tests for exact inventories, quarantine, row 00818, root containment, byte classification, and immutability.  
   Files: `tests/integration/test_planck_mes_extended_data_inventory.py`
2. **PMI-STEP-202** — Implement and execute metadata/sidecar preflight, semantic FITS checks for selected inputs, pre/post raw metadata snapshots, and portable route receipts; stream-hash each selected file on its first scientific read.  
   Files: `scripts/observed_runs/inspect_planck_mes_extended_data.py`, `docs/generated/planck_mes_extended_data/**`

**Verification**
- targeted: `python -m pytest -q tests/integration/test_planck_mes_extended_data_inventory.py`
- negative: `python -m pytest -q tests/integration/test_planck_mes_extended_data_inventory.py -k 'partial or absent or 00818 or mutation or symlink'`
- regression: `python -m pytest -q tests/integration/test_planck_pr3_admission_preparation.py tests/integration/test_planck_pr3_current_stack.py`

**PASS →** Start PMI-WU-004 from the verified intake and recover the primary 301-row carrier.

**FAIL →** Emit one typed inventory BLOCKED state, preserve raw inputs, and stop without more governance.

### PMI-WU-004 — Recover the primary 301-row harmonic carrier and V2 portable replay

**Objective.** Modify the Planck operator/output boundary so the observed SMICA row and exact 300 paired CMB+noise rows preserve typed ell=2..5 harmonic carriers while the V1 scalar products remain unchanged.

**Observable success.** A V2 NPZ/metadata/replay stores observed (32,) and null (300,32) real carriers, typed block identities and scalar features; V2 reproduces V1 scalar bytes/ranks and carrier-derived features within registered tolerance.

**Preconditions**
- `python -c "import json; p=json.load(open('docs/generated/planck_mes_extended_data/intake_summary.json')); assert p['status']=='SUCCEEDED'"` → verified intake
- `python -m pytest -q tests/integration/test_planck_pr3_operator.py tests/integration/test_planck_pr3_current_stack.py` → existing operator path passes

**Load-bearing invariants**
- `PMI-INV-V1-IMMUTABLE` (P0): Existing V1 scalar packages, exact ranks, schemas, and filenames are unchanged; V2 is additive.  
  Check: `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py::test_v1_packages_and_exact_results_are_unchanged`
- `PMI-INV-CARRIER-CONVENTION` (P0): The 32 real coefficients use the registered ell/m/sign order, frame, mask, beam/pixel, source, and operator identities.  
  Check: `python -m pytest -q tests/integration/test_planck_irrep_carrier.py::test_carrier_round_trip_and_identity_binding`
- `PMI-INV-CARRIER-FEATURE-PARITY` (P0): Scalar features recomputed from each serialized carrier match the stored scalar row under exact or registered tolerance.  
  Check: `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py::test_carrier_reproduces_every_scalar_feature_row`
- `PMI-INV-NO-CARRIER-DROP` (P1): A successful primary map pass cannot serialize scalar features without the typed carrier.  
  Check: `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py::test_success_terminal_requires_carrier_and_scalar_projection`

**Ordered implementation**
1. **PMI-STEP-301** — Write and run RED tests for real-basis round trips, exact identities, V1 immutability, per-row carrier/feature parity, serialization determinism, and success-terminal completeness.  
   Files: `tests/integration/test_planck_irrep_carrier.py`, `tests/integration/test_planck_primary_irrep_v2.py`
2. **PMI-STEP-302** — Implement the V2 carrier writer/replay around ObservableIrrepState with deterministic NPZ arrays, canonical JSON, per-row content hashes, block offsets, and scalar projection.  
   Files: `htt/obsstat/planck_irrep_carrier.py`
3. **PMI-STEP-303** — Thread JointCutSkyFit.retained_coefficients through the existing observed/null run and write a separate V2 package beside the unchanged V1 package; execute the real paired-300 recovery.  
   Files: `htt/obsstat/planck_pr3_operator.py`, `scripts/observed_runs/run_planck_pr3.py`, `docs/generated/planck_mes_primary_irrep_v2/**`

**Verification**
- targeted: `python -m pytest -q tests/integration/test_planck_irrep_carrier.py tests/integration/test_planck_primary_irrep_v2.py`
- negative: `python -m pytest -q tests/integration/test_planck_irrep_carrier.py tests/integration/test_planck_primary_irrep_v2.py -k 'identity or layout or scalar or missing or overwrite or mutation'`
- regression: `python -m pytest -q tests/integration/test_planck_pr3_operator.py tests/integration/test_planck_pr3_current_stack.py tests/integration/test_planck_mes_morphology.py`
- integration: `python scripts/observed_runs/run_planck_pr3.py --replay-irrep-v2 docs/generated/planck_mes_primary_irrep_v2`

**PASS →** Start PMI-WU-005 and use the accepted carrier implementation for the 999 lane.

**FAIL →** On carrier convention, V1 mutation, or scalar parity failure emit BLOCKED_BY_P0 and preserve all outputs; do not tune tolerances or rerun under a new operator.

### PMI-WU-005 — Execute the carrier-preserving SMICA 999 CMB-only robustness lane

**Objective.** Execute the separate official 999 CMB-only SMICA lane with the same operator, typed harmonic carriers, legacy and preregistered reducer/tail outputs, and no primary replacement.

**Observable success.** A 1000-row V2 package/result/replay/terminal preserves exact official IDs, scalar/carrier parity, immutable primary authority, legacy and ECDF reducer outputs, registered-tail sensitivity, and inspected rank/00818 diagnostics.

**Preconditions**
- `python -c "import json; p=json.load(open('docs/generated/planck_mes_primary_irrep_v2/terminal.json')); assert p['state']=='SUCCEEDED'"` → primary carrier accepted
- `python -c "import json; p=json.load(open('docs/generated/planck_mes_extended_data/intake_summary.json')); assert p['status']=='SUCCEEDED'"` → exact inventory accepted

**Load-bearing invariants**
- `PMI-INV-SMICA-999-ORDER` (P0): IDs are 00000..00999 excluding only 00970, in ascending order, and include semantically admitted 00818.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py::test_exact_official_999_inventory_and_order`
- `PMI-INV-999-CARRIER` (P1): Every successful 1000-row output contains scalar rows and 32-component typed carriers with common operator identity.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py::test_success_requires_scalar_and_carrier_for_every_row`
- `PMI-INV-PRIMARY-SEPARATE` (P0): The 999 lane cannot overwrite or supersede the paired-300 primary and has a distinct schema/null identity.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py::test_primary_301_row_authority_is_immutable_and_separate`
- `PMI-INV-PLOT-INSPECTION` (P1): Family-rank, row-score, and 00818-influence figures are hash-bound to explicit inspection findings.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py::test_plot_audit_binds_all_required_figures`

**Ordered implementation**
1. **PMI-STEP-401** — Write and run RED tests for exact official inventory, primary separation, scalar/carrier parity, reducer/tail specs, deterministic replay, 00818 influence, claims, and plot inspection.  
   Files: `tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py`
2. **PMI-STEP-402** — Execute the 999 maps once through the accepted joint cut-sky operator, serialize both scalar and carrier V2 products, run legacy/ECDF and registered-tail families, replay, plot, and inspect.  
   Files: `scripts/observed_runs/run_planck_mes_smica_cmbonly_999.py`, `docs/generated/planck_mes_smica_cmbonly_999_irrep/**`

**Verification**
- targeted: `python -m pytest -q tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py`
- negative: `python -m pytest -q tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py -k 'missing or duplicate or primary or carrier or claim or 00818 or plot'`
- regression: `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py tests/integration/test_planck_mes_morphology.py tests/paper/test_planck_mes_first_paper.py`
- integration: `python scripts/observed_runs/run_planck_mes_smica_cmbonly_999.py --replay-irrep-v2 docs/generated/planck_mes_smica_cmbonly_999_irrep`

**PASS →** Start PMI-WU-006 using map-free carriers; do not reread all null maps for the injection study.

**FAIL →** On inventory/operator/primary-lock failure emit a typed BLOCKED state; preserve admitted files and do not tune to numerical agreement.

### PMI-WU-006 — Implement observable morphology/template scores and execute operator-aware injections

**Objective.** Build observable-only orbit projections and a leave-one-out covariance-whitened harmonic template score, then execute preregistered operator-aware analytic shear injections and a conditional native Bianchi VII_h lane.

**Observable success.** Replayed outputs provide observable morphology, exact rotation tests, complete-pool template ranks, analytic injection power with Wilson intervals/A50/A90 brackets/orientation spread, scalar-versus-harmonic power comparison, and explicit candidate dispositions; no physical inference is emitted.

**Preconditions**
- `python -c "import json; assert json.load(open('docs/generated/planck_mes_primary_irrep_v2/replay.json'))['status']=='MATCH'"` → primary carrier replay accepted
- `python -c "import json; assert json.load(open('docs/generated/planck_mes_smica_cmbonly_999_irrep/replay.json'))['status']=='MATCH'"` → robustness carrier replay accepted
- `python -c "import json; p=json.load(open('docs/generated/planck_mes_irrep_injections/candidate_dispositions.json')); assert p['ANALYTIC_AXISYMMETRIC_STF_L2_L3_V1']=='PROMOTED'"` → mandatory candidate executed

**Load-bearing invariants**
- `PMI-INV-OBSERVABLE-ONLY` (P0): Observable morphology and template scores consume ObservableIrrepState and cannot emit physical-state or Bianchi-family labels.  
  Check: `python -m pytest -q tests/obsstat/test_lowell_irrep_morphology.py::test_observable_report_forbids_physical_and_family_claims`
- `PMI-INV-AXIS-SIGN` (P0): Unoriented multipole-axis sign flips leave allowed morphology unchanged and cannot produce handedness claims.  
  Check: `python -m pytest -q tests/obsstat/test_lowell_irrep_morphology.py::test_axis_sign_flips_leave_allowed_invariants_unchanged_and_forbid_signed_claims`
- `PMI-INV-LOO-TEMPLATE-SCORE` (P0): Every row uses leave-one-out mean/covariance, full-rank fail-closed whitening, and identical 384-rotation maximization.  
  Check: `python -m pytest -q tests/obsstat/test_harmonic_template_score.py::test_leave_one_out_whitening_and_orientation_max_are_permutation_equivariant`
- `PMI-INV-OPERATOR-AWARE-INJECTION` (P0): Each rotated template is passed through the exact source transfer and joint cut-sky operator before carrier addition.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_every_template_orientation_has_content_bound_operator_response`
- `PMI-INV-CANDIDATE-COVERAGE` (P1): Analytic and native template candidates have explicit terminal dispositions.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_candidate_disposition_ledger_is_complete`
- `PMI-INV-PLOT-INSPECTION` (P1): Every required power, response, and residual figure is hash-bound to a human/agent inspection record.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_irrep_injections.py::test_plot_audit_binds_all_required_figures_and_findings`

**Ordered implementation**
1. **PMI-STEP-501** — Freeze analytic template bytes/formula, orientation grids, dimensionless full-sky-RMS amplitude grid, score, covariance rule, rejection rule, candidate vocabulary, and expected output schemas; write and run RED tests.  
   Files: `docs/research_program/post_pr275/planck_irrep_template_registry.yaml`, `tests/obsstat/test_lowell_irrep_morphology.py`, `tests/obsstat/test_harmonic_template_score.py`, `tests/integration/test_planck_mes_irrep_injections.py`
2. **PMI-STEP-502** — Implement observable-only amplitude/shape and axis-sign-invariant projections from ObservableIrrepState; expose no physical-state constructors or family labels.  
   Files: `htt/obsstat/lowell_irrep_morphology.py`
3. **PMI-STEP-503** — Implement real-basis rotation matrices, orthogonality/composition checks, leave-one-out full covariance whitening, orientation-max score, and exact finite-null calibration.  
   Files: `htt/obsstat/harmonic_template_score.py`
4. **PMI-STEP-504** — Precompute the operator-effective analytic template bank for all 384 rotations, inject the exact dimensionless full-sky-RMS amplitude grid into the accepted carriers over 96 evaluation orientations, execute the score/power study, and run the native lane only if authority admission passes.  
   Files: `scripts/observed_runs/run_planck_mes_irrep_injections.py`, `docs/generated/planck_mes_irrep_injections/**`
5. **PMI-STEP-505** — Generate null-score, operator-response, power, orientation-spread, scalar-versus-harmonic, and residual figures; inspect adversarially and write plot_audit.json before terminal success.  
   Files: `docs/generated/planck_mes_irrep_injections/**`

**Verification**
- targeted: `python -m pytest -q tests/obsstat/test_lowell_irrep_morphology.py tests/obsstat/test_harmonic_template_score.py tests/integration/test_planck_mes_irrep_injections.py`
- negative: `python -m pytest -q tests/obsstat/test_lowell_irrep_morphology.py tests/obsstat/test_harmonic_template_score.py tests/integration/test_planck_mes_irrep_injections.py -k 'sign or physical or singular or covariance or orientation or posthoc or authority or candidate or plot'`
- regression: `python -m pytest -q tests/integration/test_planck_primary_irrep_v2.py tests/integration/test_planck_mes_smica_cmbonly_999_irrep.py tests/integration/test_planck_mes_coordinate_mechanism_audit.py`
- integration: `python scripts/observed_runs/run_planck_mes_irrep_injections.py --replay docs/generated/planck_mes_irrep_injections`

**PASS →** Start PMI-WU-007 with only successful replayed projections; a deferred native template is an allowed nonblocking disposition.

**FAIL →** On score equivariance, operator-response, or preregistration failure emit BLOCKED_BY_P0; on missing native authority mark only that candidate DEFERRED and continue the analytic lane.

### PMI-WU-007 — Execute Commander descriptive carrier comparison and reframe the methods paper

**Objective.** Process Commander through the same observable-irrep operator without finite calibration, then rebuild the paper around coordinate sensitivity, carrier preservation, and validated injection power with clean provenance.

**Observable success.** Commander result/replay/terminal emits typed carriers and feature deltas with finite_rank_emitted=false; the rebuilt manuscript states analytic identities, method non-invariance, null fidelity, eps1 sensitivity, prior constraints, reproducibility specs, and only successful injection/robustness findings.

**Preconditions**
- `python -c "import json; assert json.load(open('docs/generated/planck_mes_irrep_injections/terminal.json'))['state']=='SUCCEEDED'"` → mandatory analytic injection lane succeeded
- `python -c "import json; assert json.load(open('docs/generated/planck_mes_coordinate_mechanism/replay.json'))['status']=='MATCH'"` → mechanism result replay accepted

**Load-bearing invariants**
- `PMI-INV-COMMANDER-NO-RANK` (P0): Commander remains observation-only with finite_rank_emitted=false and partial simulations never enter a null pool.  
  Check: `python -m pytest -q tests/integration/test_planck_mes_commander_irrep.py::test_commander_cannot_emit_finite_rank_or_open_partial_inputs`
- `PMI-INV-PAPER-EVIDENCE` (P1): The manuscript consumes only successful terminal+replay projections and states each result at its exact claim level.  
  Check: `python -m pytest -q tests/paper/test_planck_mes_irrep_methods_paper.py::test_paper_requires_successful_replayed_evidence_and_claim_boundaries`
- `PMI-INV-PAPER-F1-F4` (P1): The manuscript includes the analytic identities/information equivalence, reducer non-invariance, existing-constraint comparison, eps1 sensitivity, null fidelity, and full physical operator specs.  
  Check: `python -m pytest -q tests/paper/test_planck_mes_irrep_methods_paper.py::test_referee_load_bearing_revisions_are_present`
- `PMI-INV-PDF-INSPECTION` (P1): The rebuilt PDF and all revised figures are inspected for semantic consistency, clipping, and legibility.  
  Check: `python -m pytest -q tests/paper/test_planck_mes_irrep_methods_paper.py::test_pdf_and_figure_audit_is_bound_to_source_and_artifacts`

**Ordered implementation**
1. **PMI-STEP-601** — Write RED tests, execute Commander observation plus three complete sanity rows through the same operator, serialize carriers/features/deltas, refuse partial files before FITS open, and emit no finite rank.  
   Files: `tests/integration/test_planck_mes_commander_irrep.py`, `scripts/observed_runs/run_planck_mes_commander_observation.py`, `docs/generated/planck_mes_commander_observation_irrep/**`
2. **PMI-STEP-602** — Write RED paper tests and reframe the paper as a methods result; include F1/F2 identities and factorial/ECDF results, F4 comparison, eps1 sensitivity, registered tails, null fidelity/leakage/reproducibility specs, Neff/tie/MC diagnostics, octupole direction, injection power, and bounded robustness/Commander appendices.  
   Files: `tests/paper/test_planck_mes_irrep_methods_paper.py`, `scripts/paper/build_planck_mes_first_paper.py`, `papers/planck_mes_first_observation/main.tex`, `papers/planck_mes_first_observation/references.bib`, `docs/generated/planck_mes_first_paper/**`
3. **PMI-STEP-603** — Build the PDF, inspect all pages and figures, bind clean commit/tree/generator/input identities, and write the final audit receipt.  
   Files: `papers/planck_mes_first_observation/main.tex`, `docs/generated/planck_mes_first_paper/**`

**Verification**
- targeted: `python -m pytest -q tests/integration/test_planck_mes_commander_irrep.py tests/paper/test_planck_mes_irrep_methods_paper.py`
- negative: `python -m pytest -q tests/integration/test_planck_mes_commander_irrep.py tests/paper/test_planck_mes_irrep_methods_paper.py -k 'partial or rank or physical or unexecuted or replay or claim or pdf or figure'`
- regression: `python -m pytest -q tests/paper/test_planck_mes_first_paper.py tests/integration/test_planck_mes_morphology.py tests/integration/test_planck_mes_coordinate_mechanism_audit.py tests/integration/test_planck_mes_irrep_injections.py`
- integration: `latexmk -pdf -interaction=nonstopmode -halt-on-error papers/planck_mes_first_observation/main.tex`

**PASS →** Transition to external scientific review or submission preparation; do not start another internal audit loop.

**FAIL →** If Commander attempts calibration or the paper consumes unexecuted/overclaimed evidence, emit BLOCKED_BY_P0/P1 and apply one bounded repair only.


## E. Fresh-Context Review Contract

The first review pass is read-only. It receives only the accepted base/final SHAs, the current work-unit contract, the diff, verification logs, objective artifacts, plot audit when applicable, candidate dispositions, and unresolved blockers. It reports findings using the schema in `FRESH_CONTEXT_REVIEW_CONTRACT.yaml`. PASS requires `P0=0` and `P1=0`; a further review loop is forbidden absent a newly reproduced current-task P0/P1.

## F. Final Differential Audit Contract

The final strong review examines only `base..final`, the compiled contract, evidence bundle, fresh-review findings, repair delta, and unresolved blockers. It asks whether the delta violated the contract, exposed a new P0/P1 class, misclassified byte identity, claimed unexecuted work, or expanded scope. It does not restart the historical project audit.

## G. Unresolved Specification Boundaries

No unresolved boundary blocks `PMI-WU-001` through the mandatory analytic observable-STF injection lane.

The following are explicitly conditional rather than guessed:

- `NATIVE_BIANCHI_VIIH_CONTENT_BOUND_V1`: run only when exact template bytes, solver commit/tree, conventions, transfer provenance, and operator response identity are admitted; otherwise record `DEFERRED_MISSING_TEMPLATE_AUTHORITY`.
- journal/author metadata and repository DOI: submission metadata only; they do not block numerical execution.
- physical interpretation of an observable irrep: unavailable until a channel-matched content-bound response operator exists.

## H. Process-Cost Assessment

Reuse the existing Planck operator, scalar packages, MES anchor authority, PR-326 bridge, and physical state/orbit modules. Do not rehash unrelated raw data, run the whole suite by default, reread all maps during injection, add another planning package, or create review-of-review layers. The first objective result must appear in `PMI-WU-002`; the first large-data pass must emit the harmonic carrier. Two process-only cycles trigger `PROCESS_STARVATION` and force the next declared executable transition.

## Completion States

Use exactly:

```text
PASS
PASS_WITH_NONBLOCKING_FINDINGS
BLOCKED_BY_UNRESOLVED_SPEC
BLOCKED_BY_P0
BLOCKED_BY_P1
PARTIAL
FAILED
```

A plan, scaffold, RED test alone, or unexecuted runner is never `PASS`.
