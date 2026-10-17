"""Bounded, header-only structural integrity check for published PR3 SMICA FITS.

No astropy/healpy required. This is not a FITS science-content validator,
publisher cryptographic signature, or matched full-pipeline CMB null.
"""
from __future__ import annotations
from pathlib import Path
import re

BLOCK = 2880
CARD = 80
NPIX = 12 * 2048**2


def _read_header(f, offset: int, size: int):
    if offset % BLOCK or offset >= size:
        raise ValueError('FITS_HEADER_OFFSET')
    f.seek(offset)
    cards = []
    for _ in range(64):
        block = f.read(BLOCK)
        if len(block) != BLOCK:
            raise ValueError('FITS_TRUNCATED_HEADER')
        for i in range(0, BLOCK, CARD):
            card = block[i:i + CARD].decode('ascii', errors='strict')
            if card[:8].strip() == 'END':
                fields = {}
                for c in cards:
                    if c[8:10] != '= ':
                        continue
                    key = c[:8].strip()
                    value = c[10:].split('/', 1)[0].strip()
                    fields[key] = value.strip("' ")
                return fields, offset + (len(cards) // 36 + 1) * BLOCK
            cards.append(card)
    raise ValueError('FITS_HEADER_NO_END')


def _int(d, key):
    v = d.get(key)
    if not isinstance(v, str) or not re.fullmatch(r'[+-]?\d+', v):
        raise ValueError(f'FITS_INTEGER_{key}_INVALID')
    return int(v)


def _data_length(header):
    axes = _int(header, 'NAXIS')
    if axes == 0:
        return 0
    if axes != 2 or header.get('XTENSION') != 'BINTABLE':
        raise ValueError('FITS_UNSUPPORTED_HDU')
    row_bytes = _int(header, 'NAXIS1')
    rows = _int(header, 'NAXIS2')
    heap = _int(header, 'PCOUNT')
    groups = _int(header, 'GCOUNT')
    if min(row_bytes, rows) < 0 or heap < 0 or groups != 1:
        raise ValueError('FITS_INVALID_DATA_LENGTH')
    return row_bytes * rows + heap


def _hdu(f, offset, size):
    header, data_start = _read_header(f, offset, size)
    data_length = _data_length(header)
    padded = ((data_length + BLOCK - 1) // BLOCK) * BLOCK
    end = data_start + padded
    if end > size:
        raise ValueError('FITS_TRUNCATED_DATA_OR_MISSING_EXTENSION')
    return header, end, data_length


def _assert_equal(h, key, expected):
    observed = str(h.get(key, '')).strip()
    if observed != str(expected):
        raise ValueError(f'SMICA_HEADER_{key}_MISMATCH: {observed!r} != {expected!r}')


def inspect_smica_fits(path, product: str, *, expected_npix=NPIX, beam_rows=4097):
    """Verify primary+COMP-MAP and (full only) effective-beam HDUs and exact EOF.

    Small fixture controls are for tests only; published production defaults
    are frozen to NSIDE2048, 50,331,648 pixels and 4097 beam samples.
    """
    if product not in ('full', 'hm1', 'hm2', 'oe1', 'oe2'):
        raise ValueError('SMICA_PRODUCT_NOT_ALLOWED')
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError('SMICA_NOT_REGULAR_FILE')
    size = p.stat().st_size
    if size < BLOCK * 2 or size % BLOCK:
        raise ValueError('SMICA_SIZE_OR_FITS_PADDING')
    with p.open('rb') as f:
        primary, pos, plen = _hdu(f, 0, size)
        _assert_equal(primary, 'SIMPLE', 'T')
        _assert_equal(primary, 'NAXIS', 0)
        if plen:
            raise ValueError('SMICA_PRIMARY_NOT_EMPTY')
        component, pos, first_len = _hdu(f, pos, size)
        specs = {'full': (40, 10)}
        width, count = specs.get(product, (12, 3))
        for key, val in {
            'XTENSION':'BINTABLE','NAXIS1':width,'NAXIS2':expected_npix,
            'TFIELDS':count,'NSIDE':2048,'ORDERING':'NESTED',
            'COORDSYS':'GALACTIC','POLCCONV':'COSMO',
            'METHOD':'SMICA','PIXTYPE':'HEALPIX',
        }.items():
            _assert_equal(component, key, val)
        for i,label in enumerate(('I_STOKES','Q_STOKES','U_STOKES'),start=1):
            _assert_equal(component, f'TTYPE{i}', label)
            _assert_equal(component, f'TFORM{i}', '1E')
            _assert_equal(component, f'TUNIT{i}', 'K_CMB')
        if product == 'full':
            _assert_equal(component, 'TTYPE5', 'PMASK')
            beam, pos, beam_len = _hdu(f, pos, size)
            for key, val in {'XTENSION':'BINTABLE','NAXIS1':8,
                             'NAXIS2':beam_rows,'TFIELDS':2,
                             'TTYPE1':'INT_BEAM','TTYPE2':'POL_BEAM',
                             'TFORM1':'1E','TFORM2':'1E'}.items():
                _assert_equal(beam,key,val)
        else:
            beam_len = 0
        if pos != size:
            raise ValueError('SMICA_UNEXPECTED_TRAILING_HDU_OR_BYTES')
    return {'schema':'htt.PR3_SMICA_FITS_HDU_STRUCTURAL_AUDIT/1',
            'product':product,'bytes':size,'component_data_bytes':first_len,
            'beam_data_bytes':beam_len,
            'status':'COMPLETE_DECLARED_HDU_STRUCTURE',
            'scientific_validation':'NOT_EVALUATED'}
