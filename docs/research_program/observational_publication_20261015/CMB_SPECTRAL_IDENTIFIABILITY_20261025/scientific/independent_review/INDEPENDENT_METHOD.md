# R30 independent actual-result review preparation

Status: PREPARATION_ONLY. No numerical checker has been launched. This document is written before inspection of author implementation. Requested reviewer Astra/xhigh; observed runtime UNKNOWN. No prior review or verdict is an input.

## Independent mathematical construction

For a fixed selected finite passband, construct each integral as a sum over adjacent retained nodes: sum_j ((nu[j+1]-nu[j])/2)*(tau[j]*S[j]+tau[j+1]*S[j+1]). Use actual released binary input floats converted by as_integer_ratio; construct stipulated decimal constants anew within each mpmath workdps context. The division by the same trapezoid of the CMB derivative gives the stipulated dimensionless response. Repeating the CMB numerator verifies unity directly.

Synchrotron has logarithm log(b_s)+(beta+2)*log(nu/nu_s); its beta derivatives multiply the spectrum by L_s and L_s squared. Dust has logarithm log(b_d)+beta*log(nu/nu_d)+log(B_nu(T))-log(B_nud(T)). With t=(T-Td)/Td, the first logarithmic derivative at zero is D=g(x)-g(xd), and the second logarithmic derivative is -D-[x*g'(x)-xd*g'(xd)]. Therefore the second derivative of the spectrum is S*(D squared-D-E). This will be tested by direct arbitrary-precision differentiation of the original spectral expression as a function of beta and t, rather than differentiating an author expression or the analytic column formula.

Assemble raw F1 and F2 in the frozen order. All six branch choices are fixed before inspection. Unit-column normalization supplies the computational SVD metric. Check the complete singular spectra, augmented rank, pseudoinverse projection, quotient weights, least-squares witness, and deterministic QR minor. A resolved threshold crossing yields numerical rank of this finite model only.

Use explicitly formed A=kron(ones(7,1),I24), B=kron(F,I24) and H=kron(w^T,I24). Evaluate every column of H*A-I24 and H*B. In the full-row-rank case evaluate A*v+B*(-kron(c,v)) for each signed coordinate basis vector; save all 24 residuals. The algebraic conditional statement follows independently from P*A=(P_F*a) tensor I24: rank is 24 if the nonzero frequency vector P_F*a exists, otherwise zero. No claim of physically realizable unconstrained signed moments follows from this relaxation.

Check nonzero column scalings, nesting, CMB unity, pivot zeros, the synthetic duplicate-column and injected-CMB controls, and all promised qualifier domains. Read author outputs as comparison candidates, never as independent evidence. Author checker will neither be imported nor executed.

## Execution gate and evidence

Actual execution requires fresh controller review packet, ACK, root GO and settled account head. One independent checker only, complete supervisor enclosure at most 90 seconds with kill/reap/flush tail inside the cap, one BLAS/OpenMP thread, an enforced 1 GiB process address-space ceiling with scope reported, observed peak RSS, MemAvailable at least 4 GiB, free disk at least 2 GiB. No retries or additional scientific invocation. Record every started command once; overlapping tool/supervisor intervals are alternative observations, not additive charges. Charge authoritative settled enclosure equally to the same seven source-frequency accounts; no SMICA increment or new bank. Resource enforcement and historical observed compliance are evaluated separately from numerical validity.

## Review ceiling

This review can decide only the frozen finite-model spectral discriminator. Physical x and observed tensor NOT_MEASURED; Q NOT_EVALUATED; F_physical NOT_EVALUABLE; Pi NOT_CALIBRATED; G_F NOT_APPLICABLE. Actual sky, calibration, omitted moments, blackbody contaminants, response uncertainty, null/covariance gates and campaign scientific acceptances remain outside admission.
