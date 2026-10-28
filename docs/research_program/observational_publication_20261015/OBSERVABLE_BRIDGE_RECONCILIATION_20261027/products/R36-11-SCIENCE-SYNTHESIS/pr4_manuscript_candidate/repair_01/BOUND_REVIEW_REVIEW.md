# SCOPED_CODE_REVIEW — preparatory repair required

Reviewed preparation manifest: `e08b2523083a5b7bb9ddf45c18cc32967d2425b8e50e722af2ae4210949833c4`.
Reviewed `assemble.py`: `626f80c691ed95916c097932311a960379238483ad945891e853341529ac886d`.
Repository HEAD: `bdead6a8f51282ca647224b460b0f65de085568b`.
Requested reviewer: `gpt-6-astra/xhigh`; observed runtime: `UNKNOWN`.

Scope is source-level cached-consumer preparation only. All executed numerical/build fixtures are labelled `SYNTHETIC_UNIT_FIXTURE`; no actual MC result, FITS read, producer, network, STATE, Git, or production mutation occurred. No actual source/scientific qualification is issued.

## F1 — P2: required lossless numerical supplement is not checked

Location: candidate `assemble.py`, `check_rendered_products`, lines 286–294; generation occurs at lines 282–284. The identically sealed prepared `pr4_morphology_supplement/assemble.py` has the same defect.

`--check` validates TeX numbers/tables, CSV, figure files, citations and `NUMBER_FIGURE_MAP.json`, but never reads `NUMERICAL_SUPPLEMENT.json`. In an otherwise passing explicitly synthetic rendered fixture, removing the supplement returns `True`. Restoring it and replacing the observed `B_l2_l3_l4_full_signed_m` map with `{}` also returns `True`.

The supplement is the required complete lossless carrier of all 101 rows, signed E/B, response columns, metadata and receipts. A successful output check can therefore accompany a missing carrier or a scientifically incomplete carrier; the flat CSV cannot replace it.

Minimal reproduction: run `probe_rendered_consumption.py`; see `RENDERED_CONSUMPTION_PROBE.json` keys `missing_numerical_supplement_accepted=true` and `lost_observed_B_coefficients_accepted=true`.

Bounded repair: factor the existing expected supplement object into one small builder used by rendering and checking. Require the file and compare its full lossless content with the current validated context: all source/result and selected-observed rows with signed E/B, complete response, raw input inventory, source scope, source candidate identity, export index, and copied source receipts. Preserve the explicitly synthetic fixture format separately if needed. Add missing-file, signed-B deletion, response mutation and current-binding mutation negatives. No new science schema or acceptance gate is needed.

## F2 — P1: output check accepts a PDF from an older assembled source

Location: candidate `assemble.py`, lines 278–285 and `check_rendered_products` lines 295–297. Existing PDF validation checks only that a log exists, its diagnostics are clean and PDF text lacks `??`; it does not establish that the PDF consumed current generated inputs.

Minimal reproduced sequence:

1. Assemble and successfully build the labelled synthetic fixture: observed `T=0.2`, `k=54`, `p_rank=0.544554455446`.
2. Change the synthetic observed row to `T=0.6`, recompute the synthetic rank (`k=0`, `p_rank=1/101`), and reassemble generated sources and figures without rebuilding the PDF.
3. Run `check_rendered_products` against the new context. It returns `True`, although `main.pdf` is byte-unchanged and still reports `T=0.2`, `k=54` and the old rank.

This permits the final check to report success for a manuscript PDF containing numbers from a different source context. The defect is dependency consumption, not a metadata-only PDF byte difference.

Evidence: `RENDERED_CONSUMPTION_PROBE.json`, `rendered_consumption_first.log`, successful `synthetic_build_first.log`, and `synthetic_pdf_before.layout.txt` lines 103–105 and 133–134. The stale PDF and new generated inputs remain under `rendered_probe/`.

Bounded repair: distinguish pre-build assembled readiness from post-build verification. After reassembly, a PDF may count as current only when a successful current build consumed the exact current TeX/numerical/table/figure/bibliography inputs. Reuse existing LaTeX dependency/build evidence or run a bounded forced build before a post-build PASS; verify the resulting numerical text/content against the current assembled values. A stale PDF must fail or remain explicitly unverified, while byte-identical input regeneration and PDF metadata-only variation remain allowed. Preserve the old PDF/first failure as evidence. Add the .2-to-.6 regression, then force a real synthetic rebuild and verify current numbers are consumed. Do not add a general governance receipt/schema.

## Passing coverage and limits

- All 43 preparation-manifest files and the editor/clarification/author-return identities match supplied hashes.
- Supplied suite: 36 passed.
- Independent suite: 8 passed, covering all 101 CP counts via independent binomial-tail equations, inclusive tie endpoints, distinct source/review packet handling, candidate/export identity mismatch, exact manifest bytes, payload byte-copy mismatch, relocation with unchanged payload preimages, independent reviewer identity, optional nonempty-findings pending behavior, full 42-by-3 signed response coordinates and missing actual qualification.
- Actual pending binding exits 3 before assembly. Guarded TeX exits 12 with `PENDING_SOURCE_QUALIFICATION` and no PDF.
- Synthetic TeX build succeeds. The two output-consumption defects above remain unrepaired.
- `prepare.py` and `finalize_preparation.py` received static inspection. The finalizer was not executed because its destination is the protected repository candidate. No production/source edits were made.
- Nonempty actual reviewer findings remain a pending adapter until the real structured format exists; this is not a finding. Unknown Commander effective beam does not stop the stipulated conditional computation.
- Complete actual MC100 source, actual fresh formal scientific qualification, actual paper build and independent final manuscript review remain pending.

Decision: preparatory consumer code needs the two bounded fixes before code eligibility. This review is not final science or manuscript qualification.
