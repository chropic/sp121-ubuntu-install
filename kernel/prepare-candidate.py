#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Preflight and apply the explicitly selected development series, without builds."""

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "kernel/ports/v7.3/manifest.json"


def load_manifest(path):
    manifest = json.loads(path.read_text())
    if path.resolve() != MANIFEST.resolve():
        if manifest.get("experiment_schema") != 1:
            raise ValueError("Alternate manifests require experiment_schema: 1")
        if not re.fullmatch(r"[0-9a-f]{40}", manifest.get("base_commit", "")):
            raise ValueError("Experiment requires a full base commit")
        identities = set()
        versions = set()
        for profile in manifest.get("profiles", {}).values():
            release = profile.get("kernel_release", "")
            version = profile.get("package_version", "")
            if not re.fullmatch(r"[0-9][A-Za-z0-9.+~-]*-sp12-exp-[a-z0-9-]+", release):
                raise ValueError("Experiment requires a unique sp12-exp- kernel release")
            if not re.fullmatch(r"[0-9][A-Za-z0-9.+~]*-[A-Za-z0-9.+~]*sp12exp[a-z0-9]+", version):
                raise ValueError("Experiment requires a unique sp12exp package version")
            if release in identities or version in versions:
                raise ValueError("Experiment profiles must have distinct release/package identities")
            identities.add(release)
            versions.add(version)
        if not manifest.get("profiles"):
            raise ValueError("Experiment requires explicit profiles")
    return manifest


def verify_identity(manifest, profile, config):
    if manifest.get("experiment_schema") != 1:
        return
    selection = manifest["profiles"][profile]
    release = selection["kernel_release"]
    suffix = release[release.index("-sp12-exp-"):]
    lines = config.read_text().splitlines()
    if f'CONFIG_LOCALVERSION="{suffix}"' not in lines or "# CONFIG_LOCALVERSION_AUTO is not set" not in lines:
        raise ValueError("Experiment config must pin its release suffix and disable LOCALVERSION_AUTO")


def manifest_identity(manifest, profile):
    return {"profile": profile, "manifest_sha256": hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def git(source, *args, env=None):
    return subprocess.run(
        ["git", "-C", str(source), *args], check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
    ).stdout.strip()


def checked_input(root, item):
    path = (root / item["path"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError("Input escapes repository")
    if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
        raise ValueError(f"Input hash mismatch: {item['path']}")
    return path


def selected_inputs(manifest, profile):
    if "profiles" not in manifest:
        return manifest["series"], manifest["config_seed"]
    selection = manifest["profiles"][profile]
    return manifest["series"] + selection.get("extra_series", []), selection["config"]


def series_tree(source, patches, index):
    env = dict(os.environ, GIT_INDEX_FILE=str(index))
    git(source, "read-tree", "HEAD", env=env)
    for patch in patches:
        git(source, "apply", "--cached", "--check", str(patch), env=env)
        git(source, "apply", "--cached", str(patch), env=env)
    return git(source, "write-tree", env=env)


def prepare(source, manifest, root, apply=False, profile="platform", output=None):
    source = source.resolve(strict=True)
    if Path(git(source, "rev-parse", "--show-toplevel")).resolve() != source:
        raise ValueError("--source must name the kernel checkout root")
    actual = git(source, "rev-parse", "HEAD")
    if actual != manifest["base_commit"]:
        raise ValueError(f"Wrong base: expected {manifest['base_commit']}, found {actual}")
    if git(source, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError("Source tree is not clean")
    config_dir = output.resolve() if output else source
    config_path = config_dir / ".config"
    # .config is normally ignored, so Git status alone cannot protect it.
    if config_path.exists() or config_path.is_symlink():
        raise ValueError("Existing .config would be overwritten")
    receipt = config_dir / ".sp12-candidate.json"
    if receipt.exists() or receipt.is_symlink():
        raise ValueError("Existing candidate receipt would be overwritten")
    if output and ((source / ".config").exists() or (source / "include/config").exists()):
        raise ValueError("Out-of-tree builds require an unconfigured source tree")
    entries, config_entry = selected_inputs(manifest, profile)
    config = checked_input(root, config_entry)
    verify_identity(manifest, profile, config)
    patches = [checked_input(root, item) for item in entries]
    # A disposable index checks the entire ordered series without modifying
    # the checkout or its real index. Linked Git worktrees are supported.
    with tempfile.TemporaryDirectory(prefix="sp12-series-") as temporary:
        tree = series_tree(source, patches, Path(temporary) / "index")
    print(f"Base commit: {actual}")
    print(f"Ordered series verified: {len(patches)} patch(es)")
    print(f"Candidate source tree: {tree}")
    print("Signature verification and remaining hardware gates are recorded in the manifest.")
    if not apply:
        print("DRY RUN: source tree and .config were not changed.")
        return
    for patch in patches:
        git(source, "apply", str(patch))
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path.write_bytes(config.read_bytes())
    if manifest.get("experiment_schema") == 1:
        (config_dir / ".sp12-candidate.json").write_text(json.dumps(manifest_identity(manifest, profile)) + "\n")
    print(f"Applied {profile} development series; config: {config_path}")
    print("This is a candidate for validation; see kernel/ports/v7.3/README.md.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--profile", choices=("platform", "camera"), default="platform")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    args = parser.parse_args()
    try:
        prepare(args.source, load_manifest(args.manifest), ROOT, args.apply, args.profile, args.output)
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
        parser.exit(1, f"Candidate preparation failed: {detail}\n")


if __name__ == "__main__":
    main()
