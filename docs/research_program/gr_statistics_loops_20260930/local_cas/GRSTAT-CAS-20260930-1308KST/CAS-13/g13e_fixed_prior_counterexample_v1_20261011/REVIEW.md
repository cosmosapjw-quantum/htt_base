# Independent review — G13-E exact certificate

Verdict: `PASS_SCOPED_CERTIFICATE`.

The reviewer was requested as `gpt-6-astra/ultra`; observed model and effort
are `UNKNOWN`.  It independently reran the frozen SymPy script with exit 0,
empty stderr, and byte-identical stdout.

The exact source, packet, script, and raw-output hashes match the receipt.  The
review confirms the lower-node equation
`20625*u^3 - 9700*u^2 - 7760*u - 6208 = 0`, the Sturm isolation interval
`(539/500, 1079/1000)`, the required lower-node domain, both lower endpoint
expressions, and the strict exact comparisons:

- `L5 - frame5 >= 58571515929/6450285156250 > 0`;
- `L6 - frame6 >= 37245342523/1320312500000 > 0`.

These are rational/Sturm/Bernstein certificates, not decimal comparisons.  They
support only the frozen Maxwell--Boltzmann fixed-prior counterexample: the
matched frame can lie below the two fixed-fugacity mixture lower bounds.

The reviewer corrected an initial diagnostic that incorrectly required strict
positivity at closed enclosure endpoints; the corrected nonnegative enclosure
check passed.  Candidate files were not changed.

Excluded: Lean formalization, full G13-E, FD/BE inversion, historical four-axis
adjudication, publication-level scientific claim, and scientific admission.
