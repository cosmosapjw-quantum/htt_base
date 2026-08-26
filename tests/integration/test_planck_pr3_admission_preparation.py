from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def _module():
    return importlib.import_module(
        "scripts.observed_runs.prepare_planck_pr3_admission"
    )


def _write_inventory(root: Path, *, kind: str, count: int = 300) -> None:
    root.mkdir(parents=True)
    for index in range(count):
        (root / f"dx12_v3_smica_{kind}_mc_{index:05d}_raw.fits").write_bytes(
            f"{kind}-{index:05d}".encode("ascii")
        )


def _raw_fixture(tmp_path: Path):
    cmb = tmp_path / "cmb"
    noise = tmp_path / "noise"
    _write_inventory(cmb, kind="cmb")
    _write_inventory(noise, kind="noise")
    observed = tmp_path / "COM_CMB_IQU-smica_2048_R3.00_full.fits"
    mask = tmp_path / "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
    observed.write_bytes(b"observed-smica")
    mask.write_bytes(b"temperature-mask")
    return cmb, noise, observed, mask


def test_primary_pair_manifest_is_exact_ordered_and_hash_bound(tmp_path: Path) -> None:
    module = _module()
    cmb, noise, observed, mask = _raw_fixture(tmp_path)
    manifest = module.build_raw_input_manifest(
        cmb_root=cmb,
        noise_root=noise,
        observed_smica=observed,
        temperature_mask=mask,
    )

    assert manifest["schema"] == "htt.planck_pr3.smica_raw_input_manifest.v1"
    assert len(manifest["pairs"]) == 300
    assert [row["ordinal"] for row in manifest["pairs"]] == list(range(300))
    assert [row["realization_id"] for row in manifest["pairs"]] == list(range(300))
    assert manifest["ordered_row_ids_sha256"] == module.SMICA_EXISTING_INVENTORY_ID
    module.validate_raw_input_manifest(manifest, verify_files=True)

    mutated = cmb / "dx12_v3_smica_cmb_mc_00017_raw.fits"
    mutated.write_bytes(b"changed-with-same-scope")
    with pytest.raises(module.PlanckPreparationError, match="hash"):
        module.validate_raw_input_manifest(manifest, verify_files=True)


def test_raw_observation_and_pair_manifest_are_acceptance_bound(tmp_path: Path) -> None:
    module = _module()
    cmb, noise, observed, mask = _raw_fixture(tmp_path)
    manifest = module.build_raw_input_manifest(
        cmb_root=cmb,
        noise_root=noise,
        observed_smica=observed,
        temperature_mask=mask,
    )
    identity = module.raw_input_manifest_identity(manifest)

    assert identity.startswith("sha256:")
    changed = dict(manifest)
    changed["observed_smica"] = dict(manifest["observed_smica"])
    changed["observed_smica"]["sha256"] = "sha256:" + "0" * 64
    assert module.raw_input_manifest_identity(changed) != identity
    with pytest.raises(module.PlanckPreparationError, match="observed_smica hash"):
        module.validate_raw_input_manifest(changed, verify_files=False)


def test_partial_primary_inventory_emits_no_manifest(tmp_path: Path) -> None:
    module = _module()
    cmb = tmp_path / "cmb"
    noise = tmp_path / "noise"
    _write_inventory(cmb, kind="cmb", count=299)
    _write_inventory(noise, kind="noise", count=299)
    observed = tmp_path / "observed.fits"
    mask = tmp_path / "mask.fits"
    observed.write_bytes(b"observed")
    mask.write_bytes(b"mask")

    with pytest.raises(module.PlanckPreparationError, match="missing"):
        module.build_raw_input_manifest(
            cmb_root=cmb,
            noise_root=noise,
            observed_smica=observed,
            temperature_mask=mask,
        )
