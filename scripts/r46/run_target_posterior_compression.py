#!/usr/bin/env python3
"""R46 synthetic target-specific Bayesian posterior compression."""
import argparse, json
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor, cho_solve
SEED = 20261109

def sym(x): return (np.asarray(x, float) + np.asarray(x, float).T) / 2

def posterior(sigma, h, noise):
    v = sym(h @ sigma @ h.T + noise)
    f = cho_factor(v, lower=True)
    gain = sigma @ h.T @ cho_solve(f, np.eye(len(v)))
    cy = sym(sigma - gain @ h @ sigma)
    return v, cy, gain

def target_moments(y, a, mu, sigma, h, noise, b=None):
    y = np.atleast_2d(y); a = np.atleast_2d(a)
    v, cy, gain = posterior(sigma, h, noise)
    if b is None:
        lm = mu + (y - (h @ mu)) @ gain.T
        return lm @ a, sym(a.T @ cy @ a)
    cs = sym(b.T @ v @ b)
    cross = a.T @ sigma @ h.T @ b
    gs = cho_solve(cho_factor(cs, lower=True), cross.T).T
    s = (y - h @ mu) @ b
    return a.T @ mu + s @ gs.T, sym(a.T @ sigma @ a - gs @ cross.T)

def gaussian_kl(mp, cp, mq, cq):
    d = len(mp); f = cho_factor(cq, lower=True)
    v = .5 * (np.trace(cho_solve(f, cp)) + (mq-mp) @ cho_solve(f, mq-mp)
              - d + np.linalg.slogdet(cq)[1] - np.linalg.slogdet(cp)[1])
    if v < -1e-10: raise ArithmeticError("negative Gaussian KL")
    return max(float(v), 0.)

def metrics(y, a, mu, sigma, h, noise, b):
    my, cy = target_moments(y,a,mu,sigma,h,noise)
    ms, cs = target_moments(y,a,mu,sigma,h,noise,b)
    fc = cho_factor(cs, lower=True); inv = cho_solve(fc,np.eye(len(cs)))
    delta = my-ms
    quad = np.einsum("ni,ij,nj->n",delta,inv,delta)
    kl = .5*(np.trace(cho_solve(fc,cy))+quad-len(cy)+np.linalg.slogdet(cs)[1]-np.linalg.slogdet(cy)[1])
    kl = np.maximum(kl,0.); risk = np.einsum("ni,ni->n",delta,delta)
    tracegap = float(np.trace(cs-cy))
    return {"expected_target_posterior_kl_nats":float(kl.mean()),"target_posterior_kl_mcse_nats":float(kl.std(ddof=1)/np.sqrt(len(kl))),
            "target_mmse_risk_gap_direct":float(risk.mean()),"target_mmse_risk_gap_mcse":float(risk.std(ddof=1)/np.sqrt(len(risk))),
            "target_mmse_risk_gap_covariance_trace":tracegap,"target_mmse_identity_abs_error":float(abs(risk.mean()-tracegap)),
            "raw_target_posterior_covariance_trace":float(np.trace(cy)),"summary_target_posterior_covariance_trace":float(np.trace(cs)),"n_prior_predictive_draws":len(kl)}

def latent_loss(sigma,h,noise,b):
    v,cy,_=posterior(sigma,h,noise); cross=sigma@h.T@b
    cs=sym(sigma-cross@cho_solve(cho_factor(sym(b.T@v@b),lower=True),cross.T))
    return float(.5*(np.linalg.slogdet(cs)[1]-np.linalg.slogdet(cy)[1]))

def row_basis(k):
    _,s,vh=np.linalg.svd(k,full_matrices=False); rank=int(np.sum(s>1e-11*s[0]))
    return vh[:rank].T,rank

def joint17(n,seed):
    r=np.random.default_rng(seed); p,m,q=17,23,2
    z=r.normal(size=(p,p)); sig=sym(z@z.T/p+.6*np.eye(p)); h=r.normal(size=(m,p))/np.sqrt(p)
    zn=r.normal(size=(m,m)); noise=sym(.35*zn@zn.T/m+.7*np.eye(m)); mu=.05*r.normal(size=p)
    a=np.zeros((p,q)); a[:5,0]=np.array([1,-1,1,-1,1])/np.sqrt(5); a[5:8,1]=np.array([1,1,-2])/np.sqrt(6)
    v,_,_=posterior(sig,h,noise); k=a.T@sig@h.T@np.linalg.solve(v,np.eye(m)); be,rank=row_basis(k); bl=be[:,:1]
    y=r.multivariate_normal(h@mu,v,size=n); ex=metrics(y,a,mu,sig,h,noise,be); lo=metrics(y,a,mu,sig,h,noise,bl)
    fe,fl=latent_loss(sig,h,noise,be),latent_loss(sig,h,noise,bl)
    return {"latent_dimension":p,"observation_dimension":m,"target_dimension":q,"target_score_map_shape":list(k.shape),"target_aligned_summary_rank":rank,
            "exact_target_summary":ex,"one_direction_dropped_summary":lo,"full_latent_posterior_loss_under_exact_target_summary_nats":fe,
            "full_latent_posterior_loss_under_lossy_summary_nats":fl,"data_processing_target_loss_le_full_loss_margin_nats":fe-ex["expected_target_posterior_kl_nats"],
            "data_processing_margin_under_lossy_summary_nats":fl-lo["expected_target_posterior_kl_nats"]}

def controls2d(n,seed):
    r=np.random.default_rng(seed); mu=np.zeros(2); sig=h=noise=np.eye(2); y=r.multivariate_normal(np.zeros(2),2*np.eye(2),size=n); b=np.ones((2,1))
    return {"aligned_sum_target":metrics(y,np.ones((2,1)),mu,sig,h,noise,b),
            "misaligned_first_component_target":metrics(y,np.array([[1.],[0.]]),mu,sig,h,noise,b),
            "analytic_misaligned_target_kl_nats":float(.5*np.log(1.5)),"analytic_misaligned_target_mmse_risk_gap":.25,
            "analytic_full_latent_posterior_loss_under_sum_summary_nats":float(.5*np.log(2))}

def radial():
    d,t,n=5,.7,1.3; c=t/(t+n); v=t*n/(t+n); lam=c*c/v
    return {"isotropic_radial_target":{"dimension":d,"prior_variance":t,"noise_variance":n,"posterior_mean_gain":c,"posterior_variance":v,
            "target_distribution":"||Lambda||^2/v|Y=y is noncentral chi-square(df=d, noncentrality=c^2||y||^2/v)","target_posterior_preserved":True,
            "same_norm_noncentrality_a":lam,"same_norm_noncentrality_b":lam,"same_norm_noncentrality_mismatch_max":0.,
            "full_latent_posterior_mean_squared_error_gap_under_norm_summary":c*c*d*(t+n)},
            "anisotropic_radial_counterexample":{"prior_covariance":[[1.,0.],[0.,4.]],"noise_covariance":[[1.,0.],[0.,1.]],
            "observation_a":[1.,0.],"observation_b":[0.,1.],"observed_norm_a":1.,"observed_norm_b":1.,"posterior_target_mean_a":1.55,
            "posterior_target_mean_b":1.94,"posterior_target_mean_difference_same_norm":.39,"target_posterior_preserved_by_norm":False}}

def run_experiment(n_rep=40000,seed=SEED):
    return {"schema":"htt.r46_target_posterior_compression/1","seed":seed,"classification":"SYNTHETIC_BAYESIAN_TARGET_COMPRESSION_NOT_OBSERVATIONAL",
            "replications_per_monte_carlo_experiment":n_rep,"experiments":{"seventeen_dimensional_target_aligned":joint17(n_rep,seed+101),
            "two_dimensional_controls":controls2d(n_rep,seed+211),"radial_symmetry_and_anisotropy":radial()},
            "scope":{"real_survey_data":"NOT_RUN","physical_Bianchi_transfer":"NOT_RUN","Cobaya_production_sampling":"NOT_RUN","empirical_calibration":"NOT_RUN",
            "HTT_physical_target_maps":"CANDIDATE_CHART_FUNCTIONALS_ONLY_NOT_EMPIRICALLY_CALIBRATED","HTT_summary_semantics":"T=(x,Q,Pi,F,G_F) is one joint posterior/compatibility push-forward, never independent likelihood factors",
            "novelty_claim":"No novelty claim for target sufficiency or conditional-MI; Gaussian row-space result is a fixed-prior exact specialization."}}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--seed",type=int,default=SEED); p.add_argument("--replications",type=int,default=40000); p.add_argument("--output",type=Path,default=Path("R46_MOCK_RESULTS.json")); a=p.parse_args()
    result=run_experiment(a.replications,a.seed); a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    e=result["experiments"]; x=e["seventeen_dimensional_target_aligned"]
    print(json.dumps({"output":str(a.output),"target_aligned_rank":x["target_aligned_summary_rank"],
        "17d_exact_target_KL":x["exact_target_summary"]["expected_target_posterior_kl_nats"],
        "17d_lossy_target_KL":x["one_direction_dropped_summary"]["expected_target_posterior_kl_nats"],
        "17d_full_latent_loss":x["full_latent_posterior_loss_under_exact_target_summary_nats"],
        "2d_misaligned_target_KL":e["two_dimensional_controls"]["misaligned_first_component_target"]["expected_target_posterior_kl_nats"],
        "anisotropic_same_norm_target_mean_gap":.39},indent=2))

if __name__=="__main__": main()
