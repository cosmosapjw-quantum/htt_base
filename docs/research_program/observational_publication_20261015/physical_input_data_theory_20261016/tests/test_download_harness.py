import io,json,os
from pathlib import Path
import pytest
from scripts.htt_data_fetch import secure_dest,validate_url,detect_payload,digest,copy_fetch,main

def test_url_restrictions():
    validate_url('https://irsa.ipac.caltech.edu/data/x.fits')
    for url in ['http://irsa.ipac.caltech.edu/x','https://evil.example/path','file:///tmp/file']:
        with pytest.raises(ValueError):validate_url(url)

def test_path_traversal(tmp_path):
    for x in ['../evil','/etc/passwd','a/../../b']:
        with pytest.raises(ValueError):secure_dest(tmp_path,x)
    assert secure_dest(tmp_path,'a/b').is_relative_to(tmp_path)

def test_html_rejected(tmp_path):
    bad=tmp_path/'bad.fits';bad.write_bytes(b'<html>404</html>')
    with pytest.raises(ValueError):detect_payload(bad,'fits')

def test_fits_magic(tmp_path):
    fits=tmp_path/'correct.fits';fits.write_bytes(b'SIMPLE  = '+b' '*5000)
    detect_payload(fits,'fits')
    assert len(digest(fits))==64

def test_planck_registry(tmp_path):
    reg=Path(__file__).resolve().parents[1]/'DATA_REGISTRY.json'
    r=json.loads(reg.read_text())
    assert len(r['items'])>=15
    assert any(x['id']=='smica_nosz_I_only' and 'NO Q/U' in x['scientific_scope'] for x in r['items'])
    assert main(['--registry',str(reg),'--root',str(tmp_path),'--dry-run'])==0

def test_failclosed_existing_unverified(tmp_path):
    dst=tmp_path/'cf4';dst.mkdir();(dst/'raw.txt').write_text('unknown')
    with pytest.raises(ValueError):copy_fetch({'id':'z','path':'cf4/raw.txt','url':'https://cdsarc.cds.unistra.fr/file','format':'ascii'},tmp_path,{},0,5)

def test_mock_https_download_and_verify(tmp_path,monkeypatch):
    class Response(io.BytesIO):
        status=200
        headers={'Content-Type':'application/fits'}
        def __enter__(self):return self
        def __exit__(self,*args):self.close()
        def geturl(self):return 'https://irsa.ipac.caltech.edu/f.fits'
    def fake_urlopen(req,timeout):return Response(b'SIMPLE  = '+b' '*4300)
    monkeypatch.setattr('scripts.htt_data_fetch.request.urlopen',fake_urlopen)
    item={'id':'f','path':'planck/f.fits','url':'https://irsa.ipac.caltech.edu/f.fits','format':'fits','min_bytes':80}
    copy_fetch(item,tmp_path,{},0,20)
    assert (tmp_path/'planck/f.fits').is_file()
    r=json.loads((tmp_path/'provenance/DOWNLOAD_RECEIPTS.json').read_text())
    assert r['f']['sha256']==digest(tmp_path/'planck/f.fits')
    assert r['f']['source_validation'].endswith('NOT validated')
    assert main(['--registry',str((Path(__file__).parents[1]/'DATA_REGISTRY.json')),'--root',str(tmp_path),'--id','smica_full','--verify'])==2


def test_resume_206_is_not_duplicated(tmp_path,monkeypatch):
    url='https://irsa.ipac.caltech.edu/a.fits'
    item={'id':'a','path':'planck/a.fits','url':url,'format':'fits','min_bytes':40}
    d=tmp_path/'planck';d.mkdir()
    prefix=b'SIMPLE  = '+b' '*300
    suffix=b' '*800
    (d/'a.fits.part').write_bytes(prefix)
    class Response(io.BytesIO):
        status=206
        headers={'Content-Range':f'bytes {len(prefix)}-{len(prefix)+len(suffix)-1}/{len(prefix)+len(suffix)}','Content-Type':'application/fits'}
        def __enter__(self):return self
        def __exit__(self,*args):self.close()
        def geturl(self):return url
    def fake(req,timeout):
        assert req.headers['Range']==f'bytes={len(prefix)}-'
        return Response(suffix)
    monkeypatch.setattr('scripts.htt_data_fetch.request.urlopen',fake)
    copy_fetch(item,tmp_path,{},0,30)
    assert (d/'a.fits').read_bytes()==prefix+suffix
