"""Read precomputed official legacy T fixtures; never execute upstream solver."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from astropy.io import fits

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parents[2]
REPO = PROGRAM.parents[2]
sys.path.insert(0, str(REPO/'htt'))
from obsstat.r7_cmb_product_response import real_design

RAW = Path('/mnt/extdrive/workdir/htt_open_data/external_transfer/bianchi_v1_1_1c90b98')
FILES = {'sky_bianchi_test.fits': '2f2ef5aa37de1bb7438808c53819b786915ebda0',
         'sky_bianchi_test_mK.fits': '9c99cd6c0a44a45987bf09e2d75fedf60dd7ba59'}


def read_map(path, git_blob):
    data = path.read_bytes()
    if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest() != git_blob:
        raise ValueError('IMMUTABLE_GIT_BLOB_MISMATCH')
    with fits.open(path) as hdus:
        h = hdus[1]
        if (h.header.get('NSIDE') != 64 or h.header.get('ORDERING') != 'RING'
                or h.columns.names != ['simulation']):
            raise ValueError('LEGACY_MAP_LAYOUT')
        a = np.asarray(h.data['simulation'], float).reshape(-1)
        if a.shape != (49152,) or not np.isfinite(a).all() or np.any(abs(a) >= 1e20):
            raise ValueError('LEGACY_MAP_INVALID')
        meta = {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                'git_blob': git_blob, 'unit_header': h.header.get('TUNIT1'),
                'coordsys_header': h.header.get('COORDSYS'), 'nside': 64, 'ordering': 'RING'}
    return a, meta


def unit_comparison(a, b):
    if a.shape != b.shape or not np.isfinite(a).all() or not np.isfinite(b).all() or a@a <= 0:
        raise ValueError('FINITE_NONZERO_EQUAL_MAPS_REQUIRED')
    scale = float(a@b/(a@a))
    if b@b <= 0: raise ValueError('NONZERO_SECOND_MAP_REQUIRED')
    return {'least_squares_scale': scale,
            'relative_residual_best_scale': float(np.linalg.norm(b-scale*a)/np.linalg.norm(b)),
            'relative_residual_declared_2725': float(np.linalg.norm(b-2725*a)/np.linalg.norm(b))}


def run():
    import healpy as hp
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    target = HERE/'RESULT.json'
    if target.exists() or (HERE/'COEFFICIENTS.npz').exists():
        raise FileExistsError('CREATE_ONLY_OUTPUT_EXISTS')
    arrays, records = zip(*(read_map(RAW/'test'/n, blob) for n, blob in FILES.items()))
    a, b = arrays
    comp = unit_comparison(a, b)
    # A source-qualified unit-consistency criterion only, not physical acceptance.
    if abs(comp['least_squares_scale']/2725-1) > 2e-6 or comp['relative_residual_declared_2725'] > 2e-6:
        raise ValueError('UNIT_VARIANTS_NOT_CONSISTENT')
    n = np.column_stack(hp.pix2vec(64, np.arange(49152)))
    design = real_design(n, ell_max=12)
    coeff, _, rank, singular = np.linalg.lstsq(design, a, rcond=None)
    if rank != 169: raise ValueError('FINITE_DESIGN_RANK')
    residual = a-design@coeff
    power = [float(coeff[l*l:(l+1)**2]@coeff[l*l:(l+1)**2]) for l in range(13)]
    # No sky-coordinate interpretation: this is the file's arbitrary angular chart.
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
    axes[0].semilogy(np.arange(13), power, 'o-')
    axes[0].set(xlabel='ell', ylabel='Sum of squared real coefficients (file unit squared)',
                title='Precomputed legacy T map: finite pixel fit')
    axes[1].hist((b-2725*a)*1e9, bins=60)
    axes[1].set(xlabel='mK variant minus 2725 × default (10^-9 mK)', ylabel='Pixels',
                title='Published unit-variant consistency')
    fig.suptitle('External legacy fixture; no E/B, atlas or physical null')
    fig.tight_layout()
    for ext in ('png', 'pdf'): fig.savefig(HERE/f'LEGACY_T_INTAKE.{ext}', dpi=150)
    with (HERE/'COEFFICIENTS.npz').open('xb') as stream:
        np.savez_compressed(stream, real_l0_l12_default_file_units=coeff)
    result = {'owner': 'obsstat', 'scope': 'PRECOMPUTED_EXTERNAL_LEGACY_T_FIXTURE_INTAKE',
        'claim_tier': 'DIAGNOSTIC_ONLY', 'transfer_source': 'astro-informatics/bianchi v1.1 precomputed test files',
        'source_commit': '1c90b9867b96eedf93983e33de72b3394f39d58e',
        'source_url': 'https://astro-informatics.github.io/bianchi/', 'sources': records,
        'unit_comparison': comp, 'unit_interpretation': 'default DeltaT/T; mK variant consistent with Tcmb=2.725 K',
        'frame': 'UNKNOWN_ABSOLUTE_SKY_FRAME_FILE_ANGULAR_CHART_ONLY',
        'parameter_binding': 'UPSTREAM_DECLARED_PARAM_PAR_TEST_MAP_BINDING',
        'parameter_binding_source': 'https://raw.githubusercontent.com/astro-informatics/bianchi/1c90b9867b96eedf93983e33de72b3394f39d58e/doc/index.html#testing',
        'parameter_binding_execution_verification': 'NOT_RUN_OWNER_FORBIDS_SOLVER_EXECUTION',
        'sky_support_status': 'FULLSKY_FILE_PIXELS_NO_OBSERVATIONAL_MASK',
        'null_mock_status': 'NONE_NO_INFERENCE',
        'fit': {'lmax': 12, 'rank': int(rank), 'condition': float(singular[0]/singular[-1]),
                'rms_default_units': float(np.sqrt(np.mean(a*a))),
                'residual_rms_default_units': float(np.sqrt(np.mean(residual**2))),
                'residual_fraction': float(np.linalg.norm(residual)/np.linalg.norm(a)),
                'power_by_ell_default_units_squared': power},
        'polarization': 'NOT_SUPPLIED_NOT_ZERO', 'native_solver': False,
        'physical_atlas_eligibility': False, 'B02_original_acceptance': 'HOLD',
        'caveats': ['Legacy source describes temperature-only VIIh without dark energy.',
                    'No source code executed, solver built, or ODE integrated.',
                    'Finite l<=12 pixel projection is not exact harmonic continuum transfer.',
                    'Parameter binding is upstream-declared, not independently executed; absolute frame, beam and global-history mapping are not certified.',
                    'No morphology match to observed sky or native family identification.'],
        'requested_runtime': 'gpt-6.1-sol/high', 'observed_runtime': 'UNKNOWN'}
    target.write_text(json.dumps(result, indent=2)+'\n')


if __name__ == '__main__': run()
