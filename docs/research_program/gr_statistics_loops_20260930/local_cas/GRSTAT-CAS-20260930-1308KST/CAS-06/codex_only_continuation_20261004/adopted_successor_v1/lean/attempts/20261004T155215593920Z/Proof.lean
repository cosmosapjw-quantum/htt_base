import Mathlib

/-!
Finite subcomponents of the owner-adopted CAS-06 successor.  This file intentionally
contains no declaration of the full C01--C04 conjunction: a compiled sublemma must
not be mistaken for the required tensor/action derivation.
-/

namespace CAS06Adopted
noncomputable section
open Filter Topology

/- The positive domain of the fixed-family radius parameter. -/
def RadiusDomain (y : ℝ) : Prop := 0 < y ∧ y < 1

def C (μ Λ : ℝ) : ℝ := 2 * μ + Λ / 3
def B (μ κ p Λ : ℝ) : ℝ := μ + κ * p / 2 - Λ / 3
def radius (μ Λ y : ℝ) : ℝ := y / Real.sqrt (C μ Λ)
def lapseAtRadius (μ Λ y : ℝ) : ℝ := 1 - C μ Λ * radius μ Λ y ^ 2
def accelFromRadius (c μ κ p Λ y : ℝ) : ℝ :=
  c ^ 2 * |B μ κ p Λ| * radius μ Λ y / Real.sqrt (lapseAtRadius μ Λ y)
def accelAsY (c μ κ p Λ y : ℝ) : ℝ :=
  (c ^ 2 * |B μ κ p Λ| / Real.sqrt (C μ Λ)) * y / Real.sqrt (1 - y ^ 2)

theorem radius_pos {μ Λ y : ℝ} (hC : 0 < C μ Λ) (hy : RadiusDomain y) :
    0 < radius μ Λ y := by
  unfold radius
  exact div_pos hy.1 (Real.sqrt_pos.2 hC)

theorem lapse_reduction {μ Λ y : ℝ} (hC : 0 < C μ Λ) :
    lapseAtRadius μ Λ y = 1 - y ^ 2 := by
  unfold lapseAtRadius radius
  have hroot : (Real.sqrt (C μ Λ)) ^ 2 = C μ Λ := Real.sq_sqrt hC.le
  have hne : Real.sqrt (C μ Λ) ≠ 0 := ne_of_gt (Real.sqrt_pos.2 hC)
  field_simp
  nlinarith

theorem lapse_pos {μ Λ y : ℝ} (hC : 0 < C μ Λ)
    (hy : RadiusDomain y) : 0 < lapseAtRadius μ Λ y := by
  rw [lapse_reduction hC]
  rcases hy with ⟨hy0, hy1⟩
  nlinarith [sq_nonneg (1 - y)]

theorem accel_reduction {c μ κ p Λ y : ℝ} (hC : 0 < C μ Λ) :
    accelFromRadius c μ κ p Λ y = accelAsY c μ κ p Λ y := by
  unfold accelFromRadius accelAsY radius
  rw [lapse_reduction hC]
  ring

theorem accel_positive {c μ κ p Λ y : ℝ}
    (hc : 0 < c) (hC : 0 < C μ Λ) (hB : B μ κ p Λ ≠ 0)
    (hy : RadiusDomain y) : 0 < accelAsY c μ κ p Λ y := by
  unfold accelAsY
  have hb : 0 < |B μ κ p Λ| := abs_pos.2 hB
  have hden : 0 < Real.sqrt (1 - y ^ 2) := by
    apply Real.sqrt_pos.2
    rcases hy with ⟨hy0, hy1⟩
    nlinarith [sq_nonneg (1 - y)]
  exact div_pos (mul_pos (div_pos (mul_pos (sq_pos_of_pos hc) hb)
    (Real.sqrt_pos.2 hC)) hy.1) hden

theorem accel_limit {c μ κ p Λ : ℝ}
    (hc : 0 < c) (hC : 0 < C μ Λ) (hB : B μ κ p Λ ≠ 0) :
    Tendsto (accelAsY c μ κ p Λ) (𝓝[<] (1 : ℝ)) atTop := by
  have hbase : Tendsto (fun y : ℝ => 1 - y ^ 2)
      (𝓝[<] (1 : ℝ)) (𝓝 (0 : ℝ)) := by
    have hid : Tendsto (fun y : ℝ => y) (𝓝[<] (1 : ℝ)) (𝓝 (1 : ℝ)) :=
      tendsto_id.mono_left nhdsWithin_le_nhds
    convert (tendsto_const_nhds.sub (hid.pow 2)) using 1 <;>
      norm_num
  have hpos : ∀ᶠ y : ℝ in 𝓝[<] (1 : ℝ), 0 < 1 - y ^ 2 := by
    filter_upwards [self_mem_nhdsWithin,
      (nhdsWithin_le_nhds (Ioi_mem_nhds (show (0 : ℝ) < 1 by norm_num)))]
      with y hy1 hy0
    change y < 1 at hy1
    change 0 < y at hy0
    have hprod : 0 < (1 - y) * (1 + y) :=
      mul_pos (sub_pos.mpr hy1) (by linarith)
    nlinarith
  have hroot : Tendsto (fun y : ℝ => Real.sqrt (1 - y ^ 2))
      (𝓝[<] (1 : ℝ)) (𝓝[>] (0 : ℝ)) := by
    apply tendsto_nhdsWithin_iff.mpr
    refine ⟨?_, ?_⟩
    · simpa only [Function.comp_def, Real.sqrt_zero] using
        Real.continuous_sqrt.continuousAt.tendsto.comp hbase
    · filter_upwards [hpos] with y hy
      exact Real.sqrt_pos.2 hy
  have htop : Tendsto (fun y : ℝ => (Real.sqrt (1 - y ^ 2))⁻¹)
      (𝓝[<] (1 : ℝ)) atTop := by
    convert hroot.inv_tendsto_nhdsGT_zero using 1
    ext y
    rfl
  have hcoef : 0 < c ^ 2 * |B μ κ p Λ| / Real.sqrt (C μ Λ) :=
    div_pos (mul_pos (sq_pos_of_pos hc) (abs_pos.2 hB)) (Real.sqrt_pos.2 hC)
  have hnum : Tendsto (fun y : ℝ =>
      (c ^ 2 * |B μ κ p Λ| / Real.sqrt (C μ Λ)) * y)
      (𝓝[<] (1 : ℝ))
      (𝓝 (c ^ 2 * |B μ κ p Λ| / Real.sqrt (C μ Λ))) := by
    have hid : Tendsto (fun y : ℝ => y) (𝓝[<] (1 : ℝ)) (𝓝 (1 : ℝ)) :=
      tendsto_id.mono_left nhdsWithin_le_nhds
    simpa using hid.const_mul
      (c ^ 2 * |B μ κ p Λ| / Real.sqrt (C μ Λ))
  have := hnum.pos_mul_atTop hcoef htop
  convert this using 1
  ext y
  dsimp [accelAsY]
  ring

#print axioms radius_pos
#print axioms lapse_reduction
#print axioms lapse_pos
#print axioms accel_reduction
#print axioms accel_positive
#print axioms accel_limit

/- C01: actual first derivatives of the admitted metric and radial mass lapse.
   These are prerequisites for a complete connection/curvature calculation. -/
def metric00 (ν : ℝ → ℝ) (r : ℝ) : ℝ := -Real.exp (2 * ν r)
def metric11 (F : ℝ → ℝ) (r : ℝ) : ℝ := (F r)⁻¹
def metric22 (r : ℝ) : ℝ := r ^ 2
def metric33 (r θ : ℝ) : ℝ := r ^ 2 * Real.sin θ ^ 2
def massLapse (m : ℝ → ℝ) (Λ r : ℝ) : ℝ := 1 - 2 * m r / r - Λ * r ^ 2 / 3

theorem metric00_derivative {ν : ℝ → ℝ} {r νr : ℝ}
    (hν : HasDerivAt ν νr r) :
    HasDerivAt (metric00 ν) (-2 * Real.exp (2 * ν r) * νr) r := by
  convert ((Real.hasDerivAt_exp (2 * ν r)).comp r
    ((hasDerivAt_const r (2 : ℝ)).mul hν)).neg using 1 <;>
    try { ext x; rfl } <;> ring

theorem metric11_derivative {F : ℝ → ℝ} {r Fr : ℝ}
    (hF : HasDerivAt F Fr r) (hF0 : F r ≠ 0) :
    HasDerivAt (metric11 F) (-Fr / (F r) ^ 2) r := by
  convert hF.inv hF0 using 1
  all_goals rfl

theorem metric22_derivative (r : ℝ) :
    HasDerivAt metric22 (2 * r) r := by
  simpa [metric22] using! (hasDerivAt_pow 2 r :
    HasDerivAt (fun x : ℝ => x ^ 2) ((2 : ℝ) * r ^ (2 - 1)) r)

theorem metric33_radial_derivative (r θ : ℝ) :
    HasDerivAt (fun s : ℝ => metric33 s θ)
      (2 * r * Real.sin θ ^ 2) r := by
  simpa only [metric33, metric22] using
    (metric22_derivative r).mul_const (Real.sin θ ^ 2)

theorem metric33_angular_derivative (r θ : ℝ) :
    HasDerivAt (metric33 r)
      (2 * r ^ 2 * Real.sin θ * Real.cos θ) θ := by
  convert ((Real.hasDerivAt_sin θ).mul (Real.hasDerivAt_sin θ)).const_mul
    (r ^ 2) using 1
  all_goals first
    | rfl
    | (funext t; change r ^ 2 * Real.sin t ^ 2 =
        r ^ 2 * (Real.sin t * Real.sin t); ring)
    | ring

/- The following Christoffel slots are computed from the metric-derivative
   formula, with no Einstein or curvature target inserted. -/
def gamma001 (ν νr : ℝ) : ℝ :=
  ((-Real.exp (2 * ν))⁻¹ * (-2 * Real.exp (2 * ν) * νr)) / 2

theorem gamma001_eq (ν νr : ℝ) : gamma001 ν νr = νr := by
  unfold gamma001
  have hE : Real.exp (2 * ν) ≠ 0 := (Real.exp_pos _).ne'
  field_simp <;> ring

theorem gamma001_from_metric {ν : ℝ → ℝ} {r νr : ℝ}
    (hν : HasDerivAt ν νr r) :
    ((metric00 ν r)⁻¹ * deriv (metric00 ν) r) / 2 = νr := by
  rw [(metric00_derivative hν).deriv]
  exact gamma001_eq (ν r) νr

def gamma100 (F ν νr : ℝ) : ℝ :=
  -(F * (-2 * Real.exp (2 * ν) * νr)) / 2

theorem gamma100_eq (F ν νr : ℝ) :
    gamma100 F ν νr = F * Real.exp (2 * ν) * νr := by
  unfold gamma100
  ring

theorem gamma100_from_metric {F ν : ℝ → ℝ} {r νr : ℝ}
    (hν : HasDerivAt ν νr r) :
    -(F r * deriv (metric00 ν) r) / 2 = F r * Real.exp (2 * ν r) * νr := by
  rw [(metric00_derivative hν).deriv]
  exact gamma100_eq (F r) (ν r) νr

def massLapseJet (m mr Λ r : ℝ) : ℝ :=
  -(2 * mr / r) + 2 * m / r ^ 2 - 2 * Λ * r / 3

theorem massLapse_derivative {m : ℝ → ℝ} {Λ r mr : ℝ}
    (hr : r ≠ 0) (hm : HasDerivAt m mr r) :
    HasDerivAt (massLapse m Λ) (massLapseJet (m r) mr Λ r) r := by
  have hquot : HasDerivAt (fun s : ℝ => 2 * m s / s)
      ((2 * mr * r - 2 * m r) / r ^ 2) r := by
    convert (hm.const_mul (2 : ℝ)).div (hasDerivAt_id r) hr using 1 <;>
      try {rfl} <;> simp [id] <;> ring
  have hΛ : HasDerivAt (fun s : ℝ => Λ * s ^ 2 / 3)
      (2 * Λ * r / 3) r := by
    convert ((metric22_derivative r).const_mul Λ).div_const (3 : ℝ) using 1 <;>
      try {rfl} <;> ring
  convert ((hasDerivAt_const r (1 : ℝ)).sub hquot).sub hΛ using 1
  all_goals first
    | rfl
    | (funext s; rfl)
    | (unfold massLapseJet; field_simp [hr]; ring)

theorem tov_temporal_numerator {m mr Λ κ ε r : ℝ}
    (hr : r ≠ 0) (hTOV : mr = κ * r ^ 2 * ε / 2) :
    1 - (1 - 2 * m / r - Λ * r ^ 2 / 3) -
      r * massLapseJet m mr Λ r - Λ * r ^ 2 = κ * r ^ 2 * ε := by
  rw [hTOV]
  unfold massLapseJet
  field_simp
  ring

/- Literal chart metric and its first coordinate derivative jets.  The radial
   and angular diagonal entries are the derivatives proved above. -/
def chartMetric (ν F r θ : ℝ) (a b : Fin 4) : ℝ :=
  if a != b then 0 else
  if a = 0 then -Real.exp (2 * ν) else
  if a = 1 then F⁻¹ else
  if a = 2 then r ^ 2 else r ^ 2 * Real.sin θ ^ 2

def chartInverse (ν F r θ : ℝ) (a b : Fin 4) : ℝ :=
  if a != b then 0 else
  if a = 0 then -(Real.exp (2 * ν))⁻¹ else
  if a = 1 then F else
  if a = 2 then (r ^ 2)⁻¹ else (r ^ 2 * Real.sin θ ^ 2)⁻¹

def chartPartial (ν F νr Fr r θ : ℝ) (dir a b : Fin 4) : ℝ :=
  if a != b then 0 else
  if dir = 1 then
    if a = 0 then -2 * Real.exp (2 * ν) * νr else
    if a = 1 then -Fr / F ^ 2 else
    if a = 2 then 2 * r else 2 * r * Real.sin θ ^ 2
  else if dir = 2 ∧ a = 3 then
    2 * r ^ 2 * Real.sin θ * Real.cos θ
  else 0

def chartGamma (ν F νr Fr r θ : ℝ) (a b c : Fin 4) : ℝ :=
  (∑ d : Fin 4, chartInverse ν F r θ a d *
      (chartPartial ν F νr Fr r θ b d c +
       chartPartial ν F νr Fr r θ c d b -
       chartPartial ν F νr Fr r θ d b c)) / 2

theorem chartGamma001 (ν F νr Fr r θ : ℝ) :
    chartGamma ν F νr Fr r θ 0 0 1 = νr := by
  simp [chartGamma, chartInverse, chartPartial]
  have hE : Real.exp (2 * ν) ≠ 0 := (Real.exp_pos _).ne'
  field_simp <;> ring

theorem chartGamma100 (ν F νr Fr r θ : ℝ) :
    chartGamma ν F νr Fr r θ 1 0 0 = F * Real.exp (2 * ν) * νr := by
  simp [chartGamma, chartInverse, chartPartial]
  ring

def chartGammaTable (ν F νr Fr r θ : ℝ) (a b c : Fin 4) : ℝ :=
  if a = 0 ∧ ((b = 0 ∧ c = 1) ∨ (b = 1 ∧ c = 0)) then νr else
  if a = 1 ∧ b = 0 ∧ c = 0 then F * Real.exp (2 * ν) * νr else
  if a = 1 ∧ b = 1 ∧ c = 1 then -Fr / (2 * F) else
  if a = 1 ∧ b = 2 ∧ c = 2 then -F * r else
  if a = 1 ∧ b = 3 ∧ c = 3 then -F * r * Real.sin θ ^ 2 else
  if a = 2 ∧ ((b = 1 ∧ c = 2) ∨ (b = 2 ∧ c = 1)) then r⁻¹ else
  if a = 2 ∧ b = 3 ∧ c = 3 then -Real.sin θ * Real.cos θ else
  if a = 3 ∧ ((b = 1 ∧ c = 3) ∨ (b = 3 ∧ c = 1)) then r⁻¹ else
  if a = 3 ∧ ((b = 2 ∧ c = 3) ∨ (b = 3 ∧ c = 2)) then
    Real.cos θ / Real.sin θ else 0

theorem chartGamma_table (ν F νr Fr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    ∀ a b c : Fin 4,
      chartGamma ν F νr Fr r θ a b c = chartGammaTable ν F νr Fr r θ a b c := by
  intro a b c
  fin_cases a <;> fin_cases b <;> fin_cases c <;>
    simp [chartGamma, chartGammaTable, chartInverse, chartPartial] <;>
    field_simp [hF, hr, hs] <;> ring
  all_goals
    rw [Fin.sum_univ_four]
    simp

/- The static matched event has U⁰=c.  This is its radial coordinate
   acceleration Γ¹₀₀ (U⁰)² and its positive rest-frame magnitude.  The
   following uses the TOV ν' jet rather than assuming the acceleration answer. -/
def tovNuJet (m κ α ε Λ r F : ℝ) : ℝ :=
  (m + κ * α * ε * r ^ 3 / 2 - Λ * r ^ 3 / 3) / (r ^ 2 * F)

theorem matched_tovNuJet {μ κ α ε Λ r F : ℝ}
    (hr : r ≠ 0) (hF : F ≠ 0) :
    tovNuJet (μ * r ^ 3) κ α ε Λ r F =
      B μ κ (α * ε) Λ * r / F := by
  unfold tovNuJet B
  field_simp <;> ring

theorem matched_acceleration_from_connection
    {c μ κ α ε Λ r F Fr θ : ℝ}
    (hc : 0 < c) (hr : 0 < r) (hF : 0 < F) :
    |chartGamma 0 F (tovNuJet (μ * r ^ 3) κ α ε Λ r F) Fr r θ 1 0 0 * c ^ 2| /
      Real.sqrt F = c ^ 2 * |B μ κ (α * ε) Λ| * r / Real.sqrt F := by
  have hν := matched_tovNuJet (μ := μ) (κ := κ) (α := α)
    (ε := ε) (Λ := Λ) (r := r) (F := F) hr.ne' hF.ne'
  rw [chartGamma100]
  rw [hν]
  simp only [mul_zero, Real.exp_zero, mul_one]
  have hΓ : F * (B μ κ (α * ε) Λ * r / F) =
      B μ κ (α * ε) Λ * r := by field_simp
  rw [hΓ, abs_mul, abs_mul, abs_of_pos hr, abs_of_pos (sq_pos_of_pos hc)]
  ring

theorem family_acceleration_from_connection
    {c μ κ α ε Λ y Fr θ : ℝ}
    (hc : 0 < c) (hC : 0 < C μ Λ) (hy : RadiusDomain y) :
    |chartGamma 0 (lapseAtRadius μ Λ y)
      (tovNuJet (μ * radius μ Λ y ^ 3) κ α ε Λ
        (radius μ Λ y) (lapseAtRadius μ Λ y))
      Fr (radius μ Λ y) θ 1 0 0 * c ^ 2| /
      Real.sqrt (lapseAtRadius μ Λ y) =
      accelAsY c μ κ (α * ε) Λ y := by
  calc
    _ = c ^ 2 * |B μ κ (α * ε) Λ| * radius μ Λ y /
          Real.sqrt (lapseAtRadius μ Λ y) :=
      matched_acceleration_from_connection hc (radius_pos hC hy) (lapse_pos hC hy)
    _ = accelAsY c μ κ (α * ε) Λ y := accel_reduction hC

theorem family_acceleration_limit_from_connection
    {c μ κ α ε Λ Fr θ : ℝ}
    (hc : 0 < c) (hC : 0 < C μ Λ) (hB : B μ κ (α * ε) Λ ≠ 0) :
    Tendsto (fun y : ℝ =>
      |chartGamma 0 (lapseAtRadius μ Λ y)
        (tovNuJet (μ * radius μ Λ y ^ 3) κ α ε Λ
          (radius μ Λ y) (lapseAtRadius μ Λ y))
        Fr (radius μ Λ y) θ 1 0 0 * c ^ 2| /
        Real.sqrt (lapseAtRadius μ Λ y))
      (𝓝[<] (1 : ℝ)) atTop := by
  have hdom : ∀ᶠ y : ℝ in 𝓝[<] (1 : ℝ), RadiusDomain y := by
    filter_upwards [self_mem_nhdsWithin,
      (nhdsWithin_le_nhds (Ioi_mem_nhds (show (0 : ℝ) < 1 by norm_num)))]
      with y hy1 hy0
    exact ⟨hy0, hy1⟩
  apply (accel_limit (c := c) (μ := μ) (κ := κ) (p := α * ε) (Λ := Λ)
    hc hC hB).congr'
  filter_upwards [hdom] with y hy
  exact (family_acceleration_from_connection hc hC hy).symm

#print axioms metric00_derivative
#print axioms metric11_derivative
#print axioms metric22_derivative
#print axioms metric33_radial_derivative
#print axioms metric33_angular_derivative
#print axioms gamma001_eq
#print axioms gamma001_from_metric
#print axioms gamma100_eq
#print axioms gamma100_from_metric
#print axioms massLapse_derivative
#print axioms tov_temporal_numerator
#print axioms chartGamma001
#print axioms chartGamma100
#print axioms chartGamma_table
#print axioms matched_tovNuJet
#print axioms matched_acceleration_from_connection
#print axioms family_acceleration_from_connection
#print axioms family_acceleration_limit_from_connection

end
end CAS06Adopted
