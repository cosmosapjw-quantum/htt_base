"""New split noises through the unchanged original selected-pixel operator.

One nominal simulation ID is descriptive, never an ensemble covariance or PTE.
"""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys
import time
import tarfile
import io

import numpy as np
from astropy.io import fits

HERE = Path(__file__).resolve().parent
PROGRAM = HERE.parents[2]
OLD = PROGRAM / 'CONTINUATION_20261018/L03_EXECUTION_20261018'
spec = importlib.util.spec_from_file_location('source_matched_pilot', OLD/'source_matched_pilot.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
ROOT = Path('/mnt/extdrive/workdir/htt_open_data')
SPLITS = ('HM1', 'HM2', 'OE1', 'OE2')
PILOT_SHA = '75a9a46c3cb2f576c994fefec248805cc604532345f7843bcd487ca848953123'


def weight_intake():
    path = ROOT/'planck/PR3/weights/COM_Code_SMICA-weights-propagation_R3.00.tar.gz'
    rec = json.loads(path.with_name(path.name+'.receipt.json').read_text())
    meta = old.identity(path, rec['sha256'])
    arrays = {}
    with tarfile.open(path, 'r:gz') as archive:
        readme = archive.extractfile('README').read().decode()
        if 'weights include a beam correction' not in readme or 're-normalization' not in readme:
            raise ValueError('WEIGHTS_BEAM_CALIBRATION_CONVENTION')
        for name in ('weights_T_smica_R3.00_Xfull.txt', 'weights_T_smica_R3.00_Xhigh.txt',
                     'weights_EB_smica_R3.00.txt'):
            data = archive.extractfile(name).read()
            a = np.loadtxt(io.BytesIO(data))
            if not np.isfinite(a).all(): raise ValueError('NONFINITE_WEIGHTS')
            arrays[name] = {'shape': list(a.shape), 'sha256': hashlib.sha256(data).hexdigest()}
        p = np.loadtxt(archive.extractfile('weights_EB_smica_R3.00.txt')).reshape(2, 7, 4001)
        arrays['polarization_reshape'] = list(p.shape)
    return {'source': meta, 'members': arrays, 'upstream_code_executed': False,
            'beam_correction_already_in_weights': True, 'LFI_renormalization_already_in_weights': True,
            'additional_beam_applied': False, 'split_specific_response': 'UNKNOWN'}


def contrasts(coeff):
    a = np.asarray(coeff, float)
    if a.shape != (5, 96) or not np.isfinite(a).all():
        raise ValueError('FIVE_FINITE_ORDERED_FULL_HM1_HM2_OE1_OE2_ROWS_REQUIRED')
    return np.array([(a[1]-a[2])/2, (a[3]-a[4])/2,
                     a[0]-(a[1]+a[2])/2, a[0]-(a[3]+a[4])/2])


def validate_hdu(h):
    if (h.header.get('NSIDE') != 2048 or h.header.get('ORDERING') != 'RING'
        or h.header.get('COORDSYS', 'G') != 'G'
        or h.columns.names != list(old.FIELDS)
        or any(h.header.get(f'TUNIT{k}') != 'K_CMB' for k in (1, 2, 3))):
        raise ValueError('SPLIT_FITS_SOURCE_LAYOUT')
    if any(h.data[name].size != 12*2048**2 for name in old.FIELDS):
        raise ValueError('SPLIT_PIXEL_COUNT')


def run():
    import healpy as hp
    t0 = time.monotonic()
    out = HERE/'RESULT.json'
    compact = HERE/'COEFFICIENTS.npz'
    cache = ROOT/'provenance/D04_SPLIT_NOISE_SELECTED_IQU_00000_20261018.npz'
    if any(p.exists() for p in (out, compact, cache)):
        raise FileExistsError('CREATE_ONLY_OUTPUT_EXISTS')
    paths = [ROOT/f'planck/PR3/split_noise/dx12_v3_smica_noise_{s.lower()}_mc_00000_raw.fits' for s in SPLITS]
    # Fail before expensive work unless every acquisition has completed.
    receipts = []
    for p in paths:
        r = json.loads(p.with_name(p.name+'.receipt.json').read_text())
        if r['status'] != 'DOWNLOADED' or r['bytes'] != p.stat().st_size:
            raise ValueError('ACQUISITION_NOT_COMPLETE')
        receipts.append(r)
    weights = weight_intake()
    wt, wp, st, sp, support = old.matched_support(ROOT, hp)
    _, scalar = old.pixel_fit_geometry()
    theta, phi = hp.pix2ang(64, np.arange(49152))
    spin = old.block_design(theta, phi, 2, 5)
    ot, mt = old.linear_projector(scalar, st)
    op, mp = old.linear_projector(spin, np.r_[sp, sp])
    pilot = OLD/'results/PILOT_COEFFICIENTS.npz'
    pilot_id = old.identity(pilot, PILOT_SHA)
    with np.load(pilot, allow_pickle=False) as z:
        full = z['component_coefficients_K_CMB'][0, 1].copy()
    coeff = np.empty((5, 96)); coeff[0] = full
    maps = np.empty((4, 3, 49152))
    sources = []
    for j, (p, receipt) in enumerate(zip(paths, receipts)):
        before = (p.stat().st_size, p.stat().st_mtime_ns)
        rec = old.identity(p, receipt['sha256'])
        with fits.open(p, memmap=True) as h:
            validate_hdu(h[1])
            reduced, coverage = old.ring_stream_selected_mean(
                [h[1].data[name] for name in old.FIELDS], (wt, wp, wp),
                (st, sp, sp), nside_in=2048, nside_out=64)
        if min(coverage) < .995 or before != (p.stat().st_size, p.stat().st_mtime_ns):
            raise ValueError('SOURCE_DRIFT_OR_COVERAGE')
        maps[j] = reduced
        coeff[j+1] = np.r_[(ot@reduced[0, st])[4:], op@np.r_[reduced[1, sp], reduced[2, sp]]]
        rec.update(split=SPLITS[j], minimum_coverage=coverage.tolist(),
                   coordsys='GALACTIC_RELEASE_CONVENTION_IF_HEADER_ABSENT')
        sources.append(rec)
        print(json.dumps({'phase': 'SPLIT_DONE', 'split': SPLITS[j], 'seconds': time.monotonic()-t0}), flush=True)
    diff = contrasts(coeff)
    sys.path.insert(0, str(OLD))
    import apply_l02_family as adapter
    family = adapter.family
    archive = family.SOURCE/'retained_common_support_coefficients.npz'
    chart = old.identity(archive, family.SOURCE_SHA)
    family.load_source()
    with np.load(archive, allow_pickle=False) as z:
        indices = adapter.explicit_field_indices(json.loads(z['column_spin_metadata_json'].item()))
    morphology = []
    baseline = []
    labels = list(('FULL',)+SPLITS)+['HM_HALF_DIFF', 'OE_HALF_DIFF', 'FULL_MINUS_HM_MEAN', 'FULL_MINUS_OE_MEAN']
    for label, row in zip(labels, np.concatenate((coeff, diff))):
        fields, tensors = {}, {}
        for field, ix in indices.items():
            retained = row[ix]*1e6
            q, o = family.tensors_from_real(retained)
            tensors[field] = (q, o)
            fields[field] = {'C2_microK2': float(retained[:5]@retained[:5]/5),
                             'C3_microK2': float(retained[5:12]@retained[5:12]/7),
                             **family.descriptors(q, o, field)}
            baseline.append((label, field, retained))
        morphology.append({'label': label, 'fields': fields,
            'same_row_cross_fields': {a+b: {'physical_O3_contraction_parity': -1 if 'B' in (a,b) else 1,
                                           **family.cross_features(*tensors[a], *tensors[b])}
                                     for a, b in (('T', 'E'), ('T', 'B'), ('E', 'B'))}})
    metamorphic = family.metamorphic_checks(baseline)
    blocks = {'T': list(range(32)), 'E': [], 'B': []}
    offset = 32
    for ell in range(2, 6):
        for name in ('E', 'B'):
            blocks[name].extend(range(offset, offset+2*ell+1)); offset += 2*ell+1
    summary = {name: {'five_row_norm_microK': (np.linalg.norm(coeff[:, ix], axis=1)*1e6).tolist(),
                      'contrast_norm_microK': (np.linalg.norm(diff[:, ix], axis=1)*1e6).tolist()}
               for name, ix in blocks.items()}
    cache.parent.mkdir(exist_ok=True)
    with cache.open('xb') as stream:
        np.savez_compressed(stream, splits=np.array(SPLITS), selected_IQU_K_CMB=maps,
                            T_mask=st, P_mask=sp)
    with compact.open('xb') as stream:
        np.savez_compressed(stream, rows=np.array(('FULL',)+SPLITS),
                            coefficients_K_CMB=coeff, contrasts_K_CMB=diff)
    result = {'owner': 'obsstat', 'scope': 'SAME_ID_SPLIT_PROCESSING_DIAGNOSTIC',
        'claim_tier': 'DIAGNOSTIC_ONLY', 'transfer_source': 'Planck PR3 FFP10 external simulations',
        'null_mock_status': 'ONE_NOMINAL_ID_NOT_ENSEMBLE', 'simulation_id': 0,
        'sky_support_status': support, 'source_files': sources, 'full_noise_reused': pilot_id,
        'fixed_weights_intake': weights,
        'operator': {'T': mt, 'P': mp, 'source': old.identity(OLD/'source_matched_pilot.py'),
                     'description': 'native masked child means then finite original OLS; no new beam or SHT'},
        'contrast_order': ['(HM1-HM2)/2', '(OE1-OE2)/2', 'FULL-(HM1+HM2)/2', 'FULL-(OE1+OE2)/2'],
        'blocks': summary, 'coefficients': old.identity(compact), 'external_coarse_cache': old.identity(cache),
        'fixed_L02_morphology': morphology, 'original_chart': chart,
        'L02_kernel': old.identity(family.HERE/'statistic_family.py'),
        'morphology_metamorphic_checks': metamorphic,
        'inference': None, 'physical_covariance': 'UNKNOWN', 'L03_original_acceptance': 'HOLD',
        'caveats': ['Nominal ID equality does not prove complete cross-split latent coupling.',
                    'No independent skies, covariance inversion, PTE or physical null calibration.',
                    '2018 HM signal/foreground and split response/selection law still missing.',
                    'Q/U average without parallel transport exactly as the original operator.'],
        'elapsed_seconds': time.monotonic()-t0, 'requested_runtime': 'gpt-6.1-sol/high',
        'observed_runtime': 'UNKNOWN', 'git_intake': '1528ebd3c4ace48a561b9dcaa6d5f891121a22a5'}
    out.write_text(json.dumps(result, indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, field in zip(axes, ('T', 'E', 'B')):
        ax.bar(np.arange(4), summary[field]['contrast_norm_microK'])
        ax.set(title=field+' original-operator noise contrasts', ylabel='Coefficient norm (microK)',
               xticks=np.arange(4), xticklabels=('HMdiff/2', 'OEdiff/2', 'F-HMmean', 'F-OEmean'))
        ax.tick_params(axis='x', rotation=30)
    fig.suptitle('One nominal ID00000 tuple; no ensemble covariance or PTE')
    fig.tight_layout()
    for ext in ('png', 'pdf'): fig.savefig(HERE/f'SPLIT_CONTRASTS.{ext}', dpi=150)


if __name__ == '__main__':
    run()
