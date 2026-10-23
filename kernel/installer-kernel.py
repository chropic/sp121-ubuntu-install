#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Verify the maintained 7.3 platform package and prepare a mounted install target."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
RELEASE = "7.3.0-sp12-v7.3-platform"
DTB = "qcom/x1p42100-microsoft-sp12in.dtb"
REQUIRED = ["ufs_qcom", "phy_qcom_qmp_ufs", "pinctrl_x1e80100", "gcc_x1e80100",
            "qnoc_x1e80100", "qcom_rpmh_regulator", "msm", "panel_edp"]
spec = importlib.util.spec_from_file_location("inspect_candidate", ROOT / "kernel/inspect-candidate.py")
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify(package, build_info):
    build = json.loads(build_info.read_text())
    manifest_path = ROOT / "kernel/ports/v7.3/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    require(build.get("kernel_release") == RELEASE and build.get("profile") == "platform",
            "Installer target must be the maintained 7.3 platform profile")
    require(build.get("base_commit") == manifest["base_commit"], "Wrong kernel base")
    require(build.get("manifest_sha256") == inspector.sha(manifest_path), "Build manifest mismatch")
    outputs = {Path(item["path"]).name: item["sha256"] for item in build["outputs"]}
    require(outputs[".config"] == manifest["profiles"]["platform"]["config"]["sha256"],
            "Build does not use the reviewed platform configuration")
    image_hash = outputs.get("vmlinuz.efi", outputs["Image"])
    result = inspector.inspect(package, RELEASE, image_hash, outputs[".config"],
                               outputs["x1p42100-microsoft-sp12in.dtb"])
    require(result["metadata"]["Package"] == "linux-image-" + RELEASE,
            "Expected the exact platform image package")
    require(result["metadata"]["Version"] == build["package_version"], "Package/build version mismatch")
    require(not result["issues"], "Package inspection failed: " + "; ".join(result["issues"]))
    result["file"] = "linux-image.deb"  # Stable bundle name, independent of the build directory.
    return {"schema": 1, "kernel_release": RELEASE, "profile": "platform", "package": result,
            "build_info_sha256": inspector.sha(build_info), "image_sha256": image_hash,
            "config_sha256": outputs[".config"], "dtb_sha256": outputs["x1p42100-microsoft-sp12in.dtb"]}


def bundle(args):
    report = verify(args.package.resolve(strict=True), args.build_info.resolve(strict=True))
    args.output.mkdir()  # A fresh directory prevents mixed or overwritten bundles.
    for source, name in [(args.package, "linux-image.deb"), (args.build_info, "buildinfo.json")]:
        shutil.copyfile(source, args.output / name)
    require(inspector.sha(args.output / "linux-image.deb") == report["package"]["sha256"],
            "Package changed during bundle creation")
    require(inspector.sha(args.output / "buildinfo.json") == report["build_info_sha256"],
            "Build information changed during bundle creation")
    (args.output / "inspection.json").write_text(json.dumps(report, indent=2) + "\n")
    print("Verified installer target bundle: " + RELEASE)


def require_fresh_target(target):
    for relative in ["etc/sp12-linux/boot.conf", "usr/local/sbin/sp12-sync-boot",
                     "etc/kernel/postinst.d/zzzz-sp12-sync",
                     "etc/initramfs/post-update.d/zzzz-sp12-sync"]:
        path = target / relative
        require(not path.exists() and not path.is_symlink(),
                "Existing SP12 boot hook/configuration: use installed-system maintenance instead")


def install(args):
    target = args.target.resolve(strict=True)
    require(str(target) == "/target", "Only the separately mounted /target is accepted")
    subprocess.run([str(ROOT / "scripts/inspect-install-target"), "--target", str(target)], check=True)
    package = args.bundle / "linux-image.deb"
    report = verify(package.resolve(strict=True), (args.bundle / "buildinfo.json").resolve(strict=True))
    saved = json.loads((args.bundle / "inspection.json").read_text())
    require(saved == report, "Bundle inspection does not match the supplied package/build information")
    require_fresh_target(target)
    for tool in ["dpkg", "modinfo", "modprobe", "lsinitramfs", "update-initramfs"]:
        require(any((target / directory / tool).is_file() for directory in
                    ["usr/bin", "usr/sbin", "bin", "sbin"]), "Target lacks " + tool)
    print("Target kernel: " + RELEASE)
    print("Package SHA-256: " + report["package"]["sha256"])
    print("Target DTB: /target/boot/dtb-" + RELEASE)
    if not args.apply:
        print("DRY RUN: no target or ESP files changed")
        return
    require(os.geteuid() == 0, "--apply requires root")
    require(os.uname().machine == "aarch64", "Native ARM64 live environment required")
    for relative in ["tmp", "boot", "dev", "proc", "sys"]:
        require(not (target / relative).is_symlink(), "Refusing symlinked target " + relative)
    mounted = []
    with tempfile.TemporaryDirectory(prefix="sp12-kernel-", dir=target / "tmp") as temporary:
        temporary = Path(temporary)
        copied = temporary / "linux-image.deb"
        shutil.copyfile(package, copied)
        require(inspector.sha(copied) == report["package"]["sha256"], "Staged package mismatch")
        try:
            for source in ["/dev", "/proc", "/sys"]:
                destination = target / source.lstrip("/")
                destination.mkdir(exist_ok=True)
                if subprocess.run(["mountpoint", "-q", str(destination)]).returncode:
                    subprocess.run(["mount", "--rbind", source, str(destination)], check=True)
                    mounted.append(destination)
                    subprocess.run(["mount", "--make-rslave", str(destination)], check=True)
            environment = dict(os.environ, DEBIAN_FRONTEND="noninteractive", SYSTEMD_OFFLINE="1")
            inside = "/" + str(copied.relative_to(target))
            subprocess.run(["chroot", str(target), "dpkg", "--install", inside], env=environment, check=True)
            subprocess.run(["chroot", str(target), "update-initramfs", "-u", "-k", RELEASE],
                           env=environment, check=True)
            for path, expected in [(target / ("boot/vmlinuz-" + RELEASE), report["image_sha256"]),
                    (target / ("boot/config-" + RELEASE), report["config_sha256"]),
                    (target / ("usr/lib/linux-image-" + RELEASE) / DTB, report["dtb_sha256"])]:
                require(not path.is_symlink() and inspector.sha(path) == expected,
                        "Installed payload mismatch: " + str(path))
            listing = subprocess.check_output(["chroot", str(target), "lsinitramfs",
                       "/boot/initrd.img-" + RELEASE], text=True)
            names = {line.removeprefix("./").removeprefix("usr/").rstrip("/") for line in listing.splitlines()}
            releases = {p.split("/")[2] for p in names if p.startswith("lib/modules/") and len(p.split("/")) > 2}
            require(releases == {RELEASE}, "Unexpected initramfs module release set")
            for module in REQUIRED:
                version = subprocess.check_output(["chroot", str(target), "modinfo", "-k", RELEASE,
                                                   "-F", "vermagic", module], text=True).split()[0]
                require(version == RELEASE, "Wrong module release: " + module)
                deps = subprocess.check_output(["chroot", str(target), "modprobe", "--show-depends",
                                               "--set-version", RELEASE, module], text=True)
                for line in deps.splitlines():
                    if line.startswith("insmod "):
                        require(line.split()[1].lstrip("/").removeprefix("usr/") in names,
                                "Required module absent from initramfs: " + module)
            destination = target / ("boot/dtb-" + RELEASE)
            require(not destination.is_symlink(), "Refusing symlinked target DTB")
            if destination.exists():
                require(inspector.sha(destination) == report["dtb_sha256"], "Existing target DTB differs")
            else:
                shutil.copyfile(target / ("usr/lib/linux-image-" + RELEASE) / DTB, destination)
                destination.chmod(0o644)
            require(inspector.sha(destination) == report["dtb_sha256"], "Installed DTB copy mismatch")
        finally:
            for destination in reversed(mounted):
                subprocess.run(["umount", "--recursive", str(destination)], check=True)
    print("7.3 target image, modules, initramfs and DTB verified; ESP selection has not been changed.")
    print("Next: scripts/install-fallback-target --dtb-source /target/boot/dtb-" + RELEASE)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("bundle")
    create.add_argument("--package", type=Path, required=True)
    create.add_argument("--build-info", type=Path, required=True)
    create.add_argument("--output", type=Path, required=True)
    target = sub.add_parser("install")
    target.add_argument("--bundle", type=Path, default=Path("/cdrom/sp12-kernel"))
    target.add_argument("--target", type=Path, default=Path("/target"))
    target.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        (bundle if args.command == "bundle" else install)(args)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, str(error) + "\n")


if __name__ == "__main__":
    main()
