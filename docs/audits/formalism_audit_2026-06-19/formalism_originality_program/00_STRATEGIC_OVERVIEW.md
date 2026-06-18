# 00 — Strategic Overview: The Formalism's Originality Is Its Architecture

**Premise.** The adversarial audit returned MAJOR REVISIONS, but the driver was the *figure/prose layer* (a mislabeled semantic-split figure, "detection" wording), **not** the formalism. The audit's own words — the contracts are "internally consistent, sign-aware, provenance-bearing, test-backed" and "enforce nearly all rejection triggers at the code level" — are the originality case. This document argues that the genuine novelty of `x_C / Q / Π / F / G_F` is **architectural and methodological**, is independent of any detection, and is *strengthened* by the honesty corrections rather than diminished by them.

---

## 1. The novelty inversion (same lever as the physics paper, applied to the statistics)

The thing that endangered the manuscript was the implication that `Q/F/G_F` *detect* anisotropy. That was never the contribution. The contribution is the **diagnostic algebra and its enforcement machinery**:

> A claim-tiered, comparator-explicit, sign-aware family of FLRW-departure diagnostics whose definitions, provenance, and *anti-overclaim guarantees* are encoded as machine-checked contracts and backed by an adversarial test suite — so that a diagnostic *cannot be constructed* in an over-claimed form.

Deleting "detection" language costs nothing and frees this. The audit removed a liability and pointed at the real result.

## 2. Reposition the genre

| From (fragile) | To (defensible, more publishable) |
|---|---|
| A set of summary statistics that "show" anisotropy | A **statistical-methodology / framework** contribution: a contract-enforced diagnostic algebra for quantifying FLRW departure |
| Headline = `Q`/`F`/`G_F` values implying a signal | Headline = the *architecture* (signed coordinate + fail-closed certification + semantic firewall + typed diagnostic↔inference boundary) and what it structurally guarantees |
| Reviewer reflex: "over-interpreted diagnostics" → reject | Reviewer reflex: "a principled, machine-checked, overclaim-proof diagnostic framework" → accept |

This can stand as its own **methods paper** (or the methods backbone of the physics paper), in a statistics-for-cosmology or methodology venue. Framework papers with explicit guarantees are more durable than contested signals.

## 3. What is genuinely new (delineated against prior art — see `06`)

The reproducibility community already has **blinding / pre-registration** (DES catalog/data-vector/parameter blinding) and **multiverse / specification-curve analysis** (Steegen 2016; Gelman & Loken's "garden of forking paths"). Those are *practices* that prevent biased analysis *choices*. The formalism's distinct move is to **encode those ideas as typed, machine-checked contracts on the diagnostics themselves**, and to add a fourth, under-precedented idea:

- **A semantic firewall**: the diagnostic object *refuses to be constructed* if its metadata uses reserved overclaim language (occupancy/posterior/evidence/family/geometry/global-tilt), if its owner/tier is wrong, or if its certification gates fail. This is not blinding (which hides results) and not multiverse reporting (which enumerates outcomes) — it is a structural prohibition on *mislabeling a diagnostic as evidence*.
- **A typed diagnostic↔inference boundary** (MIO↔HTT): the inference-side pushforward *rejects* diagnostic-side inputs and forbids `ln_b`/`evidence`/`posterior` tokens, so diagnostics cannot be laundered into evidence.

> **Framing sentence for the abstract:** *We encode, as machine-checked contracts, three reproducibility disciplines usually left informal in cosmology — specification-curve/multiverse reporting, anti-post-hoc threshold pre-registration, and a typed diagnostic↔inference firewall — and add a semantic firewall that structurally refuses to construct an over-claimed FLRW-departure diagnostic.*

## 4. Honesty ↔ novelty pairing (every tone-down is paired with a novelty move)

| Honesty move (audit-mandated) | Paired novelty-preservation move |
|---|---|
| Stop calling `Q/F/G_F` a "detection" | Promote the **firewall** (F1) and the **typed MIO↔HTT boundary** (F6) as the headline contributions — they are what make non-detection honest |
| `x_C≈0` must not read as isotropy | Promote `cancellation_index` to a first-class output and add a **sector-resolved departure vector** (F7) — a *new* reported object |
| "filling fraction" over-connotes physical occupancy | Define `F` precisely **and** add an unsigned **total-anisotropy magnitude companion** (F8) so users get both signed ceiling-occupancy and a genuine magnitude |
| The semantic-split figure mislabels Π/F/G_F | Generalize the lesson into a **semantic-firewall specification + adversarial fuzzer** (F9), and ship a *correct* semantic-separation figure |
| `G_F` currently gives no boost-vs-tilt separation | Build the **matched-null + depth-template discrimination** (U4/E4), turning the limitation into a forecast result (links to the tomographic forecast) |
| Legacy VER2 labels assert atlas/production-grade | Over-stamp as `legacy_not_current`; the firewall already bars the live overclaims |

## 5. Delete / demote / keep / upgrade

- **Delete** (no novelty cost): "detection"/"98% accuracy" prose; the mislabeled semantic-split bars.
- **Demote** (kept, recast): `Q/F/G_F` numeric displays → explicitly descriptive, comparator/measure-kind-stamped.
- **Keep & foreground** (the real paper): the firewall (F1), the signed coordinate + cancellation (F2), fail-closed `F` (F3), registered-threshold `Π` (F4), denominator-split `G_F` (F5), the MIO↔HTT boundary (F6).
- **Upgrade** (new from audit): sector vector (F7), magnitude companion (F8), firewall spec + fuzzer (F9), matched-null depth discrimination (U4).

## 6. Risk register

| Risk | Mitigation |
|---|---|
| "This is software engineering, not statistics/physics" | It is a *methodology* contribution with statistical content (signed projection, certification semantics, exceedance/threshold registration, confound separation); the firewall is the novel methodological object, evidenced by the audit's inability to break it |
| "Multiverse analysis already does this" | Multiverse reporting enumerates outcomes; it does not *refuse to construct* over-claimed objects, nor pin owner/tier, nor enforce a diagnostic↔inference boundary (see `06`) |
| "The diagnostics don't detect anything" | Correct and by design; the contribution is the architecture and its guarantees, not a detection |
| Reviewers want a worked physical payoff | E1 (cancellation null), E4 (matched-null depth discrimination), E5 (comparator sensitivity) produce concrete quantitative outputs |

## 7. Execution order (maps to the rest of this package)

1. `01_NOVELTY_LEDGER.md` — F1–F9 ranked and defended.
2. `02_REFRAME_AND_REORG.md` — methods-paper framing + abstract + claim ladder.
3. `03_UPGRADE_PLAN.md` — five upgrades (U1–U5) with acceptance criteria.
4. `04_EXPERIMENT_PROGRAM.md` — E1–E7 numerical experiments.
5. `05_DEFENSE_DOSSIER.md` — anticipated objections → responses.
6. `06_PRIOR_ART_POSITIONING.md` — CRAG novelty map (methodology + physics).
7. `code/` + `experiment_tracker.xlsx` — runnable reference implementation, experiments, and tracker.

**Bottom line:** the formalism does not need a detection to be original; its originality is a machine-checked, overclaim-proof diagnostic algebra. The audit's corrections make that contribution *cleaner and more visible*, not smaller.
