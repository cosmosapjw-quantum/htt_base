# Neutral author brief — CAS11-C02 v3

This is an execution instruction, not a proof or a previous verdict. The byte-frozen attached contract is the mathematical authority. It has SHA-256 `c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a`.

Your axis is assigned separately as exactly one of `wolfram_xact`, `sympy`, `sage_singular`, or `lean`. Use only that axis's engine/proof environment and permitted neutral inputs. Work in the existing primary checkout, with a disjoint own-axis output directory and fresh author context. Do not create another checkout or spawn children.

For every positive integer n, every real symmetric PSD n-by-n matrix R, every real vector e and every real ε≥0, verify the forward implication from

    for every a in R^n, |a^T e|^2 <= 2 ε a^T R a

to

    e belongs to range(R), and e^T Rdagger e <= 2 ε.

Use the contract's spectral definition of the real symmetric Moore–Penrose pseudoinverse. PSD is an input assumption; any repeated PSD output acknowledges it rather than establishing physical provenance. Include positive definite, singular nonzero and zero R, ε=0 and ε>0, and all intersections. Do not assume range membership or the desired bound. Do not replace a universal quantifier by finitely many probes. The reverse implication is not an assigned target.

Preserve the contract's assumptions and exclusions. No singular inverse substitution, unchecked division by a possibly zero expression, numerical-only proof, `sorry`, `admit`, or newly assumed target-equivalent axiom is permitted. Where an engine verifies only a reduction or component, explain the unverified remainder explicitly. Fixed-dimension success alone is not full coverage.

Permitted mathematical inputs are the exact contract and its declared neutral specifications. Do not read Host derivations, Host coverage notes, old scripts/results/reviews, sibling work or repository-wide search results exposing them before adjudication. Record any accidental exposure immediately. Requested model/profile is not proof of observed authorship.

Return own-axis source, actual invocation and engine version, complete raw stdout/stderr, imported lemma/dependency list, statement alignment, arbitrary-dimension/rank coverage, and explicit gaps or counterexamples. Seal the source hash before the final observed invocation. Historical evidence must not be copied as a new execution result.

The existing runner expects exactly the obligation key `CAS11-C02-FINITE-GRAM` under `checks`, plus `domain_assumption_diff` and `counterexample`. A successful completed evaluation emits one stdout JSON document; engine banners and complete logs are saved separately. Never emit success from constant checks or unproved assertions. Incomplete proof or missing engine output is not a mathematical false result: preserve the actual error/nonzero exit and a separate coverage report without fabricating a scientific-failure payload. Host adjudication retains the runner's raw classification and the explanation separately.

This finite component does not establish C01/C03, physical derivative bounds, continuum closure, noise covariance, observational inference, novelty or scientific admission.
