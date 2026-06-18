# 04 — Numerical Experiment Program

Ordered by leverage. Each: hypothesis, method, produced object, success criterion, effort, dependencies. Tracker in `experiment_tracker.xlsx`; code in `code/` (all run against the dependency-free `reference_formalism.py`).

🟢 hours · 🟡 days · 🔴 weeks.

---

## E1 — Cancellation null distribution  🟢  (→ U1/F7)

- **Hypothesis:** under realistic sector priors, the signed `x_C` (and `F`) materially under-represents total anisotropy a non-negligible fraction of the time, so a signed-only report is misleading.
- **Method:** sample `(Σ², W², Ω_tilt, Ω_{k,aniso})` from documented priors; compute the distribution of `cancellation_index` and of `|x_C|/M` (signed-to-total ratio). `code/exp01_cancellation_null.py`.
- **Produces:** the fraction of draws with `cancellation_index > {0.5, 0.9}`; the `|x_C|/M` distribution; a worked counter-example.
- **Success:** quantifies how often cancellation hides anisotropy → justifies reporting the sector profile + magnitude (U1/U2).
- **Depends on:** `reference_formalism.py`.

## E2 — `F` fail-closed coverage  🟢  (→ F3)

- **Hypothesis:** the certification gate correctly *refuses* every inadmissible input (negative `x_C`, super-ceiling, non-admissible/external ceiling) with no silent clipping.
- **Method:** stress grid of `(x_C, U, policy, is_admissible)` spanning valid/invalid; assert `F` constructs iff valid and equals `x_C/U` then, raises otherwise. `code/exp02_F_failclosed_coverage.py`.
- **Produces:** a coverage table (constructed vs raised) over the grid; confirmation of no clipping.
- **Success:** 100% correct accept/reject; zero clipped values.
- **Depends on:** `reference_formalism.py`.

## E3 — `Π` threshold-registration bias  🟢  (→ F4)

- **Hypothesis:** post-hoc threshold selection inflates the apparent exceedance significance; `Π`'s registration prevents it.
- **Method:** simulate a null sample bank; compare (a) a pre-registered threshold's exceedance fraction vs (b) the *minimum* exceedance fraction achievable by post-hoc threshold picking (the garden-of-forking-paths inflation); show the look-elsewhere gap. `code/exp03_Pi_threshold_bias.py`.
- **Produces:** the post-hoc vs pre-registered exceedance gap; the implied false-positive inflation.
- **Success:** quantifies the bias `Π`'s registration removes → validates F4.
- **Depends on:** `reference_formalism.py`.

## E4 — `G_F` matched-null + boost-vs-tilt depth discrimination  🟡  (→ U4)  ★

- **Hypothesis:** with matched-calibrated nulls, a depth-*dependent* `G_F` template (global tilt; sign change at a transition depth) separates from a depth-*independent* one (local boost); the current unmatched config does not (FPR≈1).
- **Method:** build matched vs unmatched null banks; compute the `G_F`-depth-profile ROC / Fisher separation of boost vs tilt as a function of depth coverage. `code/exp04_GF_matched_null_boost_vs_tilt.py`.
- **Produces:** FPR under matched calibration; ROC AUC / Fisher σ for boost-vs-tilt; the depth coverage needed for separation.
- **Success:** matched-null FPR below threshold; a quantitative separation forecast (else `G_F` stated as non-discriminating).
- **Depends on:** `reference_formalism.py`; links to the physics-program tomographic forecast.

## E5 — Comparator multiverse for `x_C`/`Q`  🟢  (→ U5/F2)

- **Hypothesis:** `x_C`/`Q` vary across comparators (flat/matched/closed) enough that an implicit comparator is a hidden researcher degree of freedom.
- **Method:** compute `x_C`/`Q` under each comparator for representative configs; report the specification-curve and across-comparator spread. `code/exp05_comparator_sensitivity.py`.
- **Produces:** the comparator specification-curve; the spread as an uncertainty.
- **Success:** spread quantified; comparator never implicit in reporting.
- **Depends on:** `reference_formalism.py`.

## E6 — Semantic-firewall fuzz  🟡  (→ F1/F9)

- **Hypothesis:** the firewall refuses every attempt to construct an over-claimed diagnostic.
- **Method:** property-based fuzzer that randomly injects reserved language, mis-owns quantities, clips/sign-dirties `F`, post-hoc-selects `Π` thresholds; asserts refusal. `code/semantic_firewall_fuzz.py`.
- **Produces:** the count of successful smuggles (target 0); a coverage report by attack type.
- **Success:** 0 successful smuggles across N trials.
- **Depends on:** `reference_formalism.py`.

## E7 — MIO↔HTT leakage audit  🟡  (→ F6)

- **Hypothesis:** no construction path launders a diagnostic into an inference object (evidence/posterior/ranking).
- **Method:** enumerate the diagnostic→inference interfaces; assert the inference-side constructor rejects diagnostic inputs and forbids `ln_b`/`evidence`/`posterior` tokens (mirrors `reject_mio_likelihood_inputs`). `code/semantic_firewall_fuzz.py::leakage_audit`.
- **Produces:** a leakage report (paths checked, rejections confirmed).
- **Success:** 0 leakage paths.
- **Depends on:** `reference_formalism.py`.

---

## Priority and sequencing

```
Now (validate + new outputs): E1, E2, E3, E5, E6, E7  (🟢/🟡; all run on reference_formalism)
Upgrade (forecast result):    E4                       (🟡; matched-null + boost-vs-tilt)
```

**Minimum set to make the originality case + satisfy the audit:** E1 + E2 + E6 (cancellation honesty, fail-closed validation, firewall adversarial proof). E3/E5/E7 strengthen; E4 turns the `G_F` limitation into a forecast. Each `Produces` row is a methods-paper-ready object.
