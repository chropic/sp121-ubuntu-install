# Installing the fallback path into `/target`

This workflow runs from the customized live installer after Ubuntu has populated
and mounted `/target` and `/target/boot/efi`.

Inspect without changing anything:

```bash
scripts/inspect-install-target \
  --target /target \
  --kernel-release YOUR_EXACT_KERNEL_RELEASE
```

Then preview the complete operation:

```bash
scripts/install-fallback-target \
  --kernel-release YOUR_EXACT_KERNEL_RELEASE \
  --dtb-source /cdrom/casper/x1p42100-microsoft-sp12in.dtb
```

The installer refuses targets that are not separate mountpoints, non-FAT ESPs,
non-Ubuntu 26.04 roots, missing GRUB ARM64 modules, missing exact kernel files, or
unsupported Surface hardware. It calculates the root UUID from the mounted target
rather than accepting a typed value.

Only add `sudo` and `--apply` after reviewing every displayed path. The apply path:

1. stages and verifies the versioned DTB under target `/boot`;
2. stages and verifies the exact kernel, initramfs, and DTB on the target ESP;
3. builds and validates `BOOTAA64.NEW` inside the target chroot;
4. preserves the pre-existing loader once as `BOOTAA64.EFI.pre-sp12`;
5. renames the verified payload and loader into place;
6. installs the pinned synchronization helper and hooks;
7. compares the final payload again.

This script intentionally does not partition disks and does not extract arbitrary
support archives as root.
