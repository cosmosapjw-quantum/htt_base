"""Acquire only official public flow metadata and small grouped FITS fields."""
from pathlib import Path
import hashlib
import json
import urllib.request
import shutil
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
RAW = Path('/mnt/extdrive/workdir/htt_open_data/cf4/d06_flow_20261018')
URLS = {
    'cosmicflows.html': 'https://projets.ip2i.in2p3.fr/cosmicflows/',
    'CF4gp_new_64-z008_velocity.fits': 'https://projets.ip2i.in2p3.fr//cosmicflows/CF4gp_new_64-z008_velocity.fits',
    'CF4gp_new_64-z008_velocity_cube_error.fits': 'https://projets.ip2i.in2p3.fr//cosmicflows/CF4gp_new_64-z008_velocity_cube_error.fits',
    'retrieve_CF4pp_grid_values.py': 'https://projets.ip2i.in2p3.fr//cosmicflows/retrieve_CF4pp_grid_values.py',
    'CF4pp_mean_std_grids.npz': 'https://projets.ip2i.in2p3.fr//cosmicflows/CF4pp_mean_std_grids.npz',
    'new_CF4pp_mean_std_grids.npz': 'https://projets.ip2i.in2p3.fr//cosmicflows/new_CF4pp_mean_std_grids.npz',
}


def acquire():
    RAW.mkdir(exist_ok=True)
    receipts = {}
    for name, url in URLS.items():
        path, receipt = RAW / name, RAW / (name + '.receipt.json')
        if path.exists():
            if not receipt.exists():
                raise ValueError('existing source without receipt: ' + str(path))
            meta = json.loads(receipt.read_text())
            if hashlib.sha256(path.read_bytes()).hexdigest() != meta['sha256']:
                raise ValueError('source bytes changed: ' + str(path))
        else:
            try:
                cap = 190 * 1024**2 if name.endswith('.npz') else 8 * 1024**2
                if shutil.disk_usage(RAW).free < 2 * 1024**3 + cap:
                    raise ValueError('2GiB reserve would be violated')
                with urllib.request.urlopen(url, timeout=60) as response:
                    if response.status != 200:
                        raise ValueError('unexpected HTTP status')
                    blob = response.read(cap + 1)
                    if len(blob) > cap:
                        raise ValueError('per-product hard cap exceeded')
                    expected = response.headers.get('Content-Length')
                    if expected is not None and len(blob) != int(expected):
                        raise ValueError('incomplete source bytes')
                    meta = {'url': url, 'final_url': response.url, 'status': response.status,
                            'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest(),
                            'content_length': expected, 'etag': response.headers.get('ETag'),
                            'last_modified': response.headers.get('Last-Modified'),
                            'received_utc': datetime.now(timezone.utc).isoformat()}
                path.write_bytes(blob)
                receipt.write_text(json.dumps(meta, indent=2) + '\n')
            except Exception as exc:
                with (HERE / 'ACQUISITION_FAILURES.jsonl').open('a') as stream:
                    stream.write(json.dumps({'name': name, 'url': url, 'error': repr(exc)}) + '\n')
                if name != 'retrieve_CF4pp_grid_values.py':
                    raise
                continue
        receipts[name] = meta
    (HERE / 'ACQUISITION_RECEIPT.json').write_text(json.dumps(receipts, indent=2) + '\n')
    print(json.dumps(receipts, indent=2))


if __name__ == '__main__':
    acquire()
