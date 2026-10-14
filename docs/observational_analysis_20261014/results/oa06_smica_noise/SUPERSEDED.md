# Superseded first OA06 interpretation

The files in this directory are the first same-operator SMICA projection. The projection itself succeeded, but the initial `result.json` called the centered simulation matrix a conditional noise covariance and the plot subtracted its simulation mean. A subsequent check of the same 300 cached maps found mean pairwise selected-map correlation 0.1322387373, maximum absolute low-mode simulation mean 0.4033513975 microK, and first/second-half covariance difference 0.4768033697 in relative Frobenius norm. Independence, the common component's physical meaning and the measurement bias are unresolved.

Use `../oa06_smica_scatter_v2/result.json` and its plot for current interpretation. The first files are retained as raw correction evidence; neither version supplies a calibrated full CMB measurement covariance or physical posterior.
