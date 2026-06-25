# EGS2 Extension Programme — Beyond the Final Results Report

Folded execution of two complementary 2026-06-25/26 audit companions on top of
the credible-claim report:

1. **EGS extension** (`egs_extension_program`) — the NT2-* theorems (a Fisher
   floor, a two-sided exclusion, a sourced mechanism, a joint no-go) that go
   *beyond* the report's NT-A1/A3/B3 and PAPER-A/B, plus concrete public-data
   discharges of three standing blocks.
2. **Publishable-next** (`htt_base_publishable_next_package`) — the T1–T6
   theorem candidates (max-scan calibration, rank-exact identifiability,
   Boltzmann collision-gap memory bound, visibility no-go, almost-EGS gate,
   curl no-go) + the `NEXT_DAG_PR08` blocker DAG + claim ledger.

The audit verdict was **MINOR REVISIONS (near-PASS)**; the lead fix (NT-A3
"Cramér–Rao floor" mislabel) landed in rev-r119, and the genuine floor (NT2-A1)
in rev-r120.

## Map

- `THEOREM_MAP.md` — NT2-* and T1–T6 → repo modules + gate tests.
- `BLOCKER_DISCHARGES.md` — K1/K6/K5 public-data discharges + the interim
  semi-native shear→quadrupole calculator.
- `PRIOR_ART.md` — web-CRAG grounding (Knox/Tegmark Fisher; EGS/almost-EGS;
  Nilsson–Uggla–Wainwright–Lim H3/Weyl loophole; Hoffman–Ribak; Planck E2E) +
  the novelty delta.
- `CLAIM_LEDGER.yaml` — claim tiers for the proposed next claims.
- `NEXT_DAG.yaml` — the PR08/PR10 blocker DAG (reconciled with `../pr07/`).
- `tickets/` — the still-blocked real-data work (K5 mocks, semi-native calculator).

## Run

```bash
make egs2-gates          # 13 NT2 + blocker-discharge gates
make egs2-experiments    # -> docs/generated/egs2_experiments.json
# integration runner (reuses repo + EGS2 modules; T1-T6 + synthetic mechanics):
venv/bin/python docs/final_report/htt_base_publishable_next_package/scripts/run_next_research_experiments.py --quick
```

## Claim boundary

Conditional EGS-type theorems and synthetic mechanics only. No detection, no
Bianchi-family/geometry claim, no native-solver validation, no MIO-as-odds. The
toy Fisher response and scalarised hierarchy are documented; closing each theorem
to real numbers needs the covariant coefficients and real low-ℓ data. Blocked
real-data runs keep their registered blocker codes.
