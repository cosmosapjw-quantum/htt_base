"""Inspect the two frozen Quaia auxiliary products without extraction.

This small FITS reader accepts only the actual released single-column layout;
it is not a general astronomical FITS parser. Catalogue analysis uses Astropy.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
import numpy as np


def header(stream):
    result = {}
    while True:
        block = stream.read(2880)
        if len(block) != 2880:
            raise ValueError('Truncated FITS header')
        for offset in range(0, 2880, 80):
            card = block[offset:offset+80].decode('ascii')
            key = card[:8].strip()
            if key == 'END':
                return result
            if card[8:10] == '= ':
                value = card[10:].split('/')[0].strip()
                result[key] = value.strip("'").strip()


def summary(a):
    return {'shape':list(a.shape), 'dtype':str(a.dtype),
            'finite':int(np.isfinite(a).sum()), 'min':float(a.min()),
            'max':float(a.max()), 'negative':int((a<0).sum())}


def inspect(root):
    root = Path(root)
    fits = root/'selection_function_NSIDE64_G20.0.fits'
    archive = root/'selection_function_template_maps.zip'
    with fits.open('rb') as f:
        primary = header(f)
        if primary.get('NAXIS') != '0':
            raise ValueError('Unexpected primary data')
        h = header(f)
        expected = {'XTENSION':'BINTABLE','NAXIS1':'8192','NAXIS2':'48',
                    'TFIELDS':'1','TFORM1':'1024D','NSIDE':'64','ORDERING':'RING'}
        if any(h.get(k) != v for k,v in expected.items()):
            raise ValueError('Released-map layout changed')
        a = np.frombuffer(f.read(8192*48), dtype='>f8').copy()
        if a.size != 49152 or not np.isfinite(a).all():
            raise ValueError('Invalid map data')
    members = {}
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP CRC failure')
        for item in z.infolist():
            if item.is_dir():
                continue
            name = item.filename
            if not name.endswith('.npy'):
                raise ValueError('Unexpected member')
            # NumPy disallows object pickle execution; bytes are never extracted.
            value = np.load(io.BytesIO(z.read(name)), allow_pickle=False)
            if value.shape != (49152,) or not np.isfinite(value).all():
                raise ValueError('Template shape/finite check failed')
            members[name] = summary(value)
    return {'owner':'data source audit','scope':'Quaia v1.0.0 auxiliary inputs only',
            'claim_tier':'C0_SOURCE_SCHEMA','source':'https://zenodo.org/records/10403370',
            'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (fits,archive)},
            'map':{'header':h,'summary':summary(a)},'templates':members,
            'coordinate_header_present':'COORDSYS' in h,
            'qualification':'FORMAT_AND_SCHEMA_ONLY',
            'caveats':['Selection values are relative, not absolute inclusion probabilities',
                       'Some template entries are negative; never interpret all templates as counts or probabilities',
                       'Current pinned producer uses RA/DEC RING; release-time producer binding still to confirm',
                       'No physical selection likelihood, cross-source astrometric covariance or catalogue fit supplied']}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(inspect(a.data_root),indent=2)+'\n')
