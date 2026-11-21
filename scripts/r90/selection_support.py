"""R90 full-pixel Quaia selection-map comparison with exact official file identities.

This is selection geometry, not cosmological source anisotropy, and assumes
only that both HEALPix RING maps share a pixel chart. Sky coordinate
convention is intentionally UNBOUND until independently verified.
"""
from pathlib import Path
import hashlib
import numpy as np
import healpy as hp
from scripts.r90.download_minimal import ALLOWLIST, DEST

def measure():
    names=[name for name in ALLOWLIST if name.endswith(".fits")]
    maps={}
    summaries={}
    nside=64
    npix=hp.nside2npix(nside)
    v=np.asarray(hp.pix2vec(nside,np.arange(npix))).T
    dyad=v[:,:,None]*v[:,None,:]-np.eye(3)[None,:,:]/3.
    for name in names:
        path=DEST/name
        arr=hp.read_map(str(path)).astype(float)
        if len(arr)!=npix or np.any(~np.isfinite(arr)) or arr.min()<0 or arr.max()>1:
            raise ValueError("selection map invalid")
        md5=hashlib.md5(path.read_bytes()).hexdigest()
        if md5!=ALLOWLIST[name][1]:
            raise ValueError("selection map identity drift")
        delta=arr/arr.mean()-1
        dip=3*(delta[:,None]*v).mean(axis=0)
        Q=7.5*np.einsum("n,nij->ij",delta,dyad)/npix
        eig=np.linalg.eigvalsh(Q)
        maps[name]=delta
        summaries[name]={
            "bytes":path.stat().st_size,"md5":md5,"nside":nside,
            "pixel_order":"RING","coordinate_chart":"UNVERIFIED_FROM_FITS_HEADER",
            "n_pixels":npix,"min":float(arr.min()),"max":float(arr.max()),
            "mean":float(arr.mean()),"p10_p50_p90":np.percentile(arr,[10,50,90]).tolist(),
            "F_uniform_sky_selection_gt0p5":float(np.mean(arr>0.5)),
            "dipole_norm_native_map_chart":float(np.linalg.norm(dip)),
            "STF2_eigenvalues_native_map_chart":eig.tolist(),
            "STF2_frobenius_norm":float(np.linalg.norm(Q)),
            "physical_Pi":None,
        }
    a,b=names
    return {
      "schema":"htt.r90.quaia_minimal_selection_geometry/1",
      "destination":str(DEST),"source":"Zenodo Quaia record 10403370",
      "full_survey_selection_maps":summaries,
      "cross_threshold_full_pixel_delta_pearson":float(np.corrcoef(maps[a],maps[b])[0,1]),
      "same_pixelization_49152":True,
      "source_selection_status":"OBSERVED_INSTRUMENT_SELECTION_NOT_COSMOLOGY",
      "sky_frame":"UNQUALIFIED; do not compare sky orientation with Gaia VSH or CF4",
      "no_pr4_download":True,"no_external_drive_write":True,
      "physical_Pi":None,"physical_GF":None,
    }
