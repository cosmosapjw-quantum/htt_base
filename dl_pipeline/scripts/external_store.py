#!/usr/bin/env python3
"""
external_store.py - keep bulk external data off the repository filesystem
=========================================================================

Every external observational product the pipeline downloads or extracts is
addressed as ``<root>/<something>`` where ``<root>`` is the repository
``workdir/``. That directory sits on the 1 TB system NVMe inside a Dropbox
tree; the bulk data belongs on the 2 TB NVMe instead.

This module makes that placement automatic. Call :func:`ensure_data_dir`
wherever the pipeline would have called ``Path.mkdir(parents=True)``. The
returned path is the caller's original repository-side path, so no downstream
code, manifest, or test needs to learn about the second disk: reads and writes
go through a symlink.

Placement rules
---------------

Links are created on the *children* of ``workdir/`` and of ``workdir/raw/``,
never on those two directories themselves:

* ``workdir/`` carries the extended attribute ``com.dropbox.ignored=1``, which
  is what keeps the Dropbox daemon from descending into it. A symlink cannot
  carry that guarantee, and Dropbox follows directory symlinks.
* the external ``raw/`` tree holds acquisitions that are deliberately not
  exposed to the repository (e.g. Planck NPIPE PR4); linking ``raw/`` wholesale
  would make them appear under ``workdir/raw/``.

``workdir/logs/`` stays physically local: it is small, write-hot, and holds no
observational data.

Configuration
-------------

``HTT_EXTERNAL_DATA_ROOT``
    Absolute path of the external store. Defaults to
    ``/mnt/sn850x2t/htt_base_e2e/workdir`` when that volume is mounted. Set it
    to an empty string (or ``0``/``off``/``none``) to disable the redirect and
    write everything inside the repository, which is the behaviour on any host
    without the second disk.

If a redirect link exists but its target is unreachable - the usual symptom of
an unmounted external volume - this module raises rather than silently
recreating hundreds of gigabytes on the system disk.
"""
from __future__ import annotations

import os
from pathlib import Path, PurePath

REPO_ROOT = Path(__file__).resolve().parents[2]
REPO_WORKDIR = REPO_ROOT / "workdir"

ENV_VAR = "HTT_EXTERNAL_DATA_ROOT"
DEFAULT_EXTERNAL_STORE = Path("/mnt/sn850x2t/htt_base_e2e/workdir")
_DISABLED_VALUES = frozenset({"", "0", "off", "none", "no"})

# Must stay physically inside the checkout: small, write-hot, not data.
LOCAL_ONLY = frozenset({"logs"})
# Linked one level deeper than usual (see module docstring).
LINK_ONE_LEVEL_DEEPER = frozenset({"raw"})

class _Auto:
    """Sentinel distinguishing "caller said nothing, detect the store" from an
    explicit ``store=None``, which means "do not redirect at all"."""


_AUTO = _Auto()


class ExternalStoreUnavailable(RuntimeError):
    """A redirect link exists but its target cannot be reached."""


def external_store_root() -> Path | None:
    """Return the configured external store, or None when it is unavailable.

    The default is used only when the mount point is actually present, so a
    checkout on another machine degrades to plain in-repository writes.
    """
    configured = os.environ.get(ENV_VAR)
    if configured is not None:
        if configured.strip().lower() in _DISABLED_VALUES:
            return None
        return Path(configured).expanduser()
    if DEFAULT_EXTERNAL_STORE.parent.is_dir():
        return DEFAULT_EXTERNAL_STORE
    return None


def _link_point(rel: PurePath) -> PurePath | None:
    """Directory, relative to workdir, that carries the redirect symlink.

    None means "no redirect": create this path inside the repository.
    """
    parts = rel.parts
    if not parts or parts[0] in LOCAL_ONLY:
        return None
    if parts[0] in LINK_ONE_LEVEL_DEEPER:
        # workdir/raw itself stays a real directory; link its children.
        if len(parts) < 2 or parts[1] in LOCAL_ONLY:
            return None
        return PurePath(parts[0], parts[1])
    return PurePath(parts[0])


def _relative_to_workdir(path: Path, workdir: Path) -> PurePath | None:
    try:
        rel = path.relative_to(workdir)
    except ValueError:
        return None
    return PurePath(rel) if rel.parts else None


def ensure_data_dir(
    path: str | os.PathLike[str],
    *,
    workdir: Path | None = None,
    store: Path | None | _Auto = _AUTO,
) -> Path:
    """Create ``path``, placing bulk data on the external store when possible.

    Returns ``path`` unchanged (as a Path). Anything outside the repository
    ``workdir/`` tree, and anything covered by :data:`LOCAL_ONLY`, is simply
    created where it was asked for. Passing ``store=None`` disables the
    redirect for this call; omitting it detects the store as documented above.
    """
    path = Path(path)
    if not path.is_absolute():
        path = Path.cwd() / path
    path = Path(os.path.normpath(path))

    workdir = Path(workdir) if workdir is not None else REPO_WORKDIR
    workdir = Path(os.path.normpath(workdir.absolute()))

    rel = _relative_to_workdir(path, workdir)
    if rel is None:
        path.mkdir(parents=True, exist_ok=True)
        return path

    link_rel = _link_point(rel)
    if link_rel is None:
        path.mkdir(parents=True, exist_ok=True)
        return path

    link = workdir / link_rel
    if link.is_symlink() and not link.exists():
        raise ExternalStoreUnavailable(
            f"{link} points at {os.readlink(link)}, which is not reachable. "
            "Mount the external data volume, or set "
            f"{ENV_VAR}= to write inside the repository."
        )
    if link.exists():
        # Already a real directory or an intact redirect; nothing to decide.
        path.mkdir(parents=True, exist_ok=True)
        return path

    resolved_store = external_store_root() if isinstance(store, _Auto) else store
    if resolved_store is None:
        path.mkdir(parents=True, exist_ok=True)
        return path

    target = Path(resolved_store) / link_rel
    target.mkdir(parents=True, exist_ok=True)
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(target.absolute())
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_data_parent(
    path: str | os.PathLike[str],
    *,
    workdir: Path | None = None,
    store: Path | None | _Auto = _AUTO,
) -> Path:
    """Create the parent directory of a file destination. Returns the file path."""
    path = Path(path)
    ensure_data_dir(path.parent, workdir=workdir, store=store)
    return path
