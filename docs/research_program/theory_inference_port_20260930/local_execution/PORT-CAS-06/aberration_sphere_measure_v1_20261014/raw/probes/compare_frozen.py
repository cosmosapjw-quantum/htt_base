"""Compare each frozen declaration (FROZEN_TARGETS.md code blocks) with the final
source, whitespace-normalised; declaration text runs up to ':=' or the end of block."""
import re, sys, json, pathlib
T = pathlib.Path(__file__).resolve().parents[2]
fz = (T / "FROZEN_TARGETS.md").read_text()
src = (T / "lean" / "P06ASphere.lean").read_text()
blocks = re.findall(r"```lean\n(.*?)```", fz, re.S)
norm = lambda s: " ".join(s.split())
decls = []
for b in blocks:
    parts = re.split(r"\n(?=(?:/--.*?-/\s*)?(?:theorem|noncomputable def|def|abbrev) )", "\n" + b, flags=re.S)
    for p in parts:
        p = re.sub(r"/--.*?-/", "", p, flags=re.S).strip()
        m = re.match(r"(theorem|noncomputable def|def|abbrev) (\S+)", p)
        if not m: continue
        head = p.split(":=")[0] if m.group(1) == "theorem" else p
        decls.append((m.group(2), norm(head)))
nsrc = norm(re.sub(r"/--.*?-/", "", src, flags=re.S))
res = {}
for name, head in decls:
    res[name] = "MATCH" if head in nsrc else "DIFF"
print(json.dumps(res, indent=1))
