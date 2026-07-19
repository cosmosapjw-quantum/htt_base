"""K1 E2E footprint-reduction + faithful-cache gate roundtrip.

The gate authorizes deleting ~1 TB of raw FFP10/NPIPE maps, so it MUST be
bit-exact and fail-closed. This exercises the reduce -> gate roundtrip on tiny
fixtures (same `{tag}_mc_{id}.npz` layout the real downgraded maps use) and
checks: the cache reproduces the raw-to-cache maps bit-exactly while the partial
fixture remains deletion-ineligible, a corrupted raw file trips the hash check
(fail-closed), and a missing raw file cannot pass. Production deletion
eligibility additionally requires the exact 999+300 inventory, observed/mask
and result replay, a distinct-device backup, and a PR4 replacement receipt.
"""
from __future__ import annotations

import importlib.util
import hashlib
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
    assert res["direct_raw_to_cache_array_equal"] is True
    assert res["full_map_replay"] is True
    assert res["replay_files_exact"] is True
    # A partial fixture proves the mechanical roundtrip only.  It can never
    # authorize raw deletion: the production gate additionally requires the
    # exact 999+300 inventory, observed/mask/result replay, independent backup,
    # and a future authenticated PR4 replacement-ready receipt.
    assert res["cache_reproducibility_green"] is False
    assert res["safe_to_delete_raw"] is False


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
    assert res["direct_raw_to_cache_array_equal"] is False
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


def test_gate_display_path_accepts_relative_cli_output(monkeypatch):
    gate = _load("k1_e2e_cache_gate")
    monkeypatch.chdir(REPO)
    assert gate._display_path(Path("docs/generated/gate.json")) == \
        "docs/generated/gate.json"


def _pr4_file_record(path: Path, **identity) -> dict:
    return {
        **identity,
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def test_pr4_replacement_receipt_rehashes_typed_inventory(tmp_path):
    gate = _load("k1_e2e_cache_gate")
    fake = tmp_path / "fake.json"
    fake.write_text(json.dumps({
        "status": "PR4_REPLACEMENT_READY",
        "access_status": "available",
        "input_checksums_verified": True,
        "download_plan_size_probed": True,
    }))
    rejected = gate._pr4_ready(fake)
    assert rejected["ready"] is False
    assert "schema_invalid" in rejected["errors"]
    assert rejected["verified_file_count"] == 0

    observed_path = tmp_path / gate.PR4_OBSERVED_MAP_ID
    simulation_path = tmp_path / "sim_00000.fits"
    noise_fix_path = tmp_path / "noise_fix.dat"
    observed_path.write_bytes(b"observed PR4 map")
    simulation_path.write_bytes(b"simulation zero")
    noise_fix_path.write_bytes(b"noise fix")
    observed = _pr4_file_record(
        observed_path, map_id=gate.PR4_OBSERVED_MAP_ID)
    simulation = _pr4_file_record(
        simulation_path, simulation_id="00000")
    noise_fix = _pr4_file_record(noise_fix_path)
    normalized_observed = {"role": "observed_map", **observed,
                           "path": str(observed_path.resolve())}
    normalized_simulation = {"role": "simulation[0]", **simulation,
                             "path": str(simulation_path.resolve())}
    normalized_noise = {"role": "noise_fix", **noise_fix,
                        "path": str(noise_fix_path.resolve())}
    inventory_hash = gate._canonical_hash({
        "observed_map": normalized_observed,
        "simulations": [normalized_simulation],
        "excluded_ids": [],
        "noise_fix": normalized_noise,
    })
    receipt = tmp_path / "ready.json"
    receipt.write_text(json.dumps({
        "schema": gate.PR4_READY_SCHEMA,
        "status": "PR4_REPLACEMENT_READY",
        "access_status": "available",
        "analysis_status": "ready",
        "replacement_scope": "PR4_NPIPE_SEVEM_ANALYSIS_INPUTS",
        "input_checksums_verified": True,
        "download_plan_size_probed": True,
        "source_authority": "authenticated local test inventory",
        "generating_command": "build-pr4-receipt --verify",
        "observed_map": observed,
        "simulation_inventory": {
            "nominal_count": 1,
            "usable_count": 1,
            "excluded_ids": [],
            "files": [simulation],
        },
        "noise_fix": noise_fix,
        "total_size_bytes": sum(path.stat().st_size for path in (
            observed_path, simulation_path, noise_fix_path)),
        "verified_inventory_sha256": inventory_hash,
    }))
    accepted = gate._pr4_ready(receipt)
    assert accepted["ready"] is True
    assert accepted["verified_file_count"] == 3
    assert accepted["errors"] == []

    simulation_path.write_bytes(b"tampered simulation zero")
    tampered = gate._pr4_ready(receipt)
    assert tampered["ready"] is False
    assert "simulation[0]:size_mismatch" in tampered["errors"]
    assert "simulation[0]:hash_mismatch" in tampered["errors"]


def test_mechanical_pr4_readiness_never_self_authorizes_deletion():
    gate = _load("k1_e2e_cache_gate")
    decision = gate._deletion_decision(cache_green=True, pr4_ready=True)
    assert decision["mechanically_deletion_eligible"] is True
    assert decision["explicit_storage_swap_authorization_provided"] is False
    assert decision["safe_to_delete_raw"] is False
