"""A37 probe_name grammar acceptance tests (W12D1 / W11 F4 close).

Plan §2 Days 1-2, docs/INDEPENDENT_TRACKS_NEXT_SESSION.md W12D1. Enforces
the A37.2 grammar v1 on every MIO emitter that populates
``MioCertificate.probe_name``.

Grammar (A37.2 v1):

    probe_name  := singleton | bundle | atlas_label
    singleton   := PROBE_ID                              # e.g. "CMB"
    bundle      := PROBE_ID ("+" PROBE_ID)+              # alphabetical, no ws
    atlas_label := MODEL_ID ("_vs_" MODEL_ID | ("+" MODEL_ID)+)?
    PROBE_ID    := [A-Za-z][A-Za-z0-9]{0,23}
    MODEL_ID    := FLRW | BianchiI…IX | Tilted<Name>

Tests cover the three active emitters (HJ-01, HJ-02a, HJ-02b) against
two rules from A37.6:
  * ``probe_name == "+".join(sorted(...))`` for bundle-form outputs.
  * ``probe_name`` matches the grammar regex.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from mio.coherence.directional import STANDARD_PROBES, emit_directional_coherence_artefact
from mio.coherence.redshift_binned import STANDARD_Z_PROBES, emit_redshift_coherence_artefact
from mio.extraction.hj01_shear import (
    _bianchi_type_to_model_id,
    emit_shear_extraction_artefact,
)


# ---------------------------------------------------------------------------
# Grammar regex constants — literal transcription of A37.2 v1.
# ---------------------------------------------------------------------------

PROBE_ID_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,23}$")

MODEL_ID_RE = re.compile(
    r"^(?:FLRW"
    r"|BianchiI|BianchiII|BianchiV|BianchiVI(?:0|h)"
    r"|BianchiVII(?:0|h)|BianchiVIII|BianchiIX"
    r"|Tilted[A-Z][A-Za-z]+)$"
)

BUNDLE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9]{0,23}(?:\+[A-Za-z][A-Za-z0-9]{0,23})+$")

# atlas_label: MODEL_ID optionally suffixed with "_vs_MODEL_ID" or "+MODEL_ID"*.
# Reuse MODEL_ID regex body.
_MID = (
    r"(?:FLRW|BianchiI|BianchiII|BianchiV|BianchiVI(?:0|h)"
    r"|BianchiVII(?:0|h)|BianchiVIII|BianchiIX|Tilted[A-Z][A-Za-z]+)"
)
ATLAS_LABEL_RE = re.compile(
    r"^" + _MID + r"(?:(?:_vs_" + _MID + r")|(?:(?:\+" + _MID + r")+))?$"
)


def _matches_grammar_v1(name: str) -> bool:
    """True iff ``name`` parses as probe_name under A37.2 v1."""
    if PROBE_ID_RE.fullmatch(name) is not None:
        return True
    if BUNDLE_RE.fullmatch(name) is not None:
        return True
    if ATLAS_LABEL_RE.fullmatch(name) is not None:
        return True
    return False


# ---------------------------------------------------------------------------
# Self-tests for the regex constants themselves — guards against regressions
# in the test harness from masking real producer bugs.
# ---------------------------------------------------------------------------


def test_grammar_regex_accepts_registered_probe_ids():
    """The five A37.3 PROBE_IDs must each parse as a singleton."""
    for pid in ("CMB", "CatWISE", "Radio", "CF4pp", "BiPoSH"):
        assert PROBE_ID_RE.fullmatch(pid) is not None, pid
        assert _matches_grammar_v1(pid), pid


def test_grammar_regex_accepts_model_ids():
    """A37.2 MODEL_ID samples parse; unknown Bianchi tokens do not."""
    for mid in (
        "FLRW",
        "BianchiI", "BianchiII", "BianchiV",
        "BianchiVI0", "BianchiVIh",
        "BianchiVII0", "BianchiVIIh",
        "BianchiVIII", "BianchiIX",
        "TiltedOrthogonal",
    ):
        assert MODEL_ID_RE.fullmatch(mid) is not None, mid
        assert _matches_grammar_v1(mid), mid
    # Negative cases — legacy HJ-01 "atlas_name:bianchi_type" form uses ':'
    # which is not a legal separator anywhere in the A37.2 grammar.
    for bad in (
        "FLRW:I",
        "test_kl_atlas_v1:FLRW",
        "Bianchi-VIIh",        # '-' not allowed in PROBE_ID body
        "CMB CatWISE",         # whitespace forbidden (A37.2 rule 1)
        "",                    # empty
    ):
        assert not _matches_grammar_v1(bad), bad
    # And the bare Bianchi suffixes that HJ-01 used to emit verbatim are
    # now rejected as MODEL_IDs (even though they parse as singletons,
    # they do NOT parse as atlas_labels, which is what HJ-01 must emit).
    for bare in ("I", "II", "VIIh", "IX"):
        assert MODEL_ID_RE.fullmatch(bare) is None, bare


# ---------------------------------------------------------------------------
# HJ-01 shear extraction — singleton atlas_label (MODEL_ID only).
# ---------------------------------------------------------------------------


def _synthetic_kl(bianchi_type: str):
    ell = np.arange(2, 31, dtype=int)
    k_ell = 1.0 + 0.05 * np.sin(0.3 * ell.astype(float))
    c_lcdm = 1000.0 + 200.0 * np.exp(-0.1 * (ell - ell.min()).astype(float))
    sig_c = np.full(ell.size, 25.0, dtype=float)
    return {
        "ell": ell,
        "C_ell_obs": c_lcdm.copy(),
        "C_ell_lcdm": c_lcdm.copy(),
        "K_ell": k_ell,
        "sigma_C_ell": sig_c,
        "bianchi_type": bianchi_type,
        "atlas_name": "test_kl_atlas_v1",
        "generated_by": "test_probe_name_grammar",
        "git_commit": "synthetic",
        "config_hash": "synthetic",
    }


def test_probe_name_matches_grammar_v1_HJ01(tmp_path: Path):
    """HJ-01 emitter probe_name must be a valid atlas_label singleton."""
    # FLRW atlas — probe_name == "FLRW".
    payload_flrw = emit_shear_extraction_artefact(
        tmp_path / "mio_hj01_flrw.json",
        kl=_synthetic_kl(bianchi_type="FLRW"),
    )
    name_flrw = payload_flrw["certificate"]["probe_name"]
    assert name_flrw == "FLRW"
    assert _matches_grammar_v1(name_flrw)

    # Bianchi VIIh — bare "VIIh" input must normalise to "BianchiVIIh".
    payload_viih = emit_shear_extraction_artefact(
        tmp_path / "mio_hj01_viih.json",
        kl=_synthetic_kl(bianchi_type="VIIh"),
    )
    name_viih = payload_viih["certificate"]["probe_name"]
    assert name_viih == "BianchiVIIh"
    assert _matches_grammar_v1(name_viih)
    assert ":" not in name_viih  # Regression guard: no legacy "atlas:type" form.


def test_bianchi_type_to_model_id_handles_known_suffixes():
    """Every ``bianchi_type`` we ship in the W9 DOS-A13 atlas must normalise."""
    for (raw, expected) in [
        ("FLRW", "FLRW"),
        ("I", "BianchiI"),
        ("II", "BianchiII"),
        ("V", "BianchiV"),
        ("VI0", "BianchiVI0"),
        ("VIh", "BianchiVIh"),
        ("VII0", "BianchiVII0"),
        ("VIIh", "BianchiVIIh"),
        ("VIII", "BianchiVIII"),
        ("IX", "BianchiIX"),
        ("BianchiI", "BianchiI"),              # idempotent
        ("TiltedOrthogonal", "TiltedOrthogonal"),  # idempotent
    ]:
        got = _bianchi_type_to_model_id(raw)
        assert got == expected, f"{raw!r} -> {got!r} != {expected!r}"
        assert _matches_grammar_v1(got), got


# ---------------------------------------------------------------------------
# HJ-02a directional coherence — alphabetical bundle.
# ---------------------------------------------------------------------------


def test_probe_name_is_alphabetical_bundle_HJ02a(tmp_path: Path):
    """HJ-02a probe_name must equal the alphabetical "+"-join of probe names."""
    payload = emit_directional_coherence_artefact(
        tmp_path / "mio_directional_coherence_v1.json",
        n_mock=8,
    )
    name = payload["certificate"]["probe_name"]
    expected = "+".join(sorted(p.name for p in STANDARD_PROBES))
    assert name == expected, f"probe_name {name!r} != expected {expected!r}"


def test_probe_name_matches_grammar_v1_HJ02a(tmp_path: Path):
    payload = emit_directional_coherence_artefact(
        tmp_path / "mio_directional_coherence_v1.json",
        n_mock=8,
    )
    assert _matches_grammar_v1(payload["certificate"]["probe_name"])


# ---------------------------------------------------------------------------
# HJ-02b redshift-binned coherence — alphabetical bundle.
# ---------------------------------------------------------------------------


def test_probe_name_is_alphabetical_bundle_HJ02b(tmp_path: Path):
    payload = emit_redshift_coherence_artefact(
        tmp_path / "mio_redshift_coherence_v1.json",
        n_mock=8,
    )
    name = payload["certificate"]["probe_name"]
    expected = "+".join(sorted(p.name for p in STANDARD_Z_PROBES))
    assert name == expected, f"probe_name {name!r} != expected {expected!r}"


def test_probe_name_matches_grammar_v1_HJ02b(tmp_path: Path):
    payload = emit_redshift_coherence_artefact(
        tmp_path / "mio_redshift_coherence_v1.json",
        n_mock=8,
    )
    assert _matches_grammar_v1(payload["certificate"]["probe_name"])
