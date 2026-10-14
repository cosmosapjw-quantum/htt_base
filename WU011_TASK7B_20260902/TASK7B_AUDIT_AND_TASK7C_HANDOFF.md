# PMG-WU-011 Task-7B audit and Task-7C handoff

## Current state

`PASS_TASK7B_ATLAS_NO_CANDIDATE / TASK7C_DESIGN_READY / TASK8_NOT_AUTHORIZED`

- Repository: `cosmosapjw-quantum/htt_base`
- Draft PR: `#444`
- Task-7B execution source: `13d40cb4d600e9e5687f27f506aa978c77cbcfb7`
- Task-7B audit head: `fbf89ad6cd34bc7278bc51c1185bd29f1acb120f`
- Task-7C design/plan head: `978fbe612a570b9973b17c51237965f16b630fc4`
- Artifact branch: `artifact/wu011-task7b-13d40cb4d600e9e5687f27f506aa978c77cbcfb7`
- Artifact ID: `9832711817`
- Artifact ZIP SHA-256: `e0d59195f4b0941b21beed5294a4e859c0aacdaf9e5c040b0168ae0447b7aff2`
- Atlas content ID: `sha256:fb1e31753212f4f4738a31ef949c2d480cae77de259b29bb2f7d98b22b44a98a`
- Manifest SHA-256: `6623d91262effe7b26946523976a568f624db5f54f6cd11dc038f418fcb6292e`
- Atlassian canonical Task-7B page: `24281089`
- Jira: `BASS-21`

## Exact conventions

`g_ab=(-,+,+,+)`, outward sky direction `n=-e`, active boost `+beta`, `beta=v/c`, thermodynamic-temperature Doppler weight `d=1`.

The exact full-sky source-sector metric Frobenius squares are

```text
8, 27, 91, 189, 125, 216
```

with total `656`, anisotropy rank `48`, structural physical-`T0` nullity `1`, and `kappa_+=sqrt(63/8)=2.806243040080...`.

## Registered result

| Case | condition | ell6 alias/neighbour | ell7..9 tail/neighbour | tail projection | candidate |
| --- | ---: | ---: | ---: | ---: | --- |
| full identity | 2.8063 | 0.00129 | 0.00385 | numerical-floor control | no: control |
| binary half sky | 8406.5 | 107.09 | 403.61 | 0.999987 | no |
| narrow apodization | 2550.5 | 58.10 | 156.25 | 0.999895 | no |
| reference identity | 496.97 | 21.57 | 38.09 | 0.998956 | no |
| wide identity | 32.21 | 2.516 | 5.279 | 0.961207 | no |
| reference matched transfer | 390.13 | 19.89 | 34.20 | 0.998511 | no |
| Task-7A reference transfer | 407.91 | 21.48 | 36.94 | 0.998655 | no |

Wide apodization improves the reference condition by `12.66x`, alias by `8.54x`, and tail by `7.00x`, but remains leakage dominated. Matching transfer improves only `5–8%`; mask/source-band coupling is the dominant failure.

## Workflow evidence

- RED run `#1 / 33593252618`: dependency setup passed; failed only because the Task-7B module was absent.
- Smoke run `#2 / 33593732148`: `6 passed in 6.01s`.
- CI_CORE run `#4 / 33593850011`: `6 passed in 11.72s`; runner, manifest verification, artifact upload, and create-only publication passed.
- Standard Task-7B source workflows PR04, PR07, WU011 processed boost, Task-7A, Task-7B, and Repository integrity all succeeded.

## Why no deterministic augmented inverse is allowed

Registered low source dimension: `48`.

Source `ell=7..9` nuisance dimension: `51`.

Stacked output dimension: `96`.

Therefore a naive augmented response has `99` source columns and nullity at least `3`. For fixed beta the retained output is only `32`-dimensional, so unrestricted high-ell nuisance may span the entire output.

## Next node

`PMG-WU-011-TASK7C-AUGMENTED-SOURCE-BAND-CONVERGENCE-AND-NUISANCE-SPAN`

Task-7C will:

1. extend source cutoffs to `L=9,12,16`;
2. use wide apodization as the primary cut-sky baseline;
3. compare full/reference controls and `nside=16/32`;
4. contract along six boost directions;
5. compute nuisance image rank and `P_K^perp J_beta`;
6. return identified-subspace, no-identified-subspace, or source-band-not-converged.

A covariance-aware likelihood is deferred until source-band convergence and deterministic survivor status are known.

## Open limitation

The exact binary artifact is retained in GitHub Actions/artifact branch and the active ChatGPT sandbox. The connected Dropbox writer accepts UTF-8 text only, so this Dropbox backup contains the authority, numerical result, digests, and handoff but not the ZIP/PNG bytes.

Hostile external visual inspection of the five PNG figures remains open because the current local image runtime failed. Numeric CSV/JSON and hash verification passed.

## Claim boundary

No admitted Planck absolute-temperature product, observed rank, empirical beta, boost subtraction, global matter-frame tilt, polarization result, foreground exclusion, Bianchi-family attribution, causal identification, or P01-P27 formal-dossier replay. PR #444 remains draft and unmerged.
