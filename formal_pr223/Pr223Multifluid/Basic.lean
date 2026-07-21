/- PR-223 antipodal two-stream moment cone (Lean 4 core). Streams +1, -1 with
   unit weight. Zero net flux, nonzero trace, traceless nonzero anisotropic
   stress. Convention/mechanics only. -/
namespace Pr223Multifluid

-- first moment (net flux): 1*(+1) + 1*(-1)
def firstMoment : Int := 1 * 1 + 1 * (-1)

-- second-moment trace (tilt energy): 1*1*1 + 1*(-1)*(-1)
def traceK : Int := 1 * 1 * 1 + 1 * (-1) * (-1)

-- 3*Pi = 3*diag(2,0,0) - 2*I = diag(4,-2,-2)
def aniso3Diag : Int × Int × Int := (4, -2, -2)
def aniso3Trace : Int := aniso3Diag.1 + aniso3Diag.2.1 + aniso3Diag.2.2

def checks : Bool :=
  decide (firstMoment = 0)          -- zero net flux
  && decide (traceK = 2) && decide (traceK > 0)   -- nonzero tilt energy
  && decide (aniso3Trace = 0)        -- anisotropic stress is traceless
  && decide (aniso3Diag.1 ≠ 0)       -- but nonzero

theorem all_checks : checks = true := by native_decide

end Pr223Multifluid
