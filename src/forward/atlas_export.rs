// HI-01 (Rust side): Atlas Export for HTT Ingestion.
//
// Serializes the pre-computed Atlas (from BF-02/atlas.rs) to JSON format
// that Python's atlas_loader.py can read.
//
// Format:
// {
//   "config": { "sigma2_grid": [...], "beta_grid": [...], "ell_max": N,
//               "types": ["I", "V", "VII_h", "IX"], "sectors": ["orth", "tilt"] },
//   "entries": [
//     { "type": "I", "sector": "orth", "sigma2": 1e-8, "beta": 0.0,
//       "cl_tt": [...], "d2_uK2": 0.174, "biposh_power": [...] },
//     ...
//   ]
// }

use crate::inference::atlas::{Atlas, AtlasConfig, AtlasEntry};
use crate::inference::directional::{BianchiType, TiltSector};

/// Serialize Atlas to JSON string.
pub(crate) fn atlas_to_json(atlas: &Atlas) -> String {
    let cfg = &atlas.config;
    let n_type = cfg.types.len();
    let n_sector = cfg.sectors.len();
    let n_s2 = cfg.sigma2_grid.len();
    let n_beta = cfg.beta_grid.len();

    let mut json = String::with_capacity(1024 * 1024); // ~1MB estimate
    json.push_str("{\n");

    // Config section
    json.push_str("  \"config\": {\n");
    json.push_str(&format!("    \"ell_max\": {},\n", cfg.ell_max));
    json.push_str("    \"sigma2_grid\": [");
    for (i, &s2) in cfg.sigma2_grid.iter().enumerate() {
        if i > 0 { json.push_str(", "); }
        json.push_str(&format!("{:.6e}", s2));
    }
    json.push_str("],\n");
    json.push_str("    \"beta_grid\": [");
    for (i, &b) in cfg.beta_grid.iter().enumerate() {
        if i > 0 { json.push_str(", "); }
        json.push_str(&format!("{:.6e}", b));
    }
    json.push_str("],\n");
    json.push_str("    \"types\": [");
    for (i, t) in cfg.types.iter().enumerate() {
        if i > 0 { json.push_str(", "); }
        json.push_str(&format!("\"{}\"", t.label()));
    }
    json.push_str("],\n");
    json.push_str("    \"sectors\": [");
    for (i, s) in cfg.sectors.iter().enumerate() {
        if i > 0 { json.push_str(", "); }
        let label = match s { TiltSector::Orthogonal => "orth", TiltSector::Tilted => "tilt" };
        json.push_str(&format!("\"{}\"", label));
    }
    json.push_str("]\n  },\n");

    // Entries
    json.push_str("  \"entries\": [\n");
    let mut first = true;
    for ti in 0..n_type {
        for si in 0..n_sector {
            for s2i in 0..n_s2 {
                for bi in 0..n_beta {
                    let entry = atlas.get(ti, si, s2i, bi);
                    if !first { json.push_str(",\n"); }
                    first = false;

                    let sector_label = match &cfg.sectors[si] {
                        TiltSector::Orthogonal => "orth",
                        TiltSector::Tilted => "tilt",
                    };

                    json.push_str("    {");
                    json.push_str(&format!("\"type\":\"{}\",", cfg.types[ti].label()));
                    json.push_str(&format!("\"sector\":\"{}\",", sector_label));
                    json.push_str(&format!("\"sigma2\":{:.6e},", cfg.sigma2_grid[s2i]));
                    json.push_str(&format!("\"beta\":{:.6e},", cfg.beta_grid[bi]));
                    json.push_str(&format!("\"d2_uK2\":{:.6e},", entry.d2));

                    // C_ℓ (compact: only ℓ=2..min(30, ell_max))
                    let ell_out = 30.min(cfg.ell_max);
                    json.push_str("\"cl_tt\":[");
                    for ell in 2..=ell_out {
                        if ell > 2 { json.push_str(","); }
                        json.push_str(&format!("{:.6e}", entry.cl_tt[ell]));
                    }
                    json.push_str("]");
                    json.push_str("}");
                }
            }
        }
    }
    json.push_str("\n  ]\n}\n");
    json
}

/// Export atlas to file.
pub(crate) fn export_atlas_json(atlas: &Atlas, path: &str) -> Result<(), String> {
    let json = atlas_to_json(atlas);
    std::fs::write(path, &json).map_err(|e| format!("Write failed: {}", e))
}

/// Atlas summary statistics.
pub(crate) struct AtlasSummary {
    pub(crate) n_entries: usize,
    pub(crate) n_types: usize,
    pub(crate) n_sectors: usize,
    pub(crate) sigma2_range: (f64, f64),
    pub(crate) beta_range: (f64, f64),
    pub(crate) ell_max: usize,
    pub(crate) d2_range: (f64, f64),
    pub(crate) json_size_bytes: usize,
}

pub(crate) fn atlas_summary(atlas: &Atlas) -> AtlasSummary {
    let cfg = &atlas.config;
    let n = atlas.n_entries();
    let mut d2_min = f64::MAX;
    let mut d2_max = f64::MIN;

    for ti in 0..cfg.types.len() {
        for si in 0..cfg.sectors.len() {
            for s2i in 0..cfg.sigma2_grid.len() {
                for bi in 0..cfg.beta_grid.len() {
                    let d = atlas.get(ti, si, s2i, bi).d2;
                    d2_min = d2_min.min(d);
                    d2_max = d2_max.max(d);
                }
            }
        }
    }

    let json = atlas_to_json(atlas);

    AtlasSummary {
        n_entries: n,
        n_types: cfg.types.len(),
        n_sectors: cfg.sectors.len(),
        sigma2_range: (*cfg.sigma2_grid.first().unwrap_or(&0.0),
                       *cfg.sigma2_grid.last().unwrap_or(&0.0)),
        beta_range: (*cfg.beta_grid.first().unwrap_or(&0.0),
                     *cfg.beta_grid.last().unwrap_or(&0.0)),
        ell_max: cfg.ell_max,
        d2_range: (d2_min, d2_max),
        json_size_bytes: json.len(),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_atlas_export_compact() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        let json = atlas_to_json(&atlas);

        // JSON must be valid (basic structure checks)
        assert!(json.starts_with("{"), "JSON must start with {{");
        assert!(json.contains("\"config\""), "Must contain config");
        assert!(json.contains("\"entries\""), "Must contain entries");
        assert!(json.contains("\"cl_tt\""), "Must contain cl_tt");
        assert!(json.contains("\"d2_uK2\""), "Must contain d2_uK2");

        eprintln!("  Atlas JSON: {} bytes, {} entries",
            json.len(), atlas.n_entries());
    }

    #[test]
    fn test_atlas_summary() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        let summary = atlas_summary(&atlas);

        assert_eq!(summary.n_entries, atlas.n_entries());
        assert!(summary.d2_range.0 >= 0.0, "D₂ min must be ≥ 0");
        assert!(summary.d2_range.1 > 0.0, "D₂ max must be > 0");
        assert!(summary.json_size_bytes > 100, "JSON must be non-trivial");

        eprintln!("  Summary: {} entries, {} types × {} sectors",
            summary.n_entries, summary.n_types, summary.n_sectors);
        eprintln!("  D₂ range: [{:.4e}, {:.4e}] μK²",
            summary.d2_range.0, summary.d2_range.1);
        eprintln!("  JSON size: {} KB", summary.json_size_bytes / 1024);
    }

    #[test]
    fn test_atlas_d2_in_json() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        let json = atlas_to_json(&atlas);

        // Parse back a D₂ value to check consistency
        // Find first d2_uK2 value
        if let Some(pos) = json.find("\"d2_uK2\":") {
            let start = pos + 9;
            let end = json[start..].find(',').map(|p| start + p).unwrap_or(json.len());
            let d2_str = &json[start..end];
            let d2_parsed: f64 = d2_str.trim().parse().unwrap_or(-1.0);
            assert!(d2_parsed >= 0.0, "Parsed D₂ = {} (must be ≥ 0)", d2_parsed);
        }
    }

    #[test]
    fn test_atlas_types_in_json() {
        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);
        let json = atlas_to_json(&atlas);

        // All configured types must appear
        for t in &cfg.types {
            assert!(json.contains(&format!("\"type\":\"{}\"", t.label())),
                "Type {} missing from JSON", t.label());
        }
    }

    #[test]
    fn test_legacy_d2_bridge() {
        // HI-01 backward compatibility: atlas D₂ must match d2_transfer
        use crate::forward::d2_convention::d2_from_sigma2;

        let cfg = AtlasConfig::compact();
        let atlas = Atlas::build(&cfg);

        // For BI orthogonal (type_idx=0, sector_idx=0), atlas D₂ at each Σ²
        // should match the Route B transfer function
        for s2i in 0..cfg.sigma2_grid.len() {
            let s2 = cfg.sigma2_grid[s2i];
            let atlas_d2 = atlas.get(0, 0, s2i, 0).d2;

            // For BI orthogonal, forward_d2 uses d2_transfer × f2
            // f2(BI) = 1.0, so atlas_d2 = d2_transfer(s2) exactly
            let transfer_d2 = d2_from_sigma2(s2);

            // At low β=0, sector=orth: no boost contribution
            // Atlas D₂ = base_d2 × type_mod (f2=1.0 for BI)
            // Should be very close to d2_from_sigma2
            if s2 > 1e-30 && transfer_d2 > 1e-30 {
                let rel = (atlas_d2 - transfer_d2).abs() / transfer_d2;
                assert!(rel < 0.01,
                    "Σ²={:.2e}: atlas D₂={:.4e} vs transfer={:.4e}, rel={:.2e}",
                    s2, atlas_d2, transfer_d2, rel);
            }
        }
    }
}
