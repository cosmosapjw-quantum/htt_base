# HTT six-paper: source-conditioned READY sibling execution, 2026-10-16

Authority: `cosmosapjw-quantum/htt_base` draft PR #543 head `eac75859f38bf223d5e5ee215ae0b65a1617ceaa` and six-paper `PUBLICATION_DAG.json`; **not** the 245 PR engineering queue, not `main` and not a journal-submission approval. All input source bytes below were inspected from the exact ChatGPT Library ZIP checkpoints, not inferred from filenames.

## X01 common source-binding and overlap

Recovered real selected CF4 groups: 35,970 unique IDs, source NPZ SHA-256 `86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c`. Method groups FP=26,916, TF=7,614, SN=700, OTHER=740. Every redshift-window and method partition reuses the underlying source galaxy groups: correlated, **not** independent catalogues. CF4 survey selection and method shared zero-point law remain unknown. Recovered single Planck cosmological sky: nine T processing products (9×32 finite low-ℓ) and eight E/B (8×64); separate NSIDE64 T and P mask support (26,846 vs 30,021 pixels). HM/OE/NILC/noSZ are algorithmic processing/split products, not independent cosmic skies; no authenticated noSZ full E/B map. Same cosmological sky enters P1/P2/P4/P5 and CF4 groups enter P1/P3/P4/P6. `X01_SOURCE_BINDINGS.json` assigns source and absent physical transport per paper; it never infers inter-release independence from different filenames.

## X03 historical versus prospective selections

The prior p=0.039 is historical/exploratory. Planck `ell=2..5`, 9 T / 8 EB products and mask ordering, H03 redshift Gaussian centers (0.025,0.04,0.06,0.08), σ_z=0.012, method-family splits and twelve sky patches are already exposed to data; no retroactive prospective label. `X03_CLAIM_SELECTION_LEDGER.json` gives the still-UNREGISTERED new-null requirements and forbids conditional selected trials being promoted to confirmatory results. No new observational null was tested here.

## V01: local observer boost versus material/radiation velocity

Adopt signature (-,+,+,+), c=299792458 m/s, timelike tetrad u.u=-c². Define `beta_RO` = observer O velocity **measured in radiation R**, `beta_RM` = matter M velocity **measured in R**, and `beta_MO` = O velocity **measured in M's canonical rotation-free boost chart**. For three-vector b=beta_RO, u=beta_RM, gamma_u=(1-|u|²)^(-1/2):

`beta_MO = (b/gamma_u - u + [gamma_u/(gamma_u+1)]*(u.b)*u)/(1-u.b)`.

One-dimensional limit gives `(b-u)/(1-b*u)`; noncollinear ordered Lorentz boosts induce a Wigner rotation if another chart is composed. The invariant pair rapidity is `rho_OM=arccosh(gamma_O*gamma_M*(1-b.u))=atanh(|beta_MO|)`, **not** `|beta_MO|` itself. Survey bulk B_W has km/s units and is a finite selection-window velocity, not automatically a radiation-matter global tilt. Numerical relative-speed and norm checks use manufactured vectors; they do not model Planck Doppler calibration or estimate global tilt.

## K01: same-congruence kinematics and radial null

For u.u=-c² and projector h_ab=g_ab+u_a u_b/c²,

`nabla_b u_a = -u_b A_a/c² + (Theta/3) h_ab + sigma_ab + omega_ab`,

where `A_a=u^b nabla_b u_a` in m/s²; `Theta`, `sigma_ab` and `omega_ab` have s⁻¹, sigma spatial STF and omega spatial antisymmetric. `omega^i=(1/2) eps^{ijk} omega_jk` is an axial pseudovector. For a local instantaneous Euclidean spatial gradient `J=H I + sigma + omega` (all s⁻¹),

`r(n)=n_i J_ij n_j = H+n_i sigma_ij n_j`, so `n_i omega_ij n_j=0` identically.

A direct design with 160 manufactured unit directions has generic rank 6 acting on nine gradient entries, with three exactly null antisymmetric directions. This is **not a no-go theorem for all nonradial optics or covariant cosmography**, nor does it identify geometric shear from the apparent CF4 STF2 fit without source matching. A complete optical/Jacobi/clock transfer and covariance remains K02/K03/K04 work.

## B01: 11 Bianchi canonical branches and available external solvers

Bianchi I,II,III,IV,V,VI0,VIh,VII0,VIIh,VIII,IX = 11; VI_{-1/9} is an exceptional VI_h branch, **not** a 12th type. The Bianchi representative canonical Jacobi condition `a_i n^{ij}=0` and n-sign patterns, class A/B and h-branch descriptors are in `B01_BIANCHI_ATLAS_REGISTRY.json`. AniCLASS public wiki documents nearly-FLRW I,V,VII0,VIIh,IX with temperature/polarization; source ZIP was *found in Dropbox* but could not be read into this isolated runtime. Neither a full 11-type all-m high-ℓ polarized transfer, tilt, recombination, nor matching Planck likelihood was executed; B02 remains missing. Primary sources: Pontzen & Challinor (2007) doi:10.1111/j.1365-2966.2007.12221.x; Pitrou & Pereira (2019) PRD 100 123535 and Pereira & Pitrou (2019) PRD 100 123534; https://github.com/CyrilPitrou/aniclass/wiki.

## S02 and L01 bounded actual-data source readback (NOT completed)

Re-read H03 exact original source `86dfd896...` and its four *working* monopole coefficients: 75.16799577, 75.30321189, 74.55921682, 72.44515209 km/s/Mpc; the 36×36 conditional covariance minimum eigenvalue ≈0.00101644. These are not observations of geometric H=Theta/3 and cannot be mapped to signed `x_C`, certified F, or its physical Pi without a matched full kinematic source and same-congruence joint posterior. The sampled physical sector's missingness is therefore epistemic; formal outer [0,1] probability bounds are uninformative and conditional on a possible physical functional completion.

Reconstructed the actual temperature sky-mask finite block K_T(ell6..32) with shape 32×1053 from the source-locked Planck archive; spectral operator norm **2.4328695605629203**, Frobenius norm **5.317044435521295**. Physical P spin-2 ell6..8 mask response, effective beam, foreground and E2E remain pending L01. P2's eight E/B processing products are one sky, not eight independent null draws. The readback checks verified archive SHA-256 `303c78ff...` and `43cf6a29...` before reading data.

## Evidence and limits

- `X01`/`X03`/`B01` ledgers: source-backed inventories and selection constraints, no new observation.
- `V01`/`K01` new source code and 160-direction / 300-relative-velocity manufactured checks: algebraically derived and locally numerical verified, not independent physical source-transfer tests.
- `S02`/`L01` remain pending; all seven external-input physical qualification nodes remain blocked at publication level despite many existing raw/code downloads.
- No local Codex, NCP, full repo CI, new external physical solver, original owner dirty checkout edits, physical p-value or paper submission performed. `native_subagent: NOT_RUN` (not exposed in this chat).
