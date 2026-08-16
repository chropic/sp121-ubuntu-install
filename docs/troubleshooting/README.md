# Troubleshooting

Start by creating the privacy-conscious inventory report:

```bash
scripts/sp12-diagnostics --output ~/sp12-diagnostics.txt
```

The report excludes journals, filesystem UUIDs, MAC addresses, hostnames, and
firmware contents by design. Review it manually before sharing it.

## System Program Problem Detected during installation

Ubuntu 26.04's installer can display this generic error late in installation on
the Surface Pro 12. Check the actual failure before retrying or rebooting:

```bash
sudo tail -n 120 /var/log/installer/curtin-install.log
```

If the log ends in the `install-grub` stage with all of these details:

```text
Command: ... chroot /target efibootmgr -v
Exit code: 2
Stderr: EFI variables are not supported on this system.
```

then curtin failed while querying firmware boot entries. This is distinct from
an earlier storage, filesystem, package-extraction, or kernel failure. The system
copy may be usable, but do not assume it is complete merely because `/target`
exists.

Keep the installer open, open a live-session terminal, and return to
[Install Linux and prepare boot](../../GUIDE.md#4-install-linux-and-prepare-boot).
Both `/target` and `/target/boot/efi` must still be mounted. Select the exact
installed kernel from `/target/boot`, then run the repository's structural check:

```bash
ls -1 /target/boot/vmlinuz-* /target/boot/initrd.img-*
scripts/inspect-install-target \
  --target /target \
  --kernel-release YOUR_EXACT_KERNEL_RELEASE
```

Only a `RESULT: PASS` makes it appropriate to preview
`scripts/install-fallback-target`. The preview is non-mutating; its `--apply`
path remains release-unsupported until a fresh physical installation validates
it. If the target check fails, preserve the evidence before doing anything else:

```bash
sudo tar -czf /tmp/installer-logs.tar.gz /var/log/installer
```

Copy that archive to separate removable storage and review it for private data
before sharing it. Do not repeatedly run the graphical installer against the
same target; a retry can erase the evidence or alter the partially installed
system.

## APT requests installation media after first boot

The installer may leave an active `/etc/apt/sources.list.d/cdrom.sources` while
the installer medium is unavailable. Do not delete source files or substitute
unverified mirrors. Follow the guide's guarded procedure to
[inspect, preserve, and enable the Ubuntu package repositories](../../GUIDE.md#enable-the-ubuntu-package-repositories).
It disables the CD-ROM entry reversibly and uses
`ubuntu.sources.curtin.orig` only after its release suites and official Ubuntu
URIs have been reviewed. Keep a tested wired connection attached and stop if
the template is absent, names the wrong release, contains an unexpected URI, or
`apt update` fails.

## Device will not boot

Use [Recovery](../../GUIDE.md#9-recover). Restore a matching kernel, initramfs, and DTB
as a set. Do not start by rebuilding the kernel.

## Internal storage is missing

Stop installation. Confirm the exact device tree and inspect kernel messages from
the live environment. No partitioning command can repair a UFS controller that
never appeared.

## Display remains black

Confirm the DTB matches the tablet and kernel. Do not replace compressed GPU
firmware merely because an early uncompressed lookup failed; the kernel may load
the `.zst` file successfully afterward.

## Wi-Fi is absent

Confirm the WCN7850 board file exists, then inspect `ath12k` messages. Do not use a
board file from a different model simply because its filename is similar.

## Audio card exists but applications are silent

Confirm the exact topology, UCM file mode `0644`, PipeWire/WirePlumber state, and
speaker CPS controls. Do not remove speaker volume limits.

## Cameras are absent

List media entities first. Camera wiring scripts cannot create missing CAMSS,
CSIPHY, sensor, media, or video devices.

## A service says inactive

The power policy is a `Type=oneshot` service and normally becomes inactive after
success. Check `Result` and `ExecMainStatus` instead.
