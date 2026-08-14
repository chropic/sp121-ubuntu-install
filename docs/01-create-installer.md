# Build from the stock Ubuntu ISO

This project distributes a builder, not an installer image. Each user downloads
Canonical's stock ARM64 ISO and creates a local SP12 boot copy. The builder does
not alter the downloaded base file and does not write a USB drive.

The stock ISO is the trusted operating-system payload, but it is not used
unchanged on this device. It lacks the machine-tested SP12 device tree and GRUB
device-tree directive. The local builder adds only that boot information, this
project's tracked source archive, media-check updates, and build provenance.

## Inputs

Obtain these files on another Linux computer with at least 10 GB free:

1. the official Ubuntu 26.04 ARM64 Desktop ISO;
2. Canonical's matching `SHA256SUMS` file;
3. the pinned SP12 installer DTB named `x1p42100-microsoft-sp12in.dtb`;
4. a clean checkout of this repository.

The separately pinned Harrison support checkout is needed only for optional
post-install platform files. It is not placed in the ISO because it contains
third-party binary files this project does not redistribute.

## Download the stock files

From the repository root:

```bash
mkdir -p build/installer-inputs build/output
cd build/installer-inputs
curl -fLO https://cdimage.ubuntu.com/releases/26.04/release/SHA256SUMS
curl -fLO https://cdimage.ubuntu.com/releases/26.04/release/SHA256SUMS.gpg
curl -fLO https://cdimage.ubuntu.com/releases/26.04/release/ubuntu-26.04-desktop-arm64.iso
```

Authenticate Canonical's checksum metadata before trusting it:

```bash
gpgv --keyring /usr/share/keyrings/ubuntu-archive-keyring.gpg \
  SHA256SUMS.gpg SHA256SUMS
```

The command must report a good signature from the Ubuntu CD Image signing key.
If that keyring is unavailable, stop and use
[Canonical's image-verification procedure](https://documentation.ubuntu.com/security/software-integrity/image-verification/)
rather than skipping authentication.

Verify the official ISO before modifying it:

```bash
sha256sum -c SHA256SUMS --ignore-missing
```

Do not continue unless the ISO reports `OK`.

Capture the expected hash from Canonical's `SHA256SUMS`; do not calculate this
value from an unverified ISO and then pass it back to the builder:

```bash
ISO=ubuntu-26.04-desktop-arm64.iso
ISO_SHA256=$(awk -v name="*$ISO" '$2 == name { print $1 }' SHA256SUMS)
test "${#ISO_SHA256}" -eq 64
```

For the initial Ubuntu 26.04 ARM64 Desktop release, the authenticated value is:

```text
c2afd538d66fdd77377d03f1ed2ac76a34f1c116baecc9a8170d68f833121f57
```

Download and verify the installer DTB separately. The machine-tested live
installer used the DTB from the pinned support checkout; do not substitute the
later installed `7.2.0~rc7-6` DTB, whose compatibility with Ubuntu's stock live
kernel has not been established.

```bash
curl -fL \
  -o x1p42100-microsoft-sp12in.dtb \
  https://raw.githubusercontent.com/harrisonvanderbyl/surface-pro-12-inch-linux/ea0f07e66beea95898d96fbeb6daa472f4735af3/boot/dtb
DTB=x1p42100-microsoft-sp12in.dtb
DTB_SHA256=d7ed4b073c7344cb0bb2c3f7d00655df60b473588a5c0364af54537dc2c672c7
printf '%s  %s\n' "$DTB_SHA256" "$DTB" | sha256sum -c -
```

## Required tool

On Ubuntu or Debian:

```bash
sudo apt install curl git gzip xorriso
```

## Build

Return to the repository root, then run:

```bash
cd ../..
ISO=build/installer-inputs/$ISO
DTB=build/installer-inputs/$DTB
scripts/build-installer \
  --iso "$ISO" \
  --iso-sha256 "$ISO_SHA256" \
  --dtb "$DTB" \
  --dtb-sha256 "$DTB_SHA256" \
  --output build/output/sp12-ubuntu-26.04-arm64.iso
```

The script refuses to overwrite an existing output or sidecar. It independently
checks the base ISO hash and refuses to build from a dirty project checkout. It
inserts the DTB, adds the required GRUB device-tree directive and
`stubble.dtb_override=true`, and includes only this project's committed files at
`/sp12-linux.tar.gz`. It does not include the separate support checkout or its
firmware, DSP, and sensor binaries. It also refreshes Ubuntu's media-check hashes
and trims xorriso's write padding to the reported hybrid-image sector count so
the backup GPT remains at the physical end of the image.

Alongside the ISO it writes:

- `<output>.sha256`, containing the finished image checksum;
- `<output>.buildinfo`, recording the base ISO, DTB, project archive, and builder
  revisions and hashes.

The same build information is embedded at `/sp12-buildinfo.txt` in the ISO.

Keep all three files together. Verify the image again before writing media:

```bash
(cd build/output && sha256sum -c sp12-ubuntu-26.04-arm64.iso.sha256)
```

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
5. Extract the supplied project copy into a writable directory:

   ```bash
   mkdir -p /tmp/sp12-linux
   tar -xzf /cdrom/sp12-linux.tar.gz -C /tmp/sp12-linux
   cd /tmp/sp12-linux
   ```

6. Run the preflight gate:

   ```bash
   scripts/sp12-preflight
   ```

Do not start the installer if the model check or UFS check fails.
