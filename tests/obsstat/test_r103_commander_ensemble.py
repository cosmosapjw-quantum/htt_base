"""Independent harmonic, transfer, and resumability checks for Commander PR3."""
from argparse import Namespace
from io import BytesIO
import hashlib
import json

import healpy as hp
import numpy as np
import pytest

from scripts.r102 import acquire_commander_pair as acq
from scripts.r103 import commander_ensemble as ensemble


def test_distinct_T_P_masks_and_all_six_spectra(tmp_path, monkeypatch):
    nside, lmax = 4, 6
    npix = hp.nside2npix(nside)
    rng = np.random.default_rng(71219)
    sig, noise = rng.normal(size=(2, 3, npix)) * 1.e-6
    noise[1] -= 2.5*sig[1]  # signed cross spectra cannot be inferred from intensities
    for name, maps in (("signal", sig), ("noise", noise)):
        hp.write_map(str(tmp_path/(name+".fits")), maps, overwrite=False, dtype=np.float64)
    pix = np.arange(npix)
    masks = (pix % 3 != 0, pix % 4 != 0)
    s = ensemble.masked_alms(tmp_path/"signal.fits", masks, lmax)
    n = ensemble.masked_alms(tmp_path/"noise.fits", masks, lmax)
    out = ensemble.reduce_alms(s, n)
    expected_maps = (sig + noise) * np.stack([masks[0], masks[1], masks[1]])
    expected = hp.anafast(expected_maps, lmax=lmax, iter=3, pol=True)[:,2:] * 1.e12
    assert tuple(out) == ("TT", "EE", "BB", "TE", "EB", "TB")
    assert (expected[3:] < 0).any() and (expected[3:] > 0).any()
    np.testing.assert_allclose([out[ch] for ch in ensemble.CHANNELS], expected,
                               rtol=5.e-12, atol=1.e-13)


@pytest.mark.parametrize("part", ["cmb", "noise"])
def test_indexed_chunked_download_and_cached_bytes(tmp_path, monkeypatch, part):
    payload = b"small fit payload for indexed intake fixture"
    monkeypatch.setattr(acq, "COMMANDER_SIZE", len(payload))
    job = acq.ensemble_job(part, 17)
    assert job["id"] == f"dx12_v3_commander_{part}_mc_00017_raw.fits"
    assert job['url'].endswith(job['id'])
    calls = []

    class Response(BytesIO):
        status = 200
        headers = {"Transfer-Encoding": "chunked", "Content-Type": "image/fits",
                   "Content-Disposition": f'inline; filename="{job["id"]}"'}

    def open_stub(req, timeout):
        calls.append(req.full_url)
        return Response(payload)

    def digest(path, _job):
        return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}

    monkeypatch.setattr(acq, 'urlopen', open_stub)
    monkeypatch.setattr(acq, 'validate_payload', digest)
    with pytest.raises(ValueError):
        acq.acquire_commander_product(part, 17, tmp_path, max_bytes=len(payload)-1)
    first = acq.acquire_commander_product(part, 17, tmp_path, max_bytes=len(payload))
    cached = acq.acquire_commander_product(part, 17, tmp_path, max_bytes=len(payload))
    assert first["transferred_bytes"] == len(payload) and cached["transferred_bytes"] == 0
    assert first['sha256'] == cached['sha256'] and calls == [job['url']]


@pytest.mark.parametrize("part,index", [("cmb",-1), ("noise",300), ("even",0), ("cmb", True)])
def test_invalid_ensemble_job(part,index):
    with pytest.raises(ValueError):
        acq.ensemble_job(part,index)


def test_inventory_and_missing_allowance(tmp_path, monkeypatch):
    monkeypatch.setattr(ensemble, "COMMANDER_SIZE", 4)
    for idx, part, payload in [(0, "cmb", b"abcd"), (0,"noise",b"short"), (1,"noise",b"efgh")]:
        (tmp_path/acq.ensemble_job(part,idx)["id"]).write_bytes(payload)
    paths = ensemble.inventory([tmp_path, tmp_path],0,2)
    info = ensemble.plan(paths,0,2)
    assert info["missing_bytes"] == 8
    assert info["available_pairs_size_checked_only"] == []
    assert info["available_size_checked_only"] == {"cmb":[0], "noise":[1]}
    with pytest.raises(ValueError):
        ensemble.inventory([tmp_path], 0, 301)


@pytest.fixture
def batch(tmp_path, monkeypatch):
    args = Namespace(start=0, stop=1, lmax=4, max_download_bytes=0, scratch=tmp_path/"scratch",
                     output_dir=tmp_path/"out", mask_int=tmp_path/"t", mask_pol=tmp_path/"p")
    meth = lambda p,*a: (np.ones(12,bool), {"hdus":[{},{"nside":2048}],"n_bad_pixels":0})
    monkeypatch.setattr(ensemble, "_read_healpix_to_ring", meth)
    args.mask_int.write_bytes(b't')
    args.mask_pol.write_bytes(b'p')
    for part in ensemble.PARTS:
        (tmp_path/part).write_bytes(part.encode())
    paths={(0,p):[tmp_path/p] for p in ensemble.PARTS}
    monkeypatch.setattr(ensemble, 'validate_payload', lambda path,job:
                        {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    def alms(path, masks, lmax):
        return np.ones((3, hp.Alm.getsize(lmax)), dtype=complex)
    monkeypatch.setattr(ensemble, 'masked_alms', alms)
    return args, paths


def test_resume_reuses_compatible_reduction_and_detects_raw_changes(batch,monkeypatch):
    args, paths = batch
    with pytest.raises(ValueError, match='allowance'):
        ensemble.run_batch(args, {})
    ensemble.run_batch(args, paths)
    monkeypatch.setattr(ensemble,'masked_alms', lambda *args: pytest.fail("expected cached reduction"))
    ensemble.run_batch(args, paths)
    paths[(0,'noise')][0].write_bytes(b'changed')
    with pytest.raises(ValueError, match='conflict'):
        ensemble.run_batch(args, paths)


@pytest.mark.parametrize("malformation", ["sha_collision","matrix","physical","shape"])
def test_resume_rejects_incompatible_or_malformed_reduction(batch,malformation):
    args, paths = batch
    ensemble.run_batch(args, paths)
    out = args.output_dir/"commander_pr3_00000.json"
    value = json.loads(out.read_text())
    if malformation == 'sha_collision':
        value["raw_sha256"]["noise"] = value["raw_sha256"]["cmb"]
    elif malformation == 'matrix':
        value["pseudo_cl_ell2_up_uK2"]["EB"] = [[2., 3.]] * (args.lmax-1)
    elif malformation == 'physical':
        value["physical_Pi"] = .8
    else:
        value["pseudo_cl_ell2_up_uK2"]["BB"] = []
    out.write_text(json.dumps(value))
    # Simulate an already-cleaned raw scratch directory, i.e. provenance comes
    # solely from the json. An extant raw collision must not hide the cache bug.
    with pytest.raises(ValueError):
        ensemble.run_batch(args, {})


def test_immutable_pair_publication_preserves_conflicting_writer(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    path = tmp_path / "result.json"
    barrier = Barrier(2)

    def publish(value):
        barrier.wait()
        try:
            ensemble.atomic_json(path, value, immutable=True)
            return "created"
        except FileExistsError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        states = list(pool.map(publish, [{"mask":"first"}, {"mask":"second"}]))
    assert sorted(states) == ["conflict", "created"]
    saved = json.loads(path.read_text())
    before = path.read_bytes()
    ensemble.atomic_json(path, saved, immutable=True)  # idempotent identical publisher
    assert path.read_bytes() == before and len(list(tmp_path.iterdir())) == 1
