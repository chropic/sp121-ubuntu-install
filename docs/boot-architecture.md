# Boot architecture

The supported design avoids relying on EFI NVRAM entries or on GRUB reading the
installation's ext4 filesystem.

```text
Surface UEFI
  -> FAT ESP: /EFI/BOOT/BOOTAA64.EFI
  -> FAT ESP: /sp12/vmlinuz
  -> FAT ESP: /sp12/initrd.img
  -> FAT ESP: /sp12/dtb
  -> Linux root filesystem, selected by UUID
```

The three files under `/sp12/` are an inseparable release set. A kernel from one
release must never be booted with an initramfs or DTB from another release.

The ESP is normally mounted read-only. Updates copy to temporary `.new` files,
verify byte-for-byte equality, rename them into place, synchronize storage, and
return the ESP to read-only mode.

Ubuntu may report that EFI variables are unsupported even after it successfully
copied the operating system. That message alone is not proof that installation
failed; the target root, ESP, operating-system metadata, and boot files must be
inspected first.
