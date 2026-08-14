# Create the installer

This procedure modifies a local copy of an official ARM64 installation ISO. It
does not download an ISO and does not write a USB drive.

## Inputs

Obtain these files on another Linux computer:

1. the official Ubuntu 26.04 ARM64 Desktop ISO;
2. Canonical's matching `SHA256SUMS` file;
3. a tested SP12 DTB named `x1p42100-microsoft-sp12in.dtb`;
4. a clean checkout of this repository.

The separately pinned Harrison support checkout is a post-install input. It is
not placed in the ISO because it contains third-party binary files this project
does not redistribute.

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

Verify the installer DTB separately. The machine-tested live installer used the
DTB from the pinned support checkout; do not substitute the later installed
`7.2.0~rc7-6` DTB, whose compatibility with Ubuntu's stock live kernel has not
been established.

```bash
DTB=/path/to/x1p42100-microsoft-sp12in.dtb
DTB_SHA256=d7ed4b073c7344cb0bb2c3f7d00655df60b473588a5c0364af54537dc2c672c7
printf '%s  %s\n' "$DTB_SHA256" "$DTB" | sha256sum -c -
```

## Required tool

On Ubuntu or Debian:

```bash
sudo apt install git gzip xorriso
```

## Build

From this repository, run:

```bash
scripts/build-installer \
  --iso "$ISO" \
  --iso-sha256 "$ISO_SHA256" \
  --dtb "$DTB" \
  --dtb-sha256 "$DTB_SHA256" \
  --output /path/to/sp12-installer.iso
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
(cd /path/to && sha256sum -c sp12-installer.iso.sha256)
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
5. Run the copy of `sp12-preflight` supplied with the project.

Do not start the installer if the model check or UFS check fails.
