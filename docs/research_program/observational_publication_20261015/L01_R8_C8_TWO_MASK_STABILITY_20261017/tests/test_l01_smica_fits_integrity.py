"""Independent miniature FITS framing controls, not actual 2GB Planck input."""
from pathlib import Path
import pytest
from l01_smica_fits_integrity import inspect_smica_fits


def _header(cards):
    lines=[]
    for name,value in cards.items():
        formatted=f"'{value}'" if isinstance(value,str) and value!='T' else str(value)
        lines.append(f'{name:<8}= {formatted:<20}'.ljust(80).encode('ascii'))
    lines.append('END'.ljust(80).encode('ascii'))
    x=b''.join(lines)
    return x+b' '*(-len(x)%2880)


def _hdu(cards,data=b''):
    return _header(cards)+data+b'\0'*(-len(data)%2880)


def synthetic_smica(*,product='full',beam=True,change=None):
    primary={'SIMPLE':'T','BITPIX':32,'NAXIS':0,'EXTEND':'T'}
    nfields=10 if product=='full' else 3
    comp={'XTENSION':'BINTABLE','BITPIX':8,'NAXIS':2,'NAXIS1':nfields*4,
        'NAXIS2':12,'PCOUNT':0,'GCOUNT':1,'TFIELDS':nfields,
        'NSIDE':2048,'ORDERING':'NESTED','COORDSYS':'GALACTIC',
        'POLCCONV':'COSMO','METHOD':'SMICA','PIXTYPE':'HEALPIX'}
    for i,k in enumerate(('I_STOKES','Q_STOKES','U_STOKES'),1):
        comp[f'TTYPE{i}']=k;comp[f'TFORM{i}']='1E';comp[f'TUNIT{i}']='K_CMB'
    if product=='full':comp['TTYPE5']='PMASK'
    if change:comp.update(change)
    ret=_hdu(primary)+_hdu(comp,b'\0'*(12*nfields*4))
    if product=='full' and beam:
        beam_header={'XTENSION':'BINTABLE','BITPIX':8,'NAXIS':2,'NAXIS1':8,
            'NAXIS2':9,'PCOUNT':0,'GCOUNT':1,'TFIELDS':2,
            'TTYPE1':'INT_BEAM','TTYPE2':'POL_BEAM','TFORM1':'1E','TFORM2':'1E'}
        ret+=_hdu(beam_header,b'\0'*(8*9))
    return ret


def test_correct_full_and_split(tmp_path):
    for product in ('full','hm1','oe2'):
        p=tmp_path/f'{product}.fits';p.write_bytes(synthetic_smica(product=product))
        r=inspect_smica_fits(p,product,expected_npix=12,beam_rows=9)
        assert r['status']=='COMPLETE_DECLARED_HDU_STRUCTURE'
        assert r['component_data_bytes']==12*(40 if product=='full' else 12)
        assert r['beam_data_bytes']==(8*9 if product=='full' else 0)


def test_missing_beam_extension_fails_closed(tmp_path):
    p=tmp_path/'x.fits';p.write_bytes(synthetic_smica(beam=False))
    with pytest.raises(ValueError,match='FITS_HEADER_OFFSET'):
        inspect_smica_fits(p,'full',expected_npix=12,beam_rows=9)


def test_beam_truncation_rejected(tmp_path):
    p=tmp_path/'x.fits';p.write_bytes(synthetic_smica()[:-2880])
    with pytest.raises(ValueError,match='TRUNCATED_DATA'):
        inspect_smica_fits(p,'full',expected_npix=12,beam_rows=9)


def test_semantic_header_mismatch_rejected(tmp_path):
    p=tmp_path/'x.fits';p.write_bytes(synthetic_smica(change={'POLCCONV':'IAU'}))
    with pytest.raises(ValueError,match='SMICA_HEADER_POLCCONV'):
        inspect_smica_fits(p,'full',expected_npix=12,beam_rows=9)


def test_correct_fits_plus_unexpected_extra_hdu_rejected(tmp_path):
    p=tmp_path/'x.fits';p.write_bytes(synthetic_smica()+b' '*2880)
    with pytest.raises(ValueError,match='UNEXPECTED_TRAILING'):
        inspect_smica_fits(p,'full',expected_npix=12,beam_rows=9)
