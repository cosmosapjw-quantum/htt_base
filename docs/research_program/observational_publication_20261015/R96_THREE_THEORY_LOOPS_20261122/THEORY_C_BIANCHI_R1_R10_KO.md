# R96-C: Bianchi multipoles and spin-2 m-blocks, theory R1–R10 (executed bounded route)

**Scope:** reuse R49 12-family tilted Einstein–Euler, R95 source-qualified HyRec2+tanh visibility and BASS exact Thomson + original legacy PR13AG finite-L numerics. Expand spin-2 free-streaming to explicit m=-2..+2, ell_max=8,16,32,60, not general all-m tilted Bianchi likelihood. Signature (-,+,+,+), k in inverse comoving Mpc, eta in comoving Mpc, shear amplitude dimensionless H-normalized, c restored in background H(z) to conformal 1/Mpc.

**R1 · Target.** Implement the missing azimuthal and magnetic polarization degrees of freedom in an auditable source kernel while preserving original R95 m=0 T+E constraints and physical claim ceiling.

**R2 · Literature and reuse.** Pontzen & Challinor (2007), Bianchi multipole hierarchy: https://arxiv.org/abs/0706.2075 . Sung & Coles polarization/observer-frame transport: https://arxiv.org/html/0905.2307v2 and https://arxiv.org/html/1004.0957v2 . Saadeh et al. coherent Bianchi polarization limits: https://arxiv.org/abs/1604.01024 . Source: scripts/r95/bianchi_polarized_hierarchy.py, BASS bianchi/matter/hierarchy.py, bianchi/q/polarization.py and legacy PR13AG_projected_multipole_solver_restoration.py. PR13AG visibility/shear input is synthetic, not a physical Bianchi source.

**R3 · Representations.** T multipoles use spin 0. Polarization P_+=-(E+iB) and P_-=-(E-iB) use spin +2,-2; helicity is not a scalar. A single m=0 T+E background cannot establish m!=0 B-mode transport. The R95 analytic 11,155-dimensional all-m *capacity count* is not an executed all-m system.

**R4 · Alternative models.** A: current R95 120-state m=0 T+E sparse hierarchy at L=60. B: independent m-block exact spin-weighted spherical streaming including B, using sparse LU and real HyRec2 visibility. C: full curved Bianchi geodesic direction/m-screen precession producing m<->m' couplings, matter radiation sources and multi-k topology, not completed here. Use B as concrete preparation for C, not its surrogate.

**R5 · Derivation.** For s=0,±2:
\[
\cos\theta\,{}_sY_{\ell m}
 = c_{\ell+1}^{sm}\,{}_sY_{\ell+1,m}
 + c_{\ell}^{sm}\,{}_sY_{\ell-1,m}
 - {s m\over\ell(\ell+1)}\,{}_sY_{\ell m},\quad
 c_\ell^{sm}={\sqrt{(\ell^2-m^2)(\ell^2-s^2)}\over \ell\sqrt{(2\ell-1)(2\ell+1)}}.
\]
With \partial_\eta P_s=-ik\cos\theta P_s and P±=-(E±iB), the m diagonal produces E'=k d_m B and B'=-k d_m E with d_m=-2m/[ell(ell+1)], in addition to complex off-diagonal \ell<->\ell±1 transport. For m=0 or k=0 this term vanishes. The T2/E2 Thomson block from R95 is [[-.9,-sqrt(6)/10],[-3/(5sqrt(6)),-.4]] with eigenvalues -1,-0.3. B damping is -1 in this simplified collision model. In absence of collision, the streaming generator is skew-Hermitian and preserves coefficient norm.

**R6 · Exact and numerical oracles.** The recurrence was evaluated with BASS/R49 spin-weighted harmonics at independent angles, max error 1.78e-16; Wolfram exact c_4^{s=2,m=2}=1/sqrt(7) and 2m/[l(l+1)]=1/5. The streaming matrix satisfies A+A^†=0 to machine precision. For k=0 or m=0, B remains zero with zero initial B. Real STF sky source coefficients have a_2,-m=(-1)^m a_2m*, separately tested.

**R7 · Actual sparse integration.** scripts/r96/spin2_mblock_extension.py uses actual R95 HyRec2+tanh visibility and source time grid, sparse CSC/LU backward Euler. L in {8,16,32,60}, m in {-2,-1,0,+1,+2}, with constructed STF quadrupole source normalized to sigma/H=1e-4 and k=0.002 Mpc^-1. Actual full run 20 blocks in ~0.55s at this scale. Output signed complex T2,E2,B2 coefficients, all-mode norm, B/E power proxy and convergence proxies. L60 m0 B=0 exactly; nonzero m have finite B from free streaming. No actual R49 shear history was extrapolated to recombination redshift.

**R8 · Scientific claim.** Mathematically derived and numerically checked all-five-low-m *axisymmetric free-streaming* spin-2 model. It is not a fully coupled curved tilted Bianchi all-m T/E/B solver. Nonzero B/E is an internal modal response, not a cosmological B-mode detection or source-qualified C_l prediction. State spaces for all m>2 and coupling by general Bianchi Lie structure are not executed.

**R9 · Computational form.** For each m, state y_m=(T_{ell m},E_{ell m},B_{ell m}) and solve (I-\Delta eta[A_m + tau_dot K_m]) y^{j+1}=y^j+\Delta eta S_{2m}(eta_j) with sparse LU. R95's actual Born/Thomson source and R49 general tilted state history must enter via a source mapping with time/frame/c boundary and rotation convention. Separate numerical cutoff error, stiff collision error, physical source model error, and external PR3/SMICA foreground/mask errors.

**R10 · Result and cheapest next production work.** SPIN2_MBLOCK_HIERARCHY.json and scripts/r96/spin2_mblock_extension.py with physics-focused tests. Next: project full R49 4D connection/BASS screen onto spherical spin harmonics, build sparse \Delta m=0,±1,±2 coupling matrices and check proper SO(3), handedness, current conservation, Thomson and E/B parity in Type I/V/VII_h/VI_-1/9/IX; attach REC/REI source-qualified photon perturbations and real geometry histories. Native all-m B02–B05 still BLOCKED_SOURCE/MODEL, not numeric feature PASS.
