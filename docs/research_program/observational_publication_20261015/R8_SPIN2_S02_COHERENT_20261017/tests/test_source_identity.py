from pathlib import Path
import hashlib
import sys
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from fits_source_identity import (audit_source_files, SourceIdentityError,
                                  inspect_planck_pmask, semantic_compare_pmask,
                                  classify_byte_semantic)


def card(key, value=None):
    if value is None:
        return f'{key:<8}'.ljust(80).encode('ascii')
    if isinstance(value, str):
        q = "'" + value + "'"
    elif isinstance(value, bool):
        q = 'T' if value else 'F'
    else:
        q = str(value)
    return f'{key:<8}= {q:<20}'.ljust(80).encode('ascii')


def block(cards):
    bs = b''.join(cards + [card('END')])
    return bs.ljust(((len(bs)+2879)//2880)*2880, b' ')


def write_mask(path, values, nside=1, date='2026-10-17', ordering='NESTED'):
    count=12*nside*nside
    assert len(values) == count
    primary=block([card('SIMPLE',True),card('BITPIX',32),card('NAXIS',0),card('EXTEND',True),card('DATE',date)])
    ext=block([card('XTENSION','BINTABLE'),card('BITPIX',8),card('NAXIS',2),
               card('NAXIS1',4),card('NAXIS2',count),card('PCOUNT',0),card('GCOUNT',1),
               card('TFIELDS',1),card('PIXTYPE','HEALPIX'),card('COORDSYS','GALACTIC'),
               card('ORDERING',ordering),card('NSIDE',nside),card('BAD_DATA',-1.6375e30),
               card('TTYPE1','PMASK'),card('TFORM1','1E'),card('TUNIT1','')])
    data=np.asarray(values,dtype='>f4').tobytes()
    path.write_bytes(primary+ext+data.ljust(((len(data)+2879)//2880)*2880,b'\x00'))
    return path


def test_original_oe_digest_is_malformed(tmp_path):
    dirname=tmp_path/'planck/PR3/masks';dirname.mkdir(parents=True)
    p=dirname/'OE.fits';write_mask(p,np.ones(12))
    r=audit_source_files(tmp_path, {'OE': 'OE.fits'}, {'OE': '1b2b4138f791b739938485fa0ebcac5f462e04aac3900'})
    assert r['OE']['byte_status']=='EXPECTED_DIGEST_MALFORMED'
    assert len(r['OE']['observed_sha256'])==64
    assert r['OE']['expected_digest_wellformed'] is False
    assert classify_byte_semantic(r['OE']['byte_status'],'SEMANTIC_NOT_EVALUATED')=='NOT_ADMITTED__SEMANTICS_UNRESOLVED'


def test_exact_source_bytes_admit_but_not_scientific_validation(tmp_path):
    d=tmp_path/'planck/PR3/masks';d.mkdir(parents=True)
    p=write_mask(d/'OE.fits',np.ones(12))
    r=audit_source_files(tmp_path, {'OE':'OE.fits'}, {'OE':hashlib.sha256(p.read_bytes()).hexdigest()},p.stat().st_size)
    assert r['OE']['byte_status']=='BYTE_IDENTICAL'
    assert classify_byte_semantic('BYTE_IDENTICAL','SEMANTIC_NOT_EVALUATED')=='ORIGINAL_BYTES_ADMITTED'


def test_valid_hash_bad_bytes_is_distinct(tmp_path):
    d=tmp_path/'planck/PR3/masks';d.mkdir(parents=True)
    p=write_mask(d/'OE.fits',np.ones(12))
    r=audit_source_files(tmp_path,{'OE':'OE.fits'},{'OE':'0'*64})
    assert r['OE']['byte_status']=='BYTE_SHA_MISMATCH'


def test_header_reserialization_semantically_same(tmp_path):
    data=np.arange(12,dtype=np.float32)/11
    a=write_mask(tmp_path/'a.fits',data,date='2018-01-01')
    b=write_mask(tmp_path/'b.fits',data,date='2026-10-17')
    assert hashlib.sha256(a.read_bytes()).digest()!=hashlib.sha256(b.read_bytes()).digest()
    assert inspect_planck_pmask(a,nside=1)['data_offset']==5760
    s=semantic_compare_pmask(a,b,nside=1,chunk_pixels=4)
    assert s['semantic_status']=='SEMANTIC_EQUIVALENT_PMASK'
    assert classify_byte_semantic('BYTE_SHA_MISMATCH',s['semantic_status']).startswith('ALTERNATE_BYTES')


def test_data_mutation_is_semantically_different(tmp_path):
    data=np.ones(12,dtype=np.float32)
    a=write_mask(tmp_path/'a.fits',data)
    data[7]=0.
    b=write_mask(tmp_path/'b.fits',data)
    s=semantic_compare_pmask(a,b,nside=1,chunk_pixels=4)
    assert s['semantic_status']=='SEMANTIC_DIFFERENT'
    assert s['first_different_pixel']==7


def test_changed_pixel_order_is_not_automatically_declared_equivalent(tmp_path):
    a=write_mask(tmp_path/'a.fits',np.ones(12))
    b=write_mask(tmp_path/'b.fits',np.ones(12),ordering='RING')
    with pytest.raises(ValueError,match='PMASK_LAYOUT_CONTRACT_MISMATCH'):
        semantic_compare_pmask(a,b,nside=1)


def test_invalid_mask_values_fail(tmp_path):
    a=write_mask(tmp_path/'a.fits',np.ones(12))
    x=np.ones(12,dtype=np.float32);x[1]=np.nan
    b=write_mask(tmp_path/'b.fits',x)
    assert semantic_compare_pmask(a,b,nside=1)['semantic_status']=='PMASK_VALUES_INVALID'


def test_truncation_detected(tmp_path):
    a=write_mask(tmp_path/'a.fits',np.ones(12))
    a.write_bytes(a.read_bytes()[:-1])
    with pytest.raises(ValueError, match='FITS_LENGTH_HDU_MISMATCH'):
        inspect_planck_pmask(a,nside=1)


def test_symlinks_not_accepted(tmp_path):
    d=tmp_path/'planck/PR3/masks';d.mkdir(parents=True)
    a=write_mask(tmp_path/'a.fits',np.ones(12))
    (d/'OE.fits').symlink_to(a)
    assert audit_source_files(tmp_path,{'OE':'OE.fits'},{'OE':'0'*64})['OE']['byte_status']=='INPUT_MISSING_OR_SYMLINK'


def test_main_native_guard_compatible_mock_and_typed_audit(tmp_path):
    from native_planck_pol_response import verify_native_files, audit_native_identity
    d=tmp_path/'planck/PR3/masks';d.mkdir(parents=True)
    a=write_mask(d/'OE.fits',np.ones(12))
    r=verify_native_files(tmp_path,files={'OE':'OE.fits'},
                          sha={'OE':hashlib.sha256(a.read_bytes()).hexdigest()},
                          expected_size=a.stat().st_size)
    assert r['OE']['source_size_bytes']==a.stat().st_size
    with pytest.raises(SourceIdentityError) as err:
        verify_native_files(tmp_path,files={'OE':'OE.fits'},
                            sha={'OE':'1b2b4138f791b739938485fa0ebcac5f462e04aac3900'},
                            expected_size=a.stat().st_size)
    assert err.value.receipt['OE']['byte_status']=='EXPECTED_DIGEST_MALFORMED'
    aud=audit_native_identity(tmp_path,files={'OE':'OE.fits'},
                              sha={'OE':'1b2b4138f791b739938485fa0ebcac5f462e04aac3900'},
                              expected_size=a.stat().st_size,nside=1)
    assert aud['OE']['byte_status']=='EXPECTED_DIGEST_MALFORMED'
    assert aud['OE']['structural_status']=='PLANCK_PMASK_LAYOUT_VALID'
    assert aud['OE']['semantic_status']=='SEMANTIC_NOT_EVALUATED_NO_REFERENCE'
    assert aud['OE']['admission']=='NOT_ADMITTED__SEMANTICS_UNRESOLVED'
