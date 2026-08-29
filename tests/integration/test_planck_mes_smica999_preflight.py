from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest
from astropy.io import fits

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/observed_runs/preflight_planck_mes_smica999.py"
SPEC = importlib.util.spec_from_file_location("smica999_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)

def write_minimal_fits(path: Path, *, valid: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not valid:
        path.write_bytes(b"not a FITS file")
        return
    columns = [
        fits.Column(name=name, format="E", array=np.array([1.0, 2.0], dtype=np.float32))
        for name in ("INTENSITY", "Q-POLARISATION", "U-POLARISATION")
    ]
    table = fits.BinTableHDU.from_columns(columns)
    table.header["NSIDE"] = 2048
    table.header["ORDERING"] = "RING"
    table.header["INDXSCHM"] = "IMPLICIT"
    fits.HDUList([fits.PrimaryHDU(), table]).writeto(path)


@pytest.fixture
def small_inventory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    workdir = tmp_path / "workdir"
    ffp10 = workdir / "raw/planck_ffp10"
    cmb_dir = ffp10 / "smica/cmb_mc"
    noise_dir = ffp10 / "smica/noise_mc"
    planck_data = workdir / "raw/planck_data"
    analysis = workdir / "analysis/planck_mes_irrep/smica999"
    output = tmp_path / "repo-output"
    analysis.mkdir(parents=True)
    cmb_dir.mkdir(parents=True)
    noise_dir.mkdir(parents=True)
    planck_data.mkdir(parents=True)
    monkeypatch.setattr(module, "EXPECTED_CMB_IDS", ("00000", "00818", "00999"))
    monkeypatch.setattr(module, "EXPECTED_NOISE_IDS", ("00000", "00001"))
    for row_id in module.EXPECTED_CMB_IDS:
        write_minimal_fits(cmb_dir / f"dx12_v3_smica_cmb_mc_{row_id}_raw.fits")
    for row_id in module.EXPECTED_NOISE_IDS:
        write_minimal_fits(noise_dir / f"dx12_v3_smica_noise_mc_{row_id}_raw.fits")
    write_minimal_fits(planck_data / module.OBSERVED_NAME)
    write_minimal_fits(planck_data / module.MASK_NAME)
    return {
        "workdir": workdir,
        "ffp10": cmb_dir,
        "output": output,
        "private": analysis / "preflight_manifest.json",
    }


def test_full_contract_constants_are_exact() -> None:
    assert len(module.EXPECTED_CMB_IDS) == 999
    assert module.EXPECTED_CMB_IDS[0] == "00000"
    assert module.EXPECTED_CMB_IDS[-1] == "00999"
    assert "00970" not in module.EXPECTED_CMB_IDS
    assert "00818" in module.EXPECTED_CMB_IDS
    assert len(module.EXPECTED_NOISE_IDS) == 300


def test_canonical_nested_smica_layout_is_admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    workdir = tmp_path / "workdir"
    ffp10 = workdir / "raw/planck_ffp10"
    cmb_dir = ffp10 / "smica/cmb_mc"
    noise_dir = ffp10 / "smica/noise_mc"
    planck_data = workdir / "raw/planck_data"
    private = workdir / "analysis/planck_mes_irrep/smica999/preflight_manifest.json"
    output = tmp_path / "repo-output"
    cmb_dir.mkdir(parents=True)
    noise_dir.mkdir(parents=True)
    planck_data.mkdir(parents=True)
    private.parent.mkdir(parents=True)
    monkeypatch.setattr(module, "EXPECTED_CMB_IDS", ("00000", "00818", "00999"))
    monkeypatch.setattr(module, "EXPECTED_NOISE_IDS", ("00000", "00001"))
    for row_id in module.EXPECTED_CMB_IDS:
        write_minimal_fits(cmb_dir / f"dx12_v3_smica_cmb_mc_{row_id}_raw.fits")
    for row_id in module.EXPECTED_NOISE_IDS:
        write_minimal_fits(noise_dir / f"dx12_v3_smica_noise_mc_{row_id}_raw.fits")
    write_minimal_fits(planck_data / module.OBSERVED_NAME)
    write_minimal_fits(planck_data / module.MASK_NAME)

    result = module.build_preflight(
        workdir=workdir,
        output_dir=output,
        private_output=private,
        execute=False,
    )

    assert result["summary"]["cmb_complete_count"] == 3
    assert result["summary"]["noise_available_count"] == 2
    assert result["selected_input_manifest"]["noise_files_selected"] == 0


def test_exact_inventory_preflight_executes_without_scientific_rank(small_inventory) -> None:
    result = module.build_preflight(
        workdir=small_inventory["workdir"],
        output_dir=small_inventory["output"],
        private_output=small_inventory["private"],
        execute=True,
    )
    summary = result["summary"]
    assert summary["state"] == "PREFLIGHT_SUCCEEDED"
    assert summary["cmb_complete_count"] == 3
    assert summary["noise_available_count"] == 2
    assert summary["noise_selected_count"] == 0
    assert summary["scientific_rank_generated"] is False
    assert summary["wu007_scientific_execution_started"] is False
    assert result["route_receipt"]["downloads_performed"] == 0
    assert result["route_receipt"]["full_raw_tree_hash_performed"] is False
    assert result["route_receipt"]["row_00818"]["status"] == "ADMITTED_BY_FITS_STRUCTURE_AND_STREAMING_SHA256"
    terminal = json.loads((small_inventory["output"] / "preflight_terminal.json").read_text())
    assert terminal["state"] == "PRECONDITION_SUCCEEDED"
    assert terminal["scientific_execution_state"] == "NOT_STARTED"
    assert small_inventory["private"].is_file()


def test_dry_run_writes_nothing(small_inventory) -> None:
    module.build_preflight(
        workdir=small_inventory["workdir"],
        output_dir=small_inventory["output"],
        private_output=small_inventory["private"],
        execute=False,
    )
    assert not small_inventory["output"].exists()
    assert not small_inventory["private"].exists()


def test_missing_or_extra_inventory_fails_closed(small_inventory) -> None:
    (small_inventory["ffp10"] / "dx12_v3_smica_cmb_mc_00999_raw.fits").unlink()
    with pytest.raises(module.PreflightError, match="inventory mismatch"):
        module.build_preflight(
            workdir=small_inventory["workdir"], output_dir=small_inventory["output"],
            private_output=small_inventory["private"], execute=False,
        )


def test_00970_or_partial_file_is_rejected(small_inventory) -> None:
    write_minimal_fits(small_inventory["ffp10"] / "dx12_v3_smica_cmb_mc_00970_raw.fits")
    with pytest.raises(module.PreflightError, match="inventory mismatch"):
        module.build_preflight(
            workdir=small_inventory["workdir"], output_dir=small_inventory["output"],
            private_output=small_inventory["private"], execute=False,
        )
    (small_inventory["ffp10"] / "dx12_v3_smica_cmb_mc_00970_raw.fits").unlink()
    (small_inventory["ffp10"] / "interrupted.fits.partial").write_bytes(b"x")
    with pytest.raises(module.PreflightError, match="partial"):
        module.build_preflight(
            workdir=small_inventory["workdir"], output_dir=small_inventory["output"],
            private_output=small_inventory["private"], execute=False,
        )


def test_00818_requires_semantic_fits_structure(small_inventory) -> None:
    write_minimal_fits(
        small_inventory["ffp10"] / "dx12_v3_smica_cmb_mc_00818_raw.fits", valid=False,
    )
    with pytest.raises(module.PreflightError, match="FITS"):
        module.build_preflight(
            workdir=small_inventory["workdir"], output_dir=small_inventory["output"],
            private_output=small_inventory["private"], execute=False,
        )


def test_00818_accepts_missing_terminal_padding_when_payload_is_complete(
    small_inventory,
) -> None:
    path = small_inventory["ffp10"] / "dx12_v3_smica_cmb_mc_00818_raw.fits"
    path.write_bytes(path.read_bytes()[:-17])

    result = module.build_preflight(
        workdir=small_inventory["workdir"],
        output_dir=small_inventory["output"],
        private_output=small_inventory["private"],
        execute=False,
    )

    semantic = result["route_receipt"]["row_00818"]["fits"]
    assert semantic["state"] == "ADMITTED_SEMANTICALLY"
    assert semantic["terminal_padding_shortfall_bytes"] == 17


def test_symlink_escape_and_raw_output_are_rejected(small_inventory, tmp_path: Path) -> None:
    outside = tmp_path / "outside.fits"
    write_minimal_fits(outside)
    target = small_inventory["ffp10"] / "dx12_v3_smica_cmb_mc_00000_raw.fits"
    target.unlink()
    target.symlink_to(outside)
    with pytest.raises(module.PreflightError, match="escape"):
        module.build_preflight(
            workdir=small_inventory["workdir"], output_dir=small_inventory["output"],
            private_output=small_inventory["private"], execute=False,
        )
    target.unlink()
    write_minimal_fits(target)
    raw_output = small_inventory["workdir"] / "raw/generated"
    with pytest.raises(module.PreflightError, match="inside raw"):
        module.build_preflight(
            workdir=small_inventory["workdir"], output_dir=raw_output,
            private_output=small_inventory["private"], execute=False,
        )


def test_noise_files_are_available_but_never_selected(small_inventory) -> None:
    result = module.build_preflight(
        workdir=small_inventory["workdir"], output_dir=small_inventory["output"],
        private_output=small_inventory["private"], execute=False,
    )
    selected = result["selected_input_manifest"]
    assert selected["noise_files_available_but_not_routed"] == 2
    assert selected["noise_files_selected"] == 0
    assert all("noise_mc" not in Path(row["path"]).name for row in selected["null_rows"])
