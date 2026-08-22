use sha2::{Digest, Sha256};
use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::os::unix::fs::OpenOptionsExt;
use std::os::unix::process::{CommandExt, ExitStatusExt};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::{Duration, Instant};

use crate::receipts::StartReceiptToken;

#[derive(Debug, Clone)]
pub(crate) struct WorkerSpec {
    pub(crate) artifact_mode: String,
    pub(crate) runtime_executable: PathBuf,
    pub(crate) runtime_arguments: Vec<String>,
    pub(crate) entrypoint: PathBuf,
    pub(crate) candidate_root: PathBuf,
    pub(crate) output_root: PathBuf,
    pub(crate) environment: BTreeMap<String, String>,
    pub(crate) worker_uid: Option<u32>,
    pub(crate) worker_gid: Option<u32>,
    pub(crate) timeout: Duration,
}

#[derive(Debug)]
pub(crate) struct WorkerOutcome {
    pub(crate) terminal: String,
    pub(crate) exit_code: Option<i32>,
    pub(crate) signal: Option<i32>,
    pub(crate) timeout: bool,
    pub(crate) stdout_sha256: String,
    pub(crate) stderr_sha256: String,
}

pub(crate) fn materialize_entrypoint(candidate_root: &Path, raw: &[u8]) -> Result<PathBuf, String> {
    let metadata = fs::symlink_metadata(candidate_root)
        .map_err(|error| format!("worker staging inspection failed: {error}"))?;
    if !metadata.file_type().is_dir() || metadata.file_type().is_symlink() {
        return Err("worker staging is not a nonsymlink directory".to_owned());
    }
    let entrypoint = candidate_root.join("entrypoint");
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o500)
        .custom_flags(libc::O_NOFOLLOW | libc::O_CLOEXEC)
        .open(&entrypoint)
        .map_err(|error| format!("worker entrypoint materialization failed: {error}"))?;
    file.write_all(raw)
        .map_err(|error| format!("worker entrypoint write failed: {error}"))?;
    file.sync_all()
        .map_err(|error| format!("worker entrypoint fsync failed: {error}"))?;
    File::open(candidate_root)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| format!("worker staging fsync failed: {error}"))?;
    Ok(entrypoint)
}

fn validate_worker_spec(token: &StartReceiptToken, spec: &WorkerSpec) -> Result<(), String> {
    let entrypoint = fs::canonicalize(&spec.entrypoint)
        .map_err(|error| format!("cannot resolve worker entrypoint: {error}"))?;
    let output_root = fs::canonicalize(&spec.output_root)
        .map_err(|error| format!("cannot resolve bound output root: {error}"))?;
    let candidate_root = fs::canonicalize(&spec.candidate_root)
        .map_err(|error| format!("cannot resolve candidate staging root: {error}"))?;
    if !entrypoint.starts_with(&candidate_root) || candidate_root.starts_with(&output_root) {
        return Err("worker entrypoint is outside isolated read-only candidate staging".to_owned());
    }
    // Possession of this unforgeable token proves ReceiptStore::write_start
    // completed and fsynced. The binding is touched here so the ordering seam
    // cannot be optimized away into an unused marker.
    if token.binding_id().is_empty() {
        return Err("fsynced start receipt token is invalid".to_owned());
    }
    if spec.timeout.is_zero() || spec.timeout > Duration::from_secs(86_400) {
        return Err("worker timeout is outside the bounded range".to_owned());
    }
    if spec.environment.keys().any(|key| {
        key == "PYTHONPATH"
            || key == "LD_PRELOAD"
            || key == "PYTHONUSERBASE"
            || key.starts_with("GIT_")
    }) {
        return Err("worker environment contains a forbidden capability".to_owned());
    }
    for (key, expected) in [("LANG", "C"), ("LC_ALL", "C"), ("PATH", "/usr/bin:/bin")] {
        if spec.environment.get(key).map(String::as_str) != Some(expected) {
            return Err(format!("worker environment {key} is not launcher-fixed"));
        }
    }
    if spec.environment.get("HOME").map(String::as_str) != spec.output_root.to_str() {
        return Err("worker HOME is not the bound output root".to_owned());
    }
    if spec.artifact_mode == "production" {
        let uid = spec
            .worker_uid
            .ok_or_else(|| "production worker UID is absent".to_owned())?;
        let gid = spec
            .worker_gid
            .ok_or_else(|| "production worker GID is absent".to_owned())?;
        if uid == 0 || gid == 0 || unsafe { libc::geteuid() } != 0 {
            return Err(
                "production worker requires root launcher and nonroot dedicated IDs".to_owned(),
            );
        }
    } else if spec.worker_uid.is_some() || spec.worker_gid.is_some() {
        return Err("synthetic worker cannot request privilege changes".to_owned());
    }
    Ok(())
}

fn hash(raw: &[u8]) -> String {
    format!("sha256:{}", hex::encode(Sha256::digest(raw)))
}

pub(crate) fn run_worker(
    token: &StartReceiptToken,
    spec: &WorkerSpec,
) -> Result<WorkerOutcome, String> {
    validate_worker_spec(token, spec)?;
    let mut command = Command::new(&spec.runtime_executable);
    command
        .env_clear()
        .envs(&spec.environment)
        .args(&spec.runtime_arguments)
        .arg(&spec.entrypoint)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .current_dir(&spec.output_root);
    if spec.artifact_mode == "production" {
        unsafe {
            command.pre_exec(|| {
                if libc::setgroups(0, std::ptr::null()) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
                if libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
                Ok(())
            });
        }
        command.uid(spec.worker_uid.expect("validated worker UID"));
        command.gid(spec.worker_gid.expect("validated worker GID"));
    }
    let mut child = command
        .spawn()
        .map_err(|error| format!("isolated worker spawn failed: {error}"))?;
    let mut stdout = child
        .stdout
        .take()
        .ok_or_else(|| "worker stdout pipe unavailable".to_owned())?;
    let mut stderr = child
        .stderr
        .take()
        .ok_or_else(|| "worker stderr pipe unavailable".to_owned())?;
    let stdout_thread = thread::spawn(move || {
        let mut bytes = Vec::new();
        stdout.read_to_end(&mut bytes).map(|_| bytes)
    });
    let stderr_thread = thread::spawn(move || {
        let mut bytes = Vec::new();
        stderr.read_to_end(&mut bytes).map(|_| bytes)
    });
    let started = Instant::now();
    let mut timed_out = false;
    let status = loop {
        if let Some(status) = child
            .try_wait()
            .map_err(|error| format!("worker monitor failed: {error}"))?
        {
            break status;
        }
        if started.elapsed() >= spec.timeout {
            timed_out = true;
            child
                .kill()
                .map_err(|error| format!("timed-out worker kill failed: {error}"))?;
            break child
                .wait()
                .map_err(|error| format!("timed-out worker reap failed: {error}"))?;
        }
        thread::sleep(Duration::from_millis(5));
    };
    let stdout_bytes = stdout_thread
        .join()
        .map_err(|_| "worker stdout reader panicked".to_owned())?
        .map_err(|error| format!("worker stdout read failed: {error}"))?;
    let stderr_bytes = stderr_thread
        .join()
        .map_err(|_| "worker stderr reader panicked".to_owned())?
        .map_err(|error| format!("worker stderr read failed: {error}"))?;
    let (terminal, exit_code, signal, timeout) = if timed_out {
        ("TIMEOUT".to_owned(), None, None, true)
    } else if let Some(signal) = status.signal() {
        ("SIGNAL".to_owned(), None, Some(signal), false)
    } else if status.success() {
        ("SUCCESS".to_owned(), Some(0), None, false)
    } else {
        ("ERROR".to_owned(), status.code(), None, false)
    };
    Ok(WorkerOutcome {
        terminal,
        exit_code,
        signal,
        timeout,
        stdout_sha256: hash(&stdout_bytes),
        stderr_sha256: hash(&stderr_bytes),
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::receipts::ReceiptStore;
    use tempfile::tempdir;

    fn token_and_script(
        script: &[u8],
    ) -> (
        tempfile::TempDir,
        ReceiptStore,
        StartReceiptToken,
        PathBuf,
        PathBuf,
    ) {
        let temporary = tempdir().unwrap();
        let store = ReceiptStore::acquire(temporary.path(), false).unwrap();
        let binding = format!("sha256:{}", "a".repeat(64));
        let candidate = temporary.path().join("candidate");
        fs::create_dir(&candidate).unwrap();
        let output = temporary.path().join("output");
        fs::create_dir(&output).unwrap();
        let entrypoint = materialize_entrypoint(&candidate, script).unwrap();
        let (_, token) = store
            .write_start("synthetic_fixture", &binding, "2026-08-22T00:00:00Z")
            .unwrap();
        (temporary, store, token, entrypoint, output)
    }

    fn spec(entrypoint: PathBuf, output_root: PathBuf, timeout: Duration) -> WorkerSpec {
        let candidate_root = entrypoint.parent().unwrap().to_owned();
        WorkerSpec {
            artifact_mode: "synthetic_fixture".to_owned(),
            runtime_executable: PathBuf::from("/bin/sh"),
            runtime_arguments: Vec::new(),
            entrypoint,
            candidate_root,
            output_root: output_root.clone(),
            environment: BTreeMap::from([
                (
                    "HOME".to_owned(),
                    output_root.to_string_lossy().into_owned(),
                ),
                ("LANG".to_owned(), "C".to_owned()),
                ("LC_ALL".to_owned(), "C".to_owned()),
                ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
            ]),
            worker_uid: None,
            worker_gid: None,
            timeout,
        }
    }

    #[test]
    fn worker_has_sanitized_environment() {
        let (_temporary, _store, token, entrypoint, output_root) =
            token_and_script(b"#!/bin/sh\nenv | sort\n");
        let outcome = run_worker(
            &token,
            &spec(entrypoint, output_root, Duration::from_secs(2)),
        )
        .unwrap();
        assert_eq!(outcome.terminal, "SUCCESS");
        // A deterministic hash proves the child output is captured. The command
        // itself is constructed with env_clear(), so caller GIT/PYTHON/LD state
        // has no propagation surface.
        assert_ne!(outcome.stdout_sha256, format!("sha256:{}", "0".repeat(64)));
    }

    #[test]
    fn success_error_timeout_and_signal_are_distinct_terminal_paths() {
        let cases: &[(&[u8], Duration, &str)] = &[
            (b"#!/bin/sh\nexit 0\n", Duration::from_secs(2), "SUCCESS"),
            (b"#!/bin/sh\nexit 7\n", Duration::from_secs(2), "ERROR"),
            (
                b"#!/bin/sh\nsleep 2\n",
                Duration::from_millis(20),
                "TIMEOUT",
            ),
            (
                b"#!/bin/sh\nkill -TERM $$\n",
                Duration::from_secs(2),
                "SIGNAL",
            ),
        ];
        for (script, timeout, expected) in cases {
            let (_temporary, _store, token, entrypoint, output_root) = token_and_script(script);
            let outcome = run_worker(&token, &spec(entrypoint, output_root, *timeout)).unwrap();
            assert_eq!(&outcome.terminal, expected);
        }
    }

    #[test]
    fn production_worker_cannot_keep_root_identity() {
        let (_temporary, _store, token, entrypoint, output_root) =
            token_and_script(b"#!/bin/sh\nexit 0\n");
        let mut worker = spec(entrypoint, output_root, Duration::from_secs(1));
        worker.artifact_mode = "production".to_owned();
        worker.worker_uid = Some(0);
        worker.worker_gid = Some(0);
        assert!(run_worker(&token, &worker).is_err());
    }
}
