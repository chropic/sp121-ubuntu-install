# Create the installer

This procedure modifies a local copy of an official ARM64 installation ISO. It
does not download an ISO and does not write a USB drive.

## Inputs

Obtain these files on another Linux computer:

1. the official Ubuntu 26.04 ARM64 Desktop ISO;
2. Canonical's matching `SHA256SUMS` file;
3. a tested SP12 DTB named `x1p42100-microsoft-sp12in.dtb`;
4. a checkout of Harrison van der Byl's SP12 support repository.

Verify the official ISO before modifying it:

```bash
sha256sum -c SHA256SUMS --ignore-missing
```

Do not continue unless the ISO reports `OK`.

## Required tool

On Ubuntu or Debian:

```bash
sudo apt install xorriso
```

## Build

From this repository, run:

```bash
scripts/build-installer \
  --iso /path/to/ubuntu-26.04-desktop-arm64.iso \
  --dtb /path/to/x1p42100-microsoft-sp12in.dtb \
  --support-dir /path/to/surface-pro-12-inch-linux \
  --output /path/to/sp12-installer.iso
```

The script refuses to overwrite an existing output. It inserts the DTB, adds the
required GRUB device-tree directive and `stubble.dtb_override=true`, and includes
the support repository as a source archive for post-install use.

Save the printed SHA-256 checksum beside the ISO.

## Write the USB

USB-writing instructions are intentionally not automated yet. Selecting the
wrong output disk would erase it. Use a graphical imaging tool that shows the
drive's manufacturer and capacity, eject the drive cleanly, then reconnect it
and verify that its partitions are readable.

## First boot from USB

1. Power off the Surface completely.
2. Insert the USB and connect power.
3. Hold Volume Down while pressing Power.
4. In the live environment, open Terminal.
5. Run the copy of `sp12-preflight` supplied with the project.

Do not start the installer if the model check or UFS check fails.
