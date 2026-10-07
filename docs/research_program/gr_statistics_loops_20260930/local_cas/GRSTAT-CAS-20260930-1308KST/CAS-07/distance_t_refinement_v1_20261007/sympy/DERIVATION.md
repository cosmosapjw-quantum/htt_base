# CAS-07 M06 SymPy derivation

This axis reads only the frozen execution contract and admitted inputs.  Put
`q=d_A/(1-eta_L)` and `t=min(L,q)`.  The admitted facts give
`1-eta_L>0`, `d_A>=s(1-eta_s)`, and
`0<=eta_s<=eta_t<=eta_L<1` after applying accepted M01 monotonicity on
`s<=t<=L`.

For the `t=q` branch,

`q-s = [d_A-s(1-eta_s)+s(eta_L-eta_s)]/(1-eta_L) >= 0`.

For the `t=L` branch, `s<=t` is the admitted `s<=L`.  Each branch has
`t<=L`, and positivity follows from `L>0` or from `d_A>0` and
`1-eta_L>0`.  Accepted M01 then yields the contracted eta ordering.

Writing `h=abs(H0)`, exact expansion gives

`FD1(t)-FD1(s) = M2(t-s)(t+s)/2
                  + h[(t-s)eta_t+s(eta_t-eta_s)]/c >= 0`.

The accepted C03 FD1 bound at `s` therefore implies the refined bound at
`t`.  Finally `t<=q` and `eta_t<=eta_L`, and exact expansion gives

`FD2-FD1(t) = M2(q-t)(q+t)/2
               + h[(q-t)eta_L+t(eta_L-eta_t)]/c >= 0`.

At `K=0`, accepted M05 reduces to `d_A=s`, so `q=s` and `t=s` because
`s<=L`.  The script also checks the `H0=0` and `M2=0` reductions exactly.
Its high-precision vectors exercise both minimum branches and `K=0`; they
are supplementary sanity checks, not the universal proof.
