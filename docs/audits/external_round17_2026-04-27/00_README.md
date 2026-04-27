# BASS Phase-1 Closure — External Audit Bundle (Round-17)
**Date assembled:** 2026-04-27.   **Repo commit:** `02cb6c0` (`main` branch).
**Subject:** the 6.43× linear-probe `D_2` residual against the Rust MB-95 anchor `D_2 = 1002.086744 μK²`.

This bundle is **self-contained**: an external auditor with no prior context on the project should be able to read the documents, navigate the cited code, reproduce the measurement, and deliver an opinion without needing to clone the full repository.

---

## Read order

1. `02_AUDIT_FOCUSED_SUMMARY.md` (~15 min) — start here. Compressed problem statement, history, what's been tried, plan, blockers, the questions we want answered.
2. `03_AUDIT_PROMPT.md` (~5 min) — the formal audit prompt (English + Korean). If you are an LLM, this is what your invoking agent likely passed you.
3. `01_DETAILED_ANALYSIS.md` (~30–40 min) — full self-contained technical analysis. Physics, code-internal algorithms, conditional behavior, forbidden moves, reproduction.
4. `code/` (selective) — open source files cited by §-references in the docs above.
5. `reference_docs/` (selective) — pull when the focused brief cites a prior investigation.

---

## Bundle layout

```
external_round17_2026-04-27/
├── 00_README.md                           — this file
├── 01_DETAILED_ANALYSIS.md                — ~25 KB self-contained technical analysis
├── 02_AUDIT_FOCUSED_SUMMARY.md            — 15-min audit brief
├── 03_AUDIT_PROMPT.md                     — the prompt to send to an external auditor
│
├── code/                                  — 7 source files, all in scope for the analysis
│   ├── flrw_pipeline.py                   — (1338 LoC) entry points: compute_flrw_d_ell + compute_flrw_d_ell_linear_probe
│   ├── cl_assembly.py                     — ( 837 LoC) C_ℓ assembly + Planck-2018 P_R(k) wiring
│   ├── regular_adiabatic_ic.py            — ( 425 LoC) _seed_formulae — D-2 source code
│   ├── los_grid_builder.py                — ( 184 LoC) Round-15 P0 D-1 fix (LoS grid decoupling)
│   ├── integrator.py                      — ( 742 LoC) IMEX + conditional inline DAE-relaxation (lines 434–498)
│   ├── test_d2_pstf_closure.py            — ( 105 LoC) the closure regression test (xfail)
│   └── v5_round17_linear_probe_measurement.py  — (148 LoC) reproduction script (31 min wall time on 4 workers)
│
└── reference_docs/                        — 7 internal investigation docs
    ├── V5_ROUND17_PR_S13_REAL_SCOPE.md            — current scope ticket (this round)
    ├── V5_ROUND17_NEXT_SESSION_OPENER.md          — bootstrap doc for fresh sessions
    ├── V5_ROUND12_TO_14_INVESTIGATION_SUMMARY.md  — three-defect 10-auditor consensus (D-1 / D-2 / D-3)
    ├── V5_ROUND9_FINDINGS.md                       — linear-probe origins + ν seed bug-fix
    ├── V5_ROUND15_P0_D1_FIX_SUMMARY.md             — D-1 closure record (2026-04-25)
    ├── V5_RUNTIME_TRACK_DIAGNOSIS.md               — IMEX stability closure (Blockers 1+2; 8 algebraic patches)
    └── CHANGELOG_excerpts.md                       — Round-16 P2 + Round-17 P2 entries
```

---

## Conventions used in this bundle

- **File-path-and-line-number citations**: `code/regular_adiabatic_ic.py:142–186` means lines 142 to 186 inclusive. All paths in `code/` and `reference_docs/` are relative to the bundle root.
- **Internal repo paths** (in the analysis docs): paths like `htt/bass/spectrum/flrw_pipeline.py:1136` refer to the location in the *full repository*. The bundle's `code/` directory contains a subset of these files at flat names. To navigate from a bundle citation to the full-repo path, see the path index at the end of `01_DETAILED_ANALYSIS.md` Appendix C.
- **Audit verdicts**: prior cycles use the labels `CONFIRMED`, `PARTIALLY-CONFIRMED`, `REFUTED`, with a confidence note and concrete counter-test. Please match this convention.

---

## What this audit is NOT asking for

- **Not** a re-derivation of the linear Boltzmann-Einstein hierarchy. We have R7-authoritative `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md` (not included; see repo) and the standard Lewis-Challinor / Ma-Bertschinger / Ellis-van Elst literature for that.
- **Not** a code review of the entire pipeline. We are asking specifically about the 6.43× residual diagnosis and the proposed closure path.
- **Not** a HYBRID-architecture proposal (using CAMB transfer functions in production for FLRW). That option was 4/4-recommended by Round-14 auditors and explicitly user-rejected on 2026-04-25; the production code must remain self-contained without external CAMB runtime dependency.

---

## Reproducing the 6.43× measurement (requires full repo, not bundle)

```bash
# Prerequisites: git clone the BASS repo, set up venv with Python 3.11
# numpy + scipy + numba + sympy. The bundle's code/v5_round17_linear_probe_measurement.py
# is provided for reference; running it requires the full repo.

cd /path/to/bass-htt-base
venv/bin/python scripts/v5_round17_linear_probe_measurement.py

# Expected output line: "D_2 (Python linear-probe): 6.439500e+03 μK²"
# Wall time: ~31 minutes on 4-worker baseline (130 solver tasks → 33 rounds).
# Run on commit 02cb6c0 (or any later commit; bit-stable across recent history).
```

---

## Materials NOT included (deliberately) — but cited

- The full Rust path `bass_rs/src/sync_gauge_camb.rs` (7363 lines). Cited only as "the path that produces the anchor"; auditor does not need to inspect it for this audit.
- `htt/bass/los/test_flrw_bessel_projector.py` (large; the regression-armor test for the Doppler `/k` ban is referenced at `02_AUDIT_FOCUSED_SUMMARY.md §3` but its content is not load-bearing for the open question).
- `htt/bass/spectrum/tier_b_source_extraction.py` (D-3 territory, parked).
- `docs/V5_ROUND15_P1_PSTF_DERIVATION_OPUS.md` (R7-authoritative tetrad-PSTF derivation; available in repo if needed).
- `docs/SSOT_POLICY.md` (Π_BASS / polter convention; available in repo).
- The full `CHANGELOG.md` (only the Round-16 P2 and Round-17 P2 entries are excerpted).

If the auditor finds that a missing item would be load-bearing for the verdict, please flag it and we will provide.

---

## Prior audit precedent

This is **the second formal external audit cycle** for BASS Phase-1 closure work. The first cycle was Round-12-to-14 (2026-04-25): 10 external auditor verdicts across three rounds, archived at `docs/audits/external_round12_to_14_2026-04-25/`. Verdict files there follow the convention `roundN_auditNN_<provider>.md`:

```
round13_audit01_gpt55.md     — GPT-5.5 Thinking,  PARTIALLY-CONFIRMED
round13_audit02_codex.md     — Codex,             PARTIALLY-CONFIRMED  
round13_audit03_opus.md      — Claude Opus,       REFUTED (most precise on Option A)
round14_audit01_codex.md     — Codex GPT-5,       HYBRID-RECOMMENDED
round14_audit02_opus.md      — Claude Opus 4.7,   HYBRID-RECOMMENDED
round14_audit03_gpt55.md     — GPT-5.5 Thinking,  HYBRID-RECOMMENDED
round14_audit04_opus.md      — Claude Opus 4.7,   HYBRID-RECOMMENDED (most detailed; D-1/D-2/D-3 enumeration)
```

This Round-17 audit is asking the same questions on the post-Round-15-P0 / post-Round-16 / post-Round-17-P2 codebase; the residual has dropped from 7.57 × 10² to 6.43 since the prior cycle, and the diagnosis has narrowed from "three independent defects" to "D-2 dominant, D-3 parked".

---

## Bundle assembly notes (for the human)

This bundle was assembled programmatically on 2026-04-27 from commit `02cb6c0`. Mechanical steps to re-assemble or refresh:

```bash
# From repo root:
mkdir -p docs/audits/external_round17_$(date +%F)/{code,reference_docs}
# (then populate per the layout in 00_README.md)
cd docs/audits/external_round17_$(date +%F)
zip -r ../audit_round17_$(date +%F).zip . -x "*.zip"
```

The bundle is **idempotent** with respect to commit hash — re-running the assembly script on the same commit produces a byte-identical zip (modulo timestamps). For full reproducibility, also archive the commit hash and `git status` snapshot.
