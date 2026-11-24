# R111 HOLD Design Specifications (T1, T2, T3)

> **Status: HOLD (design specifications only; no production code written or promoted).**
> Every T-item below documents physical equations, interface contracts, required external inputs,
> and backward-compatibility invariants prior to future implementation.

---

## T1. Native Differential Anisotropic Recombination in BASS (`rec_microphysics::anisotropic`)

### 1.1 Objective and Claim Boundary
Couple the pointwise anisotropic HYREC-2 three-level-atom (TLA) source in
`rec_microphysics::anisotropic` (`anisotropic_one_temperature_source`,
`compton_temperature_k`, `photoionization_average_s`, `escape_rate_factor`,
`wien_average_ln`) to the BASS e-fold history `homogeneous_sky` without
modifying frozen R109/R110 defaults (`--ionization` remains a scalar tabular replay
unless explicitly opted in).

### 1.2 Missing Physical Anchors and Preconditions
1. **Absolute temperature scale $T_{\rm CMB}(z)$**: BASS photon transport evolves bolometric
   intensity $I(\hat{n}; \eta)$ on dimensionless clock $\eta = \ln(a / a_{\rm emit})$ including
   cosmological $e^{-4\eta}$ redshifting relative to initial $\langle I \rangle_{\rm init}$.
   Evaluating $\exp(-E_{21} / k_B T)$, $\beta_p(T)$, and Compton occupation requires an explicit
   present-day anchor $T_{\rm CMB,0}$ (`2.7255 K` reference) with redshift-scaled reference
   $I_{\rm ref}(\eta) \equiv \langle I \rangle_{\rm init}\,e^{-4\eta}$ (so cosmological redshifting is
   NOT double-counted):
   $$T(\hat{e}_i; \eta) = T_{\rm CMB,0}\,(1 + z_{\rm emit})\,e^{-\eta}\left(\frac{I_{\rm baryon}(\hat{e}_i; \eta)}{I_{\rm ref}(\eta)}\right)^{1/4} = T_{\rm CMB,0}\,(1 + z_{\rm emit})\left(\frac{I_{\rm baryon}(\hat{e}_i; \eta)}{\langle I \rangle_{\rm init}}\right)^{1/4}.$$
2. **Baryon (electron-host) rest-frame transform**: `anisotropic.rs` requires incoming directions,
   weights, temperatures, and Sobolev expansion factors in the **baryon rest frame** $u_b^a$
   (`host.beam(0).beta`), NOT the hypersurface normal frame:
   - Aberration & Doppler shift from normal-frame photon propagation directions $\hat{n}_j$
     (`Photon.direction`, opposite to outward sky direction) to rest-frame propagation angles
     $\hat{e}_j$ with Doppler factor $D_j = \gamma_b (1 - \vec{\beta}_b \cdot \hat{n}_j)$ so
     $w_j^{\rm rest} \propto w_j^{\rm normal} D_j^{-2}$,
     $I_{\rm rest}(\hat{e}_j) = D_j^4 I_{\rm normal}(\hat{n}_j)$.
   - Expansion gradient factor $f(\hat{e}_j) = 1 + \Sigma_{ab} \hat{e}_j^a \hat{e}_j^b$ (checked via
     `AnisotropyError::ContractingDirection` so $f > 0$; tilt correction $\nabla u_b$ documented
     as $O(\beta_b \Sigma, \dot{\beta}_b)$ remainder).
3. **Separate matter temperature $T_m(\eta)$ below $z \sim 800$**: `anisotropic_one_temperature_source`
   sets $T_m = T_C$ (Compton equilibrium). Below $z \approx 800$, Compton heat exchange weakens
   relative to adiabatic expansion ($d\ln T_m / d\eta = -2$), so $T_m(\eta)$ must satisfy
   $$\frac{d T_m}{d\eta} = -2 T_m + \frac{8 \sigma_T a_r T_{\rm eff}^4}{3 m_e c H(\eta)}\,\frac{x_e}{1 + f_{\rm He} + x_e}\,(T_C^{\rm aniso} - T_m).$$
4. **Helium sector (He I / He II)**: Must track Saha + Peebles/HYREC-2 helium recombination at
   $z \gtrsim 1600$ (fixed $Y_{\rm He} = 0.2454$) before hydrogen dominates; otherwise early
   $x_e \approx 1 + 2 f_{\rm He} \to 1$ transition shifts $\tau(z \ge 1600)$.

### 1.3 Differential Algorithm (`HYREC baseline × Anisotropic/FLRW Peebles Ratio`)
Rather than integrating stiff atomic rates from scratch without helium two-photon/feedback corrections:
1. Retain a baseline FLRW hydrogen+helium table $x_e^{\rm HYREC}(\eta)$ (matching C1 `4cffa8a0`
   on $z \in [1600, 0]$).
2. At each BASS step midpoint $(\eta_k + \eta_{k+1})/2$, compute both:
   - Anisotropic source $\mathcal{S}_{\rm aniso} = \text{anisotropic\_one\_temperature\_source}(\text{sky}_{\rm rest}, n_H, H, \text{state})$
     giving Peebles net rate $\dot{x}_{e,\rm Peebles}^{\rm aniso}(x_e, T_m, H, \Sigma, \text{sky})$,
   - Matched FLRW Peebles evaluation $\dot{x}_{e,\rm Peebles}^{\rm FLRW}(x_e^{\rm HYREC}, T_m^{\rm FLRW}, H_{\rm FLRW}, \Sigma=0, T_{\rm iso})$
     with the identical `rec_microphysics` closure.
3. Propagate the dimensionless anisotropic perturbation factor $r(\eta) = x_e(\eta) / x_e^{\rm HYREC}(\eta)$
   (initial $r(0)=1$, clamped outside Saha/full-ionization where $1 - x_e < 10^{-8}$) or linearized
   difference $\delta x_e = x_e - x_e^{\rm HYREC}$:
   $$\frac{d(\delta x_e)}{d\eta} = \frac{\dot{x}_{e,\rm Peebles}^{\rm aniso} - \dot{x}_{e,\rm Peebles}^{\rm FLRW}}{H(\eta)} + \left(\frac{1}{H(\eta)} - \frac{1}{H_{\rm FLRW}(\eta)}\right)\dot{x}_{e,\rm Peebles}^{\rm HYREC} + \text{Compton } \delta T_m\text{-coupling}.$$
4. **Gate**: Exact FLRW limit ($\Sigma=0, \beta_b=0, I=\text{iso}, H=H_{\rm FLRW}$) must give
   $\delta x_e \equiv 0$ identically to `< 1e-14`; linear shear thick-limit cancellation lemma
   (`tau0 >> 1`) must agree with perturbation theory before coupling into C3 production runs.

---

## T2. Unequal Baryon/CDM Host Masses and Momentum-Balanced Opposed Tilt (`tilted_dust::Dust`)

### 2.1 Current Limitation
In `BASS/_rustcore/src/kinetic/tilted_dust.rs:18-22`, `Dust` stores a single scalar
`mass_number_initial: f64`, forcing `streams[0]` (electron/baryon Thomson host) and
`streams[1]` (non-interacting counter-stream) to carry identical rest-mass density (`50/50` split).
Cosmologically ($\Omega_b h^2 = 0.0224$, $\Omega_c h^2 = 0.120$, $\Omega_m = \Omega_b + \Omega_c$),
the baryon-to-total-matter rest fraction is $f_b \approx 0.157$ and CDM is $1 - f_b \approx 0.843$.

### 2.2 Proposed Data Structure and Initialization
Replace `mass_number_initial: f64` with `mass_number_initial: [f64; 2]` (per-stream $(m n_{\rm normal})_{\rm init}$):
1. Preserve existing `Dust::opposed(initial_energy, beta)` and `Dust::coflow(initial_energy, beta)`
   setting `mass_number_initial = [0.5 * E0 / gamma, 0.5 * E0 / gamma]` (R109/R110 bitwise compatible).
2. Add `Dust::opposed_two_species(initial_energy: f64, baryon_fraction: f64, beta_baryon: [f64; 3])`:
   - Validate $0 < f_b < 1$, $|\beta_b| < 1$.
   - Set stream 0 (`baryon`, kicked by `scatter_with_recoil_events`) velocity vector $p_0 = \gamma_b \beta_b$.
   - Enforce **exact zero net normal momentum** $q_0 + q_1 = M_0 p_0 + M_1 p_1 = 0$ on the initial
     slice (`Codazzi` unchanged when total $q_{\rm tot} = 0$):
     $$M_0 = f_b\, m_{\rm unit},\qquad M_1 = (1 - f_b)\, m_{\rm unit},\qquad p_1 = -\frac{M_0}{M_1}\, p_0,$$
     $$\gamma_1 = \sqrt{1 + |p_1|^2},\qquad m_{\rm unit} = \frac{E_{\rm initial}}{f_b \gamma_0 + (1 - f_b)\gamma_1}.$$
   - Guarantee $E_0 + E_1 = M_0 \gamma_0 + M_1 \gamma_1 = E_{\rm initial}$ and
     $\vec{q}_0 + \vec{q}_1 = \vec{0}$ identically (`< 1e-15`), while `p_1` remains subluminal ($|p_1| < \infty$ always).
3. Restrict Thomson `kick` to stream `0` (`host.kick(0, delta_q)` in `recoil.rs` already does this);
   stream `1` (CDM) evolves purely collisionlessly along timelike geodesics in `Dust::advance`.
4. Note for `--lie-ic` Codazzi coflow mode (`coflow = true` in `solve.rs`): if Codazzi requires nonzero
   initial total flux $q_{\rm req}$, allocate $(q_0, q_1)$ via $\beta_{\rm req}$ on the baryon stream or uniform
   coflow only with explicit CLI choice (`--coflow-species baryon|both`), keeping default equal-velocity coflow until specified.
5. Expose `--baryon-fraction <f>` (defaulting to current `0.5` symmetric split when omitted so R109/R110 defaults are unaltered).

---

## T3. $z < 4$ REI Physics Replacement Specification (`rei_microphysics::bass_ionization`)

### 3.1 Current Conditional Placeholder
`rei_microphysics::bass_ionization::Continuation` (`src/bass_ionization.rs:8-55`) replaces missing
$0 \le z < 4$ astrophysical reionization modeling with a continuous 4-parameter donor-matched
$\tanh[(y(z_{\rm HeII}) - y(z))/\Delta y]$ curve joining the AX08 $z=4$ output to full H+He II
ionization $x_e(0) = 1 + 2 f_{\rm He} \approx 1.1626$ ($Y_{\rm He} = 0.2454$).

### 3.2 Physical Modules Required to Retire the Placeholder (Aligned with R108 `M1–M6`)
To replace `Continuation` with a physically solved $z < 4$ closure:
- **M1 — Ionizing Emissivity $\epsilon_\nu(z)$**: Empirical + physical luminosity-function integration
  for QSO/AGN and star-forming galaxies producing HI ($\ge 13.6\text{ eV}$) and He II ($\ge 54.4\text{ eV}$)
  ionizing photon rates $\dot{n}_{\rm ion}^{\rm HI}(z), \dot{n}_{\rm ion}^{\rm HeII}(z)$ with spectral slope $\alpha_{\rm UV}$.
- **M2 — Absorber Mean Free Path & Clumping**: Coupling ionizing background intensity $J_\nu(z)$
  to observed Lyman-limit system / Forest mean free path $\lambda_{\rm mfp}(\nu, z)$ (no optically
  thin $J_\nu$ approximation when He II reionizes around $z \sim 3.5 \to 2.5$) and volume clumping
  $C_{\rm HII}(z), C_{\rm HeIII}(z)$.
- **M3 — Photoheating and Thermal History $T_0(\eta)$**: Solve $d T_{\rm IGM} / d\eta$ with
  H I, He I, and especially He II photoheating vs Compton cooling, recombination cooling, and
  Hubble adiabatic cooling so Case-A/B recombination coefficients $\alpha(T)$ are self-consistent.
- **M4 — Coupled Species ODE (`H I, H II, He I, He II, He III`)**: Solve non-equilibrium ionization
  rates on `[z_low_ax08 = 4.0, 0.0]` replacing `Continuation::xe` (`bass_ionization::merge`
  simply switches the third-interval owner from `Continuation` to `rei_lowz_solver`).
- **M5 — Observational Calibration Gate**: Compare predicted $\tau_{\rm reio}$ ($z \in [0, 20]$)
  and Ly$\alpha$/He II Gunn-Peterson optical depths against external forest / CMB bounds before
  unblocking astrophysical claims (`GAP_REGISTER` `SQ-P1-ANCHOR` / `L06` remains conditional).
- **M6 — Metric-Perturbation Boundary**: Keep explicit that homogeneous global $\bar{x}_e(\eta)$
  neglects patchy reionization ($k$-dependent optical depth fluctuations $\delta\tau(\hat{n}, z)$).
