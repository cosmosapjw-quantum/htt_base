"""Offline tests of scripts/r108/gaia_acquire.py helpers (no network)."""
import numpy as np
from astropy.table import MaskedColumn, Table

from scripts.r108 import gaia_acquire as acq


def test_fits_safe_converts_variable_length_strings(tmp_path):
    t = Table()
    t["source_id"] = np.array([1, 2, 3], np.int64)
    t["name"] = MaskedColumn(np.array(["ICRF J1", None, "x"], dtype=object), mask=[False, True, False])
    t["flag"] = np.array([True, False, True])
    acq.fits_safe(t).write(tmp_path / "t.fits", format="fits")
    back = Table.read(tmp_path / "t.fits")
    names = back["name"].filled("") if hasattr(back["name"], "filled") else back["name"]  # astropy reads '' as masked
    assert list(names) == ["ICRF J1", "", "x"] and back["source_id"].dtype.newbyteorder("=") == np.dtype(np.int64)


def test_queries_are_the_manifest_join_and_split_ranges_cover_all_source_ids():
    assert acq.D10_ADQL.startswith("SELECT a.source_id, a.catalogue_name") and "USING (source_id)" in acq.D10_ADQL
    n = 48
    edges = [acq.SOURCE_ID_MAX * k // n for k in range(n + 1)]
    assert edges[0] == 0 and edges[-1] == acq.SOURCE_ID_MAX and all(b > a for a, b in zip(edges, edges[1:]))
    assert acq.SOURCE_ID_MAX == 12 * 4 ** 12 * 2 ** 35
    assert "WHERE x.icrf3sx = 'true'" in acq.ICRF3_GAIA_ADQL and "gaia_source" not in acq.D10F_ADQL


def test_new_dir_refuses_existing(tmp_path):
    acq.new_dir(tmp_path, "p")
    try:
        acq.new_dir(tmp_path, "p")
    except FileExistsError:
        return
    raise AssertionError("existing product directory was not refused")


def test_d10_query_is_verbatim_manifest_adql():
    from scripts.r107_cloud import acquisition as manifest

    item = [i for i in manifest.ITEMS if i["id"] == "D10"][0]
    assert item["adql"] == acq.D10_ADQL and item["service"] == acq.GAIA_TAP
