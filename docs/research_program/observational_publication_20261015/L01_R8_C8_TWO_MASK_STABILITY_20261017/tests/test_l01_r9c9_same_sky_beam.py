"""R9/C9 contract tests; manufactured matrices/HTTP responses, NO Planck E2E."""
from __future__ import annotations
import io
import sys
from pathlib import Path

import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE/"src"))
from test_l01_k_certificate import fake_complex_operator
from l01_r9c9_same_sky_beam import (beam_difference, multipole_diagonal,
                                   shared_source_covariance, min_norm_lift)
import fetch_planck_pr3_smica as dl


def test_beam_replication_and_identity():
    k=fake_complex_operator()
    t=fake_complex_operator(seed=11)
    beam=np.exp(-0.001*np.arange(16)*(np.arange(16)+1))
    d=t-k
    low=multipole_diagonal(beam,(2,3,4,5),invert=True)
    high=multipole_diagonal(beam,(6,7,8))
    result=beam_difference(k,t,beam)
    expected=(low[:,None]*d)*high[None,:]
    assert np.isclose(result["deconvolved_low_norm"],np.linalg.norm(expected,2),rtol=1e-12)
    assert result["observed_low_norm"]>0
    assert result["assumption"].startswith("AXISYMMETRIC")


def test_beam_rejects_bad_value():
    beam=np.ones(15);beam[4]=0.
    with pytest.raises(ValueError,match="INADMISSIBLE_BEAM"):
        beam_difference(fake_complex_operator(),fake_complex_operator(seed=3),beam)
    beam=np.ones(15);beam[7]=np.nan
    with pytest.raises(ValueError,match="NONFINITE_BEAM"):
        multipole_diagonal(beam,(6,7,8))


def test_mask_outputs_correlated_not_independent():
    k=fake_complex_operator()
    cov=np.eye(90)
    out=shared_source_covariance(k,k,cov)
    np.testing.assert_allclose(out["cross"],out["common"])
    assert np.linalg.norm(out["difference"])<1e-13


def test_correlated_covariance_psd_and_cross_terms():
    k=fake_complex_operator()
    t=fake_complex_operator(seed=13)
    cov=np.diag(np.linspace(.1,2.,90))
    out=shared_source_covariance(k,t,cov)
    np.testing.assert_allclose(out["difference"],(t-k)@cov@(t-k).T)
    assert np.linalg.eigvalsh(out["difference"]).min()>-1e-12
    assert np.linalg.norm(out["common"]+out["triple"]-out["difference"])>.1


def test_nonpsd_covariance_rejected():
    k=fake_complex_operator()
    c=np.eye(90);c[0,0]=-10
    with pytest.raises(ValueError,match="NOT_PSD"):
        shared_source_covariance(k,k,c)


def test_minimum_source_witness_agrees_with_exact_full_row_formula():
    rng=np.random.default_rng(17)
    A=fake_complex_operator()
    d=rng.normal(size=64)
    out=min_norm_lift(A,d)
    assert out["numerical_rank"]==64
    assert out["reachable"]
    expected=A.T@np.linalg.solve(A@A.T,d)
    assert abs(out["min_source_norm_if_reachable"]-np.linalg.norm(expected))<1e-9
    assert out["target_residual"]<1e-10


def test_zero_operator_nonzero_target_is_not_reachable():
    z=np.zeros((64,90));d=np.zeros(64);d[0]=1
    out=min_norm_lift(z,d)
    assert not out["reachable"]
    assert out["min_source_norm_if_reachable"] is None


class FakeResponse:
    def __init__(self, data, status=200, headers=None):
        self.buf=io.BytesIO(data)
        self.status=status
        self.headers=headers or {}
    def read(self,n): return self.buf.read(n)
    def getcode(self): return self.status
    def close(self): self.buf.close()


def minimal_fits(n=2):
    return (b"SIMPLE  ="+b" "*2871)+(b"X"*2880)*(n-1)


def test_official_smica_allowlist_and_fake_download(tmp_path, monkeypatch):
    assert dl.filename("full")=="COM_CMB_IQU-smica_2048_R3.00_full.fits"
    with pytest.raises(ValueError):
        dl.filename("../hijack")
    monkeypatch.setitem(dl.MIN_BYTES,"full",2000)
    data=minimal_fits()
    original=dl.transfer("full",tmp_path,opener=lambda req:FakeResponse(data,200,{"Content-Length":str(len(data))}))
    assert original["status"]=="DOWNLOADED_FITS_FRAMING_VALID"
    assert Path(original["path"]).read_bytes()==data
    again=dl.transfer("full",tmp_path,opener=lambda req:(_ for _ in ()).throw(AssertionError("HTTP must not occur")))
    assert again["status"]=="EXISTING_REUSED"


def test_range_mismatch_rejected_and_partial_preserved(tmp_path, monkeypatch):
    monkeypatch.setitem(dl.MIN_BYTES,"full",2000)
    name=dl.filename("full")
    p=tmp_path/"planck/PR3/cmb"/(name+".part")
    p.parent.mkdir(parents=True)
    p.write_bytes(b"abc")
    with pytest.raises(ValueError,match="UNVERIFIED_HTTP_RANGE"):
        dl.transfer("full",tmp_path,opener=lambda req:FakeResponse(minimal_fits(),206,{"Content-Range":"bytes 0-5759/5760"}))
    assert p.read_bytes()==b"abc"


def test_full_smica_header_scope_without_large_file(tmp_path, monkeypatch):
    import types
    from l01_r9c9_same_sky_beam import read_official_smica_pol_beam
    p=tmp_path/"COM_CMB_IQU-smica_2048_R3.00_full.fits"
    p.write_bytes(b"manufactured")
    class HDU:
        def __init__(self,header,names=(),data=None):
            self.header=header
            self.columns=types.SimpleNamespace(names=list(names))
            self.data=data
    class HDUList(list):
        def __enter__(self): return self
        def __exit__(self,*a): return None
    h0=HDU({})
    h1=HDU({"NSIDE":2048,"ORDERING":"NESTED","COORDSYS":"GALACTIC",
            "POLCCONV":"COSMO","METHOD":"SMICA",
            "TUNIT1":"K_CMB","TUNIT2":"K_CMB","TUNIT3":"K_CMB"},
           ["I_STOKES","Q_STOKES","U_STOKES"])
    pol=np.exp(-0.00001*np.arange(4097,dtype=float))
    h2=HDU({"LMIN":0,"LMAX_P":4096},["INT_BEAM","POL_BEAM"],
           {"POL_BEAM":pol})
    hd=HDUList([h0,h1,h2])
    fits=types.SimpleNamespace(open=lambda *args,**kwargs:hd)
    astropy=types.ModuleType("astropy")
    io_module=types.ModuleType("astropy.io")
    io_module.fits=fits
    astropy.io=io_module
    monkeypatch.setitem(sys.modules,"astropy",astropy)
    monkeypatch.setitem(sys.modules,"astropy.io",io_module)
    monkeypatch.setitem(sys.modules,"astropy.io.fits",fits)
    got=read_official_smica_pol_beam(p)
    assert got.shape==(4097,) and got[2]>0
    h1.header["POLCCONV"]="IAU"
    with pytest.raises(ValueError,match="SMICA_HEADER_POLCCONV"):
        read_official_smica_pol_beam(p)
