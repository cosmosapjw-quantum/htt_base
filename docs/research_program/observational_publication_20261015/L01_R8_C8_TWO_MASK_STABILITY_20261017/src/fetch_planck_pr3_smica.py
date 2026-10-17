"""Allowlisted Planck PR3 SMICA IQU downloads (full/HM/OE).

The URLs were read from NASA/IPAC IRSA's actual CMB map matrix and previews.
Local SHA256 is NOT a publisher-certified checksum. FITS files remain outside Git.
For interrupted transfers, resume only after HTTP 206 and checked Content-Range.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.request import Request, urlopen

INDEX = "https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/matrix_cmb.html"
PREFIX = "https://irsa.ipac.caltech.edu/data/Planck/release_3/all-sky-maps/maps/component-maps/cmb/"
NAME = "COM_CMB_IQU-smica_2048_R3.00_"
PRODUCTS = ("full", "hm1", "hm2", "oe1", "oe2")
PIXELS = 12 * 2048**2
MIN_BYTES = {"full": 40*PIXELS, **{k:12*PIXELS for k in PRODUCTS[1:]}}


def filename(product):
    if product not in PRODUCTS:
        raise ValueError("PRODUCT_NOT_IRSA_ALLOWLISTED")
    return NAME + product + ".fits"


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def verify_local_file(path, product):
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("NOT_REGULAR_FITS")
    size = p.stat().st_size
    if size < MIN_BYTES[product] or size % 2880:
        raise ValueError("FITS_SIZE_OR_PADDING")
    with p.open("rb") as f:
        if not f.read(80).startswith(b"SIMPLE  ="):
            raise ValueError("FITS_HEADER_SIGNATURE")
    return {"size_bytes": size, "sha256_local": digest(p),
            "provenance": "DOWNLOADED_LOCAL_BYTES_NOT_PUBLISHER_SIGNED"}


def transfer(product, root, *, timeout=120, chunk_mib=8, opener=None):
    if timeout<=0 or not (1<=chunk_mib<=128):
        raise ValueError("DOWNLOAD_PARAMETER")
    fname = filename(product)
    path = Path(root)/"planck/PR3/cmb"/fname
    url = PREFIX + fname
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        return dict(verify_local_file(path,product),status="EXISTING_REUSED",
                    path=str(path),url=url)
    temp = Path(str(path)+".part")
    if temp.is_symlink():
        raise ValueError("PARTIAL_SYMLINK_REJECTED")
    start = temp.stat().st_size if temp.exists() else 0
    headers = {"User-Agent": "htt_base-Planck-PR3-source/1"}
    if start:
        headers["Range"] = f"bytes={start}-"
    connection = opener or (lambda req: urlopen(req,timeout=timeout))
    res = connection(Request(url, headers=headers))
    expected_total = None
    try:
        status = getattr(res,"status",None)
        if status is None:
            status = res.getcode()
        if start and status == 206:
            cr = res.headers.get("Content-Range","")
            match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+|\*)",cr.strip())
            if not match or int(match.group(1)) != start:
                raise ValueError("UNVERIFIED_HTTP_RANGE_RESUME")
            expected_total = None if match.group(3)=="*" else int(match.group(3))
            mode = "ab"
        elif status == 200:
            expected_total = (int(res.headers["Content-Length"])
                              if res.headers.get("Content-Length","").isdigit() else None)
            mode = "wb"
        else:
            raise ValueError(f"UNEXPECTED_HTTP_STATUS_{status}")
        with temp.open(mode) as out:
            while True:
                block = res.read(chunk_mib << 20)
                if not block:
                    break
                out.write(block)
            out.flush()
            os.fsync(out.fileno())
    finally:
        res.close()
    if expected_total is not None and temp.stat().st_size != expected_total:
        raise ValueError("DOWNLOAD_INCOMPLETE")
    receipt = verify_local_file(temp,product)
    # Atomic same-directory no-clobber link: race cannot replace existing FITS.
    os.link(temp,path,follow_symlinks=False)
    temp.unlink()
    return dict(receipt,status="DOWNLOADED_FITS_FRAMING_VALID",
                path=str(path),url=url,irsa_index=INDEX)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root",default="/mnt/extdrive/workdir/htt_open_data")
    ap.add_argument("--products",nargs="+",choices=PRODUCTS,default=["full"])
    ap.add_argument("--dry-run",action="store_true")
    ap.add_argument("--timeout",type=int,default=120)
    args = ap.parse_args(argv)
    summary = {"schema":"htt.Planck_PR3_SMICA_source_fetch/1",
               "data":[],"physical_simulation_admission":"NOT_ESTABLISHED"}
    for name in dict.fromkeys(args.products):
        if args.dry_run:
            result = {"product":name,"url":PREFIX+filename(name),
                      "minimum_bytes":MIN_BYTES[name],"status":"DRY_RUN"}
        else:
            result = dict(product=name,**transfer(name,args.root,timeout=args.timeout))
        summary["data"].append(result)
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
