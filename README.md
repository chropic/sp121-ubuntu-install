# Ubuntu on Surface Pro 12

The main configuration is **Ubuntu 26.10 ARM64 with the custom Linux 7.3
platform kernel**, `7.3.0-sp12-v7.3-platform`.

This project is for the **Surface Pro 12-inch, 1st Edition**, with Snapdragon
X Plus `X1P42100`. Other Surface models are outside its scope.

> [!WARNING]
> **Installation is experimental and has not been fully vetted.** The 26.10
> image has booted on the SP12, but a complete fresh installation and recovery
> test have not been completed. Do not treat it as an installation-tested release.

## Start here

- [Try the image or plan an installation](docs/install.md)
- [Maintain the system, fix problems, and recover boot](docs/maintenance.md)
- [Ubuntu 26.04: legacy notes](docs/legacy-26.04.md)
- [Build tools, test records, and sources](docs/developer/README.md)

## Support status

| Area | Status |
| --- | --- |
| Main configuration | Ubuntu 26.10 ARM64 + custom SP12 Linux 7.3 platform |
| Live USB | The owner booted private live v2, confirmed the kernel name, and reported everything working, including Wi-Fi and sound |
| Fresh installation and recovery | Experimental; not fully vetted; installation was deferred because no spare target disk was available |
| Detailed hardware checks | Older installed-system results are recorded separately; the live report is not a new measurement of every feature |
| Secure Boot, cameras, and hibernate | No new support claim; see the [hardware records](docs/developer/records/kernel-7.3-hardware.md) |
| Public image download | Not offered; the tested private image includes device files excluded from project distribution |

The first 26.10 candidate used Ubuntu's generic kernel and had no working Wi-Fi
or sound. **Private live v2**, which uses the custom kernel and matching device
files, is the tested configuration above. See its [exact build record](docs/developer/live-image.md).

## Repository layout

| Folder | Purpose |
| --- | --- |
| `docs/` | The installation and maintenance guides; developer references are under `docs/developer/` |
| `scripts/` | Commands for building, checking, installing, and recovering |
| `kernel/` | Kernel source recipes, patches, configurations, and build evidence |
| `system/` | Files installed by the guarded setup tools |
| `firmware/` | Device-file source pins and distribution rules; no firmware blobs |
| `release/` | Machine-readable build and test records; no binary releases in Git |

[Credits](docs/developer/reference/credits.md) ·
[Contributing](CONTRIBUTING.md) · [Security](SECURITY.md) · [License](LICENSE.md)

Independent community project. Not affiliated with Microsoft, Qualcomm, or Canonical.
