# Physmath harness integration map

| Upstream surface | Repository use | Authority rule |
| --- | --- | --- |
| coding phase prompts | Reproduction, bounded implementation, validation and independent-diff checklists | `AGENTS.md` and PR card override |
| research phase prompts | Evidence acquisition, hypothesis graph, adversarial review and closeout templates | Initial/final CRAG windows and web lock override |
| generic upstream skills | Inert reference material only | Never copied to root `.agents/skills` |
| upstream state templates | Shape examples for the audit package | Repository manifest schema is controlling |
| upstream initializers | Not activated | Never run in repo or immutable vendor roots |
| upstream validators | Vendor-integrity smoke checks | Run read-only after static review |

The active entrypoint is `.agents/skills/htt-physmath-audit/SKILL.md`. It binds
the upstream workflow to COMMON ownership, HTT/MIO separation, OBSSTAT feature
scope, transfer provenance, fail-closed execution receipts, and the C6 family
gate. Counterfactual family/geometry exploration is allowed only as
`hypothesis_only`, `public_use=false` audit material.
