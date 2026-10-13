# OBS-07 sensitivity independent review

Decision: `PASS_SCOPED_MANUFACTURED_SENSITIVITY`. Physical OBS-07 bridge and certified remainder remain `HOLD`.

The reviewer was read-only and separate from the implementation author. Requested reviewer: `gpt-6-astra/xhigh`; observed runtime identity: `UNKNOWN`. The manufactured values theta_hat=0.2, SE=1/sqrt(3), box support 4rho/3 and ellipsoid support 2sqrt(2)rho/3 were independently verified. All eight box corners, the ellipsoid extremizer, and all sixteen interval endpoints agreed with a 70-digit calculation within absolute tolerance 1e-14. Four focused tests passed. The reviewer inspected the PNG against the JSON and generating code; no summed support or coverage claim appears.

Final reviewed SHA-256: script `d2ac2db4e7419baee5f66a9999fbbf90d5811b1d9c87c7d4e734c5f85dcf39fb`; test `dd60aa7542982487af85a81b184be5d86adefd95e8c8c1d736be5fb502121c54`; sensitivity JSON `efce1dda75f129c356c1e4260d7d314f3e1a8fd709f6bdc8a6faaa74a79cf9bc`; PNG `afcbfa16ce7828c151fd53240c8468ef97ee7917c13a6f95bd41572444d9687a`; corrected execution JSON `4b4bcec5505631f6e4ce3686c16fe1c7bf4f19cfbd7ad0bd731f8835f1d786b1`.

The first serialization failure is represented by a summary only. Its raw traceback is `UNAVAILABLE` and cannot be independently verified. The supplied bias radii are assumed dimensionless sensitivity inputs, not measured physical limits. No K, M2, L or CF4 remainder certificate was produced.
