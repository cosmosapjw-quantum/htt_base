# PMG-WU-011 Task-7B Cut-Sky Identifiability Atlas Audit

## Authority and disposition

- Repository: `cosmosapjw-quantum/htt_base`
- Draft PR: `#444`
- Exact source head: `13d40cb4d600e9e5687f27f506aa978c77cbcfb7`
- Dedicated workflow: `WU011 Task7B identifiability #4 / 33593850011`
- Exact-head artifact ID: `9832711817`
- Artifact archive digest: `sha256:e0d59195f4b0941b21beed5294a4e859c0aacdaf9e5c040b0168ae0447b7aff2`
- Artifact branch: `artifact/wu011-task7b-13d40cb4d600e9e5687f27f506aa978c77cbcfb7`
- Atlas content ID: `sha256:fb1e31753212f4f4738a31ef949c2d480cae77de259b29bb2f7d98b22b44a98a`
- Manifest SHA-256: `6623d91262effe7b26946523976a568f624db5f54f6cd11dc038f418fcb6292e`

```text
PASS_TASK7B_ATLAS_NO_CANDIDATE
```

This is a successful negative characterization. All seven registered cases ran, all artifacts verified, and no cut-sky case met the simultaneous engineering floors for rank, metric-whitened condition, source-`ell=6` alias, and source-`ell=7..9` tail. No inference or claim promotion is authorized.

## Fixed conventions

```text
metric signature: (-,+,+,+)
outward observer sky direction: n=-e
active local observer boost: +beta
beta=v/c
thermodynamic-temperature Doppler weight: d=1
scientific source coordinate: physical T0 plus stored-real ell=1..6
retained coordinate: stored-real ell=2..5
```

Temperature coefficients have temperature units, `beta` and every coefficient-response Jacobian entry are dimensionless, and all singular diagnostics use the Parseval metrics of the stored-real harmonic coordinates.

## Registered response and exact full-sky oracle

For the stacked registered response,

```text
J_tilde=(I_3 kron G_R^(1/2)) J_stack G_S^(-1/2),
G_S=diag(4*pi,G_1,...,G_6),
G_R=diag(G_2,G_3,G_4,G_5).
```

Wolfram exact algebra gives source-sector metric Frobenius squares

```text
ell=1..6: 8, 27, 91, 189, 125, 216
sum: 656
```

and fractions

```text
1/82, 27/656, 91/656, 189/656, 125/656, 27/82.
```

The exact nonzero condition is

```text
sqrt(63/8)=2.806243040080...
```

with anisotropy rank `48` and one structural physical-`T0` null. The numerical `FULL_IDENTITY` case recovered condition `2.806251598509`, validating the normalization at the declared HEALPix resolution.

## Case results

| Case | Joint normal condition | Response condition | ell6 alias / neighbour | ell7..9 tail / neighbour | Tail projection into registered image | Candidate |
|---|---:|---:|---:|---:|---:|---|
| FULL_IDENTITY | 1.0051 | 2.8063 | 0.00129 | 0.00385 | 0.5409 at numerical-floor amplitude | no: full-sky control |
| BINARY_Z_IDENTITY | 3.216e6 | 8406.5 | 107.09 | 403.61 | 0.999987 | no |
| APODIZED_Z_NARROW_IDENTITY | 4.398e5 | 2550.5 | 58.10 | 156.25 | 0.999895 | no |
| APODIZED_Z_REFERENCE_IDENTITY | 3.335e4 | 496.97 | 21.57 | 38.09 | 0.998956 | no |
| APODIZED_Z_WIDE_IDENTITY | 857.58 | 32.21 | 2.516 | 5.279 | 0.961207 | no |
| APODIZED_Z_REFERENCE_MATCHED_GAUSSIAN | 3.335e4 | 390.13 | 19.89 | 34.20 | 0.998511 | no |
| APODIZED_Z_REFERENCE_GAUSSIAN | 3.335e4 | 407.91 | 21.48 | 36.94 | 0.998655 | no |

The preregistered cut-sky candidate floors were rank `48`, condition `<=100`, source-`ell=6` alias/neighbour `<=1`, and cumulative `ell=7..9` tail/neighbour `<=1`.

## What controls the failure

### 1. Mask sharpness is the dominant control

Relative to the reference Gaussian-transfer case, the wide identity-transfer apodization improved

```text
response condition: factor 12.6640
ell6 alias/neighbour: factor 8.5369
ell7..9 tail/neighbour: factor 6.9980.
```

The binary and narrow masks are catastrophically ill-conditioned. Wide apodization restores a near-full-sky weak-mode structure and yields a condition below the candidate ceiling, but its alias and extended-source tail remain above one.

### 2. Transfer mismatch is secondary in the registered family

At the reference mask, replacing the Task-7A source/target mismatch by a matched Gaussian transfer improved

```text
response condition: factor 1.0456
ell6 alias/neighbour: factor 1.0798
ell7..9 tail/neighbour: factor 1.0802.
```

Thus post-fit transfer commonization is not the primary origin of the no-candidate result. The fixed-mask joint solve and its coupling to out-of-band source modes dominate.

### 3. High-source multipoles are not a small correction

For the reference case, the registered response Frobenius weight is dominated by source `ell=6` at about `0.835`, with source `ell=5` at about `0.162`. The weakest right-singular combination is distributed mainly across `ell=1..4`, rather than remaining a nearly pure full-sky `ell=1` mode.

For the wide mask, source fractions shift to about `0.525` in `ell=5` and `0.396` in `ell=6`, while the weakest mode returns mainly to `ell=1` (`0.838`) and `ell=2` (`0.151`). This explains the large conditioning improvement without implying source-band closure.

### 4. The extended tail is almost completely confounded

In all cut-sky cases the metric projection of the `ell=7..9` tail into the registered low-source response image is between `0.961` and `0.99999`. The minimum principal angle is numerically zero or below `10^-6` degrees. Arbitrary high-ell source content can therefore mimic registered low-source processed responses almost perfectly.

The full-sky projection fraction and principal angle must not be interpreted physically because the full-sky extended blocks lie at the HEALPix replay floor. For non-negligible cut-sky tails, the near-unit projection is load-bearing.

## Extended-source values

The cumulative tail is built from separately typed source blocks `ell=7,8,9`.

- Full sky: block norms `0.0256, 0.0356, 0.0357`; cumulative tail/neighbour `0.00385`.
- Reference identity: `257.85, 416.98, 270.09`; tail/neighbour `38.09`.
- Reference Gaussian: `207.22, 333.54, 203.05`; tail/neighbour `36.94`.
- Wide identity: `58.57, 45.55, 22.66`; tail/neighbour `5.279`.

Only the wide case exhibits a monotonic decline over `ell=7..9`, but three sectors are insufficient to establish convergence.

## Dimension and identifiability consequence

The registered anisotropy source dimension is

```text
sum_(ell=1)^6 (2 ell+1)=48.
```

The diagnostic tail through `ell=9` has dimension

```text
15+17+19=51.
```

The stacked three-axis output has dimension `3*32=96`. Hence a naively augmented deterministic matrix has `99` source columns and at most rank `96`, so its nullity is at least three even before mask-induced near-collinearity.

For a fixed boost direction, the retained output dimension is only `32`, while the `ell=7..9` nuisance source has 51 coordinates. Unrestricted deterministic marginalization can therefore span the entire retained output. A model-independent point inverse is not an admissible next step.

## Literature cross-check

The result is structurally consistent with:

- Gruetjen & Shellard, *Physical Review D* **89**, 063008 (2014): mask-induced mode coupling and augmented basis requirements;
- Leung et al., *The Astrophysical Journal* **928**, 175 (2022), DOI `10.3847/1538-4357/ac562f`: two-dimensional transfer matrices are required when filtering, beam, and mask produce mode mixing;
- Ferreira & Quartin, *Physical Review D* **104**, 063503 (2021): realistic beam, noise, and masks must be propagated separately through Doppler/aberration estimators;
- Dai & Chluba, *Physical Review D* **89**, 123504 (2014): exact full-sky Doppler-weight-one nearest-neighbour boost kernels.

These sources motivate the architecture but do not validate this repository-specific response; the exact-head synthetic atlas provides that project-specific evidence.

## PHYS-MATH audit

`PASS_TASK7B_FORMULAS_AND_NUMERICAL_TABLES_WITH_TYPED_LIMITATIONS`

- dimensions, units, signs, source/retained registries, and metric whitening are consistent;
- full-sky normalization and condition agree with the exact irrep oracle;
- full-sky numerical high-ell blocks remain a replay-floor control, not physical leakage;
- cut-sky high-ell leakage is large and nearly contained in the registered response image;
- no model-free deterministic inverse is justified.

## PHYS-MATH-CODE audit

`PASS_TASK7B_EXECUTION / HOSTILE_VISUAL_FIGURE_AUDIT_PENDING`

- RED run failed only on the missing Task-7B module;
- GREEN smoke tests passed;
- CI_CORE tests, runner, manifest verification, artifact upload, and create-only artifact publication passed;
- the extended signed source path does not weaken the positive absolute-temperature finite-sky API;
- the authoritative simultaneous joint solver is reused;
- no raw Planck path is opened.

Five PNG figures are SHA-256 bound in the artifact branch. In the current ChatGPT runtime the downloaded binary ZIP could not be opened because the local Python/container surface returned a client error. Therefore the numeric tables and manifests are audited, but the external hostile visual inspection is explicitly deferred to the next frozen-head audit. This limitation does not change the no-candidate terminal.

## Disposition and next node

```text
TASK7B_SCIENTIFIC_CHARACTERIZATION_COMPLETE
NO_CUTSKY_CANDIDATE_IN_REGISTERED_FAMILY
TASK8_NOT_AUTHORIZED
```

Next:

```text
PMG-WU-011-TASK7C-AUGMENTED-SOURCE-BAND-CONVERGENCE-AND-NUISANCE-SPAN
```

Task-7C must extend the high-ell tail beyond `ell=9`, quantify the nuisance-image rank and overlap for fixed boost directions, and distinguish a model-free identified-set failure from a covariance-regularized statistical lane. Wide apodization is the primary baseline; reference and full-sky cases remain controls.

## Claim boundary

No admitted Planck absolute-temperature product, observed rank, empirical `beta`, boost subtraction, global matter-frame tilt, polarization result, foreground exclusion, Bianchi-family attribution, causal identification, or P01-P27 formal-dossier replay is introduced. PR #444 remains draft and unmerged.
