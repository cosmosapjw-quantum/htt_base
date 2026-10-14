"""Compare every frozen theorem statement in FROZEN_TARGETS.md (with the (BH) abbreviation expanded
verbatim) against the theorem header in lean/G11CWeightedEllipsoid.lean, whitespace-normalised."""
import re, pathlib, hashlib, sys
T = pathlib.Path(__file__).resolve().parent.parent
fz = (T / "FROZEN_TARGETS.md").read_text()
src = (T / "lean" / "G11CWeightedEllipsoid.lean").read_text()
BH = """(μ : Measure X) (s : Stat) (f g W : X → ℝ)
    (hf : Measurable f) (hg : Measurable g)
    (hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s)
    (hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε)
    (hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)"""
norm = lambda t: re.sub(r"\s+", " ", t).strip()
blocks = re.findall(r"```lean\n(.*?)```", fz, re.S)
frozen = {}
for b in blocks:
    for m in re.finditer(r"^theorem (\S+)(.*?)(?=^\s*$|^theorem |^--|^end |\Z)", b, re.S | re.M):
        frozen[m.group(1)] = norm("theorem " + m.group(1) + m.group(2).replace("(BH)", BH))
ok = True
for name, stmt in frozen.items():
    m = re.search(r"^theorem " + re.escape(name) + r"\b(.*?):=", src, re.S | re.M)
    if not m:
        print("MISSING", name); ok = False; continue
    got = norm("theorem " + name + m.group(1))
    same = got == stmt
    ok &= same
    print("MATCH" if same else "DIFF ", name)
    if not same:
        print("  frozen:", stmt); print("  source:", got)
print("frozen_sha256", hashlib.sha256(fz.encode()).hexdigest())
print("source_sha256", hashlib.sha256(src.encode()).hexdigest())
print("ALL_MATCH" if ok else "MISMATCH", len(frozen))
sys.exit(0 if ok else 1)
