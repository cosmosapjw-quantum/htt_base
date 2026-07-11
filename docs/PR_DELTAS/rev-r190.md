# REV-R190 — MESb web-trace + refutation of the in-house non-geodesic bounds

## Context

Owner directive (2026-07-12): web-search the original MESb (Paper II,
Phys. Rev. D 51, 5942), trace the derivation as far as accessible, and within
the accessible range re-derive/correct or **refute** the wrong parts, then
re-freeze like the existing MES cycle. Two candidate anchors were to be
adversarially verified and the survivor adopted; manuscript ch04 to be
corrected.

## What the web-trace established

Three accessible primary sources re-fetched (2026-07-12) and SHA-archived
(clean `pdftotext -layout` extractions added):

| Source | arXiv | Role |
|--------|-------|------|
| MESa | astro-ph/9501016 | geodesic (u̇=0); eq 60 ω=(10/3,2/15,0); no accel bound |
| ΔT/T companion | astro-ph/9510126 | all-three-MES-authors; presents the MESb reduced bounds |
| SAG 1997 | astro-ph/9904346 | clean LaTeX eq 4 ω=(10/3,2/15,0); ε₁=0 (eq 12) |

- σ = (5/3,3,3/7): confirmed by three sources (MESa eq 59, companion eq 7,
  SAG eq 3). Unchanged.
- Geodesic ω = (10/3,2/15,0): confirmed verbatim by MESa eq 60 + SAG eq 4 +
  the C1/C2 reduction. No acceleration bound (both papers geodesic).
- Companion eq (6) raw shear is labelled "MESb Eq (24)" and equals MESa
  eq (51) identically; companion eq (8) gives the reduced ω/Θ < α×10⁻⁵ with
  α×10⁻⁵ = max(ε₂,ε₃) (assumption (c)).

## The refutation (headline)

The previously-registered non-geodesic **ω = (3/4,2,2/7)** and
**accel = (3/4,1,3/14)** are **REFUTED**:

- **Robust (α-independent) ground:** they appear in NO accessible source.
  Their in-repo origin is an in-house reconstruction
  (`docs/ver2_upgrade/mes_full_covariance_extension_self_contained.md` +
  manuscript ch04); the "Thm 3.2/Eq 3.12" labels are in-house numbering, not
  MESa/MESb equations.
- **Secondary (reading-dependent) corroboration:** at ε₁=0, the in-house
  B_ω = 8.85×10⁻⁶ exceeds the companion's faithful cap max(ε₂,ε₃) = 6.07×10⁻⁶
  by ~1.46× (it does fit the loose COBE α~1 cap, so this corroboration is
  reading-dependent).
- The accel bound has no accessible source at all (both primary papers
  geodesic).

## Adversarial verification (five refute-prompted lanes) + adjudication

- **GEODESIC anchor W2_max = 3.3789×10⁻¹³: SURVIVES** — exact, triply
  primary-sourced; only the geodesic frame + ε₁=0 convention are registered
  caveats (the number is airtight).
- **COMPANION non-geodesic envelope: PLAUSIBLE, order-of-magnitude only.** The
  adversary surfaced a real P1: the earlier ε₂ nominal (1.90×10⁻¹¹)
  **understated** the ceiling — the companion's own assumption (c) pins
  α×10⁻⁵ to *max*(ε₂,ε₃)=ε₃, so the faithful cap is (3/2)ε₃² = 5.52×10⁻¹¹
  (COBE α~1 → 1.50×10⁻¹⁰). Corrected in the module + all surfaces.
- **ADOPTED:** geodesic 3.3789×10⁻¹³ stays the LIVE anchor (unchanged value,
  now web-traced + adversarially survived); companion 5.52×10⁻¹¹ disclosed as
  the non-geodesic branch; in-house refuted.

## Manuscript ch04 correction (owner-approved)

- `thm:MES-omega` → geodesic ω = (10/3,2/15,0) with primary citation; ε₁→0
  collapses it to (2/15)ε₂. Invented "Δℓ=1 coupling" derivation prose removed.
- `thm:MES-udot` → geodesic congruence has no acceleration ceiling (A²=0);
  the (3/4,1,3/14) is superseded.
- `prop:ordering` → the shear–vorticity ordering B_σ > B_ω is now stated as
  **conditional** on ε₁ < ε₁_crit = (43/25)ε₂ + (9/35)ε₃ ≈ 7.68×10⁻⁶ (the
  geodesic ω's larger ε₁-coefficient 10/3 makes it overtake B_σ at the full
  observed dipole), with the residual-dipole convention flagged load-bearing.
- Std-form + constraint-inventory A² ceiling → 0 (geodesic).
- Cross-chapter one-liners asserting the old universal three-bound ordering
  corrected in ch03 (rem:hierarchy-conservation) and ch06 (cross-checks).
- Registered follow-up (open-items rank 1): the downstream Saadeh–MES gap
  magnitude (ch09 subsection, ch04 atlas) needs recomputation against the
  geodesic W2_max (~8–9 OOM, was quoted ~6).

## Artifacts

- `htt/obsstat/egs3_mesb_web_trace.py` + `wolfram/mesb_web_trace.wls`
  (cross-engine PASS); seal runner → `mesb_web_trace_seal.json` +
  `mesb_web_trace_wolfram_seal.json`.
- `research_gates/egs3/tests/test_egs3_axis_g_mesb_web_trace.py` (10 gates).
- `docs/audits/mes_primary_sources/PROVENANCE_M4b.md` + archived clean layouts
  + updated SHA256.
- Registry +MES-MESB-TRACE (65 entries, ACTIVE); CLAIM_LEDGER
  +egs3.mesb_web_trace; results table v9 → 67 rows; ticket
  `mes_full_rederivation` → `web_traced_in_house_refuted_geodesic_readopted`;
  open-items ledger → 8 items; v9 report rebuilt in place (new MES-MESB-TRACE
  subsection + corrected ε-provenance paragraph).

## Discipline

Frozen `three_bound_hierarchy` (W2_max = 1.3087×10⁻⁶) byte-identical (v5–v8
reproducibility); x_C untouched (W2_max is the admissibility ceiling, not an
x_C input); diagnostic-only; no observational claim. The adversarial ledger
stays internal (`docs/generated/`), never rendered into the report.
