"""Run original REI → REC opacity and BASS deterministic sky over finite registered material.

From htt_base: python -m scripts.r109.native_material_sky --help
The late and early windows have separate donors, finite observers and normal clocks.
No extrapolation or cross-band addition is performed.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import shutil
from pathlib import Path
import subprocess
import tempfile

import numpy as np

from .material_bridge import (CASES, C_SIGMA_T, MATERIAL_HEADER, REC_PATH, REC_REV, REC_SHA, REI_PATH, REI_REV,
                              REI_SHA, conservative_material, git_blob, material_stream, r105_quadrupoles, rec_material,
                              rei_clock, validate_cells)

ROOT = Path(__file__).resolve().parents[2]
SCIENCE = ROOT / "docs/research_program/observational_publication_20261015"
R105 = SCIENCE / "R105_RESEARCH_20261124/REC_OBSERVER_REDSHIFT.json"
R106 = SCIENCE / "R106_RESEARCH_20261124/REI/REI_RESTART_REPLAY.json"
REFERENCE_HASHES = {
    R105:"0295eaf8c75aff9a85d410bb7d945975fde077a1df723f98c18a94ad5c757144",
    R106:"b0029c27c9f6851c56089bda653ae3e8d44552688b82283f9b4962aef2cc1963",
}
OUT = SCIENCE / "R109_NATIVE_RUST_BIANCHI_20261124/NATIVE_MATERIAL_SKY.json"
REDSHIFTS = np.array([.1, .3, .6, 1., 2., 3.])
BINS = {
    "rei": ("rust/rei_microphysics", "--example", "thomson_history"),
    "rec": ("rust/rec_microphysics", "--bin", "rec_ray_thomson"),
    "bass": ("_rustcore", "--example", "homogeneous_sky"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(repo, name, build_root):
    crate, flag, binary = BINS[name]
    revision = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    path = repo / crate
    # Include tracked/untracked crate files; Cargo ignores target directories.
    dirty = subprocess.check_output(["git","-C",str(repo),"status","--porcelain","--",crate], text=True)
    if dirty.strip():
        raise ValueError(f"commit the native {name} crate before provenance-bound execution: {dirty}")
    target = build_root if build_root else path / "target"
    cmd = ["cargo", "build", "--quiet", "--release", "--manifest-path", str(path / "Cargo.toml"),
           "--target-dir", str(target), flag, binary]
    if (path / "Cargo.lock").is_file():
        cmd.insert(2, "--locked")
    subprocess.run(cmd, check=True)
    executable = target / "release" / ("examples" if flag == "--example" else "") / binary
    return executable, {"commit": revision, "repo": str(repo), "crate": crate,
                        "source_tree": subprocess.check_output(["git","-C",str(repo),"rev-parse",
                                                               f"HEAD:{crate}"], text=True).strip(),
                        "executable_sha256": sha(executable.read_bytes()), "command":cmd}


def run(argv):
    return subprocess.run(list(map(str, argv)), capture_output=True, check=True, text=True)


def read_table(raw):
    return np.atleast_1d(np.genfromtxt(io.StringIO(raw), names=True, delimiter=None, encoding="utf-8"))


def rei_material(exe, source, case):
    out = run([exe, source, case, "rest", 0, 0, 0, 0, 0, 1])
    if out.stdout.splitlines()[0].split() != MATERIAL_HEADER:
        raise ValueError("unrecognized original REI output columns")
    table = read_table(out.stdout)
    rows = np.column_stack([table[k] for k in MATERIAL_HEADER])
    if len(rows) != 1001:
        raise ValueError("original five-case history must return 1001 knots per case")
    return rows, json.loads(out.stderr), out.stdout


def save_tsv(path, header, rows):
    np.savetxt(path,rows,header="\t".join(header),delimiter="\t",comments="",fmt="%.17g")


def read_modes(directory, L):
    table = read_table((directory / "modes.tsv").read_text())
    degree = table["ell"].astype(int)
    m = table["m"].astype(int)
    want = [(l,k) for l in range(L+1) for k in range(-l,l+1)]
    if (not np.array_equal(table["ell"],degree) or not np.array_equal(table["m"],m)
            or len(degree) != len(want) or sorted(zip(degree,m)) != want):
        raise ValueError("deterministic multipole table must cover each signed coefficient")
    alm = {x:table[x+"_re"] + 1j*table[x+"_im"] for x in "TEB"}
    if not all(np.isfinite(v).all() for v in alm.values()):
        raise ValueError("nonfinite deterministic sky")
    indices = {(l,k):i for i,(l,k) in enumerate(zip(degree,m))}
    for i,(l,k) in enumerate(zip(degree,m)):
        sign = -1 if k % 2 else 1
        if any(not np.isclose(a[indices[l,-k]],sign*a[i].conjugate(),rtol=2e-12,atol=1e-18)
               for a in alm.values()):
            raise ValueError("harmonics violate real-sky conjugacy")
    spectra = {}
    for xy in ("TT","TE","TB","EE","EB","BB"):
        prod = alm[xy[0]] * alm[xy[1]].conj()
        if not np.allclose(prod,table[xy+"_re"]+1j*table[xy+"_im"],rtol=2e-12,atol=1e-24):
            raise ValueError(f"incorrect signed {xy} products")
        spectra[xy] = [float(np.sum(prod[degree==l].real)/(2*l+1))
                       for l in range(L+1)]
    cl = read_table((directory / "cl.tsv").read_text())
    if not np.array_equal(cl["ell"],np.arange(L+1)):
        raise ValueError("invalid ell index in cl.tsv")
    for xy, array in spectra.items():
        if not np.allclose(array,cl[xy],rtol=2e-11,atol=1e-24):
            raise ValueError(f"BASS m multiplicities or {xy} normalization mismatch")
    return np.column_stack([alm[x] for x in "TEB"]), spectra


def native_sky(exe, material_path, duration, steps, out, args):
    command = [exe,"--family",args.family,"--shear",args.shear,"--duration",f"{duration:.17g}","--steps",steps,
               "--nmu",args.nmu,"--nphi",args.nphi,"--lmax",args.lmax,"--observer-beta","0,0,0",
               "--feedback","tracer","--material",material_path,"--out",out]
    run(command)
    alm,cl = read_modes(out,args.lmax)
    products = {n:sha((out/n).read_bytes()) for n in ("modes.tsv","cl.tsv","diagnostics.tsv")}
    diagnostics = read_table((out/"diagnostics.tsv").read_text())
    rates = read_table(material_path.read_text())
    depth_expected = np.sum(np.diff(rates["eta"])*.5*(rates["rate_per_eta"][:-1]+rates["rate_per_eta"][1:]))
    consumed = float(diagnostics["proper_depth"][-1])
    if abs(consumed-depth_expected)>3e-12 * max(float(depth_expected),1.):
        raise ValueError("native BASS did not integrate the prescribed REC exposure")
    argv = [str(x) for x in command]
    argv[argv.index("--material")+1] = "rate.tsv"
    argv[argv.index("--out")+1] = out.name
    return alm, {"steps":steps,"argv_in_case_workdir":argv[1:],"files_sha256":products,
                 "consumed_depth":consumed,"consumed_minus_rec_depth":float(consumed-depth_expected),
                 "feedback":"polarized_tracer_on_native_scalar_radiation",
                 "max_abs_gauss":float(np.max(abs(diagnostics["gauss"]))),
                 "signed_alm":read_table((out/"modes.tsv").read_text())[list(("ell","m","T_re","T_im","E_re","E_im","B_re","B_im"))].tolist(),
                 "signed_alm_columns":["ell","m","T_re","T_im","E_re","E_im","B_re","B_im"], "cl_dimensionless":cl}


def partial_compare(case, rows, tau, references):
    r105,r106 = references
    mono, quad = r105_quadrupoles(rows[:,9],rows[:,10],tau,REDSHIFTS)
    old2 = np.array(r105["cases"][case]["tau_legendre2"])
    old0 = np.array(r105["cases"][case]["tau_monopole"])
    q106 = r106["cases"][case]["clock_H_consistency_and_quadrature"]["conditional_thomson_depth_mean_z_20_to_4"]
    d = float(tau[0] - q106["value_richardson_dN_form"])
    if abs(d)>1e-7 or np.max(abs(old2-quad))>2e-7 or np.max(abs(old0-mono))>1e-6:
        raise ValueError(f"{case} finite-observer replay exceeds fixed accuracy")
    return {"r106_native_312238_rows_tau":q106["value_richardson_dN_form"],"minus_r106_native":d,
            "ray_redshift":REDSHIFTS.tolist(),"tau0":mono.tolist(),"tau2":quad.tolist(),
            "tau2_minus_r105":(quad-old2).tolist(),"max_tau0_minus_r105":float(np.max(abs(mono-old0)))}


def run_bridge(args):
    repos = dict(rei=args.rei_repo,rec=args.rec_repo,bass=args.bass_repo)
    pins = json.loads(args.pins.read_text()) if args.pins else {}
    for name,expected in pins.items():
        if name not in repos: raise ValueError(f"unknown pinned repository {name}")
        got=subprocess.check_output(["git","-C",str(repos[name]),"rev-parse","HEAD"],text=True).strip()
        if got != expected: raise ValueError(f"{name} HEAD {got} differs from requested {expected}")
    targets = {name:args.build_root/name if args.build_root else None for name in BINS}
    if args.bass_target:
        targets["bass"] = args.bass_target
    natives = {name:build(repos[name],name,targets[name]) for name in BINS}
    rei_bytes = git_blob(args.rei_source,REI_REV,REI_PATH,REI_SHA)
    rec_bytes = git_blob(args.rec_source,REC_REV,REC_PATH,REC_SHA)
    references = []
    for path, expected in REFERENCE_HASHES.items():
        data=path.read_bytes()
        if sha(data)!=expected:
            raise ValueError(f"historical comparator checksum differs: {path}")
        references.append(json.loads(data))
    results = {}
    if args.products_dir and args.products_dir.exists():
        raise FileExistsError(f"choose a fresh --products-dir: {args.products_dir}")
    with tempfile.TemporaryDirectory(prefix="r109-material-",dir=args.work_parent) as tmp:
        tmp = Path(tmp)
        abundance = tmp / "five.csv"
        abundance.write_bytes(gzip.decompress(rei_bytes))
        for case in ["REC_1200_1000", *CASES]:
            work = tmp/case
            work.mkdir()
            moments_path = work/"rest.tsv"
            if case == "REC_1200_1000":
                rows,H = rec_material(rec_bytes)
                native_rei = None
                save_tsv(moments_path,MATERIAL_HEADER,rows)
            else:
                rows,native_rei,raw = rei_material(natives["rei"][0],abundance,case)
                moments_path.write_text(raw)
                H = rei_clock(rows[:,9],CASES[case])
            material = material_stream(rows,H)
            material_path = work / "rate.tsv"
            cells_text = run([natives["rec"][0],moments_path]).stdout
            cell_table = read_table(cells_text)
            tau,cert = validate_cells(rows,cell_table)
            dtau = cell_table["delta_tau"][np.argsort(cell_table["far_t_s"])]
            constrained,conservation = conservative_material(material,dtau)
            save_tsv(material_path,["eta","rate_per_eta","beta_x","beta_y","beta_z"],constrained)
            stream_tau = float(np.sum(np.diff(material[:,0]) * .5*(material[1:,1]+material[:-1,1])))
            if abs(stream_tau-tau[0]) > 4e-4 * max(tau[0],1e-12):
                raise ValueError(f"{case} rest-rate and proper-time material clocks disagree")
            info = {"knots":len(rows),"finite_mean_redshift":[float(np.expm1(-rows[i,9])) for i in [0,-1]],
                    "duration_ln_a":float(material[-1,0]),"bare_depth_ln_a_trapezoid":stream_tau,
                    "ln_a_minus_proper_time_tau":float(stream_tau-tau[0]),"independent_cells":cert,"rec_to_bass_conservation":conservation,
                    "original_rei_diagnostics":native_rei,"material_table_sha256":sha(material_path.read_bytes()),
                    "rec_cells_sha256":sha(cells_text.encode())}
            if args.products_dir:
                (work/"rec_cells.tsv").write_text(cells_text)
            if native_rei is not None:
                info["rec_log_density_minus_rei_linear_rate_tau"] = float(tau[0]-native_rei["tau_to_terminal"])
                info["historical_comparison"] = partial_compare(case,rows,tau,references)
            # The prescribed I background for the transfer study is independent of the donor's dynamics.
            # Signed REI partners have nearly equal bare depths on fixed material endpoints.
            if case in args.sky_cases:
                previous = None
                runs=[]
                for steps in args.steps:
                    alm,entry = native_sky(natives["bass"][0],material_path,material[-1,0],steps,
                                           work/f"sky{steps}",args)
                    if previous is not None:
                        entry["max_delta_alm_vs_preceding_resolution"] = dict(zip("TEB",np.max(abs(alm-previous),axis=0).tolist()))
                    previous=alm
                    runs.append(entry)
                info["transfer_runs"] = runs
            results[case] = info
        if args.products_dir:
            args.products_dir.parent.mkdir(parents=True,exist_ok=True)
            # Publish the finished products atomically on the destination filesystem.
            with tempfile.TemporaryDirectory(prefix=".r109-publish-",dir=args.products_dir.parent) as staging:
                dest=Path(staging)/"products"
                dest.mkdir()
                for case in results:
                    shutil.copytree(tmp/case,dest/case)
                os.rename(dest,args.products_dir)
    return {"schema":"htt.r109.original_material_sky/1",
            "toolchain":{"rustc":subprocess.check_output(["rustc","-Vv"],text=True).strip(),
                         "cargo":subprocess.check_output(["cargo","--version"],text=True).strip()},
            "binaries":{k:v[1] for k,v in natives.items()},
            "source_material":{"REC":[REC_REV,REC_PATH,REC_SHA],"REI":[REI_REV,REI_PATH,REI_SHA]},
            "bridge_source_sha256":{p.name:sha(p.read_bytes()) for p in
                                    [Path(__file__),Path(__file__).with_name("material_bridge.py")]},
            "c_sigmaT_m3_s":C_SIGMA_T,
            "historical_receipt_hashes":{p.name:sha(p.read_bytes()) for p in [R105,R106]},
            "transfer_configuration":{"family":args.family,"shear":args.shear,"nmu":args.nmu,"nphi":args.nphi,
                                      "lmax":args.lmax,"observer_beta":[0,0,0],"electron_beta":[0,0,0]},
            "interpretation":"The original charge and clock prescribe finite material opacity to the chosen BASS dynamics. "
                "R105 uses the donor LRS-I metric for fixed-ray-redshift multipoles; REC material uses original q=0 HyRec. "
                "The two redshift windows are independent. Alm and cross-powers are deterministic sky outputs.",
            "physical_Pi":None,"family_attribution":None,"cases":results}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ["rei","rec","bass"]:
        p.add_argument(f"--{k}-repo",type=Path,required=True,help="original Rust checkout with the R109 commit")
    for k in ["rei","rec"]:
        p.add_argument(f"--{k}-source",type=Path,help="optional separate repository containing the historical donor object")
    p.add_argument("--pins",type=Path,help="JSON mapping of original repository names to expected HEADs")
    p.add_argument("--build-root",type=Path,help="optional alternative Cargo target root, organized by repository")
    p.add_argument("--bass-target",type=Path,help="reuse a specific original Rust BASS Cargo build target")
    p.add_argument("--work-parent",type=Path)
    p.add_argument("--products-dir",type=Path,help="new directory for native material TSVs, modes, spectra and diagnostics")
    p.add_argument("--sky-cases",nargs="+",choices=["REC_1200_1000",*CASES],default=["REC_1200_1000","ZERO","SHEAR_PLUS"])
    p.add_argument("--steps",type=int,nargs="+",default=[16,32])
    p.add_argument("--family",default="I")
    p.add_argument("--shear",type=float,default=.008)
    p.add_argument("--lmax",type=int,default=4)
    p.add_argument("--nmu",type=int,default=10)
    p.add_argument("--nphi",type=int,default=24)
    p.add_argument("--output",type=Path,default=OUT)
    args=p.parse_args()
    if min(args.steps)<1 or sorted(set(args.steps))!=args.steps:
        p.error("--steps must be strictly increasing positive integers")
    args.rei_source=args.rei_source or args.rei_repo
    args.rec_source=args.rec_source or args.rec_repo
    report=run_bridge(args)
    args.output.parent.mkdir(exist_ok=True,parents=True)
    with tempfile.NamedTemporaryFile(mode="w",dir=args.output.parent,delete=False) as f:
        json.dump(report,f,indent=2,allow_nan=False)
        f.write("\n")
    os.replace(f.name,args.output)


if __name__=="__main__":
    main()
