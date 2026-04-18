// Bianchi type registry: classification, canonical parameters.
// BB-01: 9 algebraically distinct types from Ellis-MacCallum decomposition.

/// The 9 Bianchi types. VI_h and VII_h carry a continuous group parameter h.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) enum BianchiType {
    I,
    II,
    III,       // special case of VI_h with h = -1
    IV,
    V,
    VI0,
    VIh(f64),  // h < 0, h ≠ -1
    VII0,
    VIIh(f64), // h > 0
    VIII,
    IX,
}

/// Ellis-MacCallum class: A (a = 0) or B (a ≠ 0).
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) enum BianchiClass {
    A,
    B,
}

/// Canonical parameters for a Bianchi type.
///
/// The Ellis-MacCallum decomposition is:
///   C^α_{βγ} = ε_{βγδ} n^{αδ} + δ^α_{[β} a_{γ]}
/// with Jacobi identity n^{αβ} a_β = 0.
#[derive(Clone, Debug)]
pub(crate) struct BianchiParams {
    pub(crate) btype: BianchiType,
    pub(crate) n_eigenvalues: [f64; 3],  // (n₁, n₂, n₃) eigenvalues of n^{αβ}
    pub(crate) a_magnitude: f64,          // |a_α| (a₃ component in canonical frame)
    pub(crate) h_param: Option<f64>,      // group parameter for VI_h, VII_h
}

impl BianchiType {
    /// Return the Ellis-MacCallum class.
    pub(crate) fn class(&self) -> BianchiClass {
        match self {
            BianchiType::I | BianchiType::II | BianchiType::VI0
            | BianchiType::VII0 | BianchiType::VIII | BianchiType::IX
                => BianchiClass::A,
            BianchiType::III | BianchiType::IV | BianchiType::V
            | BianchiType::VIh(_) | BianchiType::VIIh(_)
                => BianchiClass::B,
        }
    }

    /// Whether this type admits an FLRW (isotropic) limit.
    ///
    /// FLRW limits: I (k=0), V (k=−1), VII₀ (k=0), VII_h (k<0), IX (k=+1).
    pub(crate) fn has_flrw_limit(&self) -> bool {
        matches!(self,
            BianchiType::I | BianchiType::V | BianchiType::VII0
            | BianchiType::VIIh(_) | BianchiType::IX
        )
    }

    /// Canonical (n₁, n₂, n₃, a) for this type.
    pub(crate) fn canonical_params(&self) -> BianchiParams {
        let (n, a, h) = match self {
            // Class A: a = 0
            BianchiType::I    => ([0.0, 0.0, 0.0], 0.0, None),
            BianchiType::II   => ([1.0, 0.0, 0.0], 0.0, None),
            BianchiType::VI0  => ([1.0, -1.0, 0.0], 0.0, None),
            BianchiType::VII0 => ([1.0, 1.0, 0.0], 0.0, None),
            BianchiType::VIII => ([1.0, 1.0, -1.0], 0.0, None),
            BianchiType::IX   => ([1.0, 1.0, 1.0], 0.0, None),
            // Class B: a ≠ 0, n₃ = 0 (Jacobi identity)
            BianchiType::V    => ([0.0, 0.0, 0.0], 1.0, None),
            BianchiType::IV   => ([1.0, 0.0, 0.0], 1.0, None),
            BianchiType::III  => ([1.0, -1.0, 0.0], 1.0, Some(-1.0)),
            // VI_h: h = a²/(n₁n₂) < 0 → a = sqrt(-h) with n₁=1, n₂=-1
            BianchiType::VIh(h) => {
                let a = (-h).abs().sqrt();
                ([1.0, -1.0, 0.0], a, Some(*h))
            }
            // VII_h: h = a²/(n₁n₂) > 0 → a = sqrt(h) with n₁=1, n₂=1
            BianchiType::VIIh(h) => {
                let a = h.abs().sqrt();
                ([1.0, 1.0, 0.0], a, Some(*h))
            }
        };
        BianchiParams {
            btype: *self,
            n_eigenvalues: n,
            a_magnitude: a,
            h_param: h,
        }
    }

    /// Short label for display.
    pub(crate) fn label(&self) -> String {
        match self {
            BianchiType::I => "I".into(),
            BianchiType::II => "II".into(),
            BianchiType::III => "III".into(),
            BianchiType::IV => "IV".into(),
            BianchiType::V => "V".into(),
            BianchiType::VI0 => "VI₀".into(),
            BianchiType::VIh(h) => format!("VI_h(h={:.4})", h),
            BianchiType::VII0 => "VII₀".into(),
            BianchiType::VIIh(h) => format!("VII_h(h={:.4})", h),
            BianchiType::VIII => "VIII".into(),
            BianchiType::IX => "IX".into(),
        }
    }
}

/// All 9 canonical types (VI_h and VII_h use representative h values).
pub(crate) fn all_canonical_types() -> Vec<BianchiType> {
    vec![
        BianchiType::I,
        BianchiType::II,
        BianchiType::III,
        BianchiType::IV,
        BianchiType::V,
        BianchiType::VI0,
        BianchiType::VII0,
        BianchiType::VIh(-0.5),   // representative h for VI_h
        BianchiType::VIIh(0.5),   // representative h for VII_h
        BianchiType::VIII,
        BianchiType::IX,
    ]
}
