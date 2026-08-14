# Boot synchronization design

The installed helper reads two values from `/etc/sp12-linux/boot.conf`:

```text
KVER=7.2.0-rc7-sp12-extra-camera
DTB=/boot/dtb-7.2.0-rc7-sp12-extra-camera
```

It derives exact kernel and initramfs paths from `KVER`, validates all sources,
remounts the ESP read-write, copies to `.new` files, compares them, atomically
renames the verified files, and restores the ESP to read-only mode through a trap.

Preview installation against an already installed kernel:

```bash
scripts/install-boot-sync \
  --kernel-release 7.2.0-rc7-sp12-extra-camera \
  --dtb /boot/dtb-7.2.0-rc7-sp12-extra-camera
```

Only add `sudo` and `--apply` after checking the displayed paths and hashes. The
installer then synchronizes the ESP immediately. Package and initramfs hooks call
the same helper for later updates, but the pinned release remains unchanged until
an administrator deliberately edits the configuration.

This mechanism updates an existing fallback loader. Creating `BOOTAA64.EFI` during
the initial live installation is a separate workflow that still needs automated
target-root and target-ESP validation.
