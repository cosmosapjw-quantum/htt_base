"""
obs_loader.py
=============

Unified loader for the BASS observational dataset bundle.

Usage
-----
    from obs_loader import ObsCatalog

    cat = ObsCatalog()                # auto-detects obs/ relative to this file
    print(cat.list_ids())             # all dataset_ids

    # Power spectrum (returns a dict-like Bunch with attribute access)
    pl_tt = cat.load("planck.pr3.tt_full")
    ell, dl, err = pl_tt.ell, pl_tt.dl, pl_tt.err_lo

    # JSON (returns a plain dict)
    obs = cat.load("obs_defaults.canonical")
    beta = obs["dipole_observations"]["cf4_watkins_2023"]["beta"]

    # Map (Healpy NSIDE=16, RING)
    cmd = cat.load("planck.commander.nside16")
    I, mask = cmd.I, cat.load("planck.temp_mask.nside16").mask

    # By collection
    for did in cat.ids_in("cmb.powerspectra"):
        print(did, cat.meta(did)["spectrum"])

Conventions
-----------
- All Dl values are in uK^2 unless otherwise noted in INDEX.json.
- Healpix maps use the RING ordering (healpy default).
- DESI catalogs use float32 throughout.
- Power-spectrum NPZs share a common (ell, dl, err_lo, err_hi, ...) schema
  across Planck / ACT, but ACT uses (dl, dl_err) while Planck uses
  (dl, err_lo, err_hi). Use cat.normalize_spectrum() if you need a uniform
  (ell, dl, sigma) view.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterator

import numpy as np


__all__ = ["ObsCatalog", "Bunch"]


class Bunch(dict):
    """Dict that exposes its keys as attributes. Returned by NPZ loads."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __dir__(self):
        return list(self.keys()) + list(super().__dir__())


class ObsCatalog:
    """Single entry point for every observational dataset in the bundle."""

    def __init__(self, root: str | Path | None = None):
        if root is None:
            root = Path(__file__).resolve().parent
        self.root = Path(root)
        index_path = self.root / "INDEX.json"
        if not index_path.exists():
            raise FileNotFoundError(
                f"INDEX.json not found at {index_path}. "
                f"Pass root=/path/to/obs to ObsCatalog()."
            )
        with open(index_path) as f:
            self._index = json.load(f)

    # ---------------- discovery ----------------

    def collections(self) -> list[str]:
        return [k for k in self._index.keys() if not k.startswith("_")]

    def list_ids(self) -> list[str]:
        ids = []
        for col in self.collections():
            for key in self._index[col]:
                if key.startswith("_"):
                    continue
                ids.append(key)
        return ids

    def ids_in(self, collection: str) -> list[str]:
        if collection not in self._index:
            raise KeyError(f"Unknown collection {collection!r}. Have: {self.collections()}")
        return [k for k in self._index[collection] if not k.startswith("_")]

    def meta(self, dataset_id: str) -> dict:
        """Return the INDEX.json metadata block for a dataset_id."""
        for col, block in self._index.items():
            if col.startswith("_"):
                continue
            if dataset_id in block:
                meta = dict(block[dataset_id])
                meta["_collection"] = col
                return meta
        raise KeyError(f"Unknown dataset_id {dataset_id!r}. Try cat.list_ids().")

    # ---------------- loading ----------------

    def load(self, dataset_id: str) -> Bunch | dict:
        """Load a dataset by id. Returns Bunch (NPZ) or dict (JSON)."""
        meta = self.meta(dataset_id)
        path = self.root / meta["path"]
        if not path.exists():
            raise FileNotFoundError(f"Missing data file: {path}")

        if path.suffix == ".npz":
            with np.load(path, allow_pickle=True) as z:
                out = Bunch()
                for k in z.files:
                    arr = z[k]
                    # Decode 0-d string arrays into plain Python str.
                    if arr.shape == () and arr.dtype.kind in ("U", "S", "O"):
                        out[k] = arr.item()
                    else:
                        out[k] = arr
                out["_meta"] = meta
                return out

        if path.suffix == ".json":
            with open(path) as f:
                return json.load(f)

        raise ValueError(f"Unsupported file type: {path.suffix}")

    # ---------------- helpers ----------------

    @staticmethod
    def normalize_spectrum(b: Bunch) -> Bunch:
        """
        Return a (ell, dl, sigma) view that works for both Planck and ACT.

        Planck NPZs carry (err_lo, err_hi); we use err_lo as a symmetric proxy.
        ACT NPZs carry dl_err.
        """
        out = Bunch()
        out["ell"] = np.asarray(b["ell"])
        out["dl"] = np.asarray(b["dl"])
        if "err_lo" in b:
            out["sigma"] = np.asarray(b["err_lo"])
        elif "dl_err" in b:
            out["sigma"] = np.asarray(b["dl_err"])
        else:
            raise KeyError("No error column found (need err_lo or dl_err).")
        return out

    def find(self, *, spectrum: str | None = None,
             instrument: str | None = None) -> list[str]:
        """Filter datasets by spectrum (TT/TE/EE/BB/EB) or instrument substring."""
        out = []
        for did in self.list_ids():
            try:
                m = self.meta(did)
            except KeyError:
                continue
            if spectrum is not None and m.get("spectrum") != spectrum:
                continue
            if instrument is not None and instrument.lower() not in did.lower():
                continue
            out.append(did)
        return out

    # ---------------- repr ----------------

    def __repr__(self) -> str:
        n = len(self.list_ids())
        return f"<ObsCatalog root={self.root} n_datasets={n}>"


# ---------------- module-level convenience ----------------

_default_catalog: ObsCatalog | None = None


def default() -> ObsCatalog:
    """Singleton helper: `obs_loader.default().load(...)`."""
    global _default_catalog
    if _default_catalog is None:
        _default_catalog = ObsCatalog()
    return _default_catalog


def load(dataset_id: str) -> Bunch | dict:
    """Shortcut: `obs_loader.load("planck.pr3.tt_full")`."""
    return default().load(dataset_id)


def list_ids() -> list[str]:
    return default().list_ids()


if __name__ == "__main__":
    cat = ObsCatalog()
    print(cat)
    print()
    print("Collections:")
    for c in cat.collections():
        ids = cat.ids_in(c)
        print(f"  [{c}] {len(ids)} datasets")
        for did in ids:
            print(f"     - {did}")
