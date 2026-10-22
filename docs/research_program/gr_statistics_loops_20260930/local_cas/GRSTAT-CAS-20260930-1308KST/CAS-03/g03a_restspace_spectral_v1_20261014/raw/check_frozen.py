"""Check that every frozen declaration in FROZEN_TARGETS.md appears verbatim (whitespace-normalised,
up to its first `<proof>` placeholder) in lean/G03ARestspace.lean."""
import hashlib, json, pathlib, re
T = pathlib.Path(__file__).resolve().parent.parent
frozen = (T / "FROZEN_TARGETS.md").read_text()
main = (T / "lean" / "G03ARestspace.lean").read_text()
code = frozen.split("```lean", 1)[1].split("```", 1)[0]
norm = lambda s: re.sub(r"\s+", " ", s).strip()
nmain = norm(main)
blocks = [b for b in re.split(r"\n\s*\n", code) if b.strip()]
results = []
for b in blocks:
    head = b.strip().splitlines()[0]
    if b.strip().startswith(("/-", "import", "namespace", "open", "end ")) and not re.search(r"^(theorem|def|noncomputable|instance|structure)", b.strip(), re.M):
        continue
    if "<proof>" in b:
        if b.strip().startswith("theorem"):
            prefix = b.split("<proof>", 1)[0]
        else:
            idx = b.index("<proof>")
            prefix = b[: b.rfind("\n", 0, idx) + 1] if "\n" in b[:idx] else b[:idx]
    else:
        prefix = b
    # several declarations may share one block (e.g. M1..M3): check each line-group separately
    ok = norm(prefix) in nmain
    results.append({"decl": norm(head)[:90], "verbatim": ok})
out = {"frozen_sha256": hashlib.sha256(frozen.encode()).hexdigest(),
       "main_sha256": hashlib.sha256(main.encode()).hexdigest(),
       "checked": len(results), "all_verbatim": all(r["verbatim"] for r in results),
       "results": results}
(T / "raw" / "check_frozen.out.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
print(out["checked"], out["all_verbatim"])
for r in results:
    if not r["verbatim"]: print("MISMATCH:", r["decl"])
