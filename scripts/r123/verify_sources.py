"""Compare current committed production inputs to R120's exact execution inputs."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/"docs/research_program/observational_publication_20261015/R123_CURVED_LINEAR_ORACLE_20261128"
OLD=DOC.parent/"R120_NATIVE_FAMILY_MANIFOLD_20261128"
REVS={"bass":("ba94045df21fee8277bb67927c0b289a8a605ac1","research/r118c4j_operator_jet"),
      "rec":("6848ad20e9b59eb2575292f3fe08aa3cbec8ee21","research/r118c4j_signed_tangent"),
      "rei":("3727f816ba4eadfd4cc31238bc9d152b1944932a","research/r118c4j_shape_jac")}
def sha(b):return hashlib.sha256(b).hexdigest()
def inspect():
    x=json.loads((OLD/"SOURCE_LOCK.json").read_text());inc=json.loads((OLD/"REI_EXTERNAL_INCLUDES.json").read_text());out={}
    for k,(rev,science) in REVS.items():
        s=x[k];repo=Path.home()/s["repo"]
        def git(*a):return subprocess.check_output(["git","-C",str(repo),*a])
        tree=git("rev-parse",rev+":"+s["crate"]).decode().strip()
        b=git("show",rev+":"+science+"/FINAL_SCIENCE.json");z=json.loads(b)
        item={"repo":str(repo),"current_commit":rev,"r120_commit":s["commit"],"crate":s["crate"],
              "tree":tree,"r120_tree":s["tree"],"tree_identical":tree==s["tree"],
              "science_path":science+"/FINAL_SCIENCE.json","science_sha256":sha(b),"science_keys":list(z),
              "next":git("show",rev+":"+science+"/NEXT.md").decode().strip()}
        if k=="bass":
            item["extra_trees"]={rel:{"current":git("rev-parse",rev+":"+rel).decode().strip(),"r120":h} for rel,h in s["extra_trees"].items()}
            if any(v["current"]!=v["r120"] for v in item["extra_trees"].values()):raise ValueError("BASS extra tree mismatch")
        if k=="rei":
            item["external_includes"]={rel:sha(git("show",rev+":"+rel)) for rel in inc}
            if item["external_includes"]!=inc:raise ValueError("REI external include mismatch")
        if tree!=s["tree"]:raise ValueError("changed crate: "+k)
        out[k]=item
    back=json.loads((OLD/"C10_BACKUP.json").read_text())["backup"];archive=Path(back["path"])
    if sha(archive.read_bytes())!=back["sha256"]:raise ValueError("archive mismatch")
    with tarfile.open(archive,"r:gz") as t:
        if t.getnames()!=list(back["members_sha256"]):raise ValueError("archive members mismatch")
        for n,h in back["members_sha256"].items():
            f=t.extractfile(n)
            if f is None or sha(f.read())!=h:raise ValueError("member mismatch "+n)
    return {"repositories":out,"backup":back,"r120_input_tree_identity":True,"scope":"same production crate and extra tree/include bytes; C4J research drivers not activated"}
if __name__=="__main__":
    print(json.dumps(inspect(),indent=2,allow_nan=False))
