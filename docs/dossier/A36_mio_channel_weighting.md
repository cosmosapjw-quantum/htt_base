# A36 · MIO channel weighting policy

**Appendix**: A36 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with DOS-A30-MIO Week 11 Day 5-6).
**Code anchor**:
[`bass_py/mio/coherence/directional.py`](../../bass_py/mio/coherence/directional.py) (HJ-02a per-probe inverse-variance weights);
[`bass_py/mio/coherence/redshift_binned.py`](../../bass_py/mio/coherence/redshift_binned.py) (HJ-02b per-bin resultants);
[`bass_py/mio/extraction/hj01_shear.py`](../../bass_py/mio/extraction/hj01_shear.py) (HJ-01 per-ℓ residual weighting).
**Parent references**:
v3 §4.5 (MIO Phase J module tree);
v3 §16.2 FM2 (σ_cone placeholders feeding inverse-variance weights);
W10 F2 (HJ-01 cosmic-variance per-ℓ covariance deferred);
A34 (G19 cross-check protocol — which channels merge, which do not).

---

## A36.1 Purpose

The MIO pillar publishes *multi-channel* diagnostics:

- HJ-01 — per-multipole Σ²_MIO(ℓ) across the ℓ window (channel = ℓ);
- HJ-02a — per-probe directions (channel = probe identity);
- HJ-02b — per-z-bin resultants (channel = redshift bin);
- HJ-03 (planned) — per-channel Δln B decomposition (channel = CMB channel b/c/d/e/f/g/h).

This dossier fixes the **policy** for when those per-channel numbers
may be weighted and combined, and when they must be kept disaggregated.
The policy is structural (G19) and not statistical: it tells the
certificate author *what question each weighted scalar answers*, not
*which estimator has lowest variance*.

## A36.2 Three categories of weighting

| Category | Allowed inside MIO? | Rationale |
|---|---|---|
| **Per-probe / per-ℓ inverse-variance within a single statistic** | **Yes** | Constructing a single statistic (resultant R, χ², posterior-predictive test) from N noisy measurements of the same quantity is a standard estimator choice. HJ-02a's `weight = 1 / σ_cone²` and HJ-01's `Σ² = Σ_ℓ w_ℓ · (ΔC_ℓ / K_ℓ)` fall here. |
| **Cross-channel fusion within MIO** (e.g. merging HJ-01 Σ² and HJ-02a R into one scalar) | **No** — emit both side-by-side | These measure different observable content. Any single-scalar fusion would require a joint likelihood, which MIO does not own (G19 §12.2 — MIO never produces likelihoods). A34 documents the *advisory* cross-check channel catalogue; merging is explicitly prohibited. |
| **MIO + HTT fusion** (e.g. adding MIO Σ² to HTT ln B) | **No, ever** | G19's load-bearing prohibition. An audit-enforced grep ensures `mio.*` results never flow into `htt.*` likelihoods. See A34.4 failure-mode table. |

The policy is therefore: **weighting within a single MIO statistic
is unrestricted; weighting across statistics is prohibited.**

## A36.3 Per-statistic weighting specifications

### HJ-01 Σ²_MIO(ℓ)

Per-ℓ weights are
`w_ℓ = 1 / σ_ℓ²`
with
`σ_ℓ² = σ_obs² / K_ℓ²`
(the measurement-noise contribution divided by the squared nonparametric kernel value).
W10 F2 notes that this treatment ignores cosmic-variance correlations
between multipoles; upgrading to the full per-ℓ covariance from
bass_py W10-02 is the prerequisite for promoting `reduction_status`
from `diagnostic-only` to `theory-direct`.

### HJ-02a resultant R

Per-probe weights are
`w_i = weight_i / σ_cone_i²`
where `weight_i` defaults to 1.0 and is meant only for deliberate
down-weighting (e.g. an outlier probe kept in the catalogue for
audit purposes). The inverse-variance weighting is documented
inside `_probe_weights` and reused across
`resultant_vector`, `isotropy_pvalue`, and `coherence_chi2` so that
the SSOT is a single function, not three parallel recomputations.

### HJ-02b per-bin resultant

Inside each z bin, the weighting **identically** matches HJ-02a —
`w_i = weight_i / σ_cone_i²` on the probes that landed in that bin.
Across bins no weighting is applied: the total-drift statistic is a
pure sum of adjacent-bin angular separations. Empty bins contribute
zero and are flagged with `n_probes=0` + NaN direction.

### HJ-03 Δln B (planned)

Once HJ-03 lands, per-channel Δln B numbers are passed through
**without re-weighting**. The consumer may choose to plot a cumulative
stack, but A36.2 row 2 means no single weighted fused scalar is
emitted from MIO.

## A36.4 Placeholder σ caveat (v3 §16.2 FM2)

Three of the five HJ-02a probes currently carry plan-suggested σ_cone
placeholders (Radio / CF4++ / BiPoSH). Because inverse-variance
weighting emphasises low-σ probes, the CMB axis (σ = 0.5°)
dominates the HJ-02a resultant and HJ-02b low-z bin fitted direction.
Until MANU-CH12-NEW §12.2 cites published σ values, the
`domain_caveats` list attached to every `MioCertificate` from these
modules carries `*_sigma_cone_plan_placeholder` entries so the
downstream reader is explicitly warned.

**Provenance anchor (W13D3 / W14D2)**: the per-PROBE_ID literature
lookup for σ_cone has been moved to
[A36a σ_cone literature](A36a_sigma_cone_literature.md). §A36a.2
records the DOI/arXiv-anchored value per probe, §A36a.3 records the
Δ between code-side σ and literature σ per probe, and §A36a.5
spells out the three-condition retirement criterion for the
`*_sigma_cone_plan_placeholder` caveat flag (paired with the cross-
producer σ parity test added in W14D1 —
`test_standard_probes_have_consistent_sigma_cone_across_producers`).

## A36.5 G19 posture

- Per-statistic weighting is internal to one module and produces one
  certificate; no posterior is formed.
- Cross-statistic weighting would implicitly require a joint likelihood,
  which is exactly the merge pattern forbidden by G19. The A34 channel
  catalogue makes this explicit at the protocol level.
- All channel-weighted scalars inside a single MIO certificate are
  exposed in `consistency_metrics` with their dimensioned quantities
  (χ²/dof, drift_pvalue, p_value_independence), not a hidden composite.

## A36.6 Related appendices

- [A32 MioCertificate schema](A32_mio_certificate_schema.md) — where
  weighted scalars are stored (`consistency_metrics` vs
  `adequacy_indicators`).
- [A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md) —
  the complementary "no cross-statistic merging" rule.
- [A35 HJ-02a directional coherence](A35_directional_coherence.md) —
  concrete σ_cone-weighted statistic.
- [A37 MIO probe-name schema](A37_mio_probe_name_schema.md) — the
  naming field that labels which probes participated in each
  weighted statistic.
- [A39 per-module epistemic ownership](A39_per_module_epistemic_ownership.md)
  — which module owns each weighting decision.
