mod admission;
mod authority;
mod canonical_json;
mod crypto;
mod execution_plan;
mod git_objects;
mod nonce_ledger;
mod receipts;
mod worker;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::env;
use std::fs::{self};
use std::os::unix::fs::{MetadataExt, PermissionsExt};
use std::path::{Path, PathBuf};

use admission::replay_exact_admission;
use authority::{
    active_lane_authority, verify_human_authorization, verify_registry_root,
    HumanAuthorizationReceipt,
};
use canonical_json::{canonical_bytes, parse_canonical};
use crypto::load_external_root;
use execution_plan::bind_execution_plan;
use git_objects::{inspect_candidate, read_candidate_blob};
use nonce_ledger::consume_nonce;
use receipts::{ObservedExecutionBinding, ReceiptStore, TerminalReceipt};
use worker::{materialize_entrypoint, run_worker, WorkerSpec};

const LAUNCHER_PATH: &str = "/usr/local/libexec/htt-auth-launcher";
const ROOT_PUBLIC_KEY: &str = "/etc/htt/trust/root_authority_ed25519.pub";
const ROOT_FINGERPRINT: &str = "/etc/htt/trust/root_authority_ed25519.pub.sha256";
const ROOT_REGISTRY_SIGNATURE: &str = "/etc/htt/trust/human_authority_registry.root-signature.json";
const NONCE_STORE: &str = "/var/lib/htt-auth/nonces";
const RUN_STORE: &str = "/var/lib/htt-auth/runs";
const CANDIDATE_REPOSITORY: &str = "/srv/htt/candidate.git";
const AUTHORITY_REGISTRY_BLOB: &str =
    "docs/research_program/post_pr275/human_authority_registry.json";

#[derive(Clone)]
struct TransactionPaths {
    launcher_path: PathBuf,
    root_public_key: PathBuf,
    root_fingerprint: PathBuf,
    root_registry_signature: PathBuf,
    nonce_store: PathBuf,
    run_store: PathBuf,
    candidate_repository: PathBuf,
}

impl TransactionPaths {
    fn production() -> Self {
        Self {
            launcher_path: PathBuf::from(LAUNCHER_PATH),
            root_public_key: PathBuf::from(ROOT_PUBLIC_KEY),
            root_fingerprint: PathBuf::from(ROOT_FINGERPRINT),
            root_registry_signature: PathBuf::from(ROOT_REGISTRY_SIGNATURE),
            nonce_store: PathBuf::from(NONCE_STORE),
            run_store: PathBuf::from(RUN_STORE),
            candidate_repository: PathBuf::from(CANDIDATE_REPOSITORY),
        }
    }

    #[cfg(test)]
    fn synthetic(root: &Path) -> Self {
        Self {
            launcher_path: root.join("not-installed-launcher"),
            root_public_key: root.join("trust/root.pub"),
            root_fingerprint: root.join("trust/root.pub.sha256"),
            root_registry_signature: root.join("trust/registry.signature.json"),
            nonce_store: root.join("nonces"),
            run_store: root.join("runs"),
            candidate_repository: root.join("candidate"),
        }
    }
}

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct TransactionRequest {
    schema: String,
    artifact_mode: String,
    run_id: String,
    lane_id: String,
    candidate_commit: String,
    candidate_tree: String,
    execution_plan_path: String,
}

fn valid_run_id(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 128
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
}

fn read_regular(path: &Path, label: &str, require_root: bool) -> Result<Vec<u8>, String> {
    let metadata =
        fs::symlink_metadata(path).map_err(|error| format!("cannot inspect {label}: {error}"))?;
    if !metadata.file_type().is_file() || metadata.file_type().is_symlink() {
        return Err(format!("{label} is not a regular nonsymlink file"));
    }
    if require_root && (metadata.uid() != 0 || metadata.mode() & 0o022 != 0) {
        return Err(format!("{label} is not root-owned and non-writable"));
    }
    fs::read(path).map_err(|error| format!("cannot read {label}: {error}"))
}

fn sha256_file(path: &Path) -> Result<String, String> {
    let raw = fs::read(path).map_err(|error| format!("cannot hash launcher: {error}"))?;
    Ok(format!("sha256:{}", hex::encode(Sha256::digest(raw))))
}

fn require_installed_launcher(paths: &TransactionPaths) -> Result<String, String> {
    if unsafe { libc::geteuid() } != 0 {
        return Err("production launcher requires effective UID 0".to_owned());
    }
    let current = fs::canonicalize(env::current_exe().map_err(|error| error.to_string())?)
        .map_err(|error| format!("cannot resolve running launcher: {error}"))?;
    if current != paths.launcher_path {
        return Err("binary is not running from the compiled production launcher path".to_owned());
    }
    let metadata = fs::symlink_metadata(&current)
        .map_err(|error| format!("cannot inspect installed launcher: {error}"))?;
    if !metadata.file_type().is_file()
        || metadata.file_type().is_symlink()
        || metadata.uid() != 0
        || metadata.mode() & 0o022 != 0
    {
        return Err("installed launcher ownership or mode is unsafe".to_owned());
    }
    sha256_file(&current)
}

fn now_utc() -> Result<String, String> {
    let seconds = unsafe { libc::time(std::ptr::null_mut()) };
    if seconds < 0 {
        return Err("system clock is unavailable".to_owned());
    }
    let mut output: libc::tm = unsafe { std::mem::zeroed() };
    if unsafe { libc::gmtime_r(&seconds, &mut output) }.is_null() {
        return Err("UTC clock conversion failed".to_owned());
    }
    Ok(format!(
        "{:04}-{:02}-{:02}T{:02}:{:02}:{:02}Z",
        output.tm_year + 1900,
        output.tm_mon + 1,
        output.tm_mday,
        output.tm_hour,
        output.tm_min,
        output.tm_sec
    ))
}

fn ensure_directory(path: &Path, mode: u32, require_root: bool) -> Result<(), String> {
    if !path.exists() {
        fs::create_dir(path).map_err(|error| format!("directory creation failed: {error}"))?;
        fs::set_permissions(path, fs::Permissions::from_mode(mode))
            .map_err(|error| format!("directory mode failed: {error}"))?;
    }
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("directory inspection failed: {error}"))?;
    if !metadata.file_type().is_dir() || metadata.file_type().is_symlink() {
        return Err("transaction path is not a nonsymlink directory".to_owned());
    }
    if require_root && (metadata.uid() != 0 || metadata.mode() & 0o777 != mode) {
        return Err(format!(
            "production directory is not root-owned mode {mode:o}"
        ));
    }
    Ok(())
}

fn c_path(path: &Path) -> Result<std::ffi::CString, String> {
    use std::os::unix::ffi::OsStrExt;
    std::ffi::CString::new(path.as_os_str().as_bytes())
        .map_err(|_| "filesystem path contains NUL".to_owned())
}

fn prepare_transaction_directories(
    run_dir: &Path,
    worker_uid: u32,
    worker_gid: u32,
    require_root: bool,
) -> Result<(PathBuf, PathBuf, PathBuf), String> {
    ensure_directory(run_dir, 0o711, require_root)?;
    let receipts = run_dir.join("receipts");
    ensure_directory(&receipts, 0o700, require_root)?;
    let output = run_dir.join("output");
    ensure_directory(&output, 0o700, false)?;
    let candidate = run_dir.join("candidate");
    ensure_directory(&candidate, if require_root { 0o550 } else { 0o700 }, false)?;
    if require_root {
        let result = unsafe { libc::chown(c_path(&output)?.as_ptr(), worker_uid, worker_gid) };
        if result != 0 {
            return Err(format!(
                "output root ownership failed: {}",
                std::io::Error::last_os_error()
            ));
        }
        if unsafe { libc::chown(c_path(&candidate)?.as_ptr(), 0, worker_gid) } != 0 {
            return Err(format!(
                "candidate staging ownership failed: {}",
                std::io::Error::last_os_error()
            ));
        }
    }
    Ok((receipts, output, candidate))
}

#[allow(clippy::too_many_arguments)]
fn execute_transaction(
    paths: &TransactionPaths,
    run_id: &str,
    root_key: &[u8; 32],
    launcher_sha256: &str,
    evaluated_at_utc: &str,
    require_root: bool,
) -> Result<TerminalReceipt, String> {
    if !valid_run_id(run_id) {
        return Err("run_id is not canonical".to_owned());
    }
    ensure_directory(&paths.run_store, 0o711, require_root)?;
    ensure_directory(&paths.nonce_store, 0o700, require_root)?;
    let run_dir = paths.run_store.join(run_id);
    ensure_directory(&run_dir, 0o711, require_root)?;
    let request_raw = read_regular(
        &run_dir.join("request.json"),
        "transaction request",
        require_root,
    )?;
    let request: TransactionRequest = parse_canonical(&request_raw, "transaction request")?;
    let expected_mode = if require_root {
        "production"
    } else {
        "synthetic_fixture"
    };
    if request.schema != "common.observed_execution_request.v1"
        || request.run_id != run_id
        || request.artifact_mode != expected_mode
    {
        return Err("transaction request mode or identity drifted".to_owned());
    }
    inspect_candidate(
        &paths.candidate_repository,
        &request.candidate_commit,
        &request.candidate_tree,
    )?;
    let registry_raw = read_candidate_blob(
        &paths.candidate_repository,
        &request.candidate_commit,
        AUTHORITY_REGISTRY_BLOB,
    )?;
    let root_signature = read_regular(
        &paths.root_registry_signature,
        "external registry root signature",
        require_root,
    )?;
    let (_, registry) = verify_registry_root(
        &registry_raw,
        &root_signature,
        root_key,
        &request.candidate_commit,
        &request.candidate_tree,
    )?;
    let authorization_raw = read_regular(
        &run_dir.join("authorization.json"),
        "human authorization receipt",
        require_root,
    )?;
    let untrusted: HumanAuthorizationReceipt =
        parse_canonical(&authorization_raw, "human authorization receipt")?;
    if untrusted.lane_id != request.lane_id {
        return Err("request lane does not equal signed authorization lane".to_owned());
    }
    let authority = active_lane_authority(&registry, &request.lane_id)?;
    let authorization = verify_human_authorization(
        &authorization_raw,
        &authority,
        &request.candidate_commit,
        &request.candidate_tree,
        evaluated_at_utc,
    )?;
    let lane_registry = read_candidate_blob(
        &paths.candidate_repository,
        &request.candidate_commit,
        "docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json",
    )?;
    let admission_raw = read_regular(
        &run_dir.join("admission.json"),
        "complete admission decision",
        require_root,
    )?;
    let replayed = replay_exact_admission(&lane_registry, &admission_raw, &authorization)?;
    if replayed.lane_id != request.lane_id
        || replayed.analysis_plan_id != authorization.analysis_plan_id
        || replayed.required_human_gate_id != authorization.required_human_gate_id
        || replayed.record_ids != authorization.exact_admission_record_ids
        || replayed.bundle_id != authorization.lane_admission_bundle_id
    {
        return Err("replayed admission does not equal signed authorization".to_owned());
    }
    let plan_raw = read_candidate_blob(
        &paths.candidate_repository,
        &request.candidate_commit,
        &request.execution_plan_path,
    )?;
    let plan = bind_execution_plan(
        &paths.candidate_repository,
        &request.candidate_commit,
        &plan_raw,
        &authorization,
    )?;
    let (receipt_root, output_root, candidate_root) =
        prepare_transaction_directories(&run_dir, plan.worker_uid, plan.worker_gid, require_root)?;
    let store = ReceiptStore::acquire(&receipt_root, require_root)?;
    let binding = ObservedExecutionBinding::build(
        &request.artifact_mode,
        run_id,
        &request.candidate_commit,
        &request.candidate_tree,
        &authorization,
        &plan,
        launcher_sha256,
        &output_root,
    )?;
    store.write_binding(&binding)?;
    let entrypoint = materialize_entrypoint(&candidate_root, &plan.worker_entrypoint)?;
    if require_root {
        if unsafe { libc::chown(c_path(&entrypoint)?.as_ptr(), 0, plan.worker_gid) } != 0 {
            return Err(format!(
                "worker material ownership failed: {}",
                std::io::Error::last_os_error()
            ));
        }
    }
    let nonce_receipt = consume_nonce(
        &paths.nonce_store,
        &request.artifact_mode,
        &authorization.authorization_id,
        run_id,
        &authorization.nonce,
        evaluated_at_utc,
        require_root,
    )?;
    store.write_nonce(&nonce_receipt)?;
    let (start, token) = store.write_start(
        &request.artifact_mode,
        &binding.binding_id,
        evaluated_at_utc,
    )?;
    let worker_spec = WorkerSpec {
        artifact_mode: request.artifact_mode.clone(),
        runtime_executable: plan.runtime_executable,
        runtime_arguments: plan.runtime_arguments,
        entrypoint,
        candidate_root,
        output_root: output_root.clone(),
        environment: {
            let mut environment = plan.environment;
            environment.insert(
                "HOME".to_owned(),
                output_root.to_string_lossy().into_owned(),
            );
            environment
        },
        worker_uid: require_root.then_some(plan.worker_uid),
        worker_gid: require_root.then_some(plan.worker_gid),
        timeout: std::time::Duration::from_secs(plan.timeout_seconds),
    };
    let outcome = match run_worker(&token, &worker_spec) {
        Ok(value) => value,
        Err(error) => worker::WorkerOutcome {
            terminal: "ERROR".to_owned(),
            exit_code: Some(126),
            signal: None,
            timeout: false,
            stdout_sha256: format!("sha256:{}", hex::encode(Sha256::digest([]))),
            stderr_sha256: format!("sha256:{}", hex::encode(Sha256::digest(error.as_bytes()))),
        },
    };
    let observed_bytes_opened = output_root.join("observed-bytes-opened.marker").is_file();
    let terminal = TerminalReceipt::build(
        &request.artifact_mode,
        token.binding_id(),
        &outcome.terminal,
        outcome.exit_code,
        observed_bytes_opened,
        BTreeMap::new(),
        &outcome.stdout_sha256,
        &outcome.stderr_sha256,
        &start.started_at_utc,
        evaluated_at_utc,
        outcome.signal,
        outcome.timeout,
    )?;
    store.write_terminal(&terminal)?;
    Ok(terminal)
}

fn contract() -> serde_json::Value {
    serde_json::json!({
        "schema": "htt.auth_launcher_contract.v1",
        "launcher_path": LAUNCHER_PATH,
        "root_public_key": ROOT_PUBLIC_KEY,
        "root_fingerprint": ROOT_FINGERPRINT,
        "root_registry_signature": ROOT_REGISTRY_SIGNATURE,
        "nonce_store": NONCE_STORE,
        "run_store": RUN_STORE,
        "candidate_repository": CANDIDATE_REPOSITORY,
        "production_path_overrides_absent": true,
        "production_launcher_installed": false,
        "active_authorities": 0,
        "real_signature_present": false,
        "production_nonce_consumed": false,
        "observed_data_executed": false,
        "ready_state_emitted": false,
    })
}

fn run() -> Result<(), String> {
    let args = env::args().skip(1).collect::<Vec<_>>();
    match args.as_slice() {
        [flag] if flag == "--contract" => {
            println!(
                "{}",
                String::from_utf8(canonical_bytes(&contract())?).expect("contract is ASCII")
            );
            Ok(())
        }
        [flag, run_id] if flag == "--execute" => {
            let paths = TransactionPaths::production();
            let launcher_hash = require_installed_launcher(&paths)?;
            let root_key = load_external_root(&paths.root_public_key, &paths.root_fingerprint)?;
            let terminal =
                execute_transaction(&paths, run_id, &root_key, &launcher_hash, &now_utc()?, true)?;
            println!(
                "{}",
                String::from_utf8(canonical_bytes(&terminal)?).expect("terminal is ASCII")
            );
            Ok(())
        }
        _ => Err(
            "usage: htt-auth-launcher --contract | --execute RUN_ID; path overrides are forbidden"
                .to_owned(),
        ),
    }
}

fn main() {
    if let Err(error) = run() {
        eprintln!("htt-auth-launcher: {error}");
        std::process::exit(78);
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use base64::engine::general_purpose::STANDARD;
    use base64::Engine as _;
    use ed25519_dalek::{Signer, SigningKey};
    use serde_json::{json, Map, Value};
    use std::process::Command;

    use crate::authority::RootSignaturePayload;
    use crate::canonical_json::{content_id, sha256_identity};
    use crate::crypto::key_id;

    #[test]
    fn production_paths_are_compiled_and_request_has_no_path_override_fields() {
        let paths = TransactionPaths::production();
        assert_eq!(paths.launcher_path, Path::new(LAUNCHER_PATH));
        assert_eq!(paths.nonce_store, Path::new(NONCE_STORE));
        let request = TransactionRequest {
            schema: "common.observed_execution_request.v1".to_owned(),
            artifact_mode: "synthetic_fixture".to_owned(),
            run_id: "fixture".to_owned(),
            lane_id: "PLANCK".to_owned(),
            candidate_commit: "a".repeat(40),
            candidate_tree: "b".repeat(40),
            execution_plan_path: "docs/plan.json".to_owned(),
        };
        let value = serde_json::to_value(request).unwrap();
        for forbidden in [
            "root_key",
            "root_fingerprint",
            "nonce_store",
            "run_store",
            "candidate_repository",
            "output_root",
        ] {
            assert!(value.get(forbidden).is_none());
        }
    }

    #[test]
    fn synthetic_path_constructor_is_test_only_and_disjoint_from_production() {
        let temporary = tempfile::tempdir().unwrap();
        let paths = TransactionPaths::synthetic(temporary.path());
        assert!(paths.run_store.starts_with(temporary.path()));
        assert_ne!(paths.run_store, Path::new(RUN_STORE));
    }

    fn write_canonical(path: &Path, value: &impl Serialize) {
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).unwrap();
        }
        fs::write(path, canonical_bytes(value).unwrap()).unwrap();
    }

    fn git(repo: &Path, args: &[&str]) -> String {
        let output = Command::new("/usr/bin/git")
            .env_clear()
            .env("HOME", "/nonexistent")
            .env("LC_ALL", "C")
            .env("LANG", "C")
            .arg("-C")
            .arg(repo)
            .args(args)
            .output()
            .unwrap();
        assert!(
            output.status.success(),
            "git failed: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        String::from_utf8(output.stdout).unwrap().trim().to_owned()
    }

    fn synthetic_record() -> Value {
        let sha = |character: char| format!("sha256:{}", character.to_string().repeat(64));
        let profile_id = sha('9');
        let mut row = Map::new();
        for (key, value) in [
            ("schema", json!("common.data_identity_record.v2")),
            ("record_id", json!("")),
            ("inspection_receipt_id", json!("")),
            ("lane_id", json!("PLANCK")),
            ("product_id", json!("PLANCK_SYNTHETIC")),
            ("component_id", json!("synthetic_map")),
            ("component_ordinal", json!(0)),
            ("source_locator_kind", json!("absolute_local_root")),
            ("source_locator_identity", json!("docs:synthetic")),
            ("release_name", json!("SYNTHETIC")),
            ("release_version", json!("v1")),
            ("release_identity", json!("docs:synthetic-v1")),
            ("license_identity", json!("spdx:CC0-1.0")),
            ("regular_file_status", json!("REGULAR_FILE")),
            ("symlink_status", json!("NOT_SYMLINK")),
            ("byte_size", json!(4)),
            ("content_sha256", json!(sha('1'))),
            ("component_inventory_id", json!(sha('2'))),
            ("completeness_status", json!("COMPLETE")),
            ("units_contract_id", json!("units:synthetic")),
            ("coordinate_frame_id", json!("frame:synthetic")),
            ("sign_orientation_convention_id", json!("sign:synthetic")),
            ("directional_convention_id", json!("direction:synthetic")),
            ("harmonic_convention_id", json!("harmonic:synthetic")),
            ("mask_id", json!("mask:synthetic")),
            ("selection_id", json!("selection:synthetic")),
            ("sky_support_id", json!("sky:synthetic")),
            ("covariance_id", json!("covariance:synthetic")),
            ("covariance_status", json!("REGISTERED")),
            ("null_ensemble_id", json!("null:synthetic")),
            ("null_ensemble_status", json!("REGISTERED")),
            ("transfer_source", json!("none")),
            ("transfer_function_spec_id", json!("none")),
            ("transfer_provenance_status", json!("NOT_APPLICABLE")),
            ("sky_support_status", json!("BOUND")),
            ("license_status", json!("BOUND")),
            ("native_identity_profile_id", json!(profile_id.clone())),
            ("native_identity_profile", json!({"profile_id": profile_id})),
            ("acquisition_status", json!("COMPLETE")),
            ("inspected_at_utc", json!("2026-08-22T00:00:00Z")),
        ] {
            row.insert(key.to_owned(), value);
        }
        let mut stable = row.clone();
        stable.remove("record_id");
        stable.remove("inspection_receipt_id");
        stable.remove("inspected_at_utc");
        row.insert(
            "record_id".to_owned(),
            Value::String(content_id(&Value::Object(stable)).unwrap()),
        );
        let mut inspection = row.clone();
        inspection.remove("inspection_receipt_id");
        row.insert(
            "inspection_receipt_id".to_owned(),
            Value::String(content_id(&Value::Object(inspection)).unwrap()),
        );
        Value::Object(row)
    }

    #[test]
    fn complete_synthetic_transaction_rehearses_root_auth_nonce_start_worker_terminal() {
        let temporary = tempfile::tempdir().unwrap();
        let paths = TransactionPaths::synthetic(temporary.path());
        fs::create_dir_all(&paths.candidate_repository).unwrap();
        fs::create_dir_all(paths.root_registry_signature.parent().unwrap()).unwrap();
        fs::create_dir_all(&paths.nonce_store).unwrap();
        fs::create_dir_all(&paths.run_store).unwrap();
        Command::new("/usr/bin/git")
            .args(["init", "-q"])
            .arg(&paths.candidate_repository)
            .status()
            .unwrap();

        let root_signing = SigningKey::from_bytes(&[31_u8; 32]);
        let human_signing = SigningKey::from_bytes(&[47_u8; 32]);
        let authority_registry = json!({
            "schema": "common.human_authority_registry.v1",
            "lane_order": ["PLANCK"],
            "authorities": {
                "PLANCK": {
                    "status": "ACTIVE",
                    "key_id": key_id(&human_signing.verifying_key().to_bytes()),
                    "public_key_base64": STANDARD.encode(human_signing.verifying_key().to_bytes()),
                    "gate_id": "H-PLANCK",
                    "scope": "admitted_planck_observed_execution"
                }
            }
        });
        let lane_registry = json!({
            "schema": "common.data_identity_lane_registry.v2",
            "registry_id": "PR289-LANE-REGISTRY-V2",
            "lane_order": ["PLANCK"],
            "universal_semantic_fields": [],
            "lanes": [{
                "lane_id": "PLANCK",
                "product_id": "PLANCK_SYNTHETIC",
                "required_component_ids": ["synthetic_map"],
                "component_cardinality": {"synthetic_map": 1},
                "native_identity_schema": "common.synthetic_native_identity.v1",
                "required_human_gate_id": "H-PLANCK",
                "analysis_plan_id": "plan:synthetic",
                "allowed_transfer_sources": ["none"],
                "name_only_forbidden": true
            }]
        });
        let support = [
            (
                "docs/model.json",
                json!({"schema":"synthetic.model.v1","value":1}),
            ),
            (
                "docs/runtime.json",
                json!({"schema":"synthetic.runtime.v1","value":2}),
            ),
            (
                "docs/rank.json",
                json!({"schema":"synthetic.rank.v1","value":3}),
            ),
            (
                "docs/normalization.json",
                json!({"schema":"synthetic.normalization.v1","value":4}),
            ),
        ];
        let worker_raw = b"#!/bin/dash\nexit 0\n";
        let runtime_raw = fs::read("/bin/dash").unwrap();
        let plan = json!({
            "schema": "common.observed_execution_plan.v1",
            "artifact_mode": "synthetic_fixture",
            "lane_id": "PLANCK",
            "model_contract_path": support[0].0,
            "runtime_environment_receipt_path": support[1].0,
            "computed_response_rank_receipt_path": support[2].0,
            "normalization_evidence_path": support[3].0,
            "worker_entrypoint_path": "scripts/synthetic_worker.sh",
            "worker_entrypoint_sha256": sha256_identity(worker_raw),
            "runtime_executable": "/bin/dash",
            "runtime_executable_sha256": sha256_identity(&runtime_raw),
            "runtime_arguments": [],
            "environment": {"LANG":"C","LC_ALL":"C","PATH":"/usr/bin:/bin"},
            "worker_uid": 65534,
            "worker_gid": 65534,
            "timeout_seconds": 2
        });
        let candidate = &paths.candidate_repository;
        write_canonical(
            &candidate.join(AUTHORITY_REGISTRY_BLOB),
            &authority_registry,
        );
        write_canonical(
            &candidate
                .join("docs/research_program/post_pr275/data_registry_v2/LANE_REGISTRY_V2.json"),
            &lane_registry,
        );
        for (relative, value) in &support {
            write_canonical(&candidate.join(relative), value);
        }
        write_canonical(&candidate.join("docs/plan.json"), &plan);
        fs::create_dir_all(candidate.join("scripts")).unwrap();
        fs::write(candidate.join("scripts/synthetic_worker.sh"), worker_raw).unwrap();
        git(candidate, &["add", "."]);
        git(
            candidate,
            &[
                "-c",
                "user.name=HTT Synthetic",
                "-c",
                "user.email=synthetic@example.invalid",
                "commit",
                "-q",
                "-m",
                "synthetic fixture",
            ],
        );
        let commit = git(candidate, &["rev-parse", "HEAD"]);
        let tree = git(candidate, &["rev-parse", "HEAD^{tree}"]);

        let registry_raw = fs::read(candidate.join(AUTHORITY_REGISTRY_BLOB)).unwrap();
        let root_payload = RootSignaturePayload {
            schema: "common.human_authority_registry_root_signature.v1".to_owned(),
            registry_blob_sha256: sha256_identity(&registry_raw),
            candidate_commit: commit.clone(),
            candidate_tree: tree.clone(),
            authorization_domain: "lane_data_execution".to_owned(),
            registry_version: 1,
            issued_at_utc: "2026-08-22T00:00:00Z".to_owned(),
            root_authority_key_id: key_id(&root_signing.verifying_key().to_bytes()),
        };
        let root_signature = STANDARD.encode(
            root_signing
                .sign(&canonical_bytes(&root_payload).unwrap())
                .to_bytes(),
        );
        write_canonical(
            &paths.root_registry_signature,
            &json!({
                "schema":"common.human_authority_registry_root_signature_envelope.v1",
                "payload": root_payload,
                "registry_signature_ed25519": root_signature
            }),
        );

        let record = synthetic_record();
        let record_id = record["record_id"].as_str().unwrap().to_owned();
        let inventory_id = record["component_inventory_id"].as_str().unwrap();
        let bundle_id = content_id(&json!({
            "lane_id":"PLANCK",
            "product_id":"PLANCK_SYNTHETIC",
            "component_inventory_id":inventory_id,
            "record_ids":[record_id]
        }))
        .unwrap();
        let admission = json!({
            "lane_admission_bundle_id":bundle_id,
            "lane_id":"PLANCK",
            "product_id":"PLANCK_SYNTHETIC",
            "reasons":[],
            "records":[record],
            "status":"ADMITTED_IDENTITY_ONLY"
        });
        let mut authorization = HumanAuthorizationReceipt {
            authorization_id: String::new(),
            schema: "common.human_execution_authorization_receipt.v3".to_owned(),
            lane_id: "PLANCK".to_owned(),
            exact_admission_record_ids: vec![admission["records"][0]["record_id"]
                .as_str()
                .unwrap()
                .to_owned()],
            lane_admission_bundle_id: admission["lane_admission_bundle_id"]
                .as_str()
                .unwrap()
                .to_owned(),
            analysis_plan_id: "plan:synthetic".to_owned(),
            required_human_gate_id: "H-PLANCK".to_owned(),
            authorized_scope: "admitted_planck_observed_execution".to_owned(),
            authorization_domain: "lane_data_execution".to_owned(),
            model_contract_content_id: content_id(&support[0].1).unwrap(),
            runtime_environment_receipt_id: content_id(&support[1].1).unwrap(),
            computed_response_rank_receipt_id: content_id(&support[2].1).unwrap(),
            normalization_evidence_id: content_id(&support[3].1).unwrap(),
            execution_plan_content_id: content_id(&plan).unwrap(),
            candidate_commit: commit.clone(),
            candidate_tree: tree.clone(),
            issued_at_utc: "2026-08-22T00:00:00Z".to_owned(),
            expires_at_utc: "2026-08-22T00:10:00Z".to_owned(),
            nonce: format!("nonce:v1:{}", "a".repeat(64)),
            signer_key_id: key_id(&human_signing.verifying_key().to_bytes()),
            authorization_signature_ed25519: String::new(),
        };
        authorization.authorization_id = content_id(&authorization.unsigned_value()).unwrap();
        authorization.authorization_signature_ed25519 = STANDARD.encode(
            human_signing
                .sign(&canonical_bytes(&authorization.signed_value()).unwrap())
                .to_bytes(),
        );
        let run_id = "synthetic-e2e";
        let run_dir = paths.run_store.join(run_id);
        fs::create_dir(&run_dir).unwrap();
        write_canonical(&run_dir.join("authorization.json"), &authorization);
        write_canonical(&run_dir.join("admission.json"), &admission);
        write_canonical(
            &run_dir.join("request.json"),
            &TransactionRequest {
                schema: "common.observed_execution_request.v1".to_owned(),
                artifact_mode: "synthetic_fixture".to_owned(),
                run_id: run_id.to_owned(),
                lane_id: "PLANCK".to_owned(),
                candidate_commit: commit,
                candidate_tree: tree,
                execution_plan_path: "docs/plan.json".to_owned(),
            },
        );
        let terminal = execute_transaction(
            &paths,
            run_id,
            &root_signing.verifying_key().to_bytes(),
            &sha256_identity(b"synthetic-launcher"),
            "2026-08-22T00:05:00Z",
            false,
        )
        .unwrap();
        assert_eq!(terminal.terminal, "SUCCESS");
        assert_eq!(terminal.artifact_mode, "synthetic_fixture");
        assert!(!terminal.observed_bytes_opened);
        for receipt in ["binding.json", "nonce.json", "start.json", "terminal.json"] {
            assert!(run_dir.join("receipts").join(receipt).is_file());
        }
        assert!(execute_transaction(
            &paths,
            run_id,
            &root_signing.verifying_key().to_bytes(),
            &sha256_identity(b"synthetic-launcher"),
            "2026-08-22T00:05:01Z",
            false,
        )
        .is_err());
    }
}
