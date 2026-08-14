# Linux on the Surface Pro 12-inch (1st Edition)

Community installation and recovery tooling for the ARM64 Microsoft Surface Pro
12-inch, 1st Edition (`microsoft,surface-pro-12in`, Qualcomm `X1P42100`). Similar
Intel models, Surface Pro 11, and later SP12 revisions are not supported.

> [!WARNING]
> No installer ISO is distributed. The local builder starts with Canonical's
> stock Ubuntu 26.04 ARM64 ISO, and the repository workflow is not yet marked
> **installation-tested**. Follow [the complete guide](GUIDE.md) and every stop
> condition.

## Start here

- **Install, configure, update, or recover:** [GUIDE.md](GUIDE.md)
- **Diagnose a problem:** [Troubleshooting](docs/troubleshooting/README.md)
- **Check a feature:** [Support matrix](SUPPORT.md)
- **Understand implementation details:** [Development notes](docs/DEVELOPMENT.md)
- **Audit firmware, sources, or attribution:** [Firmware policy](firmware/README.md),
  [source ledger](SOURCES.md), and [credits](CREDITS.md)
- **Reproduce the kernel:** [Kernel notes](kernel/README.md)
- **Audit the original machine-tested notes:** [Reference snapshot](docs/reference/)

## Tested reference

Last validated 2026-08-13: Ubuntu 26.04 ARM64, kernel
`7.2.0-rc7-sp12-extra-camera` (`linux-image` package `7.2.0~rc7-6`), Sharp
`LQ120P1JX51` panel, Secure Boot disabled.

Internal storage, display, GPU, Wi-Fi, Bluetooth, Type Cover, touchscreen, pen,
audio, sensors, battery reporting, SCMI CPU-frequency scaling, and IRIS decoding
worked. Cameras, RTC, suspend, volume buttons, DisplayPort audio, and charge-limit
changes still need feature-level runtime validation. Hibernate is unsupported.

## Safety invariants

1. Run `scripts/sp12-preflight`; stop if it fails.
2. Keep Secure Boot disabled until the separate signed-boot design is proven.
3. Keep a bootable USB and known-good recovery kernel.
4. Treat each kernel, initramfs, and DTB as one versioned set.
5. Never copy generic `/boot/vmlinuz` or `/boot/initrd.img` symlinks to the ESP.
6. Never purge the running or recovery kernel.
7. Never guess a charge-threshold interface or range.

The project is in its documentation and reproducibility phase. Planned release
artifacts are versioned kernel packages, a matching DTB, checksums, and build
provenance; redistributable binaries belong in GitHub Releases, not Git history.
The verbatim 2026-08-13 guide remains under `docs/reference/` for provenance.

This independent community project is not affiliated with or endorsed by
Microsoft, Qualcomm, Canonical, or the Linux kernel project.
