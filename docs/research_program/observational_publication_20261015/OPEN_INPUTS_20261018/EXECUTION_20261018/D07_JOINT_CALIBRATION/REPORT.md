# D07 actual joint-calibration contrasts

HTT owner; C0 / CONDITIONAL; exploratory, non-claim-bearing. This is one bounded
execution of [D07_CONTRACT.md](../D07_CONTRACT.md), framed by an Astra/xhigh agent
whose observed runtime is UNKNOWN. A different fresh reviewer must assess this
execution. The requested executor is Sol/high; observed model/effort are UNKNOWN.
The existing checkout is `research/htt-open-input-theory-20261018`.
`6219ff0923890aab487135c98db5dd0d5f6dbdf7` is the D03/task-intake identity,
not an observed campaign execution HEAD. Campaign HEAD is
`NOT_DIRECTLY_OBSERVED`. Initial candidate freezing directly observed
`3677216f5ddfe6fd0b159b830db003aa3095b269`; this observation does not establish
the earlier campaign HEAD. Parent dispatch requested the Sol/high profile;
the exact requested model is `UNVERIFIED`, and observed model/effort are UNKNOWN.
The original receipt's hardcoded `gpt-6-sol` and `base_head=6219...` fields remain
preserved historical metadata, not runtime or campaign-HEAD attestations.
Only this new D07 directory was written.

## Main result

The actual source-defined joint model has a nonempty reference-compatible set
at minimum dimensionless radius **tmin = 1.4172887581262443**. One campaign
completed exactly **97 LPs in 8.783 seconds**, under the unchanged 97-LP / 10-minute
caps. This radius is a deterministic compatibility/sensitivity quantity, not a
noise quantile, confidence level, measured covariance, or physical remainder bound.

The actual eight gauge witnesses give **zero** residual in the H02, CF4–Pantheon,
and Pantheon–Cepheid prediction blocks. Thus the absolute common calibration
`eta` and every latent apparent coefficient `theta_w` remain unbounded in the
declared model; physical interpretation is UNAVAILABLE. The relative fields can nevertheless be studied
conditionally. After explicit scalar-nuisance projection, the joint angular
design has **rank 80 of 96**. The relative apparent `psi_w` and calibration
contrast `chi` are design-estimable; `zeta` retains the common gamma confounding
and is only bounded here by the declared ±0.02-mag relative-gamma boxes and
finite reference radius. This is not an independent angular anchor or a physical
shear/tilt determination. Original H02/S02/S04/H04/K04 acceptance remains HOLD.

## Actual inventory and retained dependence

The reviewed D03 candidate was reused without modification: aggregate
`c326fc79b4cfd255d4655cb47b27a4b399403179c3342ac30ae7113c80dcc388`, result
`c711a82bf5dbe95fd7bd847fea2d7b7d8f30e18463d9113de406ae16dbbf7296`.
The selected CF4 source is the frozen pooled NPZ with SHA-256
`86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`.

| Inventory | Actual count / treatment |
|---|---|
| D03 rows in selected H02 groups, before exclusions | 559 |
| Pair rows retained | 559; no pair exclusions |
| Distinct associated host PGCs / pooled groups | 437 / 429 |
| Pooled partitions among pairs | FP 20; TF 2; SN 430; OTHER 107 |
| Published calibrator residual inventory | 77 rows |
| Corroborated host-direction support | 75 rows, 37 literal named hosts |
| Strict CF4-linked calibrator subset | 65 rows; not required for c support |
| Unknown calibrator host directions | `2005df_ANU`, `2008fv_comb` |
| Pantheon rows appearing in both retained blocks | 12 |
| D02 target-outcome overlaps | 6 host rows; 15 group rows |

The contract framer clarified that the 75 rows with explicit same-release
SNID/IAUC aliases, corroborated SN sky, and finite valid named-host J2000
coordinates form the c angular block. CF4 linkage is not required. All 77
`MU_SH0ES − CEPH_DIST` residuals are retained; only the two uncorroborated
directions are excluded from angular fitting/scoring. There is no `-999`
propagation, zero fill, SN-position substitution, or invented alias. The same
75 indices select c, its covariance block, and its design. Repeated host rows
and their named-host incidence matrix are retained, with the full released
Pantheon covariance subblock. The original 1,543 literal Pantheon CIDs are not
promoted to independent objects.

Each pair uses **pooled group DMzp minus MU_SH0ES**, its exact group ID,
`e_DMzp`, selected group direction, and original pooled partition. It does not
use method-specific `DMsnIa`/`DMtf` as a substitute for the pooled distance.
The pooled FP/TF/SN/OTHER partitions are not raw independent calibration
contributor labels. D02 outcomes are annotations only; no selection weights or
parent targeting probabilities are introduced. H02 centers, boxes and source
membership are reused; the 35,970-group regression is not repeated.

## Shared model, conventions and gauge check

All angular coefficients are magnitudes in the original J2000 equatorial raw
basis `(nx, ny, nz, nx²−nz², ny²−nz², 2nxny, 2nxnz, 2nynz)`. Pair directions
are the selected CF4 group directions; c uses the corroborated host directions.
Transporting the Pantheon angular response to a group direction has an unmeasured
angular/depth discrepancy, retained in the declared pair-comparison remainder.
It is not a physical finite-z/flow error budget.

The shared original parameters and predictions are:

```
b_mw = theta_w + eta + gamma_m + epsilon_mw
a_i  = Za_i alpha + Xg_i (eta + gamma_m(i) - kappaP) + ra_i
c_i  = Zc_i beta  + Xh_i (kappaP - kappaC) + rc_i
```

The same 32 gamma coefficients apply to all five H02 windows and all pair rows.
`kappaP` and `kappaC` are unrestricted; no angular calibration response is fixed
to zero. `Za` retains common, observed-survey and pooled-partition scalar offsets
(20 columns); `Zc` retains common and observed-survey scalar offsets (14 columns).
Their combined nuisance rank is **31/34**; redundant one-hot columns are retained
with explicit SVD nullspaces, rather than regularized or silently dropped.

For each of the eight unit vectors v, the stored actual-design witness shifts
`theta_w → theta_w − v`, `eta → eta + v`, `kappaP → kappaP + v`, and
`kappaC → kappaC + v`, with gamma unchanged. All three displayed predictions
cancel exactly in floating arithmetic; the scaled infinity residual is 0, below
the contracted 1e-12 threshold. Arbitrary multiples of these witnesses preserve
all constraints and move every absolute common-calibration eta and latent
apparent theta coordinate without bound in this declared model. These
parameters are not established physical observables.

The invariant targets are `zeta = eta − kappaP`,
`psi_w = theta_w + kappaP`, and `chi = kappaP − kappaC`. Their maximum
response to the actual projected-design nullspace is approximately 0.447,
2.90e-15, and 1.51e-15 respectively. The latter two are estimable in the finite
design; zeta is not design-only estimable without the gamma bounds. The c scalar
nuisance rank is 13 and its projected eight-column relative angular response has
rank eight. Only chi ranks/nullspace are reported; no extra chi projection LPs
were run. Full singular values, nullspaces and ranks at 0.1×/1×/10× the rule
`max(shape) eps smax` are recorded. All reported ranks are stable; the joint
angular tolerance is 5.079488615745902e-12.

## Reference norm and conditional projections

The untouched Pantheon raw covariance retains its known 3e-8-mag² asymmetry;
the calculation explicitly uses the same labelled symmetric part as D03.
The pair norm whitens its exact full selected subblock plus
`B diag(e_DMzp²) B.T`, with repeated rows sharing the same pooled-group error.
The calibrator norm whitens its exact 75-row symmetric Pantheon subblock.
The whitening is the **principal symmetric inverse square root**, which avoids
an order-dependent Cholesky infinity norm. Reversing the actual data/covariance
and independently rebuilding both whiteners changes the whitened designs by at
most 1.47e-13 and whitened data by at most 3.11e-14.

The two norms are applied as separate deterministic inequalities. Their zero
crossblock is a chosen **reference norm**, not a measurement or imputation of a
missing joint covariance. The overlapping 12 row indices and the Pantheon
row-error crossblock component are retained separately; CF4 shared calibration,
the joint survey/ladder law, selection, velocity and pair transport remain unknown.
No block independence or confidence/coverage interpretation follows.

The H02 constraints retain all five windows, all four pooled partitions, eight
coefficients each, Gaussian-marginal union-bound rule with alpha=.05 and 160
comparisons, and the unchanged `|gamma_mj| ≤ .02 mag` component bounds. After
minimizing t, the remaining 96 LPs project all eight zeta and eight base-window
psi coordinates at `tmin + {0,1,2}`. The increments are dimensionless sensitivity
choices, not measured errors or noise levels.

Selected dipole-coordinate projections illustrate their strong radius dependence:

| Target | tmin+1 (mag) | tmin+2 (mag) |
|---|---|---|
| zeta nx | [−0.39459, +0.35393] | [−0.55949, +0.51423] |
| zeta ny | [−0.49346, +0.45803] | [−0.70323, +0.68162] |
| zeta nz | [−0.58068, +0.55390] | [−0.84913, +0.83894] |
| psi base nx | [−0.34294, +0.40562] | [−0.50337, +0.57052] |
| psi base ny | [−0.47721, +0.51286] | [−0.70068, +0.72215] |
| psi base nz | [−0.47501, +0.69518] | [−0.76214, +0.96334] |

At exactly tmin the numerical zeta endpoint pairs are near
`[-.009339, -.072824, +.006387, +.094774, -.008367, -.002474, +.095898, -.120632]`
mag, but these must **not** be asserted exact singleton projections. Nine raw
endpoint pairs (all eight zeta plus base psi nx) have lower/upper ordering
differences of 2.39e-14–5.54e-14 mag and are labelled
`NUMERICALLY_UNRESOLVED_WITHIN_SOLVER_PRECISION`. The raw solver outputs and
witnesses are unchanged. The model defines sharp mathematical projections;
finite numerical endpoint values have the stated solver precision, not exactness.

All 97 HiGHS solves returned nominally optimal. Primal/dual feasibility tolerances remain
1e-9; independently reconstructed endpoint witnesses give maximum H02 violation
2.16e-16 mag, reference-norm violation 1.02e-12 units, and gamma-bound violation
1.97e-13 mag, within the unchanged 1e-7 verification ceilings. No LP was repeated,
bound relaxed, value clamped/reordered, or budget reset.

The fresh independent reviewer reconstructed all 97 objectives and primal
constraints (maximum violation about 1.016e-12), and checked dual witnesses
using linear algebra only (maximum gap about 5.65e-13 and stationarity residual
about 1.066e-12), as reported by the controller. These support floating-point
numerical optimality under the declared tolerances, not an exact certified
optimum or exact endpoint order. This review added no LP solve or numerical
campaign; the two metadata/language findings remain for the same reviewer's
targeted closeout.

## Execution, tests and first failure

The existing `.venv` uses Python 3.12.3, NumPy 2.5.4, SciPy 1.18.1,
Matplotlib 3.11.2 and Astropy as recorded in [RUN_RECEIPT.json](RUN_RECEIPT.json).
BLAS/OMP/MKL limits and HiGHS `threads` are two. SciPy emits the documented
passthrough notice for the HiGHS thread option; this is recorded per solve.

The original bounded campaign command was:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D07_JOINT_CALIBRATION/run_validation.py
```

It cannot silently launch another campaign: `d07.py` refuses to run if an LP
ledger exists. Recheck tests and rendering without any LP using:

```bash
OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2 .venv/bin/python docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/D07_JOINT_CALIBRATION/run_validation.py --verify-only
```

Final verification is **11 focused tests PASS**, no skips, with the frozen D03
candidate files checked unchanged and actual full
covariance/index bindings, all 97 actual witnesses rechecked without solving LPs,
source basis/signs, same gamma across windows, all actual gauge and invariant
responses, invalid-host rejection, redundant scalar quotient and principal-norm
permutation invariance. The initial mathematical fixtures also passed before the
campaign. No source/rank/gauge/endpoint validation failure occurred.

The first figure attempt failed because `errorbar` requires nonnegative lengths,
while the retained tiny endpoint crossings yield negative floating widths.
[FIRST_FAILURE.txt](FIRST_FAILURE.txt) and the prior receipt retain the raw
failure. The controller authorized presentation-only repair: direct raw endpoint
segments and an explicit unresolved-order label. `annotate_endpoints.py` changes
only descriptive ordering metadata; the numerical objectives and witness NPZ
remain unchanged. The final PNG/PDF render succeeds; the PNG is visually inspected.

The review bundle is [D07_RESULT.json](D07_RESULT.json),
[actual design/witness NPZ](D07_DESIGN_WITNESSES.npz),
[all raw LP outcomes](LP_RAW.json), [PNG](D07_JOINT_CALIBRATION.png),
[PDF](D07_JOINT_CALIBRATION.pdf), code, tests and this report. The single figure
is emitted in two formats. No upstream code, full SH0ES named ladder fit,
35,970-group refit, solver/ODE, ideal maser augmentation, commit/push or canonical
status change occurred. The unresolved authoritative 47-column SH0ES mapping is
not inferred from table order or values.

## Claim audit and next transition

| Claim | Status / owner | Evidence / ceiling |
|---|---|---|
| Exact selected pairs and retained calibrator support | implemented/tested / htt | actual 559/77/75 inventory and full covariance row tests |
| Absolute common calibration eta and latent apparent theta unbounded in this declared model | finite actual-design witness / htt | eight cancellation directions; physical interpretation UNAVAILABLE |
| Relative target rank and radius-sensitive projections | CONDITIONAL / htt | stable finite-design SVD and 97 retained LP witnesses |
| Source-conditioned t or intervals imply physical coverage | forbidden | reference norm, pair transport, calibration/selection law unmeasured |
| Original node acceptance or independent anchor supplied | HOLD | no such promotion |

One authorized metadata/language repair preserves `RUN_RECEIPT.json` byte-for-byte
and the initial candidate as `CANDIDATE_INITIAL.json`. It distinguishes intake,
initial-freeze and unobserved campaign identities, leaves exact model identity
unverified, and corrects eta/theta language in this report, result metadata and
figure text. The numerical generator, all 97 raw LP outcomes/objectives,
design/witness NPZ, nine unresolved endpoint crossings and first plot failure
are unchanged. Only the changed figure text was rendered; the campaign wrapper
and annotator were not run. Its future wrapper metadata now observes the HEAD
at wrapper start and distinguishes that from the campaign HEAD. See
`METADATA_LANGUAGE_REPAIR.json` for the exact preservation checks.

Next: the same independent Astra reviewer closes these two findings against the
revised candidate. Safe follow-on work can use these shared
designs and explicit gauge/relative directions; physical admission requires the
missing joint selected-data/calibration/velocity/transport law or justified bounds.
