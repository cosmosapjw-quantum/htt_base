# AUDIT_PRELIMINARY_RESULTS_MODE_2026-04-22

## Scope

- `docs/manuscript/ch01_introduction.tex`
- `docs/manuscript/ch06_pipeline.tex`
- `docs/manuscript/ch07_results.tex`
- `docs/manuscript/ch09_discussion.tex`
- `docs/ver2_upgrade/VER2_PHASE_PROMPTS_05_PRELIMINARY_RESULTS.md`
- `docs/ver2_upgrade/NEXT_SESSION_PROMPT_VER2.md`

## Purpose

Re-anchor the next development stage around the actual research goal in the
manuscript, not around maximal exactness-by-default.

## Manuscript readout

### From `ch01_introduction.tex`

- the central question is not “build a universal exact solver first”
- it is “how large is the departure from FLRW, and what does it constrain?”
- the current principal result is tilt-compatible anomaly support under an
  assumption-explicit low-`\ell` framework
- geometry/source identifiability remains blocked

### From `ch06_pipeline.tex`

- BASS owns forward low-order Boltzmann / background / observable production
- HTT owns evidence, posteriors, figures
- MIO owns certification / status classification
- the system is meant to be runnable end-to-end through shared artifacts

### From `ch07_results.tex`

- current results are likelihood/evidence-driven and already framed in bounded
  model-comparison language
- the results chapter does not require every remaining exactness debt to close
  before preliminary output is useful

### From `ch09_discussion.tex`

- the present science target is a CMB-vs-matter and tilt-vs-geometry
  distinction
- the data-honest interpretation explicitly keeps geometry claims blocked unless
  stronger directional observables appear

## Audit conclusion

The correct operating target for the next stage is:

1. make `htt/bass/*` usable as a low-`\ell` preliminary solver,
2. keep HTT/MIO/TSC interop live,
3. keep plotting/export scripts runnable,
4. produce conditional/preliminary result packs,
5. reopen deeper exactness work only when it blocks a concrete preliminary
   claim.

## Process changes adopted

- new prompt document:
  - `docs/ver2_upgrade/VER2_PHASE_PROMPTS_05_PRELIMINARY_RESULTS.md`
- `NEXT_SESSION_PROMPT_VER2.md` now points to that mode first for BASS work
- verification is intentionally lighter in this mode:
  - CoVe
  - metacognitive audit
  - equation-to-code consistency against the SDD
  - touched-surface tests
  - script/export `--check` when relevant
- plot-based visual audit is no longer mandatory unless the touched step is
  itself figure/export work or a numerical mismatch remains unresolved

## Explicit non-goals

- this mode does **not** downgrade claim ceilings silently
- this mode does **not** promote blocked geometry claims
- this mode does **not** declare non-Type-I exact closure done
- this mode does **not** prioritize legacy cleanup ahead of preliminary results
