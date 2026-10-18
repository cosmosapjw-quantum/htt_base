"""Fetch only primary source documentation; never execute upstream code."""
from pathlib import Path
import hashlib
import json
import urllib.request

ROOT = Path('/mnt/extdrive/workdir/htt_open_data/pantheonplus/shoes_ladder_20261018')
COMMIT = 'c447f0fea703fcd0fff57de5000947b5ca81286b'

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    urls = {'reanalysis_2208.11169v3.html': 'https://arxiv.org/html/2208.11169v3'}
    for name in ('read_chains_example.py', 'MCMC_utils.py'):
        urls[name] = f'https://raw.githubusercontent.com/PantheonPlusSH0ES/DataRelease/{COMMIT}/SH0ES_Data/{name}'
    records = []
    for name, url in urls.items():
        path = ROOT / name
        if not path.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                data = response.read()
            path.write_bytes(data)
        data = path.read_bytes()
        records.append(dict(path=str(path), url=url, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    (ROOT / 'ACQUISITION.json').write_text(json.dumps(records, indent=2)+'\n')
    print(json.dumps(records, indent=2))

if __name__ == '__main__':
    main()
