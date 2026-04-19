# Dossier — Bianchi V with tilt (open-curvature-driven shear)

**Appendix**: A13-10
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiV_tilt` (name `BV_tilt`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-10 |
| Model name            | Bianchi V with tilt (`BV_tilt`) |
| Structural class      | Bianchi type V (open, negatively-curved, tilted) — Σ² is derived from (β, Ω_k), not free |
| Dimensionality        | 2 free d.o.f. (β, Ω_k with Ω_k > 0 enforced) |
| Reference DOIs / arXiv | Maartens-Ellis 1995 (PRD 51, 5942); Ellis & van Elst 1998 |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Tilt rapidity | β | log-uniform | [10⁻⁸, 10⁻¹] |
| Curvature | Ω_k | Gaussian (clamped Ω_k > 0) | μ = 0.0007, σ = 0.0019; `Ok = max(Ok, 1e-6)` |
| Shear amplitude | Σ² | derived | `Sig2_BV(beta, Ok)` = analytic function of (β, Ω_k) |
| W², A² | — | δ-priors at 0 | — |

Matched-complexity: 2-d.o.f. bucket — direct competitor to BI_tilt with
a different coupling between shear and tilt (here derived, there free).

## 3. Kinematic signature

- Σ²(η) — derived from `Sig2_BV(β, Ω_k)`; decay mode.
- β(η) — free amplitude (log-uniform prior).
- Ω_k enters both background H(η) and the shear amplitude via Sig2_BV.
- W², A² ≡ 0.

This is one of only two models in the ladder (the other being BIII_tilt
partially) where Σ² is not independently sampled. The matched-complexity
enforcement remains at D_anisotropy = 2 because (β, Ω_k) are the
effective parameters.

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | D_2 shear + boost | *pending* |
| (c) | TE (via β) | nonzero |
| (d) | Bulk flow | nonzero |
| (e) | BAO (via Ω_k shift — informative) | **primary** — breaks β/Ω_k degeneracy |
| (f) | MES hard ceiling | active on Σ² |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | primary |

BV_tilt is the best candidate for a model that simultaneously touches
the tilt channel (d) and the curvature channel (e).

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BV_tilt | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline | *pending* | *pending* |
| S2 | + bulk-flow | *pending* | *pending* |
| S3 | full stack (+ BAO) | *pending* | *pending* (S3 is this model's native playground) |

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| β         | *pending* | — | — |
| Ω_k       | *pending* (Planck prior-dominated expected) | — | — |
| Σ² (derived) | *pending* | — | — |

## 7. Pitfalls / identifiability notes

- **Derived-parameter reporting**: Σ² marginal must be reconstructed
  from (β, Ω_k) posterior samples via `Sig2_BV`, not sampled directly;
  a Phase-H post-hoc step is needed.
- **Ω_k pushed to lower edge (1e-6)**: if the Planck prior dominates,
  the posterior will sit near the OK_PLANCK mean but any edge pile-up
  at 1e-6 flags data preference for flat / closed geometry —
  inconsistent with VIII's open requirement.
- **β × Ω_k degeneracy**: small-β / large-Ω_k can mimic large-β /
  small-Ω_k via Sig2_BV coupling; the BAO channel (e) is the primary
  breaker.

## 8. Reference figures

- F28 — (β, Ω_k) joint posterior
- F29 — derived Σ² marginal
- F30 — S3 BAO χ² profile

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BV_tilt` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
