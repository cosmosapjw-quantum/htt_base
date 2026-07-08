# REV-R146 - External re-review response: v6 audit report + identified-set/seal program

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none (symbolic seals + synthetic statistics witnesses; no downloads, no raw data)
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Respond to the external re-review of the v5 external-audit report (B1/B2 blockers +
M1'-M6' + minors + numerical-experiment and new-theorem candidates) while the K1 E2E
download runs. All work is CPU-local.

## Findings addressed

- **B1 (W^2 convention, BLOCKER)** -- document-only defect. The code was ALREADY on the
  registered convention (`comparator_policy.py:337` `Wstd_sq = omega_sq/(6H^2)`;
  `bounds.py` / `three_bound_hierarchy.py` `W2_max = (3/2) B_omega^2`); the v5 report's
  `omega_a omega^a/H^2` statement was exactly 3x the registered value. v6 registers
  `W^2 := omega_ab omega^ab/(6H^2) (= omega_a omega^a/(3H^2))`, DISPLAYS the parent
  constraint identity `1 = Om + OL + Ok + Otilt + Sigma^2 - W^2`, derives c=(1,-1,1,1)
  symbolically (tilted frame included) and the (3/2) MES conversion rule in a fail-closed
  SymPy seal. **Zero edits to existing htt/ modules; all bit-identical x_C anchors and
  frozen artifacts untouched (guarded by gate E7).**
- **B2** -- P26-P32 full statement-and-proof bodies written into the v6 body
  (3.4/4/5.2/7/8.2/8.4); ledger gains a Body-section column.
- **M1'** -- two-stage tau (spec test alpha1 on m-r residual dof; conditional
  chi^2_r ellipsoid alpha2) + new **P35** coverage theorem + Imbens-Manski endpoint
  correction (undercoverage of the naive endpoint CI demonstrated by MC).
- **M2'** -- empty-set (refutability, size alpha1 / power curve) + unbounded (no-result)
  branches; new algorithm **A8**.
- **M3'** -- new **P36** joint-feasible-set G_F interval (joint subset of naive quotient,
  width ratio 0.58 on the registered toy); P33 domain-restricted to point-identified.
- **M4'** -- section-10 rows carry N/seed/SE/multi-threshold Markov checks; new E1-E8
  witness table rendered fail-closed from deterministic repo artifacts with sha256 prefixes.
- **M5'** -- Omega_tilt=(1+w)Omega_m sinh^2(beta), Omega_k=-R3/(6H^2) closed forms +
  FLAT/MATCHED/NULL reference policy registered; Hartlap/Sellentin-Heavens requirement
  registered in the K1 lane.
- **M6'** -- F>1 -> ceiling-unfit clip (3.3 + A2 + A8).
- **Minors** -- Fourth Revision title/abstract; [x_C]_+ vs sup-endpoint notation split;
  posterior wording ("HTT-owned; this report makes none"); P13 + P26 -> DERIVED_CONDITIONAL;
  P15 response coefficient renamed lambda_2; P8 column- vs row-duplication split (P30);
  registry-stable-numbering note; external literature-context subsection (registered
  exception; context, not evidence).

## New code (additive; no existing htt/ module edited)

- `htt/obsstat/egs3_identified_set.py` -- two-stage tau, A8 status report
  (feasible/empty/unbounded/ceiling_unfit), SLSQP + closed-form cross-checked endpoints,
  Imbens-Manski machinery, IM-coverage + refutability-power experiments.
- `htt/obsstat/egs3_gf_interval.py` (P36), `htt/obsstat/egs3_evalue_merge.py` (P29 +
  Ville), `htt/obsstat/egs3_prior_exposure.py` (P28 KL=0 witness),
  `htt/obsstat/egs3_parent_identity.py` (B1 SymPy seal),
  `htt/obsstat/egs3_bianchi_v_constraint.py` (P5 constraint-algebra seal; the
  Hewitt-Wainwright evolution check stays a registered stretch item),
  `htt/obsstat/egs3_shear_memory_bias.py` (P13 kappa-bias curve, zero at e0=1).
- `scripts/run_egs3_symbolic_seals.py` + `make egs3-seals` ->
  `docs/generated/{parent_identity_seal,bianchi_v_constraint_seal}.json` (--check; fail-closed).
- Gates: `research_gates/egs3/tests/test_egs3_axis_e_identified_set.py` (E1-E7 incl.
  CoVe + x_C bit-identity guard) + `test_egs3_axis_f_physics_seals.py` (F1-F4);
  `make egs3-gates` 61 -> 109.
- `scripts/run_egs3_experiments.py` += axis_e/axis_f (axis a-d blocks value-identical);
  results table += EGS3-E1..E4 + F1..F3 (25 -> 32 rows); 3 new theorem figures
  (`fig_egs3_e_im_coverage`, `fig_egs3_e_refutability_power`,
  `fig_egs3_f_shear_memory_bias`) + contract STEMS extended.
- `scripts/build_external_audit_report_v6.py` -> `external_audit_research_report_20260708_v6/`
  (26 pp; Fourth Revision; P35/P36 + A8 + audit-grade section 10; deterministic
  GENERATED_AT; --check; REQUIRED_ARTIFACTS fail-closed) + root PDF. Frozen v5 package
  untouched.
- `docs/research_program/egs3/CLAIM_LEDGER.yaml` += 8 entries.

## Claim discipline

Diagnostic-only. All new results are symbolic seals or synthetic statistics witnesses --
no data claim, no detection, no family/geometry/native-solver/posterior claim. The
Bianchi V seal is constraint algebra under the stated LRS/small-tilt conditions (the
family label is the CONDITION of a legacy-recovery statement). Sigma^2 stays partial;
fail-closed sectors stay fail-closed; BLOCKERS.md unchanged (no blocker state changed).
B1 is a document-only repair: x_C bit-identical, no artifact drift.

## Validation

| Check | Status |
| --- | --- |
| `make egs3-seals` + `--check` | both seals PASS; artifacts current |
| `make egs3-gates` | 109 tests OK (was 61) |
| `run_egs3_experiments.py` (axis a-d value-identical) | wrote egs3_experiments.json (+142 lines, additive) |
| `build_egs_results_table.py` + `--check` | 32 rows; current |
| `make_egs2_egs3_theorem_figures.py` + `--check` | 14 figures; sidecars current; 3 new PNGs visually inspected |
| `build_external_audit_report_v6.py` + `--check` | 26-page PDF, 0 undefined refs; text artifacts current |
| `check_claim_language.py external_audit_research_report_20260708_v6` | clean |
| `claim_lint_research_surfaces.py` | 0 hits |
| `pytest tests/contracts` | pass (pre-existing structural failures untouched) |
| audit packages rebuilt + `--check` | current |
