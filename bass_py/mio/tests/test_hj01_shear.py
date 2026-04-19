"""MIO-HJ-01 (W10D3-4) — non-parametric shear extraction skeleton tests.

Plan §21 / Week 10 Days 3-4 gate: ≥10 new tests; MIO contribution
37 → ≥47. No bass_py runtime dependency — all K_ℓ atlases here are
synthetic dicts that satisfy ``KL_ATLAS_REQUIRED_KEYS``.

Test groups
-----------
1. Schema validator (5 tests):
   - test_validate_kl_atlas_schema_accepts_valid_dict
   - test_validate_kl_atlas_schema_rejects_missing_keys
   - test_validate_kl_atlas_schema_rejects_shape_mismatch
   - test_validate_kl_atlas_schema_rejects_nonpositive_sigma
   - test_validate_kl_atlas_schema_rejects_nonfinite_arrays

2. Core extraction (5 tests):
   - test_extract_flrw_null_consistent_with_zero
   - test_extract_bianchi_injection_recovers_value
   - test_ell_independence_passes_for_homogeneous_shear
   - test_ell_independence_fails_for_ell_dependent_residual
   - test_extract_drops_zero_kernel_multipoles

3. AtlasEntry adapter (1 test):
   - test_extract_from_atlas_entry_matches_dict_path

4. Certificate packaging (3 tests):
   - test_to_mio_certificate_marks_diagnostic_only_until_v_gate
   - test_to_mio_certificate_has_no_posterior_field (G19)
   - test_to_mio_certificate_flrw_band_indicator

5. Misc (2 tests):
   - test_required_keys_constant_is_documented
   - test_artefact_emitter_writes_mio_prefixed_json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from mio.extraction import (
    ARTEFACT_FILENAME,
    DIAGNOSTIC_ONLY_CAVEAT,
    KL_ATLAS_REQUIRED_KEYS,
    ShearExtractor,
    ShearExtractorConfig,
    ShearExtractorReport,
    emit_shear_extraction_artefact,
    extract_from_atlas_entry,
    extract_from_kl_atlas,
    to_mio_certificate,
    validate_kl_atlas_schema,
)
from workspace.contracts.atlas_entry import AtlasEntry
from workspace.contracts.mio_certificate import MioCertificate


# ---------------------------------------------------------------------------
# Synthetic K_ell atlas builders
# ---------------------------------------------------------------------------


def _base_kl(
    *,
    ell_min: int = 2,
    ell_max: int = 30,
    bianchi_type: str = "FLRW",
    atlas_name: str = "test_kl_atlas_v1",
    rng_seed: int = 20260419,
    sigma2_inject: float = 0.0,
    sigma_obs_uK2: float = 50.0,
    add_obs_noise: bool = True,
):
    """Build a synthetic K_ℓ atlas dict.

    The construction deliberately uses very simple shapes; this is a
    skeleton suite, not a physics test. The numbers are arbitrary but
    self-consistent: the extractor recovers the injected Σ² up to
    Gaussian shot noise with σ_obs.
    """
    rng = np.random.default_rng(seed=rng_seed)
    ell = np.arange(ell_min, ell_max + 1, dtype=float)
    # K_ell modelled as a smooth O(1) function with ℓ — deliberately
    # non-trivial so divisor pathologies show up if any.
    k_ell = 1.0 + 0.05 * np.sin(0.3 * ell) + 0.01 * (ell - ell_min)
    # Mock ΛCDM prediction.
    c_lcdm = 1000.0 + 200.0 * np.exp(-0.1 * (ell - ell_min))
    # Inject a homogeneous Σ² departure.
    c_obs_clean = c_lcdm + sigma2_inject * k_ell
    if add_obs_noise:
        noise = rng.normal(loc=0.0, scale=sigma_obs_uK2, size=ell.size)
        c_obs = c_obs_clean + noise
    else:
        c_obs = c_obs_clean
    sig_c = np.full(ell.size, sigma_obs_uK2, dtype=float)

    return {
        "ell": ell.astype(int),
        "C_ell_obs": c_obs,
        "C_ell_lcdm": c_lcdm,
        "K_ell": k_ell,
        "sigma_C_ell": sig_c,
        "bianchi_type": bianchi_type,
        "atlas_name": atlas_name,
        "generated_by": "test_hj01_shear synthetic",
        "git_commit": "synthetic",
        "config_hash": "synthetic",
        "domain_caveats": ["synthetic-K_ell-no-bass_py"],
    }


# ---------------------------------------------------------------------------
# 1. Schema validator
# ---------------------------------------------------------------------------


def test_validate_kl_atlas_schema_accepts_valid_dict():
    kl = _base_kl()
    # Must not raise.
    validate_kl_atlas_schema(kl)


def test_validate_kl_atlas_schema_rejects_missing_keys():
    kl = _base_kl()
    del kl["K_ell"]
    with pytest.raises(KeyError, match="K_ell"):
        validate_kl_atlas_schema(kl)


def test_validate_kl_atlas_schema_rejects_shape_mismatch():
    kl = _base_kl()
    kl["sigma_C_ell"] = np.ones(kl["ell"].size + 3)
    with pytest.raises(ValueError, match="length"):
        validate_kl_atlas_schema(kl)


def test_validate_kl_atlas_schema_rejects_nonpositive_sigma():
    kl = _base_kl()
    kl["sigma_C_ell"][5] = 0.0
    with pytest.raises(ValueError, match="sigma_C_ell"):
        validate_kl_atlas_schema(kl)


def test_validate_kl_atlas_schema_rejects_nonfinite_arrays():
    kl = _base_kl()
    kl["C_ell_obs"][3] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        validate_kl_atlas_schema(kl)


# ---------------------------------------------------------------------------
# 2. Core extraction
# ---------------------------------------------------------------------------


def test_extract_flrw_null_consistent_with_zero():
    """Pure FLRW input (sigma2_inject=0) should give Σ²_best within 2σ of 0."""
    kl = _base_kl(sigma2_inject=0.0, sigma_obs_uK2=50.0, rng_seed=1)
    report = extract_from_kl_atlas(kl)
    z = abs(report.sigma2_best) / report.sigma2_best_uncertainty
    assert z < 2.0, f"FLRW null falsely flagged: |z|={z:.3f}"
    # Independence χ² should be statistically reasonable (p > 0.01).
    assert report.p_value_independence > 0.01, (
        f"FLRW null χ² test rejected at p={report.p_value_independence:.4f}"
    )


def test_extract_bianchi_injection_recovers_value():
    """Inject a homogeneous Σ²; recover it within ~3σ of the per-ℓ scatter."""
    inject = 200.0  # μK² per K_ℓ unit — large enough to dominate noise.
    kl = _base_kl(sigma2_inject=inject, sigma_obs_uK2=50.0,
                  bianchi_type="I", rng_seed=2)
    report = extract_from_kl_atlas(kl)
    z = (report.sigma2_best - inject) / report.sigma2_best_uncertainty
    assert abs(z) < 3.0, (
        f"recovered Σ²_best={report.sigma2_best:.3f} ± "
        f"{report.sigma2_best_uncertainty:.3f}; injected {inject}; |z|={abs(z):.3f}"
    )


def test_ell_independence_passes_for_homogeneous_shear():
    """Homogeneous shear → χ² should not reject (p > 0.05) on average."""
    rng = np.random.default_rng(seed=20260419)
    p_values = []
    for trial in range(10):
        kl = _base_kl(sigma2_inject=300.0, sigma_obs_uK2=40.0,
                      rng_seed=int(rng.integers(1, 1_000_000)))
        report = extract_from_kl_atlas(kl)
        p_values.append(report.p_value_independence)
    # At least 7/10 should pass at p > 0.05 (loose Bonferroni).
    n_pass = sum(p > 0.05 for p in p_values)
    assert n_pass >= 7, (
        f"only {n_pass}/10 trials passed ℓ-independence; p_values={p_values}"
    )


def test_ell_independence_fails_for_ell_dependent_residual():
    """Inject an ℓ-dependent residual; χ² test should flag with p < 0.05."""
    kl = _base_kl(sigma2_inject=0.0, sigma_obs_uK2=10.0, rng_seed=3,
                  add_obs_noise=False)
    # Add a slope: Δ C_ell = 30 × (ℓ - ℓ_min); this manifests as Σ² growing
    # roughly linearly with ℓ once divided by K_ℓ ≈ 1.
    ell = kl["ell"].astype(float)
    kl["C_ell_obs"] = kl["C_ell_obs"] + 30.0 * (ell - ell.min())
    report = extract_from_kl_atlas(kl)
    assert report.p_value_independence < 0.05, (
        f"ℓ-dependent residual not flagged: p={report.p_value_independence:.4f}; "
        f"χ²={report.chi2_independence:.2f} dof={report.dof_independence}"
    )


def test_extract_drops_zero_kernel_multipoles():
    """A multipole with K_ℓ = 0 must be dropped (divide-by-zero guard)."""
    kl = _base_kl(sigma2_inject=100.0, sigma_obs_uK2=20.0, rng_seed=4)
    # Force K_ell to vanish at ℓ = 5 and ℓ = 17.
    kl["K_ell"][3] = 0.0   # ell = 5
    kl["K_ell"][15] = 0.0  # ell = 17
    report = extract_from_kl_atlas(kl)
    assert 5 in report.dropped_ells
    assert 17 in report.dropped_ells
    assert 5 not in report.ell.tolist()
    assert 17 not in report.ell.tolist()
    # Remaining ells should still recover the injection.
    assert report.ell.size == 27  # 29 in window minus 2 dropped


# ---------------------------------------------------------------------------
# 3. AtlasEntry adapter
# ---------------------------------------------------------------------------


def test_extract_from_atlas_entry_matches_dict_path():
    """The AtlasEntry adapter must give identical results to the dict path."""
    kl = _base_kl(sigma2_inject=150.0, sigma_obs_uK2=30.0, rng_seed=5)
    entry = AtlasEntry(
        atlas_name=kl["atlas_name"],
        bianchi_type=kl["bianchi_type"],
        parameter_point={"Sigma2": 0.0, "beta": 0.0},
        ell=np.asarray(kl["ell"]),
        kernel_values=np.asarray(kl["K_ell"]),
        kernel_name="K_ell",
        generated_by=kl["generated_by"],
        git_commit=kl["git_commit"],
        config_hash=kl["config_hash"],
        entry_hash="abc123",
    )
    report_entry = extract_from_atlas_entry(
        entry,
        c_ell_obs=kl["C_ell_obs"],
        c_ell_lcdm=kl["C_ell_lcdm"],
        sigma_c_ell=kl["sigma_C_ell"],
    )
    report_dict = extract_from_kl_atlas(kl)
    assert report_entry.sigma2_best == pytest.approx(report_dict.sigma2_best)
    assert report_entry.chi2_independence == pytest.approx(report_dict.chi2_independence)
    assert report_entry.ell.tolist() == report_dict.ell.tolist()


def test_extract_from_atlas_entry_rejects_wrong_kernel_name():
    kl = _base_kl()
    entry = AtlasEntry(
        atlas_name=kl["atlas_name"],
        bianchi_type=kl["bianchi_type"],
        parameter_point={"Sigma2": 0.0},
        ell=np.asarray(kl["ell"]),
        kernel_values=np.asarray(kl["K_ell"]),
        kernel_name="Sobolev_A1",  # WRONG
        generated_by="x",
        git_commit="x",
        config_hash="x",
        entry_hash="x",
    )
    with pytest.raises(ValueError, match="K_ell"):
        extract_from_atlas_entry(
            entry,
            c_ell_obs=kl["C_ell_obs"],
            c_ell_lcdm=kl["C_ell_lcdm"],
            sigma_c_ell=kl["sigma_C_ell"],
        )


# ---------------------------------------------------------------------------
# 4. Certificate packaging
# ---------------------------------------------------------------------------


def test_to_mio_certificate_marks_diagnostic_only_until_v_gate():
    kl = _base_kl(sigma2_inject=0.0, sigma_obs_uK2=20.0, rng_seed=6)
    report = extract_from_kl_atlas(kl)
    cert = to_mio_certificate(report)
    assert isinstance(cert, MioCertificate)
    assert cert.reduction_status == "diagnostic-only"
    assert DIAGNOSTIC_ONLY_CAVEAT in cert.domain_caveats
    assert cert.report_type == "shear_extraction"
    assert cert.channel == "TT_low_ell"


def test_to_mio_certificate_has_no_posterior_field():
    """G19 hard separation — no field name may contain 'posterior'."""
    kl = _base_kl()
    report = extract_from_kl_atlas(kl)
    cert = to_mio_certificate(report)
    serialised = json.dumps({
        "departure_variables": cert.departure_variables,
        "adequacy_indicators": cert.adequacy_indicators,
        "consistency_metrics": cert.consistency_metrics,
        "domain_caveats": cert.domain_caveats,
    })
    assert "posterior" not in serialised.lower()
    with pytest.raises(NotImplementedError):
        cert.as_posterior_bundle()


def test_to_mio_certificate_flrw_band_indicator():
    """flrw_consistent_within_band indicator behaves correctly on each side.

    Uses noiseless inputs so the assertion is deterministic. With 29
    iid 2σ tests the false-flag rate on a random FLRW realisation is
    ~75% — that is a property of the band, not a property of the code,
    so it is not what this test is for.
    """
    # FLRW input (noiseless) → band consistent.
    kl_flrw = _base_kl(sigma2_inject=0.0, sigma_obs_uK2=50.0, rng_seed=7,
                       add_obs_noise=False)
    cert_flrw = to_mio_certificate(extract_from_kl_atlas(kl_flrw))
    assert cert_flrw.adequacy_indicators["flrw_consistent_within_band"] is True

    # Strong injection → band fails (1000 μK² Σ² >> 10 μK² obs noise floor).
    kl_strong = _base_kl(sigma2_inject=1000.0, sigma_obs_uK2=10.0,
                         rng_seed=8, add_obs_noise=False)
    cert_strong = to_mio_certificate(extract_from_kl_atlas(kl_strong))
    assert cert_strong.adequacy_indicators["flrw_consistent_within_band"] is False


# ---------------------------------------------------------------------------
# 5. Misc
# ---------------------------------------------------------------------------


def test_required_keys_constant_matches_validator():
    """KL_ATLAS_REQUIRED_KEYS must list every key actually checked by the
    validator. This guards against silent schema drift between docs and code."""
    expected = {
        "ell", "C_ell_obs", "C_ell_lcdm", "K_ell", "sigma_C_ell",
        "bianchi_type", "atlas_name", "generated_by", "git_commit", "config_hash",
    }
    assert set(KL_ATLAS_REQUIRED_KEYS) == expected


def test_artefact_emitter_writes_mio_prefixed_json(tmp_path: Path):
    kl = _base_kl(sigma2_inject=100.0, sigma_obs_uK2=25.0, rng_seed=9)
    out = tmp_path / ARTEFACT_FILENAME
    payload = emit_shear_extraction_artefact(out, kl)
    assert out.exists()
    assert out.name.startswith("mio_")
    loaded = json.loads(out.read_text())
    assert loaded["schema_version"] == "v1"
    assert loaded["bianchi_type"] == kl["bianchi_type"]
    assert loaded["atlas_name"] == kl["atlas_name"]
    assert "summary" in loaded and "sigma2_best" in loaded["summary"]
    assert payload["certificate"]["reduction_status"] == "diagnostic-only"


def test_artefact_emitter_rejects_non_mio_filename(tmp_path: Path):
    kl = _base_kl()
    bad_out = tmp_path / "result_v1.json"  # missing 'mio_' prefix
    with pytest.raises(ValueError, match="REG-02"):
        emit_shear_extraction_artefact(bad_out, kl)


def test_shear_extractor_class_extract_and_certify():
    cfg = ShearExtractorConfig(ell_min=3, ell_max=20, flrw_null_band_sigma=2.5)
    extractor = ShearExtractor(config=cfg)
    kl = _base_kl(sigma2_inject=0.0, sigma_obs_uK2=20.0, rng_seed=10)
    report = extractor.extract(kl)
    assert isinstance(report, ShearExtractorReport)
    # Window restriction should chop ℓ=2 and ℓ=21..30.
    assert report.ell.min() >= 3
    assert report.ell.max() <= 20
    cert = extractor.certify(kl)
    # ell_min/max in the certificate consistency_metrics should match cfg.
    assert cert.consistency_metrics["ell_min"] == 3.0
    assert cert.consistency_metrics["ell_max"] == 20.0
    assert cert.consistency_metrics["flrw_null_band_sigma"] == 2.5
