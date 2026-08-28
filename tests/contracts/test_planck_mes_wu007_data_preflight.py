from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/validate_planck_mes_wu007_data_preflight.py"
SPEC = importlib.util.spec_from_file_location("wu007_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


def _touch(path: Path, payload: bytes = b"x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _repo_terminals(root: Path) -> None:
    terminal4 = root / "docs/generated/planck_mes_irrep_inventory/terminal.json"
    terminal4.parent.mkdir(parents=True, exist_ok=True)
    terminal4.write_text(
        json.dumps(
            {
                "work_unit": "PMG-WU-004",
                "state": "SUCCEEDED",
                "next_executable_action": "PMG-WU-005",
            }
        )
    )
    terminal6 = root / "docs/generated/planck_mes_irrep_analysis/terminal.json"
    terminal6.parent.mkdir(parents=True, exist_ok=True)
    terminal6.write_text(
        json.dumps(
            {
                "work_unit": "PMG-WU-006",
                "state": "SUCCEEDED",
                "replay_status": "MATCH",
                "raw_data_read_or_mutated": False,
            }
        )
    )


def _planck_inputs(workdir: Path) -> None:
    planck = workdir / "raw/planck_data"
    for name in (
        "COM_CMB_IQU-smica_2048_R3.00_full.fits",
        "COM_CMB_IQU-commander_2048_R3.00_full.fits",
        "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits",
    ):
        _touch(planck / name)
    cmb = workdir / "raw/planck_ffp10/smica/cmb_mc"
    for index in range(1000):
        if index == 970:
            continue
        _touch(cmb / f"dx12_v3_smica_cmb_mc_{index:05d}_raw.fits")
    noise = workdir / "raw/planck_ffp10/smica/noise_mc"
    for index in range(300):
        _touch(noise / f"dx12_v3_smica_noise_mc_{index:05d}_raw.fits")
    commander = workdir / "raw/planck_ffp10/commander/cmb_mc"
    for index in range(3):
        _touch(commander / f"dx12_v3_commander_cmb_mc_{index:05d}_raw.fits")
    for index in range(3, 7):
        _touch(
            commander
            / f"dx12_v3_commander_cmb_mc_{index:05d}_raw.fits.partial"
        )


def _local_gap_sources(workdir: Path, repo: Path) -> None:
    for spectrum in ("tt", "te", "ee"):
        _touch(workdir / f"htt_extracted/act_dr6_{spectrum}_bandpowers.npz")
    for stem in (
        "BGS_ANY_NGC",
        "BGS_ANY_SGC",
        "LRG_NGC",
        "LRG_SGC",
        "QSO_NGC",
        "QSO_SGC",
    ):
        _touch(
            workdir
            / f"compact_products/desi/{stem}_clustering_extended.npz"
        )
    for name in (
        "obs_defaults.json",
        "obs_defaults_watkins2023.json",
        "obs_defaults_CF4pp.json",
    ):
        (repo / name).write_text("{}")


def _complete_fixture(tmp_path: Path) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    workdir = tmp_path / "workdir"
    workdir.mkdir()
    _repo_terminals(repo)
    _planck_inputs(workdir)
    _local_gap_sources(workdir, repo)
    return repo, workdir


def test_complete_download_surface_opens_exploratory_wu007(tmp_path: Path) -> None:
    repo, workdir = _complete_fixture(tmp_path)
    payload = module.build_preflight(workdir=workdir, repo_root=repo)
    assert payload["state"] == "PASS"
    assert payload["download"] == {
        "mandatory_remote_download_count": 0,
        "active_downloads": 0,
        "eta_minutes": 0,
        "classification": "COMPLETE",
    }
    assert payload["planck_wu007"]["smica_cmb"]["count"] == 999
    assert payload["planck_wu007"]["smica_noise"]["count"] == 300
    assert payload["obs_bundle"]["target_count"] == 12
    assert payload["obs_bundle"]["local_placement_required_count"] == 12
    assert payload["obs_bundle"]["unresolved_local_source_count"] == 0
    assert (
        payload["transition"]["wu007"]["execution_permission"]
        == "EXPLORATORY_NONAUTHORITATIVE"
    )
    assert (
        payload["transition"]["wu007"]["claim_admission"]
        == "BLOCKED_PENDING_PMG_WU005_REBIND"
    )


def test_known_missing_00970_is_required_not_a_download_gap(tmp_path: Path) -> None:
    repo, workdir = _complete_fixture(tmp_path)
    _touch(
        workdir
        / "raw/planck_ffp10/smica/cmb_mc/dx12_v3_smica_cmb_mc_00970_raw.fits"
    )
    with pytest.raises(module.PreflightError, match="unexpected=00970"):
        module.inspect_planck_wu007_inputs(workdir)


def test_commander_partial_cannot_be_promoted_to_complete(tmp_path: Path) -> None:
    repo, workdir = _complete_fixture(tmp_path)
    _touch(
        workdir
        / "raw/planck_ffp10/commander/cmb_mc/"
        "dx12_v3_commander_cmb_mc_00003_raw.fits"
    )
    with pytest.raises(module.PreflightError, match="unexpected=00003"):
        module.inspect_planck_wu007_inputs(workdir)


def test_missing_local_source_does_not_reopen_download_claim(tmp_path: Path) -> None:
    repo, workdir = _complete_fixture(tmp_path)
    (
        workdir / "compact_products/desi/QSO_SGC_clustering_extended.npz"
    ).unlink()
    report = module.inspect_obs_bundle_local_gaps(
        workdir=workdir, repo_root=repo
    )
    assert report["unresolved_local_source_count"] == 1
    assert report["remote_download_required_count"] is None
    assert report["classification"] == (
        "BLOCKED_UNRESOLVED_LOCAL_SOURCE_NOT_CLASSIFIED_AS_DOWNLOAD"
    )


def test_existing_obs_bundle_target_counts_as_present(tmp_path: Path) -> None:
    repo, workdir = _complete_fixture(tmp_path)
    target = workdir / "obs_bundle/cmb/powerspectra/act_dr6_tt.npz"
    _touch(target, b"placed")
    (workdir / "htt_extracted/act_dr6_tt_bandpowers.npz").unlink()
    report = module.inspect_obs_bundle_local_gaps(
        workdir=workdir, repo_root=repo
    )
    assert report["present_count"] == 1
    assert report["local_placement_required_count"] == 11
    assert report["unresolved_local_source_count"] == 0


def test_preflight_output_beneath_raw_is_refused(tmp_path: Path) -> None:
    repo, workdir = _complete_fixture(tmp_path)
    payload = module.build_preflight(workdir=workdir, repo_root=repo)
    with pytest.raises(module.PreflightError, match="beneath the raw"):
        module._write_output(
            workdir / "raw/forbidden.json", payload, workdir=workdir
        )
