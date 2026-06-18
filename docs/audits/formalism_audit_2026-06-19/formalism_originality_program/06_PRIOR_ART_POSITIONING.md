# 06 — Prior-Art Positioning (CRAG)

Where the formalism's originality sits, on two axes: the **reproducibility-methodology** axis (the firewall/contracts) and the **anisotropy-statistics** axis (the diagnostics). Status: ✅ verified current · ⚠️ differentiate.

---

## Map

```
 REPRODUCIBILITY METHODOLOGY (the enforcement layer)        ANISOTROPY STATISTICS (the diagnostics)
 ──────────────────────────────────────────────            ───────────────────────────────────────
 Blinding (DES Y1/Y3/Y6: catalog/data-vector/         ✅    MES kinematic bounds (per-mode shear/vort)  ✅
   parameter level; commit-on-unblind) ⚠️                   1+3 covariant anisotropy (Maartens/Ellis)   ✅
 Pre-registration / registered reports ⚠️                   Saadeh 2016 (CMB Bianchi test)              ✅
 Multiverse / specification-curve analysis                  Tsagas tilted-cosmology (depth/z structure) ✅
   (Steegen 2016; Simonsohn) ⚠️                              ratio-to-bound occupancy (Omega_k/Omega_k,max)
 Garden of forking paths / researcher                       tomographic dipole (boost vs tilt z-template)
   degrees of freedom (Gelman & Loken 2013) ✅
 Provenance / reproducibility infra (hashes,
   schema validation, lineage) ✅
```

## What is genuinely new (delineated against each neighbor)

| Neighbor | What they do | What the formalism adds (the gap) |
|---|---|---|
| **Blinding** (DES) | Hide results (catalog/data-vector/parameter) to protect analysis *choices* from confirmation bias | A **semantic firewall on the diagnostics' labels** — refuses to *mislabel* a diagnostic as evidence/occupancy/geometry/family. Complementary, not overlapping: blinding protects choices, the firewall protects claims (F1) |
| **Pre-registration / registered reports** | Commit to analysis/thresholds in advance | **Typed, in-object** threshold pre-registration (`Π`: registration_hash, anti-post-hoc), enforced at construction, not by editorial process (F4) |
| **Multiverse / specification-curve** (Steegen 2016; Gelman & Loken) | Enumerate defensible forks; report the outcome distribution | **Encode the forks as typed policy fields** (comparator/numerator/denominator/threshold/measure-kind) with provenance, *and* refuse over-claimed constructions, *and* enforce a diagnostic↔inference boundary — none of which multiverse reporting does (F1/F4/F6; U5) |
| **Provenance/reproducibility infra** | Track lineage, validate schemas | A **certification semantics** (`F` exists iff sign-clean + admissible ceiling, no clipping) and a **fail-closed** posture, beyond passive lineage (F3) |
| **MES / 1+3 covariant** | Bound modes separately; covariant anisotropy variables | A **single signed comparator projection** with a **cancellation invariant** that prevents `x_C≈0` reading as isotropy (F2/F7) |
| **Saadeh 2016 / Tsagas** | CMB Bianchi test; tilted-cosmology depth/z structure | A **matter-sector, depth-resolved diagnostic** with a denominator-evolution split and a boost-vs-tilt depth-template forecast (F5; U4/E4) |

**One-sentence originality claim:** *We operationalize three reproducibility disciplines — specification-curve/multiverse reporting, anti-post-hoc threshold registration, and provenance — as typed, machine-checked contracts on a family of FLRW-departure diagnostics, and add two contributions with little precedent: a semantic firewall that structurally refuses to construct an over-claimed diagnostic, and a typed diagnostic↔inference boundary that prevents diagnostics from being laundered into evidence.*

## Strategic citations

- Cite **Gelman & Loken 2013** (garden of forking paths) and **Steegen et al. 2016** (multiverse) as the conceptual motivation, then state precisely what is *encoded* vs *added* (the firewall + the boundary).
- Cite **DES blinding** (Y1 2017 / Y3 2021 / Y6 2026) as the cosmology-side bias-control prior art, and position the firewall as complementary (label-protection vs choice-protection).
- On the physics side, cite **MES**, **Saadeh 2016**, and **Tsagas** for the departure variables and the depth/z structure that `G_F`/U4 build on; link `G_F`'s depth-template discriminant to the tomographic boost-vs-tilt forecast.

This positioning inoculates against the two most likely referee moves — "multiverse already does this" (O2) and "blinding already does this" (O3) — by stating the exact, defensible delta: encoded forks + a refuse-to-overclaim firewall + a typed diagnostic↔inference boundary.

*(Verified via search June 2026: DES blinding protocols Y1/Y3/Y6; multiverse analysis & garden-of-forking-paths literature current through 2026. Physics-side references carried from the manuscript's verified bibliography.)*
