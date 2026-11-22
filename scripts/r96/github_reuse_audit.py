"""R96 read-only remote GitHub project tree and historical branch audit.

Use authenticated gh CLI, no checkout, push, pull, merge, network payload
mutation. Public repo paths are scientific source metadata. Private repos
only metadata in private Downloads report, never published to HTT.
"""
import json,subprocess,time
from pathlib import Path

OWNER="cosmosapjw-quantum"
REPOS=["htt_base","bass","rec_bianchi","rei_bianchi","BASS_HE","bass_cr","bianchi_phase_r","HEP-ASTRO-COSMO","cosmo_lab"]
ACTIVE={"htt_base":"research/r69-observable-physics-bridges-20261118",
"bass":"forward/rust-microphysics-host-20260930",
"rec_bianchi":"forward/rust-he-sources-20260922",
"rei_bianchi":"research/flrw-production-integration-20261015"}
ROOT=Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
OUT=ROOT/"docs/research_program/observational_publication_20261015/R96_THREE_THEORY_LOOPS_20261122/GITHUB_SOURCE_AUDIT.json"
PRIVATE=Path("/home/cosmosapjw/Downloads/htt_r96_private_index/remote_trees.json")
PAT=("biposh","cf4","covari","calibr","boltzmann","polar","photon","sachs","thomson","lowl","highell","multipole","transport","mask")
def cmd(*args):
 p=subprocess.run(["gh",*args],capture_output=True,text=True,timeout=30)
 if p.returncode:raise RuntimeError(p.stderr[:350])
 return json.loads(p.stdout)
def main():
 if OUT.exists() or PRIVATE.exists():raise FileExistsError("R96 remote audit create-only")
 pub=[];all_remote=[]
 for repo in REPOS:
  rec={"name":repo}
  try:
   data=cmd("api",f"repos/{OWNER}/{repo}")
   rec.update(url=data["html_url"],default=data["default_branch"],private=bool(data["private"]),branches=[])
   if rec["private"]:
    all_remote.append(rec)
    pub.append({"name":repo,"private_metadata_only":True})
    continue
   refs=list(dict.fromkeys([rec["default"],ACTIVE.get(repo,rec["default"])]))
   for branch in refs:
    b={"branch":branch}
    try:
     sha=cmd("api",f"repos/{OWNER}/{repo}/branches/{branch}")["commit"]["sha"]
     tree=cmd("api",f"repos/{OWNER}/{repo}/git/trees/{sha}?recursive=1")
     blobs=[x["path"] for x in tree["tree"] if x["type"]=="blob"]
     interesting=[x for x in blobs if any(t in x.lower() for t in PAT)]
     b.update(sha=sha,n_files=len(blobs),api_truncated=bool(tree.get("truncated")),
              relevant_count=len(interesting),relevant_paths=interesting[:250])
    except Exception as e:b.update(error=str(e)[:350])
    rec["branches"].append(b)
   pub.append({"name":repo,"url":rec["url"],"branches":[
       {k:v for k,v in b.items() if k!="relevant_paths"} for b in rec["branches"]]})
   all_remote.append(rec)
  except Exception as e:
   rec["error"]=str(e)[:300]
   pub.append({"name":repo,"error":rec["error"]})
   all_remote.append(rec)
  print("GH_R96",repo,"BRANCH",[(b.get("branch"),b.get("n_files"),b.get("api_truncated")) for b in rec.get("branches",[])],flush=True)
 PRIVATE.write_text(json.dumps({"projects":all_remote},indent=2,ensure_ascii=False)+"\n")
 OUT.write_text(json.dumps({"schema":"htt.r96.github_reuse_metadata/1",
  "projects":pub,"remote_list_count":len(pub),"read_only":True,
  "no_private_repository_contents_published":True,
  "API_truncated_is_not_complete_tree":True,
  "original_local_R95_head":"a87df07da328ba6d704e7cf0d554081f52d39213"},indent=2,ensure_ascii=False)+"\n")
if __name__=="__main__":main()
