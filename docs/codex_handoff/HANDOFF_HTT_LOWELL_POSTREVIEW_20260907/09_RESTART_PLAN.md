# 09 — RESTART PLAN

## First 15 minutes

| Step | Action | Input | Tool/command | Expected output | Stop/fail condition |
|---|---|---|---|---|---|
| 1 | Fresh-read active plan | PR463 `0e2d6e3a890ae44303440e8534fb6080d1dac881` | open `00_MASTER_PLAN_KO.md` and `03_PROGRAM_DAG.yaml` | exact current M1/M2/M3 status | if branch/head moved, stop and reconcile newer owner state |
| 2 | Read addendum without making it a second programme | PR464 `fa86d940f6d954af554bae5b577d5eb465aa2ae1` | open `REUSE_AND_DATA_MAP.md` and review-seeded corrections | code/data/source risks merged into the existing DAG | if a newer master conflicts, active owner-approved master wins; log conflict |
| 3 | Confirm source-role identities | default `50ea6d76...`, decoder `9f7d06de...`, boost `29427a1f...`, processed `de73549c...` | GitHub refs / local `git show` | role table, no source merge | if semantic donor moved, rebind before any implementation |
| 4 | Begin `M1_CMB_MODEL` | active master + implementation contract + selected product metadata | MAIN scientific work | exact CMB observation/joint-null model | do not delegate statistic/prior/null/product choice to Codex |
| 5 | Close `M2_REDSHIFT_MODEL` | addendum + selected CF4/DESI metadata | MAIN scientific work | explicit likelihood/windows/frame/functionals | if requested target is not identified, return partial-identification model rather than proxy |
| 6 | Build `M3_EXPERIMENT` | M1+M2 | MAIN | immutable finite execution table | fail if any “choose appropriate setting later” remains |
| 7 | Publish `THEORY_FREEZE` | M3 | Git handoff branch | exact Local Codex contract | execution forbidden before this |
| 8 | Run Local C0–C5 | frozen contract + workstation inventory | isolated worktree; exact commands from M3 | integration, tests, synthetic, intake, observed/typed stop, Git return | any science-model change returns to MAIN; ordinary defects repaired in scope |
| 9 | MAIN result review | C5 immutable Git evidence | GitHub connector | final result/claim ceiling | software PASS must not substitute for science result |

## Exact first action: close M1, do not write another plan

M1 must leave a single Git-readable mathematical specification answering all of the following:

1. Which exact PR3 temperature product is the **primary** analysis product? The present default candidate is PR3 SMICA, but product identity must be verified from owned metadata.
2. What ordered operation turns the stored product into the analysis vector? Specify units, component-separation convention, beam/pixel window, coordinate basis, monopole/dipole/kinematic-quadrupole treatment, mask and fit order.
3. What are the low and high data vectors, their dimensions, real-coordinate metrics and cross-covariance blocks?
4. Which foreground/noise/systematic quantities are random variables, deterministic nuisance parameters, conditioned measurements or sensitivity-only controls?
5. What is the primary morphology/response statistic? Which alternatives are secondary controls rather than a post-hoc scan?
6. What is the complete finite-null construction? State product-matched FFP10 requirements, unique realisation IDs, row dependencies, chart failure/abstention and tie/selection policy.
7. How are high-source truncation/tails handled for the selected mask? Do not reuse a universal `L=30` guess. Preserve the exact `L=10` axial theorem only in its continuum scope.
8. What finite numerical matrix is the target and what numerical error statement is required: rigorous enclosure or explicitly empirical convergence?
9. What exact conditions yield `NOT_RUN`, `UNIDENTIFIED`, `MODEL_INADEQUATE`, numerical failure or valid null-consistent output?
10. What aspects are sensitivity analyses (other PR3 components, admitted PR4, WMAP) and how are same-sky dependencies preserved?

M1 exit criterion: **no product, statistic, prior, null law, missing-response substitution or key numerical target is left for Local Codex to choose.**

## M2 concrete closure

M2 must select the actual distance/redshift observable and likelihood before looking at a preferred fitted direction. It must specify calibration/group nuisances, selection, coordinate frame, redshift/distance windows, cross-covariance with reconstructions and which of bulk/symmetric-affine/dipole-depth functions are identified. Preserve exact radial rigid-rotation nulls and the observer/free-shell gauge. Do not use a reconstruction or toy profile as native global tilt.

## M3 concrete closure

Compile M1/M2 into one finite table: exact estimands, product paths/semantic predicates, masks/bins/parameter grid, simulation IDs/roles, training/calibration/test split, null/alternative injections, multiplicity and coverage, power/effect-size targets, abstention rules, numerical tolerances/error budgets, missing-input branches and model-inadequacy outcomes. `THEORY_FREEZE` is the hash-addressed publication of this complete table and formulas.

## Failure return policy after freeze

C5 return is allowed from **any** C0–C4 node. Do not wait for observed-analysis success to return a real blocker. A missing data product blocks its lane, not every other admitted lane. Null scientific results and partially identified results are valid outcomes.
