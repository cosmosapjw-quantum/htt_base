# A38 · Masked-sky caveats (HJ-05a-lite)

**Appendix**: A38 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with DOS-A30-MIO Week 7 Day 7).
**Code anchor**: [`bass_py/mio/diagnostics/masked_sky_caveats.py`](../../bass_py/mio/diagnostics/masked_sky_caveats.py)
**Support library**: [`bass_py/src/common/healpix_selection.py`](../../bass_py/src/common/healpix_selection.py)
**Parent references**: v3 §4.5.3.5 (HJ-05a); INDEPENDENT_TRACKS_PLAN
v1.2 §12.6 (MIO-HJ-05a-lite landing, Week 6 Day 7).

---

## A38.1 Purpose

HJ-05a-lite materialises the sky-coverage caveats (effective
`f_sky`, ZoA half-angle, ecliptic-pole gap, mask provenance) that
feed the `domain_caveats` field of a `MioCertificate`. The module
consumes **data only** — no HTT posterior, no bass_py forward — which
is why this "lite" slice ships inside Week 6 before the full HJ-05
stack that depends on bass_py forward outputs.

Output object: `SkyCoverageReport` with a `caveats` list directly
consumable as `MioCertificate.domain_caveats`.

## A38.2 Definitions

`f_sky_effective` is the straight pixel-count ratio

    f_sky_effective = n_pix_kept / n_pix_total,

kept as an integer-ratio-routed float so bit-identical mocks produce
bit-identical values across Python / numpy version changes.
Solid-angle-weighted variants (`f_sky_solid` with per-pixel area
weights from `healpy.nside2pixarea`) belong to the full HJ-05
landing in Week 8+; HJ-05a-lite deliberately does not ship them.

`zoa_half_angle_deg` is the Zone-of-Avoidance cut applied to
`|b_galactic|` during mask construction (via
`common.healpix_selection.build_zoa_mask`). Values of 15°, 20°, and
30° are the standard ladder; the REG-01 `test_zoa_ladder_no_fallback_leak`
anchor asserts that mask construction never silently falls back to
full-sky when a nonzero cut is requested.

`ecliptic_pole_gap_deg` is the optional polar cap exclusion around
the ecliptic poles (dominant for IRAS / WISE foregrounds); set to
`None` when no polar cut is applied.

`mask_provenance` is a free-form string identifying the mask origin
(e.g. `"Planck_SMICA_common_mask_2018"`). Present in the caveats
list so downstream reviewers can re-trace the mask pedigree without
re-running the full pipeline.

## A38.3 Caveat generation rules

The `build_report` helper auto-generates caveats under the following
conditions, in order:

| Trigger | Caveat string |
|---|---|
| `f_sky_effective < 1.0` and `zoa_half_angle_deg is not None` | `"masked_sky_partial"` |
| `zoa_half_angle_deg is not None` | `"zoa_half_angle_{x}_deg_applied"` (x = float value) |
| `ecliptic_pole_gap_deg is not None` | `"ecliptic_pole_gap_{x}_deg_applied"` |
| `mask_provenance != "unknown"` | `"mask_source_{provenance}"` |
| caller-supplied `extra_caveats` | appended verbatim after the auto set |

These rules are test-anchored in
`bass_py/mio/tests/test_masked_sky_caveats.py`. The caveats list is a
plain `list[str]` to match the `MioCertificate.domain_caveats`
schema (v3 §4.5.2.1).

## A38.4 Integration into MioCertificate

```python
from mio.diagnostics.masked_sky_caveats import build_report
from common.healpix_selection import build_zoa_mask, nside_to_npix

nside = 64
mask_pix = build_zoa_mask(nside=nside, bcut_deg=20.0)
report = build_report(
    mask_pix=mask_pix,
    nside=nside,
    zoa_half_angle_deg=20.0,
    mask_provenance="Planck_SMICA_common_mask_2018",
)
# report.caveats is now directly consumable as
#   MioCertificate(..., domain_caveats=report.caveats, ...)
```

The `SkyCoverageReport` itself is **not** a `MioCertificate`; it is a
staging dataclass that feeds the caveats list. The primary MIO
diagnostic (`mio.coherence.directional`, `mio.extraction.*`, …)
builds the certificate and pulls the caveats in.

## A38.5 What HJ-05a-lite does NOT do

- **No power-spectrum mask-mode-coupling matrix** (M_ℓℓ'). Full
  HJ-05 will provide the Wigner-3j coupling matrix for
  pseudo-C_ℓ correction; HJ-05a-lite reports only that a mask was
  applied, not its spectral response.
- **No selection-function weighting.** The Wiener-filter / inverse-
  variance reweighting lives in `common.healpix_selection` and is
  reported separately by the COMMON-B / COMMON-C diagnostics
  (REG-01 `test_weights_decomposition_logged`).
- **No bass_py forward propagation.** The full HJ-05 diagnostic
  couples the mask to the bass_py K_ℓ atlas (W10-02 dependency);
  HJ-05a-lite is the bass-free precursor.

## A38.6 Known placeholder behaviours

- Caveat string formatting is stable (`"zoa_half_angle_20.0_deg_applied"`
  rather than `"20 deg"`) so mock-data downstream tests can `grep`
  for exact substrings. A future MANU-CH12-NEW §12.2 update may
  switch to a structured `{key: value}` mapping; that would be a
  `SkyCoverageReport` schema bump and must coordinate with
  `MioCertificate.domain_caveats` which is a plain string list.
- The mask is always evaluated at a single nside. Multi-resolution
  masks (e.g. nside=2048 for Planck, nside=64 for CF4 galaxy-count
  cross-correlation) must be rendered at each nside separately.

## A38.7 Related appendices

- [A32 MioCertificate schema](A32_mio_certificate_schema.md) — where
  `domain_caveats` is defined.
- [A35 MIO directional coherence](A35_directional_coherence.md) —
  first consumer of the HJ-05a-lite caveats (HJ-02a populates its
  certificate's `domain_caveats` from this report).
- [A39 per-module epistemic ownership](A39_per_module_epistemic_ownership.md)
  — the row "Sky-coverage / mask-propagation caveats".
- `common/healpix_selection.py` REG-01 anchor — the
  zero-fallback-leak guarantee HJ-05a-lite inherits.
