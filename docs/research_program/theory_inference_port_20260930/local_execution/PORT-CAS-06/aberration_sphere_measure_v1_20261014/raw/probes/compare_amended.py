"""Check that the ONLY difference of the DIFF declarations is the binder annotation
`∀ᵐ n ∂σS,` -> `∀ᵐ (n : S2) ∂σS,` in F8/F9."""
import re, json, pathlib, runpy
T = pathlib.Path(__file__).resolve().parents[2]
fz = (T / "FROZEN_TARGETS.md").read_text()
src = (T / "lean" / "P06ASphere.lean").read_text()
norm = lambda s: " ".join(s.split())
nsrc = norm(re.sub(r"/--.*?-/", "", src, flags=re.S))
out = {}
for name in ["endpoint_optical_sphere", "endpoint_optical_sphere_beta_zero"]:
    m = re.search(r"theorem " + name + r" (.*?):= by|theorem " + name + r" (.*?)```", fz, re.S)
    body = re.search(r"theorem " + re.escape(name) + r"\s.*?(?=```)", fz, re.S).group(0)
    am = body.replace("∀ᵐ n ∂σS,", "∀ᵐ (n : S2) ∂σS,")
    out[name] = {"occurrences_replaced": body.count("∀ᵐ n ∂σS,"),
                 "amended_matches_final": norm(am) in nsrc}
print(json.dumps(out, indent=1))
