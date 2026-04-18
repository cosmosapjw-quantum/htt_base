# Dossier — FLRW (null baseline)

**Appendix**: A13-00
**Status**: example / template calibration; null reference against which every
other dossier's ln B is reported. Posterior fields placeholder pending Phase H.
**Upstream**: BASS_PY_HTT_TSC_RESEARCH_PLAN.md §11.10.1 / DOS-A13

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-00 |
| Model name            | FLRW (spatially flat Λ + CDM) |
| Structural class      | FLRW |
| Dimensionality        | 0 physical anisotropy d.o.f.; background ΛCDM only |
| Reference DOIs / arXiv | Planck 2018 VI (arXiv:1807.06209) |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Hubble today | `h` | δ-prior | `h = 0.6736` (Planck 2018 VI fiducial) |
| Matter density | `Ω_m` | δ-prior | 0.3153 |
| Radiation density | `Ω_r` | δ-prior | 9.15 × 10⁻⁵ |
| Cosmological constant | `Ω_Λ` | δ-prior | 0.6847 |

Matched-complexity note: FLRW is the reference; all anisotropy parameters
(β, Σ², W², A², (l, b)) are enforced as δ-priors at zero to keep the
effective dimension equal to the tilted/anisotropic competitors (A15).

## 3. Kinematic signature

- Σ²(η) ≡ 0
- W²(η) ≡ 0
- β(η) ≡ 0
- Θ(η) = 3H(η), w_eff from ΛCDM.

## 4. Distinguishing channels

No anisotropic contribution to any channel. Expected `Δ ln B` against any
Bianchi/tilted competitor is the *negative* of the competitor's channel
stack — i.e., FLRW is the subtracted zero point.

| Channel | Expected `Δ ln B` |
|---|---|
| (b) | 0 (reference) |
| (c) | 0 |
| (d) | 0 |
| (e) | 0 |
| (f) | 0 |
| (g) | 0 |
| (h) | 0 |

## 5. Scenario-dependent Bayes factors

FLRW serves as the ln B denominator, so `ln B_{FLRW vs FLRW} = 0` in all
scenarios (S1/S2/S3). The table below is for bookkeeping symmetry with
non-null dossiers.

| Scenario | ln Z_FLRW | ln B_{FLRW vs FLRW} |
|---|---|---|
| S1 | *pending* | 0 |
| S2 | *pending* | 0 |
| S3 | *pending* | 0 |

## 6. Posterior summary

Not applicable — no free anisotropy parameters. ΛCDM parameters inherit
Planck 2018 VI posteriors and are not re-sampled in this pipeline.

## 7. Pitfalls / identifiability notes

- FLRW is exactly identifiable — but it is also the easiest target for
  model-misspecification bias: if the truth is a small-β tilted FLRW,
  fitting FLRW will appear "preferred" by LOOCV when the data is too
  noisy to resolve the anisotropy. A17 (LOOCV) and A18 (posterior
  predictive p-value) must both be consulted before declaring a null.

## 8. Reference figures

- F01 — Planck D_ℓ best-fit band (reference overlay)
- F02 — residual band after subtracting FLRW mean

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_FLRW_baseline` |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
