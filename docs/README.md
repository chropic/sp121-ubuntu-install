# Documentation

Read the page for your task; the historical notes are retained separately for
source tracing.

## Use the tablet

1. [Install Ubuntu](install.md) — supported model, verified inputs, USB and fallback boot.
2. [Configure the first boot](first-boot.md) — repositories, platform files, Wi-Fi, audio and sensors.
3. [Verify hardware](hardware-tests.md) — repeatable checks after kernel or DTB changes.
4. [Maintain the system](maintenance.md) — power policy, updates and ESP space.
5. [Recover boot](recovery.md) — restore a matching kernel/initramfs/DTB set.

[Release-upgrade assessment](release-upgrade.md) — Ubuntu release compatibility
and readiness checks before upgrading the installed system.

[Support matrix](support.md) · [Troubleshooting](troubleshooting/README.md)

[23 October 2026 testing results](testing-2026-10-23.md) — verified boots and
recovery, suspend findings, unresolved issues and remaining checks.

## Develop and audit

- [Kernel guide](../kernel/README.md) and [Linux 7.3 port](../kernel/ports/v7.3/README.md)
- [Boot and sensor implementation](development.md)
- [Firmware policy](../firmware/README.md) and [release requirements](../release/README.md)
- [Source ledger](reference/sources.md) and [credits](reference/credits.md)
- [Original tested notes](reference/README.md) — preserved verbatim, not the installation entry point
- [Contributing](../CONTRIBUTING.md) and [security policy](../SECURITY.md)
