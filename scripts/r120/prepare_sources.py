"""Reconstruct exact R120 dependency overlay from Git objects, not working files."""
import argparse,hashlib,io,json,subprocess,tarfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/"docs/research_program/observational_publication_20261015/R120_NATIVE_FAMILY_MANIFOLD_20261128"

def sha(b):return hashlib.sha256(b).hexdigest()

def prepare(workspace):
    d=Path(workspace)
    d.mkdir(parents=True,exist_ok=False)
    lock=json.loads((DOC/"SOURCE_LOCK.json").read_text())
    external=json.loads((DOC/"REI_EXTERNAL_INCLUDES.json").read_text())
    paths={"bass":d/"bass_repo/_rustcore","rec":d/"rec","rei":d/"rei_repo/rust/rei_microphysics"}
    def git(spec,*args):
        return subprocess.check_output(["git","-C",str(Path.home()/spec["repo"]),*args])
    def export(raw,dest):
        dest.mkdir(parents=True,exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(raw)) as t:t.extractall(dest,filter="data")
    for n,s in lock.items():
        assert git(s,"rev-parse",s["commit"]+":"+s["crate"]).decode().strip()==s["tree"]
        export(git(s,"archive",s["commit"]+":"+s["crate"]),paths[n])
    bass=lock["bass"]
    for rel,tree in bass["extra_trees"].items():
        assert git(bass,"rev-parse",bass["commit"]+":"+rel).decode().strip()==tree
        export(git(bass,"archive",bass["commit"],rel),d/"bass_repo")
    rei=lock["rei"]
    for rel,h in external.items():
        raw=git(rei,"show",rei["commit"]+":"+rel)
        if sha(raw)!=h:raise ValueError("REI included data mismatch "+rel)
        dest=d/"rei_repo"/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    for fn,stem in (("Cargo.toml","BASS_CARGO"),("Cargo.lock","BASS_LOCK")):
        ext=".toml" if fn.endswith(".toml") else ".lock";p=paths["bass"]/fn
        if p.read_bytes()!=(DOC/(stem+"_ORIGINAL"+ext)).read_bytes():
            raise ValueError("original BASS dependency file mismatch")
        p.write_bytes((DOC/(stem+"_OVERLAY"+ext)).read_bytes())
    return paths

def main():
    ap=argparse.ArgumentParser();ap.add_argument("workspace",type=Path);ap.add_argument("--build",action="store_true");a=ap.parse_args()
    paths=prepare(a.workspace)
    out={"prepared":{k:str(v) for k,v in paths.items()}}
    if a.build:
        for n,ex in (("bass","homogeneous_sky"),("rei","bass_ionization")):
            cmd=["cargo","build","--offline","--locked","--release","--manifest-path",str(paths[n]/"Cargo.toml"),"--target-dir",str(a.workspace/"target"),"--example",ex]
            subprocess.run(cmd,check=True)
            out[n]={"sha256":sha((a.workspace/"target/release/examples"/ex).read_bytes()),"argv":cmd}
        out["scope"]="new build identity; compare against R7 or qualify independently"
    print(json.dumps(out,indent=2))
if __name__=="__main__":main()
