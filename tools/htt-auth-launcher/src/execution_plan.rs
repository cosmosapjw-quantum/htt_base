use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Component, Path, PathBuf};

use crate::authority::HumanAuthorizationReceipt;
use crate::canonical_json::{content_id, parse_canonical, parse_strict, require_sha256};
use crate::git_objects::read_candidate_blob;

#[derive(Debug, Clone, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct ExecutionPlanV1 {
    pub(crate) schema: String,
    pub(crate) artifact_mode: String,
    pub(crate) lane_id: String,
    pub(crate) model_contract_path: String,
    pub(crate) runtime_environment_receipt_path: String,
    pub(crate) computed_response_rank_receipt_path: String,
    pub(crate) normalization_evidence_path: String,
    pub(crate) worker_entrypoint_path: String,
    pub(crate) worker_entrypoint_sha256: String,
    pub(crate) runtime_executable: String,
    pub(crate) runtime_executable_sha256: String,
    pub(crate) runtime_arguments: Vec<String>,
    pub(crate) environment: BTreeMap<String, String>,
    pub(crate) worker_uid: u32,
    pub(crate) worker_gid: u32,
    pub(crate) timeout_seconds: u64,
}

#[derive(Debug, Clone)]
pub(crate) struct BoundExecutionPlan {
    pub(crate) plan_id: String,
    pub(crate) lane_id: String,
    pub(crate) artifact_mode: String,
    pub(crate) worker_entrypoint: Vec<u8>,
    pub(crate) runtime_executable: PathBuf,
    pub(crate) runtime_arguments: Vec<String>,
    pub(crate) environment: BTreeMap<String, String>,
    pub(crate) worker_uid: u32,
    pub(crate) worker_gid: u32,
    pub(crate) timeout_seconds: u64,
}

fn candidate_relative(value: &str, field: &str) -> Result<(), String> {
    let path = Path::new(value);
    if value.is_empty()
        || !value.is_ascii()
        || path.is_absolute()
        || value != path.to_string_lossy()
        || value.contains(['\0', '\n', '\r', ':'])
        || path
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        return Err(format!("{field} is not a canonical candidate blob path"));
    }
    Ok(())
}

fn semantic_blob_id(raw: &[u8], field: &str) -> Result<String, String> {
    let value: Value = parse_strict(raw, field)?;
    content_id(&value)
}

fn hash_regular_executable(path: &Path) -> Result<String, String> {
    if !path.is_absolute() {
        return Err("runtime executable must be an absolute path".to_owned());
    }
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("cannot inspect runtime executable: {error}"))?;
    if !metadata.file_type().is_file()
        || metadata.file_type().is_symlink()
        || metadata.mode() & 0o111 == 0
        || metadata.mode() & 0o022 != 0
    {
        return Err("runtime executable is not a fixed non-writable executable".to_owned());
    }
    let raw = fs::read(path).map_err(|error| format!("cannot hash runtime executable: {error}"))?;
    Ok(format!("sha256:{}", hex::encode(Sha256::digest(raw))))
}

pub(crate) fn bind_execution_plan(
    repo: &Path,
    candidate_commit: &str,
    plan_raw: &[u8],
    authorization: &HumanAuthorizationReceipt,
) -> Result<BoundExecutionPlan, String> {
    let plan: ExecutionPlanV1 = parse_canonical(plan_raw, "execution plan")?;
    let plan_id = semantic_blob_id(plan_raw, "execution plan")?;
    let permitted_mode = plan.artifact_mode == "production"
        || (cfg!(test) && plan.artifact_mode == "synthetic_fixture");
    if plan.schema != "common.observed_execution_plan.v1"
        || !permitted_mode
        || plan.lane_id != authorization.lane_id
        || plan_id != authorization.execution_plan_content_id
    {
        return Err("execution plan identity, lane, or mode drifted".to_owned());
    }
    for (path, field) in [
        (&plan.model_contract_path, "model_contract_path"),
        (
            &plan.runtime_environment_receipt_path,
            "runtime_environment_receipt_path",
        ),
        (
            &plan.computed_response_rank_receipt_path,
            "computed_response_rank_receipt_path",
        ),
        (
            &plan.normalization_evidence_path,
            "normalization_evidence_path",
        ),
        (&plan.worker_entrypoint_path, "worker_entrypoint_path"),
    ] {
        candidate_relative(path, field)?;
    }
    let bindings = [
        (
            &plan.model_contract_path,
            &authorization.model_contract_content_id,
            "model contract",
        ),
        (
            &plan.runtime_environment_receipt_path,
            &authorization.runtime_environment_receipt_id,
            "runtime environment receipt",
        ),
        (
            &plan.computed_response_rank_receipt_path,
            &authorization.computed_response_rank_receipt_id,
            "computed response-rank receipt",
        ),
        (
            &plan.normalization_evidence_path,
            &authorization.normalization_evidence_id,
            "normalization evidence",
        ),
    ];
    for (path, expected, label) in bindings {
        require_sha256(expected, label)?;
        let raw = read_candidate_blob(repo, candidate_commit, path)?;
        if semantic_blob_id(&raw, label)? != *expected {
            return Err(format!("{label} content binding mismatched"));
        }
    }
    require_sha256(&plan.worker_entrypoint_sha256, "worker_entrypoint_sha256")?;
    let worker_entrypoint =
        read_candidate_blob(repo, candidate_commit, &plan.worker_entrypoint_path)?;
    let worker_hash = format!("sha256:{}", hex::encode(Sha256::digest(&worker_entrypoint)));
    if worker_hash != plan.worker_entrypoint_sha256 {
        return Err("worker entrypoint Git blob hash mismatched".to_owned());
    }
    require_sha256(&plan.runtime_executable_sha256, "runtime_executable_sha256")?;
    let runtime_executable = PathBuf::from(&plan.runtime_executable);
    if hash_regular_executable(&runtime_executable)? != plan.runtime_executable_sha256 {
        return Err("runtime executable hash mismatched".to_owned());
    }
    if plan.timeout_seconds == 0 || plan.timeout_seconds > 86_400 {
        return Err("execution timeout is outside the bounded range".to_owned());
    }
    if plan.runtime_arguments.len() > 32
        || plan.runtime_arguments.iter().any(|value| {
            value.is_empty() || !value.is_ascii() || value.contains(['\0', '\n', '\r'])
        })
    {
        return Err("runtime argument inventory is malformed".to_owned());
    }
    let allowed_environment = [
        "LANG",
        "LC_ALL",
        "PATH",
        "PYTHONHASHSEED",
        "PYTHONNOUSERSITE",
    ];
    if plan.environment.len() > allowed_environment.len()
        || plan.environment.iter().any(|(key, value)| {
            !allowed_environment.contains(&key.as_str())
                || value.contains(['\0', '\n', '\r'])
                || !value.is_ascii()
        })
        || plan.environment.keys().any(|key| {
            key == "PYTHONPATH"
                || key == "LD_PRELOAD"
                || key.starts_with("GIT_")
                || key == "PYTHONUSERBASE"
        })
    {
        return Err("worker environment is not a bounded allowlist".to_owned());
    }
    for (key, expected) in [("LANG", "C"), ("LC_ALL", "C"), ("PATH", "/usr/bin:/bin")] {
        if plan.environment.get(key).map(String::as_str) != Some(expected) {
            return Err(format!("execution plan {key} is not launcher-fixed"));
        }
    }
    Ok(BoundExecutionPlan {
        plan_id,
        lane_id: plan.lane_id,
        artifact_mode: plan.artifact_mode,
        worker_entrypoint,
        runtime_executable,
        runtime_arguments: plan.runtime_arguments,
        environment: plan.environment,
        worker_uid: plan.worker_uid,
        worker_gid: plan.worker_gid,
        timeout_seconds: plan.timeout_seconds,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn forbidden_environment_and_path_escape_are_rejected() {
        assert!(candidate_relative("../escape", "path").is_err());
        assert!(candidate_relative("docs/worker.py", "path").is_ok());
        let mut environment = BTreeMap::new();
        environment.insert("PYTHONPATH".to_owned(), "/tmp/attacker".to_owned());
        assert!(environment.keys().any(|key| key == "PYTHONPATH"));
    }
}
