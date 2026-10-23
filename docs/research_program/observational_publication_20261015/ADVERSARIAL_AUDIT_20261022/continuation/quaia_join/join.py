"""A22-03: exact integer-ID Quaia/retained-CRF3 cohort, no astrometric fit."""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import platform
import time
import zipfile

import healpy as hp
import numpy as np
from astropy.io import fits

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
RAW = Path('/mnt/extdrive/workdir/htt_open_data')
QUAIA = RAW / 'adversarial20261022/quaia'
GAIA = RAW / 'gaia/d05_full_20261018/full.vot'
OUT = RAW / 'a22_20261023/quaia_join'
GAIA_SHA = 'e8454190bb3be7d10203ecfe6fe90b34d245fb13b9bb72a155242f85e4271810'
PAYLOADS = {
    'quaia_G20.0.fits': 'efeda9ae727bf2cd75569f52460a0492827c8a3fcd8ce29dc692b559fca2acb0',
    'selection_function_NSIDE64_G20.0.fits': 'f66684999b0fdab1cdc3f8fc3ac8ef16956cb037785dbac2dc395dae3ffedd7d',
    'selection_function_template_maps.zip': '7e5987925120b40d59ce1b89a49866d471be8d1f025b5b9636ea1c47d867dc5e',
}
TEMPLATES = ['dust', 'stars', 'm10', 'mcs', 'unwise', 'unwisescan', 'mcsunwise']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024**2), b''):
            h.update(b)
    return h.hexdigest()


def integer_ids(values):
    x = np.asarray(values)
    if x.dtype.kind not in 'iu' or x.ndim != 1 or np.any(x <= 0):
        raise ValueError('positive integer source_id vector required; no float IDs')
    return x.astype(np.int64)


def exact_indices(sorted_ids, query_ids):
    a, b = integer_ids(sorted_ids), integer_ids(query_ids)
    if len(a) == 0 or np.any(a[1:] <= a[:-1]):
        raise ValueError('reference source_ids must be strictly increasing')
    j = np.searchsorted(a, b)
    good = j < len(a)
    good[good] &= a[j[good]] == b[good]
    return j[good], np.flatnonzero(good)


def selection_pixels(ra, dec):
    ra, dec = np.asarray(ra, float), np.asarray(dec, float)
    if not np.isfinite(ra).all() or not np.isfinite(dec).all() or np.any(abs(dec) > 90):
        raise ValueError('finite ICRS coordinates required')
    return hp.ang2pix(64, ra, dec, lonlat=True, nest=False)


def main():
    start = time.perf_counter()
    identities = {}
    for name, expected in PAYLOADS.items():
        p = QUAIA / name
        actual = digest(p)
        if actual != expected:
            raise ValueError('Quaia immutable input drift: ' + name)
        receipt = json.loads(Path(str(p) + '.receipt.json').read_text())
        if receipt['sha256'] != actual or receipt['bytes'] != p.stat().st_size:
            raise ValueError('Quaia receipt mismatch')
        identities[name] = dict(path=str(p), bytes=p.stat().st_size, sha256=actual)
    with fits.open(QUAIA / 'quaia_G20.0.fits', memmap=True) as h:
        if len(h[1].data) != 755850:
            raise ValueError('Quaia G20 release count')
        columns = ['source_id', 'ra', 'dec', 'redshift_quaia', 'redshift_quaia_err',
                   'phot_g_mean_mag', 'pm', 'pmra', 'pmdec', 'pmra_error', 'pmdec_error']
        q = {k: np.array(h[1].data[k]) for k in columns}
        schema = [{'name': c.name, 'format': c.format, 'unit': c.unit} for c in h[1].columns]
    order = np.argsort(integer_ids(q['source_id']))
    q = {k: v[order] for k, v in q.items()}
    ids = integer_ids(q['source_id'])
    if np.any(ids[1:] <= ids[:-1]):
        raise ValueError('duplicate Quaia source_id')
    for k, a in q.items():
        if k != 'source_id' and not np.isfinite(a).all():
            raise ValueError('nonfinite Quaia required field: ' + k)
    if np.any(q['redshift_quaia_err'] < 0):
        raise ValueError('negative reported redshift error')
    with fits.open(QUAIA / 'selection_function_NSIDE64_G20.0.fits', memmap=True) as h:
        if h[1].header['NSIDE'] != 64 or h[1].header['ORDERING'] != 'RING':
            raise ValueError('selection geometry drift')
        selection_map = np.array(h[1].data['T']).ravel()
    pix = selection_pixels(q['ra'], q['dec'])
    q['selection_relative'] = selection_map[pix]
    q['pixel_ring64'] = pix
    if not np.isfinite(selection_map).all() or np.any(selection_map < 0):
        raise ValueError('invalid relative selection map')
    with zipfile.ZipFile(QUAIA / 'selection_function_template_maps.zip') as z:
        for name in TEMPLATES:
            data = np.load(io.BytesIO(z.read('selection_function_template_maps/map_' + name + '_NSIDE64.npy')), allow_pickle=False)
            if data.shape != (49152,) or not np.isfinite(data).all():
                raise ValueError('invalid template: ' + name)
            q['template_' + name] = data[pix]
    donor = REPO / 'docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/EXECUTION_20261018/GAIA_COVARIANCE_ENVELOPE_20261019/envelope.py'
    spec = importlib.util.spec_from_file_location('a22_frozen_gaia_reader', donor)
    reader_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader_module)
    found = np.zeros(len(ids), bool)
    fields = ['ra', 'dec', 'pmra', 'pmdec', 'pmra_error', 'pmdec_error',
              'pmra_pmdec_corr', 'astrometric_params_solved', 'ruwe']
    gaia = {k: np.full(len(ids), np.nan) for k in fields}

    def consume(rows):
        dst, src = exact_indices(ids, rows['source_id'])
        if np.any(found[dst]) or len(np.unique(dst)) != len(dst):
            raise ValueError('non-unique Gaia-to-Quaia match')
        for k in fields:
            gaia[k][dst] = rows[k][src]
        found[dst] = True

    reader = reader_module.FrozenReader(consume)
    h = hashlib.sha256()
    with GAIA.open('rb') as f:
        for b in iter(lambda: f.read(1024**2), b''):
            h.update(b)
            reader.feed(b)
    reader.feed(b'', final=True)
    if h.hexdigest() != GAIA_SHA or reader.rows != 1614173:
        raise ValueError('retained Gaia immutable hash/count mismatch')
    joined = {k: a[found] for k, a in q.items()}
    comparison = {}
    for k in fields[:6]:
        diff = float(np.max(abs(gaia[k][found] - joined[k])))
        comparison[k] = diff
        if diff > 1e-10:
            raise ValueError('same-ID astrometry differs from Quaia: ' + k)
    for k in fields:
        joined['gaia_' + k] = gaia[k][found]
    rho = joined['gaia_pmra_pmdec_corr']
    if not np.isfinite(rho).all() or np.any(abs(rho) >= 1):
        raise ValueError('invalid proper-motion correlation')
    if np.any(joined['pmra_error'] <= 0) or np.any(joined['pmdec_error'] <= 0):
        raise ValueError('nonpositive PM errors')
    # One mas/yr -> microas/yr conversion; covariance factors are formed downstream.
    joined['pmra_uasyr'] = joined['pmra'].astype(float) * 1000
    joined['pmdec_uasyr'] = joined['pmdec'].astype(float) * 1000
    joined['pmra_error_uasyr'] = joined['pmra_error'].astype(float) * 1000
    joined['pmdec_error_uasyr'] = joined['pmdec_error'].astype(float) * 1000
    pm_limit = 10 ** (0.4 * (q['phot_g_mean_mag'].astype(float) - 18.25))
    edges = np.array([0, 1, 2, 10.0])
    rows = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (q['redshift_quaia'] >= lo) & (q['redshift_quaia'] < hi)
        rows.append(dict(z_interval=[float(lo), float(hi)], quaia=int(sel.sum()),
                         crf3_match=int((sel & found).sum()), unmatched=int((sel & ~found).sum())))
    OUT.mkdir(parents=True, exist_ok=True)
    target = OUT / 'quaia_crf3_join.npz'
    np.savez_compressed(target, **joined)
    result = dict(owner='obsstat', scope='exact Quaia G20 / Gaia CRF3 intersection cohort',
                  claim_tier='C0_DIAGNOSTIC_ONLY', transfer_source='none',
                  input_identities=identities, quaia_schema=schema,
                  gaia_input=dict(path=str(GAIA), sha256=h.hexdigest(), bytes=GAIA.stat().st_size,
                                  rows=reader.rows, reused_reader_sha256=digest(donor)),
                  quaia_rows=len(ids), matched_rows=int(found.sum()), unmatched_rows=int((~found).sum()),
                  exact_integer_source_id=True, unique_source_ids=True, loss_by_redshift=rows,
                  same_id_astrometry_max_abs_difference=comparison,
                  selection_frame='ICRS equatorial, author v1.0.0 notebook; FITS lacks COORDSYS',
                  selection_relative_zero_rows=int((q['selection_relative'] == 0).sum()),
                  pm_cut=dict(formula='pm < 10**(0.4*(G-18.25)) mas/yr',
                              nonpassing_rows=int((q['pm'] >= pm_limit).sum()),
                              total_pm_vector_max_abs_difference=float(np.max(abs(q['pm'] - np.hypot(q['pmra'], q['pmdec']))))),
                  redshift_minmax=[float(q['redshift_quaia'].min()), float(q['redshift_quaia'].max())],
                  rho_minmax=[float(rho.min()), float(rho.max())],
                  artifact=dict(path=str(target), sha256=digest(target), bytes=target.stat().st_size),
                  runtime=dict(python=platform.python_version(), numpy=np.__version__, requested_parent='gpt-6.1-sol/high', observed='UNKNOWN'),
                  seconds=time.perf_counter() - start,
                  caveats=['Intersection is additionally conditioned on CRF3 membership; unmatched objects are not imputed.',
                           'Relative selection values/templates are covariates, not absolute inclusion probabilities or inverse weights.',
                           'Measured PM cut and upstream Gaia classifiers make intrinsic untruncated Gaussian inference unqualified.',
                           'No cross-source covariance, acceleration, congruence transfer or original K03 admission is supplied.'])
    (HERE / 'RESULT.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    bins = np.linspace(0, 5, 41)
    ax[0].hist(q['redshift_quaia'], bins=bins, histtype='step', label='Quaia G<20')
    ax[0].hist(q['redshift_quaia'][found], bins=bins, histtype='step', label='CRF3 intersection')
    ax[0].set(xlabel='reported spectrophotometric redshift', ylabel='source count')
    ax[0].legend()
    ax[1].hist(rho, bins=50)
    ax[1].set(xlabel='reported PM correlation', ylabel='matched source count')
    fig.suptitle('A22-03 exact-ID cohort linkage; no acceleration inference')
    fig.tight_layout()
    for ext in ('png', 'pdf'):
        fig.savefig(HERE / ('JOIN.' + ext), dpi=160)
    plt.close(fig)
    print(json.dumps({k: result[k] for k in ('quaia_rows', 'matched_rows', 'unmatched_rows', 'seconds')}))


if __name__ == '__main__':
    main()
