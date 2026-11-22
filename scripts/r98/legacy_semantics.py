"""R98 read-only content/AST and archived-source rescue audit.

Reuses R96 root/candidate definitions, adding actual text-payload inspection.
Original corpora and archive members are never extracted or executed. Private
file-level records stay in Downloads; only aggregate and selected scientific
source provenance is exported to the research branch.
"""
from __future__ import annotations
import argparse, ast, collections, gzip, hashlib, json, os, re, subprocess, time, zipfile
from pathlib import Path
from scripts.r96.reindex_source_reuse import SRC, CURATED

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/research_program/observational_publication_20261015/R98_FOURTH_RESEARCH_CYCLE_20261123"
PRIVATE = Path("/home/cosmosapjw/Downloads/htt_r98_private_index")
EXT = {".py",".f90",".f95",".f",".for",".c",".h",".cpp",".hpp",".rs",".jl",".wl",".m",".wls",".tex",".md",".yaml",".yml",".toml"}
CODE_EXT = EXT - {".tex",".md",".yaml",".yml",".toml"}
EXCLUDE = {".git",".venv","venv","node_modules","site-packages","__pycache__",".mypy_cache",".pytest_cache","target","build","dist"}
TOKENS = {"transport":r"geodesic|sachs|jacobi|tetrad|transport|christoffel",
          "kinetic":r"boltzmann|thomson|stokes|polariz|hierarch|collision|visibility",
          "observables":r"biposh|covarian|likelihood|multipole|proper.motion|calibrat|selection",
          "geometry":r"bianchi|codazzi|hamiltonian|shear|vorticity|tilt"}
PAT = {k:re.compile(v,re.I) for k,v in TOKENS.items()}
MAX_TEXT = 4*2**20
def sha_bytes(data): return hashlib.sha256(data).hexdigest()
def inspect_payload(data: bytes, suffix: str):
    try: text=data.decode("utf-8")
    except UnicodeDecodeError: return {"decode":"non_utf8"}
    hits={k:len(v.findall(text)) for k,v in PAT.items()}
    rec={"decode":"utf8","sha256":sha_bytes(data),"bytes":len(data),
         "lines":text.count("\n")+1,"keyword_hits":hits}
    if suffix==".py":
        try:
            tree=ast.parse(text)
            rec["ast_sha256"]=sha_bytes(ast.dump(tree,include_attributes=False).encode())
            rec["symbols"]=[n.name for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]
            rec["imports"]=sorted({n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}|
                                  {a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names})
            rec["declared_intent"]=(ast.get_docstring(tree) or "")[:900]
            rec["ast_status"]="PARSED"
        except SyntaxError as e:rec["ast_status"]="PARSE_ERROR";rec["ast_error"]=str(e)
    elif suffix in CODE_EXT:
        rec["symbols"]=re.findall(r"(?:function|subroutine|fn|class)\s+(\w+)",text,re.I)[:100]
    rec["scope_flags"]=[x for x in ("placeholder","toy","TODO","NotImplementedError","mock","synthetic","native","source") if x in text]
    return rec
def cmd(args, timeout=45):
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=timeout)
    return {"returncode":p.returncode,"stdout":p.stdout,"stderr":p.stderr[:600]}
def scan_dossiers():
    records=[]
    for p in sorted(SRC[2].glob("*.pdf")):
        proc=subprocess.run(["pdftotext","-layout",str(p),"-"],capture_output=True,timeout=45)
        rec={"filename":p.name,"pdf_sha256":sha_bytes(p.read_bytes()),"returncode":proc.returncode}
        if proc.returncode==0:
            text=proc.stdout.decode("utf8",errors="replace")
            (PRIVATE/(p.stem+".txt")).write_text(text)
            rec.update(text_sha256=sha_bytes(proc.stdout),characters=len(text),pages=text.count("\f"),
                       keyword_hits={k:len(v.findall(text)) for k,v in PAT.items()},
                       first_heading=text[:250].strip())
        else:rec["error"]=proc.stderr.decode("utf8",errors="replace")[:300]
        records.append(rec)
    return records
def run():
    t=time.monotonic(); PRIVATE.mkdir(parents=True,exist_ok=True); OUT.mkdir(parents=True,exist_ok=True)
    index=PRIVATE/"content_payloads.jsonl.gz"
    roots=[];errors=[];identities=collections.defaultdict(list);asts=collections.defaultdict(list)
    with gzip.open(index,"wt",encoding="utf8") as f:
        for rid,base in enumerate(SRC):
            count=collections.Counter(); exts=collections.Counter()
            for folder,dirs,names in os.walk(base,followlinks=False):
                skipped=[x for x in dirs if x in EXCLUDE]
                count["excluded_directories"]+=len(skipped)
                dirs[:]=[x for x in dirs if x not in EXCLUDE and not (Path(folder)/x).is_symlink()]
                for name in names:
                    path=Path(folder)/name
                    if path.is_symlink():count["symlink_not_followed"]+=1;continue
                    try: size=path.stat().st_size
                    except OSError as e:errors.append(str(e));continue
                    count["physical_files_seen"]+=1;exts[path.suffix.lower()]+=1
                    suffix=path.suffix.lower()
                    if suffix in EXT:
                        if size>MAX_TEXT:count["text_too_large"]+=1;continue
                        try:
                            rec=inspect_payload(path.read_bytes(),suffix)
                            rec.update(root_id=rid,path=str(path.relative_to(base)),archive=None)
                            count["text_payloads_read"]+=1;count["text_bytes_read"]+=size
                            count["scientific_keyword_payloads"]+=int(any(rec.get("keyword_hits",{}).values()))
                            count["python_ast_parsed"]+=int(rec.get("ast_status")=="PARSED")
                            count["python_ast_errors"]+=int(rec.get("ast_status")=="PARSE_ERROR")
                            f.write(json.dumps(rec,ensure_ascii=False)+"\n")
                            if rec.get("sha256"):identities[rec["sha256"]].append((rid,rec["path"]))
                            if rec.get("ast_sha256"):asts[rec["ast_sha256"]].append((rid,rec["path"]))
                        except OSError as e: errors.append(str(e))
                    # Full eligible text inspection of every legacy ZIP. Other
                    # root archives retain R96 inventory, avoiding repeated bulk.
                    if rid==0 and suffix==".zip":
                        count["zip_attempted"]+=1
                        try:
                            with zipfile.ZipFile(path) as z:
                                for ent in z.infolist():
                                    count["zip_members_seen"]+=1
                                    ep=Path(ent.filename)
                                    if ent.is_dir() or ep.suffix.lower() not in EXT:continue
                                    if any(x in EXCLUDE for x in ep.parts):count["archive_vendor_skipped"]+=1;continue
                                    if ent.file_size>MAX_TEXT:count["archive_text_too_large"]+=1;continue
                                    rec=inspect_payload(z.read(ent),ep.suffix.lower())
                                    rec.update(root_id=rid,path=ent.filename,archive=str(path.relative_to(base)))
                                    count["archive_text_payloads_read"]+=1;count["archive_text_bytes_read"]+=ent.file_size
                                    f.write(json.dumps(rec,ensure_ascii=False)+"\n")
                        except (OSError,zipfile.BadZipFile,ValueError,RuntimeError) as e:
                            count["zip_errors"]+=1;errors.append(f"legacy/{path.relative_to(base)}: {e}")
            roots.append({"root_id":rid,"root":str(base),"counts":dict(count),"extensions":exts.most_common(12)})
            print("R98_CONTENT_ROOT",rid,dict(count),flush=True)
    locks={}
    for key,p in CURATED.items():
        if p.is_file():
            rec={"path":str(p),"bytes":p.stat().st_size,"sha256":sha_bytes(p.read_bytes())}
            if p.suffix in CODE_EXT:
                inspected=inspect_payload(p.read_bytes(),p.suffix)
                rec.update({k:inspected[k] for k in ("ast_status","ast_sha256","symbols","imports","declared_intent","scope_flags") if k in inspected})
            locks[key]=rec
    # Actual local Git trees close the previous recursive-API truncation.
    head=cmd(["git","rev-parse","HEAD"])["stdout"].strip()
    tree=cmd(["git","ls-tree","-r","--name-only",head])
    branches=cmd(["git","for-each-ref","--format=%(refname:short)\t%(objectname)","refs/heads","refs/remotes"])
    selected_branches=[line for line in branches["stdout"].splitlines() if re.search(r"cf4|lowell|bianchi|polar|transport|solver|r69|gaia|radio|mes-|pr296|pr13",line,re.I)]
    logs=cmd(["git","log","--all","--format=%H\t%s","--max-count=100","--regexp-ignore-case","--extended-regexp","--grep=projected.multipole|transport.spine|PR13AG|cf4.*covarian|biposh|Gaia.*VSH|Thomson"])
    prs=cmd(["gh","pr","list","--state","all","--limit","1000","--json","number,title,state,headRefName,baseRefName,mergeCommit,url"],timeout=90)
    selected_pr=[]
    if prs["returncode"]==0:
        all_pr=json.loads(prs["stdout"]); (PRIVATE/"github_pr_inventory.json").write_text(json.dumps(all_pr,indent=2))
        selected_pr=[p for p in all_pr if re.search(r"CF4|Bianchi|solver|polar|Thomson|transport|low.?ell|Gaia|BiPoSH|dossier",p["title"],re.I)]
    else:errors.append("gh_pr_list: "+prs["stderr"])
    (PRIVATE/"duplicate_byte_classes.json").write_text(json.dumps([v for v in identities.values() if len(v)>1],indent=2))
    (PRIVATE/"duplicate_ast_classes.json").write_text(json.dumps([v for v in asts.values() if len(v)>1],indent=2))
    out={"schema":"htt.r98.legacy_content_reuse/1","baseline_head":head,"elapsed_s":time.monotonic()-t,
         "roots":roots,"excluded_directories":sorted(EXCLUDE),"max_text_bytes":MAX_TEXT,
         "legacy_zip_payload_policy":"all eligible UTF8 source/docs <=4MiB; no code execution/extraction; other roots archives reuse R96 inventory",
         "content_index":{"path":str(index),"sha256":sha_bytes(index.read_bytes())},
         "byte_duplicate_classes":sum(len(v)>1 for v in identities.values()),
         "ast_structure_duplicate_classes":sum(len(v)>1 for v in asts.values()),
         "ast_identity_is_not_scientific_semantic_equivalence":True,
         "curated_source_locks":locks,
         "local_git_tree":{"head":head,"tracked_file_count":len(tree["stdout"].splitlines()),"api_truncation":False},
         "relevant_existing_branches":[dict(zip(("ref","sha"),x.split("\t",1))) for x in selected_branches],
         "selected_history_commits":[dict(zip(("sha","subject"),x.split("\t",1))) for x in logs["stdout"].splitlines()],
         "github_pr_query":{"returncode":prs["returncode"],"selected_count":len(selected_pr),"selected":selected_pr,
                            "branch_ancestry_not_used_to_infer_merge":True},
         "dossier_fulltext":scan_dossiers(),
         "errors":errors,"source_corpus_modified":False,
         "interpretation":"Content/AST intake locates reuse; scientific admission requires consumer equations, tests and scope. Metadata matches alone prove neither semantics nor physical adequacy."}
    (OUT/"LEGACY_CONTENT_AUDIT.json").write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps({"completed":True,"roots":len(roots),"seconds":out["elapsed_s"],"errors":len(errors),"selected_pr":len(selected_pr)}))
    return out
if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--dossiers-only",action="store_true");args=ap.parse_args()
    if args.dossiers_only:
        target=OUT/"LEGACY_CONTENT_AUDIT.json";out=json.loads(target.read_text())
        out["dossier_fulltext"]=scan_dossiers();target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n")
        print(json.dumps(out["dossier_fulltext"],ensure_ascii=False))
    else:run()
