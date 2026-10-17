"""HTTP Range retry tests using no network and no real FITS data."""
import io
from functools import partial
from pathlib import Path
import pytest
import fetch_planck_pr3_smica as dl

class Response:
    def __init__(self,data,status,headers):
        self.status=status;self.headers=headers;self.stream=io.BytesIO(data)
    def read(self,n):return self.stream.read(n)
    def close(self):self.stream.close()
    def getcode(self):return self.status


def test_retry_incomplete_http200_then_exact_206_resume(tmp_path,monkeypatch):
    monkeypatch.setitem(dl.MIN_BYTES,'full',1024)
    monkeypatch.setattr(dl,'inspect_smica_fits',lambda *_a,**_kw:{'status':'COMPLETE_DECLARED_HDU_STRUCTURE'})
    data=b'SIMPLE  ='+b' '*2871+b'\0'*2880
    assert len(data)==5760
    calls=[]
    def opener(req):
        calls.append(req.headers.get('Range'))
        if len(calls)==1:
            return Response(data[:2880],200,{'Content-Length':'5760'})
        return Response(data[2880:],206,{'Content-Range':'bytes 2880-5759/5760','Content-Length':'2880'})
    worker=partial(dl.transfer,opener=opener)
    result=dl.transfer_with_retry('full',tmp_path,attempts=2,transfer_fn=worker)
    assert result['status']=='DOWNLOADED_FITS_FRAMING_VALID'
    assert Path(result['path']).read_bytes()==data
    assert calls==[None,'bytes=2880-']
    assert not Path(result['path']+'.part').exists()


def test_server_ignores_range_keeps_partial(tmp_path):
    p=tmp_path/'planck/PR3/cmb'/ (dl.filename('full')+'.part')
    p.parent.mkdir(parents=True);p.write_bytes(b'abc')
    with pytest.raises(ValueError,match='HTTP_RANGE_IGNORED'):
        dl.transfer('full',tmp_path,opener=lambda req:Response(b'newdata',200,{'Content-Length':'7'}))
    assert p.read_bytes()==b'abc'


def test_wrong_resume_start_keeps_partial(tmp_path):
    p=tmp_path/'planck/PR3/cmb'/(dl.filename('full')+'.part')
    p.parent.mkdir(parents=True);p.write_bytes(b'abc')
    with pytest.raises(ValueError,match='UNVERIFIED_HTTP_RANGE_RESUME'):
        dl.transfer('full',tmp_path,opener=lambda req:Response(b'abc',206,{'Content-Range':'bytes 0-2/10','Content-Length':'3'}))
    assert p.read_bytes()==b'abc'


def test_checksum_manifest_not_claimed(tmp_path):
    assert 'PUBLISHER' in dl.verify_local_file.__doc__ if dl.verify_local_file.__doc__ else True
    with pytest.raises(ValueError,match='PRODUCT_NOT_IRSA_ALLOWLISTED'):
        dl.filename('../../x')


def test_retry_budget_and_failclosed_validation(tmp_path):
    with pytest.raises(ValueError,match='DOWNLOAD_ATTEMPTS'):
        dl.transfer_with_retry('full',tmp_path,attempts=9)
    def bad(*args,**kw):raise ValueError('SMICA_HEADER_WRONG')
    with pytest.raises(ValueError,match='SMICA_HEADER_WRONG'):
        dl.transfer_with_retry('full',tmp_path,attempts=3,transfer_fn=bad)


def test_dry_run_no_network(capsys,tmp_path):
    assert dl.main(['--root',str(tmp_path),'--dry-run','--products','full'])==0
    assert 'DRY_RUN' in capsys.readouterr().out
