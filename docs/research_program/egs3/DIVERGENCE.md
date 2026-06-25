# EGS3 diverge -> metacognition -> verification -> convergence

## Diverge (3 axes, over-generated)
- Math/stat: [E1] graded-comparator rank, [E2] floor reparam-invariance, [E3] Pi
  e-value calibration, [E4] Rao-Blackwell sufficiency, [E5] PSD-cone reframing.
- GR/cosmo: [E6] semi-native shear->multipole transfer, [E7] Volterra depth
  memory, [E8] vorticity re-opening, [E9] covariant bracket constants, [E10] B-mode
  Weyl channel.
- Data: [E11] K1 FFP10/NPIPE global p, [E12] CF4 WF/CR posteriors, [E13] graded
  joint pushforward, [E14] 2MRS cross-check, [E15] forward-mock cosmic variance.

## Metacognition (self-ask prune)
- Drop duplicates of existing theorems (B4-memory/visibility, S-series): kept only
  *new* statements or genuine upgrades (B1 derives the toy r_l; B2 upgrades NT2-B2).
- Drop anything needing the native solver to even *state*: B1 is single-mode +
  analytic visibility (states without the atlas); kept with documented to-close.
- Require each survivor to reduce to a runnable experiment + an analytic core.
- [E5] PSD-cone reframing kept as a design (next stage), not an immediate gate, to
  protect the x_C regression.

## Verification (runnable + symbolic)
- A1-A4 -> `research_gates/egs3/test_egs3_axis_a.py` (7 gates).
- B1-B3 -> `research_gates/egs3/test_egs3_axis_b.py` (5 gates); B4 -> Wolfram.
- Framework upgrade -> `tests/contracts/test_graded_comparator_upgrade.py`.

## Convergence
- Theorem candidates A1-A4, B1-B4 with stated limits (all gated green).
- Data candidates C1-C4 converge to discharge pipelines + tickets (mechanics
  landed; real-data runs blocked-coded).
- Diverge->converge: 15 candidates -> 8 theorem survivors + 4 data discharges + 1
  redesign design.
