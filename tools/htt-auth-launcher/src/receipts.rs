use serde::Serialize;
use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::Write;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Path, PathBuf};

use crate::authority::HumanAuthorizationReceipt;
use crate::canonical_json::{canonical_bytes, content_id, require_git_object, require_sha256};
use crate::execution_plan::BoundExecutionPlan;

#[derive(Debug, Clone, Serialize)]
pub(crate) struct ObservedExecutionBinding {
    pub(crate) schema: String,
    pub(crate) artifact_mode: String,
    pub(crate) run_id: String,
    pub(crate) lane_id: String,
    pub(crate) candidate_commit: String,
    pub(crate) candidate_tree: String,
    pub(crate) exact_admission_record_ids: Vec<String>,
    pub(crate) lane_admission_bundle_id: String,
    pub(crate) authorization_id: String,
    pub(crate) model_contract_content_id: String,
    pub(crate) runtime_environment_receipt_id: String,
    pub(crate) computed_response_rank_receipt_id: String,
    pub(crate) normalization_evidence_id: String,
    pub(crate) execution_plan_content_id: String,
    pub(crate) launcher_binary_sha256: String,
    pub(crate) output_root: String,
    pub(crate) binding_id: String,
}

impl ObservedExecutionBinding {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn build(
        artifact_mode: &str,
        run_id: &str,
        candidate_commit: &str,
        candidate_tree: &str,
        authorization: &HumanAuthorizationReceipt,
        plan: &BoundExecutionPlan,
        launcher_binary_sha256: &str,
        output_root: &Path,
    ) -> Result<Self, String> {
        if !matches!(artifact_mode, "production" | "synthetic_fixture")
            || plan.artifact_mode != artifact_mode
            || plan.lane_id != authorization.lane_id
        {
            return Err("execution binding artifact mode or lane drifted".to_owned());
        }
        require_git_object(candidate_commit, "candidate_commit")?;
        require_git_object(candidate_tree, "candidate_tree")?;
        require_sha256(launcher_binary_sha256, "launcher_binary_sha256")?;
        let output = output_root
            .to_str()
            .filter(|value| output_root.is_absolute() && !value.contains("..") && value.is_ascii())
            .ok_or_else(|| "output_root is not a canonical absolute path".to_owned())?;
        let unsigned = serde_json::json!({
            "artifact_mode": artifact_mode,
            "run_id": run_id,
            "lane_id": authorization.lane_id,
            "candidate_commit": candidate_commit,
            "candidate_tree": candidate_tree,
            "exact_admission_record_ids": authorization.exact_admission_record_ids,
            "lane_admission_bundle_id": authorization.lane_admission_bundle_id,
            "authorization_id": authorization.authorization_id,
            "model_contract_content_id": authorization.model_contract_content_id,
            "runtime_environment_receipt_id": authorization.runtime_environment_receipt_id,
            "computed_response_rank_receipt_id": authorization.computed_response_rank_receipt_id,
            "normalization_evidence_id": authorization.normalization_evidence_id,
            "execution_plan_content_id": plan.plan_id,
            "launcher_binary_sha256": launcher_binary_sha256,
            "output_root": output,
        });
        Ok(Self {
            schema: "common.observed_execution_binding.v1".to_owned(),
            artifact_mode: artifact_mode.to_owned(),
            run_id: run_id.to_owned(),
            lane_id: authorization.lane_id.clone(),
            candidate_commit: candidate_commit.to_owned(),
            candidate_tree: candidate_tree.to_owned(),
            exact_admission_record_ids: authorization.exact_admission_record_ids.clone(),
            lane_admission_bundle_id: authorization.lane_admission_bundle_id.clone(),
            authorization_id: authorization.authorization_id.clone(),
            model_contract_content_id: authorization.model_contract_content_id.clone(),
            runtime_environment_receipt_id: authorization.runtime_environment_receipt_id.clone(),
            computed_response_rank_receipt_id: authorization
                .computed_response_rank_receipt_id
                .clone(),
            normalization_evidence_id: authorization.normalization_evidence_id.clone(),
            execution_plan_content_id: plan.plan_id.clone(),
            launcher_binary_sha256: launcher_binary_sha256.to_owned(),
            output_root: output.to_owned(),
            binding_id: content_id(&unsigned)?,
        })
    }
}

#[derive(Debug, Clone, Serialize)]
pub(crate) struct StartReceipt {
    pub(crate) schema: String,
    pub(crate) artifact_mode: String,
    pub(crate) binding_id: String,
    pub(crate) started_at_utc: String,
    pub(crate) observed_bytes_opened: bool,
    pub(crate) receipt_id: String,
}

#[derive(Debug, Clone, Serialize)]
pub(crate) struct TerminalReceipt {
    pub(crate) schema: String,
    pub(crate) artifact_mode: String,
    pub(crate) binding_id: String,
    pub(crate) terminal: String,
    pub(crate) exit_code: Option<i32>,
    pub(crate) observed_bytes_opened: bool,
    pub(crate) output_artifact_hashes: BTreeMap<String, String>,
    pub(crate) stdout_sha256: String,
    pub(crate) stderr_sha256: String,
    pub(crate) started_at_utc: String,
    pub(crate) ended_at_utc: String,
    pub(crate) signal: Option<i32>,
    pub(crate) timeout: bool,
    pub(crate) receipt_id: String,
}

impl TerminalReceipt {
    #[allow(clippy::too_many_arguments)]
    pub(crate) fn build(
        artifact_mode: &str,
        binding_id: &str,
        terminal: &str,
        exit_code: Option<i32>,
        observed_bytes_opened: bool,
        output_artifact_hashes: BTreeMap<String, String>,
        stdout_sha256: &str,
        stderr_sha256: &str,
        started_at_utc: &str,
        ended_at_utc: &str,
        signal: Option<i32>,
        timeout: bool,
    ) -> Result<Self, String> {
        let consistent = match terminal {
            "SUCCESS" => exit_code == Some(0) && signal.is_none() && !timeout,
            "ERROR" => exit_code.is_some_and(|code| code != 0) && signal.is_none() && !timeout,
            "TIMEOUT" => exit_code.is_none() && signal.is_none() && timeout,
            "SIGNAL" => exit_code.is_none() && signal.is_some_and(|value| value > 0) && !timeout,
            _ => false,
        };
        if !consistent {
            return Err("terminal exit semantics are inconsistent".to_owned());
        }
        require_sha256(binding_id, "binding_id")?;
        require_sha256(stdout_sha256, "stdout_sha256")?;
        require_sha256(stderr_sha256, "stderr_sha256")?;
        for value in output_artifact_hashes.values() {
            require_sha256(value, "output artifact hash")?;
        }
        let unsigned = serde_json::json!({
            "artifact_mode": artifact_mode,
            "binding_id": binding_id,
            "terminal": terminal,
            "exit_code": exit_code,
            "observed_bytes_opened": observed_bytes_opened,
            "output_artifact_hashes": output_artifact_hashes,
            "stdout_sha256": stdout_sha256,
            "stderr_sha256": stderr_sha256,
            "started_at_utc": started_at_utc,
            "ended_at_utc": ended_at_utc,
            "signal": signal,
            "timeout": timeout,
        });
        Ok(Self {
            schema: "common.observed_run_terminal_receipt.v1".to_owned(),
            artifact_mode: artifact_mode.to_owned(),
            binding_id: binding_id.to_owned(),
            terminal: terminal.to_owned(),
            exit_code,
            observed_bytes_opened,
            output_artifact_hashes,
            stdout_sha256: stdout_sha256.to_owned(),
            stderr_sha256: stderr_sha256.to_owned(),
            started_at_utc: started_at_utc.to_owned(),
            ended_at_utc: ended_at_utc.to_owned(),
            signal,
            timeout,
            receipt_id: content_id(&unsigned)?,
        })
    }
}

pub(crate) struct StartReceiptToken {
    binding_id: String,
}

impl StartReceiptToken {
    pub(crate) fn binding_id(&self) -> &str {
        &self.binding_id
    }
}

pub(crate) struct ReceiptStore {
    root: PathBuf,
    lock_path: PathBuf,
    _lock: File,
}

fn ensure_directory(root: &Path, require_root: bool) -> Result<(), String> {
    let metadata = fs::symlink_metadata(root)
        .map_err(|error| format!("cannot inspect run directory: {error}"))?;
    if !metadata.file_type().is_dir() || metadata.file_type().is_symlink() {
        return Err("run store is not a nonsymlink directory".to_owned());
    }
    if require_root && (metadata.uid() != 0 || metadata.mode() & 0o077 != 0) {
        return Err("production run store is not root-owned mode 0700".to_owned());
    }
    Ok(())
}

fn exclusive_file(path: &Path) -> Result<File, String> {
    OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .custom_flags(libc::O_NOFOLLOW | libc::O_CLOEXEC)
        .open(path)
        .map_err(|error| format!("exclusive receipt creation failed: {error}"))
}

fn write_fsync(root: &Path, name: &str, payload: &impl Serialize) -> Result<(), String> {
    let path = root.join(name);
    let mut file = exclusive_file(&path)?;
    let mut bytes = canonical_bytes(payload)?;
    bytes.push(b'\n');
    file.write_all(&bytes)
        .map_err(|error| format!("receipt write failed: {error}"))?;
    file.sync_all()
        .map_err(|error| format!("receipt file fsync failed: {error}"))?;
    File::open(root)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| format!("receipt directory fsync failed: {error}"))
}

impl ReceiptStore {
    pub(crate) fn acquire(root: &Path, require_root: bool) -> Result<Self, String> {
        ensure_directory(root, require_root)?;
        let lock_path = root.join("transaction.lock");
        let lock = exclusive_file(&lock_path)
            .map_err(|error| format!("output-root lock unavailable: {error}"))?;
        lock.sync_all()
            .map_err(|error| format!("output-root lock fsync failed: {error}"))?;
        File::open(root)
            .and_then(|directory| directory.sync_all())
            .map_err(|error| format!("output-root lock directory fsync failed: {error}"))?;
        Ok(Self {
            root: root.to_owned(),
            lock_path,
            _lock: lock,
        })
    }

    pub(crate) fn write_start(
        &self,
        artifact_mode: &str,
        binding_id: &str,
        started_at_utc: &str,
    ) -> Result<(StartReceipt, StartReceiptToken), String> {
        let unsigned = serde_json::json!({
            "artifact_mode": artifact_mode,
            "binding_id": binding_id,
            "started_at_utc": started_at_utc,
            "observed_bytes_opened": false,
        });
        let receipt = StartReceipt {
            schema: "common.observed_run_start_receipt.v1".to_owned(),
            artifact_mode: artifact_mode.to_owned(),
            binding_id: binding_id.to_owned(),
            started_at_utc: started_at_utc.to_owned(),
            observed_bytes_opened: false,
            receipt_id: content_id(&unsigned)?,
        };
        write_fsync(&self.root, "start.json", &receipt)?;
        Ok((
            receipt,
            StartReceiptToken {
                binding_id: binding_id.to_owned(),
            },
        ))
    }

    pub(crate) fn write_binding(&self, binding: &ObservedExecutionBinding) -> Result<(), String> {
        write_fsync(&self.root, "binding.json", binding)
    }

    pub(crate) fn write_nonce(&self, receipt: &impl Serialize) -> Result<(), String> {
        write_fsync(&self.root, "nonce.json", receipt)
    }

    pub(crate) fn write_terminal(&self, receipt: &TerminalReceipt) -> Result<(), String> {
        write_fsync(&self.root, "terminal.json", receipt)
    }
}

impl Drop for ReceiptStore {
    fn drop(&mut self) {
        let _ = fs::remove_file(&self.lock_path);
        if let Ok(directory) = File::open(&self.root) {
            let _ = directory.sync_all();
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn start_must_exist_before_a_worker_token_and_terminal_is_at_most_once() {
        let temporary = tempdir().unwrap();
        let store = ReceiptStore::acquire(temporary.path(), false).unwrap();
        let binding = format!("sha256:{}", "a".repeat(64));
        let (_, token) = store
            .write_start("synthetic_fixture", &binding, "2026-08-22T00:00:00Z")
            .unwrap();
        assert_eq!(token.binding_id(), binding);
        assert!(temporary.path().join("start.json").is_file());
        let terminal = TerminalReceipt::build(
            "synthetic_fixture",
            &binding,
            "SUCCESS",
            Some(0),
            false,
            BTreeMap::new(),
            &format!("sha256:{}", "b".repeat(64)),
            &format!("sha256:{}", "c".repeat(64)),
            "2026-08-22T00:00:00Z",
            "2026-08-22T00:00:01Z",
            None,
            false,
        )
        .unwrap();
        store.write_terminal(&terminal).unwrap();
        assert!(store.write_terminal(&terminal).is_err());
    }

    #[test]
    fn concurrent_output_lock_is_refused() {
        let temporary = tempdir().unwrap();
        let first = ReceiptStore::acquire(temporary.path(), false).unwrap();
        assert!(ReceiptStore::acquire(temporary.path(), false).is_err());
        drop(first);
        assert!(ReceiptStore::acquire(temporary.path(), false).is_ok());
    }
}
