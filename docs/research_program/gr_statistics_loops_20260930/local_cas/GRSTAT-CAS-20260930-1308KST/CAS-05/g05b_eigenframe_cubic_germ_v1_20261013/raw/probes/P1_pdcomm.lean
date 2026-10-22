import Mathlib
import G05AConformalDEC
open G05AConformalDEC
example {f : (I → ℝ) → ℝ} {x : I → ℝ} (hf : ContDiffAt ℝ 2 f x) (a i : I) :
    pd (fun z => pd f a z) i x = pd (fun z => pd f i z) a x := by
  have hs := hf.isSymmSndFDerivAt (by simp)
  have hd : DifferentiableAt ℝ (fderiv ℝ f) x :=
    (hf.fderiv_right (m := 1) (by norm_num)).differentiableAt (by norm_num)
  unfold pd
  rw [fderiv_clm_apply hd (differentiableAt_const _), fderiv_clm_apply hd (differentiableAt_const _)]
  trace_state
  simp
  trace_state
  exact hs _ _
