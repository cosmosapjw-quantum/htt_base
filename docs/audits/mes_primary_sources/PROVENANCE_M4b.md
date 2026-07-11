# M4b — MESb web-trace + refutation of the in-house non-geodesic bounds

Supersedes the "print-only / not reconstructable" disposition of PROVENANCE_M4
for the ω/accel coefficients. Owner directive (2026-07-12): web-search the
original MESb (Paper II, PRD 51 5942), trace the derivation, and within the
accessible range re-derive/correct or **refute** the wrong parts, then re-freeze.

Ticket: `docs/research_program/egs3/tickets/mes_full_rederivation.yaml`.
Seal: `htt/obsstat/egs3_mesb_web_trace.py` + `wolfram/mesb_web_trace.wls`.

## Sources (web-fetched 2026-07-12, archived + SHA-pinned in this directory)

| Tag | arXiv | Role |
|-----|-------|------|
| **MESa** | `astro-ph/9501016` (PRD 51,1525) | geodesic (u̇=0, eq 11); eq 59 σ, eq 60 ω; NO accel bound |
| **companion (ΔT/T)** | `astro-ph/9510126` | all-three-MES-authors; presents the MESb reduced bounds |
| **SAG 1997** | `astro-ph/9904346` (ApJ 476,435) | Stoeger co-author; clean LaTeX eq 3 σ, eq 4 ω; ε₁=0 (eq 12) |
| **MESb** | PRD 51,5942 — **print-only** | accessible only via the companion reduced bounds |

Clean `pdftotext -layout` extractions added: `*_layout.txt`.

## What the trace establishes

1. **σ = (5/3, 3, 3/7)** — confirmed by THREE accessible sources
   (MESa eq 59, companion eq 7, SAG eq 3) and reproduced bit-exact by the
   frozen C1/C2 reduction of MESa eq 51. Unchanged.
2. **Geodesic ω = (10/3, 2/15, 0)** — confirmed verbatim by TWO primary
   sources (MESa eq 60, **SAG eq 4** clean LaTeX). Reproduced bit-exact by
   reducing MESa eq 52. NO acceleration bound in either (both geodesic).
3. **MESb eq (24) ≡ MESa eq (51)** — the companion labels its raw σ bound
   "MESb Eq (24)" and it is *identical* to MESa eq (51). So MESb's raw
   bounds coincide with MESa's; relaxing the geodesic assumption did not
   blow up the reduced bounds.
4. **Companion eq (8)** (the MES team's own MESb reduced limits):
   `σ/Θ|₀ < 4α×10⁻⁵`, `ω/Θ|₀ < α×10⁻⁵` (ε₁→0; ε₂~ε₃~α×10⁻⁵), with the
   prose "the limit on the relative vorticity is comparable to that on
   distortion".

## The refutation (headline)

The previously-registered non-geodesic **ω = (3/4, 2, 2/7)** and
**accel = (3/4, 1, 3/14)** are NOT from MESb. Their in-repo origin is an
**in-house reconstruction** — `docs/ver2_upgrade/mes_full_covariance_extension_
self_contained.md` and `docs/manuscript/ch04_bianchi_bounds.tex` — whose
"Thm 3.1–3.4 / Eq 3.7/3.12/3.15" labels are **in-house numbering**, not
MESa/MESb equation numbers. These values:

- **PRIMARY (α-independent) ground:** they appear in **no accessible source**
  (MESa, companion, SAG all checked); the "Thm 3.2/Eq 3.12" labels are
  in-house numbering, not MESb's.
- **Secondary corroboration (reading-dependent):** at ε₁ = 0,
  `B_ω,in-house = 2ε₂ + (2/7)ε₃ = 8.85×10⁻⁶`, which **exceeds** the companion's
  *faithful* cap `α×10⁻⁵ = max(ε₂,ε₃) = ε₃ = 6.07×10⁻⁶` (assumption (c),
  companion line 219) by ~1.46×. It *does* fit the loose COBE reading
  (α ~ 1 → 1×10⁻⁵), so this corroboration is reading-dependent; the
  no-source ground is the robust one.

→ **REFUTED**, not merely "print-only / not reconstructable" (the PROVENANCE_M4
disposition). The in-house acceleration bound has no accessible source at all
(both accessible primary papers are geodesic and carry no accel bound).

## The two candidate re-freeze anchors (adjudicated by adversarial verification)

| Anchor | W²_max | basis | verdict |
|--------|--------|-------|---------|
| **A geodesic** (LIVE) | 3.3789×10⁻¹³ | MESa eq 60 + SAG eq 4, exact; ε₁=0 | **SURVIVES** (precise) |
| **B companion envelope** | 5.52×10⁻¹¹ faithful (α~1 → 1.50×10⁻¹⁰) | companion eq 8 non-geodesic ω, `α×10⁻⁵ = max(ε₂,ε₃)` | **PLAUSIBLE** (order-of-magnitude; disclosed) |
| ~~in-house~~ | ~~1.18×10⁻¹⁰~~ | ~~in-house (3/4,2,2/7)~~ | **REFUTED** |

Five refute-prompted lanes ran (2026-07-12): the geodesic anchor SURVIVES a
hostile attack on the reduction, frame, and ε₁=0 convention (the number is
exact and triply-sourced); the companion envelope is PLAUSIBLE but
order-of-magnitude — the adversary confirmed the earlier ε₂ nominal
(1.90×10⁻¹¹) **understated** the ceiling (assumption (c) pins α×10⁻⁵ to
*max*(ε₂,ε₃)=ε₃), corrected here to the faithful 5.52×10⁻¹¹ with the COBE
α~1 endpoint disclosed. **Adopted LIVE anchor: geodesic 3.3789×10⁻¹³**
(unchanged from the prior cycle; now web-traced + adversarially survived);
companion envelope disclosed as the non-geodesic branch; in-house refuted.
The frozen `three_bound_hierarchy` (W2_max = 1.3087×10⁻⁶) stays byte-identical;
x_C is untouched (W2_max is the admissibility ceiling, not an x_C input).
