"""Pass native BASS templates through the registered Commander linear map estimator."""
import argparse
import csv
import hashlib
import io
import json
import tarfile
from pathlib import Path

import healpy as hp
import numpy as np

from scripts.r108.s6_b03_templates import T_CMB_UK, coefficients, orientations

FAMILIES = ("I", "II", "III", "IV", "V", "VI0", "VIh", "VIstar", "VII0", "VIIh", "VIII", "IX")
REGISTERED = Path(__file__).resolve().parents[2] / (
    "docs/research_program/observational_publication_20261015/"
    "R108_LOS_ATLAS_DATA_20261124/SOLVER/S6_B03_TEMPLATES.json")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def modes(raw):
    rows = list(csv.DictReader(io.StringIO(raw.decode()), delimiter="\t"))
    lmax = max(int(r["ell"]) for r in rows)
    data = {(int(r["ell"]), int(r["m"])): np.array([
        complex(float(r[f+"_re"]), float(r[f+"_im"])) for f in "TEB"]) for r in rows}
    keys = {(l, m) for l in range(lmax+1) for m in range(-l,l+1)}
    if set(data) != keys or len(rows) != len(keys):
        raise ValueError("missing or duplicate (ell,m)")
    if not all(np.isfinite(a).all() for a in data.values()):
        raise ValueError("nonfinite alm")
    for (l, m), a in data.items():
        if not np.allclose(data[l,-m], (-1)**m*a.conj(), atol=1e-15, rtol=1e-13):
            raise ValueError("inconsistent negative m")
    ls, ms = hp.Alm.getlm(lmax)
    return lmax, np.asarray([data[int(l),int(m)] for l,m in zip(ls,ms)]).T.copy()


def project(kernel_path, archive_path, out, modes_name="modes.tsv"):
    """modes_name selects the archive member per family: R109 forward
    Lagrangian modes ("modes.tsv", l<=4) or the R110 line-of-sight replay
    ("los_modes.tsv", any l up to the instrument kernel band limit)."""
    receipt = json.loads(REGISTERED.read_text())["kernel"]
    if sha(kernel_path) != receipt["kernel_sha256"]:
        raise ValueError("kernel bytes differ from the R108 released mask and beam operator")
    euler = orientations()
    with np.load(kernel_path) as npz:
        k = dict(npz)
    L, nside = int(k["lmax"]), int(k["nside"])
    pix = hp.pixwin(nside, pol=True, lmax=L)
    response = [k["beam_int"]*pix[0], k["beam_pol"]*pix[1], k["beam_pol"]*pix[1]]
    npix = hp.nside2npix(nside)
    skysets = ("fullsky", "masked")
    out.mkdir(exist_ok=False, parents=True)
    store = {s: np.empty((len(FAMILIES),len(euler),3,5)) for s in skysets}
    summaries = []
    verif = 0.
    with tarfile.open(archive_path, "r:gz") as ar:
        for i, family in enumerate(FAMILIES):
            raw = ar.extractfile("recoil_"+family+"/"+modes_name).read()
            ell, data = modes(raw)
            if ell>L:
                raise ValueError("template exceeds instrument kernel bandlimit")
            lvals,mvals = hp.Alm.getlm(ell)
            reindex = hp.Alm.getidx(L,lvals,mvals)
            beams = np.array([b[lvals] for b in response])
            template = data * T_CMB_UK * beams
            args = {s: [k[s+"_kT"][...,reindex], k[s+"_kP"][...,reindex],
                        k[s+"_T"], k[s+"_P"], npix] for s in skysets}
            # Independent layout check: apply the unmodified original operator to padded data.
            padded = np.zeros((3,hp.Alm.getsize(L)), dtype=complex)
            padded[:,reindex] = template
            for s in skysets:
                ref = coefficients(padded,k[s+"_kT"],k[s+"_kP"],k[s+"_T"],k[s+"_P"],npix)
                pred = coefficients(template,*args[s])
                verif = max(verif,float(np.max(np.abs(pred-ref)) / max(np.max(np.abs(ref)),1e-30)))
            for j,(phi,theta,psi) in enumerate(euler):
                rotated = template.copy()
                for f in rotated:
                    hp.rotate_alm(f,psi=psi,theta=theta,phi=phi)
                for s in skysets:
                    store[s][i,j] = coefficients(rotated,*args[s])
            cut,full=store["masked"][i],store["fullsky"][i]
            n = np.linalg.norm(full,axis=2)
            frac = np.linalg.norm(cut-full,axis=2) / np.maximum(n,1e-30)
            summaries.append(dict(family=family,lmax=ell,raw_modes_sha256=hashlib.sha256(raw).hexdigest(),
                                  cut_minus_full_relative_max_T_E_B=np.max(frac,axis=0).tolist(),
                                  orientation="boosted observer tetrad subsequently rotated into the Galactic estimator"))
    if verif > 1e-12:
        raise ValueError(f"compact vs full kernel {verif}")
    filename=out/"COMMANDER_NATIVE_COEFFICIENTS.npz"
    np.savez_compressed(filename,families=np.array(FAMILIES),angles_rad=euler,**store)
    record=dict(schema="htt.r109.native_commander.v1",kernel_sha256=sha(kernel_path),atlas_sha256=sha(archive_path),
                output_sha256=sha(filename),shape=list(store["masked"].shape),channels=["T","E","B"],
                units="microkelvin-equivalent template from dimensionless bolometric T,Q,U times 2725480; prescribed amplitudes",
                input="R109 active cold Thomson recoil; synthetic templates only; band-limited at supplied ell_max",
                frames="BASS final observer includes its boost; extrinsic healpy ZYZ orientations in R108 Galactic frame",
                scope="linear projection only; no observed data, noise score, physical orientation prior or calibration",
                truncated_vs_padded_max_relative=verif, summaries=summaries)
    if modes_name != "modes.tsv":
        record["modes_name"] = modes_name
        record["input"] = ("R110 line-of-sight replay of the native BASS solve; synthetic "
                           "templates only; band-limited at the supplied ell_max")
    (out/"COMMANDER_NATIVE_PROJECTION.json").write_text(json.dumps(record,indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("kernel","atlas","out"):
        parser.add_argument("--"+option,type=Path,required=True)
    parser.add_argument("--modes-name",default="modes.tsv",choices=["modes.tsv","los_modes.tsv"],
                        help="per-family archive member (R110 atlases also carry los_modes.tsv)")
    g = parser.parse_args()
    project(g.kernel,g.atlas,g.out,g.modes_name)
