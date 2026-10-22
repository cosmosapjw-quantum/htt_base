# G07-A — independent repair review of CAS07-C01 (Lean axis)

Reviewer: fresh-context read-only subagent, requested gpt-6-astra/ultra (unavailable), observed claude-opus-5-5. Did not author the source or the lead receipts.

**Verdict: PASS_WITH_NOTES. No blocking finding.**

## Checks

| Check | Result |
|---|---|
| Contract `CAS-07.json` exact_statement[0] and `c01_input_aligned_v1_20261005/ADMITTED_INPUTS.json` read before the proof | PASS (Kc>0 positive sqrt, s≥0, separate flat branch f0=s, fixed-s right limit Kc→0+, integral identity derived not assumed) |
| Source sha256 `282d48caf23e01b2cdc81efa81d5bf9818df82b29a107962548660500c82dedd` | PASS |
| f(0)=0, f′(0)=1 (backed by HasDerivAt, not Lean's default deriv) | PASS |
| f″=k f (HasDerivAt of deriv) | PASS |
| k∫₀ˢ(s−t)f(t)dt = f(s) − s | PASS: hand integration by parts; mpmath 40-digit residual ≤ 1e−40 on four (k,s) points; wrong-sign form gives residuals 0.34–2695 |
| Hypotheses assume a conclusion | PASS (only 0<k, 0≤s) |
| Lean total sqrt/division at k≤0 | PASS: every claim except trivial `hyper_zero` requires 0<k; `hyper 0 s = 0`, and the file keeps k=0 as the separate `flat` branch |
| Flat branch and limit `nhdsWithin 0 (Ioi 0)` | PASS (one-sided limit is the correct one) |
| Units | PASS |
| Build/axiom receipts | PASS: exit 0; all declarations depend only on propext, Classical.choice, Quot.sound; no sorry or escape hatch |
| Independent rerun outside the repo | PASS: exit 0; `.olean` sha256 `2ef41d2b255a8ad2f937f20a5649bdda731fff8a5616f6c98941bc45d2ab0cb6` byte-identical to the lead run |
| attempt01 | harness failure only (missing `-R`), preserved |

## Notes (non-blocking)

- **N1.** `flat_integral` (`0 * ∫ … = flat s − s`) holds for any integrand. It is contract-faithful ("integral identity 0=0"); its integrand (s−t)·t is correct. An optional strengthening would be ∫₀ˢ(s−t)t dt = s³/6.
- **N2.** Interface caution: `hyper 0 s = 0`, not s. Any consumer of the contract's Kc≥0 assumption must split into `0<Kc → hyper` and `Kc=0 → flat`. Instantiating `hyper` at 0 gives the wrong comparison function.
- **N3.** The limit is pointwise in s, not uniform; nothing is claimed for limits of f′, f″ or the integral.
- **N4.** `hs` is unused in `hyper_integral` (the identity holds for all real s); linter warnings are cosmetic.
- **N5.** Scope: Lean axis only. Wolfram, SymPy and Sage historical axes and the R1 flat-branch repair behind `ADJUDICATION_FLAT_REPAIRED.json` were not re-run.

## Not proved

Jacobi solution existence or majorization (‖D − sI‖ ≤ f − s); CAS07-C02; CAS07-C03; conditional synthesis implication; physical distance inference; scientific admission (HOLD).
