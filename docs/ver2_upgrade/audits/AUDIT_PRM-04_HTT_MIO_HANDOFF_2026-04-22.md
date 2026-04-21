# AUDIT_PRM-04_HTT_MIO_HANDOFF_2026-04-22

## Scope

- packet: `PRM-04-HTT-MIO-HANDOFF`
- authority: `docs/ver2_upgrade/*`
- mode: preliminary-results mode
- verification style: CoVe + metacognitive audit + equation-to-code consistency + touched-surface tests

## Target

Make HTT, MIO, and TSC consume the generated preliminary VER2 result packs
without local JSON surgery or package-specific ad hoc parsing.

## Key finding

After `PRM-03`, the generated result packs were correct, but the external
packages still lacked a canonical ingestion path:

- HTT still consumed native objects more naturally than generated packs;
- MIO could read its own artifact family but not the pack-level preliminary
  bundle as a first-class input;
- TSC had downstream adapters but not a pack-backed loader path for the
  exported overlay.

So the remaining blocker was handoff friction, not missing preliminary science
artifacts.

## Closure chosen

`PRM-04` closes by adding:

1. a shared `workspace.contracts.preliminary_results` loader surface for:
   - generated result-pack summaries;
   - generated artifact envelopes;
   - bounded native reconstruction of exported `ObservableVector`,
     `AtlasEntryLite`, `DiscriminationMatrix`, `TscAdequacyOverlay`, and
     `MioCertificate`;
2. a package-local HTT handoff helper built from packs `A`, `B`, and `D`;
3. a package-local MIO handoff helper built from pack `D`;
4. a package-local TSC handoff helper built from packs `C` and `D`.

The loader is deliberately summary-aware: if the exported artifact carries a
bounded summary payload rather than the full raw internal object, the loader
reconstructs the native contract with explicit summary-only defaults instead of
pretending the full heavy object was serialized.

## Code changes

- shared loader:
  - `htt/workspace/contracts/preliminary_results.py`
- HTT handoff:
  - `htt/htt/htt/integration/preliminary_results.py`
- MIO handoff:
  - `htt/mio/bridges/preliminary_results.py`
- TSC handoff:
  - `htt/tsc/adapters/preliminary_results.py`
- re-export updates:
  - `htt/workspace/contracts/__init__.py`
  - `htt/htt/htt/integration/__init__.py`
  - `htt/mio/bridges/__init__.py`
  - `htt/tsc/adapters/__init__.py`
- tests:
  - `htt/workspace/contracts/tests/test_preliminary_results.py`
  - `htt/htt/tests/test_preliminary_results_handoff.py`
  - `htt/mio/tests/test_preliminary_results_bridge.py`
  - `htt/tsc/adapters/test_preliminary_results.py`

## Physics / contract audit

- kept:
  - all-11-type / orthogonal-vs-tilted / tilt-vs-boost metadata
  - current pack claim tiers and caveats
  - TSC advisory-only ownership
  - MIO diagnostic-only ownership
- closed:
  - local JSON surgery for generated preliminary pack consumption
- refused:
  - any new physics promotion
  - any HTT posterior correction from TSC
  - any MIO truth-certificate reinterpretation

## Metacognitive audit

- what changed:
  - generated preliminary packs are now a first-class interop surface for
    HTT/MIO/TSC, not just exporter/manuscript products
- what it still does not justify:
  - no new geometry claim
  - no new tilted runtime success claim
  - no non-Type-I exact-propagator promotion
- what downstream could still misread:
  - summary-aware reconstructed contracts are bounded preliminary surfaces,
    not raw internal solver dumps

## Verification

- `venv/bin/python -m py_compile htt/workspace/contracts/preliminary_results.py htt/htt/htt/integration/preliminary_results.py htt/mio/bridges/preliminary_results.py htt/tsc/adapters/preliminary_results.py htt/workspace/contracts/tests/test_preliminary_results.py htt/htt/tests/test_preliminary_results_handoff.py htt/mio/tests/test_preliminary_results_bridge.py htt/tsc/adapters/test_preliminary_results.py`
- `PYTHONPATH=htt:htt/src venv/bin/python -m pytest htt/workspace/contracts/tests/test_preliminary_results.py htt/htt/tests/test_preliminary_results_handoff.py htt/mio/tests/test_preliminary_results_bridge.py htt/tsc/adapters/test_preliminary_results.py -q`
  - result: `7 passed`
- smoke usage:
  - `build_preliminary_directional_handoff(required_channels=("TT",))`
    returns pack ids `("A", "B", "D")`
  - `build_preliminary_mio_handoff()` returns pack id `"D"`
  - `build_preliminary_tsc_handoff()` returns pack ids `("C", "D")`

No plot audit was required for this packet under preliminary-results mode.

## Carry-forward

- representative tilted runtime remains blocked
- non-Type-I exact propagator remains unresolved
- direction-resolved reionization microphysics remains unresolved
- if later downstream work needs raw internal heavy objects instead of the
  exported summary surfaces, reopen under `PRM-05-TARGETED-PHYSICS` or a later
  contract-expansion packet rather than widening the preliminary handoff layer

## Verdict

`PRM-04` is closed for preliminary-results mode.

The preliminary chain is now live end to end:

- BASS emits bounded preliminary artifacts
- exporter/result-pack generation serializes them
- HTT/MIO/TSC ingest the generated packs through canonical loaders
- no package needs local JSON surgery to consume the current preliminary
  result surfaces
