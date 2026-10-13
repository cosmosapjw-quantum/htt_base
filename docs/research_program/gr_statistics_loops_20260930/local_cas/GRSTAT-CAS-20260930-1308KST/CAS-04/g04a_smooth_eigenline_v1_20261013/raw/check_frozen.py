"""Check every frozen declaration in FROZEN_TARGETS.md occurs verbatim (statement part) in the final Lean file."""
import pathlib, re, sys, json, hashlib
T = pathlib.Path(__file__).resolve().parent.parent
md = (T / "FROZEN_TARGETS.md").read_text()
lean = (T / "lean" / "G04AEigenline.lean").read_text()
block = md.split("```lean\n", 1)[1].split("\n```", 1)[0]
block = block.replace("\nend G04A", "")
chunks = [c.strip("\n") for c in re.split(r"\n\s*\n", block) if c.strip()]
res = []
for c in chunks:
    stmt = re.sub(r"\s*:=\s*by <proof>\s*$", "", c)
    stmt = re.sub(r"\s*:=\s*$", "", stmt)
    ok = stmt in lean
    res.append({"decl": stmt.split("\n")[0][:90], "verbatim_present": ok})
forb = {k: len(re.findall(k, lean)) for k in [r"\bsorry\b", r"\badmit\b", r"sorryAx", r"native_decide", r"^\s*axiom\b"]}
out = {"frozen_md_sha256": hashlib.sha256(md.encode()).hexdigest(),
       "lean_sha256": hashlib.sha256(lean.encode()).hexdigest(), "checks": res,
       "all_verbatim": all(r["verbatim_present"] for r in res), "forbidden_token_counts": forb}
print(json.dumps(out, indent=1))
sys.exit(0 if out["all_verbatim"] and not any(forb.values()) else 1)
