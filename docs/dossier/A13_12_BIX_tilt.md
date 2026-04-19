# Dossier — Bianchi IX with tilt (closed-universe tilted shear)

**Appendix**: A13-12
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiIX_tilt` (name `BIX_tilt`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-12 |
| Model name            | Bianchi IX with tilt (`BIX_tilt`) |
| Structural class      | Bianchi type IX (closed, SU(2) algebra) with tilt |
| Dimensionality        | 3 free d.o.f. (Σ², β, Ω_k<0) |
| Reference DOIs / arXiv | Misner 1969 (PRL 22, 1071); Pontzen & Challinor 2007 |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] |
| Tilt rapidity | β | log-uniform | [10⁻⁸, 10⁻¹] |
| Curvature | Ω_k | folded Gaussian, enforced negative | `Ok = -abs(_gauss)`; if Ok ≥ 0 ⇒ Ok = −1e−6 |
| W², A² | — | δ-priors at 0 | — |

Matched-complexity: 3-d.o.f. bucket. Direct analogue: BIII_tilt (open).

## 3. Kinematic signature

- Σ²(η) — decay mode.
- β(η) — log-uniform prior.
- Ω_k < 0 enforces closed geometry; the SU(2) algebra is the structural
  Lie group.
- Mixmaster chaos suppressed by MES ceiling (as in BIX_orth).

## 4. Distinguishing channels

Identical channel pattern to BIII_tilt but with opposite-sign Ω_k
branch. The BAO channel (e) provides the primary sign-of-curvature
discrimination.

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | D_2 shear + boost | *pending* |
| (c) | TE (via β) | nonzero |
| (d) | Bulk flow | nonzero |
| (e) | BAO (via Ω_k, opposite sign) | informative |
| (f) | MES hard ceiling | active |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | primary |

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BIX_tilt | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline | *pending* | *pending* |
| S2 | + bulk-flow | *pending* | *pending* |
| S3 | full stack | *pending* | *pending* |

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| β         | *pending* | — | — |
| Ω_k       | *pending* (negative branch) | — | — |

## 7. Pitfalls / identifiability notes

- **Ω_k = 0 pile-up at clamp edge (−1e-6)**: folded Gaussian places
  most prior mass near zero; posterior-mode near 0 is expected under
  the null, not a sign-of-closure detection.
- **Joint (Σ², β, Ω_k) volume**: the 3D prior volume × 26-decade Σ²
  × 7-decade β × Planck-wide Ω_k totals ~180 (log-scale); the Occam
  penalty is severe and requires 3σ+ positive detection to overcome.
- **Mixmaster chaos**: as in BIX_orth, the MES ceiling keeps the
  evolution linear; any posterior above Σ² ~ 10⁻⁴ is edge-hitting,
  not physical.

## 8. Reference figures

- F34 — 3D corner (Σ², β, Ω_k)
- F35 — BIX_tilt vs BIII_tilt Ω_k-branch comparison
- F36 — D_ℓ residual band

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BIX_tilt` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
