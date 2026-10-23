# Install Ubuntu

This is the installation guide for the Microsoft Surface Pro 12-inch, 1st
Edition with Snapdragon X Plus (`X1P42100`). It does not support Intel Surface
devices, Surface Pro 11, or a later Surface Pro 12 revision.

The installed-system target is **7.3.0-sp12-v7.3-platform**, the sole maintained
kernel line and the project's main version. See the [support matrix](support.md)
for verified features and known issues.
The live session uses Canonical's stock Ubuntu kernel and a frozen compatible
bootstrap DTB. The installed target receives the separately verified 7.3 image,
modules and matching packaged DTB; these two boot paths use different DTBs.

> [!CAUTION]
> This repository builds a local installer from Canonical's stock Ubuntu 26.04
> ARM64 Desktop ISO; it does not distribute an ISO. The repository workflow has
> not yet passed a fresh end-to-end physical installation test. Installing an
> operating system can erase every file on the tablet.

## 1. Prepare and know when to stop

The intended installation creates Linux filesystems on the selected disk and a
fallback ARM64 bootloader on the EFI System Partition (ESP). The fallback loader
reads a fixed kernel, initramfs, and device tree from the FAT ESP, then mounts the
Linux root filesystem by UUID. An incorrect disk selection can destroy another
operating system and its data.

Before continuing, provide:

- another Linux computer with internet access and enough disk-backed space for
  the [kernel build](../kernel/ports/v7.3/README.md) and installer inputs;
- the Surface charger and a reliable USB installer drive;
- a separate, verified backup/recovery drive that is detached while partitioning;
- a USB keyboard if the Type Cover is unavailable in the live environment;
- Microsoft recovery media and the saved BitLocker recovery key if Windows must
  remain recoverable.

Verify the backup by opening several files from it. Stop immediately if:

- `scripts/sp12-preflight` reports the wrong model or architecture;
- the internal UFS disk is not visible;
- the installer cannot mount its target root and ESP;
- any download checksum does not match;
- any command names a disk you did not intentionally select;
- the known-good recovery files have not been preserved; or
- power is unreliable.

Do not “try anyway.” A missing UFS device or mismatched DTB is a platform
problem, not an installer prompt to click through.

Current limits: Secure Boot is disabled in the tested setup; hibernate is not
validated; camera nodes do not prove capture works; suspend needs repeated tests
with saved work; and Linux charge-threshold attributes must remain untouched
until their meaning and valid range are known.

## 2. Build the installer

The builder leaves the downloaded ISO unchanged and never writes a USB drive.
It adds the frozen bootstrap device tree and GRUB handoff, a verified 7.3 target
image package/build record, this repository's tracked source archive, updated
media checks, and build provenance to a new ISO.
The separately pinned Harrison support checkout is only needed for optional
post-install files; its third-party binaries are never included.

Clone this repository on the other Linux computer, then download Canonical's
official files:

```bash
git clone https://github.com/chropic/sp121-ubuntu-install.git sp12-linux
cd sp12-linux
```

First complete the [7.3 platform build recipe](../kernel/ports/v7.3/README.md#reproduce-preparation-and-builds).
For that recipe's paths, verify these generated inputs exist:

```bash
KERNEL_PACKAGE=/var/tmp/sp12-kernel/linux-image-7.3.0-sp12-v7.3-platform_7.3-1~sp12candidate1_arm64.deb
KERNEL_BUILD_INFO=/var/tmp/sp12-kernel/reproduce-build-7.3-platform/sp12-buildinfo.json
test -f "$KERNEL_PACKAGE" && test -f "$KERNEL_BUILD_INFO"
mkdir -p build/installer-inputs build/output
cd build/installer-inputs
curl -fLO https://cdimage.ubuntu.com/releases/26.04/release/SHA256SUMS
curl -fLO https://cdimage.ubuntu.com/releases/26.04/release/SHA256SUMS.gpg
curl -fLO https://cdimage.ubuntu.com/releases/26.04/release/ubuntu-26.04-desktop-arm64.iso
```

Authenticate Canonical's checksum metadata, then verify the ISO:

```bash
gpgv --keyring /usr/share/keyrings/ubuntu-archive-keyring.gpg \
  SHA256SUMS.gpg SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing
```

The first command must report a good signature from the Ubuntu CD Image signing
key, and the second must report `ubuntu-26.04-desktop-arm64.iso: OK`. If the
keyring is unavailable, stop and follow [Canonical's image-verification
procedure](https://documentation.ubuntu.com/security/software-integrity/image-verification/).
Never replace the expected hash with one calculated from an unverified download.

Capture the authenticated hash. For the initial Ubuntu 26.04 ARM64 Desktop
release it is
`c2afd538d66fdd77377d03f1ed2ac76a34f1c116baecc9a8170d68f833121f57`.

```bash
ISO=ubuntu-26.04-desktop-arm64.iso
ISO_SHA256=$(awk -v name="*$ISO" '$2 == name { print $1 }' SHA256SUMS)
test "${#ISO_SHA256}" -eq 64
```

Download the machine-tested live-installer DTB from the pinned support commit.
Do not substitute the installed 7.3 DTB into this stock live boot path. The
installed target will use the DTB contained in the matching 7.3 package.

```bash
curl -fL \
  -o x1p42100-microsoft-sp12in.dtb \
  https://raw.githubusercontent.com/harrisonvanderbyl/surface-pro-12-inch-linux/ea0f07e66beea95898d96fbeb6daa472f4735af3/boot/dtb
DTB=x1p42100-microsoft-sp12in.dtb
DTB_SHA256=d7ed4b073c7344cb0bb2c3f7d00655df60b473588a5c0364af54537dc2c672c7
printf '%s  %s\n' "$DTB_SHA256" "$DTB" | sha256sum -c -
```

Stop unless it reports `OK`. Install the local requirements on Ubuntu or Debian,
return to the repository root, and build:

```bash
sudo apt install curl git gzip xorriso python3 dpkg zstd
cd ../..
ISO=build/installer-inputs/$ISO
DTB=build/installer-inputs/$DTB
scripts/build-installer \
  --iso "$ISO" \
  --iso-sha256 "$ISO_SHA256" \
  --dtb "$DTB" \
  --dtb-sha256 "$DTB_SHA256" \
  --kernel-package "$KERNEL_PACKAGE" \
  --kernel-build-info "$KERNEL_BUILD_INFO" \
  --output build/output/sp12-ubuntu-26.04-arm64.iso
(cd build/output && sha256sum -c sp12-ubuntu-26.04-arm64.iso.sha256)
```

The builder refuses existing outputs and dirty project checkouts. It verifies the
base ISO, inserts the DTB, adds the GRUB device-tree directive and
`stubble.dtb_override=true`, embeds only committed project files at
`/sp12-linux.tar.gz`, refreshes Ubuntu's media hashes, and trims xorriso write
padding so the backup GPT remains at the image's physical end.

Keep the ISO with its `.sha256` and `.buildinfo` sidecars. The same provenance is
embedded at `/sp12-buildinfo.txt`. The target bundle at `/sp12-kernel/` contains
the exact image package, build information and inspection report. The builder
checks the reviewed platform configuration, source manifest, ARM64 module
architecture and image/DTB hashes; 7.2 and camera target packages are rejected.
This does not replace a physical live-boot/installation test.

## 3. Write and boot the USB

USB writing is deliberately not automated. Use a graphical imaging tool that
shows the drive manufacturer and capacity, eject cleanly, reconnect it, and
verify that its partitions are readable.

1. With the Surface off, hold **Volume Up** while pressing Power to enter UEFI.
2. Record the original Secure Boot setting, disable Secure Boot for this unsigned
   path, and enable USB boot.
3. Power off, insert the USB, connect power, then hold **Volume Down** while
   pressing Power.
4. In the live environment, open Terminal and run:

   ```bash
   mkdir -p /tmp/sp12-linux
   tar -xzf /cdrom/sp12-linux.tar.gz -C /tmp/sp12-linux
   cd /tmp/sp12-linux
   scripts/sp12-preflight
   ```

Continue only if the final line is:

```text
RESULT: PASS -- supported Surface Pro 12 hardware detected
```

## 4. Install Linux and prepare boot

This section records the intended checkpoints while post-install automation is
still being developed. Before opening the installer, run:

```bash
cat /proc/device-tree/model
tr '\0' '\n' </proc/device-tree/compatible
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINTS,MODEL
```

Expected device-tree values include:

```text
Surface Pro 12in 1st Edition
microsoft,surface-pro-12in
qcom,x1p42100
```

The internal UFS storage must appear in `lsblk`. The tested initial installation
used the entire internal disk without encryption, which is destructive. Dual
boot will be documented only after a tested partition-preservation and recovery
procedure exists. Record the internal disk's name, model/manufacturer, and size;
confirm all three in the graphical installer's final summary.

The ordinary installer can copy Linux successfully yet fail to create a usable
Surface boot entry. On the Surface firmware, Ubuntu 26.04's installer may show
**System Program Problem Detected** near the end because `efibootmgr -v` reports
`EFI variables are not supported on this system`; curtin currently treats that
response as a fatal bootloader error. Do not restart the installer or reboot.
The target may already contain the copied system, kernel, initramfs, ARM64 GRUB
modules, and mounted ESP, but the error dialog alone does not establish that all
of them are present. Open a live-session terminal and confirm the target and ESP:

```bash
findmnt /target
findmnt /target/boot/efi
test -f /target/etc/os-release && cat /target/etc/os-release
ls -la /target/boot
scripts/inspect-install-target --target /target
scripts/install-kernel-target
```

The kernel helper previews the verified 7.3 bundle and accepts only a separately
mounted Ubuntu 26.04 `/target`. It never chooses a generic kernel from symlinks
or a wildcard. `uname -r` describes the stock live environment. If either `findmnt`
command or the inspection script fails,
stop, save `/var/log/installer`, and do not run the fallback installer. See the
[installer-error troubleshooting procedure](troubleshooting/README.md#system-program-problem-detected-during-installation).

After reviewing the dry run, install the target kernel:

```bash
sudo scripts/install-kernel-target --apply
KVER=7.3.0-sp12-v7.3-platform
scripts/inspect-install-target --target /target --kernel-release "$KVER"
```

This runs package hooks inside the native ARM64 target, regenerates its initramfs,
checks required storage/display module dependencies and exact payload hashes,
then copies the package's matching DTB to `/target/boot/dtb-$KVER`. It does not
select an ESP payload. Stop on any failure; target installation is not atomic,
and a failed package/initramfs step needs inspection before fallback setup.

Preview construction of the fallback path:

```bash
scripts/install-fallback-target \
  --kernel-release "$KVER" \
  --dtb-source /target/boot/dtb-$KVER
```

The command is dry-run-only unless `sudo` and `--apply` are deliberately added.
Its apply path still needs a physical live-install test before it is considered
release-supported. The script rejects unsafe mount layouts, non-FAT ESPs,
non-Ubuntu 26.04 roots, missing ARM64 GRUB modules or exact kernel files, and the
wrong hardware; it derives the root UUID from the mounted target. Its complete
design is documented in [the development notes](development.md#installing-the-fallback-path-into-target).

After checking the preview, install the fallback path and a clean, root-owned
snapshot of this repository at the stable target location `/opt/sp12-linux`:

```bash
sudo scripts/install-fallback-target \
  --kernel-release "$KVER" \
  --dtb-source /target/boot/dtb-$KVER \
  --apply
```

Before rebooting, verify the first-boot tools were copied into the installed
system and kept executable. No additional Wi-Fi, audio, sensor, or platform
firmware is required merely to attempt the first boot; install those components
later from the installed system when their documented prerequisites are
available. These checks must all pass with the same exact kernel release used
above:

```bash
findmnt /target
findmnt /target/boot/efi
test -f /target/boot/vmlinuz-$KVER
test -f /target/boot/initrd.img-$KVER
test -f /target/boot/dtb-$KVER
test -f /target/boot/efi/EFI/BOOT/BOOTAA64.EFI
test -f /target/boot/efi/sp12/SP12BOOT
cmp -s /target/boot/vmlinuz-$KVER /target/boot/efi/sp12/vmlinuz
cmp -s /target/boot/initrd.img-$KVER /target/boot/efi/sp12/initrd.img
cmp -s /target/boot/dtb-$KVER /target/boot/efi/sp12/dtb
grep -Fx "KVER=$KVER" /target/etc/sp12-linux/boot.conf
grep -Fx "DTB=/boot/dtb-$KVER" /target/etc/sp12-linux/boot.conf
test -x /target/opt/sp12-linux/scripts/sp12-verify
test -x /target/opt/sp12-linux/scripts/install-platform-files
test -x /target/opt/sp12-linux/scripts/install-wifi-board
test -x /target/opt/sp12-linux/scripts/install-audio-topology
test -x /target/opt/sp12-linux/scripts/install-audio-ucm
test -x /target/opt/sp12-linux/scripts/install-power-policy
test -x /target/opt/sp12-linux/scripts/sp12-restore-recovery
test -x /target/opt/sp12-linux/scripts/sp12-diagnostics
test ! -e /target/opt/sp12-linux/.git
```

### Boot design

```text
Surface UEFI
  -> FAT ESP: /EFI/BOOT/BOOTAA64.EFI
  -> FAT ESP: /sp12/vmlinuz
  -> FAT ESP: /sp12/initrd.img
  -> FAT ESP: /sp12/dtb
  -> Linux root filesystem, selected by UUID
```

This avoids EFI NVRAM entries and GRUB reading ext4. The three `/sp12/` files are
an inseparable release set. The ESP is normally read-only; updates stage `.new`
files, compare them byte-for-byte, rename them into place, sync storage, and
restore read-only mode. The fallback path is deliberately independent of EFI
variables. This is why the late installer error can be recoverable, but only when
all of the preceding target checks pass.


Continue with [first-boot setup](first-boot.md), then run the
[hardware checks](hardware-tests.md). Keep the [recovery procedure](recovery.md)
available on a separate device.
