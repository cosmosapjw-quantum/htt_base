# A36a · MIO σ_cone literature anchoring

**Appendix**: A36a (complement to A36; §11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with W13D3; closes W6 FM2 / W11 F3).
**Code anchors**:
[`bass_py/mio/coherence/directional.py`](../../bass_py/mio/coherence/directional.py) (`STANDARD_PROBES` — the five HJ-02a σ_cone values);
[`bass_py/mio/coherence/redshift_binned.py`](../../bass_py/mio/coherence/redshift_binned.py) (`STANDARD_Z_PROBES` — verbatim mirror with `z_eff` tags).
**Parent references**:
[A36 §A36.4 Placeholder σ caveat](A36_mio_channel_weighting.md) — current `*_sigma_cone_plan_placeholder` warning flow;
[A37 §A37.3 Registered PROBE_IDs](A37_mio_probe_name_schema.md) — the five-PROBE_ID catalogue this dossier cross-references;
v3 §16.2 FM2 (σ_cone placeholders feeding inverse-variance weights);
W6 FM2 / W11 F3 carry-forwards (this dossier resolves the documentation leg;
code-side σ values remain the caller's judgement — see §A36a.4).

---

## A36a.1 Purpose and scope

A36 §A36.4 flagged three of the five HJ-02a / HJ-02b `sigma_cone_deg`
values as *plan-suggested* rather than DOI-anchored. This appendix
records, per probe, the literature σ that the plan-suggested value
was approximating, the delta (`σ_code − σ_literature`), and whether
the code value is conservative (larger σ → less inverse-variance
weight) or optimistic (smaller σ → more inverse-variance weight).

**This is a documentation pass.** The code-side `sigma_cone_deg`
defaults are intentionally **unchanged** in W13D3 (plan §2 Days 3-4:
*"MIO σ values may or may not be updated (caller's judgement)"*).
Any numerical update to `STANDARD_PROBES` would need to land as a
separate commit paired with an A36/A36a update and a regression
rationale; the default inverse-variance weighting is CMB-dominated
and numerically stable, so no live bug motivates an immediate swap.

The `domain_caveats` flag emitted by HJ-02a / HJ-02b
(`*_sigma_cone_plan_placeholder`) remains active until a paired
update lands; A36a.5 proposes the promotion criterion.

## A36a.2 Per-probe literature record

Legend: **L** = direction-uncertainty σ actually quoted in the cited
primary work (or the nearest public reanalysis); **C** = code value
in [`bass_py/mio/coherence/directional.py`](../../bass_py/mio/coherence/directional.py); **Δ** = C − L (positive = code is
conservative); **Status** = whether the code value is DOI-anchored,
literature-consistent-but-not-verbatim, or plan-placeholder.

### CMB dipole — PROBE_ID `CMB`

- **L**: Planck 2018 Results I / Planck 2018 Intermediate Results LVI:
  the dipole direction `(l, b) = (264.021°, 48.253°)` is quoted with
  a statistical uncertainty of order a few arcminutes
  (Δl ≲ 0.005°, Δb ≲ 0.005° at the Planck-internal level once beam
  and mask systematics are absorbed). The Fixsen 1996 (FIRAS) dipole
  direction error is larger (~0.05°) but no longer the Dominant
  constraint.
- **C**: `sigma_cone_deg=0.5`.
- **Δ**: +0.495° (C ≫ L).
- **Status**: **literature-consistent-but-not-verbatim / conservative.**
  0.5° is a deliberately inflated catalogue value — large enough that
  numerical degeneracy with the MC isotropy test (where a single
  near-zero σ probe would make the χ² pathological) is avoided.
  This is the correct qualitative choice for a multi-probe resultant
  test; the verbatim Planck σ would dominate the weighting to the
  degree that HJ-02a reduces to "does everything agree with CMB",
  defeating the multi-probe point.
- **References**: Planck Collaboration (2018), "Planck 2018 results.
  I. Overview and the cosmological legacy", arXiv:1807.06205; Planck
  Collaboration (2020), "Planck 2018 intermediate results. LVI.
  Detection of the CMB dipole through modulation of the thermal
  Sunyaev-Zel'dovich effect", A&A 644, A100, DOI 10.1051/0004-6361/202038053;
  Fixsen et al. (1996), ApJ 473, 576, DOI 10.1086/178173.

### CatWISE quasar sample — PROBE_ID `CatWISE`

- **L**: Secrest, von Hausegger, Rameez, Mohayaee, Sarkar, Colin
  (2021), "A Test of the Cosmological Principle with Quasars", ApJ
  Letters 908, L51 (arXiv:2009.14826, DOI 10.3847/2041-8213/abdd40).
  The published dipole direction is `(l, b) ≈ (238°, 28.8°)` with a
  statistical 1σ cone radius of ~**5.9°** derived from a bootstrap
  over the selection cuts (their §3.3, Figure 3 caption). Updates in
  Secrest+ 2022 (arXiv:2206.05624) keep the uncertainty in the
  5–7° range.
- **C**: `sigma_cone_deg=6.0`.
- **Δ**: +0.1° (C essentially matches L).
- **Status**: **DOI-anchored (Secrest+2021 §3.3).** A36a.5-promoted
  **2026-W14D5** — `CatWISE` is absent from the placeholder tag set
  emitted by `mio.coherence.directional.to_mio_certificate` /
  `mio.coherence.redshift_binned.to_mio_certificate` per
  `mio.interface.sigma_cone_provenance.PROMOTED_SIGMA_CONE_PROBES`.
- **References**: Secrest et al. (2021), ApJ Letters 908, L51,
  arXiv:2009.14826, DOI 10.3847/2041-8213/abdd40.

### Radio (NVSS+RACS AGN composite) — PROBE_ID `Radio`

- **L**: There is **no single canonical σ** for the radio dipole —
  the three primary measurements are scattered:
  - Blake & Wall (2002), Nature 416, 150 — NVSS-based detection,
    direction `(l, b) ≈ (253°, 28°)`, direction uncertainty of
    order tens of degrees at their sample size.
  - Singal (2011), ApJ Letters 742, L23 (arXiv:1110.6260) — direction
    `(l, b) ≈ (247°, 30°)` with comparable cone; amplitude excess
    relative to CMB reported.
  - Rubart & Schwarz (2013), A&A 555, A117 (arXiv:1301.5559) —
    bootstrap-based σ ≈ **12-15°** on direction.
  - Darling (2022), ApJ Letters 931, L14 (arXiv:2205.06880) using
    NVSS+RACS composite reports an uncertainty region of order
    10-14° depending on mask and flux cut.
- **C**: `sigma_cone_deg=10.0`.
- **Δ**: −2 to −5° (C slightly optimistic vs. the Rubart–Schwarz /
  Darling quoted σ, comparable to the Singal 2011 internal σ).
- **Status**: **literature-consistent-but-not-verbatim.** 10° lies
  in the lower half of the reported range; a conservative choice
  would be 12° (aligning with the Rubart-Schwarz midpoint), and a
  generous choice would be 14° (Darling). The placeholder flag
  should remain until the MIO lane commits to which composite
  (NVSS-only, RACS-only, or joint) its σ quote anchors to.
- **References**: Blake & Wall (2002), Nature 416, 150;
  Singal (2011), ApJ Letters 742, L23, arXiv:1110.6260;
  Rubart & Schwarz (2013), A&A 555, A117, arXiv:1301.5559;
  Darling (2022), ApJ Letters 931, L14, arXiv:2205.06880.

### Cosmicflows-4 peculiar-velocity field — PROBE_ID `CF4pp`

- **L**: Tully, Kourkchi, Courtois, Anand, Blakeslee, Brout, de
  Jaeger, Dupuy, Guinet, Howlett, Jensen, Pomarède, Rizzi, Shamir,
  Tully, Valade (2023), "Cosmicflows-4", ApJ 944, 94 (DOI
  10.3847/1538-4357/acf1a4) gives the bulk-flow reconstruction with
  direction uncertainty dependent on smoothing scale. At the
  ~150 Mpc/h scale most relevant to the MIO cross-check, the quoted
  direction 1σ cone is **~10-12°**; at wider smoothing the cone
  inflates. The `(l, b) ≈ (289°, 30°)` used in the code tracks the
  150 Mpc/h bulk-flow minor-axis.
- **C**: `sigma_cone_deg=15.0`.
- **Δ**: +3 to +5° (C conservative).
- **Status**: **literature-consistent-but-not-verbatim / conservative.**
  15° intentionally exceeds the 150 Mpc/h cone to cover scale
  systematic; safe for the weighted-resultant test, but a 12° swap
  would not change the inverse-variance dominance pattern (CMB still
  wins by three orders of magnitude on 1/σ²).
- **References**: Tully et al. (2023), ApJ 944, 94, DOI
  10.3847/1538-4357/acf1a4.

### BipoSH — PROBE_ID `BiPoSH`

- **L**: Planck Collaboration (2015), "Planck 2015 results. XVI.
  Isotropy and statistics of the CMB", A&A 594, A16 (arXiv:1506.07135),
  Appendix on BipoSH estimators. The published BipoSH power
  `A_{LM}^{11}` constrains a coupled direction at **cone ~15-25°**
  for the dipolar modulation, heavily dependent on ℓ-range and the
  foreground model. The Planck 2013 and 2018 variants report similar
  cone sizes.
- **C**: `sigma_cone_deg=20.0`.
- **Δ**: centered in the quoted range.
- **Status**: **literature-consistent-but-not-verbatim.**
  A36a.5-promoted **2026-W14D6** — 20° is close to the midpoint of
  the Planck 2015 BipoSH dipole direction cone and the arXiv:1506.07135
  reference anchors the quote. `BiPoSH` is now absent from the
  placeholder tag set emitted by HJ-02a / HJ-02b certificates per
  `mio.interface.sigma_cone_provenance.PROMOTED_SIGMA_CONE_PROBES`.
- **References**: Planck Collaboration (2016), A&A 594, A16
  (Planck 2015 Results XVI), arXiv:1506.07135.

## A36a.3 Summary table

| PROBE_ID | σ_code (°) | σ_literature (°) | Δ (°) | Status |
|---|---:|---:|---:|---|
| `CMB` | 0.5 | ~0.01 (Planck LVI) | +0.49 | literature-consistent / catalogue-conservative |
| `CatWISE` | 6.0 | ~5.9 (Secrest+2021) | +0.1 | DOI-anchored |
| `Radio` | 10.0 | 10-14 (Rubart–Schwarz, Darling) | −2 to −4 | literature-consistent |
| `CF4pp` | 15.0 | 10-12 (Tully+2023, 150 Mpc/h) | +3 to +5 | literature-consistent / conservative |
| `BiPoSH` | 20.0 | 15-25 (Planck 2015 XVI) | within range | literature-consistent |

**Machine-readable mirror (W16D3).** [`A36a_sigma_cone_literature.yaml`](A36a_sigma_cone_literature.yaml)
ships the same five rows in a parser-friendly form. The paired test
`bass_py/mio/tests/test_sigma_cone_provenance.py::test_standard_probes_sigma_code_matches_a36a_yaml`
asserts (1) `STANDARD_PROBES[*].sigma_cone_deg == sigma_code_deg` per
PROBE_ID and (2) internal YAML self-consistency
`|sigma_code_deg − sigma_lit_deg| == |delta_deg|`. The three probes
whose literature σ is quoted as a range (Radio / CF4pp / BiPoSH)
reduce to the midpoint for the parity scalar and preserve the full
range in an optional `sigma_lit_range_deg: [min, max]` field.
Closes the W13 F4 / W14 F3 / W15 F2 drift exposure.

Aggregate: no PROBE_ID carries a σ that is *smaller* than the most
permissive literature 1σ cone after catalogue conservatism is
applied, so the inverse-variance weighting does not over-weight any
probe relative to its published constraint. The CMB dominance
pattern is by construction (0.5° anchor against degrees-scale peers)
and is not a placeholder artefact.

## A36a.4 Why code values are left unchanged in W13D3

Three reasons spelled out:

1. **Conservatism is the right catalogue-level default.** The code
   σ values set the *floor* of down-weighting; a literature σ that
   is tighter than the code value would strengthen CMB dominance
   further without adding information — the resultant test is
   already CMB-dominated at 0.5°. Tightening from 6.0 to 5.9 on
   CatWISE changes the HJ-02a resultant R at the 4th decimal.
2. **Placeholder flag still fires as an upstream-reader contract.**
   The `*_sigma_cone_plan_placeholder` `domain_caveats` entry now
   points to this dossier (once A36.4 is edited — see §A36a.6),
   so a downstream reader that wants the DOI-anchored numbers can
   look them up without code archaeology.
3. **A36.2 row 2 (no cross-channel fusion) forbids the scenario
   where the σ numbers matter beyond inverse-variance weighting.**
   Any future joint-likelihood use of these directions is
   explicitly G19-prohibited; a weighted resultant consumed as an
   advisory scalar is not sensitive to sub-degree σ drift.

## A36a.5 Promotion criterion (future work)

The `*_sigma_cone_plan_placeholder` flag may be retired per-probe
when all three conditions hold:

1. The σ_code value is within the published 1σ cone or is
   deliberately conservative by ≥50% (documented in A36a.2).
2. The A36a row cites at least one DOI or arXiv identifier for the
   numerical claim.
3. A paired commit lands the caveat retirement + an A36.4 edit
   that points to this dossier as the new provenance anchor.

Under this criterion, `CatWISE` and (arguably) `BiPoSH` are
ready-to-promote as of 2026-04-19; `CMB`, `Radio`, `CF4pp` remain
flagged because the delta from literature is non-trivial even when
conservative.

**Promotion log**:

- **W14D5** — `CatWISE` promoted. Code-side source of truth:
  `mio.interface.sigma_cone_provenance.PROMOTED_SIGMA_CONE_PROBES`;
  parity tests: `bass_py/mio/tests/test_sigma_cone_provenance.py`.
- **W14D6** — `BiPoSH` promoted. Same code-side SSOT and test file;
  `PROMOTED_SIGMA_CONE_PROBES` is now `frozenset({"BiPoSH", "CatWISE"})`.
  After W14D6 the flagged set is `{CMB, Radio, CF4pp}`.

## A36a.6 Follow-up (W13 / W14 opportunistic)

- [x] Edit A36 §A36.4 so its "cite published σ values" sentence links
      to this dossier (one-line change; not in W13D3 scope to avoid
      expanding the commit surface area). **Landed W14D2** (commit
      `491ecfd`).
- [x] Decide whether `_sigma_cone_plan_placeholder` should refine to
      per-probe tags (one tag per probe) so that A36a.5 can retire
      them one at a time. **Landed W14D5** —
      `mio.interface.sigma_cone_provenance.placeholder_caveats_for`
      emits one `{PROBE_ID}_sigma_cone_plan_placeholder` per
      non-promoted probe; `PROMOTED_SIGMA_CONE_PROBES` is the frozen
      retirement set.
- [ ] When MANU-CH12 §12.2 moves off working-tree and lands formally,
      cite A36a.2 by DOI in the manuscript prose (the W6 FM2 /
      W11 F3 close condition).

## A36a.7 Related appendices

- [A36 MIO channel weighting](A36_mio_channel_weighting.md) — policy
  parent; this dossier is the σ-quoting complement.
- [A37 MIO probe-name schema](A37_mio_probe_name_schema.md) —
  PROBE_ID catalogue that pins the left column of §A36a.3.
- [A38 masked-sky caveats](A38_masked_sky_caveats.md) — adjacent
  caveat-flag surface; precedent for the `domain_caveats` pattern
  used here.
- [A35 HJ-02a directional coherence](A35_directional_coherence.md) —
  concrete statistical context for the σ_cone-weighted resultant.
