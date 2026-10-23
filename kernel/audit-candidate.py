#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Reconstruct reference postimages and inventory every aggregate hunk against 7.3.

Requires both pinned tags in --source. Partial clones may fetch missing blobs.
The source checkout is read only; the aggregate is applied in a temporary folder.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from importlib.util import module_from_spec, spec_from_file_location

ROOT = Path(__file__).resolve().parent.parent
PORT = ROOT / "kernel/ports/v7.3"
spec = spec_from_file_location("candidate", ROOT / "kernel/prepare-candidate.py")
candidate = module_from_spec(spec)
spec.loader.exec_module(candidate)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def show(source, commit, path):
    return subprocess.run(
        ["git", "-C", str(source), "show", f"{commit}:{path}"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout


def group(path):
    if path == "MAINTAINERS":
        return "camera profile: reference PHY maintainer entry retained"
    if path.endswith("x1p42100-microsoft-sp12in.dts"):
        return "board: upstream baseline plus platform volume/DP-audio/charge changes; camera resources staged disabled in camera profile"
    if "/rtc/" in path or path.endswith("surface_aggregator_registry.c"):
        return "platform profile: reference RTC source and SP12 software-node registration; upstream SAM registration retained"
    if path.endswith("aggregator/controller.c"):
        return "platform profile: reference suspend workaround narrowed to SP12 only"
    if path.endswith("qcom_scm.c") or path.endswith("panel-edp.c") or path.endswith("qcom/Makefile"):
        return "upstream platform support retained; duplicate aggregate intent excluded"
    return "camera profile: three-way reconciled reference intent retaining upstream changes; CAMCC retained upstream; runtime camera nodes disabled"


def audit(source):
    research = json.loads((PORT / "research/linux-7.3-patch-audit.json").read_text())
    manifest = json.loads((PORT / "manifest.json").read_text())
    old = research["reference_reconstruction"]["base_commit"]
    new = manifest["base_commit"]
    for tag, commit in [("v7.2-rc7", old), ("v7.3", new)]:
        if candidate.git(source, "rev-parse", f"{tag}^{{commit}}") != commit:
            raise ValueError(f"Unexpected {tag} commit")
    if candidate.git(source, "rev-parse", "v7.3") != manifest["base_tag_object"]:
        raise ValueError("Unexpected v7.3 tag object")
    snapshot = candidate.checked_input(ROOT, {
        "path": research["aggregate"]["patch"],
        "sha256": research["aggregate"]["sha256"],
    })
    sections = re.split(r"(?=^diff --git )", snapshot.read_text(), flags=re.M)
    sections = {re.search(r"^diff --git a/(.+) b/", s).group(1): s
                for s in sections if s.startswith("diff --git ")}
    results = []
    with tempfile.TemporaryDirectory(prefix="sp12-reference-") as temporary:
        tree = Path(temporary)
        for path, section in sections.items():
            if "--- /dev/null" not in section:
                target = tree / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(show(source, old, path))
        subprocess.run(["git", "-c", "core.autocrlf=false", "apply", "--check", str(snapshot)], cwd=tree, check=True)
        subprocess.run(["git", "-c", "core.autocrlf=false", "apply", str(snapshot)], cwd=tree, check=True)
        for previous in research["reference_reconstruction"]["files"]:
            path = previous["path"]
            reference = (tree / path).read_bytes()
            if sha(reference) != previous["reference_postimage_sha256"]:
                raise ValueError(f"Reconstruction mismatch: {path}")
            current = show(source, new, path) if previous["upstream_present"] else None
            if current is not None and sha(current) != previous["upstream_sha256"]:
                raise ValueError(f"Upstream source mismatch: {path}")
            section = sections[path]
            results.append({
                "path": path, "reference_postimage_sha256": sha(reference),
                "upstream_sha256": sha(current) if current is not None else None,
                "disposition": group(path),
                "hunks": re.findall(r"^@@.*$", section, flags=re.M),
                "status": "source disposition reviewed; compile/DT results recorded separately; hardware validation pending",
            })
    if set(sections) != {r["path"] for r in results}:
        raise ValueError("Aggregate hunk inventory is incomplete")
    return {"schema": 1, "base_commit": new, "reference_base_commit": old,
            "aggregate_sha256": sha(snapshot.read_bytes()),
            "method": "Reconstructed aggregate in temporary directory; verified all postimage and upstream hashes against supplied audit; classified every hunk by file. No semantic equivalence or build claim.",
            "files": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.source.resolve())
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Verified and classified {len(report['files'])} aggregate files.")
