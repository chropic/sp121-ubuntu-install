# Install Linux

This chapter is not yet marked installation-tested in repository form. It records
the intended checkpoints while the post-install automation is being developed.

## Before clicking Install

Run:

```bash
cat /proc/device-tree/model
tr '\0' '\n' </proc/device-tree/compatible
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MOUNTPOINTS,MODEL
```

Expected device-tree values include:

```text
Surface Pro 12in 1st Edition
microsoft,surface-pro-12in
qcom,x1p42100
```

The internal UFS storage must appear in `lsblk`. If it does not, stop.

## Disk selection

The tested initial installation used the entire internal disk without encryption.
That is destructive. A future release will document dual boot only after it has
its own tested partition-preservation and recovery procedure.

Write down the internal disk's name, manufacturer/model, and size. Confirm all
three values in the graphical installer's final summary before accepting changes.

## Before rebooting

The ordinary installer may copy Linux successfully but fail to create a usable
Surface boot entry. Do not reboot immediately. Confirm the installed target and
ESP:

```bash
findmnt /target
findmnt /target/boot/efi
test -f /target/etc/os-release && cat /target/etc/os-release
ls -la /target/boot
```

Inspect the target without changing it:

```bash
scripts/inspect-install-target \
  --target /target \
  --kernel-release YOUR_EXACT_KERNEL_RELEASE
```

Then preview construction of the fixed fallback path:

```bash
scripts/install-fallback-target \
  --kernel-release YOUR_EXACT_KERNEL_RELEASE \
  --dtb-source /cdrom/casper/x1p42100-microsoft-sp12in.dtb
```

This command remains dry-run-only unless `sudo` and `--apply` are deliberately
added. Its apply path must receive a physical live-install test before the public
guide treats it as release-supported. See the detailed
[target fallback design](development/target-fallback-install.md).
