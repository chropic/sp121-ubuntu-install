# Try Ubuntu 26.10 or plan an installation

Use **Ubuntu 26.10 ARM64 with the custom SP12 7.3 platform kernel**.
ARM64 is the processor type in this Surface. A live session runs from USB and
does not require installing Ubuntu on the internal disk.

> [!WARNING]
> **Fresh installation and recovery are experimental and not fully vetted.**
> The owner tested the live image, then deferred installation. A live boot does
> not prove that the installer can safely create a working installed system.

## Before you start

- Use a Surface Pro 12-inch, 1st Edition, with Snapdragon X Plus `X1P42100`.
- Connect the charger. Keep a working USB keyboard available.
- Have a separate backup and recovery USB before changing any disk.
- For installation testing, use a spare disk that you agree to erase.
  A Ventoy boot drive is not the installation target.

No public ISO is provided. The tested private image includes device files
that this project does not distribute. Building an equivalent personal image
is an advanced task; follow the [developer guide](developer/README.md).
Ubuntu 26.04 is covered only in the [legacy notes](legacy-26.04.md).

## Boot the tested live image

The tested filename is `sp12-ubuntu-26.10-arm64-private-live-v2.iso`.
Keep its `.sha256` and `.buildinfo` files. In the directory containing them, run:

```bash
sha256sum -c sp12-ubuntu-26.10-arm64-private-live-v2.iso.sha256
```

Continue only if it reports `OK`.

1. Copy the ISO onto the Ventoy data partition. Do not format an existing
   Ventoy drive just to add this image. Eject the drive safely.
2. On the powered-off Surface, use **Volume Up + Power** to enter its firmware
   settings. Record the current settings. The tested boot path uses Secure Boot
   disabled and USB boot enabled.
3. Connect the charger and Ventoy drive. Use **Volume Down + Power** to boot USB.
4. Select the **private live v2** image, then its live-session menu entry.
5. Open Terminal and run:

```bash
uname -r
cat /etc/os-release
cat /proc/device-tree/model
tr '\0' '\n' </proc/device-tree/compatible
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINTS,MODEL
```

Expect `7.3.0-sp12-v7.3-platform`, Ubuntu `26.10`, and device-tree values
`microsoft,surface-pro-12in` and `qcom,x1p42100`. Stop if the model or kernel is
wrong, the internal disk is missing, or the display and input do not work.
Test Wi-Fi and sound before proceeding. See [hardware checks](maintenance.md#test-hardware).

## Experimental installation

This is the intended test procedure, **not a validated installation recipe**.
The private live layer is not automatically copied into an installed system:
Ubuntu's original installation layers remain unchanged. The target needs its
own custom kernel, matching device tree, device files, and boot setup.
A **device tree (DTB)** tells the kernel how the tablet hardware is connected.
An **initramfs** contains the early drivers needed to start Ubuntu.

Choose the spare disk by its name, model, and capacity. Review the graphical
installer's final disk summary before accepting writes. Do not erase the
working internal system or the boot USB. If a spare disk is unavailable, stop
here and keep using the live session.

After the installer copies Ubuntu, keep the live session open. Do not reboot
until the target checks below pass. Extract the tools from the image:

```bash
mkdir -p /tmp/sp12-linux
tar -xzf /cdrom/sp12-linux.tar.gz -C /tmp/sp12-linux
cd /tmp/sp12-linux
scripts/sp12-preflight
findmnt /target
findmnt /target/boot/efi
cat /target/etc/os-release
scripts/inspect-install-target --experimental-26.10 --target /target
scripts/install-kernel-target --experimental-26.10
```

`/target` must be the selected spare disk. `/target/boot/efi` must be that disk's
**EFI System Partition (ESP)**, the small FAT partition holding boot files.
Stop if a mount is absent or points to another disk. A passing check confirms
the layout and required files; it does not prove an installed system will boot.

After reviewing the kernel dry run, apply it and preview the boot setup:

```bash
sudo scripts/install-kernel-target --experimental-26.10 --apply
KVER=7.3.0-sp12-v7.3-platform
scripts/inspect-install-target --experimental-26.10 --target /target --kernel-release "$KVER"
scripts/install-fallback-target --experimental-26.10 \
  --kernel-release "$KVER" --dtb-source /target/boot/dtb-$KVER
```

The fallback loader starts Ubuntu without creating a firmware boot entry.
Review all paths. Only then apply and compare the three boot files:

```bash
sudo scripts/install-fallback-target --experimental-26.10 \
  --kernel-release "$KVER" --dtb-source /target/boot/dtb-$KVER --apply
cmp /target/boot/vmlinuz-$KVER /target/boot/efi/sp12/vmlinuz
cmp /target/boot/initrd.img-$KVER /target/boot/efi/sp12/initrd.img
cmp /target/boot/dtb-$KVER /target/boot/efi/sp12/dtb
test -f /target/boot/efi/EFI/BOOT/BOOTAA64.EFI
test -x /target/opt/sp12-linux/scripts/sp12-verify
```

Each comparison must exit without differences. Preserve a separate recovery
set, arrange offline access to the required device files, and complete the
[first-boot checks](maintenance.md#first-boot). Do not assume that working
Wi-Fi, sound, or sensors in the live session will transfer to the installed system.
The [developer test checklist](developer/hardware-tests.md) records what remains
before this installation path can be considered fully tested.

If the installer reports an error, keep the live session open and follow
[installer error checks](maintenance.md#installer-error). Do not repeatedly
restart the installer or guess a disk-repair command.
