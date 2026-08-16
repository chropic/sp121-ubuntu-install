# Install, configure, and maintain Linux on the Surface Pro 12

This is the single user guide for the Microsoft Surface Pro 12-inch, 1st
Edition with Snapdragon X Plus (`X1P42100`). It does not support Intel Surface
devices, Surface Pro 11, or a later Surface Pro 12 revision.

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

- another Linux computer with internet access and at least 10 GB free;
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
It adds only the machine-tested device tree and GRUB handoff, this repository's
tracked source archive, updated media checks, and build provenance to a new ISO.
The separately pinned Harrison support checkout is only needed for optional
post-install files; its third-party binaries are never included.

Clone this repository on the other Linux computer, then download Canonical's
official files:

```bash
git clone https://github.com/chropic/sp121-ubuntu-install.git sp12-linux
cd sp12-linux
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
Do not substitute the later installed `7.2.0~rc7-6` DTB; its compatibility with
Ubuntu's stock live kernel has not been established.

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
sudo apt install curl git gzip xorriso
cd ../..
ISO=build/installer-inputs/$ISO
DTB=build/installer-inputs/$DTB
scripts/build-installer \
  --iso "$ISO" \
  --iso-sha256 "$ISO_SHA256" \
  --dtb "$DTB" \
  --dtb-sha256 "$DTB_SHA256" \
  --output build/output/sp12-ubuntu-26.04-arm64.iso
(cd build/output && sha256sum -c sp12-ubuntu-26.04-arm64.iso.sha256)
```

The builder refuses existing outputs and dirty project checkouts. It verifies the
base ISO, inserts the DTB, adds the GRUB device-tree directive and
`stubble.dtb_override=true`, embeds only committed project files at
`/sp12-linux.tar.gz`, refreshes Ubuntu's media hashes, and trims xorriso write
padding so the backup GPT remains at the image's physical end.

Keep the ISO with its `.sha256` and `.buildinfo` sidecars. The same provenance is
embedded at `/sp12-buildinfo.txt`.

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
scripts/inspect-install-target \
  --target /target \
  --kernel-release YOUR_EXACT_KERNEL_RELEASE
```

Obtain `YOUR_EXACT_KERNEL_RELEASE` from the filename printed by
`ls /target/boot/vmlinuz-*`; do not guess it or use `uname -r`, which describes
the live environment. If either `findmnt` command or the inspection script fails,
stop, save `/var/log/installer`, and do not run the fallback installer. See the
[installer-error troubleshooting procedure](docs/troubleshooting/README.md#system-program-problem-detected-during-installation).

Preview construction of the fallback path:

```bash
scripts/install-fallback-target \
  --kernel-release YOUR_EXACT_KERNEL_RELEASE \
  --dtb-source /cdrom/casper/x1p42100-microsoft-sp12in.dtb
```

The command is dry-run-only unless `sudo` and `--apply` are deliberately added.
Its apply path still needs a physical live-install test before it is considered
release-supported. The script rejects unsafe mount layouts, non-FAT ESPs,
non-Ubuntu 26.04 roots, missing ARM64 GRUB modules or exact kernel files, and the
wrong hardware; it derives the root UUID from the mounted target. Its complete
design is documented in [the development notes](docs/DEVELOPMENT.md#installing-the-fallback-path-into-target).

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

## 5. Configure the first boot

After the installed system boots, inventory it:

```bash
cat /proc/device-tree/model
uname -r
lsblk
findmnt /boot/efi
ls -lh /boot/efi/EFI/BOOT/BOOTAA64.EFI /boot/efi/sp12/*
sudo scripts/sp12-verify
```

### Platform files

The tested installation placed Harrison van der Byl's support checkout at
`/opt/surface-pro-12-linux`. Do not copy an unpinned or unreviewed checkout into
`/lib`. Read [the firmware policy](firmware/README.md), inspect, and preview:

```bash
scripts/inspect-support-source --source /opt/surface-pro-12-linux
sudo scripts/install-platform-files --source /opt/surface-pro-12-linux
```

Both must end in `PASS` or `DRY RUN`. If you obtained the checkout legitimately
and accept its third-party terms:

```bash
sudo scripts/install-platform-files \
  --source /opt/surface-pro-12-linux \
  --apply --acknowledge-third-party-files
```

This installs only pinned `lib/firmware/qcom` and `usr/share/qcom` trees—not
Wi-Fi, audio topology/UCM, locally built sensors, services, or rules. Rebuild the
initramfs only for the exact kernel you will boot, then synchronize its matching
kernel/initramfs/DTB set.

### Wi-Fi

Do not use the original `fixwifi.sh`; it executes a moving `master` version of
`ath12k-bdencoder`. The replacement verifies an immutable encoder commit,
extracts the tested compatible entry from installed `board-2.bin`, verifies the
data, and previews by default:

```bash
sudo scripts/install-wifi-board
sudo scripts/install-wifi-board --apply
```

A different existing `board.bin` is preserved as `board.bin.before-sp12`; an
existing backup is never overwritten. After regenerating and synchronizing the
active initramfs, verify:

```bash
ls -lh /lib/firmware/ath12k/WCN7850/hw2.0/board.bin
ip link
```

### Audio

The tested topology comes from audioreach-topology `v1.0.4`, commit
`d7a5e9d80ad18a7a6844eeb32cacbdeea0e7e677`, and installs as:

```text
/lib/firmware/qcom/x1e80100/X1P42100-Microsoft-Surface-Pro-12in-tplg.bin
```

From a checkout at that revision, build and verify without installing:

```bash
sudo scripts/install-audio-topology \
  --source /opt/surface-pro-12-linux/audioreach-topology
```

Add `--apply` only when the tested hash is reported. It builds and installs only
the SP12 target, saves a different existing file as `.before-sp12`, and does not
change UCM. Ubuntu 26.04's `alsa-ucm-conf` predates corrected Surface routing:

```bash
sudo scripts/install-audio-ucm
sudo scripts/install-audio-ucm --apply
systemctl --user restart pipewire.service pipewire-pulse.service wireplumber.service
wpctl status
aplay -l
arecord -l
```

The installer verifies the pinned fix, uses `dpkg-divert`, and installs it mode
`0644`; mode `0600` caused the tested user-session failure. If logs contain
`bus clsh`, mute `SpkrLeft CPS` and `SpkrRight CPS` in `alsamixer`, then reboot.
Never remove kernel speaker-gain limits.

### Sensors

The tested stack uses `libssc`, Harrison's Hexagon RPC fork, and Harrison's IIO
Sensor Proxy fork. Its old installer cloned moving branches and is not the
reproducible public path. On an already configured system, check:

```bash
systemctl status hexagonrpc.service iio-sensor-proxy.service
monitor-sensor
```

Automatic brightness can be disabled without disabling the proxy, preserving
rotation and compass access. Exact pins, hashes, and remaining installer work are
in [the sensor-stack notes](docs/DEVELOPMENT.md#reproducible-sensor-stack).

## 6. Verify hardware

Run these tests after every kernel or DTB change; a DTB node is not a hardware
pass.

| Area | Command or test | Expected result / caution |
|---|---|---|
| Display/GPU | `glxinfo -B` | Direct rendering, Freedreno, Adreno X1-45 |
| Audio | `wpctl status`; `aplay -l`; `arecord -l` | Test playback and recording at conservative volume |
| Sensors | `monitor-sensor` while rotating and covering the light sensor | Accelerometer, ambient-light, and compass events |
| Video | `readlink -f /sys/bus/platform/devices/aa00000.video-codec/driver` | `qcom-iris`; install only firmware the kernel requests |
| Cameras | `media-ctl -p`; `v4l2-ctl --list-devices`; `ls -l /dev/video* /dev/media* 2>/dev/null` | Configure links only after CAMSS, CSIPHY/CSID/VFE, sensor, media, and video entities exist |

Inspect CPU frequency policies:

```bash
for policy in /sys/devices/system/cpu/cpufreq/policy*; do
    printf '%s cpus=%s driver=%s governor=%s min=%s max=%s\n' \
        "${policy##*/}" \
        "$(cat "$policy/affected_cpus")" \
        "$(cat "$policy/scaling_driver")" \
        "$(cat "$policy/scaling_governor")" \
        "$(cat "$policy/scaling_min_freq")" \
        "$(cat "$policy/scaling_max_freq")"
done
```

The tested system exposes policies for CPUs 0–3 and 4–7 after loading
`scmi_perf_domain` and `scmi_cpufreq`.

For experimental features: attach a USB-C DP/HDMI display before testing
DisplayPort audio; use `libinput debug-events` for volume buttons; save work and
prove multiple suspend/resume cycles; and inspect charge-limit attributes
read-only until their range is established.

## 7. Power and battery

The reference policy reduced one light active-discharge workload from about
13.5–13.8 W to a five-sample 5.08 W average; this is not a battery-life promise.
Preview, then deliberately apply:

```bash
scripts/install-power-policy
sudo scripts/install-power-policy --apply
```

It installs measured CPU/GPU limits, SCMI module loading, AC/battery event
handling, and the GNOME automatic-brightness override. Reference-owner USB
receiver and dock IDs are omitted; autosuspend external devices only after
testing wake, input, and networking.

```bash
systemctl is-enabled sp12-power-tune.service
systemctl show sp12-power-tune.service -p Result -p ExecMainStatus
cat /sys/devices/system/cpu/cpufreq/boost
cat /sys/class/devfreq/3d00000.gpu/min_freq
cat /sys/class/devfreq/3d00000.gpu/max_freq
cat /sys/module/pcie_aspm/parameters/policy
powerprofilesctl get
```

The successful `Type=oneshot` service normally becomes inactive; require
`Result=success` and `ExecMainStatus=0`. Do not add
`After=power-profiles-daemon.service`, which creates an ordering cycle because
that daemon starts after `multi-user.target`. For frequent AC use, prefer the
Surface UEFI battery-limit option; never write Linux thresholds reporting unknown
or zero ranges.

## 8. Update safely

Ordinary package updates are permitted, but the ESP payload remains pinned:

```bash
sudo apt update
sudo apt upgrade
uname -r
dpkg-query -W 'linux-image*' 'linux-headers*' 2>/dev/null
```

Never purge the running or retained recovery kernel. Avoid `-dbg` kernel packages
unless symbol debugging is intentional; they consume several gigabytes.

Changing the custom kernel means installing its exact image and headers,
generating its initramfs, choosing its matching DTB, updating both values in the
ESP sync configuration, synchronizing and comparing all three files, preserving
the previous recovery set, rebooting, and completing section 6. Generic APT
kernel symlinks must never choose the ESP payload automatically. See [the boot
synchronization design](docs/DEVELOPMENT.md#boot-synchronization).

## 9. Recover

Recovery is part of installation. If the previous kernel boots, confirm it with
`uname -r` and restore the matching kernel, initramfs, and DTB together—never one
file alone. The tested recovery set is:

```text
/boot/efi/sp12-recovery-panel/vmlinuz
/boot/efi/sp12-recovery-panel/initrd.img
/boot/efi/sp12-recovery-panel/dtb
```

Preview its paths and hashes, then apply only if correct:

```bash
scripts/sp12-restore-recovery
sudo scripts/sp12-restore-recovery --apply
```

The script validates the tablet and all three files, stages `.new` copies,
compares them, atomically renames the complete set, and returns the ESP read-only
even if interrupted.

If no installed kernel boots:

1. Power off, insert the tested installer USB, and boot with Volume Down + Power.
2. Run `scripts/sp12-preflight` in the live environment.
3. Identify and mount the Linux root and ESP.
4. Copy a matching recovery set to `/sp12/` on the ESP.
5. Sync writes and cleanly remount or unmount the ESP.

The installed recovery script cannot operate here. Live-USB target restoration
still needs a target-disk-validated workflow before it is novice-safe.

From any bootable environment, collect:

```bash
uname -a
cat /proc/device-tree/model
tr '\0' '\n' </proc/device-tree/compatible
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINTS,MODEL
journalctl -b -k --no-pager
```

Review logs for Wi-Fi names, UUIDs, hostnames, usernames, and other identifiers
before sharing them. The safer default is the redacted diagnostic report:

```bash
scripts/sp12-diagnostics --output ~/sp12-diagnostics.txt
```

For symptom-specific checks, see [Troubleshooting](docs/troubleshooting/README.md).
