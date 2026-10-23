#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Inspect candidate Debian packages without installing them or running hooks."""

import argparse
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import subprocess
import tarfile


def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def elf_machine(data):
    if data[:4] != b"\x7fELF":
        return None
    return int.from_bytes(data[18:20], "little" if data[5] == 1 else "big")


def inspect(package, release, image_hash, config_hash, dtb_hash, symbols_hash=None):
    fields = ["Package", "Version", "Architecture", "Depends"]
    metadata = {}
    for field in fields:
        metadata[field] = subprocess.check_output(
            ["dpkg-deb", "--field", str(package), field], text=True).strip()
    issues = []
    if metadata["Architecture"] != "arm64":
        issues.append("Package architecture is not arm64")
    result = {"file": package.name, "sha256": sha(package), "size_bytes": package.stat().st_size,
              "metadata": metadata, "issues": issues, "module_count": 0,
              "module_machine_counts": {}, "foreign_header_tools": [], "native_header_tool_count": 0}
    process = subprocess.Popen(["dpkg-deb", "--fsys-tarfile", str(package)], stdout=subprocess.PIPE)
    with tarfile.open(fileobj=process.stdout, mode="r|") as archive:
        for member in archive:
            if not member.isfile():
                continue
            name = member.name.removeprefix("./")
            stream = archive.extractfile(member)
            if name == f"boot/vmlinuz-{release}":
                prefix = stream.read(4096)
                pe_offset = int.from_bytes(prefix[60:64], "little")
                pe_arm64 = (prefix[:2] == b"MZ" and
                            prefix[pe_offset:pe_offset + 6] == b"PE\x00\x00\x64\xaa")
                result["arm64_image_magic"] = prefix[56:60] == b"ARMd" or pe_arm64
                result["boot_image_format"] = "arm64-pe-coff" if pe_arm64 else "arm64-linux-image"
                digest = hashlib.sha256(prefix)
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
                result["image_matches"] = digest.hexdigest() == image_hash
            elif name == f"boot/config-{release}":
                result["config_matches"] = hashlib.sha256(stream.read()).hexdigest() == config_hash
            elif name.endswith("/qcom/x1p42100-microsoft-sp12in.dtb"):
                data = stream.read()
                result["dtb"] = {"path": name, "matches": hashlib.sha256(data).hexdigest() == dtb_hash}
            elif f"lib/modules/{release}/" in name and ".ko" in name:
                data = stream.read() if name.endswith((".gz", ".xz", ".zst")) else stream.read(64)
                if name.endswith(".gz"):
                    data = gzip.decompress(data)
                elif name.endswith(".xz"):
                    data = lzma.decompress(data)
                elif name.endswith(".zst"):
                    data = subprocess.check_output(["zstd", "-d", "-q", "-c"], input=data)
                machine = elf_machine(data)
                result["module_count"] += 1
                key = str(machine)
                result["module_machine_counts"][key] = result["module_machine_counts"].get(key, 0) + 1
            elif metadata["Package"].startswith("linux-headers-"):
                if name == f"usr/src/linux-headers-{release}/Module.symvers":
                    result["header_symbols_match"] = hashlib.sha256(stream.read()).hexdigest() == symbols_hash
                elif name == f"usr/src/linux-headers-{release}/include/config/kernel.release":
                    result["header_release_matches"] = stream.read().decode().strip() == release
                machine = elf_machine(stream.read(64))
                if machine == 183:
                    result["native_header_tool_count"] += 1
                if machine is not None and machine != 183:
                    result["foreign_header_tools"].append({"path": name, "elf_machine": machine})
    returncode = process.wait()
    process.stdout.close()
    if returncode != 0:
        raise ValueError(f"Unable to read package: {package}")
    if metadata["Package"].startswith("linux-image-") and not metadata["Package"].endswith("-dbg"):
        for field in ["arm64_image_magic", "image_matches", "config_matches"]:
            if not result.get(field):
                issues.append(f"Missing or mismatched image payload: {field}")
        if not result.get("dtb", {}).get("matches"):
            issues.append("Missing or mismatched SP12 DTB")
        if not result["module_count"] or set(result["module_machine_counts"]) != {"183"}:
            issues.append("Module payload is missing or contains non-AArch64 ELF")
    if result["foreign_header_tools"]:
        issues.append("Cross-built headers contain host ELF tools; hold this package pending target-tool repair/native rebuild")
    if metadata["Package"].startswith("linux-headers-"):
        if not symbols_hash or not result.get("header_symbols_match"):
            issues.append("Header Module.symvers is missing or differs from the completed kernel build")
        if not result.get("header_release_matches") or not result["native_header_tool_count"]:
            issues.append("Header package lacks the expected release or native AArch64 build tools")
    result["status"] = "hold" if issues else "passed-static-package-inspection"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-info", type=Path, required=True)
    parser.add_argument("--package", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build = json.loads(args.build_info.read_text())
    outputs = {Path(item["path"]).name: item["sha256"] for item in build["outputs"]}
    image_hash = outputs.get("vmlinuz.efi", outputs["Image"])
    results = [inspect(package.resolve(strict=True), build["kernel_release"], image_hash, outputs[".config"],
                       outputs["x1p42100-microsoft-sp12in.dtb"], outputs.get("Module.symvers")) for package in args.package]
    report = {"schema": 1, "kernel_release": build["kernel_release"], "packages": results,
              "target_installation": "not-run", "target_initramfs": "not-generated-or-inspected",
              "hardware": "not-run", "installer": "unchanged"}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Inspected {len(results)} packages; report: {args.output}")
    if any(result["issues"] for result in results):
        parser.exit(1, "One or more packages are held; inspect the report before target installation.\n")


if __name__ == "__main__":
    main()
