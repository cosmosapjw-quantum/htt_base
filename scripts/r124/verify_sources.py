"""Compare current committed production inputs to R120's exact execution inputs."""
import hashlib,json,subprocess,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/"docs/research_program/observational_publication_20261015/R124_CODAZZI_LINEAR_SECTORS_20261128"
OLD=DOC.parent/"R120_NATIVE_FAMILY_MANIFOLD_20261128"
REVS={"bass":("2d7565762605d0e88904ca8ac768adffb6af2a0d","research/r118c4k_composite_tangent"),
      "rec":("6273f720394f025b8c44498dd99773830feca54b","research/r118c4k_lambda_tangent"),
      "rei":("eae6845626335ad802a06d7ca21ced1d0a059937","research/r118c4k_moving_nodes")}
def sha(b):return hashlib.sha256(b).hexdigest()
def inspect():
    x=json.loads((OLD/"SOURCE_LOCK.json").read_text());inc=json.loads((OLD/"REI_EXTERNAL_INCLUDES.json").read_text());out={}
    for k,(rev,science) in REVS.items():
        s=x[k];repo=Path.home()/s["repo"]
        def git(*a):return subprocess.check_output(["git","-C",str(repo),*a])
        tree=git("rev-parse",rev+":"+s["crate"]).decode().strip()
        filename={"bass":"REFINED_COMPOSITE.json","rec":"PRECOMPUTED_FD.json","rei":"GOAL_REFINEMENT.json"}[k]
        b=git("show",rev+":"+science+"/"+filename);z=json.loads(b)
        item={"repo":str(repo),"current_commit":rev,"r120_commit":s["commit"],"crate":s["crate"],
              "tree":tree,"r120_tree":s["tree"],"tree_identical":tree==s["tree"],
              "science_path":science+"/"+filename,"science_sha256":sha(b),"science_keys":list(z) if isinstance(z,dict) else {"list_records":len(z)},
              "science_scope":"C4K in-progress source receipt, not completed FINAL_SCIENCE"}
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
    return {"repositories":out,"backup":back,"r120_input_tree_identity":True,"scope":"same production crate and extra tree/include bytes; C4K research drivers not activated"}
if __name__=="__main__":
    print(json.dumps(inspect(),indent=2,allow_nan=False))
