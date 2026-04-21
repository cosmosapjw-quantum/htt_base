"""MIO-HJ-02b (W11D3-4) — redshift-binned directional-coherence tests.

Plan v1.3 §20 Week 11 Day 3-4 gate: 12 tests covering
  * probe catalogue SSOT + default z-bins
  * z-bin assignment (inclusive/exclusive edges + empty bins)
  * per-bin resultant (weighted spherical mean) matches HJ-02a algebra
  * total-drift statistic is 0 when all probes share one axis
  * permutation p-value is high when there is no real z-drift
  * permutation p-value is low when an explicit z-drift is injected
  * MioCertificate has `reduction_status='diagnostic-only'` and no posterior field
  * emit_redshift_coherence_artefact rejects non-`mio_` filenames (REG-02)
  * artefact payload schema is stable
  * JSON round-trip is pure
  * integration: STANDARD_Z_PROBES + DEFAULT_Z_BINS does not raise
  * drift_pvalue single-probe edge returns 1.0
"""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import numpy as np
import pytest

from mio.coherence.redshift_binned import (
    ARTEFACT_FILENAME,
    DEFAULT_Z_BINS,
    EXACT_ENUMERATION_MAX_PERMUTATIONS,
    RedshiftBinnedProbe,
    STANDARD_Z_PROBES,
    ZBinResult,
    assign_probes_to_bins,
    drift_pvalue,
    emit_redshift_coherence_artefact,
    pairwise_bin_separations,
    per_bin_resultants,
    to_mio_certificate,
    total_drift_deg,
)
from mio.tests._overlay_fixtures import build_pending_overlay
from workspace.contracts.mio_certificate import MioCertificate


# ---------------------------------------------------------------------------
# 1. SSOT catalogue + default z bins
# ---------------------------------------------------------------------------


def test_standard_z_probes_has_five_entries():
    assert len(STANDARD_Z_PROBES) == 5
    names = tuple(p.name for p in STANDARD_Z_PROBES)
    assert set(names) == {"CF4pp", "CatWISE", "Radio", "CMB", "BiPoSH"}


def test_default_z_bins_are_ordered_and_cover_cmb():
    # Bins must be strictly increasing and the final bin must include z ~ 1100.
    lows = [lo for lo, _ in DEFAULT_Z_BINS]
    assert lows == sorted(lows)
    last_lo, last_hi = DEFAULT_Z_BINS[-1]
    assert last_lo <= 1100.0 <= last_hi


# ---------------------------------------------------------------------------
# 2. Bin assignment
# ---------------------------------------------------------------------------


def test_assign_probes_to_bins_respects_inclusive_exclusive_edges():
    # Default bins: [0, 0.1), [0.1, 10.0), [100.0, 2000.0].
    # Put one probe exactly at each edge.
    probes = (
        RedshiftBinnedProbe("below", 0.0, 0.0, 5.0, z_eff=0.05),
        RedshiftBinnedProbe("edge_low",   0.0, 0.0, 5.0, z_eff=0.1),  # → bin 1
        RedshiftBinnedProbe("inside_mid", 0.0, 0.0, 5.0, z_eff=1.0),  # → bin 1
        RedshiftBinnedProbe("final_low",  0.0, 0.0, 5.0, z_eff=100.0),  # → bin 2
        RedshiftBinnedProbe("final_high", 0.0, 0.0, 5.0, z_eff=2000.0),  # → bin 2 (inclusive)
    )
    groups = assign_probes_to_bins(probes)
    assert [p.name for p in groups[0]] == ["below"]
    assert [p.name for p in groups[1]] == ["edge_low", "inside_mid"]
    assert [p.name for p in groups[2]] == ["final_low", "final_high"]


def test_assign_probes_to_bins_raises_on_invalid_bin():
    with pytest.raises(ValueError):
        assign_probes_to_bins([], bins=())
    with pytest.raises(ValueError):
        assign_probes_to_bins([], bins=[(0.1, 0.1)])


def test_assign_drops_probes_outside_all_bins():
    probes = (
        RedshiftBinnedProbe("in_bin_0",  0.0, 0.0, 5.0, z_eff=0.01),
        RedshiftBinnedProbe("beyond_all", 0.0, 0.0, 5.0, z_eff=5000.0),
        RedshiftBinnedProbe("between_gaps", 0.0, 0.0, 5.0, z_eff=50.0),
    )
    groups = assign_probes_to_bins(probes)
    flat = [p.name for grp in groups for p in grp]
    assert flat == ["in_bin_0"]


# ---------------------------------------------------------------------------
# 3. Per-bin resultant algebra
# ---------------------------------------------------------------------------


def test_per_bin_resultants_match_manual_spherical_mean():
    # Two identical probes in one bin + one alone in another + empty bin.
    probes = (
        RedshiftBinnedProbe("a", 250.0, 40.0, 5.0, z_eff=0.05),
        RedshiftBinnedProbe("b", 250.0, 40.0, 5.0, z_eff=0.07),
        RedshiftBinnedProbe("c", 100.0, -10.0, 8.0, z_eff=500.0),
    )
    # Custom 3-bin set: low (both a,b), mid (empty), high (c only).
    bins = ((0.0, 0.1), (0.1, 100.0), (100.0, 1200.0))
    results = per_bin_resultants(probes, bins)
    assert results[0].n_probes == 2
    assert results[0].probe_names == ("a", "b")
    # Two identical probes → resultant equals their common direction with R=1.
    assert results[0].resultant_R == pytest.approx(1.0, abs=1e-12)
    assert results[0].l_deg == pytest.approx(250.0, abs=1e-10)
    assert results[0].b_deg == pytest.approx(40.0, abs=1e-10)
    # Empty bin → n_probes=0, NaN direction, R=0.
    assert results[1].n_probes == 0
    assert np.isnan(results[1].l_deg)
    assert results[1].resultant_R == 0.0
    # Single probe in bin → axis matches probe exactly.
    assert results[2].n_probes == 1
    assert results[2].l_deg == pytest.approx(100.0, abs=1e-10)
    assert results[2].b_deg == pytest.approx(-10.0, abs=1e-10)


# ---------------------------------------------------------------------------
# 4. Drift statistic + permutation p-value
# ---------------------------------------------------------------------------


def test_total_drift_deg_zero_when_all_bins_share_axis():
    probes = (
        RedshiftBinnedProbe("a", 264.0, 48.0, 5.0, z_eff=0.02),
        RedshiftBinnedProbe("b", 264.0, 48.0, 5.0, z_eff=1.0),
        RedshiftBinnedProbe("c", 264.0, 48.0, 5.0, z_eff=1100.0),
    )
    results = per_bin_resultants(probes)
    assert total_drift_deg(results) == pytest.approx(0.0, abs=1e-8)


def test_drift_pvalue_high_when_directions_are_random_wrt_z():
    # All probes isotropic but with random z_eff labels: permutation
    # distribution should look like the observed (non-detection).
    rng = np.random.default_rng(seed=20260419)
    u = rng.uniform(-1.0, 1.0, size=9)
    phi = rng.uniform(0.0, 2 * np.pi, size=9)
    s = np.sqrt(1.0 - u * u)
    x, y, z = s * np.cos(phi), s * np.sin(phi), u
    l = np.rad2deg(np.arctan2(y, x)) % 360.0
    b = np.rad2deg(np.arcsin(np.clip(z, -1.0, 1.0)))
    z_eff = rng.uniform(0.01, 1.5, size=9)
    probes = tuple(
        RedshiftBinnedProbe(f"p{i}", float(l[i]), float(b[i]), 10.0, z_eff=float(z_eff[i]))
        for i in range(9)
    )
    # Custom two-bin split inside the populated range.
    bins = ((0.0, 0.5), (0.5, 2.0))
    p = drift_pvalue(probes, bins=bins, n_mock=2000, rng=np.random.default_rng(seed=11))
    assert p > 0.05, f"no-drift null falsely flagged: p={p:.4f}"


def test_drift_pvalue_low_when_z_is_perfectly_correlated_with_direction():
    # Inject a strong 3-bin correlation: low-z probes at axis A (+x),
    # mid-z at B (+y), high-z at C (+z). A, B, C are mutually orthogonal.
    # Observed drift = sep(A,B) + sep(B,C) = 90° + 90° = 180°. Permuting
    # z_eff mixes the axes within each bin — the mixed-axis resultants
    # lie closer together so the permutation distribution of the drift
    # statistic peaks well below 180°.
    low_probes = tuple(
        RedshiftBinnedProbe(f"lo{i}", 0.0, 0.0, 5.0, z_eff=0.01 + 0.001 * i)
        for i in range(4)
    )
    mid_probes = tuple(
        RedshiftBinnedProbe(f"md{i}", 90.0, 0.0, 5.0, z_eff=0.5 + 0.01 * i)
        for i in range(4)
    )
    high_probes = tuple(
        RedshiftBinnedProbe(f"hi{i}", 0.0, 90.0, 5.0, z_eff=1000.0 + i)
        for i in range(4)
    )
    bins = ((0.0, 0.1), (0.1, 10.0), (100.0, 2000.0))
    p = drift_pvalue(
        low_probes + mid_probes + high_probes,
        bins=bins, n_mock=1000, rng=np.random.default_rng(seed=22),
    )
    assert p < 0.05, f"strong z-drift not flagged: p={p:.4f}"


def test_drift_pvalue_single_probe_returns_one():
    probes = (RedshiftBinnedProbe("solo", 0.0, 0.0, 5.0, z_eff=0.5),)
    # n_mock=1 is the minimum; the single-probe branch short-circuits.
    p = drift_pvalue(probes, n_mock=1, rng=np.random.default_rng(seed=0))
    assert p == 1.0


# ---------------------------------------------------------------------------
# 5. Certificate is diagnostic-only + has no posterior field
# ---------------------------------------------------------------------------


def test_to_mio_certificate_has_no_posterior_field():
    probes = STANDARD_Z_PROBES
    results = per_bin_resultants(probes)
    p = drift_pvalue(probes, n_mock=200, rng=np.random.default_rng(seed=5))
    drift = total_drift_deg(results)
    cert = to_mio_certificate(probes, results, p_drift=p, total_drift=drift)

    assert isinstance(cert, MioCertificate)
    assert cert.reduction_status == "diagnostic-only"
    cert_dict = dataclasses.asdict(cert)
    flat = json.dumps(cert_dict).lower()
    # G19 enforcement: no "posterior" string anywhere in the serialised cert.
    assert "posterior" not in flat


# ---------------------------------------------------------------------------
# 6. Artefact emitter (REG-02 + round-trip)
# ---------------------------------------------------------------------------


def test_emit_rejects_non_mio_prefix_filename(tmp_path: Path):
    with pytest.raises(ValueError, match="REG-02"):
        emit_redshift_coherence_artefact(
            tmp_path / "bad_name.json",
            n_mock=10,
            rng=np.random.default_rng(seed=0),
        )


def test_emit_artefact_schema_is_stable(tmp_path: Path):
    overlay = build_pending_overlay()
    payload = emit_redshift_coherence_artefact(
        tmp_path / ARTEFACT_FILENAME,
        n_mock=50,
        rng=np.random.default_rng(seed=42),
        tsc_overlay=overlay,
    )
    expected_keys = {
        "schema_version", "probes", "bins", "bin_results",
        "total_drift_deg", "drift_pvalue", "n_mock",
        "pairwise_bin_separations_deg", "certificate",
    }
    assert set(payload.keys()) == expected_keys
    assert payload["schema_version"] == "v1"
    assert payload["certificate"]["tsc_overlay_ref"] == "tsc.overlay"
    # JSON round-trip: the on-disk file parses back to the same dict.
    round_trip = json.loads((tmp_path / ARTEFACT_FILENAME).read_text(encoding="utf-8"))
    assert round_trip == payload


def test_emit_artefact_with_standard_probes_smoke(tmp_path: Path):
    # Integration: default catalogue + default bins through the full emitter.
    payload = emit_redshift_coherence_artefact(
        tmp_path / ARTEFACT_FILENAME,
        n_mock=20,
        rng=np.random.default_rng(seed=7),
    )
    assert len(payload["bin_results"]) == len(DEFAULT_Z_BINS)
    # Each standard probe must be placed into some bin (none silently dropped).
    all_names = sum((r["probe_names"] for r in payload["bin_results"]), [])
    assert set(all_names) == {p.name for p in STANDARD_Z_PROBES}


# ---------------------------------------------------------------------------
# 7. Pairwise separation helper
# ---------------------------------------------------------------------------


def test_pairwise_bin_separations_is_symmetric_with_zero_diagonal():
    probes = (
        RedshiftBinnedProbe("a", 0.0,   0.0, 5.0, z_eff=0.05),
        RedshiftBinnedProbe("b", 90.0,  0.0, 5.0, z_eff=1.0),
        RedshiftBinnedProbe("c", 180.0, 0.0, 5.0, z_eff=1100.0),
    )
    results = per_bin_resultants(probes)
    sep = pairwise_bin_separations(results)
    assert sep.shape == (3, 3)
    assert np.allclose(np.diag(sep), 0.0, atol=1e-10)
    assert np.allclose(sep, sep.T, atol=1e-10)


# ---------------------------------------------------------------------------
# 8. W12D3 — exact-enumeration path for drift_pvalue (W11 F1 close).
# ---------------------------------------------------------------------------


def _orthogonal_three_bin_probes():
    """Build a 6-probe / 3-bin fixture with injected z-drift (6! = 720)."""
    return (
        RedshiftBinnedProbe("lo0", 0.0,   0.0, 5.0, z_eff=0.01),
        RedshiftBinnedProbe("lo1", 0.0,   0.0, 5.0, z_eff=0.02),
        RedshiftBinnedProbe("md0", 90.0,  0.0, 5.0, z_eff=0.5),
        RedshiftBinnedProbe("md1", 90.0,  0.0, 5.0, z_eff=0.6),
        RedshiftBinnedProbe("hi0", 0.0,  90.0, 5.0, z_eff=1000.0),
        RedshiftBinnedProbe("hi1", 0.0,  90.0, 5.0, z_eff=1100.0),
    )


def test_exact_enumeration_max_permutations_is_tractable():
    """The ceiling must be ≥ 7! so typical N ≤ 7 fixtures enumerate.

    Also: the ceiling must exclude 8! = 40 320 so test authors don't
    accidentally stall a smoke run on an 8-probe exact call.
    """
    import math as _math
    assert EXACT_ENUMERATION_MAX_PERMUTATIONS >= _math.factorial(7)
    assert EXACT_ENUMERATION_MAX_PERMUTATIONS < _math.factorial(8)


def test_drift_pvalue_exact_is_deterministic():
    """Two exact calls must give bit-identical p-values (no RNG dependence)."""
    probes = _orthogonal_three_bin_probes()
    bins = ((0.0, 0.1), (0.1, 10.0), (100.0, 2000.0))
    p1 = drift_pvalue(probes, bins=bins, exact=True)
    p2 = drift_pvalue(probes, bins=bins, exact=True,
                      rng=np.random.default_rng(seed=42))
    assert p1 == p2
    # And repeat calls with an unused kwarg must not drift.
    p3 = drift_pvalue(probes, bins=bins, n_mock=12345, exact=True)
    assert p1 == p3


def test_drift_pvalue_exact_matches_mc_at_small_N():
    """Exact p-value should agree with MC (n=2000) to within ~2-3 decimals."""
    probes = _orthogonal_three_bin_probes()
    bins = ((0.0, 0.1), (0.1, 10.0), (100.0, 2000.0))
    p_exact = drift_pvalue(probes, bins=bins, exact=True)
    p_mc = drift_pvalue(
        probes, bins=bins, n_mock=2000,
        rng=np.random.default_rng(seed=20260419),
    )
    # MC uses Lidstone smoothing (+1/+1) so allow a generous tol; 6!=720
    # permutations give deterministic exact while MC is stochastic.
    assert abs(p_exact - p_mc) < 0.05, (
        f"exact={p_exact:.4f} vs mc={p_mc:.4f}; delta too large"
    )


def test_drift_pvalue_exact_returns_count_over_n_factorial():
    """Exact p-value is a rational of form k/N!, not the MC (k+1)/(N+1)
    smoothed form. Verifies by asserting ``p * N!`` is an integer within
    floating-point tolerance."""
    import math as _math
    probes = _orthogonal_three_bin_probes()
    bins = ((0.0, 0.1), (0.1, 10.0), (100.0, 2000.0))
    p = drift_pvalue(probes, bins=bins, exact=True)
    n_fact = _math.factorial(len(probes))  # 6! = 720
    k = p * n_fact
    assert abs(k - round(k)) < 1e-9, (
        f"p={p} is not of the form k/{n_fact}; k={k}"
    )
    # And k must lie in [1, N!] (tie-inclusive count guarantees ≥ 1).
    assert 1 <= round(k) <= n_fact


def test_drift_pvalue_exact_raises_on_oversize_N():
    """N=8 triggers 40 320 permutations > ceiling → clear ValueError."""
    # 8 distinct z_eff labels + mutually orthogonal axes.
    probes = tuple(
        RedshiftBinnedProbe(
            f"p{i}",
            l_deg=90.0 * (i % 4),
            b_deg=30.0 * ((i // 4) - 0.5),
            sigma_cone_deg=5.0,
            z_eff=float(i + 1),
        )
        for i in range(8)
    )
    with pytest.raises(ValueError, match="40320"):
        drift_pvalue(probes, exact=True)


def test_drift_pvalue_exact_single_probe_returns_one():
    """Single-probe short-circuit is independent of ``exact``."""
    probes = (RedshiftBinnedProbe("solo", 0.0, 0.0, 5.0, z_eff=0.5),)
    assert drift_pvalue(probes, exact=True) == 1.0
