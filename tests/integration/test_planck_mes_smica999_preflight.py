from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/observed_runs/preflight_planck_mes_smica999.py"
SPEC = importlib.util.spec_from_file_location("smica999_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def card(keyword: str, value: str | None = None) -> bytes:
    text = keyword if value is None else f"{keyword:<8}= {value}"
    return text.ljust(80).encode("ascii")


def header(cards: list[bytes]) -> bytes:
    payload = b"".join(cards + [card("END")])
    return payload.ljust(((len(payload) + 2879) // 2880) * 2880, b" ")


def write_minimal_fits(path: Path, *, valid: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not valid:
        path.write_bytes(b"not a FITS file")
        return
    primary = header([
        card("SIMPLE", "T"), card("BITPIX", "8"), card("NAXIS", "0"), card("EXTEND", "T"),
    ])
    table = header([
        card("XTENSION", "'BINTABLE'"), card("BITPIX", "8"), card("NAXIS", "2"),
        card("NAXIS1", "4"), card("NAXIS2", "2"), card("PCOUNT", "0"),
        card("GCOUNT", "1"), card("TFIELDS", "0"),
    ])
    data = b"\x00\x00\x00\x01\x00\x00\x00\x02".ljust(2880, b"\0")
    path.write_bytes(primary + table + data)


@pytest.fixture
def small_inventory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    workdir = tmp_path / "workdir"
    ffp10 = workdir / "raw/planck_ffp10"
    planck_data = workdir / "raw/planck_data"
    analysis = workdir / "analysis/planck_mes_irrep/smica999"
    output = tmp_path / "repo-output"
    analysis.mkdir(parents=True)
    ffp10.mkdir(parents=True)
    planck_data.mkdir(parents=True)
    monkeypatch.setattr(module, "EXPECTED_CMB_IDS", ("00000", "00818", "00999"))
    monkeypatch.setattr(module, "EXPECTED_NOISE_IDS", ("00000", "00001"))
    for row_id in module.EXPECTED_CMB_IDS:
        write_minimal_fits(ffp10 / f"dx12_v3_smica_cmb_mc_{row_id}_raw.fits")
    for row_id in module.EXPECTED_NOISE_IDS:
        write_minimal_fits(ffp10 / f"dx12_v3_smica_noise_mc_{row_id}_raw.fits")
    write_minimal_fits(planck_data / module.OBSERVED_NAME)
    write_minimal_fits(planck_data / module.MASK_NAME)
    return {
        "workdir": workdir,
        "ffp10": ffp10,
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
