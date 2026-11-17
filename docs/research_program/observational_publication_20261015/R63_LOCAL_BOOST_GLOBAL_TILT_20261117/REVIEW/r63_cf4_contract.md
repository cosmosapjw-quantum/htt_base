# R63 CF4 source contract: Vcmb and DMzp
Date:2026-11-17. Bounded R3 source-contract task only. Requested model/effort:gpt-6.1-sol/high; observed:UNKNOWN/UNKNOWN. Read-only RDC device cosmosapjw, edd1b263-56a0-4391-8a2a-677dd00eabf5. Existing checkout:/home/cosmosapjw/Dropbox/bianchi/htt_base. HEAD observed:f29bbab420a33aecb1c398ddd961fd45097f536b. No remote files, repository state, catalogue files or source code were written.

## Conclusion

**Established from actual bytes + primary release documentation:** The selected 35,970-source carrier contains the published group distance modulus DMzp and error exactly, and z_CMB=V3k/299792.458 exactly. The release calls the corresponding Dist a **luminosity distance**, not a proper or comoving distance. DMzp is a weighted group distance-indicator result placed on the calibrator absolute scale. It is not the derived peculiar-velocity column Vpec.

**Unresolved source transport:** These facts do not establish that DMzp is an untouched bolometric flux distance in a heliocentric observing tetrad, or that all heterogeneous FP/TF/SN/calibrator contributions have one observer-flux correction p. Neither the selected carrier nor the inspected source contract records that p or a common exact frame-correction algorithm q. Therefore transporting the raw-bolometric Hui–Greene response as the exact physical response of this released CF4 carrier is not certified. Preserve g=(A−1)/c as the inherited declared working response, not as an independently established CF4 reduction law.

## Actual data and parsing evidence

Read primary release documentation:
- Tully et al., Cosmicflows-4, ApJ944,94(2023), DOI10.3847/1538-4357/ac94d8, arXiv:2209.11238 (full primary text read, rendered last-revision metadata2022-12-28): https://arxiv.org/html/2209.11238 .
- Publisher-linked CDS/VizieR release J/ApJ/944/94, byte descriptions: https://cdsarc.u-strasbg.fr/viz-bin/ReadMe/J/ApJ/944/94?format=html&tex=true .
- Authors' EDD Table4 column descriptions, page says UPDATED2023/05/02: http://edd.ifa.hawaii.edu/describe_columns.php?table=kcf4allvel .
Primary text was successfully retrieved through Exa; generic-web CDS timeout/arXiv disabled fetch did not supply evidence and was not used as a successful read.

CDS Table4 byte schema (1-indexed inclusive):
|Column|Bytes|Meaning|
|---|---:|---|
|DMzp|9–14|Weighted group distance modulus; absolute scale from calibrator galaxies|
|e_DMzp|16–20|Reported modulus uncertainty|
|Dist|22–26|Luminosity distance corresponding to DMzp|
|Vh|28–32|Group velocity relative to Sun|
|Vls|34–38|Local-Sheet frame velocity|
|V3k|40–44|Group velocity relative to cosmic background|
|fV3k|46–50|V3k with separate cosmological curvature factor|
|Vpds,Vpwf,Vpec|52–69|Derived peculiar-velocity estimators, not observed redshift or distance|
|Hi|71–75|Derived Hubble parameter|
|RAdeg,DEdeg|84–100|J2000 directions|

Table3 uses name Vcmb (bytes29–33); Table4 uses V3k. The selected carrier names the result z_CMB.

A read-only Python schema/parity check joined the actual Table4 rows by group_id to the selected NPZ, without transporting any catalogue to scratch:
- Raw release rows:38,053 in each current Table3 and Table4. This differs from38,065 groups in the paper's assembled catalogue; it is the actual existing release identity, not a silently corrected count.
- Selected rows:35,970.
- maxabs(selected dmzp−raw Table4 DMzp)=0.
- maxabs(selected e_dmzp−raw Table4 e_DMzp)=0.
- maxabs(selected z_CMB−raw Table4 V3k/299792.458)=0.
- maxabs(selected n_J2000−unit vector from raw Table4 RAdeg,DEdeg)=0.

NPZ fields are exactly group_id,z_CMB,dmzp,e_dmzp,n_J2000,method_family. It does **not** retain Vh,zHEL,per-method fluxes,photometric/K corrections,source-PV correction fields,method mixing weights or explicit observer deboost p. Raw Table4 retains Vh, so an effective per-row redshift ratio (1+V3k/c)/(1+Vh/c) can in principle be reconstructed from rounded published pairs. This is not yet the underlying exact relativistic correction algorithm or an independently measured observer velocity; no such reconstruction/fit was performed here.

## What DMzp already contains

Tully2023 SecIII.3–III.4 integrates Tully–Fisher subsamples by modulus zero-point adjustment and group averaging; the MCMC likelihood Eqs1–2 registers overlapping contributions. The authors state that relative moduli within a TFR subsample are not altered by that particular registration step. This does not mean the upstream distances were unreduced flux measurements.

SecIV.1 explicitly states that the **accepted6dFGSv distance moduli incorporate revised bias corrections and morphological corrections**. The FP likelihood is distance/selection dependent; its normalization was recalculated with a brighter J-band threshold, J<13.38, validated with mocks. Distances therefore have measurement/selection modelling, beyond a universal local Doppler factor. The paper Eq3 describes d_i as luminosity distance and uses a separate cosmological curvature factor f_i with redshift.

SecX table descriptions distinguish:
- individual multi-method distance moduli on a common absolute scale;
- Table3 group weighted average moduli;
- Table4 derivative velocities/H_i.
SecXI Eqs9–11 computes Vpds,Vpwf,Vpec from distances and CMB velocities, so those columns are downstream products, not inputs substituted into DMzp by the inspected selected carrier.

“Redshift-independent distance indicator” is appropriate in the operational sense that DMzp comes from indicator measurements/calibration rather than simply setting d=cz/H0. It must not be strengthened into “the reduction never uses redshift, cosmology, selection normalization or peculiar-velocity modelling.” The FP construction explicitly violates that stronger meaning. The historical loop6_result phrase “cosmology-calibrated” is its project metadata; the primary precise classification here is calibrated heterogeneous distance-indicator modulus with documented method-dependent bias/selection processing.

## Exact inspected code contract

Paths relative to existing checkout:
1. htt/htt/htt/infer/r54_distance_estimators.py: distance_mpc(mu)=10^((mu−25)/5); log_distance_ratio(mu,z,Om) calls flat_lcdm_distance_factors and returns eta=ln[y(z)/d(mu)].
2. htt/htt/htt/infer/r54_lcdm_body.py:208, flat_lcdm_distance_factors:
   chi_hat=int_0^z dz'/E(z'),
   y=c(1+z)chi_hat,
   g=[(1+z)/(E chi_hat)−1]/c.
   The module labels this response as Doppler source motion plus the source luminosity-distance factor. This is a stated theory/model contract, not direct documentation of upstream CF4 photometric correction.
3. scripts/r54/run_r54_cf4_exact.py:load reads only the six NPZ fields and checks pinned source/operator hashes plus group-ID parity. It does not reconstruct observer-frame reductions.
4. docs/research_program/cf4_schur_loop8_20261015/inputs/loop6_result.json explicitly records:
   source_frame = published Vcmb/C, not observer heliocentric redshift; J2000 sky. Frame boost/distance selection not physically reconstructed.
5. htt/obsstat/catalogs/cf4_grouped_observations.py:load_grouped_observations is an available **different** raw intake that reads Table4 Vh,DMzp,e_DMzp and J2000 directions; Table3 supplies method presence only. It does not deboost magnitudes or supply per-method p either. This loader must not be substituted silently for the frozen z_CMB selected experiment.
6. htt/src/common/cf4_manifest.py distinguishes Vcmb/V3k as frame-derived, fV3k as cosmology-corrected, DMzp as distance indicator, and Vpds/Vpwf/Vpec as reconstruction.

The original Loop6 selection producer itself was not located/read in this bounded task; actual selected-to-raw numerical identity was checked directly. No catalogue pipeline correction q/p was inferred from comments declaring an apparent-Hubble model.

## Primary contemporary conversion cross-check, without changing this experiment

A targeted primary search also found a directly relevant CF4 analysis:
Nusser & Tully, “Cosmicflows-4 and the Cosmological Consistency of Large-Scale Motions”, arXiv:2608.14265v1(2026-08-14):
https://arxiv.org/html/2608.14265v1 .
Read SecIII.1 and AppendixA.2. It defines the measured modulus as a luminosity-distance modulus and explicitly uses
  D_L,z=(1+zHEL)D_C(zCMB) [EqA5].
Its stated comoving-coordinate velocity u and physical peculiar velocity v obey u=(1+z)v at linear order; its K conversion is defined in EqA6. This is evidence that separate heliocentric and CMB redshift roles matter in current CF4 work. It does not prove every upstream DMzp contributor used that operation, and its individual-source analysis is not the present grouped source experiment. No results or numerical model from that paper were imported.

## Implication for R63

For eta=ln[y(z)/d], the source response g=(A−1)/c is the negative of the native luminosity-distance source coefficient (1−A)/c under the specified velocity-only FLRW model. The observer response depends additionally on what q and p the catalogue actually applied. The label “luminosity distance” alone cannot choose among native observer coefficient A, redshift-only coefficient−1, or fully deboosted coefficient0 for delta_D.

The smallest constructive next source step, if a physical observer-versus-matter velocity claim is required, is to document method-level distance definitions/photometric corrections and the actual Vh→V3k operation, then aggregate those responses using the release's group/method weights. An alternative is a source-matched generative reduction whose response is verified by injection. This is a specific missing observation contract, not a general impossibility of using CF4 or an instruction to rebuild unrelated likelihoods. Current conditional apparent-field/endpoint experiments can continue under their declared inherited working response.

## Byte identities observed in this task

|Object|SHA256|
|---|---|
|selected_source_observables.npz|86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c|
|table3.dat.gz compressed bytes|1c02e2b3829b0b323524a5f3671a5f530cbdccae3c10b432db0c2e2fe09672fe|
|table3.dat decompressed bytes|c2351c52de3e38a7fd80256b6f0818c550dd9f105b91e84fbcc1eb7234160b4d|
|table4.dat.gz compressed bytes|be91d4fae6fa01552ab3bc85db695411fca3249eeae08b566a712e6ea790bd99|
|table4.dat decompressed bytes|b6edfec68bdfddeada8f3b8f11938f3bbda98a8e2894ff136a369c2ad6594e94|
|workdir/raw/cf4_full/ReadMe|2cfed1418147d5a626dee1fa37c47252124477c9828490508d9bbe511d34edb4|
|r54_distance_estimators.py|9640b9785d2c4a5164e75018c2bfd2d0c8f6eb8072cb1a445e4f7589f9876d50|
|r54_lcdm_body.py|a61e88bb012fedeff78e57a31278f1e62e9225c03cca5f10c29c23cf996b3085|
|scripts/r54/run_r54_cf4_exact.py|0d84ec958dfc964d28f39ac2edc506dd5c8ed8009ad1c12019cb425b15418300|
|loop6_result.json|9764f6e865832e921bd9801e45790f378fa306931e7d4db41a3f4fa38352d254|
|cf4_grouped_observations.py|0e2bf3b3dbda2e87c4815d1cc1f621c4c3f45177c4942f152e5b7b7ab18f2f5a|
|cf4_manifest.py|174c0b7253f126fd725e9f81d60059d528c46c058a7cbc21faba11d38738c581|

The decompressed raw hashes match the archived Loop6/Table3–4 identities. Hashes establish byte provenance, not the missing physical observer transformation. Two scoped rg invocations included nonexistent legacy directories/globs and reported those path errors; subsequent reads used observed actual paths. No numerical inference failed, no test suite was needed/run for these read-only checks, and no additional review or broader model expansion was started.
