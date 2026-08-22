use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use std::collections::{BTreeMap, BTreeSet};

use crate::authority::HumanAuthorizationReceipt;
use crate::canonical_json::{content_id, parse_canonical, parse_strict, require_sha256};

const RECORD_FIELDS: &[&str] = &[
    "schema",
    "record_id",
    "inspection_receipt_id",
    "lane_id",
    "product_id",
    "component_id",
    "component_ordinal",
    "source_locator_kind",
    "source_locator_identity",
    "release_name",
    "release_version",
    "release_identity",
    "license_identity",
    "regular_file_status",
    "symlink_status",
    "byte_size",
    "content_sha256",
    "component_inventory_id",
    "completeness_status",
    "units_contract_id",
    "coordinate_frame_id",
    "sign_orientation_convention_id",
    "directional_convention_id",
    "harmonic_convention_id",
    "mask_id",
    "selection_id",
    "sky_support_id",
    "covariance_id",
    "covariance_status",
    "null_ensemble_id",
    "null_ensemble_status",
    "transfer_source",
    "transfer_function_spec_id",
    "transfer_provenance_status",
    "sky_support_status",
    "license_status",
    "native_identity_profile_id",
    "native_identity_profile",
    "acquisition_status",
    "inspected_at_utc",
];

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct LaneRegistry {
    schema: String,
    registry_id: String,
    lane_order: Vec<String>,
    universal_semantic_fields: Vec<String>,
    lanes: Vec<LaneSpec>,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct LaneSpec {
    lane_id: String,
    product_id: String,
    required_component_ids: Vec<String>,
    component_cardinality: BTreeMap<String, u64>,
    native_identity_schema: String,
    required_human_gate_id: String,
    analysis_plan_id: String,
    allowed_transfer_sources: Vec<String>,
    name_only_forbidden: bool,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct AdmissionDecision {
    lane_id: String,
    product_id: String,
    status: String,
    reasons: Vec<String>,
    records: Vec<Value>,
    lane_admission_bundle_id: Option<String>,
}

#[derive(Debug, Clone)]
pub(crate) struct ReplayedAdmission {
    pub(crate) lane_id: String,
    pub(crate) analysis_plan_id: String,
    pub(crate) required_human_gate_id: String,
    pub(crate) record_ids: Vec<String>,
    pub(crate) bundle_id: String,
}

fn object<'a>(value: &'a Value, field: &str) -> Result<&'a Map<String, Value>, String> {
    value
        .as_object()
        .ok_or_else(|| format!("{field} must be a JSON object"))
}

fn string_field<'a>(map: &'a Map<String, Value>, field: &str) -> Result<&'a str, String> {
    map.get(field)
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty() && value.trim() == *value && value.is_ascii())
        .ok_or_else(|| format!("record {field} is not a canonical string"))
}

pub(crate) fn replay_exact_admission(
    registry_raw: &[u8],
    decision_raw: &[u8],
    authorization: &HumanAuthorizationReceipt,
) -> Result<ReplayedAdmission, String> {
    let registry: LaneRegistry = parse_strict(registry_raw, "PR-289 lane registry")?;
    if registry.schema != "common.data_identity_lane_registry.v2"
        || registry.registry_id != "PR289-LANE-REGISTRY-V2"
        || registry.lane_order.iter().collect::<BTreeSet<_>>().len() != registry.lane_order.len()
        || registry.lane_order
            != registry
                .lanes
                .iter()
                .map(|lane| lane.lane_id.clone())
                .collect::<Vec<_>>()
    {
        return Err("PR-289 lane registry authority drifted".to_owned());
    }
    let lane = registry
        .lanes
        .iter()
        .find(|lane| lane.lane_id == authorization.lane_id)
        .ok_or_else(|| "authorization lane is not registered by PR-289".to_owned())?;
    if lane.required_human_gate_id != authorization.required_human_gate_id
        || lane.analysis_plan_id != authorization.analysis_plan_id
        || lane.required_component_ids.is_empty()
        || lane
            .required_component_ids
            .iter()
            .collect::<BTreeSet<_>>()
            .len()
            != lane.required_component_ids.len()
        || lane.component_cardinality.keys().collect::<BTreeSet<_>>()
            != lane.required_component_ids.iter().collect::<BTreeSet<_>>()
    {
        return Err("PR-289 lane spec or authorization binding drifted".to_owned());
    }
    let decision: AdmissionDecision =
        parse_canonical(decision_raw, "PR-289 complete admission decision")?;
    if decision.lane_id != lane.lane_id
        || decision.product_id != lane.product_id
        || decision.status != "ADMITTED_IDENTITY_ONLY"
        || !decision.reasons.is_empty()
        || decision.records.is_empty()
    {
        return Err("authorization requires one complete PR-289 admission".to_owned());
    }
    let expected_fields: BTreeSet<&str> = RECORD_FIELDS.iter().copied().collect();
    let mut record_ids = Vec::new();
    let mut roles = Vec::new();
    let mut inventory_id: Option<String> = None;
    let mut shared: Option<Map<String, Value>> = None;
    for (index, record) in decision.records.iter().enumerate() {
        let row = object(record, "admission record")?;
        if row.keys().map(String::as_str).collect::<BTreeSet<_>>() != expected_fields {
            return Err(format!("PR-289 admission record {index} fields drifted"));
        }
        if string_field(row, "schema")? != "common.data_identity_record.v2"
            || string_field(row, "lane_id")? != lane.lane_id
            || string_field(row, "product_id")? != lane.product_id
            || string_field(row, "acquisition_status")? != "COMPLETE"
        {
            return Err(format!("PR-289 admission record {index} identity drifted"));
        }
        let record_id = string_field(row, "record_id")?.to_owned();
        let inspection_id = string_field(row, "inspection_receipt_id")?.to_owned();
        require_sha256(&record_id, "record_id")?;
        require_sha256(&inspection_id, "inspection_receipt_id")?;
        require_sha256(string_field(row, "content_sha256")?, "content_sha256")?;
        let profile_id = string_field(row, "native_identity_profile_id")?;
        require_sha256(profile_id, "native_identity_profile_id")?;
        if object(
            row.get("native_identity_profile")
                .ok_or_else(|| "native identity profile missing".to_owned())?,
            "native identity profile",
        )?
        .get("profile_id")
        .and_then(Value::as_str)
            != Some(profile_id)
        {
            return Err("native identity profile identity drifted".to_owned());
        }
        let mut stable = row.clone();
        stable.remove("record_id");
        stable.remove("inspection_receipt_id");
        stable.remove("inspected_at_utc");
        if record_id != content_id(&Value::Object(stable))? {
            return Err(format!("PR-289 record_id {index} does not replay"));
        }
        let mut inspection = row.clone();
        inspection.remove("inspection_receipt_id");
        if inspection_id != content_id(&Value::Object(inspection))? {
            return Err(format!("PR-289 inspection receipt {index} does not replay"));
        }
        let component = string_field(row, "component_id")?.to_owned();
        let ordinal = row
            .get("component_ordinal")
            .and_then(Value::as_u64)
            .ok_or_else(|| "component_ordinal is invalid".to_owned())?;
        roles.push((component, ordinal));
        let current_inventory = string_field(row, "component_inventory_id")?.to_owned();
        require_sha256(&current_inventory, "component_inventory_id")?;
        if inventory_id.get_or_insert_with(|| current_inventory.clone()) != &current_inventory {
            return Err("admitted records disagree on component inventory".to_owned());
        }
        let mut current_shared = row.clone();
        for key in [
            "record_id",
            "inspection_receipt_id",
            "component_id",
            "component_ordinal",
            "byte_size",
            "content_sha256",
        ] {
            current_shared.remove(key);
        }
        if let Some(expected) = &shared {
            if expected != &current_shared {
                return Err("admitted record semantic fields disagree".to_owned());
            }
        } else {
            shared = Some(current_shared);
        }
        record_ids.push(record_id);
    }
    let expected_roles = lane
        .required_component_ids
        .iter()
        .flat_map(|component| {
            let count = lane
                .component_cardinality
                .get(component)
                .copied()
                .unwrap_or(0);
            (0..count).map(move |ordinal| (component.clone(), ordinal))
        })
        .collect::<Vec<_>>();
    if roles != expected_roles || record_ids != authorization.exact_admission_record_ids {
        return Err("ordered admission record inventory drifted".to_owned());
    }
    let bundle = content_id(&serde_json::json!({
        "lane_id": lane.lane_id,
        "product_id": lane.product_id,
        "component_inventory_id": inventory_id.ok_or_else(|| "missing component inventory".to_owned())?,
        "record_ids": record_ids,
    }))?;
    if decision.lane_admission_bundle_id.as_deref() != Some(&bundle)
        || authorization.lane_admission_bundle_id != bundle
    {
        return Err("lane admission bundle identity drifted".to_owned());
    }
    Ok(ReplayedAdmission {
        lane_id: lane.lane_id.clone(),
        analysis_plan_id: lane.analysis_plan_id.clone(),
        required_human_gate_id: lane.required_human_gate_id.clone(),
        record_ids,
        bundle_id: bundle,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn refused_decision_never_replays_as_complete_admission() {
        let authorization = HumanAuthorizationReceipt {
            authorization_id: format!("sha256:{}", "0".repeat(64)),
            schema: "common.human_execution_authorization_receipt.v3".to_owned(),
            lane_id: "PLANCK".to_owned(),
            exact_admission_record_ids: vec![format!("sha256:{}", "1".repeat(64))],
            lane_admission_bundle_id: format!("sha256:{}", "2".repeat(64)),
            analysis_plan_id: "plan:p".to_owned(),
            required_human_gate_id: "H-PLANCK".to_owned(),
            authorized_scope: "admitted_planck_observed_execution".to_owned(),
            authorization_domain: "lane_data_execution".to_owned(),
            model_contract_content_id: format!("sha256:{}", "3".repeat(64)),
            runtime_environment_receipt_id: format!("sha256:{}", "4".repeat(64)),
            computed_response_rank_receipt_id: format!("sha256:{}", "5".repeat(64)),
            normalization_evidence_id: format!("sha256:{}", "6".repeat(64)),
            execution_plan_content_id: format!("sha256:{}", "7".repeat(64)),
            candidate_commit: "a".repeat(40),
            candidate_tree: "b".repeat(40),
            issued_at_utc: "2026-08-22T00:00:00Z".to_owned(),
            expires_at_utc: "2026-08-22T00:10:00Z".to_owned(),
            nonce: format!("nonce:v1:{}", "8".repeat(64)),
            signer_key_id: format!("sha256:{}", "9".repeat(64)),
            authorization_signature_ed25519: "x".to_owned(),
        };
        let registry = br#"{"lane_order":["PLANCK"],"lanes":[{"allowed_transfer_sources":["none"],"analysis_plan_id":"plan:p","component_cardinality":{"map":1},"lane_id":"PLANCK","name_only_forbidden":true,"native_identity_schema":"x","product_id":"p","required_component_ids":["map"],"required_human_gate_id":"H-PLANCK"}],"registry_id":"PR289-LANE-REGISTRY-V2","schema":"common.data_identity_lane_registry.v2","universal_semantic_fields":[]}"#;
        let decision = br#"{"lane_admission_bundle_id":null,"lane_id":"PLANCK","product_id":"p","reasons":["missing"],"records":[],"status":"REJECTED_NOT_PRESENT"}"#;
        assert!(replay_exact_admission(registry, decision, &authorization).is_err());
    }
}
