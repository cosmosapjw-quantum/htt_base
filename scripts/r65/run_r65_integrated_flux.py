"""Bounded R8 actual integrated-flux repair with same-source overlap retained."""
from __future__ import annotations

import json
from pathlib import Path
import sys
import time

import healpy as hp
import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_r65_counts import analyze, build_geometry, digest, jsonable, write_json
from htt.htt.infer.r65_count_quotient import shared_maps
from htt.htt.infer.r65_overlap import common_influences, source_overlap_sandwich

P = Path('docs/research_program/observational_publication_20261015/R65_DIPOLE_ANOMALY_20261117')
RAW = Path('/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/RACS_SBI_20261117/Full_NVSS_combined_named.dat')
EXPECTED_SHA = '52eb576c1e3e71837f2fca26121789ccc0b316152cca3f25ea2f37ea8ef5a38e'


def main():
    started = time.time()
    sha = digest(RAW)
    if sha != EXPECTED_SHA:
        raise ValueError('provider catalogue SHA256 mismatch')
    table = pd.read_csv(RAW, sep=r'\s+', quotechar='"')
    required = ['source_name', 'ra', 'dec', 'integrated_flux', 'integrated_flux_unc', 'peak_flux', 'peak_flux_unc']
    if table.columns.tolist() != required:
        raise ValueError('provider catalogue schema differs from pinned source')
    ra, dec = table.ra.to_numpy(float), table.dec.to_numpy(float)
    peak, total = table.peak_flux.to_numpy(float), table.integrated_flux.to_numpy(float)
    valid = np.isfinite(ra) & np.isfinite(dec) & np.isfinite(peak) & np.isfinite(total)
    valid &= (ra >= 0) & (ra < 360) & (dec >= -90) & (dec <= 90) & (peak > 0) & (total > 0)
    source = dict(path=str(RAW), sha256=sha, bytes=RAW.stat().st_size,
                  release='https://github.com/o-oayda/cracking-into-racs-i/releases/tag/v1.0.0',
                  original_rows=len(table), finite_positive_paired_rows=int(valid.sum()),
                  duplicate_source_names=int(table.source_name.duplicated().sum()),
                  columns=required, integrated_flux_unit='mJy (provider Figure2 implementation contract)',
                  peak_flux_unit='mJy/beam (provider component peak; distinct from raw FITS peak)',
                  original_extraction_replay=False,
                  object_definition='Gaussian catalogue component; not necessarily one entire physical galaxy')
    ra, dec, peak, total = ra[valid], dec[valid], peak[valid], total[valid]
    result = dict(schema='htt.r65.integrated_flux_refinement/1', source=source, models={}, geometries={},
                  role='R8 bounded source-qualification refinement; original raw-peak experiment retained',
                  physical_LSS_calibrated=False, publication_status='NOT_READY_TO_SUBMIT')
    data, objects, geometries = {}, {}, {}
    for field, flux in [('provider_peak', peak), ('provider_integrated', total)]:
        geometry = build_geometry(64, 10, False, ra, dec, flux/1000.)
        geometries[field] = geometry
        result['geometries'][field] = {k: v for k, v in geometry.items()
                                       if k not in ('pixel_indices', 'pixel_vectors', 'features', 'groups', 'counts')}
        data[field+'_counts'] = geometry['counts']
        for quad in [False, True]:
            suffix = '_dipole_stf' if quad else '_dipole'
            model, experiments = analyze(geometry, quad)
            for response in model['conditional_peak_response_diagnostics'].values():
                response['meaning'] = ('ideal integrated-component flux response with alpha fixed; parent peak-detection, spectral distribution and component selection remain conditional'
                                       if field == 'provider_integrated' else
                                       'provider peak-selected unresolved-source proxy; not a physical speed measurement')
            model['five_views']['x']['selection_field'] = field
            model['five_views']['x']['exact_carrier'] = 'PROVIDER_NVSS_CARRIERS.npz'
            model['five_views']['G_F']['path_coordinate'] = ('integrated-component flux bins in mJy' if field == 'provider_integrated' else 'provider peak-intensity bins in mJy/beam')
            result['models'][field+suffix] = model
            objects[field+suffix] = experiments
            print(field+suffix, 'N=', geometry['observed_counts_per_bin'].tolist(),
                  'common_u=', model['common_transverse_fit']['estimate'][:2].tolist(), flush=True)
    leftgeo, rightgeo = geometries['provider_peak'], geometries['provider_integrated']
    assert np.array_equal(leftgeo['pixel_indices'], rightgeo['pixel_indices'])
    nside, npix = 64, hp.nside2npix(64)
    pix = hp.ang2pix(nside, ra, dec, lonlat=True, nest=False)
    peakbin = np.searchsorted([20, 40, 80], peak, side='right')
    totalbin = np.searchsorted([20, 40, 80], total, side='right')
    joint = np.bincount((4*peakbin+totalbin)*npix+pix, minlength=16*npix).reshape(4, 4, npix)
    joint = joint[:, :, leftgeo['pixel_indices']]
    data.update(joint_bin_pixel_counts=joint, pixel_indices=leftgeo['pixel_indices'],
                features=leftgeo['features'], groups=leftgeo['groups'])
    np.savez_compressed(P/'RESULTS/PROVIDER_NVSS_CARRIERS.npz', **data)
    result['source_migration_counts_4x4'] = joint.sum(axis=2)
    result['migration_order'] = ['below20', '20to40', '40to80', '80plus']
    result['paired_comparisons'] = {}
    for quad in [False, True]:
        suffix = '_dipole_stf' if quad else '_dipole'
        left = result['models']['provider_peak'+suffix]
        right = result['models']['provider_integrated'+suffix]
        maps, _ = shared_maps(3, 6 if quad else 2)
        a = common_influences(objects['provider_peak'+suffix], left['common_transverse_fit'], maps)
        b = common_influences(objects['provider_integrated'+suffix], right['common_transverse_fit'], maps)
        covariance = source_overlap_sandwich(a, leftgeo['counts'], b, rightgeo['counts'], joint[1:, 1:])
        delta = np.asarray(right['common_transverse_fit']['estimate'][:2])-np.asarray(left['common_transverse_fit']['estimate'][:2])
        dcov = covariance['covariance_contrast']
        stat = float(delta@np.linalg.solve(dcov, delta))
        result['paired_comparisons'][suffix[1:]] = dict(
            integrated_minus_peak=delta, covariance=covariance,
            mean_contrast_convention='right minus left; covariance is unchanged by reversing both contrast signs',
            marginal_sd=np.sqrt(np.diag(dcov)),
            poisson_source_linearized_wald=stat, df=2,
            poisson_source_linearized_tail=float(stats.chi2.sf(stat, 2)),
            meaning='apparent common dipole difference between same-provider selections; does not isolate instrumental bias from population change',
            law='empirical independent-source Poisson influence/sandwich; shared components retained; LSS and source multiplicity uncalibrated')
    result['carrier_sha256'] = digest(P/'RESULTS/PROVIDER_NVSS_CARRIERS.npz')
    result['elapsed_seconds'] = time.time()-started
    write_json(P/'RESULTS/PROVIDER_NVSS_RESULT.json', result)
    print(json.dumps(jsonable(result['paired_comparisons']), indent=2), flush=True)
    print('R8 source refinement completed', result['elapsed_seconds'], flush=True)


if __name__ == '__main__':
    main()
