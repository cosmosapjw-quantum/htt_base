# PMG-WU-011 Task-7B Cut-Sky Identifiability and Sensitivity Design

## Status and authority

`DESIGN_FROZEN / IMPLEMENTATION_NOT_STARTED`

- Repository: `cosmosapjw-quantum/htt_base`
- Draft PR: `#444`
- Task-7A verified predecessor: `b2422d9435eafbebd2584b747cb4b4ef9716caaf`
- Task-7A artifact commit: `db8c0f4a1bbce86a0fa82ba5941aaef0e6f040cf`
- Metric signature: `(-,+,+,+)`
- Outward sky direction: `n=-e`
- Active local observer boost: `+beta`, `beta=v/c`
- Thermodynamic-temperature Doppler weight: `d=1`

Task-7A established a deterministic processed-response substrate, but its reference cut-sky case had metric-whitened nonzero condition `407.914947`, FWL Schur condition `15415.6425`, and raised-ell alias / physical `ell=6->5` neighbour ratio `21.4783276`. Task-7B determines which mask, transfer, source sector, and out-of-band modes create this failure. It does not fit or subtract a velocity.

## Scientific question

For the frozen processed map

```text
positive absolute sky
-> finite or linear local-observer boost
-> source beam/pixel transfer
-> HEALPix synthesis
-> weighted simultaneous ell=0..5 fit
-> post-fit commonization
-> retained ell=2..5 carrier,
```

which processing choices control

1. the metric-whitened nonzero singular condition of the registered `(3,32,49)` response;
2. the weak right-singular source combination;
3. the physical `ell=6->5` response versus raised-channel alias;
4. the leakage from source multipoles `ell>=7` into the retained carrier;
5. whether a numerically plausible candidate survives for later covariance-aware validation?

## Evidence classes

- `FULLSKY_REFERENCE`: exact or convergent formula/normalization checks.
- `PROCESSED_SYNTHETIC`: frozen HEALPix, mask, transfer, and joint-solve response.
- `DIAGNOSTIC_CANDIDATE`: passes explicit engineering floors but is not an inference operator.
- `REFUSE_CURRENT_OPERATOR`: rank, conditioning, alias, or source-band sensitivity blocks inference use.

## Registered case family

All `CI_CORE` cases use `nside=16`, `processing_lmax=12`, fit `ell=0..5`, and retain `ell=2..5`.

### Mask isolation at identity transfer

1. `FULL_IDENTITY`
2. `BINARY_Z_IDENTITY`
3. `APODIZED_Z_NARROW_IDENTITY`
4. `APODIZED_Z_REFERENCE_IDENTITY`
5. `APODIZED_Z_WIDE_IDENTITY`

The three apodized masks have equator-centred linear transitions of total width `0.45`, `0.90`, and `1.50` in `z=cos(theta)`. The binary mask uses the same half-sky orientation. Record

```text
f_sky_mean = mean(W)
f_sky_quadratic = mean(W^2)
f_sky_effective = mean(W)^2 / mean(W^2)
transition_fraction = mean(0 < W < 1).
```

### Transfer isolation at the reference apodized mask

6. `APODIZED_Z_REFERENCE_MATCHED_GAUSSIAN`
7. `APODIZED_Z_REFERENCE_GAUSSIAN`

The matched case uses identical source and target beam/pixel arrays. The reference case retains the Task-7A non-amplifying source/target mismatch. This separates mask-induced mode mixing from post-fit commonization effects.

## Invariant response diagnostics

Use the Task-5B scientific metrics

```text
G_S = diag(4*pi,G_1,...,G_6)
G_R = diag(G_2,G_3,G_4,G_5)
J_tilde = (I_3 kron G_R^(1/2)) J_stack G_S^(-1/2).
```

For every case report:

- scientific anisotropy rank;
- metric-whitened nonzero condition number;
- joint normal-matrix condition number;
- exact scientific `T0` null and separate replay leakage;
- source-sector Frobenius fractions;
- source-sector weights of the weakest right singular vector;
- physical `ell=6->5` neighbour norm;
- raised-ell processed alias norm and alias/neighbour ratio.

The source-sector diagnostics are

```text
F_ell = ||J_tilde P_ell||_F^2 / ||J_tilde||_F^2,
p_ell = ||P_ell v_min||_2^2,
```

where `v_min` is the unit right singular vector associated with the smallest nonzero singular value. Both sets must sum to one within numerical tolerance.

## Extended out-of-band response

The frozen physical sky class remains `ell<=6`; do not weaken it. Task-7B adds a separate signed first-order diagnostic builder for scientific stored-real basis modes at `ell=7,8,9`.

For each source `ell`, construct

```text
K_ell in R^(3*32) x (2*ell+1)
```

using the same Doppler-weight-one generator, source transfer, HEALPix synthesis, weighted joint fit, commonization, and retained selector. Since no `ell>=7` source has a direct full-sky neighbour in retained `ell=2..5`, every nonzero processed block is out-of-band leakage.

Report:

```text
block_frobenius_norm
block_operator_norm
cumulative_tail_frobenius
cumulative_tail_to_ell6_neighbor
projection_fraction_into_low_source_image
minimum_principal_angle_degrees.
```

The projection fraction uses the metric-whitened column space of the registered `ell=1..6` response. A large fraction means high-ell leakage is observationally confounded with the declared low-source response.

## Exact Wolfram oracle

For the full-sky registered response,

```text
sigma_ell^2 = {8/3,27/5,13,21,125/11,216/13}
trace contributions = {8,27,91,189,125,216}
total metric Frobenius square = 656
sector fractions = {1/82,27/656,91/656,189/656,125/656,27/82}
kappa_nonzero = sqrt(63/8).
```

For normalized `v_min`, the six sector weights sum to one. These are formula checks, not processed-case predictions.

## Candidate and refusal semantics

A case is only a `DIAGNOSTIC_CANDIDATE` when all of the following hold:

```text
anisotropy_rank == 48
metric_whitened_nonzero_condition <= 100
ell6_alias_to_neighbor <= 1
cumulative_ell7_to_ell9_tail_to_neighbor <= 1
source-sector and weak-mode weights close to unit sum
all matrices finite and content-bound.
```

These floors are engineering preregistration for selecting cases for later covariance-aware work. They are not a theorem of statistical identifiability.

Task-7B terminal states are:

```text
PASS_TASK7B_ATLAS_CANDIDATE_FOUND
PASS_TASK7B_ATLAS_NO_CANDIDATE
BLOCKED_BY_CASE_CONSTRUCTION
BLOCKED_BY_METRIC_INCONSISTENCY
BLOCKED_BY_EXTENDED_BAND_FAILURE
BLOCKED_BY_ARTIFACT_INTEGRITY.
```

A no-candidate terminal is a successful characterization, not a failed experiment.

## Mandatory outputs

- `summary.json` and `terminal.json`;
- case table and sector-participation table;
- extended-source leakage table;
- scientific matrices or content-addressed compressed arrays;
- separate figures for condition versus mask, alias/tail norms, weak-mode sector weights, source-sector Frobenius fractions, and high-ell leakage decay;
- SHA-256 manifest;
- exact source revision and dependency identities.

## Claim boundary

No admitted Planck absolute-temperature product, observed rank, empirical `beta`, boost subtraction, global matter-frame tilt, foreground exclusion, polarization result, Bianchi-family attribution, causal identification, or P01-P27 formal-dossier replay is introduced. The Bianchi photon hierarchy remains a separate formula authority and does not convert this observer-side response atlas into a solver or inference result.
