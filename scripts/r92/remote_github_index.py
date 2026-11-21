"""R92 read-only GitHub tree index, scope only repositories related to BASS/Bianchi.

Uses authorized gh CLI, no git checkout, no clone, no repo mutation. Full tree
paths kept in local Downloads; publication-safe summary strips code file list
and private project metadata. Both default and explicitly known active branch
are inspected where present. API errors/truncation remain explicit.
"""
import concurrent.futures,datetime,json,subprocess
from pathlib import Path

OUT=Path("/home/cosmosapjw/Downloads/htt_r92_private_index")
OWNER="cosmosapjw-quantum"
PROJECTS=["htt_base","bass","rec_bianchi","rei_bianchi","BASS_HE","bass_cr",
          "bianchi_phase_r","HEP-ASTRO-COSMO","cosmo_lab"]
ACTIVE={
 "htt_base":"research/r69-observable-physics-bridges-20261118",
 "bass":"forward/rust-microphysics-host-20260930",
 "rec_bianchi":"forward/rust-he-sources-20260922",
 "rei_bianchi":"research/flrw-production-integration-20261015"
}
def gh(*args):
 x=subprocess.run(["gh",*args],capture_output=True,text=True,timeout=30,check=False)
 if x.returncode:raise RuntimeError(f"gh failure code={x.returncode}: {x.stderr[:350]}")
 return json.loads(x.stdout)

def one(repo):
 record={"name":repo,"status":"UNKNOWN","branches":[]}
 try:
  info=gh("api",f"repos/{OWNER}/{repo}")
  record.update(is_private=bool(info["private"]),url=info["html_url"],
                default_branch=info["default_branch"],repo_id=info["id"])
  if record["is_private"]:
   record.update(status="PRIVATE_METADATA_ONLY_NOT_MIRRORED")
   return record
  branches=list(dict.fromkeys([record["default_branch"],ACTIVE.get(repo,record["default_branch"])]))
  for br in branches:
   item={"branch":br}
   try:
    branch=gh("api",f"repos/{OWNER}/{repo}/branches/{br}")
    sha=branch["commit"]["sha"]
    tree=gh("api",f"repos/{OWNER}/{repo}/git/trees/{sha}?recursive=1")
    filelist=[e for e in tree["tree"] if e["type"]=="blob"]
    item.update(head_sha=sha,blob_paths=len(filelist),
                truncated=bool(tree.get("truncated",False)),
                status="INDEXED_DEFAULT_OR_ACTIVE" if not tree.get("truncated") else "TRUNCATED_API_TREE",
                content_candidates=sum(1 for f in filelist if f["path"].endswith((".py",".rs",".md",".tex",".ipynb",".f90"))))
    filepath=OUT/("R92_REMOTE_TREE_"+repo.replace("-","_")+"_"+br.replace("/","_")+".json")
    if filepath.exists():raise RuntimeError("create-only remote tree index exists")
    filepath.write_text(json.dumps({"repo":repo,"branch":br,"sha":sha,"tree":tree["tree"]},ensure_ascii=False)+"\n")
    item["private_index"]=str(filepath)
   except Exception as e:item.update(status="ERROR",error=str(e)[:400])
   record["branches"].append(item)
  record["status"]="INDEXED" if all(b["status"].startswith("INDEXED") for b in record["branches"]) else "PARTIAL"
 except Exception as e:record.update(status="ERROR",error=str(e)[:400])
 return record

def main():
 if (OUT/"R92_REMOTE_GITHUB_AUDIT.json").exists():raise RuntimeError("already indexed")
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  results=list(pool.map(one,PROJECTS))
 p=OUT/"R92_REMOTE_GITHUB_AUDIT.json"
 p.write_text(json.dumps({"schema":"htt.r92.related_remote_github_tree_index/1",
                          "utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),
                          "projects":results},ensure_ascii=False,indent=2)+"\n")
 for r in results:print("GH_REPO",r["name"],r["status"],
                           [(x.get("branch"),x.get("blob_paths"),x.get("status")) for x in r["branches"]],flush=True)
if __name__=="__main__":main()
