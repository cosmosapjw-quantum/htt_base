"""CONTRACTS-01 — MioCertificate schema tests (INDEPENDENT_TRACKS_PLAN v1.2 §11.1)."""
from __future__ import annotations

import dataclasses
import hashlib

import pytest

from workspace.contracts.mio_certificate import MioCertificate


def _certificate(**overrides):
    base = dict(
        report_type="directional_coherence",
        probe_name="CMB",
        channel="dipole",
        departure_variables={"resultant_R": 0.91},
        adequacy_indicators={"isotropy_p_lt_0p01": True},
        consistency_metrics={"chi2_per_dof": 1.02},
        domain_caveats=["masked_sky_partial"],
        channel_caveats=["dipole_only"],
        reduction_status="diagnostic-only",
        generated_by="mio.coherence.directional v0.1",
        git_commit="deadbeef",
        config_hash="cafef00d",
        input_data_hashes=["h1", "h2"],
    )
    base.update(overrides)
    return MioCertificate(**base)


def test_miocertificate_no_posterior_access():
    cert = _certificate()
    with pytest.raises(NotImplementedError, match="not a posterior"):
        cert.as_posterior_bundle()


def test_miocertificate_frozen():
    cert = _certificate()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cert.report_type = "shear_extraction"  # type: ignore[misc]


def test_miocertificate_schema_frozen():
    """Anti-regression: schema hash of (field name, field type str) tuple.

    If a field is added or renamed, this hash changes and the test must
    be updated consciously (v3 §10.2bis G19 contract freeze).
    """
    field_sig = [(f.name, str(f.type)) for f in dataclasses.fields(MioCertificate)]
    digest = hashlib.sha256(repr(field_sig).encode("utf-8")).hexdigest()[:16]
    expected = {
        "report_type", "probe_name", "channel",
        "departure_variables", "adequacy_indicators", "consistency_metrics",
        "domain_caveats", "channel_caveats", "reduction_status",
        "generated_by", "git_commit", "config_hash", "input_data_hashes",
        "htt_cross_check_suggested",
    }
    names = {n for n, _ in field_sig}
    assert names == expected, (
        f"MioCertificate schema drift: digest {digest}; "
        f"added={names - expected}; removed={expected - names}"
    )


def test_miocertificate_no_posterior_field_in_schema():
    """G19 first-line: 'posterior' keyword must not appear in any field name."""
    for f in dataclasses.fields(MioCertificate):
        assert "posterior" not in f.name.lower(), (
            f"MioCertificate must not expose a 'posterior' field "
            f"(found '{f.name}') — violates v3 §10.2bis G19."
        )
