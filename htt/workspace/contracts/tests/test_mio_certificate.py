"""CONTRACTS-01 — MioCertificate schema tests (INDEPENDENT_TRACKS_PLAN v1.2 §11.1)."""
from __future__ import annotations

import dataclasses
import hashlib

import pytest

from common.contracts import ArtifactManifest
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
        "manifest",
        "tsc_overlay_ref",
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


def test_git_commit_is_capture_time_not_lazy(monkeypatch):
    """W17D1 (W16 F2) — A44.3 runtime gate on at-instantiation capture.

    A44.3 pins provenance-SHA resolution to MioCertificate.__init__ time
    (per W6 FM6 / W11 F5). If a future refactor moves git_commit onto a
    lazy property / descriptor that re-resolves HEAD at read time, this
    test fails loudly. Mechanism: patch the helper that COULD re-resolve
    HEAD (subprocess.run here, since `workspace.contracts.mio_certificate`
    imports nothing git-related today — so the plain-string contract is
    the invariant being locked).
    """
    import subprocess as _subprocess
    import workspace.contracts.mio_certificate as mod

    captured_sha = "a1b2c3d4e5f60718293a4b5c6d7e8f9011223344"
    cert = _certificate(git_commit=captured_sha)

    def _raise_if_called(*_args, **_kwargs):
        raise AssertionError(
            "git_commit read path must not invoke subprocess — A44.3 "
            "requires at-instantiation capture."
        )

    monkeypatch.setattr(_subprocess, "run", _raise_if_called)
    if hasattr(mod, "_resolve_git_commit"):
        monkeypatch.setattr(
            mod, "_resolve_git_commit", lambda: "FFFFFFFFFFFFFFFF"
        )

    assert cert.git_commit == captured_sha
    assert dataclasses.asdict(cert)["git_commit"] == captured_sha
    assert isinstance(type(cert).__dict__.get("git_commit", None), type(None)), (
        "git_commit must be a plain dataclass field on the instance, "
        "not a class-level descriptor / property that could re-resolve."
    )


def test_miocertificate_manifest_owner_must_be_mio():
    manifest = ArtifactManifest(
        artifact_id="mio.bad-owner",
        artifact_path="artifacts/htt/mio.json",
        owner="HTT",
        implementation_scope="htt",
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg1",
        input_hashes=["x"],
        code_version="0.0-test",
        schema_version="ver2-v0",
    )
    with pytest.raises(ValueError, match="must be 'MIO'"):
        _certificate(manifest=manifest)


def test_miocertificate_accepts_overlay_hook():
    cert = _certificate(tsc_overlay_ref="tsc:overlay:001")
    assert cert.tsc_overlay_ref == "tsc:overlay:001"
