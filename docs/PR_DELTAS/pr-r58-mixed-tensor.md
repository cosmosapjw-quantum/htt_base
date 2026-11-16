# R58 scoped delta

Problem: polar and STF likelihoods were separated while the owned CF4 catalogue has material cross covariance; direct kinematic x existed in R39 but was not carried through this mixed observation.

Change: preserve full32 covariance, fit11 apparent coefficients, pull back to22 normalized kinematic+calibration coordinates with explicit11-dimensional kernel; typed five views; R54 theorem-domain and overflow repairs. Standard GLS is the exact-likelihood comparator and ties.

Validation: see R58/VALIDATION.json and independent REVIEW receipts. Existing frozen results and caches unchanged.

Scope: C0 conditional selected-sample application; no cosmological detection/Bianchi family/global tilt identification. R59 native replay/manuscript is sole terminal successor.
