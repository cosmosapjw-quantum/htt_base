"""Regression anchors for MIO HJ-02 directional + redshift-binned coherence.

Companion to ``htt/tests/test_production_anchors.py`` (HTT-side) and
``tsc/integration/test_htt_bridge_production_anchors.py`` (TSC-side).

Pins bit-identical output from the HJ-02a / HJ-02b production SSOT:

  * ``mio.coherence.directional.STANDARD_PROBES`` — the 5 literature
    anchors (Planck CMB, CatWISE, Radio, CF4++, BiPoSH) whose
    (l, b, σ_cone) triple is the production source-of-truth.
  * A canonical 5-probe fixture covering all three
    ``redshift_binned.DEFAULT_Z_BINS`` = [(0, 0.1), (0.1, 10), (100, 2000)].

Any drift in those SSOT coordinates, the inverse-variance weighting, the
spherical-mean arithmetic, the χ² definition, or the permutation /
isotropy Monte Carlo plumbing will fire at least one test here. None of
the tests depend on BASS outputs — HJ-02 is the "completely independent"
MIO diagnostic per plan §16.2.
"""
from __future__ import annotations

import numpy as np
import pytest

from mio.coherence.directional import (
    STANDARD_PROBES,
    coherence_chi2,
    isotropy_pvalue,
    pairwise_separations,
    resultant_vector,
)
from mio.coherence.redshift_binned import (
    DEFAULT_Z_BINS,
    RedshiftBinnedProbe,
    drift_pvalue,
    per_bin_resultants,
    total_drift_deg,
)


# ═══════════════════════════════════════════════════════════════════════
# Part 1 — HJ-02a directional coherence (5-probe STANDARD_PROBES SSOT)
# ═══════════════════════════════════════════════════════════════════════

# Measured bit-identical on 2026-04-24; determinism verified across
# repeated calls with the same seed/rng.
_DIRECTIONAL_RESULTANT = {
    "l_best_deg": 263.776994834410,
    "b_best_deg":  48.121598863610,
    "R":            0.998952068364,
}
_DIRECTIONAL_CHI2 = {
    "chi2": 28.339536851487,
    "dof":  3,
}
# pairwise separation matrix first row (CMB vs others), degrees
_DIRECTIONAL_PAIRWISE_CMB_ROW = [
    0.0,
    27.790333,   # CMB-CatWISE
    13.941962,   # CMB-Radio
    26.395632,   # CMB-CF4pp
    28.533523,   # CMB-BiPoSH
]


def test_standard_probes_ssot_frozen():
    """The 5-probe SSOT coordinates are literature anchors — freeze them.

    Any silent edit to ``STANDARD_PROBES`` (e.g. a CatWISE re-analysis that
    ships a 238.4° longitude) must be explicit — not a drive-by constant.
    """
    names = [p.name for p in STANDARD_PROBES]
    assert names == ["CMB", "CatWISE", "Radio", "CF4pp", "BiPoSH"]

    cmb, catwise, radio, cf4, biposh = STANDARD_PROBES
    assert (cmb.l_deg, cmb.b_deg, cmb.sigma_cone_deg) == (264.021, 48.253, 0.5)
    assert (catwise.l_deg, catwise.b_deg, catwise.sigma_cone_deg) == (238.2, 28.8, 6.0)
    assert (radio.l_deg, radio.b_deg, radio.sigma_cone_deg) == (251.0, 38.0, 10.0)
    assert (cf4.l_deg, cf4.b_deg, cf4.sigma_cone_deg) == (289.0, 30.0, 15.0)
    assert (biposh.l_deg, biposh.b_deg, biposh.sigma_cone_deg) == (220.0, 65.0, 20.0)


def test_resultant_vector_pinned():
    """Inverse-variance spherical mean of STANDARD_PROBES is pinned."""
    l, b, R = resultant_vector(STANDARD_PROBES)
    assert l == pytest.approx(_DIRECTIONAL_RESULTANT["l_best_deg"], abs=1e-9)
    assert b == pytest.approx(_DIRECTIONAL_RESULTANT["b_best_deg"], abs=1e-9)
    assert R == pytest.approx(_DIRECTIONAL_RESULTANT["R"],          abs=1e-9)


def test_coherence_chi2_pinned():
    """Common-axis χ² and dof are pinned (literature-level anchor)."""
    chi2, dof = coherence_chi2(STANDARD_PROBES)
    assert chi2 == pytest.approx(_DIRECTIONAL_CHI2["chi2"], abs=1e-9)
    assert dof == _DIRECTIONAL_CHI2["dof"]


def test_pairwise_separations_cmb_row_pinned():
    """First row (CMB vs others) of pairwise angular separations."""
    M = pairwise_separations(STANDARD_PROBES)
    assert M.shape == (5, 5)
    # Zero diagonal on the CMB row
    assert M[0, 0] == pytest.approx(0.0, abs=1e-10)
    # Each pairwise entry pinned to 6 decimals
    for i, expected in enumerate(_DIRECTIONAL_PAIRWISE_CMB_ROW):
        assert M[0, i] == pytest.approx(expected, abs=5e-6), (
            f"pairwise_separations[0, {i}] drifted: got {M[0, i]!r}"
        )


def test_isotropy_pvalue_deterministic_with_seed():
    """Seeded RNG → bit-identical p-value across repeated calls."""
    p1 = isotropy_pvalue(
        STANDARD_PROBES, n_mock=5000, rng=np.random.default_rng(42),
    )
    p2 = isotropy_pvalue(
        STANDARD_PROBES, n_mock=5000, rng=np.random.default_rng(42),
    )
    assert p1 == p2, f"isotropy_pvalue non-deterministic: {p1!r} vs {p2!r}"


def test_isotropy_pvalue_pinned_at_canonical_seed():
    """Pinned reference value at (n_mock=5000, seed=42)."""
    p = isotropy_pvalue(
        STANDARD_PROBES, n_mock=5000, rng=np.random.default_rng(42),
    )
    # Measured 2026-04-24: 0.000599880024. At n_mock=5000 the minimum
    # representable p-value with Lidstone smoothing is 1/5001 ≈ 2e-4;
    # the observed value indicates ~2 mock resultants met/exceeded |R|.
    assert p == pytest.approx(0.000599880024, abs=1e-9)


def test_isotropy_pvalue_reflects_strong_clustering():
    """STANDARD_PROBES cluster on the sky → p should be far below 5%.

    Semantic anchor — if some refactor accidentally swaps the Monte-Carlo
    direction (e.g. returns 1 - p instead of p), this catches it.
    """
    p = isotropy_pvalue(
        STANDARD_PROBES, n_mock=5000, rng=np.random.default_rng(42),
    )
    assert p < 0.01, f"p-value {p!r} too large: STANDARD_PROBES are clustered."


# ═══════════════════════════════════════════════════════════════════════
# Part 2 — HJ-02b redshift-binned coherence (canonical 5-probe fixture)
# ═══════════════════════════════════════════════════════════════════════

# Canonical fixture: each probe from STANDARD_PROBES gets a literature
# z_eff that lands it in one of the three DEFAULT_Z_BINS.
#   CF4pp   → z_eff = 0.05   → bin [0, 0.1)
#   Radio   → z_eff = 1.0    → bin [0.1, 10)
#   CatWISE → z_eff = 1.3    → bin [0.1, 10)
#   BiPoSH  → z_eff = 1089.9 → bin [100, 2000) (recombination proxy)
#   CMB     → z_eff = 1100.0 → bin [100, 2000) (Planck z_*)
_Z_BIN_FIXTURE = [
    RedshiftBinnedProbe(
        name="CMB",     l_deg=264.021, b_deg=48.253, sigma_cone_deg=0.5,
        z_eff=1100.0, weight=1.0,
    ),
    RedshiftBinnedProbe(
        name="CatWISE", l_deg=238.2,   b_deg=28.8,   sigma_cone_deg=6.0,
        z_eff=1.3,    weight=1.0,
    ),
    RedshiftBinnedProbe(
        name="Radio",   l_deg=251.0,   b_deg=38.0,   sigma_cone_deg=10.0,
        z_eff=1.0,    weight=1.0,
    ),
    RedshiftBinnedProbe(
        name="CF4pp",   l_deg=289.0,   b_deg=30.0,   sigma_cone_deg=15.0,
        z_eff=0.05,   weight=1.0,
    ),
    RedshiftBinnedProbe(
        name="BiPoSH",  l_deg=220.0,   b_deg=65.0,   sigma_cone_deg=20.0,
        z_eff=1089.9, weight=1.0,
    ),
]


# Measured 2026-04-24; bit-identical across repeats.
_Z_BIN_PER_BIN_PINNED = {
    # (z_min, z_max): (n_probes, resultant_R, l_deg, b_deg)
    (0.0,   0.1):    (1, 1.000000000000, 289.000000, 30.000000),
    (0.1,   10.0):   (2, 0.994139037924, 241.320250, 31.348957),
    (100.0, 2000.0): (2, 0.999924178044, 264.005210, 48.266482),
}
_TOTAL_DRIFT_PINNED    = 64.817439433441
_DRIFT_PVALUE_EXACT    = 0.066666666667   # 8/120 under N!=120 enumeration
_DRIFT_PVALUE_MC_SEED42 = 0.069186162767  # (n_mock=5000, seed=42)


def test_default_z_bins_ssot_frozen():
    """Three-bin default structure is fixed by plan §4.5.3.3."""
    assert DEFAULT_Z_BINS == ((0.0, 0.1), (0.1, 10.0), (100.0, 2000.0))


def test_per_bin_resultants_pinned():
    """Per-bin (l, b, R, n_probes) are pinned against the 5-probe fixture."""
    results = per_bin_resultants(_Z_BIN_FIXTURE)
    assert len(results) == 3
    for r in results:
        key = (r.z_min, r.z_max)
        assert key in _Z_BIN_PER_BIN_PINNED, f"unexpected bin {key}"
        n_exp, R_exp, l_exp, b_exp = _Z_BIN_PER_BIN_PINNED[key]
        assert r.n_probes == n_exp
        assert r.resultant_R == pytest.approx(R_exp, abs=1e-9)
        assert r.l_deg       == pytest.approx(l_exp, abs=1e-6)
        assert r.b_deg       == pytest.approx(b_exp, abs=1e-6)


def test_total_drift_deg_pinned():
    """Total inter-bin drift is pinned."""
    drift = total_drift_deg(per_bin_resultants(_Z_BIN_FIXTURE))
    assert drift == pytest.approx(_TOTAL_DRIFT_PINNED, abs=1e-9)


def test_drift_pvalue_exact_pinned():
    """Exact permutation p-value at N=5 (5!=120 < 10_000 ceiling)."""
    p = drift_pvalue(_Z_BIN_FIXTURE, exact=True)
    assert p == pytest.approx(_DRIFT_PVALUE_EXACT, abs=1e-9)


def test_drift_pvalue_mc_deterministic_with_seed():
    """Seeded MC p-value is bit-identical across repeats."""
    p1 = drift_pvalue(
        _Z_BIN_FIXTURE, n_mock=5000, rng=np.random.default_rng(42),
    )
    p2 = drift_pvalue(
        _Z_BIN_FIXTURE, n_mock=5000, rng=np.random.default_rng(42),
    )
    assert p1 == p2


def test_drift_pvalue_mc_pinned_at_canonical_seed():
    """Pinned MC p-value at (n_mock=5000, seed=42)."""
    p = drift_pvalue(
        _Z_BIN_FIXTURE, n_mock=5000, rng=np.random.default_rng(42),
    )
    assert p == pytest.approx(_DRIFT_PVALUE_MC_SEED42, abs=1e-9)


def test_drift_pvalue_mc_converges_to_exact():
    """At large n_mock the MC estimator should approach the exact value.

    Loose tolerance (±0.015) — the exact ``p = 1/15`` and the
    Lidstone-smoothed MC at n_mock=20_000 should differ by ~σ_MC where
    σ_MC ≈ sqrt(p(1−p)/N) ≈ 1.8e-3. We allow a healthy margin.
    """
    p_exact = drift_pvalue(_Z_BIN_FIXTURE, exact=True)
    p_mc = drift_pvalue(
        _Z_BIN_FIXTURE, n_mock=20_000, rng=np.random.default_rng(2026),
    )
    assert p_mc == pytest.approx(p_exact, abs=0.015)


# ═══════════════════════════════════════════════════════════════════════
# Part 3 — G19 structural guarantees for coherence certificates
# ═══════════════════════════════════════════════════════════════════════

def test_directional_certificate_has_no_posterior_field():
    """The directional MIO certificate must not expose posterior semantics."""
    from mio.coherence.directional import to_mio_certificate

    probes = STANDARD_PROBES
    l, b, R = resultant_vector(probes)
    p_iso = isotropy_pvalue(probes, n_mock=1000, rng=np.random.default_rng(0))
    cert = to_mio_certificate(probes, p_iso, (l, b, R))

    assert cert.reduction_status == "diagnostic-only"
    assert "posterior" not in str(cert.departure_variables).lower()
    assert "posterior" not in str(cert.adequacy_indicators).lower()
    assert "posterior" not in str(cert.consistency_metrics).lower()


def test_redshift_binned_certificate_has_no_posterior_field():
    """The z-binned MIO certificate must not expose posterior semantics."""
    from mio.coherence.redshift_binned import to_mio_certificate

    results = per_bin_resultants(_Z_BIN_FIXTURE)
    drift = total_drift_deg(results)
    p_drift = drift_pvalue(_Z_BIN_FIXTURE, exact=True)
    cert = to_mio_certificate(_Z_BIN_FIXTURE, results, p_drift, drift)

    assert cert.reduction_status == "diagnostic-only"
    for field_dict in (
        cert.departure_variables,
        cert.adequacy_indicators,
        cert.consistency_metrics,
    ):
        assert "posterior" not in str(field_dict).lower()
