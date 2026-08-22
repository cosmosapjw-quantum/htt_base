use serde::{Deserialize, Serialize};
use serde_json::json;
use std::collections::BTreeMap;

use crate::canonical_json::{
    canonical_bytes, content_id, parse_canonical, parse_strict, require_git_object, require_sha256,
    sha256_identity,
};
use crate::crypto::{canonical_base64, key_id, verify_ed25519};

pub(crate) const AUTHORIZATION_DOMAIN: &str = "lane_data_execution";
pub(crate) const MAX_TTL_SECONDS: i64 = 1800;

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct RootSignaturePayload {
    pub(crate) schema: String,
    pub(crate) registry_blob_sha256: String,
    pub(crate) candidate_commit: String,
    pub(crate) candidate_tree: String,
    pub(crate) authorization_domain: String,
    pub(crate) registry_version: u64,
    pub(crate) issued_at_utc: String,
    pub(crate) root_authority_key_id: String,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct RootSignatureEnvelope {
    schema: String,
    payload: RootSignaturePayload,
    registry_signature_ed25519: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct AuthorityRow {
    pub(crate) status: String,
    pub(crate) key_id: Option<String>,
    pub(crate) public_key_base64: Option<String>,
    pub(crate) gate_id: String,
    pub(crate) scope: String,
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct HumanAuthorityRegistry {
    pub(crate) schema: String,
    pub(crate) lane_order: Vec<String>,
    pub(crate) authorities: BTreeMap<String, AuthorityRow>,
}

#[derive(Debug, Clone)]
pub(crate) struct TrustedLaneAuthority {
    pub(crate) lane_id: String,
    pub(crate) key_id: String,
    pub(crate) public_key: [u8; 32],
    pub(crate) gate_id: String,
    pub(crate) scope: String,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct HumanAuthorizationReceipt {
    pub(crate) authorization_id: String,
    pub(crate) schema: String,
    pub(crate) lane_id: String,
    pub(crate) exact_admission_record_ids: Vec<String>,
    pub(crate) lane_admission_bundle_id: String,
    pub(crate) analysis_plan_id: String,
    pub(crate) required_human_gate_id: String,
    pub(crate) authorized_scope: String,
    pub(crate) authorization_domain: String,
    pub(crate) model_contract_content_id: String,
    pub(crate) runtime_environment_receipt_id: String,
    pub(crate) computed_response_rank_receipt_id: String,
    pub(crate) normalization_evidence_id: String,
    pub(crate) execution_plan_content_id: String,
    pub(crate) candidate_commit: String,
    pub(crate) candidate_tree: String,
    pub(crate) issued_at_utc: String,
    pub(crate) expires_at_utc: String,
    pub(crate) nonce: String,
    pub(crate) signer_key_id: String,
    pub(crate) authorization_signature_ed25519: String,
}

impl HumanAuthorizationReceipt {
    pub(crate) fn unsigned_value(&self) -> serde_json::Value {
        json!({
            "schema": self.schema,
            "lane_id": self.lane_id,
            "exact_admission_record_ids": self.exact_admission_record_ids,
            "lane_admission_bundle_id": self.lane_admission_bundle_id,
            "analysis_plan_id": self.analysis_plan_id,
            "required_human_gate_id": self.required_human_gate_id,
            "authorized_scope": self.authorized_scope,
            "authorization_domain": self.authorization_domain,
            "model_contract_content_id": self.model_contract_content_id,
            "runtime_environment_receipt_id": self.runtime_environment_receipt_id,
            "computed_response_rank_receipt_id": self.computed_response_rank_receipt_id,
            "normalization_evidence_id": self.normalization_evidence_id,
            "execution_plan_content_id": self.execution_plan_content_id,
            "candidate_commit": self.candidate_commit,
            "candidate_tree": self.candidate_tree,
            "issued_at_utc": self.issued_at_utc,
            "expires_at_utc": self.expires_at_utc,
            "nonce": self.nonce,
            "signer_key_id": self.signer_key_id,
        })
    }

    pub(crate) fn signed_value(&self) -> serde_json::Value {
        let mut payload = self.unsigned_value();
        payload
            .as_object_mut()
            .expect("authorization payload is an object")
            .insert(
                "authorization_id".to_owned(),
                serde_json::Value::String(self.authorization_id.clone()),
            );
        payload
    }
}

pub(crate) fn verify_registry_root(
    registry_raw: &[u8],
    envelope_raw: &[u8],
    external_root_key: &[u8; 32],
    candidate_commit: &str,
    candidate_tree: &str,
) -> Result<(RootSignaturePayload, HumanAuthorityRegistry), String> {
    let envelope: RootSignatureEnvelope =
        parse_canonical(envelope_raw, "external registry root signature")?;
    let payload = &envelope.payload;
    if envelope.schema != "common.human_authority_registry_root_signature_envelope.v1"
        || payload.schema != "common.human_authority_registry_root_signature.v1"
        || payload.authorization_domain != AUTHORIZATION_DOMAIN
        || payload.registry_version == 0
    {
        return Err("registry root signature contract drifted".to_owned());
    }
    require_sha256(&payload.registry_blob_sha256, "registry_blob_sha256")?;
    require_sha256(&payload.root_authority_key_id, "root_authority_key_id")?;
    require_git_object(&payload.candidate_commit, "candidate_commit")?;
    require_git_object(&payload.candidate_tree, "candidate_tree")?;
    canonical_timestamp_seconds(&payload.issued_at_utc)?;
    if payload.registry_blob_sha256 != sha256_identity(registry_raw)
        || payload.root_authority_key_id != key_id(external_root_key)
        || payload.candidate_commit != candidate_commit
        || payload.candidate_tree != candidate_tree
    {
        return Err("external registry root binding mismatched".to_owned());
    }
    verify_ed25519(
        external_root_key,
        &canonical_bytes(payload)?,
        &envelope.registry_signature_ed25519,
        "registry root signature",
    )?;
    let registry: HumanAuthorityRegistry =
        parse_strict(registry_raw, "candidate human authority registry")?;
    if registry.schema != "common.human_authority_registry.v1"
        || registry.lane_order.len() != registry.authorities.len()
        || registry
            .lane_order
            .iter()
            .any(|lane| !registry.authorities.contains_key(lane))
    {
        return Err("human authority registry inventory drifted".to_owned());
    }
    Ok((payload.clone(), registry))
}

pub(crate) fn active_lane_authority(
    registry: &HumanAuthorityRegistry,
    lane_id: &str,
) -> Result<TrustedLaneAuthority, String> {
    let row = registry
        .authorities
        .get(lane_id)
        .ok_or_else(|| "lane has no root-signed authority row".to_owned())?;
    if row.status != "ACTIVE" {
        return Err("lane authority is not ACTIVE in root-signed registry".to_owned());
    }
    let key_id_value = row
        .key_id
        .as_deref()
        .ok_or_else(|| "active authority key_id is absent".to_owned())?;
    let key = canonical_base64::<32>(
        row.public_key_base64
            .as_deref()
            .ok_or_else(|| "active authority public key is absent".to_owned())?,
        "authority public key",
    )?;
    if key_id_value != key_id(&key) {
        return Err("active authority key identity mismatched".to_owned());
    }
    Ok(TrustedLaneAuthority {
        lane_id: lane_id.to_owned(),
        key_id: key_id_value.to_owned(),
        public_key: key,
        gate_id: row.gate_id.clone(),
        scope: row.scope.clone(),
    })
}

pub(crate) fn verify_human_authorization(
    raw: &[u8],
    authority: &TrustedLaneAuthority,
    candidate_commit: &str,
    candidate_tree: &str,
    evaluated_at_utc: &str,
) -> Result<HumanAuthorizationReceipt, String> {
    let receipt: HumanAuthorizationReceipt = parse_canonical(raw, "human authorization receipt")?;
    if receipt.schema != "common.human_execution_authorization_receipt.v3"
        || receipt.authorization_domain != AUTHORIZATION_DOMAIN
        || receipt.lane_id != authority.lane_id
        || receipt.signer_key_id != authority.key_id
        || receipt.required_human_gate_id != authority.gate_id
        || receipt.authorized_scope != authority.scope
        || receipt.candidate_commit != candidate_commit
        || receipt.candidate_tree != candidate_tree
    {
        return Err("human authorization authority or candidate binding drifted".to_owned());
    }
    require_git_object(&receipt.candidate_commit, "candidate_commit")?;
    require_git_object(&receipt.candidate_tree, "candidate_tree")?;
    for (field, value) in [
        ("authorization_id", &receipt.authorization_id),
        (
            "lane_admission_bundle_id",
            &receipt.lane_admission_bundle_id,
        ),
        (
            "model_contract_content_id",
            &receipt.model_contract_content_id,
        ),
        (
            "runtime_environment_receipt_id",
            &receipt.runtime_environment_receipt_id,
        ),
        (
            "computed_response_rank_receipt_id",
            &receipt.computed_response_rank_receipt_id,
        ),
        (
            "normalization_evidence_id",
            &receipt.normalization_evidence_id,
        ),
        (
            "execution_plan_content_id",
            &receipt.execution_plan_content_id,
        ),
    ] {
        require_sha256(value, field)?;
    }
    if receipt.exact_admission_record_ids.is_empty() {
        return Err("authorization has no admitted records".to_owned());
    }
    for value in &receipt.exact_admission_record_ids {
        require_sha256(value, "exact_admission_record_ids")?;
    }
    if receipt.nonce.len() != 73
        || !receipt.nonce.starts_with("nonce:v1:")
        || !receipt.nonce[9..]
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err("authorization nonce is not canonical high entropy".to_owned());
    }
    let issued = canonical_timestamp_seconds(&receipt.issued_at_utc)?;
    let expires = canonical_timestamp_seconds(&receipt.expires_at_utc)?;
    let evaluated = canonical_timestamp_seconds(evaluated_at_utc)?;
    if expires <= issued
        || expires - issued > MAX_TTL_SECONDS
        || evaluated < issued
        || evaluated >= expires
    {
        return Err("authorization time window is invalid, future, or expired".to_owned());
    }
    if receipt.authorization_id != content_id(&receipt.unsigned_value())? {
        return Err("authorization_id does not bind the unsigned receipt".to_owned());
    }
    verify_ed25519(
        &authority.public_key,
        &canonical_bytes(&receipt.signed_value())?,
        &receipt.authorization_signature_ed25519,
        "human authorization signature",
    )?;
    Ok(receipt)
}

pub(crate) fn canonical_timestamp_seconds(value: &str) -> Result<i64, String> {
    let bytes = value.as_bytes();
    if bytes.len() != 20
        || bytes[4] != b'-'
        || bytes[7] != b'-'
        || bytes[10] != b'T'
        || bytes[13] != b':'
        || bytes[16] != b':'
        || bytes[19] != b'Z'
    {
        return Err("timestamp is not canonical UTC seconds".to_owned());
    }
    let number = |start: usize, end: usize| -> Result<i64, String> {
        value[start..end]
            .parse::<i64>()
            .map_err(|_| "timestamp contains non-digits".to_owned())
    };
    let year = number(0, 4)?;
    let month = number(5, 7)?;
    let day = number(8, 10)?;
    let hour = number(11, 13)?;
    let minute = number(14, 16)?;
    let second = number(17, 19)?;
    let leap = year % 4 == 0 && (year % 100 != 0 || year % 400 == 0);
    let month_days = [
        31,
        if leap { 29 } else { 28 },
        31,
        30,
        31,
        30,
        31,
        31,
        30,
        31,
        30,
        31,
    ];
    if !(1..=12).contains(&month)
        || day < 1
        || day > month_days[(month - 1) as usize]
        || hour > 23
        || minute > 59
        || second > 59
    {
        return Err("timestamp calendar value is invalid".to_owned());
    }
    let adjusted_year = year - i64::from(month <= 2);
    let era = if adjusted_year >= 0 {
        adjusted_year
    } else {
        adjusted_year - 399
    } / 400;
    let year_of_era = adjusted_year - era * 400;
    let shifted_month = month + if month > 2 { -3 } else { 9 };
    let day_of_year = (153 * shifted_month + 2) / 5 + day - 1;
    let day_of_era = year_of_era * 365 + year_of_era / 4 - year_of_era / 100 + day_of_year;
    let days = era * 146097 + day_of_era - 719468;
    Ok(days * 86400 + hour * 3600 + minute * 60 + second)
}

#[cfg(test)]
mod tests {
    use super::*;
    use base64::engine::general_purpose::STANDARD;
    use base64::Engine as _;
    use ed25519_dalek::{Signer, SigningKey};

    fn active_registry(signing: &SigningKey) -> HumanAuthorityRegistry {
        HumanAuthorityRegistry {
            schema: "common.human_authority_registry.v1".to_owned(),
            lane_order: vec!["PLANCK".to_owned()],
            authorities: BTreeMap::from([(
                "PLANCK".to_owned(),
                AuthorityRow {
                    status: "ACTIVE".to_owned(),
                    key_id: Some(key_id(&signing.verifying_key().to_bytes())),
                    public_key_base64: Some(STANDARD.encode(signing.verifying_key().to_bytes())),
                    gate_id: "H-PLANCK".to_owned(),
                    scope: "admitted_planck_observed_execution".to_owned(),
                },
            )]),
        }
    }

    fn signed_receipt(signing: &SigningKey) -> Vec<u8> {
        let mut receipt = HumanAuthorizationReceipt {
            authorization_id: String::new(),
            schema: "common.human_execution_authorization_receipt.v3".to_owned(),
            lane_id: "PLANCK".to_owned(),
            exact_admission_record_ids: vec![format!("sha256:{}", "1".repeat(64))],
            lane_admission_bundle_id: format!("sha256:{}", "2".repeat(64)),
            analysis_plan_id: "plan:synthetic".to_owned(),
            required_human_gate_id: "H-PLANCK".to_owned(),
            authorized_scope: "admitted_planck_observed_execution".to_owned(),
            authorization_domain: AUTHORIZATION_DOMAIN.to_owned(),
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
            signer_key_id: key_id(&signing.verifying_key().to_bytes()),
            authorization_signature_ed25519: String::new(),
        };
        receipt.authorization_id = content_id(&receipt.unsigned_value()).unwrap();
        receipt.authorization_signature_ed25519 = STANDARD.encode(
            signing
                .sign(&canonical_bytes(&receipt.signed_value()).unwrap())
                .to_bytes(),
        );
        canonical_bytes(&receipt).unwrap()
    }

    #[test]
    fn validates_rooted_authorization_and_rejects_candidate_drift() {
        let signer = SigningKey::from_bytes(&[9_u8; 32]);
        let registry = active_registry(&signer);
        let authority = active_lane_authority(&registry, "PLANCK").unwrap();
        let raw = signed_receipt(&signer);
        verify_human_authorization(
            &raw,
            &authority,
            &"a".repeat(40),
            &"b".repeat(40),
            "2026-08-22T00:05:00Z",
        )
        .unwrap();
        assert!(verify_human_authorization(
            &raw,
            &authority,
            &"c".repeat(40),
            &"b".repeat(40),
            "2026-08-22T00:05:00Z",
        )
        .is_err());
    }

    #[test]
    fn pending_candidate_registry_cannot_self_authorize() {
        let signer = SigningKey::from_bytes(&[4_u8; 32]);
        let mut registry = active_registry(&signer);
        registry.authorities.get_mut("PLANCK").unwrap().status =
            "PENDING_HUMAN_PROVISIONING".to_owned();
        assert!(active_lane_authority(&registry, "PLANCK").is_err());
    }
}
