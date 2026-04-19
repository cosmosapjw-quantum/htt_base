# Dossier — Bianchi II, orthogonal (Heisenberg-algebra shear)

**Appendix**: A13-04
**Status**: DOS-A13 landing (posterior fields placeholder pending Phase H).
**Upstream**: BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md §11.10.1 / DOS-A13;
`htt.core.evidence_models_R03a.BianchiII_orth` (name `BII_orth`).

---

## 1. Model identity

| Field | Value |
|---|---|
| Dossier ID            | A13-04 |
| Model name            | Bianchi II, orthogonal (`BII_orth`) |
| Structural class      | Bianchi type II (Heisenberg Lie algebra, n₁ ≠ 0 structure constant) |
| Dimensionality        | 2 free d.o.f. (Σ², n₁) |
| Reference DOIs / arXiv | King & Ellis 1973 (Comm. Math. Phys. 31, 209); Wainwright & Ellis §8.3 |

## 2. Free parameters and priors

| Parameter | Symbol | Prior family | Support / hyperparameters |
|---|---|---|---|
| Shear amplitude | Σ² | log-uniform | [10⁻³⁰, 10⁻⁴] |
| Structure constant | n₁ | log-uniform | [10⁻⁶, 1] (`_logu(u[1], 1e-6, 1.)`) |
| Tilt β | — | δ-prior at 0 | — |
| Four-acceleration A² | — | δ-prior at 0 | — |

Matched-complexity note: 2-d.o.f. bucket — direct competitors at this
dimension include BI_tilt (Σ², β), BVI0_orth (Σ², a₁), BVIIh_orth
(Σ², x_h), and BVIII/BIX_orth (Σ², Ω_k).

## 3. Kinematic signature

- Σ²(η) — decay mode (`_shear_mode = 'decay'`).
- n₁ sets the Heisenberg-algebra torsion amplitude; n₁ → 0 recovers
  BI_orth.
- Additional mode coupling: BII geometry injects non-diagonal stress
  terms that back-react at subleading order (neglected in the R03a
  likelihood; only Σ² enters `shear_to_D2/D3` via `_pred_orth`).
- β, A², ω_H ≡ 0.

## 4. Distinguishing channels

| Channel | Physics | Expected `Δ ln B` |
|---|---|---|
| (b) | TT anomalies (D2, D3) | *pending* |
| (c) | TE dipole | ~0 |
| (d) | Bulk flow | ~0 |
| (e) | BAO hooks | *pending* |
| (f) | MES hard ceiling | active |
| (g) | MES soft sigmoid | inert |
| (h) | D_ℓ χ² | *pending* |

BII n₁ is unresolved in the leading-order likelihood; its prior volume
contributes an Occam penalty of ≈ −ln(6) = −1.79 per decade relative
to BI_orth.

## 5. Scenario-dependent Bayes factors (S1 / S2 / S3)

| Scenario | Description | ln Z_BII_orth | ln B vs. FLRW |
|---|---|---|---|
| S1 | baseline (Planck 2018 Commander low-ℓ) | *pending* | *pending* |
| S2 | Planck + bulk-flow                       | *pending* | *pending* |
| S3 | full stack (+ BAO + lensing)             | *pending* | *pending* |

## 6. Posterior summary (median + 68% HPD)

| Parameter | Median | 68% HPD | 95% HPD |
|---|---|---|---|
| Σ²        | *pending* | — | — |
| n₁        | *pending* (flat marginal expected) | — | — |

## 7. Pitfalls / identifiability notes

- **n₁ is observationally invisible at R03a order**: the likelihood only
  uses Σ² through `_pred_orth`. n₁ shows up in A18 residual patterns
  only if the D_ℓ analysis includes higher-order multipoles beyond
  ℓ ≤ 3 (W11-02 BiPoSH).
- **Unresolved nuisance**: n₁ posterior will be prior-dominated; the
  6-decade prior imposes a −1.79 · (Δ log₁₀ n₁) Occam penalty.
- **Algebraic degeneracy with BI_orth**: at n₁ → 0 this model collapses
  to BI_orth; cross-check via Δ ln B at the n₁-prior lower edge.

## 8. Reference figures

- F11 — (Σ², n₁) joint posterior
- F12 — D_ℓ residual band
- F13 — A18 posterior predictive χ²/ndof

## 9. Provenance

| Field | Value |
|---|---|
| Posterior run ID | `run_BII_orth` (pending Phase H) |
| Dynesty config hash | *pending* |
| Data bundle hash | *pending* |
| Generated on | 2026-04-19 |
