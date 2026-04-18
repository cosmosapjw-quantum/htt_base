// PSTF (Projected Symmetric Trace-Free) tensor algebra.
// BC-01: STF projection, contraction, angular integrals, Clebsch-Gordan.

pub(crate) mod tensor;
pub(crate) mod coupling;
pub(crate) mod hierarchy_matrix;
pub(crate) mod hierarchy;
pub(crate) mod m_decomposition;
pub(crate) mod lm_indexing;  // P1-01: (ℓ,m) m-major state vector layout
pub(crate) mod streaming_lm; // P1-02: m-dependent streaming matrix
pub(crate) mod collision_lm; // P1-03: m-dependent collision + Θ⁴ + baryon
pub(crate) mod tca_lm;       // P1-04: operator-based TCA (25 DOF)
#[cfg(test)]
mod integration_tests;
