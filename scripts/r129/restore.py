"""Restore only the exact R120 archive into a newly created disposable root."""
import argparse, gzip, json, subprocess, tarfile
from pathlib import Path
from scripts.r129.verify_sources import DOC,OLD,sha
from scripts.r120.native_scan import sources

def restore(dest):
    identity=json.loads((DOC/"SOURCE_IDENTITY.json").read_text())
    back=identity["backup"];archive=Path(back["path"])
    if sha(archive.read_bytes())!=back["sha256"]:raise ValueError("archive identity mismatch")
    dest=Path(dest)
    dest.mkdir(parents=True,exist_ok=False)
    with tarfile.open(archive,"r:gz") as t:
        if t.getnames()!=list(back["members_sha256"]):raise ValueError("archive members mismatch")
        for member in t.getmembers():
            f=t.extractfile(member)
            if not member.isfile() or f is None or sha(f.read())!=back["members_sha256"][member.name]:
                raise ValueError("nonregular or changed member")
        t.extractall(dest,filter="data")
    for n,h in back["members_sha256"].items():
        if sha((dest/n).read_bytes())!=h:raise ValueError("restore mismatch "+n)
    binary,table,ref,pilot=sources(dest)
    ax=dest/"AX08.csv";ax.write_bytes(gzip.decompress((dest/"AX08.csv.gz").read_bytes()))
    cmd=[str(dest/"target/release/examples/bass_ionization"),str(dest/"hyrec_xe_1600.tsv"),str(ax),"ZERO","--z-emit","1600"]
    r=subprocess.run(cmd,capture_output=True,check=True)
    if sha(r.stdout)!=sha(table.read_bytes()):raise ValueError("REI joined history byte mismatch")
    return {"source_identity_sha256":sha((DOC/"SOURCE_IDENTITY.json").read_bytes()),"archive_sha256":back["sha256"],
            "verified_members":len(back["members_sha256"]),"binary_sha256":sha(binary.read_bytes()),
            "rei_binary_sha256":sha((dest/"target/release/examples/bass_ionization").read_bytes()),
            "opacity_sha256":sha(table.read_bytes()),"rei_join_replay_byte_identical":True,"rei_join":json.loads(r.stderr),
            "scope":"R120 exact build with identical C4N committed production input trees; historical donor and conditional low-z tail"}
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("dest",type=Path);a=p.parse_args()
    print(json.dumps(restore(a.dest),indent=2,allow_nan=False))
