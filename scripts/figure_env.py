#!/usr/bin/env python3
"""Shared environment helpers for paper/research figure generation."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
WORKDIR_ROOT = Path(
    os.environ.get("HTT_WORKDIR", REPO_ROOT / "workdir")
).resolve()
OBS_BUNDLE_ROOT = Path(
    os.environ.get("HTT_OBS_BUNDLE_ROOT", WORKDIR_ROOT / "obs_bundle")
).resolve()
COMPACT_ROOT = Path(
    os.environ.get("HTT_COMPACT_ROOT", WORKDIR_ROOT / "compact_products")
).resolve()
RAW_ROOT = Path(
    os.environ.get("HTT_RAW_ROOT", WORKDIR_ROOT / "raw")
).resolve()


def configure_repo_paths() -> None:
    """Make the active `htt/` Python tree importable for figure scripts."""
    for path in (
        REPO_ROOT / "htt",
        REPO_ROOT / "htt" / "src",
        OBS_BUNDLE_ROOT,
    ):
        if path.exists() and str(path) not in sys.path:
            sys.path.insert(0, str(path))


def recombination_fixture_dir() -> Path:
    return REPO_ROOT / "htt" / "bass" / "recombination" / "fixtures"


class Bunch(dict):
    """Lightweight dict-with-attribute-access for fallback loads."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


_DESI_RAW_FILES = {
    "desi.bgs.ngc": RAW_ROOT / "desi" / "BGS_ANY_NGC_clustering.dat.fits",
    "desi.bgs.sgc": RAW_ROOT / "desi" / "BGS_ANY_SGC_clustering.dat.fits",
    "desi.lrg.ngc": RAW_ROOT / "desi" / "LRG_NGC_clustering.dat.fits",
    "desi.lrg.sgc": RAW_ROOT / "desi" / "LRG_SGC_clustering.dat.fits",
    "desi.qso.ngc": RAW_ROOT / "desi" / "QSO_NGC_clustering.dat.fits",
    "desi.qso.sgc": RAW_ROOT / "desi" / "QSO_SGC_clustering.dat.fits",
}

_DESI_COMPACT_FILES = {
    "desi.bgs.ngc": COMPACT_ROOT / "desi" / "BGS_ANY_NGC_clustering_extended.npz",
    "desi.bgs.sgc": COMPACT_ROOT / "desi" / "BGS_ANY_SGC_clustering_extended.npz",
    "desi.lrg.ngc": COMPACT_ROOT / "desi" / "LRG_NGC_clustering_extended.npz",
    "desi.lrg.sgc": COMPACT_ROOT / "desi" / "LRG_SGC_clustering_extended.npz",
    "desi.qso.ngc": COMPACT_ROOT / "desi" / "QSO_NGC_clustering_extended.npz",
    "desi.qso.sgc": COMPACT_ROOT / "desi" / "QSO_SGC_clustering_extended.npz",
}

_FALLBACK_DATASETS = {
    "cf4.query_batch": COMPACT_ROOT / "cf4" / "query_batch.npz",
    "cf4.query_single": COMPACT_ROOT / "cf4" / "query_single.json",
    "dipole_scalar_observations.consolidated": (
        COMPACT_ROOT / "dipole_scalar_observations.json"
    ),
    "obs_defaults.canonical": (
        REPO_ROOT / "htt" / "workspace" / "data" / "obs_defaults.json"
    ),
    "camb.planck2018.lensing_refs": (
        COMPACT_ROOT / "camb_planck2018_lensing_refs.npz"
    ),
}


def _decode_scalar(arr: np.ndarray) -> Any:
    if arr.shape == () and arr.dtype.kind in ("U", "S", "O"):
        return arr.item()
    return arr


def _load_npz(path: Path) -> Bunch:
    with np.load(path, allow_pickle=True) as z:
        out = Bunch()
        for key in z.files:
            out[key] = _decode_scalar(z[key])
        out["_meta"] = {"path": str(path)}
        return out


def _load_json(path: Path) -> dict[str, Any]:
    with open(path) as fh:
        return json.load(fh)


def _load_desi_raw(path: Path) -> Bunch:
    from astropy.io import fits

    with fits.open(path, memmap=True) as hdul:
        data = hdul[1].data
        out = Bunch(
            ra=np.asarray(data["RA"], dtype=np.float32),
            dec=np.asarray(data["DEC"], dtype=np.float32),
            z=np.asarray(data["Z"], dtype=np.float32),
            weight=np.asarray(data["WEIGHT"], dtype=np.float32),
        )
        for key, out_key in (
            ("WEIGHT_FKP", "weight_fkp"),
            ("WEIGHT_SYS", "weight_sys"),
            ("WEIGHT_COMP", "weight_comp"),
            ("WEIGHT_ZFAIL", "weight_zfail"),
            ("NTILE", "ntile"),
        ):
            if key in data.columns.names:
                out[out_key] = np.asarray(data[key])
        out["_meta"] = {"path": str(path), "source": "raw_fits"}
        return out


class FigureObsCatalog:
    """Figure-facing observational-data catalog with real-data fallbacks."""

    def __init__(self) -> None:
        configure_repo_paths()
        from obs_loader import ObsCatalog  # type: ignore

        self._obs = ObsCatalog(root=OBS_BUNDLE_ROOT)
        self.normalize_spectrum = ObsCatalog.normalize_spectrum

    def load(self, dataset_id: str) -> Bunch | dict[str, Any]:
        if dataset_id in _DESI_RAW_FILES:
            raw_path = _DESI_RAW_FILES[dataset_id]
            if raw_path.exists():
                return _load_desi_raw(raw_path)
            compact_path = _DESI_COMPACT_FILES[dataset_id]
            if compact_path.exists():
                return _load_npz(compact_path)
            raise FileNotFoundError(
                f"Missing DESI inputs for {dataset_id}: {raw_path} and {compact_path}"
            )

        try:
            return self._obs.load(dataset_id)
        except (FileNotFoundError, KeyError):
            pass

        fallback = _FALLBACK_DATASETS.get(dataset_id)
        if fallback and fallback.exists():
            if fallback.suffix == ".json":
                return _load_json(fallback)
            if fallback.suffix == ".npz":
                return _load_npz(fallback)

        raise FileNotFoundError(
            f"Unable to resolve dataset {dataset_id!r} from "
            f"{OBS_BUNDLE_ROOT} or fallback stores under {WORKDIR_ROOT}"
        )


def build_obs_catalog() -> FigureObsCatalog:
    return FigureObsCatalog()
