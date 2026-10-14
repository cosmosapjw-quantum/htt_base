#!/usr/bin/env python3
"""Generate publication-facing conditional report from executed result artifacts."""
from pathlib import Path
import json,hashlib,subprocess
R=Path(__file__).resolve().parents[1];B=R/'docs/observational_reboot_20261014';O=B/'results/scientific_report'
def load(rel):return json.loads((B/'results'/rel).read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build():
 O.mkdir(parents=True,exist_ok=True)
 joint=load('posterior/result.json');base=joint['scenarios']['rho_p0.00'];cf=load('cf4/posterior_v1/result.json')['posterior'];latent=load('cf4/latent_v1/result.json')['latent_bridge'];injection=load('cf4/injection_v1/result.json');morph=load('tensor_family_v1/calibration.json')['global_joint_null'];scan=load('smica_response_scan_v2/calibration.json')['global_joint_null'];dip=load('physical_dipole_v2/result.json');bk=load('bk18_fixed_fiducial_v1/result.json');ffp=load('spectra_ffp10_first_pair_v1/result.json');cl=load('class_noise_v1/result.json');cosmos=load('cosmos_selection_v1/result.json');gaia=load('gaia_frame_v1/result.json');jagb=load('jagb_kids_v1/result.json');lens=load('cache_lensing_v1/result.json');pm=load('cache_planck_marginal_v1/result.json')
 facts={'joint_rho0':base['moments'],'joint_cross_covariance_range':{k:{'rho':v['rho'],'moments':v['moments'],'PPC':v['PPC'],'quadrature':v['quadrature_status']}for k,v in joint['scenarios'].items()},'CF4_endpoint_posterior':cf['runs'][-1],'CF4_same_state_PPC':latent['repeated_measurement_ppc'],'CF4_injection_summary':injection['summary'],'SMICA_tensor_rank':morph,'SMICA_processing_rank':scan,'physical_dipole_proxy':{'speed':dip['kinematic_speed_km_s'],'sigma':dip['conditional_speed_sigma_km_s']},'BK18_reference_Q_HL':bk['Q_HL'],'CLASS_joint_noise_rank':cl['calibration']['rank_p'],'COSMOS_rows':cosmos['counts']['rows'],'Gaia_rows':gaia['returned_rows'],'JAGB_rows':jagb['cchp']['summary']['row_count']}
 optional=B/'results/planck_pr3_exact_v1/result.json'
 if optional.exists():
  pr3=json.loads(optional.read_text());facts['Planck_PR3_reference']=[{'variant':v['variant'],**{k:v['fit'][k]for k in ('amplitude','conditional_se')}}for v in pr3['variants']]
 sources=[]
 for path in sorted((B/'results').glob('*/result.json')):
  if path.parent==O:continue
  sources.append({'path':str(path.relative_to(R)),'sha256':sha(path)})
 for path in [B/'results/planck_pr3_peak_closeout_v1/closeout.json',B/'results/cf4/posterior_v1/result.json',B/'results/cf4/latent_v1/result.json',B/'results/cf4/injection_v1/result.json',B/'results/cf4/quadrature_refinement_v2/result.json',B/'results/tensor_family_v1/calibration.json',B/'results/smica_response_scan_v2/calibration.json']:sources.append({'path':str(path.relative_to(R)),'sha256':sha(path)})
 figspec=[('posterior/legacy_distance_image.pdf','posterior/result.json','Same posterior rho=0 flat-LCDM distance functions; pointwise5/95% quantiles; physical MES unavailable'),('cf4/latent_v1/latent_ppc.pdf','cf4/latent_v1/result.json','Same posterior latent dA and repeated measurement PPC, without reselection; conditional selected scenario'),('cf4/injection_v1/recovery.pdf','cf4/injection_v1/result.json','32 conditional selected scenario injections, not empirical CF4 coverage'),('bk18_fixed_fiducial_v1/diagnostic.pdf','bk18_fixed_fiducial_v1/result.json','BK18 correlated fixed fiducial HL descriptor; no PTE or r fit'),('class_noise_v1/diagnostic.pdf','class_noise_v1/result.json','CLASS BB component only; joint six feature rank driven by EE; independent split-noise approximation'),('spectra_ffp10_first_pair_v1/diagnostic.pdf','spectra_ffp10_first_pair_v1/result.json','First raw pair formal spin-2 operator; U plus/minus are declared encodings; source bridge HOLD'),('cosmos_selection_v1/selection_redshift.pdf','cosmos_selection_v1/result.json','Released zfinal retention includes zero star/artifact placeholders; no galaxy population or completeness inference'),('gaia_frame_v1/frame_controls.pdf','gaia_frame_v1/result.json','4756 outcome-selected frame sources: spin/glide working model; no independent physics inference')]
 if optional.exists():figspec.append(('planck_pr3_peak_closeout_v1/peak_closeout.pdf','planck_pr3_peak_closeout_v1/closeout.json','Planck PR3 source-corrected reconstruction amplitude; shared Planck information retained'))
 figs=[]
 for file,data,caption in figspec:
  p=B/'results'/file
  if not p.exists():raise FileNotFoundError(p)
  figs.append({'file':str(p.relative_to(R)),'sha256':sha(p),'source_result':str((B/'results'/data).relative_to(R)),'caption':caption,'scope':'CONDITIONAL_DIAGNOSTIC','owner':'HTT/obsstat','transfer_source':(pr3['transfer_source'] if file.startswith('planck_pr3_') else json.loads((B/'results'/data).read_text()).get('transfer_source','none'))})
 (O/'figure_inventory.json').write_text(json.dumps(figs,indent=2)+'\n')
 report={'owner':'HTT','scope':'finite currentlyexecuted conditionalobservationalscope','claim_tier':'CONDITIONAL_DIAGNOSTIC','transfer_source':'solver independent diagnostics; fixed released CAMB reference in spectra/lensing; no native Bianchi transfer','source_results':sources,'facts':facts,'figures':'figure_inventory.json','generator':str(Path(__file__).relative_to(R)),'generator_sha256':sha(Path(__file__)),'requested_parent':'gpt-6.1-sol/high','observed_runtime':'UNKNOWN','native_atlas':'ABSENT','physical_MES_unknown_mass':1,'coverage_scope':'named retained products/subsets only, not complete universe ofdata or empiricalphysicalnull','statistic_vs_bias':'MCconditionalranks, scenarioPPC, posteriorfunctions andfiniteinjectionbias keptdistinct','code_git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip()}
 (O/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 om=base['moments']['Omega_m'];ar=base['moments']['H0_rd'];post=cf['runs'][-1]
 md=f'''# HTT 관측 적용: 현재 자료의 조건부 과학 결과

## 주요 결과

**공동 거리 posterior.** Union3의 22개 압축 거리 node와 DESI BGS qiso를 하나의 flat-LCDM 관측법칙으로 적합했다. 기준 cross-covariance 가정 rho=0에서 Ωm={om['mean']:.6f}±{om['sd']:.6f}, H0rd={ar['mean']:.2f}±{ar['sd']:.2f} km/s다. 하나의 공통 magnitude offset을 적분하고 128/256/512차 quadrature를 비교했다. 다섯 rho 가정은 각각 공분산 민감도다. rho에 posterior odds를 붙이지 않았으며 H0와 rd를 따로 측정하지 않는다.

**CF4 선택 관측법칙.** 실제 24개 SNIa-only 그룹의 endpoint H posterior mean은 {post['mean'][0]:.6f} km/s/Mpc, ESS는 {post['ess']:.2f}다. H는 heliocentric endpoint 계수이며 cosmological H0로 해석하지 않는다. 같은 2,048개 draw ID와 weight에서 공유 zero point, dA, ztrue, dL을 계산했다. 반복측정 PPC exceedance는 {latent['repeated_measurement_ppc']['weighted_exceedance_descriptive']:.6f}다. 고정된 32개 조건부 주입 표본이 모두 수치 검사를 통과했다. H의 bias는 {injection['summary']['bias'][0]:.6f}, RMSE는 {injection['summary']['RMSE'][0]:.6f}다. 이는 선언한 law와 근사 Wald 구간의 복원 검사이며 실제 CF4 coverage 인증이 아니다.

**SMICA 온도 morphology.** STF tensor family의 조건부 Monte Carlo rank는 {morph['p_rank_exact']}={morph['p_rank']:.6f}, mask·fitted multipole·통계량의 48개 선택을 포함한 공동 scan rank는 {scan['p_rank_exact']}={scan['p_rank']:.6f}다. 두 절차는 같은 관측 하늘과 같은 300개 signal/noise 행을 사용한다. 각 절차 안의 training 60행과 calibration 240행은 서로 겹치지 않지만, 두 결과는 독립 증거가 아니다. 전달 simulation 모형에 조건부인 회고적 rank이며 역사적 p=.039와의 차이를 개선량으로 해석하지 않는다.

**편광과 spectrum.** BK18의 정확한 BB-only release에서 고정 fiducial HL descriptor Q={bk['Q_HL']:.6f}를 계산하고 native Cobaya와 대조했다. primordial r fit, evidence, PTE가 아니다. CLASS의 200개 고유 split-noise 쌍은 고정 두 mask와 여섯 feature를 사용해 rank={cl['calibration']['rank_p']:.8f}를 얻었다. EE가 joint maximum을 주도하며 독립 split-noise 근사에 조건부다. 관측 half-difference의 signal leakage, foreground, systematics를 검증한 physical null은 아니다.

FFP10의 첫 raw signal/noise 쌍을 NSIDE2048에서 직접 spin-2 변환했다. U±를 명시한 formal operator의 선형성과 signed cross term이 닫혔다. 좌표·polarization·raw-vs-005a processing bridge는 여전히 HOLD다. 한 쌍에서 ensemble null p를 계산하지 않았다. Planck/ACT/SPT spectrum residual은 해당 reference·window·covariance·foreground 조건에 묶이며, BeyondPlanck posterior-mean map도 독립 하늘이 아니다.

**다른 실제 자료.** COSMOS-Web {cosmos['counts']['rows']}행 전체를 79개 batch로 검사했다. zfinal=0 placeholder를 포함한 출판값의 retention이며 galaxy photo-z 분포나 완전성 추정이 아니다. Gaia {gaia['returned_rows']}개 frame source는 공개된 2×2 공분산으로 spin/glide를 적합하고 고정 8개 octant를 leave-out했다. upstream outcome-selected 표본이므로 독립 frame physics 검정이 아니다. CCHP의 {jagb['cchp']['summary']['row_count']}개 photometry 행의 radial color, KiDS의 다섯 N(z), Union3 node 삭제, SDSS observer-box mock과 JWST의 공유 method calibration 결과도 연결했다.

## 관측법칙과 민감도

CF4는 [∫p(eta)Πfi]/[∫p(eta)ΠZi]의 preselection law다. ∫p(eta)Π(fi/Zi)와 다르다. Gaussian redshift 좌표 y=c log(1+Vh/c)와 latent t=c log(1+ztrue)를 구별한다. dL=dA(1+ztrue)^2를 모든 적용 가능한 동일 draw에서 유지했다. Population, velocity width, calibration, absolute scale, finite-distance polynomial은 명시한 scenario다. Calibration prior의 폭을 .05에서 .10 mag로 바꾸는 민감도는 endpoint H를 약 73에서 67로 옮긴다. 유한거리 remainder upper bound를 인증하지 않는다.

공동 거리 law의 rho∈{{0,±.25,±.5}}는 released marginal covariance를 보존하는 가정 family다. 공통 M~Normal(43,5) mag을 정규화된 Gaussian 적분으로 처리했으며 Om~Uniform(.01,.99), H0rd~Uniform(5000,20000) km/s를 사용했다. CF4와 Union3의 object overlap·calibration, endpoint H→H0 bridge가 없어 CF4를 이 posterior에 곱하지 않았다. ACT+Planck, Planck marginal, PR3 reference, primary CMB, CLASS/FFP/mean map은 공유 정보를 가진 source이므로 별도 조건부 결과로 남긴다.

Monte Carlo rank p, posterior predictive PPC, posterior exceedance Pi, legacy power index를 구별한다. 공동 거리 posterior의 동일 ID/weight 함수상은 E, q_deceleration, H0DL/c, H0DA/c, DM/rd, DH/rd다. 같은 congruence의 Sigma2, W2, tilt, curvature, x ceiling에 대한 관측 bridge가 없으므로 physical x,Q,Pi,F4/MES의 unknown mass는 1이다. Flat-LCDM 거리 reference를 가정했다고 미관측 physical sector를 0으로 채우지 않는다.

## 그림과 상세 보고서

[공동 posterior](../posterior/report.md), [동일 draw 거리 함수상](../posterior/legacy_distance_image.pdf), [CF4 posterior](../cf4/posterior_v1/report.md), [CF4 latent/PPC](../cf4/latent_v1/report.md), [CF4 주입](../cf4/injection_v1/report.md), [BK18](../bk18_fixed_fiducial_v1/report.md), [CLASS](../class_noise_v1/report.md), [FFP 첫 쌍](../spectra_ffp10_first_pair_v1/report.md), [Gaia](../gaia_frame_v1/report.md), [COSMOS](../cosmos_selection_v1/report.md), [JAGB/KiDS](../jagb_kids_v1/report.md).

모든 수치는 report.json의 원본 result에 연결되며 figure_inventory.json이 그림과 source를 연결한다. PDF는 scientific_report.pdf다. 기존 RB00 pilot·calibration·response laboratory, OA/DESI, R7/R8 density·legacy adapter와 covariance/operator helper를 재사용했다. 상위 증명과 동일 입력의 큰 계산을 다시 시작하지 않았다.

## 검증과 잔여 입력

각 묶음에는 저자와 별도의 독립 read-only reviewer를 요청했다(requested Astra/xhigh; observed runtime UNKNOWN). 검토와 push는 scientific admission이나 main merge가 아니다. 원래 RB10/11/12/15의 전체 physical gate는 보존하고, 조건부 거리·보고서는 별도 RB23/25로 연결했다.

남은 입력은 global-history response, 같은 congruence의 physical tensor/MES ceiling·remainder, 실제 full-survey selection·calibration·object overlap law, raw-QE filter·mean field·bias, external native atlas다. FFP source-variant/convention bridge와 CLASS의 physical split law도 남는다. 정확한 상태와 재개 행동은 ../../RETURN.md 및 ../../BLOCKERS.json에 기록한다. 이 저장소에서 새 native Bianchi solver를 구현하지 않았다.
'''
 if optional.exists():
  v=pr3['variants'][0]['fit'];v2=pr3['variants'][1]['fit']
  if md.count('## 관측법칙과 민감도')!=1:raise ValueError('Planck result insertion heading changed')
  md=md.replace('## 관측법칙과 민감도',f"Planck PR3의 정확한 source window·linear correction·공분산으로 reconstructed φφ reference amplitude A={v['amplitude']:.6f}±{v['conditional_se']:.6f}를 얻었다. fixed-CMB variant는 {v2['amplitude']:.6f}±{v2['conditional_se']:.6f}의 같은 자료 민감도다. reference cosmology 자체가 Planck lensing을 사용하므로 release-consistency 결과다. CMB-marginalized 제품도 primary CMB 정보를 사용했으며 독립 calibration이나 독립 likelihood가 아니다. [상세 source와 native 대조](../planck_pr3_peak_closeout_v1/report.md).\n\n## 관측법칙과 해석")
 (O/'SCIENTIFIC_REPORT_KO.md').write_text(md)
 tex=r'''\documentclass[10pt]{article}
\usepackage[margin=0.75in]{geometry}
\usepackage{graphicx,booktabs,amsmath,hyperref}
\hypersetup{colorlinks=true,urlcolor=blue}
\title{HTT observational applications: conditional results from retained products}
\author{HTT observational research}\date{14 October 2026}
\begin{document}\maketitle
\begin{abstract}
We executed retained-product observational diagnostics, a selected 24-group CF4
scenario posterior and latent predictive image, and a joint Union3--DESI compressed
distance posterior. Scientific interpretation remains conditional on the declared
processing, selection, covariance and model assumptions. No physical shear, global
tilt, native Bianchi family, or physical MES admission follows.
\end{abstract}
\section{Joint distance result}
Union3 has 22 compressed nodes, not 22 independent supernovae. One DESI BGS
$q_{\rm iso}$ summary enters once. In the flat late-time matter--Lambda scenario,
$E(z)^2=\Omega_m(1+z)^3+1-\Omega_m$ and $I(z)=\int_0^z du/E(u)$.
We analytically integrate a common magnitude offset $M\sim N(43,5^2)$.
Proper priors are $\Omega_m\sim U(.01,.99)$ and $H_0r_d\sim U(5000,20000)$ km/s.
The reference factorization scenario gives $\Omega_m=@@OM@@$ and
$H_0r_d=@@AR@@$ km/s. It does not separate $H_0$ and $r_d$.
Five covariance scenarios $\rho=0,\pm.25,\pm.5$ preserve the released marginal
covariances. These are assumptions, not measured cross-covariances or posterior odds.
Orders128,256,512 close the declared quadrature criteria. The posterior image retains
all original 262144 node IDs and weights. Physical MES fields remain unavailable,
with unknown mass 1; imposed distance geometry is not measured zero anisotropy.
\section{Selected CF4 scenario}
For 24 SNIa-only grouped observations, $x=\log d_A$, $t=c\log(1+z_{\rm true})$,
$\mu=25+(5/\ln10)x+2(5/\ln10)t/c+\eta$.
A single shared zero point is integrated with the preselection law
$L=[\int p(\eta)\prod_i f_i d\eta]/[\int p(\eta)\prod_i Z_i d\eta]$.
The finite-box endpoint posterior has 2048 nodes and ESS@@ESS@@.
The endpoint coefficient is not cosmological $H_0$.
Same-state $d_L=d_A(1+z_{\rm true})^2$ and repeated-measurement PPC give
exceedance @@PPC@@; this is not a uniform null p-value. Thirty-two frozen same-law
injections resolve; endpoint-H bias @@BIAS@@ and RMSE @@RMSE@@.
The interval study is finite conditional Gaussian-Wald calibration, not empirical
CF4 coverage. Population, velocity width, calibration and remainder are scenarios.
No certified remainder upper bound is obtained.
\section{Temperature and polarization}
SMICA tensor-family conditional rank is@@MORPH@@; a joint 48-choice processing scan
has rank @@SCAN@@. Both procedures reuse the same sky and the same 300 paired simulations. Each has
disjoint training 60 and calibration 240 subsets, but the two results are not independent. No
improvement relative to historical p=.039 is inferred. Temperature quadrupole is not
physical shear, and residual ell1 is not a physical dipole.
BK18's actual 66 correlatedBB spectra in 9 bins give fixed-fiducial HL descriptor
$Q_{\rm HL}=@@BK@@$, with independent/native algebra parity. It is not a PTE,
normalized evidence or primordial-r fit. CLASS 200 unique-per-split noise pairs
produce a six-feature joint conditional rank @@CLASS@@; EE drives this maximum,
whereas the displayed BB components are near their noise means. Its independent
split-noise law is an approximation; signal leakage/systematics are not calibrated.
The first raw FFP10 pair closes six-transform spin2 linearity and signed cross-term
checks under two formal U encodings. Raw-product frame/convention/processing binding
remains HOLD; no ensemble or actual-data inference is made.
\section{Other retained products and limitations}
The ACT--Planck released joint lensing amplitude, its Planck marginal and the Planck
PR3 reference are overlapping products; they are not multiplied independently.
Source-matched Planck/ACT/SPT spectrum residuals retain their reference, covariance
and foreground/calibration scope. BeyondPlanck mean maps are not independent skies.
COSMOS scans all released 784016 rows, including zero zfinal placeholders; retention
is not completeness or a galaxy-population law. Gaia fits 4756 selected frame sources
with 2x2 covariance blocks; upstream outcome selection prevents an independent physical
frame test. JWST/CCHP photometry, KiDS n(z), Union3 deletion and SDSS observer-box
controls retain their shared-source and conditional assumptions.
\section{Provenance and review}
Exact generating result files, code/input identities, fixed assumptions, figures and
review scopes accompany this report in report.json and figure\_inventory.json.
Requested author/reviewer settings are separate from observed runtime UNKNOWN.
Prior scoped results and upper proofs are reused. Physical joint-model and external
native atlas dependencies remain gated. See the Korean report and RETURN for exact
missing inputs and resume commands. Publication is not scientific admission.
\paragraph{Primary source context.}
\href{https://github.com/rubind/union3_release}{Union3 release};
\href{https://arxiv.org/abs/1807.06208}{Planck component separation};
\href{https://arxiv.org/abs/1807.06210}{Planck lensing};
\href{https://github.com/ACTCollaboration/act_dr6_lenslike}{ACT lensing software};
\href{https://arxiv.org/abs/2110.00483}{BICEP/Keck XIII};
\href{https://lambda.gsfc.nasa.gov/product/class/}{CLASS release};
\href{https://cosmos2025.iap.fr/catalog.html}{COSMOS-Web};
\href{https://arxiv.org/abs/2204.12574}{Gaia celestial frame}.
'''
 values={'OM':f"{om['mean']:.6f}\\pm{om['sd']:.6f}",'AR':f"{ar['mean']:.2f}\\pm{ar['sd']:.2f}",'ESS':f"{post['ess']:.2f}",'PPC':f"{latent['repeated_measurement_ppc']['weighted_exceedance_descriptive']:.6f}",'BIAS':f"{injection['summary']['bias'][0]:.6f}",'RMSE':f"{injection['summary']['RMSE'][0]:.6f}",'MORPH':morph['p_rank_exact'],'SCAN':scan['p_rank_exact'],'BK':f"{bk['Q_HL']:.6f}",'CLASS':f"{cl['calibration']['rank_p']:.8f}"}
 for k,v in values.items():tex=tex.replace('@@'+k+'@@',v)
 if optional.exists():
  v=pr3['variants'][0]['fit']
  paragraph=f"The source-qualified Planck PR3 corrected reference amplitude is $A_{{PP}}={v['amplitude']:.6f}\\pm{v['conditional_se']:.6f}$. Its reference cosmology already includes Planck lensing; this is release consistency, not independent calibration. CMB marginalization has used primary CMB information and does not establish product independence.\n"
  tex=tex.replace('Source-matched Planck/ACT/SPT',paragraph+'Source-matched Planck/ACT/SPT')
 for f in figs:
  relative=Path(f['file']).relative_to(B.relative_to(R)/'results');tex+='\n\\clearpage\\begin{figure}[p]\\centering\n\\includegraphics[width=\\linewidth,height=.70\\textheight,keepaspectratio]{../'+str(relative)+'}\n\\caption{'+f['caption'].replace('_',r'\_').replace('%',r'\%')+'}\n\\end{figure}\n'
 tex+='\\end{document}\n';(O/'scientific_report.tex').write_text(tex)
 print(json.dumps({'report':str(O),'figures':len(figs),'source_artifacts':len(sources)}))
if __name__=='__main__':build()
