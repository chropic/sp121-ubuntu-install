# Linux on the Surface Pro 12-inch (1st Edition)

Community installation and recovery tooling for the Microsoft Surface Pro
12-inch, 1st Edition with the Qualcomm Snapdragon X Plus `X1P42100` SoC.

> [!WARNING]
> This repository does not distribute an installer ISO. Its public path starts
> with Canonical's stock Ubuntu ARM64 ISO and prepares a local SP12 boot copy.
> That path is not yet marked **installation-tested** in repository form. Start
> with [QUICKSTART.md](QUICKSTART.md) and obey every stop condition.

## Supported device

| Property | Required value |
|---|---|
| Marketing name | Microsoft Surface Pro 12-inch, 1st Edition |
| Device-tree model | `Surface Pro 12in 1st Edition` |
| Primary compatible | `microsoft,surface-pro-12in` |
| SoC compatible | `qcom,x1p42100` |
| Architecture | ARM64 / AArch64 |

This project does not claim support for similarly named Intel Surface devices,
the Surface Pro 11, or a later Surface Pro 12 revision.

## Tested reference

The source guide was last validated on 2026-08-13 with:

```text
Ubuntu 26.04 ARM64
7.2.0-rc7-sp12-extra-camera
linux-image package 7.2.0~rc7-6
Sharp LQ120P1JX51 panel
Secure Boot disabled
```

Working in that reference installation: internal storage, display, GPU, Wi-Fi,
Bluetooth, Type Cover, touchscreen, pen, audio, sensors, battery reporting,
SCMI CPU-frequency scaling, and IRIS video decoding. Camera, RTC, suspend,
volume-button, DisplayPort-audio, and charge-limit additions still require
feature-by-feature runtime validation. Hibernate is not supported.

## Choose a path

- **Building locally from stock Ubuntu:** [Quick start](QUICKSTART.md)
- **Preparing safely:** [Before you start](docs/00-before-you-start.md)
- **Understanding the boot design:** [Boot architecture](docs/boot-architecture.md)
- **Auditing the fallback loader:**
  [Standalone loader](docs/development/fallback-loader.md) and
  [target installer](docs/development/target-fallback-install.md)
- **Auditing device-support files:** [Firmware policy and pinned sources](firmware/README.md)
- **Checking hardware after changes:**
  [Hardware verification](docs/04-hardware-verification.md)
- **Installing the measured battery policy:**
  [Power and battery](docs/05-power-and-battery.md)
- **Auditing the sensor build:** [Reproducible sensor stack](docs/development/sensor-stack.md)
- **Recovering a failed boot:** [Recovery](docs/07-recovery.md)
- **Diagnosing a problem safely:** [Troubleshooting](docs/troubleshooting/README.md)
- **Checking support:** [Support matrix](SUPPORT.md)
- **Giving credit or auditing sources:** [Credits](CREDITS.md) and
  [source ledger](SOURCES.md)
- **Auditing the original machine-tested notes:**
  [reference guide](docs/reference/original-tested-guide.md)

## Non-negotiable safety rules

1. Run `scripts/sp12-preflight` and stop if it fails.
2. Keep Secure Boot disabled until the separate signed-boot design is proven.
3. Keep a bootable installer USB and a known-good recovery kernel.
4. Treat the kernel, initramfs, and DTB as one versioned set.
5. Never copy generic `/boot/vmlinuz` or `/boot/initrd.img` symlinks to the ESP.
6. Never purge the running kernel or the recovery kernel.
7. Never write a charge threshold whose interface and valid range are unknown.

## Project status

The repository is in its documentation and reproducibility phase. It includes a
local builder for Canonical's stock Ubuntu ISO and does not publish a modified
installer image. Planned release artifacts are versioned kernel image/header
packages, a matching DTB, checksums, and build provenance. Redistributable binary
artifacts will live in GitHub Releases, not Git history.

The complete 2026-08-13 source guide is preserved verbatim under `docs/reference/`.
The numbered chapters are the safer public interface; the reference snapshot is
kept for provenance and for technical details that have not yet been migrated.

This is an independent community project. It is not affiliated with or endorsed
by Microsoft, Qualcomm, Canonical, or the Linux kernel project.
