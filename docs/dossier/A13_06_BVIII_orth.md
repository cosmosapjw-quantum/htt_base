# Dossier — Bianchi VIII, orthogonal (open-universe shear)

**Appendix**: A13-06
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiVIII_orth` (name `BVIII_orth`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-06 |
| Model name            | Bianchi VIII, orthogonal (`BVIII_orth`) |
| Structural class      | Bianchi type VIII (SL(2,ℝ) Lie algebra, open-sectional-curvature cosmology) |
| Dimensionality        | 2 free d.o.f. (Σ², Ω_k with Ω_k > 0 branch) |
| Reference DOIs / arXiv | Lukash 1976 (NPhB 118, 91); Jaffe+2005 (astro-ph/0503213) |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] |
| Curvature | Ω_k | Gaussian | μ = 0.0007 (OK_PLANCK), σ = 0.0019 (OK_SIGMA) (code uses unclamped `_gauss`) |
| β, W², A² | — | δ-priors at 0 | — |

Matched-complexity: 2-d.o.f. bucket. Note: the code's
`BianchiVIII_orth.prior_transform` does NOT enforce Ω_k > 0 (unlike
BIX which clamps negative); this is a known approximation — VIII
strictly requires open geometry (Ω_k > 0), and Phase-H posteriors
should verify the Gaussian-drawn samples stay on the physical branch
at > 3σ confidence level (OK_PLANCK is ~ 0.4σ from 0).

## 3. Kinematic signature

- Σ²(η) — decay mode.
- Curvature modifies the background H(η); Ω_k > 0 induces additional
  late-time shear growth of mild amplitude.
- Negligible whirl signature at VIII's SL(2,ℝ) structure.

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | D_2 / D_3 (via Σ²) | *pending* |
| (c) | TE | ~0 |
| (d) | Bulk flow | ~0 |
| (e) | BAO (via Ω_k shift) | weak but nonzero |
| (f) | MES hard ceiling | active |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | *pending* |

Channel (e) BAO acquires mild sensitivity to Ω_k via the sound-horizon
calibration; opposite sign to BIX_orth (closed) at matched |Ω_k|.

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BVIII_orth | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline (Planck 2018 Commander low-ℓ) | *pending* | *pending* |
| S2 | Planck + bulk-flow                       | *pending* | *pending* |
| S3 | full stack (+ BAO + lensing)             | *pending* | *pending* |

S3 Bayes factor is the most diagnostic because the Ω_k prior is
informative and the BAO channel breaks the Σ² ↔ Ω_k degeneracy.

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| Ω_k       | *pending* (should track Planck 2018 Ω_k = 0.0007 ± 0.0019) | — | — |

## 7. Pitfalls / identifiability notes

- **Ω_k sign enforcement not implemented in code**: verify the Phase-H
  posterior does not drift into Ω_k < 0 samples (unphysical for VIII).
  Fix-forward: add `Ok = max(Ok, 1e-6)` in `prior_transform` mirroring
  BV_tilt / BIII_tilt.
- **Weak Σ² / Ω_k degeneracy**: the sound-horizon shift from Ω_k and
  the D_ℓ residual from Σ² partly counter each other; S3 disentangles
  this by adding BAO-independent channel (h).
- **Prior-edge Ω_k**: posterior-mean Ω_k pushed to 0 (or < 0) signals
  that the data prefer a closed / flat solution; no action required
  but flag in A18.

## 8. Reference figures

- F16 — (Σ², Ω_k) joint posterior
- F17 — BAO χ² contribution vs Ω_k
- F18 — D_ℓ residual band

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BVIII_orth` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
