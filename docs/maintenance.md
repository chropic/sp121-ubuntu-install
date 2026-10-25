# Maintain the system and fix problems

The main configuration is Ubuntu 26.10 with custom kernel
`7.3.0-sp12-v7.3-platform`. Fresh installation and recovery on 26.10 remain
experimental. Older installed-system tests are not new 26.10 installation passes.

Commands below use the installed project snapshot at `/opt/sp12-linux`.
If it is missing, return to the [installation guide](install.md) rather than
running commands from an unknown checkout as root.

## First boot

```bash
uname -r
cat /etc/os-release
findmnt /boot/efi
sudo /opt/sp12-linux/scripts/sp12-verify
```

Expect the custom 7.3 kernel, Ubuntu 26.10, and matching kernel, initramfs and
DTB files on the EFI System Partition (ESP). Stop on a failed check.
The live image's private device files are not automatically installed.

## Package sources

If APT asks for the installation USB, inspect its source files first:

```bash
find /etc/apt -maxdepth 2 -type f -print
cat /etc/os-release
sudo cat /etc/apt/sources.list.d/ubuntu.sources
sudo cat /etc/apt/sources.list.d/cdrom.sources
```

A missing file may be normal. Do not delete or replace all APT sources.
If `cdrom.sources` is active, preserve it by renaming it to
`cdrom.sources.disabled`, only if that destination does not already exist.
If `ubuntu.sources` is missing, inspect `ubuntu.sources.curtin.orig` before
copying it. It must name the installed Ubuntu release and official Ubuntu
archive/security servers. Stop if it is missing, names another release, or
uses an unknown server. Keep each original file so the change can be reversed.

Once the sources and network connection are correct:

```bash
sudo apt update
```

Stop if it fails. Do not replace the release name in APT files to force a
release upgrade. The [26.04 legacy notes](legacy-26.04.md) cover that separate path.

## Device files and Wi-Fi

Some devices need extra firmware: files loaded by a driver to operate hardware.
Read the [device-file policy](../firmware/README.md) before using the pinned
support checkout. Inspect it and preview the copy:

```bash
/opt/sp12-linux/scripts/inspect-support-source --source /opt/surface-pro-12-linux
sudo /opt/sp12-linux/scripts/install-platform-files --source /opt/surface-pro-12-linux
```

Only after the source checks pass and you accept its terms:

```bash
sudo /opt/sp12-linux/scripts/install-platform-files \
  --source /opt/surface-pro-12-linux --apply --acknowledge-third-party-files
sudo /opt/sp12-linux/scripts/install-wifi-board
sudo /opt/sp12-linux/scripts/install-wifi-board --apply
```

These tools use pinned sources and verified Wi-Fi board data. Do not substitute
a board file from another tablet. A different existing board file is preserved
as `board.bin.before-sp12`; existing backups are not overwritten.
Follow the [boot-file update procedure](#update-boot-files) after changing firmware.

## Audio and sensors

Audio needs the matching driver, topology and ALSA routing configuration (UCM).
The topology describes audio connections; UCM tells applications which paths to use.
Use the [pinned source revisions](developer/reference/sources.md), not moving branches.
Preview each change first:

```bash
sudo /opt/sp12-linux/scripts/install-audio-topology \
  --source /opt/surface-pro-12-linux/audioreach-topology
sudo /opt/sp12-linux/scripts/install-audio-ucm
```

Add `--apply` to each command only after its hash check passes. Then run:

```bash
systemctl --user restart pipewire.service pipewire-pulse.service wireplumber.service
wpctl status
aplay -l
arecord -l
```

Test playback and a short microphone recording at low volume. If a card exists
but applications are silent, check UCM file permissions (`0644`) and audio-service
logs. For `bus clsh` errors, the earlier tested workaround was to mute
`SpkrLeft CPS` and `SpkrRight CPS` in `alsamixer`, then reboot.
Never remove the kernel's speaker-gain limits.

The sensor installer is not yet a validated clean-system procedure. On an
already configured system, check `hexagonrpc.service`, `iio-sensor-proxy.service`
and `monitor-sensor`. See the [sensor implementation notes](developer/boot-and-sensors.md#reproducible-sensor-stack).

## ESP space

`/boot/efi` is separate from `/boot`. Free space on the Linux root does not
mean there is enough room for a boot update. Check without changing files:

```bash
findmnt /boot/efi
df -h /boot /boot/efi
/opt/sp12-linux/scripts/sp12-esp-space
```

If an interrupted update left recognized `.new` files, review the report, then:

```bash
sudo /opt/sp12-linux/scripts/sp12-esp-space --apply-stale-only
```

This removes only validated stale staging files. Keep active boot files, Windows
files and recovery sets. If space is still insufficient, stop the update.
Do not resize a mounted ESP or remove recovery files to make an update fit.

## Update boot files

First check the selected release and preserve a recovery set:

```bash
cat /etc/sp12-linux/boot.conf
uname -r
```

The main release is `KVER=7.3.0-sp12-v7.3-platform` with
`DTB=/boot/dtb-7.3.0-sp12-v7.3-platform`. Rebuild only that release's initramfs:

```bash
sudo update-initramfs -u -k 7.3.0-sp12-v7.3-platform
sudo /opt/sp12-linux/scripts/sp12-verify
```

The installed sync hook must copy the matching kernel, initramfs and DTB together
and restore the ESP to read-only. Stop on any sync or verification error.
Never let a generic kernel symlink choose the boot files. Keep the running and
recovery kernels when updating packages. A change to a different custom kernel
needs its exact package, matching DTB and a reviewed configuration change;
see the [boot-sync design](developer/boot-and-sensors.md#boot-synchronization).

## Power and hardware tests

Preview optional power settings with `/opt/sp12-linux/scripts/install-power-policy`.
Apply only after reviewing the limits. Earlier power measurements came from a
different installed setup; they are not a 26.10 battery-life promise.
An inactive one-shot service can be normal: check `Result=success` and
`ExecMainStatus=0`. Never write unknown or zero battery-threshold values.

## Test hardware

After a kernel or DTB change, check display, touch, keyboard, Wi-Fi reconnect,
Bluetooth, speakers and microphone. Save work before testing suspend/resume.
Also test rotation, brightness, charging, USB and an external display if available.
Record each result separately; booting alone does not test every feature.
Use the [detailed checklist](developer/hardware-tests.md) for commands and test limits.

## Fix a problem

Start with a diagnostic report and review it before sharing:

```bash
/opt/sp12-linux/scripts/sp12-diagnostics --output ~/sp12-diagnostics.txt
```

The report omits journal logs, filesystem UUIDs, MAC addresses, hostnames and
firmware contents. It can still need manual review.

- **Missing internal disk:** stop installation. Check the model, DTB and kernel logs.
  Partitioning cannot fix a storage controller that never appeared.
- **Black screen:** check the matching DTB and GPU logs. An early firmware lookup
  error may be followed by a successful load of the compressed `.zst` file.
- **Missing Wi-Fi or silent audio:** use the device-file and audio checks above.
- **Missing cameras:** inspect media devices first. A device-tree node does not
  prove capture works.
- **Full ESP:** use the [space checks](#esp-space), not general file deletion.

### Installer error

Keep the live session open and inspect:

```bash
sudo tail -n 120 /var/log/installer/curtin-install.log
```

The older 26.04 installer could fail while querying firmware boot entries with
`EFI variables are not supported on this system`. That observation is not a
26.10 installation result. Check the actual failed stage. Do not assume the
system copy completed because `/target` exists. Return to the
[experimental target checks](install.md#experimental-installation) only after
confirming the selected root and ESP. Save the installer logs before retrying.

## Recover boot

**Fresh 26.10 installation and recovery are not fully vetted.** The earlier
installed-system recovery tool uses the known matching three-file set under
`/boot/efi/sp12-recovery-panel/`. Preview it before applying:

```bash
/opt/sp12-linux/scripts/sp12-restore-recovery
sudo /opt/sp12-linux/scripts/sp12-restore-recovery --apply
```

Restore the kernel, initramfs and DTB together. Handled errors restore read-only
mode, but power loss can leave a partial set. Keep separate recovery media.
If no installed kernel boots, start the live USB and collect the disk layout
and logs. The installed recovery tool is not a validated live-USB target repair
procedure. Stop rather than guessing a destination disk or copying one boot file.
