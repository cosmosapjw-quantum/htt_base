import Mathlib.Tactic

/- Scoped arithmetic certificates for I3's idealized full-sky response.
   The spherical moment identities are assumptions of these reductions;
   this file does not formalize the optics, source selection, or data law. -/
namespace HTTMESI3

theorem stf_sphere_gram_from_moments
    (trS trT inner : ℝ) (hS : trS = 0) (hT : trT = 0) :
    inner / 3 - (trS * trT + 2 * inner) / 15 = inner / 5 := by
  rw [hS, hT]
  ring

theorem tilt_gram_det (p1 p2 p3 : ℝ) :
    let q := p1^2 + p2^2 + p3^2
    let a := q/2 + p1^2/6
    let d := q/2 + p2^2/6
    let f := q/2 + p3^2/6
    let b := p1*p2/6
    let c := p1*p3/6
    let e := p2*p3/6
    a*d*f + 2*b*c*e - a*e^2 - d*c^2 - f*b^2 = q^3/6 := by
  dsimp
  ring

end HTTMESI3
