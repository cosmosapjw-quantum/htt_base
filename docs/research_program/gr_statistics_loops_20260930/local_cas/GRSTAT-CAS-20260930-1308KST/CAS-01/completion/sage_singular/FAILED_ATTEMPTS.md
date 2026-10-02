# Development failures retained

The first executed run of `sage -python run.py` exited 1 at the C01 certificate with `AttributeError: 'sage.modules.free_module_element.FreeModuleElement_generic_dense' object has no attribute 'reduce'`. The cause was Sage vector multiplication and matrix iteration yielding vectors where scalar or flattened component polynomials were required. The script was corrected to use `dot_product` and matrix `.list()`.

The next executed run exited 0 and emitted `{"checks":{"CAS-01-C01":false,"CAS-01-C02":true,"CAS-01-C03":true,"CAS-01-C04":true},"counterexample":null,"domain_assumption_diff":[]}`. Its certificate showed `null_cone_kernel.converse_sage=false`. The cause was taking `dict().values()` from a polynomial ring that included the symmetric-form entries as variables; those values were rational scalars, which made the resulting coefficient ideal invalid. The script now groups monomials by the three sphere-variable exponents and reconstructs coefficients as polynomials in the form entries. The final run tests both ideal containments in Sage and Singular.

These development observations are recorded from the executed command outputs. They are not relabeled as final engine evidence.
