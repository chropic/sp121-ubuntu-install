# Recovery

Recovery is part of installation, not an optional later topic.

## If the previous kernel still boots

Boot the known-good entry, confirm the running kernel with `uname -r`, and restore
the matching recovery kernel, initramfs, and DTB together. Never restore only one
of the three files.

The tested recovery payload is stored separately from the active payload:

```text
/boot/efi/sp12-recovery-panel/vmlinuz
/boot/efi/sp12-recovery-panel/initrd.img
/boot/efi/sp12-recovery-panel/dtb
```

Preview the exact recovery payload and its checksums:

```bash
scripts/sp12-restore-recovery
```

If the paths and hashes describe the intended known-good set, apply it:

```bash
sudo scripts/sp12-restore-recovery --apply
```

The script validates the tablet, requires all three recovery files, copies them
to `.new` files, compares every copy, renames the complete verified set, and
returns the ESP to read-only mode even if interrupted.

## If no installed kernel boots

1. Power off completely.
2. Insert the tested installer USB.
3. Hold Volume Down while pressing Power.
4. From the live environment, run `scripts/sp12-preflight` again.
5. Identify and mount the Linux root filesystem and its ESP.
6. Copy a matching recovery set to `/sp12/` on the ESP.
7. Synchronize writes and remount or unmount the ESP cleanly.

The installed-system recovery script cannot operate when the installed system
does not boot. Live-USB target mounting and restoration still require a separate
target-disk-validated workflow before they can be presented as novice-safe.

## Information to collect

From a bootable environment, save:

```bash
uname -a
cat /proc/device-tree/model
tr '\0' '\n' </proc/device-tree/compatible
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,UUID,MOUNTPOINTS,MODEL
journalctl -b -k --no-pager
```

Review logs for Wi-Fi names, filesystem UUIDs, hostnames, usernames, and other
identifying data before attaching them to a public issue.
