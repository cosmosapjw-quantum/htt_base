# R114 HOLD Design Specifications (`T1`–`T5`)

> **Status: HOLD (design specifications only; no production code written or promoted).**
> Each specification documents exact equations, data contracts, failure modes, and gating
> requirements prior to implementation. Off-axis / non-`{FLRW, I, V, IX}` Python PSTF dispatch
> in `htt_base` remains fail-closed under `T5`.

---

## T1. Helium & Matter Temperature as Evolved Variables of the Matched Step

### 1.1 Current Scope and Missing Physics
- `rec_microphysics::matched_history::implicit_matched_step` (`rust/rec_microphysics/src/matched_history.rs`)
  currently integrates only the hydrogen ionized fraction perturbation
  $x_p(\eta) = x_{\rm ref,H}(\eta) + \delta x_e(\eta)$ at **Compton equilibrium**
  $T_m(\eta) = T_C^{\rm aniso}(\hat{n})$ (`compton_temperature_k`), leaving helium fixed at the
  tabulated FLRW HYREC baseline.
- Below $z \sim 800$ (Compton cooling timescale $\gtrsim H^{-1}$) and around He II/He I
  recombination ($z \gtrsim 1600$), keeping $T_m = T_C$ ignores adiabatic cooling distortion
  and anisotropic adiabatic shear/tilt heating, while freezing He ignores anisotropic Sobolev
  escape modulation in He I 584 Å (`rec_microphysics::he_singlet`) and charge-transfer /
  bound-free feedback.

### 1.2 Coupled State Vector and Equations on E-fold Clock $\eta = \ln(a/a_{\rm emit})$
Evolve the joint state $\mathbf{y}(\eta) = (x_p, x_{\rm HeII}, x_{\rm HeIII}, T_m)$ relative to
matched FLRW baselines $(x_{p,\rm ref}, x_{\rm HeII,ref}, T_{m,\rm ref})$ via baryon rest-frame clock
$d/d\eta_{\rm mat} = (\gamma_b H)^{-1} d/d t_{\rm proper}$:
1. **Matter temperature ODE**:
   $$\frac{d T_m}{d\eta} = -2 T_m + \frac{\Gamma_C(\text{sky}_{\rm mat}, x_e)}{\gamma_b H(\eta)}
     \left(T_C^{\rm aniso}[\text{sky}_{\rm mat}] - T_m\right), \qquad
     \Gamma_C \equiv \frac{8 \sigma_T a_r T_{\rm eff}^4}{3 m_e c}\,\frac{x_e}{1 + f_{\rm He} + x_e},$$
   with $x_e = x_p + x_{\rm HeII} + 2 x_{\rm HeIII}$ and matching matched-difference predictor against
   $T_{m,\rm ref}(\eta)$ so isotropic FLRW gives $\delta T_m \equiv 0$ to machine precision.
2. **Two-temperature Hydrogen TLA RHS**:
   Evaluate `rec_microphysics::anisotropic::anisotropic_two_temperature_source(&rsky, n_h, hubble, RetainedState { xp, x2: 0.0 }, tm)`
   using the **evolved $T_m$** rather than `Some(T_C)`, preserving the decoupled recombination
   recombination coefficient $\alpha_B(T_m)$ while using directional radiation temperatures for
   photoionization $\beta_p(T(\hat{n}))$ and Wien factors.
3. **Anisotropic Helium coupling (`rec_microphysics::he_singlet`)**:
   Map BASS `MaterialDirectionalSky` rays into weighted `he_singlet::WeightedBbMode`, `PairInput`,
   and `PBoundFreeTable`/`SBoundFreeTable` inputs (`BASS/_rustcore/src/microphysics/rec.rs` frame
   contract: `CoverageError::MissingAuthority` must propagate fail-closed when photoionization tables
   are outside supported bands).

### 1.3 Gating Criteria Before Code Promotion
- **FLRW identity gate**: Isotropic sky with matching $H, n_H$ reproduces $(x_{\rm ref}, T_{m,\rm ref})$
  within $10^{-13}$ per step across $z \in [1800, 0]$.
- **Linear decoupling gate**: Below $z \approx 800$, evolved $T_m$ tracks $\propto (1+z)^2$ adiabatic
  scaling cleanly without stiff instability near $z \approx 1100$.

---

## T2. Second-Order (Strang) Operator Splitting for $\delta x_e$ Coupling

### 2.1 Current Limitation (First-Order Splitting)
In `BASS/_rustcore/src/homogeneous_sky/solve.rs`:
- Each e-fold cell $[\eta_n, \eta_{n+1}]$ evolves photons/geometry/dust via a 2nd-order SDIRK2/Strang
  step using constant `opacity.delta_xe` from the *previous* slice $\eta_n$, and only updates
  `opacity.delta_xe` via backward Euler in `implicit_matched_step` at the end of $[\eta_n, \eta_{n+1}]$.
- Consequently: (a) photon-recombination coupling has global $O(\Delta\eta)$ splitting error (vs
  $O(\Delta\eta^2)$ for SDIRK2 geometry+Thomson), and (b) `implicit_matched_step` itself is first-order
  backward Euler in $\delta x_e$.

### 2.2 Proposed Second-Order Algorithm
1. **Symmetric Strang step on $[\eta_n, \eta_{n+1}]$ (`dt = \eta_{n+1} - \eta_n`)**:
   - **Half-step A ($\eta_n \to \eta_{n+1/2}$, length $dt/2$)**: Advance $x_n \to x_{n+1/2}$ via
     trapezoidal / midpoint-implicit matched update using $\text{sky}_n$ and interpolated $(n_{H,n+1/2}, H_{n+1/2})$,
     or evaluate midpoint $\delta x_e(\eta_{n+1/2}) = \delta x_e(\eta_n) + \frac{dt}{2} \dot{\delta x}_e(\eta_n)$
     (clamped inside $[0, X_{\rm MAX}]$).
   - **Symmetric Thomson–Einstein–Thomson cell $[\eta_n, \eta_{n+1}]$**: Supply midpoint
     `opacity.delta_xe = x_{n+1/2} - x_ref(eta_{n+1/2})` to BOTH `opacity.cells(eta_n, mid)` and
     `opacity.cells(mid, eta_{n+1})` (or `delta_xe_1 = x_{n+1/4} - x_{ref,n+1/4}` on first half and
     `delta_xe_2` on second half for exact time-reversal symmetry).
   - **Half-step B ($\eta_{n+1/2} \to \eta_{n+1}$)**: Complete matched implicit Crank-Nicolson /
     TR-BDF2 correction on $x_{n+1/2} \to x_{n+1}$ using $(\text{sky}_n, \text{sky}_{n+1})$.
2. **Measured Order Test Protocol (Required Acceptance Gate)**:
   Run tilted Bianchi `I` / `VII_h` (`C2` window_strong and `z_emit = 1600`) across step counts
   $N \in \{64, 128, 256, 512, 1024\}$ on fixed reference tables, and verify that successive differences
   $| \delta x_e^{(N)} - \delta x_e^{(2N)} | / | \delta x_e^{(2N)} - \delta x_e^{(4N)} |$ and optical depth
   differences converge at **ratio $\approx 4.0$ (`3.6 .. 4.4`)** vs the current R113 `ratio ~ 2.0`.

---

## T3. Grid-Free Moving-Electron Collision on the Harmonic Route

### 3.1 Mathematical Obstruction (Non-Polynomial Boost Kernel)
On `--route harmonic`, free streaming uses Gaunt matrices of rank $L \le 2$, which are strictly
polynomial in $\hat{n}$. Rest-electron Thomson scattering ($\vec{\beta}_b = 0$) acts linearly on $\ell \le 2$
moments only ($C_0^{\rm rest}$ preserves band limit $\ell_{\rm max}$). However, for nonzero baryon
bulk velocity $\vec{\beta}_b \neq 0$, Lorentz boosting photon intensity and angle between normal frame
$\hat{n}$ and baryon rest frame $\hat{n}'$ introduces the rational Doppler factor:
$$D(\hat{n}; \vec{\beta}_b) = \gamma_b (1 - \vec{\beta}_b \cdot \hat{n}), \qquad
  I_{\rm normal}(\hat{n}) = D^{-4}(\hat{n}; \vec{\beta}_b)\, I_{\rm rest}(\hat{n}'(\hat{n}; \vec{\beta}_b)).$$
Because $(1 - \vec{\beta}_b \cdot \hat{n})^{-k}$ ($k \ge 1$) has an essential pole at $|\vec{\beta}_b| = 1$
and infinite Legendre series $\sum_{\ell=0}^\infty c_\ell(\beta_b) P_\ell(\hat{\beta}_b \cdot \hat{n})$,
the boost operator is **non-polynomial** and couples every harmonic mode $\ell$ to $\ell' \to \infty$,
preventing an exact finite-rank Gaunt matrix in closed form without grid synthesis or series truncation.

### 3.2 Covariant PSTF Expansion in $|\vec{\beta}_b|$ to Order $K$
1. **Expansion order and Gaunt coupling bandwidth**:
   Using Challinor / Pitrou boosted-collision PSTF form expanded cleanly in powers of $\beta_b \equiv |\vec{\beta}_b|$
   up to fixed order $K \in \{2, 3, 4\}$:
   - Each power $\beta_b^p$ multiplies spherical harmonics of degree $L \le p$ via `kinetic::wigner::gaunt`,
     so the collision + recoil operator couples $|\ell - \ell'| \le K + 2$.
   - Number and momentum exchange (monopole and dipole moments, $\ell = 0, 1$) must be computed to
     order $K$ or integrated consistently so photon + host total energy-momentum conservation holds to
     the truncation order $O(\beta_b^{K+1})$.
2. **Explicit Truncation Remainder Bound & Fail-Closed Threshold**:
   For $0 < \beta_b < 1$, the remainder of the Taylor/Legendre truncation of $D^{-4}$ after degree $K$
   on one cell of optical depth $\tau$ satisfies:
   $$\left\| \Delta C_{\rm trunc} \right\|_\infty \le C_K\,\tau\,\frac{\beta_b^{K+1}}{(1 - \beta_b)^{K+5}} \,\|\mathcal{I}\|_\infty,$$
   where $C_K = \binom{K+4}{4} \frac{4!}{\dots}$ reflects the $(K+1)$-th binomial coefficient of $(1-\beta)^{-4}$.
   - Requiring remainder $< \epsilon_{\rm tol}$ (e.g., $\epsilon_{\rm tol} = 10^{-8}$) imposes a strict
     **fail-closed domain gate**: e.g., at $K = 2$, grid-free collision is admitted only for
     $\beta_b \le \beta_{\max}(K=2, \epsilon_{\rm tol})$ ($\beta_b \lesssim 10^{-3}$ for $10^{-8}$),
     whereas relativistic bursts ($\beta_b \sim 0.1\text{--}0.2$, such as `V1` / strong-tilt tests) must
     fail closed or explicitly delegate to the exact pseudo-spectral `(n_theta, n_phi)` collision grid.

---

## T4. Spectral Transport and $y$-Type Compton Distortion Bookkeeping

### 4.1 Breakdown of Bolometric Temperature Approximation
In `BASS/_rustcore/src/homogeneous_sky/rec_bridge.rs`:
- `material_directional_sky` currently reconstructs a directional temperature via
  $$T_{\rm bolo}(\hat{e}; \eta) = T_{\rm unit}\, I_{\rm mat}(\hat{e}; \eta)^{1/4}.$$
- When a Planck distribution of initially uniform temperature undergoes **multiple Thomson scatterings**
  across directions of different redshifted temperatures (shear/curvature dispersion + baryon recoil/bulk tilt),
  the resulting angle-averaged spectrum is a convex superposition of Planck spectra
  $n(\nu, \hat{e}) = \int d\tilde{T}\, P(\tilde{T}|\hat{e})\, (e^{h\nu/k_B \tilde{T}} - 1)^{-1}$, which
  is **strictly non-Planckian**: its second temperature variance $\sigma_T^2(\hat{e}) = \langle (\Delta T/T)^2 \rangle$
  injects a positive **Compton $y$-distortion** parameter $y(\hat{e}) = \frac{1}{2} \sigma_T^2(\hat{e})$
  (Chluba & Sunyaev $y$-distortion from linear/nonlinear CMB superposition) and alters the Wien tail
  $e^{-E_{21}/k_B T}$ exponentially once $(\Delta T / T)^2 \cdot (E_{21}/k_B T)^2 \sim 1$.

### 4.2 Minimum Bookkeeping Upgrade Specification
1. **Two-carrier bolometric + $y$-distortion moments $(\mathcal{I}_{ab}, \mathcal{Y}_{ab})$**:
   Carry a second symmetric tracefree / bolometric-weight sky carrier $\mathcal{Y}_{ab}(\hat{n})$ alongside
   intensity coherency $\mathcal{I}_{ab}(\hat{n})$ (corresponding to frequency integral weight $\int \nu^3 (\nu \partial_\nu)^2 f\, d\nu / 4$
   generating spectral variance $2 y + \dots$), sourced cleanly during every Thomson scattering cell by:
   $$\Delta y_{\rm mix}(\hat{e}') = \frac{1}{2}\left[\langle (T(\hat{e})/\bar{T} - 1)^2 \rangle_{\rm scatt} - \left(\frac{T_{\rm exit}(\hat{e}')}{\bar{T}} - 1\right)^2\right] \ge 0.$$
2. **REC Wien & photoionization correction**:
   Extend `rec_microphysics::anisotropic::DirectionalSky` with an optional per-direction distortion array
   `y_param: Option<&[f64]>`, modifying `wien_average_ln` and `photoionization_average_s` to second order
   in $h\nu / k_B T \cdot y$ (preserving $y = 0$ bitwise compatibility).

---

## T5. `htt_base` Owning Dispatch & Contract Boundary (`CLAUDE.md` §1 Gap)

### 5.1 Current Boundary in `htt_base`
Across `htt_base`:
- `htt/bass/inference/envelope.py`: restricts production inference to `STRONG_FAMILIES = {"FLRW", "I", "V", "VII_0", "VII_h", "IX"}`, keeps `RESIDUAL_BACKED_FAMILIES` (`{"II", "III", "IV", "VI_0", "VI_h", "VIII"}`) outside strong-IC production.
- `htt/bass/transport/general_bianchi_transfer.py` (`_evaluate_linearized_near_flrw_sky`) and
  `htt/bass/runtime/ver2_execution.py` + `CLAUDE.md` §1 enforce that full-mode LoS dispatch covers `{FLRW, I, V, IX}` (or linearized-FLRW subset `{FLRW, I, V, VII_0, VII_h, IX}`), while off-axis / general-Lie requests raise `OutOfScopeError` / fail closed.
- Meanwhile, the native Rust engine (`BASS/_rustcore`, R113/R114) now solves all 12 Bianchi families + `VI*_{-1/9}` + arbitrary `SO(3)` off-axis `LieInitial` inputs cleanly via both `Route::Rays` and `Route::Harmonic`.

### 5.2 Required Contract Steps Before Enabling Rust Dispatch Inside `htt_base`
1. **Explicit Contract Upgrade & Provenance Tier (`AtlasEntryLite` / `NativeRustLieSkyAdapter`)**:
   Define a typed adapter in `htt/bass/transport/` consuming `BASS homogeneous_sky` artifacts (`modes.tsv`,
   `los_modes.tsv`, `lie_constants.tsv`, `recombination.tsv`, `run.txt`) labeled strictly as
   **`TRANSFER_CONDITIONAL_NATIVE_RUST_TEMPLATE` / deterministic single-history template** (`claim_ceiling` unchanged;
   never mixed into `EXACT_SYNTHETIC_GEODESIC_ORACLE` or calibrated posteriors).
2. **Mandatory Dispatch Acceptance Gates before lifting fail-closed guards**:
   - Convention & spin sign unit gates matching `sky_spectrum` ($\text{HEALPix } E = -E_{\rm Dossier}$, outward sky $\hat{n} = -\hat{e}$, `m >= 0` normalization) verified via `tests/obsstat/`.
   - Congruence invariance checks (`lie_type_initial == lie_type_final`, `h` invariance, rotated `SO(3)` equivariance).
   - Separate claim-firewall & R78 DAG gate check ensuring off-axis / universal-Lie outputs do **not** bypass `SQ-NATIVE` (`C1`–`C6`), `SQ-CMB-NULL` (`300+` Commander sims), or `SQ-CF4`/`SQ-OPTICAL`.
3. **Interim Standing Guard**: Until a dedicated `htt_base` PR explicitly updates `CLAUDE.md` §1, `envelope.py`,
   and `general_bianchi_transfer.py` with the adapter + test gates above, **off-axis and general-Lie Python dispatch
   remains fail-closed**; `scripts/r114/` invokes the standalone `BASS` binary strictly as bounded deterministic
   evaluation scripts.
