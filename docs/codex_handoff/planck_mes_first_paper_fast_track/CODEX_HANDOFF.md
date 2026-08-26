# Codex handoff — fastest track to the first Planck MES observation paper draft

## STATUS

```yaml
repository: cosmosapjw-quantum/htt_base
branch: changeset/pr324-mes-methodology-stack-20260826
audited_start_head: 9007c4188ea9e52ebc3f557fc88e0421a5d2d94d
audited_start_tree: 4a92669e0bb1cbafe0b58367e20687f026e15c61
mode: DRAFT_NONAUTHORITATIVE
objective: produce the first complete observational-analysis paper draft
```

This is **not** another planning, audit, provenance, or governance task.

Read exactly:

```text
docs/codex_handoff/planck_mes_first_paper_fast_track/FAST_TRACK.yaml
docs/codex_handoff/planck_mes_first_paper_fast_track/DRAFT_SKELETON.md
docs/codex_handoff/planck_mes_first_paper_fast_track/references.bib
docs/PR_DELTAS/pr-323.md
docs/PR_DELTAS/pr-325.md
docs/PR_DELTAS/pr-327.md
```

Then implement and run the paper builder immediately.

## Governing rule

```text
existing frozen evidence
→ one map-free decomposition/figure run
→ full manuscript draft
→ one targeted numeric/claim review
→ bounded repair if reproduced defect exists
→ stop
```

Do not create:

- another audit package;
- another execution plan;
- another reviewer contract;
- a new provenance schema;
- a new DAG node merely for paper preparation;
- security, cryptography, branch-protection, or anti-tamper machinery;
- a full-suite reassurance campaign.

The next commit must contain **actual generated tables/figures and a manuscript draft**, not more process prose.

## Exact scientific baseline

The current durable results are:

```yaml
generic_PR314_family_rank: 133/301
corrected_PR315_generic_rank: 133/301
primary_PR327_MES_family_rank: 98/301
MES_local_rank_numerators:
  [74, 74, 95, 182, 35, 177, 16, 155, 174, 135]
smallest_local_rank:
  feature: multipole_l3_absdot_0
  rank: 16/301
sigma_anchor_rank: 74/301
omega_anchor_rank: 74/301
directional_support: BLOCKED
local_global_identification: NONIDENTIFIED
family_identification: BLOCKED
```

The primary interpretation is a **conditional finite-ensemble null result**.
The anchors do not drive the smallest local rank. Do not write that MES reveals,
detects, strengthens, or explains an anomaly.

## Immediate P1 repairs for the paper interpretation

### 1. Decompose the rank shift

The difference

```text
133/301 → 98/301
```

simultaneously changes family composition and coordinates. Compute all six
families in `FAST_TRACK.yaml` using the same row pool, two-sided tails,
leave-one-out centers, and observation-inclusive rank:

```text
GENERIC_12
RAW_REDUCED_10
EPS_REDUCED_10
MES_10
ANCHORS_ONLY_2
MORPHOLOGY_ONLY_8
```

Do not add, remove, or select a family after seeing its result.

The comparison is descriptive operator sensitivity, not six independent
hypothesis tests and not a search for the smallest rank.

### 2. Quantify what drives the result

Report:

- the minimum local coordinate for every family;
- Pearson and Spearman dependence of the two anchors;
- numerical rank and condition of the two-anchor correlation block;
- paired Spearman correlations of row-level family scores;
- whether `MORPHOLOGY_ONLY_8` reproduces the observation's minimum;
- a direct statement that both anchor ranks are `74/301`, whereas the smallest
  local rank is `16/301` from `multipole_l3_absdot_0`.

## Implement now

Create:

```text
scripts/paper/build_planck_mes_first_paper.py
tests/paper/test_planck_mes_first_paper.py
docs/generated/planck_mes_first_paper/
papers/planck_mes_first_observation/main.tex
papers/planck_mes_first_observation/references.bib
```

The builder must read only the map-free committed inputs listed in
`FAST_TRACK.yaml`.

Do **not** open or scan:

```text
/mnt/sn850x2t/htt_base_e2e/workdir/raw/**
```

in this first pass. The raw Planck archive is available later for a reproduced
need, but it is not required to make the first draft.

## Required generated outputs

```text
docs/generated/planck_mes_first_paper/analysis_summary.json
docs/generated/planck_mes_first_paper/feature_rank_table.csv
docs/generated/planck_mes_first_paper/family_ablation_table.csv
docs/generated/planck_mes_first_paper/family_score_dependence.csv
docs/generated/planck_mes_first_paper/figure_local_rank_profile.pdf
docs/generated/planck_mes_first_paper/figure_family_rank_comparison.pdf
docs/generated/planck_mes_first_paper/figure_global_null_scores.pdf
docs/generated/planck_mes_first_paper/figure_anchor_dependence.pdf
```

PNG companions are allowed but not required.

Use one deterministic analysis function for all family variants. Reuse
`observation_inclusive_max_scan`; do not reimplement a statistically different
rank algorithm.

## Exact formulas

For each row:

```text
epsilon_l = sqrt((2l+1) C_l / (4 pi)) / T0
```

under the frozen residual-dipole attribution `eps1=0`:

```text
Sigma2_anchor = (3/2) [3 eps2 + (3/7) eps3]^2
W2_anchor     = (3/2) [(2/15) eps2]^2
```

Use the active repository authority rather than hardcoding alternate
coefficients. The explicit formulas above are manuscript checks, not a second
implementation authority.

## Manuscript story

Working title:

> Finite-null calibration of MES-anchored low-multipole morphology in Planck PR3

The paper is a narrow methods/application paper. Its contribution is:

1. typed realization-conditional MES ceiling coordinates;
2. separation of amplitude coordinates from eight irreducible morphology
   coordinates;
3. a row-equivariant observation-inclusive finite-null family statistic;
4. an exact map-free Planck PR3 SMICA application;
5. an explicit null result and honest nonidentification boundaries.

The draft must not wait for Commander, 999 CMB-only simulations, Planck PR4,
alternative masks, a directional low-z lane, xAct response completion, a native
solver, or a Bianchi atlas.

## Required manuscript sections

```text
Abstract
1. Introduction and scope
2. Planck PR3 observation and paired FFP10 null ensemble
3. Corrected joint cut-sky low-ell features
4. Typed MES realization-conditional coordinates
5. Observation-inclusive finite-null family statistic
6. Results
   6.1 coordinate-wise ranks
   6.2 family decomposition and coordinate sensitivity
   6.3 generic-control comparison
7. Interpretation and limitations
8. Conclusion
Appendix A. Exact feature and tail registry
Appendix B. Map-free replay and data/code availability
```

Start from `DRAFT_SKELETON.md`, but replace every `TO_BE_COMPUTED` marker from
the generated `analysis_summary.json`.

## Claim language

Allowed:

- “conditional on the frozen SMICA + 300 paired FFP10 ensemble”;
- “observation-inclusive finite rank”;
- “the result is not an unusually small family rank”;
- “the minimum local rank is morphology-driven”;
- “the anchors are realization-conditional same-row coordinates”;
- “Planck-only local/global separation is nonidentified.”

Forbidden:

- “unconditional p-value”;
- “detection of anisotropy/shear/vorticity/global tilt”;
- “MES uncovers a hidden anomaly”;
- “98/301 is significantly different from 133/301”;
- “self-anchors add independent information”;
- “direction, STF tensor, Bianchi family, or native-solver evidence”;
- “publication ready” merely because the draft compiles.

## Identity handling

- Existing NPZ/JSON source packages: preserve their required source/content
  identities.
- Recomputed rational ranks: require exact equality.
- Floating diagnostics: require justified numerical equality.
- Figures and PDF containers: do not require byte-identical output across
  environments; verify data values, labels, dimensions, and manuscript
  references.
- The existing dirty-generation provenance is `FIX_SOON` before submission, not
  a reason to invalidate the already reproduced numerical result or delay the
  draft.

## Focused tests

At minimum:

```text
test_primary_mes_rank_replays_as_98_of_301
test_generic_control_replays_as_133_of_301
test_all_six_predeclared_families_are_present_and_row_equivariant
test_rank_shift_decomposition_is_not_silently_omitted
test_anchor_and_minimum_feature_attribution_is_correct
test_builder_never_opens_raw_map_paths
test_manuscript_numbers_are_loaded_from_analysis_summary
test_forbidden_claims_are_absent
```

Run:

```bash
PYTHONPATH=htt:htt/src:htt/htt \
python -m pytest -q tests/paper/test_planck_mes_first_paper.py

PYTHONPATH=htt:htt/src:htt/htt \
python scripts/paper/build_planck_mes_first_paper.py \
  --output-dir docs/generated/planck_mes_first_paper \
  --paper-dir papers/planck_mes_first_observation
```

Then rerun the same focused test file. Do not run the full repository suite
unless a reproduced failure points outside this surface.

Compile LaTeX once if a local TeX engine is already installed. Missing TeX is
not a blocker to a complete source draft.

## One review only

After the draft and generated outputs exist, perform one fresh-context,
read-only review limited to:

```text
numerical transcription
statistical interpretation
MES formula/convention wording
claim-boundary violations
figure/table consistency
citation support
```

If it finds a reproduced P0/P1, repair it and rerun only affected tests. Do not
create a review-of-review or new audit package.

## Commit and push

Commit actual code, generated tables/figures, and manuscript source to this same
branch. Do not create another planning branch unless a real Git conflict makes
it necessary.

## Short completion report

Return only:

```yaml
STATUS:
ACTUAL_PROGRESS:
VERIFIED:
DEFERRED:
BLOCKERS:
NEXT:
```

`NEXT` must be exactly one action: either revise the completed draft for target
journal style, or resolve one concrete blocker that prevented draft generation.
