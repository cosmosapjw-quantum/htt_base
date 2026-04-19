# Dossier — Bianchi VII_0, orthogonal (whirl-free type I limit)

**Appendix**: A13-03
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiVII0_orth` (name `BVII0_orth`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-03 |
| Model name            | Bianchi VII_0, orthogonal (`BVII0_orth`) |
| Structural class      | Bianchi type VII₀ (flat spatial sections, whirl-parameter h=0 limit; kinematically reduces to type-I shear in the `_bianchi_type='I'` registry entry) |
| Dimensionality        | 1 free anisotropy d.o.f. (Σ²) |
| Reference DOIs / arXiv | Barrow, Juszkiewicz & Sonoda 1985 (MNRAS 213, 917); Jaffe+2005 (astro-ph/0503213) |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] (`_logu(u[0], 1e-30, 1e-4)`) |
| Tilt β | — | δ-prior at 0 | — |
| Vorticity W² | — | δ-prior at 0 | — |
| Four-acceleration A² | — | δ-prior at 0 | — |
| Whirl parameter h | — | δ-prior at 0 (VII_0 limit) | — |

Matched-complexity note: h = 0 identifies VII_0 with type I at the
observable level; the separate dossier exists to track the prior
volume and ruling-out argument cleanly.

## 3. Kinematic signature

- Σ²(η) — decay mode, identical to BI_orth (§3).
- W²(η) ≡ 0.
- β(η) ≡ 0.
- Spiral signature (characteristic of VII_h, h > 0) is absent at h = 0;
  any residual pattern is pure type-I shear.

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | TT anomalies (D2, D3) | *pending* (should match BI_orth) |
| (c) | TE response | ~0 |
| (d) | Bulk flow | ~0 |
| (e) | BAO / sound-horizon | *pending* |
| (f) | MES hard ceiling | active |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | *pending* |

Expected ln B vs BI_orth: 0 within numerical noise (the two models have
identical likelihoods up to the implicit h→0 limit).

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BVII0_orth | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline (Planck 2018 Commander low-ℓ) | *pending* | *pending* |
| S2 | Planck + bulk-flow                       | *pending* | *pending* |
| S3 | full stack (+ BAO + lensing)             | *pending* | *pending* |

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |

## 7. Pitfalls / identifiability notes

- **Degeneracy with BI_orth**: VII_0 is the h → 0 limit of VII_h; at
  the evidence level the two are indistinguishable. Keep the dossier
  separate for model-ladder completeness but fold any A18 posterior
  predictive p-value comparison against BI_orth into a single ranking
  tie-breaker (see T48 channel-contribution table).
- **Prior-volume penalty**: identical to BI_orth (§7).

## 8. Reference figures

- F09 — BVII0_orth Σ² posterior overlay vs BI_orth (should coincide)
- F10 — D_ℓ residual band

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BVII0_orth` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
