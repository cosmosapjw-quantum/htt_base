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

/- Reusable finite connection-derivative jet.  Its entries are obtained by
   differentiating the connection table; the global theorem binding every
   entry to the actual chart derivative is still a separate obligation. -/
def chartGammaRadialJet
    (ν F νr Fr νrr Frr r θ : ℝ) (a b c : Fin 4) : ℝ :=
  if a = 0 ∧ ((b = 0 ∧ c = 1) ∨ (b = 1 ∧ c = 0)) then νrr else
  if a = 1 ∧ b = 0 ∧ c = 0 then
    Real.exp (2 * ν) * (Fr * νr + 2 * F * νr ^ 2 + F * νrr) else
  if a = 1 ∧ b = 1 ∧ c = 1 then
    -Frr / (2 * F) + Fr ^ 2 / (2 * F ^ 2) else
  if a = 1 ∧ b = 2 ∧ c = 2 then -Fr * r - F else
  if a = 1 ∧ b = 3 ∧ c = 3 then -(Fr * r + F) * Real.sin θ ^ 2 else
  if a = 2 ∧ ((b = 1 ∧ c = 2) ∨ (b = 2 ∧ c = 1)) then -1 / r ^ 2 else
  if a = 3 ∧ ((b = 1 ∧ c = 3) ∨ (b = 3 ∧ c = 1)) then -1 / r ^ 2 else 0

def chartGammaAngularJet
    (F r θ : ℝ) (a b c : Fin 4) : ℝ :=
  if a = 1 ∧ b = 3 ∧ c = 3 then
    -2 * F * r * Real.sin θ * Real.cos θ else
  if a = 2 ∧ b = 3 ∧ c = 3 then
    Real.sin θ ^ 2 - Real.cos θ ^ 2 else
  if a = 3 ∧ ((b = 2 ∧ c = 3) ∨ (b = 3 ∧ c = 2)) then
    -1 / Real.sin θ ^ 2 else 0

def chartGammaDirectionalJet
    (ν F νr Fr νrr Frr r θ : ℝ) (dir a b c : Fin 4) : ℝ :=
  if dir = 1 then chartGammaRadialJet ν F νr Fr νrr Frr r θ a b c else
  if dir = 2 then chartGammaAngularJet F r θ a b c else 0

def chartRiemannJet
    (ν F νr Fr νrr Frr r θ : ℝ) (a b c d : Fin 4) : ℝ :=
  chartGammaDirectionalJet ν F νr Fr νrr Frr r θ c a d b -
  chartGammaDirectionalJet ν F νr Fr νrr Frr r θ d a c b +
  (∑ e : Fin 4,
    chartGammaTable ν F νr Fr r θ a c e *
      chartGammaTable ν F νr Fr r θ e d b) -
  (∑ e : Fin 4,
    chartGammaTable ν F νr Fr r θ a d e *
      chartGammaTable ν F νr Fr r θ e c b)

def SameIndexPair (a b c d : Fin 4) : Prop :=
  (a = c ∧ b = d) ∨ (a = d ∧ b = c)

set_option maxHeartbeats 1000000 in
theorem chartRiemannJet_mixed_zero
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (a b c d : Fin 4) (hm : ¬SameIndexPair a b c d) :
    chartRiemannJet ν F νr Fr νrr Frr r θ a b c d = 0 := by
  fin_cases a <;> fin_cases b <;> fin_cases c <;> fin_cases d <;>
    simp_all [SameIndexPair, chartRiemannJet, chartGammaDirectionalJet,
      chartGammaRadialJet, chartGammaAngularJet, chartGammaTable,
      Fin.sum_univ_four] <;>
    field_simp [hF, hr, hs] <;>
    nlinarith [Real.sin_sq_add_cos_sq θ]


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

/- A first curvature slot, with its radial derivative tied to an actual
   second ν jet.  The full tensor derivative table remains outstanding. -/
def staticGamma (ν F νr Fr : ℝ → ℝ) (θ : ℝ)
    (a b c : Fin 4) (r : ℝ) : ℝ :=
  chartGamma (ν r) (F r) (νr r) (Fr r) r θ a b c

theorem staticGamma001_derivative
    {ν F νr Fr : ℝ → ℝ} {θ r νrr : ℝ}
    (hνrr : HasDerivAt νr νrr r) :
    HasDerivAt (staticGamma ν F νr Fr θ 0 0 1) νrr r := by
  have hfun : staticGamma ν F νr Fr θ 0 0 1 = νr := by
    funext s
    exact chartGamma001 (ν s) (F s) (νr s) (Fr s) s θ
  rw [hfun]
  exact hνrr

theorem staticGamma100_derivative
    {ν F νr Fr : ℝ → ℝ} {θ r ν0 νrr F0 Fr0 : ℝ}
    (hν : HasDerivAt ν ν0 r)
    (hF : HasDerivAt F F0 r)
    (hνr : HasDerivAt νr νrr r) :
    HasDerivAt (staticGamma ν F νr Fr θ 1 0 0)
      (Real.exp (2 * ν r) *
        (F0 * νr r + 2 * F r * ν0 * νr r + F r * νrr)) r := by
  have hfun : staticGamma ν F νr Fr θ 1 0 0 =
      fun s : ℝ => F s * Real.exp (2 * ν s) * νr s := by
    funext s
    exact chartGamma100 (ν s) (F s) (νr s) (Fr s) s θ
  rw [hfun]
  have he : HasDerivAt (fun s : ℝ => Real.exp (2 * ν s))
      (Real.exp (2 * ν r) * (2 * ν0)) r := by
    convert (Real.hasDerivAt_exp (2 * ν r)).comp r
      ((hasDerivAt_const r (2 : ℝ)).mul hν) using 1 <;>
      try {rfl} <;> ring
  convert (hF.mul he).mul hνr using 1 <;>
    try {rfl} <;> simp only [Pi.mul_apply] <;> ring

def coordinateR1010Jet (ν F νr Fr νrr r θ : ℝ) : ℝ :=
  Real.exp (2 * ν) * (Fr * νr + 2 * F * νr ^ 2 + F * νrr) +
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 1 1 e * chartGamma ν F νr Fr r θ e 0 0) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 1 0 e * chartGamma ν F νr Fr r θ e 1 0)

theorem coordinateR1010_from_connection
    {ν F νr Fr νrr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR1010Jet ν F νr Fr νrr r θ =
      Real.exp (2 * ν) * (F * (νrr + νr ^ 2) + Fr * νr / 2) := by
  unfold coordinateR1010Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable]
  field_simp
  ring

def coordinateR2020Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 2 2 e * chartGamma ν F νr Fr r θ e 0 0) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 2 0 e * chartGamma ν F νr Fr r θ e 2 0)

theorem coordinateR2020_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR2020Jet ν F νr Fr r θ =
      F * Real.exp (2 * ν) * νr / r := by
  unfold coordinateR2020Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable]
  ring

def coordinateR3030Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 3 3 e * chartGamma ν F νr Fr r θ e 0 0) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 3 0 e * chartGamma ν F νr Fr r θ e 3 0)

theorem coordinateR3030_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR3030Jet ν F νr Fr r θ =
      F * Real.exp (2 * ν) * νr / r := by
  unfold coordinateR3030Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable]
  ring

def ricci00FromConnection (ν F νr Fr νrr r θ : ℝ) : ℝ :=
  coordinateR1010Jet ν F νr Fr νrr r θ +
  coordinateR2020Jet ν F νr Fr r θ +
  coordinateR3030Jet ν F νr Fr r θ

theorem ricci00_reduction
    {ν F νr Fr νrr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    ricci00FromConnection ν F νr Fr νrr r θ =
      Real.exp (2 * ν) *
        (F * (νrr + νr ^ 2) + Fr * νr / 2 + 2 * F * νr / r) := by
  unfold ricci00FromConnection
  rw [coordinateR1010_from_connection hF hr hs,
    coordinateR2020_from_connection hF hr hs,
    coordinateR3030_from_connection hF hr hs]
  ring

theorem chartGamma212 (ν F νr Fr r θ : ℝ) (hr : r ≠ 0) :
    chartGamma ν F νr Fr r θ 2 1 2 = r⁻¹ := by
  simp [chartGamma, chartInverse, chartPartial]
  field_simp [hr]

theorem chartGamma212_all (ν F νr Fr r θ : ℝ) :
    chartGamma ν F νr Fr r θ 2 1 2 = r⁻¹ := by
  by_cases hr : r = 0
  · subst r
    simp [chartGamma, chartInverse, chartPartial]
  · exact chartGamma212 ν F νr Fr r θ hr

theorem reciprocal_radial_derivative (r : ℝ) (hr : r ≠ 0) :
    HasDerivAt (fun s : ℝ => s⁻¹) (-1 / r ^ 2) r := by
  convert (hasDerivAt_id r).inv hr using 1 <;>
    try {rfl} <;> ring

theorem staticGamma212_derivative
    {ν F νr Fr : ℝ → ℝ} {θ r : ℝ} (hr : r ≠ 0) :
    HasDerivAt (staticGamma ν F νr Fr θ 2 1 2) (-1 / r ^ 2) r := by
  have hfun : staticGamma ν F νr Fr θ 2 1 2 = fun s : ℝ => s⁻¹ := by
    funext s
    exact chartGamma212_all (ν s) (F s) (νr s) (Fr s) s θ
  rw [hfun]
  exact reciprocal_radial_derivative r hr

def coordinateR2121Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  1 / r ^ 2 +
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 2 2 e * chartGamma ν F νr Fr r θ e 1 1) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 2 1 e * chartGamma ν F νr Fr r θ e 2 1)

theorem coordinateR2121_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR2121Jet ν F νr Fr r θ = -Fr / (2 * F * r) := by
  unfold coordinateR2121Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable]
  field_simp
  ring

def coordinateR3131Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  1 / r ^ 2 +
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 3 3 e * chartGamma ν F νr Fr r θ e 1 1) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 3 1 e * chartGamma ν F νr Fr r θ e 3 1)

theorem coordinateR3131_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR3131Jet ν F νr Fr r θ = -Fr / (2 * F * r) := by
  unfold coordinateR3131Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable]
  field_simp
  ring


def coordinateR0101Jet (ν F νr Fr νrr r θ : ℝ) : ℝ :=
  -νrr +
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 0 0 e * chartGamma ν F νr Fr r θ e 1 1) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 0 1 e * chartGamma ν F νr Fr r θ e 0 1)

theorem coordinateR0101_from_connection
    {ν F νr Fr νrr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR0101Jet ν F νr Fr νrr r θ =
      -νrr - Fr * νr / (2 * F) - νr ^ 2 := by
  unfold coordinateR0101Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable, Fin.sum_univ_four]
  field_simp
  ring

def ricci11FromConnection (ν F νr Fr νrr r θ : ℝ) : ℝ :=
  coordinateR0101Jet ν F νr Fr νrr r θ +
  coordinateR2121Jet ν F νr Fr r θ +
  coordinateR3131Jet ν F νr Fr r θ

theorem ricci11_reduction
    {ν F νr Fr νrr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    ricci11FromConnection ν F νr Fr νrr r θ =
      -νrr - νr ^ 2 - Fr * νr / (2 * F) - Fr / (F * r) := by
  unfold ricci11FromConnection
  rw [coordinateR0101_from_connection hF hr hs,
    coordinateR2121_from_connection hF hr hs,
    coordinateR3131_from_connection hF hr hs]
  ring

theorem orthonormalR0101_from_connection
    {ν F νr Fr νrr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    -(Real.exp (2 * ν)) * coordinateR0101Jet ν F νr Fr νrr r θ *
      ((Real.exp (2 * ν))⁻¹ * F) =
      F * (νrr + νr ^ 2) + Fr * νr / 2 := by
  rw [coordinateR0101_from_connection hF hr hs]
  have hE : Real.exp (2 * ν) ≠ 0 := (Real.exp_pos _).ne'
  field_simp
  ring

def coordinateR0202Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 0 0 e * chartGamma ν F νr Fr r θ e 2 2) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 0 2 e * chartGamma ν F νr Fr r θ e 0 2)

theorem coordinateR0202_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR0202Jet ν F νr Fr r θ = -F * νr * r := by
  unfold coordinateR0202Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable]
  ring

theorem orthonormalR0202_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    -(Real.exp (2 * ν)) * coordinateR0202Jet ν F νr Fr r θ *
      ((Real.exp (2 * ν))⁻¹ * (r ^ 2)⁻¹) = F * νr / r := by
  rw [coordinateR0202_from_connection hF hr hs]
  have hE : Real.exp (2 * ν) ≠ 0 := (Real.exp_pos _).ne'
  field_simp <;> ring

theorem chartGamma122 (ν F νr Fr r θ : ℝ) :
    chartGamma ν F νr Fr r θ 1 2 2 = -F * r := by
  simp [chartGamma, chartInverse, chartPartial]
  ring

theorem staticGamma122_derivative
    {ν F νr Fr : ℝ → ℝ} {θ r Fr0 : ℝ}
    (hF : HasDerivAt F Fr0 r) :
    HasDerivAt (staticGamma ν F νr Fr θ 1 2 2)
      (-Fr0 * r - F r) r := by
  have hfun : staticGamma ν F νr Fr θ 1 2 2 =
      fun s : ℝ => -F s * s := by
    funext s
    exact chartGamma122 (ν s) (F s) (νr s) (Fr s) s θ
  rw [hfun]
  convert (hF.neg.mul (hasDerivAt_id r)) using 1 <;>
    try {rfl} <;> simp [id] <;> ring

def coordinateR1212Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  (-Fr * r - F) +
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 1 1 e * chartGamma ν F νr Fr r θ e 2 2) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 1 2 e * chartGamma ν F νr Fr r θ e 1 2)

theorem coordinateR1212_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR1212Jet ν F νr Fr r θ = -Fr * r / 2 := by
  unfold coordinateR1212Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable]
  field_simp
  ring

theorem orthonormalR1212_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    F⁻¹ * coordinateR1212Jet ν F νr Fr r θ * (F * (r ^ 2)⁻¹) =
      -Fr / (2 * r) := by
  rw [coordinateR1212_from_connection hF hr hs]
  field_simp <;> ring

theorem chartGamma233 (ν F νr Fr r θ : ℝ) (hr : r ≠ 0) :
    chartGamma ν F νr Fr r θ 2 3 3 =
      -Real.sin θ * Real.cos θ := by
  simp [chartGamma, chartInverse, chartPartial]
  have hr2 : r ^ 2 ≠ 0 := pow_ne_zero _ hr
  field_simp
  rw [Fin.sum_univ_four]
  simp

theorem gamma233_angular_derivative (θ : ℝ) :
    HasDerivAt (fun t : ℝ => -Real.sin t * Real.cos t)
      (Real.sin θ ^ 2 - Real.cos θ ^ 2) θ := by
  convert (Real.hasDerivAt_sin θ).neg.mul (Real.hasDerivAt_cos θ)
    using 1 <;> try {rfl} <;> simp [Pi.neg_apply] <;> ring

def coordinateR2323Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  (Real.sin θ ^ 2 - Real.cos θ ^ 2) +
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 2 2 e * chartGamma ν F νr Fr r θ e 3 3) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 2 3 e * chartGamma ν F νr Fr r θ e 2 3)

theorem coordinateR2323_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR2323Jet ν F νr Fr r θ =
      (1 - F) * Real.sin θ ^ 2 := by
  unfold coordinateR2323Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable]
  field_simp
  rw [Fin.sum_univ_four]
  simp
  ring

theorem cotangent_angular_derivative (θ : ℝ)
    (hs : Real.sin θ ≠ 0) :
    HasDerivAt (fun t : ℝ => Real.cos t / Real.sin t)
      (-1 / Real.sin θ ^ 2) θ := by
  have h := (Real.hasDerivAt_cos θ).div (Real.hasDerivAt_sin θ) hs
  have hn : -Real.sin θ * Real.sin θ - Real.cos θ * Real.cos θ = -1 := by
    nlinarith [Real.sin_sq_add_cos_sq θ]
  change HasDerivAt (fun t : ℝ => Real.cos t / Real.sin t)
    ((-Real.sin θ * Real.sin θ - Real.cos θ * Real.cos θ) /
      Real.sin θ ^ 2) θ at h
  rw [hn] at h
  exact h

theorem chartGamma323 (ν F νr Fr r θ : ℝ)
    (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    chartGamma ν F νr Fr r θ 3 2 3 = Real.cos θ / Real.sin θ := by
  simp [chartGamma, chartInverse, chartPartial]
  field_simp [hr, hs]

theorem angularGamma323_derivative (ν F νr Fr r θ : ℝ)
    (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    HasDerivAt (fun t : ℝ => chartGamma ν F νr Fr r t 3 2 3)
      (-1 / Real.sin θ ^ 2) θ := by
  have hsin : ∀ᶠ t : ℝ in 𝓝 θ, Real.sin t ≠ 0 :=
    Real.continuous_sin.continuousAt.eventually_ne hs
  apply (cotangent_angular_derivative θ hs).congr_of_eventuallyEq
  filter_upwards [hsin] with t ht
  exact chartGamma323 ν F νr Fr r t hr ht

def coordinateR3232Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  1 / Real.sin θ ^ 2 +
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 3 3 e * chartGamma ν F νr Fr r θ e 2 2) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 3 2 e * chartGamma ν F νr Fr r θ e 3 2)

theorem coordinateR3232_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR3232Jet ν F νr Fr r θ = 1 - F := by
  unfold coordinateR3232Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable]
  have htrig := Real.sin_sq_add_cos_sq θ
  field_simp [hs]
  nlinarith

def ricci22FromConnection (ν F νr Fr r θ : ℝ) : ℝ :=
  coordinateR0202Jet ν F νr Fr r θ +
  coordinateR1212Jet ν F νr Fr r θ +
  coordinateR3232Jet ν F νr Fr r θ

theorem ricci22_reduction
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    ricci22FromConnection ν F νr Fr r θ =
      1 - F - F * νr * r - Fr * r / 2 := by
  unfold ricci22FromConnection
  rw [coordinateR0202_from_connection hF hr hs,
    coordinateR1212_from_connection hF hr hs,
    coordinateR3232_from_connection hF hr hs]
  ring

def coordinateR0303Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 0 0 e * chartGamma ν F νr Fr r θ e 3 3) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 0 3 e * chartGamma ν F νr Fr r θ e 0 3)

theorem coordinateR0303_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR0303Jet ν F νr Fr r θ =
      -F * νr * r * Real.sin θ ^ 2 := by
  unfold coordinateR0303Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable, Fin.sum_univ_four]
  ring

theorem chartGamma133 (ν F νr Fr r θ : ℝ) :
    chartGamma ν F νr Fr r θ 1 3 3 = -F * r * Real.sin θ ^ 2 := by
  simp [chartGamma, chartInverse, chartPartial, Fin.sum_univ_four]
  ring

theorem staticGamma133_derivative
    {ν F νr Fr : ℝ → ℝ} {θ r Fr0 : ℝ}
    (hF : HasDerivAt F Fr0 r) :
    HasDerivAt (staticGamma ν F νr Fr θ 1 3 3)
      (-(Fr0 * r + F r) * Real.sin θ ^ 2) r := by
  have hfun : staticGamma ν F νr Fr θ 1 3 3 =
      fun s : ℝ => (-F s * s) * Real.sin θ ^ 2 := by
    funext s
    exact chartGamma133 (ν s) (F s) (νr s) (Fr s) s θ
  rw [hfun]
  convert ((hF.neg.mul (hasDerivAt_id r)).mul_const
    (Real.sin θ ^ 2)) using 1 <;> try {rfl} <;>
    simp only [Pi.neg_apply, Pi.mul_apply, id_eq] <;> ring

def coordinateR1313Jet (ν F νr Fr r θ : ℝ) : ℝ :=
  -(Fr * r + F) * Real.sin θ ^ 2 +
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 1 1 e * chartGamma ν F νr Fr r θ e 3 3) -
  (∑ e : Fin 4,
    chartGamma ν F νr Fr r θ 1 3 e * chartGamma ν F νr Fr r θ e 1 3)

theorem coordinateR1313_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    coordinateR1313Jet ν F νr Fr r θ =
      -Fr * r * Real.sin θ ^ 2 / 2 := by
  unfold coordinateR1313Jet
  simp_rw [chartGamma_table ν F νr Fr r θ hF hr hs]
  simp [chartGammaTable, Fin.sum_univ_four]
  field_simp
  ring

def ricci33FromConnection (ν F νr Fr r θ : ℝ) : ℝ :=
  coordinateR0303Jet ν F νr Fr r θ +
  coordinateR1313Jet ν F νr Fr r θ +
  coordinateR2323Jet ν F νr Fr r θ

theorem ricci33_reduction
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    ricci33FromConnection ν F νr Fr r θ =
      (1 - F - F * νr * r - Fr * r / 2) * Real.sin θ ^ 2 := by
  unfold ricci33FromConnection
  rw [coordinateR0303_from_connection hF hr hs,
    coordinateR1313_from_connection hF hr hs,
    coordinateR2323_from_connection hF hr hs]
  ring

/- Direct diagonal contraction with the inverse metric.  Mixed Ricci slots do
   not contribute to this contraction because chartInverse is diagonal. -/
def scalarFromRicciDiagonal (ν F νr Fr νrr r θ : ℝ) : ℝ :=
  -(Real.exp (2 * ν))⁻¹ * ricci00FromConnection ν F νr Fr νrr r θ +
  F * ricci11FromConnection ν F νr Fr νrr r θ +
  (r ^ 2)⁻¹ * ricci22FromConnection ν F νr Fr r θ +
  (r ^ 2 * Real.sin θ ^ 2)⁻¹ * ricci33FromConnection ν F νr Fr r θ

def einsteinHat00FromRicciDiagonal (ν F νr Fr νrr r θ : ℝ) : ℝ :=
  (Real.exp (2 * ν))⁻¹ * ricci00FromConnection ν F νr Fr νrr r θ +
  scalarFromRicciDiagonal ν F νr Fr νrr r θ / 2

theorem einsteinHat00_from_connection
    {ν F νr Fr νrr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    einsteinHat00FromRicciDiagonal ν F νr Fr νrr r θ =
      (1 - F) / r ^ 2 - Fr / r := by
  unfold einsteinHat00FromRicciDiagonal scalarFromRicciDiagonal
  rw [ricci00_reduction hF hr hs,
    ricci11_reduction hF hr hs,
    ricci22_reduction hF hr hs,
    ricci33_reduction hF hr hs]
  have hE : Real.exp (2 * ν) ≠ 0 := (Real.exp_pos _).ne'
  field_simp [hr, hs, hE, hF]
  ring

theorem einsteinHat00_tov_from_connection
    {ν F νr Fr νrr m mr Λ κ ε r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (hFvalue : F = 1 - 2 * m / r - Λ * r ^ 2 / 3)
    (hFr : Fr = massLapseJet m mr Λ r)
    (hTOV : mr = κ * r ^ 2 * ε / 2) :
    einsteinHat00FromRicciDiagonal ν F νr Fr νrr r θ - Λ = κ * ε := by
  rw [einsteinHat00_from_connection hF hr hs, hFvalue, hFr]
  have hnum := tov_temporal_numerator (m := m) (mr := mr)
    (Λ := Λ) (κ := κ) (ε := ε) (r := r) hr hTOV
  field_simp [hr] at hnum ⊢
  nlinarith

def einsteinHat11FromRicciDiagonal (ν F νr Fr νrr r θ : ℝ) : ℝ :=
  F * ricci11FromConnection ν F νr Fr νrr r θ -
  scalarFromRicciDiagonal ν F νr Fr νrr r θ / 2

theorem einsteinHat11_from_connection
    {ν F νr Fr νrr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    einsteinHat11FromRicciDiagonal ν F νr Fr νrr r θ =
      2 * F * νr / r - (1 - F) / r ^ 2 := by
  unfold einsteinHat11FromRicciDiagonal scalarFromRicciDiagonal
  rw [ricci00_reduction hF hr hs,
    ricci11_reduction hF hr hs,
    ricci22_reduction hF hr hs,
    ricci33_reduction hF hr hs]
  have hE : Real.exp (2 * ν) ≠ 0 := (Real.exp_pos _).ne'
  field_simp [hr, hs, hE, hF]
  ring

theorem einsteinHat11_tov_from_connection
    {ν F Fr νrr m Λ κ p r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (hFvalue : F = 1 - 2 * m / r - Λ * r ^ 2 / 3) :
    einsteinHat11FromRicciDiagonal ν F
      ((m + κ * p * r ^ 3 / 2 - Λ * r ^ 3 / 3) / (r ^ 2 * F))
      Fr νrr r θ + Λ = κ * p := by
  rw [einsteinHat11_from_connection hF hr hs]
  field_simp [hr, hF]
  rw [hFvalue]
  field_simp [hr]
  ring

theorem orthonormalR2323_from_connection
    {ν F νr Fr r θ : ℝ}
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    r ^ 2 * coordinateR2323Jet ν F νr Fr r θ *
      ((r ^ 2)⁻¹ * (r ^ 2 * Real.sin θ ^ 2)⁻¹) =
      (1 - F) / r ^ 2 := by
  rw [coordinateR2323_from_connection hF hr hs]
  field_simp <;> ring

/- Physical static velocity U=c e₀.  The only nonzero coordinate derivative
   is radial; static transport along U therefore leaves the partial term zero. -/
def staticVelocity (c ν : ℝ) (a : Fin 4) : ℝ :=
  if a = 0 then c * Real.exp (-ν) else 0

def staticVelocityPartial (c ν νr : ℝ) (dir a : Fin 4) : ℝ :=
  if dir = 1 ∧ a = 0 then -c * Real.exp (-ν) * νr else 0

theorem staticVelocity0_radial_derivative
    {c : ℝ} {ν : ℝ → ℝ} {r νr : ℝ}
    (hν : HasDerivAt ν νr r) :
    HasDerivAt (fun s : ℝ => staticVelocity c (ν s) 0)
      (staticVelocityPartial c (ν r) νr 1 0) r := by
  convert ((Real.hasDerivAt_exp (-ν r)).comp r hν.neg).const_mul c using 1 <;>
    try {rfl} <;> simp [staticVelocityPartial] <;> ring

theorem staticVelocity_time_derivative (c ν : ℝ) (a : Fin 4) (x0 : ℝ) :
    HasDerivAt (fun _t : ℝ => staticVelocity c ν a) 0 x0 := by
  exact hasDerivAt_const x0 _

theorem staticVelocity_angular_derivative (c ν : ℝ) (a : Fin 4) (θ : ℝ) :
    HasDerivAt (fun _t : ℝ => staticVelocity c ν a) 0 θ := by
  exact hasDerivAt_const θ _

def staticAccelVector (c ν F νr Fr r θ : ℝ) (b : Fin 4) : ℝ :=
  (∑ a : Fin 4, staticVelocity c ν a * staticVelocityPartial c ν νr a b) +
  (∑ a : Fin 4, ∑ d : Fin 4,
    staticVelocity c ν a * chartGamma ν F νr Fr r θ b a d *
      staticVelocity c ν d)

theorem staticAccel_at_normalized_event (c F νr Fr r θ : ℝ) (b : Fin 4) :
    staticAccelVector c 0 F νr Fr r θ b =
      chartGamma 0 F νr Fr r θ b 0 0 * c ^ 2 := by
  simp [staticAccelVector, staticVelocity, staticVelocityPartial,
    Fin.sum_univ_four]
  ring

theorem staticAccel_components (c F νr Fr r θ : ℝ) :
    ∀ b : Fin 4,
      staticAccelVector c 0 F νr Fr r θ b =
        if b = 1 then F * νr * c ^ 2 else 0 := by
  intro b
  rw [staticAccel_at_normalized_event]
  fin_cases b <;> simp [chartGamma, chartInverse, chartPartial] <;>
    ring <;> simp

def metricAccelNorm (F r θ : ℝ) (A : Fin 4 → ℝ) : ℝ :=
  Real.sqrt (∑ b : Fin 4, chartMetric 0 F r θ b b * (A b) ^ 2)

theorem staticAccel_metric_norm
    {c F νr Fr r θ : ℝ} (hF : 0 < F) :
    metricAccelNorm F r θ (staticAccelVector c 0 F νr Fr r θ) =
      |F * νr * c ^ 2| / Real.sqrt F := by
  have hA := staticAccel_components c F νr Fr r θ
  unfold metricAccelNorm
  simp [Fin.sum_univ_four, hA, chartMetric]
  rw [show F⁻¹ * (F * νr * c ^ 2) ^ 2 =
    (F * νr * c ^ 2) ^ 2 / F by ring]
  rw [Real.sqrt_div (sq_nonneg _), Real.sqrt_sq_eq_abs]
  simp [abs_mul, abs_of_pos hF]

theorem matched_static_accel_metric_norm
    {c μ κ α ε Λ r F Fr θ : ℝ}
    (hc : 0 < c) (hr : 0 < r) (hF : 0 < F) :
    metricAccelNorm F r θ
      (staticAccelVector c 0 F
        (tovNuJet (μ * r ^ 3) κ α ε Λ r F) Fr r θ) =
      c ^ 2 * |B μ κ (α * ε) Λ| * r / Real.sqrt F := by
  rw [staticAccel_metric_norm hF]
  have h := matched_acceleration_from_connection
    (c := c) (μ := μ) (κ := κ) (α := α) (ε := ε)
    (Λ := Λ) (r := r) (F := F) (Fr := Fr) (θ := θ) hc hr hF
  simpa [chartGamma100] using h

theorem fixed_family_static_accel_metric_limit
    {c μ κ α ε Λ Fr θ : ℝ}
    (hc : 0 < c) (hC : 0 < C μ Λ)
    (hB : B μ κ (α * ε) Λ ≠ 0) :
    Tendsto (fun y : ℝ =>
      metricAccelNorm (lapseAtRadius μ Λ y) (radius μ Λ y) θ
        (staticAccelVector c 0 (lapseAtRadius μ Λ y)
          (tovNuJet (μ * radius μ Λ y ^ 3) κ α ε Λ
            (radius μ Λ y) (lapseAtRadius μ Λ y))
          Fr (radius μ Λ y) θ))
      (𝓝[<] (1 : ℝ)) atTop := by
  have hdom : ∀ᶠ y : ℝ in 𝓝[<] (1 : ℝ), RadiusDomain y := by
    filter_upwards [self_mem_nhdsWithin,
      (nhdsWithin_le_nhds (Ioi_mem_nhds (show (0 : ℝ) < 1 by norm_num)))]
      with y hy1 hy0
    exact ⟨hy0, hy1⟩
  apply (accel_limit (c := c) (μ := μ) (κ := κ) (p := α * ε) (Λ := Λ)
    hc hC hB).congr'
  filter_upwards [hdom] with y hy
  symm
  calc
    metricAccelNorm (lapseAtRadius μ Λ y) (radius μ Λ y) θ
        (staticAccelVector c 0 (lapseAtRadius μ Λ y)
          (tovNuJet (μ * radius μ Λ y ^ 3) κ α ε Λ
            (radius μ Λ y) (lapseAtRadius μ Λ y))
          Fr (radius μ Λ y) θ) =
      c ^ 2 * |B μ κ (α * ε) Λ| * radius μ Λ y /
        Real.sqrt (lapseAtRadius μ Λ y) :=
      matched_static_accel_metric_norm hc (radius_pos hC hy) (lapse_pos hC hy)
    _ = accelAsY c μ κ (α * ε) Λ y := accel_reduction hC

theorem gamma111_table_radial_derivative
    {F Fr : ℝ → ℝ} {r Frr : ℝ}
    (hF : HasDerivAt F (Fr r) r)
    (hFr : HasDerivAt Fr Frr r) (hF0 : F r ≠ 0) :
    HasDerivAt (fun s : ℝ => -Fr s / (2 * F s))
      (-Frr / (2 * F r) + Fr r ^ 2 / (2 * F r ^ 2)) r := by
  have hden : (2 : ℝ) * F r ≠ 0 := mul_ne_zero (by norm_num) hF0
  convert hFr.neg.div (hF.const_mul 2) hden using 1 <;>
    try {rfl} <;> simp only [Pi.neg_apply, Pi.mul_apply] <;>
    field_simp [hF0] <;> ring

set_option maxHeartbeats 1000000 in
theorem chartGammaTable_radial_derivative
    {ν F νr Fr : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hν : HasDerivAt ν (νr r) r)
    (hF : HasDerivAt F (Fr r) r)
    (hνr : HasDerivAt νr νrr r)
    (hFr : HasDerivAt Fr Frr r)
    (hF0 : F r ≠ 0) (hr : r ≠ 0) :
    ∀ a b c : Fin 4,
      HasDerivAt (fun s : ℝ =>
        chartGammaTable (ν s) (F s) (νr s) (Fr s) s θ a b c)
        (chartGammaRadialJet (ν r) (F r) (νr r) (Fr r) νrr Frr r θ a b c) r := by
  have h100 : HasDerivAt (fun s : ℝ =>
      F s * Real.exp (2 * ν s) * νr s)
      (Real.exp (2 * ν r) *
        (Fr r * νr r + 2 * F r * νr r ^ 2 + F r * νrr)) r := by
    have h := staticGamma100_derivative (Fr := Fr) (Fr0 := Frr)
      (θ := θ) hν hF hνr
    have hf : staticGamma ν F νr Fr θ 1 0 0 =
        fun s : ℝ => F s * Real.exp (2 * ν s) * νr s := by
      funext s
      exact chartGamma100 (ν s) (F s) (νr s) (Fr s) s θ
    rw [hf] at h
    convert h using 1 <;> try {rfl} <;>
      try {funext s; ring} <;> ring
  have h122 : HasDerivAt (fun s : ℝ => -(F s * s))
      (-(Fr r * r) - F r) r := by
    have h := staticGamma122_derivative (ν := ν) (νr := νr)
      (Fr := Fr) (θ := θ) hF
    have hf : staticGamma ν F νr Fr θ 1 2 2 =
        fun s : ℝ => -F s * s := by
      funext s
      exact chartGamma122 (ν s) (F s) (νr s) (Fr s) s θ
    rw [hf] at h
    simpa only [neg_mul] using h
  have h133 : HasDerivAt (fun s : ℝ =>
      -(F s * s * Real.sin θ ^ 2))
      ((-F r + -(Fr r * r)) * Real.sin θ ^ 2) r := by
    have h := staticGamma133_derivative (ν := ν) (νr := νr)
      (Fr := Fr) (θ := θ) hF
    have hf : staticGamma ν F νr Fr θ 1 3 3 =
        fun s : ℝ => -F s * s * Real.sin θ ^ 2 := by
      funext s
      exact chartGamma133 (ν s) (F s) (νr s) (Fr s) s θ
    rw [hf] at h
    convert h using 1 <;> try {rfl} <;>
      try {funext s; ring} <;> ring
  intro a b c
  fin_cases a <;> fin_cases b <;> fin_cases c <;>
    simp [chartGammaTable, chartGammaRadialJet] <;>
    first
    | exact hasDerivAt_const r 0
    | exact hνr
    | exact h100
    | exact gamma111_table_radial_derivative hF hFr hF0
    | exact h122
    | exact h133
    | exact reciprocal_radial_derivative r hr
    | exact hasDerivAt_const r _

theorem gamma133_table_angular_derivative (F r θ : ℝ) :
    HasDerivAt (fun t : ℝ => -F * r * Real.sin t ^ 2)
      (-2 * F * r * Real.sin θ * Real.cos θ) θ := by
  convert ((Real.hasDerivAt_sin θ).mul (Real.hasDerivAt_sin θ)).const_mul
    (-F * r) using 1
  all_goals first
    | rfl
    | (funext t; simp only [Pi.mul_apply]; ring)
    | ring

set_option maxHeartbeats 1000000 in
theorem chartGammaTable_angular_derivative
    (ν F νr Fr r θ : ℝ) (hs : Real.sin θ ≠ 0) :
    ∀ a b c : Fin 4,
      HasDerivAt (fun t : ℝ => chartGammaTable ν F νr Fr r t a b c)
        (chartGammaAngularJet F r θ a b c) θ := by
  have h133 : HasDerivAt (fun t : ℝ => -(F * r * Real.sin t ^ 2))
      (-(2 * F * r * Real.sin θ * Real.cos θ)) θ := by
    have h := gamma133_table_angular_derivative F r θ
    convert h using 1 <;> try {rfl} <;>
      try {funext t; ring} <;> ring
  have h233 : HasDerivAt (fun t : ℝ =>
      -(Real.sin t * Real.cos t))
      (Real.sin θ ^ 2 - Real.cos θ ^ 2) θ := by
    have h := gamma233_angular_derivative θ
    convert h using 1 <;> try {rfl} <;>
      try {funext t; ring} <;> ring
  intro a b c
  fin_cases a <;> fin_cases b <;> fin_cases c <;>
    simp [chartGammaTable, chartGammaAngularJet] <;>
    first
    | exact hasDerivAt_const θ _
    | exact h133
    | exact h233
    | exact cotangent_angular_derivative θ hs

theorem chartGamma_radial_derivative_all
    {ν F νr Fr : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hν : HasDerivAt ν (νr r) r)
    (hF : HasDerivAt F (Fr r) r)
    (hνr : HasDerivAt νr νrr r)
    (hFr : HasDerivAt Fr Frr r)
    (hF0 : F r ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    ∀ a b c : Fin 4,
      HasDerivAt (staticGamma ν F νr Fr θ a b c)
        (chartGammaRadialJet (ν r) (F r) (νr r) (Fr r) νrr Frr r θ a b c) r := by
  intro a b c
  have hFnear : ∀ᶠ s : ℝ in 𝓝 r, F s ≠ 0 :=
    hF.continuousAt.eventually_ne hF0
  have hrnear : ∀ᶠ s : ℝ in 𝓝 r, s ≠ 0 :=
    continuousAt_id.eventually_ne hr
  have hEq : staticGamma ν F νr Fr θ a b c =ᶠ[𝓝 r]
      (fun s : ℝ => chartGammaTable (ν s) (F s) (νr s) (Fr s) s θ a b c) := by
    filter_upwards [hFnear, hrnear] with s hFs hrs
    exact chartGamma_table (ν s) (F s) (νr s) (Fr s) s θ hFs hrs hs a b c
  exact (chartGammaTable_radial_derivative hν hF hνr hFr hF0 hr a b c)
    |>.congr_of_eventuallyEq hEq

theorem chartGamma_angular_derivative_all
    (ν F νr Fr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    ∀ a b c : Fin 4,
      HasDerivAt (fun t : ℝ => chartGamma ν F νr Fr r t a b c)
        (chartGammaAngularJet F r θ a b c) θ := by
  intro a b c
  have hsnear : ∀ᶠ t : ℝ in 𝓝 θ, Real.sin t ≠ 0 :=
    Real.continuous_sin.continuousAt.eventually_ne hs
  have hEq : (fun t : ℝ => chartGamma ν F νr Fr r t a b c) =ᶠ[𝓝 θ]
      (fun t : ℝ => chartGammaTable ν F νr Fr r t a b c) := by
    filter_upwards [hsnear] with t hst
    exact chartGamma_table ν F νr Fr r t hF hr hst a b c
  exact (chartGammaTable_angular_derivative ν F νr Fr r θ hs a b c)
    |>.congr_of_eventuallyEq hEq

def chartBaseCoordinate (dir : Fin 4) (r θ : ℝ) : ℝ :=
  if dir = 1 then r else if dir = 2 then θ else 0

def chartGammaCoordinateLine
    (ν F νr Fr : ℝ → ℝ) (r θ : ℝ)
    (dir a b c : Fin 4) (s : ℝ) : ℝ :=
  if dir = 1 then staticGamma ν F νr Fr θ a b c s else
  if dir = 2 then chartGamma (ν r) (F r) (νr r) (Fr r) r s a b c else
  chartGamma (ν r) (F r) (νr r) (Fr r) r θ a b c

theorem chartGammaCoordinateLine_derivative
    {ν F νr Fr : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hν : HasDerivAt ν (νr r) r)
    (hF : HasDerivAt F (Fr r) r)
    (hνr : HasDerivAt νr νrr r)
    (hFr : HasDerivAt Fr Frr r)
    (hF0 : F r ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    ∀ dir a b c : Fin 4,
      HasDerivAt (chartGammaCoordinateLine ν F νr Fr r θ dir a b c)
        (chartGammaDirectionalJet (ν r) (F r) (νr r) (Fr r)
          νrr Frr r θ dir a b c)
        (chartBaseCoordinate dir r θ) := by
  intro dir a b c
  fin_cases dir
  · change HasDerivAt (fun _s : ℝ =>
        chartGamma (ν r) (F r) (νr r) (Fr r) r θ a b c) 0 0
    exact hasDerivAt_const (0 : ℝ) _
  · change HasDerivAt (staticGamma ν F νr Fr θ a b c)
        (chartGammaRadialJet (ν r) (F r) (νr r) (Fr r)
          νrr Frr r θ a b c) r
    exact chartGamma_radial_derivative_all hν hF hνr hFr hF0 hr hs a b c
  · change HasDerivAt (fun t : ℝ =>
        chartGamma (ν r) (F r) (νr r) (Fr r) r t a b c)
        (chartGammaAngularJet (F r) r θ a b c) θ
    exact chartGamma_angular_derivative_all (ν r) (F r) (νr r) (Fr r)
      r θ hF0 hr hs a b c
  · change HasDerivAt (fun _s : ℝ =>
        chartGamma (ν r) (F r) (νr r) (Fr r) r θ a b c) 0 0
    exact hasDerivAt_const (0 : ℝ) _

def chartRiemannFromMetric
    (ν F νr Fr : ℝ → ℝ) (r θ : ℝ)
    (a b c d : Fin 4) : ℝ :=
  deriv (chartGammaCoordinateLine ν F νr Fr r θ c a d b)
      (chartBaseCoordinate c r θ) -
  deriv (chartGammaCoordinateLine ν F νr Fr r θ d a c b)
      (chartBaseCoordinate d r θ) +
  (∑ e : Fin 4,
    chartGamma (ν r) (F r) (νr r) (Fr r) r θ a c e *
      chartGamma (ν r) (F r) (νr r) (Fr r) r θ e d b) -
  (∑ e : Fin 4,
    chartGamma (ν r) (F r) (νr r) (Fr r) r θ a d e *
      chartGamma (ν r) (F r) (νr r) (Fr r) r θ e c b)

theorem chartRiemannFromMetric_eq_jet
    {ν F νr Fr : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hν : HasDerivAt ν (νr r) r)
    (hF : HasDerivAt F (Fr r) r)
    (hνr : HasDerivAt νr νrr r)
    (hFr : HasDerivAt Fr Frr r)
    (hF0 : F r ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (a b c d : Fin 4) :
    chartRiemannFromMetric ν F νr Fr r θ a b c d =
      chartRiemannJet (ν r) (F r) (νr r) (Fr r) νrr Frr r θ a b c d := by
  unfold chartRiemannFromMetric chartRiemannJet
  rw [(chartGammaCoordinateLine_derivative hν hF hνr hFr hF0 hr hs
        c a d b).deriv,
      (chartGammaCoordinateLine_derivative hν hF hνr hFr hF0 hr hs
        d a c b).deriv]
  simp_rw [chartGamma_table (ν r) (F r) (νr r) (Fr r) r θ hF0 hr hs]

theorem chartRiemannFromMetric_mixed_zero
    {ν F νr Fr : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hν : HasDerivAt ν (νr r) r)
    (hF : HasDerivAt F (Fr r) r)
    (hνr : HasDerivAt νr νrr r)
    (hFr : HasDerivAt Fr Frr r)
    (hF0 : F r ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (a b c d : Fin 4) (hm : ¬SameIndexPair a b c d) :
    chartRiemannFromMetric ν F νr Fr r θ a b c d = 0 := by
  rw [chartRiemannFromMetric_eq_jet hν hF hνr hFr hF0 hr hs a b c d]
  exact chartRiemannJet_mixed_zero (ν r) (F r) (νr r) (Fr r)
    νrr Frr r θ hF0 hr hs a b c d hm

def chartRicciFromMetric
    (ν F νr Fr : ℝ → ℝ) (r θ : ℝ)
    (b d : Fin 4) : ℝ :=
  ∑ a : Fin 4, chartRiemannFromMetric ν F νr Fr r θ a b a d

def chartRicciJet
    (ν F νr Fr νrr Frr r θ : ℝ) (b d : Fin 4) : ℝ :=
  ∑ a : Fin 4, chartRiemannJet ν F νr Fr νrr Frr r θ a b a d

theorem chartRicciFromMetric_eq_jet
    {ν F νr Fr : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hν : HasDerivAt ν (νr r) r)
    (hF : HasDerivAt F (Fr r) r)
    (hνr : HasDerivAt νr νrr r)
    (hFr : HasDerivAt Fr Frr r)
    (hF0 : F r ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (b d : Fin 4) :
    chartRicciFromMetric ν F νr Fr r θ b d =
      chartRicciJet (ν r) (F r) (νr r) (Fr r) νrr Frr r θ b d := by
  unfold chartRicciFromMetric chartRicciJet
  apply Finset.sum_congr rfl
  intro a _
  exact chartRiemannFromMetric_eq_jet hν hF hνr hFr hF0 hr hs a b a d

theorem chartRicciFromMetric_offdiag_zero
    {ν F νr Fr : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hν : HasDerivAt ν (νr r) r)
    (hF : HasDerivAt F (Fr r) r)
    (hνr : HasDerivAt νr νrr r)
    (hFr : HasDerivAt Fr Frr r)
    (hF0 : F r ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (b d : Fin 4) (hbd : b ≠ d) :
    chartRicciFromMetric ν F νr Fr r θ b d = 0 := by
  unfold chartRicciFromMetric
  apply Finset.sum_eq_zero
  intro a _
  apply chartRiemannFromMetric_mixed_zero hν hF hνr hFr hF0 hr hs
  intro hp
  rcases hp with ⟨_, h⟩ | ⟨h₁, h₂⟩
  · exact hbd h
  · exact hbd (h₂.trans h₁)

set_option maxHeartbeats 1000000 in
theorem chartRicciJet_00
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    chartRicciJet ν F νr Fr νrr Frr r θ 0 0 =
      Real.exp (2 * ν) *
        (F * (νrr + νr ^ 2) + Fr * νr / 2 + 2 * F * νr / r) := by
  simp [chartRicciJet, chartRiemannJet, chartGammaDirectionalJet,
    chartGammaRadialJet, chartGammaAngularJet, chartGammaTable,
    Fin.sum_univ_four]
  field_simp [hF, hr, hs]
  ring

set_option maxHeartbeats 1000000 in
theorem chartRicciJet_11
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    chartRicciJet ν F νr Fr νrr Frr r θ 1 1 =
      -νrr - νr ^ 2 - Fr * νr / (2 * F) - Fr / (F * r) := by
  simp [chartRicciJet, chartRiemannJet, chartGammaDirectionalJet,
    chartGammaRadialJet, chartGammaAngularJet, chartGammaTable,
    Fin.sum_univ_four]
  field_simp [hF, hr, hs]
  ring

set_option maxHeartbeats 1000000 in
theorem chartRicciJet_22
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    chartRicciJet ν F νr Fr νrr Frr r θ 2 2 =
      1 - F - F * νr * r - Fr * r / 2 := by
  simp [chartRicciJet, chartRiemannJet, chartGammaDirectionalJet,
    chartGammaRadialJet, chartGammaAngularJet, chartGammaTable,
    Fin.sum_univ_four]
  field_simp [hF, hr, hs]
  nlinarith [Real.sin_sq_add_cos_sq θ]

set_option maxHeartbeats 1000000 in
theorem chartRicciJet_33
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    chartRicciJet ν F νr Fr νrr Frr r θ 3 3 =
      (1 - F - F * νr * r - Fr * r / 2) * Real.sin θ ^ 2 := by
  simp [chartRicciJet, chartRiemannJet, chartGammaDirectionalJet,
    chartGammaRadialJet, chartGammaAngularJet, chartGammaTable,
    Fin.sum_univ_four]
  field_simp [hF, hr, hs]
  nlinarith [Real.sin_sq_add_cos_sq θ]

def chartScalarJet (ν F νr Fr νrr Frr r θ : ℝ) : ℝ :=
  ∑ a : Fin 4,
    chartInverse ν F r θ a a * chartRicciJet ν F νr Fr νrr Frr r θ a a

def chartEinsteinJet (ν F νr Fr νrr Frr r θ : ℝ)
    (b d : Fin 4) : ℝ :=
  chartRicciJet ν F νr Fr νrr Frr r θ b d -
    chartMetric ν F r θ b d * chartScalarJet ν F νr Fr νrr Frr r θ / 2

theorem chartScalarJet_reduction
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    chartScalarJet ν F νr Fr νrr Frr r θ =
      -2 * F * (νrr + νr ^ 2) - Fr * νr -
      4 * F * νr / r - 2 * Fr / r + 2 * (1 - F) / r ^ 2 := by
  simp [chartScalarJet, Fin.sum_univ_four, chartInverse,
    chartRicciJet_00 ν F νr Fr νrr Frr r θ hF hr hs,
    chartRicciJet_11 ν F νr Fr νrr Frr r θ hF hr hs,
    chartRicciJet_22 ν F νr Fr νrr Frr r θ hF hr hs,
    chartRicciJet_33 ν F νr Fr νrr Frr r θ hF hr hs]
  have hE : Real.exp (2 * ν) ≠ 0 := (Real.exp_pos _).ne'
  field_simp [hF, hr, hs, hE]
  ring

theorem chartEinsteinJet_offdiag_zero
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (b d : Fin 4) (hbd : b ≠ d) :
    chartEinsteinJet ν F νr Fr νrr Frr r θ b d = 0 := by
  have hR : chartRicciJet ν F νr Fr νrr Frr r θ b d = 0 := by
    unfold chartRicciJet
    apply Finset.sum_eq_zero
    intro a _
    apply chartRiemannJet_mixed_zero ν F νr Fr νrr Frr r θ hF hr hs
    intro hp
    rcases hp with ⟨_, h⟩ | ⟨h₁, h₂⟩
    · exact hbd h
    · exact hbd (h₂.trans h₁)
  simp [chartEinsteinJet, hR, chartMetric, hbd]

theorem chartEinsteinJet_hat00
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    (Real.exp (2 * ν))⁻¹ *
      chartEinsteinJet ν F νr Fr νrr Frr r θ 0 0 =
      (1 - F) / r ^ 2 - Fr / r := by
  rw [chartEinsteinJet, chartRicciJet_00 ν F νr Fr νrr Frr r θ hF hr hs,
    chartScalarJet_reduction ν F νr Fr νrr Frr r θ hF hr hs]
  simp [chartMetric]
  have hE : Real.exp (2 * ν) ≠ 0 := (Real.exp_pos _).ne'
  field_simp [hF, hr, hs, hE]
  ring

theorem chartEinsteinJet_hat11
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    F * chartEinsteinJet ν F νr Fr νrr Frr r θ 1 1 =
      2 * F * νr / r - (1 - F) / r ^ 2 := by
  rw [chartEinsteinJet, chartRicciJet_11 ν F νr Fr νrr Frr r θ hF hr hs,
    chartScalarJet_reduction ν F νr Fr νrr Frr r θ hF hr hs]
  simp [chartMetric]
  field_simp [hF, hr, hs]
  ring

theorem chartEinsteinJet_hat22
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    (r ^ 2)⁻¹ * chartEinsteinJet ν F νr Fr νrr Frr r θ 2 2 =
      F * (νrr + νr ^ 2 + νr / r) + Fr * (νr / 2 + 1 / (2 * r)) := by
  rw [chartEinsteinJet, chartRicciJet_22 ν F νr Fr νrr Frr r θ hF hr hs,
    chartScalarJet_reduction ν F νr Fr νrr Frr r θ hF hr hs]
  simp [chartMetric]
  field_simp [hF, hr, hs]
  ring

theorem chartEinsteinJet_hat33
    (ν F νr Fr νrr Frr r θ : ℝ)
    (hF : F ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    (r ^ 2 * Real.sin θ ^ 2)⁻¹ *
      chartEinsteinJet ν F νr Fr νrr Frr r θ 3 3 =
      F * (νrr + νr ^ 2 + νr / r) + Fr * (νr / 2 + 1 / (2 * r)) := by
  rw [chartEinsteinJet, chartRicciJet_33 ν F νr Fr νrr Frr r θ hF hr hs,
    chartScalarJet_reduction ν F νr Fr νrr Frr r θ hF hr hs]
  simp [chartMetric]
  field_simp [hF, hr, hs]
  ring

def chartScalarFromMetric
    (ν F νr Fr : ℝ → ℝ) (r θ : ℝ) : ℝ :=
  ∑ a : Fin 4,
    chartInverse (ν r) (F r) r θ a a *
      chartRicciFromMetric ν F νr Fr r θ a a

def chartEinsteinFromMetric
    (ν F νr Fr : ℝ → ℝ) (r θ : ℝ)
    (b d : Fin 4) : ℝ :=
  chartRicciFromMetric ν F νr Fr r θ b d -
    chartMetric (ν r) (F r) r θ b d *
      chartScalarFromMetric ν F νr Fr r θ / 2

theorem chartScalarFromMetric_eq_jet
    {ν F νr Fr : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hν : HasDerivAt ν (νr r) r)
    (hF : HasDerivAt F (Fr r) r)
    (hνr : HasDerivAt νr νrr r)
    (hFr : HasDerivAt Fr Frr r)
    (hF0 : F r ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0) :
    chartScalarFromMetric ν F νr Fr r θ =
      chartScalarJet (ν r) (F r) (νr r) (Fr r) νrr Frr r θ := by
  unfold chartScalarFromMetric chartScalarJet
  apply Finset.sum_congr rfl
  intro a _
  rw [chartRicciFromMetric_eq_jet hν hF hνr hFr hF0 hr hs a a]

theorem chartEinsteinFromMetric_eq_jet
    {ν F νr Fr : ℝ → ℝ} {r θ νrr Frr : ℝ}
    (hν : HasDerivAt ν (νr r) r)
    (hF : HasDerivAt F (Fr r) r)
    (hνr : HasDerivAt νr νrr r)
    (hFr : HasDerivAt Fr Frr r)
    (hF0 : F r ≠ 0) (hr : r ≠ 0) (hs : Real.sin θ ≠ 0)
    (b d : Fin 4) :
    chartEinsteinFromMetric ν F νr Fr r θ b d =
      chartEinsteinJet (ν r) (F r) (νr r) (Fr r) νrr Frr r θ b d := by
  unfold chartEinsteinFromMetric chartEinsteinJet
  rw [chartRicciFromMetric_eq_jet hν hF hνr hFr hF0 hr hs b d,
    chartScalarFromMetric_eq_jet hν hF hνr hFr hF0 hr hs]

def tovNumerator (m κ p Λ r : ℝ) : ℝ :=
  m + κ * p * r ^ 3 / 2 - Λ * r ^ 3 / 3

def tovNumeratorJet (mr κ p pr Λ r : ℝ) : ℝ :=
  mr + κ * pr * r ^ 3 / 2 + 3 * κ * p * r ^ 2 / 2 - Λ * r ^ 2

def tovDenominator (F r : ℝ) : ℝ := r ^ 2 * F
def tovDenominatorJet (F Fr r : ℝ) : ℝ := 2 * r * F + r ^ 2 * Fr

def tovNuSecondJet (m mr κ p pr Λ F Fr r : ℝ) : ℝ :=
  (tovNumeratorJet mr κ p pr Λ r * tovDenominator F r -
    tovNumerator m κ p Λ r * tovDenominatorJet F Fr r) /
    (tovDenominator F r) ^ 2

theorem tangential_tov_jet_algebra
    {m mr κ p pr ε Λ F Fr r : ℝ}
    (hr : r ≠ 0) (hF : F ≠ 0)
    (hm : mr = κ * r ^ 2 * ε / 2)
    (hp : pr = -(ε + p) *
      (tovNumerator m κ p Λ r / tovDenominator F r))
    (hFvalue : F = 1 - 2 * m / r - Λ * r ^ 2 / 3)
    (hFr : Fr = massLapseJet m mr Λ r) :
    F * (tovNuSecondJet m mr κ p pr Λ F Fr r +
      (tovNumerator m κ p Λ r / tovDenominator F r) ^ 2 +
      (tovNumerator m κ p Λ r / tovDenominator F r) / r) +
      Fr * ((tovNumerator m κ p Λ r / tovDenominator F r) / 2 +
        1 / (2 * r)) + Λ = κ * p := by
  rw [hm] at hFr
  rw [hm, hp, hFr]
  unfold tovNuSecondJet tovNumeratorJet tovNumerator
    tovDenominator tovDenominatorJet massLapseJet
  field_simp [hr, hF]
  rw [hFvalue]
  field_simp [hr]
  ring

def tovNuFunction (m p F : ℝ → ℝ) (κ Λ s : ℝ) : ℝ :=
  (m s + (κ / 2) * (p s * s ^ 3) - (Λ / 3) * s ^ 3) /
    (s ^ 2 * F s)

theorem tovNuFunction_value (m p F : ℝ → ℝ) (κ Λ r : ℝ) :
    tovNuFunction m p F κ Λ r =
      tovNumerator (m r) κ (p r) Λ r / tovDenominator (F r) r := by
  unfold tovNuFunction tovNumerator tovDenominator
  congr 1
  ring

theorem tovNuFunction_derivative
    {m p F : ℝ → ℝ} {κ Λ r mr pr Fr : ℝ}
    (hm : HasDerivAt m mr r)
    (hp : HasDerivAt p pr r)
    (hF : HasDerivAt F Fr r)
    (hr : r ≠ 0) (hF0 : F r ≠ 0) :
    HasDerivAt (tovNuFunction m p F κ Λ)
      (tovNuSecondJet (m r) mr κ (p r) pr Λ (F r) Fr r) r := by
  have hpow3 : HasDerivAt (fun s : ℝ => s ^ 3) (3 * r ^ 2) r := by
    simpa using (hasDerivAt_pow 3 r :
      HasDerivAt (fun s : ℝ => s ^ 3) (3 * r ^ (3 - 1)) r)
  have hpow2 : HasDerivAt (fun s : ℝ => s ^ 2) (2 * r) r := by
    change HasDerivAt metric22 (2 * r) r
    exact metric22_derivative r
  have hN := (hm.add ((hp.mul hpow3).const_mul (κ / 2))).sub
    (hpow3.const_mul (Λ / 3))
  have hD := hpow2.mul hF
  have hD0 : r ^ 2 * F r ≠ 0 := mul_ne_zero (pow_ne_zero 2 hr) hF0
  have hquot := hN.div hD hD0
  convert hquot using 1 <;> try {rfl} <;>
    simp [tovNuFunction, tovNuSecondJet, tovNumeratorJet,
      tovNumerator, tovDenominator, tovDenominatorJet,
      Pi.add_apply, Pi.sub_apply, Pi.mul_apply] <;>
    ring

#print axioms chartRiemannJet_mixed_zero
#print axioms gamma111_table_radial_derivative
#print axioms chartGammaTable_radial_derivative
#print axioms chartGammaTable_angular_derivative
#print axioms chartGamma_radial_derivative_all
#print axioms chartGamma_angular_derivative_all
#print axioms chartGammaCoordinateLine_derivative
#print axioms chartRiemannFromMetric_eq_jet
#print axioms chartRiemannFromMetric_mixed_zero
#print axioms chartRicciFromMetric_eq_jet
#print axioms chartRicciFromMetric_offdiag_zero
#print axioms chartRicciJet_00
#print axioms chartRicciJet_11
#print axioms chartRicciJet_22
#print axioms chartRicciJet_33
#print axioms chartScalarJet_reduction
#print axioms chartEinsteinJet_offdiag_zero
#print axioms chartEinsteinJet_hat00
#print axioms chartEinsteinJet_hat11
#print axioms chartEinsteinJet_hat22
#print axioms chartEinsteinJet_hat33
#print axioms chartScalarFromMetric_eq_jet
#print axioms chartEinsteinFromMetric_eq_jet
#print axioms tangential_tov_jet_algebra
#print axioms tovNuFunction_value
#print axioms tovNuFunction_derivative

#print axioms staticVelocity0_radial_derivative
#print axioms staticVelocity_time_derivative
#print axioms staticVelocity_angular_derivative
#print axioms staticAccel_at_normalized_event
#print axioms staticAccel_components
#print axioms staticAccel_metric_norm
#print axioms matched_static_accel_metric_norm
#print axioms fixed_family_static_accel_metric_limit

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
#print axioms staticGamma001_derivative
#print axioms staticGamma100_derivative
#print axioms coordinateR1010_from_connection
#print axioms coordinateR2020_from_connection
#print axioms coordinateR3030_from_connection
#print axioms ricci00_reduction
#print axioms chartGamma212_all
#print axioms staticGamma212_derivative
#print axioms coordinateR2121_from_connection
#print axioms coordinateR3131_from_connection
#print axioms coordinateR0101_from_connection
#print axioms ricci11_reduction
#print axioms orthonormalR0101_from_connection
#print axioms coordinateR0202_from_connection
#print axioms orthonormalR0202_from_connection
#print axioms chartGamma122
#print axioms staticGamma122_derivative
#print axioms coordinateR1212_from_connection
#print axioms orthonormalR1212_from_connection
#print axioms chartGamma233
#print axioms gamma233_angular_derivative
#print axioms coordinateR2323_from_connection
#print axioms orthonormalR2323_from_connection
#print axioms cotangent_angular_derivative
#print axioms angularGamma323_derivative
#print axioms coordinateR3232_from_connection
#print axioms ricci22_reduction
#print axioms coordinateR0303_from_connection
#print axioms staticGamma133_derivative
#print axioms coordinateR1313_from_connection
#print axioms ricci33_reduction
#print axioms einsteinHat00_from_connection
#print axioms einsteinHat00_tov_from_connection
#print axioms einsteinHat11_from_connection
#print axioms einsteinHat11_tov_from_connection

end
end CAS06Adopted
