# R66 validation and failure classification

## Executed numerical checks

Native command in the existing owner checkout:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=htt/src:htt:. \
.venv/bin/python -B -m pytest -p no:cacheprovider -q tests/test_r66_radiation_quotient.py
```

Final focused suite: **24 passed in2.02s**, process362547, exit0. Initial19-test version also passed before the source-repair extension; those earlier tests did not qualify an unseen temperature source. `RESULTS/TEST_RECEIPT.json` records exact final code/test hashes and executed command.

The suite checks harmonic normalization/sign independently by quadrature; mask/monopole/dipole response;4D quotient rank and shift invariance; covariance-profile equivalence; rotations; exact boosted blackbody stress/flux/Landau at beta0,.00123,.2; dipole–octupole coefficient24/35; retainedT^4 remainder; a separateell7completion bound; finiteNcalibration through12000independent Wishart and sky draws; positive-radiation body and occupancy; absentdepthGF; signed alternatives lost byscalarpower; shared-skyGLS covariance andduplicate rejection; conventionalpowertensortrace/rotation/sign; all-zero carrier rejection; knownanalyticcovariance distinctfromestimatedcovariance; angularunitcancellationandradialStudentintegral; sphere-densitynormalization; andHEALPixadjointvsdirectfiniteharmonicsum/covariance.

## Actual observations and conditional reference

- Both raw observed map hashes, columns, native units, ordering, mask and finite operator are preserved in `OBSERVED_EXTRACTION.json`.
- Native-injected DQ recovery maximum absolute error3.997e-14microK; fitted monopole/dipole leakage maximum5.93e-16.
- Ideal Gaussian covariance construction process336380 completed successfully; run elapsed44.85s. Exact nativeQinjection response error1.22e-15.
- Final observation analysis process343647 completed exit0 in3.53s. It reads the actual observed carrier and separately hashed ideal reference.4096 synthetic rows are never labelled actual Commander realizations.
- Knownanalytic covariance is used in the selected likelihood. FiniteNStudent/F remains a checked alternative and diagnostic.
- Common-sky pairedGLS WJ error2.22e-15. Full cross-operator covariance retained. Heldout2048 is a validation sample of the same ideal model, not physical evidence.
- Exact retained-family radiation response: moment/direct maxdifference1.33e-15 forPR4. Fulltrue-skycompletion remainsunbounded.
- GeneratedPNG visually inspected: legible4panels, explicitidealGaussianreferencelegend, signedstress, nuisanceamplitude, andpredeclaredprocessingcontrols. No data point is plotted withpopulation scatter asmeasurement error.

## Failures and their disposition

| Failure | Kind | Evidence and disposition |
|---|---|---|
|100005aIcarriersidenticallyzero | Source-content/product-selection | Original rawhashesmatch; arraysandoriginalsourcepreserved; covariancefailedclosed; noPTE/nojitter |
| Correct bare0200TUNITblank | Unresolvedmetadata | Fullproductidentifiedandcontentdiagnosed; noµKconversionbyamplitudeguess |
|16fileconcurrentpilotHTTPprematureEOF | Runtime/network | Logandpartialfilelengthspreserved; ownedbatchstopped; partialsnotrealizations |
|WolframcontextMCP−32603 | Runtimeconnector | Notclassifiedasmathematicalfailure; separateevaluatorcompletedtwopolynomialintegrals |
|Empty fully-masked RING chunk | Implementation | Preserved first failure; skip empty extrema and test a real small FITS/mask/order case |
|FullCommanderresponse/noise/foreground/exchangeability | Unresolvedscientificinput | Ideal-referenceclaimsmarkedconditional; noactualphysicalPTE |
|Largeobservedbanddependence | Scientificresult | Reported66.6%vectorchange; conventionalreconstructioncomparisonremainsrequired |

The R66 source repair does not invalidate prior E/B analyses of the polarization-use005a bank. No original scientific gate is promoted by having completed a finite implementation. Existing original42 payload and paper contracts are checked separately during additive DAG closeout.

## Reproduction order

1. `scripts/r66/extract_r66_commander.py` reads only the two actual observations. The corrected default excludes the zero-Ibank and rejects all-zero temperature input.
2. `scripts/r66/build_r66_ideal_reference.py` reuses the exact archived theory file, constructs the fullanalyticcovariance and4096syntheticcarriers.
3. `scripts/r66/analyze_r66_observables.py` emits all tables, likelihooddiagnostics, physicalmoments, conventionalcomparison andfigure.
4. `scripts/r66/acquire_r66_temperature_pilot.py --count 1` is a cached-only contentdiagnostic bydefault. The explicit --download flag enables network acquisition only; the command never infers or assigns a missing physical unit. Itneverautomaticallymakesareferencepopulation.
5. Focusedtests, thenonefreshindependentreview, additiveDAGvalidation and nonforcebranchpush.

Source snapshots distinguish byte identity from semantic identity: the original extraction imported a prior module snapshot; its actual harmonic/design/estimator kernels are checked semantically against the final code. That does not claim the complete module's bytes stayed unchanged.
