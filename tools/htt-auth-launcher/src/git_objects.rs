use std::path::{Component, Path};
use std::process::Command;

use crate::canonical_json::require_git_object;

const TRUSTED_GIT: &str = "/usr/bin/git";

fn relative_blob_path(value: &str) -> Result<(), String> {
    let path = Path::new(value);
    if value.is_empty()
        || value != path.to_string_lossy()
        || path.is_absolute()
        || value.contains(['\0', '\n', '\r', ':'])
        || path
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        return Err("candidate blob path is not canonical and relative".to_owned());
    }
    Ok(())
}

fn git(repo: &Path, args: &[&str]) -> Result<Vec<u8>, String> {
    if !Path::new(TRUSTED_GIT).is_file() {
        return Err("trusted Git executable is unavailable".to_owned());
    }
    let output = Command::new(TRUSTED_GIT)
        .env_clear()
        .env("GIT_CONFIG_NOSYSTEM", "1")
        .env("GIT_CONFIG_GLOBAL", "/dev/null")
        .env("GIT_LITERAL_PATHSPECS", "1")
        .env("GIT_NO_REPLACE_OBJECTS", "1")
        .env("GIT_NO_LAZY_FETCH", "1")
        .env("GIT_OPTIONAL_LOCKS", "0")
        .env("LC_ALL", "C")
        .env("LANG", "C")
        .args([
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.fsmonitor=false",
            "-c",
            "core.untrackedCache=false",
            "-C",
        ])
        .arg(repo)
        .args(args)
        .output()
        .map_err(|error| format!("trusted Git invocation failed: {error}"))?;
    if !output.status.success() {
        return Err(format!(
            "trusted Git rejected object request: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ));
    }
    Ok(output.stdout)
}

pub(crate) fn inspect_candidate(repo: &Path, commit: &str, tree: &str) -> Result<(), String> {
    require_git_object(commit, "candidate_commit")?;
    require_git_object(tree, "candidate_tree")?;
    let kind = git(repo, &["cat-file", "-t", commit])?;
    if kind != b"commit\n" {
        return Err("candidate_commit is not a commit object".to_owned());
    }
    let expression = format!("{commit}^{{tree}}");
    let observed = git(repo, &["rev-parse", "--verify", &expression])?;
    if observed != format!("{tree}\n").as_bytes() {
        return Err("candidate commit/tree binding mismatched".to_owned());
    }
    Ok(())
}

pub(crate) fn read_candidate_blob(
    repo: &Path,
    commit: &str,
    relative: &str,
) -> Result<Vec<u8>, String> {
    require_git_object(commit, "candidate_commit")?;
    relative_blob_path(relative)?;
    let object = format!("{commit}:{relative}");
    if git(repo, &["cat-file", "-t", &object])? != b"blob\n" {
        return Err("candidate resource is not a Git blob".to_owned());
    }
    git(repo, &["cat-file", "blob", &object])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn candidate_path_rejects_escape_and_git_environment_is_not_an_api() {
        for path in ["/absolute", "../escape", "a/../b", "HEAD:file", "a\nb"] {
            assert!(relative_blob_path(path).is_err());
        }
        assert!(relative_blob_path("docs/plan.json").is_ok());
    }
}
