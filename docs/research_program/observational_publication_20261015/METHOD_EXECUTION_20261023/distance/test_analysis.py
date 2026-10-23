"""Independent dense references for the actual R24 distance discriminator."""
import csv
import json
from pathlib import Path

import numpy as np
from scipy import stats

import analyze


def prepared():
    rows, ledger, ids, groups, folds, rule, coords, n = analyze.load()
    y, s, v, feats = analyze.features(rows, n)
    result = json.loads((Path(analyze.__file__).parent / "RESULT.json").read_text())
    return rows, ids, groups, folds, y, s, v, feats, result


def test_cohort_source_join_and_group_folds():
    rows, ids, groups, folds, y, s, v, feats, result = prepared()
    assert len(ids) == len(set(ids)) == 274
    assert result["cohort"]["selected"] == 628
    assert result["cohort"]["undefined"] == 354
    assert result["direction_sources"] == {"CF4_J2000":269,"HyperLEDA_J2000":5,
                                           "missing":0,"five_PGCs":list(analyze.MISSING_FIVE)}
    assert all(len(set(folds[np.array(groups)==g])) == 1 for g in set(groups))
    assert np.min(v) == 317 and rows[int(np.argmin(v))]["pgc"] == "9031"
    assert result["historical_residual_failure"]["T"] == 4.555321823822732
    assert result["historical_residual_failure"]["p_plus_one"] == 0.000976324139614352


def test_dense_gls_and_conditional_gaussian_references():
    rows, ids, groups, folds, y, s, v, feats, result = prepared()
    for a,b,model,fold in ((0.0,0.0,"B_optical_STF",0),(.055,.29,"C_union",3)):
        key=f"a_{a:.3f}_b_{b:.3f}"
        names=analyze.MODELS[model]
        X=analyze.design(feats,names)
        V=np.diag(s*s-a*a)+a*a*np.ones((274,274))+b*b*np.equal.outer(groups,groups)
        tr=np.flatnonzero(folds!=fold); te=np.flatnonzero(folds==fold)
        Vtt=V[np.ix_(tr,tr)]; Vst=V[np.ix_(te,tr)]; Vss=V[np.ix_(te,te)]
        # Independent dense normal-equation and scipy density reference.
        wtX=np.linalg.solve(Vtt,X[tr])
        wty=np.linalg.solve(Vtt,y[tr])
        beta=np.linalg.solve(X[tr].T@wtX,X[tr].T@wty)
        resid=y[tr]-X[tr]@beta
        sigma2=float(resid@np.linalg.solve(Vtt,resid)/len(tr))
        B=Vst@np.linalg.solve(Vtt,np.eye(len(tr)))
        pred=X[te]@beta+B@resid
        S=sigma2*(Vss-B@Vst.T)
        ref=float(stats.multivariate_normal.logpdf(y[te],mean=pred,cov=S))
        actual=result["scenarios"][key]["models"][model]["folds"][fold]
        np.testing.assert_allclose(actual["coefficient_raw_units"],beta,rtol=1e-9,atol=1e-10)
        np.testing.assert_allclose(actual["sigma2_ML_train"],sigma2,rtol=1e-9,atol=1e-10)
        np.testing.assert_allclose(actual["joint_log_predictive_score"],ref,rtol=1e-9,atol=1e-10)
        assert np.linalg.eigvalsh(S).min() > 0


def test_full_tensor_covariance_and_oof_score_accounting():
    rows, ids, groups, folds, y, s, v, feats, result = prepared()
    out=list(csv.DictReader((Path(analyze.__file__).parent/"OOF_ROWS.csv").open(newline="")))
    assert len(out) == 4*3*274
    for scenario,sd in result["scenarios"].items():
        for model,md in sd["models"].items():
            full=md["full_fit"]
            assert all(x == len(md["column_names_raw_units"]) for x in full["rank_sensitivity"].values())
            C=np.asarray(full["coefficient_covariance_raw_units"])
            np.testing.assert_allclose(C,C.T,rtol=1e-10,atol=1e-10)
            assert np.linalg.eigvalsh(C).min() > -1e-10
            tensor=full["angular_tensor_state"]
            assert len(tensor["coefficient_vector"]) == len(tensor["names"])
            assert np.asarray(tensor["full_joint_covariance_including_cross_blocks"]).shape == (len(tensor["names"]),)*2
            assert len(md["folds"]) == 5
            np.testing.assert_allclose(md["total_joint_log_predictive_score"],
                sum(f["joint_log_predictive_score"] for f in md["folds"]),rtol=1e-10,atol=1e-10)
            selected=[float(x["OOF_ordered_conditional_log_score"]) for x in out
                      if x["scenario"]==scenario and x["model"]==model]
            assert len(selected)==274
            np.testing.assert_allclose(sum(selected),md["total_joint_log_predictive_score"],rtol=1e-10,atol=1e-10)
