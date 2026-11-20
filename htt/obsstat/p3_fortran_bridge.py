"""R83 optional source-hash-certified Fortran H03 joint sufficient statistics.

Returns F_j, b_j and source raw 36x36 G_jk information blocks. These are not
covariance blocks until profiled through the same source F_j^-1.
"""
from __future__ import annotations

import ctypes,fcntl,hashlib,json,os,platform,shutil,subprocess,tempfile
from functools import lru_cache
from pathlib import Path
import numpy as np

SOURCE=Path(__file__).parent/"native"/"p3_multiwindow_source.f90"
CFG=Path(__file__).with_name("p2p3_lane.json")


def _digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()


@lru_cache(maxsize=4)
def _compile_fortran(source_sha):
    compiler=shutil.which("gfortran")
    if compiler is None:raise RuntimeError("gfortran unavailable")
    flags=["-O3","-fPIC","-shared","-fopenmp","-fno-fast-math"]
    version=subprocess.check_output([compiler,"--version"],text=True,timeout=10).splitlines()[0]
    key=hashlib.sha256((source_sha+str(flags)+version+platform.machine()).encode()).hexdigest()[:24]
    folder=Path(os.environ.get("HTT_NATIVE_CACHE_DIR",
                str(Path(tempfile.gettempdir())/"htt_r79_native_cache")))/"r83"/"fortran"/key
    folder.mkdir(parents=True,exist_ok=True)
    output=folder/"libhtt_r83_source_fortran.so"
    receipt=folder/"manifest.json"
    with (folder/"lock").open("a+b") as fp:
        fcntl.flock(fp,fcntl.LOCK_EX)
        if output.exists() and receipt.exists():
            try:
                obj=json.loads(receipt.read_text())
                if obj["source_sha256"]==source_sha and obj["binary_sha256"]==_digest(output):
                    return str(output)
            except (OSError,ValueError,TypeError,KeyError):
                pass
        temp=folder/f"temp_{os.getpid()}.so"
        try:
            subprocess.run([compiler,*flags,str(SOURCE),"-o",str(temp)],
                           capture_output=True,text=True,check=True,timeout=90)
            if not temp.is_file() or temp.stat().st_size==0:
                raise RuntimeError("Fortran source compilation produced no library")
            os.replace(temp,output)
            receipt.write_text(json.dumps({
                "compiler":version,"flags":flags,"source_sha256":source_sha,
                "binary_sha256":_digest(output)},sort_keys=True)+"\n")
        finally:
            if temp.exists():temp.unlink()
    return str(output)


def _certified_fortran():
    policy=json.loads(CFG.read_text())
    src=_digest(SOURCE)
    if policy.get("fortran_source_sha256")!=src:
        raise RuntimeError("Fortran source hash not certified")
    lib=Path(_compile_fortran(src))
    receipt=lib.with_name("manifest.json")
    if not lib.exists() or not receipt.exists():
        raise RuntimeError("source-certified Fortran binary/manifest missing")
    data=json.loads(receipt.read_text())
    if data["source_sha256"]!=src or data["binary_sha256"]!=_digest(lib):
        raise RuntimeError("Fortran binary hash invalid")
    return str(lib)


def fortran_sufficient_statistics(X,y,weights,sigma,libpath,threads=4):
    """Consume already validated contiguous float64 exact H03 source arrays."""
    lib=ctypes.CDLL(str(Path(libpath).resolve()))
    fn=lib.htt_p3_multiwindow_source_v1
    fp=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
    fn.argtypes=[ctypes.c_int64,fp,fp,fp,fp,ctypes.c_int32,fp,fp,fp,
                 ctypes.POINTER(ctypes.c_int)]
    fn.restype=None
    n=len(X)
    F=np.empty((4,9,9),np.float64)
    b=np.empty((4,9),np.float64)
    G=np.empty((36,36),np.float64)
    status=ctypes.c_int(-1)
    fn(n,X,weights,y,sigma,threads,F,b,G,ctypes.byref(status))
    if status.value or not all(np.isfinite(x).all() for x in (F,b,G)):
        raise RuntimeError(f"R83 native Fortran source reducer failed {status.value}")
    return F,b,G
