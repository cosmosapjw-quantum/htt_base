"""Bounded, create-only download of official Kourkchi2020 catalogue sources."""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import gzip
import hashlib
import json
from datetime import datetime, timezone

RAW = Path('/mnt/extdrive/workdir/htt_open_data/cf4/upstream_20261018')
HERE = Path(__file__).resolve().parent
BASES = ['https://cdsarc.cds.unistra.fr/ftp/J/ApJ/902/145',
         'https://cdsarc.cds.unistra.fr/ftp/cats/J/ApJ/902/145',
         'https://cdsarc.u-strasbg.fr/ftp/pub/cats/J/ApJ/902/145']


def acquire():
    RAW.mkdir(parents=True, exist_ok=True)
    attempts = []
    sources = {}
    for name in ('ReadMe', 'table1.dat', 'table4.dat'):
        dest = RAW/name
        if dest.exists():
            raise FileExistsError(f'Existing source requires explicit receipt reuse: {dest}')
        for base in BASES:
            candidates = [name] if name == 'ReadMe' else [name, name+'.gz']
            for variant in candidates:
                url = base+'/'+variant
                item = {'url': url, 'time_utc': datetime.now(timezone.utc).isoformat()}
                try:
                    with urlopen(Request(url, headers={'User-Agent': 'HTT-source-provenance/1.0'}), timeout=25) as r:
                        blob = r.read(12_000_001)
                        item.update(http_status=r.status, content_type=r.headers.get('Content-Type'), final_url=r.geturl(), response_bytes=len(blob))
                    if len(blob) > 12_000_000:
                        raise ValueError('bounded response cap exceeded')
                    if blob[:2] == b'\x1f\x8b':
                        blob = gzip.decompress(blob)
                    if len(blob) > 12_000_000 or not blob or blob.lstrip().lower().startswith((b'<html', b'<!doctype')):
                        raise ValueError('empty/HTML/oversized response is not catalogue')
                    with dest.open('xb') as f:
                        f.write(blob)
                    item['status'] = 'SOURCE_SAVED'
                    sources[name] = {'url': url, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest(), 'path': str(dest)}
                except Exception as exc:
                    item.update(status='FAILED', error_type=type(exc).__name__, error=str(exc))
                    if isinstance(exc, HTTPError):
                        item['http_status'] = exc.code
                        body = exc.read(4096)
                        item['error_body_preview'] = body.decode('utf8', errors='replace')[:500]
                attempts.append(item)
                print(json.dumps(item), flush=True)
                if name in sources:
                    break
            if name in sources:
                break
    receipt = {'catalogue': 'J/ApJ/902/145', 'sources': sources, 'attempts': attempts,
               'observed_runtime': 'UNKNOWN', 'requested_runtime': 'gpt-6.1-sol/high'}
    with (HERE/'ACQUISITION_RECEIPT.json').open('x') as f:
        json.dump(receipt, f, indent=2)
        f.write('\n')
    return receipt


if __name__ == '__main__':
    acquire()
