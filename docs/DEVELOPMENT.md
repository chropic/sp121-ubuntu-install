# Development notes

These notes describe the guarded boot and sensor workflows behind the user
guide. They are audit references, not extra installation paths.

## Fallback bootloader

`scripts/build-fallback-loader` builds an ARM64 `BOOTAA64.EFI` without mounting
or changing an ESP. Its embedded GRUB configuration searches FAT filesystems for
`/sp12/SP12BOOT`, then loads fixed payload names from that filesystem.

```bash
scripts/build-fallback-loader \
  --root-uuid YOUR-LINUX-ROOT-UUID \
  --output ./BOOTAA64.EFI
```

The builder checks every required GRUB module, refuses to overwrite output, and
uses `grub-file` to confirm an ARM64 EFI executable. The installation-specific
root UUID is embedded; rebuild only when it or the boot logic changes. Fixed
`/sp12/` kernel, initramfs, and DTB updates do not require a loader rebuild.
Never publish a root UUID as a universal value.

## Installing the fallback path into `/target`

From the customized live installer, after Ubuntu mounts `/target` and
`/target/boot/efi`, inspect and preview:

```bash
scripts/inspect-install-target \
  --target /target \
  --kernel-release YOUR_EXACT_KERNEL_RELEASE
scripts/install-fallback-target \
  --kernel-release YOUR_EXACT_KERNEL_RELEASE \
  --dtb-source /cdrom/casper/x1p42100-microsoft-sp12in.dtb
```

The installer rejects non-separate mountpoints, non-FAT ESPs, non-Ubuntu 26.04
roots, missing ARM64 GRUB modules or exact kernel files, and unsupported Surface
hardware. It derives the root UUID from the mounted target rather than accepting
typed input. Add `sudo` and `--apply` only after reviewing every displayed path.

The apply path stages and verifies the versioned DTB under target `/boot` and
the exact three-file ESP payload; builds and validates `BOOTAA64.NEW` in the
target chroot; preserves the previous loader once as `BOOTAA64.EFI.pre-sp12`;
renames the verified payload and loader into place; installs the pinned sync
helper and hooks; and compares the final payload again. It neither partitions
disks nor extracts arbitrary support archives as root.

## Boot synchronization

The installed helper reads:

```text
/etc/sp12-linux/boot.conf
KVER=7.2.0-rc7-sp12-extra-camera
DTB=/boot/dtb-7.2.0-rc7-sp12-extra-camera
```

It derives exact kernel/initramfs paths from `KVER`, validates sources, remounts
the ESP read-write, stages `.new` files, compares them, atomically renames them,
and restores read-only mode through a trap. Preview installation:

```bash
scripts/install-boot-sync \
  --kernel-release 7.2.0-rc7-sp12-extra-camera \
  --dtb /boot/dtb-7.2.0-rc7-sp12-extra-camera
```

Add `sudo` and `--apply` only after checking paths and hashes. Installation also
synchronizes immediately. Package and initramfs hooks call the helper later, but
the pinned release changes only when an administrator edits the configuration.
This updates an existing fallback loader; initial `BOOTAA64.EFI` creation is the
separate target workflow above.

## Reproducible sensor stack

The working reference uses three GPL components:

1. `libssc` 0.4.4 at `f6dfbfa5f34ef22f3d47ef346c22834e79c60df1`;
2. Harrison van der Byl's Hexagon RPC 0.4.0 fork at
   `78b67e2f00df0455f0c0282183b1b1b8b219447d`;
3. Harrison's IIO Sensor Proxy 3.9 fork at
   `fcd5b5cf431bc053375350c57064b8b13dd961b4`, built with
   `-Dssc-support=enabled` and prefix `/usr/local`.

These revisions predate the 2026-08-13 reference installation, remain the tested
branch heads, and report the live artifact versions. Exact binary hashes are in
[`firmware/sources.yaml`](../firmware/sources.yaml).

The old installer cloned three moving branches, recursively copied a large
`usr/` tree, removed build checkouts, wrote services with shell heredocs, and held
a distribution package. It proved the stack worked but cannot identify future
binary sources or make partial failures easy to recover from.

Its replacement must verify all origins and commits; build `libssc`, Hexagon RPC,
then IIO Sensor Proxy; consistently use `/usr/local`; call `ldconfig` only after a
successful install; install reviewed service/udev templates; use
`/dev/fastrpc-adsp` rather than `/dev/fastrpc-adsp-secure`; add the tested fork's
`ssc-accel` udev tag; exclude Qualcomm DSP binaries from this repository and its
releases; preview and stage before writing the live root; and independently test
accelerometer, ambient light, and compass after reboot.

Until that builder passes a clean-machine test, fresh sensor installation remains
a release gate—not an invitation to run the moving-branch installer.
