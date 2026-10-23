# Recover a bootable system

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
/opt/sp12-linux/scripts/sp12-restore-recovery
sudo /opt/sp12-linux/scripts/sp12-restore-recovery --apply
```

The script validates the tablet and all three files, stages `.new` copies,
compares them, renames the verified files into place, and returns the ESP read-only
on handled exit or interruption. Power loss or forced process termination can
leave a partial set; keep the independent recovery USB available.

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
/opt/sp12-linux/scripts/sp12-diagnostics --output ~/sp12-diagnostics.txt
```

For symptom-specific checks, see [Troubleshooting](troubleshooting/README.md).
