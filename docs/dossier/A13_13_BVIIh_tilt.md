# Dossier — Bianchi VII_h with tilt (maximal-signature model; grow/dec pair)

**Appendix**: A13-13
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiVIIh_tilt` (name `BVIIh_tilt`) and
`BianchiVIIh_tilt_grow` (alternate `_shear_mode='grow'` variant).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-13 |
| Model name            | Bianchi VII_h with tilt (`BVIIh_tilt`) + grow-mode variant (`BVIIh_tilt_grow`) |
| Structural class      | Bianchi type VII_h with tilt; all four Ellis-Bruni scalars (Σ², W², β, ε₁) active — the "maximal model" |
| Dimensionality        | 4 free d.o.f. (Σ², W², β, x_h) |
| Reference DOIs / arXiv | Jaffe+2005 (astro-ph/0503213); Pontzen & Challinor 2007 (MNRAS 380, 1387); Saadeh+2016 |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] (decay); [10⁻²⁰, 10⁻⁴] (grow variant) |
| Vorticity | W² | log-uniform | [10⁻²⁴, 10⁻¹⁰] (note: free, unlike BVIIh_orth where W² is derived) |
| Tilt rapidity | β | log-uniform | [10⁻⁸, 10⁻¹] |
| Whirl parameter | x_h | log-uniform | [10⁻³, 10³] |
| A² | — | δ-prior at 0 | — |

Matched-complexity: 4-d.o.f. bucket. This is the top of the ladder —
no single-model direct competitor at the same dimensionality. Occam
penalty is largest here; requires strong positive signal to rank.

## 3. Kinematic signature

- Σ²(η) — decay mode (`BVIIh_tilt`) or grow mode (`BVIIh_tilt_grow`).
- W²(η) — free, log-uniform; decouples from Σ² (unlike BVIIh_orth where
  W² = R_WS_VIIH² × Σ²).
- β(η) — independent tilt amplitude.
- x_h — whirl parameter; sets the CMB spiral signature.
- All three Ellis-Bruni kinematic scalars (Σ², W², ε₁) nonzero.
- ω_H = `omH_from_W2(W2)`.

### BVIIh_tilt_grow variant

Shifted Σ² prior lower edge (10⁻²⁰ vs 10⁻³⁰) reflects the grow mode's
late-time amplification; at late times Σ² grows rather than decays.
Separate `ALL_MODELS` entry; covered as sibling in this dossier.

## 4. Distinguishing channels

Every channel fires — BVIIh_tilt is the most informative model on
paper.

| Channel | Physics | Expected `Δ ln B` (fiducial) |
|---|---|---|
| (b) | D_2 shear + boost + whirl D_ℓ | primary |
| (c) | TE (via β) | nonzero |
| (d) | Bulk flow (via β) | nonzero |
| (e) | BAO | weak |
| (f) | MES hard ceiling | active on all of (Σ², β) |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | primary |

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BVIIh_tilt | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline | *pending* | *pending* |
| S2 | + bulk-flow | *pending* | *pending* |
| S3 | full stack | *pending* | *pending* |

| Scenario | BVIIh_tilt_grow ln Z | grow Δ ln B vs decay |
|---|---|---|
| S1 | *pending* | *pending* |
| S2 | *pending* | *pending* |
| S3 | *pending* | *pending* |

Historical context: Jaffe+2005 reported evidence for BVIIh_tilt with
Σ ~ 2×10⁻¹⁰ and tilt aligned near (ℓ, b) ≈ (222°, −62°). Saadeh+2016
and Planck 2018 VII ruled this out at > 3σ confidence on full-sky
Planck data. Our Phase-H posterior must report both ln B and PPC
p-value to determine whether any residual support is prior-volume
artefact or genuine data preference.

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| W²        | *pending* | — | — |
| β         | *pending* | — | — |
| x_h       | *pending* (historic Jaffe-peak near x_h ≈ 0.62 should appear only under injection tests) | — | — |

## 7. Pitfalls / identifiability notes

- **4-parameter prior-volume penalty**: with Σ² × W² × β × x_h the
  prior volume dwarfs any plausible posterior — ln B is the net of
  likelihood gain minus this Occam floor. A18 PPC p-value is the
  correct sanity check when ln B is marginal.
- **W² ↔ Σ² correlation**: unlike BVIIh_orth where W² is tied to Σ²
  via R_WS_VIIH, here the two are independent. Phase-H corner must
  verify they don't lock to the fixed ratio by accident (which would
  signal prior-leak from the _orth sibling).
- **Jaffe-peak prior artefact**: the x_h prior range [10⁻³, 10³]
  includes the historic Jaffe best-fit; A17 Occam decomposition must
  quantify the prior-support contribution before claiming any
  "residual preference".
- **Grow / decay branch separation**: `BVIIh_tilt` and
  `BVIIh_tilt_grow` are separate ALL_MODELS entries and must NOT be
  marginalised together.
- **ZoA contamination**: HTT-P0-AJ gate must enforce
  `production_allowed=True` on the preferred axis feeding the β
  posterior.

## 8. Reference figures

- F37 — 4D corner (Σ², W², β, x_h)
- F38 — Jaffe-region overlay on (Σ², x_h) slice
- F39 — BVIIh_tilt vs BVIIh_tilt_grow ln Z comparison
- F40 — PPC χ²/ndof per scenario

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BVIIh_tilt`, `run_BVIIh_tilt_grow` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
