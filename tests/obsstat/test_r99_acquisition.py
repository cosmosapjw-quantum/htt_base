"""Narrow contracts for acquisition and an independent geometric exposure."""
import math
import healpy as hp
import numpy as np
import pytest
from scripts.r99 import acquisition as a


def test_deferred_and_non_file_responses_cannot_be_science_payload():
    with pytest.raises(a.DeferredProduct, match="202"):
        a.validate_product_response(202, {"Content-Type": "application/json",
                                       "Content-Length": "349"}, 4507238400)
    with pytest.raises(ValueError, match="non-scientific"):
        a.validate_product_response(200, {"Content-Type": "text/html",
                                         "Content-Length": "100"}, 100)
    with pytest.raises(ValueError, match="size mismatch"):
        a.validate_product_response(200, {"Content-Length": "99"}, 100)


def test_resume_requires_exact_range_and_release_size():
    headers = {"Content-Type": "application/octet-stream", "Content-Length": "32",
               "Content-Range": "bytes 64-95/100"}
    assert a.validate_product_response(206, headers, 100, start=64, count=32)
    with pytest.raises(ValueError, match="honored exactly"):
        a.validate_product_response(200, headers, 100, start=64, count=32)
    with pytest.raises(ValueError, match="honored exactly"):
        a.validate_product_response(206, headers, 101, start=64, count=32)
    with pytest.raises(ValueError, match="interval"):
        a.validate_product_response(206, headers, 100, start=64, count=37)


def test_identifiers_never_roundtrip_through_float_and_mocks_split_by_box():
    token = "1237662306187083999"
    assert a.exact_identifier(token) == 1237662306187083999
    assert a.exact_identifier("1.237662306187083999e18") == int(token)
    with pytest.raises(ValueError, match="floating"):
        a.exact_identifier(float(token))
    for bad in ("NaN", "-1", "1.5"):
        with pytest.raises(ValueError):
            a.exact_identifier(bad)
    one = a.mock_genealogy("SDSS_mock_R19007.0_err_corr.dat")
    two = a.mock_genealogy("SDSS_mock_R19007.7_err_corr.dat")
    assert one["independent_holdout_group"] == two["independent_holdout_group"]
    assert one["observer"] != two["observer"]
    with pytest.raises(ValueError):
        a.mock_genealogy("SDSS_mock_R19007.8_err_corr.dat")


def test_budget_is_explicit_and_deferred_job_stays_deferred():
    plan = {"jobs": [
        {"id": "one", "expected_bytes": 17, "status": "PREPARED", "url": "https://example.org/a"},
        {"id": "two", "expected_bytes": 31, "status": "DEFERRED_HTTP_202", "url": "https://example.org/b"}]}
    for ids, budget in (([], 100), (["one", "one"], 100), (["missing"], 100), (["one"], 16)):
        with pytest.raises(ValueError):
            a.select_jobs(plan, ids, budget)
    result = a.select_jobs(plan, ["one", "two"], 48)
    assert result["expected_bytes"] == 48
    assert result["deferred_ids"] == ["two"]
    assert not result["ready_for_explicit_future_fetch"]
    assert result["downloaded_bytes"] == 0


def test_ra_wrap_polygon_oracle_overlap_and_winding():
    p = a.polygon_vectors("[358 -10 2 -10 2 10 358 10]")
    directions = hp.ang2vec([0, 359, 1, 180, 10, 0], [0, 0, 0, 0, 0, 20], lonlat=True)
    assert np.array_equal(a.independent_union_membership([p], directions),
                          [True, True, True, False, False, False])
    union = a.polygon_union([p], 32)
    assert np.array_equal(union, a.polygon_union([p, p], 32))
    assert np.array_equal(union, a.polygon_union([p[::-1]], 32))
    sample = np.arange(len(union))
    exact = a.independent_union_membership([p], np.asarray(hp.pix2vec(32, sample, nest=True)).T)
    assert np.array_equal(union, exact)
    assert union[hp.ang2pix(32, 0, 0, nest=True, lonlat=True)]
    assert not union[hp.ang2pix(32, 180, 0, nest=True, lonlat=True)]


def test_analytic_octant_area_and_nested_area_conservation():
    # x,y,z >= 0 is one spherical octant with solid angle pi/2.
    p = np.eye(3)
    mask = a.polygon_union([p], 64)
    fraction = a.aggregate_exposure(mask, 64, 8)
    area = mask.sum() * hp.nside2pixarea(64)
    assert abs(area - math.pi / 2) < 0.03
    assert fraction.sum() * hp.nside2pixarea(8) == pytest.approx(area, abs=2e-15)
    assert np.any((fraction > 0) & (fraction < 1))


def test_zero_count_cells_preserved_and_positive_count_support_mismatch_rejected():
    f = np.zeros(48)
    f[:3] = [1, .5, .25]
    counts = np.zeros(48)
    counts[0] = 4
    area, offset, support = a.count_offset(f, 2, counts)
    assert support.sum() == 3
    assert np.count_nonzero(support & (counts == 0)) == 2
    assert np.exp(offset[support]) == pytest.approx(area[support])
    assert np.all(np.isneginf(offset[~support]))
    counts[3] = 1
    with pytest.raises(ValueError, match="outside"):
        a.count_offset(f, 2, counts)
    f[4] = np.nan
    with pytest.raises(ValueError, match="fraction"):
        a.count_offset(f, 2)
