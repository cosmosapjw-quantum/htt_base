"""REG-02 — artifact filename prefix guard (INDEPENDENT_TRACKS_PLAN v1.2 §14.2).

BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3 §14.1 requires every MIO-generated
artifact filename to carry the `mio_` prefix (so G19 hard separation is
visible at the filesystem level, not only in type hints).

This test acts as a **forward guard**: it scans every existing production
module under `bass_py/mio/` (Week 6+ landing) and
`bass_py/htt/htt/PR13AM_*.py` (Week 5 Day 5 PR13AM-MIO-TAG will add the
`_mio_artifact_name` helper) for string literals shaped like JSON / NPZ
filenames. If such a literal is found and does not begin with `mio_`, the
test fails loudly. Until MIO code lands, the scan is vacuous / trivially
passing, preserving additive-commits discipline.
"""
from __future__ import annotations

import re
from pathlib import Path


# Match things that look like filename literals for MIO-ish outputs:
# strings of the form "<basename>.json" / ".npz" / ".npy" / ".h5" inside
# Python string literals. We only care about artifacts produced by MIO
# code, so we scope the scan to MIO-owned modules.
_ARTIFACT_RE = re.compile(r"""['"]([A-Za-z0-9_\-]+\.(json|npz|npy|h5|parquet))['"]""")


def _repo_root() -> Path:
    # test file lives at bass_py/workspace/contracts/tests/test_*.py
    return Path(__file__).resolve().parents[4]


def _mio_owned_files(root: Path) -> list[Path]:
    mio_pkg = root / "bass_py" / "mio"
    files: list[Path] = []
    if mio_pkg.is_dir():
        for py in mio_pkg.rglob("*.py"):
            if "/tests/" in str(py) or py.name.startswith("test_"):
                continue
            files.append(py)

    # PR13AM is semantically MIO-owned per v1.1 PATCH-01 (PR13AM-MIO-TAG,
    # landing Day 5). Scan it too — the `__mio_owned__` flag is the
    # signal; only those files that carry it are MIO-owned.
    htt_core = root / "bass_py" / "htt" / "htt"
    if htt_core.is_dir():
        for py in htt_core.rglob("PR13AM_*.py"):
            text = py.read_text(encoding="utf-8", errors="ignore")
            if "__mio_owned__" in text:
                files.append(py)
    return files


def test_mio_artifact_filename_has_mio_prefix():
    root = _repo_root()
    offenders: list[tuple[str, int, str]] = []
    for py in _mio_owned_files(root):
        text = py.read_text(encoding="utf-8", errors="ignore")
        for n, line in enumerate(text.splitlines(), start=1):
            # Skip comments and docstrings — only flag actual code literals.
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            for match in _ARTIFACT_RE.finditer(line):
                stem = match.group(1)
                if stem.startswith("mio_"):
                    continue
                # Allow legacy-era filenames IF the line is explicitly a
                # cross-reference (contains 'legacy' or 'shim').
                lowered = line.lower()
                if "legacy" in lowered or "shim" in lowered:
                    continue
                offenders.append((str(py.relative_to(root)), n, stripped))

    assert not offenders, (
        "v3 §14.1 violation: MIO-owned module produces an artifact "
        "without the mandatory 'mio_' prefix:\n"
        + "\n".join(f"  {p}:{n}: {s}" for p, n, s in offenders)
    )
