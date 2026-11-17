# R66 stage8 source repair — existing Planck TT reference and Commander0200 unit

This bounded read-only search supplies a concrete alternative ideal-sky reference input. No native scientific code, FITS payload, fitting, downloading or mutation was performed. It does not turn ideal Gaussian skies into released Commander end-to-end simulations.

## Exact existing spectrum

```
/mnt/extdrive/workdir/raw/planck_data/COM_PowerSpect_CMB-base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory_R3.01.txt
```

- Actual file205647bytes, directly recomputed SHA256 `50eecd4422e22026070bdacf9fa8a7e7ef3badf4fa50fffea040df669715cf51`.
- This exactly matches the existing `hashed_primary_files.pr3_theory_cl` identity in `docs/research_program/observational_publication_20261015/R49_GENERAL_TILTED_BIANCHI_20261112/DATA_REHASH_RECEIPT.json`, lines84–89.
- Official product/release identity is the PlanckPR3R3.01 `base-plikHM-TTTEEE-lowl-lowE-lensing-minimum-theory` spectrum, already used by the native legacy producer. No new web lookup was needed to find the local carrier. Parameter estimates are the named minimum-theory/best-fit reference, not a parameter posterior draw.
- First header: `# L TT TE EE BB PP`; rows l=2..2508. Existing producer `scripts/r49/run_r49_cmb_and_multiprobe_lanes.py`, lines486–502, reads these as `D_l` in μK² and converts TT column1 by `2*pi/[ell*(ell+1)]`. Header itself omits units; the Dl/μK² interpretation is explicitly present in the existing source consumer.
- Example stored TT values: D2=1016.73,D3=963.727,D8=822.295μK². The full l2..2508 range exceeds both a declaredl≤8reference and typicalNSIDE64bandlimitl≤191.

Computational form:

```
ell = table[:,0].astype(int)
Cl_TT_uK2[ell] = table[:,1] * 2*pi/(ell*(ell+1))
Cl_TT_K2 = 1e-12 * Cl_TT_uK2
```

Set l0/1 explicitly according to the estimator's declared nuisance/removed-mode convention; the file does not contain them. Do not pass Dl directly as Cl. For a real statistically isotropic Gaussian sky: a_l0~N(0,Cl), Re/Im a_lm~N(0,Cl/2), and negative-m reality. The parent may generate maps or the exact finite linear Gaussian covariance, then apply the same **actualR66synthesis/pixel/mask/fitoperator**. Under a fixed linear finite-band operatorA and full orthonormal real-harmonic carrier, covariance is A diag(Cl repeated2l+1) Aᵀ, with any source/beam/pixel factor included once inA. Unit scaling and monopole/dipole elimination must match observed processing.

This is an **explicit ideal isotropic Gaussian Planck-reference law**. It excludes Commander foreground residuals, component-separation response errors, E2Enoise/systematics and cosmological-parameter uncertainty unless separately added with a justified law. A finiteL truncation is a stated model, not an automatically negligible tail. For a cut-sky fit, l>8leaks into retainedl≤8; usingonlyl≤8nullmust be labelled finite-bandconditional. The existing complete file supports a broader declaredNSIDE64reference without requiring another spectrum download.

R51 `scripts/r51/run_r51_pr3_lowell.py` itself builds its source-bound covariance from matchedSMICAFFP10pairs; R60Commander tensor is deterministic reuse ofR51carrier and does not introduceTTcalibration. The concrete theoryfileconsumer isR49. R49's historical `cov_npipe=diag(cov_cv/fsky+fg_spread+rh_noise+1e−3)` is a separate heuristic covariance; it should not be silently imported intoR66. The useful inheritance is the spectrum identity andDlconversion, followed by the actualR66operator.

## Bare Commander0200–0299 temperature unit evidence

A decisive previously cached prefix-header receipt exists:

```
/mnt/extdrive/workdir/htt_open_data/r36_pr4_contract_preparation/COMMANDER_HEADER_PROBE.json
```

Actual JSON SHA256 `e4b3bccac2914be627b975ed271f0a6753270da7a4ed3c22e8cd469389bab3a5` (directly recomputed). Its `commander_sim0200` record binds the exact official URL `...SIMULATED_MAP.FILE_ID=npipe6v20_commander_cmb_mc_0200.fits`, HTTP200at2026-10-27,11520bytesread,prefixSHA `fc97fedec75edc8dc02e85b431ff53f0245a5b8bbf29a65327c9578093481917`.

Recorded FITS cards for this exact0200file are:

```
ORDERING=RING
NSIDE=4096
TFIELDS=1
TTYPE1=I_Stokes
TFORM1=1024D
TUNIT1='        '  / Map unit
NAXIS1=8192
NAXIS2=196608
```

Thus native4096RINGsingle-fieldtemperature structure is **source-supported by an existing actual header probe**, closing the earlierfilename-only uncertainty. **The unit remains blank.** No inspected legacyproducer/catalognote independently binds µK_CMB for this bare0200family. The same cached JSON explicitly gives µK_CMB for the different2048/0300/005aIQU product and K_CMB for observed4096CommanderTEMPERATURE; neither can be transferred to0200without source evidence. Numeric amplitude plausibility could diagnose a scale but would not by itself establish physical units/provenance.

The catalog100bare0200..0299products and preciseURL/OIDs are recorded in `r66_temperature_bank_audit.md`. The newheaderfinding supersedes that note's previously unresolvedNSIDE/HDUstructure. No further product acquisition or unit assumption was made in this task.
