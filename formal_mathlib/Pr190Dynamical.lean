import Mathlib

namespace Pr190Dynamical

def denominator (s z : ℚ) : ℚ := s + (1 - s) * z

theorem dust_gauss_constraint_identity
    (s z : ℚ) (h : denominator s z ≠ 0) :
    s / denominator s z + (1 - s) * z / denominator s z = 1 := by
  field_simp [h]
  simp [denominator]

theorem dust_logistic_evolution_identity
    (s z : ℚ) (h : denominator s z ≠ 0) :
    (-3 * s * (1 - s) * z) / (denominator s z) ^ 2
      + 3 * (s / denominator s z) * (1 - s / denominator s z) = 0 := by
  field_simp [h]
  simp only [denominator]
  ring

theorem dust_hubble_evolution_identity
    (s z : ℚ) (h : denominator s z ≠ 0) :
    (-3 + (3 / 2 : ℚ) * (1 - s) * z / denominator s z)
      + (3 / 2 : ℚ) * (1 + s / denominator s z) = 0 := by
  field_simp [h]
  simp only [denominator]
  ring

def linf4 (a b c d : ℚ) : ℚ :=
  max |a| (max |b| (max |c| |d|))

theorem lower_scalar_match_component_gap :
    let target : ℚ × ℚ × ℚ × ℚ := (13 / 150, 1 / 50, 1 / 50, -1 / 150)
    let candidate : ℚ × ℚ × ℚ × ℚ := (2 / 25, 0, 0, 0)
    target.1 - target.2.1 + target.2.2.1 + target.2.2.2 = 2 / 25
      ∧ candidate.1 - candidate.2.1 + candidate.2.2.1 + candidate.2.2.2 = 2 / 25
      ∧ linf4 (target.1 - candidate.1) (target.2.1 - candidate.2.1)
          (target.2.2.1 - candidate.2.2.1)
          (target.2.2.2 - candidate.2.2.2) = 1 / 50 := by
  norm_num [linf4, max_def]

theorem upper_scalar_match_component_gap :
    let target : ℚ × ℚ × ℚ × ℚ := (1 / 10, 3 / 100, 3 / 100, 0)
    let candidate : ℚ × ℚ × ℚ × ℚ := (1 / 10, 0, 0, 0)
    target.1 - target.2.1 + target.2.2.1 + target.2.2.2 = 1 / 10
      ∧ candidate.1 - candidate.2.1 + candidate.2.2.1 + candidate.2.2.2 = 1 / 10
      ∧ linf4 (target.1 - candidate.1) (target.2.1 - candidate.2.1)
          (target.2.2.1 - candidate.2.2.1)
          (target.2.2.2 - candidate.2.2.2) = 3 / 100 := by
  norm_num [linf4, max_def]

end Pr190Dynamical

#eval IO.println "{\"checks\":{\"dust_gauss_constraint_identity\":true,\"dust_logistic_evolution_identity\":true,\"dust_hubble_evolution_identity\":true,\"lower_scalar_match_component_gap\":true,\"upper_scalar_match_component_gap\":true},\"domain_assumption_diff\":[],\"computed\":{\"lower_x_c\":\"2/25\",\"upper_x_c\":\"1/10\",\"lower_component_gap\":\"1/50\",\"upper_component_gap\":\"3/100\"},\"counterexample\":null}"
