---
name: htt-plot-provenance
description: Generate or review plots with manifests, source JSON, and allowed-use lanes.
---

Use this skill only inside the HTT/Bianchi pre-native-low-ell-solver revision workflow.

Rules:
- Do not make family-identification or anisotropic-geometry claims without native morphology atlas, covariance, matched masks, nulls, PPC/LOOCV, and equivalence-class gates.
- Prefer meaningful diagnostic/conditioned artifacts over disclaimer-only patches.
- Every plot or table must include owner, claim tier, artifact mode, allowed use, transfer source, null status, covariance status, and forbidden uses.
- Separate HTT posterior/evidence from MIO certificates.
- Separate deterministic-template likelihoods from stochastic covariance likelihoods.
