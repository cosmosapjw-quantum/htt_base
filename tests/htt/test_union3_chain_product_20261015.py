"""Small deterministic fixtures for Union3 public-chain compression audit."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "audit_union3_chain_product_20261015.py"
spec = importlib.util.spec_from_file_location("union_audit_20261015", SCRIPT)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_known_gaussian_chain_and_fits_compression():
    rng = np.random.default_rng(20261015)
    draws = rng.normal(size=(900, 3)) @ np.array([[1.0, 0.1, 0.0],
                                                    [0.2, 0.7, -0.1],
                                                    [0.0, 0.3, 1.4]]) + np.array([32., 36., 40.])
    table = np.zeros((4, 4))
    table[0, 1:] = [0.01, 0.1, 1.0]
    table[1:, 0] = np.median(draws, axis=0)
    table[1:, 1:] = np.linalg.inv(np.cov(draws, rowvar=False))
    result = mod.audit_table(draws, table)
    assert result["precision_numerical_match"]
    assert result["raw_location_numerical_match"]
    assert result["full_direct_summary_numerical_match"]
    assert result["n_nodes"] == 3
    assert result["raw_median_max_abs_difference_mag"] < 1e-12
    assert result["precision_relative_frobenius_difference"] < 1e-12


def test_tampered_fits_does_not_claim_identity():
    rng = np.random.default_rng(123)
    draws = rng.normal(size=(140, 2))
    table = np.zeros((3, 3))
    table[0, 1:] = [0.01, 0.2]
    table[1:, 0] = np.median(draws, axis=0)
    table[1:, 1:] = np.linalg.inv(np.cov(draws, rowvar=False))
    table[1, 1] *= 1.1
    assert not mod.audit_table(draws, table)["precision_numerical_match"]


def test_nonfinite_and_singular_sources_rejected():
    with pytest.raises(mod.ProductAuditError, match="nonfinite"):
        mod.chain_moments(np.array([[1., 2.], [2., np.nan], [3., 4.]]))
    with pytest.raises(mod.ProductAuditError, match="singular"):
        mod.chain_moments(np.column_stack([np.arange(7.), 2*np.arange(7.)]))


def test_invalid_redshift_and_tolerance_rejected():
    rng = np.random.default_rng(1)
    draws = rng.normal(size=(100, 2))
    table = np.zeros((3, 3))
    table[0, 1:] = [0.2, 0.1]
    table[1:, 0] = np.median(draws, axis=0)
    table[1:, 1:] = np.linalg.inv(np.cov(draws, rowvar=False))
    with pytest.raises(mod.ProductAuditError, match="redshift"):
        mod.audit_table(draws, table)
    with pytest.raises(mod.ProductAuditError, match="negative tolerance"):
        mod.audit_table(draws, table, median_tolerance_mag=-1.)


def test_reference_shift_is_diagnostic_not_exact_generator_attribution():
    rng = np.random.default_rng(77)
    draws = rng.normal(size=(300, 2))
    z = np.array([0.05, 0.9])
    table = np.zeros((3, 3))
    table[0, 1:] = z
    table[1:, 0] = np.median(draws, axis=0) + mod.flat_lcdm_reference_modulus(z)
    table[1:, 1:] = np.linalg.inv(np.cov(draws, rowvar=False))
    result = mod.audit_table(draws, table)
    assert result["precision_numerical_match"]
    assert not result["raw_location_numerical_match"]
    assert result["reference_candidate"]["fiducial_shift_max_abs_residual_mag"] < 1e-12
    assert result["reference_candidate"]["exact_coordinate_conversion"] == "UNVERIFIED"
