"""R92 exact Gaunt selection under a quadrupolar angular modulation.

This is a *toy covariance model*, not a validated Bianchi radiation hierarchy.
Shows how high-l off-diagonal modes can add information beyond C_l scalars,
and how parity/triangle rules restrict couplings L=2.
"""
from __future__ import annotations
import json,math
from sympy import N
from sympy.physics.wigner import wigner_3j

def count_pair_modes(lmin,lmax):
    # The off-diagonal branch l' = l+2 with M=0 has 2*l+1 allowed m.
    return sum(2*l+1 for l in range(lmin,lmax-1))
def examine():
    entries=[]
    for l in (4,16,40,80):
        cells=[]
        for lp in range(l-3,l+4):
            if lp<0:continue
            val=wigner_3j(l,2,lp,0,0,0)
            if lp%2==l%2 and abs(lp-l)<=2:
                if val==0:raise AssertionError("allowed coupling falsely zero")
            else:
                if val!=0:raise AssertionError("parity/triangle forbidden coupling nonzero")
            cells.append({"lp":lp,"threej_000":str(val),"numerical":float(N(val,12))})
        entries.append({"l":l,"cells":cells})
    samples={
      "ell_le_16":count_pair_modes(2,16),
      "ell_le_64":count_pair_modes(2,64),
      "ell_le_128":count_pair_modes(2,128)
    }
    return {"schema":"htt.r92.gaunt_high_ell_toy_construction/1",
            "model":"T'(n)=[1+g*Y20(n)]s(n), s Gaussian isotropic with C_l; first order in g",
            "coupling_formula":"G=(-1)^m sqrt[(2l+1)*5*(2lp+1)/(4pi)] (l 2 lp;0 0 0)(l 2 lp;-m M mp)",
            "linear_covariance":"Cov[a_lm,a_l'm'*]=C_l delta_l l' delta_m m' + g(C_l+C_l') G + O(g²)",
            "Gaunt_L2_selection":"abs(l-l')<=2, l+l'+2 even; for scalar M0, m=m'. Thus l'=l,l+-2",
            "exact_checks":entries,
            "offdiagonal_l_to_lplus2_M0_mode_count":samples,
            "mode_count_ratio_64_vs_16":samples["ell_le_64"]/samples["ell_le_16"],
            "mode_count_is_not_Fisher_information":True,
            "bandpower_only_plik_sufficient":False,
            "physical_Bianchi_polarized_all_m_transfer_replaced":False,
            "cosmological_significance":"UNQUALIFIED_TOY_SOURCE_SHAPE",
            "foreground_mask_noise_covariance":"REQUIRED_FOR_REAL_HIGH_ELL_ANALYSIS"}
if __name__=="__main__":print(json.dumps(examine(),ensure_ascii=False,indent=2))
