from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import healpy as hp
import numpy as np
import pytest
from astropy.io import fits


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/observed_runs/prepare_planck_pr3_admission.py"


def _preparer():
    spec = importlib.util.spec_from_file_location("pr314_smica_preparer", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_inventory(root: Path, *, kind: str, count: int = 300) -> None:
    root.mkdir()
    for index in range(count):
        (root / f"dx12_v3_smica_{kind}_mc_{index:05d}_raw.fits").write_bytes(
            kind.encode("ascii")
        )


def test_smica_existing_null_inventory_is_exactly_300_cmb_plus_noise_pairs(
    tmp_path: Path,
) -> None:
    module = _preparer()
    cmb = tmp_path / "cmb"
    noise = tmp_path / "noise"
    _write_inventory(cmb, kind="cmb")
    _write_inventory(noise, kind="noise")

    paired = module.inspect_smica_cmb_noise_inventory(
        cmb_root=cmb, noise_root=noise
    )

    assert tuple(paired) == tuple(range(300))
    assert paired[0][0].name.endswith("cmb_mc_00000_raw.fits")
    assert paired[0][1].name.endswith("noise_mc_00000_raw.fits")
    (noise / "dx12_v3_smica_noise_mc_00299_raw.fits").unlink()
    with pytest.raises(module.PlanckPreparationError, match="noise.*missing.*00299"):
        module.inspect_smica_cmb_noise_inventory(cmb_root=cmb, noise_root=noise)


def test_smica_combined_null_adds_cmb_and_noise_before_one_reduction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _preparer()
    cmb_path = tmp_path / "cmb.fits"
    noise_path = tmp_path / "noise.fits"
    cmb_path.write_bytes(b"cmb")
    noise_path.write_bytes(b"noise")
    cmb = np.arange(12, dtype=float)
    noise = np.linspace(-0.5, 0.5, 12)
    loaded = {
        cmb_path: module.TemperatureMap(cmb, "K_CMB", "RING", "GALACTIC", 1),
        noise_path: module.TemperatureMap(
            noise, "K_CMB", "RING", "GALACTIC", 1
        ),
    }
    monkeypatch.setattr(
        module, "read_temperature_fits", lambda path, **kwargs: loaded[path]
    )
    seen = []

    def fake_reduce(values, **kwargs):
        seen.append(np.asarray(values).copy())
        return np.asarray(values) * 1.0e6

    monkeypatch.setattr(module, "reduce_temperature_map", fake_reduce)

    reduced = module.reduce_smica_cmb_plus_noise(
        cmb_path=cmb_path, noise_path=noise_path, output_nside=16
    )

    assert len(seen) == 1
    np.testing.assert_array_equal(seen[0], cmb + noise)
    np.testing.assert_array_equal(reduced, (cmb + noise) * 1.0e6)


@pytest.mark.requires_healpy
def test_bandlimited_reduction_converts_kcmb_to_microkcmb_explicitly() -> None:
    module = _preparer()
    alm = np.zeros(hp.Alm.getsize(5), dtype=np.complex128)
    alm[hp.Alm.getidx(5, 2, 0)] = 2.5e-6
    alm[hp.Alm.getidx(5, 3, 1)] = 0.7e-6 - 0.2e-6j
    source = hp.alm2map(alm, nside=16, lmax=5)

    reduced = module.reduce_temperature_map(
        source,
        source_unit="K_CMB",
        source_ordering="RING",
        output_nside=8,
    )
    recovered = hp.map2alm(reduced, lmax=5, iter=3)

    np.testing.assert_allclose(recovered, alm * 1.0e6, rtol=2.0e-5, atol=2.0e-5)
    with pytest.raises(module.PlanckPreparationError, match="K_CMB"):
        module.reduce_temperature_map(
            source,
            source_unit="microK_CMB",
            source_ordering="RING",
            output_nside=8,
        )


def test_release_beam_zeros_outside_analysis_band_become_noop(tmp_path: Path) -> None:
    module = _preparer()
    path = tmp_path / "smica.fits"
    beam = np.array([0.0, 0.0, 1.2, 1.1, 1.0, 0.9], dtype=np.float32)
    beam_hdu = fits.BinTableHDU.from_columns(
        [fits.Column(name="INT_BEAM", format="1E", array=beam)]
    )
    fits.HDUList(
        [fits.PrimaryHDU(), fits.BinTableHDU.from_columns([]), beam_hdu]
    ).writeto(path)

    selected = module.read_temperature_beam(path)

    np.testing.assert_array_equal(selected[:2], np.ones(2))
    np.testing.assert_array_equal(selected[2:], beam[2:].astype(np.float64))


def test_smica_existing_preflight_is_metadata_only_and_exact(tmp_path: Path) -> None:
    module = _preparer()
    cmb = tmp_path / "cmb"
    noise = tmp_path / "noise"
    _write_inventory(cmb, kind="cmb")
    _write_inventory(noise, kind="noise")
    observed = tmp_path / "observed.fits"
    mask = tmp_path / "mask.fits"
    observed.write_bytes(b"not-opened")
    mask.write_bytes(b"not-opened")

    payload = module.build_smica_existing_preflight(
        cmb_root=cmb,
        noise_root=noise,
        observed_smica=observed,
        temperature_mask=mask,
    )

    assert payload["ready"] is True
    assert payload["expected_null_rows"] == 300
    assert payload["null_semantics"] == "FFP10_CMB_PLUS_NOISE_PAIRED_BY_ID"
    assert payload["observed_temperature_payload_opened"] is False


def test_preflight_cli_reports_partial_inventory_without_outputs(
    tmp_path: Path,
) -> None:
    cmb = tmp_path / "cmb"
    noise = tmp_path / "noise"
    _write_inventory(cmb, kind="cmb", count=1)
    _write_inventory(noise, kind="noise", count=1)
    observed = tmp_path / "observed.fits"
    mask = tmp_path / "mask.fits"
    observed.write_bytes(b"metadata")
    mask.write_bytes(b"metadata")

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--preflight-smica-existing",
            "--smica-cmb-root",
            str(cmb),
            "--smica-noise-root",
            str(noise),
            "--observed-smica",
            str(observed),
            "--temperature-mask",
            str(mask),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 3
    payload = json.loads(completed.stdout)
    assert "missing" in payload["blocker"]
    assert payload["observed_temperature_payload_opened"] is False
    assert list(tmp_path.glob("**/smica_existing_plan.json")) == []


def test_prepare_orchestration_keeps_observed_temperature_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    module = _preparer()
    cmb = tmp_path / "cmb"
    noise = tmp_path / "noise"
    cmb.mkdir()
    noise.mkdir()
    observed = tmp_path / "observed.fits"
    mask = tmp_path / "mask.fits"
    observed.write_bytes(b"observed")
    mask.write_bytes(b"mask")
    output = tmp_path / "prepared"
    calls = []
    monkeypatch.setattr(
        module,
        "build_smica_existing_preflight",
        lambda **kwargs: {"ready": True, "observed_temperature_payload_opened": False},
    )
    monkeypatch.setattr(
        module, "write_smica_operator_metadata", lambda **kwargs: calls.append("meta")
    )
    monkeypatch.setattr(
        module,
        "write_smica_existing_null_inventory",
        lambda **kwargs: calls.append("null"),
    )
    monkeypatch.setattr(
        module,
        "write_smica_existing_operator_components",
        lambda **kwargs: calls.append("operator")
        or {"plan_path": str(output / "plan.json"), "covariance_rank": 12},
    )

    result = module.prepare_smica_existing_products(
        output_root=output,
        cmb_root=cmb,
        noise_root=noise,
        observed_smica=observed,
        temperature_mask=mask,
        output_nside=16,
    )

    assert calls == ["meta", "null", "operator"]
    assert result["pipeline_scope"] == "SMICA_ONLY"
    assert result["covariance_rank"] == 12
    assert result["observed_temperature_payload_opened"] is False
