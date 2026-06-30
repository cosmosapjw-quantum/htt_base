# REV-R138 - Root progress + Planck-raw-analysis-plan report

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_observed_and_external_transfer_conditional
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Summarise research progress to date and describe the Planck raw-data analysis plan in
detail; write it in LaTeX, compile to PDF, and provide it at repo root.

## Deliverable

`htt_progress_and_planck_plan.{tex,pdf}` at repo root (6 pp). Self-contained: text +
tables only, no `\includegraphics`, so the build is clean and there is no
missing-figure risk. Built via the htt-latex-paper-build skill workflow.

Sections:
- Framework + graded comparator g=(Sigma^2, W^2, Omega_tilt, Omega_k), PSD-cone rep.
- Theorem ledger (14 proven: 6 symbolic + 8 gate; 3 data), incl. the W^2 (structural,
  order-independent) vs Omega_k (leading-order no-channel) null-precision refinement.
- Real-data status: K5 |B|=341+/-102 km/s with conditional CV coverage (0.67 vs 0.19),
  K6 WF curl-suppression no-go (vorticity <=0.55% of shear), K1 look-elsewhere global p
  = 0.097 (SMICA) / 0.121 (Commander) under a LambdaCDM null, PR08-006 rank-2 = one
  measured (Omega_tilt) + one partial (Sigma^2) + two fail-closed.
- External-audit revision summary (rev-r135).
- Planck-raw analysis plan: blocker, FFP10 SMICA acquisition (1000 CMB + 300 noise,
  ~1 TB), pipeline, the three implemented runner modes (route-4 / full Route-A / v2
  precision), the v2 precision set (NSIDE=64 ell<=8 ceiling + pixel-window table,
  ell_max=30, mask+inpaint), measured wall-time + RAM budget, exit gate + kill switches,
  native-solver ell=2-30 co-evolution.
- Claim envelope + reproducibility appendix.

## Claim discipline

Diagnostic-only throughout; no family-ID/geometry/native-validation/detection/MIO-as-odds.
The only "family identification" mentions are the explicit boundary-negation sentences.

## Validation

| Check | Status |
| --- | --- |
| `latexmk` | exit 0; 6 pages |
| undefined references / citations | 0 (authoritative latexmk log) |
| missing figures | none (no `\includegraphics`) |
| overfull boxes | max 17 pt (one justified prose line; cosmetic) |
| forbidden claim-phrase scan | clean (negation sentences only) |
