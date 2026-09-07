# Report A publication assembly

This directory defines the deterministic publication assembly for

> *Tensorized Low-Multipole CMB Inference under Conditional Isotropy Bounds and Response-Limited Identifiability*.

## Authority rule

The only editable scientific-prose authority is

```text
../HTT_REPORT_A_THEORY_METHODS_DRAFT_R3_20260904.md
```

The formal bibliography authority is

```text
../HTT_REPORT_A_REFERENCES.bib
```

Files under `build/` are generated outputs. They must not be edited by hand or cited as an independent scientific authority. The quarantined historical source `docs/manuscript/main.tex` is not an input: it contains superseded scalar/Bianchi-conditioned material and an explicit legacy-reproduction guard.

## Deterministic transformation

`pandoc.yaml` specifies a Pandoc conversion from the flattened Markdown SSOT to standalone LaTeX. `structure.lua` removes the control-plane prologue from the rendered paper, promotes the manuscript section hierarchy, strips already-written numeric section prefixes, marks the abstract unnumbered, and inserts `\\appendix` before Appendix A. `header.tex` contains only publication-format support and no scientific claims.

The pinned build-tool identities are recorded in `R4B0_PUBLICATION_ASSEMBLY_SPEC.yaml`. R4B0 assembles and statically audits the source only. PDF compilation and page-level visual review belong to R4B1.

## Scientific integration

`REPORT_A_ORGANIC_INTEGRATION_MATRIX.yaml` records how the original repository programme and the later tensorized/response developments enter one argument. It prevents a chronological PR digest from replacing the scientific structure and forbids revival of scalar-only ranks, withdrawn WU-006--008 interpretations, finite-HEALPix overclaim, or BASS/native-solver content.

## Intended local commands

After the pinned tools are available:

```bash
cd docs/research_reports/report_a
pandoc --defaults=pandoc.yaml
tectonic -X compile build/HTT_REPORT_A_THEORY_METHODS_R4B0.tex \
  --outdir build --keep-logs
```

These commands are informative until an accepted execution receipt exists. A generated PDF is not frozen or publication-authorized merely because it compiles.
