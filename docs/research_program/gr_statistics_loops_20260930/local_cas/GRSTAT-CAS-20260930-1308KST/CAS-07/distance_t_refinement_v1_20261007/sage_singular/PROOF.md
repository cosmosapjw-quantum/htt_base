# CAS07 M06: SageMath and Singular exact certificates

This axis uses only the frozen M06 contract and admitted M01, C03-FD1, and M05 statements. Let `e_s=eta_K(s)`, `e_t=eta_K(t)`, `e_L=eta_K(L)`, `h=|H0|`, `delta=1-e_L`, and `q=dA/delta`. The admitted `e_L<1` makes `delta>0`; `c>0` permits multiplication by `2c`. Every inequality below is over the declared real domain.

M01 gives `0<=e_s<=e_L<1`, while M05 gives `dA>=s(1-e_s)`. Sage and Singular both verify the exact identity

`dA-s delta = [dA-s(1-e_s)] + s(e_L-e_s)`.

Both terms on the right are nonnegative, so `q>=s`. On the branch `q<=L`, `t=q>=s`. On the branch `L<=q`, `t=L>=s`. Thus `s<=t<=L` and `t>0`. Applying M01 again yields `0<=e_s<=e_t<=e_L<1`.

Write `F(r)=M2*r^2/2+h*r*eta_K(r)/c`. Sage and Singular check the polynomial identity obtained by multiplying `F(t)-F(s)` by `2c`:

`M2*c*(t-s)*(t+s) + 2*h*[(t-s)*e_t+s*(e_t-e_s)]`.

Every factor is nonnegative because `M2,h>=0`, `c,s,t>0`, and M01 supplies the order. Hence `F(s)<=F(t)`. The accepted C03-FD1 inequality at `s` then gives the contracted refined FD1 inequality at `t`.

Since `t=min(L,q)`, `t<=q`. The admitted FD2 right side is exactly `M2*q^2/2+h*q*e_L/c`. Sage and Singular check that multiplying its difference from `F(t)` by `2c` gives

`M2*c*(q-t)*(q+t) + 2*h*[(q-t)*e_L+t*(e_L-e_t)]`.

All factors are nonnegative, proving that the refined right side is no larger than FD2. The formulas remain valid when `h=0` or `M2=0`; neither needs a strict lower bound.

For `K=0`, M01 gives `e_s=e_t=e_L=0`. Both admitted M05 distance inequalities then force `dA=s`. Thus `q=s`, `t=min(L,s)=s`, and the refined bound equals FD1. The boundary `e_L=1` is excluded exactly as in the contract.

`proof_sage.py` checks the identities over `QQ` and its fraction field. The pinned Singular 4.4.1 binary independently returns zero for the polynomial identities and for the ratio/domain relation reduced modulo `q(1-e_L)-dA`. The runner inspects Singular's entire raw stdout and stderr, not just exit status, and records them under `direct_execution/`. This proves the contracted algebraic composition conditional on the admitted analytic theorems; it does not reprove those dependencies or establish physical or observational admission.
