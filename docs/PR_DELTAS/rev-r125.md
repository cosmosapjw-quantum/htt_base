# REV-R125 - EGS3 revisionary redesign: PSD-cone sector comparator (realized + gated)

owner: COMMON
implementation_scope: common
claim_tier: program_theorem_and_synthetic_mechanics
transfer_source: none
generating_command: `make egs3-gates egs3-wolfram egs3-experiments` + contracts
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Continue the remaining EGS3 PRs. The only fully-actionable one (no external-data
blocker, no native solver) is the registered revisionary redesign
`tickets/psd_cone_redesign.yaml`: promote the diagnostic layer from the scalar /
graded-vector comparator to a PSD-cone-valued comparator. The data tickets (K1
FFP10/NPIPE, K5/K6, PR08-*) stay blocked on external FITS ensembles + ownership
and keep their registered blocker codes; PR10 is a separate project.

## Changes

- `htt/obsstat/egs3_psd_cone.py` (new): the PSD-matrix comparator
  `M = diag(g) >= 0` whose labelled spectrum is the four sectors, signature
  `C = diag(+1,-1,+1,+1)`.
  * `xc_from_matrix` = `tr(C M)` -- **bit-identical** to the graded `<c,g>`;
  * `admissibility` -- PSD-cone membership, fail-closed on a negative labelled
    invariant; `convex_combination_is_admissible` witnesses the cone is convex;
  * `eigen_identifiability` -- measurement map `M -> P_R M P_R` keeps
    `{Sigma2, Omega_tilt}` (rank 2) and annihilates the blind sector
    `{W2, Omega_k}` exactly (null residual 0) -- A1 + NT2-B3 as one statement;
  * `cone_shell_membership` / `bracket_shell_from_a2a3` -- NT2-B1 as convex
    cone-shell membership `{M>=0 : s_lo < lambda_Sigma < s_hi}`, `s_lo>0`
    excludes the shear-free FLRW vertex.
- `research_gates/egs3/tests/test_egs3_axis_psd.py` (new): P1 trace identity +
  signature + spectrum; P2 convex cone + fail-closed; P3 reachable
  eigendirections / structural null; P4 convex cone-shell bracket (8 gates,
  auto-discovered by `make egs3-gates`).
- `tests/contracts/test_psd_cone_redesign.py` (new): bit-identical `x_C=tr(C M)`
  across cancellation / vertex / extreme inputs; PSD-admissible for all
  nonnegative sector vectors; redesign introduces no new scalar.
- `wolfram/egs3_psd_cone.wls` (new) + `make egs3-wolfram` second invocation ->
  `docs/generated/egs3_psd_cone_proof.json` (PASS): closed-form trace identity,
  spectrum=sectors, positive homogeneity, convex cone, convex shell
  (`Resolve[ForAll...]`), positive-lower-bound vertex exclusion.
- `scripts/run_egs3_experiments.py`: `axis_psd()` block + `revisionary_redesign`
  field -> `docs/generated/egs3_experiments.json`.
- `docs/research_program/egs3/tickets/psd_cone_redesign.yaml`: state
  `planned -> implemented_behind_review` + `realized_by` / `review_gate`.
- `docs/research_program/egs3/FRAMEWORK_CRITIQUE_AND_REDESIGN.md`: redesign
  section rewritten as realized + gated.
- `docs/final_report/main.tex` §8: PSD-cone paragraph upgraded to "implemented
  and gated (representation only)".
- `scripts/build_pr04_research_audit_package.py` + `build_final_report_audit_package.py`:
  +module, +`egs3_psd_cone.wls`, +`egs3_psd_cone_proof.json`; deltas r108..r125.

## Claim discipline

Representation change only. `x_C` is bit-identical (the gating regression); the
redesign ships **behind** the graded upgrade and does NOT front the production
diagnostic until independently reviewed. The strong content is structural -- a
convex admissible cone, a rank-2 reachable spectrum with an exact structural
null, and a convex bracket-shell excluding the FLRW vertex -- none of which
asserts a detection, family/geometry, or native-solver result. Off-diagonal
(cross-sector) PSD structure is reserved for the native solver and not used.

## Validation

| Command | Status |
| --- | --- |
| `make egs3-gates` | PASS (was 12 -> now 20 gates) |
| `make egs3-wolfram` (PSD core) | PASS (trace identity + convex cone + convex shell) |
| `make egs3-experiments` | wrote egs3_experiments.json (axis_psd bit_identical=true) |
| contracts (egs3 + graded + psd + 2 packages) | passed |
| `make pr04-gates pr07-gates egs2-gates forbidden-deps` | green |
| `pytest tests/obsstat` | passed |
| `latexmk -pdf main.tex` + `pdf_claim_lint.py` | PASS; 0 failed |
| both audit packages + `--check` | byte-deterministic |
