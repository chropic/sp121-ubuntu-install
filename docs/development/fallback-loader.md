# Standalone fallback loader

`scripts/build-fallback-loader` builds an ARM64 `BOOTAA64.EFI` without mounting or
changing an ESP. Its embedded GRUB configuration searches FAT filesystems for the
marker `/sp12/SP12BOOT`, then loads fixed payload names from that same filesystem.

```bash
scripts/build-fallback-loader \
  --root-uuid YOUR-LINUX-ROOT-UUID \
  --output ./BOOTAA64.EFI
```

The builder verifies every required GRUB module, refuses to overwrite output, and
uses `grub-file` to confirm the result is an ARM64 EFI executable.

The root UUID is embedded in the loader. Rebuild `BOOTAA64.EFI` only when that UUID
or the embedded boot logic changes. Kernel, initramfs, and DTB updates replace the
fixed `/sp12/` payload without rebuilding the loader.

The root UUID is installation-specific. Do not publish it as though it were a
universal value.
