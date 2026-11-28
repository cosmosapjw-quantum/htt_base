import io
import json
from pathlib import Path
import numpy as np
import pytest
from common.native_morphology_atlas import CASES, HEADER, PAIRS, CHANNELS, NativeMorphologyAtlas, build_manifest, decode_signed_modes
from common import bianchi_transfer_adapter as adapter

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/"docs/research_program/observational_publication_20261015"
REF=DOC/"R114_LOCAL_UNIVERSAL_LIE_SKY_20261125"
MAN=DOC/"R119_NATIVE_CLASSIFICATION_INTAKE_20261128/ATLAS_MANIFEST.json"
RECEIPT=REF/"C1_HARMONIC_LONG_ATLAS.json"
LEDGER=REF/"EXECUTED_COMMANDS.json"

def synthetic():
    # Parser fixture only; never admitted as native source.
    a=np.zeros((9,3),complex)
    a[4]=[1+2j,3+4j,1-1j];a[8]=a[4].conj()
    a[6]=[2,1,-3]
    t=np.zeros((9,20));t[:,:2]=[(l,m) for l in range(3) for m in range(-l,l+1)]
    t[:,2:8:2]=a.real;t[:,3:8:2]=a.imag
    for j,xy in enumerate(PAIRS):
        z=a[:,CHANNELS.index(xy[0])]*a[:,CHANNELS.index(xy[1])].conj()
        t[:,8+2*j]=z.real;t[:,9+2*j]=z.imag
    return t,a

def encode(t,header=HEADER):
    s=io.StringIO();np.savetxt(s,t,header=" ".join(header),comments="")
    return s.getvalue().encode()

def test_signed_modes_exact():
    t,a=synthetic();r,c=decode_signed_modes(encode(t),2)
    np.testing.assert_array_equal(r,a)
    np.testing.assert_allclose(c[2,0],np.vdot(a[:,0],a[:,0]).real/5)
    assert not r.flags.writeable and not c.flags.writeable

@pytest.mark.parametrize("kind",["header","missing","duplicate","nan","reality","spin2","product"])
def test_reject_bad_table(kind):
    t,_=synthetic();header=HEADER
    if kind=="header":header=(*HEADER[:-1],"bad")
    if kind=="missing":t=t[:-1]
    if kind=="duplicate":t[-1,:2]=t[-2,:2]
    if kind=="nan":t[5,2]=np.nan
    if kind=="reality":t[4,2]+=1
    if kind=="spin2":t[0,4]=1
    if kind=="product":t[6,8]+=1
    with pytest.raises(ValueError):
        decode_signed_modes(encode(t,header),2)

def test_source_lock(tmp_path):
    f=tmp_path/"receipt.json";f.write_bytes(RECEIPT.read_bytes()+b" ")
    with pytest.raises(ValueError,match="SHA256"):
        build_manifest(f,LEDGER)

def test_manifest_cannot_self_authorize(tmp_path):
    m=json.loads(MAN.read_text());m["cases"]["II"]["runs"]["h32_s2000"]["sha256"]="0"*64
    f=tmp_path/"fake.json";f.write_text(json.dumps(m))
    with pytest.raises(ValueError,match="manifest differs"):
        NativeMorphologyAtlas(f,tmp_path,RECEIPT,LEDGER)

def test_source_missing_or_changed(tmp_path):
    a=NativeMorphologyAtlas(MAN,tmp_path,RECEIPT,LEDGER)
    assert a.cases==CASES
    with pytest.raises(ValueError,match="unsupported"):
        a.read("../II")
    with pytest.raises(FileNotFoundError):
        a.read("II")
    f=tmp_path/"II/h32_s2000/los_modes.tsv";f.parent.mkdir(parents=True);f.write_bytes(encode(synthetic()[0]))
    with pytest.raises(ValueError,match="pinned source"):
        a.read("II")
    m=a.metadata;m["cases"].clear()
    assert len(a.metadata["cases"])==13

def test_c6_marker_never_authorizes(monkeypatch):
    monkeypatch.setattr(adapter,"is_native_atlas_present",lambda:True)
    g=adapter.FamilyIdentificationGate.evaluate_gate(adapter.ClaimTier.C6_BIANCHI_FAMILY_IDENTIFICATION)
    assert g.verdict=="BLOCKED" and "external_null_mask_covariance_gates" in g.missing_gates
    assert g.is_family_identification_claimed and g.allowed_claim_tier==adapter.ClaimTier.C0_DIAGNOSTIC

def test_c6_external_marker_never_authorizes(monkeypatch):
    from common.transfer_registry import TransferSource, ObservableKind, CalibrationStatus, TransferFunctionSpec, TransferValidRange
    monkeypatch.setattr(adapter,"is_native_atlas_present",lambda:True)
    s=TransferFunctionSpec(transfer_id="external",source=TransferSource.ANICLASS_EXTERNAL,
        family="VII_h",valid_range=TransferValidRange(k_min=1e-4,k_max=.1,ell_min=2,ell_max=30),
        observable_kind=ObservableKind.TEMPERATURE,normalization="dimensionless_amplitude",
        calibration_status=CalibrationStatus.EXTERNAL_CALIBRATED,caveats=["external"])
    g=adapter.FamilyIdentificationGate.evaluate_gate(adapter.ClaimTier.C6_BIANCHI_FAMILY_IDENTIFICATION,s)
    assert g.verdict=="BLOCKED" and g.transfer_label=="external-transfer-conditional"
