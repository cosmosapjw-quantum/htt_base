# Source attribution and resolved convention

Owner: HTT controller. Scope: factual corrections to retained source intake;
no numerical or original scientific acceptance change. Requested independent
reviewer gpt-6-astra/xhigh; observed runtime UNKNOWN.

## H02 paper attribution

The preserved H02_ACQUISITION_RAW.json misattributes MNRAS526(2):3051 to
“Watkins et al.”. The correct authors are **Abbé M. Whitford, Cullan Howlett
and Tamara M. Davis**, *Evaluating bulk flow estimators for CosmicFlows–4
measurements*, MNRAS526(2),3051–3071(2023),
[DOI10.1093/mnras/stad2764](https://doi.org/10.1093/mnras/stad2764).
The independent reviewer checked the primary
[author manuscript arXiv2306.11269v2](https://arxiv.org/html/2306.11269v2),
Data Availability and sections2.4.1–2.4.2. CF4 and6dFGSv/CF4TF mocks remain
available on request, while SDSS mocks have the separate Zenodo6640513 route.
The linked Measuring_bulkflows tree exposes a file named
`example_surveymock.dat` and estimator/mock-generation code. Its README documents
input columns and calls the .txt files example estimator results; it does not
expressly describe the .dat file as an example input. That stronger README
attribution in the raw intake is corrected here. The realistic ensemble
availability follows the paper, while the public code/tree alone does not
qualify the full H02 joint selection/calibration/null law. The source-gap
conclusion is unchanged.
[Qin et al. arXiv2109.14808v1](https://arxiv.org/html/2109.14808v1) independently
states its CF4TF mock request route. The original raw receipt is byte-preserved;
future consumers must apply this correction to the paper attribution.

## Radio RA convention resolved

The separate K03 reviewer checked
[Truebenbach & Darling, arXiv1710.02099v1](https://arxiv.org/abs/1710.02099),p3:
the released RA proper motions and uncertainties include the declination factor.
This coordinate convention is resolved. It must not be retained as a missing-input
question. The actual radio NNR/session-slope transfer, cross-component/joint errors,
and source-centroid-to-matter physical motion law remain unqualified. No K03_PM
numeric result or candidate payload changes.
