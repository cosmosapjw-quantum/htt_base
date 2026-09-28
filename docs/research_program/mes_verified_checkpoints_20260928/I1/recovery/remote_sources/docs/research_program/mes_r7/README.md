# MES R7 conditional source image

WORK_UNIT: `MES_R7_CONDITIONAL_SOURCE_IMAGE_IMPLEMENTATION`.
Owner: common numerical kernel / obsstat frozen-release adapter.
Scope: `CONDITIONAL_SCENARIO_AND_SCOPED_IMPLEMENTATION`; opt-in research code.
Current status: implementation, frozen replay and independent review content pass;
historical runtime acceptance remains blocked.
The owner authorized local integration and publication to `main` on 2026-09-22.
Production enable and scientific admission remain unauthorized.

The owner authorized this independent slice on 2026-09-21, preserving R9's next
D2 task, D4/FORMAL_DEPTH obligations, budgets, failures and HOLDs. The local card
`PR-MES-R7-SOURCE-IMAGE` depends only on the already completed `PR-R9-INTAKE`
interface. It does not replace or admit R9. Base commit
`870bd67af159993ccde4ede9923424a475c01375`, tree
`415d789446e836b97e8a8f64343450c170237b2f`; branch
`implementation/mes-r7-conditional-source-image-20260921`.

## Fixed input and implemented object

Original supplied ZIP SHA256:
`eb78eb20ca29dec2d6c6b2cb59d40366ec19856795319ebc64a6bba474758ac7`.
Its accepted independent decision is `PROMOTE_CONDITIONAL_R7_FOR_LOCAL_INTAKE`;
this is prior source review, not review of this new integration. The input and
fixture byte pins are explicit in `obsstat.mes_r7_source_image.PINS`.

`common.conditional_source_image.BoxSourceImage` validates `(m,q,p)=(525,4,5)`.
It computes `Phi(xi)=-L log1p(-A xi)` with
`A=diag(1/(c*z-v0)) G diag(halfwidth)` and `c=299792.458 km/s`.
The row order, signed L, 525 distinct release indices and 418 literal CIDs are
preserved. Repeated CID does not imply independent SN and is not deduplicated.
Coordinates are ICRS Frobenius-orthonormal STF features and Galactic Cartesian
velocity calibration. `xi` is dimensionless in `[-1,1]^4`; calibration increments
have units `(dimensionless,km/s,km/s,km/s)`. `beta_flow=f/b_gal` is not tilt beta_a.

The kernel reuses the accepted prototype's Decimal primitives, finite dyadic cover
and witness optimizer, rather than defining a second bound. At depth 6 it covers
all 64 boxes with 42-digit directed arithmetic. Upper bounds enclose the function
of exact stored binary64 L/A/u, not astronomical preprocessing or physical truth.
SLSQP supplies feasible lower candidates only. Its returned candidate can be
projected into the latent box and re-evaluated; invalid physical logarithm or
redshift domains are never clipped. The remaining gap is returned unchanged.

The supported facade validates finite real arrays, shapes, row identities, units,
frames, nonnegative widths, whole-box logarithm and redshift domains, and each
shared xi. Zero widths are allowed. Ellipsoids return `UNSUPPORTED_DOMAIN` and
other m/q/p sizes return `UNSUPPORTED_SHAPE`. General notation is not generic
solver support. Internal arithmetic helpers retain the prototype's lower-level
signatures for exact reuse and tests; use the validated facade for input intake.

A realization contains one xi, its physical calibration increments and all five
feature coefficients. A support batch contains separate realizations for each
direction. It is not joint image membership, a convex body, or a MES anchor.
The first-order left-null direction still has finite nonlinear leakage. R6's
independent row-box translated zonotope is a different object. If a residual is
later registered, exact sequential composition requires denominator
`d-G delta_theta` with that same xi; independent images cannot simply be added
using the original denominator.

## Consumer and refusal behavior

`obsstat.mes_r7_source_image` checks frozen bytes, consumes the original fixture,
and reuses unchanged `ProductIntake(SCENARIO_ONLY)` and `SharedStateEmbedding`.
The latter is an incidence mapping, not a unit/frame converter. No new covariance,
likelihood, posterior, transfer equivalence or physical state is inferred.

The JSON returns `CONDITIONAL_SCENARIO`, 14 directional brackets/gaps, each latent
witness and its complete feature vector, and unresolved physical inputs together.
Other quantity requests, including empirical D, physical shear, joint confidence,
MES anchors or native results, return `INSUFFICIENT_PHYSICAL_INPUTS` and CLI exit 2.
No gamma, squared gauge, canonical directional F or physical MES D is computed.

Physical source closure, target/source full response and U_R/optical bridge remain
HOLD. Source mean/correlation/target transfer remain UNRESOLVED. Empirical MES D
is `HOLD_NOT_COMPUTED`. No zero/identity/independent-Gaussian fill is used.

## Reproduction and validation

Source directory in the current local delivery:
`/home/cosmosapjw/Dropbox/bianchi/htt_base/incoming/MES_R7_CONDITIONAL_SOURCE_IMAGE_INTAKE/mes_r7`.
The original CLI was run ONCE into `rerun/local_intake`; exit 0. Do not run that
command again at the same output path. Its source and original artifacts were not
changed. A single exclusive replay reservation and raw stdout/stderr are retained.

From this worktree, choose a NEW output directory for the adapter:

```bash
export MES_R7_SOURCE=/home/cosmosapjw/Dropbox/bianchi/htt_base/incoming/MES_R7_CONDITIONAL_SOURCE_IMAGE_INTAKE/mes_r7
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:htt/htt python3 -m obsstat.mes_r7_source_image --source "$MES_R7_SOURCE" --out /tmp/mes-r7-new-output --cover-depth 6
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:htt/htt python3 -m pytest -q htt/src/common/test_conditional_source_image.py tests/r9/test_intake_depth.py
```

Existing directories, files or dangling symlinks at the output path are refused
before computation; mkdir without exist_ok reserves the path against another
writer. Failed executions leave their output reservation for diagnosis.

The recorded environment is Python 3.12.3, NumPy 2.4.2, SciPy 1.17.0,
Matplotlib 3.10.8 and pytest 9.1.1. Before any replay, comparisons were fixed:
fixture floats rtol=1e-11/atol=5e-13; support/gaps/features
rtol=1e-10/atol=1e-12; direction/witness coordinates rtol=0/atol=1e-7.
These are separate roundoff/optimizer comparisons, not the source support gap.
No tolerance was increased after seeing results. Original derivative <1e-11,
STF coefficient <1e-15, orthogonality <1e-14 and bulk identity <1e-18 checks are
unchanged and exercised against the integrated arithmetic.

33 tests passed, including the real consumer, original arithmetic assertions,
input/domain/refusal/collision cases and the existing intake/depth interface tests.
These are unit/regression tests, not DESI/SDSS/CF3 experiment or R9 proof replays.
The first test collection failed because pytest reserves the parameter name
`request`; it was renamed to `quantity`. The first DAG check exposed missing
new-card topological coverage; only that new entry was added. Both original
failures are preserved. The corrected DAG validates with 207 cards.

Original replay: numerical comparison PASS; NPZ/JSON bytes differ, PNG bytes match.
The new adapter uses the exact saved fixture. All 14 upper endpoints match the
saved source endpoints exactly; the maximum lower/gap difference is
2.710505431213761e-19. Each full feature vector agrees with direct evaluation of
its own xi. Source support gap remains approximately 2.2956317334001065e-06.

Raw execution, prereplay criteria, comparison results, 14 complete query records,
source pins and review status are in the local return directory
`incoming/MES_R7_CONDITIONAL_SOURCE_IMAGE_IMPLEMENTATION/` in the original checkout.
Scientific numeric agreement, byte identity and independent review are separate
states. The registered reviewer actually ran the prescribed suite (33 passed),
returned `pass` with no findings, and its result envelope validated. This is
independent review content, not formal lifecycle acceptance. The original launch
`cl_30228d252e36403dc84a40c962f69dcf` remains tied to its historical worktree;
`CHILD_CONTINUATION_NOT_RESERVED` prevents terminal acceptance. A generated
validator bytecode cache also caused an earlier stop failure; interpreter `-B`
prevents the reproduced hook-side cache creation without changing validators.
The original failure receipts remain preserved. Do not label this work
`SCOPED_IMPLEMENTATION_REPLAY_COMPLETE` while that acceptance is unresolved.

## Integration into the primary checkout

The owner approved merging and publishing the existing conditional implementation,
not promoting its physical claims or historical review authentication. The primary
checkout now carries the exact kernel, adapter and test bytes that were reviewed.
The R9 runner correction is integrated through commit
`e70663a11651f1136b5368342f42fa6c89b8ad9a`; no R9 proof was rerun.
The local returns under `incoming/MES_R7_REVIEW_RETURN_20260922/` and
`incoming/MES_R7_HOOK_CACHE_REPAIR_20260922/` retain full numerical evidence and raw
failures. They are local evidence packages, not downloads supplied by this README.
The old worktree and its run identity are preserved; this checkout is not a
substitute runtime identity for that child. R9 D2, D4/FORMAL_DEPTH, all physical
HOLDs and empirical MES D=`HOLD_NOT_COMPUTED` are unchanged.

Primary-checkout integration validation (2026-09-22): the MES module, existing
intake/depth interface, and e70663a runner regressions passed together: 38 tests
and 5 subtests. The canonical 207-card DAG and its mirrors validate. These are
Host integration checks, not another independent review or a formal R9 replay.
The no-new-worktree instruction is delivered by the regenerated primary-checkout
context pack; no historical assignment was rewritten to that new context.
