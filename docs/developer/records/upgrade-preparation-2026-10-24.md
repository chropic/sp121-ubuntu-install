# Ubuntu 26.04 upgrade preparation: 24 October 2026

This is a dated preparation record, not a release-upgrade pass. The current main
configuration is [Ubuntu 26.10 with custom SP12 Linux 7.3](../../../README.md).
The device in this record was running Ubuntu 26.04.1 ARM64.

## Scope

Work started from repository revision `8486d6b743c6d22ecfdaba2a8957a6eaac0fd305`.
Target packages were authenticated, downloaded and extracted for inspection and
isolated tests. No target package was installed on the working system. No
release-upgrader offer metadata was fetched, no upgrader transaction started,
and no APT release sources were changed. Stable package indexes and an offered
release upgrade are separate checks.

The owner later allowed one normal boot test of the existing installation.
Independent full-system and separate user-data backups were deferred. That boot
test does not validate a fresh 26.10 installation or recovery USB restoration.

## Checks completed

| Check | Result and limit |
| --- | --- |
| Preflight without offer metadata | `--skip-release-metadata` makes no offer request and cannot return ready; default metadata checking remains intact |
| Latest root preflight | Zero failed checks, seven manual gates; `NOT READY` |
| Boot-space fixtures | 17 cases on Linux; 16 on disposable FAT with one symlink skip covered on Linux |
| Target Rust commands | Authenticated coreutils 0.12.0 and target libraries, including libc 2.44, ran inside an isolated ARM64 chroot with networking disabled |
| FAT validation | Root-only runner used a new disposable image in a private mount namespace; installed ESP hashes, firmware entries and ESP mount state compared unchanged |
| GRUB guard | Six isolated guard cases passed; authenticated target GRUB/shim hooks and supported installer options were reviewed |
| Sensor runtime | Deployed held sensor fork and RPC/library components passed target-library loading checks; no live sensor hardware was exposed to the chroot |
| R runtime | Deployed CRAN R 4.6.1 passed target-library BLAS/statistics and PDF/JPEG/PNG checks; personal compiled extensions were not covered |
| Existing-system reboot | Owner reported no firmware/GRUB errors; remote checks confirmed the maintained 7.3 kernel, active services and no failed systemd units |

FAT testing first exposed a fixture space-rounding error; it was fixed before
the successful rerun. Two added cases cover absent recovery markers and failed
backup copying. No production boot-space helper defect was found by these cases.
The target runtime tests avoid silently using host libc through a loader wrapper.

## Package strategy

The copied-state target APT simulations are diagnostics, not the actual Ubuntu
release-upgrader removal plan. They do not authorize package changes.

- Running and recovery kernels were marked manual in the simulated state.
- The installed sensor fork remains held; its target-library tests do not prove
  a clean sensor installation or all hardware behavior.
- Target GDAL requires MariaDB-compatible development headers that conflict with
  Oracle MySQL development headers. The owner selected MariaDB-compatible headers
  for a future transition. No live header package was changed.
- The refined diagnostic plan retains the intended kernel/application/R stack.
  The actual upgrader must still be reviewed before accepting any removal.
- Third-party R, Codex, Tailscale, VS Code and Waydroid sources still need review
  for a real upgrade. Target runtime success does not establish vendor support.

Exact package sets, hashes and simulated outcomes are recorded once here:

- [Device target summary](../../../release/upgrade-preparation/2026-10-24-device-target-summary.json)
- [Selected development strategy](../../../release/upgrade-preparation/2026-10-24-selected-development-strategy.json)
- [Rust runtime hashes](../../../release/upgrade-preparation/2026-10-24-rust-runtime.sha256)
- [Sensor runtime hashes](../../../release/upgrade-preparation/2026-10-24-sensor-runtime.sha256)
- [R runtime hashes](../../../release/upgrade-preparation/2026-10-24-r-runtime.sha256)
- [Initramfs package hashes](../../../release/upgrade-preparation/2026-10-24-initramfs-packages.sha256)

## Boot protection and observed state

The selected kernel was `7.3.0-sp12-v7.3-platform`, with matching installed
kernel, initramfs, modules and DTB. The active ESP files matched their sources.
Three older recovery kernels remained installed. The ESP was FAT and read-only;
the latest observed free space was about 806 MiB, with about 185 GiB free on root.
These figures describe the observation, not a future upgrader space guarantee.

The verified GRUB helper diversion forces `--no-extra-removable` and `--no-nvram`.
A guarded GRUB/shim package rehearsal preserved the fallback loader, active
SP12 files, boot order and read-only ESP state. The diversion protects calls
through that helper; direct package cleanup in Ubuntu's vendor EFI directory
is outside it. Debconf settings alone are not the protection.

After the normal reboot, boot-file hashes and firmware entries still matched.
Early GPU lookups later recovered, but UFS RPMB, audio and PMIC warning classes
remained. A successful reboot is not a warning-free hardware test.

## Remaining gates

Before a real upgrade, obtain independent backups and tested recovery media,
check Ubuntu's stable upgrade offer, review the complete device-specific package
and removal plan, confirm kernel/recovery/hook retention, review held packages
and third-party sources, and check final space requirements. Do not use `-d` or
install target-suite packages to bypass these gates. See the short
[26.04 legacy guide](../../legacy-26.04.md).
