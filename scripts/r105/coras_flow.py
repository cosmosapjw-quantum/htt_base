"""Run real CORAS ensemble members on the R104 common CF4 selection."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

import numpy as np

DONOR_COMMIT = "45ab25635aa32869ce207511d556ea257ab8a591"
INPUTS = ("data/2MRS_group_member_catalog.dat", "data/CosmicEmu_spectrum_Planck18.dat")


def digest(path):
    with Path(path).open("rb") as fd:
        return hashlib.file_digest(fd, "sha256").hexdigest()


def samples():
    from scripts.r98 import cf4_p1 as old
    from scripts.r104 import cf4_2mrs_field as field
    H = old.r95._load_h03()
    source = H.source(old.r95.SELECT)
    ids, mu, emu, cz, v, _, _, _, n, _ = old.catalog()
    j = np.flatnonzero((cz / old.C >= .01) & (cz / old.C <= .10))
    j = j[np.argsort(ids[j])]
    if not np.array_equal(ids[j], source.ids) or np.max(abs(n[j] - source.n)) > 1e-10:
        raise ValueError("CF4 group identifiers or directions drifted")
    sci, *_ = old._load_r30_and_bridge()
    r, g, *_ = sci.background(cz[j]/old.C, 64)
    g0 = sci.H0 * (-1.5*sci.OM + 1/sci.growth_integral(np.array([1.]), 64)[0])
    if not np.isclose(sci.H0/100, field.H_LITTLE):
        raise ValueError("R104 distance convention changed")
    ng = field.to_galactic(n[j])
    radius = r * field.H_LITTLE
    vel, ok = field.interpolate(field.load_field(), ng*radius[:, None])
    jj = j[ok]
    _, y, _, A, cov, _ = old.tomography(H, n[jj], cz[jj], v[jj], mu[jj], emu[jj])
    weight = A * (g[ok]/g0 * (1 + v[jj]/old.C)/v[jj])
    return dict(ids=ids[jj], radius=radius[ok], ng=ng[ok], weights=weight, observed=A@y,
                measurement_cov=cov, nn=weight@np.einsum("ij,ij->i", vel[ok], ng[ok]))


def run(args, *, site_factory=samples, nodes=("H02", "SQ-CF4")):
    donor, binary, out = (p.resolve() for p in (args.donor, args.binary, args.output))
    sha = subprocess.check_output(["git","-C",str(donor),"rev-parse","HEAD"], text=True).strip()
    if sha != DONOR_COMMIT:
        raise ValueError(f"unexpected CORAS commit {sha}")
    subprocess.run(["git","-C",str(donor),"diff","--quiet","HEAD","--","src","configuration.hpp",*INPUTS], check=True)
    if args.first < 1 or args.last < args.first or args.threads < 1:
        raise ValueError("invalid seed interval or thread count")
    data = site_factory()
    out.mkdir(parents=True, exist_ok=False)
    sites = out / "sites.tsv"
    ng = data["ng"]
    direction = np.mod(np.arctan2(ng[:,1], ng[:,0]), 2*np.pi)
    direction[direction >= 2*np.pi] = 0.
    np.savetxt(sites, np.column_stack([data["ids"],data["radius"],np.arccos(np.clip(ng[:,2],-1,1)),direction]),
               fmt=["%d","%.17g","%.17g","%.17g"], delimiter="\t")
    argv = [str(binary),str(sites),str(out),str(args.first),str(args.last),str(args.radial),
            str(args.ell),str(args.fft),str(args.smoothing)]
    config = dict(radial=args.radial, ell=args.ell, fft=args.fft, smoothing_Mpch=args.smoothing,
                  growth_fsigma8=0.405, external_bulk_galactic_kms=[95,-172,28])
    start = time.monotonic()
    with (out/"generate.log").open("x") as log:
        subprocess.run(argv, cwd=donor, env={**os.environ,"OMP_NUM_THREADS":str(args.threads)},
                       stdout=log, stderr=subprocess.STDOUT, check=True)
    all_outputs = [out/"mean.tsv", *(out/f"residual_{i}.tsv" for i in range(args.first,args.last+1))]
    receipt = dict(first=args.first, last=args.last, config=config, nodes=list(nodes), groups=len(ng),
                   cpu_threads=args.threads, seconds=time.monotonic()-start, argv=argv, cwd=str(donor),
                   donor_commit=sha, source_sha256=digest(Path(__file__).with_name("coras_radial.cpp")),
                   binary_sha256=digest(binary), input_sha256={name:digest(donor/name) for name in INPUTS},
                   sites_sha256=digest(sites), output_sha256={p.name:digest(p) for p in all_outputs})
    if "catalogue" in data:
        receipt["catalogue"] = data["catalogue"]
    pending = out/"run.json.tmp"
    pending.write_text(json.dumps(receipt,indent=2)+"\n")
    pending.replace(out/"run.json")
    print(f"{len(ng)} groups, {len(all_outputs)-1} draws, {receipt['seconds']:.1f}s, {out}", flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("donor","binary","output"):
        p.add_argument("--"+name, required=True, type=Path)
    for name, default in (("first",1),("last",8),("radial",24),("ell",4),("fft",16),("threads",1)):
        p.add_argument("--"+name, type=int, default=default)
    p.add_argument("--smoothing", type=float, default=15.)
    run(p.parse_args())
