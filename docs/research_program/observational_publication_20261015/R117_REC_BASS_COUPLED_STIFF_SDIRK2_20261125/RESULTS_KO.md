# R117: coupled chemistry SDIRK and conservative BASS stage opacity

REC commit f67be237187372f4d89fe8c021819a38261b14eb
tree bb886873f49e0e383439ca77ce6642fb08f6a7c0.
BASS commit 5622db58771dbb2dff1e89ccdf1b547fa1d3e27a
tree 85d35cc4a954aaf2281609c151b831607c72c229.
Both owner research branch remote refs verified.
R116-B HTT parent f0220ea86cf7ff798157e48827f1cc53406c6807.

R117 uses Alexander two-stage SDIRK in matched REC difference coordinates.
Existing BE preserved. BASS uses conservative radiation/geometry substeps
at c1=1-1/sqrt(2), c2=1, with linear full bare opacity k=c sigma_T nH xe/H
between each actual pair of stage endpoints. Scalar nonlinear closure
solves the right k simultaneously with REC state, geometry and radiation
response. Stage beta' is actual same-slice dust plus Thomson derivative
rather than finite-difference secant. Preserve mass-shell recoil and accepted
LoS replay; not monolithic SDIRK on all degrees of freedom. Optional
explicit nonuniform macro edges. Thermal and binding energy tracer only.
No automatic adaptive step or phase joins.

REC 141 tests, 21 source-owned standalone cases; matched identical-input
null exact, analytic scalar and nonautonomous stiff thermal checks.
H standalone xe/Tm ratios 4.31677/4.43514; He 3.21289/2.046875, thermal xe
roundoff floor and Tm 5.94824; not uniform second order.

BASS 231 regular + 3 example tests. 33 accepted CLI cases, 5824 stages,
all 12 Bianchi families in short helium overlap, 3 strong early-tilt
domain probes rejected. Max stage bare-rate residual 2.84146e-14,
max independent rate recomputation 0, depth sum defect 2.84217e-14.
Thermal ledger max 9.05431e-31 J/H; raw chemistry state-scaled residual
max 6.40057e-7, not a machine-epsilon nonlinear residual claim.
Gauss 5.45670e-7, Codazzi 7.90678e-9, Jacobi 2.42543e-21.
Uniform coupled H window common-node RMS ratios xe/Tm 3.87424/3.70508;
LoS/depth 3.54237/3.69913 (128/256/512). Thermal nonuniform 32/64/128
eta_j=eta_end*(j/N)^1.3: common-node RMS 4.15822/3.96847,
LoS/depth 4.00342/3.97627. Endpoint xe cancellation/roundoff remains.
Legacy 4 runs, 26 output files byte identical.
Early He probe z=2800 with initial beta=(.1,.03,0), N=128/512/2048
min Sobolev factors on rejected trials -11.1144,-93.3773,-148.4953.
Not an admitted history or proof of nonexistence; positive-expansion
Sobolev closure not usable for these trial states. Resolving frequency
turning/nonmonotone characteristics requires different line transport.

Research receipts and scripts in REC research/r117_sdirk and BASS
research/r117_coupled_sdirk. Raw final local CLI outputs:
~/Downloads/bass_r117_final; reproducible from source slices and scripts.
No native subagent exposed; no independent agent review claimed.
No changes to REI, R78 or unrelated dirty files.
Next R118-NATIVE-COLD-SPECTRAL-MOMENTS-01: photon-number/energy Mellin and
log-temperature moment transport with conservative ledger. Develop
frequency-resolved resonance transfer and nonmonotone characteristics
as follow-on; stiff-uniform/asymptotic and HeIII/phase joins remain open.
