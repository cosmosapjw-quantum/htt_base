"""Read the pinned R114 deterministic BASS LOS atlas, not Delta_l(k).

Source lock is historical, not a claim of observational validation. Arrays are
signed dimensionless harmonic coefficients in the native host observer frame.
"""
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path

import numpy as np

RECEIPT_SHA = "3060f718bd9b6ee4b2a79afe8322f7fa725e0e259f77f5bf5ad7af1c749d84ca"
LEDGER_SHA = "d58481fff753df1867c015ad3c17f47ed5c28164b3cc2ef45ff71d21626ffd69"
CASES = ("FLRW","I","II","III","IV","V","VI0","VIh","VIstar","VII0","VIIh","VIII","IX")
TAGS = ("h24_s2000","h32_s2000")
CHANNELS = "TEB"
PAIRS = ("TT","TE","TB","EE","EB","BB")
HEADER = ("ell","m",*(c+"_"+part for c in (*CHANNELS,*PAIRS) for part in ("re","im")))


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _locked_json(path: Path, expected: str):
    raw = Path(path).read_bytes()
    if sha256(raw) != expected:
        raise ValueError("pinned R114 source SHA256 mismatch: "+str(path))
    return json.loads(raw)


def build_manifest(receipt: Path, ledger: Path) -> dict:
    ref = _locked_json(receipt, RECEIPT_SHA)
    logs = _locked_json(ledger, LEDGER_SHA)
    if tuple(ref["cases"]) != CASES:
        raise ValueError("unexpected R114 cases")
    bass = logs["repositories"]["bass"]
    if bass["binary_sha256"] != ref["binary_sha256"]:
        raise ValueError("R114 producer binary disagreement")
    return {
        "schema":"htt.r119.r114_deterministic_atlas/1",
        "claim_ceiling":"source-conditioned finite deterministic templates only; no stochastic covariance or family identification",
        "receipt_sha256":RECEIPT_SHA, "ledger_sha256":LEDGER_SHA,
        "producer_revision":bass["r114_commit"], "binary_sha256":ref["binary_sha256"],
        "archive_sha256":ref["tarball_sha256"], "ionization_sha256":ref["ionization_sha256"],
        "rec_source_csv_sha256":ref["rec_source_csv_sha256"],
        "observer":"host", "units":"native dimensionless",
        "opacity":"common prescribed HyRec xe; evolved host density",
        "ell_max":128, "channels":list(CHANNELS), "pairs":list(PAIRS),
        "cosmology_anchors":ref["cosmology_anchors"], "common_shear_6":ref["common_shear_6"],
        "cases":{
            name:{"expected_type":c["expected_type"], "lie_ic":c["lie_ic"],
                  "zero_tilt_case":c["zero_tilt_case"],
                  "runs":{tag:{
                      "relative_path":f"{name}/{tag}/los_modes.tsv",
                      "sha256":c["runs"][tag]["los_modes_sha256"],
                      "frames":c["runs"][tag]["frames"],
                      "selected_cl":c["runs"][tag]["los_cl_summary_selected_ells"],
                      "max_abs_gauss_residual":c["runs"][tag]["max_abs_gauss_residual"],
                      "max_codazzi_residual_norm":c["runs"][tag]["max_codazzi_residual_norm"],
                      "max_abs_jacobi_residual":c["runs"][tag]["max_abs_jacobi_residual"],
                  } for tag in TAGS}}
            for name,c in ref["cases"].items()},
        "historical_acceptance":ref["acceptance"],
    }


def decode_signed_modes(raw: bytes, ell_max: int) -> tuple[np.ndarray,np.ndarray]:
    """Validate one all-m LOS table and reconstruct deterministic spectra."""
    if type(ell_max) is not int or ell_max < 0:
        raise ValueError("invalid ell_max")
    if not raw or tuple(raw.splitlines()[0].decode().split()) != HEADER:
        raise ValueError("invalid native LOS header")
    table = np.loadtxt(io.BytesIO(raw),skiprows=1,ndmin=2)
    ell = np.repeat(np.arange(ell_max+1),2*np.arange(ell_max+1)+1)
    m = np.concatenate([np.arange(-l,l+1) for l in range(ell_max+1)])
    if table.shape != ((ell_max+1)**2,len(HEADER)) or not np.array_equal(table[:,:2],np.column_stack((ell,m))):
        raise ValueError("invalid full signed-m layout")
    if not np.isfinite(table).all():
        raise ValueError("nonfinite native LOS data")
    a = table[:,2:8:2]+1j*table[:,3:8:2]
    if not np.allclose(a[ell*(ell+1)-m],(-1.)**m[:,None]*a.conj(),rtol=2e-12,atol=1e-18):
        raise ValueError("signed-m reality failed")
    if np.any(a[ell<2,1:] != 0):
        raise ValueError("spin-2 support below ell=2")
    cls=[]
    for j,xy in enumerate(PAIRS):
        prod=a[:,CHANNELS.index(xy[0])]*a[:,CHANNELS.index(xy[1])].conj()
        if not np.isfinite(prod).all() or not np.allclose(prod,table[:,8+2*j]+1j*table[:,9+2*j],rtol=2e-12,atol=1e-24):
            raise ValueError("inconsistent deterministic mode product "+xy)
        cls.append(np.bincount(ell,weights=prod.real)/(2*np.arange(ell_max+1)+1))
    cl=np.column_stack(cls)
    if not np.isfinite(cl).all():
        raise ValueError("nonfinite deterministic spectra")
    a.setflags(write=False); cl.setflags(write=False)
    return a,cl


@dataclass(frozen=True)
class NativeMorphologySky:
    case: str
    tag: str
    source_sha256: str
    producer_revision: str
    ell_max: int
    alm: np.ndarray
    cl: np.ndarray

    def band(self, ell_min: int, ell_max: int) -> np.ndarray:
        if type(ell_min) is not int or type(ell_max) is not int or not 0 <= ell_min <= ell_max <= self.ell_max:
            raise ValueError("invalid harmonic band")
        return self.alm[ell_min**2:(ell_max+1)**2]


class NativeMorphologyAtlas:
    """Explicit source-bound access; no inference and no interpolation in k."""

    def __init__(self, manifest: Path, raw_root: Path, receipt: Path, ledger: Path):
        expected=build_manifest(receipt,ledger)
        actual=json.loads(Path(manifest).read_text())
        if json.dumps(actual,sort_keys=True,allow_nan=False) != json.dumps(expected,sort_keys=True,allow_nan=False):
            raise ValueError("manifest differs from pinned source-derived contract")
        self._manifest=expected
        self._root=Path(raw_root).resolve(strict=True)
        if not self._root.is_dir():
            raise ValueError("raw root is not a directory")

    @property
    def cases(self):
        return CASES

    @property
    def metadata(self):
        return json.loads(json.dumps(self._manifest))

    def read(self, case: str, tag: str="h32_s2000") -> NativeMorphologySky:
        if case not in CASES or tag not in TAGS:
            raise ValueError("unsupported case or run tag")
        run=self._manifest["cases"][case]["runs"][tag]
        path=(self._root/run["relative_path"]).resolve(strict=True)
        if not path.is_relative_to(self._root):
            raise ValueError("native source path escapes raw root")
        raw=path.read_bytes()
        if sha256(raw)!=run["sha256"]:
            raise ValueError("native LOS bytes differ from pinned source: "+case+"/"+tag)
        lmax=self._manifest["ell_max"]
        a,cl=decode_signed_modes(raw,lmax)
        for l,values in run["selected_cl"].items():
            if not np.allclose(cl[int(l)], [values[x] for x in PAIRS],rtol=2e-11,atol=1e-24):
                raise ValueError("native selected spectrum disagrees with receipt")
        return NativeMorphologySky(case,tag,run["sha256"],self._manifest["producer_revision"],lmax,a,cl)
