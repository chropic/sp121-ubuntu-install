# Developer reference

User instructions live in [installation](../install.md) and
[maintenance](../maintenance.md). Keep each procedure there once. Use short
sentences, explain new terms, and distinguish a test result from an expectation.

The main configuration is Ubuntu 26.10 ARM64 with
`7.3.0-sp12-v7.3-platform`. Fresh installation and recovery remain experimental.

## Build and test

- [Kernel sources and build recipe](../../kernel/ports/v7.3/README.md)
- [Live-image inputs, build steps, and exact tested image](live-image.md)
- [Boot synchronization and sensor implementation](boot-and-sensors.md)
- [Detailed hardware test checklist](hardware-tests.md)
- [System templates](../../system/README.md)

Run from a Linux checkout before opening a PR:

```bash
scripts/check-repository
shellcheck scripts/* tests/* kernel/prepare-tree kernel/build-packages \
  system/usr-local-sbin/* system/etc/kernel/postinst.d/* \
  system/etc/initramfs/post-update.d/*
git diff --check
```

Tests use isolated fixtures. `tests/scratch-fat` is a separate root-only runner
for a newly created, disposable FAT image. Do not point tests at a physical ESP.
Its symlink case is skipped on FAT and covered on Linux filesystems.

## Evidence

The current live result is owner-reported: the custom kernel name matched and
everything tested by the owner worked, including Wi-Fi and sound. A complete
fresh installation, recovery test and new per-feature measurements were deferred.

| Record | Scope |
| --- | --- |
| [Private live v2](../../release/CANDIDATE-26.10-private-live-v2.json) | Audited image; custom-kernel live boot and working hardware reported by owner |
| [Earlier generic-kernel candidate](../../release/CANDIDATE-26.10.json) | Booted, but Wi-Fi and sound failed; not the main configuration |
| [7.3 hardware detail](records/kernel-7.3-hardware.md) | Earlier installed-system observations and unresolved issues |
| [23 October tests](records/hardware-2026-10-23.md) | Exact earlier kernel boot, recovery and suspend checks |
| [26.04 upgrade preparation](records/upgrade-preparation-2026-10-24.md) | Package/chroot/FAT and physical-state comparisons, not an upgrade pass |

Records describe their observation date. Preserve their input hashes and test
limits; do not promote older results to a new release without a new test.
The old root handoff and repeated upgrade assessment remain in Git history;
current status belongs in the README and unique test evidence belongs here.

## Sources and publication

- [Source ledger](reference/sources.md) and [credits](reference/credits.md)
- [Original source notes](reference/README.md)
- [Device-file policy](../../firmware/README.md)
- [Release requirements](../../release/README.md)

Do not commit ISO, kernel, DTB or proprietary firmware binaries. Personal images
with private machine support are not public project releases. A future public
image still needs corresponding kernel source, reproducible inputs, licence
review, and physical installation/recovery evidence.
