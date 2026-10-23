"""Anonymous TAP upload of only unmatched Quaia IDs; persistent UWS identity."""
from pathlib import Path
import argparse
import datetime
import hashlib
import io
import json
import shutil
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np
from astropy.io import fits
from astropy.io.votable import parse_single_table
from astropy.table import Table
from join import RAW, QUAIA, OUT, HERE, digest, exact_indices

BASE = 'https://gaia.ari.uni-heidelberg.de/tap'
RESERVE = 2 * 1024**3
QUERY = ('SELECT g.source_id,g.pmra_pmdec_corr,g.ruwe,g.astrometric_params_solved '
         'FROM gaiadr3.gaia_source AS g JOIN TAP_UPLOAD.ids AS u ON g.source_id=u.source_id')


def request(url, data=None, headers=None):
    if isinstance(data, dict):
        data = urllib.parse.urlencode(data).encode()
    return urllib.request.urlopen(urllib.request.Request(url, data=data, headers={
        'User-Agent': 'HTT-A22-03-public-subset/1', 'Accept-Encoding': 'identity', **(headers or {})}), timeout=45)


def save(record):
    (OUT / 'supplement.job.json').write_text(json.dumps(record, indent=2) + '\n')


def validate_subset(table, needed):
    expected = ['source_id', 'pmra_pmdec_corr', 'ruwe', 'astrometric_params_solved']
    if table.colnames != expected:
        raise ValueError('subset schema differs from the exact query')
    for k in expected:
        if np.ma.getmaskarray(table[k]).any() or not np.isfinite(table[k]).all():
            raise ValueError('subset NULL/nonfinite field: ' + k)
    if table['source_id'].dtype.kind not in 'iu':
        raise ValueError('subset source_id must be integer')
    sid = np.asarray(table['source_id'], dtype=np.int64)
    if len(sid) != len(needed) or not np.array_equal(np.sort(sid), needed):
        raise ValueError('subset IDs missing/duplicate/unrequested')
    if np.any(abs(np.asarray(table['pmra_pmdec_corr'])) >= 1):
        raise ValueError('subset PM correlation outside positive covariance domain')
    return sid


def refresh_status(record, target, collecting):
    # The server's temporary UWS object may expire. Immutable local data remain
    # reusable; the caller still checks its hash, status, schema and exact IDs.
    if collecting and target.exists():
        if record.get('phase') != 'COMPLETED' or not record.get('sha256'):
            raise ValueError('cached subset lacks completed identity metadata')
        return None
    with request(record['job_url']) as r:
        body = r.read()
    (OUT / 'supplement.uws.xml').write_bytes(body)
    node = ET.fromstring(body)
    record['phase'] = node.findtext('{*}phase')
    save(record)
    return node


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--collect', action='store_true')
    args = ap.parse_args()
    meta = OUT / 'supplement.job.json'
    cache = OUT / 'quaia_crf3_join.npz'
    join_result = json.loads((HERE / 'RESULT.json').read_text())
    if digest(cache) != join_result['artifact']['sha256']:
        raise ValueError('first-stage join changed')
    if digest(QUAIA / 'quaia_G20.0.fits') != join_result['input_identities']['quaia_G20.0.fits']['sha256']:
        raise ValueError('Quaia immutable source changed')
    with np.load(cache, allow_pickle=False) as z:
        old = {k: z[k] for k in z.files}
    with fits.open(QUAIA / 'quaia_G20.0.fits', memmap=True) as h:
        q = {k: np.array(h[1].data[k]) for k in h[1].columns.names if k != 'unwise_objid'}
    order = np.argsort(q['source_id'])
    q = {k: a[order] for k, a in q.items()}
    ids = q['source_id'].astype(np.int64)
    matched, _ = exact_indices(ids, old['source_id'])
    missing = np.ones(len(ids), bool)
    missing[matched] = False
    needed = ids[missing]
    ids_sha = hashlib.sha256(needed.astype('<i8').tobytes()).hexdigest()
    if not meta.exists():
        upload = io.BytesIO()
        Table({'source_id': needed}).write(upload, format='votable')
        boundary = 'HTTA22UploadBoundary'
        pieces = []
        fields = dict(REQUEST='doQuery', LANG='ADQL', QUERY=QUERY, FORMAT='votable/b2',
                      MAXREC=str(len(needed) + 1), UPLOAD='ids,param:ids', RUNID='HTT_A22_03_MISSING')
        for key, value in fields.items():
            pieces.append(('--' + boundary + '\r\nContent-Disposition: form-data; name="' + key + '"\r\n\r\n' + value + '\r\n').encode())
        pieces.append(('--' + boundary + '\r\nContent-Disposition: form-data; name="ids"; filename="ids.vot"\r\nContent-Type: application/x-votable+xml\r\n\r\n').encode() + upload.getvalue() + b'\r\n')
        pieces.append(('--' + boundary + '--\r\n').encode())
        with request(BASE + '/async', b''.join(pieces), {'Content-Type': 'multipart/form-data; boundary=' + boundary}) as r:
            job = r.geturl().rstrip('/')
            body = r.read()
        if '/async/' not in job:
            (OUT / 'supplement.create_failure.txt').write_bytes(body)
            raise ValueError('no durable UWS identity')
        record = dict(job_url=job, query=QUERY, missing_ids_sha256=ids_sha, requested_rows=len(needed),
                      created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), phase='CREATED_NOT_STARTED')
        save(record)
        with request(job + '/phase', {'PHASE': 'RUN'}) as r:
            r.read()
    else:
        record = json.loads(meta.read_text())
        if record['missing_ids_sha256'] != ids_sha or record['query'] != QUERY:
            raise ValueError('existing subset identity differs; never replace job')
    target = OUT / 'supplement.vot'
    node = refresh_status(record, target, args.collect)
    print(json.dumps(record), flush=True)
    if record['phase'] == 'ERROR':
        with request(record['job_url'] + '/error') as r:
            (OUT / 'supplement.error.xml').write_bytes(r.read())
        raise ValueError('subset query failed; raw error preserved')
    if not args.collect or record['phase'] != 'COMPLETED':
        return
    if not target.exists():
        result = node.find('.//{*}result')
        url = result.get('{http://www.w3.org/1999/xlink}href')
        part = target.with_suffix('.vot.part')
        if part.exists():
            raise ValueError('partial preserved; inspect before collection')
        if shutil.disk_usage(OUT).free < RESERVE:
            raise OSError('disk reserve')
        h = hashlib.sha256()
        size = 0
        with request(url) as r, part.open('xb') as f:
            expected = r.headers.get('Content-Length')
            while block := r.read(1024**2):
                if shutil.disk_usage(OUT).free < RESERVE + len(block):
                    raise OSError('streaming disk reserve')
                f.write(block)
                h.update(block)
                size += len(block)
        if expected is not None and size != int(expected):
            raise ValueError('subset HTTP length mismatch')
        record.update(result_url=url, bytes=size, sha256=h.hexdigest(), result_path=str(target))
        save(record)
        part.rename(target)
    if digest(target) != record['sha256']:
        raise ValueError('subset raw drift')
    statuses = []
    for _, e in ET.iterparse(target, events=('end',)):
        if e.tag.endswith('INFO') and e.get('name') == 'QUERY_STATUS':
            statuses.append(e.get('value'))
        e.clear()
    if not statuses or any(v != 'OK' for v in statuses):
        raise ValueError('subset overflow/error')
    table = parse_single_table(target).to_table()
    sid = validate_subset(table, needed)
    full = {k: a.copy() for k, a in q.items() if k in old}
    for k, a in old.items():
        if k not in full:
            full[k] = np.full(len(ids), np.nan, dtype=float)
        full[k][matched] = a
    ix = np.searchsorted(ids, sid)
    for k in ('pmra_pmdec_corr', 'ruwe', 'astrometric_params_solved'):
        full['gaia_' + k][ix] = np.asarray(table[k], float)
    for k in ('ra', 'dec', 'pmra', 'pmdec', 'pmra_error', 'pmdec_error'):
        full['gaia_' + k][missing] = q[k][missing]
    # Reuse source-frame/order definitions, and apply them to every catalogue row.
    from join import selection_pixels, TEMPLATES
    import zipfile
    pix = selection_pixels(q['ra'], q['dec'])
    with fits.open(QUAIA / 'selection_function_NSIDE64_G20.0.fits', memmap=True) as h:
        full['selection_relative'] = np.asarray(h[1].data['T']).ravel()[pix]
    full['pixel_ring64'] = pix
    with zipfile.ZipFile(QUAIA / 'selection_function_template_maps.zip') as z:
        for name in TEMPLATES:
            full['template_' + name] = np.load(io.BytesIO(z.read('selection_function_template_maps/map_' + name + '_NSIDE64.npy')), allow_pickle=False)[pix]
    for k in ('pmra', 'pmdec', 'pmra_error', 'pmdec_error'):
        full[k + '_uasyr'] = q[k].astype(float) * 1000
    full['in_retained_crf3'] = ~missing
    rho = full['gaia_pmra_pmdec_corr']
    if not np.isfinite(rho).all() or np.any(abs(rho) >= 1):
        raise ValueError('supplement PM covariance invalid')
    target_full = OUT / 'quaia_gaia_full_join.npz'
    np.savez_compressed(target_full, **full)
    result = dict(owner='obsstat', scope='full Quaia G20 exact Gaia ID covariance supplementation',
                  claim_tier='C0_SOURCE_JOIN', quaia_rows=len(ids), cached_matches=len(matched),
                  subset_rows=len(sid), final_join_rows=len(ids), missing_rows=0,
                  subset_job=record, query_status=statuses, covariance='reported per-source 2x2 PM blocks only',
                  artifact=dict(path=str(target_full), bytes=target_full.stat().st_size, sha256=digest(target_full)),
                  caveats=join_result['caveats'][1:])
    (HERE / 'SUPPLEMENT_RESULT.json').write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(dict(full_join_rows=len(ids), subset_rows=len(sid), artifact=str(target_full))))


if __name__ == '__main__':
    main()
