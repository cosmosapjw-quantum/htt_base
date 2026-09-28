#!/usr/bin/env python3
"""Select a package from explicit input. No environment or model introspection."""

import argparse
import json
from pathlib import Path, PurePosixPath
import re
import sys


FAMILIES = ("gpt56", "gpt6-astra")
TASKS = ("research", "coding")
DEFAULT_REGISTRY = Path(__file__).resolve().parent.parent / "MODEL_ROUTER.json"


class ConfigError(ValueError):
    """The registry is unavailable or cannot safely define deterministic routing."""


def normalize(label):
    return label.strip().casefold()


def _require(condition, message):
    if not condition:
        raise ConfigError(message)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def read_registry(path):
    """Load and validate every route, including routes not selected by this call."""
    try:
        registry = json.loads(Path(path).read_text(encoding="utf-8"), object_pairs_hook=_unique_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigError(f"Cannot read registry: {exc}") from exc
    _require(isinstance(registry, dict), "Registry must be a JSON object")
    _require(type(registry.get("router_version")) is int and registry["router_version"] == 1,
             "Unsupported router_version; expected integer 1")
    families = registry.get("families")
    _require(isinstance(families, dict) and set(families) == set(FAMILIES),
             "Registry must contain exactly gpt56 and gpt6-astra families")
    alias_map = {}
    for family, record in families.items():
        _require(isinstance(record, dict), f"Invalid family record: {family}")
        aliases = record.get("aliases")
        _require(isinstance(aliases, list) and len(aliases) > 0,
                 f"Missing aliases: {family}")
        for alias in aliases:
            _require(isinstance(alias, str) and bool(normalize(alias)),
                     f"Invalid alias: {family}")
            key = normalize(alias)
            _require(key not in alias_map, f"Alias collision after normalization: {key}")
            alias_map[key] = family
        packages = record.get("packages")
        _require(isinstance(packages, dict) and set(packages) == set(TASKS),
                 f"Each family must define research and coding packages: {family}")
        for task, package in packages.items():
            _require(isinstance(package, dict), f"Invalid package: {family}/{task}")
            filename = package.get("filename")
            _require(isinstance(filename, str) and filename.endswith(".zip")
                     and PurePosixPath(filename).name == filename and "\\" not in filename,
                     f"Invalid package filename: {family}/{task}")
            _require(package.get("library_path") == f"/Research-Harnesses/{filename}",
                     f"Package path and filename disagree: {family}/{task}")
            file_id = package.get("library_file_id")
            _require(file_id is None or (isinstance(file_id, str)
                     and bool(re.fullmatch(r"libfile_[A-Za-z0-9]+", file_id))),
                     f"Invalid Library file ID: {family}/{task}")
            digest = package.get("sha256")
            _require(digest is None or (isinstance(digest, str)
                     and bool(re.fullmatch(r"[0-9a-f]{64}", digest))),
                     f"Invalid SHA-256: {family}/{task}")
            entrypoints = package.get("entrypoints")
            _require(isinstance(entrypoints, list) and len(entrypoints) > 0,
                     f"Missing entrypoints: {family}/{task}")
            for entry in entrypoints:
                _require(isinstance(entry, str) and bool(entry)
                         and not PurePosixPath(entry).is_absolute()
                         and ".." not in PurePosixPath(entry).parts and "\\" not in entry,
                         f"Invalid relative entrypoint: {family}/{task}")
    return registry, alias_map


def resolve(registry, aliases, model=None, harness=None, task="research"):
    """Return selection only. Input labels are caller assertions, not verification."""
    if harness is not None:
        if harness not in FAMILIES:
            raise ValueError("Unsupported explicit harness")
        family = harness
        basis = "explicit_user_harness_override"
    else:
        family = aliases.get(normalize(model)) if model is not None else None
        basis = "caller_supplied_model_label" if family else None
    if task not in (*TASKS, "both"):
        raise ValueError("Unsupported task")
    common = {
        "router_version": 1,
        "status": "SELECTED" if family else "MODEL_UNRESOLVED",
        "family": family,
        "task": task,
        "selection_basis": basis,
        "supplied_model_label": model,
        "explicit_harness_override": harness,
        "model_identity_verified": False,
        "model_switched": False,
        "harness_loaded": False,
        "harness_executed": False,
        "packages": [],
    }
    if family is None:
        common["reason"] = "Supply an exact supported model label or an explicit harness choice. Do not infer model identity."
        return common
    selected_tasks = TASKS if task == "both" else (task,)
    for selected_task in selected_tasks:
        package = registry["families"][family]["packages"][selected_task]
        common["packages"].append({"task": selected_task, **package})
    return common


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", help="Observed or user-selected model label supplied by the caller")
    parser.add_argument("--harness", choices=FAMILIES,
                        help="Explicit user harness choice; overrides --model without switching models")
    parser.add_argument("--task", choices=(*TASKS, "both"), default="research")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    args = parser.parse_args(argv)
    try:
        registry, aliases = read_registry(args.registry)
        result = resolve(registry, aliases, args.model, args.harness, args.task)
    except ConfigError as exc:
        print(json.dumps({"router_version": 1, "status": "CONFIG_ERROR",
                          "reason": str(exc), "packages": []}, ensure_ascii=False))
        return 3
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "SELECTED" else 2


if __name__ == "__main__":
    sys.exit(main())
