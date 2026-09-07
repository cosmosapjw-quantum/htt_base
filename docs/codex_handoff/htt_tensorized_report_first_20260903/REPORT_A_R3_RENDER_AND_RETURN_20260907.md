# Report A revision 3 — source reconciliation checks, native render and direct Git return

Date: 2026-09-07
Work unit: HTT_REPORT_A_R3_RENDER_AND_RETURN
Scope: render the complete manuscript already authored by MAIN, not another research plan or implementation replay. No WORK_THREAD is required.

## Objective and inputs

MAIN has assembled the full evidence-integrated theory-and-methods edition, retaining twelve core sections and forty candidate identities and adding the reviewed execution scopes. Produce its actual review PDF and TeX, inspect the pages, publish the actual source/build evidence and return immutable Git links. This source edition is not yet a rendered or publication-approved release.

Repository: `cosmosapjw-quantum/htt_base`.
Source snapshot: `c105c1456e2de919f0927adb12995cfeb0357f9c`.
Report branch: `docs/htt-tensorized-mes-response-synthesis-20260903` (PR449).
The snapshot is the input identity, not a claim that this remains the live head. Read any same-task branch/worktree first and reuse a matching active or completed result; do not start a competing writer.

| Input at the source snapshot | Git blob |
|---|---|
| `docs/research_reports/final_candidate_20260907/HTT_REPORT_A_EVIDENCE_INTEGRATED_R3.md` | `e8566be7c8095c38befdbbdbe7851f9502510753` |
| `docs/research_reports/final_candidate_20260907/HTT_REPORT_A_REFERENCES.bib` | `331c557c0f6a7de84fdd97123d8bdb8fae0e0a53` |
| `docs/research_reports/report_a/structure.lua` | `afaf143126319a864b7f08790348db20963d55d2` |
| `docs/research_reports/report_a/header.tex` | `21102ea9ae0a117fc921189884916226c13d5aae` |

The bibliography copy was read back by MAIN and has the SAME Git blob as the compiled twenty-entry K2FR bibliography. Do not reconstruct or update references from search-engine metadata.

Scientific predecessor for the content comparison:
`docs/research_reports/drafts/HTT_REPORT_A_FULL_KINEMATICAL_MES_DRAFT_K3_20260905.md`, blob `99a3f75c67ece3cfb00179bfd61787f47cb7e7ac`, available at the source snapshot.

Core ID comparison: `artifacts/research_reports/k2fr_20260905/authority-bundle/REPORT_SECTION_CLAIM_MAP_V3.csv` at `581d50cb8b8be61ca8ead538d0bf7d75420f9037`, blob `1478f55c074ec0aeb62a8680a5e7fc76849b89c4`. Read the fixed file through existing Git, not a fabricated manifest. Thirty retained identities include four revised statements; ten additional candidates bring the total to forty. Do not count forty as forty new claims or add test counts to claim counts.

Read AGENTS.md and the applicable repository claim/build skills. If available locally, read `/home/oai/skills/pdfs/SKILL.md`; do not claim to have read an absent skill. Use the installed working Pandoc/TeX/PDF environment rather than a mathematics-package census. The old K5 handoff is a rendering precedent, not the active three-thread/no-push/two-edit restriction.

## Work to perform

Use an isolated child worktree and a new external build directory; preserve the user's original checkout, venv, data, earlier PDF and all accepted execution evidence. No reset/clean of unrelated work. No CPython 3.12 or Lean requirement is imposed on this document-only renderer; record the actual versions used. A hosted CI failure is not a reason to stop an available local build or to retry old workflows.

First check the assembled source, without rerunning science:

- Compare the displayed mathematical expressions in core Sections 1–12 with revision 2. The intended changes are prose/evidence scope, not coefficients, signs, equations, domains or inherited numerical values. Compare parsed math tokens, allowing only harmless ASCII whitespace changes; do not globally lowercase, strip macros, replace symbols or erase control characters. Report the actual comparison, not an expected PASS.
- Confirm twelve main sections, Appendices A–D, exactly the materialised forty core IDs in Appendix A, and the same twenty bibliography keys with no unresolved citations. Compare the inherited continuum table and the K4 corrections in Sections 5.1, 8.2 and 11.2 explicitly.
- Confirm the new text distinguishes observable contraction v from physical frame velocity, numerical implementation from exact inverse formula, and R2's four obligations from unrelated theorems. Original K2 scope findings stay visible with the separate annex; PR284 remains deferred, finite-HEALPix rank remains unresolved and no observations are added.
- Record the actual source/bibliography hash and a concise change summary. No new permanent validator or new claim ledger is needed. A small run-local check script is sufficient.

A mechanical transcription difference introduced by MAIN may be corrected against the exact predecessor or cited evidence, with a patch and a specific reason, within this task. Preserve all intended new evidence paragraphs. This is not permission to change a theorem, conclusion, tolerance, citation metadata, original ledger or old receipt. A genuinely new mathematical discrepancy is returned as such, not repaired by changing its claim.

Then render the full source. Start from the previously used Pandoc/LaTeX route, not the old 30-claim defaults. In particular, do NOT use `report_a/pandoc.yaml`, old metadata or the old title-specific generated-TeX validator as authority for this edition.

Known adapter difference found by MAIN from source inspection: `structure.lua` subtracts one heading level globally after the abstract. This edition has natural Markdown appendix subheadings such as `## B.1 ...`; they must become appendix SUBSECTIONS, not extra lettered appendices. Make a run-local adapter derived from the existing filter that preserves the proper appendix hierarchy, removes manual appendix-subsection prefixes when automatic numbering supplies them, and makes the final References heading unnumbered and unique. The existing filter also removes the pre-Abstract prologue, so retain the edition and noncanonical review status in PDF metadata/subtitle. This is a layout adaptation, not an observed compiler failure or a scientific-source change.

Suggested metadata:

```yaml
title: Tensorised Low-Multipole CMB Morphology, Kinematical Isotropy Bounds and Response-Limited Identification
subtitle: Evidence-integrated theory-and-methods edition, revision 3 — review candidate; not a canonical release
author: Jiwon Park
date: 2026-09-07
lang: en-GB
documentclass: article
classoption: [11pt, a4paper]
geometry: [margin=25mm]
```

Resolve REPO and OUT to actual absolute paths. Use a run-local `structure-r3.lua` and, where necessary, a formatting-only `header-r3.tex`, preserving their provenance and diffs. The following is a recipe to execute and adapt to actual installed CLI support, not a run performed by MAIN:

```bash
MANUSCRIPT="$REPO/docs/research_reports/final_candidate_20260907/HTT_REPORT_A_EVIDENCE_INTEGRATED_R3.md"
BIB="$REPO/docs/research_reports/final_candidate_20260907/HTT_REPORT_A_REFERENCES.bib"

pandoc "$MANUSCRIPT" \
  --from=markdown+tex_math_single_backslash+raw_tex+citations+fenced_code_blocks+pipe_tables \
  --to=latex --standalone --number-sections --top-level-division=section \
  --lua-filter="$OUT/structure-r3.lua" --citeproc \
  --bibliography="$BIB" --metadata-file="$OUT/metadata.yaml" \
  --include-in-header="$OUT/header-r3.tex" --wrap=preserve \
  --log="$OUT/pandoc.json" --output="$OUT/HTT_REPORT_A_R3.tex"

latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error \
  -outdir="$OUT" "$OUT/HTT_REPORT_A_R3.tex"
```

Use an actually installed alternative engine if necessary, recording the real commands. Capture original stdout/stderr, exit and warnings separately. Do not overwrite old logs, hide failed commands, or call the old K5 PDF this edition. No fixed 24-page requirement: the new evidence appendices may change pagination.

## Inspection and bounded correction

Inspect every produced page using a PDF rasteriser and actual image view, not text extraction alone. Check equations, signs, bars, indices, epsilon/omega conventions, the physical-functionals section, tables, long hashes/links, forty-ID map, twenty references, appendix numbering, one References heading, page breaks, missing glyphs, overlap and clipping. Distinguish warnings judged harmless from unresolved findings. If some pages could not be visually inspected, state exactly which; do not report all-page visual PASS.

Formatting and source-transcription corrections within the above authority may iterate to completion without an approval for each edit. No tolerance relaxation, equation deletion, bibliography removal or omission of a difficult appendix to make the build pass. Recheck after the last relevant edit and preserve prior failures. This is not a rerun of K2FER1, R2, authority, decoder or PR450 extraction.

Use finite subprocess timeouts suitable for the actual tool. Planning allowances are adjustable as requested by the owner: record the reason, old/new allowance and cumulative use when changing one. Do not turn a planning estimate or an old workflow's 15-minute timeout into a universal cap. Explicit owner hard limits, tool/platform limits, new privilege/cost boundaries and preregistered experiments remain protected. Blind repetition without a changed cause is bounded; productive layout fixes are not one-edit-limited.

## Direct Git publication and return

LOCAL_CODEX is the sole writer/publisher of this render candidate. After local review, non-force push one isolated branch, for example `docs/htt-report-a-r3-render-20260907-r1`, based on the source snapshot, and create its own Draft PR targeting the report branch. Do not move existing PR449 or accepted evidence-child refs; MAIN's coordination comments are separate.

Publish a small actual review PDF and generated TeX, the exact rendered Markdown/bibliography or immutable source references, run-local adapter/metadata/header, source-comparison results, raw relevant logs, `PAGE_REVIEW.md` and a concise `RETURN_TO_MAIN.md`/receipt with immutable links. The PDF is the requested document deliverable; publishing it does not assert scientific release approval. Check repository size/policy and the actual binary size first. Do not upload fonts, environments, caches, secrets or unrelated data. A ZIP may be an optional backup, but do not put all decisive evidence only in a ZIP or a local path. Keep necessary textual verification readable through the GitHub connector.

Read back the remote commit and decisive new files, and report actual coverage. A pushed commit with failed Draft-PR creation remains usable via immutable links. If publication is blocked, preserve the actual local PDF/results and the exact blocker. Do not imply a failed upload means failed rendering.

Return: actual source/candidate and publication commit/tree; PDF and TeX URLs; source/diff and bibliography identities; equation/section/claim-ID/citation comparison results; page count and pages actually viewed; raw exit/warning status; correction history; publication readback; and remaining concrete issues. No broad re-audit or additional WORK_THREAD is required. MAIN will read the linked output and make the limited artifact-acceptance decision.

Keep canonical T9 v4/30, candidate forty, original five K2 findings, all prior evidence grades, deferred observation/PR284 and unresolved finite-HEALPix boundaries. Do not merge, mark ready, promote canonical claims, change account billing or run unrelated tasks. The only new native operation is finishing and checking this changed report artifact.

MAIN action record: the complete revision-3 text and identical bibliography copy were written to Git; their publication was read back. The source was manually assembled and remains subject to the mechanical checks above. MAIN's shell and independent Python calls returned ClientError before execution, including the attempt to read the local PDF skill; no new PDF or machine-wide source comparison was produced in MAIN. AWT checked a five-paragraph scope synopsis and SciSpace/primary arXiv abstracts were used for a narrow citation-role check. Neither is a whole-report mathematical certificate. This handoff is not evidence that a local Codex session has been started.
