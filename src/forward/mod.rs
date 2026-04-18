pub(crate) mod bass_rhs;
pub(crate) mod d2_convention;  // CL-08 audit: D₂/Σ²/σ/H normalization SSOT
pub(crate) mod htt_bridge;
pub(crate) mod biposh_channel;
pub(crate) mod mio_bridge;
pub(crate) mod atlas_export;     // HI-01: atlas serialization for HTT ingestion
#[cfg(test)]
mod end_to_end;
