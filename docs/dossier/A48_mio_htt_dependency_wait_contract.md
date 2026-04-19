# A48 · MIO → HTT dependency-wait contract

**Appendix**: A48 (§11.14.9 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W20D5 design dossier (documentation-only; no
code landing — A48 catalogues what is blocked on which upstream
milestone, it does not ship the unblocking work).
**Status**: **steady-state ledger** — re-read every Week-N plan
rotation; rows retire when their upstream milestone lands (per
§A48.5 the audit §8 row flips from `R<n>` to `RESOLVED <W>D<M>`).
**Parent references**:
v3 §7 (post-LB-6 bass_py roadmap — W10-02 K_ℓ atlas, W11-02
BiPoSH, Phase F posteriors);
v3 §17.3 (MIO dependency-wait list — the scattered surface A48
consolidates);
v3 §10.2 (HTT ↔ MIO contract table);
[A32 MioCertificate schema](A32_mio_certificate_schema.md)
(`reduction_status` field — the promotion target);
[A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md)
(channel catalogue — grows a new row per HJ when the upstream
prerequisite lands);
[A41 report_type extension protocol](A41_mio_report_type_extension_protocol.md)
(§A41.6 HJ-03 worked example — the PR that exercises this
ledger when bass_py W10-02 + HTT Phase F land);
[A42 evidence anatomy stub](A42_evidence_anatomy.md) (HJ-03
design — blocked on HTT Phase F posteriors);
[A44 MIO → HTT handshake sequence](A44_mio_htt_handshake_sequence.md)
(t₁→t₅ execution order applies to every row in §A48.2 once its
promotion conditions are met);
[A45 MIO cache-replay drift protocol](A45_mio_cache_replay_drift.md)
(content-hash guard lands with HJ-03 — see the `HJ-03` row
below);
[A47 HJ-03 acceptance-test paste-replace protocol](A47_hj03_acceptance_test_paste_replace_protocol.md)
(§A47.2 five input prerequisites — most are A48's dependency
rows);
W9 §2 audit ledger (the earliest consolidated statement of the
MIO-blocked surface, before A48 existed);
`docs/INDEPENDENT_TRACKS_NEXT_SESSION.md` §2 "Deferred to
Week N+" (the per-session restatement of §A48.2).

---

## A48.1 Purpose

The ind-tracks lane's Week 10+ MIO workstream is structurally
rate-limited by the bass_py lane's post-LB-6 roadmap. Specific
artefacts (HJ-01 production wiring, HJ-03 evidence anatomy, HJ-04
departure skeleton, MANU-CH12 §§12.1 / 12.4 / 12.5 / 12.8) sit in
a "skeleton landed, promotion deferred" state until the upstream
bass_py output they consume reaches V-gate signature. The exact
upstream milestone and the exact promotion action are currently
spread across: v3 §7 (bass_py roadmap), v3 §17.3 (a partial list),
W9+ audit §8 tables (per-week incremental updates), and the
per-artefact dossier's "deferred to" clauses (A41.6 / A42.5 / A45.3
/ A47.2).

A48 consolidates that surface into a single per-artefact matrix
(§A48.2) with (a) the frozen upstream milestone tag, (b) the
current `reduction_status` in the emitted certificate, (c) the
specific bass_py / HTT output the promotion consumes, and (d)
the exact paste-target inside the ind-tracks codebase. The
ledger is **steady-state**: rows retire when a milestone lands,
but new rows enter only if a new HJ-N or manuscript section
enters the deferred list.

## A48.2 Dependency matrix (as of 2026-04-19 W20)

| Ind-tracks artefact | Current status | Upstream milestone | Consumed output | Paste target | Audit ref |
|---|---|---|---|---|---|
| HJ-01 shear extraction | `reduction_status='diagnostic-only'`; χ² uses per-ℓ-independence (W10 F2); `DIAGNOSTIC_ONLY_CAVEAT` in first slot of `domain_caveats` | bass_py W10-02 (K_ℓ atlas V-gate) | per-ℓ covariance `C_ℓ,ℓ'` from the V-gated atlas | `bass_py/mio/extraction/hj01_shear.py::ShearExtractor._independence_chi2` → weighted χ² with folded covariance; drop the caveat tag; flip `reduction_status` to `'theory-direct'` | W10 F1 / F2 / F3 |
| HJ-03 evidence anatomy | not yet skeletoned — A42 design stub only | HTT Phase F (independent `ln B` per-channel posteriors) | HTT-Phase-F posterior bundle (A44 t₃ output) | new `bass_py/mio/interface/cache_replay.py` (A47.3) + new `bass_py/mio/decomposition/hj03_evidence_anatomy.py` (per A42.2 unweighted per-channel decomposition); drives the A45.6 five-test paste block | A42.5 / A45.3 / A47.2 |
| HJ-04 departure skeleton | not yet skeletoned; `flrw_tension` binding per A41 | HTT Phase F + HJ-03 landing (transitive: the departure score reuses HJ-03's per-channel decomposition) | per-channel `Δ ln B` vector from HJ-03 | new `bass_py/mio/decomposition/hj04_departure.py`; A46.6 notes it reuses the HJ-03 three-file dossier triplet | v3 §17.3 HJ-04 row |
| HJ-05-full (masked-sky w/ bias correction) | W6 HJ-05a-lite only — caveat-surfacing stub; upstream `_apply_bias_to_direction` intentionally untouched (W5 APPLY-BIAS-AMP) | bass_py ChannelSummary gains a `velocity_amplitude` field | `|V_true|` per channel from the upstream summary struct | `bass_py/htt/htt/PR13AH_observables_reintegration.py::_apply_bias_to_direction` — swap the amplitude-measurement argument; remove `BIAS_AMP_CAVEAT` from the certificate domain caveats list | W5 APPLY-BIAS-AMP resolution contract |
| MANU-CH12 §12.1 (HJ-01 production results) | deferred; §12.0 / §12.2 / §12.3 / §12.6 / §12.7 landed W8–W10 | HJ-01 production promotion (see row 1) | HJ-01 `ShearExtractorReport` with `reduction_status='theory-direct'` | `project/00_manuscript/ch12_mio_observatory_results.tex` after §12.0.x; ≥ 150 L subsection; banned-vocab scan = 0; not committed (W8 FM1 `/project` rule) | v3 §17.3 MANU-CH12 |
| MANU-CH12 §12.4 (HJ-03 evidence anatomy) | deferred | HJ-03 landing (see row 2) | HJ-03 per-channel decomposition numbers | same file; ≥ 150 L subsection | v3 §17.3 |
| MANU-CH12 §12.5 (HJ-04 departure) | deferred | HJ-04 landing (see row 3) | HJ-04 departure scalar + per-type decomposition | same file; ≥ 150 L subsection | v3 §17.3 |
| MANU-CH12 §12.8 (cross-channel synthesis) | deferred | HJ-01 production + HJ-03 + HJ-04 (all three rows above) | `MioCertificate` bundle across all four MIO harnesses | same file; ≥ 200 L synthesis subsection | v3 §17.3 |
| A43 digest test (W7 FM3 code-side close) | spec-only (§A43.6 paste-ready); test not landed | first schema extension (HJ-03 `'evidence_anatomy'` `report_type` OR HJ-04 `'flrw_tension'` OR TSC-05 v2) | new `report_type` literal + any payload-dict key addition | new `bass_py/workspace/contracts/tests/test_schema_hash_digest.py` (paste block from §A43.6); single commit with the extension | W15 F3 / A43.3 |

## A48.3 Per-row promotion conditions

* **HJ-01**: the upstream atlas must (a) carry a `C_ℓ,ℓ'` covariance
  block with the same `(ℓ_min, ℓ_max)` coverage as
  `ShearExtractorConfig`, (b) pass bass_py's V-gate signature (the
  atlas JSON carries `v_gate_sha=...` in its provenance), and (c)
  the HTT Phase F posterior draws consume the same atlas
  (verified by `atlas_sha` cross-match between the V-gate JSON and
  the HTT posterior bundle). The promotion PR is a single-file edit
  to `hj01_shear.py` + its tests; the caveat tag and
  `reduction_status` transitions land in the same commit.
* **HJ-03**: A47 specifies the landing-PR shape (§A47.2 inputs
  include a V-gated K_ℓ atlas and a Phase-F posterior bundle); the
  PR bundles the three-file ind-tracks landing (A46.6) + the
  replay harness + the five-test paste block (A45.6). A43's digest
  test lands in the same PR if the HJ-03 schema extension is the
  first schema change (W15 F3 trigger).
* **HJ-04**: requires HJ-03 already landed (transitive dependency
  via per-channel decomposition reuse). Promotion PR reuses A46.6's
  dossier triplet pattern with `flrw_tension` substituted for
  `evidence_anatomy`.
* **HJ-05-full**: independent of HJ-01 / HJ-03 / HJ-04 — blocked
  only on the upstream ChannelSummary field addition. A new caveat
  tag `BIAS_CORRECTION_APPLIED_CAVEAT` replaces the current
  `BIAS_AMP_CAVEAT` in the emission path.
* **MANU-CH12 §§12.1 / 12.4 / 12.5 / 12.8**: landing gates are
  `/project` working-tree edits only (W8 FM1 rule); each subsection
  consumes the promoted MIO artefact of its upstream row and needs
  a banned-vocab scan = 0 + ≥ 150 L body.

## A48.4 Audit §8 ledger mechanics

Each row in §A48.2 corresponds to an `R<n>` repair row in the
per-week audit §8 table. The `R<n>` entry carries:

* a tag matching the row's "Upstream milestone" column (e.g.
  `R-W10-02` for the K_ℓ atlas);
* a "landing trigger" sentence naming the upstream sha pattern
  (e.g. "bass_py commits an `LB-7 W10-02 K_ℓ atlas V-gated`
  commit on main");
* a "ind-tracks action" sentence naming the paste target from the
  §A48.2 row.

When the upstream milestone lands, the R-row flips to `RESOLVED
<W>D<M>` with a reference to the promotion PR. The three audit
rows currently outstanding (as of W19 audit) are W10 F2 (HJ-01
folded covariance), W10 F1 (HJ-01 `_gammaincc` warn path), and
W10 F3 (HJ-01 Bonferroni knob); they collapse into a single
HJ-01-promotion PR per §A48.3 row 1 conditions.

## A48.5 Relation to other appendices

* **A34 channel catalogue** — A48.2 row 2 (HJ-03 landing) fires
  A34.3's third catalogue entry. The channel-catalogue extension
  is a documentation edit inside A34 that lands in the HJ-03 PR
  (per A47.6 single-PR rule).
* **A41 report_type extension protocol** — A41.6's HJ-03 worked
  example is the mechanical checklist for the HJ-03 row's
  promotion PR; A48 is the calendar ledger that pins *when* the
  checklist fires.
* **A42 / A45 / A47** — each dossier has its own "deferred to"
  clause pointing at the same HJ-03 landing trigger; A48.2 row 2
  is the single source of truth that those clauses dereference.
* **v3 §17.3** — A48 supersedes the partial list in v3 §17.3. A
  future v4 research plan can reference A48.2 instead of re-stating
  the matrix inline.

## A48.6 No code landing

A48 is specification-only. The ledger is re-read at every Week-N
plan rotation (§0 rule: the next-session prompt's §2 "Deferred"
block is a projection of §A48.2 filtered to rows whose upstream
milestone has not yet landed). Re-audit trigger: if a new HJ-N
(beyond HJ-01 / HJ-03 / HJ-04 / HJ-05) enters the ind-tracks
scope, A48.2 grows a new row in the same PR that introduces the
skeleton. If the bass_py roadmap rearranges (e.g. W10-02 splits
into two milestones), A48.2's "Upstream milestone" column is
updated in a dedicated AUDIT(Wx Rn) commit before the next
promotion PR lands.
