# Codex setup

Unpack to a new staging directory and inspect/merge repo instructions before applying. Never unzip over an existing repository as an installation step. Preserve project AGENTS, scientific values, logs and existing skills. The five bundled `.agents/skills/*/SKILL.md` files are unchanged inherited assets, not a personal-skill installation.

Run `python3 tools/validate_harness.py --json` on the package, then merge only selected files. `init_harness.py --root /absolute/repo` creates missing state files and preserves every existing file including empty files; it does not install the harness. v4 removes the destructive `--force` option.

Use the host's actual model inventory and `docs/MODEL_ROUTING.md`. Model names in documents do not change the runtime. Read AGENTS loading and tool behavior from current official documentation when configuring a host. Do not assume that API and host effort names are identical. API-specific configuration and host-specific capabilities must be reported separately.
