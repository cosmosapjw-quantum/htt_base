import ExactBoostMap

open ExactBoostMap

namespace NonlinearRemainder

abbrev E3 := EuclideanSpace ℝ (Fin 3)
def toE (v : V3) : E3 := WithLp.toLp 2 v
def eNorm (v : V3) : ℝ := ‖toE v‖
noncomputable def matrixOp (D : M3) : E3 →L[ℝ] E3 :=
  (Matrix.toEuclideanLin D).toContinuousLinearMap
noncomputable def opNorm (D : M3) : ℝ := ‖matrixOp D‖
noncomputable def remainder (D : M3) (beta : V3) : V3 :=
  dipoleMap D beta + 2 • D.mulVec beta

#check EuclideanSpace.inner_eq_star_dotProduct
#check real_inner_self_eq_norm_sq
#check Matrix.toEuclideanLin_apply_piLp_toLp
#check ContinuousLinearMap.le_opNorm
#check abs_real_inner_le_norm

end NonlinearRemainder
