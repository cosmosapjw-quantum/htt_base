# A43 · Schema-hash digest test (W7 FM3 closure)

**Appendix**: A43 (§11.14.6 of `BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN.md` v3)
**Version**: 2026-04-19 W15D3 design dossier (no code landing — test
specification only; lands at first schema extension per §A43.3).
**Status**: **deferred-to-extension** — A43 fixes the digest mechanism
that closes [W7 FM3](../audits/AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md#fm3-schema-bump-vs-frozen-hash-coordination-p3).
The test itself does not land until the first schema extension actually
occurs (§A43.3); landing pre-extension would freeze the wrong digest
and force a one-line bump in the same PR that adds the extension —
no information gain.
**Code anchors (current — both literal-key-set freezes)**:
[`bass_py/workspace/contracts/mio_certificate.py`](../../bass_py/workspace/contracts/mio_certificate.py)
+ [`bass_py/workspace/contracts/tests/test_mio_certificate.py::test_miocertificate_schema_frozen`](../../bass_py/workspace/contracts/tests/test_mio_certificate.py);
[`bass_py/tsc/charts/michaelis_menten_export.py`](../../bass_py/tsc/charts/michaelis_menten_export.py)
+ [`bass_py/tsc/charts/test_michaelis_menten_export.py`](../../bass_py/tsc/charts/test_michaelis_menten_export.py).
**Parent references**:
v3 §10.2bis (G19 enforcement matrix);
[W7 FM3](../audits/AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md#fm3-schema-bump-vs-frozen-hash-coordination-p3);
[A32 MioCertificate schema](A32_mio_certificate_schema.md) (§A32.5
enforcement table — A43 specifies the "Schema hash anti-regression"
row's mechanism);
[A41 report_type extension protocol](A41_mio_report_type_extension_protocol.md)
(§A41.2 — what changes vs what does not at extension time; §A41.5 —
why a value-level addition leaves the field-set hash invariant);
[A42 evidence anatomy](A42_evidence_anatomy.md) (§A42.5 — the HJ-03
landing PR is the most likely trigger for the first extension).

---

## A43.1 Purpose

Both `MioCertificate` (v3 §4.5.2.1) and `MichaelisMentenExport`
(TSC-05) declare a schema "freeze" but enforce it via a literal-key-set
test, not a content-addressed digest:

* `test_miocertificate_schema_frozen` *computes* a 16-character SHA-256
  prefix of `[(field.name, str(field.type))]` but only asserts on
  set-equality of the field-name set. The digest appears solely in
  the error message. A type-only change (e.g. `Dict[str, float]` →
  `Mapping[str, float]`) leaves the test green but rotates the
  digest silently.
* TSC-05 declares `SCHEMA_VERSION: str = "TSC-05/v1"` and the consumer
  test pins the literal string. A new top-level key (e.g. a `T_CMB_MICROK`
  convenience field) must be paired with a manual `"TSC-05/v2"` bump
  + the `expected_keys` literal update; nothing forces the bump.

[W7 FM3](../audits/AUDIT_PHASE_IND_TRACKS_W7_2026-04-19.md#fm3-schema-bump-vs-frozen-hash-coordination-p3)
records both gaps as a single P3 item with the mitigation deferred
"when an extension is actually planned". A43 is that mitigation,
written ahead of the extension so the HJ-03 / HJ-04 landing author
has a mechanical specification to follow.

A43 is **not** a request to retrofit the digest test today. The
trigger is §A43.3 — first schema extension, not first opportunity.

## A43.2 Scope — what is digested, what is metadata

The digest covers the **structural surface** of the contract: the
ordered tuple of `(field_name, normalised_field_type, default_kind)`
across all fields the consumer reads at parse time. Anything
metadata-only or downstream-derived is excluded so the digest tracks
contract-breakage, not cosmetic edits.

### A43.2.1 Included in the digest (rotates on edit)

| Item | Rationale |
|---|---|
| Field name (string) | A reader keys on this; renaming breaks every consumer. |
| Field type (normalised string — see §A43.4) | A reader assumes a shape; type swap (e.g. `List[str]` → `Tuple[str, ...]`) breaks `.append`-style consumers. |
| Default kind (`'no_default'` / `'literal'` / `'factory'`) | A field gaining a default permits consumers to omit it; a field losing one is a breaking change. The default *value* is excluded — TSC-05 may legitimately retune `T_CMB_K_MIRROR` without a schema bump. |
| Field order | Positional `__init__` calls in tests pin order; reordering is a breaking change. The digest ingests the field tuple in declaration order. |

### A43.2.2 Excluded from the digest (free to edit)

| Item | Rationale |
|---|---|
| Field docstring / inline comment | Documentation only. |
| Default *value* (when `default_kind == 'literal'`) | Re-tuning a constant (e.g. `SCHEMA_VERSION` itself, `T_CMB_K_MIRROR`) must not rotate the digest. The freeze layer that catches a value drift lives in regression tests (`test_t_cmb_k_mirror_frozen`), not in the schema digest. |
| Set of legal `report_type` / `channel` *values* | A new `report_type` is a value-level addition, not a field-level one (per [A41.2](A41_mio_report_type_extension_protocol.md#a412-what-changes-what-does-not) and [§A41.5](A41_mio_report_type_extension_protocol.md#a415-interaction-with-the-w7-fm3-schema-hash-freeze)). Folding the value-set into the digest would force a hash rotation on every HJ-N landing — defeats the purpose of A41. |
| Contents of `Dict[str, float]` payload fields | A new key in `consistency_metrics` (e.g. `decomposition_residual` from [§A42.3](A42_evidence_anatomy.md#a423-computation-planned)) is a value-level addition. The dict-of-floats type guarantees `.get(key, default)`-style consumer access; new keys are additive. |
| Class docstring | Documentation only. |
| Module-level constants outside the dataclass body (e.g. `T_CMB_K_MIRROR`, `ROUTE_B_C1`) | Provenance tracked separately in TSC-05's literal SSOT mirror tests. |

### A43.2.3 Boundary cases

* **Adding a new dataclass field** rotates the digest — by design.
  The extension PR must paste the new digest into the test as an
  AUDIT trail (one-line edit).
* **Adding a new key to an existing payload dict** does **not** rotate
  the digest. This is the explicit affordance the A41 + A42 design
  relies on (HJ-03 lands `consistency_metrics["decomposition_residual"]`
  without touching the schema layer).
* **Changing `Optional[Dict[str, str]]` → `Dict[str, str]` on
  `htt_cross_check_suggested`** rotates the digest because the
  default kind shifts from `'literal'` (`None`) to `'no_default'`.
  This is correct: removing the optional default is a breaking change
  for every existing caller.

## A43.3 CI trigger point — when this dossier becomes code

A43 lands as a test in the same PR as the **first schema extension**
to either `MioCertificate` or `MichaelisMentenExport`. The most likely
candidates (per the deferred-to-Phase-J table in
`INDEPENDENT_TRACKS_NEXT_SESSION.md` §2):

1. **HJ-03 landing** — adds no new `MioCertificate` field by design
   (`decomposition_residual` lives inside `consistency_metrics`); but
   if HJ-03 chooses to introduce a top-level `cross_check_residuals`
   field, that is the trigger.
2. **HJ-04 landing** — same posture. `flrw_tension` is expected to
   reuse `departure_variables["x_C"]` + `consistency_metrics
   ["look_elsewhere_corrected_p"]`; only an unexpected top-level
   addition triggers A43.
3. **TSC-05 extension** — first time anyone wants a new top-level
   key (`T_CMB_MICROK` is the canonical hypothetical from the W7
   FM3 audit). Triggers a `"TSC-05/v2"` literal bump *and* the A43
   digest test landing.
4. **CONTRACTS-01 v2** — explicit contract bump (e.g. `MioCertificate`
   gains a `cross_check_evidence: Optional[CrossCheckBundle]` field
   per a future v3 §11.14.7 amendment). Triggers A43 plus a coordinated
   migration of every consumer.

If none of (1)–(4) materialise within Week 15–20, A43 stays a
documentation-only dossier. The mechanism specification is the
deliverable; landing the test ahead of the trigger would freeze the
wrong digest (today's field tuple) and force a manual bump on the
first extension PR — a no-op edit that adds noise without catching
anything the literal-key-set test misses.

## A43.4 Type normalisation rule

The digest depends on a stable string representation of `field.type`.
Python's `str(field.type)` form is unstable across versions:

* `Dict[str, float]` (Python 3.8) vs `dict[str, float]` (Python 3.9+).
* `Optional[X]` vs `X | None` vs `Union[X, None]`.

A43 specifies the canonical form for digest input:

```python
import typing

def _normalise_type(t) -> str:
    """Stable, version-independent type string for digest input."""
    s = str(t)
    s = s.replace("typing.", "")
    s = s.replace("Dict[", "dict[")
    s = s.replace("List[", "list[")
    s = s.replace("Tuple[", "tuple[")
    s = s.replace("Optional[", "Union[None, ")  # canonicalise; close paren falls out
    return s
```

The HJ-03 landing PR may extend this normaliser as new typing forms
appear, but every extension must paste the new digest as an AUDIT
trail entry in the same commit. The normaliser itself is part of the
contract; rewriting it without re-pasting the digest is a silent
break.

## A43.5 Worked example — adding `consistency_metrics["decomposition_residual"]`

HJ-03 (per [§A42.3 step 3](A42_evidence_anatomy.md#a423-computation-planned)
+ [§A42.5](A42_evidence_anatomy.md#a425-certificate-contract-planned))
populates `consistency_metrics["decomposition_residual"]` to report
the per-channel sum reproduction floor.

| Step | Touches dataclass body? | Touches digest? | Touches A43 test? |
|---|---|---|---|
| Author `mio.decomposition.evidence_anatomy.py`. | No. | No. | No. |
| Emit `MioCertificate(report_type="evidence_anatomy", consistency_metrics={"decomposition_residual": 4.7e-4, ...})`. | No. | No. | No. |
| Add `test_evidence_anatomy_reproduces_htt_total_within_floor` per [A42.8](A42_evidence_anatomy.md#a428-test-plan-placeholder). | No. | No. | No. |
| Land the new `report_type` value `"evidence_anatomy"` (per [A41.3 step 1](A41_mio_report_type_extension_protocol.md#a413-extension-checklist-mechanical-seven-steps)). | No (value-level). | No (per [§A41.5](A41_mio_report_type_extension_protocol.md#a415-interaction-with-the-w7-fm3-schema-hash-freeze)). | No. |

Net: HJ-03 lands without an A43 trigger. The dossier-claimed scope
boundary holds in the worked example.

### A43.5.1 Counter-example — adding a `cross_check_evidence` field

Suppose HJ-03 instead chooses to expose the per-channel covariance
matrix as a top-level field rather than nesting it in
`consistency_metrics`:

```python
@dataclass(frozen=True)
class MioCertificate:
    ...
    htt_cross_check_suggested: Optional[Dict[str, str]] = None
    cross_check_evidence: Optional[CrossCheckBundle] = None  # NEW
```

| Step | Touches dataclass body? | Touches digest? | Touches A43 test? |
|---|---|---|---|
| Add field. | **Yes**. | **Yes** (new tuple entry). | **Yes** — paste the new SHA-256 prefix into the assertion. |
| Update `test_miocertificate_schema_frozen` `expected` set. | No (legacy test). | — | — |
| AUDIT trail entry in commit body documenting the digest rotation. | No. | — | **Required** (W7 FM3 audit-record contract). |

The single one-line digest paste + the AUDIT-trail commit body is the
entire footprint of A43 at trigger time. If a contributor edits the
field set without rotating the digest, the A43 test fails loudly with
the new digest in the error message — they paste it, re-stage, and
re-commit. The AUDIT trail catches the cosmetic-edit case (e.g.
`Dict` → `Mapping`) that the literal-key-set test misses today.

## A43.6 Test specification (lands at trigger)

```python
# bass_py/workspace/contracts/tests/test_mio_certificate.py — addition
import dataclasses
import hashlib
import typing

from workspace.contracts.mio_certificate import MioCertificate


def _normalise_type(t) -> str:
    s = str(t)
    s = s.replace("typing.", "")
    s = s.replace("Dict[", "dict[")
    s = s.replace("List[", "list[")
    s = s.replace("Tuple[", "tuple[")
    s = s.replace("Optional[", "Union[None, ")
    return s


def _default_kind(f: dataclasses.Field) -> str:
    if f.default is not dataclasses.MISSING:
        return "literal"
    if f.default_factory is not dataclasses.MISSING:
        return "factory"
    return "no_default"


def test_miocertificate_schema_digest_frozen():
    """A43 · Hash-based schema freeze (W7 FM3 closure).

    Field-tuple digest rotates on:
      * field add / remove / rename
      * field-type normalised-string change
      * field default kind change (no_default vs literal vs factory)
      * field order change
    Does NOT rotate on:
      * docstring / comment edits
      * default value retunes
      * legal-value-set extensions for `report_type` / `channel`
      * payload-dict key additions
    """
    fields = dataclasses.fields(MioCertificate)
    sig = [(f.name, _normalise_type(f.type), _default_kind(f)) for f in fields]
    digest = hashlib.sha256(repr(sig).encode("utf-8")).hexdigest()[:16]
    expected = "<paste-on-extension>"  # rotate at A43 trigger
    assert digest == expected, (
        f"MioCertificate schema digest rotated: got {digest}; "
        f"expected {expected}. If this rotation is intentional, paste the "
        f"new digest above and add an AUDIT trail entry per A43.5.1."
    )
```

The mirror test for `MichaelisMentenExport` has the same shape with
`from tsc.charts.michaelis_menten_export import MichaelisMentenExport`
and lives in `bass_py/tsc/charts/test_michaelis_menten_export.py`.
Both tests land in the same trigger PR.

## A43.7 G19 posture

A43 is a **schema-layer** mechanism; it does not touch G19 separation.
The digest catches structural drift; G19 prohibits posterior-token
field names, MIO-into-HTT scalar fusion, and the `as_posterior_bundle`
implementation (§A32.5). Those rules are enforced by separate tests
([`test_g19_enforcement.py`](../../bass_py/workspace/contracts/tests/test_g19_enforcement.py))
and remain unchanged. A digest rotation triggered by a G19-violating
field would be flagged twice: A43 catches the structural change; the
G19 token scan catches the semantic violation. The redundancy is
intentional.

## A43.8 Open items

* **Default-value drift lint** — explicitly out of scope for A43;
  TSC-05 already pins `T_CMB_K_MIRROR == 2.7255` in a separate test
  and `MioCertificate` carries no constant-default fields. If a
  future field gains a load-bearing literal default, add a paired
  `test_<field>_default_frozen` next to A43, not inside it.
* **Cross-package digest registry** — HJ-04 may want a shared digest
  registry under `workspace.contracts.schema_digests`. Premature
  until two contracts actually rotate; revisit at the second
  extension PR.
* **Migration-record file** — when an extension lands, append a row
  to a new `docs/dossier/A43_digest_history.md` (created on first
  rotation) with `{commit, contract, old_digest, new_digest,
  reason}`. Premature pre-trigger.

## A43.9 Related appendices

* [A32 MioCertificate schema](A32_mio_certificate_schema.md) — the
  contract whose digest A43 specifies; §A32.5 row "Schema hash
  anti-regression" points here for its mechanism.
* [A34 G19 cross-check protocol](A34_g19_cross_check_protocol.md) —
  parallel concern (G19 separation enforcement) but disjoint surface;
  A43 catches structural drift, A34 catches cross-check protocol
  drift.
* [A41 report_type extension protocol](A41_mio_report_type_extension_protocol.md)
  — §A41.2 + §A41.5 specify the value-level / field-level boundary
  that A43 mechanises on the field-level side.
* [A42 evidence anatomy](A42_evidence_anatomy.md) — §A42.5 contract
  table + §A42.3 derived fields; the worked example in §A43.5
  references both directly.
