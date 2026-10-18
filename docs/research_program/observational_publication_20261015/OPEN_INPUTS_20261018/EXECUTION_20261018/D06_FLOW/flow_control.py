"""Source-qualified flow queries; source-dependent proxy sensitivities only.

Author CF4++ cell lookup is reproduced without clipping. Grouped FITS has no WCS,
so only source/finite-field validation is allowed for that distinct product.
"""
import os
for _name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[_name] = '2'
from pathlib import Path
from collections import Counter
import csv
import hashlib
import importlib.util
import json
import sys
from email.utils import parsedate_to_datetime
import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.io import fits

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'AGENTS.md').exists())
RAW = Path('/mnt/extdrive/workdir/htt_open_data/cf4/d06_flow_20261018')
D03 = HERE.parent / 'D03_PANTHEON_CF4'
D03_DIGEST = 'c326fc79b4cfd255d4655cb47b27a4b399403179c3342ac30ae7113c80dcc388'
CF4 = RAW.parent / 'J_ApJ_944_94'
CF4_SHA = {'ReadMe': '2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4',
           'table2.dat': '8e908928e68352b59292cf67020a4d70aaa6d30f278dfa6aa3e41a9df808332f'}
C = 299792.458
L = 1000.
N = 128
DELTA = L / N


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sealed(path, expected):
    blob = path.read_bytes()
    if hashlib.sha256(blob).hexdigest() != expected:
        raise ValueError('immutable source mismatch: ' + str(path))
    return blob


def summary(values):
    values = np.asarray(values)
    finite = np.isfinite(values)
    return {'shape': list(values.shape), 'total': int(values.size), 'finite': int(finite.sum()),
            'nonfinite': int((~finite).sum()),
            'quantiles_0_16_50_84_100': np.quantile(values[finite], [0, .16, .5, .84, 1]).tolist() if finite.any() else None}


def cell_indices(xyz):
    """Exact half-open source cells on [-500,500); no clipping or wrapping."""
    xyz = np.asarray(xyz, dtype=float)
    if xyz.ndim != 2 or xyz.shape[1] != 3:
        raise ValueError('positions must have shape n,3')
    inside = np.isfinite(xyz).all(axis=1) & (xyz >= -L / 2).all(axis=1) & (xyz < L / 2).all(axis=1)
    indices = np.full(xyz.shape, -1, dtype=int)
    # Addition before division can round a value below an edge onto that edge,
    # including mapping nextafter(500,-inf) to the invalid index128. These
    # binary-exact edges preserve ordering of every accepted input coordinate.
    edges = np.linspace(-L / 2, L / 2, N + 1)
    indices[inside] = np.searchsorted(edges, xyz[inside], side='right') - 1
    return indices, inside


def sg_positions(ra, dec, velocity):
    """Numeric h^-1Mpc redshift proxy cz/100, FK5/J2000 directions."""
    coord = SkyCoord(ra=np.asarray(ra) * u.deg, dec=np.asarray(dec) * u.deg,
                     frame='fk5', equinox='J2000.000')
    direction = coord.supergalactic.cartesian.xyz.value.T
    radius = np.asarray(velocity, dtype=float) / 100.
    return direction * radius[:, None], direction


def manual_supergalactic_from_galactic(lon, lat):
    """Independent Cartesian basis: north SG pole (47.37,6.32) Galactic deg."""
    def unit(l, b):
        l, b = np.deg2rad(np.asarray([l, b], float))
        return np.stack([np.cos(b) * np.cos(l), np.cos(b) * np.sin(l), np.sin(b)], axis=-1)
    x = unit(137.37, 0.)
    z = unit(47.37, 6.32)
    y = np.cross(z, x)
    return unit(lon, lat) @ np.stack([x, y, z]).T


def query(field, xyz):
    if field.shape != (N, N, N):
        raise ValueError('CF4++ scalar field shape changed')
    indices, inside = cell_indices(xyz)
    values = np.full(len(xyz), np.nan)
    good = indices[inside]
    values[inside] = field[good[:, 0], good[:, 1], good[:, 2]]
    return values, inside, indices


def redshift_proxy_shift(cz, velocity):
    """5log10((cz-u)/cz), only where both artificial H100 distances are positive.

    This is an algebraic redshift-distance proxy sensitivity, NOT a physical
    luminosity distance/finite-z correction and NOT an alteration of D03 data.
    """
    cz, velocity = np.broadcast_arrays(np.asarray(cz, float), np.asarray(velocity, float))
    valid = np.isfinite(cz) & np.isfinite(velocity) & (cz > 0) & (cz - velocity > 0)
    result = np.full(cz.shape, np.nan)
    result[valid] = 5 * np.log10((cz[valid] - velocity[valid]) / cz[valid])
    return result, valid


def load_d03():
    candidate = json.loads((D03 / 'CANDIDATE.json').read_text())
    if candidate['candidate_digest_sha256'] != D03_DIGEST:
        raise ValueError('D03 frozen candidate identity changed')
    for name in ('d03.py', 'results/OBJECT_GRAPH.csv', 'results/host_SN.npz'):
        sealed(D03 / name, candidate['files'][name]['sha256'])
    spec = importlib.util.spec_from_file_location('d03_reader', D03 / 'd03.py')
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    rd = sealed(CF4 / 'ReadMe', CF4_SHA['ReadMe']).decode('ascii')
    sealed(CF4 / 'table2.dat', CF4_SHA['table2.dat'])
    galaxies = reader.table(CF4 / 'table2.dat', reader.schema(rd, 'table2.dat'), 'PGC', 55877)
    with (D03 / 'results/OBJECT_GRAPH.csv').open() as stream:
        graph = list(csv.DictReader(stream))
    matched = [r for r in graph if r['association_status'] == 'unique_host_coordinate_and_redshift']
    ids = sorted({int(r['PGC']) for r in matched})
    if len(graph) != 1701 or len(matched) != 654 or len(ids) != 494:
        raise ValueError('frozen D03 matched support changed')
    return galaxies, matched, ids, candidate


def run():
    receipts = json.loads((HERE / 'ACQUISITION_RECEIPT.json').read_text())
    for name, meta in receipts.items():
        sealed(RAW / name, meta['sha256'])
    page = (RAW / 'cosmicflows.html').read_text(encoding='iso-8859-1')
    script = (RAW / 'retrieve_CF4pp_grid_values.py').read_text()
    if 'multiply by 52' not in page or 'SGZ,SGY,SGX' not in page.replace(' ', ''):
        raise ValueError('grouped source convention unavailable')
    if 'Oct 13th, 2026' not in script or 'Oct 13th 2026' not in page:
        raise ValueError('corrected-release source qualification missing')
    for text in ['N=128,L=1000', 'distance *= clight/100', 'distance /= 100',
                 'd_data[ix,iy,iz]', 'vr_data[ix,iy,iz]', "frame='fk5',equinox='J2000.000'"]:
        if text not in script:
            raise ValueError('author query convention changed: ' + text)
    v = np.asarray(fits.getdata(RAW / 'CF4gp_new_64-z008_velocity.fits'), float)
    rms = np.asarray(fits.getdata(RAW / 'CF4gp_new_64-z008_velocity_cube_error.fits'), float)
    if v.shape != (3, 64, 64, 64) or rms.shape != (64, 64, 64):
        raise ValueError('grouped source shape changed')
    grouped = {'velocity_raw': summary(v), 'velocity_times52_kms': summary(52 * v),
               'scalar_error_raw': summary(rms), 'scalar_error_times52_kms': summary(52 * rms),
               'header_keys': list(fits.getheader(RAW / 'CF4gp_new_64-z008_velocity.fits').keys()),
               'spatial_order_source': '(SGZ,SGY,SGX)',
               'query_status': 'HOLD: no WCS, grid origin/spacing or component-order contract in FITS/page; scalar RMS not a radial/component covariance',
               'not_applied': 'Do not copy the distinct CF4++ 128-grid geometry into this64-grid product.'}
    new_name = 'new_CF4pp_mean_std_grids.npz'
    if parsedate_to_datetime(receipts[new_name]['last_modified']).date().isoformat() < '2026-10-13':
        raise ValueError('corrected source Last-Modified predates erratum')
    with np.load(RAW / new_name, allow_pickle=False) as grid:
        field_summary = {name: summary(grid[name]) for name in grid.files}
        if set(grid.files) != {'d_mean', 'd_std', 'vr_mean', 'vr_std', 'v_mean', 'v_std', 'N'}:
            raise ValueError('corrected archive schema differs from inspected seven-key release')
        metadata_N = int(grid['N'])
        vr, sr = grid['vr_mean'].copy(), grid['vr_std'].copy()
        vxyz = grid['v_mean'].copy()
        with np.load(RAW / 'CF4pp_mean_std_grids.npz', allow_pickle=False) as old_grid:
            revision = {name: {'old_key': name + '_CF4pp',
                              'exact_array_equal': bool(np.array_equal(grid[name], old_grid[name + '_CF4pp'])),
                              'new_minus_old': summary(grid[name] - old_grid[name + '_CF4pp'])}
                        for name in ('d_mean', 'd_std', 'vr_mean', 'vr_std', 'v_mean', 'v_std')}
    if vr.shape != (N, N, N) or sr.shape != vr.shape or vxyz.shape != (3, N, N, N):
        raise ValueError('CF4++ shape contract changed')
    if not np.isfinite(vr).all() or not np.isfinite(sr).all() or (sr < 0).any():
        raise ValueError('missing or negative radial uncertainty source values')
    # This is a semantic diagnostic, not an inferred axis relabelling. Test the
    # declared XYZ ordering at source voxel centers and retain actual mismatch.
    axis = -L / 2 + (np.arange(N) + .5) * DELTA
    mesh = np.meshgrid(axis, axis, axis, indexing='ij', sparse=True)
    radius = np.sqrt(sum(a * a for a in mesh))
    reconstructed = sum(vxyz[i] * mesh[i] / radius for i in range(3))
    projection = summary(vr - reconstructed)
    if np.max(np.abs(vr - reconstructed)) > 1e-9:
        raise ValueError('corrected radial field disagrees with declared XYZ voxel-center projection')
    del vxyz, reconstructed
    galaxies, links, pgcs, candidate = load_d03()
    rows = [galaxies[p] for p in pgcs]
    velocities = np.array([g['Vcmb'] for g in rows], float)
    ra, dec = np.array([g['RAdeg'] for g in rows]), np.array([g['DEdeg'] for g in rows])
    xyz, direction = sg_positions(ra, dec, velocities)
    gal = SkyCoord(ra=ra * u.deg, dec=dec * u.deg, frame='fk5', equinox='J2000.000').galactic
    manual = manual_supergalactic_from_galactic(gal.l.deg, gal.b.deg)
    transform_error = float(np.max(np.abs(manual - direction)))
    if transform_error > 2e-14:
        raise ValueError('independent SG basis check failed')
    mean, inside, indices = query(vr, xyz)
    std, _, _ = query(sr, xyz)
    valid_radius = velocities > 0
    mean[~valid_radius], std[~valid_radius] = np.nan, np.nan
    shifts, defined = redshift_proxy_shift(velocities, mean)
    shift_high_u, high_defined = redshift_proxy_shift(velocities, mean + std)
    shift_low_u, low_defined = redshift_proxy_shift(velocities, mean - std)
    host_ledger = []
    by_pgc = {}
    for i, pgc in enumerate(pgcs):
        item = {'PGC': pgc, 'CF4_group': rows[i]['1PGC'], 'host_RA_J2000': float(ra[i]), 'host_DEC_J2000': float(dec[i]),
                'CF4_Vcmb_kms': float(velocities[i]), 'SGX': float(xyz[i, 0]), 'SGY': float(xyz[i, 1]), 'SGZ': float(xyz[i, 2]),
                'ix': int(indices[i, 0]), 'iy': int(indices[i, 1]), 'iz': int(indices[i, 2]),
                'query_status': 'VALID_SOURCE_CELL' if inside[i] and valid_radius[i] else 'UNKNOWN_POSITION',
                'vr_mean_kms': None if not np.isfinite(mean[i]) else float(mean[i]),
                'vr_rms_kms': None if not np.isfinite(std[i]) else float(std[i]),
                'proxy_delta_mu': float(shifts[i]) if defined[i] else None,
                'proxy_mean_plus_rms_delta_mu': float(shift_high_u[i]) if high_defined[i] else None,
                'proxy_mean_minus_rms_delta_mu': float(shift_low_u[i]) if low_defined[i] else None}
        host_ledger.append(item)
        by_pgc[pgc] = i
    alt_xyz, _ = sg_positions([float(r['RA']) for r in links], [float(r['DEC']) for r in links], [float(r['zCMB']) * C for r in links])
    # Alternative uses SN positions and Pantheon zCMB only to expose query input
    # sensitivity; no claim that it equals the host's physical location.
    alt_mean, alt_inside, alt_indices = query(vr, alt_xyz)
    primary_for_link = np.array([mean[by_pgc[int(r['PGC'])]] for r in links])
    primary_indices = np.array([indices[by_pgc[int(r['PGC'])]] for r in links])
    host_csv = RAW / 'D03_HOST_FLOW_QUERIES.csv'
    with host_csv.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(host_ledger[0]))
        writer.writeheader()
        writer.writerows(host_ledger)
    output = {'schema': 'htt.d06_flow_control/1', 'owner': 'htt', 'claim_tier': 'DIAGNOSTIC_ONLY',
              'artifact_mode': 'NON_CLAIM_BEARING_EXPLORATORY', 'transfer_source': 'empirical_proxy',
              'scope': 'dependent CF4 reconstruction source validation and actual D03 matched-host queries',
              'allowed_use': 'source-dependent redshift-space query and algebraic H100 proxy sensitivity',
              'null_status': 'not a null test', 'covariance_status': 'RMS fields only; no HMC draws or joint covariance',
              'forbidden_uses': ['independent CF4 validation', 'physical luminosity-distance correction', 'confidence coverage', 'original node admission'],
              'sources': receipts, 'D03_candidate_digest': D03_DIGEST,
              'D03_consumed_source_sha': {name: candidate['files'][name]['sha256'] for name in ('d03.py', 'results/OBJECT_GRAPH.csv', 'results/host_SN.npz')},
              'CF4_sources': CF4_SHA, 'grouped_validation': grouped,
              'CF4pp_field_inventory': field_summary, 'CF4pp_radial_minus_center_vector_projection_kms': projection,
              'CF4pp_scalar_N': {'value': metadata_N, 'semantics': 'NOT_PROVIDED_BY_QUERY_SCRIPT; not used as spatial resolution'},
              'CF4pp_old_vs_corrected_arrays': revision,
              'source_resolution': {'page_href': 'CF4pp_mean_std_grids.npz (stale May2025 file)',
                                    'author_script_filename': new_name,
                                    'corrected_source': 'official script-named file, Last-Modified Oct13 2026, distinct167773886bytes',
                                    'schema_change': 'corrected keys d_mean,d_std,vr_mean,vr_std,v_mean,v_std,N; official script still expects old _CF4pp suffixes; explicit six-field mapping used only for revision comparison',
                                    'old_linked_file_status': 'NOT_QUALIFIED_AS_CORRECTED_RADIAL_INPUT; first numeric outputs retained in STALE_LINKED_NPZ_DIAGNOSTIC.json',
                                    'first_linked_generator_sha256': sha(RAW / 'FIRST_LINKED_NPZ_GENERATOR.py'),
                                    'first_linked_host_ledger_sha256': sha(RAW / 'STALE_LINKED_NPZ_HOST_QUERIES.csv')},
              'coordinate_policy': {'grid': '1000h^-1Mpc;128 cells;[-500,500);delta7.8125; spatialXYZ per current author script',
                                    'position': 'CF4 host FK5/J2000 direction at radius Vcmb/100 h^-1Mpc; redshift-space lookup only',
                                    'lookup': 'exact-edge half-open voxel query; strict bounds, no clipping, no periodic wrap',
                                    'velocity': 'CF4++ released km/s; no grouped52factor applied to CF4++',
                                    'independent_manual_SG_basis_max_abs_error': transform_error},
              'matched_support': {'D03_rows': len(links), 'unique_host_PGCs': len(pgcs),
                                  'unique_groups': len({g['1PGC'] for g in rows}),
                                  'valid_host_positions': int((inside & valid_radius).sum()),
                                  'outside_host_positions': int((~inside).sum()), 'nonpositive_host_radius': int((~valid_radius).sum()),
                                  'host_query_status': dict(Counter(r['query_status'] for r in host_ledger)),
                                  'unique_source_cells': len({tuple(row) for row in indices[inside & valid_radius]})},
              'host_flow': {'radial_mean_kms': summary(mean), 'radial_rms_kms': summary(std),
                            'radial_mean_over_CMB_velocity': summary(mean / velocities),
                            'exact_algebraic_H100_proxy_shift_mag': summary(shifts),
                            'mean_plus_RMS_proxy_shift_mag': summary(shift_high_u),
                            'mean_minus_RMS_proxy_shift_mag': summary(shift_low_u),
                            'all_mean_plus_minus_RMS_proxy_defined': int((defined & high_defined & low_defined).sum())},
              'alternate_Pantheon_SN_query_input_sensitivity': {'rows': len(links), 'valid_positions': int(alt_inside.sum()),
                                                               'different_cells_from_host_query': int(np.any(alt_indices != primary_indices, axis=1).sum()),
                                                               'radial_mean_difference_kms': summary(alt_mean - primary_for_link)},
              'proxy_definition': '5log10((cz-u)/cz); exact algebraic sensitivity of chosen H100 redshift proxy; neither physical dL correction nor finite-z/flow remainder bound',
              'RMS_envelope': 'mean±released radial RMS is a chosen pointwise sensitivity, not a confidence interval or joint realization envelope',
              'host_ledger': {'path': str(host_csv), 'rows': len(host_ledger), 'sha256': sha(host_csv)},
              'scientific_status': 'Original H02/H04/S02/S04/K04 HOLD unchanged; source reconstruction depends on CF4 data',
              'runtime': {'requested': 'Sol/high', 'requested_exact_model': 'UNVERIFIED: original accepted spawn settings unavailable in worker context',
                          'observed': 'UNKNOWN', 'python': sys.version, 'threads': 2},
              'generator_sha256': sha(Path(__file__)),
              'caveats': ['No grouped-grid position query: its missing geometry cannot be borrowed from CF4++.',
                          'Means/RMS are not HMC samples or interobject covariance; repeated host/group/cells are dependent.',
                          'Redshift-space positions are the author lookup convention, not inferred true comoving locations.',
                          'D03 same-host CF4 SN aggregates and reconstruction share CF4 calibration/data; no independent validation.',
                          'Mean±RMS pointwise scenarios have no simultaneous coverage qualification.']}
    (HERE / 'D06_RESULT.json').write_text(json.dumps(output, indent=2, allow_nan=False) + '\n')
    plot(host_ledger)
    print(json.dumps({'support': output['matched_support'], 'host_flow': output['host_flow'],
                      'coordinate_check': transform_error, 'projection_check': projection,
                      'alternate': output['alternate_Pantheon_SN_query_input_sensitivity']}, indent=2))
    return output


def plot(rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    valid = [r for r in rows if r['vr_mean_kms'] is not None]
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.5))
    x = [r['CF4_Vcmb_kms'] / 100 for r in valid]
    y = [r['vr_mean_kms'] for r in valid]
    c = [r['vr_rms_kms'] for r in valid]
    sc = axes[0].scatter(x, y, c=c, s=15, cmap='viridis')
    axes[0].axhline(0, color='gray', linewidth=.7)
    axes[0].set(xlabel='CF4 host CMB velocity /100 (h^-1 Mpc proxy)', ylabel='Released radial mean (km/s)')
    fig.colorbar(sc, ax=axes[0], label='Released radial RMS (km/s)')
    good = [r for r in valid if r['proxy_delta_mu'] is not None]
    axes[1].scatter([r['CF4_Vcmb_kms'] for r in good], [r['proxy_delta_mu'] for r in good], s=15, alpha=.7)
    axes[1].axhline(0, color='gray', linewidth=.7)
    axes[1].set(xlabel='CF4 host CMB velocity (km/s)', ylabel='5 log10[(cz-u)/cz] (proxy mag)')
    fig.suptitle('Dependent corrected CF4++ control at actual D03 matched hosts')
    fig.text(.02, .01, 'HTT | DIAGNOSTIC_ONLY | empirical_proxy | means/RMS, no joint covariance/null | no physical dL correction', fontsize=8)
    fig.tight_layout(rect=(0, .05, 1, .94))
    for extension in ('png', 'pdf'):
        fig.savefig(HERE / f'D06_HOST_FLOW.{extension}', dpi=170)
    plt.close(fig)


if __name__ == '__main__':
    run()
