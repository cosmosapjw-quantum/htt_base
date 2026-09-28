# R2 first failures and scope

- Initial broad web searches returned irrelevant results. They were not used as scientific sources. Direct verified arXiv sources were opened next; raw result retained in evidence/OWNER_TOOL_EVIDENCE.json.
- Python current turn passed. First symbolic script invocation failed with `ModuleNotFoundError: sympy`; primary-runtime Python had the same missing package. Classification: PACKAGE_MISSING, not runtime unavailable. No dependencies installed. Exact stdlib/Wolfram route selected.
- Wolfram first optical check produced unsimplified expressions and undefined-symbol warnings (symbolic H and P); inverse/norm residuals simplified to zero. The first owner attempt to wrap FullSimplify used an unmatched closing bracket and returned `$Failed` (implementation syntax error, not physical failure). Corrected call returned all zero residuals with symbolic warning retained. Raw calls/results preserved.
- No previous native-client mismatch, runtime transport failure, repository scientific verdict or VIGILODE dependency was inherited.

- Independent decision review found an actual reference-translation error: the candidate constrained k in B although B was defined for k−k_ref. Corrected main Eq.(29) and statistics §7 to k−k_ref in B, explicitly preserving k_ref+B. V1 report/statistics and identities remain in evidence. Added explicit curvature-commutator sign convention.
