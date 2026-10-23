#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Preflight and apply the explicitly selected development series, without builds."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "kernel/ports/v7.3/manifest.json"


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
    if output and ((source / ".config").exists() or (source / "include/config").exists()):
        raise ValueError("Out-of-tree builds require an unconfigured source tree")
    entries, config_entry = selected_inputs(manifest, profile)
    config = checked_input(root, config_entry)
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
    print(f"Applied {profile} development series; config: {config_path}")
    print("This is a candidate for validation; see kernel/ports/v7.3/README.md.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--profile", choices=("platform", "camera"), default="platform")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        prepare(args.source, json.loads(MANIFEST.read_text()), ROOT, args.apply, args.profile, args.output)
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        detail = error.stderr if isinstance(error, subprocess.CalledProcessError) else str(error)
        parser.exit(1, f"Candidate preparation failed: {detail}\n")


if __name__ == "__main__":
    main()
