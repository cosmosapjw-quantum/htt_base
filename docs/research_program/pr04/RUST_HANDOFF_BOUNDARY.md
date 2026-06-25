# New Rust project boundary

## Salvage candidates

Independently testable numerical and representation utilities may be ported:
LU/sparse kernels, PSTF/STF indexing, tensor containers, source/config schemas,
and selected quadrature utilities.

## Quarantined science outputs

Do not import old FLRW/Bianchi spectra, family evidence, atlas ranking,
truth-engine values or hard-coded HTT/MIO bridges into validation.

## Required golden contracts

1. exact flat-FLRW background and perturbation comparator;
2. Lorentz/frame and STF round-trip contracts;
3. Bianchi-I constraint transport and shear-memory fixtures;
4. collision/visibility conservation and positivity checks;
5. transfer convergence with independent comparator;
6. truthful family x mode x orientation support matrix.

The future Rust code is a separate long-term project and does not block PAPER-A
or PAPER-B.
