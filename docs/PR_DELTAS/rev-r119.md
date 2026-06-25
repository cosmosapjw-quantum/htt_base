# REV-R119 - PR-A: EGS2 audit MINOR-REVISIONS fixes (NT-A3 label + consistency)

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
generating_command: `prove_egs_lowell_theorems.py + make_egs_lowell_theorem_figures.py + latexmk`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Apply the 2026-06-25 EGS2 final-results audit (verdict **MINOR REVISIONS**,
near-PASS). Lead finding: the NT-A3 theorem registry + Fig. 2 mislabel a
single-estimator sampling dispersion as a "cosmic-variance Cramer-Rao floor"
("irreducible", "unmeasurable below 63%"), contradicting the report's own
Theorem 2 text. Plus three minor cross-document consistency items.

## Changes

- `scripts/prove_egs_lowell_theorems.py` (NT-A3): title
  "Cosmic-variance Cramer-Rao floor on F_shear" -> "Single-sky sampling
  dispersion of the standard F_shear estimator"; claim rewritten to "the
  standard full-sky estimator has ~63% fractional sampling dispersion at the
  quadrupole; this is the dispersion of that one estimator, NOT a Cramer-Rao
  bound or a universal floor over all estimators" (points to NT2-A1 for the
  genuine floor); step keys `fractional_floor*` -> `fractional_sampling_dispersion*`.
  The Wolfram math (`sqrt(2/(2l+1))`) is unchanged and re-verified (QED=True).
- `scripts/make_egs_lowell_theorem_figures.py` (NT-A3 / Fig. 2): title, y-label,
  source keys, and sidecar title relabelled to "single-sky sampling dispersion
  (one estimator); not a universal floor". Figure filename kept.
- Regenerated `docs/generated/egs_lowell_theorem_proofs.{json,md}` and the
  three theorem figures (png + source.json + manifest.json).
- `docs/final_report/main.tex`:
  - §2: state `x_max=9.25e-6` is the combined shear+tilt+curvature ceiling for
    the full comparator, distinct from / larger than the VER06 shear-only bound
    `Sigma^2_std < 6.4e-6`.
  - §5.3: K5 ~345 km/s is not in tension with K4 ~590 km/s --- different
    estimands (K4 volume-averaged reconstruction velocity vs K5 GLS bulk flow
    from group peculiar velocities); add the contested-bulk-flow-literature note
    (consistency is to the WF/CR reconstruction line, not a settled value).

## Claim discipline

Label-only correction (the math is unchanged); no result strengthened. The
genuine multi-multipole Fisher-CR floor is supplied separately by NT2-A1
(EGS2 extension). Forbidden-token claim lint passes (0 failed).

## Validation

| Command | Status |
| --- | --- |
| `prove_egs_lowell_theorems.py` | NT-A1/A3/B3 QED=True; registry regenerated |
| `make_egs_lowell_theorem_figures.py` | 3 figures + sidecars regenerated |
| registry scan for "Cramer/irreducible/unmeasurable" | only the negation remains |
| `latexmk -pdf main.tex` | PASS; 16 pages |
| `pdf_claim_lint.py` | Failed 0 |
