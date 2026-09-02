"""RED/GREEN contracts for independently downloaded Task-7C verifiers."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "scripts" / "research" / "run_wu011_task7c_external_verifiers.py"


def _api():
    if not MODULE.is_file():
        pytest.fail(f"external verifier module is absent: {MODULE}", pytrace=False)
    spec = importlib.util.spec_from_file_location("wu011_external_verifiers", MODULE)
    if spec is None or spec.loader is None:
        pytest.fail("external verifier module cannot be loaded", pytrace=False)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_registered_package_contract_and_hashes() -> None:
    api = _api()
    contract = api.package_contract()
    assert contract["pywigxjpf"] == "1.13.3"
    assert contract["python-flint"] == "0.9.0"
    assert contract["ducc0"] == "0.41.0"
    assert contract["mpmath"] == "1.4.1"
    assert contract["sympy"] == "1.14.0"
    assert contract["scipy"] == "1.18.1"
    assert contract["numpy"] == "2.5.2"
    assert (
        api.PYWIGXJPF_SDIST_SHA256
        == "30122c9ab2775aa8a0531d01956892627f1c6e82ba65c3abf6b8fc4fb75c3aef"
    )


def test_three_way_wigner_crosscheck() -> None:
    api = _api()
    result = api.validate_wigner_symbols()
    assert result["status"] == "PASS"
    assert result["case_count"] >= 100
    assert result["maximum_absolute_residual"] <= 5.0e-14


def test_sympy_exact_z_direction_L12_has_real_rank_32() -> None:
    api = _api()
    result = api.sympy_exact_z_block_certificate(source_cutoff=12)
    assert result["status"] == "PASS"
    assert result["complex_block_ranks"] == [4, 4, 4, 3, 2, 1]
    assert result["real_stored_rank"] == 32
    assert all(item["determinant_nonzero"] for item in result["pivot_minors"])


def test_arb_balls_exclude_zero_for_every_pivot_minor() -> None:
    api = _api()
    exact = api.sympy_exact_z_block_certificate(source_cutoff=12)
    result = api.arb_pivot_minor_certificate(exact)
    assert result["status"] == "PASS"
    assert result["minor_count"] == 6
    assert all(not item["contains_zero"] for item in result["minors"])


def test_ducc_quadrature_reproduces_wolfram_z_spectrum() -> None:
    api = _api()
    result = api.ducc_z_quadrature_certificate(source_cutoff=12)
    assert result["status"] == "PASS"
    assert result["real_stored_rank"] == 32
    assert result["relative_smallest_singular_residual"] <= 2.0e-7
    assert result["normal_matrix_relative_residual"] <= 2.0e-11


def test_artifact_writer_round_trip(tmp_path: Path) -> None:
    api = _api()
    result = api.write_external_verifier_artifacts(tmp_path)
    assert result["status"] == "PASS_EXTERNAL_VERIFIER_AXES"
    manifest = tmp_path / "SHA256SUMS"
    assert manifest.is_file()
    summary = json.loads((tmp_path / "external_verifier_summary.json").read_text())
    assert summary["claim_promotion"] is False
    assert summary["scientific_terminal_authorized"] is False
    assert summary["z_direction_continuum_full_row_rank"] is True
