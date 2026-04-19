# A37 · MIO probe-name schema

**Appendix**: A37 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 draft (landed with DOS-A30-MIO Week 11 Day 5-6).
**Code anchors**:
[`bass_py/workspace/contracts/mio_certificate.py`](../../bass_py/workspace/contracts/mio_certificate.py) (`probe_name: str` field in the `MioCertificate` frozen schema);
[`bass_py/mio/coherence/directional.py`](../../bass_py/mio/coherence/directional.py) (HJ-02a string-join);
[`bass_py/mio/coherence/redshift_binned.py`](../../bass_py/mio/coherence/redshift_binned.py) (HJ-02b string-join);
[`bass_py/mio/extraction/hj01_shear.py`](../../bass_py/mio/extraction/hj01_shear.py) (HJ-01 single-probe form).
**Parent references**:
v3 §4.5.3.5 (MioCertificate schema — probe_name field);
v3 §16.2 FM5 (probe-name ad-hoc string-join flagged);
W6 FM5 (PROBE-NAME-SCHEMA carry-forward — this dossier).

---

## A37.1 Purpose

The `MioCertificate.probe_name` field is a free-form `str`. Every MIO
module that emits a certificate has to decide how to fill it, and the
decisions have so far been ad hoc:

| Module | Current value | Convention |
|---|---|---|
| HJ-01 (shear extraction) | `"FLRW"` or `"BianchiVIIh"` (per atlas entry) | MODEL_ID derived from `bianchi_type` via `_bianchi_type_to_model_id` (W12D1) |
| HJ-02a (directional coherence) | `"BiPoSH+CF4pp+CMB+CatWISE+Radio"` | `"+".join(sorted(p.name for p in probes))` (W12D1) |
| HJ-02b (z-binned coherence) | same as HJ-02a | `"+".join(sorted(p.name for p in probes))` (W12D1) |

Downstream consumers (MANU-CH12-NEW, A34 cross-check tables,
future figure scripts) need to parse this string. The **ad-hoc
string-join is not a contract** — a future plus-sign or punctuation
change would silently break every table that splits on `+`. This
dossier freezes the grammar so that (a) existing cert files remain
parseable, and (b) a structured `probe_names: list[str]` migration
has a clear target.

## A37.2 Grammar (v1, frozen 2026-04-19)

```
probe_name       := singleton | bundle | atlas_label
singleton        := PROBE_ID                         e.g. "CMB"
bundle           := PROBE_ID ("+" PROBE_ID)+          e.g. "CMB+CatWISE+CF4pp"
atlas_label      := MODEL_ID ("_vs_" MODEL_ID | ("+" MODEL_ID)+)?  e.g. "BianchiVIIh", "FLRW_vs_BianchiIX"

PROBE_ID         := [A-Za-z][A-Za-z0-9]{0,23}   (1–24 chars, alnum only)
MODEL_ID         := /(FLRW|BianchiI|BianchiII|BianchiV|BianchiVI(0|h)|BianchiVII(0|h)|BianchiVIII|BianchiIX|Tilted[A-Z][A-Za-z]+)/
```

Three hard rules for producers:

1. **No whitespace**. Parsers may split on `+` or `_vs_` without
   stripping.
2. **Alphabetical order within a `bundle`**. `"CatWISE+CMB"` and
   `"CMB+CatWISE"` are **not** interchangeable; only the alphabetical
   form is canonical (so the probe_name becomes a stable dictionary
   key for cross-cert aggregation).
3. **`_vs_` is reserved** for atlas-derived null/alternative pairs
   (HJ-01 FLRW-vs-Bianchi contrasts). `+` is reserved for bundle
   membership (HJ-02a/b, or future channel bundles).

## A37.3 Registered PROBE_IDs (v1)

The five HJ-02a SSOT probes, mirrored verbatim into HJ-02b:

| ID | Origin | Reference |
|---|---|---|
| `CMB` | Planck 2018 intermediate | Fixsen 1996 + Planck LIX |
| `CatWISE` | Secrest+ 2020 | arXiv:2009.14826 |
| `Radio` | NVSS+RACS AGN composite | Singal 2011 / Rubart–Schwarz 2013 / Blake–Wall 2002 |
| `CF4pp` | Tully+ 2023 Cosmicflows-4 | `10.3847/1538-4357/acf1a4` |
| `BiPoSH` | Planck 2015 BipoSH | Planck 2015 Appendix |

New probes must (a) pass `PROBE_ID` regex, (b) be added to this table,
and (c) be registered in `STANDARD_PROBES` and `STANDARD_Z_PROBES`
in a single lane-aware commit.

## A37.4 HJ-02b interaction (z tagging)

HJ-02b attaches `z_eff` to each probe at the dataclass level and uses
the same PROBE_ID vocabulary. `probe_name` therefore does **not**
encode z — the z range lives in `departure_variables.n_populated_bins`,
the per-bin breakdown lives in `bin_results`, and the certificate
inherits from HJ-02a's alphabetical-bundle shape.

Exception: when a future HJ-02b variant emits one certificate *per
bin*, the PROBE_ID may be suffixed with the bin index in a structured
way once the schema bump v2 lands (see A37.7 below).

## A37.5 Migration path to structured `probe_names: list[str]`

The v3 §16.2 FM5 plan is to eventually replace `probe_name: str` with
`probe_names: list[str]` on a CONTRACTS-01 v2 bump, preserving the
current string field as an auto-derived alphabetical `"+"`-join for
backward compatibility. The grammar above is forward-compatible with
that migration — every bundle of the form `A+B+C` (A < B < C
alphabetically) unambiguously serialises to `["A", "B", "C"]`.

A future writer that wants to emit `probe_names` directly should:

1. Keep populating `probe_name` as the alphabetical join.
2. Add the list via a sibling `probe_names` field on the schema v2 bump.
3. Freeze both with the schema-hash digest test (W7 FM3 pattern).

## A37.6 Acceptance tests (landed W12D1)

Shipped in [`bass_py/mio/tests/test_probe_name_grammar.py`](../../bass_py/mio/tests/test_probe_name_grammar.py)
(8 tests; W12D1 / W11 F4 closure):

- `test_probe_name_is_alphabetical_bundle_HJ02a` / `…_HJ02b` — verify
  `probe_name == "+".join(sorted(p.name for p in probes))` for the two
  bundle-emitting modules.
- `test_probe_name_matches_grammar_v1_HJ01` / `…_HJ02a` / `…_HJ02b` —
  regex-check each emitted certificate against the BNF in A37.2 via
  ``PROBE_ID_RE`` / ``MODEL_ID_RE`` / ``BUNDLE_RE`` / ``ATLAS_LABEL_RE``.
- `test_bianchi_type_to_model_id_handles_known_suffixes` — locks the
  HJ-01 bare-suffix → MODEL_ID normaliser against the DOS-A13 atlas
  (``"I"`` → ``"BianchiI"``; ``"FLRW"`` idempotent; etc.).
- `test_grammar_regex_accepts_registered_probe_ids` /
  `test_grammar_regex_accepts_model_ids` — regex self-tests against the
  A37.3 PROBE_ID catalogue and the A37.2 MODEL_ID samples; guards
  against harness regressions.

The W12D1 landing also tightened the two bundle producers
([`mio/coherence/directional.py`](../../bass_py/mio/coherence/directional.py),
[`mio/coherence/redshift_binned.py`](../../bass_py/mio/coherence/redshift_binned.py))
to emit alphabetically-sorted joins, and replaced the legacy
``atlas_name:bianchi_type`` probe_name in
[`mio/extraction/hj01_shear.py`](../../bass_py/mio/extraction/hj01_shear.py)
with the MODEL_ID-only singleton form. No downstream consumer asserted
on the unsorted / colonned strings; the change is backward-compatible
with every prior artefact reader (A37.5 migration remains unaffected).

## A37.7 G19 posture

- `probe_name` is metadata, never a statistical scalar.
- The grammar is public so any reader can verify cross-cert identity
  without reading Python source.
- The `_vs_` vs `+` split is the structural mechanism behind A34's
  cross-check channel table: `bundle` certs are candidates for
  directional cross-checks, `atlas_label` certs for evidence
  cross-checks.

## A37.8 Related appendices

- [A32 MioCertificate schema](A32_mio_certificate_schema.md) —
  where the string lives.
- [A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md) —
  uses the grammar to classify cert pairings.
- [A35 HJ-02a directional coherence](A35_directional_coherence.md) —
  concrete bundle-form example.
- [A36 MIO channel weighting policy](A36_mio_channel_weighting.md) —
  complements this schema (A36 = how scalars combine; A37 = how the
  identity label is built).
