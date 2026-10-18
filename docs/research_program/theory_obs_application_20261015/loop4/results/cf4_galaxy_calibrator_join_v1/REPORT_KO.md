# CF4 Table2 개별 직접 보정 관측과 Table3 그룹 결합의 source join

Table2 actual individual rows: 55877; method values: {'TRGB': 446, 'Cepheid': 69, 'SNIa': 1004, 'Maser': 6}.
Group direct calibrator DMcal count: 336; same group DMav exists: 108; direct-only: 228.
Literal 1PGC group join with at least one individual TRGB/Cepheid/Maser datum: 311/336.
Unresolved literal group IDs: 25. A valid group-level calibration uncertainty cannot be assumed for them.
Naive inverse individual-error mean vs published DMcal matches <=0.001 mag for 257/311 linked groups.
95th percentile abs discrepancy: 0.085313 mag; maximum 1.6804 mag.

The released per-galaxy sigma_i is not the covariance among TRGB/Cepheid/Maser methods, LMC calibration or galaxy-group memberships.
Therefore neither the 311 linked groups nor the 108 overlap groups are certified independent absolute zero-point measurements.
For numerical inference, keep the original release group DMcal/DMzp provenance and construct a joint calibrator covariance before treating overlaps as an external zero-point prior.
