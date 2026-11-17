"""Execute the registered R65 NVSS conditional count experiments once."""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import time
from pathlib import Path

import healpy as hp
import numpy as np
from astropy import __version__ as astropy_version
from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as u
from scipy import linalg, stats

from htt.htt.infer.r65_count_quotient import (
    RingLikelihood, angular_features, finite_bin_response, fit_joint,
    gaussian_five_views, nested_lr, shared_maps,
)

RAW = Path('/mnt/extdrive/workdir/raw/new_acquisitions/radio_hi/NVSS_nrao_20261110/CATALOG.FIT')
DEFAULT_OUT = Path('docs/research_program/observational_publication_20261015/R65_DIPOLE_ANOMALY_20261117/RESULTS')
BOUNDS = np.array([.020, .040, .080, np.inf])
FEATURES = ['ux', 'uy', 'STF_xx_minus_yy', 'STF_xy', 'STF_xz', 'STF_yz']
SPEED_CMB = 369.82
C_KM_S = 299792.458
CMB_RA_DEG, CMB_DEC_DEG = 167.942, -6.944


def jsonable(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, dict):
        return {k: jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    return x


def write_json(path, data):
    path.write_text(json.dumps(jsonable(data), indent=2, ensure_ascii=False,
                               allow_nan=False)+'\n')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while b := f.read(1048576):
            h.update(b)
    return h.hexdigest()


def cmb_direction():
    ra, dec = np.deg2rad([CMB_RA_DEG, CMB_DEC_DEG])
    return np.array([np.cos(dec)*np.cos(ra), np.cos(dec)*np.sin(ra), np.sin(dec)])


def build_geometry(nside, bcut, clean, ra, dec, peak):
    pixels = np.arange(hp.nside2npix(nside))
    vectors = np.column_stack(hp.pix2vec(nside, pixels, nest=False))
    lon, lat = hp.pix2ang(nside, pixels, lonlat=True, nest=False)
    galb = SkyCoord(ra=lon*u.deg, dec=lat*u.deg, frame='icrs').galactic.b.deg
    mask = (lat > -37) & (np.abs(galb) > bcut)
    if clean:
        for r0, r1, d0, d1 in [(82, 90, -7, -1), (49, 52, -39, -36), (185, 189, 11, 14)]:
            mask &= ~((lon > r0) & (lon < r1) & (lat > d0) & (lat < d1))
        bright = np.flatnonzero(peak >= 2.5)
        for j in bright:
            v = hp.ang2vec(ra[j], dec[j], lonlat=True)
            at = hp.query_disc(nside, v, np.deg2rad(.3), inclusive=True, fact=4, nest=False)
            mask[at] = False
    objpix = hp.ang2pix(nside, ra, dec, lonlat=True, nest=False)
    kept = np.flatnonzero(mask)
    counts = np.array([np.bincount(objpix[(peak >= low) & (peak < high)], minlength=len(pixels))[kept]
                       for low, high in zip(BOUNDS[:-1], BOUNDS[1:])])
    ring = hp.pix2ring(nside, kept, nest=False).astype(int)
    fv = angular_features(vectors[kept], True)
    # Fixed symmetric log windows estimate the population boundary density;
    # this is not a source-size or spectral-response calibration.
    log_half_width = .10
    boundary = [int(np.count_nonzero(mask[objpix] &
                   (peak >= edge*np.exp(-log_half_width)) &
                   (peak < edge*np.exp(log_half_width))))/(2*log_half_width)
                for edge in BOUNDS[:-1]]+[0.]
    return dict(nside=nside, galactic_latitude_cut_deg=bcut, clean_bright_boxes=clean,
                pixel_indices=kept, pixel_vectors=vectors[kept], features=fv, groups=ring,
                counts=counts, boundary_log_density=np.array(boundary),
                boundary_log_half_width=log_half_width,
                mask_sha256=hashlib.sha256(mask.astype(np.uint8).tobytes()).hexdigest(),
                retained_pixels=len(kept), retained_rings=len(np.unique(ring)),
                sky_fraction=float(mask.mean()), observed_counts_per_bin=counts.sum(axis=1))


def response_fits(experiments, full_ll, responses, nfeatures):
    result = {}
    for alpha, response in responses.items():
        maps, offsets = shared_maps(len(experiments), nfeatures, response)
        fitted = fit_joint(experiments, maps, offsets)
        if nfeatures > 2:
            fixedmaps, fixedoffsets = shared_maps(len(experiments), nfeatures, response,
                                                 fixed_dipole=SPEED_CMB/C_KM_S*cmb_direction()[:2])
            fixedfit = fit_joint(experiments, fixedmaps, fixedoffsets)
            fixed_ll = fixedfit['log_likelihood_relative_zero']
        else:
            fixed_ll = sum(e.evaluate(k*SPEED_CMB/C_KM_S*cmb_direction()[:2])[0]
                           for e, k in zip(experiments, response))
        result[alpha] = dict(
            response=response, shared_peak_proxy_beta_fit=fitted,
            independent_vs_shared=nested_lr(full_ll, fitted['log_likelihood_relative_zero'], 4),
            independent_vs_fixed_cmb=nested_lr(full_ll, fixed_ll, 6),
            meaning='conditional unresolved-source peak-intensity proxy, not a physical speed measurement',
            response_uncertainty='boundary estimate and alpha held fixed in this working comparison',
            same_u_vs_shared_beta='nonnested; no Wilks calibration of their likelihood difference')
    return result


def analyze(geometry, quadrupole):
    p = 6 if quadrupole else 2
    experiments = [RingLikelihood(y, geometry['features'][:, :p], geometry['groups'])
                   for y in geometry['counts']]
    fitted = [fit_joint([e]) for e in experiments]
    full_ll = sum(f['log_likelihood_relative_zero'] for f in fitted)
    maps, offsets = shared_maps(3, p)
    common = fit_joint(experiments, maps, offsets)
    common_lr = nested_lr(full_ll, common['log_likelihood_relative_zero'], 4)
    estimates = np.concatenate([f['estimate'] for f in fitted])
    covariance = linalg.block_diag(*[f['covariance'] for f in fitted])
    dipole_indices = np.concatenate([np.arange(b*p, b*p+2) for b in range(3)])
    dipoles = estimates[dipole_indices]
    dipcov = covariance[np.ix_(dipole_indices, dipole_indices)]
    views = gaussian_five_views(dipoles, dipcov)
    views['x'].update(joint_vector_stf_levels=estimates, joint_vector_stf_covariance=covariance,
                      feature_order=FEATURES[:p], exact_carrier='NVSS_CONDITIONAL_CARRIERS.npz')
    views['x']['cross_bin_covariance'] = 'zero only in this conditional independent-multinomial working law; LSS not supplied'
    score_baseline = []
    for e, f in zip(experiments, fitted):
        _, score0, j0, _ = e.evaluate(np.zeros(p))
        one = linalg.solve(j0, score0, assume_a='pos')
        delta = one-f['estimate']
        result = dict(estimate=one, full_covariance=linalg.inv(j0),
                      difference_to_exact=delta,
                      squared_shift_in_fitted_information=float(delta@f['precision']@delta),
                      baseline='one-step Fisher score with the identical ring nuisance and angular support')
        if p == 6:
            cfixed = linalg.inv(f['precision'][:2, :2])
            result['dipole_sd_inflation_from_free_STF'] = np.sqrt(np.diag(f['covariance'])[:2]/np.diag(cfixed))
            corr = f['covariance']/np.sqrt(np.outer(np.diag(f['covariance']), np.diag(f['covariance'])))
            result['maximum_absolute_dipole_STF_correlation'] = float(np.max(np.abs(corr[:2, 2:])))
        score_baseline.append(result)
    alpha_responses = {str(a): finite_bin_response(geometry['observed_counts_per_bin'],
                                                   geometry['boundary_log_density'], a)
                       for a in [.5, .75, 1.]}
    conditional_response = response_fits(experiments, full_ll, alpha_responses, p)
    # Keep the full correlated path. A diagonal-path ablation changes its law.
    path = views['G_F']['signed_path']
    pc = views['G_F']['full_path_covariance']
    full_wald = float(dipoles@np.linalg.solve(dipcov, dipoles))
    path_wald = float(path@np.linalg.solve(pc, path))
    diagonal_path = float(np.sum(path*path/np.diag(pc)))
    m = dict(n_features_per_bin=p, features=FEATURES[:p], independent_fits=fitted,
             common_transverse_fit=common, common_vector_lr=common_lr,
             full_log_likelihood_relative_zero=full_ll,
             five_views=views, matched_score_baseline=score_baseline,
             conditional_peak_response_diagnostics=conditional_response,
             path_information=dict(original_wald=full_wald, retained_path_wald=path_wald,
                                   incorrect_diagonal_path_wald=diagonal_path,
                                   diagonal_path_is_different_experiment=True),
             exact_omitted_axial_dipole='unidentified in the discrete loglinear ring quotient',
             exact_omitted_axisymmetric_STF='unidentified in the discrete loglinear ring quotient',
             observation_scope='apparent log-count morphology, no global tilt/Bianchi inference')
    return m, experiments


def bootstrap_common(experiments, observed, nsim, seed, output):
    rng = np.random.default_rng(seed)
    p = experiments[0].features.shape[1]
    maps, offsets = shared_maps(3, p)
    truth = observed['common_transverse_fit']['per_experiment_estimates']
    values = np.empty(nsim)
    for j in range(nsim):
        simulated = [e.simulate(t, rng) for e, t in zip(experiments, truth)]
        free_ll = sum(fit_joint([e])['log_likelihood_relative_zero'] for e in simulated)
        common = fit_joint(simulated, maps, offsets,
                           start=observed['common_transverse_fit']['estimate'])
        values[j] = nested_lr(free_ll, common['log_likelihood_relative_zero'], 4)['statistic']
        if (j+1) % 64 == 0:
            print(f'conditional bootstrap {j+1}/{nsim}', flush=True)
    stat = observed['common_vector_lr']['statistic']
    exceed = int(np.count_nonzero(values >= stat))
    np.savez_compressed(output/'CONDITIONAL_BOOTSTRAP_DRAWS.npz', lr=values)
    return dict(nsim=nsim, seed=seed, exceedances=exceed, observed_lr=stat,
                fitted_null_mc_tail=(exceed+1)/(nsim+1),
                resolution=1/(nsim+1), quantiles=np.quantile(values, [.5, .9, .95, .99]),
                chi2_df4_quantiles=stats.chi2.ppf([.5, .9, .95, .99], 4),
                law='parametric conditional multinomial bootstrap with fitted common dipole and per-bin STF nuisance',
                physical_LSS_calibrated=False, exact_finite_sample_composite_test=False,
                scan_correction='primary prespecified geometry/model only; no best-cut selection')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    parser.add_argument('--bootstrap', type=int, default=512)
    args = parser.parse_args()
    if args.bootstrap < 1:
        raise ValueError('positive registered bootstrap size required')
    args.out.mkdir(parents=True, exist_ok=True)
    start = time.time()
    with fits.open(RAW, memmap=True) as hdul:
        table = hdul[1]
        field_unit = table.columns['PEAK INT'].unit
        if field_unit.strip().upper() != 'JY/BEAM':
            raise ValueError(f'peak field source unit changed: {field_unit}')
        ra = np.array(table.data['RA(2000)'], dtype=float)
        dec = np.array(table.data['DEC(2000)'], dtype=float)
        peak = np.array(table.data['PEAK INT'], dtype=float)
    valid = np.isfinite(ra) & np.isfinite(dec) & np.isfinite(peak)
    valid &= (ra >= 0) & (ra < 360) & (dec >= -90) & (dec <= 90) & (peak > 0)
    original_n = len(ra)
    ra, dec, peak = ra[valid], dec[valid], peak[valid]
    result = dict(schema='htt.r65.nvss_count_quotient/1', baseline_commit='d76ef3a4e9b33c4703a02647b3aa850004d04253',
                  source=dict(path=str(RAW), sha256=digest(RAW), bytes=RAW.stat().st_size,
                              original_rows=original_n, finite_positive_rows=len(ra),
                              field='PEAK INT', field_unit=field_unit,
                              bin_edges_mjy_per_beam=[20, 40, 80, 'infinity']),
                  conventions=dict(frame='ICRS/J2000', n='sourceward', metric_signature='(-+++)',
                                   c_km_s=C_KM_S, CMB_speed_km_s=SPEED_CMB,
                                   CMB_ra_dec_deg=[CMB_RA_DEG, CMB_DEC_DEG],
                                   mask='pixel-centre selection, whole-pixel bright-disc rejection'),
                  runtime=dict(python=platform.python_version(), numpy=np.__version__,
                               healpy=hp.__version__, astropy=astropy_version),
                  geometries={}, models={}, status='OBSERVED_CONDITIONAL_ANALYSIS',
                  physical_LSS_calibrated=False, publication_status='NOT_READY_TO_SUBMIT')
    carriers = {}
    primary_experiments = None
    specifications = [('base64', 64, 10, False), ('base32', 32, 10, False),
                      ('gal20', 64, 20, False), ('clean64', 64, 10, True)]
    for name, nside, bcut, clean in specifications:
        geometry = build_geometry(nside, bcut, clean, ra, dec, peak)
        result['geometries'][name] = {k: v for k, v in geometry.items()
                                      if k not in ('pixel_indices', 'pixel_vectors', 'features', 'groups', 'counts')}
        for key in ('pixel_indices', 'pixel_vectors', 'features', 'groups', 'counts'):
            carriers[name+'_'+key] = geometry[key]
        for quadrupole in [False, True]:
            model_id = name+('_dipole_stf' if quadrupole else '_dipole')
            model, experiments = analyze(geometry, quadrupole)
            result['models'][model_id] = model
            if model_id == 'base64_dipole_stf':
                primary_experiments = experiments
            print(model_id, 'N=', geometry['observed_counts_per_bin'].tolist(),
                  'u=', [f['estimate'][:2].tolist() for f in model['independent_fits']],
                  'common LR=', model['common_vector_lr'], flush=True)
    np.savez_compressed(args.out/'NVSS_CONDITIONAL_CARRIERS.npz', **carriers)
    # Checkpoint observed fits before finite conditional calibration.
    write_json(args.out/'NVSS_OBSERVED_RESULT.json', result)
    primary = result['models']['base64_dipole_stf']
    result['primary_common_vector_bootstrap'] = bootstrap_common(
        primary_experiments, primary, args.bootstrap, 2026111765, args.out)
    result['elapsed_seconds'] = time.time()-start
    result['carrier_sha256'] = digest(args.out/'NVSS_CONDITIONAL_CARRIERS.npz')
    result['bootstrap_sha256'] = digest(args.out/'CONDITIONAL_BOOTSTRAP_DRAWS.npz')
    write_json(args.out/'NVSS_OBSERVED_RESULT.json', result)
    print('completed', len(result['models']), 'observed models;', args.bootstrap,
          'conditional bootstrap catalogues;', round(result['elapsed_seconds'], 2), 'seconds', flush=True)


if __name__ == '__main__':
    main()
