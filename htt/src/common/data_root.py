"""PR-188: checksum-bound external-data-root resolution (H20).

Data-dependent cards must resolve the external cache through this resolver
(``HTT_DATA_ROOT`` env, default the documented NVMe path) rather than a
hard-coded private absolute path. Missing data raises ``DataUnavailable``,
which callers surface as an explicit BLOCKED exit -- never a silent skip.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

DEFAULT_DATA_ROOT = "/mnt/sn850x2t/htt_base_e2e"
ENV_VAR = "HTT_DATA_ROOT"


class DataUnavailable(RuntimeError):
    """Raised when a required external-data artifact is absent or mismatched."""


def data_root() -> Path:
    return Path(os.environ.get(ENV_VAR, DEFAULT_DATA_ROOT))


def resolve(relative: str, *, sha256: str | None = None) -> Path:
    """Resolve ``relative`` under the data root; verify the checksum if given.

    Raises DataUnavailable (never a silent skip) when the file is missing or
    its checksum does not match.
    """
    path = data_root() / relative
    if not path.is_file():
        raise DataUnavailable(
            f"required external data absent: {path} "
            f"(set {ENV_VAR} or stage the data recipe)"
        )
    if sha256 is not None:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != sha256:
            raise DataUnavailable(
                f"external data checksum mismatch for {path}: {digest} != {sha256}"
            )
    return path


def recipe_status(entries: list[dict]) -> dict:
    """Report resolution status for a recipe (list of {relative, sha256}).

    Never raises; returns a status dict. ``all_present`` drives the caller's
    BLOCKED exit.
    """
    resolved, missing = [], []
    for entry in entries:
        try:
            resolve(entry["relative"], sha256=entry.get("sha256"))
            resolved.append(entry["relative"])
        except DataUnavailable:
            missing.append(entry["relative"])
    return {
        "data_root": str(data_root()),
        "resolved": resolved,
        "missing": missing,
        "all_present": not missing,
        "blocked_exit_on_missing": 2,
    }
