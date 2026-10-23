# Configure the first boot

Start after the [installation checks](install.md) pass and the installed system boots.
Commands use the guarded repository snapshot at `/opt/sp12-linux`.

After the installed system boots, inventory it:

```bash
cat /proc/device-tree/model
uname -r
lsblk
findmnt /boot/efi
ls -lh /boot/efi/EFI/BOOT/BOOTAA64.EFI /boot/efi/sp12/*
sudo /opt/sp12-linux/scripts/sp12-verify
```

### Enable the Ubuntu package repositories

Have a tested wired USB Ethernet connection attached before relying on APT.
First inspect the installer-generated source state; do not delete or blindly
overwrite any source file:

```bash
find /etc/apt -maxdepth 2 -type f -print
sudo sed -n '1,160p' /etc/apt/sources.list 2>/dev/null || true
sudo sed -n '1,160p' /etc/apt/sources.list.d/cdrom.sources 2>/dev/null || true
sudo sed -n '1,160p' /etc/apt/sources.list.d/ubuntu.sources 2>/dev/null || true
sudo sed -n '1,160p' /etc/apt/sources.list.d/ubuntu.sources.curtin.orig 2>/dev/null || true
```

An active `cdrom.sources` can make APT request installation media. Preserve it
as a rollback copy while disabling it:

```bash
if test -f /etc/apt/sources.list.d/cdrom.sources; then
  sudo mv /etc/apt/sources.list.d/cdrom.sources \
    /etc/apt/sources.list.d/cdrom.sources.disabled
fi
```

If `ubuntu.sources` is absent but `ubuntu.sources.curtin.orig` exists, inspect
the template first. It must use only official Ubuntu archive/security HTTPS
URIs and suites for the installed Ubuntu codename reported by `/etc/os-release`.
Stop if the template is missing, names another release, or contains an
unexpected URI. Only then preserve the template and activate a copy:

```bash
. /etc/os-release
printf 'Installed codename: %s\n' "$VERSION_CODENAME"
sudo cat /etc/apt/sources.list.d/ubuntu.sources.curtin.orig
test ! -e /etc/apt/sources.list.d/ubuntu.sources
sudo cp -a /etc/apt/sources.list.d/ubuntu.sources.curtin.orig \
  /etc/apt/sources.list.d/ubuntu.sources
```

Review the active file again, confirm wired connectivity, and update package
metadata. Do not continue to package-dependent steps unless this succeeds:

```bash
sudo cat /etc/apt/sources.list.d/ubuntu.sources
ip route
sudo apt update
```

To roll back these source-file changes, remove only the copy created above (if
you created it), then restore the preserved CD-ROM source:

```bash
sudo rm -f /etc/apt/sources.list.d/ubuntu.sources
if test -f /etc/apt/sources.list.d/cdrom.sources.disabled; then
  sudo mv /etc/apt/sources.list.d/cdrom.sources.disabled \
    /etc/apt/sources.list.d/cdrom.sources
fi
```

### Platform files

The tested installation placed Harrison van der Byl's support checkout at
`/opt/surface-pro-12-linux`. Do not copy an unpinned or unreviewed checkout into
`/lib`. Read [the firmware policy](../firmware/README.md), inspect, and preview:

```bash
/opt/sp12-linux/scripts/inspect-support-source --source /opt/surface-pro-12-linux
sudo /opt/sp12-linux/scripts/install-platform-files --source /opt/surface-pro-12-linux
```

Both must end in `PASS` or `DRY RUN`. If you obtained the checkout legitimately
and accept its third-party terms:

```bash
sudo /opt/sp12-linux/scripts/install-platform-files \
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
sudo /opt/sp12-linux/scripts/install-wifi-board
sudo /opt/sp12-linux/scripts/install-wifi-board --apply
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
sudo /opt/sp12-linux/scripts/install-audio-topology \
  --source /opt/surface-pro-12-linux/audioreach-topology
```

Add `--apply` only when the tested hash is reported. It builds and installs only
the SP12 target, saves a different existing file as `.before-sp12`, and does not
change UCM. Ubuntu 26.04's `alsa-ucm-conf` predates corrected Surface routing:

```bash
sudo /opt/sp12-linux/scripts/install-audio-ucm
sudo /opt/sp12-linux/scripts/install-audio-ucm --apply
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
in [the sensor-stack notes](development.md#reproducible-sensor-stack).


Next: [verify hardware](hardware-tests.md) and review [maintenance](maintenance.md).
