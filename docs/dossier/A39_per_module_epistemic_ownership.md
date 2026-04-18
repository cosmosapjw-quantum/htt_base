# A39 · Per-module epistemic ownership

**Appendix**: A39 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with DOS-A30-MIO Week 5 Day 7).
**Primary reference**: v3 §0.1bis — "Epistemic control은 '분산 소유'다".
**Related**: [A32 `MioCertificate` schema](A32_mio_certificate_schema.md);
[A33 HttForwardOutput + AtlasEntry schema](A33_htt_forward_output_atlas_entry.md);
v3 §4.5.4 (G19 Hard separation rule).

---

## A39.1 Motivating principle

v2 of the research plan described MIO as an *"epistemic control / post-hoc
certification"* layer that centralised all adequacy reporting for the
project. v3 identifies this as a category error:

> **Epistemic hygiene is not concentrated in any single module; each
> module is responsible for its own adequacy.** MIO reports *"what is
> directly visible in the data, without assuming a model"*, not *"what
> is true"*.

Concretely: the solver tells you whether the numerics are trustworthy;
`tsc.admissibility` tells you whether a configuration is physically
realisable; `htt.infer` tells you whether a model's posterior passes
matched-complexity / LOOCV / PPC; `mio.diagnostics` tells you whether
the data is consistent with the model's adequacy claims *without
referencing any specific model*. Each produces its own artefact
(`RuntimeGate`, `RealizabilityReport`, `MatchedComplexityReport`,
`MioCertificate`) and each is consumed independently downstream — they
are never summed into a single master score.

## A39.2 Ownership table (canonical)

| Epistemic domain | Primary owner | Secondary contributors | Governing contract | Key test |
|---|---|---|---|---|
| Forward-solver numerical fidelity | `bass.runtime.*` | — | `RuntimeGate`, W3 Σ² floor | `bass/**/test_runtime_gate_*.py` |
| Solver-internal 3-tier claim labels | `bass.runtime.claims` | `bass.scripts.make_physics_gallery` | tier enum | gallery regen gate |
| Physical realisability (admissibility) | `tsc.admissibility.*` | `tsc.diagnostics.tangency` | `RealizabilityReport` | `bass_py/tsc/admissibility/test_realizability*.py` |
| Tangency / entropy invariants | `tsc.diagnostics.tangency` | `tsc.admissibility` | invariant dict | `bass_py/tsc/diagnostics/test_tangency*.py` |
| Posterior adequacy (model-dependent) | `htt.infer.matched_complexity` | `htt.infer.null_competition`, `htt.advanced_diagnostics.*` | `MatchedComplexityReport` | `bass_py/htt/tests/test_matched_complexity.py` (roadmap) |
| Posterior predictive checks | `htt.advanced_diagnostics.PosteriorPredictive` | — | `PPCReport` | `bass_py/htt/tests/test_advanced_diagnostics.py` (roadmap) |
| Null-competition FPR | `htt.infer.null_competition` | `htt.nulls.runner` | `NullCompetitionReport` | `bass_py/htt/tests/test_nulls.py` |
| Cross-channel coherence / LOOCV | `htt.advanced_diagnostics` | — | bespoke report dict | (roadmap) |
| Model-independent diagnostic reporting | `mio.diagnostics.adequacy_certificates` | all `mio.*` modules | [`MioCertificate`](../../bass_py/workspace/contracts/mio_certificate.py) | [test_mio_certificate.py](../../bass_py/workspace/contracts/tests/test_mio_certificate.py) |
| Directional cross-probe coherence | `mio.coherence.directional` | — | `MioCertificate(report_type="directional_coherence")` | (Week 6) |
| Non-parametric Σ² / β² extraction | `mio.extraction.*` | consumes `AtlasEntry` | `MioCertificate(report_type="shear_extraction")` | (Week 6+) |
| FLRW tension metric (PPP, x_C) | `mio.tension.*` | — | `MioCertificate(report_type="flrw_tension")` | (Week 6 dep) |
| Evidence anatomy (HTT ln B decomposition) | `mio.decomposition.evidence_anatomy` | consumes HTT posteriors as CROSS-CHECK | `MioCertificate(report_type="evidence_anatomy")` | (Week 6 dep) |
| Predictive residuals (where models fail) | `mio.diagnostics.predictive_residuals` | — | `MioCertificate(report_type="predictive_residuals")` | (Week 6) |
| Sky-coverage / mask-propagation caveats | `mio.diagnostics.masked_sky_caveats` | — | `SkyCoverageReport` → `domain_caveats` | (Week 6) |
| Interface semantics boundary | [`bass_py/workspace/contracts/`](../../bass_py/workspace/contracts/) | all packages | 4 frozen dataclasses | [contracts/tests/](../../bass_py/workspace/contracts/tests/) |
| Production-axis gate | `bass_py/src/common/contracts.py` `PreferredAxis` | `htt.PR13AJ_full_a2m_restoration` | `PreferredAxis.production_allowed` | `bass_py/htt/tests/test_PR13AJ_gate.py` |
| Four-summary integrity (raw / zoa / selection / mock) | `htt.PR13AH_observables_reintegration` | consumes COMMON-F | `ChannelSummary` | [test_PR13AH.py](../../bass_py/htt/tests/test_PR13AH.py) |
| MIO bridge semantic tag | `htt.PR13AM_te_sign_d1d3_bridge` (`__mio_owned__`) | — | module flag | [test_PR13AM_production_gate.py](../../bass_py/htt/tests/test_PR13AM_production_gate.py) |

## A39.3 What this table is NOT

- **Not a dependency graph** — many of these modules are mutually
  independent and only communicate through the `workspace/contracts/`
  interface objects. See [A33](A33_htt_forward_output_atlas_entry.md)
  for the actual data-flow.
- **Not a merge table** — the G19 rule forbids summing outputs across
  rows. HTT's `MatchedComplexityReport` and MIO's `MioCertificate` are
  *cross-checked*, not combined.
- **Not a license to duplicate** — each row identifies the *primary*
  owner. Other modules that need the same information MUST import from
  the owner, not re-implement.

## A39.4 G19 first-line defences

v3 §12.2bis identifies three semantic first-line-defence mechanisms that
this ownership structure relies on:

1. **Filename prefix**: MIO artefacts MUST begin with `mio_`
   (`mio_directional_coherence_v1.json`, `mio_pr13am_te_sign_v1.json`).
   Enforced by
   [test_reg02_artifact_prefix.py](../../bass_py/workspace/contracts/tests/test_reg02_artifact_prefix.py).
2. **Module tag**: MIO-owned modules physically located in other
   packages carry `__mio_owned__ = True` plus a `__mio_rationale__`
   string. Currently: `htt.PR13AM_te_sign_d1d3_bridge`.
3. **Schema token ban**: The string `'posterior'` is forbidden in any
   field name on the non-HTT contracts (`MioCertificate`, `AtlasEntry`,
   `HttForwardOutput`). Enforced by
   [test_g19_enforcement.py](../../bass_py/workspace/contracts/tests/test_g19_enforcement.py).

## A39.5 Historical note

The v2 text referred to MIO as an *"epistemic control / post-hoc
certification engine"*. All such phrases are v2 mis-statements and will
be removed during the MANU-CH11-REDESIGN track (Week 8). The
[legacy/](../../legacy/) tree preserves the v2 snapshot for history; the
banner added by LEGACY-README (v1.2 §19.6) warns against treating
[legacy/mio/](../../legacy/mio/) as active code.

## A39.6 Maintenance

This table is authoritative. Any new module added to `bass_py/` must:

1. Fit into an existing row *or* justify a new row in this table via a
   short audit note in `docs/audits/`.
2. Expose its outputs as a frozen dataclass (under
   `bass_py/workspace/contracts/` if cross-package, under its own
   package otherwise).
3. Ship with at least one test under `tests/` that asserts the
   contract's immutability and any required G19 guards.
