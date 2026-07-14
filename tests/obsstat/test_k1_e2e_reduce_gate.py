"""K1 E2E footprint-reduction + faithful-cache gate roundtrip.

The gate authorizes deleting ~1 TB of raw FFP10/NPIPE maps, so it MUST be
bit-exact and fail-closed. This exercises the reduce -> gate roundtrip on tiny
fixtures (same `{tag}_mc_{id}.npz` layout the real downgraded maps use) and
checks: the cache reproduces the from-raw statistics bit-exactly
(`safe_to_delete_raw` true), a corrupted raw file trips the hash check
(fail-closed), and a missing raw file cannot pass.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "scripts"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

hp = pytest.importorskip("healpy")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _write_sims(d: Path, tag: str, n: int, seed: int):
    d.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    for i in range(n):
        m = rng.normal(0, 60, hp.nside2npix(16))
        np.savez(d / f"dx12_v3_smica_{tag}_mc_{i:05d}.npz", I=m.astype(float), unit="uK")


@pytest.fixture()
def dirs(tmp_path):
    cmb = tmp_path / "cmb_mc"
    noise = tmp_path / "noise_mc"
    _write_sims(cmb, "cmb", 6, 1)
    _write_sims(noise, "noise", 3, 2)
    return cmb, noise, tmp_path


def test_reduce_then_gate_is_bit_exact_and_green(dirs, tmp_path, monkeypatch):
    cmb, noise, _ = dirs
    reduce = _load("k1_e2e_reduce")
    gate = _load("k1_e2e_cache_gate")
    man = tmp_path / "manifest.json"
    # write manifest into tmp (not docs/generated) via the build API
    payload = reduce.build(cmb, noise, "smica", "ffp10", tmp_path / "cache",
                           reduce.REDUCE_NSIDE, reduce.LMAX_CACHE, None)
    man.write_text(json.dumps(payload))

    res = gate.run(man, {"cmb": cmb, "noise": noise}, sample=0, do_all=True, tol=1e-9)
    assert res["raw_hash_ok"] is True
    assert res["stat_reproduced"] is True
    assert res["safe_to_delete_raw"] is True
    assert res["max_abs_stat_diff"] == 0.0          # float64 cache -> bit-exact


def test_gate_fails_closed_on_corrupted_raw(dirs, tmp_path):
    cmb, noise, _ = dirs
    reduce = _load("k1_e2e_reduce")
    gate = _load("k1_e2e_cache_gate")
    man = tmp_path / "manifest.json"
    payload = reduce.build(cmb, noise, "smica", "ffp10", tmp_path / "cache",
                           reduce.REDUCE_NSIDE, reduce.LMAX_CACHE, None)
    man.write_text(json.dumps(payload))
    # corrupt one raw noise file AFTER reduction -> hash must mismatch, gate must block
    victim = sorted(noise.glob("*.npz"))[0]
    m = np.random.default_rng(9).normal(0, 60, hp.nside2npix(16))
    np.savez(victim, I=m.astype(float), unit="uK")

    res = gate.run(man, {"cmb": cmb, "noise": noise}, sample=0, do_all=True, tol=1e-9)
    assert res["raw_hash_ok"] is False
    assert res["safe_to_delete_raw"] is False


def test_gate_cannot_pass_if_raw_absent(dirs, tmp_path):
    cmb, noise, _ = dirs
    reduce = _load("k1_e2e_reduce")
    gate = _load("k1_e2e_cache_gate")
    man = tmp_path / "manifest.json"
    payload = reduce.build(cmb, noise, "smica", "ffp10", tmp_path / "cache",
                           reduce.REDUCE_NSIDE, reduce.LMAX_CACHE, None)
    man.write_text(json.dumps(payload))
    for f in noise.glob("*.npz"):          # simulate premature deletion
        f.unlink()

    res = gate.run(man, {"cmb": cmb, "noise": noise}, sample=0, do_all=True, tol=1e-9)
    assert res["safe_to_delete_raw"] is False
