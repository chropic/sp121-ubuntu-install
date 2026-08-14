# First boot

## Basic inventory

After the installed system boots, run:

```bash
cat /proc/device-tree/model
uname -r
lsblk
findmnt /boot/efi
ls -lh /boot/efi/EFI/BOOT/BOOTAA64.EFI /boot/efi/sp12/*
```

Then run:

```bash
sudo scripts/sp12-verify
```

## Platform support files

The tested installation placed Harrison van der Byl's support checkout at:

```text
/opt/surface-pro-12-linux
```

Its `lib/` tree supplies device-specific firmware and configuration. Do not copy
files from an unpinned or unreviewed checkout into `/lib`. This project pins the
tested checkout and restricts installation to two committed subtrees.

First inspect it and preview the installation:

```bash
scripts/inspect-support-source --source /opt/surface-pro-12-linux
sudo scripts/install-platform-files --source /opt/surface-pro-12-linux
```

Both commands must end in `PASS` or `DRY RUN`. The preview does not write. Read
[`../firmware/README.md`](../firmware/README.md), review the third-party terms,
and then apply only if you obtained the checkout legitimately:

```bash
sudo scripts/install-platform-files \
  --source /opt/surface-pro-12-linux \
  --apply --acknowledge-third-party-files
```

This installs only the pinned `lib/firmware/qcom` and `usr/share/qcom` trees. It
does not install Wi-Fi, the audio topology or UCM override, locally built sensor
programs, services, or rules. Rebuild the initramfs only for the exact kernel you
intend to boot and synchronize its matching kernel/initramfs/DTB set afterward.

## Wi-Fi

The original `fixwifi.sh` downloads and executes the moving `master` version of
`ath12k-bdencoder`. Do **not** use it in a reproducible installation. Preview the
pinned, checksum-verifying replacement instead:

```bash
sudo scripts/install-wifi-board
```

It downloads the encoder from an immutable commit, verifies the encoder, extracts
the tested compatible entry from the installed `board-2.bin` bundle, and verifies
the extracted data. It does not install during the preview. If every check passes:

```bash
sudo scripts/install-wifi-board --apply
```

An existing, different `board.bin` is preserved as `board.bin.before-sp12`; the
script refuses to overwrite an existing backup.

After regenerating and synchronizing the exact active initramfs, verify:

```bash
ls -lh /lib/firmware/ath12k/WCN7850/hw2.0/board.bin
ip link
```

## Audio

The tested topology was built from audioreach-topology `v1.0.4`, commit
`d7a5e9d80ad18a7a6844eeb32cacbdeea0e7e677`. The expected installed file is:

```text
/lib/firmware/qcom/x1e80100/X1P42100-Microsoft-Surface-Pro-12in-tplg.bin
```

Given a checkout at that exact revision, build and verify it without installing:

```bash
sudo scripts/install-audio-topology \
  --source /opt/surface-pro-12-linux/audioreach-topology
```

If it reports that the tested hash was built, add `--apply`. This tool builds only
the SP12 topology target, installs only that one output, and preserves a different
existing file as `.before-sp12`. It does not modify ALSA UCM configuration.

Ubuntu 26.04's `alsa-ucm-conf` predates the corrected Surface routing. Preview the
pinned upstream fix:

```bash
sudo scripts/install-audio-ucm
```

If its checksum passes, add `--apply`. The installer uses `dpkg-divert` to preserve
and protect the package-owned configuration, installs mode `0644`, and makes no
other ALSA changes. Restart the user audio services only after installation:

```bash
systemctl --user restart pipewire.service pipewire-pulse.service wireplumber.service
wpctl status
aplay -l
arecord -l
```

The Surface UCM file must be world-readable (`0644`) so the user audio session can
load it. Mode `0600` caused the tested practical audio failure.

If kernel logs contain `bus clsh`, open `alsamixer`, mute `SpkrLeft CPS` and
`SpkrRight CPS`, then reboot. Do not remove the kernel's speaker gain limits.

## Sensors

The tested stack uses `libssc`, Harrison's Hexagon RPC fork, and Harrison's IIO
Sensor Proxy fork. Their old installer cloned moving branches and is not yet the
reproducible public installation path. On an already configured system, confirm:

```bash
systemctl status hexagonrpc.service iio-sensor-proxy.service
monitor-sensor
```

Automatic brightness may be disabled without disabling the sensor proxy; that
preserves display rotation and compass access.

The exact source pins, versions, live artifact hashes, and remaining replacement
installer requirements are documented in
[`development/sensor-stack.md`](development/sensor-stack.md).
