# Ubuntu on Surface Pro 12

Installation, recovery and kernel tooling for the **Surface Pro 12-inch,
1st Edition** — Snapdragon X Plus `X1P42100`, ARM64.

Intel Surface models, Surface Pro 11 and later SP12 revisions are outside this
project's scope.

> [!IMPORTANT]
> **Linux 7.3 platform is the project's main kernel and sole maintained default**
> for builds and installed systems. On-device checks cover boot, display, input,
> audio, sensors, Bluetooth audio and video through both USB-C ports. See the
> [support matrix](docs/support.md) for known issues and feature-specific results.
> The installer bundles 7.3 while retaining Ubuntu's stock live bootstrap.
> Fresh end-to-end installer validation is pending; no ISO is distributed.

## Choose your task

| I want to… | Start here |
|---|---|
| Install Ubuntu | [Installation guide](docs/install.md) |
| Configure Wi-Fi, sound and sensors | [First boot](docs/first-boot.md) |
| Check what works | [Support matrix](docs/support.md) · [Hardware tests](docs/hardware-tests.md) |
| Update or manage ESP space | [Maintenance](docs/maintenance.md) |
| Fix a problem or restore boot | [Troubleshooting](docs/troubleshooting/README.md) · [Recovery](docs/recovery.md) |
| Build or review Linux 7.3 | [Kernel build guide](kernel/ports/v7.3/README.md) |
| Contribute or audit sources | [Contributing](CONTRIBUTING.md) · [Documentation index](docs/README.md) |

## Before changing boot files

1. Run `scripts/sp12-preflight`; stop if it fails.
2. Keep Secure Boot disabled for the current unsigned boot path.
3. Keep a bootable recovery USB and the known-good kernel.
4. Update the **kernel, initramfs and DTB together**, using exact versioned files.
5. Keep the running and recovery kernels. Inspect ESP usage before copying updates.

See the [support matrix](docs/support.md) for current 7.3 results and known issues.
The optional camera profile keeps camera nodes disabled; camera capture is not
supported yet.

## Repository map

| Directory | Contents |
|---|---|
| [`docs/`](docs/README.md) | Installation, maintenance, recovery and reference material |
| [`scripts/`](scripts/) | Guarded installers, diagnostics and checks |
| [`kernel/`](kernel/README.md) | Configurations, patches, build tools and validation records |
| [`system/`](system/README.md) | Reviewed installed-system templates |
| [`firmware/`](firmware/README.md) | Source pins and policy; no firmware blobs |
| [`release/`](release/README.md) | Build provenance and release gates; no binaries in Git |

[Credits](docs/reference/credits.md) · [Source ledger](docs/reference/sources.md) ·
[Security policy](SECURITY.md) · [License](LICENSE.md)

Independent community project; not affiliated with Microsoft, Qualcomm,
Canonical or the Linux kernel project.
