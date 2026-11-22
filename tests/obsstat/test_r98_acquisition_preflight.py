"""R98 bounded acquisition: partial integrity, exact range and metadata semantics."""
import hashlib
import io
from pathlib import Path

import pytest
from astropy.io import fits

from scripts.r98 import acquisition_preflight as acq


class Reply(io.BytesIO):
    def __init__(self, payload, status=200, headers=None):
        super().__init__(payload)
        self.status=status
        self.headers=headers or {}


@pytest.fixture
def source(monkeypatch,tmp_path):
    body=b"verified-payload"
    name="test-release.bin"
    monkeypatch.setattr(acq,"DEST",tmp_path)
    monkeypatch.setitem(acq.ALLOWLIST,name,(len(body),hashlib.md5(body).hexdigest()))
    return acq.archive_job(name),body,tmp_path/(name+".partial")


def no_request(*args,**kwargs):
    raise AssertionError("unexpected network request")


def test_complete_partial_is_verified_without_range(source,monkeypatch):
    job,body,part=source
    part.write_bytes(body)
    monkeypatch.setattr(acq,"urlopen",no_request)
    result=acq.download(job,len(body))
    assert result["status"]=="VALIDATED_COMPLETE_PARTIAL"
    assert Path(result["path"]).read_bytes()==body
    assert acq.download(job,len(body))["sha256"]==hashlib.sha256(body).hexdigest()


def test_corrupt_complete_partial_preserved_without_range(source,monkeypatch):
    job,body,part=source
    bad=b"x"*len(body)
    part.write_bytes(bad)
    monkeypatch.setattr(acq,"urlopen",no_request)
    with pytest.raises(ValueError,match="MD5"):
        acq.download(job,len(body))
    assert part.read_bytes()==bad


@pytest.mark.parametrize("code,content_range",[(200,None),(206,"bytes 4-15/16"),(206,"bytes 3-14/16"),(206,"bytes 3-15/17")])
def test_invalid_range_never_appends(source,monkeypatch,code,content_range):
    job,body,part=source
    part.write_bytes(body[:3])
    monkeypatch.setattr(acq,"urlopen",lambda *a,**kw:Reply(body[3:],code,{"Content-Range":content_range}))
    with pytest.raises(ValueError,match="resume not honored"):
        acq.download(job,len(body))
    assert part.read_bytes()==body[:3]


def test_exact_resume_validates_full_object(source,monkeypatch):
    job,body,part=source
    part.write_bytes(body[:3])
    def opened(req,timeout):
        assert req.get_header("Range")=="bytes=3-"
        return Reply(body[3:],206,{"Content-Range":f"bytes 3-{len(body)-1}/{len(body)}"})
    monkeypatch.setattr(acq,"urlopen",opened)
    assert acq.download(job,len(body))["sha256"]==hashlib.sha256(body).hexdigest()


def test_budget_and_fresh_length_guard(source,monkeypatch):
    job,body,part=source
    monkeypatch.setattr(acq,"urlopen",no_request)
    with pytest.raises(ValueError,match="budget"):
        acq.download(job,len(body)-1)
    monkeypatch.setattr(acq,"urlopen",lambda *a,**kw:Reply(body+b"!"))
    with pytest.raises(ValueError,match="exceeds"):
        acq.download(job,len(body))
    assert not (acq.DEST/job["id"]).exists()


def test_commander_prefix_identity_filename_and_bounded_read(monkeypatch,tmp_path):
    name=acq.COMMANDER_IDS[1]
    ext=fits.Header()
    fields={"XTENSION":"BINTABLE","NSIDE":2048,"ORDERING":"RING","TFIELDS":3,"NAXIS1":12288,"NAXIS2":49152}
    for i,col in enumerate(("INTENSITY","Q-POLARISATION","U-POLARISATION"),1):
        fields.update({f"TTYPE{i}":col,f"TFORM{i}":"1024E",f"TUNIT{i}":"K_CMB"})
    for key,value in fields.items():ext[key]=value
    primary=fits.Header()
    primary["SIMPLE"]=True
    b=(primary.tostring()+ext.tostring()).encode("ascii")
    class Bounded(Reply):
        def read(self,n=-1):
            assert n==5760
            return super().read(n)
    monkeypatch.setattr(acq,"COMMANDER_RAW",tmp_path)
    def probe(req,timeout):
        assert req.get_header("Range")=="bytes=0-5759"
        return Bounded(b+b"untransferred payload",200,{"Content-Disposition":f'inline; filename="{name}"'})
    monkeypatch.setattr(acq,"urlopen",probe)
    result=acq.commander_probe(name)
    assert result["header_bytes"]==5760 and result["range_honored"] is False
    assert result["status"]=="HEADER_VERIFIED_ONLY" and result["full_payload_sha256"] is None
    monkeypatch.setattr(acq,"urlopen",lambda *a,**kw:Bounded(b,200,{"Content-Disposition":"inline; filename=wrong.fits"}))
    with pytest.raises(ValueError,match="wrong Commander"):
        acq.commander_probe(name)


def test_unbound_commander_partial_never_publishes(monkeypatch,tmp_path):
    monkeypatch.setattr(acq,"DEST",tmp_path)
    monkeypatch.setattr(acq,"urlopen",no_request)
    job=acq.archive_job(acq.COMMANDER_IDS[1])
    (tmp_path/(job["id"]+".partial")).write_bytes(b"unbound prefix")
    with pytest.raises(ValueError,match="trusted full-object"):
        acq.download(job,job["bytes"])

def test_lotss_probe_reads_only_actual_table_header(tmp_path,monkeypatch):
    import numpy as np
    local=tmp_path/acq.LOTSS_NAME
    ext=fits.BinTableHDU.from_columns([fits.Column(name="id",array=np.arange(3),format="K")],
                                      name="LoTSS_DR3_srl")
    fits.HDUList([fits.PrimaryHDU(),ext]).writeto(local)
    with fits.open(local) as hdul:
        info=hdul[1].fileinfo()
        start,end=info["hdrLoc"],info["datLoc"]
    raw=local.read_bytes()
    content_range=f"bytes {start}-{end-1}/{len(raw)}"
    class HeaderOnly(Reply):
        def read(self,n=-1):
            assert 0<n<=2880 and self.tell()+n<=end-start
            return super().read(n)
    def opened(req,timeout):
        assert req.get_header("Range")==f"bytes={start}-{end-1}"
        return HeaderOnly(raw[start:end],206,{"Content-Range":content_range})
    monkeypatch.setattr(acq,"urlopen",opened)
    monkeypatch.setattr(acq,"LOTSS_LOCAL",local)
    page=tmp_path/"release";page.write_text("A catalogue of 2 radio sources")
    data=acq.lotss_catalog_probe({"local_path":str(page),"links":[acq.LOTSS_URL]})
    assert data["local_FITS_NAXIS2"]==data["official_FITS_NAXIS2"]==3
    assert data["official_FITS_minus_prose"]==1
    assert data["received_bytes"]==end-start and data["catalogue_row_payload_bytes_read"]==0
    assert data["local_extension_header_byte_identical"]
