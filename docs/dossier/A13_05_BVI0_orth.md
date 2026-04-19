# Dossier — Bianchi VI_0, orthogonal (hyperbolic plane-symmetric shear)

**Appendix**: A13-05
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiVI0_orth` (name `BVI0_orth`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-05 |
| Model name            | Bianchi VI_0, orthogonal (`BVI0_orth`) |
| Structural class      | Bianchi type VI₀ (plane-symmetric, hyperbolic-like shear; a₁ structure constant ≠ 0) |
| Dimensionality        | 2 free d.o.f. (Σ², a₁) |
| Reference DOIs / arXiv | Wainwright & Ellis §8.4; Collins-Hawking 1973 (MNRAS 162, 307) |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] |
| Structure constant | a₁ | log-uniform | [10⁻⁶, 1] |
| β, W², A² | — | δ-priors at 0 | — |

Matched-complexity: 2-d.o.f. bucket (see A13-04 §2).

## 3. Kinematic signature

- Σ²(η) — decay mode.
- a₁ sets the Class-B anisotropy parameter; a₁ → 0 recovers BI_orth
  (degenerate limit).
- Unlike BII, VI₀'s structure constants commute with themselves
  differently (Class B algebra), leaving a distinct higher-ℓ residual
  signature that is not captured by the R03a likelihood's D_ℓ-only
  channel.

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | D_2 / D_3 (via Σ²) | *pending* |
| (c) | TE | ~0 |
| (d) | Bulk flow | ~0 |
| (e) | BAO | *pending* |
| (f) | MES hard ceiling | active |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | *pending* |

Expected Occam penalty for the unresolved a₁ is identical to the BII n₁
case (§4 A13-04).

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BVI0_orth | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline (Planck 2018 Commander low-ℓ) | *pending* | *pending* |
| S2 | Planck + bulk-flow                       | *pending* | *pending* |
| S3 | full stack (+ BAO + lensing)             | *pending* | *pending* |

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| a₁        | *pending* (prior-dominated expected) | — | — |

## 7. Pitfalls / identifiability notes

- **a₁ invisibility at R03a order**: like n₁ in BII, a₁ only enters
  observations at higher multipole / full-sky BiPoSH level (W11-02).
- **Class A vs Class B confusion**: VI₀ (Class B) shares the ℓ ≤ 3
  signature with BI_orth (Class A) once a₁ is marginalised — the
  distinguishing fingerprint is at ℓ ≥ 4 which the leading-channel
  stack does not yet probe.
- **Prior-edge behaviour at Σ² → 10⁻³⁰**: posterior tail should fold
  smoothly; if A18 flags bimodality at the floor, re-run with wider
  prior support and check MES consistency.

## 8. Reference figures

- F14 — (Σ², a₁) joint posterior
- F15 — D_ℓ residual band vs BI_orth

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BVI0_orth` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
