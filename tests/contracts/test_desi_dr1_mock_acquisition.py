"""Restart/storage contract tests for the official DESI DR1 mock acquisition."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from astropy.io import fits

REPO = Path(__file__).resolve().parents[2]


def _load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


acq = _load("dl_pipeline/scripts/download_desi_dr1_mocks.py", "desi_mock_acq")
card = _load("scripts/desi_official_mock_card.py", "desi_official_card")


def _write_random(path: Path, seed: int) -> None:
    rng = np.random.default_rng(seed)
    n = 256
    cols = [
        fits.Column(name="RA", format="D", array=rng.uniform(0, 360, n)),
        fits.Column(name="DEC", format="D", array=rng.uniform(-70, 70, n)),
        fits.Column(name="Z", format="D", array=rng.uniform(0.05, 0.45, n)),
        fits.Column(name="WEIGHT", format="D", array=rng.uniform(0.8, 1.2, n)),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    fits.BinTableHDU.from_columns(cols).writeto(path)


def test_family_contract_binds_ffa_data_and_two_random_indices() -> None:
    ez = acq.family_contract("ezmock", 17)
    assert ez["data"] == ("BGS_ffa_NGC_clustering.dat.fits",
                          "BGS_ffa_SGC_clustering.dat.fits")
    assert ez["random"][0][0] == "BGS_ffa_NGC_0_clustering.ran.fits"
    assert ez["random"][1][1] == "BGS_ffa_SGC_1_clustering.ran.fits"
    ab = acq.family_contract("abacus", 0)
    assert ab["data"][0] == "BGS_BRIGHT-21.5_ffa_NGC_clustering.dat.fits"
    assert ab["random"][0][1] == \
        "BGS_BRIGHT-21.5_ffa_SGC_0_clustering.ran.fits"


def test_aria_queue_is_part_file_and_checksum_bound(tmp_path) -> None:
    queue = tmp_path / "queue.txt"
    n = acq._aria_input(queue, [{
        "url": "https://example.invalid/mock.fits", "dir": str(tmp_path),
        "out": "mock.fits.part", "sha256": "a" * 64,
    }])
    assert n == 1
    text = queue.read_text()
    assert "out=mock.fits.part" in text
    assert "checksum=sha-256=" + "a" * 64 in text


def test_random_pair_is_compacted_then_raw_is_deleted(tmp_path) -> None:
    directory = tmp_path / "EZmock/bright/v1/mock1"
    names = ("BGS_ffa_NGC_0_clustering.ran.fits",
             "BGS_ffa_SGC_0_clustering.ran.fits")
    for i, name in enumerate(names):
        _write_random(directory / name, i + 1)
    expected = {name: acq.sha256(directory / name) for name in names}
    row = acq.compact_random_pair(directory, names, expected, 0, tmp_path,
                                  retain_raw=False)
    assert not any((directory / name).exists() for name in names)
    assert Path(row["path"]).is_file()
    assert acq.sha256(Path(row["path"])) == row["sha256"]
    with np.load(row["path"]) as data:
        assert int(data["nside"]) == 64
        assert data["NGC"].shape == (12 * 64 * 64,)
        assert float(data["NGC"].sum()) > 0
    meta = json.loads(Path(row["metadata_path"]).read_text())
    assert meta["raw_retained"] is False
    assert meta["source_sha256"] == expected
    assert meta["extraction_config"]["weight_column"] == "WEIGHT"
    assert len(row["deletion_receipts"]) == 2
    for receipt in row["deletion_receipts"]:
        deletion = json.loads(Path(receipt).read_text())
        assert deletion["source_absent"] is True
        assert deletion["compact_sha256"] == row["sha256"]


def test_random_replication_audit_is_measurement_not_second_null() -> None:
    rows = [{
        "family": "ezmock", "realization": 1, "random_indices": [0, 1],
        "amplitude_r0": 1.0, "amplitude_r1": 1.1,
        "absolute_amplitude_difference": 0.1,
        "relative_amplitude_difference": 0.1,
        "dipole_direction_difference_deg": 2.0,
    }]
    summary = card._audit_summary(rows)
    assert summary["n_audited"] == 1
    assert summary["relative_amplitude_difference"]["median"] == 0.1
    assert "not an additional cosmological null" in summary["interpretation"]


def test_official_finite_rank_is_observation_inclusive_and_recomputable() -> None:
    rank = card._finite_rank(2.5, [1.0, 2.0, 3.0, 4.0])
    assert rank["n_mock"] == 4
    assert rank["upper_exceedance_count"] == 2
    assert rank["lower_exceedance_count"] == 2
    assert rank["right_tail_p"] == 3 / 5
    assert rank["left_tail_p"] == 3 / 5
    assert rank["central_two_sided_p"] == 1.0
    assert rank["support_resolution"] == 1 / 5


def test_receipt_parser_rejects_duplicate_and_unsafe_names(tmp_path) -> None:
    receipt = tmp_path / "receipt.sha256sum"
    receipt.write_text(f"{'a' * 64}  file.fits\n{'b' * 64}  file.fits\n")
    try:
        acq.parse_receipt(receipt)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate receipt basename was accepted")
    receipt.write_text(f"{'a' * 64}  ../file.fits\n")
    try:
        acq.parse_receipt(receipt)
    except ValueError as exc:
        assert "unsafe" in str(exc)
    else:
        raise AssertionError("unsafe receipt path was accepted")


def test_missing_weight_column_fails_closed(tmp_path) -> None:
    path = tmp_path / "missing_weight.fits"
    cols = [
        fits.Column(name="RA", format="D", array=np.asarray([1.0])),
        fits.Column(name="DEC", format="D", array=np.asarray([2.0])),
        fits.Column(name="Z", format="D", array=np.asarray([0.2])),
    ]
    fits.BinTableHDU.from_columns(cols).writeto(path)
    try:
        acq.random_pixel_counts(path)
    except ValueError as exc:
        assert "WEIGHT" in str(exc)
    else:
        raise AssertionError("missing WEIGHT column was silently accepted")
    try:
        card.pixel_counts(path)
    except ValueError as exc:
        assert "WEIGHT" in str(exc)
    else:
        raise AssertionError("data estimator silently substituted unit WEIGHT")


def test_completed_record_rehashes_data_and_requires_two_deletion_receipts(
        tmp_path) -> None:
    directory = tmp_path / "EZmock/bright/v1/mock1"
    names = ("BGS_ffa_NGC_0_clustering.ran.fits",
             "BGS_ffa_SGC_0_clustering.ran.fits")
    for i, name in enumerate(names):
        _write_random(directory / name, i + 1)
    expected = {name: acq.sha256(directory / name) for name in names}
    window = acq.compact_random_pair(directory, names, expected, 0, tmp_path,
                                     retain_raw=False)
    data_path = directory / "BGS_ffa_NGC_clustering.dat.fits"
    data_path_sgc = directory / "BGS_ffa_SGC_clustering.dat.fits"
    data_path.write_bytes(b"authenticated-data")
    data_path_sgc.write_bytes(b"authenticated-sgc!")
    receipt = directory / "official.sha256sum"
    receipt.write_text("receipt\n")
    record = {
        "schema": "htt.desi_dr1_mock_acquisition_record.v1",
        "family": "ezmock", "realization": 1, "status": "authenticated",
        "receipt": str(receipt), "receipt_sha256": acq.sha256(receipt),
        "data_files": [
            {"path": str(data_path_sgc), "sha256": acq.sha256(data_path_sgc),
             "size_bytes": data_path_sgc.stat().st_size},
            {"path": str(data_path), "sha256": acq.sha256(data_path),
             "size_bytes": data_path.stat().st_size},
        ],
        "random_windows": {"0": window},
    }
    record_path = directory / "acquisition_record.json"
    record_path.write_text(json.dumps(record))
    assert acq._record_complete(record_path, audit_required=False)

    # Same-size byte corruption must be noticed before a record is skipped.
    data_path.write_bytes(b"corrupted-data!!!!")
    assert data_path.stat().st_size == record["data_files"][0]["size_bytes"]
    assert not acq._record_complete(record_path, audit_required=False)
    data_path.write_bytes(b"authenticated-data")

    # Two records that alias the same cap/file cannot masquerade as NGC+SGC.
    valid_rows = list(record["data_files"])
    record["data_files"] = [valid_rows[0], valid_rows[0]]
    record_path.write_text(json.dumps(record))
    assert not acq._record_complete(record_path, audit_required=False)
    record["data_files"] = valid_rows

    record["random_windows"]["0"]["deletion_receipts"] = \
        record["random_windows"]["0"]["deletion_receipts"][:1]
    record_path.write_text(json.dumps(record))
    assert not acq._record_complete(record_path, audit_required=False)
