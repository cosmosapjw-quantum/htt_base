"""Acquire fixed primary source bytes only; never execute upstream code."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

STORE = Path('/mnt/extdrive/workdir/htt_open_data/moving_lens_20261018')


def acquire():
    STORE.mkdir(parents=True, exist_ok=True)
    receipts = []
    for name, url in [('2605.18938v1.html', 'https://arxiv.org/html/2605.18938v1'),
                      ('2605.18938v1.pdf', 'https://arxiv.org/pdf/2605.18938v1')]:
        path = STORE / name
        if path.exists():
            raise FileExistsError(f'Preserve existing acquisition: {path}')
        with urlopen(Request(url, headers={'User-Agent': 'HTT-source-research/1.0'}), timeout=45) as response:
            payload = response.read()
            final_url = response.url
            content_type = response.headers.get('Content-Type')
        if name.endswith('.pdf') and not payload.startswith(b'%PDF-'):
            raise ValueError('Expected PDF source')
        path.write_bytes(payload)
        receipts.append(dict(path=str(path), source_url=url, final_url=final_url,
                             content_type=content_type, bytes=len(payload),
                             sha256=hashlib.sha256(payload).hexdigest(),
                             acquired_utc=datetime.now(timezone.utc).isoformat()))
    receipt = dict(source_release='arXiv:2605.18938v1', raw_source_outside_git=True,
                   upstream_code_executed=False, sources=receipts)
    (STORE / 'ACQUISITION.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    acquire()
