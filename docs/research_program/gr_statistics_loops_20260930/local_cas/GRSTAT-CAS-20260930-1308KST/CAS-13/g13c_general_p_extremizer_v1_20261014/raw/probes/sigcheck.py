"""Compare frozen signatures (FROZEN_TARGETS.md code blocks) with the compiled source, whitespace/comment-normalized."""
import re, sys, pathlib
T = pathlib.Path(__file__).resolve().parents[2]
fro = (T / "FROZEN_TARGETS.md").read_text()
src = (T / "lean" / "G13CGeneralPExtremizer.lean").read_text()
blocks = re.findall(r"```lean\n(.*?)```", fro, re.S)
def norm(s):
    s = re.sub(r"/--.*?-/", "", s, flags=re.S); s = re.sub(r"--[^\n]*", "", s)
    return " ".join(s.split())
items = []
for b in blocks:
    b = re.sub(r"/--.*?-/", "", b, flags=re.S)
    parts = re.split(r"\n(?=(?:theorem|def) )", "\n" + b.strip())
    items += [norm(p) for p in parts if p.strip()]
srcn = norm(src)
ok = 0
for it in items:
    name = it.split()[1]
    if it.startswith("def "):
        hit = it in srcn
    else:
        hit = (it + " :=") in srcn
    ok += hit
    print("OK " if hit else "MISS", name)
print(f"{ok}/{len(items)} frozen items textually present")
sys.exit(0 if ok == len(items) else 1)
