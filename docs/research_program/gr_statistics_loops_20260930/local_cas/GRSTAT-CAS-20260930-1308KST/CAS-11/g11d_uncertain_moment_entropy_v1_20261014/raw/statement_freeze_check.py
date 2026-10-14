"""Compare each frozen theorem statement (FROZEN_TARGETS.md, (BH) expanded) with the Lean source header."""
import re, pathlib, sys
T = pathlib.Path(__file__).resolve().parent.parent
md = (T / "FROZEN_TARGETS.md").read_text()
src = (T / "lean" / "G11DUncertainMoment.lean").read_text()
BH = ("(μ : Measure X) (s : Stat) (f g W : X → ℝ) (hf : Measurable f) (hg : Measurable g) "
      "(hfd : ∀ᵐ x ∂μ, f x ∈ cdom s) (hgd : ∀ᵐ x ∂μ, g x ∈ dom s) "
      "(hW : WEnvelope μ s W f g) {ε : ℝ} (hε0 : 0 ≤ ε) "
      "(hε : Dext μ (hS s) (hS' s) f g ≤ ENNReal.ofReal ε)")
norm = lambda t: re.sub(r"\s+", " ", re.sub(r"--[^\n]*", "", t)).strip()
blocks = "\n".join(re.findall(r"```lean\n(.*?)```", md, re.S))
frozen = {}
for m in re.finditer(r"theorem (\w+)(.*?)(?=\ntheorem |\n--|\nend General|\Z)", blocks, re.S):
    frozen[m.group(1)] = norm(m.group(2).replace("(BH)", BH))
lean = {}
for m in re.finditer(r"theorem (\w+)(.*?):=", src, re.S):
    lean[m.group(1)] = norm(m.group(2))
ok = True
for name, st in frozen.items():
    if name not in lean:
        print("MISSING", name); ok = False; continue
    if "..." in st:
        print("ELIDED_IN_FROZEN (checked by hand)", name); continue
    print("MATCH" if st == lean[name] else "DIFF", name)
    if st != lean[name]:
        ok = False; print("  frozen:", st); print("  lean  :", lean[name])
print("extra lean theorems (helpers):", sorted(set(lean) - set(frozen)))
sys.exit(0 if ok else 1)
