import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from astropy import units as u
from astropy.coordinates import SkyCoord

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('d06', HERE / 'flow_control.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_cell_bounds_no_clipping_or_wrapping():
    points = np.array([[-500, -500, -500], [0, 0, 0], [499.999, 0, 0],
                       [500, 0, 0], [-500.001, 0, 0], [np.nan, 0, 0]])
    ix, valid = m.cell_indices(points)
    np.testing.assert_array_equal(valid, [1, 1, 1, 0, 0, 0])
    np.testing.assert_array_equal(ix[:3], [[0, 0, 0], [64, 64, 64], [127, 64, 64]])
    assert (ix[3:] == -1).all()


def test_exact_edges_and_both_nextafter_neighbors_all_axes():
    edges = np.linspace(-500., 500., 129)
    for axis in range(3):
        for k, edge in enumerate(edges):
            for value, expected in ((np.nextafter(edge, -np.inf), k - 1),
                                    (edge, k), (np.nextafter(edge, np.inf), k)):
                point = np.zeros((1, 3))
                point[0, axis] = value
                index, inside = m.cell_indices(point)
                accepted = -500. <= value < 500.
                assert bool(inside[0]) == accepted
                if accepted:
                    expected_xyz = np.full(3, 64)
                    expected_xyz[axis] = expected
                    np.testing.assert_array_equal(index[0], expected_xyz)
                    assert ((0 <= index[0]) & (index[0] < 128)).all()
                else:
                    assert (index[0] == -1).all()


def test_query_at_endpoint_neighbors_and_internal_regression_all_axes():
    grid = np.arange(128 ** 3, dtype=float).reshape(128, 128, 128)
    for axis in range(3):
        for value, expected in ((-500., 0), (np.nextafter(-500., np.inf), 0),
                                (np.nextafter(500., -np.inf), 127),
                                (-242.18750000000003, 32)):
            point = np.zeros((1, 3))
            point[0, axis] = value
            found, inside, index = m.query(grid, point)
            expected_xyz = np.full(3, 64)
            expected_xyz[axis] = expected
            assert inside[0]
            assert found[0] == grid[tuple(expected_xyz)]
        for value in (500., np.nextafter(500., np.inf), np.nextafter(-500., -np.inf), np.nan, np.inf, -np.inf):
            point = np.zeros((1, 3))
            point[0, axis] = value
            found, inside, index = m.query(grid, point)
            assert not inside[0] and np.isnan(found[0]) and (index[0] == -1).all()


def test_boundary_repair_leaves_all_cached_host_lookup_and_numerics_unchanged():
    result = json.loads((HERE / 'D06_RESULT.json').read_text())
    initial = json.loads((HERE / 'D06_RESULT_INITIAL.json').read_text())
    with Path(result['host_ledger']['path']).open() as stream:
        rows = list(csv.DictReader(stream))
    xyz = np.array([[float(r[k]) for k in ('SGX', 'SGY', 'SGZ')] for r in rows])
    expected = np.array([[int(r[k]) for k in ('ix', 'iy', 'iz')] for r in rows])
    found, inside = m.cell_indices(xyz)
    assert len(rows) == 494 and inside.all()
    np.testing.assert_array_equal(found, expected)
    assert result['host_ledger'] == initial['host_ledger']
    initial_candidate = json.loads((HERE / 'CANDIDATE_INITIAL.json').read_text())
    for name in ('D06_HOST_FLOW.png', 'D06_HOST_FLOW.pdf'):
        assert m.sha(HERE / name) == initial_candidate['files'][name]['sha256']
    # Exact equality of all prior scientific values, not a tolerance check or
    # rerun of the complete grid analysis. Only lookup/seal metadata may differ.
    for key, value in initial.items():
        if key not in ('generator_sha256', 'coordinate_policy'):
            assert result[key] == value
    for key, value in initial['coordinate_policy'].items():
        if key != 'lookup':
            assert result['coordinate_policy'][key] == value


def test_axis_order_nonconstant_grid():
    grid = np.zeros((128, 128, 128))
    grid[1, 2, 3] = 123.
    point = -500 + (np.array([[1, 2, 3]]) + .5) * m.DELTA
    value, valid, ix = m.query(grid, point)
    assert valid[0] and value[0] == 123
    missing, valid, _ = m.query(grid, np.array([[600, 0, 0]]))
    assert not valid[0] and np.isnan(missing[0])


def test_independent_supergalactic_basis_and_radius():
    gal = SkyCoord(l=[137.37, 47.37, 0, 90] * u.deg, b=[0, 6.32, 0, 30] * u.deg, frame='galactic')
    xyz = gal.supergalactic.cartesian.xyz.value.T
    manual = m.manual_supergalactic_from_galactic(gal.l.deg, gal.b.deg)
    np.testing.assert_allclose(manual, xyz, atol=1e-14, rtol=0)
    np.testing.assert_allclose(xyz[0], [1, 0, 0], atol=1e-14)
    np.testing.assert_allclose(xyz[1], [0, 0, 1], atol=1e-14)
    position, direction = m.sg_positions([10, 200], [-20, 30], [1000, 10000])
    np.testing.assert_allclose(np.linalg.norm(position, axis=1), [10, 100], atol=1e-12)
    np.testing.assert_allclose(np.linalg.norm(direction, axis=1), 1, atol=1e-14)


def test_proxy_sign_limit_and_undefined_mass():
    shifts, valid = m.redshift_proxy_shift([1000, 1000, 1000, 0, 1000], [0, 100, -100, 1, 1200])
    assert shifts[0] == 0
    assert shifts[1] < 0 < shifts[2]
    assert not valid[3] and not valid[4]
    assert np.isnan(shifts[3:]).all()
    assert shifts[1] == pytest.approx(5 * np.log10(.9))


def test_actual_source_qualification_and_previous_wrong_link_preserved():
    result = json.loads((HERE / 'D06_RESULT.json').read_text())
    assert result['sources']['new_CF4pp_mean_std_grids.npz']['bytes'] == 167773886
    assert result['sources']['CF4pp_mean_std_grids.npz']['bytes'] == 167773716
    assert result['sources']['new_CF4pp_mean_std_grids.npz']['last_modified'].startswith('Tue, 13 Oct 2026')
    old = json.loads((HERE / 'STALE_LINKED_NPZ_DIAGNOSTIC.json').read_text())
    assert old['CF4pp_radial_minus_center_vector_projection_kms']['quantiles_0_16_50_84_100'][0] < -4000
    assert max(abs(x) for x in result['CF4pp_radial_minus_center_vector_projection_kms']['quantiles_0_16_50_84_100']) < 1e-9
    assert result['generator_sha256'] == m.sha(HERE / 'flow_control.py')


def test_actual_host_queries_match_corrected_raw_cells():
    result = json.loads((HERE / 'D06_RESULT.json').read_text())
    path = Path(result['host_ledger']['path'])
    assert m.sha(path) == result['host_ledger']['sha256']
    with path.open() as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == len({r['PGC'] for r in rows}) == 494
    assert len({r['CF4_group'] for r in rows}) == 482
    assert len({(r['ix'], r['iy'], r['iz']) for r in rows}) == 460
    with np.load(m.RAW / 'new_CF4pp_mean_std_grids.npz', allow_pickle=False) as grid:
        mean, rms = grid['vr_mean'], grid['vr_std']
    for row in rows:
        cell = tuple(int(row[k]) for k in ('ix', 'iy', 'iz'))
        assert row['query_status'] == 'VALID_SOURCE_CELL'
        assert float(row['vr_mean_kms']) == mean[cell]
        assert float(row['vr_rms_kms']) == rms[cell]
        expected = 5 * np.log10((float(row['CF4_Vcmb_kms']) - mean[cell]) / float(row['CF4_Vcmb_kms']))
        assert float(row['proxy_delta_mu']) == pytest.approx(expected)


def test_grouped_is_finite_but_geometry_holds():
    result = json.loads((HERE / 'D06_RESULT.json').read_text())
    grouped = result['grouped_validation']
    assert grouped['velocity_raw']['shape'] == [3, 64, 64, 64]
    assert grouped['scalar_error_raw']['shape'] == [64, 64, 64]
    assert grouped['query_status'].startswith('HOLD')
    np.testing.assert_allclose(np.array(grouped['velocity_times52_kms']['quantiles_0_16_50_84_100']),
                               52 * np.array(grouped['velocity_raw']['quantiles_0_16_50_84_100']), atol=1e-10)
    assert not any(k.startswith(('CRPIX', 'CRVAL', 'CDELT', 'CTYPE', 'CUNIT')) for k in grouped['header_keys'])


def test_frozen_d03_identity_stays_bound():
    result = json.loads((HERE / 'D06_RESULT.json').read_text())
    assert result['D03_candidate_digest'] == m.D03_DIGEST
    for name, digest in result['D03_consumed_source_sha'].items():
        assert m.sha(m.D03 / name) == digest
