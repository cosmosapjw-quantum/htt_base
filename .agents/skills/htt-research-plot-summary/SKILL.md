---
name: htt-research-plot-summary
summary: Generate and audit diagnostic plots and figure provenance for HTT/MIO/BASS result packs without overclaiming smoke plots as validation.
description: Use when PRs produce plots, result packs, convergence diagnostics, residual plots, local/global discrimination heatmaps, G_F depth-gap plots, BiPoSH/template summaries, or manuscript figures.
---

# HTT Research Plot Summary Skill

## Purpose

Make figures useful, reproducible, and honest. A plot is not evidence unless its data, script, category, and claim tier are recorded.

## Plot categories

Use exactly one:

- `SMOKE`: confirms code path executes.
- `DIAGNOSTIC`: explores behavior; not validation.
- `VALIDATION`: tied to a predeclared test or benchmark.
- `PUBLICATION_CANDIDATE`: manifest-backed, provenance-complete, claim-tier-reviewed.

## Required workflow

1. Identify plotted quantity and owner.
2. Identify source data/artifact and manifest.
3. Identify script that generates the plot.
4. Record units, normalization, frame, coordinate system, transfer source, and random seed.
5. Add caveat text: what the plot does not show.
6. Add claim-tier label.
7. Preserve old plot or update manifest with replacement reason.

## Recommended HTT/MIO plots

- `Q` vs certified `F` status.
- `G_F` depth-gap with local/systematic null bands.
- local/global response-overlap matrix.
- HTT/MIO cross-check table without merge.
- transfer sensitivity: AniCLASS external vs future native.
- figure provenance/missing source inventory.

## Required output

```markdown
## Plot summary

## Quantity plotted

## Data/script/manifest provenance

## Category and claim tier

## Interpretation

## What this plot does not show

## Missing validation before publication
```

## Hard prohibitions

- Do not call smoke plots validation.
- Do not hide arbitrary normalization.
- Do not overwrite figures without provenance.
- Do not let a figure caption imply a stronger claim tier than the underlying artifact.
