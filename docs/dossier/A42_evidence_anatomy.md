# A42 · MIO evidence anatomy (HJ-03) — deferred design stub

**Appendix**: A42 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W13D5 **stub** (documentation-only; no code landing).
**Status**: **deferred** — HJ-03 is blocked on HTT Phase F posterior-
decomposition outputs (v3 §17.3). This dossier exists so A41.6 "Worked
example — HJ-03 evidence anatomy" has a concrete target to cross-link.
**Code anchors (planned)**:
`bass_py/mio/decomposition/evidence_anatomy.py` — **not yet created**;
the HJ-03 author lands this module per the A41 mechanical checklist.
**Parent references**:
v3 §4.5.3.3 (MIO evidence-anatomy module);
v3 §17.3 (dependency wait list — HTT Phase F ln B decomposition);
[A32 MioCertificate schema](A32_mio_certificate_schema.md);
[A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md) (the
cross-check against `htt.core.analysis_extended.EvidenceComparison`);
[A36 MIO channel weighting](A36_mio_channel_weighting.md) (no re-
weighting on the per-channel Δln B stream);
[A39 per-module epistemic ownership](A39_per_module_epistemic_ownership.md);
[A40 G19 architectural stance](A40_g19_architectural_stance.md);
[A41 report_type extension protocol](A41_mio_report_type_extension_protocol.md).

---

## A42.1 Purpose

HJ-03 "evidence anatomy" answers the question: **given an HTT
posterior ln B for a Bianchi-type vs FLRW comparison, which CMB
channel contributes which fraction of the total?** The MIO pillar
produces a disaggregated per-channel Δln B table as an advisory
cross-check; the HTT pillar owns the authoritative total. G19
separation is therefore enforced not by a posterior ban (MIO never
emits a posterior) but by refusing to recombine channels into a
single scalar once they have been decomposed (A36.2 row 2).

The MIO certificate answers *three* derived questions:

1. **Anatomy**: which channel dominates the evidence — low-ℓ TT,
   high-ℓ TT, TE, EE, or a lensing-reconstruction subset?
2. **Sign coherence**: do all contributing channels agree on the
   sign of `ln B_Bianchi − ln B_FLRW`, or is the net ln B the result
   of a cancellation between disagreeing channels?
3. **Consistency**: does the per-channel sum reproduce the HTT
   total within the expected numerical floor, or is there a
   decomposition residual that flags an upstream bug?

## A42.2 Inputs (planned)

HJ-03 consumes an **HTT posterior bundle** produced by
`htt.core.analysis_extended.EvidenceComparison.run_all`. The
contract is the forthcoming HTT Phase F deliverable and is **not yet
frozen**; the A42.5 placeholder table below lists the required
surface.

| Key (planned) | Type | Meaning |
|---|---|---|
| `channel_names` | `tuple[str, ...]` | e.g. `("lowTT", "highTT", "TE", "EE", "lensing")`. |
| `delta_lnB_per_channel` | `np.ndarray` shape `(len(channel_names),)` | `ln B_Bianchi_c − ln B_FLRW_c` per channel `c`. |
| `cov_delta_lnB` | `np.ndarray` shape `(C, C)` | Numerical-sampling covariance across channels; diagonal in the ideal case, off-diagonal in practice. |
| `total_lnB` | `float` | HTT authoritative total; the anatomy must reproduce this within ε (see A42.4). |
| `atlas_entry_id` | `str` | MODEL_ID of the winning Bianchi type (→ A37.2 atlas_label singleton). |

**Status**: all five keys are documentation-only as of W13D5. Once
HTT Phase F lands, a `workspace.contracts.HTTEvidenceDecomposition`
dataclass (or equivalent) will be added and HJ-03 will bind against
it.

## A42.3 Computation (planned)

The per-channel stream is passed through *unweighted* (A36 §A36.3
row "HJ-03 Δln B (planned)" — the tabular label was renamed from
HJ-04 to HJ-03 across A34 / A36 / A40 in W14D3; see §A42.6).
Derived fields:

1. **Anatomy ranking**: argsort(|delta_lnB_per_channel|) giving the
   top-2 and bottom-2 dominant channels; reported in
   `departure_variables.dominant_channels: list[str]`.
2. **Sign-coherence fraction**: `frac_same_sign = sum(1 for c in channels
   if sign(delta_lnB_c) == sign(total_lnB)) / C`. Reported in
   `adequacy_indicators.sign_coherence_frac: float ∈ [0, 1]`.
3. **Decomposition residual**: `delta = total_lnB − sum(delta_lnB_per_channel)`
   reported in `consistency_metrics.decomposition_residual: float`
   (expected ~`1e-3` or better for a correctly-computed decomposition).
4. **Cross-check scalar**: the tuple `(top_channel, frac_same_sign,
   decomposition_residual)` is the A34.7 cross-check surface; no
   single-scalar fusion.

No channel-level inverse-variance weighting is applied. The covariance
`cov_delta_lnB` is reported in the certificate payload (so the
downstream reader can form a per-channel error bar) but is **not**
used by MIO to contract the stream.

## A42.4 Decomposition-residual acceptance floor

A passing decomposition has
`|decomposition_residual| ≤ max(1e-3, 1e-3 · |total_lnB|)`
— i.e. one part in a thousand, with a 1e-3 absolute floor for
`total_lnB ≲ 1`. Exceeding the floor triggers a
`DIAGNOSTIC_ONLY_CAVEAT`-style caveat
(`"decomposition_residual_above_floor"`) and forces
`reduction_status = "diagnostic-only"` even after HTT Phase F
promotes the upstream total to authoritative. The floor is a
*numerics* gate, not a *physics* gate: a failure indicates an HTT
bug or a mis-registered channel key, not an astrophysical signal.

## A42.5 Certificate contract (planned)

A42 fixes the **shape** HJ-03 must emit once it lands. The fields
below are proposed values; they will be frozen on the first HJ-03
landing commit per the A41.2 rule (new `report_type` value, no
schema-hash rotation).

| `MioCertificate` field | Planned value | Source |
|---|---|---|
| `report_type` | `"evidence_anatomy"` | pre-reserved A32.2. |
| `channel` | `"full_TTTEEE"` (default) or `"low_ell"` / `"lensing"` per caller | A41.6 step 3 pattern. |
| `probe_name` | `"BianchiVIIh"` / `"BianchiIX"` / `"BianchiI"` — MODEL_ID atlas_label singleton per A37.2 | A37.3 extension not required (PROBE_ID list is closed at five; MODEL_IDs are a separate vocabulary). |
| `reduction_status` | `"diagnostic-only"` until HTT Phase F V-gate; `"theory-direct"` in a paired promotion commit. | A41.6 step 5. |
| `departure_variables.dominant_channels` | `list[str]`, 2-4 entries | A42.3 step 1. |
| `adequacy_indicators.sign_coherence_frac` | `float ∈ [0, 1]` | A42.3 step 2. |
| `consistency_metrics.decomposition_residual` | `float` | A42.3 step 3; gated by A42.4. |
| `domain_caveats` | `["DIAGNOSTIC_ONLY_CAVEAT", …]` until V-gate; may add `"decomposition_residual_above_floor"` | A42.4; A41.3 step 3. |

**Artefact filename**: `mio_evidence_anatomy_v1.json`
(REG-02 `mio_` prefix per the HJ-01 / HJ-02a / HJ-02b precedent).

## A42.6 Naming-drift carry-forward (RESOLVED W14D3)

The governing plan (`INDEPENDENT_TRACKS_NEXT_SESSION.md` §2
Week 13 Days 5-6) binds **HJ-03 ↔ evidence_anatomy** and
**HJ-04 ↔ flrw_tension**. This binding is now consistent across
the dossier tree:

- [A34 §A34.3](A34_g19_cross_check_protocol.md) — channel catalogue
  now reads "HJ-03 evidence anatomy".
- [A36 §A36.1 / §A36.3](A36_mio_channel_weighting.md) — bullet and
  per-statistic heading now read "HJ-03 Δln B (planned)".
- [A40 §A40.1 / §A40.4 / §A40.7](A40_g19_architectural_stance.md) —
  prose and ownership-table row now read "HJ-03 evidence anatomy".

**Closure commit**: W14D3 (W13 F1 sweep) — three dossier files
renamed in a single commit scoped exactly to the three paths above;
no code change. The commit restores the invariant that A32 / A41
(schema-authoritative) and A34 / A36 / A40 (tabular) describe the
same diagnostic under the same label. Gate at commit time: ripgrep
for the pre-rename phrase ("HJ" then "-04 evidence") across
`docs/dossier/` returns zero matches.

## A42.7 G19 posture

- HJ-03 consumes an HTT posterior **as a cross-check input** under
  A34. The consumption is one-way: MIO reads HTT fields; MIO does
  not write back into any HTT data structure.
- No Δln B number is ever merged into a MIO scalar beyond
  per-channel pass-through (A36.2 row 2 — prohibition against
  cross-statistic fusion).
- The A42.5 certificate stores both the per-channel stream and the
  three A42.3 derived scalars side by side; a reader that wants a
  weighted composite must construct it downstream under a
  non-MIO-owned likelihood (G19 §10.2bis).

## A42.8 Test plan (placeholder)

Once HJ-03 lands (post-Phase-F), the following acceptance tests are
required by A41.3 step 6:

1. `test_evidence_anatomy_reproduces_htt_total_within_floor` —
   computes `|decomposition_residual|` on a synthetic HTT bundle and
   asserts `≤ 1e-3`.
2. `test_evidence_anatomy_sign_coherence_on_degenerate_case` —
   constructs a per-channel stream with all-same-sign entries and
   asserts `sign_coherence_frac == 1.0`.
3. `test_evidence_anatomy_probe_name_matches_atlas_label_grammar` —
   A37.2 atlas_label singleton compliance (reuses the W12D1
   `test_probe_name_grammar.py` harness).
4. `test_evidence_anatomy_refuses_posterior_keyword` — inherited
   from the A41.3 step 6.1 G19 harness.
5. `test_evidence_anatomy_artefact_uses_mio_prefix` — REG-02 gate.

The first landing commit will also land a dossier delta that
promotes §A42 from **stub** to **landed**, tightens the A42.2
contract to the actual HTT dataclass, and records the A42.4 floor
that was achieved in practice.

## A42.9 Related appendices

- [A32 MioCertificate schema](A32_mio_certificate_schema.md) — the
  field taxonomy the A42.5 table plugs into.
- [A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md) —
  the protocol HJ-03 plugs into as an `is_cross_check=True` consumer
  of HTT.
- [A36 MIO channel weighting](A36_mio_channel_weighting.md) — the
  "no cross-channel fusion" rule A42.3 inherits.
- [A40 G19 architectural stance](A40_g19_architectural_stance.md) —
  architectural ringfence around the decomposition.
- [A41 report_type extension protocol](A41_mio_report_type_extension_protocol.md)
  — the mechanical checklist HJ-03 follows on landing; this dossier
  is A41.6's worked-example target.
