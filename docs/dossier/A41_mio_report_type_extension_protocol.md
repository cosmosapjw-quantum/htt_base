# A41 · MIO `report_type` extension protocol

**Appendix**: A41 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with DOS-A30-MIO Week 12 Day 5).
**Code anchors**:
[`bass_py/workspace/contracts/mio_certificate.py`](../../bass_py/workspace/contracts/mio_certificate.py)
(schema contract);
[`bass_py/mio/interface/mio_certificate.py`](../../bass_py/mio/interface/mio_certificate.py)
(generator API);
[`bass_py/workspace/contracts/tests/test_g19_enforcement.py`](../../bass_py/workspace/contracts/tests/test_g19_enforcement.py)
(posterior-token ban).
**Parent references**:
v3 §4.5.2.1 (MioCertificate dataclass body);
v3 §4.5.4 (G19 hard separation);
v3 §10.2bis (enforcement matrix);
[W7 FM3](../audits/AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md#w7-fm3)
(schema-hash vs. literal-version freeze);
[A32 MioCertificate schema](A32_mio_certificate_schema.md);
[A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md);
[A37 probe-name schema](A37_mio_probe_name_schema.md);
[A39 per-module epistemic ownership](A39_per_module_epistemic_ownership.md).

---

## A41.1 Purpose

The `MioCertificate.report_type` field is a `str` that distinguishes
which MIO diagnostic produced the certificate. As of Week 11 three
values are in active use — `"shear_extraction"` (HJ-01),
`"directional_coherence"` (HJ-02a), `"redshift_binned_coherence"`
(HJ-02b) — and the v3 plan reserves four more —
`"evidence_anatomy"` (HJ-03), `"flrw_tension"` (HJ-04),
`"predictive_residuals"`, `"adequacy_certificate"`. When bass_py
W10-02 (K_ℓ atlas) and W11-02 (BiPoSH) V-gates pass, the HJ-03 and
HJ-04 modules will both want to land new `report_type` strings.

Adding a new `report_type` is *not* a schema version bump — the v1
schema hash must remain stable so that (a) the W7 FM3 literal freeze
in [`tsc.charts.michaelis_menten_export`](../../bass_py/tsc/charts/michaelis_menten_export.py)
remains valid, and (b) cross-check readers (A34 catalogue) keep
parsing W1–W11 cert files without modification. This dossier fixes
the **extension protocol** so HJ-03 / HJ-04 authors can land a new
report_type with a mechanical checklist and no cross-lane
coordination meeting.

## A41.2 What changes, what does not

A new `report_type` extends the **set of legal string values** at
the caller site. It **does not**:

- add, remove, rename, or retype any `MioCertificate` field;
- change the schema-hash digest of `MioCertificate` (A32.5);
- change the `probe_name` grammar (A37.2);
- change the G19 enforcement perimeter (A32.5, A39.4);
- introduce a new cross-check channel (A34.3 — separate landing).

A new `report_type` **does**:

- register a string in A32.2 §`report_type` row (docs-only edit);
- pick a `channel` vocabulary (free-form; A32 enumerates current
  channels for each `report_type`);
- pick a `probe_name` production path compliant with A37.2;
- pick a `reduction_status` (`'theory-direct'` / `'theory-approximate'`
  / `'diagnostic-only'`) appropriate to the V-gate state of the module;
- ship a concrete test that exercises the full generator round-trip
  and asserts the G19 posterior-token ban.

## A41.3 Extension checklist (mechanical, seven steps)

1. **Pick the string.** Use `snake_case`; match `^[a-z][a-z0-9_]{0,31}$`.
   Scan [`bass_py/mio/`](../../bass_py/mio/) for existing uses to avoid
   collisions. The canonical reservation list lives in A32.2; update
   it in the same PR as the new module (same commit, not follow-up).

2. **Author the producing module** under the ownership lane in
   A39.2. New file name must start with `mio_` if it emits an artefact
   (REG-02 rule); new module path must live under `bass_py/mio/*`.
   Cross-package "MIO-owned" code lives where it logically belongs
   and carries `__mio_owned__ = True` + `__mio_rationale__`
   (cf. [`htt.PR13AM_te_sign_d1d3_bridge`](../../bass_py/htt/htt/PR13AM_te_sign_d1d3_bridge.py)).

3. **Channel vocabulary.** For CMB-like diagnostics reuse
   `'low_ell'` / `'biposh'` / `'dipole'` / `'recomb_only'` /
   `'reion_only'` / `'full_TTTEEE'`. For z-tagged diagnostics reuse
   `'dipole_vs_z'` (HJ-02b pattern). Coin a new channel only when the
   physical domain is genuinely new; document in A32.2 §`channel`.

4. **Probe-name production.** Pick one of the A37.2 forms:
   - **singleton** — when the cert reports a single probe (e.g.
     `'CMB'`);
   - **bundle** — alphabetical `"+"`-join via
     `"+".join(sorted(p.name for p in probes))` (HJ-02a/b pattern);
   - **atlas_label** — MODEL_ID via
     [`mio.extraction.hj01_shear._bianchi_type_to_model_id`](../../bass_py/mio/extraction/hj01_shear.py)
     (HJ-01 pattern).
   Add a `test_probe_name_matches_grammar_v1_<module>` case to
   [`test_probe_name_grammar.py`](../../bass_py/mio/tests/test_probe_name_grammar.py)
   mirroring the three existing entries.

5. **Reduction status.**
   - `'diagnostic-only'` — the default for every module gated on a
     bass_py or HTT V-gate that has not yet signed off
     (HJ-01 today, HJ-02a, HJ-02b, every planned HJ-03 / HJ-04 slot
     until the upstream atlases land; see v3 §17.3).
   - `'theory-approximate'` — valid once the module's upstream
     dependencies have signed off *but* the module itself applies a
     documented approximation (e.g. diagonal independence χ² when the
     full covariance is available — W10 F2).
   - `'theory-direct'` — reserve for modules whose maths matches the
     plan's physical claim verbatim; no module should self-promote
     from the lower tiers without an accompanying audit log row.

6. **Tests.** Land at minimum:
   - one round-trip test proving `report_type == "<new_value>"`;
   - one G19 token-ban test (regex `"posterior"` absent from the
     serialised certificate; cf.
     [`test_to_mio_certificate_has_no_posterior_field`](../../bass_py/mio/tests/test_hj01_shear.py));
   - one grammar test per A37 (see step 4);
   - one `reduction_status` test asserting the expected tier.

7. **Dossier entry.** Extend A32.2 with the new row, extend A34.3 if
   a new cross-check channel opens, and add a dedicated
   `docs/dossier/Axx_<report_type>.md` if the module introduces
   non-trivial mathematics. The dossier convention follows A35 / A36
   / A37 (purpose, grammar / policy, code anchors, G19 posture,
   related appendices).

## A41.4 Non-scope for an extension PR

The extension PR **must not**:

- mutate the `MioCertificate` dataclass itself — that is a schema
  bump, governed separately (A32.5 + W7 FM3; requires a hash-digest
  update and a coordinated migration of all prior cert readers);
- add a cross-check channel to the A34.3 catalogue — that requires
  the five G19 properties in A34.2 (loud-fail guard, `is_cross_check`
  flag, etc.) and is never automatic;
- relax any G19 enforcement rule (`posterior`-token ban,
  `as_posterior_bundle` `NotImplementedError`, HTT ingestion ban);
- rename or retire an existing `report_type` string — old strings
  remain valid forever for W1–W11 cert files.

## A41.5 Interaction with the W7 FM3 schema-hash freeze

[`tsc.charts.michaelis_menten_export`](../../bass_py/tsc/charts/michaelis_menten_export.py)
uses `SCHEMA_VERSION = "TSC-05/v1"` with a literal key-set test.
`MioCertificate` uses a hash-based freeze — any change to the
dataclass fields rotates the digest.

Because `report_type` is a *value* of a field (not a field itself),
adding a new legal value does **not** rotate the hash. This is the
design mechanism that lets HJ-03 / HJ-04 land without a CONTRACTS-01
v2 bump. The hash-based freeze only catches field-level drift; it is
deliberately lenient to value-level expansion so that the pillar can
grow new diagnostics with a single PR.

Corollary: a reader that hard-codes the four W11 `report_type`
values (`'shear_extraction'` / `'directional_coherence'` /
`'redshift_binned_coherence'` / any future addition) in an
exhaustive `match` statement is a *consumer-side* bug, not a schema
violation. Readers should default-fallback on unknown `report_type`
and defer strict validation to explicit registries
(e.g. A34.3 cross-check catalogue; A39.2 ownership table).

## A41.6 Worked example — HJ-03 evidence anatomy (deferred)

When bass_py W10-02 K_ℓ atlas + HTT Phase F posterior-decomposition
infrastructure land, the HJ-03 author will:

1. Pick `report_type = "evidence_anatomy"` (pre-reserved in A32.2).
2. Create `bass_py/mio/decomposition/evidence_anatomy.py`.
3. Use `channel = "full_TTTEEE"` for the full-spectrum decomposition;
   `channel = "low_ell"` for the low-ℓ sub-report.
4. `probe_name` as an atlas_label singleton per A37.2 (MODEL_ID of
   the winning Bianchi type, e.g. `"BianchiVIIh"`).
5. `reduction_status = "diagnostic-only"` until the HTT Phase F
   posterior-decomposition tests pass; promote to `"theory-direct"`
   in a follow-up commit that cites the passing test IDs.
6. Tests per A41.3 step 6 + A34.3 cross-check channel entry pointing
   at `htt.core.analysis_extended.EvidenceComparison.run_all` as the
   HTT counterparty.
7. Dossier: extend A34.3; create `docs/dossier/A42_evidence_anatomy.md`
   with the decomposition maths.

No CONTRACTS-01 v2 bump; no schema-hash rotation; no migration of
existing cert readers. The extension is purely additive.

## A41.7 Related appendices

- [A32 MioCertificate schema](A32_mio_certificate_schema.md) — the
  dataclass whose `report_type` field this protocol governs.
- [A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md) —
  parallel protocol for the `is_cross_check=True` reports; A41 does
  **not** cover cross-check landings.
- [A37 probe-name schema](A37_mio_probe_name_schema.md) — A37.2
  grammar every new `report_type` emitter must comply with.
- [A39 per-module epistemic ownership](A39_per_module_epistemic_ownership.md) —
  ownership lane the new module plugs into.
- [A40 G19 architectural stance](A40_g19_architectural_stance.md) —
  non-negotiable hard-separation rules that the extension protocol
  ring-fences.
