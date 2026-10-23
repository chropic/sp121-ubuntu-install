#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Offline package/bundle tests; fixtures are not bootable kernels."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("installer_kernel", ROOT / "kernel/installer-kernel.py")
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


def fixture(directory, machine=183):
    tree = directory / "package"
    release = installer.RELEASE
    (tree / "DEBIAN").mkdir(parents=True, exist_ok=True)
    (tree / "DEBIAN/control").write_text(
        "Package: linux-image-" + release + "\nVersion: 7.3-1~sp12candidate1\n"
        "Architecture: arm64\nMaintainer: Offline test <test@example.invalid>\n"
        "Description: Nonbootable installer test fixture\n")
    boot = tree / "boot"
    boot.mkdir(exist_ok=True)
    image = bytearray(64)
    image[56:60] = b"ARMd"
    (boot / ("vmlinuz-" + release)).write_bytes(image)
    config = ROOT / "kernel/config/config-7.3-sp12-platform"
    (boot / ("config-" + release)).write_bytes(config.read_bytes())
    dtb = tree / ("usr/lib/linux-image-" + release) / installer.DTB
    dtb.parent.mkdir(parents=True, exist_ok=True)
    dtb.write_bytes(b"nonbootable DTB fixture")
    module = tree / ("lib/modules/" + release + "/kernel/fixture.ko")
    module.parent.mkdir(parents=True, exist_ok=True)
    elf = bytearray(64)
    elf[:6] = b"\x7fELF\x02\x01"
    elf[18:20] = machine.to_bytes(2, "little")
    module.write_bytes(elf)
    package = directory / "image.deb"
    subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(tree), str(package)],
                   stdout=subprocess.DEVNULL, check=True)
    manifest = ROOT / "kernel/ports/v7.3/manifest.json"
    info = {"schema": 1, "profile": "platform", "kernel_release": release,
            "package_version": "7.3-1~sp12candidate1", "base_commit": json.loads(manifest.read_text())["base_commit"],
            "manifest_sha256": installer.inspector.sha(manifest), "outputs": [
                {"path": name, "sha256": digest} for name, digest in [
                    ("Image", installer.inspector.sha(boot / ("vmlinuz-" + release))),
                    (".config", installer.inspector.sha(config)),
                    ("x1p42100-microsoft-sp12in.dtb", installer.inspector.sha(dtb))]]}
    build_info = directory / "buildinfo.json"
    build_info.write_text(json.dumps(info))
    return package, build_info


class InstallerKernelTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.package, self.build_info = fixture(self.directory)

    def test_platform_bundle_round_trip(self):
        args = type("Args", (), {"package": self.package, "build_info": self.build_info,
                                 "output": self.directory / "bundle"})()
        installer.bundle(args)
        report = installer.verify(args.output / "linux-image.deb", args.output / "buildinfo.json")
        self.assertEqual(json.loads((args.output / "inspection.json").read_text()), report)
        self.assertEqual({"183": 1}, report["package"]["module_machine_counts"])
        with self.assertRaises(FileExistsError):
            installer.bundle(args)

    def test_rejects_historical_or_camera_target(self):
        for release, profile in [("7.2.0-sp12-extra-camera", "platform"),
                                 ("7.3.0-sp12-v7.3-camera", "camera")]:
            info = json.loads(self.build_info.read_text())
            info.update(kernel_release=release, profile=profile)
            self.build_info.write_text(json.dumps(info))
            with self.assertRaisesRegex(ValueError, "maintained 7.3 platform"):
                installer.verify(self.package, self.build_info)

    def test_rejects_wrong_manifest_and_config(self):
        original = json.loads(self.build_info.read_text())
        for field in ["manifest", "config"]:
            info = json.loads(json.dumps(original))
            if field == "manifest":
                info["manifest_sha256"] = "0" * 64
            else:
                info["outputs"][1]["sha256"] = "0" * 64
            self.build_info.write_text(json.dumps(info))
            with self.assertRaises(ValueError):
                installer.verify(self.package, self.build_info)

    def test_rejects_foreign_modules(self):
        package, info = fixture(self.directory, machine=62)
        with self.assertRaisesRegex(ValueError, "non-AArch64"):
            installer.verify(package, info)

    def test_rejects_changed_kernel_payload(self):
        path = self.directory / ("package/boot/vmlinuz-" + installer.RELEASE)
        path.write_bytes(path.read_bytes() + b"changed")
        subprocess.run(["dpkg-deb", "--build", "--root-owner-group", str(self.directory / "package"),
                        str(self.package)], stdout=subprocess.DEVNULL, check=True)
        with self.assertRaisesRegex(ValueError, "image_matches"):
            installer.verify(self.package, self.build_info)

    def test_refuses_host_or_arbitrary_target_before_mutation(self):
        for target in [Path("/"), self.directory]:
            args = type("Args", (), {"target": target})()
            with self.assertRaisesRegex(ValueError, "separately mounted /target"):
                installer.install(args)

    def test_refuses_legacy_hooks_even_without_boot_conf(self):
        target = self.directory / "target"
        target.mkdir()
        installer.require_fresh_target(target)
        hook = target / "usr/local/sbin/sp12-sync-boot"
        hook.parent.mkdir(parents=True)
        hook.write_text("legacy hook")
        with self.assertRaisesRegex(ValueError, "Existing SP12 boot hook"):
            installer.require_fresh_target(target)
        hook.unlink()
        config = target / "etc/sp12-linux/boot.conf"
        config.parent.mkdir(parents=True)
        config.symlink_to("missing.conf")
        with self.assertRaises(ValueError):
            installer.require_fresh_target(target)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--fixture":
        fixture(Path(sys.argv[2]))
    else:
        unittest.main()
