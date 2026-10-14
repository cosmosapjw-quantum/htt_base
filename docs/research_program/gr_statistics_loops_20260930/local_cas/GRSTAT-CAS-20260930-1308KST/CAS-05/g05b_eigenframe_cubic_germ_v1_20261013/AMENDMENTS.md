# G05-B post-freeze notes

FROZEN_TARGETS.md (sha256 b26beecc…82fc, frozen 2026-10-13T21:04:04Z) is unchanged. No frozen statement
was changed, weakened or strengthened. `raw/check_frozen.py` reports all 27 frozen declarations verbatim
(`raw/check_frozen.out.json`).

Implementation notes (not amendments):
- `Ein_first_jet`, `Ric_symm`, `selfAdj_mixed` are proved inside `section` blocks as `*_sec` forms and
  restated outside the sections with the exact frozen binders (`:= by exact *_sec …`).
- Additional non-frozen helper theorems (e.g. `dGam_jet`, `Ric_jet`, `pd_ginv`, `trace_dGam`,
  `rate_origin`, `det_ne_of_lorentzian`) are all covered by the axiom audit (98 theorems).
- Intermediate compile attempts 06–08 of `G05BJet` contained a `sorry` placeholder for `dGam_jet`
  (06/07 also failed); the final sources contain no `sorry`.
