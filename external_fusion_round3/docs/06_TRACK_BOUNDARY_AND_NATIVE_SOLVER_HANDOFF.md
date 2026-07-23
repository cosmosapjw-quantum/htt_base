# Track Boundary and Native Solver Handoff Contract

Track I may consume FLRW Boltzmann codes, lightcone/LSS simulators, phenomenological source injectors and real CMB/LSS products.  It may report response rank, source-confusion, identified sets, coverage and actual-data consistency.  It may not emit a Bianchi family posterior, native anisotropic transfer validation or geometry identification.

Track II requires an authenticated `SolverDeliveryReceipt` containing source and environment hashes, tetrad/frame conventions, harmonic and spin phases, time/redshift coordinate, T/E/B transfer, recombination/reionization, conservation, FLRW exact null, Bianchi-I analytic benchmark, convergence and an independent oracle.

`python experiments/track_boundary_validator.py --track II` must exit 3 until the receipt exists.  A synthetic or mock receipt is a blocker fixture, never a scientific unlock.
