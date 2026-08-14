# Quick start

This project does not distribute an installer ISO. You download Canonical's
stock Ubuntu 26.04 ARM64 Desktop ISO and use this repository to make a local
SP12 boot copy.

> [!CAUTION]
> The unmodified stock ISO does not contain the Surface Pro 12 device tree and
> is not the finished USB image. Installing an operating system can erase every
> file on the tablet. The local build path is not yet marked
> **installation-tested** in repository form.

## 1. Confirm the device and prepare recovery

This guide supports only the **Surface Pro 12-inch, 1st Edition with Snapdragon
X Plus**. It does not support an Intel Surface, Surface Pro 11, or a later SP12
revision.

Before continuing, prepare:

- another Linux computer with internet access and at least 10 GB free;
- one reliable USB installer drive and a separate backup/recovery drive;
- the Surface charger, a verified backup, and any BitLocker recovery key;
- Microsoft's recovery media if Windows must remain recoverable.

Read [Before you start](docs/00-before-you-start.md) before creating media.

## 2. Download the stock Ubuntu ISO

Clone this repository on the other Linux computer, then download the official
Ubuntu files from Canonical:

```bash
git clone https://github.com/chropic/sp121-ubuntu-install.git sp12-linux
cd sp12-linux
mkdir -p build/installer-inputs build/output
cd build/installer-inputs

curl -fLO https://cdimage.ubuntu.com/releases/26.04/release/SHA256SUMS
curl -fLO https://cdimage.ubuntu.com/releases/26.04/release/SHA256SUMS.gpg
curl -fLO https://cdimage.ubuntu.com/releases/26.04/release/ubuntu-26.04-desktop-arm64.iso
```

Verify Canonical's signature and the ISO. Both commands must succeed, and the
second must print `ubuntu-26.04-desktop-arm64.iso: OK`:

```bash
gpgv --keyring /usr/share/keyrings/ubuntu-archive-keyring.gpg \
  SHA256SUMS.gpg SHA256SUMS
sha256sum -c SHA256SUMS --ignore-missing
```

If the keyring is unavailable, stop and follow
[Canonical's image-verification procedure](https://documentation.ubuntu.com/security/software-integrity/image-verification/).
Never replace the expected hash with one calculated from an unverified download.

## 3. Download the pinned installer DTB

Download only the machine-tested installer device tree from the pinned upstream
commit:

```bash
curl -fL \
  -o x1p42100-microsoft-sp12in.dtb \
  https://raw.githubusercontent.com/harrisonvanderbyl/surface-pro-12-inch-linux/ea0f07e66beea95898d96fbeb6daa472f4735af3/boot/dtb

printf '%s  %s\n' \
  d7ed4b073c7344cb0bb2c3f7d00655df60b473588a5c0364af54537dc2c672c7 \
  x1p42100-microsoft-sp12in.dtb | sha256sum -c -
```

Stop unless the DTB reports `OK`.

## 4. Build your local USB image

Install the local build dependency on Ubuntu or Debian:

```bash
sudo apt install curl git gzip xorriso
```

Return to the repository root and build:

```bash
cd ../..
ISO_SHA256=$(awk '$2 == "*ubuntu-26.04-desktop-arm64.iso" { print $1 }' \
  build/installer-inputs/SHA256SUMS)
test "${#ISO_SHA256}" -eq 64
scripts/build-installer \
  --iso build/installer-inputs/ubuntu-26.04-desktop-arm64.iso \
  --iso-sha256 "$ISO_SHA256" \
  --dtb build/installer-inputs/x1p42100-microsoft-sp12in.dtb \
  --dtb-sha256 d7ed4b073c7344cb0bb2c3f7d00655df60b473588a5c0364af54537dc2c672c7 \
  --output build/output/sp12-ubuntu-26.04-arm64.iso

(cd build/output && sha256sum -c sp12-ubuntu-26.04-arm64.iso.sha256)
```

The builder modifies only the new output. It does not change Canonical's stock
ISO, write a USB drive, or bundle the separate third-party support checkout.

## 5. Write and boot the USB

Use a graphical imaging tool that clearly shows the USB manufacturer's name and
capacity. Selecting the wrong destination can erase another disk. Eject the USB
cleanly when writing finishes.

With the Surface powered off:

1. Hold **Volume Up** while pressing Power to enter Surface UEFI.
2. Record the original Secure Boot setting, then disable Secure Boot for the
   tested unsigned path and ensure USB boot is enabled.
3. Power off, insert the USB, connect power, then hold **Volume Down** while
   pressing Power.

In the live environment, open Terminal and run the project copy from the ISO:

```bash
mkdir -p /tmp/sp12-linux
tar -xzf /cdrom/sp12-linux.tar.gz -C /tmp/sp12-linux
cd /tmp/sp12-linux
scripts/sp12-preflight
```

Continue only if the final line is:

```text
RESULT: PASS -- supported Surface Pro 12 hardware detected
```

Also confirm that internal UFS storage is visible before opening the installer.
Then follow [Install Linux](docs/02-install-linux.md). Obey every stop condition;
that chapter remains pending a fresh end-to-end physical installation test.
