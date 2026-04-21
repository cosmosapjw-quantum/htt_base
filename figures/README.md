# Figure tree

Unified figure root for the tilted-FLRW / BASS project. Consolidated
on 2026-04-19 from the former `figures/` + `plots/` split into three
parallel subtrees:

| Subtree | Audience | Curation | Count |
| --- | --- | --- | --- |
| [`paper/`](paper/INDEX.md) | manuscript inclusion | full captions, Okabe-Ito palette, PNG + PDF | ~80 figures across ch02–ch12 |
| [`preliminary/`](preliminary/) | early-stage review | Tier A/B/C/D grouping | 5 (Tier A only so far) |
| [`physics_gallery/`](physics_gallery/README.md) | code-internal diagnostic | 50 plots across 11 physics topics | 50 |

Manuscript LaTeX (`project/00_manuscript/main.tex`) has
`\graphicspath{{./figures/}}` so every chapter's `\includegraphics`
resolves under this tree.

## Quick regeneration map

```bash
# Paper figures (four waves)
venv/bin/python scripts/make_preliminary_figures.py --tier A
venv/bin/python scripts/make_paper_figures.py
venv/bin/python scripts/make_additional_figures.py
venv/bin/python scripts/make_more_figures.py
venv/bin/python scripts/make_third_wave_figures.py

# Physics diagnostic gallery (regenerated every LB-N phase boundary)
venv/bin/python scripts/make_physics_gallery.py
```

VER2 manuscript/export scaffolding is separate from figure rendering:

```bash
# IM-09D live exporter: result-pack surfaces + figure-manifest audit
venv/bin/python scripts/ver2_artifact_export.py
venv/bin/python scripts/ver2_artifact_export.py --check
```

Paper generators resolve observational inputs from the current
`workdir/` tree, preferring `workdir/obs_bundle` and then falling back
to `workdir/raw` or `workdir/compact_products` when the bundle index is
ahead of the packaged files. In the 2026-04-20 rerun this means:

- DESI footprint / density / `n(z)` figures use the full raw Y1 FITS
  catalogs when available, not legacy plotting fixtures.
- CF4 observational figures read the regenerated query products under
  `workdir/compact_products/cf4/`, which are derived from the raw
  `CF4pp_mean_std_grids.npz` adapter path.
- The multi-experiment ACT extension figure prefers ACT DR6 bandpowers
  when unpacked in `workdir/obs_bundle`; if DR6 is absent it degrades to
  the real ACT DR4 compact release and labels the figure accordingly.

See each subtree's README / INDEX for per-figure detail, captions, and
known placeholder / mock figures. For the VER2 manifest gate, read
`paper/VER2_MANIFEST_INDEX.md` before treating any legacy paper figure as
manuscript-ready.

## Figures blocked on the bass_py low-ℓ solver

The audit at
[`paper/INDEX.md`](paper/INDEX.md) § "Figure status" cross-checked
against `docs/audits/AUDIT_PHASE_IND_TRACKS_W10_…md`,
`…W11_…md`, `…W19_…md` identifies a **single** figure that will
change when the bass_py low-ℓ Boltzmann solver W10-02 V-gate is
signed:

- [`paper/ch12_mio/fig_ch12d_hj01_extraction_real_backbone.png`](paper/ch12_mio/fig_ch12d_hj01_extraction_real_backbone.png)
  — Planck TT residual backbone is real, but the K_ℓ template is a
  power-law placeholder. When the W10-02 K_ℓ atlas lands, swap in
  the production `AtlasEntry` and regenerate with
  `venv/bin/python scripts/make_third_wave_figures.py --only ch12d_hj01_real_backbone`.

All BLOCKED figures carry a `STATUS: BLOCKED-ON-SOLVER` tag in their
`.caption.txt` so the regeneration list can be recovered at any time
with:

```bash
grep -rln "STATUS: BLOCKED-ON-SOLVER" figures/
```

Four other figures that *look* like mocks are in fact **intentional
pedagogical mocks** (schematic, smoke-test, scenario study, algorithm
demo) — they will never be replaced by solver output. See
`paper/INDEX.md` § "INTENTIONAL-MOCK" for the list and the reason
each stays mock.

## Policy notes

- **Paper figures** carry a matching `.caption.txt` drafted for direct
  inclusion in `project/00_manuscript/`. Each follows the Okabe-Ito
  colour palette from `htt.core.plot_style` and ships as both PNG and
  PDF at 300 dpi. Under VER2, these figure triples still require a
  canonical `.manifest.json` sidecar before manuscript promotion.
- **Preliminary figures** exist for the Tier A / B / C / D review
  cadence (`make_preliminary_figures.py --tier X`). Only Tier A is
  populated at present.
- **Physics gallery** is a code-validation diagnostic suite regenerated
  at every phase boundary (see `.claude/hooks/check_phase_boundary_audit.py`
  and the `phase_boundary_gallery` feedback memory). No captions; the
  gallery README carries a topic-by-topic description.

## Directory layout

```text
figures/
├── README.md                 ← this file
├── paper/                    ← manuscript-grade figures
│   ├── INDEX.md              ← per-chapter catalog
│   ├── ch02_dipole/
│   ├── ch03_framework/
│   ├── ch04_bounds/
│   ├── ch05_teff/
│   ├── ch06_pipeline/
│   ├── ch07_results/
│   ├── ch08_robustness/
│   ├── ch09_discussion/
│   ├── ch11_errors/
│   └── ch12_mio/
├── preliminary/              ← Tier A/B/C/D preliminary figures
│   ├── README.md
│   ├── TIER_A/               ← MES bounds, Colin β, Route B sentinel
│   ├── TIER_B/               ← reserved
│   ├── TIER_C/               ← reserved
│   └── TIER_D/               ← reserved
└── physics_gallery/          ← 50-plot bass_py diagnostic suite
    ├── README.md             ← topic-by-topic catalog
    ├── 01_species_background/
    ├── 02_flrw_geometry/
    ├── 03_recombination/
    ├── 04_reionization/
    ├── 05_bianchi_shear/
    ├── 06_tilt_boost/
    ├── 07_friedmann_closure/
    ├── 08_parameter_sweeps/
    ├── 09_pstf_hierarchy/
    ├── 10_collision_and_visibility/
    └── 11_integrator/
```
