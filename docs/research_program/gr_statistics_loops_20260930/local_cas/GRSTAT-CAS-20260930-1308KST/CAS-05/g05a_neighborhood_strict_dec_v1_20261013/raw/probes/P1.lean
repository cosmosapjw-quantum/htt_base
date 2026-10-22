import Mathlib
abbrev I := Fin 4
def sum4 (f : I → ℝ) : ℝ := f 0 + f 1 + f 2 + f 3
noncomputable def pd (f : (I → ℝ) → ℝ) (c : I) (x : I → ℝ) : ℝ :=
  fderiv ℝ f x (Pi.single c 1)

theorem pd_add {f g : (I → ℝ) → ℝ} {x : I → ℝ} (c : I)
    (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g x) :
    pd (fun y => f y + g y) c x = pd f c x + pd g c x := by
  simp [pd, fderiv_fun_add hf hg]
theorem pd_sub {f g : (I → ℝ) → ℝ} {x : I → ℝ} (c : I)
    (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g x) :
    pd (fun y => f y - g y) c x = pd f c x - pd g c x := by
  simp [pd, fderiv_fun_sub hf hg]
theorem pd_mul {f g : (I → ℝ) → ℝ} {x : I → ℝ} (c : I)
    (hf : DifferentiableAt ℝ f x) (hg : DifferentiableAt ℝ g x) :
    pd (fun y => f y * g y) c x = f x * pd g c x + g x * pd f c x := by
  simp [pd, fderiv_fun_mul hf hg]
theorem pd_const (k : ℝ) (c : I) (x : I → ℝ) : pd (fun _ => k) c x = 0 := by
  simp [pd]
theorem pd_coord (a c : I) (x : I → ℝ) :
    pd (fun y => y a) c x = if c = a then 1 else 0 := by
  unfold pd
  rw [(hasFDerivAt_apply a x).fderiv]
  simp [Pi.single_apply]
theorem pd_exp {f : (I → ℝ) → ℝ} {x : I → ℝ} (c : I)
    (hf : DifferentiableAt ℝ f x) :
    pd (fun y => Real.exp (f y)) c x = Real.exp (f x) * pd f c x := by
  simp [pd, fderiv_exp hf]
theorem pd_pow {f : (I → ℝ) → ℝ} {x : I → ℝ} (c : I) (n : ℕ)
    (hf : DifferentiableAt ℝ f x) :
    pd (fun y => f y ^ n) c x = n * f x ^ (n-1) * pd f c x := by
  simp [pd, fderiv_pow n hf]
  ring

noncomputable def phi (b lam : ℝ) (X : I → ℝ) : ℝ :=
  -b * X 0 ^ 2 - b / 2 * (X 1 ^ 2 + X 2 ^ 2 + X 3 ^ 2) +
    lam / 2 * X 0 ^ 2 * X 1

example (b lam : ℝ) : ContDiff ℝ 2 (phi b lam) := by unfold phi; fun_prop
example (b lam : ℝ) : ContDiff ℝ 2 (fun y => Real.exp (2 * phi b lam y)) := by unfold phi; fun_prop

theorem pd_phi0 (b lam : ℝ) (y : I → ℝ) :
    pd (phi b lam) 0 y = -2*b*y 0 + lam*y 0*y 1 := by
  unfold phi
  simp (disch := fun_prop) only [pd_add, pd_sub, pd_mul, pd_pow, pd_const, pd_coord]
  simp
  ring
