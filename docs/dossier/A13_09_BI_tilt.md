# Dossier — Bianchi I with tilt (shear + boost)

**Appendix**: A13-09
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiI_tilt` (name `BI_tilt`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-09 |
| Model name            | Bianchi I with tilt (`BI_tilt`) |
| Structural class      | Bianchi type I with tilted congruence (shear + boost, no vorticity) |
| Dimensionality        | 2 free d.o.f. (Σ², β) |
| Reference DOIs / arXiv | King & Ellis 1973; Maartens-Ellis 1995 (PRD 51, 5942); Jaffe+2005 |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] |
| Tilt rapidity | β | log-uniform | [10⁻⁸, 10⁻¹] |
| W², A² | — | δ-priors at 0 | — |

Matched-complexity: 2-d.o.f. bucket. Direct evidence competitors:
BVIIh_orth, BII_orth, BVI0_orth, BVIII_orth, BIX_orth at same D.

## 3. Kinematic signature

- Σ²(η) — decay mode.
- β(η) — treated as z-independent amplitude at leading order; W_R window
  dynamics (W12-01) refines this for S3.
- ε₁ = eps1_from_beta(β) couples β to the Ellis-Bruni ε₁ invariant.
- Both shear (`shear_to_D2(Sig2,"decay")`) and boost (`boost_to_D2(beta)`)
  channels fire.

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` (fiducial Σ² = 10⁻⁸, β = 10⁻³) |
|---|---|---|
| (b) | D_2 shear + D_2 boost | primary discriminator |
| (c) | TE dipole response (via β) | nonzero, weak |
| (d) | Bulk flow | nonzero — tilt sources a peculiar velocity monopole |
| (e) | BAO | ~0 |
| (f) | MES hard ceiling | active |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | primary |

W14-01 (3-signature separator) expects BI_tilt to appear in both TT and
EE (shear) AND to couple bulk flow (channel d) via the β component.

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BI_tilt | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline | *pending* | *pending* |
| S2 | + bulk-flow | *pending* | *pending* (best-case: β resolves distinct from Σ²) |
| S3 | full stack | *pending* | *pending* |

Target (v3 §11.14): S2 should resolve the β-Σ² degeneracy via the bulk
flow channel; the Route B anchor `ln B ≈ +26.4` is the FLRW_tilt target
— BI_tilt at matched (β, Σ²) should fall within ±1σ of that.

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| β         | *pending* | — | — |

## 7. Pitfalls / identifiability notes

- **Σ² ↔ β degeneracy at S1**: without bulk flow, (Σ², β) span a
  banana-shaped likelihood along `D_2^shear + D_2^boost = const`.
  Break via S2 (bulk flow) — COMMON-D selection-aware likelihood.
- **β lower-prior edge behavior**: posterior piling up at β ≈ 10⁻⁸
  signals β is undetected; the 7-decade log-prior imposes an Occam
  penalty that pushes ln B toward the pure-shear BI_orth unless β has
  positive support.
- **MES compound constraint**: both Σ² and ε₁(β) must satisfy `_mes_ok`;
  the coupled ceiling removes some high-(Σ², β) corners of the prior.
- **ZoA contamination**: a diagnostic axis (HTT-P0-AJ gate) must not
  feed the tilt posterior; `directional_models` isolates the preferred
  axis cleanly.

## 8. Reference figures

- F25 — (Σ², β) joint posterior with MES ceiling contour
- F26 — 3-signature decomposition (TT + EE + bulk flow)
- F27 — channel contribution bar

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BI_tilt` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
