"""R90 strictly limited public-data intake.

Only three official Quaia/Zenodo files <2 MB together. Destination is the
owner's LOCAL Downloads folder; never /mnt/extdrive, no PR4/NPIPE bulk intake.
This module cannot download arbitrary user URLs or files not on the allowlist.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
from urllib.request import urlopen, Request

DEST = Path.home() / "Downloads/htt_r90_minimal_inputs"
RECORD = "https://zenodo.org/api/records/10403370/files/"
ALLOWLIST = {
    "selection_function_NSIDE64_G20.0.fits":
        (400320,"9bec5ff5d2bda8f283fd99d6db6621df"),
    "selection_function_NSIDE64_G20.5.fits":
        (400320,"0aec3460d2e1152afe700d77554341d3"),
    "selection_function_template_maps.zip":
        (879199,"5a887fcdbcb2bb3f2bc4b9de58cd9c67"),
}
CAP_BYTES = 2_000_000

def file_md5(path:Path)->str:
    h=hashlib.md5()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(262144),b""): h.update(block)
    return h.hexdigest()

def download_all()->list[dict]:
    # Strictly in Downloads; explicit path containment.
    if DEST != (Path.home() / "Downloads/htt_r90_minimal_inputs"):
        raise ValueError("invalid destination")
    if sum(s for s,_ in ALLOWLIST.values()) > CAP_BYTES:
        raise ValueError("maximum download budget exceeded")
    DEST.mkdir(parents=True,exist_ok=True)
    receipt=[]
    for name,(expected_size,expected_md5) in ALLOWLIST.items():
        path=DEST/name
        if path.exists():
            if path.stat().st_size!=expected_size or file_md5(path)!=expected_md5:
                raise ValueError(f"pre-existing download identity conflict: {path}")
            receipt.append({"name":name,"status":"ALREADY_IDENTICAL","path":str(path),"bytes":expected_size,"md5":expected_md5})
            continue
        tmp=DEST/(name+".partial")
        if tmp.exists():
            raise ValueError(f"stale partial: {tmp}; do not overwrite blindly")
        try:
            req=Request(RECORD+name+"/content",headers={"User-Agent":"htt-r90-quaia-minimal/1.0"})
            with urlopen(req,timeout=30) as remote, tmp.open("xb") as f:
                total=0
                while True:
                    chunk=remote.read(131072)
                    if not chunk:break
                    total+=len(chunk)
                    if total>expected_size or total>CAP_BYTES:
                        raise ValueError("remote file exceeds verified size budget")
                    f.write(chunk)
            if tmp.stat().st_size!=expected_size or file_md5(tmp)!=expected_md5:
                raise ValueError(f"download checksum/size mismatch: {name}")
            os.rename(tmp,path)
            receipt.append({"name":name,"status":"DOWNLOADED","path":str(path),"bytes":expected_size,"md5":expected_md5})
        except Exception:
            # remove only our newly created partial on failure, never original files.
            if tmp.exists():tmp.unlink()
            raise
    return receipt

def main():
    parser=argparse.ArgumentParser()
    g=parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--list",action="store_true",help="print the fixed 3-file plan; no network or filesystem writes")
    g.add_argument("--fetch",action="store_true",help="download 1.68 MB official Quaia selection metadata to local Downloads")
    args=parser.parse_args()
    info={"schema":"htt.r90.minimal_quaia_downloads/1","directory":str(DEST),
          "whole_planck_pr4_download":False,"external_drive_write":False,
          "official_record":"https://zenodo.org/records/10403370",
          "total_expected_bytes":sum(s for s,_ in ALLOWLIST.values()),
          "allowlist":[{"name":n,"bytes":v[0],"md5":v[1],"url":RECORD+n+"/content"} for n,v in ALLOWLIST.items()],
          "missing_physics_not_repaired_by_these_files":["CF4 upstream MCMC posterior","CF4 physical PV covariance",
          "Commander release-matched polarization MC", "native Bianchi all-m photon transfer"]}
    if args.fetch:
        info["receipt"]=download_all()
    print(json.dumps(info,ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()
