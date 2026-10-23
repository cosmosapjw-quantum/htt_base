# Fixed 100 GHz HM amplitude-beam contrast, finite coarse interface

Astra contract /root/pantheon_source_response_review, requestedgpt-6-astra/xhigh,
observedUNKNOWN. Executor requestedgpt-6.1-sol/high, observedUNKNOWN. Ownerobsstat,
C0diagnostic-only. No original-node admission; not native/exactprocessedresponse.

Question: what finite coefficient response can the released100hm1/hm2 amplitude
beam difference produce through fixed published polarization weights and the
existing30021pixel COARSE support? No map/noise or prior scalarPOL_BEAM replay.

## Frozen source/conventions

Official HEALPix primary read2026-10-18:
https://healpix.sourceforge.io/html/fac_Using_HEALPix_Fortran_90_fa.htm
Version3.83/2024-11-13, beam sectionlines28–40 specifies FITS T/E/B amplitude
columns spanning integerell0..lmax. Combined with actualHEALPixcompatible
4001rows/MAX-LPOL4000, zero-basedrowj maps toellj. The /doc/html URL timed out;
the /html URL was actually read successfully by framer and parent. This external
qualification does NOT rewrite the separately reviewed archive-only intake.

HFI raw outsideGit:
/mnt/extdrive/workdir/htt_open_data/planck/PR3/beams/HFI_RIMO_BEAMS_R3.01.tar.gz
86556876bytes SHA187755434816addc045f13a4efd8515bb86b83531adc0eb7586412d9cfca4994.
Exactlytwo gzip layers, previously qualified in D04_HFI_BEAM_SOURCE.
Exact tar members14/22:
BeamWf_HFI_R3.01/Bl_TEB_R3.01_fullsky_100hm1x100hm1.fits
BeamWf_HFI_R3.01/Bl_TEB_R3.01_fullsky_100hm2x100hm2.fits.
Validate DET1/DET2/HDU1ASCII schema against sourceindex. ReadONLYrows0..8,
preserving literalT/E/Btokens; useE/Bell2..8. Reportrows0..1 without fabricated
normalization tests. Use amplitudeB directly, NOTB²/sqrt/divisionbymonopole.

Existing weights archive outsideGit:
/mnt/extdrive/workdir/htt_open_data/planck/PR3/weights/COM_Code_SMICA-weights-propagation_R3.00.tar.gz
SHA044ec9bed746ae745ad35a8b6ccf6e603f546083fec328e9c64d866ac9221f93.
Member weights_EB_smica_R3.00.txt
SHA541378f6c9ab37574aae909519b0f1fe020714a6cea2b8dd1c7fcedb5ffd87df.
Sourcecode reshape(2,7,4001): E/B,frequencies030/044/070/100/143/217/353;
channelindex3, textrows3/10. Preserve source binding; no weight renormalization.

Existing cache under observational_publication_20261015/
CONTINUATION_20261018/L01_EXECUTION_20261018/results/:
ORIGINAL_SELECTED_SUPPORT_RESPONSE.json
SHAbbb250b0288df040cc9273ef8483b91ae8253d5b720f3f22ee817cd846a36205;
ORIGINAL_SELECTED_SUPPORT_RESPONSE.npz
SHA7a462ba827ebe3ef5768552565f323ad2e1a679425be5d077fe8f46b9f0fdec6.
Reuse high6_8_to_low2_5 directly. This is RING64 synthesis/projector on30021
support, NOT D04native-child averaging. No mask/design/projector/injection replay.

## Finite calculation

d_l^X = (1/2) w_100,l^X (B_100hm1,l^X - B_100hm2,l^X), X=E,B,ell2..8.
Repeat over2ell+1 realcoordinates in existing per-ell EthenB m0/cos/sin order.
Validate that ordering against cachemetadata; failclosed on conflict.
C=[I64 K64x90], A=C diag(d), mapping154inputcoefficients to64lowcoefficients.
Conditionalcommon-sky SINGLECHANNEL contribution BEFOREcoadderfinalpixelwindow.
No second beam applied to processedmaps/noise. Otherchannels are outside this
pre-value-selection contract, UNKNOWNnotzero, and physicalcommonresponseHOLD.

Report signed d(E/B), exactsourcetokens/lastprinteddecimalunits; numerical||A||2;
high-E→low-B blocknorm; conservativegainbounds perunitinputnorm (NOabsoluteµK).
Treat decimal tokens and cachedbinary64K as exactpublishednumbers for certificate:
constructrationalA and S=sum(A_ij²); n=ceil(10^60 S), m=ceil_sqrt(n) viaINTEGER
arithmetic; U=m*10^-30 >=||A||F >=||A||2. Sameforleakageblock. Physicalbeam
uncertainty/skyamplitudeenvelope is NOTsupplied; never infer it from this bound.

## Controls/acceptance

Equalbeam→zero; zeroselectedweight→zero; swapsplits→-A; retainhalf-factor;
rejectwrongfield/order/schema/nonfiniteinputs. Normalize nonzeromatrices before
SVD; normalizedleft/rightsingularvectorresiduals<=1e-10; norms<=independent
Frobeniusupperbounds within1e-10relativenumericaltolerance. Exactzerovalid.
Flag SERIALIZATION_RESOLUTION_LIMITED whenabs(beamdiff)<=sumoftwolastprinted
decimalunits. This is NOTcertifiedroundinginterval/physicaluncertaintylaw.
Zero/precisionlimitedoutcomesarecompleteoutcomes; no postvalueselectionretuning.

## Bounds/result/review

ONEactualdataexecution canonicalvenv, <=2threads, <=512MiBprocessmemory;
60sCUMULATIVEnewexecution INCLUDINGtargetedcontrols/plotting; <=512MiBNEWdecoded
archivebytes; NOnetwork. Carry completedintake206907570decodedbytes and
3.929713791s into EXISTING1GiB/120sarchivehandlingceilings. Bothgzip layers,
allskips/replay/CRCbytes counted; preserve failures/cumulativeusage, no resets.
Onecompactresult/sourcetokentable/onesignedE/BcontrastPNG+PDFplot and conditional
bound explanation. Separatefreshindependentreviewbefore scopedpublication.
STOPonidentity/schema/conventionmismatch orcap; noautomaticrerun/relaxation.

StillHOLD: native-child/exactSMICAprocessedresponse,otherchannels/LFI,spatial/
offdiagonalbeams,pixelwindow,omittedmultipoles,physicalbeamuncertainties/
correlations,foregrounds,weightselection,jointsignal/noiselaw,D04/L03/originalDAG.
No ODE/native solver/mainmerge/submission. This is not physicalsignalcontamination.
