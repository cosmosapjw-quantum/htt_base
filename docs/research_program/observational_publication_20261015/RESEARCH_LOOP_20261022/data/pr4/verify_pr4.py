"""Read-only transport, schema, and pixel-integrity intake for two observed PR4 maps."""

from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

import numpy as np
from astropy.io import fits


HERE = Path(__file__).resolve().parent.parent
ROOT = Path('/mnt/extdrive/workdir/htt_open_data/research20261022')
IDS = {'PR4_LFI30_OBS_YEAR13', 'PR4_LFI30_OBS_YEAR24', 'PR4_LOLLIPOP_NS16_MASK'}
ARCHIVE_ID = 'PR4_RIMO_TF_ARCHIVE'
BEAM_MEMBERS = {
    'Bl_TEB': 'simulated_maps/npipe_aux/beam_window_functions/AB/Bl_TEB_npipe6v20_030Ax030B.fits',
    'Wl': 'simulated_maps/npipe_aux/beam_window_functions/AB/Wl_npipe6v20_030Ax030B.fits',
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def inspect(spec: dict) -> dict:
    path = ROOT / spec['path']
    receipt = json.loads(Path(str(path) + '.receipt.json').read_text())
    assert path.stat().st_size == spec['expected_bytes'] == receipt['bytes']
    assert receipt['sha256'] == sha256(path) and receipt['url'] == spec['url']
    assert path.stat().st_size % 2880 == 0
    result = {'id': spec['id'], 'path': str(path), 'bytes': path.stat().st_size,
              'sha256': receipt['sha256'], 'url': receipt['url']}
    with fits.open(path, memmap=True, checksum=False) as hdus:
        assert len(hdus) >= 2 and isinstance(hdus[1], fits.BinTableHDU)
        hdr = hdus[1].header
        result['schema'] = {'naxis1': hdr['NAXIS1'], 'naxis2': hdr['NAXIS2'],
                            'tfields': hdr['TFIELDS'], 'nside': hdr['NSIDE'],
                            'ordering': hdr['ORDERING'].strip(),
                            'coordsys': hdr['COORDSYS'].strip(),
                            'pixtype': hdr['PIXTYPE'].strip()}
        assert result['schema']['pixtype'] == 'HEALPIX'
        assert result['schema']['coordsys'] == 'G'
        if spec['id'] == 'PR4_LOLLIPOP_NS16_MASK':
            assert (hdr['NSIDE'], hdr['NAXIS2'], hdr['TFIELDS'], hdr['ORDERING'].strip()) == (16, 3, 1, 'RING')
            assert hdr['TTYPE1'].strip() == 'T' and hdr['TFORM1'].strip() == '1024E'
            counts = {'pixels': 0, 'finite': 0, 'zero': 0, 'one': 0, 'other_finite': 0}
            for start in range(0, len(hdus[1].data), 256):
                x = np.asarray(hdus[1].data['T'][start:start + 256]).reshape(-1)
                good = np.isfinite(x)
                counts['pixels'] += x.size
                counts['finite'] += int(good.sum())
                counts['zero'] += int(np.count_nonzero(x == 0))
                counts['one'] += int(np.count_nonzero(x == 1))
                counts['other_finite'] += int(np.count_nonzero(good & (x != 0) & (x != 1)))
            assert counts['pixels'] == 12 * 16**2
            result['mask_counts'] = counts
        else:
            assert (hdr['NSIDE'], hdr['NAXIS2'], hdr['TFIELDS'], hdr['ORDERING'].strip()) == (1024, 12288, 10, 'NESTED')
            assert hdr['NAXIS1'] == 40960
            split = 'A' if spec['id'] == 'PR4_LFI30_OBS_YEAR13' else 'B'
            assert hdr['FREQ'] == 30 and hdr['POLCCONV'].strip() == 'COSMO'
            assert f'npipe6v20{split}_030_map.fits' in str(hdr['COMMENT'])
            result['producer_split'] = f'npipe6v20{split}'
            result['polarization_convention'] = hdr['POLCCONV'].strip()
            fields = [hdr[f'TTYPE{i}'].strip() for i in range(1, 11)]
            assert fields[:3] == ['I_STOKES', 'Q_STOKES', 'U_STOKES']
            assert all(hdr[f'TFORM{i}'].strip() == '1024E' for i in (1, 2, 3))
            assert all(hdr[f'TUNIT{i}'].strip() == 'K_CMB' for i in (1, 2, 3))
            bad = float(np.float32(hdr['BAD_DATA']))
            result['fields'] = fields
            result['stokes_unit'] = 'K_CMB'
            result['bad_data_sentinel'] = bad
            counts = {k: {'pixels': 0, 'finite': 0, 'non_sentinel_finite': 0,
                          'nan_or_inf': 0} for k in fields[:3]}
            for start in range(0, len(hdus[1].data), 256):
                for field in fields[:3]:
                    x = np.asarray(hdus[1].data[field][start:start + 256]).reshape(-1)
                    good = np.isfinite(x)
                    counts[field]['pixels'] += x.size
                    counts[field]['finite'] += int(good.sum())
                    counts[field]['non_sentinel_finite'] += int(np.count_nonzero(good & (x != bad)))
                    counts[field]['nan_or_inf'] += int((~good).sum())
            assert all(v['pixels'] == 12 * 1024**2 for v in counts.values())
            result['stokes_counts'] = counts
    return result


def inspect_archive(spec: dict) -> dict:
    path = ROOT / spec['path']
    receipt = json.loads(Path(str(path) + '.receipt.json').read_text())
    assert path.stat().st_size == spec['expected_bytes'] == receipt['bytes']
    assert sha256(path) == receipt['sha256'] and receipt['url'] == spec['url']
    result = {'id': spec['id'], 'path': str(path), 'bytes': path.stat().st_size,
              'sha256': receipt['sha256'], 'url': receipt['url'], 'members': {}}
    with tarfile.open(path, 'r:gz') as archive:
        result['tar_member_count'] = len(archive.getmembers())
        for kind, name in BEAM_MEMBERS.items():
            member = archive.getmember(name)
            assert member.isfile()
            payload = archive.extractfile(member).read()
            assert len(payload) == member.size
            fields = {}
            with fits.open(io.BytesIO(payload), memmap=False, checksum=False) as hdus:
                if kind == 'Bl_TEB':
                    assert len(hdus) == 2 and hdus[1].header['NAXIS2'] == 4097
                    assert hdus[1].columns.names == ['T', 'E', 'B']
                else:
                    assert [h.name for h in hdus[1:]] == ['TT', 'EE', 'BB', 'TE']
                    assert all(h.header['TFIELDS'] == 9 for h in hdus[1:])
                for hdu in hdus[1:]:
                    for field in hdu.columns.names:
                        values = np.asarray(hdu.data[field])
                        assert values.size == 4097 and np.isfinite(values).all()
                        fields[hdu.name + ':' + field] = int(values.size)
            result['members'][kind] = {'name': name, 'bytes': member.size,
                                       'sha256': hashlib.sha256(payload).hexdigest(),
                                       'finite_fields': fields}
    return result


def main() -> None:
    manifest = json.loads((HERE / 'ACQUISITION_MANIFEST.json').read_text())
    specs = [x for x in manifest['resources'] if x['id'] in IDS]
    assert {x['id'] for x in specs} == IDS
    archive = next(x for x in manifest['resources'] if x['id'] == ARCHIVE_ID)
    print(json.dumps({'qualification': 'TRANSPORT_SCHEMA_PIXEL_ONLY',
                      'resources': [inspect(spec) for spec in specs],
                      'archive': inspect_archive(archive)}, indent=2))


if __name__ == '__main__':
    main()
