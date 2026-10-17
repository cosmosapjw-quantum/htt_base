"""V2 qualification tests have no access to actual Planck native FITS on this host."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from source_lock_v2 import load_v2_manifest, qualify_v2, require_v2_admission
from unittest.mock import patch
import source_lock_v2
from fits_source_identity import SourceIdentityError
from test_source_identity import write_mask

LABELS = {"common": "COM_Mask_CMB-common-Mask-Pol_2048_R3.00.fits",
          "HM": "COM_Mask_CMB-HM-Misspix-Mask-Pol_2048_R3.00.fits",
          "OE": "COM_Mask_CMB-OE-Misspix-Mask-Pol_2048_R3.00.fits"}


def fixture(root, ref):
    a, b = (p / "planck/PR3/masks" for p in (root, ref))
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    sha = {}
    for i, (key, filename) in enumerate(LABELS.items()):
        source = write_mask(a / filename, np.linspace(0, 1, 12, dtype=np.float32), nside=1,
                            date="2026-10-17")
        reference = write_mask(b / filename, np.linspace(0, 1, 12, dtype=np.float32), nside=1,
                               date="2026-10-17")
        sha[key] = hashlib.sha256(source.read_bytes()).hexdigest()
        assert reference.read_bytes() == source.read_bytes()
    return a, b, sha, source.stat().st_size


def verify(root, ref, sha, size):
    with patch.dict(source_lock_v2.EXISTING_V1_PINS, {k:sha[k] for k in ("common","HM")}, clear=True):
        return qualify_v2(root, ref, names=LABELS, expected_sha=sha, expected_size=size, nside=1)


def test_v2_manifest_and_historical_lock_stay_distinct():
    m = load_v2_manifest()
    assert set(m["expected_sha256"]) == set(LABELS)
    assert len(m["historical_v1_OE_sha256"]) == 45
    assert len(m["expected_sha256"]["OE"]) == 64
    assert m["expected_sha256"]["OE"] == "1b2b4138f791b739938485fa0ebcac5f462e04fbc55626e93d71abd04aac3900"
    assert m["observed_reference_evidence"]["independently_verified_publisher_download_log"] is False


def test_independently_located_same_bytes_admit_scoped_geometry(tmp_path):
    root, ref = tmp_path / "local", tmp_path / "external"
    _, _, sha, size = fixture(root, ref)
    report = verify(root, ref, sha, size)
    r = require_v2_admission(report)
    assert set(r) == set(LABELS)
    for k,entry in report.items():
        if k == "OE":
            assert entry["reference_status"] == "REFERENCE_BYTE_IDENTICAL_TO_PINNED_SOURCE"
            assert entry["semantic_status"] == "SEMANTIC_EQUIVALENT_PMASK"
            assert entry["provenance_status"] == "REFERENCE_ORIGIN_USER_REPORTED__NOT_INDEPENDENTLY_AUTHENTICATED"
        else:
            assert entry["reference_status"] == "UNCHANGED_V1_BYTE_LOCK_REUSED"
            assert entry["admission"] == "ORIGINAL_V1_LOCK_REUSED_GEOMETRY_ONLY"
        assert entry["scientific_status"] == "P2_L01_NOT_READY_FOR_PHYSICAL_CLAIM"


def test_reference_root_required_even_if_local_bytes_admit(tmp_path):
    root, ref = tmp_path / "local", tmp_path / "external"
    _, _, sha, size = fixture(root, ref)
    receipt = verify(root, None, sha, size)
    assert all(v["byte_status"] == "BYTE_IDENTICAL" for v in receipt.values())
    assert receipt["OE"]["reference_status"] == "REFERENCE_ROOT_REQUIRED"
    assert receipt["OE"]["admission"] == "NOT_ADMITTED"
    assert receipt["HM"]["admission"] == "ORIGINAL_V1_LOCK_REUSED_GEOMETRY_ONLY"
    with pytest.raises(SourceIdentityError): require_v2_admission(receipt)


def test_same_inode_reference_is_not_independent(tmp_path):
    root, ref = tmp_path / "local", tmp_path / "external"
    a, b, sha, size = fixture(root, ref)
    (b / LABELS["OE"]).unlink()
    (b / LABELS["OE"]).hardlink_to(a / LABELS["OE"])
    r = verify(root, ref, sha, size)
    assert r["OE"]["reference_status"] == "REFERENCE_ALIASES_LOCAL_FILE"
    with pytest.raises(SourceIdentityError): require_v2_admission(r)


def test_reference_sha_mismatch_rejected(tmp_path):
    root, ref = tmp_path / "local", tmp_path / "external"
    _, b, sha, size = fixture(root, ref)
    f = b / LABELS["OE"]
    blob = bytearray(f.read_bytes())
    blob[-1] ^= 1  # FITS padding byte; should still be rejected by SOURCE lock.
    f.write_bytes(blob)
    r = verify(root, ref, sha, size)
    assert r["OE"]["reference_status"] == "REFERENCE_SHA_MISMATCH"
    assert r["OE"]["admission"] == "NOT_ADMITTED"


def test_local_sha_mismatch_rejected_even_if_reference_matches(tmp_path):
    root, ref = tmp_path / "local", tmp_path / "external"
    a, _, sha, size = fixture(root, ref)
    f = a / LABELS["OE"]
    blob = bytearray(f.read_bytes()); blob[-4] ^= 1; f.write_bytes(blob)
    r = verify(root, ref, sha, size)
    assert r["OE"]["reference_status"] == "LOCAL_BYTES_NOT_PINNED"
    assert r["OE"]["byte_status"] == "BYTE_SHA_MISMATCH"
    with pytest.raises(SourceIdentityError): require_v2_admission(r)


def test_reference_symlink_rejected(tmp_path):
    root, ref = tmp_path / "local", tmp_path / "external"
    a, b, sha, size = fixture(root, ref)
    x = b / LABELS["OE"]
    x.unlink(); x.symlink_to(a / LABELS["OE"])
    r = verify(root, ref, sha, size)
    assert r["OE"]["reference_status"] == "REFERENCE_MISSING_OR_SYMLINK"


def test_wrong_reference_layout_rejected_even_when_bytes_pinned(tmp_path):
    root, ref = tmp_path / "local", tmp_path / "external"
    a, b, sha, size = fixture(root, ref)
    for path in [a / LABELS["OE"], b / LABELS["OE"]]:
        bad = path.read_bytes().replace(b"'NESTED'", b"'RING  '")
        assert len(bad) == size
        path.write_bytes(bad)
    sha["OE"] = hashlib.sha256((a / LABELS["OE"]).read_bytes()).hexdigest()
    r = verify(root, ref, sha, size)
    assert r["OE"]["reference_status"] == "LOCAL_FITS_LAYOUT_INVALID"
    assert r["OE"]["admission"] == "NOT_ADMITTED"


def test_malformed_v2_manifest_fails_before_acceptance(tmp_path):
    original = load_v2_manifest()
    original["expected_sha256"]["OE"] = "ff"  # no migration by observation
    path = tmp_path / "bad.json"; path.write_text(json.dumps(original))
    with pytest.raises(ValueError, match="MALFORMED_V2_LOCK_DIGEST"):
        load_v2_manifest(path)


def test_v2_lock_does_not_change_default_original_source_constant():
    import native_planck_pol_response as native
    assert native.SOURCE["OE"] == "1b2b4138f791b739938485fa0ebcac5f462e04aac3900"
    assert "--source-lock" in Path(native.__file__).read_text()


def test_v2_cli_verify_only_reuses_v1_pins_and_checks_only_oe_reference(tmp_path, monkeypatch, capsys):
    import native_planck_pol_response as native
    root, ref = tmp_path / "local", tmp_path / "external"
    _, b, sha, size = fixture(root, ref)
    # The user need only retain the independently downloaded OE source; the two
    # pre-existing v1 admitted originals are not requalified or redownloaded.
    for label in ("common", "HM"):
        (b / LABELS[label]).unlink()
    monkeypatch.setattr(native,"NAME", LABELS)
    monkeypatch.setattr(native,"EXPECTED_SIZE", size)
    monkeypatch.setattr(native,"load_v2_manifest", lambda: {"expected_sha256": sha})
    from source_lock_v2 import qualify_v2 as original_qualify
    def tiny_qualify(r, rr, **kwargs):
        with patch.dict(source_lock_v2.EXISTING_V1_PINS,
                        {k: sha[k] for k in ("common", "HM")}, clear=True):
            return original_qualify(r, rr, nside=1, **kwargs)
    monkeypatch.setattr(native,"qualify_v2",tiny_qualify)
    code=native.main(["--root",str(root),"--compare-root",str(ref),
                      "--source-lock","v2","--verify-only"])
    output=json.loads(capsys.readouterr().out)
    assert code == 0
    assert output["OE"]["admission"]=="V2_REFERENCE_LOCK_ADMITTED_GEOMETRY_ONLY"
    assert output["common"]["reference_status"]=="UNCHANGED_V1_BYTE_LOCK_REUSED"
    assert output["HM"]["reference_status"]=="UNCHANGED_V1_BYTE_LOCK_REUSED"


def test_effective_mask_receipt_is_canonical_and_bit_sensitive():
    from native_planck_pol_response import canonical_ring64_mask_sha256
    m=np.zeros(12*64*64,dtype=np.bool_);m[:12345]=True
    d=canonical_ring64_mask_sha256(m)
    assert d==hashlib.sha256(m.astype(np.uint8).tobytes()).hexdigest()
    changed=m.copy();changed[2]=False
    assert canonical_ring64_mask_sha256(changed)!=d
    with pytest.raises(ValueError): canonical_ring64_mask_sha256(m.astype(np.float32))


def test_coarse_threshold_does_not_commute_with_native_intersection():
    # Manufactured one coarse pixel with 4 subpixels. Each of three masks
    # covers 3/4 so all independently thresholded coarse masks pass, while
    # only one high-res subpixel survives the native intersection.
    a=np.array([1,1,1,0],dtype=bool)
    b=np.array([0,1,1,1],dtype=bool)
    c=np.array([1,0,1,1],dtype=bool)
    t=.5
    post=all(np.mean(x)>t for x in [a,b,c])
    native_then_coarse=np.mean(a&b&c)>t
    assert post is True
    assert native_then_coarse == np.bool_(False)
