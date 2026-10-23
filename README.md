# Ubuntu on Surface Pro 12

Installation, recovery and kernel tooling for the **Surface Pro 12-inch,
1st Edition** — Snapdragon X Plus `X1P42100`, ARM64.

Intel Surface models, Surface Pro 11 and later SP12 revisions are outside this
project's scope.

> [!IMPORTANT]
> **Linux 7.3 boots on the test SP12.** Both kernel profiles build, but hardware
> regression, rollback and camera capture tests remain incomplete. The installer
> still uses its 7.2 reference inputs and has not passed a fresh end-to-end
> installation test. No installer ISO is distributed.

## Choose your task

| I want to… | Start here |
|---|---|
| Install Ubuntu | [Installation guide](docs/install.md) |
| Configure Wi-Fi, sound and sensors | [First boot](docs/first-boot.md) |
| Check what works | [Support matrix](docs/support.md) · [Hardware tests](docs/hardware-tests.md) |
| Update or manage ESP space | [Maintenance](docs/maintenance.md) |
| Fix a problem or restore boot | [Troubleshooting](docs/troubleshooting/README.md) · [Recovery](docs/recovery.md) |
| Build or review Linux 7.3 | [Kernel port](kernel/ports/v7.3/README.md) |
| Contribute or audit sources | [Contributing](CONTRIBUTING.md) · [Documentation index](docs/README.md) |

## Before changing boot files

1. Run `scripts/sp12-preflight`; stop if it fails.
2. Keep Secure Boot disabled for the current unsigned boot path.
3. Keep a bootable recovery USB and the known-good kernel.
4. Update the **kernel, initramfs and DTB together**, using exact versioned files.
5. Keep the running and recovery kernels. Inspect ESP usage before copying updates.

See the [support matrix](docs/support.md) for the historical working reference and
current 7.3 evidence. Camera nodes in the 7.3 camera profile remain disabled;
compilation does not establish capture support.

## Repository map

| Directory | Contents |
|---|---|
| [`docs/`](docs/README.md) | Installation, maintenance, recovery and reference material |
| [`scripts/`](scripts/) | Guarded installers, diagnostics and checks |
| [`kernel/`](kernel/README.md) | Configurations, patches, build tools and port validation |
| [`system/`](system/README.md) | Reviewed installed-system templates |
| [`firmware/`](firmware/README.md) | Source pins and policy; no firmware blobs |
| [`release/`](release/README.md) | Build provenance and release gates; no binaries in Git |

[Credits](docs/reference/credits.md) · [Source ledger](docs/reference/sources.md) ·
[Security policy](SECURITY.md) · [License](LICENSE.md)

Independent community project; not affiliated with Microsoft, Qualcomm,
Canonical or the Linux kernel project.
