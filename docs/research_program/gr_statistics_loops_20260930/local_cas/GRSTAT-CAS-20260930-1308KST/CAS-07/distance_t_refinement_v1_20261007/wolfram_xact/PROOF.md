# CAS-07 M06: Wolfram+xAct axis

Contract `e4169b089e5c19accb838e3b43daa0fe44bfab43b0a5025a3167280069a6eb13`, admitted inputs `9c85a30bdde1a294930ae40009b121e0e1a767a5c2d5e97fa9e27a3dc14b5bd3`, and `COMMON_SPEC` `4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897` control this axis. The accepted M01, C03, and M05 statements are premises. Their proofs and other axes are outside this axis. The result is a distance-only analytic component; scientific admission remains `HOLD`.

Write `e_s=eta_K(s)`, `e_t=eta_K(t)`, `e_L=eta_K(L)`, `q=1-e_L`, `D=d_A/q`, and `B=|H_0|/c`. The domain gives `q>0`, `B>=0`, `M_2>=0`, `0<s<=L`, and `0<=e_s<=e_L<1`. From accepted M05 and M01,

```text
d_A >= s(1-e_s) >= s(1-e_L) = s q,
```

so `D>=s>0`. If `L<=D`, then `t=L` and `s<=t<=L`. If `D<=L`, then `t=D` and again `s<=t<=L`. The two branches cover all real `D`. Only after obtaining this domain do we instantiate accepted M01 at `s,t,L`: `0<=e_s<=e_t<=e_L<1`. This is an application of an accepted theorem, not an assumption that the M06 target already holds.

Accepted C03 gives `|Z-Z_0-H_0 d_A/c|<=F(s)` with `F(r)=M_2 r^2/2+B r eta_K(r)`. Exact algebra yields

```text
F(t)-F(s)
  = M_2 (t-s)(t+s)/2
    + B ((t-s)e_t + s(e_t-e_s)) >= 0.
```

Every factor is nonnegative on either min branch. Therefore the refined FD1 inequality follows. Since `t<=D` and `e_t<=e_L`, exact algebra also gives

```text
FD2_rhs-F(t)
  = M_2 (D-t)(D+t)/2
    + B ((D-t)e_L + t(e_L-e_t)) >= 0.
```

The Wolfram source checks both identities and both branch signs symbolically. It proves denominator positivity before using `D=d_A/q`. It also checks the `H_0=0` and `M_2=0` limits. For `K=0`, the accepted definition has `e_s=e_t=e_L=0`, and both sides of accepted M05 give `d_A=s`; hence `D=t=s` and both right sides equal `M_2 s^2/2`. The `eta_L=1` case is excluded by the frozen domain.

Units are consistent: `D,t,s,L,d_A` have length; `M_2 r^2` and `|H_0|r/c` are dimensionless. The scalar inequalities do not use a Lorentz norm. The xTensor run independently checks the 2-dimensional metric/inverse contraction `g^{ab}g_{ab}=2` as a package sanity check; it supplies no premise to the scalar proof.

The first raw attempt is retained: Wolfram rejected the initially chosen symbol `D` because it is protected for differentiation. The second attempt exposed an insufficient `FullSimplify` decomposition. The final source uses the admitted two-sided M05 statement and explicit nonnegative factors. All raw attempts remain under `attempts/`; `result.json` identifies the successful one.
