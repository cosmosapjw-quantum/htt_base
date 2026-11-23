# R105 Planck PR3 Commander quadrupole transfer

P2 / L03 / B03. The data are the non-inpainted full-mission Commander I, Q and U maps and three matched FFP10 signal plus noise-and-systematics realizations. The estimator fits all five real components of each temperature, E and B quadrupole on the retained native pixels. Its observable is the masked fit in Galactic coordinates. This comparison has three realizations and a rank interval of 0.25.

## Release contract

Planck 2018 IV §3.5 describes propagating the signal and noise ensembles separately with the frequency weights fixed to those of the data. Section 4.2 and Fig. 9 specify the separate common confidence masks. Section 4.3, Eq. 9, says that the output CMB simulation contains both beam and pixel convolution and that the input sky contains neither. The residual estimated from output/input spectra divides out a nominal 5-arcmin Gaussian and the native pixel window. This resolves the R102/R104 ambiguity about the missing beam extension in the delivered raw simulation FITS. Directly sum the matched simulation maps. Put the released response into the forward model for a synthetic sky. [Planck Collaboration IV, A&A 641, A4 (2020), §§3.5, 4.2–4.4](https://doi.org/10.1051/0004-6361/201833881) · [Primary paper PDF](https://discovery.ucl.ac.uk/id/eprint/10110648/1/aa33881-18.pdf) · [ESA PR3 CMB dataset](https://doi.org/10.5270/esa-zfx8b4s)

The observed full-mission FITS HDU 2 identifies the cleaning method as COMMANDER and provides INT_BEAM and POL_BEAM. Both vanish at multipoles 0 and 1. At multipole 2 the values are 0.9999103546 and 0.9988206029. As a check that the intensity column includes the nominal beam, its ratio to the nominal 5-arcmin Gaussian at multipole 2000 is 0.997509, consistent with the residual plotted in Fig. 11. Separately evaluated native HEALPix pixel windows at multipole 2 are 0.9999999606 and 0.9999999778. The net response factors are 0.9999103153 and 0.9988205807. The single archived polarization column is used for E and B. Beam asymmetry, T-to-P leakage and directional variation in the cut-sky beam remain part of the physical calibration uncertainty. The paper explicitly qualifies the full-sky transfer on restricted sky fractions. [Planck Collaboration IV, §4.3](https://doi.org/10.1051/0004-6361/201833881)

## Estimator and signed checks

The observed FITS is NESTED, Galactic, COSMO convention and thermodynamic kelvin. The MC FITS uses RING pixels and thermodynamic kelvin. Its coordinate and polarization-convention header cards are absent. Processing assumes the release's common sky frame and convention for its matched pipeline outputs. The reader aligns indices with the exact native RING/NESTED permutation. It selects the official common masks above 0.5 and applies them directly to their respective fits. T and P retain 0.7794118722 and 0.7814398805 of the sky. There is no smoothing across a confidence-mask boundary.

For a real scalar quadrupole represented by the trace-free quadratic form q(n), the complex COSMO polarization pattern for unit E is −2 q(eθ + i eφ)/√24. Unit B multiplies this by i. The scalar fit also marginalizes over a free temperature monopole and Cartesian dipole. The complex normal equations recover the five E+iB coefficients using one common polarization mask. The code solves the native-mask least-squares problem in chunks and reports the mean of the five squared coefficients per field in μK². Higher multipoles on a cut sky contribute to the fit. The results support a matched finite-sample comparison, with neither higher-mode leakage nor an inverse-noise covariance removed.

The measured T and P normal-matrix condition numbers are 17.737 and 1.501. Both signed injections into the real-data score recover the assigned coefficient shifts to 7.11 × 10⁻¹⁵ μK or better. A separate test uses healpy harmonic synthesis of a signed 15-component input, unequal T/P windows, asymmetric masks and temperature nuisance modes. This checks the polarization sign and normalization independently of the analytic template generator. The same test module covers vector FITS indexing, invalid values, tied ranks, duplicate/conflicting pairs and the global download budget.

## Results

| Native fit | T in μK² | E in μK² | B in μK² |
|---|---:|---:|---:|
| Observed Commander | 185.721798 | 0.0570003 | 0.0854786 |
| FFP10 pair 00000 | 1547.550886 | 0.0537476 | 0.0242067 |
| FFP10 pair 00001 | 975.561419 | 0.0744681 | 0.1169439 |
| FFP10 pair 00002 | 199.775238 | 0.0149516 | 0.0269097 |
| Simulations at or above observed | 3 | 1 | 1 |
| (1 + upper count) / (1 + 3) | 1.00 | 0.50 | 0.50 |

The machine-readable inputs and coefficients are in COMMANDER_TRANSFER.json and COMMANDER_PAIR_00001.json. COMMANDER_MERGED.json combines distinct realizations by index and verifies estimator, masks, beam, observation and input identities. The older R104 raw pseudo-spectra are a different statistic. The three-rank result is descriptive. Cross-split HM/OE controls, full sky-fraction-specific instrument response and an adequately sized, validated ensemble remain open. No cosmological significance or physical Π is inferred.

## Local replay and acquisition

The production checkout started from 5a5f3b44d4fa5be65b71c2f80e715ebf9d1abf0a. Unique science inputs total 5,637,257,280 bytes. One new noise realization (00002) and one transient replay of noise 00001 transferred 603,987,840 bytes each, for 1,207,975,680 bytes in R105. Number 00002 remains in the local download cache, with its validated acquisition receipt. Number 00001 matched the previously recorded SHA-256 and was removed from temporary staging after reduction. Input bytes and per-file SHA-256 are in the result receipts. The full raw inventory currently lacks 356,956,813,440 bytes for all 300 raw pairs. Reusing the three completed reductions reduces the additional acquisition for the 297 unfinished estimators to 356,352,825,600 bytes. Those bytes have not been requested.

From the repository root, reproduce the merged rank with a zero-byte cap. This command was executed on the three actual receipts and produced a byte-identical merged result.

```bash
D=docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2
.venv/bin/python -m scripts.r105.commander_ensemble batch --start 0 --stop 3 \
  --include "$D/COMMANDER_TRANSFER.json" "$D/COMMANDER_PAIR_00001.json" \
  --directory /tmp/r105-commander-resume-replay --max-download-bytes 0
cmp /tmp/r105-commander-resume-replay/merged.json "$D/COMMANDER_MERGED.json"
.venv/bin/python -m pytest -q tests/obsstat/test_r105_commander_transfer.py
```

The next contiguous group needs four noise products. The four corresponding signal products already exist. The following command prepares and reduces them sequentially, then merges all seven pairs. Its cumulative cap is 2,415,951,360 bytes. Increasing the exclusive stop to 100 would require a total of 114,757,689,600 new bytes from the present three completed receipts. Finite rank resolution is 1/(N+1), with no claim about ensemble representativeness from that arithmetic alone.

```bash
.venv/bin/python -m scripts.r105.commander_ensemble batch --start 0 --stop 7 \
  --include "$D/COMMANDER_TRANSFER.json" "$D/COMMANDER_PAIR_00001.json" \
  --directory "$HOME/Downloads/htt_r105_commander/reductions" \
  --max-download-bytes 2415951360
```

Per-index reduction receipts are written atomically. Running the same command again reuses completed indices. Each new pair is size-checked up front, fetched under the existing validated PLA contract if missing, reduced, and released from temporary staging. The R105 estimator is restricted to the quadrupole. Expanding it to additional multipoles requires a new response and leakage validation.
