use base64::engine::general_purpose::STANDARD;
use base64::Engine as _;
use ed25519_dalek::{Signature, Verifier, VerifyingKey};
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::Path;

use crate::canonical_json::sha256_identity;

pub(crate) fn canonical_base64<const N: usize>(
    value: &str,
    field: &str,
) -> Result<[u8; N], String> {
    let decoded = STANDARD
        .decode(value)
        .map_err(|error| format!("{field} is not base64: {error}"))?;
    if decoded.len() != N || STANDARD.encode(&decoded) != value {
        return Err(format!("{field} is not canonical base64 for {N} bytes"));
    }
    decoded
        .try_into()
        .map_err(|_| format!("{field} has the wrong byte length"))
}

pub(crate) fn key_id(public_key: &[u8; 32]) -> String {
    sha256_identity(public_key)
}

pub(crate) fn verify_ed25519(
    public_key: &[u8; 32],
    message: &[u8],
    signature_base64: &str,
    field: &str,
) -> Result<(), String> {
    let signature_bytes = canonical_base64::<64>(signature_base64, field)?;
    let key = VerifyingKey::from_bytes(public_key)
        .map_err(|error| format!("invalid Ed25519 public key: {error}"))?;
    key.verify(message, &Signature::from_bytes(&signature_bytes))
        .map_err(|_| format!("{field} verification failed"))
}

fn require_root_owned_regular(path: &Path, label: &str) -> Result<(), String> {
    let metadata =
        fs::symlink_metadata(path).map_err(|error| format!("cannot inspect {label}: {error}"))?;
    if !metadata.file_type().is_file() || metadata.file_type().is_symlink() {
        return Err(format!("{label} is not a regular nonsymlink file"));
    }
    if metadata.uid() != 0 || metadata.mode() & 0o022 != 0 {
        return Err(format!("{label} is not root-owned and non-writable"));
    }
    Ok(())
}

pub(crate) fn load_external_root(
    public_key_path: &Path,
    fingerprint_path: &Path,
) -> Result<[u8; 32], String> {
    require_root_owned_regular(public_key_path, "external root public key")?;
    require_root_owned_regular(fingerprint_path, "external root fingerprint")?;
    let key_text = fs::read_to_string(public_key_path)
        .map_err(|error| format!("cannot read external root public key: {error}"))?;
    if !key_text.ends_with('\n') || key_text.matches('\n').count() != 1 {
        return Err("external root public key must be one canonical base64 line".to_owned());
    }
    let public_key = canonical_base64::<32>(key_text.trim_end_matches('\n'), "root public key")?;
    let expected = fs::read_to_string(fingerprint_path)
        .map_err(|error| format!("cannot read root fingerprint: {error}"))?;
    if expected != format!("{}\n", key_id(&public_key)) {
        return Err("external root fingerprint mismatched".to_owned());
    }
    Ok(public_key)
}

#[cfg(test)]
mod tests {
    use super::*;
    use ed25519_dalek::{Signer, SigningKey};

    #[test]
    fn signature_and_canonical_base64_are_exact() {
        let signing = SigningKey::from_bytes(&[7_u8; 32]);
        let message = b"root-bound-message";
        let signature = STANDARD.encode(signing.sign(message).to_bytes());
        verify_ed25519(
            &signing.verifying_key().to_bytes(),
            message,
            &signature,
            "signature",
        )
        .unwrap();
        assert!(verify_ed25519(
            &signing.verifying_key().to_bytes(),
            b"different",
            &signature,
            "signature"
        )
        .is_err());
        assert!(canonical_base64::<32>("not-base64", "key").is_err());
    }
}
