# A40 · G19 architectural stance

**Appendix**: A40 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with DOS-A30-MIO Week 7 Day 7).
**Anchor rule**: v3 §4.5.4 "Hard separation" + v3 §10.2bis enforcement
matrix.
**Operational anchor**: [A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md).
**Related**: [A32 MioCertificate schema](A32_mio_certificate_schema.md);
[A39 per-module epistemic ownership](A39_per_module_epistemic_ownership.md).

---

## A40.1 Statement

G19 is the v3 architectural rule that **MIO, HTT, and TSC must never
be merged into a single score**. Each reports its own kind of truth
with its own contract, and the pipeline consumes all three
independently. Concretely:

1. **MIO** (`bass_py/mio/*`) reports what is directly visible in the
   data without assuming a model. Its output is a `MioCertificate`
   (see A32).
2. **HTT** (`bass_py/htt/htt/*`) reports posteriors under specific
   models. Its output is a posterior draw + log-evidence + matched-
   complexity report.
3. **TSC** (`bass_py/tsc/*`) reports physical realisability under the
   Paper I T_eff chart. Its output is a `RealizabilityReport` and
   the admissibility / filling-fraction / three-bound diagnostics.

These three domains may **cross-check** each other (TSC-06 ↔ HTT
filling fraction; HJ-04 evidence anatomy ↔ HTT ln B; HJ-02a directional
coherence ↔ HTT dipole likelihood) but they must never be summed,
averaged, or merged into a single scalar quality score.

## A40.2 Why this is non-negotiable

The v2 plan tried to centralise adequacy reporting in MIO. v3
identifies this as a category error:

> **Epistemic hygiene is not concentrated in any single module;
> each module is responsible for its own adequacy.** MIO reports
> *"what is directly visible in the data, without assuming a
> model"*, not *"what is true"*.

Four structural failures follow from a merge:

1. **Collapse of independent witnesses.** A bug that corrupts both
   sides identically becomes undetectable. TSC-06's whole point is
   to produce two numerically-comparable scalars from two
   independently implemented code paths; a merged score destroys
   that.
2. **Miscounting of shared uncertainty.** A merged F_Bayes does not
   reduce variance by a factor of √2 — both sides share the same
   (ε₁, ε₂, ε₃) posterior draw. Merged variance arithmetic is
   therefore pseudo-science.
3. **Contamination of HTT likelihoods.** Once MIO and HTT scores are
   fungible, nothing prevents a future PR from ingesting a MIO
   certificate as an HTT likelihood input — a direct G19 violation
   and a catastrophic loss of the model-independence guarantee.
4. **Destruction of the TSC realisability gate.** TSC's
   `RealizabilityReport` is Boolean (admissible / not). A merged
   score would force the Boolean into a continuous averaged field,
   corrupting the gate semantics.

## A40.3 Enforcement layers

G19 is enforced at four layers in the current codebase:

### A40.3.1 Type layer (frozen dataclass fields)

`workspace/contracts/mio_certificate.py::MioCertificate` has no
`posterior` field; the schema-hash freeze in
`test_miocertificate_schema_frozen` locks the field set. Any PR that
adds such a field breaks the hash.

`tsc/integration/htt_bridge.py::FFCrossCheckReport` exposes
`F_Bayes_tsc` **and** `F_Bayes_htt_mean` as two separate fields — never
a merged `F_Bayes_combined` field. Construction raises `ValueError`
if `is_cross_check` is set to `False`.

### A40.3.2 Generator-site layer (keyword scan)

`mio.interface.mio_certificate.build_mio_certificate` scans its
keyword arguments for the substring `"posterior"` and raises
`ValueError` before any instance is built. This catches the mistake
of passing `posterior_samples=...` to a MIO certificate builder
whether or not the schema already bans the field.

### A40.3.3 Ingestion-site layer (HTT likelihood refusal)

`test_htt_cannot_ingest_miocertificate_as_likelihood` asserts that
passing a `MioCertificate` instance to any `htt.*.log_likelihood`
entry point raises `TypeError`. The test catches the mistake of a
future PR treating a certificate as a posterior.

### A40.3.4 Repo-wide scan layer (scalar-sum lint)

`workspace/contracts/tests/test_g19_enforcement.py` runs a static
text scan across `bass_py/{bass, htt/htt, mio, src/common, tsc,
workspace}` production code for patterns like

    mio_score + htt_lnB
    np.mean([mio_score, htt_lnB])
    ...

and fails if any hit is found. The scan is conservative (regex-based)
and may produce false positives that must be whitelisted explicitly.

## A40.4 Legitimate cross-check channels

A40.3 bans the merge; A34 documents how to *cross-check* without
merging. Summarised here:

| Channel | Owner | Report type | Status |
|---|---|---|---|
| TSC-06 F_Bayes | `tsc.integration.htt_bridge` | `FFCrossCheckReport` (is_cross_check=True) | landed |
| HJ-04 evidence anatomy | `mio.decomposition.evidence_anatomy` | planned `MioCertificate(report_type="evidence_anatomy")` | deferred (Week 10+) |
| HJ-02a dipole alignment | `mio.coherence.directional` | `MioCertificate(report_type="directional_coherence")` | landed — advisory only (no numerical counterpart) |
| TSC-03 ↔ HTT bounds | `tsc.admissibility.three_bound_hierarchy` | `compare_against_htt_bounds(...)` | landed (sibling channel, rtol 1e-10) |
| TSC-05 ↔ bass MM SSOT | `tsc.charts.michaelis_menten_export` | `assert_mirror_matches_bass_ssot()` | landed (sibling channel, rtol 0) |

Each row of the above is code-enforced: the dataclass or guard
function carries the `is_cross_check=True` tag or equivalent (TSC-03
uses `all_agree`; TSC-05 uses `assert_mirror_matches_bass_ssot`).

## A40.5 Deprecated v2 vocabulary

The v2 plan described MIO as a *"certification engine"* or *"truth
attestation layer"*. These terms are **banned** under v3:

| v2 term | v3 replacement | Rationale |
|---|---|---|
| "certification engine" | "Model-Independent Observatory" | MIO reports diagnostics, not attestations. |
| "truth attestation" | "departure-variable reporting" | Truth claims belong to the model, not the observatory. |
| "epistemic control" | "distributed ownership" | No single module owns adequacy (A39). |
| "identified vs reporting" | "adequacy certificate" | Reflects the v3 `MioCertificate.reduction_status` field. |

A banned-vocabulary scan is wired into the MANU-CH11 / MANU-CH12
commit hook (Week 8 pending) to prevent regression into v2 language.
Meanwhile, the `legacy/README.md` banner (landed W5D7) flags any v2
MIO snapshot the reader might encounter in `legacy/mio/*`.

## A40.6 Failure modes a relaxation would introduce

A40.2 lists the four high-level structural failures. At the pipeline
level, relaxing G19 would also cause:

- **HTT-OBS drift.** If MIO observational defaults (probe directions,
  σ_cone values) leak into HTT likelihoods as priors, the HTT
  posterior becomes prior-dominated and the model-independence
  principle collapses.
- **TSC-03 / TSC-05 regression leakage.** Both are sibling
  cross-checks that assert bit-identity with htt / bass SSOT. If
  any merge path creates an "average" coefficient, both regressions
  fail simultaneously and the coefficient drift becomes ambiguous
  — the tester cannot tell which side drifted.
- **Misuse of `legacy/mio/`.** The v2 snapshot in `legacy/mio/`
  contains "certification engine" vocabulary by design; the legacy
  banner calls this out. A merge that silently imports from the
  v2 tree would re-introduce the retired architecture.

## A40.7 How to extend this dossier

When a new MIO diagnostic lands that exposes a numerical
cross-check (e.g. HJ-04 evidence anatomy), §A34.7 specifies the
five requirements the new channel must meet (independent code
paths, frozen `is_cross_check` tag, loud-fail guard, no merge field,
test anchor). A40.4 must be updated to add the new row once the
channel lands. The reverse direction — relaxing §A40.3 or
§A40.4 — is architecturally forbidden without a v4 plan revision.

## A40.8 Related appendices

- [A32 MioCertificate schema](A32_mio_certificate_schema.md)
- [A33 HttForwardOutput + AtlasEntry schema](A33_htt_forward_output_atlas_entry.md)
- [A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md)
- [A35 MIO directional coherence](A35_directional_coherence.md)
- [A38 masked-sky caveats](A38_masked_sky_caveats.md)
- [A39 per-module epistemic ownership](A39_per_module_epistemic_ownership.md)
