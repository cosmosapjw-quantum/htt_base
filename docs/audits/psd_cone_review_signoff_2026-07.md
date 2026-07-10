# PSD-cone comparator redesign — independent review record (2026-07-10)

Ticket: `EGS3-redesign-psd-cone` (`docs/research_program/egs3/tickets/psd_cone_redesign.yaml`,
rev-r125, `state: implemented_behind_review`). Review gate: independent reviewer
sign-off before the representation may front the production diagnostic; the
standing guard is the bit-identical `x_C` regression.

Two independent reviewers were run in the v8-update cycle (REV-R161), each
hostile-prompted, read-only, with test execution.

## Reviewer 1 — claim-discipline (claim-gate-reviewer)

**Verdict: SIGN_OFF.** No P0/P1 findings. Verified: claim tier is
representation/diagnostic-only in module, ticket, experiment runner and results
table; no statement upgrades the redesign into a physical/observational/
detection/geometry claim; the bit-identity contract is enforced by exact
`np.array_equal`/`==` (20/20 gate+contract tests pass; Wolfram seal PASS); the
"cone-shell excludes the FLRW vertex" statement is a mathematical property of
the representation (a strictly positive shear-eigenvalue lower bound excludes
`lambda_Sigma = 0`), with the conditional lower-bound provenance delegated to
`egs2_shear_bracket` ("No detection"); no production diagnostic imports the
module, so the redesign genuinely stays behind the graded upgrade. Three P2
wording notes recorded (non-blocking): "measured comparator" comment wording,
results-table row qualifier, and the (correct) absence of a dedicated
CLAIM_LEDGER row.

## Reviewer 2 — mathematics/statistics (physics-stat-auditor)

**Initial verdict: FINDINGS (revise-and-resubmit).** The representation core
and the ship-gate were verified sound (trace identity bit-exact over 200k
adversarial draws; diagonal-PSD block equivalence; shell convexity; rank-2
reachable/null structure; fail-closed diagonal-scope guards). Four findings:

1. **P1 (units defect, genuine):** `bracket_shell_from_a2a3` returned bounds on
   the LINEAR shear `Sigma` while `cone_shell_membership` compares the
   second-moment eigenvalue `lambda_Sigma = M[0,0] = Sigma^2` — a units
   mismatch producing wrong shell membership over a discriminating range and
   flowing into `fig_egs3_psd_cone` and the `axis_psd` rows of
   `egs3_experiments.json`. The P4 gate masked it with a non-discriminating
   probe point.
2. **P2:** headline "PSD matrix comparator M >= 0" contradicted by the admitted
   signed `Omega_k < 0` case (code correct, framing overstated).
3. **P2:** the Wolfram seal proved convexity of the 4-D nonnegative orthant
   under an `ok >= 0` assumption the code does not impose, and its signature
   string overstated "admissible set = PSD cone".
4. **P2:** `eigen_identifiability` dropped the null-KIND distinction
   (`W2` = order-independent structural null vs `Omega_k` = leading-order
   no-channel that re-opens beyond leading order).

## Repairs applied in-session (REV-R161)

- `htt/obsstat/egs3_psd_cone.py`: bracket mapped through the (monotone,
  nonnegative-domain) square — `(max(shear_lower,0))^2, shear_upper^2` — with a
  units-repair docstring; module headline reworded to "PSD on the three genuine
  second-moment sectors ... global M >= 0 is NOT asserted";
  `EigenIdentifiability.null_sector_kinds` propagates
  `egs3_graded_comparator.NULL_SECTOR_KIND`; `xc_from_matrix` docstring states
  the exact-float reason for bit-identity (C = diag(+-1)).
- `research_gates/egs3/tests/test_egs3_axis_psd.py`: new `P7ReviewRepairTests`
  — bracket-is-the-square pin, a DISCRIMINATING eigenvalue strictly between the
  squared and linear lower bounds asserted in-shell (the pre-repair bracket
  ejected it), and the null-kind pins.
- `wolfram/egs3_psd_cone.wls` (schema v2): `Omega_k` left free everywhere;
  cone/convexity proved on the 3-sector moment block; signed-line closure
  recorded; new `linear_to_eigenvalue_bracket_square_exact` (`Resolve ForAll`);
  signature string corrected. Regenerated
  `docs/generated/egs3_psd_cone_proof.json` = PASS, all checks true.
- `fig_egs3_psd_cone` regenerated (sidecars `--check` current): `Sigma^2`-unit
  log-axis shell; `W2` (red, structural null) visually distinguished from
  `Omega_k` (orange, leading-order no-channel); "moment block >= 0" title.

**Deliberate non-action (freeze):** `docs/generated/egs3_experiments.json` is
v7-byte-frozen (its SHA is embedded in the frozen v7 report MANIFEST), so its
`axis_psd` rows still carry the pre-repair linear-bracket shell numbers. This
is a documented frozen-artifact defect; the successor
`egs3_experiments_v8.json` (this cycle) carries the corrected values.

## Disposition

- The claim-discipline reviewer signed off outright; the mathematical reviewer's
  findings were repaired in-session and re-verified (final verification verdict
  recorded in `docs/generated/psd_cone_review_signoff.json`).
- Per the claim reviewer's scope note, this record does NOT authorize fronting
  the production diagnostic: the ticket's `review_gate` is discharged to
  `reviewed_fixes_applied_behind_graded` — sign-off recorded, representation
  remains behind the additive graded upgrade, and any future fronting decision
  keeps the bit-identical `x_C` regression as the standing guard.
