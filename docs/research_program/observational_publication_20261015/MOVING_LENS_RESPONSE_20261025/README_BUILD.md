# Moving-lens supplement: build and provenance

Prepared 25 October 2026. Owner: htt. Scope: standalone external-reader English translation of the reviewed response-domain and estimator-differential argument; non-claim-bearing C0, CONDITIONAL. Transfer source: empirical_proxy; no native transfer. This supplement does not modify or rebuild the existing full report. Publication and scientific admission are not authorized by this preparation; fresh independent review of this supplement is pending.

## Build status

SUCCESS: REVTeX4-2, APS/PRD, single-column reprint layout, five pages. Entrypoint: `main.tex`; output: `main.pdf`. Bibliography is inline (`thebibliography`), using primary links and arXiv version identifiers already inspected in the source intake/review. No BibTeX file, figures, included chapters, external image files or numerical implementation is used. No new primary-source search, numerical run or CAS verification occurred.

Commands (from this directory):

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > build.stdout.log 2>&1
pdftotext -layout main.pdf main.extracted.txt
pdftoppm -f 1 -singlefile -scale-to 1300 -png main.pdf preview_page1
pdftoppm -f 2 -l 5 -scale-to 1100 -png main.pdf preview
```

Final build exit status: 0. Retained logs: `build.stdout.log`, `main.log`, `preview_render.log`. Scan result: no undefined references/citations, missing files, duplicate labels, overfull or underfull boxes. One warning remains: `Package nameref Warning: The definition of \\label has changed!` (REVTeX/hyperref interaction); it is reported rather than suppressed. Rendered pages were inspected for title, equations and bibliography. An initial preprint layout separated the title; the final single-column reprint layout brings title and abstract together.

## Exact source binding

- Revised derivation: `/mnt/extdrive/workdir/htt_open_data/r29_nonradial_moving_lens_intake/REPORT_REVISED.md`; SHA256 `0f66033f7f4adc86c214c45ca479e557de1ede447c1b48afedae2752d505ce2d`.
- Independent targeted closeout: `/mnt/extdrive/workdir/htt_open_data/r29_moving_lens_source_independent_review/CLOSEOUT.md`; SHA256 `63b357cb8db379d478c709b3274aa54eaa33228ede97f6a66c6c55e1901ba1cb`; SCOPED_PASS closes F1/F2 text corrections only. Source-specific physical-response HOLD remains.
- Original report, unchanged: SHA256 `52c4a64e6013ab9ed9ebec4b19787fd2d09322f49e980e0099f77882610f6126`.
- Original independent review, unchanged: SHA256 `b3d771aadb12e9039396f0c97032239eb18a309ccc05e478d1945784eedd12e7`.
- Independent source audit: `/mnt/extdrive/workdir/htt_open_data/r29_moving_lens_source_independent_review/SOURCE_AUDIT.json`; exact seal in `IMPLEMENTATION_RETURN.json`.

The source's author-revision preamble predates its closeout. This supplement uses the closeout binding above, without changing either input. Bibliographic author names are limited to those explicitly supplied by these inputs; arXiv identifiers stand in place of unverified journal metadata.

Initial repository identity (read-only): `/home/cosmosapjw/Dropbox/bianchi/htt_base`, branch `research/htt-adaptive-methods-20261023`, HEAD `d93605e66adfececa89b90681124b232a5f90220`, origin `https://github.com/cosmosapjw-quantum/htt_base.git`. Existing tracked and untracked changes were present. This worker wrote only this new external directory, performed no Git mutation and created no checkout or subagent. Requested model/effort: gpt-6.1-sol/medium; observed identity: UNKNOWN / NOT_INDEPENDENTLY_OBSERVED. Free space was over 2 TiB, exceeding the 2 GiB reserve.

Writing guidance: my-writing-style research v4 and its WRITING_PROTOCOL_V4, repository htt-latex-paper-build, htt-claim-firewall and htt-claim-provenance-ledger. Guidance is not a scientific or review oracle.

## Claim audit

| Content | Status | Evidence and ceiling |
|---|---|---|
| Coherent translation and scale separation | DERIVED, CONDITIONAL | Reviewed source; not unrestricted local matter advection |
| Poisson--continuity sinusoidal snapshot | DERIVED, CONDITIONAL | Exact reviewed coefficient ratio; no numerical execution/global solution |
| Fitted amplitude differential | DERIVED, CONDITIONAL | Full data/template/covariance derivative; no survey physical-rank measurement |
| Angular curl and parity | CONDITIONAL operator distinctions | Reconstruction, temperature and cross-mean kept distinct |
| Signed E/B and tensor interpretation | NOT_EVALUABLE | Missing qualified response, state, calibration, physical null/selection law and complete covariance |

No claim was upgraded. No numerical or cosmological no-go claim was introduced. No claim ledger, repository status or controller state was edited. The supplement's final independent review is the next decision; this worker cannot self-approve or publish.

## Source package

`source_bundle.zip` contains only `main.tex` and this README. Inline references make the TeX entrypoint self-contained with installed REVTeX/standard packages. PDF, build auxiliaries, logs, previews, extraction and return metadata are retained outside the source archive. `IMPLEMENTATION_RETURN.json` records input and output SHA256 identities, commands, build scan and pending-review status; it does not hash itself.
