use libc::{c_int, O_CLOEXEC, O_CREAT, O_DIRECTORY, O_EXCL, O_NOFOLLOW, O_RDONLY, O_WRONLY};
use serde::Serialize;
use sha2::{Digest, Sha256};
use std::ffi::CString;
use std::fs::{self, File};
use std::io::Write;
use std::os::fd::{AsRawFd, FromRawFd};
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::MetadataExt;
use std::path::Path;

use crate::canonical_json::{canonical_bytes, content_id, require_sha256};

#[derive(Debug, Clone, Serialize)]
pub(crate) struct NonceConsumptionReceipt {
    pub(crate) schema: String,
    pub(crate) artifact_mode: String,
    pub(crate) authorization_id: String,
    pub(crate) run_id: String,
    pub(crate) nonce_sha256: String,
    pub(crate) consumed_at_utc: String,
    pub(crate) ledger_entry_identity: String,
    pub(crate) receipt_id: String,
}

#[derive(Serialize)]
struct LedgerEntry<'a> {
    schema: &'static str,
    artifact_mode: &'a str,
    authorization_id: &'a str,
    run_id: &'a str,
    nonce_sha256: &'a str,
    consumed_at_utc: &'a str,
}

fn open_directory(path: &Path, require_root: bool) -> Result<File, String> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("cannot inspect nonce ledger directory: {error}"))?;
    if !metadata.file_type().is_dir() || metadata.file_type().is_symlink() {
        return Err("nonce ledger path is not a nonsymlink directory".to_owned());
    }
    if require_root && (metadata.uid() != 0 || metadata.mode() & 0o077 != 0) {
        return Err("production nonce ledger is not root-owned mode 0700".to_owned());
    }
    let raw_path = CString::new(path.as_os_str().as_bytes())
        .map_err(|_| "nonce ledger path contains NUL".to_owned())?;
    let fd = unsafe {
        libc::open(
            raw_path.as_ptr(),
            O_RDONLY | O_DIRECTORY | O_NOFOLLOW | O_CLOEXEC,
        )
    };
    if fd < 0 {
        return Err(format!(
            "cannot open nonce ledger directory safely: {}",
            std::io::Error::last_os_error()
        ));
    }
    Ok(unsafe { File::from_raw_fd(fd) })
}

fn openat_exclusive(directory: &File, filename: &str) -> Result<File, String> {
    let name = CString::new(filename).map_err(|_| "nonce filename contains NUL".to_owned())?;
    let fd: c_int = unsafe {
        libc::openat(
            directory.as_raw_fd(),
            name.as_ptr(),
            O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW | O_CLOEXEC,
            0o600,
        )
    };
    if fd < 0 {
        return Err(format!(
            "nonce is already consumed or ledger creation failed permanently: {}",
            std::io::Error::last_os_error()
        ));
    }
    Ok(unsafe { File::from_raw_fd(fd) })
}

pub(crate) fn consume_nonce(
    ledger_root: &Path,
    artifact_mode: &str,
    authorization_id: &str,
    run_id: &str,
    raw_nonce: &str,
    consumed_at_utc: &str,
    require_root: bool,
) -> Result<NonceConsumptionReceipt, String> {
    if !matches!(artifact_mode, "production" | "synthetic_fixture") {
        return Err("nonce artifact mode is invalid".to_owned());
    }
    require_sha256(authorization_id, "authorization_id")?;
    if raw_nonce.len() != 73
        || !raw_nonce.starts_with("nonce:v1:")
        || !raw_nonce[9..]
            .bytes()
            .all(|byte| byte.is_ascii_hexdigit() && !byte.is_ascii_uppercase())
    {
        return Err("nonce is not canonical high entropy".to_owned());
    }
    if run_id.is_empty()
        || run_id.len() > 128
        || !run_id
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_'))
    {
        return Err("run_id is not safe for the nonce ledger".to_owned());
    }
    let nonce_sha256 = format!(
        "sha256:{}",
        hex::encode(Sha256::digest(raw_nonce.as_bytes()))
    );
    let entry = LedgerEntry {
        schema: "common.nonce_ledger_entry.v1",
        artifact_mode,
        authorization_id,
        run_id,
        nonce_sha256: &nonce_sha256,
        consumed_at_utc,
    };
    let bytes = canonical_bytes(&entry)?;
    let ledger_entry_identity = content_id(&entry)?;
    let directory = open_directory(ledger_root, require_root)?;
    let filename = format!("{}.json", nonce_sha256.trim_start_matches("sha256:"));
    let mut file = openat_exclusive(&directory, &filename)?;
    file.write_all(&bytes)
        .map_err(|error| format!("nonce ledger write failed: {error}"))?;
    file.sync_all()
        .map_err(|error| format!("nonce ledger file fsync failed: {error}"))?;
    directory
        .sync_all()
        .map_err(|error| format!("nonce ledger directory fsync failed: {error}"))?;
    let unsigned = serde_json::json!({
        "artifact_mode": artifact_mode,
        "authorization_id": authorization_id,
        "run_id": run_id,
        "nonce_sha256": nonce_sha256,
        "consumed_at_utc": consumed_at_utc,
        "ledger_entry_identity": ledger_entry_identity,
    });
    Ok(NonceConsumptionReceipt {
        schema: "common.nonce_consumption_receipt.v1".to_owned(),
        artifact_mode: artifact_mode.to_owned(),
        authorization_id: authorization_id.to_owned(),
        run_id: run_id.to_owned(),
        nonce_sha256: unsigned["nonce_sha256"].as_str().unwrap().to_owned(),
        consumed_at_utc: consumed_at_utc.to_owned(),
        ledger_entry_identity: unsigned["ledger_entry_identity"]
            .as_str()
            .unwrap()
            .to_owned(),
        receipt_id: content_id(&unsigned)?,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn nonce_is_atomic_permanent_and_never_named_by_raw_secret() {
        let temporary = tempdir().unwrap();
        let nonce = format!("nonce:v1:{}", "a".repeat(64));
        let authorization = format!("sha256:{}", "b".repeat(64));
        let first = consume_nonce(
            temporary.path(),
            "synthetic_fixture",
            &authorization,
            "run-1",
            &nonce,
            "2026-08-22T00:00:00Z",
            false,
        )
        .unwrap();
        assert!(!first.nonce_sha256.contains(&nonce));
        assert_eq!(fs::read_dir(temporary.path()).unwrap().count(), 1);
        assert!(consume_nonce(
            temporary.path(),
            "synthetic_fixture",
            &authorization,
            "run-1",
            &nonce,
            "2026-08-22T00:00:01Z",
            false,
        )
        .is_err());
    }

    #[test]
    fn preexisting_partial_entry_permanently_refuses_replay() {
        let temporary = tempdir().unwrap();
        let nonce = format!("nonce:v1:{}", "c".repeat(64));
        let digest = hex::encode(Sha256::digest(nonce.as_bytes()));
        fs::write(temporary.path().join(format!("{digest}.json")), b"").unwrap();
        assert!(consume_nonce(
            temporary.path(),
            "synthetic_fixture",
            &format!("sha256:{}", "d".repeat(64)),
            "run-2",
            &nonce,
            "2026-08-22T00:00:00Z",
            false,
        )
        .is_err());
    }
}
