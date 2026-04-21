"""MIO-HJ-06a (W6D2) — `build_mio_certificate` generator tests.

Plan §12.4 gate: 3 required tests
  * `test_build_certificate_frozen`
  * `test_build_rejects_posterior_keyword`
  * `test_provenance_auto_populated`

Plus a G19 cross-check reusing `MioCertificate.as_posterior_bundle()`.
"""
from __future__ import annotations

import dataclasses

import pytest

from mio.interface.mio_certificate import build_mio_certificate, certificate_to_payload
from mio.tests._overlay_fixtures import build_pending_overlay
from workspace.contracts.mio_certificate import MioCertificate


def _base_payload():
    return dict(
        report_type="directional_coherence",
        probe_name="CMB",
        channel="dipole",
        departure_variables={"resultant_R": 0.91},
        adequacy_indicators={"isotropy_p_lt_0p01": True},
        consistency_metrics={"chi2_per_dof": 1.02},
        domain_caveats=["masked_sky_partial"],
        reduction_status="diagnostic-only",
        generated_by="mio.coherence.directional v0.1",
        input_data_hashes=["h1", "h2"],
    )


def test_build_certificate_frozen():
    cert = build_mio_certificate(**_base_payload())
    assert isinstance(cert, MioCertificate)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cert.report_type = "shear_extraction"  # type: ignore[misc]


def test_build_rejects_posterior_keyword():
    payload = _base_payload()
    with pytest.raises(ValueError, match="MIO cannot generate posteriors"):
        build_mio_certificate(**payload, posterior_samples={"x": [1, 2, 3]})
    with pytest.raises(ValueError, match="MIO cannot generate posteriors"):
        build_mio_certificate(**payload, posterior_mean=0.5)


def test_provenance_auto_populated():
    cert = build_mio_certificate(**_base_payload())
    assert cert.git_commit, "git_commit must not be empty"
    assert cert.git_commit != "", "git_commit must not be empty string"
    assert len(cert.config_hash) == 16, "config_hash is a 16-char sha256 prefix"
    assert cert.config_hash.isalnum()


def test_generator_output_preserves_g19_contract():
    """Cross-check: generated cert still raises NotImplementedError on
    as_posterior_bundle() — proves build didn't silently substitute a
    posterior-bearing subclass.
    """
    cert = build_mio_certificate(**_base_payload())
    with pytest.raises(NotImplementedError):
        cert.as_posterior_bundle()


def test_generator_rejects_unknown_kwargs():
    """Any kwarg not in the schema + not matching 'posterior' rule is TypeError."""
    payload = _base_payload()
    with pytest.raises(TypeError, match="unexpected keyword"):
        build_mio_certificate(**payload, evidence_score=0.5)


def test_config_hash_is_deterministic_for_same_payload():
    """Identical diagnostic payload → identical config_hash (idempotency)."""
    p = _base_payload()
    a = build_mio_certificate(**p)
    b = build_mio_certificate(**p)
    assert a.config_hash == b.config_hash


def test_config_hash_changes_with_payload():
    """Distinct diagnostic content → distinct config_hash."""
    p1 = _base_payload()
    p2 = _base_payload()
    p2["departure_variables"] = {"resultant_R": 0.42}
    a = build_mio_certificate(**p1)
    b = build_mio_certificate(**p2)
    assert a.config_hash != b.config_hash


def test_caller_overrides_are_honoured():
    cert = build_mio_certificate(
        **_base_payload(),
        git_commit="pinned-sha",
        config_hash="pinned-hash",
    )
    assert cert.git_commit == "pinned-sha"
    assert cert.config_hash == "pinned-hash"


def test_channel_caveats_default_empty_list():
    cert = build_mio_certificate(**_base_payload())
    assert cert.channel_caveats == []


def test_tsc_overlay_ref_only_marks_attachment_without_overlay_fields():
    cert = build_mio_certificate(
        **_base_payload(),
        tsc_overlay_ref="tsc.overlay.external",
    )
    assert cert.tsc_overlay_ref == "tsc.overlay.external"
    assert cert.adequacy_indicators["tsc_overlay_attached"] is True
    assert "tsc_overlay_diagnostic_only" not in cert.adequacy_indicators
    assert "tsc_overlay_diagnostic_only" not in cert.domain_caveats
    assert cert.channel_caveats == []


def test_tsc_overlay_object_populates_default_ref_and_overlay_caveats():
    overlay = build_pending_overlay()
    cert = build_mio_certificate(
        **_base_payload(),
        tsc_overlay=overlay,
    )
    assert cert.tsc_overlay_ref == "tsc.overlay"
    assert cert.adequacy_indicators["tsc_overlay_attached"] is True
    assert cert.adequacy_indicators["tsc_overlay_diagnostic_only"] is True
    assert "tsc_overlay_diagnostic_only" in cert.domain_caveats
    assert any(
        caveat.startswith("tsc_channel_responsibility:")
        for caveat in cert.channel_caveats
    )


def test_explicit_overlay_ref_overrides_overlay_manifest_ref():
    overlay = build_pending_overlay()
    cert = build_mio_certificate(
        **_base_payload(),
        tsc_overlay=overlay,
        tsc_overlay_ref="tsc.overlay.alias",
    )
    assert cert.tsc_overlay_ref == "tsc.overlay.alias"


def test_certificate_payload_serializes_overlay_ref():
    cert = build_mio_certificate(
        **_base_payload(),
        tsc_overlay_ref="tsc.overlay.external",
    )
    payload = certificate_to_payload(cert)
    assert payload["tsc_overlay_ref"] == "tsc.overlay.external"


def test_htt_cross_check_hint_is_not_a_posterior():
    """Cross-check hint is a descriptor dict, not a posterior."""
    cert = build_mio_certificate(
        **_base_payload(),
        htt_cross_check_suggested={"module": "htt.infer.directional_lowell"},
    )
    assert cert.htt_cross_check_suggested == {"module": "htt.infer.directional_lowell"}
    assert "posterior" not in str(cert.htt_cross_check_suggested).lower()


def test_hash_config_matches_a45_2_pseudocode_shape():
    """W18D1 (W17 F1 / W17 R1) — docs-↔-code anchor for `_hash_config`.

    `docs/dossier/A45_mio_cache_replay_drift.md` §A45.2 names
    `_hash_config` as the re-hashing helper its `verify_cache_replay`
    pseudocode calls with the six-field payload tuple
    (`report_type`, `probe_name`, `channel`, `departure_variables`,
    `adequacy_indicators`, `consistency_metrics`). This test anchors
    that signature + output-shape pair in code: a silent rename of the
    helper (import fails), a signature reorder, or a change to the
    16-char lowercase-hex output shape all fail loudly and point the
    HJ-03 author at §A45.2 (which paste-copies §A45.6's five-test
    block).

    W19D1 (W18 F1 / W18 R1) — kwarg-evolution hedge: extends the
    anchor with an `inspect.signature(_hash_config).parameters`
    frozen-list assertion. The W18D1 anchor passed a positional call
    with six arguments against a `*parts` variadic form and would
    silently keep passing if a future refactor added a keyword-only
    argument (e.g. `*, digest_length=16` to introduce A43's
    schema-hash digest upgrade). The added assertion freezes both the
    parameter list (`("parts",)`) and the kind (`VAR_POSITIONAL`) so
    the HJ-03 author paste-copying §A45.6 is flagged at anchor time
    if §A45.2 grows a new kwarg that the pseudocode does not forward.

    **Anchor scope (W19 F3 / W20D1).** The frozen-list assertion
    intentionally trips on three refactor kinds: (i) the A43
    schema-hash digest upgrade (§A43.3 trigger; e.g. `*,
    digest_length=16`) — REQUIRES a paired §A45.2 edit in the same
    PR; (ii) a cache-replay strict-mode flag (e.g. `*, strict=True`)
    added independently of A43 — MAY require an §A45.2 edit if the
    pseudocode forwards the flag, otherwise is a pure signature
    bump; (iii) any non-`*parts` signature shape change (reorder,
    rename, or promotion to positional-or-keyword) — caller's
    judgement on whether §A45.2's pseudocode needs re-derivation
    per §A47.6's single-PR rule. A hit on kind (ii) or (iii) does
    not automatically mandate a dossier edit; the assertion message
    names §A45.2 because that is the most common fix site, not the
    only one.
    """
    import inspect
    import string

    from mio.interface.mio_certificate import _hash_config

    assert _hash_config.__name__ == "_hash_config", (
        "A45.2 pseudocode names the helper `_hash_config`; a rename "
        "requires updating §A45.2 in the same PR."
    )

    EXPECTED_PARAM_NAMES = ("parts",)
    EXPECTED_PARAM_KINDS = (inspect.Parameter.VAR_POSITIONAL,)
    sig_params = inspect.signature(_hash_config).parameters
    actual_names = tuple(sig_params)
    actual_kinds = tuple(p.kind for p in sig_params.values())
    assert actual_names == EXPECTED_PARAM_NAMES, (
        f"_hash_config parameter list drifted from A45.2 pseudocode: "
        f"expected {EXPECTED_PARAM_NAMES}, got {actual_names}. A new "
        "keyword-only argument (e.g. `*, digest_length=16` for the "
        "A43 schema-hash digest upgrade) must be reflected in "
        "§A45.2's `verify_cache_replay` pseudocode in the same PR."
    )
    assert actual_kinds == EXPECTED_PARAM_KINDS, (
        f"_hash_config parameter kind drifted from A45.2: expected "
        f"{EXPECTED_PARAM_KINDS}, got {actual_kinds}. The `*parts` "
        "variadic form is what §A45.2's six-field tuple unpack "
        "relies on; a change to POSITIONAL_OR_KEYWORD or "
        "KEYWORD_ONLY would break the paste-ready block in §A45.6."
    )

    payload = _base_payload()
    digest = _hash_config(
        payload["report_type"],
        payload["probe_name"],
        payload["channel"],
        payload["departure_variables"],
        payload["adequacy_indicators"],
        payload["consistency_metrics"],
    )

    assert isinstance(digest, str), "digest must be a str"
    assert len(digest) == 16, (
        f"A45.2 assumes a 16-char sha256 prefix; got len={len(digest)}"
    )
    assert digest == digest.lower(), "digest must be lowercase-hex"
    assert set(digest).issubset(set(string.hexdigits.lower())), (
        "digest must be hexadecimal"
    )

    cert = build_mio_certificate(**payload)
    assert cert.config_hash == digest, (
        "config_hash computed inside build_mio_certificate must match "
        "the direct _hash_config call on the same six-field tuple; "
        "otherwise A45.2's recomputed_config_hash step would drift."
    )
