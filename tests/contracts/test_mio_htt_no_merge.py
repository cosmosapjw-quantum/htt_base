from __future__ import annotations

import re
from pathlib import Path

import pytest

from common.contracts import ArtifactManifest
from workspace.contracts.mio_certificate import MioCertificate
from workspace.contracts.htt_posterior import (
    HTTPosteriorBundle,
    HttLikelihoodTerm,
    reject_mio_likelihood_inputs,
)


def _manifest(owner: str = "HTT", scope: str = "htt") -> ArtifactManifest:
    return ArtifactManifest(
        artifact_id=f"{owner.lower()}.test.artifact",
        artifact_path=f"artifacts/{owner.lower()}/artifact.json",
        owner=owner,
        implementation_scope=scope,
        claim_tier="conditional",
        production_status="production_candidate",
        created_by="test-suite",
        git_commit="abc123",
        config_hash="cfg",
        input_hashes=["input"],
        code_version="0.0-test",
        schema_version="pr013",
    )


def _certificate(**overrides: object) -> MioCertificate:
    payload: dict[str, object] = {
        "report_type": "directional_coherence",
        "probe_name": "CMB",
        "channel": "dipole",
        "departure_variables": {"resultant_R": 0.91},
        "adequacy_indicators": {"isotropy_p_lt_0p01": True},
        "consistency_metrics": {"isotropy_pvalue": 0.001},
        "domain_caveats": ["masked_sky_partial"],
        "channel_caveats": ["dipole_only"],
        "reduction_status": "diagnostic-only",
        "generated_by": "test-suite",
        "git_commit": "abc123",
        "config_hash": "cfg",
        "input_data_hashes": ["input"],
        "manifest": _manifest("MIO", "mio"),
    }
    payload.update(overrides)
    return MioCertificate(**payload)  # type: ignore[arg-type]


def _term(**overrides: object) -> HttLikelihoodTerm:
    payload: dict[str, object] = {
        "term_id": "htt.lowell.directional",
        "source_owner": "HTT",
        "log_likelihood_contribution": -1.25,
        "source_ref": "htt.directional.lowell",
        "caveats": ("htt_owned_likelihood_term",),
    }
    payload.update(overrides)
    return HttLikelihoodTerm(**payload)  # type: ignore[arg-type]


def test_certificate_declares_diagnostic_only_and_no_model_claim() -> None:
    cert = _certificate()

    assert cert.is_diagnostic_only is True
    assert cert.is_truth_claim is False


def test_mio_certificate_cannot_be_likelihood_term_or_posterior() -> None:
    cert = _certificate()

    with pytest.raises(NotImplementedError, match="not a posterior"):
        cert.as_posterior_bundle()
    with pytest.raises(TypeError, match="diagnostic-only"):
        cert.as_likelihood_term()


def test_htt_posterior_bundle_rejects_mio_certificate_as_likelihood_term() -> None:
    with pytest.raises(TypeError, match="MioCertificate"):
        HTTPosteriorBundle(
            bundle_id="htt.posterior.test",
            model="local_global_candidate",
            log_evidence=-2.0,
            likelihood_terms=(_certificate(),),
            manifest=_manifest(),
        )


def test_htt_likelihood_term_rejects_mio_source_owner() -> None:
    with pytest.raises(TypeError, match="MIO"):
        _term(source_owner="MIO")


def test_htt_likelihood_term_rejects_mio_pvalue_metadata() -> None:
    with pytest.raises(ValueError, match="mio_pvalue"):
        _term(metadata={"mio_pvalue": 0.01})


def test_htt_likelihood_term_rejects_nested_mio_diagnostic_metadata() -> None:
    with pytest.raises(ValueError, match="mio_score"):
        _term(metadata={"diagnostics": {"mio_score": 0.99}})


def test_htt_likelihood_term_rejects_nested_mio_certificate_payload() -> None:
    with pytest.raises(TypeError, match="MIO diagnostic payload"):
        _term(
            metadata={
                "diagnostics": {
                    "report_type": "directional_coherence",
                    "departure_variables": {"resultant_R": 0.91},
                    "adequacy_indicators": {"isotropy_p_lt_0p01": True},
                    "consistency_metrics": {"isotropy_pvalue": 0.001},
                    "reduction_status": "diagnostic-only",
                }
            }
        )


def test_htt_likelihood_term_rejects_dynamic_model_claim_key() -> None:
    key = "m" + "io_" + "truth"
    with pytest.raises(ValueError, match=key):
        _term(metadata={key: False})


def test_htt_posterior_guard_rejects_dict_like_mio_certificate_payload() -> None:
    with pytest.raises(TypeError, match="MIO diagnostic payload"):
        reject_mio_likelihood_inputs(
            {
                "owner": "MIO",
                "report_type": "directional_coherence",
                "departure_variables": {"resultant_R": 0.91},
                "consistency_metrics": {"isotropy_pvalue": 0.001},
            }
        )


def test_htt_posterior_guard_rejects_ownerless_mio_certificate_payload() -> None:
    with pytest.raises(TypeError, match="MIO diagnostic payload"):
        reject_mio_likelihood_inputs(
            {
                "report_type": "directional_coherence",
                "departure_variables": {"resultant_R": 0.91},
                "adequacy_indicators": {"isotropy_p_lt_0p01": True},
                "consistency_metrics": {"isotropy_pvalue": 0.001},
            }
        )


def test_htt_posterior_guard_rejects_raw_mio_diagnostic_keys() -> None:
    with pytest.raises(ValueError, match="mio_evidence"):
        reject_mio_likelihood_inputs({"mio_evidence": 0.2})


def test_valid_htt_posterior_bundle_accepts_only_htt_likelihood_terms() -> None:
    bundle = HTTPosteriorBundle(
        bundle_id="htt.posterior.test",
        model="local_global_candidate",
        log_evidence=-2.0,
        likelihood_terms=(_term(),),
        manifest=_manifest(),
        caveats=("transfer_conditional",),
    )

    assert bundle.owner == "HTT"
    assert bundle.bundle_kind == "posterior"
    assert bundle.likelihood_terms[0].source_owner == "HTT"


def test_htt_posterior_bundle_manifest_owner_must_be_htt() -> None:
    with pytest.raises(ValueError, match="must be 'HTT'"):
        HTTPosteriorBundle(
            bundle_id="htt.posterior.bad-owner",
            model="local_global_candidate",
            log_evidence=-2.0,
            likelihood_terms=(_term(),),
            manifest=_manifest("MIO", "mio"),
        )


def test_reject_mio_likelihood_inputs_guard_rejects_nested_certificate() -> None:
    with pytest.raises(TypeError, match="MioCertificate"):
        reject_mio_likelihood_inputs([_term(), _certificate()])


def test_static_firewall_scans_real_roots_for_mio_pvalue_evidence_leaks() -> None:
    repo = Path(__file__).resolve().parents[2]
    roots = [
        repo / "htt" / "workspace" / "contracts",
        repo / "htt" / "htt" / "htt",
        repo / "htt" / "mio",
        repo / "htt" / "src" / "common",
    ]
    scanned_files: list[Path] = []
    patterns = [
        re.compile(
            r"(mio_pvalue|mio_p_value|certificate_pvalue|mio_score|mio_evidence)"
            r".{0,120}"
            r"(log_evidence|log_likelihood|ln_B|lnB|model_evidences|posterior_weight|prior_weight)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(log_evidence|log_likelihood|ln_B|lnB|model_evidences|posterior_weight|prior_weight)"
            r".{0,120}"
            r"(mio_pvalue|mio_p_value|certificate_pvalue|mio_score|mio_evidence)",
            re.IGNORECASE,
        ),
    ]
    offenders: list[tuple[str, int, str]] = []

    for root in roots:
        assert root.is_dir(), f"PR-013 static scan root missing: {root}"
        for path in root.rglob("*.py"):
            if "/tests/" in str(path) or path.name.startswith("test_"):
                continue
            scanned_files.append(path)
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if any(pattern.search(line) for pattern in patterns):
                    offenders.append((str(path.relative_to(repo)), line_no, line.strip()))

    assert scanned_files, "PR-013 static scan did not inspect production files"
    assert not offenders, "MIO diagnostic scalar appears near HTT evidence terms: " + repr(offenders)
