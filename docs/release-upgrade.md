# Ubuntu 26.10 release-upgrade assessment

Checked **2026-10-23**, using official Ubuntu sources and read-only inspection
of the test device. No release upgrade, package installation or configuration
change was performed for this assessment.

## Current decision: do not start the upgrade yet

Ubuntu supports upgrading 26.04 to 26.10 when the system follows interim
releases. Ubuntu 26.10 was released on October 15, 2026, with nine months of
maintenance. That establishes an upgrade route, not compatibility of this
custom Surface installation. See the [release announcement][announcement].

Two immediate conditions prevent proceeding:

- The device has `Prompt=lts` in `/etc/update-manager/release-upgrades`.
  Following interim releases requires deliberately changing this to
  `Prompt=normal`; see [Canonical's instructions][switch].
- Two fresh HTTPS requests from the device to Canonical's
  [stable upgrade metadata][metadata] listed 26.04.1 as the latest release and
  contained no 26.10 entry. This is a **time-specific observation**, not a claim
  that 26.10 is unreleased. Recheck before acting. Do not use `-d` to bypass
  stable upgrade availability.

## What is already verified

The device runs Ubuntu 26.04.1 LTS with `7.3.0-sp12-v7.3-platform`. Maintained
boot sync explicitly selects its matching kernel and DTB. Approximately
187 GiB is available on root and 810 MiB on the ESP; `dpkg --audit` reported no
problems. Ordinary package updates remain pending. The held package is
`iio-sensor-proxy`; locally built sensor components and service overrides are
installed. The corrected Surface audio UCM file has a local diversion.

The installed boot/configuration recovery set and an independent copy were
verified. **They are not a full-system rollback.** Restoring an old kernel after
a release upgrade still runs the upgraded userspace. Ubuntu does not support
an in-place downgrade; preserve a restorable root backup and user data before
proceeding. See [Ubuntu's upgrade guide][upgrade] and this repository's
[boot recovery guide](recovery.md).

## Repository work needed before a supported procedure

1. Add a read-only upgrade preflight covering availability, pending updates,
   holds, external repositories, space, matching boot files/modules and
   full-system recovery.
2. Define and test fallback-loader protection during GRUB/shim updates.
   Current sync protects `/sp12/*`, not `/EFI/BOOT/BOOTAA64.EFI`.
   Installed GRUB maintainer code can run `grub-install`; its actual
   `grub2/no_efi_extra_removable` setting still needs privileged inspection.
   Do not blanket-hold bootloader packages.
3. Verify retention of running and recovery kernel packages, and inspect the
   release upgrader's proposed removals before obsolete-package cleanup.
4. Run boot-sync, staging, space and failure-restoration tests under 26.10.
   Its default core utilities fully switch to Rust implementations, including
   `cp` and `mv`, which these scripts use. See the [release notes][notes].
5. Validate sensor libraries/services, the sensor hold, firmware, audio
   diversion, graphics, networking and power policy against upgraded packages.
   Do not automatically remove holds or overwrite newer distribution fixes.

`scripts/inspect-install-target` intentionally accepts only 26.04. That guard
does not block an in-place upgrade: runtime boot sync has no OS-version guard.
Fresh 26.10 installer support separately requires verified ISO provenance,
installation tests and updated release metadata. Relaxing the guard alone
would not establish support.

## Eventual operator sequence

1. Complete the safeguards above; verify full-system backup and recovery media.
2. Apply ordinary 26.04 updates, verify boot/loader hashes, reboot and test.
3. Choose the interim track deliberately and confirm the stable upgrader offers
   26.10. Availability must be rechecked on the device.
4. On AC power, run `sudo do-release-upgrade` locally and review package
   removals and configuration decisions. Ubuntu disables third-party
   repositories during upgrading; review their compatibility individually.
5. Before reboot, verify the custom loader, explicit boot selection, retained
   kernels, modules, initramfs and ESP payload.
6. Repeat [hardware checks](hardware-tests.md), including warm/cold boot,
   input, audio/sensors, graphics, networking and suspend.

Remaining unknowns include the actual 26.10 dependency/removal plan, local
sensor ABI compatibility, bootloader configuration and full-root backup
readiness. The release notes mention Snapdragon Wi-Fi/resume problems; this
does not establish that they explain this device's existing PCIe timeout.

[announcement]: https://lists.ubuntu.com/archives/ubuntu-announce/2026-October/000330.html
[switch]: https://ubuntu.com/desktop/docs/en/latest/how-to/switch-between-an-lts-and-interim-release/
[metadata]: https://changelogs.ubuntu.com/meta-release
[upgrade]: https://ubuntu.com/desktop/docs/en/latest/how-to/upgrade-ubuntu-desktop/
[notes]: https://documentation.ubuntu.com/release-notes/26.10/
