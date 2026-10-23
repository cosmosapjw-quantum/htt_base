# Observed PR4 30 GHz Q/U split comparison — 2026-10-22

**Status:** `SOURCE_CONDITIONAL_DESCRIPTIVE_SPLIT_COMPARISON`, C0 non-claim-bearing. Owner: HTT observational research intake. This is one observed A/B map comparison on an explicitly chosen support, not a null or noise result. Transfer source: none. Requested coding runtime: `gpt-6-sol/high`; observed runtime identity: `UNKNOWN`. The [separate Astra review](INDEPENDENT_REVIEW.md) closed with **SCOPED_PASS_C0** after the targeted test repair. The original 17/42 state and F06/L03 HOLD are unchanged.

## Inputs and method

Base checkout: branch `research/htt-open-input-theory-20261018`, HEAD `d2c11c4a850fadbf1cf181c190c3c30f48425ff3`, clean before this unit. [Source intake](../data/pr4/INTAKE.md) and [validation](../data/pr4/VALIDATION.json), SHA-256 `10e6475aa970d0224fbe27f6561e9afec0901d4fdaf730cf25e4ed20b842ba60`, independently verified the cached source bytes and receipts at the base. This run checked each current file's size and corresponding receipt digest against that validation; it did not rehash the ~1 GB map payloads.

| Input | SHA-256 from verified intake | Geometry, unit |
|---|---|---|
| IRSA PR4 R4.00 30 GHz `year-1-3` A map | `7dc8414835f5041ad51373505e15a17f3fb286fac1f41a48e72f09f46aa901b0` | NSIDE1024 NESTED Galactic COSMO, Q/U `K_CMB` |
| IRSA PR4 R4.00 30 GHz `year-2-4` B map | `b7de3e4fbafb2553db26d2c24b5d91f68dd42b86135e989c25d095a63e611c8f` | Same |
| NERSC PR4 LoLLiPoP binary mask | `7d7df63e77066a7739cc7faed3a005593bb3612af6cdeea2ed48a37fb600946d` | NSIDE16 RING Galactic; 1,273 ones |

For each NESTED parent `p`, its RING mask value is `mask_ring[nest2ring(16,p)]`. A parent with value exactly one selects the contiguous NSIDE1024 NESTED children `[4096p,4096(p+1))`; zero excludes them. Thus 1,273/3,072 equal-area parents and 5,214,208/12,582,912 native pixels are selected: 41.4388020833% of the sky, 17,094.733 square degrees. Each selected parent maps to four FITS vector rows of 1,024 float32 values. These Q/U values are converted to float64 for native-pixel algebra and sums. All selected A/B Q/U values passed finiteness checks. There is no Q/U smoothing, interpolation, direct RING/NESTED addition, beam inversion, or spectrum-window-as-map-operator step.

At every native pixel, `P=(Q,U)`, `S=(P_A+P_B)/2`, `D=(P_A-P_B)/2`. The powers below are equal-area means of `Q²+U²` or `A·B` over the 5,214,208 selected native pixels. The scalar figure shows **sqrt(mean over the native children of |D|²)** for each selected NSIDE16 parent. It is not a regridded polarization vector. The binary-mask threshold and means are choices for this descriptive comparison; mask/statistic compatibility is uncalibrated.

## Numerical result

| Quantity | `K_CMB²` | `microK_CMB²` |
|---|---:|---:|
| mean `|S|²` | 1.0124469731240014e-8 | 10,124.469731240013 |
| mean `|D|²` | 1.0045456339316961e-8 | 10,045.456339316961 |
| mean `|A|²` | 2.0291746077493402e-8 | 20,291.7460774934 |
| mean `|B|²` | 2.0048106063620548e-8 | 20,048.106063620548 |
| mean `A·B` | 7.901339192305173e-11 | 79.01339192305173 |

`mean |D|² / mean |S|² = 0.9921957994817991`, evaluated only because the denominator is positive. This is an observed split-disagreement ratio. Differential sky, foreground, processing and instrument response may contribute; the result is not a pure-noise estimate, significance, isolated CMB polarization, or Bianchi detection.

The identities use `P_S+P_D=(P_A+P_B)/2` and `P_S-P_D=<A,B>` for equal-area means of squared amplitudes. Actual-data residuals are 0 and `6.333101564859118e-25 K_CMB²`; the latter is `8.01522553420646e-15` on the guarded relative scale. A common COSMO-basis rotation by `psi=0.371` rad, `Q'=cos(2psi)Q+sin(2psi)U`, `U'=-sin(2psi)Q+cos(2psi)U`, left all five scalar quantities invariant to a largest absolute residual `3.308722450212111e-24 K_CMB²` and largest guarded relative residual `8.01522553420646e-15` across the identity set. The criterion is `|residual|/max(|lhs|,|rhs|,1e-18 K_CMB²) <= 1e-10`; `1e-18 K_CMB²` corresponds to `1e-6 microK_CMB²` and only guards the relative denominator. Every check passed without changing this tolerance. The scalar parent RMS spans 36.2066–145.8406 `microK_CMB`; its equal-area parent mean is 98.7680 and median 103.3238 `microK_CMB`. These parent summaries are distinct from the native-pixel power means.

## Reproduction, validation, and first failure

Run from the repository root with the existing `.venv`; each command used `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`:

```bash
.venv/bin/python -m pytest -q docs/research_program/observational_publication_20261015/RESEARCH_LOOP_20261022/pr4_comparison/test_pr4_split.py
.venv/bin/python docs/research_program/observational_publication_20261015/RESEARCH_LOOP_20261022/pr4_comparison/pr4_split.py --write-artifacts
```

Final results: focused tests **4 passed**, exit 0; actual-data/figure command exit 0. Versions: Python 3.12.3, NumPy 2.5.4, Astropy 8.0.2, healpy 1.19.0, Matplotlib 3.11.2, pytest 9.1.1. The tests expose a wrong direct RING/NESTED mask, exact nested child lifting, float64 split identities and rotation, nonfinite rejection, positive-ratio domain, and native counts. Full-data validation was performed in the same bounded pass as the comparison. The first generated two-panel figure had overlapping axes; after a plot-layout repair, a single-panel figure had a caption/colorbar overlap. Both were presentation failures, not numerical failures; the final single-panel layout was visually inspected. The actual-data command was repeated only to regenerate the corrected figure. All numerical values were unchanged across those runs.

Independent review found one nonblocking test weakness: the manufactured parallelogram assertion at line 43 used NumPy's default absolute tolerance `1e-8 K_CMB²`, comparable to the fixture powers. The targeted repair set `atol=0.0` while retaining `rtol=1e-14`; the adjacent cross assertion already had explicit `atol=1e-26 K_CMB²`. Targeted closeout command used the same thread limits with `PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`: **4 passed**, exit 0. No actual map pass or plot regeneration was performed for this test-only repair; RESULT and plot hashes below are unchanged.

Generated files and final SHA-256:

| Artifact | SHA-256 |
|---|---|
| [Consumer](pr4_split.py) | `706ee20d64ac04cc7a5df13f5fe9605686b55403de7c0ebb8cf14fa3cd73fb83` |
| [Tests](test_pr4_split.py) | `f90131251fbbc1b7cd1f3182c345e293626cea184dc2e4cfb3b295a082383161` |
| [Result](RESULT.json) | `159b0721ff33114bbd4ef33dcc3be3ad815c292360d9146d50b5ae7492589541` |
| [PNG](D_RMS_NS16.png) | `5dbee56651e0057b69796e96b52566d846d0486529995741e6c5c2d497542efe` |
| [PDF](D_RMS_NS16.pdf) | `6babb9767f9acec2d1bc6d629b02e50cb1bc0b2cd271052c82c7a69ac4101d20` |
| [Plot receipt](PLOT_RECEIPT.json) | `bf71c4abe625e25c9a50ba3d851637fd826fbc58fe970c504e14c0a2e228babc` |

No raw 12.6-million-pixel arrays were added to Git. The input files remain in the external cache and are referenced by exact intake identities. Independent review is complete within the descriptive scope. Any stronger F06/L03 use still needs a source-qualified matched processed-total/foreground map operator, applicable mask/beam/weight treatment, and a statistic-specific joint null law with coverage; the exact A/B spectrum windows alone do not supply these. A physical Bianchi/global-history polarized transfer remains a distinct missing input.
