# PMG-WU-011 Task-7C Augmented Source-Band Convergence and Nuisance-Span Design

## Status and authority

`DESIGN_FROZEN / IMPLEMENTATION_NOT_STARTED`

- Repository: `cosmosapjw-quantum/htt_base`
- Draft PR: `#444`
- Task-7B execution source: `13d40cb4d600e9e5687f27f506aa978c77cbcfb7`
- Task-7B audit head: `fbf89ad6cd34bc7278bc51c1185bd29f1acb120f`
- Task-7B terminal: `PASS_TASK7B_ATLAS_NO_CANDIDATE`
- Task-7B atlas content ID: `sha256:fb1e31753212f4f4738a31ef949c2d480cae77de259b29bb2f7d98b22b44a98a`

Fixed conventions remain metric `(-,+,+,+)`, outward sky direction `n=-e`, active local observer boost `+beta`, `beta=v/c`, and thermodynamic-temperature Doppler weight `d=1`.

## Motivation

Task-7B found no admissible cut-sky candidate in its registered family. The wide apodized identity-transfer case improved the response condition to `32.21`, but its source-`ell=6` raised-channel alias remained `2.52` times the physical `6->5` neighbour and its source-`ell=7..9` tail remained `5.28` times that neighbour. The tail projected into the registered low-source response image at fraction `0.961`.

The reference cases were worse: tail/neighbour `34–38` and projection fractions above `0.9985`. Therefore Task-7C must not fit an empirical velocity or merely enlarge the deterministic inverse. It must answer two narrower questions:

1. Does the high-ell processed response converge as the source cutoff and pixel resolution are increased?
2. Once the high-ell source is treated as unrestricted nuisance, does any low-source local-boost response remain outside its image?

## Dimensional obstruction

The registered anisotropy source has dimension

```text
sum_(ell=1)^6 (2 ell+1) = 48.
```

The first diagnostic tail `ell=7..9` has dimension

```text
15+17+19 = 51.
```

The stacked three-axis output dimension is `3*32=96`. A naive augmented deterministic response through `ell=9` therefore has `99` source columns and generic nullity at least three.

For one fixed boost direction, the retained output has dimension 32 while the `ell=7..9` nuisance has 51 coordinates. Unrestricted nuisance can generically span the entire retained output. A joint point inverse of all low- and high-source coefficients is therefore forbidden.

## Directional response geometry

For registered low-source tensor `J_i` and extended high-source tensors `K_i^(ell)`, define for a unit boost direction `bhat`

```text
J_bhat = sum_i bhat_i J_i in R^(32 x 48),
K_bhat(L) = [sum_i bhat_i K_i^(7) | ... | sum_i bhat_i K_i^(L)].
```

All matrices must be whitened with the retained stored-real output metric and the appropriate source-block Parseval metrics.

Let `Q_K` be an orthonormal basis for `Im K_bhat(L)` and

```text
P_K_perp = I_32 - Q_K Q_K^T,
J_surv = P_K_perp J_bhat.
```

Report:

- `rank(K_bhat)` and its singular values;
- `rank(J_bhat)`;
- `rank(J_surv)`;
- `||J_surv||_F / ||J_bhat||_F`;
- minimum and maximum principal angles between low and high response images;
- low-source sector participation in surviving directions;
- stability under source cutoff and resolution.

This is a deterministic model-free identified-subspace test. It does not estimate beta.

## Registered boost directions

Use six sign-nonredundant directions because the response is linear in beta:

```text
X = (1,0,0)
Y = (0,1,0)
Z = (0,0,1)
D111 = (1,1,1)/sqrt(3)
D1M11 = (1,-1,1)/sqrt(3)
D11M1 = (1,1,-1)/sqrt(3).
```

The mask breaks rotational invariance, so Cartesian axes alone are insufficient as an adversarial direction set.

## Registered source-cutoff and resolution ladders

### Core ladder

Use the wide apodized identity-transfer operator, which was the best Task-7B cut-sky case:

```text
nside = 16
processing_lmax = 17
source cutoffs L = 9, 12, 16.
```

Every extended source block at ell requires `processing_lmax >= ell+1`.

### Resolution controls

At cutoff `L=12`, compare

```text
nside = 16, processing_lmax = 17
nside = 32, processing_lmax = 17.
```

### Operator controls

At `nside=16`, `L=12`, compare

```text
FULL_IDENTITY
APODIZED_Z_WIDE_IDENTITY
APODIZED_Z_REFERENCE_GAUSSIAN.
```

The full-sky case is a numerical zero control for every source `ell>=7`. The reference case remains a failure control.

## Source-band convergence diagnostics

For source block `K^(ell)`, report its metric Frobenius and operator norms. For cumulative tail through `L`, report

```text
T_F(L) = ||[K^(7)|...|K^(L)]||_F,
T_2(L) = ||[K^(7)|...|K^(L)]||_2,
last_fraction_F(L) = ||K^(L)||_F / T_F(L),
last_fraction_2(L) = ||K^(L)||_2 / T_2(L).
```

Because cumulative norms are nondecreasing, convergence is not defined by `T(L)-T(L-1)->0` alone. A cutoff is provisionally converged only when both last-block fractions are below a preregistered ceiling and the nuisance image/rank diagnostics are stable between the two highest cutoffs.

Engineering ceilings for this synthetic node:

```text
last_fraction_F <= 0.10
last_fraction_2 <= 0.10
rank(K_bhat) unchanged between L=12 and L=16
rank(J_surv) unchanged between L=12 and L=16
surviving_Frobenius_fraction absolute drift <= 0.02.
```

These are numerical stopping rules, not physical priors or inference theorems.

## Model-free terminal semantics

```text
PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE
PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE
PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED
BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE
BLOCKED_BY_CUTOFF_CONSTRUCTION
BLOCKED_BY_ARTIFACT_INTEGRITY.
```

- `IDENTIFIED_SUBSPACE`: source-band stopping rules pass and every registered direction retains a nonzero stable `J_surv` rank.
- `NO_IDENTIFIED_SUBSPACE`: source-band stopping rules pass and the high-source nuisance spans the low response image for every registered direction within tolerance.
- `SOURCE_BAND_NOT_CONVERGED`: execution succeeds but the `L=16` stopping rules fail. This is a valid negative characterization and must not be converted into a code failure.

## Covariance-aware successor boundary

If arbitrary deterministic nuisance removes the low response, a later statistical lane may introduce an explicitly declared high-ell covariance `C_H`. For fixed beta,

```text
A(beta) = sum_i beta_i K_i,
Sigma_eff(beta) = Sigma_0 + A(beta) C_H A(beta)^T.
```

The likelihood must include both the quadratic form and `log det Sigma_eff(beta)`. A simplified constant-covariance linear likelihood is not automatically valid because the nuisance response is proportional to beta.

Task-7C does not choose `C_H`, fit beta, or claim statistical identification. It only determines whether a model-free survivor exists and whether the high-source cutoff is numerically controlled.

## Mandatory outputs

- exact case, direction, cutoff, and source-mode registries;
- directional low/high/surviving ranks;
- source-block and cumulative tail norms;
- principal-angle and projection tables;
- source-cutoff and resolution convergence tables;
- separate figures for block decay, nuisance rank, surviving low-response fraction, principal angles, and cutoff convergence;
- typed terminal, source SHA, dependency identities, and SHA-256 manifest.

## Claim boundary

No admitted Planck absolute-temperature product, observed rank, empirical beta, boost subtraction, global matter-frame tilt, foreground exclusion, polarization result, Bianchi-family attribution, causal identification, or P01-P27 formal-dossier replay is introduced. A no-identified-subspace terminal is a model-free operator result, not evidence against physical observer motion.
