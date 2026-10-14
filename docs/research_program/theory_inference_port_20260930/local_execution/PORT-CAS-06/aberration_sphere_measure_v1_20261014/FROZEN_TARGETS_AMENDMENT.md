# Amendment to FROZEN_TARGETS.md (recorded after the first main compile; FROZEN_TARGETS.md itself is unchanged)

FROZEN_TARGETS.md (sha256 `fb45b2b305432ab9c8ea4c2e04916c623fecfa028ab1e324d019bfc1d1e041e5`,
mtime 2026-10-14T02:54:23Z; the in-document "02:55Z" stamp is a rounding slip, the
first compile receipt `raw/compile_01_imp_port01.json` started 02:54:40Z).

## A1 — binder annotation in F8 and F9 (elaboration fix, no semantic change)

As frozen, F8 `endpoint_optical_sphere` and F9 `endpoint_optical_sphere_beta_zero`
wrote `∀ᵐ n ∂σS, … (n : E3) 0 …`.  Lean elaborated the binder from the first
ascription `(n : E3)` as `n : E3`, so the frozen statements do not typecheck against
`σS : Measure S2` and `rnDeriv … n` (receipt `raw/compile_07_main.json`, exit 1,
stdout lines 78-114: "argument n has type E3 but is expected to have type ↑S2" and
"failed to synthesize FunLike (Measure ↑S2) (Set E3) ℝ≥0∞").

Amendment: in exactly these two statements, `∀ᵐ n ∂σS,` → `∀ᵐ (n : S2) ∂σS,`.
Nothing else changed: same hypotheses, quantifiers, measure, conclusions.  The
intended reading (σS-a.e. over S²) is the only one under which the frozen text is
well-typed.  Check: `raw/probes/compare_amended.py` → `compare_amended.out.json`
(after this single substitution the frozen text equals the final source, both
statements); `raw/probes/compare_frozen.py` → all 23 other frozen declarations MATCH
the final source verbatim (whitespace-normalised).
