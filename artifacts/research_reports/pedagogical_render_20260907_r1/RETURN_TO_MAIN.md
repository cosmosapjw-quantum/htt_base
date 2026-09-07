# Return to MAIN — complete pedagogical Report A

STATUS: LOCAL_ASSEMBLY_PROOF_RENDER_COMPLETE_PENDING_MAIN_REVIEW

The new single document contains all six MAIN-authored parts, Sections 1–13, Appendices A–E and all eight full linking replacements. It is a freshly compiled **55-page** PDF; **55 pages viewed, 0 unviewed**. The older 29-page R3 PDF was not reused.

SOURCE_PIN: `f666b244f7061451a6941f5a57aa2d721bbfa81d`, tree `491c67eb44d9bfd0e5b096a17f64ea81d907e157`.

TESTED_SOURCE: `297f7f97af6646f243344812a7e2db6827d942f7`, tree `2dcfe1e0a5347ee36dd389799389c1544cec2840`.

The only manuscript correction restores `\frac1{45}` in Appendix C.14 where a form-feed had replaced backslash-f. Its exact source diff and first real assembly failure are preserved. The renderer also corrects Part/contents page placement, unnumbered link destinations, and two literal STF angle-index expressions on page 50 that Markdown had classified as HTML. Page images prove all other pages unchanged by the last fix; page 50 was re-viewed. Separate run-local checker errors and the initial failed TeX compile remain in the raw evidence.

CHECKS: all 154 displayed math blocks preserved through assembly; all 931 source Math nodes preserved in order in final TeX; 147 unique tags present in TeX/PDF; 20 bibliography keys used and rendered once, 0 unused, 0 unresolved. The bibliography is byte-identical to the fixed source. All 12 actual Fraction certificate comparisons pass, the expected-numerator mutation produces NONPASS, and all 12 printed PDF fractions reconstruct exactly. Proof dependency and Appendix E moment/coefficient inspection found no genuine mathematical inconsistency within the stated premises. This is a bounded document verification, not a new formal or four-axis scientific validation.

MES MODEL SCOPE: the sufficient branch is the explicitly retained first-order geodesic, collisionless thermodynamic radiation model with positive density/expansion and the displayed all-domain derivative envelopes. The quadrupole streaming coefficient is 2/5; five is a conservative weakening in a later norm bound. The double-prime envelope controls the contracted differentiated divergence, with no silent factor-one identification with an uncontracted Hessian. Weak premises give weak bounds unless strict slack is supplied. No general nonlinear Einstein–Liouville, finite-amplitude remainder bound or observational confirmation of the premises is claimed.

FINAL BUILD: native XeLaTeX/latexmk exit 0; no overfull/underfull boxes, missing glyphs or undefined references. Two warnings about unused unicode-math/mathtools bracket and colon macro definitions are retained. [Build record](BUILD.md), [raw command exits](COMMAND_EXITS.json), [source check](evidence/source-check.json), [proof review](evidence/PROOF_REVIEW.md), [final correspondence](evidence/final-render-check.json), [page review](PAGE_REVIEW.md) and [receipt](RENDER_RECEIPT.json) give exact coverage.

NEXT: MAIN reviews this complete artifact. Prior PR450/R2/K2/authority/decoder evidence and the original dirty checkout are preserved. No merge, ready transition, canonical/claim update, private corpus/style file, font binary or installed environment is part of this work.

ARTIFACT_CANDIDATE: `06f90445648db42618a450c25c4e205c3cdd46c7`, tree `b933606e9e1c24706e53af4e629759c5f5f28f6b`.

Publication uses the isolated branch `docs/htt-pedagogical-render-20260907-r1` and [Draft PR #461](https://github.com/cosmosapjw-quantum/htt_base/pull/461), targeting the unchanged MAIN manuscript branch. The immutable commit containing this return is the evidence publication; its exact commit/tree and final readback are supplied in the PR description and final response, avoiding a self-referential Git hash inside its own file.

- [Single PDF](https://github.com/cosmosapjw-quantum/htt_base/blob/06f90445648db42618a450c25c4e205c3cdd46c7/artifacts/research_reports/pedagogical_render_20260907_r1/FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.pdf)
- [Standalone TeX](https://github.com/cosmosapjw-quantum/htt_base/blob/06f90445648db42618a450c25c4e205c3cdd46c7/artifacts/research_reports/pedagogical_render_20260907_r1/FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.tex)
- [Assembled Markdown](https://github.com/cosmosapjw-quantum/htt_base/blob/06f90445648db42618a450c25c4e205c3cdd46c7/artifacts/research_reports/pedagogical_render_20260907_r1/FROM_A_CMB_SKY_MAP_TO_PHYSICAL_CONSTRAINTS.md)
- [All-page review](https://github.com/cosmosapjw-quantum/htt_base/blob/06f90445648db42618a450c25c4e205c3cdd46c7/artifacts/research_reports/pedagogical_render_20260907_r1/PAGE_REVIEW.md)

REMOTE READBACK: all **213** candidate files (203 task artifacts, nine source/helper/README files and the fixed bibliography) matched exact bytes at the pinned candidate commit. The remote tree matched and was not truncated. The PDF, RETURN and receipt also passed Contents API path/ref readback. The full record is [candidate-readback.json](evidence/candidate-readback.json). The subsequent evidence-only publication carries this observed record; its final readback is performed after push.

CI LIMITATION: the three jobs on candidate workflow run 34089298450 did not start. Their actual GitHub annotations report failed account payments or a spending limit. This is infrastructure nonexecution, not a native document-test failure. No old suite was rerun, billing changed, or hosted PASS inferred.

The scoped publication diff check reports only a blank line at EOF in the actual built header. Those built bytes are retained; this whitespace lint is not a layout or mathematical defect. Original checkout default porcelain output still matches the preflight inventory exactly.
