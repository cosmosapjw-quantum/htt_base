"""G19-ENFORCE-01 — Hard-separation enforcement tests.

INDEPENDENT_TRACKS_PLAN v1.2 §11.2 / BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN
v3 §10.2bis. Three enforcement layers:

    1. `MioCertificate.as_posterior_bundle()` raises NotImplementedError
       (exercised here + in test_mio_certificate.py — duplicated as a
       hard-separation regression anchor).
    2. HTT likelihood entry points cannot accept a MioCertificate as
       input without raising TypeError (natural duck-typing failure +
       explicit isinstance check at test level).
    3. The codebase contains no scalar-sum expression that merges
       `MioCertificate` evidence / score with HTT lnB / evidence
       (text-scan lint).
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from workspace.contracts import (
    AtlasEntry,
    HttForwardOutput,
    MioCertificate,
    PosteriorExportBundle,
)


def _certificate() -> MioCertificate:
    return MioCertificate(
        report_type="directional_coherence",
        probe_name="CMB",
        channel="dipole",
        departure_variables={"resultant_R": 0.91},
        adequacy_indicators={"isotropy_p_lt_0p01": True},
        consistency_metrics={"chi2_per_dof": 1.02},
        domain_caveats=[],
        channel_caveats=[],
        reduction_status="diagnostic-only",
        generated_by="test",
        git_commit="x",
        config_hash="y",
        input_data_hashes=[],
    )


# ---------------------------------------------------------------------------
# Layer 1 — MioCertificate cannot yield a posterior.
# ---------------------------------------------------------------------------

def test_mio_certificate_as_posterior_bundle_raises():
    with pytest.raises(NotImplementedError):
        _certificate().as_posterior_bundle()


# ---------------------------------------------------------------------------
# Layer 2 — HTT likelihoods reject MioCertificate inputs.
# ---------------------------------------------------------------------------

def test_g19_htt_cannot_ingest_miocertificate_as_likelihood():
    """HTT's directional likelihood signature is (l_deg, b_deg, sigma_deg)
    float scalars — passing a MioCertificate is a TypeError by duck-typing.
    """
    from htt.infer.directional_lowell import LowellLikelihood

    ll = LowellLikelihood()
    cert = _certificate()
    with pytest.raises((TypeError, AttributeError)):
        ll.directional_log_likelihood(cert, cert, cert)  # type: ignore[arg-type]


def test_g19_mio_certificate_not_a_posterior_export_bundle():
    """Structural check — MioCertificate is not a PosteriorExportBundle,
    so any HTT consumer type-hinted on PosteriorExportBundle excludes it.
    """
    cert = _certificate()
    assert not isinstance(cert, PosteriorExportBundle)


# ---------------------------------------------------------------------------
# Layer 3 — MIO outputs have no posterior-shaped fields.
# ---------------------------------------------------------------------------

def test_g19_mio_output_has_no_posterior_field():
    """No field named *posterior* on any MIO-owned contract."""
    import dataclasses

    for tp in (MioCertificate, AtlasEntry, HttForwardOutput):
        for f in dataclasses.fields(tp):
            assert "posterior" not in f.name.lower(), (
                f"{tp.__name__}.{f.name} violates v3 §10.2bis — "
                f"'posterior' token must not appear in non-HTT contract fields."
            )


# ---------------------------------------------------------------------------
# Layer 4 — Static lint: no scalar-sum expression merging MIO and HTT.
# ---------------------------------------------------------------------------

_FORBIDDEN_PATTERNS = [
    # MioCertificate.<field> + HTT-ish lnB / evidence (and commutations)
    re.compile(
        r"MioCertificate[^\n]*\.\s*(evidence_score|score|lnB|ln_B)"
        r"\s*\+\s*"
        r"(htt\.?|Htt|HTT)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(htt\.?|Htt|HTT)[^\n]*(lnB|ln_B|evidence)"
        r"\s*\+\s*"
        r"MioCertificate",
        re.IGNORECASE,
    ),
]

# Files that contain the banned pattern as *commentary* (docstrings, this
# test itself) must not trigger the scan. Restrict the lint to package
# production code: bass_py/bass, bass_py/htt/htt, bass_py/mio, bass_py/src,
# bass_py/tsc — excluding tests/ subtrees.
_SCAN_ROOTS = [
    "bass_py/bass",
    "bass_py/htt/htt",
    "bass_py/mio",
    "bass_py/src/common",
    "bass_py/tsc",
    "bass_py/workspace",
]


def _repo_root() -> Path:
    # test file lives at bass_py/workspace/contracts/tests/test_*.py
    # so repo root = parents[4]
    return Path(__file__).resolve().parents[4]


def test_g19_no_scalar_sum_of_mio_and_htt():
    root = _repo_root()
    offenders: list[tuple[str, int, str]] = []

    for rel in _SCAN_ROOTS:
        base = root / rel
        if not base.is_dir():
            continue
        for py in base.rglob("*.py"):
            if "/tests/" in str(py) or py.name.startswith("test_"):
                continue
            text = py.read_text(encoding="utf-8", errors="ignore")
            for n, line in enumerate(text.splitlines(), start=1):
                for pat in _FORBIDDEN_PATTERNS:
                    if pat.search(line):
                        offenders.append((str(py.relative_to(root)), n, line.strip()))

    assert not offenders, (
        "G19 violation: scalar sum of MioCertificate score with HTT lnB/evidence "
        "detected in production code (v3 §10.2bis):\n"
        + "\n".join(f"  {p}:{n}: {s}" for p, n, s in offenders)
    )
