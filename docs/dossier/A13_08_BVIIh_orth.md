# Dossier — Bianchi VII_h, orthogonal (whirl-shear baseline; grow/dec pair)

**Appendix**: A13-08
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiVIIh_orth` (name `BVIIh_orth`) and
`BianchiVIIh_orth_grow` (alternate `_shear_mode='grow'` variant).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-08 |
| Model name            | Bianchi VII_h, orthogonal (`BVIIh_orth`) + grow-mode variant (`BVIIh_orth_grow`) |
| Structural class      | Bianchi type VII_h (whirl parameter h > 0, spiral CMB signature) |
| Dimensionality        | 2 free d.o.f. (Σ², x_h); tilt δ-prior 0 |
| Reference DOIs / arXiv | Barrow, Juszkiewicz & Sonoda 1985; Jaffe+2005 (astro-ph/0503213); Saadeh+2016 (PRL 117, 131302) |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] (decay mode); [10⁻²⁰, 10⁻⁴] (grow variant — tighter low-edge) |
| Whirl parameter | x_h | log-uniform | [10⁻³, 10³] |
| Vorticity | W² | derived | `W² = R_WS_VIIH² × Σ²` with `R_WS_VIIH = 1.06` (Wainwright & Ellis) |
| β, A² | — | δ-priors at 0 | — |

Matched-complexity: 2-d.o.f. bucket. Note: W² is an analytic function of
Σ² in this model (not a free parameter), so the effective
`D_anisotropy = 2` (Σ², x_h) is correct.

## 3. Kinematic signature

- Σ²(η) — decay mode (`BVIIh_orth`) or grow mode (`BVIIh_orth_grow`).
- W²(η) = 1.1236 × Σ²(η) via the WS ratio.
- Spiral "whirl" signature in CMB D_ℓ: characteristic x-pattern
  modulated by x_h; this is the famous "Jaffe alignment" feature at
  x_h ≈ 1 — Planck 2018 VII ruled out this specific x_h region at
  |Σ| < 5×10⁻¹⁰.
- β, A² ≡ 0.

### BVIIh_orth_grow variant

Same parameters, different `_shear_mode`. Grow-mode allows Σ² to
increase toward late times rather than decay — this changes the
late-integrated Sachs-Wolfe contribution to channel (b) and shifts
the predicted D_ℓ residual envelope. Covered as a sibling entry
`BVIIh_orth_grow` in `ALL_MODELS` and scanned jointly.

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | D_2 / D_3 + spiral D_ℓ signature | **primary discriminator**; Jaffe pattern sits at specific (Σ², x_h) |
| (c) | TE | ~0 (orthogonal, no boost) |
| (d) | Bulk flow | ~0 |
| (e) | BAO | *pending* |
| (f) | MES hard ceiling | active |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | *pending* |

Historical context: VII_h_orth is the Bianchi model most constrained
by Planck 2018 VII — the whirl signature is very specific.

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BVIIh_orth | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline | *pending* | *pending* (expect strongly disfavored — Planck 2018 VII ruled out) |
| S2 | + bulk-flow | *pending* | *pending* |
| S3 | full stack | *pending* | *pending* |

| Scenario | BVIIh_orth_grow ln Z | grow Δ ln B vs decay |
|---|---|---|
| S1 | *pending* | *pending* |
| S2 | *pending* | *pending* |
| S3 | *pending* | *pending* |

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| x_h       | *pending* (expect bimodal — peak near x_h ≈ 1 Jaffe region) | — | — |

## 7. Pitfalls / identifiability notes

- **Jaffe-peak degeneracy**: x_h ≈ 1 reproduces the historic "cold spot"
  claim; any posterior concentration there should be triangulated
  against the Saadeh+2016 null (PRL 117, 131302). Phase H must report
  both ln B and PPC p-value to distinguish "data prefers x_h ≈ 1" from
  "prior volume concentrates there by default".
- **Σ² grow vs decay branch ambiguity**: treat the two as separate
  models (`BVIIh_orth` and `BVIIh_orth_grow`) for evidence purposes;
  do NOT marginalise across shear modes — that would double-count the
  x_h peak.
- **Spiral signature is data-specific**: Planck 2018 Commander maps at
  N_side = 2048 are the reference; masked-sky caveats per A38 apply.

## 8. Reference figures

- F22 — (Σ², x_h) joint posterior with Jaffe-region overlay
- F23 — spiral D_ℓ residual pattern (N_side = 64)
- F24 — BVIIh_orth vs BVIIh_orth_grow Σ² trajectory comparison

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BVIIh_orth`, `run_BVIIh_orth_grow` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
