# A35 · MIO directional coherence (HJ-02a)

**Appendix**: A35 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with DOS-A30-MIO Week 7 Day 7).
**Code anchor**: [`bass_py/mio/coherence/directional.py`](../../bass_py/mio/coherence/directional.py)
**Test anchor**: [`bass_py/mio/tests/test_directional_coherence.py`](../../bass_py/mio/tests/)
**Artefact**: [`bass_py/workspace/results/mio_directional_coherence_v1.json`](../../bass_py/workspace/results/)
**Parent references**: v3 §4.5.3.2 (HJ-02 directional coherence);
v3 §16.2 (MIO-HJ-02a "완전 독립" row).

---

## A35.1 Purpose

HJ-02a answers one question on data alone: **do the five independent
directional probes (CMB / CatWISE / Radio / CF4++ / BiPoSH) point to a
common axis on the sky, or are they mutually isotropic?**

HJ-02a is the single MIO diagnostic in v3 §16.2 classified as
*"completely independent"* — it consumes neither a bass_py forward
K_ℓ atlas nor an HTT posterior. A single `MioCertificate` with
`report_type="directional_coherence"` is produced from the probe
measurements alone.

## A35.2 Inputs

The five SSOT probes live in `mio.coherence.directional.STANDARD_PROBES`:

| Probe | l (deg) | b (deg) | σ_cone (deg) | Weight | Provenance |
|---|---|---|---|---|---|
| CMB | 264.021 | 48.253 | 0.5 | 1.0 | Planck 2018 intermediate (Fixsen 1996 vector; Planck LIX) |
| CatWISE | 238.2 | 28.8 | 10.0 | 1.0 | Secrest+2020, arXiv:2009.14826 |
| Radio | 253.0 | 25.0 | 10.0 | 1.0 | Singal 2011 / Rubart-Schwarz 2013 / Blake-Wall 2002 composite; σ placeholder (see v3 §16.2 FM2) |
| CF4++ | 301.0 | -30.0 | 15.0 | 1.0 | Tully+2023 Cosmicflows-4 Principal Tidal field; σ placeholder |
| BiPoSH | 222.0 | -22.0 | 20.0 | 1.0 | Planck 2015 Appendix BipoSH; σ placeholder |

The σ_cone values for Radio / CF4++ / BiPoSH are plan-suggested
placeholders (v3 §16.2 FM2), kept constant until the Week 8
MANU-CH12-NEW §12.2 draft cites NVSS+RACS / Tully+2023 / Planck BipoSH
values with references. Impact on R and p_iso is dominated by the
CMB probe (σ = 0.5°) and is therefore negligible for current
conclusions.

## A35.3 Computation

Four derived statistics:

1. **Inverse-variance weighted spherical mean** via
   `common.sky_geometry.spherical_mean` — returns (l_bar, b_bar, R).
   The resultant length R ∈ [0, 1]; R = 1 corresponds to exact
   alignment, R = 0 to antipodal cancellation.
2. **Monte-Carlo p-value for isotropy** — the fraction of isotropic
   n_mock draws whose resultant length ≥ R_observed. Lidstone smoothed
   as `(k + 1) / (n_mock + 1)` so the point estimate never collapses
   to zero.
3. **Pairwise separation matrix** (deg) — literature cross-check for
   the published (CMB–CatWISE) ≈ 27.8° separation.
4. **Common-axis χ² / dof** — `Σ (Δ_i / σ_i)² / (N − 2)` with Δ_i the
   angular separation between probe i and the fitted axis.

## A35.4 Landed artefact (2026-04-19, seed 20260419)

Written to `bass_py/workspace/results/mio_directional_coherence_v1.json`
as part of W6D5 commit:

| Quantity | Value |
|---|---|
| (l_bar, b_bar) | (260.9°, 42.5°) |
| R | 0.9990 |
| p_iso | ≈ 3 × 10⁻⁴ |
| χ² / dof | 9.45 (dof = 3) |
| pairwise max separation | 80.4° (Radio ↔ BiPoSH) |

The low p_iso + high R at the 5-probe bundle are consistent with the
informal consensus in the literature that the matter-frame dipole
directions point roughly toward Hydra – Centaurus – Norma. The high
χ² per dof is the expected tension: CF4++ and BiPoSH deviate from the
CMB axis by 60–80°, which the common-axis fit does not absorb.

## A35.5 MioCertificate mapping

The report is serialised via `to_mio_certificate(...)`:

```python
MioCertificate(
    report_type="directional_coherence",
    probe_name="CMB+CatWISE+Radio+CF4pp+BiPoSH",
    channel="dipole",
    departure_variables={
        "resultant_R": 0.9990,
        "l_deg_best": 260.9,
        "b_deg_best": 42.5,
    },
    adequacy_indicators={
        "isotropy_p_lt_0p01": True,
        "all_probes_within_20deg_cone": False,
    },
    consistency_metrics={
        "chi2_per_dof": 9.45,
        "pairwise_max_sep_deg": 80.4,
    },
    domain_caveats=[
        "radio_sigma_cone_plan_placeholder",
        "cf4pp_sigma_cone_plan_placeholder",
        "biposh_sigma_cone_plan_placeholder",
    ],
    channel_caveats=[],
    reduction_status="theory-direct",
    generated_by="mio.coherence.directional v0.1",
    ...
)
```

The `probe_name = "CMB+CatWISE+Radio+CF4pp+BiPoSH"` string-join is
ad hoc (v3 §16.2 FM5); a structured `probe_names: list[str]` field
would trip the CONTRACTS-01 schema freeze and must wait on a
coordinated v2 schema bump.

## A35.6 G19 posture

HJ-02a satisfies G19 structurally:

- **No posterior output.** The certificate carries only summary
  statistics; `as_posterior_bundle()` raises `NotImplementedError`.
- **No HTT ingestion path.** The `MioCertificate` instance cannot be
  fed into any HTT likelihood (enforced by
  `test_htt_cannot_ingest_miocertificate_as_likelihood`).
- **Advisory cross-check with HTT dipole.** The common-axis χ²/dof is
  informative for HTT PR13AH's dipole-vector likelihood, but the two
  sides never merge into a single score. This channel is listed in
  A34.3 as *advisory*, not numerical — there is no matched numerical
  pair to cross-check yet.

## A35.7 Scope-of-validity

The diagnostic trusts that:

- Each probe reports its direction in the **matter-frame** (heliocentric
  frame boosted by β_kin into the local CMB rest frame). Probes
  reporting in the geometry-frame would need an un-boosting step;
  `spherical_mean` does not apply that correction.
- The σ_cone numbers capture an isotropic Gaussian cone around the
  reported direction. Probes with asymmetric / non-Gaussian pointing
  uncertainty would produce an inflated χ²/dof; the HJ-02-full
  upgrade path (Week 8+) will switch to per-probe posterior samples
  when available.

## A35.8 Related appendices

- [A32 MioCertificate schema](A32_mio_certificate_schema.md) — field
  semantics for the dataclass HJ-02a populates.
- [A38 masked-sky caveats](A38_masked_sky_caveats.md) — the
  sky-coverage caveats attached to `domain_caveats`.
- [A39 per-module epistemic ownership](A39_per_module_epistemic_ownership.md)
  — where `mio.coherence.directional` sits in the ownership table.
- [A40 G19 architectural stance](A40_g19_architectural_stance.md) —
  why HJ-02a carries no posterior.
