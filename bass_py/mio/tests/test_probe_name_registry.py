"""A37.3 PROBE_ID registry parity tests (W13D2 / W12 F3 close).

Plan: docs/INDEPENDENT_TRACKS_NEXT_SESSION.md §2 Days 1-2 Week 13.
Contract: the frozen ``REGISTERED_PROBE_IDS`` tuple in
``mio.interface.probe_name_registry`` must match the A37.3 markdown
table row-for-row. A new probe requires a three-file commit (code,
dossier, STANDARD_PROBES); this test gates the code↔dossier pair.
"""
from __future__ import annotations

import re
from pathlib import Path

from mio.coherence.directional import STANDARD_PROBES
from mio.coherence.redshift_binned import STANDARD_Z_PROBES
from mio.interface.probe_name_registry import (
    REGISTERED_PROBE_IDS,
    is_registered_probe_id,
)


DOSSIER_PATH = (
    Path(__file__).resolve().parent.parent.parent.parent
    / "docs" / "dossier" / "A37_mio_probe_name_schema.md"
)


def _parse_a37_3_probe_ids_from_markdown(text: str) -> tuple[str, ...]:
    """Extract PROBE_IDs from the A37.3 table.

    The A37.3 section starts at the header ``## A37.3`` and ends at the
    next ``## A37`` header. Inside that window the canonical probe table
    has the form:

        | ID | Origin | Reference |
        |---|---|---|
        | `CMB` | ... | ... |

    We harvest the backtick-wrapped first-column values.
    """
    start_match = re.search(r"^## A37\.3\b", text, flags=re.MULTILINE)
    if start_match is None:
        raise AssertionError("A37.3 section header not found in dossier.")
    after = text[start_match.end():]
    end_match = re.search(r"^## A37\.[4-9]", after, flags=re.MULTILINE)
    section = after[: end_match.start()] if end_match else after
    # First-column backtick tokens on table rows (skip the header separator).
    row_re = re.compile(r"^\|\s*`([A-Za-z][A-Za-z0-9]{0,23})`\s*\|", re.MULTILINE)
    return tuple(row_re.findall(section))


def test_dossier_parser_recovers_five_probe_ids():
    """Self-check on the markdown parser before we trust parity assertions."""
    text = DOSSIER_PATH.read_text(encoding="utf-8")
    ids = _parse_a37_3_probe_ids_from_markdown(text)
    assert len(ids) == 5, f"expected 5 A37.3 rows, got {len(ids)}: {ids!r}"
    assert set(ids) == {"CMB", "CatWISE", "Radio", "CF4pp", "BiPoSH"}


def test_probe_name_registry_matches_a37_dossier():
    """The code-side tuple must be a set-equal to the dossier's A37.3 rows.

    Order of listing in the markdown table is intentional (documentary
    priority), so we compare as sets. The code-side tuple additionally
    imposes alphabetical ordering, validated by
    ``test_registry_is_alphabetical_and_immutable``.
    """
    text = DOSSIER_PATH.read_text(encoding="utf-8")
    dossier_ids = set(_parse_a37_3_probe_ids_from_markdown(text))
    assert set(REGISTERED_PROBE_IDS) == dossier_ids, (
        f"code registry {sorted(REGISTERED_PROBE_IDS)!r} != "
        f"dossier A37.3 {sorted(dossier_ids)!r}"
    )


def test_registry_is_alphabetical_and_immutable():
    """Tuple is ASCII-alphabetically sorted (key for cross-cert lookup)
    and immutable (not a list/set)."""
    assert isinstance(REGISTERED_PROBE_IDS, tuple)
    assert list(REGISTERED_PROBE_IDS) == sorted(REGISTERED_PROBE_IDS)


def test_is_registered_probe_id_accepts_all_five():
    for pid in REGISTERED_PROBE_IDS:
        assert is_registered_probe_id(pid), pid


def test_is_registered_probe_id_rejects_typos_and_novel_names():
    for bad in ("cmb", "CMB ", " CMB", "CatWise", "catwise", "", "NEW"):
        assert not is_registered_probe_id(bad), bad


def test_standard_probes_agree_with_registry():
    """The HJ-02a / HJ-02b producer SSOTs must use only registered IDs.

    This is the (3) half of the A37.3 three-file invariant: any rename or
    new addition in ``STANDARD_PROBES`` / ``STANDARD_Z_PROBES`` that
    drifts from the registry will fail here before a producer commit
    lands.
    """
    code_names = {p.name for p in STANDARD_PROBES}
    code_names |= {p.name for p in STANDARD_Z_PROBES}
    assert code_names == set(REGISTERED_PROBE_IDS), (
        f"STANDARD_PROBES ∪ STANDARD_Z_PROBES {sorted(code_names)!r} != "
        f"registry {sorted(REGISTERED_PROBE_IDS)!r}"
    )


def test_standard_probes_have_consistent_sigma_cone_across_producers():
    """Cross-producer σ_cone / l / b parity (W13 F2 / W14D1).

    W13D2's ``test_standard_probes_agree_with_registry`` only gates the
    ``name`` set. A paired edit that touches only ``STANDARD_PROBES`` or
    only ``STANDARD_Z_PROBES`` — e.g. drifting CatWISE's sigma_cone_deg
    on the HJ-02a side while leaving the HJ-02b side frozen — would pass
    the registry test silently. This test zips the two SSOTs by ``name``
    and asserts the three direction-on-sky fields match exactly, forcing
    any sigma update to be a paired two-file edit (per A36a.4 / A36a.5).

    z_eff is intentionally *not* compared: ``DirectionalProbe`` does not
    carry a z_eff field (HJ-02a is z-agnostic by design — A36.1), so the
    parity contract is restricted to the direction-on-sky trio.
    """
    by_name_directional = {p.name: p for p in STANDARD_PROBES}
    by_name_z = {p.name: p for p in STANDARD_Z_PROBES}
    assert set(by_name_directional) == set(by_name_z), (
        "STANDARD_PROBES and STANDARD_Z_PROBES name-sets must match"
    )
    for name in sorted(by_name_directional):
        dp = by_name_directional[name]
        zp = by_name_z[name]
        assert dp.l_deg == zp.l_deg, (
            f"{name}: l_deg drift {dp.l_deg!r} (HJ-02a) vs "
            f"{zp.l_deg!r} (HJ-02b)"
        )
        assert dp.b_deg == zp.b_deg, (
            f"{name}: b_deg drift {dp.b_deg!r} (HJ-02a) vs "
            f"{zp.b_deg!r} (HJ-02b)"
        )
        assert dp.sigma_cone_deg == zp.sigma_cone_deg, (
            f"{name}: sigma_cone_deg drift {dp.sigma_cone_deg!r} (HJ-02a) "
            f"vs {zp.sigma_cone_deg!r} (HJ-02b)"
        )
