from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from astropy.io import fits


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/observed_runs/inspect_planck_mes_irrep_data.py"


def _module():
    spec = importlib.util.spec_from_file_location("planck_irrep_intake", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _small_fits(path: Path) -> None:
    columns = [
        fits.Column(name=name, format="E", array=np.array([1.0, 2.0], dtype=np.float32))
        for name in ("INTENSITY", "Q-POLARISATION", "U-POLARISATION")
    ]
    table = fits.BinTableHDU.from_columns(columns)
    table.header["NSIDE"] = 2048
    table.header["ORDERING"] = "RING"
    table.header["INDXSCHM"] = "IMPLICIT"
    fits.HDUList([fits.PrimaryHDU(), table]).writeto(path)


def _fixture_tree(tmp_path: Path) -> Path:
    workdir = tmp_path / "workdir"
    raw = workdir / "raw"
    planck = raw / "planck_data"
    cmb = raw / "planck_ffp10/smica/cmb_mc"
    noise = raw / "planck_ffp10/smica/noise_mc"
    commander = raw / "planck_ffp10/commander/cmb_mc"
    kids = raw / "hsc_kids/kids"
    npipe = raw / "planck_npipe_pr4"
    for directory in (planck, cmb, noise, commander, kids, npipe):
        directory.mkdir(parents=True)
    for name in (
        "COM_CMB_IQU-smica_2048_R3.00_full.fits",
        "COM_CMB_IQU-commander_2048_R3.00_full.fits",
        "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits",
    ):
        (planck / name).write_bytes(b"fixture")
    for index in range(1000):
        if index != 970:
            path = cmb / f"dx12_v3_smica_cmb_mc_{index:05d}_raw.fits"
            if index == 818:
                _small_fits(path)
            else:
                path.write_bytes(b"fixture")
    for index in range(300):
        (noise / f"dx12_v3_smica_noise_mc_{index:05d}_raw.fits").write_bytes(b"fixture")
    for index in range(3):
        (commander / f"dx12_v3_commander_cmb_mc_{index:05d}_raw.fits").write_bytes(b"fixture")
    for index in range(3, 7):
        (commander / f"dx12_v3_commander_cmb_mc_{index:05d}_raw.fits.partial").write_bytes(b"partial")
    (kids / "KiDS_DR4.1_catalog.fits").write_bytes(b"kids")
    return workdir


def test_exact_inventory_and_metadata(tmp_path: Path) -> None:
    module = _module()
    workdir = _fixture_tree(tmp_path)
    portable = tmp_path / "portable"
    private = tmp_path / "private/intake_manifest.json"
    result = module.inspect_planck_mes_irrep_data(
        workdir=workdir, portable_output=portable, private_output=private,
        verify_selected=True,
    )
    assert result["state"] == "SUCCEEDED"
    summary = json.loads((portable / "intake_summary.json").read_text())
    assert summary["smica_cmb_mc"]["count"] == 999
    assert summary["smica_cmb_mc"]["missing_ids"] == ["00970"]
    assert summary["smica_noise_mc"]["count"] == 300
    assert summary["commander_cmb_mc"]["complete_ids"] == ["00000", "00001", "00002"]
    assert summary["commander_cmb_mc"]["quarantined_partial_ids"] == ["00003", "00004", "00005", "00006"]
    assert summary["planck_npipe_pr4"]["state"] == "BLOCKED_MISSING_DATA"
    assert summary["hsc_kids"]["state"] == "UNAVAILABLE_KIDS_ONLY"
    assert private.is_file()
    assert private.stat().st_mode & 0o777 == 0o600
    selected = json.loads((portable / "selected_input_manifest.json").read_text())
    assert all("checksum_status" in entry and "sidecars" in entry for entry in selected["inputs"])
    assert selected["row_00818"]["decision_basis"] != "SIZE_ONLY"
    assert selected["row_00818"]["sha256"].startswith("sha256:")


def test_00818_semantics_accept_missing_terminal_padding_but_not_payload(tmp_path: Path) -> None:
    module = _module()
    valid = tmp_path / "valid.fits"
    _small_fits(valid)
    valid.write_bytes(valid.read_bytes()[:-17])
    accepted = module.adjudicate_00818(valid)
    assert accepted["state"] == "ADMITTED_SEMANTICALLY"
    assert accepted["terminal_padding_shortfall_bytes"] == 17
    invalid = tmp_path / "invalid.fits"
    _small_fits(invalid)
    invalid.write_bytes(invalid.read_bytes()[:-2870])
    with pytest.raises(module.IntakeBlocked, match="payload"):
        module.adjudicate_00818(invalid)


def test_partial_commander_is_quarantined_before_fits_open(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = _module()
    workdir = _fixture_tree(tmp_path)
    opened: list[Path] = []
    original = module.adjudicate_00818
    def record(path: Path):
        opened.append(path)
        return original(path)
    monkeypatch.setattr(module, "adjudicate_00818", record)
    module.inspect_planck_mes_irrep_data(
        workdir=workdir, portable_output=tmp_path / "portable",
        private_output=tmp_path / "private.json", verify_selected=True,
    )
    assert [path.name for path in opened] == ["dx12_v3_smica_cmb_mc_00818_raw.fits"]


def test_symlink_escape_and_mutation_are_refused(tmp_path: Path) -> None:
    module = _module()
    workdir = _fixture_tree(tmp_path)
    target = workdir / "raw/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits"
    target.unlink()
    target.symlink_to(tmp_path / "outside.fits")
    (tmp_path / "outside.fits").write_bytes(b"outside")
    with pytest.raises(module.IntakeBlocked, match="escape"):
        module.inspect_planck_mes_irrep_data(
            workdir=workdir, portable_output=tmp_path / "portable",
            private_output=tmp_path / "private.json", verify_selected=True,
        )


def test_raw_stat_identity_is_unchanged_and_private_not_portable(tmp_path: Path) -> None:
    module = _module()
    workdir = _fixture_tree(tmp_path)
    row = workdir / "raw/planck_ffp10/smica/cmb_mc/dx12_v3_smica_cmb_mc_00818_raw.fits"
    before = module.stat_identity(row)
    portable = tmp_path / "portable"
    private = tmp_path / "private/intake_manifest.json"
    module.inspect_planck_mes_irrep_data(
        workdir=workdir, portable_output=portable, private_output=private,
        verify_selected=True,
    )
    assert module.stat_identity(row) == before
    assert private.resolve() not in [path.resolve() for path in portable.rglob("*")]
    terminal = json.loads((portable / "terminal.json").read_text())
    assert terminal["raw_data_mutation"] is False
    assert terminal["real_host_execution"] is True
