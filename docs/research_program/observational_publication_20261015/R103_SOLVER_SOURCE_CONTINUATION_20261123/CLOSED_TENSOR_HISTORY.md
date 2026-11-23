# Common-history closed tensor benchmark

The compiled AniCLASS solver supplies a regular tensor history for a closed IX perturbation at `Omega_k=-0.01`. The spatial curvature radius is 44210.656 Mpc. The field varies with redshift, the Thomson rate drops through decoupling and rises again during reionization, and the spin-2 rotation continuously mixes E and B. In this geometry the tensor hierarchy closes at the quadrupole. All exported multipoles from degree 3 through 6 vanish in the reference trajectory.

Set the dimensionful clock to conformal length $t=c\eta$ in Mpc. In AniCLASS's raw tensor basis $U=(\Theta_2,E_2,B_2)$, the prescribed-field equation is

$$
\frac{dU}{dt}=
\left[
\frac{2}{\ell_c}
\begin{pmatrix}0&0&0\\0&0&-1\\0&1&0\end{pmatrix}
+\kappa'(t)
\begin{pmatrix}-9/10&-\sqrt{6}/10&0\\-\sqrt{6}/10&-4/10&0\\0&0&-1\end{pmatrix}
\right]U-\begin{pmatrix}h'(t)\\0\\0\end{pmatrix}.
$$

Here $h'$ is the actual `Hdot (gwdot)` column of the compiled tensor solver in inverse Mpc and $\kappa'>0$ is the Thomson scattering rate per Mpc from its thermodynamics output. The two matrices do not commute. The native geometry uses $n_{ij}=2\delta_{ij}/\ell_c$, with the raw upstream components mapped to native coefficients by $\mathrm{diag}(1,-1,-1)$ in the isolated $m=2$ block. The code reads the exact $k$ chosen by AniCLASS for IX and checks $k=\sqrt{6}/\ell_c$ against the donor background. It reads both real and imaginary components. This orientation has a real solution.

Use the donor $U$ once, at $z=1601.419$, after the tight-coupling approximation. Hold out the later photon multipoles. Read $h'$ and $\kappa'$ by shape-preserving interpolation and sample them at the midpoint of each cell. The actual BASS SDIRK propagator evolves the native Stokes state to four later redshifts, 1102.12, 598.39, 7.99968 and 0. Errors below are the largest absolute checkpoint discrepancy for a channel divided by the maximum absolute donor amplitude in that channel across the sampled interval. They are independent of an unstable relative error at a zero crossing.

| Actual cells | T | E | B |
|---:|---:|---:|---:|
| 67 | 3.43e-4 | 2.07e-3 | 1.68e-3 |
| 131 | 8.20e-5 | 8.55e-4 | 9.50e-4 |
| 259 | 2.21e-5 | 1.86e-4 | 4.61e-5 |
| 515 | 5.52e-6 | 4.63e-5 | 1.20e-5 |

The benchmark exercises transport on one regular closed tensor **using the same supplied metric and thermodynamics**. Future self-consistent comparisons need E/ν stress and metric initial data at the matching time, consistent densities and visibility, and a BASS-sourced metric and opacity. Open-space higher-multipole transport is a separate comparison.

```bash
export PYTHONPATH="$PWD/htt" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
.venv/bin/python scripts/r103/closed_tensor_history.py \
  --aniclass-root /home/cosmosapjw/workdir/htt_external_physics_20261015/reference_code/AniCLASS \
  --output /tmp/htt_r103_closed_tensor_history.json
```

The runner hashes all donor products, records the binary and native transport source identities, and exits nonzero if the 515-cell error exceeds $2\times10^{-4}$ in any channel. It generates fresh temporary donor inputs and outputs for each run. [Vicente, Pereira & Pitrou](https://arxiv.org/html/2506.07786v2). [AniCLASS source](https://github.com/jgvicente/AniCLASS/tree/be1e43fcb1d7549710ba3ca2baa74bb0216bd228).
