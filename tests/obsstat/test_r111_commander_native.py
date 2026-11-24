"""Tests for scripts/r109/commander_native.py R110/R111 high-l and prefix support."""
from __future__ import annotations

import hashlib
import io
import json
import tarfile
from pathlib import Path

import healpy as hp
import numpy as np
import pytest

from scripts.r109 import commander_native as cn


def _make_modes_tsv(lmax: int, amplitude: float = 1e-5) -> bytes:
    buf = io.StringIO()
    cols = ["ell", "m", "T_re", "T_im", "E_re", "E_im", "B_re", "B_im"]
    for ch in ("TT", "TE", "TB", "EE", "EB", "BB"):
        cols.extend([f"{ch}_re", f"{ch}_im"])
    buf.write("\t".join(cols) + "\n")
    for ell in range(lmax + 1):
        for m in range(-ell, ell + 1):
            t_re = amplitude if (ell == 2 and m == 0) else (amplitude * 0.5 * (-1) ** (m < 0) if (ell == 2 and abs(m) == 1) else 0.0)
            e_re = amplitude * 0.1 if (ell == 2 and m == 0) else 0.0
            b_im = amplitude * 0.05 * (1.0 if m > 0 else (-1.0 if m < 0 else 0.0)) if (ell == 2 and abs(m) == 2) else 0.0
            vals = [t_re, 0.0, e_re, 0.0, 0.0, b_im]
            # Products zero-padded cleanly for columns not read by modes()
            prods = [0.0] * 12
            buf.write("\t".join([str(ell), str(m), *[f"{v:.16e}" for v in vals + prods]]) + "\n")
    return buf.getvalue().encode("utf-8")


def _make_synthetic_kernel(tmp_path: Path, lmax: int = 8, nside: int = 16) -> tuple[Path, str]:
    n_alm = hp.Alm.getsize(lmax)
    rng = np.random.default_rng(111)
    kT = (rng.normal(size=(9, n_alm)) + 1j * rng.normal(size=(9, n_alm))) * 1e-3
    kP = (rng.normal(size=(5, 2, n_alm)) + 1j * rng.normal(size=(5, 2, n_alm))) * 1e-3
    # Real fields have m=0 imaginary part zero.
    ls, ms = hp.Alm.getlm(lmax)
    kT[:, ms == 0] = kT[:, ms == 0].real + 0j
    kP[:, :, ms == 0] = kP[:, :, ms == 0].real + 0j
    full_T = np.eye(9) * 1e3
    masked_T = np.eye(9) * 8e2
    full_P = np.eye(5, dtype=np.complex128) * 1e3
    masked_P = np.eye(5, dtype=np.complex128) * 8e2
    kernel_path = tmp_path / "kernel.npz"
    np.savez_compressed(
        kernel_path,
        lmax=lmax,
        nside=nside,
        beam_int=np.ones(lmax + 1),
        beam_pol=np.ones(lmax + 1),
        fullsky_kT=kT,
        masked_kT=kT,
        fullsky_T=full_T,
        masked_T=masked_T,
        fullsky_kP=kP,
        masked_kP=kP,
        fullsky_P=full_P,
        masked_P=masked_P,
    )
    return kernel_path, hashlib.sha256(kernel_path.read_bytes()).hexdigest()


def test_commander_native_modes_name_and_member_prefix(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kernel_path, ksha = _make_synthetic_kernel(tmp_path, lmax=8, nside=16)
    reg = tmp_path / "REG.json"
    reg.write_text(json.dumps({"kernel": {"kernel_sha256": ksha}}))
    monkeypatch.setattr(cn, "REGISTERED", reg)

    tar_path = tmp_path / "atlas.tar.gz"
    raw_l6 = _make_modes_tsv(6)
    with tarfile.open(tar_path, "w:gz") as tf:
        for fam in cn.FAMILIES:
            info = tarfile.TarInfo(f"long_{fam}/los_modes.tsv")
            info.size = len(raw_l6)
            tf.addfile(info, io.BytesIO(raw_l6))

    out_dir = tmp_path / "proj"
    cn.project(kernel_path, tar_path, out_dir, modes_name="los_modes.tsv", member_prefix="long_")
    meta = json.loads((out_dir / "COMMANDER_NATIVE_PROJECTION.json").read_text())
    assert meta["modes_name"] == "los_modes.tsv"
    assert meta["member_prefix"] == "long_"
    assert meta["truncated_vs_padded_max_relative"] < 1e-12
    assert meta["shape"] == [12, 384, 3, 5]
    assert all(s["lmax"] == 6 for s in meta["summaries"])


def test_commander_native_rejects_above_bandlimit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    kernel_path, ksha = _make_synthetic_kernel(tmp_path, lmax=4, nside=16)
    reg = tmp_path / "REG.json"
    reg.write_text(json.dumps({"kernel": {"kernel_sha256": ksha}}))
    monkeypatch.setattr(cn, "REGISTERED", reg)

    tar_path = tmp_path / "atlas_too_high.tar.gz"
    raw_l6 = _make_modes_tsv(6)
    with tarfile.open(tar_path, "w:gz") as tf:
        for fam in cn.FAMILIES:
            info = tarfile.TarInfo(f"recoil_{fam}/los_modes.tsv")
            info.size = len(raw_l6)
            tf.addfile(info, io.BytesIO(raw_l6))

    with pytest.raises(ValueError, match="bandlimit"):
        cn.project(kernel_path, tar_path, tmp_path / "out_fail", modes_name="los_modes.tsv")
