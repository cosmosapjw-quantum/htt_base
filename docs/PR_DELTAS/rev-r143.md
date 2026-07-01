# REV-R143 - Root progress+plan report refreshed to the upgraded code

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Update the previous (vulnerable, pre-Axis-C/D) root research-plan file to the upgraded code and
regenerate the PDF at repo root, replacing the previous version.

## Change

Rewrote `htt_progress_and_planck_plan.{tex,pdf}` (was rev-r138) to match rev-r141 (Axis C) +
rev-r142 (Axis D):

- **NEW §3 Axis C** - the "Leaky Universe" boost->shear vulnerability and the closed-form fix
  `Sigma_tilde^2 = Sigma^2 - alpha (Omega_tilt)^2` (alpha = (4/9) T0^2 N2 / (kappa_T^2 R_sigma)),
  gate-verified (EGS3-C1..C4) + Wolfram-verified; coupled Fisher, identifiability, injection-recovery FPR.
- **NEW §4 Axis D** - the BASS-Extended joint PV+CMB analysis: feasible Woodbury PV covariance
  (real CF4 |B|=341 km/s), JWST distance-anchor acquisition + CF4 cross-match (labelled forecast),
  coupled-Fisher degeneracy break, real SMICA/Commander BipoSH SI measurement (p=0.68/0.65, GRF null),
  and the fail-closed theory-g C_{lm,l'm'}(g) sector.
- Ledger table 14+3 -> 25 rows (19 proven: 6 symbolic + 13 gate); `make egs3-gates` now 61.
- Real-data status += the D3 BipoSH channel + the Woodbury PV; Planck-raw plan notes the shared
  GRF-now / FFP10-pending E2E null; claim envelope + reproducibility commands refreshed.

## Claim discipline

Diagnostic-only. Sigma^2 stays partial; theory-g CMB fail-closed (never fabricated); JWST prior is a
labelled forecast; SMICA BipoSH is a real measurement consistent with isotropy. No family/geometry/
native-solver/posterior claim. Firewall-clean (only negations / fail-closed language).

## Validation

| Check | Status |
| --- | --- |
| `latexmk` | exit 0; 8 pages |
| undefined references | 0 (2-pass, longtable) |
| overfull boxes | none > 25 pt |
| claim-firewall scan | clean |
