#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Build only a hash-verified candidate source/config pair; never install it."""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

spec = spec_from_file_location("candidate", Path(__file__).with_name("prepare-candidate.py"))
candidate = module_from_spec(spec)
spec.loader.exec_module(candidate)


def verify(source, output, manifest, profile, root):
    if manifest.get("experiment_schema") == 1:
        receipt = json.loads((output / ".sp12-candidate.json").read_text())
        if receipt != candidate.manifest_identity(manifest, profile):
            raise ValueError("Prepared manifest/profile does not match selected manifest")
    if candidate.git(source, "rev-parse", "HEAD") != manifest["base_commit"]:
        raise ValueError("Wrong candidate base commit")
    entries, config_entry = candidate.selected_inputs(manifest, profile)
    patches = [candidate.checked_input(root, entry) for entry in entries]
    candidate.checked_input(root, config_entry)
    candidate.verify_identity(manifest, profile, output / ".config")
    if hashlib.sha256((output / ".config").read_bytes()).hexdigest() != config_entry["sha256"]:
        raise ValueError("Build config differs from the reviewed candidate config")
    with tempfile.TemporaryDirectory(prefix="sp12-build-check-") as temporary:
        expected = candidate.series_tree(source, patches, Path(temporary) / "expected")
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temporary) / "actual"))
        candidate.git(source, "read-tree", "HEAD", env=env)
        excludes = ["--", ".", ":(exclude).sp12-candidate.json"] if manifest.get("experiment_schema") == 1 else []
        candidate.git(source, "add", "--all", *excludes, env=env)
        actual = candidate.git(source, "write-tree", env=env)
    if actual != expected:
        raise ValueError(f"Source does not match selected series: expected {expected}, found {actual}")
    return actual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--profile", choices=("platform", "camera"), default="platform")
    parser.add_argument("--jobs", type=int, default=os.cpu_count() or 1)
    parser.add_argument("--cross-compile", default="")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--manifest", type=Path, default=candidate.MANIFEST)
    args = parser.parse_args()
    try:
        if args.jobs < 1:
            raise ValueError("Job count must be positive")
        source = args.source.resolve(strict=True)
        output = args.output.resolve(strict=True) if args.output else source
        manifest = candidate.load_manifest(args.manifest)
        manifest_hash = hashlib.sha256(args.manifest.read_bytes()).hexdigest()
        tree = verify(source, output, manifest, args.profile, candidate.ROOT)
        if args.verify_only:
            print(f"Verified {args.profile} source/config pair; source tree: {tree}")
            return
        for command in ["make", f"{args.cross_compile}gcc", f"{args.cross_compile}ld", "pahole"]:
            if not shutil.which(command):
                raise ValueError(f"Missing build command: {command}")
        # The full source/config identity is verified above; an uncommitted
        # patch series must not append a Git-dependent '-dirty' release suffix.
        package_version = manifest.get("profiles", {}).get(args.profile, {}).get("package_version", "7.3-1~sp12candidate1")
        # Debian's build-arch passes the package revision to Kbuild. Use the
        # same version and timestamp in the preceding parallel build, so the
        # serial packaging phase does not relink vmlinux and every module BTF.
        timestamp = os.environ.get("KBUILD_BUILD_TIMESTAMP")
        if not timestamp:
            epoch = os.environ.get("SOURCE_DATE_EPOCH")
            instant = datetime.fromtimestamp(int(epoch), timezone.utc) if epoch else datetime.now(timezone.utc)
            timestamp = instant.strftime("%Y-%m-%d %H:%M:%S +0000")
        build_env = dict(os.environ, KBUILD_BUILD_TIMESTAMP=timestamp)
        make = ["make", "-C", str(source), "ARCH=arm64", "LOCALVERSION=",
                f"KBUILD_BUILD_VERSION={package_version.rsplit('-', 1)[1]}",
                f"CROSS_COMPILE={args.cross_compile}"]
        if output != source:
            make.append(f"O={output}")
        expected_release = manifest.get("profiles", {}).get(args.profile, {}).get("kernel_release")
        if expected_release:
            actual_release = subprocess.check_output(make + ["-s", "kernelrelease"], text=True).strip()
            if actual_release != expected_release:
                raise ValueError("Kernel release differs from selected experiment manifest")
        targets = ["Image", "modules", "qcom/x1p42100-microsoft-sp12in.dtb"]
        if "CONFIG_EFI_ZBOOT=y" in (output / ".config").read_text().splitlines():
            targets.append("vmlinuz.efi")
        subprocess.run(make + [f"-j{args.jobs}", *targets], check=True, env=build_env)
        # Kconfig can refresh compiler-dependent values during a build. Do not
        # package a silently changed configuration under the reviewed identity.
        verify(source, output, manifest, args.profile, candidate.ROOT)
        if not args.build_only:
            for command in ["dpkg-buildpackage", "rsync", "cpio"]:
                if not shutil.which(command):
                    raise ValueError(f"Missing packaging command: {command}")
            profiles = os.environ.get("DEB_BUILD_PROFILES", "").split()
            # Preserve debug info in the build tree without creating a very
            # large optional debug package. Build ARM64 headers natively:
            # cross install-extmod-build needs target libcrypto and leaves the
            # build-host resolve_btfids binary in the resulting headers.
            profiles.append("pkg.linux-sp12.nokerneldbg")
            if args.cross_compile:
                profiles.append("pkg.linux-sp12.nokernelheaders")
            package_env = dict(build_env, DEB_BUILD_PROFILES=" ".join(profiles))
            subprocess.run(make + ["-j1", "bindeb-pkg", "KBUILD_DEBARCH=arm64",
                                   "KDEB_SOURCENAME=linux-sp12",
                                   f"KDEB_PKGVERSION={package_version}"], check=True, env=package_env)
        release = subprocess.check_output(make + ["-s", "kernelrelease"], text=True).strip()
        verify(source, output, manifest, args.profile, candidate.ROOT)
        if expected_release and release != expected_release:
            raise ValueError("Completed kernel release differs from experiment manifest")
        if hashlib.sha256(args.manifest.read_bytes()).hexdigest() != manifest_hash:
            raise ValueError("Manifest changed during build")
        files = [output / "arch/arm64/boot/Image",
                 output / "arch/arm64/boot/dts/qcom/x1p42100-microsoft-sp12in.dtb",
                 output / ".config", output / "modules.order", output / "Module.symvers", output / "System.map"]
        if "vmlinuz.efi" in targets:
            files.append(output / "arch/arm64/boot/vmlinuz.efi")
        report = {
            "schema": 1, "status": "built-not-hardware-tested",
            "profile": args.profile, "base_commit": manifest["base_commit"],
            "source_tree": tree, "kernel_release": release,
            "build_timestamp": timestamp, "package_version": package_version,
            "manifest_sha256": manifest_hash,
            "inputs": [*candidate.selected_inputs(manifest, args.profile)[0],
                       candidate.selected_inputs(manifest, args.profile)[1]],
            "compiler": subprocess.check_output([f"{args.cross_compile}gcc", "--version"], text=True).splitlines()[0],
            "linker": subprocess.check_output([f"{args.cross_compile}ld", "--version"], text=True).splitlines()[0],
            "outputs": [{"path": str(p), "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                        for p in files],
            "remaining": ["package content/target installation inspection", "physical boot and rollback",
                          "hardware feature tests", "installer integration", "publication provenance"],
        }
        report["cross_headers"] = (
            "not packaged (--build-only)" if args.build_only else
            "not packaged; build and test headers natively with the same Module.symvers"
            if args.cross_compile else "native header package generated")
        (output / "sp12-buildinfo.json").write_text(json.dumps(report, indent=2) + "\n")
        print(f"Candidate build recorded in {output / 'sp12-buildinfo.json'}")
    except (KeyError, ValueError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Candidate build failed: {error}\n")


if __name__ == "__main__":
    main()
