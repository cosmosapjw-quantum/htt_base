import Pr124Mes.Basic

/-- PR-124 Lean axis runner: every proposition in `Pr124Mes.Basic` is closed
    by `native_decide` at elaboration time, so a successful `lake build` IS
    the check. `main` re-`decide`s the load-bearing propositions at runtime,
    emits the COMPUTED exact rationals (so the orchestrator cross-checks
    this axis against the contract values like the other three engines),
    and prints one JSON object. -/
def main : IO Unit := do
  let checks : List (String × Bool) := [
    ("sigma_reduction",
      decide (Pr124Mes.sigmaTriple = ((5:Rat)/3, (3:Rat), (3:Rat)/7))),
    ("omega_reduction",
      decide (Pr124Mes.omegaTriple = ((10:Rat)/3, (2:Rat)/15, (0:Rat)))),
    ("e1_crit_coefficients",
      decide (Pr124Mes.e1CritDerived = Pr124Mes.e1Crit)),
    ("w2_ceiling_exact",
      decide (Pr124Mes.w2Max
        = (4223652872547 : Rat) / 12500000000000000000000000)),
    ("sigma2_ceiling_exact",
      decide (Pr124Mes.sigma2Max
        = (6479509460609043 : Rat) / 24500000000000000000000000)),
    ("hierarchy_e1_zero_strict",
      Pr124Mes.ratPos (Pr124Mes.bSigma 0 Pr124Mes.e2v Pr124Mes.e3v
          - Pr124Mes.bOmega 0 Pr124Mes.e2v Pr124Mes.e3v)
        && Pr124Mes.ratPos (Pr124Mes.bOmega 0 Pr124Mes.e2v Pr124Mes.e3v)),
    ("hierarchy_observed_fails",
      Pr124Mes.ratPos (Pr124Mes.bOmega Pr124Mes.e1Obs Pr124Mes.e2v Pr124Mes.e3v
        - Pr124Mes.bSigma Pr124Mes.e1Obs Pr124Mes.e2v Pr124Mes.e3v)),
    ("boundary_e1_crit_equality",
      decide (Pr124Mes.bSigma Pr124Mes.e1Crit Pr124Mes.e2v Pr124Mes.e3v
        = Pr124Mes.bOmega Pr124Mes.e1Crit Pr124Mes.e2v Pr124Mes.e3v))
  ]
  let allTrue := checks.all (fun p => p.2)
  let body := String.intercalate ","
    (checks.map (fun p =>
      "\"" ++ p.1 ++ "\":" ++ (if p.2 then "true" else "false")))
  let q := fun (r : Rat) => "\"" ++ Pr124Mes.ratStr r ++ "\""
  let computed := String.intercalate "," [
    "\"sigma_triple\":[" ++ q Pr124Mes.sigmaTriple.1 ++ ","
      ++ q Pr124Mes.sigmaTriple.2.1 ++ "," ++ q Pr124Mes.sigmaTriple.2.2 ++ "]",
    "\"omega_triple\":[" ++ q Pr124Mes.omegaTriple.1 ++ ","
      ++ q Pr124Mes.omegaTriple.2.1 ++ "," ++ q Pr124Mes.omegaTriple.2.2 ++ "]",
    "\"B_sigma_exact\":" ++ q (Pr124Mes.bSigma 0 Pr124Mes.e2v Pr124Mes.e3v),
    "\"B_omega_exact\":" ++ q (Pr124Mes.bOmega 0 Pr124Mes.e2v Pr124Mes.e3v),
    "\"W2_max_exact\":" ++ q Pr124Mes.w2Max,
    "\"Sigma2_max_exact\":" ++ q Pr124Mes.sigma2Max
  ]
  -- engine_version is the repo-pinned toolchain; the runner additionally
  -- records the live command exit in the axis envelope.
  IO.println ("{\"engine\":\"lean\",\"engine_version\":\"lean4:v4.31.0-repo-pinned\""
    ++ ",\"checks\":{" ++ body ++ "},\"computed\":{" ++ computed
    ++ "},\"all_pass\":" ++ (if allTrue then "true" else "false") ++ "}")
