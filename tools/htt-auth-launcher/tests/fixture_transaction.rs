use std::process::Command;

#[test]
fn release_contract_has_fixed_paths_and_no_override_surface() {
    let binary = env!("CARGO_BIN_EXE_htt-auth-launcher");
    let output = Command::new(binary)
        .arg("--contract")
        .output()
        .expect("launcher contract command must run");
    assert!(output.status.success());

    let payload: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("contract must be JSON");
    assert_eq!(
        payload["launcher_path"],
        "/usr/local/libexec/htt-auth-launcher"
    );
    assert_eq!(
        payload["root_public_key"],
        "/etc/htt/trust/root_authority_ed25519.pub"
    );
    assert_eq!(payload["nonce_store"], "/var/lib/htt-auth/nonces");
    assert_eq!(payload["run_store"], "/var/lib/htt-auth/runs");
    assert_eq!(payload["production_path_overrides_absent"], true);
    assert_eq!(payload["production_launcher_installed"], false);
    assert_eq!(payload["observed_data_executed"], false);
}

#[test]
fn release_cli_rejects_all_path_override_flags() {
    let binary = env!("CARGO_BIN_EXE_htt-auth-launcher");
    for flag in [
        "--root-key",
        "--root-fingerprint",
        "--nonce-store",
        "--run-store",
        "--candidate-repo",
        "--output-root",
    ] {
        let output = Command::new(binary)
            .args(["--contract", flag, "/tmp/attacker"])
            .output()
            .expect("launcher must reject override");
        assert!(!output.status.success(), "accepted {flag}");
    }
}
