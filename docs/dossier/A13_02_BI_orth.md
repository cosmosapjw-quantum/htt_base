# Dossier — Bianchi I, orthogonal (pure-shear baseline)

**Appendix**: A13-02
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiI_orth` (name `BI_orth`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-02 |
| Model name            | Bianchi I, orthogonal (`BI_orth`) |
| Structural class      | Bianchi type I (flat spatial sections, diagonal shear) |
| Dimensionality        | 1 free anisotropy d.o.f. (Σ²); tilt/vorticity enforced to zero by δ-prior |
| Reference DOIs / arXiv | Jaffe+2005 (astro-ph/0503213); Saadeh+2016 (PRL 117, 131302); Planck 2018 VII |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] (`_logu(u[0], 1e-30, 1e-4)`) |
| Tilt            | β  | δ-prior at 0 | — |
| Vorticity       | W² | δ-prior at 0 | — |
| Four-acceleration | A² | δ-prior at 0 | — |
| Direction (l, b) | (l, b) | δ-prior (identified with shear eigenframe) | — |

Matched-complexity note: BI_orth has `D_anisotropy = 1` in the htt registry.
A15 requires that direct competitors at the 1-d.o.f. level (e.g. FLRW_tilt
with β-only) carry matching δ-priors; see A13-01 §2.

## 3. Kinematic signature

- Σ²(η) — monotonic decay under `_shear_mode = 'decay'` (default);
  analytically Σ² ∝ a(η)⁻⁶ in the radiation era.
- W²(η) ≡ 0 — no vorticity (type I has no structure constants).
- β(η) ≡ 0 — orthogonal congruence.
- Θ(η), H(η) — ΛCDM background with small shear back-reaction neglected
  at leading order (MES hard-ceiling `_mes_ok(Sig2)` guards the regime).

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | TT anomalies (D2, D3 via `shear_to_D2`, `shear_to_D3`) | *pending* |
| (c) | TE dipole response | ~0 (orthogonal — no boost to TE) |
| (d) | Bulk flow | ~0 (no peculiar velocity sourced by pure shear) |
| (e) | BAO / sound-horizon hooks | *pending* |
| (f) | MES hard ceiling | active (`_mes_ok` clips Σ² > 10⁻⁴) |
| (g) | MES soft sigmoid | inert by default |
| (h) | D_ℓ χ² direct | *pending* |

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BI_orth | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline (Planck 2018 Commander low-ℓ) | *pending* | *pending* |
| S2 | Planck + bulk-flow                       | *pending* | *pending* |
| S3 | full stack (+ BAO + lensing)             | *pending* | *pending* |

Target from v3 §11.14.2: BI_orth serves as the pure-shear floor in the
15-model ladder; its ln B vs FLRW is expected to be mildly disfavored
(Σ² prior volume vastly exceeds the posterior support).

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| (l, b)    | *pending* (identified with shear eigenframe) | — | — |

Posterior fields land in Phase H (W15-02 dynesty run).

## 7. Pitfalls / identifiability notes

- **Σ² prior-volume Occam penalty**: the 26-decade log-uniform prior is
  the dominant contribution to ln B when Σ² is unresolved; declare any
  small |ln B| as "prior-volume-driven" via A17 Occam decomposition.
- **Eigenframe vs (l, b) identifiability**: BI_orth has no intrinsic
  preferred direction beyond the shear eigenframe; `directional_models`
  marginalises this out rather than sampling (see HTT-P0-AJ).
- **MES hard-ceiling saturation**: `_mes_ok(Sig2)` clips the posterior
  above Σ² ~ 10⁻⁴ — any edge-hitting posterior flags a model-data
  mismatch, not a detection.

## 8. Reference figures

- F06 — Σ² posterior marginal with MES ceiling overlay
- F07 — D_ℓ residual band (BI_orth MAP vs Planck)
- F08 — channel contribution bar (b/c/d/e/f/g/h → ln Z)

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BI_orth` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
