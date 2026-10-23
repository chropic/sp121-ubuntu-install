# Development notes

These notes describe the guarded boot and sensor workflows behind the user
guide. They are audit references, not extra installation paths.

## Fallback bootloader

`scripts/build-fallback-loader` builds an ARM64 `BOOTAA64.EFI` without mounting
or changing an ESP. Its embedded GRUB configuration searches FAT filesystems for
`/sp12/SP12BOOT`, then loads fixed payload names from that filesystem.
This example derives the UUID of the currently running installed root; use the
target workflow below when operating from a live USB.

```bash
ROOT_UUID=$(findmnt -rn -o UUID --target /)
test -n "$ROOT_UUID" || exit 1
scripts/build-fallback-loader \
  --root-uuid "$ROOT_UUID" \
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
scripts/install-kernel-target
# After reviewing the native target/package checks:
sudo scripts/install-kernel-target --apply
KVER=7.3.0-sp12-v7.3-platform
scripts/inspect-install-target \
  --target /target \
  --kernel-release "$KVER"
scripts/install-fallback-target \
  --kernel-release "$KVER" \
  --dtb-source /target/boot/dtb-$KVER
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
KVER=7.3.0-sp12-v7.3-platform
DTB=/boot/dtb-7.3.0-sp12-v7.3-platform
```

It derives exact kernel/initramfs paths from `KVER` and validates sources.
Identical payloads are skipped. Before remounting read-write, it rejects existing
`.new` files and checks FAT-rounded space for changed files plus a 1 MiB margin.
It stages only changed files, compares them, renames them into place and restores
read-only mode through a trap. It keeps temporary rollback copies on the Linux
filesystem and restores promoted files on handled failures, retaining those
copies if restoration fails. Failed attempts remove only their own staging
files. A shared lock excludes concurrent sync, cleanup, recovery and fallback
installation. The three-file switch is not atomic across power loss; retain an
independent recovery set. See [ESP maintenance](maintenance.md#check-esp-space-before-updates) for
reporting and narrowly scoped stale-file cleanup. Preview installation:

```bash
scripts/install-boot-sync \
  --kernel-release 7.3.0-sp12-v7.3-platform \
  --dtb /boot/dtb-7.3.0-sp12-v7.3-platform
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
