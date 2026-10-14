---
name: numerical-validation
description: Validate numerical stability, convergence, sensitivity, stochastic reproducibility, and performance of physics or mathematics research code after a change.
---


# Numerical Validation
For `htt_base`, follow `AGENTS.md` and the selected task contract. Use applicable existing records; create a new artifact only when a consuming decision requires it. Preserve frozen and historical evidence. A skill verdict does not promote scientific admission beyond the applicable project gate.


1. Identify the numerical claim and valid regime.
2. Run applicable resolution/timestep/tolerance/solver/seed sweeps.
3. Compare with analytic or trusted references.
4. Record convergence order, stable and unstable ranges, uncertainty, runtime, memory, and environment.
5. Distinguish code defects from method limitations.
6. Update applicable existing numerical rows of `VALIDATION_MATRIX.md`, or return the results to the task owner.
