"""Bounded, pinned-tree-only acquisition. Never executes upstream files."""
from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path('/mnt/extdrive/workdir/htt_open_data/pantheonplus/source_null_20261018')
REUSE = ROOT.parent / 'c447f0f/SIM_0001.FITRES.gz'
RELEASE = 'c447f0fea703fcd0fff57de5000947b5ca81286b'
CAP = 20_000_000
OUT = Path(__file__).resolve().parent


def identity(path):
    data = path.read_bytes()
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'git_blob': hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()}


def main():
    receipt_path = OUT / 'acquisition.json'
    if receipt_path.exists():
        raise RuntimeError('Existing receipt: preserve and reconcile; no automatic re-download')
    tree = json.loads((ROOT / 'datarelease_tree.json').read_text())
    assert not tree['truncated']
    framing = [{'local': str(p), **identity(p)} for p in sorted(ROOT.rglob('*')) if p.is_file()]
    entries = [x for x in tree['tree'] if x['type'] == 'blob' and
               x['path'].startswith('Pantheon+_Data/6_SIMULATIONS/') and
               (re.search(r'LCFITS/SIM_\d{4}\.FITRES\.gz$', x['path']) or
                x['path'].endswith('_HEAD.FITS.gz') or x['path'].endswith('/SIMLOGS.tar.gz'))]
    assert sum(x['path'].endswith('.FITRES.gz') for x in entries) == 10
    assert sum(x['path'].endswith('_HEAD.FITS.gz') for x in entries) == 50
    byblob = {x['git_blob']: x['local'] for x in framing}
    reused = identity(REUSE)
    assert reused['sha256'] == '2a26a338dfe2549b969ef57c98e0f429cc4d0c798d045d4b72a44f7146e3ca2b'
    byblob[reused['git_blob']] = str(REUSE)
    used = sum(x['size'] for x in framing) + reused['size']
    # Reuse is accounted once, not as a new HTTP transfer.
    receipt = {'release': RELEASE, 'cap_bytes': CAP, 'framing': framing,
               'reused_fitres': {'local': str(REUSE), **reused},
               'initial_unique_source_bytes': used, 'http_body_bytes': 0,
               'entries': [], 'requested_model': 'gpt-6.1-sol/high', 'observed_runtime': 'UNKNOWN'}

    def save():
        receipt['charged_source_bytes'] = used
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')

    save()
    for entry in entries:
        item = dict(entry)
        if entry['sha'] in byblob:
            path = Path(byblob[entry['sha']])
            item.update(local=str(path), disposition='REUSED_NO_HTTP', **identity(path))
        else:
            if used + entry['size'] > CAP:
                receipt['status'] = 'HOLD_CAP'; save(); raise RuntimeError('Acquisition cap')
            url = ('https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/' + RELEASE + '/' +
                   urllib.parse.quote(entry['path'], safe='/'))
            dest = ROOT / 'release' / entry['path']
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                raise RuntimeError(f'Unreconciled existing file {dest}')
            item.update(local=str(dest), url=url, disposition='HTTP', start_utc=time.time())
            # No retries: failed/transferred bytes remain charged and visible.
            try:
                with urllib.request.urlopen(url, timeout=45) as response, dest.open('xb') as f:
                    item['http_status'] = response.status
                    item['http_headers'] = dict(response.headers)
                    n = 0
                    while True:
                        chunk = response.read(min(65536, CAP - used + 1))
                        if not chunk:
                            break
                        n += len(chunk); used += len(chunk)
                        receipt['http_body_bytes'] += len(chunk)
                        f.write(chunk)
                        if used > CAP:
                            raise RuntimeError('Actual HTTP exceeded hard cap')
                item.update(identity(dest)); item['actual_http_body_bytes'] = n
                assert item['size'] == entry['size'], (entry['path'], item['size'], entry['size'])
                assert item['git_blob'] == entry['sha'], entry['path']
                byblob[entry['sha']] = str(dest)
            except Exception as exc:
                item['error'] = repr(exc); receipt['entries'].append(item)
                receipt['status'] = 'FIRST_FAILURE'; save(); raise
        if item['path'].endswith('.gz'):
            assert Path(item['local']).read_bytes()[:2] == b'\x1f\x8b'
            with gzip.open(item['local'], 'rb') as stream:
                first = stream.read(160)
            item['decompressed_magic'] = first[:32].decode('ascii', errors='replace')
            if item['path'].endswith('_HEAD.FITS.gz'):
                assert first.startswith(b'SIMPLE  =')
            elif item['path'].endswith('.FITRES.gz'):
                assert b'#' in first or b'VARNAMES:' in first
        receipt['entries'].append(item); save()
        print(len(receipt['entries']), entry['path'].split('/')[-1], item['disposition'], used, flush=True)
    receipt['status'] = 'ACQUIRED_PINNED_BLOBS'
    receipt['new_unique_bytes'] = used - receipt['initial_unique_source_bytes']
    save()


if __name__ == '__main__':
    main()
