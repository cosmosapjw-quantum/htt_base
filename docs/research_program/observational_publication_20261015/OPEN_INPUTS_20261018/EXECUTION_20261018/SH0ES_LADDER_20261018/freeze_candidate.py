"""Freeze only this bounded review bundle; exclude later review records."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent


def main():
    destination = HERE/'CANDIDATE.json'
    if destination.exists():
        raise SystemExit('candidate already frozen')
    records = []
    for path in sorted(HERE.iterdir()):
        if path.is_file() and path.name != destination.name and 'REVIEW' not in path.name:
            records.append({'name':path.name,'bytes':path.stat().st_size,
                            'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    encoded = json.dumps(records,sort_keys=True,separators=(',',':')).encode()
    candidate = dict(scope='SH0ES_LADDER_20261018 only',owner='htt',claim_tier='C0',
                     requested_runtime='gpt-6.1-sol/high',observed_runtime='UNKNOWN',
                     observed_head=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
                     status='FROZEN_FOR_INDEPENDENT_READ_ONLY_REVIEW',files=records,
                     bundle_sha256=hashlib.sha256(encoded).hexdigest())
    destination.write_text(json.dumps(candidate,indent=2)+'\n')
    print(json.dumps(candidate,indent=2))


if __name__ == '__main__':
    main()
