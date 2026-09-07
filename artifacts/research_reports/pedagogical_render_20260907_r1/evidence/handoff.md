# Pedagogical Report A — assemble, check and render the already authored exposition

Date: 2026-09-07
Route: MAIN conversation <-> Local Codex; direct Git return
Work unit: HTT_REPORT_A_PEDAGOGICAL_ASSEMBLY_VERIFY_RENDER

## 1. The requested artifact

The owner requested an external-facing, introductory and pedagogical account, following the supplied earlier report and stylometric guidelines, with definitions, propositions and proofs understandable without consulting private reports or repository records. MAIN has written six source parts containing Sections 1–13 and Appendices A–E. This is not a request for Local Codex to design or write the missing chapters.

New manuscript branch:
`docs/htt-report-a-pedagogical-20260907-r1` in `cosmosapjw-quantum/htt_base`.

Source directory:
`docs/research_reports/pedagogical_20260907/`.

The branch was created from the accepted report coordination snapshot `d2ed5bc628486859e7d58ef75037f84dc643c0c8`. That ancestor does NOT contain the new exposition. Read the actual current handoff and chapter files, resolve them to a complete immutable commit before execution, and record the actual source commit/tree and input file identities. Do not pretend that an old source pin includes later text.

The first five chapter files were already present at `13c4c33c7eae99bbbe1f7ccb1d7b04d460f47a99`. The sixth radiation-model appendix, assembly program, rational checker, README and this instruction were added later. Use the complete new branch state, not just the five-part historical snapshot. If a matching local or remote task/result already exists, read and reuse it rather than starting a competing writer.

Deliver a single integrated Markdown document, one external-facing PDF, standalone TeX and the fixed bibliography, plus a separate concise build/review return record. Do not distribute a set of incomplete chapter pointers as the final reader artifact.

## 2. Source and scope

Read these complete files before running:

- 01_FOUNDATIONS_AND_THE_SKY.md
- 02_ORBITS_PHYSICAL_STATE_AND_MES.md
- 03_INFERENCE_RANDOMISATION_AND_OBSERVER_RESPONSE.md
- 04_MASKS_NUISANCE_AND_NUMERICAL_ERROR.md
- 05_APPENDICES_CERTIFICATES_AND_FIBRES.md
- 06_RADIATION_MODEL_AND_MES_DERIVATION.md
- assemble_edition.py
- check_axial_certificate.py
- README.md

The source is an expansion of the accepted R3, not a replacement of its evidence history. The retained bibliography is `docs/research_reports/final_candidate_20260907/HTT_REPORT_A_REFERENCES.bib`, blob `331c557c0f6a7de84fdd97123d8bdb8fae0e0a53`.

A key addition is the internal radiation appendix. It derives sufficient first-order shear/vorticity bounds from a specified collisionless geodesic brightness model, angular moments, commutators and derivative envelopes. The double-prime quadrupole envelope explicitly controls a contracted differentiated divergence. It is NOT silently identified with an uncontracted Hessian norm, and weak assumptions do not imply strict conclusions. The appendix does not claim the most general nonlinear Einstein–Liouville almost-isotropy theorem or an observational determination of its hypotheses. Preserve these distinctions.

The assembly program supplies final, already-authored replacement paragraphs that connect the earlier five parts to this new appendix and remove obsolete statements that the relevant derivation was left outside the exposition. It does not change original R3. If a literal source anchor is mismatched, correct only the mechanical selection to the actual intended paragraph, preserve the complete authored replacement, and record the correction. Do not remove unrelated caveats or silently rewrite a physical assumption to make the assembly pass.

The book also internalises the existing fibre/Hausdorff companion mathematics and the axial continuum rank certificate. That inclusion is requested exposition, not a new canonical claim map or retrospective extension of the old R2 four-lemma proof.

## 3. Editorial contract

The paper itself is in English. Its reader starts with basic calculus, matrix multiplication and elementary probability, not prior knowledge of covariant cosmology, STF tensors, invariant theory or partial identification. Retain the sequence motivation -> definition -> worked example -> proposition -> proof -> interpretation.

Use the author's direct explanatory voice: inclusive 'we' for steps actually performed in the argument; 'one' for hypothetical constructions; short transition sentences before nontrivial derivations; ordinary, precise academic English rather than promotional or bureaucratic prose. Explain a symbol before using it. Let each displayed equation connect to the surrounding grammatical argument. Do not imitate accidental errors from an example corpus, replace mathematics with motivational prose, or repeatedly announce that a claim is 'not a certificate'.

Do not put internal PR numbers, source hashes, workflow state labels, test dashboards, canonical ledger bookkeeping or long tool-failure histories into the scientific body. Place build provenance in RETURN_TO_MAIN and the machine-readable receipt. References are for attribution/further reading; the proofs and exact certificate needed to follow the asserted results are in the paper.

The user's original example report and three private style files are not authorised for repository publication. They must not be copied into a public source or evidence bundle. No font binaries or installed mathematics packages are to be published.

## 4. Native work only

Use a clean isolated worktree and a new output directory outside the user's original checkout. The local process is the sole writer of its candidate while running. Preserve dirty work, data, environments, earlier PDFs and accepted evidence. Use an existing Python and Pandoc/TeX/PDF environment; no package census, Rust/Docker/Wolfram reinstall, old CAS rerun or host reconstruction.

This document build has no mandatory CPython 3.12 requirement. Record the actual installed versions. Planning allowances may be adjusted with concrete progress, old/new allowance and cumulative accounting, as requested by the owner. Do not convert an earlier workflow timeout into a universal hard budget. Explicit owner hard limits, platform limits, new paid/privileged actions and separately preregistered experimental budgets remain distinct.

MAIN has not demonstrated a successful native run of the new assembly program, rational checker or renderer. Preserve the first real failure if encountered. Fix ordinary in-scope programming, mechanical source-selection, cross-reference or layout defects and continue to a verified result without asking for approval at each edit. A genuine change to protected scientific meaning is not a formatting fix: return its exact location and derivation discrepancy, not a forced PASS.

## 5. Required source and mathematical correspondence checks

Resolve REPO, PY and OUT to actual absolute paths. Freeze the actual chapter state before a recorded final run. Begin with syntax and inspect the two small helper programs; they are document-specific, not new repository-wide validators.

Run `assemble_edition.py` using an empty output directory and the fixed bibliography. Retain its source identities and editorial replacement record. Its expected structure is Sections 1–13, Appendices A–E and one final References heading. If a heading spelling differs from an expected selector, preserve the intended complete content and correct the selector, not the book's scientific argument.

Read the assembled text, including the end of each chapter, to ensure no duplicate or contradictory 'missing proof' paragraphs survive after Appendix E. Distinguish an explicitly assumed physical model from a theorem whose proof is merely missing. A sentence may properly say the general nonlinear theorem is outside scope; it must not say that an internally claimed sufficient first-order bound still requires an external proof.

Check notation and equation references mechanically and by reading: the physical velocity versus observable contraction vector, geometric versus inverse-time rates and c, full tensor vorticity norm versus axial-vector norm, temperature versus radiation energy moments, the two derivative-envelope meanings, strict versus weak bounds, and the finite continuum versus finite-pixel distinction. The first-order model in Appendix E is a sufficient explicit branch, not a new equivalence claim with every version of the original MES hypotheses.

Read all proof dependency links. In particular, verify that projection/least-squares, SVD perturbation, Cholesky, angular integrals, STF normalisations, Krylov reconstruction, finite-rank lemmas, randomisation arguments, the boost-response factor of three and projector-gap lemma do not invoke an unproved project-specific result. Basic real arithmetic, differentiation, integration and the stated physical equations are premises, not hidden empirical facts.

Use `check_axial_certificate.py` for the newly printed finite rational certificate. It evaluates the Appendix-B polynomial formulae using Fraction arithmetic only. Preserve the actual normal determinants, minor squares and comparison results. It must not compare an old PASS string to another PASS string. If a mismatch occurs, investigate the actual printed polynomial, normalisation and selected source columns against the retained exact certificate before changing anything. A valid alternate normalisation is not byte identity and must be explained, not silently substituted. No finite-HEALPix rank or numerical-error coverage is certified by this computation.

The checker contains simple arithmetic controls and expected fractions copied from the retained exact certificate. Test sensitivity by changing one selected expected numerator in memory or a temporary fixture and confirming that the comparison reports NONPASS; do not modify the archived source/certificate. Report this as a checker test, not another physical result. The exact certificate calculation is a bounded check of new exposition, not a repeated whole research-harness audit.

For Appendix E, check the displayed angular-moment contractions and coefficients in the stated first-order model. The quadrupole streaming coefficient is two fifths; the coefficient five in the conventional shear estimate is an explicitly conservative weakening, not that streaming coefficient. The vorticity estimate must preserve the specified contracted derivative control. Do not silently claim that a general uncontracted derivative norm has operator factor one. Keep the distinction between a proof inside the linearised system and a rigorous finite-amplitude nonlinear error bound.

Check every cited key and bibliography entry. Use the fixed list; do not rewrite author names, dates or citation metadata from a search-engine snippet. A source reference may remain as historical attribution, but it cannot stand in for a missing proof claimed by this paper. Do not force an arbitrary citation count merely to match R3 if the new exposition legitimately cites a subset; report actual used and unused keys separately.

## 6. Render and inspect the single complete document

Use the assembled single Markdown and bibliography, not the old R3 Pandoc defaults or PDF. The title is 'From a CMB Sky Map to Physical Constraints'; the subtitle is 'An introductory account of tensor morphology, kinematical bounds and response-limited inference'. Include Jiwon Park as author, English/UK metadata and an ordinary date/version. Do not fill the cover with internal validation status.

Adapt a run-local Lua filter to the actual hierarchy: Parts introduce thematic divisions; numbered main-section headings map to sections; numbered subsections map to subsections; Appendix A begins a single appendix transition and Appendices A–E map to the five lettered sections. Appendix subheadings remain subsections. The Abstract and reading guide are unnumbered; References is unnumbered and unique. Remove manual heading-number prefixes only when LaTeX supplies the same numbering. Explicit mathematical tags must not be duplicated or lost.

Use a table of contents and comfortable reading margins. Do not force the old 29-page count, reduce font size globally to hit a target, omit proofs, or move essential definitions into an external source. Large exact integers may be laid out on multiple clearly indicated lines with no inserted digits or hyphens. Their source strings and reconstructed values must remain unchanged. Keep body mathematics and tables legible; allow page count to reflect the new self-contained exposition.

Compile the actual TeX/PDF, preserve raw stdout/stderr/exit and corrections, and inspect every page through rasterised page images. Check nested headings, proof endings, long equations and rational certificates, inline symbols, citations, table boundaries, signs, indices, clipped lines and cross-page text. Re-view pages affected by a layout change; reuse unchanged page views only when backed by an actual image comparison. Report actual page count and viewed/unviewed pages. Do not call text extraction alone visual inspection.

The previous accepted R3 is not the requested new artifact and must not be renamed as such. Do not rerun its old 55/80/28/90 suites or R2 as prerequisites. A new computation needed to validate a new printed proof is identified separately and does not retroactively alter old evidence grades.

## 7. Direct Git return and completion

Create one isolated child branch from the resolved complete pedagogical source snapshot, for example `docs/htt-pedagogical-render-20260907-r1`. Non-force push actual source corrections and the resulting small PDF/TeX, assembled Markdown/bibliography, layout adapters, compact source/proof checks, raw relevant logs, PAGE_REVIEW and RETURN_TO_MAIN. Create a Draft PR targeting `docs/htt-report-a-pedagogical-20260907-r1` when possible. Do not move another writer's source branch, merge, mark ready or alter canonical claims.

The user should return only immutable Git links; a ZIP is optional backup, not the only container of decisive evidence. Keep private corpus/style files, credentials, fonts and installed environments out of the commit. Reference rather than duplicate unrelated historical evidence. The scientific paper must remain readable by itself; its build/debug record belongs alongside it, not inside its argument.

Read back the remote commit and the decisive source/PDF/receipt files and record actual coverage. The local source-under-test identity, artifact candidate and final publication may differ; record each honestly. A failed publication does not erase a completed render; a produced PDF does not erase a failed proof comparison. Do not announce external-reader readiness until the declared source/proof/citation/layout checks actually succeed.

Return the actual source and publication commit/tree, PDF/TeX/assembled Markdown URLs, proof and source check outcomes including the explicit MES-model scope, any corrections, final page count/all-page review, bibliography status, raw command exits, and the exact remaining issue if NONPASS. No new WORK_THREAD or routine approval round trip is required. MAIN will read the real return and assess the artifact, not accept a self-certified reviewer label.
