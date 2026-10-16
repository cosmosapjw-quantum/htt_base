import sys,importlib.util,zipfile
from pathlib import Path
import pytest
path=Path(__file__).resolve().parents[1]/'src'
sys.path.insert(0,str(path))
from prior_selected_source_sky import audit_npz_bytes, NAME
archive=Path('/mnt/data/HTT_SIXPAPER_X02_K02_S02_L01_20261016.zip')
local_source=Path(__file__).resolve().parents[1]/'data/selected_source_observables.npz'

def test_prior_35970_sha_and_method_nuisance_rank():
    if local_source.exists():data=local_source.read_bytes()
    elif archive.exists():
        with zipfile.ZipFile(archive) as z:data=z.read(NAME)
    else:pytest.skip('original selected source unavailable')
    r=audit_npz_bytes(data)
    assert r['selected_source_count']==35970
    assert sum(p['n_groups'] for p in r['methods'].values())==35970
    assert r['rank_angular_after_calibration']==8
    assert r['claim_admission'].endswith('H02 SELECTION HOLD')

def test_source_npz_payload_replacement_not_accepted():
    with pytest.raises(ValueError,match='SHA mismatch'):
        audit_npz_bytes(b'not the original source')
