# Dependency-gated execution schedule

## Phase F — foundation

`LR-06A` is the only entry gate. Freeze the baseline, merge PR04-002–007, run
all external and canonical tests, and serialize the integration manifest.

## Phase T — immediate theorem/method outputs

`LR-06B` and `LR-06C` run in parallel after the foundation gate.

- `LR-06B` closes PAPER-A: response-subspace identifiability, radial-vorticity
  no-go, single-shell degeneracy, complementary-channel sufficiency, and
  temporal tensor rank.
- `LR-06C` closes PAPER-B: Bianchi-I flux balance, PSD tilt moments, exact
  conservation, constraint transport, shear memory, and scalar nonclosure.

These papers do not wait for raw data or the new Rust solver.

## Phase D — delegated data/transfer work

`LR-06D`, `LR-06E`, and `LR-06F` may run in parallel. `LR-06G` depends on the
Bianchi-I dynamics gate and on a validated light-cone/transfer owner.

No task advances merely because a posterior becomes numerically nonsingular.
Each ticket must report data rank separately from prior-conditioned rank.

## Phase J — joint inference

`LR-06H` begins only when D–G have release hashes, covariance ownership,
injection coverage, and response manifests. It produces source-owned vector and
tensor posteriors, not legacy scalars as primitives.

## Phase R — restricted branch and reporting

`LR-06I` tests registered Bianchi-I branches. `LR-06J` performs the legacy
scalar pushforward. Missing trace, vorticity, curvature or tilt components block
the affected scalar rather than being set to zero.

## Phase P — PAPER-C result branch

`LR-06K` reruns the complete adaptive search in every matched mock. Its output
is either a calibrated source-owned detection or a simultaneous upper bound.
Both are scientifically strong endpoints; neither permits unrestricted Bianchi
family identification.

## Separate project

`LR-06L` owns the new Rust design. It starts from language-neutral golden
contracts and an exact FLRW comparator. Old Rust spectra, evidence and atlas
rankings are not inherited as validation.
