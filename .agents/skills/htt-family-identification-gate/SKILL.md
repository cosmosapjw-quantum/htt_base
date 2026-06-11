---
name: htt-family-identification-gate
summary: Guard Bianchi geometry and family-identification claims against premature scalar, directional, or external-transfer-only evidence.
description: Use whenever a PR, report, figure, likelihood, or manuscript text mentions Bianchi family identification, geometry candidate, equivalence classes, native transfer atlas, BiPoSH morphology, or family ranking.
---

# HTT Family Identification Gate Skill

## Purpose

Make family identification hard in the right way. The project may explore family compatibility before the native low-ell solver, but must not claim identification without morphology and null gates.
FORBIDDEN before C6 gates: family identification, geometry detection, or family
ranking from scalar, directional, or external-transfer-only evidence.

## Claim ladder

- C0 raw anomaly.
- C1 scalar departure.
- C2 certified filling.
- C3 depth/direction diagnostic.
- C4 global-tilt candidate.
- C5 background-anisotropy morphology compatible.
- C6 post-native-atlas, externally-gated Bianchi geometry/family-identification claim.

Before external/native low-ell solver outputs enter, PRs may at most target C3/C4 unless they are purely synthetic/methodological demonstrations.

## Required gates for C5/C6

External-transfer morphology compatibility may reach C5 only when explicitly
transfer-conditional. C6 Bianchi geometry/family identification requires a
native low-ell morphology atlas plus null/mask/covariance/equivalence/rank/PPC
gates.

1. Native transfer provenance for C6; explicitly transfer-conditional external
   transfer provenance for C5 morphology compatibility only.
2. `a_lm` template or anisotropic covariance/BiPoSH support.
3. TE/EE/BB compatibility status, or explicit channel limitation.
4. local boost/systematics nulls.
5. equivalence-class graph.
6. response-rank / nuisance-projection audit.
7. PPC/LOOCV or held-out probe check for HTT inference.
8. MIO diagnostic cross-check without posterior merge.
9. figure/manuscript claim-tier labels.

## Required output

```markdown
## Family-identification gate verdict

## Requested claim tier

## Allowed claim tier

## Missing gates

## Equivalence-class risks

## Transfer/source risks

## Required downclaim or next PR
```

## Hard prohibitions

- FORBIDDEN: Largest Bayes factor is not family identification.
- FORBIDDEN: Scalar `D_l`, `x,Q,Pi,F,G`, or direction coherence alone cannot identify a Bianchi family.
- FORBIDDEN: External AniCLASS transfer cannot be silently described as native solver evidence.
- FORBIDDEN: A diagnostic MIO certificate cannot upgrade HTT posterior odds.
