# Phase 8 — Numerical and Reproducibility Validation

Select checks that can falsify the numerical claim: grid/timestep convergence, precision sweep, solver/initialization sensitivity, conditioning/stiffness, NaN/Inf handling, singular limits, sampling and ensemble uncertainty. Separate truncation, iteration, roundoff and sampling errors. For JVP/AD use an independent directional derivative and step-size sweep, detect cancellation and truncation windows, and preserve primal/pair and projection semantics.

Identify shared code, inputs, coefficients or interpolation in reference comparisons. Record stable/unstable regimes, actual environment/commands/exit, seeds and resources. Do not fabricate performance or cost. Relevant sufficient evidence terminates optional sweeps; an unchanged failing rerun does not replace diagnosis.
