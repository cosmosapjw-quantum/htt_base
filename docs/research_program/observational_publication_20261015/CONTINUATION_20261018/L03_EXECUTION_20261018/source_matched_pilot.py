"""Eight genuine FFP10 I/Q/U pairs through original L01 child-average OLS.

No SHT, deconvolution, observed-map reread, covariance inversion or PTE.
The fixed-weight full-mission experiment is diagnostic, not joint HM/OE law.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import resource
import sys
import time

import numpy as np
from astropy.io import fits
from scipy.linalg import cho_factor, cho_solve

HERE = Path(__file__).resolve().parent
PROGRAMME = HERE.parents[1]
REPO = PROGRAMME.parents[2]
sys.path.insert(0, str(REPO / "htt"))
sys.path.insert(0, str(PROGRAMME / "L01_R8_C8_TWO_MASK_STABILITY_20261017/src"))
sys.path.insert(0, str(HERE.parent / "L01_EXECUTION_20261018"))
from original_selected_support import parent_coverage
import l01_smica_processed_bands as producer
from spin2_finite import block_design
from obsstat.r7_cmb_product_response import pixel_fit_geometry

RAW = Path("/mnt/extdrive/workdir/raw/planck_ffp10/smica")
MANIFEST = RAW / "logs/SHA256SUMS.raw_fits.available1299.txt"
CACHE = REPO / "workdir/compact_products/planck_pr3_pr150/k1_ffp10_reduced_smica.npz"
CACHE_SHA = "86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"
BRIDGE = HERE.parent / "L01_EXECUTION_20261018/results/ORIGINAL_SELECTED_SUPPORT_RESPONSE.json"
BRIDGE_SHA = "bbb250b0288df040cc9273ef8483b91ae8253d5b720f3f22ee817cd846a36205"
FIELDS = ("INTENSITY", "Q-POLARISATION", "U-POLARISATION")
T_MASK_SHA = {
    "common": "23f49a3479073408b83a7f1bb2cca490d9be7f934b2e0e891524b6a1d06a5fc4",
    "HM-Misspix": "f4fd909734d80fb80214018b3ef9b44a378a4d04418337786c48f6d388dfb2a0",
    "OE-Misspix": "ecb39152ad5b93ea309baf396aad404a062edd6745a30c0b941b3556ca28aff9",
}


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def identity(path, expected=None):
    path = Path(path)
    actual = digest(path)
    if expected is not None and actual != expected:
        raise ValueError("IMMUTABLE_SOURCE_BYTE_MISMATCH: " + str(path))
    return {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}


def validate_pairs(signal_ids, noise_ids):
    a, b = np.asarray(signal_ids), np.asarray(noise_ids)
    if (a.shape != (8,) or b.shape != (8,) or
            a.dtype.kind not in "iu" or b.dtype.kind not in "iu" or
            len(set(a.tolist())) != 8 or len(set(b.tolist())) != 8 or
            not np.array_equal(a, b) or not np.array_equal(a, np.arange(8))):
        raise ValueError("EXACT_EIGHT_DISTINCT_MATCHED_IDS_REQUIRED_NO_REUSE")


def linear_projector(design, selected):
    a = np.asarray(design)[selected]
    gram = a.T @ a
    eigen = np.linalg.eigvalsh(gram)
    if eigen[0] <= 0 or eigen[-1] / eigen[0] > 1e12:
        raise ValueError("ORIGINAL_OLS_NOT_IDENTIFIABLE")
    op = cho_solve(cho_factor(gram, lower=True), a.T)
    error = float(np.max(np.abs(op @ a - np.eye(a.shape[1]))))
    if error > 1e-9:
        raise ValueError("ORIGINAL_OLS_IDENTITY")
    return op, {"design_condition": float(np.sqrt(eigen[-1]/eigen[0])),
                "identity_max_absolute": error}


def nested_selected_mean(ring_fields, windows, selected, *, nside_in, nside_out,
                         chunk_parents=256):
    """Gather identical pixels by nest2ring; average original native children.

    Columns can be strided FITS vectors; no full-resolution dense reorder occurs.
    Q/U retain their original Galactic local-polar coordinates. Averaging does
    not parallel-transport polarization, exactly as the original observed fit.
    """
    import healpy as hp
    nout = hp.nside2npix(nside_out)
    if (not hp.isnsideok(nside_in, nest=True) or not hp.isnsideok(nside_out, nest=True)
            or nside_in < nside_out or nside_in % nside_out or chunk_parents < 1):
        raise ValueError("NESTED_REDUCTION_GEOMETRY")
    children = (nside_in // nside_out)**2
    if (len(ring_fields) != len(windows) or len(selected) != len(windows)
            or any(np.asarray(w).dtype != bool or np.shape(w) != (nout*children,) for w in windows)
            or any(np.asarray(m).dtype != bool or np.shape(m) != (nout,) for m in selected)):
        raise ValueError("FIXED_MASK_GEOMETRY")
    selected_nest = [hp.reorder(m, r2n=True) for m in selected]
    parents = np.flatnonzero(np.logical_or.reduce(selected_nest))
    output = np.zeros((len(windows), nout), dtype=float)
    minimum_coverage = np.ones(len(windows))
    roundtrip = True
    for start in range(0, len(parents), chunk_parents):
        pp = parents[start:start+chunk_parents]
        nn = pp[:, None]*children + np.arange(children)
        rr = hp.nest2ring(nside_in, nn)
        roundtrip &= bool(np.array_equal(hp.ring2nest(nside_in, rr), nn))
        for j, (field, window, mask) in enumerate(zip(ring_fields, windows, selected_nest)):
            use = mask[pp]
            if not np.any(use):
                continue
            # FITS stores 1024-pixel RING vectors; accept a 1D control map too.
            values = (field[rr[use]] if field.ndim == 1 else
                      field[rr[use]//field.shape[1], rr[use] % field.shape[1]])
            values = np.asarray(values, dtype=float)
            valid = window[nn[use]]
            if np.any(valid & (~np.isfinite(values) | (np.abs(values) >= 1e20))):
                raise ValueError("INVALID_SOURCE_INSIDE_FIXED_SELECTED_NATIVE_WINDOW")
            count = valid.sum(axis=1)
            if np.any(count == 0):
                raise ValueError("EMPTY_SELECTED_PARENT")
            coverage = count/children
            minimum_coverage[j] = min(minimum_coverage[j], float(coverage.min()))
            output[j, pp[use]] = np.where(valid, values, 0.).sum(axis=1)/count
    if not roundtrip:
        raise ValueError("RING_NESTED_PIXEL_IDENTITY_FAILURE")
    return np.stack([hp.reorder(x, n2r=True) for x in output]), minimum_coverage


def ring_stream_selected_mean(ring_fields, windows, selected, *, nside_in, nside_out,
                              chunk_pixels=262144):
    """Same masked native-child means using sequential FITS/RING reads.

    RING traversal only changes summation order. Source pixel identity, fixed
    masks, selected parents and normalization by retained-child count are exact.
    No changes to the source law, harmonic chart, support or tolerances.
    """
    import healpy as hp
    nout, nin = hp.nside2npix(nside_out), hp.nside2npix(nside_in)
    if (not hp.isnsideok(nside_in, nest=True) or not hp.isnsideok(nside_out, nest=True)
            or nside_in < nside_out or nside_in % nside_out or chunk_pixels < 1):
        raise ValueError("NESTED_REDUCTION_GEOMETRY")
    children = (nside_in//nside_out)**2
    if (len(ring_fields) != len(windows) or len(selected) != len(windows)
            or any(np.asarray(w).dtype != bool or np.shape(w) != (nin,) for w in windows)
            or any(np.asarray(m).dtype != bool or np.shape(m) != (nout,) for m in selected)):
        raise ValueError("FIXED_MASK_GEOMETRY")
    for field in ring_fields:
        if field.ndim not in (1, 2) or field.size != nin or np.iscomplexobj(field):
            raise ValueError("RING_SOURCE_LAYOUT")
        if field.ndim == 2 and chunk_pixels % field.shape[1]:
            raise ValueError("RING_CHUNK_MUST_ALIGN_FITS_VECTOR_ROWS")
    selected_nest = [hp.reorder(m, r2n=True) for m in selected]
    sums = np.zeros((len(windows), nout), float)
    counts = np.zeros((len(windows), nout), np.int64)
    for start in range(0, nin, chunk_pixels):
        stop = min(nin, start+chunk_pixels)
        rr = np.arange(start, stop)
        nn = hp.ring2nest(nside_in, rr)
        if not np.array_equal(hp.nest2ring(nside_in, nn), rr):
            raise ValueError("RING_NESTED_PIXEL_IDENTITY_FAILURE")
        pp = nn//children
        for j, (field, window, mask) in enumerate(zip(ring_fields, windows, selected_nest)):
            valid = window[nn] & mask[pp]
            # Read sequential vector rows, not scattered memmap scalar elements.
            if field.ndim == 1:
                values = np.asarray(field[start:stop], float)
            else:
                width = field.shape[1]
                values = np.asarray(field[start//width:(stop+width-1)//width], float).reshape(-1)[:stop-start]
            if np.any(valid & (~np.isfinite(values) | (np.abs(values) >= 1e20))):
                raise ValueError("INVALID_SOURCE_INSIDE_FIXED_SELECTED_NATIVE_WINDOW")
            sums[j] += np.bincount(pp[valid], weights=values[valid], minlength=nout)
            counts[j] += np.bincount(pp[valid], minlength=nout)
    output = np.zeros_like(sums)
    minimum = np.ones(len(windows))
    for j, mask in enumerate(selected_nest):
        if np.any(counts[j, mask] == 0):
            raise ValueError("EMPTY_SELECTED_PARENT")
        output[j, mask] = sums[j, mask]/counts[j, mask]
        minimum[j] = float(np.min(counts[j, mask]/children))
    return np.stack([hp.reorder(row, n2r=True) for row in output]), minimum


def matched_support(root, hp):
    bridge_identity = identity(BRIDGE, BRIDGE_SHA)
    bridge = json.loads(BRIDGE.read_text())
    receipt, _ = producer.verify_receipt(root/"provenance/L01_NATIVE_PR3_POL_K64x90_v2.json")
    wp, _, psha = producer.read_windows(root, hp, receipt)
    wt = np.ones(len(wp), dtype=bool)
    sources = []
    for name, expected in T_MASK_SHA.items():
        path = root/f"planck/PR3/masks/COM_Mask_CMB-{name}-Mask-Int_2048_R3.00.fits"
        sources.append(identity(path, expected))
        with fits.open(path, memmap=True) as ff:
            hdu = ff[1]
            if hdu.header["NSIDE"] != 2048 or hdu.header["ORDERING"] != "NESTED":
                raise ValueError("TEMPERATURE_MASK_ORDERING")
            wt &= np.asarray(hdu.data["TMASK"]).reshape(-1) > .5
    cache_identity = identity(CACHE, CACHE_SHA)
    with np.load(CACHE, allow_pickle=False) as z:
        k1mask = z["common_mask"] > .5
        validate_pairs(z["cmb_ids"][:8], z["noise_ids"][:8])
    st = (hp.reorder(parent_coverage(wt), n2r=True) >= .995) & k1mask
    sp = hp.reorder(parent_coverage(wp), n2r=True) >= .995
    shas = [hashlib.sha256(m.astype(np.uint8).tobytes()).hexdigest() for m in (st, sp)]
    if (int(st.sum()) != 26846 or int(sp.sum()) != 30021 or
            shas[1] != bridge["selected_support"]["mask_sha256"] or
            psha != bridge["selected_support"]["native_window_sha256"]):
        raise ValueError("ORIGINAL_L01_SUPPORT_NOT_REPRODUCED")
    return wt, wp, st, sp, {"T_selected_pixels": int(st.sum()), "P_selected_pixels": int(sp.sum()),
        "T_ring64_mask_sha256": shas[0], "P_ring64_mask_sha256": shas[1],
        "T_native_window_sha256": hashlib.sha256(wt.astype(np.uint8).tobytes()).hexdigest(),
        "P_native_window_sha256": psha, "T_mask_sources": sources,
        "L01_bridge": bridge_identity, "K1_cache_reused_unchanged": cache_identity}


def component_diagnostics(coeff):
    # coeff[ID, signal/noise, T32+interleaved_EB64]; never invert sample covariance.
    total = coeff.sum(axis=1)
    centred = total-total.mean(axis=0)
    singular = np.linalg.svd(centred, compute_uv=False)
    blocks = {"T": np.arange(32), "E": [], "B": []}
    offset = 32
    for ell in range(2, 6):
        n = 2*ell+1
        blocks["E"].extend(range(offset, offset+n)); offset += n
        blocks["B"].extend(range(offset, offset+n)); offset += n
    summaries = {}
    for name, ix in blocks.items():
        x = coeff[:, :, ix]
        norms = np.linalg.norm(x, axis=-1)*1e6
        energy = np.sum(total[:, ix]**2, axis=1)
        lag = float(np.corrcoef(energy[:-1], energy[1:])[0, 1]) if np.std(energy) else None
        summaries[name] = {"signal_norm_microK": norms[:, 0].tolist(),
            "noise_plus_systematics_norm_microK": norms[:, 1].tolist(),
            "sum_norm_microK": (np.linalg.norm(total[:, ix], axis=1)*1e6).tolist(),
            "sum_energy_lag1_sample_correlation": lag,
            "mean_signal_noise_inner_product_microK2": float(np.mean(np.sum(x[:, 0]*x[:, 1], axis=1)))*1e12}
    return {"blocks": summaries, "joint_dimension": 96, "independent_pair_rows": 8,
        "centred_sample_rank": int(np.sum(singular > singular[0]*1e-12)),
        "centred_singular_values_K_CMB": singular.tolist(), "covariance_inverted": False,
        "autocorrelation_qualification": "EIGHT_ROWS_INSUFFICIENT_TO_ESTABLISH_INDEPENDENCE",
        "physical_coverage": "NOT_ESTABLISHED", "p_value": None}


def run(args):
    import healpy as hp
    t0 = time.perf_counter()
    paths = [args.out_dir/"PILOT.json", args.out_dir/"PILOT_COEFFICIENTS.npz", args.coarse_cache]
    if any(p.exists() for p in paths):
        raise FileExistsError("CREATE_ONLY_OUTPUT_EXISTS")
    if args.out_dir.resolve() != HERE/"results":
        raise ValueError("OUTPUT_OWNERSHIP")
    wt, wp, st, sp, support = matched_support(args.root, hp)
    print(json.dumps({"phase": "ORIGINAL_SUPPORT_VERIFIED", "T_pixels": int(st.sum()),
        "P_pixels": int(sp.sum()), "elapsed_s": time.perf_counter()-t0,
        "execution_attempt": 2, "same_cumulative_task": True}), flush=True)
    _, scalar = pixel_fit_geometry()
    theta, phi = hp.pix2ang(64, np.arange(49152))
    spin = block_design(theta, phi, 2, 5)
    ot, mt = linear_projector(scalar, st)
    op, mp = linear_projector(spin, np.r_[sp, sp])
    if abs(mp["design_condition"] - 3.1309622770574452) > 1e-10:
        raise ValueError("ORIGINAL_SPIN_CONDITION")
    # Native healpy synthesis, independent of the finite Wigner-d implementation.
    c = np.random.default_rng(20261018).standard_normal(64)
    aa = np.zeros((2, hp.Alm.getsize(5)), complex)
    offset = 0
    for ell in range(2, 6):
        for field in range(2):
            aa[field, hp.Alm.getidx(5, ell, 0)] = c[offset]; offset += 1
            for m in range(1, ell+1):
                aa[field, hp.Alm.getidx(5, ell, m)] = (c[offset]-1j*c[offset+1])/np.sqrt(2)
                offset += 2
    native = np.concatenate(hp.alm2map_spin(aa, 64, 2, lmax=5))
    injection_error = float(np.linalg.norm(op@native[np.r_[sp, sp]]-c)/np.linalg.norm(c))
    if injection_error > 2e-8:
        raise ValueError("NATIVE_LOW_INJECTION")
    expected = {Path(line.split()[1]).name: line.split()[0] for line in MANIFEST.read_text().splitlines()}
    coeff = np.empty((8, 2, 96))
    coarse = np.empty((8, 2, 3, 49152))
    sources = []
    for i in range(8):
        for j, component in enumerate(("cmb", "noise")):
            p = RAW/f"{component}_mc/dx12_v3_smica_{component}_mc_{i:05d}_raw.fits"
            before = (p.stat().st_size, p.stat().st_mtime_ns)
            record = identity(p, expected[p.name])
            print(json.dumps({"phase": "SOURCE_BYTES_VERIFIED", "id": i, "component": component,
                              "sha256": record["sha256"], "elapsed_s": time.perf_counter()-t0}), flush=True)
            with fits.open(p, memmap=True) as ff:
                h = ff[1]
                if (h.header["NSIDE"] != 2048 or h.header["ORDERING"] != "RING" or
                        h.header.get("COORDSYS", "G") != "G" or
                        h.columns.names != list(FIELDS) or
                        any(h.header[f"TUNIT{k}"] != "K_CMB" for k in (1, 2, 3))):
                    raise ValueError("FFP10_IQU_RELEASE_LAYOUT")
                maps, cov = ring_stream_selected_mean([h.data[name] for name in FIELDS],
                    (wt, wp, wp), (st, sp, sp), nside_in=2048, nside_out=64)
            if min(cov) < .995 or before != (p.stat().st_size, p.stat().st_mtime_ns):
                raise ValueError("SOURCE_CHANGED_OR_SELECTED_COVERAGE")
            coarse[i, j] = maps
            coeff[i, j, :32] = (ot@maps[0, st])[4:]
            coeff[i, j, 32:] = op@np.r_[maps[1, sp], maps[2, sp]]
            record.update(simulation_id=i, component=component, minimum_selected_coverage=cov.tolist(),
                          coordsys="NOT_IN_HEADER_GALACTIC_RELEASE_CONVENTION", ring_nested_roundtrip="ALL_SELECTED_CHILDREN_PASS")
            sources.append(record)
            print(json.dumps({"phase": "PAIR_COMPONENT_DONE", "id": i, "component": component,
                              "sha256": record["sha256"], "elapsed_s": time.perf_counter()-t0}), flush=True)
    # Map-level addition is checked after the source reduction, not merely array addition of coefficients.
    closure = []
    for i in range(8):
        maps = coarse[i].sum(axis=0)
        direct = np.r_[(ot@maps[0, st])[4:], op@np.r_[maps[1, sp], maps[2, sp]]]
        closure.append(float(np.linalg.norm(direct-coeff[i].sum(axis=0))/np.linalg.norm(direct)))
    if max(closure) > 2e-12:
        raise ValueError("PAIRED_MAP_LEVEL_LINEARITY")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    args.coarse_cache.parent.mkdir(parents=True, exist_ok=True)
    with args.coarse_cache.open("xb") as stream:
        np.savez_compressed(stream, paired_iqu_K_CMB=coarse, signal_ids=np.arange(8), noise_ids=np.arange(8),
                            mask_T_ring64=st, mask_P_ring64=sp)
    with paths[1].open("xb") as stream:
        np.savez_compressed(stream, component_coefficients_K_CMB=coeff, sum_coefficients_K_CMB=coeff.sum(axis=1),
                            signal_ids=np.arange(8), noise_ids=np.arange(8), mask_T_ring64=st, mask_P_ring64=sp)
    result = {"schema": "htt.L03_eight_pair_original_operator/1", "owner": "obsstat", "claim_tier": "C0",
        "execution_attempt": 2, "same_cumulative_task": True,
        "preserved_attempt1": identity(HERE/"ATTEMPT1_PERFORMANCE_OUTCOME.json"),
        "status": "DIAGNOSTIC_ONLY", "non_claim_bearing": True, "node_acceptance": "HOLD",
        "transfer_source": "none", "scope": "FFP10 fixed-weight SMICA full-mission source-conditional pilot",
        "same_original_child_average_operator": True, "support": support,
        "operator": {"T": mt, "P": mp, "native_spin_injection_relative": injection_error,
            "map_level_signal_plus_noise_linearity_relative": closure, "nside_native": 2048,
            "native_order": "RING", "gather_order": "NESTED", "out_order": "RING64",
            "implementation": "SEQUENTIAL_RING_CHUNKS_RING2NEST_MASKED_PARENT_BINCOUNT",
            "coverage_floor": .995, "T_fit_ells": [0, 5], "T_retained_ells": [2, 5],
            "EB_fit_ells": [2, 5], "EB_order": "per ell E(m0,cos,sin...),B(m0,cos,sin...)",
            "units": "K_CMB", "polarization_transport": "NONE_ORIGINAL_CHILD_AVERAGE_CONVENTION",
            "additional_beam_application": False, "deconvolution": False, "SHT": False},
        "diagnostics": component_diagnostics(coeff), "sources": sources,
        "raw_manifest": identity(MANIFEST), "coarse_cache": identity(args.coarse_cache),
        "coefficients": identity(paths[1]), "code": identity(__file__),
        "dependencies": [identity(producer.__file__), identity(sys.modules["spin2_finite"].__file__),
                         identity(sys.modules["original_selected_support"].__file__)],
        "runtime": {"python": sys.version, "executable": sys.executable, "numpy": np.__version__,
            "healpy": hp.__version__, "requested_model": "gpt-6.1-sol", "requested_effort": "high",
            "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN"},
        "missing_law": ["Joint same-realization HM1/HM2/OE1/OE2 signal+noise-plus-systematics outputs at fixed method weights",
            "Qualified foreground residual/weight-estimation law, including the actual selection family",
            "Experiment-specific exchangeability and heldout coverage beyond an eight-row pilot"],
        "caveats": ["I/Q/U of each component remain one realization; E/B/T and processing products are not independent skies.",
            "Numeric matched IDs define a fixed one-to-one signal/noise coupling, not proof of shared upstream seed.",
            "Local noise files are treated as delivered noise-plus-systematics, not independent white noise.",
            "Eight rows cannot estimate or invert 96-dimensional covariance or qualify physical coverage.",
            "No observed source was reread; original L01 child averaging does not parallel-transport polarization.",
            "Galactic frame follows the Planck release convention; COORDSYS is absent in local simulation headers.",
            "Official fixed-weight simulations are informative but do not establish full foreground/selection exchangeability."],
        "paper_gate": "NOT_READY_TO_SUBMIT", "elapsed_s": time.perf_counter()-t0,
        "peak_rss_kib_linux": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    with paths[0].open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False); stream.write("\n")
    print(json.dumps({"out": str(paths[0]), "elapsed_s": result["elapsed_s"], "diagnostics": result["diagnostics"]}), flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", type=Path, default=Path("/mnt/extdrive/workdir/htt_open_data"))
    ap.add_argument("--out-dir", type=Path, default=HERE/"results")
    ap.add_argument("--coarse-cache", type=Path, required=True)
    run(ap.parse_args())
