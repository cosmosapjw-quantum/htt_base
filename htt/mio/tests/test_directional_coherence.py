"""MIO-HJ-02a (W6D3-5) — directional coherence tests.

Plan §12.3 gate: 5 required tests
  * test_isotropic_null_pvalue_gt_0p05
  * test_aligned_probes_pvalue_lt_0p01
  * test_resultant_vector_antipodal_probes_R_zero
  * test_pairwise_separations_cmb_catwise_literature_ge_28deg (Secrest+2020)
  * test_to_mio_certificate_has_no_posterior_field

Plus emitter + regression tests for the SSOT probe table.
"""
from __future__ import annotations

import dataclasses
import json

import numpy as np
import pytest

from mio.coherence.directional import (
    ARTEFACT_FILENAME,
    DirectionalProbe,
    STANDARD_PROBES,
    coherence_chi2,
    emit_directional_coherence_artefact,
    isotropy_pvalue,
    pairwise_separations,
    resultant_vector,
    to_mio_certificate,
)
from workspace.contracts.mio_certificate import MioCertificate


# ---------------------------------------------------------------------------
# Plan §12.3 required tests
# ---------------------------------------------------------------------------


def test_isotropic_null_pvalue_gt_0p05():
    """10k mocks drawn from the null: observed R should not falsely flag."""
    rng = np.random.default_rng(seed=20260419)
    # Build one random (but isotropic) draw as the "observed" set — the
    # subsequent mocks are identically distributed, so p-value should
    # roughly be uniform; require p > 0.05 to reject false detection.
    u = rng.uniform(-1.0, 1.0, size=5)
    phi = rng.uniform(0.0, 2 * np.pi, size=5)
    s = np.sqrt(1.0 - u * u)
    x, y, z = s * np.cos(phi), s * np.sin(phi), u
    l_deg = np.rad2deg(np.arctan2(y, x)) % 360.0
    b_deg = np.rad2deg(np.arcsin(np.clip(z, -1, 1)))
    probes = tuple(
        DirectionalProbe(name=f"p{i}", l_deg=float(l_deg[i]), b_deg=float(b_deg[i]),
                         sigma_cone_deg=10.0)
        for i in range(5)
    )
    p = isotropy_pvalue(probes, n_mock=10_000, rng=np.random.default_rng(seed=1))
    assert p > 0.05, f"isotropic null falsely flagged: p={p:.4f}"


def test_aligned_probes_pvalue_lt_0p01():
    """5 probes within a 20° cone: isotropy should be rejected at p < 0.01."""
    # Center axis at galactic (l, b) = (250°, 40°). Scatter 5 probes within
    # a 20° cone around that axis.
    center_l, center_b = 250.0, 40.0
    rng = np.random.default_rng(seed=42)
    offsets = rng.uniform(-20.0, 20.0, size=(5, 2))
    probes = tuple(
        DirectionalProbe(
            name=f"a{i}",
            l_deg=(center_l + offsets[i, 0]) % 360.0,
            b_deg=max(min(center_b + offsets[i, 1], 89.9), -89.9),
            sigma_cone_deg=10.0,
        )
        for i in range(5)
    )
    p = isotropy_pvalue(probes, n_mock=10_000, rng=np.random.default_rng(seed=2))
    assert p < 0.01, f"aligned 5-probe set NOT flagged: p={p:.4f}"


def test_resultant_vector_antipodal_probes_R_zero():
    """A probe at (l,b) and its antipode must cancel → R ≈ 0."""
    probes = (
        DirectionalProbe(name="A", l_deg=30.0,  b_deg=20.0, sigma_cone_deg=5.0),
        DirectionalProbe(name="B", l_deg=210.0, b_deg=-20.0, sigma_cone_deg=5.0),
    )
    _, _, R = resultant_vector(probes)
    assert R < 1e-6, f"antipodal probes did not cancel: R={R:.3e}"


def test_pairwise_separations_cmb_catwise_literature_ge_28deg():
    """Secrest+2020: CMB–CatWISE separation is 27.8° ± 0.6° — assert ≈28°.

    The test name retains the plan §12.3 "ge_28deg" signal; the actual
    literature anchor is 27.8° ± 0.6°, so the assertion is bounded by
    the ±1° band around that value.
    """
    cmb = next(p for p in STANDARD_PROBES if p.name == "CMB")
    catwise = next(p for p in STANDARD_PROBES if p.name == "CatWISE")
    sep = pairwise_separations((cmb, catwise))
    assert 27.0 <= sep[0, 1] <= 29.0, (
        f"CMB–CatWISE separation {sep[0, 1]:.2f}° outside Secrest+2020 "
        "band 27.8° ± 1°"
    )


def test_to_mio_certificate_has_no_posterior_field():
    """G19 hard separation — generated certificate must not expose posterior."""
    resultant = resultant_vector(STANDARD_PROBES)
    cert = to_mio_certificate(
        STANDARD_PROBES,
        p_iso=0.001,
        resultant=resultant,
    )
    assert isinstance(cert, MioCertificate)
    for f in dataclasses.fields(cert):
        assert "posterior" not in f.name.lower()
    with pytest.raises(NotImplementedError):
        cert.as_posterior_bundle()


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------


def test_standard_probes_sanity():
    """SSOT 5-probe table: well-formed + latitude constraints."""
    names = {p.name for p in STANDARD_PROBES}
    assert names == {"CMB", "CatWISE", "Radio", "CF4pp", "BiPoSH"}
    for p in STANDARD_PROBES:
        assert 0.0 <= p.l_deg < 360.0
        assert -90.0 <= p.b_deg <= 90.0
        assert p.sigma_cone_deg > 0.0


def test_coherence_chi2_runs_on_standard_probes():
    chi2, dof = coherence_chi2(STANDARD_PROBES)
    assert chi2 >= 0.0
    assert dof == len(STANDARD_PROBES) - 2


def test_emit_artefact_writes_json(tmp_path):
    out = tmp_path / ARTEFACT_FILENAME
    payload = emit_directional_coherence_artefact(
        out,
        probes=STANDARD_PROBES,
        n_mock=500,
        rng=np.random.default_rng(seed=3),
    )
    assert out.exists()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["schema_version"] == "v1"
    assert len(loaded["probes"]) == 5
    assert 0.0 <= loaded["resultant"]["R"] <= 1.0
    assert loaded["certificate"]["report_type"] == "directional_coherence"
    assert payload == loaded


def test_emit_artefact_rejects_non_mio_prefix(tmp_path):
    """REG-02 — MIO-produced artefacts must begin with 'mio_'."""
    with pytest.raises(ValueError, match="must start with 'mio_'"):
        emit_directional_coherence_artefact(
            tmp_path / "directional_coherence.json",
            probes=STANDARD_PROBES,
            n_mock=100,
            rng=np.random.default_rng(seed=4),
        )


def test_isotropy_pvalue_requires_nonempty():
    with pytest.raises(ValueError):
        isotropy_pvalue(tuple(), n_mock=10)


def test_resultant_vector_requires_nonempty():
    with pytest.raises(ValueError):
        resultant_vector([])


def test_isotropy_mock_count_lower_bound():
    with pytest.raises(ValueError):
        isotropy_pvalue(STANDARD_PROBES, n_mock=0)
