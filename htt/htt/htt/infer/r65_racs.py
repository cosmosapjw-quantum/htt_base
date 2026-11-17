"""Weighted, source-conditional RACS SBI posterior vector pushforward.

The CSV weights are the original nested posterior weights. Population moments
and inverse weighted empirical-CDF quantiles describe that posterior measure;
ESS=1/sum(w**2) is a weight-concentration descriptor, not independent sample N.
No likelihood, Bayes factor, frequentist p-value, or joint NVSS law is created.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import zipfile
import platform
import importlib.util
import astropy

import numpy as np
import yaml
from astropy.coordinates import SkyCoord
import astropy.units as u

SPEED_KM_S = 369.82
C_KM_S = 299792.458
OUTER_SHA256 = '143cdcf32d85479ee171c8d5bc5da814178dd7123024ba12e5b5d9f9b9c94fc7'
SOURCE_COMMIT = 'f34f948752d2b6ceb8e2a0fdfb12a337f3c261bf'
SOURCE_REPOSITORY = 'https://github.com/o-oayda/sbi.git'
# v1.0.0 release child identities (observed archive names), checked against filenames and
# internal per-member manifests. No moving remote source is consulted at run time.
CHILD_HASHES = {
    'racs_low3_fiducial': '187a6cf51f2e01b2bb2a6dfdd25e3f674b03aaa843b082e1ecfdfa2091e2bb17',
    'racs_low3_noclus': '0658f579c6cb6ed16b5fe37c8772aa68794f1d948a8999e7dbdf0c488810d4d0',
    'racs_low3_notemp': '6ce751b560dda480e44b461932cfe1bc8561c62ad7d45f2a49f303f85f7000e3',
    'racs_mid1_fiducial': '98db5375948b2d0c372afee0643dda9c8f6a8ae7f7e24504cb91823d44685e3c',
    'racs_mid1_noclus': '67d0968c9a8b1bf42faf6b076735f6362ff55664117fec427988094d401b1108',
    'racs_mid1_notemp': '0d2ed7d09e60276d9879caaa06aaa72d95cd35519b82629787dbd62651d4e51e',
}
REQUIRED = ('observer_speed', 'dipole_longitude', 'dipole_latitude')


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_weights(weights):
    w = np.asarray(weights, dtype=float)
    if w.ndim != 1 or w.size == 0 or not np.isfinite(w).all() or np.any(w < 0):
        raise ValueError('weights must be a finite nonnegative nonempty vector')
    m = w.max()
    if m <= 0:
        raise ValueError('posterior weights have zero total mass')
    scaled = w / m
    return scaled / scaled.sum()


def read_posterior_csv(raw: bytes):
    """Read actual three-row anesthetic CSV without reweighting by logL.

    Zero-weight rows are retained. Unused logL_birth blanks are legitimate.
    Required and nuisance columns must be finite, including zero-weight rows.
    """
    rows = csv.reader(io.StringIO(raw.decode('utf-8-sig')))
    try:
        header, labels, weight_header = next(rows), next(rows), next(rows)
    except StopIteration as exc:
        raise ValueError('posterior CSV requires three header rows') from exc
    if len(header) < 5 or header[:2] != ['', '']:
        raise ValueError('unexpected CSV index/weight column header')
    if len(labels) != len(header) or labels[0] != 'labels':
        raise ValueError('unexpected CSV label header')
    if len(weight_header) != len(header) or weight_header[:2] != ['', 'weights']:
        raise ValueError('second CSV column is not original posterior weights')
    names = header[2:]
    if len(names) != len(set(names)) or not set(REQUIRED) <= set(names):
        raise ValueError('missing or duplicate posterior parameter columns')
    selected = [n for n in names if n in (*REQUIRED, 'temp_beta', 'lambda_clus', 'log10_n_initial_samples')]
    pos = [header.index(n) for n in selected]
    weights, values, indexes = [], [], []
    for line, row in enumerate(rows, 4):
        if not row:
            continue
        if len(row) != len(header):
            raise ValueError(f'CSV row {line} has wrong number of columns')
        try:
            indexes.append(int(row[0]))
            weights.append(float(row[1]))
            values.append([float(row[i]) for i in pos])
        except ValueError as exc:
            raise ValueError(f'invalid numeric data at CSV row {line}') from exc
    if len(set(indexes)) != len(indexes):
        raise ValueError('duplicate CSV row index')
    w = normalize_weights(weights)
    v = np.asarray(values, float)
    if not np.isfinite(v).all():
        raise ValueError('posterior parameters must be finite')
    cols = {name: v[:, i] for i, name in enumerate(selected)}
    if np.any(cols['observer_speed'] < 0):
        raise ValueError('negative radial observer speed')
    if np.any(np.abs(cols['dipole_latitude']) > 90):
        raise ValueError('Galactic latitude outside [-90,90] degrees')
    if np.any((cols['dipole_longitude'] < 0) | (cols['dipole_longitude'] > 360)):
        raise ValueError('Galactic longitude outside [0,360] degrees')
    return cols, w, {'header': header, 'label_row': labels, 'weight_header': weight_header,
                     'n_rows': len(w), 'n_zero_weights': int(np.sum(w == 0)),
                     'raw_weight_max': float(np.max(weights)),
                     'normalization': 'original nonnegative nested weights / their sum (stable scaling)',
                     'weights_sha256_float64_raw': sha256(np.asarray(weights, '<f8').tobytes())}


def weighted_moments(values, weights):
    x = np.asarray(values, dtype=float)
    w = normalize_weights(weights)
    if x.ndim == 1:
        x = x[:, None]
    if x.ndim != 2 or x.shape[0] != len(w) or not np.isfinite(x).all():
        raise ValueError('finite sample matrix must match weights')
    mean = w @ x
    r = x - mean
    cov = (r * w[:, None]).T @ r
    return mean, (cov + cov.T) / 2


def weighted_quantile(values, weights, probabilities):
    """Inverse weighted empirical CDF; no invented interpolation mass."""
    x = np.asarray(values, float)
    w = normalize_weights(weights)
    p = np.asarray(probabilities, float)
    if x.ndim != 1 or len(x) != len(w) or not np.isfinite(x).all():
        raise ValueError('finite scalar values must match weights')
    if not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError('quantile probabilities outside [0,1]')
    positive = w > 0
    order = np.argsort(x[positive], kind='stable')
    xp, wp = x[positive][order], w[positive][order]
    cdf = np.cumsum(wp)
    cdf[-1] = 1.0
    return xp[np.minimum(np.searchsorted(cdf, p, side='left'), len(xp) - 1)]


def scalar_summary(values, weights):
    mean, cov = weighted_moments(values, weights)
    q = weighted_quantile(values, weights, [.025, .16, .5, .84, .975])
    return {'mean': float(mean[0]), 'sd': float(np.sqrt(max(cov[0, 0], 0))),
            'median': float(q[2]), 'central68': q[[1, 3]].tolist(), 'central95': q[[0, 4]].tolist()}


def galactic_to_icrs_vectors(l_deg, b_deg, speed_km_s):
    l, b, speed = np.broadcast_arrays(np.asarray(l_deg, float), np.asarray(b_deg, float), np.asarray(speed_km_s, float))
    if not (np.isfinite(l).all() and np.isfinite(b).all() and np.isfinite(speed).all()):
        raise ValueError('nonfinite coordinate or speed')
    if np.any(np.abs(b) > 90) or np.any(speed < 0):
        raise ValueError('invalid latitude or negative speed')
    sky = SkyCoord(l=l*u.deg, b=b*u.deg, frame='galactic').icrs
    return np.asarray(sky.cartesian.xyz.value).T * speed[..., None]


def summarize_posterior(columns, weights, *, cmb_ra_deg=167.942, cmb_dec_deg=-6.944,
                        speed_normalizer=SPEED_KM_S):
    if not np.isfinite(speed_normalizer) or speed_normalizer <= 0:
        raise ValueError('speed normalizer must be positive')
    w = normalize_weights(weights)
    v = galactic_to_icrs_vectors(columns['dipole_longitude'], columns['dipole_latitude'],
                                speed_normalizer * columns['observer_speed'])
    if v.ndim != 2 or v.shape != (len(w), 3):
        raise ValueError('posterior vector sample shape mismatch')
    axis = np.asarray(SkyCoord(ra=cmb_ra_deg*u.deg, dec=cmb_dec_deg*u.deg, frame='icrs').cartesian.xyz.value)
    xy_axis = axis[:2]
    xy_norm = np.linalg.norm(xy_axis)
    if xy_norm < 1e-12:
        raise ValueError('CMB axis at ICRS pole has undefined transverse direction')
    parallel_xy = v[:, :2] @ (xy_axis/xy_norm)
    perp_xy = v[:, :2] @ np.array([-xy_axis[1], xy_axis[0]]) / xy_norm
    # A pure unit-CMB-speed vector yields ratio1 in BOTH this quotient and3D.
    parallel_ratio_xy = parallel_xy / (speed_normalizer * xy_norm)
    axis_ratio_3d = v @ axis / speed_normalizer
    mu, cov = weighted_moments(v, w)
    scalars = {'speed_ratio': columns['observer_speed'], 'speed_km_s': speed_normalizer*columns['observer_speed'],
               'icrs_x_km_s': v[:, 0], 'icrs_y_km_s': v[:, 1], 'icrs_z_km_s': v[:, 2],
               'transverse_norm_km_s': np.linalg.norm(v[:, :2], axis=1),
               'transverse_parallel_km_s': parallel_xy, 'transverse_perpendicular_km_s': perp_xy,
               'transverse_parallel_ratio_to_cmb': parallel_ratio_xy,
               'cmb_axis_parallel_ratio_3d': axis_ratio_3d,
               'cmb_axis_parallel_km_s_3d': v @ axis,
               'cmb_axis_perpendicular_norm_km_s_3d': np.linalg.norm(v - (v @ axis)[:,None]*axis[None,:],axis=1)}
    summaries = {k: scalar_summary(x, w) for k, x in scalars.items()}
    correlations = {}
    for name in ['temp_beta', 'lambda_clus']:
        if name in columns:
            y = columns[name]
            summaries[name] = scalar_summary(y, w)
            _, joint_cov = weighted_moments(np.column_stack([v, parallel_ratio_xy, y]), w)
            s = np.sqrt(np.maximum(np.diag(joint_cov), 0))
            correlations[name] = {
                k: (float(joint_cov[i, 4]/(s[i]*s[4])) if s[i] > 0 and s[4] > 0 else None)
                for i, k in enumerate(['icrs_x','icrs_y','icrs_z','transverse_parallel_ratio'])}
    return {'frame': 'ICRS Cartesian; sourceward directions transformed from Galactic using astropy SkyCoord',
            'units': 'km/s; covariance (km/s)^2; ratios dimensionless; temp_beta per degree C',
            'mean_velocity_icrs_km_s': mu.tolist(), 'covariance_velocity_icrs_km2_s2': cov.tolist(),
            'mean_transverse_icrs_xy_km_s': mu[:2].tolist(), 'covariance_transverse_icrs_xy_km2_s2': cov[:2,:2].tolist(),
            'cmb_axis': {'ra_deg':cmb_ra_deg,'dec_deg':cmb_dec_deg,'unit_icrs':axis.tolist(),
                         'speed_km_s':speed_normalizer,'xy_normalization':float(xy_norm)},
            'scalar_summaries': summaries,
            'posterior_probability_transverse_parallel_ratio_gt1': float(w[parallel_ratio_xy > 1].sum()),
            'probability_semantics':'source-conditional posterior probability, NOT a frequentist p-value',
            'nuisance_weighted_pearson_correlations': correlations,
            'weight_concentration_ess': float(1/(w@w)),
            'ess_semantics':'descriptive weight concentration, not independent sample size',
            'quantile_convention':'inverse weighted empirical CDF; central equal-tail68 and95 percent',
            'covariance_convention':'normalized posterior population covariance, no Bessel correction'}


def read_child_archive(raw, filename, *, expected_hash, experiment_id):
    """Verify child-byte/filename identity and every internal manifest member."""
    base = Path(filename).name
    match = re.fullmatch(r'(.+)\.([0-9a-f]{64})\.analysis\.zip', base)
    if not match or match.group(1) != experiment_id:
        raise ValueError('child filename/experiment mismatch')
    digest = sha256(raw)
    if digest != match.group(2) or digest != expected_hash:
        raise ValueError('child SHA256 differs from filename or pinned release identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError('duplicate ZIP member names')
        bad = z.testzip()
        if bad:
            raise ValueError(f'corrupt inner ZIP member {bad}')
        manifest_raw = z.read('artifact-manifest.yaml')
        manifest = yaml.safe_load(manifest_raw)
        if manifest['format_version'] != 3 or manifest['experiment_id'] != experiment_id:
            raise ValueError('manifest format/experiment mismatch')
        source = manifest['source']
        if source['repository'] != SOURCE_REPOSITORY or source['commit'] != SOURCE_COMMIT:
            raise ValueError('source repository or commit differs from source contract')
        records = manifest['files']
        if len({r['archive_path'] for r in records}) != len(records):
            raise ValueError('duplicate manifest member paths')
        member_hashes = {}
        verified = {}
        for rec in records:
            name = rec['archive_path']
            data = z.read(name)
            h = sha256(data)
            if len(data) != rec['size'] or h != rec['sha256']:
                raise ValueError(f'manifest member identity mismatch: {name}')
            member_hashes[name] = h
            verified[name] = data
        for name in ['posterior/final-posterior.csv','provenance/model_config.json','configs/experiment.yaml']:
            if name not in verified:
                raise ValueError(f'unmanifested science input: {name}')
        cols, weights, csv_meta = read_posterior_csv(verified['posterior/final-posterior.csv'])
        configs = {n: yaml.safe_load(verified[n]) for n in ['configs/experiment.yaml','configs/inference.yaml','configs/observation.yaml'] if n in verified}
        config = configs['configs/experiment.yaml']
        if config.get('experiment_id') != experiment_id:
            raise ValueError('configuration experiment mismatch')
        if config.get('args',{}).get('observer_speed_max') != 12.0 or config['args'].get('observer_speed_min') != 0.0:
            raise ValueError('radial-speed prior changed from published source')
        meta = {'experiment_id':experiment_id,'child_archive_name':base,'child_archive_sha256':digest,
                'artifact_manifest_sha256':sha256(manifest_raw),'artifact_manifest':manifest,
                'verified_member_hashes':member_hashes,'model_config':json.loads(verified['provenance/model_config.json']),
                'configs':configs,'csv':csv_meta}
        return cols, weights, meta


def run(archive_path, *, expected_outer_sha256=OUTER_SHA256, cmb_ra_deg=167.942, cmb_dec_deg=-6.944):
    raw = Path(archive_path).read_bytes()
    digest = sha256(raw)
    if digest != expected_outer_sha256:
        raise ValueError('outer archive SHA256 mismatch')
    results = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = [n for n in z.namelist() if '__MACOSX' not in Path(n).parts and not Path(n).name.startswith('._')]
        for exp, expected in CHILD_HASHES.items():
            found = [n for n in names if Path(n).name == f'{exp}.{expected}.analysis.zip']
            if len(found) != 1:
                raise ValueError(f'expected exactly one release child for {exp}')
            cols, weights, meta = read_child_archive(z.read(found[0]), found[0], expected_hash=expected, experiment_id=exp)
            results[exp] = {'source':meta,'posterior_pushforward':summarize_posterior(cols,weights,cmb_ra_deg=cmb_ra_deg,cmb_dec_deg=cmb_dec_deg)}
    return {'schema':'htt.r65.racs_weighted_projection/1','source_archive':str(archive_path),
            'source_archive_sha256':digest,
            'runtime':{'python':platform.python_version(),'numpy':np.__version__,'astropy':astropy.__version__,
                       'pyyaml':yaml.__version__,'anesthetic_available':importlib.util.find_spec('anesthetic') is not None,
                       'reader':'validated csv module reader; original nested weights, no logL reweighting'},
            'frame_reference':'https://docs.astropy.org/en/stable/coordinates/transforming.html',
            'source_release':'https://github.com/o-oayda/cracking-into-racs-i/releases/tag/v1.0.0',
            'speed_normalizer_authority':'primary arXiv2610.35207v1 Eq2;369.82km/s',
            'prior_semantics':'source speed uniform[0,12], isotropic direction; Cartesian density proportional1/|v|^2; nuisance priors inherited',
            'scope':'weighted posterior pushforward only; no new fit, posterior-as-likelihood, cross-survey joint significance or independent-survey assumption',
            'models':results}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',required=True)
    p.add_argument('--output',required=True)
    p.add_argument('--cmb-ra-deg',type=float,default=167.942)
    p.add_argument('--cmb-dec-deg',type=float,default=-6.944)
    args = p.parse_args()
    out = run(args.archive,cmb_ra_deg=args.cmb_ra_deg,cmb_dec_deg=args.cmb_dec_deg)
    Path(args.output).write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')


if __name__ == '__main__':
    main()
