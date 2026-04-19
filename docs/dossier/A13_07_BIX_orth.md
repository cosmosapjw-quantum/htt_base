# Dossier — Bianchi IX, orthogonal (closed-universe shear)

**Appendix**: A13-07
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiIX_orth` (name `BIX_orth`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-07 |
| Model name            | Bianchi IX, orthogonal (`BIX_orth`) |
| Structural class      | Bianchi type IX (SU(2) Lie algebra, closed spatial sections, Ω_k < 0) |
| Reference DOIs / arXiv | Misner 1969 (PRL 22, 1071 — Mixmaster); Jaffe+2005; Pontzen & Challinor 2007 |
| Dimensionality        | 2 free d.o.f. (Σ², Ω_k with Ω_k < 0 branch enforced) |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] |
| Curvature | Ω_k | folded Gaussian, enforced negative | `Ok = -abs(_gauss(u[1], OK_PLANCK, OK_SIGMA))`; if Ok ≥ 0 ⇒ Ok = −1e−6 |
| β, W², A² | — | δ-priors at 0 | — |

Matched-complexity: 2-d.o.f. bucket.

## 3. Kinematic signature

- Σ²(η) — decay mode.
- Closed geometry (Ω_k < 0) bounds the spatial volume; at late times the
  shear mode amplitude saturates rather than decaying monotonically.
- Mixmaster chaos (Misner 1969) is suppressed when the MES hard ceiling
  is enforced — Σ² ≪ 10⁻⁴ keeps evolution linear.

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | D_2 / D_3 (via Σ²) | *pending* |
| (c) | TE | ~0 |
| (d) | Bulk flow | ~0 |
| (e) | BAO (opposite-sign Ω_k vs BVIII) | weak but nonzero |
| (f) | MES hard ceiling | active |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | *pending* |

The paired S3 evidence vs BVIII_orth isolates the sign-of-curvature
discrimination from the Σ² amplitude — a dedicated model-ladder
diagnostic.

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BIX_orth | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline (Planck 2018 Commander low-ℓ) | *pending* | *pending* |
| S2 | Planck + bulk-flow                       | *pending* | *pending* |
| S3 | full stack (+ BAO + lensing)             | *pending* | *pending* |

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| Ω_k       | *pending* (expected to pile up near 0 from the Planck prior) | — | — |

## 7. Pitfalls / identifiability notes

- **Ω_k = 0 prior-edge pile-up**: the folded Gaussian places most prior
  weight near 0 — the posterior will look "prior-edge" even when the
  data are consistent with closed geometry. Use A18 posterior predictive
  p-value rather than marginal credible intervals.
- **Mixmaster chaos regime is out-of-support**: MES hard ceiling clips
  Σ² well below the chaos threshold; any edge-hitting posterior flags
  model-data mismatch, not a physical detection.
- **BIX vs BVIII is not a simple sign flip**: the SL(2,ℝ) / SU(2)
  Lie-algebra structures differ in sub-leading topology but coincide
  at the R03a D_ℓ-channel observable level — expected Δ ln B ≈ 0 at
  matched |Ω_k|.

## 8. Reference figures

- F19 — (Σ², Ω_k) joint posterior
- F20 — BIX vs BVIII Ω_k-branch comparison
- F21 — D_ℓ residual band

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BIX_orth` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
