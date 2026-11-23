"""PR3 Commander cut-sky quadrupole fit with released beam and native pixel windows."""
import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path

from astropy.io import fits
import healpy as hp
import numpy as np

from scripts.r102.acquire_commander_pair import ensemble_job
from scripts.r102.commander_pair_check import (
    DEFAULT_MASK_INT, DEFAULT_MASK_POL, DEFAULT_OBS, _sha256_file,
)


def real_quadrupoles(x, y, z):
    """Five orthonormal real scalar harmonics, extended as homogeneous polynomials."""
    a = np.sqrt(5 / (16 * np.pi))
    b = np.sqrt(15 / (4 * np.pi))
    return np.column_stack((a * (2*z*z - x*x - y*y), -b*x*z, -b*y*z,
                            0.5*b*(x*x - y*y), b*x*y))


def design(theta, phi, response):
    """Scalar and spin +2 COSMO design. Complex coefficients denote E+iB."""
    st, ct = np.sin(theta), np.cos(theta)
    sp, cp = np.sin(phi), np.cos(phi)
    x, y = st*cp, st*sp
    scalar = np.column_stack((np.ones_like(ct), x, y, ct,
                              response[0] * real_quadrupoles(x, y, ct)))
    # Twice applying eth gives twice the STF tensor on (e_theta+i e_phi)^2.
    spin = (-2 * response[1] / np.sqrt(24)) * real_quadrupoles(
        ct*cp - 1j*sp, ct*sp + 1j*cp, -st)
    return scalar, spin


def chunk_terms(matrix, data, keep):
    X = matrix[keep]
    y = data[keep]
    if not np.isfinite(y).all() or (y.real < -1e29).any() or (y.imag < -1e29).any():
        raise ValueError("Invalid data in retained pixels")
    return X.conj().T @ X, X.conj().T @ y


def read_column(column, index):
    if column.ndim == 1:
        return column[index]
    rows, sub = np.divmod(index, column.shape[1])
    return column[rows, sub]


def fit_vectors(gram, rhs):
    t = np.linalg.solve(gram[0], rhs[0])[4:]
    p = np.linalg.solve(gram[1], rhs[1])
    return np.stack((t, p.real, p.imag))


def describe(q):
    return {"fit_uK": q.tolist(), "mean_square_uK2": np.mean(q*q, axis=1).tolist()}


def ranks(obs, simulated):
    if not simulated:
        raise ValueError("Need at least one paired realization")
    n = len(simulated)
    tail = np.sum(np.asarray(simulated) >= np.asarray(obs), axis=0)
    return {"n_pairs": n, "upper_ge_count": tail.tolist(),
            "one_sided_plus_one_ranks": ((1+tail)/(1+n)).tolist(),
            "resolution": 1/(1+n), "precision_null_qualified": False}


def reduce_files(obs, mask_t, mask_p, pairs, chunk=131072):
    if chunk < 1 or not pairs:
        raise ValueError("Positive chunk and at least one pair required")
    paths = [Path(obs), Path(mask_t), Path(mask_p)]
    labels = ["observed", "temperature_mask", "polarization_mask"]
    indices = sorted(pairs)
    for i in indices:
        for kind, path in zip(("cmb", "noise"), pairs[i], strict=True):
            if Path(path).name != ensemble_job(kind, i)["id"]:
                raise ValueError("Mismatched index or product family")
            labels.append(f"{kind}_{i:05d}")
            paths.append(Path(path))
    with ExitStack() as stack:
        hdus = [stack.enter_context(fits.open(p, memmap=True)) for p in paths]
        tables = [h[1] for h in hdus]
        ns = tables[0].header["NSIDE"]
        if ns != 2048 or tables[0].header.get("POLCCONV") != "COSMO":
            raise ValueError("Expected PR3 native COSMO observation")
        if hdus[0][2].header.get("METHOD") != "COMMANDER":
            raise ValueError("Expected Commander beam HDU")
        b = np.array([hdus[0][2].data[name][2] for name in ("INT_BEAM", "POL_BEAM")],float)
        win = np.array([p[2] for p in hp.pixwin(ns, pol=True, lmax=2)])
        response = b * win
        if not np.isfinite(response).all() or np.any(response <= 0):
            raise ValueError("Invalid quadrupole beam or pixel window")
        if any(t.header.get("NSIDE") != ns or t.header.get("ORDERING") not in ("NESTED","RING")
               for t in tables):
            raise ValueError("Incompatible HEALPix geometry")
        sky_indices = [0, *range(3,len(tables))]
        if any(tables[j].header.get(f"TUNIT{k}") != "K_CMB" for j in sky_indices for k in (1,2,3)):
            raise ValueError("Expected thermodynamic kelvin")
        expected = (("I_STOKES", "Q_STOKES", "U_STOKES"), ("TMASK",), ("PMASK",))
        for table, names in zip(tables[:3], expected, strict=True):
            if tuple(table.columns.names[:len(names)]) != names or table.header.get("COORDSYS") != "GALACTIC":
                raise ValueError("Expected Galactic PR3 IQU and common T/P masks")
        for t in tables[3:]:
            if tuple(t.columns.names) != ("INTENSITY","Q-POLARISATION","U-POLARISATION"):
                raise ValueError("Unexpected simulation fields")
        fields = [[t.data.field(k) for k in range(1 if j in (1,2) else 3)]
                  for j,t in enumerate(tables)]
        nsky = len(sky_indices)
        gram = [np.zeros((9,9)), np.zeros((5,5),complex)]
        rhs = [np.zeros((9,nsky)), np.zeros((5,nsky),complex)]
        npix = hp.nside2npix(ns)
        kept = np.zeros(2,int)
        for start in range(0,npix,chunk):
            ring = np.arange(start,min(start+chunk,npix))
            nest = hp.ring2nest(ns,ring)
            ids = [nest if t.header["ORDERING"] == "NESTED" else ring for t in tables]
            masks = [read_column(fields[j][0], ids[j]) > 0.5 for j in (1,2)]
            kept += [m.sum() for m in masks]
            Xs = design(*hp.pix2ang(ns,ring),response)
            vals = [np.column_stack([read_column(fields[j][k],ids[j]) for j in sky_indices])
                    .astype(np.float64) * 1e6 for k in range(3)]
            for j, (X, data) in enumerate(zip(Xs,(vals[0],vals[1]+1j*vals[2]),strict=True)):
                g, r = chunk_terms(X,data,masks[j])
                gram[j] += g
                rhs[j] += r
        fit = fit_vectors(gram,rhs)
    identities = {label: {"filename":p.name,"bytes":p.stat().st_size,"sha256":_sha256_file(p)}
                  for label,p in zip(labels,paths,strict=True)}
    observed = describe(fit[:,:,0])
    sims = {}
    for k,i in enumerate(indices):
        signal, noise = fit[:,:,1+2*k], fit[:,:,2+2*k]
        sims[f"{i:05d}"] = {"signal":describe(signal), "noise":describe(noise),
                              "paired":describe(signal+noise)}
    # Inject both signs into the observed score on the actual cut sky. Tests also
    # synthesize the sky independently with healpy, probing signs and normalization.
    injected = np.array([[1.,-2.,3.,-4.,5.],[-0.5,1.,-1.5,2.,-2.5],
                         [0.2,-0.4,0.6,-0.8,1.]])
    raw = [np.r_[np.zeros(4),injected[0]],injected[1]+1j*injected[2]]
    errors = {}
    for sign in (-1,1):
        shifted = [r[:,0] + sign*g@v for r,g,v in zip(rhs,gram,raw,strict=True)]
        delta = fit_vectors(gram,shifted) - fit[:,:,0]
        errors[str(sign)] = float(np.max(np.abs(delta-sign*injected)))
    return {"schema":"r105.commander.galactic.real_l2_masked_fit.v1",
            "healpy":hp.__version__, "code_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "real_basis":["m0","sqrt2 Re Y21","sqrt2 Im Y21","sqrt2 Re Y22","sqrt2 Im Y22"],
            "field_order":["T","E","B"], "input_sha256_and_bytes":identities,
            "ell":2,"nside":ns,"native_beam_TP":b.tolist(),"pixel_window_TP":win.tolist(),
            "net_response_TP":response.tolist(),"kept_fraction_TP":(kept/npix).tolist(),
            "normal_matrix_condition_TP":[float(np.linalg.cond(g)) for g in gram],
            "observed":observed,"realizations":sims,
            "rank":ranks(observed["mean_square_uK2"],[s["paired"]["mean_square_uK2"] for s in sims.values()]),
            "signed_score_injection_max_error_uK":errors}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pair", nargs=3, action="append", required=True, metavar=("INDEX","SIGNAL","NOISE"))
    parser.add_argument("--observation",type=Path,default=DEFAULT_OBS)
    parser.add_argument("--temperature-mask",type=Path,default=DEFAULT_MASK_INT)
    parser.add_argument("--polarization-mask",type=Path,default=DEFAULT_MASK_POL)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    pairs={int(i):(s,n) for i,s,n in args.pair}
    if len(pairs)!=len(args.pair):
        parser.error("Repeated realization index")
    result=reduce_files(args.observation,args.temperature_mask,args.polarization_mask,pairs)
    args.output.write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")


if __name__=="__main__":
    main()
