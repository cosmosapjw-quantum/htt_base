"""Check that every frozen declaration in FROZEN_TARGETS.md occurs verbatim (whitespace-normalized,
up to `:= by <proof>`) in the final Lean sources.  Writes raw/check_frozen.out.json."""
import hashlib, json, pathlib, re

T = pathlib.Path(__file__).resolve().parent.parent
frozen = (T / "FROZEN_TARGETS.md").read_text()
mods = ["G05BJet", "G05BIFT", "G05BSymm", "G05BGerm"]
src = {m: (T / "lean" / f"{m}.lean").read_text() for m in mods}
norm = lambda s: re.sub(r"\s+", " ", s).strip()
allsrc = norm("\n".join(src.values()))

blocks = re.findall(r"```lean\n(.*?)```", frozen, re.S)
decls = []
for b in blocks:
    lines = [l for l in b.splitlines()]
    cur = None
    for l in lines:
        st = l.strip()
        start = re.match(r"^(noncomputable def|def|theorem) ", st)
        if start:
            if cur: decls.append(cur)
            cur = [l]
        elif cur is not None:
            if st.startswith("--") or st.startswith("/--") or st == "":
                decls.append(cur); cur = None
            else:
                cur.append(l)
    if cur: decls.append(cur)

results = []
for d in decls:
    text = "\n".join(d)
    text = text.split(":= by <proof>")[0]
    name = re.match(r"^\s*(?:noncomputable def|def|theorem) (\S+)", text).group(1)
    ok = norm(text) in allsrc
    results.append({"name": name, "verbatim": ok})

out = {"all_verbatim": all(r["verbatim"] for r in results), "count": len(results),
       "ok": sum(r["verbatim"] for r in results), "results": results,
       "frozen_sha256": hashlib.sha256((T / "FROZEN_TARGETS.md").read_bytes()).hexdigest(),
       "source_sha256": {m: hashlib.sha256(src[m].encode()).hexdigest() for m in mods}}
(T / "raw" / "check_frozen.out.json").write_text(json.dumps(out, indent=1) + "\n")
print(out["all_verbatim"], out["ok"], "/", out["count"])
for r in results:
    if not r["verbatim"]:
        print("NOT VERBATIM:", r["name"])
