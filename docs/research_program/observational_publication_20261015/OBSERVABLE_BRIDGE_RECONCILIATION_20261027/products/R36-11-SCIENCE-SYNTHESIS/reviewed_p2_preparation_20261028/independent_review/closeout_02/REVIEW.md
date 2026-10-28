# Same-unit prepared-code closeout: F1 and F2 resolved

Decision: SCOPED_CODE_REVIEW_PASS — eligibility is limited to the prepared cached-consumer code. The candidate remains PREPARED_PENDING_SOURCE_QUALIFICATION. This is not a scientific result, actual manuscript build qualification, publication authorization or final manuscript review.

Current identities independently checked:

- PREPARATION_MANIFEST.json: `a59298455cf9d63e2518834c5c40f59948ac9f3cd1a7e557f88e30ad938ebf4e`.
- assemble.py: `4c2a7dcfce6124d859d3c1d59ed57819ab99fc120237047d7086d738b59fea8a`.
- Author RETURN.json: `d3b25b327f4eadbdf1aea1f4ae2b909fd54c466b7f3e19d19deeb799c139f8a9`.
- All 106 preparation-manifest entries match their hashes and lengths.
- Requested reviewer: `gpt-6-astra/xhigh`; observed runtime: `UNKNOWN`.

AST comparison against closeout_01 confirms that only `verify_current_pdf` changed. It now performs an actual bounded `latexmk -g` build before admitting the PDF as current. The supplement builder/check, row/statistic/CP calculations, export binding and scientific qualification gates are unchanged.

F2 exact residual reproduction and resolution:

1. Build the labelled synthetic T=.6 result and retain the older response PDF.
2. Negate the signed E/B outputs of the second response column, leaving T/k/p and all extracted PDF text unchanged; verify a real current build.
3. Restore the exact older PDF bytes while retaining the current generated sources and real build/dependency records.
4. Invoke the repaired verification path. A new build actually executes before VERIFIED_CURRENT_BUILD.
5. Rasterize response page 4. The rebuilt output differs from the correct current output at zero pixels and differs from the restored old response at 23,119 pixels (510-by-660 page). The old/current extracted text is identical. The actual current figure, not merely the scalar paragraph, was consumed.

F1 remains closed. The targeted signed-B deletion still rejects before any verifier build. Other passing regressions: no-op reassembly; actual metadata-varying PDF rebuild with identical text; actual pending source CLI exits 3 before any verifier build log is created; an intentionally invalid current TeX source causes a real build failure and is rejected before PASS. That intentional failure log is preserved and is not an unresolved defect.

Executed closeout probe exits 0. Six latexmk invocations started: one explicit initial build and five verifier builds, with five successes and one intentional failure. This belongs to the same task/cost history. Existing unchanged 36+8 baseline and closed F1 evidence are reused; no adjacent scientific execution was repeated. The pending TeX/source guard is unchanged by source/AST comparison and retains prior rejection evidence.

Residual findings: none in this targeted code closeout. Verification now intentionally rebuilds an existing PDF before issuing VERIFIED_CURRENT_BUILD and uses the current installed latexmk/TeX tools. Missing actual source qualification continues to stop before that path.

Raw evidence: `CLOSEOUT_PROBE.json`, `closeout_probe_first.log`, `restored_old_pdf_force_build.log`, the old/current/after-verification PDFs and raster images, plus the preserved intentional build-failure log. Every executed fixture is SYNTHETIC_UNIT_FIXTURE; no actual MC numbers or actual-result PDF were created. No source producer, FITS, network, production candidate, Git, STATE, goal or child mutation occurred.

Still required: complete actual fixed100 source; its fresh independent formal scientific qualification and final binding/export; actual manuscript assembly/build; separate fresh independent final manuscript review. Prior findings, first failures and both earlier review packs remain unchanged.
