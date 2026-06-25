# EGS3 Programme — toward a publishable novel data-analysis paper

A self-synthesized extension beyond the report + EGS2 (NT2-*) + the
publishable-next (T1-T6). It does three things the prior programs did not:

1. **Critically upgrades the five-variable framework** (`x_C,Q,Π,F,G_F`): promote
   the signed scalar `x_C` to a **graded comparator vector** `g=(Σ²,W²,Ω_tilt,Ω_k)`
   (additive, `x_C=⟨c,g⟩` bit-identical), and design the **PSD-cone-valued
   revisionary redesign** as the next stage. See `FRAMEWORK_CRITIQUE_AND_REDESIGN.md`.
2. **Applies GR + the covariant Boltzmann hierarchy directly to the variables**
   (Axis B): a semi-native shear→multipole transfer, a Volterra depth-memory, a
   vorticity re-opening complement, and covariant bracket constants.
3. **Discharges the standing data blocks** toward a publishable joint result
   (Axis C): the K1 global p on public Planck E2E, the K6/K5 posteriors via
   Hoffman–Ribak CR + WF/CR mocks, and the graded-comparator joint pushforward
   (a *measured* rank-2 comparator + a *proven* two-sector no-go).

**Anti-tone-down:** every theorem is a strong conditional statement — a floor, an
exclusion, a no-go, a calibrated e-value, a sufficiency, a mechanism — strong
*because* conditional. The data axis delivers a strong honest result, not a hedge.

## Map

- `FRAMEWORK_CRITIQUE_AND_REDESIGN.md` — the five-variable critique + the graded
  upgrade (landed) + the PSD-cone revisionary redesign (next stage).
- `THEOREM_CANDIDATES.md` — A1–A4, B1–B4, C1–C4 with statements + status + gates.
- `DIVERGENCE.md` — diverge → metacognition → verification → convergence trace.
- `BLOCKER_SOLUTIONS.md` — concrete discharges (C1/C2) + the semi-native path.
- `CLAIM_LEDGER.yaml` — claim tiers for the proposed next claims.
- `tickets/` — the data-blocked work (FFP10/NPIPE, CF4 WF/CR) + the PSD-cone redesign.

## Run

```bash
make egs3-gates          # Axis A (7) + Axis B (5)
make egs3-experiments    # -> docs/generated/egs3_experiments.json
make egs3-wolfram        # B4 covariant bracket constants (local Wolfram)
pytest tests/contracts/test_graded_comparator_upgrade.py   # x_C bit-identical
```

## Claim boundary

Conditional theorems + synthetic mechanics + (once data lands) calibrated
measurements only. No Bianchi-family ID, no geometry detection, no native-solver
validation, no MIO-as-odds, no scalar→family promotion. The graded comparator
and PSD-cone redesign change *representation*, not the claim envelope.
