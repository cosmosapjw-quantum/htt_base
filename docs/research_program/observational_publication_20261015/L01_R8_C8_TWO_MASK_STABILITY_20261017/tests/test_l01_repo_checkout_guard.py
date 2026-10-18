"""Host-neutral tests for exact-head and import-gated repo execution."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

PROGRAMME = Path(__file__).resolve().parents[2]
SCRIPT = PROGRAMME / "L01_R10_C10_RUNTIME_RECOVERY_20261017" / "scripts" / "l01_checkout_guard.py"
spec = importlib.util.spec_from_file_location("l01_checkout_guard", SCRIPT)
guard = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(guard)


def _git(root, *args):
    p = subprocess.run(["git", "-C", str(root), *args],
                       check=True, capture_output=True, text=True)
    return p.stdout.strip()


def fake_checkout(tmp_path):
    root = tmp_path / "checkout"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "htt-test@example.invalid")
    _git(root, "config", "user.name", "HTT Test")
    for f in guard.REQUIRED:
        p = root / f
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("# fixture\n", encoding="utf-8")
    _git(root, "add", ".")
    _git(root, "commit", "-qm", "fixture")
    head = _git(root, "rev-parse", "HEAD")
    _git(root, "update-ref", "refs/remotes/" + guard.EXPECTED_REF, head)
    return root


def test_guard_accepts_exact_clean_head(tmp_path):
    root = fake_checkout(tmp_path)
    out = guard.check_checkout(root, smoke=False)
    assert out["status"] == "PASS_EXACT_HEAD_CLEAN_IMPORTS"
    assert out["head"] == _git(root, "rev-parse", "HEAD")


def test_guard_blocks_stale_branch_even_with_files_present(tmp_path):
    root = fake_checkout(tmp_path)
    (root / "different.txt").write_text("new\n")
    _git(root, "add", "different.txt")
    _git(root, "commit", "-qm", "newer")
    with pytest.raises(guard.CheckoutError, match="STALE_CHECKOUT_HEAD"):
        guard.check_checkout(root, smoke=False)


def test_guard_blocks_dirty_head_to_preserve_work(tmp_path):
    root = fake_checkout(tmp_path)
    (root / "original_notes.txt").write_text("preserve me\n")
    with pytest.raises(guard.CheckoutError, match="DIRTY_WORKTREE"):
        guard.check_checkout(root, smoke=False)
    assert (root / "original_notes.txt").read_text() == "preserve me\n"


def test_guard_blocks_missing_predecessor_source(tmp_path):
    root = fake_checkout(tmp_path)
    (root / guard.REQUIRED[-2]).unlink()
    # A removed tracked file also marks checkout dirty, which is intentionally blocked first.
    with pytest.raises(guard.CheckoutError, match="DIRTY_WORKTREE"):
        guard.check_checkout(root, smoke=False)


def test_guard_accepts_explicit_continuation_remote_ref(tmp_path):
    root = fake_checkout(tmp_path)
    ref = "origin/research/authorized-continuation"
    _git(root, "update-ref", "refs/remotes/" + ref, _git(root, "rev-parse", "HEAD"))
    out = guard.check_checkout(root, ref, smoke=False)
    assert out["remote_ref"] == ref
    assert out["head"] == _git(root, "rev-parse", "HEAD")


def test_existing_versioned_scripts_import_and_expose_options():
    root = PROGRAMME.parents[2]
    scripts = [
        ("l01_mask_difference_stability.py", "--spectral-receipt"),
        ("l01_r9c9_same_sky_beam.py", "--c8-receipt"),
        ("fetch_planck_pr3_smica.py", "--attempts"),
    ]
    for name, option in scripts:
        src = PROGRAMME / "L01_R8_C8_TWO_MASK_STABILITY_20261017" / "src" / name
        p = subprocess.run([sys.executable, str(src), "--help"],
                           cwd=root, capture_output=True, text=True, timeout=30)
        assert p.returncode == 0, p.stderr
        assert option in p.stdout
