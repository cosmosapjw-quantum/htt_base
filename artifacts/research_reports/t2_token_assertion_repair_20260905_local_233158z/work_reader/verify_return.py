"""One-shot WORK_THREAD return review; no authored source edits or pytest/CAS execution."""
import ast, hashlib, json, re, sys, time, zipfile
from datetime import datetime, timezone
from pathlib import Path
import xml.etree.ElementTree as ET
import yaml

ROOT = Path(__file__).resolve().parent
R = ROOT / "local_return/result"
def readj(p): return json.loads(p.read_text())
def sha(b): return hashlib.sha256(b).hexdigest()
def blob(b): return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def stamp(): return datetime.now(timezone.utc).isoformat()
def lf_lines(b):
    parts=b.split(b"\n")
    return [x+b"\n" for x in parts[:-1]] + ([parts[-1]] if parts[-1] else [])
base = readj(ROOT/"base_tree.json")
assert base["sha"]=="26d68c52997cff838670ccea9dc05d15f7bda75f" and base["truncated"] is False
bt={x["path"]:x for x in base["tree"] if x["type"]!="tree"}
before=readj(R/"source-manifest.before.json"); after=readj(R/"source-manifest.after.json")
bm={x["path"]:x for x in before["files"]}; am={x["path"]:x for x in after["files"]}
assert len(bt)==len(bm)==len(am)==5869 and set(bt)==set(bm)==set(am)
changed=[]
for p,b in bm.items():
    a=am[p]; g=bt[p]
    assert b["git_blob"]==g["sha"]==a["old_git_blob"]
    assert b["mode"]==g["mode"]
    assert b["sha256"]==a["old_sha256"]
    different=(a["old_git_blob"]!=a["new_git_blob"])
    assert different == (a["old_sha256"]!=a["new_sha256"]) == (not a["unchanged"])
    if different: changed.append(p)
allowed=["docs/research_reports/theory_packs/T2_QO_ORBIT_RECONSTRUCTION_THEOREM_PACK.md","tests/contracts/test_report_a_r4a0_source.py"]
assert set(changed)==set(allowed)==set(after["changed_paths"])
ident=readj(R/"old-new-identities.json")
assert {x["path"] for x in ident}==set(allowed)
original={}; repaired={}
for x in ident:
    p=x["path"]; original[p]=(R/"original-source"/p).read_bytes(); repaired[p]=(R/"repaired-source"/p).read_bytes()
    for version,data in [("old",original[p]),("new",repaired[p])]:
        assert blob(data)==x[version+"_git_blob"]==am[p][version+"_git_blob"]
        assert sha(data)==x[version+"_sha256"]==am[p][version+"_sha256"]
        assert len(data)==x[version+"_bytes"]
    assert blob(original[p])==bt[p]["sha"]
# Recompute the Git tree, including file modes and byte-order directory sorting.
def make_tree(entries):
    trie={}
    for path,mode,oid in entries:
        node=trie
        parts=path.split("/")
        for name in parts[:-1]: node=node.setdefault(name,{})
        assert parts[-1] not in node
        node[parts[-1]]=(mode,oid)
    def emit(node):
        payload=b""
        for name,item in sorted(node.items(),key=lambda kv:(kv[0]+("/" if isinstance(kv[1],dict) else "")).encode()):
            mode,oid=("40000",emit(item)) if isinstance(item,dict) else item
            payload+=mode.encode()+b" "+name.encode()+b"\0"+bytes.fromhex(oid)
        return hashlib.sha1(b"tree "+str(len(payload)).encode()+b"\0"+payload).hexdigest()
    return emit(trie)
assert make_tree((p,g["mode"],g["sha"]) for p,g in bt.items())==base["sha"]
candidate_tree=make_tree((p,g["mode"],am[p]["new_git_blob"]) for p,g in bt.items())
# Replay the exact submitted unified patch in memory, preserving form-feed and LF bytes.
patch=(R/"two-file-repair.patch").read_bytes()
blocks=patch.split(b"diff --git ")[1:]
assert len(blocks)==2
patch_paths=[]
for block in blocks:
    lines=lf_lines(b"diff --git "+block)
    match=re.fullmatch(rb"diff --git a/(.+) b/(.+)\n",lines[0])
    assert match and match[1]==match[2]
    p=match[1].decode();patch_paths.append(p)
    old=lf_lines(original[p]); out=[]; cursor=0; i=0
    while i<len(lines):
        if not lines[i].startswith(b"@@ "): i+=1;continue
        h=re.match(rb"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@",lines[i]);assert h
        start=int(h[1])-1; nold=int(h[2] or b"1");nnew=int(h[4] or b"1")
        out+=old[cursor:start];cursor=start;used=made=0;i+=1
        while i<len(lines) and not lines[i].startswith(b"@@ "):
            line=lines[i];op=line[:1];value=line[1:]
            assert op in (b" ",b"-",b"+"),line
            if op in (b" ",b"-"): assert old[cursor]==value;cursor+=1;used+=1
            if op in (b" ",b"+"): out.append(value);made+=1
            i+=1
        assert (used,made)==(nold,nnew)
    out+=old[cursor:]
    assert b"".join(out)==repaired[p]
assert set(patch_paths)==set(allowed)
# Exactly the three documented corrupt tokens; independent reversal.
t2=allowed[0]; old=original[t2];new=repaired[t2]
sites=[m.start() for m in re.finditer(b"\x0crac\\{",old)]
assert sites==[4643,4703,4754] and old.count(b"\x0c")==3
assert len(new)==len(old)+3 and old.replace(b"\x0crac{",b"\\frac{")==new
back=new
for i,offset in reversed(list(enumerate(sites))):
    offset+=i
    assert back[offset:offset+6]==b"\\frac{"
    back=back[:offset]+b"\x0crac{"+back[offset+6:]
assert back==old
site_rows=[{"old_offset_zero_based":o,"new_offset_zero_based":o+i,"LF_line":old[:o].count(b"\n")+1} for i,o in enumerate(sites)]
fixed={x["path"]:x for x in readj(ROOT/"fixed_sources.json")}
fixed_records=[]
for p,x in fixed.items():
    data=x["content"].encode()
    assert blob(data)==x["sha"]==bt[p]["sha"]
    assert sha(data)==bm[p]["sha256"]
    fixed_records.append({"path":p,"git_blob":blob(data),"sha256":sha(data)})
r3path="docs/research_reports/HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md"
r3=fixed[r3path]["content"]
proof=readj(R/"token-restoration-proof.json")
for formula in proof["authority_formulas"]: assert formula in r3
assert proof["intact_authority_blob"]==fixed[r3path]["sha"]
# Contract identity and external result versus embedded result.
live=readj(ROOT/"github_before.json")
contract=live["contract"]["body"].encode()
assert sha(contract)=="b7d7ab18124e5ebf3e4637141d33bbb46549c32f487b6f03346557a77d49a66f"
assert (R/"intake/LOCAL_CODEX_EXECUTION_CONTRACT.md").read_bytes()==contract
embedded=yaml.safe_load((R/"t2_repair_result.yaml").read_text())["t2_repair_result"]
external=yaml.safe_load((ROOT.parent/"upload/t2_repair_result.yaml").read_text())["t2_repair_result"]
allowed_external={"return_archive_sha256","return_archive_digest_location","return_archive_path","return_archive_bytes","return_payload_file_count","archive_crc_and_sha256_manifest_verified","archive_verified_at"}
external_diff=[k for k in set(external)|set(embedded) if external.get(k)!=embedded.get(k)]
assert set(external_diff)<=allowed_external,external_diff
assert embedded["return_archive_sha256"] is None
assert external["return_archive_sha256"]==readj(ROOT/"ARCHIVE_INTAKE.json")["archive_sha256"]
# Original RED bytes matched to the immutable published Git tree.
red_prefix="artifacts/research_reports/authority_citation_replay_20260905_local_130332z/"
red_records=[]
for file in (R/"archived-red").iterdir():
    if file.name.startswith("source-manifest."): continue
    remote=red_prefix+(file.name if file.name in ("NODE_ACCOUNTING.json","PROTECTED_SOURCE_REVIEW.json") else "local_return/result/"+file.name)
    assert remote in bt and blob(file.read_bytes())==bt[remote]["sha"],remote
    red_records.append({"path":file.name,"remote_path":remote,"git_blob":blob(file.read_bytes()),"sha256":sha(file.read_bytes())})
red_review=readj(R/"archived-red/PROTECTED_SOURCE_REVIEW.json")
for tag in ("before","after"):
    assert sha((R/f"archived-red/source-manifest.{tag}.json").read_bytes())==red_review[tag+"_manifest_sha256"]
# Parse actual original/new/focused JUnit; counts are distinct by node identity.
def junit(path):
    data=path.read_bytes()
    assert b"<!DOCTYPE" not in data and b"<!ENTITY" not in data
    doc=ET.fromstring(data); rows={}
    for c in doc.iter("testcase"):
        node=c.attrib["classname"].replace(".","/")+".py::"+c.attrib["name"]
        assert node not in rows
        state="FAIL" if c.find("failure") is not None else "ERROR" if c.find("error") is not None else "SKIP" if c.find("skipped") is not None else "PASS"
        rows[node]={"status":state,"seconds":c.attrib.get("time")}
    summaries=[dict(x.attrib) for x in doc.iter("testsuite")]
    return rows,summaries
red,red_s=junit(R/"archived-red/authority-replay.xml")
full,full_s=junit(R/"authority-replay.xml");focus,focus_s=junit(R/"focused.xml")
assert len(red)==40 and sum(x["status"]=="FAIL" for x in red.values())==3
assert len(full)==80 and all(x["status"]=="PASS" for x in full.values())
assert len(focus)==43 and all(x["status"]=="PASS" for x in focus.values())
assert set(red)<set(full) and set(focus)<set(full)
collected=[line for line in (R/"collect.stdout").read_text().split("\n") if line.startswith("tests/") and "::" in line]
redcol=[line for line in (R/"archived-red/collect.stdout").read_text().split("\n") if line.startswith("tests/") and "::" in line]
assert len(collected)==len(set(collected))==80 and set(collected)==set(full)
assert len(redcol)==40 and set(redcol)==set(red)
added=set(full)-set(red)
pos={n for n in added if "::test_canonical_section_accepts_ascii_wrapping[" in n or "::test_scope_accepts_only_the_two_declared_positive_spellings[" in n}
neg=added-pos
assert len(pos)==7 and len(neg)==33
inventory=readj(R/"NODE_AND_FIXTURE_RESULTS.json")
for key,expected in [("original_results",set(red)),("added_results",added),("positive_fixture_results",pos),("negative_fixture_results",neg)]:
    assert {x["nodeid"] for x in inventory[key]}==expected
    assert all(x["status"]=="PASS" for x in inventory[key])
# Validate complete command records and source freeze without running them again.
receipt=readj(R/"EXECUTION_RECEIPT.json");freeze=readj(R/"repaired-source-freeze.json");versions=readj(R/"versions.json")
assert versions==receipt["versions"]
assert (versions["implementation"],versions["python"],versions["pytest"],versions["PyYAML"])==("CPython","3.12.3","8.4.2","6.0.3")
frozen_time=datetime.fromisoformat(freeze["frozen_at"])
for x in freeze["files"]:
    assert sha(repaired[x["path"]])==x["sha256"] and blob(repaired[x["path"]])==x["git_blob"]
assert len(receipt["commands"])==5
commands=[];last=None
for c in receipt["commands"]:
    label=c["label"]
    assert readj(R/(label+".command.json"))==c
    assert c["exit_code"]==int((R/(label+".exit")).read_text())==0
    assert not c["timed_out"] and c["timeout_seconds"]==900 and c["invocation_count_for_label"]==1
    assert c["source_freeze_sha256"]==sha((R/"repaired-source-freeze.json").read_bytes())
    assert c["versions"]==versions
    assert (R/c["stderr"]).read_bytes()==b""
    start=datetime.fromisoformat(c["started_at"]);end=datetime.fromisoformat(c["completed_at"])
    assert frozen_time<start<=end
    if last: assert last<=start
    last=end
    assert c["elapsed_seconds"]<c["timeout_seconds"]
    commands.append({k:c[k] for k in ["label","argv","cwd","child_pid","exit_code","started_at","completed_at","elapsed_seconds","timed_out"]})
plan=readj(R/"execution-plan.before-edits.json")
assert receipt["commands"][-1]["argv"]==plan["suite_argv"]
assert len(plan["suite_files"])==8 and set(plan["suite_files"])=={n.split("::")[0] for n in red}
assert "80 passed" in (R/"authority-replay.stdout").read_text() and "43 passed" in (R/"focused.stdout").read_text()
assert (R/"main-head.after").read_bytes()==(R/"intake/main-head.before").read_bytes()
assert (R/"main-status.after").read_bytes()==(R/"intake/main-status.before").read_bytes()
# Preserve original names; static source audit, no importing submitted tests.
old_ast=ast.parse(original[allowed[1]]);new_ast=ast.parse(repaired[allowed[1]])
old_names={n.name for n in old_ast.body if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")}
new_names={n.name for n in new_ast.body if isinstance(n,ast.FunctionDef) and n.name.startswith("test_")}
assert len(old_names)==3 and old_names<=new_names
for n in ast.walk(new_ast):
    if isinstance(n,ast.Attribute): assert n.attr not in ("skip","skipif","xfail")
# Recompute canonical ID digest by independent reader, not by pytest.
t9rec=readj(ROOT/"t9_source.json");t9b=t9rec["content"].encode()
assert blob(t9b)==t9rec["sha"]==bt[t9rec["path"]]["sha"]
assert sha(t9b)==bm[t9rec["path"]]["sha256"]==am[t9rec["path"]]["new_sha256"]
ledger=yaml.safe_load(t9b)
ids=[x["id"] for x in ledger["claims"]]
assert len(ids)==len(set(ids))==30
digest=sha(("\n".join(sorted(ids))+"\n").encode())
assert digest==embedded["canonical_30_id_digest"]=="e103c581ce353b5102af81834831ac292105f18699671e8eb75b171acd97f01e"
assert ledger["coverage"]["canonical_sorted_id_sha256"] is None
assert ledger["coverage"]["canonical_sorted_id_sha256_status"]=="PENDING_SUPPORTED_RUNTIME_REPLAY"
report={
 "work_unit":receipt["work_unit"],"review_role":"WORK_THREAD","review_mode":"SEQUENTIAL_RESULT_INFORMED_NOT_BLIND",
 "status":"PASS_RETURN_INTEGRITY_AND_EXECUTION_EVIDENCE_REVIEW",
 "base_commit":before["base"],"base_tree":base["sha"],"candidate_source_tree_computed_not_committed":candidate_tree,
 "base_tree_rows":len(bt),"manifest_rows_compared":len(bm),"protected_unchanged_manifest_rows":5867,
 "complete_native_workstation_rehash_by_work":False,
 "evidence_limit":"WORK rehashed actual returned and selected GitHub payloads and checked all manifest identities against the immutable Git tree; untouched native files are attested by the local before/after capture.",
 "changed_paths":changed,"old_new_identities":ident,"patch_replayed_in_memory_exactly":True,
 "three_token_sites":site_rows,"token_reversal_recovers_original":True,"all_other_T2_bytes_identical":True,
 "fixed_payloads_rehashed":fixed_records,"external_result_differences":external_diff,
 "archived_RED":{"nodes":40,"PASS":37,"FAIL":3,"fresh_run":False,"published_payloads_rehashed":red_records,"large_manifests_match_published_hashes":True},
 "original_nodes":{"executed":40,"PASS":40,"FAIL":0},"added_nodes":{"executed":40,"positive":7,"negative":33},
 "full_suite":{"executed":80,"PASS":80,"FAIL":0,"errors":0,"skips":0,"xfail":0,"xpass":0,"deselected":0,"timeouts":0},
 "focused":{"executed":43,"PASS":43,"subset_of_full":True},"full_junit_summaries":full_s,"focused_junit_summaries":focus_s,
 "new_pytest_executions_by_work":0,"new_CAS_executions_by_work":0,"local_versions":versions,
 "local_command_records":commands,"source_frozen_before_execution":True,"original_test_functions_preserved":sorted(old_names),
 "canonical_30_ID_digest":digest,"canonical_ledger_hash_field":None,"canonical_ledger_hash_status":ledger["coverage"]["canonical_sorted_id_sha256_status"],
 "canonical_claims":30,"candidate_claims":40,"recorded_at":stamp()
}
(ROOT/"RETURN_VERIFICATION.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n")
(ROOT/"verified_node_inventory.json").write_text(json.dumps({"original":sorted(red),"positive":sorted(pos),"negative":sorted(neg),"full_junit":full,"focused_junit":focus},indent=2)+"\n")
print(json.dumps({k:report[k] for k in ["status","candidate_source_tree_computed_not_committed","manifest_rows_compared","protected_unchanged_manifest_rows","three_token_sites","original_nodes","added_nodes","full_suite","focused","canonical_30_ID_digest"]},indent=2))

