# HTT Six-paper P1/S01: stage-2 reproducible computation and claim gate

**Date:** 2026-10-16 KST. **Node:** S01, prereq E3 (previously completed_scoped). **Scope:** typed, source-independent, mathematically partial statistical functional API; no observational data and no physical likelihood.

## What was actually constructed

- `htt/obsstat/publication_functionals.py`: independently callable standard-Python data models `GaussProjection`, `shear_anchored_q`, `certified_sector_f`, `DepthContract`, `depth_contrast_g_f`, `PartialDraw`, `PartialMeasure`.
- Unlike existing HTT PR066 `PosteriorPushforwardSample`, this code requires explicit reasons for missing functional values and never divides observed mass by the total of defined draws. `G_F` has a registered floor, depth and common metadata. The strict `>` tail rule, the signed `Q` domain and a source-identity guard are tested. Existing PR066/MIO modules remain untouched.
- `tests/htt/test_publication_functionals_s01.py`: 16 isolated boundary, negative, randomized metamorphic and cross-threshold coupling tests. All are generated mathematical fixtures, no Planck or CF4 data.
- `scripts/run_htt_s01_demo.py`: deterministic same-ID three-draw example and `results/S01_NUMERIC_EXAMPLE.json`. The fixture's SHA256 identifies manufactured input only, not an observational release.

## Reproducible execution

```
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider tests/htt/test_publication_functionals_s01.py
PYTHONDONTWRITEBYTECODE=1 python scripts/run_htt_s01_demo.py --output results/S01_NUMERIC_EXAMPLE.json
```

On sandbox Python 3.13 with pytest 9.0.2: `16 passed in 0.08s` after correction of an immutable missing-reasons mapping type and addition of 3 tests. First run before these changes was 13 passed, not a failure. `py_compile` passed. Wolfram independent exact algebra: `G_F` log/rational identity residual `0`; shear normalizer check `3/8`; synthetic Gauss value `-11/10`.

`results/S01_NUMERIC_EXAMPLE.json` SHA256 `935a45d4d797cca60ae3895816957f9220521335b16650d5e0758482ff1dd41b`, fixture SHA `df2f9a6cc86e181a9b74afc061b0a74785434307137a80a545df45642cd05e1c`. Deterministic results: signed Q -0.8, Pi_Q(0.2) [0.3,0.8], Pi_Q(0.5) [0,0.5] with ties excluded, Pi_F(0.2) [0.3,1], G_F(0,.6; delta=.1)=6 up to floating error.

## Bound qualification / physical gate

For *unrestricted mathematical completion* of missing **events** per threshold, [known tail mass, known tail mass + missing mass] is sharp. For a restricted scalar range (especially admissible F in [0,1]) or a domain that is actually invalid, this interval is a conservative outer bound only and must not be relabeled sharp physical posterior. Ordered-threshold curves share missing draws, therefore an arbitrary Cartesian product of pointwise intervals is not attainable. Null, posterior adequacy, real sky/velocity selection and source-law inference remain **NOT_RUN**.

Manski, *Partial Identification of Probability Distributions* (2003), https://isipta03.sipta.org/charles.pdf, and *Partial identification with missing data: concepts and findings* (2005), https://www.sciencedirect.com/science/article/pii/S0888613X04001124, are primary prior art for set-valued missing-data identification. This is **not a novelty claim**; cosmology-specific source conditioning and real estimands belong to later S02–S04.

## Admission

`S01` is eligible for **completed_scoped** in the six-paper publication DAG when these exact files are preserved and read back; allowed claim `MATHEMATICAL_DERIVATION + IMPLEMENTATION_VERIFIED_ISOLATED_SANDBOX`. No source-bound astrophysical probability or `S02` execution is implied. `main`, the pre-existing PR stack and the 245-card code-development backlog must remain unchanged. Native subagent and byte-exact full-repository test: `NOT_RUN`; remote Desktop Commander unavailable (monthly quota), not a scientific failure. All six journal submission gates remain `NOT_READY_TO_SUBMIT`.