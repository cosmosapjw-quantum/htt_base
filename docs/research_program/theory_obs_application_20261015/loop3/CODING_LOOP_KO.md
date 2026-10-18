# HTT next coding research loop C1-C10: source-bound results

2026-10-15 KST, same source HEAD
13d8d85fa470d645d008986e8f77d8d0f70fdf54,
branch obs/solver-free-dossier-20261014.

## C1–C4: Targets, inputs and algorithms

Goal A: fixed mask K=P_low Y_6:12 left-singular directions.
Three lowrank candidate k=1..3, three ridge multipliers
0.25,1,4, CV on train60 only. Real Planck observed sky and
heldout240 same CMB+noise paired sky IDs are invisible
to training selection. Two mask choices remain two correlated
columns of one simulation row.

Goal B: preserve exact CF4 PR179 5-fold H_ONLY q-withheld status,
quantify the registered nuisance hierarchy and prove/measure
the radial algebra envelope on its same selected source cohort.
Raw source is /mnt/extdrive/workdir/raw/cf4_full.
Use raw source hash and frozen PR179 IDs, no upstream mutation.

## C5: Actual implementation

- htt/obsstat/geometric_lowrank_control.py:
  left singular geometry, rank-constrained control, 5-fold
  training-only selection, finite-null compatible scoring,
  same-row two-mask global rank.
- scripts/run_htt_geometric_lowrank_20261015.py:
  actual K from NSIDE64 masked source harmonic geometry,
  paired SMICA products, training-selected control, heldout
  MSE/paired bootstrap, lowrank boost-surrogate tangent,
  JSON, report and PNG.
- htt/obsstat/cf4_q_nuisance_ablation.py:
  arbitrary positive-diagonal weighted nuisance projection;
  raw/conditional generalized relative Fisher eigenvalues
  and exact radial fourth-moment alias bound.
- scripts/run_htt_cf4_q_nuisance_ablation_20261015.py:
  authenticated real CF4 raw and existing PR179 folds,
  source-bound nuisance ablations, exact alias witness,
  report and plot.
- Two new targeted test modules ensure fixed geometry,
  basis rotational invariance, train-only selection,
  tied finite-null rank, independent physically planted
  lowrank predictor recovery and Gaussian-null calibration;
  q nuisance nesting, coordinate/weight invariance,
  exact fourth-moment asymptotics, complex fail-closed.

## C6–C8: Executed numerical runs

Planck authoritative source application:
  PYTHONPATH=htt:htt/src:scripts OPENBLAS_NUM_THREADS=2
  OMP_NUM_THREADS=2 python3
  scripts/run_htt_geometric_lowrank_20261015.py
  --output-dir
  docs/research_program/theory_obs_application_20261015/loop3/results/planck_geo_lowrank_v2

Result: real same-sky null 300 pairs (60/240), two registered
masks, rank3 rho4 selected by training-only fivefold CV on both.
Relative heldout MSE +0.2345% and +0.2600%; rank 172/241
conditional. Planck surrogate boost Jacobian inheritance checked
against prior processed L12 source, conditional response/scatter
reference is approximately 0.0221/0.0223, no physical inference.
Input 512MB cache remains unchanged. Earlier v1 is immutable
pre-Jacobian historical execution; v2 authoritative interpretation.

CF4 authoritative source:
  PYTHONPATH=htt:htt/src:scripts OPENBLAS_NUM_THREADS=2
  OMP_NUM_THREADS=2 python3
  scripts/run_htt_cf4_q_nuisance_ablation_20261015.py
  --output-dir
  docs/research_program/theory_obs_application_20261015/loop3/results/cf4_q_nuisance_v2

Result: actual raw 38,053 / PR179 35,549 groups,
original q scalar frozen response reproduced in all five folds,
sequential nuisance relative Gram eig calculations.
Mean residual information for prior base+H+cubic is 0.002655.
Fourth-moment exact constructive alias bound verified, with
actual best H+cubic q trace squared residual 0.006770
against bound 0.018467. Prior v1 retained as historical
pre-alias-witness result.

## C9–C10: Scientific boundary and handoff

Independent symbolic check: Wolfram polynomial identity,
leading narrow-shell fourth-order asymptotics and ridge
scalar regression loss. Independent numerical reference:
prior repo source comparison and controlled local synthetic
regressions. Do not label these as fresh-context independent
human/multi-agent review. Native subagent tool is not exposed;
native_subagent=NOT_RUN.

Actual paired/mock sky source identity, raw group cohort,
mathematical and byte provenance, test records and blocker
delta belong to the local loop3 MANIFEST.json and
BLOCKER_DELTA.json. No native Bianchi solver, no new physical
CF4 q posterior, no authoritative Planck anomaly claim.

Next executable experiment within present files: construct a
physical prior on high harmonic source coefficients and test
its cross-source reliability, or obtain independent calibrated
sources/realistic foreground-split E2E observations. No
unjustified statistic/published likelihood promotion.
