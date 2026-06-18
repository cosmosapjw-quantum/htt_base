# 01 — Novelty Ledger: What Is Original in the Formalism, Ranked

Each entry: the claim as it should appear, its **tier** (honest strength), why it is **novel** vs the prior art in `06_PRIOR_ART_POSITIONING.md`, the **audit status**, and the **one-line defense**.

Tiers: **Exact** (algebra/contract is provably what it says) · **Methodological** (a reusable method/architecture) · **Supported** (derived + tested) · **New** (created by responding to the audit).

---

## F1 — Contract-enforced semantic firewall for diagnostic statistics  ★ flagship

- **Tier:** Methodological / Exact (the refusals are deterministic and test-backed).
- **What it is:** each diagnostic (`x_C, Q, Π, F, G_F`) is a frozen typed object that *refuses construction* if (a) its metadata/labels/caveats use reserved overclaim language (occupancy, posterior, evidence, bayes factor, family-ID, geometry, "global tilt", native-validated), (b) its `owner`/`claim_tier` is not the pinned diagnostic-only value, or (c) its certification gates fail. Enforced by `_scan_reserved_language`, owner/tier checks, and `tests/mio/*`.
- **Novelty:** Blinding (DES) hides *results* to protect analysis *choices*; pre-registration commits to choices in advance; multiverse/specification-curve analysis enumerates *outcomes*. **None refuses to construct an over-claimed diagnostic object.** A machine-checkable, test-enforced *semantic* firewall on the statistics themselves is essentially unprecedented in cosmology.
- **Audit status:** Praised — "enforce nearly all rejection triggers at the code level." Untouched.
- **Defense:** *"This is just disclaimers."* — Disclaimers are prose a reader can ignore; this is a *constructor that throws* on overclaim, with adversarial tests proving it (see F9/E6). It is the mechanism that makes a non-detection result structurally honest.

## F2 — Signed comparator-projection coordinate `x_C` with a cancellation diagnostic

- **Tier:** Exact (it is the normalized constraint rearranged) + Methodological (the cancellation_index).
- **What it is:** `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}`, a single *signed* scalar with explicit comparator/frame/units and a `cancellation_index = 1 − |x_C|/Σ|components|` that quantifies inter-sector cancellation.
- **Novelty:** Prior covariant work (MES; 1+3 covariant) bounds modes separately or uses unsigned magnitudes. The *signed, comparator-explicit packaging plus a cancellation diagnostic that exposes the `x_C≈0 ≠ isotropy` trap* is new. (Verified: `x_C=0` with `cancellation_index=1` while shear+vorticity are large.)
- **Audit status:** `x_C` correct; the cancellation caveat is a finding → promote `cancellation_index` to first-class (F7).
- **Defense:** *"Just the Friedmann constraint."* — Yes, exact by design; the contribution is the signed/sector packaging and the built-in cancellation guard, not a new equation.

## F3 — Fail-closed certified filling fraction `F`

- **Tier:** Methodological / Supported.
- **What it is:** `F = x_C/U` computed sample-wise (mean of ratios, not ratio of means), constructible *only* when `x_C ≥ 0` (sign-clean), the budget is an admissible ceiling, and `0 ≤ F ≤ 1` **without clipping** (it raises otherwise); external/atlas/observational denominators are barred from certifying.
- **Novelty:** Ratios-to-bounds exist (e.g. `Ω_k/Ω_k,max`). A *fail-closed certification semantics* — the object exists iff the preconditions hold, no silent clipping, provenance-stamped — applied to an anisotropy occupancy is new.
- **Audit status:** Praised (no clipping, sign-clean enforced). Naming finding → add F8 magnitude companion.
- **Defense:** *"Why refuse to return a number?"* — Because a clipped or sign-dirty occupancy is a false certificate; refusing is the honest behavior.

## F4 — Registered-threshold exceedance curve `Π`

- **Tier:** Methodological.
- **What it is:** an empirical survival fraction of `Q`/`F` samples with a typed threshold policy: `CURVE_ONLY` (no selected threshold) or `PRE_REGISTERED` (requires a `registration_hash` + `selection_rule`, forbids post-hoc language), plus a `measure_kind` that forces covariance/null status for `bootstrap`/`null_ensemble`.
- **Novelty:** Pre-registration is a practice; here it is **baked into the type** of the statistic, with anti-post-hoc enforcement and anti-smuggling of selected thresholds. A typed micro-pre-registration for an exceedance curve is new.
- **Audit status:** Praised. Finding: state `measure_kind` in captions (exceedance ≠ p-value unless matched null).
- **Defense:** *"Just a survival function."* — With a constructor that refuses post-hoc threshold selection and truth-probability language; that is the contribution.

## F5 — Denominator-evolution-split depth gap `G_F`

- **Tier:** Methodological / Supported.
- **What it is:** `G_F = exp(log F_cmp − log F_ref)` over ordered non-overlapping depth bins, floor-stabilized, with a mandatory **denominator-evolution split** that separates "F changed because `x_C` changed" from "because the ceiling/denominator changed," and mandatory covariance/null/calibration metadata.
- **Novelty:** Tomographic ratios are standard; the *structural separation of the numerator-vs-denominator-evolution confound*, with matched-null metadata required and "global tilt" language barred, is new.
- **Audit status:** Praised (split exposed). Finding: matched-null required before any tilt meaning; FPRs currently exceed threshold → no discrimination (honest).
- **Defense:** *"A depth ratio."* — One that refuses to hide the denominator-evolution confound and refuses to call itself global-tilt evidence.

## F6 — Typed diagnostic↔inference (MIO↔HTT) firewall

- **Tier:** Methodological / Exact.
- **What it is:** diagnostics are owner-pinned MIO/diagnostic-only; the inference-side `posterior_pushforward` *rejects MIO inputs* (`reject_mio_likelihood_inputs`) and forbids `ln_b`/`evidence`/`posterior`/`score` tokens.
- **Novelty:** A *typed boundary* that prevents laundering diagnostics into evidence/posterior/ranking. Reproducibility frameworks track provenance; they do not enforce a diagnostic↔inference type boundary.
- **Audit status:** Praised. Untouched.
- **Defense:** *"Bookkeeping."* — Bookkeeping that makes "these are diagnostics, not evidence" a checkable invariant rather than a hope.

## F7 — Sector-resolved departure vector + first-class cancellation reporting  ★ new

- **Tier:** New (from the audit's cancellation finding).
- **What it is:** report the four signed components `(Σ², −W², Ω_tilt, Ω_{k,aniso})` and `cancellation_index` as first-class outputs alongside `x_C`, so `x_C≈0` is never mistaken for isotropy.
- **Novelty:** turns a known semantic trap into a *new reported object* (a sector-resolved departure profile) that is strictly more informative than the scalar.
- **Defense:** *"You only added this because of the audit."* — Correct; the corrected object is strictly more informative.

## F8 — Total-anisotropy magnitude companion to `F`  ★ new

- **Tier:** New (from the audit's naming finding).
- **What it is:** an unsigned magnitude (e.g. `absolute_component_total` or a sector-norm) reported beside `F`, so users get both the *signed ceiling-occupancy* (`F`) and a genuine *total-anisotropy magnitude* — curing the "filling fraction"→physical-occupancy misread.
- **Novelty:** a paired signed/unsigned reporting convention for departure that prevents the cancellation trap from propagating into `F`.
- **Defense:** *"Redundant."* — Not redundant: `F` and the magnitude diverge exactly under cancellation, which is the case that matters.

## F9 — Semantic-firewall specification + adversarial fuzzer  ★ new

- **Tier:** New / Methodological (from the audit's semantic-split finding).
- **What it is:** a portable specification of the firewall (reserved-language sets, owner/tier rules, fail-closed gates) plus a **property-based fuzzer** that attempts to smuggle forbidden language/values and confirms refusal — generalizing the semantic-split lesson into a reusable artifact.
- **Novelty:** packages the firewall as something *other projects can adopt and test*, not just an internal guard.
- **Defense:** *"Internal tooling."* — A spec + fuzzer for anti-overclaim contracts is itself a methodological deliverable (cf. linters/validators as contributions).

---

## Summary table

| ID | Claim | Tier | Audit status | New output? |
|----|-------|------|--------------|-------------|
| F1 | Contract-enforced semantic firewall | Methodological/Exact | Praised (flagship) | — (guarantee) |
| F2 | Signed comparator-projection `x_C` + cancellation | Exact | `x_C` correct; promote cancellation | cancellation_index |
| F3 | Fail-closed certified `F` | Methodological | Praised | — |
| F4 | Registered-threshold `Π` | Methodological | Praised | — |
| F5 | Denominator-split depth gap `G_F` | Methodological | Praised; matched-null needed | denominator-split |
| F6 | Typed MIO↔HTT firewall | Methodological/Exact | Praised | — |
| F7 | Sector-resolved departure vector | New | New (from cancellation) | signed component profile |
| F8 | Total-anisotropy magnitude companion | New | New (from naming) | unsigned magnitude |
| F9 | Firewall spec + adversarial fuzzer | New/Methodological | New (from semantic-split) | portable spec + fuzzer |

**Read-out:** six contributions (F1–F6) survive the audit untouched/praised; three (F7–F9) are *new*, created by the corrections. The formalism is **more** original after the honesty pass — its crown jewel (F1, the semantic firewall) is exactly what makes a non-detection result publishable.
