# CAS-03-C03 domain counterexample

Source: published contract `cas/contracts/CAS-03.json` at commit `11602167b64e4f0c50c1f57c37fe9df2292f9725`. The local execution contract is `EXECUTION_CONTRACT.json`; its SHA-256 is recorded in `ADJUDICATION.json`.

The contracted component says: “For arbitrary invertible D=H I+sigma, verify the linear relation h1=-2D beta and inverse beta=-D^-1 h1/2; the truncated inverse has defect sigma^2 beta/H^2. Verify the rational diagonal negative control. An O(beta^2) remainder needs a separate bounded Taylor argument.”

Take `D=diag(1,1,-2)`, `H=tr(D)/3=0`, and `sigma=D`. The matrix is invertible (`det D=-2`) and `sigma` is trace-free. The exact inverse exists, but the stated truncated expression and its defect divide by `H^2` and are undefined. This is a domain omission in the combined component, not a counterexample to the exact inverse relation. A future contract version would need to state `H != 0` for the truncated expansion and run all four axes again under that new hash.

The SymPy axis computed the determinant and trace exactly in `sympy/run.py` and retained its raw output in `sympy/raw.log`. The observed four-axis verdict remains `CAS_CONFLICT`. No original research file, published contract, HOLD status, or scientific claim was changed.
