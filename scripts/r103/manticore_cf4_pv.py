"""Manticore-Local z=0 ensemble on the published R98 CF4 working 36-D windows."""
from __future__ import annotations

import argparse
from contextlib import closing, contextmanager
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import tempfile

import numpy as np

SOURCE_SHA = {
    "selected": "86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c",
    "table3": "c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d",
    "table4": "b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94",
}
KEY = re.compile(r"R1024/mcmc_([0-9]+)/velocity_fields/N256/field\.h5")
PRODUCT_CAP = 512 * 1024**2


def digest(path):
    with Path(path).open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def field_catalog():
    from manticore_data import ManticoreDataLoader, ManticoreGeneration
    files = ManticoreDataLoader(ManticoreGeneration.Local).get_velocity_field(1024, mesh_resolution=256)
    result = {}
    for obj in files:
        key = obj.key.removeprefix("manticore-local/")
        match = KEY.fullmatch(key)
        if obj.bucket_name != "manticore-local" or not match:
            raise ValueError("unexpected Manticore Local velocity-field product")
        idx = int(match.group(1))
        if idx in result:
            raise ValueError("duplicate draw identity")
        result[idx] = (obj, key)
    return result


def canonical(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)


@contextmanager
def staged(path):
    """Place complete bytes beside the destination; never replace user data."""
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".manticore-", delete=False) as out:
        tmp = Path(out.name)
        try:
            yield out
            out.flush()
            os.fsync(out.fileno())
            try:
                os.link(tmp, path)
            except FileExistsError:
                if path.is_symlink() or not path.is_file() or digest(tmp) != digest(path):
                    raise FileExistsError(f"conflicting object preserved: {path}") from None
            fd = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
        finally:
            tmp.unlink(missing_ok=True)


def draw_receipt(path, *, allow_missing_data=False):
    match = re.fullmatch(r"manticore_local_(\d{3})\.h5", path.name)
    if not match:
        raise ValueError("unrecognized realization filename")
    idx = int(match.group(1))
    side = path.with_suffix(".source.json")
    if side.is_symlink() or not side.is_file():
        raise ValueError(f"missing release receipt: {side}")
    rec = json.loads(side.read_text())
    key = KEY.fullmatch(str(rec.get("key")))
    if (rec.get("schema") != "htt.manticore_local.source/1" or rec.get("bucket") != "manticore-local"
            or type(rec.get("index")) is not int or rec["index"] != idx or key is None or int(key.group(1)) != idx
            or type(rec.get("bytes")) is not int or not 0 < rec["bytes"] <= PRODUCT_CAP
            or not isinstance(rec.get("etag"), str) or not rec["etag"]
            or re.fullmatch(r"[0-9a-f]{64}",str(rec.get("sha256"))) is None):
        raise ValueError(f"invalid release receipt: {side}")
    if (path.exists() or not allow_missing_data or path.is_symlink()) and (
            path.is_symlink() or not path.is_file() or path.stat().st_size != rec["bytes"]
            or digest(path) != rec["sha256"]):
        raise ValueError(f"raw bytes disagree with receipt: {path}")
    return rec


def fetch_fields(directory, indices, cap):
    """Bind each immutable draw to S3 key, ETag, size and streamed SHA before exposing data."""
    catalog = field_catalog()
    directory.mkdir(parents=True, exist_ok=True)
    jobs = []
    for idx in indices:
        obj, key = catalog[idx]
        params = dict(Bucket=obj.bucket_name, Key=key)
        head = obj.s3.head_object(**params)
        size, etag = int(head["ContentLength"]), head["ETag"]
        if not 0 < size <= PRODUCT_CAP or not etag:
            raise ValueError(f"invalid provider metadata for {key}")
        target = directory/f"manticore_local_{idx:03d}.h5"
        source = dict(schema="htt.manticore_local.source/1", index=idx, bucket=obj.bucket_name,
                      key=key, bytes=size, etag=etag)
        side = target.with_suffix(".source.json")
        if side.exists() or side.is_symlink():
            old = draw_receipt(target, allow_missing_data=True)
            if any(old.get(k) != v for k,v in source.items()):
                raise ValueError(f"live provider identity differs from {side}")
            if target.is_file():
                print(canonical(dict(**old, transferred_bytes=0)), flush=True)
                continue
        jobs.append((target,obj,params,source))
    if sum(source["bytes"] for _,_,_,source in jobs) > cap:
        raise ValueError("requested missing objects exceed the explicit total byte allowance")
    for target,obj,params,source in jobs:
        response = obj.s3.get_object(**params, IfMatch=source["etag"])
        with closing(response["Body"]) as stream, staged(target) as out:
            if response["ContentLength"] != source["bytes"] or response["ETag"] != source["etag"]:
                raise ValueError("provider HEAD/GET identity mismatch")
            got = 0
            sha = hashlib.sha256()
            while got < source["bytes"]:
                block = stream.read(min(1024**2, source["bytes"]-got))
                if not block or len(block) > source["bytes"]-got:
                    raise ValueError("invalid body length")
                got += len(block)
                sha.update(block)
                out.write(block)
            out.flush()
            import h5py
            with h5py.File(out.name) as field:
                check_mesh(field, 256)
            receipt = dict(**source, sha256=sha.hexdigest())
            # Recover a legacy unreceipted file by checking against the exact GET.
            if target.is_symlink() or (target.exists() and
                    (not target.is_file() or digest(target) != receipt["sha256"])):
                raise FileExistsError(f"conflicting object preserved: {target}")
            # If killed between links, the next run can re-fetch the same ETag
            # and SHA using the sidecar; a reduction requires both files.
            with staged(target.with_suffix(".source.json")) as side:
                side.write((canonical(receipt)+"\n").encode())
        print(canonical(dict(**receipt, transferred_bytes=got)), flush=True)


def check_mesh(field, mesh_size):
    for name in ("density","p0","p1","p2"):
        if field[name].shape != (mesh_size,)*3 or field[name].dtype.kind != "f":
            raise ValueError(f"invalid {name} grid")


def mesh_stencil(nhat, distance, mesh_size=256, box_mpc=1000., offset=0.):
    """Tutorial: equatorial xyz at index N/2+r*n/dx, distance in physical Mpc at z=0."""
    n = np.asarray(nhat, dtype=float)
    r = np.asarray(distance, dtype=float)
    if (n.shape != (r.size,3) or r.ndim != 1 or not np.isfinite(r).all() or
            np.any(r < 0) or not np.isfinite(n).all() or not np.allclose((n*n).sum(1),1,rtol=0,atol=1e-10)):
        raise ValueError("finite unit equatorial directions and nonnegative Mpc radii required")
    xyz = mesh_size/2. + offset + n*(r*mesh_size/box_mpc)[:,None]
    if not np.isfinite(xyz).all() or np.any(xyz < 0.) or np.any(xyz > mesh_size-1):
        raise ValueError("out-of-mesh coordinate; do not wrap or pad catalogue objects")
    base = np.minimum(xyz.astype(int), mesh_size-2)
    frac = xyz-base
    bits = np.array(list(itertools.product(range(2),repeat=3)))
    coords = base[:,None,:]+bits
    weights = np.prod(np.where(bits,frac[:,None,:],1.-frac[:,None,:]),axis=2)
    flat = np.ravel_multi_index(coords.reshape(-1,3).T,(mesh_size,)*3)
    uniq, inv = np.unique(flat,return_inverse=True)
    return np.array(np.unravel_index(uniq,(mesh_size,)*3)), inv.reshape(len(n),8), weights


def project_field(field, n, stencil, mesh_size=256, observer_relative=False):
    """Trilinearly interpolate vertex velocities p/rho, then contract with each outward ray."""
    check_mesh(field, mesh_size)
    coords, inv, weights = stencil
    x,y,z = coords
    samples = np.empty((len(x),4))
    # Each x plane is read once per channel. The working set scales with visited
    # cells and one plane, independent of a full 3-vector cube allocation.
    ix, starts, counts = np.unique(x,return_index=True,return_counts=True)
    for plane,start,count in zip(ix,starts,counts):
        rows = slice(start,start+count)
        for j,name in enumerate(("density","p0","p1","p2")):
            samples[rows,j] = field[name][int(plane),:,:][y[rows],z[rows]]
    active = np.unique(inv[weights>0])
    if not np.isfinite(samples[active]).all() or (samples[active,0]<=0).any():
        raise ValueError("undefined grid velocity on active stencil")
    velocity = np.zeros((len(x),3))
    velocity[active] = samples[active,1:]/samples[active,:1]
    values = np.einsum("ij,ijk->ik", weights, velocity[inv])
    if observer_relative:
        # The observer is supplied as the final stencil row, with r=0. Its ray
        # is an unused placeholder. The subtraction is performed on 3-vectors.
        values -= values[-1].copy()
    return np.einsum("ij,ij->i", values,n)


def velocity_growth_ratio(g, g0):
    """Linear growth transport of a z=0 peculiar velocity: v(z)=v(0) g(z)/g(0), g=aHfD."""
    g = np.asarray(g, dtype=float)
    if not np.isfinite(g0) or g0 <= 0 or not np.isfinite(g).all() or np.any(g <= 0):
        raise ValueError("positive finite velocity growth rates required")
    return g / float(g0)


def geometry():
    from scripts.r98 import cf4_p1 as old
    from scripts.r97 import cf4_genealogy_and_partial_id as r97
    paths = {"selected":old.r95.SELECT,"table3":r97.RAW_CF4/"table3.dat","table4":r97.RAW_CF4/"table4.dat"}
    if {name:digest(path) for name,path in paths.items()} != SOURCE_SHA:
        raise ValueError("R98 source identities changed")
    H = old.r95._load_h03()
    inp = H.source(old.r95.SELECT)
    ids,mu,emu,cz,v,_,_,_,n,_ = old.catalog()
    j = np.flatnonzero((cz/old.C >= .01) & (cz/old.C <= .10))
    j = j[np.argsort(ids[j])]
    if not (np.array_equal(ids[j],inp.ids) and np.max(abs(n[j]-inp.n)) <= 1.e-10):
        raise ValueError("selected row/sky alignment drift")
    sci,*_ = old._load_r30_and_bridge()
    r,g,*_ = sci.background(cz[j]/old.C,64)
    g0 = float(sci.background(np.array([0.]),64)[1][0])
    _,_,_,a,_,_ = old.tomography(H,n[j],cz[j],v[j],mu[j],emu[j])
    # Manticore supplies v(z=0) in km/s. g=aHfD carries km/s/Mpc, so the
    # linear transport of an existing velocity is g(z)/g(0) (R104 correction;
    # R103 multiplied by g itself, a factor g(0)=35.52 too large).
    # q_WF converts km/s to a log-distance response.
    weight = a * (velocity_growth_ratio(g, g0) * (1.+v[j]/old.C)/v[j])
    return ids[j], n[j], r, weight


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("geometry")
    get = sub.add_parser("fetch")
    get.add_argument("--indices", nargs="+", type=int, required=True)
    get.add_argument("--max-bytes", type=int, required=True)
    get.add_argument("--directory", type=Path, required=True)
    red = sub.add_parser("reduce")
    red.add_argument("--files", nargs="+", type=Path, required=True)
    red.add_argument("--frame", choices=["simulation","relative-to-grid-observer"], required=True)
    red.add_argument("--origin-offset", choices=[0.,-.5], type=float, default=0.)
    red.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.action=="fetch":
        if len(set(args.indices)) != len(args.indices) or min(args.indices)<0 or args.max_bytes<0:
            raise ValueError("unique nonnegative draw IDs and a nonnegative allowance required")
        fetch_fields(args.directory,args.indices,args.max_bytes)
        return
    ids, n, r, weight = geometry()
    offset = getattr(args,"origin_offset",0.)
    rays = np.vstack((n, [1.,0.,0.]))
    stencil = mesh_stencil(rays,np.append(r,0.),offset=offset)
    if args.action=="geometry":
        print(json.dumps(dict(n_selected=len(ids), r_mpc=[r.min(),r.max()], windows=list(weight.shape),
                              n_stencil_cells=stencil[0].shape[1],source_sha256=SOURCE_SHA)))
        return
    import h5py
    if len(args.files)>80 or len(args.files)<2:
        raise ValueError("sample covariance requires 2..80 unique draws")
    draw_ids, shas, vectors, receipts = [], [], [], []
    for path in sorted(args.files, key=lambda p: p.name):
        receipt = draw_receipt(path)
        receipts.append(receipt)
        idx, sha = receipt["index"], receipt["sha256"]
        if idx in draw_ids or sha in shas:
            raise ValueError("duplicate realization")
        with h5py.File(path) as field:
            v = project_field(field,rays,stencil,observer_relative=(args.frame=="relative-to-grid-observer"))
        vectors.append(weight @ v[:-1])
        draw_ids.append(idx)
        shas.append(sha)
    arr = np.stack(vectors)
    centered = arr-arr.mean(0)
    metadata = dict(schema="htt.manticore_local.cf4_ensemble/1", draw_sources=receipts,
                    frame=args.frame, mesh_index_offset=offset, mesh_size=256, box_mpc=1000.,
                    source_sha256=SOURCE_SHA, kernel_sha256=digest(Path(__file__)),
                    n_selected=len(ids), projection="R98 A * R100 g(z) q_WF * vlos(z=0)",
                    covariance="centered, ddof=1, conditioned on Manticore-Local observations")
    for name, values, dtype in (("group_id",ids,"<i8"), ("nhat",n,"<f8"), ("r_mpc",r,"<f8"),
                                ("weights",weight,"<f8")):
        metadata[name+"_sha256"] = hashlib.sha256(np.ascontiguousarray(values, dtype=dtype)).hexdigest()
    with staged(args.output) as f:
        np.savez_compressed(f, draw_ids=draw_ids, sha256=shas, b=arr, posterior_mean=arr.mean(0),
                            posterior_cov=(centered.T @ centered)/(len(arr)-1),
                            metadata_json=canonical(metadata), frame=args.frame, grid_index_offset=offset,
                            source_sha256_json=json.dumps(SOURCE_SHA,sort_keys=True),
                            scope="conditional z0 DMO reconstructed PV, R100 linear WF growth; no additive S_PV qualification")


if __name__ == "__main__":
    main()
