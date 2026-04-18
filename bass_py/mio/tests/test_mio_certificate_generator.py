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

from mio.interface.mio_certificate import build_mio_certificate
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


def test_htt_cross_check_hint_is_not_a_posterior():
    """Cross-check hint is a descriptor dict, not a posterior."""
    cert = build_mio_certificate(
        **_base_payload(),
        htt_cross_check_suggested={"module": "htt.infer.directional_lowell"},
    )
    assert cert.htt_cross_check_suggested == {"module": "htt.infer.directional_lowell"}
    assert "posterior" not in str(cert.htt_cross_check_suggested).lower()
