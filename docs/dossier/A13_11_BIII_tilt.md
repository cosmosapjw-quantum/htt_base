# Dossier — Bianchi III with tilt (LRS hyperbolic shear + tilt)

**Appendix**: A13-11
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiIII_tilt` (name `BIII_tilt`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-11 |
| Model name            | Bianchi III with tilt (`BIII_tilt`) |
| Structural class      | Bianchi type III (LRS, hyperbolic-like) with tilt; open (Ω_k > 0) |
| Dimensionality        | 3 free d.o.f. (Σ², β, Ω_k>0) |
| Reference DOIs / arXiv | Ellis & MacCallum 1969 (Comm. Math. Phys. 12, 108); Maartens-Ellis 1995 |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] |
| Tilt rapidity | β | log-uniform | [10⁻⁸, 10⁻¹] |
| Curvature | Ω_k | Gaussian, clamped Ω_k > 0 | μ = 0.0007, σ = 0.0019; `Ok = max(Ok, 1e-6)` |
| W², A² | — | δ-priors at 0 | — |

Matched-complexity: 3-d.o.f. bucket. Direct competitor: BIX_tilt
(closed analogue) at the same dimensionality.

## 3. Kinematic signature

- Σ²(η) — decay mode.
- β(η) — log-uniform prior amplitude.
- Ω_k enters the background and modifies the sound horizon.
- BIII is LRS (locally rotationally symmetric) — one axis is
  privileged; the Σ² eigenframe aligns with this symmetry axis.

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | D_2 shear + boost | *pending* |
| (c) | TE (via β) | nonzero |
| (d) | Bulk flow (via β) | nonzero |
| (e) | BAO (via Ω_k) | informative (Planck prior-dominated) |
| (f) | MES hard ceiling | active on Σ² |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | primary |

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BIII_tilt | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline | *pending* | *pending* |
| S2 | + bulk-flow | *pending* | *pending* |
| S3 | full stack (+ BAO) | *pending* | *pending* |

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| β         | *pending* | — | — |
| Ω_k       | *pending* | — | — |

## 7. Pitfalls / identifiability notes

- **3-parameter banana at S1**: without informative channels (d) and
  (e) the (Σ², β, Ω_k) posterior spans a 3D ribbon. All three
  scenarios (S1, S2, S3) needed for full breaking.
- **Ω_k prior pile-up at clamp edge (1e-6)**: flags data preference
  for flat geometry; inconsistent with BIII's open requirement — flag
  in A18 as a model-data mismatch.
- **LRS symmetry axis**: any A18 residual aligned with `directional_models`
  recovered preferred axis is a genuine positive signal; misalignment
  flags a ZoA contamination (HTT-P0-AJ gate).

## 8. Reference figures

- F31 — 3D corner (Σ², β, Ω_k)
- F32 — LRS axis residual pattern
- F33 — S1/S2/S3 ln B comparison

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BIII_tilt` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
